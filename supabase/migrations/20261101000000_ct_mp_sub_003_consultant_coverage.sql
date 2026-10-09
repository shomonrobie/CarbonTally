-- ============================================================================
-- CarbonTally CT-MP-SUB-003 — CONSULTANT-SPONSORED MANUAL PROCESSING COVERAGE
-- File: 20261101000000_ct_mp_sub_003_consultant_coverage.sql
--
-- PO SPEC: docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md
-- (CT-PO-MP-SUB-003, PO APPROVED — AUTHORITATIVE).
--
-- Adds the ONE persistent record the consultant-sponsored entitlement model was
-- missing: the per-client SELECTED-CLIENTS allocation ledger.
--
--   public.consultant_mp_allocations
--       consultant_id        -> consultant_profiles.id   (the FIRM)
--       consultant_client_id -> consultant_clients.id    (the firm<->org grant)
--       organization_id      -> organizations.id        (the covered client)
--       state                -> 'active' | 'released'
--
-- Design boundary (PO spec §25 — concepts are NOT collapsed):
--   * COMMERCIAL coverage (mode + selected capacity) is expressed by the
--     consultant firm's OWN organization subscription plan
--     (billing_plans.features.consultant_manual_processing). This migration does
--     NOT create a second subscription/plan/coverage table — the existing D37
--     org-scoped commercial model remains authoritative and is read server-side.
--   * ELIGIBILITY remains the existing consultant_client relationship.
--   * ALLOCATION (this table) exists ONLY for selected-mode explicit capacity.
--     ALL_ELIGIBLE_CLIENTS coverage needs no per-client row.
--
-- What this migration deliberately does NOT create:
--   * no second subscription/entitlement table (D37 commercial model reused);
--   * no second consultant/relationship model (consultant_clients reused);
--   * no second PE model or assignment ledger (D38 + FIN-06 routing reused);
--   * no parallel audit system (public.audit_logs reused by the API).
--
-- SECURITY POSTURE (identical to FIN-06 governance + routing): RLS ENABLED with
-- ZERO policies and both client roles revoked. Only the service role (the
-- FastAPI backend, which performs the CarbonTally-Admin authorization at the API
-- boundary) can read or write these rows. An allocation row is NOT an
-- authorization grant: consultant-client access keeps its own gate.
--
-- SCOPE DISCIPLINE: additive + idempotent. Creates exactly ONE new table.
-- No existing table, column, policy, grant, function, trigger, storage object or
-- data row is modified. No production data is seeded.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Preconditions
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.organizations') IS NULL THEN
        RAISE EXCEPTION 'CT-MP-SUB-003 precondition failed: public.organizations is absent';
    END IF;
    IF to_regclass('public.consultant_profiles') IS NULL THEN
        RAISE EXCEPTION 'CT-MP-SUB-003 precondition failed: public.consultant_profiles is absent';
    END IF;
    IF to_regclass('public.consultant_clients') IS NULL THEN
        RAISE EXCEPTION 'CT-MP-SUB-003 precondition failed: public.consultant_clients is absent';
    END IF;
    IF to_regclass('public.customer_subscriptions') IS NULL THEN
        RAISE EXCEPTION 'CT-MP-SUB-003 precondition failed: public.customer_subscriptions is absent (D37 commercial model required)';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. public.consultant_mp_allocations (selected-mode allocation ledger)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.consultant_mp_allocations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    -- The consultant FIRM (consultant_profiles.id). The firm's organisation
    -- subscription is the commercial source of the sponsored coverage.
    consultant_id uuid NOT NULL
        REFERENCES public.consultant_profiles (id) ON DELETE RESTRICT,
    -- The firm <-> organisation relationship grant (ELIGIBILITY anchor).
    consultant_client_id uuid NOT NULL
        REFERENCES public.consultant_clients (id) ON DELETE RESTRICT,
    -- The covered client organisation (denormalised for fast reads).
    organization_id uuid NOT NULL
        REFERENCES public.organizations (id) ON DELETE RESTRICT,
    state text NOT NULL DEFAULT 'active',
    reason text,
    allocated_by uuid NOT NULL,
    allocated_at timestamptz NOT NULL DEFAULT now(),
    released_by uuid,
    released_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT consultant_mp_allocations_state_check
        CHECK (state IN ('active', 'released'))
);

COMMENT ON TABLE public.consultant_mp_allocations IS $ctmp$
CT-MP-SUB-003 consultant-sponsored Manual Processing SELECTED-CLIENTS allocation
ledger. One row per allocation attempt; a released row is retained for audit and
returns its capacity unit. Only the service role (backend, behind the
CarbonTally-Admin authorization) may read or write this table: RLS is ENABLED
with ZERO policies and both client roles are revoked. An allocation row is NOT
an authorization grant — consultant access keeps its own consultant_clients gate.
$ctmp$;

COMMENT ON COLUMN public.consultant_mp_allocations.consultant_id IS
'The consultant firm (consultant_profiles.id). Its organisation subscription carries the purchased coverage.';
COMMENT ON COLUMN public.consultant_mp_allocations.consultant_client_id IS
'The consultant_clients grant (firm <-> organisation) that establishes ELIGIBILITY for this client.';
COMMENT ON COLUMN public.consultant_mp_allocations.organization_id IS
'The covered client organisation (organizations.id).';
COMMENT ON COLUMN public.consultant_mp_allocations.state IS
'active consumes one selected-capacity unit; released returns the unit. History is never deleted.';

-- ---------------------------------------------------------------------------
-- 3. Indexes + the duplicate-ACTIVE-allocation guarantee (PO spec §20)
-- ---------------------------------------------------------------------------
-- At most ONE active allocation per (firm, organisation): prevents duplicate
-- active allocations consuming more than one capacity unit for the same client.
CREATE UNIQUE INDEX IF NOT EXISTS uq_consultant_mp_allocations_active
    ON public.consultant_mp_allocations (consultant_id, organization_id)
    WHERE state = 'active';

CREATE INDEX IF NOT EXISTS idx_consultant_mp_allocations_firm
    ON public.consultant_mp_allocations (consultant_id, state);
CREATE INDEX IF NOT EXISTS idx_consultant_mp_allocations_org
    ON public.consultant_mp_allocations (organization_id, state);

-- ---------------------------------------------------------------------------
-- 4. RLS — fail closed, service-role only (identical to FIN-06 governance)
-- ---------------------------------------------------------------------------
ALTER TABLE public.consultant_mp_allocations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.consultant_mp_allocations FROM anon;
REVOKE ALL ON TABLE public.consultant_mp_allocations FROM authenticated;
-- No policy is created: with RLS enabled and zero policies, every RLS-bound role
-- is denied by construction. The backend uses the service role (BYPASSRLS) and
-- performs the CarbonTally-Admin authorization at the API boundary.

COMMIT;

-- ============================================================================
-- VERIFICATION CHECKLIST (CT-MP-SUB-003)
--   [x] public.consultant_mp_allocations created (single new table)
--   [x] UNIQUE (consultant_id, organization_id) WHERE state='active'
--   [x] state CHECK ('active','released')
--   [x] FK integrity: consultant_profiles, consultant_clients, organizations
--   [x] RLS enabled, ZERO policies (client roles fail closed)
--   [x] anon + authenticated revoked; service_role untouched (unchanged)
-- ============================================================================

