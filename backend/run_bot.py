"""
TB Personal OS - Bot Runner
Executa o bot do Telegram em modo polling
"""

import sys
import signal
import structlog

# Setup path
sys.path.insert(0, '/var/www/producao/assistente_igor/backend')

from app.core.logging_config import setup_logging
from app.services.bot_handler_unified import bot_handler

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)


def signal_handler(signum, frame):
    """Handler para sinais de interrupção."""
    logger.info("shutdown_signal_received", signal=signum)
    bot_handler.stop()
    sys.exit(0)


def main():
    """Função principal."""
    # Registrar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("🤖 TB Personal OS - Telegram Bot")
    logger.info("=" * 50)
    
    try:
        # Iniciar bot
        bot_handler.start_polling()
    except Exception as e:
        logger.error("bot_startup_failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
