"""
TB Personal OS - Tasks API Endpoints
CRUD completo para tarefas
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime, date
import structlog

from supabase import Client
from app.api.v1.dependencies import get_supabase_client, get_current_user, get_current_user_id
from app.models.tasks import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskCompleteRequest,
    TaskBulkUpdateRequest,
    TaskStatus,
    TaskPriority,
)
from app.models.common import SuccessResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar tarefa",
    description="Cria uma nova tarefa"
)
async def create_task(
    task: TaskCreate,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Cria uma nova tarefa."""
    try:
        data = {
            "user_id": user_id,
            "title": task.title,
            "description": task.description,
            "status": "todo",
            "priority": task.priority.value if task.priority else "medium",
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "due_time": task.due_time.isoformat() if task.due_time else None,
            "tags": task.tags or [],
            "project_id": task.project_id,
            "inbox_item_id": task.inbox_item_id,
            "estimated_minutes": task.estimated_minutes
        }
        
        result = supabase.table("tasks").insert(data).execute()
        
        logger.info(
            "task_created",
            task_id=result.data[0]["id"],
            user_id=user_id,
            title=task.title[:50]
        )
        
        return SuccessResponse(
            data=result.data[0],
            message="Task created successfully"
        )
        
    except Exception as e:
        logger.error("create_task_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Listar tarefas",
    description="Lista tarefas com filtros e paginação"
)
async def list_tasks(
    task_status: Optional[TaskStatus] = Query(None, alias="status", description="Filtrar por status"),
    priority: Optional[TaskPriority] = Query(None, description="Filtrar por prioridade"),
    project_id: Optional[str] = Query(None, description="Filtrar por projeto"),
    due_date_from: Optional[date] = Query(None, description="Data limite inicial"),
    due_date_to: Optional[date] = Query(None, description="Data limite final"),
    search: Optional[str] = Query(None, description="Buscar no título"),
    include_done: bool = Query(False, description="Incluir tarefas concluídas"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Items por página"),
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Lista tarefas do usuário."""
    try:
        # Query base
        query = supabase.table("tasks")\
            .select("*", count="exact")\
            .eq("user_id", user_id)\
            .order("priority", desc=True)\
            .order("due_date")\
            .order("created_at", desc=True)
        
        # Aplicar filtros
        if task_status:
            query = query.eq("status", task_status.value)
        elif not include_done:
            query = query.in_("status", ["todo", "in_progress"])
        
        if priority:
            query = query.eq("priority", priority.value)
        
        if project_id:
            query = query.eq("project_id", project_id)
        
        if due_date_from:
            query = query.gte("due_date", due_date_from.isoformat())
        
        if due_date_to:
            query = query.lte("due_date", due_date_to.isoformat())
        
        if search:
            query = query.ilike("title", f"%{search}%")
        
        # Paginação
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)
        
        result = query.execute()
        
        return TaskListResponse(
            data=result.data,
            total=result.count or 0,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error("list_tasks_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.get(
    "/today",
    response_model=SuccessResponse,
    summary="Tarefas de hoje",
    description="Lista tarefas com vencimento hoje"
)
async def get_today_tasks(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém tarefas de hoje."""
    try:
        today = date.today().isoformat()
        
        result = supabase.table("tasks")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("due_date", today)\
            .in_("status", ["todo", "in_progress"])\
            .order("priority", desc=True)\
            .execute()
        
        return SuccessResponse(
            data=result.data,
            message=f"{len(result.data)} tasks for today"
        )
        
    except Exception as e:
        logger.error("get_today_tasks_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's tasks: {str(e)}"
        )


@router.get(
    "/overdue",
    response_model=SuccessResponse,
    summary="Tarefas atrasadas",
    description="Lista tarefas com vencimento passado"
)
async def get_overdue_tasks(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém tarefas atrasadas."""
    try:
        today = date.today().isoformat()
        
        result = supabase.table("tasks")\
            .select("*")\
            .eq("user_id", user_id)\
            .lt("due_date", today)\
            .in_("status", ["todo", "in_progress"])\
            .order("due_date")\
            .execute()
        
        return SuccessResponse(
            data=result.data,
            message=f"{len(result.data)} overdue tasks"
        )
        
    except Exception as e:
        logger.error("get_overdue_tasks_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overdue tasks: {str(e)}"
        )


@router.get(
    "/{task_id}",
    response_model=SuccessResponse,
    summary="Obter tarefa",
    description="Obtém uma tarefa pelo ID"
)
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém uma tarefa específica."""
    try:
        result = supabase.table("tasks")\
            .select("*")\
            .eq("id", task_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return SuccessResponse(data=result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_task_failed", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.patch(
    "/{task_id}",
    response_model=SuccessResponse,
    summary="Atualizar tarefa",
    description="Atualiza uma tarefa"
)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Atualiza uma tarefa."""
    try:
        # Verificar se existe
        check = supabase.table("tasks")\
            .select("id")\
            .eq("id", task_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Preparar dados para update
        update_data = task.model_dump(exclude_unset=True)
        
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
        
        if "priority" in update_data and update_data["priority"]:
            update_data["priority"] = update_data["priority"].value
        
        if "due_date" in update_data and update_data["due_date"]:
            update_data["due_date"] = update_data["due_date"].isoformat()
        
        if "due_time" in update_data and update_data["due_time"]:
            update_data["due_time"] = update_data["due_time"].isoformat()
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("tasks")\
            .update(update_data)\
            .eq("id", task_id)\
            .execute()
        
        logger.info("task_updated", task_id=task_id, fields=list(update_data.keys()))
        
        return SuccessResponse(
            data=result.data[0],
            message="Task updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_task_failed", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.post(
    "/{task_id}/complete",
    response_model=SuccessResponse,
    summary="Concluir tarefa",
    description="Marca uma tarefa como concluída"
)
async def complete_task(
    task_id: str,
    request: TaskCompleteRequest = TaskCompleteRequest(),
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Marca uma tarefa como concluída."""
    try:
        # Verificar se existe
        check = supabase.table("tasks")\
            .select("id, title")\
            .eq("id", task_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        update_data = {
            "status": "done",
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if request.actual_minutes:
            update_data["actual_minutes"] = request.actual_minutes
        
        result = supabase.table("tasks")\
            .update(update_data)\
            .eq("id", task_id)\
            .execute()
        
        logger.info("task_completed", task_id=task_id, title=check.data[0]["title"][:50])
        
        return SuccessResponse(
            data=result.data[0],
            message="Task completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("complete_task_failed", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete task: {str(e)}"
        )


@router.delete(
    "/{task_id}",
    response_model=SuccessResponse,
    summary="Deletar tarefa",
    description="Remove uma tarefa"
)
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Deleta uma tarefa."""
    try:
        # Verificar se existe
        check = supabase.table("tasks")\
            .select("id")\
            .eq("id", task_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        supabase.table("tasks")\
            .delete()\
            .eq("id", task_id)\
            .execute()
        
        logger.info("task_deleted", task_id=task_id, user_id=user_id)
        
        return SuccessResponse(message="Task deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_task_failed", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.post(
    "/bulk-update",
    response_model=SuccessResponse,
    summary="Atualização em lote",
    description="Atualiza múltiplas tarefas de uma vez"
)
async def bulk_update_tasks(
    request: TaskBulkUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Atualiza múltiplas tarefas."""
    try:
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if request.status:
            update_data["status"] = request.status.value
        
        if request.priority:
            update_data["priority"] = request.priority.value
        
        if request.project_id:
            update_data["project_id"] = request.project_id
        
        updated_count = 0
        for task_id in request.task_ids:
            result = supabase.table("tasks")\
                .update(update_data)\
                .eq("id", task_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                updated_count += 1
        
        logger.info(
            "tasks_bulk_updated",
            count=updated_count,
            user_id=user_id
        )
        
        return SuccessResponse(
            data={"updated_count": updated_count},
            message=f"{updated_count} tasks updated"
        )
        
    except Exception as e:
        logger.error("bulk_update_tasks_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tasks: {str(e)}"
        )
