-- ============================================================================
-- CT-IMPLEMENT-02 — database verification suite (R-9, R-10.6, R-3, PD-1, PD-2)
-- File: e2e/environment/scripts/ct02_db_suite.sql
--
-- Runs against a DISPOSABLE canonical-schema database only.
--
-- STRUCTURE: everything runs inside ONE transaction that ends with ROLLBACK,
-- so the suite creates fixtures (tenants, members, reports, versions, log rows)
-- and proves behaviour *without persisting anything*. A run therefore cannot
-- damage a data-bearing target even if it is pointed at one, and cannot leave
-- residue that a later run would trip over.
--
-- Two kinds of assertion are emitted, both machine-parsed by
-- e2e/environment/scripts/ct02_verify_db.py:
--   NOTICE ... PASS <name> ...
--   NOTICE ... FAIL <name> ...
--
-- NEGATIVE TESTS ASSERT THE *REASON*, NOT MERELY THAT SOMETHING FAILED.
-- A test expecting an RLS denial checks that the refusal is an RLS outcome; a
-- test expecting a privilege denial checks that it is a privilege denial. This
-- prevents the classic false pass where a missing GRANT masquerades as a
-- working security boundary.
--
-- SAFETY: no investor/demo/live database, no production target. The wrapper
-- script refuses database names matching qa/demo/investor/prod/live.
-- ============================================================================

\set ON_ERROR_STOP off
\pset format unaligned
\pset tuples_only on
\pset pager off

BEGIN;

-- ---------------------------------------------------------------------------
-- Fixtures (rolled back at the end)
-- ---------------------------------------------------------------------------
INSERT INTO public.users (id, email) VALUES
    ('11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test'),
    ('22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test'),
    ('33333333-0000-4000-8000-00000000000c', 'ct02-consultant@example.test'),
    ('44444444-0000-4000-8000-00000000000d', 'ct02-recipient@example.test');

INSERT INTO public.organizations (id, name) VALUES
    ('aaaaaaaa-0000-4000-8000-000000000001', 'CT02 Tenant A'),
    ('bbbbbbbb-0000-4000-8000-000000000002', 'CT02 Tenant B'),
    ('cccccccc-0000-4000-8000-000000000003', 'CT02 Consultant Firm C');

INSERT INTO public.organization_members (organization_id, user_id, role, is_active) VALUES
    ('aaaaaaaa-0000-4000-8000-000000000001', '11111111-0000-4000-8000-00000000000a', 'owner', true),
    ('bbbbbbbb-0000-4000-8000-000000000002', '22222222-0000-4000-8000-00000000000b', 'owner', true),
    ('cccccccc-0000-4000-8000-000000000003', '33333333-0000-4000-8000-00000000000c', 'owner', true),
    -- The consultant also operates client A (its entitled client), not client B.
    ('aaaaaaaa-0000-4000-8000-000000000001', '33333333-0000-4000-8000-00000000000c', 'admin', true);

-- Reports and versions: A has an immutable (APPROVED) version and a mutable
-- (DRAFT) one; B has its own report + immutable version.
INSERT INTO public.report_generation_queue (id, organization_id, report_type, reporting_year, report_name, status)
VALUES
    ('a1000000-0000-4000-8000-0000000000a1', 'aaaaaaaa-0000-4000-8000-000000000001', 'annual', 2024, 'CT02 A annual 2024', 'completed'),
    ('b1000000-0000-4000-8000-0000000000b1', 'bbbbbbbb-0000-4000-8000-000000000002', 'annual', 2024, 'CT02 B annual 2024', 'completed');

INSERT INTO public.report_versions (id, report_id, version_number, status, is_current)
VALUES
    ('a2000000-0000-4000-8000-0000000000a1', 'a1000000-0000-4000-8000-0000000000a1', 1, 'APPROVED', true),
    ('a2000000-0000-4000-8000-0000000000a2', 'a1000000-0000-4000-8000-0000000000a1', 2, 'DRAFT', false),
    ('b2000000-0000-4000-8000-0000000000b1', 'b1000000-0000-4000-8000-0000000000b1', 1, 'FINAL', true);

INSERT INTO public.emissions_logs (
    id, organization_id, raw_quantity, unit,
    calculated_kg_co2e, start_date, end_date, created_by_user_id
) VALUES
    ('a3000000-0000-4000-8000-0000000000a1', 'aaaaaaaa-0000-4000-8000-000000000001',
     100, 'litres', 268.0, '2024-03-01', '2024-03-01',
     '11111111-0000-4000-8000-00000000000a'),
    ('b3000000-0000-4000-8000-0000000000b1', 'bbbbbbbb-0000-4000-8000-000000000002',
     200, 'litres', 536.0, '2024-03-01', '2024-03-01',
     '22222222-0000-4000-8000-00000000000b');

