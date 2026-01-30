# UI Design Reference - Stay Hydrated App
**Data:** 25 de Janeiro de 2026  
**Fonte:** Referência visual de aplicativo de hidratação

---

## 🎨 Análise Visual Completa

### **1. Paleta de Cores**
```css
/* Cores Primárias */
--neon-yellow: #CAFF00;        /* Destaque principal - títulos, ícones, cards */
--deep-teal: #1A5F7A;          /* Cards secundários, gráficos */
--dark-teal: #0D3D4F;          /* Backgrounds de seções */
--light-gray: #E8EEF2;         /* Background principal */
--white: #FFFFFF;              /* Cards, containers */

/* Cores de Acento */
--blue-water: #4A9FD8;         /* Ícones de água, ilustrações */
--mint-green: #B8E6D5;         /* Bebida verde (chá) */
--coffee-brown: #8B6F47;       /* Café */
--blue-drink: #5FB3E8;         /* Bebida azul */

/* Cores de Estado */
--shadow: rgba(0, 0, 0, 0.08); /* Sombras sutis */
--border: rgba(0, 0, 0, 0.05); /* Bordas suaves */
```

---

## 📐 Estrutura de Layout

### **Grid System:**
- **Sidebar esquerdo:** 80px fixo (vertical navigation)
- **Container principal:** max-width 1200px, padding 24px
- **Grid de cards:** 2 colunas com gap de 24px
- **Responsivo:** Mobile single column, Desktop 2-3 colunas

### **Spacing System:**
```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
2xl: 48px
```

---

## 🧩 Componentes Identificados

### **1. Header com Branding**
```typescript
<Header>
  - Logo (ícone gota d'água)
  - Título "STAY" (preto, bold, 48px)
  - Subtítulo "HYDRATED!" (neon yellow, highlight, 48px)
  - User avatar (canto superior direito)
  - Mini calendar widget
</Header>
```

**Características:**
- Tipografia grande e impactante
- Highlight amarelo neon no subtítulo
- Contraste forte preto/amarelo
- Avatar circular com nome e status

---

### **2. Sidebar de Navegação Vertical**
```typescript
<Sidebar>
  - Home (ícone casa)
  - Dashboard (ícone estrela - ativo)
  - Favoritos (ícone coração)
  - Tarefas (ícone checkbox)
  - Configurações (ícone engrenagem)
  - Mais opções (ícone três pontos)
</Sidebar>
```

