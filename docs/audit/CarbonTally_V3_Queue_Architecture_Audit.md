# CarbonTally V3 Queue & Work Management Architecture Audit

## 1. Executive Summary

CarbonTally currently has **more than the four named queue structures**. A read-only
trace of the actual schema, migrations, backend routes, admin frontend, and prior
audits identifies **fourteen queue-like tables or table families** that participate in
work management today.

The decisive finding is that the system already **implicitly separates "technical
state machines" from "human work items"** — but it never names the distinction and
never consolidates it:

- **`manual_review_queue` is the de-facto human work-item store.** It is the only
  queue table actively produced and consumed by live code (admin routes
  `assignments.py`, `reviews.py`, `dashboard.py`, `analytics.py`, `workload.py`;
  customer routes; upload route; admin frontend). It already carries status,
  priority, priority-score, SLA deadline/breach, escalation level, assignment,
  review timing, customer notification, batch linkage and audit history.
- **`document_processing_queue` and `report_generation_queue` are technical state
  machines** (document AI-extraction pipeline state; report-output persistence).
  `report_generation_queue` is actively used by the v2.1 `ReportsRepository`
  (`backend/data/reports.py`). `document_processing_queue` is constrained and
  documented but has **no active producer in the current backend** — its only
  writers are legacy monolithic copies (`backend/main copy.py`, `main copy 2.py`).
- **`processing_queue` (+ `processing_assignments` + `processing_steps`) is a
  dormant generic task queue.** It has RLS, claim indexes, SLA columns and FK
  children (`approval_requests`, `qc_checks`) but **zero active code paths** write
  or read it. The RC1 worker-architecture design intended it as the generic worker
  queue; that design was never wired to live routes.

There is **no canonical Work Item model** and **no Queue Management subsystem**.
The four "queues" overlap because they were designed at different times for
different work surfaces and each duplicated a status machine, assignment columns
and SLA columns. `processing_queue`, `processing_assignments`, `manual_review_queue`,
`upload_batches`, `manual_extraction_*` and `review_assignment_history` are the
overlapping set.

## 2. Scope, Method & Evidence

This is a **read-only** audit. No code, schema, migration, RLS, Storage, API,
frontend, or test file was modified. No database was written. The factor baseline
(DEFRA 7,029 / SEAI 20 / TOTAL 7,049) is untouched.

| # | Source | Role |
|---|--------|------|
| E1 | `supabase/migrations/00000000000000_init_schema.sql` | Table definitions for all queue/work tables |
| E2 | `supabase/migrations/schema_snapshot.sql` | Live-schema dump (RLS policies, indexes) |
| E3 | `database/rc1/001-007_rc1_*.sql`, `database/rc2/*.sql` | Constraint / index / RLS hardening, claim indexes |
| E4 | `backend/routes/admin/{assignments,reviews,dashboard,analytics,workload,extraction}.py` | Admin producers/consumers |
| E5 | `backend/routes/{upload,customer_documents,documents_main,customer_dashboard,notifications,reports}.py` | Other producers/consumers |
| E6 | `backend/data/reports.py` | v2.1 `ReportsRepository` → `report_generation_queue` |
| E7 | `backend/main copy.py`, `main copy 2.py`, `process_emissions.py` | Legacy producers (monolithic app) |
| E8 | `admin/src/**` (ManualReviewQueue.jsx, ReviewAssignment.js, Dashboard.js, LiveQueueStats.jsx, ReviewModal, ReviewExtractionModal, ExtractionErrorReview, WorkHub.jsx, RealtimeContext.jsx) | Admin frontend direct Supabase consumers |
| E9 | `docs/Final_Kimi/.../05_worker_architecture.md`, `03_module_breakdown.md`, `CarbonTally RC1 — Independent Database Audit.md`, `carbontally_rc2_freeze.agent.final.md` | Design intent + independent DB audit |
| E10 | `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md`, `CarbonTally-v2.1-Traceability-Matrix-v1.0.md` | Prior V3/traceability assessments |
| E11 | `API_ENDPOINTS.md`, `docs/architecture/RealTImeImplementation`, `docs/architecture/changelog.md` | Endpoint + realtime inventory |

### 2.1 Definitive structure inventory (all queue/work structures found)

| Structure | Found where | Active code? |
|-----------|-------------|--------------|
| `processing_queue` | init schema E1; rc1 claim idx E3 | **No** active producer/consumer |
| `processing_assignments` | init schema E1 | **No** active producer/consumer |
| `processing_steps` | init schema E1 | **No** active producer/consumer |
| `document_processing_queue` | init schema E1; rc1/rc2 E3 | **No** active producer (legacy only E7) |
| `manual_review_queue` | init schema E1 | **Yes** (E4, E5, E8) |
| `report_generation_queue` | init schema E1; v2.1 repo E6 | **Yes** (E6, legacy `report_generator.py`) |
| `upload_batches` | init schema E1 | **Yes** (E4/E5 producers; E8 consumers) |
| `manual_extraction_batches` | init schema E1 | **No** active producer (dormant with dpq) |
| `manual_extraction_items` | init schema E1 | **No** active producer |
| `review_assignment_history` | init schema E1 | **Yes** (written by `assignments.py` E4) |
| `reassignment_history` | init schema E1 | **Partial** — targets `processing_assignments` (dormant) |
| `staff_workload` | init schema E1 | **Yes** (maintained by `reviews.py`, read by `workload.py`/`dashboard.py`) |
| `staff_performance` / `staff_daily_performance` / `team_performance` | init schema E1 | Metrics tables (dashboards) |
| `queue_settings` | init schema E1 | **Yes** (`workload.py` get/put E4) |
| `sla_definitions` / `sla_compliance` / `business_hours` | init schema E1 | Config/records (SLA monitor reads `manual_review_queue` E4) |
| `approval_requests` / `approval_decisions` | init schema E1 | **No** active producer (FK to `processing_assignments`) |
| `customer_verifications` / `customer_review_log` | init schema E1 | **Partial** (customer approval surface) |
| `processing_audit_trail` / `review_audit_trail` / `processing_time_log` / `verification_activity_log` | init schema E1 | History tables |
| `draft_entries` / `user_feedback` | init schema E1 | Draft / issue-like surfaces (`user_feedback.assigned_to`) |
| `export_history` | init schema E1 | Output log |
| `internal_tasks` / `task_assignments` | rc1 trigger list + module docs only | **Not in init schema** — intent only, not live |

