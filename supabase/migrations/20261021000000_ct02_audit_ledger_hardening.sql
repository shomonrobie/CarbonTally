-- ============================================================================
-- CT-IMPLEMENT-02 — canonical audit-ledger hardening (PD-3 / R-6 / R-10.6)
-- File: 20261021000000_ct02_audit_ledger_hardening.sql
--
-- PO DECISIONS IMPLEMENTED (ratified — not reinterpreted here):
--   PD-3  Security and accounting-integrity events MUST fail closed; low-risk
--         observability may log-and-continue.  (The *application* side of that
--         policy lives in backend/domain/audit_policy.py +
--         backend/data/audit.py; this file is the *database* side.)
--   PD-4  The canonical lasting ledger remains public.audit_trail.  No parallel
--         audit architecture is created.
--   R-10.6  audit_trail must be append-only for UPDATE, DELETE **and TRUNCATE**,
--         enforced at the database rather than by application convention; and
--         retained legacy audit surfaces must accept no uncontrolled INSERT and
--         no UPDATE/DELETE at all.
--
-- WHAT WAS WRONG (verified live against the canonical rebuild, not assumed):
--   * `audit_trail` carried the row-level trigger `p7_audit_trail_immutable`
--     (BEFORE UPDATE OR DELETE FOR EACH ROW).  TRUNCATE is a *statement-level*
--     operation, so it never fired the row trigger, while `postgres` and
--     `service_role` held TRUNCATE on the ledger — the append-only guarantee
--     therefore had a hole that no application code could close.
--   * `authenticated` held INSERT/SELECT/UPDATE/DELETE on `audit_trail`.
--     UPDATE/DELETE were inert (the row trigger raised) but the grant itself
--     contradicted the append-only posture.
--   * The retained legacy tables `audit_logs` / `activity_logs` were still
--     fully mutable by `service_role` (UPDATE/DELETE/TRUNCATE), and the only
--     protection was the absence of tenant UPDATE/DELETE policies — which does
--     not bind a BYPASSRLS role.  That is CT-AUDIT-01 finding F-5.
--
-- WHAT THIS MIGRATION DOES (additive + idempotent; modifies no earlier file):
--   1. Extends the append-only guarantee to TRUNCATE for `public.audit_trail`
--      with a statement-level guard trigger that fires for EVERY role.
--   2. Removes the contradictory UPDATE/DELETE/TRUNCATE grants on
--      `audit_trail` from every non-provider role, keeping INSERT/SELECT for
--      the server-side writer (`service_role`/`postgres`).
--   3. Makes `audit_logs` and `activity_logs` genuinely append-only: no UPDATE,
--      no DELETE, no TRUNCATE for any role; no client INSERT
--      (`anon`/`authenticated`/`PUBLIC`); INSERT retained only for the trusted
--      server-side roles (`service_role`, `postgres`) that own the write path.
--   4. Documents each retained legacy surface as historical/deprecated so it
--      cannot be mistaken for the canonical ledger.
--
-- DELIBERATE NON-ACTIONS (recorded so they are not mistaken for oversights):
--   * `document_activity_log` is NOT changed here: the ratified remediation
--     scope for F-5 names `audit_logs`/`activity_logs`, and this migration
--     exists to harden the canonical ledger plus those two surfaces. Its
--     disposition remains an open classification item (report §16) rather than
--     an unapproved change.
--   * No table is dropped and no data is deleted. The canonical retirement of
--     legacy tables is a PO-gated migration-safety decision (AGENTS.md §79).
--
-- ESCAPE HATCH: a future *authorised* retention/purge procedure must set the
-- session GUC `ct.audit_purge_authorised = 'on'` (and still hold the required
-- privilege).  Nothing in the application sets it, so ordinary runtime — the
-- backend's service role included — cannot truncate the ledger.
--
-- VERIFICATION CHECKLIST
--   [ ] function public.ct02_audit_truncate_guard() exists
--   [ ] trigger ct02_audit_trail_no_truncate exists on public.audit_trail
--   [ ] UPDATE/DELETE on public.audit_trail still raise (p7 row trigger intact)
--   [ ] TRUNCATE on public.audit_trail raises (every role)
--   [ ] INSERT/SELECT on public.audit_trail still work for service_role
--   [ ] UPDATE/DELETE/TRUNCATE on audit_logs / activity_logs raise
--   [ ] INSERT on audit_logs / activity_logs still works for service_role
--   [ ] anon/authenticated hold no INSERT on audit_logs / activity_logs
--   [ ] re-running this file is a no-op
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Preconditions — fail closed rather than silently no-op
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.audit_trail') IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 precondition failed: public.audit_trail is absent. '
            'The canonical ledger must exist before it can be hardened.';
    END IF;
    IF to_regclass('public.audit_logs') IS NULL
       OR to_regclass('public.activity_logs') IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 precondition failed: the retained legacy audit '
            'surfaces (audit_logs / activity_logs) are absent. Determine their '
            'actual disposition before applying this migration.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. Statement-level TRUNCATE guards
