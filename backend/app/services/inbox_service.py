"""
TB Personal OS - Inbox Service
Gerencia items da inbox unificada
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from supabase import Client
import structlog

logger = structlog.get_logger()


class InboxService:
    """Service para gerenciar inbox items"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def create_inbox_item(
        self,
        user_id: str,
        content: str,
        source: str = "telegram",
        content_type: str = "text",
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_metadata: Optional[dict] = None,
        suggested_actions: Optional[dict] = None
    ) -> dict:
        """
        Cria um novo item na inbox
        
        Args:
            user_id: ID do usuário
            content: Conteúdo do item
            source: Origem (telegram, web, api)
            content_type: Tipo (text, link, file, voice)
            category: Categoria do item
            tags: Tags do item
            source_metadata: Metadata da origem
            suggested_actions: Ações sugeridas pelo LLM
        
        Returns:
            dict: Item criado
        """
        try:
            data = {
                "user_id": user_id,
                "content": content,
                "content_type": content_type,
                "source": source,
                "status": "new",
                "category": category or "other",
                "tags": tags or [],
                "source_metadata": source_metadata or {},
                "suggested_actions": suggested_actions or {}
            }
            
            result = self.supabase.table("inbox_items").insert(data).execute()
            
            logger.info(
                "inbox_item_created",
                item_id=result.data[0]["id"],
                user_id=user_id,
                category=category
            )
            
            return result.data[0]
            
        except Exception as e:
            logger.error("inbox_creation_failed", error=str(e), user_id=user_id)
            raise
    
    async def get_user_inbox(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        Obtém items da inbox do usuário
        
        Args:
            user_id: ID do usuário
            status: Filtrar por status (new, processing, processed, archived)
            limit: Limite de resultados
        
        Returns:
            List[dict]: Lista de items
        """
        try:
            query = self.supabase.table("inbox_items")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error("inbox_fetch_failed", error=str(e), user_id=user_id)
            raise
    
    async def update_inbox_status(
        self,
        item_id: str,
        status: str,
        processed_at: Optional[datetime] = None
    ) -> dict:
        """
        Atualiza status de um item
        
        Args:
            item_id: ID do item
            status: Novo status
            processed_at: Data de processamento
        
        Returns:
            dict: Item atualizado
        """
        try:
            data = {"status": status}
            if processed_at:
                data["processed_at"] = processed_at.isoformat()
            
            result = self.supabase.table("inbox_items")\
                .update(data)\
                .eq("id", item_id)\
                .execute()
            
            logger.info("inbox_status_updated", item_id=item_id, status=status)
            return result.data[0]
            
        except Exception as e:
            logger.error("inbox_update_failed", error=str(e), item_id=item_id)
            raise