## 3. Per-Queue Deep Analysis

### 3.1 `processing_queue` — dormant generic task queue

- **Definition** (E1 lines 737-760): `id, document_id, organization_id (FK, ON DELETE CASCADE), batch_id, document_type, priority, priority_score, queue_status CHECK (pending|assigned|in_progress|on_hold|completed|cancelled), sla_deadline, sla_breached, estimated_completion_hours, actual_completion_hours, page_count, file_size_bytes, notes, metadata, created_at/updated_at/created_by/updated_by`.
- **Purpose**: generic worker/task queue. RC1 worker architecture (E9 `05_worker_architecture.md`) designed it as the generic worker queue (e.g., `document_type='notification'` rows for a notification worker, claimed via `processing_queue_claim_idx`).
- **Who creates**: **nobody active.** Only design docs + legacy monolithic app intent. No insert path found in active backend routes (E4/E5). `approval_requests`/`qc_checks` FK to `processing_assignments` → `processing_queue`, so the approval/QC chains are dormant too.
- **Who consumes**: nobody active.
- **Lifecycle**: `pending → assigned → in_progress → on_hold/completed/cancelled`. Never exercised by live code.
- **RLS**: rc1 enabled RLS + `processing_queue_tenant_select/insert/update` via `is_org_member(uuid)` (E3, pgdelta catalog).
- **Verdict**: **schema + claim index + SLA columns exist, but it is a dormant queue** — the strongest evidence a "generic queue" was designed but never wired.

### 3.2 `processing_assignments` / `processing_steps` — dormant assignment/step tracking

- `processing_assignments` (E1 762-776): `queue_id (FK→processing_queue), assigned_to, assigned_by, assignment_status, started_at, completed_at, processing_time_seconds, notes`.
- `processing_steps` (E1 778-793): `assignment_id (FK→processing_assignments), step_name, step_order, status, started_at/completed_at, duration_seconds, notes, errors`.
- **Verdict**: dormant. `approval_requests` and `qc_checks` reference `processing_assignments`, so the same un-wired cluster.

### 3.3 `document_processing_queue` (dpq) — document AI-extraction state machine

- **Definition** (E1 680-735): wide stage-prefixed column groups — `ai_*` (ai_extraction_result, ai_confidence_score, ai_extraction_method, ai_mapped_facility/asset/supplier_id, ai_mapping_confidence, ai_mapped_document_type_code), `manual_*` (manual_requested_by/assigned_to/extraction_result/notes…), `qc_*` (qc_required, qc_by, qc_at, qc_notes, qc_approved), `customer_*` (customer_reviewed_by, customer_approved, customer_rejection_reason), plus `calculated_emissions_kg_co2e`, `emission_factor_used` (renamed from `defra_factor_used` by RC2 R2), `batch_id`, `batch_sequence`, `processing_cost`, `billing_currency`.
- **Status vocabulary** (CHECK): `pending|processing|ai_extracted|manual_review|manual_extraction|qc|customer_review|approved|rejected|completed|failed`.
- **Purpose**: full document-processing workflow state (AI → manual → QC → customer). RC2 freeze (E9) called this the "single processing-queue direction" (frozen ADR) — the wide stage-prefixed columns are the deliberate alternative to split stage tables.
- **Who creates**: **no active backend route.** Legacy monolithic copies (E7) were the intended producers. The active `customer_documents` route (E5) manages `customer_documents` + `manual_review_queue`, not dpq.
- **Who consumes**: design docs describe staff/customer workspaces (OcrReviewWorkspace, E9); no active v2.1 route found.
- **RLS**: tenant policies (E3 pgdelta: `document_processing_queue_tenant_insert` → `is_org_member`). rc1 added `dpq_claim_idx` partial index.
### 3.4 `manual_review_queue` — the active human work-item store

- **Definition** (E1 1818-1851): `organization_id (FK), file_url, file_name, file_type, data_type, status, auto_extraction_result JSONB, manual_extraction_result JSONB, assigned_to, priority, customer_notes, staff_notes, completed_at, estimated_completion_hours, batch_id (FK→upload_batches), assigned_by, started_at, completed_by, data_entry JSONB, review_time_seconds, priority_score, sla_deadline, sla_breached, escalation_level, customer_notified_at, customer_responded_at, customer_document_id`.
- **Purpose**: manual review work items. RC2-028 made `organization_id` NOT NULL — a first-class tenant table.
- **Who creates**: active routes `upload.py` (file→review), `customer_documents.py`, `documents_main.py`; legacy copies E7. Admin frontend updates status/notes.
- **Who consumes**: `admin/assignments.py`, `admin/reviews.py` (queue/start/complete/reorder/escalate/SLA-monitor/reassign), `admin/dashboard.py`, `admin/analytics.py`, `admin/workload.py`, `customer_dashboard.py`, `customer_documents.py`, `reports.py`, `notifications.py`; admin frontend (ManualReviewQueue.jsx, ReviewAssignment.js, Dashboard.js, LiveQueueStats.jsx, ReviewModal, ReviewExtractionModal, ExtractionErrorReview, WorkHub.jsx) + RealtimeContext.
- **Status vocabulary (used in code)**: `pending, assigned, in_progress, completed, rejected` (+ `processing`, `failed`, `review`, `escalated` across code/UI history).
- **RLS**: tenant policies `manual_review_queue_tenant_select/insert/update` (is_org_member + is_org_consultant). **Legacy permissive policies also exist in the dump** (`"Staff can insert queue items" WITH CHECK (true)`, `"Allow authenticated users to update queue items"`, `"Allow authenticated users to view pending queue items"`) — see §16.
- **Verdict**: **the de-facto canonical human work-item table.** Already contains the majority of V3 Work Item capabilities (status, priority+SLA+escalation, assignment, timing, customer interaction, batch linkage, org isolation).

### 3.5 `report_generation_queue` — report output persistence/status

