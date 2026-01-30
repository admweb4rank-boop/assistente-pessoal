# 🤖 Assistente Pessoal - TB Personal OS

Sistema completo de assistente pessoal com integração Telegram, gamificação e métricas de performance.

## ✨ Funcionalidades

### 🎮 Sistema de Gamificação
- **6 tipos de check-in**: Energia, Humor, Sono, Foco, Treino, Nutrição
- **Sistema de XP**: +10 XP por check-in completado
- **Níveis e conquistas**
- **Painel de métricas** com 6 indicadores de performance

### 📊 Métricas de Performance
- ⚡ **Energia**: Baseado em check-ins diários
- 🎯 **Foco**: Nível de concentração (1-10)
- 🛠️ **Execução**: Tarefas completadas
- 💰 **Renda**: Transações financeiras
- 😴 **Sono**: Horas e qualidade do sono
- 😊 **Humor**: Média semanal com emojis

### 🎯 Fluxos Interativos
- **Check-in de Foco**: Valor 1-10
- **Check-in de Treino**: Tipo → Duração → Intensidade
- **Check-in de Nutrição**: Refeição → Qualidade → Hidratação
- **State machine** para gerenciar conversas
- **Validações** em tempo real

### 🧠 Quiz de Onboarding
- 8 perguntas personalizadas
- Definição de metas 2026
- Áreas de foco (work, health, finance, etc.)
- Habilidades prioritárias
- Identificação de bloqueios

### 📱 Integração com Telegram
- Bot interativo com botões inline
- Comandos: `/checkin`, `/status`, `/quiz`, `/tasks`
- Notificações e lembretes

### 🔗 Integrações
- Google Calendar
- Gmail
- Google Drive
- Gemini AI (2 chaves com fallback automático)

## 🚀 Quick Start

### 1. Clonar Repositório
```bash
git clone https://github.com/admweb4rank-boop/assistente-pessoal.git
cd assistente-pessoal
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp backend/.env.example backend/.env
```

**Variáveis obrigatórias:**
```bash
# Supabase (seu banco de dados)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-service-key

# Telegram
TELEGRAM_BOT_TOKEN=seu-token-do-botfather
OWNER_TELEGRAM_CHAT_ID=seu-chat-id

# Gemini AI
GEMINI_API_KEY=sua-chave-gemini
GEMINI_API_KEY_2=segunda-chave-gemini  # Opcional, para fallback

# Google OAuth (opcional)
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-client-secret
```

**Como obter as credenciais:**

**Supabase:**
1. Acesse https://supabase.com
2. Crie um projeto
3. Vá em Settings → API
4. Copie a URL e a Service Role Key

**Telegram:**
1. Fale com @BotFather no Telegram
2. `/newbot` → Escolha nome e username
3. Copie o token fornecido
4. Para chat_id: Use @userinfobot no Telegram

**Gemini AI:**
1. Acesse https://aistudio.google.com/app/apikey
2. Crie uma API key
3. (Opcional) Crie uma segunda para fallback

**Google OAuth (opcional):**
1. Console do Google Cloud
2. APIs & Services → Credentials
3. Create Credentials → OAuth client ID

### 3. Iniciar com Docker

```bash
docker-compose up -d
```

Ou sem Docker:

```bash
cd backend
pip install -r requirements.txt
python run_bot.py
```

### 4. Aplicar Migrações do Banco

Execute o SQL no Supabase Dashboard:

```bash
./scripts/apply_checkin_types_migration.sh
```

Copie o SQL exibido e execute em: Supabase Dashboard → SQL Editor

### 5. Testar no Telegram

```
/start
/quiz  → Responda as 8 perguntas
/status → Veja seu painel de métricas
/checkin → Faça um check-in
```

## 📚 Documentação Completa

- [IMPLEMENTACAO_COMPLETA.md](IMPLEMENTACAO_COMPLETA.md) - Detalhes técnicos das implementações
- [GUIA_TESTE_CHECKINS.md](GUIA_TESTE_CHECKINS.md) - Roteiro completo de testes
- [GUIA_TECNICO_COMPLETO.md](GUIA_TECNICO_COMPLETO.md) - Documentação técnica
- [GUIA_USUARIO.md](GUIA_USUARIO.md) - Guia para usuários finais

## 🏗️ Arquitetura

```
assistente-pessoal/
├── backend/
│   ├── app/
│   │   ├── services/           # Lógica de negócio
│   │   │   ├── checkin_service.py      # 6 tipos de check-in
│   │   │   ├── gamification_service.py # XP e métricas
│   │   │   ├── bot_handler_unified.py  # Bot Telegram
│   │   │   └── onboarding_service_v2.py # Quiz
│   │   ├── api/                # Endpoints REST
│   │   └── jobs/               # Tarefas agendadas
│   ├── supabase/
│   │   └── migrations/         # Migrations do banco
│   └── requirements.txt
├── frontend/                   # React + TypeScript (WIP)
├── docker-compose.yml
└── README.md
```

## 🔧 Stack Tecnológica

- **Backend**: Python 3.11, FastAPI
- **Bot**: python-telegram-bot v13
- **AI**: Gemini 2.0 Flash (REST API)
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis
- **Frontend**: React + TypeScript + Vite (WIP)

## 📊 Status do Projeto

**Versão**: 1.0.0  
**Status**: ✅ Produção  
**Última atualização**: 2026-01-27

### Funcionalidades Implementadas

| Funcionalidade | Status | Notas |
|----------------|--------|-------|
| Check-in de Energia | ✅ | 1-10 + gamificação |
| Check-in de Humor | ✅ | Emojis + score |
| Check-in de Sono | ✅ | Horas + qualidade |
| Check-in de Foco | ✅ | 1-10 + gamificação |
| Check-in de Treino | ✅ | Tipo + duração + intensidade |
| Check-in de Nutrição | ✅ | Refeição + qualidade + hidratação |
| Sistema de XP | ✅ | +10 por check-in |
| Painel de Métricas | ✅ | 6 métricas calculadas |
| Quiz de Onboarding | ✅ | 8 perguntas |
| Integração Google | ⏳ | Calendar, Gmail, Drive |
| Frontend Web | ⏳ | Em desenvolvimento |

## 🤝 Contribuindo

Este é um projeto privado. Contribuições são bem-vindas via pull requests.

## 📝 Licença

Privado - Todos os direitos reservados.

## 🆘 Suporte

Para dúvidas ou problemas:
- Veja a [documentação completa](GUIA_TECNICO_COMPLETO.md)
- Verifique os [logs do bot](backend/bot.log)
- Entre em contato com o administrador

---

**Desenvolvido com** ❤️ **por Igor Bessa**  
**Powered by** Gemini 2.0 Flash, Supabase & Telegram (Igor) 🧠

**Assistente Pessoal Operacional e Evolutivo**

> Um sistema completo para centralizar, organizar e otimizar a vida pessoal e profissional através de IA, automação e aprendizado contínuo.

## 🎯 Visão Geral

O TB Personal OS não é apenas um chatbot - é um **sistema operacional para a vida**:

- 📥 **Captura**: Entradas via Telegram, web, links, arquivos
- 🧠 **Processa**: IA (Gemini) classifica, extrai e sugere ações
- ⚡ **Executa**: Integra com Google Calendar, Gmail, Drive, Tasks
- 📊 **Aprende**: ML detecta padrões e recomenda melhorias
- 🔄 **Evolui**: Melhoria contínua baseada em dados reais

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACES                           │
│  Telegram Bot │ React Web App │ (Future: Voice/Mobile) │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────┐
│                 ORCHESTRATION LAYER                       │
│              Python Assistant API (FastAPI)               │
│  • Input Normalization  • Gemini Integration             │
│  • Tool Execution       • Memory Management              │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│   SUPABASE     │ │ INTEGRATIONS│ │  ML SERVICE    │
│ • Auth         │ │ • Google    │ │ • Patterns     │
│ • PostgreSQL   │ │ • Telegram  │ │ • Learning     │
│ • Storage      │ │ • Gemini AI │ │ • Recommend.   │
│ • Realtime     │ │             │ │                │
└────────────────┘ └─────────────┘ └────────────────┘
```

## 🚀 Stack Tecnológico

### Backend
- **Python 3.11+** (FastAPI)
- **Supabase** (Auth, PostgreSQL, Storage, Edge Functions)
- **Gemini API** (LLM principal)
- **Telegram Bot API** (canal de entrada principal)

### Frontend
- **React 18+** (Vite)
- **TypeScript**
- **TailwindCSS**
- **Shadcn/ui**
- **Supabase Client**

### ML/Analytics
- **scikit-learn**
- **pandas**
- **numpy**
- **APScheduler** (jobs recorrentes)

### Integrações
- **Google Calendar API**
- **Gmail API**
- **Google Drive API**
- **Google Sheets API**
- **Telegram Bot API**

## 📦 Módulos Principais

### 1. **Inbox Unificada**
Centraliza todas as entradas (Telegram, web, uploads, links) e classifica automaticamente:
- Pessoal / Trabalho / Saúde / Conteúdo / Financeiro
- Extrai entidades: pessoas, datas, tarefas, projetos
- Sugere ações automáticas

### 2. **Memória & Conhecimento**
Sistema de memória em camadas:
- **Curta**: Contexto das últimas interações
- **Longa**: Preferências, objetivos, princípios
- **Base de Conhecimento**: Documentos, links, arquivos
- **Timeline**: Histórico completo de eventos

### 3. **Planner & Rotinas**
- Tarefas (rápidas e estruturadas)
- Rotinas diárias/semanais (manhã, noite, planejamento)
- Objetivos (metas trimestrais/mensais)
- Check-ins (humor, energia, foco)

### 4. **Projetos & Operação (Modo CEO)**
- Gestão de projetos e clientes
- Status, próximas ações, prioridades
- Follow-ups automáticos
- Registro de decisões e reuniões

### 5. **Content OS**
- Captura de ideias (texto/áudio/links)
- Curadoria semanal
- Geração de variações por canal (IG/LinkedIn)
- Calendário editorial
- Tracking de performance

### 6. **Health OS**
- Sono, treino, nutrição
- Check-ins de energia/libido/humor
- Recomendações comportamentais (coaching)

### 7. **Finance OS**
- Entradas/saídas
- Recorrências
- Metas de caixa
- Alertas de risco

### 8. **ML & Insights**
- Detecção de padrões de produtividade
- Correlação hábitos × energia
- Análise de conteúdo × performance
- Recomendações acionáveis

## 🔐 Segurança

- ✅ Supabase Auth com MFA opcional
- ✅ Row Level Security (RLS) no PostgreSQL
- ✅ API Keys em environment/secrets
- ✅ Logs completos de todas as ações
- ✅ Níveis de autonomia configuráveis:
  - **Sugerir** (padrão)
  - **Executar com confirmação**
  - **Executar automático** (rotinas seguras)

## 📋 Instalação

### Pré-requisitos
```bash
Node.js 18+
Python 3.11+
PostgreSQL 15+ (via Supabase)
Contas: Supabase, Google Cloud, Gemini API, Telegram
```

### 1. Clone e Configure
```bash
cd /var/www/producao/assistente_igor

# Backend
cd backend
cp .env.example .env
# Configure as variáveis de ambiente
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
cp .env.example .env.local
npm install
```

### 2. Database Setup
```bash
# Execute as migrations no Supabase
cd ../database
# Importe schema.sql no SQL Editor do Supabase
```

### 3. Configurar Integrações

#### Google APIs
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto
3. Ative: Calendar API, Gmail API, Drive API, Sheets API
4. Crie credenciais OAuth 2.0
5. Configure as variáveis no `.env`

#### Telegram Bot
1. Fale com [@BotFather](https://t.me/botfather)
2. Crie um novo bot
3. Copie o token
4. Configure `TELEGRAM_BOT_TOKEN` no `.env`

#### Gemini API
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Gere uma API key
3. Configure `GEMINI_API_KEY` no `.env`

### 4. Executar

```bash
# Backend (desenvolvimento)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (desenvolvimento)
cd frontend
npm run dev

# ML Service (jobs)
cd ml_service
python jobs/scheduler.py
```

## 🎯 Roadmap MVP (4 Semanas)

### ✅ Semana 1 - Fundação
- [ ] Supabase Auth + DB + RLS
- [ ] React app (layout + login + dashboard)
- [ ] Inbox básica (criar/visualizar)
- [ ] Webhook Telegram recebendo mensagens

### ✅ Semana 2 - Orquestração Gemini
- [ ] Python Assistant API (FastAPI)
- [ ] Classificação + extração (tarefas, datas, tags)
- [ ] Criar tarefas e notas a partir do Telegram
- [ ] Logs completos de cada ação

### ✅ Semana 3 - Google Package
- [ ] Calendar read + create
- [ ] "planejar semana" + "resumo do dia"
- [ ] Drive/Sheets básico para export

### ✅ Semana 4 - Aprendizado v1
- [ ] Check-ins (energia/sono/foco) no Telegram
- [ ] Heurísticas + relatórios semanais
- [ ] Recomendações simples e úteis
- [ ] Dashboard Insights

Detalhamento completo em: [ROADMAP.md](./docs/ROADMAP.md)

## 📖 Documentação

- [Arquitetura Detalhada](./docs/ARQUITETURA.md)
- [Roadmap Completo](./docs/ROADMAP.md)
- [Estrutura do Banco](./docs/DATABASE.md)
- [APIs e Integrações](./docs/INTEGRACOES.md)
- [Machine Learning](./docs/ML_STRATEGY.md)
- [Segurança](./docs/SECURITY.md)
- [Guia de Desenvolvimento](./docs/DEV_GUIDE.md)

## 🤝 Contribuição

Este é um projeto pessoal (single-tenant) em desenvolvimento.
Versão multi-tenant planejada para Q3 2026.

## 📄 Licença

Proprietary - Todos os direitos reservados

## 👤 Autor

**Igor** - Fundador Tech à Bessa

---

**Status**: 🚧 Em Desenvolvimento Ativo (Janeiro 2026)
**Versão**: 0.1.0-alpha
**Última atualização**: 03/01/2026
