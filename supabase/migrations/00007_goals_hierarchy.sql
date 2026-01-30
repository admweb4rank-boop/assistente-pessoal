-- ============================================
-- Migration: 00007 - Goals Hierarchy System
-- Sistema de objetivos hierárquicos (Macro/Meso/Micro)
-- ============================================

-- ============================================
-- GOALS TABLE (Objetivos Hierárquicos)
-- ============================================
CREATE TABLE IF NOT EXISTS goals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Hierarquia
    level VARCHAR(20) NOT NULL, -- 'macro' (ano), 'meso' (trimestre), 'micro' (semana)
    parent_id UUID REFERENCES goals(id) ON DELETE SET NULL, -- Objetivo pai
    
    -- Identificação
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    
    -- Área da vida
    area VARCHAR(50), -- 'work', 'health', 'finance', 'relationships', 'learning', 'personal'
    
    -- Período
    period_type VARCHAR(20) NOT NULL, -- 'year', 'quarter', 'month', 'week'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_label VARCHAR(50), -- 'Q1 2026', 'Semana 4', etc.
    
    -- Progresso
    progress_type VARCHAR(20) DEFAULT 'percentage', -- 'percentage', 'numeric', 'boolean', 'checklist'
    target_value DECIMAL(10, 2), -- Para metas numéricas
    current_value DECIMAL(10, 2) DEFAULT 0,
    progress_percentage INTEGER DEFAULT 0, -- 0-100
    
    -- Key Results (para OKRs)
    key_results JSONB DEFAULT '[]'::jsonb,
    -- Estrutura:
    -- [
    --   {"id": "uuid", "description": "texto", "target": 100, "current": 50, "unit": "clientes"},
    --   ...
    -- ]
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- 'draft', 'active', 'paused', 'completed', 'abandoned'
    priority INTEGER DEFAULT 3, -- 1 (urgente) a 5 (baixa)
    
    -- Reflexão
    reflection TEXT, -- Reflexão ao finalizar
    lessons_learned TEXT, -- Aprendizados
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Índices
CREATE INDEX idx_goals_user ON goals(user_id);
CREATE INDEX idx_goals_level ON goals(level);
CREATE INDEX idx_goals_parent ON goals(parent_id);
CREATE INDEX idx_goals_area ON goals(area);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_period ON goals(period_start, period_end);

-- RLS
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own goals" ON goals
    FOR ALL USING (auth.uid() = user_id);

-- Trigger
CREATE TRIGGER update_goals_updated_at
    BEFORE UPDATE ON goals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- GOAL_CHECKINS TABLE (Check-ins de Objetivos)
-- ============================================
CREATE TABLE IF NOT EXISTS goal_checkins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    
    -- Progresso reportado
    progress_delta DECIMAL(10, 2), -- Quanto avançou
    new_progress_percentage INTEGER,
    
    -- Contexto
    notes TEXT,
    blockers TEXT, -- O que está travando
    next_actions TEXT, -- Próximos passos
    
    -- Sentimento
    confidence_level INTEGER, -- 1-5, quão confiante está em atingir
    energy_level INTEGER, -- 1-5, energia para esse objetivo
    
    -- Timestamp
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_goal_checkins_user ON goal_checkins(user_id);
CREATE INDEX idx_goal_checkins_goal ON goal_checkins(goal_id);
CREATE INDEX idx_goal_checkins_date ON goal_checkins(checked_at DESC);

-- RLS
ALTER TABLE goal_checkins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own goal checkins" ON goal_checkins
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- GOAL_HABITS TABLE (Hábitos vinculados a Objetivos)
-- ============================================
CREATE TABLE IF NOT EXISTS goal_habits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    
    -- Hábito
    habit_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Frequência
    frequency VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'specific_days'
    target_per_period INTEGER DEFAULT 1, -- Quantas vezes por período
    days_of_week INTEGER[] DEFAULT '{}', -- Para specific_days: [1,3,5] = seg, qua, sex
    
    -- Tracking
    streak_current INTEGER DEFAULT 0,
    streak_best INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_goal_habits_goal ON goal_habits(goal_id);

-- RLS
ALTER TABLE goal_habits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage goal habits via goals" ON goal_habits
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM goals g 
            WHERE g.id = goal_habits.goal_id 
            AND g.user_id = auth.uid()
        )
    );


-- ============================================
-- HABIT_COMPLETIONS TABLE (Registros de Hábitos)
-- ============================================
CREATE TABLE IF NOT EXISTS habit_completions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    habit_id UUID NOT NULL REFERENCES goal_habits(id) ON DELETE CASCADE,
    
    -- Quando foi feito
    completed_date DATE NOT NULL DEFAULT CURRENT_DATE,
    completed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Contexto
    notes TEXT,
    quality INTEGER, -- 1-5, qualidade da execução
    
    -- Constraint: um registro por dia por hábito
    UNIQUE(habit_id, completed_date)
);

-- Índices
CREATE INDEX idx_habit_completions_habit ON habit_completions(habit_id);
CREATE INDEX idx_habit_completions_date ON habit_completions(completed_date DESC);

-- RLS
ALTER TABLE habit_completions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage habit completions via goals" ON habit_completions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM goal_habits gh
            JOIN goals g ON g.id = gh.goal_id
            WHERE gh.id = habit_completions.habit_id 
            AND g.user_id = auth.uid()
        )
    );


