# CarbonTally WS4 / Gate 3 — Workstream 4D Report
## Item Assignment UI + Integration Preparation

- **Date:** 4 September 2026
- **Basis:** PO accepted Workstreams 4A (RLS), 4B (D38 service) and 4C (HTTP/API). This workstream made the existing CarbonTally Operations UI consume the approved 4C item-level assignment contract and verified the UI does not reintroduce batch-level assumptions.
- **Scope:** frontend/integration only, plus one small backend SQL fix discovered while verifying the PE UI path (see §6). No new UI system, no new assignment data model, no D40 notification work, no workflow/origin changes, no migration. Gate 3 was NOT executed.
- **Environment:** local stack (API `127.0.0.1:8050`, Supabase `127.0.0.1:54425/54426`).
- **No commit/push was made.**

---

## 1. Implementation Summary

The existing **Operations → Assignments** surface (`frontend/src/v3/ops/OpsAssignmentsTab.jsx`, already mounted as an Operations tab for internal staff with `can_process`/`can_review`) was updated to consume the **4C dual-target D38 contract**: an authorised CarbonTally Operations user can now assign an individual work item to a **Processing Entity** or to **CarbonTally internal staff** and reassign between them (PE→PE, PE→Internal, Internal→PE). The row rendering shows the three canonical layers — **batch default**, **item assignment**, **effective processor** — using the API's own `effective` summary (never a frontend re-derivation). A mixed batch therefore renders per-item processors instead of implying one batch party.

The internal item workspace deep-link was preserved/extended (returns to the tab the item was opened from), the PE application was verified to be free of Operations assignment controls, and the PE `/work` listing defect that surfaced during verification was fixed at the source.

## 2. Existing UI Surface Used

- **Operations hub** `frontend/src/v3/ops/OperationsPage.jsx` — tab navigation (Assignments tab already gated to internal `can_process`/`can_review`; PE profiles are redirected to `/pe` before any Operations tab renders).
- **Operations Assignments tab** `frontend/src/v3/ops/OpsAssignmentsTab.jsx` (the existing D38 work-item surface) — reused its batch-directory → per-batch-items structure, D21 primitives (`DataTable`, `Button`, `Alert`, `LoadingState`), `v3-ops`/`v12` styling and its existing claim/release/complete controls. No redesign.
- **Internal item workspace route** `frontend/src/v3/ops/OperatorItemPage.jsx` — existing routed workspace for internal processing (used as the “Open item” deep link).
- **PE application** `frontend/src/v3/pe/PeWorkItemsPage.jsx`, `PEDedicatedHome.jsx` — unchanged surfaces; verified they have no reassignment controls.
- **API client** `frontend/src/v3/api.js` — existing V3 fetch layer (`v3Fetch`) reused; no direct Supabase table access anywhere.

## 3. UI Changes

| File | Change |
| --- | --- |
| `frontend/src/v3/ops/OpsAssignmentsTab.jsx` | Assignment surface now supports PE + internal targets; batch directory composes internal/unassigned batches (operator queue) **and** batches defaulted to each active Processing Entity (`/api/v3/ops/entities?status=active` + per-entity extraction batch listing), so PE-defaulted and mixed batches are visible to Ops. Per-row “Assign to me”, PE select + apply, internal staff select + apply (assign when no open assignment, reassign when one exists), Release/Complete (disabled for items effectively assigned to a PE, matching server semantics), expandable history, and an **Open item** link to the internal workspace. Effective assignment is displayed verbatim from `GET /api/v3/ops/items/{id}/work`.
| `frontend/src/v3/api.js` | Added `opsWorkAssignTarget(itemId, {assigned_to|entity_id})` and `opsWorkReassignTarget(...)` (exactly-one-target payloads hitting the 4C `/work/assign` and `/work/reassign` endpoints); extended `listProcessingEntities(limit, offset, status)` so the UI can request **active** entities only.
| `frontend/src/v3/ops/OperatorItemPage.jsx` | “Back to queue” now returns to the originating tab (`?tab=` default data-entry) so items opened from the Assignments surface return there (CL-59 pattern).
| `frontend/src/v3/pe/PeWorkItemsPage.jsx` | Comment-only clarification (item-level assignments are governed by CarbonTally Operations; PE-initiated reassignment controls remain absent). No functional change.

