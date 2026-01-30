-- Migration: Add Multi-User Support and Onboarding System
-- Date: 2026-01-24
-- Description: Adiciona suporte para múltiplos usuários com quiz de onboarding e API keys personalizadas

-- =============================================
-- 1. ADICIONAR CAMPOS DE PERSONALIZAÇÃO AO PROFILE
-- =============================================

-- Adicionar campos para onboarding e personalização
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS gemini_api_key TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 0;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS quiz_answers JSONB DEFAULT '{}'::jsonb;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS personality_profile JSONB DEFAULT '{}'::jsonb;

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_profiles_onboarding_step ON profiles(onboarding_step);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

-- =============================================
-- 2. CRIAR TABELA DE QUIZ DE ONBOARDING
-- =============================================

CREATE TABLE IF NOT EXISTS onboarding_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_order INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL, -- 'single', 'multiple', 'text', 'scale'
    options JSONB, -- Para questões com opções predefinidas
    category TEXT, -- 'personality', 'goals', 'preferences', 'context'
    required BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- 3. CRIAR TABELA DE RESPOSTAS DO QUIZ
-- =============================================

CREATE TABLE IF NOT EXISTS onboarding_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES onboarding_questions(id) ON DELETE CASCADE,
    response JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_responses_user ON onboarding_responses(user_id);

-- =============================================
-- 4. INSERIR PERGUNTAS DO QUIZ INICIAL
-- =============================================

INSERT INTO onboarding_questions (question_order, question_text, question_type, options, category) VALUES
-- Pergunta 1: Objetivo Principal
(1, 
 'Qual seu principal objetivo ao usar este assistente?',
 'single',
 '{
   "options": [
     {"value": "productivity", "label": "📊 Aumentar produtividade"},
     {"value": "organization", "label": "📁 Organizar vida pessoal"},
     {"value": "health", "label": "💪 Melhorar saúde e bem-estar"},
     {"value": "learning", "label": "📚 Aprender e crescer"},
     {"value": "business", "label": "💼 Gerenciar negócios"},
     {"value": "multiple", "label": "🎯 Múltiplos objetivos"}
   ]
 }'::jsonb,
 'goals'),

-- Pergunta 2: Estilo de Comunicação
(2,
 'Como você prefere que eu me comunique?',
 'single',
 '{
   "options": [
     {"value": "direct", "label": "💬 Direto e objetivo"},
     {"value": "friendly", "label": "😊 Amigável e casual"},
     {"value": "professional", "label": "👔 Formal e profissional"},
     {"value": "motivational", "label": "🚀 Motivador e energético"}
   ]
 }'::jsonb,
 'personality'),

-- Pergunta 3: Nível de Autonomia
(3,
 'Quanto de autonomia você quer me dar?',
 'single',
 '{
   "options": [
     {"value": "suggest", "label": "💡 Apenas sugerir (eu decido tudo)"},
     {"value": "confirm", "label": "✓ Sugerir e pedir confirmação"},
     {"value": "auto", "label": "🤖 Executar automaticamente"}
   ]
 }'::jsonb,
 'preferences'),

-- Pergunta 4: Áreas de Foco
(4,
 'Quais áreas você quer que eu te ajude? (múltiplas)',
 'multiple',
 '{
   "options": [
     {"value": "tasks", "label": "✅ Tarefas e projetos"},
     {"value": "calendar", "label": "📅 Calendário e agenda"},
     {"value": "finance", "label": "💰 Finanças pessoais"},
     {"value": "health", "label": "🏃 Saúde e exercícios"},
     {"value": "content", "label": "📱 Criação de conteúdo"},
     {"value": "learning", "label": "📖 Aprendizado"},
     {"value": "habits", "label": "🎯 Hábitos e rotinas"}
   ]
 }'::jsonb,
 'goals'),

