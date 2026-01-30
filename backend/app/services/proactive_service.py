"""
TB Personal OS - Proactive Service
Serviço de sugestões proativas baseadas em padrões aprendidos
"""

import structlog
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
import random
from supabase import create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class ProactiveService:
    """
    Serviço que gera e envia sugestões proativas baseadas em:
    - Padrões aprendidos do usuário
    - Contexto atual (tarefas, eventos, objetivos)
    - Horário do dia
    - Histórico de interações
    """
    
    def __init__(self):
        self._supabase = None
        self._telegram = None
    
    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    @property
    def telegram(self):
        """Lazy load do serviço Telegram."""
        if self._telegram is None:
            from app.services.telegram_service import telegram_service
            self._telegram = telegram_service
        return self._telegram
    
    # ==========================================
    # SUGESTÕES CONTEXTUAIS
    # ==========================================
    
    async def send_contextual_suggestions(
        self,
        user_id: str,
        hour: int
    ) -> Dict[str, Any]:
        """
        Gera e envia sugestões baseadas no contexto e horário.
        
        Args:
            user_id: ID do usuário
            hour: Hora atual (para contexto)
        """
        try:
            # Obter dados do usuário
            user = self.supabase.table("users")\
                .select("telegram_chat_id, full_name, preferences")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if not user.data or not user.data.get("telegram_chat_id"):
                return {"success": False, "reason": "User not found or no chat_id"}
            
            chat_id = user.data["telegram_chat_id"]
            preferences = user.data.get("preferences", {})
            
            # Verificar se sugestões proativas estão habilitadas
            if not preferences.get("proactive_suggestions", True):
                return {"success": False, "reason": "Proactive suggestions disabled"}
            
            # Gerar sugestões baseadas no contexto
            suggestions = await self._generate_suggestions(user_id, hour)
            
            if not suggestions:
                return {"success": True, "reason": "No relevant suggestions"}
            
            # Formatar mensagem
            message = self._format_suggestions_message(suggestions, hour)
            
            # Enviar via Telegram
            await self.telegram.send_message(chat_id, message)
            
            # Registrar que sugestão foi enviada
            await self._log_suggestion(user_id, suggestions)
            
            logger.info(
                "proactive_suggestions_sent",
                user_id=user_id,
                suggestions_count=len(suggestions)
            )
            
            return {
                "success": True,
                "suggestions_count": len(suggestions),
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error("send_contextual_suggestions_failed", user_id=user_id, error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _generate_suggestions(
        self,
        user_id: str,
        hour: int
    ) -> List[Dict[str, Any]]:
        """Gera sugestões baseadas em múltiplos fatores."""
        suggestions = []
        
        # 1. Sugestões de tarefas pendentes
        task_suggestions = await self._get_task_suggestions(user_id, hour)
        suggestions.extend(task_suggestions)
        
        # 2. Sugestões de objetivos/metas
        goal_suggestions = await self._get_goal_suggestions(user_id)
        suggestions.extend(goal_suggestions)
        
        # 3. Sugestões baseadas em padrões
        pattern_suggestions = await self._get_pattern_suggestions(user_id, hour)
        suggestions.extend(pattern_suggestions)
        
        # 4. Sugestões de eventos/calendário
        event_suggestions = await self._get_event_suggestions(user_id)
        suggestions.extend(event_suggestions)
        
        # 5. Sugestões de revisão de inbox
        inbox_suggestions = await self._get_inbox_suggestions(user_id)
        suggestions.extend(inbox_suggestions)
        
        # Limitar a 3-5 sugestões mais relevantes
        suggestions = sorted(suggestions, key=lambda x: x.get("priority", 5), reverse=True)
        return suggestions[:5]
    
    async def _get_task_suggestions(
        self,
        user_id: str,
        hour: int
    ) -> List[Dict]:
        """Sugestões baseadas em tarefas."""
        suggestions = []
        today = date.today().isoformat()
        
        try:
            # Tarefas atrasadas
            overdue = self.supabase.table("tasks")\
                .select("id, title, priority, due_date")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .lt("due_date", today)\
                .order("priority", desc=True)\
                .limit(3)\
                .execute()
            
            if overdue.data:
                suggestions.append({
                    "type": "overdue_tasks",
                    "priority": 10,
                    "icon": "⚠️",
                    "title": "Tarefas atrasadas",
                    "description": f"Você tem {len(overdue.data)} tarefa(s) atrasada(s)",
                    "tasks": [t["title"] for t in overdue.data[:3]],
                    "action": "Que tal resolver agora?"
                })
            
            # Tarefas de hoje (manhã)
            if hour < 12:
                today_tasks = self.supabase.table("tasks")\
                    .select("id, title, priority")\
                    .eq("user_id", user_id)\
                    .eq("status", "pending")\
                    .eq("due_date", today)\
                    .order("priority", desc=True)\
                    .limit(5)\
                    .execute()
                
                if today_tasks.data:
                    high_priority = [t for t in today_tasks.data if t.get("priority", 3) >= 4]
                    if high_priority:
                        suggestions.append({
                            "type": "high_priority_today",
                            "priority": 8,
                            "icon": "🔥",
                            "title": "Prioridades do dia",
                            "description": f"{len(high_priority)} tarefa(s) importante(s) para hoje",
                            "tasks": [t["title"] for t in high_priority[:3]],
                            "action": "Foque nessas primeiro!"
                        })
            
            # Tarefas próximas do fim do dia (tarde)
            if hour >= 14:
                pending_today = self.supabase.table("tasks")\
                    .select("id, title")\
                    .eq("user_id", user_id)\
                    .eq("status", "pending")\
                    .eq("due_date", today)\
                    .execute()
                
                if pending_today.data and len(pending_today.data) > 0:
                    suggestions.append({
                        "type": "end_of_day",
                        "priority": 7,
                        "icon": "⏰",
                        "title": "Revisão da tarde",
                        "description": f"Ainda restam {len(pending_today.data)} tarefa(s) para hoje",
                        "tasks": [t["title"] for t in pending_today.data[:3]],
                        "action": "Precisa reagendar alguma?"
                    })
                    
        except Exception as e:
            logger.error("get_task_suggestions_failed", error=str(e))
        
        return suggestions
    
    async def _get_goal_suggestions(self, user_id: str) -> List[Dict]:
        """Sugestões baseadas em objetivos/metas."""
        suggestions = []
        
        try:
            # Verificar se há objetivos com progresso baixo
            goals = self.supabase.table("goals")\
                .select("id, title, progress, target_value, current_value, frequency")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .execute()
            
            if goals.data:
                # Objetivos com pouco progresso
                low_progress = [
                    g for g in goals.data
                    if g.get("progress", 0) < 30 or 
                    (g.get("current_value", 0) / max(g.get("target_value", 1), 1)) < 0.3
                ]
                
                if low_progress:
                    goal = low_progress[0]  # Pegar o primeiro
                    suggestions.append({
                        "type": "goal_reminder",
                        "priority": 6,
                        "icon": "🎯",
                        "title": "Lembrete de objetivo",
                        "description": f"'{goal['title']}' precisa de atenção",
                        "action": f"Progresso: {goal.get('progress', 0):.0f}%"
                    })
            
            # Key Results com deadline próximo
            key_results = self.supabase.table("key_results")\
                .select("id, title, target_date, current_value, target_value")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .gte("target_date", date.today().isoformat())\
                .lte("target_date", (date.today() + timedelta(days=7)).isoformat())\
                .execute()
            
            if key_results.data:
                for kr in key_results.data[:2]:
                    progress = (kr.get("current_value", 0) / max(kr.get("target_value", 1), 1)) * 100
                    if progress < 80:
                        suggestions.append({
                            "type": "key_result_deadline",
                            "priority": 7,
                            "icon": "📊",
                            "title": "Meta próxima",
                            "description": f"'{kr['title']}' vence em breve",
                            "action": f"Progresso atual: {progress:.0f}%"
                        })
                        
        except Exception as e:
            logger.error("get_goal_suggestions_failed", error=str(e))
        
        return suggestions
    
    async def _get_pattern_suggestions(
        self,
        user_id: str,
        hour: int
    ) -> List[Dict]:
        """Sugestões baseadas em padrões aprendidos."""
        suggestions = []
        
        try:
            patterns = self.supabase.table("learned_patterns")\
                .select("pattern_type, pattern_data, confidence")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .gte("confidence", 0.6)\
                .execute()
            
            if not patterns.data:
                return suggestions
            
            for pattern in patterns.data:
                ptype = pattern["pattern_type"]
                pdata = pattern["pattern_data"]
                
                # Padrão de horário de foco
                if ptype == "productivity_cycle":
                    peak_hours = pdata.get("peak_hours", [])
                    if hour in peak_hours:
                        suggestions.append({
                            "type": "peak_hour",
                            "priority": 5,
                            "icon": "⚡",
                            "title": "Hora de pico!",
                            "description": "Este é um dos seus horários mais produtivos",
                            "action": "Aproveite para tarefas que exigem concentração!"
                        })
                
                # Padrão de tipo de tarefa
                if ptype == "time_preference":
                    best_for = pdata.get("best_for", {})
                    if hour < 12 and "creative" in best_for.get("morning", []):
                        suggestions.append({
                            "type": "creative_time",
                            "priority": 4,
                            "icon": "🎨",
                            "title": "Momento criativo",
                            "description": "Manhãs são bons para trabalho criativo",
                            "action": "Que tal focar em algo que exige criatividade?"
                        })
                    elif hour >= 14 and "routine" in best_for.get("afternoon", []):
                        suggestions.append({
                            "type": "routine_time",
                            "priority": 4,
                            "icon": "📋",
                            "title": "Hora das rotinas",
                            "description": "Tardes são boas para tarefas rotineiras",
                            "action": "Bom momento para e-mails e tarefas administrativas"
                        })
                        
        except Exception as e:
            logger.error("get_pattern_suggestions_failed", error=str(e))
        
        return suggestions
    
    async def _get_event_suggestions(self, user_id: str) -> List[Dict]:
        """Sugestões baseadas em eventos do calendário."""
        suggestions = []
        
        try:
            today = date.today().isoformat()
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            
            # Eventos de hoje
            events = self.supabase.table("calendar_events")\
                .select("id, title, start_time, end_time")\
                .eq("user_id", user_id)\
                .gte("start_time", f"{today}T00:00:00")\
                .lt("start_time", f"{tomorrow}T00:00:00")\
                .order("start_time")\
                .execute()
            
            if events.data and len(events.data) > 0:
                # Próximo evento
                now = datetime.now()
                upcoming = [
                    e for e in events.data
                    if datetime.fromisoformat(e["start_time"].replace("Z", "")) > now
                ]
                
                if upcoming:
                    next_event = upcoming[0]
                    event_time = datetime.fromisoformat(next_event["start_time"].replace("Z", ""))
                    time_until = event_time - now
                    
                    if time_until.total_seconds() < 3600:  # Menos de 1 hora
                        suggestions.append({
                            "type": "upcoming_event",
                            "priority": 9,
                            "icon": "📅",
                            "title": "Evento próximo",
                            "description": f"'{next_event['title']}' começa em {int(time_until.total_seconds() / 60)} min",
                            "action": "Prepare-se!"
                        })
                        
        except Exception as e:
            logger.error("get_event_suggestions_failed", error=str(e))
        
        return suggestions
    
    async def _get_inbox_suggestions(self, user_id: str) -> List[Dict]:
        """Sugestões baseadas no inbox."""
        suggestions = []
        
        try:
            # Contar itens não processados
            inbox = self.supabase.table("inbox_items")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .execute()
            
            count = inbox.count if hasattr(inbox, 'count') else len(inbox.data)
            
            if count and count > 5:
                suggestions.append({
                    "type": "inbox_overflow",
                    "priority": 5,
                    "icon": "📥",
                    "title": "Inbox cheio",
                    "description": f"{count} itens aguardando processamento",
                    "action": "Reserve 10 minutos para limpar o inbox!"
                })
            elif count and count > 0:
                suggestions.append({
                    "type": "inbox_reminder",
                    "priority": 3,
                    "icon": "📥",
                    "title": "Revise seu inbox",
                    "description": f"{count} item(ns) para processar",
                    "action": "Use /inbox para ver"
                })
                
        except Exception as e:
            logger.error("get_inbox_suggestions_failed", error=str(e))
        
        return suggestions
    
    def _format_suggestions_message(
        self,
        suggestions: List[Dict],
        hour: int
    ) -> str:
        """Formata as sugestões em uma mensagem amigável."""
        if hour < 12:
            greeting = "🌅 *Bom dia!*"
        elif hour < 18:
            greeting = "☀️ *Boa tarde!*"
        else:
            greeting = "🌙 *Boa noite!*"
        
        lines = [greeting, "", "Algumas sugestões para você:", ""]
        
        for s in suggestions:
            icon = s.get("icon", "•")
            title = s.get("title", "")
            desc = s.get("description", "")
            action = s.get("action", "")
            
            lines.append(f"{icon} *{title}*")
            lines.append(f"   {desc}")
            if action:
                lines.append(f"   _{action}_")
            lines.append("")
        
        lines.append("_Baseado no seu histórico e padrões 🤖_")
        
        return "\n".join(lines)
    
    async def _log_suggestion(
        self,
        user_id: str,
        suggestions: List[Dict]
    ):
        """Registra sugestões enviadas para análise futura."""
        try:
            # Salvar como memória do sistema
            from app.services.context_service import context_service, MemoryCategory
            
            await context_service.add_memory(
                user_id=user_id,
                category=MemoryCategory.CONTEXT,
                content=f"Sugestões proativas enviadas: {[s['type'] for s in suggestions]}",
                importance=2
            )
            
        except Exception as e:
            logger.error("log_suggestion_failed", error=str(e))
    
    # ==========================================
    # APRENDIZADO COM FEEDBACK
    # ==========================================
    
    async def process_suggestion_feedback(
        self,
        user_id: str,
        suggestion_type: str,
        was_useful: bool
    ) -> Dict:
        """
        Processa feedback sobre sugestões para melhorar o sistema.
        """
        try:
            from app.services.context_service import context_service, MemoryCategory
            
            # Registrar feedback
            feedback_text = f"Sugestão '{suggestion_type}' foi {'útil' if was_useful else 'não útil'}"
            
            await context_service.add_memory(
                user_id=user_id,
                category=MemoryCategory.FEEDBACK,
                content=feedback_text,
                importance=4
            )
            
            # Ajustar padrão de sugestões
            await self._adjust_suggestion_pattern(user_id, suggestion_type, was_useful)
            
            return {"success": True}
            
        except Exception as e:
            logger.error("process_suggestion_feedback_failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _adjust_suggestion_pattern(
        self,
        user_id: str,
        suggestion_type: str,
        was_useful: bool
    ):
        """Ajusta padrões baseado no feedback."""
        try:
            # Buscar padrão de preferência de resposta
            pattern = self.supabase.table("learned_patterns")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("pattern_type", "response_preference")\
                .eq("is_active", True)\
                .limit(1)\
                .execute()
            
            if pattern.data:
                current = pattern.data[0]
                data = current["pattern_data"]
                
                # Atualizar preferências de sugestão
                if "suggestion_preferences" not in data:
                    data["suggestion_preferences"] = {}
                
                if suggestion_type not in data["suggestion_preferences"]:
                    data["suggestion_preferences"][suggestion_type] = {"useful": 0, "not_useful": 0}
                
                if was_useful:
                    data["suggestion_preferences"][suggestion_type]["useful"] += 1
                else:
                    data["suggestion_preferences"][suggestion_type]["not_useful"] += 1
                
                # Atualizar
                self.supabase.table("learned_patterns")\
                    .update({
                        "pattern_data": data,
                        "sample_count": current["sample_count"] + 1
                    })\
                    .eq("id", current["id"])\
                    .execute()
            else:
                # Criar novo padrão
                self.supabase.table("learned_patterns")\
                    .insert({
                        "user_id": user_id,
                        "pattern_type": "response_preference",
                        "name": "Preferências de sugestões",
                        "pattern_data": {
                            "suggestion_preferences": {
                                suggestion_type: {
                                    "useful": 1 if was_useful else 0,
                                    "not_useful": 0 if was_useful else 1
                                }
                            }
                        },
                        "confidence": 0.5,
                        "sample_count": 1
                    })\
                    .execute()
                    
        except Exception as e:
            logger.error("adjust_suggestion_pattern_failed", error=str(e))
    
    # ==========================================
    # INSIGHTS PROATIVOS
    # ==========================================
    
    async def generate_weekly_insight(self, user_id: str) -> Optional[str]:
        """
        Gera um insight semanal baseado nos padrões e dados.
        """
        try:
            from app.services.gemini_service import gemini_service
            
            # Coletar dados da semana
            week_ago = (date.today() - timedelta(days=7)).isoformat()
            
            # Tarefas completadas
            completed = self.supabase.table("tasks")\
                .select("title, completed_at")\
                .eq("user_id", user_id)\
                .eq("status", "completed")\
                .gte("completed_at", week_ago)\
                .execute()
            
            # Padrões ativos
            patterns = self.supabase.table("learned_patterns")\
                .select("pattern_type, pattern_data")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .execute()
            
            # Check-ins
            checkins = self.supabase.table("checkins")\
                .select("type, data")\
                .eq("user_id", user_id)\
                .gte("created_at", week_ago)\
                .execute()
            
            # Gerar insight com Gemini
            prompt = f"""
Com base nos dados da semana do usuário, gere UM insight curto e acionável (máximo 2 frases).

Dados:
- Tarefas completadas: {len(completed.data) if completed.data else 0}
- Padrões identificados: {[p['pattern_type'] for p in (patterns.data or [])]}
- Check-ins feitos: {len(checkins.data) if checkins.data else 0}

Gere um insight útil, pessoal e motivador.
"""
            
            insight = await gemini_service.generate_text(
                prompt,
                temperature=0.7,
                max_tokens=100
            )
            
            return insight.strip()
            
        except Exception as e:
            logger.error("generate_weekly_insight_failed", error=str(e))
            return None


# Instância global
proactive_service = ProactiveService()
