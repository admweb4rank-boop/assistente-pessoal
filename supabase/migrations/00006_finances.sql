-- ============================================
-- Migration: 00006 - Finances Module
-- Sistema de controle financeiro pessoal
-- ============================================

-- ============================================
-- FINANCE_ACCOUNTS TABLE (Contas/Carteiras)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Identificação
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'checking', 'savings', 'credit_card', 'investment', 'cash', 'wallet'
    institution VARCHAR(100), -- Banco/Corretora
    
    -- Saldo
    current_balance DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'BRL',
    
    -- Configurações
    is_active BOOLEAN DEFAULT true,
    include_in_total BOOLEAN DEFAULT true, -- Incluir no patrimônio total
    color VARCHAR(7), -- Cor hex para UI
    icon VARCHAR(10), -- Emoji
    
    -- Limites (para cartão de crédito)
    credit_limit DECIMAL(15, 2),
    closing_day INTEGER, -- Dia de fechamento
    due_day INTEGER, -- Dia de vencimento
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_finance_accounts_user ON finance_accounts(user_id);
CREATE INDEX idx_finance_accounts_type ON finance_accounts(type);

-- RLS
ALTER TABLE finance_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own accounts" ON finance_accounts
    FOR ALL USING (auth.uid() = user_id);

-- Trigger
CREATE TRIGGER update_finance_accounts_updated_at
    BEFORE UPDATE ON finance_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- FINANCE_CATEGORIES TABLE (Categorias)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_categories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- NULL = categoria do sistema
    
    -- Identificação
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'income', 'expense', 'transfer', 'investment'
    parent_id UUID REFERENCES finance_categories(id), -- Subcategorias
    
    -- Aparência
    icon VARCHAR(10),
    color VARCHAR(7),
    
    -- Status
    is_system BOOLEAN DEFAULT false, -- Categoria padrão do sistema
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_finance_categories_user ON finance_categories(user_id);
CREATE INDEX idx_finance_categories_type ON finance_categories(type);
CREATE INDEX idx_finance_categories_parent ON finance_categories(parent_id);

-- RLS
ALTER TABLE finance_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view system and own categories" ON finance_categories
    FOR SELECT USING (user_id IS NULL OR auth.uid() = user_id);

CREATE POLICY "Users can manage own categories" ON finance_categories
    FOR ALL USING (auth.uid() = user_id);

-- Inserir categorias padrão do sistema
INSERT INTO finance_categories (name, type, icon, color, is_system) VALUES
-- Receitas
('Salário', 'income', '💼', '#22c55e', true),
('Freelance', 'income', '💻', '#10b981', true),
('Investimentos', 'income', '📈', '#059669', true),
('Vendas', 'income', '🛒', '#14b8a6', true),
('Outros (Receita)', 'income', '💰', '#0d9488', true),

-- Despesas
('Moradia', 'expense', '🏠', '#ef4444', true),
('Alimentação', 'expense', '🍽️', '#f97316', true),
('Transporte', 'expense', '🚗', '#f59e0b', true),
('Saúde', 'expense', '🏥', '#eab308', true),
('Educação', 'expense', '📚', '#84cc16', true),
('Lazer', 'expense', '🎮', '#a855f7', true),
('Compras', 'expense', '🛍️', '#ec4899', true),
('Assinaturas', 'expense', '📱', '#8b5cf6', true),
('Impostos', 'expense', '📋', '#6366f1', true),
('Outros (Despesa)', 'expense', '💸', '#64748b', true),

-- Investimentos
('Ações', 'investment', '📊', '#3b82f6', true),
('Renda Fixa', 'investment', '🏦', '#0ea5e9', true),
('Fundos', 'investment', '📁', '#06b6d4', true),
('Cripto', 'investment', '🪙', '#f59e0b', true),
('Previdência', 'investment', '👴', '#8b5cf6', true)

ON CONFLICT DO NOTHING;


