-- ============================================================================
-- CarbonTally Phase 8 B4 (Narrative, Finalisation and Frozen Artefact) — migration 2
-- File: 20260919000000_p8_b4_frozen_artefact.sql
--
-- Purpose: public.report_version_artifacts — the APPEND-ONLY record of the frozen
--          report artefact produced at finalisation (deliverable S5).
--
-- RATIFIED PO DECISION B4-D5/D6/D7 (contract §25 Amendment 3) — implemented
-- exactly, with no exception path:
--   * the frozen artefact is MANDATORY at finalisation;
--   * it lives in the PRIVATE Supabase Storage bucket 'report-artifacts' — the
--     bucket name is constrained here so no other bucket (or external storage)
--     can ever hold it;
--   * the object key is structurally forced to
--     {organization_id}/{report_id}/{version_id}.pdf (the CHECK *derives* the
--     key from the row, so a mismatched key cannot be inserted);
--   * integrity is SHA-256 (format-constrained);
--   * ONE artefact record per finalised report version (UNIQUE);
--   * the record is append-only: UPDATE and DELETE are NOT granted to
--     'authenticated' and no UPDATE/DELETE policy exists. Corrections create a
--     new report version (D15 / DM-7).
--
-- Scope discipline: ADDITIVE + IDEMPOTENT. Creates exactly ONE new table.
-- MODIFIES ZERO existing tables, grants, policies or RLS flags. No storage
-- object is created by this migration. No retention artefact (B4-D8 is still an
-- open PO decision). No trigger.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.report_versions') IS NULL THEN
        RAISE EXCEPTION
            'B4-2 precondition failed: report_versions is absent. Apply the Phase 8 chain (S3, B1) before B4-2.';
    END IF;
    IF to_regprocedure('public.p8_disclosure_is_org_member(uuid)') IS NULL
       OR to_regprocedure('public.p8_disclosure_is_org_admin(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'B4-2 precondition failed: B1 helpers are absent. Apply 20260914000000_p8_b1_disclosure_model_foundation.sql first.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.report_version_artifacts (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_version_artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_id uuid NOT NULL REFERENCES public.report_generation_queue(id) ON DELETE CASCADE,
    report_version_id uuid NOT NULL REFERENCES public.report_versions(id) ON DELETE CASCADE,
    storage_bucket varchar(63) NOT NULL DEFAULT 'report-artifacts',
    object_key text NOT NULL,
    content_sha256 char(64) NOT NULL,
    byte_size bigint NOT NULL,
    content_type varchar(64) NOT NULL DEFAULT 'application/pdf',
    produced_by uuid,
    produced_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    -- B4-D6: exactly one artefact record per finalised report version.
    CONSTRAINT report_version_artifacts_version_key UNIQUE (report_version_id),
    -- B4-D6: the private, named bucket only (no external/alternative storage).
    CONSTRAINT report_version_artifacts_bucket_check CHECK (storage_bucket = 'report-artifacts'),
    CONSTRAINT report_version_artifacts_type_check CHECK (content_type = 'application/pdf'),
    -- B4-D6: derive the mandated key layout from the row itself.
    CONSTRAINT report_version_artifacts_key_check CHECK (
        object_key = organization_id::text || '/' || report_id::text || '/' || report_version_id::text || '.pdf'
    ),
    -- B4-D7: SHA-256, lowercase hex. No SHA-512, no MD5 fallback.
    CONSTRAINT report_version_artifacts_sha256_check CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT report_version_artifacts_size_check CHECK (byte_size > 0)
);

COMMENT ON TABLE public.report_version_artifacts IS $cmt$
B4/S5 (PO B4-D5/D6/D7): the frozen report artefact produced at finalisation.
Append-only — one row per finalised report version; UPDATE/DELETE are not granted
and no such policy exists. Immutability is enforced by this append-only record plus
the FINAL state of the report version; corrections create a new version (D15/DM-7).
The object lives in the private Supabase Storage bucket 'report-artifacts' under
{organization_id}/{report_id}/{version_id}.pdf and is reachable only through
short-lived signed URLs issued after authorization.
$cmt$;
COMMENT ON COLUMN public.report_version_artifacts.content_sha256 IS
  'SHA-256 (lowercase hex) of the stored frozen bytes (B4-D7). Never updated.';
COMMENT ON COLUMN public.report_version_artifacts.object_key IS
  'Derived key: {organization_id}/{report_id}/{report_version_id}.pdf (B4-D6). Never updated.';

-- ---------------------------------------------------------------------------
-- 2. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_rva_organization
    ON public.report_version_artifacts (organization_id);
CREATE INDEX IF NOT EXISTS idx_rva_report
    ON public.report_version_artifacts (report_id);

-- ---------------------------------------------------------------------------
-- 3. RLS — member read; Owner/Admin insert; NO update/delete (append-only)
-- ---------------------------------------------------------------------------
ALTER TABLE public.report_version_artifacts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.report_version_artifacts FROM anon;
-- Append-only: INSERT + SELECT are granted; UPDATE/DELETE are deliberately NOT.
REVOKE ALL ON TABLE public.report_version_artifacts FROM authenticated;
GRANT SELECT, INSERT ON TABLE public.report_version_artifacts TO authenticated;
DROP POLICY IF EXISTS report_version_artifacts_read ON public.report_version_artifacts;
CREATE POLICY report_version_artifacts_read
    ON public.report_version_artifacts FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));
DROP POLICY IF EXISTS report_version_artifacts_insert ON public.report_version_artifacts;
CREATE POLICY report_version_artifacts_insert
    ON public.report_version_artifacts FOR INSERT TO authenticated
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

COMMIT;
