"""
Melhorias para o Bot - Conversação Mais Natural e Progressiva
Implementação das recomendações da análise de qualidade
"""

# ==========================================
# 1. PROMPT MELHORADO - CONVERSACIONAL
# ==========================================

IMPROVED_SYSTEM_PROMPT = """Você é Igor, o assistente pessoal do usuário.

PERSONALIDADE:
- Amigável e descontraído, mas eficiente
- Fala naturalmente, como um amigo prestativo
- Usa "você" e "tu", não formalidades excessivas
- Emojis COM MODERAÇÃO (1-2 por mensagem, quando relevante)
- Não é robotizado ou técnico

REGRAS DE OURO DA CONVERSA:

1. SEMPRE PROGRIDA A CONVERSA:
   - Se usuário pede ajuda com algo → faça 2-3 perguntas específicas imediatamente
   - Se usuário concorda/confirma ("ok", "beleza", "sim") → continue com próximo passo
   - Nunca responda apenas "ok" ou "aguardando" → sempre proponha ação ou faça pergunta

2. SEJA DIRETO E PRÁTICO:
   - Não fale sobre o que VAI fazer, FAÇA
   - Evite: "Vou processar", "Vou salvar", "Vou ajudar"
   - Use: "Anotei!", "Beleza!", "Feito!", "Vamos lá"

3. LINGUAGEM NATURAL:
   ❌ NUNCA use: "processado", "registrado", "item salvo", "ID:", "status:"
   ✅ SEMPRE use: "anotei", "lembrei", "beleza", "feito", "ok"

4. CONTEXTO É TUDO:
   - Sempre considere as mensagens anteriores
   - Faça referências ao que foi dito ("como você mencionou", "sobre aquilo que falou")
   - Mantenha coerência com objetivo da conversa

5. SEJA PROATIVO:
   - Sugira próximos passos
   - Ofereça ajuda adicional relevante
   - Antecipe necessidades

EXEMPLOS DE BOM COMPORTAMENTO:

Usuário: "Quero criar uma dieta"
Você: "Boa! Vamos montar algo personalizado pra você. Me conta:

1️⃣ Qual seu objetivo principal? (emagrecer, ganhar massa, etc)
2️⃣ Faz exercício? Quantas vezes por semana?
3️⃣ Tem alguma restrição alimentar?"

---

Usuário: "Beleza, vamos"
Você: "Ótimo! Primeira pergunta: qual seu peso e altura atuais? 
(vou usar pra calcular suas necessidades calóricas)"

---

Usuário: "Oi"
Você: "E aí! 👋 Tudo certo? 

Em que posso ajudar hoje?"

QUANDO SALVAR NA INBOX:
- Tarefas, lembretes, ideias, projetos → SALVAR (mas não avisar detalhes técnicos)
- Perguntas sobre dados, consultas → NÃO SALVAR (apenas responder)
- Cumprimentos casuais ("oi", "beleza") → NÃO SALVAR (apenas conversar)

FORMATO DE RESPOSTA:
Sempre que criar algo (tarefa, lembrete, etc), mencione naturalmente:
✅ "Anotei: 'Ligar pro dentista amanhã' 📅"
✅ "Criei a tarefa 'Finalizar relatório' pra você ✓"
❌ NUNCA: "✅ Salvo na Inbox | Tipo: task | ID: 87dd92f9"
"""


# ==========================================
# 2. DETECÇÃO DE INTENÇÃO MELHORADA
# ==========================================