**Estilo:**
- Background cinza claro (#E8EEF2)
- Ícones 24x24px
- Item ativo com círculo azul teal
- Padding 16px entre ícones
- Border radius 16px nos itens

---

### **3. Card "Overview" - Hero Principal**
```typescript
<OverviewCard>
  <Ilustração> Pessoa água splash (azul aquarela) </Ilustração>
  <Stats>
    - Meta diária: 1200ml (ícone gota)
    - Passos: 3,544 (ícone pegadas)
    - Progresso: Barra vertical 75%
  </Stats>
  <ProgressCards>
    - Card 1/12 (copos/meta): gráfico linha
    - Card 1h/4h (tempo): waveform amarelo + play button
    - Card visual: copo com água 3D
  </ProgressCards>
</OverviewCard>
```

**Estilo Overview:**
- Background branco com shadow suave
- Border radius 24px
- Padding 32px
- Ilustração estilo watercolor azul
- Cards internos: yellow (#CAFF00) com ícones pretos
- Mini cards com border radius 16px

---

### **4. Card "Select Type of Drink"**
```typescript
<DrinkSelectorCard>
  <Header> "SELECT TYPE OF DRINK" + "All Drinks" link </Header>
  <DrinkIcons>
    - Chá verde (ícone folha)
    - Água (copo azul grande - ativo)
    - Café (xícara marrom)
  </DrinkIcons>
  <Slider>
    350ml | 400ml | 450ml | [500ml] | 550ml | 600ml | 650ml
    Yellow highlight no valor selecionado
  </Slider>
</DrinkSelectorCard>
```

**Estilo Selector:**
- Background branco
- Border radius 24px
- Ícones 64x64px com background colorido
- Slider com marcadores e highlight amarelo
- Valor selecionado em destaque (500ml)

---

### **5. Card "Drink Statistic"**
```typescript
<DrinkStatisticCard>
  <Background> Dark teal (#0D3D4F) </Background>
  <Title> "DRINK STATISTIC" (branco, bold) </Title>
  <BarChart>
    Horários: 8:00, 12:00, 3:00, 8:00, 00:00, 4:00
    Barra amarela destacando horário 12:00
  </BarChart>
  <IconGrid> 
    3x4 grid de copos (ícones pequenos)
    Mostram histórico visual
  </IconGrid>
</DrinkStatisticCard>
```

**Estilo Statistic:**
- Background dark teal gradiente
- Border radius 24px
- Padding 24px
- Gráfico de barras minimalista
- Grid de ícones 12px cada
- Contraste forte branco/amarelo no dark

---

## 🎭 Padrões de Design

### **Typography System:**
```css
/* Títulos */
h1: 48px, font-weight: 900, line-height: 1.1
h2: 32px, font-weight: 800, line-height: 1.2
h3: 24px, font-weight: 700, line-height: 1.3

/* Body */
body: 16px, font-weight: 400, line-height: 1.6
small: 14px, font-weight: 500, line-height: 1.4
caption: 12px, font-weight: 600, line-height: 1.2

/* Font Family */
font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
```

### **Shadows & Elevation:**
```css
/* Elevation 1 - Cards */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

/* Elevation 2 - Floating elements */
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);

/* Elevation 3 - Modals */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.16);
```

### **Border Radius System:**
```css
--radius-sm: 8px;   /* Badges, small buttons */
--radius-md: 16px;  /* Input fields, medium cards */
--radius-lg: 24px;  /* Large cards, containers */
--radius-xl: 32px;  /* Hero sections */
--radius-full: 9999px; /* Avatars, pills */
```

---

## 🔄 Animações & Interações

### **Micro-interactions:**
1. **Hover states:** Scale 1.02, shadow increase
2. **Active states:** Scale 0.98, opacity 0.9
3. **Loading:** Skeleton shimmer effect
4. **Transitions:** 200ms ease-in-out

### **Elementos Animados:**
- Waveform audio (1h/4h card)
- Progress bars (fill animation)
- Water level (liquid animation)
- Play button (pulse effect)

---

## 📱 Responsividade

### **Breakpoints:**
```css
mobile: < 640px
tablet: 640px - 1024px
desktop: > 1024px
```

### **Layout Mobile:**
- Sidebar vira bottom navigation
- Cards empilham verticalmente
- Overview card simplificado
- Slider de drinks fica horizontal scroll

---

## 🎯 Características-Chave para Implementação

### **1. Visual Hierarchy**
- Títulos grandes com highlight amarelo neon
- Contraste forte entre elementos
- Uso de whitespace generoso
- Ilustrações como focal points

### **2. Color Usage**
- Amarelo neon para CTAs e destaques
- Teal para dados e gráficos
- Branco para leitura confortável
- Sombras sutis para profundidade

### **3. Data Visualization**
- Barras verticais minimalistas
- Progress circles com percentuais
- Icon grids para histórico
- Line charts para tendências

### **4. Component Patterns**
- Glass cards com shadow
- Rounded corners everywhere
- Icon + text combinations
- Nested mini-cards dentro de hero cards

---

## 💡 Insights de UX

1. **Gamification:** Contadores, metas, progresso visual
2. **Personalização:** Seletor de bebidas customizável
3. **Feedback visual:** Cores indicam status (verde = ok, amarelo = atenção)
4. **Hierarquia clara:** Informação mais importante em destaque
5. **Scanning pattern:** F-pattern com hero card à esquerda

---

## 🛠️ Stack de Implementação Sugerido

### **Framework:**
- React 18+ com TypeScript
- Tailwind CSS para styling
- Framer Motion para animações
- Recharts para gráficos

### **Componentes Necessários:**
```typescript
// Core Components
- Card (com variantes: hero, compact, dark)
- Button (variantes: primary, outline, icon)
- Avatar (com status indicator)
- Badge (status, category)
- ProgressBar (linear, circular, arc)

// Data Viz Components
- BarChart (vertical mini bars)
- LineChart (trend lines)
- IconGrid (status grid)
- Slider (range selector)

// Layout Components
- Sidebar (vertical navigation)
- Header (branding + user)
- Grid (responsive 2-col)
- Container (max-width wrapper)
```

---

## 🎨 CSS Custom Properties

```css
:root {
  /* Colors */
  --color-neon-yellow: #CAFF00;
  --color-deep-teal: #1A5F7A;
  --color-dark-teal: #0D3D4F;
  --color-light-gray: #E8EEF2;
  
  /* Spacing */
  --space-unit: 8px;
  --space-xs: calc(var(--space-unit) * 0.5);
  --space-sm: var(--space-unit);
  --space-md: calc(var(--space-unit) * 2);
  --space-lg: calc(var(--space-unit) * 3);
  --space-xl: calc(var(--space-unit) * 4);
  
  /* Typography */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;
  --font-size-4xl: 3rem;
  
  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.16);
  
  /* Radius */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --radius-full: 9999px;
  
  /* Transitions */
  --transition-fast: 150ms ease-in-out;
  --transition-base: 200ms ease-in-out;
  --transition-slow: 300ms ease-in-out;
}
```

---

## 📋 Checklist de Implementação

### **Fase 1: Fundação**
- [ ] Setup de cores no Tailwind config
- [ ] Tipografia e font system
- [ ] Grid e spacing system
- [ ] Shadow e border radius tokens

### **Fase 2: Componentes Base**
- [ ] Card component (3 variantes)
- [ ] Button component
- [ ] Avatar component
- [ ] Badge component
- [ ] Icon system

### **Fase 3: Componentes de Dados**
- [ ] ProgressBar (linear + circular)
- [ ] BarChart mini
- [ ] LineChart
- [ ] IconGrid
- [ ] Slider/Range selector

### **Fase 4: Layout**
- [ ] Sidebar navigation
- [ ] Header com branding
- [ ] Dashboard grid
- [ ] Responsive breakpoints

### **Fase 5: Páginas**
- [ ] Dashboard overview
- [ ] Drink selector
- [ ] Statistics view
- [ ] User profile

### **Fase 6: Polimento**
- [ ] Micro-animations
- [ ] Hover states
- [ ] Loading states
- [ ] Empty states
- [ ] Error handling

---

## 🎯 Aplicação ao Projeto TB Personal OS

### **Adaptações Necessárias:**

1. **Substituir tema de hidratação por produtividade:**
   - Água → Tarefas completadas
   - Copos → Tasks/Goals
   - Tempo de hidratação → Tempo focado
   - Meta diária → Daily goals

2. **Manter padrões visuais:**
   - Cards brancos com shadow
   - Neon yellow para CTAs
   - Dark teal para gráficos
   - Light gray background
   - Sidebar vertical

3. **Componentes reutilizáveis:**
   - Hero card "Overview" → Task Overview
   - Selector card → Mode Selector / Quick Actions
   - Statistic card → Productivity Chart
   - Mini progress cards → Daily metrics

4. **Elementos únicos a implementar:**
   - Ilustração personalizada (pessoa → produtividade)
   - Waveform card → Pomodoro timer ou Focus sessions
   - Icon grid → Task completion history
   - Calendar widget → Agenda integration

---

## 🚀 Próximos Passos

1. ✅ Criar paleta de cores no Tailwind
2. ✅ Estruturar componentes base
3. ⏳ Implementar Dashboard overview
4. ⏳ Adicionar data visualization
5. ⏳ Polir animações e interações
6. ⏳ Testar responsividade
7. ⏳ Refinar acessibilidade

---

**Última atualização:** 25/01/2026  
**Versão:** 1.0  
**Autor:** TB Personal OS Development Team
