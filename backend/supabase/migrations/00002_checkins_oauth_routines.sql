-- Migration: Add checkins, oauth_tokens, and routine_logs tables
-- Run this in Supabase SQL Editor

-- ==========================================
-- CHECKINS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_type VARCHAR(50) NOT NULL, -- energy, mood, sleep, workout, focus, custom
    value JSONB NOT NULL, -- Flexible: number, string, or object
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    checkin_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para checkins
CREATE INDEX IF NOT EXISTS idx_checkins_user_id ON checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_checkins_type ON checkins(checkin_type);
CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date);
CREATE INDEX IF NOT EXISTS idx_checkins_user_date ON checkins(user_id, checkin_date);

-- RLS para checkins
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own checkins"
    ON checkins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own checkins"
    ON checkins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own checkins"
    ON checkins FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own checkins"
    ON checkins FOR DELETE
    USING (auth.uid() = user_id);

-- Service role bypass
CREATE POLICY "Service role full access checkins"
    ON checkins FOR ALL
    USING (auth.role() = 'service_role');


-- ==========================================
-- OAUTH TOKENS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- google, microsoft, etc
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    scopes TEXT[], -- Array de scopes autorizados
    token_type VARCHAR(50) DEFAULT 'Bearer',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint: um token por provider por usuário
    UNIQUE(user_id, provider)
);

-- Índices para oauth_tokens
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_provider ON oauth_tokens(provider);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_provider ON oauth_tokens(user_id, provider);

-- RLS para oauth_tokens
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own tokens"
    ON oauth_tokens FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tokens"
    ON oauth_tokens FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tokens"
    ON oauth_tokens FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own tokens"
    ON oauth_tokens FOR DELETE
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access oauth_tokens"
    ON oauth_tokens FOR ALL
    USING (auth.role() = 'service_role');


-- ==========================================
-- ROUTINE LOGS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS routine_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    routine_type VARCHAR(50) NOT NULL, -- morning, night, weekly
    message_sent TEXT,
    status VARCHAR(20) DEFAULT 'completed', -- completed, failed, skipped
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para routine_logs
CREATE INDEX IF NOT EXISTS idx_routine_logs_user_id ON routine_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_routine_logs_type ON routine_logs(routine_type);
CREATE INDEX IF NOT EXISTS idx_routine_logs_executed_at ON routine_logs(executed_at);

-- RLS para routine_logs
ALTER TABLE routine_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own routine logs"
    ON routine_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access routine_logs"
    ON routine_logs FOR ALL
    USING (auth.role() = 'service_role');


-- ==========================================
-- CALENDAR EVENTS CACHE TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS calendar_events_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    calendar_id VARCHAR(255) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    location VARCHAR(500),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    all_day BOOLEAN DEFAULT FALSE,
    status VARCHAR(50),
    html_link TEXT,
    attendees JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(user_id, calendar_id, event_id)
);

-- Índices para calendar_events_cache
CREATE INDEX IF NOT EXISTS idx_calendar_cache_user_id ON calendar_events_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_cache_start ON calendar_events_cache(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_cache_user_start ON calendar_events_cache(user_id, start_time);

-- RLS para calendar_events_cache
ALTER TABLE calendar_events_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own calendar cache"
    ON calendar_events_cache FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access calendar_cache"
    ON calendar_events_cache FOR ALL
    USING (auth.role() = 'service_role');


-- ==========================================
-- HELPER FUNCTIONS
-- ==========================================

-- Função para limpar cache de calendário antigo
CREATE OR REPLACE FUNCTION cleanup_old_calendar_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM calendar_events_cache
    WHERE synced_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Função para obter média de energia dos últimos N dias
CREATE OR REPLACE FUNCTION get_avg_energy(p_user_id UUID, p_days INTEGER DEFAULT 7)
RETURNS NUMERIC AS $$
DECLARE
    v_avg NUMERIC;
BEGIN
    SELECT AVG((value::text)::numeric)
    INTO v_avg
    FROM checkins
    WHERE user_id = p_user_id
    AND checkin_type = 'energy'
    AND checkin_date >= CURRENT_DATE - p_days;
    
    RETURN COALESCE(v_avg, 0);
END;
$$ LANGUAGE plpgsql;


-- ==========================================
-- GRANT PERMISSIONS
-- ==========================================

-- Grants para anon e authenticated
GRANT SELECT ON checkins TO anon, authenticated;
GRANT INSERT ON checkins TO authenticated;
GRANT UPDATE ON checkins TO authenticated;
GRANT DELETE ON checkins TO authenticated;

GRANT SELECT ON oauth_tokens TO authenticated;
GRANT INSERT ON oauth_tokens TO authenticated;
GRANT UPDATE ON oauth_tokens TO authenticated;
GRANT DELETE ON oauth_tokens TO authenticated;

GRANT SELECT ON routine_logs TO authenticated;

GRANT SELECT ON calendar_events_cache TO authenticated;


-- ==========================================
-- VERIFY TABLES
-- ==========================================

SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('checkins', 'oauth_tokens', 'routine_logs', 'calendar_events_cache');
