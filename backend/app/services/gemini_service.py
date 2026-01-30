"""
TB Personal OS - Gemini AI Service
Interface for Google Gemini API
Supports both SDK and REST API fallback
"""

import structlog
import aiohttp
import json
from typing import List, Dict, Optional, Any
from app.core.config import settings

logger = structlog.get_logger(__name__)

# Flag para indicar se Gemini está disponível
GEMINI_AVAILABLE = False
GEMINI_MODE = "none"  # "sdk", "rest", or "none"
genai = None

# Tenta usar SDK primeiro
try:
    import google.generativeai as genai_module
    genai_module.configure(api_key=settings.GEMINI_API_KEY)
    # Tenta criar modelo para verificar se funciona
    test_model = genai_module.GenerativeModel(settings.GEMINI_MODEL)
    genai = genai_module
    GEMINI_AVAILABLE = True
    GEMINI_MODE = "sdk"
    logger.info("gemini_sdk_configured", mode="sdk")
except Exception as e:
    logger.warning("gemini_sdk_not_available", error=str(e))
    # Fallback para REST API se tiver API key
    if settings.GEMINI_API_KEY:
        GEMINI_AVAILABLE = True
        GEMINI_MODE = "rest"
        logger.info("gemini_rest_configured", mode="rest")


class GeminiService:
    """Service for interacting with Gemini AI via SDK or REST API with automatic fallback"""
    
    # REST API base URL
    REST_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(self):
        self.model = None
        self.chat_sessions: Dict[str, Any] = {}
        
        # Sistema de múltiplas chaves API para fallback automático
        self.api_keys = [settings.GEMINI_API_KEY]
        if settings.GEMINI_API_KEY_2:
            self.api_keys.append(settings.GEMINI_API_KEY_2)
        
        self.current_key_index = 0
        self.api_key = self.api_keys[self.current_key_index]
        self.model_name = settings.GEMINI_MODEL or "gemini-pro"
        
        logger.info(
            "gemini_service_initialized", 
            total_keys=len(self.api_keys),
            current_key=self.current_key_index + 1
        )
        
        if GEMINI_MODE == "sdk" and genai:
            try:
                self.model = genai.GenerativeModel(self.model_name)
                logger.info("gemini_model_initialized", model=self.model_name, mode="sdk")
            except Exception as e:
                logger.warning("gemini_model_init_failed", error=str(e))
        elif GEMINI_MODE == "rest":
            logger.info("gemini_rest_ready", model=self.model_name, mode="rest")
    
    def _is_available(self) -> bool:
        """Verifica se o Gemini está disponível."""
        return GEMINI_AVAILABLE and (self.model is not None or GEMINI_MODE == "rest")
    
    def _switch_to_next_api_key(self) -> bool:
        """
        Troca para próxima chave API disponível.
        Retorna True se conseguiu trocar, False se não há mais chaves.
        """
        if len(self.api_keys) <= 1:
            logger.warning("no_alternative_api_keys")
            return False
        
        # Ir para próxima chave
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.api_key = self.api_keys[self.current_key_index]
        
        logger.info(
            "switched_to_api_key",
            new_key_index=self.current_key_index + 1,
            total_keys=len(self.api_keys)
        )
        
        return True
    
    async def _call_rest_api(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        retry_with_fallback: bool = True
    ) -> str:
        """Chama Gemini via REST API com fallback automático de chaves."""
        url = f"{self.REST_API_BASE}/models/{self.model_name}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Build request body
        body = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            body["generationConfig"]["maxOutputTokens"] = max_tokens
        
        params = {"key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract text from response
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                        return ""
                    
                    elif response.status == 429 and retry_with_fallback:
                        # Rate limit atingido - tentar próxima chave
                        error_text = await response.text()
                        logger.warning(
                            "gemini_rate_limit_switching_key",
                            status=response.status,
                            current_key=self.current_key_index + 1,
                            error=error_text[:200]
                        )
                        
                        # Tentar trocar de chave
                        if self._switch_to_next_api_key():
                            logger.info("retrying_with_new_api_key")
                            # Tentar novamente com nova chave (sem retry recursivo)
                            return await self._call_rest_api(
                                prompt, 
                                temperature, 
                                max_tokens,
                                retry_with_fallback=False
                            )
                        else:
                            logger.error("all_api_keys_exhausted")
                            return ""
                    
                    else:
                        error_text = await response.text()
                        logger.error("gemini_rest_api_error", status=response.status, error=error_text)
                        return ""
        except Exception as e:
            logger.error("gemini_rest_api_exception", error=str(e))
            return ""
    
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Gemini (SDK ou REST)
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for context
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated text
        """
        if not self._is_available():
            logger.warning("gemini_not_available_using_fallback")
            return self._generate_fallback_response(prompt)
        
        # Build full prompt with system instruction
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        
        try:
            # Use REST API if SDK not available
            if GEMINI_MODE == "rest":
                result = await self._call_rest_api(full_prompt, temperature, max_tokens)
                if result:
                    logger.info(
                        "gemini_rest_generation_completed",
                        prompt_length=len(prompt),
                        response_length=len(result),
                    )
                    return result
                return self._generate_fallback_response(prompt)
            
            # Use SDK
            generation_config = {}
            if temperature is not None:
                generation_config["temperature"] = temperature
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens
            
            if genai and hasattr(genai, 'GenerationConfig'):
                config = genai.GenerationConfig(**generation_config) if generation_config else None
                response = self.model.generate_content(full_prompt, generation_config=config)
            else:
                response = self.model.generate_content(full_prompt)
            
            result = response.text
            
            logger.info(
                "gemini_generation_completed",
                prompt_length=len(prompt),
                response_length=len(result),
            )
            
            return result
            
        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e))
            return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """
        Resposta de fallback elegante quando Gemini não está disponível.
        Tenta dar resposta útil baseada em regras simples.
        """
        prompt_lower = prompt.lower()
        
        # Cumprimentos
        if any(word in prompt_lower for word in ["oi", "olá", "hey", "e aí", "bom dia"]):
            return "E aí! 👋 Tô com um probleminha técnico agora, mas já já volto. Em que posso ajudar?"
        
        # Perguntas sobre tarefas
        if any(word in prompt_lower for word in ["tarefas", "pendente", "fazer hoje"]):
            return "Opa, tô meio lento agora 😅 Mas anotei sua pergunta! Já te respondo com a lista de tarefas."
        
        # Criação de tarefa/lembrete
        if any(word in prompt_lower for word in ["criar", "lembrar", "anotar", "não esquecer"]):
            return "Anotei! ✓\n\nEstou processando isso e já te confirmo os detalhes."
        
        # Pedido de ajuda
        if any(word in prompt_lower for word in ["ajuda", "help", "como", "preciso"]):
            return "Quero te ajudar! 😊\n\nEstou com um pequeno problema técnico mas salvei sua mensagem. Já te respondo melhor!"
        
        # Resposta genérica mais amigável
        return (
            "Opa, tô com um probleminha técnico agora 😅\n\n"
            "Mas salvei sua mensagem e já te respondo direitinho!"
        )
    
    async def chat(
        self,
        user_id: str,
        message: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Chat with Gemini (maintains conversation context)
        
        Args:
            user_id: Unique user identifier
            message: User message
            system_instruction: System instruction
            
        Returns:
            Assistant response
        """
        try:
            # Get or create chat session
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
                
                # Add system instruction as first message if provided
                if system_instruction:
                    self.chat_sessions[user_id].send_message(
                        f"[SYSTEM] {system_instruction}"
                    )
            
            chat = self.chat_sessions[user_id]
            
            # Send message
            response = chat.send_message(message)
            result = response.text
            
            logger.info(
                "Chat message processed",
                user_id=user_id,
                message_length=len(message),
                response_length=len(result),
            )
            
            return result
            
        except Exception as e:
            logger.error("Chat processing failed", exc_info=e, user_id=user_id)
            raise
    
    def clear_chat_history(self, user_id: str):
        """Clear chat history for user"""
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]
            logger.info("Chat history cleared", user_id=user_id)
    
    async def extract_structured_data(
        self,
        text: str,
        schema: Dict,
    ) -> Dict:
        """
        Extract structured data from text
        
        Args:
            text: Input text
            schema: Expected data structure
            
        Returns:
            Extracted data as dictionary
        """
        prompt = f"""
        Extract structured data from the following text.
        
        Expected schema:
        {schema}
        
        Text:
        {text}
        
        Return ONLY valid JSON matching the schema.
        """
        
        try:
            response = await self.generate_text(prompt, temperature=0.3)
            return self._parse_json_response(response)
            
        except Exception as e:
            logger.error("Data extraction failed", exc_info=e)
            raise
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        Parse JSON from Gemini response.
        Handles markdown code blocks and other formatting.
        """
        import json
        
        # Remove markdown code blocks
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (code block markers)
            lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            text = "\n".join(lines)
        
        # Find JSON in response
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        raise ValueError("No valid JSON found in response")
    
    async def classify_message(
        self,
        message: str,
        context: Optional[str] = None,
    ) -> Dict:
        """
        Classify a message with AI.
        
        Args:
            message: Message to classify
            context: Optional context (previous messages, user info)
            
        Returns:
            Classification result
        """
        context_text = f"\nCONTEXTO: {context}" if context else ""
        
        prompt = f"""Você é um assistente pessoal. Analise esta mensagem e classifique-a.
{context_text}
MENSAGEM: "{message}"

