"""
TB Personal OS - Autonomy API Endpoints
Endpoints para configuração de níveis de autonomia
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field

from app.api.v1.dependencies.auth import get_current_user_id
from app.services.autonomy_service import autonomy_service

router = APIRouter(prefix="/autonomy", tags=["autonomy"])


# ==========================================
# SCHEMAS
# ==========================================

class AutonomyLevelUpdate(BaseModel):
    """Schema para atualizar nível de autonomia."""
    level: int = Field(..., ge=1, le=5, description="Nível de autonomia (1-5)")


class ActionCheckRequest(BaseModel):
    """Schema para verificar permissão de ação."""
    action: str = Field(..., description="Nome da ação a verificar")


# ==========================================
# LEVEL ENDPOINTS
# ==========================================

@router.get("/level", summary="Obter nível atual")
async def get_current_level(
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém o nível de autonomia atual do usuário.
    
    Níveis:
    - 1: Observador - Apenas observa e reporta
    - 2: Sugestor - Sugere ações
    - 3: Confirmador - Executa após confirmação
    - 4: Executor - Executa automaticamente
    - 5: Proativo - Antecipa e age
    """
    try:
        level = await autonomy_service.get_user_autonomy_level(user_id)
        description = autonomy_service.get_level_description(level)
        return description
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/level", summary="Definir nível de autonomia")
async def set_autonomy_level(
    data: AutonomyLevelUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Define o nível de autonomia do assistente.
    
    Níveis disponíveis:
    - 1: **Observador** - Só responde quando perguntado
    - 2: **Sugestor** - Sugere mas não executa
    - 3: **Confirmador** - Executa após confirmação (recomendado)
    - 4: **Executor** - Executa ações comuns automaticamente
    - 5: **Proativo** - Antecipa necessidades e age
    """
    try:
        success = await autonomy_service.set_user_autonomy_level(user_id, data.level)
        if success:
            description = autonomy_service.get_level_description(data.level)
            return {
                "message": "Nível de autonomia atualizado",
                **description
            }
        raise HTTPException(status_code=500, detail="Falha ao atualizar")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/levels", summary="Listar todos os níveis")
async def list_all_levels():
    """
    Lista todos os níveis de autonomia disponíveis.
    
    Útil para criar interfaces de seleção.
    """
    levels = autonomy_service.get_all_levels()
    return {
        "total": len(levels),
        "recommended": 3,
        "levels": levels
    }


@router.get("/levels/{level_id}", summary="Detalhes de um nível")
async def get_level_details(
    level_id: int
):
    """Obtém detalhes de um nível específico."""
    if level_id < 1 or level_id > 5:
        raise HTTPException(status_code=400, detail="Nível deve ser entre 1 e 5")
    
    return autonomy_service.get_level_description(level_id)


# ==========================================
# ACTIONS ENDPOINTS
# ==========================================

@router.get("/actions", summary="Listar ações permitidas")
async def list_allowed_actions(
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todas as ações e suas permissões.
    
    Retorna ações categorizadas em:
    - automatic: Executadas sem perguntar
    - with_confirmation: Precisam de confirmação
    - not_allowed: Não permitidas no nível atual
    """
    try:
        actions = await autonomy_service.get_allowed_actions(user_id)
        return actions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/check", summary="Verificar permissão")
async def check_action_permission(
    data: ActionCheckRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Verifica se uma ação específica é permitida.
    
    Ações disponíveis:
    - read_*: Leitura de dados
    - suggest_*: Sugestões
    - create_*: Criação de itens
    - update_*: Atualização de itens
    - auto_*: Ações proativas
    """
    try:
        result = await autonomy_service.can_perform_action(user_id, data.action)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/available", summary="Listar ações disponíveis")
async def list_available_actions():
    """Lista todas as ações conhecidas pelo sistema."""
    from app.services.autonomy_service import ACTION_LEVELS, AutonomyLevel
    
    actions = []
    for action, level in sorted(ACTION_LEVELS.items()):
        actions.append({
            "action": action,
            "required_level": level,
            "required_level_name": AutonomyLevel(level).name,
            "category": action.split("_")[0]  # read, create, update, etc
        })
    
    return {
        "total": len(actions),
        "actions": actions
    }


# ==========================================
# HISTORY ENDPOINTS
# ==========================================

@router.get("/history", summary="Histórico de ações")
async def get_action_history(
    limit: int = Query(50, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtém histórico de ações automáticas executadas.
    
    Útil para auditoria e entender o que o assistente fez.
    """
    try:
        history = await autonomy_service.get_action_history(user_id, limit)
        return {
            "total": len(history),
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# QUICK ACTIONS
# ==========================================

@router.post("/level/increase", summary="Aumentar autonomia")
async def increase_autonomy(
    user_id: str = Depends(get_current_user_id)
):
    """Aumenta o nível de autonomia em 1."""
    try:
        current = await autonomy_service.get_user_autonomy_level(user_id)
        if current >= 5:
            raise HTTPException(status_code=400, detail="Já está no nível máximo")
        
        await autonomy_service.set_user_autonomy_level(user_id, current + 1)
        return autonomy_service.get_level_description(current + 1)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/level/decrease", summary="Diminuir autonomia")
async def decrease_autonomy(
    user_id: str = Depends(get_current_user_id)
):
    """Diminui o nível de autonomia em 1."""
    try:
        current = await autonomy_service.get_user_autonomy_level(user_id)
        if current <= 1:
            raise HTTPException(status_code=400, detail="Já está no nível mínimo")
        
        await autonomy_service.set_user_autonomy_level(user_id, current - 1)
        return autonomy_service.get_level_description(current - 1)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
