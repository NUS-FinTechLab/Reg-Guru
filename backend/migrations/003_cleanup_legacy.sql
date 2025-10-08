-- Remove legacy tables no longer used by the chat system.
DROP TABLE IF EXISTS app.chat_history CASCADE;
DROP TABLE IF EXISTS app.saved_queries CASCADE;