Retorne APENAS um JSON válido (sem markdown, sem explicações) no formato:
{{
    "type": "task|idea|note|question|event|reminder",
    "category": "personal|work|health|content|finance|other",
    "priority": "low|medium|high|urgent",
    "sentiment": "positive|neutral|negative",
    "needs_response": true ou false,
    "suggested_action": "descrição curta da ação sugerida",
    "entities": {{
        "people": ["nomes de pessoas mencionadas"],
        "dates": ["datas/horários mencionados"],
        "locations": ["locais mencionados"],
        "values": ["valores monetários"],
        "topics": ["tópicos principais"]
    }},
    "summary": "resumo em 1 linha do conteúdo",
    "response": "se needs_response=true, escreva uma resposta útil e concisa"
}}

Regras:
- type: task (algo a fazer), idea (sugestão/insight), note (informação), question (pergunta), event (compromisso), reminder (lembrete)
- category: baseado no contexto principal da mensagem
- priority: urgente/hoje/deadline=high, normal=medium, sem pressa/eventual=low
- needs_response: true apenas se for pergunta que precisa de resposta direta
- Extraia todas as entidades relevantes mencionadas"""
        
        try:
            response = await self.generate_text(prompt, temperature=0.3, max_tokens=1000)
            result = self._parse_json_response(response)
            result["confidence"] = "high"
            result["method"] = "gemini"
            return result
            
        except Exception as e:
            logger.warning("AI classification failed, using fallback", error=str(e))
            return self._classify_fallback(message)
    
    def _classify_fallback(self, message: str) -> Dict:
        """Fallback classification using keywords."""
        text_lower = message.lower()
        
        # Determine type
        msg_type = "note"
        if any(word in text_lower for word in ["tarefa", "fazer", "to-do", "preciso", "tenho que", "devo"]):
            msg_type = "task"
        elif any(word in text_lower for word in ["ideia", "pensei", "e se", "poderia", "talvez"]):
            msg_type = "idea"
        elif any(word in text_lower for word in ["reunião", "evento", "encontro", "call", "às"]):
            msg_type = "event"
        elif any(word in text_lower for word in ["lembrar", "não esquecer", "lembrete"]):
            msg_type = "reminder"
        elif message.endswith("?"):
            msg_type = "question"
        
        # Determine category
        category = "other"
        category_keywords = {
            "work": ["trabalho", "cliente", "projeto", "reunião", "deadline", "empresa", "chefe"],
            "health": ["academia", "treino", "saúde", "exercício", "dieta", "sono", "médico"],
            "content": ["post", "conteúdo", "instagram", "linkedin", "blog", "youtube", "vídeo"],
            "finance": ["pagar", "receber", "dinheiro", "grana", "conta", "fatura", "banco", "pix"],
            "personal": ["família", "amigo", "pessoal", "casa", "comprar", "viagem"],
        }
        
        for cat, keywords in category_keywords.items():
            if any(word in text_lower for word in keywords):
                category = cat
                break
        
        # Determine priority
        priority = "medium"
        if any(word in text_lower for word in ["urgente", "hoje", "agora", "crítico", "importante", "deadline"]):
            priority = "high"
        elif any(word in text_lower for word in ["depois", "quando der", "sem pressa", "eventualmente"]):
            priority = "low"
        
        return {
            "type": msg_type,
            "category": category,
            "priority": priority,
            "sentiment": "neutral",
            "needs_response": msg_type == "question",
            "suggested_action": f"Salvar como {msg_type}",
            "entities": {"people": [], "dates": [], "locations": [], "values": [], "topics": []},
            "summary": message[:100],
            "confidence": "low",
            "method": "keywords"
        }
    
    async def generate_response(
        self,
        question: str,
        context: Optional[str] = None,
        user_info: Optional[Dict] = None,
    ) -> str:
        """
        Generate a helpful response to a question.
        
        Args:
            question: User's question
            context: Context from previous messages
            user_info: User preferences and info
            
        Returns:
            Generated response
        """
        user_context = ""
        if user_info:
            user_context = f"\nINFO DO USUÁRIO: {user_info}"
        
        history_context = ""
        if context:
            history_context = f"\nCONTEXTO DAS CONVERSAS ANTERIORES:\n{context}"
        
        system = f"""Você é um assistente pessoal chamado Igor (TB Personal OS).
