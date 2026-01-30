# 🚀 Guia de Configuração Rápida - TB Personal OS

## ✅ Status: Credenciais Supabase e Gemini Configuradas!

### 🎯 Configurações Aplicadas

- ✅ Supabase URL: `https://lbxsqyzjtjqtfclagddd.supabase.co`
- ✅ Supabase Keys: Configuradas (anon + service_role)
- ✅ Gemini API: Configurada
- ⏳ Telegram Bot: Precisa configurar
- ⏳ Google OAuth: Opcional (pode fazer depois)

---

## 📱 Passo 1: Criar Bot do Telegram (5 minutos)

### 1.1 Fale com o BotFather

1. Abra o Telegram
2. Busque por: **@BotFather**
3. Inicie conversa: `/start`

### 1.2 Crie seu bot

```
Você: /newbot

BotFather: Alright, a new bot. How are we going to call it?
Você: TB Personal OS Igor

BotFather: Good. Now let's choose a username for your bot.
Você: tb_personal_igor_bot
(ou qualquer nome que termina com _bot)

BotFather: Done! Your bot token is:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 1.3 Configure o Token

```bash
cd /var/www/producao/assistente_igor/backend
nano .env

# Encontre a linha TELEGRAM_BOT_TOKEN e cole o token:
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 1.4 Pegue seu Chat ID

1. Envie qualquer mensagem para seu bot no Telegram
2. Execute este comando:

```bash
# Substitua SEU_TOKEN pelo token do bot
curl https://api.telegram.org/botSEU_TOKEN/getUpdates
```

3. Procure por `"chat":{"id":123456789}` na resposta
4. Adicione no `.env`:

```bash
OWNER_TELEGRAM_CHAT_ID=123456789
```

---

## 🗄️ Passo 2: Criar Banco de Dados no Supabase

### 2.1 Acesse o Supabase

1. Abra: https://lbxsqyzjtjqtfclagddd.supabase.co
2. Faça login
3. Clique em **SQL Editor** (menu lateral)

### 2.2 Execute o Schema

1. Clique em **"+ New query"**
2. Copie todo o conteúdo de: `supabase/migrations/00001_initial_schema.sql`
3. Cole no editor
4. Clique em **"Run"** (ou pressione `Ctrl + Enter`)

### 2.3 Verifique se funcionou

Execute no SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

Você deve ver as tabelas: `users`, `profiles`, `inbox_items`, `tasks`, etc.

---

## 🔧 Passo 3: Setup do Ambiente

```bash
cd /var/www/producao/assistente_igor

# Execute o setup
./scripts/setup.sh
```

Isso vai:
- Criar ambiente virtual Python
- Instalar dependências backend
- Instalar dependências frontend
- Verificar configurações

---

## 🚀 Passo 4: Iniciar o Projeto

```bash
# Inicie o desenvolvimento
./scripts/dev.sh
```

Isso abrirá uma sessão tmux com:
- **Window 0**: Backend (Python FastAPI)
- **Window 1**: Frontend (React + Vite)
- **Window 2**: Logs

### Acessar:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

### Navegar no tmux:
- Trocar windows: `Ctrl+B` depois `0`, `1` ou `2`
- Desanexar: `Ctrl+B` depois `d`
- Reanexar: `tmux attach -t tb-personal-os`

---

## 🧪 Passo 5: Teste Inicial

### 5.1 Teste o Backend

```bash
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

### 5.2 Teste o Gemini

```bash
curl -X POST http://localhost:8000/api/v1/assistant/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, assistente!"}'
```

### 5.3 Teste o Telegram

1. Envie uma mensagem para seu bot
2. Verifique os logs no backend
3. O bot deve responder

---

## 📝 Checklist de Configuração

- [x] Supabase URL e Keys
- [x] Gemini API Key
- [ ] Telegram Bot Token
- [ ] Telegram Chat ID (seu)
- [ ] Banco de dados criado
- [ ] Backend rodando
- [ ] Frontend rodando
- [ ] Primeiro teste bem sucedido

---

## 🔍 Troubleshooting

### Erro: "Module not found"
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: "Port already in use"
```bash
# Mude a porta no backend/.env
API_PORT=8001

# Reinicie
./scripts/dev.sh
```

### Erro: "Cannot connect to Supabase"
- Verifique se a URL está correta
- Verifique se as keys estão corretas
- Teste no navegador: https://lbxsqyzjtjqtfclagddd.supabase.co

### Bot do Telegram não responde
1. Verifique se o token está correto
2. Verifique se o webhook não está configurado (deve estar vazio)
3. Reinicie o backend

---

## 🎯 Próximas Features (Após Setup)

### Semana 1:
1. Implementar Inbox básica
2. Processar mensagens do Telegram
3. Criar tarefas via comando
4. Sistema de logs completo

### Recursos:
- [README.md](README.md) - Visão geral
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md) - Arquitetura
- [docs/MVP_PLAN.md](docs/MVP_PLAN.md) - Plano de 4 semanas
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Status atual

---

## 💡 Dicas

1. **Use o tmux**: É muito mais fácil gerenciar os serviços
2. **Logs são seus amigos**: Sempre verifique os logs quando algo não funcionar
3. **API Docs**: http://localhost:8000/api/docs é interativo!
4. **Git**: Faça commits frequentes do seu progresso
5. **Documentação**: Atualize PROJECT_STATUS.md com o que concluir

---

**Criado em:** 03/01/2026  
**Última atualização:** 03/01/2026  
**Status:** ✅ Pronto para começar!

🚀 **Vamos começar seu assistente pessoal para 2026!**