class ImprovedIntentDetector:
    """Detecta intenção real do usuário para respostas apropriadas."""
    
    CASUAL_GREETINGS = {
        "oi", "olá", "ola", "hey", "oi!", "e aí", "eai", "e ai",
        "opa", "salve", "fala", "beleza", "blz", "oi bot"
    }
    
    ACKNOWLEDGMENTS = {
        "ok", "okay", "beleza", "blz", "certo", "entendi", "sim",
        "vamos", "bora", "dale", "pode ser", "legal", "ótimo",
        "perfeito", "show", "massa", "valeu"
    }
    
    HELP_KEYWORDS = {
        "ajuda": ["ajuda", "ajudar", "help", "socorro"],
        "create": ["criar", "fazer", "montar", "gerar", "construir"],
        "plan": ["planejar", "planilha", "organizar", "estruturar"],
        "remember": ["lembrar", "lembrete", "não esquecer", "anotar"],
        "question": ["qual", "quando", "onde", "como", "por que", "quem"]
    }
    
    @classmethod
    def detect(cls, message: str, context: dict = None) -> str:
        """
        Detecta intenção da mensagem.
        
        Returns:
            - "greeting": Cumprimento casual
            - "acknowledgment": Confirmação/concordância (precisa continuar conversa)
            - "help_request": Pedido de ajuda específico
            - "question": Pergunta sobre dados
            - "task": Criar tarefa/lembrete
            - "general": Conversa geral
        """
        msg_lower = message.lower().strip()
        
        # Cumprimentos casuais
        if msg_lower in cls.CASUAL_GREETINGS:
            return "greeting"
        
        # Confirmações (contexto importa!)
        if msg_lower in cls.ACKNOWLEDGMENTS:
            # Se há contexto de conversa em andamento, é "acknowledgment"
            # Senão, é apenas "greeting"
            if context and context.get("active_conversation"):
                return "acknowledgment"
            return "greeting"
        
        # Pedido explícito de ajuda
        if any(kw in msg_lower for kw in cls.HELP_KEYWORDS["ajuda"]):
            return "help_request"
        
        # Criação de algo
        if any(kw in msg_lower for kw in cls.HELP_KEYWORDS["create"]):
            return "help_request"
        
        # Lembrete/tarefa
        if "lembr" in msg_lower or "anotar" in msg_lower or "não esquecer" in msg_lower:
            return "task"
        
        # Perguntas
        if any(kw in msg_lower for kw in cls.HELP_KEYWORDS["question"]):
            return "question"
        
        return "general"


# ==========================================
# 3. GERENCIADOR DE CONTEXTO
# ==========================================

class ConversationContextManager:
    """Gerencia contexto de conversas para respostas mais inteligentes."""
    
    def __init__(self):
        self.conversations = {}  # user_id -> conversation_state
    
    def get_context(self, user_id: str) -> dict:
        """Obtém contexto atual da conversa."""
        if user_id not in self.conversations:
            self.conversations[user_id] = {
                "messages": [],
                "active_topic": None,
                "expected_info": [],  # O que estamos esperando do usuário
                "user_profile": {}
            }
        return self.conversations[user_id]
    
    def add_message(self, user_id: str, role: str, content: str):
        """Adiciona mensagem ao histórico."""
        ctx = self.get_context(user_id)
        ctx["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Manter apenas últimas 10 mensagens
        if len(ctx["messages"]) > 10:
            ctx["messages"] = ctx["messages"][-10:]
    
    def set_active_topic(self, user_id: str, topic: str, expected_info: list = None):
        """Define tópico ativo (ex: "diet_planning", "project_setup")."""
        ctx = self.get_context(user_id)
        ctx["active_topic"] = topic
        ctx["expected_info"] = expected_info or []
    
    def get_recent_messages(self, user_id: str, limit: int = 5) -> list:
        """Retorna mensagens recentes."""
        ctx = self.get_context(user_id)
        return ctx["messages"][-limit:]
    
    def format_for_prompt(self, user_id: str) -> str:
        """Formata contexto para incluir no prompt da IA."""
        ctx = self.get_context(user_id)
        
        # Mensagens recentes
        recent = self.get_recent_messages(user_id, limit=5)
        messages_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}"
            for msg in recent
        ])
        
        # Tópico ativo
        topic_text = ""
        if ctx["active_topic"]:
            topic_text = f"\nTópico atual: {ctx['active_topic']}"
            if ctx["expected_info"]:
                topic_text += f"\nInformações necessárias: {', '.join(ctx['expected_info'])}"
        
        return f"""
CONTEXTO DA CONVERSA:
{messages_text}
{topic_text}

Baseado neste contexto, responda a nova mensagem do usuário.
Lembre-se: se o usuário confirmou algo ("ok", "beleza"), CONTINUE a conversa!
"""


# ==========================================
# 4. GERADOR DE RESPOSTAS PROGRESSIVAS
# ==========================================

