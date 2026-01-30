-- TB Personal OS - Database Schema
-- PostgreSQL 15+
-- Supabase Compatible

-- =============================================
-- EXTENSIONS
-- =============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Para buscas textuais
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================
-- CUSTOM TYPES (ENUMS)
-- =============================================

CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done', 'cancelled');
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE inbox_status AS ENUM ('new', 'processing', 'processed', 'archived');
CREATE TYPE inbox_category AS ENUM ('personal', 'work', 'health', 'content', 'finance', 'other');
CREATE TYPE project_status AS ENUM ('planning', 'active', 'paused', 'completed', 'cancelled');
CREATE TYPE content_status AS ENUM ('idea', 'draft', 'scheduled', 'published', 'archived');
CREATE TYPE content_channel AS ENUM ('instagram', 'linkedin', 'twitter', 'blog', 'youtube', 'other');
CREATE TYPE recommendation_type AS ENUM ('productivity', 'health', 'content', 'finance', 'general');
CREATE TYPE recommendation_status AS ENUM ('pending', 'read', 'applied', 'dismissed');

-- =============================================
-- CORE TABLES
-- =============================================

-- Users (gerenciado pelo Supabase Auth, mas mantemos referência)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- User Profiles (preferências e configurações)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timezone TEXT DEFAULT 'America/Sao_Paulo',
    language TEXT DEFAULT 'pt-BR',
    
    -- Preferências de notificação
    notify_morning_summary BOOLEAN DEFAULT true,
    notify_night_summary BOOLEAN DEFAULT true,
    notify_weekly_planning BOOLEAN DEFAULT true,
    morning_summary_time TIME DEFAULT '07:00',
    night_summary_time TIME DEFAULT '21:00',
    
    -- Preferências de autonomia
    autonomy_level TEXT DEFAULT 'confirm',  -- 'suggest', 'confirm', 'auto'
    
    -- Objetivos e princípios (JSONB para flexibilidade)
    goals JSONB DEFAULT '[]'::jsonb,
    principles JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    onboarding_completed BOOLEAN DEFAULT false,
    onboarded_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- =============================================
-- INBOX & NOTES
-- =============================================

-- Inbox unificada
CREATE TABLE inbox_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Conteúdo
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'text',  -- 'text', 'link', 'file', 'voice'
    file_url TEXT,
    
    -- Classificação
    status inbox_status DEFAULT 'new',
    category inbox_category DEFAULT 'other',
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Processamento
    processed_at TIMESTAMPTZ,
    suggested_actions JSONB,  -- Ações sugeridas pelo LLM
    
    -- Origem
    source TEXT DEFAULT 'telegram',  -- 'telegram', 'web', 'api'
    source_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes serão criados separadamente
    CONSTRAINT inbox_content_not_empty CHECK (length(trim(content)) > 0)
);

-- Notes (anotações processadas e organizadas)
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Conteúdo
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_html TEXT,  -- Versão renderizada
    
    -- Organização
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    category inbox_category DEFAULT 'other',
    is_pinned BOOLEAN DEFAULT false,
    
    -- Vinculações
    inbox_item_id UUID REFERENCES inbox_items(id) ON DELETE SET NULL,
    project_id UUID,  -- Will reference projects(id)
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    
    CONSTRAINT note_title_not_empty CHECK (length(trim(title)) > 0)
);

-- =============================================
-- TASKS & HABITS
-- =============================================

-- Tasks (tarefas e to-dos)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Conteúdo
    title TEXT NOT NULL,
    description TEXT,
    
    -- Status e prioridade
    status task_status DEFAULT 'todo',
    priority task_priority DEFAULT 'medium',
    
    -- Datas
    due_date DATE,
    due_time TIME,
    completed_at TIMESTAMPTZ,
    
    -- Vinculações
    project_id UUID,  -- Will reference projects(id)
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,  -- Subtarefas
    inbox_item_id UUID REFERENCES inbox_items(id) ON DELETE SET NULL,
    
    -- Organização
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Estimativas
    estimated_minutes INTEGER,
    actual_minutes INTEGER,
    
    -- Recorrência (opcional)
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT,  -- iCalendar RRULE format
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT task_title_not_empty CHECK (length(trim(title)) > 0)
);

