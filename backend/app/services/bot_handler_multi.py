"""
Multi-User Telegram Bot Handler with Onboarding
Suporta múltiplos usuários com quiz inicial personalizado
"""

from telegram import Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
import structlog
from app.core.config import settings
from app.services.gemini_service import GeminiService
from app.services.inbox_service import InboxService
from app.services.onboarding_service import OnboardingService
from supabase import create_client

logger = structlog.get_logger()


class MultiUserBotHandler:
    """Handler multi-user para bot do Telegram"""
    
    def __init__(self):
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        self.gemini = GeminiService()
        self.inbox_service = InboxService(self.supabase)
        self.onboarding_service = OnboardingService(self.supabase)
    
    def _ensure_user_exists(self, telegram_user) -> tuple:
        """
        Garante que usuário existe no banco.
        Retorna (user_id, is_new_user)
        """
        try:
            # Buscar por chat_id do Telegram
            chat_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", telegram_user.id)\
                .execute()
            
            if chat_result.data:
                return chat_result.data[0]["user_id"], False
            
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
        Retorna True se ainda está em onboarding, False se completou.
        """
        try:
            status = self.onboarding_service.check_onboarding_status(user_id)
            
            if status["completed"]:
                return False
            
            # Se acabou de começar conversa, iniciar onboarding
            if status["current_step"] == 0 and not update.message.text.startswith("/"):
                welcome_msg = (
                    "👋 *Bem-vindo ao TB Personal OS!*\n\n"
                    "Antes de começarmos, vou fazer algumas perguntas rápidas "
                    "para personalizar sua experiência.\n\n"
                    "_São apenas 7 perguntas que levam ~2 minutos._\n\n"
                    "Vamos lá? 🚀"
                )
                update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
                time.sleep(1)
            
            # Pegar próxima pergunta
            next_question = self.onboarding_service.get_next_question(user_id)
            
            if not next_question:
                # Onboarding completo
                return self._complete_onboarding(update, user_id)
            
            # Se não é primeira pergunta, processar resposta anterior
            if status["current_step"] > 0 and not update.message.text.startswith("/"):
                prev_question = self.onboarding_service.QUIZ_QUESTIONS[status["current_step"] - 1]
                answer = self.onboarding_service.parse_answer(prev_question, update.message.text)
                
                if "error" in answer:
                    update.message.reply_text(
                        f"⚠️ {answer['error']}\n\n"
                        "Por favor, tente novamente.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # Re-enviar pergunta
                    question_msg = self.onboarding_service.format_question_message(prev_question)
                    update.message.reply_text(question_msg, parse_mode=ParseMode.MARKDOWN)
                    return True
                
                # Salvar resposta
                self.onboarding_service.save_answer(user_id, prev_question["id"], answer)
                
                # Confirmar
                update.message.reply_text("✓", parse_mode=ParseMode.MARKDOWN)
                time.sleep(0.3)
                
                # Buscar próxima pergunta (pode ter mudado)
                next_question = self.onboarding_service.get_next_question(user_id)
                
                if not next_question:
                    return self._complete_onboarding(update, user_id)
            
            # Enviar próxima pergunta
            question_msg = self.onboarding_service.format_question_message(next_question)
            update.message.reply_text(question_msg, parse_mode=ParseMode.MARKDOWN)
            
            return True
            
        except Exception as e:
            logger.error("onboarding_handle_failed", error=str(e))
            update.message.reply_text(
                "❌ Erro no onboarding. Tente novamente com /start"
            )
            return True
    
    def _complete_onboarding(self, update: Update, user_id: str) -> bool:
        """Finaliza onboarding e dá boas-vindas."""
        try:
            result = self.onboarding_service.complete_onboarding(user_id)
            
            if not result["success"]:
                raise Exception(result.get("error", "Unknown error"))
            
            # Buscar nome do usuário
            profile = self.supabase.table("profiles")\
                .select("quiz_answers")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            user_name = profile.data.get("quiz_answers", {}).get("question_7", {}).get("value", "")
            
            greeting = f"Olá {user_name}! " if user_name else "Olá! "
            
            completion_msg = (
                f"🎉 *Onboarding Completo!*\n\n"
                f"{greeting}Seu assistente está configurado e pronto.\n\n"
                f"*O que posso fazer:*\n"
                f"• 💬 Conversar naturalmente\n"
                f"• 📝 Gerenciar tarefas e notas\n"
                f"• 📅 Organizar sua agenda\n"
                f"• 🎯 Acompanhar seus objetivos\n"
                f"• 🤖 E muito mais!\n\n"
                f"_Envie qualquer mensagem para começar._\n"
                f"_Use /help para ver todos os comandos._"
            )
            
            update.message.reply_text(completion_msg, parse_mode=ParseMode.MARKDOWN)
            
            logger.info("onboarding_completed", user_id=user_id)
            return False
            
        except Exception as e:
            logger.error("onboarding_completion_failed", error=str(e))
            update.message.reply_text(
                "❌ Erro ao finalizar onboarding. Contate o suporte."
            )
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
                # Usuário existente
                status = self.onboarding_service.check_onboarding_status(user_id)
                
                if not status["completed"]:
                    # Onboarding incompleto - continuar
                    update.message.reply_text(
                        "👋 Bem-vindo de volta!\n\n"
                        "Vamos continuar seu onboarding de onde paramos...",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    self._handle_onboarding(update, context, user_id)
                else:
                    # Onboarding completo - mensagem de boas-vindas normal
                    welcome_msg = (
                        "👋 *TB Personal OS*\n\n"
                        "Seu assistente pessoal está ativo!\n\n"
                        "*Como posso ajudar hoje?*\n"
                        "• Envie qualquer mensagem\n"
                        "• Use /help para comandos\n\n"
                        "Vamos lá! 🚀"
                    )
                    update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error("start_command_failed", error=str(e))
            update.message.reply_text(
                "❌ Erro ao iniciar. Tente novamente."
            )
    
    def help_command(self, update: Update, context: CallbackContext):
        """Handler para /help"""
        help_text = (
            "📖 *Comandos Disponíveis*\n\n"
            "*Básicos:*\n"
            "• /start - Iniciar bot\n"
            "• /help - Este menu\n"
            "• /config - Minhas configurações\n\n"
            "*Inbox & Tarefas:*\n"
            "• /inbox - Ver items pendentes\n"
            "• /tasks - Ver tarefas\n"
            "• /done - Concluir tarefa\n\n"
            "*Check-ins:*\n"
            "• /checkin - Check-in diário\n"
            "• /energy [1-10] - Registrar energia\n"
            "• /mood [texto] - Registrar humor\n\n"
            "*Relatórios:*\n"
            "• /summary - Resumo do dia\n"
            "• /week - Resumo semanal\n\n"
            "*Conversa Livre:*\n"
            "Envie qualquer mensagem e eu:\n"
            "• Processo com IA\n"
            "• Classifico automaticamente\n"
            "• Salvo na inbox\n"
            "• Respondo inteligentemente"
        )
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def config_command(self, update: Update, context: CallbackContext):
        """Mostra configurações do usuário."""
        try:
            user_id, _ = self._ensure_user_exists(update.effective_user)
            
            profile = self.supabase.table("profiles")\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            data = profile.data
            personality = data.get("personality_profile", {})
            
            config_msg = (
                "⚙️ *Suas Configurações*\n\n"
                f"*Nome:* {data.get('full_name', 'Não definido')}\n"
                f"*Objetivo:* {personality.get('main_goal', 'Múltiplos')}\n"
                f"*Estilo:* {personality.get('communication_style', 'Amigável')}\n"
                f"*Autonomia:* {data.get('autonomy_level', 'confirm')}\n"
                f"*API Key própria:* {'✓ Sim' if data.get('gemini_api_key') else '✗ Não'}\n\n"
                f"_Use /reset para refazer onboarding_"
            )
            
            update.message.reply_text(config_msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("config_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar configurações.")
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handler principal para mensagens de texto."""
        telegram_user = update.effective_user
        message_text = update.message.text
        
        try:
            # Garantir que usuário existe
            user_id, is_new = self._ensure_user_exists(telegram_user)
            
            # Verificar onboarding
            in_onboarding = self._handle_onboarding(update, context, user_id)
            
            if in_onboarding:
                return  # Ainda em onboarding, não processar como mensagem normal
            
            logger.info(
                "message_received",
                user_id=user_id,
                message_length=len(message_text)
            )
            
            # Processar mensagem com Gemini (versão simplificada)
            ai_response = self.gemini.generate_text_sync(
                f"Você é um assistente pessoal amigável. Responda naturalmente:\n\n{message_text}"
            )
            
            # Enviar resposta
            update.message.reply_text(ai_response)
            
            logger.info("message_processed", user_id=user_id)
            
        except Exception as e:
            logger.error("message_handling_failed", error=str(e))
            update.message.reply_text(
                "❌ Erro ao processar mensagem.\n\n"
                "_Tente novamente em alguns segundos._"
            )
    
    def create_updater(self) -> Updater:
        """Cria e configura updater do bot."""
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
        
        logger.info("multi_user_bot_configured")
        return updater

# Instância global
bot_handler = MultiUserBotHandler()