- **Definition** (E1 893-922): `organization_id, user_id, template_id, report_type, reporting_year, report_name, data_sources JSONB, status, progress_percentage, current_step, generated_content JSONB, user_edits JSONB, final_report_url, final_report_file_name, final_report_size_bytes, ai_model_used, ai_tokens_used, ai_cost, ai_processing_time_ms, started_at, completed_at, error_log, metadata`.
- **Purpose**: report-generation job state + output persistence. The v2.1 `ReportsRepository` (`backend/data/reports.py`) persists `GeneratedReport` here (RC2 has no `generated_reports` table). Legacy `report_generator.py` writes `final_report_url`.
- **Who creates**: v2.1 Phase 9C/10 `generate-report` → `ReportsRepository`; legacy report generator.
- **Who consumes**: `backend/data/reports.py` (get/update/delete), reports routes; `report_generation_queue_claim_idx` exists for a hypothetical worker.
- **Verdict**: **a persistence/status table for output generation, not a human work queue.** It should remain outside the V3 Work Management system (specialized technical mechanism).

## 4. Additional Queue-Adjacent Structures

### 4.1 `upload_batches` — batch grouping (the batch anchor)

`id, organization_id (FK), batch_name, total_files, processed_files, status, created_by_user_id, metadata, batch_type, estimated_processing_time, error_count, manual_extraction_requested, manual_extraction_batch_id`.
Active producer: `routes/upload.py`; consumers: `admin/assignments.py`, `admin/reviews.py`, `admin/extraction.py`, admin frontend (batch progress). `manual_review_queue.batch_id` FK → `upload_batches` (ON DELETE CASCADE). RC2-028 made `organization_id` NOT NULL. **Verdict**: keep — the natural batch/grouping anchor; V3 "batch = grouping, work item = atomic" maps directly onto it.

### 4.2 `manual_extraction_batches` / `manual_extraction_items` — dormant manual-extraction workflow

Per-page costing (`total_pages`, `price_per_page`, `total_cost`, currency), QC columns, `document_processing_queue_id` link on items. Dormant with dpq (no active producer). **Verdict**: consolidate later with the dpq path; not needed for a V3 work-item abstraction.

### 4.3 `approval_requests` / `approval_decisions` — dormant approval chain

FK to `processing_assignments` (dormant). `approval_type, status, priority, notes, sla_deadline` + `decision_by, decision, reason, comments, metadata`. **Verdict**: the approval vocabulary exists but is wired to a dormant queue; V3 approval layers will need it re-pointed at the canonical work item or kept as a parallel approval surface (`customer_verifications` already serves customer approval).

### 4.4 `customer_verifications` / `customer_review_log` — customer approval surface

`customer_verifications`: `customer_document_id, organization_id, customer_member_id, status, submitted_at/by, verified_at/by, rejected_at/by, revision_requested_at/by, is_escalated, escalation_reason, escalated_at, metadata`. RC2 made `organization_id` NOT NULL (RC2-028). Real-time enabled (`REPLICA IDENTITY FULL`, E11). **Verdict**: keep — the customer-approval layer already exists; escalation flags on it plus `manual_review_queue.escalation_level` cover the escalation concept.

### 4.5 Staff ops & metrics

- `staff_workload` (daily): `staff_id, assigned_tasks, in_progress_tasks, pending_tasks, completed_today, workload_score, capacity_percentage, date`. Maintained by `reviews.py::update_staff_workload`, read by `workload.py`, `dashboard.py`, WorkHub.
- `staff_performance`, `staff_daily_performance`, `team_performance`, `dashboard_metrics`: period metrics.
- `queue_settings`: `setting_key UNIQUE, setting_value JSONB` — holds `max_reviews_per_staff`, `sla_hours`, `auto_assign_enabled`, `escalation_hours`, `priority_weights` (read/written by `workload.py`). **This is the existing auto-assignment config surface.**
- `sla_definitions` (`document_type, priority_level, sla_hours, escalation_hours, is_active`), `sla_compliance` (`queue_id, sla_deadline, is_breached, breach_time_minutes`), `business_hours` (`day_of_week UNIQUE, start/end, is_holiday, timezone`).
- `processing_time_log` (assignment activity timing), `processing_audit_trail` (queue_id + action + JSONB diffs), `review_audit_trail` (review_id + action + diffs).

### 4.6 Issue-like / draft surfaces

`draft_entries` (customer draft data), `user_feedback` (`assigned_to, status, severity, resolved_at`), `export_history`, `notifications` / `notification_delivery`. `internal_tasks` / `task_assignments` appear **only** in rc1 trigger lists and module docs — **not** in the init schema (intent, not live).

## 5. Producer/Consumer Trace Table

| Structure | Producer | Consumer | Route/Module | Purpose |
|---|---|---|---|---|
| `processing_queue` | — (none active) | — | schema only; `05_worker_architecture.md` design | generic worker queue (dormant) |
| `processing_assignments` / `processing_steps` | — | — | schema only | assignment/step tracking (dormant) |
| `document_processing_queue` | legacy `main copy*.py` (AI path) | staff/customer workspaces (design) | schema only in active app | document AI-extraction state machine |
| `manual_review_queue` | `upload.py`, `customer_documents.py`, `documents_main.py`, legacy main | admin routes + admin frontend + customer routes | assignments, reviews, dashboard, analytics, workload, customer_documents, customer_dashboard, reports, notifications | human review work items (ACTIVE) |
| `report_generation_queue` | `ReportsRepository` (v2.1), legacy `report_generator.py` | `data/reports.py`, reports routes | Phase 9C/10, reports | report output persistence |
| `upload_batches` | `upload.py`, legacy main | admin assignments/reviews/extraction, admin frontend | batch progress/completion | batch grouping (ACTIVE) |
| `manual_extraction_batches/items` | — (dormant) | — | schema only | manual extraction workflow |
| `review_assignment_history` | `assignments.py` | audits | assignments.py | assignment attribution for reviews (ACTIVE) |
| `reassignment_history` | — (targets dormant `processing_assignments`) | — | schema only | reassignment attribution |
| `staff_workload` | `reviews.py` | `workload.py`, `dashboard.py`, WorkHub | admin | per-day workload counters (ACTIVE) |
| `queue_settings` | `workload.py` | `workload.py` | admin | queue/auto-assign/SLA config (ACTIVE) |
| `sla_compliance` | — | `dashboard.py` | admin | SLA records |
| `approval_requests/decisions` | — (dormant) | — | schema only | approval chain (dormant) |
| `customer_verifications` | customer flows | customer portal | realtime | customer approval (PARTIAL) |

## 6. Queue vs Work Item

