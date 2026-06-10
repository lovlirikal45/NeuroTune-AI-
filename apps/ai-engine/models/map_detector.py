import numpy as np
import torch
import torch.nn as nn
import onnxruntime as ort
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class MapType(Enum):
    AXIS_1D = "1D"
    MAP_2D = "2D"
    MAP_3D = "3D"
    VOLUMETRIC = "volumetric"

class AxisType(Enum):
    RPM = "rpm"
    LOAD = "load"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FUEL_QUANTITY = "fuel_quantity"
    IGNITION_ANGLE = "ignition_angle"
    LAMBDA = "lambda"
    BOOST = "boost"
    TORQUE = "torque"
    UNKNOWN = "unknown"

@dataclass
class DetectedMap:
    """Map détectée avec métadonnées"""
    address: int
    map_type: MapType
    axis_types: List[AxisType]
    dimensions: Tuple[int, ...]
    data: np.ndarray
    confidence: float
    axis_ranges: List[Tuple[float, float]]
    unit: str
    is_signed: bool
    endianess: str

class MapDetectorNN(nn.Module):
    """Réseau de neurones pour la détection de maps ECU"""
    
    def __init__(self, input_size: int = 256, hidden_size: int = 512):
        super().__init__()
        
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_size, hidden_size * 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size * 2),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size),
        )
        
        # Têtes de classification multiples
        self.map_type_head = nn.Linear(hidden_size, len(MapType))
        self.axis_type_head = nn.Linear(hidden_size, len(AxisType) * 3)  # Max 3 axes
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.feature_extractor(x)
        map_type = self.map_type_head(features)
        axis_type = self.axis_type_head(features)
        confidence = self.confidence_head(features)
        return map_type, axis_type, confidence

