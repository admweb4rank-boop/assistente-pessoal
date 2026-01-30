# Segurança e Privacidade - TB Personal OS

> Diretrizes de segurança, privacidade e boas práticas

**Versão:** 1.0  
**Data:** 03/01/2026

---

## 📋 Índice

1. [Princípios de Segurança](#princípios-de-segurança)
2. [Autenticação e Autorização](#autenticação-e-autorização)
3. [Proteção de Dados](#proteção-de-dados)
4. [Segurança da API](#segurança-da-api)
5. [Integrações Externas](#integrações-externas)
6. [Logs e Auditoria](#logs-e-auditoria)
7. [Conformidade](#conformidade)
8. [Incident Response](#incident-response)

---

## 1. Princípios de Segurança

### 1.1 Privacy by Design

- **Mínima coleta:** Coletar apenas dados estritamente necessários
- **Mínimo acesso:** Princípio do menor privilégio
- **Transparência:** Usuário sabe o que é coletado e por quê
- **Controle:** Usuário pode exportar, corrigir ou deletar seus dados

### 1.2 Security by Default

- **Autenticação obrigatória:** Sem acesso anônimo
- **HTTPS everywhere:** Toda comunicação criptografada
- **Secrets protegidos:** API keys nunca em código
- **RLS ativo:** Row Level Security sempre ativo
- **Validação rigorosa:** Input validation em todas as camadas

### 1.3 Defense in Depth

Múltiplas camadas de proteção:
```
1. Network (HTTPS, Firewall)
2. Application (Auth, RBAC, Validation)
3. Database (RLS, Encryption at rest)
4. Monitoring (Logs, Alerts, Anomaly detection)
```

---

## 2. Autenticação e Autorização

### 2.1 Supabase Auth

**Métodos suportados:**
- Email + Password
- Magic Link (email)
- OAuth (Google - futuro)
- MFA/2FA (opcional mas recomendado)

**Configuração:**
```javascript
// Frontend - Supabase client
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL,
  process.env.REACT_APP_SUPABASE_ANON_KEY
)

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'igor@example.com',
  password: 'secure_password'
})

// MFA (opcional)
const { data: factors } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'Igor Mobile'
})
```

### 2.2 JWT Tokens

**Estrutura:**
```json
{
  "sub": "user_uuid",
  "email": "igor@example.com",
  "role": "authenticated",
  "iat": 1704326400,
  "exp": 1704412800
}
```

**Validação no Backend:**
```python
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2.3 Row Level Security (RLS)

**Regras PostgreSQL:**

```sql
-- Tabela: tasks
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Política: Usuário só vê suas próprias tarefas
CREATE POLICY "Users can view own tasks"
ON tasks FOR SELECT
USING (auth.uid() = user_id);

-- Política: Usuário só pode criar suas próprias tarefas
CREATE POLICY "Users can create own tasks"
ON tasks FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Política: Usuário só pode atualizar suas próprias tarefas
CREATE POLICY "Users can update own tasks"
ON tasks FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Política: Usuário só pode deletar suas próprias tarefas
CREATE POLICY "Users can delete own tasks"
ON tasks FOR DELETE
USING (auth.uid() = user_id);
```

**Aplicar a todas as tabelas:**
```sql
-- Script para aplicar RLS a todas as tabelas
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT LIKE 'pg_%'
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('
            CREATE POLICY "Users can view own data"
            ON %I FOR SELECT
            USING (auth.uid() = user_id)
        ', t);
    END LOOP;
END;
$$;
```

---

## 3. Proteção de Dados

### 3.1 Criptografia

**Em Trânsito:**
- HTTPS/TLS 1.3 obrigatório
- Certificate pinning (mobile app futuro)
- No HTTP traffic

**Em Repouso:**
- PostgreSQL encryption at rest (Supabase)
- Disk encryption (LUKS) na VPS
- Backup encryption

**Dados Sensíveis:**
```python
from cryptography.fernet import Fernet

# Encryption key (armazenada em secrets)
ENCRYPTION_KEY = os.getenv("DATA_ENCRYPTION_KEY")
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_sensitive_data(data: str) -> str:
    """Criptografa dados sensíveis"""
    return cipher.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted: str) -> str:
    """Descriptografa dados sensíveis"""
    return cipher.decrypt(encrypted.encode()).decode()

# Exemplo: tokens OAuth
class OAuthToken(BaseModel):
    access_token: str
    refresh_token: str
    
    def save_to_db(self, user_id: str):
        encrypted_access = encrypt_sensitive_data(self.access_token)
        encrypted_refresh = encrypt_sensitive_data(self.refresh_token)
        
        await db.execute("""
            INSERT INTO oauth_tokens (user_id, access_token, refresh_token)
            VALUES ($1, $2, $3)
        """, user_id, encrypted_access, encrypted_refresh)
```

### 3.2 Secrets Management

**Variáveis de Ambiente:**

```bash
# .env (nunca commitar!)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_KEY=eyJhbGci...  # CUIDADO: super privilegiado
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
GEMINI_API_KEY=AIzaSy...
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
DATA_ENCRYPTION_KEY=...
JWT_SECRET=...
```

**Supabase Vault (futuro):**
```sql
-- Armazenar secrets no Supabase Vault
INSERT INTO vault.secrets (name, secret)
VALUES ('gemini_api_key', 'AIzaSy...');

-- Buscar secrets
SELECT decrypted_secret FROM vault.decrypted_secrets
WHERE name = 'gemini_api_key';
```

### 3.3 Sanitização de Inputs

**Backend (Pydantic):**
```python
from pydantic import BaseModel, Field, validator
import bleach

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    
    @validator('title', 'description')
    def sanitize_html(cls, v):
        if v:
            # Remove tags HTML, previne XSS
            return bleach.clean(v, strip=True)
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
```

**Frontend (DOMPurify):**
```javascript
import DOMPurify from 'dompurify';

function sanitizeInput(input) {
  return DOMPurify.sanitize(input, { 
    ALLOWED_TAGS: [], // Nenhuma tag permitida
    ALLOWED_ATTR: []
  });
}

// Uso
const userInput = "<script>alert('xss')</script>Hello";
const safe = sanitizeInput(userInput); // "Hello"
```

---

## 4. Segurança da API

### 4.1 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Aplicar rate limits
@app.post("/api/v1/message")
@limiter.limit("100/hour")  # 100 requests por hora
async def process_message(request: Request):
    # ...

@app.post("/api/v1/tasks")
@limiter.limit("500/hour")  # Mais generoso para CRUD
async def create_task(request: Request):
    # ...
```

**Rate Limits por Endpoint:**
- `/auth/login`: 10/hour (previne brute force)
- `/auth/register`: 3/hour
- `/api/message`: 100/hour
- `/api/tasks/*`: 500/hour
- `/api/notes/*`: 500/hour

### 4.2 CORS

```python
from fastapi.middleware.cors import CORSMiddleware

# Produção: apenas domínios específicos
ALLOWED_ORIGINS = [
    "https://assistant.igordomain.com",
    "http://localhost:3000",  # Dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 4.3 Request Validation

```python
from fastapi import Request, HTTPException
import hashlib

async def validate_telegram_webhook(request: Request):
    """Valida que webhook veio do Telegram"""
    
    # Telegram envia X-Telegram-Bot-Api-Secret-Token
    secret_token = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    received_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    
    if not received_token or received_token != secret_token:
        raise HTTPException(status_code=403, detail="Invalid webhook token")
    
    return True

@app.post("/webhooks/telegram")
async def telegram_webhook(
    request: Request,
    validated: bool = Depends(validate_telegram_webhook)
):
    # Processar webhook
    pass
```

### 4.4 SQL Injection Prevention

**Sempre usar parametrized queries:**

```python
# ❌ ERRADO (vulnerável a SQL injection)
user_input = "Igor'; DROP TABLE users; --"
query = f"SELECT * FROM users WHERE name = '{user_input}'"
await db.execute(query)

# ✅ CORRETO (parametrizado)
user_input = "Igor'; DROP TABLE users; --"
query = "SELECT * FROM users WHERE name = $1"
await db.execute(query, user_input)
```

**SQLAlchemy ORM previne automaticamente:**
```python
from sqlalchemy import select

# Safe
result = await session.execute(
    select(User).where(User.name == user_input)
)
```

---

## 5. Integrações Externas

### 5.1 OAuth2 (Google APIs)

**Escopos mínimos necessários:**
```python
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',  # Calendar
    'https://www.googleapis.com/auth/gmail.send',       # Gmail send
    'https://www.googleapis.com/auth/gmail.readonly',   # Gmail read
    'https://www.googleapis.com/auth/drive.file',       # Drive (files created by app)
]
```

**Armazenamento seguro de tokens:**
```python
class GoogleOAuth:
    async def store_tokens(self, user_id: str, tokens: dict):
        """Armazena tokens de forma segura"""
        encrypted_access = encrypt_sensitive_data(tokens['access_token'])
        encrypted_refresh = encrypt_sensitive_data(tokens['refresh_token'])
        
        await db.execute("""
            INSERT INTO oauth_tokens (
                user_id, provider, access_token, refresh_token, expires_at
            ) VALUES ($1, 'google', $2, $3, $4)
            ON CONFLICT (user_id, provider) 
            DO UPDATE SET 
                access_token = $2,
                refresh_token = $3,
                expires_at = $4,
                updated_at = NOW()
        """, user_id, encrypted_access, encrypted_refresh, tokens['expires_at'])
    
    async def refresh_token(self, user_id: str):
        """Refresh token se expirado"""
        # Buscar refresh_token do DB
        # Chamar Google OAuth2 para renovar
        # Salvar novos tokens
```

### 5.2 Telegram Bot Security

**Webhook Validation:**
```python
def validate_telegram_update(update: dict, token: str) -> bool:
    """Valida que update veio do Telegram"""
    # Telegram assina updates com bot token
    # Verificar assinatura
    pass

# Configurar webhook com secret token
import requests

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
WEBHOOK_URL = "https://assistant.igordomain.com/webhooks/telegram"
SECRET_TOKEN = secrets.token_urlsafe(32)

response = requests.post(
    f"{TELEGRAM_API}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "secret_token": SECRET_TOKEN,
        "allowed_updates": ["message", "callback_query"]
    }
)
```

### 5.3 Gemini API

**Proteção de API Key:**
- Nunca expor no frontend
- Usar variável de ambiente
- Rate limiting no backend

**Sanitização de prompts:**
```python
async def call_gemini(prompt: str, user_id: str) -> str:
    """Chama Gemini com segurança"""
    
    # Rate limit por usuário (previne abuso)
    await check_user_rate_limit(user_id, "gemini_calls", limit=100, period="hour")
    
    # Sanitizar prompt (remover dados sensíveis se necessário)
    sanitized_prompt = sanitize_prompt(prompt)
    
    # Truncar se muito longo (previne custos excessivos)
    if len(sanitized_prompt) > 10000:
        sanitized_prompt = sanitized_prompt[:10000]
    
    # Chamar API
    response = await gemini.generate_content(sanitized_prompt)
    
    # Log da chamada (sem dados sensíveis)
    await log_gemini_call(user_id, len(sanitized_prompt), response.token_count)
    
    return response.text
```

---

## 6. Logs e Auditoria

### 6.1 Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self):
        self.logger = logging.getLogger("assistant")
        
    def log(self, level: str, message: str, **context):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **context
        }
        
        # Remover dados sensíveis
        log_entry = self._sanitize(log_entry)
        
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_entry)
        )
    
    def _sanitize(self, entry: dict) -> dict:
        """Remove dados sensíveis dos logs"""
        sensitive_keys = ['password', 'token', 'api_key', 'secret']
        
        for key in list(entry.keys()):
            if any(s in key.lower() for s in sensitive_keys):
                entry[key] = "***REDACTED***"
        
        return entry

# Uso
logger = StructuredLogger()

logger.log("info", "User action", 
    user_id="123",
    action="create_task",
    task_id="456"
)
```

### 6.2 Assistant Logs (Auditoria)

```sql
CREATE TABLE assistant_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    action_type TEXT NOT NULL,  -- 'message', 'tool_call', 'recommendation'
    input_data JSONB,
    output_data JSONB,
    reasoning TEXT,  -- LLM reasoning
    tool_calls JSONB,  -- Ferramentas executadas
    tokens_used INTEGER,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assistant_logs_user_created 
ON assistant_logs(user_id, created_at DESC);
```

**Inserir log:**
```python
async def log_assistant_action(
    user_id: str,
    action_type: str,
    input_data: dict,
    output_data: dict,
    reasoning: str = None,
    tool_calls: list = None,
    tokens_used: int = 0,
    duration_ms: int = 0,
    success: bool = True,
    error_message: str = None
):
    await db.execute("""
        INSERT INTO assistant_logs (
            user_id, action_type, input_data, output_data,
            reasoning, tool_calls, tokens_used, duration_ms,
            success, error_message
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """, user_id, action_type, input_data, output_data,
        reasoning, tool_calls, tokens_used, duration_ms,
        success, error_message)
```

---

## 7. Conformidade

### 7.1 LGPD (Lei Geral de Proteção de Dados)

**Direitos do usuário:**
1. ✅ Acesso aos dados
2. ✅ Correção de dados
3. ✅ Exclusão de dados (direito ao esquecimento)
4. ✅ Portabilidade (export JSON)
5. ✅ Transparência (política de privacidade)

**Implementação:**
```python
@app.get("/api/v1/user/data-export")
async def export_user_data(user_id: str = Depends(get_current_user)):
    """Exporta todos os dados do usuário (LGPD compliance)"""
    
    data = {
        "user": await get_user_data(user_id),
        "tasks": await get_user_tasks(user_id),
        "notes": await get_user_notes(user_id),
        "projects": await get_user_projects(user_id),
        "logs": await get_user_logs(user_id),
        # ... todos os dados
    }
    
    # Retornar JSON
    return JSONResponse(content=data)

@app.delete("/api/v1/user/delete-account")
async def delete_account(
    user_id: str = Depends(get_current_user),
    confirmation: str = Body(...)
):
    """Deleta conta e todos os dados (direito ao esquecimento)"""
    
    if confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(400, "Invalid confirmation")
    
    # Soft delete (manter logs por 30 dias)
    await db.execute("""
        UPDATE users 
        SET deleted_at = NOW(), 
            email = 'deleted_' || id || '@deleted.local'
        WHERE id = $1
    """, user_id)
    
    # Agendar hard delete após 30 dias
    await schedule_hard_delete(user_id, days=30)
    
    return {"message": "Account deletion scheduled"}
```

### 7.2 Política de Retenção de Dados

```python
# Retenção de logs
RETENTION_POLICIES = {
    "assistant_logs": 365,  # 1 ano
    "audit_logs": 2190,     # 6 anos (compliance)
    "deleted_users": 30,    # 30 dias antes de hard delete
    "backups": 90,          # 90 dias
}

# Job de limpeza (rodar diariamente)
async def cleanup_old_data():
    for table, days in RETENTION_POLICIES.items():
        await db.execute(f"""
            DELETE FROM {table}
            WHERE created_at < NOW() - INTERVAL '{days} days'
        """)
```

---

## 8. Incident Response

### 8.1 Plano de Resposta a Incidentes

**Níveis de severidade:**

| Nível | Descrição | Tempo de Resposta | Exemplo |
|-------|-----------|-------------------|---------|
| P0    | Crítico   | Imediato          | Data breach, sistema down |
| P1    | Alto      | 1 hora            | API lenta, erros frequentes |
| P2    | Médio     | 4 horas           | Feature quebrada |
| P3    | Baixo     | 24 horas          | Bug cosmético |

**Processo:**

1. **Detecção**
   - Monitoring alerts
   - User reports
   - Security scans

2. **Contenção**
   - Isolar sistema afetado
   - Revogar acessos se necessário
   - Backup imediato

3. **Erradicação**
   - Identificar causa raiz
   - Aplicar correção
   - Testar fix

4. **Recuperação**
   - Restaurar serviço
   - Validar funcionamento
   - Comunicar usuários

5. **Lições Aprendidas**
   - Post-mortem
   - Documentar
   - Prevenir recorrência

### 8.2 Contatos de Emergência

```
Security Lead: Igor
Email: security@igordomain.com
Telegram: @igor_security
Phone: +55 (XX) XXXXX-XXXX

Backup: [Developer 2]
Email: dev2@igordomain.com
```

### 8.3 Comunicação de Incidentes

**Template de comunicação:**

```
Subject: [SECURITY] Incident Notification - [SUMMARY]

Dear User,

We are writing to inform you of a security incident that occurred on [DATE].

WHAT HAPPENED:
[Brief description]

WHAT DATA WAS AFFECTED:
[Specific data types, no sensitive details]

WHAT WE'RE DOING:
[Actions taken]

WHAT YOU SHOULD DO:
[User actions if needed]

We sincerely apologize for any inconvenience.

Best regards,
TB Personal OS Security Team
```

---

## 9. Checklist de Segurança

### Desenvolvimento

- [ ] Variáveis de ambiente configuradas
- [ ] Secrets não commitados no Git
- [ ] Input validation em todas as entradas
- [ ] Output encoding (previne XSS)
- [ ] SQL injection prevention (parametrized queries)
- [ ] RLS ativo em todas as tabelas
- [ ] HTTPS enforced
- [ ] CORS configurado corretamente
- [ ] Rate limiting implementado
- [ ] Logging estruturado
- [ ] Error handling sem expor internals

### Deploy

- [ ] SSL/TLS certificate válido
- [ ] Firewall configurado
- [ ] Backups automáticos ativos
- [ ] Monitoring e alertas configurados
- [ ] Secrets em environment variables
- [ ] Database backups criptografados
- [ ] Incident response plan documentado
- [ ] Política de retenção de dados implementada

### Manutenção

- [ ] Dependencies atualizadas (npm audit, pip-audit)
- [ ] Security patches aplicados
- [ ] Logs revisados semanalmente
- [ ] Backups testados mensalmente
- [ ] Penetration testing anual
- [ ] Security training contínuo

---

## 10. Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Supabase Security Docs](https://supabase.com/docs/guides/auth/row-level-security)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [LGPD](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

---

**Última atualização:** 03/01/2026  
**Versão:** 1.0  
**Próxima revisão:** 03/04/2026