The current architecture **does not distinguish a Work Item from a Queue**. Evidence:

- The four "queues" are **row stores**: each row is a piece of work with an embedded `status` column. None is a routing table of "which queue does this item sit in".
- `manual_review_queue` is both the work item *and* its queue. Routing is simulated by filtering `status='pending'` and `assigned_to IS NULL` (`admin/assignments.py::get_available_reviews`).
- `processing_queue` similarly embeds routing in `queue_status`.
- **Implication**: a V3 canonical Work Item can be added *without* removing any existing table, because the existing tables are already item stores — the "queue" concept is a query over `status`. This makes the hybrid Option D (canonical work-item abstraction over existing stores) the lowest-risk path.

## 7. V3 Work Item — Candidate Attributes vs Existing State

| Potential Work Item attribute | Exists today? | Where |
|---|---|---|
| `work_item_id` | Partial | `manual_review_queue.id`, `processing_queue.id`, `report_generation_queue.id` (no unified id) |
| `work_type` | No | Implied by table (review vs processing vs report); no discriminator |
| `source_type` | Partial | `manual_review_queue.data_type`, `processing_queue.document_type`, dpq `processing_type` |
| `customer_id / organization_id` | **Yes** | `organization_id` FK on all three queue tables + `upload_batches` |
| `batch_id` | **Yes** | `manual_review_queue.batch_id` → `upload_batches`; dpq `batch_id`; `processing_queue.batch_id` |
| `document_id` | Partial | `manual_review_queue.customer_document_id`; dpq `customer_document_id`; `processing_queue.document_id` |
| `processing_entity_id` | **No** | No entity concept anywhere (V3-003 conditional) |
| `assigned_team_id` | **No** | No `teams` table in init schema (only in DB-migration docs) |
| `assigned_worker_id` | **Yes** | `manual_review_queue.assigned_to`, `processing_assignments.assigned_to` |
| `status` | **Yes** | Per-table CHECK vocabularies (not unified) |
| `priority` / `priority_score` | **Yes** | `manual_review_queue.priority` + `priority_score`; `processing_queue.priority` + `priority_score` |
| `sla` / `due_at` | **Yes** | `sla_deadline` on `manual_review_queue`/`processing_queue`; `sla_definitions`/`sla_compliance`/`business_hours` |
| `created_at` / `started_at` / `completed_at` | **Yes** | All three queue tables |
| `retry_count` | **No** | No retry counter on any queue table |
| `escalation_level` | **Yes** | `manual_review_queue.escalation_level`; `customer_verifications.is_escalated` |
| `parent_work_item_id` | **No** | No parent/child work-item relationship |
| `assignment_history` | Partial | `review_assignment_history` (review_id) active; `reassignment_history` (assignment_id) dormant |
| `metadata` | **Yes** | `metadata JSONB` on all three queue tables |

**Conclusion**: ~13 of 19 candidate attributes already exist in at least one table; the gaps are `work_type`, `processing_entity_id`, `assigned_team_id`, `retry_count`, `parent_work_item_id`, and a unified identity. These gaps are exactly the V3-003 (entity model) and V3-004 (work item) decision surface.

## 8. Work Types

Distinct work types that exist in the current architecture:

| Work type | Existing structure | Active? |
|---|---|---|
| DOCUMENT_AI_EXTRACTION | `document_processing_queue` (`ai_extracted`, `ai_*` cols) | No active producer |
| MANUAL_DATA_ENTRY / MANUAL_REVIEW | `manual_review_queue` (`data_entry`, `manual_extraction_result`) | **Yes** |
| QC_REVIEW | `qc_checks`/`qc_errors`/`qc_checklists` (FK `processing_assignments`) + dpq `qc_*` cols | Partial (schema; FK chain dormant) |
| CUSTOMER_REVIEW / APPROVAL | `customer_verifications`, `customer_review_log`, dpq `customer_*` cols | Partial (customer_verifications wired to realtime) |
| REPORT_GENERATION | `report_generation_queue` | **Yes** (v2.1 repository) |
| FILE_UPLOAD / BATCH | `upload_batches` | **Yes** |
| ISSUE_RESOLUTION | `user_feedback` (assigned_to, status) | Partial (feedback surface) |
| EXPORT | `export_history` | Log only |
| FACTOR_REVIEW | — | **No** (V3-002 customer factors future) |
| CORRECTION / REPROCESSING | `draft_entries`, `report_versions` | Partial (versions exist) |

V3 only genuinely needs the types already proven: document extraction, manual data entry/review, QC, customer review, report generation, plus **factor review** (new, tied to V3-002). No enum should be created yet — work type should stay a domain constant until the Work Item model is approved.

## 9. Work Item Lifecycle

The requested canonical lifecycle (QUEUED → ASSIGNED → IN_PROGRESS → SUBMITTED → VALIDATION → QC → APPROVED → COMPLETED, plus REJECTED/CORRECTION_REQUIRED/REASSIGNED/ESCALATED/ON_HOLD/FAILED/CANCELLED/REOPENED) is **partially supported by combining three existing vocabularies**:

- `manual_review_queue`: pending → assigned → in_progress → completed / rejected (+ `processing`, `failed`, `escalated` in code/UI history). Supports REASSIGNED via `/queue/reassign` + `review_assignment_history`; ESCALATED via `/queue/escalate` (+`escalation_level`).
- `document_processing_queue` CHECK: pending|processing|ai_extracted|manual_review|manual_extraction|qc|customer_review|approved|rejected|completed|failed — the closest to the full pipeline lifecycle.
- `customer_verifications`: submitted → verified/rejected/revision_requested/escalated.

**No single table spans the full lifecycle.** V3 either unions these statuses under a Work Item domain state (map) or extends `manual_review_queue.status`. No new status table is required; a domain-level status map is sufficient.

## 10. Multi-Entity Processing Test (500 documents / 5 entities)

Scenario: Customer uploads 500 documents, split across CarbonTally + entities A–D (100 each); Worker A completes 30 of 100, then becomes unavailable; the remaining 70 must be reassigned without losing attribution/history/SLA/audit/ownership/isolation.

