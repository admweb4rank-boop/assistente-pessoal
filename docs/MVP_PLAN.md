# Plano de Implementação MVP - TB Personal OS

> Roadmap detalhado de 4 semanas para o MVP funcional

**Período:** 06 Janeiro - 02 Fevereiro 2026  
**Objetivo:** Sistema funcional end-to-end com IA, integrações e aprendizado básico

---

## 📋 Visão Geral do MVP

### O que será entregue

✅ Telegram bot funcional recebendo e respondendo mensagens  
✅ Backend API com Gemini integrado  
✅ Frontend React com dashboard interativo  
✅ Google Calendar, Gmail e Drive integrados  
✅ Sistema de tarefas e notas completo  
✅ Check-ins de saúde (energia, sono, humor)  
✅ ML básico com recomendações úteis  
✅ Rotinas automáticas (manhã, noite, semanal)  
✅ Logs completos de todas as ações  

### O que NÃO será entregue no MVP

❌ Projects OS completo  
❌ Content OS completo  
❌ Finance OS completo  
❌ Voice input (Whisper)  
❌ ML avançado (deep learning)  
❌ Mobile app  
❌ Múltiplos usuários (multi-tenant)  

---

## 🗓️ SEMANA 1: Fundação (06-12 Janeiro)

**Objetivo:** Infraestrutura básica funcionando + Telegram recebendo mensagens

### Segunda-feira (06/01) - Setup Inicial

**Backend:**
- [ ] Criar projeto Supabase
- [ ] Executar migration inicial (`00001_initial_schema.sql`)
- [ ] Configurar RLS policies
- [ ] Criar usuário de teste via Supabase Auth
- [ ] Testar conexão com database

**Scripts:**
```bash
# Supabase setup
cd /var/www/producao/assistente_igor
npm install -g supabase
supabase login
supabase init
supabase db reset  # Executa migrations

# Criar .env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cp ml-service/.env.example ml-service/.env

# Editar com suas keys
nano backend/.env
```

**Entregável:** Database criado e acessível

---

### Terça-feira (07/01) - Backend Core

**Backend:**
- [ ] Setup FastAPI básico
- [ ] Estrutura de pastas (`app/`, `models/`, `schemas/`, `services/`)
- [ ] `main.py` com health check
- [ ] Conexão com Supabase/PostgreSQL
- [ ] CORS configurado
- [ ] Logging estruturado

**Código:**
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/")
async def root():
    return {"message": "TB Personal OS API"}
```

**Testar:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Em outro terminal
curl http://localhost:8000/health
```

**Entregável:** API rodando e respondendo

---

### Quarta-feira (08/01) - Auth + CRUD Básico

**Backend:**
- [ ] Middleware de autenticação (Supabase JWT)
- [ ] Dependência `get_current_user()`
- [ ] Endpoints de tasks:
  - `POST /api/v1/tasks` - criar
  - `GET /api/v1/tasks` - listar
  - `PATCH /api/v1/tasks/{id}` - atualizar
  - `DELETE /api/v1/tasks/{id}` - deletar
- [ ] Endpoints de notes (mesma estrutura)

**Código:**
```python
# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from app.core.config import settings

async def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(
            token, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

**Testar com Postman/Insomnia:**
```
POST http://localhost:8000/api/v1/tasks
Authorization: Bearer YOUR_TOKEN
Body: {
  "title": "Primeira tarefa",
  "priority": "high"
}
```

**Entregável:** CRUD de tasks e notes funcionando

---

### Quinta-feira (09/01) - Frontend Básico

**Frontend:**
- [ ] Setup Vite + React + TypeScript
- [ ] TailwindCSS configurado
- [ ] React Router configurado
- [ ] Supabase client configurado
- [ ] Página de Login
- [ ] Layout base (sidebar + header)
- [ ] Dashboard vazio
- [ ] Página de Tasks básica

**Estrutura:**
```
frontend/src/
├── components/
│   ├── Layout.tsx
│   ├── Sidebar.tsx
│   └── Header.tsx
├── pages/
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   └── Tasks.tsx
├── services/
│   ├── api.ts
│   └── supabase.ts
├── hooks/
│   └── useAuth.ts
└── App.tsx
```

**Testar:**
```bash
cd frontend
npm install
npm run dev
# Abrir http://localhost:3000
```

**Entregável:** Frontend rodando com login funcionando

---

### Sexta-feira (10/01) - Telegram Bot

**Backend:**
- [ ] Criar bot no @BotFather
- [ ] Configurar webhook
- [ ] Endpoint `POST /webhooks/telegram`
- [ ] Validação do webhook (secret token)
- [ ] Processar mensagens básicas
- [ ] Responder mensagens
- [ ] Salvar na inbox_items

**Código:**
```python
# app/api/v1/endpoints/telegram.py
from fastapi import APIRouter, Request, HTTPException, Header
from app.services.telegram import TelegramService
from app.core.config import settings

