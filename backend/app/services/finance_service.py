"""
TB Personal OS - Finance Service
Gerenciamento de finanças pessoais (entradas, saídas, recorrências)
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID
import pytz

from supabase import Client, create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class FinanceService:
    """
    Serviço para gerenciamento de finanças.
    Gerencia transações, recorrências e análises.
    """
    
    def __init__(self, supabase: Optional[Client] = None):
        self._supabase = supabase
    
    @property
    def supabase(self) -> Client:
        """Lazy load Supabase client."""
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    # ==========================================
    # TRANSACTIONS - CRUD
    # ==========================================
    
    async def create_transaction(
        self,
        user_id: str,
        transaction_type: str,
        amount: float,
        description: str,
        category: Optional[str] = None,
        transaction_date: Optional[date] = None,
        project_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_rule: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma nova transação.
        
        Args:
            user_id: ID do usuário
            transaction_type: 'income' ou 'expense'
            amount: Valor (sempre positivo)
            description: Descrição da transação
            category: Categoria (salary, client_payment, subscription, food, etc)
            transaction_date: Data da transação
            project_id: Projeto relacionado (opcional)
            contact_id: Contato relacionado (opcional)
            is_recurring: Se é transação recorrente
            recurrence_rule: Regra de recorrência (monthly, weekly, etc)
            tags: Tags para organização
            
        Returns:
            Transação criada
        """
        try:
            if transaction_type not in ["income", "expense"]:
                raise ValueError("transaction_type deve ser 'income' ou 'expense'")
            
            if amount <= 0:
                raise ValueError("amount deve ser positivo")
            
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            if not transaction_date:
                transaction_date = datetime.now(tz).date()
            
            data = {
                "user_id": user_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "description": description,
                "category": category,
                "transaction_date": transaction_date.isoformat(),
                "project_id": project_id,
                "contact_id": contact_id,
                "is_recurring": is_recurring,
                "recurrence_rule": recurrence_rule,
                "tags": tags or []
            }
            
            result = self.supabase.table("transactions").insert(data).execute()
            
            if result.data:
                logger.info(
                    "transaction_created",
                    user_id=user_id,
                    type=transaction_type,
                    amount=amount,
                    transaction_id=result.data[0]["id"]
                )
                return result.data[0]
            
            raise ValueError("Falha ao criar transação")
            
        except Exception as e:
            logger.error("create_transaction_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_transactions(
        self,
        user_id: str,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista transações com filtros."""
        try:
            query = self.supabase.table("transactions") \
                .select("*, projects(name), contacts(name)") \
                .eq("user_id", user_id) \
                .order("transaction_date", desc=True)
            
            if transaction_type:
                query = query.eq("transaction_type", transaction_type)
            if category:
                query = query.eq("category", category)
            if start_date:
                query = query.gte("transaction_date", start_date.isoformat())
            if end_date:
                query = query.lte("transaction_date", end_date.isoformat())
            if project_id:
                query = query.eq("project_id", project_id)
            
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error("get_transactions_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_transaction(self, user_id: str, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Obtém uma transação específica."""
        try:
            result = self.supabase.table("transactions") \
                .select("*, projects(name), contacts(name)") \
                .eq("id", transaction_id) \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error("get_transaction_failed", user_id=user_id, transaction_id=transaction_id, error=str(e))
            return None
    
    async def update_transaction(
        self,
        user_id: str,
        transaction_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Atualiza uma transação."""
        try:
            valid_fields = ["transaction_type", "amount", "description", "category",
                          "transaction_date", "project_id", "contact_id", "is_recurring",
                          "recurrence_rule", "tags"]
            data = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
            
            if "transaction_date" in data and isinstance(data["transaction_date"], date):
                data["transaction_date"] = data["transaction_date"].isoformat()
            
            data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("transactions") \
                .update(data) \
                .eq("id", transaction_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("transaction_updated", user_id=user_id, transaction_id=transaction_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("update_transaction_failed", user_id=user_id, transaction_id=transaction_id, error=str(e))
            raise
    
    async def delete_transaction(self, user_id: str, transaction_id: str) -> bool:
        """Deleta uma transação."""
        try:
            result = self.supabase.table("transactions") \
                .delete() \
                .eq("id", transaction_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("transaction_deleted", user_id=user_id, transaction_id=transaction_id)
                return True
            return False
            
        except Exception as e:
            logger.error("delete_transaction_failed", user_id=user_id, transaction_id=transaction_id, error=str(e))
            raise
    
    # ==========================================
    # SUMMARY & ANALYTICS
    # ==========================================
    
    async def get_summary(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtém resumo financeiro do período.
        
        Args:
            user_id: ID do usuário
            start_date: Data inicial (default: início do mês)
            end_date: Data final (default: hoje)
            
        Returns:
            Resumo com totais e saldo
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            if not start_date:
                start_date = now.replace(day=1).date()
            if not end_date:
                end_date = now.date()
            
            # Buscar todas as transações do período
            transactions = await self.get_transactions(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            total_income = 0.0
            total_expense = 0.0
            by_category = {}
            
            for t in transactions:
                amount = float(t["amount"])
                category = t.get("category") or "other"
                
                if t["transaction_type"] == "income":
                    total_income += amount
                else:
                    total_expense += amount
                
                if category not in by_category:
                    by_category[category] = {"income": 0, "expense": 0}
                by_category[category][t["transaction_type"]] += amount
            
            balance = total_income - total_expense
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "balance": round(balance, 2),
                "transaction_count": len(transactions),
                "by_category": by_category,
                "status": "positive" if balance >= 0 else "negative"
            }
            
        except Exception as e:
            logger.error("get_summary_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_monthly_comparison(
        self,
        user_id: str,
        months: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Obtém comparação mensal dos últimos X meses.
        
        Args:
            user_id: ID do usuário
            months: Quantidade de meses para comparar
            
        Returns:
            Lista com resumo de cada mês
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            results = []
            
            for i in range(months):
                # Calcular mês
                month_date = (now - timedelta(days=30 * i))
                start = month_date.replace(day=1).date()
                
                # Último dia do mês
                if month_date.month == 12:
                    end = date(month_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
                
                summary = await self.get_summary(
                    user_id=user_id,
                    start_date=start,
                    end_date=end
                )
                
                summary["month"] = month_date.strftime("%Y-%m")
                summary["month_name"] = month_date.strftime("%B %Y")
                results.append(summary)
            
            return results
            
        except Exception as e:
            logger.error("get_monthly_comparison_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_recurring_transactions(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Lista transações recorrentes."""
        try:
            result = self.supabase.table("transactions") \
                .select("*, projects(name), contacts(name)") \
                .eq("user_id", user_id) \
                .eq("is_recurring", True) \
                .order("transaction_date", desc=True) \
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error("get_recurring_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_category_breakdown(
        self,
        user_id: str,
        transaction_type: str = "expense",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtém breakdown por categoria.
        
        Args:
            user_id: ID do usuário
            transaction_type: 'income' ou 'expense'
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Breakdown com percentuais por categoria
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            if not start_date:
                start_date = now.replace(day=1).date()
            if not end_date:
                end_date = now.date()
            
            transactions = await self.get_transactions(
                user_id=user_id,
                transaction_type=transaction_type,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            by_category = {}
            total = 0.0
            
            for t in transactions:
                amount = float(t["amount"])
                category = t.get("category") or "other"
                
                if category not in by_category:
                    by_category[category] = 0
                by_category[category] += amount
                total += amount
            
            # Calcular percentuais
            breakdown = []
            for category, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                breakdown.append({
                    "category": category,
                    "amount": round(amount, 2),
                    "percentage": round((amount / total * 100), 1) if total > 0 else 0
                })
            
            return {
                "transaction_type": transaction_type,
                "total": round(total, 2),
                "breakdown": breakdown
            }
            
        except Exception as e:
            logger.error("get_category_breakdown_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # ALERTS & PROJECTIONS
    # ==========================================
    
    async def get_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Gera alertas financeiros baseados em análise.
        
        Alertas possíveis:
        - Gastos acima da média
        - Saldo negativo projetado
        - Recorrências próximas
        """
        try:
            alerts = []
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            # Comparar mês atual com média
            current_month = await self.get_summary(
                user_id=user_id,
                start_date=now.replace(day=1).date(),
                end_date=now.date()
            )
            
            # Mês anterior completo
            last_month_end = now.replace(day=1).date() - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            last_month = await self.get_summary(
                user_id=user_id,
                start_date=last_month_start,
                end_date=last_month_end
            )
            
            # Alerta de gastos crescentes
            if last_month["total_expense"] > 0:
                expense_change = ((current_month["total_expense"] - last_month["total_expense"]) 
                                  / last_month["total_expense"] * 100)
                if expense_change > 20:
                    alerts.append({
                        "type": "expense_increase",
                        "severity": "warning",
                        "title": "Gastos acima do mês anterior",
                        "message": f"Seus gastos estão {expense_change:.0f}% maiores que o mês passado",
                        "data": {
                            "current": current_month["total_expense"],
                            "previous": last_month["total_expense"],
                            "change_percent": round(expense_change, 1)
                        }
                    })
            
            # Alerta de saldo negativo
            if current_month["balance"] < 0:
                alerts.append({
                    "type": "negative_balance",
                    "severity": "danger",
                    "title": "Saldo negativo",
                    "message": f"Seu saldo está negativo em R$ {abs(current_month['balance']):.2f}",
                    "data": {
                        "balance": current_month["balance"]
                    }
                })
            
            # Alerta de recorrências
            recurring = await self.get_recurring_transactions(user_id)
            upcoming_expenses = sum(
                float(t["amount"]) 
                for t in recurring 
                if t["transaction_type"] == "expense"
            )
            
            if upcoming_expenses > 0 and current_month["balance"] < upcoming_expenses:
                alerts.append({
                    "type": "recurring_warning",
                    "severity": "warning",
                    "title": "Atenção com recorrências",
                    "message": f"Você tem R$ {upcoming_expenses:.2f} em despesas recorrentes",
                    "data": {
                        "recurring_expenses": upcoming_expenses,
                        "current_balance": current_month["balance"]
                    }
                })
            
            return alerts
            
        except Exception as e:
            logger.error("get_alerts_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_projection(
        self,
        user_id: str,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Projeta saldo futuro baseado em padrões.
        
        Args:
            user_id: ID do usuário
            days_ahead: Dias para projetar
            
        Returns:
            Projeção de saldo
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            # Média diária dos últimos 30 dias
            start_30 = (now - timedelta(days=30)).date()
            summary_30 = await self.get_summary(
                user_id=user_id,
                start_date=start_30,
                end_date=now.date()
            )
            
            avg_daily_income = summary_30["total_income"] / 30
            avg_daily_expense = summary_30["total_expense"] / 30
            avg_daily_balance = avg_daily_income - avg_daily_expense
            
            # Saldo atual
            current_balance = summary_30["balance"]
            
            # Projeção
            projected_balance = current_balance + (avg_daily_balance * days_ahead)
            
            # Recorrências confirmadas
            recurring = await self.get_recurring_transactions(user_id)
            recurring_income = sum(float(t["amount"]) for t in recurring if t["transaction_type"] == "income")
            recurring_expense = sum(float(t["amount"]) for t in recurring if t["transaction_type"] == "expense")
            
            return {
                "current_balance": round(current_balance, 2),
                "days_ahead": days_ahead,
                "projected_balance": round(projected_balance, 2),
                "avg_daily": {
                    "income": round(avg_daily_income, 2),
                    "expense": round(avg_daily_expense, 2),
                    "net": round(avg_daily_balance, 2)
                },
                "recurring_monthly": {
                    "income": round(recurring_income, 2),
                    "expense": round(recurring_expense, 2)
                },
                "projection_date": (now + timedelta(days=days_ahead)).date().isoformat(),
                "trend": "positive" if avg_daily_balance >= 0 else "negative"
            }
            
        except Exception as e:
            logger.error("get_projection_failed", user_id=user_id, error=str(e))
            raise


# Singleton
finance_service = FinanceService()
