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

-- Create table for checklist stages.
CREATE TABLE IF NOT EXISTS app.checklist_stage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checklist_id UUID NOT NULL REFERENCES app.checklist (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create table for checklist items.
CREATE TABLE IF NOT EXISTS app.checklist_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checklist_id UUID NOT NULL REFERENCES app.checklist (id) ON DELETE CASCADE,
    stage_id UUID NOT NULL REFERENCES app.checklist_stage (id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status app.checklist_item_status NOT NULL DEFAULT 'not_started',
    priority app.checklist_item_priority NOT NULL DEFAULT 'medium',
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_checklist_user_id
    ON app.checklist (user_id);

CREATE INDEX IF NOT EXISTS idx_checklist_stage_checklist_id
    ON app.checklist_stage (checklist_id);

CREATE INDEX IF NOT EXISTS idx_checklist_stage_position
    ON app.checklist_stage (checklist_id, position);

-- Ensure stage_id column exists for pre-existing deployments.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'checklist_item'
          AND column_name = 'stage_id'
    ) THEN
        ALTER TABLE app.checklist_item
            ADD COLUMN stage_id UUID;
    END IF;
END $$;

-- Ensure position column exists for legacy tables.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'checklist_item'
          AND column_name = 'position'
    ) THEN
        ALTER TABLE app.checklist_item
            ADD COLUMN position INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- Backfill stages for existing checklist items that predate the stage schema.
DO $$
DECLARE
    stage_column_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'checklist_item'
          AND column_name = 'stage_id'
    ) INTO stage_column_exists;

    IF stage_column_exists THEN
        -- Create a default stage for any checklist missing one.
        INSERT INTO app.checklist_stage (id, checklist_id, title, description, position)
        SELECT gen_random_uuid(), c.id, 'General', '', 0
        FROM app.checklist AS c
        WHERE NOT EXISTS (
            SELECT 1
            FROM app.checklist_stage AS cs
            WHERE cs.checklist_id = c.id
        );

        -- Assign stage IDs to existing checklist items without a stage.
        UPDATE app.checklist_item AS ci
        SET stage_id = cs.id
        FROM app.checklist_stage AS cs
        WHERE ci.checklist_id = cs.checklist_id
          AND ci.stage_id IS NULL;

        -- Enforce NOT NULL now that every item is associated with a stage.
        ALTER TABLE app.checklist_item
            ALTER COLUMN stage_id SET NOT NULL;
    END IF;
END $$;

-- Ensure a foreign key constraint exists for stage linkage.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_schema = 'app'
          AND table_name = 'checklist_item'
          AND constraint_name = 'checklist_item_stage_id_fkey'
    ) THEN
        ALTER TABLE app.checklist_item
            ADD CONSTRAINT checklist_item_stage_id_fkey
            FOREIGN KEY (stage_id) REFERENCES app.checklist_stage (id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_checklist_item_checklist_id
    ON app.checklist_item (checklist_id);

CREATE INDEX IF NOT EXISTS idx_checklist_item_stage_id
    ON app.checklist_item (stage_id);

CREATE INDEX IF NOT EXISTS idx_checklist_item_stage_position
    ON app.checklist_item (stage_id, position);

CREATE INDEX IF NOT EXISTS idx_checklist_item_status
    ON app.checklist_item (status);

CREATE INDEX IF NOT EXISTS idx_checklist_item_priority
    ON app.checklist_item (priority);
