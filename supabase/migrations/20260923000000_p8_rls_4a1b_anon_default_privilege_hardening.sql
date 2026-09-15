-- ============================================================================
-- CarbonTally Phase 8 — Separate Workstream RLS — RLS-4A-1 durability (F-4A2-2)
-- File: 20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql
--
-- PO DECISION (2026-09-14) APPROVED — Option A of finding F-4A2-2:
--   "Option A approved. Proceed with the bounded anonymous-role
--    default-privilege hardening and independent verification.
--    Do not expand the RLS scope."
--
-- THE GAP THIS CLOSES (measured, not assumed):
--   RLS-4A-1 revoked `anon` table privileges **table by table**. The `public`
--   default ACL registered by role `postgres` still granted `Dxtm`
--   (TRUNCATE, REFERENCES, TRIGGER, MAINTAIN) to `anon` on every **future**
--   table, so RLS-4A-1's containment would have silently regressed on the next
--   `CREATE TABLE`. RLS-4A-2 removed the identical `authenticated` default
--   entry; this file removes the `anon` one.
--
-- SCOPE — DELIBERATELY MINIMAL (one statement, REVOKE only):
--   * ONLY the `public`-schema TABLE default ACL for role `anon`, owned by
--     role `postgres` (the role that creates CarbonTally objects).
--   * NO table-level change: the only existing table where `anon` still holds
--     non-DML privileges is `emission_factors`, which is the **unratified
--     product decision D-4** and is therefore left exactly as found.
--   * NO change to sequences (`anon=w` on sequence defaults is a different
--     object type and is NOT part of the approved Option A wording — recorded
--     as a residual observation instead).
--   * NO change to the `storage` schema (Supabase-managed, out of scope).
--   * NO change to any RLS flag, policy, column, constraint, index or data.
--   * `service_role` default privileges are untouched (backend role).
--
-- RESULTING POSTURE: future `public` tables created by `postgres` receive no
--   `anon` privileges from defaults; `anon` keeps exactly the access it has
--   today (the deliberate read on `emission_factors`).
--
-- ENVIRONMENT: QA / non-production only (`carbontally_qa_phase8`). Production
--   is PROHIBITED (G0-D open) and is not touched.
--
-- IDEMPOTENT: re-running is a no-op (the entry is already absent).
-- ============================================================================

BEGIN;

DO $$
DECLARE
    before_acl text;
    after_acl  text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        RAISE EXCEPTION 'RLS-4A-1 durability precondition failed: role anon is absent';
    END IF;

    SELECT cast(defaclacl as text) INTO before_acl
    FROM pg_default_acl a
    JOIN pg_roles r ON r.oid = a.defaclrole
    JOIN pg_namespace n ON n.oid = a.defaclnamespace
    WHERE r.rolname = 'postgres' AND n.nspname = 'public'
      AND a.defaclobjtype = 'r';

    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
        REVOKE TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON TABLES FROM anon;

    SELECT cast(defaclacl as text) INTO after_acl
    FROM pg_default_acl a
    JOIN pg_roles r ON r.oid = a.defaclrole
    JOIN pg_namespace n ON n.oid = a.defaclnamespace
    WHERE r.rolname = 'postgres' AND n.nspname = 'public'
      AND a.defaclobjtype = 'r';

    RAISE NOTICE 'RLS-4A-1 durability: public TABLE default ACL for anon changed % -> %',
        before_acl, after_acl;
END $$;

COMMIT;
