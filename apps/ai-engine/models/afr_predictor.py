import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import onnxruntime as ort

@dataclass
class AFRPrediction:
    """Prédiction complète du ratio air/carburant"""
    lambda_value: float
    afr: float
    fuel_mass: float  # mg/coup
    air_mass: float    # mg/coup
    confidence: float
    is_safe: bool
    egt_impact: float  # Impact estimé sur la température d'échappement
    knock_risk: float  # Risque de cliquetis (0-1)
    recommendations: list

class AFRPredictorNN(nn.Module):
    """Réseau de neurones pour la prédiction AFR"""
    
    def __init__(self, input_features: int = 12, hidden_size: int = 256):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_features, hidden_size),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size),
            nn.Dropout(0.2),
            
            nn.Linear(hidden_size, hidden_size * 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size * 2),
            nn.Dropout(0.2),
            
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size)
        )
        
        # Têtes de prédiction spécialisées
        self.lambda_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()  # Sortie normalisée entre 0.7 et 2.0
        )
        
        self.fuel_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        self.egt_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        self.knock_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        features = self.encoder(x)
        
        return {
            'lambda': self.lambda_head(features) * 1.3 + 0.7,  # Scale to [0.7, 2.0]
            'fuel_mass': self.fuel_head(features),
            'egt_impact': self.egt_head(features),
            'knock_risk': self.knock_head(features),
            'confidence': self.confidence_head(features)
        }

class AFRPredictor:
    """Prédicteur de ratio air/carburant avec validation sécurité"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AFRPredictorNN().to(self.device)
        
        if model_path:
            self.load_model(model_path)
        
        # Seuils de sécurité
        self.safety_limits = {
            'lambda_min': 0.75,  # Trop riche - risque
            'lambda_max': 1.25,  # Trop pauvre - risque
            'lambda_power': 0.82,  # Lambda pour puissance max
            'lambda_eco': 1.05,    # Lambda pour économie
            'egt_max': 950,        # Température max échappement (°C)
            'knock_threshold': 0.3  # Seuil de risque de cliquetis
        }
        
        # Facteurs de correction physiques
        self.stoichiometric_afr = {
            'essence': 14.7,
            'e85': 9.8,
            'diesel': 14.5,
            'gpl': 15.5
        }
    
    def predict_afr(
        self, 
        rpm: float, 
        load: float, 
        current_map_values: Dict[str, float],
        target_power: Optional[float] = None
    ) -> AFRPrediction:
        """Prédit l'AFR optimal pour des conditions données"""
        
        # Préparer les features d'entrée
        features = self._prepare_features(rpm, load, current_map_values)
        
        # Inférence
        with torch.no_grad():
            features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            predictions = self.model(features_tensor)
        
        # Extraire les prédictions
        lambda_value = predictions['lambda'].item()
        fuel_mass = predictions['fuel_mass'].item()
        egt_impact = predictions['egt_impact'].item()
        knock_risk = predictions['knock_risk'].item()
        confidence = predictions['confidence'].item()
        
        # Calculer l'AFR
        fuel_type = current_map_values.get('fuel_type', 'essence')
        afr = lambda_value * self.stoichiometric_afr[fuel_type]
        
        # Calculer la masse d'air
        air_mass = fuel_mass * afr
        
        # Vérification de sécurité
        is_safe = self._validate_safety(lambda_value, egt_impact, knock_risk)
        
        # Générer des recommandations
        recommendations = self._generate_recommendations(
            lambda_value, knock_risk, target_power
        )
        
        return AFRPrediction(
            lambda_value=lambda_value,
            afr=afr,
            fuel_mass=fuel_mass,
            air_mass=air_mass,
            confidence=confidence,
            is_safe=is_safe,
            egt_impact=egt_impact,
            knock_risk=knock_risk,
            recommendations=recommendations
        )
    
    def _prepare_features(
        self, 
        rpm: float, 
        load: float, 
        map_values: Dict[str, float]
    ) -> np.ndarray:
        """Prépare le vecteur de features pour le modèle"""
        
        features = [
            rpm / 8000.0,  # Normalisation RPM
            load / 100.0,  # Normalisation charge
            map_values.get('boost_pressure', 0) / 3000.0,
            map_values.get('intake_temp', 25) / 100.0,
            map_values.get('coolant_temp', 90) / 120.0,
            map_values.get('ignition_angle', 20) / 60.0,
            map_values.get('fuel_pressure', 0) / 2000.0,
            map_values.get('injection_duration', 0) / 10.0,
            map_values.get('injection_angle', 0) / 360.0,
            map_values.get('ambient_pressure', 1013) / 1100.0,
            map_values.get('ambient_temp', 20) / 50.0,
            map_values.get('ethanol_content', 0) / 100.0
        ]
        
        return np.array(features, dtype=np.float32)
    
    def _validate_safety(
        self, 
        lambda_value: float, 
        egt_impact: float, 
        knock_risk: float
    ) -> bool:
        """Valide la sécurité d'une prédiction AFR"""
        
        # Vérifier les limites de lambda
        if lambda_value < self.safety_limits['lambda_min']:
            return False
        if lambda_value > self.safety_limits['lambda_max']:
            return False
        
        # Vérifier la température d'échappement
        if egt_impact > self.safety_limits['egt_max']:
            return False
        
        # Vérifier le risque de cliquetis
        if knock_risk > self.safety_limits['knock_threshold']:
            return False
        
        return True
    
    def _generate_recommendations(
        self, 
        lambda_value: float, 
        knock_risk: float,
        target_power: Optional[float]
    ) -> list:
        """Génère des recommandations de tuning"""
        
        recommendations = []
        
        if lambda_value < 0.8:
            recommendations.append({
                'type': 'warning',
                'message': 'Mélange trop riche - risque d\'encrassement',
                'action': 'Augmenter le lambda vers 0.85-0.90'
            })
        
        if lambda_value > 1.15:
            recommendations.append({
                'type': 'warning',
                'message': 'Mélange trop pauvre - risque de surchauffe',
                'action': 'Réduire le lambda vers 1.05-1.10'
            })
        
        if knock_risk > 0.2:
            recommendations.append({
                'type': 'danger',
                'message': f'Risque élevé de cliquetis ({knock_risk:.0%})',
                'action': 'Réduire l\'avance ou enrichir le mélange'
            })
        
        if target_power:
            if lambda_value > self.safety_limits['lambda_power']:
                recommendations.append({
                    'type': 'info',
                    'message': 'Enrichir pour atteindre la puissance cible',
                    'action': f'Cibler lambda {self.safety_limits["lambda_power"]}'
                })
        
        return recommendations
    
    def load_model(self, model_path: str):
        """Charge un modèle entraîné"""
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
    
    def export_to_onnx(self, output_path: str):
        """Exporte le modèle au format ONNX"""
        dummy_input = torch.randn(1, 12).to(self.device)
        
        torch.onnx.export(
            self.model,
            dummy_input,
            output_path,
            input_names=['features'],
            output_names=['lambda', 'fuel_mass', 'egt_impact', 'knock_risk', 'confidence'],
            dynamic_axes={
                'features': {0: 'batch_size'},
                'lambda': {0: 'batch_size'},
                'fuel_mass': {0: 'batch_size'}
            }
        )