# CarbonTally WS4 / Gate 3 — Workstream 4C Report
## Item-Level Processing Assignment — CarbonTally Operations HTTP/API Surface

- **Date:** 4 September 2026
- **Basis:** PO accepted Workstreams 4A (RLS) and 4B (service layer). This workstream exposes the approved CarbonTally Ops item-assignment capabilities over HTTP and finishes the PE `next-item`/legacy entity-listing consistency follow-ups.
- **Scope executed:** HTTP/API integration ONLY. No UI, no D40 notification changes, no workflow/calculation changes, no Gate 3 execution.
- **Environment:** local stack (API `127.0.0.1:8050`, Supabase `127.0.0.1:54425/54426`).
- **No commit/push was made.**

---

## 1. Implementation Summary

The existing D38 Ops routes
(`POST /api/v3/ops/items/{item_id}/work/{assign,reassign,recover}`) now accept a
Processing Entity target in addition to an internal-staff target, using the
canonical D38 service (`ops_assign_item` / `ops_reassign_item` /
`ops_recover_item`) so the API never touches `work_item_assignments` directly.
History inspection remains on the existing
`GET /api/v3/ops/items/{item_id}/work` (current + history + effective + origin).
PE `next-item` and the legacy ops-entity batch listing were aligned to the
item-level effective-assignment model.

## 2. Exact API Endpoints Added/Modified

