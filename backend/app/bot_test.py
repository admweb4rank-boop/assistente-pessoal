"""
TB Personal OS - Telegram Bot ULTRA Simple (Sem Supabase)
Apenas testa conexão com Telegram
"""

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import structlog
from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


class SimpleTelegramBot:
    """Bot simplificado apenas para teste"""
    
    def __init__(self):
        self.owner_chat_id = int(settings.OWNER_TELEGRAM_CHAT_ID)
    
    def start_command(self, update: Update, context: CallbackContext):
        """Handler para /start"""
        user = update.effective_user
        logger.info("start_received", user_id=user.id, username=user.username)
        
        if user.id != self.owner_chat_id:
            update.message.reply_text("⛔️ Bot privado.")
            return
        
        update.message.reply_text(
            "🤖 *TB Personal OS - Teste*\n\n"
            "Bot funcionando! ✅\n\n"
            "Envie qualquer mensagem para testar.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handler para mensagens"""
        user = update.effective_user
        message_text = update.message.text
        
        if user.id != self.owner_chat_id:
            return
        
        logger.info("message_received", user_id=user.id, length=len(message_text))
        
        # Resposta simples
        response = (
            f"✅ *Mensagem recebida!*\n\n"
            f"📝 Você enviou: {message_text[:50]}...\n"
            f"📊 Tamanho: {len(message_text)} caracteres\n\n"
            f"_Bot funcionando perfeitamente!_"
        )
        
        update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        logger.info("response_sent", user_id=user.id)
    
    def create_updater(self):
        """Cria updater"""
        updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        logger.info("bot_configured")
        return updater


def main():
    """Main"""
    logger.info("🤖 Starting SIMPLE Telegram Bot...")
    
    bot = SimpleTelegramBot()
    updater = bot.create_updater()
    
    logger.info("✅ Bot started - Polling...")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == "__main__":
    main()