router = APIRouter()
telegram_service = TelegramService()

@router.post("/webhooks/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    # Validar secret
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(403, "Invalid secret")
    
    # Processar update
    update = await request.json()
    await telegram_service.process_update(update)
    
    return {"ok": True}
```

**Configurar webhook:**
```python
# scripts/setup_telegram_webhook.py
import requests
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "secret_token": SECRET,
        "allowed_updates": ["message", "callback_query"]
    }
)
print(response.json())
```

**Testar:**
- Enviar mensagem no Telegram
- Verificar se chega no endpoint
- Verificar se salva na inbox_items

**Entregável:** Telegram → Backend → Database

---

### Sábado-Domingo (11-12/01) - Integração e Testes

**Tasks:**
- [ ] Conectar frontend com backend (tasks CRUD)
- [ ] Exibir tasks na UI
- [ ] Criar task via UI
- [ ] Marcar como concluída
- [ ] Ver inbox no frontend
- [ ] Docker Compose funcional
- [ ] README com instruções de setup

**Entregável Semana 1:**
✅ Sistema básico funcionando  
✅ Telegram recebendo mensagens  
✅ Tasks CRUD completo  
✅ Frontend exibindo dados  

---

## 🗓️ SEMANA 2: Orquestração + Gemini (13-19 Janeiro)

**Objetivo:** LLM processando mensagens e executando ações

### Segunda-feira (13/01) - Gemini Integration

**Backend:**
- [ ] Setup Gemini API client
- [ ] Service `GeminiService`
- [ ] Teste de chamada básica
- [ ] Configurar rate limiting
- [ ] Logging de tokens usados

**Código:**
```python
# app/services/gemini.py
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def generate(self, prompt: str, system_instruction: str = None):
        # Implementar chamada
        response = self.model.generate_content(prompt)
        return response.text
```

**Testar:**
```python
# test_gemini.py
gemini = GeminiService()
response = await gemini.generate("Oi, me ajude a criar uma tarefa")
print(response)
```

**Entregável:** Gemini respondendo corretamente

---

### Terça-feira (14/01) - Intent Classification

**Backend:**
- [ ] `IntentClassifier` usando Gemini
- [ ] Classificar intenção da mensagem
- [ ] Extrair entidades (datas, prioridades, etc)
- [ ] Retornar structured output (JSON)

**Prompt:**
```python
INTENT_CLASSIFICATION_PROMPT = """
Você é um assistente que classifica intenções de mensagens.

Classifique a mensagem em uma das seguintes intenções:
- create_task: criar uma tarefa
- create_note: salvar uma nota/anotação
- query_info: buscar informação
- schedule_event: agendar algo no calendário
- other: outros casos

Além disso, extraia entidades relevantes:
- title: título da tarefa/nota/evento
- description: descrição detalhada
- due_date: data de vencimento (formato ISO 8601)
- priority: low, medium, high, urgent

Mensagem: "{message}"

Retorne APENAS um JSON válido no formato:
{{
  "intent": "create_task",
  "entities": {{
    "title": "...",
    "description": "...",
    "due_date": "2026-01-15",
    "priority": "high"
  }}
}}
"""
```

**Testar:**
```
Input: "Preciso terminar o relatório até sexta"
Output: {
  "intent": "create_task",
  "entities": {
    "title": "Terminar relatório",
    "due_date": "2026-01-17",
    "priority": "medium"
  }
}
```

**Entregável:** Classificação funcionando bem

---

### Quarta-feira (15/01) - Tool Orchestrator

**Backend:**
- [ ] Base class `BaseTool`
- [ ] `TaskTool` (create, list, update, delete)
- [ ] `NoteTool` (create, search)
- [ ] `ToolOrchestrator` (roteamento)

**Código:**
```python
# app/services/tools/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def validate(self, params: Dict[str, Any]) -> bool:
        pass

