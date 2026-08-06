-- ============================================================================
-- CarbonTally v1.0 RC1 — Production Hardening Migration
-- File 001 of 008: Schema changes (renames R1–R3, approved new columns C1–C10)
-- Source of truth: CarbonTally_v1.0_Structural_Change_Review.md
--   Implements ONLY items marked APPROVE. DEFER items (C11, C12, C13, T2) and
--   REJECT items (C14, C15, T1, T3, I6, K9) are intentionally absent.
-- Database: PostgreSQL 16 (Supabase). Schema: public.
-- Run order: 001 → 002 → 003 (003 is non-transactional, see its header).
-- This file is wrapped in a single transaction: all statements here are
-- metadata-only or seed-scale rewrites, safe to run transactionally.
-- RLS policies, functions and triggers are NOT touched here (later files).
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1 — RENAMES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- R1: rename defra_conversion_factors → emission_factors
-- (Structural Change Review §1 R1, APPROVE)
-- Jurisdiction-neutral name; the single structural v1.1-Ireland enabler that
-- cannot be deferred. Metadata-only rename (no table rewrite).
-- Guarded on BOTH names so the file is idempotent and fails loudly if neither
-- table exists.
-- ROLLBACK (destructive reverse — comment out to execute):
--   ALTER TABLE public.emission_factors RENAME TO defra_conversion_factors;
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'public' AND table_name = 'defra_conversion_factors')
       AND NOT EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'public' AND table_name = 'emission_factors') THEN
        ALTER TABLE public.defra_conversion_factors RENAME TO emission_factors;
        RAISE NOTICE 'R1: defra_conversion_factors renamed to emission_factors';
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables
                  WHERE table_schema = 'public' AND table_name = 'emission_factors') THEN
        RAISE NOTICE 'R1: emission_factors already present — no-op (idempotent)';
    ELSE
        RAISE EXCEPTION 'R1: neither defra_conversion_factors nor emission_factors found — investigate before continuing';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- R2: rename referencing factor columns
-- (Structural Change Review §1 R2, APPROVE — companion to R1)
--   emissions_logs.defra_factor_id            → emission_factor_id
--   document_processing_queue.defra_factor_used → emission_factor_used
--   manual_extraction_items.defra_factor_used   → emission_factor_used
--     (added to the R2 rename batch per the RC2 Architecture Freeze, RC2-003)
-- Metadata-only renames, guarded on both old and new names.
-- ROLLBACK:
--   ALTER TABLE public.emissions_logs RENAME COLUMN emission_factor_id TO defra_factor_id;
--   ALTER TABLE public.document_processing_queue RENAME COLUMN emission_factor_used TO defra_factor_used;
--   ALTER TABLE public.manual_extraction_items RENAME COLUMN emission_factor_used TO defra_factor_used;
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='emissions_logs' AND column_name='defra_factor_id')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='emissions_logs' AND column_name='emission_factor_id') THEN
        ALTER TABLE public.emissions_logs RENAME COLUMN defra_factor_id TO emission_factor_id;
        RAISE NOTICE 'R2: emissions_logs.defra_factor_id → emission_factor_id';
    ELSE
        RAISE NOTICE 'R2: emissions_logs.emission_factor_id already present or source missing — no-op';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='document_processing_queue' AND column_name='defra_factor_used')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='document_processing_queue' AND column_name='emission_factor_used') THEN
        ALTER TABLE public.document_processing_queue RENAME COLUMN defra_factor_used TO emission_factor_used;
        RAISE NOTICE 'R2: document_processing_queue.defra_factor_used → emission_factor_used';
    ELSE
        RAISE NOTICE 'R2: document_processing_queue.emission_factor_used already present or source missing — no-op';
    END IF;

    -- Added to the R2 batch per the RC2 Architecture Freeze (RC2-003).
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='manual_extraction_items' AND column_name='defra_factor_used')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='manual_extraction_items' AND column_name='emission_factor_used') THEN
        ALTER TABLE public.manual_extraction_items RENAME COLUMN defra_factor_used TO emission_factor_used;
        RAISE NOTICE 'R2: manual_extraction_items.defra_factor_used → emission_factor_used';
    ELSE
        RAISE NOTICE 'R2: manual_extraction_items.emission_factor_used already present or source missing — no-op';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- R3: organizations.default_defra_version → default_factor_year
-- (Structural Change Review §1 R3, APPROVE)
-- Matches the neutral platform-level system_settings.default_emission_factor_year.
-- ROLLBACK:
--   ALTER TABLE public.organizations RENAME COLUMN default_factor_year TO default_defra_version;
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='organizations' AND column_name='default_defra_version')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='organizations' AND column_name='default_factor_year') THEN
        ALTER TABLE public.organizations RENAME COLUMN default_defra_version TO default_factor_year;
        RAISE NOTICE 'R3: organizations.default_defra_version → default_factor_year';
    ELSE
        RAISE NOTICE 'R3: default_factor_year already present or source missing — no-op';
    END IF;
END $$;

-- ============================================================================
-- SECTION 2 — APPROVED NEW COLUMNS (C1–C10 approved subset only)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- C1: facilities.eircode + relax facilities.postcode NOT NULL
-- (Structural Change Review §2 C1, APPROVE — the non-negotiable Ireland
-- write-path change; Ireland has no postcodes.)
-- The companion presence CHECK is added in 002_rc1_constraints.sql (K-section).
-- Eircode FORMAT validation stays at the API layer (K9 REJECT — see 002).
-- ----------------------------------------------------------------------------
ALTER TABLE public.facilities
    ADD COLUMN IF NOT EXISTS eircode varchar;

COMMENT ON COLUMN public.facilities.eircode IS
    'Irish Eircode (C1, APPROVE). Nullable; presence enforced pairwise with postcode by facilities_postcode_or_eircode_check (002). Format validation at API layer (K9 rejected).';

-- Relax postcode NOT NULL → nullable (guarded). Pre-launch data is GB-only
-- seed, so no backfill is required; the presence CHECK in 002 closes the
-- harmful both-NULL state for all future writes.
-- ROLLBACK (destructive — tighten again):
--   ALTER TABLE public.facilities ALTER COLUMN postcode SET NOT NULL;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='facilities'
                 AND column_name='postcode' AND is_nullable='NO') THEN
        ALTER TABLE public.facilities ALTER COLUMN postcode DROP NOT NULL;
        RAISE NOTICE 'C1: facilities.postcode NOT NULL relaxed';
    ELSE
        RAISE NOTICE 'C1: facilities.postcode already nullable — no-op';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- C2: organizations.is_active + organizations.archived_at lifecycle columns
-- (Structural Change Review §2 C2, APPROVE)
-- is_active: NOT NULL, DEFAULT true, backfilled true (pre-launch-safe).
-- ROLLBACK:
--   ALTER TABLE public.organizations DROP COLUMN is_active, DROP COLUMN archived_at;
-- ----------------------------------------------------------------------------
ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS is_active boolean;

-- Backfill-then-constrain: populate existing rows BEFORE tightening.
UPDATE public.organizations SET is_active = true WHERE is_active IS NULL;

ALTER TABLE public.organizations
    ALTER COLUMN is_active SET DEFAULT true,
    ALTER COLUMN is_active SET NOT NULL;

ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS archived_at timestamptz;

COMMENT ON COLUMN public.organizations.is_active IS
    'Tenant lifecycle flag (C2, APPROVE). NOT NULL DEFAULT true, backfilled true. Reversible evidence-preserving off-switch; RLS suspend predicate.';
COMMENT ON COLUMN public.organizations.archived_at IS
    'Tenant archival timestamp (C2, APPROVE). NULL = never archived.';

-- ----------------------------------------------------------------------------
-- C3: consultant_billing.currency
-- (Structural Change Review §2 C3, APPROVE — the only billing table without
-- a currency column.) Nullable add, DEFAULT 'GBP', backfilled 'GBP'
-- (UK-primary launch reality; validated against existing rows pre-launch).
-- Constrained by K2's IN-list in 002.
-- ROLLBACK: ALTER TABLE public.consultant_billing DROP COLUMN currency;
-- ----------------------------------------------------------------------------
ALTER TABLE public.consultant_billing
    ADD COLUMN IF NOT EXISTS currency varchar;

