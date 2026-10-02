-- ============================================================================
-- CarbonTally — CT-FINAL-03 (residual closure) : `staff_workload` RLS
-- File: 20261029000000_ct_final_03_staff_workload_rls.sql
--
-- AUTHORITY — owner implementation authorisation (2026-10-02, third pass),
-- "FINAL-03 RLS — CLOSE THE SINGLE REMAINING RLS RESIDUAL". The owner chose the
-- security-first objective: CarbonTally should carry no known, unnecessary
-- RLS-disabled table. Package 08 §C listed `staff_workload` among the
-- RLS-disabled tables; package 09 §4.7/§6.0 downgraded it to an owner decision
-- and recorded the remediation option as "RLS + 0 policies (free) + delete the
-- 3 dead column references". The owner has now taken that option.
--
-- WHY A SEPARATE FILE (governance, stated so a verifier can audit the choice):
--   * AGENTS.md §66 requires "every schema change must have a migration"; the
--     repository states no rule permitting an already-created migration to be
--     edited after it has been written. The authorisation therefore defaults to
--     "do not modify the already-created migration — add the change safely
--     according to the repository's migration rules".
--   * The sibling artefact `20261028000000_ct_final_03_rls_security_remediation.sql`
--     is the artefact already accepted for independent verification "in
--     principle". Editing it would change the bytes of an accepted artefact and
--     invalidate that acceptance. It is therefore left byte-for-byte untouched,
--     and this additive file closes the one residual it recorded.
--   * No duplication and no conflict: `staff_workload` is NOT in that file's
--     approved set (41 fail-closed + 2 policy-preserving = 43), that file
--     creates/drops no policy, and this file touches exactly one table and also
--     creates/drops no policy. The two table sets are disjoint (asserted by
--     test).
--
-- OPERATION — RLS ENABLEMENT ONLY (1 table): `ALTER TABLE public.staff_workload
-- ENABLE ROW LEVEL SECURITY` with ZERO policies. With RLS on and no policy,
-- every `anon` / `authenticated` SELECT / INSERT / UPDATE / DELETE is denied,
-- while `service_role` (the FastAPI backend, which holds BYPASSRLS) keeps the
-- access every current reader/writer uses — the same deliberate backend trust
-- model recorded in package 09 (I-3/I-4). No browser path is weakened,
-- preserved or worked around:
--   * the only browser *read* of the table was already deleted as dead code
--     (`admin/src/pages/admin/WorkHub.jsx`; it selected `assigned_reviews`,
--     `in_progress_reviews`, `last_updated` — columns that exist nowhere). That
--     deletion is preserved by this change-set; the read is NOT restored.
--   * the inert realtime subscription registration for the table
--     (`frontend/src/lib/realtime/manager.js:247`, `event: 'UPDATE'`, filtered
--     by `staff_id`) delivers no row to a browser once RLS is on; per the
--     authorisation ("do not weaken or create a policy merely to preserve
--     legacy behaviour") it is left exactly as it is and documented instead.
--
-- NOT IN SCOPE (deliberate, recorded):
--   * no GRANT / REVOKE / ALTER DEFAULT PRIVILEGES, no FORCE ROW LEVEL SECURITY
--     (package 08 D-11 stays deferred — the backend keeps BYPASSRLS), no policy,
--     no function, no trigger, no storage, no schema, no column, no index, no
--     data change. No other table is touched. Class A (`emission_factors`,
--     `business_hours`, `sla_definitions`) is not revisited.
--   * the table is not dropped, renamed, back-filled or re-modelled; the three
--     dead backend column references recorded by package 09 §4.7 stay as they
--     are (they are application code, outside this database change-set, and
--     already fail softly).
--
-- SAFETY (verified, not assumed):
--   * Statements executed: `ALTER TABLE … ENABLE ROW LEVEL SECURITY` only. No
--     INSERT/UPDATE/DELETE/TRUNCATE, no DROP, no GRANT, no data mutation. The
--     file is therefore additive/security-only and reversible in the one
--     dimension it changes (see ROLLBACK below).
--   * Pre-condition guards REFUSE to run when: `staff_workload` is absent (this
--     migration has exactly one target, so absence means "not a CarbonTally
--     database" — unlike the 43-table file it must not silently no-op on a
--     security control; the table is created by
--     `00000000000000_init_schema.sql`), `anon`/`authenticated` hold BYPASSRLS
--     (which would make the enablement theatre), or the table already carries a
--     policy (an unrecognised grant path that must be reviewed before it can be
--     certified fail-closed).
--     NOTE: a database where the table is ALREADY RLS-enabled (the local dev
--     cluster enables RLS on all of its public tables) is accepted — the
--     enablement is then a no-op and the post-conditions still have to hold.
--   * Post-conditions prove: `staff_workload` is RLS-enabled, it carries zero
--     policies, the total policy count in `public` is unchanged (delta = 0),
--     and FORCE ROW LEVEL SECURITY was not set.
--   * Idempotent: re-running is a no-op (`ENABLE ROW LEVEL SECURITY` is
--     idempotent and every guard/post-condition holds on an already-enabled
--     database).
--
-- ORDERING: the filename sorts immediately AFTER
-- `20261028000000_ct_final_03_rls_security_remediation.sql`, which in turn sorts
-- immediately after `20261027000000_ct_backup_02_backup_sets_and_verification.sql`.
-- No historical migration is modified, reordered, replaced or duplicated.
--
-- ROLLBACK (owner-authorised reversal only — NOT to be run as part of a release):
--   Reversal is the exact inverse single-statement form:
--       ALTER TABLE public.staff_workload DISABLE ROW LEVEL SECURITY;
--   A reversal re-opens the exposure closed here (package 09 §4.7 latent
--   exposure), so it requires a new, separately authorised migration and a
--   written risk acceptance. Because this migration changes no policy, no data
--   and no grant, no other revert action exists or is needed.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Single deterministic, auditable block: guards → enablement → post-conditions.
-- ----------------------------------------------------------------------------
DO $ct_final_03_staff_workload$
DECLARE
    -- The single fail-closed target: RLS enabled, ZERO policies.
    fail_closed     text[] := ARRAY['staff_workload'];

    t               text;
    offenders       text[];
    policies_before integer;
    policies_after  integer;
    table_policies  integer;
    enabled_before  boolean;
    enabled_after   boolean;
    forced          boolean;
BEGIN
    -- (0) Internal arithmetic guard: the set definition is part of the audit
    --     record, so a silent edit of it must fail loudly rather than sail on.
    IF coalesce(array_length(fail_closed, 1), 0) <> 1 THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual: target set definition changed (targets=%) — refusing to run',
            coalesce(array_length(fail_closed, 1), 0);
    END IF;

    -- (1) Wrong-target guard: this migration has exactly one target, so its
    --     absence is not "skip and continue" — it means this is not a
    --     CarbonTally database (the table is created by the init schema).
    IF to_regclass('public.staff_workload') IS NULL THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual precondition failed: public.staff_workload is absent — refusing to no-op on a security control (wrong target?)';
    END IF;

    -- (2) Enforcement guard: anon/authenticated must not hold BYPASSRLS, or
    --     enabling RLS would be theatre rather than a control.
    IF EXISTS (
        SELECT 1 FROM pg_roles
         WHERE rolname IN ('anon', 'authenticated') AND rolbypassrls
    ) THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual precondition failed: anon/authenticated hold BYPASSRLS — RLS would not be enforced';
    END IF;

    -- (3) Fail-closed drift guard: a policy on the target is an unrecognised
    --     grant path and must be reviewed (package 09 §6.2) before this
    --     migration is allowed to certify the table fail-closed.
    SELECT array_agg(DISTINCT p.policyname ORDER BY p.policyname) INTO offenders
      FROM pg_policies p
     WHERE p.schemaname = 'public'
       AND p.tablename = ANY(fail_closed);

    IF offenders IS NOT NULL THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual precondition failed: fail-closed table already carries policies (%) — review before enabling RLS', offenders;
    END IF;

    -- (4) Baseline state, and the pre-enablement grant evidence (the exposure
    --     this migration closes). Grant state is reported, not asserted on:
    --     containment could legitimately be held by grants alone.
    SELECT c.relrowsecurity, c.relforcerowsecurity
      INTO enabled_before, forced
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
       AND c.relname = 'staff_workload';

    SELECT count(*) INTO policies_before
      FROM pg_policies WHERE schemaname = 'public';

    SELECT count(*) INTO table_policies
      FROM pg_policies
     WHERE schemaname = 'public' AND tablename = ANY(fail_closed);

    IF to_regrole('authenticated') IS NOT NULL AND to_regrole('anon') IS NOT NULL THEN
        RAISE NOTICE 'CT-FINAL-03 residual: pre-enable grant/RLS state on public.staff_workload — rls_on=%, force_rls=%, policies=%, authenticated SELECT/INSERT/UPDATE/DELETE=%, anon SELECT=%',
            enabled_before, forced, table_policies,
            has_table_privilege('authenticated', 'public.staff_workload', 'SELECT,INSERT,UPDATE,DELETE'),
            has_table_privilege('anon', 'public.staff_workload', 'SELECT');
    END IF;

    -- ------------------------------------------------------------------------
    -- THE ONLY DDL IN THIS MIGRATION: enablement. No policy, no grant, no
    -- FORCE ROW LEVEL SECURITY, no function, no data statement.
    -- ------------------------------------------------------------------------
    FOREACH t IN ARRAY fail_closed LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;

    -- ---------------------------- POST-CONDITIONS ---------------------------
    SELECT c.relrowsecurity, c.relforcerowsecurity
      INTO enabled_after, forced
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
       AND c.relname = 'staff_workload';

    IF enabled_after IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual post-condition failed: public.staff_workload is not RLS-enabled';
    END IF;

    SELECT count(*) INTO table_policies
      FROM pg_policies
     WHERE schemaname = 'public' AND tablename = ANY(fail_closed);

    IF table_policies <> 0 THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual post-condition failed: % policy/policies exist on public.staff_workload — it must be fail-closed with zero policies', table_policies;
    END IF;

    SELECT count(*) INTO policies_after
      FROM pg_policies WHERE schemaname = 'public';

    IF policies_after <> policies_before THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual post-condition failed: policy count changed (% → %) — this migration must create and drop no policy', policies_before, policies_after;
    END IF;

    -- FORCE ROW LEVEL SECURITY is deliberately untouched: `service_role` keeps
    -- BYPASSRLS backend access (package 08 D-11 remains deferred).
    IF forced THEN
        RAISE EXCEPTION 'CT-FINAL-03 residual post-condition failed: FORCE ROW LEVEL SECURITY must remain untouched on public.staff_workload';
    END IF;

    RAISE NOTICE 'CT-FINAL-03 residual: targets=%, rls_enabled_before=%, rls_enabled_after=%, policies_on_target=0, policies_before=%, policies_after=% (delta 0), force_rls=off. RLS enablement only on public.staff_workload: no policy/grant/default-privilege/force/function/trigger/storage/schema/index/data change, no other table touched.',
        array_length(fail_closed, 1), enabled_before, enabled_after,
        policies_before, policies_after;
END
$ct_final_03_staff_workload$;

COMMIT;


