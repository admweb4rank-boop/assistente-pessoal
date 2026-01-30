-- =============================================
-- TB Personal OS - Conversas e Memória de Longo Prazo
-- Migration: 00009_conversations_memory.sql
-- =============================================

-- =============================================
-- HISTÓRICO DE CONVERSAS
-- =============================================

-- Sessões de conversa
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Metadados da sessão
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Contexto da sessão
    mode_id UUID REFERENCES user_modes(id),  -- Modo ativo durante a sessão
    topic TEXT,  -- Tópico principal detectado
    summary TEXT,  -- Resumo gerado da conversa
    
    -- Métricas
    message_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Mensagens individuais
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Conteúdo
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Metadados
    tokens INTEGER,
    source TEXT DEFAULT 'telegram',  -- telegram, web, api
    
    -- Análise
    intent TEXT,  -- Intenção detectada
    entities JSONB DEFAULT '[]',  -- Entidades extraídas
    sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    
    -- Ações resultantes
    actions_taken JSONB DEFAULT '[]',  -- Ex: [{"type": "task_created", "id": "..."}]
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================
-- MEMÓRIA DE LONGO PRAZO
-- =============================================

-- Memórias persistentes do usuário
CREATE TABLE IF NOT EXISTS user_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Classificação
    category TEXT NOT NULL CHECK (category IN (
        'preference',      -- Preferências do usuário
        'fact',           -- Fatos sobre o usuário
        'pattern',        -- Padrões de comportamento
        'relationship',   -- Relacionamentos mencionados
        'goal',           -- Objetivos de longo prazo
        'context',        -- Contexto importante
        'feedback'        -- Feedback sobre o assistente
    )),
    
    -- Conteúdo
    content TEXT NOT NULL,
    summary TEXT,  -- Versão resumida para busca
    
    -- Importância e relevância
    importance INTEGER DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    relevance_decay FLOAT DEFAULT 0.95,  -- Decaimento de relevância por dia
    
    -- Origem
    source_session_id UUID REFERENCES conversation_sessions(id),
    source_message_id UUID REFERENCES conversation_messages(id),
    
    -- Embedding para busca semântica (requer pgvector - adicionar depois)
    -- embedding VECTOR(768),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================
-- PADRÕES APRENDIDOS
-- =============================================

-- Padrões de comportamento aprendidos
CREATE TABLE IF NOT EXISTS learned_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tipo de padrão
    pattern_type TEXT NOT NULL CHECK (pattern_type IN (
        'time_preference',     -- Horários preferidos
        'task_category',       -- Categorias de tarefas comuns
        'communication_style', -- Estilo de comunicação preferido
        'priority_tendency',   -- Tendência de priorização
        'productivity_cycle',  -- Ciclos de produtividade
        'topic_interest',      -- Tópicos de interesse
        'response_preference', -- Como prefere respostas
        'workflow'             -- Fluxos de trabalho comuns
    )),
    
    -- Descrição do padrão
    name TEXT NOT NULL,
    description TEXT,
    
    -- Dados do padrão
    pattern_data JSONB NOT NULL,
    -- Exemplo: 
    -- time_preference: {"morning_start": "09:00", "focus_hours": [10, 11, 14, 15]}
    -- communication_style: {"preferred_length": "concise", "emoji_usage": true}
    -- productivity_cycle: {"peak_days": ["tue", "wed"], "low_days": ["mon"]}
    
    -- Confiança e amostras
    confidence FLOAT DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    sample_count INTEGER DEFAULT 0,
    
    -- Última validação
    last_validated_at TIMESTAMP WITH TIME ZONE,
    validation_count INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================
-- CONTEXTO DE DOCUMENTOS/CONHECIMENTO
-- =============================================

-- Base de conhecimento pessoal (para RAG)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Metadados
    title TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN (
        'document',    -- Documento enviado
        'note',        -- Nota pessoal
        'webpage',     -- Conteúdo de webpage
        'conversation',-- Extraído de conversa
        'manual'       -- Adicionado manualmente
    )),
    source_url TEXT,
    
    -- Conteúdo
    content TEXT NOT NULL,
    content_hash TEXT,  -- Para detectar duplicatas
    
    -- Chunks para RAG
    chunks JSONB DEFAULT '[]',  -- Array de chunks com embeddings
    
    -- Metadados de indexação
    indexed_at TIMESTAMP WITH TIME ZONE,
    chunk_count INTEGER DEFAULT 0,
    
    -- Categorização
    tags TEXT[] DEFAULT '{}',
    category TEXT,
    
    -- Status
    is_indexed BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================