--    Row-level triggers cannot observe TRUNCATE; this closes that hole.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.ct02_audit_truncate_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- An authorised retention/purge procedure must opt in explicitly, in its
    -- own session, and still hold the privilege. Nothing else may truncate.
    IF coalesce(current_setting('ct.audit_purge_authorised', true), 'off') = 'on' THEN
        RETURN NULL;
    END IF;
    RAISE EXCEPTION
        'append-only ledger (CT-IMPLEMENT-02): TRUNCATE of %.% is not permitted '
        '(set ct.audit_purge_authorised=on only from an authorised purge run)',
        TG_TABLE_SCHEMA, TG_TABLE_NAME
        USING ERRCODE = 'raise_exception';
END;
$$;

COMMENT ON FUNCTION public.ct02_audit_truncate_guard() IS
    'CT-IMPLEMENT-02 (PD-4/R-10.6) — statement-level guard that makes TRUNCATE '
    'of an append-only audit ledger impossible for every role; an authorised '
    'purge run must opt in per session via ct.audit_purge_authorised.';

DROP TRIGGER IF EXISTS ct02_audit_trail_no_truncate ON public.audit_trail;
CREATE TRIGGER ct02_audit_trail_no_truncate
    BEFORE TRUNCATE ON public.audit_trail
    FOR EACH STATEMENT
    EXECUTE FUNCTION public.ct02_audit_truncate_guard();

DROP TRIGGER IF EXISTS ct02_audit_logs_no_truncate ON public.audit_logs;
CREATE TRIGGER ct02_audit_logs_no_truncate
    BEFORE TRUNCATE ON public.audit_logs
    FOR EACH STATEMENT
    EXECUTE FUNCTION public.ct02_audit_truncate_guard();

DROP TRIGGER IF EXISTS ct02_activity_logs_no_truncate ON public.activity_logs;
CREATE TRIGGER ct02_activity_logs_no_truncate
    BEFORE TRUNCATE ON public.activity_logs
    FOR EACH STATEMENT
    EXECUTE FUNCTION public.ct02_audit_truncate_guard();


-- ---------------------------------------------------------------------------
-- 3. Row-level immutability for the retained legacy surfaces
--    (F-5: service_role could previously rewrite or erase them.)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.ct02_append_only_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF coalesce(current_setting('ct.audit_purge_authorised', true), 'off') = 'on' THEN
        RETURN NULL;
    END IF;
    RAISE EXCEPTION
        'append-only table (CT-IMPLEMENT-02): % on %.% is not permitted. '
        'public.audit_trail is the canonical ledger; historical and '
        'access-history records must never be rewritten or erased.',
        TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME
        USING ERRCODE = 'raise_exception';
END;
$$;

COMMENT ON FUNCTION public.ct02_append_only_guard() IS
    'CT-IMPLEMENT-02 (F-5/PD-1) — blocks UPDATE/DELETE for every role '
    '(service_role included) on append-only history tables: the retained legacy '
    'audit surfaces and the report-share access history.';

DROP TRIGGER IF EXISTS ct02_audit_logs_immutable ON public.audit_logs;
CREATE TRIGGER ct02_audit_logs_immutable
    BEFORE UPDATE OR DELETE ON public.audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_append_only_guard();

