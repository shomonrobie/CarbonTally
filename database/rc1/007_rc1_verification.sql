-- ============================================================================
-- CarbonTally v1.0 RC1 — Post-Migration Verification Suite
-- File 007 of 008 (verification; companion to release notes 008).
--
-- READ-ONLY: every statement is a SELECT or a DO block that only RAISEs
-- NOTICE. Nothing here writes. Safe to run against production as any role
-- with catalogue read access (run as the migration owner / postgres role on
-- Supabase for full visibility of pg_policies and pg_index).
--
-- Run order: after 001–006 have all been applied, BEFORE Gate 4 (RLS
-- penetration matrix) and BEFORE application smoke tests. Each section header
-- states what it proves and the pass criterion. Any FAIL row must be resolved
-- before sign-off (Structural Change Review / Hardening Plan §9 gates).
-- ============================================================================

-- ============================================================================
-- SECTION 1 — RENAMES (001 R1–R3, C4 region retirement)
-- Proves: old object names are gone and new names exist exactly once.
-- PASS: first query returns 0 rows; second returns all 7 expected objects.
-- ============================================================================

-- 1a. Old names must NOT exist (table or column). PASS = empty set.
SELECT 'table' AS object_type, t.table_name AS object_name
  FROM information_schema.tables t
 WHERE t.table_schema = 'public' AND t.table_name = 'defra_conversion_factors'
UNION ALL
SELECT 'column', c.table_name || '.' || c.column_name
  FROM information_schema.columns c
 WHERE c.table_schema = 'public'
   AND ( (c.table_name = 'emissions_logs'            AND c.column_name = 'defra_factor_id')
      OR (c.table_name = 'document_processing_queue' AND c.column_name = 'defra_factor_used')
      OR (c.table_name = 'manual_extraction_items'   AND c.column_name = 'defra_factor_used')
      OR (c.table_name = 'organizations'             AND c.column_name = 'default_defra_version')
      OR (c.table_name = 'emission_factors'          AND c.column_name = 'region') );

-- 1b. New names must exist. PASS = 7 rows.
SELECT 'table' AS object_type, t.table_name AS object_name
  FROM information_schema.tables t
 WHERE t.table_schema = 'public' AND t.table_name = 'emission_factors'
UNION ALL
SELECT 'column', c.table_name || '.' || c.column_name
  FROM information_schema.columns c
 WHERE c.table_schema = 'public'
   AND ( (c.table_name = 'emissions_logs'            AND c.column_name = 'emission_factor_id')
      OR (c.table_name = 'document_processing_queue' AND c.column_name = 'emission_factor_used')
      OR (c.table_name = 'manual_extraction_items'   AND c.column_name = 'emission_factor_used')
      OR (c.table_name = 'organizations'             AND c.column_name = 'default_factor_year')
      OR (c.table_name = 'emission_factors'          AND c.column_name = 'region_deprecated')
      OR (c.table_name = 'facilities'                AND c.column_name = 'eircode') );

-- ============================================================================
-- SECTION 2 — NEW COLUMNS (001 C1–C10)
-- Proves: all 16 approved columns exist with the expected nullability.
-- PASS = 16 rows. postcode must report is_nullable = 'YES' (C1 relaxation);
-- organizations.is_active must be NOT NULL with default true (C2).
-- ============================================================================
SELECT c.table_name, c.column_name, c.data_type, c.is_nullable, c.column_default
  FROM information_schema.columns c
 WHERE c.table_schema = 'public'
   AND ( (c.table_name = 'facilities'             AND c.column_name IN ('eircode','meter_mpan_mprn','postcode'))
      OR (c.table_name = 'organizations'          AND c.column_name IN ('is_active','archived_at'))
      OR (c.table_name = 'consultant_billing'     AND c.column_name = 'currency')
      OR (c.table_name = 'emission_factors'       AND c.column_name IN ('unit','scope','factor_source','factor_set','country'))
      OR (c.table_name = 'emissions_logs'         AND c.column_name IN ('unit','scope'))
      OR (c.table_name = 'customer_documents'     AND c.column_name = 'file_checksum')
      OR (c.table_name = 'suppliers'              AND c.column_name = 'sort_code')
      OR (c.table_name = 'organization_metadata'  AND c.column_name IN ('total_floor_area_sqm','occupied_floor_area_sqm')) )
 ORDER BY c.table_name, c.column_name;

-- C7 widening: file_attachments.file_size must be bigint. PASS = 1 row, bigint.
SELECT c.data_type
  FROM information_schema.columns c
 WHERE c.table_schema = 'public' AND c.table_name = 'file_attachments'
   AND c.column_name = 'file_size' AND c.data_type = 'bigint';

-- ============================================================================
-- SECTION 3 — FOREIGN KEYS (002 F1)
-- Proves: the 11 F1 foreign keys exist and are validated; no orphans on the
-- key relationships.
-- ============================================================================

-- 3a. FK inventory with validation status. PASS = 11 rows, all validated = true.
--     (If any row shows validated = false, the table was locked or orphans
--      blocked VALIDATE — resolve orphans and re-run 002; it is idempotent.)
SELECT con.conname, cl.relname AS child_table, con.convalidated AS validated,
       pg_get_constraintdef(con.oid) AS definition
  FROM pg_constraint con
  JOIN pg_class cl ON cl.oid = con.conrelid
  JOIN pg_namespace n ON n.oid = cl.relnamespace
 WHERE n.nspname = 'public' AND con.contype = 'f'
   AND con.conname IN (
       'emissions_logs_emission_factor_id_fkey',
       'emissions_logs_asset_id_fkey',
       'emissions_logs_unit_fkey',
       'customer_documents_supplier_id_fkey',
       'customer_documents_document_type_id_fkey',
       'customer_documents_org_member_id_fkey',
       'dpq_ai_mapped_facility_id_fkey',
       'dpq_ai_mapped_asset_id_fkey',
       'dpq_ai_mapped_supplier_id_fkey',
       'dpq_emission_factor_used_fkey',
       'messages_conversation_id_fkey')
 ORDER BY con.conname;

-- 3b. NOT VALID constraint audit (all types, whole schema).
-- Proves: nothing was left unvalidated by any migration file. PASS = empty.
SELECT con.conname, cl.relname AS table_name, con.contype
  FROM pg_constraint con
  JOIN pg_class cl ON cl.oid = con.conrelid
  JOIN pg_namespace n ON n.oid = cl.relnamespace
 WHERE n.nspname = 'public' AND con.convalidated = false
 ORDER BY cl.relname, con.conname;

-- 3c. Orphan checks — every count must be 0.
-- Proves: referential integrity holds on the hot paths (factor reference,
-- unit reference, AI-mapping hints, message threading).
SELECT 'emissions_logs.emission_factor_id' AS check_name, count(*) AS orphans
  FROM public.emissions_logs el
 WHERE el.emission_factor_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.emission_factors ef WHERE ef.id = el.emission_factor_id)
UNION ALL
SELECT 'emissions_logs.unit', count(*)
  FROM public.emissions_logs el
 WHERE el.unit IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.units u WHERE u.code = el.unit)
UNION ALL
SELECT 'emissions_logs.asset_id', count(*)
  FROM public.emissions_logs el
 WHERE el.asset_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.assets a WHERE a.id = el.asset_id)
UNION ALL
SELECT 'customer_documents.supplier_id', count(*)
  FROM public.customer_documents cd
 WHERE cd.supplier_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.suppliers s WHERE s.id = cd.supplier_id)
UNION ALL
SELECT 'dpq.emission_factor_used', count(*)
  FROM public.document_processing_queue q
 WHERE q.emission_factor_used IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.emission_factors ef WHERE ef.id = q.emission_factor_used)
UNION ALL
SELECT 'dpq.ai_mapped_facility_id', count(*)
  FROM public.document_processing_queue q
 WHERE q.ai_mapped_facility_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.facilities f WHERE f.id = q.ai_mapped_facility_id)
UNION ALL
SELECT 'messages.conversation_id', count(*)
  FROM public.messages m
 WHERE m.conversation_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.conversations c WHERE c.id = m.conversation_id);

