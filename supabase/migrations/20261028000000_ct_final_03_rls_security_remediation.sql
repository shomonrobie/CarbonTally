-- ============================================================================
-- CarbonTally — CT-FINAL-03 : RLS SECURITY REMEDIATION (fail-closed)
-- File: 20261028000000_ct_final_03_rls_security_remediation.sql
--
-- AUTHORITY — owner implementation authorisation (2026-10-02), implementing the
-- bounded conclusion of the two assessment packages and nothing else:
--   * 08-final-03-p2-p5-p6-rls-decision-package-20261002.md
--   * 09-final-03-r1-r2-r3-remediation-decision-20261002.md
--   Objective: RLS according to a security-first / least-privilege /
--   fail-closed model. The old `149 / 149 / 271` baseline is deliberately NOT
--   an objective (package 09 §6.0: that figure is not the measured state).
--
-- OPERATION — RLS ENABLEMENT ONLY (43 tables, two groups):
--
--   GROUP A (41) — FAIL-CLOSED: `ALTER TABLE public.<t> ENABLE ROW LEVEL
--   SECURITY` with ZERO policies. With RLS on and no policy, every
--   `anon` / `authenticated` SELECT/INSERT/UPDATE/DELETE is denied while
--   `service_role` (the FastAPI backend, which holds BYPASSRLS) is unaffected —
--   the deliberate backend trust model recorded in package 09 (I-3/I-4).
--     * critical       : system_settings (R-1), staff_roles (R-2),
--                        password_reset_tokens + beta_access_codes (R-3)
--     * remaining C    : beta_users, email_logs, notifications,
--                        review_audit_trail, waitlist, audit_trail (R-5),
--                        consultant_billing, consultant_tasks, login_history
--     * class D (D-6)  : conversation_activity_log, message_activity_log,
--                        report_comments, report_versions, staff_activity_log,
--                        typing_status, user_activity_log, user_presence,
--                        verification_logs
--     * class B (19)   : enabled under the authorisation §8 "genuinely free"
--                        latitude — each was verified to have zero browser
--                        references of any kind (`from('t')` and realtime
--                        `table: 't'`) in admin/src + frontend/src and no
--                        authenticated write path. See the manifest for the
--                        exact list and rationale.
--
--   GROUP B (2) — ENABLE ONLY, POLICY-PRESERVING: `conversation_participants`
--   (3 existing policies) and `manual_extraction_items` (1 existing policy).
--   No policy is created, dropped, altered, broadened or narrowed: the tables
--   that hold retained customer data (14 manual_extraction_items rows; the
--   conversation membership row) are protected by the product's own isolation
--   intent, which until now was inert because RLS was off (R-4 / I-6).
--
-- NOT IN SCOPE (deliberate, recorded):
--   * class A — `emission_factors` (containment is proven by grants: the
--     `authenticated` role holds no privileges there), `business_hours`,
--     `sla_definitions`. RLS is not added merely to make a count look cleaner.
--   * `staff_workload` — package 09 §6.0 downgraded it to an owner decision and
--     the owner did not authorise it in this change-set. It remains the single
--     recorded residual; its dead browser references were removed app-side.
--   * no GRANT / REVOKE / ALTER DEFAULT PRIVILEGES, no FORCE ROW LEVEL
--     SECURITY (package 08 D-11 stays deferred — the backend keeps BYPASSRLS),
--     no policy, no function, no storage, no schema, no column, no data change.
--
-- SAFETY (verified, not assumed):
--   * Statements executed: `ALTER TABLE … ENABLE ROW LEVEL SECURITY` only.
--     No INSERT/UPDATE/DELETE/TRUNCATE, no DROP, no GRANT, no data mutation.
--     The migration is therefore additive/security-only and reversible in the
--     one dimension it changes (see ROLLBACK below).
--   * Pre-condition guards REFUSE to run when: a fail-closed table already
--     carries a policy (an unrecognised grant path that must be reviewed),
--     the retained-policy family has changed, `anon`/`authenticated` hold
--     BYPASSRLS (which would make the enablement theatre), or the two
--     retained-data tables are absent (wrong target).
--   * Post-conditions prove: every present approved table is RLS-enabled, the
--     total policy count in `public` is unchanged (delta = 0), the retained
--     policy family is byte-for-byte the same set, and no approved table has
--     FORCE ROW LEVEL SECURITY.
--   * Idempotent: re-running is a no-op — `ENABLE ROW LEVEL SECURITY` is
--     idempotent and the guards/post-conditions hold on an already-enabled
--     database (verified on the disposable local environment).
--   * Tables absent in a given environment are skipped with a NOTICE (the
--     established RLS-4B precedent), so a partial clone cannot be broken by the
--     migration; production carries all 43.
--
-- ORDERING: the filename sorts immediately AFTER the current head of the
-- migration chain, `20261027000000_ct_backup_02_backup_sets_and_verification.sql`.
-- No historical migration is modified, reordered or replaced.
--
-- ROLLBACK (owner-authorised reversal only — NOT to be run as part of a release):
--   Reversal is the exact inverse single-statement form for the 43 tables:
--       ALTER TABLE public.<t> DISABLE ROW LEVEL SECURITY;
--   A reversal re-opens every exposure closed here (R-1…R-5), so it requires a
--   new, separately authorised migration and a written risk acceptance. Because
--   this migration changes no policy, no data and no grant, no other revert
--   action exists or is needed.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Single deterministic, auditable block: guards → enablement → post-conditions.
-- ----------------------------------------------------------------------------
DO $ct_final_03$
DECLARE
    -- GROUP A — fail-closed: RLS enabled, ZERO policies for anon/authenticated.
    group_a text[] := ARRAY[
        -- §3 CRITICAL (package 09 §1-§3 / R-1, R-2, R-3)
        'system_settings',
        'staff_roles',
        'password_reset_tokens',
        'beta_access_codes',
        -- §5 remaining production-sensitive Class-C (package 09 §5.3 / R-5)
        'beta_users',
        'email_logs',
        'notifications',
        'review_audit_trail',
        'waitlist',
        'audit_trail',
        'consultant_billing',
        'consultant_tasks',
        'login_history',
        -- §6 Class-D (package 09 §5.4 / D-6 — security-first "enable now")
        'conversation_activity_log',
        'message_activity_log',
        'report_comments',
        'report_versions',
        'staff_activity_log',
        'typing_status',
        'user_activity_log',
        'user_presence',
        'verification_logs',
        -- §8 Class-B (19) — enabled because enablement is genuinely free:
        -- zero browser references of any kind, no authenticated write path,
        -- every writer is the service-role backend or a migration.
        'approval_decisions',
        'approval_requests',
        'dashboard_metrics',
        'notification_delivery',
        'processing_assignments',
        'processing_audit_trail',
        'processing_steps',
        'processing_time_log',
        'qc_checklists',
        'qc_checks',
        'qc_errors',
        'queue_settings',
        'reassignment_history',
        'review_assignment_history',
        'sla_compliance',
        'staff_daily_performance',
        'staff_performance',
        'team_performance',
        'verification_activity_log'
    ];

    -- GROUP B — enable only; the existing policies are kept exactly as they are.
    group_b text[] := ARRAY[
        'conversation_participants',
        'manual_extraction_items'
    ];

    -- The retained policy family RLS enablement activates (never rewritten here).
    retained_policies text[] := ARRAY[
        'conversation_participants_entity_select',
        'conversation_participants_select',
        'conversation_participants_update_own',
        'manual_extraction_items_entity_select'
    ];

    approved        text[];
    t               text;
    absent          text[];
    offenders       text[];
    found           text[];
    expected        text[];
    policies_before integer;
    policies_after  integer;
    enabled_before  integer := 0;
    enabled_after   integer := 0;
    present         integer := 0;
    skipped         integer := 0;
    processed       integer := 0;
