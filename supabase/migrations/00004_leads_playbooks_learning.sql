-- ============================================
-- Migration: 00004 - Leads, Playbooks & Learning
-- Módulos: Negócio (CRM), Aprendizado & Evolução
-- ============================================

-- ============================================
-- LEADS TABLE (CRM / Funil de Vendas)
-- ============================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Dados básicos
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    position VARCHAR(255),
    
    -- Status e origem
    status VARCHAR(50) DEFAULT 'new' CHECK (status IN (
        'new', 'contacted', 'qualified', 'proposal', 
        'negotiation', 'won', 'lost', 'inactive'
    )),
    source VARCHAR(50) DEFAULT 'other' CHECK (source IN (
        'instagram', 'linkedin', 'website', 'referral',
        'cold_outreach', 'event', 'other'
    )),
    
    -- Valor e scoring
    deal_value DECIMAL(10, 2),
    score INTEGER DEFAULT 50 CHECK (score >= 0 AND score <= 100),
    
    -- Anotações
    notes TEXT,
    tags TEXT[] DEFAULT '{}',
    
    -- Follow-up
    next_followup TIMESTAMPTZ,
    last_contact TIMESTAMPTZ,
    
    -- Histórico de contatos (JSON array)
    contact_history JSONB DEFAULT '[]',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para leads
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_next_followup ON leads(next_followup);
CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);

-- RLS para leads
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own leads" ON leads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own leads" ON leads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own leads" ON leads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own leads" ON leads
    FOR DELETE USING (auth.uid() = user_id);

-- Trigger para updated_at
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- PLAYBOOKS TABLE (Scripts de Vendas)
-- ============================================
CREATE TABLE IF NOT EXISTS playbooks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Conteúdo
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'script', 'email_template', 'objection', 'pitch',
        'follow_up', 'closing', 'discovery'
    )),
    content TEXT NOT NULL,
    
    -- Metadados
    stage VARCHAR(50), -- Em qual estágio do funil usar
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para playbooks
CREATE INDEX idx_playbooks_user_id ON playbooks(user_id);
CREATE INDEX idx_playbooks_category ON playbooks(category);
CREATE INDEX idx_playbooks_stage ON playbooks(stage);
CREATE INDEX idx_playbooks_active ON playbooks(is_active) WHERE is_active = true;

-- RLS para playbooks
ALTER TABLE playbooks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own playbooks" ON playbooks
    FOR ALL USING (auth.uid() = user_id);

-- Trigger para updated_at
CREATE TRIGGER update_playbooks_updated_at
    BEFORE UPDATE ON playbooks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- LEARNING_ITEMS TABLE (Learning OS)
-- ============================================
CREATE TABLE IF NOT EXISTS learning_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Conteúdo principal
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN (
        'book', 'article', 'course', 'video', 'podcast',
        'summary', 'note', 'highlight', 'flashcard'
    )),
    source_url TEXT,
    source_title VARCHAR(500),
    
    -- Resumo e notas
    summary TEXT,
    key_insights TEXT[], -- Array de insights principais
    personal_notes TEXT,
    
    -- Categorização
    topic VARCHAR(255),
    tags TEXT[] DEFAULT '{}',
    
    -- Status de aprendizado
    status VARCHAR(50) DEFAULT 'to_learn' CHECK (status IN (
        'to_learn', 'learning', 'completed', 'reviewing', 'mastered'
    )),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    
    -- Revisão Espaçada (Spaced Repetition)
    next_review TIMESTAMPTZ,
    review_count INTEGER DEFAULT 0,
    ease_factor DECIMAL(3, 2) DEFAULT 2.50, -- Fator de facilidade
    interval_days INTEGER DEFAULT 1, -- Intervalo atual em dias
    last_reviewed TIMESTAMPTZ,
    
    -- Métricas
    time_spent_minutes INTEGER DEFAULT 0,
    completion_percentage INTEGER DEFAULT 0 CHECK (
        completion_percentage >= 0 AND completion_percentage <= 100
    ),
    
    -- Trilha de aprendizado (pode pertencer a uma trilha)
    learning_path_id UUID,
    order_in_path INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para learning_items
CREATE INDEX idx_learning_items_user_id ON learning_items(user_id);
CREATE INDEX idx_learning_items_status ON learning_items(status);
CREATE INDEX idx_learning_items_type ON learning_items(content_type);
CREATE INDEX idx_learning_items_topic ON learning_items(topic);
CREATE INDEX idx_learning_items_next_review ON learning_items(next_review);
CREATE INDEX idx_learning_items_path ON learning_items(learning_path_id);
CREATE INDEX idx_learning_items_priority ON learning_items(priority DESC);

-- RLS para learning_items
ALTER TABLE learning_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own learning items" ON learning_items
    FOR ALL USING (auth.uid() = user_id);

-- Trigger para updated_at
CREATE TRIGGER update_learning_items_updated_at
    BEFORE UPDATE ON learning_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- LEARNING_PATHS TABLE (Trilhas de Aprendizado)
-- ============================================
CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Detalhes da trilha
    title VARCHAR(255) NOT NULL,
    description TEXT,
    goal TEXT, -- Objetivo final da trilha
    
    -- Categorização
    topic VARCHAR(255),
    tags TEXT[] DEFAULT '{}',
    
    -- Progresso
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN (
        'planned', 'active', 'paused', 'completed', 'archived'
    )),
    total_items INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    
    -- Datas
    target_completion TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para learning_paths
