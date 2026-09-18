-- ============================================================================
-- CarbonTally — F-039-1 Activity Clarification — parent FK binding
-- File: 20260929000000_p8_fs_activity_clarifications_fks.sql
--
-- PURPOSE
--   Close the documented limitation of 20260928000000_p8_fs_activity_clarifications.sql:
--   item_key / batch_key were stored as plain text because the authoritative parent
--   tables had not been confirmed in that window. They are now confirmed:
--       public.manual_extraction_items     (id uuid PRIMARY KEY)   — extraction item
--       public.manual_extraction_batches   (id uuid PRIMARY KEY)   — extraction batch
--   (confirmed by schema probe of the dedicated disposable carbontally_test database:
--    manual_extraction_items.id = uuid, manual_extraction_batches.id = uuid,
--    manual_extraction_batches.organization_id = uuid.)
--
-- WHY THE COLUMNS CHANGE TYPE
--   A foreign key requires matching types; the columns are text and the parents are uuid,
--   so the columns are narrowed to uuid first. The cast runs only when the column is still
--   text, so the migration is idempotent, and it is safe because the table was empty when
--   the type was verified (row count 0) — no value can fail the cast.
--
-- DELETE ACTION — follows the established CarbonTally convention, not a new policy
--   `organization_id`  → ON DELETE CASCADE     (existing, unchanged in this migration)
--   source-item links  → ON DELETE SET NULL    (cf. 20260823010000_d33_evidence_traceability.sql:
--                                               calculation_snapshots.source_item_id →
--                                               manual_extraction_items(id) ON DELETE SET NULL;
--                                               and 20260916000000_p8_b2_evidence_line_items.sql:
--                                               source_file_id → organization_files(id) ON DELETE SET NULL)
--   A clarification records an adjudication *about* an item; deleting the item must not
--   destroy the adjudication history, so the link is severed (SET NULL) rather than cascading.
--   RESTRICT was not chosen: blocking item deletion is a stronger operational claim than the
--   existing evidence conventions make. `ON DELETE SET NULL` is the closest existing analogue.
--
-- STATUS: created in the repository. Applied and verified ONLY in the dedicated disposable
--   carbontally_test database. NEVER applied to production.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Narrow the parent keys to uuid (idempotent: only while still text)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name   = 'activity_clarifications'
           AND column_name  = 'item_key'
           AND data_type    = 'text'
    ) THEN
        ALTER TABLE public.activity_clarifications
            ALTER COLUMN item_key TYPE uuid USING item_key::uuid;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name   = 'activity_clarifications'
           AND column_name  = 'batch_key'
           AND data_type    = 'text'
    ) THEN
        ALTER TABLE public.activity_clarifications
            ALTER COLUMN batch_key TYPE uuid USING batch_key::uuid;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. Bind the confirmed parents (idempotent: guarded by constraint existence)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'activity_clarifications_item_key_fkey'
           AND conrelid = 'public.activity_clarifications'::regclass
    ) THEN
        ALTER TABLE public.activity_clarifications
            ADD CONSTRAINT activity_clarifications_item_key_fkey
            FOREIGN KEY (item_key)
            REFERENCES public.manual_extraction_items(id)
            ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'activity_clarifications_batch_key_fkey'
           AND conrelid = 'public.activity_clarifications'::regclass
    ) THEN
        ALTER TABLE public.activity_clarifications
            ADD CONSTRAINT activity_clarifications_batch_key_fkey
            FOREIGN KEY (batch_key)
            REFERENCES public.manual_extraction_batches(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3. Indexes for the new parent lookups (FK columns are not auto-indexed)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS activity_clarifications_item_idx
    ON public.activity_clarifications (item_key);
CREATE INDEX IF NOT EXISTS activity_clarifications_batch_idx
    ON public.activity_clarifications (batch_key);
