"""
TB Personal OS - Telegram Bot Handler (Unified)
Processa mensagens e comandos do Telegram usando python-telegram-bot v13.x
"""

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)
import structlog
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from supabase import create_client, Client

logger = structlog.get_logger(__name__)

# Lazy imports dos serviços de contexto (importados quando necessário)
_context_service = None
_memory_service = None


class TelegramBotHandler:
    """
    Handler unificado para o bot do Telegram.
    Usa python-telegram-bot v13.x com padrão síncrono.
    """
    
    def __init__(self):
        self._supabase: Optional[Client] = None
        self._gemini_service = None
        self.owner_chat_id = int(settings.OWNER_TELEGRAM_CHAT_ID) if settings.OWNER_TELEGRAM_CHAT_ID else 0
        self.updater: Optional[Updater] = None
        
        logger.info(
            "bot_handler_initialized",
            owner_chat_id=self.owner_chat_id
        )
    
    @property
    def supabase(self) -> Optional[Client]:
        """Lazy load do Supabase client. Retorna None se não conectar."""
        if self._supabase is None:
            try:
                self._supabase = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                # Testar conexão
                self._supabase.table("users").select("id").limit(1).execute()
                logger.info("supabase_client_connected")
            except Exception as e:
                logger.warning("supabase_unavailable_offline_mode", error=str(e))
                self._supabase = None
        return self._supabase
    
    @property
    def gemini(self):
        """Lazy load do Gemini service."""
        if self._gemini_service is None:
            from app.services.gemini_service import GeminiService
            self._gemini_service = GeminiService()
            logger.info("gemini_service_initialized")
        return self._gemini_service
    
    # ==========================================
    # VERIFICAÇÕES E UTILITÁRIOS
    # ==========================================
    
    def _is_owner(self, user_id: int) -> bool:
        """Verifica se o usuário é o owner."""
        return user_id == self.owner_chat_id
    
    def _is_supabase_available(self) -> bool:
        """Verifica se o Supabase está disponível."""
        return self.supabase is not None
    
    def _get_user_id(self, telegram_user_id: int) -> Optional[str]:
        """Obtém o user_id do banco a partir do telegram_user_id."""
        if not self._is_supabase_available():
            return f"offline_{telegram_user_id}"
        
        try:
            result = self.supabase.table("telegram_chats")\
                .select("user_id")\
                .eq("chat_id", telegram_user_id)\
                .execute()
            
            if result.data:
                return result.data[0]["user_id"]
            return None
        except Exception as e:
            logger.error("get_user_id_failed", error=str(e), telegram_user_id=telegram_user_id)
            return f"offline_{telegram_user_id}"
    
    def _ensure_user_exists(self, update: Update) -> Optional[str]:
        """
        Garante que o usuário existe no banco.
        Cria se necessário. Retorna o user_id.
        """
        user = update.effective_user
        
        # Modo offline - retorna ID temporário
        if not self._is_supabase_available():
            logger.info("offline_mode_user", telegram_id=user.id)
            return f"offline_{user.id}"
        
        try:
            # Verificar se já existe
            user_id = self._get_user_id(user.id)
            if user_id and not user_id.startswith("offline_"):
                return user_id
            
            # Criar novo usuário
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Telegram User"
            
            new_user = self.supabase.table("users").insert({
                "email": f"telegram_{user.id}@tbpersonal.os",
                "full_name": full_name
            }).execute()
            
            user_id = new_user.data[0]["id"]
            
            # Criar profile
            self.supabase.table("profiles").insert({
                "user_id": user_id,
                "timezone": settings.OWNER_TIMEZONE,
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
            
            logger.info(
                "user_created",
                user_id=user_id,
                telegram_id=user.id,
                username=user.username
            )
            
            return user_id
            
        except Exception as e:
            logger.error("ensure_user_failed", error=str(e), telegram_id=user.id)
            # Retornar ID offline em caso de erro
            return f"offline_{user.id}"
    
    def _classify_message_simple(self, text: str) -> Dict[str, Any]:
        """
        Classificação simples por keywords (fallback sem IA).
        """
        text_lower = text.lower()
        
        # Determinar tipo
        msg_type = "note"
        if any(word in text_lower for word in ["tarefa", "fazer", "to-do", "preciso", "lembrar de"]):
            msg_type = "task"
        elif any(word in text_lower for word in ["ideia", "pensei", "e se", "poderia"]):
            msg_type = "idea"
        elif text.endswith("?"):
            msg_type = "question"
        
        # Determinar categoria
        category = "other"
        if any(word in text_lower for word in ["trabalho", "cliente", "projeto", "reunião", "deadline"]):
            category = "work"
        elif any(word in text_lower for word in ["academia", "treino", "saúde", "exercício", "dieta", "sono"]):
            category = "health"
        elif any(word in text_lower for word in ["post", "conteúdo", "instagram", "linkedin", "blog"]):
            category = "content"
        elif any(word in text_lower for word in ["pagar", "receber", "dinheiro", "grana", "conta", "fatura"]):
            category = "finance"
        elif any(word in text_lower for word in ["família", "amigo", "pessoal", "casa"]):
            category = "personal"
        
        # Determinar prioridade
        priority = "medium"
        if any(word in text_lower for word in ["urgente", "hoje", "agora", "crítico", "importante"]):
            priority = "high"
        elif any(word in text_lower for word in ["depois", "quando der", "sem pressa", "eventualmente"]):
            priority = "low"
        
        return {
            "type": msg_type,
            "category": category,
            "priority": priority,
            "needs_response": msg_type == "question",
            "suggested_action": f"Salvar como {msg_type}",
            "confidence": "low",
            "method": "keywords"
        }
    
    def _classify_message_ai(self, text: str) -> Dict[str, Any]:
        """
        Classificação usando Gemini AI.
        """
        try:
            prompt = f"""Analise esta mensagem e classifique-a.

MENSAGEM: "{text}"

Retorne APENAS um JSON válido (sem markdown, sem explicações) no formato:
{{
    "type": "task|idea|note|question",
    "category": "personal|work|health|content|finance|other",
    "priority": "low|medium|high|urgent",
    "needs_response": true ou false,
    "suggested_action": "descrição curta da ação sugerida",
    "entities": {{
        "people": ["nomes mencionados"],
        "dates": ["datas mencionadas"],
        "values": ["valores monetários"]
    }},
    "response": "se needs_response=true, escreva uma resposta útil aqui"
}}

Regras:
- type: task (algo a fazer), idea (sugestão/insight), note (informação), question (pergunta)
- category: baseado no contexto principal
- priority: urgente/hoje=high, normal=medium, sem pressa=low
- needs_response: true apenas se for pergunta que precisa resposta
"""
            
            # Chamada síncrona ao Gemini
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    self.gemini.generate_text(prompt, temperature=0.3)
                )
            finally:
                loop.close()
            
            # Extrair JSON da resposta
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                result["confidence"] = "high"
                result["method"] = "gemini"
                return result
            
            raise ValueError("No valid JSON in response")
            
        except Exception as e:
            logger.warning(
                "ai_classification_failed",
                error=str(e),
                text_preview=text[:50]
            )
            # Fallback para classificação simples
            result = self._classify_message_simple(text)
            result["ai_error"] = str(e)
            return result
    
    def _save_to_inbox(
        self,
        user_id: str,
        content: str,
        classification: Dict[str, Any],
        source_metadata: Dict[str, Any]
    ) -> Optional[Dict]:
        """Salva item na inbox."""
        try:
            data = {
                "user_id": user_id,
                "content": content,
                "content_type": "text",
                "source": "telegram",
                "status": "new",
                "category": classification.get("category", "other"),
                "tags": [classification.get("type", "note")],
                "source_metadata": source_metadata,
                "suggested_actions": classification
            }
            
            result = self.supabase.table("inbox_items").insert(data).execute()
            
            logger.info(
                "inbox_item_created",
                item_id=result.data[0]["id"],
                category=classification.get("category"),
                type=classification.get("type")
            )
            
            return result.data[0]
            
        except Exception as e:
            logger.error("save_to_inbox_failed", error=str(e), user_id=user_id)
            return None
    
    def _log_assistant_action(
        self,
        user_id: str,
        action_type: str,
        input_data: Dict,
        output_data: Dict,
        success: bool = True
    ):
        """Registra ação no log do assistente."""
        try:
            self.supabase.table("assistant_logs").insert({
                "user_id": user_id,
                "action_type": action_type,
                "input_data": input_data,
                "output_data": output_data,
                "success": success,
                "source": "telegram"
            }).execute()
        except Exception as e:
            logger.error("log_action_failed", error=str(e))
    
    # ==========================================
    # COMMAND HANDLERS
    # ==========================================
    
    def cmd_start(self, update: Update, context: CallbackContext):
        """Handler para /start."""
        user = update.effective_user
        
        logger.info(
            "command_start",
            user_id=user.id,
            username=user.username
        )
        
        # Verificar se é o owner
        if not self._is_owner(user.id):
            update.message.reply_text(
                "⛔️ Este bot é privado.\n"
                "Apenas o proprietário pode utilizá-lo."
            )
            return
        
        # Garantir que usuário existe no banco
        db_user_id = self._ensure_user_exists(update)
        
        # Verificar modo offline
        offline_mode = db_user_id and db_user_id.startswith("offline_")
        
        # Verificar se já fez onboarding
        needs_onboarding = False
        if not offline_mode and self._is_supabase_available():
            try:
                result = self.supabase.table('profiles')\
                    .select('onboarding_completed')\
                    .eq('user_id', db_user_id)\
                    .execute()
                
                if result.data and not result.data[0].get('onboarding_completed', False):
                    needs_onboarding = True
            except:
                pass
        offline_notice = ""
        if offline_mode:
            offline_notice = "\n⚠️ _Modo Offline: banco de dados indisponível_\n"
        
        # Verificar se completou onboarding
        onboarding_completed = False
        if not offline_mode:
            try:
                profile = self.supabase.table('profiles')\
                    .select('onboarding_completed')\
                    .eq('user_id', db_user_id)\
                    .execute()
                
                if profile.data and profile.data[0].get('onboarding_completed'):
                    onboarding_completed = True
            except:
                pass
        
        # Se não completou onboarding, mostrar mensagem inicial Performance Points
        if not onboarding_completed:
            welcome = (
                f"👋 Olá, {user.first_name}!\n\n"
                "🧠 *PERFORMANCE POINTS*\n"
                "_Assistente Pessoal de Alta Performance & Vida Integrada_\n\n"
                "Para começar, vamos criar seu perfil em 7 perguntas rápidas.\n\n"
                "📊 Use /quiz para iniciar\n\n"
                "💡 Menos dispersão. Mais presença. Progresso real."
            )
        else:
            # Mensagem para quem já completou
            welcome = (
                f"👋 Bem-vindo de volta, {user.first_name}!\n\n"
                "🧠 *PERFORMANCE POINTS*\n\n"
                "Comandos principais:\n"
                "📊 /status - Ver painel\n"
                "🎯 /quest - Missão do dia\n"
                "🌅 /checkin - Check-in de energia\n"
                "🔄 /revisar - Atualizar perfil\n\n"
                "💬 Ou envie qualquer texto e eu processo com IA\n\n"
                "Use /help para ver todos os comandos."
            )
        
        update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)
    
    def cmd_help(self, update: Update, context: CallbackContext):
        """Handler para /help."""
        if not self._is_owner(update.effective_user.id):
            return
        
        help_text = (
            "📖 *Comandos Disponíveis*\n\n"
            "*🎮 Gamificação & Perfil:*\n"
            "• /status - Ver painel Performance Points\n"
            "• /atributos - Detalhes dos 4 atributos\n"
            "• /conquistas - Ver conquistas desbloqueadas\n"
            "• /quiz - Iniciar personalização (onboarding)\n\n"
            "*🎯 Quests (Missões Adaptativas):*\n"
            "• /quest - Quest do dia (adaptativa)\n"
            "• /quest semanal - Quest estratégica\n"
            "• /quest reflexiva - Pergunta poderosa\n\n"
            "*🌅 Check-in Diário:*\n"
            "• /checkin - Check-in de energia (0-100)\n"
            "• /checkin 75 - Registrar energia rapidamente\n\n"
            "*✏️ Perfil Vivo:*\n"
            "• /revisar - Revisar e atualizar perfil (a cada 15-30 dias)\n"
            "• /editar perfil - Menu de edição completo\n"
            "• /editar areas - Editar áreas prioritárias\n"
            "• /editar metas - Editar meta principal\n"
            "• /editar habilidades - Editar skills\n"
            "• /editar corpo - Editar exercício/energia\n"
            "• /editar renda - Editar fontes de renda\n\n"
            "*📥 Inbox & Organização:*\n"
            "• /inbox - Ver items na inbox\n"
            "• /inbox clear - Arquivar processados\n\n"
            "*📋 Tarefas:*\n"
            "• /tasks - Listar tarefas pendentes\n"
            "• /task [título] - Criar nova tarefa\n"
            "• /done [id] - Marcar como concluída (+XP)\n\n"
            "*📁 Projetos:*\n"
            "• /projetos - Listar projetos ativos\n"
            "• /projeto [nome] - Ver ou criar projeto\n\n"
            "*📊 Histórico:*\n"
            "• /energia [1-10] - Registrar energia\n"
            "• /humor [texto] - Registrar humor\n"
            "• /resumo - Resumo do dia\n\n"
            "*📆 Agenda:*\n"
            "• /agenda - Ver eventos de hoje\n"
            "• /rotina - Executar rotina manualmente\n\n"
            "*📧 Email:*\n"
            "• /emails - Ver emails não lidos\n\n"
            "*💡 Conteúdo:*\n"
            "• /ideia [texto] - Salvar ideia\n"
            "• /ideias - Listar ideias\n\n"
            "*💰 Finanças:*\n"
            "• /financas - Resumo financeiro\n"
            "• /entrada [valor] [desc] - Registrar entrada\n"
            "• /saida [valor] [desc] - Registrar saída\n\n"
            "*🧠 Memória:*\n"
            "• /lembrar [texto] - Salvar memória\n"
            "• /buscar [termo] - Buscar memórias\n\n"
            "*📊 Insights:*\n"
            "• /insights - Ver insights e recomendações\n\n"
            "*🤖 Configurações:*\n"
            "• /autonomia [1-5] - Nível de autonomia\n\n"
            "*💬 Envio Livre:*\n"
            "Envie qualquer texto e eu processo com IA!"
        )
        
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def cmd_inbox(self, update: Update, context: CallbackContext):
        """Handler para /inbox."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            # Buscar items
            items = self.supabase.table("inbox_items")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "new")\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if not items.data:
                update.message.reply_text(
                    "📥 *Inbox vazia*\n\n"
                    "Nenhum item pendente! ✅\n\n"
                    "_Envie mensagens para adicionar itens._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Formatar lista
            emoji_map = {
                "personal": "👤", "work": "💼", "health": "🏃",
                "content": "📝", "finance": "💰", "other": "📌"
            }
            
            message = "📥 *Inbox - Items Pendentes*\n\n"
            
            for idx, item in enumerate(items.data, 1):
                emoji = emoji_map.get(item.get("category", "other"), "📌")
                content = item["content"][:60]
                if len(item["content"]) > 60:
                    content += "..."
                
                # Extrair tipo das tags
                tags = item.get("tags", [])
                item_type = tags[0] if tags else "note"
                
                message += f"{idx}. {emoji} *{item_type.title()}*\n"
                message += f"   {content}\n\n"
            
            total = len(items.data)
            message += f"_Total: {total} item{'s' if total > 1 else ''}_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_inbox_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar inbox.")
    
    def cmd_tasks(self, update: Update, context: CallbackContext):
        """Handler para /tasks."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            # Buscar tarefas pendentes
            tasks = self.supabase.table("tasks")\
                .select("*")\
                .eq("user_id", user_id)\
                .in_("status", ["todo", "in_progress"])\
                .order("priority", desc=True)\
                .order("due_date")\
                .limit(10)\
                .execute()
            
            if not tasks.data:
                update.message.reply_text(
                    "✅ *Sem Tarefas Pendentes*\n\n"
                    "Você está em dia! 🎉\n\n"
                    "_Use /task [título] para criar uma nova._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            priority_emoji = {
                "urgent": "🔴", "high": "🟠", 
                "medium": "🟡", "low": "🟢"
            }
            
            message = "📋 *Tarefas Pendentes*\n\n"
            
            for idx, task in enumerate(tasks.data, 1):
                emoji = priority_emoji.get(task.get("priority", "medium"), "🟡")
                status = "🔄" if task.get("status") == "in_progress" else "⬜"
                
                title = task["title"][:50]
                if len(task["title"]) > 50:
                    title += "..."
                
                due = ""
                if task.get("due_date"):
                    due = f" 📅 {task['due_date']}"
                
                message += f"{status} {emoji} {title}{due}\n"
                message += f"   _ID: {task['id'][:8]}_\n\n"
            
            message += f"_Total: {len(tasks.data)} tarefas_\n\n"
            message += "Use /done [ID] para concluir"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_tasks_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar tarefas.")
    
    def cmd_task(self, update: Update, context: CallbackContext):
        """Handler para /task [título] - criar tarefa."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        # Extrair título
        if not context.args:
            update.message.reply_text(
                "❌ *Uso:* /task [título da tarefa]\n\n"
                "_Exemplo: /task Revisar proposta do cliente_",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        title = " ".join(context.args)
        
        try:
            # Criar tarefa
            task = self.supabase.table("tasks").insert({
                "user_id": user_id,
                "title": title,
                "status": "todo",
                "priority": "medium"
            }).execute()
            
            task_id = task.data[0]["id"]
            
            logger.info("task_created", task_id=task_id, title=title)
            
            update.message.reply_text(
                f"✅ *Tarefa Criada*\n\n"
                f"📋 {title}\n\n"
                f"_ID: {task_id[:8]}_",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_task_failed", error=str(e))
            update.message.reply_text("❌ Erro ao criar tarefa.")
    
    def cmd_done(self, update: Update, context: CallbackContext):
        """Handler para /done [id] - marcar tarefa como concluída."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "❌ *Uso:* /done [ID da tarefa]\n\n"
                "_Use /tasks para ver os IDs_",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        task_id_partial = context.args[0]
        
        try:
            # Buscar tarefa que começa com o ID fornecido
            tasks = self.supabase.table("tasks")\
                .select("*")\
                .eq("user_id", user_id)\
                .like("id", f"{task_id_partial}%")\
                .execute()
            
            if not tasks.data:
                update.message.reply_text("❌ Tarefa não encontrada.")
                return
            
            task = tasks.data[0]
            
            # Atualizar status
            self.supabase.table("tasks")\
                .update({
                    "status": "done",
                    "completed_at": datetime.utcnow().isoformat()
                })\
                .eq("id", task["id"])\
                .execute()
            
            logger.info("task_completed", task_id=task["id"])
            
            # Adicionar XP por completar tarefa
            try:
                from app.services.gamification_service import gamification
                priority = task.get('priority', 'medium')
                xp_result = gamification.on_task_completed(user_id, priority)
                
                xp_msg = f"\n🎮 *+{xp_result.get('xp_gained', 0)} XP*"
                if xp_result.get('level_up'):
                    xp_msg += f"\n🎉 *LEVEL UP!* Nível {xp_result.get('new_level')}!"
            except:
                xp_msg = ""
            
            update.message.reply_text(
                f"✅ *Tarefa Concluída!*\n\n"
                f"~~{task['title']}~~{xp_msg}\n\n"
                f"🎉 Bom trabalho!",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_done_failed", error=str(e))
            update.message.reply_text("❌ Erro ao concluir tarefa.")
    
    def cmd_checkin(self, update: Update, context: CallbackContext):
        """Handler para /checkin - check-in interativo."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        # Criar teclado inline
        keyboard = [
            [
                InlineKeyboardButton("⚡ Energia", callback_data="checkin_energy"),
                InlineKeyboardButton("😊 Humor", callback_data="checkin_mood"),
            ],
            [
                InlineKeyboardButton("😴 Sono", callback_data="checkin_sleep"),
                InlineKeyboardButton("🎯 Foco", callback_data="checkin_focus"),
            ],
            [
                InlineKeyboardButton("🏋️ Treino", callback_data="checkin_workout"),
                InlineKeyboardButton("🥗 Nutrição", callback_data="checkin_nutrition"),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "📊 *Check-in*\n\n"
            "O que você quer registrar?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def cmd_resumo(self, update: Update, context: CallbackContext):
        """Handler para /resumo - resumo do dia."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Buscar dados do dia
            inbox_count = self.supabase.table("inbox_items")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", today)\
                .execute()
            
            tasks_done = self.supabase.table("tasks")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("status", "done")\
                .gte("completed_at", today)\
                .execute()
            
            tasks_pending = self.supabase.table("tasks")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .in_("status", ["todo", "in_progress"])\
                .execute()
            
            message = (
                f"📊 *Resumo do Dia*\n"
                f"_{today}_\n\n"
                f"📥 Inbox: {inbox_count.count or 0} novos items\n"
                f"✅ Tarefas concluídas: {tasks_done.count or 0}\n"
                f"📋 Tarefas pendentes: {tasks_pending.count or 0}\n"
            )
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_resumo_failed", error=str(e))
            update.message.reply_text("❌ Erro ao gerar resumo.")
    
    # ==========================================
    # MESSAGE HANDLERS
    # ==========================================
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handler para mensagens de texto livres."""
        user = update.effective_user
        message_text = update.message.text
        
        if not self._is_owner(user.id):
            return
        
        logger.info(
            "message_received",
            user_id=user.id,
            length=len(message_text),
            preview=message_text[:50]
        )
        
        # Garantir usuário
        user_id = self._ensure_user_exists(update)
        if not user_id:
            update.message.reply_text("❌ Erro interno. Tente /start novamente.")
            return
        
        # ESTADOS DE CONVERSA
        # 1. Check-ins
        awaiting = context.user_data.get('awaiting_checkin')
        
        if awaiting == 'energy':
            try:
                level = int(message_text)
                if not 1 <= level <= 10:
                    raise ValueError()
                
                from app.services.checkin_service import CheckinService
                from app.services.gamification_service import GamificationService
                
                checkin_svc = CheckinService(self.supabase)
                gamif = GamificationService(self.supabase)
                
                checkin_svc.checkin_energy(user_id, level)
                gamif.on_checkin_completed(user_id, 'energy')
                
                update.message.reply_text(f"✅ ⚡ Energia registrada: {level}/10\n\n+10 XP")
                context.user_data.pop('awaiting_checkin', None)
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número entre 1 e 10")
                return
        
        elif awaiting == 'sleep':
            try:
                hours = float(message_text.replace(',', '.'))
                if not 0 <= hours <= 24:
                    raise ValueError()
                
                from app.services.checkin_service import CheckinService
                from app.services.gamification_service import GamificationService
                
                checkin_svc = CheckinService(self.supabase)
                gamif = GamificationService(self.supabase)
                
                # Score baseado nas horas (7-9h = ideal)
                if 7 <= hours <= 9:
                    quality = 10
                elif 6 <= hours <= 10:
                    quality = 8
                elif 5 <= hours <= 11:
                    quality = 6
                else:
                    quality = 4
                
                checkin_svc.checkin_sleep(user_id, hours, quality)
                gamif.on_checkin_completed(user_id, 'sleep')
                
                update.message.reply_text(f"✅ 😴 Sono registrado: {hours}h\n\n+10 XP")
                context.user_data.pop('awaiting_checkin', None)
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número válido de horas (ex: 7.5)")
                return
        
        elif awaiting == 'focus':
            try:
                level = int(message_text)
                if not 1 <= level <= 10:
                    raise ValueError()
                
                from app.services.checkin_service import CheckinService
                from app.services.gamification_service import GamificationService
                
                checkin_svc = CheckinService(self.supabase)
                gamif = GamificationService(self.supabase)
                
                checkin_svc.checkin_focus(user_id, level)
                gamif.on_checkin_completed(user_id, 'focus')
                
                update.message.reply_text(f"✅ 🎯 Foco registrado: {level}/10\n\n+10 XP")
                context.user_data.pop('awaiting_checkin', None)
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número entre 1 e 10")
                return
        
        elif awaiting == 'workout_duration':
            try:
                duration = int(message_text)
                if duration <= 0:
                    raise ValueError()
                
                workout_type = context.user_data.get('workout_type', 'other')
                context.user_data['workout_duration'] = duration
                
                # Perguntar intensidade
                keyboard = [
                    [InlineKeyboardButton("🔥 Alta", callback_data="workout_intensity_high")],
                    [InlineKeyboardButton("💪 Moderada", callback_data="workout_intensity_moderate")],
                    [InlineKeyboardButton("🌿 Leve", callback_data="workout_intensity_light")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                update.message.reply_text(
                    f"🏋️ *{duration} minutos*\n\nQual foi a intensidade?",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_checkin'] = 'workout_intensity'
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número válido de minutos")
                return
        
        elif awaiting == 'nutrition_quality':
            try:
                quality = int(message_text)
                if not 1 <= quality <= 10:
                    raise ValueError()
                
                context.user_data['nutrition_quality'] = quality
                
                update.message.reply_text(
                    "💧 *Hidratação*\n\nQuantos copos de água? (0-15)",
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_checkin'] = 'nutrition_hydration'
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número entre 1 e 10")
                return
        
        elif awaiting == 'nutrition_hydration':
            try:
                hydration = int(message_text)
                if not 0 <= hydration <= 15:
                    raise ValueError()
                
                from app.services.checkin_service import CheckinService
                from app.services.gamification_service import GamificationService
                
                checkin_svc = CheckinService(self.supabase)
                gamif = GamificationService(self.supabase)
                
                meal_type = context.user_data.get('nutrition_meal', 'meal')
                quality = context.user_data.get('nutrition_quality', 5)
                
                checkin_svc.checkin_nutrition(user_id, meal_type, quality, hydration)
                gamif.on_checkin_completed(user_id, 'nutrition')
                
                update.message.reply_text(
                    f"✅ 🥗 Nutrição registrada!\n\n"
                    f"Qualidade: {quality}/10\n"
                    f"Hidratação: {hydration} copos\n\n"
                    f"+10 XP"
                )
                
                # Limpar estados
                context.user_data.pop('awaiting_checkin', None)
                context.user_data.pop('nutrition_meal', None)
                context.user_data.pop('nutrition_quality', None)
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número entre 0 e 15")
                return
        
        # 1b. Check se está aguardando energia do check-in (legacy)
        if context.user_data.get('awaiting_checkin_energy'):
            try:
                energy = int(message_text)
                from app.services.checkin_service import checkin_service
                result = checkin_service.process_daily_energy(user_id, energy)
                update.message.reply_text(result['message'])
                context.user_data['awaiting_checkin_energy'] = False
                return
            except ValueError:
                update.message.reply_text("❌ Digite um número entre 0 e 100")
                return
        
        # 2. Check se está em revisão de perfil
        if context.user_data.get('in_profile_review'):
            # TODO: Processar escolha de campo a editar
            if message_text == '0' or message_text.lower() in ['cancelar', '/cancelar']:
                context.user_data['in_profile_review'] = False
                update.message.reply_text("✅ Revisão cancelada.")
                return
            else:
                # Mapear número para campo
                field_map = {
                    '1': 'life_areas',
                    '2': 'skills',
                    '3': 'main_goal',
                    '4': 'blockers',
                    '5': 'exercise',
                    '6': 'income_sources'
                }
                
                field = field_map.get(message_text)
                if field:
                    from app.services.profile_editor_service import profile_editor
                    # Iniciar edição do campo específico
                    context.user_data['editing_field'] = field
                    context.user_data['in_profile_review'] = False
                    update.message.reply_text(f"🔄 Edição de {field} em desenvolvimento. Use /editar {field} por enquanto.")
                    return
                else:
                    update.message.reply_text("❌ Digite um número de 1 a 6, ou 0 para cancelar")
                    return
        
        # 3. Check se está em onboarding respondendo questão de texto
        if context.user_data.get('onboarding_text_question'):
            from app.services.onboarding_service_v2 import onboarding_v2
            question_id = context.user_data['onboarding_text_question']
            
            # Buscar answers do context
            current_answers = context.user_data.get('onboarding_answers', {})
            
            # Salvar resposta
            result = onboarding_v2.save_answer(user_id, question_id, message_text, current_answers)
            
            # Atualizar answers no context
            if result.get('answers'):
                context.user_data['onboarding_answers'] = result['answers']
            
            # Limpar flag de texto
            context.user_data['onboarding_text_question'] = None
            
            if result.get('completed'):
                # Onboarding completo!
                msg = result.get('message', '✅ Perfil criado!')
                update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
                
                # Limpar context
                context.user_data.pop('onboarding_answers', None)
            else:
                # Próxima pergunta
                self._send_onboarding_question(update, result, context)
            return
        
        # Mostrar "digitando..."
        update.message.chat.send_action("typing")
        
        try:
            # MODO CONVERSA COM IA (comportamento padrão)
            # Buscar contexto completo antes de conversar (RAG)
            
            # Primeiro, tentar conversar com IA
            try:
                # Importar serviços dinamicamente (evita circular imports)
                global _context_service, _memory_service
                if _context_service is None:
                    from app.services.context_service import context_service
                    _context_service = context_service
                if _memory_service is None:
                    from app.services.memory_service import memory_service
                    _memory_service = memory_service
                
                # Buscar perfil do usuário
                try:
                    profile_data = self.supabase.table('profiles').select('*').eq('user_id', user_id).single().execute()
                    profile = profile_data.data if profile_data and profile_data.data else {}
                except Exception as profile_error:
                    logger.warning("profile_fetch_failed", error=str(profile_error))
                    profile = {}
                
                # Buscar contexto do usuário (pode ser async, então usamos sync wrapper)
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Buscar contexto RAG completo
                    user_context = loop.run_until_complete(
                        _context_service.get_context_for_message(user_id, message_text)
                    )
                    
                    # Buscar memória de conversas recentes
                    recent_memory = loop.run_until_complete(
                        _memory_service.format_context_for_llm(user_id, limit=5)
                    )
                    
                    loop.close()
                except Exception as ctx_error:
                    logger.warning("context_fetch_failed", error=str(ctx_error))
                    user_context = {}
                    recent_memory = ""
                
                # Montar contexto enriquecido
                enriched_context = {
                    "profile": profile,
                    "quiz_answers": profile.get('quiz_answers', {}),
                    "personality_profile": profile.get('personality_profile', {}),
                    "recent_conversations": recent_memory,
                    "patterns": user_context.get('active_patterns', []),
                    "pending_tasks": user_context.get('pending_tasks', []),
                    "current_mode": user_context.get('current_mode', {}),
                    "recent_goals": user_context.get('recent_goals', [])
                }
                
                ai_response = self.gemini.chat_sync(
                    user_message=message_text,
                    user_id=user_id,
                    context=enriched_context
                )
                
                if ai_response and ai_response.get('response'):
                    update.message.reply_text(
                        ai_response['response'],
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Salvar interação na memória para contexto futuro
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            _memory_service.save_interaction(
                                user_id=user_id,
                                user_message=message_text,
                                assistant_response=ai_response['response'],
                                metadata={"source": "telegram", "chat_id": user.id}
                            )
                        )
                        loop.close()
                    except Exception as save_error:
                        logger.warning("memory_save_failed", error=str(save_error))
                    
                    logger.info(
                        "conversation_processed",
                        user_id=user_id,
                        message_preview=message_text[:50],
                        context_used=True
                    )
                    return
            except Exception as ai_error:
                logger.warning("ai_conversation_failed", error=str(ai_error))
            
            # FALLBACK: Se IA falhar, classificar e salvar na inbox
            classification = self._classify_message_ai(message_text)
            
            # Salvar na inbox
            source_metadata = {
                "telegram_user_id": user.id,
                "telegram_message_id": update.message.message_id,
                "username": user.username,
                "chat_type": update.message.chat.type
            }
            
            inbox_item = self._save_to_inbox(
                user_id=user_id,
                content=message_text,
                classification=classification,
                source_metadata=source_metadata
            )
            
            if not inbox_item:
                update.message.reply_text("❌ Erro ao processar. Tente novamente.")
                return
            
            # Log da ação
            self._log_assistant_action(
                user_id=user_id,
                action_type="message_processed",
                input_data={"message": message_text[:500]},
                output_data={"item_id": inbox_item["id"], "classification": classification}
            )
            
            # Preparar resposta
            if classification.get("needs_response") and classification.get("response"):
                # Se for pergunta com resposta da IA
                response = classification["response"]
            else:
                # Resposta padrão de confirmação
                type_emoji = {
                    "task": "📋", "idea": "💡", 
                    "note": "📝", "question": "❓"
                }
                category_emoji = {
                    "personal": "👤", "work": "💼", "health": "🏃",
                    "content": "📝", "finance": "💰", "other": "📌"
                }
                
                t_emoji = type_emoji.get(classification.get("type", "note"), "📝")
                c_emoji = category_emoji.get(classification.get("category", "other"), "📌")
                
                method = "🤖 IA" if classification.get("method") == "gemini" else "📊 Auto"
                
                response = (
                    f"✅ *Salvo na Inbox*\n\n"
                    f"{t_emoji} *Tipo:* {classification.get('type', 'note').title()}\n"
                    f"{c_emoji} *Categoria:* {classification.get('category', 'other').title()}\n"
                    f"⚡ *Prioridade:* {classification.get('priority', 'medium').title()}\n"
                    f"🔍 *Método:* {method}\n\n"
                    f"_ID: {inbox_item['id'][:8]}_"
                )
                
                # Adicionar sugestão se houver
                if classification.get("suggested_action"):
                    response += f"\n\n💡 _{classification['suggested_action']}_"
            
            update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            logger.info(
                "message_processed",
                item_id=inbox_item["id"],
                type=classification.get("type"),
                category=classification.get("category"),
                method=classification.get("method")
            )
            
        except Exception as e:
            logger.error("handle_message_failed", error=str(e), exc_info=True)
            update.message.reply_text(
                f"❌ Erro ao processar mensagem.\n\n"
                f"_Tente novamente ou use /help_",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def handle_callback(self, update: Update, context: CallbackContext):
        """Handler para callbacks de botões inline."""
        query = update.callback_query
        query.answer()
        
        if not self._is_owner(query.from_user.id):
            return
        
        data = query.data
        
        # Quiz onboarding
        if data.startswith("quiz_"):
            self._handle_quiz_answer(update, context, data)
            return
        
        if data.startswith("checkin_"):
            checkin_type = data.replace("checkin_", "")
            
            # Fluxos interativos por tipo
            if checkin_type == "energy":
                query.edit_message_text(
                    "⚡ *Energia*\n\nDigite um valor de 1 a 10:",
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_checkin'] = 'energy'
                
            elif checkin_type == "mood":
                # Criar teclado de emojis
                keyboard = [
                    [
                        InlineKeyboardButton("🤩", callback_data="mood_amazing"),
                        InlineKeyboardButton("😊", callback_data="mood_happy"),
                        InlineKeyboardButton("😐", callback_data="mood_neutral"),
                    ],
                    [
                        InlineKeyboardButton("😢", callback_data="mood_sad"),
                        InlineKeyboardButton("😤", callback_data="mood_frustrated"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(
                    "😊 *Humor*\n\nComo você está se sentindo?",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
            elif checkin_type == "sleep":
                query.edit_message_text(
                    "😴 *Sono*\n\nQuantas horas dormiu? (ex: 7.5)",
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_checkin'] = 'sleep'
                
            elif checkin_type == "focus":
                query.edit_message_text(
                    "🎯 *Foco*\n\nDigite um valor de 1 a 10:",
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_checkin'] = 'focus'
                
            elif checkin_type == "workout":
                # Criar teclado de tipos de treino
                keyboard = [
                    [
                        InlineKeyboardButton("🏋️ Musculação", callback_data="workout_strength"),
                        InlineKeyboardButton("🏃 Cardio", callback_data="workout_cardio"),
                    ],
                    [
                        InlineKeyboardButton("🧘 Yoga/Flex", callback_data="workout_flexibility"),
                        InlineKeyboardButton("⚽ Esporte", callback_data="workout_sport"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(
                    "🏋️ *Treino*\n\nQue tipo de exercício?",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
            elif checkin_type == "nutrition":
                # Criar teclado de refeições
                keyboard = [
                    [
                        InlineKeyboardButton("🌅 Café", callback_data="nutrition_breakfast"),
                        InlineKeyboardButton("🍽️ Almoço", callback_data="nutrition_lunch"),
                    ],
                    [
                        InlineKeyboardButton("🌙 Jantar", callback_data="nutrition_dinner"),
                        InlineKeyboardButton("🍎 Lanche", callback_data="nutrition_snack"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(
                    "🥗 *Nutrição*\n\nQual refeição?",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Callbacks de humor
        if data.startswith("mood_"):
            mood = data.replace("mood_", "")
            user_id = self._get_user_id(query.from_user.id)
            
            try:
                from app.services.checkin_service import CheckinService
                checkin_svc = CheckinService(self.supabase)
                
                mood_map = {
                    'amazing': ('🤩', 10),
                    'happy': ('😊', 8),
                    'neutral': ('😐', 5),
                    'sad': ('😢', 3),
                    'frustrated': ('😤', 1)
                }
                
                emoji, score = mood_map.get(mood, ('😐', 5))
                result = checkin_svc.checkin_mood(user_id, emoji, score)
                
                # Gamificação
                from app.services.gamification_service import GamificationService
                gamif = GamificationService(self.supabase)
                gamif.on_checkin_completed(user_id, 'mood')
                
                query.edit_message_text(
                    f"✅ {emoji} Humor registrado!\n\n+10 XP",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error("mood_checkin_failed", error=str(e))
                query.edit_message_text("❌ Erro ao registrar humor.")
            return
        
        # Callbacks de workout
        if data.startswith("workout_"):
            workout_type = data.replace("workout_", "")
            context.user_data['workout_type'] = workout_type
            
            query.edit_message_text(
                f"🏋️ *Treino - {workout_type.title()}*\n\n"
                "Quanto tempo treinou? (em minutos, ex: 45)",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['awaiting_checkin'] = 'workout_duration'
            return
        
        # Callbacks de nutrition
        if data.startswith("nutrition_"):
            meal_type = data.replace("nutrition_", "")
            context.user_data['nutrition_meal'] = meal_type
            
            query.edit_message_text(
                f"🥗 *{meal_type.title()}*\n\n"
                "Como foi a qualidade? (1-10)",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['awaiting_checkin'] = 'nutrition_quality'
    
    def _send_onboarding_question(self, update, result, context=None):
        """Envia próxima pergunta do onboarding."""
        question = result.get('question', '')
        subtitle = result.get('subtitle', '')
        options = result.get('options', [])
        text_input = result.get('text_input', False)
        hint = result.get('hint', '')
        is_multiple = result.get('multiple', False)
        accumulated = result.get('accumulated', False)
        question_id = result.get('question_id')
        max_choices = result.get('max_choices')
        
        msg = f"{question}\n\n{subtitle}"
        if hint:
            msg += f"\n\n💡 {hint}"
        
        # Adicionar indicador de seleções múltiplas
        if is_multiple:
            if accumulated and context:
                # Mostrar quantas foram selecionadas
                current_answers = context.user_data.get('onboarding_answers', {})
                selected = current_answers.get(question_id, '')
                selected_list = selected.split(',') if selected else []
                count = len(selected_list)
                
                if count > 0:
                    # Buscar labels das opções selecionadas
                    selected_labels = []
                    for opt_id, opt_label in options:
                        if opt_id in selected_list:
                            # Extrair apenas o emoji e primeira palavra
                            label_short = opt_label.split()[0] if opt_label else opt_id
                            selected_labels.append(label_short)
                    
                    msg += f"\n\n✅ *Selecionadas ({count}"
                    if max_choices:
                        msg += f"/{max_choices}"
                    msg += f"):* {' '.join(selected_labels)}"
                
                msg += "\n\n_Clique em mais opções ou 'Próxima' para continuar_"
            elif max_choices:
                msg += f"\n\n_Escolha até {max_choices} opções_"
        
        if text_input:
            # Questão de texto livre
            if hasattr(update, 'callback_query') and update.callback_query:
                update.callback_query.edit_message_text(msg.strip(), parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(msg.strip(), parse_mode=ParseMode.MARKDOWN)
        else:
            # Questão com botões
            keyboard = []
            for opt_id, opt_label in options:
                keyboard.append([InlineKeyboardButton(
                    opt_label,
                    callback_data=f"quiz_{result.get('question_id')}_{opt_id}"
                )])
            
            # Adicionar botão "Próxima" para perguntas múltiplas
            if is_multiple:
                keyboard.append([InlineKeyboardButton(
                    "➡️ Próxima",
                    callback_data=f"quiz_next_{result.get('question_id')}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if hasattr(update, 'callback_query') and update.callback_query:
                update.callback_query.edit_message_text(
                    msg.strip(),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                update.message.reply_text(
                    msg.strip(),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
    
    def _handle_quiz_answer(self, update: Update, context: CallbackContext, data: str):
        """Processa resposta do quiz V2."""
        try:
            from app.services.onboarding_service_v2 import onboarding_v2
            
            query = update.callback_query
            user_id = self._get_user_id(query.from_user.id)
            
            logger.info("quiz_callback_received", data=data)
            
            # Parse: quiz_next_question_id ou quiz_question_id_answer
            if data.startswith("quiz_next_"):
                # Botão "Próxima": quiz_next_question_id
                is_next_button = True
                question_id = data.replace("quiz_next_", "")
            else:
                # Resposta normal: quiz_question_id_answer
                # Remover prefixo "quiz_"
                is_next_button = False
                remaining = data.replace("quiz_", "", 1)
                
                # Encontrar o question_id correto verificando contra as perguntas conhecidas
                question_id = None
                answer = None
                
                # IDs de perguntas conhecidos (em ordem de prioridade - mais longos primeiro)
                known_ids = ['communication_style', 'physical_activity', 'income_situation', 
                            'year_goals', 'life_areas', 'skills', 'blockers']
                
                for qid in known_ids:
                    if remaining.startswith(qid + "_"):
                        question_id = qid
                        answer = remaining[len(qid) + 1:]  # +1 para remover o underscore
                        break
                
                if not question_id:
                    logger.error("quiz_parse_failed", data=data, remaining=remaining)
                    return
            
            logger.info("quiz_button_type", is_next=is_next_button, question_id=question_id)
            
            if is_next_button:
                # Buscar a última resposta acumulada
                current_answers = context.user_data.get('onboarding_answers', {})
                accumulated = current_answers.get(question_id, '')
                
                logger.info("quiz_finalizing", question_id=question_id, accumulated=accumulated)
                
                # Salvar com is_final=True para avançar
                result = onboarding_v2.save_answer(
                    user_id, 
                    question_id, 
                    accumulated,  # Enviar tudo acumulado
                    current_answers,
                    is_final=True
                )
            else:
                # Buscar answers do context
                current_answers = context.user_data.get('onboarding_answers', {})
                
                logger.info("quiz_accumulating", question_id=question_id, answer=answer, is_final=False)
                
                # Verificar se é opção "custom" (personalizado)
                if answer == 'custom':
                    # Marcar estado para aguardar texto
                    context.user_data['onboarding_text_question'] = question_id
                    
                    # Editar mensagem pedindo texto
                    query.edit_message_text(
                        f"✏️ *Digite sua resposta personalizada:*\n\n_Envie como uma mensagem de texto_",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Salvar resposta com is_final=False (acumular)
                result = onboarding_v2.save_answer(
                    user_id, 
                    question_id, 
                    answer, 
                    current_answers,
                    is_final=False
                )
            
            # Atualizar answers no context
            if result.get('answers'):
                context.user_data['onboarding_answers'] = result['answers']
            
            if result.get('completed'):
                # Onboarding completo!
                msg = result.get('message', '✅ Perfil criado!')
                query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
                
                # Limpar context
                context.user_data.pop('onboarding_answers', None)
                context.user_data.pop('onboarding_text_question', None)
                
            else:
                # Próxima pergunta
                text_input = result.get('text_input', False)
                
                if text_input:
                    # Questão de texto - marcar estado
                    context.user_data['onboarding_text_question'] = result.get('question_id')
                
                self._send_onboarding_question(update, result, context)
                
        except Exception as e:
            logger.error("handle_quiz_answer_v2_failed", error=str(e), exc_info=True)
            query.edit_message_text("❌ Erro ao processar resposta. Tente /quiz novamente.")
    
    def cmd_energia(self, update: Update, context: CallbackContext):
        """Handler para /energia [1-10] - registrar energia."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "❌ *Uso:* /energia [1-10]\n\n"
                "_Exemplo: /energia 7_",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            level = int(context.args[0])
            if not 1 <= level <= 10:
                raise ValueError("Fora do range")
        except:
            update.message.reply_text("❌ Valor deve ser entre 1 e 10.")
            return
        
        try:
            self.supabase.table("checkins").insert({
                "user_id": user_id,
                "checkin_type": "energy",
                "value": level,
                "notes": f"Via Telegram /energia {level}"
            }).execute()
            
            energy_bar = "🟢" * level + "⚪" * (10 - level)
            
            update.message.reply_text(
                f"⚡ *Energia Registrada*\n\n"
                f"{energy_bar}\n"
                f"Nível: *{level}/10*",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_energia_failed", error=str(e))
            update.message.reply_text("❌ Erro ao registrar energia.")
    
    def cmd_humor(self, update: Update, context: CallbackContext):
        """Handler para /humor [texto ou emoji] - registrar humor."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "❌ *Uso:* /humor [como você está]\n\n"
                "_Exemplos:_\n"
                "/humor feliz\n"
                "/humor 😊\n"
                "/humor cansado mas produtivo",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        mood = " ".join(context.args)
        
        # Mapear para score
        mood_lower = mood.lower()
        score = 5  # default
        if any(w in mood_lower for w in ["feliz", "😊", "ótimo", "excelente", "🤩"]):
            score = 8
        elif any(w in mood_lower for w in ["triste", "😢", "mal", "péssimo"]):
            score = 3
        elif any(w in mood_lower for w in ["cansado", "😴", "tired"]):
            score = 4
        elif any(w in mood_lower for w in ["irritado", "😤", "estressado"]):
            score = 3
        elif any(w in mood_lower for w in ["empolgado", "animado", "motivated"]):
            score = 9
        
        try:
            self.supabase.table("checkins").insert({
                "user_id": user_id,
                "checkin_type": "mood",
                "value": score,
                "notes": mood
            }).execute()
            
            update.message.reply_text(
                f"😊 *Humor Registrado*\n\n"
                f"Você está: _{mood}_\n"
                f"Score: *{score}/10*",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_humor_failed", error=str(e))
            update.message.reply_text("❌ Erro ao registrar humor.")
    
    def cmd_projetos(self, update: Update, context: CallbackContext):
        """Handler para /projetos - listar projetos ativos."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            # Buscar projetos ativos
            result = self.supabase.table("projects")\
                .select("id, name, status, color, description")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if not result.data:
                update.message.reply_text(
                    "📁 *Projetos*\n\n"
                    "Nenhum projeto ativo encontrado.\n\n"
                    "_Use /projeto [nome] para criar um novo._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📁 *Projetos Ativos*\n\n"
            
            for proj in result.data:
                # Contar tarefas do projeto
                tasks_count = self.supabase.table("tasks")\
                    .select("id", count="exact")\
                    .eq("project_id", proj["id"])\
                    .in_("status", ["todo", "in_progress"])\
                    .execute()
                
                count = tasks_count.count or 0
                icon = "📁"
                message += f"{icon} *{proj['name']}*\n"
                message += f"   _{count} tarefa{'s' if count != 1 else ''} pendente{'s' if count != 1 else ''}_\n\n"
            
            message += "_Use /projeto [nome] para ver detalhes_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_projetos_failed", error=str(e))
            update.message.reply_text("❌ Erro ao listar projetos.")
    
    def cmd_projeto(self, update: Update, context: CallbackContext):
        """Handler para /projeto [nome] - criar ou ver projeto."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "📁 *Projetos*\n\n"
                "Uso:\n"
                "• `/projeto [nome]` - Ver ou criar projeto\n"
                "• `/projetos` - Listar projetos ativos\n",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        name = " ".join(context.args)
        
        try:
            # Verificar se projeto já existe
            existing = self.supabase.table("projects")\
                .select("*")\
                .eq("user_id", user_id)\
                .ilike("name", name)\
                .execute()
            
            if existing.data:
                proj = existing.data[0]
                
                # Buscar tarefas do projeto
                tasks = self.supabase.table("tasks")\
                    .select("id, title, status, priority")\
                    .eq("project_id", proj["id"])\
                    .in_("status", ["todo", "in_progress"])\
                    .order("priority", desc=True)\
                    .limit(5)\
                    .execute()
                
                message = f"📁 *{proj['name']}*\n"
                if proj.get("description"):
                    message += f"_{proj['description']}_\n"
                message += f"\nStatus: {proj['status']}\n\n"
                
                if tasks.data:
                    message += "📋 *Tarefas:*\n"
                    for task in tasks.data:
                        status_icon = "⏳" if task["status"] == "todo" else "🔄"
                        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "⚪")
                        message += f"  {status_icon} {priority_icon} {task['title']}\n"
                else:
                    message += "_Nenhuma tarefa pendente_"
                
                update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            else:
                # Criar novo projeto
                new_project = self.supabase.table("projects").insert({
                    "user_id": user_id,
                    "name": name,
                    "status": "active"
                }).execute()
                
                update.message.reply_text(
                    f"✅ *Projeto Criado*\n\n"
                    f"📁 *{name}*\n\n"
                    f"_Use /task [título] para adicionar tarefas_",
                    parse_mode=ParseMode.MARKDOWN
                )
            
        except Exception as e:
            logger.error("cmd_projeto_failed", error=str(e))
            update.message.reply_text("❌ Erro ao processar projeto.")

    def cmd_agenda(self, update: Update, context: CallbackContext):
        """Handler para /agenda - ver eventos do dia."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            # Verificar se tem Google conectado
            from app.services.google_auth_service import google_auth_service
            from app.services.google_calendar_service import google_calendar_service
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                connected = loop.run_until_complete(google_auth_service.is_connected(user_id))
            finally:
                loop.close()
            
            if not connected:
                update.message.reply_text(
                    "📆 *Agenda*\n\n"
                    "⚠️ Google Calendar não conectado.\n\n"
                    "Para ver sua agenda, conecte sua conta Google:\n"
                    f"🔗 Acesse: /connect",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Buscar eventos
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                events = loop.run_until_complete(
                    google_calendar_service.get_today_events(user_id)
                )
            finally:
                loop.close()
            
            if not events:
                update.message.reply_text(
                    "📆 *Agenda de Hoje*\n\n"
                    "Nenhum evento encontrado! ✨\n\n"
                    "_Dia livre para focar no que importa._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📆 *Agenda de Hoje*\n\n"
            
            for event in events:
                time_str = "Dia inteiro" if event.get("all_day") else event.get("start", "")[:5]
                title = event.get("title", "Sem título")
                message += f"• *{time_str}* - {title}\n"
            
            message += f"\n_Total: {len(events)} evento{'s' if len(events) > 1 else ''}_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_agenda_failed", error=str(e))
            update.message.reply_text(
                "📆 *Agenda*\n\n"
                "❌ Erro ao buscar agenda.\n"
                "_Verifique a conexão com Google Calendar._",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def cmd_rotina(self, update: Update, context: CallbackContext):
        """Handler para /rotina - executar rotina manualmente."""
        user = update.effective_user
        
        if not self._is_owner(user.id):
            return
        
        user_id = self._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        # Verificar argumento
        if not context.args:
            keyboard = [
                [
                    InlineKeyboardButton("☀️ Manhã", callback_data="rotina_morning"),
                    InlineKeyboardButton("🌙 Noite", callback_data="rotina_night"),
                ],
                [
                    InlineKeyboardButton("📅 Semanal", callback_data="rotina_weekly"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                "⏰ *Rotinas*\n\n"
                "Qual rotina você quer executar?",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        routine_type = context.args[0].lower()
        self._execute_routine(update, user_id, routine_type)
    
    def _execute_routine(self, update: Update, user_id: str, routine_type: str):
        """Executa uma rotina específica."""
        from app.services.scheduler_service import scheduler_service
        
        valid_types = ["morning", "night", "weekly", "manhã", "noite", "semanal"]
        
        # Normalizar tipo
        type_map = {"manhã": "morning", "noite": "night", "semanal": "weekly"}
        routine_type = type_map.get(routine_type, routine_type)
        
        if routine_type not in ["morning", "night", "weekly"]:
            update.message.reply_text(
                "❌ Tipo inválido. Use: morning, night ou weekly",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        update.message.reply_text(
            f"⏳ Executando rotina *{routine_type}*...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            success = scheduler_service.run_job_now(routine_type, user_id)
            
            if success:
                update.message.reply_text(
                    f"✅ Rotina *{routine_type}* executada!",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text("❌ Falha ao executar rotina.")
                
        except Exception as e:
            logger.error("execute_routine_failed", error=str(e))
            update.message.reply_text("❌ Erro ao executar rotina.")
    
    def cmd_status(self, update: Update, context: CallbackContext):
        """Handler para /status - Exibir status RPG do usuário."""
        if not self._is_owner(update.effective_user.id):
            return
        
        user_id = self._get_user_id(update.effective_user.id)
        if not user_id:
            update.message.reply_text("❌ Você precisa fazer /start primeiro")
            return
        
        logger.info("command_status", user_id=user_id)
        
        try:
            from app.services.gamification_service import gamification
            
            username = update.effective_user.first_name or "Igor"
            status_msg = gamification.format_status_message(user_id, username)
            
            update.message.reply_text(status_msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("status_failed", error=str(e))
            update.message.reply_text("❌ Erro ao carregar status")
    
    def cmd_quiz(self, update: Update, context: CallbackContext):
        """Handler para /quiz - Iniciar onboarding V2 (Life Hacker)."""
        if not self._is_owner(update.effective_user.id):
            return
        
        user_id = self._get_user_id(update.effective_user.id)
        if not user_id:
            update.message.reply_text("❌ Você precisa fazer /start primeiro")
            return
        
        logger.info("command_quiz_v2", user_id=user_id)
        
        # LIMPAR CONTEXT ANTERIOR (forçar início do zero)
        context.user_data.pop('onboarding_answers', None)
        context.user_data.pop('onboarding_text_question', None)
        context.user_data.pop('onboarding_step', None)
        
        try:
            from app.services.onboarding_service_v2 import onboarding_v2
            
            # Iniciar onboarding V2
            result = onboarding_v2.start_onboarding(user_id)
            
            if not result or result.get('completed'):
                update.message.reply_text("❌ Erro ao iniciar quiz")
                return
            
            # Montar mensagem com primeira pergunta (life hacker style)
            question = result.get('question', '')
            subtitle = result.get('subtitle', '')
            options = result.get('options', [])
            step = result.get('step', 1)
            total = result.get('total_steps', 7)
            is_multiple = result.get('multiple', False)
            
            # Criar botões inline
            keyboard = []
            for opt_id, opt_label in options:
                keyboard.append([InlineKeyboardButton(
                    opt_label,
                    callback_data=f"quiz_{result.get('question_id')}_{opt_id}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Mensagem life hacker RPG
            msg = f"""{question}

{subtitle}
"""
            
            if is_multiple:
                max_choices = result.get('max_choices', 1)
                if max_choices > 1:
                    msg += f"\n_Você pode escolher até {max_choices}._"
            
            update.message.reply_text(
                msg.strip(),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error("quiz_v2_failed", error=str(e), exc_info=True)
            update.message.reply_text("❌ Erro ao iniciar quiz. Tente novamente.")
    
    # ==========================================
    # PERFIL VIVO - EDIÇÃO
    # ==========================================
    
    def cmd_editar(self, update: Update, context: CallbackContext):
        """Handler para /editar - Menu de edição do perfil."""
        if not self._is_owner(update.effective_user.id):
            return
        
        user_id = self._get_user_id(update.effective_user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro")
            return
        
        # Verificar subcomando
        if not context.args:
            # Menu principal
            update.message.reply_text(
                "✏️ *Editar Perfil*\n\n"
                "Seu perfil é vivo. Nada é definitivo.\n\n"
                "*O que quer editar?*\n\n"
                "• /editar areas - Áreas prioritárias\n"
                "• /editar metas - Meta principal\n"
                "• /editar habilidades - Skills em desenvolvimento\n"
                "• /editar corpo - Exercício e energia\n"
                "• /editar renda - Fontes de renda\n\n"
                "_Pessoas evoluem. Personagens também._",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        subcommand = context.args[0].lower()
        
        # TODO: Implementar cada tipo de edição
        # Por ora, apenas confirmar
        update.message.reply_text(
            f"🔧 Edição de {subcommand} será implementada em breve.\n\n"
            "Use /quiz para refazer o onboarding completo por enquanto.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ==========================================
    # QUESTS
    # ==========================================
    
    def cmd_quest(self, update: Update, context: CallbackContext):
        """Handler para /quest - Sistema de quests adaptativas."""
        if not self._is_owner(update.effective_user.id):
            return
        
        user_id = self._get_user_id(update.effective_user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro")
            return
        
        try:
            from app.services.quest_service import quest_service
            
            # Verificar tipo de quest
            quest_type = context.args[0].lower() if context.args else 'daily'
            
            if quest_type == 'semanal' or quest_type == 'weekly':
                quest = quest_service.get_weekly_quest(user_id)
                msg = f"🎯 *Quest Semanal*\n\n*{quest['title']}*\n\n{quest['description']}\n\n💎 Recompensa: +{quest['xp']} XP"
            
            elif quest_type == 'reflexiva' or quest_type == 'reflective':
                quest = quest_service.get_reflective_quest(user_id)
                msg = f"🧠 *Quest Reflexiva*\n\n{quest['description']}\n\n💎 Recompensa: +{quest['xp']} XP"
            
            else:
                # Quest diária ADAPTATIVA
                quest = quest_service.get_daily_quest(user_id)
                
                # Formato completo do painel de quests
                msg = f"""🎯 *QUESTS DE HOJE*

⚡ *{quest['title']}*
{quest['description']}

💎 Recompensa: +{quest['xp']} XP
🎯 Atributo: {quest['attribute'].title()}

━━━━━━━━━━━━━━━━━━

_Digite "feito" ao concluir_
_Use /quest reflexiva para uma pergunta poderosa_
"""
            
            update.message.reply_text(msg.strip(), parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("quest_failed", error=str(e), exc_info=True)
            update.message.reply_text("❌ Erro ao carregar quest")
    
    def cmd_atributos(self, update: Update, context: CallbackContext):
        """Handler para /atributos - Detalhes dos atributos."""
        if not self._is_owner(update.effective_user.id):
            return
        
        user_id = self._get_user_id(update.effective_user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro")
            return
        
        try:
            from app.services.gamification_service import gamification
            attributes = gamification.get_attributes(user_id)
            
            msg = f"""⚔️ *ATRIBUTOS PRINCIPAIS*

Os 4 pilares do seu progresso:

⚡ *Energia: {attributes.get('energy', 50)}%*
Corpo, sono, movimento
• Sobe com: atividade física, descanso, respiração
• Cai com: sedentarismo, noites mal dormidas

🎯 *Foco: {attributes.get('focus', 50)}%*
Clareza mental, atenção
• Sobe com: planejamento, tarefas concluídas
• Cai com: excesso de estímulos, procrastinação

🛠️ *Execução: {attributes.get('execution', 50)}%*
Consistência e ação
• Sobe com: quests completadas, ações registradas
• Cai com: dias sem ação

💰 *Renda: {attributes.get('income', 50)}%*
Saúde financeira
• Sobe com: fontes ativas, ações financeiras
• Cai com: estagnação prolongada

━━━━━━━━━━━━━━━━━━
Use /quest para melhorar seus atributos
"""
            
            update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("atributos_failed", error=str(e))
            update.message.reply_text("❌ Erro ao carregar atributos")
    
    def cmd_conquistas(self, update: Update, context: CallbackContext):
        """Handler para /conquistas - Listar conquistas."""
        if not self._is_owner(update.effective_user.id):
            return
        
        user_id = self._get_user_id(update.effective_user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro")
            return
        
        try:
            from app.services.gamification_service import gamification
            
            # Buscar conquistas
            achievements = gamification.supabase.table('achievements')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('unlocked_at', desc=True)\
                .execute()
            
            if not achievements.data:
                update.message.reply_text(
                    "🏅 *CONQUISTAS*\n\n"
                    "Você ainda não desbloqueou nenhuma conquista.\n\n"
                    "Complete o onboarding, faça quests e mantenha consistência!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Formatar lista
            achievements_list = []
            for ach in achievements.data:
                title = ach.get('title', 'Conquista')
                desc = ach.get('description', '')
                xp = ach.get('xp_reward', 0)
                achievements_list.append(f"🏅 *{title}*\n_{desc}_\n+{xp} XP")
            
            msg = f"""🏅 *SUAS CONQUISTAS*

Total: {len(achievements.data)}

━━━━━━━━━━━━━━━━━━

{chr(10).join(achievements_list[:10])}

━━━━━━━━━━━━━━━━━━
Continue evoluindo! 🔥
"""
            
            update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("conquistas_failed", error=str(e))
            update.message.reply_text("❌ Erro ao carregar conquistas")
    
    def cmd_checkin_daily(self, update: Update, context: CallbackContext):
        """Comando /checkin - Check-in diário simplificado."""
        try:
            user_id = str(update.effective_user.id)
            
            from app.services.checkin_service import checkin_service
            
            # Se tem argumento (número), processar energia
            if context.args:
                try:
                    energy = int(context.args[0])
                    result = checkin_service.process_daily_energy(user_id, energy)
                    
                    update.message.reply_text(result['message'])
                    
                except ValueError:
                    update.message.reply_text("❌ Use: /checkin <número de 0 a 100>")
            else:
                # Mostrar mensagem de check-in e marcar estado
                msg = checkin_service.get_daily_checkin_message()
                update.message.reply_text(msg)
                # Marcar que aguarda resposta de energia
                context.user_data['awaiting_checkin_energy'] = True
            
        except Exception as e:
            logger.error("checkin_daily_failed", error=str(e))
            update.message.reply_text("❌ Erro ao processar check-in")
    
    def cmd_revisar(self, update: Update, context: CallbackContext):
        """Comando /revisar - Revisão de perfil evolutiva."""
        try:
            user_id = str(update.effective_user.id)
            
            from app.services.profile_editor_service import profile_editor
            
            result = profile_editor.start_profile_review(user_id)
            
            if result['success']:
                update.message.reply_text(result['message'])
                
                # Marcar que está em revisão (para capturar próxima resposta)
                context.user_data['in_profile_review'] = True
            else:
                update.message.reply_text(result['message'])
            
        except Exception as e:
            logger.error("revisar_failed", error=str(e))
            update.message.reply_text("❌ Erro ao iniciar revisão de perfil")
    
    # ==========================================
    # ERROR HANDLER
    # ==========================================
    
    def handle_error(self, update: Update, context: CallbackContext):
        """Handler para erros."""
        logger.error(
            "telegram_error",
            error=str(context.error),
            update=str(update) if update else None,
            exc_info=context.error
        )
        
        if update and update.effective_message:
            update.effective_message.reply_text(
                "❌ Ocorreu um erro. Tente novamente."
            )
    
    # ==========================================
    # BOT SETUP
    # ==========================================
    
    def create_updater(self) -> Updater:
        """Cria e configura o Updater do bot."""
        self.updater = Updater(
            token=settings.TELEGRAM_BOT_TOKEN,
            use_context=True
        )
        
        dp = self.updater.dispatcher
        
        # Comandos básicos
        dp.add_handler(CommandHandler("start", self.cmd_start))
        dp.add_handler(CommandHandler("help", self.cmd_help))
        dp.add_handler(CommandHandler("status", self.cmd_status))
        dp.add_handler(CommandHandler("quiz", self.cmd_quiz))
        dp.add_handler(CommandHandler("inbox", self.cmd_inbox))
        dp.add_handler(CommandHandler("tasks", self.cmd_tasks))
        dp.add_handler(CommandHandler("task", self.cmd_task))
        dp.add_handler(CommandHandler("done", self.cmd_done))
        dp.add_handler(CommandHandler("checkin", self.cmd_checkin_daily))
        dp.add_handler(CommandHandler("resumo", self.cmd_resumo))
        dp.add_handler(CommandHandler("energia", self.cmd_energia))
        dp.add_handler(CommandHandler("humor", self.cmd_humor))
        dp.add_handler(CommandHandler("agenda", self.cmd_agenda))
        dp.add_handler(CommandHandler("rotina", self.cmd_rotina))
        dp.add_handler(CommandHandler("projetos", self.cmd_projetos))
        dp.add_handler(CommandHandler("projeto", self.cmd_projeto))
        
        # Perfil Vivo - Edição e Revisão
        dp.add_handler(CommandHandler("editar", self.cmd_editar))
        dp.add_handler(CommandHandler("revisar", self.cmd_revisar))
        
        # Quests e Atributos
        dp.add_handler(CommandHandler("quest", self.cmd_quest))
        dp.add_handler(CommandHandler("atributos", self.cmd_atributos))
        dp.add_handler(CommandHandler("conquistas", self.cmd_conquistas))
        
        # Registrar comandos estendidos (Gmail, Drive, Content, Finance, Memory, Insights)
        try:
            from app.services.bot_commands_extended import register_extended_commands
            self._extended_commands = register_extended_commands(self)
            logger.info("extended_commands_loaded")
        except Exception as e:
            logger.warning("extended_commands_load_failed", error=str(e))
        
        # Callbacks de botões inline
        dp.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Mensagens de texto (deve ser o último)
        dp.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.handle_message)
        )
        
        # Error handler
        dp.add_error_handler(self.handle_error)
        
        logger.info("telegram_bot_handlers_configured")
        
        return self.updater
    
    def start_polling(self):
        """Inicia o bot em modo polling."""
        if not self.updater:
            self.create_updater()
        
        logger.info("starting_telegram_bot_polling")
        
        self.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        logger.info("telegram_bot_started")
        
        # Mantém rodando até Ctrl+C
        self.updater.idle()
    
    def stop(self):
        """Para o bot."""
        if self.updater:
            self.updater.stop()
            logger.info("telegram_bot_stopped")


# Instância global
bot_handler = TelegramBotHandler()
