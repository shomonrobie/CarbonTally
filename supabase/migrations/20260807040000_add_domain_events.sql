-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M5 of 8
-- File: 20260807040000_add_domain_events.sql
--
-- Append-only domain event store (Backend v2.1 §14 Workflow & Event Platform).
--
-- Design:
--   * Written by the EventBus on every publish; read by audit and replay.
--   * Never updated or deleted (append-only).
--   * correlation_id links all events originating from one API request.
--   * aggregate_type/aggregate_id identify the business entity (e.g.
--     document/customer_documents/<uuid>).
--   * payload JSONB holds the typed event fields.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.domain_events (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    event_type VARCHAR NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id UUID NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_domain_events_correlation
    ON public.domain_events (correlation_id);

CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate
    ON public.domain_events (aggregate_type, aggregate_id);

COMMENT ON TABLE public.domain_events IS
    'Append-only domain event store. Written by the EventBus, read by audit and replay (Backend v2.1 §14).';
COMMENT ON COLUMN public.domain_events.correlation_id IS
    'Links every event triggered by a single API request (equals the request id).';
COMMENT ON COLUMN public.domain_events.payload IS
    'Typed event fields serialized as JSON (matches the concrete DomainEvent subclass).';

-- ============================================================================
-- VERIFICATION CHECKLIST (M5)
--   [ ] Table exists in public schema
--   [ ] Index on correlation_id exists
--   [ ] Index on (aggregate_type, aggregate_id) exists
--   [ ] payload NOT NULL JSONB
--   [ ] Re-running this file is a no-op
-- ============================================================================
