-- P6-2F E2E environment ONLY — restore the `authenticated` table privileges that
-- this stack's own schema already assumes.
--
-- WHY THIS EXISTS
--   PostgREST requests from a signed-in user run as role `authenticated`. In the
--   isolated E2E stack, 100+ public tables (e.g. `organizations`,
--   `organization_members`, `notifications`, `users`) carry RLS policies whose
--   role is `authenticated` (e.g. `organizations_org_select`) but hold only the
--   PUBLIC-ish leftovers `REFERENCES, TRIGGER, TRUNCATE`. PostgreSQL therefore
--   answers `42501 permission denied` BEFORE any RLS policy is evaluated, so the
--   RLS boundary could not be tested at all.
--
-- WHAT IT DOES
--   Grants `authenticated` exactly the DML privileges implied by that table's
--   OWN RLS policies (`SELECT` / `INSERT` / `UPDATE` / `DELETE`), derived from
--   `pg_policies` at run time — not a blanket `GRANT ALL`. RLS still decides
--   every row, so this does not widen access; it only lets the existing policy
--   run. `anon` is deliberately NOT touched (stricter than Supabase's default
--   baseline, keeping the unauthenticated boundary unambiguous).
--
--   EXECUTE on public functions is included because the repo's own convention
--   grants it to `authenticated` (see the anonymise_user migration), and row
--   policies may call helper functions.
--
-- SAFETY
--   * E2E only; run against port 55326. Never against demo/investor.
--   * No RLS policy is created, altered, dropped or disabled here.
--   * No schema, migration or application change.
--   * Idempotent: re-running is a no-op.

GRANT USAGE ON SCHEMA public TO authenticated;

DO $$
DECLARE
    r     record;
    privs text;
BEGIN
    FOR r IN
        SELECT tablename,
               bool_or(cmd IN ('SELECT', 'ALL')) AS sel,
               bool_or(cmd IN ('INSERT', 'ALL')) AS ins,
               bool_or(cmd IN ('UPDATE', 'ALL')) AS upd,
               bool_or(cmd IN ('DELETE', 'ALL')) AS del
          FROM pg_policies
         WHERE schemaname = 'public'
           AND 'authenticated' = ANY (roles)
         GROUP BY tablename
    LOOP
        privs := concat_ws(', ',
            CASE WHEN r.sel THEN 'SELECT' END,
            CASE WHEN r.ins THEN 'INSERT' END,
            CASE WHEN r.upd THEN 'UPDATE' END,
            CASE WHEN r.del THEN 'DELETE' END);
        IF privs IS NOT NULL AND privs <> '' THEN
            EXECUTE format('GRANT %s ON TABLE public.%I TO authenticated', privs, r.tablename);
        END IF;
    END LOOP;
END $$;

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
