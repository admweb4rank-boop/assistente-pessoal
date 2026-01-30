"""
TB Personal OS - Content API Endpoints
Endpoints para gerenciamento de conteúdo (ideias e posts)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel
import structlog

from app.api.v1.dependencies.auth import get_current_user
from app.services.content_service import content_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/content", tags=["Content"])


# ==========================================
# SCHEMAS
# ==========================================

class IdeaCreate(BaseModel):
    """Dados para criar ideia."""
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    target_channels: Optional[List[str]] = None


class IdeaUpdate(BaseModel):
    """Dados para atualizar ideia."""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    target_channels: Optional[List[str]] = None
    status: Optional[str] = None


class PostCreate(BaseModel):
    """Dados para criar post."""
    title: str
    content: str
    channel: str
    idea_id: Optional[str] = None
    scheduled_for: Optional[datetime] = None


class PostUpdate(BaseModel):
    """Dados para atualizar post."""
    title: Optional[str] = None
    content: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    post_url: Optional[str] = None


class MetricsUpdate(BaseModel):
    """Dados para atualizar métricas."""
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None


class GenerateVariationsRequest(BaseModel):
    """Dados para gerar variações."""
    channels: Optional[List[str]] = None


# ==========================================
# IDEAS ENDPOINTS
# ==========================================

@router.post("/ideas")
async def create_idea(
    data: IdeaCreate,
    user: dict = Depends(get_current_user)
):
    """Cria uma nova ideia de conteúdo."""
    try:
        idea = await content_service.create_idea(
            user_id=user["id"],
            title=data.title,
            description=data.description,
            content=data.content,
            category=data.category,
            tags=data.tags,
            target_channels=data.target_channels
        )
        return idea
        
    except Exception as e:
        logger.error("create_idea_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar ideia: {str(e)}")


@router.get("/ideas")
async def list_ideas(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    """Lista ideias de conteúdo."""
    try:
        ideas = await content_service.get_ideas(
            user_id=user["id"],
            status=status,
            category=category,
            limit=limit,
            offset=offset
        )
        return {"ideas": ideas, "count": len(ideas)}
        
    except Exception as e:
        logger.error("list_ideas_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao listar ideias: {str(e)}")


@router.get("/ideas/{idea_id}")
async def get_idea(
    idea_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtém uma ideia específica."""
    try:
        idea = await content_service.get_idea(user["id"], idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Ideia não encontrada")
        return idea
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_idea_failed", user_id=user["id"], idea_id=idea_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar ideia: {str(e)}")


@router.patch("/ideas/{idea_id}")
async def update_idea(
    idea_id: str,
    data: IdeaUpdate,
    user: dict = Depends(get_current_user)
):
    """Atualiza uma ideia."""
    try:
        idea = await content_service.update_idea(
            user_id=user["id"],
            idea_id=idea_id,
            **data.model_dump(exclude_none=True)
        )
        if not idea:
            raise HTTPException(status_code=404, detail="Ideia não encontrada")
        return idea
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_idea_failed", user_id=user["id"], idea_id=idea_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar ideia: {str(e)}")


