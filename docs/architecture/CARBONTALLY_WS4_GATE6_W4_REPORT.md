# CarbonTally WS4 — Gate 6 — Workstream W4 Implementation Report
**G6-D: Human Correction, Resume-Marker, and Processing Integrity**

- **Date:** 4 September 2026
- **Authority:** G6-A / G6-B / G6-C PASSED/ACCEPTED. Final Gate 6
  implementation workstream — addresses **G6-D only**.
- **Git HEAD:** `1639121`. **No commit. No push.** No Phase 6 work was started.

---

## 1. Exact stale-state problem found

Two distinct integrity failures existed when a human corrected automated output
after the pipeline had already computed results:

- **Resume markers:** `document_processing_queue.validation_result` and
  `calculation_snapshot_id` are the durable "already done" markers. The worker
  skips validation when `validation_result.status == "passed"` and skips
  calculation (advancing straight to review) whenever
  `calculation_snapshot_id` is set. `sync_item_data` overwrote
  `extracted_data`/`mapped_data` with human-corrected values **without** clearing
  those markers, so a corrected job that had already been validated/calculated
  resumed past validation/calculation and stayed pointed at the pre-correction
  snapshot.
- **Snapshot dedupe resurrection:** even if the snapshot pointer were cleared,
  the per-line deterministic request id (`uuid5(job::calc::{idx})`) is derived
  only from the job id. The recalculation would find the pre-correction snapshot
  by request id in `find_snapshot_by_request_id` and silently reuse it — the old
  snapshot would still be presented as the calculation for the corrected data.
- **Item-level attribution:** human extraction saves (ops `extract`, PE
  extract, org `update_item`, and the confirm-gate correction save) overwrote
  the machine zero-UUID marker in `manual_extraction_items.extracted_by` without
  an audit-trail event, so a human correction was not distinguishable from the
  machine extraction in the audit trail.

## 2. Exact correction path

`POST /api/v3/processing/jobs/{id}/confirm` (human confirm after rework) →
human corrections saved to the linked `manual_extraction_items` row →
`reenqueue(...)` → `sync_item_data` copies the corrected values onto the durable
job → the worker resumes at `enqueued`. Also relevant: internal/PE item
`extract` endpoints and the org `update_item` surface, which a human uses to fix
extraction on the work item before confirming.

## 3. Files changed

| File | Change |
|---|---|
| `backend/data/document_processing.py` | `sync_item_data` now conditionally invalidates the downstream resume markers (`validation_result`, `calculation_snapshot_id`) when a supplied value is DISTINCT from the persisted value; identical (no-op) syncs leave them intact. |
| `backend/services/automatic_processing.py` | Calculation request ids are now keyed on a canonical data digest (`::calc::{idx}::c1::{digest}`), so corrected data produces a NEW snapshot while unchanged crash re-runs still dedupe; duplicate "processed" notifications suppressed on correction-driven recalculation. |
| `backend/api/audit_helpers.py` | **New** shared best-effort helper `record_item_extraction_edit(...)` (+ `changed_extraction_keys`) for item-level human extraction-edit audit events. |
| `backend/api/v3_operations.py` | Internal ops `extract` and PE entity `extract` now emit `ops_extract:applied` / `pe_extract:applied` item audits. |
| `backend/api/v3_manual_extraction.py` | Org `update_item` emits `org_item_extraction:edited` when extraction data is supplied. |
| `backend/api/v3_automatic_processing.py` | Confirm-gate extraction corrections emit the job-correlated item audit `automatic_processing:item_extraction_corrected`. |
| `backend/tests/unit/services/test_automatic_processing.py` | New `TestGate6W4ResumeIntegrity` (4 scenario tests: corrected recalc vs old snapshot; unchanged-data dedupe; multiple corrections; blocked-before-calc reprocess). |
| `backend/tests/unit/api/test_v3_automatic_processing_jobs.py` | `MemoryProcessing.sync_item_data` fake; new confirm-correction item-audit API test. |
| `docs/architecture/CARBONTALLY_WS4_GATE6_W4_REPORT.md` | This report. |

## 4. State invalidation / re-entry mechanism

`sync_item_data` now clears `validation_result` and `calculation_snapshot_id`
**only when** the incoming `extracted_data`/`mapped_data` actually differs
(`IS DISTINCT FROM`) from the persisted value. This means:

- corrected data re-enters the required **validation → calculation** stages on
  resume (extraction/mapping are NOT forced to re-run — their persisted markers
  remain valid, using the existing state machine);
- an identical (no-op) confirm/retry leaves the markers intact, so a plain
  replay never causes unnecessary re-validation or duplicate snapshots;
- `automation_extracted_data` and the Gate-5 automation block are never touched
  by the sync (verified at the DB level).

## 5. Human extraction-edit audit mechanism

Item-level human extraction edits now emit an append-only event through the
existing `audit_trail` repository (best-effort, never breaks the action):

- entity = `manual_extraction_item`, record id = item id;
- correlation id = the linked job id when the item has one, else the item id;
- action = `ops_extract:applied` (CarbonTally internal staff), `pe_extract:applied`
  (Processing Entity staff), `org_item_extraction:edited` (org member edit), or
  `automatic_processing:item_extraction_corrected` (confirm-gate correction);
- actor = authenticated human user id (from request context only);
- `changed_fields` = status_from/status_to, `previous_extracted_by`,
  `corrected_machine_output` (true when the previous extractor was the machine
  zero-UUID marker), `job_id` when known, and a compact `changed_keys` list of
  the top-level extraction keys that changed. **No payloads are stored** in the
  audit trail.

