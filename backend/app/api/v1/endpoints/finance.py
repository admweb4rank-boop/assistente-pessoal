"""
TB Personal OS - Finance API Endpoints
Endpoints para gerenciamento de finanças
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field
import structlog

from app.api.v1.dependencies.auth import get_current_user
from app.services.finance_service import finance_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/finance", tags=["Finance"])


# ==========================================
# SCHEMAS
# ==========================================

class TransactionCreate(BaseModel):
    """Dados para criar transação."""
    transaction_type: str = Field(..., description="'income' ou 'expense'")
    amount: float = Field(..., gt=0, description="Valor positivo")
    description: str
    category: Optional[str] = None
    transaction_date: Optional[date] = None
    project_id: Optional[str] = None
    contact_id: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    tags: Optional[List[str]] = None


class TransactionUpdate(BaseModel):
    """Dados para atualizar transação."""
    transaction_type: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    category: Optional[str] = None
    transaction_date: Optional[date] = None
    project_id: Optional[str] = None
    contact_id: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    tags: Optional[List[str]] = None


class QuickTransaction(BaseModel):
    """Transação rápida simplificada."""
    type: str = Field(..., description="'in' ou 'out'")
    amount: float = Field(..., gt=0)
    description: str
    category: Optional[str] = None


# ==========================================
# TRANSACTIONS ENDPOINTS
# ==========================================

@router.post("/transactions")
async def create_transaction(
    data: TransactionCreate,
    user: dict = Depends(get_current_user)
):
    """Cria uma nova transação."""
    try:
        transaction = await finance_service.create_transaction(
            user_id=user["id"],
            transaction_type=data.transaction_type,
            amount=data.amount,
            description=data.description,
            category=data.category,
            transaction_date=data.transaction_date,
            project_id=data.project_id,
            contact_id=data.contact_id,
            is_recurring=data.is_recurring,
            recurrence_rule=data.recurrence_rule,
            tags=data.tags
        )
        return transaction
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_transaction_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar transação: {str(e)}")


@router.post("/transactions/quick")
async def create_quick_transaction(
    data: QuickTransaction,
    user: dict = Depends(get_current_user)
):
    """
    Cria transação de forma rápida.
    
    - type: 'in' para entrada, 'out' para saída
    """
    try:
        transaction_type = "income" if data.type == "in" else "expense"
        
        transaction = await finance_service.create_transaction(
            user_id=user["id"],
            transaction_type=transaction_type,
            amount=data.amount,
            description=data.description,
            category=data.category
        )
        return transaction
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("quick_transaction_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar transação: {str(e)}")


@router.get("/transactions")
async def list_transactions(
    transaction_type: Optional[str] = Query(None, description="'income' ou 'expense'"),
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    project_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    """Lista transações com filtros."""
    try:
        transactions = await finance_service.get_transactions(
            user_id=user["id"],
            transaction_type=transaction_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        return {"transactions": transactions, "count": len(transactions)}
        
    except Exception as e:
        logger.error("list_transactions_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao listar transações: {str(e)}")


@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtém uma transação específica."""
    try:
        transaction = await finance_service.get_transaction(user["id"], transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_transaction_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transação: {str(e)}")


@router.patch("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    user: dict = Depends(get_current_user)
):
    """Atualiza uma transação."""
    try:
        transaction = await finance_service.update_transaction(
            user_id=user["id"],
            transaction_id=transaction_id,
            **data.model_dump(exclude_none=True)
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_transaction_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar transação: {str(e)}")


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user: dict = Depends(get_current_user)
):
    """Deleta uma transação."""
    try:
        deleted = await finance_service.delete_transaction(user["id"], transaction_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        return {"status": "success", "message": "Transação deletada"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_transaction_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao deletar transação: {str(e)}")


# ==========================================
# SUMMARY & ANALYTICS
# ==========================================

@router.get("/summary")
async def get_summary(
    start_date: Optional[date] = Query(None, description="Data inicial (default: início do mês)"),
    end_date: Optional[date] = Query(None, description="Data final (default: hoje)"),
    user: dict = Depends(get_current_user)
):
    """Obtém resumo financeiro do período."""
    try:
        summary = await finance_service.get_summary(
            user_id=user["id"],
            start_date=start_date,
            end_date=end_date
        )
        return summary
        
    except Exception as e:
        logger.error("get_summary_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo: {str(e)}")


@router.get("/monthly")
async def get_monthly_comparison(
    months: int = Query(3, ge=1, le=12, description="Quantidade de meses"),
    user: dict = Depends(get_current_user)
):
    """Obtém comparação mensal."""
    try:
        comparison = await finance_service.get_monthly_comparison(
            user_id=user["id"],
            months=months
        )
        return {"months": comparison}
        
    except Exception as e:
        logger.error("get_monthly_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar comparação: {str(e)}")


@router.get("/recurring")
async def get_recurring_transactions(
    user: dict = Depends(get_current_user)
):
    """Lista transações recorrentes."""
    try:
        recurring = await finance_service.get_recurring_transactions(user_id=user["id"])
        return {"recurring": recurring, "count": len(recurring)}
        
    except Exception as e:
        logger.error("get_recurring_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao listar recorrências: {str(e)}")


@router.get("/breakdown")
async def get_category_breakdown(
    transaction_type: str = Query("expense", description="'income' ou 'expense'"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Obtém breakdown por categoria."""
    try:
        breakdown = await finance_service.get_category_breakdown(
            user_id=user["id"],
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        return breakdown
        
    except Exception as e:
        logger.error("get_breakdown_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar breakdown: {str(e)}")


@router.get("/alerts")
async def get_finance_alerts(
    user: dict = Depends(get_current_user)
):
    """Obtém alertas financeiros."""
    try:
        alerts = await finance_service.get_alerts(user_id=user["id"])
        return {"alerts": alerts, "count": len(alerts)}
        
    except Exception as e:
        logger.error("get_alerts_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alertas: {str(e)}")


@router.get("/projection")
async def get_projection(
    days_ahead: int = Query(30, ge=7, le=90, description="Dias para projetar"),
    user: dict = Depends(get_current_user)
):
    """Projeta saldo futuro."""
    try:
        projection = await finance_service.get_projection(
            user_id=user["id"],
            days_ahead=days_ahead
        )
        return projection
        
    except Exception as e:
        logger.error("get_projection_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao projetar: {str(e)}")
