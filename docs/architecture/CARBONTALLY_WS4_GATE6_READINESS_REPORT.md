# CarbonTally WS4 — Gate 6 — Human-After-Automation — Architecture & Readiness Report

- **Date:** 4 September 2026
- **Scope:** Architecture/readiness review **only**. No code, SQL, migration,
  RLS, API, UI, D38/D39/D40, workflow or architecture was modified; no data was
  changed; no fixtures were created; nothing was committed or pushed.
- **Git HEAD inspected:** `1639121` (working tree matches the accepted
  Gate-5-final state; report verified against live code and read-only live DB
  schema).

---

## 1. Gate 6 ratified definition

**Gate 6 = Human-After-Automation Attribution.** When a human subsequently acts
on output produced by automated processing, the system must preserve **both**:

1. the original automated provenance; and
2. the actual human actor/action provenance,

and the two must remain distinguishable. The desired evidence relationship is:

**Source Document → Work Item → Automated Execution → Automated Output →
Human Action → Calculation → Snapshot → Review/QC → Approval**

Gate 4 (human provenance) and Gate 5 (automated machine provenance) are PASSED /
ACCEPTED and authoritative. Gate 5 established `document_processing_queue` as
the canonical automated-execution record with the write-once `automation_*`
block, `automatic_processing:extracted` audit events, and the typed API
`automation` payload. Gate 6 must build on these mechanisms and **must not**
create a competing provenance system.

## 2. Current implementation inspected

Inspection was performed directly against HEAD code and the live database
(read-only):

- `backend/domain/automatic_processing.py` — DPQ stage machine, job model
  (incl. Gate-5 `automation_provider/model/version`, per-stage timestamps,
  `pipeline_version`, `source_item_id`); `_SYSTEM_ACTOR` is the zero UUID,
  `_AUTOMATION_ACTOR = "automatic_pipeline"` (services file).
- `backend/workers/automatic_processing.py` + `services/automatic_processing.py`
  — durable claim/process loop; `_extract` persists extraction output to the job
  (write-once automation block), mirrors it to the manual-extraction item with
  the zero-UUID system actor, then fires the `automatic_processing:extracted`
  audit event (actor `automatic_pipeline`); `_map` / `_validate` / `_calculate`
  resume-marker semantics; blocking → human gate; calculation via the engine
  with deterministic request ids (no-duplicate snapshots); notifications.
- `backend/data/document_processing.py` — repository SQL: `create`
  (`created_by`), `advance_stage` (COALESCE automation writes), `mark_blocked`,
  `reenqueue` (`updated_by`), `complete_review` (`customer_reviewed_by/at`,
  `customer_approved`, `customer_notes`, `customer_rejection_reason`),
  `sync_item_data` (overwrites `extracted_data`/`mapped_data`, no actor param),
  `_JOB_COLUMNS` (deliberately does **not** select `created_by`/`updated_by`/
  `customer_reviewed_by`/… — the human actor columns are DB-only today).
- `backend/api/v3_automatic_processing.py` — job list/detail payload (typed
  `automation` block, stage timestamps, outputs) and the human gate endpoints:
  `POST /jobs/{id}/confirm` (human corrections + `reenqueue(updated_by=user)`
  + `sync_item_data`), `POST /jobs/{id}/retry` (`reenqueue(updated_by=user)`),
  `POST /jobs/{id}/review` (approve/reject via `complete_review(reviewer=user)`
  + item `customer_review`). **No audit events are written by these endpoints.**
- `backend/data/manual_extraction.py` — item persistence: `save_extracted_data`
  (overwrites data + stamps `extracted_by` = actor), `save_mapped_data` (no
  `mapped_by`), `save_calculation`, `set_item_status`, `customer_review`,
  `pe_review_decision` / `pe_qc_decision` / `ct_qc_decision` / `qc_review`
  (stamp `pe_reviewed_by`/`pe_qc_by`/`qc_by`), item actor columns confirmed live.
- `backend/api/v3_operations.py` — canonical human ops surface; Gate-4 F1 audit
  helper `_record_item_action_audit` records human actor ids for
  `ops_map:applied`, `ops_validate:blocked/validated`, `ops_calculate:applied`
  and the PE variants (`pe_map:applied`, `pe_calculate:applied`, …), plus
  review/QC entries; `CalculationRequest.performed_by` stamps human actors on
  snapshots (`calculation_snapshots.performed_by`/`source_item_id`, Gate-4 F2).
