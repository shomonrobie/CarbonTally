-- ============================================================================
-- CarbonTally Phase 8-X X2 — operational telemetry retention setting
-- File: 20260924000000_p8x_x2_operational_telemetry_retention.sql
--
-- PO DECISION (2026-09-14, PX-7 Option (a)) APPROVED:
--   "Operational telemetry retention = configurable server-side, with an initial
--    value of 90 days." Add the dedicated setting
--    `operational_telemetry_retention_days`; 90 must NOT be hard-coded into the
--    retention logic; enforced server-side through the existing retention
--    service; additive and idempotent only; do NOT reuse `data_retention_days`;
--    do NOT alter report/evidence retention; do NOT alter
--    `document_processing_queue` / `processing_logs` retention.
--
-- WHAT THIS ADDS (one column + at most one settings row):
--   * `system_settings.operational_telemetry_retention_days integer NOT NULL
--     DEFAULT 90` — the initial value is the PO's approved 90 days, expressed as
--     a schema DEFAULT (configuration), never as a literal in application code.
--   * a settings row is created only if none exists, so the value is actually
--     configurable without inventing any other setting.
--
-- WHAT IT DOES NOT TOUCH:
--   * `document_retention_days`, `data_retention_days`, `audit_log_retention_days`,
--     `backup_retention_days` — unchanged.
--   * `document_processing_queue`, `processing_logs` — never aged by this policy.
--   * reports, evidence, audit — untouched (B4-D8 retention remains indefinite).
--   * no other table, column, policy or grant.
--
-- ENVIRONMENT: QA / non-production only. Production is PROHIBITED (G0-D open).
-- IDEMPOTENT: re-running is a no-op (IF NOT EXISTS + guarded insert).
-- ============================================================================

BEGIN;

ALTER TABLE public.system_settings
    ADD COLUMN IF NOT EXISTS operational_telemetry_retention_days integer NOT NULL DEFAULT 90;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'system_settings'
          AND column_name = 'operational_telemetry_retention_days'
    ) THEN
        RAISE EXCEPTION 'X2 precondition failed: operational_telemetry_retention_days was not created';
    END IF;

    -- The retention row is identified by the app's own fixed key
    -- (``SettingsRepository._SETTINGS_KEY == 'platform_retention'``). Create it
    -- only when absent, setting ONLY the approved X2 value; every other retention
    -- column is left NULL, which the repository already reports as "not
    -- configured" (no policy value is invented).
    IF NOT EXISTS (
        SELECT 1 FROM public.system_settings WHERE setting_key = 'platform_retention'
    ) THEN
        INSERT INTO public.system_settings (
            setting_key, setting_type, description, setting_value,
            operational_telemetry_retention_days
        ) VALUES (
            'platform_retention', 'retention',
            'Platform retention policy (N3 retention + Phase 8-X X2 operational telemetry)',
            '{}'::jsonb, 90
        );
        RAISE NOTICE 'X2: created the platform_retention row with operational_telemetry_retention_days=90';
    END IF;

    RAISE NOTICE 'X2: operational_telemetry_retention_days = %',
        (SELECT operational_telemetry_retention_days
           FROM public.system_settings WHERE setting_key = 'platform_retention');
END $$;

COMMENT ON COLUMN public.system_settings.operational_telemetry_retention_days IS
    'Phase 8-X X2 (PX-7) — retention for operational TELEMETRY detail only '
    '(heartbeat/metric rows and operational alert notifications + deliveries). '
    'Applied server-side by services/retention.py. EXCLUDES document_processing_queue '
    'and processing_logs (business records) and all report/evidence tables.';

COMMIT;