**What the current architecture supports:**
- **Batch grouping**: `upload_batches` (total_files/processed_files/status) — one batch row per upload; per-item progress tracked by counting remaining `manual_review_queue` rows for `batch_id` (implemented in admin frontend `ManualReviewQueue.jsx`).
- **Per-item work**: `manual_review_queue` rows (atomic, `organization_id`, `batch_id`, `assigned_to`, status).
- **Reassignment with history**: `POST /queue/reassign` writes `review_assignment_history` (previous/current assignee, action, note) — attribution preserved.
- **SLA**: per-item `sla_deadline`/`sla_breached` + `sla_compliance` records.
- **Audit**: `review_audit_trail`, `processing_audit_trail`, `staff_activity_log`.
- **Org isolation**: tenant RLS on `manual_review_queue`/`upload_batches` via `is_org_member`.

**What it does NOT support (V3 gaps):**
- **Entity dimension**: no `entity_id` on any table; "Entity A/B/C/D" cannot be represented. Staff model is internal-only (`staff_profiles`); Babui is `company_name` metadata only (V3-003).
- **Entity split**: a single `upload_batches` row cannot be partitioned across entities without a new field or multiple batch rows.
- **Entity isolation**: no RLS helper for "member of processing entity"; `is_org_member`/`is_org_consultant` only.
- **Entity-level SLA/capacity**: `staff_workload` is per-staff (internal); no entity capacity.
- **Worker unavailable → entity reassignment**: works within staff via `/queue/reassign`; there is no entity-scoped equivalent.
- **Partial-work recovery across entities**: `reassignment_history` targets `processing_assignments` (dormant) rather than `manual_review_queue`; the active history is `review_assignment_history`.

**Conclusion**: the 500-doc case is supportable **only after a conditional entity-model decision** (V3-003). The queue/assignment mechanics already exist; the missing piece is the entity scope, not another queue.

## 11. Queue Management Model Options (A/B/C/D)

**OPTION A — Keep existing queues separately.** Rejected for V3. Evidence: duplicate state machines (3+ status vocabularies), duplicate assignment logic (manual_review_queue.assigned_to vs processing_assignments.assigned_to), duplicate SLA logic (per-table sla_deadline vs sla_definitions/sla_compliance), duplicate audit (review_assignment_history vs reassignment_history vs review_audit_trail vs processing_audit_trail). This is the current state and it is exactly the overlap problem.

**OPTION B — Select one existing queue as canonical.** Partially viable: `manual_review_queue` is the de-facto human work-item store and has the richest surface (escalation, SLA, priority-score, customer interaction, batch). But it cannot represent document-extraction state (dpq) or report output (report_generation_queue), and it has no entity dimension. B alone forces non-human work into a human-shaped table.

**OPTION C — Canonical Work Item model + logical queues.** Viable for the human operations surface. A domain `WorkItem` abstraction over `manual_review_queue` (+ optional `work_items` table) with logical queues ("CarbonTally queue", "Entity A queue") as filtered views over work items. Requires the entity-model decision (V3-003) to be useful for multi-entity allocation.

**OPTION D — Dedicated Queue Management subsystem (Work Items / Queues / Assignments / Queue Rules / Routing / Capacity / SLA / Escalation / History).** Overkill at this stage. Evidence: the current system already has the underlying tables (manual_review_queue = work items, queue_settings = rules, review_assignment_history = history, sla_* = SLA, staff_workload = capacity counters, escalation_level = escalation). A full subsystem would duplicate all of these. **D is unnecessary today; the V3 assessment's "five-layer approval" and "multi-entity allocation" do not require a new subsystem.**

**Recommended**: **Hybrid** — technical state machines stay (dpq, report_generation_queue); human operations get a canonical Work Item abstraction over the active `manual_review_queue` surface (C-style), extended conditionally with entity scope. This is the "hybrid (D)" from the V3 scope boundary, implemented at minimal cost.

## 12. Auto-Assignment

- **Config exists**: `queue_settings` holds `auto_assign_enabled`, `max_reviews_per_staff`, `sla_hours`, `escalation_hours`, `priority_weights`; read/written by `admin/workload.py` (`GET/PUT /queue/settings`, admin-only).
- **Capacity exists**: `staff_workload` (`workload_score`, `capacity_percentage`, daily counters) maintained by `reviews.py::update_staff_workload`.
- **Priority exists**: `manual_review_queue.priority` + `priority_score`; ordering by `priority_score DESC, created_at` in `assignments.py`.
- **Skills**: no skill dimension anywhere.
- **Auto-assignment engine**: **does not exist.** The V3-009 `AutoAssignmentEngine` is correctly marked NEW in the V3 assessment. The building blocks (config + capacity + priority) already exist; an engine would orchestrate them, not require new tables (unless entity-scoped → conditional).

## 13. Configuration

| Config | Table | Fields | Used by |
|---|---|---|---|
| Queue rules | `queue_settings` | `setting_key`/`setting_value` (max_reviews, sla_hours, auto_assign, escalation_hours, priority_weights) | `workload.py` |
| SLA | `sla_definitions` | `document_type, priority_level, sla_hours, escalation_hours, is_active` | config; not read by active routes found |
| SLA records | `sla_compliance` | `queue_id, sla_deadline, is_breached, breach_time_minutes` | `dashboard.py` |
| Working hours | `business_hours` | `day_of_week UNIQUE, start/end, is_working_day, is_holiday, timezone` | config; SLA/deadline calc |
| System | `system_settings` | key/value | platform config |

These can support a future Queue Management System **without schema change**; they are the existing configuration surface.

## 14. Database Relationship Map (Conceptual vs Actual)

Conceptual target:

```
Batch (upload_batches) → Document (customer_documents / dpq)
  → Work Item (canonical)
  → Queue (logical: CT / Entity A / ...)
  → Assignment (assigned_to / review_assignment_history)
  → Worker/Entity (staff_profiles / [entity])
  → Review/QC (review_audit_trail / qc_checks / customer_verifications)
  → Completion
```

Actual today:

```
upload_batches ──batch_id──▶ manual_review_queue ──assigned_to──▶ staff_profiles
      │                        │  │
      │                        │  └──customer_document_id──▶ customer_documents
      │                        └────review_assignment_history / review_audit_trail
      └─(manual_extraction_batch_id)─▶ manual_extraction_batches ──▶ manual_extraction_items
                                         └──document_processing_queue_id──▶ document_processing_queue
document_processing_queue ──(FK none)──▶ processing_queue (parallel dormant tree)
processing_queue ──▶ processing_assignments ──▶ processing_steps / approval_requests / qc_checks
report_generation_queue ──▶ report_versions / report_comments
```

