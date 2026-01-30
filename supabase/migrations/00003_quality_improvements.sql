-- Migration: 00003_quality_improvements.sql
-- Description: Fix débitos técnicos e melhorias de qualidade
-- Date: 2026-01-21
-- Author: System

-- =============================================
-- FIX: Adicionar coluna 'source' em assistant_logs
-- =============================================
ALTER TABLE assistant_logs 
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'system';

COMMENT ON COLUMN assistant_logs.source IS 'Origem da ação: telegram, api, system, scheduler';

-- =============================================
-- IMPROVEMENT: Índices para performance
-- =============================================

-- Índice para busca de tarefas por status e data
CREATE INDEX IF NOT EXISTS idx_tasks_status_due_date 
ON tasks(user_id, status, due_date) 
WHERE status IN ('todo', 'in_progress');

-- Índice para busca de inbox por status
CREATE INDEX IF NOT EXISTS idx_inbox_status_created 
ON inbox_items(user_id, status, created_at DESC);

-- Índice para busca de check-ins por tipo e data
CREATE INDEX IF NOT EXISTS idx_checkins_type_date 
ON checkins(user_id, checkin_type, created_at DESC);

-- Índice para busca de transações por tipo e data
CREATE INDEX IF NOT EXISTS idx_transactions_type_date 
ON transactions(user_id, type, date DESC);

-- Índice para busca de content_ideas por status
CREATE INDEX IF NOT EXISTS idx_content_ideas_status 
ON content_ideas(user_id, status, created_at DESC);

-- Índice para busca de memórias (contexts)
CREATE INDEX IF NOT EXISTS idx_contexts_type_created 
ON contexts(user_id, context_type, created_at DESC);

-- Índice para busca de assistant_logs por ação
CREATE INDEX IF NOT EXISTS idx_assistant_logs_action 
ON assistant_logs(user_id, action_type, created_at DESC);

-- =============================================
-- NEW TABLE: api_request_logs (observabilidade)
-- =============================================
CREATE TABLE IF NOT EXISTS api_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    status_code INTEGER,
    duration_ms INTEGER,
    request_body JSONB,
    response_body JSONB,
    headers JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_logs_request_id ON api_request_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_path ON api_request_logs(user_id, path, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_status ON api_request_logs(status_code, created_at DESC);

COMMENT ON TABLE api_request_logs IS 'Log de requisições da API para observabilidade';

-- =============================================
-- NEW TABLE: rate_limit_tracking
-- =============================================
CREATE TABLE IF NOT EXISTS rate_limit_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL, -- IP ou user_id
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_identifier 
ON rate_limit_tracking(identifier, endpoint, window_start);

COMMENT ON TABLE rate_limit_tracking IS 'Tracking de rate limiting por identificador';

-- =============================================
-- NEW TABLE: health_goals (para Health OS)
-- =============================================
CREATE TABLE IF NOT EXISTS health_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type VARCHAR(50) NOT NULL, -- sleep_hours, steps, water, weight, exercise_minutes
    target_value DECIMAL(10,2) NOT NULL,
    current_value DECIMAL(10,2) DEFAULT 0,
    unit VARCHAR(20), -- hours, steps, ml, kg, minutes
    frequency VARCHAR(20) DEFAULT 'daily', -- daily, weekly, monthly
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, paused
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_goals_user_status 
ON health_goals(user_id, status);

CREATE TRIGGER update_health_goals_updated_at
    BEFORE UPDATE ON health_goals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

COMMENT ON TABLE health_goals IS 'Metas de saúde do usuário';

-- =============================================
-- NEW TABLE: health_correlations (para insights)
-- =============================================
CREATE TABLE IF NOT EXISTS health_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_a VARCHAR(50) NOT NULL, -- sleep_hours, energy, mood, etc
    metric_b VARCHAR(50) NOT NULL,
    correlation_value DECIMAL(5,4), -- -1 a 1
    sample_size INTEGER,
    significance DECIMAL(5,4), -- p-value
    insight_text TEXT,
    period_start DATE,
    period_end DATE,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_correlations_user 
ON health_correlations(user_id, calculated_at DESC);

COMMENT ON TABLE health_correlations IS 'Correlações calculadas entre métricas de saúde';

-- =============================================
-- UPDATE: Adicionar campos em profiles para autonomia
-- =============================================
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS autonomy_preferences JSONB DEFAULT '{}';

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS notification_preferences JSONB DEFAULT '{
    "morning_summary": true,
    "night_summary": true,
    "task_reminders": true,
    "checkin_reminders": true,
    "financial_alerts": true
}';

