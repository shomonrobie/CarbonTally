-- ============================================================================
-- P17-C — Contractual instruments and instrument allocations
-- File: 20261011000000_p17c_contractual_instruments_and_allocations.sql
--
-- Authority: docs/architecture/artifacts/p17_schema_delta_20250925.md §3.1, §3.2,
--            §10.6 (canonical terminology). Scope 2 domain matrix DC-09.
--
-- Why: Scope 2 market-based accounting backed by contractual instruments
-- (energy attribute certificates, guarantees of origin, PPAs, green tariffs,
-- supplier-specific contracts) is not expressible with the existing 141-table
-- inventory. This migration adds the two entities the architecture names and
-- nothing else.
--
-- Canonical terminology (§10.6): the CONCEPTUAL name for the claiming tenant is
-- `claimant_organization_id` (used in the Scope 2 domain matrix and DC-09). The
-- PHYSICAL column is `organization_id`, so the table follows the uniform P17
-- tenant/RLS convention. The two are one-to-one.
--
-- Tenant safety:
--   * organization_id is the RLS tenant key on BOTH tables.
--   * instrument_allocations carries a COMPOSITE foreign key
--     (instrument_id, organization_id) -> contractual_instruments(id, organization_id),
--     which makes a cross-tenant allocation structurally impossible rather than
--     merely policy-denied.
--
-- Additive only: two new tables. No existing table, column, row, index or policy
-- is modified.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. contractual_instruments (P17-C) — the instrument the tenant CLAIMS
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.contractual_instruments (
    id          uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,

    instrument_type text NOT NULL,
    identifier      text NOT NULL,
    issuer          text,
    source_facility text,
    geography       text NOT NULL,

    generation_period_start date,
    generation_period_end   date,
    vintage_year            integer,

    quantity numeric NOT NULL,
    unit     text NOT NULL,

    valid_from date,
    valid_to   date,

    retirement_status    text NOT NULL DEFAULT 'active',
    retirement_reference text,

    evidence_item_id uuid REFERENCES public.evidence_line_items(id) ON DELETE SET NULL,

    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT contractual_instruments_type_check CHECK (instrument_type IN (
        'energy_attribute_certificate', 'guarantee_of_origin',
        'supplier_specific_contract', 'ppa', 'rec', 'green_tariff', 'other')),
    CONSTRAINT contractual_instruments_quantity_check CHECK (quantity > 0),
    CONSTRAINT contractual_instruments_retirement_check
        CHECK (retirement_status IN ('active', 'retired', 'cancelled')),
    CONSTRAINT contractual_instruments_vintage_check
        CHECK (vintage_year IS NULL OR vintage_year BETWEEN 1990 AND 2200),
    CONSTRAINT contractual_instruments_period_check
        CHECK (generation_period_start IS NULL OR generation_period_end IS NULL
               OR generation_period_end >= generation_period_start),
    -- one instrument identity per tenant
    CONSTRAINT contractual_instruments_identity_unique
        UNIQUE (organization_id, instrument_type, identifier),
    -- required by the allocation composite FK below
    CONSTRAINT contractual_instruments_id_org_unique UNIQUE (id, organization_id)
);

COMMENT ON TABLE public.contractual_instruments IS
    'P17-C: a contractual instrument claimed by an organization for Scope 2 market-based accounting. organization_id IS the claimant organisation (conceptual name claimant_organization_id, §10.6).';
COMMENT ON COLUMN public.contractual_instruments.vintage_year IS
    'P17-C: generation vintage. The factor-year guard is preserved: a vintage mismatch must never silently substitute a factor from another year.';

CREATE INDEX IF NOT EXISTS idx_contractual_instruments_org_geo_vintage
    ON public.contractual_instruments (organization_id, geography, vintage_year);
CREATE INDEX IF NOT EXISTS idx_contractual_instruments_org_retirement
    ON public.contractual_instruments (organization_id, retirement_status);

