"""
Report Service - Serviço Unificado de Relatórios
Suporta: Semanal, Mensal, Trimestral, Anual
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import structlog

from app.core.config import settings
from supabase import create_client, Client

logger = structlog.get_logger()


class ReportType(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ReportService:
    """Serviço unificado para geração de relatórios."""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    # =============================================
    # MÉTODOS PÚBLICOS
    # =============================================
    
    async def generate_report(
        self,
        user_id: str,
        report_type: ReportType,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> Dict[str, Any]:
        """Gera relatório do tipo especificado."""
        
        # Calcula período se não fornecido
        if not period_start or not period_end:
            period_start, period_end = self._calculate_period(report_type)
        
        logger.info("generating_report", 
                   user_id=user_id, 
                   type=report_type.value,
                   start=period_start.isoformat(),
                   end=period_end.isoformat())
        
        # Coleta dados base
        base_data = await self._collect_base_data(user_id, period_start, period_end)
        
        # Gera relatório específico por tipo
        if report_type == ReportType.WEEKLY:
            report_data = self._build_weekly_report(base_data, period_start, period_end)
        elif report_type == ReportType.MONTHLY:
            report_data = self._build_monthly_report(base_data, period_start, period_end)
        elif report_type == ReportType.QUARTERLY:
            report_data = await self._build_quarterly_report(user_id, base_data, period_start, period_end)
        else:  # ANNUAL
            report_data = await self._build_annual_report(user_id, base_data, period_start, period_end)
        
        # Gera insights
        report_data["insights"] = self._generate_insights(report_data, report_type)
        
        # Formata mensagem
        report_data["message"] = self._format_message(report_data, report_type)
        
        # Salva relatório
        await self._save_report(user_id, report_type, report_data)
        
        return {
            "success": True,
            "type": report_type.value,
            "data": report_data,
            "message": report_data["message"]
        }
    
    async def get_weekly_report(
        self, 
        user_id: str, 
        week_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gera relatório semanal."""
        if week_number and year:
            # Calcula data a partir da semana
            first_day = date(year, 1, 1)
            start = first_day + timedelta(weeks=week_number - 1)
            start = start - timedelta(days=start.weekday())  # Ajusta para segunda
            end = start + timedelta(days=6)
        else:
            # Semana anterior
            today = date.today()
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
        
        return await self.generate_report(user_id, ReportType.WEEKLY, start, end)
    
    async def get_monthly_report(
        self, 
        user_id: str, 
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gera relatório mensal."""
        if month and year:
            start = date(year, month, 1)
            if month == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
        else:
            # Mês anterior
            today = date.today()
            first_this_month = date(today.year, today.month, 1)
            end = first_this_month - timedelta(days=1)
            start = date(end.year, end.month, 1)
        
        return await self.generate_report(user_id, ReportType.MONTHLY, start, end)
    
    async def get_quarterly_report(
        self, 
        user_id: str, 
        quarter: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gera relatório trimestral."""
        today = date.today()
        
        if quarter and year:
            start_month = (quarter - 1) * 3 + 1
            start = date(year, start_month, 1)
            end_month = start_month + 2
            if end_month == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, end_month + 1, 1) - timedelta(days=1)
        else:
            # Trimestre anterior
            current_quarter = (today.month - 1) // 3 + 1
            if current_quarter == 1:
                year = today.year - 1
                quarter = 4
            else:
                year = today.year
                quarter = current_quarter - 1
            
            start_month = (quarter - 1) * 3 + 1
            start = date(year, start_month, 1)
            end_month = start_month + 2
            if end_month == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, end_month + 1, 1) - timedelta(days=1)
        
        return await self.generate_report(user_id, ReportType.QUARTERLY, start, end)
    
    async def get_annual_report(
        self, 
        user_id: str, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gera relatório anual."""
        if not year:
            year = date.today().year - 1  # Ano anterior
        
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        
        return await self.generate_report(user_id, ReportType.ANNUAL, start, end)
    
    # =============================================
    # COLETA DE DADOS
    # =============================================
    
    async def _collect_base_data(self, user_id: str, start: date, end: date) -> Dict:
        """Coleta dados base para qualquer tipo de relatório."""
        return {
            "tasks": await self._get_tasks_data(user_id, start, end),
            "goals": await self._get_goals_data(user_id, start, end),
            "finances": await self._get_finance_data(user_id, start, end),
            "habits": await self._get_habits_data(user_id, start, end),
            "checkins": await self._get_checkins_data(user_id, start, end),
            "content": await self._get_content_data(user_id, start, end),
            "inbox": await self._get_inbox_data(user_id, start, end)
        }
    
    async def _get_tasks_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados de tarefas."""
        try:
            created = self.supabase.table("tasks").select("id, status, priority").eq(
                "user_id", user_id
            ).gte("created_at", start.isoformat()).lte(
                "created_at", f"{end.isoformat()}T23:59:59"
            ).execute()
            
            completed = self.supabase.table("tasks").select("id").eq(
                "user_id", user_id
            ).eq("status", "completed").gte(
                "completed_at", start.isoformat()
            ).lte("completed_at", f"{end.isoformat()}T23:59:59").execute()
            
            tasks = created.data or []
            completed_tasks = completed.data or []
            
            # Por prioridade
            by_priority = {}
            for t in tasks:
                p = t.get("priority", "medium")
                by_priority[p] = by_priority.get(p, 0) + 1
            
            return {
                "created": len(tasks),
                "completed": len(completed_tasks),
                "pending": len([t for t in tasks if t.get("status") not in ["completed", "cancelled"]]),
                "completion_rate": round(len(completed_tasks) / max(len(tasks), 1) * 100),
                "by_priority": by_priority
            }
        except Exception as e:
            logger.error("tasks_data_error", error=str(e))
            return {"created": 0, "completed": 0, "pending": 0, "completion_rate": 0, "by_priority": {}}
    
    async def _get_goals_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados de objetivos."""
        try:
            goals = self.supabase.table("goals").select(
                "id, level, status, progress_percentage, area, title"
            ).eq("user_id", user_id).or_(
                f"period_start.lte.{end.isoformat()},period_end.gte.{start.isoformat()}"
            ).execute()
            
            data = goals.data or []
            
            by_level = {}
            by_status = {}
            by_area = {}
            total_progress = 0
            
            for g in data:
                level = g.get("level", "unknown")
                status = g.get("status", "unknown")
                area = g.get("area", "other")
                
                by_level[level] = by_level.get(level, 0) + 1
                by_status[status] = by_status.get(status, 0) + 1
                by_area[area] = by_area.get(area, 0) + 1
                total_progress += g.get("progress_percentage", 0)
            
            return {
                "total": len(data),
                "completed": by_status.get("completed", 0),
                "active": by_status.get("active", 0),
                "avg_progress": round(total_progress / max(len(data), 1)),
                "by_level": by_level,
                "by_status": by_status,
                "by_area": by_area,
                "top_goals": data[:5]  # Top 5 goals
            }
        except Exception as e:
            logger.error("goals_data_error", error=str(e))
            return {"total": 0, "completed": 0, "active": 0, "avg_progress": 0, "by_level": {}, "by_status": {}, "by_area": {}}
    
    async def _get_finance_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados financeiros."""
        try:
            transactions = self.supabase.table("finance_transactions").select(
                "id, type, amount, category_id, description, transaction_date"
            ).eq("user_id", user_id).gte(
                "transaction_date", start.isoformat()
            ).lte("transaction_date", end.isoformat()).execute()
            
            data = transactions.data or []
            
            income = sum(t["amount"] for t in data if t.get("type") == "income")
            expense = sum(t["amount"] for t in data if t.get("type") == "expense")
            
            # Por categoria
            by_category = {}
            for t in data:
                cat = t.get("category_id") or "other"
                if t.get("type") == "expense":
                    by_category[cat] = by_category.get(cat, 0) + t["amount"]
            
            # Top gastos
            top_expenses = sorted(
                [t for t in data if t.get("type") == "expense"],
                key=lambda x: x["amount"],
                reverse=True
            )[:5]
            
            return {
                "income": income,
                "expense": expense,
                "balance": income - expense,
                "savings_rate": round((income - expense) / max(income, 1) * 100),
                "transaction_count": len(data),
                "by_category": by_category,
                "top_expenses": top_expenses
            }
        except Exception as e:
            logger.error("finance_data_error", error=str(e))
            return {"income": 0, "expense": 0, "balance": 0, "savings_rate": 0, "transaction_count": 0}
    
    async def _get_habits_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados de hábitos."""
        try:
            # RPC call se disponível
            result = self.supabase.rpc(
                "get_habit_completions_count",
                {"p_user_id": user_id, "p_start": start.isoformat(), "p_end": end.isoformat()}
            ).execute()
            
            completions = result.data if result.data else 0
            
            # Calcula dias no período
            days = (end - start).days + 1
            
            return {
                "completions": completions,
                "days_in_period": days,
                "avg_per_day": round(completions / max(days, 1), 1)
            }
        except:
            return {"completions": 0, "days_in_period": 0, "avg_per_day": 0}
    
    async def _get_checkins_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados de check-ins."""
        try:
            checkins = self.supabase.table("check_ins").select(
                "id, type, mood_score, energy_level, created_at"
            ).eq("user_id", user_id).gte(
                "created_at", start.isoformat()
            ).lte("created_at", f"{end.isoformat()}T23:59:59").execute()
            
            data = checkins.data or []
            
            moods = [c.get("mood_score") for c in data if c.get("mood_score")]
            energies = [c.get("energy_level") for c in data if c.get("energy_level")]
            
            # Tendência de humor (início vs fim do período)
            mood_trend = 0
            if len(moods) >= 4:
                first_half = moods[:len(moods)//2]
                second_half = moods[len(moods)//2:]
                mood_trend = round(sum(second_half)/len(second_half) - sum(first_half)/len(first_half), 1)
            
            return {
                "total": len(data),
                "avg_mood": round(sum(moods) / max(len(moods), 1), 1),
                "avg_energy": round(sum(energies) / max(len(energies), 1), 1),
                "mood_trend": mood_trend,
                "best_mood": max(moods) if moods else 0,
                "worst_mood": min(moods) if moods else 0
            }
        except Exception as e:
            logger.error("checkins_data_error", error=str(e))
            return {"total": 0, "avg_mood": 0, "avg_energy": 0, "mood_trend": 0}
    
    async def _get_content_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados de conteúdo."""
        try:
            content = self.supabase.table("content_items").select(
                "id, status, platform, content_type"
            ).eq("user_id", user_id).gte(
                "created_at", start.isoformat()
            ).lte("created_at", f"{end.isoformat()}T23:59:59").execute()
            
            data = content.data or []
            
            by_platform = {}
            by_type = {}
            for c in data:
                p = c.get("platform", "other")
                t = c.get("content_type", "other")
                by_platform[p] = by_platform.get(p, 0) + 1
                by_type[t] = by_type.get(t, 0) + 1
            
            return {
                "created": len(data),
                "published": len([c for c in data if c.get("status") == "published"]),
                "draft": len([c for c in data if c.get("status") == "draft"]),
                "by_platform": by_platform,
                "by_type": by_type
            }
        except:
            return {"created": 0, "published": 0, "draft": 0, "by_platform": {}, "by_type": {}}
    
    async def _get_inbox_data(self, user_id: str, start: date, end: date) -> Dict:
        """Dados da inbox."""
        try:
            items = self.supabase.table("inbox_items").select(
                "id, status, category, content_type"
            ).eq("user_id", user_id).gte(
                "created_at", start.isoformat()
            ).lte("created_at", f"{end.isoformat()}T23:59:59").execute()
            
            data = items.data or []
            processed = [i for i in data if i.get("status") != "new"]
            
            by_category = {}
            for i in data:
                cat = i.get("category", "other")
                by_category[cat] = by_category.get(cat, 0) + 1
            
            return {
                "captured": len(data),
                "processed": len(processed),
                "processing_rate": round(len(processed) / max(len(data), 1) * 100),
                "by_category": by_category
            }
        except:
            return {"captured": 0, "processed": 0, "processing_rate": 0, "by_category": {}}
    
    # =============================================
    # BUILDERS DE RELATÓRIO
    # =============================================
    
    def _build_weekly_report(self, data: Dict, start: date, end: date) -> Dict:
        """Constrói relatório semanal."""
        week_num = start.isocalendar()[1]
        return {
            "type": "weekly",
            "period": {
                "week": week_num,
                "year": start.year,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "label": f"Semana {week_num}/{start.year}"
            },
            **data
        }
    
    def _build_monthly_report(self, data: Dict, start: date, end: date) -> Dict:
        """Constrói relatório mensal."""
        return {
            "type": "monthly",
            "period": {
                "month": start.month,
                "year": start.year,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "label": f"{self._get_month_name(start.month)} {start.year}"
            },
            **data
        }
    
    async def _build_quarterly_report(self, user_id: str, data: Dict, start: date, end: date) -> Dict:
        """Constrói relatório trimestral com comparativos."""
        quarter = (start.month - 1) // 3 + 1
        
        # Busca dados do trimestre anterior para comparação
        prev_end = start - timedelta(days=1)
        prev_start = date(prev_end.year, ((quarter - 2) % 4) * 3 + 1, 1)
        if quarter == 1:
            prev_start = date(prev_end.year - 1, 10, 1)
        
        prev_data = await self._collect_base_data(user_id, prev_start, prev_end)
        
        # Calcula variações
        variations = {
            "tasks_completed": data["tasks"]["completed"] - prev_data["tasks"]["completed"],
            "goals_completed": data["goals"]["completed"] - prev_data["goals"]["completed"],
            "income_change": data["finances"]["income"] - prev_data["finances"]["income"],
            "expense_change": data["finances"]["expense"] - prev_data["finances"]["expense"],
            "mood_change": data["checkins"]["avg_mood"] - prev_data["checkins"]["avg_mood"]
        }
        
        return {
            "type": "quarterly",
            "period": {
                "quarter": quarter,
                "year": start.year,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "label": f"Q{quarter}/{start.year}"
            },
            "current": data,
            "previous": prev_data,
            "variations": variations,
            **data
        }
    
    async def _build_annual_report(self, user_id: str, data: Dict, start: date, end: date) -> Dict:
        """Constrói relatório anual com análise por trimestre."""
        year = start.year
        
        # Coleta dados por trimestre
        quarters = []
        for q in range(1, 5):
            q_start = date(year, (q - 1) * 3 + 1, 1)
            if q == 4:
                q_end = date(year, 12, 31)
            else:
                q_end = date(year, q * 3 + 1, 1) - timedelta(days=1)
            
            q_data = await self._collect_base_data(user_id, q_start, q_end)
            quarters.append({
                "quarter": q,
                "label": f"Q{q}",
                "data": q_data
            })
        
        # Ano anterior para comparação
        prev_year = year - 1
        prev_data = await self._collect_base_data(
            user_id, 
            date(prev_year, 1, 1), 
            date(prev_year, 12, 31)
        )
        
        # Variações YoY
        yoy = {
            "tasks_completed": round((data["tasks"]["completed"] - prev_data["tasks"]["completed"]) / max(prev_data["tasks"]["completed"], 1) * 100),
            "goals_completed": data["goals"]["completed"] - prev_data["goals"]["completed"],
            "income_change": round((data["finances"]["income"] - prev_data["finances"]["income"]) / max(prev_data["finances"]["income"], 1) * 100),
            "savings_change": data["finances"]["savings_rate"] - prev_data["finances"]["savings_rate"]
        }
        
        # Melhores meses
        months_data = []
        for m in range(1, 13):
            m_start = date(year, m, 1)
            if m == 12:
                m_end = date(year, 12, 31)
            else:
                m_end = date(year, m + 1, 1) - timedelta(days=1)
            
            m_data = await self._collect_base_data(user_id, m_start, m_end)
            months_data.append({
                "month": m,
                "name": self._get_month_name(m),
                "tasks_completed": m_data["tasks"]["completed"],
                "income": m_data["finances"]["income"],
                "mood": m_data["checkins"]["avg_mood"]
            })
        
        # Top meses
        best_productivity = max(months_data, key=lambda x: x["tasks_completed"])
        best_income = max(months_data, key=lambda x: x["income"])
        best_mood = max(months_data, key=lambda x: x["mood"])
        
        return {
            "type": "annual",
            "period": {
                "year": year,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "label": str(year)
            },
            "quarters": quarters,
            "months_summary": months_data,
            "previous_year": prev_data,
            "yoy_variations": yoy,
            "highlights": {
                "best_productivity_month": best_productivity,
                "best_income_month": best_income,
                "best_mood_month": best_mood
            },
            **data
        }
    
    # =============================================
    # INSIGHTS
    # =============================================
    
    def _generate_insights(self, data: Dict, report_type: ReportType) -> List[str]:
        """Gera insights baseados nos dados."""
        insights = []
        
        # Tarefas
        tasks = data.get("tasks", {})
        if tasks.get("completion_rate", 0) >= 80:
            insights.append("🏆 Excelente produtividade! Taxa de conclusão acima de 80%")
        elif tasks.get("completion_rate", 0) < 50:
            insights.append("⚠️ Muitas tarefas pendentes - considere revisar prioridades")
        
        # Objetivos
        goals = data.get("goals", {})
        if goals.get("completed", 0) > 0:
            insights.append(f"🎯 {goals['completed']} objetivo(s) concluído(s)!")
        if goals.get("avg_progress", 0) >= 70:
            insights.append("📈 Progresso sólido nos objetivos")
        
        # Finanças
        finances = data.get("finances", {})
        if finances.get("savings_rate", 0) >= 20:
            insights.append("💰 Excelente taxa de poupança!")
        elif finances.get("balance", 0) < 0:
            insights.append("🚨 Atenção: gastos maiores que receitas")
        
        # Check-ins
        checkins = data.get("checkins", {})
        if checkins.get("avg_mood", 0) >= 4:
            insights.append("😊 Humor consistentemente positivo")
        if checkins.get("mood_trend", 0) > 0.5:
            insights.append("📈 Tendência de melhora no humor")
        elif checkins.get("mood_trend", 0) < -0.5:
            insights.append("📉 Atenção: tendência de queda no humor")
        
        # Inbox
        inbox = data.get("inbox", {})
        if inbox.get("processing_rate", 0) >= 80:
            insights.append("📥 Inbox bem gerenciada!")
        
        # Conteúdo
        content = data.get("content", {})
        if content.get("published", 0) > 0:
            insights.append(f"✍️ {content['published']} conteúdo(s) publicado(s)")
        
        # Insights específicos por tipo
        if report_type == ReportType.QUARTERLY:
            variations = data.get("variations", {})
            if variations.get("income_change", 0) > 0:
                insights.append(f"📈 Receita cresceu R$ {variations['income_change']:,.2f} vs trimestre anterior")
        
        if report_type == ReportType.ANNUAL:
            yoy = data.get("yoy_variations", {})
            if yoy.get("income_change", 0) > 0:
                insights.append(f"📈 Crescimento de {yoy['income_change']}% na receita vs ano anterior")
            
            highlights = data.get("highlights", {})
            if highlights:
                best_month = highlights.get("best_productivity_month", {})
                insights.append(f"⭐ Mês mais produtivo: {best_month.get('name', 'N/A')}")
        
        return insights[:8]  # Limita a 8 insights
    
    # =============================================
    # FORMATAÇÃO
    # =============================================
    
    def _format_message(self, data: Dict, report_type: ReportType) -> str:
        """Formata mensagem para Telegram."""
        period = data.get("period", {})
        tasks = data.get("tasks", {})
        goals = data.get("goals", {})
        finances = data.get("finances", {})
        checkins = data.get("checkins", {})
        content = data.get("content", {})
        inbox = data.get("inbox", {})
        insights = data.get("insights", [])
        
        # Emoji e título por tipo
        type_config = {
            ReportType.WEEKLY: ("📅", "Semanal"),
            ReportType.MONTHLY: ("📊", "Mensal"),
            ReportType.QUARTERLY: ("📈", "Trimestral"),
            ReportType.ANNUAL: ("🎊", "Anual")
        }
        
        emoji, title = type_config.get(report_type, ("📊", "Relatório"))
        
        message = f"""{emoji} *Relatório {title} - {period.get('label', '')}*

━━━━━━━━━━━━━━━━━━━━

📋 *Tarefas*
• Criadas: {tasks.get('created', 0)}
• Concluídas: {tasks.get('completed', 0)}
• Taxa: {tasks.get('completion_rate', 0)}%

🎯 *Objetivos*
• Ativos: {goals.get('active', 0)}
• Concluídos: {goals.get('completed', 0)}
• Progresso: {goals.get('avg_progress', 0)}%

💰 *Finanças*
• Receitas: R$ {finances.get('income', 0):,.2f}
• Despesas: R$ {finances.get('expense', 0):,.2f}
• Saldo: R$ {finances.get('balance', 0):,.2f}
• Poupança: {finances.get('savings_rate', 0)}%

📝 *Check-ins*
• Total: {checkins.get('total', 0)}
• Humor: {checkins.get('avg_mood', 0)}/5
• Energia: {checkins.get('avg_energy', 0)}/5

✍️ *Conteúdo*
• Criados: {content.get('created', 0)}
• Publicados: {content.get('published', 0)}

📥 *Inbox*
• Capturados: {inbox.get('captured', 0)}
• Processados: {inbox.get('processed', 0)} ({inbox.get('processing_rate', 0)}%)

━━━━━━━━━━━━━━━━━━━━

💡 *Insights*
"""
        
        for insight in insights[:5]:
            message += f"• {insight}\n"
        
        if not insights:
            message += "• Sem insights especiais neste período\n"
        
        # Adiciona info específica para relatórios maiores
        if report_type == ReportType.QUARTERLY:
            variations = data.get("variations", {})
            message += f"""
━━━━━━━━━━━━━━━━━━━━

📊 *Vs Trimestre Anterior*
• Tarefas: {'+' if variations.get('tasks_completed', 0) >= 0 else ''}{variations.get('tasks_completed', 0)}
• Receita: {'+' if variations.get('income_change', 0) >= 0 else ''}R$ {variations.get('income_change', 0):,.2f}
"""
        
        if report_type == ReportType.ANNUAL:
            yoy = data.get("yoy_variations", {})
            highlights = data.get("highlights", {})
            message += f"""
━━━━━━━━━━━━━━━━━━━━

📊 *Vs Ano Anterior*
• Receita: {'+' if yoy.get('income_change', 0) >= 0 else ''}{yoy.get('income_change', 0)}%
• Poupança: {'+' if yoy.get('savings_change', 0) >= 0 else ''}{yoy.get('savings_change', 0)}%

⭐ *Destaques do Ano*
• Melhor mês (produtividade): {highlights.get('best_productivity_month', {}).get('name', 'N/A')}
• Melhor mês (receita): {highlights.get('best_income_month', {}).get('name', 'N/A')}
• Melhor mês (humor): {highlights.get('best_mood_month', {}).get('name', 'N/A')}
"""
        
        message += "\n_Relatório gerado pelo TB Personal OS_"
        
        return message
    
    # =============================================
    # HELPERS
    # =============================================
    
    def _calculate_period(self, report_type: ReportType) -> tuple:
        """Calcula período padrão para cada tipo."""
        today = date.today()
        
        if report_type == ReportType.WEEKLY:
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
        
        elif report_type == ReportType.MONTHLY:
            first_this_month = date(today.year, today.month, 1)
            end = first_this_month - timedelta(days=1)
            start = date(end.year, end.month, 1)
        
        elif report_type == ReportType.QUARTERLY:
            current_q = (today.month - 1) // 3 + 1
            if current_q == 1:
                year, q = today.year - 1, 4
            else:
                year, q = today.year, current_q - 1
            
            start = date(year, (q - 1) * 3 + 1, 1)
            if q == 4:
                end = date(year, 12, 31)
            else:
                end = date(year, q * 3 + 1, 1) - timedelta(days=1)
        
        else:  # ANNUAL
            year = today.year - 1
            start = date(year, 1, 1)
            end = date(year, 12, 31)
        
        return start, end
    
    def _get_month_name(self, month: int) -> str:
        """Retorna nome do mês em português."""
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        return months[month - 1]
    
    async def _save_report(self, user_id: str, report_type: ReportType, data: Dict) -> None:
        """Salva relatório no banco."""
        try:
            period = data.get("period", {})
            self.supabase.table("user_reports").upsert({
                "user_id": user_id,
                "report_type": report_type.value,
                "period_start": period.get("start_date"),
                "period_end": period.get("end_date"),
                "report_data": data
            }, on_conflict="user_id,report_type,period_start,period_end").execute()
        except Exception as e:
            logger.warning("report_save_failed", error=str(e))
    
    async def send_via_telegram(self, user_id: str, message: str) -> bool:
        """Envia relatório via Telegram."""
        try:
            chat = self.supabase.table("telegram_chats").select(
                "chat_id"
            ).eq("user_id", user_id).single().execute()
            
            if not chat.data:
                return False
            
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": chat.data["chat_id"],
                        "text": message,
                        "parse_mode": "Markdown"
                    }
                )
                return response.status_code == 200
                
        except Exception as e:
            logger.error("telegram_send_failed", error=str(e))
            return False


# Singleton
report_service = ReportService()
