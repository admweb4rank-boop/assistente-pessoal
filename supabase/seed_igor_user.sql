-- Criar usuário Igor no Supabase
-- Execute este SQL no Supabase SQL Editor

-- Criar usuário principal
INSERT INTO users (id, email, full_name, avatar_url)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'igor@tbpersonal.os',
    'Igor Bessa',
    NULL
)
ON CONFLICT (id) DO NOTHING;

-- Criar profile
INSERT INTO profiles (
    user_id,
    timezone,
    language,
    notify_morning_summary,
    notify_night_summary,
    morning_summary_time,
    night_summary_time,
    autonomy_level,
    goals,
    principles,
    onboarding_completed,
    onboarded_at
)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'America/Sao_Paulo',
    'pt-BR',
    true,
    true,
    '07:00',
    '21:00',
    'confirm',
    '["Crescer o negócio de Personal OS em 2026", "Manter saúde e energia alta", "Produzir conteúdo de valor regularmente"]'::jsonb,
    '["Agir com integridade", "Priorizar saúde", "Buscar excelência"]'::jsonb,
    true,
    NOW()
)
ON CONFLICT (user_id) DO NOTHING;

-- Criar chat do Telegram
INSERT INTO telegram_chats (
    user_id,
    chat_id,
    username,
    first_name,
    last_name,
    is_active
)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    8225491023,
    'Igor',
    'Igor',
    'Bessa',
    true
)
ON CONFLICT (chat_id) DO NOTHING;

-- Verificar criação
SELECT 
    u.id,
    u.email,
    u.full_name,
    p.timezone,
    tc.chat_id,
    tc.username
FROM users u
LEFT JOIN profiles p ON u.id = p.user_id
LEFT JOIN telegram_chats tc ON u.id = tc.user_id
WHERE u.email = 'igor@tbpersonal.os';
