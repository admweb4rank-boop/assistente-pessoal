# 🧪 Guia de Teste - Sistema de Check-ins Completo

## ✅ Pré-requisitos

1. Bot está rodando:
```bash
ps aux | grep run_bot
```

2. Verifique logs:
```bash
tail -f /var/www/assistente_igor/backend/bot.log
```

---

## 🎯 Testes Essenciais

### 1️⃣ **Teste do Menu de Check-in**

**Comando:**
```
/checkin
```

**Resultado Esperado:**
```
📊 Check-in

O que você quer registrar?

[⚡ Energia] [😊 Humor]
[😴 Sono] [🎯 Foco]
[🏋️ Treino] [🥗 Nutrição]
```

✅ **Sucesso:** 6 botões aparecem  
❌ **Falha:** Menos de 6 botões ou erro

---

### 2️⃣ **Teste de Energia (Básico)**

**Fluxo:**
1. `/checkin`
2. Clique: ⚡ Energia
3. Digite: `8`

**Resultado Esperado:**
```
✅ ⚡ Energia registrada: 8/10

+10 XP
```

---

### 3️⃣ **Teste de Humor (Botões)**

**Fluxo:**
1. `/checkin`
2. Clique: 😊 Humor
3. Clique: 😊 (Happy)

**Resultado Esperado:**
```
✅ 😊 Humor registrado!

+10 XP
```

---

### 4️⃣ **Teste de Sono (Decimal)**

**Fluxo:**
1. `/checkin`
2. Clique: 😴 Sono
3. Digite: `7.5`

**Resultado Esperado:**
```
✅ 😴 Sono registrado: 7.5h

+10 XP
```

---

### 5️⃣ **Teste de Foco (NOVO)**

**Fluxo:**
1. `/checkin`
2. Clique: 🎯 Foco
3. Digite: `9`

**Resultado Esperado:**
```
✅ 🎯 Foco registrado: 9/10

+10 XP
```

---

### 6️⃣ **Teste de Treino (Fluxo Completo - NOVO)**

**Fluxo:**
1. `/checkin`
2. Clique: 🏋️ Treino
3. Clique: 🏃 Cardio
4. Digite: `45`
5. Clique: 🔥 Alta

**Resultado Esperado:**
```
✅ 🏋️ Treino registrado!

Tipo: cardio
Duração: 45min
Intensidade: 🔥 high

+10 XP
```

---

### 7️⃣ **Teste de Nutrição (Fluxo Completo - NOVO)**

**Fluxo:**
1. `/checkin`
2. Clique: 🥗 Nutrição
3. Clique: 🍽️ Almoço
4. Digite: `9`
5. Digite: `6`

**Resultado Esperado:**
```
✅ 🥗 Nutrição registrada!

Qualidade: 9/10
Hidratação: 6 copos

+10 XP
```

---

### 8️⃣ **Teste de Métricas no Status**

**Comando:**
```
/status
```

**Resultado Esperado:**
```
📊 *MÉTRICAS DE PERFORMANCE:*

⚡ Energia: XX% | 🎯 Foco: XX%
🛠️ Execução: XX% | 💰 Renda: XX%
😴 Sono: XX% | 😊 XX% (X reg.)
```

✅ **Sucesso:** 6 métricas aparecem, Mood com emoji e contador  
❌ **Falha:** Menos de 6 métricas ou erro

---

## 🔍 Testes de Validação

### Teste de Validação 1: Energia Inválida
```
/checkin → ⚡ Energia → 15
```
**Esperado:** `❌ Digite um número entre 1 e 10`

### Teste de Validação 2: Sono Inválido
```
/checkin → 😴 Sono → 30
```
**Esperado:** `❌ Digite um número válido de horas (ex: 7.5)`

### Teste de Validação 3: Foco Negativo
```
/checkin → 🎯 Foco → -5
```
**Esperado:** `❌ Digite um número entre 1 e 10`

### Teste de Validação 4: Nutrição Qualidade Alta
```
/checkin → 🥗 Nutrição → Café → 15
```
**Esperado:** `❌ Digite um número entre 1 e 10`

---

## 📊 Teste de Gamificação

1. Anote o XP atual: `/status`
2. Faça um check-in qualquer
3. Verifique `/status` novamente
4. **Esperado:** XP aumentou em +10

---

## 🐛 Troubleshooting

### Problema: Bot não responde

**Solução:**
```bash
cd /var/www/assistente_igor/backend
pkill -f run_bot.py
nohup python3 run_bot.py > bot.log 2>&1 &
```

### Problema: Erro ao registrar check-in

**Verificar:**
1. Logs: `tail -f bot.log`
2. Tipo de check-in está permitido no banco?
   - Execute: `/var/www/assistente_igor/scripts/apply_checkin_types_migration.sh`
   - Copie o SQL e execute no Supabase Dashboard

### Problema: Métricas não aparecem

**Verificar:**
1. Código de `gamification_service.py` foi atualizado?
2. Bot foi reiniciado?

---

## ✅ Checklist de Validação Completa

- [ ] Menu `/checkin` mostra 6 botões
- [ ] Energia funciona (1-10)
- [ ] Humor funciona (emojis)
- [ ] Sono funciona (horas decimais)
- [ ] **Foco funciona (NOVO 1-10)**
- [ ] **Treino completo (tipo → duração → intensidade)**
- [ ] **Nutrição completa (refeição → qualidade → hidratação)**
- [ ] `/status` mostra 6 métricas
- [ ] Mood aparece no status com emoji e contador
- [ ] Validações bloqueiam valores inválidos
- [ ] XP é concedido em todos os check-ins
- [ ] Estado de conversa limpo após check-in

---

## 📝 Notas

- **Migration pendente:** Executar SQL no Supabase para permitir tipos 'focus' e 'nutrition'
- **Próxima feature:** Adaptar métricas exibidas baseado no quiz
- **Documentação completa:** Ver `IMPLEMENTACAO_COMPLETA.md`

---

**Data do Teste:** _______________  
**Testador:** _______________  
**Resultado:** ⭕ PASSOU | ⭕ FALHOU | ⭕ PARCIAL
