#!/usr/bin/env python3
"""Télécharge les modèles pré-entraînés pour NeuroTune AI"""

import os
import sys
import torch
import requests
from pathlib import Path
from tqdm import tqdm

MODELS = {
    'map_detector_v2.onnx': 'https://models.neurotune.ai/map_detector_v2.onnx',
    'afr_predictor_v3.onnx': 'https://models.neurotune.ai/afr_predictor_v3.onnx',
    'egt_estimator_v2.onnx': 'https://models.neurotune.ai/egt_estimator_v2.onnx',
    'torque_model_v4.onnx': 'https://models.neurotune.ai/torque_model_v4.onnx',
    'boost_analyzer_v2.onnx': 'https://models.neurotune.ai/boost_analyzer_v2.onnx',
}

def download_file(url: str, destination: Path):
    """Télécharge un fichier avec barre de progression"""
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as f:
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=destination.name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))

def main():
    model_path = Path(os.getenv('MODEL_PATH', '/models'))
    model_path.mkdir(parents=True, exist_ok=True)
    
    print("📦 Téléchargement des modèles NeuroTune AI...")
    
    for model_name, url in MODELS.items():
        destination = model_path / model_name
        
        if destination.exists():
            print(f"✅ {model_name} déjà présent")
            continue
        
        print(f"⬇️  Téléchargement de {model_name}...")
        try:
            download_file(url, destination)
            print(f"✅ {model_name} téléchargé")
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement de {model_name}: {e}")
    
    print("\n✅ Tous les modèles sont prêts!")

if __name__ == '__main__':
    main()