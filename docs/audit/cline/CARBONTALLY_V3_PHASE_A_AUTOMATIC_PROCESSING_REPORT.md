# CarbonTally V3 — Phase A (CL-56): Durable Automatic Document Processing — Implementation Report

**Implementer:** Cline
**Date:** 2026-08-29
**Baseline:** `6148c86` (`main`)
**Authoritative contract:** OpenHands `CARBONTALLY_V3_POST_RESTORATION_ACCEPTANCE_AUDIT.md` §31.8 and
`CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` CL-56, per the Phase 2 implementation order
(Phase A is the highest-priority item).

---

## 1. What was built

A **real, durable, idempotent automatic document-processing pipeline** replacing the previous
"best-effort OCR metadata only" upload behaviour. The backend now actually processes documents
end-to-end:

```
UPLOAD -> ENQUEUE -> INGEST -> EXTRACT -> MAP -> VALIDATE -> CALCULATE
-> EVIDENCE -> REVIEW/APPROVAL -> COMPLETED
                     \-> BLOCKED (manual-review gate) -> resume after human action
```

The pipeline is driven by a background worker registered at application startup
(`backend/workers/automatic_processing.py`), not by a fake frontend animation. Job state is
durable in `document_processing_queue`; the worker survives restarts and resumes in-flight work.

## 2. Architecture

| Layer | Module | Responsibility |
|---|---|---|
| Migration | `supabase/migrations/20260829000000_v3m9_durable_automatic_processing.sql` | Durable-job columns (`stage`, `attempt_count`, `max_attempts`, `last_error`, `locked_at`, `lock_token`, `extracted_data`, `mapped_data`, `validation_result`, `calculation_snapshot_id`, `manual_review_reason`, `source_item_id`, per-stage timestamps, `reprocess_count`, `pipeline_version`) + claim/org/lock/snapshot indexes. Applied to the live local DB. |
| Domain | `backend/domain/automatic_processing.py` | Explicit state machine (`AUTOMATIC_PIPELINE`), stage-to-RC2-status mapping, confidence thresholds, `AutomaticProcessingJob` model (completeness, gate/terminal predicates). |
| Data | `backend/data/document_processing.py` | Durable-job repository: `create`, `get`, `list_for_org`, `claim_next` (`FOR UPDATE SKIP LOCKED`), `release_lock`, `release_stale_locks`, `advance_stage`, `mark_failed`, `mark_blocked`, `reenqueue`, `complete_review`, `sync_item_data`, `mark_notified`, `count_by_stage`. |
| Service | `backend/services/automatic_processing.py` | Pipeline execution: ingest (private storage) -> extract (PDF/OCR/CSV/XLSX) -> map (factor matching + D-cf-5 customer-factor precedence + aggregate-factor preference) -> validate (existing engine) -> calculate (authoritative engine) -> evidence/notify. |
| Extraction | `backend/services/automatic_extraction.py` | Deterministic file->`extracted_data` parsing: PDF (pdfplumber -> Tesseract -> pypdfium2+ONNX OCR fallback), images (Tesseract -> ONNX OCR), CSV/XLSX (tabular -> line items, unit-embedded headers, spend-based currency detection). |
| Worker | `backend/workers/automatic_processing.py` | Background claim/process loop, started/stopped by the FastAPI lifespan (`main.py`). |
| API | `backend/api/v3_automatic_processing.py` | Org-scoped surface: `GET /api/v3/processing/jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry`, `POST /jobs/{id}/confirm`, `POST /jobs/{id}/review`, `POST /documents/{file_id}/enqueue`. |
| Wiring | `api/router.py`, `api/dependencies.py`, `api/v3_documents.py`, `main.py` | Router registration; `processing` repository on the bundle; upload handler enqueues a durable job; worker lifecycle. |

### 2.1 Requirement coverage (CL-56 checklist)

- **Explicit state machine** - `AUTOMATIC_PIPELINE` (`enqueued -> ingesting -> extracting ->
  mapping -> validating -> calculating -> review -> completed`, gates to `blocked`, terminal
  `failed`).
- **Durable job records** - `document_processing_queue` with `stage`/`status`/timestamps/lock
  fields.
- **Idempotency** - each stage's persisted output is its resume marker; re-runs skip completed
  stages; `claim_next` uses `FOR UPDATE SKIP LOCKED`.
- **Retry handling** - `attempt_count`/`max_attempts` (default 3); `reenqueue` resets/keeps
  attempts.
- **Failure handling / dead-letter** - `failed` terminal state with `last_error`; `retry` re-enters.
- **No duplicate calculations** - deterministic `uuid5("<job id>::calc::<line>")` request ids; the
  calculation stage reuses an existing snapshot for the same request id before recalculating.
- **Resumability** - stale-lock recovery (`release_stale_locks`) + resume markers; a worker restart
  resumes every in-flight job.
- **Persisted progress** - per-stage completion timestamps (`ingested_at` ... `review_ready_at`).
- **Confidence/manual-review gates** - extraction completeness < 0.50 -> `blocked`; mapping without a
  confident factor -> `blocked`; blocking validation findings -> `blocked`; `confirm` re-enqueues
  with human corrections.
