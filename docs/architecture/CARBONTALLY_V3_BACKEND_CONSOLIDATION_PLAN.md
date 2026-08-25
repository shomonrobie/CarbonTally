---
Document Type: Architecture & Implementation Plan
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: PLAN (approved — implementation pending)
Created: 2026-08-15
Author: Cline
Inputs: local codebase, V3 DB schema, live OpenAPI, v2.1 engine code
---

# CarbonTally V3 — Backend Consolidation & API Readiness Plan

> Plan only. No source, schema, RLS, migration, API, frontend, config, `.env`, credential, or package changes were made during planning. Findings are labelled by source-of-truth status.

Label key used throughout:

- **EXISTS NOW** — implemented and deployed in `backend/main.py`.
- **EXISTS IN V2.1 BUT NOT DEPLOYED** — implemented in `backend/api|engines|domain|data|infra|core` but not reachable from the live `main.py`.
- **DATABASE ONLY** — present in the schema but not wired to any app layer.
- **PARTIALLY IMPLEMENTED** — partially present across layers.
- **MISSING** — absent from all layers.
- **PROPOSED** — recommended addition (not existing functionality).

## 1. Executive Summary

The CarbonTally V3 backend is currently **two divergent applications behind one frontend**:

1. **`backend/main.py` (`main:app`)** — the live monolith. A flat `routes/` tree (customer + admin + organizations) that performs database access through the synchronous Supabase **service-role REST client**, with business logic inline in route handlers and results stored as JSON blobs.
2. **`backend/main_v2.py` → `api/router.py::create_app()`** — a clean, layered v2.1 architecture (`core` / `domain` / `engines` / `data` / `infra` / `api`) with reproducible emission calculation (SHA-256 snapshots), a staged factor-matching engine, a validation engine with stable issue codes, structured report generation, customer-factors, issues, and processing-entity repositories — but it is **NOT imported by `main.py`**, so none of it is deployed.

The V3 database schema (`CarbonTally_DB_Schema_V3M2.sql`) is **ahead of both** — it already defines consultant multi-client tables, manual-extraction batch/item tables, processing entities, customer factors, factor aliases, issues, and RLS consultant policies that no deployed route exposes.

**Recommendation (OPTION C):** adopt the v2.1 layered architecture as the **canonical V3 backend**, serve it as a single FastAPI application, and migrate the legacy `routes/` capability into it incrementally. Do not merge v2.1 into `main.py`; do not keep two apps. The live `main.py` continues serving the existing frontend during a backward-compatible transition.

## 2. Current Architecture

| Layer | Live (`main.py`) | v2.1 (not deployed) |
|---|---|---|
| App factory | `backend/main.py` `app` | `backend/api/router.py` `create_app()` |
| Routing | flat `routes/`, `routes/admin/`, `routes/organizations/` | `api/*` routers under one `api.router` |
| Business logic | inline in handlers + `utils/` + `report_generator.py` + `pdf_engine.py` | `engines/*` (stateless, per-request) |
| Data access | sync `supabase` REST client (`database.py`, `auth.py`) | async `asyncpg` repositories over a service-role pool (`data/*`, `infra/supabase.py`) |
| Domain model | Pydantic request/response models only | immutable dataclasses in `domain/*` |
| Auth | `auth.py` (Supabase JWT + roles) | reuses `auth.py` (same system) |
| Storage | Supabase Storage bucket `documents` (service role) | same bucket (later phases) |
| Realtime | frontend Supabase Realtime only | not used by backend |
| Background work | none (synchronous) | none (event bus is in-process, fire-and-forget) |
| PDF/OCR | pdfplumber / pytesseract / pdf2image / reportlab (lazy, Windows-oriented) | text extraction only (`engines/extraction.py`) |
| Frontend | customer `frontend/` + staff `admin/` | (consumes either) |

## 3. main.py Analysis

**EXISTS NOW.** The live FastAPI app (`main:app`) registers these routers (verified from `main.py` and `routes/__init__.py`):

