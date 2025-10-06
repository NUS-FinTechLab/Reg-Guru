-- Update chat schema to bind sessions to users and rename history table.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM app.user WHERE username = 'system'
    ) THEN
        INSERT INTO app.user (username, email, password_hash)
        VALUES ('system', 'system@example.com', 'system_placeholder_password');
    END IF;
END$$;

ALTER TABLE app.chat_sessions
    ADD COLUMN IF NOT EXISTS user_id UUID;

UPDATE app.chat_sessions
SET user_id = sub.id
FROM (
    SELECT id FROM app.user WHERE username = 'system'
) AS sub
WHERE user_id IS NULL;

ALTER TABLE app.chat_sessions
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE app.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES app.user(id) ON DELETE CASCADE;

-- Rename saved_queries to chat_history and adjust foreign keys/columns.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'app' AND table_name = 'saved_queries'
    ) THEN
        ALTER TABLE app.saved_queries RENAME TO chat_history;
    END IF;
END$$;

ALTER TABLE app.chat_history
    RENAME COLUMN session_id TO chat_id;

-- Rename dependent objects where necessary.
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT constraint_name INTO constraint_name
    FROM information_schema.table_constraints
    WHERE table_schema = 'app'
      AND table_name = 'chat_history'
      AND constraint_type = 'FOREIGN KEY'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE app.chat_history RENAME CONSTRAINT %I TO chat_history_chat_id_fkey', constraint_name);
    END IF;
END$$;

-- Ensure foreign key references chat_sessions id.
ALTER TABLE app.chat_history
    DROP CONSTRAINT IF EXISTS chat_history_chat_id_fkey;
ALTER TABLE app.chat_history
    ADD CONSTRAINT chat_history_chat_id_fkey
    FOREIGN KEY (chat_id) REFERENCES app.chat_sessions(id) ON DELETE SET NULL;

-- Rename sequence and primary key if they exist under old name.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.sequences
        WHERE sequence_schema = 'app' AND sequence_name = 'saved_queries_id_seq'
    ) THEN
        ALTER SEQUENCE app.saved_queries_id_seq RENAME TO chat_history_id_seq;
    END IF;
END$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'app' AND indexname = 'saved_queries_pkey'
    ) THEN
        ALTER INDEX app.saved_queries_pkey RENAME TO chat_history_pkey;
    END IF;
END$$;
