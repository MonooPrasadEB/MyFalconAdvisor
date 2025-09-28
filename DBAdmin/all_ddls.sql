--
-- PostgreSQL database dump
--

\restrict ixpiHC2H6zQQxND1g9RI1N4yFHtbGduBp64PwsP3hj4waFGy9YhtWKjf9aUHNrQ

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: create_audit_trail(); Type: FUNCTION; Schema: public; Owner: avnadmin
--

CREATE FUNCTION public.create_audit_trail() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.create_audit_trail() OWNER TO avnadmin;

--
-- Name: update_updated_at(); Type: FUNCTION; Schema: public; Owner: avnadmin
--

CREATE FUNCTION public.update_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at() OWNER TO avnadmin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.accounts (
    account_id text NOT NULL,
    user_id text,
    account_type text,
    base_currency text,
    opened_date timestamp with time zone,
    status text
);


ALTER TABLE public.accounts OWNER TO avnadmin;

--
-- Name: agent_workflows; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.agent_workflows (
    workflow_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid,
    workflow_type character varying(50),
    current_state character varying(50),
    workflow_data jsonb,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp with time zone,
    status character varying(20),
    CONSTRAINT agent_workflows_status_check CHECK (((status)::text = ANY ((ARRAY['running'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[])))
);


ALTER TABLE public.agent_workflows OWNER TO avnadmin;

--
-- Name: ai_messages; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.ai_messages (
    message_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid,
    agent_type character varying(30),
    message_type character varying(20),
    message_content text NOT NULL,
    message_metadata jsonb,
    tokens_used integer,
    processing_time_ms integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ai_messages_agent_type_check CHECK (((agent_type)::text = ANY ((ARRAY['user'::character varying, 'advisor'::character varying, 'compliance'::character varying, 'execution'::character varying, 'supervisor'::character varying])::text[]))),
    CONSTRAINT ai_messages_message_type_check CHECK (((message_type)::text = ANY ((ARRAY['query'::character varying, 'response'::character varying, 'recommendation'::character varying, 'approval_request'::character varying, 'system'::character varying])::text[])))
);


ALTER TABLE public.ai_messages OWNER TO avnadmin;

--
-- Name: ai_sessions; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.ai_sessions (
    session_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    session_type character varying(30),
    status character varying(20),
    context_data jsonb,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ended_at timestamp with time zone,
    total_messages integer DEFAULT 0,
    total_tokens_used integer DEFAULT 0,
    CONSTRAINT ai_sessions_session_type_check CHECK (((session_type)::text = ANY ((ARRAY['advisory'::character varying, 'compliance'::character varying, 'execution'::character varying, 'general'::character varying])::text[]))),
    CONSTRAINT ai_sessions_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'completed'::character varying, 'terminated'::character varying])::text[])))
);


ALTER TABLE public.ai_sessions OWNER TO avnadmin;

--
-- Name: audit_trail; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.audit_trail (
    audit_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(255) NOT NULL,
    action character varying(50) NOT NULL,
    old_values jsonb,
    new_values jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.audit_trail OWNER TO avnadmin;

--
-- Name: compliance_checks; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.compliance_checks (
    check_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    portfolio_id uuid,
    transaction_id uuid,
    recommendation_id uuid,
    check_type character varying(30),
    rule_name character varying(100),
    rule_description text,
    check_result character varying(20),
    violation_details jsonb,
    severity character varying(20),
    auto_resolved boolean DEFAULT false,
    resolution_notes text,
    checked_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp with time zone,
    CONSTRAINT compliance_checks_check_result_check CHECK (((check_result)::text = ANY ((ARRAY['pass'::character varying, 'fail'::character varying, 'warning'::character varying])::text[]))),
    CONSTRAINT compliance_checks_check_type_check CHECK (((check_type)::text = ANY ((ARRAY['suitability'::character varying, 'concentration'::character varying, 'liquidity'::character varying, 'regulatory'::character varying, 'risk_limit'::character varying])::text[]))),
    CONSTRAINT compliance_checks_severity_check CHECK (((severity)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'critical'::character varying])::text[])))
);


ALTER TABLE public.compliance_checks OWNER TO avnadmin;