- `backend/engines/calculation.py` — `calculation:completed` audit, actor =
  `request.performed_by or "calculation_engine"` (so human calculations are
  audited with the human id; machine runs with the engine label).
- Migrations: `20260905000000_gate4_actor_provenance.sql`,
  `20260905010000_gate5_t1_automation_provenance.sql`,
  `20260905020000_gate5_t6_automation_write_once_guard.sql`.
- Live schema (read-only): DPQ has 78 columns including `created_by`,
  `updated_by`, `customer_reviewed_by/at`, `customer_approved`,
  `customer_notes`, `customer_rejection_reason`, `manual_requested_by/at`,
  `manual_extracted_by/at`, `qc_by/at/notes/approved`; the write-once guard
  function/trigger is present (1/1); DPQ RLS = 4 org-scoped policies (tenant
  select/insert/update/delete). `manual_extraction_items` carries
  `extracted_by`, `extracted_at`, `qc_by`, `customer_reviewed_by`,
  `pe_reviewed_by`, `pe_qc_by`, `processing_origin`. `calculation_snapshots`
  carries `performed_by`, `source_item_id`, `calculated_by`, factor/evidence
  columns.

---

## 3. Existing human-after-automation behaviour (as implemented)

Two complementary records carry a job through automation then human action:

1. **Automated execution record (Gate 5):** the DPQ row is the canonical
   automated-execution record. The worker persists `extracted_data` /
   `mapped_data` / `validation_result` / `calculation_snapshot_id` with
   per-stage timestamps, stamps the write-once `automation_*` block when an AI
   pass **contributed** (NULL for deterministic/legacy/failed-attempt runs), and
   fires one `automatic_processing:extracted` audit event (actor
   `automatic_pipeline`, entity/correlation = job id).
2. **Work-item mirror:** each job is linked to a `manual_extraction_items` row
   (`source_item_id`), which the worker keeps live (extraction mirror written
   with the zero-UUID system actor). This is the row the human workbench edits.
3. **Human gates on the job:**
   - *Blocked/failed → human rework*: `POST /jobs/{id}/confirm` (or `retry`)
     persists human corrections to the item (with the human user id), re-enqueues
     the job with `updated_by = human user id`, and syncs corrected item data
     into the job (`sync_item_data`) before the worker resumes. The
     `automation_*` columns are never written by these paths.
   - *Customer review*: `POST /jobs/{id}/review` (owner/admin only) records
     `customer_reviewed_by/at`, `customer_approved`, notes/reason on the job and
     mirrors the decision onto the item (`customer_reviewed_by/at`).
4. **Item-level human actions after automation:** a human working the linked
   item through the ops/PE surfaces (`extract`/`map`/`validate`/`calculate`,
   review, QC) stamps the item actor columns (`extracted_by`, `qc_by`,
   `pe_reviewed_by`, `pe_qc_by`, `customer_reviewed_by`) and — for
   map/validate/calculate/review/QC — writes append-only audit events with the
   authenticated human user id as actor (Gate-4 F1). Human calculations produce
   `calculation:completed` audit rows with the human id as actor and a snapshot
   carrying `performed_by = human id` and `source_item_id` (Gate-4 F2).
   Machine calculations keep `performed_by = NULL` and audit with actor
   `calculation_engine`.

The two provenance kinds therefore live on distinct surfaces that do not
overwrite each other: the machine facts live in the job's automation block and
machine audit events; the human facts live in human actor columns and
human-actor audit events.

## 4. Automated provenance preservation assessment (required questions 1, 3, 4, 5)

- **Q1 — original automated execution identifiable after a human edits the
  result:** **Yes.** The DPQ job id remains, and the `automation_provider` /
  `automation_model` / `automation_model_version` block is write-once
  (repository COALESCE first-write-wins **and** the T6 database trigger). No
  human-path SQL (`sync_item_data`, `reenqueue`, `complete_review`, item saves)
  touches those columns. This was proven on the real stack in Gate-5
  acceptance (overwrite/clear attempts rejected; human retry and owner approval
  left the block unchanged).
- **Q3 — automated and human provenance independently persisted:** **Yes for
  the identity facts.** Machine = DPQ automation block + per-job
  `automatic_processing:extracted` audit row. Human = actor columns on the job
  (`updated_by`, `customer_reviewed_by`) and item (`extracted_by`,
  `customer_reviewed_by`, QC/review columns) plus human-actor audit rows for
  ops map/validate/calculate/review/QC and human calculations. The two records
  are distinguishable (distinct storage, distinct actor vocabularies: machine
  label/zero-UUID vs authenticated user UUID).
