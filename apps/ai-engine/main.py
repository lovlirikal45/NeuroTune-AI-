import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import torch
import logging

from api.routes import router
from config import settings

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    
    # Startup
    logger.info("🚀 Démarrage du moteur IA NeuroTune...")
    
    # Vérifier GPU
    if torch.cuda.is_available():
        logger.info(f"✅ GPU détecté: {torch.cuda.get_device_name(0)}")
        logger.info(f"   Mémoire: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        logger.info("⚠️  Pas de GPU détecté - utilisation CPU")
    
    # Vérifier les modèles
    logger.info("📦 Chargement des modèles IA...")
    # Les modèles seront chargés à la demande par le service d'inférence
    
    logger.info("✅ Moteur IA prêt!")
    
    yield
    
    # Shutdown
    logger.info("👋 Arrêt du moteur IA...")

# Créer l'application FastAPI
app = FastAPI(
    title="NeuroTune AI Engine",
    description="Moteur d'intelligence artificielle pour calibration ECU",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://neurotune.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Inclure les routes
app.include_router(router)

# Point d'entrée
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )