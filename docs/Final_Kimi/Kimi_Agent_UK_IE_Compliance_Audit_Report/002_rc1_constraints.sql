-- ============================================================================
-- CarbonTally v1.0 RC1 — Production Hardening Migration
-- File 002 of 008: Constraints (C1 presence CHECK, K1–K8, F1/F2 foreign keys)
-- Source of truth: CarbonTally_v1.0_Structural_Change_Review.md, §2 C1 and
-- §5/§6 APPROVE items only.
--
-- FROZEN DECISION — NO FORMAT CHECKS (K9, REJECT):
--   No regex/format CHECK constraints are created in this file (UK company
--   number, UK VAT, MOD97, postcode, Eircode routing keys, phone, email).
--   Format validation lives exclusively in the API validation pack. The
--   database enforces exactly four validation shapes: IN-lists, ranges,
--   presence, uniqueness. (Structural Change Review §5 K9, REJECT.)
--
-- PATTERN: all CHECK/UNIQUE constraints on populated tables are added
-- NOT VALID and then VALIDATE CONSTRAINTd, so existing rows are never
-- scanned under a write-blocking lock. Each VALIDATE is preceded by a
-- value-mapping/audit statement. Run the staging data audit (NULL counts,
-- duplicate sweeps, value mapping) BEFORE this file; the mapping UPDATEs
-- below cover the known seed variants.
-- ============================================================================

BEGIN;

-- ============================================================================
-- C1 companion — facilities presence CHECK
-- (Structural Change Review §2 C1, APPROVE)
-- "At least one of postcode/eircode present" — the review's preferred simple
-- form. The per-country conditional rule (Eircode required when country='IE',
-- postcode when 'GB') is owned by the API layer because facilities.country is
-- itself nullable.
-- ROLLBACK: ALTER TABLE public.facilities DROP CONSTRAINT IF EXISTS facilities_postcode_or_eircode_check;
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'facilities_postcode_or_eircode_check') THEN
        ALTER TABLE public.facilities
            ADD CONSTRAINT facilities_postcode_or_eircode_check
            CHECK (postcode IS NOT NULL OR eircode IS NOT NULL) NOT VALID;
    END IF;
    ALTER TABLE public.facilities VALIDATE CONSTRAINT facilities_postcode_or_eircode_check;
END $$;

-- ============================================================================
-- K1 — country IN ('GB','IE')
-- (Structural Change Review §5 K1, APPROVE)
-- Constrains the EXISTING country columns on organizations, facilities,
-- suppliers, consultant_profiles, plus the new emission_factors.country (C4).
-- No country_code column is added — that was explicitly REJECTED (second
-- source of truth).
-- Value mapping first: known seed variants mapped to 'GB'; anything else
-- non-conforming must be resolved by the staging audit before VALIDATE.
-- ROLLBACK (per table): ALTER TABLE <t> DROP CONSTRAINT IF EXISTS <t>_country_in_list;
-- ============================================================================
UPDATE public.organizations       SET country = 'GB' WHERE country IN ('UK','United Kingdom','Great Britain','England','Scotland','Wales','Northern Ireland','uk','gb');
UPDATE public.organizations       SET country = 'IE' WHERE country IN ('Ireland','Republic of Ireland','IRL','ie');
UPDATE public.facilities          SET country = 'GB' WHERE country IN ('UK','United Kingdom','Great Britain','England','Scotland','Wales','Northern Ireland','uk','gb');
UPDATE public.facilities          SET country = 'IE' WHERE country IN ('Ireland','Republic of Ireland','IRL','ie');
UPDATE public.suppliers           SET country = 'GB' WHERE country IN ('UK','United Kingdom','Great Britain','England','Scotland','Wales','Northern Ireland','uk','gb');
UPDATE public.suppliers           SET country = 'IE' WHERE country IN ('Ireland','Republic of Ireland','IRL','ie');
UPDATE public.consultant_profiles SET country = 'GB' WHERE country IN ('UK','United Kingdom','Great Britain','England','Scotland','Wales','Northern Ireland','uk','gb');
UPDATE public.consultant_profiles SET country = 'IE' WHERE country IN ('Ireland','Republic of Ireland','IRL','ie');

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['organizations','facilities','suppliers','consultant_profiles','emission_factors'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = t || '_country_in_list') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (country IN (''GB'',''IE'')) NOT VALID', t, t || '_country_in_list');
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I', t, t || '_country_in_list');
    END LOOP;
END $$;

-- ============================================================================
-- K2 — currency IN ('GBP','EUR') on the seven currency columns +
--      system_settings.default_currency
-- (Structural Change Review §5 K2, APPROVE; consultant_billing.currency is the
-- C3 column.) EUR defaulting for country='IE' is application-layer work.
-- ROLLBACK (per table): ALTER TABLE <t> DROP CONSTRAINT IF EXISTS <t>_<col>_in_list;
-- ============================================================================
UPDATE public.organizations              SET currency = 'GBP' WHERE currency IN ('£','gbp','GBP ') OR upper(currency) = 'POUND';
UPDATE public.suppliers                  SET payment_currency = 'GBP' WHERE payment_currency IN ('£','gbp');
UPDATE public.document_processing_queue  SET billing_currency = 'GBP' WHERE billing_currency IN ('£','gbp');
UPDATE public.customer_subscriptions     SET currency = 'GBP' WHERE currency IN ('£','gbp');
UPDATE public.manual_extraction_batches  SET currency = 'GBP' WHERE currency IN ('£','gbp');
UPDATE public.consultant_profiles        SET revenue_currency = 'GBP' WHERE revenue_currency IN ('£','gbp');

DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN
        SELECT * FROM (VALUES
            ('organizations','currency'),
            ('suppliers','payment_currency'),
            ('document_processing_queue','billing_currency'),
            ('customer_subscriptions','currency'),
            ('manual_extraction_batches','currency'),
            ('consultant_profiles','revenue_currency'),
            ('consultant_billing','currency'),
            ('system_settings','default_currency')
        ) AS v(tbl, col)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_in_list') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I IN (''GBP'',''EUR'')) NOT VALID',
                           pair.tbl, pair.tbl || '_' || pair.col || '_in_list', pair.col);
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I',
                       pair.tbl, pair.tbl || '_' || pair.col || '_in_list');
    END LOOP;
END $$;

-- ============================================================================
-- K3 — Range CHECKs
-- (Structural Change Review §5 K3, APPROVE)
-- (a) ≥ 0 on emission quantities, factors and supplier per-scope values;
-- (b) ≥ 0 on money/usage counters (same batch, per the review);
-- (c) 0–100 on percentage columns and confidence scores (scale assumption:
--     confidence scores are stored 0–100; if the staging audit finds 0–1
--     storage, tighten the bounds before VALIDATE — NOT VALID means existing
--     rows do not block);
-- (d) file_attachments.file_size ≥ 0 (C7 companion, per lead instruction).
-- Corrections use positive quantities with a sign/flag — never negative
-- adjustment lines (design decision confirmed in the review).
-- ROLLBACK: drop each named constraint (names listed inline).
-- ============================================================================

-- (a) Core emission quantities & factors -------------------------------------
DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN
        SELECT * FROM (VALUES
            ('emissions_logs','raw_quantity'),
            ('emissions_logs','calculated_kg_co2e'),
            ('emission_factors','co2e_multiplier')
        ) AS v(tbl, col)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_nonneg') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I >= 0) NOT VALID',
                           pair.tbl, pair.tbl || '_' || pair.col || '_nonneg', pair.col);
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I',
                       pair.tbl, pair.tbl || '_' || pair.col || '_nonneg');
    END LOOP;
END $$;

DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN
        SELECT * FROM (VALUES
            ('suppliers','annual_emissions_scope1'), ('suppliers','annual_emissions_scope2'),
            ('suppliers','annual_emissions_scope3'), ('suppliers','emission_factor_scope1'),
            ('suppliers','emission_factor_scope2'),  ('suppliers','emission_factor_scope3'),
            ('supplier_categories','default_emission_factor'),
            -- (b) money / usage counters -------------------------------------
            ('usage_tracking','ai_files_processed'), ('usage_tracking','batch_files_uploaded'),
            ('usage_tracking','manual_pages_extracted'), ('usage_tracking','reports_generated'),
            ('usage_tracking','total_storage_bytes'),
            ('customer_subscriptions','ai_extraction_used'),
            ('customer_subscriptions','manual_extraction_pages_used'),
            ('customer_subscriptions','price_per_ai_extra'),
            ('customer_subscriptions','price_per_manual_page'),
            ('consultant_billing','auto_extraction_used'),
            ('consultant_billing','manual_extraction_used'),
            ('consultant_billing','auto_extraction_price'),
            ('consultant_billing','manual_extraction_price')
        ) AS v(tbl, col)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_nonneg') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I >= 0) NOT VALID',
                           pair.tbl, pair.tbl || '_' || pair.col || '_nonneg', pair.col);
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I',
                       pair.tbl, pair.tbl || '_' || pair.col || '_nonneg');
    END LOOP;
END $$;

-- (c) Percentages 0–100 and confidence scores --------------------------------
DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN
        SELECT * FROM (VALUES
            ('organization_metadata','renewable_energy_percentage'),
            ('organization_metadata','carbon_offset_percentage'),
            ('report_generation_queue','progress_percentage'),
            ('customer_documents','confidence_score'),
            ('emissions_logs','confidence_score'),
            ('document_processing_queue','ai_confidence_score'),
            ('document_processing_queue','ai_mapping_confidence')
        ) AS v(tbl, col)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_range') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I IS NULL OR (%I >= 0 AND %I <= 100)) NOT VALID',
                           pair.tbl, pair.tbl || '_' || pair.col || '_range',
                           pair.col, pair.col, pair.col);
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I',
                       pair.tbl, pair.tbl || '_' || pair.col || '_range');
    END LOOP;
END $$;

-- (d) File sizes ≥ 0 (C7 companion + int8 peer columns) -----------------------
DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN
        SELECT * FROM (VALUES
            ('file_attachments','file_size'),
            ('document_processing_queue','file_size_bytes'),
            ('processing_queue','file_size_bytes'),
            ('report_generation_queue','final_report_size_bytes')
        ) AS v(tbl, col)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_nonneg') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I >= 0) NOT VALID',
                           pair.tbl, pair.tbl || '_' || pair.col || '_nonneg', pair.col);
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I',
                       pair.tbl, pair.tbl || '_' || pair.col || '_nonneg');
    END LOOP;
END $$;

-- ============================================================================
-- K4 — Status/role CHECK value lists on the five approved columns
-- (Structural Change Review §5 K4, APPROVE)
-- CHECKs chosen over PG enums deliberately (enums are migration-hostile).
-- IMPORTANT: the lists below are scoped from the application enumerations as
-- currently understood. The staging value-mapping audit MUST reconcile each
-- list against the application's centralised status constants before
-- VALIDATE; adjust the list (not the data) for any legitimate state missing.
-- The remaining ~20 free-text statuses defer to v1.1 per the review.
-- ROLLBACK: drop each named constraint.
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'processing_queue_queue_status_in_list') THEN
        ALTER TABLE public.processing_queue
            ADD CONSTRAINT processing_queue_queue_status_in_list
            CHECK (queue_status IN ('pending','assigned','in_progress','on_hold','completed','cancelled')) NOT VALID;
    END IF;
    ALTER TABLE public.processing_queue VALIDATE CONSTRAINT processing_queue_queue_status_in_list;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'document_processing_queue_status_in_list') THEN
        ALTER TABLE public.document_processing_queue
            ADD CONSTRAINT document_processing_queue_status_in_list
            CHECK (status IN ('pending','processing','ai_extracted','manual_review','manual_extraction','qc','customer_review','approved','rejected','completed','failed')) NOT VALID;
    END IF;
    ALTER TABLE public.document_processing_queue VALIDATE CONSTRAINT document_processing_queue_status_in_list;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'customer_documents_status_in_list') THEN
        ALTER TABLE public.customer_documents
            ADD CONSTRAINT customer_documents_status_in_list
            CHECK (status IN ('uploaded','pending','processing','processed','manual_review','verified','approved','rejected','failed')) NOT VALID;
    END IF;
    ALTER TABLE public.customer_documents VALIDATE CONSTRAINT customer_documents_status_in_list;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'organization_members_role_in_list') THEN
        ALTER TABLE public.organization_members
            ADD CONSTRAINT organization_members_role_in_list
            CHECK (role IN ('owner','admin','member','viewer')) NOT VALID;
    END IF;
    ALTER TABLE public.organization_members VALIDATE CONSTRAINT organization_members_role_in_list;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'customer_subscriptions_status_in_list') THEN
        ALTER TABLE public.customer_subscriptions
            ADD CONSTRAINT customer_subscriptions_status_in_list
            CHECK (status IN ('trialing','active','past_due','paused','cancelled','expired')) NOT VALID;
    END IF;
    ALTER TABLE public.customer_subscriptions VALIDATE CONSTRAINT customer_subscriptions_status_in_list;
