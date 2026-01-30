"""
TB Personal OS - Projects Service
Gerencia projetos e suas tarefas
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import Client, create_client

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ProjectService:
    """
    Serviço de gerenciamento de projetos.
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
    # CRUD OPERATIONS
    # ==========================================
    
    async def create_project(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        color: Optional[str] = None,
        due_date: Optional[str] = None,
        goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo projeto.
        """
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "description": description,
                "category": category,
                "color": color or "#3B82F6",  # Azul padrão
                "status": "active",
                "progress": 0,
                "goals": goals or [],
                "due_date": due_date,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("projects").insert(data).execute()
            
            logger.info(
                "project_created",
                project_id=result.data[0]["id"],
                name=name
            )
            
            return result.data[0]
            
        except Exception as e:
            logger.error("create_project_failed", error=str(e))
            raise
    
    async def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém um projeto pelo ID."""
        try:
            result = self.supabase.table("projects")\
                .select("*")\
                .eq("id", project_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error("get_project_failed", error=str(e))
            return None
    
    async def list_projects(
        self,
        user_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista projetos do usuário.
        """
        try:
            query = self.supabase.table("projects")\
                .select("*, tasks:tasks(count)")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if status:
                query = query.eq("status", status)
            if category:
                query = query.eq("category", category)
            
            result = query.execute()
            
            # Calcular progresso para cada projeto
            projects = []
            for proj in result.data or []:
                proj["progress"] = await self._calculate_progress(proj["id"], user_id)
                projects.append(proj)
            
            return projects
            
        except Exception as e:
            logger.error("list_projects_failed", error=str(e))
            return []
    
    async def update_project(
        self,
        project_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza um projeto.
        """
        try:
            # Campos permitidos
            allowed = ["name", "description", "category", "color", "status", "due_date", "goals"]
            filtered_updates = {k: v for k, v in updates.items() if k in allowed}
            
            filtered_updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("projects")\
                .update(filtered_updates)\
                .eq("id", project_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                logger.info("project_updated", project_id=project_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("update_project_failed", error=str(e))
            raise
    
    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """Deleta um projeto."""
        try:
            # Verificar se tem tarefas associadas
            tasks = self.supabase.table("tasks")\
                .select("id", count="exact")\
                .eq("project_id", project_id)\
                .execute()
            
            if tasks.count and tasks.count > 0:
                # Desassociar tarefas
                self.supabase.table("tasks")\
                    .update({"project_id": None})\
                    .eq("project_id", project_id)\
                    .execute()
            
            # Deletar projeto
            self.supabase.table("projects")\
                .delete()\
                .eq("id", project_id)\
                .eq("user_id", user_id)\
                .execute()
            
            logger.info("project_deleted", project_id=project_id)
            return True
            
        except Exception as e:
            logger.error("delete_project_failed", error=str(e))
            return False
    
    # ==========================================
    # PROJECT TASKS
    # ==========================================
    
    async def get_project_tasks(
        self,
        project_id: str,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista tarefas de um projeto."""
        try:
            query = self.supabase.table("tasks")\
                .select("*")\
                .eq("project_id", project_id)\
                .eq("user_id", user_id)\
                .order("priority", desc=True)\
                .order("created_at", desc=True)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error("get_project_tasks_failed", error=str(e))
            return []
    
    async def add_task_to_project(
        self,
        task_id: str,
        project_id: str,
        user_id: str
    ) -> bool:
        """Adiciona uma tarefa a um projeto."""
        try:
            self.supabase.table("tasks")\
                .update({"project_id": project_id})\
                .eq("id", task_id)\
                .eq("user_id", user_id)\
                .execute()
            
            logger.info("task_added_to_project", task_id=task_id, project_id=project_id)
            return True
            
        except Exception as e:
            logger.error("add_task_to_project_failed", error=str(e))
            return False
    
    async def remove_task_from_project(
        self,
        task_id: str,
        user_id: str
    ) -> bool:
        """Remove uma tarefa de um projeto."""
        try:
            self.supabase.table("tasks")\
                .update({"project_id": None})\
                .eq("id", task_id)\
                .eq("user_id", user_id)\
                .execute()
            
            logger.info("task_removed_from_project", task_id=task_id)
            return True
            
        except Exception as e:
            logger.error("remove_task_from_project_failed", error=str(e))
            return False
    
    # ==========================================
    # HELPERS
    # ==========================================
    
    async def _calculate_progress(self, project_id: str, user_id: str) -> int:
        """Calcula o progresso do projeto baseado nas tarefas."""
        try:
            # Total de tarefas
            total = self.supabase.table("tasks")\
                .select("id", count="exact")\
                .eq("project_id", project_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not total.count or total.count == 0:
                return 0
            
            # Tarefas concluídas
            done = self.supabase.table("tasks")\
                .select("id", count="exact")\
                .eq("project_id", project_id)\
                .eq("user_id", user_id)\
                .eq("status", "done")\
                .execute()
            
            progress = int((done.count or 0) / total.count * 100)
            return progress
            
        except:
            return 0
    
    async def get_project_stats(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Obtém estatísticas do projeto."""
        try:
            project = await self.get_project(project_id, user_id)
            if not project:
                return {}
            
            tasks = await self.get_project_tasks(project_id, user_id)
            
            stats = {
                "total_tasks": len(tasks),
                "completed": sum(1 for t in tasks if t["status"] == "done"),
                "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
                "todo": sum(1 for t in tasks if t["status"] == "todo"),
                "high_priority": sum(1 for t in tasks if t.get("priority") in ["high", "urgent"]),
                "progress": await self._calculate_progress(project_id, user_id)
            }
            
            return stats
            
        except Exception as e:
            logger.error("get_project_stats_failed", error=str(e))
            return {}


# Instância global
project_service = ProjectService()
