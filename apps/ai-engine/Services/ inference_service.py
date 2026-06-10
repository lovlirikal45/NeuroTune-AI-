import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
from redis import asyncio as aioredis
from pydantic import BaseModel, ValidationError

from models.map_detector import AIDetector, DetectedMap
from models.afr_predictor import AFRPredictor, AFRPrediction
from models.egt_estimator import EGTEstimator, EGTEstimation
from models.torque_model import TorqueModel, TorquePrediction
from models.boost_analyzer import BoostAnalyzer, BoostAnalysis
from utils.safety_checker import SafetyChecker
from utils.ecu_utils import ECUUtils
from config import settings

class InferenceRequest(BaseModel):
    """Requête d'inférence standardisée"""
    request_id: str
    project_id: str
    ecu_data: Optional[bytes] = None
    current_maps: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, float]] = None
    target: Optional[Dict[str, float]] = None
    analysis_types: List[str]

class InferenceResult(BaseModel):
    """Résultat d'inférence"""
    request_id: str
    timestamp: str
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, str]]
    safety_checks: Dict[str, bool]
    confidence_scores: Dict[str, float]
    processing_time_ms: float

class InferenceService:
    """Service central d'inférence IA"""
    
    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL)
        
        # Initialiser les modèles
        self.map_detector = AIDetector(settings.MAP_DETECTION_MODEL)
        self.afr_predictor = AFRPredictor(settings.AFR_PREDICTION_MODEL)
        self.egt_estimator = EGTEstimator(settings.EGT_MODEL)
        self.torque_model = TorqueModel(settings.TORQUE_MODEL)
        self.boost_analyzer = BoostAnalyzer(settings.BOOST_MODEL)
        
        # Utilitaires
        self.safety_checker = SafetyChecker()
        self.ecu_utils = ECUUtils()
        
        # Cache
        self.cache_ttl = settings.CACHE_TTL
        
    async def process_request(self, request: InferenceRequest) -> InferenceResult:
        """Traite une requête d'inférence complète"""
        
        start_time = datetime.now()
        
        # Vérifier le cache
        cache_key = self._generate_cache_key(request)
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Initialiser les résultats
        analysis = {}
        recommendations = []
        safety_checks = {}
        confidence_scores = {}
        
        # Traiter chaque type d'analyse demandé
        tasks = []
        
        if 'map_detection' in request.analysis_types and request.ecu_data:
            tasks.append(self._detect_maps(request))
        
        if 'afr_analysis' in request.analysis_types and request.conditions:
            tasks.append(self._analyze_afr(request))
        
        if 'egt_analysis' in request.analysis_types and request.conditions:
            tasks.append(self._analyze_egt(request))
        
        if 'torque_analysis' in request.analysis_types:
            tasks.append(self._analyze_torque(request))
        
        if 'boost_analysis' in request.analysis_types:
            tasks.append(self._analyze_boost(request))
        
        if 'full_safety_check' in request.analysis_types:
            tasks.append(self._full_safety_check(request))
        
        # Exécuter toutes les analyses en parallèle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Agréger les résultats
        for result in results:
            if isinstance(result, Exception):
                continue
            
            analysis.update(result.get('analysis', {}))
            recommendations.extend(result.get('recommendations', []))
            safety_checks.update(result.get('safety_checks', {}))
            confidence_scores.update(result.get('confidence_scores', {}))
        
        # Calculer le temps de traitement
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Créer le résultat final
        inference_result = InferenceResult(
            request_id=request.request_id,
            timestamp=datetime.now().isoformat(),
            analysis=analysis,
            recommendations=recommendations,
            safety_checks=safety_checks,
            confidence_scores=confidence_scores,
            processing_time_ms=processing_time
        )
        
        # Mettre en cache
        await self._cache_result(cache_key, inference_result)
        
        return inference_result
    
    async def _detect_maps(self, request: InferenceRequest) -> Dict:
        """Détection de maps dans un binaire ECU"""
        
        try:
            # Validation du fichier
            is_valid = self.ecu_utils.validate_ecu_file(request.ecu_data)
            if not is_valid:
                return {
                    'analysis': {},
                    'recommendations': [{'type': 'error', 'message': 'Fichier ECU invalide'}],
                    'safety_checks': {'valid_file': False},
                    'confidence_scores': {}
                }
            
            # Détection de l'endianess
            endianess = self.ecu_utils.detect_endianess(request.ecu_data)
            
            # Détection des maps
            maps = self.map_detector.detect_maps(request.ecu_data)
            
            # Classifier les maps
            classified_maps = self._classify_maps(maps)
            
            return {
                'analysis': {
                    'detected_maps': [
                        {
                            'address': hex(m.address),
                            'type': m.map_type.value,
                            'confidence': m.confidence,
                            'axis_types': [at.value for at in m.axis_types]
                        }
                        for m in maps[:20]  # Limiter à 20 maps
                    ],
                    'total_maps': len(maps),
                    'endianess': endianess
                },
                'recommendations': self._generate_map_recommendations(maps),
                'safety_checks': {
                    'maps_found': len(maps) > 0,
                    'file_valid': True
                },
                'confidence_scores': {
                    f'map_{i}': m.confidence 
                    for i, m in enumerate(maps[:10])
                }
            }
            
        except Exception as e:
            return {
                'analysis': {'error': str(e)},
                'recommendations': [{'type': 'error', 'message': f'Erreur détection: {str(e)}'}],
                'safety_checks': {'detection_error': True},
                'confidence_scores': {}
            }
    
    async def _analyze_afr(self, request: InferenceRequest) -> Dict:
        """Analyse complète AFR"""
        
        conditions = request.conditions
        rpm = conditions.get('rpm', 3000)
        load = conditions.get('load', 50)
        current_maps = request.current_maps or {}
        target_power = request.target.get('power') if request.target else None
        
        # Prédiction principale
        prediction = self.afr_predictor.predict_afr(
            rpm, load, current_maps, target_power
        )
        
        # Analyse de la plage RPM/Load
        afr_map = self._generate_afr_map(rpm, load, current_maps)
        
        return {
            'analysis': {
                'current_lambda': prediction.lambda_value,
                'current_afr': prediction.afr,
                'optimal_lambda_power': 0.82,
                'optimal_lambda_eco': 1.05,
                'fuel_mass': prediction.fuel_mass,
                'egt_impact': prediction.egt_impact,
                'knock_risk': prediction.knock_risk,
                'afr_map_2d': afr_map.tolist() if len(afr_map) < 1000 else 'too_large'
            },
            'recommendations': prediction.recommendations,
            'safety_checks': {
                'lambda_safe': prediction.is_safe,
                'knock_safe': prediction.knock_risk < 0.3,
                'egt_safe': prediction.egt_impact < 950
            },
            'confidence_scores': {
                'afr_prediction': prediction.confidence
            }
        }
    
    async def _analyze_egt(self, request: InferenceRequest) -> Dict:
        """Analyse EGT"""
        
        conditions = request.conditions
        estimation = self.egt_estimator.estimate_egt(
            rpm=conditions.get('rpm', 3000),
            load=conditions.get('load', 50),
            lambda_value=conditions.get('lambda', 1.0),
            ignition_angle=conditions.get('ignition_angle', 20),
            boost_pressure=conditions.get('boost_pressure', 1000),
            intake_temp=conditions.get('intake_temp', 25),
            coolant_temp=conditions.get('coolant_temp', 90),
            exhaust_backpressure=conditions.get('exhaust_backpressure', 100)
        )
        
        return {
            'analysis': {
                'egt_celsius': estimation.egt_celsius,
                'turbine_inlet_temp': estimation.turbine_inlet_temp,
                'exhaust_pressure': estimation.exhaust_manifold_pressure,
                'cooling_needed': not estimation.is_safe
            },
            'recommendations': [
                {'type': 'warning' if not estimation.is_safe else 'info',
                 'message': estimation.cooling_recommendation or 'EGT normal',
                 'action': 'Surveiller' if estimation.is_safe else 'Refroidir'}
            ],
            'safety_checks': {
                'egt_safe': estimation.is_safe,
                'egt_below_warning': estimation.egt_celsius < 900,
                'egt_below_critical': estimation.egt_celsius < 1000
            },
            'confidence_scores': {
                'egt_estimation': estimation.confidence
            }
        }
    
    async def _analyze_torque(self, request: InferenceRequest) -> Dict:
        """Analyse du couple moteur"""
        
        conditions = request.conditions or {}
        
        # Simulation du couple
        torque_pred = self.torque_model.predict_torque(
            rpm=conditions.get('rpm', 3000),
            load=conditions.get('load', 50),
            lambda_value=conditions.get('lambda', 1.0),
            ignition_angle=conditions.get('ignition_angle', 20),
            boost_pressure=conditions.get('boost_pressure', 1000),
            intake_temp=conditions.get('intake_temp', 25)
        )
        
        return {
            'analysis': {
                'estimated_torque': torque_pred.torque_nm,
                'estimated_power': torque_pred.power_hp,
                'torque_at_wheels': torque_pred.torque_nm * 0.85,
                'bmep': torque_pred.bmep_bar,
                'volumetric_efficiency': torque_pred.volumetric_efficiency
            },
            'recommendations': [
                {'type': 'info',
                 'message': f'Couple estimé: {torque_pred.torque_nm:.0f} Nm',
                 'action': 'Optimiser les maps de couple'}
            ],
            'safety_checks': {
                'torque_plausible': 0 < torque_pred.torque_nm < 2000,
                'bmep_safe': torque_pred.bmep_bar < 30
            },
            'confidence_scores': {
                'torque_prediction': torque_pred.confidence
            }
        }
    
    async def _analyze_boost(self, request: InferenceRequest) -> Dict:
        """Analyse de la pression de suralimentation"""
        
        conditions = request.conditions or {}
        
        boost_analysis = self.boost_analyzer.analyze_boost_safety(
            target_boost=request.target.get('boost') if request.target else None,
            current_boost=conditions.get('boost_pressure', 1000),
            rpm=conditions.get('rpm', 3000),
            turbo_size=request.current_maps.get('turbo_size') if request.current_maps else None
        )
        
        return {
            'analysis': {
                'current_boost': boost_analysis.current_boost,
                'max_safe_boost': boost_analysis.max_safe_boost,
                'turbo_efficiency': boost_analysis.efficiency,
                'surge_margin': boost_analysis.surge_margin,
                'overspeed_risk': boost_analysis.overspeed_risk
            },
            'recommendations': boost_analysis.recommendations,
            'safety_checks': {
                'boost_safe': boost_analysis.is_safe,
                'surge_safe': boost_analysis.surge_margin > 10,
                'overspeed_safe': boost_analysis.overspeed_risk < 0.3
            },
            'confidence_scores': {
                'boost_analysis': boost_analysis.confidence
            }
        }
    
    async def _full_safety_check(self, request: InferenceRequest) -> Dict:
        """Vérification complète de sécurité"""
        
        # Combiner toutes les vérifications
        safety_results = self.safety_checker.comprehensive_check(
            ecu_data=request.ecu_data,
            conditions=request.conditions,
            current_maps=request.current_maps,
            target=request.target
        )
        
        return {
            'analysis': {
                'safety_score': safety_results.overall_score,
                'critical_issues': safety_results.critical_issues,
                'warnings': safety_results.warnings
            },
            'recommendations': safety_results.recommendations,
            'safety_checks': safety_results.checks,
            'confidence_scores': {
                'safety_assessment': safety_results.confidence
            }
        }
    
    def _classify_maps(self, maps: List[DetectedMap]) -> Dict:
        """Classifie les maps détectées par catégorie"""
        classified = {
            'fuel': [],
            'ignition': [],
            'boost': [],
            'torque': [],
            'sensors': [],
            'other': []
        }
        
        for map_obj in maps:
            axis_types = [at.value for at in map_obj.axis_types]
            
            if 'lambda' in axis_types or 'fuel_quantity' in axis_types:
                classified['fuel'].append(map_obj)
            elif 'ignition_angle' in axis_types:
                classified['ignition'].append(map_obj)
            elif 'boost' in axis_types:
                classified['boost'].append(map_obj)
            elif 'torque' in axis_types:
                classified['torque'].append(map_obj)
            elif 'temperature' in axis_types or 'pressure' in axis_types:
                classified['sensors'].append(map_obj)
            else:
                classified['other'].append(map_obj)
        
        return classified
    
    def _generate_map_recommendations(self, maps: List[DetectedMap]) -> List[Dict]:
        """Génère des recommandations basées sur les maps détectées"""
        recommendations = []
        
        if len(maps) == 0:
            recommendations.append({
                'type': 'warning',
                'message': 'Aucune map détectée',
                'action': 'Vérifier le fichier ECU'
            })
            return recommendations
        
        # Recommandations basées sur les types de maps trouvées
        axis_types = set()
        for map_obj in maps:
            for at in map_obj.axis_types:
                axis_types.add(at)
        
        if AxisType.LAMBDA not in axis_types:
            recommendations.append({
                'type': 'info',
                'message': 'Map lambda non détectée',
                'action': 'Rechercher manuellement'
            })
        
        return recommendations
    
    def _generate_afr_map(
        self, 
        base_rpm: float, 
        base_load: float, 
        current_maps: Dict
    ) -> np.ndarray:
        """Génère une cartographie AFR 2D"""
        
        rpm_range = np.linspace(1000, 7000, 10)
        load_range = np.linspace(10, 100, 10)
        afr_map = np.zeros((len(rpm_range), len(load_range)))
        
        for i, rpm in enumerate(rpm_range):
            for j, load in enumerate(load_range):
                pred = self.afr_predictor.predict_afr(rpm, load, current_maps)
                afr_map[i, j] = pred.lambda_value
        
        return afr_map
    
    def _generate_cache_key(self, request: InferenceRequest) -> str:
        """Génère une clé de cache unique"""
        
        cache_data = {
            'project_id': request.project_id,
            'analysis_types': sorted(request.analysis_types),
            'conditions': request.conditions,
            'data_hash': hashlib.sha256(
                request.ecu_data or b''
            ).hexdigest() if request.ecu_data else 'no_data'
        }
        
        key_string = json.dumps(cache_data, sort_keys=True)
        return f"inference:{hashlib.sha256(key_string.encode()).hexdigest()}"
    
    async def _get_cached_result(self, key: str) -> Optional[InferenceResult]:
        """Récupère un résultat en cache"""
        
        cached = await self.redis.get(key)
        if cached:
            return InferenceResult(**json.loads(cached))
        return None
    
    async def _cache_result(self, key: str, result: InferenceResult):
        """Met en cache un résultat"""
        
        await self.redis.setex(
            key,
            self.cache_ttl,
            result.json()
        )