-- ============================================
-- FINANCE_TRANSACTIONS TABLE (Transações)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Conta
    account_id UUID NOT NULL REFERENCES finance_accounts(id) ON DELETE CASCADE,
    
    -- Tipo e valor
    type VARCHAR(20) NOT NULL, -- 'income', 'expense', 'transfer_in', 'transfer_out'
    amount DECIMAL(15, 2) NOT NULL,
    
    -- Descrição
    description VARCHAR(255) NOT NULL,
    notes TEXT,
    
    -- Categorização
    category_id UUID REFERENCES finance_categories(id),
    tags TEXT[] DEFAULT '{}',
    
    -- Data
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Recorrência
    is_recurring BOOLEAN DEFAULT false,
    recurrence_id UUID, -- ID do grupo de recorrência
    
    -- Transferência entre contas
    related_transaction_id UUID REFERENCES finance_transactions(id),
    
    -- Contexto (para análise do assistente)
    context JSONB DEFAULT '{}'::jsonb,
    -- {
    --   "mood": "stressed|neutral|happy",
    --   "impulse_buy": true/false,
    --   "planned": true/false,
    --   "source": "telegram|web|import"
    -- }
    
    -- Status
    is_confirmed BOOLEAN DEFAULT true, -- Para transações pendentes
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_finance_transactions_user ON finance_transactions(user_id);
CREATE INDEX idx_finance_transactions_account ON finance_transactions(account_id);
CREATE INDEX idx_finance_transactions_category ON finance_transactions(category_id);
CREATE INDEX idx_finance_transactions_date ON finance_transactions(transaction_date DESC);
CREATE INDEX idx_finance_transactions_type ON finance_transactions(type);
CREATE INDEX idx_finance_transactions_recurring ON finance_transactions(recurrence_id) WHERE recurrence_id IS NOT NULL;

-- RLS
ALTER TABLE finance_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own transactions" ON finance_transactions
    FOR ALL USING (auth.uid() = user_id);

-- Trigger
CREATE TRIGGER update_finance_transactions_updated_at
    BEFORE UPDATE ON finance_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- FINANCE_BUDGETS TABLE (Orçamentos)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_budgets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Categoria ou geral
    category_id UUID REFERENCES finance_categories(id), -- NULL = orçamento geral
    
    -- Período
    period_type VARCHAR(20) NOT NULL, -- 'monthly', 'weekly', 'yearly'
    period_start DATE NOT NULL,
    period_end DATE,
    
    -- Valores
    amount DECIMAL(15, 2) NOT NULL,
    spent DECIMAL(15, 2) DEFAULT 0,
    
    -- Alertas
    alert_at_percentage INTEGER DEFAULT 80, -- Alertar quando gastar X%
    is_notified BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_finance_budgets_user ON finance_budgets(user_id);
CREATE INDEX idx_finance_budgets_category ON finance_budgets(category_id);
CREATE INDEX idx_finance_budgets_period ON finance_budgets(period_start, period_end);

-- RLS
ALTER TABLE finance_budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own budgets" ON finance_budgets
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- FINANCE_GOALS TABLE (Metas Financeiras)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_goals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Identificação
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    
    -- Meta
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0,
    
    -- Prazo
    target_date DATE,
    
    -- Estratégia
    monthly_contribution DECIMAL(15, 2), -- Contribuição mensal sugerida
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'completed', 'cancelled'
    completed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_finance_goals_user ON finance_goals(user_id);
CREATE INDEX idx_finance_goals_status ON finance_goals(status);

