"""
Learning Service - Módulo de Aprendizado & Evolução
Gerencia itens de aprendizado, revisão espaçada (SM-2), e trilhas
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ContentType(Enum):
    BOOK = "book"
    ARTICLE = "article"
    COURSE = "course"
    VIDEO = "video"
    PODCAST = "podcast"
    SUMMARY = "summary"
    NOTE = "note"
    HIGHLIGHT = "highlight"
    FLASHCARD = "flashcard"


class LearningStatus(Enum):
    TO_LEARN = "to_learn"
    LEARNING = "learning"
    COMPLETED = "completed"
    REVIEWING = "reviewing"
    MASTERED = "mastered"


class PathStatus(Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class LearningService:
    """Service para Learning OS com revisão espaçada"""
    
    def __init__(self):
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Inicializa cliente Supabase"""
        try:
            from supabase import create_client
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        except Exception as e:
            logger.error("Failed to init Supabase for learning", error=str(e))
    
    # ==========================================
    # LEARNING ITEMS CRUD
    # ==========================================
    
    def create_item(
        self,
        user_id: str,
        title: str,
        content_type: str,
        source_url: Optional[str] = None,
        source_title: Optional[str] = None,
        summary: Optional[str] = None,
        key_insights: Optional[List[str]] = None,
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: int = 5,
        learning_path_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Cria novo item de aprendizado"""
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "content_type": content_type,
                "source_url": source_url,
                "source_title": source_title,
                "summary": summary,
                "key_insights": key_insights or [],
                "topic": topic,
                "tags": tags or [],
                "priority": priority,
                "learning_path_id": learning_path_id,
                "status": "to_learn",
                "next_review": datetime.now().isoformat()
            }
            
            result = self.supabase.table("learning_items").insert(data).execute()
            
            if result.data:
                logger.info("Learning item created", item_id=result.data[0]["id"])
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to create learning item", error=str(e))
            return None
    
    def get_items(
        self,
        user_id: str,
        status: Optional[str] = None,
        content_type: Optional[str] = None,
        topic: Optional[str] = None,
        path_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Lista itens de aprendizado com filtros"""
        try:
            query = self.supabase.table("learning_items")\
                .select("*, learning_paths(title)")\
                .eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            if content_type:
                query = query.eq("content_type", content_type)
            if topic:
                query = query.eq("topic", topic)
            if path_id:
                query = query.eq("learning_path_id", path_id)
            
            result = query.order("priority", desc=True)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("Failed to get learning items", error=str(e))
            return []
    
    def get_item(self, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Obtém item específico"""
        try:
            result = self.supabase.table("learning_items")\
                .select("*, learning_paths(title)")\
                .eq("user_id", user_id)\
                .eq("id", item_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error("Failed to get learning item", error=str(e))
            return None
    
    def update_item(
        self,
        user_id: str,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Atualiza item de aprendizado"""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.supabase.table("learning_items")\
                .update(updates)\
                .eq("user_id", user_id)\
                .eq("id", item_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to update learning item", error=str(e))
            return None
    
    def delete_item(self, user_id: str, item_id: str) -> bool:
        """Remove item de aprendizado"""
        try:
            self.supabase.table("learning_items")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("id", item_id)\
                .execute()
            return True
        except Exception as e:
            logger.error("Failed to delete learning item", error=str(e))
            return False
    
    # ==========================================
    # REVISÃO ESPAÇADA (SM-2 Algorithm)
    # ==========================================
    
    def get_items_for_review(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Obtém itens que precisam de revisão"""
        try:
            now = datetime.now().isoformat()
            
            result = self.supabase.table("learning_items")\
                .select("*")\
                .eq("user_id", user_id)\
                .lte("next_review", now)\
                .neq("status", "mastered")\
                .order("next_review")\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error("Failed to get items for review", error=str(e))
            return []
    
    def record_review(
        self,
        user_id: str,
        item_id: str,
        quality: int,  # 0-5
        time_spent_seconds: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Registra uma sessão de revisão e calcula próxima data
        
        Quality scale (SM-2):
        0 - Completo esquecimento
        1 - Incorreto, lembrou ao ver resposta
        2 - Incorreto, parecia fácil ao ver
        3 - Correto com dificuldade
        4 - Correto após hesitação
        5 - Correto imediatamente
        """
        try:
            # Obtém item atual
            item = self.get_item(user_id, item_id)
            if not item:
                return None
            
            # Calcula novos valores (SM-2 Algorithm)
            ease_factor = float(item.get("ease_factor", 2.5))
            interval = int(item.get("interval_days", 1))
            
            new_ef, new_interval, next_review = self._calculate_sm2(
                quality, ease_factor, interval
            )
            
            # Registra sessão de revisão
            session_data = {
                "user_id": user_id,
                "learning_item_id": item_id,
                "quality": quality,
                "time_spent_seconds": time_spent_seconds,
                "new_ease_factor": new_ef,
                "new_interval": new_interval
            }
            
            self.supabase.table("review_sessions").insert(session_data).execute()
            
            # Atualiza item com novos valores
            new_status = item["status"]
            if quality >= 4 and item["review_count"] >= 5:
                new_status = "mastered"
            elif quality >= 3:
                new_status = "reviewing"
            
            updates = {
                "ease_factor": new_ef,
                "interval_days": new_interval,
                "next_review": next_review.isoformat(),
                "last_reviewed": datetime.now().isoformat(),
                "review_count": item.get("review_count", 0) + 1,
                "status": new_status
            }
            
            if time_spent_seconds:
                updates["time_spent_minutes"] = item.get("time_spent_minutes", 0) + \
                    (time_spent_seconds // 60)
            
            return self.update_item(user_id, item_id, updates)
            
        except Exception as e:
            logger.error("Failed to record review", error=str(e))
            return None
    
    def _calculate_sm2(
        self,
        quality: int,
        ease_factor: float,
        interval: int
    ) -> tuple:
        """
        Implementa o algoritmo SM-2 para revisão espaçada
        Returns: (new_ease_factor, new_interval, next_review_date)
        """
        # Calcula novo ease factor
        new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)  # Mínimo de 1.3
        
        # Calcula novo intervalo
        if quality < 3:
            # Errou - reinicia
            new_interval = 1
        elif interval == 0:
            new_interval = 1
        elif interval == 1:
            new_interval = 6
        else:
            new_interval = round(interval * new_ef)
        
        # Calcula próxima data de revisão
        next_review = datetime.now() + timedelta(days=new_interval)
        
        return (round(new_ef, 2), new_interval, next_review)
    
    def get_review_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Estatísticas de revisão"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Sessões de revisão
            sessions = self.supabase.table("review_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("reviewed_at", start_date)\
                .execute()
            
            sessions_data = sessions.data or []
            
            # Itens por status
            items = self.get_items(user_id, limit=1000)
            
            status_counts = {}
            for item in items:
                status = item.get("status", "to_learn")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calcula métricas
            total_reviews = len(sessions_data)
            avg_quality = sum(s["quality"] for s in sessions_data) / total_reviews \
                if total_reviews > 0 else 0
            
            return {
                "period_days": days,
                "total_reviews": total_reviews,
                "average_quality": round(avg_quality, 2),
                "items_by_status": status_counts,
                "total_items": len(items),
                "mastered_items": status_counts.get("mastered", 0),
                "items_due_for_review": len(self.get_items_for_review(user_id)),
                "retention_rate": round(avg_quality / 5 * 100, 1) if avg_quality > 0 else 0
            }
        except Exception as e:
            logger.error("Failed to get review stats", error=str(e))
            return {}
    
    # ==========================================
    # TRILHAS DE APRENDIZADO
    # ==========================================
    
    def create_path(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        goal: Optional[str] = None,
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None,
        target_completion: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Cria uma nova trilha de aprendizado"""
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "description": description,
                "goal": goal,
                "topic": topic,
                "tags": tags or [],
                "status": "planned"
            }
            
            if target_completion:
                data["target_completion"] = target_completion.isoformat()
            
            result = self.supabase.table("learning_paths").insert(data).execute()
            
            if result.data:
                logger.info("Learning path created", path_id=result.data[0]["id"])
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to create learning path", error=str(e))
            return None
    
    def get_paths(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Lista trilhas de aprendizado"""
        try:
            query = self.supabase.table("learning_paths")\
                .select("*")\
                .eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            
            result = query.order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            paths = result.data or []
            
            # Adiciona contagem de itens para cada trilha
            for path in paths:
                items = self.get_items(user_id, path_id=path["id"], limit=1000)
                path["total_items"] = len(items)
                path["completed_items"] = len([
                    i for i in items 
                    if i["status"] in ["completed", "mastered"]
                ])
                path["progress_percentage"] = round(
                    path["completed_items"] / path["total_items"] * 100
                ) if path["total_items"] > 0 else 0
            
            return paths
        except Exception as e:
            logger.error("Failed to get learning paths", error=str(e))
            return []
    
    def get_path(self, user_id: str, path_id: str) -> Optional[Dict[str, Any]]:
        """Obtém trilha com itens"""
        try:
            result = self.supabase.table("learning_paths")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("id", path_id)\
                .single()\
                .execute()
            
            if result.data:
                path = result.data
                items = self.get_items(user_id, path_id=path_id, limit=100)
                path["items"] = items
                path["total_items"] = len(items)
                path["completed_items"] = len([
                    i for i in items 
                    if i["status"] in ["completed", "mastered"]
                ])
                return path
            return None
        except Exception as e:
            logger.error("Failed to get learning path", error=str(e))
            return None
    
    def update_path(
        self,
        user_id: str,
        path_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Atualiza trilha"""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.supabase.table("learning_paths")\
                .update(updates)\
                .eq("user_id", user_id)\
                .eq("id", path_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to update learning path", error=str(e))
            return None
    
    def start_path(self, user_id: str, path_id: str) -> Optional[Dict[str, Any]]:
        """Inicia uma trilha"""
        return self.update_path(user_id, path_id, {
            "status": "active",
            "started_at": datetime.now().isoformat()
        })
    
    def complete_path(self, user_id: str, path_id: str) -> Optional[Dict[str, Any]]:
        """Marca trilha como completa"""
        return self.update_path(user_id, path_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })
    
    # ==========================================
    # QUICK CAPTURE & INSIGHTS
    # ==========================================
    
    def quick_capture(
        self,
        user_id: str,
        content: str,
        source_url: Optional[str] = None,
        source_title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Captura rápida de insight/nota"""
        return self.create_item(
            user_id=user_id,
            title=content[:100] + "..." if len(content) > 100 else content,
            content_type="note",
            source_url=source_url,
            source_title=source_title,
            summary=content,
            priority=5
        )
    
    def create_flashcard(
        self,
        user_id: str,
        question: str,
        answer: str,
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Cria um flashcard para revisão"""
        return self.create_item(
            user_id=user_id,
            title=question,
            content_type="flashcard",
            summary=answer,
            topic=topic,
            tags=tags,
            priority=7  # Flashcards têm prioridade maior
        )
    
    def get_topic_insights(self, user_id: str, topic: str) -> Dict[str, Any]:
        """Obtém insights de um tópico específico"""
        try:
            items = self.get_items(user_id, topic=topic, limit=100)
            
            all_insights = []
            for item in items:
                insights = item.get("key_insights", [])
                if insights:
                    all_insights.extend(insights)
            
            return {
                "topic": topic,
                "total_items": len(items),
                "items_by_status": {
                    status: len([i for i in items if i["status"] == status])
                    for status in ["to_learn", "learning", "completed", "reviewing", "mastered"]
                },
                "all_insights": all_insights[:20],  # Top 20 insights
                "total_time_minutes": sum(i.get("time_spent_minutes", 0) for i in items),
                "average_ease_factor": sum(
                    float(i.get("ease_factor", 2.5)) for i in items
                ) / len(items) if items else 2.5
            }
        except Exception as e:
            logger.error("Failed to get topic insights", error=str(e))
            return {}
    
    # ==========================================
    # RECOMENDAÇÕES
    # ==========================================
    
    def get_daily_recommendations(
        self,
        user_id: str,
        max_items: int = 5
    ) -> Dict[str, Any]:
        """Gera recomendações diárias de estudo"""
        try:
            # Itens para revisar (prioridade máxima)
            review_items = self.get_items_for_review(user_id, limit=max_items)
            
            # Itens em progresso
            learning_items = self.get_items(
                user_id, 
                status="learning", 
                limit=max_items
            )
            
            # Novos itens de alta prioridade
            new_items = self.supabase.table("learning_items")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "to_learn")\
                .order("priority", desc=True)\
                .limit(max_items)\
                .execute()
            
            # Estatísticas
            stats = self.get_review_stats(user_id, days=7)
            
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "review_required": len(review_items),
                "items_to_review": review_items[:max_items],
                "continue_learning": learning_items[:3],
                "start_new": (new_items.data or [])[:2],
                "weekly_stats": stats,
                "suggested_focus_time": min(60, len(review_items) * 5 + 15),
                "message": self._get_motivation_message(stats)
            }
        except Exception as e:
            logger.error("Failed to get daily recommendations", error=str(e))
            return {}
    
    def _get_motivation_message(self, stats: Dict[str, Any]) -> str:
        """Gera mensagem motivacional baseada nas estatísticas"""
        retention = stats.get("retention_rate", 0)
        mastered = stats.get("mastered_items", 0)
        
        if retention >= 80:
            return f"🌟 Excelente! Sua taxa de retenção está em {retention}%!"
        elif retention >= 60:
            return f"📚 Bom progresso! {mastered} itens dominados. Continue assim!"
        elif stats.get("total_reviews", 0) == 0:
            return "🚀 Hora de começar! Que tal revisar alguns itens hoje?"
        else:
            return "💪 Consistência é a chave! Pratique um pouco todos os dias."


# Singleton
learning_service = LearningService()