ALTER TABLE public.consultant_billing
    ALTER COLUMN currency SET DEFAULT 'GBP';

UPDATE public.consultant_billing SET currency = 'GBP' WHERE currency IS NULL;

COMMENT ON COLUMN public.consultant_billing.currency IS
    'ISO 4217 currency for consultant billing (C3, APPROVE). Backfilled GBP; IN (GBP,EUR) enforced in 002 (K2).';

-- ----------------------------------------------------------------------------
-- C4: emission_factors provenance columns: unit, scope, factor_source,
--     factor_set, country  (+ fold/retire legacy `region`)
-- (Structural Change Review §2 C4, APPROVE — third v1.1-Ireland enabler.)
-- All columns nullable at add; existing rows backfilled:
--   factor_source = 'DEFRA-DESNZ'  (all existing rows are DEFRA/DESNZ)
--   country       = 'GB'           (all existing rows are UK factors)
--   factor_set    = 'DEFRA-' || reporting_year (vintage/set identifier aligning
--                   with system_settings.default_emission_factor_set)
-- unit/scope left NULL at backfill — genuinely unknown per row; populated by
-- the companion factor data audit (data work, not structural).
-- The legacy nullable `region` column (noted in the review; absent from the
-- dump — handled defensively) is folded into `country` then RETIRED by rename
-- to region_deprecated (non-destructive, per the review's
-- single-source-of-truth stance; a guarded drop is provided commented).
-- ROLLBACK:
--   ALTER TABLE public.emission_factors RENAME COLUMN region_deprecated TO region;  -- if retired
--   ALTER TABLE public.emission_factors DROP COLUMN unit, DROP COLUMN scope,
--     DROP COLUMN factor_source, DROP COLUMN factor_set, DROP COLUMN country;
-- ----------------------------------------------------------------------------
ALTER TABLE public.emission_factors
    ADD COLUMN IF NOT EXISTS unit text,
    ADD COLUMN IF NOT EXISTS scope text,
    ADD COLUMN IF NOT EXISTS factor_source text,
    ADD COLUMN IF NOT EXISTS factor_set text,
    ADD COLUMN IF NOT EXISTS country varchar;

-- Fold legacy region values into country BEFORE backfilling (region wins only
-- where it already carries a recognisable GB/IE value; everything else → 'GB').
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='emission_factors' AND column_name='region') THEN
        UPDATE public.emission_factors
           SET country = CASE upper(btrim(region))
                            WHEN 'GB' THEN 'GB' WHEN 'UK' THEN 'GB'
                            WHEN 'UNITED KINGDOM' THEN 'GB' WHEN 'GREAT BRITAIN' THEN 'GB'
                            WHEN 'ENGLAND' THEN 'GB' WHEN 'SCOTLAND' THEN 'GB'
                            WHEN 'WALES' THEN 'GB' WHEN 'NORTHERN IRELAND' THEN 'GB'
                            WHEN 'IE' THEN 'IE' WHEN 'IRL' THEN 'IE'
                            WHEN 'IRELAND' THEN 'IE' WHEN 'REPUBLIC OF IRELAND' THEN 'IE'
                            ELSE 'GB'
                         END
         WHERE country IS NULL;
        -- Non-destructive retirement: rename rather than drop.
        ALTER TABLE public.emission_factors RENAME COLUMN region TO region_deprecated;
        RAISE NOTICE 'C4: region values folded into country; region renamed to region_deprecated';
    ELSE
        UPDATE public.emission_factors SET country = 'GB' WHERE country IS NULL;
        RAISE NOTICE 'C4: no region column present (dump-accurate); country backfilled GB only';
    END IF;
END $$;

-- GUARDED DESTRUCTIVE OPTION (preferred retirement is the rename above;
-- execute only after a full consumer audit confirms no references):
--   ALTER TABLE public.emission_factors DROP COLUMN IF EXISTS region_deprecated;

