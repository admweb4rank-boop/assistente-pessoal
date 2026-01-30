# 🏗️ REVISÃO COMPLETA DA ARQUITETURA - Performance Points

> Documento técnico detalhando a lógica, contexto e funcionamento atual do assistente

**Data:** 26 de Janeiro de 2026  
**Status:** Sistema em produção  
**Escopo:** Performance Points (pivot do TB Personal OS)

---

## 📊 VISÃO GERAL ATUAL

### Estado do Sistema
- **Bot Telegram**: ✅ Funcionando (python-telegram-bot v13)
- **IA Conversacional**: ✅ Gemini 2.0 Flash Exp
- **Banco de Dados**: ✅ Supabase PostgreSQL
- **Frontend**: ⏳ Não implementado
- **ML**: ⏸️ Infraestrutura pronta, não ativa

---

## 🧠 SISTEMA DE CONTEXTO E PROMPTS

### 1. Contexto Fixo (System Instruction)

**Localização:** `backend/app/services/gemini_service.py` → método `chat_sync()`

```python
system_context = """Você é o assistente Performance Points, um sistema de alta performance gamificado.

**SUA PERSONALIDADE:**
- Direto, estratégico e motivacional
- Foca em ação e progresso real
- Usa linguagem acessível mas poderosa
- Celebra vitórias, desafia procrastinação

**SEU PROPÓSITO:**
Ajudar pessoas a progredirem através de:
1. **Sistema de Pontos (XP)**: Cada ação gera pontos
2. **Quests Adaptativas**: Missões diárias baseadas no perfil
3. **4 Atributos**: Presença, Disciplina, Execução, Clareza Mental
4. **Perfil Evolutivo**: Se adapta a cada 15-30 dias
5. **Conversa + Estrutura**: Tanto conversa natural quanto comandos

**CAPACIDADES:**
- Criar e gerenciar tarefas com gamificação (+XP)
- Registrar check-ins de energia (0-100)
- Gerar quests diárias personalizadas
- Conversar sobre qualquer assunto
- Classificar automaticamente mensagens em tasks/ideias/notas
- Acompanhar progresso (nível, XP, conquistas)
- Editar perfil periodicamente (/revisar)

**COMANDOS PRINCIPAIS:**
/status - Painel completo
/quest - Missão do dia
/checkin - Energia atual
/task - Criar tarefa
/quiz - Refazer onboarding

**COMO RESPONDER:**
- Se perguntarem "como pode ajudar" → Explique seu propósito único
- Se enviarem mensagem solta → Converse naturalmente, mas sugira comandos relevantes
- Se for uma tarefa → Pergunte se quer criar com /task
- Se for pergunta sobre capacidades → Destaque o diferencial

Seja engajado, mas conciso. Máximo 200 palavras por resposta.
"""
```

**Características:**
- ✅ **Fixo**: Não muda dinamicamente
- ✅ **Contextualizado**: Ensina quem é e o que faz
- ✅ **Conciso**: ~200 palavras de instrução
- ❌ **Sem RAG**: Não busca contexto do banco de dados
- ❌ **Sem Memória**: Não lembra conversas anteriores
- ❌ **Sem Perfil**: Não injeta dados do usuário

### 2. Contexto Dinâmico (RAG) - Implementado mas NÃO USADO

**Serviços Disponíveis:**

#### A. `ContextService` (`backend/app/services/context_service.py`)
```python
async def get_context_for_message(user_id, message):
    return {
        "user_info": await self._get_user_info(user_id),
        "current_mode": await self._get_current_mode(user_id),
        "recent_messages": await self._get_recent_messages(user_id, limit=5),
        "relevant_memories": await self._search_memories(user_id, message, limit=5),
        "active_patterns": await self._get_active_patterns(user_id),
        "pending_tasks": await self._get_pending_tasks(user_id, limit=5),
        "upcoming_events": await self._get_upcoming_events(user_id),
        "recent_goals": await self._get_recent_goals(user_id),
        "finance_summary": await self._get_finance_summary(user_id),
    }
```

**Status:** ⚠️ **NÃO CONECTADO** - Implementado mas não chamado no fluxo de conversação

#### B. `MemoryService` (`backend/app/services/memory_service.py`)
```python
async def get_recent_context(user_id, limit=5):
    # Busca últimas interações do usuario_logs
    # Formata para incluir no prompt LLM
    
async def format_context_for_llm(user_id, limit=5):
    # Formata contexto para string
    return "## Contexto das últimas conversas:\n..."
```

