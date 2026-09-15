-- ============================================================================
-- CarbonTally Phase 8 Reporting / Disclosure — B4 (Narrative, Finalisation and
-- Frozen Artefact) — migration 1 (B4-1)
-- File: 20260918000000_p8_b4_narrative_overlay.sql
--
-- Purpose (task CT-P8-B4-CONTRACT-AND-PO-DECISIONS-20260913-034; contract §7):
--   public.disclosure_narrative_entries — the requirement-bound narrative store.
--
-- RATIFIED CONSTRAINTS HONOURED (no new product decision is taken here)
--   * A1  — narrative is BOUNDED and REQUIREMENT-SPECIFIC: the binding
--           requirement_version_id is NOT NULL and is part of the unique key;
--           there is no report-wide narrative path.
--   * A1/P3 — authoring authority is Customer Owner/Admin (RLS write policy uses
--           the B1 helper public.p8_disclosure_is_org_admin); customers can
--           never edit calculated values/provenance (this table has no link
--           that could write them).
--   * A3  — NO arbitrary character/field limits: only a non-empty check and a
--           closed narrative_kind vocabulary. Any future limit must be
--           evidence-backed, not hard-coded here.
--   * DM-5 — the finalisation gate is a service/domain concern; the table only
--           records narrative state (DRAFT -> SUPERSEDED).
--   * D15  — historical immutability: application-side version guard; no trigger.
--
-- SCOPE DISCIPLINE (B4-1 only)
--   * ADDITIVE + IDEMPOTENT. Creates exactly ONE new table. MODIFIES ZERO
--     existing tables, grants, policies or RLS flags.
--   * No artefact/storage object (that is B4-2, gated on PO decisions B4-D5..D7).
--   * NO trigger; NO retention artefact (the B2-D11 / B3-D10 posture).
--   * NO B3 object change; NO calculation/provenance touch; NO P1/P2/RLS/8-X.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regprocedure('public.p8_disclosure_is_org_member(uuid)') IS NULL
       OR to_regprocedure('public.p8_disclosure_is_org_admin(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'B4-1 precondition failed: B1 helpers are absent. Apply 20260914000000_p8_b1_disclosure_model_foundation.sql first.';
    END IF;
    IF to_regclass('public.disclosure_requirement_versions') IS NULL
       OR to_regclass('public.disclosure_values') IS NULL
       OR to_regclass('public.report_versions') IS NULL THEN
        RAISE EXCEPTION
            'B4-1 precondition failed: the B3/B1 requirement spine or report_versions is absent. Apply the Phase 8 chain (S3, B1, B2, B3) before B4-1.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.disclosure_narrative_entries
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_narrative_entries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_version_id uuid NOT NULL REFERENCES public.report_versions(id) ON DELETE CASCADE,
    requirement_version_id uuid NOT NULL REFERENCES public.disclosure_requirement_versions(id) ON DELETE RESTRICT,
    disclosure_value_id uuid REFERENCES public.disclosure_values(id) ON DELETE SET NULL,
    narrative_kind varchar(30) NOT NULL DEFAULT 'CUSTOMER_COMMENTARY',
    body text NOT NULL,
    state varchar(20) NOT NULL DEFAULT 'DRAFT',
    authored_by uuid,
    authored_at timestamptz,
    updated_by uuid,
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT disclosure_narrative_entries_unique
        UNIQUE (report_version_id, requirement_version_id, narrative_kind),
    CONSTRAINT disclosure_narrative_entries_kind_check
        CHECK (narrative_kind IN ('CUSTOMER_COMMENTARY', 'METHODOLOGY_NOTE', 'EXPLANATION')),
    CONSTRAINT disclosure_narrative_entries_state_check
        CHECK (state IN ('DRAFT', 'SUPERSEDED')),
    -- A3: no arbitrary character limit. The only requirement is real content.
    CONSTRAINT disclosure_narrative_entries_body_check
        CHECK (length(btrim(body)) > 0)
);

COMMENT ON TABLE public.disclosure_narrative_entries IS
  'B4: requirement-bound customer narrative overlay (A1). One current entry per (report version, requirement version, kind). Authoring is Owner/Admin only and impossible on an APPROVED/FINAL version (application-side D15 guard). No trigger, no retention artefact (B2-D11 analogue).';
COMMENT ON COLUMN public.disclosure_narrative_entries.requirement_version_id IS
  'A1 binding: narrative is requirement-specific. NOT NULL by design - a report-wide narrative path does not exist.';
COMMENT ON COLUMN public.disclosure_narrative_entries.body IS
  'Plain text only (lifecycle spec 10.3). No arbitrary length limit (A3): only non-empty content is enforced here; any future limit must be evidence-backed.';

-- ---------------------------------------------------------------------------
-- 2. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dne_organization
    ON public.disclosure_narrative_entries (organization_id);
CREATE INDEX IF NOT EXISTS idx_dne_report_version
    ON public.disclosure_narrative_entries (report_version_id);
CREATE INDEX IF NOT EXISTS idx_dne_requirement
    ON public.disclosure_narrative_entries (requirement_version_id);

-- ---------------------------------------------------------------------------
-- 3. RLS — organisation-scoped: member READ; Owner/Admin WRITE (B1 posture)
-- ---------------------------------------------------------------------------
ALTER TABLE public.disclosure_narrative_entries ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.disclosure_narrative_entries FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.disclosure_narrative_entries TO authenticated;
DROP POLICY IF EXISTS disclosure_narrative_entries_read ON public.disclosure_narrative_entries;
CREATE POLICY disclosure_narrative_entries_read
    ON public.disclosure_narrative_entries FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));
DROP POLICY IF EXISTS disclosure_narrative_entries_write ON public.disclosure_narrative_entries;
CREATE POLICY disclosure_narrative_entries_write
    ON public.disclosure_narrative_entries FOR ALL TO authenticated
    USING (public.p8_disclosure_is_org_admin(organization_id))
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

COMMIT;
