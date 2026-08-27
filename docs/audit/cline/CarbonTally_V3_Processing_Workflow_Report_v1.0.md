---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + wiring + tests); RUNTIME VERIFICATION PENDING (shell unavailable)
Created: 2026-08-15
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md (§10–16), CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md
---

# CarbonTally V3 — Phase 3: Processing Workflow Report

## 1. Executive Summary

Phase 3 delivered the end-to-end **document-processing workflow** for outsourced
manual extraction, implementing the core pipeline

    Source → Extraction → Mapping → Validation → Calculation → Review → Approval

as an org-scoped `/api/v3/processing/*` surface. The workflow is built entirely
on the existing RC2 tables — `manual_extraction_batches`/`manual_extraction_items`
(carrying `extracted_data`, `mapped_data`, `emission_factor_used`,
`calculated_emissions_kg_co2e`, QC and customer-review columns) and the
first-class `issues` table (ADR-V3-009) for validation findings. **No database,
schema, RLS or migration was modified.**

## 2. Capability → endpoint map

| Capability | Endpoint | Notes |
|---|---|---|
| Processing dashboard | `GET /api/v3/processing/dashboard` | batches, items per status/stage, QC + customer-review queue lengths, % complete |
| Processing status | `GET /api/v3/processing/status` | per-stage pipeline counts, total items, % complete, active batches |
| Batch progress | `GET /api/v3/processing/batches/{id}/progress` | per-status + per-stage counts + % complete |
| Batch lifecycle | `POST /batches/{id}/start`, `/complete`, `/cancel` | org admin; start assigns + stamps `in_progress`; complete stamps `completed_by/at` + `actual_completion_date` |
| Extraction (data entry) | `POST /items/{id}/start` + `/extract` | claim stage → save `extracted_data` → `extracted` (`extracted_by/at`) |
| Mapping | `POST /items/{id}/map` + `GET /items/{id}/mapping-options` | `mapped_data` + facility/asset/supplier/factor refs; suggestions from org facilities/assets/suppliers + factor activity search |
| Validation | `POST /items/{id}/validate` | pure rules → blocking findings persisted as `issues` (work_item-scoped) → item back to `mapping` or forward to `validated` |
| Calculation | `POST /items/{id}/calculate` | `calculated_emissions_kg_co2e` (≥ 0) → `calculated` |
| Customer review | `GET /processing/customer-review` + `POST /items/{id}/customer-review` | approve → `approved`; reject (reason required) → `rejected` + rework |
| Issues | `GET /api/v3/processing/issues` | org-scoped, optional status filter |
| Document processing workspace | `GET /items/{id}/workspace` | split-screen contract: `source` (left) + `data` (right) + status/QC/customer-review + issues + allowed transitions |
| Split-screen source/data | `source.file_url/viewer_url`, `data.extracted_data/mapped_data/…` | viewer + form payload in one response |
| Data-entry workflow | `GET /next-item` + `start`/`extract` | operator high-volume flow (oldest-first), per stage |
| Customer verification workflow | `customer-review` queue + approve/reject | decision stamped `customer_reviewed_by/at`, reason + notes stored |

## 3. What was built

**Domain (`domain/partners.py`)** — extended `ManualExtractionBatch` (est/actual
completion, SLA breach, assignment, QC, notes, actor, completion stamps) and
`ManualExtractionItem` (document_processing_queue_id, emission_factor_used,
extracted_at, customer-review fields, updated_at); added `BATCH_STATUSES`,
`ITEM_STATUSES`, `WORKFLOW_STAGES`, `WORKFLOW_STAGE_STATUSES`,
`ITEM_STATUS_FLOW` (state machine) and `can_transition_item_status()`.

**Repository (`data/manual_extraction.py`)** — full column lists + mappers;
batch lifecycle (`update_batch`, `complete_batch`, `cancel_batch`,
`batch_progress`); item workflow (`save_extracted_data`, `save_mapped_data`,
`save_calculation`, `set_item_status`, `customer_review`); queues/dashboards
(`list_items_for_org`, `list_by_stage`, `next_item`, `list_customer_review`,
`get_item_org`, `count_qc_pending`, `workflow_dashboard`, `workflow_status`).

**Issues (`data/issues.py`)** — added `list_for_work_item(work_item_id)` and
`list_for_batch(batch_id)`.

**Engine (`engines/processing_workflow.py`)** — pure `validate_processing_item`
rules (`EXTRACTION_MISSING_FIELD`, `INVALID/NEGATIVE_QUANTITY`, `MISSING_UNIT`,
`MAPPING_MISSING`, `FACTOR_MISSING`, `NEGATIVE_RESULT`) + `has_blocking_findings`.

