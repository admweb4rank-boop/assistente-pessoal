"""
Modes API Endpoints - Sistema de Modos/Identidades
Gerencia ativação e configuração de modos operacionais
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import structlog

from app.api.v1.dependencies.auth import get_api_key
from app.services.mode_service import mode_service, ModeType

router = APIRouter(prefix="/modes", tags=["Modes"])
logger = structlog.get_logger()

# Hardcoded user_id para single-user
DEFAULT_USER_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


# ==========================================
# MODELS
# ==========================================

class ModeActivate(BaseModel):
    mode_name: str = Field(..., description="Nome do modo a ativar")
    trigger_source: str = Field(default="api", description="Origem da ativação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode_name": "execution",
                "trigger_source": "api"
            }
        }


class CustomModeCreate(BaseModel):
    mode_name: str = Field(..., description="Identificador único do modo")
    display_name: str = Field(..., description="Nome de exibição")
    description: str
    system_prompt: str = Field(..., description="Prompt do sistema para este modo")
    icon: str = Field(default="🎯")
    priority_tools: Optional[List[str]] = None


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("")
async def list_modes(api_key: str = Depends(get_api_key)):
    """Lista todos os modos disponíveis"""
    modes = mode_service.get_available_modes()
    return {
        "modes": modes,
        "total": len(modes)
    }


@router.get("/active")
async def get_active_mode(api_key: str = Depends(get_api_key)):
    """Obtém o modo atualmente ativo"""
    active = mode_service.get_active_mode(DEFAULT_USER_ID)
    return {
        "active_mode": active,
        "mode_name": active.get("mode_name", "default"),
        "display_name": active.get("display_name", "Assistente Geral"),
        "icon": active.get("icon", "🤖")
    }


@router.post("/activate")
async def activate_mode(
    data: ModeActivate,
    api_key: str = Depends(get_api_key)
):
    """Ativa um modo específico"""
    result = mode_service.activate_mode(
        user_id=DEFAULT_USER_ID,
        mode_name=data.mode_name,
        trigger_source=data.trigger_source
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Erro ao ativar modo"))
    
    return {
        "success": True,
        "mode": result.get("mode"),
        "greeting": result.get("greeting"),
        "message": f"Modo '{data.mode_name}' ativado com sucesso!"
    }


@router.post("/deactivate")
async def deactivate_mode(api_key: str = Depends(get_api_key)):
    """Desativa o modo atual (volta ao default)"""
    result = mode_service.deactivate_mode(DEFAULT_USER_ID)
    return {
        "success": True,
        "message": "Modo resetado para padrão"
    }


@router.get("/types")
async def get_mode_types(api_key: str = Depends(get_api_key)):
    """Lista os tipos de modo disponíveis"""
    return {
        "types": [m.value for m in ModeType],
        "descriptions": {
            "default": "Assistente geral equilibrado",
            "execution": "Foco em produtividade e negócios",
            "content": "Foco em conteúdo e marca pessoal",
            "health": "Foco em saúde e energia",
            "learning": "Foco em aprendizado e evolução",
            "presence": "Foco em presença e atratividade"
        }
    }


@router.get("/{mode_name}")
async def get_mode_details(
    mode_name: str,
    api_key: str = Depends(get_api_key)
):
    """Obtém detalhes de um modo específico"""
    modes = mode_service.get_available_modes()
    mode = next((m for m in modes if m["mode_name"] == mode_name), None)
    
    if not mode:
        raise HTTPException(status_code=404, detail=f"Modo '{mode_name}' não encontrado")
    
    # Adiciona prompt
    mode["system_prompt"] = mode_service.get_mode_prompt(mode_name)
    mode["greeting"] = mode_service.get_mode_greeting(mode_name)
    
    return mode


@router.get("/stats/usage")
async def get_mode_stats(
    days: int = 30,
    api_key: str = Depends(get_api_key)
):
    """Estatísticas de uso de modos"""
    stats = mode_service.get_mode_stats(DEFAULT_USER_ID, days)
    return stats


@router.post("/custom")
async def create_custom_mode(
    data: CustomModeCreate,
    api_key: str = Depends(get_api_key)
):
    """Cria um modo personalizado"""
    result = mode_service.create_custom_mode(
        user_id=DEFAULT_USER_ID,
        mode_name=data.mode_name,
        display_name=data.display_name,
        description=data.description,
        system_prompt=data.system_prompt,
        icon=data.icon,
        priority_tools=data.priority_tools
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Erro ao criar modo"))
    
    return {
        "success": True,
        "mode_name": result.get("mode_name"),
        "message": "Modo personalizado criado com sucesso!"
    }


# ==========================================
# ATALHOS PARA MODOS ESPECÍFICOS
# ==========================================

@router.post("/execution")
async def activate_execution_mode(api_key: str = Depends(get_api_key)):
    """Atalho: Ativa modo Execução"""
    result = mode_service.activate_mode(DEFAULT_USER_ID, "execution", "shortcut")
    return {"success": True, "greeting": result.get("greeting")}


@router.post("/content")
async def activate_content_mode(api_key: str = Depends(get_api_key)):
    """Atalho: Ativa modo Conteúdo"""
    result = mode_service.activate_mode(DEFAULT_USER_ID, "content", "shortcut")
    return {"success": True, "greeting": result.get("greeting")}


@router.post("/health")
async def activate_health_mode(api_key: str = Depends(get_api_key)):
    """Atalho: Ativa modo Saúde"""
    result = mode_service.activate_mode(DEFAULT_USER_ID, "health", "shortcut")
    return {"success": True, "greeting": result.get("greeting")}


@router.post("/learning")
async def activate_learning_mode(api_key: str = Depends(get_api_key)):
    """Atalho: Ativa modo Aprendizado"""
    result = mode_service.activate_mode(DEFAULT_USER_ID, "learning", "shortcut")
    return {"success": True, "greeting": result.get("greeting")}


@router.post("/presence")
async def activate_presence_mode(api_key: str = Depends(get_api_key)):
    """Atalho: Ativa modo Presença"""
    result = mode_service.activate_mode(DEFAULT_USER_ID, "presence", "shortcut")
    return {"success": True, "greeting": result.get("greeting")}
