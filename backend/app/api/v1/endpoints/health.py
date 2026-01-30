"""
TB Personal OS - Health API Endpoints
Endpoints para sistema de saúde pessoal
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.v1.dependencies.auth import get_current_user
from app.services.health_service import health_service

router = APIRouter(prefix="/health", tags=["health"])


# ==============================
# SCHEMAS
# ==============================
class CheckinCreate(BaseModel):
    """Schema para criar check-in."""
    checkin_type: str = Field(..., description="Tipo: morning, evening, health, mood, exercise, nutrition")
    data: dict = Field(..., description="Dados do check-in")
    
    class Config:
        schema_extra = {
            "example": {
                "checkin_type": "morning",
                "data": {
                    "sleep_hours": 7.5,
                    "sleep_quality": 8,
                    "energy": 7,
                    "mood": 8,
                    "intentions": ["Finalizar projeto X", "Exercício 30min"]
                }
            }
        }


class HealthGoalCreate(BaseModel):
    """Schema para criar meta de saúde."""
    goal_type: str = Field(..., description="Tipo: sleep, steps, water, exercise, etc")
    target_value: float = Field(..., gt=0, description="Valor alvo")
    unit: str = Field(..., description="Unidade: hours, steps, ml, minutes")
    frequency: str = Field("daily", description="Frequência: daily, weekly")
    description: Optional[str] = Field(None, description="Descrição")
    
    class Config:
        schema_extra = {
            "example": {
                "goal_type": "sleep",
                "target_value": 7.5,
                "unit": "hours",
                "frequency": "daily",
                "description": "Dormir pelo menos 7.5 horas por noite"
            }
        }


class HealthGoalUpdate(BaseModel):
    """Schema para atualizar meta."""
    target_value: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ==============================
# CHECK-INS
# ==============================
@router.post("/checkins", summary="Criar check-in de saúde")
async def create_checkin(
    body: CheckinCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um novo check-in de saúde.
    
    Tipos disponíveis:
    - **morning**: Check-in matinal (sono, energia, intenções)
    - **evening**: Check-in noturno (produtividade, gratidão, reflexões)
    - **health**: Métricas gerais de saúde
    - **mood**: Registro de humor
    - **exercise**: Registro de exercícios
    - **nutrition**: Registro de alimentação
    """
    return await health_service.create_checkin(
        user_id=current_user["id"],
        checkin_type=body.checkin_type,
        data=body.data
    )


@router.get("/checkins", summary="Listar check-ins")
async def list_checkins(
    checkin_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Lista check-ins do usuário."""
    return await health_service.get_checkins(
        user_id=current_user["id"],
        checkin_type=checkin_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/checkins/streak", summary="Obter streak de check-ins")
async def get_checkin_streak(
    checkin_type: str = Query("morning", description="Tipo de check-in"),
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna streak atual e máximo de check-ins consecutivos.
    """
    return await health_service.get_checkin_streak(
        user_id=current_user["id"],
        checkin_type=checkin_type
    )


# ==============================
# METAS DE SAÚDE
# ==============================
@router.post("/goals", summary="Criar meta de saúde")
async def create_health_goal(
    body: HealthGoalCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria uma nova meta de saúde.
    
    Tipos comuns:
    - **sleep**: Horas de sono
    - **steps**: Passos diários
    - **water**: Hidratação (ml)
    - **exercise**: Minutos de exercício
    - **meditation**: Minutos de meditação
    """
    return await health_service.create_health_goal(
        user_id=current_user["id"],
        goal_type=body.goal_type,
        target_value=body.target_value,
        unit=body.unit,
        frequency=body.frequency,
        description=body.description
    )


@router.get("/goals", summary="Listar metas de saúde")
async def list_health_goals(
    active_only: bool = Query(True, description="Apenas metas ativas"),
    current_user: dict = Depends(get_current_user)
):
    """Lista metas de saúde do usuário."""
    return await health_service.get_health_goals(
        user_id=current_user["id"],
        active_only=active_only
    )


@router.patch("/goals/{goal_id}", summary="Atualizar meta")
async def update_health_goal(
    goal_id: UUID,
    body: HealthGoalUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza uma meta de saúde."""
    updates = body.dict(exclude_unset=True)
    return await health_service.update_health_goal(
        user_id=current_user["id"],
        goal_id=goal_id,
        **updates
    )


@router.get("/goals/{goal_id}/progress", summary="Progresso da meta")
async def get_goal_progress(
    goal_id: UUID,
    period_days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna progresso detalhado de uma meta.
    
    Inclui:
    - Porcentagem de progresso
    - Média no período
    - Dias em que a meta foi atingida
    - Taxa de adesão
    """
    return await health_service.get_goal_progress(
        user_id=current_user["id"],
        goal_id=goal_id,
        period_days=period_days
    )


# ==============================
# CORRELAÇÕES E TENDÊNCIAS
# ==============================
@router.get("/correlations", summary="Listar correlações descobertas")
async def list_correlations(
    current_user: dict = Depends(get_current_user)
):
    """
    Lista correlações descobertas entre métricas de saúde.
    
    As correlações são calculadas automaticamente após cada check-in
    quando há dados suficientes (mínimo 7 dias).
    
    Exemplos de correlações:
    - Sono vs Produtividade
    - Exercício vs Humor
    - Hidratação vs Energia
    """
    return await health_service.get_correlations(
        user_id=current_user["id"]
    )


@router.get("/trends/{metric}", summary="Tendência de uma métrica")
async def get_health_trend(
    metric: str,
    period_days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Analisa tendência de uma métrica de saúde.
    
    Retorna:
    - Tendência (improving, stable, declining)
    - Estatísticas (média, min, max)
    - Comparação entre períodos
    """
    return await health_service.get_health_trends(
        user_id=current_user["id"],
        metric=metric,
        period_days=period_days
    )


@router.get("/summary", summary="Resumo de saúde")
async def get_health_summary(
    period_days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """
    Gera um resumo completo de saúde do usuário.
    
    Inclui:
    - Médias de todas as métricas
    - Streak de check-ins
    - Metas ativas
    - Correlações significativas
    - Insights personalizados
    """
    return await health_service.get_health_summary(
        user_id=current_user["id"],
        period_days=period_days
    )
