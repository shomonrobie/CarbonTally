-- ============================================================================
-- CarbonTally v1.0 RC2 — Production Hardening Migration (REPAIR RELEASE)
-- File 002 of 008: Constraints & referential-integrity repairs
-- Source of truth:
--   * Baseline: supabase/migrations/00000000000000_init_schema.sql
--   * CarbonTally RC1 — Independent Database Audit.md
--   * CarbonTally_v1.0_Structural_Change_Review.md (APPROVE items only)
-- Database: PostgreSQL 16 (Supabase). Schema: public. Single transaction.
--
-- BASELINE REALITY (verified against the actual init file):
--   * FKs required by F1 already exist inline and validated, except none needs
--     creating in 002 — 002 REPAIRS and CONFORMS, never re-creates.
--   * The invalid `emissions_logs_unit_fkey` (mocku text unit -> units.code)
--     EXISTS in the baseline and is the RC2-H2 Critical defect → dropped here.
--   * Check constraints under baseline names (…_role_check, …_status_check) are
--     preserved; RC2 adds only the widened Vocabulary required by H4/M3.
--
-- ASSUMPTIONS (confirmed): a fresh, empty database — no seed data. This makes
-- every backfill below a no-op trivially and the SET NOT NULL tightenings
-- safe (0 rows). All statements are idempotent / guard-protected for re-run.
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1 — RC2-H2: DROP THE INVALID emissions_logs UNIT FOREIGN KEY
-- ============================================================================
-- Audit H2 (RC2-Critical): emissions_logs.unit is free-text prose captured
-- from documents, NOT a units.code reference. A hard FK blocks legitimate
-- factor reads/links and wrongly couples a business value to a lookup table.
-- The column stays (C5) but is deliberately NOT FK'd.
-- ============================================================================
ALTER TABLE public.emissions_logs
    DROP CONSTRAINT IF EXISTS emissions_logs_unit_fkey;

-- ============================================================================
-- SECTION 2 — RC2-H3 / RC2-M9: WIDEN THE EMISSION FACTOR NATURAL KEY
-- ============================================================================
-- The baseline unique index `emission_factors_year_activity_country_uniq`
-- keys ONLY (reporting_year, activity_type, country). The same activity_type
-- can legitimately recur for the same year/country with a different unit or
-- scope (e.g. kWh vs m3 natural gas), so the key is too NARROW and will cause
-- spurious collisions. It is widened to the full natural key and made
-- NULL-safe (COALESCE) so rows that lack unit/scope/country are still unique.
-- Network effect / data impact: none (empty table). REQUIRES WAIT on 001
-- having settled emissions_logs; independent of emissions_logs here.
-- ============================================================================
DROP INDEX IF EXISTS public.emission_factors_year_activity_country_uniq;

CREATE UNIQUE INDEX emission_factors_year_activity_country_uniq
    ON public.emission_factors (
        reporting_year,
        activity_type,
        COALESCE(country, 'GB'),
        COALESCE(unit, '{no-unit}'),
        COALESCE(scope, '{no-scope}')
    );

-- ============================================================================
-- SECTION 3 — RC2-M8: NULL-SAFE USAGE-TRACKING UNIQUE KEY
-- ============================================================================
-- Baseline: UNIQUE (organization_id, usage_month) with a NULLABLE usage_month.
-- Postgres treats NULLs as distinct, so NULL-month rows are NOT made unique by
-- the baseline key — duplicates can slip in. COALESCE provides a stable key
-- component for the uncategorised bucket so the guarantee holds.
-- ============================================================================
DROP INDEX IF EXISTS public.usage_tracking_org_month_uniq;

CREATE UNIQUE INDEX usage_tracking_org_month_uniq
    ON public.usage_tracking (
        organization_id,
        COALESCE(usage_month, DATE '1900-01-01')
    );

-- ============================================================================
-- SECTION 4 — RC2-H4: WIDEN CUSTOMER SUBSCRIPTION STATUS VOCABULARY
-- ============================================================================
-- Baseline check only admits ('trialing','active','past_due','paused',
-- 'cancelled','expired'). Stripe also issues 'incomplete',
-- 'incomplete_expired' and 'unpaid' during checkout; we widen the CHECK so
-- legitimate lifecycle rows aren't rejected. No seed data → safe to replace.
-- ============================================================================
ALTER TABLE public.customer_subscriptions
    DROP CONSTRAINT IF EXISTS customer_subscriptions_status_check;

ALTER TABLE public.customer_subscriptions
    ADD CONSTRAINT customer_subscriptions_status_check
        CHECK (status IN ('trialing','active','past_due','paused','cancelled',
                          'expired','incomplete','incomplete_expired','unpaid'));

-- ============================================================================
-- SECTION 5 — RC2-K7: TENANCY TIGHTENING ON THE SIX HOLE TABLES
-- ============================================================================
-- A NULL organization_id puts a row outside every tenant-equality RLS policy
-- (it is invisible to all tenants yet writable by service_role) — a tenancy
-- hole. The six tables where org id was left nullable are SET NOT NULL here.
-- Empty table → no backfill burden. (conversations/messages may legitimately
-- be NULL in OLTP-supplied flows per the review note, but the approved K7
-- direction is "owner must resolve"; empty baseline makes this a schema guard.)
-- ============================================================================
ALTER TABLE public.conversations           ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE public.messages                ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE public.upload_batches          ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE public.manual_review_queue     ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE public.file_attachments        ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE public.customer_verifications  ALTER COLUMN organization_id SET NOT NULL;