Você ajuda a organizar vida pessoal e profissional.
Seja conciso, útil e proativo.
Responda em português brasileiro.
{user_context}
{history_context}"""
        
        try:
            response = await self.generate_text(
                prompt=question,
                system_instruction=system,
                temperature=0.7,
                max_tokens=500
            )
            return response
            
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return "Desculpe, não consegui processar sua pergunta. Pode reformular?"
    
    async def summarize_day(
        self,
        tasks_done: List[Dict],
        tasks_pending: List[Dict],
        inbox_items: List[Dict],
        checkins: Optional[List[Dict]] = None,
    ) -> str:
        """
        Generate a daily summary.
        
        Args:
            tasks_done: Completed tasks
            tasks_pending: Pending tasks
            inbox_items: Inbox items of the day
            checkins: Health check-ins
            
        Returns:
            Summary text
        """
        data = {
            "tasks_done": len(tasks_done),
            "tasks_done_titles": [t.get("title", "") for t in tasks_done[:5]],
            "tasks_pending": len(tasks_pending),
            "tasks_pending_titles": [t.get("title", "") for t in tasks_pending[:5]],
            "inbox_count": len(inbox_items),
            "checkins": checkins or []
        }
        
        prompt = f"""Gere um resumo do dia baseado nos dados:

