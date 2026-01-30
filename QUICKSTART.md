# Quick Start - TB Personal OS

> Guia rápido para começar a desenvolver

## 🚀 Setup Rápido (5 minutos)

### 1. Pré-requisitos

```bash
# Verificar versões
node --version  # >= 18
python --version  # >= 3.11
docker --version
```

### 2. Clonar e Configurar

```bash
cd /var/www/producao/assistente_igor

# Copiar env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cp ml-service/.env.example ml-service/.env

# Editar com suas keys (IMPORTANTE!)
nano backend/.env
```

### 3. Supabase Setup

```bash
# Instalar CLI
npm install -g supabase

# Login
supabase login

# Criar projeto no dashboard: https://supabase.com/dashboard

# Configurar .env com suas keys do Supabase
```

### 4. Criar Telegram Bot

```bash
# 1. Abrir @BotFather no Telegram
# 2. Enviar: /newbot
# 3. Seguir instruções
# 4. Copiar token e colocar em backend/.env
```

### 5. Rodar com Docker (Recomendado)

```bash
docker-compose up -d
```

### 6. Ou rodar manualmente

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**ML Service:**
```bash
cd ml-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

### 7. Acessar

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ML Service:** http://localhost:8001

### 8. Testar

```bash
# Health check
curl http://localhost:8000/health

# Criar tarefa
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Primeira tarefa", "priority": "high"}'
```

## 📖 Próximos Passos

1. Ler [README.md](README.md)
2. Seguir [MVP_PLAN.md](docs/MVP_PLAN.md)
3. Estudar [ARQUITETURA.md](docs/ARQUITETURA.md)
4. Configurar integrações Google

## 🆘 Problemas Comuns

**Erro: Connection refused (database)**
→ Verificar se PostgreSQL está rodando: `docker-compose ps`

**Erro: Invalid token**
→ Verificar `SUPABASE_JWT_SECRET` no .env

**Erro: Module not found**
→ Reinstalar dependências: `pip install -r requirements.txt`

**Telegram não responde**
→ Verificar webhook: `python scripts/check_telegram_webhook.py`

## 🎯 Checklist Inicial

- [ ] Supabase projeto criado
- [ ] Database migrations executadas
- [ ] Telegram bot criado
- [ ] Variáveis de ambiente configuradas
- [ ] Backend rodando (port 8000)
- [ ] Frontend rodando (port 3000)
- [ ] Telegram respondendo mensagens

---

**Dúvidas?** Ver documentação completa no [README.md](README.md)