# app/services/tools/task_tool.py
class TaskTool(BaseTool):
    name = "create_task"
    description = "Creates a new task"
    
    async def execute(self, params):
        # Criar task no DB
        task = await db.create_task(params)
        return {"success": True, "task_id": task.id}
```

**Entregável:** Tools executando ações

---

### Quinta-feira (16/01) - Assistant Core

**Backend:**
- [ ] `MessageRouter` (roteador principal)
- [ ] `ContextManager` (contexto das conversas)
- [ ] Fluxo completo: Telegram → Router → Classifier → Tool → Response

**Fluxo:**
```python
# app/services/assistant/router.py
class MessageRouter:
    def __init__(self):
        self.classifier = IntentClassifier()
        self.orchestrator = ToolOrchestrator()
        self.context_manager = ContextManager()
    
    async def route_message(self, message: str, user_id: str):
        # 1. Buscar contexto
        context = await self.context_manager.get_context(user_id)
        
        # 2. Classificar intenção
        intent = await self.classifier.classify(message, context)
        
        # 3. Executar ferramenta
        result = await self.orchestrator.execute(
            intent["intent"], 
            intent["entities"]
        )
        
        # 4. Gerar resposta
        response = self.generate_response(result)
        
        # 5. Logar
        await self.log_action(user_id, message, intent, result)
        
        return response
```

**Entregável:** Fluxo end-to-end funcionando

---

### Sexta-feira (17/01) - Telegram Avançado

**Backend:**
- [ ] Comandos estruturados (`/tarefa`, `/nota`, `/buscar`)
- [ ] Inline keyboards (botões)
- [ ] Mensagens de confirmação
- [ ] Tratamento de erros amigável

**Comandos:**
```python
COMMANDS = {
    "/tarefa": "Criar nova tarefa",
    "/nota": "Salvar nota",
    "/buscar": "Buscar informação",
    "/resumo": "Resumo do dia",
    "/ajuda": "Ver comandos"
}

# Handler
async def handle_command(command: str, args: str, user_id: str):
    if command == "/tarefa":
        return await create_task_flow(args, user_id)
    # ...
```

**Entregável:** Comandos Telegram funcionando

---

### Sábado-Domingo (18-19/01) - Logging & Testes

**Tasks:**
- [ ] `assistant_logs` table sendo populada
- [ ] Ver reasoning do LLM nos logs
- [ ] Dashboard de logs no frontend
- [ ] Testes automatizados (pytest)
- [ ] Cobertura > 70%

**Entregável Semana 2:**
✅ Gemini processando mensagens  
✅ Tarefas sendo criadas via linguagem natural  
✅ Logs completos de todas as ações  
✅ Comandos Telegram funcionando  

---

## 🗓️ SEMANA 3: Google Integrations (20-26 Janeiro)

**Objetivo:** Calendar, Gmail e Drive integrados

### Segunda-feira (20/01) - Google OAuth Setup

**Backend:**
- [ ] Fluxo OAuth2 completo
- [ ] Endpoint `/auth/google`
- [ ] Endpoint `/auth/google/callback`
- [ ] Salvar tokens (criptografados)
- [ ] Refresh automático

**Código:**
```python
# app/services/integrations/google_auth.py
from google_auth_oauthlib.flow import Flow

