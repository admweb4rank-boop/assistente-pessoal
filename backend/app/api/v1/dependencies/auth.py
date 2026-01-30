"""
TB Personal OS - Authentication Dependencies
Middleware e dependências de autenticação
"""

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import structlog
from jose import jwt, JWTError
from supabase import create_client, Client

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


def get_supabase_client() -> Client:
    """Retorna cliente Supabase."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[dict]:
    """
    Obtém usuário atual (opcional - não falha se não autenticado).
    Suporta JWT do Supabase ou API Key.
    """
    
    # Tentar API Key primeiro
    if x_api_key:
        if x_api_key == settings.API_SECRET_KEY:
            # API Key válida - retorna owner
            try:
                result = supabase.table("telegram_chats")\
                    .select("user_id, users(id, email, full_name)")\
                    .eq("chat_id", int(settings.OWNER_TELEGRAM_CHAT_ID))\
                    .execute()
                
                if result.data:
                    user_data = result.data[0]
                    return {
                        "id": user_data["user_id"],
                        "email": user_data["users"]["email"],
                        "full_name": user_data["users"]["full_name"],
                        "auth_method": "api_key"
                    }
            except Exception as e:
                logger.warning("api_key_user_lookup_failed", error=str(e))
            
            return None
        else:
            return None
    
    # Tentar JWT
    if not credentials:
        return None
    
    token = credentials.credentials
    
    try:
        # Decodificar JWT do Supabase
        # Nota: Em produção, verificar assinatura com SUPABASE_JWT_SECRET
        payload = jwt.decode(
            token,
            options={"verify_signature": False}  # TODO: Verificar em produção
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id:
            return None
        
        # Buscar dados completos do usuário
        result = supabase.table("users")\
            .select("*")\
            .eq("id", user_id)\
            .execute()
        
        if result.data:
            user = result.data[0]
            return {
                "id": user["id"],
                "email": user.get("email", email),
                "full_name": user.get("full_name"),
                "auth_method": "jwt"
            }
        
        return {
            "id": user_id,
            "email": email,
            "auth_method": "jwt"
        }
        
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        return None
    except Exception as e:
        logger.error("auth_error", error=str(e))
        return None


async def get_current_user(
    user: Optional[dict] = Depends(get_current_user_optional)
) -> dict:
    """
    Obtém usuário atual (obrigatório).
    Lança exceção se não autenticado.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_id(
    user: dict = Depends(get_current_user)
) -> str:
    """Retorna apenas o ID do usuário atual."""
    return user["id"]


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> bool:
    """
    Valida API Key para endpoints internos/administrativos.
    Lança exceção se não autorizado.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required",
            headers={"X-API-Key": "Required"},
        )
    
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    
    return True


class RateLimiter:
    """
    Rate limiter simples em memória.
    Em produção, usar Redis.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}
    
    async def check(self, key: str) -> bool:
        """Verifica se a requisição está dentro do limite."""
        import time
        
        now = time.time()
        minute_ago = now - 60
        
        # Limpar requisições antigas
        if key in self.requests:
            self.requests[key] = [
                t for t in self.requests[key] if t > minute_ago
            ]
        else:
            self.requests[key] = []
        
        # Verificar limite
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        
        # Registrar requisição
        self.requests[key].append(now)
        return True


# Instância global do rate limiter
rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


async def check_rate_limit(
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """Dependency para verificar rate limit."""
    key = user["id"] if user else "anonymous"
    
    if not await rate_limiter.check(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    Obtém API Key do header.
    Retorna None se não fornecida.
    """
    if x_api_key and x_api_key == settings.API_SECRET_KEY:
        return x_api_key
    return None


async def validate_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """
    Valida API Key obrigatória.
    Lança exceção se inválida.
    """
    if not x_api_key or x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida ou não fornecida"
        )
    return x_api_key
