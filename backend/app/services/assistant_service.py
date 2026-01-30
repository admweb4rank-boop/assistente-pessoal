"""
TB Personal OS - Assistant Service
Serviço central de orquestração do assistente
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from supabase import Client, create_client

from app.core.config import settings
from app.services.gemini_service import GeminiService

logger = structlog.get_logger(__name__)


class AssistantService:
    """
    Serviço central do assistente.
    Orquestra classificação, processamento e ações.
    """
    
    def __init__(self, supabase: Optional[Client] = None):
        self._supabase = supabase
        self._gemini: Optional[GeminiService] = None
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
    
    @property
    def gemini(self) -> GeminiService:
        """Lazy load Gemini service."""
        if self._gemini is None:
            self._gemini = GeminiService()
        return self._gemini
    
    # ==========================================
    # CONTEXT MANAGEMENT
    # ==========================================
    
    async def get_user_context(
        self,
        user_id: str,
        include_recent_messages: bool = True,
        include_tasks: bool = True,
        message_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Obtém contexto do usuário para enriquecer interações.
        """
        context = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Buscar profile
            profile = self.supabase.table("profiles")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if profile.data:
                context["profile"] = {
                    "timezone": profile.data[0].get("timezone"),
                    "goals": profile.data[0].get("goals", []),
                    "principles": profile.data[0].get("principles", []),
                    "autonomy_level": profile.data[0].get("autonomy_level", "confirm")
                }
            
            # Buscar mensagens recentes
            if include_recent_messages:
                recent = self.supabase.table("inbox_items")\
                    .select("content, category, created_at")\
                    .eq("user_id", user_id)\
                    .order("created_at", desc=True)\
                    .limit(message_limit)\
                    .execute()
                
                context["recent_messages"] = [
                    {"content": m["content"][:200], "category": m["category"]}
                    for m in recent.data
                ] if recent.data else []
            
            # Buscar tarefas pendentes
            if include_tasks:
                tasks = self.supabase.table("tasks")\
                    .select("title, priority, due_date")\
                    .eq("user_id", user_id)\
                    .in_("status", ["todo", "in_progress"])\
                    .order("priority", desc=True)\
                    .limit(5)\
                    .execute()
                
                context["pending_tasks"] = [
                    {"title": t["title"], "priority": t["priority"], "due": t.get("due_date")}
                    for t in tasks.data
                ] if tasks.data else []
            
            return context
            
        except Exception as e:
            logger.error("get_context_failed", error=str(e), user_id=user_id)
            return context
    
    def _format_context_for_ai(self, context: Dict) -> str:
        """Formata contexto para uso em prompts."""
        parts = []
        
        if context.get("profile"):
            if context["profile"].get("goals"):
                parts.append(f"Objetivos: {', '.join(context['profile']['goals'][:3])}")
        
        if context.get("pending_tasks"):
            tasks = [t["title"] for t in context["pending_tasks"][:3]]
            parts.append(f"Tarefas pendentes: {', '.join(tasks)}")
        
        if context.get("recent_messages"):
            recent = [m["content"][:50] for m in context["recent_messages"][:3]]
            parts.append(f"Mensagens recentes: {' | '.join(recent)}")
        
        return "\n".join(parts) if parts else ""
    
    # ==========================================
    # MESSAGE PROCESSING
    # ==========================================
    
    async def process_message(
        self,
        user_id: str,
        content: str,
        source: str = "api",
        source_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem do usuário.
        
        1. Obtém contexto
        2. Classifica com IA
        3. Salva na inbox
        4. Executa ações automáticas (se configurado)
        5. Gera resposta
        """
        result = {
            "success": False,
            "inbox_item": None,
            "classification": None,
            "response": None,
            "actions_taken": []
        }
        
        try:
            # 1. Obter contexto
            context = await self.get_user_context(user_id)
            context_text = self._format_context_for_ai(context)
            
            # 2. Classificar com IA
            classification = await self.gemini.classify_message(content, context_text)
            result["classification"] = classification
            
            # 3. Salvar na inbox
            inbox_data = {
                "user_id": user_id,
                "content": content,
                "content_type": "text",
                "source": source,
                "status": "new",
                "category": classification.get("category", "other"),
                "tags": [classification.get("type", "note")],
                "source_metadata": source_metadata or {},
                "suggested_actions": classification
            }
            
            inbox_result = self.supabase.table("inbox_items").insert(inbox_data).execute()
            result["inbox_item"] = inbox_result.data[0] if inbox_result.data else None
            
            # 4. Ações automáticas
            await self._execute_auto_actions(user_id, classification, result)
            
            # 5. Gerar resposta se necessário
            if classification.get("needs_response"):
                if classification.get("response"):
                    result["response"] = classification["response"]
                else:
                    result["response"] = await self.gemini.generate_response(
                        content,
                        context_text,
                        context.get("profile")
                    )
            
            # Log da ação
            await self._log_action(
                user_id=user_id,
                action_type="message_processed",
                input_data={"message": content[:500], "source": source},
                output_data=result
            )
            
            result["success"] = True
            
            logger.info(
                "message_processed",
                user_id=user_id,
                type=classification.get("type"),
                category=classification.get("category"),
                method=classification.get("method")
            )
            
        except Exception as e:
            logger.error("process_message_failed", error=str(e), user_id=user_id)
            result["error"] = str(e)
        
        return result
    
    async def _execute_auto_actions(
        self,
        user_id: str,
        classification: Dict,
        result: Dict
    ):
        """Executa ações automáticas baseadas na classificação."""
        # Verificar nível de autonomia do usuário
        profile = self.supabase.table("profiles")\
            .select("autonomy_level")\
            .eq("user_id", user_id)\
            .execute()
        
        autonomy = "confirm"  # default
        if profile.data:
            autonomy = profile.data[0].get("autonomy_level", "confirm")
        
        # Se autonomia é "auto", executar ações automaticamente
        if autonomy == "auto":
            msg_type = classification.get("type")
            
            # Criar tarefa automaticamente se for task
            if msg_type == "task":
                task_data = {
                    "user_id": user_id,
                    "title": classification.get("summary", "Nova tarefa"),
                    "status": "todo",
                    "priority": classification.get("priority", "medium"),
                    "inbox_item_id": result.get("inbox_item", {}).get("id")
                }
                
                # Extrair data se houver
                dates = classification.get("entities", {}).get("dates", [])
                if dates:
                    # TODO: Parse da data
                    pass
                
                task = self.supabase.table("tasks").insert(task_data).execute()
                if task.data:
                    result["actions_taken"].append({
                        "action": "task_created",
                        "task_id": task.data[0]["id"]
                    })
    
    # ==========================================
    # DAILY ROUTINES
    # ==========================================
    
    async def generate_morning_summary(self, user_id: str) -> Dict[str, Any]:
        """Gera resumo da manhã."""
        try:
            today = date.today().isoformat()
            
            # Buscar agenda do dia (se tiver calendar sync)
            # TODO: Integrar com Google Calendar
            
            # Buscar tarefas pendentes
            tasks = self.supabase.table("tasks")\
                .select("*")\
                .eq("user_id", user_id)\
                .in_("status", ["todo", "in_progress"])\
                .order("priority", desc=True)\
                .limit(10)\
                .execute()
            
            pending_tasks = tasks.data if tasks.data else []
            
            # Tarefas para hoje
            today_tasks = [t for t in pending_tasks if t.get("due_date") == today]
            
            # Tarefas atrasadas
            overdue = [t for t in pending_tasks if t.get("due_date") and t["due_date"] < today]
            
            # Gerar resumo com IA
            prompt = f"""Gere um resumo matinal motivacional.

TAREFAS PARA HOJE ({len(today_tasks)}):
{[t['title'] for t in today_tasks[:5]]}

TAREFAS ATRASADAS ({len(overdue)}):
{[t['title'] for t in overdue[:3]]}

TOTAL PENDENTES: {len(pending_tasks)}

Crie um resumo breve (máx 150 palavras) com:
1. Bom dia motivacional
2. Prioridades do dia
3. Alerta de atrasadas (se houver)
4. Uma dica de produtividade

Tom: amigável, energético, focado."""
            
            summary = await self.gemini.generate_text(prompt, temperature=0.7)
            
            return {
                "success": True,
                "summary": summary,
                "data": {
                    "today_tasks": len(today_tasks),
                    "overdue_tasks": len(overdue),
                    "total_pending": len(pending_tasks)
                }
            }
            
        except Exception as e:
            logger.error("morning_summary_failed", error=str(e), user_id=user_id)
            return {"success": False, "error": str(e)}
    
    async def generate_night_summary(self, user_id: str) -> Dict[str, Any]:
        """Gera resumo da noite/fechamento do dia."""
        try:
            today = date.today().isoformat()
            
            # Tarefas concluídas hoje
            done = self.supabase.table("tasks")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "done")\
                .gte("completed_at", today)\
                .execute()
            
            tasks_done = done.data if done.data else []
            
            # Tarefas ainda pendentes
            pending = self.supabase.table("tasks")\
                .select("*")\
                .eq("user_id", user_id)\
                .in_("status", ["todo", "in_progress"])\
                .execute()
            
            tasks_pending = pending.data if pending.data else []
            
            # Inbox do dia
            inbox = self.supabase.table("inbox_items")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("created_at", today)\
                .execute()
            
            inbox_items = inbox.data if inbox.data else []
            
            # Gerar resumo
            summary = await self.gemini.summarize_day(
                tasks_done=tasks_done,
                tasks_pending=tasks_pending,
                inbox_items=inbox_items
            )
            
            return {
                "success": True,
                "summary": summary,
                "data": {
                    "tasks_completed": len(tasks_done),
                    "tasks_pending": len(tasks_pending),
                    "inbox_processed": len(inbox_items)
                }
            }
            
        except Exception as e:
            logger.error("night_summary_failed", error=str(e), user_id=user_id)
            return {"success": False, "error": str(e)}
    
    # ==========================================
    # LOGGING
    # ==========================================
    
    async def _log_action(
        self,
        user_id: str,
        action_type: str,
        input_data: Dict,
        output_data: Dict,
        success: bool = True
    ):
        """Registra ação no log do assistente."""
        try:
            self.supabase.table("assistant_logs").insert({
                "user_id": user_id,
                "action_type": action_type,
                "input_data": input_data,
                "output_data": output_data,
                "success": success,
                "source": "assistant_service"
            }).execute()
        except Exception as e:
            logger.error("log_action_failed", error=str(e))
    
    # ==========================================
    # STATS & INSIGHTS
    # ==========================================
    
    async def get_productivity_stats(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Obtém estatísticas de produtividade."""
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Tarefas concluídas no período
            done = self.supabase.table("tasks")\
                .select("id, completed_at, priority", count="exact")\
                .eq("user_id", user_id)\
                .eq("status", "done")\
                .gte("completed_at", start_date)\
                .execute()
            
            # Tarefas criadas no período
            created = self.supabase.table("tasks")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", start_date)\
                .execute()
            
            # Inbox items no período
            inbox = self.supabase.table("inbox_items")\
                .select("id, category", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", start_date)\
                .execute()
            
            return {
                "period_days": days,
                "tasks_completed": done.count or 0,
                "tasks_created": created.count or 0,
                "completion_rate": round((done.count or 0) / max(created.count or 1, 1) * 100, 1),
                "inbox_items": inbox.count or 0,
                "avg_tasks_per_day": round((done.count or 0) / days, 1)
            }
            
        except Exception as e:
            logger.error("get_stats_failed", error=str(e), user_id=user_id)
            return {"error": str(e)}


# Global instance
assistant_service = AssistantService()