--
-- Name: economic_indicators; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.economic_indicators (
    indicator_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    indicator_code character varying(50) NOT NULL,
    indicator_name character varying(200),
    data_date date NOT NULL,
    value numeric(15,6),
    units character varying(50),
    frequency character varying(20),
    data_source character varying(20) DEFAULT 'fred'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.economic_indicators OWNER TO avnadmin;

--
-- Name: executions; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.executions (
    exec_id text NOT NULL,
    order_id text,
    filled_quantity bigint,
    fill_price numeric(18,2),
    exec_timestamp timestamp with time zone
);


ALTER TABLE public.executions OWNER TO avnadmin;

--
-- Name: fundamental_data; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.fundamental_data (
    fundamental_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    symbol character varying(20),
    data_date date NOT NULL,
    pe_ratio numeric(8,4),
    pb_ratio numeric(8,4),
    peg_ratio numeric(8,4),
    dividend_yield numeric(6,4),
    beta numeric(6,4),
    eps numeric(8,4),
    revenue bigint,
    net_income bigint,
    book_value_per_share numeric(8,4),
    debt_to_equity numeric(8,4),
    roe numeric(6,4),
    roa numeric(6,4),
    profit_margin numeric(6,4),
    data_source character varying(20) DEFAULT 'alpha_vantage'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.fundamental_data OWNER TO avnadmin;

--
-- Name: interactions; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.interactions (
    interaction_id text NOT NULL,
    account_id text,
    "timestamp" timestamp with time zone,
    channel text,
    message text
);


ALTER TABLE public.interactions OWNER TO avnadmin;

--
-- Name: kyc_status; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.kyc_status (
    user_id text NOT NULL,
    kyc_status text,
    aml_screening text,
    document_type text,
    document_last_updated timestamp with time zone
);


ALTER TABLE public.kyc_status OWNER TO avnadmin;

--
-- Name: market_data; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.market_data (
    data_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    symbol character varying(20),
    data_date date NOT NULL,
    open_price numeric(12,4),
    high_price numeric(12,4),
    low_price numeric(12,4),
    close_price numeric(12,4),
    volume bigint,
    adjusted_close numeric(12,4),
    dividend_amount numeric(8,4),
    split_coefficient numeric(8,4) DEFAULT 1.0,
    data_source character varying(20) DEFAULT 'yahoo_finance'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.market_data OWNER TO avnadmin;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.orders (
    order_id text NOT NULL,
    account_id text,
    ticker text,
    sector text,
    quantity bigint,
    order_type text,
    limit_price numeric(18,2),
    "timestamp" timestamp with time zone,
    time_in_force text
);


ALTER TABLE public.orders OWNER TO avnadmin;

--
-- Name: portfolio_assets; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.portfolio_assets (
    asset_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    portfolio_id uuid,
    symbol character varying(20) NOT NULL,
    asset_name character varying(200),
    asset_type character varying(20),
    quantity numeric(15,6) NOT NULL,
    average_cost numeric(12,4),
    current_price numeric(12,4),
    market_value numeric(15,2),
    allocation_percent numeric(5,4),
    sector character varying(50),
    industry character varying(100),
    country character varying(50) DEFAULT 'US'::character varying,
    currency character varying(3) DEFAULT 'USD'::character varying,
    dividend_yield numeric(6,4),
    expense_ratio numeric(6,4),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT portfolio_assets_asset_type_check CHECK (((asset_type)::text = ANY ((ARRAY['stock'::character varying, 'etf'::character varying, 'bond'::character varying, 'mutual_fund'::character varying, 'crypto'::character varying, 'other'::character varying])::text[])))
);


ALTER TABLE public.portfolio_assets OWNER TO avnadmin;

--
-- Name: portfolio_metrics; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.portfolio_metrics (
    metric_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    portfolio_id uuid,
    calculation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    total_return_1d numeric(8,6),
    total_return_1w numeric(8,6),
    total_return_1m numeric(8,6),
    total_return_3m numeric(8,6),
    total_return_1y numeric(8,6),
    portfolio_beta numeric(6,4),
    portfolio_volatility numeric(8,6),
    sharpe_ratio numeric(8,4),
    sortino_ratio numeric(8,4),
    value_at_risk_95 numeric(12,4),
    expected_shortfall_95 numeric(12,4),
    max_drawdown numeric(8,6),
    effective_number_stocks numeric(8,4),
    sector_concentration numeric(8,6),
    esg_score numeric(4,2)
);


ALTER TABLE public.portfolio_metrics OWNER TO avnadmin;

--
-- Name: portfolios; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.portfolios (
    portfolio_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    portfolio_name character varying(100) NOT NULL,
    total_value numeric(15,2) NOT NULL,
    cash_balance numeric(15,2) DEFAULT 0,
    portfolio_type character varying(20),
    is_primary boolean DEFAULT false,
    portfolio_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT portfolios_portfolio_type_check CHECK (((portfolio_type)::text = ANY ((ARRAY['taxable'::character varying, 'ira'::character varying, 'roth_ira'::character varying, '401k'::character varying, 'other'::character varying])::text[])))
);


ALTER TABLE public.portfolios OWNER TO avnadmin;

--
-- Name: positions; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.positions (
    account_id text NOT NULL,
    ticker text NOT NULL,
    sector text,
    quantity bigint,
    avg_cost numeric(18,4)
);


ALTER TABLE public.positions OWNER TO avnadmin;

--
-- Name: recommendations; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.recommendations (
    rec_id text NOT NULL,
    account_id text,
    ticker text,
    action text,
    percentage bigint,
    rationale text,
    created_at timestamp with time zone
);


ALTER TABLE public.recommendations OWNER TO avnadmin;

--
-- Name: risk_profiles; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.risk_profiles (
    risk_profile_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    assessment_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    investment_experience character varying(20),
    risk_tolerance character varying(20),
    time_horizon integer,
    primary_goal character varying(30),
    secondary_goals text[],
    risk_comfort_level integer,
    volatility_tolerance integer,
    liquidity_needs integer,
    loss_tolerance_percent numeric(5,2),
    risk_score numeric(4,2),
    recommended_equity_allocation numeric(5,4),
    loss_aversion_score numeric(4,2) DEFAULT 1.0,
    overconfidence_score numeric(4,2) DEFAULT 1.0,
    home_bias_score numeric(4,2) DEFAULT 1.0,
    is_current boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT risk_profiles_investment_experience_check CHECK (((investment_experience)::text = ANY ((ARRAY['beginner'::character varying, 'intermediate'::character varying, 'advanced'::character varying, 'expert'::character varying])::text[]))),
    CONSTRAINT risk_profiles_liquidity_needs_check CHECK (((liquidity_needs >= 1) AND (liquidity_needs <= 10))),
    CONSTRAINT risk_profiles_primary_goal_check CHECK (((primary_goal)::text = ANY ((ARRAY['retirement'::character varying, 'wealth_building'::character varying, 'income_generation'::character varying, 'capital_preservation'::character varying])::text[]))),
    CONSTRAINT risk_profiles_risk_comfort_level_check CHECK (((risk_comfort_level >= 1) AND (risk_comfort_level <= 10))),
    CONSTRAINT risk_profiles_risk_score_check CHECK (((risk_score >= (1)::numeric) AND (risk_score <= (10)::numeric))),
    CONSTRAINT risk_profiles_risk_tolerance_check CHECK (((risk_tolerance)::text = ANY ((ARRAY['conservative'::character varying, 'moderate'::character varying, 'aggressive'::character varying])::text[]))),
    CONSTRAINT risk_profiles_volatility_tolerance_check CHECK (((volatility_tolerance >= 1) AND (volatility_tolerance <= 10)))
);


ALTER TABLE public.risk_profiles OWNER TO avnadmin;

--
-- Name: securities; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.securities (
    symbol character varying(20) NOT NULL,
    company_name character varying(200),
    sector character varying(50),
    industry character varying(100),
    country character varying(50) DEFAULT 'US'::character varying,
    currency character varying(3) DEFAULT 'USD'::character varying,
    market_cap bigint,
    shares_outstanding bigint,
    ipo_date date,
    is_active boolean DEFAULT true,
    exchange character varying(20),
    asset_type character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.securities OWNER TO avnadmin;

--
-- Name: transactions; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.transactions (
    transaction_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    portfolio_id uuid,
    user_id text NOT NULL,
    symbol character varying(20) NOT NULL,
    transaction_type character varying(10),
    quantity numeric(15,6) NOT NULL,
    price numeric(12,4),
    total_amount numeric(15,2),
    fees numeric(8,2) DEFAULT 0,
    order_type character varying(20) DEFAULT 'market'::character varying,
    status character varying(20),
    execution_date timestamp with time zone,
    broker_reference character varying(100),
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT transactions_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'executed'::character varying, 'cancelled'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT transactions_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['BUY'::character varying, 'SELL'::character varying, 'DIVIDEND'::character varying, 'SPLIT'::character varying, 'TRANSFER'::character varying])::text[])))
);