class ProgressiveResponseGenerator:
    """Gera respostas que avançam a conversa naturalmente."""
    
    @staticmethod
    def generate_help_response(topic: str, context_mgr, user_id: str) -> str:
        """Gera resposta para pedidos de ajuda com perguntas específicas."""
        
        if "diet" in topic or "dieta" in topic:
            context_mgr.set_active_topic(
                user_id, 
                "diet_planning",
                expected_info=["objetivos", "peso_altura", "exercicio", "restricoes"]
            )
            return """Boa! Vamos montar uma dieta personalizada pra você 🎯

Me conta:

1️⃣ Qual seu objetivo? (emagrecer, ganhar massa, definição...)
2️⃣ Você treina? Quantas vezes por semana?
3️⃣ Tem alguma restrição alimentar ou alimento que não gosta?

Responde aí que eu vou montando o plano!"""
        
        elif "projeto" in topic or "app" in topic:
            context_mgr.set_active_topic(
                user_id,
                "project_planning",
                expected_info=["objetivo", "tecnologias", "prazo"]
            )
            return """Legal! Vamos organizar esse projeto 🚀

Pra começar:

1️⃣ Qual o objetivo principal do app?
2️⃣ Já tem ideia das tecnologias? (ou quer sugestões?)
3️⃣ Tem algum prazo em mente?"""
        
        elif "tarefa" in topic or "lembrar" in topic:
            return """Beleza! Pra criar um lembrete bom, me fala:

📌 O que precisa fazer?
📅 Quando? (data/hora)
⚡️ É urgente?"""
        
        else:
            return f"""Entendi que você quer ajuda com: {topic}

Conta mais detalhes pra eu poder te ajudar melhor! 😊"""
    
    @staticmethod
    def generate_acknowledgment_response(context_mgr, user_id: str) -> str:
        """
        Responde a confirmações ("ok", "beleza") continuando a conversa.
        NUNCA apenas confirma - sempre avança!
        """
        ctx = context_mgr.get_context(user_id)
        active_topic = ctx.get("active_topic")
        expected_info = ctx.get("expected_info", [])
        
        if active_topic == "diet_planning":
            if expected_info:
                next_q = expected_info[0]
                if next_q == "peso_altura":
                    return "Beleza! Agora me diz: qual seu peso e altura atuais?"
                elif next_q == "exercicio":
                    return "Ótimo! Você faz exercício? Se sim, quantas vezes por semana?"
                elif next_q == "restricoes":
                    return "Perfeito! Tem alguma restrição alimentar ou comida que não curte?"
            else:
                return """Show! Com essas infos já consigo montar algo.

Vou criar um plano de dieta personalizado pra você. 
Quer que eu divida por refeições (café, almoço, jantar) ou prefere só diretrizes gerais?"""
        
        elif active_topic == "project_planning":
            if expected_info:
                return """Legal! Vamos começar então.

Primeira coisa: vou criar as tarefas principais do projeto.
O que você acha de começar por:
1. Definir arquitetura
2. Setup do ambiente
3. MVP das funcionalidades core

Faz sentido?"""
        
        else:
            # Sem contexto específico
            return """Ótimo! 

Em que mais posso te ajudar? 😊"""
    
    @staticmethod
    def generate_greeting_response() -> str:
        """Resposta para cumprimentos casuais."""
        return """E aí! 👋 Tudo certo?

Bora trabalhar? Me fala o que você precisa:
• Criar tarefa ou lembrete
• Consultar agenda
• Planejar algo
• Ou só conversar!"""
    
    @staticmethod
    def add_next_step(response: str, context_mgr, user_id: str) -> str:
        """Adiciona sugestão de próximo passo ao final da resposta."""
        ctx = context_mgr.get_context(user_id)
        active_topic = ctx.get("active_topic")
        
        # Não adicionar se já tem pergunta
        if "?" in response:
            return response
        
        suggestions = {
            "diet_planning": "\n\n💡 Quer que eu monte um cardápio semanal completo?",
            "project_planning": "\n\n🎯 Vamos criar as primeiras tarefas?",
            "task_created": "\n\n📅 Quer adicionar ao calendário também?"
        }
        
        return response + suggestions.get(active_topic, "")


# ==========================================
# 5. HANDLER MELHORADO
# ==========================================

from typing import Optional