DADOS: {data}

Crie um resumo breve e motivacional que inclua:
1. Tarefas concluídas (celebrar se houver)
2. Tarefas pendentes prioritárias
3. Itens novos na inbox
4. Métricas de saúde (se houver)
5. Uma sugestão para amanhã

Formato: texto corrido, máximo 200 palavras, tom amigável."""
        
        try:
            return await self.generate_text(prompt, temperature=0.7, max_tokens=400)
        except Exception as e:
            logger.error("Summary generation failed", error=str(e))
            return f"📊 Resumo: {data['tasks_done']} tarefas concluídas, {data['tasks_pending']} pendentes."
    
    def generate_text_sync(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Versão síncrona do generate_text para compatibilidade com bot v13.
        Usa REST API de forma síncrona com requests.
        """
        import requests
        
        if not self.current_api_key:
            return self._generate_fallback_response(prompt)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.current_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens or 800
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            # Rate limit - trocar chave
            if response.status_code == 429:
                logger.warning("rate_limit_hit_sync", api_key_index=self.current_key_index)
                self._switch_to_next_api_key()
                # Retry com nova chave
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.current_api_key}"
                response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code != 200:
                logger.error("gemini_rest_sync_failed", status=response.status_code)
                return self._generate_fallback_response(prompt)
            
            data = response.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if not text:
                return self._generate_fallback_response(prompt)
            
            logger.info(
                "gemini_sync_generation_completed",
                prompt_length=len(prompt),
                response_length=len(text)
            )
            
            return text
            
        except Exception as e:
            logger.error("gemini_sync_generation_failed", error=str(e))
            return self._generate_fallback_response(prompt)
    
    def chat_sync(
        self,
        user_message: str,
        user_id: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Versão síncrona do chat para bot v13.
        Conversa contextualizada com system instruction + RAG (perfil, memória, padrões).
        """
        system_context = """Você é o assistente Performance Points. Um sistema inteligente de alta performance que combina gamificação, tracking e conversa natural.

**QUEM VOCÊ É:**
Um parceiro de progresso. Direto, estratégico, sem enrolação. Você adapta seu tom ao perfil do usuário, mas sempre mantém foco em ação real e resultados mensuráveis.

**O QUE VOCÊ FAZ:**

1. **Sistema de Progresso RPG**
   - XP por cada ação (tarefas, check-ins, quests)
   - Níveis e conquistas desbloqueáveis
   - 4 métricas: Energia, Foco, Execução, Renda

2. **Quests Inteligentes**
   - Missões diárias baseadas no perfil do usuário
   - Adaptadas às áreas prioritárias e bloqueios
   - Ajustam dificuldade conforme progresso

3. **Tracking Contextual**
   - Check-ins de energia (rápido: /checkin 8)
   - Tarefas com categorização automática
   - Patterns detectados por ML (horários, consistência)

4. **Conversa Natural + Comandos**
   - Responde perguntas e conversa sobre qualquer tema
   - Usa dados do perfil para personalizar respostas
   - Sugere ações baseadas no contexto

**COMANDOS ESSENCIAIS:**
• /status → Dashboard completo (XP, métricas, perfil)
• /quest → Missão do dia
• /checkin [1-10] → Registrar energia
• /task → Criar tarefa gamificada
• /quiz → Refazer perfil

**COMO VOCÊ RESPONDE:**

• **Perguntas gerais**: Responda usando dados do perfil quando relevante
• **Tarefas mencionadas**: Sugira /task ou pergunte se quer gamificar
• **Check de progresso**: Mencione métricas e próximos passos
• **Bloqueios**: Relacione com padrões detectados e sugira ação
• **Conversas casuais**: Engaje naturalmente, mas conecte ao propósito quando fizer sentido

**REGRAS DE OURO:**
1. Use o nome e arquétipo do usuário quando relevante
2. Mencione metas e áreas prioritárias quando conectar com o contexto
3. Celebre conquistas (XP, tarefas completas, consistência)
4. Desafie procrastinação com ação concreta, não sermão
5. Máximo 250 palavras por resposta (seja denso, não prolixo)
6. Adapte tom: direto para "Executores", reflexivo para "Estrategistas", etc.

**O QUE VOCÊ NÃO É:**
Não é só lista de tarefas. Não é coach motivacional genérico. Não dá conselhos vazios. É um sistema de alta performance que sabe exatamente onde o usuário está e para onde está indo.

Responda com inteligência contextual, não respostas decoradas."""

        # Adicionar contexto dinâmico do usuário (RAG)
        context_text = ""
        if context and isinstance(context, dict):
            # Perfil e onboarding
            if context.get('quiz_answers'):
                quiz = context['quiz_answers']
                context_text += "\n\n## PERFIL DO USUÁRIO:\n"
                if quiz.get('life_areas'):
                    context_text += f"- Áreas prioritárias: {', '.join(quiz['life_areas'])}\n"
                if quiz.get('skills'):
                    context_text += f"- Habilidades: {', '.join(quiz['skills'])}\n"
                if quiz.get('year_goals'):
                    context_text += f"- Meta principal: {quiz['year_goals']}\n"
                if quiz.get('blockers'):
                    context_text += f"- Bloqueios: {', '.join(quiz['blockers'])}\n"
            
            # Arquétipo
            if context.get('personality_profile', {}).get('archetype'):
                archetype = context['personality_profile']['archetype']
                context_text += f"- Arquétipo: {archetype}\n"
            
            # Histórico de conversas recentes
            if context.get('recent_conversations'):
                context_text += f"\n{context['recent_conversations']}\n"
            
            # Padrões detectados por ML
            if context.get('patterns'):
                patterns = context['patterns']
                if patterns:
                    context_text += "\n## PADRÕES DETECTADOS (ML):\n"
                    for pattern in patterns[:3]:  # Máximo 3 padrões mais relevantes
                        if isinstance(pattern, dict):
                            context_text += f"- {pattern.get('description', 'Padrão identificado')}\n"
            
            # Tarefas pendentes
            if context.get('pending_tasks'):
                tasks = context['pending_tasks']
                if tasks:
                    context_text += f"\n## TAREFAS PENDENTES: {len(tasks)} tarefa(s)\n"
                    for task in tasks[:3]:
                        if isinstance(task, dict):
                            context_text += f"- {task.get('title', 'Tarefa')}\n"
            
            # Modo atual
            if context.get('current_mode', {}).get('mode'):
                mode = context['current_mode']['mode']
                context_text += f"\n## MODO ATUAL: {mode}\n"
            
            # Metas recentes
            if context.get('recent_goals'):
                goals = context['recent_goals']
                if goals:
                    context_text += f"\n## METAS ATIVAS: {len(goals)} meta(s)\n"

        try:
            full_prompt = f"{system_context}{context_text}\n\nUsuário: {user_message}\n\nResposta:"
            
            response_text = self.generate_text_sync(
                full_prompt,
                temperature=0.8,
                max_tokens=500
            )
            
            return {
                'response': response_text,
                'success': True
            }
            
        except Exception as e:
            logger.error("chat_sync_failed", error=str(e), user_id=user_id)
            return {
                'response': self._generate_fallback_chat_response(user_message),
                'success': False
            }
    
    def _generate_fallback_chat_response(self, message: str) -> str:
        """Resposta de fallback quando Gemini falha."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['oi', 'olá', 'hey', 'e ai']):
            return "👋 Oi! Sou o Performance Points. Como posso te ajudar hoje? Use /help para ver meus comandos ou apenas converse comigo!"
        
        if any(word in message_lower for word in ['ajuda', 'ajudar', 'pode fazer', 'capaz']):
            return """🎯 **Performance Points - O que posso fazer:**

📊 Sistema de XP e níveis por cada ação
🎮 Quests diárias adaptadas ao seu perfil  
⚡ Check-ins de energia e tracking
📝 Tarefas com gamificação (+XP)
🗣️ Conversa natural sobre qualquer assunto
🔄 Perfil que evolui com você

Use /status para ver seu painel ou /help para comandos completos!"""
        
        return f"Entendi sua mensagem. Como posso te ajudar com isso? Use /help se precisar ver os comandos disponíveis."


# Global service instance
gemini_service = GeminiService()