-- 3d. K7 backfilled organization_id — NULL counts on the six hot tables.
-- Proves: the tenancy hole is closed (a NULL org id falls outside every
-- tenant-equality RLS policy). PASS = all six counts 0 (the SET NOT NULL
-- guard in 002 already enforced this; this re-proves it post-hoc).
SELECT 'conversations' AS table_name, count(*) AS null_org_rows FROM public.conversations WHERE organization_id IS NULL
UNION ALL SELECT 'messages',             count(*) FROM public.messages             WHERE organization_id IS NULL
UNION ALL SELECT 'upload_batches',        count(*) FROM public.upload_batches        WHERE organization_id IS NULL
UNION ALL SELECT 'manual_review_queue',   count(*) FROM public.manual_review_queue   WHERE organization_id IS NULL
UNION ALL SELECT 'file_attachments',      count(*) FROM public.file_attachments      WHERE organization_id IS NULL
UNION ALL SELECT 'customer_verifications',count(*) FROM public.customer_verifications WHERE organization_id IS NULL;

-- 3e. K6 — password_reset_tokens.user_id must no longer be unique; token must
-- remain unique. PASS: first query empty, second returns 1 row.
SELECT i.indexrelid::regclass AS still_unique_on_user_id
  FROM pg_index i
  JOIN pg_class ct ON ct.oid = i.indrelid
  JOIN pg_namespace n ON n.oid = ct.relnamespace
 WHERE n.nspname = 'public' AND ct.relname = 'password_reset_tokens'
   AND i.indisunique AND NOT i.indisprimary AND i.indnatts = 1
   AND (SELECT a.attname FROM pg_attribute a
         WHERE a.attrelid = ct.oid AND a.attnum = i.indkey[0]) = 'user_id';

SELECT i.indexrelid::regclass AS token_unique_index
  FROM pg_index i
  JOIN pg_class ct ON ct.oid = i.indrelid
  JOIN pg_namespace n ON n.oid = ct.relnamespace
 WHERE n.nspname = 'public' AND ct.relname = 'password_reset_tokens'
   AND i.indisunique AND i.indnatts = 1
   AND (SELECT a.attname FROM pg_attribute a
         WHERE a.attrelid = ct.oid AND a.attnum = i.indkey[0]) = 'token';

-- ============================================================================
-- SECTION 4 — INDEXES (003 I1–I5 + FK-supporting; 002 K5 unique-backed)
-- ============================================================================

-- 4a. Presence of all 18 indexes from 003. PASS = 18 rows.
SELECT i.indexname, i.tablename
  FROM pg_indexes i
 WHERE i.schemaname = 'public'
   AND i.indexname IN (
       -- I1 tenant composites
       'customer_documents_org_created_idx','emissions_logs_org_start_date_idx',
       'suppliers_org_idx','facilities_org_idx',
       -- I2 queue-claim partials
       'dpq_claim_idx','processing_queue_claim_idx','report_generation_queue_claim_idx',
       -- I3 messaging/notifications
       'messages_conversation_created_idx','conversation_participants_conv_user_idx',
       'notifications_unread_recipient_idx',
       -- I4 GIN
       'consultant_firm_members_client_access_gin',
       -- I5 trigram
       'suppliers_name_trgm_idx','suppliers_vat_number_trgm_idx','organizations_name_trgm_idx',
       -- FK-supporting
       'emissions_logs_emission_factor_id_idx','emissions_logs_asset_id_idx',
       'customer_documents_supplier_id_idx','dpq_customer_document_id_idx')
 ORDER BY i.indexname;

-- 4b. K5 unique-backed indexes from 002. PASS = 7 rows.
SELECT i.indexname, i.tablename, i.indexdef
  FROM pg_indexes i
 WHERE i.schemaname = 'public'
   AND i.indexname IN (
       'organization_members_org_user_uniq','consultant_clients_consultant_org_uniq',
       'usage_tracking_org_month_uniq','report_versions_report_version_uniq',
       'suppliers_org_vat_number_uniq','suppliers_org_company_number_uniq',
       'emission_factors_year_activity_country_uniq')
 ORDER BY i.indexname;

-- 4c. Invalid indexes — a failed CREATE INDEX CONCURRENTLY leaves an invalid
-- index behind. PASS = empty. (Fix: DROP INDEX CONCURRENTLY <name>; re-run 003.)
SELECT c.relname AS invalid_index, ct.relname AS table_name
  FROM pg_index i
  JOIN pg_class c  ON c.oid  = i.indexrelid
  JOIN pg_class ct ON ct.oid = i.indrelid
  JOIN pg_namespace n ON n.oid = ct.relnamespace
 WHERE n.nspname = 'public' AND i.indisvalid = false;

-- 4d. Duplicate/overlapping index scan — same table, same leading column set,
-- both non-partial btree (one is redundant). Review any hits manually; the
-- RC1 families are designed non-overlapping, so PASS = empty for the 18+7
-- RC1 names. (Pre-existing indexes from Supabase migrations may appear here;
-- that is a Gate 1 reconciliation finding, not an RC1 failure.)
SELECT a.indexrelid::regclass AS index_a, b.indexrelid::regclass AS index_b,
       ct.relname AS table_name
  FROM pg_index a
  JOIN pg_index b ON a.indrelid = b.indrelid AND a.indexrelid < b.indexrelid
  JOIN pg_class ct ON ct.oid = a.indrelid
  JOIN pg_namespace n ON n.oid = ct.relnamespace
 WHERE n.nspname = 'public'
   AND a.indisvalid AND b.indisvalid
   AND a.indpred IS NULL AND b.indpred IS NULL          -- both full-table
   AND a.indkey::text = b.indkey::text                  -- identical key columns
 ORDER BY ct.relname;

-- 4e. pg_trgm extension (I5 prerequisite). PASS = 1 row.
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_trgm';

-- ============================================================================
-- SECTION 5 — CHECK CONSTRAINTS (001/002: C1 presence, K1–K4)
-- ============================================================================

-- 5a. Full RC1 CHECK inventory with validation status.
-- PASS = 53 rows, all validated = true:
--   1  facilities_postcode_or_eircode_check
--   5  <table>_country_in_list            (K1)
--   8  <table>_<col>_in_list              (K2 currency)
--   27 <table>_<col>_nonneg               (K3: 2 emissions_logs + 1 factor
--      + 20 quantity/money loop + 4 file-size loop)
--   7  <table>_<col>_range                (K3c)
--   5  <table>_status/queue_status/role_in_list (K4)
SELECT con.conname, cl.relname AS table_name, con.convalidated AS validated,
       pg_get_constraintdef(con.oid) AS definition
  FROM pg_constraint con
  JOIN pg_class cl ON cl.oid = con.conrelid
  JOIN pg_namespace n ON n.oid = cl.relnamespace
 WHERE n.nspname = 'public' AND con.contype = 'c'
   AND ( con.conname = 'facilities_postcode_or_eircode_check'
      OR con.conname ~ '_(country|currency|payment_currency|billing_currency|revenue_currency|default_currency)_in_list$'
      OR con.conname ~ '_(nonneg|range)$'
      OR con.conname IN ('processing_queue_queue_status_in_list',
                         'document_processing_queue_status_in_list',
                         'customer_documents_status_in_list',
                         'organization_members_role_in_list',
                         'customer_subscriptions_status_in_list') )
 ORDER BY cl.relname, con.conname;

-- 5b. Facilities presence CHECK — both NULL must be impossible.
-- PASS = 0 rows (existing data) — the CHECK blocks new violations.
SELECT count(*) AS facilities_both_null
  FROM public.facilities
 WHERE postcode IS NULL AND eircode IS NULL;

-- 5c. K1 country vocabulary — rows outside 'GB'/'IE'. PASS = all zero.
SELECT 'organizations' AS table_name, count(*) AS bad_country FROM public.organizations WHERE country IS NOT NULL AND country NOT IN ('GB','IE')
UNION ALL SELECT 'facilities',          count(*) FROM public.facilities          WHERE country IS NOT NULL AND country NOT IN ('GB','IE')
UNION ALL SELECT 'suppliers',           count(*) FROM public.suppliers           WHERE country IS NOT NULL AND country NOT IN ('GB','IE')
UNION ALL SELECT 'consultant_profiles', count(*) FROM public.consultant_profiles WHERE country IS NOT NULL AND country NOT IN ('GB','IE')
UNION ALL SELECT 'emission_factors',    count(*) FROM public.emission_factors    WHERE country IS NOT NULL AND country NOT IN ('GB','IE');