- **Q4 — can a human save overwrite any automation field:** **No.** Enforced at
  two layers; verified by the accepted Gate-5 write-once acceptance and again
  by code inspection of every human-path UPDATE (none lists the automation
  columns, and the trigger would reject any attempt).
- **Q5 — can a human action make an automated result appear human-generated:**
  **No at the job/audit level.** No code path stamps a human identity into the
  automation block or the machine audit events, and `automatic_pipeline` is not
  an authorization principal. **Partial caveat at the item level:** the worker
  mirrors automated extraction onto the item with the zero-UUID system marker
  in `extracted_by`; a later human extraction save overwrites both the item
  payload and `extracted_by` with the human id, so the item surface alone then
  shows the human as the (last) extractor and no longer shows that the original
  output was machine-produced. The machine origin remains recoverable only
  through the linked job + job audit event — acceptable today only because the
  job is the canonical record (Gap G-A/G-D, §10).


## 5. Human actor attribution assessment (required questions 2, 9, 10)

- **Q2 — human actor who subsequently changed/reviewed/validated/mapped/
  calculated the data identifiable:** **Mostly yes.** Item-level ops actions are
  attributable to the authenticated user id via actor columns and (for
  map/validate/calculate/review/QC) audit events; job-level confirm/retry/review
  persist the human id in DPQ `updated_by` / `customer_reviewed_by`. **Gaps:**
  those job-level actor columns are not surfaced by the repository mapper, the
  domain model or the API payload, and the job-level gate actions produce no
  audit-trail event (Gap G-B). A human *extraction* edit on an item (ops
  `extract`, `PUT /items/{id}`) is recorded only as `item.extracted_by` and is
  not written to the audit trail (Gap G-D).
- **Q9 — human review that merely accepts automated output without changing it
  still attributable:** **Yes at persistence level.** `complete_review` records
  `customer_reviewed_by` + `customer_reviewed_at` + `customer_approved` on the
  job, and `customer_review` mirrors them on the item. **Gap:** no audit event
  is emitted and the reviewer identity is not exposed through the job API
  (Gap G-B), so the acceptance evidence must come from DB columns rather than
  the typed API or audit trail.
- **Q10 — paths lacking actor attribution:** enumerated in §10 (G-B: job
  confirm/retry/review only in unmapped columns, no audit; G-D: item extraction
  edits recorded only in `extracted_by`, no audit, machine marker overwritten;
  machine validation/calculation audit rows use engine labels rather than the
  `automatic_pipeline` label — consistent with machine runs and not a human
  gap). **Mandatory for Gate 6:** G-B and G-D affect the human-after-automation
  acceptance scenario (the human action and actor must be demonstrable through
  the real API and the audit trail); G-C (below) affects correctness of the
  resulting state.

## 6. Audit-trail assessment (required question 6)

- The append-only audit trail (service-role, immutable) already distinguishes:
  `automatic_processing:extracted` (actor `automatic_pipeline`) — the machine
  extraction event — from later human engine/ops events (`ops_map:applied`,
  `ops_validate:*`, `ops_calculate:applied`, PE variants, `calculation:completed`
  with a human actor id). Q6 is therefore **satisfied for the actions that are
  audited**.
- **Not satisfied today:** the job-level human gates (`confirm`, `retry`,
  review approve/reject) are **not** written to the audit trail at all, so the
  audit trail alone cannot prove those human actions, their actor, or their
  ordering relative to the machine event (Gap G-B). The machine extraction
  audit `after` block also does not carry the extracted payload (by accepted
  design it carries method/pipeline/provider/model/version/confidence/attempt/
  item/ai_status), so it cannot serve as the immutable copy of the machine
  output after a human correction (Gap G-A).

## 7. Temporal / provenance-chain assessment (required question 7)

- The chain **Source Document → Work Item → Automated Execution → Snapshot →
  Emissions** is verifiable: `organization_files` → `manual_extraction_items`
  (`source_item_id`) → DPQ job → `calculation_snapshots`
  (`source_item_id`, `performed_by`) → `emissions_logs`.
- Machine-first/human-later ordering is provable where both sides produce
  evidence: job per-stage timestamps (`extracted_at`, … `review_ready_at`,
  `customer_reviewed_at`) and audit `performed_at` on machine extraction and on
  human ops/calculation events. **Gap:** job-level human confirm/retry/review
  actions have timestamps only in DPQ columns (`updated_at`,
  `customer_reviewed_at`) and no audit row, so an audit-only query cannot
  reconstruct the full temporal sequence (Gap G-B).

