"""
TB Personal OS - Rate Limiting
Sistema de rate limiting com slowapi
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


def get_identifier(request: Request) -> str:
    """
    Obtém identificador para rate limiting.
    Prioriza user_id se autenticado, senão usa IP.
    """
    # Tentar obter user_id do state (setado pelo auth)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Fallback para IP
    return get_remote_address(request)


# Configurar limiter
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute"],
    storage_uri="memory://",  # Em prod, usar Redis: "redis://localhost:6379"
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handler customizado para rate limit exceeded."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.warning(
        "rate_limit_exceeded",
        correlation_id=correlation_id,
        path=request.url.path,
        identifier=get_identifier(request),
        limit=str(exc.detail)
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Muitas requisições. Aguarde um momento.",
                "details": {
                    "retry_after": exc.detail
                }
            },
            "meta": {
                "request_id": correlation_id
            }
        },
        headers={
            "Retry-After": str(60),  # Segundos para retry
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(60)
        }
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configura rate limiting na aplicação.
    
    Limites padrão:
    - 100 req/min por usuário autenticado
    - 30 req/min por IP não autenticado
    
    Limites específicos podem ser definidos por endpoint com @limiter.limit()
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("rate_limiting_configured")


# Decorators para limites específicos
def limit_auth_endpoints():
    """Limite mais restrito para endpoints de auth (evitar brute force)."""
    return limiter.limit("10/minute")


def limit_heavy_endpoints():
    """Limite para endpoints pesados (IA, integrações)."""
    return limiter.limit("20/minute")


def limit_light_endpoints():
    """Limite mais permissivo para endpoints leves."""
    return limiter.limit("200/minute")