-- RLS
ALTER TABLE finance_goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own goals" ON finance_goals
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- FINANCE_RECURRING TABLE (Transações Recorrentes)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_recurring (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Conta padrão
    account_id UUID REFERENCES finance_accounts(id),
    
    -- Template da transação
    type VARCHAR(20) NOT NULL, -- 'income', 'expense'
    amount DECIMAL(15, 2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    category_id UUID REFERENCES finance_categories(id),
    
    -- Recorrência
    frequency VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'yearly'
    day_of_month INTEGER, -- Para mensais
    day_of_week INTEGER, -- Para semanais (0-6)
    
    -- Período
    start_date DATE NOT NULL,
    end_date DATE, -- NULL = infinito
    
    -- Controle
    last_generated_date DATE,
    next_due_date DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_finance_recurring_user ON finance_recurring(user_id);
CREATE INDEX idx_finance_recurring_next_due ON finance_recurring(next_due_date);
CREATE INDEX idx_finance_recurring_active ON finance_recurring(is_active) WHERE is_active = true;

-- RLS
ALTER TABLE finance_recurring ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own recurring" ON finance_recurring
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- FINANCE_PATTERNS TABLE (Padrões Identificados)
-- ============================================
CREATE TABLE IF NOT EXISTS finance_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Tipo de padrão
    pattern_type VARCHAR(50) NOT NULL,
    -- 'emotional_spending', 'weekend_splurge', 'stress_buying',
    -- 'income_spike', 'expense_spike', 'saving_streak'
    
    -- Descrição
    title VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Dados do padrão
    pattern_data JSONB NOT NULL,
    -- {
    --   "trigger": "stress|weekend|payday",
    --   "avg_amount": 500,
    --   "frequency": "weekly",
    --   "categories": ["lazer", "compras"],
    --   "confidence": 0.85
    -- }
    
    -- Recomendação
    recommendation TEXT,
    
    -- Status
    is_acknowledged BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    
    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
);

-- Índices
CREATE INDEX idx_finance_patterns_user ON finance_patterns(user_id);
CREATE INDEX idx_finance_patterns_type ON finance_patterns(pattern_type);

-- RLS
ALTER TABLE finance_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own patterns" ON finance_patterns
    FOR ALL USING (auth.uid() = user_id);


-- ============================================
-- VIEWS
-- ============================================

-- View: Resumo financeiro do mês
CREATE OR REPLACE VIEW v_finance_monthly_summary AS
SELECT 
    user_id,
    DATE_TRUNC('month', transaction_date) AS month,
    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expenses,
    SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) AS balance,
    COUNT(*) AS transaction_count
FROM finance_transactions
WHERE type IN ('income', 'expense')
GROUP BY user_id, DATE_TRUNC('month', transaction_date);


-- View: Gastos por categoria (mês atual)
CREATE OR REPLACE VIEW v_finance_category_spending AS
SELECT 
    t.user_id,
    c.id AS category_id,
    c.name AS category_name,
    c.icon,
    c.color,
    SUM(t.amount) AS total_spent,
    COUNT(*) AS transaction_count,
    DATE_TRUNC('month', t.transaction_date) AS month
FROM finance_transactions t
JOIN finance_categories c ON t.category_id = c.id
WHERE t.type = 'expense'
GROUP BY t.user_id, c.id, c.name, c.icon, c.color, DATE_TRUNC('month', t.transaction_date);


-- View: Patrimônio total
CREATE OR REPLACE VIEW v_finance_net_worth AS
SELECT 
    user_id,
    SUM(CASE 
        WHEN type IN ('checking', 'savings', 'investment', 'cash', 'wallet') THEN current_balance
        WHEN type = 'credit_card' THEN -current_balance
        ELSE 0 
    END) AS net_worth,
    SUM(CASE WHEN type IN ('checking', 'savings', 'cash', 'wallet') THEN current_balance ELSE 0 END) AS liquid_assets,
    SUM(CASE WHEN type = 'investment' THEN current_balance ELSE 0 END) AS investments,
    SUM(CASE WHEN type = 'credit_card' THEN current_balance ELSE 0 END) AS credit_debt
FROM finance_accounts
WHERE is_active = true AND include_in_total = true
GROUP BY user_id;


-- ============================================
-- FUNCTIONS
-- ============================================

