-- P16-REMEDIATION-07 / P16-R7 — calculation idempotency.
--
-- Defect (P16-R6, reproduced in P16-R7): a repeat calculation for ONE source
-- item produced a SECOND reportable snapshot set, doubling the accounting total
-- (4175.903780 -> 8351.807560). Two batches eight seconds apart carried
-- DIFFERENT request ids: the automatic pipeline derives a deterministic
-- `uuid5(...)` request id (services/automatic_processing.py) and reuses the
-- existing snapshot via `find_snapshot_by_request_id`, but the manual ops routes
-- used a random `uuid4()` and never checked, so idempotency could not engage.
--
-- The architecture's intended contract is therefore: the request id is the
-- idempotency key. This migration makes a duplicate idempotency key structurally
-- impossible at the storage layer, closing the concurrency window that an
-- application-level lookup alone cannot (two simultaneous requests could both
-- miss a read-then-insert race).
--
-- Additive only: one partial unique index. No column, row, value, policy or
-- existing index is modified. Verified before creation: 32 snapshots, 32
-- distinct non-null request_id values, 0 duplicates.

CREATE UNIQUE INDEX IF NOT EXISTS uq_calc_snapshots_request_id
    ON public.calculation_snapshots (request_id)
    WHERE request_id IS NOT NULL;

COMMENT ON INDEX public.uq_calc_snapshots_request_id IS
    'P16-RD-7: the calculation request id is the idempotency key. One persisted snapshot per request id, so an identical repeat calculation cannot create a second reportable result.';