UPDATE public.emission_factors SET factor_source = 'DEFRA-DESNZ' WHERE factor_source IS NULL;
UPDATE public.emission_factors
   SET factor_set = 'DEFRA-' || reporting_year::text
 WHERE factor_set IS NULL AND reporting_year IS NOT NULL;
UPDATE public.emission_factors SET country = 'GB' WHERE country IS NULL;  -- safety net

COMMENT ON COLUMN public.emission_factors.unit IS 'Unit the co2e_multiplier applies to, e.g. kWh, kg, litre, passenger.km (C4, APPROVE). Free text by design (units FK = over-modelling).';
COMMENT ON COLUMN public.emission_factors.scope IS 'GHG Protocol scope label 1/2/3 (C4, APPROVE).';
COMMENT ON COLUMN public.emission_factors.factor_source IS 'Source authority: DEFRA-DESNZ (backfill), SEAI/EPA for v1.1 Irish rows (C4, APPROVE).';
COMMENT ON COLUMN public.emission_factors.factor_set IS 'Named factor vintage/set, aligns with system_settings.default_emission_factor_set (C4, APPROVE).';
COMMENT ON COLUMN public.emission_factors.country IS 'Jurisdiction of the factor: GB or IE (C4, APPROVE). Backfilled GB; IN-list enforced in 002 (K1 mechanism). Feeds K5 factor UNIQUE.';
COMMENT ON COLUMN public.emission_factors.region_deprecated IS 'Legacy free-text region, folded into country during C4 backfill and retired non-destructively (C4, APPROVE). Do not read; drop after consumer audit.';

-- ----------------------------------------------------------------------------
-- C5: emissions_logs.unit + emissions_logs.scope
-- (Structural Change Review §2 C5, APPROVE — self-describing quantities for
-- SECR/scope rollups without the factor join.)
-- unit: text, FK to units.code added in 002 (F1 batch).
-- Backfill derives unit/scope via the factor join where possible; rows without
-- a factor stay NULL (staging data audit gates, per the review).
-- ROLLBACK:
--   ALTER TABLE public.emissions_logs DROP COLUMN unit, DROP COLUMN scope;
-- ----------------------------------------------------------------------------
ALTER TABLE public.emissions_logs
    ADD COLUMN IF NOT EXISTS unit text,
    ADD COLUMN IF NOT EXISTS scope varchar;

-- Derived backfill from the renamed factor table (seed-scale volumes).
UPDATE public.emissions_logs el
   SET unit = ef.unit,
       scope = ef.scope
  FROM public.emission_factors ef
 WHERE el.emission_factor_id = ef.id
   AND el.unit IS NULL
   AND ef.unit IS NOT NULL;

COMMENT ON COLUMN public.emissions_logs.unit IS 'Unit of raw_quantity; FK to units.code added in 002 (C5/F1). Backfilled via factor join where derivable.';
COMMENT ON COLUMN public.emissions_logs.scope IS 'GHG Protocol scope label (C5, APPROVE). Value list to be constrained by K4 mechanism once populated (v1.1).';

-- ----------------------------------------------------------------------------
-- C6: customer_documents.file_checksum (SHA-256 hex)
-- (Structural Change Review §2 C6, APPROVE — deterministic duplicate-upload
-- detection on the pipeline entity. No UNIQUE in v1.0 by design.)
-- ROLLBACK: ALTER TABLE public.customer_documents DROP COLUMN file_checksum;
-- ----------------------------------------------------------------------------
ALTER TABLE public.customer_documents
    ADD COLUMN IF NOT EXISTS file_checksum text;

COMMENT ON COLUMN public.customer_documents.file_checksum IS
    'SHA-256 hex of uploaded file content (C6, APPROVE). Populated at upload; existing rows stay NULL. Deliberately NOT unique in v1.0.';

