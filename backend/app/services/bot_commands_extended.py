"""
TB Personal OS - Extended Bot Commands
Comandos adicionais para Gmail, Drive, Content, Finance, Memory e Insights
"""

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import structlog
import asyncio
from typing import Optional
from datetime import datetime

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ExtendedBotCommands:
    """
    Comandos estendidos do bot.
    Adiciona funcionalidades para os novos módulos.
    """
    
    def __init__(self, bot_handler):
        self.bot = bot_handler
    
    # ==========================================
    # GMAIL COMMANDS
    # ==========================================
    
    def cmd_emails(self, update: Update, context: CallbackContext):
        """Handler para /emails - ver emails não lidos."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.gmail_service import gmail_service
            from app.services.google_auth_service import google_auth_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Verificar conexão
                connected = loop.run_until_complete(google_auth_service.is_connected(user_id))
                
                if not connected:
                    update.message.reply_text(
                        "📧 *Emails*\n\n"
                        "⚠️ Google não conectado.\n"
                        "Use /connect para conectar sua conta.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Buscar emails não lidos
                emails = loop.run_until_complete(gmail_service.get_unread_emails(user_id, max_results=5))
            finally:
                loop.close()
            
            if not emails:
                update.message.reply_text(
                    "📧 *Emails*\n\n"
                    "✅ Nenhum email não lido!\n\n"
                    "_Sua inbox está em dia._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📧 *Emails Não Lidos*\n\n"
            
            for i, email in enumerate(emails, 1):
                sender = email.get("from", "Desconhecido")
                # Simplificar sender
                if "<" in sender:
                    sender = sender.split("<")[0].strip()
                sender = sender[:25]
                
                subject = email.get("subject", "Sem assunto")[:40]
                
                message += f"{i}. *{sender}*\n"
                message += f"   _{subject}_\n\n"
            
            message += f"_Total: {len(emails)} não lidos_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_emails_failed", error=str(e))
            update.message.reply_text(
                "📧 *Emails*\n\n"
                "❌ Erro ao buscar emails.\n"
                "_Verifique a conexão com Google._",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ==========================================
    # CONTENT COMMANDS
    # ==========================================
    
    def cmd_ideia(self, update: Update, context: CallbackContext):
        """Handler para /ideia [texto] - criar ideia de conteúdo."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "💡 *Nova Ideia de Conteúdo*\n\n"
                "Uso: `/ideia [sua ideia]`\n\n"
                "_Exemplo:_\n"
                "/ideia Post sobre produtividade para empreendedores",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        idea_text = " ".join(context.args)
        
        try:
            from app.services.content_service import content_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                idea = loop.run_until_complete(content_service.create_idea(
                    user_id=user_id,
                    title=idea_text[:100],
                    description=idea_text if len(idea_text) > 100 else None,
                    source="telegram"
                ))
            finally:
                loop.close()
            
            update.message.reply_text(
                f"💡 *Ideia Salva!*\n\n"
                f"_{idea_text[:100]}_\n\n"
                f"ID: `{idea['id'][:8]}`\n\n"
                f"Use /ideias para ver todas as ideias.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_ideia_failed", error=str(e))
            update.message.reply_text("❌ Erro ao salvar ideia.")
    
    def cmd_ideias(self, update: Update, context: CallbackContext):
        """Handler para /ideias - listar ideias de conteúdo."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.content_service import content_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                ideas = loop.run_until_complete(content_service.get_ideas(
                    user_id=user_id,
                    status="new",
                    limit=10
                ))
            finally:
                loop.close()
            
            if not ideas:
                update.message.reply_text(
                    "💡 *Ideias de Conteúdo*\n\n"
                    "Nenhuma ideia salva.\n\n"
                    "_Use /ideia [texto] para adicionar._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "💡 *Ideias de Conteúdo*\n\n"
            
            for i, idea in enumerate(ideas, 1):
                title = idea.get("title", "")[:50]
                platform = idea.get("platform", "geral")
                message += f"{i}. _{title}_\n"
                message += f"   📱 {platform}\n\n"
            
            message += f"_Total: {len(ideas)} ideias_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_ideias_failed", error=str(e))
            update.message.reply_text("❌ Erro ao listar ideias.")
    
    # ==========================================
    # FINANCE COMMANDS
    # ==========================================
    
    def cmd_financas(self, update: Update, context: CallbackContext):
        """Handler para /financas - resumo financeiro."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.finance_service import finance_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                summary = loop.run_until_complete(finance_service.get_summary(user_id))
            finally:
                loop.close()
            
            income = summary.get("total_income", 0)
            expense = summary.get("total_expense", 0)
            balance = summary.get("balance", 0)
            
            # Formatar valores
            def fmt(val):
                return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            balance_emoji = "🟢" if balance >= 0 else "🔴"
            
            message = (
                f"💰 *Resumo Financeiro*\n"
                f"_{summary.get('period', {}).get('start', '')[:10]} a {summary.get('period', {}).get('end', '')[:10]}_\n\n"
                f"📈 Entradas: *{fmt(income)}*\n"
                f"📉 Saídas: *{fmt(expense)}*\n"
                f"{balance_emoji} Saldo: *{fmt(balance)}*\n\n"
                f"_Transações: {summary.get('transactions_count', 0)}_"
            )
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_financas_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar dados financeiros.")
    
    def cmd_entrada(self, update: Update, context: CallbackContext):
        """Handler para /entrada [valor] [descrição] - registrar entrada."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if len(context.args) < 2:
            update.message.reply_text(
                "💵 *Registrar Entrada*\n\n"
                "Uso: `/entrada [valor] [descrição]`\n\n"
                "_Exemplos:_\n"
                "/entrada 1500 Freelance site\n"
                "/entrada 500.50 Consultoria",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            amount = float(context.args[0].replace(",", "."))
            description = " ".join(context.args[1:])
        except ValueError:
            update.message.reply_text("❌ Valor inválido. Use números.")
            return
        
        try:
            from app.services.finance_service import finance_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                transaction = loop.run_until_complete(finance_service.quick_transaction(
                    user_id=user_id,
                    amount=amount,
                    description=description,
                    transaction_type="income"
                ))
            finally:
                loop.close()
            
            update.message.reply_text(
                f"✅ *Entrada Registrada*\n\n"
                f"💵 *R$ {amount:,.2f}*\n"
                f"📝 {description}\n\n"
                f"_ID: {transaction['id'][:8]}_",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_entrada_failed", error=str(e))
            update.message.reply_text("❌ Erro ao registrar entrada.")
    
    def cmd_saida(self, update: Update, context: CallbackContext):
        """Handler para /saida [valor] [descrição] - registrar saída."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if len(context.args) < 2:
            update.message.reply_text(
                "💸 *Registrar Saída*\n\n"
                "Uso: `/saida [valor] [descrição]`\n\n"
                "_Exemplos:_\n"
                "/saida 150 Almoço de negócios\n"
                "/saida 89.90 Software mensal",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            amount = float(context.args[0].replace(",", "."))
            description = " ".join(context.args[1:])
        except ValueError:
            update.message.reply_text("❌ Valor inválido. Use números.")
            return
        
        try:
            from app.services.finance_service import finance_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                transaction = loop.run_until_complete(finance_service.quick_transaction(
                    user_id=user_id,
                    amount=amount,
                    description=description,
                    transaction_type="expense"
                ))
            finally:
                loop.close()
            
            update.message.reply_text(
                f"✅ *Saída Registrada*\n\n"
                f"💸 *R$ {amount:,.2f}*\n"
                f"📝 {description}\n\n"
                f"_ID: {transaction['id'][:8]}_",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_saida_failed", error=str(e))
            update.message.reply_text("❌ Erro ao registrar saída.")
    
    # ==========================================
    # MEMORY COMMANDS
    # ==========================================
    
    def cmd_lembrar(self, update: Update, context: CallbackContext):
        """Handler para /lembrar [texto] - salvar memória."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "🧠 *Salvar Memória*\n\n"
                "Uso: `/lembrar [informação]`\n\n"
                "_Exemplos:_\n"
                "/lembrar Senha do WiFi é XYZ123\n"
                "/lembrar Aniversário da mãe: 15/03",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        memory_text = " ".join(context.args)
        
        try:
            from app.services.memory_service import memory_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                memory = loop.run_until_complete(memory_service.remember(
                    user_id=user_id,
                    content=memory_text,
                    category="general",
                    source="telegram"
                ))
            finally:
                loop.close()
            
            update.message.reply_text(
                f"🧠 *Memória Salva!*\n\n"
                f"_{memory_text[:100]}_\n\n"
                f"Use /buscar para encontrar.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_lembrar_failed", error=str(e))
            update.message.reply_text("❌ Erro ao salvar memória.")
    
    def cmd_buscar(self, update: Update, context: CallbackContext):
        """Handler para /buscar [termo] - buscar memórias."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        if not context.args:
            update.message.reply_text(
                "🔍 *Buscar Memórias*\n\n"
                "Uso: `/buscar [termo]`\n\n"
                "_Exemplo: /buscar senha_",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        query = " ".join(context.args)
        
        try:
            from app.services.memory_service import memory_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                memories = loop.run_until_complete(memory_service.search_memories(
                    user_id=user_id,
                    query=query,
                    limit=5
                ))
            finally:
                loop.close()
            
            if not memories:
                update.message.reply_text(
                    f"🔍 *Busca: {query}*\n\n"
                    f"Nenhum resultado encontrado.\n\n"
                    f"_Use /lembrar para salvar informações._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = f"🔍 *Busca: {query}*\n\n"
            
            for i, mem in enumerate(memories, 1):
                content = mem.get("content", "")[:80]
                date = mem.get("created_at", "")[:10]
                message += f"{i}. _{content}_\n"
                message += f"   📅 {date}\n\n"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_buscar_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar.")
    
    # ==========================================
    # INSIGHTS COMMANDS
    # ==========================================
    
    def cmd_insights(self, update: Update, context: CallbackContext):
        """Handler para /insights - ver insights e recomendações."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.insights_service import insights_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                productivity = loop.run_until_complete(
                    insights_service.get_productivity_score(user_id, days=7)
                )
                recommendations = loop.run_until_complete(
                    insights_service.generate_recommendations(user_id)
                )
            finally:
                loop.close()
            
            score = productivity.get("score", 0)
            level = productivity.get("label", "")
            
            # Score visual
            score_bar = "🟢" * (score // 10) + "⚪" * (10 - score // 10)
            
            message = (
                f"📊 *Insights*\n\n"
                f"*Produtividade:* {level}\n"
                f"{score_bar} *{score}/100*\n\n"
            )
            
            # Métricas
            metrics = productivity.get("metrics", {})
            message += (
                f"📋 Tarefas: {metrics.get('completed_tasks', 0)}/{metrics.get('total_tasks', 0)}\n"
                f"✅ Taxa: {metrics.get('completion_rate', 0)}%\n"
                f"⏰ No prazo: {metrics.get('on_time_rate', 0)}%\n\n"
            )
            
            # Recomendações
            if recommendations:
                message += "*💡 Recomendações:*\n"
                for rec in recommendations[:3]:
                    emoji = {"urgent": "🔴", "warning": "🟠", "health": "🏃", "productivity": "📈", "positive": "✨"}.get(rec.get("type"), "💡")
                    message += f"{emoji} {rec.get('message', '')[:60]}\n"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_insights_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar insights.")
    
    # ==========================================
    # AUTONOMY COMMANDS
    # ==========================================
    
    def cmd_autonomia(self, update: Update, context: CallbackContext):
        """Handler para /autonomia [1-5] - ver ou definir nível de autonomia."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.autonomy_service import autonomy_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if not context.args:
                # Mostrar nível atual
                try:
                    level = loop.run_until_complete(
                        autonomy_service.get_user_autonomy_level(user_id)
                    )
                finally:
                    loop.close()
                
                description = autonomy_service.get_level_description(level)
                
                message = (
                    f"🤖 *Nível de Autonomia*\n\n"
                    f"Atual: *{description['name']}* ({level}/5)\n\n"
                    f"_{description['description']}_\n\n"
                    f"*Exemplos:*\n"
                )
                for ex in description.get("examples", [])[:3]:
                    message += f"• {ex}\n"
                
                message += f"\n_Use /autonomia [1-5] para alterar_"
                
                update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Definir novo nível
            try:
                new_level = int(context.args[0])
                if not 1 <= new_level <= 5:
                    raise ValueError()
            except:
                update.message.reply_text("❌ Nível deve ser entre 1 e 5.")
                return
            
            try:
                loop.run_until_complete(
                    autonomy_service.set_user_autonomy_level(user_id, new_level)
                )
            finally:
                loop.close()
            
            description = autonomy_service.get_level_description(new_level)
            
            update.message.reply_text(
                f"✅ *Autonomia Atualizada*\n\n"
                f"Novo nível: *{description['name']}* ({new_level}/5)\n\n"
                f"_{description['description']}_",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_autonomia_failed", error=str(e))
            update.message.reply_text("❌ Erro ao processar autonomia.")
    
    # ==========================================
    # HEALTH COMMANDS
    # ==========================================
    
    def cmd_saude(self, update: Update, context: CallbackContext):
        """Handler para /saude - resumo de saúde."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.health_service import health_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                summary = loop.run_until_complete(
                    health_service.get_health_summary(user_id, period_days=7)
                )
            finally:
                loop.close()
            
            # Formatar resumo
            message = "🏥 *Resumo de Saúde* (7 dias)\n\n"
            
            # Streak
            streak = summary.get("streak", {})
            message += f"🔥 Streak: *{streak.get('current_streak', 0)}* dias\n"
            message += f"🏆 Recorde: {streak.get('max_streak', 0)} dias\n\n"
            
            # Médias
            averages = summary.get("averages", {})
            if averages:
                message += "📊 *Médias*:\n"
                metric_names = {
                    "sleep_hours": "💤 Sono",
                    "energy": "⚡ Energia", 
                    "mood": "😊 Humor",
                    "productivity": "📈 Produtividade"
                }
                
                for key, label in metric_names.items():
                    if key in averages:
                        val = averages[key]
                        if key == "sleep_hours":
                            message += f"{label}: {val:.1f}h\n"
                        else:
                            message += f"{label}: {val:.1f}/10\n"
                message += "\n"
            
            # Insights
            insights = summary.get("insights", [])
            if insights:
                message += "*Insights*:\n"
                for insight in insights[:3]:
                    message += f"{insight}\n"
            
            message += f"\n_Checkins: {summary.get('total_checkins', 0)}_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_saude_failed", error=str(e))
            update.message.reply_text(
                "🏥 *Saúde*\n\n"
                "❌ Erro ao buscar dados.\n"
                "_Faça check-ins diários com /checkin_",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def cmd_checkin_health(self, update: Update, context: CallbackContext):
        """Handler para /checkin - fazer check-in de saúde."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        # Sem args, mostrar menu
        if not context.args:
            message = (
                "📝 *Check-in de Saúde*\n\n"
                "Formate: `/checkin tipo dados`\n\n"
                "*Tipos disponíveis:*\n"
                "• `morning` - Checkin matinal\n"
                "• `evening` - Checkin noturno\n"
                "• `mood` - Registro de humor\n\n"
                "*Exemplos:*\n"
                "`/checkin morning sono=7.5 energia=8`\n"
                "`/checkin mood humor=7 nota=\"Dia produtivo\"`\n\n"
                "_Ou envie mensagem natural: \"Dormi 7h, energia 8\"_"
            )
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            return
        
        try:
            checkin_type = context.args[0].lower()
            valid_types = ["morning", "evening", "mood", "health", "exercise"]
            
            if checkin_type not in valid_types:
                update.message.reply_text(
                    f"❌ Tipo inválido.\nVálidos: {', '.join(valid_types)}"
                )
                return
            
            # Parsear dados
            data = {}
            raw_text = " ".join(context.args[1:])
            
            # Formato: chave=valor
            import re
            pairs = re.findall(r'(\w+)=(["\']?[\w\s\.]+["\']?)', raw_text)
            
            for key, value in pairs:
                value = value.strip('"\'')
                # Tentar converter para número
                try:
                    if '.' in value:
                        data[key] = float(value)
                    else:
                        data[key] = int(value)
                except:
                    data[key] = value
            
            if not data:
                update.message.reply_text(
                    "❌ Dados não reconhecidos.\n"
                    "Use formato: `chave=valor`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            from app.services.health_service import health_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    health_service.create_checkin(user_id, checkin_type, data)
                )
            finally:
                loop.close()
            
            update.message.reply_text(
                f"✅ *Check-in Registrado!*\n\n"
                f"Tipo: `{checkin_type}`\n"
                f"Dados: {len(data)} campos\n\n"
                f"_Continue assim! 💪_",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error("cmd_checkin_health_failed", error=str(e))
            update.message.reply_text("❌ Erro ao salvar check-in.")
    
    def cmd_metas(self, update: Update, context: CallbackContext):
        """Handler para /metas - ver metas de saúde."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.health_service import health_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                goals = loop.run_until_complete(
                    health_service.get_health_goals(user_id)
                )
            finally:
                loop.close()
            
            if not goals:
                update.message.reply_text(
                    "🎯 *Metas de Saúde*\n\n"
                    "Você ainda não tem metas.\n\n"
                    "_Use a API para criar metas._",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "🎯 *Metas de Saúde*\n\n"
            
            icons = {
                "sleep": "💤", "steps": "👟", "water": "💧",
                "exercise": "🏃", "meditation": "🧘"
            }
            
            for goal in goals[:5]:
                gtype = goal.get("goal_type", "")
                icon = icons.get(gtype, "📌")
                target = goal.get("target_value", 0)
                unit = goal.get("unit", "")
                
                message += f"{icon} *{gtype.title()}*: {target} {unit}\n"
                if goal.get("description"):
                    message += f"   _{goal['description'][:40]}_\n"
                message += "\n"
            
            message += f"_Total: {len(goals)} metas ativas_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_metas_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar metas.")
    
    def cmd_correlacoes(self, update: Update, context: CallbackContext):
        """Handler para /correlacoes - ver correlações de saúde."""
        user = update.effective_user
        
        if not self.bot._is_owner(user.id):
            return
        
        user_id = self.bot._get_user_id(user.id)
        if not user_id:
            update.message.reply_text("❌ Execute /start primeiro.")
            return
        
        try:
            from app.services.health_service import health_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                correlations = loop.run_until_complete(
                    health_service.get_correlations(user_id)
                )
            finally:
                loop.close()
            
            if not correlations:
                update.message.reply_text(
                    "📊 *Correlações de Saúde*\n\n"
                    "Ainda não há correlações.\n\n"
                    "_Continue fazendo check-ins diários "
                    "para descobrir padrões!_",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📊 *Correlações Descobertas*\n\n"
            
            for corr in correlations[:5]:
                m1 = corr.get("metric_1", "").replace("_", " ")
                m2 = corr.get("metric_2", "").replace("_", " ")
                val = corr.get("correlation_value", 0)
                
                if val > 0.5:
                    arrow = "↗️"
                    strength = "forte positiva"
                elif val > 0:
                    arrow = "↗️"
                    strength = "positiva"
                elif val < -0.5:
                    arrow = "↘️"
                    strength = "forte negativa"
                else:
                    arrow = "↘️"
                    strength = "negativa"
                
                message += f"{arrow} *{m1.title()}* × *{m2.title()}*\n"
                message += f"   Correlação {strength}: `{val:.0%}`\n\n"
            
            message += "_Quanto mais check-ins, mais preciso!_"
            
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("cmd_correlacoes_failed", error=str(e))
            update.message.reply_text("❌ Erro ao buscar correlações.")


def register_extended_commands(bot_handler) -> ExtendedBotCommands:
    """
    Registra comandos estendidos no bot handler.
    """
    from telegram.ext import CommandHandler
    
    ext = ExtendedBotCommands(bot_handler)
    dp = bot_handler.updater.dispatcher
    
    # Gmail
    dp.add_handler(CommandHandler("emails", ext.cmd_emails))
    
    # Content
    dp.add_handler(CommandHandler("ideia", ext.cmd_ideia))
    dp.add_handler(CommandHandler("ideias", ext.cmd_ideias))
    
    # Finance
    dp.add_handler(CommandHandler("financas", ext.cmd_financas))
    dp.add_handler(CommandHandler("entrada", ext.cmd_entrada))
    dp.add_handler(CommandHandler("saida", ext.cmd_saida))
    
    # Memory
    dp.add_handler(CommandHandler("lembrar", ext.cmd_lembrar))
    dp.add_handler(CommandHandler("buscar", ext.cmd_buscar))
    
    # Insights
    dp.add_handler(CommandHandler("insights", ext.cmd_insights))
    
    # Autonomy
    dp.add_handler(CommandHandler("autonomia", ext.cmd_autonomia))
    
    # Health
    dp.add_handler(CommandHandler("saude", ext.cmd_saude))
    dp.add_handler(CommandHandler("checkin", ext.cmd_checkin_health))
    dp.add_handler(CommandHandler("metas", ext.cmd_metas))
    dp.add_handler(CommandHandler("correlacoes", ext.cmd_correlacoes))
    
    logger.info("extended_commands_registered")
    
    return ext
