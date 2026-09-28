-- ============================================================================
-- D32 operator step — provider-context storage provisioning (CT-SCHEMA-02)
-- ----------------------------------------------------------------------------
-- WHAT THIS IS: the ONE operational statement that cannot be a CarbonTally
-- migration, because it needs provider privilege on a provider-owned table.
-- ``storage.objects`` is owned by Supabase's provider-managed role
-- (``supabase_storage_admin``); ``CREATE POLICY`` / ``DROP POLICY`` require
-- ownership, and CarbonTally's migration role must NOT be granted it
-- (PO decision — Route C, no privilege escalation). Supabase's supported
-- mechanism for those four policies is therefore the provider-privileged
-- context: the dashboard storage-policy editor, or this equivalent SQL.
--
-- WHERE IT RUNS IN THE CHAIN (dependency order — see
-- ``canonical_schema_rebuild.sh``):
--
--   LAYER 1  platform        : Supabase Postgres image + Storage service
--                              (storage.buckets / storage.objects / storage.foldername)
--   LAYER 2  migrations 1-26 : create public.organization_members and the rest of
--                              the application schema the predicates reference
--   THIS STEP                : private ``documents`` bucket + the four approved
--                              provider-context policies
--   LAYER 2  migrations 27-89: migration 27 then validates what this step created
--
-- This step CANNOT precede migration 1: the approved predicates reference
-- ``public.organization_members``, which migration 1 creates, so they cannot even
-- be parsed before it exists. It MUST precede migration 27, which validates them.
--
-- SINGLE SOURCE OF TRUTH: the four approved policy definitions live in the header
-- of ``supabase/migrations/20260823000000_d32_private_documents_storage.sql``.
-- ``backend/tests/unit/data/test_canonical_schema_rebuild_harness.py`` asserts that
-- the predicate below still matches that header verbatim.
--
-- SAFETY PROPERTIES (all asserted in this file):
--   * idempotent  — repeated runs leave exactly four policies and one private
--                   bucket; no duplicates, no drift, no privilege broadening;
--   * fail-closed — absent platform layer, absent ``organization_members``,
--                   unexpected policy count, or any ``anon``/``public`` grant on
--                   ``storage.objects`` aborts the whole transaction;
--   * no broad GRANTs, no ``anon``/``public`` policy, no RLS weakening — this file
--     issues no privilege statement at all and only ever names the four approved
--     policies.
--
-- APPLY AS THE PROVIDER ADMIN ROLE (disposable/local: ``supabase_admin``):
--   psql -X -q -v ON_ERROR_STOP=1 -U supabase_admin -d <db> -f d32_storage_operator.sql
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Platform / ordering preconditions
-- ---------------------------------------------------------------------------
DO $d32_op_pre$
BEGIN
    IF to_regclass('storage.buckets') IS NULL OR to_regclass('storage.objects') IS NULL THEN
        RAISE EXCEPTION
            'D32 operator precondition failed: the Supabase storage layer is not provisioned (storage.buckets / storage.objects absent). Provision the platform Storage service first — do not fabricate platform tables.';
    END IF;
    IF to_regclass('public.organization_members') IS NULL THEN
        RAISE EXCEPTION
            'D32 operator precondition failed: public.organization_members is absent. The D32 operator step runs AFTER the migrations that define it (migrations 1-26) and BEFORE migration 27.';
    END IF;
END
$d32_op_pre$;

-- ---------------------------------------------------------------------------
-- 2. Private ``documents`` bucket (idempotent; convergence, not duplication)
-- ---------------------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public)
SELECT 'documents', 'documents', FALSE
 WHERE NOT EXISTS (SELECT 1 FROM storage.buckets WHERE name = 'documents');

UPDATE storage.buckets SET public = FALSE WHERE name = 'documents';

DO $d32_op_bucket$
DECLARE
    is_public boolean;
BEGIN
    SELECT public INTO is_public FROM storage.buckets WHERE name = 'documents';
    IF is_public IS NULL THEN
        RAISE EXCEPTION
            'D32 operator failed: the private documents bucket could not be created.';
    END IF;
    IF is_public THEN
        RAISE EXCEPTION
            'D32 operator failed: the documents bucket is public; customer documents must never be served through public URLs.';
    END IF;
END
$d32_op_bucket$;