- **Mapping persisted** - `mapped_data` (per-line factor_id, factor_kind, confidence, stages).
- **Validation persisted** - `validation_result` (`passed`/`failed` + findings).
- **Calculation snapshot persisted** - immutable `calculation_snapshots` row via the existing engine.
- **`source_item_id` persisted** - every snapshot's `source_item_id` = the manual-extraction item.
- **Emissions persisted** - `emissions_logs` row linked to the snapshot.
- **Evidence chain** - `organization_files -> manual_extraction_items -> calculation_snapshots ->
  emissions_logs`; reverse lookup via `GET /api/v3/documents/{file_id}/emissions` unchanged.
- **Notifications/status updates** - in-app notification to org owners/admins on completion; job
  status queryable at any time.



## 3. Verification (live stack)

`backend/_phaseA_selfcheck.py` exercises the real pipeline against the local stack
(backend `:8050`, local Supabase `:54425/:54426`) with the investor-demo document formats.
Final run: **20/20 PASSED** (a full transcript is in the appendix).

| Scenario | Format | Result |
|---|---|---|
| Diesel expense report | CSV (`Quantity (litres)`) | auto -> review -> approve -> completed; snapshot + evidence verified (`46.31 kg CO2e`, 4 lines) |
| Gas statement | XLSX (`Consumption (m3)`) | auto -> review -> approve -> completed; evidence verified (`8774.05 kg CO2e`) |
| Consulting spend | XLSX (GBP, no unit column) | customer-factor precedence (D-cf-5) -> review -> approve; evidence verified (`500.00 kg CO2e`, `factor_kind=customer_factor`) |
| Electricity invoice | scanned image (ONNX OCR) | OCR -> mapping -> manual gate (supplier missing) -> human correction + confirm -> resume -> review -> approve; evidence verified |
| Logistics invoice | PDF (`curr_gbp_logi.pdf`) | extraction ran; low completeness -> manual gate (persisted reason) |
| Idempotency | - | blocked-job retry (dead-letter recovery) works; exactly one snapshot per job despite re-runs |

### 3.1 Dependencies added
- `rapidocr-onnxruntime` (+ onnxruntime, opencv-python) - pure-pip ONNX OCR fallback so scanned
  documents are processed on hosts without the Tesseract binary. Tesseract remains the first choice
  where present.

## 4. Files
- New: `supabase/migrations/20260829000000_v3m9_durable_automatic_processing.sql`,
  `backend/domain/automatic_processing.py`, `backend/data/document_processing.py`,
  `backend/services/automatic_extraction.py`, `backend/services/automatic_processing.py`,
  `backend/workers/automatic_processing.py`, `backend/api/v3_automatic_processing.py`,
  `backend/_phaseA_selfcheck.py`, unit tests (`tests/unit/domain/test_automatic_processing.py`,
  `tests/unit/services/test_automatic_extraction.py`,
  `tests/unit/services/test_automatic_processing.py`).
- Modified: `backend/api/dependencies.py` (bundle `processing`), `backend/api/router.py`,
  `backend/api/v3_documents.py` (enqueue on upload), `backend/data/emissions_logs.py`
  (`find_snapshot_by_request_id`), `backend/main.py` (worker lifecycle).

## 5. What remains (next phases)
Per the implementation order, Phase A is done. Phases B-F (customer workspace, consultant
application, staff/admin canonical application, PE application, shared-platform separation) are
tracked separately; the durable pipeline built here is the foundation they build on.

---

## Appendix — self-check transcript (final run)

```
== CarbonTally Phase A (CL-56) automatic-processing self-check ==
[PASS] spend-based customer factor reused (already active)
[PASS] CSV upload — Investor_Diesel_Expenses_2025Q1.csv
[PASS] CSV job created
[PASS] CSV auto pipeline -> review (extract/map/validate/calculate) — stage=review completeness=1.0 lines=4
[PASS] CSV owner approval
[PASS] CSV evidence chain — snapshot=.. source_item_id=OK co2e=46.312500 factor_kind=emission_factor
[PASS] XLSX upload — Investor_Gas_Statement_Q1.xlsx
[PASS] XLSX job enqueued
[PASS] XLSX auto pipeline -> review — stage=review lines=3
[PASS] XLSX owner approval
[PASS] XLSX evidence chain — snapshot=.. source_item_id=OK co2e=8774.052000 factor_kind=emission_factor
[PASS] spend-based XLSX upload — Investor_Consulting_Spend_Q1.xlsx
[PASS] spend-based auto pipeline (customer factor precedence, D-cf-5) — stage=review customer_factor=True
[PASS] spend-based owner approval
[PASS] spend-based evidence chain — snapshot=.. source_item_id=OK co2e=500.000000 factor_kind=customer_factor
[PASS] image (already completed) evidence chain verified
[PASS] PDF enqueue (existing investor doc)
[PASS] PDF processed (extraction ran; gate/review reached) — stage=blocked
[PASS] idempotency: blocked job retried (dead-letter recovery)
[PASS] idempotency: no duplicate calculation (single snapshot per job) — snapshots=1

== RESULT: 20 passed, 0 failed ==
```