- Customer/public: `waitlist`, `upload`, `reports`, `glossary`, `users`, `notifications`, `documents_main`, `document_activity`, `drafts`, `reference`, `logs`, `emissions`, `feedback`, `drafts_enhanced`, `customer_documents`.
- Admin: `staff`, `defra`, `extraction`, `reviews`, `assignments`, `permissions`, `workload`, `beta`, `audit`, `review_history`, `logs`, `bulk`, `email_templates`, `analytics`, `settings`.
- Organizations: `management`, `members`, `assets`, `data`, `analytics`, `dashboard`, `files`, `team`, `metadata`, `exports`, `bulk`.

Characteristics:

- Business logic inline; results stored as JSON blobs (`auto_extraction_result`, `manual_extraction_result`, `metadata`).
- Synchronous Supabase service-role REST client for all reads/writes (`database.py`).
- Calculation is largely **client-side in the frontend** (`ManualEntryStandalone` uses a hardcoded DEFRA map in `App.js`) plus `utils/emissions.py` / `process_emissions.py` helpers — no authoritative, versioned engine.
- Stale route modules exist but are not imported: `routes/admin/audit_logs.py`, `routes/admin/dashboard.py`, `routes/admin/document-types.py`, `routes/customer_verifications.py`, `routes/customer_dashboard.py`, `routes/communication.py`.
- Known defects (from the prior Render audit): `staff.py` missing `Client` import; `workload.py` concatenated duplicate module. Both are documented and are Phase-1 fixes of this plan.
- Legacy monolith copies (`main copy.py`, `main copy 2.py`) exist but are not imported.

## 4. main_v2.py Analysis

**EXISTS IN V2.1 BUT NOT DEPLOYED.** `backend/main_v2.py` → `api/router.py::create_app()` assembles a single router from:

| Router module | Prefix | Purpose |
|---|---|---|
| `api/business.py` | `/api/v2` | factor-match, calculate, validate, report (engine endpoints) |
| `api/customer_factors.py` | `/api/v3/customer-factors` | customer-owned factors (draft → approve; no self-approval; no hard delete) |
| `api/issues.py` | `/api/v3/issues` | first-class issues (lifecycle + transition authority) |
| `api/admin_entities.py` | `/api/v2/admin/entities` | processing-entity CRUD |
| `api/admin_aliases.py` | `/api/v2/admin/aliases` | factor-alias CRUD |
| `api/admin_imports.py` | `/api/v2/admin/imports` | DEFRA/SEAI import batches |
| `api/admin_providers.py` | `/api/v2/admin/providers` | factor-provider registry |
| `api/admin_audit.py` | `/api/v2/admin/audit` | audit query/export |

The layered internals:

- `core/` — exceptions (`CarbonTallyError` hierarchy with HTTP mapping), `config`, `logging`, `types`.
- `domain/` — immutable models: `calculation` (snapshot, emission log, verification result), `factor`, `matching`, `workflow` (events + pipeline), `validation`, `report`, `organization`, `customer_factor`, `audit`, `document`, `benchmarking`.
- `engines/` — stateless per-request engines: `calculation` (reproducible, SHA-256 snapshots, `verify()`), `validation` (stable issue codes A1–A9), `factor_matching` (staged pipeline: alias / exact / fuzzy / keyword / natural-key / semantic), `report_generation` (structured JSON sections, no rendering), `benchmarking`, `extraction` (text → pages/tables/fields), `workflow` (state machine), `ai_extraction`, `matching_stages`.
- `data/` — asyncpg repositories: `audit`, `customer_factors`, `documents`, `emission_factors`, `emissions_logs`, `events`, `factor_aliases`, `imports`, `issues`, `organizations`, `processing_entities`, `reports`.
- `infra/` — `supabase` (service-role client singleton + asyncpg pool), `audit_logger`, `event_bus`, `search_index`, `llm_client`, `config`.
- `api/dependencies.py` — composition root; reuses `auth.py` (`get_current_user`, `require_admin`, `require_org_member`, `require_org_admin`, `require_entity_member`).