-- Habits & Check-ins
CREATE TABLE habits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Hábito
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'other',  -- 'health', 'productivity', 'personal'
    
    -- Configuração
    target_frequency INTEGER DEFAULT 1,  -- Vezes por dia/semana
    target_period TEXT DEFAULT 'daily',  -- 'daily', 'weekly'
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    
    CONSTRAINT habit_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Check-ins (registros de hábitos e métricas)
CREATE TABLE checkins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    habit_id UUID REFERENCES habits(id) ON DELETE CASCADE,
    
    -- Tipo de check-in
    checkin_type TEXT NOT NULL,  -- 'energy', 'mood', 'sleep', 'habit'
    
    -- Valores
    value_numeric DECIMAL(5,2),  -- Para métricas numéricas (1-10, horas, etc)
    value_text TEXT,  -- Para valores textuais
    value_json JSONB,  -- Para dados estruturados
    
    -- Data/hora do check-in (não quando foi registrado)
    checkin_date DATE NOT NULL,
    checkin_time TIME,
    
    -- Notas
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_checkin_type CHECK (
        checkin_type IN ('energy', 'mood', 'sleep', 'workout', 'nutrition', 'habit', 'custom')
    )
);

-- =============================================
-- CALENDAR & EVENTS
-- =============================================

-- Google Calendar Events Cache
CREATE TABLE calendar_events_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Google Calendar data
    google_event_id TEXT NOT NULL,
    google_calendar_id TEXT NOT NULL,
    
    -- Event data
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    
    -- Datas
    start_datetime TIMESTAMPTZ NOT NULL,
    end_datetime TIMESTAMPTZ NOT NULL,
    is_all_day BOOLEAN DEFAULT false,
    timezone TEXT,
    
    -- Metadata
    attendees JSONB,
    recurrence TEXT[],  -- RRULE array
    status TEXT,  -- 'confirmed', 'tentative', 'cancelled'
    
    -- Cache control
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, google_event_id)
);

-- =============================================
-- PROJECTS & CLIENTS
-- =============================================

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Básico
    name TEXT NOT NULL,
    description TEXT,
    
    -- Status
    status project_status DEFAULT 'planning',
    priority task_priority DEFAULT 'medium',
    
    -- Datas
    start_date DATE,
    target_date DATE,
    completed_at TIMESTAMPTZ,
    
    -- Organização
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    color TEXT,  -- HEX color para UI
    
    -- Vinculações
    client_id UUID,  -- Will reference contacts(id)
    
    -- Metadata
    goals JSONB DEFAULT '[]'::jsonb,
    kpis JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    
    CONSTRAINT project_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Project Items (tarefas, decisões, documentos, etc dentro do projeto)
CREATE TABLE project_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tipo
    item_type TEXT NOT NULL,  -- 'task', 'decision', 'document', 'meeting', 'milestone'
    
    -- Conteúdo
    title TEXT NOT NULL,
    content TEXT,
    
    -- Vinculações
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    note_id UUID REFERENCES notes(id) ON DELETE SET NULL,
    
    -- Status
    status TEXT DEFAULT 'active',
    
    -- Metadata específica por tipo
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT project_item_title_not_empty CHECK (length(trim(title)) > 0)
);

-- =============================================
-- CONTACTS (Pessoas e Empresas)
-- =============================================

CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Básico
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    role TEXT,
    
    -- Tipo
    contact_type TEXT DEFAULT 'person',  -- 'person', 'company'
    
    -- Tags e categorias
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    categories TEXT[] DEFAULT ARRAY[]::TEXT[],  -- 'client', 'lead', 'partner', 'personal'
    
    -- Redes sociais e links
    linkedin_url TEXT,
    instagram_url TEXT,
    website_url TEXT,
    
    -- Notas e contexto
    notes TEXT,
    last_interaction_date DATE,
    next_followup_date DATE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    
    CONSTRAINT contact_name_not_empty CHECK (length(trim(name)) > 0)
);

-- =============================================
-- CONTENT OS
-- =============================================

-- Content Ideas
CREATE TABLE content_ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Conteúdo
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,  -- Rascunho inicial
    
    -- Categoria e tags
    category TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Status
    status content_status DEFAULT 'idea',
    
    -- Canais pretendidos
    target_channels content_channel[] DEFAULT ARRAY[]::content_channel[],
    
    -- Vinculações
    inbox_item_id UUID REFERENCES inbox_items(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT content_idea_title_not_empty CHECK (length(trim(title)) > 0)
);

-- Content Posts (conteúdos publicados)
CREATE TABLE content_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_idea_id UUID REFERENCES content_ideas(id) ON DELETE SET NULL,
    
    -- Conteúdo
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- Publicação
    channel content_channel NOT NULL,
    status content_status DEFAULT 'draft',
    published_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    
    -- URLs
    post_url TEXT,
    
    -- Métricas (atualizadas manualmente ou via API)
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT content_post_title_not_empty CHECK (length(trim(title)) > 0)
);

-- =============================================
-- FINANCE
-- =============================================

-- Transactions (entradas e saídas financeiras)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tipo
    transaction_type TEXT NOT NULL,  -- 'income', 'expense'
    
    -- Valores
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'BRL',
    
    -- Descrição
    description TEXT NOT NULL,
    category TEXT,  -- 'salary', 'client_payment', 'subscription', 'food', etc
    
    -- Vinculações
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    
    -- Datas
    transaction_date DATE NOT NULL,
    
    -- Recorrência
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT,
    
    -- Tags
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_transaction_type CHECK (transaction_type IN ('income', 'expense')),
    CONSTRAINT positive_amount CHECK (amount > 0)
);

-- =============================================
-- AI & ML
-- =============================================

-- Assistant Logs (registro completo de todas as ações do assistente)
CREATE TABLE assistant_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Ação
    action_type TEXT NOT NULL,  -- 'message', 'tool_call', 'recommendation', 'analysis'
    
    -- Input/Output
    input_data JSONB NOT NULL,
    output_data JSONB,
    
    -- LLM Details
    reasoning TEXT,  -- Reasoning do LLM (se disponível)
    tool_calls JSONB,  -- Ferramentas executadas
    tokens_used INTEGER DEFAULT 0,
    model_used TEXT,
    
    -- Performance
    duration_ms INTEGER,
    
    -- Status
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_action_type CHECK (
        action_type IN ('message', 'tool_call', 'recommendation', 'analysis', 'scheduled_task')
    )
);

-- Recommendations (recomendações do ML)
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tipo e título
    type recommendation_type NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    
    -- Detalhes
    reasoning TEXT,  -- Por que essa recomendação
    data_points INTEGER,  -- Quantidade de dados usados na análise
    confidence_score DECIMAL(3,2),  -- 0.0 a 1.0
    
    -- Ação sugerida
    suggested_action TEXT,
    action_metadata JSONB,
    
    -- Status
    status recommendation_status DEFAULT 'pending',
    
    -- Feedback
    user_feedback TEXT,  -- 'helpful', 'not_helpful', 'already_doing'
    applied_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT recommendation_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0 AND 1)
);

-- Metrics (métricas gerais para análise)
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tipo de métrica
    metric_type TEXT NOT NULL,  -- 'productivity', 'health', 'content_performance', etc
    metric_name TEXT NOT NULL,
    
    -- Valor
    value_numeric DECIMAL(10,2),
    value_text TEXT,
    value_json JSONB,
    
    -- Dimensões (para filtros e agregações)
    dimensions JSONB DEFAULT '{}'::jsonb,
    
    -- Data da métrica
    metric_date DATE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT metric_type_not_empty CHECK (length(trim(metric_type)) > 0)
);

