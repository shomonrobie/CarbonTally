-- ============================================================================
-- CarbonTally Phase 8 — Insight data quality + audit/reproducibility (P3).
-- File: 20261007000000_p8_insight_data_quality_reproducibility.sql
--
-- ORDERING (MIG-1 remediation, 2026-09-23): this file was originally named
--   20260923000000_... and therefore sorted BEFORE 20261003000000 (which creates
--   public.carbontally_insight_tool_calls) and before 20261006000000 (the P2
--   widening it builds on). On a genuinely fresh chain it failed on a missing
--   relation, and the later-sorting migrations narrowed the constraint back to
--   eight names. The 20261007000000 prefix places it after every migration it
--   depends on and after the last migration in the repository
--   (20261006000000_p8_insight_temporal_comparison.sql). No statement changed.
--
-- AUTHORITY
--   * PO P3 implementation authorization (2026-09-23): bounded data-quality and
--     audit/reproducibility Insight capabilities (capability families 14 and 16).
--   * PO Insight Capability Coverage Matrix (P1) family 14 / family 16, package P3.
--   * Preflight record CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922
--     §21 (U4): the I4 CHECK constraints hard-code the ratified tool and answer
--     vocabularies, so an authorized catalogue expansion requires the narrowest
--     possible widening here and nothing else.
--
-- SCOPE (additive, idempotent, no data change)
--   widen ci_tool_calls_tool_name_check to the ten authorized tool names.
--
-- EXPLICIT NON-SCOPE
--   No new table, no new column, no new index, no answer-state change (the I4
--   vocabulary is untouched — every P3 semantic is expressed with the existing
--   states plus result fields), no RLS change, no accounting dimension, no
--   quality-score table, no analytics warehouse, no duplicate provenance or audit
--   store, no I7 retention/deletion work, no I8 commercial concept, no data
--   backfill and no destructive statement.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. The authorized I3 tool catalogue — the four PO-ratified read-only tools, the
--    three Phase 8 analytics tools (2026-09-22), the P2 temporal-comparison tool
--    (2026-09-22) and the two P3 quality/reproducibility tools (2026-09-23).
--    Widened in place: the constraint name and enforcement point are unchanged,
--    and an unratified name still cannot be persisted.
-- ----------------------------------------------------------------------------
ALTER TABLE public.carbontally_insight_tool_calls
    DROP CONSTRAINT IF EXISTS ci_tool_calls_tool_name_check;

ALTER TABLE public.carbontally_insight_tool_calls
    ADD CONSTRAINT ci_tool_calls_tool_name_check
        CHECK (tool_name IN ('report_lookup', 'report_version_lookup',
                             'report_evidence_lookup', 'calculation_snapshot_lookup',
                             'insight_discovery', 'insight_aggregation',
                             'insight_aggregate_provenance',
                             'insight_temporal_comparison',
                             'insight_data_quality',
                             'insight_calculation_reproducibility'));

COMMENT ON CONSTRAINT ci_tool_calls_tool_name_check
    ON public.carbontally_insight_tool_calls IS
    'The authorized I3 tool catalogue: the four PO-ratified read-only tools, the three Phase 8 analytics tools and the P2 temporal-comparison tool (2026-09-22), and the two P3 data-quality / audit-reproducibility tools (2026-09-23). An unratified name can never be persisted.';
