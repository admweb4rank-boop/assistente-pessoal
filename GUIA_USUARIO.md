# 👤 GUIA DO USUÁRIO - Performance Points Assistant

> **Para:** Usuários Finais  
> **Versão:** 2.0  
> **Data:** 26 de Janeiro de 2026

---

## 📋 ÍNDICE

1. [Primeiros Passos](#primeiros-passos)
2. [Comandos Essenciais](#comandos-essenciais)
3. [Como Usar Diariamente](#como-usar-diariamente)
4. [Personalizando Seu Assistente](#personalizando-seu-assistente)
5. [Gamificação - XP e Níveis](#gamificação---xp-e-níveis)
6. [Quests Diárias](#quests-diárias)
7. [Dicas e Truques](#dicas-e-truques)
8. [FAQ](#faq)

---

## 🚀 PRIMEIROS PASSOS

### 1. Ativação

Envie `/start` no Telegram para ativar o bot.

O assistente vai iniciar o **Quiz de Onboarding** (7 perguntas rápidas):

```
1️⃣ Como você quer ser tratado?
2️⃣ Quais áreas da vida quer focar?
3️⃣ Habilidades a desenvolver?
4️⃣ Metas do ano?
5️⃣ Principais bloqueios?
6️⃣ Frequência de atividade física?
7️⃣ Situação de renda?
```

**Tempo:** 3-5 minutos  
**Por que?** Para personalizar completamente sua experiência!

### 2. Conclusão do Quiz

Após completar, você receberá:
- **Seu arquétipo** (ex: 🧠 Estrategista de Performance)
- **Resumo do perfil** (áreas, metas, desafios)
- **Próximos passos** claros

### 3. Primeira Ação

Experimente:
```
/status     → Ver seu dashboard
/quest      → Pegar primeira missão
ou apenas   → Converse naturalmente!
```

---

## 🎮 COMANDOS ESSENCIAIS

### Informações e Status

#### `/status`
Mostra seu dashboard completo:
- Nível e XP atual
- 4 métricas (Energia, Foco, Execução, Renda)
- Seu perfil (arquétipo, áreas, metas)
- Conquistas desbloqueadas
- Próxima ação sugerida

**Exemplo de resposta:**
```
🧠 STATUS | PERFORMANCE POINTS

👤 Igor
🧠 Estrategista de Performance
✨ Nível 3 • 250/300 XP

━━━━━━━━━━━━━━━━━━

⚡ Energia: 75% | 🎯 Foco: 82%
🛠️ Execução: 68% | 💰 Renda: 50%

📊 PERFIL ATUAL:

🎯 Meta 2026: Ganhar primeiro cliente
💪 Habilidades: Python, Marketing
🎨 Áreas: 💪 Saúde, 💼 Trabalho
⚠️ Bloqueios: ⏰ Procrastinação
```

#### `/help`
Lista todos os comandos disponíveis com descrições.

#### `/sobre`
Informações sobre o assistente e suas capacidades.

---

### Gamificação e Progresso

#### `/quest`
Recebe sua missão do dia (adaptada ao seu perfil).

**Características:**
- Baseada em suas áreas prioritárias
- Dificuldade ajustada ao seu nível
- XP garantido ao completar
- Atualiza a cada 24h

**Exemplo:**
```
🎯 QUEST DO DIA

🛠️ Executor de Elite

📋 Tarefa: Complete 3 tarefas da sua lista
⏱️ Tempo estimado: 90 minutos
✨ Recompensa: 150 XP

🎁 Bônus possível: +50 XP se completar antes das 12h

/quest_complete quando finalizar!
```

#### `/checkin [1-10]`
Registra sua energia atual.

**Exemplos:**
```
/checkin 8    → Energia: 80%
/checkin 5    → Energia: 50%
/checkin 10   → Energia: 100%!
```

**Impacto:**
- Atualiza métrica de Energia no `/status`
- Usado para adaptar quests
- ML detecta padrões ao longo do tempo

---

### Tarefas e Organização

#### `/task`
Cria nova tarefa com gamificação.

**Modo interativo:**
```
Você: /task
Bot: Qual tarefa você quer criar?

Você: Revisar proposta para cliente
Bot: ✅ Tarefa criada!
     📝 Revisar proposta para cliente
     💰 Categoria: work
     🎯 Prioridade: high
     ✨ +25 XP ao completar
```

**Modo direto:**
```
/task Estudar Python por 1h
```

#### `/inbox`
Mostra itens capturados automaticamente.

**O que vai para inbox:**
- Mensagens que o bot identifica como tarefas
- Ideias mencionadas
- Lembretes
- Links para revisar depois

---

### Personalização

#### `/quiz`
Refaz o quiz de onboarding.

**Quando refazer:**
- Suas prioridades mudaram
- Novos bloqueios surgiram
- A cada 15-30 dias (recomendado)

#### `/perfil`
Edita aspectos específicos do perfil sem refazer tudo.

**Opções:**
```
/perfil areas         → Mudar áreas prioritárias
/perfil metas         → Atualizar metas
/perfil habilidades   → Ajustar skills
```

---

## 💬 COMO USAR DIARIAMENTE

### Modo 1: Conversa Natural

**Você pode simplesmente conversar!**

```
Você: preciso focar mais no trabalho
Bot: Entendi. Vejo que Trabalho é uma das suas 
     áreas prioritárias. Você tem 2 tarefas 
     pendentes nessa área:
     
     • Revisar proposta
     • Preparar apresentação
     
     Quer criar uma quest focada nisso? Ou 
     prefere usar /task para organizar melhor?
```

**O bot usa seu perfil para responder:**
- Conhece suas áreas, metas e bloqueios
- Lembra conversas anteriores
- Sugere ações baseadas no contexto

### Modo 2: Check-ins Rápidos

```
Manhã:
Você: /checkin 7
Bot: ⚡ Energia: 70%. Bom dia! Pronto para 
     executar? Você tem 1 quest disponível.

Tarde:
Você: /checkin 5
Bot: ⚡ Energia: 50%. Detectei queda. Seus 
     padrões mostram que você é mais produtivo
     pela manhã. Que tal uma pausa de 15min?
```

### Modo 3: Quests Diárias

```
1. /quest                  → Pega missão
2. Executa a missão        → Trabalho focado
3. /quest_complete         → +XP
4. /status                 → Ver progresso
```

### Modo 4: Captura Rápida

```
Você: lembrar de ligar pro cliente amanhã
Bot: ✅ Anotado! Criei um lembrete.
     
     📌 Ligar pro cliente
     📅 Amanhã
     
     Aparece na sua /inbox
```

---

## 🎨 PERSONALIZANDO SEU ASSISTENTE

### Como Ele Aprende Sobre Você?

#### 1. Explicitamente (Quiz)
- Áreas prioritárias
- Metas do ano
- Bloqueios conhecidos
- Preferências de comunicação

#### 2. Implicitamente (ML)
- Detecta seus horários de pico
- Analisa taxa de conclusão de tarefas
- Aprende seu estilo de comunicação
- Identifica padrões de consistência

#### 3. Conversacionalmente (Memória)
- Lembra o que você conta
- Guarda contexto de conversas
- Usa em respostas futuras

### Ensinando Novos Assuntos

#### Método 1: Contar Diretamente
```
Você: importante: meu processo de vendas tem 3 etapas:
      1) Qualificação do lead
      2) Proposta personalizada  
      3) Follow-up em 48h

Bot: ✅ Anotei! Salvei isso como conhecimento.
     Vou usar nas próximas conversas sobre vendas.
```

#### Método 2: Criar Contexto
```
Você: vou trabalhar com metodologia SCRUM agora
Bot: Legal! SCRUM é ágil. Sprints de quanto tempo?

Você: 2 semanas
Bot: ✅ Perfeito. Vou adaptar as sugestões de 
     tarefas para ciclos de 2 semanas.
```

#### Método 3: Definir Processos
```
Você: toda segunda de manhã faço planejamento semanal
Bot: ✅ Entendi! Segunda de manhã = planejamento.
     
     Quer que eu envie um lembrete ou crie 
     uma quest recorrente pra isso?
```

### Adaptando o Tom

O assistente já adapta baseado no seu arquétipo:

- **🎯 Executor Pragmático** → Direto, sem floreios
- **🧠 Estrategista** → Analítico, usa dados
- **⚡ Guerreiro** → Motivacional, foca em energia
- **🧘 Explorador** → Reflexivo, holístico

**Quer mudar?**
```
/perfil tom

Opções:
• Direto e prático
• Calmo e reflexivo  
• Estratégico e provocador
• Personalizado (descrever)
```

---

## 🏆 GAMIFICAÇÃO - XP E NÍVEIS

### Como Ganhar XP

| Ação | XP | Frequência |
|------|----|-----------
| Completar tarefa | 25-50 | Ilimitado |
| Quest diária | 100-200 | 1x/dia |
| Check-in de energia | 10 | Ilimitado |
| Completar onboarding | 500 | 1x |
| Streak de 7 dias | 300 | Semanal |
| Level up | Bônus | Por nível |

### Sistema de Níveis

```
Nível 1-5:   🌱 Aprendiz       (0-2.500 XP)
Nível 6-10:  ⚔️ Aventureiro    (2.500-10.000 XP)
Nível 11-20: 🛡️ Veterano       (10.000-40.000 XP)
Nível 21-30: 🏆 Elite          (40.000-90.000 XP)
Nível 31-50: ⭐ Mestre         (90.000-250.000 XP)
Nível 51+:   👑 Lenda          (250.000+ XP)
```

### 4 Métricas de Performance

#### ⚡ Energia (0-100%)
**Baseado em:** Check-ins recentes  
**Como melhorar:** Check-ins regulares, quests de saúde

#### 🎯 Foco (0-100%)
**Baseado em:** Taxa de conclusão de tarefas (7 dias)  
**Como melhorar:** Completar tarefas, reduzir pendências

#### 🛠️ Execução (0-100%)
**Baseado em:** Consistência (tarefas/30 dias)  
**Como melhorar:** Criar hábito diário, streaks

#### 💰 Renda (0-100%)
**Baseado em:** Transações financeiras (se cadastradas)  
**Como melhorar:** Registrar receitas, metas financeiras

---

## 🎯 QUESTS DIÁRIAS

### Como Funcionam

1. **Geração:** Todo dia às 00:00
2. **Personalização:** Baseada em:
   - Suas áreas prioritárias
   - Nível atual
   - Energia recente
   - Bloqueios mapeados
3. **Adaptação:** Dificuldade aumenta com seu progresso

### Tipos de Quest

#### 🛠️ Execução
- Completar X tarefas
- Trabalhar focado por X minutos
- Finalizar projeto específico

#### 💪 Saúde
- Exercício por X minutos
- Check-in de energia 3x
- Dormir 8h (confirmar manhã)

#### 🧠 Desenvolvimento
- Estudar X por Y minutos
- Ler artigo/capítulo
- Praticar habilidade

#### 💰 Renda
- Prospectar X leads
- Enviar proposta
- Follow-up cliente

### Bônus e Multipliers

```
🎁 Completar antes do meio-dia: +50% XP
🔥 Streak de 7 dias: +2x XP
⭐ Quest perfeita (sem erros): +100 XP bônus
```

---

## 💡 DICAS E TRUQUES

### 1. Rotina Matinal Ideal

```
07:00 - /checkin 8
        "Bom dia! Energia: 80%"
        
07:05 - /quest
        Recebe missão do dia
        
07:10 - /status
        Vê progresso geral
        
07:15 - Executa primeira tarefa
```

### 2. Captura Rápida Durante o Dia

Não precisa comando específico:
```
Você: lembrar de revisar contrato
      → Bot salva automaticamente

Você: ideia: criar curso sobre X
      → Bot categoriza e organiza

Você: ligar pro João às 15h
      → Bot cria lembrete
```

### 3. Check-ins Estratégicos

```
Manhã (ao acordar):     /checkin
Meio-dia (pós-work):   /checkin
Tarde (pós-almoço):    /checkin
Noite (balanço):       /checkin

ML detecta padrões e sugere melhores horários!
```

### 4. Revisão Semanal

```
Todo domingo:
1. /status              → Ver métricas da semana
2. /perfil metas        → Ajustar se necessário
3. Conversar sobre      → Refletir com bot
   "como foi a semana?"
```

### 5. Maximize XP

```
Sequência ideal:
1. /checkin 9           +10 XP
2. /quest (pegar)       0 XP
3. Completar quest      +150 XP
4. /task (criar 3)      0 XP
5. Completar todas      +75 XP (3x25)
6. Streak bonus         +50 XP

Total: 285 XP em um dia! 🚀
```

---

## ❓ FAQ

### "O bot não está lembrando o que eu disse"

**Resposta:** Ele deve lembrar! Se não:
1. Verifique se completou o `/quiz`
2. Converse mais (memória aumenta com uso)
3. Use frases como "importante:", "lembre:", "anote:"

### "Como faço o bot aprender sobre meu trabalho?"

**Resposta:** Conte pra ele!
```
Você: meu trabalho envolve 3 áreas:
      1) Consultoria
      2) Criação de conteúdo
      3) Gestão de projetos

Bot: ✅ Anotei! Vou usar isso para 
     personalizar suas quests e sugestões.
```

### "Posso mudar meu arquétipo?"

**Resposta:** Sim! Use `/quiz` para refazer. Ou apenas converse diferente - o bot adapta ao longo do tempo.

### "O que acontece se eu não fizer a quest?"

**Resposta:** Nada de ruim! Nova quest no dia seguinte. Mas você perde o XP e possíveis bônus.

### "Como funciona o ML? Ele está me vigiando?"

**Resposta:** Não é vigilância! O ML apenas detecta:
- Seus horários de maior produtividade
- Sua taxa de conclusão de tarefas
- Seu estilo preferido de comunicação

Tudo para **personalizar melhor** sua experiência.

### "Posso usar com minha equipe?"

**Resposta:** Atualmente é individual. Versão empresarial (multi-usuário) planejada para 2026 Q2.

### "Como adiciono integração com outras ferramentas?"

**Resposta:** Por enquanto manual. Planejado:
- Notion (2026 Q1)
- Google Calendar (2026 Q1)
- Todoist (2026 Q2)

### "Quanto custa?"

**Resposta:** Versão atual é gratuita. Planos premium planejados com:
- Mais integrações
- Análises avançadas
- Prioridade no suporte

---

## 🎓 PRÓXIMOS PASSOS

### Novato (Nível 1-5)
1. ✅ Complete o quiz
2. ✅ Use `/status` diariamente
3. ✅ Faça 3 check-ins por dia
4. ✅ Complete primeira quest
5. ✅ Crie 5 tarefas

### Intermediário (Nível 6-20)
1. ✅ Mantenha streak de 7 dias
2. ✅ Explore todos os comandos
3. ✅ Ensine processos pro bot
4. ✅ Complete 10 quests
5. ✅ Refaça o quiz

### Avançado (Nível 21+)
1. ✅ Use conversa natural como principal
2. ✅ Deixe ML aprender seus padrões
3. ✅ Customize tom e preferências
4. ✅ Contribua com feedback
5. ✅ Ajude a melhorar o sistema

---

## 📞 SUPORTE

**Dúvidas?** Pergunte ao próprio bot:
```
Você: como faço para [sua dúvida]?
```

**Bugs ou sugestões?**
- Telegram: @seu_suporte
- Email: suporte@performancepoints.com
- GitHub: Issues no repositório

---

**Guia mantido por:** Time Performance Points  
**Última atualização:** 26 de Janeiro de 2026  
**Versão do Sistema:** 2.0

**Vamos construir progresso juntos! 🚀**
