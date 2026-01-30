"""
Goals API Endpoints
Sistema de objetivos hierárquicos (Macro/Meso/Micro)
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum

from app.api.v1.dependencies.auth import get_current_user
from app.services.goal_service import (
    goal_service, 
    GoalLevel, 
    GoalPeriod, 
    GoalStatus, 
    GoalArea
)

router = APIRouter(prefix="/goals", tags=["goals"])


# =====================
# Schemas
# =====================

class KeyResultCreate(BaseModel):
    description: str
    target: float
    unit: Optional[str] = None


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    level: GoalLevel
    period_type: GoalPeriod
    area: Optional[GoalArea] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    target_value: Optional[float] = None
    key_results: Optional[List[KeyResultCreate]] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    icon: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    area: Optional[GoalArea] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[GoalStatus] = None
    reflection: Optional[str] = None
    lessons_learned: Optional[str] = None


class ProgressUpdate(BaseModel):
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_value: Optional[float] = None


class CheckinCreate(BaseModel):
    progress_delta: Optional[float] = None
    new_progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    blockers: Optional[str] = None
    next_actions: Optional[str] = None
    confidence_level: Optional[int] = Field(None, ge=1, le=5)
    energy_level: Optional[int] = Field(None, ge=1, le=5)


class HabitCreate(BaseModel):
    habit_name: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(default="daily")
    target_per_period: int = Field(default=1, ge=1)
    days_of_week: Optional[List[int]] = None
    description: Optional[str] = None


class HabitComplete(BaseModel):
    notes: Optional[str] = None
    quality: Optional[int] = Field(None, ge=1, le=5)


# =====================
# CRUD Endpoints
# =====================

@router.post("", status_code=201)
async def create_goal(
    goal: GoalCreate,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo objetivo."""
    try:
        key_results = None
        if goal.key_results:
            key_results = [kr.model_dump() for kr in goal.key_results]
        
        result = await goal_service.create_goal(
            user_id=current_user["id"],
            title=goal.title,
            level=goal.level,
            period_type=goal.period_type,
            area=goal.area,
            description=goal.description,
            parent_id=goal.parent_id,
            target_value=goal.target_value,
            key_results=key_results,
            period_start=goal.period_start,
            period_end=goal.period_end,
            icon=goal.icon,
            priority=goal.priority
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_goals(
    level: Optional[GoalLevel] = None,
    status: Optional[GoalStatus] = None,
    area: Optional[GoalArea] = None,
    parent_id: Optional[str] = None,
    period_type: Optional[GoalPeriod] = None,
    current_user: dict = Depends(get_current_user)
):
    """Lista objetivos com filtros opcionais."""
    goals = await goal_service.get_goals(
        user_id=current_user["id"],
        level=level,
        status=status,
        area=area,
        parent_id=parent_id,
        period_type=period_type
    )
    return {"success": True, "data": goals}


@router.get("/summary")
async def get_goals_summary(
    current_user: dict = Depends(get_current_user)
):
    """Retorna resumo dos objetivos."""
    summary = await goal_service.get_summary(current_user["id"])
    return {"success": True, "data": summary}


@router.get("/current")
async def get_current_period_goals(
    current_user: dict = Depends(get_current_user)
):
    """Retorna objetivos do período atual em cada nível."""
    goals = await goal_service.get_current_period_goals(current_user["id"])
    return {"success": True, "data": goals}


@router.get("/tree")
async def get_goals_tree(
    root_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Retorna árvore hierárquica de objetivos."""
    tree = await goal_service.get_goal_tree(
        user_id=current_user["id"],
        root_id=root_id
    )
    return {"success": True, "data": tree}


@router.get("/{goal_id}")
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Busca um objetivo específico."""
    goal = await goal_service.get_goal(goal_id, current_user["id"])
    if not goal:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado")
    return {"success": True, "data": goal}


@router.patch("/{goal_id}")
async def update_goal(
    goal_id: str,
    updates: GoalUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza um objetivo."""
    # Converte para dict removendo Nones
    update_data = {
        k: v.value if isinstance(v, Enum) else v 
        for k, v in updates.model_dump().items() 
        if v is not None
    }
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    
    result = await goal_service.update_goal(
        goal_id=goal_id,
        user_id=current_user["id"],
        updates=update_data
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado")
    
    return {"success": True, "data": result}


@router.patch("/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str,
    progress: ProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza o progresso de um objetivo."""
    result = await goal_service.update_progress(
        goal_id=goal_id,
        user_id=current_user["id"],
        progress_percentage=progress.progress_percentage,
        current_value=progress.current_value
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado")
    
    return {"success": True, "data": result}


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove um objetivo."""
    deleted = await goal_service.delete_goal(goal_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado")
    return {"success": True, "message": "Objetivo removido"}


# =====================
# Check-ins
# =====================

@router.post("/{goal_id}/checkins")
async def add_checkin(
    goal_id: str,
    checkin: CheckinCreate,
    current_user: dict = Depends(get_current_user)
):
    """Adiciona um check-in de objetivo."""
    try:
        result = await goal_service.add_checkin(
            user_id=current_user["id"],
            goal_id=goal_id,
            **checkin.model_dump()
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{goal_id}/checkins")
async def list_checkins(
    goal_id: str,
    limit: int = Query(default=10, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Lista check-ins de um objetivo."""
    checkins = await goal_service.get_checkins(
        goal_id=goal_id,
        user_id=current_user["id"],
        limit=limit
    )
    return {"success": True, "data": checkins}


# =====================
# Hábitos
# =====================

@router.post("/{goal_id}/habits")
async def add_habit(
    goal_id: str,
    habit: HabitCreate,
    current_user: dict = Depends(get_current_user)
):
    """Adiciona um hábito vinculado ao objetivo."""
    # Verifica se objetivo existe
    goal = await goal_service.get_goal(goal_id, current_user["id"])
    if not goal:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado")
    
    try:
        result = await goal_service.add_habit(
            goal_id=goal_id,
            **habit.model_dump()
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{goal_id}/habits")
async def list_habits(
    goal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Lista hábitos de um objetivo."""
    habits = await goal_service.get_habits(goal_id)
    return {"success": True, "data": habits}


@router.post("/habits/{habit_id}/complete")
async def complete_habit(
    habit_id: str,
    completion: HabitComplete,
    current_user: dict = Depends(get_current_user)
):
    """Registra conclusão de um hábito."""
    try:
        result = await goal_service.complete_habit(
            habit_id=habit_id,
            **completion.model_dump()
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================
# Áreas
# =====================

@router.get("/meta/areas")
async def list_areas():
    """Lista áreas de vida disponíveis."""
    areas = [
        {"id": "work", "name": "Trabalho & Projetos", "icon": "💼", "color": "#3b82f6"},
        {"id": "health", "name": "Saúde & Energia", "icon": "💪", "color": "#22c55e"},
        {"id": "finance", "name": "Finanças", "icon": "💰", "color": "#f59e0b"},
        {"id": "relationships", "name": "Relacionamentos", "icon": "❤️", "color": "#ef4444"},
        {"id": "learning", "name": "Aprendizado", "icon": "📚", "color": "#8b5cf6"},
        {"id": "personal", "name": "Pessoal & Identidade", "icon": "✨", "color": "#ec4899"},
        {"id": "content", "name": "Conteúdo & Marca", "icon": "✍️", "color": "#06b6d4"}
    ]
    return {"success": True, "data": areas}
