# 📊 TIPOS DE CHECK-INS E MÉTRICAS DISPONÍVEIS

**Data:** 27 de Janeiro de 2026  
**Sistema:** Performance Points v2.0

---

## 🎯 MÉTRICAS EXIBIDAS NO /status

Atualmente **5 métricas** são calculadas e exibidas:

```
📊 MÉTRICAS DE PERFORMANCE:

⚡ Energia: 75% | 🎯 Foco: 82%
🛠️ Execução: 68% | 💰 Renda: 50%
😴 Sono: 70%
```

| # | Métrica | Emoji | Fonte de Dados | Cálculo |
|---|---------|-------|---------------|---------|
| 1 | **Energia** | ⚡ | Check-ins `energy` (últimos 3) | Média (0-10) → 0-100% |
| 2 | **Foco** | 🎯 | Tarefas completadas (7 dias) | Taxa de conclusão |
| 3 | **Execução** | 🛠️ | Consistência de tarefas (30 dias) | Quantidade concluída |
| 4 | **Renda** | 💰 | Transações `transactions` (30 dias) | R$ 1000+ = 100% |
| 5 | **Sono** | 😴 | Check-ins `sleep` (últimos 7) OU Quiz | Horas + qualidade |

---

## ✅ TIPOS DE CHECK-IN SUPORTADOS

### Definidos no Schema (Migration)

**Arquivo:** `supabase/migrations/00001_initial_schema.sql`

```sql
CONSTRAINT valid_checkin_type CHECK (
    checkin_type IN (
        'energy',      -- Energia
        'mood',        -- Humor
        'sleep',       -- Sono
        'workout',     -- Exercício
        'nutrition',   -- Nutrição
        'habit',       -- Hábito
        'custom'       -- Customizado
    )
)
```

### Implementados no Código

**Arquivo:** `backend/app/services/checkin_service.py`

| Tipo | Método | Status | Descrição |
|------|--------|--------|-----------|
| **energy** | `checkin_energy()` | ✅ Ativo | Nível de energia (1-10) |
| **mood** | `checkin_mood()` | ✅ Ativo | Humor (emoji ou texto) |
| **sleep** | `checkin_sleep()` | ✅ Ativo | Horas + qualidade (1-10) |
| **workout** | `checkin_workout()` | ✅ Ativo | Tipo + duração + intensidade |
| **nutrition** | - | ⚠️ Schema apenas | Não implementado |
| **habit** | - | ⚠️ Schema apenas | Não implementado |
| **custom** | `create_checkin()` | ✅ Ativo | Qualquer dado customizado |

### Botões no /checkin

**Arquivo:** `backend/app/services/bot_handler_unified.py` (linha 730-736)

```python
keyboard = [
    [
        InlineKeyboardButton("⚡ Energia", callback_data="checkin_energy"),
        InlineKeyboardButton("😊 Humor", callback_data="checkin_mood"),
    ],
    [
        InlineKeyboardButton("😴 Sono", callback_data="checkin_sleep"),
        InlineKeyboardButton("🎯 Foco", callback_data="checkin_focus"),
    ]
]
```

**4 tipos mostrados no bot:**
- ⚡ Energia
- 😊 Humor
- 😴 Sono
- 🎯 Foco (mencionado mas não totalmente implementado)

---

## 📋 DETALHAMENTO POR TIPO

### 1. ⚡ ENERGIA (`energy`)

**Status:** ✅ Totalmente implementado

**Como usar:**
```
/checkin → Energia → [1-10]
OU conversa: "minha energia está 8"
```

**Estrutura de dados:**
```json
{
  "checkin_type": "energy",
  "value": 8,  // número 1-10
  "notes": "Dormi bem, café da manhã leve"
}
```

**Cálculo da métrica:**
- Busca últimos 3 check-ins
- Calcula média
- Converte 0-10 → 0-100%
- Default: 50% se não tem dados

**Arquivo:** `gamification_service.py::_calculate_real_energy()`

---

### 2. 😊 HUMOR (`mood`)

**Status:** ✅ Totalmente implementado

**Como usar:**
```
/checkin → Humor → [emoji ou texto]
Aceita: 😊 😐 😢 😤 😴 🤩
Ou: happy, sad, tired, excited, etc.
```

**Estrutura de dados:**
```json
{
  "checkin_type": "mood",
  "value": {
    "mood": "happy",
    "score": 8
  },
  "notes": "Bom dia produtivo"
}
```

**Mapeamento de humores:**
| Emoji/Texto | Humor | Score |
|-------------|-------|-------|
| 😊 happy feliz | happy | 8 |
| 😐 neutral normal | neutral | 5 |
| 😢 sad triste | sad | 3 |
| 😤 angry irritado | angry | 2 |
| 😴 tired cansado | tired | 4 |
| 🤩 excited empolgado | excited | 9 |

