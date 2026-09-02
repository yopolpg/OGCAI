from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ModelDetails, RouteRequest, RouteDecision
from app.services.ollama_service import ollama_service
from app.services.router_service import router_service

router = APIRouter(prefix="/api", tags=["models"])

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check system and Ollama server health."""
    ollama_health = await ollama_service.check_health()
    return {
        "status": "online",
        "engine": "OGCAI Core Engine Phase 1",
        "ollama": ollama_health
    }

@router.get("/models", response_model=List[ModelDetails])
async def get_models():
    """Retrieve list of installed local Ollama models with category and UI badges."""
    models = await ollama_service.list_models()
    return models

@router.post("/route", response_model=RouteDecision)
async def test_route(request: RouteRequest):
    """Test auto-routing logic without generating a full chat response."""
    decision = await router_service.route_message(
        message=request.message,
        manual_model=request.manual_model
    )
    return decision
