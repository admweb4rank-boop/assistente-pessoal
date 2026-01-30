-- Multi-User Support Schema
-- Execute este SQL no Supabase Dashboard > SQL Editor

-- 1. Adicionar campos para multi-user em profiles
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS gemini_api_key TEXT,
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS onboarded_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS quiz_answers JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS personality_profile JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS autonomy_level TEXT DEFAULT 'confirm';

-- 2. Adicionar campo is_active em users (se não existir)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_profiles_onboarding ON profiles(onboarding_completed);
CREATE INDEX IF NOT EXISTS idx_profiles_gemini_key ON profiles(gemini_api_key) WHERE gemini_api_key IS NOT NULL;

-- 4. Comentários para documentação
COMMENT ON COLUMN profiles.gemini_api_key IS 'Chave API do Google Gemini fornecida pelo usuário (opcional)';
COMMENT ON COLUMN profiles.onboarding_completed IS 'Se o usuário completou o quiz de onboarding';
COMMENT ON COLUMN profiles.onboarding_step IS 'Passo atual do onboarding (0-7)';
COMMENT ON COLUMN profiles.quiz_answers IS 'Respostas do quiz de onboarding em formato JSON';
COMMENT ON COLUMN profiles.personality_profile IS 'Perfil de personalidade gerado a partir do quiz';
COMMENT ON COLUMN profiles.autonomy_level IS 'Nível de autonomia: suggest, confirm, auto';

-- 5. Atualizar usuário existente (Igor) com onboarding completo
UPDATE profiles
SET 
  onboarding_completed = TRUE,
  onboarded_at = NOW(),
  autonomy_level = 'confirm',
  personality_profile = jsonb_build_object(
    'main_goal', 'multiple',
    'communication_style', 'friendly',
    'autonomy_level', 'confirm',
    'focus_areas', to_jsonb(ARRAY['tasks', 'calendar', 'health', 'content']),
    'active_hours', 'flexible'
  )
WHERE user_id = (
  SELECT id FROM users WHERE full_name ILIKE '%Igor%' LIMIT 1
);

-- 6. Verificação final
SELECT 
  'profiles' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'profiles'
  AND column_name IN (
    'gemini_api_key',
    'onboarding_completed',
    'onboarding_step',
    'onboarded_at',
    'quiz_answers',
    'personality_profile',
    'autonomy_level'
  )
ORDER BY column_name;