-- 5d. K2 currency vocabulary — rows outside 'GBP'/'EUR'. PASS = all zero.
SELECT 'organizations.currency' AS col, count(*) AS bad_currency FROM public.organizations WHERE currency IS NOT NULL AND currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'suppliers.payment_currency',             count(*) FROM public.suppliers                 WHERE payment_currency IS NOT NULL AND payment_currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'document_processing_queue.billing_currency', count(*) FROM public.document_processing_queue WHERE billing_currency IS NOT NULL AND billing_currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'customer_subscriptions.currency',        count(*) FROM public.customer_subscriptions    WHERE currency IS NOT NULL AND currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'manual_extraction_batches.currency',     count(*) FROM public.manual_extraction_batches WHERE currency IS NOT NULL AND currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'consultant_profiles.revenue_currency',   count(*) FROM public.consultant_profiles       WHERE revenue_currency IS NOT NULL AND revenue_currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'consultant_billing.currency',            count(*) FROM public.consultant_billing        WHERE currency IS NOT NULL AND currency NOT IN ('GBP','EUR')
UNION ALL SELECT 'system_settings.default_currency',       count(*) FROM public.system_settings           WHERE default_currency IS NOT NULL AND default_currency NOT IN ('GBP','EUR');

-- 5e. Negative/zero-guard violations — K3 nonneg core quantities.
-- PASS = all zero. (Corrections must be positive rows by design; negative
-- values anywhere here mean the staging audit was skipped.)
SELECT 'emissions_logs.raw_quantity' AS col, count(*) AS negative_values FROM public.emissions_logs WHERE raw_quantity < 0
UNION ALL SELECT 'emissions_logs.calculated_kg_co2e',      count(*) FROM public.emissions_logs  WHERE calculated_kg_co2e < 0
UNION ALL SELECT 'emission_factors.co2e_multiplier',       count(*) FROM public.emission_factors WHERE co2e_multiplier < 0
UNION ALL SELECT 'file_attachments.file_size',             count(*) FROM public.file_attachments WHERE file_size < 0
UNION ALL SELECT 'usage_tracking.total_storage_bytes',     count(*) FROM public.usage_tracking   WHERE total_storage_bytes < 0;

-- 5f. K3c confidence/percentage range — outside 0–100. PASS = all zero.
SELECT 'customer_documents.confidence_score' AS col, count(*) AS out_of_range FROM public.customer_documents WHERE confidence_score IS NOT NULL AND (confidence_score < 0 OR confidence_score > 100)
UNION ALL SELECT 'emissions_logs.confidence_score',            count(*) FROM public.emissions_logs            WHERE confidence_score IS NOT NULL AND (confidence_score < 0 OR confidence_score > 100)
UNION ALL SELECT 'document_processing_queue.ai_confidence_score', count(*) FROM public.document_processing_queue WHERE ai_confidence_score IS NOT NULL AND (ai_confidence_score < 0 OR ai_confidence_score > 100)
UNION ALL SELECT 'document_processing_queue.ai_mapping_confidence', count(*) FROM public.document_processing_queue WHERE ai_mapping_confidence IS NOT NULL AND (ai_mapping_confidence < 0 OR ai_mapping_confidence > 100)
UNION ALL SELECT 'organization_metadata.renewable_energy_percentage', count(*) FROM public.organization_metadata WHERE renewable_energy_percentage IS NOT NULL AND (renewable_energy_percentage < 0 OR renewable_energy_percentage > 100)
UNION ALL SELECT 'report_generation_queue.progress_percentage',  count(*) FROM public.report_generation_queue WHERE progress_percentage IS NOT NULL AND (progress_percentage < 0 OR progress_percentage > 100);

-- 5g. K4 status vocabularies — rows outside the approved lists. PASS = all zero.
SELECT 'processing_queue.queue_status' AS col, count(*) AS bad_status FROM public.processing_queue
 WHERE queue_status NOT IN ('pending','assigned','in_progress','on_hold','completed','cancelled')
UNION ALL
SELECT 'document_processing_queue.status', count(*) FROM public.document_processing_queue
 WHERE status NOT IN ('pending','processing','ai_extracted','manual_review','manual_extraction','qc','customer_review','approved','rejected','completed','failed')
