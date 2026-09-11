-- ============================================================================
-- CarbonTally v1.0 RC2 — Production Hardening Migration (REPAIR RELEASE)
-- File 001 of 008: Schema conformance + additive guards
-- Source of truth:
--   * Baseline: supabase/migrations/00000000000000_init_schema.sql
--   * CarbonTally RC1 — Independent Database Audit.md (authoritative)
--   * CarbonTally_v1.0_Structural_Change_Review.md (APPROVE items only)
-- Database: PostgreSQL 16 (Supabase). Schema: public. Single transaction.
--
-- RC2 = REPAIR of RC1. Baseline strategy (B-lite): the baseline init ALREADY
-- carries most of RC1's schema shape (renames R1–R3, new columns C1–C10,
-- extension wiring, and a complete table set). This file therefore performs
-- DEFENSIVE CONFORMANCE, not rebuilds:
--   * every "addition" is a guarded no-op when already present (idempotent,
--     safe on a fresh baseline and on re-run);
--   * every guard emits a NOTICE so the operator can confirm conformance;
--   * nothing here DROPs or rewrites existing entities — the repair work for
--     the RC2-Critical/High items is carried in 002 (constraints), 003
--     (indexes), 004 (RLS), 005 (functions), 006 (triggers), 007 (verify).
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1 — RENAMES (R1–R3) — guard: confirm new name exists, old gone.
-- RC2-C1 (RC1-C1): under B-lite these already ran inside the baseline init,
-- so we only VERIFY and never issue an unconditional COMMENT on a possibly
-- missing column. The C4 `region_deprecated` handling is re-guarded below.
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema='public' AND table_name='defra_conversion_factors') THEN
        RAISE EXCEPTION 'R1: legacy defra_conversion_factors still present; aborting (baseline should already be renamed)';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='emission_factors') THEN
        RAISE EXCEPTION 'R1: emission_factors missing on baseline — schema out of conformance; investigate before continuing';
    END IF;
    RAISE NOTICE 'R1 ok: emission_factors present, defra_conversion_factors absent';

    -- R2: emissions_logs. The baseline carries BOTH the legacy defra_factor_id
    -- (plain UUID, no FK) AND the authoritative emission_factor_id (FK to
    -- emission_factors). Guard on presence to avoid a rename collision.
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='emissions_logs' AND column_name='defra_factor_id')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='emissions_logs' AND column_name='emission_factor_id') THEN
        ALTER TABLE public.emissions_logs RENAME COLUMN defra_factor_id TO emission_factor_id;
        RAISE NOTICE 'R2: emissions_logs.defra_factor_id → emission_factor_id (data-preserving rename)';
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='emissions_logs' AND column_name='defra_factor_id') THEN
        ALTER TABLE public.emissions_logs DROP COLUMN IF EXISTS defra_factor_id;
        RAISE NOTICE 'R2: emissions_logs.emission_factor_id already present — dropped redundant legacy defra_factor_id';
    END IF;

    -- R2: document_processing_queue (same both-paths pattern).
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='document_processing_queue' AND column_name='defra_factor_used')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='document_processing_queue' AND column_name='emission_factor_used') THEN
        ALTER TABLE public.document_processing_queue RENAME COLUMN defra_factor_used TO emission_factor_used;
        RAISE NOTICE 'R2: document_processing_queue.defra_factor_used → emission_factor_used (rename)';
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='document_processing_queue' AND column_name='defra_factor_used') THEN
        ALTER TABLE public.document_processing_queue DROP COLUMN IF EXISTS defra_factor_used;
        RAISE NOTICE 'R2: document_processing_queue.emission_factor_used already present — dropped redundant defra_factor_used';
    END IF;

    -- R2: manual_extraction_items (baseline has only the legacy name → rename).
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='manual_extraction_items' AND column_name='defra_factor_used')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='manual_extraction_items' AND column_name='emission_factor_used') THEN
        ALTER TABLE public.manual_extraction_items RENAME COLUMN defra_factor_used TO emission_factor_used;
        RAISE NOTICE 'R2: manual_extraction_items.defra_factor_used → emission_factor_used (rename)';
    END IF;

    -- R3: organizations.default_defra_version → default_factor_year.
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='organizations' AND column_name='default_defra_version')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='organizations' AND column_name='default_factor_year') THEN
        ALTER TABLE public.organizations RENAME COLUMN default_defra_version TO default_factor_year;
        RAISE NOTICE 'R3: organizations.default_defra_version → default_factor_year';
    END IF;
