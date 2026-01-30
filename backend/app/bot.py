"""
TB Personal OS - Bot Runner
Executa o bot do Telegram em polling mode
"""

import asyncio
import structlog
from app.services.bot_handler import bot_handler
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


async def main():
    """Função principal do bot"""
    logger.info("🤖 Starting Telegram Bot...")
    
    # Criar aplicação
    application = bot_handler.create_application()
    
    # Inicializar
    await application.initialize()
    await application.start()
    
    logger.info("✅ Bot started successfully - Polling for updates...")
    
    # Iniciar polling
    await application.updater.start_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )
    
    # Manter rodando
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("⏹ Stopping bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("👋 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
