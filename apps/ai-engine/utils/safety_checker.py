from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np

@dataclass
class SafetyResult:
    """Résultat de vérification de sécurité"""
    overall_score: float  # 0-100
    critical_issues: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    recommendations: List[Dict[str, str]]
    checks: Dict[str, bool]
    confidence: float

class SafetyChecker:
    """Vérificateur de sécurité pour calibration ECU"""
    
    def __init__(self):
        # Limites de sécurité absolues
        self.absolute_limits = {
            'lambda': {'min': 0.70, 'max': 1.30},
            'egt': {'max': 1000},  # °C
            'boost': {'max_factor': 2.5},  # x pression atmo
            'ignition': {'min': -30, 'max': 60},  # °BTDC
            'afr': {'min': 10.0, 'max': 18.0},
            'injection_duration': {'max': 20.0},  # ms
            'fuel_pressure': {'max': 2000.0}  # bar
        }
        
        # Seuils de recommandation
        self.recommendation_thresholds = {
            'lambda_power': 0.80,
            'lambda_eco': 1.05,
            'egt_warning': 900,
            'boost_warning_factor': 2.0,
            'knock_threshold': 0.2
        }
    
    def comprehensive_check(
        self,
        ecu_data: Optional[bytes],
        conditions: Optional[Dict[str, float]],
        current_maps: Optional[Dict[str, Any]],
        target: Optional[Dict[str, float]]
    ) -> SafetyResult:
        """Vérification complète de sécurité"""
        
        checks = {}
        critical_issues = []
        warnings = []
        recommendations = []
        
        # Vérifier les conditions actuelles
        if conditions:
            # Lambda
            if 'lambda' in conditions:
                lambda_val = conditions['lambda']
                if lambda_val < self.absolute_limits['lambda']['min']:
                    critical_issues.append({
                        'parameter': 'lambda',
                        'value': lambda_val,
                        'limit': self.absolute_limits['lambda']['min'],
                        'message': 'Lambda trop bas - risque moteur'
                    })
                    checks['lambda_safe'] = False
                elif lambda_val > self.absolute_limits['lambda']['max']:
                    critical_issues.append({
                        'parameter': 'lambda',
                        'value': lambda_val,
                        'limit': self.absolute_limits['lambda']['max'],
                        'message': 'Lambda trop haut - risque surchauffe'
                    })
                    checks['lambda_safe'] = False
                else:
                    checks['lambda_safe'] = True
            
            # EGT
            if 'egt' in conditions:
                egt = conditions['egt']
                if egt > self.absolute_limits['egt']['max']:
                    critical_issues.append({
                        'parameter': 'EGT',
                        'value': egt,
                        'limit': self.absolute_limits['egt']['max'],
                        'message': 'Température échappement critique'
                    })
                    checks['egt_safe'] = False
                elif egt > self.recommendation_thresholds['egt_warning']:
                    warnings.append({
                        'parameter': 'EGT',
                        'value': egt,
                        'message': 'EGT élevée - surveiller'
                    })
                    checks['egt_safe'] = True
                else:
                    checks['egt_safe'] = True
            
            # Boost
            if 'boost_pressure' in conditions:
                boost = conditions['boost_pressure']
                max_boost = 1013 * self.absolute_limits['boost']['max_factor']
                
                if boost > max_boost:
                    critical_issues.append({
                        'parameter': 'Boost',
                        'value': boost,
                        'limit': max_boost,
                        'message': 'Pression de suralimentation excessive'
                    })
                    checks['boost_safe'] = False
                else:
                    checks['boost_safe'] = True
            
            # Knock risk
            if 'knock_risk' in conditions:
                knock = conditions['knock_risk']
                if knock > self.recommendation_thresholds['knock_threshold']:
                    warnings.append({
                        'parameter': 'Knock',
                        'value': knock,
                        'message': f'Risque de cliquetis: {knock:.0%}'
                    })
                    checks['knock_safe'] = knock < 0.5
                else:
                    checks['knock_safe'] = True
        
        # Vérifier les maps actuelles
        if current_maps:
            map_checks = self._validate_maps(current_maps)
            checks.update(map_checks)
        
        # Vérifier la cible
        if target:
            target_checks = self._validate_target(target, conditions or {})
            checks.update(target_checks)
        
        # Calculer le score de sécurité
        safe_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks) if checks else 1
        overall_score = (safe_checks / total_checks) * 100
        
        # Générer des recommandations
        if critical_issues:
            recommendations.append({
                'type': 'danger',
                'message': f'{len(critical_issues)} problème(s) critique(s) détecté(s)',
                'action': 'Ne pas appliquer la calibration'
            })
        
        if warnings:
            recommendations.append({
                'type': 'warning',
                'message': f'{len(warnings)} avertissement(s)',
                'action': 'Réviser les paramètres avant application'
            })
        
        return SafetyResult(
            overall_score=overall_score,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            checks=checks,
            confidence=0.95 if total_checks > 5 else 0.7
        )
    
    def _validate_maps(self, maps: Dict[str, Any]) -> Dict[str, bool]:
        """Valide la cohérence des maps"""
        checks = {}
        
        # Vérifier la continuité des maps
        if 'ignition_map' in maps:
            ignition_map = np.array(maps['ignition_map'])
            if ignition_map.size > 0:
                # Vérifier les gradients
                gradients = np.diff(ignition_map, axis=0)
                max_gradient = np.max(np.abs(gradients))
                checks['ignition_smooth'] = max_gradient < 10  # ° par cellule
        
        if 'fuel_map' in maps:
            fuel_map = np.array(maps['fuel_map'])
            if fuel_map.size > 0:
                # Vérifier les valeurs
                checks['fuel_positive'] = np.all(fuel_map > 0)
                checks['fuel_plausible'] = np.all(fuel_map < 200)  # mg/coup max
        
        return checks
    
    def _validate_target(
        self, 
        target: Dict[str, float], 
        current: Dict[str, float]
    ) -> Dict[str, bool]:
        """Valide si la cible est atteignable en sécurité"""
        checks = {}
        
        # Vérifier l'augmentation de puissance
        if 'power' in target and 'power' in current:
            power_increase = target['power'] / max(current['power'], 1)
            checks['power_increase_safe'] = power_increase < 1.5  # Max 50% augmentation
        
        # Vérifier l'augmentation de boost
        if 'boost' in target and 'boost' in current:
            boost_increase = target['boost'] / max(current['boost'], 1)
            checks['boost_increase_safe'] = boost_increase < 1.3  # Max 30% augmentation
        
        return checks