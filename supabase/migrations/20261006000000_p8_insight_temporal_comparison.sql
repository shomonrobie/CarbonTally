-- ============================================================================
-- CarbonTally Phase 8 — Insight Temporal Comparison (P2, capability family 11).
-- File: 20261006000000_p8_insight_temporal_comparison.sql
--
-- AUTHORITY
--   * PO P2 implementation authorization (2026-09-22): bounded temporal
--     comparison of two explicitly defined periods on the authoritative kg CO2e
--     basis, adding exactly ONE tool to the authorized I3 catalogue.
--   * PO Insight Capability Coverage Matrix (P1) family 11 and package P2.
--   * Preflight record CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922
--     §21 (U4): the I4 CHECK constraints hard-code the ratified tool and answer
--     vocabularies, so an authorized catalogue expansion requires the narrowest
--     possible widening here and nothing else.
--
-- SCOPE (additive, idempotent, no data change)
--   widen ci_tool_calls_tool_name_check to the eight authorized tool names.
--
-- EXPLICIT NON-SCOPE
--   No new table, no new column, no new index, no answer-state change (the I4
--   vocabulary is untouched: a zero-baseline comparison is expressed with the
--   existing states plus a result field, never a new state), no RLS change, no
--   accounting dimension, no analytics cache, no materialized view, no I7
--   retention/deletion work, no I8 commercial concept, no data backfill and no
--   destructive statement.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. The authorized I3 tool catalogue — the four PO-ratified read-only tools,
--    the three Phase 8 analytics tools (2026-09-22) and the P2 temporal
--    comparison tool (2026-09-22). Widened in place: the constraint name and
--    enforcement point are unchanged, and an unratified name still cannot be
--    persisted.
-- ----------------------------------------------------------------------------
ALTER TABLE public.carbontally_insight_tool_calls
    DROP CONSTRAINT IF EXISTS ci_tool_calls_tool_name_check;

ALTER TABLE public.carbontally_insight_tool_calls
    ADD CONSTRAINT ci_tool_calls_tool_name_check
        CHECK (tool_name IN ('report_lookup', 'report_version_lookup',
                             'report_evidence_lookup', 'calculation_snapshot_lookup',
                             'insight_discovery', 'insight_aggregation',
                             'insight_aggregate_provenance',
                             'insight_temporal_comparison'));

COMMENT ON CONSTRAINT ci_tool_calls_tool_name_check
    ON public.carbontally_insight_tool_calls IS
    'The authorized I3 tool catalogue: the four PO-ratified read-only tools, the three Phase 8 analytics tools (2026-09-22) and the P2 bounded temporal comparison tool (2026-09-22). An unratified name can never be persisted.';
