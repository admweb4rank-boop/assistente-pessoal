"""
TB Personal OS - Calendar Endpoints
API para Google Calendar
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import structlog

from app.services.google_calendar_service import google_calendar_service
from app.api.v1.dependencies.auth import require_api_key
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ==========================================
# SCHEMAS
# ==========================================

class CreateEventRequest(BaseModel):
    """Request para criar evento."""
    title: str = Field(..., min_length=1, max_length=200)
    start_time: datetime
    end_time: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=500)
    all_day: bool = False
    reminders: Optional[List[int]] = Field(
        None,
        description="Minutos antes para lembrete (ex: [10, 30, 60])"
    )
    calendar_id: str = "primary"


class QuickAddRequest(BaseModel):
    """Request para quick add."""
    text: str = Field(..., description="Texto em linguagem natural. Ex: 'Reunião amanhã às 14h'")
    calendar_id: str = "primary"


class UpdateEventRequest(BaseModel):
    """Request para atualizar evento."""
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None


class CalendarResponse(BaseModel):
    """Response de calendário."""
    id: str
    summary: str
    primary: bool
    background_color: Optional[str] = None


class EventResponse(BaseModel):
    """Response de evento."""
    id: str
    title: str
    start: str
    end: Optional[str] = None
    all_day: bool
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    html_link: Optional[str] = None


# ==========================================
# ENDPOINTS - CALENDARS
# ==========================================

@router.get("/calendars", response_model=List[CalendarResponse])
async def list_calendars(
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Lista calendários do usuário.
    Requer conexão Google ativa.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        calendars = await google_calendar_service.list_calendars(target_user_id)
        return [CalendarResponse(**cal) for cal in calendars]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("list_calendars_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINTS - EVENTS READ
# ==========================================

@router.get("/events/today", response_model=List[EventResponse])
async def get_today_events(
    calendar_id: str = Query("primary"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Obtém eventos de hoje.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        events = await google_calendar_service.get_today_events(
            target_user_id,
            calendar_id
        )
        return [EventResponse(**e) for e in events]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_today_events_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(
    hours: int = Query(24, ge=1, le=168, description="Próximas X horas"),
    calendar_id: str = Query("primary"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Obtém eventos das próximas X horas.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        events = await google_calendar_service.get_upcoming_events(
            target_user_id,
            hours=hours,
            calendar_id=calendar_id
        )
        return [EventResponse(**e) for e in events]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_upcoming_events_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/week", response_model=List[EventResponse])
async def get_week_events(
    calendar_id: str = Query("primary"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Obtém eventos da semana.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        events = await google_calendar_service.get_week_events(
            target_user_id,
            calendar_id
        )
        return [EventResponse(**e) for e in events]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_week_events_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=List[EventResponse])
async def get_events_range(
    start_date: date = Query(..., description="Data inicial"),
    end_date: date = Query(..., description="Data final"),
    calendar_id: str = Query("primary"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Obtém eventos em um período.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        
        events = await google_calendar_service.get_events_range(
            target_user_id,
            start,
            end,
            calendar_id
        )
        return [EventResponse(**e) for e in events]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_events_range_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINTS - EVENTS WRITE
# ==========================================

@router.post("/events", response_model=EventResponse)
async def create_event(
    request: CreateEventRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Cria um evento no calendário.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        event = await google_calendar_service.create_event(
            user_id=target_user_id,
            title=request.title,
            start_time=request.start_time,
            end_time=request.end_time,
            description=request.description,
            location=request.location,
            calendar_id=request.calendar_id,
            all_day=request.all_day,
            reminders=request.reminders
        )
        return EventResponse(**event)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("create_event_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/quick", response_model=EventResponse)
async def quick_add_event(
    request: QuickAddRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Adiciona evento usando linguagem natural.
    
    Exemplos:
    - "Reunião com João amanhã às 14h"
    - "Dentista sexta às 10h"
    - "Call com cliente 20/01 às 15:30"
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        event = await google_calendar_service.quick_add(
            user_id=target_user_id,
            text=request.text,
            calendar_id=request.calendar_id
        )
        return EventResponse(**event)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("quick_add_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    calendar_id: str = Query("primary"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Atualiza um evento.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    
    try:
        event = await google_calendar_service.update_event(
            user_id=target_user_id,
            event_id=event_id,
            updates=updates,
            calendar_id=calendar_id
        )
        return EventResponse(**event)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("update_event_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    calendar_id: str = Query("primary"),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Deleta um evento.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        success = await google_calendar_service.delete_event(
            user_id=target_user_id,
            event_id=event_id,
            calendar_id=calendar_id
        )
        
        if success:
            return {"success": True, "message": "Evento deletado"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao deletar evento")
            
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("delete_event_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
