-- ============================================================================
-- CarbonTally Phase 8 — S2 report-table schema/integrity (`…046`)
-- File: 20260921000000_p8_s2_is_current_single_valued.sql
--
-- PO RULING (D-17 / A-RLS / S2 reconciliation — **Option A**, 2026-09-14):
--   * adopt the DOCUMENTED APP-LAYER-ONLY RLS posture for `report_versions` and
--     `report_comments`: RLS stays ENABLED with ZERO policies, which is
--     intentionally FAIL-CLOSED for RLS-bound roles; backend access remains
--     governed by the existing verified organization-boundary authorization;
--   * implement the outstanding S2 integrity requirement — **at most one
--     `is_current = true` row per `report_id`** — using the additive PARTIAL
--     UNIQUE INDEX approach;
--   * do NOT implement the superseded S2 elements:
--       - `narrative_overlay`        → superseded by ratified B4 / `A1`
--                                      (narrative is requirement-bound; there is no
--                                       report-wide narrative path)
--       - `pdf_sha256`/`content_hash`→ superseded by ratified `B4-D7`
--                                      (`report_version_artifacts.content_sha256`)
--       - `report_comments` additions→ superseded by ratified `B4-D4`/`B4-D9`
--                                      (comments remain outside B4 and DORMANT;
--                                       visibility is deferred to the S6 backlog item)
--
-- SCOPE DISCIPLINE: additive and idempotent. It creates ONE partial unique index
-- and APPENDS documentation to two existing table comments (the original comment
-- text is preserved verbatim). It changes NO lifecycle semantics, NO column, NO
-- grant, NO policy and NO RLS flag, and it touches NO data. QA/non-production only
-- (production is prohibited — G0-D).
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions — refuse to create a unique index over invalid data
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    bad_reports int;
BEGIN
    IF to_regclass('public.report_versions') IS NULL THEN
        RAISE EXCEPTION 'S2 precondition failed: public.report_versions is absent';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'report_versions'
          AND column_name = 'is_current'
    ) THEN
        RAISE EXCEPTION 'S2 precondition failed: report_versions.is_current is absent';
    END IF;

    SELECT count(*) INTO bad_reports
    FROM (
        SELECT report_id FROM public.report_versions
        WHERE is_current
        GROUP BY report_id
        HAVING count(*) > 1
    ) x;

    IF bad_reports > 0 THEN
        RAISE EXCEPTION
            'S2 precondition failed: % report(s) already have more than one current version',
            bad_reports;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. The S2 integrity requirement: one current version per report
-- ---------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS report_versions_one_current_per_report
    ON public.report_versions (report_id)
    WHERE is_current;

COMMENT ON INDEX public.report_versions_one_current_per_report IS
  'S2 (`…046`) integrity guarantee: at most ONE row with is_current = true per report_id (partial unique index). Enforced at the database level so two concurrent "new version" operations cannot both become current.';

-- ---------------------------------------------------------------------------
-- 2. Documentation of the ratified RLS posture (comments APPENDED, originals kept)
-- ---------------------------------------------------------------------------
COMMENT ON TABLE public.report_versions IS
  'Report version history. RLS posture (PO D-17 / A-RLS, Option A): RLS is ENABLED with ZERO policies BY DESIGN — intentionally fail-closed for RLS-bound roles; access is backend-mediated under the verified organization-boundary authorization. No direct-Supabase organization-scoped policy model applies to this table (S2).';

COMMENT ON TABLE public.report_comments IS
  'Report comments. RLS posture (PO D-17 / A-RLS, Option A): RLS is ENABLED with ZERO policies BY DESIGN — intentionally fail-closed for RLS-bound roles; access is backend-mediated under the verified organization-boundary authorization. The table remains DORMANT: comment functionality and visibility are outside B4 (B4-D4/B4-D9) and are deferred to the S6 backlog item.';

-- ---------------------------------------------------------------------------
-- 3. Postconditions
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = 'report_versions'
          AND indexname = 'report_versions_one_current_per_report'
    ) THEN
        RAISE EXCEPTION 'S2 postcondition failed: the partial unique index was not created';
    END IF;
    RAISE NOTICE 'S2 (`…046`): one-current-per-report guarantee in place; documented app-layer-only RLS posture recorded.';
END $$;

COMMIT;