UNION ALL
SELECT 'customer_documents.status', count(*) FROM public.customer_documents
 WHERE status NOT IN ('uploaded','pending','processing','processed','manual_review','verified','approved','rejected','failed')
UNION ALL
SELECT 'organization_members.role', count(*) FROM public.organization_members
 WHERE role NOT IN ('owner','admin','member','viewer')
UNION ALL
SELECT 'customer_subscriptions.status', count(*) FROM public.customer_subscriptions
 WHERE status NOT IN ('trialing','active','past_due','paused','cancelled','expired');

-- 5h. NOT NULL tightenings (001 C2; 002 K7/K8). PASS = 13 rows, all 'NO'.
SELECT c.table_name, c.column_name, c.is_nullable
  FROM information_schema.columns c
 WHERE c.table_schema = 'public'
   AND ( (c.table_name = 'organizations' AND c.column_name = 'is_active')
      OR (c.column_name = 'organization_id' AND c.table_name IN
          ('conversations','messages','upload_batches','manual_review_queue','file_attachments','customer_verifications'))
      OR (c.table_name = 'customer_documents' AND c.column_name = 'status')
      OR (c.table_name = 'document_processing_queue' AND c.column_name IN ('status','qc_required','customer_approved'))
      OR (c.table_name = 'processing_queue' AND c.column_name IN ('queue_status','sla_breached')) )
 ORDER BY c.table_name, c.column_name;

-- ============================================================================
-- SECTION 6 — RLS (004)
-- ============================================================================

-- 6a. THE DANGEROUS STATE: RLS enabled but zero policies (table locked to all
-- non-owner roles). PASS = empty.
SELECT t.tablename
  FROM pg_tables t
 WHERE t.schemaname = 'public'
   AND t.rowsecurity = true
   AND NOT EXISTS (SELECT 1 FROM pg_policies p
                    WHERE p.schemaname = 'public' AND p.tablename = t.tablename)
 ORDER BY t.tablename;

-- 6b. Tenant tables WITHOUT RLS enabled (the inverse hole).
-- Every organization_id-bearing table must have RLS on. PASS = empty.
SELECT c.table_name
  FROM information_schema.columns c
 WHERE c.table_schema = 'public' AND c.column_name = 'organization_id'
   AND NOT EXISTS (SELECT 1 FROM pg_tables t
                    WHERE t.schemaname = 'public' AND t.tablename = c.table_name
                      AND t.rowsecurity = true)
 ORDER BY c.table_name;

-- 6c. Policy inventory by table. PASS: each of the 36 Section-1 tenant tables
-- has its four *_tenant_* policies; organizations has 2; users/notifications
-- have 2 each; the 10 reference tables have *_authenticated_read. Expected
-- totals (upper bound, if none pre-existed): 36×4 + 2 + 4 + 10 = 160.
-- Pre-existing policies under other names are additive and acceptable —
-- the penetration matrix (Gate 4) validates the union.
SELECT p.tablename, count(*) AS policy_count,
       string_agg(p.policyname, ', ' ORDER BY p.policyname) AS policies
  FROM pg_policies p
 WHERE p.schemaname = 'public'
 GROUP BY p.tablename
 ORDER BY p.tablename;

-- 6d. RLS helper functions present with correct hardening.
-- PASS = 2 rows, both security definer. (Created in 004, not 005.)
SELECT p.proname, p.prosecdef AS security_definer, p.proconfig AS settings
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname = 'public' AND p.proname IN ('is_org_member','is_org_active');

-- ============================================================================
-- SECTION 7 — TRIGGERS (006) + FUNCTIONS (005)
-- ============================================================================

-- 7a. Coverage gap: mutable tables with updated_at but NO maintenance trigger.
-- The six excluded append-only logs are intentional and filtered out.
-- PASS = empty (tables skipped by the DO guard because they lack updated_at
-- will not appear here; cross-check against the 006 skip NOTICEs).
SELECT c.table_name
  FROM information_schema.columns c
 WHERE c.table_schema = 'public' AND c.column_name = 'updated_at'
   AND c.table_name NOT IN ('activity_logs','document_activity_log','email_logs',
                            'processing_logs','user_activity_log','review_audit_trail')
   AND NOT EXISTS (SELECT 1 FROM information_schema.triggers tr
                    WHERE tr.event_object_schema = 'public'
                      AND tr.event_object_table = c.table_name
                      AND tr.trigger_name = 'trg_set_updated_at_' || c.table_name)
 ORDER BY c.table_name;

