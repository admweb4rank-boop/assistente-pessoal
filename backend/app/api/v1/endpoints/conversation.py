"""
Conversation & Memory API Endpoints
Endpoints para gerenciamento de conversas, memórias e contexto
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from enum import Enum

from app.api.v1.dependencies.auth import get_current_user
from app.services.conversation_service import conversation_service
from app.services.context_service import context_service, MemoryCategory, PatternType

router = APIRouter(prefix="/conversation", tags=["conversation"])


# =============================================
# SCHEMAS
# =============================================

class MessageRequest(BaseModel):
    message: str
    source: str = "api"


class MessageResponse(BaseModel):
    response: str
    intent: str
    actions: list
    memories_created: list
    session_id: Optional[str]


class MemoryCreate(BaseModel):
    category: str  # preference, fact, pattern, relationship, goal, context, feedback
    content: str
    importance: int = 5


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    importance: Optional[int] = None
    is_active: Optional[bool] = None


class PatternCreate(BaseModel):
    pattern_type: str
    name: str
    description: Optional[str] = None
    pattern_data: dict


class FeedbackRequest(BaseModel):
    message_id: str
    feedback_type: str  # positive, negative, correction, preference
    feedback_content: Optional[str] = None
    corrected_response: Optional[str] = None


class KnowledgeCreate(BaseModel):
    title: str
    source_type: str  # document, note, webpage, manual
    content: str
    tags: List[str] = []
    category: Optional[str] = None
    source_url: Optional[str] = None


# =============================================
# CONVERSATION ENDPOINTS
# =============================================

@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Envia uma mensagem e recebe resposta do assistente."""
    try:
        result = await conversation_service.process_message(
            user_id=current_user["id"],
            message=request.message,
            source=request.source
        )
        return MessageResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    session_id: Optional[str] = None,
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Busca histórico de conversas."""
    try:
        history = await conversation_service.get_conversation_history(
            user_id=current_user["id"],
            session_id=session_id,
            limit=limit
        )
        return {"success": True, "messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(
    active_only: bool = False,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Lista sessões de conversa."""
    try:
        query = context_service.supabase.table("conversation_sessions")\
            .select("id, started_at, ended_at, topic, summary, message_count, is_active")\
            .eq("user_id", current_user["id"])
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.order("started_at", desc=True).limit(limit).execute()
        
        return {"success": True, "sessions": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Envia feedback sobre uma resposta do assistente."""
    try:
        success = await conversation_service.submit_feedback(
            user_id=current_user["id"],
            message_id=request.message_id,
            feedback_type=request.feedback_type,
            feedback_content=request.feedback_content,
            corrected_response=request.corrected_response
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# MEMORY ENDPOINTS
# =============================================

@router.post("/memories")
async def create_memory(
    request: MemoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Cria uma nova memória manualmente."""
    try:
        category = MemoryCategory(request.category)
        memory = await context_service.add_memory(
            user_id=current_user["id"],
            category=category,
            content=request.content,
            importance=request.importance
        )
        
        if memory:
            return {"success": True, "memory": memory}
        raise HTTPException(status_code=500, detail="Falha ao criar memória")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Categoria inválida: {request.category}")


@router.get("/memories")
async def list_memories(
    category: Optional[str] = None,
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Lista memórias do usuário."""
    try:
        query = context_service.supabase.table("user_memories")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .eq("is_active", True)
        
        if category:
            query = query.eq("category", category)
        
        result = query.order("importance", desc=True).limit(limit).execute()
        
        return {"success": True, "memories": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Busca uma memória específica."""
    try:
        result = context_service.supabase.table("user_memories")\
            .select("*")\
            .eq("id", memory_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Memória não encontrada")
        
        return {"success": True, "memory": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/memories/{memory_id}")
async def update_memory(
    memory_id: str,
    request: MemoryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza uma memória."""
    try:
        success = await context_service.update_memory(
            memory_id=memory_id,
            content=request.content,
            importance=request.importance,
            is_active=request.is_active
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Desativa uma memória (soft delete)."""
    try:
        success = await context_service.update_memory(
            memory_id=memory_id,
            is_active=False
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# PATTERNS ENDPOINTS
# =============================================

@router.post("/patterns")
async def create_pattern(
    request: PatternCreate,
    current_user: dict = Depends(get_current_user)
):
    """Cria ou atualiza um padrão aprendido."""
    try:
        pattern_type = PatternType(request.pattern_type)
        pattern = await context_service.add_or_update_pattern(
            user_id=current_user["id"],
            pattern_type=pattern_type,
            name=request.name,
            pattern_data=request.pattern_data,
            description=request.description
        )
        
        if pattern:
            return {"success": True, "pattern": pattern}
        raise HTTPException(status_code=500, detail="Falha ao criar padrão")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo de padrão inválido: {request.pattern_type}")


@router.get("/patterns")
async def list_patterns(
    pattern_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Lista padrões aprendidos."""
    try:
        query = context_service.supabase.table("learned_patterns")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .eq("is_active", True)
        
        if pattern_type:
            query = query.eq("pattern_type", pattern_type)
        
        result = query.order("confidence", desc=True).execute()
        
        return {"success": True, "patterns": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/patterns/{pattern_id}")
async def delete_pattern(
    pattern_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Desativa um padrão (soft delete)."""
    try:
        context_service.supabase.table("learned_patterns")\
            .update({"is_active": False})\
            .eq("id", pattern_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# KNOWLEDGE BASE ENDPOINTS
# =============================================

@router.post("/knowledge")
async def add_knowledge(
    request: KnowledgeCreate,
    current_user: dict = Depends(get_current_user)
):
    """Adiciona item à base de conhecimento."""
    try:
        import hashlib
        content_hash = hashlib.sha256(request.content.encode()).hexdigest()
        
        # Verificar duplicata
        existing = context_service.supabase.table("knowledge_base")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .eq("content_hash", content_hash)\
            .execute()
        
        if existing.data:
            return {"success": False, "error": "Conteúdo já existe", "existing_id": existing.data[0]["id"]}
        
        result = context_service.supabase.table("knowledge_base")\
            .insert({
                "user_id": current_user["id"],
                "title": request.title,
                "source_type": request.source_type,
                "content": request.content,
                "content_hash": content_hash,
                "tags": request.tags,
                "category": request.category,
                "source_url": request.source_url,
                "is_active": True
            })\
            .execute()
        
        if result.data:
            return {"success": True, "knowledge": result.data[0]}
        raise HTTPException(status_code=500, detail="Falha ao adicionar conhecimento")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge")
async def list_knowledge(
    source_type: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Lista itens da base de conhecimento."""
    try:
        query = context_service.supabase.table("knowledge_base")\
            .select("id, title, source_type, category, tags, created_at")\
            .eq("user_id", current_user["id"])\
            .eq("is_active", True)
        
        if source_type:
            query = query.eq("source_type", source_type)
        if category:
            query = query.eq("category", category)
        if tag:
            query = query.contains("tags", [tag])
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {"success": True, "items": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{item_id}")
async def get_knowledge_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Busca um item da base de conhecimento."""
    try:
        result = context_service.supabase.table("knowledge_base")\
            .select("*")\
            .eq("id", item_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        
        return {"success": True, "item": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/{item_id}")
async def delete_knowledge_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove item da base de conhecimento (soft delete)."""
    try:
        context_service.supabase.table("knowledge_base")\
            .update({"is_active": False})\
            .eq("id", item_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# CONTEXT ENDPOINT
# =============================================

@router.get("/context")
async def get_current_context(
    current_user: dict = Depends(get_current_user)
):
    """Retorna o contexto atual do usuário para debug/visualização."""
    try:
        context = await context_service.get_context_for_message(
            user_id=current_user["id"],
            message="contexto geral"
        )
        
        formatted = context_service.format_context_for_prompt(context)
        
        return {
            "success": True,
            "raw": context,
            "formatted": formatted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
