"""
TB Personal OS - Conversation Service
Gerencia conversas naturais com contexto e aprendizado
"""

import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
import re
from supabase import create_client
from app.core.config import settings
from app.services.context_service import context_service, MemoryCategory
from app.services.gemini_service import gemini_service

logger = structlog.get_logger(__name__)


class ConversationService:
    """
    Serviço de conversação que implementa:
    - Conversas naturais com Gemini
    - Contexto RAG
    - Extração de memórias e ações
    - Persistência de histórico
    """
    
    # Prompt do sistema base - VERSÃO MELHORADA (Conversacional)
    SYSTEM_PROMPT_BASE = """Você é Igor, o assistente pessoal do usuário.

PERSONALIDADE:
- Amigável e descontraído, mas eficiente
- Fala naturalmente, como um amigo prestativo  
- Usa "você", não formalidades excessivas
- Emojis COM MODERAÇÃO (1-2 por mensagem, quando relevante)
- NÃO é robotizado ou técnico

REGRAS DE OURO DA CONVERSA:

1. SEMPRE PROGRIDA A CONVERSA:
   - Se usuário pede ajuda com algo → faça 2-3 perguntas específicas IMEDIATAMENTE
   - Se usuário concorda/confirma ("ok", "beleza", "sim") → CONTINUE com próximo passo
   - NUNCA responda apenas "ok" ou "aguardando" → sempre proponha ação ou faça pergunta

2. SEJA DIRETO E PRÁTICO:
   - Não fale sobre o que VAI fazer, FAÇA
   - Evite: "Vou processar", "Vou salvar", "Vou ajudar"
   - Use: "Anotei!", "Beleza!", "Feito!", "Vamos lá"

3. LINGUAGEM NATURAL:
   ❌ NUNCA use: "processado", "registrado", "item salvo", "ID:", "status:"
   ✅ SEMPRE use: "anotei", "lembrei", "beleza", "feito", "ok"

4. CONTEXTO É TUDO:
   - Sempre considere as mensagens anteriores da conversa
   - Faça referências ao que foi dito antes
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

Usuário: "Beleza, vamos"
Você: "Ótimo! Primeira pergunta: qual seu peso e altura atuais?"

Usuário: "Oi"
Você: "E aí! 👋 Tudo certo? Em que posso ajudar hoje?"

QUANDO MENCIONAR AÇÕES:
- Tarefas criadas: "Anotei: 'Ligar pro dentista amanhã' 📅"
- Lembretes: "Criei um lembrete pra você ✓"
❌ NUNCA: "✅ Salvo na Inbox | Tipo: task | ID: 87dd92f9"""

    # Prompts por modo
    MODE_PROMPTS = {
        "foco": "Modo FOCO ativo. Seja breve e direto. Evite distrações.",
        "criativo": "Modo CRIATIVO ativo. Seja expansivo, sugira ideias, faça conexões.",
        "planejamento": "Modo PLANEJAMENTO ativo. Ajude a estruturar, priorizar e organizar.",
        "reflexao": "Modo REFLEXÃO ativo. Faça perguntas, ajude a analisar, sugira journaling."
    }
    
    # Cumprimentos casuais que não devem ser salvos na inbox
    CASUAL_GREETINGS = {
        "oi", "olá", "ola", "hey", "oi!", "e aí", "eai", "e ai",
        "opa", "salve", "fala", "beleza", "blz", "oi bot", "oie"
    }
    
    # Confirmações que indicam continuação de conversa
    ACKNOWLEDGMENTS = {
        "ok", "okay", "beleza", "blz", "certo", "entendi", "sim",
        "vamos", "bora", "dale", "pode ser", "legal", "ótimo",
        "perfeito", "show", "massa", "valeu", "continua", "vai"
    }
    
    def __init__(self):
        self._supabase = None
    
    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    def _is_casual_greeting(self, message: str) -> bool:
        """Verifica se mensagem é apenas cumprimento casual."""
        msg_clean = message.lower().strip().rstrip('!?.')
        return msg_clean in self.CASUAL_GREETINGS
    
    def _is_acknowledgment(self, message: str) -> bool:
        """Verifica se mensagem é confirmação/concordância."""
        msg_clean = message.lower().strip().rstrip('!?.')
        return msg_clean in self.ACKNOWLEDGMENTS
    
    # ==========================================
    # SESSÕES DE CONVERSA
    # ==========================================
    
    async def get_or_create_session(
        self,
        user_id: str,
        mode_id: Optional[str] = None
    ) -> Dict:
        """Obtém sessão ativa ou cria nova."""
        try:
            # Buscar sessão ativa
            result = self.supabase.table("conversation_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .order("started_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                session = result.data[0]
                # Verificar se não é muito antiga (> 6 horas)
                started = datetime.fromisoformat(session["started_at"].replace("Z", "+00:00"))
                if datetime.now(started.tzinfo) - started < timedelta(hours=6):
                    return session
                else:
                    # Fechar sessão antiga
                    await self._close_session(session["id"])
            
            # Criar nova sessão
            new_session = self.supabase.table("conversation_sessions")\
                .insert({
                    "user_id": user_id,
                    "mode_id": mode_id,
                    "is_active": True,
                    "message_count": 0
                })\
                .execute()
            
            logger.info("session_created", user_id=user_id, session_id=new_session.data[0]["id"])
            return new_session.data[0]
            
        except Exception as e:
            logger.error("session_get_or_create_failed", error=str(e))
            # Retornar sessão mock para não quebrar
            return {"id": None, "user_id": user_id}
    
    async def _close_session(self, session_id: str):
        """Fecha uma sessão de conversa."""
        try:
            # Gerar resumo da sessão
            messages = self.supabase.table("conversation_messages")\
                .select("role, content")\
                .eq("session_id", session_id)\
                .order("created_at")\
                .execute()
            
            summary = None
            if messages.data and len(messages.data) > 3:
                # Gerar resumo com Gemini
                conversation_text = "\n".join([
                    f"{m['role']}: {m['content'][:200]}" 
                    for m in messages.data
                ])
                try:
                    summary = await gemini_service.generate_text(
                        f"Resuma esta conversa em 1-2 frases:\n{conversation_text}",
                        temperature=0.3,
                        max_tokens=100
                    )
                except:
                    pass
            
            self.supabase.table("conversation_sessions")\
                .update({
                    "is_active": False,
                    "ended_at": datetime.utcnow().isoformat(),
                    "summary": summary
                })\
                .eq("id", session_id)\
                .execute()
                
            logger.info("session_closed", session_id=session_id)
            
        except Exception as e:
            logger.error("session_close_failed", error=str(e))
    
    # ==========================================
    # PROCESSAMENTO DE MENSAGENS
    # ==========================================
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        source: str = "telegram"
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem do usuário e gera resposta.
        
        Retorna:
            {
                "response": str,
                "intent": str,
                "actions": List[Dict],
                "memories_created": List[Dict]
            }
        """
        try:
            # 1. Obter ou criar sessão
            session = await self.get_or_create_session(user_id)
            session_id = session.get("id")
            
            # 1.5. Verificar se é cumprimento casual (não processar com IA)
            if self._is_casual_greeting(message):
                return {
                    "response": "E aí! 👋 Tudo certo?\n\nEm que posso ajudar hoje?",
                    "intent": "greeting",
                    "actions": [],
                    "memories_created": [],
                    "session_id": session_id
                }
            
            # 1.6. Verificar se é confirmação (continuar conversa anterior)
            if self._is_acknowledgment(message):
                # Buscar último contexto da conversa
                recent_messages = await self._get_recent_messages(session_id, limit=3)
                if recent_messages and len(recent_messages) >= 2:
                    # Gerar continuação baseada no contexto
                    continuation = await self._generate_continuation(user_id, recent_messages)
                    if continuation:
                        await self._save_message(
                            session_id=session_id,
                            user_id=user_id,
                            role="user",
                            content=message,
                            source=source
                        )
                        await self._save_message(
                            session_id=session_id,
                            user_id=user_id,
                            role="assistant",
                            content=continuation,
                            intent="continuation"
                        )
                        return {
                            "response": continuation,
                            "intent": "continuation",
                            "actions": [],
                            "memories_created": [],
                            "session_id": session_id
                        }
            
            # 2. Coletar contexto (RAG)
            context = await context_service.get_context_for_message(user_id, message)
            context_text = context_service.format_context_for_prompt(context)
            
            # 3. Construir prompt do sistema
            system_prompt = self._build_system_prompt(context)
            
            # 4. Salvar mensagem do usuário
            user_message_id = await self._save_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=message,
                source=source
            )
            
            # 5. Gerar resposta com Gemini
            full_prompt = f"""
{system_prompt}

--- CONTEXTO DO USUÁRIO ---
{context_text}
--- FIM DO CONTEXTO ---

Mensagem do usuário: {message}

Responda de forma natural e útil. Se identificar uma ação (criar tarefa, lembrete, etc), 
indique claramente no final: [AÇÃO: tipo_acao | detalhes]
"""
            
            response = await gemini_service.generate_text(
                full_prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # 6. Extrair ações da resposta
            clean_response, actions = self._extract_actions(response)
            
            # 6.5. Limpar linguagem técnica e IDs
            clean_response = self._clean_technical_language(clean_response)
            
            # 7. Detectar intenção
            intent = await self._detect_intent(message)
            
            # 8. Salvar resposta do assistente
            await self._save_message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=clean_response,
                intent=intent,
                actions=actions
            )
            
            # 9. Extrair e salvar memórias relevantes
            memories = await self._extract_and_save_memories(
                user_id=user_id,
                message=message,
                response=clean_response,
                session_id=session_id,
                message_id=user_message_id
            )
            
            # 10. Executar ações identificadas
            executed_actions = await self._execute_actions(user_id, actions)
            
            # 11. Aprendizado incremental (não bloqueante)
            await self._incremental_learning(user_id, message, intent)
            
            logger.info(
                "message_processed",
                user_id=user_id,
                intent=intent,
                actions_count=len(actions),
                memories_count=len(memories)
            )
            
            return {
                "response": clean_response,
                "intent": intent,
                "actions": executed_actions,
                "memories_created": memories,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error("message_processing_failed", error=str(e), user_id=user_id)
            return {
                "response": "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?",
                "intent": "error",
                "actions": [],
                "memories_created": []
            }
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Constrói o prompt do sistema baseado no contexto."""
        prompt = self.SYSTEM_PROMPT_BASE
        
        # Adicionar prompt do modo se ativo
        mode = context.get("current_mode")
        if mode and mode.get("mode"):
            mode_info = mode["mode"]
            if mode_info.get("system_prompt"):
                prompt += f"\n\n{mode_info.get('system_prompt')}"
            elif mode_info.get("name"):
                mode_name = mode_info.get("name", "").lower()
                if mode_name in self.MODE_PROMPTS:
                    prompt += f"\n\n{self.MODE_PROMPTS[mode_name]}"
        
        # Adicionar padrões de comunicação se existirem
        patterns = context.get("active_patterns", [])
        comm_pattern = next(
            (p for p in patterns if p.get("pattern_type") == "communication_style"),
            None
        )
        if comm_pattern:
            data = comm_pattern.get("pattern_data", {})
            if data.get("preferred_length") == "concise":
                prompt += "\n\nO usuário prefere respostas CONCISAS e diretas."
            elif data.get("preferred_length") == "detailed":
                prompt += "\n\nO usuário prefere respostas DETALHADAS e explicativas."
        
        return prompt
    
    async def _save_message(
        self,
        session_id: Optional[str],
        user_id: str,
        role: str,
        content: str,
        source: str = "telegram",
        intent: Optional[str] = None,
        actions: Optional[List] = None
    ) -> Optional[str]:
        """Salva uma mensagem no banco."""
        if not session_id:
            return None
            
        try:
            data = {
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "source": source
            }
            
            if intent:
                data["intent"] = intent
            if actions:
                data["actions_taken"] = actions
            
            result = self.supabase.table("conversation_messages")\
                .insert(data)\
                .execute()
            
            return result.data[0]["id"] if result.data else None
            
        except Exception as e:
            logger.error("message_save_failed", error=str(e))
            return None
    
    def _extract_actions(self, response: str) -> Tuple[str, List[Dict]]:
        """Extrai ações marcadas na resposta."""
        actions = []
        clean_response = response
        
        # Pattern: [AÇÃO: tipo | detalhes]
        pattern = r'\[AÇÃO:\s*(\w+)\s*\|\s*([^\]]+)\]'
        matches = re.findall(pattern, response)
        
        for action_type, details in matches:
            actions.append({
                "type": action_type.lower(),
                "details": details.strip()
            })
        
        # Remover marcadores de ação da resposta
        clean_response = re.sub(pattern, '', response).strip()
        
        return clean_response, actions
    
    async def _detect_intent(self, message: str) -> str:
        """Detecta a intenção da mensagem."""
        message_lower = message.lower()
        
        # Intenções baseadas em keywords
        intent_keywords = {
            "task_create": ["criar tarefa", "adicionar tarefa", "nova tarefa", "preciso fazer", "tenho que"],
            "reminder_create": ["lembrar", "lembrete", "me avise", "não esquecer"],
            "question": ["como", "o que", "quando", "onde", "por que", "qual", "quais", "?"],
            "calendar_query": ["agenda", "calendário", "compromisso", "reunião", "evento"],
            "finance_query": ["gasto", "receita", "dinheiro", "financeiro", "quanto gastei"],
            "goal_query": ["objetivo", "meta", "progresso", "como estou indo"],
            "task_query": ["tarefas", "pendências", "o que tenho", "lista"],
            "report_request": ["relatório", "resumo", "balanço", "visão geral"],
            "greeting": ["oi", "olá", "bom dia", "boa tarde", "boa noite", "hey", "e aí"],
            "gratitude": ["obrigado", "valeu", "agradeço", "thanks"],
            "note": ["anotar", "ideia", "pensamento", "anotação"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return intent
        
        return "general"
    
    async def _extract_and_save_memories(
        self,
        user_id: str,
        message: str,
        response: str,
        session_id: Optional[str],
        message_id: Optional[str]
    ) -> List[Dict]:
        """Extrai informações importantes e salva como memórias."""
        memories = []
        
        try:
            # Usar Gemini para extrair informações importantes
            extraction_prompt = f"""
Analise esta conversa e extraia informações que devem ser lembradas sobre o usuário.
Retorne um JSON com array de memórias, cada uma com:
- category: "preference" | "fact" | "relationship" | "goal" | "context"
- content: descrição concisa da memória
- importance: 1-10

Conversa:
Usuário: {message}
Assistente: {response}

Retorne APENAS o JSON, sem markdown. Se não houver nada importante, retorne [].
Exemplo: [{{"category": "preference", "content": "Prefere café pela manhã", "importance": 6}}]
"""
            
            extraction = await gemini_service.generate_text(
                extraction_prompt,
                temperature=0.3,
                max_tokens=300
            )
            
            # Parse do JSON
            try:
                # Limpar possível markdown
                extraction = extraction.strip()
                if extraction.startswith("```"):
                    extraction = re.sub(r'^```\w*\n?', '', extraction)
                    extraction = re.sub(r'\n?```$', '', extraction)
                
                extracted_memories = json.loads(extraction)
                
                for mem in extracted_memories:
                    if isinstance(mem, dict) and mem.get("content"):
                        category = MemoryCategory(mem.get("category", "context"))
                        saved = await context_service.add_memory(
                            user_id=user_id,
                            category=category,
                            content=mem["content"],
                            importance=mem.get("importance", 5),
                            session_id=session_id,
                            message_id=message_id
                        )
                        if saved:
                            memories.append(saved)
                            
            except json.JSONDecodeError:
                pass  # Sem memórias extraídas
                
        except Exception as e:
            logger.warning("memory_extraction_failed", error=str(e))
        
        return memories
    
    async def _get_recent_messages(
        self,
        session_id: Optional[str],
        limit: int = 5
    ) -> List[Dict]:
        """Busca mensagens recentes da sessão."""
        if not session_id:
            return []
        
        try:
            result = self.supabase.table("conversation_messages")\
                .select("role, content, intent")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.debug("recent_messages_fetch_failed", error=str(e))
            return []
    
    async def _generate_continuation(
        self,
        user_id: str,
        recent_messages: List[Dict]
    ) -> Optional[str]:
        """
        Gera continuação natural da conversa baseado em mensagens recentes.
        Usado quando usuário confirma/concorda ("ok", "beleza").
        """
        try:
            # Formatar contexto
            context_text = "\n".join([
                f"{msg['role'].title()}: {msg['content']}"
                for msg in recent_messages[-3:]
            ])
            
            prompt = f"""Baseado nesta conversa, o usuário acabou de confirmar/concordar.

{context_text}
User: ok/beleza (confirmação)

Você deve CONTINUAR a conversa naturalmente:
- Se estava fazendo perguntas, faça a PRÓXIMA pergunta
- Se estava explicando algo, prossiga para próximo passo
- Se terminou um assunto, sugira próxima ação

NUNCA responda apenas "ok" ou "aguardando". SEMPRE avance!

Sua resposta:"""
            
            continuation = await gemini_service.generate_text(
                prompt,
                temperature=0.7,
                max_tokens=200
            )
            
            return self._clean_technical_language(continuation.strip())
            
        except Exception as e:
            logger.debug("continuation_generation_failed", error=str(e))
            return None
    
    def _clean_technical_language(self, response: str) -> str:
        """
        Remove linguagem técnica, IDs e termos robotizados da resposta.
        Torna resposta mais natural e humana.
        """
        # Remove IDs (UUIDs, hashes)
        response = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', response, flags=re.IGNORECASE)
        response = re.sub(r'ID:\s*[a-zA-Z0-9-]+', '', response, flags=re.IGNORECASE)
        response = re.sub(r'#[a-f0-9]{8}', '', response)
        
        # Remove termos técnicos robotizados
        tech_terms_map = {
            r'processado com sucesso': 'feito',
            r'item registrado': 'anotado',
            r'salvo na inbox': 'anotei',
            r'status:': '',
            r'tipo:': '',
            r'prioridade:': '',
            r'método:\s*\S+': '',
            r'categoria:': '',
            r'🤖\s*IA': '',
            r'\[ação:\s*\w+\s*\|\s*[^\]]+\]': '',
            r'acknowledge the message': '',
        }
        
        for pattern, replacement in tech_terms_map.items():
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Remove linhas vazias múltiplas
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        # Remove espaços múltiplos
        response = re.sub(r' {2,}', ' ', response)
        
        return response.strip()
    
    async def _execute_actions(
        self,
        user_id: str,
        actions: List[Dict]
    ) -> List[Dict]:
        """Executa as ações identificadas."""
        executed = []
        
        for action in actions:
            action_type = action.get("type")
            details = action.get("details", "")
            
            try:
                if action_type == "task":
                    # Criar tarefa
                    result = self.supabase.table("tasks")\
                        .insert({
                            "user_id": user_id,
                            "title": details,
                            "status": "pending",
                            "priority": 2
                        })\
                        .execute()
                    
                    if result.data:
                        executed.append({
                            "type": "task_created",
                            "id": result.data[0]["id"],
                            "title": details
                        })
                        
                elif action_type == "inbox":
                    # Salvar na inbox
                    result = self.supabase.table("inbox_items")\
                        .insert({
                            "user_id": user_id,
                            "content": details,
                            "content_type": "text",
                            "source": "conversation",
                            "status": "new"
                        })\
                        .execute()
                    
                    if result.data:
                        executed.append({
                            "type": "inbox_added",
                            "id": result.data[0]["id"]
                        })
                        
                elif action_type == "reminder":
                    # TODO: Implementar sistema de lembretes
                    executed.append({
                        "type": "reminder_pending",
                        "details": details
                    })
                    
            except Exception as e:
                logger.error("action_execution_failed", action=action_type, error=str(e))
        
        return executed
    
    # ==========================================
    # FEEDBACK E CORREÇÕES
    # ==========================================
    
    async def submit_feedback(
        self,
        user_id: str,
        message_id: str,
        feedback_type: str,
        feedback_content: Optional[str] = None,
        corrected_response: Optional[str] = None
    ) -> bool:
        """Registra feedback do usuário sobre uma resposta."""
        try:
            # Buscar resposta original
            message = self.supabase.table("conversation_messages")\
                .select("content")\
                .eq("id", message_id)\
                .execute()
            
            original = message.data[0]["content"] if message.data else None
            
            # Salvar feedback
            self.supabase.table("response_feedback")\
                .insert({
                    "user_id": user_id,
                    "message_id": message_id,
                    "feedback_type": feedback_type,
                    "original_response": original,
                    "feedback_content": feedback_content,
                    "corrected_response": corrected_response
                })\
                .execute()
            
            # Se for correção, criar memória sobre preferência
            if feedback_type == "correction" and corrected_response:
                await context_service.add_memory(
                    user_id=user_id,
                    category=MemoryCategory.FEEDBACK,
                    content=f"Corrigiu resposta: preferiu '{corrected_response[:100]}' ao invés de '{original[:100] if original else '?'}'",
                    importance=7
                )
            
            logger.info("feedback_submitted", user_id=user_id, type=feedback_type)
            return True
            
        except Exception as e:
            logger.error("feedback_submission_failed", error=str(e))
            return False
    
    # ==========================================
    # HISTÓRICO
    # ==========================================
    
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Busca histórico de conversas."""
        try:
            query = self.supabase.table("conversation_messages")\
                .select("id, role, content, created_at, intent")\
                .eq("user_id", user_id)
            
            if session_id:
                query = query.eq("session_id", session_id)
            
            result = query\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return list(reversed(result.data)) if result.data else []
            
        except Exception as e:
            logger.error("history_fetch_failed", error=str(e))
            return []
    
    # ==========================================
    # APRENDIZADO INCREMENTAL
    # ==========================================
    
    async def _incremental_learning(
        self,
        user_id: str,
        message: str,
        intent: str
    ):
        """
        Aprende de forma incremental com cada interação.
        Atualiza padrões de forma leve, sem bloquear a resposta.
        """
        try:
            now = datetime.now()
            hour = now.hour
            day_of_week = now.strftime("%a").lower()
            
            # 1. Atualizar padrão de horário de comunicação
            await self._update_time_pattern(user_id, hour, day_of_week, intent)
            
            # 2. Atualizar padrão de tópicos de interesse
            await self._update_topic_pattern(user_id, intent, message)
            
            # 3. A cada 20 mensagens, rodar análise mais profunda
            await self._check_deep_learning_trigger(user_id)
            
        except Exception as e:
            # Aprendizado não deve impactar resposta
            logger.debug("incremental_learning_failed", error=str(e))
    
    async def _update_time_pattern(
        self,
        user_id: str,
        hour: int,
        day: str,
        intent: str
    ):
        """Atualiza padrão de horários de uso."""
        try:
            # Buscar padrão existente
            result = self.supabase.table("learned_patterns")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("pattern_type", "time_preference")\
                .limit(1)\
                .execute()
            
            if result.data:
                pattern = result.data[0]
                data = pattern["pattern_data"]
                
                # Atualizar contadores de hora
                if "hour_counts" not in data:
                    data["hour_counts"] = {}
                hour_key = str(hour)
                data["hour_counts"][hour_key] = data["hour_counts"].get(hour_key, 0) + 1
                
                # Atualizar contadores de dia
                if "day_counts" not in data:
                    data["day_counts"] = {}
                data["day_counts"][day] = data["day_counts"].get(day, 0) + 1
                
                # Atualizar intents por período
                period = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
                if "intent_by_period" not in data:
                    data["intent_by_period"] = {}
                if period not in data["intent_by_period"]:
                    data["intent_by_period"][period] = {}
                data["intent_by_period"][period][intent] = \
                    data["intent_by_period"][period].get(intent, 0) + 1
                
                # Recalcular confiança
                sample_count = pattern["sample_count"] + 1
                confidence = min(0.95, 0.3 + (sample_count * 0.01))
                
                self.supabase.table("learned_patterns")\
                    .update({
                        "pattern_data": data,
                        "sample_count": sample_count,
                        "confidence": confidence,
                        "updated_at": datetime.utcnow().isoformat()
                    })\
                    .eq("id", pattern["id"])\
                    .execute()
            else:
                # Criar novo padrão
                self.supabase.table("learned_patterns")\
                    .insert({
                        "user_id": user_id,
                        "pattern_type": "time_preference",
                        "name": "Padrões de horário",
                        "description": "Quando o usuário interage com o sistema",
                        "pattern_data": {
                            "hour_counts": {str(hour): 1},
                            "day_counts": {day: 1},
                            "intent_by_period": {
                                ("morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")): {intent: 1}
                            }
                        },
                        "confidence": 0.3,
                        "sample_count": 1
                    })\
                    .execute()
                    
        except Exception as e:
            logger.debug("update_time_pattern_failed", error=str(e))
    
    async def _update_topic_pattern(
        self,
        user_id: str,
        intent: str,
        message: str
    ):
        """Atualiza padrão de tópicos de interesse."""
        try:
            # Buscar padrão existente
            result = self.supabase.table("learned_patterns")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("pattern_type", "topic_interest")\
                .limit(1)\
                .execute()
            
            if result.data:
                pattern = result.data[0]
                data = pattern["pattern_data"]
                
                # Contar intents
                if "intent_counts" not in data:
                    data["intent_counts"] = {}
                data["intent_counts"][intent] = data["intent_counts"].get(intent, 0) + 1
                
                # Detectar tópicos mencionados
                topics = self._detect_topics(message)
                if "topic_counts" not in data:
                    data["topic_counts"] = {}
                for topic in topics:
                    data["topic_counts"][topic] = data["topic_counts"].get(topic, 0) + 1
                
                sample_count = pattern["sample_count"] + 1
                confidence = min(0.95, 0.3 + (sample_count * 0.01))
                
                self.supabase.table("learned_patterns")\
                    .update({
                        "pattern_data": data,
                        "sample_count": sample_count,
                        "confidence": confidence
                    })\
                    .eq("id", pattern["id"])\
                    .execute()
            else:
                topics = self._detect_topics(message)
                self.supabase.table("learned_patterns")\
                    .insert({
                        "user_id": user_id,
                        "pattern_type": "topic_interest",
                        "name": "Tópicos de interesse",
                        "pattern_data": {
                            "intent_counts": {intent: 1},
                            "topic_counts": {t: 1 for t in topics}
                        },
                        "confidence": 0.3,
                        "sample_count": 1
                    })\
                    .execute()
                    
        except Exception as e:
            logger.debug("update_topic_pattern_failed", error=str(e))
    
    def _detect_topics(self, message: str) -> List[str]:
        """Detecta tópicos simples na mensagem."""
        topics = []
        message_lower = message.lower()
        
        topic_keywords = {
            "trabalho": ["trabalho", "reunião", "projeto", "cliente", "deadline", "entrega"],
            "saúde": ["academia", "exercício", "médico", "saúde", "treino", "corrida"],
            "finanças": ["dinheiro", "gasto", "investimento", "conta", "pagar", "receber"],
            "estudos": ["estudar", "curso", "livro", "aprender", "aula"],
            "pessoal": ["família", "amigo", "relacionamento", "casa", "viagem"],
            "criativo": ["ideia", "criar", "escrever", "desenhar", "projeto pessoal"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    async def _check_deep_learning_trigger(self, user_id: str):
        """Verifica se deve disparar análise profunda."""
        try:
            # Contar mensagens recentes sem análise
            today = datetime.utcnow().date().isoformat()
            
            messages = self.supabase.table("conversation_messages")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("role", "user")\
                .gte("created_at", f"{today}T00:00:00")\
                .execute()
            
            count = messages.count if hasattr(messages, 'count') else len(messages.data or [])
            
            # A cada 20 mensagens, disparar análise profunda
            if count and count > 0 and count % 20 == 0:
                from app.services.pattern_learning_service import pattern_learning_service
                # Executar análise mais completa (assíncrono, não bloqueante)
                await pattern_learning_service.analyze_communication_style(user_id)
                logger.info("deep_learning_triggered", user_id=user_id, message_count=count)
                
        except Exception as e:
            logger.debug("deep_learning_trigger_failed", error=str(e))
    
    def process_message_sync(
        self,
        user_id: str,
        message: str,
        message_type: str = "telegram"
    ) -> Dict[str, Any]:
        """
        Versão síncrona do process_message para compatibilidade com bot v13.
        Simplificada - apenas processa com Gemini e retorna resposta.
        """
        try:
            # Verificar cumprimento casual
            if self._is_casual_greeting(message):
                return {
                    "reply": "E aí! 👋 Tudo certo?\n\nEm que posso ajudar?",
                    "action": "greeting",
                    "parse_mode": "markdown"
                }
            
            # Gerar resposta com Gemini (síncrono)
            prompt = f"""{self.SYSTEM_PROMPT_BASE}

Mensagem do usuário: {message}

Responda de forma natural e útil."""
            
            response = self.gemini.generate_text_sync(prompt, temperature=0.7, max_tokens=400)
            
            # Limpar resposta
            clean_response = self._clean_technical_language(response)
            
            return {
                "reply": clean_response,
                "action": "message",
                "category": "general",
                "parse_mode": None
            }
            
        except Exception as e:
            logger.error("sync_message_processing_failed", error=str(e))
            return {
                "reply": "Desculpe, tive um problema. Tente novamente! 🙏",
                "action": "error",
                "parse_mode": None
            }


# Instância global
conversation_service = ConversationService()