Maturity: high for the calculation/matching/validation/reporting path; no consultant / processing-company / QC / manual-extraction routes yet (only repositories/entities).

## 5. Recommended Canonical V3 Architecture

**PROPOSED.** Promote the v2.1 layer as canonical:

```text
Frontend (customer + admin + consultant + processing-company)
   ↓  one OpenAPI contract
API  (api/* — thin: auth, validation, serialisation only)
   ↓
Engines  (engines/* — stateless business logic)
   ↓
Domain  (domain/* — immutable models/contracts)
   ↓
Repositories  (data/* — asyncpg, service-role)
   ↓
Supabase (Postgres + Auth + Storage)  +  Background workers (PROPOSED)
```

Canonical location for each responsibility:

- Authentication → `auth.py` (reused everywhere); org access → `api/dependencies.py` guards (RLS in production).
- Document processing / extraction → `engines/extraction.py` + `engines/ai_extraction.py`.
- Mapping / factor matching → `engines/factor_matching.py` + `engines/matching_stages.py`.
- Calculation → `engines/calculation.py`.
- Validation → `engines/validation.py`.
- Customer verification → new `api/verification.py` (PROPOSED).
- Customer factors → `api/customer_factors.py`; Issues → `api/issues.py`.
- Reporting → `engines/report_generation.py` + `data/reports.py`.
- Consultant management → new `api/consultants.py` (PROPOSED).
- Processing-company management → `api/admin_entities.py` + new `api/manual_extraction.py` (PROPOSED).
- Review → migrate `routes/admin/reviews.py` logic to engine layer (PROPOSED); QC → new `api/qc.py` (PROPOSED).
- Notifications → migrate `routes/notifications.py`; Messaging → realtime service (PROPOSED).
- Audit → `data/audit.py` + `api/admin_audit.py`.

## 6. Route Consolidation Plan

**PROPOSED** canonical V3 surface (current → recommended). All new/changed paths are `/api/v3/*`; the legacy `/api/*` tree stays mounted during transition (see §22/§23).

