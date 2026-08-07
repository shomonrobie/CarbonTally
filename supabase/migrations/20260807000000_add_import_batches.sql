-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M1 of 8
-- File: 20260807000000_add_import_batches.sql
--
-- Creates the versioned import-batch tracking table for emission-factor
-- provider imports (DEFRA, SEAI, EPA, ADEME, IPCC, custom).
--
-- Design notes (per Backend v2.1 §12 Import Platform):
--   * Imports are versioned: every import creates a new batch; batches are
--     never deleted or updated destructively.
--   * Only one batch per (provider_key, reporting_year) is "active" at a time
--     (is_active = TRUE). Activation/rollback flips this flag only.
--   * `rolled_back_from` points to the replacement batch when this batch is
--     rolled back (non-destructive rollback chain).
--   * The source file checksum (SHA-256) permits independent verification of
--     the imported dataset against the publisher's artefact.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS. Safe to re-run.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.import_batches (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    provider_key VARCHAR NOT NULL,
    provider_version VARCHAR NOT NULL,
    source_file TEXT NOT NULL,
    source_checksum VARCHAR(64) NOT NULL,
    reporting_year INTEGER NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','importing','completed','failed','rolled_back')),
    rows_total INTEGER DEFAULT 0,
    rows_imported INTEGER DEFAULT 0,
    rows_skipped INTEGER DEFAULT 0,
    rows_duplicate INTEGER DEFAULT 0,
    errors JSONB,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    rolled_back_from UUID REFERENCES public.import_batches(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.import_batches IS
    'Versioned import batches for emission-factor provider datasets (Backend v2.1, Import Platform).';
COMMENT ON COLUMN public.import_batches.provider_key IS
    'Provider identifier: defra, seai, epa, ademe, ipcc, custom.';
COMMENT ON COLUMN public.import_batches.provider_version IS
    'Provider-defined dataset version, e.g. 2025.1 (DEFRA), 2024 (SEAI).';
COMMENT ON COLUMN public.import_batches.source_checksum IS
    'SHA-256 hex digest of the publisher source file for independent verification.';
COMMENT ON COLUMN public.import_batches.status IS
    'pending → importing → completed | failed | rolled_back.';
COMMENT ON COLUMN public.import_batches.is_active IS
    'At most one batch per (provider_key, reporting_year) is active; inactive batches remain for provenance.';
COMMENT ON COLUMN public.import_batches.rolled_back_from IS
    'Replacement batch id when this batch was rolled back (non-destructive rollback chain).';

-- ============================================================================
-- VERIFICATION CHECKLIST (M1)
--   [ ] Table exists in public schema
--   [ ] provider_key / provider_version / source_checksum / reporting_year
--       columns present with NOT NULL
--   [ ] status CHECK constraint allows only the five lifecycle values
--   [ ] rolled_back_from self-FK present (ON DELETE SET NULL)
--   [ ] Re-running this file is a no-op (CREATE TABLE IF NOT EXISTS)
-- ============================================================================
