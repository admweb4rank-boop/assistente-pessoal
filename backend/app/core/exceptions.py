"""
TB Personal OS - Custom Exceptions
Hierarquia de exceções padronizadas
"""

from typing import Optional, Dict, Any


class AppError(Exception):
    """Base error para toda a aplicação."""
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte erro para dict para resposta JSON."""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AppError):
    """Erro de validação de dados de entrada."""
    status_code = 400
    error_code = "VALIDATION_ERROR"


class NotFoundError(AppError):
    """Recurso não encontrado."""
    status_code = 404
    error_code = "NOT_FOUND"


class AuthenticationError(AppError):
    """Erro de autenticação."""
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppError):
    """Erro de autorização (sem permissão)."""
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"


class ConflictError(AppError):
    """Conflito com estado atual (ex: duplicata)."""
    status_code = 409
    error_code = "CONFLICT_ERROR"


class RateLimitError(AppError):
    """Rate limit excedido."""
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class IntegrationError(AppError):
    """Erro em integração externa (Google, Gemini, etc)."""
    status_code = 502
    error_code = "INTEGRATION_ERROR"


class ServiceUnavailableError(AppError):
    """Serviço temporariamente indisponível."""
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"


class DatabaseError(AppError):
    """Erro de banco de dados."""
    status_code = 500
    error_code = "DATABASE_ERROR"


class ConfigurationError(AppError):
    """Erro de configuração."""
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
