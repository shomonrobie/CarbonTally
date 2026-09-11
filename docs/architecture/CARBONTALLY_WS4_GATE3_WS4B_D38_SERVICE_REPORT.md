# CarbonTally WS4 / Gate 3 — Workstream 4B Report
## D38 Item-Level Processing Assignment — Service Layer + Application Authorization

- **Date:** 3 September 2026
- **Basis:** PO accepted Workstream 4A; approved rule: effective processing assignment = open item-level D38 assignment → batch default → unassigned.
- **Scope executed:** service-layer + application-authorization extension ONLY. No new HTTP endpoints, no UI, no notifications, no workflow/calculation changes, no Gate 3 execution.
- **Environment:** local stack (Supabase Postgres `127.0.0.1:54426`, API `127.0.0.1:8050`).
- **No commit/push was made.**

---

## 1. Implementation Summary

The D38 service and the PE/Ops item-processing authorization paths now resolve
the item's **effective** processing assignment (open D38 ledger row first,
batch default second, else unassigned) instead of authorizing purely from
`manual_extraction_batches.entity_id`. The batch fields are retained as the
operational **default**. The RLS helper created in 4A
(`public.work_item_effective_entity`) is mirrored in the service layer so RLS
and service agree. `work_item_assignments` remains the single canonical
assignment ledger; `processing_origin` is never written by the assignment
service.

## 2. Exact Files Changed

| File | Change |
| --- | --- |
| `backend/services/work_items.py` | Added `work_item_effective()`; extended `ops_assign_item()` to accept a **processing-entity target** (in addition to internal staff) with active-entity validation and idempotency; `ops_reassign_item`/`ops_recover_item` gained entity targets; `_ops_close`/`ops_complete_item` now deny only effectively-PE items; `_pe_entity_item` now requires the item's **effective** entity; `work_item_read` exposes an `effective` summary. |
| `backend/data/manual_extraction.py` | Added `work_item_effective_entity()` (calls the 4A SQL helper), `effective_entity_map(batch_id)` (single-query per-batch effective map), `list_batches_with_open_entity_item(entity_id)`. |
| `backend/api/v3_pe.py` | `_ensure_assigned_item()` resolves effective entity; `_ensure_assigned_batch()` allows the batch default OR batches containing an item-level open assignment for the entity; `/work` includes item-assignment batches and counts only effective items; `/batches/{id}/items` returns only items effectively assigned to the caller PE. |
| `backend/api/v3_operations.py` | Added `_ensure_internal_item_processing()` (item-level internal gate) and switched internal start/extract/map/calculate processing to it; `_entity_checked_item()` is effective-aware for entity staff; `entity_extraction_batch_items()` filters to effective items for entity staff. |
| `backend/tests/unit/api/fakes.py` | In-memory D38 ledger + effective-assignment mirror (`work_item_current/open/close/history`, `work_item_effective_entity`, `effective_entity_map`, `list_batches_with_open_entity_item`, `get_item_origin`, `is_active_internal_staff`/seed helper). |
| `backend/tests/unit/api/test_v3_work_item_effective_assignment.py` | **New** — 10 focused service tests (Cases 1–10). |


## 3. D38 Changes

- `ops_assign_item` now supports **either** an internal-staff user
  (`target_user_id`) **or** a processing entity (`target_entity_id`); exactly
  one is required (422 otherwise). Entity targets are validated against the
  processing-entities repository (must exist and be `active`). The previous
  blanket denial for items in PE-defaulted batches was removed because a
  CarbonTally item-level assignment is exactly the mechanism that overrides the
  batch default.
- Reassignment (`ops_reassign_item`, `ops_recover_item`) closes the current
  open assignment and opens the new one **atomically** through the existing
  `work_item_open` CTE — preserving `previous_assigned_to`,
  `previous_processing_entity_id`, the single-open partial unique index
  invariant, actor attribution (`assigned_by`, `actor_domain`), append-only
  history and audit events (`work_item:assign` / `work_item:reassign` /
  `work_item:recover`).
- PE domain behaviour preserved: `pe_claim_item`/`pe_release_item`/
  `pe_complete_item` remain; `pe_claim_item` has no target parameter and PE
  reassignment remains impossible (no route/service path).

## 4. PE Authorization Changes

- `v3_pe._ensure_assigned_item` and service `_pe_entity_item` now authorize only
  when `work_item_effective_entity(item) == caller entity`. A PE can no longer
  reach an item merely because `batch.entity_id == caller entity` when an
  item-level override (Beta) or an internal override exists.
- PE batch item lists (`/pe/batches/{id}/items` and the ops entity workspace
  list) return **only items effectively assigned to the caller PE**; the PE
  `/work` queue includes batches that only carry the PE's item-level
  assignments and reports item counts by effective assignment.
