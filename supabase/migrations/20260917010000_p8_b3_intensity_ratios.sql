-- ============================================================================
-- CarbonTally Phase 8 Reporting / Disclosure — B3 (Disclosure Model
-- Integration) — migration 2 of 2 (B3-2)
-- File: 20260917010000_p8_b3_intensity_ratios.sql
--
-- Purpose (contract §6.2, §17):
--   public.disclosure_intensity_ratios — the ORGANISATION-SCOPED, per report
--   version selection of a denominator from the controlled catalogue, with the
--   customer's confirmation and a mandatory selection basis persisted.
--
-- RATIFIED CONSTRAINTS HONOURED
--   * D11-CAT: the denominator is chosen from the controlled catalogue (FK to
--     disclosure_intensity_denominator_types with ON DELETE RESTRICT — a
--     referenced capability cannot be silently removed).
--   * D11-CAT: CarbonTally may RECOMMEND but must NEVER silently select; the
--     selection and its basis are persisted, and confirmation is recorded
--     (selection_source + confirmed_by/confirmed_at).
--   * No arbitrary/customer-authored denominator: the FK is the only path.
--
-- SCOPE DISCIPLINE (B3-2 only)
--   * ADDITIVE + IDEMPOTENT. Creates exactly ONE new table; MODIFIES ZERO
--     existing tables, grants, policies or RLS flags.
--   * NO trigger and NO retention artefact (the B2-D11 analogue): ratio_value
--     is computed by the application layer, not by the database.
--   * NO projections, NO B4, NO P1/P2, NO RLS remediation, NO Phase 8-X.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.disclosure_intensity_denominator_types') IS NULL THEN
        RAISE EXCEPTION
            'B3-2 precondition failed: public.disclosure_intensity_denominator_types is absent. Apply 20260917000000_p8_b3_intensity_catalogue.sql first.';
    END IF;
    IF to_regclass('public.disclosure_values') IS NULL
       OR to_regclass('public.report_versions') IS NULL
       OR to_regclass('public.organizations') IS NULL THEN
        RAISE EXCEPTION
            'B3-2 precondition failed: disclosure_values / report_versions / organizations are absent. Apply B1 and verify the report lifecycle schema first.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.disclosure_intensity_ratios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_intensity_ratios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_version_id uuid NOT NULL REFERENCES public.report_versions(id) ON DELETE CASCADE,
    denominator_type_id uuid NOT NULL REFERENCES public.disclosure_intensity_denominator_types(id) ON DELETE RESTRICT,
    numerator_disclosure_value_id uuid REFERENCES public.disclosure_values(id) ON DELETE SET NULL,
    denominator_value numeric,
    denominator_unit varchar(40),
    ratio_value numeric,
    selection_basis text NOT NULL,
    selection_source varchar(30) NOT NULL DEFAULT 'CUSTOMER_SELECTED',
    confirmed_by uuid,
    confirmed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_intensity_ratios_unique
        UNIQUE (organization_id, report_version_id, denominator_type_id),
    CONSTRAINT disclosure_intensity_ratios_selection_source_check
        CHECK (selection_source IN ('CUSTOMER_SELECTED', 'CUSTOMER_CONFIRMED', 'CARBONTALLY_RECOMMENDED')),
    CONSTRAINT disclosure_intensity_ratios_basis_check
        CHECK (length(btrim(selection_basis)) > 0),
    CONSTRAINT disclosure_intensity_ratios_denominator_positive
        CHECK (denominator_value IS NULL OR denominator_value > 0),
    CONSTRAINT disclosure_intensity_ratios_ratio_positive
        CHECK (ratio_value IS NULL OR ratio_value >= 0),
    -- A CARBONTALLY_RECOMMENDED row is a proposal, never a completed selection:
    -- it must not carry a confirmation stamp.
    CONSTRAINT disclosure_intensity_ratios_recommendation_not_confirmed
        CHECK (selection_source <> 'CARBONTALLY_RECOMMENDED' OR confirmed_at IS NULL)
);

COMMENT ON TABLE public.disclosure_intensity_ratios IS
  'B3: organisation-scoped selection of an intensity denominator from the controlled catalogue, with persisted basis and recorded confirmation (D11-CAT). ratio_value is application-computed; there is no trigger and no retention artefact (B2-D11 analogue).';
COMMENT ON COLUMN public.disclosure_intensity_ratios.selection_source IS
  'CUSTOMER_SELECTED / CUSTOMER_CONFIRMED / CARBONTALLY_RECOMMENDED. CarbonTally may recommend but must never silently select (D11-CAT): a RECOMMENDED row cannot carry a confirmation stamp.';
COMMENT ON COLUMN public.disclosure_intensity_ratios.ratio_value IS
  'Computed by the application layer as numerator/denominator; persisted for provenance. Never hand-edited; recomputed when inputs change for a non-finalised version.';

-- ---------------------------------------------------------------------------
-- 2. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_diir_organization
    ON public.disclosure_intensity_ratios (organization_id);
CREATE INDEX IF NOT EXISTS idx_diir_report_version
    ON public.disclosure_intensity_ratios (report_version_id);
CREATE INDEX IF NOT EXISTS idx_diir_denominator_type
    ON public.disclosure_intensity_ratios (denominator_type_id);

-- ---------------------------------------------------------------------------
-- 3. RLS — organisation-scoped: member READ; org-admin WRITE
--    (mirrors the B1 disclosure_applicability_assessments posture).
-- ---------------------------------------------------------------------------
ALTER TABLE public.disclosure_intensity_ratios ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.disclosure_intensity_ratios FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.disclosure_intensity_ratios TO authenticated;
DROP POLICY IF EXISTS disclosure_intensity_ratios_read ON public.disclosure_intensity_ratios;
CREATE POLICY disclosure_intensity_ratios_read
    ON public.disclosure_intensity_ratios FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));
DROP POLICY IF EXISTS disclosure_intensity_ratios_write ON public.disclosure_intensity_ratios;
CREATE POLICY disclosure_intensity_ratios_write
    ON public.disclosure_intensity_ratios FOR ALL TO authenticated
    USING (public.p8_disclosure_is_org_admin(organization_id))
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

COMMIT;
