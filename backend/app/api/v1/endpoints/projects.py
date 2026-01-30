"""
TB Personal OS - Projects Endpoints
API para gerenciamento de projetos
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date
import structlog

from app.services.project_service import project_service
from app.api.v1.dependencies.auth import require_api_key
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


# ==========================================
# SCHEMAS
# ==========================================

class CreateProjectRequest(BaseModel):
    """Request para criar projeto."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, description="Cor hex (ex: #3B82F6)")
    due_date: Optional[date] = None
    goals: Optional[List[str]] = Field(None, max_items=10)


class UpdateProjectRequest(BaseModel):
    """Request para atualizar projeto."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = Field(None, description="active, paused, completed, archived")
    due_date: Optional[date] = None
    goals: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    """Response de projeto."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    status: str
    progress: int
    goals: Optional[List[str]] = None
    due_date: Optional[str] = None
    created_at: str


class ProjectStatsResponse(BaseModel):
    """Response de estatísticas."""
    total_tasks: int
    completed: int
    in_progress: int
    todo: int
    high_priority: int
    progress: int


class AddTaskRequest(BaseModel):
    """Request para adicionar tarefa."""
    task_id: str


# ==========================================
# ENDPOINTS - CRUD
# ==========================================

@router.post("/", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Cria um novo projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        project = await project_service.create_project(
            user_id=target_user_id,
            name=request.name,
            description=request.description,
            category=request.category,
            color=request.color,
            due_date=request.due_date.isoformat() if request.due_date else None,
            goals=request.goals
        )
        
        return ProjectResponse(**project)
        
    except Exception as e:
        logger.error("create_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None, description="active, paused, completed, archived"),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Lista projetos do usuário.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        projects = await project_service.list_projects(
            user_id=target_user_id,
            status=status,
            category=category,
            limit=limit
        )
        
        return [ProjectResponse(**p) for p in projects]
        
    except Exception as e:
        logger.error("list_projects_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str = Path(...),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Obtém detalhes de um projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        project = await project_service.get_project(project_id, target_user_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        return ProjectResponse(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    request: UpdateProjectRequest,
    project_id: str = Path(...),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Atualiza um projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if "due_date" in updates and updates["due_date"]:
        updates["due_date"] = updates["due_date"].isoformat()
    
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    
    try:
        project = await project_service.update_project(
            project_id=project_id,
            user_id=target_user_id,
            updates=updates
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        return ProjectResponse(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    project_id: str = Path(...),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Deleta um projeto.
    Tarefas associadas são desassociadas (não deletadas).
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        success = await project_service.delete_project(project_id, target_user_id)
        
        if success:
            return {"success": True, "message": "Projeto deletado"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao deletar projeto")
            
    except Exception as e:
        logger.error("delete_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINTS - TASKS
# ==========================================

@router.get("/{project_id}/tasks", response_model=List[Dict[str, Any]])
async def get_project_tasks(
    project_id: str = Path(...),
    status: Optional[str] = Query(None),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Lista tarefas de um projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        tasks = await project_service.get_project_tasks(
            project_id=project_id,
            user_id=target_user_id,
            status=status
        )
        
        return tasks
        
    except Exception as e:
        logger.error("get_project_tasks_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/tasks")
async def add_task_to_project(
    request: AddTaskRequest,
    project_id: str = Path(...),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Adiciona uma tarefa existente ao projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        success = await project_service.add_task_to_project(
            task_id=request.task_id,
            project_id=project_id,
            user_id=target_user_id
        )
        
        if success:
            return {"success": True, "message": "Tarefa adicionada ao projeto"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao adicionar tarefa")
            
    except Exception as e:
        logger.error("add_task_to_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/tasks/{task_id}")
async def remove_task_from_project(
    project_id: str = Path(...),
    task_id: str = Path(...),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Remove uma tarefa do projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        success = await project_service.remove_task_from_project(
            task_id=task_id,
            user_id=target_user_id
        )
        
        if success:
            return {"success": True, "message": "Tarefa removida do projeto"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao remover tarefa")
            
    except Exception as e:
        logger.error("remove_task_from_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINTS - STATS
# ==========================================

@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: str = Path(...),
    user_id: str = Query(default=None),
    _: str = Depends(require_api_key)
):
    """
    Obtém estatísticas do projeto.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    try:
        stats = await project_service.get_project_stats(project_id, target_user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        return ProjectStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_project_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