-- ---------------------------------------------------------------------------
-- 3. The four approved provider-context policies (idempotent convergence)
--    Verbatim predicate: bucket scope + uploads/<org_id>/ path layout +
--    authenticated membership of the owning organisation.
-- ---------------------------------------------------------------------------
DO $d32_op_policies$
DECLARE
    approved constant text[] := ARRAY[
        'd32_documents_select_org_member|SELECT',
        'd32_documents_insert_org_member|INSERT',
        'd32_documents_update_org_member|UPDATE',
        'd32_documents_delete_org_member|DELETE'
    ];
    approved_predicate constant text :=
        'bucket_id = ''documents'' '
        || 'AND (storage.foldername(name))[1] = ''uploads'' '
        || 'AND (storage.foldername(name))[2]::uuid IN ('
        || 'SELECT organization_id FROM public.organization_members '
        || 'WHERE user_id = auth.uid() AND is_active = TRUE)';
    entry text;
    policy_name text;
    policy_cmd text;
    statement text;
BEGIN
    FOREACH entry IN ARRAY approved LOOP
        policy_name := split_part(entry, '|', 1);
        policy_cmd := split_part(entry, '|', 2);

        -- convergence: drop then recreate ONLY this approved policy name
        EXECUTE format('DROP POLICY IF EXISTS %I ON storage.objects', policy_name);

        IF policy_cmd = 'INSERT' THEN
            statement := format(
                'CREATE POLICY %I ON storage.objects FOR INSERT TO authenticated '
                'WITH CHECK (%s)', policy_name, approved_predicate);
        ELSE
            statement := format(
                'CREATE POLICY %I ON storage.objects FOR %s TO authenticated '
                'USING (%s)', policy_name, policy_cmd, approved_predicate);
        END IF;
        EXECUTE statement;
    END LOOP;
END
$d32_op_policies$;

-- ---------------------------------------------------------------------------
-- 4. Verification — exactly four approved D32 policies, nothing broadened.
--    (Predicate identity/semantics are validated structurally by migration 27
--    and proven behaviourally by verify_d32_policy_semantics.sql.)
-- ---------------------------------------------------------------------------
DO $d32_op_verify$
DECLARE
    approved constant text[] := ARRAY[
        'd32_documents_select_org_member|SELECT',
        'd32_documents_insert_org_member|INSERT',
        'd32_documents_update_org_member|UPDATE',
        'd32_documents_delete_org_member|DELETE'
    ];
    d32_policies int;
    entry text;
    found_cmd text;
    found_roles text[];
    broadened int;
BEGIN
    SELECT count(*) INTO d32_policies
      FROM pg_policies
     WHERE schemaname = 'storage' AND tablename = 'objects'
       AND policyname LIKE 'd32\_documents\_%';

    IF d32_policies <> 4 THEN
        RAISE EXCEPTION
            'D32 operator verification failed: expected exactly 4 approved d32_documents_* policies on storage.objects, found %.',
            d32_policies;
    END IF;

    FOREACH entry IN ARRAY approved LOOP
        SELECT p.cmd, p.roles::text[] INTO found_cmd, found_roles
          FROM pg_policies p
         WHERE p.schemaname = 'storage' AND p.tablename = 'objects'
           AND p.policyname = split_part(entry, '|', 1);

        IF found_cmd IS NULL THEN
            RAISE EXCEPTION
                'D32 operator verification failed: policy % is missing after provisioning.',
                split_part(entry, '|', 1);
        END IF;
        IF found_cmd <> split_part(entry, '|', 2) THEN
            RAISE EXCEPTION
                'D32 operator verification failed: policy % has command % but the approved command is %.',
                split_part(entry, '|', 1), found_cmd, split_part(entry, '|', 2);
        END IF;
        IF NOT ('authenticated' = ANY (found_roles)) THEN
            RAISE EXCEPTION
                'D32 operator verification failed: policy % is not granted to authenticated.',
                split_part(entry, '|', 1);
        END IF;
    END LOOP;

    SELECT count(*) INTO broadened
      FROM pg_policies p
     WHERE p.schemaname = 'storage' AND p.tablename = 'objects'
       AND ('anon' = ANY (p.roles::text[]) OR 'public' = ANY (p.roles::text[]));
    IF broadened > 0 THEN
        RAISE EXCEPTION
            'D32 operator verification failed: % storage.objects policy/policies grant anon/public (no anonymous access is permitted).',
            broadened;
    END IF;
END
$d32_op_verify$;

COMMIT;

