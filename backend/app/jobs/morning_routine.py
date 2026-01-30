"""
TB Personal OS - Morning Routine Job
Rotina executada toda manhã
"""

import structlog
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from supabase import create_client, Client

from app.core.config import settings

logger = structlog.get_logger(__name__)


def get_supabase() -> Client:
    """Obtém cliente Supabase."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )


def run_morning_routine(user_id: str):
    """
    Executa a rotina da manhã.
    
    Envia para o usuário:
    1. Saudação personalizada
    2. Resumo da agenda do dia (se conectado ao Google Calendar)
    3. Tarefas prioritárias para hoje
    4. Pergunta sobre energia/disposição
    """
    logger.info("morning_routine_started", user_id=user_id)
    
    try:
        supabase = get_supabase()
        
        # Buscar dados do usuário
        user_data = get_user_data(supabase, user_id)
        if not user_data:
            logger.error("user_not_found", user_id=user_id)
            return
        
        chat_id = user_data.get("chat_id")
        if not chat_id:
            logger.error("chat_id_not_found", user_id=user_id)
            return
        
        # Gerar conteúdo da mensagem
        message = generate_morning_message(supabase, user_id, user_data)
        
        # Enviar via Telegram
        send_telegram_message(chat_id, message)
        
        # Log da execução
        log_routine_execution(supabase, user_id, "morning", message)
        
        logger.info("morning_routine_completed", user_id=user_id)
        
    except Exception as e:
        logger.error("morning_routine_failed", user_id=user_id, error=str(e))
        raise


def get_user_data(supabase: Client, user_id: str) -> Optional[Dict[str, Any]]:
    """Busca dados do usuário."""
    try:
        # Buscar profile
        profile = supabase.table("profiles")\
            .select("*")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        # Buscar telegram chat
        telegram = supabase.table("telegram_chats")\
            .select("chat_id")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        # Buscar user
        user = supabase.table("users")\
            .select("full_name")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        return {
            "profile": profile.data if profile.data else {},
            "chat_id": telegram.data.get("chat_id") if telegram.data else None,
            "name": user.data.get("full_name", "").split()[0] if user.data else "Usuário"
        }
    except Exception as e:
        logger.error("get_user_data_failed", error=str(e))
        return None


def generate_morning_message(
    supabase: Client,
    user_id: str,
    user_data: Dict[str, Any]
) -> str:
    """Gera a mensagem da manhã."""
    
    now = datetime.now()
    today = date.today()
    name = user_data.get("name", "")
    
    # Saudação baseada na hora
    hour = now.hour
    if hour < 12:
        greeting = f"☀️ Bom dia, {name}!"
    else:
        greeting = f"🌤️ Bom dia, {name}!"
    
    parts = [greeting, ""]
    
    # Data
    weekdays_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    parts.append(f"📅 {weekdays_pt[today.weekday()]}, {today.strftime('%d/%m/%Y')}")
    parts.append("")
    
    # Tarefas de hoje
    tasks_today = get_tasks_for_today(supabase, user_id)
    if tasks_today:
        parts.append("📋 *Tarefas para hoje:*")
        for i, task in enumerate(tasks_today[:5], 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "⚪")
            parts.append(f"  {i}. {priority_icon} {task['title']}")
        if len(tasks_today) > 5:
            parts.append(f"  ... e mais {len(tasks_today) - 5} tarefas")
        parts.append("")
    else:
        parts.append("✨ Nenhuma tarefa agendada para hoje!")
        parts.append("")
    
    # Tarefas atrasadas
    overdue = get_overdue_tasks(supabase, user_id)
    if overdue:
        parts.append(f"⚠️ *Atenção:* {len(overdue)} tarefa(s) atrasada(s)")
        for task in overdue[:3]:
            parts.append(f"  • {task['title']}")
        parts.append("")
    
    # Agenda do dia (placeholder para Google Calendar)
    # TODO: Integrar com Google Calendar
    parts.append("📆 *Agenda:* (configure Google Calendar para ver eventos)")
    parts.append("")
    
    # Sugestões baseadas em padrões aprendidos
    pattern_suggestions = get_pattern_based_suggestions(supabase, user_id, hour)
    if pattern_suggestions:
        parts.append("💡 *Sugestões para hoje:*")
        for suggestion in pattern_suggestions[:3]:
            parts.append(f"  • {suggestion}")
        parts.append("")
    
    # Check-in
    parts.append("💪 Como está sua energia hoje?")
    parts.append("Use /checkin para registrar")
    
    return "\n".join(parts)


def get_tasks_for_today(supabase: Client, user_id: str) -> List[Dict]:
    """Busca tarefas para hoje."""
    today = date.today().isoformat()
    
    try:
        result = supabase.table("tasks")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("due_date", today)\
            .in_("status", ["todo", "in_progress"])\
            .order("priority", desc=True)\
            .execute()
        return result.data or []
    except:
        return []


def get_overdue_tasks(supabase: Client, user_id: str) -> List[Dict]:
    """Busca tarefas atrasadas."""
    today = date.today().isoformat()
    
    try:
        result = supabase.table("tasks")\
            .select("*")\
            .eq("user_id", user_id)\
            .lt("due_date", today)\
            .in_("status", ["todo", "in_progress"])\
            .order("due_date")\
            .limit(5)\
            .execute()
        return result.data or []
    except:
        return []


def send_telegram_message(chat_id: int, message: str):
    """Envia mensagem via Telegram API."""
    import requests
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        })
        response.raise_for_status()
        logger.info("telegram_message_sent", chat_id=chat_id)
    except Exception as e:
        logger.error("telegram_send_failed", chat_id=chat_id, error=str(e))
        raise


def log_routine_execution(
    supabase: Client,
    user_id: str,
    routine_type: str,
    message: str
):
    """Loga a execução da rotina."""
    try:
        supabase.table("routine_logs").insert({
            "user_id": user_id,
            "routine_type": routine_type,
            "message_sent": message[:1000],  # Limitar tamanho
            "executed_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        # Tabela pode não existir ainda - ignorar silenciosamente
        logger.debug("routine_log_failed", error=str(e))


def get_pattern_based_suggestions(
    supabase: Client,
    user_id: str,
    hour: int
) -> List[str]:
    """
    Gera sugestões baseadas nos padrões aprendidos do usuário.
    """
    suggestions = []
    
    try:
        # Buscar padrões do usuário
        patterns = supabase.table("learned_patterns")\
            .select("pattern_type, pattern_data, confidence")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .gte("confidence", 0.5)\
            .execute()
        
        if not patterns.data:
            return []
        
        for pattern in patterns.data:
            ptype = pattern["pattern_type"]
            pdata = pattern["pattern_data"]
            confidence = pattern["confidence"]
            
            # Padrão de produtividade
            if ptype == "productivity_cycle":
                peak_hours = pdata.get("peak_hours", [])
                if peak_hours:
                    peak_str = ", ".join([f"{h}h" for h in peak_hours[:3]])
                    suggestions.append(f"Seus horários mais produtivos: {peak_str}")
                
                low_days = pdata.get("low_days", [])
                today_day = datetime.now().strftime("%a").lower()
                if today_day in low_days:
                    suggestions.append("Hoje costuma ser um dia mais lento - considere tarefas mais leves")
            
            # Padrão de horário
            if ptype == "time_preference":
                best_for = pdata.get("best_for", {})
                if "morning" in best_for:
                    morning_tasks = best_for["morning"]
                    if morning_tasks:
                        suggestions.append(f"Manhãs são boas para: {', '.join(morning_tasks[:2])}")
            
            # Padrão de tópicos de interesse
            if ptype == "topic_interest" and confidence >= 0.6:
                topic_counts = pdata.get("topic_counts", {})
                if topic_counts:
                    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:2]
                    if top_topics:
                        focus_areas = ", ".join([t[0] for t in top_topics])
                        suggestions.append(f"Seus focos recentes: {focus_areas}")
        
        # Limitar a 3 sugestões
        return suggestions[:3]
        
    except Exception as e:
        logger.debug("get_pattern_suggestions_failed", error=str(e))
        return []
