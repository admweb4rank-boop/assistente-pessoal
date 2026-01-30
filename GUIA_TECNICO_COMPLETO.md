# 📚 GUIA TÉCNICO COMPLETO - Performance Points Assistant

> **Para:** Desenvolvedores e Mantenedores  
> **Versão:** 2.0  
> **Data:** 26 de Janeiro de 2026

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Sistema de Aprendizado](#sistema-de-aprendizado)
4. [Como Adicionar Conhecimento](#como-adicionar-conhecimento)
5. [RAG - Retrieval Augmented Generation](#rag---retrieval-augmented-generation)
6. [Machine Learning](#machine-learning)
7. [Fluxos de Dados](#fluxos-de-dados)
8. [API e Endpoints](#api-e-endpoints)
9. [Customização Avançada](#customização-avançada)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 VISÃO GERAL

### O que é o Performance Points?

Um assistente inteligente que combina:
- **Gamificação** (XP, níveis, conquistas)
- **RAG** (Retrieval-Augmented Generation)
- **Machine Learning** (detecção de padrões)
- **Conversa Natural** (Gemini 2.0 Flash)

### Princípios de Design

1. **Contextual**: Usa dados reais do usuário em toda resposta
2. **Adaptável**: Tom e conteúdo baseados no perfil
3. **Evolutivo**: Aprende com padrões de uso
4. **Transparente**: Decisões rastreáveis e auditáveis

---

## 🏗️ ARQUITETURA DO SISTEMA

### Stack Tecnológico

```
┌─────────────────────────────────────────────────────┐
│                   INTERFACE                          │
│  • Telegram Bot (python-telegram-bot v13)           │
│  • FastAPI REST API                                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              ORCHESTRATION LAYER                     │
│  • bot_handler_unified.py                           │
│  • Gerencia estados e fluxos                        │
│  • Conecta serviços                                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│                SERVICE LAYER                         │
│  • gemini_service.py (IA conversacional)            │
│  • context_service.py (RAG)                         │
│  • memory_service.py (memória conversacional)       │
│  • pattern_learning_service.py (ML)                 │
│  • gamification_service.py (XP/níveis)              │
│  • quest_service.py (missões)                       │
│  • onboarding_service_v2.py (quiz)                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│                 DATA LAYER                           │
│  • Supabase PostgreSQL                              │
│  • Tables: profiles, tasks, checkins, etc.          │
│  • RLS (Row Level Security)                         │
└─────────────────────────────────────────────────────┘
```

### Componentes Principais

#### 1. Gemini Service (`gemini_service.py`)
**Responsabilidade:** IA conversacional

```python
def chat_sync(user_message, user_id, context):
    # 1. Monta system instruction (identidade do assistente)
    # 2. Adiciona contexto RAG (perfil, memória, padrões)
    # 3. Chama Gemini REST API
    # 4. Retorna resposta contextualizada
```

**Arquivos:**
- `backend/app/services/gemini_service.py`

#### 2. Context Service (`context_service.py`)
**Responsabilidade:** RAG - busca contexto relevante

```python
async def get_context_for_message(user_id, message):
    return {
        "user_info": perfil_completo,
        "recent_messages": ultimas_5_conversas,
        "relevant_memories": memorias_relevantes,
        "active_patterns": padroes_ml_detectados,
        "pending_tasks": tarefas_pendentes,
        "upcoming_events": eventos_proximos,
        "recent_goals": metas_ativas,
        "finance_summary": resumo_financeiro
    }
```

**Arquivos:**
- `backend/app/services/context_service.py`

#### 3. Memory Service (`memory_service.py`)
**Responsabilidade:** Memória conversacional

```python
async def save_interaction(user_id, user_message, assistant_response):
    # Salva em assistant_logs
    # Usado para histórico de conversas
```

**Arquivos:**
- `backend/app/services/memory_service.py`

#### 4. Pattern Learning Service (`pattern_learning_service.py`)
**Responsabilidade:** Machine Learning de padrões

```python
async def analyze_time_patterns(user_id):
    # Detecta horários de pico de produtividade
    
async def analyze_task_patterns(user_id):
    # Analisa taxa de conclusão e consistência
    
async def analyze_communication_style(user_id):
    # Detecta estilo de comunicação preferido
```

**Arquivos:**
- `backend/app/services/pattern_learning_service.py`
- `backend/app/jobs/pattern_analysis.py`

---

## 🧠 SISTEMA DE APRENDIZADO

### Como o Assistente Aprende?

O sistema usa **3 tipos de aprendizado**:

#### 1. Aprendizado Explícito (Quiz/Onboarding)
**Quando:** Usuário completa `/quiz`  
**Armazena:** `profiles.quiz_answers` (JSONB)

```json
{
  "communication_style": "direct",
  "life_areas": ["work_business", "body_energy"],
  "skills": ["execution", "discipline"],
  "year_goals": "Ganhar primeiro cliente",
  "blockers": ["procrastination", "focus"]
}
```

#### 2. Aprendizado Implícito (Patterns ML)
**Quando:** Job diário às 23:30  
**Armazena:** `context_patterns` (table)

**Detecta:**
- Horários de maior produtividade
- Taxa de conclusão de tarefas
- Estilo de comunicação
- Consistência de check-ins

#### 3. Aprendizado Conversacional (RAG)
**Quando:** A cada interação  
**Armazena:** `assistant_logs` (table)

**Captura:**
- Histórico de conversas
- Contexto de mensagens
- Respostas do assistente

---

## 🔧 COMO ADICIONAR CONHECIMENTO

### Método 1: Adicionar ao System Instruction

**Arquivo:** `backend/app/services/gemini_service.py`

**Localização:** Método `chat_sync()`, variável `system_context`

```python
system_context = """Você é o assistente Performance Points...

**CONHECIMENTO ADICIONAL:**

[ADICIONE AQUI NOVO CONHECIMENTO FIXO]

Exemplo:
- Como funciona o sistema de quests
- Metodologias de produtividade
- Frameworks específicos
- Processos da empresa/pessoa
"""
```

**Quando usar:**
- Conhecimento que TODOS os usuários devem ter
- Informações fixas (não mudam por usuário)
- Regras de negócio gerais

**Exemplo Prático:**
```python
# Adicionar conhecimento sobre GTD
system_context = """...

**METODOLOGIA GTD:**
O assistente usa princípios do Getting Things Done:
1. Capture tudo na inbox
2. Classifique em: task, idea, note
3. Organize por contexto e prioridade
4. Revise semanalmente
5. Execute com foco

Use esses princípios ao sugerir organização de tarefas.
"""
```

---

### Método 2: Criar Memórias Específicas

**Arquivo:** Via API ou script

**Endpoint:** `POST /api/v1/memories`

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid-do-usuario",
    "category": "KNOWLEDGE",
    "content": "Processo de vendas: 1) Qualificação 2) Proposta 3) Follow-up",
    "importance": 8,
    "tags": ["vendas", "processo"]
  }'
```

**Quando usar:**
- Conhecimento específico por usuário
- Informações que devem ser lembradas
- Processos personalizados

**Categorias disponíveis:**
- `PREFERENCE` - Preferências do usuário
- `FACT` - Fatos sobre o usuário
- `PATTERN` - Padrões detectados
- `KNOWLEDGE` - Conhecimento geral
- `GOAL` - Metas e objetivos
- `CONTEXT` - Contexto de conversas

---

### Método 3: Treinar com Documentos (Future)

**Status:** Planejado para v3.0

**Como funcionará:**
```python
# Futuro: Upload de documentos
POST /api/v1/knowledge/upload
{
  "file": "documento.pdf",
  "category": "procedimentos",
  "user_id": "uuid"
}

# Sistema fará:
# 1. Parse do documento
# 2. Chunking (dividir em partes)
# 3. Embeddings com AI
# 4. Armazenar em vector database
# 5. RAG usa na busca semântica
```

---

### Método 4: Adicionar Comandos Personalizados

**Arquivo:** `backend/app/services/bot_handler_unified.py`

```python
def cmd_novo_comando(self, update: Update, context: CallbackContext):
    """Handler para /novo_comando"""
    user_id = self._get_user_id(update.effective_user.id)
    
    # Sua lógica aqui
    resultado = processar_algo()
    
    update.message.reply_text(
        f"Resultado: {resultado}",
        parse_mode=ParseMode.MARKDOWN
    )

# Registrar o comando no setup_handlers()
dispatcher.add_handler(CommandHandler('novo_comando', self.cmd_novo_comando))
```

**Quando usar:**
- Funcionalidades específicas
- Integrações com sistemas externos
- Workflows automatizados

---

## 🔍 RAG - RETRIEVAL AUGMENTED GENERATION

### Como Funciona?

```
Usuário: "qual minha meta?"
    ↓
1. Context Service busca dados relevantes:
   - quiz_answers.year_goals
   - recent_goals table
   - memories com tag "goal"
    ↓
2. Monta contexto enriquecido:
   "PERFIL: Meta principal: Ganhar primeiro cliente"
    ↓
3. Gemini Service monta prompt:
   System Instruction + Contexto + Mensagem
    ↓
4. Gemini responde com contexto:
   "Sua meta é ganhar seu primeiro cliente! 
    Você tem 3 tarefas pendentes relacionadas..."
```

### Fonte de Dados RAG

| Fonte | Tabela | Usado Para |
|-------|--------|------------|
| Perfil | `profiles` | Info básica, quiz |
| Conversas | `assistant_logs` | Histórico |
| Padrões | `context_patterns` | ML insights |
| Tarefas | `tasks` | Pendências |
| Check-ins | `checkins` | Energia/humor |
| Metas | `goals` | Objetivos |
| Eventos | `events` | Agenda |
| Finanças | `transactions` | Situação financeira |

### Customizar RAG

**Arquivo:** `backend/app/services/context_service.py`

```python
async def get_context_for_message(self, user_id, message):
    context = {}
    
    # ADICIONAR NOVA FONTE DE CONTEXTO
    context["custom_data"] = await self._get_custom_data(user_id)
    
    return context

async def _get_custom_data(self, user_id):
    # Buscar dados de nova tabela
    result = self.supabase.table('nova_tabela')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    return result.data
```

---

## 🤖 MACHINE LEARNING

### Padrões Detectados Automaticamente

#### 1. Time Patterns (Horários)
**Analisa:** Últimos 30 dias de mensagens  
**Detecta:**
- Horários de pico (4 mais frequentes)
- Período preferido (manhã/tarde/noite)
- Dias de maior atividade

**Uso:** Sugerir melhor momento para tarefas

#### 2. Task Patterns (Tarefas)
**Analisa:** Últimos 90 dias de tarefas  
**Detecta:**
- Taxa de conclusão
- Tempo médio de conclusão
- Priorização (alta/média/baixa)

**Uso:** Ajustar dificuldade de quests

#### 3. Communication Style (Comunicação)
**Analisa:** Últimas 100 mensagens  
**Detecta:**
- Comprimento médio de mensagens
- Formalidade (0-10)
- Uso de emojis

**Uso:** Adaptar tom do assistente

### Job de Análise

**Arquivo:** `backend/app/jobs/pattern_analysis.py`

**Agenda:** Diariamente às 23:30

```python
class PatternAnalysisJob:
    async def run(self, user_id=None):
        # Se user_id específico, analisa apenas ele
        # Se None, analisa todos usuários ativos
        
        for user in users:
            await pattern_learning_service.analyze_time_patterns(user)
            await pattern_learning_service.analyze_task_patterns(user)
            await pattern_learning_service.analyze_communication_style(user)
```

**Como adicionar novo padrão:**

1. Adicionar método em `pattern_learning_service.py`:
```python
async def analyze_novo_padrao(self, user_id):
    # Buscar dados
    # Analisar
    # Salvar em context_patterns
    pass
```

2. Adicionar no job:
```python
await pattern_learning_service.analyze_novo_padrao(user)
```

---

## 🔄 FLUXOS DE DADOS

### Fluxo de Mensagem

```
Telegram → bot_handler_unified.handle_message()
    ↓
1. Verifica estado (onboarding? checkin? review?)
    ↓
2. Se conversa normal:
    ├─ Busca perfil (Supabase)
    ├─ Busca contexto RAG (10 fontes)
    ├─ Busca memória (últimas 5 conversas)
    └─ Monta enriched_context
    ↓
3. gemini_service.chat_sync()
    ├─ System instruction (350 palavras)
    ├─ Contexto dinâmico (300-500 palavras)
    └─ Mensagem do usuário
    ↓
4. Gemini 2.0 Flash processa
    ↓
5. Resposta → Usuário
    ↓
6. memory_service.save_interaction()
```

### Fluxo de Comando

```
Telegram: /status
    ↓
bot_handler_unified.cmd_status()
    ↓
gamification_service.format_status_message()
    ├─ Busca profile
    ├─ Calcula métricas reais
    ├─ Formata dashboard
    └─ Retorna mensagem
    ↓
Telegram ← resposta formatada
```

### Fluxo de Quiz

```
Telegram: /quiz
    ↓
onboarding_service_v2.start_onboarding()
    ↓
Loop de 7 perguntas:
    ├─ Exibe pergunta com botões
    ├─ Usuário clica/digita
    ├─ Salva resposta
    └─ Próxima pergunta
    ↓
complete_onboarding()
    ├─ Analisa respostas
    ├─ Define arquétipo
    ├─ Salva em profiles.quiz_answers
    └─ Mensagem personalizada
    ↓
Telegram ← conclusão com próximos passos
```

---

## 🌐 API E ENDPOINTS

### Endpoints Disponíveis

```
POST   /api/v1/chat                 - Conversa com IA
GET    /api/v1/profile/{user_id}    - Buscar perfil
PUT    /api/v1/profile/{user_id}    - Atualizar perfil
POST   /api/v1/tasks                - Criar tarefa
GET    /api/v1/tasks/{user_id}      - Listar tarefas
POST   /api/v1/checkins             - Registrar check-in
GET    /api/v1/quests/{user_id}     - Buscar quest do dia
POST   /api/v1/memories             - Criar memória
GET    /api/v1/patterns/{user_id}   - Buscar padrões ML
GET    /api/v1/health               - Health check
```

### Exemplo: Adicionar Conhecimento via API

```bash
# 1. Criar memória de conhecimento
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "user_id": "uuid",
    "category": "KNOWLEDGE",
    "content": "Framework SCRUM: Sprints de 2 semanas, Daily de 15min",
    "importance": 9,
    "tags": ["scrum", "agile", "processo"]
  }'

# 2. Associar ao contexto
# O RAG automaticamente incluirá em conversas sobre "processo" ou "scrum"
```

---

## 🎨 CUSTOMIZAÇÃO AVANÇADA

### 1. Personalizar Tom do Assistente

**Por arquétipo:**

```python
# Em gemini_service.py
if context.get('personality_profile', {}).get('archetype') == 'Executor Pragmático':
    system_context += "\n\nTom: Direto, sem floreios. Foco em ação."
elif archetype == 'Estrategista de Performance':
    system_context += "\n\nTom: Analítico, reflexivo. Use dados."
```

### 2. Adicionar Nova Quest

**Arquivo:** `backend/app/services/quest_service.py`

```python
# Em _build_quest_pools()
self.quest_pools['nova_categoria'] = [
    {
        'id': 'nova_quest_1',
        'title': 'Título da Quest',
        'description': 'Descrição',
        'xp_reward': 100,
        'difficulty': 'medium',
        'estimated_time': 30,
        'requirements': ['area:work_business']
    }
]
```

### 3. Criar Novo Tipo de Check-in

**Arquivo:** `backend/app/services/checkin_service.py`

```python
async def register_novo_checkin(self, user_id, value, notes=None):
    result = self.supabase.table('checkins').insert({
        'user_id': user_id,
        'checkin_type': 'novo_tipo',
        'value': value,
        'notes': notes
    }).execute()
    return result.data
```

### 4. Integração Externa

```python
# Exemplo: Integrar com Notion
class NotionService:
    async def sync_tasks(self, user_id):
        # Buscar tarefas do Notion
        # Criar no Performance Points
        pass
```

---

## 🐛 TROUBLESHOOTING

### Sistema não lembra conversas

**Causa:** `memory_service.save_interaction()` não está sendo chamado

**Solução:**
```bash
# Verificar logs
grep "memory_save" /tmp/bot_final.log

# Se não aparece, verificar bot_handler_unified.py linha ~920
```

### ML não detecta padrões

**Causa:** Job não está rodando ou dados insuficientes

**Solução:**
```bash
# Verificar se scheduler está ativo
grep "Scheduler started" /tmp/bot_final.log

# Verificar job manual
curl http://localhost:8000/api/v1/patterns/run
```

### Contexto RAG está vazio

**Causa:** `context_service` não está sendo chamado

**Solução:**
```python
# Em bot_handler_unified.py, verificar se tem:
user_context = await context_service.get_context_for_message(user_id, message)
```

### Gemini retorna erro 429

**Causa:** Rate limit atingido

**Solução:** Sistema já tem fallback automático para 2ª chave
```python
# Verificar em gemini_service.py:
self.api_keys = [KEY1, KEY2]  # Adicionar mais chaves
```

---

## 📚 REFERÊNCIAS TÉCNICAS

### Arquivos Importantes

```
backend/app/services/
├── gemini_service.py         # IA conversacional
├── context_service.py        # RAG
├── memory_service.py         # Memória
├── pattern_learning_service.py # ML
├── gamification_service.py   # XP/níveis
├── quest_service.py          # Missões
├── onboarding_service_v2.py  # Quiz
└── bot_handler_unified.py    # Orquestrador

backend/app/jobs/
└── pattern_analysis.py       # Job ML diário

backend/app/api/v1/endpoints/
├── chat.py                   # Endpoint conversa
├── profile.py                # Endpoint perfil
└── patterns.py               # Endpoint ML
```

### Banco de Dados

**Tabelas principais:**
- `profiles` - Perfil do usuário
- `assistant_logs` - Histórico de conversas
- `context_patterns` - Padrões ML
- `tasks` - Tarefas
- `checkins` - Check-ins
- `goals` - Metas
- `achievements` - Conquistas

### Variáveis de Ambiente

```bash
GEMINI_API_KEY=sua-chave-1
GEMINI_API_KEY_2=sua-chave-2
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=sua-service-key
TELEGRAM_BOT_TOKEN=seu-token
OWNER_TELEGRAM_CHAT_ID=seu-chat-id
```

---

## 🚀 PRÓXIMOS PASSOS

### Roadmap de Aprendizado

- [ ] **v2.1** - Upload de documentos (PDFs, TXTs)
- [ ] **v2.2** - Vector database para busca semântica
- [ ] **v2.3** - Fine-tuning com conversas do usuário
- [ ] **v3.0** - Agente autônomo com ferramentas

### Como Contribuir

1. Fork o repositório
2. Crie branch feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Abra Pull Request

---

**Documentação mantida por:** Time Performance Points  
**Última atualização:** 26 de Janeiro de 2026  
**Versão do Sistema:** 2.0
