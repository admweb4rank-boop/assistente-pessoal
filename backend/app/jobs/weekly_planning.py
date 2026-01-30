"""
TB Personal OS - Weekly Planning Job
Rotina executada todo domingo à noite
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


def run_weekly_planning(user_id: str):
    """
    Executa o planejamento semanal.
    
    Envia para o usuário:
    1. Resumo da semana que passou
    2. O que foi conquistado
    3. O que ficou pendente
    4. Preview da semana que vem
    5. Perguntas para planejamento
    """
    logger.info("weekly_planning_started", user_id=user_id)
    
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
        message = generate_weekly_message(supabase, user_id, user_data)
        
        # Enviar via Telegram
        send_telegram_message(chat_id, message)
        
        # Log da execução
        log_routine_execution(supabase, user_id, "weekly", message)
        
        logger.info("weekly_planning_completed", user_id=user_id)
        
    except Exception as e:
        logger.error("weekly_planning_failed", user_id=user_id, error=str(e))
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
            "name": user.data.get("full_name", "").split()[0] if user.data else "Usuário",
            "goals": profile.data.get("goals", []) if profile.data else []
        }
    except Exception as e:
        logger.error("get_user_data_failed", error=str(e))
        return None


def generate_weekly_message(
    supabase: Client,
    user_id: str,
    user_data: Dict[str, Any]
) -> str:
    """Gera a mensagem de planejamento semanal."""
    
    today = date.today()
    name = user_data.get("name", "")
    goals = user_data.get("goals", [])
    
    # Calcular período da semana passada
    week_start = today - timedelta(days=today.weekday() + 7)  # Segunda da semana passada
    week_end = week_start + timedelta(days=6)  # Domingo da semana passada
    
    # Calcular período da próxima semana
    next_week_start = today + timedelta(days=1)  # Segunda
    next_week_end = next_week_start + timedelta(days=6)  # Domingo
    
    parts = [
        f"📅 *Planejamento Semanal*",
        f"Olá, {name}!",
        ""
    ]
    
    # Resumo da semana
    stats = get_week_stats(supabase, user_id, week_start, week_end)
    
    parts.append("📊 *Resumo da Semana:*")
    parts.append(f"  ✅ Tarefas concluídas: {stats['completed']}")
    parts.append(f"  📝 Tarefas criadas: {stats['created']}")
    parts.append(f"  📥 Items processados: {stats['inbox_processed']}")
    parts.append("")
    
    # Taxa de conclusão
    if stats['created'] > 0:
        completion_rate = (stats['completed'] / stats['created']) * 100
        parts.append(f"📈 Taxa de conclusão: {completion_rate:.0f}%")
        
        if completion_rate >= 80:
            parts.append("🌟 Excelente! Semana muito produtiva!")
        elif completion_rate >= 50:
            parts.append("👍 Bom progresso! Continue assim!")
        else:
            parts.append("💪 Próxima semana será melhor!")
        parts.append("")
    
    # Top conquistas
    top_completed = get_completed_tasks_week(supabase, user_id, week_start, week_end)
    if top_completed:
        parts.append("🎉 *Principais conquistas:*")
        for task in top_completed[:5]:
            parts.append(f"  • {task['title']}")
        parts.append("")
    
    # Pendências
    pending = get_pending_tasks(supabase, user_id)
    if pending:
        parts.append(f"⏳ *Tarefas pendentes:* {len(pending)}")
        for task in pending[:5]:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "⚪")
            parts.append(f"  {priority_icon} {task['title']}")
        parts.append("")
    
    # Preview da próxima semana
    next_week_tasks = get_tasks_for_week(supabase, user_id, next_week_start, next_week_end)
    if next_week_tasks:
        parts.append(f"📆 *Próxima semana:* {len(next_week_tasks)} tarefas agendadas")
        
        # Agrupar por dia
        by_day = {}
        for task in next_week_tasks:
            due = task.get("due_date", "")
            if due not in by_day:
                by_day[due] = []
            by_day[due].append(task)
        
        weekdays_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for day_str, tasks in sorted(by_day.items())[:3]:
            try:
                day_date = date.fromisoformat(day_str)
                day_name = weekdays_pt[day_date.weekday()]
                parts.append(f"  {day_name}: {len(tasks)} tarefa(s)")
            except:
                pass
        parts.append("")
    else:
        parts.append("📆 *Próxima semana:* Nenhuma tarefa agendada ainda")
        parts.append("")
    
    # Lembrete dos objetivos
    if goals:
        parts.append("🎯 *Seus objetivos:*")
        for goal in goals[:3]:
            parts.append(f"  • {goal}")
        parts.append("")
    
    # Call to action
    parts.append("💭 *Perguntas para reflexão:*")
    parts.append("  1. O que foi muito bem essa semana?")
    parts.append("  2. O que pode melhorar?")
    parts.append("  3. Qual a prioridade #1 da próxima semana?")
    parts.append("")
    parts.append("Use /task para criar suas tarefas da semana!")
    
    return "\n".join(parts)


def get_week_stats(
    supabase: Client,
    user_id: str,
    week_start: date,
    week_end: date
) -> Dict[str, int]:
    """Busca estatísticas da semana."""
    start_str = datetime.combine(week_start, datetime.min.time()).isoformat()
    end_str = datetime.combine(week_end, datetime.max.time()).isoformat()
    
    stats = {
        "completed": 0,
        "created": 0,
        "inbox_processed": 0
    }
    
    try:
        # Tarefas completadas
        completed = supabase.table("tasks")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .eq("status", "done")\
            .gte("completed_at", start_str)\
            .lte("completed_at", end_str)\
            .execute()
        stats["completed"] = completed.count or 0
        
        # Tarefas criadas
        created = supabase.table("tasks")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .gte("created_at", start_str)\
            .lte("created_at", end_str)\
            .execute()
        stats["created"] = created.count or 0
        
        # Inbox processados
        inbox = supabase.table("inbox_items")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .eq("status", "processed")\
            .gte("created_at", start_str)\
            .lte("created_at", end_str)\
            .execute()
        stats["inbox_processed"] = inbox.count or 0
        
    except Exception as e:
        logger.error("get_week_stats_failed", error=str(e))
    
    return stats


def get_completed_tasks_week(
    supabase: Client,
    user_id: str,
    week_start: date,
    week_end: date
) -> List[Dict]:
    """Busca tarefas completadas na semana."""
    start_str = datetime.combine(week_start, datetime.min.time()).isoformat()
    end_str = datetime.combine(week_end, datetime.max.time()).isoformat()
    
    try:
        result = supabase.table("tasks")\
            .select("title, priority")\
            .eq("user_id", user_id)\
            .eq("status", "done")\
            .gte("completed_at", start_str)\
            .lte("completed_at", end_str)\
            .order("priority", desc=True)\
            .limit(10)\
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


def get_tasks_for_week(
    supabase: Client,
    user_id: str,
    week_start: date,
    week_end: date
) -> List[Dict]:
    """Busca tarefas agendadas para a semana."""
    try:
        result = supabase.table("tasks")\
            .select("title, due_date, priority")\
            .eq("user_id", user_id)\
            .gte("due_date", week_start.isoformat())\
            .lte("due_date", week_end.isoformat())\
            .in_("status", ["todo", "in_progress"])\
            .order("due_date")\
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
