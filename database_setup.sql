-- ============================================================================
-- INDICOME BOT DATABASE SETUP
-- ============================================================================
-- This file contains all the database tables needed for the bot

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    search_count INT DEFAULT 0,
    search_credits INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Messages/Feedback table
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    query TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payments table (for PayPal transactions)
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    payment_id TEXT UNIQUE NOT NULL,
    payer_id TEXT,
    amount DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_type TEXT DEFAULT 'credits',
    credits INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_messages_telegram_id ON messages(telegram_id);
CREATE INDEX IF NOT EXISTS idx_search_history_telegram_id ON search_history(telegram_id);
CREATE INDEX IF NOT EXISTS idx_payments_telegram_id ON payments(telegram_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. All new users get 3 free search credits (search_credits = 3)
-- 2. VIP system has been removed - only credit-based system now
-- 3. Users can buy credits via PayPal
-- 4. Credits never expire
-- 5. Each search costs 1 credit

