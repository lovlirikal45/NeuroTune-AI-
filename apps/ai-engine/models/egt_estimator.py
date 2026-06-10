import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class EGTEstimation:
    """Estimation complète de la température d'échappement"""
    egt_celsius: float
    egt_kelvin: float
    turbine_inlet_temp: float
    exhaust_manifold_pressure: float
    confidence: float
    is_safe: bool
    cooling_recommendation: Optional[str]

class EGTEstimatorNN(nn.Module):
    """Réseau de neurones pour l'estimation EGT"""
    
    def __init__(self, input_features: int = 15, hidden_size: int = 256):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_features,
            hidden_size=hidden_size,
            num_layers=3,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,
            num_heads=8,
            batch_first=True
        )
        
        self.regressor = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 4)  # EGT, TIT, EMP, confidence
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        # LSTM
        lstm_out, _ = self.lstm(x)
        
        # Attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Pooling
        pooled = torch.mean(attn_out, dim=1)
        
        # Régression
        output = self.regressor(pooled)
        
        egt = output[:, 0]
        tit = output[:, 1]
        emp = output[:, 2]
        confidence = torch.sigmoid(output[:, 3])
        
        return egt, tit, emp, confidence

class EGTEstimator:
    """Estimateur de température d'échappement"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = EGTEstimatorNN().to(self.device)
        
        if model_path:
            self.load_model(model_path)
        
        # Limites de sécurité
        self.egt_limits = {
            'safe': 850,      # °C - Zone safe
            'warning': 900,   # °C - Attention
            'danger': 950,    # °C - Danger
            'critical': 1000  # °C - Critique
        }
        
        # Facteurs de refroidissement
        self.cooling_factors = {
            'enrichment_effect': 50,    # °C de baisse par 0.1 lambda
            'timing_effect': 30,        # °C de baisse par degré de retard
            'water_methanol': 100,      # °C de baisse avec injection WMI
            'intercooler_efficiency': 0.7  # Efficacité typique intercooler
        }
    
    def estimate_egt(
        self,
        rpm: float,
        load: float,
        lambda_value: float,
        ignition_angle: float,
        boost_pressure: float,
        intake_temp: float,
        coolant_temp: float,
        exhaust_backpressure: float,
        duration: float = 5.0
    ) -> EGTEstimation:
        """Estime l'EGT avec conditions transitoires"""
        
        # Préparer les features temporelles
        time_steps = self._generate_time_steps(
            rpm, load, lambda_value, ignition_angle,
            boost_pressure, intake_temp, coolant_temp,
            exhaust_backpressure, duration
        )
        
        # Inférence
        with torch.no_grad():
            features_tensor = torch.FloatTensor(time_steps).unsqueeze(0).to(self.device)
            egt, tit, emp, confidence = self.model(features_tensor)
        
        egt_celsius = egt.item()
        tit_celsius = tit.item()
        emp_bar = emp.item()
        confidence_val = confidence.item()
        
        # Vérification de sécurité
        is_safe = egt_celsius < self.egt_limits['warning']
        
        # Recommandation de refroidissement si nécessaire
        cooling_rec = None
        if egt_celsius > self.egt_limits['danger']:
            cooling_rec = self._calculate_cooling_strategy(
                egt_celsius, lambda_value, ignition_angle
            )
        
        return EGTEstimation(
            egt_celsius=egt_celsius,
            egt_kelvin=egt_celsius + 273.15,
            turbine_inlet_temp=tit_celsius,
            exhaust_manifold_pressure=emp_bar,
            confidence=confidence_val,
            is_safe=is_safe,
            cooling_recommendation=cooling_rec
        )
    
    def _generate_time_steps(
        self, 
        rpm: float, 
        load: float, 
        lambda_value: float,
        ignition_angle: float, 
        boost_pressure: float,
        intake_temp: float, 
        coolant_temp: float,
        exhaust_backpressure: float, 
        duration: float
    ) -> np.ndarray:
        """Génère des pas de temps pour l'analyse transitoire"""
        
        n_steps = int(duration * 10)  # 10 Hz
        time_steps = []
        
        for t in range(n_steps):
            # Simuler des variations réalistes
            rpm_var = rpm * (1 + 0.02 * np.sin(2 * np.pi * t / n_steps))
            load_var = load * (1 + 0.05 * np.random.randn())
            
            step_features = [
                rpm_var / 8000.0,
                load_var / 100.0,
                lambda_value,
                (ignition_angle + 60) / 120.0,  # Normaliser
                boost_pressure / 3000.0,
                intake_temp / 100.0,
                coolant_temp / 120.0,
                exhaust_backpressure / 5000.0,
                (intake_temp + 273.15) / 373.15,  # Température normalisée
                (coolant_temp + 273.15) / 393.15,
                rpm_var * load_var / (8000 * 100),  # Puissance normalisée
                boost_pressure * rpm_var / (3000 * 8000),  # Débit normalisé
                lambda_value * rpm_var / 8000.0,
                (ignition_angle * rpm_var) / (60 * 8000),
                t / n_steps  # Progression temporelle
            ]
            
            time_steps.append(step_features)
        
        return np.array(time_steps, dtype=np.float32)
    
    def _calculate_cooling_strategy(
        self,
        current_egt: float,
        lambda_value: float,
        ignition_angle: float
    ) -> str:
        """Calcule la stratégie de refroidissement optimale"""
        
        strategies = []
        target_egt = self.egt_limits['safe']
        delta_egt = current_egt - target_egt
        
        # Stratégie 1: Enrichissement
        if lambda_value > 0.85:
            enrichment_needed = delta_egt / self.cooling_factors['enrichment_effect']
            new_lambda = lambda_value - enrichment_needed * 0.1
            if new_lambda >= 0.75:  # Limite de sécurité
                strategies.append(f"Enrichir de {enrichment_needed:.1f} points de lambda")
        
        # Stratégie 2: Retard à l'allumage
        retard_needed = delta_egt / self.cooling_factors['timing_effect']
        if retard_needed <= 10:  # Limite raisonnable
            strategies.append(f"Retarder l'allumage de {retard_needed:.1f}°")
        
        # Stratégie 3: Injection eau/méthanol
        if delta_egt > 100:
            strategies.append("Considérer l'injection eau/méthanol (WMI)")
        
        if not strategies:
            return "Réduire immédiatement la charge moteur"
        
        return " | ".join(strategies)
    
    def load_model(self, model_path: str):
        """Charge un modèle entraîné"""
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()