class AIDetector:
    """Détecteur IA de maps ECU"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = MapDetectorNN().to(self.device)
        
        if model_path:
            self.load_model(model_path)
        
        # Patterns connus pour chaque type de map
        self.known_patterns = {
            AxisType.RPM: {
                'range': (0, 8000),
                'typical_step': 200,
                'typical_points': [16, 24, 32]
            },
            AxisType.LOAD: {
                'range': (0, 100),
                'typical_step': 5,
                'typical_points': [16, 20, 24]
            },
            AxisType.IGNITION_ANGLE: {
                'range': (-30, 60),
                'typical_step': 1.5,
                'typical_points': [16, 24]
            },
            AxisType.LAMBDA: {
                'range': (0.7, 2.0),
                'typical_step': 0.05,
                'typical_points': [16, 20]
            },
            AxisType.BOOST: {
                'range': (0, 3000),
                'typical_step': 50,
                'typical_points': [16, 24]
            }
        }
        
    def load_model(self, model_path: str):
        """Charge un modèle pré-entraîné"""
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
    def detect_maps(self, binary_data: bytes) -> List[DetectedMap]:
        """Détecte toutes les maps dans un binaire ECU"""
        maps = []
        data = np.frombuffer(binary_data, dtype=np.uint8)
        
        # Approche multi-échelle pour la détection
        window_sizes = [16, 24, 32, 64]
        
        for window_size in window_sizes:
            for offset in range(0, len(data) - window_size * 4, 2):
                candidate = data[offset:offset + window_size * 4]
                
                # Vérification rapide par heuristique
                if self._quick_heuristic_check(candidate):
                    # Analyse approfondie par IA
                    detected = self._analyze_candidate(candidate, offset)
                    if detected and detected.confidence > 0.7:
                        maps.append(detected)
                        offset += window_size * 4  # Éviter les chevauchements
        
        # Post-traitement: fusion des détections proches
        return self._merge_overlapping_maps(maps)
    
    def _quick_heuristic_check(self, data: np.ndarray) -> bool:
        """Vérification rapide pour filtrer les candidats"""
        if len(data) < 64:
            return False
            
        # Vérifier la monotonie des axes potentiels
        axis_values = data[:16].view('>u2')
        
        # Vérifier si les valeurs sont croissantes
        is_increasing = np.all(np.diff(axis_values) > 0)
        
        # Vérifier si les valeurs sont dans des plages raisonnables
        in_range = np.all((axis_values > 0) & (axis_values < 8000))
        
        return is_increasing and in_range
    
    def _analyze_candidate(
        self, 
        data: np.ndarray, 
        offset: int
    ) -> Optional[DetectedMap]:
        """Analyse approfondie d'un candidat de map"""
        
        # Préparation des features pour le réseau
        features = self._extract_features(data)
        
        # Inférence
        with torch.no_grad():
            features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            map_type_logits, axis_type_logits, confidence = self.model(features_tensor)
        
        map_type_idx = torch.argmax(map_type_logits).item()
        confidence_val = confidence.item()
        
        if confidence_val < 0.5:
            return None
        
        # Déterminer les types d'axes
        axis_probs = torch.softmax(axis_type_logits.reshape(-1, len(AxisType)), dim=1)
        axis_indices = torch.argmax(axis_probs, dim=1)
        axis_types = [list(AxisType)[idx] for idx in axis_indices[:3]]
        
        # Extraire les données de la map
        map_data = self._extract_map_data(data, list(MapType)[map_type_idx])
        
        return DetectedMap(
            address=offset,
            map_type=list(MapType)[map_type_idx],
            axis_types=axis_types,
            dimensions=map_data.shape,
            data=map_data,
            confidence=confidence_val,
            axis_ranges=[(0, 8000), (0, 100)],  # À déterminer dynamiquement
            unit=self._determine_unit(axis_types[0]),
            is_signed=False,
            endianess='little'
        )
    
    def _extract_features(self, data: np.ndarray) -> np.ndarray:
        """Extrait les features d'un segment de données"""
        features = []
        
        # Caractéristiques statistiques
        data_16 = data.view('>u2')
        features.extend([
            np.mean(data_16),
            np.std(data_16),
            np.min(data_16),
            np.max(data_16),
            np.median(data_16)
        ])
        
        # Caractéristiques de gradient
        grad = np.diff(data_16)
        features.extend([
            np.mean(grad),
            np.std(grad),
            np.sum(grad > 0) / len(grad),  # Proportion de valeurs croissantes
            np.sum(grad < 0) / len(grad)   # Proportion de valeurs décroissantes
        ])
        
        # Caractéristiques de périodicité
        fft = np.fft.fft(data_16)
        features.extend(np.abs(fft)[:10].real.tolist())
        
        return np.array(features, dtype=np.float32)
    
    def _extract_map_data(self, data: np.ndarray, map_type: MapType) -> np.ndarray:
        """Extrait les données numériques de la map"""
        if map_type == MapType.MAP_2D:
            axis_size = 16  # Taille typique d'axe
            values = data[axis_size * 2:axis_size * 2 + axis_size * 2]
            return values.view('>u2').astype(np.float32)
        
        elif map_type == MapType.MAP_3D:
            size = int(np.sqrt(len(data) / 2))
            return data[:size * size * 2].view('>u2').reshape(size, size).astype(np.float32)
        
        return data.view('>u2').astype(np.float32)
    
    def _determine_unit(self, axis_type: AxisType) -> str:
        """Détermine l'unité en fonction du type d'axe"""
        unit_map = {
            AxisType.RPM: "tr/min",
            AxisType.LOAD: "%",
            AxisType.TEMPERATURE: "°C",
            AxisType.PRESSURE: "hPa",
            AxisType.FUEL_QUANTITY: "mg/coup",
            AxisType.IGNITION_ANGLE: "°BTDC",
            AxisType.LAMBDA: "λ",
            AxisType.BOOST: "hPa",
            AxisType.TORQUE: "Nm"
        }
        return unit_map.get(axis_type, "raw")
    
    def _merge_overlapping_maps(self, maps: List[DetectedMap]) -> List[DetectedMap]:
        """Fusionne les détections qui se chevauchent"""
        if not maps:
            return []
        
        # Trier par confiance décroissante
        sorted_maps = sorted(maps, key=lambda m: m.confidence, reverse=True)
        merged = []
        
        for map_obj in sorted_maps:
            overlap = False
            for existing in merged:
                if self._calculate_overlap(map_obj, existing) > 0.5:
                    overlap = True
                    break
            
            if not overlap:
                merged.append(map_obj)
        
        return merged
    
    def _calculate_overlap(self, map1: DetectedMap, map2: DetectedMap) -> float:
        """Calcule le taux de chevauchement entre deux maps"""
        start1, end1 = map1.address, map1.address + len(map1.data.tobytes())
        start2, end2 = map2.address, map2.address + len(map2.data.tobytes())
        
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return 0.0
        
        overlap_size = overlap_end - overlap_start
        total_size = min(end1 - start1, end2 - start2)
        
        return overlap_size / total_size