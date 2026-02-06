-- Database initialization script for AI Voice Detection API
-- Run this script to create the required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============== USERS TABLE ==============
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on api_key for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);

-- ============== API CALLS TABLE ==============
CREATE TABLE IF NOT EXISTS api_calls (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key VARCHAR(64),
    endpoint VARCHAR(100) NOT NULL,
    language VARCHAR(50),
    prediction VARCHAR(20),
    confidence FLOAT,
    processing_time_ms FLOAT,
    audio_duration_s FLOAT,
    audio_hash VARCHAR(64),
    client_ip VARCHAR(45),
    user_agent TEXT,
    status_code INT,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_api_calls_user_id ON api_calls(user_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON api_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_calls_api_key ON api_calls(api_key);
CREATE INDEX IF NOT EXISTS idx_api_calls_prediction ON api_calls(prediction);

-- ============== RATE LIMITS TABLE ==============
CREATE TABLE IF NOT EXISTS rate_limits (
    api_key VARCHAR(64) PRIMARY KEY,
    calls_this_minute INT DEFAULT 0,
    calls_this_hour INT DEFAULT 0,
    calls_this_day INT DEFAULT 0,
    minute_reset TIMESTAMP WITH TIME ZONE,
    hour_reset TIMESTAMP WITH TIME ZONE,
    day_reset TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============== DAILY STATS TABLE ==============
CREATE TABLE IF NOT EXISTS daily_stats (
    date DATE PRIMARY KEY,
    total_calls INT DEFAULT 0,
    successful_calls INT DEFAULT 0,
    failed_calls INT DEFAULT 0,
    ai_detected INT DEFAULT 0,
    human_detected INT DEFAULT 0,
    avg_confidence FLOAT,
    avg_processing_time_ms FLOAT,
    avg_audio_duration_s FLOAT,
    unique_users INT DEFAULT 0,
    by_language JSONB DEFAULT '{}',
    by_tier JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============== INSERT DEFAULT USER ==============
INSERT INTO users (email, api_key, tier) 
VALUES ('demo@example.com', 'demo_key_12345', 'demo')
ON CONFLICT (api_key) DO NOTHING;

-- ============== USEFUL VIEWS ==============

-- View: Recent API calls with user info
CREATE OR REPLACE VIEW v_recent_api_calls AS
SELECT 
    ac.id,
    ac.timestamp,
    u.email,
    ac.language,
    ac.prediction,
    ac.confidence,
    ac.processing_time_ms,
    ac.audio_duration_s,
    ac.status_code
FROM api_calls ac
LEFT JOIN users u ON ac.user_id = u.id
ORDER BY ac.timestamp DESC
LIMIT 100;

-- View: Hourly stats for last 24 hours
CREATE OR REPLACE VIEW v_hourly_stats AS
SELECT 
    date_trunc('hour', timestamp) AS hour,
    COUNT(*) AS total_calls,
    COUNT(*) FILTER (WHERE prediction = 'AI_GENERATED') AS ai_detected,
    COUNT(*) FILTER (WHERE prediction = 'HUMAN') AS human_detected,
    AVG(confidence) AS avg_confidence,
    AVG(processing_time_ms) AS avg_processing_time
FROM api_calls
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', timestamp)
ORDER BY hour DESC;

-- ============== FUNCTIONS ==============

-- Function to update daily stats
CREATE OR REPLACE FUNCTION update_daily_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO daily_stats (date, total_calls, ai_detected, human_detected, avg_confidence, avg_processing_time_ms)
    VALUES (
        DATE(NEW.timestamp),
        1,
        CASE WHEN NEW.prediction = 'AI_GENERATED' THEN 1 ELSE 0 END,
        CASE WHEN NEW.prediction = 'HUMAN' THEN 1 ELSE 0 END,
        NEW.confidence,
        NEW.processing_time_ms
    )
    ON CONFLICT (date) DO UPDATE SET
        total_calls = daily_stats.total_calls + 1,
        ai_detected = daily_stats.ai_detected + CASE WHEN NEW.prediction = 'AI_GENERATED' THEN 1 ELSE 0 END,
        human_detected = daily_stats.human_detected + CASE WHEN NEW.prediction = 'HUMAN' THEN 1 ELSE 0 END,
        avg_confidence = (daily_stats.avg_confidence * daily_stats.total_calls + NEW.confidence) / (daily_stats.total_calls + 1),
        avg_processing_time_ms = (daily_stats.avg_processing_time_ms * daily_stats.total_calls + NEW.processing_time_ms) / (daily_stats.total_calls + 1);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update daily stats
DROP TRIGGER IF EXISTS trigger_update_daily_stats ON api_calls;
CREATE TRIGGER trigger_update_daily_stats
    AFTER INSERT ON api_calls
    FOR EACH ROW
    WHEN (NEW.prediction IS NOT NULL)
    EXECUTE FUNCTION update_daily_stats();

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
END $$;
