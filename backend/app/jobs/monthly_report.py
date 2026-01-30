"""
Monthly Report Job - Relatório Mensal Automático
Envia um resumo completo do mês via Telegram
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import structlog

from app.core.config import settings
from supabase import create_client, Client

logger = structlog.get_logger()


class MonthlyReportJob:
    """Job para gerar e enviar relatório mensal."""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    async def run(self, user_id: str, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Executa o job de relatório mensal."""
        
        # Determina o mês do relatório (default: mês anterior)
        today = date.today()
        if month is None or year is None:
            # Mês anterior
            first_day_this_month = date(today.year, today.month, 1)
            last_day_prev_month = first_day_this_month - timedelta(days=1)
            month = last_day_prev_month.month
            year = last_day_prev_month.year
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        logger.info("generating_monthly_report", 
                   user_id=user_id, month=month, year=year)
        
        # Coleta dados
        report_data = {
            "period": {
                "month": month,
                "year": year,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "month_name": self._get_month_name(month)
            },
            "tasks": await self._get_tasks_summary(user_id, start_date, end_date),
            "goals": await self._get_goals_summary(user_id, start_date, end_date),
            "finances": await self._get_finance_summary(user_id, start_date, end_date),
            "habits": await self._get_habits_summary(user_id, start_date, end_date),
            "checkins": await self._get_checkins_summary(user_id, start_date, end_date),
            "content": await self._get_content_summary(user_id, start_date, end_date),
            "inbox": await self._get_inbox_summary(user_id, start_date, end_date)
        }
        
        # Gera insights
        report_data["insights"] = self._generate_insights(report_data)
        
        # Formata mensagem
        message = self._format_telegram_message(report_data)
        
        # Salva relatório
        await self._save_report(user_id, report_data)
        
        return {
            "success": True,
            "data": report_data,
            "message": message
        }
    
    async def _get_tasks_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo de tarefas do período."""
        try:
            # Tarefas criadas
            created = self.supabase.table("tasks").select("id, status").eq(
                "user_id", user_id
            ).gte("created_at", start.isoformat()).lte(
                "created_at", f"{end.isoformat()}T23:59:59"
            ).execute()
            
            # Tarefas completadas
            completed = self.supabase.table("tasks").select("id").eq(
                "user_id", user_id
            ).eq("status", "completed").gte(
                "completed_at", start.isoformat()
            ).lte("completed_at", f"{end.isoformat()}T23:59:59").execute()
            
            tasks_data = created.data or []
            completed_data = completed.data or []
            
            return {
                "created": len(tasks_data),
                "completed": len(completed_data),
                "pending": len([t for t in tasks_data if t.get("status") not in ["completed", "cancelled"]]),
                "completion_rate": round(len(completed_data) / max(len(tasks_data), 1) * 100)
            }
        except Exception as e:
            logger.error("tasks_summary_failed", error=str(e))
            return {"created": 0, "completed": 0, "pending": 0, "completion_rate": 0}
    
    async def _get_goals_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo de objetivos do período."""
        try:
            goals = self.supabase.table("goals").select(
                "id, level, status, progress_percentage, area"
            ).eq("user_id", user_id).gte(
                "period_start", start.isoformat()
            ).lte("period_end", end.isoformat()).execute()
            
            goals_data = goals.data or []
            
            by_level = {}
            by_status = {}
            total_progress = 0
            
            for goal in goals_data:
                level = goal.get("level", "unknown")
                status = goal.get("status", "unknown")
                
                by_level[level] = by_level.get(level, 0) + 1
                by_status[status] = by_status.get(status, 0) + 1
                total_progress += goal.get("progress_percentage", 0)
            
            return {
                "total": len(goals_data),
                "by_level": by_level,
                "by_status": by_status,
                "completed": by_status.get("completed", 0),
                "avg_progress": round(total_progress / max(len(goals_data), 1))
            }
        except Exception as e:
            logger.error("goals_summary_failed", error=str(e))
            return {"total": 0, "by_level": {}, "by_status": {}, "completed": 0, "avg_progress": 0}
    
    async def _get_finance_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo financeiro do período."""
        try:
            transactions = self.supabase.table("finance_transactions").select(
                "id, type, amount, category_id"
            ).eq("user_id", user_id).gte(
                "transaction_date", start.isoformat()
            ).lte("transaction_date", end.isoformat()).execute()
            
            data = transactions.data or []
            
            total_income = sum(t["amount"] for t in data if t.get("type") == "income")
            total_expense = sum(t["amount"] for t in data if t.get("type") == "expense")
            
            return {
                "income": total_income,
                "expense": total_expense,
                "balance": total_income - total_expense,
                "transaction_count": len(data),
                "savings_rate": round((total_income - total_expense) / max(total_income, 1) * 100)
            }
        except Exception as e:
            logger.error("finance_summary_failed", error=str(e))
            return {"income": 0, "expense": 0, "balance": 0, "transaction_count": 0, "savings_rate": 0}
    
    async def _get_habits_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo de hábitos do período."""
        try:
            # Busca hábitos via goals
            completions = self.supabase.rpc(
                "get_habit_completions_count",
                {"p_user_id": user_id, "p_start": start.isoformat(), "p_end": end.isoformat()}
            ).execute()
            
            return {
                "completions": completions.data if completions.data else 0,
                "best_streak": 0,
                "consistency": 0
            }
        except Exception as e:
            # Se a função não existir, retorna padrão
            return {"completions": 0, "best_streak": 0, "consistency": 0}
    
    async def _get_checkins_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo de check-ins do período."""
        try:
            checkins = self.supabase.table("check_ins").select(
                "id, type, mood_score, energy_level"
            ).eq("user_id", user_id).gte(
                "created_at", start.isoformat()
            ).lte("created_at", f"{end.isoformat()}T23:59:59").execute()
            
            data = checkins.data or []
            
            total_mood = sum(c.get("mood_score", 0) or 0 for c in data)
            total_energy = sum(c.get("energy_level", 0) or 0 for c in data)
            count = len(data) or 1
            
            return {
                "total": len(data),
                "avg_mood": round(total_mood / count, 1),
                "avg_energy": round(total_energy / count, 1)
            }
        except Exception as e:
            logger.error("checkins_summary_failed", error=str(e))
            return {"total": 0, "avg_mood": 0, "avg_energy": 0}
    
    async def _get_content_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo de conteúdo do período."""
        try:
            content = self.supabase.table("content_items").select(
                "id, status, platform"
            ).eq("user_id", user_id).gte(
                "created_at", start.isoformat()
            ).lte("created_at", f"{end.isoformat()}T23:59:59").execute()
            
            data = content.data or []
            published = [c for c in data if c.get("status") == "published"]
            
            return {
                "created": len(data),
                "published": len(published)
            }
        except Exception as e:
            return {"created": 0, "published": 0}
    
    async def _get_inbox_summary(self, user_id: str, start: date, end: date) -> Dict:
        """Resumo da inbox do período."""
        try:
            items = self.supabase.table("inbox_items").select(
                "id, status, category"
            ).eq("user_id", user_id).gte(
                "created_at", start.isoformat()
            ).lte("created_at", f"{end.isoformat()}T23:59:59").execute()
            
            data = items.data or []
            processed = [i for i in data if i.get("status") != "new"]
            
            return {
                "captured": len(data),
                "processed": len(processed),
                "processing_rate": round(len(processed) / max(len(data), 1) * 100)
            }
        except Exception as e:
            return {"captured": 0, "processed": 0, "processing_rate": 0}
    
    def _generate_insights(self, data: Dict) -> List[str]:
        """Gera insights a partir dos dados."""
        insights = []
        
        # Tarefas
        if data["tasks"]["completion_rate"] >= 80:
            insights.append("🏆 Excelente taxa de conclusão de tarefas!")
        elif data["tasks"]["completion_rate"] < 50:
            insights.append("⚠️ Muitas tarefas pendentes - considere revisar prioridades")
        
        # Finanças
        if data["finances"]["savings_rate"] >= 20:
            insights.append("💰 Ótima taxa de poupança este mês!")
        elif data["finances"]["balance"] < 0:
            insights.append("🚨 Gastos maiores que receitas - atenção!")
        
        # Objetivos
        if data["goals"]["completed"] > 0:
            insights.append(f"🎯 {data['goals']['completed']} objetivo(s) concluído(s)!")
        
        if data["goals"]["avg_progress"] >= 70:
            insights.append("📈 Bom progresso geral nos objetivos")
        
        # Check-ins
        if data["checkins"]["avg_mood"] >= 4:
            insights.append("😊 Média de humor alta - bom trabalho!")
        elif data["checkins"]["avg_mood"] < 3 and data["checkins"]["total"] > 0:
            insights.append("💭 Humor abaixo da média - cuide de você")
        
        # Inbox
        if data["inbox"]["processing_rate"] >= 80:
            insights.append("📥 Inbox bem processada!")
        
        return insights
    
    def _format_telegram_message(self, data: Dict) -> str:
        """Formata mensagem para Telegram."""
        period = data["period"]
        tasks = data["tasks"]
        goals = data["goals"]
        finances = data["finances"]
        checkins = data["checkins"]
        content = data["content"]
        inbox = data["inbox"]
        insights = data["insights"]
        
        message = f"""📊 *Relatório Mensal - {period['month_name']} {period['year']}*

━━━━━━━━━━━━━━━━━━━━

📋 *Tarefas*
• Criadas: {tasks['created']}
• Concluídas: {tasks['completed']}
• Taxa: {tasks['completion_rate']}%

🎯 *Objetivos*
• Total: {goals['total']}
• Concluídos: {goals['completed']}
• Progresso médio: {goals['avg_progress']}%

💰 *Finanças*
• Receitas: R$ {finances['income']:,.2f}
• Despesas: R$ {finances['expense']:,.2f}
• Saldo: R$ {finances['balance']:,.2f}
• Taxa poupança: {finances['savings_rate']}%

📝 *Check-ins*
• Total: {checkins['total']}
• Humor médio: {checkins['avg_mood']}/5
• Energia média: {checkins['avg_energy']}/5

✍️ *Conteúdo*
• Criados: {content['created']}
• Publicados: {content['published']}

📥 *Inbox*
• Capturados: {inbox['captured']}
• Processados: {inbox['processed']} ({inbox['processing_rate']}%)

━━━━━━━━━━━━━━━━━━━━

💡 *Insights*
"""
        
        for insight in insights[:5]:
            message += f"• {insight}\n"
        
        if not insights:
            message += "• Sem insights especiais este mês\n"
        
        message += "\n_Relatório gerado automaticamente pelo TB Personal OS_"
        
        return message
    
    async def _save_report(self, user_id: str, data: Dict) -> None:
        """Salva relatório no banco."""
        try:
            self.supabase.table("user_reports").insert({
                "user_id": user_id,
                "report_type": "monthly",
                "period_start": data["period"]["start_date"],
                "period_end": data["period"]["end_date"],
                "report_data": data
            }).execute()
        except Exception as e:
            # Tabela pode não existir ainda
            logger.warning("report_save_failed", error=str(e))
    
    def _get_month_name(self, month: int) -> str:
        """Retorna nome do mês em português."""
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        return months[month - 1]
    
    async def send_via_telegram(self, user_id: str, message: str) -> bool:
        """Envia relatório via Telegram."""
        try:
            # Busca chat_id do usuário
            chat = self.supabase.table("telegram_chats").select(
                "chat_id"
            ).eq("user_id", user_id).single().execute()
            
            if not chat.data:
                logger.warning("telegram_chat_not_found", user_id=user_id)
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


# Job singleton
monthly_report_job = MonthlyReportJob()


async def run_monthly_report_for_all_users():
    """Executa relatório mensal para todos os usuários ativos."""
    supabase = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
    
    # Busca usuários ativos
    users = supabase.table("users").select("id").eq(
        "is_active", True
    ).execute()
    
    for user in users.data or []:
        try:
            result = await monthly_report_job.run(user["id"])
            if result.get("success"):
                await monthly_report_job.send_via_telegram(
                    user["id"], 
                    result["message"]
                )
                logger.info("monthly_report_sent", user_id=user["id"])
        except Exception as e:
            logger.error("monthly_report_failed", 
                        user_id=user["id"], error=str(e))
