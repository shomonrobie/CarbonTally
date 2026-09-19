-- ============================================================================
-- CarbonTally — F-039-1: ONE ADJUDICATION LINEAGE PER BOUNDED CONTEXT
-- File: 20260931000000_p8_fs_adjudication_context_lineage.sql
--
-- PURPOSE (PO DECISION D-F039-1-J, ratified 2026-09-19)
--   "For every F-039-1 bounded context, CarbonTally shall maintain exactly one
--    adjudication lineage. That lineage may contain multiple immutable versions
--    over time, but there shall be exactly one effective/current version at a
--    time. Concurrent clarification attempts for the same bounded context must
--    converge into that same lineage rather than creating independent lineages."
--
-- WHY THE EXISTING INDEX IS NOT ENOUGH
--   ``activity_clarifications_current_unique`` is UNIQUE(adjudication_id) WHERE
--   is_current — it bounds current rows WITHIN one lineage, so it cannot stop a
--   writer from starting a SECOND lineage for the same context. A current row is
--   exactly the row that carries the bounded context, so uniqueness of
--   (organization_id, effective_context_key, activity_key, original_activity)
--   among current rows is the database-level statement of D-F039-1-J.
--
-- BOUNDED CONTEXT (existing semantics, unchanged — the same four columns the
-- effective read has always used):
--   organization_id · effective_context_key · activity_key · original_activity
--
-- WHAT THIS MAKES IMPOSSIBLE
--   two current rows for one bounded context ⇒ no second lineage can be
--   committed, on any path (repository, service, script or future code). A
--   concurrent loser blocks on the index and then fails loudly instead of
--   silently forking; the repository converges it into the winning lineage.
--
-- SAFETY
--   * additive: it adds ONE index; no column, table, policy, grant or row changes;
--   * fail-safe: a bounded context that already has more than one current row is
--     refused with an explicit message BEFORE the index is attempted — no data is
--     deleted, merged or rewritten, and no reconciliation policy is invented here;
--   * idempotent: safe to re-apply.
--
-- STATUS: applied and verified ONLY in disposable test databases. NEVER applied to
--   production by this change; production promotion is a separate release action.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Pre-flight (non-destructive): refuse if the data cannot satisfy the index
-- ---------------------------------------------------------------------------
DO $$
DECLARE dup_contexts integer;
BEGIN
    SELECT count(*) INTO dup_contexts
      FROM (
            SELECT 1
              FROM public.activity_clarifications
             WHERE is_current
             GROUP BY organization_id, effective_context_key, activity_key, original_activity
            HAVING count(*) > 1
           ) AS duplicated;

    IF dup_contexts > 0 THEN
        RAISE EXCEPTION
            'D-F039-1-J pre-flight: % bounded context(s) already have more than one '
            'current adjudication row. Resolve them under a PO decision before applying '
            'this uniqueness index; this migration never deletes, merges or rewrites rows.',
            dup_contexts;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. One current row per bounded context (D-F039-1-J)
-- ---------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS activity_clarifications_context_unique
    ON public.activity_clarifications
       (organization_id, effective_context_key, activity_key, original_activity)
    WHERE is_current;

COMMENT ON INDEX public.activity_clarifications_context_unique IS
    'D-F039-1-J: at most one current (effective) adjudication row per bounded '
    'context ⇒ exactly one adjudication lineage per bounded context.';
