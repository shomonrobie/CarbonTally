-- ============================================================================
-- CarbonTally Phase 8 FIN-06 — MANUAL PROCESSING GOVERNANCE
-- File: 20260927000000_p8_fin06_manual_processing_governance.sql
--
-- PO DECISION (approved, P8-FINALIZATION-IMPLEMENT-001):
--   * Manual Processing is OFF by default;
--   * only CarbonTally Admin may enable/disable it (server-enforced);
--   * organisations, organisation admins, consultants and consultant-client
--     users must not be able to self-enable it;
--   * the control supports: individual Organization; Consultant (firm);
--     individual Consultant Client; selected Consultant Clients; all Consultant
--     Clients under a Consultant;
--   * precedence: most-specific applicable setting wins
--        consultant_client  >  consultant_firm  >  organization  >  default(DENY);
--   * absence of an explicit row means DISABLED (fail closed);
--   * every governance change is auditable (recorded in public.audit_logs by the
--     API, not in a parallel audit system).
--
-- Scope targets are the REAL relationship entities — no duplicate tenancy concept:
--   organization      -> organizations.id
--   consultant_firm   -> consultant_profiles.id  (the firm)
--   consultant_client -> consultant_clients.id   (the firm<->organisation grant)
--
-- SECURITY POSTURE (fail-closed): RLS ENABLED with ZERO policies, and BOTH client
-- roles revoked. Only the service role (the FastAPI backend, which performs the
-- CarbonTally-Admin authorization) can read or write these rows.
--
-- SCOPE DISCIPLINE: additive + idempotent. Creates exactly ONE new table. No
-- existing table, column, policy, grant, function, trigger, storage object or
-- data row is modified. No destructive change.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Preconditions
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.organizations') IS NULL THEN
        RAISE EXCEPTION 'FIN-06 precondition failed: public.organizations is absent';
    END IF;
    IF to_regclass('public.consultant_clients') IS NULL THEN
        RAISE EXCEPTION 'FIN-06 precondition failed: public.consultant_clients is absent';
    END IF;
    IF to_regclass('public.consultant_profiles') IS NULL THEN
        RAISE EXCEPTION 'FIN-06 precondition failed: public.consultant_profiles is absent';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. public.manual_processing_grants (governance control plane)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.manual_processing_grants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type text NOT NULL,
    scope_id uuid NOT NULL,
    enabled boolean NOT NULL,
    reason text,
    set_by uuid NOT NULL,
    set_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    -- Exactly one governance row per scope target (upsert semantics).
    CONSTRAINT manual_processing_grants_scope_key UNIQUE (scope_type, scope_id),
    -- The ratified scope vocabulary: no duplicate tenancy concept is invented.
    CONSTRAINT manual_processing_grants_scope_type_check
        CHECK (scope_type IN ('organization', 'consultant_firm', 'consultant_client'))
);

COMMENT ON TABLE public.manual_processing_grants IS $fin06$
CarbonTally Admin-controlled Manual Processing governance plane (FIN-06).
ABSENCE of a row means DISABLED (fail closed). Precedence, most specific first:
consultant_client > consultant_firm > organization > platform default (DENY).
Only the service role (backend, behind the CarbonTally-Admin authorization) may
read or write this table: RLS is ENABLED with ZERO policies and both client
roles are revoked. Written ONLY by the admin API, always with an audit entry.
$fin06$;

COMMENT ON COLUMN public.manual_processing_grants.scope_type IS
'FIN-06 scope vocabulary: organization | consultant_firm | consultant_client.';
COMMENT ON COLUMN public.manual_processing_grants.scope_id IS
'The REAL relationship id for the scope: organizations.id, consultant_profiles.id (firm) or consultant_clients.id (firm <-> organisation grant).';
COMMENT ON COLUMN public.manual_processing_grants.enabled IS
'Explicit governance value for this exact scope. TRUE permits manual processing for the scope (subject to consultant capability flags); FALSE denies it even if a broader scope would allow it.';
COMMENT ON COLUMN public.manual_processing_grants.set_by IS
'The CarbonTally Admin user id that set the value (server-resolved, never client-supplied).';

-- ---------------------------------------------------------------------------
-- 3. Indexes (scope resolution + expansion)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_manual_processing_grants_scope
    ON public.manual_processing_grants (scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_manual_processing_grants_enabled
    ON public.manual_processing_grants (enabled);

-- ---------------------------------------------------------------------------
-- 4. RLS — fail closed, service-role only
-- ---------------------------------------------------------------------------
ALTER TABLE public.manual_processing_grants ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.manual_processing_grants FROM anon;
REVOKE ALL ON TABLE public.manual_processing_grants FROM authenticated;
-- No policy is created: with RLS enabled and zero policies, every RLS-bound role
-- is denied by construction. The backend uses the service role (BYPASSRLS) and
-- performs the CarbonTally-Admin authorization at the API boundary.

COMMIT;

-- ============================================================================
-- VERIFICATION CHECKLIST (FIN-06)
--   [x] public.manual_processing_grants created (single new table)
--   [x] UNIQUE (scope_type, scope_id)  — one governance row per scope
--   [x] scope_type CHECK — ratified vocabulary only
--   [x] RLS enabled, ZERO policies (client roles fail closed)
--   [x] anon + authenticated revoked; service_role untouched (unchanged)
--   [ ] default posture verified OFF on a fresh apply:
--       SELECT count(*) FROM public.manual_processing_grants WHERE enabled; -- => 0
-- ============================================================================
