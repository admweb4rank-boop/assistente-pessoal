# TB Personal OS (Igor) - Escopo e Backlog Completo

**Data:** 04/01/2026  
**Versão:** 1.0  
**Status:** MVP em Desenvolvimento

---

## 1. Visão do Produto

### 1.1 Objetivo do Sistema

Construir um assistente operacional e evolutivo para o Igor:

- ✅ **Centraliza entradas** (Telegram/WhatsApp, web, voz/texto, links, docs)
- ✅ **Organiza vida/negócios** em módulos
- 🔄 **Executa ações** via integrações (agenda, email, tasks)
- ⏳ **Aprende com dados** (padrões e recomendações)
- ⏳ **Cria rotinas** e alertas úteis
- 🔄 **Vira "segundo cérebro"** com memória confiável + logs

**Fluxo central:**  
`Input → Normalização → Memória/DB → LLM (Gemini) → Tools → Output → Log → Aprendizado`

### 1.2 Princípios do Produto

1. **Baixa fricção**: captar rápido (Telegram primeiro) ✅
2. **Confiabilidade**: tudo vira registro e histórico (logs, timeline) ✅
3. **Ação > conversa**: conversa serve para decidir e executar 🔄
4. **Aprendizado incremental**: começa simples, melhora com dados ⏳
5. **Privacidade e controle**: você manda, o sistema sugere ✅

### 1.3 Importante

O assistente **NÃO é só chat**. Ele é:  
**Captura → Processamento → Ação → Aprendizado → Melhoria Contínua**

---

## 2. Arquitetura Técnica

### 2.1 Stack Tecnológico

| Camada | Tecnologia | Status |
|--------|------------|--------|
| **Frontend** | React 18.2, TypeScript, Vite, Tailwind | ✅ Estrutura criada |
| **Backend** | Python 3.8, FastAPI 0.108.0, uvicorn | ✅ Funcionando |
| **Database** | Supabase (PostgreSQL 15+) | ✅ Schema executado (18 tabelas) |
| **AI/LLM** | Google Gemini API | ✅ Configurado, ⏳ Integração completa |
| **Comunicação** | Telegram Bot (Evolution WhatsApp futuro) | ✅ Bot funcionando |
| **Integrações** | Google Calendar, Gmail, Drive, Sheets | ⏳ A fazer |
| **ML/Analytics** | Python (scikit-learn, pandas) | ⏳ A fazer |
| **Job Scheduler** | APScheduler / Supabase Cron | ⏳ A fazer |

### 2.2 Componentes da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  Dashboard | Inbox | Planner | Projects | Content | Health  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              SUPABASE (PostgreSQL + Auth + Storage)         │
│  18 Tabelas | RLS | Triggers | Views | Functions           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│         PYTHON ASSISTANT API (FastAPI)                      │
│  Orchestration | Tool Calling | Context Management         │
└─────────┬───────────────────────────┬───────────────────────┘
          │                           │
