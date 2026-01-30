"""
TB Personal OS - Telegram Bot Handler
Processa mensagens e comandos do Telegram (python-telegram-bot v13.x)
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
from supabase import create_client

logger = structlog.get_logger()


class TelegramBotHandler:
    """Handler para bot do Telegram"""
    
    def __init__(self):
        self.gemini = GeminiService()
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        self.inbox_service = InboxService(self.supabase)
        self.owner_chat_id = int(settings.OWNER_TELEGRAM_CHAT_ID)
    
    def start_command(self, update: Update, context: CallbackContext):
        """Handler para /start"""
        user = update.effective_user
        
        logger.info(
            "telegram_start",
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        # Verificar se é o owner
        if user.id != self.owner_chat_id:
            await update.message.reply_text(
                "⛔️ Este bot é privado.\n"
                "Apenas o proprietário pode utilizá-lo."
            )
            return
        
        welcome_message = (
            "🤖 *TB Personal OS*\n\n"
            "Olá Igor! Seu assistente pessoal está pronto.\n\n"
            "*Comandos disponíveis:*\n"
            "• /help - Ver todos os comandos\n"
            "• /inbox - Ver items da inbox\n"
            "• /tasks - Ver tarefas pendentes\n\n"
            "*Como usar:*\n"
            "• Envie qualquer mensagem e eu vou processar\n"
            "• Ideias, tarefas, notas - tudo vai para sua inbox\n"
            "• Faça perguntas e eu respondo com IA\n\n"
            "Vamos começar? 🚀"
        )
        
        update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def help_command(self, update: Update, context: CallbackContext):
        """Handler para /help"""
        help_text = (
            "📖 *Comandos Disponíveis*\n\n"
            "*Inbox & Tarefas:*\n"
            "• /inbox - Ver items na inbox\n"
            "• /tasks - Ver tarefas pendentes\n"
            "• /done - Marcar última tarefa como concluída\n\n"
            "*Hábitos & Check-ins:*\n"
            "• /checkin - Fazer check-in diário\n"
            "• /energy [1-10] - Registrar energia\n"
            "• /mood [texto] - Registrar humor\n\n"
            "*Conteúdo:*\n"
            "• /ideas - Ver ideias de conteúdo\n"
            "• /post - Criar post\n\n"
            "*Análises:*\n"
            "• /summary - Resumo do dia\n"
            "• /week - Resumo da semana\n\n"
            "*Envio Livre:*\n"
            "Envie qualquer texto e eu processo com IA:\n"
            "• Capturo como item da inbox\n"
            "• Classifico automaticamente\n"
            "• Sugiro ações\n"
            "• Respondo perguntas"
        )
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def inbox_command(self, update: Update, context: CallbackContext):
        """Handler para /inbox - mostra items recentes"""
        # Versão síncrona simplificada para v13
        try:
            update.message.reply_text(
                "📥 *Inbox*\n\n"
                "Este comando listará seus items pendentes.\n"
                "_Feature em desenvolvimento..._",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error("inbox_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar inbox.")
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handler para mensagens de texto normais"""
        user = update.effective_user
        message_text = update.message.text
        
        # Verificar se é o owner
        if user.id != self.owner_chat_id:
            return
        
        logger.info(
            "telegram_message_received",
            user_id=user.id,
            message_length=len(message_text)
        )
        
        try:
            # Processar com Gemini AI
            ai_prompt = f"""Você é um assistente pessoal. Analise esta mensagem do usuário:

"{message_text}"

Determine:
1. É uma tarefa, ideia, nota ou pergunta?
2. Qual a categoria? (personal, work, health, content, finance, other)
3. Qual a prioridade? (low, medium, high, urgent)
4. Precisa resposta ou apenas salvar?

Responda em JSON:
{{
    "type": "task|idea|note|question",
    "category": "categoria",
    "priority": "prioridade",
    "needs_response": true/false,
    "suggested_action": "descrição da ação",
    "response": "resposta ao usuário (se needs_response=true)"
}}"""
            
            ai_response = await self.gemini.generate_text(ai_prompt)
            
            # Parse da resposta (simplificado - em produção usar extract_structured_data)
            import json
            analysis = {}
            try:
                # Tentar extrair JSON da resposta
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    analysis = json.loads(ai_response[json_start:json_end])
            except:
                # Fallback se não conseguir parsear
                analysis = {
                    "type": "note",
                    "category": "other",
                    "priority": "medium",
                    "needs_response": False,
                    "suggested_action": "Salvar na inbox"
                }
            
            # Salvar na inbox
            # Buscar user_id pelo chat_id
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            # Se não encontrar, criar usuário automaticamente
            if not user_result.data:
                # Criar usuário
                new_user = self.supabase.table("users").insert({
                    "email": f"telegram_{user.id}@tbpersonal.os",
                    "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip()
                }).execute()
                
                user_id = new_user.data[0]["id"]
                
                # Criar profile
                self.supabase.table("profiles").insert({
                    "user_id": user_id,
                    "timezone": "America/Sao_Paulo",
                    "language": "pt-BR"
                }).execute()
                
                # Criar telegram chat
                self.supabase.table("telegram_chats").insert({
                    "user_id": user_id,
                    "chat_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }).execute()
                
                logger.info("user_created_from_telegram", user_id=user_id, telegram_id=user.id)
            else:
                user_id = user_result.data[0]["user_id"]
            
            inbox_item = await self.inbox_service.create_inbox_item(
                user_id=user_id,
                content=message_text,
                source="telegram",
                category=analysis.get("category", "other"),
                tags=[analysis.get("type", "note")],
                source_metadata={
                    "telegram_user_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name
                },
                suggested_actions=analysis
            )
            
            # Responder ao usuário
            if analysis.get("needs_response") and analysis.get("response"):
                response = analysis["response"]
            else:
                response = (
                    f"✅ *Salvo na Inbox*\n\n"
                    f"📌 Tipo: {analysis.get('type', 'note').title()}\n"
                    f"🏷 Categoria: {analysis.get('category', 'other').title()}\n"
                    f"⚡️ Prioridade: {analysis.get('priority', 'medium').title()}\n\n"
                    f"_Item #{inbox_item['id'][:8]}..._"
                )
            
            await update.message.reply_text(response, parse_mode="Markdown")
            
            logger.info(
                "message_processed",
                item_id=inbox_item["id"],
                type=analysis.get("type"),
                category=analysis.get("category")
            )
            
        except Exception as e:
            logger.error("message_processing_failed", error=str(e))
            await update.message.reply_text(
                "❌ Erro ao processar mensagem. Tente novamente.\n\n"
                f"_Erro: {str(e)[:100]}_",
                parse_mode="Markdown"
            )
    
    def create_application(self) -> Application:
        """Cria e configura a aplicação do bot"""
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Comandos
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("inbox", self.inbox_command))
        
        # Mensagens de texto
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        logger.info("telegram_bot_configured")
        return application


# Instância global do bot
bot_handler = TelegramBotHandler()
