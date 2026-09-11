-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M3 of 8
-- File: 20260807020000_add_calculation_snapshots.sql
--
-- Creates the immutable forensic record for every emissions calculation
-- (Backend v2.1 §13 Calculation Platform, ADR-5).
--
-- Design:
--   * Snapshots are NEVER updated or deleted (append-only). Auditors can
--     re-run any historical calculation and verify the identical result.
--   * content_hash (SHA-256 of all inputs) provides tamper detection.
--   * factor_id → emission_factors(id) uses ON DELETE RESTRICT: a factor that
--     a snapshot references must never be deleted (factors are deactivated,
--     not removed — Import Platform guarantees this).
--   * organization_id cascades with the owning organization.
--   * import_batch_id links to the producing import batch when known.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.calculation_snapshots (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    activity VARCHAR NOT NULL,
    activity_type VARCHAR NOT NULL,
    quantity NUMERIC NOT NULL CHECK (quantity >= 0),
    quantity_unit VARCHAR NOT NULL,
    co2e_multiplier NUMERIC NOT NULL,
    co2e_kg NUMERIC NOT NULL CHECK (co2e_kg >= 0),
    scope VARCHAR,
    date DATE NOT NULL,
    factor_id UUID NOT NULL REFERENCES public.emission_factors(id) ON DELETE RESTRICT,
    factor_source VARCHAR,
    factor_set VARCHAR,
    import_batch_id UUID REFERENCES public.import_batches(id) ON DELETE SET NULL,
    reporting_year INTEGER NOT NULL,
    methodology VARCHAR NOT NULL,
    algorithm_version VARCHAR NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    calculated_by VARCHAR,
    request_id UUID
);

COMMENT ON TABLE public.calculation_snapshots IS
    'Immutable forensic record of every emissions calculation. Append-only; never updated or deleted (Backend v2.1 ADR-5).';
COMMENT ON COLUMN public.calculation_snapshots.co2e_multiplier IS
    'Exact factor value used at calculation time (Decimal precision preserved).';
COMMENT ON COLUMN public.calculation_snapshots.content_hash IS
    'SHA-256 hex digest of all calculation inputs for tamper detection and reproducibility verification.';
COMMENT ON COLUMN public.calculation_snapshots.factor_id IS
    'emission_factors.id used. ON DELETE RESTRICT — a referenced factor can never be deleted.';
COMMENT ON COLUMN public.calculation_snapshots.algorithm_version IS
    'Engine/algorithm version (Backend v2.1, e.g. 2.1.0) for methodology traceability.';
COMMENT ON COLUMN public.calculation_snapshots.request_id IS
    'Originating API request id; correlates with audit trail and domain events.';

-- ============================================================================
-- VERIFICATION CHECKLIST (M3)
--   [ ] Table exists in public schema
--   [ ] organization_id FK → organizations(id) ON DELETE CASCADE
--   [ ] factor_id FK → emission_factors(id) ON DELETE RESTRICT (convalidated)
--   [ ] import_batch_id FK → import_batches(id) ON DELETE SET NULL
--   [ ] quantity / co2e_kg CHECK (>= 0) constraints present
--   [ ] content_hash NOT NULL (64-char)
--   [ ] Re-running this file is a no-op
-- ============================================================================