-- ============================================================================
-- SECTION 6 — RC2-K8: CUSTOMER DOCUMENT STATUS NOT NULL
-- ============================================================================
ALTER TABLE public.customer_documents ALTER COLUMN status SET DEFAULT 'uploaded';
ALTER TABLE public.customer_documents ALTER COLUMN status SET NOT NULL;

-- ============================================================================
-- SECTION 7 — RC2-K6: PASSWORD RESET TOKEN user_id NOT UNIQUE (verify)
-- ============================================================================
-- The audit required that a single user may hold MULTIPLE outstanding reset
-- tokens; the baseline already declares user_id as non-unique (plain column).
-- Re-affirm harmlessly: drop any stray single-column unique index on user_id
-- while preserving the guaranteed-unique `token` index.
-- ============================================================================
DROP INDEX IF EXISTS password_reset_tokens_user_id_uniq;

-- ============================================================================
-- SECTION 8 — CONFORMANCE: FKs F1 SET NULL / NO ACTION ON document_processing_queue
-- ============================================================================
-- Baseline already defines:
--   ai_mapped_facility_id  -> ON DELETE SET NULL  (M20 repair, satisfied)
--   ai_mapped_asset_id     -> ON DELETE SET NULL  (M20 satisfied)
--   ai_mapped_supplier_id  -> ON DELETE SET NULL  (M20 satisfied)
--   emission_factor_used   -> ON DELETE NO ACTION (default; F1 satisfied)
-- These are correct; only the referential ORPHAN state is checked in 007.
-- (emissions_logs.emission_factor_id FK -> emission_factors is present and
--  validated in the baseline; also checked in 007.)
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint con
                   WHERE con.conname = 'emissions_logs_emission_factor_id_fkey'
                     AND con.contype = 'f' AND con.convalidated) THEN
        RAISE WARNING 'emissions_logs_emission_factor_id_fkey missing/unvalidated — verify in 007';
    END IF;
END $$;

-- ============================================================================
-- SECTION 9 — CONFORMANCE: K1 country / K2 currency vocabularies (verify,
--           with a guarded fallback so a scheme without them is made safe).
-- ============================================================================
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['organizations','facilities','suppliers','consultant_profiles','emission_factors'] LOOP
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema='public' AND table_name=t AND column_name='country')
           AND NOT EXISTS (SELECT 1 FROM pg_constraint
                           WHERE conname = t || '_country_in_list') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (country IN (''GB'',''IE'')) NOT VALID',
                           t, t || '_country_in_list');
        END IF;
    END LOOP;
END $$;

DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN SELECT * FROM (VALUES
        ('organizations','currency'),
        ('suppliers','payment_currency'),
        ('document_processing_queue','billing_currency'),
        ('customer_subscriptions','currency'),
        ('manual_extraction_batches','currency'),
        ('consultant_profiles','revenue_currency'),
        ('consultant_billing','currency')
    ) AS v(tbl, col) LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema='public' AND table_name=pair.tbl AND column_name=pair.col)
           OR EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_in_list') THEN
            CONTINUE;
        END IF;
        EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I IN (''GBP'',''EUR'')) NOT VALID',
                       pair.tbl, pair.tbl || '_' || pair.col || '_in_list', pair.col);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 10 — CONFORMANCE: K3 non-negative guards (verify/fallback)
-- ============================================================================
DO $$
DECLARE pair RECORD;
BEGIN
    FOR pair IN SELECT * FROM (VALUES
        ('emissions_logs','raw_quantity'),
        ('emissions_logs','calculated_kg_co2e'),
        ('emission_factors','co2e_multiplier')
    ) AS v(tbl, col) LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = pair.tbl || '_' || pair.col || '_nonneg') THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (%I >= 0) NOT VALID',
                           pair.tbl, pair.tbl || '_' || pair.col || '_nonneg', pair.col);
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 11 — VALIDATE ALL NOT-VALID CONSTRAINTS (f/c) IN public
-- ============================================================================
-- Converts the one-pass NOT VALID guards added above into fully enforced
-- constraints. Empty tables validate trivially. Also catches any NOT VALID
-- leftovers from the baseline that were not yet validated.
-- ============================================================================
DO $$
DECLARE con RECORD;
BEGIN
    FOR con IN
        SELECT conname, conrelid::regclass::text AS table_name
        FROM pg_constraint
        WHERE convalidated = false
          AND contype IN ('f','c')
          AND connamespace = 'public'::regnamespace
    LOOP
        EXECUTE format('ALTER TABLE %I VALIDATE CONSTRAINT %I', con.table_name, con.conname);
    END LOOP;
END $$;

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED HERE (register verification):
--   * K9 (postcode/eircode format regex) — REJECTED (API-layer validation).
--   * f2 (DPQ mapped FKs SET NULL) — already satisfied inline in baseline
--     (M20); no re-add.
--   * C11/C12/C13 deferred/rejected per review — not constraints.
--   * Country/currency UI-picker seed rows — DEFERRED (no seeding).
--   * New CHECK rows for consultation table lists (consent) — out of RC2 scope.
-- Rolls back to baseline by reversing drops/rebuilds; see RC2_CHANGELOG runbook.
-- ============================================================================

COMMIT;

-- End of 002_rc2_constraints.sql
