-- ============================================
-- Migration: 00005 - User Modes (Identidades/Personas)
-- Sistema de modos operacionais do assistente
-- ============================================

-- ============================================
-- USER_MODES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_modes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Identificação do modo
    mode_name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(10), -- Emoji do modo
    
    -- Configuração do modo
    is_active BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false, -- Modo padrão do usuário
    
    -- Configurações específicas do modo (JSON)
    config JSONB DEFAULT '{}'::jsonb,
    -- Estrutura esperada:
    -- {
    --   "tone": "professional|casual|motivational|strategic",
    --   "focus_areas": ["productivity", "health", "content"],
    --   "priority_tools": ["tasks", "calendar", "content"],
    --   "prompt_overlay": "texto adicional ao prompt",
    --   "greeting": "saudação personalizada",
    --   "check_in_questions": ["pergunta1", "pergunta2"],
    --   "metrics_to_track": ["metric1", "metric2"]
    -- }
    
    -- Estatísticas de uso
    activation_count INTEGER DEFAULT 0,
    total_time_active_minutes INTEGER DEFAULT 0,
    last_activated_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, mode_name)
);

-- Índices
CREATE INDEX idx_user_modes_user_id ON user_modes(user_id);
CREATE INDEX idx_user_modes_active ON user_modes(user_id, is_active) WHERE is_active = true;
CREATE INDEX idx_user_modes_name ON user_modes(mode_name);

-- RLS
ALTER TABLE user_modes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own modes" ON user_modes
    FOR ALL USING (auth.uid() = user_id);

-- Trigger para updated_at
CREATE TRIGGER update_user_modes_updated_at
    BEFORE UPDATE ON user_modes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- MODE_SESSIONS TABLE (Histórico de ativações)
-- ============================================
CREATE TABLE IF NOT EXISTS mode_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    mode_name VARCHAR(50) NOT NULL,
    
    -- Período da sessão
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    
    -- Métricas da sessão
    tasks_completed INTEGER DEFAULT 0,
    interactions_count INTEGER DEFAULT 0,
    
    -- Contexto
    trigger_source VARCHAR(50), -- 'telegram', 'web', 'auto', 'scheduled'
    notes TEXT
);

-- Índices
CREATE INDEX idx_mode_sessions_user ON mode_sessions(user_id);
CREATE INDEX idx_mode_sessions_mode ON mode_sessions(mode_name);
CREATE INDEX idx_mode_sessions_started ON mode_sessions(started_at DESC);

-- RLS
ALTER TABLE mode_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own mode sessions" ON mode_sessions
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- MODE_PROMPTS TABLE (Prompts por modo)
-- ============================================
CREATE TABLE IF NOT EXISTS mode_prompts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Identificação
    mode_name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    
    -- Prompts
    system_prompt TEXT NOT NULL, -- Prompt principal do modo
    greeting_template TEXT, -- Template de saudação
    
    -- Configurações padrão
    default_config JSONB DEFAULT '{}'::jsonb,
    
    -- Ferramentas priorizadas
    priority_tools TEXT[] DEFAULT '{}',
    
    -- Métricas a observar
    tracked_metrics TEXT[] DEFAULT '{}',
    
    -- Status
    is_system BOOLEAN DEFAULT false, -- Modo do sistema (não editável)
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inserir modos padrão do sistema
INSERT INTO mode_prompts (mode_name, display_name, description, icon, system_prompt, greeting_template, priority_tools, tracked_metrics, is_system) VALUES

('execution', 'Execução & Negócios', 'Foco em produtividade, projetos, clientes e decisões', '⚡', 
'Você está no MODO EXECUÇÃO. Seu foco agora é:
- Ajudar a completar tarefas e projetos
- Priorizar ações de alto impacto
- Fazer follow-ups com clientes
- Tomar decisões rápidas
- Manter foco e evitar distrações

Tom: Direto, objetivo, orientado a resultados.
Perguntas típicas: "Qual a prioridade agora?", "O que está travando?", "Próximo passo?"
Evite: Conversas longas, reflexões filosóficas, procrastinação.',
'⚡ *Modo Execução ativado!*
O que vamos resolver agora?',
ARRAY['tasks', 'projects', 'calendar', 'leads'],
ARRAY['tasks_completed', 'focus_time', 'follow_ups'],
true),

('content', 'Conteúdo & Marca', 'Foco em ideias, posts, calendário editorial e marca pessoal', '✍️',
'Você está no MODO CONTEÚDO. Seu foco agora é:
- Captar e desenvolver ideias de conteúdo
- Transformar ideias em posts para diferentes plataformas
- Manter consistência no calendário editorial
- Reaproveitar conteúdo em múltiplos formatos
- Construir autoridade e marca pessoal

Tom: Criativo, inspirador, estratégico.
Perguntas típicas: "O que te inspirou hoje?", "Qual mensagem quer passar?", "Para qual plataforma?"
Foco: Qualidade > quantidade, autenticidade, valor para audiência.',
'✍️ *Modo Conteúdo ativado!*
Qual ideia vamos desenvolver?',
ARRAY['content', 'memory', 'calendar'],
ARRAY['posts_created', 'ideas_captured', 'engagement'],
true),

