#!/bin/bash
# Script para aplicar migration de tipos de check-in
# Execute este script manualmente quando necessário

echo "🔄 Aplicando migração: adicionar tipos 'focus' e 'nutrition'"
echo ""
echo "📝 Execute o seguinte SQL no Supabase Dashboard > SQL Editor:"
echo "   https://supabase.com/dashboard/project/lbxsqyzjtjqtfclagddd/sql"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'SQL'
-- Migration 00010: Adicionar tipos focus e nutrition

ALTER TABLE checkins DROP CONSTRAINT IF EXISTS checkins_checkin_type_check;

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

CREATE INDEX IF NOT EXISTS idx_checkins_type_created 
  ON checkins(checkin_type, created_at DESC);

-- Verificar tipos válidos
SELECT 
  constraint_name, 
  check_clause 
FROM information_schema.check_constraints 
WHERE constraint_name = 'checkins_checkin_type_check';
SQL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Após executar, os novos tipos estarão disponíveis!"
