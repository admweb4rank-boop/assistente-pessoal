# Design System V2 - BESSA.OS
## Inspirado em Easy·A, Fitness Apps e padrões modernos

---

## 📊 ANÁLISE DAS REFERÊNCIAS

### Easy·A (Web3 Learning)
- **Background**: #0A0B0E (quase preto) com noise texture
- **Primary**: Purple (#8B5CF6, #A78BFA, #C084FC)
- **Accent**: Green (#10B981, #34D399) para CTAs principais
- **Glassmorphism**: backdrop-blur-xl, borders rgba(255,255,255,0.1)
- **Typography**: Inter/DM Sans, hierarchy forte
- **Rounded Corners**: 16-24px
- **Glow Effects**: Neon purple/green em elementos importantes
- **3D Elements**: Floating cards, NFT icons com depth
- **Stats Display**: Números grandes (48-72px), bold

### Fitness App (Dark + Lime)
- **Background**: Pure black (#000000)
- **Accent**: Lime yellow (#CAFF00, #D4FF00) - vibrante
- **Progress**: Circular gauges, arc charts
- **Images**: Hero images grandes, high contrast
- **Cards**: Grid 2-col, rounded 24px+
- **Bottom Nav**: Fixed, com accent color
- **Typography**: Stats em destaque, bold numbers

### HR/Hiring App
- **Soft UI**: Beige/cream backgrounds
- **Pastels**: Multi-color progress bars
- **Avatar-first**: Photos em destaque
- **Clean**: Minimal, whitespace generoso

---

## 🎨 DESIGN TOKENS V2

### Colors (Enhanced)
```js
colors: {
  // Base (mais escuro)
  dark: {
    bg: {
      primary: '#0A0B0E',      // Quase preto (Easy·A)
      secondary: '#13141A',     // Cards level 1
      tertiary: '#1A1B23',      // Cards level 2
      elevated: '#22232E',      // Hover states
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#A3A3B8',
      tertiary: '#6B6B80',
      disabled: '#4A4A5C',
    },
    border: 'rgba(255, 255, 255, 0.08)',
    borderHover: 'rgba(255, 255, 255, 0.15)',
  },
  
  // Brand (purple spectrum)
  brand: {
    purple: {
      50: '#FAF5FF',
      100: '#F3E8FF',
      200: '#E9D5FF',
      300: '#D8B4FE',
      400: '#C084FC',
      500: '#A855F7',  // Primary
      600: '#9333EA',
      700: '#7E22CE',
      800: '#6B21A8',
      900: '#581C87',
    },
  },
  
  // Accent colors
  accent: {
    green: {
      400: '#34D399',
      500: '#10B981',  // Success/CTA
      600: '#059669',
    },
    lime: {
      400: '#D4FF00',  // Vibrant accent
      500: '#CAFF00',
      600: '#B8E600',
    },
    blue: {
      400: '#60A5FA',
      500: '#3B82F6',
      600: '#2563EB',
    },
    pink: {
      400: '#F472B6',
      500: '#EC4899',
      600: '#DB2777',
    },
    yellow: {
      400: '#FBBF24',
      500: '#F59E0B',
      600: '#D97706',
    },
    red: {
      400: '#F87171',
      500: '#EF4444',
      600: '#DC2626',
    },
  },
  
  // Gradients
  gradients: {
    purpleBlue: 'linear-gradient(135deg, #A855F7 0%, #3B82F6 100%)',
    purpleGreen: 'linear-gradient(135deg, #A855F7 0%, #10B981 100%)',
    purplePink: 'linear-gradient(135deg, #A855F7 0%, #EC4899 100%)',
    greenBlue: 'linear-gradient(135deg, #10B981 0%, #3B82F6 100%)',
    darkPurple: 'linear-gradient(135deg, #1A1B23 0%, #2D1B69 100%)',
  },
}
```

### Typography (Enhanced)
```js
fontSize: {
  // Display sizes (para hero numbers)
  'display-2xl': ['72px', { lineHeight: '90px', fontWeight: '700' }],
  'display-xl': ['60px', { lineHeight: '72px', fontWeight: '700' }],
  'display-lg': ['48px', { lineHeight: '60px', fontWeight: '700' }],
  
  // Standard sizes
  '3xl': ['30px', { lineHeight: '36px', fontWeight: '700' }],
  '2xl': ['24px', { lineHeight: '32px', fontWeight: '600' }],
  'xl': ['20px', { lineHeight: '28px', fontWeight: '600' }],
  'lg': ['18px', { lineHeight: '28px', fontWeight: '500' }],
  'base': ['16px', { lineHeight: '24px', fontWeight: '400' }],
  'sm': ['14px', { lineHeight: '20px', fontWeight: '400' }],
  'xs': ['12px', { lineHeight: '16px', fontWeight: '400' }],
}
```

### Spacing (Enhanced)
```js
spacing: {
  '0': '0px',
  '1': '4px',
  '2': '8px',
  '3': '12px',
  '4': '16px',
  '5': '20px',
  '6': '24px',
  '8': '32px',
  '10': '40px',
  '12': '48px',
  '16': '64px',
  '20': '80px',
  '24': '96px',
  '32': '128px',
}
```

### Border Radius (Enhanced)
```js
borderRadius: {
  'none': '0',
  'sm': '8px',
  'md': '12px',
  'lg': '16px',
  'xl': '20px',
  '2xl': '24px',
  '3xl': '32px',
  'full': '9999px',
}
```

### Shadows & Glows
```js
boxShadow: {
  // Glass shadows
  'glass-sm': '0 2px 8px rgba(0, 0, 0, 0.4)',
  'glass': '0 4px 16px rgba(0, 0, 0, 0.5)',
  'glass-lg': '0 8px 32px rgba(0, 0, 0, 0.6)',
  
  // Neon glows
  'glow-purple': '0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(168, 85, 247, 0.2)',
  'glow-green': '0 0 20px rgba(16, 185, 129, 0.4), 0 0 40px rgba(16, 185, 129, 0.2)',
  'glow-lime': '0 0 20px rgba(202, 255, 0, 0.4), 0 0 40px rgba(202, 255, 0, 0.2)',
  'glow-blue': '0 0 20px rgba(59, 130, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.2)',
  'glow-pink': '0 0 20px rgba(236, 72, 153, 0.4), 0 0 40px rgba(236, 72, 153, 0.2)',
}
```

### Animations (Enhanced)
```js
animation: {
  'float': 'float 6s ease-in-out infinite',
  'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
  'slide-up': 'slide-up 0.5s ease-out',
  'slide-down': 'slide-down 0.5s ease-out',
  'slide-left': 'slide-left 0.5s ease-out',
  'slide-right': 'slide-right 0.5s ease-out',
  'fade-in': 'fade-in 0.6s ease-out',
  'scale-in': 'scale-in 0.4s ease-out',
  'shimmer': 'shimmer 2s linear infinite',
  'spin-slow': 'spin 3s linear infinite',
}

keyframes: {
  'glow-pulse': {
    '0%, 100%': { opacity: '1' },
    '50%': { opacity: '0.5' },
  },
  'shimmer': {
    '0%': { backgroundPosition: '-1000px 0' },
    '100%': { backgroundPosition: '1000px 0' },
  },
}
```

---

## 🧩 COMPONENTES V2

### 1. GlassCard Enhanced
```tsx
- backdrop-blur-2xl (mais forte)
- border: 1px solid rgba(255,255,255,0.1)
- shadow-glass-lg
- rounded-2xl (24px)
- hover: border-color glow effect
- props: variant (default, elevated, neon)
```

### 2. StatCard (Novo - Easy·A style)
```tsx
- Número grande (display-lg, 48-72px)
- Label pequeno (text-xs, secondary)
- Icon com gradient background
- Trend indicator (+/- com seta)
- Glow effect opcional
- Animated number counting
```

### 3. ProgressCard (Novo - Fitness style)
```tsx
- Circular progress gauge
- Arc progress (semicírculo)
- Linear progress bar com gradient
- Número central grande
- Label + sublabel
- Color variants (purple, green, lime, blue)
```

### 4. Button V2
```tsx
Variants:
- primary: gradient purple→green, glow-purple
- secondary: glass com border
- accent: lime/green solid, glow-green
- ghost: transparent com hover glow
- danger: red solid
- outline: border 2px com glow no hover

Sizes:
- xs: px-3 py-1.5 text-xs
- sm: px-4 py-2 text-sm
- md: px-6 py-3 text-base (default)
- lg: px-8 py-4 text-lg
- xl: px-10 py-5 text-xl

States:
- hover: scale-105, brightness-110, glow increase
- active: scale-95
- disabled: opacity-40
- loading: shimmer animation
```

### 5. Badge V2
```tsx
Variants:
- purple, green, lime, blue, pink, yellow, red
- default, outlined, gradient

Sizes:
- sm: px-2 py-0.5 text-xs rounded-md
- md: px-3 py-1 text-sm rounded-lg
- lg: px-4 py-1.5 text-base rounded-xl

Features:
- dot indicator opcional
- icon left/right
- close button
- glow effect
```

### 6. Avatar Enhanced
```tsx
- Gradient border (purple ring)
- Status indicator (online, offline, busy)
- Hover: scale + glow
- Sizes: xs(24px), sm(32px), md(40px), lg(56px), xl(80px), 2xl(120px)
- Fallback com initials + gradient bg
```

### 7. BottomNav (Novo - Mobile)
```tsx
- Fixed bottom, glassmorphism
- 4-5 items max
- Active: glow + icon scale
- Smooth transitions
- Safe area inset
```

### 8. Hero Card (Novo - Easy·A style)
```tsx
- Large gradient background
- Floating 3D elements (icons, shapes)
- Hero text (display-2xl)
- CTA button prominent
- Particles/noise texture
```

### 9. Timeline/Feed Card
```tsx
- Avatar + content
- Timestamp subtle
- Actions (like, comment)
- Glass background
- Hover: elevation increase
```

### 10. Modal V2
```tsx
- Backdrop blur-2xl
- Glass card central
- Slide-up animation
- Header com gradient border
- Footer fixed
- Overlay dimmed
```

---

## 📱 LAYOUT PATTERNS

### Dashboard Layout
```
┌─────────────────────────────────────┐
│ Header (glass, fixed)               │
├─────────────────────────────────────┤
│ Hero Card (gradient, stats)         │
├─────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│ │Stat 1│ │Stat 2│ │Stat 3│ │Stat 4││ Stats Grid
│ └──────┘ └──────┘ └──────┘ └──────┘│
├─────────────────────────────────────┤
│ ┌────────────┐  ┌─────────────────┐│
│ │ Chart Card │  │  Quick Actions  ││ 2-column
│ │            │  │                 ││
│ └────────────┘  └─────────────────┘│
├─────────────────────────────────────┤
│ Recent Activity Feed                │
└─────────────────────────────────────┘
```

### Tasks/List Layout
```
┌─────────────────────────────────────┐
│ Header + Search + Filter            │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Overdue (red glow)              │ │ Section 1
│ │  → Task 1                       │ │
│ │  → Task 2                       │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Today (green glow)              │ │ Section 2
│ │  → Task 3                       │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 🎯 PLANO DE IMPLEMENTAÇÃO

### Fase 1: Foundation (Tokens & Base Components)
1. **Atualizar Tailwind Config**
   - Cores V2
   - Typography display sizes
   - Shadows & glows
   - Animations

2. **Atualizar Global CSS**
   - Noise texture background
   - Enhanced glassmorphism
   - Glow utilities
   - Animation classes

3. **Atualizar Componentes Base**
   - GlassCard V2
   - Button V2
   - Badge V2
   - Avatar Enhanced

4. **Criar Novos Componentes**
   - StatCard
   - ProgressCard
   - HeroCard
   - BottomNav

### Fase 2: Pages (Implementação Página por Página)

#### 2.1 LoginPage ⭐
- Hero section com gradient + 3D elements
- Glass login card central
- Button accent lime/green
- Animated background

#### 2.2 DashboardPage ⭐⭐
- Hero stats card com números grandes
- Grid 4-col de StatCards
- Quick actions com icons
- Recent activity timeline
- Bottom nav (mobile)

#### 2.3 TasksPage ⭐⭐
- Sections com glow colors (red/yellow/green)
- Task cards glassmorphism
- Progress indicators
- Checkbox custom com animation

#### 2.4 ChatPage ⭐
- Messages glassmorphism
- Avatar com gradient border
- Input com glass background
- Typing indicator animated

#### 2.5 HealthPage ⭐⭐⭐
- Circular progress gauges (Easy·A style)
- Stats grid com números grandes
- Charts com gradients
- Streak card com fire emoji

#### 2.6 InboxPage ⭐
- Stats cards com icons gradient
- Items list glassmorphism
- Badges coloridos
- Actions com hover glow

#### 2.7 Outras Páginas ⭐
- InsightsPage: Charts + AI cards
- ProjectsPage: Kanban board glass
- CalendarPage: Events com colors
- SettingsPage: Sections + toggles

### Fase 3: Polish & Testing
- Micro-interactions
- Loading states
- Empty states
- Error states
- Responsive ajustes
- Performance optimization

---

## 🚀 PRIORIDADE DE EXECUÇÃO

1. **CRÍTICO** (Fazer agora):
   - Tailwind config V2
   - Global CSS V2
   - GlassCard, Button, Badge V2
   - LoginPage V2
   - DashboardPage V2

2. **ALTO** (Logo depois):
   - StatCard, ProgressCard
   - TasksPage V2
   - HealthPage V2
   - ChatPage V2

3. **MÉDIO** (Quando possível):
   - InboxPage V2
   - Outras páginas
   - Micro-interactions
   - Empty states

4. **BAIXO** (Nice to have):
   - Advanced animations
   - 3D elements
   - Particles effects
   - Easter eggs