**Router (`api/v3_processing_workflow.py`)** — 18 endpoints under
`/api/v3/processing/*`; org-scoped (`require_org_member`/`require_org_admin` +
`ensure_org_access` via batch), transition-checked (409 on illegal transitions),
422 on missing factor/rejection reason/negative result.

**Wiring** — `api/router.py` includes the new router.

**Tests** — `tests/unit/api/test_v3_processing_workflow.py`: route registration
(18 fragments) + validation rules + transition-table coverage.

## 4. Files created / changed

Created: `engines/processing_workflow.py`, `api/v3_processing_workflow.py`,
`tests/unit/api/test_v3_processing_workflow.py`, and this report.

Changed: `domain/partners.py` (constants + extended models), `data/manual_extraction.py`
(columns, mappers, workflow methods), `data/issues.py` (work-item/batch lists),
`api/router.py` (router include).

## 5. Design decisions

1. No schema changes: the RC2 `manual_extraction_items` table already carries
   every pipeline column; validation findings use the first-class `issues` table
   (ADR-V3-009) linked via `work_item_id`.
2. Item `status` is the pipeline position; `WORKFLOW_STAGES` groups statuses
   into the seven core stages; illegal transitions return HTTP 409.
3. Validation failures and customer rejections route items back to
   `mapping`/`extracting` (rework loop) instead of adding statuses.
4. QC remains the orthogonal CarbonTally-staff gate (`v3_qc.py`); workflow
   batch/queue endpoints count `qc_pending` (extracted + no quality_score).
5. Mapping suggestions reuse the org facilities/assets (OrganizationsRepository),
   suppliers (SuppliersRepository) and factor activity search
   (EmissionFactorsRepository.find_by_activity) — no new index surfaces.
6. Customer verification is item-level on `manual_extraction_items`
   (`customer_reviewed_by/at/approved/rejection_reason/notes`); document-level
   verification stays on `/api/v3/verifications` (customer_documents).

## 6. Verification status

**Executed (static):** every new/modified file was created and consistency-checked
(domain constants match the RC2 table columns verified from
`CarbonTally_DB_Schema_V3M2.sql`; repository methods used by the router all
exist on the expected `RepositoryBundle` members; auth guards resolve to
`auth.py`; router mounted in `api/router.py`; tests exercise the validation
engine and route registration without a database).

**Not executed (environmental):** `pytest`/`uvicorn`/live-DB checks could not
run because the shell tool remains wedged on a hung `docker exec` from an
earlier session (documented previously). This is an environment limitation.

## 7. Commands to run

```bash
cd backend
python -m py_compile domain/partners.py engines/processing_workflow.py \
    data/manual_extraction.py data/issues.py api/v3_processing_workflow.py
python -m pytest tests/unit/api/test_v3_processing_workflow.py -q
python -m pytest tests/unit/api/test_v3_new_capabilities.py -q
python -m pytest tests/unit/api/test_v3_routes_exposed.py -q
python -m pytest tests/unit -q
uvicorn main:app --host 0.0.0.0 --port 8000   # then curl /openapi.json
```

## 8. Limitations & next steps

- Runtime/DB verification pending (see §6); repository SQL assumes the RC2
  column shapes verified from the schema.
- The split-screen contract returns `viewer_url` (= `file_url`) — PDF/image
  rendering and page/coordinate highlighting (Phase-2 span model) are frontend
  + additive-schema follow-ons.
- Calculation is recorded by the operator (`POST /calculate`); wiring the
  authoritative `engines/calculation.py` (snapshot + hash provenance) to write
  `emissions_logs` and stamp `emission_factor_used` is a next phase.
- Validation currently uses lightweight item rules; the org-level A1–A9
  `engines/validation.py` engine can be layered in later.
- Processing-company (entity) assignment of batches/items and entity-scoped
  staff access are follow-ons (entity policies deferred to ADR-V3-010).
- Operator assignment per item (`assigned_to` on items) is not yet persisted —
  items are claimed via status transitions.

## 9. Risks

1. Untested SQL against live tables — mitigated by integration tests before use.
2. `list_qc_pending` (admin QC queue) remains global; org-scoped QC counts are
   provided on the dashboard — confirm product intent for QC role isolation.
3. Status vocabulary is free-text at the DB (no CHECK on
   `manual_extraction_items.status`); all writes flow through the state machine.
4. Item statuses written by the legacy `update_item` (`status='extracted'`)
   remain compatible with the new pipeline.