**Status:** ⚠️ **NÃO CONECTADO** - Pronto mas não usado

---

## 🔄 FLUXO DE CONVERSAÇÃO ATUAL

```
┌──────────────────────────────────────────────────────┐
│ 1. Usuário envia mensagem no Telegram               │
└─────────────────┬────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────┐
│ 2. bot_handler_unified.handle_message()              │
│    - Verifica estados (onboarding, checkin, review)  │
│    - Se nenhum estado ativo → Chama IA               │
└─────────────────┬────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────┐
│ 3. gemini_service.chat_sync()                        │
│    - Monta prompt com system_context FIXO            │
│    - Envia: system_context + mensagem do usuário    │
│    - NÃO busca contexto do banco                     │
│    - NÃO inclui perfil do usuário                    │
└─────────────────┬────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────┐
│ 4. Gemini REST API                                   │
│    - Processa com Gemini 2.0 Flash Exp              │
│    - Retorna resposta                                │
└─────────────────┬────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────┐
│ 5. Bot envia resposta ao usuário                     │
│    - parse_mode=Markdown                             │
└──────────────────────────────────────────────────────┘
```

### PROBLEMAS IDENTIFICADOS:

1. ❌ **Sem RAG**: Não busca contexto relevante do banco
2. ❌ **Sem Memória**: Não lembra conversas anteriores
3. ❌ **Sem Perfil**: Não sabe nada sobre o usuário (quiz, áreas, metas)
4. ❌ **Sem Sessões**: Cada mensagem é isolada (stateless)
5. ✅ **System Instruction OK**: Pelo menos sabe quem é

---

## 🤖 MACHINE LEARNING - Estado Atual

### Estrutura Implementada:

#### 1. `PatternLearningService`
**Localização:** `backend/app/services/pattern_learning_service.py`

**Funcionalidades:**
```python
async def analyze_time_patterns(user_id):
    # Analisa horários de uso (últimos 30 dias)
    # Detecta: horas pico, dias pico, período preferido
    # Salva padrão no context_service
    
async def analyze_task_patterns(user_id):
    # Analisa padrões de tarefas (últimos 90 dias)
    # Detecta: taxa conclusão, tempo médio, priorização
    
async def analyze_communication_style(user_id):
    # Analisa estilo de comunicação
    # Detecta: comprimento, formalidade, emoji usage
```

**Status:** ✅ Implementado | ⚠️ Não executado automaticamente

#### 2. `LearningService`
**Localização:** `backend/app/services/learning_service.py`

**Funcionalidades:**
- Gerencia itens de aprendizado
- Revisão espaçada (algoritmo SM-2)
- Trilhas de aprendizado

**Status:** ✅ Implementado | ⚠️ Não conectado ao fluxo principal

#### 3. Jobs Agendados
**Localização:** `backend/app/jobs/pattern_analysis.py`

```python
class PatternAnalysisJob:
    async def run(user_id=None):
        # Executa análise completa de padrões
        # Pode rodar para usuário específico ou todos
```

**Status:** ✅ Implementado | ❌ Não agendado (sem scheduler ativo)

### ML Service Separado
**Localização:** `ml-service/` e `ml_service/`

**Status:** 📁 Diretórios existem mas estão vazios

---

## 📦 SERVIÇOS IMPLEMENTADOS

### ✅ Serviços Funcionando:

1. **GamificationService** (`gamification_service.py`)
   - XP, níveis, conquistas
   - 4 atributos (Presença, Disciplina, Execução, Clareza)
   - Painel de status

2. **QuestService** (`quest_service.py`)
   - Geração de quests adaptativas
   - Baseado em perfil e energia
   - 6 pools de quests

3. **OnboardingServiceV2** (`onboarding_service_v2.py`)
   - Quiz de 7 perguntas
   - Salva em `quiz_answers` JSON
   - Gera arquétipo

4. **CheckinService** (`checkin_service.py`)
   - Registro de energia (0-100)
   - Tracking de métricas

5. **ProfileEditorService** (`profile_editor_service.py`)
   - Revisão periódica (15-30 dias)
   - Edição de campos do perfil

### ⚠️ Serviços Implementados mas Não Ativos:

1. **ContextService** - RAG não conectado
2. **MemoryService** - Memória não usada
3. **PatternLearningService** - Análise não executada
4. **GmailService** - Precisa OAuth
5. **GoogleCalendarService** - Precisa OAuth
6. **DriveService** - Precisa OAuth
7. **FinanceService** - Implementado, não testado
8. **ContentService** - Implementado, não testado
9. **ProjectService** - Implementado, não testado