-- Pergunta 5: Horário Preferido
(5,
 'Em que horário você é mais ativo?',
 'single',
 '{
   "options": [
     {"value": "morning", "label": "🌅 Manhã (6h-12h)"},
     {"value": "afternoon", "label": "☀️ Tarde (12h-18h)"},
     {"value": "evening", "label": "🌆 Noite (18h-23h)"},
     {"value": "night", "label": "🌙 Madrugada (23h-6h)"},
     {"value": "flexible", "label": "🔄 Varia muito"}
   ]
 }'::jsonb,
 'context'),

-- Pergunta 6: Chave API Gemini
(6,
 'Cole sua chave API do Google Gemini (opcional - você pode usar a padrão):',
 'text',
 '{
   "placeholder": "AIzaSy...",
   "help_text": "Obtenha em: https://makersuite.google.com/app/apikey",
   "optional": true
 }'::jsonb,
 'preferences'),

-- Pergunta 7: Nome
(7,
 'Como prefere ser chamado?',
 'text',
 '{
   "placeholder": "Digite seu nome ou apelido"
 }'::jsonb,
 'personality')
ON CONFLICT DO NOTHING;

-- =============================================
-- 5. CRIAR FUNÇÃO PARA PROCESSAR QUIZ
-- =============================================

CREATE OR REPLACE FUNCTION process_onboarding_quiz(
    p_user_id UUID,
    p_quiz_answers JSONB
) RETURNS JSONB AS $$
DECLARE
    v_profile_data JSONB;
    v_personality_profile JSONB;
BEGIN
    -- Extrair dados do quiz para profile
    v_personality_profile := jsonb_build_object(
        'communication_style', p_quiz_answers->'question_2'->>'value',
        'autonomy_level', p_quiz_answers->'question_3'->>'value',
        'focus_areas', p_quiz_answers->'question_4',
        'active_hours', p_quiz_answers->'question_5'->>'value',
        'main_goal', p_quiz_answers->'question_1'->>'value'
    );
    
    -- Atualizar profile
    UPDATE profiles
    SET 
        quiz_answers = p_quiz_answers,
        personality_profile = v_personality_profile,
        onboarding_completed = true,
        onboarded_at = NOW(),
        autonomy_level = COALESCE(p_quiz_answers->'question_3'->>'value', 'confirm'),
        gemini_api_key = NULLIF(p_quiz_answers->'question_6'->>'value', '')
    WHERE user_id = p_user_id;
    
    RETURN v_personality_profile;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 6. ATUALIZAR PROFILES EXISTENTES
-- =============================================

-- Marcar perfil do Igor como onboarding completo
UPDATE profiles 
SET 
    onboarding_completed = true,
    onboarded_at = NOW(),
    personality_profile = '{
        "communication_style": "friendly",
        "autonomy_level": "confirm",
        "focus_areas": ["tasks", "calendar", "finance", "health", "content"],
        "active_hours": "flexible",
        "main_goal": "multiple"
    }'::jsonb
WHERE onboarding_completed = false;

-- =============================================
-- 7. POLÍTICAS DE SEGURANÇA (RLS)
-- =============================================

-- Habilitar RLS
ALTER TABLE onboarding_responses ENABLE ROW LEVEL SECURITY;

-- Política: usuários só veem suas próprias respostas
CREATE POLICY "Users can view own responses" ON onboarding_responses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own responses" ON onboarding_responses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- =============================================
-- 8. COMENTÁRIOS E DOCUMENTAÇÃO
-- =============================================

COMMENT ON TABLE onboarding_questions IS 'Perguntas do quiz de onboarding para novos usuários';
COMMENT ON TABLE onboarding_responses IS 'Respostas dos usuários ao quiz de onboarding';
COMMENT ON COLUMN profiles.gemini_api_key IS 'Chave API personalizada do Gemini para o usuário';
COMMENT ON COLUMN profiles.personality_profile IS 'Perfil de personalidade baseado no quiz';
COMMENT ON COLUMN profiles.quiz_answers IS 'Respostas brutas do quiz de onboarding';