| Capability | Current (source, deployed?) | Recommended canonical |
|---|---|---|
| AUTH | `/api/users/*` — routes/users.py — EXISTS NOW | `/api/v3/auth/*` (reset/profile; auth stays in Supabase) |
| ORGANIZATIONS | `/api/organizations/*` — routes/organizations/management.py — EXISTS NOW | `/api/v3/organizations` |
| MEMBERS | `/api/organizations/members/*` — members.py — EXISTS NOW | `/api/v3/organizations/{id}/members` |
| DOCUMENTS | `/api/documents/*` — documents_main.py, document_activity.py — EXISTS NOW | `/api/v3/documents` |
| UPLOAD | `/api/upload`, `/api/test-upload`, `/api/repair-pdf` — upload.py — EXISTS NOW | `/api/v3/uploads` |
| BATCHES | `/api/batches/*`, `/api/upload-batch` — upload.py — EXISTS NOW | `/api/v3/batches` |
| EXTRACTION | `/api/admin/extraction/*` — extraction.py — EXISTS NOW | `/api/v3/extractions` |
| MAPPING / FACTOR MATCHING | `/api/v2/factor-match` — api/business.py — EXISTS IN V2.1 BUT NOT DEPLOYED | `/api/v3/factor-match` |
| CALCULATION | `/api/v2/calculate` — api/business.py — EXISTS IN V2.1 BUT NOT DEPLOYED | `/api/v3/calculate` |
| VALIDATION | `/api/v2/validate` — api/business.py — EXISTS IN V2.1 BUT NOT DEPLOYED | `/api/v3/validate` |
| CUSTOMER VERIFICATION | `/api/customer-documents/*` — customer_documents.py — EXISTS NOW (partial); stale `customer_verifications.py` | `/api/v3/verifications` |
| CUSTOMER FACTORS | `/api/v3/customer-factors` — api/customer_factors.py — EXISTS IN V2.1 BUT NOT DEPLOYED | keep `/api/v3/customer-factors` |
| ISSUES | `/api/v3/issues` — api/issues.py — EXISTS IN V2.1 BUT NOT DEPLOYED | keep `/api/v3/issues` |
| REPORTING / EXPORT | `/api/reports/*` — reports.py — EXISTS NOW; `report_generation_queue` repo — EXISTS IN V2.1 BUT NOT DEPLOYED | `/api/v3/reports` (queued lifecycle) |
| SUPPLIERS | none in main.py — suppliers table — DATABASE ONLY | `/api/v3/suppliers` (PROPOSED) |
| FACILITIES / ASSETS | `/api/organizations/{org_id}/facilities|assets` — assets.py — EXISTS NOW | `/api/v3/organizations/{id}/facilities`, `/api/v3/assets` |
| CONSULTANTS / CLIENTS / TASKS | none — consultant_* tables — DATABASE ONLY | `/api/v3/consultants`, `/api/v3/consultant/clients`, `/api/v3/consultant/tasks` (PROPOSED) |
| PROCESSING ENTITIES | `/api/v2/admin/entities` — api/admin_entities.py — EXISTS IN V2.1 BUT NOT DEPLOYED | `/api/v3/processing-entities` |
| MANUAL EXTRACTION | none — manual_extraction_batches/items — DATABASE ONLY | `/api/v3/manual-extraction/batches`, `/items` (PROPOSED) |
| REVIEW | `/api/admin/reviews/*` — reviews.py — EXISTS NOW | `/api/v3/admin/reviews` |
| QC | none — MISSING | `/api/v3/admin/qc` (PROPOSED) |
| STAFF / ASSIGNMENTS / SLA / PERFORMANCE | `/api/admin/staff|assignments|workload|analytics/*` — EXISTS NOW | `/api/v3/admin/*` |
| MESSAGING / NOTIFICATIONS | chat widget + `/api/notifications/*` — notifications.py — EXISTS NOW | `/api/v3/notifications` + realtime service |
| ADMIN | `/api/admin/*` — EXISTS NOW | `/api/v3/admin/*` |
| SYSTEM | `/`, `/health`, `/api/v2/health` — EXISTS NOW | `/health` + `/api/v3/system/*` |

Duplicates observed: stale `customer_verifications.py` vs `customer_documents.py` verification endpoints; `reviews.py` vs `review_history.py` share `/api/admin/reviews`; v2.1 `admin_audit` vs legacy `routes/admin/audit.py` and stale `audit_logs.py`.

## 7. Emission Calculation Architecture

- Where calculations occur today: **frontend hardcoded DEFRA map** (`App.js`/`ManualEntryStandalone`) — must be removed; `utils/emissions.py` + `process_emissions.py` (main.py, partial); `engines/calculation.py` (v2.1, authoritative, not deployed).
- **Authoritative engine (PROPOSED):** `engines/calculation.py` — consumes the matched `EmissionFactor` via `CalculationRequest`, applies unit-match validation and `RESULT_PRECISION` quantisation, builds a `CalculationSnapshot` with a SHA-256 content hash, persists through `EmissionsLogsRepository.save`, publishes workflow events + audit, and exposes `verify()` for audit-time reproducibility.
- Results stored in: `emissions_logs` (`snapshot_id`, `metadata`).
- Provenance: snapshot hash + `factor_kind` / `customer_factor_id` / provider / country / unit / algorithm version are preserved, so historical calculations remain reproducible.
- **Decision:** one canonical engine; the frontend must never be the calculation authority; the API contract returns `CalculationResult` + `snapshot_id`; legacy `utils/emissions.py` helpers are retired once routes migrate.

## 8. Factor Matching Architecture