**Uso:** Análise de padrões emocionais (futuro)

---

### 3. 😴 SONO (`sleep`)

**Status:** ✅ Totalmente implementado

**Como usar:**
```
/checkin → Sono → [horas] [qualidade 1-10]
Exemplo: 7.5 horas, qualidade 8
```

**Estrutura de dados:**
```json
{
  "checkin_type": "sleep",
  "value": {
    "hours": 7.5,
    "quality": 8,
    "score": 9.75  // (hours + quality/2)
  },
  "notes": "Sono profundo, sem interrupções"
}
```

**Cálculo da métrica:**
1. Prioridade: Últimos 7 check-ins de sono
2. Fallback: Resposta do quiz (`sleep_quality`)
3. Mapeamento quiz → score:
   - excellent → 90%
   - good → 70%
   - irregular → 50%
   - poor → 30%
   - very_poor → 15%

**Arquivo:** `gamification_service.py::_calculate_real_sleep()`

---

### 4. 🏋️ EXERCÍCIO (`workout`)

**Status:** ✅ Implementado (não exibido em métrica)

**Como usar:**
```python
# Via código (não tem botão no /checkin)
await checkin_service.checkin_workout(
    user_id=user_id,
    workout_type="corrida",
    duration_minutes=30,
    intensity="high"
)
```

**Estrutura de dados:**
```json
{
  "checkin_type": "workout",
  "value": {
    "type": "corrida",
    "duration": 30,
    "intensity": "high",
    "score": 7.5
  },
  "metadata": {
    "workout_type": "corrida"
  }
}
```

**Tipos de treino:** Qualquer (corrida, musculação, yoga, etc.)  
**Intensidade:** low (3), medium (6), high (9)

**Uso:** Análise de frequência e volume de treinos

---

### 5. 🎯 FOCO (`checkin_focus`)

**Status:** ⚠️ Parcialmente implementado

**Situação atual:**
- ✅ Botão existe no `/checkin`
- ❌ Método dedicado não implementado
- ✅ Métrica calculada de forma **indireta** (taxa de conclusão de tarefas)

**Como a métrica de Foco é calculada:**
- Fonte: Tarefas dos últimos 7 dias
- Fórmula: `(tarefas_completas / total_tarefas) * 100`
- Arquivo: `gamification_service.py::_calculate_real_focus()`

**Pendente:** Implementar check-in direto de foco

---

### 6. 🍎 NUTRIÇÃO (`nutrition`)

**Status:** ⚠️ Schema apenas (não implementado)

**Definido em:** Migration `00001_initial_schema.sql`

**Uso planejado:**
- Registrar refeições
- Qualidade alimentar (1-10)
- Hidratação
- Análise de padrões

**Para implementar:**
```python
async def checkin_nutrition(
    user_id: str,
    meal_type: str,  # café, almoço, jantar, lanche
    quality: int,    # 1-10
    notes: str = None
) -> Dict:
    value = {
        "meal": meal_type,
        "quality": quality,
        "score": quality
    }
    return await create_checkin(
        user_id, "nutrition", value, notes
    )
```

---

### 7. 🔁 HÁBITO (`habit`)

**Status:** ⚠️ Schema apenas (não implementado)

**Definido em:** Migration `00001_initial_schema.sql`

**Relação:** `habit_id UUID REFERENCES habits(id)`

**Uso planejado:**
- Tracking de hábitos específicos
- Streaks (sequências)
- Consistência

---

### 8. ✏️ CUSTOM (`custom`)

**Status:** ✅ Suportado

**Como usar:**
```python
await checkin_service.create_checkin(
    user_id=user_id,
    checkin_type="custom",
    value={"qualquer": "coisa"},
    notes="Check-in personalizado",
    metadata={"categoria": "produtividade"}
)
```

**Uso:** Qualquer tipo de dado que não se encaixa nos tipos padrão

---

## 🔮 MÉTRICAS FUTURAS (NÃO IMPLEMENTADAS)

Estas métricas foram mencionadas mas **não estão ativas**:

| Métrica | Emoji | Status | Como seria calculada |
|---------|-------|--------|---------------------|
| **Saúde/Corpo** | 💪 | 📋 Planejado | Check-ins workout + nutrition |
| **Mindfulness** | 🧘 | 📋 Planejado | Meditação + práticas contemplativas |
| **Produtividade** | 📊 | 📋 Planejado | Pomodoros + deep work hours |
| **Estresse** | 😰 | 📋 Planejado | Check-in direto (1-10) |
| **Social** | 👥 | 📋 Planejado | Interações + relacionamentos |
| **Criatividade** | 🎨 | 📋 Planejado | Projetos + ideias registradas |
| **Aprendizado** | 📚 | 📋 Planejado | Cursos + horas de estudo |

---

## 🎮 RELAÇÃO COM GAMIFICAÇÃO

### XP Ganho por Check-ins

