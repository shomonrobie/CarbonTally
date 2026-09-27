-- ============================================================================
-- CT-IMPLEMENT-02 — canonical scheduled reporting (PD-2)
-- File: 20261023000000_ct02_scheduled_reporting.sql
--
-- PO DECISION IMPLEMENTED (ratified — not reinterpreted here):
--   PD-2  IMPLEMENT CANONICAL SCHEDULED REPORTING.
--         * Do NOT retire scheduled reporting.
--         * Do NOT recreate `report_schedules` as a blind legacy table.
--         * Create a canonical schedule model compatible with the V3
--           report/version architecture.
--
-- WHAT WAS WRONG (verified, not assumed):
--   `POST /api/reports/schedule` and its siblings in
--   `backend/routes/reports.py` wrote to a `report_schedules` table that does
--   not exist in the canonical schema. The surface was live-broken, had no
--   canonical report definition binding, no execution record, no idempotency,
--   no failure/retry state, no tenant-isolation proof and no audit; and nothing
--   anywhere executed a schedule, so a "scheduled report" could never produce a
--   report.
--
-- NAMING (deliberate, and required by PD-2): the canonical tables are
--   `report_schedule_definitions` and `report_schedule_runs`, NOT
--   `report_schedules`. PD-2 forbids recreating a legacy table of that name;
--   using a distinct canonical name removes any possibility that a future
--   reader, grep or migration mistake the new model for the retired one.
--
-- WHAT THIS FILE PROVIDES:
--   public.report_schedule_definitions  the schedule (definition + state)
--   public.report_schedule_runs         one row per due-slot execution attempt
--
-- EXECUTION GUARANTEES (semantics enforced here; orchestration is the
-- application's job — see backend/services/report_schedule_runner.py):
--   * `UNIQUE (schedule_id, scheduled_for)` makes execution IDEMPOTENT: a
--     repeated tick for the same due slot cannot create a second run, and the
--     produced report is therefore never duplicated.
--   * A run records its real outcome (`running`/`succeeded`/`failed`/
--     `skipped`), the report/version it produced (when it produced one), and
--     the failure reason (when it did not) — never a spinner.
--   * `next_run_at`/`last_run_at`/`last_result`/`failure_count`/`retry_policy`
--     are persisted schedule state, so a restart resumes from the database
--     rather than from memory.
--   * `is_active` + `paused_at` express pause/resume explicitly.
--   * Nothing in this schema can bypass the report workflow: a run stores a
--     canonical `report_versions` row produced by the normal engine, and the
--     version keeps its own lifecycle (DRAFT → … → FINAL).
--
-- SCOPE DISCIPLINE: additive + idempotent. Creates exactly TWO new tables.
-- MODIFIES ZERO existing tables. No `report_schedules` and no `report_history`
-- is created. No second competing scheduler infrastructure is introduced: the
-- runner reuses the existing repository/engine/audit substrate.
--
-- VERIFICATION CHECKLIST
--   [ ] tables report_schedule_definitions / report_schedule_runs exist
--   [ ] report_schedules and report_history are still ABSENT
--   [ ] RLS enabled on both; no anon/public policy or grant
--   [ ] unsupported report_type rejected; unknown frequency rejected
--   [ ] unknown IANA timezone rejected (trigger)
--   [ ] empty recipient list rejected; malformed retry policy rejected
--   [ ] duplicate (schedule_id, scheduled_for) rejected (idempotency)
--   [ ] runs reject UPDATE/DELETE/TRUNCATE (trigger + privileges)
--   [ ] re-running this file is a no-op
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions — fail closed rather than silently no-op
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.report_generation_queue') IS NULL
       OR to_regclass('public.report_versions') IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2) precondition failed: report_generation_queue '
            '/ report_versions are absent. Scheduling must produce canonical '
            'reports and versions.';
    END IF;
    IF to_regprocedure('public.p8_disclosure_is_org_member(uuid)') IS NULL
       OR to_regprocedure('public.p8_disclosure_is_org_admin(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2) precondition failed: the B1 organisation '
            'helpers are absent. Apply '
            '20260914000000_p8_b1_disclosure_model_foundation.sql first.';
    END IF;
    IF to_regclass('public.report_schedules') IS NOT NULL
       OR to_regclass('public.report_history') IS NOT NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2): a legacy report_schedules/report_history '
            'table EXISTS in this target. PD-2 forbids recreating them; '
            'investigate before applying.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.report_schedule_definitions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_schedule_definitions (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name text NOT NULL,
    -- The canonical report definition this schedule drives. It is expressed in
    -- the same vocabulary as the reports surface, and only engine-supported
    -- types are accepted: a schedule can never claim a report the engine cannot
    -- actually produce.
    report_type varchar(32) NOT NULL DEFAULT 'annual',
    reporting_year integer NOT NULL,
    period_start date,
    period_end date,
    recipients jsonb NOT NULL,
    frequency varchar(16) NOT NULL,
    -- Local time of day the run is due, in the schedule's own timezone.
    run_time time NOT NULL DEFAULT '07:00',
    timezone text NOT NULL DEFAULT 'Europe/London',
    is_active boolean NOT NULL DEFAULT true,
    paused_at timestamptz,
    created_by uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    -- Execution state (persisted, so a restart resumes from the database).
    next_run_at timestamptz,
    last_run_at timestamptz,
    last_result varchar(16),
    last_error text,
    failure_count integer NOT NULL DEFAULT 0,
    retry_policy jsonb NOT NULL DEFAULT
        '{"max_attempts": 3, "backoff_minutes": [5, 30, 120]}'::jsonb,
    CONSTRAINT report_schedule_definitions_name_check
        CHECK (btrim(name) <> ''),
    -- Only report types the canonical engine genuinely supports.
    CONSTRAINT report_schedule_definitions_report_type_check
        CHECK (report_type IN ('annual')),
    CONSTRAINT report_schedule_definitions_year_check
        CHECK (reporting_year BETWEEN 1990 AND 2100),
    CONSTRAINT report_schedule_definitions_period_order_check
        CHECK (period_start IS NULL OR period_end IS NULL OR period_end >= period_start),
    CONSTRAINT report_schedule_definitions_recipients_check
        CHECK (jsonb_typeof(recipients) = 'array' AND jsonb_array_length(recipients) > 0),
    CONSTRAINT report_schedule_definitions_frequency_check
        CHECK (frequency IN ('weekly', 'monthly', 'quarterly', 'annual')),
    CONSTRAINT report_schedule_definitions_result_check
        CHECK (last_result IS NULL
               OR last_result IN ('succeeded', 'failed', 'skipped')),
    -- A failed run must explain itself.
    CONSTRAINT report_schedule_definitions_failure_described_check
        CHECK (last_result IS DISTINCT FROM 'failed'
               OR (last_error IS NOT NULL AND btrim(last_error) <> '')),
    CONSTRAINT report_schedule_definitions_pause_check
        CHECK (is_active OR paused_at IS NOT NULL),
    CONSTRAINT report_schedule_definitions_failure_count_check
        CHECK (failure_count >= 0),
    CONSTRAINT report_schedule_definitions_retry_policy_check
        CHECK (jsonb_typeof(retry_policy) = 'object'
               AND retry_policy ? 'max_attempts'
               AND (retry_policy->>'max_attempts') ~ '^[0-9]+$'
               AND (retry_policy->>'max_attempts')::int BETWEEN 1 AND 10)
);