END $$;

-- ============================================================================
-- SECTION 2 — NEW COLUMNS (C1–C10) — guarded ADD COLUMN IF NOT EXISTS.
-- RC2-C1 note: none of these issues an unconditional COMMENT against a
-- possibly-absent column; `region_deprecated` is only ever commented AFTER a
-- lifetime existence guard. The baseline init already created these columns,
-- so in normal operation every block below no-ops with a NOTICE.
-- ============================================================================

-- C1: facilities.eircode + postcode nullable
ALTER TABLE public.facilities
    ADD COLUMN IF NOT EXISTS eircode varchar;
COMMENT ON COLUMN public.facilities.eircode IS
    'Irish Eircode (C1, APPROVE). Pairwise presence with postcode is enforced by facilities_postcode_or_eircode_check (002 conformance). API-layer format validation (K9 rejected).';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='facilities'
                 AND column_name='postcode' AND is_nullable='NO') THEN
        ALTER TABLE public.facilities ALTER COLUMN postcode DROP NOT NULL;
        RAISE NOTICE 'C1: facilities.postcode relaxed to nullable';
    END IF;
END $$;

-- C2: organizations lifecycle flag + archive timestamp
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS is_active boolean;
UPDATE public.organizations SET is_active = true WHERE is_active IS NULL;
ALTER TABLE public.organizations ALTER COLUMN is_active SET DEFAULT true;
ALTER TABLE public.organizations ALTER COLUMN is_active SET NOT NULL;
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS archived_at timestamptz;
COMMENT ON COLUMN public.organizations.is_active IS 'Tenant lifecycle flag (C2, APPROVE). NOT NULL DEFAULT true. RLS suspend predicate.';
COMMENT ON COLUMN public.organizations.archived_at IS 'Tenant archival timestamp (C2, APPROVE). NULL = never archived.';

-- C3: consultant_billing.currency
ALTER TABLE public.consultant_billing ADD COLUMN IF NOT EXISTS currency varchar;
ALTER TABLE public.consultant_billing ALTER COLUMN currency SET DEFAULT 'GBP';
UPDATE public.consultant_billing SET currency='GBP' WHERE currency IS NULL;
COMMENT ON COLUMN public.consultant_billing.currency IS 'ISO 4217 currency (C3, APPROVE). IN (GBP,EUR) enforced in 002 (K2).';

-- ----------------------------------------------------------------------------
-- C4: emission_factors provenance columns (+ safe region_deprecated handling)
-- RC2-C1 REPAIR (authoritative): the live `region` column and the retired
-- `region_deprecated` column are handled non-destructively and idempotently.
-- In the baseline init `emission_factors` already exists WITH the provenance
-- columns and receives `region_deprecated` only when a legacy `region` is
-- folded. The COMMENT below is therefore guarded on column existence — it can
-- never abort a fresh apply (the RC1-C1 failure mode).
-- ----------------------------------------------------------------------------
ALTER TABLE public.emission_factors
    ADD COLUMN IF NOT EXISTS unit text,
    ADD COLUMN IF NOT EXISTS scope text,
    ADD COLUMN IF NOT EXISTS factor_source text,
    ADD COLUMN IF NOT EXISTS factor_set text,
    ADD COLUMN IF NOT EXISTS country varchar;

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
                            ELSE 'GB' END
         WHERE country IS NULL;
        ALTER TABLE public.emission_factors RENAME COLUMN region TO region_deprecated;
    END IF;
END $$;

-- The RC2-C1 guard: comment region_deprecated ONLY if it exists.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='emission_factors' AND column_name='region_deprecated') THEN
        COMMENT ON COLUMN public.emission_factors.region_deprecated IS
            'Legacy free-text region folded into country during C4 backfill and retired non-destructively (C4, APPROVE). Do not read; drop after consumer audit.';
    ELSE
        RAISE NOTICE 'C4: region_deprecated not present (clean baseline) — no comment issued';
    END IF;
END $$;

