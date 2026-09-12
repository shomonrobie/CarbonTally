-- ============================================================================
-- CarbonTally Phase 8 Reporting S3 — report-version lifecycle state
-- File: 20260913000000_p8_report_lifecycle_status.sql
--
-- Purpose (Phase 8 Reporting S3 — bounded, PO-authorised):
--   Add the ratified report-VERSION lifecycle state to the existing
--   ``public.report_versions`` table so the version state machine
--   (DRAFT → REVIEWED → APPROVED → FINAL, with CHANGES_REQUESTED / REJECTED
--   review outcomes) can be persisted and server-guarded.
--
-- Canonical responsibility (no new lifecycle architecture is introduced):
--   * ``public.report_versions`` (RC2) — the version spine. Its existing
--     ``UNIQUE (report_id, version_number)`` natural key and ``is_current``
--     flag are unchanged; the single-current-version invariant remains
--     enforced in the repository (Phase 8 S1-A).
--   * ``public.report_generation_queue.status`` — the GENERATION state machine
--     (pending/generating/completed/failed). It is deliberately NOT reused for
--     lifecycle state (ratified: the two vocabularies must not be conflated).
--   * ``public.audit_trail`` — the append-only lifecycle audit substrate.
--
-- Scope discipline:
--   * ADDITIVE + IDEMPOTENT. Existing rows converge to ``status='DRAFT'`` via
--     the column default (the ratified "a completed generation yields a DRAFT
--     version" rule). No row content is rewritten.
--   * NO RLS change. ``report_versions`` already has RLS enabled; this file
--     adds no policy, disables nothing, and weakens nothing.
--   * NO other table, column, constraint, index or policy is touched.
--   * Narrative overlay, comments, frozen-PDF artefacts, hashing and approval
--     columns belong to later bounded stages and are deliberately absent.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Version lifecycle state
-- ---------------------------------------------------------------------------
ALTER TABLE public.report_versions
    ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'DRAFT';

-- ---------------------------------------------------------------------------
-- 2. Bounded vocabulary guard (only the six ratified stored states)
-- ---------------------------------------------------------------------------
ALTER TABLE public.report_versions
    DROP CONSTRAINT IF EXISTS report_versions_status_check;

ALTER TABLE public.report_versions
    ADD CONSTRAINT report_versions_status_check
    CHECK (
        status IN (
            'DRAFT',
            'REVIEWED',
            'CHANGES_REQUESTED',
            'REJECTED',
            'APPROVED',
            'FINAL'
        )
    );

COMMENT ON COLUMN public.report_versions.status IS
    'Phase 8 S3 — report VERSION lifecycle state. Distinct from '
    'report_generation_queue.status (the generation state machine). '
    'Approved/final versions are immutable; a post-approval change creates a '
    'new version.';

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [ ] column public.report_versions.status exists (varchar(32), NOT NULL)
--   [ ] default 'DRAFT'; existing rows read as DRAFT
--   [ ] constraint report_versions_status_check exists with the six states
--   [ ] report_versions RLS state/policies unchanged
--   [ ] re-running this file is a no-op
-- ============================================================================