END $$;

-- ============================================================================
-- K5 — Uniqueness set
-- (Structural Change Review §5 K5, APPROVE)
-- Seven constraints. The staging dedupe sweep gates each one; partial UNIQUEs
-- avoid penalising NULL-heavy legitimate supplier rows. A name-unique on
-- suppliers is deliberately NOT created (legitimate same-name suppliers;
-- the I5 trigram indexes are the soft control).
-- Implemented as UNIQUE INDEXES (idempotent via IF NOT EXISTS); each backing
-- index also serves its lookup path (counted here, not in the index file).
-- ROLLBACK: DROP INDEX IF EXISTS <name>;
-- ============================================================================
CREATE UNIQUE INDEX IF NOT EXISTS organization_members_org_user_uniq
    ON public.organization_members (organization_id, user_id);

CREATE UNIQUE INDEX IF NOT EXISTS consultant_clients_consultant_org_uniq
    ON public.consultant_clients (consultant_id, organization_id);

CREATE UNIQUE INDEX IF NOT EXISTS usage_tracking_org_month_uniq
    ON public.usage_tracking (organization_id, usage_month);

CREATE UNIQUE INDEX IF NOT EXISTS report_versions_report_version_uniq
    ON public.report_versions (report_id, version_number);

CREATE UNIQUE INDEX IF NOT EXISTS suppliers_org_vat_number_uniq
    ON public.suppliers (organization_id, vat_number)
    WHERE vat_number IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS suppliers_org_company_number_uniq
    ON public.suppliers (organization_id, company_number)
    WHERE company_number IS NOT NULL;

-- Factor uniqueness on the natural key (post-C4): prevents silently
-- double-counted factors from duplicate (year, activity, jurisdiction) rows.
CREATE UNIQUE INDEX IF NOT EXISTS emission_factors_year_activity_country_uniq
    ON public.emission_factors (reporting_year, activity_type, country);

-- ============================================================================
-- K6 — Drop UNIQUE on password_reset_tokens.user_id (keep UNIQUE on token)
-- (Structural Change Review §5 K6, APPROVE — closes the unauthenticated
-- reset-DoS; latest-valid-wins semantics in the application.)
-- Relaxes a constraint: safe direction. The backing index name is the PG
-- default <table>_<col>_key; a DO block finds it defensively by definition.
-- ROLLBACK:
--   CREATE UNIQUE INDEX password_reset_tokens_user_id_key
--       ON public.password_reset_tokens (user_id);
-- ============================================================================
DO $$
DECLARE idx RECORD;
BEGIN
    FOR idx IN
        SELECT ci.relname AS index_name
          FROM pg_index i
          JOIN pg_class ci ON ci.oid = i.indexrelid
          JOIN pg_class ct ON ct.oid = i.indrelid
          JOIN pg_namespace n ON n.oid = ct.relnamespace
         WHERE n.nspname = 'public'
           AND ct.relname = 'password_reset_tokens'
           AND i.indisunique AND NOT i.indisprimary
           AND i.indnatts = 1
           AND (SELECT a.attname FROM pg_attribute a
                 WHERE a.attrelid = ct.oid AND a.attnum = i.indkey[0]) = 'user_id'
    LOOP
        -- If the index backs a UNIQUE constraint (the usual case for a
        -- column-level Unique), drop the constraint; otherwise drop the index.
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conindid =
                   (SELECT oid FROM pg_class WHERE relname = idx.index_name
                      AND relnamespace = 'public'::regnamespace)) THEN
            EXECUTE format('ALTER TABLE public.password_reset_tokens DROP CONSTRAINT %I', idx.index_name);
            RAISE NOTICE 'K6: dropped UNIQUE constraint % on password_reset_tokens(user_id)', idx.index_name;
        ELSE
            EXECUTE format('DROP INDEX public.%I', idx.index_name);
            RAISE NOTICE 'K6: dropped UNIQUE index % on password_reset_tokens(user_id)', idx.index_name;
        END IF;
    END LOOP;
END $$;
-- password_reset_tokens.token UNIQUE is untouched.



-- ============================================================================
-- K7 — Backfill then NOT NULL organization_id on six hot tenant tables
-- (Structural Change Review §5 K7, APPROVE — tenancy-hole closure: a NULL
-- organization_id row falls outside every tenant-equality RLS policy.)
-- Tables: conversations, messages, upload_batches, manual_review_queue,
-- file_attachments, customer_verifications (all confirmed nullable in dump).
-- Backfill from parent rows where derivable; the SET NOT NULL step is guarded
-- — it raises an exception listing any rows that could not be backfilled, so
-- the migration fails safe rather than silently rejecting unknown data.
-- MANDATORY: take a pre-migration snapshot of these six tables (un-backfilling
-- is impossible — review attribute 5).
-- ROLLBACK (per table):
--   ALTER TABLE public.<t> ALTER COLUMN organization_id DROP NOT NULL;
-- ============================================================================

-- messages ← conversations via conversation_id
UPDATE public.messages m
   SET organization_id = c.organization_id
  FROM public.conversations c
 WHERE m.conversation_id = c.id
   AND m.organization_id IS NULL;

-- file_attachments ← conversations, then ← messages
UPDATE public.file_attachments fa
   SET organization_id = c.organization_id
  FROM public.conversations c
 WHERE fa.conversation_id = c.id
   AND fa.organization_id IS NULL;
UPDATE public.file_attachments fa
   SET organization_id = m.organization_id
  FROM public.messages m
 WHERE fa.message_id = m.id
   AND fa.organization_id IS NULL;

-- customer_verifications ← customer_documents
UPDATE public.customer_verifications cv
   SET organization_id = cd.organization_id
  FROM public.customer_documents cd
 WHERE cv.customer_document_id = cd.id
   AND cv.organization_id IS NULL;

-- manual_review_queue ← customer_documents
UPDATE public.manual_review_queue mrq
   SET organization_id = cd.organization_id
  FROM public.customer_documents cd
 WHERE mrq.customer_document_id = cd.id
   AND mrq.organization_id IS NULL;

-- conversations and upload_batches have no parent to derive from: any NULLs
-- here are orphaned rows for the staging audit to resolve (assign or delete)
-- BEFORE this migration runs; the guard below enforces zero-NULL.

DO $$
DECLARE t text; n bigint;
BEGIN
    FOREACH t IN ARRAY ARRAY['conversations','messages','upload_batches',
                             'manual_review_queue','file_attachments',
                             'customer_verifications'] LOOP
        EXECUTE format('SELECT count(*) FROM public.%I WHERE organization_id IS NULL', t) INTO n;
        IF n > 0 THEN
            RAISE EXCEPTION 'K7: % rows in public.% still have NULL organization_id after backfill — resolve via staging audit before tightening', n, t;
        END IF;
        EXECUTE format('ALTER TABLE public.%I ALTER COLUMN organization_id SET NOT NULL', t);
        RAISE NOTICE 'K7: %.organization_id set NOT NULL', t;
    END LOOP;