-- FEEDBACK E CORREÇÕES
-- =============================================

-- Feedback do usuário sobre respostas
CREATE TABLE IF NOT EXISTS response_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_messages(id),
    
    -- Tipo de feedback
    feedback_type TEXT NOT NULL CHECK (feedback_type IN (
        'positive',     -- Resposta boa
        'negative',     -- Resposta ruim
        'correction',   -- Correção específica
        'preference'    -- Preferência aprendida
    )),
    
    -- Conteúdo
    original_response TEXT,
    feedback_content TEXT,
    corrected_response TEXT,
    
    -- Aplicação
    applied_to_memory BOOLEAN DEFAULT false,
    applied_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================
-- ÍNDICES
-- =============================================

-- Conversas
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user 
    ON conversation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_active 
    ON conversation_sessions(user_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session 
    ON conversation_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_user_time 
    ON conversation_messages(user_id, created_at DESC);

-- Memória
CREATE INDEX IF NOT EXISTS idx_user_memories_user_category 
    ON user_memories(user_id, category);
CREATE INDEX IF NOT EXISTS idx_user_memories_active 
    ON user_memories(user_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_memories_importance 
    ON user_memories(user_id, importance DESC);

-- Padrões
CREATE INDEX IF NOT EXISTS idx_learned_patterns_user_type 
    ON learned_patterns(user_id, pattern_type);
CREATE INDEX IF NOT EXISTS idx_learned_patterns_active 
    ON learned_patterns(user_id, is_active) WHERE is_active = true;

-- Knowledge Base
CREATE INDEX IF NOT EXISTS idx_knowledge_base_user 
    ON knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_indexed 
    ON knowledge_base(user_id, is_indexed);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_tags 
    ON knowledge_base USING GIN(tags);

-- Feedback
CREATE INDEX IF NOT EXISTS idx_response_feedback_user 
    ON response_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_response_feedback_message 
    ON response_feedback(message_id);

-- =============================================
-- TRIGGERS
-- =============================================

-- Atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_sessions_updated_at
    BEFORE UPDATE ON conversation_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_memories_updated_at
    BEFORE UPDATE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learned_patterns_updated_at
    BEFORE UPDATE ON learned_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Incrementar contador de mensagens na sessão
CREATE OR REPLACE FUNCTION increment_session_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversation_sessions 
    SET message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_increment_message_count
    AFTER INSERT ON conversation_messages
    FOR EACH ROW EXECUTE FUNCTION increment_session_message_count();

-- =============================================
-- VIEWS ÚTEIS
-- =============================================

-- Contexto recente do usuário
CREATE OR REPLACE VIEW v_user_recent_context AS
SELECT 
    u.id as user_id,
    u.full_name,
    -- Última sessão
    (SELECT json_build_object(
        'session_id', cs.id,
        'topic', cs.topic,
        'message_count', cs.message_count,
        'started_at', cs.started_at
    ) FROM conversation_sessions cs 
    WHERE cs.user_id = u.id AND cs.is_active = true 
    ORDER BY cs.started_at DESC LIMIT 1) as current_session,
    -- Últimas memórias relevantes
    (SELECT json_agg(json_build_object(
        'category', um.category,
        'content', um.content,
        'importance', um.importance
    ) ORDER BY um.importance DESC)
    FROM (SELECT * FROM user_memories WHERE user_id = u.id AND is_active = true LIMIT 10) um) as top_memories,
    -- Padrões ativos
    (SELECT json_agg(json_build_object(
        'type', lp.pattern_type,
        'name', lp.name,
        'data', lp.pattern_data,
        'confidence', lp.confidence
    ))
    FROM learned_patterns lp WHERE lp.user_id = u.id AND lp.is_active = true) as patterns
FROM users u;

-- =============================================
-- DADOS INICIAIS
-- =============================================

-- Inserir padrões base (serão atualizados pelo sistema)
-- Não inserimos nada - o sistema aprenderá

COMMENT ON TABLE conversation_sessions IS 'Sessões de conversa com o assistente';
COMMENT ON TABLE conversation_messages IS 'Mensagens individuais dentro das sessões';
COMMENT ON TABLE user_memories IS 'Memórias de longo prazo sobre o usuário';
COMMENT ON TABLE learned_patterns IS 'Padrões de comportamento aprendidos';
COMMENT ON TABLE knowledge_base IS 'Base de conhecimento pessoal para RAG';
COMMENT ON TABLE response_feedback IS 'Feedback do usuário para melhoria contínua';
