-- ============================================================================
-- D33 (P0) — Evidence traceability: authoritative source-lineage columns
-- ----------------------------------------------------------------------------
-- Release-blocker: every calculated emission must be traceable to the exact
-- source evidence. This migration is ADDITIVE + IDEMPOTENT — it preserves all
-- existing rows/IDs/RLS and never rewrites historical provenance.
--
-- 1. calculation_snapshots gains the persisted source references the engine
--    already carries transiently (source_file/source_page) PLUS the exact
--    extraction item that produced the line (source_item_id). Combined with
--    the existing emissions_logs.snapshot_id the chain becomes:
--
--    organization_files <-(file_id)- manual_extraction_items
--       <-(source_item_id)- calculation_snapshots
--       <-(snapshot_id)- emissions_logs
--
-- 2. manual_extraction_items gains file_id (-> organization_files) so the
--    source document is structurally linked (not string-matched).
-- ============================================================================

BEGIN;

ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS source_item_id uuid,
    ADD COLUMN IF NOT EXISTS source_file text,
    ADD COLUMN IF NOT EXISTS source_page integer;

ALTER TABLE public.manual_extraction_items
    ADD COLUMN IF NOT EXISTS file_id uuid;

-- Authoritative, non-destructive source links (SET NULL preserves history if
-- an item/file is ever removed).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'calculation_snapshots_source_item_id_fkey'
    ) THEN
        ALTER TABLE public.calculation_snapshots
            ADD CONSTRAINT calculation_snapshots_source_item_id_fkey
            FOREIGN KEY (source_item_id)
            REFERENCES public.manual_extraction_items(id)
            ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'manual_extraction_items_file_id_fkey'
    ) THEN
        ALTER TABLE public.manual_extraction_items
            ADD CONSTRAINT manual_extraction_items_file_id_fkey
            FOREIGN KEY (file_id)
            REFERENCES public.organization_files(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_calculation_snapshots_source_item
    ON public.calculation_snapshots (source_item_id);
CREATE INDEX IF NOT EXISTS idx_manual_extraction_items_file
    ON public.manual_extraction_items (file_id);

-- Idempotent backfill: link existing items to their organization_files row by
-- exact path match (the historical file_url == organization_files.path). Only
-- rows without a file_id are touched; unmatched rows stay NULL (honest).
UPDATE public.manual_extraction_items i
   SET file_id = f.id
  FROM public.organization_files f
 WHERE i.file_id IS NULL
   AND f.path = i.file_url;

COMMIT;