ALTER TABLE public.transactions OWNER TO avnadmin;

--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.user_preferences (
    preference_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    esg_investing boolean DEFAULT false,
    sector_preferences text[],
    sector_restrictions text[],
    international_exposure boolean DEFAULT true,
    alternative_investments boolean DEFAULT false,
    rebalancing_frequency character varying(20),
    notification_preferences jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_preferences_rebalancing_frequency_check CHECK (((rebalancing_frequency)::text = ANY ((ARRAY['monthly'::character varying, 'quarterly'::character varying, 'semi-annually'::character varying, 'annually'::character varying])::text[])))
);


ALTER TABLE public.user_preferences OWNER TO avnadmin;

--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.user_profiles (
    profile_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    age integer,
    annual_income numeric(15,2),
    net_worth numeric(15,2),
    marital_status character varying(20),
    dependents integer DEFAULT 0,
    employment_status character varying(30),
    occupation character varying(100),
    emergency_fund_months integer,
    debt_to_income_ratio numeric(5,4),
    monthly_savings_rate numeric(5,4),
    current_retirement_savings numeric(15,2),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_profiles_marital_status_check CHECK (((marital_status)::text = ANY ((ARRAY['single'::character varying, 'married'::character varying, 'divorced'::character varying, 'widowed'::character varying])::text[])))
);


