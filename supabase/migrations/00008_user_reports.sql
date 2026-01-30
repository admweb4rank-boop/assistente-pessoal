-- ============================================
-- Migration: 00008 - User Reports Table
-- Tabela para armazenar relatórios gerados
-- ============================================

CREATE TABLE IF NOT EXISTS user_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Tipo de relatório
    report_type VARCHAR(50) NOT NULL, -- 'monthly', 'weekly', 'quarterly', 'annual'
    
    -- Período
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Dados do relatório (JSON)
    report_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Metadados
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    sent_via VARCHAR(50), -- 'telegram', 'email', etc.
    sent_at TIMESTAMPTZ,
    
    -- Índice único para evitar duplicatas
    UNIQUE(user_id, report_type, period_start, period_end)
);

-- Índices
CREATE INDEX idx_user_reports_user ON user_reports(user_id);
CREATE INDEX idx_user_reports_type ON user_reports(report_type);
CREATE INDEX idx_user_reports_period ON user_reports(period_start, period_end);

-- RLS
ALTER TABLE user_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own reports" ON user_reports
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can manage reports" ON user_reports
    FOR ALL USING (true);


-- ============================================
-- Função RPC para contar completions de hábitos
-- ============================================
CREATE OR REPLACE FUNCTION get_habit_completions_count(
    p_user_id UUID,
    p_start DATE,
    p_end DATE
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM habit_completions hc
    JOIN goal_habits gh ON gh.id = hc.habit_id
    JOIN goals g ON g.id = gh.goal_id
    WHERE g.user_id = p_user_id
    AND hc.completed_date BETWEEN p_start AND p_end;
    
    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