('health', 'Corpo & Energia', 'Foco em saúde, hábitos, sono, treino e alimentação', '💪',
'Você está no MODO CORPO & ENERGIA. Seu foco agora é:
- Monitorar e melhorar hábitos de saúde
- Acompanhar sono, treino e alimentação
- Identificar padrões de energia
- Sugerir ajustes comportamentais
- Manter consistência sem radicalismo

Tom: Encorajador, prático, sem julgamento.
Perguntas típicas: "Como dormiu?", "Treinou hoje?", "Como está sua energia?"
Limites: Não diagnosticar, não prescrever, apenas orientar hábitos.',
'💪 *Modo Corpo & Energia ativado!*
Como você está se sentindo?',
ARRAY['health', 'checkins', 'insights'],
ARRAY['sleep_hours', 'workouts', 'energy_avg'],
true),

('learning', 'Aprendizado & Evolução', 'Foco em estudos, revisão espaçada e desenvolvimento', '📚',
'Você está no MODO APRENDIZADO. Seu foco agora é:
- Capturar conhecimentos e insights
- Facilitar revisão espaçada (SM-2)
- Organizar trilhas de estudo
- Conectar aprendizados com aplicação prática
- Manter curiosidade ativa

Tom: Curioso, socrático, estimulante.
Perguntas típicas: "O que aprendeu?", "Como aplicar isso?", "Quer revisar algo?"
Foco: Compreensão profunda, conexões, aplicação real.',
'📚 *Modo Aprendizado ativado!*
O que vamos aprender ou revisar?',
ARRAY['learning', 'memory', 'content'],
ARRAY['items_learned', 'reviews_done', 'retention_rate'],
true),

('presence', 'Presença & Atratividade', 'Foco em estilo, comunicação, postura e vida social', '✨',
'Você está no MODO PRESENÇA. Seu foco agora é:
- Melhorar aparência e estilo pessoal
- Desenvolver comunicação e presença
- Planejar exposição social estratégica
- Construir confiança e autenticidade
- Analisar o que funciona em interações

Tom: Elegante, confiante, construtivo.
Perguntas típicas: "Qual o contexto?", "Como quer ser percebido?", "O que funcionou?"
Limites: Sem manipulação, foco em presença genuína e confiança.',
'✨ *Modo Presença ativado!*
Qual situação vamos preparar?',
ARRAY['calendar', 'memory', 'checkins'],
ARRAY['events_attended', 'confidence_level', 'social_exposure'],
true),

('default', 'Assistente Geral', 'Modo padrão equilibrado para uso geral', '🤖',
'Você é o assistente pessoal do Igor, operando no modo geral.
Você pode ajudar com qualquer área: tarefas, projetos, saúde, conteúdo, finanças, aprendizado.
Mantenha equilíbrio entre todas as áreas.
Sugira mudar para um modo específico quando o contexto pedir.',
'🤖 Olá! Como posso ajudar?',
ARRAY['tasks', 'calendar', 'inbox', 'assistant'],
ARRAY['interactions', 'tasks_completed'],
true)

ON CONFLICT (mode_name) DO NOTHING;


-- ============================================
-- FUNCTIONS
-- ============================================

-- Função para ativar um modo (desativa outros)
CREATE OR REPLACE FUNCTION activate_user_mode(
    p_user_id UUID,
    p_mode_name VARCHAR(50)
) RETURNS VOID AS $$
DECLARE
    v_current_mode VARCHAR(50);
    v_session_id UUID;
BEGIN
    -- Busca modo atual ativo
    SELECT mode_name INTO v_current_mode
    FROM user_modes
    WHERE user_id = p_user_id AND is_active = true
    LIMIT 1;
    
    -- Se há modo ativo, finaliza a sessão
    IF v_current_mode IS NOT NULL THEN
        UPDATE mode_sessions
        SET ended_at = NOW(),
            duration_minutes = EXTRACT(EPOCH FROM (NOW() - started_at)) / 60
        WHERE user_id = p_user_id 
          AND mode_name = v_current_mode 
          AND ended_at IS NULL;
        
        -- Desativa modo atual
        UPDATE user_modes
        SET is_active = false, updated_at = NOW()
        WHERE user_id = p_user_id AND is_active = true;
    END IF;
    
    -- Ativa novo modo (cria se não existir)
    INSERT INTO user_modes (user_id, mode_name, display_name, is_active, activation_count, last_activated_at)
    SELECT p_user_id, mode_name, display_name, true, 1, NOW()
    FROM mode_prompts
    WHERE mode_name = p_mode_name
    ON CONFLICT (user_id, mode_name) 
    DO UPDATE SET 
        is_active = true,
        activation_count = user_modes.activation_count + 1,
        last_activated_at = NOW(),
        updated_at = NOW();
    
    -- Cria nova sessão
    INSERT INTO mode_sessions (user_id, mode_name, trigger_source)
    VALUES (p_user_id, p_mode_name, 'manual');
    
END;
$$ LANGUAGE plpgsql;


-- View: Modo ativo do usuário
CREATE OR REPLACE VIEW v_active_user_mode AS
SELECT 
    um.user_id,
    um.mode_name,
    mp.display_name,
    mp.icon,
    mp.system_prompt,
    mp.greeting_template,
    mp.priority_tools,
    um.config,
    um.last_activated_at
FROM user_modes um
JOIN mode_prompts mp ON um.mode_name = mp.mode_name
WHERE um.is_active = true;
