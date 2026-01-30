"""
TB Personal OS - Telegram Bot Handler (Simplified for v13.x)
Processa mensagens e comandos do Telegram
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
from datetime import datetime
import asyncio
from app.core.config import settings
from supabase import create_client
from app.services.mode_service import mode_service
from app.services.finance_service import finance_service
from app.services.goal_service import goal_service, GoalLevel, GoalPeriod, GoalArea
from app.jobs.monthly_report import monthly_report_job
from app.services.audio_service import audio_service
from app.services.report_service import report_service, ReportType
from app.services.conversation_service import conversation_service
from app.services.context_service import context_service, MemoryCategory
from app.services.pattern_learning_service import pattern_learning_service
import json

logger = structlog.get_logger()


class TelegramBotHandler:
    """Handler simplificado para bot do Telegram"""
    
    def __init__(self):
        self._supabase = None
        self.owner_chat_id = int(settings.OWNER_TELEGRAM_CHAT_ID)
    
    @property
    def supabase(self):
        """Lazy load do Supabase client"""
        if self._supabase is None:
            try:
                self._supabase = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                logger.info("supabase_connected")
            except Exception as e:
                logger.error("supabase_connection_failed", error=str(e))
                raise
        return self._supabase
    
    def start_command(self, update: Update, context: CallbackContext):
        """Handler para /start"""
        user = update.effective_user
        
        logger.info("telegram_start", user_id=user.id, username=user.username)
        
        # Verificar se é o owner
        if user.id != self.owner_chat_id:
            update.message.reply_text(
                "⛔️ Este bot é privado.\n"
                "Apenas o proprietário pode utilizá-lo."
            )
            return
        
        # Verificar/criar usuário
        try:
            user_check = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_check.data:
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
                
                logger.info("user_created", user_id=user_id)
        except Exception as e:
            logger.error("user_creation_failed", error=str(e))
        
        welcome_message = (
            "🤖 *TB Personal OS*\n\n"
            "Olá Igor! Seu assistente pessoal está pronto.\n\n"
            "*Comandos disponíveis:*\n"
            "• /help - Ver todos os comandos\n"
            "• /inbox - Ver items da inbox\n\n"
            "*Como usar:*\n"
            "• Envie qualquer mensagem e eu vou processar\n"
            "• Ideias, tarefas, notas - tudo vai para sua inbox\n\n"
            "Vamos começar? 🚀"
        )
        
        update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    def help_command(self, update: Update, context: CallbackContext):
        """Handler para /help"""
        help_text = (
            "📖 *Comandos Disponíveis*\n\n"
            "*Inbox & Tarefas:*\n"
            "• /inbox - Ver items na inbox\n"
            "• /tasks - Ver tarefas pendentes\n\n"
            "*Modos do Assistente:*\n"
            "• /modo - Ver modo atual\n"
            "• /modos - Listar todos os modos\n\n"
            "*Finanças:*\n"
            "• /financas - Resumo financeiro\n"
            "• /gasto [valor] [desc] - Registrar despesa\n"
            "• /receita [valor] [desc] - Registrar receita\n\n"
            "*Objetivos:*\n"
            "• /objetivo - Ver resumo de objetivos\n"
            "• /objetivos - Listar objetivos ativos\n\n"
            "*Memória & Contexto:*\n"
            "• /lembrar [info] - Salvar informação\n"
            "• /memorias - Ver memórias salvas\n"
            "• /aprender - Analisar padrões\n\n"
            "*Relatórios:*\n"
            "• /relatorio - Relatório mensal\n"
            "• /relatorio semanal/trimestral/anual\n\n"
            "*Conversa Livre:*\n"
            "Envie texto ou áudio e eu respondo! 🤖"
        )
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def inbox_command(self, update: Update, context: CallbackContext):
        """Handler para /inbox"""
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", update.effective_user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            items = self.supabase.table("inbox_items")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "new")\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if not items.data:
                update.message.reply_text(
                    "📥 *Inbox vazia*\n\nNenhum item pendente! ✅",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📥 *Items na Inbox*\n\n"
            
            for idx, item in enumerate(items.data, 1):
                category_emoji = {
                    "personal": "👤", "work": "💼", "health": "🏃",
                    "content": "📝", "finance": "💰", "other": "📌"
                }.get(item.get("category", "other"), "📌")
                
                content = item["content"][:50]
                if len(item["content"]) > 50:
                    content += "..."
                
                message += f"{idx}. {category_emoji} {content}\n"
            
            message += f"\n_Total: {len(items.data)} items_"
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("inbox_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar inbox.")
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handler para mensagens de texto - CONVERSA NATURAL COM IA"""
        user = update.effective_user
        message_text = update.message.text
        
        if user.id != self.owner_chat_id:
            return
        
        logger.info("message_received", user_id=user.id, length=len(message_text))
        
        try:
            # Buscar user_id
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Indicador de "digitando"
            update.message.chat.send_action("typing")
            
            # Processar mensagem com IA conversacional
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    conversation_service.process_message(
                        user_id=user_id,
                        message=message_text,
                        source="telegram"
                    )
                )
            finally:
                loop.close()
            
            # Resposta principal
            response = result.get("response", "Desculpe, não entendi.")
            
            # Adicionar ações executadas
            actions = result.get("actions", [])
            if actions:
                action_msgs = []
                for action in actions:
                    if action.get("type") == "task_created":
                        action_msgs.append(f"✅ Tarefa criada: {action.get('title', '')[:30]}")
                    elif action.get("type") == "inbox_added":
                        action_msgs.append("📥 Adicionado à inbox")
                    elif action.get("type") == "reminder_pending":
                        action_msgs.append("⏰ Lembrete registrado")
                
                if action_msgs:
                    response += "\n\n" + "\n".join(action_msgs)
            
            # Enviar resposta (dividir se muito longa)
            if len(response) > 4000:
                parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for part in parts:
                    update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            # Log
            logger.info(
                "conversation_processed",
                user_id=user_id,
                intent=result.get("intent"),
                actions_count=len(actions)
            )
            
        except Exception as e:
            logger.error("message_failed", error=str(e))
            # Fallback: salvar na inbox
            try:
                self.supabase.table("inbox_items").insert({
                    "user_id": user_id,
                    "content": message_text,
                    "content_type": "text",
                    "source": "telegram",
                    "status": "new",
                    "category": "other"
                }).execute()
                update.message.reply_text(
                    "⚠️ Processamento de IA indisponível.\n"
                    "✅ Mensagem salva na inbox."
                )
            except:
                update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
    
    def handle_audio(self, update: Update, context: CallbackContext):
        """Handler para mensagens de áudio/voz - TRANSCREVE E PROCESSA COM IA"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        logger.info("audio_received", user_id=user.id)
        
        try:
            # Pega o arquivo de áudio (voice ou audio)
            if update.message.voice:
                audio_file = update.message.voice
                audio_type = "voice"
            elif update.message.audio:
                audio_file = update.message.audio
                audio_type = "audio"
            else:
                update.message.reply_text("❌ Formato de áudio não reconhecido.")
                return
            
            # Feedback inicial
            update.message.reply_text(
                "🎙️ _Transcrevendo áudio..._",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Buscar user_id
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Transcreve o áudio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                transcription = loop.run_until_complete(
                    audio_service.transcribe_from_telegram(
                        file_id=audio_file.file_id,
                        bot_token=settings.TELEGRAM_BOT_TOKEN
                    )
                )
            finally:
                loop.close()
            
            if not transcription:
                update.message.reply_text(
                    "⚠️ Não foi possível transcrever o áudio.\n"
                    "_Áudio não processado._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Mostrar transcrição
            preview = transcription[:150]
            if len(transcription) > 150:
                preview += "..."
            
            update.message.reply_text(
                f"📝 *Transcrição:*\n_{preview}_\n\n🤖 _Processando..._",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Indicador de "digitando"
            update.message.chat.send_action("typing")
            
            # Processar texto transcrito com IA conversacional
            loop2 = asyncio.new_event_loop()
            asyncio.set_event_loop(loop2)
            try:
                result = loop2.run_until_complete(
                    conversation_service.process_message(
                        user_id=user_id,
                        message=f"[Áudio transcrito]: {transcription}",
                        source="telegram_audio"
                    )
                )
            finally:
                loop2.close()
            
            # Resposta principal
            response = result.get("response", "Desculpe, não entendi o áudio.")
            
            # Adicionar ações executadas
            actions = result.get("actions", [])
            if actions:
                action_msgs = []
                for action in actions:
                    if action.get("type") == "task_created":
                        action_msgs.append(f"✅ Tarefa criada: {action.get('title', '')[:30]}")
                    elif action.get("type") == "inbox_added":
                        action_msgs.append("📥 Adicionado à inbox")
                
                if action_msgs:
                    response += "\n\n" + "\n".join(action_msgs)
            
            # Enviar resposta
            if len(response) > 4000:
                parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for part in parts:
                    update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            logger.info(
                "audio_processed",
                user_id=user_id,
                duration=audio_file.duration,
                intent=result.get("intent")
            )
            
        except Exception as e:
            logger.error("audio_failed", error=str(e))
            update.message.reply_text(
                f"❌ Erro ao processar áudio: {str(e)[:100]}"
            )
    
    def create_updater(self) -> Updater:
        """Cria o updater do bot"""
        updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Comandos
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("inbox", self.inbox_command))
        dp.add_handler(CommandHandler("modo", self.mode_command))
        dp.add_handler(CommandHandler("modos", self.list_modes_command))
        dp.add_handler(CommandHandler("financas", self.finance_command))
        dp.add_handler(CommandHandler("gasto", self.expense_command))
        dp.add_handler(CommandHandler("receita", self.income_command))
        dp.add_handler(CommandHandler("objetivo", self.goal_command))
        dp.add_handler(CommandHandler("objetivos", self.list_goals_command))
        dp.add_handler(CommandHandler("relatorio", self.report_command))
        
        # Memory & Learning commands
        dp.add_handler(CommandHandler("lembrar", self.remember_command))
        dp.add_handler(CommandHandler("memorias", self.memories_command))
        dp.add_handler(CommandHandler("aprender", self.learn_command))
        
        # Mensagens de texto
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        # Mensagens de áudio/voz
        dp.add_handler(MessageHandler(Filters.voice | Filters.audio, self.handle_audio))
        
        logger.info("telegram_bot_configured")
        return updater
    
    def mode_command(self, update: Update, context: CallbackContext):
        """Handler para /modo [nome]"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Mapeia nomes em português para inglês
            mode_map = {
                "execucao": "execution",
                "execução": "execution",
                "conteudo": "content",
                "conteúdo": "content",
                "saude": "health",
                "saúde": "health",
                "aprendizado": "learning",
                "presenca": "presence",
                "presença": "presence",
                "padrao": "default",
                "padrão": "default"
            }
            
            # Se não passou argumento, mostra modo atual
            if not context.args:
                active_mode = mode_service.get_active_mode(user_id)
                icon = active_mode.get("icon", "🤖")
                name = active_mode.get("display_name", "Geral")
                mode_name = active_mode.get("mode_name", "default")
                
                message = (
                    f"{icon} *Modo Atual: {name}*\n\n"
                    f"Para trocar de modo:\n"
                    f"• `/modo execucao` - Produtividade\n"
                    f"• `/modo conteudo` - Conteúdo\n"
                    f"• `/modo saude` - Corpo & Energia\n"
                    f"• `/modo aprendizado` - Learning\n"
                    f"• `/modo presenca` - Presença\n"
                    f"• `/modo padrao` - Voltar ao padrão"
                )
                update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Ativar modo especificado
            requested_mode = context.args[0].lower()
            mode_name = mode_map.get(requested_mode, requested_mode)
            
            result = mode_service.activate_mode(user_id, mode_name, "telegram")
            
            if result.get("success"):
                greeting = result.get("greeting", "Modo ativado!")
                update.message.reply_text(greeting, parse_mode=ParseMode.MARKDOWN)
                logger.info("mode_activated", user_id=user_id, mode=mode_name)
            else:
                update.message.reply_text(
                    f"❌ Erro: {result.get('error', 'Modo não encontrado')}"
                )
                
        except Exception as e:
            logger.error("mode_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao processar comando de modo.")
    
    def list_modes_command(self, update: Update, context: CallbackContext):
        """Handler para /modos - lista todos os modos"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            modes = mode_service.get_available_modes()
            
            message = "🎭 *Modos Disponíveis*\n\n"
            
            for mode in modes:
                icon = mode.get("icon", "🤖")
                name = mode.get("display_name", mode["mode_name"])
                desc = mode.get("description", "")[:50]
                message += f"{icon} *{name}*\n_{desc}_\n\n"
            
            message += "_Use `/modo [nome]` para ativar_"
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("list_modes_failed", error=str(e))
            update.message.reply_text("❌ Erro ao listar modos.")
    
    # ==========================================
    # FINANCE COMMANDS
    # ==========================================
    
    def finance_command(self, update: Update, context: CallbackContext):
        """Handler para /financas - resumo financeiro"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Buscar resumo financeiro
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                summary = loop.run_until_complete(
                    finance_service.get_summary(user_id)
                )
                alerts = loop.run_until_complete(
                    finance_service.get_alerts(user_id)
                )
            finally:
                loop.close()
            
            # Formatação
            income = summary.get("total_income", 0)
            expense = summary.get("total_expense", 0)
            balance = summary.get("balance", 0)
            status_emoji = "🟢" if balance >= 0 else "🔴"
            
            message = (
                f"💰 *Resumo Financeiro*\n"
                f"_{summary.get('period', {}).get('start_date', '')} a {summary.get('period', {}).get('end_date', '')}_\n\n"
                f"📈 Receitas: R$ {income:,.2f}\n"
                f"📉 Despesas: R$ {expense:,.2f}\n"
                f"{status_emoji} Saldo: R$ {balance:,.2f}\n\n"
            )
            
            # Alertas
            if alerts:
                message += "*⚠️ Alertas:*\n"
                for alert in alerts[:3]:
                    message += f"• {alert.get('title', '')}\n"
            
            message += "\n_Comandos:_\n"
            message += "`/gasto 50 Almoço` - Registrar despesa\n"
            message += "`/receita 1000 Freelance` - Registrar receita"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            logger.info("finance_summary_sent", user_id=user_id)
            
        except Exception as e:
            logger.error("finance_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar dados financeiros.")
    
    def expense_command(self, update: Update, context: CallbackContext):
        """Handler para /gasto [valor] [descrição]"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            if len(context.args) < 2:
                update.message.reply_text(
                    "📝 *Uso:* `/gasto [valor] [descrição]`\n"
                    "Exemplo: `/gasto 50 Almoço restaurante`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Extrair valor e descrição
            try:
                amount = float(context.args[0].replace(",", "."))
            except ValueError:
                update.message.reply_text("❌ Valor inválido. Use números.")
                return
            
            description = " ".join(context.args[1:])
            
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Criar transação
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                transaction = loop.run_until_complete(
                    finance_service.create_transaction(
                        user_id=user_id,
                        transaction_type="expense",
                        amount=amount,
                        description=description
                    )
                )
            finally:
                loop.close()
            
            if transaction:
                update.message.reply_text(
                    f"✅ *Gasto registrado!*\n\n"
                    f"💸 R$ {amount:,.2f}\n"
                    f"📝 {description}",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("expense_added", user_id=user_id, amount=amount)
            else:
                update.message.reply_text("❌ Erro ao registrar gasto.")
                
        except Exception as e:
            logger.error("expense_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao registrar gasto.")
    
    def income_command(self, update: Update, context: CallbackContext):
        """Handler para /receita [valor] [descrição]"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            if len(context.args) < 2:
                update.message.reply_text(
                    "📝 *Uso:* `/receita [valor] [descrição]`\n"
                    "Exemplo: `/receita 1500 Freelance projeto X`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Extrair valor e descrição
            try:
                amount = float(context.args[0].replace(",", "."))
            except ValueError:
                update.message.reply_text("❌ Valor inválido. Use números.")
                return
            
            description = " ".join(context.args[1:])
            
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Criar transação
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                transaction = loop.run_until_complete(
                    finance_service.create_transaction(
                        user_id=user_id,
                        transaction_type="income",
                        amount=amount,
                        description=description
                    )
                )
            finally:
                loop.close()
            
            if transaction:
                update.message.reply_text(
                    f"✅ *Receita registrada!*\n\n"
                    f"💰 R$ {amount:,.2f}\n"
                    f"📝 {description}",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("income_added", user_id=user_id, amount=amount)
            else:
                update.message.reply_text("❌ Erro ao registrar receita.")
                
        except Exception as e:
            logger.error("income_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao registrar receita.")
    
    # ==========================================
    # GOALS COMMANDS
    # ==========================================
    
    def goal_command(self, update: Update, context: CallbackContext):
        """Handler para /objetivo [titulo] - criar ou ver objetivo"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Se passou argumentos, cria novo objetivo
            if context.args:
                title = " ".join(context.args)
                
                # Detecta área pelo texto
                area = None
                area_keywords = {
                    "work": ["trabalho", "projeto", "cliente", "negócio", "empresa"],
                    "health": ["saúde", "treino", "academia", "corpo", "peso", "dieta"],
                    "finance": ["dinheiro", "receita", "faturar", "investir", "pagar"],
                    "learning": ["aprender", "estudar", "curso", "livro", "ler"],
                    "content": ["conteúdo", "post", "vídeo", "youtube", "instagram"],
                    "relationships": ["família", "amigos", "networking", "relacionamento"],
                    "personal": ["eu", "pessoal", "hábito", "rotina"]
                }
                
                for area_key, keywords in area_keywords.items():
                    if any(kw in title.lower() for kw in keywords):
                        area = GoalArea(area_key)
                        break
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    goal = loop.run_until_complete(
                        goal_service.create_goal(
                            user_id=user_id,
                            title=title,
                            level=GoalLevel.MICRO,  # Default: semanal
                            period_type=GoalPeriod.WEEK,
                            area=area
                        )
                    )
                finally:
                    loop.close()
                
                area_emoji = {
                    "work": "💼", "health": "💪", "finance": "💰",
                    "learning": "📚", "content": "✍️", 
                    "relationships": "❤️", "personal": "✨"
                }.get(area.value if area else "", "🎯")
                
                update.message.reply_text(
                    f"✅ *Objetivo criado!*\n\n"
                    f"{area_emoji} {title}\n"
                    f"📅 Período: Semana atual\n"
                    f"📊 Progresso: 0%\n\n"
                    f"_Use `/objetivos` para ver todos_",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("goal_created", user_id=user_id, title=title)
                return
            
            # Sem argumentos: mostra resumo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                summary = loop.run_until_complete(
                    goal_service.get_summary(user_id)
                )
            finally:
                loop.close()
            
            message = (
                f"🎯 *Seus Objetivos*\n\n"
                f"📊 *Total:* {summary.get('total', 0)}\n"
                f"🔵 Macro (ano): {summary.get('active_macro', 0)}\n"
                f"🟢 Meso (trimestre): {summary.get('active_meso', 0)}\n"
                f"🟡 Micro (semana): {summary.get('active_micro', 0)}\n\n"
                f"📈 Progresso médio: {summary.get('avg_progress', 0)}%\n\n"
                f"_Comandos:_\n"
                f"`/objetivo [título]` - Criar objetivo\n"
                f"`/objetivos` - Ver lista completa"
            )
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("goal_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao processar objetivos.")
    
    def list_goals_command(self, update: Update, context: CallbackContext):
        """Handler para /objetivos - lista objetivos ativos"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                current_goals = loop.run_until_complete(
                    goal_service.get_current_period_goals(user_id)
                )
            finally:
                loop.close()
            
            area_emoji = {
                "work": "💼", "health": "💪", "finance": "💰",
                "learning": "📚", "content": "✍️", 
                "relationships": "❤️", "personal": "✨"
            }
            
            message = "🎯 *Objetivos Atuais*\n\n"
            
            # Anual
            if current_goals.get("year"):
                message += "🔵 *Anuais (Macro):*\n"
                for g in current_goals["year"][:3]:
                    emoji = area_emoji.get(g.get("area", ""), "🎯")
                    progress = g.get("progress_percentage", 0)
                    message += f"  {emoji} {g['title']} ({progress}%)\n"
                message += "\n"
            
            # Trimestral  
            if current_goals.get("quarter"):
                message += "🟢 *Trimestrais (Meso):*\n"
                for g in current_goals["quarter"][:3]:
                    emoji = area_emoji.get(g.get("area", ""), "🎯")
                    progress = g.get("progress_percentage", 0)
                    message += f"  {emoji} {g['title']} ({progress}%)\n"
                message += "\n"
            
            # Semanal
            if current_goals.get("week"):
                message += "🟡 *Semanais (Micro):*\n"
                for g in current_goals["week"][:5]:
                    emoji = area_emoji.get(g.get("area", ""), "🎯")
                    progress = g.get("progress_percentage", 0)
                    message += f"  {emoji} {g['title']} ({progress}%)\n"
                message += "\n"
            
            if not any(current_goals.values()):
                message += "_Nenhum objetivo ativo._\n\n"
                message += "Use `/objetivo [título]` para criar!"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("list_goals_failed", error=str(e))
            update.message.reply_text("❌ Erro ao listar objetivos.")
    
    # ==========================================
    # MEMORY & LEARNING COMMANDS
    # ==========================================
    
    def remember_command(self, update: Update, context: CallbackContext):
        """Handler para /lembrar [info] - salva uma informação na memória"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            if not context.args:
                update.message.reply_text(
                    "💡 *Como usar:*\n"
                    "`/lembrar Prefiro café sem açúcar`\n"
                    "`/lembrar Meu aniversário é 15/03`\n"
                    "`/lembrar Reunião semanal às terças 10h`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            content = " ".join(context.args)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                memory = loop.run_until_complete(
                    context_service.add_memory(
                        user_id=user_id,
                        category=MemoryCategory.FACT,
                        content=content,
                        importance=7
                    )
                )
            finally:
                loop.close()
            
            if memory:
                update.message.reply_text(
                    f"🧠 *Memorizado!*\n\n"
                    f"_{content}_\n\n"
                    f"Vou lembrar disso nas próximas conversas.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text("❌ Erro ao salvar memória.")
                
        except Exception as e:
            logger.error("remember_command_failed", error=str(e))
            update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
    
    def memories_command(self, update: Update, context: CallbackContext):
        """Handler para /memorias - lista memórias salvas"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            # Buscar memórias
            memories = self.supabase.table("user_memories")\
                .select("category, content, importance, created_at")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .order("importance", desc=True)\
                .limit(15)\
                .execute()
            
            if not memories.data:
                update.message.reply_text(
                    "📭 *Nenhuma memória salva*\n\n"
                    "Use `/lembrar [info]` para salvar algo.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Agrupar por categoria
            by_category = {}
            for mem in memories.data:
                cat = mem.get("category", "other")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(mem)
            
            # Emojis por categoria
            emoji_map = {
                "preference": "⭐",
                "fact": "📌",
                "pattern": "🔄",
                "relationship": "👥",
                "goal": "🎯",
                "context": "💭",
                "feedback": "💬"
            }
            
            lines = ["🧠 *Minhas Memórias*\n"]
            
            for cat, mems in by_category.items():
                emoji = emoji_map.get(cat, "•")
                lines.append(f"\n*{cat.title()}:*")
                for m in mems[:5]:
                    content = m.get("content", "")[:60]
                    if len(m.get("content", "")) > 60:
                        content += "..."
                    lines.append(f"  {emoji} {content}")
            
            lines.append(f"\n_Total: {len(memories.data)} memórias_")
            
            update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("memories_command_failed", error=str(e))
            update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
    
    def learn_command(self, update: Update, context: CallbackContext):
        """Handler para /aprender - executa análise de padrões"""
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            
            update.message.reply_text(
                "🔍 *Analisando seus padrões...*\n"
                "_Isso pode levar alguns segundos._",
                parse_mode=ParseMode.MARKDOWN
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    pattern_learning_service.run_full_analysis(user_id)
                )
            finally:
                loop.close()
            
            if result.get("status") == "completed":
                details = result.get("details", {})
                lines = ["🧪 *Análise Completa!*\n"]
                
                # Horários
                time_p = details.get("time_patterns", {})
                if time_p.get("status") == "success":
                    pattern = time_p.get("pattern", {})
                    lines.append(f"⏰ *Horários:* Mais ativo às {pattern.get('peak_hours', ['-'])[0]}h")
                    lines.append(f"   Período preferido: {pattern.get('preferred_period', '-')}")
                
                # Produtividade
                prod_p = details.get("productivity_cycles", {})
                if prod_p.get("status") == "success":
                    pattern = prod_p.get("pattern", {})
                    lines.append(f"\n📊 *Produtividade:* Picos em {', '.join(pattern.get('peak_days', []))}")
                
                # Tarefas
                task_p = details.get("task_patterns", {})
                if task_p.get("status") == "success":
                    pattern = task_p.get("pattern", {})
                    lines.append(f"\n✅ *Tarefas:* {pattern.get('completion_rate', 0)}% conclusão")
                    if pattern.get("avg_completion_days"):
                        lines.append(f"   Tempo médio: {pattern.get('avg_completion_days')} dias")
                
                # Comunicação
                comm_p = details.get("communication_style", {})
                if comm_p.get("status") == "success":
                    pattern = comm_p.get("pattern", {})
                    lines.append(f"\n💬 *Comunicação:* {pattern.get('preferred_length', '-')}, {pattern.get('formality', '-')}")
                
                # Interesses
                topic_p = details.get("topic_interests", {})
                if topic_p.get("status") == "success":
                    pattern = topic_p.get("pattern", {})
                    interests = pattern.get("top_interests", [])[:3]
                    if interests:
                        lines.append(f"\n🎯 *Interesses:* {', '.join(interests)}")
                
                lines.append(f"\n_Análises bem-sucedidas: {result.get('successful_analyses', 0)}/6_")
                
                update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(
                    "⚠️ Análise incompleta.\n"
                    "Preciso de mais dados de uso para identificar padrões.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error("learn_command_failed", error=str(e))
            update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
    
    # ==========================================
    # REPORT COMMANDS
    # ==========================================
    
    def report_command(self, update: Update, context: CallbackContext):
        """Handler para /relatorio [tipo] [params] - gera relatórios diversos
        
        Formatos suportados:
        - /relatorio - relatório mensal (mês anterior)
        - /relatorio semanal - última semana
        - /relatorio mensal [mes] [ano]
        - /relatorio trimestral [Q] [ano]
        - /relatorio anual [ano]
        """
        user = update.effective_user
        
        if user.id != self.owner_chat_id:
            return
        
        try:
            user_result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", user.id)\
                .execute()
            
            if not user_result.data:
                update.message.reply_text("❌ Execute /start primeiro.")
                return
            
            user_id = user_result.data[0]["user_id"]
            args = context.args if context.args else []
            
            # Determinar tipo de relatório
            report_type = "mensal"  # default
            if len(args) >= 1:
                first_arg = args[0].lower()
                if first_arg in ["semanal", "semana", "week", "w"]:
                    report_type = "semanal"
                    args = args[1:]  # remove tipo dos args
                elif first_arg in ["mensal", "mes", "month", "m"]:
                    report_type = "mensal"
                    args = args[1:]
                elif first_arg in ["trimestral", "trimestre", "quarter", "q"]:
                    report_type = "trimestral"
                    args = args[1:]
                elif first_arg in ["anual", "ano", "year", "y"]:
                    report_type = "anual"
                    args = args[1:]
                else:
                    # Se não é um tipo, é param do mensal (retrocompatibilidade)
                    pass
            
            # Emoji por tipo
            emoji_map = {
                "semanal": "📅",
                "mensal": "📊",
                "trimestral": "📈",
                "anual": "📚"
            }
            
            update.message.reply_text(
                f"{emoji_map.get(report_type, '📊')} Gerando relatório {report_type}...\n"
                "_Isso pode levar alguns segundos._",
                parse_mode=ParseMode.MARKDOWN
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if report_type == "semanal":
                    # /relatorio semanal [semana] [ano]
                    week = int(args[0]) if len(args) >= 1 else None
                    year = int(args[1]) if len(args) >= 2 else None
                    
                    result = loop.run_until_complete(
                        report_service.get_weekly_report(user_id, week_number=week, year=year)
                    )
                    
                elif report_type == "trimestral":
                    # /relatorio trimestral [Q] [ano]
                    quarter = int(args[0]) if len(args) >= 1 else None
                    year = int(args[1]) if len(args) >= 2 else None
                    
                    if quarter and (quarter < 1 or quarter > 4):
                        update.message.reply_text("❌ Trimestre inválido (1-4)")
                        return
                    
                    result = loop.run_until_complete(
                        report_service.get_quarterly_report(user_id, quarter=quarter, year=year)
                    )
                    
                elif report_type == "anual":
                    # /relatorio anual [ano]
                    year = int(args[0]) if len(args) >= 1 else None
                    
                    result = loop.run_until_complete(
                        report_service.get_annual_report(user_id, year=year)
                    )
                    
                else:
                    # Mensal (default)
                    # /relatorio [mes] [ano] ou /relatorio mensal [mes] [ano]
                    month = None
                    year = None
                    
                    if len(args) >= 1:
                        try:
                            month = int(args[0])
                            if month < 1 or month > 12:
                                update.message.reply_text("❌ Mês inválido (1-12)")
                                return
                        except ValueError:
                            pass
                    
                    if len(args) >= 2:
                        try:
                            year = int(args[1])
                        except ValueError:
                            pass
                    
                    result = loop.run_until_complete(
                        report_service.get_monthly_report(user_id, month=month, year=year)
                    )
                    
            finally:
                loop.close()
            
            if result.get("success"):
                # Envia relatório formatado
                message = result.get("message", "")
                
                # Telegram limita mensagem a 4096 chars
                if len(message) > 4000:
                    # Dividir em partes
                    parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
                    for part in parts:
                        update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
                else:
                    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
                    
                logger.info("report_sent", user_id=user_id, type=report_type)
            else:
                update.message.reply_text(f"❌ Erro ao gerar relatório: {result.get('message', 'Erro desconhecido')}")
                
        except ValueError as e:
            update.message.reply_text(f"❌ Parâmetro inválido: {str(e)}")
        except Exception as e:
            logger.error("report_command_failed", error=str(e))
            update.message.reply_text("❌ Erro ao processar relatório.")


# Instância global
bot_handler = TelegramBotHandler()
