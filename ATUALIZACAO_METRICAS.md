# Atualização de Métricas e Check-ins

## Alterações Implementadas

### 1. ✅ Métrica de Humor (Mood) Adicionada ao Status

**Arquivo:** `backend/app/services/gamification_service.py`

#### Novo método `_calculate_real_mood()`:
```python
def _calculate_real_mood(self, user_id: str) -> Dict[str, Any]:
    """
    Calcula humor médio da semana.
    Retorna: {emoji, score, trend, count}
    """
    # Busca check-ins de mood dos últimos 7 dias
    # Calcula média dos scores
    # Mapeia score → emoji apropriado
    # Retorna: {"emoji": "😊", "score": 70, "count": 5}
```

**Mapeamento de Scores → Emojis:**
- 8-10: 🤩 (Muito animado)
- 6-7.9: 😊 (Feliz)
- 4-5.9: 😐 (Neutro)
- 3-3.9: 😢 (Triste)
- 0-2.9: 😤 (Frustrado)

#### Painel de Status Atualizado:
```
📊 *MÉTRICAS DE PERFORMANCE:*

⚡ Energia: 75% | 🎯 Foco: 60%
🛠️ Execução: 80% | 💰 Renda: 45%
😴 Sono: 65% | 😊 70% (5 reg.)
```

O contador de registros (`5 reg.`) indica quantos check-ins de humor foram feitos nos últimos 7 dias.

---

### 2. ✅ Métodos de Check-in de Foco e Nutrição

**Arquivo:** `backend/app/services/checkin_service.py`

#### Método `checkin_focus()`:
```python
async def checkin_focus(self, user_id: str, level: int, notes: Optional[str] = None):
    """Check-in de foco/concentração (1-10)."""
    if not 1 <= level <= 10:
        raise ValueError("Nível de foco deve ser entre 1 e 10")
    return await self.create_checkin(
        user_id=user_id,
        checkin_type="focus",
        value=level,
        notes=notes
    )
```

#### Método `checkin_nutrition()`:
```python
async def checkin_nutrition(self, user_id, meal_type, quality, hydration, notes):
    """Check-in de nutrição."""
    if not 1 <= quality <= 10:
        raise ValueError("Qualidade deve ser entre 1 e 10")
    value = {
        "meal": meal_type,      # breakfast, lunch, dinner, snack
        "quality": quality,      # 1-10
        "hydration": hydration,  # copos de água
        "score": quality
    }
    return await self.create_checkin(user_id, "nutrition", value, notes)
```

---

## Próximos Passos

### 🔴 **Crítico** (Necessário para funcionar):

1. **Adicionar handlers do bot para Focus e Nutrition**
   - Arquivo: `backend/app/bot_handler_unified.py`
   - Adicionar callbacks para botões e conversas interativas

2. **Adicionar botões de Workout e Nutrition ao /checkin**
   - Modificar teclado inline em `checkin_main()`
   - Adicionar opções: 🏋️ Treino | 🥗 Nutrição

3. **Migração do banco de dados**
   - Adicionar 'focus' ao tipo válido em `checkins.checkin_type`
   - Arquivo: `supabase/migrations/00010_add_focus_type.sql`

### 🟡 **Importante** (Melhorias):

4. **Adaptar métricas ao perfil do quiz**
   - Mostrar apenas métricas relevantes às áreas de foco do usuário
   - Exemplo: se áreas = [work, health], destacar Execução e Energia

5. **Sugestões contextuais no status**
   - Baseado nas métricas baixas, sugerir ações
   - Exemplo: "Energia em 40%. Que tal um check-in de sono?"

### 🟢 **Opcional** (Nice to have):

6. **Histórico de métricas**
   - Comando /evolucao com gráficos de tendência
   - Comparação semanal/mensal

7. **Metas personalizadas**
   - Permitir usuário definir metas específicas por métrica
   - Exemplo: "Quero alcançar Energia > 80%"

---

## Status Atual dos Check-ins

| Tipo | Backend | UI Button | Handler | Status Display |
|------|---------|-----------|---------|----------------|
| Energy | ✅ | ✅ | ✅ | ✅ |
| Mood | ✅ | ✅ | ✅ | ✅ **NOVO** |
| Sleep | ✅ | ✅ | ✅ | ✅ |
| Focus | ✅ **NOVO** | ❌ | ❌ | ❌ |
| Workout | ✅ | ❌ | ✅ | ❌ |
| Nutrition | ✅ **NOVO** | ❌ | ❌ | ❌ |
| Habit | ❌ | ❌ | ❌ | ❌ |
| Custom | ✅ | ❌ | ✅ | ❌ |

---

## Como Testar

1. **Teste a métrica de Humor:**
   ```
   /checkin → 😊 Humor → Escolha um emoji
   /status → Veja "😊 70% (1 reg.)" na linha de métricas
   ```

2. **Teste os novos métodos via código:**
   ```python
   # Focus
   await checkin_service.checkin_focus(user_id, level=8, notes="Produtivo hoje")
   
   # Nutrition
   await checkin_service.checkin_nutrition(
       user_id=user_id,
       meal_type="lunch",
       quality=9,
       hydration=6,
       notes="Almoço saudável"
   )
   ```

---

## Arquivos Modificados

1. **backend/app/services/gamification_service.py**
   - Adicionado `_calculate_real_mood()` (linhas ~700-750)
   - Modificado `get_user_status()` para incluir humor (linha 398)

2. **backend/app/services/checkin_service.py**
   - Adicionado `checkin_focus()` (linhas ~348-362)
   - Adicionado `checkin_nutrition()` (linhas ~364-390)

---

## Impacto

- **Usuários agora veem 6 métricas** no status (antes 5)
- **Humor contextualizado** com emoji e contagem de registros
- **Base pronta** para implementar Focus e Nutrition na UI
- **Sistema mais completo** e alinhado com o roadmap

---

**Data:** 2025-01-XX  
**Desenvolvedor:** GitHub Copilot  
**Status:** ✅ Backend completo | ⏳ UI pendente