@router.delete("/ideas/{idea_id}")
async def delete_idea(
    idea_id: str,
    user: dict = Depends(get_current_user)
):
    """Deleta uma ideia."""
    try:
        deleted = await content_service.delete_idea(user["id"], idea_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ideia não encontrada")
        return {"status": "success", "message": "Ideia deletada"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_idea_failed", user_id=user["id"], idea_id=idea_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao deletar ideia: {str(e)}")


@router.post("/ideas/{idea_id}/variations")
async def generate_variations(
    idea_id: str,
    data: GenerateVariationsRequest,
    user: dict = Depends(get_current_user)
):
    """
    Gera variações de conteúdo para diferentes canais usando IA.
    
    Canais suportados: instagram, linkedin, twitter, blog, youtube
    """
    try:
        variations = await content_service.generate_variations(
            user_id=user["id"],
            idea_id=idea_id,
            channels=data.channels
        )
        return {"variations": variations}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("generate_variations_failed", user_id=user["id"], idea_id=idea_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao gerar variações: {str(e)}")


# ==========================================
# POSTS ENDPOINTS
# ==========================================

@router.post("/posts")
async def create_post(
    data: PostCreate,
    user: dict = Depends(get_current_user)
):
    """Cria um novo post."""
    try:
        post = await content_service.create_post(
            user_id=user["id"],
            title=data.title,
            content=data.content,
            channel=data.channel,
            idea_id=data.idea_id,
            scheduled_for=data.scheduled_for
        )
        return post
        
    except Exception as e:
        logger.error("create_post_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar post: {str(e)}")


@router.get("/posts")
async def list_posts(
    channel: Optional[str] = Query(None, description="Filtrar por canal"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    """Lista posts de conteúdo."""
    try:
        posts = await content_service.get_posts(
            user_id=user["id"],
            channel=channel,
            status=status,
            limit=limit,
            offset=offset
        )
        return {"posts": posts, "count": len(posts)}
        
    except Exception as e:
        logger.error("list_posts_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao listar posts: {str(e)}")


@router.get("/posts/{post_id}")
async def get_post(
    post_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtém um post específico."""
    try:
        post = await content_service.get_post(user["id"], post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_post_failed", user_id=user["id"], post_id=post_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar post: {str(e)}")


@router.patch("/posts/{post_id}")
async def update_post(
    post_id: str,
    data: PostUpdate,
    user: dict = Depends(get_current_user)
):
    """Atualiza um post."""
    try:
        post = await content_service.update_post(
            user_id=user["id"],
            post_id=post_id,
            **data.model_dump(exclude_none=True)
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_post_failed", user_id=user["id"], post_id=post_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar post: {str(e)}")


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    user: dict = Depends(get_current_user)
):
    """Deleta um post."""
    try:
        deleted = await content_service.delete_post(user["id"], post_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return {"status": "success", "message": "Post deletado"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_post_failed", user_id=user["id"], post_id=post_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao deletar post: {str(e)}")


@router.post("/posts/{post_id}/metrics")
async def update_post_metrics(
    post_id: str,
    data: MetricsUpdate,
    user: dict = Depends(get_current_user)
):
    """Atualiza métricas de um post."""
    try:
        post = await content_service.update_metrics(
            user_id=user["id"],
            post_id=post_id,
            views=data.views,
            likes=data.likes,
            comments=data.comments,
            shares=data.shares
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_metrics_failed", user_id=user["id"], post_id=post_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar métricas: {str(e)}")


@router.post("/posts/{post_id}/publish")
async def publish_post(
    post_id: str,
    post_url: Optional[str] = Query(None, description="URL do post publicado"),
    user: dict = Depends(get_current_user)
):
    """Marca um post como publicado."""
    try:
        post = await content_service.update_post(
            user_id=user["id"],
            post_id=post_id,
            status="published",
            post_url=post_url
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("publish_post_failed", user_id=user["id"], post_id=post_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao publicar post: {str(e)}")


# ==========================================
# CALENDAR & STATS
# ==========================================

@router.get("/calendar")
async def get_calendar(
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    user: dict = Depends(get_current_user)
):
    """Obtém calendário editorial."""
    try:
        calendar = await content_service.get_calendar(
            user_id=user["id"],
            start_date=start_date,
            end_date=end_date
        )
        return {"calendar": calendar}
        
    except Exception as e:
        logger.error("get_calendar_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar calendário: {str(e)}")


@router.get("/stats")
async def get_content_stats(
    user: dict = Depends(get_current_user)
):
    """Obtém estatísticas de conteúdo."""
    try:
        stats = await content_service.get_content_stats(user_id=user["id"])
        return stats
        
    except Exception as e:
        logger.error("get_stats_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")