COMMENT ON COLUMN profiles.autonomy_preferences IS 'Preferências granulares de autonomia por ação';
COMMENT ON COLUMN profiles.notification_preferences IS 'Preferências de notificações';

-- =============================================
-- RLS Policies para novas tabelas
-- =============================================

-- api_request_logs (apenas admin pode ver todos, usuário vê os seus)
ALTER TABLE api_request_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own api logs" ON api_request_logs
    FOR SELECT USING (auth.uid() = user_id);

-- health_goals
ALTER TABLE health_goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own health goals" ON health_goals
    FOR ALL USING (auth.uid() = user_id);

-- health_correlations
ALTER TABLE health_correlations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own health correlations" ON health_correlations
    FOR SELECT USING (auth.uid() = user_id);

-- =============================================
-- FUNCTION: Calcular correlação entre métricas
-- =============================================
CREATE OR REPLACE FUNCTION calculate_health_correlation(
    p_user_id UUID,
    p_metric_a VARCHAR,
    p_metric_b VARCHAR,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    correlation DECIMAL,
    sample_size INTEGER,
    insight TEXT
) AS $$
DECLARE
    v_correlation DECIMAL;
    v_count INTEGER;
    v_insight TEXT;
BEGIN
    -- Calcular correlação de Pearson simplificada
    WITH metric_data AS (
        SELECT 
            DATE(created_at) as day,
            checkin_type,
            AVG(value) as avg_value
        FROM checkins
        WHERE user_id = p_user_id
        AND checkin_type IN (p_metric_a, p_metric_b)
        AND created_at > NOW() - (p_days || ' days')::INTERVAL
        GROUP BY DATE(created_at), checkin_type
    ),
    paired_data AS (
        SELECT 
            a.day,
            a.avg_value as value_a,
            b.avg_value as value_b
        FROM metric_data a
        JOIN metric_data b ON a.day = b.day
        WHERE a.checkin_type = p_metric_a
        AND b.checkin_type = p_metric_b
    )
    SELECT 
        COALESCE(
            CORR(value_a, value_b),
            0
        ),
        COUNT(*)
    INTO v_correlation, v_count
    FROM paired_data;
    
    -- Gerar insight
    IF v_count < 7 THEN
        v_insight := 'Dados insuficientes para análise confiável';
    ELSIF v_correlation > 0.7 THEN
        v_insight := format('Forte correlação positiva entre %s e %s', p_metric_a, p_metric_b);
    ELSIF v_correlation > 0.4 THEN
        v_insight := format('Correlação moderada positiva entre %s e %s', p_metric_a, p_metric_b);
    ELSIF v_correlation < -0.7 THEN
        v_insight := format('Forte correlação negativa entre %s e %s', p_metric_a, p_metric_b);
    ELSIF v_correlation < -0.4 THEN
        v_insight := format('Correlação moderada negativa entre %s e %s', p_metric_a, p_metric_b);
    ELSE
        v_insight := format('Correlação fraca entre %s e %s', p_metric_a, p_metric_b);
    END IF;
    
    RETURN QUERY SELECT v_correlation, v_count, v_insight;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- GRANT PERMISSIONS
-- =============================================
GRANT SELECT, INSERT ON api_request_logs TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON health_goals TO authenticated;
GRANT SELECT ON health_correlations TO authenticated;
GRANT EXECUTE ON FUNCTION calculate_health_correlation TO authenticated;
