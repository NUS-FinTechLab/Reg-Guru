-- Update reference link storage to support structured metadata.

ALTER TABLE app.checklist_stage
    ADD COLUMN IF NOT EXISTS reference_links JSONB NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'checklist_item'
          AND column_name = 'referencelink'
    ) THEN
        ALTER TABLE app.checklist_item
            RENAME COLUMN referencelink TO reference_links;
    END IF;
END $$;

DO $$
BEGIN
    -- Only run the conversion when the column is still stored as a text array.
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'checklist_item'
          AND column_name = 'reference_links'
          AND udt_name <> 'jsonb'
    ) THEN
        ALTER TABLE app.checklist_item
            ALTER COLUMN reference_links DROP DEFAULT;

        ALTER TABLE app.checklist_item
            ALTER COLUMN reference_links TYPE JSONB
                USING COALESCE(to_jsonb(reference_links), '[]'::jsonb);
    END IF;
END $$;

UPDATE app.checklist_item
SET reference_links = '[]'::jsonb
WHERE reference_links IS NULL;

ALTER TABLE app.checklist_item
    ALTER COLUMN reference_links SET DEFAULT '[]'::jsonb;

ALTER TABLE app.checklist_item
    ALTER COLUMN reference_links SET NOT NULL;
