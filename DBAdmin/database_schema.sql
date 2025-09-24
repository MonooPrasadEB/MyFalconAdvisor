-- MyFalconAdvisor PostgreSQL Database Schema
-- Designed to support multi-agent AI investment advisory platform

-- Enable UUID extension for better ID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USER MANAGEMENT TABLES
-- ============================================================================

-- Users table - Core user information
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE
);

-- User profiles - Extended demographic and financial information
CREATE TABLE user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    age INTEGER,
    annual_income DECIMAL(15,2),
    net_worth DECIMAL(15,2),
    marital_status VARCHAR(20) CHECK (marital_status IN ('single', 'married', 'divorced', 'widowed')),
    dependents INTEGER DEFAULT 0,
    employment_status VARCHAR(30),
    occupation VARCHAR(100),
    emergency_fund_months INTEGER,
    debt_to_income_ratio DECIMAL(5,4),
    monthly_savings_rate DECIMAL(5,4),
    current_retirement_savings DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Risk assessment profiles
CREATE TABLE risk_profiles (
    risk_profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    assessment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    investment_experience VARCHAR(20) CHECK (investment_experience IN ('beginner', 'intermediate', 'advanced', 'expert')),
    risk_tolerance VARCHAR(20) CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
    time_horizon INTEGER, -- years
    primary_goal VARCHAR(30) CHECK (primary_goal IN ('retirement', 'wealth_building', 'income_generation', 'capital_preservation')),
    secondary_goals TEXT[], -- Array of goals
    risk_comfort_level INTEGER CHECK (risk_comfort_level BETWEEN 1 AND 10),
    volatility_tolerance INTEGER CHECK (volatility_tolerance BETWEEN 1 AND 10),
    liquidity_needs INTEGER CHECK (liquidity_needs BETWEEN 1 AND 10),
    loss_tolerance_percent DECIMAL(5,2),
    risk_score DECIMAL(4,2) CHECK (risk_score BETWEEN 1 AND 10),
    recommended_equity_allocation DECIMAL(5,4),
    loss_aversion_score DECIMAL(4,2) DEFAULT 1.0,
    overconfidence_score DECIMAL(4,2) DEFAULT 1.0,
    home_bias_score DECIMAL(4,2) DEFAULT 1.0,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    preference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    esg_investing BOOLEAN DEFAULT FALSE,
    sector_preferences TEXT[], -- Array of preferred sectors
    sector_restrictions TEXT[], -- Array of restricted sectors
    international_exposure BOOLEAN DEFAULT TRUE,
    alternative_investments BOOLEAN DEFAULT FALSE,
    rebalancing_frequency VARCHAR(20) CHECK (rebalancing_frequency IN ('monthly', 'quarterly', 'semi-annually', 'annually')),
    notification_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. PORTFOLIO MANAGEMENT TABLES
-- ============================================================================

-- Portfolios
CREATE TABLE portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(100) NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) DEFAULT 0,
    portfolio_type VARCHAR(20) CHECK (portfolio_type IN ('taxable', 'ira', 'roth_ira', '401k', 'other')),
    is_primary BOOLEAN DEFAULT FALSE,
    portfolio_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio holdings/assets
CREATE TABLE portfolio_assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    asset_name VARCHAR(200),
    asset_type VARCHAR(20) CHECK (asset_type IN ('stock', 'etf', 'bond', 'mutual_fund', 'crypto', 'other')),
    quantity DECIMAL(15,6) NOT NULL,
    average_cost DECIMAL(12,4),
    current_price DECIMAL(12,4),
    market_value DECIMAL(15,2),
    allocation_percent DECIMAL(5,4),
    sector VARCHAR(50),
    industry VARCHAR(100),
    country VARCHAR(50) DEFAULT 'US',
    currency VARCHAR(3) DEFAULT 'USD',
    dividend_yield DECIMAL(6,4),
    expense_ratio DECIMAL(6,4), -- For ETFs/Mutual Funds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, symbol)
);