## 6. Snapshot integrity mechanism

- Pre-correction snapshots are **never rewritten or reused** for corrected
  data: the recalculation runs through the existing calculation engine with the
  corrected authoritative data and produces a **new** snapshot (append
  semantics; history/audit of the old snapshot remain intact).
- Deterministic request ids are now derived from a canonical digest of the
  authoritative working data (`extracted_data` + `mapped_data`), preserving the
  crash-resume no-duplicate guarantee for identical data while guaranteeing a
  different request id — and therefore a new snapshot — whenever the data
  changed.
- The new snapshot preserves actor attribution (machine run = `performed_by`
  NULL / engine audit; human-driven recalculation keeps its own actor trail),
  `source_item_id` and the corrected work-item relationship unchanged.

## 7. Actor attribution

- Human extraction corrections: authenticated `current_user.user_id`
  (ops/PE/org/confirm endpoints) — the same authoritative request-context source
  used throughout Gate 4/B/C. Client-supplied actor fields are never trusted.
- Item actor columns continue to record the last extractor
  (`extracted_by` → human id after a correction), while the machine zero-UUID
  marker is captured in the audit event's `previous_extracted_by` +
  `corrected_machine_output` so machine extraction and human correction stay
  distinguishable even after the column is overwritten.
- Machine provenance (`automation_extracted_data`, Gate-5 automation block,
  machine extraction audit) remains unchanged through every correction.

## 8. Security verification

- No authorization change: the confirm/retry/review and item-edit endpoints
  keep their existing guards (`ensure_processing_org_access`,
  `require_org_admin`, staff/entity workspace guards); PE and cross-org denials
  unchanged (existing tests pass).
- Item-edit audit actor derives from the request context only; no client actor
  injection (verified by tests).
- No new endpoint, role, capability or RLS policy; audit events are written via
  the existing service-role audit path.
- Scenario 6 (unauthorized correction): denied requests fail authorization
  before any state change or audit event (existing cross-org 403 tests).

## 9. Database / migration impact

**No migration required.** All changes reuse existing columns, the existing
state machine and the existing audit trail. Verified on real PostgreSQL: the new
`sync_item_data` invalidation (no-op keeps markers; corrected sync clears them;
G6-A preserved output and Gate-5 block untouched; G6-A write-once guard still
rejects overwrites; unrelated updates allowed; transaction rolled back, baseline
count restored 36/36).

## 10. Tests and real-stack verification

- **Focused/regression (from `backend/`):**
  `pytest tests/unit/services/test_automatic_processing.py
  tests/unit/api/test_v3_automatic_processing_jobs.py
  tests/unit/api/test_v3_automatic_processing_payload.py
  tests/unit/api/test_v3_operations.py
  tests/unit/api/test_v3_entity_extraction.py
  tests/unit/api/test_gate4_remediation_actor_provenance.py
  tests/unit/domain/test_automatic_processing.py -q`
  → **121 passed** (covers the G6-D scenario tests, automatic processing,
  manual-extraction endpoints, calculation/snapshot resume, Gate-4 actor
  provenance, Gate-5 automation provenance, G6-A, G6-B, G6-C payload).
- **`py_compile`** of all changed modules → OK.
- **Real-PostgreSQL verification** (main DB, rolled back): no-op sync keeps
  markers; corrected sync clears `validation_result` and
  `calculation_snapshot_id` and updates current data; mapping preserved; G6-A
  preserved output and Gate-5 block untouched; G6-A guard intact; unrelated
  update allowed; baseline restored (36/36). **10/10 PASS.**
- New service scenario tests cover: correction-after-calculation producing a NEW
  snapshot (not the old one); unchanged-data crash re-run still dedupes to the
  exact snapshot; multiple corrections each producing a fresh snapshot with
  machine provenance surviving; blocked-before-calculation reprocessing.
- New API test proves the confirm-gate extraction correction records the item
  audit event (`automatic_processing:item_extraction_corrected`) with the
  authenticated actor, machine-origin flag, job correlation, and that G6-A +
  Gate-5 provenance survive on the job.

## 11. Legacy-data treatment

No fabrication or backfill: existing jobs, items, snapshots and audit rows are
untouched. The new request-id digest applies only to future calculation runs;
new audit events are written only when a real human extraction edit occurs.

## 12. No Phase 6 work started

Confirmed: this workstream implements only G6-D (resume-marker integrity +
item extraction-edit attribution). No Phase 6 Consultant Workflow, Gate 7 /
Assurance architecture, analytics, reporting redesign, new authorization
model/roles/RLS/workspace, or PE workflow redesign was started.

## 13. Remaining Gate 6 concerns

None blocking. Two documented design notes: (1) `mapped_data` remains the
authoritative workspace mapping after a correction — a human changing an
activity/unit should re-map the item via the existing map surface so the
recalculated snapshot uses the corrected factor; the integrity fix guarantees
validation/calculation always re-run on whatever authoritative data the item
holds. (2) Correction-driven recalculation no longer re-notifies
owners/admins (notification fires once per job) to avoid duplicate
"processed" messages. G6-A/B/C remain frozen and untouched.

**Status: G6-D IMPLEMENTED & TESTED — Gate 6 implementation complete; awaiting
PO acceptance before the final Gate 6 acceptance review.**