DROP TRIGGER IF EXISTS ct02_activity_logs_immutable ON public.activity_logs;
CREATE TRIGGER ct02_activity_logs_immutable
    BEFORE UPDATE OR DELETE ON public.activity_logs
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_append_only_guard();



-- ---------------------------------------------------------------------------
-- 4. Privilege tightening
--    Role names are platform-provisioned; each statement is guarded so this
--    file also runs correctly on a target where a role is absent.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    role_name text;
    grantee   text;
    subjects  text[] := ARRAY['PUBLIC', 'anon', 'authenticated', 'service_role'];
    writers   text[] := ARRAY['service_role', 'postgres'];
    clients   text[] := ARRAY['PUBLIC', 'anon', 'authenticated'];
BEGIN
    -- 4a. No role may mutate or truncate an audit surface.
    FOREACH role_name IN ARRAY subjects LOOP
        CONTINUE WHEN role_name <> 'PUBLIC'
                    AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name);
        -- PUBLIC is a privilege keyword, never a quoted identifier.
        grantee := CASE WHEN role_name = 'PUBLIC' THEN 'PUBLIC'
                        ELSE quote_ident(role_name) END;
        EXECUTE format(
            'REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.audit_trail FROM %s',
            grantee);
        EXECUTE format(
            'REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.audit_logs FROM %s',
            grantee);
        EXECUTE format(
            'REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.activity_logs FROM %s',
            grantee);
    END LOOP;

    -- 4b. No uncontrolled client INSERT: the canonical ledger is written
    -- server-side, and the retained legacy surfaces are historical records.
    FOREACH role_name IN ARRAY clients LOOP
        CONTINUE WHEN role_name <> 'PUBLIC'
                    AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name);
        grantee := CASE WHEN role_name = 'PUBLIC' THEN 'PUBLIC'
                        ELSE quote_ident(role_name) END;
        EXECUTE format('REVOKE INSERT ON TABLE public.audit_trail FROM %s', grantee);
        EXECUTE format('REVOKE INSERT ON TABLE public.audit_logs FROM %s', grantee);
        EXECUTE format('REVOKE INSERT ON TABLE public.activity_logs FROM %s', grantee);
    END LOOP;

    -- 4c. Keep the historical writers working. Verified against the live
    -- canonical rebuild: every legacy call site in the backend inserts through
    -- the service-key client, so service_role must retain INSERT.
    FOREACH role_name IN ARRAY writers LOOP
        CONTINUE WHEN NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name);
        EXECUTE format('GRANT SELECT, INSERT ON TABLE public.audit_trail TO %s',
                       quote_ident(role_name));
        EXECUTE format('GRANT SELECT, INSERT ON TABLE public.audit_logs TO %s',
                       quote_ident(role_name));
        EXECUTE format('GRANT SELECT, INSERT ON TABLE public.activity_logs TO %s',
                       quote_ident(role_name));
    END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 5. Formal classification of the retained legacy surfaces
-- ---------------------------------------------------------------------------
COMMENT ON TABLE public.audit_logs IS
    'DEPRECATED / HISTORICAL (CT-IMPLEMENT-02 classification: legacy registered '
    'surface, retained, not canonical). Append-only and immutable since '
    '20261021000000: no UPDATE/DELETE/TRUNCATE for any role and no client '
    'INSERT. public.audit_trail is the canonical audit ledger — do not build '
    'new capability on this table.';

COMMENT ON TABLE public.activity_logs IS
    'DEPRECATED / HISTORICAL (CT-IMPLEMENT-02 classification: legacy registered '
    'surface, retained, not canonical). Append-only and immutable since '
    '20261021000000: no UPDATE/DELETE/TRUNCATE for any role and no client '
    'INSERT. public.audit_trail is the canonical audit ledger — do not build '
    'new capability on this table.';

COMMENT ON TABLE public.audit_trail IS
    'CANONICAL append-only audit ledger (PD-4). Immutable for UPDATE/DELETE '
    '(row trigger p7_audit_trail_immutable) and for TRUNCATE (statement trigger '
    'ct02_audit_trail_no_truncate, CT-IMPLEMENT-02). RLS is enabled with zero '
    'policies (deny-by-default); writes happen through the server-side audit '
    'repository (backend/data/audit.py).';

COMMIT;
