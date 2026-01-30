"""
TB Personal OS - Google Auth Service
Gerencia OAuth2 para Google APIs
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from supabase import Client, create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class GoogleAuthService:
    """
    Serviço de autenticação Google OAuth2.
    Gerencia tokens e refresh automático.
    """
    
    SCOPES = [
        # Calendar
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        # Gmail
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.send',
        # Drive
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
    ]
    
    def __init__(self, supabase: Optional[Client] = None):
        self._supabase = supabase
        self._credentials_cache: Dict[str, Credentials] = {}
    
    @property
    def supabase(self) -> Client:
        """Lazy load Supabase client."""
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    def get_authorization_url(self, user_id: str, redirect_uri: Optional[str] = None) -> str:
        """
        Gera URL de autorização OAuth2.
        
        Returns:
            URL para redirecionar o usuário
        """
        try:
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri or settings.GOOGLE_REDIRECT_URI]
                    }
                },
                scopes=self.SCOPES
            )
            
            flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=user_id  # Passar user_id no state
            )
            
            logger.info("auth_url_generated", user_id=user_id)
            return authorization_url
            
        except Exception as e:
            logger.error("auth_url_generation_failed", error=str(e))
            raise
    
    async def handle_callback(
        self,
        authorization_code: str,
        state: str,  # user_id
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa callback OAuth2 e salva tokens.
        
        Args:
            authorization_code: Código de autorização
            state: user_id passado no state
        
        Returns:
            Informações do token
        """
        try:
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri or settings.GOOGLE_REDIRECT_URI]
                    }
                },
                scopes=self.SCOPES
            )
            
            flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            user_id = state
            
            # Salvar tokens no banco
            await self._save_tokens(user_id, credentials)
            
            # Cachear credentials
            self._credentials_cache[user_id] = credentials
            
            logger.info("oauth_callback_success", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": list(credentials.scopes) if credentials.scopes else []
            }
            
        except Exception as e:
            logger.error("oauth_callback_failed", error=str(e))
            raise
    
    async def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Obtém credentials válidas para um usuário.
        Faz refresh automático se expirado.
        
        Returns:
            Credentials válidas ou None
        """
        # Verificar cache
        if user_id in self._credentials_cache:
            creds = self._credentials_cache[user_id]
            if creds.valid:
                return creds
        
        # Buscar do banco
        try:
            result = self.supabase.table("oauth_tokens")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("provider", "google")\
                .single()\
                .execute()
            
            if not result.data:
                return None
            
            token_data = result.data
            
            creds = Credentials(
                token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=token_data.get("scopes", [])
            )
            
            # Verificar se precisa refresh
            if not creds.valid:
                if creds.refresh_token:
                    creds.refresh(Request())
                    await self._save_tokens(user_id, creds)
                else:
                    logger.warning("no_refresh_token", user_id=user_id)
                    return None
            
            # Cachear
            self._credentials_cache[user_id] = creds
            return creds
            
        except Exception as e:
            logger.error("get_credentials_failed", user_id=user_id, error=str(e))
            return None
    
    async def is_connected(self, user_id: str) -> bool:
        """Verifica se o usuário tem conexão Google válida."""
        creds = await self.get_credentials(user_id)
        return creds is not None and creds.valid
    
    async def disconnect(self, user_id: str) -> bool:
        """Remove conexão Google do usuário."""
        try:
            self.supabase.table("oauth_tokens")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("provider", "google")\
                .execute()
            
            # Limpar cache
            self._credentials_cache.pop(user_id, None)
            
            logger.info("google_disconnected", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("disconnect_failed", error=str(e))
            return False
    
    async def _save_tokens(self, user_id: str, credentials: Credentials):
        """Salva ou atualiza tokens no banco."""
        try:
            token_data = {
                "user_id": user_id,
                "provider": "google",
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": list(credentials.scopes) if credentials.scopes else [],
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert
            self.supabase.table("oauth_tokens").upsert(
                token_data,
                on_conflict="user_id,provider"
            ).execute()
            
            logger.info("tokens_saved", user_id=user_id)
            
        except Exception as e:
            logger.error("save_tokens_failed", error=str(e))
            raise


# Instância global
google_auth_service = GoogleAuthService()
