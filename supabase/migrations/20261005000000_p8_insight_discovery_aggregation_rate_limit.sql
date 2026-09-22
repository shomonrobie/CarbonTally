-- ============================================================================
-- CarbonTally Phase 8 — Insight Discovery / Aggregation / Provenance /
-- Rate limiting (bounded analytics foundation).
-- File: 20261005000000_p8_insight_discovery_aggregation_rate_limit.sql
--
-- AUTHORITY
--   * PO Insight Discovery-Aggregation-Provenance-RateLimiting implementation
--     authorization (2026-09-22), bounded by the PO decision matrix:
--       D-01 authoritative data → deterministic computation → evidence →
--            LLM narration (the model is never a query engine);
--       D-02 bounded discovery (zero / one / multiple matches);
--       D-03 bounded aggregation over fixed allowlisted dimensions;
--       D-10 aggregate → bounded contributing calculation records;
--       D-14 technical rate limiting (NOT commercial billing/entitlement).
--   * Preflight record CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922
--     §8.1/§21 (U4): the I4 CHECK constraints hard-code the ratified tool and
--     answer vocabularies, so the authorized catalogue/state expansion requires
--     the narrowest possible widening here and nothing else.
--
-- SCOPE (additive, idempotent, no data change)
--   1. widen ci_tool_calls_tool_name_check to the seven authorized tool names;
--   2. widen ci_interactions_answer_status_check by exactly one authorized state
--      (multiple_matches) — the I3 six-value tool_status vocabulary is unchanged;
--   3. create the two shared rate-limit / concurrency tables the limiter needs.
--
-- EXPLICIT NON-SCOPE
--   No new business tables, no calculation/reporting change, no RLS policy
--   change on existing tables, no retention/I7 work, no billing/entitlement
--   concept (the limiter tables hold counters and timestamps only), no change to
--   the I1/I2/I3/I5/I6 tables, no data backfill, no destructive statement.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. The authorized I3 tool catalogue (four ratified + three analytics tools).
--    Widened in place: the constraint name and enforcement point are unchanged.
-- ----------------------------------------------------------------------------
ALTER TABLE public.carbontally_insight_tool_calls
    DROP CONSTRAINT IF EXISTS ci_tool_calls_tool_name_check;

ALTER TABLE public.carbontally_insight_tool_calls
    ADD CONSTRAINT ci_tool_calls_tool_name_check
        CHECK (tool_name IN ('report_lookup', 'report_version_lookup',
                             'report_evidence_lookup', 'calculation_snapshot_lookup',
                             'insight_discovery', 'insight_aggregation',
                             'insight_aggregate_provenance'));

COMMENT ON CONSTRAINT ci_tool_calls_tool_name_check
    ON public.carbontally_insight_tool_calls IS
    'The authorized I3 tool catalogue: the four PO-ratified read-only tools plus the three Phase 8 analytics tools authorized on 2026-09-22. An unratified name can never be persisted.';

-- ----------------------------------------------------------------------------
-- 2. The I4 answer vocabulary — fourteen Master Spec §14 states plus exactly one
--    authorized analytics state (multiple_matches). No other value is added.
-- ----------------------------------------------------------------------------
ALTER TABLE public.carbontally_insight_interactions
    DROP CONSTRAINT IF EXISTS ci_interactions_answer_status_check;

ALTER TABLE public.carbontally_insight_interactions
    ADD CONSTRAINT ci_interactions_answer_status_check
        CHECK (answer_status IS NULL OR answer_status IN (
            'success', 'zero', 'no_data', 'not_authorized', 'insufficient_data',
            'needs_clarification', 'tool_failure', 'provider_unavailable',
            'partial', 'rate_limited', 'refused', 'ungrounded',
            'invalid_input', 'error', 'multiple_matches'));

COMMENT ON CONSTRAINT ci_interactions_answer_status_check
    ON public.carbontally_insight_interactions IS
    'I4 answer states: the fourteen Master Spec §14 states (PO Q3) plus multiple_matches (PO Insight analytics authorization 2026-09-22). Several authoritative records matched; the system asks which one instead of choosing.';

-- ----------------------------------------------------------------------------
-- 3. Shared Insight execution rate-limit state (technical abuse protection).
--
--    Why PostgreSQL: the API runs behind multiple workers/instances, so a
--    process-local counter would let a caller multiply its allowance. Each
--    transition is a single atomic statement in the repository (see
--    ``data/insight_rate_limit.py``), so concurrent workers cannot interleave.
--
--    These tables are operational counters: no question text, no customer data,
--    no commercial entitlement, no billing meaning of any kind.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.insight_rate_limit_buckets (
    scope              text        NOT NULL,
    scope_key          text        NOT NULL,
    tokens             numeric     NOT NULL,
    capacity           integer     NOT NULL CHECK (capacity >= 1),
    refill_per_second  numeric     NOT NULL CHECK (refill_per_second > 0),
    updated_at         timestamptz NOT NULL DEFAULT NOW(),
    denied_count       bigint      NOT NULL DEFAULT 0 CHECK (denied_count >= 0),
    last_denied_at     timestamptz,
    CONSTRAINT insight_rate_limit_buckets_pkey PRIMARY KEY (scope, scope_key),
    CONSTRAINT insight_rate_limit_buckets_scope_check CHECK (scope IN ('user', 'org'))
);

COMMENT ON COLUMN public.insight_rate_limit_buckets.scope_key IS
    'The authenticated user id (scope=user) or organization id (scope=org). Never accepted from a request body in a way that could raise a limit.';

CREATE INDEX IF NOT EXISTS insight_rate_limit_buckets_updated_at_idx
    ON public.insight_rate_limit_buckets (updated_at);

CREATE TABLE IF NOT EXISTS public.insight_concurrency_leases (
    scope             text        NOT NULL,
    scope_key         text        NOT NULL,
    in_flight         integer     NOT NULL DEFAULT 0 CHECK (in_flight >= 0),
    max_concurrent    integer     NOT NULL CHECK (max_concurrent >= 1),
    lease_expires_at  timestamptz,
    updated_at        timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT insight_concurrency_leases_pkey PRIMARY KEY (scope, scope_key),
    CONSTRAINT insight_concurrency_leases_scope_check CHECK (scope IN ('user', 'org'))
);

COMMENT ON COLUMN public.insight_concurrency_leases.lease_expires_at IS
    'When the current holders are assumed dead; an expired lease is reclaimed by the next acquire.';

CREATE INDEX IF NOT EXISTS insight_concurrency_leases_expiry_idx
    ON public.insight_concurrency_leases (lease_expires_at);

-- Service-role-only operational state: RLS enabled with no policy, exactly like
-- the other Insight tables, so anon/authenticated PostgREST roles can neither
-- read nor write it. The API reaches it through the service-role pool only.
ALTER TABLE public.insight_rate_limit_buckets     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insight_concurrency_leases     ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.insight_rate_limit_buckets IS
    'Token bucket per (scope, key) for customer-facing Insight execution: sustained requests_per_minute with a bounded burst allowance. Technical abuse protection only — never a commercial entitlement or billing signal. RLS is enabled with no policy: service-role access only.';
COMMENT ON TABLE public.insight_concurrency_leases IS
    'In-flight Insight execution counter per (scope, key) with a lease expiry, so a crashed worker cannot permanently hold capacity. RLS is enabled with no policy: service-role access only.';