class ImprovedBotHandler:
    """Handler melhorado para conversas naturais."""
    
    def __init__(self):
        self.context_mgr = ConversationContextManager()
        self.intent_detector = ImprovedIntentDetector()
        self.response_generator = ProgressiveResponseGenerator()
    
    async def handle_message(
        self,
        user_id: str,
        message: str,
        gemini_service
    ) -> dict:
        """
        Processa mensagem com conversação progressiva.
        
        Returns:
            {
                "response": str,
                "should_save_inbox": bool,
                "actions": list
            }
        """
        # 1. Adicionar ao contexto
        self.context_mgr.add_message(user_id, "user", message)
        
        # 2. Detectar intenção
        ctx = self.context_mgr.get_context(user_id)
        intent = self.intent_detector.detect(message, ctx)
        
        # 3. Gerar resposta baseada em intent
        response = None
        should_save = False
        
        if intent == "greeting":
            response = self.response_generator.generate_greeting_response()
            should_save = False
        
        elif intent == "acknowledgment":
            # Usuário confirmou - CONTINUAR conversa!
            response = self.response_generator.generate_acknowledgment_response(
                self.context_mgr,
                user_id
            )
            should_save = False
        
        elif intent == "help_request":
            # Pedido de ajuda - fazer perguntas específicas
            response = self.response_generator.generate_help_response(
                message,
                self.context_mgr,
                user_id
            )
            should_save = False
        
        else:
            # Usar IA com contexto rico
            context_prompt = self.context_mgr.format_for_prompt(user_id)
            
            try:
                response = await gemini_service.generate_text(
                    f"{context_prompt}\n\nNova mensagem: {message}",
                    temperature=0.7
                )
                
                # Limpar resposta
                response = self._clean_response(response)
                
                # Adicionar próximo passo se apropriado
                response = self.response_generator.add_next_step(
                    response,
                    self.context_mgr,
                    user_id
                )
                
                should_save = intent in ["task", "general"]
                
            except Exception as e:
                # Fallback elegante
                response = self._generate_fallback_response(message, intent)
                should_save = True
        
        # 4. Salvar resposta no contexto
        self.context_mgr.add_message(user_id, "assistant", response)
        
        return {
            "response": response,
            "should_save_inbox": should_save,
            "actions": []
        }
    
    def _clean_response(self, response: str) -> str:
        """Remove elementos técnicos da resposta."""
        # Remove IDs
        import re
        response = re.sub(r'ID:\s*[a-zA-Z0-9-]+', '', response)
        response = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', response)
        
        # Remove termos técnicos
        tech_terms = [
            "processado com sucesso",
            "item registrado",
            "salvo na inbox",
            "status:",
            "tipo:",
            "prioridade:",
            "método:"
        ]
        
        for term in tech_terms:
            response = response.replace(term, "")
            response = response.replace(term.title(), "")
        
        return response.strip()
    
    def _generate_fallback_response(self, message: str, intent: str) -> str:
        """Gera resposta fallback quando IA falha."""
        if intent == "task":
            return f"Anotei: '{message}' ✓\n\nVou processar isso e te aviso quando tiver uma resposta melhor!"
        
        return (
            "Opa, tô com um probleminha técnico agora 😅\n\n"
            "Mas salvei sua mensagem e já te respondo direitinho!"
        )


# ==========================================
# 6. EXEMPLO DE USO
# ==========================================

"""
# No bot_handler.py principal:

from improvements import ImprovedBotHandler

class TelegramBotHandler:
    def __init__(self):
        self.improved_handler = ImprovedBotHandler()
        self.gemini = GeminiService()
    
    async def handle_message(self, update: Update, context: CallbackContext):
        user_id = str(update.effective_user.id)
        message = update.message.text
        
        # Usar handler melhorado
        result = await self.improved_handler.handle_message(
            user_id=user_id,
            message=message,
            gemini_service=self.gemini
        )
        
        # Responder
        await update.message.reply_text(
            result["response"],
            parse_mode="Markdown"
        )
        
        # Salvar na inbox SE NECESSÁRIO (silenciosamente)
        if result["should_save_inbox"]:
            await self._save_to_inbox_silent(user_id, message)
    
    async def _save_to_inbox_silent(self, user_id: str, message: str):
        # Salva sem enviar notificação técnica
        pass
"""