COMMENT ON TABLE public.report_schedule_definitions IS
    'CT-IMPLEMENT-02 (PD-2) — canonical scheduled-report definition. Tenant '
    'owned, engine-truthful report_type, explicit period configuration, '
    'recipient configuration, frequency + IANA timezone, explicit pause state, '
    'persisted execution/retry state. Execution produces a normal canonical '
    'report/version through the authoritative engine; the schedule never '
    'bypasses the report workflow. Audit linkage: every create/change/delete/run '
    'is appended to public.audit_trail with correlation_id = schedule id.';
COMMENT ON COLUMN public.report_schedule_definitions.recipients IS
    'Recipient configuration (non-empty JSON array). Each element names an '
    'authenticated user and/or an address; the runner validates each recipient '
    'against the organisation before delivery.';
COMMENT ON COLUMN public.report_schedule_definitions.retry_policy IS
    'Bounded retry policy: {"max_attempts": 1..10, "backoff_minutes": [...]}. '
    'Applied by the runner when a run fails.';
COMMENT ON COLUMN public.report_schedule_definitions.next_run_at IS
    'Persisted due time of the next run (UTC). The runner selects due schedules '
    'from this column, never from in-memory state.';


-- ---------------------------------------------------------------------------
-- 2. IANA timezone validation (fail closed; a CHECK cannot consult a catalogue)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.ct02_report_schedule_validate()
RETURNS trigger
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_timezone_names tz WHERE tz.name = NEW.timezone) THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2): % is not a known IANA timezone. A schedule '
            'must run in a real timezone, never in an implied one.',
            NEW.timezone
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.is_active AND NEW.next_run_at IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2): an active schedule must carry next_run_at; '
            'otherwise it can never become due.'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.ct02_report_schedule_validate() IS
    'CT-IMPLEMENT-02 (PD-2) — validates the IANA timezone against '
    'pg_timezone_names and requires a due time on an active schedule.';