-- ----------------------------------------------------------------------------
-- C7: file_attachments.file_size int4 → int8 widening
-- (Structural Change Review §2 C7, APPROVE — aligns with the int8 peer columns
-- document_processing_queue.file_size_bytes / processing_queue.file_size_bytes;
-- removes the 2 GB overflow ceiling.) Value-compatible widening; table rewrite
-- is trivial at pre-launch row counts. Companion ≥ 0 CHECK in 002 (K3).
-- ROLLBACK (lossy if any value > int4 max — verify first):
--   ALTER TABLE public.file_attachments ALTER COLUMN file_size TYPE int4;
-- ----------------------------------------------------------------------------
ALTER TABLE public.file_attachments
    ALTER COLUMN file_size TYPE bigint;

COMMENT ON COLUMN public.file_attachments.file_size IS
    'File size in bytes, int8 (C7, APPROVE — widened from int4). Non-negative CHECK in 002 (K3).';

-- ----------------------------------------------------------------------------
-- C8: suppliers.sort_code (UK domestic account routing)
-- (Structural Change Review §2 C8, APPROVE — pairs with existing iban for full
-- GB/IE banking coverage.) Stored normalised (digits only); masking is an API
-- concern. Format validation at API layer (K9 rejected).
-- ROLLBACK: ALTER TABLE public.suppliers DROP COLUMN sort_code;
-- ----------------------------------------------------------------------------
ALTER TABLE public.suppliers
    ADD COLUMN IF NOT EXISTS sort_code varchar;

COMMENT ON COLUMN public.suppliers.sort_code IS
    'UK bank sort code, digits only, normalised by API (C8, APPROVE). PII register; last-4 masking at API layer. No format CHECK (K9 rejected).';

-- ----------------------------------------------------------------------------
-- C9: facilities.meter_mpan_mprn
-- (Structural Change Review §2 C9, APPROVE — MPAN (GB electricity) / MPRN
-- (GB & IE gas) free-format identifier for future bill-to-facility matching.)
-- ROLLBACK: ALTER TABLE public.facilities DROP COLUMN meter_mpan_mprn;
-- ----------------------------------------------------------------------------
ALTER TABLE public.facilities
    ADD COLUMN IF NOT EXISTS meter_mpan_mprn varchar;

COMMENT ON COLUMN public.facilities.meter_mpan_mprn IS
    'Meter identifier: MPAN (GB electricity) or MPRN (GB/IE gas), free format (C9, APPROVE). Normalisation at API layer (K9 layering rule).';

-- ----------------------------------------------------------------------------
-- C10: organization_metadata.total_floor_area_sqm / occupied_floor_area_sqm
-- (Structural Change Review §2 C10, APPROVE — metric-labelled columns
-- alongside the existing sqft pair; prevents m² values being entered into
-- sqft-labelled columns by Irish beta users. sqft deprecation deferred v1.1.)
-- ROLLBACK:
--   ALTER TABLE public.organization_metadata
--     DROP COLUMN total_floor_area_sqm, DROP COLUMN occupied_floor_area_sqm;
-- ----------------------------------------------------------------------------
ALTER TABLE public.organization_metadata
    ADD COLUMN IF NOT EXISTS total_floor_area_sqm numeric,
    ADD COLUMN IF NOT EXISTS occupied_floor_area_sqm numeric;

COMMENT ON COLUMN public.organization_metadata.total_floor_area_sqm IS
    'Total floor area in square metres (C10, APPROVE). API populates the column matching the org country default; reporting reads m² preferentially.';
COMMENT ON COLUMN public.organization_metadata.occupied_floor_area_sqm IS
    'Occupied floor area in square metres (C10, APPROVE). See total_floor_area_sqm.';

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED HERE (review register verification):
--   C11 typed invoice columns — DEFER to v1.1
--   C12 emissions_logs.facility_id — DEFER to v1.1
--   C13 customer_documents.deleted_at — DEFER to v1.0.x window
--   C14 per-user 2FA/lockout columns — REJECT (Supabase Auth ADR)
--   C15 external_id/integration columns — REJECT (premature)
--   T1 emission_factor_sets table — REJECT (C4 columns are sufficient)
--   T2 audit-archive table — DEFER
--   T3 county lookup table — REJECT
--   country_code column — REJECTED (existing country column constrained in 002)
-- ============================================================================

COMMIT;

-- End of 001_rc1_schema.sql
