-- Create enum types for checklist item status and priority.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type typ
        JOIN pg_namespace nsp ON nsp.oid = typ.typnamespace
        WHERE typ.typname = 'checklist_item_status'
          AND nsp.nspname = 'app'
    ) THEN
        CREATE TYPE app.checklist_item_status AS ENUM ('not_started', 'ongoing', 'finished');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type typ
        JOIN pg_namespace nsp ON nsp.oid = typ.typnamespace
        WHERE typ.typname = 'checklist_item_priority'
          AND nsp.nspname = 'app'
    ) THEN
        CREATE TYPE app.checklist_item_priority AS ENUM ('low', 'medium', 'high');
    END IF;
END $$;

-- Create table for checklists owned by users.
CREATE TABLE IF NOT EXISTS app.checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app."user" (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create table for checklist items.
CREATE TABLE IF NOT EXISTS app.checklist_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checklist_id UUID NOT NULL REFERENCES app.checklist (id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status app.checklist_item_status NOT NULL DEFAULT 'not_started',
    priority app.checklist_item_priority NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_checklist_user_id
    ON app.checklist (user_id);

CREATE INDEX IF NOT EXISTS idx_checklist_item_checklist_id
    ON app.checklist_item (checklist_id);

CREATE INDEX IF NOT EXISTS idx_checklist_item_status
    ON app.checklist_item (status);

CREATE INDEX IF NOT EXISTS idx_checklist_item_priority
    ON app.checklist_item (priority);
