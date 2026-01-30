"""
TB Personal OS - Night Routine Job
Rotina executada toda noite
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


def run_night_routine(user_id: str):
    """
    Executa a rotina da noite.
    
    Envia para o usuário:
    1. Resumo do dia (tarefas concluídas)
    2. O que ficou pendente
    3. Perguntas de check-in (energia, humor, conquistas)
    4. Preview do dia seguinte
    """
    logger.info("night_routine_started", user_id=user_id)
    
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
        message = generate_night_message(supabase, user_id, user_data)
        
        # Enviar via Telegram
        send_telegram_message(chat_id, message)
        
        # Log da execução
        log_routine_execution(supabase, user_id, "night", message)
        
        logger.info("night_routine_completed", user_id=user_id)
        
    except Exception as e:
        logger.error("night_routine_failed", user_id=user_id, error=str(e))
        raise


def get_user_data(supabase: Client, user_id: str) -> Optional[Dict[str, Any]]:
    """Busca dados do usuário."""
    try:
        profile = supabase.table("profiles")\
            .select("*")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        telegram = supabase.table("telegram_chats")\
            .select("chat_id")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
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


def generate_night_message(
    supabase: Client,
    user_id: str,
    user_data: Dict[str, Any]
) -> str:
    """Gera a mensagem da noite."""
    
    now = datetime.now()
    today = date.today()
    name = user_data.get("name", "")
    
    # Saudação
    parts = [f"🌙 Boa noite, {name}!", ""]
    
    # Resumo do dia
    stats = get_day_stats(supabase, user_id, today)
    
    parts.append("📊 *Resumo do dia:*")
    parts.append(f"  ✅ Tarefas concluídas: {stats['completed']}")
    parts.append(f"  📝 Tarefas criadas: {stats['created']}")
    parts.append(f"  📥 Items na inbox: {stats['inbox_items']}")
    parts.append("")
    
    # Tarefas concluídas hoje
    completed_tasks = get_completed_today(supabase, user_id, today)
    if completed_tasks:
        parts.append("🎉 *Você completou:*")
        for task in completed_tasks[:5]:
            parts.append(f"  • {task['title']}")
        parts.append("")
    
    # O que ficou pendente
    pending = get_pending_tasks(supabase, user_id)
    if pending:
        parts.append(f"⏳ *Pendentes:* {len(pending)} tarefas")
        for task in pending[:3]:
            parts.append(f"  • {task['title']}")
        parts.append("")
    
    # Preview de amanhã
    tomorrow = today + timedelta(days=1)
    tomorrow_tasks = get_tasks_for_date(supabase, user_id, tomorrow)
    if tomorrow_tasks:
        parts.append(f"📅 *Amanhã:* {len(tomorrow_tasks)} tarefas agendadas")
        for task in tomorrow_tasks[:3]:
            parts.append(f"  • {task['title']}")
        parts.append("")
    else:
        parts.append("📅 *Amanhã:* Nenhuma tarefa agendada ainda")
        parts.append("")
    
    # Check-in noturno
    parts.append("💤 *Check-in noturno:*")
    parts.append("Como foi seu dia? (1-10)")
    parts.append("")
    parts.append("Use /checkin energia 7 para registrar")
    parts.append("")
    
    # Mensagem motivacional
    if stats['completed'] > 3:
        parts.append("🌟 Excelente dia! Continue assim!")
    elif stats['completed'] > 0:
        parts.append("👍 Bom progresso! Descanse bem.")
    else:
        parts.append("💪 Amanhã é um novo dia!")
    
    # Insight baseado nos padrões aprendidos
    insight = generate_daily_insight(supabase, user_id, stats)
    if insight:
        parts.append("")
        parts.append(f"💡 *Insight:* {insight}")
    
    return "\n".join(parts)


def get_day_stats(supabase: Client, user_id: str, day: date) -> Dict[str, int]:
    """Busca estatísticas do dia."""
    day_start = datetime.combine(day, datetime.min.time()).isoformat()
    day_end = datetime.combine(day, datetime.max.time()).isoformat()
    
    stats = {
        "completed": 0,
        "created": 0,
        "inbox_items": 0
    }
    
    try:
        # Tarefas completadas hoje
        completed = supabase.table("tasks")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .eq("status", "done")\
            .gte("completed_at", day_start)\
            .lte("completed_at", day_end)\
            .execute()
        stats["completed"] = completed.count or 0
        
        # Tarefas criadas hoje
        created = supabase.table("tasks")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .gte("created_at", day_start)\
            .lte("created_at", day_end)\
            .execute()
        stats["created"] = created.count or 0
        
        # Items na inbox
        inbox = supabase.table("inbox_items")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .gte("created_at", day_start)\
            .lte("created_at", day_end)\
            .execute()
        stats["inbox_items"] = inbox.count or 0
        
    except Exception as e:
        logger.error("get_day_stats_failed", error=str(e))
    
    return stats


def get_completed_today(supabase: Client, user_id: str, day: date) -> List[Dict]:
    """Busca tarefas completadas hoje."""
    day_start = datetime.combine(day, datetime.min.time()).isoformat()
    day_end = datetime.combine(day, datetime.max.time()).isoformat()
    
    try:
        result = supabase.table("tasks")\
            .select("title")\
            .eq("user_id", user_id)\
            .eq("status", "done")\
            .gte("completed_at", day_start)\
            .lte("completed_at", day_end)\
            .execute()
        return result.data or []
    except:
        return []


def get_pending_tasks(supabase: Client, user_id: str) -> List[Dict]:
    """Busca tarefas pendentes."""
    try:
        result = supabase.table("tasks")\
            .select("title, priority")\
            .eq("user_id", user_id)\
            .in_("status", ["todo", "in_progress"])\
            .order("priority", desc=True)\
            .limit(10)\
            .execute()
        return result.data or []
    except:
        return []


def get_tasks_for_date(supabase: Client, user_id: str, target_date: date) -> List[Dict]:
    """Busca tarefas para uma data específica."""
    try:
        result = supabase.table("tasks")\
            .select("title")\
            .eq("user_id", user_id)\
            .eq("due_date", target_date.isoformat())\
            .in_("status", ["todo", "in_progress"])\
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
            "message_sent": message[:1000],
            "executed_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.debug("routine_log_failed", error=str(e))


def generate_daily_insight(
    supabase: Client,
    user_id: str,
    stats: Dict[str, int]
) -> Optional[str]:
    """
    Gera um insight diário baseado nos padrões aprendidos.
    """
    try:
        # Buscar padrão de produtividade
        patterns = supabase.table("learned_patterns")\
            .select("pattern_type, pattern_data")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .gte("confidence", 0.5)\
            .execute()
        
        if not patterns.data:
            return None
        
        insights = []
        today_day = datetime.now().strftime("%a").lower()
        
        for pattern in patterns.data:
            ptype = pattern["pattern_type"]
            pdata = pattern["pattern_data"]
            
            # Comparar com média de produtividade
            if ptype == "productivity_cycle":
                avg_completed = pdata.get("avg_tasks_per_day", 3)
                if stats['completed'] > avg_completed * 1.5:
                    insights.append("Dia muito produtivo! Acima da sua média.")
                elif stats['completed'] < avg_completed * 0.5:
                    peak_days = pdata.get("peak_days", [])
                    if today_day not in peak_days:
                        insights.append("Dia mais lento - normal para hoje. Descanse.")
            
            # Padrão de horário
            if ptype == "time_preference":
                intent_by_period = pdata.get("intent_by_period", {})
                evening_intents = intent_by_period.get("evening", {})
                if evening_intents:
                    # Se costuma criar tarefas à noite
                    if evening_intents.get("task_create", 0) > 3:
                        insights.append("Você costuma planejar à noite. Bom momento para revisar amanhã.")
        
        return insights[0] if insights else None
        
    except Exception as e:
        logger.debug("generate_daily_insight_failed", error=str(e))
        return None
