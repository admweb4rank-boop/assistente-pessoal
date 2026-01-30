"""
TB Personal OS - Content Service
Gerenciamento de ideias de conteúdo e posts
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from uuid import UUID
import pytz

from supabase import Client, create_client
from app.core.config import settings
from app.services.gemini_service import gemini_service

logger = structlog.get_logger(__name__)


class ContentService:
    """
    Serviço para gerenciamento de conteúdo.
    Gerencia ideias, posts e geração de variações com IA.
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
    # IDEAS - CRUD
    # ==========================================
    
    async def create_idea(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        target_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma nova ideia de conteúdo.
        
        Args:
            user_id: ID do usuário
            title: Título da ideia
            description: Descrição detalhada
            content: Rascunho inicial
            category: Categoria
            tags: Tags para organização
            target_channels: Canais pretendidos (instagram, linkedin, etc)
            
        Returns:
            Ideia criada
        """
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "description": description,
                "content": content,
                "category": category,
                "tags": tags or [],
                "target_channels": target_channels or [],
                "status": "idea"
            }
            
            result = self.supabase.table("content_ideas").insert(data).execute()
            
            if result.data:
                logger.info("idea_created", user_id=user_id, idea_id=result.data[0]["id"])
                return result.data[0]
            
            raise ValueError("Falha ao criar ideia")
            
        except Exception as e:
            logger.error("create_idea_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_ideas(
        self,
        user_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista ideias de conteúdo."""
        try:
            query = self.supabase.table("content_ideas") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True)
            
            if status:
                query = query.eq("status", status)
            if category:
                query = query.eq("category", category)
            
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error("get_ideas_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_idea(self, user_id: str, idea_id: str) -> Optional[Dict[str, Any]]:
        """Obtém uma ideia específica."""
        try:
            result = self.supabase.table("content_ideas") \
                .select("*") \
                .eq("id", idea_id) \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error("get_idea_failed", user_id=user_id, idea_id=idea_id, error=str(e))
            return None
    
    async def update_idea(
        self,
        user_id: str,
        idea_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Atualiza uma ideia."""
        try:
            # Filtrar campos válidos
            valid_fields = ["title", "description", "content", "category", "tags", 
                          "target_channels", "status"]
            data = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
            data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("content_ideas") \
                .update(data) \
                .eq("id", idea_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("idea_updated", user_id=user_id, idea_id=idea_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("update_idea_failed", user_id=user_id, idea_id=idea_id, error=str(e))
            raise
    
    async def delete_idea(self, user_id: str, idea_id: str) -> bool:
        """Deleta uma ideia."""
        try:
            result = self.supabase.table("content_ideas") \
                .delete() \
                .eq("id", idea_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("idea_deleted", user_id=user_id, idea_id=idea_id)
                return True
            return False
            
        except Exception as e:
            logger.error("delete_idea_failed", user_id=user_id, idea_id=idea_id, error=str(e))
            raise
    
    # ==========================================
    # IDEAS - AI GENERATION
    # ==========================================
    
    async def generate_variations(
        self,
        user_id: str,
        idea_id: str,
        channels: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Gera variações de conteúdo para diferentes canais usando IA.
        
        Args:
            user_id: ID do usuário
            idea_id: ID da ideia
            channels: Canais para gerar (default: instagram, linkedin)
            
        Returns:
            Dict com variações por canal
        """
        try:
            # Buscar ideia
            idea = await self.get_idea(user_id, idea_id)
            if not idea:
                raise ValueError("Ideia não encontrada")
            
            channels = channels or ["instagram", "linkedin"]
            
            prompt = f"""Gere variações de conteúdo para os canais: {', '.join(channels)}

IDEIA ORIGINAL:
Título: {idea['title']}
Descrição: {idea.get('description', 'N/A')}
Conteúdo: {idea.get('content', 'N/A')}

Para cada canal, gere um texto otimizado considerando:
- Instagram: Texto curto e envolvente, com call to action, use emojis
- LinkedIn: Tom profissional, insightful, pode ser mais longo
- Twitter: Máximo 280 caracteres, direto e impactante
- Blog: Formato de artigo com introdução, desenvolvimento e conclusão
- YouTube: Roteiro com gancho inicial, pontos principais e CTA

Responda em formato JSON:
{{
    "canal": "texto do conteúdo para esse canal",
    ...
}}

Gere APENAS para os canais solicitados: {', '.join(channels)}
"""
            
            response = await gemini_service.generate_content(
                prompt=prompt,
                system_instruction="Você é um especialista em criação de conteúdo digital para redes sociais. Gere conteúdo envolvente e adequado para cada plataforma."
            )
            
            # Tentar parsear JSON
            import json
            try:
                # Limpar resposta
                text = response.get("text", "{}")
                # Remover possíveis marcadores de código
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                variations = json.loads(text.strip())
            except json.JSONDecodeError:
                # Se não conseguir parsear, retornar como está
                variations = {channels[0]: response.get("text", "")}
            
            logger.info(
                "variations_generated",
                user_id=user_id,
                idea_id=idea_id,
                channels=channels
            )
            
            return variations
            
        except Exception as e:
            logger.error("generate_variations_failed", user_id=user_id, idea_id=idea_id, error=str(e))
            raise
    
    # ==========================================
    # POSTS - CRUD
    # ==========================================
    
    async def create_post(
        self,
        user_id: str,
        title: str,
        content: str,
        channel: str,
        idea_id: Optional[str] = None,
        scheduled_for: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Cria um post de conteúdo.
        
        Args:
            user_id: ID do usuário
            title: Título do post
            content: Conteúdo do post
            channel: Canal (instagram, linkedin, etc)
            idea_id: ID da ideia original (opcional)
            scheduled_for: Data/hora para agendamento
            
        Returns:
            Post criado
        """
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "content": content,
                "channel": channel,
                "content_idea_id": idea_id,
                "status": "scheduled" if scheduled_for else "draft",
                "scheduled_for": scheduled_for.isoformat() if scheduled_for else None
            }
            
            result = self.supabase.table("content_posts").insert(data).execute()
            
            if result.data:
                logger.info(
                    "post_created",
                    user_id=user_id,
                    post_id=result.data[0]["id"],
                    channel=channel
                )
                return result.data[0]
            
            raise ValueError("Falha ao criar post")
            
        except Exception as e:
            logger.error("create_post_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_posts(
        self,
        user_id: str,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista posts de conteúdo."""
        try:
            query = self.supabase.table("content_posts") \
                .select("*, content_ideas(title, category)") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True)
            
            if channel:
                query = query.eq("channel", channel)
            if status:
                query = query.eq("status", status)
            
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error("get_posts_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_post(self, user_id: str, post_id: str) -> Optional[Dict[str, Any]]:
        """Obtém um post específico."""
        try:
            result = self.supabase.table("content_posts") \
                .select("*, content_ideas(title, category)") \
                .eq("id", post_id) \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error("get_post_failed", user_id=user_id, post_id=post_id, error=str(e))
            return None
    
    async def update_post(
        self,
        user_id: str,
        post_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Atualiza um post."""
        try:
            valid_fields = ["title", "content", "channel", "status", "scheduled_for",
                          "post_url", "views", "likes", "comments", "shares"]
            data = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
            data["updated_at"] = datetime.utcnow().isoformat()
            
            # Se marcando como publicado
            if kwargs.get("status") == "published" and "published_at" not in kwargs:
                data["published_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("content_posts") \
                .update(data) \
                .eq("id", post_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("post_updated", user_id=user_id, post_id=post_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("update_post_failed", user_id=user_id, post_id=post_id, error=str(e))
            raise
    
    async def delete_post(self, user_id: str, post_id: str) -> bool:
        """Deleta um post."""
        try:
            result = self.supabase.table("content_posts") \
                .delete() \
                .eq("id", post_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("post_deleted", user_id=user_id, post_id=post_id)
                return True
            return False
            
        except Exception as e:
            logger.error("delete_post_failed", user_id=user_id, post_id=post_id, error=str(e))
            raise
    
    # ==========================================
    # CALENDAR & SCHEDULING
    # ==========================================
    
    async def get_calendar(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém calendário editorial.
        
        Args:
            user_id: ID do usuário
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Posts agendados ou publicados no período
        """
        try:
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            
            if not start_date:
                start_date = datetime.now(tz).date()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            from datetime import timedelta
            
            query = self.supabase.table("content_posts") \
                .select("*") \
                .eq("user_id", user_id) \
                .or_(f"status.eq.scheduled,status.eq.published") \
                .order("scheduled_for", desc=False)
            
            # Filtrar por período
            if start_date:
                query = query.gte("scheduled_for", start_date.isoformat())
            if end_date:
                query = query.lte("scheduled_for", end_date.isoformat())
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error("get_calendar_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # METRICS
    # ==========================================
    
    async def update_metrics(
        self,
        user_id: str,
        post_id: str,
        views: Optional[int] = None,
        likes: Optional[int] = None,
        comments: Optional[int] = None,
        shares: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Atualiza métricas de um post."""
        try:
            data = {}
            if views is not None:
                data["views"] = views
            if likes is not None:
                data["likes"] = likes
            if comments is not None:
                data["comments"] = comments
            if shares is not None:
                data["shares"] = shares
            
            # Calcular engagement rate
            if views and views > 0:
                total_engagement = (likes or 0) + (comments or 0) + (shares or 0)
                data["engagement_rate"] = round((total_engagement / views) * 100, 2)
            
            data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("content_posts") \
                .update(data) \
                .eq("id", post_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("metrics_updated", user_id=user_id, post_id=post_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("update_metrics_failed", user_id=user_id, post_id=post_id, error=str(e))
            raise
    
    async def get_content_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém estatísticas de conteúdo.
        
        Returns:
            Estatísticas gerais de conteúdo
        """
        try:
            # Contar ideias
            ideas_result = self.supabase.table("content_ideas") \
                .select("id, status") \
                .eq("user_id", user_id) \
                .execute()
            
            ideas = ideas_result.data or []
            ideas_by_status = {}
            for idea in ideas:
                status = idea["status"]
                ideas_by_status[status] = ideas_by_status.get(status, 0) + 1
            
            # Contar posts
            posts_result = self.supabase.table("content_posts") \
                .select("id, status, channel, views, likes, comments, shares") \
                .eq("user_id", user_id) \
                .execute()
            
            posts = posts_result.data or []
            posts_by_status = {}
            posts_by_channel = {}
            total_views = 0
            total_engagement = 0
            
            for post in posts:
                status = post["status"]
                channel = post["channel"]
                
                posts_by_status[status] = posts_by_status.get(status, 0) + 1
                posts_by_channel[channel] = posts_by_channel.get(channel, 0) + 1
                
                total_views += post.get("views") or 0
                total_engagement += (post.get("likes") or 0) + (post.get("comments") or 0) + (post.get("shares") or 0)
            
            return {
                "ideas": {
                    "total": len(ideas),
                    "by_status": ideas_by_status
                },
                "posts": {
                    "total": len(posts),
                    "by_status": posts_by_status,
                    "by_channel": posts_by_channel
                },
                "metrics": {
                    "total_views": total_views,
                    "total_engagement": total_engagement,
                    "avg_engagement_rate": round((total_engagement / total_views * 100), 2) if total_views > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error("get_content_stats_failed", user_id=user_id, error=str(e))
            raise


# Singleton
content_service = ContentService()