---

## 🔧 MELHORIAS NECESSÁRIAS

### 🔴 CRÍTICO - Conversação

**Problema:** Bot "burro", não lembra contexto, não conhece o usuário

**Solução:**
```python
# Em gemini_service.chat_sync():

1. Buscar perfil do usuário:
   profile = supabase.table('profiles').select('*').eq('user_id', user_id).single()
   quiz_answers = profile['quiz_answers']
   
2. Buscar conversas recentes:
   memory_service.format_context_for_llm(user_id, limit=5)
   
3. Buscar padrões ativos:
   context_service.get_active_patterns(user_id)
   
4. Montar prompt enriquecido:
   full_prompt = f"""
   {system_context}
   
   ## PERFIL DO USUÁRIO:
   - Arquétipo: {profile['personality_profile']['archetype']}
   - Áreas prioritárias: {quiz_answers['life_areas']}
   - Habilidades: {quiz_answers['skills']}
   - Meta principal: {quiz_answers['year_goals']}
   - Bloqueios: {quiz_answers['blockers']}
   
   ## HISTÓRICO RECENTE:
   {recent_context}
   
   ## PADRÕES DETECTADOS:
   {patterns_summary}
   
   Usuário: {user_message}
   
   Responda considerando TODO o contexto acima.
   """
```

### 🟠 IMPORTANTE - Machine Learning

**Problema:** ML implementado mas não executa

**Solução:**
1. Ativar scheduler (APScheduler)
2. Agendar `pattern_analysis.py` para rodar diariamente
3. Integrar padrões detectados no prompt da IA
4. Dashboard para visualizar insights

### 🟡 RECOMENDADO - Integrações

**Problema:** Gmail, Calendar, Drive implementados mas sem OAuth

**Solução:**
1. Configurar Google OAuth corretamente
2. Implementar fluxo de autorização
3. Testar integrações end-to-end

---

## 📈 ROADMAP DE MELHORIAS

### Fase 1: RAG Básico (1-2 dias)
- [ ] Conectar `ContextService` ao `chat_sync()`
- [ ] Incluir perfil do usuário no prompt
- [ ] Incluir últimas 5 conversas
- [ ] Testar qualidade das respostas

### Fase 2: Memória de Sessão (1 dia)
- [ ] Implementar histórico de conversação
- [ ] Manter contexto na sessão do Telegram
- [ ] Limpar sessão periodicamente

### Fase 3: ML Ativo (2-3 dias)
- [ ] Ativar APScheduler
- [ ] Agendar análise de padrões (diária)
- [ ] Integrar padrões no prompt
- [ ] Dashboard de insights

### Fase 4: Integrações Google (3-4 dias)
- [ ] Configurar OAuth completo
- [ ] Testar Gmail, Calendar, Drive
- [ ] Comandos para acessar integrações

---

## 🎯 DIFERENCIAL PERFORMANCE POINTS

### O que já funciona:
✅ **Gamificação**: XP, níveis, conquistas  
✅ **Quests Adaptativas**: Baseadas em perfil  
✅ **Quiz de Onboarding**: 7 perguntas  
✅ **Perfil Evolutivo**: Revisão periódica  
✅ **Conversa Natural**: Com Gemini  

### O que falta para ser ÚNICO:
❌ **IA que lembra**: Contexto de conversas  
❌ **IA que conhece**: Perfil do usuário  
❌ **IA que aprende**: Padrões detectados  
❌ **Insights automáticos**: ML rodando  

---

## 📊 MÉTRICAS DE QUALIDADE

### Atual:
- Contexto no prompt: **~200 palavras fixas**
- Memória de conversas: **0** (não implementado)
- Uso de perfil: **0%** (não injeta)
- Padrões ativos: **0** (ML não roda)

### Ideal:
- Contexto no prompt: **500-800 palavras dinâmicas**
- Memória de conversas: **Últimas 5-10**
- Uso de perfil: **100%** (sempre inclui)
- Padrões ativos: **Detectados e usados**

---

## 🔑 CONCLUSÃO

**Status Atual:** Sistema funcional mas **"burro"** - não usa todo o potencial implementado.

**Problema Principal:** Desconexão entre serviços implementados e o fluxo de conversação.

**Solução:** Integrar RAG + Memória + ML no `chat_sync()` para criar IA contextualizada.

**Prioridade:** 🔴 CRÍTICO - Implementar RAG básico imediatamente para melhorar conversação.

---

**Próximo Passo:** Implementar conexão entre `chat_sync()` e `ContextService` para habilitar RAG.
