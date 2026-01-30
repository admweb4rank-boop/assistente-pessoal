"""
TB Personal OS - Telegram Bot Service
Interface for Telegram Bot API
"""

import httpx
import structlog
from typing import Optional, Dict, Any
from app.core.config import settings

logger = structlog.get_logger()


class TelegramService:
    """Service for interacting with Telegram Bot API"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.owner_chat_id = settings.OWNER_TELEGRAM_CHAT_ID
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Send message to Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (Markdown, HTML)
            reply_markup: Inline keyboard markup
            
        Returns:
            API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "reply_markup": reply_markup,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(
                    "Message sent to Telegram",
                    chat_id=chat_id,
                    message_length=len(text),
                )
                
                return result
                
        except Exception as e:
            logger.error(
                "Failed to send Telegram message",
                exc_info=e,
                chat_id=chat_id,
            )
            raise
    
    async def send_to_owner(
        self,
        text: str,
        parse_mode: str = "Markdown",
    ) -> Dict[str, Any]:
        """Send message to owner (Igor)"""
        if not self.owner_chat_id:
            logger.warning("Owner chat ID not configured")
            return {}
        
        return await self.send_message(
            chat_id=self.owner_chat_id,
            text=text,
            parse_mode=parse_mode,
        )
    
    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """
        Set webhook for receiving updates
        
        Args:
            webhook_url: Public URL for webhook
            
        Returns:
            API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/setWebhook",
                    json={
                        "url": webhook_url,
                        "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info("Webhook configured", url=webhook_url)
                return result
                
        except Exception as e:
            logger.error("Failed to set webhook", exc_info=e)
            raise
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook configuration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/getWebhookInfo",
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error("Failed to get webhook info", exc_info=e)
            raise
    
    async def process_update(self, update: Dict[str, Any]) -> Optional[Dict]:
        """
        Process incoming update from Telegram
        
        Args:
            update: Telegram update object
            
        Returns:
            Processing result
        """
        try:
            # Extract message
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            
            if not chat_id or not text:
                logger.warning("Invalid update received", update=update)
                return None
            
            logger.info(
                "Processing Telegram message",
                chat_id=chat_id,
                text_preview=text[:50],
            )
            
            # TODO: Route to assistant processing
            # For now, echo back
            await self.send_message(
                chat_id=str(chat_id),
                text=f"Received: {text}",
            )
            
            return {"status": "processed", "chat_id": chat_id}
            
        except Exception as e:
            logger.error("Failed to process update", exc_info=e)
            raise


# Global service instance
telegram_service = TelegramService()