┌─────────▼─────────┐       ┌────────▼────────┐
│  GEMINI AI        │       │  INTEGRATIONS   │
│  Classification   │       │  Google APIs    │
│  Entity Extract   │       │  Telegram Bot   │
│  Recommendations  │       │  Evolution API  │
└───────────────────┘       └─────────────────┘
```

### 2.3 Database Schema (18 Tabelas)

**Core:**
- ✅ `users` - Usuários do sistema
- ✅ `profiles` - Preferências e configurações
- ✅ `telegram_chats` - Chats do Telegram

**Inbox & Notes:**
- ✅ `inbox_items` - Entrada unificada
- ✅ `notes` - Notas processadas

**Tasks & Habits:**
- ✅ `tasks` - Tarefas e to-dos
- ✅ `habits` - Hábitos rastreados
- ✅ `checkins` - Registros de métricas

**Calendar:**
- ✅ `calendar_events_cache` - Cache do Google Calendar

**Projects:**
- ✅ `projects` - Projetos e iniciativas
- ✅ `project_items` - Items dentro de projetos
- ✅ `contacts` - Pessoas e empresas

**Content OS:**
- ✅ `content_ideas` - Ideias de conteúdo
- ✅ `content_posts` - Posts publicados

**Finance:**
- ✅ `transactions` - Entradas e saídas

**AI & ML:**
- ✅ `assistant_logs` - Logs de todas as ações
- ✅ `recommendations` - Recomendações do sistema
- ✅ `metrics` - Métricas gerais

**Integrations:**
- ✅ `oauth_tokens` - Tokens OAuth (Google)

---

## 3. Módulos Funcionais

### 3.1 Inbox Unificada

**Status:** 🔄 40% Completo

**Funcionalidades:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Receber mensagens Telegram | ✅ Done | P0 |
| Salvar na tabela inbox_items | ✅ Done | P0 |
| Classificação básica (keywords) | ✅ Done | P0 |
| Classificação com Gemini AI | ⏳ To-Do | P0 |
| Extração de entidades (pessoas, datas) | ⏳ To-Do | P1 |
| Sugestão de ações | ⏳ To-Do | P1 |
| Web form para captura | ⏳ To-Do | P2 |
| Upload de arquivos | ⏳ To-Do | P2 |
| Captura de links com metadata | ⏳ To-Do | P2 |

**Backlog:**
- [ ] **P0** - Integrar Gemini para classificação inteligente
- [ ] **P1** - Extrair entidades (pessoas, datas, valores)
- [ ] **P1** - Sugerir ações ("criar tarefa", "agendar", "arquivar")
- [ ] **P1** - Comando `/inbox` listar items com paginação
- [ ] **P2** - Filtros (por categoria, status, data)
- [ ] **P2** - Web form no frontend
- [ ] **P2** - Upload de arquivos (Supabase Storage)

### 3.2 Memória e Conhecimento

**Status:** ⏳ 10% Completo

**Tipos de Memória:**

| Tipo | Descrição | Status |
|------|-----------|--------|
| **Curta** | Contexto últimas interações | ⏳ To-Do |
| **Longa** | Preferências, objetivos, projetos | ⏳ To-Do |
| **Base conhecimento** | Docs, links, arquivos | ⏳ To-Do |
| **Timeline** | Histórico eventos e decisões | ✅ Done (assistant_logs) |

**Backlog:**
- [ ] **P0** - Sistema de contexto para conversas (últimas 5 mensagens)
- [ ] **P1** - Profile do usuário (goals, principles)
- [ ] **P1** - Busca semântica em notas/docs
- [ ] **P2** - Timeline visual no frontend
- [ ] **P2** - Edição de memória ("corrigir informação")

### 3.3 Planner e Rotinas

**Status:** ⏳ 5% Completo

**Funcionalidades:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Criar tarefas via Telegram | ⏳ To-Do | P0 |
| Listar tarefas pendentes (`/tasks`) | ⏳ To-Do | P0 |
| Marcar tarefa como concluída | ⏳ To-Do | P0 |
| Integração Google Calendar (leitura) | ⏳ To-Do | P0 |
| Criar eventos no Calendar | ⏳ To-Do | P1 |
| Rotina manhã (resumo do dia) | ⏳ To-Do | P0 |
| Rotina noite (fechamento) | ⏳ To-Do | P0 |
| Rotina domingo (planejamento semanal) | ⏳ To-Do | P1 |
| Check-ins (energia/humor/sono) | ⏳ To-Do | P1 |

**Backlog:**
- [ ] **P0** - Comando `/task criar [título]`
- [ ] **P0** - Comando `/tasks` listar pendentes
- [ ] **P0** - OAuth Google Calendar
- [ ] **P0** - Sincronizar eventos próximos (24h)
- [ ] **P0** - Rotina manhã (7h): resumo + agenda + prioridades
- [ ] **P0** - Rotina noite (21h): check-in + review
- [ ] **P1** - Comando `/checkin energia 8 humor 👍 sono 7h`
- [ ] **P1** - View de produtividade semanal
- [ ] **P2** - Sugestão de slots livres para reuniões

### 3.4 Projects & CEO Mode

**Status:** ⏳ 0% Completo

**Funcionalidades:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Criar projeto | ⏳ To-Do | P1 |
| Associar tarefas a projetos | ⏳ To-Do | P1 |
| Dashboard de projetos ativos | ⏳ To-Do | P1 |
| Registrar decisões | ⏳ To-Do | P2 |
| Follow-ups automáticos | ⏳ To-Do | P2 |
| Integração Drive (pastas por projeto) | ⏳ To-Do | P2 |
| Gmail threads por projeto | ⏳ To-Do | P3 |

**Backlog:**
- [ ] **P1** - Comando `/projeto criar [nome]`
- [ ] **P1** - Comando `/projeto status [nome]`
- [ ] **P1** - Dashboard frontend (cards de projetos)
- [ ] **P2** - Registro de reuniões e decisões
- [ ] **P2** - Lembretes de follow-up (X dias sem movimento)
- [ ] **P2** - Google Drive: pasta automática por projeto
- [ ] **P3** - Gmail: associar threads a projetos

### 3.5 Content OS

**Status:** ⏳ 0% Completo

**Funcionalidades:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Capturar ideias via Telegram | ⏳ To-Do | P1 |
| Listar ideias pendentes | ⏳ To-Do | P1 |
| Gerar variações por canal (IG/LinkedIn) | ⏳ To-Do | P2 |
| Calendário editorial | ⏳ To-Do | P2 |
| Tracking performance (manual) | ⏳ To-Do | P2 |
| Recomendações ML (padrões) | ⏳ To-Do | P3 |

**Backlog:**
- [ ] **P1** - Comando `/ideia [texto]` salva em content_ideas
- [ ] **P1** - Comando `/ideias` lista pendentes
- [ ] **P2** - Gemini: gerar versões (IG story, LinkedIn post)
- [ ] **P2** - Dashboard editorial (calendário)
- [ ] **P2** - Input manual de métricas (views, likes, comments)
- [ ] **P3** - ML: "posts do tipo X performam Y% melhor"

### 3.6 Health OS

**Status:** ⏳ 0% Completo

**Funcionalidades:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Check-in rápido (energia/humor/sono) | ⏳ To-Do | P1 |
| Log de treinos | ⏳ To-Do | P2 |
| Metas nutricionais | ⏳ To-Do | P2 |
| Correlações (sono x produtividade) | ⏳ To-Do | P3 |
| Recomendações comportamentais | ⏳ To-Do | P3 |

**Backlog:**
- [ ] **P1** - Comando `/checkin energia 7 humor 👍 sono 6h30`
- [ ] **P1** - Dashboard de métricas (gráficos simples)
- [ ] **P2** - Comando `/treino [tipo] [minutos]`
- [ ] **P2** - Meta de treinos semanais (alerta se não atingir)
- [ ] **P3** - ML: "quando dorme < 6h, produtividade cai 30%"

### 3.7 Finance OS

**Status:** ⏳ 0% Completo

**Funcionalidades:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Registrar entradas/saídas | ⏳ To-Do | P2 |
| Recorrências (clientes fixos) | ⏳ To-Do | P2 |
| Metas de caixa | ⏳ To-Do | P2 |
| Alertas de risco | ⏳ To-Do | P3 |
| Export para Sheets | ⏳ To-Do | P3 |

**Backlog:**
- [ ] **P2** - Comando `/receita 5000 Cliente X Projeto Y`
- [ ] **P2** - Comando `/despesa 300 AWS Infra`
- [ ] **P2** - Dashboard de fluxo de caixa
- [ ] **P3** - Alerta: "gastos subiram 20% vs mês passado"
- [ ] **P3** - Export automático para Google Sheets

### 3.8 Machine Learning & Insights

**Status:** ⏳ 0% Completo

**Objetivos:**
1. Detectar padrões de produtividade
2. Correlacionar hábitos x energia
3. Correlacionar conteúdo x performance
4. Detectar "loops" (procrastinação, gargalos)
5. Recomendar ajustes testáveis

**Features ML:**

| Feature | Status | Prioridade |
|---------|--------|------------|
| Análise de produtividade (horários) | ⏳ To-Do | P2 |
| Correlação sono x energia | ⏳ To-Do | P2 |
| Padrões de conteúdo | ⏳ To-Do | P3 |
| Detecção de procrastinação | ⏳ To-Do | P3 |
| Sistema de recomendações | ⏳ To-Do | P2 |

**Backlog:**
- [ ] **P2** - Job semanal: análise de tarefas concluídas por horário
- [ ] **P2** - Recomendação: "Você rende mais entre 9-11h"
- [ ] **P2** - Correlação: sono x energia x tarefas concluídas
- [ ] **P3** - Padrão: "Follow-ups acumulam nas sextas"
- [ ] **P3** - Dashboard Insights no frontend

---

## 4. Integrações

### 4.1 Google APIs

**Status:** ⏳ Credenciais configuradas, integração pendente

| Integração | Funcionalidades | Status | Prioridade |
|------------|-----------------|--------|------------|
| **Calendar** | Ler eventos, criar eventos, sugerir slots | ⏳ To-Do | P0 |
| **Gmail** | Ler threads, rascunhar respostas | ⏳ To-Do | P2 |
| **Drive** | Organizar arquivos por projeto | ⏳ To-Do | P2 |
| **Sheets** | Exports e relatórios | ⏳ To-Do | P3 |

**Backlog:**
- [ ] **P0** - OAuth flow completo (Calendar)
- [ ] **P0** - Listar eventos próximos (24h, 7 dias)
- [ ] **P0** - Criar evento via comando Telegram
- [ ] **P2** - Gmail: listar últimos emails não lidos
- [ ] **P2** - Gmail: rascunhar resposta (você aprova)
- [ ] **P2** - Drive: criar pasta por projeto
- [ ] **P3** - Sheets: export transações, métricas

### 4.2 Telegram Bot

**Status:** ✅ Funcionando (v13.15)

**Comandos Implementados:**
- ✅ `/start` - Inicialização e registro
- ✅ `/help` - Lista de comandos
- ✅ `/inbox` - Ver inbox (vazia por enquanto)
- ✅ Mensagens livres → salvam na inbox

**Comandos Pendentes:**
- ⏳ `/tasks` - Listar tarefas
- ⏳ `/task criar [título]` - Criar tarefa
- ⏳ `/task done [id]` - Marcar concluída
- ⏳ `/agenda` - Ver eventos do dia
- ⏳ `/agendar [data] [título]` - Criar evento
- ⏳ `/checkin [energia] [humor] [sono]` - Check-in rápido
- ⏳ `/projeto [nome]` - Status de projeto
- ⏳ `/ideia [texto]` - Capturar ideia de conteúdo
- ⏳ `/resumo` - Resumo do dia/semana

### 4.3 Evolution WhatsApp (Futuro)

**Status:** ⏳ Planejado para após MVP

- Webhook de mensagens recebidas
- Envio de mensagens
- Roteamento: "Assistant" vs "Atendimento"
- Notificações ricas (botões, listas)

---

## 5. MVP - 4 Semanas

### Sprint 1 - Fundação (Semana 1)

**Objetivo:** Infraestrutura básica funcionando

**Status:** ✅ 100% COMPLETO

| Task | Status | Responsável | Notas |
|------|--------|-------------|-------|
| Supabase Auth + DB | ✅ Done | - | Schema 893 linhas, 18 tabelas |
| React app estrutura | ✅ Done | - | Vite + Tailwind |
| Inbox básica (UI) | ✅ Done | - | Estrutura criada |
| Telegram Bot setup | ✅ Done | - | Bot funcionando, PID 2726996 |
| Webhook receber mensagens | ✅ Done | - | Polling ativo |
| Salvar inbox_items | ✅ Done | - | 3 items testados |

**Entregas:**
- ✅ Usuário Igor criado
- ✅ Chat Telegram registrado
- ✅ Inbox salvando mensagens
- ✅ Classificação básica (keywords)

---

### Sprint 2 - Orquestração Gemini (Semana 2)

**Objetivo:** Inteligência na classificação e extração

**Status:** 🔄 20% COMPLETO

| Task | Status | Responsável | Prioridade |
|------|--------|-------------|------------|
| Integrar Gemini API | 🔄 In Progress | - | P0 |
| Classificação inteligente (categorias) | ⏳ To-Do | - | P0 |
| Extração de entidades (pessoas, datas) | ⏳ To-Do | - | P0 |
| Criar tarefas da inbox | ⏳ To-Do | - | P0 |
| Criar notas da inbox | ⏳ To-Do | - | P0 |
| Logs completos (assistant_logs) | 🔄 In Progress | - | P0 |
| Comando `/task criar` | ⏳ To-Do | - | P0 |
| Comando `/tasks` listar | ⏳ To-Do | - | P0 |

**Entregas esperadas:**
- [ ] Gemini classificando inbox com 90%+ acurácia
- [ ] Extração: "reunião com João na terça 15h" → task + evento
- [ ] Comando `/tasks` funcional
- [ ] Todas as ações logadas em assistant_logs

**Bloqueios:** Nenhum

---

### Sprint 3 - Google Package (Semana 3)

**Objetivo:** Integrações essenciais (Calendar)

**Status:** ⏳ 0% COMPLETO

| Task | Status | Responsável | Prioridade |
|------|--------|-------------|------------|
| OAuth Google Calendar | ⏳ To-Do | - | P0 |
| Calendar: listar eventos (7 dias) | ⏳ To-Do | - | P0 |
| Calendar: criar evento | ⏳ To-Do | - | P0 |
| Comando `/agenda` | ⏳ To-Do | - | P0 |
| Comando `/agendar` | ⏳ To-Do | - | P0 |
| Rotina manhã (resumo + agenda) | ⏳ To-Do | - | P0 |
| Rotina noite (fechamento) | ⏳ To-Do | - | P0 |
| Scheduler (APScheduler) | ⏳ To-Do | - | P0 |
| Drive: criar pasta projeto | ⏳ To-Do | - | P2 |
| Sheets: export básico | ⏳ To-Do | - | P2 |

**Entregas esperadas:**
- [ ] OAuth completo e tokens salvos
- [ ] Ver agenda do dia via Telegram
- [ ] Criar eventos via comando
- [ ] Resumo manhã (7h) e noite (21h) automáticos

**Dependências:** Sprint 2 completa

---

### Sprint 4 - Aprendizado v1 (Semana 4)

**Objetivo:** Primeiro ciclo de ML e recomendações

**Status:** ⏳ 0% COMPLETO

| Task | Status | Responsável | Prioridade |
|------|--------|-------------|------------|
| Check-ins (energia/sono/humor) | ⏳ To-Do | - | P0 |
| Comando `/checkin` | ⏳ To-Do | - | P0 |
| Heurísticas produtividade | ⏳ To-Do | - | P1 |
| Análise semanal (tarefas/horários) | ⏳ To-Do | - | P1 |
| Tabela recommendations | ⏳ To-Do | - | P1 |
| Gerar 3 recomendações simples | ⏳ To-Do | - | P1 |
| Dashboard Insights (frontend) | ⏳ To-Do | - | P1 |
| Relatório semanal automático | ⏳ To-Do | - | P2 |

**Entregas esperadas:**
- [ ] Check-in diário funcional
- [ ] 3 recomendações úteis geradas
- [ ] Dashboard Insights com gráficos básicos
- [ ] Relatório domingo (planejamento semana)

**Dependências:** Dados de 1 semana (Sprint 3)

---

## 6. Status Atual do Projeto

### 6.1 O que está FUNCIONANDO ✅

1. **Infraestrutura**
   - Supabase: Auth, DB, Schema completo (18 tabelas)
   - Backend Python: FastAPI rodando (port 8000)
   - Frontend React: Estrutura criada (444 packages)
   - Bot Telegram: Rodando (PID 2726996)

2. **Funcionalidades**
   - Registro de usuário via `/start`
   - Recepção de mensagens no Telegram
   - Salvamento na inbox_items
   - Classificação básica (keywords: work/health/content)
   - Comandos: `/start`, `/help`, `/inbox`

3. **Database**
   - 1 usuário: Igor Bessa
   - 1 chat: 8225491023
   - 3 inbox items testados

### 6.2 O que está EM PROGRESSO 🔄

1. **Gemini Integration**
   - API key configurada
   - google-generativeai instalado (0.1.0rc1)
   - Falta: implementar classificação inteligente

2. **Logs System**
   - Tabela assistant_logs criada
   - Falta: popular em todas as ações

3. **Frontend**
   - Estrutura criada
   - Falta: implementar páginas (Dashboard, Inbox, Tasks)

### 6.3 O que está PENDENTE ⏳

**Alta Prioridade (Sprint 2):**
- Integração Gemini completa
- Extração de entidades
- Criar tarefas via comando
- Listar tarefas via `/tasks`

**Média Prioridade (Sprint 3):**
- OAuth Google Calendar
- Rotinas automáticas (manhã/noite)
- Scheduler

**Baixa Prioridade (Sprint 4+):**
- Check-ins e métricas
- ML e recomendações
- Dashboard frontend completo

---

## 7. Decisões Pendentes

### 7.1 Definições Necessárias (Igor)

1. **WhatsApp/Telegram:**
   - ❓ Usar seu número principal ou número dedicado?
   - **Padrão assumido:** Telegram dedicado (@Nariscabot)

2. **Nível de Autonomia:**
   - ❓ Apenas sugerir ou executar com confirmação?
   - **Padrão assumido:** Executar com confirmação

3. **Rotinas Obrigatórias:**
   - ❓ Quais 3 rotinas são essenciais no dia a dia?
   - **Padrão assumido:** 
     - Resumo manhã (7h)
     - Fechamento noite (21h)
     - Planejamento domingo (19h)

### 7.2 Decisões Técnicas Pendentes

1. **Scheduler:**
   - Opção A: APScheduler (Python standalone)
   - Opção B: Supabase Edge Functions + Cron
   - **Recomendação:** APScheduler (mais controle)

2. **Frontend Deployment:**
   - Opção A: Netlify
   - Opção B: Vercel
   - Opção C: Supabase Hosting
   - **Recomendação:** Netlify (já configurado)

3. **WhatsApp Evolution:**
   - Quando migrar do Telegram?
   - **Recomendação:** Após MVP (Semana 5+)

---

## 8. Métricas de Sucesso (MVP)

### 8.1 Critérios de Aceitação

**Sprint 2:**
- [ ] 100% das mensagens classificadas corretamente
- [ ] 90%+ extração de entidades acurada
- [ ] 10+ tarefas criadas via comando

**Sprint 3:**
- [ ] OAuth Google funcionando
- [ ] Agenda sincronizada (0 delay)
- [ ] 3+ eventos criados via Telegram
- [ ] Rotinas executando no horário

**Sprint 4:**
- [ ] 7+ check-ins registrados
- [ ] 3 recomendações úteis geradas
- [ ] Dashboard com dados reais

### 8.2 KPIs do Sistema

| Métrica | Meta MVP | Como medir |
|---------|----------|------------|
| **Mensagens processadas** | 100+ | COUNT(inbox_items) |
| **Taxa de classificação correta** | 90% | Feedback manual |
| **Tarefas criadas** | 50+ | COUNT(tasks) |
| **Eventos sincronizados** | 20+ | COUNT(calendar_events_cache) |
| **Check-ins realizados** | 30+ | COUNT(checkins) |
| **Recomendações aceitas** | 50%+ | COUNT(recommendations WHERE status='applied') |
| **Uptime bot** | 99%+ | Monitoramento |

---

## 9. Riscos e Mitigações

### 9.1 Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Gemini API instável | Média | Alto | Fallback para keywords + retry logic |
| Google OAuth complexo | Alta | Médio | Documentação oficial + libs testadas |
| Telegram rate limits | Baixa | Médio | Queue de mensagens + throttling |
| Supabase RLS conflicts | Média | Alto | Service key para bot, user key para web |
| Scheduler falhar | Baixa | Alto | Logs + alertas + cron backup |

### 9.2 Riscos de Produto

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Sobrecarga de features | Alta | Médio | Foco em MVP, backlog priorizado |
| UX confusa | Média | Alto | Testes com Igor, iteração rápida |
| Dados insuficientes para ML | Alta | Baixo | Começar com heurísticas simples |
| Falta de adoção | Baixa | Alto | Sistema single-user, Igor é early adopter |

---

## 10. Próximos Passos Imediatos

### 10.1 Hoje (04/01/2026)

1. ✅ **Documento de escopo criado** (este arquivo)
2. ⏳ **Implementar classificação Gemini** (2-3h)
3. ⏳ **Comando `/tasks`** (1h)
4. ⏳ **Criar tarefas da inbox** (2h)

### 10.2 Esta Semana (Sprint 2)

1. Extração de entidades (pessoas, datas, valores)
2. Logs em assistant_logs
3. Comando `/task criar`
4. Testes end-to-end

### 10.3 Próxima Semana (Sprint 3)

1. OAuth Google Calendar
2. Sincronização eventos
3. Rotinas automáticas
4. Scheduler implementado

---

## 11. Contatos e Recursos

**Desenvolvedor:** GitHub Copilot (Claude Sonnet 4.5)  
**Product Owner:** Igor Bessa  
**Telegram Bot:** @Nariscabot  
**Supabase:** https://lbxsqyzjtjqtfclagddd.supabase.co  

**Repositório:** `/var/www/producao/assistente_igor/`  
**Documentação:** `/docs/`  
**Backups:** Antes de cada sprint  

---

## 12. Versão 2.0 (Futuro - Não Agora)

**Quando?** Após 3 meses de uso do MVP

**Features V2:**
- Multi-tenant (organizations)
- Perfis e permissões (admin/suporte/aluno)
- Marketplace de templates
- Billing (Stripe)
- Onboarding self-serve
- WhatsApp Evolution integrado
- Mobile app (React Native)

**Princípio:** Igor-first agora, produto depois.

---

**Última atualização:** 04/01/2026 08:10 BRT  
**Próxima revisão:** Fim da Sprint 2 (11/01/2026)