-- ---------------------------------------------------------------------------
-- 2. instrument_allocations (P17-C) — the claim applied to a market-based result
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.instrument_allocations (
    id          uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    instrument_id   uuid NOT NULL,

    calculation_snapshot_id uuid REFERENCES public.calculation_snapshots(id) ON DELETE RESTRICT,
    emissions_log_id        uuid REFERENCES public.emissions_logs(id) ON DELETE RESTRICT,

    allocated_quantity numeric NOT NULL,
    allocated_unit     text NOT NULL,

    allocation_period_start date NOT NULL,
    allocation_period_end   date NOT NULL,

    claim_reference text,

    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT instrument_allocations_quantity_check CHECK (allocated_quantity > 0),
    CONSTRAINT instrument_allocations_period_check
        CHECK (allocation_period_end >= allocation_period_start),
    -- one allocation of one instrument to one result
    CONSTRAINT instrument_allocations_unique
        UNIQUE (instrument_id, allocation_period_start, allocation_period_end, calculation_snapshot_id),
    -- cross-tenant claim impossibility: the allocation's organization must be the
    -- instrument's organization, enforced structurally rather than by policy.
    CONSTRAINT instrument_allocations_instrument_org_fkey
        FOREIGN KEY (instrument_id, organization_id)
        REFERENCES public.contractual_instruments (id, organization_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE public.instrument_allocations IS
    'P17-C: the allocation of a contractual instrument quantity to a market-based Scope 2 result. UNIQUE (instrument_id, period, calculation_snapshot_id) means one instrument cannot be claimed twice for the same result.';
COMMENT ON CONSTRAINT instrument_allocations_instrument_org_fkey ON public.instrument_allocations IS
    'P17-C/DC-09: composite FK makes a cross-tenant instrument claim structurally impossible.';
COMMENT ON COLUMN public.instrument_allocations.allocated_quantity IS
    'P17-C: quantity allocated. sum(allocated_quantity) <= instrument.quantity is NOT guaranteed by a single-row CHECK and is therefore enforced by the allocating service plus the p17_instrument_over_allocated() detector. Stated explicitly: the database alone does not guarantee this sum.';

CREATE INDEX IF NOT EXISTS idx_instrument_allocations_instrument
    ON public.instrument_allocations (instrument_id);
CREATE INDEX IF NOT EXISTS idx_instrument_allocations_snapshot
    ON public.instrument_allocations (calculation_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_instrument_allocations_org
    ON public.instrument_allocations (organization_id);

-- ---------------------------------------------------------------------------
-- 3. RLS for both P17-C tables (established convention: ENABLE, explicit GRANTs,
--    anon denied, policies reuse public.is_org_member(uuid)).
-- ---------------------------------------------------------------------------
ALTER TABLE public.contractual_instruments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.contractual_instruments FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.contractual_instruments TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.contractual_instruments FROM authenticated;
GRANT ALL ON TABLE public.contractual_instruments TO service_role;

ALTER TABLE public.instrument_allocations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.instrument_allocations FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.instrument_allocations TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.instrument_allocations FROM authenticated;
GRANT ALL ON TABLE public.instrument_allocations TO service_role;

DROP POLICY IF EXISTS contractual_instruments_org_select ON public.contractual_instruments;
CREATE POLICY contractual_instruments_org_select
    ON public.contractual_instruments FOR SELECT TO authenticated
    USING (public.is_org_member(organization_id));

DROP POLICY IF EXISTS contractual_instruments_org_insert ON public.contractual_instruments;
CREATE POLICY contractual_instruments_org_insert
    ON public.contractual_instruments FOR INSERT TO authenticated
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS contractual_instruments_org_update ON public.contractual_instruments;
CREATE POLICY contractual_instruments_org_update
    ON public.contractual_instruments FOR UPDATE TO authenticated
    USING (public.is_org_member(organization_id))
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS contractual_instruments_org_delete ON public.contractual_instruments;
CREATE POLICY contractual_instruments_org_delete
    ON public.contractual_instruments FOR DELETE TO authenticated
    USING (public.is_org_member(organization_id));

DROP POLICY IF EXISTS instrument_allocations_org_select ON public.instrument_allocations;
CREATE POLICY instrument_allocations_org_select
    ON public.instrument_allocations FOR SELECT TO authenticated
    USING (public.is_org_member(organization_id));

DROP POLICY IF EXISTS instrument_allocations_org_insert ON public.instrument_allocations;
CREATE POLICY instrument_allocations_org_insert
    ON public.instrument_allocations FOR INSERT TO authenticated
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS instrument_allocations_org_update ON public.instrument_allocations;
CREATE POLICY instrument_allocations_org_update
    ON public.instrument_allocations FOR UPDATE TO authenticated
    USING (public.is_org_member(organization_id))
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS instrument_allocations_org_delete ON public.instrument_allocations;
CREATE POLICY instrument_allocations_org_delete
    ON public.instrument_allocations FOR DELETE TO authenticated
    USING (public.is_org_member(organization_id));

-- ---------------------------------------------------------------------------
-- 4. DC-09 detector (declared after instrument_allocations exists).
--    This is a QUERY, not a constraint: a sum-versus-quantity rule cannot be a
--    single-row CHECK. The authoritative guard is the allocating service; this
--    function exists so the invariant can be asserted deterministically.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.p17_instrument_over_allocated(p_instrument uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT COALESCE(SUM(a.allocated_quantity), 0) > i.quantity
      FROM public.contractual_instruments i
      LEFT JOIN public.instrument_allocations a ON a.instrument_id = i.id
     WHERE i.id = p_instrument
     GROUP BY i.quantity;
$$;

COMMENT ON FUNCTION public.p17_instrument_over_allocated(uuid) IS
    'P17-C/DC-09: true when the sum of allocations on an instrument exceeds the instrument quantity. Read-only detector; enforcement is in the allocating service.';

-- ============================================================================
-- VERIFICATION CHECKLIST (P17-C)
--   [ ] contractual_instruments + instrument_allocations exist
--   [ ] UNIQUE (organization_id, instrument_type, identifier) present
--   [ ] composite FK (instrument_id, organization_id) present -> cross-tenant claim impossible
--   [ ] both tables RLS ENABLED; anon has no privilege; policies use is_org_member
--   [ ] p17_instrument_over_allocated() exists and is read-only
--   [ ] re-running this file is a no-op
--   [ ] NO existing table modified
-- ============================================================================


