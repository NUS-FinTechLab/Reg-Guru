-- Update chat schema to bind sessions to users and rename saved queries to chat history.

INSERT INTO app.user (username, email, password_hash)
VALUES ('system', 'system@example.com', 'system_placeholder_password')
ON CONFLICT (username) DO NOTHING;

ALTER TABLE app.chat_sessions
    ADD COLUMN IF NOT EXISTS user_id UUID;

UPDATE app.chat_sessions AS cs
SET user_id = u.id
FROM app.user AS u
WHERE u.username = 'system' AND cs.user_id IS NULL;

ALTER TABLE app.chat_sessions
    DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;

ALTER TABLE app.chat_sessions
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE app.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES app.user(id) ON DELETE CASCADE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'app'
          AND table_name = 'saved_queries'
    ) THEN
        IF EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'app'
              AND table_name = 'chat_history'
        ) THEN
            EXECUTE $migrate$
                INSERT INTO app.chat_history (id, chat_id, query_text, response_summary, created_at)
                SELECT id, session_id, query_text, response_summary, created_at
                FROM app.saved_queries
                ON CONFLICT (id) DO NOTHING
            $migrate$;
            EXECUTE 'DROP TABLE app.saved_queries';
        ELSE
            EXECUTE 'ALTER TABLE app.saved_queries RENAME TO chat_history';
        END IF;
    END IF;
END$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'chat_history'
          AND column_name = 'session_id'
    ) THEN
        EXECUTE 'ALTER TABLE app.chat_history RENAME COLUMN session_id TO chat_id';
    END IF;
END$$;

ALTER TABLE IF EXISTS app.chat_history
    DROP CONSTRAINT IF EXISTS saved_queries_session_id_fkey;

ALTER TABLE IF EXISTS app.chat_history
    DROP CONSTRAINT IF EXISTS chat_history_session_id_fkey;

ALTER TABLE IF EXISTS app.chat_history
    DROP CONSTRAINT IF EXISTS chat_history_chat_id_fkey;

ALTER TABLE app.chat_history
    ADD CONSTRAINT chat_history_chat_id_fkey
    FOREIGN KEY (chat_id) REFERENCES app.chat_sessions(id) ON DELETE SET NULL;

ALTER SEQUENCE IF EXISTS app.saved_queries_id_seq
    RENAME TO chat_history_id_seq;

ALTER INDEX IF EXISTS app.saved_queries_pkey
    RENAME TO chat_history_pkey;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.sequences
        WHERE sequence_schema = 'app'
          AND sequence_name = 'chat_history_id_seq'
    ) THEN
        IF EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'app'
              AND table_name = 'chat_history'
        ) THEN
            PERFORM setval(
                'app.chat_history_id_seq',
                COALESCE((SELECT MAX(id) FROM app.chat_history), 0)
            );
        END IF;
    END IF;
END$$;

