"""
TB Personal OS - Common Response Models
Schemas de resposta padrão da API
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict


class SuccessResponse(BaseModel):
    """Resposta de sucesso padrão."""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Operation completed successfully"


class ErrorDetail(BaseModel):
    """Detalhes do erro."""
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Resposta de erro padrão."""
    success: bool = False
    error: ErrorDetail


class PaginationMeta(BaseModel):
    """Metadados de paginação."""
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    """Resposta paginada padrão."""
    success: bool = True
    data: list
    meta: PaginationMeta


class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str
    service: str
    version: str
    environment: str
    checks: Optional[Dict[str, bool]] = None
