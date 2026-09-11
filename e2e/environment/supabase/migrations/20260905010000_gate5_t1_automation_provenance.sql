-- ============================================================================
-- CarbonTally — WS4 Gate 5 (Automated-Extraction Machine Provenance) — T1
-- File: 20260905010000_gate5_t1_automation_provenance.sql
--
-- Accepted design: docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md
-- Task T1 (implementation work breakdown item 1): add the additive write-once
-- machine-attribution block columns to the durable job store
-- ``public.document_processing_queue`` (the canonical automated-execution
-- record). Later tasks (T3/T4/T5) persist and surface these fields; this
-- migration ONLY adds the schema.
--
-- Semantics (truthful provenance):
--   * automation_provider       — provider identity of the model that CONTRIBUTED
--     to the persisted extraction output (host-derived at runtime, never
--     fabricated). NULL = deterministic-only result / no AI contributed /
--     legacy row predating this column.
--   * automation_model          — model identifier actually sent to the provider
--     for the contributing AI pass. NULL = deterministic-only / unknown.
--   * automation_model_version  — explicit version qualifier only when truthfully
--     known; NULL otherwise (never fabricated/guessed from the model id).
--
-- Write-once: these columns are set by the worker only at the extraction-stage
-- advance that first persists extracted_data, and must never be overwritten by
-- later human processing. Database-level write-once enforcement (guard trigger)
-- is deliberately NOT included here — it belongs to task T6 of the same design.
--
-- Data safety:
--   * purely additive + idempotent (ADD COLUMN IF NOT EXISTS); existing rows
--     unaffected (the new columns are NULL for all legacy/deterministic rows);
--   * no backfill of invented provider/model/version metadata;
--   * no RLS change, no index, no constraint on existing data, no new table;
--   * Gate-4 columns (calculation_snapshots.performed_by / source_item_id) and
--     all D38/D39/D40 surfaces are untouched.
-- ============================================================================

BEGIN;

ALTER TABLE public.document_processing_queue
    ADD COLUMN IF NOT EXISTS automation_provider VARCHAR(120),
    ADD COLUMN IF NOT EXISTS automation_model VARCHAR(240),
    ADD COLUMN IF NOT EXISTS automation_model_version VARCHAR(120);

COMMENT ON COLUMN public.document_processing_queue.automation_provider IS
    'Machine-provenance provider identity of the model that CONTRIBUTED to the '
    'persisted extraction output (WS4 Gate 5, task T1). Host-derived at runtime; '
    'never fabricated. NULL = deterministic-only result, no AI contributed, or '
    'legacy row predating this column. Write-once: never overwritten by later '
    'human processing. Not a user/PE/role identity and never an authorization '
    'principal.';

COMMENT ON COLUMN public.document_processing_queue.automation_model IS
    'Machine-provenance model identifier actually sent to the provider for the '
    'contributing AI extraction pass (WS4 Gate 5, task T1). NULL = '
    'deterministic-only result or unknown. Write-once; truthful only.';

COMMENT ON COLUMN public.document_processing_queue.automation_model_version IS
    'Machine-provenance explicit model/version qualifier recorded only when '
    'truthfully known (WS4 Gate 5, task T1). NULL = unknown; never fabricated or '
    'guessed from the model identifier.';

COMMIT;
