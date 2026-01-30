"""
TB Personal OS - Memory Service
Sistema de memória e contexto do usuário
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import pytz

from supabase import Client, create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class MemoryService:
    """
    Serviço de memória e contexto.
    Gerencia:
    - Contexto de conversas recentes
    - Preferências do usuário
    - Base de conhecimento
    - Timeline de eventos
    """
    
    def __init__(self, supabase: Optional[Client] = None):
        self._supabase = supabase
        self._context_cache: Dict[str, List[Dict]] = {}
    
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
    # CONVERSATION CONTEXT
    # ==========================================
    
    async def get_recent_context(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Obtém contexto das últimas mensagens/interações.
        
        Args:
            user_id: ID do usuário
            limit: Quantidade de interações a retornar
            
        Returns:
            Lista de interações recentes
        """
        try:
            # Buscar dos logs do assistente
            result = self.supabase.table("assistant_logs") \
                .select("input_data, output_data, action_type, created_at") \
                .eq("user_id", user_id) \
                .eq("action_type", "message") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            context = []
            for log in reversed(result.data or []):
                input_data = log.get("input_data", {})
                output_data = log.get("output_data", {})
                
                context.append({
                    "user_message": input_data.get("message", ""),
                    "assistant_response": output_data.get("response", ""),
                    "timestamp": log.get("created_at")
                })
            
            return context
            
        except Exception as e:
            logger.error("get_recent_context_failed", user_id=user_id, error=str(e))
            return []
    
    async def save_interaction(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Salva uma interação no histórico de conversas.
        
        Args:
            user_id: ID do usuário
            user_message: Mensagem do usuário
            assistant_response: Resposta do assistente
            metadata: Metadados adicionais
            
        Returns:
            True se salvou com sucesso
        """
        try:
            self.supabase.table("assistant_logs").insert({
                "user_id": user_id,
                "action_type": "message",
                "input_data": {
                    "message": user_message,
                    **(metadata or {})
                },
                "output_data": {
                    "response": assistant_response
                },
                "metadata": metadata or {}
            }).execute()
            
            # Limpar cache para forçar reload
            if user_id in self._context_cache:
                del self._context_cache[user_id]
            
            logger.info("interaction_saved", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("save_interaction_failed", user_id=user_id, error=str(e))
            return False
    
    async def format_context_for_llm(
        self,
        user_id: str,
        limit: int = 5
    ) -> str:
        """
        Formata contexto para incluir no prompt do LLM.
        
        Returns:
            String formatada com contexto
        """
        try:
            context = await self.get_recent_context(user_id, limit)
            
            if not context:
                return ""
            
            formatted = "## Contexto das últimas conversas:\n"
            for i, c in enumerate(context, 1):
                formatted += f"\n### Interação {i}:\n"
                formatted += f"Usuário: {c['user_message']}\n"
                formatted += f"Assistente: {c['assistant_response']}\n"
            
            return formatted
            
        except Exception as e:
            logger.error("format_context_failed", user_id=user_id, error=str(e))
            return ""
    
    # ==========================================
    # USER PROFILE & PREFERENCES
    # ==========================================
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém perfil completo do usuário.
        
        Returns:
            Perfil com preferências, objetivos e princípios
        """
        try:
            result = self.supabase.table("profiles") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error("get_profile_failed", user_id=user_id, error=str(e))
            return None
    
    async def update_profile(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza perfil do usuário.
        
        Campos atualizáveis:
        - timezone
        - language
        - notify_morning_summary
        - notify_night_summary
        - morning_summary_time
        - night_summary_time
        - autonomy_level
        - goals
        - principles
        """
        try:
            valid_fields = [
                "timezone", "language", "notify_morning_summary",
                "notify_night_summary", "notify_weekly_planning",
                "morning_summary_time", "night_summary_time",
                "autonomy_level", "goals", "principles"
            ]
            
            data = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
            data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("profiles") \
                .update(data) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("profile_updated", user_id=user_id, fields=list(data.keys()))
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("update_profile_failed", user_id=user_id, error=str(e))
            raise
    
    async def add_goal(
        self,
        user_id: str,
        goal: str,
        category: str = "general"
    ) -> bool:
        """Adiciona um objetivo ao perfil."""
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                return False
            
            goals = profile.get("goals") or []
            goals.append({
                "text": goal,
                "category": category,
                "added_at": datetime.utcnow().isoformat()
            })
            
            await self.update_profile(user_id, goals=goals)
            logger.info("goal_added", user_id=user_id, goal=goal)
            return True
            
        except Exception as e:
            logger.error("add_goal_failed", user_id=user_id, error=str(e))
            return False
    
    async def add_principle(
        self,
        user_id: str,
        principle: str
    ) -> bool:
        """Adiciona um princípio ao perfil."""
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                return False
            
            principles = profile.get("principles") or []
            principles.append({
                "text": principle,
                "added_at": datetime.utcnow().isoformat()
            })
            
            await self.update_profile(user_id, principles=principles)
            logger.info("principle_added", user_id=user_id, principle=principle)
            return True
            
        except Exception as e:
            logger.error("add_principle_failed", user_id=user_id, error=str(e))
            return False
    
    # ==========================================
    # KNOWLEDGE BASE (MEMORIES)
    # ==========================================
    
    async def remember(
        self,
        user_id: str,
        content: str,
        category: str = "general",
        source: str = "user",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Salva uma memória/informação.
        
        Args:
            user_id: ID do usuário
            content: Conteúdo a lembrar
            category: Categoria (general, personal, work, etc)
            source: Origem (user, assistant, system)
            metadata: Dados adicionais
            
        Returns:
            Memória salva
        """
        try:
            data = {
                "user_id": user_id,
                "content": content,
                "context_type": category,
                "source": source,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("contexts").insert(data).execute()
            
            if result.data:
                logger.info("memory_saved", user_id=user_id, category=category)
                return result.data[0]
            
            raise ValueError("Falha ao salvar memória")
            
        except Exception as e:
            logger.error("remember_failed", user_id=user_id, error=str(e))
            raise
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca memórias por texto.
        
        Args:
            user_id: ID do usuário
            query: Termo de busca
            category: Filtrar por categoria
            limit: Máximo de resultados
            
        Returns:
            Lista de memórias encontradas
        """
        try:
            # Busca por texto (usando ilike para case-insensitive)
            base_query = self.supabase.table("contexts") \
                .select("*") \
                .eq("user_id", user_id) \
                .ilike("content", f"%{query}%") \
                .order("created_at", desc=True) \
                .limit(limit)
            
            if category:
                base_query = base_query.eq("context_type", category)
            
            result = base_query.execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error("search_memories_failed", user_id=user_id, query=query, error=str(e))
            return []
    
    async def get_all_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Lista todas as memórias."""
        try:
            query = self.supabase.table("contexts") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit)
            
            if category:
                query = query.eq("context_type", category)
            
            result = query.execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error("get_all_memories_failed", user_id=user_id, error=str(e))
            return []
    
    async def delete_memory(
        self,
        user_id: str,
        memory_id: str
    ) -> bool:
        """Deleta uma memória."""
        try:
            result = self.supabase.table("contexts") \
                .delete() \
                .eq("id", memory_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("memory_deleted", user_id=user_id, memory_id=memory_id)
                return True
            return False
            
        except Exception as e:
            logger.error("delete_memory_failed", user_id=user_id, memory_id=memory_id, error=str(e))
            return False
    
    # ==========================================
    # TIMELINE
    # ==========================================
    
    async def get_timeline(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém timeline de eventos e atividades.
        
        Combina:
        - Logs de assistente
        - Tarefas concluídas
        - Check-ins
        - Eventos do calendário
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            
            if not end_date:
                end_date = datetime.now(tz)
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            timeline = []
            
            # Logs do assistente
            logs_result = self.supabase.table("assistant_logs") \
                .select("id, action_type, input_data, created_at") \
                .eq("user_id", user_id) \
                .gte("created_at", start_date.isoformat()) \
                .lte("created_at", end_date.isoformat()) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            for log in logs_result.data or []:
                timeline.append({
                    "type": "assistant_interaction",
                    "action": log.get("action_type"),
                    "summary": log.get("input_data", {}).get("message", "")[:100],
                    "timestamp": log.get("created_at")
                })
            
            # Tarefas concluídas
            tasks_result = self.supabase.table("tasks") \
                .select("id, title, completed_at") \
                .eq("user_id", user_id) \
                .eq("status", "done") \
                .gte("completed_at", start_date.isoformat()) \
                .lte("completed_at", end_date.isoformat()) \
                .execute()
            
            for task in tasks_result.data or []:
                if task.get("completed_at"):
                    timeline.append({
                        "type": "task_completed",
                        "title": task.get("title"),
                        "timestamp": task.get("completed_at")
                    })
            
            # Check-ins
            checkins_result = self.supabase.table("checkins") \
                .select("id, checkin_type, value, created_at") \
                .eq("user_id", user_id) \
                .gte("created_at", start_date.isoformat()) \
                .lte("created_at", end_date.isoformat()) \
                .execute()
            
            for checkin in checkins_result.data or []:
                timeline.append({
                    "type": "checkin",
                    "checkin_type": checkin.get("checkin_type"),
                    "value": checkin.get("value"),
                    "timestamp": checkin.get("created_at")
                })
            
            # Ordenar por timestamp
            timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return timeline[:limit]
            
        except Exception as e:
            logger.error("get_timeline_failed", user_id=user_id, error=str(e))
            return []
    
    # ==========================================
    # CONTEXT SUMMARY FOR LLM
    # ==========================================
    
    async def get_full_context(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém contexto completo para o LLM.
        
        Returns:
            Dict com todo contexto relevante
        """
        try:
            # Perfil
            profile = await self.get_profile(user_id) or {}
            
            # Conversas recentes
            recent_context = await self.get_recent_context(user_id, limit=5)
            
            # Memórias relevantes (últimas)
            memories = await self.get_all_memories(user_id, limit=10)
            
            return {
                "profile": {
                    "timezone": profile.get("timezone"),
                    "language": profile.get("language"),
                    "autonomy_level": profile.get("autonomy_level"),
                    "goals": profile.get("goals", []),
                    "principles": profile.get("principles", [])
                },
                "recent_conversations": recent_context,
                "memories": [
                    {
                        "content": m.get("content"),
                        "category": m.get("context_type"),
                        "date": m.get("created_at")
                    }
                    for m in memories
                ]
            }
            
        except Exception as e:
            logger.error("get_full_context_failed", user_id=user_id, error=str(e))
            return {}
    
    async def format_full_context_for_llm(self, user_id: str) -> str:
        """
        Formata todo o contexto para incluir no prompt do LLM.
        
        Returns:
            String formatada com todo contexto
        """
        try:
            context = await self.get_full_context(user_id)
            
            formatted = "## Contexto do Usuário:\n\n"
            
            # Perfil
            profile = context.get("profile", {})
            if profile.get("goals"):
                formatted += "### Objetivos:\n"
                for goal in profile["goals"]:
                    if isinstance(goal, dict):
                        formatted += f"- {goal.get('text', goal)}\n"
                    else:
                        formatted += f"- {goal}\n"
                formatted += "\n"
            
            if profile.get("principles"):
                formatted += "### Princípios:\n"
                for principle in profile["principles"]:
                    if isinstance(principle, dict):
                        formatted += f"- {principle.get('text', principle)}\n"
                    else:
                        formatted += f"- {principle}\n"
                formatted += "\n"
            
            # Conversas recentes
            conversations = context.get("recent_conversations", [])
            if conversations:
                formatted += "### Últimas Conversas:\n"
                for conv in conversations[-3:]:  # Últimas 3
                    formatted += f"Usuário: {conv.get('user_message', '')[:100]}\n"
                    formatted += f"Assistente: {conv.get('assistant_response', '')[:100]}\n\n"
            
            # Memórias relevantes
            memories = context.get("memories", [])
            if memories:
                formatted += "### Informações Salvas:\n"
                for mem in memories[:5]:  # Top 5
                    formatted += f"- [{mem.get('category', 'geral')}] {mem.get('content', '')[:100]}\n"
            
            return formatted
            
        except Exception as e:
            logger.error("format_full_context_failed", user_id=user_id, error=str(e))
            return ""


# Singleton
memory_service = MemoryService()
