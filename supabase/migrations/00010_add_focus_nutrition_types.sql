-- Migration: Adicionar tipos 'focus' e 'nutrition' aos check-ins
-- Data: 2026-01-27
-- Descrição: Expande os tipos válidos de check-ins para incluir foco e nutrição

-- Remover constraint antigo
ALTER TABLE checkins DROP CONSTRAINT IF EXISTS checkins_checkin_type_check;

-- Adicionar novo constraint com todos os tipos
ALTER TABLE checkins
  ADD CONSTRAINT checkins_checkin_type_check 
  CHECK (checkin_type IN (
    'energy',
    'mood',
    'sleep',
    'workout',
    'focus',
    'nutrition',
    'habit',
    'custom'
  ));

-- Adicionar comentário explicativo
COMMENT ON COLUMN checkins.checkin_type IS 'Tipo de check-in: energy, mood, sleep, workout, focus, nutrition, habit, custom';

-- Criar índice para melhorar performance de queries por tipo
CREATE INDEX IF NOT EXISTS idx_checkins_type_created 
  ON checkins(checkin_type, created_at DESC);

-- Comentários sobre os tipos
COMMENT ON TABLE checkins IS '
Check-ins de usuário para rastreamento de métricas de performance.

Tipos suportados:
- energy: Nível de energia (1-10)
- mood: Humor/emocional (emoji + score 1-10)
- sleep: Sono (horas + qualidade 1-10)
- workout: Treino (type, duration, intensity)
- focus: Nível de foco/concentração (1-10)
- nutrition: Nutrição (meal_type, quality 1-10, hydration)
- habit: Hábito personalizado (boolean completed)
- custom: Check-in personalizado pelo usuário
';
