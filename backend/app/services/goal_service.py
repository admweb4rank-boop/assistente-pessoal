"""
Goal Service - Gerenciamento de Objetivos Hierárquicos
Sistema Macro/Meso/Micro com Key Results
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum

from app.core.config import settings
from supabase import create_client, Client


class GoalLevel(str, Enum):
    MACRO = "macro"      # Anual
    MESO = "meso"        # Trimestral
    MICRO = "micro"      # Semanal


class GoalPeriod(str, Enum):
    YEAR = "year"
    QUARTER = "quarter"
    MONTH = "month"
    WEEK = "week"


class GoalStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GoalArea(str, Enum):
    WORK = "work"
    HEALTH = "health"
    FINANCE = "finance"
    RELATIONSHIPS = "relationships"
    LEARNING = "learning"
    PERSONAL = "personal"
    CONTENT = "content"


class GoalService:
    """Serviço para gerenciamento de objetivos hierárquicos."""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    
    # =====================
    # CRUD de Objetivos
    # =====================
    
    async def create_goal(
        self,
        user_id: str,
        title: str,
        level: GoalLevel,
        period_type: GoalPeriod,
        area: Optional[GoalArea] = None,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        target_value: Optional[float] = None,
        key_results: Optional[List[Dict]] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        icon: Optional[str] = None,
        priority: int = 3
    ) -> Dict[str, Any]:
        """Cria um novo objetivo."""
        
        # Calcula período se não fornecido
        if not period_start or not period_end:
            period_start, period_end = self._calculate_period(period_type)
        
        # Gera label do período
        period_label = self._generate_period_label(period_type, period_start)
        
        goal_data = {
            "user_id": user_id,
            "title": title,
            "level": level.value,
            "period_type": period_type.value,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_label": period_label,
            "status": GoalStatus.ACTIVE.value,
            "priority": priority
        }
        
        if description:
            goal_data["description"] = description
        if area:
            goal_data["area"] = area.value
        if parent_id:
            goal_data["parent_id"] = parent_id
        if target_value:
            goal_data["target_value"] = target_value
            goal_data["progress_type"] = "numeric"
        if key_results:
            goal_data["key_results"] = key_results
        if icon:
            goal_data["icon"] = icon
        
        result = self.supabase.table("goals").insert(goal_data).execute()
        
        if result.data:
            return result.data[0]
        raise Exception("Falha ao criar objetivo")
    
    async def get_goal(self, goal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca um objetivo específico."""
        result = self.supabase.table("goals").select("*").eq(
            "id", goal_id
        ).eq("user_id", user_id).single().execute()
        
        return result.data
    
    async def get_goals(
        self,
        user_id: str,
        level: Optional[GoalLevel] = None,
        status: Optional[GoalStatus] = None,
        area: Optional[GoalArea] = None,
        parent_id: Optional[str] = None,
        period_type: Optional[GoalPeriod] = None,
        include_children: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista objetivos com filtros."""
        query = self.supabase.table("goals").select("*").eq("user_id", user_id)
        
        if level:
            query = query.eq("level", level.value)
        if status:
            query = query.eq("status", status.value)
        if area:
            query = query.eq("area", area.value)
        if parent_id:
            query = query.eq("parent_id", parent_id)
        elif not include_children:
            # Se não quer filhos, só pega raízes
            pass
        if period_type:
            query = query.eq("period_type", period_type.value)
        
        query = query.order("priority").order("created_at", desc=True)
        
        result = query.execute()
        return result.data or []
    
    async def get_active_goals_by_period(
        self,
        user_id: str,
        period_type: GoalPeriod
    ) -> List[Dict[str, Any]]:
        """Busca objetivos ativos do período atual."""
        today = date.today()
        
        result = self.supabase.table("goals").select("*").eq(
            "user_id", user_id
        ).eq("status", "active").eq(
            "period_type", period_type.value
        ).lte("period_start", today.isoformat()).gte(
            "period_end", today.isoformat()
        ).order("priority").execute()
        
        return result.data or []
    
    async def update_goal(
        self,
        goal_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Atualiza um objetivo."""
        # Campos permitidos
        allowed_fields = [
            "title", "description", "icon", "area", "priority",
            "target_value", "current_value", "progress_percentage",
            "key_results", "status", "reflection", "lessons_learned"
        ]
        
        filtered_updates = {
            k: v for k, v in updates.items() 
            if k in allowed_fields
        }
        
        # Se marcando como completed, adiciona timestamp
        if filtered_updates.get("status") == "completed":
            filtered_updates["completed_at"] = datetime.utcnow().isoformat()
        
        result = self.supabase.table("goals").update(filtered_updates).eq(
            "id", goal_id
        ).eq("user_id", user_id).execute()
        
        return result.data[0] if result.data else None
    
    async def update_progress(
        self,
        goal_id: str,
        user_id: str,
        progress_percentage: Optional[int] = None,
        current_value: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Atualiza o progresso de um objetivo."""
        updates = {}
        
        if progress_percentage is not None:
            updates["progress_percentage"] = min(100, max(0, progress_percentage))
        if current_value is not None:
            updates["current_value"] = current_value
            # Calcula porcentagem se tiver target
            goal = await self.get_goal(goal_id, user_id)
            if goal and goal.get("target_value"):
                pct = int((current_value / goal["target_value"]) * 100)
                updates["progress_percentage"] = min(100, max(0, pct))
        
        if updates:
            return await self.update_goal(goal_id, user_id, updates)
        return None
    
    async def delete_goal(self, goal_id: str, user_id: str) -> bool:
        """Remove um objetivo."""
        result = self.supabase.table("goals").delete().eq(
            "id", goal_id
        ).eq("user_id", user_id).execute()
        
        return len(result.data) > 0 if result.data else False
    
    # =====================
    # Check-ins
    # =====================
    
    async def add_checkin(
        self,
        user_id: str,
        goal_id: str,
        progress_delta: Optional[float] = None,
        new_progress_percentage: Optional[int] = None,
        notes: Optional[str] = None,
        blockers: Optional[str] = None,
        next_actions: Optional[str] = None,
        confidence_level: Optional[int] = None,
        energy_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Adiciona um check-in de objetivo."""
        checkin_data = {
            "user_id": user_id,
            "goal_id": goal_id
        }
        
        if progress_delta:
            checkin_data["progress_delta"] = progress_delta
        if new_progress_percentage is not None:
            checkin_data["new_progress_percentage"] = new_progress_percentage
            # Atualiza o objetivo também
            await self.update_progress(goal_id, user_id, new_progress_percentage)
        if notes:
            checkin_data["notes"] = notes
        if blockers:
            checkin_data["blockers"] = blockers
        if next_actions:
            checkin_data["next_actions"] = next_actions
        if confidence_level:
            checkin_data["confidence_level"] = min(5, max(1, confidence_level))
        if energy_level:
            checkin_data["energy_level"] = min(5, max(1, energy_level))
        
        result = self.supabase.table("goal_checkins").insert(checkin_data).execute()
        
        if result.data:
            return result.data[0]
        raise Exception("Falha ao criar check-in")
    
    async def get_checkins(
        self,
        goal_id: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Busca check-ins de um objetivo."""
        result = self.supabase.table("goal_checkins").select("*").eq(
            "goal_id", goal_id
        ).eq("user_id", user_id).order(
            "checked_at", desc=True
        ).limit(limit).execute()
        
        return result.data or []
    
    # =====================
    # Hábitos vinculados
    # =====================
    
    async def add_habit(
        self,
        goal_id: str,
        habit_name: str,
        frequency: str = "daily",
        target_per_period: int = 1,
        days_of_week: Optional[List[int]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Adiciona um hábito vinculado a um objetivo."""
        habit_data = {
            "goal_id": goal_id,
            "habit_name": habit_name,
            "frequency": frequency,
            "target_per_period": target_per_period
        }
        
        if days_of_week:
            habit_data["days_of_week"] = days_of_week
        if description:
            habit_data["description"] = description
        
        result = self.supabase.table("goal_habits").insert(habit_data).execute()
        
        if result.data:
            return result.data[0]
        raise Exception("Falha ao criar hábito")
    
    async def complete_habit(
        self,
        habit_id: str,
        notes: Optional[str] = None,
        quality: Optional[int] = None
    ) -> Dict[str, Any]:
        """Registra conclusão de um hábito."""
        completion_data = {
            "habit_id": habit_id,
            "completed_date": date.today().isoformat()
        }
        
        if notes:
            completion_data["notes"] = notes
        if quality:
            completion_data["quality"] = min(5, max(1, quality))
        
        result = self.supabase.table("habit_completions").insert(
            completion_data
        ).execute()
        
        if result.data:
            return result.data[0]
        raise Exception("Falha ao registrar conclusão")
    
    async def get_habits(self, goal_id: str) -> List[Dict[str, Any]]:
        """Busca hábitos de um objetivo."""
        result = self.supabase.table("goal_habits").select("*").eq(
            "goal_id", goal_id
        ).eq("is_active", True).execute()
        
        return result.data or []
    
    # =====================
    # Árvore de Objetivos
    # =====================
    
    async def get_goal_tree(
        self,
        user_id: str,
        root_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca árvore completa de objetivos."""
        # Busca todos os objetivos do usuário
        query = self.supabase.table("goals").select("*").eq("user_id", user_id)
        
        if root_id:
            # Busca apenas a subárvore
            query = query.or_(f"id.eq.{root_id},parent_id.eq.{root_id}")
        
        result = query.order("level").order("priority").execute()
        goals = result.data or []
        
        # Organiza em árvore
        return self._build_tree(goals, root_id)
    
    def _build_tree(
        self,
        goals: List[Dict],
        parent_id: Optional[str] = None
    ) -> List[Dict]:
        """Constrói estrutura de árvore."""
        tree = []
        
        for goal in goals:
            if goal.get("parent_id") == parent_id:
                children = self._build_tree(goals, goal["id"])
                goal_with_children = {**goal, "children": children}
                tree.append(goal_with_children)
        
        return tree
    
    # =====================
    # Resumos e Relatórios
    # =====================
    
    async def get_summary(self, user_id: str) -> Dict[str, Any]:
        """Retorna resumo dos objetivos do usuário."""
        # Busca contagens
        result = self.supabase.table("goals").select(
            "level, status, progress_percentage"
        ).eq("user_id", user_id).execute()
        
        goals = result.data or []
        
        # Agrupa por nível e status
        summary = {
            "total": len(goals),
            "by_level": {},
            "by_status": {},
            "avg_progress": 0,
            "active_macro": 0,
            "active_meso": 0,
            "active_micro": 0
        }
        
        total_progress = 0
        active_count = 0
        
        for goal in goals:
            level = goal.get("level", "unknown")
            status = goal.get("status", "unknown")
            progress = goal.get("progress_percentage", 0)
            
            # Por nível
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
            
            # Por status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Ativos por nível
            if status == "active":
                if level == "macro":
                    summary["active_macro"] += 1
                elif level == "meso":
                    summary["active_meso"] += 1
                elif level == "micro":
                    summary["active_micro"] += 1
                
                total_progress += progress
                active_count += 1
        
        if active_count > 0:
            summary["avg_progress"] = round(total_progress / active_count)
        
        return summary
    
    async def get_current_period_goals(self, user_id: str) -> Dict[str, List[Dict]]:
        """Retorna objetivos do período atual em cada nível."""
        result = {
            "year": await self.get_active_goals_by_period(user_id, GoalPeriod.YEAR),
            "quarter": await self.get_active_goals_by_period(user_id, GoalPeriod.QUARTER),
            "month": await self.get_active_goals_by_period(user_id, GoalPeriod.MONTH),
            "week": await self.get_active_goals_by_period(user_id, GoalPeriod.WEEK)
        }
        return result
    
    # =====================
    # Helpers
    # =====================
    
    def _calculate_period(self, period_type: GoalPeriod) -> tuple:
        """Calcula início e fim do período atual."""
        today = date.today()
        
        if period_type == GoalPeriod.YEAR:
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)
        
        elif period_type == GoalPeriod.QUARTER:
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start = date(today.year, start_month, 1)
            end_month = start_month + 2
            if end_month == 12:
                end = date(today.year, 12, 31)
            else:
                end = date(today.year, end_month + 1, 1) - timedelta(days=1)
        
        elif period_type == GoalPeriod.MONTH:
            start = date(today.year, today.month, 1)
            if today.month == 12:
                end = date(today.year, 12, 31)
            else:
                end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        else:  # WEEK
            start = today - timedelta(days=today.weekday())  # Segunda
            end = start + timedelta(days=6)  # Domingo
        
        return start, end
    
    def _generate_period_label(self, period_type: GoalPeriod, start_date: date) -> str:
        """Gera label legível do período."""
        if period_type == GoalPeriod.YEAR:
            return str(start_date.year)
        
        elif period_type == GoalPeriod.QUARTER:
            quarter = (start_date.month - 1) // 3 + 1
            return f"Q{quarter} {start_date.year}"
        
        elif period_type == GoalPeriod.MONTH:
            months = [
                "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"
            ]
            return f"{months[start_date.month - 1]} {start_date.year}"
        
        else:  # WEEK
            week_num = start_date.isocalendar()[1]
            return f"Semana {week_num}"


# Singleton
goal_service = GoalService()