-- Portfolio performance metrics (calculated periodically)
CREATE TABLE portfolio_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    calculation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_return_1d DECIMAL(8,6),
    total_return_1w DECIMAL(8,6),
    total_return_1m DECIMAL(8,6),
    total_return_3m DECIMAL(8,6),
    total_return_1y DECIMAL(8,6),
    portfolio_beta DECIMAL(6,4),
    portfolio_volatility DECIMAL(8,6), -- Annualized
    sharpe_ratio DECIMAL(8,4),
    sortino_ratio DECIMAL(8,4),
    value_at_risk_95 DECIMAL(12,4), -- 95% VaR
    expected_shortfall_95 DECIMAL(12,4), -- Conditional VaR
    max_drawdown DECIMAL(8,6),
    effective_number_stocks DECIMAL(8,4),
    sector_concentration DECIMAL(8,6), -- Herfindahl index
    esg_score DECIMAL(4,2)
);

-- ============================================================================
-- 3. MARKET DATA TABLES
-- ============================================================================

-- Securities master data
CREATE TABLE securities (
    symbol VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(200),
    sector VARCHAR(50),
    industry VARCHAR(100),
    country VARCHAR(50) DEFAULT 'US',
    currency VARCHAR(3) DEFAULT 'USD',
    market_cap BIGINT,
    shares_outstanding BIGINT,
    ipo_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    exchange VARCHAR(20),
    asset_type VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Real-time market data cache
CREATE TABLE market_data (
    data_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) REFERENCES securities(symbol),
    data_date DATE NOT NULL,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    volume BIGINT,
    adjusted_close DECIMAL(12,4),
    dividend_amount DECIMAL(8,4),
    split_coefficient DECIMAL(8,4) DEFAULT 1.0,
    data_source VARCHAR(20) DEFAULT 'yahoo_finance',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, data_date)
);

-- Fundamental data cache
CREATE TABLE fundamental_data (
    fundamental_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) REFERENCES securities(symbol),
    data_date DATE NOT NULL,
    pe_ratio DECIMAL(8,4),
    pb_ratio DECIMAL(8,4),
    peg_ratio DECIMAL(8,4),
    dividend_yield DECIMAL(6,4),
    beta DECIMAL(6,4),
    eps DECIMAL(8,4),
    revenue BIGINT,
    net_income BIGINT,
    book_value_per_share DECIMAL(8,4),
    debt_to_equity DECIMAL(8,4),
    roe DECIMAL(6,4),
    roa DECIMAL(6,4),
    profit_margin DECIMAL(6,4),
    data_source VARCHAR(20) DEFAULT 'alpha_vantage',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, data_date, data_source)
);

-- Economic indicators (FRED data)
CREATE TABLE economic_indicators (
    indicator_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_code VARCHAR(50) NOT NULL, -- e.g., 'GDP', 'UNRATE', 'FEDFUNDS'
    indicator_name VARCHAR(200),
    data_date DATE NOT NULL,
    value DECIMAL(15,6),
    units VARCHAR(50),
    frequency VARCHAR(20), -- daily, weekly, monthly, quarterly, annual
    data_source VARCHAR(20) DEFAULT 'fred',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator_code, data_date)
);

-- ============================================================================
-- 4. TRANSACTION AND EXECUTION TABLES
-- ============================================================================

-- Trade orders and executions
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'TRANSFER')),
    quantity DECIMAL(15,6) NOT NULL,
    price DECIMAL(12,4),
    total_amount DECIMAL(15,2),
    fees DECIMAL(8,2) DEFAULT 0,
    tax_amount DECIMAL(8,2) DEFAULT 0,
    order_type VARCHAR(20) DEFAULT 'market', -- market, limit, stop, etc.
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'executed', 'cancelled', 'failed')),
    execution_date TIMESTAMP WITH TIME ZONE,
    settlement_date DATE,
    broker_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trade recommendations from AI agents
CREATE TABLE trade_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    agent_type VARCHAR(30) CHECK (agent_type IN ('advisor', 'compliance', 'execution')),
    recommendation_type VARCHAR(20) CHECK (recommendation_type IN ('BUY', 'SELL', 'HOLD', 'REBALANCE')),
    symbol VARCHAR(20),
    recommended_quantity DECIMAL(15,6),
    recommended_price DECIMAL(12,4),
    reasoning TEXT,
    confidence_score DECIMAL(4,3), -- 0.000 to 1.000
    risk_score DECIMAL(4,2),
    expected_return DECIMAL(8,4),
    time_horizon_days INTEGER,
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected', 'executed', 'expired')),
    user_response VARCHAR(20), -- approved, rejected, modified
    user_response_notes TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. COMPLIANCE AND AUDIT TABLES
-- ============================================================================

