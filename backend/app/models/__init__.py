"""
TB Personal OS - Models Package
Pydantic schemas for API validation
"""

from app.models.inbox import (
    InboxItemCreate,
    InboxItemUpdate,
    InboxItemResponse,
    InboxListResponse,
    InboxStatus,
    InboxCategory,
)

from app.models.tasks import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatus,
    TaskPriority,
)

from app.models.common import (
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
)

__all__ = [
    # Inbox
    "InboxItemCreate",
    "InboxItemUpdate", 
    "InboxItemResponse",
    "InboxListResponse",
    "InboxStatus",
    "InboxCategory",
    # Tasks
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    "TaskStatus",
    "TaskPriority",
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
]