-- 7b. Trigger inventory. PASS = up to 76 rows named trg_set_updated_at_<table>
-- (fewer where a candidate table was missing or has no updated_at — compare
-- with the NOTICE output captured when 006 ran).
SELECT tr.event_object_table AS table_name, tr.trigger_name, tr.action_timing, tr.event_manipulation
  FROM information_schema.triggers tr
 WHERE tr.trigger_schema = 'public'
   AND tr.trigger_name LIKE 'trg\_set\_updated\_at\_%'
 ORDER BY tr.event_object_table;

-- 7c. Excluded append-only logs must NOT have the maintenance trigger.
-- PASS = empty.
SELECT tr.event_object_table AS table_name, tr.trigger_name
  FROM information_schema.triggers tr
 WHERE tr.trigger_schema = 'public'
   AND tr.event_object_table IN ('activity_logs','document_activity_log','email_logs',
                                 'processing_logs','user_activity_log','review_audit_trail')
   AND tr.trigger_name LIKE 'trg\_set\_updated\_at\_%';

-- 7d. Functions from 004/005 present. PASS = 4 rows.
SELECT p.proname, p.prosecdef AS security_definer
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname = 'public'
   AND p.proname IN ('set_updated_at','anonymise_user','is_org_member','is_org_active')
 ORDER BY p.proname;

-- 7e. Views inventory. This migration adds NO views — confirm the catalogue
-- shows none created by RC1 (any views present are pre-existing; record them
-- for Gate 1 reconciliation). Informational; no fixed pass count.
SELECT table_name AS view_name FROM information_schema.views
 WHERE table_schema = 'public' ORDER BY table_name;

-- ============================================================================
-- SECTION 8 — IRELAND-BETA READINESS
-- Proves the four v1.1 enablers shipped by RC1 are in place.
-- ============================================================================

-- 8a. facilities.eircode present and postcode nullable. PASS = 2 rows.
SELECT c.column_name, c.is_nullable
  FROM information_schema.columns c
 WHERE c.table_schema = 'public' AND c.table_name = 'facilities'
   AND c.column_name IN ('eircode','postcode')
 ORDER BY c.column_name;

-- 8b. emission_factors provenance columns. PASS = 5 rows.
SELECT c.column_name, c.data_type, c.is_nullable
  FROM information_schema.columns c
 WHERE c.table_schema = 'public' AND c.table_name = 'emission_factors'
   AND c.column_name IN ('country','unit','scope','factor_source','factor_set')
 ORDER BY c.column_name;

-- 8c. region_deprecated status: present (retired, non-destructive) and the
-- live `region` column gone. PASS: 1 row; and Section 1a already proved
-- `region` absent. Data check: no query should read region_deprecated.
SELECT c.column_name, c.is_nullable
  FROM information_schema.columns c
 WHERE c.table_schema = 'public' AND c.table_name = 'emission_factors'
   AND c.column_name = 'region_deprecated';

-- 8d. C4 backfill sanity: no NULL country/factor_source on existing factors.
-- PASS = all zero (unit/scope may legitimately be NULL pending the factor
-- data audit — that is a data task, not a structural failure).
SELECT 'country' AS col, count(*) AS nulls FROM public.emission_factors WHERE country IS NULL
UNION ALL SELECT 'factor_source', count(*) FROM public.emission_factors WHERE factor_source IS NULL
UNION ALL SELECT 'factor_set',    count(*) FROM public.emission_factors WHERE factor_set IS NULL;

