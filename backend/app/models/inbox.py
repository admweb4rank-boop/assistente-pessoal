"""
TB Personal OS - Pydantic Models for Inbox
Schemas para validação de dados da inbox
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InboxStatus(str, Enum):
    """Status possíveis de um item da inbox."""
    NEW = "new"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ARCHIVED = "archived"


class InboxCategory(str, Enum):
    """Categorias possíveis."""
    PERSONAL = "personal"
    WORK = "work"
    HEALTH = "health"
    CONTENT = "content"
    FINANCE = "finance"
    OTHER = "other"


class InboxItemBase(BaseModel):
    """Base schema para inbox item."""
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = Field(default="text", pattern="^(text|link|file|voice)$")
    category: Optional[InboxCategory] = InboxCategory.OTHER
    tags: Optional[List[str]] = []
    source: str = Field(default="api", pattern="^(telegram|web|api)$")


class InboxItemCreate(InboxItemBase):
    """Schema para criação de inbox item."""
    source_metadata: Optional[Dict[str, Any]] = {}


class InboxItemUpdate(BaseModel):
    """Schema para atualização de inbox item."""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    status: Optional[InboxStatus] = None
    category: Optional[InboxCategory] = None
    tags: Optional[List[str]] = None
    suggested_actions: Optional[Dict[str, Any]] = None


class InboxItemResponse(BaseModel):
    """Schema de resposta para inbox item."""
    id: str
    user_id: str
    content: str
    content_type: str
    status: str
    category: str
    tags: List[str]
    source: str
    source_metadata: Optional[Dict[str, Any]]
    suggested_actions: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InboxListResponse(BaseModel):
    """Schema de resposta para lista de inbox items."""
    success: bool = True
    data: List[InboxItemResponse]
    total: int
    page: int
    per_page: int
    

class InboxProcessRequest(BaseModel):
    """Schema para requisição de processamento."""
    force_ai: bool = Field(default=True, description="Forçar uso de IA para classificação")


class InboxProcessResponse(BaseModel):
    """Schema de resposta para processamento."""
    success: bool
    item: InboxItemResponse
    classification: Dict[str, Any]
    message: str
