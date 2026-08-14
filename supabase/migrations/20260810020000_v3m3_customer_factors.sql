-- ============================================================================
-- CarbonTally V3 — Implementation Phase 1, Migration V3M-3
-- File: 20260810020000_v3m3_customer_factors.sql
--
-- Implements the approved Customer-Owned Emission Factors architecture
-- (ADR-V3-002 — DECIDED, Option B; ADR-V3-014 — snapshot FK O1 DECIDED;
-- V3 IA §8 V3M-3; V3 Database Impact Plan §7).
--
-- Scope (strictly V3M-3):
--   * customer_factors       (NEW table — dedicated org-owned factor domain)
--   * calculation_snapshots  (EXTEND — O1 snapshot-FK relaxation)
--
-- Approved sub-decisions (register ADR-V3-002, resolved v1.1):
--   * D-cf-3 approval authority — Organization Admin/Owner approves; staff may
--     create/edit/validate drafts but cannot approve their own factor. Status
--     lifecycle DRAFT → ACTIVE → ARCHIVED/INACTIVE (soft-deactivate).
--   * D-cf-2 snapshot FK — Option O1: nullable `factor_id` + `factor_kind` +
--     optional `customer_factor_id` with an exactly-one-source check.
--   * D-cf-5 factor precedence — approved customer factor first (backend
--     matching concern; no schema impact here).
--   * R3 consultant access — via the existing consultant-client RLS model
--     (`is_org_consultant()` on SELECT); no global consultant access.
--
-- Non-negotiables:
--   * Customer factors NEVER go into global `emission_factors` (REJECTED).
--   * No second matching/calculation engine; no second snapshot system;
--     no `customer_calculation_snapshots` table (REJECTED).
--   * No new enums — status/factor_kind use VARCHAR + CHECK (existing style).
--   * No factor data is touched (baseline DEFRA 7,029 · SEAI 20 · TOTAL 7,049).
--
-- RLS (reuses the RC2/M8 conventions):
--   * customer_factors: RLS enabled; service_role ALL; authenticated DML (no
--     TRUNCATE/TRIGGER/REFERENCES/MAINTAIN); SELECT = org member OR authorised
--     consultant; INSERT/UPDATE = org member; NO DELETE policy (delete
--     restricted — soft-deactivate via status), mirroring factor_aliases.
--   * calculation_snapshots: existing calc_snapshots_select_own is unchanged;
--     no policy on this table is added or dropped.
--
-- Safety:
--   * Additive and backward compatible; existing snapshot rows keep their
--     `factor_id` and gain `factor_kind = 'emission_factor'` (NOT NULL DEFAULT).
--   * Exactly-one-source CHECK preserves immutable calculation provenance.
--   * FK `customer_factor_id` → customer_factors(id) ON DELETE RESTRICT (an
--     approved customer factor referenced by a snapshot can never be deleted).
--
-- Idempotent: CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS, guarded FK,
-- guarded CHECK, CREATE INDEX IF NOT EXISTS, DROP POLICY IF EXISTS + CREATE
-- POLICY, DROP TRIGGER IF EXISTS + CREATE TRIGGER.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. customer_factors (NEW)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.customer_factors (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description TEXT,
    activity_type VARCHAR NOT NULL,
    co2e_multiplier NUMERIC NOT NULL CHECK (co2e_multiplier >= 0),
    unit TEXT,
    scope TEXT,
    country VARCHAR NOT NULL DEFAULT 'GB'
        CHECK (country IN ('GB','IE')),
    reporting_year INTEGER NOT NULL,
    factor_source TEXT NOT NULL DEFAULT 'CUSTOMER',
    source_reference TEXT,
    category TEXT,
    methodology TEXT,
    effective_from DATE,
    effective_to DATE,
    status VARCHAR NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft','active','inactive','archived')),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    metadata JSONB,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT customer_factors_effective_window_check
        CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from)
);