- v2.1 `engines/factor_matching.py` runs a staged pipeline (alias → exact → fuzzy/keyword/natural-key → semantic) over `infra/search_index.FactorSearchIndex` and returns `MatchResult` with confidence, method and provider. Customer factors (`status='active'`) are matched ahead of CarbonTally-managed factors (D-cf-5). Data: `emission_factors`, `factor_aliases`, `customer_factors` (schema + repositories).
- **Decision (PROPOSED):** keep the v2.1 engine as canonical; the `/api/v3/factor-match` contract returns `MatchResult` (factor id, label, confidence, method, provider, country, unit, source, scope) with provenance; customer-factor behaviour preserved; legacy inline matching removed.

## 9. Validation Architecture

- v2.1 `engines/validation.py`: capabilities A1–A9, stable issue codes (`VAL_*`), severities, strict/non-strict blocking, `ValidationReport` (errors + warnings), audit entry per run.
- Legacy `utils/emissions.py` `extract_issues_from_result` / `has_low_confidence` are informal.
- **Decision (PROPOSED):** v2.1 engine is canonical; `/api/v3/validate` returns `ValidationReport`; "review-required" is an explicit validation state surfaced to the verification workflow.

## 10. Customer Verification Architecture

**PARTIALLY IMPLEMENTED.** `routes/customer_documents.py` has approve/reject endpoints (verified_by/verified_at, review_request, stats); stale `customer_verifications.py` is unwired. Missing: correction flow, the full extracted→mapped→factor→calculation→result chain as a typed contract, issues/comments, and customer-visible review history.

Target chain (PROPOSED): `SOURCE DOCUMENT → EXTRACTED DATA → MAPPED DATA → EMISSION FACTOR → CALCULATION → RESULT → CUSTOMER APPROVE / REJECT / CORRECT`, exposed as `/api/v3/verifications/*` with a typed result chain (not a JSON blob).

## 11. Split-Screen Data Contract

Current state: no page/coordinate model — extraction results are JSON blobs (EXISTS NOW); `manual_extraction_items.page_count` exists (DATABASE ONLY); bounding boxes / coordinates / field spans are **MISSING**.

- **PHASE 1 (source document + structured info side-by-side):** requires only `document_id`, page count, and a structured extraction result + a signed document URL. No coordinate model needed. Backend minimum (PROPOSED): `GET /api/v3/verifications/{id}/view` returning `{ document_url, pages, result }`.
- **PHASE 2 (field → source highlighting):** requires coordinate spans — page number, x/y, width/height, source text, field_id, extraction_id, version. **MISSING — schema change required** (see §20).
- Recommended contract: `DocumentView { pages, signed_url }` + `ExtractionView { fields[{ id, key, value, confidence, mapped_factor_id, calculated_kg_co2e }], spans?[{ page, x, y, w, h, text, field_id }] }`.
- Phase 2 must NOT block Phase 1.

## 12. Consultant Multi-Client Architecture

**DATABASE ONLY.** Schema: `consultant_profiles`, `consultant_firm_members`, `consultant_clients` (consultant↔organization), `consultant_tasks`, `consultant_billing`; RLS `is_org_consultant(org)` with tenant SELECT policies unioning `is_org_member OR is_org_consultant` across org tables. **MISSING:** API routes, client-context switching, frontend workspace. Note: the live backend uses the service role, so the RLS consultant policies are not currently enforced anywhere.

Target (PROPOSED): `CONSULTANT FIRM → TEAM → MULTIPLE CLIENT ORGANIZATIONS → CLIENT-SPECIFIC ACCESS → DOCUMENTS → PROCESSING → EMISSIONS → REPORTS`, backed by new `/api/v3/consultants/*` routes and a client-context resolver in `api/dependencies.py`.

## 13. External Processing Company Architecture

**DATABASE ONLY / PARTIALLY IMPLEMENTED.** Schema: `processing_entities` (active/remediation/suspended/terminated), `manual_extraction_batches`, `manual_extraction_items` (currency, cost, pages, quality_score, calculated_kg_co2e); dormant `processing_queue` / `processing_assignments` / `processing_steps`. v2.1 `api/admin_entities.py` exposes processing-entity CRUD (EXISTS IN V2.1 BUT NOT DEPLOYED). **MISSING:** operator/QC batch+item assignment, billing, frontend.

