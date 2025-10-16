-- Create table for storing refresh tokens issued to users.
CREATE TABLE IF NOT EXISTS app.refresh_token (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app."user"(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_refresh_token_token_hash
    ON app.refresh_token (token_hash);

CREATE INDEX IF NOT EXISTS idx_refresh_token_user_id
    ON app.refresh_token (user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_token_active
    ON app.refresh_token (user_id)
    WHERE revoked_at IS NULL;