-- Source documents (one per tenant) for the document-isolation and provenance
-- tests. `organization_member_id` is NOT NULL, so a member row is required.
INSERT INTO public.customer_documents (
    id, organization_id, organization_member_id, file_name, file_type, file_url
) VALUES
    ('a4000000-0000-4000-8000-0000000000a1', 'aaaaaaaa-0000-4000-8000-000000000001',
     (SELECT id FROM public.organization_members
       WHERE organization_id = 'aaaaaaaa-0000-4000-8000-000000000001'
         AND user_id = '11111111-0000-4000-8000-00000000000a'),
     'ct02-tenant-a-invoice.pdf', 'application/pdf', 'ct02/test/a.pdf'),
    ('b4000000-0000-4000-8000-0000000000b1', 'bbbbbbbb-0000-4000-8000-000000000002',
     (SELECT id FROM public.organization_members
       WHERE organization_id = 'bbbbbbbb-0000-4000-8000-000000000002'
         AND user_id = '22222222-0000-4000-8000-00000000000b'),
     'ct02-tenant-b-invoice.pdf', 'application/pdf', 'ct02/test/b.pdf');

-- Provenance spine fixtures (R-3). The canonical chain is carried by real
-- foreign keys, so every link has to be a real row:
--   import_batch -> manual_extraction_item -> calculation_snapshot -> emission log
-- and the snapshot's factor provenance is constrained by
-- calculation_snapshots_exactly_one_source_check (factor_kind + the matching FK).
INSERT INTO public.emission_factors (id, activity_type, co2e_multiplier, reporting_year)
VALUES ('af000000-0000-4000-8000-0000000000a1', 'CT02 diesel', 2.68, 2024);

INSERT INTO public.manual_extraction_batches (
    id, batch_name, organization_id, total_cost, total_documents, total_pages
) VALUES ('ab000000-0000-4000-8000-0000000000a1', 'CT02 extraction batch A',
          'aaaaaaaa-0000-4000-8000-000000000001', 0, 1, 1);

INSERT INTO public.manual_extraction_items (
    id, batch_id, file_name, file_url, page_count, status, extracted_data
) VALUES ('a6000000-0000-4000-8000-0000000000a1', 'ab000000-0000-4000-8000-0000000000a1',
          'ct02-tenant-a-invoice.pdf', 'ct02/test/a.pdf', 1, 'extracted',
          '{"raw_quantity": 100, "unit": "litres"}'::jsonb);

INSERT INTO public.calculation_snapshots (
    id, organization_id, activity, activity_type, algorithm_version,
    co2e_kg, co2e_multiplier, content_hash, date, methodology,
    quantity, quantity_unit, reporting_year, source_item_id, source_page,
    source_file, factor_kind, factor_id, factor_source, factor_set
) VALUES
    ('a5000000-0000-4000-8000-0000000000a1', 'aaaaaaaa-0000-4000-8000-000000000001',
     'CT02 diesel', 'CT02 diesel', 'ct02-fixture', 268.0, 2.68,
     repeat('a', 64), '2024-03-01', 'DEFRA', 100, 'litres', 2024,
     'a6000000-0000-4000-8000-0000000000a1', 1,
     'ct02/test/a.pdf', 'emission_factor',
     'af000000-0000-4000-8000-0000000000a1', 'carbontally', 'defra-2024');


-- ---------------------------------------------------------------------------
-- Assertion helpers (session-temporary: they vanish on ROLLBACK)
-- ---------------------------------------------------------------------------
CREATE FUNCTION pg_temp.ct02_expect_fail(p_name text, p_sql text, p_marker text)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_msg text;
BEGIN
    BEGIN
        EXECUTE p_sql;
    EXCEPTION WHEN others THEN
        v_msg := SQLERRM;
        -- Every test starts from the owner role: a test that switched role and
        -- failed must not leak that role into the next test.
        EXECUTE 'RESET ROLE';
        IF v_msg LIKE '%' || p_marker || '%' THEN
            RAISE NOTICE 'PASS % — refused: %', p_name, v_msg;
        ELSE
            RAISE NOTICE 'FAIL % — refused for the WRONG reason: %', p_name, v_msg;
        END IF;
        RETURN;
    END;
    EXECUTE 'RESET ROLE';
    RAISE NOTICE 'FAIL % — statement unexpectedly SUCCEEDED', p_name;
END $$;

CREATE FUNCTION pg_temp.ct02_expect_ok(p_name text, p_sql text)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_msg text;
BEGIN
    BEGIN
        EXECUTE p_sql;
        EXECUTE 'RESET ROLE';
        RAISE NOTICE 'PASS %', p_name;
    EXCEPTION WHEN others THEN
        v_msg := SQLERRM;
        EXECUTE 'RESET ROLE';
        RAISE NOTICE 'FAIL % — unexpectedly refused: %', p_name, v_msg;
    END;
END $$;

CREATE FUNCTION pg_temp.ct02_expect_eq(p_name text, p_sql text, p_expected bigint)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_n bigint; v_msg text;
BEGIN
    BEGIN
        EXECUTE p_sql INTO v_n;
    EXCEPTION WHEN others THEN
        v_msg := SQLERRM;
        RAISE NOTICE 'FAIL % — query errored: %', p_name, v_msg;
        RETURN;
    END;
    IF v_n = p_expected THEN
        RAISE NOTICE 'PASS % — %', p_name, v_n;
    ELSE
        RAISE NOTICE 'FAIL % — got % expected %', p_name, v_n, p_expected;
    END IF;