END $$;

-- ============================================================================
-- K8 — NOT NULL + DEFAULT on hot booleans/processing columns (scoped subset)
-- (Structural Change Review §5 K8, APPROVE — two-state booleans on the paths
-- that branch on them; the broad ~80-column sweep stays deferred to v1.1.)
-- Backfill-then-constrain per column; NULL→false for flags, NULL→'pending'
-- style defaults for statuses (aligned with the K4 lists above).
-- organizations.is_active was fully handled in 001 (C2) and is not repeated.
-- ROLLBACK (per column):
--   ALTER TABLE public.<t> ALTER COLUMN <c> DROP NOT NULL;
--   ALTER TABLE public.<t> ALTER COLUMN <c> DROP DEFAULT;
-- ============================================================================

-- customer_documents.status — NULL → 'uploaded' (rows exist ⇒ upload happened)
UPDATE public.customer_documents SET status = 'uploaded' WHERE status IS NULL;
ALTER TABLE public.customer_documents
    ALTER COLUMN status SET DEFAULT 'uploaded',
    ALTER COLUMN status SET NOT NULL;

-- document_processing_queue: status / qc_required / customer_approved
UPDATE public.document_processing_queue SET status = 'pending' WHERE status IS NULL;
UPDATE public.document_processing_queue SET qc_required = false WHERE qc_required IS NULL;
UPDATE public.document_processing_queue SET customer_approved = false WHERE customer_approved IS NULL;
ALTER TABLE public.document_processing_queue
    ALTER COLUMN status SET DEFAULT 'pending',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN qc_required SET DEFAULT false,
    ALTER COLUMN qc_required SET NOT NULL,
    ALTER COLUMN customer_approved SET DEFAULT false,
    ALTER COLUMN customer_approved SET NOT NULL;

-- processing_queue: queue_status / sla_breached
UPDATE public.processing_queue SET queue_status = 'pending' WHERE queue_status IS NULL;
UPDATE public.processing_queue SET sla_breached = false WHERE sla_breached IS NULL;
ALTER TABLE public.processing_queue
    ALTER COLUMN queue_status SET DEFAULT 'pending',
    ALTER COLUMN queue_status SET NOT NULL,
    ALTER COLUMN sla_breached SET DEFAULT false,
    ALTER COLUMN sla_breached SET NOT NULL;

