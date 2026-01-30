-- TB Personal OS - Migration 00002
-- Check-ins, OAuth Tokens, Routine Logs, Calendar Events Cache
-- Executar no SQL Editor do Supabase

-- ==========================================
-- CHECKINS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS checkins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_type VARCHAR(50) NOT NULL, -- 'energy', 'mood', 'sleep', 'workout', 'custom'
    value INTEGER, -- 1-5 para escalas, minutos para workout
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_checkins_user_id ON checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_checkins_type ON checkins(checkin_type);
CREATE INDEX IF NOT EXISTS idx_checkins_created_at ON checkins(created_at);
CREATE INDEX IF NOT EXISTS idx_checkins_user_type_date ON checkins(user_id, checkin_type, created_at);

-- RLS
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS checkins_user_policy ON checkins;
CREATE POLICY checkins_user_policy ON checkins
    FOR ALL USING (auth.uid() = user_id);

-- ==========================================
-- OAUTH TOKENS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google', 'github', etc.
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    scopes TEXT[], -- Array de scopes autorizados
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_provider ON oauth_tokens(provider);

-- RLS
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS oauth_tokens_user_policy ON oauth_tokens;
CREATE POLICY oauth_tokens_user_policy ON oauth_tokens
    FOR ALL USING (auth.uid() = user_id);

-- ==========================================
-- ROUTINE LOGS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS routine_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    routine_type VARCHAR(50) NOT NULL, -- 'morning', 'night', 'weekly'
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT true,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_routine_logs_user_id ON routine_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_routine_logs_type ON routine_logs(routine_type);
CREATE INDEX IF NOT EXISTS idx_routine_logs_executed_at ON routine_logs(executed_at);

-- RLS
ALTER TABLE routine_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS routine_logs_user_policy ON routine_logs;
CREATE POLICY routine_logs_user_policy ON routine_logs
    FOR ALL USING (auth.uid() = user_id);

-- ==========================================
-- CALENDAR EVENTS CACHE TABLE
-- ==========================================

-- Adicionar colunas que podem estar faltando na tabela existente
DO $$ 
BEGIN
    -- Adicionar start_time se não existir
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'calendar_events_cache' AND column_name = 'start_time'
    ) THEN
        -- Se a tabela existe mas não tem start_time, pode ter 'start' ou 'event_start'
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'calendar_events_cache' AND column_name = 'event_start'
        ) THEN
            ALTER TABLE calendar_events_cache RENAME COLUMN event_start TO start_time;
        ELSIF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'calendar_events_cache'
        ) THEN
            -- Tabela não existe, será criada abaixo
            NULL;
        ELSE
            ALTER TABLE calendar_events_cache ADD COLUMN start_time TIMESTAMPTZ;
        END IF;
    END IF;
    
    -- Adicionar end_time se não existir
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'calendar_events_cache' AND column_name = 'end_time'
    ) THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'calendar_events_cache' AND column_name = 'event_end'
        ) THEN
            ALTER TABLE calendar_events_cache RENAME COLUMN event_end TO end_time;
        ELSIF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'calendar_events_cache'
        ) THEN
            ALTER TABLE calendar_events_cache ADD COLUMN end_time TIMESTAMPTZ;
        END IF;
    END IF;
    
    -- Adicionar outras colunas que podem estar faltando
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'calendar_events_cache') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'calendar_events_cache' AND column_name = 'provider') THEN
            ALTER TABLE calendar_events_cache ADD COLUMN provider VARCHAR(50) DEFAULT 'google';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'calendar_events_cache' AND column_name = 'is_all_day') THEN
            ALTER TABLE calendar_events_cache ADD COLUMN is_all_day BOOLEAN DEFAULT false;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'calendar_events_cache' AND column_name = 'synced_at') THEN
            ALTER TABLE calendar_events_cache ADD COLUMN synced_at TIMESTAMPTZ DEFAULT NOW();
        END IF;
    END IF;
END $$;

-- Criar tabela apenas se não existir
CREATE TABLE IF NOT EXISTS calendar_events_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL DEFAULT 'google',
    event_id VARCHAR(255) NOT NULL,
    calendar_id VARCHAR(255) DEFAULT 'primary',
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    location TEXT,
    is_all_day BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'confirmed',
    metadata JSONB DEFAULT '{}',
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider, event_id)
);

-- Índices (só criar se a coluna existir)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'calendar_events_cache' AND column_name = 'user_id') THEN
        CREATE INDEX IF NOT EXISTS idx_calendar_cache_user_id ON calendar_events_cache(user_id);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'calendar_events_cache' AND column_name = 'start_time') THEN
        CREATE INDEX IF NOT EXISTS idx_calendar_cache_start_time ON calendar_events_cache(start_time);
        CREATE INDEX IF NOT EXISTS idx_calendar_cache_user_start ON calendar_events_cache(user_id, start_time);
    END IF;
END $$;

-- RLS
ALTER TABLE calendar_events_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS calendar_events_cache_user_policy ON calendar_events_cache;
CREATE POLICY calendar_events_cache_user_policy ON calendar_events_cache
    FOR ALL USING (auth.uid() = user_id);

-- ==========================================
-- PROJECTS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'archived', 'paused'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high'
    color VARCHAR(20) DEFAULT '#3b82f6',
    icon VARCHAR(50) DEFAULT '📁',
    start_date DATE,
    target_date DATE,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_user_status ON projects(user_id, status);

-- RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS projects_user_policy ON projects;
CREATE POLICY projects_user_policy ON projects
    FOR ALL USING (auth.uid() = user_id);

-- ==========================================
-- ADICIONAR project_id À TABELA TASKS
-- ==========================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'project_id'
    ) THEN
        ALTER TABLE tasks ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE SET NULL;
        CREATE INDEX idx_tasks_project_id ON tasks(project_id);
    END IF;
END $$;

-- ==========================================
-- FUNCTION: Update updated_at trigger
-- ==========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
DROP TRIGGER IF EXISTS update_checkins_updated_at ON checkins;
CREATE TRIGGER update_checkins_updated_at BEFORE UPDATE ON checkins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_oauth_tokens_updated_at ON oauth_tokens;
CREATE TRIGGER update_oauth_tokens_updated_at BEFORE UPDATE ON oauth_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_calendar_events_cache_updated_at ON calendar_events_cache;
CREATE TRIGGER update_calendar_events_cache_updated_at BEFORE UPDATE ON calendar_events_cache
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- COMENTÁRIOS
-- ==========================================

COMMENT ON TABLE checkins IS 'Check-ins de energia, humor, sono e treino';
COMMENT ON TABLE oauth_tokens IS 'Tokens OAuth para integrações externas';
COMMENT ON TABLE routine_logs IS 'Log de execução de rotinas automáticas';
COMMENT ON TABLE calendar_events_cache IS 'Cache de eventos de calendário';
COMMENT ON TABLE projects IS 'Projetos para organização de tarefas';