END $$;

-- ===========================================================================
-- A. AUDIT LEDGER (R-10.6 / PD-4): append-only, including TRUNCATE
-- ===========================================================================
-- Privilege denials are asserted as privilege denials...
SELECT pg_temp.ct02_expect_fail('audit_truncate_denied_service_role',
    'SET ROLE service_role; TRUNCATE public.audit_trail', 'permission denied');
SELECT pg_temp.ct02_expect_fail('audit_update_denied_service_role',
    'SET ROLE service_role; UPDATE public.audit_trail SET action_type = ''x''', 'permission denied');
SELECT pg_temp.ct02_expect_fail('audit_delete_denied_service_role',
    'SET ROLE service_role; DELETE FROM public.audit_trail', 'permission denied');
SELECT pg_temp.ct02_expect_fail('audit_insert_denied_authenticated',
    'SET ROLE authenticated; INSERT INTO public.audit_trail '
    '(action_type, table_name, record_id, performed_by) VALUES '
    '(''p'',''p'',''a1000000-0000-4000-8000-0000000000a1'','
    '''11111111-0000-4000-8000-00000000000a'')', 'permission denied');
-- ...and the owner/table-owner path is asserted as a TRIGGER refusal, because
-- privileges cannot bind the owner: that is precisely why the statement-level
-- guard exists.
SELECT pg_temp.ct02_expect_fail('audit_truncate_denied_owner_via_trigger',
    'RESET ROLE; TRUNCATE public.audit_trail', 'TRUNCATE of');
-- The legitimate write path is preserved (server-side writer keeps INSERT).
SELECT pg_temp.ct02_expect_ok('audit_insert_allowed_service_role',
    'SET ROLE service_role; INSERT INTO public.audit_trail '
    '(action_type, table_name, record_id, performed_by, metadata) VALUES '
    '(''ct02_suite_probe'',''ct02_suite_probe'',''a1000000-0000-4000-8000-0000000000a1'','
    '''00000000-0000-0000-0000-000000000000'',''{}''::jsonb); RESET ROLE');

-- ===========================================================================
-- B. RETAINED LEGACY AUDIT SURFACES (F-5 / R-10.6)
-- ===========================================================================
SELECT pg_temp.ct02_expect_fail('legacy_audit_logs_update_denied_service_role',
    'SET ROLE service_role; UPDATE public.audit_logs SET action = ''x''', 'permission denied');
SELECT pg_temp.ct02_expect_fail('legacy_audit_logs_delete_denied_service_role',
    'SET ROLE service_role; DELETE FROM public.audit_logs', 'permission denied');
SELECT pg_temp.ct02_expect_fail('legacy_audit_logs_truncate_denied_service_role',
    'SET ROLE service_role; TRUNCATE public.audit_logs', 'permission denied');
SELECT pg_temp.ct02_expect_fail('legacy_audit_logs_insert_denied_authenticated',
    'SET ROLE authenticated; INSERT INTO public.audit_logs '
    '(action_type, action) VALUES (''ct02_probe'', ''ct02_probe'')',
    'permission denied');
SELECT pg_temp.ct02_expect_ok('legacy_audit_logs_insert_allowed_service_role',
    'SET ROLE service_role; INSERT INTO public.audit_logs '
    '(action_type, action) VALUES (''ct02_probe'', ''ct02_probe''); RESET ROLE');
-- Row-level guards need a row to fire on: create one, then prove UPDATE and
-- DELETE are refused for the table owner too (privileges cannot bind the owner,
-- so this is the trigger doing the work).
SELECT pg_temp.ct02_expect_ok('legacy_activity_logs_row_created',
    'INSERT INTO public.activity_logs (action, resource_type) '
    'VALUES (''ct02_probe'', ''ct02_probe'')');
SELECT pg_temp.ct02_expect_fail('legacy_activity_logs_update_denied_owner_via_trigger',
    'RESET ROLE; UPDATE public.activity_logs SET action = ''x'' WHERE true',
    'append-only table');
SELECT pg_temp.ct02_expect_fail('legacy_activity_logs_delete_denied_owner_via_trigger',
    'RESET ROLE; DELETE FROM public.activity_logs WHERE true',
    'append-only table');
SELECT pg_temp.ct02_expect_fail('legacy_activity_logs_truncate_denied_owner_via_trigger',
    'RESET ROLE; TRUNCATE public.activity_logs', 'TRUNCATE of');