-- C4 provenance backfills (idempotent; fresh DB has zero rows, no-op)
UPDATE public.emission_factors SET country='GB'      WHERE country IS NULL;
UPDATE public.emission_factors SET factor_source='DEFRA-DESNZ' WHERE factor_source IS NULL;
UPDATE public.emission_factors
   SET factor_set = 'DEFRA-' || reporting_year::text
 WHERE factor_set IS NULL AND reporting_year IS NOT NULL;

COMMENT ON COLUMN public.emission_factors.unit IS 'Unit the co2e_multiplier applies to (C4, APPROVE). Free text by design; NOT an FK.';
COMMENT ON COLUMN public.emission_factors.scope IS 'GHG Protocol scope label (C4, APPROVE).';
COMMENT ON COLUMN public.emission_factors.factor_source IS 'Source authority: DEFRA-DESNZ, later SEAI/EPA (C4, APPROVE).';
COMMENT ON COLUMN public.emission_factors.factor_set IS 'Factor vintage/set aligned with system_settings.default_emission_factor_set (C4, APPROVE).';
COMMENT ON COLUMN public.emission_factors.country IS 'Jurisdiction: GB or IE (C4, APPROVE). Feeds the RC2 factor natural key (002 H3).';

-- ----------------------------------------------------------------------------
-- C5: emissions_logs.unit / .scope  (RC2-H2 note: NOT FK'd)
-- ----------------------------------------------------------------------------
ALTER TABLE public.emissions_logs
    ADD COLUMN IF NOT EXISTS unit text,
    ADD COLUMN IF NOT EXISTS scope varchar;

UPDATE public.emissions_logs el
   SET unit = ef.unit, scope = ef.scope
  FROM public.emission_factors ef
 WHERE el.emission_factor_id = ef.id
   AND el.unit IS NULL AND ef.unit IS NOT NULL;

COMMENT ON COLUMN public.emissions_logs.unit IS 'Unit of raw_quantity, backfilled via factor join. Deliberately not an FK (RC2-H2).';
COMMENT ON COLUMN public.emissions_logs.scope IS 'GHG Protocol scope label (C5, APPROVE).';

-- ----------------------------------------------------------------------------
-- C6: customer_documents.file_checksum
-- ----------------------------------------------------------------------------
ALTER TABLE public.customer_documents ADD COLUMN IF NOT EXISTS file_checksum text;
COMMENT ON COLUMN public.customer_documents.file_checksum IS
    'SHA-256 hex of uploaded file (C6, APPROVE). NOT unique in v1.0.';

-- C7: file_attachments.file_size bigint (baseline already bigint; guard)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='file_attachments'
                 AND column_name='file_size' AND data_type='integer') THEN
        ALTER TABLE public.file_attachments ALTER COLUMN file_size TYPE bigint;
        RAISE NOTICE 'C7: file_attachments.file_size widened to bigint';
    END IF;
END $$;

-- C8: suppliers.sort_code
ALTER TABLE public.suppliers ADD COLUMN IF NOT EXISTS sort_code varchar;
COMMENT ON COLUMN public.suppliers.sort_code IS 'UK bank sort code, digits only, API-normalised (C8, APPROVE). PII register.';

-- C9: facilities.meter_mpan_mprn
ALTER TABLE public.facilities ADD COLUMN IF NOT EXISTS meter_mpan_mprn varchar;
COMMENT ON COLUMN public.facilities.meter_mpan_mprn IS 'Meter MPAN/MPRN free format (C9, APPROVE). API normalisation.';

-- C10: organization_metadata floor area (m²)
ALTER TABLE public.organization_metadata
    ADD COLUMN IF NOT EXISTS total_floor_area_sqm numeric,
    ADD COLUMN IF NOT EXISTS occupied_floor_area_sqm numeric;
COMMENT ON COLUMN public.organization_metadata.total_floor_area_sqm IS 'Total floor area m² (C10, APPROVE).';
COMMENT ON COLUMN public.organization_metadata.occupied_floor_area_sqm IS 'Occupied floor area m² (C10, APPROVE).';

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED HERE (register verification) — unchanged from RC1:
--   C11/C12 deferred to v1.1; C13 deferred v1.0.x; C14/C15 rejected; T1–T3
--   rejected/deferred per review. No new tables introduced.
-- ============================================================================

COMMIT;

-- End of 001_rc2_schema.sql