ALTER TABLE public.user_profiles OWNER TO avnadmin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: avnadmin
--

CREATE TABLE public.users (
    user_id text DEFAULT public.uuid_generate_v4() NOT NULL,
    email character varying(255) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    dob date,
    risk_profile text,
    objective text,
    pep_flag boolean,
    annual_income_usd numeric(18,2),
    net_worth_usd numeric(18,2)
);


ALTER TABLE public.users OWNER TO avnadmin;

--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (account_id);


--
-- Name: agent_workflows agent_workflows_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.agent_workflows
    ADD CONSTRAINT agent_workflows_pkey PRIMARY KEY (workflow_id);


--
-- Name: ai_messages ai_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.ai_messages
    ADD CONSTRAINT ai_messages_pkey PRIMARY KEY (message_id);


--
-- Name: ai_sessions ai_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.ai_sessions
    ADD CONSTRAINT ai_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: audit_trail audit_trail_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.audit_trail
    ADD CONSTRAINT audit_trail_pkey PRIMARY KEY (audit_id);


--
-- Name: compliance_checks compliance_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.compliance_checks
    ADD CONSTRAINT compliance_checks_pkey PRIMARY KEY (check_id);


--
-- Name: economic_indicators economic_indicators_indicator_code_data_date_key; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.economic_indicators
    ADD CONSTRAINT economic_indicators_indicator_code_data_date_key UNIQUE (indicator_code, data_date);


--
-- Name: economic_indicators economic_indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.economic_indicators
    ADD CONSTRAINT economic_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: executions executions_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.executions
    ADD CONSTRAINT executions_pkey PRIMARY KEY (exec_id);


--
-- Name: fundamental_data fundamental_data_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.fundamental_data
    ADD CONSTRAINT fundamental_data_pkey PRIMARY KEY (fundamental_id);


--
-- Name: fundamental_data fundamental_data_symbol_data_date_data_source_key; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.fundamental_data
    ADD CONSTRAINT fundamental_data_symbol_data_date_data_source_key UNIQUE (symbol, data_date, data_source);


--
-- Name: interactions interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.interactions
    ADD CONSTRAINT interactions_pkey PRIMARY KEY (interaction_id);


--
-- Name: kyc_status kyc_status_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.kyc_status
    ADD CONSTRAINT kyc_status_pkey PRIMARY KEY (user_id);


--
-- Name: market_data market_data_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.market_data
    ADD CONSTRAINT market_data_pkey PRIMARY KEY (data_id);


--
-- Name: market_data market_data_symbol_data_date_key; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.market_data
    ADD CONSTRAINT market_data_symbol_data_date_key UNIQUE (symbol, data_date);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: portfolio_assets portfolio_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolio_assets
    ADD CONSTRAINT portfolio_assets_pkey PRIMARY KEY (asset_id);