-- ---------------------------------------------------------------------------
-- Actor-scoped helpers: run a statement AS a role with a simulated JWT, so the
-- real RLS policies (not application filters) decide the outcome.
-- ---------------------------------------------------------------------------
CREATE FUNCTION pg_temp.ct02_actor(p_role text, p_sub text, p_email text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    PERFORM set_config('role', p_role, true);
    PERFORM set_config('request.jwt.claim.sub', coalesce(p_sub, ''), true);
    PERFORM set_config('request.jwt.claim.email', coalesce(p_email, ''), true);
END $$;

CREATE FUNCTION pg_temp.ct02_assert_actor(p_name text, p_marker text, p_error text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    EXECUTE 'RESET ROLE';
    IF p_error IS NULL THEN
        RAISE NOTICE 'FAIL % — statement unexpectedly SUCCEEDED', p_name;
    ELSIF p_error LIKE '%' || p_marker || '%' THEN
        RAISE NOTICE 'PASS % — refused: %', p_name, p_error;
    ELSE
        RAISE NOTICE 'FAIL % — refused for the WRONG reason: %', p_name, p_error;
    END IF;
END $$;

CREATE FUNCTION pg_temp.ct02_expect_fail_as(
    p_name text, p_role text, p_sub text, p_email text, p_sql text, p_marker text)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_err text;
BEGIN
    PERFORM pg_temp.ct02_actor(p_role, p_sub, p_email);
    BEGIN
        EXECUTE p_sql;
    EXCEPTION WHEN others THEN
        v_err := SQLERRM;
    END;
    PERFORM pg_temp.ct02_assert_actor(p_name, p_marker, v_err);
END $$;

CREATE FUNCTION pg_temp.ct02_expect_ok_as(
    p_name text, p_role text, p_sub text, p_email text, p_sql text)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_err text;
BEGIN
    PERFORM pg_temp.ct02_actor(p_role, p_sub, p_email);
    BEGIN
        EXECUTE p_sql;
    EXCEPTION WHEN others THEN
        v_err := SQLERRM;
    END;
    EXECUTE 'RESET ROLE';
    IF v_err IS NULL THEN
        RAISE NOTICE 'PASS %', p_name;
    ELSE
        RAISE NOTICE 'FAIL % — unexpectedly refused: %', p_name, v_err;
    END IF;
END $$;

CREATE FUNCTION pg_temp.ct02_expect_rows_as(
    p_name text, p_role text, p_sub text, p_email text, p_sql text, p_expected bigint)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_n bigint; v_err text;
BEGIN
    PERFORM pg_temp.ct02_actor(p_role, p_sub, p_email);
    BEGIN
        EXECUTE p_sql INTO v_n;
    EXCEPTION WHEN others THEN
        v_err := SQLERRM;
    END;
    EXECUTE 'RESET ROLE';
    IF v_err IS NOT NULL THEN
        RAISE NOTICE 'FAIL % — query errored: %', p_name, v_err;
    ELSIF v_n = p_expected THEN
        RAISE NOTICE 'PASS % — rows=%', p_name, v_n;
    ELSE
        RAISE NOTICE 'FAIL % — rows=% expected=%', p_name, v_n, p_expected;
    END IF;
END $$;

-- ===========================================================================
-- C. REPORT SHARING (PD-1)
-- ===========================================================================
-- Positive control: the tenant's own admin may share its immutable version.
SELECT pg_temp.ct02_expect_ok_as('share_created_for_immutable_version',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_shares
        (id, organization_id, report_id, report_version_id, permission,
         recipient_email, created_by, expires_at, share_token_hash)
     VALUES (''a7000000-0000-4000-8000-0000000000a1'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a1000000-0000-4000-8000-0000000000a1'',
             ''a2000000-0000-4000-8000-0000000000a1'',
             ''view'', ''ct02-recipient@example.test'',
             ''11111111-0000-4000-8000-00000000000a'',
             now() + interval ''30 days'', repeat(''b'', 64))');

-- A second share, for the revocation / recipient tests (user-addressed).
SELECT pg_temp.ct02_expect_ok_as('share_created_for_user_recipient',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_shares
        (id, organization_id, report_id, report_version_id, permission,
         recipient_user_id, created_by)
     VALUES (''a7000000-0000-4000-8000-0000000000a2'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a1000000-0000-4000-8000-0000000000a1'',
             ''a2000000-0000-4000-8000-0000000000a1'',
             ''download'', ''44444444-0000-4000-8000-00000000000d'',
             ''11111111-0000-4000-8000-00000000000a'')');

-- CROSS-TENANT: tenant A may not share tenant B's version, even as its admin.
SELECT pg_temp.ct02_expect_fail_as('share_cross_tenant_denied_by_rls',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_shares
        (organization_id, report_id, report_version_id, permission,
         recipient_email, created_by)
     VALUES (''bbbbbbbb-0000-4000-8000-000000000002'',
             ''b1000000-0000-4000-8000-0000000000b1'',
             ''b2000000-0000-4000-8000-0000000000b1'',
             ''view'', ''ct02-owner-a@example.test'',
             ''11111111-0000-4000-8000-00000000000a'')',
    'row-level security');

-- A mutable (DRAFT) version must never be shared — refused by trigger.
SELECT pg_temp.ct02_expect_fail_as('share_mutable_version_denied_by_trigger',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_shares
        (organization_id, report_id, report_version_id, permission,
         recipient_email, created_by)
     VALUES (''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a1000000-0000-4000-8000-0000000000a1'',
             ''a2000000-0000-4000-8000-0000000000a2'',
             ''view'', ''ct02-draft@example.test'',
             ''11111111-0000-4000-8000-00000000000a'')',
    'only an immutable');

-- CHECK-level guarantees.
SELECT pg_temp.ct02_expect_fail_as('share_without_recipient_refused',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_shares
        (organization_id, report_id, report_version_id, permission, created_by)
     VALUES (''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a1000000-0000-4000-8000-0000000000a1'',
             ''a2000000-0000-4000-8000-0000000000a1'',
             ''view'', ''11111111-0000-4000-8000-00000000000a'')',
    'report_shares_recipient_check');

SELECT pg_temp.ct02_expect_fail_as('share_bad_permission_refused',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_shares
        (organization_id, report_id, report_version_id, permission,
         recipient_email, created_by)
     VALUES (''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a1000000-0000-4000-8000-0000000000a1'',
             ''a2000000-0000-4000-8000-0000000000a1'',
             ''admin'', ''ct02-badperm@example.test'',
             ''11111111-0000-4000-8000-00000000000a'')',
    'report_shares_permission_check');

-- Scope is frozen: a share may not be re-pointed at another version.
SELECT pg_temp.ct02_expect_fail_as('share_scope_change_refused',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'UPDATE public.report_shares
        SET report_version_id = ''a2000000-0000-4000-8000-0000000000a2''
      WHERE id = ''a7000000-0000-4000-8000-0000000000a1''',
    'immutable');

-- Revocation must be self-describing, then one-way.
SELECT pg_temp.ct02_expect_fail_as('share_revocation_requires_reason',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'UPDATE public.report_shares SET revoked_at = now()
      WHERE id = ''a7000000-0000-4000-8000-0000000000a1''',
    'report_shares_revocation_described_check');

SELECT pg_temp.ct02_expect_ok_as('share_revocation_recorded',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'UPDATE public.report_shares
        SET revoked_at = now(),
            revoked_by = ''11111111-0000-4000-8000-00000000000a'',
            revocation_reason = ''ct02 suite: client withdrew access''
      WHERE id = ''a7000000-0000-4000-8000-0000000000a1''');

SELECT pg_temp.ct02_expect_fail_as('share_revocation_is_one_way',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'UPDATE public.report_shares SET revoked_at = now() + interval ''1 day''
      WHERE id = ''a7000000-0000-4000-8000-0000000000a1''',
    'already revoked');

-- Access history is append-only and written server-side only.
SELECT pg_temp.ct02_expect_ok('share_access_event_recorded',
    'INSERT INTO public.report_share_access_events
        (share_id, organization_id, report_version_id, actor_user_id, event_type)
     VALUES (''a7000000-0000-4000-8000-0000000000a2'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a2000000-0000-4000-8000-0000000000a1'',
             ''44444444-0000-4000-8000-00000000000d'', ''access'')');

SELECT pg_temp.ct02_expect_fail('share_access_event_update_denied',
    'UPDATE public.report_share_access_events SET event_type = ''download''',
    'append-only table');

SELECT pg_temp.ct02_expect_fail('share_access_event_authenticated_insert_denied',
    'SET ROLE authenticated; INSERT INTO public.report_share_access_events
        (share_id, organization_id, report_version_id, event_type)
     VALUES (''a7000000-0000-4000-8000-0000000000a2'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''a2000000-0000-4000-8000-0000000000a1'', ''access'')',
    'permission denied');


-- ===========================================================================
-- D. SCHEDULED REPORTING (PD-2)
-- ===========================================================================
SELECT pg_temp.ct02_expect_ok_as('schedule_created',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_schedule_definitions
        (id, organization_id, name, report_type, reporting_year, recipients,
         frequency, timezone, is_active, created_by, next_run_at)
     VALUES (''a8000000-0000-4000-8000-0000000000a1'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''CT02 monthly board pack'', ''annual'', 2024,
             ''[{"email": "ct02-owner-a@example.test"}]''::jsonb,
             ''monthly'', ''Europe/London'', true,
             ''11111111-0000-4000-8000-00000000000a'',
             now() + interval ''1 day'')');

SELECT pg_temp.ct02_expect_fail_as('schedule_unknown_timezone_refused',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_schedule_definitions
        (organization_id, name, report_type, reporting_year, recipients,
         frequency, timezone, created_by, next_run_at)
     VALUES (''aaaaaaaa-0000-4000-8000-000000000001'',
             ''CT02 bad tz'', ''annual'', 2024, ''[{"email":"x@example.test"}]''::jsonb,
             ''monthly'', ''Mars/Olympus_Mons'',
             ''11111111-0000-4000-8000-00000000000a'',
             now() + interval ''1 day'')',
    'not a known IANA timezone');

SELECT pg_temp.ct02_expect_fail_as('schedule_empty_recipients_refused',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_schedule_definitions
        (organization_id, name, report_type, reporting_year, recipients,
         frequency, timezone, created_by, next_run_at)
     VALUES (''aaaaaaaa-0000-4000-8000-000000000001'',
             ''CT02 no recipients'', ''annual'', 2024, ''[]''::jsonb,
             ''monthly'', ''Europe/London'',
             ''11111111-0000-4000-8000-00000000000a'',
             now() + interval ''1 day'')',
    'report_schedule_definitions_recipients_check');

SELECT pg_temp.ct02_expect_fail_as('schedule_unsupported_report_type_refused',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_schedule_definitions
        (organization_id, name, report_type, reporting_year, recipients,
         frequency, timezone, created_by, next_run_at)
     VALUES (''aaaaaaaa-0000-4000-8000-000000000001'',
             ''CT02 fancy report'', ''cdp_ghg_inventory'', 2024,
             ''[{"email":"x@example.test"}]''::jsonb,
             ''monthly'', ''Europe/London'',
             ''11111111-0000-4000-8000-00000000000a'',
             now() + interval ''1 day'')',
    'report_schedule_definitions_report_type_check');

-- A schedule may not be created for another tenant's organisation (RLS).
SELECT pg_temp.ct02_expect_fail_as('schedule_cross_tenant_denied_by_rls',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'INSERT INTO public.report_schedule_definitions
        (organization_id, name, report_type, reporting_year, recipients,
         frequency, timezone, created_by, next_run_at)
     VALUES (''bbbbbbbb-0000-4000-8000-000000000002'',
             ''CT02 cross-tenant schedule'', ''annual'', 2024,
             ''[{"email":"x@example.test"}]''::jsonb,
             ''monthly'', ''Europe/London'',
             ''11111111-0000-4000-8000-00000000000a'',
             now() + interval ''1 day'')',
    'row-level security');

-- Execution is idempotent per due slot.
SELECT pg_temp.ct02_expect_ok('schedule_run_recorded',
    'INSERT INTO public.report_schedule_runs
        (id, schedule_id, organization_id, scheduled_for, status,
         finished_at, report_id, report_version_id, result_summary)
     VALUES (''a9000000-0000-4000-8000-0000000000a1'',
             ''a8000000-0000-4000-8000-0000000000a1'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''2024-07-01 06:00:00+00'', ''succeeded'', now(),
             ''a1000000-0000-4000-8000-0000000000a1'',
             ''a2000000-0000-4000-8000-0000000000a1'',
             ''{"emissions_kg_co2e": 268.0}''::jsonb)');

SELECT pg_temp.ct02_expect_fail('schedule_run_duplicate_slot_refused',
    'INSERT INTO public.report_schedule_runs
        (schedule_id, organization_id, scheduled_for, status, finished_at)
     VALUES (''a8000000-0000-4000-8000-0000000000a1'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''2024-07-01 06:00:00+00'', ''succeeded'', now())',
    'report_schedule_runs_slot_key');

SELECT pg_temp.ct02_expect_fail('schedule_run_terminal_record_immutable',
    'UPDATE public.report_schedule_runs
        SET error_code = ''rewritten_after_the_fact''
      WHERE id = ''a9000000-0000-4000-8000-0000000000a1''',
    'already terminal');

SELECT pg_temp.ct02_expect_fail('schedule_run_delete_refused',
    'DELETE FROM public.report_schedule_runs
      WHERE id = ''a9000000-0000-4000-8000-0000000000a1''',
    'append-only');

SELECT pg_temp.ct02_expect_fail('schedule_failed_run_requires_reason',
    'INSERT INTO public.report_schedule_runs
        (schedule_id, organization_id, scheduled_for, status, finished_at)
     VALUES (''a8000000-0000-4000-8000-0000000000a1'',
             ''aaaaaaaa-0000-4000-8000-000000000001'',
             ''2024-08-01 06:00:00+00'', ''failed'', now())',
    'report_schedule_runs_failure_described_check');


-- ===========================================================================
-- E. TENANT ISOLATION (R-9) — RLS enforcement, READ and WRITE
--    Each block proves BOTH directions: the tenant's own row is visible (the
--    positive control that stops a broken query passing as "isolation"), and
--    the other tenant's row is not.
-- ===========================================================================
-- E1. Emissions data.
SELECT pg_temp.ct02_expect_rows_as('iso_emissions_own_tenant_visible',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.emissions_logs
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 1);
SELECT pg_temp.ct02_expect_rows_as('iso_emissions_other_tenant_denied',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.emissions_logs
      WHERE organization_id = ''bbbbbbbb-0000-4000-8000-000000000002''', 0);

-- E2. Report versions and report rows.
-- FINDING (recorded, not normalised away): `report_versions` carries RLS with
-- ZERO policies (the documented app-layer-only posture from migration
-- 20260921000000). A client session therefore sees NO version rows at all —
-- stronger than a policy-based tenant filter. The assertions below pin BOTH
-- facts: the client sees nothing, and the server-side path still sees exactly
-- the tenant's own rows.
SELECT pg_temp.ct02_expect_rows_as('iso_report_versions_client_sees_none_own_tenant',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.report_versions', 0);
SELECT pg_temp.ct02_expect_rows_as('iso_report_versions_client_sees_none_other_tenant',
    'authenticated', '22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test',
    'SELECT count(*) FROM public.report_versions', 0);
-- Server-side (BYPASSRLS) read is the authoritative one, and it is org-filtered
-- by the application: tenant A's versions only.
SELECT pg_temp.ct02_expect_eq('iso_report_versions_server_side_org_filtered',
    'SELECT count(*) FROM public.report_versions rv
       JOIN public.report_generation_queue rq ON rq.id = rv.report_id
      WHERE rq.organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 2);

-- E3. Source documents (download boundary).
SELECT pg_temp.ct02_expect_rows_as('iso_documents_own_visible',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.customer_documents
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 1);
SELECT pg_temp.ct02_expect_rows_as('iso_documents_other_denied',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.customer_documents
      WHERE organization_id = ''bbbbbbbb-0000-4000-8000-000000000002''', 0);

-- E4. Calculation snapshots (accounting evidence).
SELECT pg_temp.ct02_expect_rows_as('iso_calculations_own_visible',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.calculation_snapshots
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 1);
SELECT pg_temp.ct02_expect_rows_as('iso_calculations_other_denied',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.calculation_snapshots
      WHERE organization_id = ''bbbbbbbb-0000-4000-8000-000000000002''', 0);


-- E5. Report shares: tenant-scoped, and recipient-scoped.
SELECT pg_temp.ct02_expect_rows_as('iso_shares_own_tenant_visible',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.report_shares
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 2);
SELECT pg_temp.ct02_expect_rows_as('iso_shares_other_tenant_denied',
    'authenticated', '22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test',
    'SELECT count(*) FROM public.report_shares
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 0);
-- The recipient sees the share addressed to them (positive control)...
SELECT pg_temp.ct02_expect_rows_as('iso_share_visible_to_addressed_recipient',
    'authenticated', '44444444-0000-4000-8000-00000000000d', 'ct02-recipient@example.test',
    'SELECT count(*) FROM public.report_shares
      WHERE id = ''a7000000-0000-4000-8000-0000000000a2''', 1);
-- ...but an unrelated authenticated user does not.
SELECT pg_temp.ct02_expect_rows_as('iso_share_hidden_from_unrelated_user',
    'authenticated', '22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test',
    'SELECT count(*) FROM public.report_shares
      WHERE id = ''a7000000-0000-4000-8000-0000000000a2''', 0);
-- An EMAIL-addressed share is matched on the authenticated email exactly:
-- the addressed address sees it, a different address with its own session
-- (even a real user of another tenant) does not.
SELECT pg_temp.ct02_expect_rows_as('iso_email_addressed_share_visible_by_email',
    'authenticated', '44444444-0000-4000-8000-00000000000d', 'ct02-recipient@example.test',
    'SELECT count(*) FROM public.report_shares
      WHERE id = ''a7000000-0000-4000-8000-0000000000a1''', 1);
SELECT pg_temp.ct02_expect_rows_as('iso_email_addressed_share_hidden_from_other_email',
    'authenticated', '22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test',
    'SELECT count(*) FROM public.report_shares
      WHERE id = ''a7000000-0000-4000-8000-0000000000a1''', 0);

-- E6. Schedule runs and audit events.
SELECT pg_temp.ct02_expect_rows_as('iso_schedule_runs_own_visible',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*) FROM public.report_schedule_runs
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 1);
SELECT pg_temp.ct02_expect_rows_as('iso_schedule_runs_other_denied',
    'authenticated', '22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test',
    'SELECT count(*) FROM public.report_schedule_runs
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 0);
SELECT pg_temp.ct02_expect_rows_as('iso_audit_trail_other_org_denied',
    'authenticated', '22222222-0000-4000-8000-00000000000b', 'ct02-owner-b@example.test',
    'SELECT count(*) FROM public.audit_trail
      WHERE metadata->>''organization_id'' = ''aaaaaaaa-0000-4000-8000-000000000001''', 0);

-- E7. Consultant operating model: the consultant is entitled to client A and
--     must still be refused client B (acting-for never widens access).
SELECT pg_temp.ct02_expect_rows_as('iso_consultant_sees_entitled_client',
    'authenticated', '33333333-0000-4000-8000-00000000000c', 'ct02-consultant@example.test',
    'SELECT count(*) FROM public.emissions_logs
      WHERE organization_id = ''aaaaaaaa-0000-4000-8000-000000000001''', 1);
SELECT pg_temp.ct02_expect_rows_as('iso_consultant_denied_other_client',
    'authenticated', '33333333-0000-4000-8000-00000000000c', 'ct02-consultant@example.test',
    'SELECT count(*) FROM public.emissions_logs
      WHERE organization_id = ''bbbbbbbb-0000-4000-8000-000000000002''', 0);


-- E8. Anonymous access to business data is denied by PRIVILEGE, and the denial
--     must be a privilege denial rather than a silent empty result — an empty
--     result would make an unauthenticated read look "safe" without actually
--     being refused.
SELECT pg_temp.ct02_expect_fail_as('anon_emissions_denied',
    'anon', '', '', 'SELECT count(*) FROM public.emissions_logs', 'permission denied');
SELECT pg_temp.ct02_expect_fail_as('anon_report_shares_denied',
    'anon', '', '', 'SELECT count(*) FROM public.report_shares', 'permission denied');
SELECT pg_temp.ct02_expect_fail_as('anon_schedules_denied',
    'anon', '', '', 'SELECT count(*) FROM public.report_schedule_definitions',
    'permission denied');

-- E9. An authenticated session with no identity claim must see nothing: RLS has
--     no reason to expose rows, and this is asserted so that "isolation" is not
--     accidentally the product of an empty fixture set.
SELECT pg_temp.ct02_expect_rows_as('iso_no_claim_authenticated_sees_nothing',
    'authenticated', '', '',
    'SELECT count(*) FROM public.emissions_logs', 0);

-- ===========================================================================
-- F. SOURCE-TO-REPORT PROVENANCE (R-3)
--    Proves the canonical chain is carried by real columns/keys, not by a
--    detached JSON blob: source document -> calculation snapshot (with its
--    source item + page) -> the emission log that consumes it.
-- ===========================================================================
SELECT pg_temp.ct02_expect_rows_as('provenance_snapshot_carries_source_context',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*)
       FROM public.calculation_snapshots cs
      WHERE cs.id = ''a5000000-0000-4000-8000-0000000000a1''
        AND cs.source_item_id IS NOT NULL
        AND cs.source_page IS NOT NULL
        AND cs.source_file IS NOT NULL
        AND cs.factor_kind IS NOT NULL', 1);

SELECT pg_temp.ct02_expect_eq('provenance_chain_columns_present',
    'SELECT count(*) FROM (
        SELECT 1 WHERE to_regclass(''public.calculation_snapshots'') IS NOT NULL
        INTERSECT SELECT 1 WHERE EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema=''public'' AND table_name=''calculation_snapshots''
              AND column_name IN (''source_item_id'',''source_page'',''factor_id'',''customer_factor_id''))
        INTERSECT SELECT 1 WHERE (
            SELECT count(*) FROM information_schema.columns
             WHERE table_schema=''public'' AND table_name=''calculation_snapshots''
               AND column_name IN (''source_item_id'',''source_page'',''factor_id'',''customer_factor_id'')) = 4
     ) s', 1);

-- A corrected mapping must be recoverable: the original value stays alongside
-- the corrected one, with actor/reason/time (P17-H / DM-7 shape).
SELECT pg_temp.ct02_expect_eq('provenance_correction_columns_present',
    'SELECT count(*) FROM information_schema.columns
      WHERE table_schema = ''public''
        AND table_name = ''calculation_snapshots''
        AND column_name IN (''invalidated_reason'', ''invalidated_by'',
                            ''invalidated_at'', ''reportability_status'')', 4);

-- Provenance must never cross tenants: the snapshot the log consumes belongs to
-- the same organisation as the log.
SELECT pg_temp.ct02_expect_rows_as('provenance_tenant_consistent',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*)
       FROM public.emissions_logs el
       JOIN public.calculation_snapshots cs ON cs.id = el.snapshot_id
      WHERE el.organization_id <> cs.organization_id', 0);


-- Link the log to its snapshot (the fixture order above requires the snapshot
-- to exist first), then prove the whole chain resolves in ONE query:
--   emission log -> calculation snapshot -> source item / page / file -> factor
UPDATE public.emissions_logs
   SET snapshot_id = 'a5000000-0000-4000-8000-0000000000a1'
 WHERE id = 'a3000000-0000-4000-8000-0000000000a1';

SELECT pg_temp.ct02_expect_rows_as('provenance_log_to_source_chain_resolves',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*)
       FROM public.emissions_logs el
       JOIN public.calculation_snapshots cs ON cs.id = el.snapshot_id
      WHERE el.id = ''a3000000-0000-4000-8000-0000000000a1''
        AND cs.source_item_id IS NOT NULL
        AND cs.source_page IS NOT NULL
        AND cs.source_file = ''ct02/test/a.pdf''
        AND cs.organization_id = el.organization_id
        AND cs.co2e_kg = 268.0', 1);

-- ...and the reverse direction: the snapshot identifies the log that consumed
-- it, so a report figure can be traced back to its source.
SELECT pg_temp.ct02_expect_rows_as('provenance_snapshot_traces_forward_to_log',
    'authenticated', '11111111-0000-4000-8000-00000000000a', 'ct02-owner-a@example.test',
    'SELECT count(*)
       FROM public.calculation_snapshots cs
       JOIN public.emissions_logs el ON el.snapshot_id = cs.id
      WHERE cs.id = ''a5000000-0000-4000-8000-0000000000a1''
        AND el.id = ''a3000000-0000-4000-8000-0000000000a1''', 1);

-- ===========================================================================
-- SUMMARY
-- ===========================================================================
DO $$
BEGIN
    RAISE NOTICE 'CT02_DB_SUITE_COMPLETE — see the assertion lines above';
END $$;

ROLLBACK;

\echo 'CT02_DB_SUITE_END'