No new routes, no new tabs, no new visual system, and no frontend authorization layer were introduced.

## 4. API Integration

Every mutation uses the existing 4C endpoints:

- `POST /api/v3/ops/items/{id}/work/assign` (PE `entity_id` or internal `assigned_to`)
- `POST /api/v3/ops/items/{id}/work/reassign` (same dual target)
- `POST /api/v3/ops/items/{id}/work/{claim|release|complete}` (existing)
- `GET /api/v3/ops/items/{id}/work` (current + history + **effective** + origin)
- Read composition: `GET /api/v3/ops/queues/operator`, `GET /api/v3/ops/entities?status=active`, `GET /api/v3/ops/entities/{e}/extraction/batches`, `GET /api/v3/ops/batches/{id}/items`.

The frontend never calls Supabase assignment tables and contains no D38 mutation logic; it reflects server errors (403 permission, 422/409 validation detail) through the existing alert pattern.

## 5. Effective Assignment Display

Each item row renders exactly the three layers from §6 of the task:

```text
Batch default: PE Alpha
Item assignment: PE Beta (reassigned)   ← only when an open D38 row exists
Previous: PE Alpha                       ← current.previous_* from the API
Effective processor: PE Beta (item assignment)  ← info.effective verbatim
```

The effective value is taken from the API's canonical `effective` (`kind`/`assignee`/`source`); the frontend does not recompute precedence. History lists action/close-action, `actor_domain`, reason and timestamp per ledger row.

## 6. PE Security Behavior

- The PE application (`/pe`) renders no Operations assignment controls and exposes only Claim/Release/Complete on its own effectively assigned items (server-filtered). OperationsPage redirects entity profiles to `/pe`, and every Ops assignment endpoint is denied to PE users (403) server-side.
- **Defect found & fixed during this workstream:** real-HTTP verification of the WS4D PE path exposed that `GET /api/v3/pe/work` returned **500** (`backend/data/manual_extraction.py`, `list_batches_with_open_entity_item`): (a) the batch column list was built from `_BATCH_COLUMNS[0]` even though the constant is a plain string (`[0]` selected the letter `i` → `column b.i does not exist`), and (b) the `$1` parameter was never bound. Both one-line defects were fixed. `/pe/work` now returns the entity's default + item-level batches with per-batch `item_count` counting only items effectively assigned to that PE. This is the relevant backend change referenced in §18 of the task; existing 4B/4C evidence remains valid (the affected endpoint was not exercised by the 4C matrix, which used `/pe/batches/...`), and focused backend suites re-passed after the fix (see §9).

## 7. Internal Processing Behavior

An internal staff member can operate on an item assigned internally **even when its batch default is a Processing Entity**: the item is surfaced through the Assignments surface (PE-default batch directory → row → **Open item**), the workspace route reads it, and `start`/`extract` are authorised by the existing server-side rule (effective internal assignment for this user). Items whose effective processor is a PE remain denied to internal operators (403), and internal staff never receive PE-style or customer capabilities.

## 8. Mixed-Batch Behavior

A single batch can contain `A → PE Alpha`, `B → PE Beta`, `C → PE Alpha`, `D → CarbonTally Internal`. The Assignments surface lists the batch once and renders each row's own item assignment/effective processor; the batch default is shown only as the fallback context. The PE side sees the same batch but only its own items (`/pe/batches/{id}/items` returns only effectively-assigned items; `/pe/work` reports a per-batch effective `item_count`).

## 9. Frontend/Integration Test Results

**New frontend tests (component level, CRA/jest + testing-library):**

| Suite | Coverage | Result |
| --- | --- | --- |
| `ops-assignments-tab.test.jsx` | UI tests 1–4 & 7: assign unassigned item → PE (calls `opsWorkAssignTarget` `{entity_id}`); reassign PE→PE and PE→Internal via `/work/reassign`; canonical effective display incl. batch-default fallback, previous party, reassignment history; mixed-batch per-row effective processors; target lists (active PEs only, internal staff only — PE users excluded); server validation error reflection; Release/Complete withheld for effectively-PE items; “Open item” deep link for an internally assigned item in a PE-default batch. | PASS |
| `operations-page-assignment-gating.test.jsx` | UI test 5 entry: internal staff with `can_process` receive the Assignments tab; PE profiles are redirected to `/pe` before any Operations tab (no assignment controls). | PASS |
| `pe-work-items-page.test.jsx` | UI tests 5/6: PE page renders only the server-reported effectively assigned items, exposes only Claim/Release/Complete, and contains no Ops assign/reassign/combobox controls. | PASS |
| `ops-work-api.test.js` | 4C client wrappers serialise exactly one target (`entity_id` XOR `assigned_to`) to the correct assign/reassign endpoint; entity directory forwards `status=active`. | PASS |

