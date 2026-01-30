# 🎯 PLANO DE FINALIZAÇÃO COMPLETA - Performance Points

**Data:** 27 de Janeiro de 2026  
**Objetivo:** Integração completa Quiz → Perfil → Métricas → Jornada Diária

---

## 🔍 MAPEAMENTO DE GARGALOS

### 🔴 CRÍTICOS (Bloqueiam UX)

| # | Gargalo | Impacto | Severidade |
|---|---------|---------|------------|
| 1 | **Botão Foco não funcional** | Usuário clica mas nada acontece | 🔴 ALTO |
| 2 | **Mood não aparece no /status** | Dados coletados mas não exibidos | 🟡 MÉDIO |
| 3 | **Workout não tem botão** | Feature implementada mas inacessível | 🟡 MÉDIO |
| 4 | **Nutrition não implementado** | Citado no quiz mas sem funcionalidade | 🟠 BAIXO |

### 🟡 IMPORTANTES (Melhoram UX)

| # | Gap | Descrição |
|---|-----|-----------|
| 5 | **Habit tracking** | Schema existe mas sem implementação |
| 6 | **Correlação quiz ↔ métricas** | Quiz mapeia áreas mas não adapta métricas |
| 7 | **Sugestões contextuais** | Não há ações sugeridas baseadas em métricas |
| 8 | **Histórico visual** | Sem gráficos de evolução |

### 🟢 OPCIONAIS (Nice to have)

| # | Feature | Prioridade |
|---|---------|-----------|
| 9 | Dashboard web | Baixa |
| 10 | Integrações externas | Baixa |
| 11 | Alertas proativos | Média |

---

## 📋 DIAGNÓSTICO DETALHADO

### 1. 🔴 Botão Foco Não Funcional

**Arquivo:** `backend/app/services/bot_handler_unified.py`

**Problema:**
```python
# Linha 735
InlineKeyboardButton("🎯 Foco", callback_data="checkin_focus")
# ❌ Callback handler não implementado
```

**Impacto:**
- Usuário clica → Nada acontece
- Confusão e frustração
- Métrica de Foco é calculada via tarefas (indireto)

**Solução:**
- Implementar `checkin_focus()` no `checkin_service.py`
- Adicionar callback handler no bot
- Método deve perguntar: "Quão focado você está? (1-10)"

---

### 2. 🟡 Mood Não Aparece no /status

**Arquivo:** `backend/app/services/gamification_service.py`

**Problema:**
```python
# Métricas calculadas:
energy = self._calculate_real_energy(user_id)
focus = self._calculate_real_focus(user_id)
execution = self._calculate_real_execution(user_id)
income = self._calculate_real_income(user_id)
sleep = self._calculate_real_sleep(user_id, quiz_answers)

# ❌ Mood NÃO é calculado nem exibido
```

**Dados disponíveis:**
- `checkins.mood` - Check-ins de humor funcionam
- Dados estruturados: `{mood: "happy", score: 8}`

**Solução:**
- Criar `_calculate_real_mood()` 
- Adicionar ao painel de status
- Exibir média da semana + emoji do humor atual

---

### 3. 🟡 Workout Sem Botão

**Arquivo:** `backend/app/services/bot_handler_unified.py`

