-- ============================================================
-- CarbonTally WS4 / Gate 3 — Workstream 4A: Item-level
-- processing-assignment foundation (DB + RLS only)
--
-- PO-approved decision (Option B of the WS4 Gate 3 Architecture
-- Reconciliation): effective processing assignment for a work item is
--   1. the item's open D38 work_item_assignments row if present;
--   2. else the batch-level default (manual_extraction_batches.entity_id /
--      assigned_to);
--   3. else unassigned.
--
-- This migration implements ONLY the database/RLS foundation:
--   * a SECURITY-DEFINER helper that resolves the item's effective PROCESSING
--     ENTITY from the open assignment ledger (processing_entity => entity;
--     internal_staff => NULL) falling back to the batch default;
--   * replacement of the PE item SELECT policy so PE access is granted per
--     ITEM on the item's effective entity - NOT merely because the item's
--     batch default belongs to the caller's entity.
--
-- Explicitly OUT of scope (later bounded workstreams): ops item assignment /
-- reassignment / recovery APIs, PE->PE or PE<->Internal reassignment routes,
-- UI, notifications, workflow, calculation/extraction changes, and Gate 3
-- execution.
--
-- The existing work_item_assignments schema is already sufficient to serve as
-- the canonical item-level current assignment (single-open partial unique
-- index, assignee_kind internal_staff|processing_entity, previous_* history
-- fields, close_action vocabulary). No second assignment table is created and
-- no assignment state is duplicated.
--
-- Forward-only and additive: existing rows, constraints, indexes and the
-- batch-level default fields (manual_extraction_batches.entity_id /
-- assigned_to) are preserved. Batch-level behaviour is unchanged when an item
-- has no item-level assignment. No business/demo/investor data is touched.
-- ============================================================

-- ---------------------------------------------------------------------------
-- 1. Effective processing-entity helper (RLS-safe, SECURITY DEFINER)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.work_item_effective_entity(p_item uuid)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $fn$
    SELECT CASE
        WHEN oa.id IS NULL THEN b.entity_id
        WHEN oa.assignee_kind = 'processing_entity' THEN oa.processing_entity_id
        ELSE NULL  -- open internal_staff assignment => not PE-visible
    END
    FROM public.manual_extraction_items i
    JOIN public.manual_extraction_batches b ON b.id = i.batch_id
    LEFT JOIN LATERAL (
        SELECT a.id, a.assignee_kind, a.processing_entity_id
          FROM public.work_item_assignments a
         WHERE a.manual_extraction_item_id = i.id
           AND a.status = 'open'
         ORDER BY a.created_at DESC, a.id DESC
         LIMIT 1
    ) oa ON TRUE
    WHERE i.id = p_item;
$fn$;

COMMENT ON FUNCTION public.work_item_effective_entity(uuid) IS
    'WS4 Gate 3 / 4A: effective processing entity for a manual-extraction work '
    'item = open processing_entity assignment, else open internal_staff '
    'assignment (=> NULL, internal overrides batch default), else batch '
    'default entity_id, else NULL (unassigned). Processing origin is never '
    'read or written here.';

REVOKE ALL ON FUNCTION public.work_item_effective_entity(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.work_item_effective_entity(uuid)
    TO authenticated, service_role;


-- ---------------------------------------------------------------------------
-- 2. PE item SELECT policy — item-level effective assignment
-- ---------------------------------------------------------------------------
-- Replaces the D22 policy that granted PE staff SELECT on every item of a
-- batch whose entity_id matched their entity. A PE may now SELECT an item only
-- when the item's EFFECTIVE processing entity is an entity the caller belongs
-- to. This is the key same-batch isolation correction:
--
--   Batch default Alpha, Item B overridden to Beta:
--     Alpha DENY  (effective entity of Item B is Beta)
--     Beta  ALLOW
--
-- Historical (closed) ledger rows never grant current access because the
-- helper only reads the single OPEN row.
--
-- The table keeps NO other authenticated policy (deny-by-default for
-- customer/consultant/internal direct reads, unchanged).
DROP POLICY IF EXISTS manual_extraction_items_entity_select
    ON public.manual_extraction_items;

CREATE POLICY manual_extraction_items_entity_select
    ON public.manual_extraction_items
    FOR SELECT TO authenticated
    USING (
        public.work_item_effective_entity(id) IS NOT NULL
        AND public.is_entity_member(public.work_item_effective_entity(id))
    );

-- ---------------------------------------------------------------------------
-- 3. Verification checklist (4A)
--   [x] work_item_effective_entity(uuid) created (STABLE, SECURITY DEFINER,
--       search_path pinned); PUBLIC revoked; authenticated + service_role
--       granted
--   [x] manual_extraction_items_entity_select now predicates on the item's
--       effective processing entity
--   [x] manual_extraction_batches_entity_select UNCHANGED (batch default
--       container view preserved)
--   [x] manual_extraction_items has NO other authenticated policy
--   [x] work_item_assignments remains RLS-on / no-policy / API-only; no grants
--       to authenticated; no second assignment table created
--   [x] processing_origin columns untouched; no data row modified
--   [x] Idempotent: CREATE OR REPLACE FUNCTION + DROP POLICY IF EXISTS /
--       CREATE POLICY
-- ============================================================================

