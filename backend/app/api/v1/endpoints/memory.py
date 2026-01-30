"""
TB Personal OS - Memory API Endpoints
Endpoints para memória, contexto e perfil
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.api.v1.dependencies.auth import get_current_user_id
from app.services.memory_service import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


# ==========================================
# SCHEMAS
# ==========================================

class MemoryCreate(BaseModel):
    """Schema para criar memória."""
    content: str = Field(..., description="Conteúdo a lembrar")
    category: str = Field(default="general", description="Categoria")
    metadata: Optional[dict] = None


class MemoryResponse(BaseModel):
    """Schema de resposta de memória."""
    id: str
    content: str
    context_type: str
    source: str
    metadata: Optional[dict]
    created_at: str


class ProfileUpdate(BaseModel):
    """Schema para atualizar perfil."""
    timezone: Optional[str] = None
    language: Optional[str] = None
    notify_morning_summary: Optional[bool] = None
    notify_night_summary: Optional[bool] = None
    notify_weekly_planning: Optional[bool] = None
    morning_summary_time: Optional[str] = None
    night_summary_time: Optional[str] = None
    autonomy_level: Optional[int] = None


class GoalCreate(BaseModel):
    """Schema para criar objetivo."""
    goal: str
    category: str = "general"


class PrincipleCreate(BaseModel):
    """Schema para criar princípio."""
    principle: str


class ContextResponse(BaseModel):
    """Schema de resposta de contexto."""
    profile: dict
    recent_conversations: List[dict]
    memories: List[dict]


class TimelineEvent(BaseModel):
    """Schema de evento na timeline."""
    type: str
    timestamp: str
    summary: Optional[str] = None
    title: Optional[str] = None
    action: Optional[str] = None


# ==========================================
# MEMORY ENDPOINTS
# ==========================================

@router.post("/remember", response_model=MemoryResponse, summary="Salvar memória")
async def remember(
    data: MemoryCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Salva uma informação na memória do assistente.
    
    O assistente usará essa informação em futuras conversas.
    """
    try:
        result = await memory_service.remember(
            user_id=user_id,
            content=data.content,
            category=data.category,
            source="user",
            metadata=data.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories", summary="Listar memórias")
async def list_memories(
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    limit: int = Query(50, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """Lista todas as memórias salvas."""
    memories = await memory_service.get_all_memories(
        user_id=user_id,
        category=category,
        limit=limit
    )
    return {
        "total": len(memories),
        "memories": memories
    }


@router.get("/search", summary="Buscar memórias")
async def search_memories(
    q: str = Query(..., description="Termo de busca"),
    category: Optional[str] = None,
    limit: int = Query(10, le=50),
    user_id: str = Depends(get_current_user_id)
):
    """
    Busca memórias por texto.
    
    Busca case-insensitive no conteúdo das memórias.
    """
    memories = await memory_service.search_memories(
        user_id=user_id,
        query=q,
        category=category,
        limit=limit
    )
    return {
        "query": q,
        "total": len(memories),
        "memories": memories
    }


@router.delete("/memories/{memory_id}", summary="Deletar memória")
async def delete_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Remove uma memória."""
    success = await memory_service.delete_memory(
        user_id=user_id,
        memory_id=memory_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Memória não encontrada")
    return {"message": "Memória removida", "id": memory_id}


# ==========================================
# PROFILE ENDPOINTS
# ==========================================

@router.get("/profile", summary="Obter perfil")
async def get_profile(
    user_id: str = Depends(get_current_user_id)
):
    """Obtém perfil completo do usuário."""
    profile = await memory_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return profile


@router.put("/profile", summary="Atualizar perfil")
async def update_profile(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Atualiza configurações do perfil.
    
    Campos atualizáveis:
    - timezone: Fuso horário (ex: America/Sao_Paulo)
    - language: Idioma (pt-BR, en-US)
    - notify_*: Configurações de notificação
    - autonomy_level: Nível de autonomia (1-5)
    """
    profile = await memory_service.update_profile(
        user_id=user_id,
        **data.model_dump(exclude_unset=True)
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return profile


# ==========================================
# GOALS ENDPOINTS
# ==========================================

@router.post("/goals", summary="Adicionar objetivo")
async def add_goal(
    data: GoalCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Adiciona um objetivo ao perfil.
    
    Categorias sugeridas:
    - general: Geral
    - health: Saúde
    - work: Trabalho
    - finance: Finanças
    - personal: Pessoal
    """
    success = await memory_service.add_goal(
        user_id=user_id,
        goal=data.goal,
        category=data.category
    )
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao adicionar objetivo")
    return {"message": "Objetivo adicionado", "goal": data.goal}


@router.get("/goals", summary="Listar objetivos")
async def list_goals(
    user_id: str = Depends(get_current_user_id)
):
    """Lista todos os objetivos do usuário."""
    profile = await memory_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    goals = profile.get("goals") or []
    return {
        "total": len(goals),
        "goals": goals
    }


# ==========================================
# PRINCIPLES ENDPOINTS
# ==========================================

@router.post("/principles", summary="Adicionar princípio")
async def add_principle(
    data: PrincipleCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Adiciona um princípio/valor ao perfil.
    
    Princípios ajudam o assistente a entender suas prioridades
    e tomar decisões mais alinhadas com você.
    """
    success = await memory_service.add_principle(
        user_id=user_id,
        principle=data.principle
    )
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao adicionar princípio")
    return {"message": "Princípio adicionado", "principle": data.principle}


@router.get("/principles", summary="Listar princípios")
async def list_principles(
    user_id: str = Depends(get_current_user_id)
):
    """Lista todos os princípios do usuário."""
    profile = await memory_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    principles = profile.get("principles") or []
    return {
        "total": len(principles),
        "principles": principles
    }


# ==========================================
# CONTEXT ENDPOINTS
# ==========================================

@router.get("/context", summary="Obter contexto completo")
async def get_context(
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém contexto completo do usuário.
    
    Inclui:
    - Perfil e preferências
    - Conversas recentes
    - Memórias salvas
    """
    context = await memory_service.get_full_context(user_id)
    return context


@router.get("/context/recent", summary="Obter conversas recentes")
async def get_recent_context(
    limit: int = Query(5, le=20),
    user_id: str = Depends(get_current_user_id)
):
    """Obtém as últimas conversas com o assistente."""
    context = await memory_service.get_recent_context(user_id, limit)
    return {
        "total": len(context),
        "conversations": context
    }


@router.get("/context/formatted", summary="Obter contexto formatado para LLM")
async def get_formatted_context(
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém contexto formatado para uso em LLM.
    
    Útil para debug ou para entender o que o assistente "sabe".
    """
    formatted = await memory_service.format_full_context_for_llm(user_id)
    return {
        "formatted_context": formatted
    }


# ==========================================
# TIMELINE ENDPOINTS
# ==========================================

@router.get("/timeline", summary="Obter timeline")
async def get_timeline(
    days: int = Query(7, le=30, description="Dias para buscar"),
    limit: int = Query(50, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém timeline de eventos e atividades.
    
    Combina:
    - Interações com assistente
    - Tarefas concluídas
    - Check-ins registrados
    """
    from datetime import timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    timeline = await memory_service.get_timeline(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "total": len(timeline),
        "events": timeline
    }


# ==========================================
# CATEGORIES ENDPOINT
# ==========================================

@router.get("/categories", summary="Listar categorias")
async def list_categories():
    """Lista categorias disponíveis para memórias."""
    return {
        "categories": [
            {"id": "general", "name": "Geral", "description": "Informações gerais"},
            {"id": "personal", "name": "Pessoal", "description": "Informações pessoais"},
            {"id": "work", "name": "Trabalho", "description": "Informações de trabalho"},
            {"id": "health", "name": "Saúde", "description": "Informações de saúde"},
            {"id": "finance", "name": "Finanças", "description": "Informações financeiras"},
            {"id": "preference", "name": "Preferência", "description": "Preferências pessoais"},
            {"id": "contact", "name": "Contato", "description": "Informações de contatos"},
            {"id": "project", "name": "Projeto", "description": "Informações de projetos"},
        ]
    }
