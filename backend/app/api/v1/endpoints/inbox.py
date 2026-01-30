"""
TB Personal OS - Inbox API Endpoints
CRUD completo para inbox items
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime
import structlog

from supabase import Client
from app.api.v1.dependencies import get_supabase_client, get_current_user, get_current_user_id
from app.models.inbox import (
    InboxItemCreate,
    InboxItemUpdate,
    InboxItemResponse,
    InboxListResponse,
    InboxProcessRequest,
    InboxProcessResponse,
    InboxStatus,
    InboxCategory,
)
from app.models.common import SuccessResponse, ErrorResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar item na inbox",
    description="Cria um novo item na inbox unificada"
)
async def create_inbox_item(
    item: InboxItemCreate,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Cria um novo item na inbox."""
    try:
        data = {
            "user_id": user_id,
            "content": item.content,
            "content_type": item.content_type,
            "source": item.source,
            "status": "new",
            "category": item.category.value if item.category else "other",
            "tags": item.tags or [],
            "source_metadata": item.source_metadata or {}
        }
        
        result = supabase.table("inbox_items").insert(data).execute()
        
        logger.info(
            "inbox_item_created",
            item_id=result.data[0]["id"],
            user_id=user_id,
            category=item.category
        )
        
        return SuccessResponse(
            data=result.data[0],
            message="Item created successfully"
        )
        
    except Exception as e:
        logger.error("create_inbox_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create item: {str(e)}"
        )


@router.get(
    "",
    response_model=InboxListResponse,
    summary="Listar items da inbox",
    description="Lista items da inbox com filtros e paginação"
)
async def list_inbox_items(
    status: Optional[InboxStatus] = Query(None, description="Filtrar por status"),
    category: Optional[InboxCategory] = Query(None, description="Filtrar por categoria"),
    search: Optional[str] = Query(None, description="Buscar no conteúdo"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Items por página"),
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Lista items da inbox do usuário."""
    try:
        # Query base
        query = supabase.table("inbox_items")\
            .select("*", count="exact")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)
        
        # Aplicar filtros
        if status:
            query = query.eq("status", status.value)
        
        if category:
            query = query.eq("category", category.value)
        
        if search:
            query = query.ilike("content", f"%{search}%")
        
        # Paginação
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)
        
        result = query.execute()
        
        return InboxListResponse(
            data=result.data,
            total=result.count or 0,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error("list_inbox_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list items: {str(e)}"
        )


@router.get(
    "/{item_id}",
    response_model=SuccessResponse,
    summary="Obter item específico",
    description="Obtém um item da inbox pelo ID"
)
async def get_inbox_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém um item específico da inbox."""
    try:
        result = supabase.table("inbox_items")\
            .select("*")\
            .eq("id", item_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        return SuccessResponse(data=result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_inbox_failed", error=str(e), item_id=item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get item: {str(e)}"
        )


@router.patch(
    "/{item_id}",
    response_model=SuccessResponse,
    summary="Atualizar item",
    description="Atualiza um item da inbox"
)
async def update_inbox_item(
    item_id: str,
    item: InboxItemUpdate,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Atualiza um item da inbox."""
    try:
        # Verificar se existe
        check = supabase.table("inbox_items")\
            .select("id")\
            .eq("id", item_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Preparar dados para update
        update_data = item.model_dump(exclude_unset=True)
        
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
        
        if "category" in update_data and update_data["category"]:
            update_data["category"] = update_data["category"].value
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("inbox_items")\
            .update(update_data)\
            .eq("id", item_id)\
            .execute()
        
        logger.info("inbox_item_updated", item_id=item_id, fields=list(update_data.keys()))
        
        return SuccessResponse(
            data=result.data[0],
            message="Item updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_inbox_failed", error=str(e), item_id=item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete(
    "/{item_id}",
    response_model=SuccessResponse,
    summary="Deletar item",
    description="Remove um item da inbox"
)
async def delete_inbox_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Deleta um item da inbox."""
    try:
        # Verificar se existe
        check = supabase.table("inbox_items")\
            .select("id")\
            .eq("id", item_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        supabase.table("inbox_items")\
            .delete()\
            .eq("id", item_id)\
            .execute()
        
        logger.info("inbox_item_deleted", item_id=item_id, user_id=user_id)
        
        return SuccessResponse(message="Item deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_inbox_failed", error=str(e), item_id=item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )


@router.post(
    "/{item_id}/process",
    response_model=InboxProcessResponse,
    summary="Processar item com IA",
    description="Processa um item da inbox usando Gemini para classificação"
)
async def process_inbox_item(
    item_id: str,
    request: InboxProcessRequest = InboxProcessRequest(),
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Processa um item da inbox com IA."""
    try:
        # Buscar item
        result = supabase.table("inbox_items")\
            .select("*")\
            .eq("id", item_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        item = result.data[0]
        
        # Classificar com Gemini
        from app.services.gemini_service import GeminiService
        gemini = GeminiService()
        
        prompt = f"""Analise esta mensagem e classifique-a.

MENSAGEM: "{item['content']}"

Retorne APENAS um JSON válido no formato:
{{
    "type": "task|idea|note|question",
    "category": "personal|work|health|content|finance|other",
    "priority": "low|medium|high|urgent",
    "needs_response": true ou false,
    "suggested_action": "descrição da ação sugerida",
    "entities": {{
        "people": [],
        "dates": [],
        "values": []
    }}
}}"""
        
        import asyncio
        response = await gemini.generate_text(prompt, temperature=0.3)
        
        # Parse JSON
        import json
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            classification = json.loads(response[json_start:json_end])
        else:
            classification = {
                "type": "note",
                "category": "other",
                "priority": "medium",
                "error": "Failed to parse AI response"
            }
        
        # Atualizar item
        update_data = {
            "status": "processed",
            "category": classification.get("category", item["category"]),
            "suggested_actions": classification,
            "processed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        updated = supabase.table("inbox_items")\
            .update(update_data)\
            .eq("id", item_id)\
            .execute()
        
        logger.info(
            "inbox_item_processed",
            item_id=item_id,
            classification=classification
        )
        
        return InboxProcessResponse(
            success=True,
            item=updated.data[0],
            classification=classification,
            message="Item processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("process_inbox_failed", error=str(e), item_id=item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process item: {str(e)}"
        )


@router.post(
    "/archive-processed",
    response_model=SuccessResponse,
    summary="Arquivar items processados",
    description="Arquiva todos os items com status 'processed'"
)
async def archive_processed_items(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Arquiva todos os items processados."""
    try:
        result = supabase.table("inbox_items")\
            .update({"status": "archived", "updated_at": datetime.utcnow().isoformat()})\
            .eq("user_id", user_id)\
            .eq("status", "processed")\
            .execute()
        
        count = len(result.data) if result.data else 0
        
        logger.info("inbox_items_archived", count=count, user_id=user_id)
        
        return SuccessResponse(
            data={"archived_count": count},
            message=f"{count} items archived"
        )
        
    except Exception as e:
        logger.error("archive_inbox_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive items: {str(e)}"
        )
