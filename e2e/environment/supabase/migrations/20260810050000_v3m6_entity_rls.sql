-- ============================================================================
-- CarbonTally V3 — Implementation Phase 2, Migration V3M-6
-- File: 20260810050000_v3m6_entity_rls.sql
--
-- Implements the approved Processing Entity-scoped RLS storey (migration plan
-- §16 step 2: "RLS is_entity_member() helper + entity policies (deny-by-default;
-- additive)"). Entity-level RLS is per DECIDED ADR-V3-001 ("RLS: NEW — entity-
-- scoped policies (deny-by-default + is_entity_member()) per ADR-V3-010
-- pattern") and the Architecture Specification §9.1 (Entity isolation —
-- deny-by-default + member-of-entity policies, now that ADR-V3-001 has resolved
-- the entity model via V3M-1/V3M-2).
--
-- Scope (strictly the entity-scoped RLS storey):
--   * is_entity_member(p_entity)  (NEW RLS helper — SECURITY DEFINER)
--   * entity-scoped SELECT policies (deny-by-default + member-of-entity) on:
--       processing_entities   (entity staff see their own entity)
--       staff_profiles        (entity staff see their entity's staff roster)
--       manual_review_queue   (entity staff see work items allocated to their entity)
--       upload_batches        (entity staff see batches allocated to their entity)
--       issues                (entity staff see entity-scoped issues for their entity)
--
-- Four access axes, each with a distinct non-overlapping RLS surface
-- (spec §8.1; register ADR-V3-010):
--   * Customer / Organization   → is_org_member()        (existing, untouched)
--   * Consultant                → is_org_consultant()    (existing, untouched)
--   * Processing Entity staff   → is_entity_member()     (NEW — this migration)
--   * CarbonTally internal staff → entity_id IS NULL + service-role/application
--                                  path (existing, untouched; RC2 §8 deny-by-default
--                                  on staff tables preserved)
--
-- NOT in scope (deferred / conditional — do NOT guess):
--   * Entity-scoped INSERT/UPDATE/DELETE on work surfaces — entity write flows
--     (claim/complete work items, create/assign/resolve issues) are gated on the
--     Work Item model (ADR-V3-003) and the Issue service (ADR-V3-009 backend) —
--     both PROVISIONALLY DECIDED / implementation pending. Entity visibility is
--     SELECT-only here; writes remain service-role/application as today.
--   * V3M-4 provider widening — DECIDED but CONDITIONAL on a scoped provider
--     import (H3 / ADR-V3-015); no provider import is currently scoped; and the
--     task forbids modifying emission_factors. NOT created.
--   * SLA/auto-assignment/audit extensions — ADR-V3-006/007/013 are
--     PROVISIONALLY DECIDED with DB impact "none" (reuse existing structures).
--   * Queue retirement — ADR-V3-016 DEFERRED.
--   * Hardening of legacy permissive queue policies — ADR-V3-010 INVESTIGATE
--     items (legacy permissive policies; consultant membership) remain open;
--     no legacy policy is touched here.
--
-- Conventions (RC2 helper + M8/V3M storey conventions):
--   * Helper is SECURITY DEFINER with SET search_path pinned (RC2 004), STABLE.
--   * REVOKE ALL FROM PUBLIC + GRANT EXECUTE TO authenticated, service_role
--     (RC1 004 helper lockdown).
--   * Policies use DROP POLICY IF EXISTS + CREATE POLICY (idempotent; M8).
--   * No factor data is touched (emission_factors / customer_factors untouched).
-- Idempotent: re-running this file is a no-op.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. is_entity_member() RLS helper
--    Entity staff membership: authenticated user is an ACTIVE staff member
--    belonging to an ACTIVE Processing Entity (staff_profiles.entity_id =
--    processing_entities.id; ADR-V3-001 Q5 convention).
--    Lifecycle gate: only status = 'active' grants access ("entity user access
--    respects entity lifecycle" — register ADR-V3-001 §7.1 clarifications).
--    'remediation'/'suspended'/'terminated' deny by default; the exact
--    lifecycle→access mapping beyond 'active' is deferred to V3 design (Q6).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.is_entity_member(p_entity uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM public.staff_profiles sp
          JOIN public.processing_entities pe ON pe.id = sp.entity_id
         WHERE sp.entity_id = p_entity
           AND sp.user_id = auth.uid()
           AND coalesce(sp.is_active, true) = true
           AND pe.status = 'active'
    );
$$;

-- Lock the helper down (RC1 004 convention): only authenticated (policy
-- evaluation) and service_role (CarbonTally-internal backend) may execute it.
REVOKE ALL ON FUNCTION public.is_entity_member(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_entity_member(uuid) TO authenticated, service_role;

-- ============================================================================

-- ---------------------------------------------------------------------------
-- 2. Entity-scoped SELECT policies (deny-by-default + member-of-entity)
--    All policies are ADDITIVE: no existing policy is dropped or altered.
-- ---------------------------------------------------------------------------

-- 2.1 processing_entities — entity staff may read their own entity row.
--     No INSERT/UPDATE/DELETE: entity lifecycle/administration is CarbonTally-
--     internal (entities cannot self-activate; register ADR-V3-001 §7.1).
DROP POLICY IF EXISTS processing_entities_entity_select ON public.processing_entities;
CREATE POLICY processing_entities_entity_select ON public.processing_entities
    FOR SELECT TO authenticated
    USING (public.is_entity_member(id));

-- 2.2 staff_profiles — entity staff may read staff rows belonging to their
--     entity (roster). Their own row is covered (their row carries their
--     entity_id). CarbonTally-internal staff rows (entity_id IS NULL) stay
--     deny-by-default for authenticated (RC2 §8 convention preserved).
DROP POLICY IF EXISTS staff_profiles_entity_select ON public.staff_profiles;
CREATE POLICY staff_profiles_entity_select ON public.staff_profiles
    FOR SELECT TO authenticated
    USING (
        entity_id IS NOT NULL
        AND public.is_entity_member(entity_id)
    );

-- 2.3 manual_review_queue — entity staff may read Work Items allocated to
--     their entity (entity_id IS NOT NULL; V3M-2 surface). Customer-org items
--     (entity_id IS NULL) remain org-scoped (existing *_tenant_* policies).
--     SELECT only: claiming/completing is the Work Item write flow
--     (ADR-V3-003 — PROVISIONALLY DECIDED); writes stay service-role today.
DROP POLICY IF EXISTS manual_review_queue_entity_select ON public.manual_review_queue;
CREATE POLICY manual_review_queue_entity_select ON public.manual_review_queue
    FOR SELECT TO authenticated
    USING (
        entity_id IS NOT NULL
        AND public.is_entity_member(entity_id)
    );

-- 2.4 upload_batches — entity staff may read batches allocated to their entity.
DROP POLICY IF EXISTS upload_batches_entity_select ON public.upload_batches;
CREATE POLICY upload_batches_entity_select ON public.upload_batches
    FOR SELECT TO authenticated
    USING (
        entity_id IS NOT NULL
        AND public.is_entity_member(entity_id)
    );

-- 2.5 issues — entity staff may read entity-scoped issues for their entity
--     (spec §14.4: entity issue surfaces are entity-scoped, internal — never
--     customer-visible). Complements the V3M-5 org storey, which keeps
--     entity_id IS NULL for customer-facing rows; the two storeys are
--     non-overlapping. SELECT only: issue create/assign/resolve is the Issue
--     service (ADR-V3-009 backend — implementation pending).
DROP POLICY IF EXISTS issues_entity_select ON public.issues;
CREATE POLICY issues_entity_select ON public.issues
    FOR SELECT TO authenticated
    USING (
        entity_id IS NOT NULL
        AND public.is_entity_member(entity_id)
    );

-- ============================================================================
-- VERIFICATION CHECKLIST (V3M-6)
--   [ ] is_entity_member(uuid) exists (STABLE, SECURITY DEFINER, search_path pinned)
--   [ ] PUBLIC revoked on is_entity_member; EXECUTE granted to authenticated + service_role
--   [ ] processing_entities_entity_select present (FOR SELECT TO authenticated,
--       USING is_entity_member(id))
--   [ ] staff_profiles_entity_select present (entity_id IS NOT NULL + is_entity_member)
--   [ ] manual_review_queue_entity_select present (entity_id IS NOT NULL + is_entity_member)
--   [ ] upload_batches_entity_select present (entity_id IS NOT NULL + is_entity_member)
--   [ ] issues_entity_select present (entity_id IS NOT NULL + is_entity_member)
--   [ ] NO entity INSERT/UPDATE/DELETE policies created (writes stay service-role)
--   [ ] NO legacy permissive policies touched (ADR-V3-010 INVESTIGATE items intact)
--   [ ] Customer/consultant isolation untouched (is_org_member / is_org_consultant
--       policies unchanged); org storey on issues (entity_id IS NULL) intact
--   [ ] CarbonTally-internal staff tables keep RC2 §8 deny-by-default
--   [ ] Factor baseline untouched (DEFRA 7,029 · SEAI 20 · TOTAL 7,049)
--   [ ] Re-running this file is a no-op
-- ============================================================================