**Key findings**: (1) the actual map is two parallel trees — the **active manual/review tree** (upload_batches → manual_review_queue → staff) and the **dormant processing tree** (processing_queue → processing_assignments → steps/approvals/QC). (2) `document_processing_queue` sits between them — it is the *document* anchor but has no FK from `manual_review_queue` (only a `customer_document_id` column). (3) There is **no single edge** that connects "batch → work item → assignment → worker" in one canonical path.

## 15. RLS / Security

Current isolation on queue/work structures:

| Structure | RLS | Basis | Notes |
|---|---|---|---|
| `manual_review_queue` | Enabled | `manual_review_queue_tenant_select/insert/update` via `is_org_member(uuid)` + `is_org_consultant(uuid)` | **Legacy permissive policies also present in the dump**: `"Staff can insert queue items" WITH CHECK (true)`, `"Allow authenticated users to update queue items"` (USING auth.role()='authenticated'), `"Allow authenticated users to view pending queue items"`. Postgres ORs permissive policies — a real cross-tenant surface if both policy families are live. **INVESTIGATE / HARDEN.** |
| `document_processing_queue` | Enabled | `document_processing_queue_tenant_insert/...` via `is_org_member` | Tenant policies confirmed in pgdelta catalog |
| `processing_queue` | Enabled | `processing_queue_tenant_insert/...` via `is_org_member` | Tenant policies confirmed |
| `report_generation_queue` | Enabled | tenant policies (rc1 list includes it) | |
| `upload_batches` | Enabled | `upload_batches_tenant_insert` via `is_org_member`; legacy `"Allow batch inserts" WITH CHECK (true)` | same legacy-policy concern |
| `manual_extraction_batches/items` | RC1 independent audit (E9) | child tables of protected parents flagged | **RC1 audit C2**: `manual_extraction_items`, `report_versions`, `report_comments` had no RLS of their own at RC1 |
| `staff_workload` / staff/QC/approval family | Enabled via rc1 Section 2 | `authenticated_read` (any authenticated user can read) | Broad by design; no staff-role RLS predicate |

