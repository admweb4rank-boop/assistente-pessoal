"""
TB Personal OS - Multi-User Bot Runner
Bot com suporte a múltiplos usuários e onboarding personalizado
Compatible with python-telegram-bot v13.x
"""

import structlog
from app.services.bot_handler_multi import bot_handler
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


def main():
    """Função principal do bot multi-user"""
    logger.info("🤖 Starting Multi-User Telegram Bot...")
    
    # Criar updater
    updater = bot_handler.create_updater()
    
    logger.info("✅ Multi-User Bot started - Polling for updates...")
    
    # Iniciar polling (blocking call)
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == "__main__":
    main()
