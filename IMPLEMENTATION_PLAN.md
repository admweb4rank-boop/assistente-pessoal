# 🚀 TB Personal OS - Plano de Implementação

> Documento de acompanhamento das etapas de desenvolvimento

**Início:** 18/01/2026  
**Status:** EM ANDAMENTO

---

## 📊 Visão Geral do Progresso

| Fase | Descrição | Status | Progresso |
|------|-----------|--------|-----------|
| **FASE 1** | Fundação Backend | ✅ Concluído | 100% |
| **FASE 2** | Integrações Google | ⏳ Aguardando | 0% |
| **FASE 3** | Bot Telegram Completo | 🔄 Em andamento | 30% |
| **FASE 4** | Frontend MVP | ⏳ Aguardando | 0% |
| **FASE 5** | ML e Insights | ⏳ Aguardando | 0% |

---

## 🔷 FASE 1: Fundação Backend

### ETAPA 1.1: Unificar e Corrigir Bot Handler
**Status:** ✅ CONCLUÍDO

**Arquivos criados:**
- ✅ `backend/app/services/bot_handler_unified.py` - Handler unificado
- ✅ `backend/run_bot.py` - Script para executar o bot

**Funcionalidades implementadas:**
- ✅ Comandos: /start, /help, /inbox, /tasks, /task, /done, /checkin, /resumo
- ✅ Classificação de mensagens (keywords + Gemini AI)
- ✅ Salvamento na inbox com metadados
- ✅ Logging estruturado
- ✅ Tratamento de erros

---

### ETAPA 1.2: Criar Endpoints API
**Status:** ✅ CONCLUÍDO

**Arquivos criados:**
- ✅ `backend/app/models/inbox.py` - Schemas Pydantic para inbox
- ✅ `backend/app/models/tasks.py` - Schemas Pydantic para tasks
- ✅ `backend/app/models/common.py` - Schemas de resposta padrão
- ✅ `backend/app/api/v1/dependencies/auth.py` - Autenticação
- ✅ `backend/app/api/v1/endpoints/inbox.py` - CRUD inbox
- ✅ `backend/app/api/v1/endpoints/tasks.py` - CRUD tasks
- ✅ `backend/app/api/v1/endpoints/telegram.py` - Webhook Telegram

**Endpoints implementados:**

#### Inbox (`/api/v1/inbox`)
- ✅ `POST /inbox` - Criar item
- ✅ `GET /inbox` - Listar com filtros
- ✅ `GET /inbox/{id}` - Obter item
- ✅ `PATCH /inbox/{id}` - Atualizar
- ✅ `DELETE /inbox/{id}` - Deletar
- ✅ `POST /inbox/{id}/process` - Processar com IA
- ✅ `POST /inbox/archive-processed` - Arquivar processados

#### Tasks (`/api/v1/tasks`)
- ✅ `POST /tasks` - Criar tarefa
- ✅ `GET /tasks` - Listar com filtros
- ✅ `GET /tasks/today` - Tarefas de hoje
- ✅ `GET /tasks/overdue` - Tarefas atrasadas
- ✅ `GET /tasks/{id}` - Obter tarefa
- ✅ `PATCH /tasks/{id}` - Atualizar
- ✅ `POST /tasks/{id}/complete` - Concluir
- ✅ `DELETE /tasks/{id}` - Deletar
- ✅ `POST /tasks/bulk-update` - Atualização em lote

#### Telegram (`/api/v1/telegram`)
- ✅ `POST /telegram/webhook` - Receber updates
- ✅ `GET /telegram/webhook/info` - Info do webhook
- ✅ `POST /telegram/webhook/set` - Configurar webhook
- ✅ `DELETE /telegram/webhook` - Remover webhook
- ✅ `POST /telegram/send` - Enviar mensagem

---

### ETAPA 1.3: Integrar Classificação Gemini Real
**Status:** ⏳ AGUARDANDO

**Funcionalidades:**
- [ ] Classificar mensagens (categoria, tipo, prioridade)
- [ ] Extrair entidades (pessoas, datas, valores)
- [ ] Sugerir ações automáticas
- [ ] Responder perguntas com contexto

**Tarefas:**
- [ ] Criar prompts estruturados para classificação
- [ ] Implementar extração de JSON do Gemini
- [ ] Criar fallback para erros de parsing
- [ ] Cache de classificações similares
- [ ] Logging de todas as interações

**Arquivos afetados:**
- `backend/app/services/gemini_service.py`
- `backend/app/services/assistant_service.py` (novo)

---

### ETAPA 1.4: Middleware de Autenticação
**Status:** ⏳ AGUARDANDO

**Funcionalidades:**
- [ ] Validar JWT do Supabase
- [ ] Dependência `get_current_user()`
- [ ] Proteção de rotas
- [ ] Rate limiting básico

**Arquivos a criar:**
- `backend/app/api/v1/dependencies/auth.py`
- `backend/app/core/security.py`

---

## 🔷 FASE 2: Integrações Google

### ETAPA 2.1: Google OAuth Flow
- [ ] Endpoints de OAuth (`/auth/google/login`, `/auth/google/callback`)
- [ ] Salvar tokens em `oauth_tokens`
- [ ] Refresh automático de tokens

### ETAPA 2.2: Calendar Sync (Read)
- [ ] Listar calendários do usuário
- [ ] Sincronizar eventos (próximas 24h)
- [ ] Cache em `calendar_events_cache`

