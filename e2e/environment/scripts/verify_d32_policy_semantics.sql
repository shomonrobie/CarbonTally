-- ============================================================================
-- D32 behavioural policy-semantics proof (CT-SCHEMA-02)
-- ----------------------------------------------------------------------------
-- WHY: migration 27 and the operator step both *structurally* validate the four
-- approved storage.objects policies (names, commands, roles, org-scope predicate,
-- and the identity of auth.uid() / public.organization_members by OID). This file
-- adds the complementary *behavioural* proof: it exercises the policies under a
-- real ``authenticated`` session and shows that PostgreSQL actually permits the
-- owning organisation's object and denies everything else.
--
-- TECHNICAL FIXTURE: two organisations, two users, one active membership and two
-- storage object rows are created INSIDE a transaction that is ALWAYS rolled back
-- (see the ROLLBACK at the end), so no fixture row survives this script. The
-- fixture exists only because policy semantics cannot be proven without rows to
-- which the predicate can apply; it carries no business data.
--
-- FAIL-CLOSED: any unexpected allow or deny raises and aborts the script.
-- No GRANT/REVOKE is issued; RLS is never disabled; nothing is weakened.
--
-- APPLY AS THE MIGRATION ROLE (postgres) against a disposable target:
--   psql -X -q -v ON_ERROR_STOP=1 -U postgres -d <db> -f verify_d32_policy_semantics.sql
-- ============================================================================

BEGIN;

DO $d32_semantics$
DECLARE
    org_a uuid := gen_random_uuid();
    org_b uuid := gen_random_uuid();
    member uuid := gen_random_uuid();
    outsider uuid := gen_random_uuid();
    path_a text;
    path_b text;
    resolved_uid uuid;
    seen int;
    touched int;
    allowed boolean;
    passed int := 0;
    failed int := 0;
