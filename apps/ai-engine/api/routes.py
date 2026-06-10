from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, BackgroundTasks
from fastapi.security import APIKeyHeader
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import asyncio

from services.inference_service import InferenceService, InferenceRequest
from config import settings

router = APIRouter(prefix="/api/v1", tags=["AI Engine"])

# Sécurité
api_key_header = APIKeyHeader(name="X-API-Key")

# Service d'inférence (singleton)
inference_service = None

def get_inference_service():
    global inference_service
    if inference_service is None:
        inference_service = InferenceService()
    return inference_service

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if settings.API_KEY and api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Modèles de requête/réponse
class MapDetectionRequest(BaseModel):
    project_id: str
    file_url: Optional[str] = None
    ecu_data_hex: Optional[str] = None

class MapDetectionResponse(BaseModel):
    request_id: str
    detected_maps: List[Dict[str, Any]]
    total_maps: int
    processing_time_ms: float

class TuningAnalysisRequest(BaseModel):
    project_id: str
    current_maps: Dict[str, Any]
    conditions: Dict[str, float]
    target: Optional[Dict[str, float]] = None
    analysis_types: List[str] = ['afr', 'egt', 'torque', 'boost', 'safety']

class TuningAnalysisResponse(BaseModel):
    request_id: str
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, str]]
    safety_score: float
    is_safe: bool

class SimulationRequest(BaseModel):
    project_id: str
    conditions: Dict[str, float]
    maps: Dict[str, Any]
    duration: float = 10.0  # secondes
    output_frequency: int = 100  # Hz

# Routes
@router.post("/detect-maps", response_model=MapDetectionResponse)
async def detect_maps(
    request: MapDetectionRequest,
    service: InferenceService = Depends(get_inference_service),
    api_key: str = Depends(verify_api_key)
):
    """Détecte automatiquement les maps dans un fichier ECU"""
    
    try:
        # Charger les données ECU
        if request.file_url:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(request.file_url) as response:
                    ecu_data = await response.read()
        elif request.ecu_data_hex:
            ecu_data = bytes.fromhex(request.ecu_data_hex)
        else:
            raise HTTPException(status_code=400, detail="Aucune donnée ECU fournie")
        
        # Lancer l'inférence
        inference_request = InferenceRequest(
            request_id=f"map_detect_{request.project_id}",
            project_id=request.project_id,
            ecu_data=ecu_data,
            analysis_types=['map_detection']
        )
        
        result = await service.process_request(inference_request)
        
        return MapDetectionResponse(
            request_id=result.request_id,
            detected_maps=result.analysis.get('detected_maps', []),
            total_maps=result.analysis.get('total_maps', 0),
            processing_time_ms=result.processing_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-tuning", response_model=TuningAnalysisResponse)
async def analyze_tuning(
    request: TuningAnalysisRequest,
    service: InferenceService = Depends(get_inference_service),
    api_key: str = Depends(verify_api_key)
):
    """Analyse complète d'une calibration"""
    
    try:
        inference_request = InferenceRequest(
            request_id=f"tuning_{request.project_id}",
            project_id=request.project_id,
            current_maps=request.current_maps,
            conditions=request.conditions,
            target=request.target,
            analysis_types=request.analysis_types
        )
        
        result = await service.process_request(inference_request)
        
        # Extraire le score de sécurité
        safety_score = result.safety_checks.get('safety_assessment', 
                      sum(1 for v in result.safety_checks.values() if v) / 
                      max(len(result.safety_checks), 1) * 100)
        
        return TuningAnalysisResponse(
            request_id=result.request_id,
            analysis=result.analysis,
            recommendations=result.recommendations,
            safety_score=safety_score,
            is_safe=all(result.safety_checks.values())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate")
async def simulate_engine(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    service: InferenceService = Depends(get_inference_service),
    api_key: str = Depends(verify_api_key)
):
    """Lance une simulation moteur complète"""
    
    # Lancer la simulation en arrière-plan
    task_id = f"sim_{request.project_id}_{asyncio.get_event_loop().time()}"
    
    background_tasks.add_task(
        service.run_simulation,
        task_id=task_id,
        conditions=request.conditions,
        maps=request.maps,
        duration=request.duration,
        output_frequency=request.output_frequency
    )
    
    return {
        'task_id': task_id,
        'status': 'started',
        'estimated_duration': request.duration
    }

@router.get("/simulation/{task_id}/status")
async def get_simulation_status(
    task_id: str,
    service: InferenceService = Depends(get_inference_service),
    api_key: str = Depends(verify_api_key)
):
    """Vérifie le statut d'une simulation"""
    
    status = await service.get_simulation_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Simulation non trouvée")
    
    return status

@router.get("/simulation/{task_id}/results")
async def get_simulation_results(
    task_id: str,
    service: InferenceService = Depends(get_inference_service),
    api_key: str = Depends(verify_api_key)
):
    """Récupère les résultats d'une simulation"""
    
    results = await service.get_simulation_results(task_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Résultats non disponibles")
    
    return results

@router.get("/health")
async def health_check():
    """Vérification de santé du service IA"""
    
    return {
        'status': 'healthy',
        'version': settings.APP_VERSION,
        'models_loaded': True,
        'gpu_available': torch.cuda.is_available(),
        'timestamp': datetime.now().isoformat()
    }