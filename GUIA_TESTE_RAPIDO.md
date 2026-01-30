# 🧪 Guia Rápido de Teste - Bot Melhorado

## ⚡ Como Testar em 5 Minutos

### 1️⃣ Reiniciar o Bot
```bash
# SSH no servidor
ssh user@189.126.105.51

# Ir para pasta do projeto
cd /var/www/assistente_igor/backend

# Parar bot (se rodando)
pkill -f run_bot.py

# Reiniciar
nohup python3 run_bot.py > bot.log 2>&1 &

# Verificar se está rodando
ps aux | grep run_bot
```

---

### 2️⃣ Testes Básicos no Telegram

#### ✅ Teste 1: Cumprimento (não deve salvar na inbox)
```
Você: Oi

Esperado: 
"E aí! 👋 Tudo certo? Em que posso ajudar hoje?"

❌ Se responder: "✅ Salvo na Inbox | ID: ..." → Não funcionou
✅ Se responder naturalmente → Funcionou!
```

#### ✅ Teste 2: Pedido de Ajuda (deve fazer perguntas)
```
Você: Quero ajuda para criar uma dieta

Esperado:
"Boa! Vamos montar algo personalizado pra você. Me conta:
1️⃣ Qual seu objetivo principal?
2️⃣ Faz exercício? Quantas vezes por semana?
3️⃣ Tem alguma restrição alimentar?"

❌ Se responder: "Estou pronto para ajudar" → Não funcionou
✅ Se fizer perguntas específicas → Funcionou!
```

#### ✅ Teste 3: Continuação (deve avançar)
```
Você: Beleza, vamos

Esperado (continuando conversa anterior):
"Ótimo! Primeira pergunta: qual seu peso e altura atuais?"

❌ Se responder: "Ok!" ou "Aguardo" → Não funcionou
✅ Se continuar com próxima pergunta → Funcionou!
```

#### ✅ Teste 4: Tarefa (sem IDs técnicos)
```
Você: Preciso lembrar de ligar pro dentista amanhã

Esperado:
"Anotei: 'Ligar pro dentista amanhã' 📅"

❌ Se mostrar: "ID: 87dd92f9" ou "Status: pending" → Não funcionou
✅ Se resposta for limpa e natural → Funcionou!
```

---

### 3️⃣ Teste Rápido Automatizado

```bash
cd /var/www/assistente_igor/backend

# Rodar teste (vai bater no rate limit, mas ok)
python3 tests/test_bot_conversation_quality.py

# Ver resultado
cat test_results_bot_quality.json | grep "avg_score"
```

**Resultado esperado:** `avg_score >= 6.0`

---

## 📊 Checklist de Validação Rápida

### Conversação Natural ✓
- [ ] Bot responde "Oi" sem salvar na inbox
- [ ] Bot faz perguntas quando usuário pede ajuda
- [ ] Bot continua conversa quando usuário confirma
- [ ] Nenhum ID ou termo técnico aparece

### Fluidez ✓  
- [ ] Conversa não "trava" em nenhum momento
- [ ] Bot sempre propõe próximo passo
- [ ] Respostas são naturais, não robotizadas

### Fallback ✓
- [ ] Se Gemini falhar, resposta é elegante
- [ ] Sem mensagens de erro técnicas para usuário

---

## 🐛 Se Algo Não Funcionar

### Problema: Bot não responde
```bash
# Ver logs
tail -100 /var/www/assistente_igor/backend/bot.log

# Verificar se processo está rodando
ps aux | grep run_bot

# Reiniciar
cd /var/www/assistente_igor/backend
pkill -f run_bot
nohup python3 run_bot.py > bot.log 2>&1 &
```

### Problema: Ainda mostra IDs/linguagem técnica
```bash
# Verificar se mudanças foram aplicadas
grep "REGRAS DE OURO" /var/www/assistente_igor/backend/app/services/conversation_service.py

# Se não encontrar, arquivo não foi atualizado
# Reaplicar mudanças ou fazer pull do repo
```

### Problema: Gemini rate limit
```
Error: "You exceeded your current quota..."
```
**Solução:** Aguardar 1 minuto entre testes (free tier = 5 req/min)

---

## 📈 Comparação Antes vs Depois

### ANTES (Ruim) ❌
```
Igor: "Oi"
Bot: "✅ Salvo na Inbox
     📌 Tipo: Note
     🏷 Categoria: Personal
     ID: 87dd92f9
     💡 Acknowledge the message"

Igor: "Quero criar uma dieta"
Bot: "Vou ajudar você!"

Igor: "Beleza"
Bot: "Ok!"
[Conversa morre]
```

### DEPOIS (Bom) ✅
```
Igor: "Oi"
Bot: "E aí! 👋 Tudo certo? Em que posso ajudar hoje?"

Igor: "Quero criar uma dieta"
Bot: "Boa! Vamos montar algo personalizado. Me conta:
     1️⃣ Qual seu objetivo?
     2️⃣ Faz exercício?
     3️⃣ Tem restrições?"

Igor: "Beleza"
Bot: "Ótimo! Primeira pergunta: qual seu peso e altura?"
[Conversa CONTINUA]
```

---

## ✅ Critérios de Sucesso

### Mínimo Aceitável (Sprint 1):
- [x] Não salva cumprimentos na inbox
- [x] Faz perguntas quando usuário pede ajuda
- [x] Continua conversa quando usuário confirma
- [x] Sem IDs ou termos técnicos
- [x] Score >= 6.0/10

### Ideal (Sprint 2+):
- [ ] Contexto emocional
- [ ] Sugestões proativas
- [ ] Memória de longo prazo
- [ ] Score >= 8.5/10

---

## 🚀 Próximo Passo

Se todos os testes passarem:
1. ✅ Marcar Sprint 1 como concluída
2. ✅ Documentar melhorias
3. 🎯 Planejar Sprint 2

Se algum teste falhar:
1. ❌ Debugar problema específico
2. ❌ Aplicar correção
3. ❌ Re-testar

---

**Tempo estimado de teste:** 5-10 minutos  
**Resultado esperado:** Melhoria visível na conversação  
**Meta:** Score 6.0+ (Aceitável) → 7.0+ (Bom)
