# 🎉 Bot Configurado! Próximos Passos

## ✅ Status Atual

- ✅ **Supabase**: Banco de dados criado
- ✅ **Telegram Bot**: @Nariscabot criado e configurado
- ✅ **Gemini API**: Configurada
- ⏳ **Chat ID**: Precisa obter

---

## 📱 Passo 1: Obter seu Chat ID (2 minutos)

### 1.1 Envie uma mensagem para o bot

1. Abra o Telegram
2. Busque por: **@Nariscabot**
3. Envie: `/start` ou qualquer mensagem

### 1.2 Pegue seu Chat ID

Execute este comando:

```bash
cd /var/www/producao/assistente_igor

curl -s "https://api.telegram.org/bot8207386845:AAGiQXcpBjneGtCndzoM81BiBts9fArfrXU/getUpdates" | python3 -c "import sys, json; data = json.load(sys.stdin); updates = data.get('result', []); print(f\"✅ Chat ID: {updates[-1]['message']['chat']['id']}\") if updates else print('⚠️ Envie /start para @Nariscabot primeiro!')"
```

### 1.3 Adicione o Chat ID no .env

```bash
nano backend/.env

# Encontre a linha OWNER_TELEGRAM_CHAT_ID e adicione o número:
OWNER_TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
```

Exemplo:
```bash
OWNER_TELEGRAM_CHAT_ID=123456789
```

---

## 🚀 Passo 2: Executar o Setup

```bash
cd /var/www/producao/assistente_igor

# Execute o setup (instala dependências)
./scripts/setup.sh
```

Isso vai:
- Criar ambiente virtual Python
- Instalar todas as dependências
- Verificar configurações

---

## 🔥 Passo 3: Iniciar o Sistema

```bash
# Inicie o desenvolvimento
./scripts/dev.sh
```

Isso abrirá uma sessão tmux com:
- **Backend** (Python FastAPI) na porta 8000
- **Frontend** (React + Vite) na porta 5173

### Acesse:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

---

## 🧪 Passo 4: Testar o Bot

### 4.1 Verificar Backend está rodando

```bash
# Em outro terminal
curl http://localhost:8000/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "service": "TB Personal OS",
  "version": "0.1.0"
}
```

### 4.2 Testar Gemini AI

```bash
curl -X POST http://localhost:8000/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá! Quem é você?"}'
```

### 4.3 Enviar mensagem para você via Telegram

```bash
curl -X POST http://localhost:8000/api/v1/telegram/send \
  -H "Content-Type: application/json" \
  -d '{"message": "🎉 TB Personal OS está online!"}'
```

### 4.4 Conversar com o bot

1. Abra o Telegram
2. Envie mensagens para @Nariscabot
3. Veja os logs no terminal do backend

---

## 🎯 Comandos do Bot (Planejados)

Comandos que vamos implementar:

```
/start - Iniciar conversa com o assistente
/inbox - Ver sua inbox
/tasks - Ver tarefas pendentes
/add <tarefa> - Adicionar tarefa rápida
/today - Resumo do dia
/week - Planejamento semanal
/energy - Registrar nível de energia
/help - Ajuda
```

---

## 🐛 Troubleshooting

### Erro: Module not found

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Backend não inicia

```bash
# Verifique se a porta 8000 está livre
lsof -i :8000

# Mude a porta se necessário (backend/.env)
API_PORT=8001
```

### Bot não responde

1. Verifique se o backend está rodando
2. Verifique os logs: `tmux attach -t tb-personal-os`
3. Verifique se o token está correto no `.env`

### Frontend com erro

```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Navegação no tmux

O comando `./scripts/dev.sh` abre 3 windows:

- **Window 0**: Backend (Python)
- **Window 1**: Frontend (React)
- **Window 2**: Logs

### Comandos úteis:

```bash
# Trocar entre windows
Ctrl+B depois 0, 1, ou 2

# Desanexar da sessão
Ctrl+B depois d

# Reanexar à sessão
tmux attach -t tb-personal-os

# Ver logs do backend
Ctrl+B depois 0

# Scroll nos logs
Ctrl+B depois [ (use setas, q para sair)

# Matar sessão
tmux kill-session -t tb-personal-os
```

---

## 📝 Checklist de Configuração

- [x] Supabase configurado
- [x] Banco de dados criado
- [x] Gemini API configurada
- [x] Bot do Telegram criado
- [x] Token do bot configurado
- [ ] Chat ID configurado
- [ ] Backend instalado (./scripts/setup.sh)
- [ ] Sistema rodando (./scripts/dev.sh)
- [ ] Primeiro teste bem sucedido

---

## 🎯 Primeira Feature: Inbox

Após tudo funcionando, a primeira feature a implementar é a **Inbox**:

1. Receber mensagens do Telegram
2. Salvar no banco (tabela `inbox_items`)
3. Classificar com Gemini AI
4. Exibir no frontend
5. Sugerir ações

**Arquivo**: `backend/app/api/v1/endpoints/inbox.py` (criar)

---

## 📚 Recursos

- **Bot Telegram**: @Nariscabot (t.me/Nariscabot)
- **Supabase**: https://lbxsqyzjtjqtfclagddd.supabase.co
- **Documentação**: `docs/ARQUITETURA.md`
- **MVP Plan**: `docs/MVP_PLAN.md`
- **Setup Guide**: `SETUP_GUIDE.md`

---

## 💡 Dicas

1. **Mantenha o tmux aberto**: Muito mais fácil visualizar logs
2. **Use os API Docs**: http://localhost:8000/api/docs para testar endpoints
3. **Commits frequentes**: Faça git commit do seu progresso
4. **Teste incrementalmente**: Não faça muitas mudanças sem testar

---

**Criado em:** 03/01/2026  
**Bot:** @Nariscabot  
**Status:** ✅ Quase pronto! Falta apenas o Chat ID

🚀 **Envie /start para @Nariscabot e vamos começar!**