DROP TRIGGER IF EXISTS ct02_report_schedule_validate
    ON public.report_schedule_definitions;
CREATE TRIGGER ct02_report_schedule_validate
    BEFORE INSERT OR UPDATE ON public.report_schedule_definitions
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_report_schedule_validate();

-- ---------------------------------------------------------------------------
-- 3. public.report_schedule_runs — one row per due-slot execution attempt
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_schedule_runs (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    schedule_id uuid NOT NULL
        REFERENCES public.report_schedule_definitions(id) ON DELETE CASCADE,
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    -- The due slot this attempt belongs to (not the wall-clock start time).
    scheduled_for timestamptz NOT NULL,
    attempt integer NOT NULL DEFAULT 1,
    status varchar(16) NOT NULL DEFAULT 'running',
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    -- The canonical artefacts the run produced, when it produced them.
    report_id uuid REFERENCES public.report_generation_queue(id) ON DELETE SET NULL,
    report_version_id uuid REFERENCES public.report_versions(id) ON DELETE SET NULL,
    result_summary jsonb,
    error_code text,
    error_message text,
    -- IDEMPOTENCY: one run row per (schedule, due slot), whatever the attempt.
    CONSTRAINT report_schedule_runs_slot_key UNIQUE (schedule_id, scheduled_for),
    CONSTRAINT report_schedule_runs_status_check
        CHECK (status IN ('running', 'succeeded', 'failed', 'skipped')),
    CONSTRAINT report_schedule_runs_attempt_check
        CHECK (attempt BETWEEN 1 AND 10),
    -- A finished run has a finish time.
    CONSTRAINT report_schedule_runs_finished_check
        CHECK (status = 'running' OR finished_at IS NOT NULL),
    -- A failure must be explainable at the database level too.
    CONSTRAINT report_schedule_runs_failure_described_check
        CHECK (status <> 'failed'
               OR (error_code IS NOT NULL AND btrim(error_code) <> '')),
    -- A skipped run must say why it was skipped (not reportable, not approved…).
    CONSTRAINT report_schedule_runs_skip_described_check
        CHECK (status <> 'skipped'
               OR (error_message IS NOT NULL AND btrim(error_message) <> '')),
    CONSTRAINT report_schedule_runs_summary_shape_check
        CHECK (result_summary IS NULL OR jsonb_typeof(result_summary) = 'object')
);

COMMENT ON TABLE public.report_schedule_runs IS
    'CT-IMPLEMENT-02 (PD-2) — append-only execution record for a scheduled '
    'report. Keyed by (schedule_id, scheduled_for), which makes execution '
    'idempotent per due slot: a repeated tick cannot create a second run or a '
    'duplicate report. Records the real outcome and the canonical '
    'report/version produced, or the failure/skip reason. Never updated except '
    'to move a running attempt to its terminal state.';


-- ---------------------------------------------------------------------------
-- 4. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_report_schedule_definitions_org
    ON public.report_schedule_definitions (organization_id);
CREATE INDEX IF NOT EXISTS idx_report_schedule_definitions_active
    ON public.report_schedule_definitions (next_run_at)
    WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_report_schedule_runs_schedule
    ON public.report_schedule_runs (schedule_id, scheduled_for DESC);
CREATE INDEX IF NOT EXISTS idx_report_schedule_runs_org
    ON public.report_schedule_runs (organization_id, scheduled_for DESC);