-- Compliance checks and validations
CREATE TABLE compliance_checks (
    check_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    portfolio_id UUID REFERENCES portfolios(portfolio_id),
    transaction_id UUID REFERENCES transactions(transaction_id),
    recommendation_id UUID REFERENCES trade_recommendations(recommendation_id),
    check_type VARCHAR(30) CHECK (check_type IN ('suitability', 'concentration', 'liquidity', 'regulatory', 'risk_limit')),
    rule_name VARCHAR(100),
    rule_description TEXT,
    check_result VARCHAR(20) CHECK (check_result IN ('pass', 'fail', 'warning')),
    violation_details JSONB,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    auto_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Immutable audit trail for all system actions
CREATE TABLE audit_trail (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    entity_type VARCHAR(50) NOT NULL, -- 'user', 'portfolio', 'transaction', etc.
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'execute', etc.
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- This table should be append-only (no updates/deletes)
    CONSTRAINT no_updates CHECK (updated_at IS NULL)
);

-- ============================================================================
-- 6. AI AGENT INTERACTION TABLES
-- ============================================================================

-- Conversation sessions with AI agents
CREATE TABLE ai_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    session_type VARCHAR(30) CHECK (session_type IN ('advisory', 'compliance', 'execution', 'general')),
    status VARCHAR(20) CHECK (status IN ('active', 'completed', 'terminated')),
    context_data JSONB, -- Store conversation context
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    total_messages INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0
);

