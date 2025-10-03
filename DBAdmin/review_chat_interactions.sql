-- MyFalconAdvisor Chat Interactions Review
-- SQL queries to review all chat interactions and AI sessions in PostgreSQL

-- ============================================
-- 1. AI SESSIONS TABLE
-- ============================================
-- This table stores chat session metadata

-- View all AI sessions
SELECT 
    session_id,
    user_id,
    session_type,
    status,
    context_data,
    started_at,
    ended_at,
    total_messages,
    total_tokens_used
FROM ai_sessions
ORDER BY started_at DESC
LIMIT 20;

-- Count sessions by type
SELECT 
    session_type,
    COUNT(*) as session_count,
    AVG(total_messages) as avg_messages_per_session,
    AVG(total_tokens_used) as avg_tokens_per_session
FROM ai_sessions
GROUP BY session_type
ORDER BY session_count DESC;

-- Recent sessions (last 24 hours)
SELECT 
    session_id,
    session_type,
    status,
    total_messages,
    started_at
FROM ai_sessions
WHERE started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;

-- ============================================
-- 2. AI MESSAGES TABLE  
-- ============================================
-- This table stores individual chat messages

-- View recent chat messages
SELECT 
    message_id,
    session_id,
    agent_type,
    message_type,
    LEFT(message_content, 100) as content_preview,
    tokens_used,
    processing_time_ms,
    created_at
FROM ai_messages
ORDER BY created_at DESC
LIMIT 20;

-- Messages by agent type
SELECT 
    agent_type,
    COUNT(*) as message_count,
    AVG(tokens_used) as avg_tokens,
    AVG(processing_time_ms) as avg_processing_time_ms
FROM ai_messages
WHERE tokens_used IS NOT NULL
GROUP BY agent_type
ORDER BY message_count DESC;

-- Full conversation for a specific session (replace session_id)
SELECT 
    agent_type,
    message_type,
    message_content,
    created_at
FROM ai_messages
WHERE session_id = 'your-session-id-here'
ORDER BY created_at ASC;

-- ============================================
-- 3. INTERACTIONS TABLE
-- ============================================
-- This table stores general user interactions

-- View recent interactions
SELECT 
    interaction_id,
    account_id,
    timestamp,
    channel,
    LEFT(message, 100) as message_preview
FROM interactions
ORDER BY timestamp DESC
LIMIT 20;

-- Interactions by channel
SELECT 
    channel,
    COUNT(*) as interaction_count
FROM interactions
GROUP BY channel
ORDER BY interaction_count DESC;

-- ============================================
-- 4. RECOMMENDATIONS TABLE
-- ============================================
-- This table stores AI-generated recommendations

-- View recent recommendations
SELECT 
    rec_id,
    account_id,
    ticker,
    action,
    percentage,
    LEFT(rationale, 100) as rationale_preview,
    created_at
FROM recommendations
ORDER BY created_at DESC
LIMIT 20;

-- Recommendations by action type
SELECT 
    action,
    COUNT(*) as recommendation_count,
    AVG(percentage) as avg_percentage
FROM recommendations
GROUP BY action
ORDER BY recommendation_count DESC;

-- ============================================
-- 5. COMBINED CHAT SESSION VIEW
-- ============================================
-- Join sessions with their messages for complete picture

-- Complete chat session overview
SELECT 
    s.session_id,
    s.session_type,
    s.started_at,
    s.total_messages,
    s.total_tokens_used,
    COUNT(m.message_id) as actual_message_count,
    STRING_AGG(
        m.agent_type || ': ' || LEFT(m.message_content, 50), 
        ' | ' 
        ORDER BY m.created_at
    ) as conversation_preview
FROM ai_sessions s
LEFT JOIN ai_messages m ON s.session_id = m.session_id
GROUP BY s.session_id, s.session_type, s.started_at, s.total_messages, s.total_tokens_used
ORDER BY s.started_at DESC
LIMIT 10;

-- ============================================
-- 6. CHAT ACTIVITY SUMMARY
-- ============================================

-- Daily chat activity
SELECT 
    DATE(started_at) as chat_date,
    COUNT(DISTINCT session_id) as sessions,
    SUM(total_messages) as total_messages,
    SUM(total_tokens_used) as total_tokens
FROM ai_sessions
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at)
ORDER BY chat_date DESC;

-- Hourly activity pattern
SELECT 
    EXTRACT(HOUR FROM started_at) as hour_of_day,
    COUNT(*) as session_count,
    AVG(total_messages) as avg_messages
FROM ai_sessions
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(HOUR FROM started_at)
ORDER BY hour_of_day;

-- ============================================
-- 7. TOKEN USAGE ANALYSIS
-- ============================================

-- Token usage by session type
SELECT 
    session_type,
    COUNT(*) as sessions,
    SUM(total_tokens_used) as total_tokens,
    AVG(total_tokens_used) as avg_tokens_per_session,
    MAX(total_tokens_used) as max_tokens_session
FROM ai_sessions
WHERE total_tokens_used > 0
GROUP BY session_type
ORDER BY total_tokens DESC;

-- Most token-intensive messages
SELECT 
    session_id,
    agent_type,
    message_type,
    tokens_used,
    LEFT(message_content, 100) as content_preview,
    created_at
FROM ai_messages
WHERE tokens_used IS NOT NULL
ORDER BY tokens_used DESC
LIMIT 10;