### ETAPA 2.3: Calendar Create Events
- [ ] Criar evento via comando Telegram
- [ ] Criar evento via API

### ETAPA 2.4: Gmail Básico
- [ ] Listar emails não lidos
- [ ] Enviar email via comando

---

## 🔷 FASE 3: Bot Telegram Completo

### ETAPA 3.1: Comandos de Tasks
- [ ] `/task criar [título]` - Criar tarefa
- [ ] `/tasks` - Listar pendentes
- [ ] `/done [id]` - Marcar como concluída
- [ ] `/task editar [id] [novo título]` - Editar

### ETAPA 3.2: Comandos de Check-in
- [ ] `/checkin energia [1-10]`
- [ ] `/checkin humor [emoji/texto]`
- [ ] `/checkin sono [horas]`
- [ ] `/checkin` - Check-in interativo

### ETAPA 3.3: Rotinas Automáticas
- [ ] Resumo manhã (8h) - agenda + prioridades
- [ ] Fechamento noite (22h) - review + check-in
- [ ] Planejamento domingo (19h) - semana

### ETAPA 3.4: Contexto de Memória
- [ ] Últimas 5 mensagens como contexto
- [ ] Profile do usuário (goals, principles)
- [ ] Referência a items anteriores

---

## 🔷 FASE 4: Frontend MVP

### ETAPA 4.1: Layout e Navegação
- [ ] Sidebar com menu
- [ ] Header com user info
- [ ] Rotas principais

### ETAPA 4.2: Autenticação Supabase
- [ ] Login page
- [ ] Register page
- [ ] Auth context
- [ ] Protected routes

### ETAPA 4.3: Dashboard Inbox
- [ ] Lista de items
- [ ] Filtros por categoria/status
- [ ] Ação rápida (processar, arquivar)

### ETAPA 4.4: Tasks View
- [ ] Lista de tarefas
- [ ] Criar/editar tarefa
- [ ] Kanban básico (opcional)

---

## 🔷 FASE 5: ML e Insights

### ETAPA 5.1: Job Scheduler
- [ ] APScheduler configurado
- [ ] Jobs de rotina
- [ ] Jobs de análise

### ETAPA 5.2: Padrões de Produtividade
- [ ] Correlação energia x tarefas
- [ ] Horários mais produtivos
- [ ] Padrões de procrastinação

### ETAPA 5.3: Recomendações Simples
- [ ] Baseadas em heurísticas
- [ ] Salvar em `recommendations`
- [ ] Enviar via Telegram

---

## 📝 Log de Progresso

### 18/01/2026
- ✅ Análise completa do projeto
- ✅ Identificação de gargalos
- ✅ Criação do plano de implementação
- ✅ Criação do arquivo de instruções (.cursorrules)
- ✅ **ETAPA 1.1 CONCLUÍDA**: Bot handler unificado
  - Criado `bot_handler_unified.py` com todos os comandos
  - Criado `run_bot.py` para execução
  - Classificação com Gemini AI + fallback keywords
- ✅ **ETAPA 1.2 CONCLUÍDA**: Endpoints API
  - 7 endpoints de inbox
  - 9 endpoints de tasks
  - 5 endpoints de telegram
  - 6 endpoints de assistant
  - Models Pydantic completos
  - Sistema de autenticação (JWT + API Key)
- ✅ **ETAPA 1.3 CONCLUÍDA**: GeminiService melhorado
  - Classificação de mensagens com IA
  - Extração de entidades
  - Geração de resumos
  - Fallback robusto quando indisponível
- ✅ **ETAPA 1.4 CONCLUÍDA**: Assistant Service
  - Orquestração central
  - Gestão de contexto
  - Rotinas (manhã/noite)
  - Estatísticas de produtividade

### Arquivos Criados/Modificados:
```
backend/
├── app/
│   ├── api/v1/
│   │   ├── __init__.py (atualizado)
│   │   ├── dependencies/
│   │   │   ├── __init__.py (novo)
│   │   │   └── auth.py (novo)
│   │   └── endpoints/
│   │       ├── __init__.py (atualizado)
│   │       ├── inbox.py (novo)
│   │       ├── tasks.py (novo)
│   │       ├── telegram.py (novo)
│   │       └── assistant.py (novo)
│   ├── models/
│   │   ├── __init__.py (atualizado)
│   │   ├── inbox.py (novo)
│   │   ├── tasks.py (novo)
│   │   └── common.py (novo)
│   └── services/
│       ├── __init__.py (atualizado)
│       ├── gemini_service.py (melhorado)
│       ├── assistant_service.py (novo)
│       └── bot_handler_unified.py (novo)
├── run_bot.py (novo)
.cursorrules (novo)
IMPLEMENTATION_PLAN.md (novo)
```

---

## 🎯 Próxima Ação

**FASE 2: Integrações Google**

1. ⏳ Configurar Google Cloud Project
2. ⏳ Implementar OAuth flow
3. ⏳ Integrar Google Calendar
4. ⏳ Integrar Gmail

**OU**

**FASE 3: Bot Telegram Completo**

1. ⏳ Testar bot unificado
2. ⏳ Implementar check-ins
3. ⏳ Configurar rotinas automáticas
4. ⏳ Melhorar contexto de memória

---
*Documento atualizado automaticamente durante o desenvolvimento*