BEGIN
    approved := group_a || group_b;

    -- (0) Internal arithmetic guard: the set definition is part of the audit
    --     record, so a silent edit of it must fail loudly rather than sail on.
    IF coalesce(array_length(group_a, 1), 0) <> 41
       OR coalesce(array_length(group_b, 1), 0) <> 2
       OR coalesce(array_length(retained_policies, 1), 0) <> 4 THEN
        RAISE EXCEPTION 'CT-FINAL-03: approved set definition changed (group_a=%, group_b=%, retained=%) — refusing to run',
            coalesce(array_length(group_a, 1), 0),
            coalesce(array_length(group_b, 1), 0),
            coalesce(array_length(retained_policies, 1), 0);
    END IF;

    -- (1) Wrong-target guard: the two tables that hold retained production data
    --     must exist. Their absence means this is not the intended database.
    IF to_regclass('public.conversation_participants') IS NULL
       OR to_regclass('public.manual_extraction_items') IS NULL THEN
        RAISE EXCEPTION 'CT-FINAL-03 precondition failed: conversation_participants / manual_extraction_items must exist (retained-data target check)';
    END IF;

    -- (2) Enforcement guard: anon/authenticated must not hold BYPASSRLS, or
    --     enabling RLS would be theatre rather than a control.
    IF EXISTS (
        SELECT 1 FROM pg_roles
         WHERE rolname IN ('anon', 'authenticated') AND rolbypassrls
    ) THEN
        RAISE EXCEPTION 'CT-FINAL-03 precondition failed: anon/authenticated hold BYPASSRLS — RLS would not be enforced';
    END IF;

    -- (3) Fail-closed drift guard: a policy on a GROUP A table is an
    --     unrecognised grant path and must be reviewed (package 09 §6.2)
    --     before this migration is allowed to certify the table fail-closed.
    SELECT array_agg(DISTINCT p.tablename ORDER BY p.tablename) INTO offenders
      FROM pg_policies p
     WHERE p.schemaname = 'public'
       AND p.tablename = ANY(group_a);

    IF offenders IS NOT NULL THEN
        RAISE EXCEPTION 'CT-FINAL-03 precondition failed: fail-closed table(s) already carry policies (%) — review before enabling RLS', offenders;
    END IF;

    -- (4) Retained-policy guard: GROUP B must carry exactly the known policy
    --     family. Anything else means the retained-data semantics changed and
    --     this migration must not silently bless the new state.
    SELECT array_agg(DISTINCT p.policyname ORDER BY p.policyname) INTO found
      FROM pg_policies p
     WHERE p.schemaname = 'public'
       AND p.tablename = ANY(group_b);

    SELECT array_agg(x ORDER BY x) INTO expected FROM unnest(retained_policies) AS x;

    IF found IS DISTINCT FROM expected THEN
        RAISE EXCEPTION 'CT-FINAL-03 precondition failed: retained policy family changed (found %, expected %) — refusing to touch it', found, expected;
    END IF;

    -- (5) Absence report: tables a given environment does not have are skipped
    --     (RLS-4B precedent) so a partial clone cannot be broken by this file.
    SELECT array_agg(x ORDER BY x) INTO absent
      FROM unnest(approved) AS x
     WHERE to_regclass('public.' || x) IS NULL;

    IF absent IS NOT NULL THEN
        skipped := array_length(absent, 1);
        RAISE NOTICE 'CT-FINAL-03: % approved table(s) absent here — skipped, no DDL performed: %', skipped, absent;
    END IF;

    -- Baseline counts (audit evidence for the NOTICE below).
    SELECT count(*) INTO policies_before
      FROM pg_policies WHERE schemaname = 'public';

    SELECT count(*) INTO enabled_before
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
       AND c.relname = ANY(approved) AND c.relrowsecurity;

    -- ------------------------------------------------------------------------
    -- THE ONLY DDL IN THIS MIGRATION: enablement. No policy, no grant, no
    -- FORCE ROW LEVEL SECURITY, no function, no data statement.
    -- ------------------------------------------------------------------------
    FOREACH t IN ARRAY approved LOOP
        IF to_regclass('public.' || t) IS NULL THEN
            CONTINUE;
        END IF;

        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        processed := processed + 1;
    END LOOP;

    -- ---------------------------- POST-CONDITIONS ---------------------------
    SELECT count(*) INTO present
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
       AND c.relname = ANY(approved);

    SELECT count(*) INTO enabled_after
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
       AND c.relname = ANY(approved) AND c.relrowsecurity;

    IF enabled_after <> present THEN
        RAISE EXCEPTION 'CT-FINAL-03 post-condition failed: % of % present approved tables are RLS-enabled', enabled_after, present;
    END IF;

    SELECT count(*) INTO policies_after
      FROM pg_policies WHERE schemaname = 'public';

    IF policies_after <> policies_before THEN
        RAISE EXCEPTION 'CT-FINAL-03 post-condition failed: policy count changed (% → %) — this migration must create and drop no policy', policies_before, policies_after;
    END IF;

    SELECT array_agg(DISTINCT p.policyname ORDER BY p.policyname) INTO found
      FROM pg_policies p
     WHERE p.schemaname = 'public'
       AND p.tablename = ANY(group_b);

    IF found IS DISTINCT FROM expected THEN
        RAISE EXCEPTION 'CT-FINAL-03 post-condition failed: retained policy family changed (found %, expected %)', found, expected;
    END IF;

    -- FORCE ROW LEVEL SECURITY is deliberately untouched: `service_role` keeps
    -- BYPASSRLS backend access (package 08 D-11 remains deferred).
    IF EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
           AND c.relname = ANY(approved) AND c.relforcerowsecurity
    ) THEN
        RAISE EXCEPTION 'CT-FINAL-03 post-condition failed: FORCE ROW LEVEL SECURITY must remain untouched on every approved table';
    END IF;

    RAISE NOTICE 'CT-FINAL-03: approved=%, present=%, absent_skipped=%, enabled_before=%, enabled_after=%, statements_run=%, policies_before=%, policies_after=% (delta 0), fail-closed tables=% (0 policies), retained-policy tables=% carrying % policies. RLS enablement only: no policy/grant/default-privilege/force/function/storage/schema/data change.',
        array_length(approved, 1), present, skipped, enabled_before, enabled_after,
        processed, policies_before, policies_after,
        array_length(group_a, 1), array_length(group_b, 1),
        array_length(retained_policies, 1);
END
$ct_final_03$;

COMMIT;