- Service cases enforced: batch default Alpha / item Beta → Alpha DENY, Beta
  ALLOW; item Internal → both DENY; unassigned → both DENY; closed Alpha + open
  Beta → Alpha DENY, Beta ALLOW.

## 5. Internal Authorization Changes

- New `_ensure_internal_item_processing` gate: CarbonTally internal staff may
  process an item when its effective assignment is internal — including an open
  item-level `internal_staff` assignment **inside a PE-defaulted batch** (4B
  rule) — and are denied when the item is effectively assigned to a Processing
  Entity. Internal batches keep the existing assignee/self-serve behaviour.
- Internal start/extract/map/calculate now call this gate; validation/review
  `allow_entity_gate` semantics are preserved.

## 6. Batch Default Behavior

Unchanged default semantics: a batch with `entity_id`/`assigned_to` and no
item-level override still behaves exactly as before (single-party batch). The
batch fields remain the operational default and were not removed or redesigned.

## 7. Processing-Origin Preservation

The D38 service never writes `manual_extraction_items.processing_origin` /
`processing_entity_id`. Real-DB verification: an item with
`processing_origin = PROCESSING_ENTITY / Alpha` reassigned Alpha → Beta kept its
origin unchanged while its current assignment became Beta.


## 8. Security Test Matrix (ALLOW/DENY results)

Hermetic service tests (10/10 PASS) plus real-DB endpoint verification
(`/tmp/w4b_db_verify_out2.txt`):

| Case | Setup | Expected | Result |
| --- | --- | --- | --- |
| 1 | Batch default Alpha, no override | Alpha ALLOW / Beta DENY | PASS |
| 2 | Batch default Alpha, item → Beta | Alpha DENY / Beta ALLOW | PASS |
| 3 | Batch default Alpha, item → Internal | Alpha DENY / Beta DENY | PASS |
| 4 | No default, no assignment | Alpha DENY / Beta DENY | PASS |
| 5 | closed Alpha + open Beta | Alpha DENY / Beta ALLOW | PASS |
| 6 | One batch A(Alpha) B(Beta) C(Alpha) D(Internal) | Alpha A,C / Beta B / D none | PASS |
| 7 | Reassign Alpha → Beta | after: Alpha DENY, Beta ALLOW; history recorded | PASS |
| 8 | Single-open invariant | exactly one open assignment after reassign | PASS |
| 9 | PE cannot reassign / reach other-entity control | denied (403 semantics) | PASS |
| 10 | Origin immutability | item unchanged by D38 service; DB origin preserved | PASS |

Real-DB endpoint checks also passed: Alpha sees A,C (200); Beta sees B (200);
Alpha sees no items in the reassigned batch (200, empty); Beta sees the
reassigned item; Alpha claim/start on Beta/internal items 403; internal operator
`start` on an internal item inside a PE-defaulted batch 200.

## 9. Regression Results

`pytest` (hermetic) — all green after the changes:
- `tests/unit/domain/test_v1_2_dual_origin_workflow.py` — 5 passed
- `tests/unit/api/test_v3_entity_extraction.py` — passed
- `tests/unit/api/test_v3_processing_workflow.py` — passed
- `tests/unit/api/test_v3_work_item_effective_assignment.py` — 10 passed (new)

46 tests green in the focused run. Existing single-party batch behaviour
continues to work (default-only items remain visible/processable by the default
PE; internal batches behave as before).

## 10. Data Baseline / Cleanup

Pre-run baseline: 7,049 factors · 975 orgs · 260 items · 56 batches ·
work_item_assignments 0 · conversations 34 · messages 52 · participants 62 ·
notifications 0 · E2E users/profiles 0 · migrations 46.

A disposable fixture was created for real-DB verification and fully removed
(including the leftover from the first interrupted verification run). Post-run
counts returned to baseline exactly: orgs 975, items 260, batches 56,
work_item_assignments 0, notifications 0. No demo/investor data was mutated.

## 11. Remaining Limitations

- The **HTTP/API surface** for CarbonTally item assignment/reassignment to a PE
  (payload/route exposure of the new service capabilities) is intentionally NOT
  implemented in this workstream — the next workstream owns it. The service
  functions are directly tested here.
- PE `next-item` queueing and legacy ops-entity listing still derive container
  context from batch defaults for non-PE callers; item-level filtering is
  applied wherever PE users read items. Minor follow-ups belong to the API/UI
  workstream.
- D40 notifications for entity-target assignments were not added (entity
  assignments emit no notification; internal-staff assignments retain the
  existing idempotent notification).

## 12. Gate Status

**Gate 3 remains BLOCKED.** This workstream does not claim Gate 3 passed; the
API surface (Workstream 4C+) and final Gate 3 execution are still required.

## Git

No commit/push. Repo changes: backend service/repo/api files listed in §2, the
new unit test, the fakes extension, and this report. Evidence under
`/tmp/w4b_*`.