Target (PROPOSED): `PROCESSING COMPANY → MANAGER → OPERATORS → QC → ASSIGNED BATCHES → ASSIGNED ITEMS → COMPLETION → QC → RETURN TO CARBONTALLY`, reusing `processing_entities` for the company and `manual_extraction_batches/items` for work, via `/api/v3/manual-extraction/*` + `/api/v3/processing-entities/*`.

## 14. Manual Data Entry Workflow

**PARTIALLY IMPLEMENTED.** `manual_review_queue` + `routes/admin/reviews.py` / `assignments.py` / `workload.py` (queue, assign, complete, SLA) and admin frontend pages (Reviews, ManualReviewQueue, StaffReviewQueue, WorkHub). **MISSING:** document viewer, split-screen form, next-item flow, correction path, high-volume operator UX.

Required for a high-volume operator workflow (PROPOSED): extraction queue + assignment, `GET /next-item`, `POST /save` and `POST /submit` writing structured results, and Phase-2 coordinate spans.

## 15. QC Workflow

**MISSING.** No QC queue, checklist, error model or QC role. Only `accuracy_rate` (staff_profiles) and `quality_score` (manual_extraction_items) fields exist (DATABASE ONLY).

Required (PROPOSED): a QC stage with checklist + pass/fail + correction + rejection + audit history + quality scoring. Likely needs a new `qc_reviews` table or a QC status on `manual_review_queue` — **schema change required** (see §20).

## 16. Async / Background Processing

**MISSING (workers).** All processing is synchronous today. Should be asynchronous: PDF/OCR, large CSV/Excel, batch uploads, AI extraction, report generation, bulk factor matching/calculation. Existing queue tables: `report_generation_queue` (in use), `manual_review_queue`, dormant `processing_queue/assignments/steps`.

Required (PROPOSED): a worker consuming `report_generation_queue` + a new generic `processing_jobs` table (or Supabase-queue); status + progress via Realtime; retry/backoff and failure states.

## 17. Authentication / Authorization Architecture

- **Development model (EXISTS NOW — unchanged):** Supabase Auth (email/password, Google OAuth, magic link); backend uses the service-role client for all data access; local `.env` service-role credentials are intentionally used for development and are not pushed to Git.
- **Production model (PROPOSED — later phase):** keep Supabase Auth; enforce RLS for direct client access; backend keeps service role but with user-scoped query discipline; add MFA/TOTP; rotate credentials; never expose service-role secrets to the frontend.
- Guards today (`auth.py`): `require_admin`, `require_staff`, `require_role`, `require_permission`, `require_any/all_permissions`, `require_org_member`, `require_org_admin`, `require_auth`, `require_entity_member`. **MISSING:** consultant role guards, processing-company role guards, QC role.

## 18. Reporting Architecture

- `report_generation_queue` is used by v2.1 `data/reports.py` (lifecycle pending → … → completed; `page_count` stored in `generated_content` JSONB) — EXISTS IN V2.1 BUT NOT DEPLOYED. Legacy `routes/reports.py` + `report_generator.py` render PDF inline with FPDF — EXISTS NOW. v2.1 `engines/report_generation.py` produces **structured JSON only** (no rendering).
- Recommended lifecycle (PROPOSED): `QUEUED → GENERATING → READY | FAILED`; structured content persisted; PDF rendering as a separate step. Canonical: v2.1 engine + repository; retire inline FPDF generation in favour of queued generation.

## 19. Supplier / Facility / Asset Architecture

- **Suppliers:** DATABASE ONLY (`suppliers` table; RC1 constraints). **MISSING** API + frontend. PROPOSED: `/api/v3/suppliers` with customer + consultant access.
- **Facilities / Assets:** EXISTS NOW (`routes/organizations/assets.py`, org-scoped; frontend `AssetManager`). Keep; align consultant access via RLS in production.
- **Product categories:** reference tables exist (DATABASE ONLY); add read-only reference endpoints only if the UI needs them.