-- ============================================
-- VIEWS
-- ============================================

-- View: Árvore de objetivos do usuário
CREATE OR REPLACE VIEW v_goals_tree AS
WITH RECURSIVE goal_tree AS (
    -- Objetivos raiz (macro)
    SELECT 
        g.id,
        g.user_id,
        g.level,
        g.title,
        g.description,
        g.icon,
        g.area,
        g.period_type,
        g.period_label,
        g.progress_percentage,
        g.status,
        g.priority,
        g.parent_id,
        1 as depth,
        ARRAY[g.id] as path
    FROM goals g
    WHERE g.parent_id IS NULL
    
    UNION ALL
    
    -- Objetivos filhos
    SELECT 
        g.id,
        g.user_id,
        g.level,
        g.title,
        g.description,
        g.icon,
        g.area,
        g.period_type,
        g.period_label,
        g.progress_percentage,
        g.status,
        g.priority,
        g.parent_id,
        gt.depth + 1,
        gt.path || g.id
    FROM goals g
    JOIN goal_tree gt ON g.parent_id = gt.id
)
SELECT * FROM goal_tree;


-- View: Resumo de objetivos ativos por período
CREATE OR REPLACE VIEW v_goals_active_summary AS
SELECT 
    user_id,
    level,
    period_type,
    COUNT(*) as total_goals,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'active') as active,
    ROUND(AVG(progress_percentage)) as avg_progress
FROM goals
WHERE status IN ('active', 'completed')
GROUP BY user_id, level, period_type;


-- ============================================
-- FUNCTIONS
-- ============================================

-- Função: Atualizar progresso do objetivo pai baseado nos filhos
CREATE OR REPLACE FUNCTION update_parent_goal_progress()
RETURNS TRIGGER AS $$
DECLARE
    v_parent_id UUID;
    v_avg_progress INTEGER;
BEGIN
    -- Busca objetivo pai
    SELECT parent_id INTO v_parent_id
    FROM goals
    WHERE id = NEW.id;
    
    IF v_parent_id IS NOT NULL THEN
        -- Calcula média de progresso dos filhos
        SELECT ROUND(AVG(progress_percentage))
        INTO v_avg_progress
        FROM goals
        WHERE parent_id = v_parent_id
        AND status IN ('active', 'completed');
        
        -- Atualiza pai
        UPDATE goals
        SET progress_percentage = COALESCE(v_avg_progress, 0),
            updated_at = NOW()
        WHERE id = v_parent_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar progresso do pai
CREATE TRIGGER trigger_update_parent_goal_progress
    AFTER UPDATE OF progress_percentage, status ON goals
    FOR EACH ROW
    EXECUTE FUNCTION update_parent_goal_progress();


-- Função: Atualizar streak do hábito
CREATE OR REPLACE FUNCTION update_habit_streak()
RETURNS TRIGGER AS $$
DECLARE
    v_last_date DATE;
    v_current_streak INTEGER;
    v_best_streak INTEGER;
BEGIN
    -- Busca última data de conclusão (exceto a atual)
    SELECT completed_date INTO v_last_date
    FROM habit_completions
    WHERE habit_id = NEW.habit_id
    AND completed_date < NEW.completed_date
    ORDER BY completed_date DESC
    LIMIT 1;
    
    -- Busca streaks atuais
    SELECT streak_current, streak_best INTO v_current_streak, v_best_streak
    FROM goal_habits
    WHERE id = NEW.habit_id;
    
    -- Se é dia consecutivo, incrementa streak
    IF v_last_date = NEW.completed_date - INTERVAL '1 day' THEN
        v_current_streak := v_current_streak + 1;
    ELSE
        v_current_streak := 1;
    END IF;
    
    -- Atualiza best streak se necessário
    IF v_current_streak > v_best_streak THEN
        v_best_streak := v_current_streak;
    END IF;
    
    -- Atualiza o hábito
    UPDATE goal_habits
    SET streak_current = v_current_streak,
        streak_best = v_best_streak,
        total_completions = total_completions + 1
    WHERE id = NEW.habit_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_habit_streak
    AFTER INSERT ON habit_completions
    FOR EACH ROW
    EXECUTE FUNCTION update_habit_streak();


-- ============================================
-- DADOS INICIAIS - Áreas de Vida
-- ============================================
CREATE TABLE IF NOT EXISTS goal_areas (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10),
    color VARCHAR(7),
    description TEXT
);

INSERT INTO goal_areas (id, name, icon, color, description) VALUES
('work', 'Trabalho & Projetos', '💼', '#3b82f6', 'Carreira, projetos, negócios'),
('health', 'Saúde & Energia', '💪', '#22c55e', 'Corpo, mente, hábitos'),
('finance', 'Finanças', '💰', '#f59e0b', 'Dinheiro, investimentos, patrimônio'),
('relationships', 'Relacionamentos', '❤️', '#ef4444', 'Família, amigos, networking'),
('learning', 'Aprendizado', '📚', '#8b5cf6', 'Estudos, habilidades, conhecimento'),
('personal', 'Pessoal & Identidade', '✨', '#ec4899', 'Valores, propósito, lifestyle'),
('content', 'Conteúdo & Marca', '✍️', '#06b6d4', 'Marca pessoal, audiência, autoridade')
ON CONFLICT (id) DO NOTHING;