**Problema:**
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
    # ❌ Falta linha para Workout
]
```

**Método existe:**
- `checkin_service.checkin_workout()` ✅
- Aceita: tipo, duração, intensidade
- Salva corretamente

**Solução:**
- Adicionar botão "🏋️ Treino" no teclado
- Criar fluxo interativo:
  1. Tipo de treino (corrida, musculação, yoga)
  2. Duração em minutos
  3. Intensidade (baixa, média, alta)

---

### 4. 🟠 Nutrition Não Implementado

**Status:** Schema existe, código não

**Schema:** `checkin_type = 'nutrition'` ✅

**Missing:**
```python
# ❌ Não existe
async def checkin_nutrition(
    user_id: str,
    meal_type: str,  # café, almoço, jantar, lanche
    quality: int,    # 1-10
    hydration: int = None  # copos de água
)
```

**Relação com Quiz:**
- Quiz pergunta sobre áreas (corpo/saúde)
- Nutrition seria métrica complementar
- Importante para usuários focados em saúde

**Solução:**
- Implementar método `checkin_nutrition()`
- Adicionar botão no /checkin (segunda linha)
- Criar métrica de Nutrição no /status (opcional)

---

## 🎯 PLANO DE IMPLEMENTAÇÃO

### FASE 1: CORREÇÕES CRÍTICAS (2-3 horas)

#### ✅ Task 1.1: Implementar Check-in de Foco

**Arquivo:** `backend/app/services/checkin_service.py`

```python
async def checkin_focus(
    self,
    user_id: str,
    level: int,  # 1-10
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check-in de foco/concentração (1-10).
    """
    if not 1 <= level <= 10:
        raise ValueError("Nível de foco deve ser entre 1 e 10")
    
    return await self.create_checkin(
        user_id=user_id,
        checkin_type="focus",
        value=level,
        notes=notes
    )
```

**Arquivo:** `backend/app/services/bot_handler_unified.py`

```python
# Adicionar handler para callback "checkin_focus"
def handle_checkin_focus_callback(self, update, context):
    query = update.callback_query
    query.answer()
    
    context.user_data['awaiting_checkin_focus'] = True
    
    query.edit_message_text(
        "🎯 *Check-in de Foco*\n\n"
        "Quão focado você está agora?\n"
        "Digite um número de 1 a 10:\n\n"
        "1 = Totalmente disperso\n"
        "5 = Foco médio\n"
        "10 = Laser focus",
        parse_mode=ParseMode.MARKDOWN
    )

# Na handle_message, adicionar:
if context.user_data.get('awaiting_checkin_focus'):
    try:
        level = int(message)
        # Salvar check-in de foco
        # +10 XP
        context.user_data['awaiting_checkin_focus'] = False
    except:
        pass
```

#### ✅ Task 1.2: Adicionar Mood ao Status

**Arquivo:** `backend/app/services/gamification_service.py`

```python
def _calculate_real_mood(self, user_id: str) -> Dict[str, Any]:
    """
    Calcula humor médio da semana.
    Retorna: {emoji, score, trend}
    """
    try:
        from datetime import datetime, timedelta
        
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        result = self.supabase.table('checkins')\
            .select('value')\
            .eq('user_id', user_id)\
            .eq('checkin_type', 'mood')\
            .gte('created_at', seven_days_ago)\
            .order('created_at', desc=True)\
            .execute()
        
        if not result.data:
            return {"emoji": "😐", "score": 5, "count": 0}
        
        # Extrair scores dos valores JSON
        scores = []
        for c in result.data:
            val = c.get('value')
            if isinstance(val, dict):
                scores.append(val.get('score', 5))
        
        if not scores:
            return {"emoji": "😐", "score": 5, "count": 0}
        
        avg_score = sum(scores) / len(scores)
        
        # Mapear score → emoji
        if avg_score >= 8:
            emoji = "🤩"
        elif avg_score >= 6:
            emoji = "😊"
        elif avg_score >= 4:
            emoji = "😐"
        elif avg_score >= 3:
            emoji = "😢"
        else:
            emoji = "😤"
        
        return {
            "emoji": emoji,
            "score": int(avg_score * 10),  # 0-100
            "count": len(scores)
        }
        
    except:
        return {"emoji": "😐", "score": 50, "count": 0}

# Adicionar no format_status_message():
mood_data = self._calculate_real_mood(user_id)

# Adicionar linha no painel:
message = f"""
...
📊 *MÉTRICAS DE PERFORMANCE:*

⚡ Energia: {energy}% | 🎯 Foco: {focus}%
🛠️ Execução: {execution}% | 💰 Renda: {income}%
😴 Sono: {sleep}% | {mood_data['emoji']} Humor: {mood_data['score']}%
...
"""
```

#### ✅ Task 1.3: Adicionar Botão Workout

**Arquivo:** `backend/app/services/bot_handler_unified.py`

```python
keyboard = [
    [
        InlineKeyboardButton("⚡ Energia", callback_data="checkin_energy"),
        InlineKeyboardButton("😊 Humor", callback_data="checkin_mood"),
    ],
    [
        InlineKeyboardButton("😴 Sono", callback_data="checkin_sleep"),
        InlineKeyboardButton("🎯 Foco", callback_data="checkin_focus"),
    ],
    [
        InlineKeyboardButton("🏋️ Treino", callback_data="checkin_workout"),
        InlineKeyboardButton("🍎 Nutrição", callback_data="checkin_nutrition"),
    ]
]
```

**Handler interativo:**
```python
def handle_checkin_workout_callback(self, update, context):
    query = update.callback_query
    query.answer()
    
    # Passo 1: Escolher tipo
    workout_keyboard = [
        [InlineKeyboardButton("🏃 Corrida", callback_data="workout_run")],
        [InlineKeyboardButton("🏋️ Musculação", callback_data="workout_gym")],
        [InlineKeyboardButton("🧘 Yoga", callback_data="workout_yoga")],
        [InlineKeyboardButton("🚴 Bicicleta", callback_data="workout_bike")],
        [InlineKeyboardButton("✏️ Outro", callback_data="workout_custom")]
    ]
    
    query.edit_message_text(
        "🏋️ *Check-in de Treino*\n\nQual tipo de treino?",
        reply_markup=InlineKeyboardMarkup(workout_keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
```

---

### FASE 2: IMPLEMENTAÇÕES IMPORTANTES (3-4 horas)

#### ✅ Task 2.1: Implementar Nutrition

**Arquivo:** `backend/app/services/checkin_service.py`

```python
async def checkin_nutrition(
    self,
    user_id: str,
    meal_type: str,  # breakfast, lunch, dinner, snack
    quality: int,    # 1-10
    hydration: Optional[int] = None,  # copos de água
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check-in de nutrição.
    """
    if not 1 <= quality <= 10:
        raise ValueError("Qualidade deve ser entre 1 e 10")
    
    value = {
        "meal": meal_type,
        "quality": quality,
        "hydration": hydration,
        "score": quality
    }
    
    return await self.create_checkin(
        user_id=user_id,
        checkin_type="nutrition",
        value=value,
        notes=notes
    )
```

#### ✅ Task 2.2: Conectar Quiz com Métricas

**Ideia:** Adaptar métricas exibidas baseado nas áreas prioritárias do quiz

**Arquivo:** `backend/app/services/gamification_service.py`

```python
def format_status_message(self, user_id: str, username: str = "Igor") -> str:
    # ... código atual ...
    
    # ADAPTAR MÉTRICAS EXIBIDAS baseado no quiz
    priority_areas = quiz_answers.get('life_areas', [])
    
    metrics_to_show = []
    
    # Sempre mostrar
    metrics_to_show.append(f"⚡ Energia: {energy}%")
    
    # Condicionais baseadas em áreas
    if 'body_energy' in priority_areas or 'mind_emotions' in priority_areas:
        metrics_to_show.append(f"😴 Sono: {sleep}%")
        metrics_to_show.append(f"{mood_data['emoji']} Humor: {mood_data['score']}%")
    
    if 'work_business' in priority_areas:
        metrics_to_show.append(f"🎯 Foco: {focus}%")
        metrics_to_show.append(f"🛠️ Execução: {execution}%")
    
    if 'income_finances' in priority_areas:
        metrics_to_show.append(f"💰 Renda: {income}%")
    
    # Formatar em 2 colunas
    # ...
```

#### ✅ Task 2.3: Adicionar Sugestões Contextuais

**Arquivo:** `backend/app/services/gamification_service.py`

```python
def _generate_contextual_suggestions(
    self, 
    user_id: str,
    metrics: Dict,
    quiz_answers: Dict
) -> str:
    """
    Gera sugestões baseadas em métricas + perfil.
    """
    suggestions = []
    
    # Energia baixa
    if metrics['energy'] < 40:
        suggestions.append("⚡ Sua energia está baixa. Considere:")
        if metrics.get('sleep', 50) < 50:
            suggestions.append("  • Priorizar sono hoje (meta: 7-8h)")
        suggestions.append("  • Fazer pausas de 5min a cada hora")
    
    # Foco baixo
    if metrics['focus'] < 50:
        suggestions.append("🎯 Foco comprometido. Tente:")
        suggestions.append("  • Técnica Pomodoro (25min focado)")
        suggestions.append("  • Desativar notificações")
    
    # Humor baixo
    if metrics.get('mood_score', 50) < 40:
        suggestions.append("😊 Humor abaixo. Considere:")
        suggestions.append("  • Conversar com alguém")
        suggestions.append("  • 10min de exercício leve")
    
    return "\n".join(suggestions) if suggestions else "✨ Continue assim!"
```

---

### FASE 3: POLIMENTO (2 horas)

#### ✅ Task 3.1: Adicionar Validações no Schema

**Arquivo:** `supabase/migrations/00010_checkin_improvements.sql`

```sql
-- Adicionar constraint para focus
ALTER TABLE checkins DROP CONSTRAINT IF EXISTS valid_checkin_type;

ALTER TABLE checkins ADD CONSTRAINT valid_checkin_type CHECK (
    checkin_type IN (
        'energy', 'mood', 'sleep', 'workout', 
        'nutrition', 'focus', 'habit', 'custom'
    )
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_checkins_user_type_recent 
ON checkins(user_id, checkin_type, created_at DESC);
```

#### ✅ Task 3.2: Testes de Integração

**Arquivo:** `backend/tests/test_checkin_integration.py`

```python
async def test_quiz_to_status_integration():
    """
    Testa fluxo completo:
    1. Usuário completa quiz
    2. Faz check-ins
    3. /status mostra métricas adaptadas
    """
    # 1. Simular quiz
    quiz_answers = {
        'life_areas': ['body_energy', 'work_business'],
        'skills': ['discipline', 'execution']
    }
    
    # 2. Fazer check-ins
    await checkin_service.checkin_energy(user_id, 8)
    await checkin_service.checkin_focus(user_id, 7)
    
    # 3. Gerar status
    status = gamification_service.format_status_message(user_id)
    
    # 4. Validar
    assert "⚡ Energia: 80%" in status
    assert "🎯 Foco:" in status
    assert "Corpo & Energia" in status  # Área do quiz
```

---

## 🗺️ ROADMAP DE EXECUÇÃO

### Sprint 1 (Hoje - 4h)
```
✅ [1h] Implementar checkin_focus()
✅ [1h] Adicionar Mood ao status
✅ [1h] Adicionar botão Workout
✅ [1h] Testar fluxo completo
```

### Sprint 2 (Amanhã - 3h)
```
✅ [2h] Implementar checkin_nutrition()
✅ [1h] Conectar quiz ↔ métricas
```

### Sprint 3 (Dia 3 - 2h)
```
✅ [1h] Sugestões contextuais
✅ [1h] Testes finais
```

---

## 📊 ESTADO FINAL ESPERADO

### Painel /status Completo

```
🧠 STATUS | PERFORMANCE POINTS

👤 Igor
🧠 Estrategista de Performance
✨ Nível 3 • 250/300 XP

━━━━━━━━━━━━━━━━━━

📊 MÉTRICAS DE PERFORMANCE:

⚡ Energia: 75% | 🎯 Foco: 82%
🛠️ Execução: 68% | 💰 Renda: 50%
😴 Sono: 70% | 😊 Humor: 85%

━━━━━━━━━━━━━━━━━━

🎯 PERFIL ATUAL:

Meta 2026:
Ganhar primeiro cliente

💪 Habilidades em Foco:
🎤 Presença
📊 Gestão de projetos
💬 Comunicação

🎨 Áreas Prioritárias:
🏋️ Corpo & Energia
💰 Renda & Finanças
💼 Trabalho / Negócios

⚠️ Bloqueios Mapeados:
🌀 Desorganização
⏳ Procrastinação

━━━━━━━━━━━━━━━━━━

💡 SUGESTÕES DO DIA:

✨ Sua energia está ótima! Aproveite para:
  • Completar tarefas de alta prioridade
  • Avançar na meta "Ganhar primeiro cliente"

🎯 Seu foco está em 82% (excelente!)
  • Mantenha sessões Pomodoro
  • Evite distrações até 16h

━━━━━━━━━━━━━━━━━━

🏆 CONQUISTAS:
🔥 Streak de 7 dias (+300 XP)
⚡ Energy Master (30 check-ins)

━━━━━━━━━━━━━━━━━━

📅 Última revisão: há 3 dias
💡 Use /quest para missão do dia

Seu perfil é baseado no quiz. Use /quiz para refazer.
```

### Botões /checkin Completos

```
📊 Check-in

O que você quer registrar?

[⚡ Energia] [😊 Humor]
[😴 Sono]    [🎯 Foco]
[🏋️ Treino]  [🍎 Nutrição]
```

---

## 🎯 CRITÉRIOS DE SUCESSO

- [ ] Todos os botões do /checkin funcionam
- [ ] Todas as métricas aparecem no /status
- [ ] Métricas são adaptadas às áreas do quiz
- [ ] Sugestões contextuais são relevantes
- [ ] Usuário pode completar jornada: Quiz → Check-ins → Quest → Progresso
- [ ] 100% dos check-ins dão XP
- [ ] Sem erros no log do bot

---

**Próximo passo:** Executar Sprint 1 agora! 🚀
