"""
TB Personal OS - Health Service
Sistema de saúde pessoal com correlações e metas
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import structlog

from supabase import create_client

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError

logger = structlog.get_logger(__name__)


class HealthService:
    """
    Serviço de saúde pessoal.
    
    Funcionalidades:
    - Check-ins de saúde (sono, humor, energia)
    - Metas de saúde
    - Correlações entre hábitos e produtividade
    - Tendências e insights
    """
    
    def __init__(self):
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    # ====================
    # CHECK-INS
    # ====================
    async def create_checkin(
        self,
        user_id: UUID,
        checkin_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria um check-in de saúde.
        
        Args:
            user_id: ID do usuário
            checkin_type: Tipo (morning, evening, health, mood)
            data: Dados do check-in
            
        Returns:
            Check-in criado
        """
        valid_types = ["morning", "evening", "health", "mood", "exercise", "nutrition"]
        if checkin_type not in valid_types:
            raise ValidationError(f"Tipo inválido. Válidos: {valid_types}")
        
        checkin = {
            "user_id": str(user_id),
            "checkin_type": checkin_type,
            "checkin_date": datetime.utcnow().date().isoformat(),
            "data": data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = self.supabase.table("checkins").insert(checkin).execute()
        
        logger.info("checkin_created", user_id=str(user_id), type=checkin_type)
        
        # Processar correlações em background
        await self._process_correlations(user_id, checkin_type, data)
        
        return result.data[0] if result.data else checkin
    
    async def get_checkins(
        self,
        user_id: UUID,
        checkin_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Lista check-ins do usuário.
        
        Args:
            user_id: ID do usuário
            checkin_type: Filtrar por tipo
            start_date: Data inicial
            end_date: Data final
            limit: Limite de resultados
            
        Returns:
            Lista de check-ins
        """
        query = self.supabase.table("checkins")\
            .select("*")\
            .eq("user_id", str(user_id))
        
        if checkin_type:
            query = query.eq("checkin_type", checkin_type)
        
        if start_date:
            query = query.gte("checkin_date", start_date.date().isoformat())
        
        if end_date:
            query = query.lte("checkin_date", end_date.date().isoformat())
        
        result = query.order("checkin_date", desc=True).limit(limit).execute()
        
        return result.data or []
    
    async def get_checkin_streak(
        self,
        user_id: UUID,
        checkin_type: str = "morning"
    ) -> Dict[str, Any]:
        """
        Calcula streak de check-ins consecutivos.
        
        Args:
            user_id: ID do usuário
            checkin_type: Tipo de check-in
            
        Returns:
            Streak atual e máximo
        """
        checkins = await self.get_checkins(
            user_id,
            checkin_type=checkin_type,
            limit=365
        )
        
        if not checkins:
            return {"current_streak": 0, "max_streak": 0, "total_checkins": 0}
        
        # Ordenar por data
        dates = sorted([
            datetime.fromisoformat(c["checkin_date"]).date()
            for c in checkins
        ], reverse=True)
        
        # Calcular streak atual
        current_streak = 0
        today = datetime.utcnow().date()
        
        for i, date in enumerate(dates):
            expected = today - timedelta(days=i)
            if date == expected:
                current_streak += 1
            else:
                break
        
        # Calcular maior streak
        max_streak = current_streak
        temp_streak = 1
        
        for i in range(1, len(dates)):
            if dates[i] == dates[i-1] - timedelta(days=1):
                temp_streak += 1
                max_streak = max(max_streak, temp_streak)
            else:
                temp_streak = 1
        
        return {
            "current_streak": current_streak,
            "max_streak": max_streak,
            "total_checkins": len(checkins)
        }
    
    # ====================
    # METAS DE SAÚDE
    # ====================
    async def create_health_goal(
        self,
        user_id: UUID,
        goal_type: str,
        target_value: float,
        unit: str,
        frequency: str = "daily",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria uma meta de saúde.
        
        Args:
            user_id: ID do usuário
            goal_type: Tipo (sleep, steps, water, exercise, etc)
            target_value: Valor alvo
            unit: Unidade (hours, steps, ml, minutes)
            frequency: Frequência (daily, weekly)
            description: Descrição opcional
            
        Returns:
            Meta criada
        """
        goal = {
            "user_id": str(user_id),
            "goal_type": goal_type,
            "target_value": target_value,
            "unit": unit,
            "frequency": frequency,
            "description": description,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = self.supabase.table("health_goals").insert(goal).execute()
        
        logger.info("health_goal_created", user_id=str(user_id), type=goal_type)
        
        return result.data[0] if result.data else goal
    
    async def get_health_goals(
        self,
        user_id: UUID,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Lista metas de saúde do usuário."""
        query = self.supabase.table("health_goals")\
            .select("*")\
            .eq("user_id", str(user_id))
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.execute()
        
        return result.data or []
    
    async def update_health_goal(
        self,
        user_id: UUID,
        goal_id: UUID,
        **updates
    ) -> Dict[str, Any]:
        """Atualiza uma meta de saúde."""
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        result = self.supabase.table("health_goals")\
            .update(updates)\
            .eq("id", str(goal_id))\
            .eq("user_id", str(user_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError(f"Meta {goal_id} não encontrada")
        
        return result.data[0]
    
    async def get_goal_progress(
        self,
        user_id: UUID,
        goal_id: UUID,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Calcula progresso de uma meta.
        
        Args:
            user_id: ID do usuário
            goal_id: ID da meta
            period_days: Período para análise
            
        Returns:
            Progresso detalhado
        """
        # Buscar meta
        goal_result = self.supabase.table("health_goals")\
            .select("*")\
            .eq("id", str(goal_id))\
            .eq("user_id", str(user_id))\
            .single()\
            .execute()
        
        if not goal_result.data:
            raise NotFoundError(f"Meta {goal_id} não encontrada")
        
        goal = goal_result.data
        
        # Buscar check-ins relacionados
        start_date = datetime.utcnow() - timedelta(days=period_days)
        checkins = await self.get_checkins(
            user_id,
            start_date=start_date,
            limit=period_days * 2
        )
        
        # Extrair valores do tipo da meta
        values = []
        for checkin in checkins:
            data = checkin.get("data", {})
            if goal["goal_type"] in data:
                values.append(data[goal["goal_type"]])
        
        if not values:
            return {
                "goal": goal,
                "progress_percentage": 0,
                "average_value": 0,
                "days_tracked": 0,
                "days_met": 0
            }
        
        avg_value = sum(values) / len(values)
        days_met = sum(1 for v in values if v >= goal["target_value"])
        
        return {
            "goal": goal,
            "progress_percentage": min(100, (avg_value / goal["target_value"]) * 100),
            "average_value": round(avg_value, 2),
            "days_tracked": len(values),
            "days_met": days_met,
            "adherence_rate": round((days_met / len(values)) * 100, 1) if values else 0
        }
    
    # ====================
    # CORRELAÇÕES
    # ====================
    async def _process_correlations(
        self,
        user_id: UUID,
        checkin_type: str,
        data: Dict[str, Any]
    ):
        """
        Processa correlações após um check-in.
        Executado em background.
        """
        try:
            # Só processar se tiver dados suficientes
            checkins = await self.get_checkins(user_id, limit=30)
            
            if len(checkins) < 7:
                return  # Precisa de pelo menos 7 dias
            
            # Calcular correlações
            correlations = self._calculate_correlations(checkins)
            
            # Salvar correlações significativas
            for corr in correlations:
                if abs(corr["correlation"]) >= 0.5:  # Correlação significativa
                    await self._save_correlation(user_id, corr)
            
        except Exception as e:
            logger.error("correlation_processing_failed", error=str(e))
    
    def _calculate_correlations(
        self,
        checkins: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calcula correlações entre métricas de saúde.
        
        Analisa:
        - Sono vs Produtividade
        - Exercício vs Humor
        - Hidratação vs Energia
        """
        correlations = []
        
        # Extrair séries de dados
        series = {}
        metrics = ["sleep_hours", "sleep_quality", "energy", "mood", 
                  "productivity", "exercise_minutes", "water_ml"]
        
        for checkin in checkins:
            date = checkin["checkin_date"]
            data = checkin.get("data", {})
            
            for metric in metrics:
                if metric in data:
                    if metric not in series:
                        series[metric] = {}
                    series[metric][date] = data[metric]
        
        # Calcular correlações entre pares
        pairs_to_check = [
            ("sleep_hours", "productivity"),
            ("sleep_hours", "energy"),
            ("sleep_quality", "mood"),
            ("exercise_minutes", "energy"),
            ("exercise_minutes", "mood"),
            ("water_ml", "energy"),
        ]
        
        for metric1, metric2 in pairs_to_check:
            if metric1 in series and metric2 in series:
                corr = self._pearson_correlation(
                    series[metric1], 
                    series[metric2]
                )
                
                if corr is not None:
                    correlations.append({
                        "metric_1": metric1,
                        "metric_2": metric2,
                        "correlation": corr,
                        "sample_size": min(len(series[metric1]), len(series[metric2]))
                    })
        
        return correlations
    
    def _pearson_correlation(
        self,
        series1: Dict[str, float],
        series2: Dict[str, float]
    ) -> Optional[float]:
        """Calcula correlação de Pearson entre duas séries."""
        # Encontrar datas comuns
        common_dates = set(series1.keys()) & set(series2.keys())
        
        if len(common_dates) < 5:
            return None
        
        x = [series1[d] for d in common_dates]
        y = [series2[d] for d in common_dates]
        
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        # Covariância
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        
        # Desvios padrão
        std_x = (sum((xi - mean_x) ** 2 for xi in x) / n) ** 0.5
        std_y = (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5
        
        if std_x == 0 or std_y == 0:
            return None
        
        correlation = cov / (n * std_x * std_y)
        
        return round(correlation, 3)
    
    async def _save_correlation(
        self,
        user_id: UUID,
        correlation: Dict[str, Any]
    ):
        """Salva correlação no banco."""
        try:
            data = {
                "user_id": str(user_id),
                "metric_1": correlation["metric_1"],
                "metric_2": correlation["metric_2"],
                "correlation_value": correlation["correlation"],
                "sample_size": correlation["sample_size"],
                "calculated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert - atualiza se já existe
            self.supabase.table("health_correlations")\
                .upsert(data, on_conflict="user_id,metric_1,metric_2")\
                .execute()
            
        except Exception as e:
            logger.warning("save_correlation_failed", error=str(e))
    
    async def get_correlations(
        self,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """Lista correlações descobertas para o usuário."""
        result = self.supabase.table("health_correlations")\
            .select("*")\
            .eq("user_id", str(user_id))\
            .order("correlation_value", desc=True)\
            .execute()
        
        return result.data or []
    
    # ====================
    # TENDÊNCIAS E INSIGHTS
    # ====================
    async def get_health_trends(
        self,
        user_id: UUID,
        metric: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analisa tendências de uma métrica de saúde.
        
        Args:
            user_id: ID do usuário
            metric: Métrica a analisar
            period_days: Período
            
        Returns:
            Tendência e estatísticas
        """
        start_date = datetime.utcnow() - timedelta(days=period_days)
        checkins = await self.get_checkins(
            user_id,
            start_date=start_date,
            limit=period_days
        )
        
        # Extrair valores da métrica
        values = []
        for checkin in checkins:
            data = checkin.get("data", {})
            if metric in data:
                values.append({
                    "date": checkin["checkin_date"],
                    "value": data[metric]
                })
        
        if len(values) < 3:
            return {
                "metric": metric,
                "trend": "insufficient_data",
                "data_points": len(values)
            }
        
        # Ordenar por data
        values.sort(key=lambda x: x["date"])
        nums = [v["value"] for v in values]
        
        # Calcular estatísticas
        avg = sum(nums) / len(nums)
        
        # Tendência simples: comparar primeira e segunda metade
        mid = len(nums) // 2
        first_half_avg = sum(nums[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(nums[mid:]) / (len(nums) - mid) if (len(nums) - mid) > 0 else 0
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "improving"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "metric": metric,
            "trend": trend,
            "average": round(avg, 2),
            "min": min(nums),
            "max": max(nums),
            "first_half_avg": round(first_half_avg, 2),
            "second_half_avg": round(second_half_avg, 2),
            "data_points": len(values),
            "period_days": period_days
        }
    
    async def get_health_summary(
        self,
        user_id: UUID,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Gera resumo de saúde do usuário.
        
        Returns:
            Resumo com médias, tendências e recomendações
        """
        # Buscar check-ins
        checkins = await self.get_checkins(user_id, limit=period_days)
        
        # Buscar metas
        goals = await self.get_health_goals(user_id)
        
        # Buscar correlações
        correlations = await self.get_correlations(user_id)
        
        # Calcular médias das métricas
        metrics_sum = {}
        metrics_count = {}
        
        for checkin in checkins:
            data = checkin.get("data", {})
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    metrics_sum[key] = metrics_sum.get(key, 0) + value
                    metrics_count[key] = metrics_count.get(key, 0) + 1
        
        averages = {
            key: round(metrics_sum[key] / metrics_count[key], 2)
            for key in metrics_sum
        }
        
        # Gerar insights
        insights = self._generate_health_insights(averages, correlations)
        
        # Streak de check-ins
        streak = await self.get_checkin_streak(user_id)
        
        return {
            "period_days": period_days,
            "total_checkins": len(checkins),
            "streak": streak,
            "averages": averages,
            "active_goals": len(goals),
            "significant_correlations": len([c for c in correlations if abs(c.get("correlation_value", 0)) >= 0.5]),
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_health_insights(
        self,
        averages: Dict[str, float],
        correlations: List[Dict[str, Any]]
    ) -> List[str]:
        """Gera insights baseados nas métricas e correlações."""
        insights = []
        
        # Análise de sono
        if "sleep_hours" in averages:
            sleep = averages["sleep_hours"]
            if sleep < 6:
                insights.append("⚠️ Média de sono abaixo do recomendado (6-8h). Considere ajustar seus horários.")
            elif sleep > 9:
                insights.append("💤 Dormindo mais que a média. Se sentir cansaço, consulte um médico.")
            else:
                insights.append("✅ Média de sono dentro da faixa saudável!")
        
        # Análise de energia
        if "energy" in averages:
            energy = averages["energy"]
            if energy < 5:
                insights.append("⚡ Níveis de energia baixos. Verifique alimentação, hidratação e sono.")
            elif energy >= 7:
                insights.append("🔋 Ótimos níveis de energia!")
        
        # Insights de correlações
        for corr in correlations[:3]:  # Top 3 correlações
            if abs(corr.get("correlation_value", 0)) >= 0.6:
                m1 = corr["metric_1"].replace("_", " ")
                m2 = corr["metric_2"].replace("_", " ")
                val = corr["correlation_value"]
                
                if val > 0:
                    insights.append(f"📊 Correlação positiva entre {m1} e {m2} ({val:.0%})")
                else:
                    insights.append(f"📊 Correlação negativa entre {m1} e {m2} ({val:.0%})")
        
        return insights


# Singleton
health_service = HealthService()