--
-- Name: portfolio_assets portfolio_assets_portfolio_id_symbol_key; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolio_assets
    ADD CONSTRAINT portfolio_assets_portfolio_id_symbol_key UNIQUE (portfolio_id, symbol);


--
-- Name: portfolio_metrics portfolio_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolio_metrics
    ADD CONSTRAINT portfolio_metrics_pkey PRIMARY KEY (metric_id);


--
-- Name: portfolios portfolios_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_pkey PRIMARY KEY (portfolio_id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (account_id, ticker);


--
-- Name: recommendations recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_pkey PRIMARY KEY (rec_id);


--
-- Name: risk_profiles risk_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.risk_profiles
    ADD CONSTRAINT risk_profiles_pkey PRIMARY KEY (risk_profile_id);


--
-- Name: securities securities_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.securities
    ADD CONSTRAINT securities_pkey PRIMARY KEY (symbol);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (preference_id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (profile_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: idx_ai_messages_session_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_ai_messages_session_id ON public.ai_messages USING btree (session_id, created_at);


--
-- Name: idx_ai_sessions_user_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_ai_sessions_user_id ON public.ai_sessions USING btree (user_id);


--
-- Name: idx_audit_trail_user_date; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_audit_trail_user_date ON public.audit_trail USING btree (user_id, created_at DESC);


--
-- Name: idx_compliance_checks_result; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_compliance_checks_result ON public.compliance_checks USING btree (check_result);


--
-- Name: idx_compliance_checks_user_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_compliance_checks_user_id ON public.compliance_checks USING btree (user_id);


--
-- Name: idx_economic_indicators_code_date; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_economic_indicators_code_date ON public.economic_indicators USING btree (indicator_code, data_date DESC);


--
-- Name: idx_fundamental_data_symbol_date; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_fundamental_data_symbol_date ON public.fundamental_data USING btree (symbol, data_date DESC);


--
-- Name: idx_market_data_symbol_date; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_market_data_symbol_date ON public.market_data USING btree (symbol, data_date DESC);


--
-- Name: idx_portfolio_assets_portfolio_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_portfolio_assets_portfolio_id ON public.portfolio_assets USING btree (portfolio_id);


--
-- Name: idx_portfolio_assets_symbol; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_portfolio_assets_symbol ON public.portfolio_assets USING btree (symbol);


--
-- Name: idx_portfolio_metrics_date; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_portfolio_metrics_date ON public.portfolio_metrics USING btree (calculation_date DESC);


--
-- Name: idx_portfolio_metrics_portfolio_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_portfolio_metrics_portfolio_id ON public.portfolio_metrics USING btree (portfolio_id);


--
-- Name: idx_portfolios_user_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_portfolios_user_id ON public.portfolios USING btree (user_id);


--
-- Name: idx_risk_profiles_current; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_risk_profiles_current ON public.risk_profiles USING btree (user_id) WHERE (is_current = true);


--
-- Name: idx_risk_profiles_user_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_risk_profiles_user_id ON public.risk_profiles USING btree (user_id);


--
-- Name: idx_transactions_portfolio_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_transactions_portfolio_id ON public.transactions USING btree (portfolio_id);


--
-- Name: idx_transactions_user_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_transactions_user_id ON public.transactions USING btree (user_id);


--
-- Name: idx_user_profiles_user_id; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_user_profiles_user_id ON public.user_profiles USING btree (user_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: avnadmin
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: portfolio_assets tr_portfolio_assets_updated_at; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_portfolio_assets_updated_at BEFORE UPDATE ON public.portfolio_assets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: portfolios tr_portfolios_audit; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_portfolios_audit AFTER INSERT OR DELETE OR UPDATE ON public.portfolios FOR EACH ROW EXECUTE FUNCTION public.create_audit_trail();


--
-- Name: portfolios tr_portfolios_updated_at; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_portfolios_updated_at BEFORE UPDATE ON public.portfolios FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: securities tr_securities_updated_at; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_securities_updated_at BEFORE UPDATE ON public.securities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: user_preferences tr_user_preferences_updated_at; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: user_profiles tr_user_profiles_updated_at; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: users tr_users_updated_at; Type: TRIGGER; Schema: public; Owner: avnadmin
--

CREATE TRIGGER tr_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: agent_workflows agent_workflows_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.agent_workflows
    ADD CONSTRAINT agent_workflows_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.ai_sessions(session_id) ON DELETE CASCADE;


--
-- Name: ai_messages ai_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.ai_messages
    ADD CONSTRAINT ai_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.ai_sessions(session_id) ON DELETE CASCADE;


--
-- Name: ai_sessions ai_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.ai_sessions
    ADD CONSTRAINT ai_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: compliance_checks compliance_checks_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.compliance_checks
    ADD CONSTRAINT compliance_checks_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(portfolio_id);


--
-- Name: compliance_checks compliance_checks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.compliance_checks
    ADD CONSTRAINT compliance_checks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: fundamental_data fundamental_data_symbol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.fundamental_data
    ADD CONSTRAINT fundamental_data_symbol_fkey FOREIGN KEY (symbol) REFERENCES public.securities(symbol);


--
-- Name: market_data market_data_symbol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.market_data
    ADD CONSTRAINT market_data_symbol_fkey FOREIGN KEY (symbol) REFERENCES public.securities(symbol);


--
-- Name: portfolio_assets portfolio_assets_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolio_assets
    ADD CONSTRAINT portfolio_assets_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(portfolio_id) ON DELETE CASCADE;


--
-- Name: portfolio_metrics portfolio_metrics_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolio_metrics
    ADD CONSTRAINT portfolio_metrics_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(portfolio_id) ON DELETE CASCADE;


--
-- Name: portfolios portfolios_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: risk_profiles risk_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.risk_profiles
    ADD CONSTRAINT risk_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: transactions transactions_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(portfolio_id) ON DELETE CASCADE;


--
-- Name: user_preferences user_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: avnadmin
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO myfalcon_team;


--
-- Name: TABLE accounts; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.accounts TO myfalcon_team;


--
-- Name: TABLE agent_workflows; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.agent_workflows TO myfalcon_team;


--
-- Name: TABLE ai_messages; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ai_messages TO myfalcon_team;


--
-- Name: TABLE ai_sessions; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ai_sessions TO myfalcon_team;


--
-- Name: TABLE audit_trail; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.audit_trail TO myfalcon_team;


--
-- Name: TABLE compliance_checks; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.compliance_checks TO myfalcon_team;


--
-- Name: TABLE economic_indicators; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.economic_indicators TO myfalcon_team;


--
-- Name: TABLE executions; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.executions TO myfalcon_team;


--
-- Name: TABLE fundamental_data; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.fundamental_data TO myfalcon_team;


--
-- Name: TABLE interactions; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.interactions TO myfalcon_team;


--
-- Name: TABLE kyc_status; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kyc_status TO myfalcon_team;


--
-- Name: TABLE market_data; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.market_data TO myfalcon_team;


--
-- Name: TABLE orders; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.orders TO myfalcon_team;


--
-- Name: TABLE portfolio_assets; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.portfolio_assets TO myfalcon_team;


--
-- Name: TABLE portfolio_metrics; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.portfolio_metrics TO myfalcon_team;


--
-- Name: TABLE portfolios; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.portfolios TO myfalcon_team;


--
-- Name: TABLE positions; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.positions TO myfalcon_team;


--
-- Name: TABLE recommendations; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.recommendations TO myfalcon_team;


--
-- Name: TABLE risk_profiles; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.risk_profiles TO myfalcon_team;


--
-- Name: TABLE securities; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.securities TO myfalcon_team;


--
-- Name: TABLE transactions; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.transactions TO myfalcon_team;


--
-- Name: TABLE user_preferences; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.user_preferences TO myfalcon_team;


--
-- Name: TABLE user_profiles; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.user_profiles TO myfalcon_team;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: avnadmin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.users TO myfalcon_team;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: avnadmin
--

ALTER DEFAULT PRIVILEGES FOR ROLE avnadmin IN SCHEMA public GRANT SELECT,USAGE ON SEQUENCES TO myfalcon_team;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: avnadmin
--

ALTER DEFAULT PRIVILEGES FOR ROLE avnadmin IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO myfalcon_team;


--
-- PostgreSQL database dump complete
--

\unrestrict ixpiHC2H6zQQxND1g9RI1N4yFHtbGduBp64PwsP3hj4waFGy9YhtWKjf9aUHNrQ