-- Função: Atualizar saldo da conta após transação
CREATE OR REPLACE FUNCTION update_account_balance()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE finance_accounts
        SET current_balance = current_balance + (
            CASE 
                WHEN NEW.type IN ('income', 'transfer_in') THEN NEW.amount
                WHEN NEW.type IN ('expense', 'transfer_out') THEN -NEW.amount
                ELSE 0
            END
        ),
        updated_at = NOW()
        WHERE id = NEW.account_id;
        
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE finance_accounts
        SET current_balance = current_balance - (
            CASE 
                WHEN OLD.type IN ('income', 'transfer_in') THEN OLD.amount
                WHEN OLD.type IN ('expense', 'transfer_out') THEN -OLD.amount
                ELSE 0
            END
        ),
        updated_at = NOW()
        WHERE id = OLD.account_id;
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- Reverter transação antiga
        UPDATE finance_accounts
        SET current_balance = current_balance - (
            CASE 
                WHEN OLD.type IN ('income', 'transfer_in') THEN OLD.amount
                WHEN OLD.type IN ('expense', 'transfer_out') THEN -OLD.amount
                ELSE 0
            END
        )
        WHERE id = OLD.account_id;
        
        -- Aplicar nova transação
        UPDATE finance_accounts
        SET current_balance = current_balance + (
            CASE 
                WHEN NEW.type IN ('income', 'transfer_in') THEN NEW.amount
                WHEN NEW.type IN ('expense', 'transfer_out') THEN -NEW.amount
                ELSE 0
            END
        ),
        updated_at = NOW()
        WHERE id = NEW.account_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar saldo
CREATE TRIGGER trigger_update_account_balance
    AFTER INSERT OR UPDATE OR DELETE ON finance_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_account_balance();


-- Função: Atualizar gasto do orçamento
CREATE OR REPLACE FUNCTION update_budget_spent()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.type = 'expense' AND NEW.category_id IS NOT NULL THEN
        UPDATE finance_budgets
        SET spent = (
            SELECT COALESCE(SUM(amount), 0)
            FROM finance_transactions
            WHERE user_id = NEW.user_id
              AND category_id = NEW.category_id
              AND type = 'expense'
              AND transaction_date >= period_start
              AND (period_end IS NULL OR transaction_date <= period_end)
        ),
        updated_at = NOW()
        WHERE user_id = NEW.user_id
          AND category_id = NEW.category_id
          AND is_active = true
          AND NEW.transaction_date >= period_start
          AND (period_end IS NULL OR NEW.transaction_date <= period_end);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_budget_spent
    AFTER INSERT OR UPDATE ON finance_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_budget_spent();


-- ============================================
-- MODO FINANCEIRO (Adicionar ao mode_prompts)
-- ============================================
INSERT INTO mode_prompts (mode_name, display_name, description, icon, system_prompt, greeting_template, priority_tools, tracked_metrics, is_system) VALUES
('finances', 'Finanças & Decisões', 'Foco em controle financeiro, investimentos e decisões conscientes', '💰',
'Você está no MODO FINANÇAS. Seu foco agora é:
- Registrar e categorizar transações
- Monitorar gastos vs orçamento
- Identificar padrões de gasto (especialmente emocionais)
- Ajudar em decisões financeiras com clareza
- Simular cenários de investimento/gastos
- Alertar sobre comportamentos recorrentes

Tom: Objetivo, sem julgamento, focado em consciência.
Perguntas típicas: "Esse gasto é planejado?", "Qual o contexto?", "Comparado com o mês passado?"

IMPORTANTE:
- Não julgue gastos, apenas mostre consequências
- Identifique se decisões vêm de estado emocional
- Sempre contextualize valores (% da renda, comparativo)
- Sugira reflexão antes de grandes decisões

Limites: Não dê conselhos de investimento específicos, apenas organize informações.',
'💰 *Modo Finanças ativado!*
O que vamos registrar ou analisar?',
ARRAY['finances', 'calendar', 'insights'],
ARRAY['spending', 'savings_rate', 'budget_adherence'],
true)
ON CONFLICT (mode_name) DO NOTHING;