-- ============================================================================
-- F1 — Verify-first FK inventory; add missing FKs implied by the dump
-- (Structural Change Review §6 F1, APPROVE as verification gate with
-- conditional remediation.)
-- The dump shows NO foreign keys, so absence cannot be confirmed from it:
-- every add below is guarded on pg_constraint — if the migration layer already
-- enforces the relationship, the block is a no-op ("verify", per the review);
-- only genuinely unenforced relationships gain a FK ("conditional remediation").
-- All adds are NOT VALID + VALIDATE (no table lock over existing rows).
-- Orphan rows block VALIDATE — that discovery is the point of the gate;
-- clean up orphans in the staging audit, then re-run (idempotent).
-- Prioritised set per the review: factor reference, AI-mapping columns,
-- asset/document/supplier references, messages.conversation_id, and the C5
-- unit FK. report_versions.report_id is intentionally omitted: the dump
-- contains no `reports` parent table — flag for the F1 inspection report.
-- ON DELETE: NO ACTION (database default ≈ RESTRICT-at-statement-end) on the
-- emissions/audit-feeding paths per F2's posture; SET NULL only where the
-- child row remains meaningful without the reference (AI-mapping hints,
-- optional attributions).
-- ROLLBACK (per FK): ALTER TABLE public.<t> DROP CONSTRAINT IF EXISTS <name>;
-- ============================================================================
DO $$
DECLARE fk RECORD;
BEGIN
    FOR fk IN
        SELECT * FROM (VALUES
            -- name                                        child table                    child column           parent table          parent col  delete rule
            ('emissions_logs_emission_factor_id_fkey',     'emissions_logs',             'emission_factor_id',  'emission_factors',   'id',   'NO ACTION'),
            ('emissions_logs_asset_id_fkey',               'emissions_logs',             'asset_id',            'assets',             'id',   'NO ACTION'),
            ('emissions_logs_unit_fkey',                   'emissions_logs',             'unit',                'units',              'code', 'NO ACTION'),
            ('customer_documents_supplier_id_fkey',        'customer_documents',         'supplier_id',         'suppliers',          'id',   'NO ACTION'),
            ('customer_documents_document_type_id_fkey',   'customer_documents',         'document_type_id',    'document_types',     'id',   'NO ACTION'),
            ('customer_documents_org_member_id_fkey',      'customer_documents',         'organization_member_id','organization_members','id','NO ACTION'),
            ('dpq_ai_mapped_facility_id_fkey',             'document_processing_queue',  'ai_mapped_facility_id','facilities',         'id',   'SET NULL'),
            ('dpq_ai_mapped_asset_id_fkey',                'document_processing_queue',  'ai_mapped_asset_id',  'assets',             'id',   'SET NULL'),
            ('dpq_ai_mapped_supplier_id_fkey',             'document_processing_queue',  'ai_mapped_supplier_id','suppliers',          'id',   'SET NULL'),
            ('dpq_emission_factor_used_fkey',              'document_processing_queue',  'emission_factor_used','emission_factors',   'id',   'NO ACTION'),
            ('messages_conversation_id_fkey',              'messages',                   'conversation_id',     'conversations',      'id',   'NO ACTION')
        ) AS v(conname, child, childcol, parent, parentcol, ondel)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = fk.conname) THEN
            EXECUTE format(
                'ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES public.%I (%I) ON DELETE %s NOT VALID',
                fk.child, fk.conname, fk.childcol, fk.parent, fk.parentcol, fk.ondel);
            RAISE NOTICE 'F1: added FK % (remediation — was unenforced)', fk.conname;
        ELSE
            RAISE NOTICE 'F1: FK % already present (verify-first: no-op)', fk.conname;
        END IF;
        EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I', fk.child, fk.conname);
    END LOOP;
END $$;

-- ============================================================================
-- F2 — ON DELETE behaviour corrections
-- (Structural Change Review §6 F2, APPROVE — conditional on F1's inspection;
-- no speculative rewrites of behaviour that may already be correct.)
-- The dump exposes no ON DELETE actions, so there is nothing to correct
-- speculatively here. Posture implemented:
--   * every FK added by F1 above lands with the approved behaviour directly
--     (NO ACTION on financial/audit-feeding paths, SET NULL on optional
--     AI-mapping hints) — so no dangerous CASCADE is introduced by RC1;
--   * pre-existing FKs discovered by the F1 inspection with dangerous CASCADE
--     (organizations/users → customer_subscriptions, consultant_billing,
--     audit_trail, emissions_logs, report_versions) are corrected with the
--     guarded swap template below, executed per confirmed finding.
-- TEMPLATE (commented out — fill in <table>/<constraint> per F1 finding after
-- dependent-row review; keep each swap inside this transaction):
--   ALTER TABLE public.<child_table>
--       DROP CONSTRAINT <existing_fk_name>,
--       ADD CONSTRAINT <existing_fk_name>
--           FOREIGN KEY (<col>) REFERENCES public.<parent> (<pcol>)
--           ON DELETE RESTRICT NOT VALID;
--   ALTER TABLE public.<child_table> VALIDATE CONSTRAINT <existing_fk_name>;
-- ROLLBACK for each swap: re-add the original ON DELETE CASCADE clause.
-- ============================================================================

COMMIT;

-- ============================================================================
-- End of 002_rc1_constraints.sql
-- Review coverage delivered by this file:
--   C1 (presence CHECK), K1, K2, K3, K4, K5, K6, K7, K8, F1, F2.
-- Explicitly absent per the register: K9 regex/format CHECKs (REJECT — API
-- layer owns format validation; stated in the file header).
-- ============================================================================