-- =============================================
-- INTEGRATIONS
-- =============================================

-- OAuth Tokens (para Google APIs)
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,  -- 'google', 'microsoft', etc
    
    -- Tokens (criptografados)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type TEXT DEFAULT 'Bearer',
    
    -- Scopes
    scopes TEXT[],
    
    -- Expiration
    expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, provider)
);

-- Telegram Chats (registro de chats ativos)
CREATE TABLE telegram_chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Telegram data
    chat_id BIGINT NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_blocked BOOLEAN DEFAULT false,
    
    -- Preferences
    preferences JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_interaction_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- INDEXES
-- =============================================

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NOT NULL;

-- Profiles
CREATE INDEX idx_profiles_user ON profiles(user_id);

-- Inbox
CREATE INDEX idx_inbox_user_status ON inbox_items(user_id, status);
CREATE INDEX idx_inbox_user_created ON inbox_items(user_id, created_at DESC);
CREATE INDEX idx_inbox_tags ON inbox_items USING GIN(tags);
CREATE INDEX idx_inbox_content_search ON inbox_items USING GIN(to_tsvector('portuguese', content));

-- Notes
CREATE INDEX idx_notes_user ON notes(user_id);
CREATE INDEX idx_notes_user_created ON notes(user_id, created_at DESC);
CREATE INDEX idx_notes_project ON notes(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_notes_tags ON notes USING GIN(tags);
CREATE INDEX idx_notes_content_search ON notes USING GIN(
    to_tsvector('portuguese', title || ' ' || content)
);

-- Tasks
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_date) WHERE status != 'done' AND status != 'cancelled';
CREATE INDEX idx_tasks_project ON tasks(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id) WHERE parent_task_id IS NOT NULL;

-- Habits & Checkins
CREATE INDEX idx_habits_user ON habits(user_id);
CREATE INDEX idx_checkins_user_date ON checkins(user_id, checkin_date DESC);
CREATE INDEX idx_checkins_habit ON checkins(habit_id) WHERE habit_id IS NOT NULL;
CREATE INDEX idx_checkins_type_date ON checkins(checkin_type, checkin_date DESC);

-- Calendar
CREATE INDEX idx_calendar_user_date ON calendar_events_cache(user_id, start_datetime DESC);
CREATE INDEX idx_calendar_google_event ON calendar_events_cache(google_event_id);