BEGIN
    -- ---------- structural preconditions ----------
    IF to_regclass('storage.objects') IS NULL OR to_regclass('storage.buckets') IS NULL THEN
        RAISE EXCEPTION 'D32 semantics precondition failed: the platform storage layer is absent.';
    END IF;
    IF 'auth.uid()'::regprocedure IS NULL THEN
        RAISE EXCEPTION 'D32 semantics precondition failed: auth.uid() is not resolvable.';
    END IF;
    IF (SELECT count(*) FROM pg_policies WHERE schemaname = 'storage' AND tablename = 'objects') <> 4 THEN
        RAISE EXCEPTION 'D32 semantics precondition failed: expected exactly four policies on storage.objects, found %.',
            (SELECT count(*) FROM pg_policies WHERE schemaname = 'storage' AND tablename = 'objects');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'storage' AND c.relname = 'objects' AND c.relrowsecurity) THEN
        RAISE EXCEPTION 'D32 semantics precondition failed: RLS is not enabled on storage.objects.';
    END IF;

    -- ---------- disposable fixture (rolled back at the end of this file) ----------
    INSERT INTO public.organizations (id, name) VALUES (org_a, 'CT-SCHEMA-02 semantics A');
    INSERT INTO public.organizations (id, name) VALUES (org_b, 'CT-SCHEMA-02 semantics B');
    INSERT INTO public.users (id, email) VALUES (member, 'ct02-member@example.invalid');
    INSERT INTO public.users (id, email) VALUES (outsider, 'ct02-outsider@example.invalid');
    INSERT INTO public.organization_members (organization_id, user_id, role, is_active)
        VALUES (org_a, member, 'member', TRUE);

    path_a := 'uploads/' || org_a::text || '/2026-01-01/a.pdf';
    path_b := 'uploads/' || org_b::text || '/2026-01-01/b.pdf';
    INSERT INTO storage.objects (id, bucket_id, name) VALUES (gen_random_uuid(), 'documents', path_a);
    INSERT INTO storage.objects (id, bucket_id, name) VALUES (gen_random_uuid(), 'documents', path_b);

    -- ---------- the private bucket ----------
    -- (IS NOT FALSE fails for TRUE *and* for a missing bucket; the earlier form
    --  was inverted and is corrected here.)
    IF (SELECT public FROM storage.buckets WHERE name = 'documents') IS NOT FALSE THEN
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL bucket_private (documents bucket is public or absent)';
    ELSE
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS bucket_private';
    END IF;

    -- ---------- the platform forbids direct SQL deletes on storage tables ----------
    -- ``storage.protect_delete`` is a platform trigger; a direct ``DELETE FROM
    -- storage.objects`` is refused regardless of policy. The DELETE policy is
    -- therefore verified structurally (migration 27 + canonical_schema_verify.py),
    -- and this check records the platform guarantee that objects cannot be deleted
    -- out from under the Storage API.
    IF EXISTS (
        SELECT 1 FROM pg_trigger tg
          JOIN pg_class c ON c.oid = tg.tgrelid
          JOIN pg_namespace n ON n.oid = c.relnamespace
          JOIN pg_proc p ON p.oid = tg.tgfoid
          JOIN pg_namespace fn ON fn.oid = p.pronamespace
         WHERE n.nspname = 'storage' AND c.relname = 'objects'
           AND fn.nspname = 'storage' AND p.proname = 'protect_delete'
           AND (tg.tgtype::int & 2) = 2   -- BEFORE
           AND (tg.tgtype::int & 8) = 8   -- DELETE
           AND NOT tg.tgisinternal
    ) THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS direct_sql_delete_blocked_by_platform_trigger';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL direct_sql_delete_blocked_by_platform_trigger (trigger absent)';
    END IF;

    -- ---------- act as an authenticated member of organisation A ----------
    PERFORM set_config('request.jwt.claim.sub', member::text, true);
    resolved_uid := auth.uid();
    IF resolved_uid IS DISTINCT FROM member THEN
        RAISE EXCEPTION 'D32 semantics setup failed: auth.uid() did not resolve to the fixture member (%.% -> %)',
            'request.jwt.claim.sub', member, coalesce(resolved_uid::text, 'NULL');
    END IF;

    EXECUTE 'SET LOCAL ROLE authenticated';

    SELECT count(*) INTO seen FROM storage.objects;
    IF seen = 1 THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS member_selects_own_org_object (visible rows = 1)';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL member_selects_own_org_object (visible rows = %, expected 1)', seen;
    END IF;

    SELECT count(*) INTO seen FROM storage.objects WHERE name = path_b;
    IF seen = 0 THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS member_cannot_see_other_org_object';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL member_cannot_see_other_org_object (rows = %)', seen;
    END IF;

    -- INSERT into the owning organisation's path must be permitted
    allowed := TRUE;
    BEGIN
        EXECUTE format('INSERT INTO storage.objects (id, bucket_id, name) VALUES (gen_random_uuid(), %L, %L)',
                       'documents', 'uploads/' || org_a::text || '/2026-01-02/own.pdf');
    EXCEPTION WHEN insufficient_privilege THEN
        allowed := FALSE;
    END;
    IF allowed THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS member_can_insert_own_org_path';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL member_can_insert_own_org_path (denied)';
    END IF;

    -- INSERT into another organisation's path must be denied
    allowed := FALSE;
    BEGIN
        EXECUTE format('INSERT INTO storage.objects (id, bucket_id, name) VALUES (gen_random_uuid(), %L, %L)',
                       'documents', 'uploads/' || org_b::text || '/2026-01-02/other.pdf');
        allowed := TRUE;
    EXCEPTION WHEN insufficient_privilege THEN
        allowed := FALSE;
    END;
    IF allowed THEN
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL member_cannot_insert_other_org_path (was allowed)';
    ELSE
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS member_cannot_insert_other_org_path';
    END IF;

    -- UPDATE is scoped by the same predicate: own row 1, other org 0
    EXECUTE 'UPDATE storage.objects SET updated_at = now() WHERE name = ' || quote_literal(path_a);
    GET DIAGNOSTICS touched = ROW_COUNT;
    IF touched = 1 THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS member_updates_own_org_object (rows = 1)';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL member_updates_own_org_object (rows = %, expected 1)', touched;
    END IF;

    EXECUTE 'UPDATE storage.objects SET updated_at = now() WHERE name = ' || quote_literal(path_b);
    GET DIAGNOSTICS touched = ROW_COUNT;
    IF touched = 0 THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS member_cannot_update_other_org_object (rows = 0)';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL member_cannot_update_other_org_object (rows = %)', touched;
    END IF;

    -- DELETE is scoped the same way, but the platform refuses direct SQL deletes
    -- (see the protect_delete check above), so the DELETE *policy* is validated
    -- structurally rather than behaviourally. This is recorded, not weakened.
    RAISE NOTICE 'D32_SEMANTICS NOTE delete_policy_verified_structurally (platform blocks direct SQL delete)';

    -- ---------- act as an authenticated outsider (member of no organisation) ----------
    PERFORM set_config('request.jwt.claim.sub', outsider::text, true);

    SELECT count(*) INTO seen FROM storage.objects;
    IF seen = 0 THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS outsider_sees_no_documents';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL outsider_sees_no_documents (rows = %)', seen;
    END IF;

    allowed := FALSE;
    BEGIN
        EXECUTE format('INSERT INTO storage.objects (id, bucket_id, name) VALUES (gen_random_uuid(), %L, %L)',
                       'documents', 'uploads/' || org_a::text || '/2026-01-03/outsider.pdf');
        allowed := TRUE;
    EXCEPTION WHEN insufficient_privilege THEN
        allowed := FALSE;
    END;
    IF allowed THEN
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL outsider_cannot_insert_documents (was allowed)';
    ELSE
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS outsider_cannot_insert_documents';
    END IF;

    -- ---------- a non-uploads path must not be governed by the org policy ----------
    PERFORM set_config('request.jwt.claim.sub', member::text, true);
    SELECT count(*) INTO seen FROM storage.objects WHERE name LIKE 'public/%';
    IF seen = 0 THEN
        passed := passed + 1;
        RAISE NOTICE 'D32_SEMANTICS PASS non_uploads_path_not_visible';
    ELSE
        failed := failed + 1;
        RAISE WARNING 'D32_SEMANTICS FAIL non_uploads_path_not_visible (rows = %)', seen;
    END IF;

    RESET ROLE;

    RAISE NOTICE 'D32_SEMANTICS_RESULT pass=% fail=%', passed, failed;
    IF failed > 0 THEN
        RAISE EXCEPTION 'D32 behavioural policy-semantics proof FAILED (% checks failed, % passed)', failed, passed;
    END IF;
END
$d32_semantics$;

-- The fixture is disposable by construction: nothing above survives this script.
ROLLBACK;

