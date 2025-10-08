-- Align chat history structures with the simplified chat/message schema.
INSERT INTO
    app."user" (username, email, password_hash)
VALUES
    (
        'system',
        'system@example.com',
        'system_placeholder_password'
    ) ON CONFLICT (username) DO NOTHING;