-- ============================================================================
-- SECTION 9 — DATA PRESERVATION (row counts before/after)
-- RC1 is additive plus renames plus seed-scale backfills: NO table or row is
-- deleted by any file (K6 drops a constraint, not rows). Row counts on every
-- table must be identical before and after the migration, with the sole
-- legitimate exception of rows deliberately assigned/deleted by the staging
-- audit (Gate 2) before 002's K7 guard.
--
-- TEMPLATE — run BEFORE migration, save output; re-run AFTER and diff:
--
--   SELECT c.relname AS table_name, c.reltuples::bigint AS estimate   -- fast
--     FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
--    WHERE n.nspname = 'public' AND c.relkind = 'r'
--    ORDER BY c.relname;
--
-- Exact-count variant for the K7 six (small tables — cheap):
--   SELECT 'conversations' t, count(*) FROM public.conversations
--   UNION ALL SELECT 'messages', count(*) FROM public.messages
--   UNION ALL SELECT 'upload_batches', count(*) FROM public.upload_batches
--   UNION ALL SELECT 'manual_review_queue', count(*) FROM public.manual_review_queue
--   UNION ALL SELECT 'file_attachments', count(*) FROM public.file_attachments
--   UNION ALL SELECT 'customer_verifications', count(*) FROM public.customer_verifications;
-- ============================================================================

-- ============================================================================
-- SECTION 10 — ONE-LINE SUMMARY (DO block; raise NOTICE per gate)
-- A single pass/fail sweep over the hard checks above. PASS = every NOTICE
-- reads OK; any FAIL line names the section to drill into.
-- ============================================================================
DO $$
DECLARE n bigint;
BEGIN
    SELECT count(*) INTO n FROM pg_tables t
     WHERE t.schemaname='public' AND t.rowsecurity
       AND NOT EXISTS (SELECT 1 FROM pg_policies p
                        WHERE p.schemaname='public' AND p.tablename=t.tablename);
    RAISE NOTICE '% RLS enabled-no-policy tables (expect 0)', n;

    SELECT count(*) INTO n FROM pg_index i
      JOIN pg_class c ON c.oid=i.indexrelid
      JOIN pg_class ct ON ct.oid=i.indrelid
      JOIN pg_namespace ns ON ns.oid=ct.relnamespace
     WHERE ns.nspname='public' AND NOT i.indisvalid;
    RAISE NOTICE '% invalid indexes (expect 0)', n;

    SELECT count(*) INTO n FROM pg_constraint con
      JOIN pg_class cl ON cl.oid=con.conrelid
      JOIN pg_namespace ns ON ns.oid=cl.relnamespace
     WHERE ns.nspname='public' AND NOT con.convalidated;
    RAISE NOTICE '% NOT VALID constraints (expect 0)', n;

    SELECT count(*) INTO n FROM pg_indexes i
     WHERE i.schemaname='public' AND i.indexname IN (
       'customer_documents_org_created_idx','emissions_logs_org_start_date_idx',
       'suppliers_org_idx','facilities_org_idx','dpq_claim_idx',
       'processing_queue_claim_idx','report_generation_queue_claim_idx',
       'messages_conversation_created_idx','conversation_participants_conv_user_idx',
       'notifications_unread_recipient_idx','consultant_firm_members_client_access_gin',
       'suppliers_name_trgm_idx','suppliers_vat_number_trgm_idx','organizations_name_trgm_idx',
       'emissions_logs_emission_factor_id_idx','emissions_logs_asset_id_idx',
       'customer_documents_supplier_id_idx','dpq_customer_document_id_idx');
    RAISE NOTICE '% of 18 expected 003 indexes present', n;

    SELECT count(*) INTO n FROM information_schema.tables
     WHERE table_schema='public' AND table_name='defra_conversion_factors';
    RAISE NOTICE '% legacy defra_conversion_factors tables (expect 0)', n;

    SELECT count(*) INTO n FROM information_schema.columns c
     WHERE c.table_schema='public' AND c.column_name='updated_at'
       AND c.table_name NOT IN ('activity_logs','document_activity_log','email_logs',
                                'processing_logs','user_activity_log','review_audit_trail')
       AND NOT EXISTS (SELECT 1 FROM information_schema.triggers tr
                        WHERE tr.event_object_schema='public'
                          AND tr.event_object_table=c.table_name
                          AND tr.trigger_name='trg_set_updated_at_'||c.table_name);
    RAISE NOTICE '% updated_at tables missing maintenance trigger (expect 0)', n;
END $$;

-- ============================================================================
-- End of 007_rc1_verification.sql — read-only. Any non-empty FAIL set blocks
-- RC1 sign-off pending resolution (see 008_RC1_RELEASE_NOTES.md §Rollback for
-- the per-file remediation path).
-- ============================================================================