**V3 implications:**
- **Organization isolation** (Customer A vs B): already enforced for active queue tables via `is_org_member` — adequate baseline.
- **Processing entity isolation** (Entity A vs B): **missing** — requires a new RLS helper (`is_entity_member` or equivalent) conditional on V3-003.
- **Worker isolation** (Worker A vs B's unassigned/private work): not enforceable via RLS today; current model relies on admin route authorization (`require_admin`/`require_role(["admin","staff"])`) + service-role code filtering. `manual_review_queue` is readable by org members, not staff-scoped — `assigned_to` privacy is application-level only.
- **Customer visibility**: customer-role surfaces read `manual_review_queue` for their org via routes; RLS permits org members. OK.
- **External processing entities** cannot access CarbonTally administrative work — there is no entity surface at all (safe today, absent in V3).
- **Legacy permissive policies** (`WITH CHECK (true)` on insert; `USING (true)` on update; `authenticated`-wide policies on manual_review_queue/upload_batches) must be reconciled before V3 (the RC2 freeze applied NOT NULL org but the policy coexistence is unverified). **Do not weaken RLS; resolve policy union.**

## 16. Duplication Analysis

Overlapping concepts across the queue/work structures:

| Concept | Implementations | Overlap |
|---|---|---|
| Work item | `manual_review_queue`, `processing_queue`, `document_processing_queue`, `report_generation_queue`, `manual_extraction_items`, `internal_tasks`(intent) | **High** — 4+ item stores |
| Status machine | 5+ vocabularies (manual_review, dpq, processing_queue CHECK, customer_verifications, approval) | **High** |
| Assignment | `manual_review_queue.assigned_to/by`, `processing_assignments.assigned_to/by`, `review_assignment_history`, `task_assignments`(intent) | **High** |
| Reassignment | `review_assignment_history` (review_id), `reassignment_history` (assignment_id) | **Medium** — different id spaces |
| SLA | `manual_review_queue.sla_deadline/sla_breached`, `processing_queue.sla_deadline/sla_breached`, `sla_definitions`, `sla_compliance`, `approval_requests.sla_deadline` | **High** |
| Escalation | `manual_review_queue.escalation_level`, `customer_verifications.is_escalated/escalation_reason`, `approval_requests`(priority) | **Medium** |
| Workload/capacity | `staff_workload`, `staff_performance`, `staff_daily_performance`, `team_performance`, `dashboard_metrics` | **Medium** |
| Audit | `review_assignment_history`, `reassignment_history`, `review_audit_trail`, `processing_audit_trail`, `verification_activity_log`, `document_activity_log`, `activity_feed`, `audit_logs` | **High** |
| Batch | `upload_batches`, `manual_extraction_batches`, dpq `batch_id`, `processing_queue.batch_id` | **Medium** |

**Root cause**: tables were added feature-by-feature (uploads → manual review → extraction → reporting → staff ops) without a shared work-item model; each added its own status/assignment/SLA/audit columns. `manual_review_queue` + `upload_batches` + `review_assignment_history` + `queue_settings` + `sla_*` + `staff_workload` already form a de-facto work-management surface; the dormant processing tree duplicates it.

## 17. Migration / Consolidation Risk

| Structure | Verdict | Rationale |
|---|---|---|
| `manual_review_queue` | **KEEP / EXTEND** | Active human work-item store; extend conditionally with `work_type`, `entity_id`, `parent_work_item_id` (V3-003) |
| `upload_batches` | **KEEP** | Batch anchor; already FK-linked |
| `review_assignment_history` | **KEEP** | Active attribution for manual path |
| `queue_settings` / `sla_definitions` / `sla_compliance` / `business_hours` / `staff_workload` | **KEEP** | Config + metrics; extend with entity scope conditionally |
| `customer_verifications` / `customer_review_log` | **KEEP** | Customer approval layer |
| `report_generation_queue` | **KEEP** | Specialized report-output mechanism (outside Work Management) |
| `document_processing_queue` | **KEEP** | Technical document-state machine; needs an active producer (V3 document extraction work type) |
| `processing_queue` | **RETIRE LATER / CONSOLIDATE** | Dormant; **do not delete** until V3 Work Item model is approved and its children (`processing_assignments`, `approval_requests`, `qc_checks`) are re-pointed |
| `processing_assignments` / `processing_steps` | **RETIRE LATER / CONSOLIDATE** | Dormant; `qc_checks`/`approval_requests` FK here — re-point before retirement |
| `reassignment_history` | **DEFER** | Targets dormant assignment id-space; reconcile with `review_assignment_history` when work-item model lands |
| `manual_extraction_batches` / `manual_extraction_items` | **CONSOLIDATE later** | Dormant; fold into dpq path when document work type is wired |
| `approval_requests` / `approval_decisions` | **DEFER** | Dormant; re-point at work item when approval layers are built |
| `staff_performance` / `team_performance` / `dashboard_metrics` | **KEEP** | Metrics; entity scope conditional |
| `internal_tasks` / `task_assignments` | **RETIRE the intent** | Not in init schema; do not create — Work Item model supersedes |

**Dependency chain before any retirement**: Work Item model approved → active document work type (dpq producer) → approval/QC re-pointed → then `processing_queue` family can be retired (never deleted; left as inert schema or archived).

## 18. Final Recommendation (answers to the 15 required questions)

1. **Why do we currently have multiple queues?** Feature-by-feature accretion: each work surface (upload→manual review, AI document extraction, report generation, staff ops) was added with its own status/assignment/SLA columns, and a generic `processing_queue` was designed (RC1 worker architecture) but never wired. There was never a shared Work Item model.
2. **Exact difference between the four named queues?**
   - `processing_queue` = dormant generic task queue (designed worker queue, no active code).
   - `document_processing_queue` = document AI-extraction state machine (stage-prefixed ai_/manual_/qc_/customer_ columns; constrained by rc1/rc2; no active producer).
   - `manual_review_queue` = active human review work-item store (pending/assigned/in_progress/completed/rejected + priority/SLA/escalation/assignment/customer).
   - `report_generation_queue` = report output persistence/status (v2.1 ReportsRepository + legacy report generator).
3. **Which are true queues?** None is a routing/claim queue in the active path. `processing_queue` was *designed* as a claim queue (claim index exists) but is dormant. The others are item/state stores.
4. **Which are really work-item stores?** `manual_review_queue` (active), `report_generation_queue` (output jobs), and — technically — `document_processing_queue` (document items).
5. **Which are legacy?** `processing_queue` family, `manual_extraction_*`, `approval_requests/decisions`, `reassignment_history` (targets dormant id-space); `internal_tasks`/`task_assignments` are intent only (not in schema).
6. **Which are actively used?** `manual_review_queue`, `upload_batches`, `review_assignment_history`, `queue_settings`, `staff_workload`, `report_generation_queue` (v2.1), `customer_verifications` (realtime).
7. **Which overlap?** `processing_queue`/`processing_assignments` vs `manual_review_queue`/`review_assignment_history` (assignment+status+SLA+audit duplicated); `manual_extraction_*` vs dpq; `reassignment_history` vs `review_assignment_history`; SLA and audit families.
8. **Do we need a dedicated Work Item model?** Yes for human operations — a domain `WorkItem` abstraction over the active `manual_review_queue` surface. No new physical table is strictly required if `manual_review_queue` is extended.
9. **Do we need a dedicated Queue Management system?** **No.** The existing tables (`manual_review_queue`, `queue_settings`, `staff_workload`, `review_assignment_history`, `sla_*`, escalation columns) already cover the subsystem's parts. A full subsystem (Option D) would duplicate them.
10. **Can an existing table be safely extended?** Yes — `manual_review_queue` is the candidate (add `work_type`, optional `entity_id`, `parent_work_item_id`, `retry_count`), all nullable/backward-compatible; `upload_batches` unchanged.
11. **Physical tables or logical queues?** Hybrid: physical tables stay as item stores; **queues are logical** (filtered views over work items by status + entity). No new queue table.
12. **Canonical V3 Work Management architecture?** Work Items over `manual_review_queue` (C-style) + logical queues + existing assignment/history/SLA/audit surfaces + conditional entity scope (V3-003). Technical state machines (dpq, report_generation_queue) remain internal.
13. **What should eventually be retired?** `processing_queue` family, `manual_extraction_*` (consolidate into dpq path), `reassignment_history` (reconcile into `review_assignment_history`), the `internal_tasks`/`task_assignments` intent. All deferred until the Work Item model + entity decision land.
14. **Minimum database change?** **None required to start** — a Work Item domain abstraction can run on existing tables. **Conditional (if V3-003 approved):** new `data_processing_entities` + nullable `entity_id` on `manual_review_queue`/`upload_batches`/`review_assignment_history`/`staff_workload` + `is_entity_member` RLS helper. Optional: `work_type` + `parent_work_item_id` + `retry_count` columns on `manual_review_queue` (nullable, backward compatible).
15. **Minimum backend change?** A `WorkItem` domain/service layer (create/claim/assign/reassign/complete/escalate) over existing repositories/routes; route thin-wrappers; an `AutoAssignmentEngine` only if V3-009 is in scope; conditional entity-scope filters. No engine redesign.

## 19. Required Final Table

| Structure | Actual Purpose | Active? | Overlap | V3 Role | Recommendation |
|---|---|---|---|---|---|
| `processing_queue` | generic worker task queue (designed) | No | high (vs manual_review_queue) | none (superseded by Work Item) | RETIRE LATER (do not delete) |
| `processing_assignments` | assignment tracking | No | high (vs review_assignment_history) | none | RETIRE LATER |
| `processing_steps` | step tracking | No | medium | none | RETIRE LATER |
| `document_processing_queue` | document AI-extraction state machine | No (no active producer) | medium | document-extraction work type anchor | KEEP; wire a producer |
| `manual_review_queue` | human review work items | **Yes** | low-medium | **canonical human Work Item store** | KEEP / EXTEND (work_type, entity_id?) |
| `report_generation_queue` | report output persistence/status | **Yes** | low | output mechanism (outside Work Mgmt) | KEEP |
| `upload_batches` | batch grouping | **Yes** | low | batch anchor (batch=grouping) | KEEP |
| `manual_extraction_batches` / `items` | manual extraction workflow | No | high (vs dpq) | — | CONSOLIDATE later |
| `review_assignment_history` | assignment attribution | **Yes** | low | reassignment attribution | KEEP / EXTEND (entity_id?) |
| `reassignment_history` | reassignment attribution | No | medium (vs review_assignment_history) | — | DEFER / reconcile |
| `staff_workload` | daily workload counters | **Yes** | medium | capacity for auto-assign | KEEP / EXTEND (entity_id?) |
| `staff_performance` / `staff_daily_performance` / `team_performance` / `dashboard_metrics` | staff/team metrics | Partial | medium | entity-scoped KPIs | KEEP / EXTEND |
| `queue_settings` | queue/auto-assign/SLA config | **Yes** | low | auto-assignment config | KEEP |
| `sla_definitions` / `sla_compliance` / `business_hours` | SLA config/records | Partial | medium | SLA/KPI engine | KEEP |
| `approval_requests` / `approval_decisions` | approval chain | No | high (vs customer_verifications) | approval layers (re-point) | DEFER / re-point |
| `customer_verifications` / `customer_review_log` | customer approval | Partial | low | customer review layer | KEEP |
| `processing_audit_trail` / `review_audit_trail` / `processing_time_log` | queue/review audit | Partial | high (audit family) | auditability | KEEP / consolidate |
| `draft_entries` | customer draft data | Partial | low | draft/reprocessing | KEEP |
| `user_feedback` | feedback/issue surface | Partial | low | issue resolution (V3-007 optional) | KEEP |
| `export_history` | export log | Partial | low | export history | KEEP |
| `internal_tasks` / `task_assignments` | staff task intent | No | high (never created) | superseded by Work Item | RETIRE the intent; do not create |

## 20. Required Final Architecture

Based on the actual findings (not the example template — evidence contradicts a full subsystem):

```
CARBONTALLY WORK MANAGEMENT (V3, hybrid)
          |
          v
   WORK ITEMS  (canonical domain over manual_review_queue)
     work_type / org_id / batch_id / status / priority / SLA / escalation
          |
    +-----+-----+-----+-----+
    |     |     |     |     |
    v     v     v     v     v
 DOC_EXTRACTION  MANUAL_ENTRY  QC  CUSTOMER_REVIEW  [FACTOR_REVIEW V3-002]
    |                |          |        |
    v                |          |        v
 document_processing_queue      |    customer_verifications
 (technical state machine)      |
          |                     |
          +----- LOGICAL QUEUES (views over work items) ----+
          |     CarbonTally queue / Entity A / Entity B ... |
          v                                                  |
    ASSIGNMENTS (assigned_to + review_assignment_history)    |
          v                                                  |
    WORKERS / SUPERVISORS (staff_profiles; entity conditional)
          v
    SLA / KPI (queue_settings, sla_*, staff_workload, dashboard_metrics)

  TECHNICAL, OUTSIDE WORK MANAGEMENT:
    report_generation_queue → report_versions / report_comments
```

Key properties: physical item stores remain; queues are logical; human operations share one Work Item domain; technical state machines stay internal; entity scope is conditional on V3-003.

## 21. Critical Architectural Question — Verdict

**Which abstraction is correct (A/B/C/D)?**

- A (multiple specialized queues) — **rejected**: this is the status quo and the source of duplication.
- B (one canonical table) — **partially viable** but cannot hold document/report technical state.
- C (canonical work-item table + logical queues) — **correct for human operations**.
- D (Work Item + Queue Management subsystem) — **unnecessary**; every subsystem part already exists as a table.

**Recommended: C-for-human-operations + internal technical state machines (the task's own "hybrid" Option D).** It minimizes duplicate tables/state machines/assignment/SLA/audit (adds none), maximizes multi-entity processing (via conditional entity scope), assignment/reassignment (existing), worker workload (staff_workload), supervisor management (admin routes), SLA/KPI (existing), QC (existing qc_* + dpq), issue escalation (existing escalation columns), auditability (existing history tables), entity isolation (conditional RLS helper), and future automation (auto-assign engine over existing config/capacity).

## 22. Deviations from the V3 Assessment

- The V3 assessment's "select one work-item surface rather than creating a fifth queue" recommendation is **confirmed with evidence**: `manual_review_queue` is the surface, and the "fifth queue" (a new `work_items` or `issues` table) is **not required** for the human-operations surface.
- The V3 assessment's conditional migration V3M-1 (entity model) is **confirmed as the only conditional DB change**; the queue tables themselves need **no migration** to start.
## 23. Evidence / References

E1 `supabase/migrations/00000000000000_init_schema.sql` (lines 680-793, 893-958, 1200-1232, 1305-1334, 1527-1552, 1686-1725, 1763-1784, 1818-1879, 2018-2078)
E2 `supabase/migrations/schema_snapshot.sql` (manual_review_queue/upload_batches legacy policies, staff_workload, queue_settings)
E3 `database/rc1/003_rc1_indexes.sql` (claim indexes), `004_rc1_rls.sql` (tenant/staff policies), `002_rc1_constraints.sql`, `database/rc2/*` (RC2 renames/constraints)
E4 `backend/routes/admin/assignments.py`, `reviews.py`, `dashboard.py`, `analytics.py`, `workload.py`, `extraction.py`
E5 `backend/routes/upload.py`, `customer_documents.py`, `documents_main.py`, `customer_dashboard.py`, `notifications.py`, `reports.py`
E6 `backend/data/reports.py`
E7 `backend/main copy.py`, `main copy 2.py`, `process_emissions.py`
E8 `admin/src/**` (ManualReviewQueue.jsx, ReviewAssignment.js, Dashboard.js, LiveQueueStats.jsx, ReviewModal, ReviewExtractionModal, ExtractionErrorReview, WorkHub.jsx, RealtimeContext.jsx)
E9 `docs/Final_Kimi/.../05_worker_architecture.md`, `09_component_inventory.md`, `03_module_breakdown.md`, `CarbonTally RC1 — Independent Database Audit.md`, `carbontally_rc2_freeze.agent.final.md`, `CarbonTally RC2 Architecture Freeze.md`
E10 `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md`, `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md`
E11 `API_ENDPOINTS.md`, `docs/architecture/RealTImeImplementation`, `docs/architecture/changelog.md`

---

*End of audit. Read-only — no code, schema, migration, RLS, Storage, API, frontend, or test changes were made. No database was written. Factor baseline untouched (DEFRA 7,029 / SEAI 20 / TOTAL 7,049).*