-- Projects
CREATE INDEX idx_projects_user_status ON projects(user_id, status);
CREATE INDEX idx_projects_client ON projects(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX idx_project_items_project ON project_items(project_id);

-- Contacts
CREATE INDEX idx_contacts_user ON contacts(user_id);
CREATE INDEX idx_contacts_categories ON contacts USING GIN(categories);
CREATE INDEX idx_contacts_name_search ON contacts USING GIN(to_tsvector('portuguese', name));

-- Content
CREATE INDEX idx_content_ideas_user_status ON content_ideas(user_id, status);
CREATE INDEX idx_content_posts_user_published ON content_posts(user_id, published_at DESC);
CREATE INDEX idx_content_posts_channel ON content_posts(channel, published_at DESC);

-- Finance
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
CREATE INDEX idx_transactions_project ON transactions(project_id) WHERE project_id IS NOT NULL;

-- ML & Logs
CREATE INDEX idx_assistant_logs_user_created ON assistant_logs(user_id, created_at DESC);
CREATE INDEX idx_assistant_logs_action ON assistant_logs(action_type, created_at DESC);
CREATE INDEX idx_recommendations_user_status ON recommendations(user_id, status, created_at DESC);
CREATE INDEX idx_metrics_user_type_date ON metrics(user_id, metric_type, metric_date DESC);

-- Integrations
CREATE INDEX idx_oauth_tokens_user_provider ON oauth_tokens(user_id, provider);
CREATE INDEX idx_telegram_chats_chat_id ON telegram_chats(chat_id);

-- =============================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================

-- Habilitar RLS em todas as tabelas
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbox_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assistant_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_chats ENABLE ROW LEVEL SECURITY;

-- Políticas RLS (usuários só veem seus próprios dados)
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own inbox" ON inbox_items FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own notes" ON notes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own tasks" ON tasks FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own habits" ON habits FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own checkins" ON checkins FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own calendar" ON calendar_events_cache FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own projects" ON projects FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own project_items" ON project_items FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own contacts" ON contacts FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own content_ideas" ON content_ideas FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own content_posts" ON content_posts FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own transactions" ON transactions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own logs" ON assistant_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view own recommendations" ON recommendations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own metrics" ON metrics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view own oauth" ON oauth_tokens FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own telegram" ON telegram_chats FOR ALL USING (auth.uid() = user_id);

-- =============================================
-- FUNCTIONS & TRIGGERS
-- =============================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger em todas as tabelas relevantes
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_inbox_updated_at BEFORE UPDATE ON inbox_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
-- (Adicionar para outras tabelas conforme necessário)

-- =============================================
-- VIEWS ÚTEIS
-- =============================================

-- View: Tarefas pendentes com informações do projeto
CREATE OR REPLACE VIEW v_active_tasks AS
SELECT 
    t.id,
    t.user_id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.due_date,
    t.due_time,
    t.estimated_minutes,
    p.id AS project_id,
    p.name AS project_name,
    p.color AS project_color,
    t.created_at,
    t.updated_at
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
WHERE t.status IN ('todo', 'in_progress')
    AND t.completed_at IS NULL
ORDER BY 
    CASE t.priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    t.due_date NULLS LAST,
    t.created_at;

-- View: Resumo de check-ins por data
CREATE OR REPLACE VIEW v_daily_checkins AS
SELECT 
    user_id,
    checkin_date,
    MAX(CASE WHEN checkin_type = 'energy' THEN value_numeric END) AS energy_level,
    MAX(CASE WHEN checkin_type = 'mood' THEN value_text END) AS mood,
    MAX(CASE WHEN checkin_type = 'sleep' THEN value_numeric END) AS sleep_hours
FROM checkins
GROUP BY user_id, checkin_date
ORDER BY checkin_date DESC;

-- View: Métricas de produtividade semanal
CREATE OR REPLACE VIEW v_weekly_productivity AS
SELECT 
    user_id,
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) FILTER (WHERE status = 'done') AS tasks_completed,
    COUNT(*) FILTER (WHERE status IN ('todo', 'in_progress')) AS tasks_pending,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'done')::NUMERIC / 
        NULLIF(COUNT(*)::NUMERIC, 0) * 100, 
        2
    ) AS completion_rate
FROM tasks
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY user_id, DATE_TRUNC('week', created_at)
ORDER BY week_start DESC;

-- =============================================
-- DADOS INICIAIS (SEED)
-- =============================================

-- Esta seção seria preenchida após ter um usuário criado
-- Exemplo de categorias padrão, templates, etc.

-- =============================================
-- COMENTÁRIOS FINAIS
-- =============================================

-- Este schema está pronto para:
-- 1. Supabase (com Auth e RLS)
-- 2. Escalabilidade (índices apropriados)
-- 3. ML e análises (tabelas de métricas e logs)
-- 4. Integrações (OAuth, Telegram, Google)
-- 5. Auditoria completa (logs de todas as ações)

-- Próximos passos:
-- 1. Executar este script no Supabase
-- 2. Configurar Auth do Supabase
-- 3. Criar migrations para versionamento
-- 4. Popular com dados de teste
