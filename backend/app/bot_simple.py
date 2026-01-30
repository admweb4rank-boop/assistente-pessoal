"""
TB Personal OS - Bot Runner (Simple)
Executa o bot do Telegram em polling mode
"""

import structlog
from app.services.bot_handler_simple import bot_handler
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


def main():
    """Função principal do bot"""
    logger.info("🤖 Starting Telegram Bot...")
    
    # Criar updater
    updater = bot_handler.create_updater()
    
    logger.info("✅ Bot started - Polling for updates...")
    
    # Iniciar polling
    updater.start_polling(drop_pending_updates=True)
    
    # Manter rodando
    updater.idle()


if __name__ == "__main__":
    main()
