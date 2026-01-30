"""
TB Personal OS - Scheduler Endpoints
Gerenciamento de rotinas automáticas
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

from app.services.scheduler_service import scheduler_service, init_default_schedules
from app.api.v1.dependencies.auth import get_current_user_id, require_api_key
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


# ==========================================
# SCHEMAS
# ==========================================

class ScheduleRoutineRequest(BaseModel):
    """Request para agendar rotina."""
    routine_type: str = Field(..., description="Tipo: morning, night, weekly")
    hour: int = Field(default=7, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    day_of_week: Optional[str] = Field(default="sun", description="Para weekly: mon,tue,wed,thu,fri,sat,sun")


class ScheduleResponse(BaseModel):
    """Response de agendamento."""
    success: bool
    job_id: str
    schedule: str
    next_run: Optional[str] = None


class JobInfo(BaseModel):
    """Informações de um job."""
    job_id: str
    type: str
    schedule: str
    next_run: Optional[str] = None
    user_id: Optional[str] = None


class RunJobRequest(BaseModel):
    """Request para executar job manualmente."""
    routine_type: str = Field(..., description="morning, night, ou weekly")


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/init", response_model=Dict[str, Any])
async def initialize_schedules(
    _: str = Depends(require_api_key)
):
    """
    Inicializa as rotinas padrão para o owner.
    Chamado automaticamente no startup, mas pode ser forçado.
    """
    try:
        init_default_schedules()
        jobs = scheduler_service.get_scheduled_jobs()
        
        return {
            "success": True,
            "message": "Rotinas inicializadas",
            "jobs": jobs
        }
    except Exception as e:
        logger.error("init_schedules_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobInfo])
async def list_scheduled_jobs(
    user_id: Optional[str] = Query(None),
    _: str = Depends(require_api_key)
):
    """Lista todos os jobs agendados."""
    try:
        jobs = scheduler_service.get_scheduled_jobs(user_id)
        
        return [
            JobInfo(
                job_id=job_id,
                type=info.get("type", "unknown"),
                schedule=info.get("schedule", ""),
                next_run=info.get("next_run"),
                user_id=info.get("user_id")
            )
            for job_id, info in jobs.items()
        ]
    except Exception as e:
        logger.error("list_jobs_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule", response_model=ScheduleResponse)
async def schedule_routine(
    request: ScheduleRoutineRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Agenda uma rotina para o usuário.
    
    Tipos disponíveis:
    - morning: Rotina da manhã (resumo do dia, tarefas, check-in)
    - night: Rotina da noite (review do dia, planejamento)
    - weekly: Planejamento semanal (domingo por padrão)
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        if request.routine_type == "morning":
            job_id = scheduler_service.schedule_morning_routine(
                target_user_id,
                hour=request.hour,
                minute=request.minute
            )
        elif request.routine_type == "night":
            job_id = scheduler_service.schedule_night_routine(
                target_user_id,
                hour=request.hour,
                minute=request.minute
            )
        elif request.routine_type == "weekly":
            job_id = scheduler_service.schedule_weekly_planning(
                target_user_id,
                day_of_week=request.day_of_week or "sun",
                hour=request.hour,
                minute=request.minute
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de rotina inválido: {request.routine_type}. Use: morning, night, weekly"
            )
        
        job_info = scheduler_service.get_scheduled_jobs().get(job_id, {})
        
        return ScheduleResponse(
            success=True,
            job_id=job_id,
            schedule=job_info.get("schedule", f"{request.hour:02d}:{request.minute:02d}"),
            next_run=job_info.get("next_run")
        )
        
    except Exception as e:
        logger.error("schedule_routine_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=Dict[str, Any])
async def run_routine_now(
    request: RunJobRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Executa uma rotina imediatamente (para testes).
    
    Útil para:
    - Testar se a rotina está funcionando
    - Forçar envio de resumo
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        success = scheduler_service.run_job_now(
            job_type=request.routine_type,
            user_id=target_user_id
        )
        
        if success:
            return {
                "success": True,
                "message": f"Rotina {request.routine_type} executada",
                "user_id": target_user_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Falha ao executar rotina: {request.routine_type}"
            )
            
    except Exception as e:
        logger.error("run_routine_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    _: str = Depends(require_api_key)
):
    """Cancela um job agendado."""
    try:
        success = scheduler_service.cancel_job(job_id)
        
        if success:
            return {"success": True, "message": f"Job {job_id} cancelado"}
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
    except Exception as e:
        logger.error("cancel_job_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def scheduler_status(
    _: str = Depends(require_api_key)
):
    """Retorna status do scheduler."""
    try:
        jobs = scheduler_service.get_scheduled_jobs()
        running = scheduler_service.scheduler.running if scheduler_service._scheduler else False
        
        return {
            "running": running,
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error("get_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