| Endpoint | Method | Change |
| --- | --- | --- |
| `/api/v3/ops/items/{item_id}/work/assign` | POST | Request body now `{assigned_to | entity_id, reason}` — assign to internal staff OR a Processing Entity (CarbonTally internal staff only). |
| `/api/v3/ops/items/{item_id}/work/reassign` | POST | Same dual target (PE→PE, PE→Internal, Internal→PE). |
| `/api/v3/ops/items/{item_id}/work/recover` | POST | Same dual target. |
| `/api/v3/ops/items/{item_id}/work/claim` | POST | Unchanged (internal self-claim). |
| `/api/v3/ops/items/{item_id}/work/release` | POST | Unchanged (release; effective-aware). |
| `/api/v3/ops/items/{item_id}/work` | GET | Unchanged shape (current + history + `effective` + origin) — now reflects item-level state from 4B. |
| `/api/v3/ops/entities/{entity_id}/extraction/batches` | GET | Entity staff see batch-default batches PLUS batches carrying their item-level assignments. |
| `/api/v3/ops/entities/{entity_id}/extraction/next-item` | GET | Entity staff queue resolves effective item assignment (never another party's item). |

No new routes were added; existing D38 route paths were extended. FastAPI
OpenAPI is generated from these routers (schema shows the dual-target body).

## 3. Authorization Model

- All four mutation endpoints run through `require_staff` →
  `require_internal_staff` → `can_process`/`can_review` (`_require_work_mutation`).
  Processing-Entity staff are denied (403) even though they have staff profiles.
- Targets are validated server-side before any mutation: internal staff must be
  active (`is_active_internal_staff`); processing entities must exist and be
  `active` (`repos.entities.get`). Arbitrary/unknown UUIDs are rejected (422).

## 9. Audit Evidence

API-triggered assignment/reassignment produces the existing D38 audit events
(`work_item:assign`, `work_item:reassign`, `work_item:recover`) with the acting
internal staff user id, item id, previous/new assignment fields, entity/internal
target, reason and timestamp in `changed_fields`. Real-HTTP verification on the
reassigned fixture item confirmed exactly `work_item:assign` +
`work_item:reassign` recorded against the `staff-admin.demo` actor.

## 10. HTTP Security Test Matrix (real authenticated HTTP)

Disposable fixture (cleaned afterwards). Results from
`/tmp/w4c_api_verify_out3.txt` — **38 checks, 0 failures**:

| Test | Setup | Expected | Result |
| --- | --- | --- | --- |
| 1 | Batch default Alpha; item no override | Alpha ALLOW / Beta DENY | PASS |
| 2 | Batch default Alpha; item → Beta | Alpha DENY / Beta ALLOW | PASS |
| 3 | Batch default Alpha; item → Internal | Alpha/Beta DENY; internal start ALLOW | PASS |
| 4 | No default; no assignment | Alpha/Beta DENY | PASS |
| 5 | closed Alpha + open Beta (API reassign) | Alpha DENY / Beta ALLOW; single open; history recorded | PASS |
| 6 | Mixed one batch A(C Alpha) B(Beta) D(Internal) | Alpha A,C; Beta B; D hidden; next-item no cross-party leak | PASS |
| 7 | Ops assign item → Alpha | HTTP 200; Alpha ALLOW | PASS |
| 8 | Ops reassign Alpha → Beta | HTTP 200; Beta effective; Alpha loses access; single open | PASS |
| 9 | Ops PE → Internal | HTTP 200; PE loses access; internal start ALLOW | PASS |
| 10 | Ops Internal → PE | HTTP 200; PE becomes effective; internal start DENY | PASS |
| 11 | PE attempts Ops assign/reassign | 403 | PASS |
| 12 | Cross-PE enumeration (workspace/list/next-item/guessed ids) | DENY / no leak | PASS |

Audit check (assign + reassign, actor `staff-admin.demo`) — PASS.

## 11. Regression Results

Hermetic focused suite green after the API changes (46 tests):
`test_v3_work_item_effective_assignment.py` (10), `test_v3_entity_extraction.py`,
`test_v3_processing_workflow.py`, `test_v1_2_dual_origin_workflow.py` (5).
Existing single-party batch behaviour and PE/internal authorization paths are
unchanged (4B semantics).

## 12. Data Baseline / Cleanup

Pre-run baseline: 7,049 factors · 975 orgs · 260 items · 56 batches ·
work_item_assignments 0 · notifications 0 · conversations 34 · messages 52 ·
participants 62 · E2E users/profiles 0 · migrations 46.

Disposable fixture org/batches/items were fully removed; D38 test notifications
created by internal assignments (D40 existing behaviour) were removed as test
artifacts. Post-run counts returned exactly to baseline (orgs 975, items 260,
batches 56, ledger 0, notifications 0). No demo/investor data was mutated.

## 13. Remaining Work

- UI consumption of the new Ops item-assignment contract (separate workstream).
- D40 notification changes for entity-target assignments (kept separate, as
  instructed; internal-staff assignment notifications already flow via the
  existing idempotent mechanism).
- Targeted final verification and **Gate 3 execution** once PO accepts the API
  contract.

## 14. Gate Status

**Gate 3 remains BLOCKED pending final targeted verification and Gate 3
execution.** This workstream does not claim Gate 3 passed.

## Git

No commit/push. Repo changes: `backend/api/v3_operations.py`,
`backend/data/manual_extraction.py`, `backend/tests/unit/api/fakes.py`,
`backend/tests/unit/api/test_v3_work_item_effective_assignment.py` (kept from
4B), plus this report. OpenAPI is generated from the routers and now advertises
the dual-target body. Evidence under `/tmp/w4c_*`.

- PE and internal item-processing authorization uses the effective-assignment
  model from 4B (item-level overrides, batch default, else unassigned). No new
  role/capability was created.

## 4. Request/Response Contract

`WorkItemTarget` (assign/reassign/recover):

```json
{
  "assigned_to": "<internal staff user id>",   // XOR
  "entity_id":   "<processing entity id>",     // XOR
  "reason": "optional free text"
}
```

Exactly one of `assigned_to` / `entity_id` is required (422 otherwise).
Response mirrors the service result: `{item_id, current, changed}` plus
`current` = the new open D38 assignment row. `GET .../work` returns
`{item_id, batch_id, batch_entity_id, item_status, current, history, effective,
processing_origin, processing_entity_id}`.

## 5. D38 Integration

The endpoints call the 4B service functions only (no duplicated ledger logic).
The service closes any prior open assignment, opens the new one atomically
(`work_item_open` CTE), preserves `previous_assigned_to` /
`previous_processing_entity_id`, enforces the single-open invariant, records
actor attribution and audit events, and never writes `processing_origin`.

## 6. Effective Assignment Behavior

Responses distinguish item-level current assignment (`current`), batch default
(`batch_entity_id` / batch `assigned_to`), and `effective` (`kind`, `assignee`,
`source`) — all produced by the service representation from 4B. No second
calculation exists in the API layer.

## 7. PE Security

PE endpoints already filter by effective assignment (4B). This workstream also
made `next-item` and the legacy entity batch list effective-aware so a PE can
never be handed or enumerate another party's items through those paths. PE
users cannot invoke any Ops assignment/reassignment/recover endpoint (403).

## 8. Internal Processing Security

Internal item processing remains gated by `_ensure_internal_item_processing`
(4B): authorized internal staff can process an internally-assigned item even in
a PE-defaulted batch, and cannot process items effectively assigned to a PE.
