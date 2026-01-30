"""
TB Personal OS - Multi-User Bot (v13 Compatible)
Bot com onboarding personalizado para múltiplos usuários
"""

import structlog
from app.services.bot_handler_multi_v13 import bot_handler_multi
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


def main():
    """Runner do bot multi-user"""
    logger.info("🤖 Starting Multi-User Bot (v13)...")
    
    # Criar updater
    updater = bot_handler_multi.create_updater()
    
    logger.info("✅ Multi-User Bot started - Polling...")
    
    # Iniciar polling
    updater.start_polling(
        drop_pending_updates=True
    )
    
    # Manter rodando
    updater.idle()


if __name__ == "__main__":
    main()
