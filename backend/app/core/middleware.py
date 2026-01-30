"""
TB Personal OS - Middleware Stack
Middlewares para observabilidade, error handling e segurança
"""

import time
import uuid
from typing import Callable
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.exceptions import AppError

logger = structlog.get_logger(__name__)

# Context var para correlation ID (thread-safe)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Obtém correlation ID do contexto atual."""
    return correlation_id_var.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware para adicionar correlation ID a cada request.
    
    - Gera UUID se não existir no header
    - Adiciona ao contexto para uso em logs
    - Inclui no header de resposta
    """
    
    HEADER_NAME = "X-Correlation-ID"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Obter ou gerar correlation ID
        correlation_id = request.headers.get(self.HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Setar no contexto
        token = correlation_id_var.set(correlation_id)
        
        # Adicionar ao request state para uso em outros lugares
        request.state.correlation_id = correlation_id
        
        try:
            # Processar request
            response = await call_next(request)
            
            # Adicionar header de resposta
            response.headers[self.HEADER_NAME] = correlation_id
            
            return response
        finally:
            # Resetar contexto
            correlation_id_var.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging estruturado de requests.
    
    - Log de início e fim de cada request
    - Métricas de duração
    - Info de erro se houver
    """
    
    # Paths para não logar (health checks, etc)
    SKIP_PATHS = {"/health", "/metrics", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip paths que não devem ser logados
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Obter correlation ID
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        # Info básica do request
        request_info = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown")[:100]
        }
        
        # Log de início
        logger.info("request_started", **request_info)
        
        # Medir tempo
        start_time = time.perf_counter()
        
        try:
            # Processar request
            response = await call_next(request)
            
            # Calcular duração
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Log de sucesso
            logger.info(
                "request_completed",
                **request_info,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # Adicionar header de tempo de resposta
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            
            return response
            
        except Exception as e:
            # Calcular duração mesmo em erro
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Log de erro
            logger.error(
                "request_failed",
                **request_info,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP do cliente, considerando proxies."""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback para IP direto
        if request.client:
            return request.client.host
        
        return "unknown"


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware global para tratamento de erros.
    
    - Captura exceções não tratadas
    - Formata resposta de erro consistente
    - Log de erros com contexto
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except AppError as e:
            # Erro de aplicação (esperado)
            return self._create_error_response(
                request=request,
                status_code=e.status_code,
                error_code=e.error_code,
                message=e.message,
                details=e.details
            )
            
        except Exception as e:
            # Erro inesperado
            logger.exception(
                "unhandled_exception",
                correlation_id=getattr(request.state, "correlation_id", "unknown"),
                path=request.url.path,
                error=str(e)
            )
            
            return self._create_error_response(
                request=request,
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="Ocorreu um erro interno. Tente novamente.",
                details={"error_type": type(e).__name__}
            )
    
    def _create_error_response(
        self,
        request: Request,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None
    ) -> JSONResponse:
        """Cria resposta de erro padronizada."""
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details or {}
                },
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            },
            headers={
                "X-Correlation-ID": correlation_id
            }
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para adicionar headers de segurança.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Cache control para APIs
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response


def setup_middlewares(app: FastAPI) -> None:
    """
    Configura todos os middlewares na ordem correta.
    
    Ordem de execução (de fora para dentro):
    1. Security Headers
    2. Correlation ID
    3. Request Logging
    4. Error Handling
    """
    # A ordem de adição é inversa à ordem de execução
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