-- Runs are append-only in substance: an attempt may only be moved from
-- 'running' to a terminal state, and only once.
CREATE OR REPLACE FUNCTION public.ct02_report_schedule_run_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2): schedule run history is append-only; '
            'DELETE is not permitted.'
            USING ERRCODE = 'check_violation';
    END IF;

    IF OLD.status <> 'running' THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2): run % is already terminal (%); its record '
            'is immutable.', OLD.id, OLD.status
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.schedule_id       IS DISTINCT FROM OLD.schedule_id
       OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
       OR NEW.scheduled_for   IS DISTINCT FROM OLD.scheduled_for
       OR NEW.attempt         IS DISTINCT FROM OLD.attempt
       OR NEW.started_at      IS DISTINCT FROM OLD.started_at THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-2): a run''s identity and due slot are '
            'immutable.'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.ct02_report_schedule_run_guard() IS
    'CT-IMPLEMENT-02 (PD-2) — makes a schedule run append-only: no DELETE, and '
    'a run may only transition once, from running to a terminal state.';

DROP TRIGGER IF EXISTS ct02_report_schedule_run_guard
    ON public.report_schedule_runs;
CREATE TRIGGER ct02_report_schedule_run_guard
    BEFORE UPDATE OR DELETE ON public.report_schedule_runs
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_report_schedule_run_guard();

DROP TRIGGER IF EXISTS ct02_report_schedule_runs_no_truncate
    ON public.report_schedule_runs;
CREATE TRIGGER ct02_report_schedule_runs_no_truncate
    BEFORE TRUNCATE ON public.report_schedule_runs
    FOR EACH STATEMENT
    EXECUTE FUNCTION public.ct02_audit_truncate_guard();


-- ---------------------------------------------------------------------------
-- 5. RLS + privileges (canonical convention: RLS enabled, anon revoked,
--    authenticated granted exactly the DML its policies imply)
-- ---------------------------------------------------------------------------
ALTER TABLE public.report_schedule_definitions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.report_schedule_definitions FROM anon;
REVOKE ALL ON TABLE public.report_schedule_definitions FROM authenticated;
-- No DELETE for clients: deleting a schedule is an authority action that the
-- server performs and audits (PD-2 requires create/change/deletion auditing).
GRANT SELECT, INSERT, UPDATE ON TABLE public.report_schedule_definitions TO authenticated;

DROP POLICY IF EXISTS report_schedule_definitions_read
    ON public.report_schedule_definitions;
CREATE POLICY report_schedule_definitions_read
    ON public.report_schedule_definitions FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));

DROP POLICY IF EXISTS report_schedule_definitions_insert
    ON public.report_schedule_definitions;
CREATE POLICY report_schedule_definitions_insert
    ON public.report_schedule_definitions FOR INSERT TO authenticated
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

DROP POLICY IF EXISTS report_schedule_definitions_update
    ON public.report_schedule_definitions;
CREATE POLICY report_schedule_definitions_update
    ON public.report_schedule_definitions FOR UPDATE TO authenticated
    USING (public.p8_disclosure_is_org_admin(organization_id))
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

ALTER TABLE public.report_schedule_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.report_schedule_runs FROM anon;
REVOKE ALL ON TABLE public.report_schedule_runs FROM authenticated;
-- Runs are produced by the server scheduler; clients only read them.
GRANT SELECT ON TABLE public.report_schedule_runs TO authenticated;

DROP POLICY IF EXISTS report_schedule_runs_read ON public.report_schedule_runs;
CREATE POLICY report_schedule_runs_read
    ON public.report_schedule_runs FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));

DO $$
DECLARE
    role_name text;
BEGIN
    FOREACH role_name IN ARRAY ARRAY['service_role', 'postgres'] LOOP
        CONTINUE WHEN NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name);
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.report_schedule_definitions TO %s',
            quote_ident(role_name));
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE ON TABLE public.report_schedule_runs TO %s',
            quote_ident(role_name));
    END LOOP;
END $$;

COMMIT;

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [ ] tables report_schedule_definitions / report_schedule_runs exist
--   [ ] report_schedules and report_history are still ABSENT
--   [ ] RLS enabled on both; no anon/public policy or grant
--   [ ] unsupported report_type rejected; unknown frequency rejected
--   [ ] unknown IANA timezone rejected (trigger)
--   [ ] empty recipient list rejected; malformed retry policy rejected
--   [ ] duplicate (schedule_id, scheduled_for) rejected (idempotency)
--   [ ] runs reject UPDATE-after-terminal / DELETE / TRUNCATE
--   [ ] re-running this file is a no-op
-- ============================================================================