-- Individual messages in AI conversations
CREATE TABLE ai_messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES ai_sessions(session_id) ON DELETE CASCADE,
    agent_type VARCHAR(30) CHECK (agent_type IN ('user', 'advisor', 'compliance', 'execution', 'supervisor')),
    message_type VARCHAR(20) CHECK (message_type IN ('query', 'response', 'recommendation', 'approval_request', 'system')),
    message_content TEXT NOT NULL,
    message_metadata JSONB, -- Store additional context, confidence scores, etc.
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent coordination and workflow states
CREATE TABLE agent_workflows (
    workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES ai_sessions(session_id) ON DELETE CASCADE,
    workflow_type VARCHAR(50), -- 'portfolio_analysis', 'trade_execution', 'compliance_check'
    current_state VARCHAR(50),
    workflow_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- ============================================================================
-- 7. INDEXES FOR PERFORMANCE
-- ============================================================================

-- User-related indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_risk_profiles_user_id ON risk_profiles(user_id);
CREATE INDEX idx_risk_profiles_current ON risk_profiles(user_id) WHERE is_current = TRUE;

-- Portfolio-related indexes
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolio_assets_portfolio_id ON portfolio_assets(portfolio_id);
CREATE INDEX idx_portfolio_assets_symbol ON portfolio_assets(symbol);
CREATE INDEX idx_portfolio_metrics_portfolio_id ON portfolio_metrics(portfolio_id);
CREATE INDEX idx_portfolio_metrics_date ON portfolio_metrics(calculation_date DESC);

-- Market data indexes
CREATE INDEX idx_market_data_symbol_date ON market_data(symbol, data_date DESC);
CREATE INDEX idx_fundamental_data_symbol_date ON fundamental_data(symbol, data_date DESC);
CREATE INDEX idx_economic_indicators_code_date ON economic_indicators(indicator_code, data_date DESC);

-- Transaction indexes
CREATE INDEX idx_transactions_portfolio_id ON transactions(portfolio_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_date ON transactions(execution_date DESC);
CREATE INDEX idx_transactions_status ON transactions(status);

-- AI and compliance indexes
CREATE INDEX idx_compliance_checks_user_id ON compliance_checks(user_id);
CREATE INDEX idx_compliance_checks_result ON compliance_checks(check_result);
CREATE INDEX idx_audit_trail_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_trail_user_date ON audit_trail(user_id, created_at DESC);
CREATE INDEX idx_ai_sessions_user_id ON ai_sessions(user_id);
CREATE INDEX idx_ai_messages_session_id ON ai_messages(session_id, created_at);

-- ============================================================================
-- 8. VIEWS FOR COMMON QUERIES
-- ============================================================================

-- User portfolio summary view
CREATE VIEW user_portfolio_summary AS
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    p.portfolio_id,
    p.portfolio_name,
    p.total_value,
    COUNT(pa.asset_id) as total_positions,
    SUM(CASE WHEN pa.asset_type = 'stock' THEN pa.market_value ELSE 0 END) as stock_value,
    SUM(CASE WHEN pa.asset_type = 'bond' THEN pa.market_value ELSE 0 END) as bond_value,
    SUM(CASE WHEN pa.asset_type = 'etf' THEN pa.market_value ELSE 0 END) as etf_value,
    rp.risk_tolerance,
    rp.recommended_equity_allocation
FROM users u
JOIN portfolios p ON u.user_id = p.user_id
LEFT JOIN portfolio_assets pa ON p.portfolio_id = pa.portfolio_id
LEFT JOIN risk_profiles rp ON u.user_id = rp.user_id AND rp.is_current = TRUE
GROUP BY u.user_id, u.first_name, u.last_name, p.portfolio_id, p.portfolio_name, 
         p.total_value, rp.risk_tolerance, rp.recommended_equity_allocation;

-- Recent transactions view
CREATE VIEW recent_transactions AS
SELECT 
    t.transaction_id,
    u.first_name || ' ' || u.last_name as user_name,
    p.portfolio_name,
    t.symbol,
    s.company_name,
    t.transaction_type,
    t.quantity,
    t.price,
    t.total_amount,
    t.status,
    t.execution_date,
    t.created_at
FROM transactions t
JOIN portfolios p ON t.portfolio_id = p.portfolio_id
JOIN users u ON t.user_id = u.user_id
LEFT JOIN securities s ON t.symbol = s.symbol
WHERE t.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY t.created_at DESC;

-- ============================================================================
-- 9. FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at columns
CREATE TRIGGER tr_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_portfolios_updated_at BEFORE UPDATE ON portfolios FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_portfolio_assets_updated_at BEFORE UPDATE ON portfolio_assets FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_securities_updated_at BEFORE UPDATE ON securities FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_trade_recommendations_updated_at BEFORE UPDATE ON trade_recommendations FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to automatically create audit trail entries
CREATE OR REPLACE FUNCTION create_audit_trail()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (entity_type, entity_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.user_id, 'delete', row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (entity_type, entity_id, action, old_values, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.user_id, 'update', row_to_json(OLD), row_to_json(NEW), NEW.user_id);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (entity_type, entity_id, action, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.user_id, 'create', row_to_json(NEW), NEW.user_id);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Audit triggers for critical tables
CREATE TRIGGER tr_portfolios_audit AFTER INSERT OR UPDATE OR DELETE ON portfolios FOR EACH ROW EXECUTE FUNCTION create_audit_trail();
CREATE TRIGGER tr_transactions_audit AFTER INSERT OR UPDATE OR DELETE ON transactions FOR EACH ROW EXECUTE FUNCTION create_audit_trail();
CREATE TRIGGER tr_trade_recommendations_audit AFTER INSERT OR UPDATE OR DELETE ON trade_recommendations FOR EACH ROW EXECUTE FUNCTION create_audit_trail();

-- ============================================================================
-- 10. SAMPLE DATA INSERTION (Optional - for testing)
-- ============================================================================

-- This section can be used to populate the database with sample data
-- based on your existing JSON files and CSV mock data

-- Example: Insert sample users (adapt based on your MOCK_DATA.csv)
/*
INSERT INTO users (email, password_hash, first_name, last_name, phone) VALUES
('ywayper0@sohu.com', '$2b$12$example_hash', 'Yardley', 'Wayper', '+1-408-813-4589'),
('tmellem1@adobe.com', '$2b$12$example_hash', 'Tobe', 'Mellem', '+1-408-813-4589');
*/

-- ============================================================================
-- 11. DATABASE PERMISSIONS AND SECURITY
-- ============================================================================

-- Create application user with limited permissions
-- CREATE USER myfalcon_app WITH PASSWORD 'secure_password_here';

-- Grant necessary permissions
-- GRANT CONNECT ON DATABASE myfalconadvisor_db TO myfalcon_app;
-- GRANT USAGE ON SCHEMA public TO myfalcon_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO myfalcon_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO myfalcon_app;

-- Row Level Security (RLS) examples
-- ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY portfolio_user_policy ON portfolios FOR ALL TO myfalcon_app USING (user_id = current_setting('app.current_user_id')::UUID);

COMMENT ON DATABASE myfalconadvisor_db IS 'MyFalconAdvisor - AI Investment Advisory Platform Database';
