-- ============================================================================
-- CarbonTally — MANUAL PROCESSING ROUTING (processor configuration)
-- File: 20261030000000_manual_processing_routing.sql
--
-- PO DECISION (ratified business rule):
--   Manual Processing is a SUBSCRIPTION-PLAN capability, and the routing
--   destination is an explicitly configured Processing Entity.
--
-- This migration adds the ONE persistent configuration this workflow was
-- missing (the forensic audit established there was NO organisation -> PE
-- persistence anywhere: `organizations` has no entity column, and no
-- `organization_processing_entity`-style table existed):
--
--   public.manual_processing_processors
--       scope_type | scope_id -> processing_entity_id (active/inactive)
--
-- It REUSES the ratified FIN-06 scope vocabulary and the REAL relationship ids
-- (`organization` -> organizations.id, `consultant_firm` -> consultant_profiles.id,
-- `consultant_client` -> consultant_clients.id) and the REAL PE model
-- (public.processing_entities). NO second PE model and NO second scope taxonomy
-- are introduced.
--
-- What this migration deliberately does NOT create:
--   * no subscription/entitlement table (the existing D37 commercial model is
--     authoritative and is read server-side, never duplicated);
--   * no second assignment table (the canonical D38 `work_item_assignments`
--     ledger is the only work-item assignment record);
--   * no round-robin / fallback-PE / workload table — routing uses ONE explicit
--     processor per scope (routing precedence = the FIN-06 most-specific-wins
--     precedence, implemented in `domain/manual_processing.py`).
--
-- SECURITY POSTURE (identical to FIN-06): RLS ENABLED with ZERO policies, and
-- both client roles revoked. Only the service role (the FastAPI backend, which
-- performs the CarbonTally-Admin authorization at the API boundary) can read or
-- write these rows. Entitlement + authorization are enforced server-side.
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
    IF to_regclass('public.processing_entities') IS NULL THEN
        RAISE EXCEPTION 'manual-processing-routing precondition failed: public.processing_entities is absent';
    END IF;
    IF to_regclass('public.organizations') IS NULL THEN
        RAISE EXCEPTION 'manual-processing-routing precondition failed: public.organizations is absent';
    END IF;
    IF to_regclass('public.manual_processing_grants') IS NULL THEN
        RAISE EXCEPTION 'manual-processing-routing precondition failed: public.manual_processing_grants is absent (FIN-06 must be applied first)';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. public.manual_processing_processors (routing destination control plane)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.manual_processing_processors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type text NOT NULL,
    scope_id uuid NOT NULL,
    -- The REAL Processing Entity (existing PE model; never hard-deleted, so a
    -- configured destination can never silently vanish).
    processing_entity_id uuid NOT NULL
        REFERENCES public.processing_entities (id) ON DELETE RESTRICT,
    active boolean NOT NULL DEFAULT TRUE,
    reason text,
    set_by uuid NOT NULL,
    set_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    -- Exactly one configured processor per scope (upsert semantics).
    CONSTRAINT manual_processing_processors_scope_key UNIQUE (scope_type, scope_id),
    -- The ratified FIN-06 scope vocabulary: no duplicate tenancy concept.
    CONSTRAINT manual_processing_processors_scope_type_check
        CHECK (scope_type IN ('organization', 'consultant_firm', 'consultant_client'))
);

COMMENT ON TABLE public.manual_processing_processors IS $mpr$
CarbonTally Admin-controlled Manual Processing processor configuration.
The configured Processing Entity that automatic-processing failures are routed
to for a scope. ABSENCE of a row for the applicable scope means NO destination
configured: routing is denied with an explicit configuration state (no arbitrary
or random PE is ever selected). Precedence (same as FIN-06 governance, most
specific first): consultant_client > consultant_firm > organization. Only the
service role (backend, behind the CarbonTally-Admin authorization) may read or
write this table: RLS is ENABLED with ZERO policies and both client roles are
revoked. Written ONLY by the admin API, always with an audit entry.
$mpr$;

COMMENT ON COLUMN public.manual_processing_processors.scope_type IS
'FIN-06 scope vocabulary: organization | consultant_firm | consultant_client.';
COMMENT ON COLUMN public.manual_processing_processors.scope_id IS
'The REAL relationship id for the scope: organizations.id, consultant_profiles.id (firm) or consultant_clients.id (firm <-> organisation grant).';
COMMENT ON COLUMN public.manual_processing_processors.processing_entity_id IS
'The configured destination Processing Entity (public.processing_entities.id) for Manual Processing work in this scope.';
COMMENT ON COLUMN public.manual_processing_processors.active IS
'FALSE disables routing for this scope without deleting the configuration history.';
COMMENT ON COLUMN public.manual_processing_processors.set_by IS
'The CarbonTally Admin user id that set the value (server-resolved, never client-supplied).';

-- ---------------------------------------------------------------------------
-- 3. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_manual_processing_processors_scope
    ON public.manual_processing_processors (scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_manual_processing_processors_entity
    ON public.manual_processing_processors (processing_entity_id);

-- ---------------------------------------------------------------------------
-- 4. RLS — fail closed, service-role only (identical to FIN-06 governance)
-- ---------------------------------------------------------------------------
ALTER TABLE public.manual_processing_processors ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.manual_processing_processors FROM anon;
REVOKE ALL ON TABLE public.manual_processing_processors FROM authenticated;
-- Explicit service-role privilege (house convention for service-only tables):
GRANT ALL ON TABLE public.manual_processing_processors TO service_role;
-- No policy is created: with RLS enabled and zero policies, every RLS-bound role
-- is denied by construction. The backend uses the service role (BYPASSRLS) and
-- performs the CarbonTally-Admin authorization at the API boundary.

COMMIT;

-- ============================================================================
-- ROLLBACK (reversible; run manually only)
-- ----------------------------------------------------------------------------
--   BEGIN;
--   DROP TABLE IF EXISTS public.manual_processing_processors;
--   COMMIT;
-- (Dropping the table removes only this routing configuration. No other table,
--  column, policy, grant or data row is affected: the FIN-06 governance table,
--  the D38 assignment ledger and the processing_entities rows are untouched.)
-- ============================================================================
-- VERIFICATION CHECKLIST
--   [x] public.manual_processing_processors created (single new table)
--   [x] UNIQUE (scope_type, scope_id)  — one processor per scope
--   [x] scope_type CHECK — ratified FIN-06 vocabulary only
--   [x] processing_entity_id FK -> public.processing_entities (ON DELETE RESTRICT)
--   [x] RLS enabled, ZERO policies (client roles fail closed)
--   [x] anon + authenticated revoked; service_role granted; no client write path
--   [x] idempotent (CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS)
--   [ ] default posture on a fresh apply:
--       SELECT count(*) FROM public.manual_processing_processors; -- => 0
-- ============================================================================
