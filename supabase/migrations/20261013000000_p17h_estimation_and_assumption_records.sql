-- ============================================================================
-- P17-H — Estimation records, assumption sets and double-counting detectors
-- File: 20261013000000_p17h_estimation_and_assumption_records.sql
--
-- Authority: docs/architecture/artifacts/p17_schema_delta_20250925.md §3.4,
--            §1 (migration 5 of 5), Scope 3 matrix DC-02/DC-04/DC-05/DC-07.
--
-- Why: the no-silent-estimation rule (invariant T-INV-12) requires that any
-- estimated value carries a persisted estimation record: method, inputs,
-- assumptions, factor, source, actor and timestamp. Estimated categories
-- (7 commuting, 11 use of sold products, 12 end-of-life, 14 franchises) and any
-- estimated line elsewhere cannot satisfy that rule today.
--
-- Also adds the read-only double-counting detectors the boundary controls need.
-- These are QUERIES, not constraints: a boundary rule spans rows and cannot be a
-- single-row CHECK. They exist so the invariants can be asserted deterministically
-- and audited by an operator; enforcement is in the application service.
--
-- Additive only: one new table plus read-only functions. No existing object is
-- modified. No estimate is fabricated.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. estimation_records (P17-H)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.estimation_records (
    id          uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,

    calculation_snapshot_id uuid REFERENCES public.calculation_snapshots(id) ON DELETE CASCADE,
    emissions_log_id        uuid REFERENCES public.emissions_logs(id) ON DELETE SET NULL,

    estimation_method text NOT NULL,
    inputs            jsonb NOT NULL DEFAULT '{}'::jsonb,
    assumptions       jsonb NOT NULL DEFAULT '{}'::jsonb,
    factor_id         uuid REFERENCES public.emission_factors(id) ON DELETE RESTRICT,
    source_reference  text,

    scope3_category smallint,

    actor_user_id uuid,
    actor_organization_id      uuid,
    acting_for_organization_id uuid,

    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT estimation_records_method_check CHECK (estimation_method IN (
        'average_data', 'proxy_data', 'spend_based', 'extrapolated',
        'supplier_specific', 'modelled', 'industry_average', 'other')),
    CONSTRAINT estimation_records_category_check
        CHECK (scope3_category IS NULL OR scope3_category BETWEEN 1 AND 15),
    -- no silent estimation: an estimation record must name its method and carry
    -- at least one assumption or input. A record that says nothing is not a record.
    CONSTRAINT estimation_records_substantiated_check
        CHECK (jsonb_typeof(assumptions) = 'object' AND jsonb_typeof(inputs) = 'object'
               AND (assumptions <> '{}'::jsonb OR inputs <> '{}'::jsonb))
);

COMMENT ON TABLE public.estimation_records IS
    'P17-H/T-INV-12: the persisted evidence that a value is estimated, with its method, inputs, assumptions, factor, source and actor. A value flagged as estimated without one of these rows violates the no-silent-estimation invariant.';
COMMENT ON COLUMN public.estimation_records.assumptions IS
    'P17-H: the assumption set. Must be non-empty unless inputs are present, so an "estimated" flag can never be unsubstantiated.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_estimation_records_snapshot
    ON public.estimation_records (calculation_snapshot_id)
    WHERE calculation_snapshot_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_estimation_records_org_category
    ON public.estimation_records (organization_id, scope3_category);

ALTER TABLE public.estimation_records ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.estimation_records FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.estimation_records TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.estimation_records FROM authenticated;
GRANT ALL ON TABLE public.estimation_records TO service_role;

DROP POLICY IF EXISTS estimation_records_org_select ON public.estimation_records;
CREATE POLICY estimation_records_org_select
    ON public.estimation_records FOR SELECT TO authenticated
    USING (public.is_org_member(organization_id));

DROP POLICY IF EXISTS estimation_records_org_insert ON public.estimation_records;
CREATE POLICY estimation_records_org_insert
    ON public.estimation_records FOR INSERT TO authenticated
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS estimation_records_org_update ON public.estimation_records;
CREATE POLICY estimation_records_org_update
    ON public.estimation_records FOR UPDATE TO authenticated
    USING (public.is_org_member(organization_id))
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS estimation_records_org_delete ON public.estimation_records;
CREATE POLICY estimation_records_org_delete
    ON public.estimation_records FOR DELETE TO authenticated
    USING (public.is_org_member(organization_id));

