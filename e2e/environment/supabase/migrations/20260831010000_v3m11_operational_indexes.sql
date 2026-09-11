-- BL-3 / QA-DB-014 — operational performance indexes.
--
-- The RC2 schema inventory (qa_harness/evidence/db/*_db_indexes.json) showed the
-- organisation-scoped document/processing queues filter upload_batches by
-- organization_id + status and manual_extraction_items by batch_id + status,
-- but no backing indexes existed for those filter predicates. These indexes
-- follow the existing naming convention (idx_<table>_<column>) and are
-- idempotent.
--
-- Individual (single-column) indexes are intentional:
--   * upload_batches (organization_id)  -> org-scoped upload queues
--   * upload_batches (status)           -> cross-org stage/queue scans
--   * manual_extraction_items (batch_id)-> the org-scoped join into batches
--   * manual_extraction_items (status)  -> processing-stage queue scans
-- A composite (batch_id, status) was deliberately NOT used: the stage queues
-- also filter by assignment/entity and Postgres can bitmap-combine the two
-- single-column indexes without pinning one fixed join order.

CREATE INDEX IF NOT EXISTS idx_upload_batches_organization_id
    ON public.upload_batches (organization_id);

CREATE INDEX IF NOT EXISTS idx_upload_batches_status
    ON public.upload_batches (status);

CREATE INDEX IF NOT EXISTS idx_manual_extraction_items_batch_id
    ON public.manual_extraction_items (batch_id);

CREATE INDEX IF NOT EXISTS idx_manual_extraction_items_status
    ON public.manual_extraction_items (status);
