"""
TB Personal OS - Pydantic Models for Tasks
Schemas para validação de dados de tarefas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum


class TaskStatus(str, Enum):
    """Status possíveis de uma tarefa."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Níveis de prioridade."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskBase(BaseModel):
    """Base schema para tarefa."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    tags: Optional[List[str]] = []
    project_id: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=1440)


class TaskCreate(TaskBase):
    """Schema para criação de tarefa."""
    inbox_item_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """Schema para atualização de tarefa."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    tags: Optional[List[str]] = None
    project_id: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=1440)
    actual_minutes: Optional[int] = Field(None, ge=0)


class TaskResponse(BaseModel):
    """Schema de resposta para tarefa."""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    due_time: Optional[time]
    completed_at: Optional[datetime]
    project_id: Optional[str]
    parent_task_id: Optional[str]
    inbox_item_id: Optional[str]
    tags: List[str]
    estimated_minutes: Optional[int]
    actual_minutes: Optional[int]
    is_recurring: bool
    recurrence_rule: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema de resposta para lista de tarefas."""
    success: bool = True
    data: List[TaskResponse]
    total: int
    page: int
    per_page: int


class TaskCompleteRequest(BaseModel):
    """Schema para marcar tarefa como concluída."""
    actual_minutes: Optional[int] = Field(None, ge=0, description="Tempo real gasto em minutos")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas sobre a conclusão")


class TaskBulkUpdateRequest(BaseModel):
    """Schema para atualização em lote."""
    task_ids: List[str]
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    project_id: Optional[str] = None
