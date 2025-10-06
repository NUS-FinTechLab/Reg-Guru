-- Creates the application schema used by the chatbot backend.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT UNIQUE NOT NULL,
    region TEXT NOT NULL CHECK (region IN ('us', 'eu', 'sg')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES app.chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'bot')),
    body TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON app.chat_messages(session_id, sent_at);

CREATE TABLE IF NOT EXISTS app.feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES app.chat_sessions(id) ON DELETE CASCADE,
    message_id BIGINT REFERENCES app.chat_messages(id) ON DELETE SET NULL,
    rating TEXT NOT NULL CHECK (rating IN ('thumbs_up', 'thumbs_down')),
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_session ON app.feedback(session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS app.saved_queries (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES app.chat_sessions(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    response_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
