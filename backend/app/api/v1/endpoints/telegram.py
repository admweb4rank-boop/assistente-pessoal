"""
TB Personal OS - Telegram Webhook Endpoints
Endpoints para receber e gerenciar webhooks do Telegram
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from typing import Optional
import structlog

from supabase import Client
from app.core.config import settings
from app.api.v1.dependencies import get_supabase_client
from app.models.common import SuccessResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/webhook",
    summary="Receber update do Telegram",
    description="Endpoint para receber webhooks do Telegram Bot API"
)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Recebe updates do Telegram via webhook.
    
    Este endpoint é chamado pelo Telegram quando há novas mensagens.
    """
    # Verificar secret token se configurado
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("telegram_webhook_invalid_secret")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret token"
            )
    
    try:
        # Obter body do request
        update = await request.json()
        
        logger.info(
            "telegram_webhook_received",
            update_id=update.get("update_id"),
            has_message=bool(update.get("message")),
            has_callback=bool(update.get("callback_query"))
        )
        
        # Processar mensagem
        message = update.get("message", {})
        callback_query = update.get("callback_query", {})
        
        if message:
            await _process_message(message, supabase)
        elif callback_query:
            await _process_callback(callback_query, supabase)
        
        # Telegram espera 200 OK
        return {"ok": True}
        
    except Exception as e:
        logger.error("telegram_webhook_failed", error=str(e), exc_info=True)
        # Retornar OK mesmo em erro para evitar reenvios do Telegram
        return {"ok": True, "error": str(e)}


async def _process_message(message: dict, supabase: Client):
    """Processa uma mensagem do Telegram."""
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    user = message.get("from", {})
    
    if not chat_id or not text:
        return
    
    # Verificar se é o owner
    if str(chat_id) != settings.OWNER_TELEGRAM_CHAT_ID:
        logger.warning("telegram_unauthorized_user", chat_id=chat_id)
        return
    
    logger.info(
        "telegram_message_processing",
        chat_id=chat_id,
        text_preview=text[:50],
        username=user.get("username")
    )
    
    # Buscar user_id
    user_result = supabase.table("telegram_chats")\
        .select("user_id")\
        .eq("chat_id", chat_id)\
        .execute()
    
    if not user_result.data:
        logger.warning("telegram_user_not_found", chat_id=chat_id)
        return
    
    user_id = user_result.data[0]["user_id"]
    
    # Se for comando, ignorar (será processado pelo polling)
    if text.startswith("/"):
        return
    
    # Salvar na inbox (processamento básico via webhook)
    # O processamento completo com IA é feito via polling no bot
    try:
        inbox_data = {
            "user_id": user_id,
            "content": text,
            "content_type": "text",
            "source": "telegram",
            "status": "new",
            "category": "other",
            "source_metadata": {
                "telegram_chat_id": chat_id,
                "telegram_message_id": message.get("message_id"),
                "telegram_user_id": user.get("id"),
                "username": user.get("username"),
                "webhook": True
            }
        }
        
        result = supabase.table("inbox_items").insert(inbox_data).execute()
        
        logger.info(
            "telegram_message_saved",
            item_id=result.data[0]["id"],
            user_id=user_id
        )
        
    except Exception as e:
        logger.error("telegram_save_failed", error=str(e))


async def _process_callback(callback_query: dict, supabase: Client):
    """Processa um callback query do Telegram."""
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    user = callback_query.get("from", {})
    
    logger.info(
        "telegram_callback_received",
        callback_id=callback_id,
        data=data,
        user_id=user.get("id")
    )
    
    # Callback queries são processados pelo bot em polling
    # Aqui apenas logamos


@router.get(
    "/webhook/info",
    response_model=SuccessResponse,
    summary="Info do webhook",
    description="Obtém informações do webhook configurado"
)
async def get_webhook_info():
    """Obtém informações do webhook do Telegram."""
    try:
        import httpx
        
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
        
        return SuccessResponse(
            data=data.get("result", {}),
            message="Webhook info retrieved"
        )
        
    except Exception as e:
        logger.error("get_webhook_info_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook info: {str(e)}"
        )


@router.post(
    "/webhook/set",
    response_model=SuccessResponse,
    summary="Configurar webhook",
    description="Configura o webhook do Telegram"
)
async def set_webhook(
    webhook_url: Optional[str] = None
):
    """
    Configura o webhook do Telegram.
    
    Se webhook_url não for fornecido, usa TELEGRAM_WEBHOOK_URL das settings.
    """
    try:
        import httpx
        
        url = webhook_url or settings.TELEGRAM_WEBHOOK_URL
        
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook URL is required"
            )
        
        api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
        
        payload = {
            "url": url,
            "allowed_updates": ["message", "callback_query"]
        }
        
        if settings.TELEGRAM_WEBHOOK_SECRET:
            payload["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, timeout=10.0)
            data = response.json()
        
        if data.get("ok"):
            logger.info("telegram_webhook_set", url=url)
            return SuccessResponse(
                data=data,
                message=f"Webhook set to: {url}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data.get("description", "Failed to set webhook")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("set_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set webhook: {str(e)}"
        )


@router.delete(
    "/webhook",
    response_model=SuccessResponse,
    summary="Remover webhook",
    description="Remove o webhook do Telegram (volta para polling)"
)
async def delete_webhook():
    """Remove o webhook do Telegram."""
    try:
        import httpx
        
        api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteWebhook"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, timeout=10.0)
            data = response.json()
        
        if data.get("ok"):
            logger.info("telegram_webhook_deleted")
            return SuccessResponse(
                data=data,
                message="Webhook deleted"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data.get("description", "Failed to delete webhook")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook: {str(e)}"
        )


@router.post(
    "/send",
    response_model=SuccessResponse,
    summary="Enviar mensagem",
    description="Envia uma mensagem via Telegram"
)
async def send_message(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "Markdown"
):
    """
    Envia uma mensagem via Telegram.
    
    Se chat_id não for fornecido, envia para o owner.
    """
    try:
        import httpx
        
        target_chat_id = chat_id or settings.OWNER_TELEGRAM_CHAT_ID
        
        if not target_chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat ID is required"
            )
        
        api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": target_chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, timeout=10.0)
            data = response.json()
        
        if data.get("ok"):
            logger.info("telegram_message_sent", chat_id=target_chat_id)
            return SuccessResponse(
                data=data.get("result"),
                message="Message sent"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data.get("description", "Failed to send message")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("send_message_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )
