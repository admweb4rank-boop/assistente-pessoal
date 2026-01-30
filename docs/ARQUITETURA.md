# Arquitetura do TB Personal OS

> Documento técnico detalhado da arquitetura do sistema

**Versão:** 1.0  
**Data:** Janeiro 2026

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Componentes do Sistema](#componentes-do-sistema)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Camada de Dados](#camada-de-dados)
5. [Camada de Aplicação](#camada-de-aplicação)
6. [Camada de Integração](#camada-de-integração)
7. [Camada de ML](#camada-de-ml)
8. [Segurança](#segurança)
9. [Escalabilidade](#escalabilidade)

---

## 1. Visão Geral

### 1.1 Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE INTERFACE                      │
├─────────────────────────────────────────────────────────────┤
│  React Web App        │        Telegram Bot                 │
│  (Dashboard + UI)     │        (Input Principal)            │
└─────────────┬─────────┴──────────────┬────────────────────┘
              │                         │
              │      REST API / WebSocket
              │                         │
┌─────────────▼─────────────────────────▼────────────────────┐
│              CAMADA DE ORQUESTRAÇÃO                         │
├─────────────────────────────────────────────────────────────┤
│           Python FastAPI Assistant Service                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Message Router  │  Intent Classifier  │  Executor   │  │
│  │  Context Manager │  Tool Orchestrator  │  Logger     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────┬─────────────────────┘
              │                       │
              │                       │
┌─────────────▼───────┐      ┌───────▼──────────────────────┐
│   SUPABASE          │      │   GOOGLE GEMINI API          │
│                     │      │   (LLM Principal)            │
│  • Auth             │      │                              │
│  • PostgreSQL       │      │  • Classificação             │
│  • Storage          │      │  • Extração de Entidades     │
│  • Edge Functions   │      │  • Geração de Respostas      │
│  • Realtime         │      │  • Reasoning                 │
└─────────────────────┘      └──────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────────┐
│                CAMADA DE INTEGRAÇÃO                       │
├───────────────────────────────────────────────────────────┤
│  Telegram  │  Google Calendar  │  Gmail  │  Drive  │ etc │
└───────────────────────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────────┐
│              CAMADA DE APRENDIZADO (ML)                   │
├───────────────────────────────────────────────────────────┤
│          Python ML Service (Background Jobs)              │
│  • Pattern Detection    • Recommendations                 │
│  • Correlation Analysis • Predictive Insights             │
└───────────────────────────────────────────────────────────┘
```

### 1.2 Princípios Arquiteturais

1. **Modularidade:** Cada módulo é independente e pode evoluir separadamente
2. **Event-Driven:** Comunicação assíncrona via eventos quando possível
3. **Stateless API:** APIs sem estado, contexto no banco
4. **Idempotência:** Operações podem ser repetidas sem efeitos colaterais
5. **Auditabilidade:** Tudo é registrado (logs completos)
6. **Failure Recovery:** Sistema resiliente a falhas de integrações
7. **Privacy-First:** Dados sensíveis protegidos, RLS ativo

---

## 2. Componentes do Sistema

### 2.1 Frontend (React SPA)

**Responsabilidades:**
- Interface do usuário
- Autenticação (Supabase Auth)
- Visualização de dados
- Interação em tempo real
- Gestão de estado local

**Tecnologias:**
- React 18+ (Hooks, Context, Suspense)
- TypeScript
- TailwindCSS + HeadlessUI
- React Query (data fetching)
- Zustand (state management)
- React Router v6
- Chart.js / Recharts (visualizações)

**Estrutura:**
```
frontend/
├── src/
│   ├── components/       # Componentes reutilizáveis
│   ├── pages/           # Páginas principais
│   ├── hooks/           # Custom hooks
│   ├── services/        # API clients
│   ├── store/           # State management
│   ├── utils/           # Utilitários
│   ├── types/           # TypeScript types
│   └── App.tsx
├── public/
└── package.json
```

### 2.2 Backend (Python FastAPI)

**Responsabilidades:**
- Orquestração de ações
- Processamento de mensagens
- Chamadas ao LLM (Gemini)
- Execução de tools/integrações
- Business logic
- Validação e sanitização
- Logging completo

**Tecnologias:**
- FastAPI (framework assíncrono)
- Pydantic (validação de dados)
- SQLAlchemy (ORM)
- asyncio / asyncpg
- python-jose (JWT)
- httpx (HTTP client assíncrono)

**Estrutura:**
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/    # Rotas da API
│   │   │   └── dependencies/ # Dependências
│   │   └── middleware/
│   ├── core/
│   │   ├── config.py        # Configurações
│   │   ├── security.py      # Auth e segurança
│   │   └── logging.py       # Logging setup
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/
│   │   ├── assistant/       # Core do assistente
│   │   ├── integrations/    # Google, Telegram, etc
│   │   └── tools/           # Ferramentas do assistant
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   └── main.py
├── tests/
├── requirements.txt
└── Dockerfile
```

### 2.3 ML Service (Python)

**Responsabilidades:**
- Análise de padrões
- Detecção de correlações
- Geração de recomendações
- Jobs agendados (cron)
- Feature engineering

**Tecnologias:**
- scikit-learn
- pandas / numpy
- APScheduler (jobs)
- matplotlib / seaborn (viz)

**Estrutura:**
```
ml-service/
├── src/
│   ├── jobs/           # Scheduled jobs
│   ├── models/         # ML models
│   ├── features/       # Feature engineering
│   ├── analyzers/      # Data analyzers
│   └── recommenders/   # Recommendation engines
├── notebooks/          # Jupyter notebooks
├── requirements.txt
└── Dockerfile
```

### 2.4 Supabase

**Uso:**
- **Auth:** Autenticação de usuários
- **Database:** PostgreSQL com RLS
- **Storage:** Arquivos e uploads
- **Edge Functions:** Serverless functions
- **Realtime:** WebSockets para updates em tempo real

**Configuração:**
```
supabase/
├── migrations/         # SQL migrations
├── functions/          # Edge functions
├── config.toml
└── seed.sql           # Dados iniciais
```

---

## 3. Fluxo de Dados

### 3.1 Fluxo de Input (Telegram → Sistema)

```
1. Usuário envia mensagem no Telegram
   ↓
2. Telegram webhook → FastAPI endpoint
   ↓
3. MessageRouter valida e normaliza
   ↓
4. Context Manager busca contexto recente (últimas 10 interações)
   ↓
5. IntentClassifier + Gemini → classifica intenção
   ↓
6. Tool Orchestrator executa ação apropriada:
   - Criar tarefa
   - Agendar evento
   - Salvar nota
   - Buscar informação
   - etc.
   ↓
7. Resultado é salvo no DB
   ↓
8. Logger registra tudo (assistant_logs)
   ↓
9. Resposta é enviada ao Telegram
   ↓
10. ML job é triggerado (se aplicável)
```

### 3.2 Fluxo de Processamento LLM

```
Input (texto) → Normalização → Gemini API
                                    ↓
                    [System Prompt + Context + Tools]
                                    ↓
                        Gemini retorna:
                        - Intent (classificação)
                        - Entities (extração)
                        - Actions (sugestões)
                        - Response (resposta)
                                    ↓
                            Tool Executor
                            (executa ações)
                                    ↓
                            Output + Log
```

### 3.3 Fluxo de Integração (Google Calendar)

```
Comando: "/agendar reunião com cliente X amanhã 14h"
    ↓
Gemini extrai: {
  "action": "create_event",
  "title": "Reunião com cliente X",
  "date": "2026-01-04",
  "time": "14:00",
  "duration": 60  # default
}
    ↓
Google Calendar API Tool:
  - Valida token OAuth
  - Cria evento
  - Retorna event_id e link
    ↓
Salva no cache (calendar_events_cache)
    ↓
Resposta ao usuário: "✅ Agendado! [Link do evento]"
```

---

## 4. Camada de Dados

### 4.1 Modelo de Dados Completo

Ver arquivo: [database-schema.sql](database-schema.sql)

### 4.2 Relacionamentos Principais

```
users
  ↓
profiles (1:1)
inbox_items (1:N)
tasks (1:N)
notes (1:N)
projects (1:N)
  ↓
project_items (1:N)
habits (1:N)
assistant_logs (1:N)
```

### 4.3 Estratégia de Cache

**Supabase Realtime** para updates em tempo real:
- Tarefas criadas/concluídas
- Novos items na inbox
- Eventos do calendário

**Redis** (opcional, futuro):
- Context cache (últimas interações)
- Rate limiting
- Session data

---

## 5. Camada de Aplicação

### 5.1 Assistant Core

**Componentes:**

#### MessageRouter
```python
class MessageRouter:
    """Roteador principal de mensagens"""
    
    async def route_message(self, message: Message) -> Response:
        # 1. Validar
        # 2. Normalizar
        # 3. Enriquecer com contexto
        # 4. Enviar para classifier
        # 5. Executar ação
        # 6. Logar
        # 7. Responder
```

#### IntentClassifier
```python
class IntentClassifier:
    """Classifica intenção usando Gemini"""
    
    async def classify(self, message: str, context: Context) -> Intent:
        prompt = self._build_prompt(message, context)
        response = await gemini.generate(prompt)
        return self._parse_intent(response)
```

#### ContextManager
```python
class ContextManager:
    """Gerencia contexto das conversas"""
    
    async def get_context(self, user_id: str, limit: int = 10) -> Context:
        # Busca últimas interações
        # Busca preferências do perfil
        # Busca objetivos atuais
        # Monta contexto estruturado
```

#### ToolOrchestrator
```python
class ToolOrchestrator:
    """Orquestra execução de ferramentas"""
    
    tools = {
        "create_task": TaskTool(),
        "create_event": CalendarTool(),
        "send_email": GmailTool(),
        "save_note": NoteTool(),
        # ...
    }
    
    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        tool = self.tools[tool_name]
        result = await tool.execute(params)
        await self._log_execution(tool_name, params, result)
        return result
```

### 5.2 Tools (Ferramentas)

Cada tool implementa interface padrão:

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema
    
    @abstractmethod
    async def execute(self, params: dict) -> ToolResult:
        pass
    
    @abstractmethod
    async def validate(self, params: dict) -> bool:
        pass
```

**Tools Implementados:**

1. **TaskTool** - Criar/listar/completar tarefas
2. **CalendarTool** - Criar/listar eventos Google Calendar
3. **GmailTool** - Enviar emails, buscar threads
4. **NoteTool** - Criar/buscar notas
5. **ProjectTool** - Gerenciar projetos
6. **ContactTool** - Gerenciar contatos
7. **ContentTool** - Gerenciar ideias de conteúdo
8. **HealthTool** - Registrar check-ins de saúde
9. **SearchTool** - Buscar informações na base

---

## 6. Camada de Integração

### 6.1 Telegram Bot

**Implementação:**
- Webhook-based (não polling)
- Async handlers
- Command handlers
- Message handlers
- Callback query handlers

**Estrutura:**
```python
class TelegramBot:
    def __init__(self, token: str, webhook_url: str):
        self.token = token
        self.webhook_url = webhook_url
        
    async def send_message(self, chat_id: int, text: str):
        # Envia mensagem
        
    async def send_photo(self, chat_id: int, photo_url: str):
        # Envia imagem
        
    async def edit_message(self, chat_id: int, message_id: int, text: str):
        # Edita mensagem
```

### 6.2 Google APIs

**OAuth2 Flow:**
```python
class GoogleAuth:
    """Gerencia autenticação OAuth2 Google"""
    
    async def get_auth_url(self, user_id: str) -> str:
        # Retorna URL de autorização
        
    async def handle_callback(self, code: str, user_id: str):
        # Troca code por tokens
        # Salva refresh_token no DB
        
    async def get_credentials(self, user_id: str) -> Credentials:
        # Busca tokens
        # Refresh se expirado
```

**Google Calendar:**
```python
class GoogleCalendar:
    async def list_events(self, user_id: str, date_range: DateRange):
        creds = await self.auth.get_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        events = service.events().list(...).execute()
        return events
        
    async def create_event(self, user_id: str, event: Event):
        # Cria evento
```

**Gmail:**
```python
class Gmail:
    async def search_threads(self, user_id: str, query: str):
        # Busca threads
        
    async def send_email(self, user_id: str, email: Email):
        # Envia email
```

---

## 7. Camada de ML

### 7.1 Pattern Detection

**Análises:**

1. **Productivity Patterns**
```python
class ProductivityAnalyzer:
    """Detecta padrões de produtividade"""
    
    async def analyze(self, user_id: str, period: DateRange):
        # Busca tarefas, check-ins, eventos
        # Agrupa por hora do dia, dia da semana
        # Calcula métricas:
        #   - Taxa de conclusão por período
        #   - Tempo médio de execução
        #   - Correlação energia x produtividade
        # Retorna insights
```

2. **Content Performance**
```python
class ContentAnalyzer:
    """Analisa performance de conteúdo"""
    
    async def analyze(self, user_id: str):
        # Busca posts e métricas
        # Identifica padrões:
        #   - Temas que performam melhor
        #   - Horários ideais
        #   - Formatos preferidos
        # Retorna recomendações
```

3. **Health Correlations**
```python
class HealthAnalyzer:
    """Correlaciona hábitos de saúde com performance"""
    
    async def analyze(self, user_id: str):
        # Busca check-ins de sono, energia, humor
        # Correlaciona com produtividade
        # Identifica padrões:
        #   - Impacto do sono na energia
        #   - Impacto do treino no humor
        # Retorna insights
```

### 7.2 Recommendation Engine

```python
class RecommendationEngine:
    """Gera recomendações personalizadas"""
    
    analyzers = [
        ProductivityAnalyzer(),
        ContentAnalyzer(),
        HealthAnalyzer(),
    ]
    
    async def generate_recommendations(self, user_id: str):
        insights = []
        for analyzer in self.analyzers:
            insight = await analyzer.analyze(user_id)
            insights.append(insight)
        
        recommendations = self._synthesize(insights)
        await self._save_recommendations(user_id, recommendations)
        return recommendations
```

### 7.3 Jobs Agendados

```python
# Usando APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Todo dia às 6h: gera recomendações
@scheduler.scheduled_job('cron', hour=6)
async def daily_recommendations():
    users = await get_all_users()
    for user in users:
        await recommendation_engine.generate_recommendations(user.id)

# Toda segunda às 9h: análise semanal
@scheduler.scheduled_job('cron', day_of_week='mon', hour=9)
async def weekly_analysis():
    users = await get_all_users()
    for user in users:
        await weekly_analyzer.analyze(user.id)
```

---

## 8. Segurança

### 8.1 Autenticação e Autorização

**Supabase Auth:**
- JWT tokens
- Refresh tokens
- MFA opcional (TOTP)

**Row Level Security (RLS):**
```sql
-- Exemplo: Usuário só vê seus próprios dados
CREATE POLICY "Users can only see their own data"
ON tasks
FOR ALL
USING (auth.uid() = user_id);
```

### 8.2 Proteção de Dados Sensíveis

**API Keys:**
- Nunca no código
- Sempre em environment variables
- Supabase Vault para secrets críticos

**Dados Pessoais:**
- Criptografia em repouso (PostgreSQL)
- Criptografia em trânsito (HTTPS/TLS)
- Logs não contém dados sensíveis (masked)

### 8.3 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/message")
@limiter.limit("100/hour")  # 100 requisições por hora
async def process_message(request: Request):
    # ...
```

### 8.4 Validação e Sanitização

**Pydantic Schemas:**
```python
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    due_date: Optional[datetime]
    priority: Literal["low", "medium", "high"] = "medium"
    
    @validator('title')
    def sanitize_title(cls, v):
        return bleach.clean(v)  # Remove HTML/XSS
```

---

## 9. Escalabilidade

### 9.1 Estratégias de Escalabilidade

**Horizontal Scaling:**
- API stateless → pode ter múltiplas instâncias
- Load balancer (Nginx) distribui carga
- Database connection pooling

**Vertical Scaling:**
- Aumentar recursos da VPS quando necessário
- Otimizar queries (índices, EXPLAIN ANALYZE)

**Caching:**
- Redis para session data e rate limiting
- Cache de respostas Gemini para queries similares
- Cache de eventos do Google Calendar

**Async Processing:**
- Filas para jobs pesados (Celery + Redis/RabbitMQ)
- Background jobs para ML e análises

### 9.2 Monitoramento

**Logs:**
- Structured logging (JSON)
- Centralização de logs (futuro: ELK stack)

**Métricas:**
- Tempo de resposta da API
- Taxa de erro
- Uso de LLM (tokens consumidos)
- Uptime

**Alertas:**
- Erro rate > threshold
- API response time > threshold
- Disk space < threshold

---

## 10. Deploy e DevOps

### 10.1 Ambiente de Desenvolvimento

```bash
# Docker Compose para dev local
docker-compose up -d
```

### 10.2 Ambiente de Produção

**VPS:** serverweb4rank.vps-kinghost.net

**Serviços:**
- Nginx (reverse proxy + SSL)
- Backend API (systemd service)
- ML Service (systemd service)
- PostgreSQL (Supabase cloud)
- Redis (opcional)

**Deployment:**
```bash
# Deploy script
./scripts/deploy.sh production
```

---

## 11. Observações Finais

Esta arquitetura foi desenhada para:

1. ✅ Começar simples (single-tenant)
2. ✅ Ser extensível (fácil adicionar novos módulos)
3. ✅ Ser confiável (logs + auditoria completa)
4. ✅ Aprender continuamente (ML incremental)
5. ✅ Escalar quando necessário (multi-tenant futuro)

**Próximos passos:** Ver [MVP_PLAN.md](MVP_PLAN.md) para cronograma detalhado de implementação.

---

**Última atualização:** 03/01/2026  
**Versão:** 1.0