-- Per-version family uniqueness (mirrors the emission_factors natural key,
-- org-scoped, with version as the revision axis). COALESCE follows the
-- factor_aliases idiom so nullable unit/scope still participate.
CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_factors_family_version
    ON public.customer_factors (
        organization_id, activity_type, reporting_year, country,
        COALESCE(unit, ''), COALESCE(scope, ''), version
    );

CREATE INDEX IF NOT EXISTS idx_customer_factors_organization_id
    ON public.customer_factors (organization_id);

CREATE INDEX IF NOT EXISTS idx_customer_factors_org_status
    ON public.customer_factors (organization_id, status);

COMMENT ON TABLE public.customer_factors IS
    'Customer-owned emission factors (ADR-V3-002 — Option B, dedicated org-scoped table). '
    'Distinct from global emission_factors. Lifecycle: draft → active → inactive/archived; '
    'approved customer factors win over CarbonTally factors in matching (D-cf-5).';
COMMENT ON COLUMN public.customer_factors.organization_id IS
    'Owning customer organization (tenant anchor + RLS scope).';
COMMENT ON COLUMN public.customer_factors.co2e_multiplier IS
    'The factor value (quantity × multiplier → CO₂e). Never auto-promoted to emission_factors.';
COMMENT ON COLUMN public.customer_factors.factor_source IS
    'Provenance: ''CUSTOMER'' (or supplier name). Free-text, matching emission_factors.factor_source style.';
COMMENT ON COLUMN public.customer_factors.status IS
    'Lifecycle: draft (created/edited/validated) → active (approved by Organization Admin/Owner; '
    'D-cf-3) → inactive/archived (soft-deactivate; protects historical snapshots).';
COMMENT ON COLUMN public.customer_factors.version IS
    'Monotonic revision per factor family; an update creates a new version so historical '
    'calculations never silently change.';
COMMENT ON COLUMN public.customer_factors.effective_to IS
    'Validity window end; empty effective window permitted (no CHECK on nullability).';

-- updated_at maintenance trigger (RC2 006 convention — dynamic install covered
-- tables existing at RC2 time; this table is new, so the trigger is installed
-- here explicitly).
DROP TRIGGER IF EXISTS trg_set_updated_at_customer_factors ON public.customer_factors;
CREATE TRIGGER trg_set_updated_at_customer_factors
    BEFORE UPDATE ON public.customer_factors
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 2. customer_factors RLS (M8 conventions; no global consultant access — R3)
-- ---------------------------------------------------------------------------
ALTER TABLE public.customer_factors ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.customer_factors TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.customer_factors TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.customer_factors FROM authenticated;

-- SELECT: org member OR authorised consultant (existing consultant-client model).
DROP POLICY IF EXISTS customer_factors_select_own ON public.customer_factors;
CREATE POLICY customer_factors_select_own ON public.customer_factors
    FOR SELECT TO authenticated
    USING (
        public.is_org_member(organization_id)
        OR public.is_org_consultant(organization_id)
    );

-- INSERT: org member only.
DROP POLICY IF EXISTS customer_factors_insert_own ON public.customer_factors;
CREATE POLICY customer_factors_insert_own ON public.customer_factors
    FOR INSERT TO authenticated
    WITH CHECK (
        public.is_org_member(organization_id)
    );

-- UPDATE: org member only (status transitions incl. approval are member-level;
-- the org-admin/owner approval authority is enforced at the API layer, D-cf-3).
DROP POLICY IF EXISTS customer_factors_update_own ON public.customer_factors;
CREATE POLICY customer_factors_update_own ON public.customer_factors
    FOR UPDATE TO authenticated
    USING (public.is_org_member(organization_id))
    WITH CHECK (public.is_org_member(organization_id));

-- NO DELETE policy: deletion is restricted (soft-deactivate via status) so
-- historical calculation snapshots and approval history remain intact.

-- ---------------------------------------------------------------------------
-- 3. calculation_snapshots — O1 snapshot-FK relaxation (ADR-V3-014)
--    Provenance may resolve to either emission_factors or customer_factors.
-- ---------------------------------------------------------------------------

-- 3.1 factor_id becomes nullable (existing FK → emission_factors kept as-is).
ALTER TABLE public.calculation_snapshots
    ALTER COLUMN factor_id DROP NOT NULL;

-- 3.2 factor_kind discriminator (NOT NULL DEFAULT covers existing rows).
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS factor_kind VARCHAR NOT NULL DEFAULT 'emission_factor'
        CHECK (factor_kind IN ('emission_factor','customer_factor'));

-- 3.3 optional customer_factor_id reference.
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS customer_factor_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'calculation_snapshots_customer_factor_id_fkey'
    ) THEN
        ALTER TABLE public.calculation_snapshots
            ADD CONSTRAINT calculation_snapshots_customer_factor_id_fkey
            FOREIGN KEY (customer_factor_id) REFERENCES public.customer_factors(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

-- 3.4 exactly-one-source check (immutable provenance preserved):
--     emission_factor rows:  factor_id IS NOT NULL, customer_factor_id IS NULL
--     customer_factor rows:  factor_id IS NULL,     customer_factor_id IS NOT NULL
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'calculation_snapshots_exactly_one_source_check'
    ) THEN
        ALTER TABLE public.calculation_snapshots
            ADD CONSTRAINT calculation_snapshots_exactly_one_source_check
            CHECK (
                (factor_kind = 'emission_factor'
                 AND factor_id IS NOT NULL
                 AND customer_factor_id IS NULL)
                OR
                (factor_kind = 'customer_factor'
                 AND factor_id IS NULL
                 AND customer_factor_id IS NOT NULL)
            );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_calculation_snapshots_customer_factor_id
    ON public.calculation_snapshots (customer_factor_id);

COMMENT ON COLUMN public.calculation_snapshots.factor_id IS
    'emission_factors.id used (O1). Nullable ONLY when factor_kind = ''customer_factor'' '
    '(then customer_factor_id is set). ON DELETE RESTRICT — a referenced factor can never be deleted.';
COMMENT ON COLUMN public.calculation_snapshots.factor_kind IS
    'Snapshot provenance source discriminator (O1): ''emission_factor'' (CarbonTally '
    'emission_factors) or ''customer_factor'' (customer_factors).';
COMMENT ON COLUMN public.calculation_snapshots.customer_factor_id IS
    'customer_factors.id used for customer-owned factor provenance (O1). NULL for '
    'CarbonTally-managed factors. ON DELETE RESTRICT — an approved customer factor referenced '
    'by a snapshot can never be deleted.';

-- ============================================================================
-- VERIFICATION CHECKLIST (V3M-3)
--   [ ] customer_factors table exists (org-scoped, status CHECK, version, metadata)
--   [ ] Per-version family UNIQUE index + org/status indexes exist
--   [ ] RLS enabled on customer_factors; service_role ALL; authenticated DML
--       (no TRUNCATE); select = is_org_member OR is_org_consultant; insert/update
--       = is_org_member; NO delete policy
--   [ ] trg_set_updated_at_customer_factors installed
--   [ ] calculation_snapshots.factor_id is now nullable; factor_kind NOT NULL
--       DEFAULT 'emission_factor'; customer_factor_id nullable FK → customer_factors
--       ON DELETE RESTRICT
--   [ ] exactly-one-source CHECK present and satisfied by existing rows
--   [ ] Index idx_calculation_snapshots_customer_factor_id exists
--   [ ] Existing snapshots untouched (factor_id preserved, factor_kind defaulted)
--   [ ] emission_factors untouched (7,049 baseline preserved; no org rows)
--   [ ] Re-running this file is a no-op
-- ============================================================================