-- ---------------------------------------------------------------------------
-- 2. Double-counting / boundary detectors (read-only, deterministic)
--    Each returns the set of offending snapshot ids for one organization so the
--    rule can be asserted in a test and audited by an operator. None of them
--    mutates data and none of them is an authorization boundary.
-- ---------------------------------------------------------------------------

-- DC-04: a category 4 (upstream) or category 9 (downstream) result with no
-- transport boundary recorded is ambiguous and must not be counted.
CREATE OR REPLACE FUNCTION public.p17_dc04_unclassified_transport(p_org uuid)
RETURNS TABLE(snapshot_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT s.id
      FROM public.calculation_snapshots s
     WHERE s.organization_id = p_org
       AND s.scope3_category IN (4, 9)
       AND s.transport_boundary IS NULL;
$$;

-- DC-05: a category 5 (operations waste) or category 12 (sold-product end of
-- life) result with no waste origin recorded is ambiguous.
CREATE OR REPLACE FUNCTION public.p17_dc05_unclassified_waste(p_org uuid)
RETURNS TABLE(snapshot_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT s.id
      FROM public.calculation_snapshots s
     WHERE s.organization_id = p_org
       AND s.scope3_category IN (5, 12)
       AND s.waste_origin IS NULL;
$$;

-- DC-07: categories 8 (upstream leased assets) and 13 (downstream leased assets)
-- depend on the consolidation approach. If the organization has not decided one,
-- these results must fail closed rather than be counted.
CREATE OR REPLACE FUNCTION public.p17_dc07_consolidation_missing(p_org uuid)
RETURNS TABLE(snapshot_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT s.id
      FROM public.calculation_snapshots s
      JOIN public.organizations o ON o.id = s.organization_id
     WHERE s.organization_id = p_org
       AND s.scope3_category IN (8, 13)
       AND o.consolidation_approach IS NULL;
$$;

-- T-INV-12: an estimated result with no persisted estimation record is a
-- no-silent-estimation violation.
CREATE OR REPLACE FUNCTION public.p17_unsubstantiated_estimates(p_org uuid)
RETURNS TABLE(snapshot_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT s.id
      FROM public.calculation_snapshots s
     WHERE s.organization_id = p_org
       AND s.data_quality IN ('secondary_estimated', 'spend_based_estimated', 'modelled')
       AND NOT EXISTS (
            SELECT 1 FROM public.estimation_records e
             WHERE e.calculation_snapshot_id = s.id);
$$;

COMMENT ON FUNCTION public.p17_dc04_unclassified_transport(uuid) IS
    'P17-H/DC-04: category 4/9 snapshots with no transport boundary. Read-only detector.';
COMMENT ON FUNCTION public.p17_dc05_unclassified_waste(uuid) IS
    'P17-H/DC-05: category 5/12 snapshots with no waste origin. Read-only detector.';
COMMENT ON FUNCTION public.p17_dc07_consolidation_missing(uuid) IS
    'P17-H/DC-07: category 8/13 snapshots for an organization whose consolidation approach is undecided. Read-only detector; these must fail closed.';
COMMENT ON FUNCTION public.p17_unsubstantiated_estimates(uuid) IS
    'P17-H/T-INV-12: estimated snapshots with no estimation record. Read-only detector for the no-silent-estimation rule.';

-- ============================================================================
-- VERIFICATION CHECKLIST (P17-H)
--   [ ] estimation_records exists with the substantiated-assumption CHECK
--   [ ] at most one estimation record per snapshot (partial unique index)
--   [ ] RLS ENABLED; anon none; policies use is_org_member
--   [ ] p17_dc04 / dc05 / dc07 / unsubstantiated_estimates exist and are read-only
--   [ ] NO estimate, methodology or factor fabricated
--   [ ] re-running this file is a no-op
-- ============================================================================