**Arquivo:** `gamification_service.py::on_checkin_completed()`

```python
def on_checkin_completed(user_id: str):
    # Check-in vale +10 XP
    self.add_xp(user_id, 10, "Check-in registrado")
```

**Eventos:**
- ✅ Cada check-in: +10 XP
- 🔥 Streak de 7 dias: +300 XP (bônus)
- 🏆 Conquista "Consistent Tracker": 30 check-ins

---

## 📊 COMANDOS DISPONÍVEIS

### Via Bot Telegram

```
/checkin         → Menu interativo (4 opções)
/checkin [1-10]  → Check-in rápido de energia
/status          → Ver todas as métricas
```

### Via API (Não documentado publicamente)

```bash
# Criar check-in
POST /api/v1/checkins
{
  "user_id": "uuid",
  "checkin_type": "energy",
  "value": 8,
  "notes": "Manhã produtiva"
}

# Listar check-ins
GET /api/v1/checkins?user_id=uuid&type=energy&days=7

# Estatísticas
GET /api/v1/checkins/stats?user_id=uuid&type=energy&days=30
```

---

## 🔧 ARQUITETURA

### Fluxo de Check-in

```
Usuário → /checkin
    ↓
bot_handler_unified.py::cmd_checkin()
    ↓
Botões inline (energy, mood, sleep, focus)
    ↓
Callback handler → solicita valor
    ↓
checkin_service.py::create_checkin()
    ↓
Supabase: INSERT INTO checkins
    ↓
gamification_service.py::on_checkin_completed()
    ↓
+10 XP ao usuário
```

### Fluxo de Cálculo de Métricas

```
Usuário → /status
    ↓
bot_handler_unified.py::cmd_status()
    ↓
gamification_service.py::format_status_message()
    ↓
Para cada métrica:
  _calculate_real_energy()    → Busca checkins.energy
  _calculate_real_sleep()     → Busca checkins.sleep
  _calculate_real_focus()     → Busca tasks (não checkins!)
  _calculate_real_execution() → Busca tasks (30 dias)
  _calculate_real_income()    → Busca transactions
    ↓
Formata e exibe
```

---

## 📝 TABELA RESUMO

| Check-in Type | Implementado | Método Dedicado | Exibido em Métrica | Botão /checkin | Ganho XP |
|--------------|--------------|-----------------|-------------------|----------------|----------|
| energy | ✅ | ✅ `checkin_energy()` | ✅ ⚡ Energia | ✅ | ✅ +10 |
| mood | ✅ | ✅ `checkin_mood()` | ❌ | ✅ | ✅ +10 |
| sleep | ✅ | ✅ `checkin_sleep()` | ✅ 😴 Sono | ✅ | ✅ +10 |
| workout | ✅ | ✅ `checkin_workout()` | ❌ | ❌ | ✅ +10 |
| focus | ⚠️ | ❌ (usa tasks) | ✅ 🎯 Foco | ✅ (não funcional) | ❌ |
| nutrition | ❌ | ❌ | ❌ | ❌ | ❌ |
| habit | ❌ | ❌ | ❌ | ❌ | ❌ |
| custom | ✅ | ✅ `create_checkin()` | ❌ | ❌ | ✅ +10 |

---

## 🚀 RECOMENDAÇÕES

### Curto Prazo (Sprint 1-2)

1. **Implementar `checkin_focus()` dedicado**
   - Pergunta: "Quão focado você está? (1-10)"
   - Adicionar ao cálculo de métrica de Foco
   - Complementar taxa de conclusão de tarefas

2. **Adicionar métrica de Humor no /status**
   - Exibir média da semana
   - Detectar padrões (dias ruins/bons)

3. **Implementar `checkin_nutrition()`**
   - Refeições + qualidade
   - Hidratação (copos de água)
   - Métrica de Saúde

### Médio Prazo (Sprint 3-4)

4. **Dashboard de Check-ins**
   - Gráficos de evolução
   - Comparação semanal/mensal
   - Correlações (sono × energia)

5. **Alertas Inteligentes**
   ```
   "Sua energia está abaixo de 30% há 3 dias.
    Fatores detectados:
    - Sono irregular (média 5.5h)
    - Zero workouts esta semana
    Quer criar um plano de recuperação?"
   ```

6. **Check-in por Voz**
   - Telegram voice → transcrição
   - Parse natural: "energia 8, dormi 7 horas"

### Longo Prazo (Sprint 5+)

7. **Integrações Externas**
   - Apple Health / Google Fit
   - Oura Ring / Whoop
   - MyFitnessPal (nutrição)

8. **ML sobre Check-ins**
   - Previsão de energia baseada em padrões
   - Sugestões personalizadas
   - Detecção de burnout

---

**Última atualização:** 27 de Janeiro de 2026  
**Versão do Sistema:** 2.0  
**Documentado por:** GitHub Copilot
