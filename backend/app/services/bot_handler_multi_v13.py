"""
Multi-User Bot Handler - v13 Compatible (python-telegram-bot 13.x)
Versão simplificada e síncrona para compatibilidade
"""

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import structlog
from app.core.config import settings
from app.services.gemini_service import GeminiService
from app.services.onboarding_service import OnboardingService
from app.services.conversation_service import ConversationService
from supabase import create_client
from typing import Tuple

logger = structlog.get_logger()


class MultiUserBotHandlerV13:
    """Handler multi-user compatível com python-telegram-bot v13"""
    
    def __init__(self):
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        self.gemini = GeminiService()
        self.onboarding_service = OnboardingService(self.supabase)
        self.conversation_service = ConversationService()  # Não recebe args
        
        # Cache de usuários em onboarding (user_id -> step)
        self.onboarding_cache = {}
    
    def _ensure_user_exists(self, telegram_user) -> Tuple[str, bool]:
        """
        Garante que usuário existe no banco.
        Retorna (user_id, is_new_user)
        """
        try:
            # Buscar por telegram_chat_id
            user_result = self.supabase.table("users")\
                .select("id")\
                .eq("telegram_chat_id", str(telegram_user.id))\
                .execute()
            
            if user_result.data:
                return user_result.data[0]["id"], False
            
            # Usuário novo - criar
            new_user = self.supabase.table("users").insert({
                "telegram_chat_id": str(telegram_user.id),
                "telegram_username": telegram_user.username,
                "full_name": f"{telegram_user.first_name or ''} {telegram_user.last_name or ''}".strip() or "Usuário",
                "is_active": True
            }).execute()
            
            user_id = new_user.data[0]["id"]
            
            # Criar profile
            self.supabase.table("profiles").insert({
                "user_id": user_id,
                "timezone": "America/Sao_Paulo",
                "language": "pt-BR",
                "onboarding_completed": False,
                "onboarding_step": 0,
                "quiz_answers": {},
                "personality_profile": {},
                "autonomy_level": "confirm"
            }).execute()
            
            logger.info(
                "new_user_created",
                user_id=user_id,
                telegram_id=telegram_user.id,
                username=telegram_user.username
            )
            
            return user_id, True
            
        except Exception as e:
            logger.error("ensure_user_failed", error=str(e))
            raise
    
    def _handle_onboarding(
        self,
        update: Update,
        context: CallbackContext,
        user_id: str
    ) -> bool:
        """
        Gerencia fluxo de onboarding.
        Retorna True se ainda está em onboarding.
        """
        try:
            status = self.onboarding_service.check_onboarding_status(user_id)
            
            if status["completed"]:
                return False
            
            # Se acabou de começar, dar boas-vindas
            if status["current_step"] == 0 and user_id not in self.onboarding_cache:
                welcome_msg = (
                    "👋 *Bem-vindo ao TB Personal OS!*\n\n"
                    "Antes de começarmos, farei algumas perguntas rápidas "
                    "para personalizar sua experiência.\n\n"
                    "_São apenas 7 perguntas (~2 minutos)._\n\n"
                    "Vamos lá? 🚀"
                )
                update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
                self.onboarding_cache[user_id] = 0
                
                # Enviar primeira pergunta
                next_question = self.onboarding_service.get_next_question(user_id)
                if next_question:
                    question_msg = self.onboarding_service.format_question_message(next_question)
                    update.message.reply_text(question_msg, parse_mode=ParseMode.MARKDOWN)
                
                return True
            
            # Processar resposta da pergunta anterior
            if status["current_step"] > 0 and not update.message.text.startswith("/"):
                prev_question = self.onboarding_service.QUIZ_QUESTIONS[status["current_step"] - 1]
                answer = self.onboarding_service.parse_answer(prev_question, update.message.text)
                
                if "error" in answer:
                    update.message.reply_text(
                        f"⚠️ {answer['error']}\n\nPor favor, tente novamente.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # Re-enviar pergunta
                    question_msg = self.onboarding_service.format_question_message(prev_question)
                    update.message.reply_text(question_msg, parse_mode=ParseMode.MARKDOWN)
                    return True
                
                # Salvar resposta
                self.onboarding_service.save_answer(user_id, prev_question["id"], answer)
                update.message.reply_text("✓")
            
            # Buscar próxima pergunta
            next_question = self.onboarding_service.get_next_question(user_id)
            
            if not next_question:
                # Onboarding completo
                result = self.onboarding_service.complete_onboarding(user_id)
                
                if result["success"]:
                    # Buscar nome
                    profile = self.supabase.table("profiles")\
                        .select("quiz_answers")\
                        .eq("user_id", user_id)\
                        .single()\
                        .execute()
                    
                    user_name = profile.data.get("quiz_answers", {}).get("question_7", {}).get("value", "")
                    greeting = f"Olá {user_name}! " if user_name else "Olá! "
                    
                    completion_msg = (
                        f"🎉 *Onboarding Completo!*\n\n"
                        f"{greeting}Seu assistente está configurado.\n\n"
                        f"*Posso ajudar com:*\n"
                        f"• 💬 Conversas naturais\n"
                        f"• 📝 Tarefas e notas\n"
                        f"• 📅 Organização\n"
                        f"• 🎯 Metas e objetivos\n\n"
                        f"_Envie qualquer mensagem para começar._"
                    )
                    
                    update.message.reply_text(completion_msg, parse_mode=ParseMode.MARKDOWN)
                    
                    # Remover do cache
                    if user_id in self.onboarding_cache:
                        del self.onboarding_cache[user_id]
                    
                    logger.info("onboarding_completed", user_id=user_id)
                    return False
                else:
                    update.message.reply_text("❌ Erro ao finalizar onboarding.")
                    return True
            
            # Enviar próxima pergunta
            question_msg = self.onboarding_service.format_question_message(next_question)
            update.message.reply_text(question_msg, parse_mode=ParseMode.MARKDOWN)
            
            return True
            
        except Exception as e:
            logger.error("onboarding_handle_failed", error=str(e), user_id=user_id)
            update.message.reply_text("❌ Erro no onboarding. Use /start novamente.")
            return True
    
    def start_command(self, update: Update, context: CallbackContext):
        """Handler para /start"""
        telegram_user = update.effective_user
        
        try:
            user_id, is_new = self._ensure_user_exists(telegram_user)
            
            if is_new:
                # Novo usuário - iniciar onboarding
                self._handle_onboarding(update, context, user_id)
            else:
                # Verificar se completou onboarding
                status = self.onboarding_service.check_onboarding_status(user_id)
                
                if not status["completed"]:
                    # Continuar onboarding
                    update.message.reply_text(
                        "👋 Bem-vindo de volta!\n\n"
                        "Vamos continuar seu onboarding...",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    self._handle_onboarding(update, context, user_id)
                else:
                    # Já completou
                    welcome_msg = (
                        "👋 *TB Personal OS*\n\n"
                        "Seu assistente está ativo!\n\n"
                        "Como posso ajudar? 🚀\n\n"
                        "_Use /help para ver comandos_"
                    )
                    update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error("start_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao iniciar.")
    
    def help_command(self, update: Update, context: CallbackContext):
        """Handler para /help"""
        help_text = (
            "📖 *Comandos*\n\n"
            "*Básicos:*\n"
            "• /start - Iniciar\n"
            "• /help - Ajuda\n"
            "• /config - Configurações\n\n"
            "*Conversa Livre:*\n"
            "Envie qualquer mensagem:\n"
            "• Processo com IA\n"
            "• Salvo automaticamente\n"
            "• Respondo inteligentemente"
        )
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def config_command(self, update: Update, context: CallbackContext):
        """Mostra configurações."""
        try:
            user_id, _ = self._ensure_user_exists(update.effective_user)
            
            profile = self.supabase.table("profiles")\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            data = profile.data
            personality = data.get("personality_profile", {})
            
            # Buscar nome do users
            user = self.supabase.table("users")\
                .select("full_name")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            config_msg = (
                "⚙️ *Configurações*\n\n"
                f"*Nome:* {user.data.get('full_name', 'Não definido')}\n"
                f"*Objetivo:* {personality.get('main_goal', '-')}\n"
                f"*Estilo:* {personality.get('communication_style', '-')}\n"
                f"*Autonomia:* {data.get('autonomy_level', 'confirm')}\n"
                f"*API própria:* {'✓' if data.get('gemini_api_key') else '✗'}\n"
            )
            
            update.message.reply_text(config_msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("config_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar configurações.")
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handler principal para mensagens."""
        telegram_user = update.effective_user
        message_text = update.message.text
        
        try:
            # Garantir usuário existe
            user_id, is_new = self._ensure_user_exists(telegram_user)
            
            # Verificar onboarding
            in_onboarding = self._handle_onboarding(update, context, user_id)
            
            if in_onboarding:
                return
            
            logger.info(
                "message_received",
                user_id=user_id,
                length=len(message_text)
            )
            
            # Processar com conversation service (síncrono)
            response = self.conversation_service.process_message_sync(
                user_id=user_id,
                message=message_text,
                message_type="telegram"
            )
            
            # Enviar resposta
            update.message.reply_text(
                response["reply"],
                parse_mode=ParseMode.MARKDOWN if response.get("parse_mode") == "markdown" else None
            )
            
            logger.info(
                "message_processed",
                user_id=user_id,
                action=response.get("action")
            )
            
        except Exception as e:
            logger.error("message_handling_failed", error=str(e))
            update.message.reply_text(
                "❌ Erro ao processar.\n\n_Tente novamente._"
            )
    
    def create_updater(self) -> Updater:
        """Cria Updater do bot (v13)."""
        updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
        
        dp = updater.dispatcher
        
        # Comandos
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("config", self.config_command))
        
        # Mensagens de texto
        dp.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.handle_message)
        )
        
        logger.info("multi_user_bot_v13_configured")
        return updater


# Instância global
bot_handler_multi = MultiUserBotHandlerV13()
