# Design System - TB Personal OS

## 🎨 Visão Geral

Design system premium inspirado em Easy·A com tema dark, gradientes vibrantes e elementos glassmorphism.

## 🎭 Paleta de Cores

### Dark Background
- **Primary**: `#0A0B0E` - Background principal
- **Secondary**: `#12141A` - Background secundário
- **Tertiary**: `#1A1D26` - Background terciário
- **Card**: `#1E2129` - Background de cards

### Brand Colors
#### Purple Gradient
- `50`: `#F5F3FF`
- `500`: `#8B5CF6` (Principal)
- `600`: `#7C3AED`
- `700`: `#6D28D9`

#### Blue Gradient
- `50`: `#EFF6FF`
- `500`: `#3B82F6` (Principal)
- `600`: `#2563EB`

### Accent Colors
- **Green**: `#00E676` - Success, positive trends
- **Cyan**: `#00E5FF` - Information
- **Pink**: `#FF4081` - Alerts, important
- **Orange**: `#FF9100` - Warnings

## 🧩 Componentes

### GlassCard
Card com efeito glassmorphism.

```tsx
import { GlassCard } from '@/components/ui';

<GlassCard hover>
  <p>Conteúdo</p>
</GlassCard>
```

**Props:**
- `hover?: boolean` - Adiciona efeito hover
- `className?: string` - Classes adicionais
- `onClick?: () => void` - Handler de clique

### Button
Botão com 3 variantes.

```tsx
<Button variant="gradient" size="lg">
  Click me
</Button>
```

**Variants:**
- `gradient` - Gradiente roxo/azul (padrão)
- `outline` - Bordado transparente
- `ghost` - Sem background

**Sizes:**
- `sm` - Pequeno
- `md` - Médio (padrão)
- `lg` - Grande

### StatCard
Card para exibir estatísticas.

```tsx
<StatCard
  label="Tarefas Hoje"
  value={12}
  icon={<CheckSquare />}
  trend={{ value: "+5", positive: true }}
/>
```

### Badge
Badge para tags e labels.

```tsx
<Badge variant="purple">New</Badge>
```

**Variants:**
- `purple` - Roxo (padrão)
- `green` - Verde
- `blue` - Azul
- `pink` - Rosa

### Input
Input com efeito glass.

```tsx
<Input
  placeholder="Digite algo..."
  icon={<Search />}
/>
```

## 🎬 Animações

### Pré-definidas
- `animate-float` - Flutuação suave
- `animate-glow` - Brilho pulsante
- `animate-slide-up` - Desliza de baixo
- `animate-slide-down` - Desliza de cima
- `animate-fade-in` - Fade in
- `animate-scale-in` - Escala com fade

### Delays
Use `style={{ animationDelay: '0.1s' }}` para sequenciar animações.

## 🎨 Classes Utilitárias

### Glass Effect
```css
.glass-card /* Card com glassmorphism */
.glass-card-hover /* Com hover effect */
```

### Gradient Text
```css
.text-gradient /* Gradiente roxo/azul */
.text-gradient-green /* Gradiente verde */
```

### Backgrounds
```css
.bg-animated /* Background com efeito mesh gradient */
.bg-gradient-purple
.bg-gradient-blue
.bg-gradient-green
```

### Shadows
```css
.shadow-glass /* Sombra para glass */
.shadow-glow-purple /* Brilho roxo */
.shadow-glow-blue /* Brilho azul */
.shadow-glow-green /* Brilho verde */
.shadow-card /* Sombra de card */
.shadow-card-hover /* Sombra de card hover */
```

### Custom Scrollbar
```css
.custom-scrollbar /* Scrollbar estilizada */
```

## 📐 Layout

### Card Grid
```tsx
<div className="card-grid">
  {/* Responsivo: 1 col mobile, 2 col tablet, 3 col desktop */}
</div>
```

### Section Heading
```tsx
<h2 className="section-heading">
  Título da Seção
</h2>
```

## 🌈 Gradientes

### Uso em Tailwind
```tsx
<div className="bg-gradient-to-br from-brand-purple-500 to-brand-blue-500">
  Conteúdo
</div>
```

### Gradientes Pré-definidos
- `from-brand-purple-500 to-brand-blue-500` - Roxo → Azul
- `from-brand-blue-500 to-accent-cyan` - Azul → Ciano
- `from-accent-green to-accent-cyan` - Verde → Ciano
- `from-accent-pink to-accent-orange` - Rosa → Laranja

## 💡 Best Practices

### 1. Hierarquia Visual
- Use `text-gradient` para títulos principais
- `text-white` para texto primário
- `text-dark-text-secondary` para texto secundário
- `text-dark-text-tertiary` para texto terciário

### 2. Espaçamento
- Use `gap-6` para grids
- Use `p-6` ou `p-8` para padding de cards
- Use `mb-6` ou `mb-12` para margens de seções

### 3. Animações
- Aplique animações com `animate-*`
- Use delays para criar sequências
- Mantenha transições suaves com `transition-all duration-300`

### 4. Glassmorphism
- Use `GlassCard` para containers principais
- Combine com `backdrop-blur-xl` quando necessário
- Adicione bordas sutis com `border-dark-border`

### 5. Responsividade
- Mobile first: design para mobile primeiro
- Use breakpoints: `md:` (tablet), `lg:` (desktop)
- Teste em diferentes tamanhos

## 🚀 Páginas de Exemplo

### Landing Page
`/src/pages/LandingPage.tsx` - Página inicial premium com hero section, features e CTA.

### Dashboard Enhanced
`/src/pages/DashboardPageEnhanced.tsx` - Dashboard com stats cards, quick actions e glassmorphism.

## 🔧 Configuração

### Tailwind Config
Todas as cores e configurações estão em `/frontend/tailwind.config.js`.

### Global Styles
Estilos globais e classes utilitárias em `/frontend/src/index.css`.

## 📱 Preview

Para ver o design system em ação:
1. `cd frontend`
2. `npm run dev`
3. Acesse `http://localhost:5173`

---

**Criado com** 💜 **para TB Personal OS**
