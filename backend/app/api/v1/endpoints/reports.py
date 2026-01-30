"""
Reports API Endpoints
Endpoints para geração de relatórios (Semanal, Mensal, Trimestral, Anual)
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from enum import Enum

from app.api.v1.dependencies.auth import get_current_user
from app.services.report_service import report_service, ReportType

router = APIRouter(prefix="/reports", tags=["reports"])


# =============================================
# SCHEMAS
# =============================================

class ReportRequest(BaseModel):
    send_telegram: bool = True


class WeeklyReportRequest(ReportRequest):
    week: Optional[int] = None  # 1-52
    year: Optional[int] = None


class MonthlyReportRequest(ReportRequest):
    month: Optional[int] = None  # 1-12
    year: Optional[int] = None


class QuarterlyReportRequest(ReportRequest):
    quarter: Optional[int] = None  # 1-4
    year: Optional[int] = None


class AnnualReportRequest(ReportRequest):
    year: Optional[int] = None


# =============================================
# WEEKLY REPORTS
# =============================================

@router.post("/weekly")
async def generate_weekly_report(
    request: WeeklyReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório semanal."""
    try:
        result = await report_service.get_weekly_report(
            user_id=current_user["id"],
            week_number=request.week,
            year=request.year
        )
        
        if result.get("success") and request.send_telegram:
            background_tasks.add_task(
                report_service.send_via_telegram,
                current_user["id"],
                result["message"]
            )
        
        return {
            "success": True,
            "type": "weekly",
            "data": result.get("data"),
            "telegram_sent": request.send_telegram
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly/{year}/{week}")
async def get_weekly_report(
    year: int,
    week: int,
    current_user: dict = Depends(get_current_user)
):
    """Busca relatório semanal específico."""
    if week < 1 or week > 53:
        raise HTTPException(status_code=400, detail="Semana inválida (1-53)")
    
    try:
        result = await report_service.get_weekly_report(
            user_id=current_user["id"],
            week_number=week,
            year=year
        )
        return {"success": True, "data": result.get("data")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# MONTHLY REPORTS
# =============================================

@router.post("/monthly")
async def generate_monthly_report(
    request: MonthlyReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório mensal."""
    try:
        result = await report_service.get_monthly_report(
            user_id=current_user["id"],
            month=request.month,
            year=request.year
        )
        
        if result.get("success") and request.send_telegram:
            background_tasks.add_task(
                report_service.send_via_telegram,
                current_user["id"],
                result["message"]
            )
        
        return {
            "success": True,
            "type": "monthly",
            "data": result.get("data"),
            "telegram_sent": request.send_telegram
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly/{year}/{month}")
async def get_monthly_report(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user)
):
    """Busca relatório mensal específico."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mês inválido (1-12)")
    
    if year < 2020 or year > date.today().year + 1:
        raise HTTPException(status_code=400, detail="Ano inválido")
    
    try:
        result = await report_service.get_monthly_report(
            user_id=current_user["id"],
            month=month,
            year=year
        )
        return {"success": True, "data": result.get("data")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-month")
async def get_current_month_report(
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório do mês atual (parcial)."""
    today = date.today()
    
    try:
        result = await report_service.get_monthly_report(
            user_id=current_user["id"],
            month=today.month,
            year=today.year
        )
        
        return {
            "success": True,
            "data": result.get("data"),
            "note": "Relatório parcial do mês em andamento"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# QUARTERLY REPORTS
# =============================================

@router.post("/quarterly")
async def generate_quarterly_report(
    request: QuarterlyReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório trimestral."""
    try:
        result = await report_service.get_quarterly_report(
            user_id=current_user["id"],
            quarter=request.quarter,
            year=request.year
        )
        
        if result.get("success") and request.send_telegram:
            background_tasks.add_task(
                report_service.send_via_telegram,
                current_user["id"],
                result["message"]
            )
        
        return {
            "success": True,
            "type": "quarterly",
            "data": result.get("data"),
            "telegram_sent": request.send_telegram
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quarterly/{year}/{quarter}")
async def get_quarterly_report(
    year: int,
    quarter: int,
    current_user: dict = Depends(get_current_user)
):
    """Busca relatório trimestral específico."""
    if quarter < 1 or quarter > 4:
        raise HTTPException(status_code=400, detail="Trimestre inválido (1-4)")
    
    try:
        result = await report_service.get_quarterly_report(
            user_id=current_user["id"],
            quarter=quarter,
            year=year
        )
        return {"success": True, "data": result.get("data")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# ANNUAL REPORTS
# =============================================

@router.post("/annual")
async def generate_annual_report(
    request: AnnualReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório anual."""
    try:
        result = await report_service.get_annual_report(
            user_id=current_user["id"],
            year=request.year
        )
        
        if result.get("success") and request.send_telegram:
            background_tasks.add_task(
                report_service.send_via_telegram,
                current_user["id"],
                result["message"]
            )
        
        return {
            "success": True,
            "type": "annual",
            "data": result.get("data"),
            "telegram_sent": request.send_telegram
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annual/{year}")
async def get_annual_report(
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """Busca relatório anual específico."""
    if year < 2020 or year > date.today().year:
        raise HTTPException(status_code=400, detail="Ano inválido")
    
    try:
        result = await report_service.get_annual_report(
            user_id=current_user["id"],
            year=year
        )
        return {"success": True, "data": result.get("data")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# CURRENT PERIOD REPORTS
# =============================================

@router.get("/current-week")
async def get_current_week_report(
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório da semana atual (parcial)."""
    today = date.today()
    week = today.isocalendar()[1]
    
    try:
        result = await report_service.get_weekly_report(
            user_id=current_user["id"],
            week_number=week,
            year=today.year
        )
        return {
            "success": True,
            "data": result.get("data"),
            "note": "Relatório parcial da semana em andamento"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-quarter")
async def get_current_quarter_report(
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório do trimestre atual (parcial)."""
    today = date.today()
    quarter = (today.month - 1) // 3 + 1
    
    try:
        result = await report_service.get_quarterly_report(
            user_id=current_user["id"],
            quarter=quarter,
            year=today.year
        )
        return {
            "success": True,
            "data": result.get("data"),
            "note": "Relatório parcial do trimestre em andamento"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-year")
async def get_current_year_report(
    current_user: dict = Depends(get_current_user)
):
    """Gera relatório do ano atual (parcial)."""
    today = date.today()
    
    try:
        result = await report_service.get_annual_report(
            user_id=current_user["id"],
            year=today.year
        )
        return {
            "success": True,
            "data": result.get("data"),
            "note": "Relatório parcial do ano em andamento"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