## 8. Security assessment

- The human-after-automation flows introduce **no new authorization path**:
  confirm/retry/review enforce the existing org-scoped guards
  (`ensure_processing_org_access`, `require_org_admin` for customer approval);
  item ops enforce staff/permission/entity-assignment guards; PE staff remain
  denied on job surfaces (verified 403 in Gate-5 acceptance).
- No new principals: `automatic_pipeline` is a string label; human actors come
  exclusively from the authenticated token (`current_user.user_id`). No
  mechanism lets a human write the automation block (Q4) or impersonate the
  machine actor in audit rows.
- RLS posture unchanged (DPQ: 4 org-scoped tenant policies; live check). The
  proposed additions (§12) are read-only provenance exposure and append-only
  audit rows on org-scoped endpoints — no RLS change is required.
- No secrets or document content are added to any payload/audit field beyond the
  machine extraction output already stored on the org-scoped job record.

## 9. Data-integrity assessment

- This review performed **no data modifications** and created **no fixtures**.
  Read-only queries confirmed the live schema, RLS and guard state; no baseline
  mutation occurred. The Gate-5 acceptance baseline (DPQ 36 rows, all NULL
  automation, snapshots 100, migrations 49/46) was not touched by this review.


---

## 10. Exact gaps, if any

Four bounded gaps prevent a full "human-after-automation" acceptance today.
None of them change machine provenance, Gate 4, audit immutability, RLS or the
workflow model; all are additive and architecture-consistent:

- **G-A — No immutable copy of the machine-extracted output.** Both
  `document_processing_queue.extracted_data` and the mirrored
  `manual_extraction_items.extracted_data` are overwritten in place when a human
  corrects them (confirm → `sync_item_data`; item `save_extracted_data` /
  `update_item`). The `automatic_processing:extracted` audit `after` block
  records machine identity + method + confidence but **not** the extracted
  payload. After a human correction the exact pre-correction automated output is
  therefore not recoverable from any durable record (only the machine
  *identity* survives). Required-questions Q1/Q8 are only partially satisfiable
  without it.
- **G-B — Job-level human-gate actions are not audit events and not API-visible.**
  `confirm`, `retry`, and review approve/reject persist the human actor only in
  DPQ columns (`updated_by`, `customer_reviewed_by/at`, `customer_approved`,
  notes/reason) that are absent from `_JOB_COLUMNS` → not on the job domain
  model and not in the typed job payload, and no audit-trail row is written.
  Q2/Q6/Q7/Q9 are therefore only partly demonstrable through the accepted
  evidence surfaces (API/audit).
- **G-C — Resume-marker staleness after human correction of a previously
  calculated job.** `reenqueue` clears `manual_review_reason`/`last_error` but
  **not** `validation_result` or `calculation_snapshot_id`, and `sync_item_data`
  overwrites `extracted_data`/`mapped_data` without clearing those downstream
  markers. For a job that previously reached calculation (e.g. rejected at
  customer review and then corrected), a confirm re-enqueue can skip
  validation/calculation, so the human correction would not produce a new
  snapshot / emissions result — breaking the required
  **Human Action → Calculation → Snapshot** link. (Jobs blocked before
  calculation are unaffected because no markers exist yet.)
- **G-D — Human extraction edits on items are not audited and erase the
  machine marker at item level.** Ops `extract` and `PUT /items/{id}` overwrite
  `extracted_data` and stamp `extracted_by` with the human id (replacing the
  worker's zero-UUID system marker) and write **no** audit event (unlike the
  map/validate/calculate paths which Gate-4 F1 audits). The human correction is
  attributable only via the current `extracted_by` value.

## 11. Whether implementation is required

**Yes — implementation is required** to fully satisfy Gate 6, and it is
bounded and additive. The core Gate-5 invariant (machine provenance preserved
through human saves) and most of the human-actor surfaces already exist; the
remaining work is: (G-A) persist the machine-extracted output immutably at
extraction time; (G-B) surface and audit the job-level human-gate actions;
(G-C) invalidate stale downstream resume markers when corrected data is
synced; (G-D) audit item-level human extraction edits. **No Product-Owner
architectural decision is required** — the changes follow existing conventions
(write-once evidence, append-only audit, org-scoped typed payloads, existing
repo/service/API layers) and do not create a competing provenance system.


## 12. Minimal architecture-consistent implementation proposal

