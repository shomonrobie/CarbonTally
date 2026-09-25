-- P16-REMEDIATION-05 / RD-4 (R9) — accounting-result reportability lifecycle.
--
-- Problem: a calculated result that is invalid (P16 historical case: a single-gas
-- CH4 component factor used as a Scope 3 total, 319.536000 kg CO2e) had no
-- machine-readable state. `calculation_snapshots` and `emissions_logs` carried
-- only the value, so exclusion from reporting was a convention, not a rule.
-- `report_versions` lifecycle governs *reports*, not emission results, and
-- `audit_trail` alone is not enforceable at a consumption boundary.
--
-- This migration adds the minimum explicit state required to make
-- valid/reportable versus invalid/not-for-reporting/superseded results
-- machine-enforceable, while leaving every historical accounting value untouched.
--
-- Scope: additive columns only. No existing column, row, value, policy or index
-- is modified or removed. Existing rows default to 'reportable' (their historical
-- meaning) unless they are explicitly invalidated later.

-- ---------------------------------------------------------------------------
-- 1. calculation_snapshots — the authoritative calculation record.
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS reportability_status text NOT NULL DEFAULT 'reportable',
    ADD COLUMN IF NOT EXISTS invalidated_reason   text,
    ADD COLUMN IF NOT EXISTS invalidated_by       uuid,
    ADD COLUMN IF NOT EXISTS invalidated_at       timestamptz,
    ADD COLUMN IF NOT EXISTS superseded_by_snapshot_id uuid;

ALTER TABLE public.calculation_snapshots
    DROP CONSTRAINT IF EXISTS calculation_snapshots_reportability_status_check;
ALTER TABLE public.calculation_snapshots
    ADD CONSTRAINT calculation_snapshots_reportability_status_check
    CHECK (reportability_status IN ('reportable', 'not_for_reporting', 'superseded'));

-- An invalidation must be self-describing: no state change without a reason,
-- an actor and a timestamp (the auditable lifecycle contract).
ALTER TABLE public.calculation_snapshots
    DROP CONSTRAINT IF EXISTS calculation_snapshots_invalidation_described_check;
ALTER TABLE public.calculation_snapshots
    ADD CONSTRAINT calculation_snapshots_invalidation_described_check
    CHECK (
        reportability_status = 'reportable'
        OR (invalidated_reason IS NOT NULL
            AND btrim(invalidated_reason) <> ''
            AND invalidated_by IS NOT NULL
            AND invalidated_at IS NOT NULL)
    );

CREATE INDEX IF NOT EXISTS idx_calc_snapshots_reportability
    ON public.calculation_snapshots (organization_id, reportability_status);

-- ---------------------------------------------------------------------------
-- 2. emissions_logs — the row consumed by reporting/disclosure.
--    Mirrors the snapshot state so the consumption boundary can filter cheaply
--    without depending on a join.
-- ---------------------------------------------------------------------------
ALTER TABLE public.emissions_logs
    ADD COLUMN IF NOT EXISTS reportability_status text NOT NULL DEFAULT 'reportable',
    ADD COLUMN IF NOT EXISTS invalidated_reason   text,
    ADD COLUMN IF NOT EXISTS invalidated_by       uuid,
    ADD COLUMN IF NOT EXISTS invalidated_at       timestamptz,
    ADD COLUMN IF NOT EXISTS superseded_by_log_id uuid;

ALTER TABLE public.emissions_logs
    DROP CONSTRAINT IF EXISTS emissions_logs_reportability_status_check;
ALTER TABLE public.emissions_logs
    ADD CONSTRAINT emissions_logs_reportability_status_check
    CHECK (reportability_status IN ('reportable', 'not_for_reporting', 'superseded'));

ALTER TABLE public.emissions_logs
    DROP CONSTRAINT IF EXISTS emissions_logs_invalidation_described_check;
ALTER TABLE public.emissions_logs
    ADD CONSTRAINT emissions_logs_invalidation_described_check
    CHECK (
        reportability_status = 'reportable'
        OR (invalidated_reason IS NOT NULL
            AND btrim(invalidated_reason) <> ''
            AND invalidated_by IS NOT NULL
            AND invalidated_at IS NOT NULL)
    );

CREATE INDEX IF NOT EXISTS idx_emissions_logs_reportability
    ON public.emissions_logs (organization_id, reportability_status);

COMMENT ON COLUMN public.emissions_logs.reportability_status IS
    'P16-RD-4: reportable | not_for_reporting | superseded. Non-reportable rows are excluded from reporting/disclosure aggregation but remain historically inspectable.';
COMMENT ON COLUMN public.calculation_snapshots.reportability_status IS
    'P16-RD-4: reportable | not_for_reporting | superseded. Historical accounting values are never rewritten; only this state changes.';
