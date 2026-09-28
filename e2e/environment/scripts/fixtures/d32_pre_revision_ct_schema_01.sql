-- ============================================================================
-- D32 (P0) — PRIVATE document storage
-- ----------------------------------------------------------------------------
-- Security hardening: customer documents must never be exposed through
-- predictable/public URLs. The ``documents`` bucket becomes PRIVATE and
-- storage.objects gains org-scoped RLS so only authenticated members of the
-- owning organisation can read/manage the objects under ``uploads/<org_id>/``.
--
-- The V3 API serves documents exclusively through short-lived signed URLs
-- (services/storage.py + /api/v3/documents/{id}/signed-url), and the pipeline
-- workspace responses sign item URLs at read time. Service-role uploads bypass
-- RLS (unchanged); signed URL generation is server-side.
--
-- ----------------------------------------------------------------------------
-- P8-D17-D32-STORAGE-POLICY-RESOLUTION-001 — PLATFORM-MANAGED POLICY MECHANISM
-- ----------------------------------------------------------------------------
-- WHY: ``storage.objects`` is owned by Supabase's provider-managed role
-- (``supabase_storage_admin``). PostgreSQL requires TABLE OWNERSHIP for
-- ``ALTER TABLE``, ``CREATE POLICY`` and ``DROP POLICY`` on that table, and
-- CarbonTally's migration role (``postgres``) must NOT be granted ownership or
-- membership of a provider role (PO decision — Route C, no privilege
-- escalation).
--
-- MECHANISM (supported; already established in this repository): the four
-- approved policies are established through Supabase's storage-policy mechanism
-- executed in the provider-privileged context — the same context this
-- repository's own e2e harness already uses for this exact migration, documented
-- in ``e2e/environment/scripts/apply_migrations.sh``:
--   "supabase db reset applies migrations as the `postgres` role, which does not
--    own `storage.objects`; the D32 storage-RLS migration therefore needs the
--    `supabase_admin` role."
-- Operationally that is the Supabase dashboard storage-policy editor, or the
-- equivalent SQL executed with provider admin rights (Supabase provides no CLI
-- or config.toml mechanism for storage RLS policies — policies are SQL DDL on
-- ``storage.objects`` in the provider context; see also
-- ``docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md``, where storage
-- provisioning is dashboard/CLI operator work rather than migration DDL).
--
-- APPROVED POLICY DEFINITIONS (single source of truth — create these in the
-- provider-privileged context; SECTION 3 validates them):
--
--   CREATE POLICY "d32_documents_select_org_member" ON storage.objects
--     FOR SELECT TO authenticated
--     USING (bucket_id = 'documents'
--            AND (storage.foldername(name))[1] = 'uploads'
--            AND (storage.foldername(name))[2]::uuid IN (
--                  SELECT organization_id FROM public.organization_members
--                   WHERE user_id = auth.uid() AND is_active = TRUE));
--
--   CREATE POLICY "d32_documents_insert_org_member" ON storage.objects
--     FOR INSERT TO authenticated
--     WITH CHECK (bucket_id = 'documents'
--            AND (storage.foldername(name))[1] = 'uploads'
--            AND (storage.foldername(name))[2]::uuid IN (
--                  SELECT organization_id FROM public.organization_members
--                   WHERE user_id = auth.uid() AND is_active = TRUE));
--
--   CREATE POLICY "d32_documents_update_org_member" ON storage.objects
--     FOR UPDATE TO authenticated
--     USING (bucket_id = 'documents'
--            AND (storage.foldername(name))[1] = 'uploads'
--            AND (storage.foldername(name))[2]::uuid IN (
--                  SELECT organization_id FROM public.organization_members
--                   WHERE user_id = auth.uid() AND is_active = TRUE));
--
--   CREATE POLICY "d32_documents_delete_org_member" ON storage.objects
--     FOR DELETE TO authenticated
--     USING (bucket_id = 'documents'
--            AND (storage.foldername(name))[1] = 'uploads'
--            AND (storage.foldername(name))[2]::uuid IN (
--                  SELECT organization_id FROM public.organization_members
--                   WHERE user_id = auth.uid() AND is_active = TRUE));
--
-- Nothing about the intended security semantics changes: the same four
-- org-scoped policies governed by the same predicates must be present, no policy
-- may grant ``anon``/``public``, and any missing, altered or broadened policy
-- fails this migration loudly.
-- ============================================================================

BEGIN;

-- 1. Private bucket — public URLs are no longer served for any object.
UPDATE storage.buckets SET public = FALSE WHERE name = 'documents';

