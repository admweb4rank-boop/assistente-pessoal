"""
TB Personal OS - Google Auth Endpoints
OAuth2 flow para Google APIs
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import structlog

from app.services.google_auth_service import google_auth_service
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth/google", tags=["Google Auth"])


# ==========================================
# SCHEMAS
# ==========================================

class AuthStatusResponse(BaseModel):
    """Status da conexão Google."""
    connected: bool
    user_id: str
    scopes: Optional[list] = None


class AuthUrlResponse(BaseModel):
    """URL de autorização."""
    authorization_url: str
    message: str


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/login", response_model=AuthUrlResponse)
async def google_login(
    user_id: str = Query(
        default=None,
        description="ID do usuário"
    ),
    redirect_uri: Optional[str] = Query(
        default=None,
        description="URI de redirect (opcional)"
    )
):
    """
    Inicia o fluxo OAuth2 do Google.
    
    Retorna a URL para redirecionar o usuário.
    Após autorização, o usuário será redirecionado para o callback.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        auth_url = google_auth_service.get_authorization_url(
            user_id=target_user_id,
            redirect_uri=redirect_uri
        )
        
        return AuthUrlResponse(
            authorization_url=auth_url,
            message="Acesse a URL para autorizar o acesso ao Google"
        )
        
    except Exception as e:
        logger.error("google_login_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login/redirect")
async def google_login_redirect(
    user_id: str = Query(
        default=None,
        description="ID do usuário"
    )
):
    """
    Redireciona diretamente para o Google OAuth.
    Use este endpoint para login direto (sem retornar URL).
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        auth_url = google_auth_service.get_authorization_url(target_user_id)
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error("google_redirect_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def google_callback(
    code: str = Query(..., description="Código de autorização"),
    state: str = Query(..., description="State (user_id)"),
    error: Optional[str] = Query(None)
):
    """
    Callback do OAuth2.
    
    O Google redireciona para cá após o usuário autorizar.
    Processa o código e salva os tokens.
    """
    if error:
        logger.error("google_oauth_error", error=error)
        raise HTTPException(
            status_code=400,
            detail=f"Erro na autorização: {error}"
        )
    
    try:
        result = await google_auth_service.handle_callback(
            authorization_code=code,
            state=state
        )
        
        # Retornar página de sucesso ou redirecionar
        return {
            "success": True,
            "message": "Google conectado com sucesso!",
            "user_id": result.get("user_id"),
            "scopes": result.get("scopes")
        }
        
    except Exception as e:
        logger.error("google_callback_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AuthStatusResponse)
async def google_status(
    user_id: str = Query(
        default=None,
        description="ID do usuário"
    )
):
    """
    Verifica status da conexão Google.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        connected = await google_auth_service.is_connected(target_user_id)
        
        scopes = None
        if connected:
            creds = await google_auth_service.get_credentials(target_user_id)
            if creds:
                scopes = list(creds.scopes) if creds.scopes else None
        
        return AuthStatusResponse(
            connected=connected,
            user_id=target_user_id,
            scopes=scopes
        )
        
    except Exception as e:
        logger.error("google_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/disconnect")
async def google_disconnect(
    user_id: str = Query(
        default=None,
        description="ID do usuário"
    )
):
    """
    Desconecta a conta Google.
    Remove todos os tokens salvos.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        success = await google_auth_service.disconnect(target_user_id)
        
        if success:
            return {
                "success": True,
                "message": "Google desconectado"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Falha ao desconectar"
            )
            
    except Exception as e:
        logger.error("google_disconnect_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