**Regression:** full frontend suite `21/22 suites · 200 tests` passed. The single failing suite (`App.test.js`) fails at module load because CRA jest 27 cannot resolve the react-router v7 subpath export (`react-router/dom`) — a pre-existing environment limitation unrelated to this workstream (no `App.js` change).

**Live integration (real HTTP, disposable fixture, cleaned):** `WS4D UI-path matrix — 21 checks, 0 failures` covering the exact endpoints the UI drives: directory composition (active PEs, internal queue excludes PE batches, PE-batch directory, mixed-batch items read), assign→PE, reassign PE→PE and PE→Internal with single-open invariant and `previous_*` provenance, per-item effective parity in a mixed batch, internal operator workspace + start on an internally assigned item in a PE-default batch (and 403 on PE-defaulted items), PE work/batch-item visibility (only effectively assigned items; cross-item 403), PE Ops assignment/reassign denied (403), and audit history (`assign` + `reassign`). Evidence: `/tmp/ws4d_ui_verify_final.txt`.

**Backend regression after the §6 SQL fix:** focused suites green — `test_v3_work_item_effective_assignment.py`, `test_v3_entity_extraction.py`, `test_v3_processing_workflow.py`, `test_v1_2_dual_origin_workflow.py`.

## 10. Data Cleanup

All fixtures were disposable and fully removed. Baseline re-verified identical:

```text
emission_factors = 7,049   organizations = 975
manual_extraction_items = 260   manual_extraction_batches = 56
work_item_assignments = 0   notifications = 0
conversations = 34  messages = 52  conversation_participants = 62
e2e_auth_users = 0  migrations = 46
```

Residual check: `fixture_orgs 0 · ledger_total 0 · notifications_total 0`. No permanent business/demo/investor data was mutated.

## 11. Remaining Issues

Explicitly distinguished:

- **Gate 3-required work (future):**
  - Browser-level visual/responsive verification of the updated Assignments surface (this workstream verified components + the live API path; a full browser Gate 3 pass is still required).
  - A data-layer regression test for `list_batches_with_open_entity_item`/`GET /api/v3/pe/work` against the real database (the defect found in §6 is covered here by live-HTTP evidence; the hermetic suites use repository fakes and cannot execute the SQL).
  - Targeted final verification and Gate 3 execution.
- **D40 notification work:** unchanged and out of scope — entity-target assignment notifications remain a separate bounded task if required before final WS4 acceptance. Internal-staff assignment notifications already flow via the existing idempotent D40 mechanism (observed and cleaned as test artifacts during verification).
- **Unrelated future improvements:** per-item row polling could later reduce the small per-batch N+1 `GET /items/{id}/work` reads if assignment lists grow; server-side pagination for very large batch directories; an Ops all-batches search endpoint (the UI composes existing read endpoints today). None were introduced to keep the change minimal.

## 12. Gate Status

**Gate 3 remains BLOCKED and was not executed in this workstream.**

This workstream does not claim Gate 3 passed. After PO review of this UI/integration report, the remaining Gate 3-required work above can be scheduled.

## Git

No commit/push. Repo changes: `frontend/src/v3/ops/OpsAssignmentsTab.jsx`, `frontend/src/v3/ops/OperatorItemPage.jsx`, `frontend/src/v3/api.js`, `frontend/src/v3/pe/PeWorkItemsPage.jsx` (comment), four new frontend test files, `backend/data/manual_extraction.py` (two-line PE-work SQL fix), plus this report. The pre-existing 4A–4C uncommitted set (`backend/services/work_items.py`, `backend/api/v3_pe.py`, `backend/api/v3_operations.py`, WS4 docs) remains untouched apart from the SQL fix noted above.