-- 2. Org-scoped storage RLS (object path layout: uploads/<org_id>/<date>/<file>).
--
-- P8-D17-MIGRATION-REVISION-001 (PO-authorised minimal revision): the previous
-- `ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY` is NOT issued here.
-- `storage.objects` is owned by Supabase's provider-managed role
-- (`supabase_storage_admin`), and ALTER TABLE requires ownership even when the
-- change is a no-op. RLS is already enabled on `storage.objects` in every
-- environment this migration targets, so the statement was a semantic no-op that
-- could only ever fail on the ownership check. The read-only assertion below
-- replaces it: it needs no ownership, and it fails loudly if the precondition is
-- ever untrue, so the intended end state cannot silently regress.
DO $d32_rls$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'storage' AND c.relname = 'objects' AND c.relrowsecurity
    ) THEN
        RAISE EXCEPTION 'D32 precondition failed: RLS is not enabled on storage.objects';
    END IF;
END
$d32_rls$;

-- 3. Org-scoped storage policies (object path layout: uploads/<org_id>/<date>/<file>).
--
-- P8-D17-D32-STORAGE-POLICY-RESOLUTION-001: the four ``CREATE POLICY`` statements
-- that used to live here are now established through the supported Supabase
-- storage-policy mechanism in the provider-privileged context (see the header).
-- CarbonTally's migration role does not own ``storage.objects`` and must not be
-- granted it, so this migration validates the platform state instead of issuing
-- ownership-sensitive DDL. The validation is read-only, idempotent and
-- fail-closed: it requires exactly the four approved policies with their approved
-- command, role and org-scope predicate, and it refuses any policy that would
-- grant ``anon`` or ``public`` (no anonymous access).
DO $d32_policies$
DECLARE
    -- "<policy name>|<approved command>"
    approved text[] := ARRAY[
        'd32_documents_select_org_member|SELECT',
        'd32_documents_insert_org_member|INSERT',
        'd32_documents_update_org_member|UPDATE',
        'd32_documents_delete_org_member|DELETE'
    ];
    -- every approved policy must carry the org-scope predicate; checked as
    -- fragments so an equivalent rewrite of the expression still passes
    fragments text[] := ARRAY[
        'bucket_id', 'documents', 'foldername', 'uploads',
        'organization_members', 'auth.uid()', 'is_active'
    ];
    entry text;
    wanted_name text;
    wanted_cmd text;
    found record;
    predicate text;
    fragment text;
    broadened int;
BEGIN
    FOREACH entry IN ARRAY approved LOOP
        wanted_name := split_part(entry, '|', 1);
        wanted_cmd := split_part(entry, '|', 2);

        SELECT p.policyname, p.cmd, p.roles::text[] AS roles,
               coalesce(p.qual, p.with_check, '') AS pred
          INTO found
          FROM pg_policies p
         WHERE p.schemaname = 'storage'
           AND p.tablename = 'objects'
           AND p.policyname = wanted_name;

        IF found.policyname IS NULL THEN
            RAISE EXCEPTION
                'D32 precondition failed: approved policy % is missing on storage.objects '
                '(create it with the definition in this migration''s header, in the '
                'provider-privileged context)', wanted_name;
        END IF;
        IF found.cmd <> wanted_cmd THEN
            RAISE EXCEPTION 'D32 policy drift: % has command % but the approved command is %',
                wanted_name, found.cmd, wanted_cmd;
        END IF;
        IF NOT ('authenticated' = ANY (found.roles)) THEN
            RAISE EXCEPTION 'D32 policy drift: % is not granted to authenticated', wanted_name;
        END IF;
        IF 'anon' = ANY (found.roles) OR 'public' = ANY (found.roles) THEN
            RAISE EXCEPTION 'D32 policy broadening rejected: % grants anon/public', wanted_name;
        END IF;

        predicate := lower(found.pred);
        FOREACH fragment IN ARRAY fragments LOOP
            IF position(lower(fragment) in predicate) = 0 THEN
                RAISE EXCEPTION
                    'D32 policy drift: % is missing the approved org-scope fragment "%"',
                    wanted_name, fragment;
            END IF;
        END LOOP;
    END LOOP;

    -- no policy anywhere on storage.objects may grant anonymous/public access
    SELECT count(*) INTO broadened
      FROM pg_policies p
     WHERE p.schemaname = 'storage'
       AND p.tablename = 'objects'
       AND ('anon' = ANY (p.roles::text[]) OR 'public' = ANY (p.roles::text[]));
    IF broadened > 0 THEN
        RAISE EXCEPTION
            'D32 broadening rejected: % storage.objects policy/policies grant anon/public',
            broadened;
    END IF;
END
$d32_policies$;

COMMIT;