CREATE INDEX idx_learning_paths_user_id ON learning_paths(user_id);
CREATE INDEX idx_learning_paths_status ON learning_paths(status);
CREATE INDEX idx_learning_paths_topic ON learning_paths(topic);

-- RLS para learning_paths
ALTER TABLE learning_paths ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own learning paths" ON learning_paths
    FOR ALL USING (auth.uid() = user_id);

-- Trigger para updated_at
CREATE TRIGGER update_learning_paths_updated_at
    BEFORE UPDATE ON learning_paths
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- REVIEW_SESSIONS TABLE (Sessões de Revisão)
-- ============================================
CREATE TABLE IF NOT EXISTS review_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    learning_item_id UUID NOT NULL REFERENCES learning_items(id) ON DELETE CASCADE,
    
    -- Resultado da revisão
    quality INTEGER NOT NULL CHECK (quality >= 0 AND quality <= 5),
    -- 0: Completo esquecimento
    -- 1: Incorreto, lembrou ao ver resposta
    -- 2: Incorreto, mas parecia fácil ao ver
    -- 3: Correto com dificuldade
    -- 4: Correto após hesitação
    -- 5: Correto imediatamente
    
    -- Tempo da sessão
    time_spent_seconds INTEGER,
    
    -- Novos valores após revisão (calculados pelo algoritmo SM-2)
    new_ease_factor DECIMAL(3, 2),
    new_interval INTEGER,
    
    -- Timestamp
    reviewed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para review_sessions
CREATE INDEX idx_review_sessions_user_id ON review_sessions(user_id);
CREATE INDEX idx_review_sessions_item ON review_sessions(learning_item_id);
CREATE INDEX idx_review_sessions_date ON review_sessions(reviewed_at DESC);

-- RLS para review_sessions
ALTER TABLE review_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own review sessions" ON review_sessions
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- FUNCTIONS / PROCEDURES
-- ============================================

-- Função para calcular próxima revisão (SM-2 Algorithm)
CREATE OR REPLACE FUNCTION calculate_next_review(
    p_quality INTEGER,
    p_ease_factor DECIMAL,
    p_interval INTEGER
) RETURNS TABLE(
    new_ease_factor DECIMAL,
    new_interval INTEGER,
    next_review TIMESTAMPTZ
) AS $$
DECLARE
    ef DECIMAL;
    int_val INTEGER;
BEGIN
    -- Calcula novo ease factor
    ef := p_ease_factor + (0.1 - (5 - p_quality) * (0.08 + (5 - p_quality) * 0.02));
    IF ef < 1.3 THEN
        ef := 1.3;
    END IF;
    
    -- Calcula novo intervalo
    IF p_quality < 3 THEN
        int_val := 1; -- Reinicia se errou
    ELSIF p_interval = 0 THEN
        int_val := 1;
    ELSIF p_interval = 1 THEN
        int_val := 6;
    ELSE
        int_val := ROUND(p_interval * ef);
    END IF;
    
    RETURN QUERY SELECT 
        ef::DECIMAL(3,2),
        int_val,
        (NOW() + (int_val || ' days')::INTERVAL)::TIMESTAMPTZ;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- VIEWS
-- ============================================

-- View: Leads pendentes de follow-up
CREATE OR REPLACE VIEW v_pending_followups AS
SELECT 
    id,
    user_id,
    name,
    company,
    status,
    next_followup,
    last_contact,
    score,
    CASE 
        WHEN next_followup < NOW() THEN 'overdue'
        WHEN next_followup < NOW() + INTERVAL '1 day' THEN 'today'
        WHEN next_followup < NOW() + INTERVAL '7 days' THEN 'this_week'
        ELSE 'later'
    END as urgency
FROM leads
WHERE next_followup IS NOT NULL
  AND status NOT IN ('won', 'lost', 'inactive')
ORDER BY next_followup ASC;


-- View: Itens para revisar hoje
CREATE OR REPLACE VIEW v_items_to_review AS
SELECT 
    li.id,
    li.user_id,
    li.title,
    li.content_type,
    li.topic,
    li.next_review,
    li.review_count,
    li.ease_factor,
    lp.title as path_title
FROM learning_items li
LEFT JOIN learning_paths lp ON li.learning_path_id = lp.id
WHERE li.next_review <= NOW()
  AND li.status NOT IN ('mastered')
ORDER BY li.next_review ASC;


-- View: Funil de vendas por estágio
CREATE OR REPLACE VIEW v_sales_funnel AS
SELECT 
    user_id,
    status,
    COUNT(*) as count,
    COALESCE(SUM(deal_value), 0) as total_value,
    AVG(score) as avg_score
FROM leads
WHERE status NOT IN ('lost', 'inactive')
GROUP BY user_id, status;


-- View: Progresso de aprendizado por tópico
CREATE OR REPLACE VIEW v_learning_progress AS
SELECT 
    user_id,
    topic,
    COUNT(*) as total_items,
    COUNT(*) FILTER (WHERE status = 'completed' OR status = 'mastered') as completed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed' OR status = 'mastered') / COUNT(*), 1) as completion_rate,
    AVG(ease_factor) as avg_ease_factor
FROM learning_items
WHERE topic IS NOT NULL
GROUP BY user_id, topic;
