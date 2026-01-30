"""
TB Personal OS - Insights Service
Sistema de ML/Analytics para insights e recomendações
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import json
import pytz

from supabase import Client, create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class InsightsService:
    """
    Serviço de insights e análises.
    Gera recomendações baseadas em dados do usuário.
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
    # PRODUCTIVITY INSIGHTS
    # ==========================================
    
    async def get_productivity_score(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calcula score de produtividade.
        
        Baseado em:
        - Tarefas concluídas
        - Tarefas no prazo
        - Consistência diária
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            end_date = datetime.now(tz)
            start_date = end_date - timedelta(days=days)
            
            # Tarefas do período
            tasks_result = self.supabase.table("tasks") \
                .select("id, status, due_date, completed_at, created_at") \
                .eq("user_id", user_id) \
                .gte("created_at", start_date.isoformat()) \
                .execute()
            
            tasks = tasks_result.data or []
            
            total_tasks = len(tasks)
            completed = [t for t in tasks if t.get("status") == "done"]
            
            # Taxa de conclusão
            completion_rate = len(completed) / total_tasks if total_tasks > 0 else 0
            
            # Tarefas no prazo
            on_time = 0
            for task in completed:
                due = task.get("due_date")
                completed_at = task.get("completed_at")
                if due and completed_at:
                    if completed_at <= due:
                        on_time += 1
                elif completed_at:
                    on_time += 1  # Sem prazo = no prazo
            
            on_time_rate = on_time / len(completed) if completed else 0
            
            # Score final (0-100)
            score = int((completion_rate * 60) + (on_time_rate * 40))
            
            # Nível baseado no score
            if score >= 80:
                level = "excellent"
                label = "Excelente"
            elif score >= 60:
                level = "good"
                label = "Bom"
            elif score >= 40:
                level = "fair"
                label = "Razoável"
            else:
                level = "needs_improvement"
                label = "Precisa melhorar"
            
            return {
                "score": score,
                "level": level,
                "label": label,
                "metrics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": len(completed),
                    "completion_rate": round(completion_rate * 100, 1),
                    "on_time_rate": round(on_time_rate * 100, 1)
                },
                "period_days": days,
                "calculated_at": datetime.now(tz).isoformat()
            }
            
        except Exception as e:
            logger.error("get_productivity_score_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_daily_productivity(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtém produtividade diária.
        
        Returns:
            Lista com dados por dia
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            end_date = datetime.now(tz)
            start_date = end_date - timedelta(days=days)
            
            # Tarefas concluídas por dia
            tasks_result = self.supabase.table("tasks") \
                .select("completed_at") \
                .eq("user_id", user_id) \
                .eq("status", "done") \
                .gte("completed_at", start_date.isoformat()) \
                .execute()
            
            # Agrupar por dia
            by_day = defaultdict(int)
            for task in tasks_result.data or []:
                if task.get("completed_at"):
                    date = task["completed_at"][:10]  # YYYY-MM-DD
                    by_day[date] += 1
            
            # Gerar lista completa de dias
            daily_data = []
            current = start_date.date()
            while current <= end_date.date():
                date_str = current.isoformat()
                daily_data.append({
                    "date": date_str,
                    "tasks_completed": by_day.get(date_str, 0),
                    "day_of_week": current.strftime("%A")
                })
                current += timedelta(days=1)
            
            return daily_data
            
        except Exception as e:
            logger.error("get_daily_productivity_failed", user_id=user_id, error=str(e))
            return []
    
    # ==========================================
    # PATTERN ANALYSIS
    # ==========================================
    
    async def analyze_best_work_days(
        self,
        user_id: str,
        days: int = 60
    ) -> Dict[str, Any]:
        """
        Analisa quais dias da semana são mais produtivos.
        """
        try:
            daily_data = await self.get_daily_productivity(user_id, days)
            
            # Agrupar por dia da semana
            by_weekday = defaultdict(list)
            for day in daily_data:
                weekday = day["day_of_week"]
                by_weekday[weekday].append(day["tasks_completed"])
            
            # Calcular médias
            weekday_averages = {}
            for weekday, values in by_weekday.items():
                avg = sum(values) / len(values) if values else 0
                weekday_averages[weekday] = round(avg, 2)
            
            # Ordenar por produtividade
            sorted_days = sorted(
                weekday_averages.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                "best_day": sorted_days[0][0] if sorted_days else None,
                "worst_day": sorted_days[-1][0] if sorted_days else None,
                "by_weekday": weekday_averages,
                "ranking": [{"day": d, "avg_tasks": v} for d, v in sorted_days],
                "period_days": days
            }
            
        except Exception as e:
            logger.error("analyze_best_work_days_failed", user_id=user_id, error=str(e))
            raise
    
    async def analyze_energy_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analisa padrões de energia baseado em check-ins.
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            end_date = datetime.now(tz)
            start_date = end_date - timedelta(days=days)
            
            # Check-ins de energia
            checkins_result = self.supabase.table("checkins") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("checkin_type", "energy") \
                .gte("created_at", start_date.isoformat()) \
                .execute()
            
            checkins = checkins_result.data or []
            
            if not checkins:
                return {
                    "message": "Sem dados de energia suficientes",
                    "data_points": 0
                }
            
            # Calcular estatísticas
            values = [c.get("value", 0) for c in checkins if c.get("value")]
            
            avg_energy = sum(values) / len(values) if values else 0
            max_energy = max(values) if values else 0
            min_energy = min(values) if values else 0
            
            # Agrupar por dia da semana
            by_weekday = defaultdict(list)
            for checkin in checkins:
                date_str = checkin.get("created_at", "")[:10]
                try:
                    date = datetime.fromisoformat(date_str)
                    weekday = date.strftime("%A")
                    by_weekday[weekday].append(checkin.get("value", 0))
                except:
                    pass
            
            weekday_averages = {
                day: round(sum(vals) / len(vals), 1)
                for day, vals in by_weekday.items() if vals
            }
            
            return {
                "average_energy": round(avg_energy, 1),
                "max_energy": max_energy,
                "min_energy": min_energy,
                "data_points": len(checkins),
                "by_weekday": weekday_averages,
                "best_day": max(weekday_averages.items(), key=lambda x: x[1])[0] if weekday_averages else None,
                "period_days": days
            }
            
        except Exception as e:
            logger.error("analyze_energy_patterns_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # CORRELATIONS
    # ==========================================
    
    async def analyze_sleep_productivity_correlation(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analisa correlação entre sono e produtividade.
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            end_date = datetime.now(tz)
            start_date = end_date - timedelta(days=days)
            
            # Check-ins de sono
            sleep_result = self.supabase.table("checkins") \
                .select("value, created_at") \
                .eq("user_id", user_id) \
                .eq("checkin_type", "sleep_hours") \
                .gte("created_at", start_date.isoformat()) \
                .execute()
            
            # Tarefas concluídas
            tasks_result = self.supabase.table("tasks") \
                .select("completed_at") \
                .eq("user_id", user_id) \
                .eq("status", "done") \
                .gte("completed_at", start_date.isoformat()) \
                .execute()
            
            # Agrupar por dia
            sleep_by_day = {}
            for s in sleep_result.data or []:
                date = s.get("created_at", "")[:10]
                sleep_by_day[date] = s.get("value", 0)
            
            tasks_by_day = defaultdict(int)
            for t in tasks_result.data or []:
                if t.get("completed_at"):
                    date = t["completed_at"][:10]
                    tasks_by_day[date] += 1
            
            # Correlacionar
            data_points = []
            for date, sleep in sleep_by_day.items():
                tasks = tasks_by_day.get(date, 0)
                data_points.append({
                    "date": date,
                    "sleep_hours": sleep,
                    "tasks_completed": tasks
                })
            
            if len(data_points) < 5:
                return {
                    "message": "Dados insuficientes para correlação",
                    "data_points": len(data_points),
                    "recommendation": "Registre mais check-ins de sono"
                }
            
            # Calcular correlação simples
            # Média de tarefas em dias com sono bom (7+ horas) vs ruim
            good_sleep_days = [d for d in data_points if d["sleep_hours"] >= 7]
            poor_sleep_days = [d for d in data_points if d["sleep_hours"] < 7]
            
            good_sleep_avg = sum(d["tasks_completed"] for d in good_sleep_days) / len(good_sleep_days) if good_sleep_days else 0
            poor_sleep_avg = sum(d["tasks_completed"] for d in poor_sleep_days) / len(poor_sleep_days) if poor_sleep_days else 0
            
            impact = ((good_sleep_avg - poor_sleep_avg) / poor_sleep_avg * 100) if poor_sleep_avg > 0 else 0
            
            return {
                "correlation_type": "sleep_productivity",
                "good_sleep_productivity": round(good_sleep_avg, 2),
                "poor_sleep_productivity": round(poor_sleep_avg, 2),
                "productivity_impact": round(impact, 1),
                "insight": f"Você completa {abs(round(impact))}% {'mais' if impact > 0 else 'menos'} tarefas em dias com sono adequado (7+ horas)",
                "data_points": len(data_points),
                "period_days": days
            }
            
        except Exception as e:
            logger.error("analyze_sleep_productivity_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # RECOMMENDATIONS
    # ==========================================
    
    async def generate_recommendations(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Gera recomendações personalizadas.
        """
        try:
            recommendations = []
            
            # 1. Análise de tarefas pendentes
            pending_result = self.supabase.table("tasks") \
                .select("id, priority, due_date") \
                .eq("user_id", user_id) \
                .neq("status", "done") \
                .execute()
            
            pending_tasks = pending_result.data or []
            
            # Tarefas atrasadas
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            overdue = [t for t in pending_tasks if t.get("due_date") and t["due_date"] < now.isoformat()]
            if overdue:
                recommendations.append({
                    "type": "urgent",
                    "category": "tasks",
                    "title": "Tarefas atrasadas",
                    "message": f"Você tem {len(overdue)} tarefas atrasadas. Recomendo revisar prioridades.",
                    "action": "Revisar tarefas atrasadas",
                    "priority": "high"
                })
            
            # Muitas tarefas de alta prioridade
            high_priority = [t for t in pending_tasks if t.get("priority") == "high"]
            if len(high_priority) > 5:
                recommendations.append({
                    "type": "warning",
                    "category": "tasks",
                    "title": "Muitas prioridades altas",
                    "message": f"Você tem {len(high_priority)} tarefas de alta prioridade. Considere repriorizar.",
                    "action": "Revisar prioridades",
                    "priority": "medium"
                })
            
            # 2. Análise de energia
            try:
                energy = await self.analyze_energy_patterns(user_id, days=7)
                if energy.get("average_energy", 10) < 5:
                    recommendations.append({
                        "type": "health",
                        "category": "energy",
                        "title": "Energia baixa",
                        "message": f"Sua energia média está em {energy['average_energy']}/10. Considere revisar sono e pausas.",
                        "action": "Verificar padrões de sono",
                        "priority": "medium"
                    })
            except:
                pass
            
            # 3. Análise de produtividade
            try:
                productivity = await self.get_productivity_score(user_id, days=7)
                if productivity.get("score", 100) < 50:
                    recommendations.append({
                        "type": "productivity",
                        "category": "tasks",
                        "title": "Produtividade baixa",
                        "message": f"Seu score de produtividade está em {productivity['score']}/100. Vamos criar um plano?",
                        "action": "Criar plano de ação",
                        "priority": "medium"
                    })
            except:
                pass
            
            # 4. Sugestão positiva se tudo estiver bem
            if not recommendations:
                recommendations.append({
                    "type": "positive",
                    "category": "general",
                    "title": "Tudo em dia!",
                    "message": "Você está com boa produtividade e energia. Continue assim!",
                    "action": None,
                    "priority": "low"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error("generate_recommendations_failed", user_id=user_id, error=str(e))
            return []
    
    # ==========================================
    # SUMMARY INSIGHTS
    # ==========================================
    
    async def get_weekly_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Gera resumo semanal com insights.
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            
            # Dados da semana
            productivity = await self.get_productivity_score(user_id, days=7)
            work_days = await self.analyze_best_work_days(user_id, days=30)
            recommendations = await self.generate_recommendations(user_id)
            
            # Tarefas da semana
            start_week = now - timedelta(days=7)
            tasks_result = self.supabase.table("tasks") \
                .select("status") \
                .eq("user_id", user_id) \
                .gte("created_at", start_week.isoformat()) \
                .execute()
            
            tasks = tasks_result.data or []
            completed = len([t for t in tasks if t.get("status") == "done"])
            total = len(tasks)
            
            return {
                "period": {
                    "start": start_week.isoformat(),
                    "end": now.isoformat()
                },
                "productivity": productivity,
                "tasks_summary": {
                    "created": total,
                    "completed": completed,
                    "pending": total - completed
                },
                "best_day": work_days.get("best_day"),
                "recommendations": recommendations[:3],  # Top 3
                "generated_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error("get_weekly_summary_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_monthly_report(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Gera relatório mensal detalhado.
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            now = datetime.now(tz)
            start_month = now - timedelta(days=30)
            
            # Produtividade mensal
            productivity = await self.get_productivity_score(user_id, days=30)
            daily = await self.get_daily_productivity(user_id, days=30)
            work_days = await self.analyze_best_work_days(user_id, days=30)
            energy = await self.analyze_energy_patterns(user_id, days=30)
            sleep_correlation = await self.analyze_sleep_productivity_correlation(user_id, days=30)
            
            # Total de tarefas
            total_completed = sum(d["tasks_completed"] for d in daily)
            
            # Tendência (últimas 2 semanas vs primeiras 2)
            first_half = daily[:15]
            second_half = daily[15:]
            
            first_avg = sum(d["tasks_completed"] for d in first_half) / 15 if first_half else 0
            second_avg = sum(d["tasks_completed"] for d in second_half) / 15 if second_half else 0
            
            trend = "up" if second_avg > first_avg else "down" if second_avg < first_avg else "stable"
            trend_percent = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            
            return {
                "period": {
                    "start": start_month.isoformat(),
                    "end": now.isoformat(),
                    "days": 30
                },
                "productivity": productivity,
                "total_tasks_completed": total_completed,
                "daily_average": round(total_completed / 30, 2),
                "trend": {
                    "direction": trend,
                    "change_percent": round(trend_percent, 1)
                },
                "patterns": {
                    "best_work_day": work_days.get("best_day"),
                    "worst_work_day": work_days.get("worst_day"),
                    "by_weekday": work_days.get("by_weekday", {})
                },
                "energy": energy,
                "correlations": {
                    "sleep_productivity": sleep_correlation
                },
                "generated_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error("get_monthly_report_failed", user_id=user_id, error=str(e))
            raise


# Singleton
insights_service = InsightsService()
