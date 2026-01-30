"""
Learning API Endpoints - Learning OS
Gerencia aprendizado, revisão espaçada, trilhas
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import structlog

from app.api.v1.dependencies.auth import get_api_key
from app.services.learning_service import learning_service, ContentType, LearningStatus

router = APIRouter(prefix="/learning", tags=["Learning OS"])
logger = structlog.get_logger()

# Hardcoded user_id para single-user
DEFAULT_USER_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


# ==========================================
# MODELS
# ==========================================

class LearningItemCreate(BaseModel):
    title: str = Field(..., description="Título do item")
    content_type: str = Field(..., description="book, article, course, video, etc")
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    summary: Optional[str] = None
    key_insights: Optional[List[str]] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: int = Field(default=5, ge=1, le=10)
    learning_path_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Clean Code - Robert C. Martin",
                "content_type": "book",
                "topic": "Programação",
                "tags": ["coding", "best-practices"],
                "priority": 8
            }
        }


class LearningItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    key_insights: Optional[List[str]] = None
    personal_notes: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    completion_percentage: Optional[int] = None


class ReviewSubmit(BaseModel):
    quality: int = Field(..., ge=0, le=5, description="0=esqueceu, 5=fácil")
    time_spent_seconds: Optional[int] = None


class PathCreate(BaseModel):
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None
    target_completion: Optional[datetime] = None


class FlashcardCreate(BaseModel):
    question: str
    answer: str
    topic: Optional[str] = None
    tags: Optional[List[str]] = None


class QuickCapture(BaseModel):
    content: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None


# ==========================================
# LEARNING ITEMS ENDPOINTS
# ==========================================

@router.post("/items")
async def create_learning_item(
    item: LearningItemCreate,
    api_key: str = Depends(get_api_key)
):
    """Cria um novo item de aprendizado"""
    try:
        result = learning_service.create_item(
            user_id=DEFAULT_USER_ID,
            **item.model_dump()
        )
        if result:
            return {"success": True, "item": result}
        raise HTTPException(status_code=500, detail="Falha ao criar item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items")
async def list_learning_items(
    status: Optional[str] = None,
    content_type: Optional[str] = None,
    topic: Optional[str] = None,
    path_id: Optional[str] = None,
    limit: int = 50,
    api_key: str = Depends(get_api_key)
):
    """Lista itens de aprendizado"""
    items = learning_service.get_items(
        user_id=DEFAULT_USER_ID,
        status=status,
        content_type=content_type,
        topic=topic,
        path_id=path_id,
        limit=limit
    )
    return {"items": items, "total": len(items)}


@router.get("/content-types")
async def get_content_types(api_key: str = Depends(get_api_key)):
    """Lista tipos de conteúdo disponíveis"""
    return {
        "types": [t.value for t in ContentType],
        "descriptions": {
            "book": "Livro completo",
            "article": "Artigo ou post",
            "course": "Curso online",
            "video": "Vídeo/YouTube",
            "podcast": "Podcast/áudio",
            "summary": "Resumo de conteúdo",
            "note": "Nota/anotação",
            "highlight": "Destaque importante",
            "flashcard": "Flashcard para revisão"
        }
    }


@router.get("/statuses")
async def get_learning_statuses(api_key: str = Depends(get_api_key)):
    """Lista status de aprendizado"""
    return {
        "statuses": [s.value for s in LearningStatus],
        "flow": ["to_learn", "learning", "completed", "reviewing", "mastered"],
        "descriptions": {
            "to_learn": "Ainda não iniciado",
            "learning": "Em andamento",
            "completed": "Primeira passagem completa",
            "reviewing": "Em revisão espaçada",
            "mastered": "Dominado"
        }
    }


@router.get("/items/{item_id}")
async def get_learning_item(item_id: str, api_key: str = Depends(get_api_key)):
    """Obtém detalhes de um item"""
    item = learning_service.get_item(DEFAULT_USER_ID, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@router.patch("/items/{item_id}")
async def update_learning_item(
    item_id: str,
    updates: LearningItemUpdate,
    api_key: str = Depends(get_api_key)
):
    """Atualiza um item"""
    update_data = updates.model_dump(exclude_unset=True)
    result = learning_service.update_item(DEFAULT_USER_ID, item_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return {"success": True, "item": result}


@router.delete("/items/{item_id}")
async def delete_learning_item(item_id: str, api_key: str = Depends(get_api_key)):
    """Remove um item"""
    success = learning_service.delete_item(DEFAULT_USER_ID, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return {"success": True, "message": "Item removido"}


# ==========================================
# REVISÃO ESPAÇADA (Spaced Repetition)
# ==========================================

@router.get("/review")
async def get_items_for_review(
    limit: int = 20,
    api_key: str = Depends(get_api_key)
):
    """Obtém itens que precisam de revisão hoje"""
    items = learning_service.get_items_for_review(DEFAULT_USER_ID, limit)
    return {
        "items": items,
        "total": len(items),
        "message": f"Você tem {len(items)} itens para revisar"
    }


@router.post("/review/{item_id}")
async def submit_review(
    item_id: str,
    review: ReviewSubmit,
    api_key: str = Depends(get_api_key)
):
    """
    Registra resultado de uma revisão
    
    Quality scale (SM-2):
    - 0: Completo esquecimento
    - 1: Incorreto, lembrou ao ver resposta
    - 2: Incorreto, parecia fácil ao ver
    - 3: Correto com dificuldade
    - 4: Correto após hesitação
    - 5: Correto imediatamente
    """
    result = learning_service.record_review(
        user_id=DEFAULT_USER_ID,
        item_id=item_id,
        quality=review.quality,
        time_spent_seconds=review.time_spent_seconds
    )
    if not result:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    return {
        "success": True,
        "item": result,
        "next_review": result.get("next_review"),
        "new_interval_days": result.get("interval_days"),
        "message": "Revisão registrada com sucesso!"
    }


@router.get("/review/stats")
async def get_review_stats(days: int = 30, api_key: str = Depends(get_api_key)):
    """Estatísticas de revisão"""
    stats = learning_service.get_review_stats(DEFAULT_USER_ID, days)
    return stats


# ==========================================
# TRILHAS DE APRENDIZADO
# ==========================================

@router.post("/paths")
async def create_learning_path(
    path: PathCreate,
    api_key: str = Depends(get_api_key)
):
    """Cria uma nova trilha de aprendizado"""
    try:
        result = learning_service.create_path(
            user_id=DEFAULT_USER_ID,
            **path.model_dump()
        )
        if result:
            return {"success": True, "path": result}
        raise HTTPException(status_code=500, detail="Falha ao criar trilha")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paths")
async def list_learning_paths(
    status: Optional[str] = None,
    limit: int = 20,
    api_key: str = Depends(get_api_key)
):
    """Lista trilhas de aprendizado"""
    paths = learning_service.get_paths(DEFAULT_USER_ID, status, limit)
    return {"paths": paths, "total": len(paths)}


@router.get("/paths/{path_id}")
async def get_learning_path(path_id: str, api_key: str = Depends(get_api_key)):
    """Obtém trilha com seus itens"""
    path = learning_service.get_path(DEFAULT_USER_ID, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")
    return path


@router.post("/paths/{path_id}/start")
async def start_learning_path(path_id: str, api_key: str = Depends(get_api_key)):
    """Inicia uma trilha"""
    result = learning_service.start_path(DEFAULT_USER_ID, path_id)
    if not result:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")
    return {"success": True, "path": result}


@router.post("/paths/{path_id}/complete")
async def complete_learning_path(path_id: str, api_key: str = Depends(get_api_key)):
    """Marca trilha como completa"""
    result = learning_service.complete_path(DEFAULT_USER_ID, path_id)
    if not result:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")
    return {"success": True, "path": result}


# ==========================================
# QUICK CAPTURE & FLASHCARDS
# ==========================================

@router.post("/capture")
async def quick_capture(
    capture: QuickCapture,
    api_key: str = Depends(get_api_key)
):
    """Captura rápida de insight/nota"""
    result = learning_service.quick_capture(
        user_id=DEFAULT_USER_ID,
        content=capture.content,
        source_url=capture.source_url,
        source_title=capture.source_title
    )
    if result:
        return {"success": True, "item": result}
    raise HTTPException(status_code=500, detail="Falha ao capturar")


@router.post("/flashcard")
async def create_flashcard(
    flashcard: FlashcardCreate,
    api_key: str = Depends(get_api_key)
):
    """Cria um novo flashcard"""
    result = learning_service.create_flashcard(
        user_id=DEFAULT_USER_ID,
        **flashcard.model_dump()
    )
    if result:
        return {"success": True, "flashcard": result}
    raise HTTPException(status_code=500, detail="Falha ao criar flashcard")


@router.get("/flashcards")
async def list_flashcards(
    topic: Optional[str] = None,
    limit: int = 50,
    api_key: str = Depends(get_api_key)
):
    """Lista todos os flashcards"""
    items = learning_service.get_items(
        user_id=DEFAULT_USER_ID,
        content_type="flashcard",
        topic=topic,
        limit=limit
    )
    return {"flashcards": items, "total": len(items)}


# ==========================================
# INSIGHTS & RECOMENDAÇÕES
# ==========================================

@router.get("/topics/{topic}/insights")
async def get_topic_insights(topic: str, api_key: str = Depends(get_api_key)):
    """Obtém insights de um tópico específico"""
    insights = learning_service.get_topic_insights(DEFAULT_USER_ID, topic)
    return insights


@router.get("/daily")
async def get_daily_recommendations(
    max_items: int = 5,
    api_key: str = Depends(get_api_key)
):
    """Recomendações diárias de estudo"""
    recommendations = learning_service.get_daily_recommendations(
        DEFAULT_USER_ID, 
        max_items
    )
    return recommendations


@router.get("/topics")
async def list_topics(api_key: str = Depends(get_api_key)):
    """Lista todos os tópicos com estatísticas"""
    items = learning_service.get_items(DEFAULT_USER_ID, limit=1000)
    
    topics = {}
    for item in items:
        topic = item.get("topic") or "Sem tópico"
        if topic not in topics:
            topics[topic] = {"total": 0, "mastered": 0, "reviewing": 0}
        topics[topic]["total"] += 1
        if item["status"] == "mastered":
            topics[topic]["mastered"] += 1
        elif item["status"] == "reviewing":
            topics[topic]["reviewing"] += 1
    
    return {
        "topics": [
            {
                "name": name,
                "total_items": data["total"],
                "mastered": data["mastered"],
                "reviewing": data["reviewing"],
                "mastery_rate": round(data["mastered"] / data["total"] * 100, 1) if data["total"] > 0 else 0
            }
            for name, data in sorted(topics.items(), key=lambda x: x[1]["total"], reverse=True)
        ]
    }
