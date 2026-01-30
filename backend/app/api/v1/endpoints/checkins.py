"""
TB Personal OS - Check-in Endpoints
API para registro e consulta de check-ins
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date
import structlog

from app.services.checkin_service import checkin_service
from app.api.v1.dependencies.auth import get_current_user_id, require_api_key
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/checkins", tags=["Check-ins"])


# ==========================================
# SCHEMAS
# ==========================================

class EnergyCheckinRequest(BaseModel):
    """Check-in de energia."""
    level: int = Field(..., ge=1, le=10, description="Nível de energia (1-10)")
    notes: Optional[str] = Field(None, max_length=500)


class MoodCheckinRequest(BaseModel):
    """Check-in de humor."""
    mood: str = Field(..., description="Humor (emoji ou texto: happy, sad, neutral, tired, excited)")
    notes: Optional[str] = Field(None, max_length=500)


class SleepCheckinRequest(BaseModel):
    """Check-in de sono."""
    hours: float = Field(..., ge=0, le=24, description="Horas dormidas")
    quality: Optional[int] = Field(None, ge=1, le=10, description="Qualidade do sono (1-10)")
    notes: Optional[str] = Field(None, max_length=500)


class WorkoutCheckinRequest(BaseModel):
    """Check-in de treino."""
    workout_type: str = Field(..., description="Tipo de treino (corrida, musculação, yoga, etc)")
    duration_minutes: int = Field(..., ge=1, le=480, description="Duração em minutos")
    intensity: Optional[str] = Field(None, description="Intensidade: low, medium, high")
    notes: Optional[str] = Field(None, max_length=500)


class QuickCheckinRequest(BaseModel):
    """Check-in rápido."""
    energy: Optional[int] = Field(None, ge=1, le=10)
    mood: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)


class CustomCheckinRequest(BaseModel):
    """Check-in customizado."""
    checkin_type: str = Field(..., description="Tipo do check-in")
    value: Any = Field(..., description="Valor (número, texto ou objeto)")
    notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict] = None


class CheckinResponse(BaseModel):
    """Response de check-in."""
    success: bool
    checkin_type: str
    value: Any
    id: Optional[str] = None
    message: Optional[str] = None


class CheckinStatsResponse(BaseModel):
    """Response de estatísticas."""
    type: str
    period_days: int
    count: int
    average: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    trend: Optional[str] = None
    values: Optional[List[float]] = None


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/energy", response_model=CheckinResponse)
async def checkin_energy(
    request: EnergyCheckinRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Registra check-in de energia.
    
    Escala: 1 (exausto) a 10 (máxima energia)
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.checkin_energy(
            user_id=target_user_id,
            level=request.level,
            notes=request.notes
        )
        
        return CheckinResponse(
            success=True,
            checkin_type="energy",
            value=request.level,
            id=result.get("id"),
            message=f"Energia registrada: {request.level}/10"
        )
    except Exception as e:
        logger.error("checkin_energy_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mood", response_model=CheckinResponse)
async def checkin_mood(
    request: MoodCheckinRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Registra check-in de humor.
    
    Aceita emojis ou texto:
    - 😊 / happy / feliz
    - 😐 / neutral / normal
    - 😢 / sad / triste
    - 😤 / angry / irritado
    - 😴 / tired / cansado
    - 🤩 / excited / empolgado
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.checkin_mood(
            user_id=target_user_id,
            mood=request.mood,
            notes=request.notes
        )
        
        return CheckinResponse(
            success=True,
            checkin_type="mood",
            value=result.get("value"),
            id=result.get("id"),
            message=f"Humor registrado: {request.mood}"
        )
    except Exception as e:
        logger.error("checkin_mood_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sleep", response_model=CheckinResponse)
async def checkin_sleep(
    request: SleepCheckinRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Registra check-in de sono.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.checkin_sleep(
            user_id=target_user_id,
            hours=request.hours,
            quality=request.quality,
            notes=request.notes
        )
        
        return CheckinResponse(
            success=True,
            checkin_type="sleep",
            value=result.get("value"),
            id=result.get("id"),
            message=f"Sono registrado: {request.hours}h"
        )
    except Exception as e:
        logger.error("checkin_sleep_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workout", response_model=CheckinResponse)
async def checkin_workout(
    request: WorkoutCheckinRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Registra check-in de treino.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.checkin_workout(
            user_id=target_user_id,
            workout_type=request.workout_type,
            duration_minutes=request.duration_minutes,
            intensity=request.intensity,
            notes=request.notes
        )
        
        return CheckinResponse(
            success=True,
            checkin_type="workout",
            value=result.get("value"),
            id=result.get("id"),
            message=f"Treino registrado: {request.workout_type} ({request.duration_minutes}min)"
        )
    except Exception as e:
        logger.error("checkin_workout_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick", response_model=Dict[str, Any])
async def quick_checkin(
    request: QuickCheckinRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Check-in rápido (energia + humor de uma vez).
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    if not request.energy and not request.mood:
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos energy ou mood"
        )
    
    try:
        result = await checkin_service.quick_checkin(
            user_id=target_user_id,
            energy=request.energy,
            mood=request.mood,
            notes=request.notes
        )
        
        return {
            "success": True,
            "checkins": result["checkins"],
            "message": f"Check-in registrado"
        }
    except Exception as e:
        logger.error("quick_checkin_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=CheckinResponse)
async def custom_checkin(
    request: CustomCheckinRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Check-in customizado para qualquer tipo de registro.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.create_checkin(
            user_id=target_user_id,
            checkin_type=request.checkin_type,
            value=request.value,
            notes=request.notes,
            metadata=request.metadata
        )
        
        return CheckinResponse(
            success=True,
            checkin_type=request.checkin_type,
            value=request.value,
            id=result.get("id"),
            message=f"Check-in {request.checkin_type} registrado"
        )
    except Exception as e:
        logger.error("custom_checkin_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Dict[str, Any]])
async def list_checkins(
    checkin_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Lista check-ins do usuário.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.get_checkins(
            user_id=target_user_id,
            checkin_type=checkin_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return result
    except Exception as e:
        logger.error("list_checkins_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today", response_model=Dict[str, Any])
async def get_today_checkins(
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Retorna check-ins de hoje.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        result = await checkin_service.get_today_checkins(target_user_id)
        return {
            "date": date.today().isoformat(),
            "checkins": result
        }
    except Exception as e:
        logger.error("get_today_checkins_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{checkin_type}", response_model=CheckinStatsResponse)
async def get_checkin_stats(
    checkin_type: str,
    days: int = Query(7, ge=1, le=90, description="Período em dias"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Retorna estatísticas de check-ins.
    
    Inclui:
    - Média
    - Mínimo/Máximo
    - Tendência (up, down, stable)
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        stats = await checkin_service.get_checkin_stats(
            user_id=target_user_id,
            checkin_type=checkin_type,
            days=days
        )
        
        return CheckinStatsResponse(**stats)
    except Exception as e:
        logger.error("get_checkin_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=Dict[str, Any])
async def get_daily_summary(
    target_date: Optional[date] = Query(None, description="Data (padrão: hoje)"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Retorna resumo diário com todos os check-ins.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        summary = await checkin_service.get_daily_summary(
            user_id=target_user_id,
            target_date=target_date
        )
        
        return summary
    except Exception as e:
        logger.error("get_daily_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
