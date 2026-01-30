"""
TB Personal OS - Insights API Endpoints
Endpoints para insights, análises e recomendações
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.api.v1.dependencies.auth import get_current_user_id
from app.services.insights_service import insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


# ==========================================
# PRODUCTIVITY ENDPOINTS
# ==========================================

@router.get("/productivity/score", summary="Score de produtividade")
async def get_productivity_score(
    days: int = Query(7, le=90, description="Período em dias"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Calcula score de produtividade (0-100).
    
    Baseado em:
    - Taxa de conclusão de tarefas
    - Tarefas no prazo
    - Consistência
    
    Níveis:
    - 80+: Excelente
    - 60-79: Bom
    - 40-59: Razoável
    - <40: Precisa melhorar
    """
    try:
        result = await insights_service.get_productivity_score(user_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productivity/daily", summary="Produtividade diária")
async def get_daily_productivity(
    days: int = Query(30, le=90, description="Período em dias"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém dados de produtividade dia a dia.
    
    Útil para gráficos e visualização de tendências.
    """
    try:
        daily = await insights_service.get_daily_productivity(user_id, days)
        return {
            "period_days": days,
            "data": daily,
            "total_days": len(daily)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# PATTERNS ENDPOINTS
# ==========================================

@router.get("/patterns/work-days", summary="Análise de dias de trabalho")
async def analyze_work_days(
    days: int = Query(60, le=90, description="Período de análise"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Analisa quais dias da semana são mais produtivos.
    
    Retorna ranking dos dias com média de tarefas concluídas.
    """
    try:
        result = await insights_service.analyze_best_work_days(user_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/energy", summary="Padrões de energia")
async def analyze_energy_patterns(
    days: int = Query(30, le=90, description="Período de análise"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Analisa padrões de energia baseado em check-ins.
    
    Inclui:
    - Média de energia
    - Melhor/pior dia da semana
    - Distribuição por dia
    """
    try:
        result = await insights_service.analyze_energy_patterns(user_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# CORRELATIONS ENDPOINTS
# ==========================================

@router.get("/correlations/sleep-productivity", summary="Correlação sono x produtividade")
async def analyze_sleep_correlation(
    days: int = Query(30, le=90, description="Período de análise"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Analisa correlação entre sono e produtividade.
    
    Compara produtividade em dias com sono bom (7+ horas)
    vs dias com sono inadequado.
    """
    try:
        result = await insights_service.analyze_sleep_productivity_correlation(user_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# RECOMMENDATIONS ENDPOINTS
# ==========================================

@router.get("/recommendations", summary="Obter recomendações")
async def get_recommendations(
    user_id: str = Depends(get_current_user_id)
):
    """
    Gera recomendações personalizadas.
    
    Baseado em:
    - Tarefas pendentes/atrasadas
    - Níveis de energia
    - Padrões de produtividade
    """
    try:
        recommendations = await insights_service.generate_recommendations(user_id)
        return {
            "total": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# SUMMARY ENDPOINTS
# ==========================================

@router.get("/summary/weekly", summary="Resumo semanal")
async def get_weekly_summary(
    user_id: str = Depends(get_current_user_id)
):
    """
    Gera resumo semanal com insights.
    
    Inclui:
    - Score de produtividade
    - Tarefas criadas/concluídas
    - Melhor dia
    - Top 3 recomendações
    """
    try:
        summary = await insights_service.get_weekly_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/monthly", summary="Relatório mensal")
async def get_monthly_report(
    user_id: str = Depends(get_current_user_id)
):
    """
    Gera relatório mensal detalhado.
    
    Inclui:
    - Score de produtividade
    - Total de tarefas
    - Tendência (melhorando/piorando)
    - Padrões por dia da semana
    - Correlações (sono x produtividade)
    """
    try:
        report = await insights_service.get_monthly_report(user_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# DASHBOARD ENDPOINT
# ==========================================

@router.get("/dashboard", summary="Dashboard completo")
async def get_insights_dashboard(
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém todos os insights para dashboard.
    
    Combina:
    - Score de produtividade
    - Recomendações
    - Padrões principais
    """
    try:
        # Buscar dados em paralelo (conceitualmente)
        productivity = await insights_service.get_productivity_score(user_id, days=7)
        recommendations = await insights_service.generate_recommendations(user_id)
        work_days = await insights_service.analyze_best_work_days(user_id, days=30)
        
        return {
            "productivity_score": productivity.get("score"),
            "productivity_level": productivity.get("label"),
            "metrics": productivity.get("metrics"),
            "best_day": work_days.get("best_day"),
            "recommendations": recommendations[:3],
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