class GoogleAuthService:
    def get_auth_url(self, user_id: str) -> str:
        flow = Flow.from_client_config(
            client_config,
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Salvar state no DB
        await save_oauth_state(user_id, state)
        
        return auth_url
```

**Testar:**
- Clicar no link de autorização
- Autorizar no Google
- Verificar se tokens foram salvos

**Entregável:** OAuth funcionando

---

### Terça-feira (21/01) - Google Calendar

**Backend:**
- [ ] Service `GoogleCalendarService`
- [ ] List events
- [ ] Create event
- [ ] Update event
- [ ] Delete event
- [ ] `CalendarTool` integrado ao assistant

**Código:**
```python
# app/services/integrations/google_calendar.py
from googleapiclient.discovery import build

class GoogleCalendarService:
    async def list_events(self, user_id: str, start_date, end_date):
        creds = await self.get_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        
        events = service.events().list(
            calendarId='primary',
            timeMin=start_date.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events.get('items', [])
```

**Testar via Telegram:**
```
"Agendar reunião com cliente amanhã às 14h"
→ Cria evento no Google Calendar
→ Responde com link do evento
```

**Entregável:** Calendar integrado

---

### Quarta-feira (22/01) - Google Gmail

**Backend:**
- [ ] Service `GmailService`
- [ ] Search threads
- [ ] Read email
- [ ] Send email (draft mode)
- [ ] `GmailTool` integrado ao assistant

**Código:**
```python
# app/services/integrations/gmail.py
class GmailService:
    async def search_threads(self, user_id: str, query: str):
        creds = await self.get_credentials(user_id)
        service = build('gmail', 'v1', credentials=creds)
        
        results = service.users().threads().list(
            userId='me',
            q=query
        ).execute()
        
        return results.get('threads', [])
    
    async def send_email(self, user_id: str, to, subject, body):
        # Criar draft ou enviar
        pass
```

**Testar:**
```
"/email buscar emails de fulano sobre projeto X"
→ Lista threads relevantes
```

**Entregável:** Gmail integrado

---

### Quinta-feira (23/01) - Google Drive

**Backend:**
- [ ] Service `GoogleDriveService`
- [ ] Upload file
- [ ] List files
- [ ] Create folder
- [ ] Share file

**Entregável:** Drive básico funcionando

---

### Sexta-feira (24/01) - Frontend Planner

**Frontend:**
- [ ] Página Planner
- [ ] Lista de tarefas
- [ ] Calendar view (integrado com Google)
- [ ] Criar tarefa/evento
- [ ] Drag & drop (opcional)

**Entregável:** Planner funcional

---

### Sábado-Domingo (25-26/01) - Comandos Telegram Avançados

**Backend:**
- [ ] `/agendar` - criar evento
- [ ] `/semana` - resumo semanal
- [ ] `/email` - buscar/enviar
- [ ] `/resumo` - resumo do dia (tarefas + eventos)

**Entregável Semana 3:**
✅ Google Calendar, Gmail e Drive funcionando  
✅ Comandos avançados no Telegram  
✅ Frontend Planner completo  

---

## 🗓️ SEMANA 4: ML & Insights (27 Janeiro - 02 Fevereiro)

**Objetivo:** Sistema aprendendo e recomendando

### Segunda-feira (27/01) - Health Check-ins

**Backend:**
- [ ] Tabelas `habits` e `checkins` populadas
- [ ] Endpoints de check-in
- [ ] Comandos Telegram:
  - `/energia 8` - registrar energia
  - `/sono 7.5` - registrar horas de sono
  - `/humor 😊` - registrar humor

**Entregável:** Check-ins funcionando

---

### Terça-feira (28/01) - ML Service Setup

**ML Service:**
- [ ] Estrutura base
- [ ] Conexão com database (read-only)
- [ ] APScheduler configurado
- [ ] Job de teste (rodar diariamente)

**Código:**
```python
# ml-service/src/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.jobs.daily_analysis import run_daily_analysis

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=6, minute=0)
async def daily_job():
    print("Running daily analysis...")
    await run_daily_analysis()

scheduler.start()
```

**Entregável:** ML service rodando

---

### Quarta-feira (29/01) - Analyzers

**ML Service:**
- [ ] `ProductivityAnalyzer` (heurísticas)
- [ ] `HealthAnalyzer` (correlações)
- [ ] Detectar:
  - Horários mais produtivos
  - Correlação sono x energia
  - Taxa de conclusão

**Código:**
```python
# ml-service/src/analyzers/productivity.py
class ProductivityAnalyzer:
    async def analyze(self, user_id: str, days=30):
        # Buscar tasks completadas
        tasks = await db.get_completed_tasks(user_id, days)
        
        # Agrupar por hora do dia
        by_hour = {}
        for task in tasks:
            hour = task.completed_at.hour
            by_hour[hour] = by_hour.get(hour, 0) + 1
        
        # Encontrar pico
        peak_hour = max(by_hour, key=by_hour.get)
        
        return {
            "peak_productivity_hour": peak_hour,
            "total_completed": len(tasks),
            "completion_rate": calculate_rate(tasks)
        }
```

**Entregável:** Análises gerando insights

---

### Quinta-feira (30/01) - Recommendations Engine

**ML Service:**
- [ ] `RecommendationEngine`
- [ ] Gerar recomendações
- [ ] Salvar na tabela `recommendations`
- [ ] Notificar via Telegram

**Exemplo de recomendação:**
```
🎯 Nova Recomendação

Você é mais produtivo entre 9h-11h
(baseado em 25 tarefas completadas nos últimos 30 dias)

Sugestão: Agende tarefas importantes nesse horário.

Útil? /feedback_sim ou /feedback_nao
```

**Entregável:** Recomendações chegando no Telegram

---

### Sexta-feira (31/01) - Dashboard Insights

**Frontend:**
- [ ] Página Insights
- [ ] Gráfico de energia por dia
- [ ] Gráfico de produtividade
- [ ] Lista de recomendações
- [ ] Histórico de padrões

**Entregável:** Dashboard Insights visual

---

### Sábado (01/02) - Rotinas Automáticas

**Backend:**
- [ ] Rotina matinal (7h):
  - Resumo do dia
  - Eventos do calendário
  - Tarefas prioritárias
- [ ] Rotina noturna (21h):
  - Check-in do dia
  - Tarefas completadas
  - Energia média
- [ ] Rotina semanal (domingo 18h):
  - Resumo da semana
  - Planejamento próxima semana
  - Recomendações

**Implementar com APScheduler:**
```python
@scheduler.scheduled_job('cron', hour=7, minute=0)
async def morning_routine():
    users = await get_active_users()
    for user in users:
        summary = await generate_morning_summary(user.id)
        await telegram.send_message(user.telegram_chat_id, summary)
```

**Entregável:** Rotinas enviando mensagens

---

### Domingo (02/02) - Finalização MVP

**Tasks:**
- [ ] Testes end-to-end
- [ ] Corrigir bugs encontrados
- [ ] Documentação atualizada
- [ ] README com instruções claras
- [ ] Deploy em produção (VPS)
- [ ] Backup configurado
- [ ] Monitoring básico

**Checklist Final:**
- [ ] Telegram funcionando 100%
- [ ] Tarefas e notas via linguagem natural
- [ ] Google integrations OK
- [ ] ML gerando recomendações
- [ ] Frontend responsivo
- [ ] Logs completos
- [ ] Performance aceitável (< 2s resposta)

**Entregável Semana 4:**
✅ MVP COMPLETO E FUNCIONAL  
✅ Sistema aprendendo e recomendando  
✅ Rotinas automáticas rodando  
✅ Deploy em produção  

---

## 📊 Métricas de Sucesso do MVP

### Funcionalidade
- [ ] 100% dos comandos Telegram funcionando
- [ ] Taxa de sucesso > 95% na classificação de intenções
- [ ] Todas as integrações Google funcionando
- [ ] ML gerando pelo menos 3 recomendações por semana

### Performance
- [ ] Tempo de resposta API < 2s (p95)
- [ ] Tempo de resposta Telegram < 3s
- [ ] Chamadas Gemini < 5s
- [ ] Uptime > 99%

### Qualidade
- [ ] Cobertura de testes > 70%
- [ ] Zero critical bugs
- [ ] Logs de todas as ações
- [ ] Documentação completa

---

## 🚀 Pós-MVP (Fevereiro em diante)

Após o MVP, seguir o [ROADMAP.md](ROADMAP.md) para:
- Projects OS
- Content OS
- Finance OS
- ML avançado
- Otimizações
- Novos módulos

---

## 📝 Notas Finais

**Prioridades:**
1. **Funcionalidade** > Performance > Estética
2. **Logs completos** > Monitoramento avançado
3. **Simplicidade** > Complexidade

**Se atrasar:**
- Cortar ML avançado (deixar heurísticas simples)
- Simplificar frontend (focar no Telegram)
- Adiar Gmail/Drive (manter só Calendar)

**Não negociável:**
- Telegram funcionando 100%
- Tarefas via linguagem natural
- Logs completos
- Google Calendar integrado

---

**Boa sorte! 🚀**

**Última atualização:** 03/01/2026  
**Versão:** 1.0
