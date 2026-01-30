# 📖 Igor Assistant - Guia do Usuário

## Sumário

1. [Introdução](#introdução)
2. [Primeiros Passos](#primeiros-passos)
3. [Bot Telegram](#bot-telegram)
4. [Dashboard Web](#dashboard-web)
5. [Módulos do Sistema](#módulos-do-sistema)
6. [Integrações Google](#integrações-google)
7. [Dicas e Truques](#dicas-e-truques)
8. [FAQ](#faq)

---

## Introdução

**Igor** é seu assistente pessoal inteligente que ajuda você a:

- 📥 **Centralizar entradas** - Capture tudo em um só lugar
- ✅ **Gerenciar tarefas** - Organize e execute com eficiência
- 📅 **Controlar agenda** - Sincronize com Google Calendar
- 🏥 **Monitorar saúde** - Acompanhe energia, humor e sono
- 💰 **Controlar finanças** - Entradas, saídas e projeções
- 💡 **Receber insights** - Padrões e recomendações personalizadas
- 🤖 **Ações autônomas** - O Igor pode agir por você

---

## Primeiros Passos

### 1. Configurar o Bot Telegram

1. Abra o Telegram e busque por `@Nariscabot`
2. Envie `/start` para iniciar
3. Pronto! Você pode começar a usar

### 2. Conectar Google (opcional)

Para sincronizar calendário, emails e arquivos:

1. No Telegram, envie `/conectar`
2. Clique no link de autorização
3. Faça login com sua conta Google
4. Autorize as permissões solicitadas

### 3. Acessar o Dashboard

1. Acesse `https://igor.seudominio.com`
2. Faça login com suas credenciais
3. Explore as diferentes páginas

---

## Bot Telegram

### Comandos Básicos

| Comando | Descrição |
|---------|-----------|
| `/start` | Iniciar o bot |
| `/ajuda` | Ver lista de comandos |
| `/resumo` | Resumo do seu dia |

### Gerenciar Tarefas

| Comando | Exemplo | Descrição |
|---------|---------|-----------|
| `/nova` | `/nova Revisar relatório` | Criar nova tarefa |
| `/tarefas` | `/tarefas` | Ver tarefas pendentes |
| `/done` | `/done 1` | Marcar tarefa como concluída |

**Dica:** Você pode simplesmente enviar uma mensagem como "preciso revisar o relatório" e o Igor irá classificar e criar a tarefa automaticamente!

### Inbox

| Comando | Descrição |
|---------|-----------|
| `/inbox` | Ver itens na sua inbox |

Qualquer mensagem que você enviar será capturada e classificada pelo Igor.

### Calendário

| Comando | Descrição |
|---------|-----------|
| `/agenda` | Ver eventos de hoje |
| `/calendario` | Ver próximos eventos |

### Saúde

| Comando | Exemplo | Descrição |
|---------|---------|-----------|
| `/checkin` | `/checkin` | Fazer check-in rápido |
| `/energia` | `/energia 7` | Registrar nível de energia (1-10) |
| `/humor` | `/humor animado` | Registrar seu humor |
| `/saude` | `/saude` | Ver resumo de saúde |
| `/metas` | `/metas` | Ver metas de saúde |
| `/correlacoes` | `/correlacoes` | Ver correlações detectadas |

### Finanças

| Comando | Exemplo | Descrição |
|---------|---------|-----------|
| `/financas` | `/financas` | Ver resumo financeiro |
| `/entrada` | `/entrada 500 Freelance` | Registrar entrada |
| `/saida` | `/saida 50 Almoço` | Registrar saída |

### Projetos

| Comando | Exemplo | Descrição |
|---------|---------|-----------|
| `/projetos` | `/projetos` | Listar projetos ativos |
| `/projeto` | `/projeto App Mobile` | Ver ou criar projeto |

### Conteúdo

| Comando | Exemplo | Descrição |
|---------|---------|-----------|
| `/ideia` | `/ideia Post sobre produtividade` | Salvar ideia |
| `/ideias` | `/ideias` | Ver ideias pendentes |

### Insights

| Comando | Descrição |
|---------|-----------|
| `/insights` | Ver insights e recomendações |

### Outros

| Comando | Descrição |
|---------|-----------|
| `/emails` | Ver emails não lidos |
| `/arquivos` | Arquivos recentes do Drive |
| `/memoria` | Buscar nas memórias |
| `/lembrar` | Salvar uma informação importante |
| `/autonomia` | Ver nível de autonomia |
| `/rotina` | Executar rotina manualmente |

---

## Dashboard Web

### Páginas Disponíveis

#### 📊 Dashboard
Visão geral do seu dia:
- Tarefas pendentes e concluídas
- Próximos eventos
- Métricas de saúde
- Atividade recente

#### ✅ Tarefas
Gerencie suas tarefas:
- Filtrar por status, prioridade, projeto
- Criar e editar tarefas
- Marcar como concluída
- Ver tarefas atrasadas

#### 📥 Inbox
Sua caixa de entrada unificada:
- Mensagens recebidas
- Processar com IA
- Converter para tarefas
- Arquivar

#### 💬 Chat
Converse com o Igor:
- Faça perguntas
- Peça recomendações
- Discuta suas metas

#### 📅 Calendário
Visualize sua agenda:
- Eventos do Google Calendar
- Navegação por mês
- Criar novos eventos

#### 📁 Projetos
Organize por projetos:
- Grid de projetos
- Progresso visual
- Tarefas por projeto

#### 🏥 Saúde
Acompanhe seu bem-estar:
- Histórico de check-ins
- Gráficos de tendência
- Metas de saúde
- Correlações detectadas

#### 💡 Insights
Entenda seus padrões:
- Score de produtividade
- Padrões detectados
- Recomendações personalizadas

#### ⚙️ Configurações
Personalize o Igor:
- Perfil
- Notificações
- Integrações
- Aparência
- Segurança

---

## Módulos do Sistema

### 📥 Inbox Unificada

O Igor captura tudo que você envia:
- Mensagens no Telegram
- Notas de voz
- Fotos e documentos
- Links

O sistema classifica automaticamente usando IA e sugere ações.

### 🧠 Memória

O Igor lembra de informações importantes:
- Suas preferências
- Objetivos declarados
- Histórico de decisões
- Contexto das conversas

Use `/lembrar [informação]` para salvar algo importante.

### 🤖 Níveis de Autonomia

Configure quanto o Igor pode agir sozinho:

| Nível | Descrição |
|-------|-----------|
| 1 - Observer | Apenas observa e reporta |
| 2 - Suggester | Sugere ações para você aprovar |
| 3 - Assistant | Executa tarefas simples automaticamente |
| 4 - Partner | Age proativamente em tarefas médias |
| 5 - Autonomous | Autonomia total em tarefas seguras |

---

## Integrações Google

### Google Calendar
- ✅ Visualizar eventos
- ✅ Criar novos eventos
- ✅ Sincronização automática
- ✅ Alertas de conflitos

### Gmail
- ✅ Ver emails não lidos
- ✅ Buscar emails
- ✅ Criar rascunhos
- ✅ Enviar emails

### Google Drive
- ✅ Listar arquivos recentes
- ✅ Buscar arquivos
- ✅ Criar pastas por projeto
- ✅ Upload de arquivos

---

## Dicas e Truques

### 1. Use Linguagem Natural
Em vez de comandos, você pode falar naturalmente:
- "Preciso ligar para o João amanhã"
- "Lembrar de pagar conta de luz dia 15"
- "Reunião com cliente às 14h"

### 2. Check-ins Rápidos
Faça check-ins curtos várias vezes ao dia. O Igor aprende seus padrões e dá recomendações melhores.

### 3. Rotinas Automáticas
O Igor envia resumos automáticos:
- **7h** - Resumo da manhã + tarefas do dia
- **21h** - Review do dia + preview de amanhã
- **Domingo 19h** - Planejamento semanal

### 4. Conecte Tudo
Quanto mais integrações, melhor o Igor funciona. Conecte:
- Google Calendar (agenda)
- Gmail (emails)
- Drive (arquivos)

### 5. Dê Feedback
Quando o Igor sugere algo, diga se foi útil. Ele aprende com seu feedback!

---

## FAQ

### O Igor é seguro?
Sim! Todos os dados são criptografados e armazenados de forma segura. Não compartilhamos informações com terceiros.

### Posso usar em grupo?
Não, o Igor é um assistente pessoal individual. Cada usuário tem sua própria instância.

### Como cancelo uma ação?
Envie `/cancelar` a qualquer momento para interromper uma operação.

### O Igor funciona offline?
Não, é necessário conexão com internet para usar o Igor.

### Como exporto meus dados?
No Dashboard, vá em Configurações > Dados > Exportar.

### Como deleto minha conta?
No Dashboard, vá em Configurações > Segurança > Deletar Conta.

### Onde vejo os logs?
No Dashboard, vá em Configurações > Segurança > Logs de Atividade.

---

## Suporte

Precisa de ajuda?

- 📧 Email: suporte@igor.app
- 💬 Telegram: @IgorSuporte
- 📚 Docs: https://docs.igor.app

---

*Última atualização: Janeiro 2026*
