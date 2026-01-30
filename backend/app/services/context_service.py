"""
TB Personal OS - Context Service (RAG)
Gerencia contexto, memória e busca de informações relevantes
"""

import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from supabase import create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class MemoryCategory(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    PATTERN = "pattern"
    RELATIONSHIP = "relationship"
    GOAL = "goal"
    CONTEXT = "context"
    FEEDBACK = "feedback"


class PatternType(str, Enum):
    TIME_PREFERENCE = "time_preference"
    TASK_CATEGORY = "task_category"
    COMMUNICATION_STYLE = "communication_style"
    PRIORITY_TENDENCY = "priority_tendency"
    PRODUCTIVITY_CYCLE = "productivity_cycle"
    TOPIC_INTEREST = "topic_interest"
    RESPONSE_PREFERENCE = "response_preference"
    WORKFLOW = "workflow"


class ContextService:
    """
    Serviço de contexto que implementa:
    - Busca de contexto relevante para RAG
    - Gerenciamento de memórias de longo prazo
    - Recuperação de padrões aprendidos
    """
    
    def __init__(self):
        self._supabase = None
    
    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    # ==========================================
    # BUSCA DE CONTEXTO (RAG)
    # ==========================================
    
    async def get_context_for_message(
        self,
        user_id: str,
        message: str,
        max_items: int = 10
    ) -> Dict[str, Any]:
        """
        Busca todo o contexto relevante para uma mensagem.
        Combina múltiplas fontes para RAG.
        """
        try:
            context = {
                "user_info": await self._get_user_info(user_id),
                "current_mode": await self._get_current_mode(user_id),
                "recent_messages": await self._get_recent_messages(user_id, limit=5),
                "relevant_memories": await self._search_memories(user_id, message, limit=5),
                "active_patterns": await self._get_active_patterns(user_id),
                "pending_tasks": await self._get_pending_tasks(user_id, limit=5),
                "upcoming_events": await self._get_upcoming_events(user_id),
                "recent_goals": await self._get_recent_goals(user_id),
                "finance_summary": await self._get_finance_summary(user_id),
            }
            
            logger.info(
                "context_gathered",
                user_id=user_id,
                memory_count=len(context.get("relevant_memories", [])),
                pattern_count=len(context.get("active_patterns", []))
            )
            
            return context
            
        except Exception as e:
            logger.error("context_gathering_failed", error=str(e), user_id=user_id)
            return {}
    
    async def _get_user_info(self, user_id: str) -> Dict:
        """Busca informações básicas do usuário."""
        try:
            result = self.supabase.table("users")\
                .select("id, full_name, email, created_at")\
                .eq("id", user_id)\
                .execute()
            
            if result.data:
                user = result.data[0]
                # Buscar profile também
                profile = self.supabase.table("profiles")\
                    .select("timezone, language, preferences")\
                    .eq("user_id", user_id)\
                    .execute()
                
                if profile.data:
                    user.update(profile.data[0])
                
                return user
            return {}
        except Exception as e:
            logger.error("user_info_fetch_failed", error=str(e))
            return {}
    
    async def _get_current_mode(self, user_id: str) -> Optional[Dict]:
        """Busca o modo atual do usuário."""
        try:
            result = self.supabase.table("mode_sessions")\
                .select("""
                    id, started_at,
                    user_modes (
                        id, name, description, system_prompt, personality_traits
                    )
                """)\
                .eq("user_id", user_id)\
                .is_("ended_at", "null")\
                .order("started_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                session = result.data[0]
                return {
                    "session_id": session["id"],
                    "mode": session.get("user_modes", {}),
                    "started_at": session["started_at"]
                }
            return None
        except Exception as e:
            logger.error("mode_fetch_failed", error=str(e))
            return None
    
    async def _get_recent_messages(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Busca mensagens recentes da conversa."""
        try:
            result = self.supabase.table("conversation_messages")\
                .select("role, content, created_at, intent")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return list(reversed(result.data)) if result.data else []
        except Exception as e:
            logger.error("recent_messages_failed", error=str(e))
            return []
    
    async def _search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Busca memórias relevantes para a query.
        TODO: Implementar busca semântica com embeddings.
        """
        try:
            # Busca básica por keywords (sem embeddings por enquanto)
            keywords = query.lower().split()[:5]  # Top 5 palavras
            
            # Busca memórias com maior importância primeiro
            result = self.supabase.table("user_memories")\
                .select("id, category, content, importance, created_at")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .order("importance", desc=True)\
                .order("last_accessed_at", desc=True)\
                .limit(limit * 2)\
                .execute()
            
            if not result.data:
                return []
            
            # Filtragem básica por relevância
            scored_memories = []
            for memory in result.data:
                content_lower = memory["content"].lower()
                score = sum(1 for kw in keywords if kw in content_lower)
                score += memory["importance"] / 10  # Boost por importância
                scored_memories.append((score, memory))
            
            # Ordenar por score e retornar top N
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            memories = [m for _, m in scored_memories[:limit]]
            
            # Atualizar acesso
            for memory in memories:
                self.supabase.table("user_memories")\
                    .update({
                        "last_accessed_at": datetime.utcnow().isoformat(),
                        "access_count": memory.get("access_count", 0) + 1
                    })\
                    .eq("id", memory["id"])\
                    .execute()
            
            return memories
            
        except Exception as e:
            logger.error("memory_search_failed", error=str(e))
            return []
    
    async def _get_active_patterns(self, user_id: str) -> List[Dict]:
        """Busca padrões aprendidos ativos."""
        try:
            result = self.supabase.table("learned_patterns")\
                .select("pattern_type, name, description, pattern_data, confidence")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .gte("confidence", 0.5)\
                .order("confidence", desc=True)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("patterns_fetch_failed", error=str(e))
            return []
    
    async def _get_pending_tasks(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Busca tarefas pendentes."""
        try:
            result = self.supabase.table("tasks")\
                .select("id, title, priority, due_date, project_id")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .order("priority", desc=True)\
                .order("due_date")\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("tasks_fetch_failed", error=str(e))
            return []
    
    async def _get_upcoming_events(self, user_id: str) -> List[Dict]:
        """Busca eventos próximos do calendário."""
        try:
            now = datetime.utcnow()
            end = now + timedelta(days=7)
            
            result = self.supabase.table("calendar_events")\
                .select("id, title, start_time, end_time, description")\
                .eq("user_id", user_id)\
                .gte("start_time", now.isoformat())\
                .lte("start_time", end.isoformat())\
                .order("start_time")\
                .limit(10)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("events_fetch_failed", error=str(e))
            return []
    
    async def _get_recent_goals(self, user_id: str) -> List[Dict]:
        """Busca objetivos ativos."""
        try:
            result = self.supabase.table("goals")\
                .select("id, title, level, progress, target_date")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .order("level")\
                .limit(5)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("goals_fetch_failed", error=str(e))
            return []
    
    async def _get_finance_summary(self, user_id: str) -> Dict:
        """Busca resumo financeiro do mês."""
        try:
            now = datetime.utcnow()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
            
            # Receitas
            income = self.supabase.table("finance_transactions")\
                .select("amount")\
                .eq("user_id", user_id)\
                .eq("type", "income")\
                .gte("date", start_of_month.date().isoformat())\
                .execute()
            
            # Despesas
            expenses = self.supabase.table("finance_transactions")\
                .select("amount")\
                .eq("user_id", user_id)\
                .eq("type", "expense")\
                .gte("date", start_of_month.date().isoformat())\
                .execute()
            
            total_income = sum(t["amount"] for t in (income.data or []))
            total_expenses = sum(t["amount"] for t in (expenses.data or []))
            
            return {
                "month": now.strftime("%B %Y"),
                "income": total_income,
                "expenses": total_expenses,
                "balance": total_income - total_expenses
            }
        except Exception as e:
            logger.error("finance_summary_failed", error=str(e))
            return {}
    
    # ==========================================
    # GERENCIAMENTO DE MEMÓRIAS
    # ==========================================
    
    async def add_memory(
        self,
        user_id: str,
        category: MemoryCategory,
        content: str,
        importance: int = 5,
        session_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Adiciona uma nova memória."""
        try:
            data = {
                "user_id": user_id,
                "category": category.value,
                "content": content,
                "importance": min(max(importance, 1), 10),
                "is_active": True
            }
            
            if session_id:
                data["source_session_id"] = session_id
            if message_id:
                data["source_message_id"] = message_id
            
            result = self.supabase.table("user_memories")\
                .insert(data)\
                .execute()
            
            if result.data:
                logger.info(
                    "memory_added",
                    user_id=user_id,
                    category=category.value,
                    importance=importance
                )
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error("memory_add_failed", error=str(e))
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Atualiza uma memória existente."""
        try:
            data = {}
            if content is not None:
                data["content"] = content
            if importance is not None:
                data["importance"] = min(max(importance, 1), 10)
            if is_active is not None:
                data["is_active"] = is_active
            
            if not data:
                return True
            
            self.supabase.table("user_memories")\
                .update(data)\
                .eq("id", memory_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error("memory_update_failed", error=str(e))
            return False
    
    async def get_memories_by_category(
        self,
        user_id: str,
        category: MemoryCategory,
        limit: int = 20
    ) -> List[Dict]:
        """Busca memórias por categoria."""
        try:
            result = self.supabase.table("user_memories")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("category", category.value)\
                .eq("is_active", True)\
                .order("importance", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("memories_fetch_failed", error=str(e))
            return []
    
    # ==========================================
    # GERENCIAMENTO DE PADRÕES
    # ==========================================
    
    async def add_or_update_pattern(
        self,
        user_id: str,
        pattern_type: PatternType,
        name: str,
        pattern_data: Dict,
        description: Optional[str] = None,
        confidence_delta: float = 0.1
    ) -> Optional[Dict]:
        """Adiciona ou atualiza um padrão aprendido."""
        try:
            # Verificar se padrão já existe
            existing = self.supabase.table("learned_patterns")\
                .select("id, confidence, sample_count")\
                .eq("user_id", user_id)\
                .eq("pattern_type", pattern_type.value)\
                .eq("name", name)\
                .execute()
            
            if existing.data:
                # Atualizar existente
                pattern = existing.data[0]
                new_confidence = min(pattern["confidence"] + confidence_delta, 1.0)
                
                result = self.supabase.table("learned_patterns")\
                    .update({
                        "pattern_data": pattern_data,
                        "confidence": new_confidence,
                        "sample_count": pattern["sample_count"] + 1,
                        "description": description or pattern.get("description")
                    })\
                    .eq("id", pattern["id"])\
                    .execute()
                
                logger.info(
                    "pattern_updated",
                    pattern_id=pattern["id"],
                    new_confidence=new_confidence
                )
                return result.data[0] if result.data else None
            else:
                # Criar novo
                result = self.supabase.table("learned_patterns")\
                    .insert({
                        "user_id": user_id,
                        "pattern_type": pattern_type.value,
                        "name": name,
                        "description": description,
                        "pattern_data": pattern_data,
                        "confidence": 0.5 + confidence_delta,
                        "sample_count": 1,
                        "is_active": True
                    })\
                    .execute()
                
                logger.info(
                    "pattern_created",
                    user_id=user_id,
                    pattern_type=pattern_type.value,
                    name=name
                )
                return result.data[0] if result.data else None
                
        except Exception as e:
            logger.error("pattern_update_failed", error=str(e))
            return None
    
    # ==========================================
    # FORMATAÇÃO DE CONTEXTO PARA PROMPT
    # ==========================================
    
    def format_context_for_prompt(self, context: Dict) -> str:
        """
        Formata o contexto coletado em texto para o prompt do LLM.
        """
        parts = []
        
        # Info do usuário
        user = context.get("user_info", {})
        if user:
            parts.append(f"**Usuário:** {user.get('full_name', 'Desconhecido')}")
            if user.get("timezone"):
                parts.append(f"**Timezone:** {user.get('timezone')}")
        
        # Modo atual
        mode = context.get("current_mode")
        if mode and mode.get("mode"):
            mode_info = mode["mode"]
            parts.append(f"\n**Modo Atual:** {mode_info.get('name', 'Padrão')}")
            if mode_info.get("description"):
                parts.append(f"  {mode_info.get('description')}")
        
        # Memórias relevantes
        memories = context.get("relevant_memories", [])
        if memories:
            parts.append("\n**Memórias Relevantes:**")
            for mem in memories[:5]:
                parts.append(f"- [{mem.get('category', '?')}] {mem.get('content', '')[:100]}")
        
        # Padrões ativos
        patterns = context.get("active_patterns", [])
        if patterns:
            parts.append("\n**Padrões Conhecidos:**")
            for p in patterns[:3]:
                parts.append(f"- {p.get('name', '?')}: {p.get('description', '')[:50]}")
        
        # Tarefas pendentes
        tasks = context.get("pending_tasks", [])
        if tasks:
            parts.append("\n**Tarefas Pendentes:**")
            for t in tasks[:5]:
                due = f" (até {t.get('due_date')})" if t.get("due_date") else ""
                parts.append(f"- {t.get('title', '?')}{due}")
        
        # Eventos próximos
        events = context.get("upcoming_events", [])
        if events:
            parts.append("\n**Próximos Eventos:**")
            for e in events[:3]:
                parts.append(f"- {e.get('title', '?')} - {e.get('start_time', '')[:10]}")
        
        # Objetivos
        goals = context.get("recent_goals", [])
        if goals:
            parts.append("\n**Objetivos Ativos:**")
            for g in goals[:3]:
                parts.append(f"- {g.get('title', '?')} ({g.get('progress', 0)}%)")
        
        # Finanças
        finance = context.get("finance_summary", {})
        if finance:
            parts.append(f"\n**Finanças ({finance.get('month', 'mês')}):**")
            parts.append(f"  Receitas: R$ {finance.get('income', 0):,.2f}")
            parts.append(f"  Despesas: R$ {finance.get('expenses', 0):,.2f}")
            parts.append(f"  Saldo: R$ {finance.get('balance', 0):,.2f}")
        
        # Mensagens recentes
        recent = context.get("recent_messages", [])
        if recent:
            parts.append("\n**Contexto da Conversa:**")
            for msg in recent[-3:]:
                role = "Você" if msg.get("role") == "assistant" else "Usuário"
                content = msg.get("content", "")[:100]
                parts.append(f"  {role}: {content}")
        
        return "\n".join(parts)


# Instância global
context_service = ContextService()
