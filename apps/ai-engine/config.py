import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configuration du moteur IA NeuroTune"""
    
    # Application
    APP_NAME: str = "NeuroTune AI Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Serveur
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    
    # GPU/CPU
    DEVICE: str = Field(default="cuda" if os.system("nvidia-smi") == 0 else "cpu")
    CUDA_VISIBLE_DEVICES: Optional[str] = Field(default=None)
    TORCH_THREADS: int = Field(default=8)
    
    # Modèles
    MODEL_PATH: str = Field(default="/models")
    MAP_DETECTION_MODEL: str = Field(default="map_detector_v2.onnx")
    AFR_PREDICTION_MODEL: str = Field(default="afr_predictor_v3.onnx")
    EGT_MODEL: str = Field(default="egt_estimator_v2.onnx")
    TORQUE_MODEL: str = Field(default="torque_model_v4.onnx")
    BOOST_MODEL: str = Field(default="boost_analyzer_v2.onnx")
    
    # Cache Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")
    CACHE_TTL: int = Field(default=3600)
    
    # Base de données
    DATABASE_URL: Optional[str] = Field(default=None)
    
    # Sécurité
    API_KEY: Optional[str] = Field(default=None)
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024)  # 100MB
    
    # Performance
    BATCH_SIZE: int = Field(default=32)
    MAX_WORKERS: int = Field(default=16)
    TIMEOUT: int = Field(default=300)
    
    # Monitoring
    PROMETHEUS_PORT: int = Field(default=9090)
    ENABLE_TRACING: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()