- **G6-W1 (G-A) — immutable machine-output evidence.** At the extraction →
  mapping advance the worker already holds the persisted machine `extracted`
  payload. (a) Add one additive migration column
  `document_processing_queue.automation_extracted_data JSONB` with the same
  write-once semantics as the existing block (extend the accepted T6 guard
  function/trigger to the new column, first-write-wins) **or** (b) extend the
  accepted `automatic_processing:extracted` audit `after` block to carry the
  normalised machine output. Option (a) keeps the audit row small and mirrors
  the accepted T1/T6 pattern; both are strictly additive evidence and are not
  authorization inputs.
- **G6-W2 (G-B) — job human-gate actor exposure + audit.** Add the human actor
  fields to the DPQ domain object / `_JOB_COLUMNS` (read-only: `updated_by`,
  `customer_reviewed_by`, `customer_reviewed_at`, `customer_approved`) and to
  the typed job payload; emit append-only audit events from
  `confirm_job` / `retry_job` / `review_job` (actions e.g.
  `automatic_processing:confirmed`, `:retried`, `:approved`, `:rejected`,
  actor = authenticated user id, entity/correlation = job id) using the
  existing `get_audit_context`/`AuditLogger` pattern. No RLS change.
- **G6-W3 (G-C) — corrected-resume marker invalidation.** When `sync_item_data`
  (or a confirm payload) overwrites `extracted_data`/`mapped_data`, clear the
  stale downstream resume markers for the chosen re-entry stage
  (`validation_result`, and `calculation_snapshot_id` when the data changed) so
  the resumed pipeline regenerates validation/calculation for the corrected
  data while preserving no-duplicate-snapshot protection for unchanged runs.
- **G6-W4 (G-D) — item extraction-edit audit.** Record an append-only item
  action on human extraction saves/edits (ops `extract`, `PUT /items/{id}`)
  with the human actor and the previous `extracted_data` as the `before` state
  (mirroring Gate-4 F1 `_record_item_action_audit`), keeping the machine
  output recoverable via G6-W1 and the job audit event.
- No new endpoints are required; no D38/D39/D40, RLS, or workflow-model change.

## 13. Focused test strategy

- **Unit/API (pytest):** worker extraction persists the immutable machine-output
  evidence with the automation block; write-once guard covers the new column;
  confirm/retry/review endpoints emit audit rows with the human actor and return
  the surfaced actor fields; sync-with-corrections clears stale markers;
  item extraction edits record before/after audit rows. Include negative tests
  (cross-org/PE still 403; unauthenticated 401; human cannot write automation).
- **Real-stack fixture run (Gate-6 acceptance, disposable fixtures, exact
  baseline restore):** contributing-AI job → review; human corrects extraction
  via the real API; confirm with corrections; assert (1) automation block
  unchanged, (2) machine-output evidence equals the pre-correction payload,
  (3) `automatic_processing:confirmed` audit row actor = human, (4) a new
  snapshot/emissions result is produced from the corrected data (G-C), (5) item
  extraction-edit audit present, (6) owner approve → `customer_reviewed_by`
  surfaced and audited; verify audit `performed_at` ordering automation → human;
  clean up and verify the exact baseline. No mocks for acceptance claims.
- **DB-level:** real-PostgreSQL assertions for the extended write-once guard and
  marker-clearing semantics; RLS/policy-count and Gate-4/Gate-5 schema checks.

## 14. Proposed bounded implementation workstreams (if required)

1. G6-W1 — machine-output immutable evidence (schema + guard + worker + repo).
2. G6-W2 — job human-gate actor surface + audit events (domain/repo/payload/API).
3. G6-W3 — corrected-resume marker invalidation (repo/service + regression).
4. G6-W4 — item extraction-edit audit (repo/ops API).
5. G6-W5 — focused unit/API regression suite, then a PO-authorized real-stack
   Gate-6 acceptance run (scenario matrix + baseline restore).

## 15. Explicit out-of-scope items

No change to: machine provenance (automation block/write-once/T6 trigger),
Gate-4 human provenance, the append-only audit design, D38/D39/D40, RLS or
authorization, the workflow stage model, the frontend beyond additive payload
display, the accepted Gate-5 schema, or unrelated legacy test hygiene. No
Phase-6 / Advanced-Analytics work. No commit or push.

## 16. Final readiness verdict

The current implementation already preserves the Gate-5 automated-provenance
block through every human save and attributes most human actions to
authenticated actors, but **four bounded, additive gaps** remain before the
full Gate-6 evidence relationship
(**Automated Output → Human Action → Calculation → Snapshot**) is provable
through the durable records, the API and the audit trail:

**GATE 6 IMPLEMENTATION REQUIRED — DESIGN READY**

