"""
TB Personal OS - Drive API Endpoints
Endpoints para gerenciamento de arquivos no Google Drive
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import Optional, List
from pydantic import BaseModel
import structlog

from app.api.v1.dependencies.auth import get_current_user
from app.services.drive_service import drive_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/drive", tags=["Drive"])


# ==========================================
# SCHEMAS
# ==========================================

class FolderCreate(BaseModel):
    """Dados para criar pasta."""
    name: str
    parent_id: Optional[str] = None


class ProjectFolderCreate(BaseModel):
    """Dados para criar estrutura de projeto."""
    project_name: str
    base_folder_id: Optional[str] = None


class FileMove(BaseModel):
    """Dados para mover arquivo."""
    new_parent_id: str


class FileResponse(BaseModel):
    """Resposta com dados de arquivo."""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    modified_at: Optional[str] = None
    url: Optional[str] = None
    is_folder: bool = False


class FolderResponse(BaseModel):
    """Resposta com dados de pasta."""
    id: str
    name: str
    url: Optional[str] = None
    type: str = "folder"


class StorageQuotaResponse(BaseModel):
    """Resposta com quota de armazenamento."""
    limit: int
    usage: int
    limit_gb: float
    usage_gb: float


# ==========================================
# ENDPOINTS - FOLDERS
# ==========================================

@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    data: FolderCreate,
    user: dict = Depends(get_current_user)
):
    """Cria uma pasta no Drive."""
    try:
        folder = await drive_service.create_folder(
            user_id=user["id"],
            name=data.name,
            parent_id=data.parent_id
        )
        return FolderResponse(**folder)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("create_folder_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar pasta: {str(e)}")


@router.post("/folders/project")
async def create_project_folder(
    data: ProjectFolderCreate,
    user: dict = Depends(get_current_user)
):
    """
    Cria estrutura de pastas para um projeto.
    
    Cria automaticamente:
    - Pasta principal com nome do projeto
    - Subpastas: Documentos, Recursos, Entregas
    """
    try:
        result = await drive_service.create_project_folder(
            user_id=user["id"],
            project_name=data.project_name,
            base_folder_id=data.base_folder_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("create_project_folder_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar pastas: {str(e)}")


# ==========================================
# ENDPOINTS - FILES LIST & SEARCH
# ==========================================

@router.get("/files")
async def list_files(
    folder_id: Optional[str] = Query(None, description="ID da pasta (None = root)"),
    page_size: int = Query(20, ge=1, le=100),
    page_token: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Lista arquivos no Drive."""
    try:
        result = await drive_service.list_files(
            user_id=user["id"],
            folder_id=folder_id,
            page_size=page_size,
            page_token=page_token
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("list_files_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao listar arquivos: {str(e)}")


@router.get("/files/recent", response_model=List[FileResponse])
async def get_recent_files(
    max_results: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """Lista arquivos recentes (últimos modificados)."""
    try:
        files = await drive_service.get_recent_files(
            user_id=user["id"],
            max_results=max_results
        )
        return [FileResponse(**f) for f in files]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_recent_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar recentes: {str(e)}")


@router.get("/search", response_model=List[FileResponse])
async def search_files(
    q: str = Query(..., description="Termo de busca"),
    max_results: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """Busca arquivos por nome."""
    try:
        files = await drive_service.search_files(
            user_id=user["id"],
            query=q,
            max_results=max_results
        )
        return [FileResponse(**f) for f in files]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("search_failed", user_id=user["id"], query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


# ==========================================
# ENDPOINTS - FILE DETAILS
# ==========================================

@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtém detalhes de um arquivo."""
    try:
        file = await drive_service.get_file(
            user_id=user["id"],
            file_id=file_id
        )
        return file
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_file_failed", user_id=user["id"], file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar arquivo: {str(e)}")


# ==========================================
# ENDPOINTS - UPLOAD
# ==========================================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Query(None, description="ID da pasta destino"),
    user: dict = Depends(get_current_user)
):
    """
    Faz upload de um arquivo.
    
    Aceita qualquer tipo de arquivo.
    """
    try:
        content = await file.read()
        
        result = await drive_service.upload_content(
            user_id=user["id"],
            content=content,
            file_name=file.filename,
            mime_type=file.content_type or 'application/octet-stream',
            folder_id=folder_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("upload_failed", user_id=user["id"], filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


# ==========================================
# ENDPOINTS - ACTIONS
# ==========================================

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    user: dict = Depends(get_current_user)
):
    """Move arquivo para a lixeira."""
    try:
        await drive_service.delete_file(
            user_id=user["id"],
            file_id=file_id
        )
        return {"status": "success", "message": "Arquivo movido para lixeira"}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("delete_failed", user_id=user["id"], file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")


@router.post("/files/{file_id}/move")
async def move_file(
    file_id: str,
    data: FileMove,
    user: dict = Depends(get_current_user)
):
    """Move arquivo para outra pasta."""
    try:
        result = await drive_service.move_file(
            user_id=user["id"],
            file_id=file_id,
            new_parent_id=data.new_parent_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("move_failed", user_id=user["id"], file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao mover: {str(e)}")


# ==========================================
# ENDPOINTS - STORAGE
# ==========================================

@router.get("/quota", response_model=StorageQuotaResponse)
async def get_storage_quota(
    user: dict = Depends(get_current_user)
):
    """Obtém informações de quota de armazenamento."""
    try:
        quota = await drive_service.get_storage_quota(user_id=user["id"])
        return StorageQuotaResponse(**quota)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_quota_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar quota: {str(e)}")
