---
Document Type: Architecture Conformity Gate (Plan / Audit only — no code changed)
Project: CarbonTally
Architecture: CarbonTally V3
Version: 1.0
Status: CONFORMITY GATE REPORT — read-only audit
Created: 2026-08-17
Author: Cline
Scope: V3 Phases 3–8 completed; Phase 9 NOT started; no code/tests/DB/RLS/.env modified
---

# CarbonTally V3 — Architecture Conformity Gate (pre-Phase-9)

> Plan/audit only. No application code, tests, database, RLS, `.env`, migrations or
> files were modified during this gate. Every conclusion below cites inspected code
> (file + line) or inspected configuration. Where a prior phase report is cited it is
> corroborated by code inspection in this session.

---

## 1. Executive Summary

**Verdict: READY WITH CONDITIONS** (see §21). The V3 layered architecture
(`api → engines → domain → data → infra → core`) genuinely exists in the tree and
is the authoritative engine layer for calculation, factor matching, validation,
emissions, reporting, ops/QC, consultants and org-scoped surfaces. The unit-level
state is green (Phase 8: 54/54; full unit suite ≈900, RC=0). **However, the
codebase is not yet architecturally consolidated.** Two application entry points
compete (`main.py` = legacy monolith + V3 mounted alongside; `main_v2.py` = a
second, standalone V3 app). The full legacy surface (`backend/routes/**`, ~48
modules, 400+ endpoints; legacy `frontend/` monolith with client-side calculation;
old `admin/` CRA app) remains deployed and consumed. A genuine end-to-end
pipeline cannot yet be proven against a live database because integration/E2E
tests have not run, and two integrity gaps connect QC/approval state to persisted
emissions logs.

The five largest conformity findings:

1. **Two apps, not one.** `main.py` mounts the legacy routers **and** the V3
   router (§3); `main_v2.py` is an independent uvicorn entrypoint serving
   `create_app()` (§4). This violates the governing "ONE V3 app" decision (D1/D2).
2. **Legacy duplicates still authoritative for the deployed UI.** Frontend
   `App.js` still holds a hardcoded `DEFRA_FACTORS` map and multiplies
   `volume * factor` client-side (`App.js:56`, `App.js:952-954`); the legacy
   FPDF reporting path (`routes/reports.py` + `report_generator.py`) is still
   mounted; legacy `utils/emissions.py` still exposes its own calculation.
3. **Pipeline integrity gap.** The V3 ops pipeline persists `emissions_logs` at
   the *calculate* step, but QC and customer-review rejection only update the
   `manual_extraction_items` row — they do **not** retract or flag the persisted
   log, and `ReportGenerationEngine` reads all logs for the org/period with no
   approval filter (§10, §12).
4. **One V3-frontend → legacy dependency.** `frontend/src/v3/api.js`
   `resolveV3Organization()` calls the legacy `/api/organizations/members/user/{id}`
   endpoint; used by `AdminPage`, `ReportDetailPage`, `ReportsPage` (§7).
5. **Service-role bypass of RLS remains the production follow-on.** RLS
   migrations exist (`supabase/migrations/…_rc2_rls.sql`,
   `…_v3m6_entity_rls.sql`) but the live DB was not verified with integration
   tests; isolation is enforced in-code, not in-DB (§9, §18).

**Phase 9 must not start** until the P0 conditions in §20–§21 are met.


---

## 2. Governing Documents

| Document | Status | Role |
|---|---|---|
| `docs/architecture/CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md` | Approved plan (D1–D9 pending) | Authoritative V3 target: ONE app, layered `core/domain/engines/data/infra/api`, `auth.py` reused, RLS in production, legacy transitional mount then removal |
| `docs/architecture/CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md` | Approved plan | Legacy inventory with RETAIN/REIMPLEMENT/ARCHIVE/REMOVE recommendations and label key (V3/LEGACY/MIGRATE/REFACTOR/ARCHIVE/REMOVE/PROPOSED) |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_8_REPORT.md` | Completed | Phase 8 state, gaps, and unit-level readiness |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_7_REPORT.md` | Completed | Consultant/multi-client state |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_6_REPORT.md` | Completed | Customer administration state |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_5_REPORT.md` | Completed | Reporting (40/40 runtime tests) |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_4_REPORT.md` | Completed | Emissions intelligence state |
| `docs/audit/cline/CARBONTALLY_V3_RESUMPTION_AFTER_POWER_LOSS.md` | Completed | Environment/toolchain recovery notes |

The implementation source of truth used for this gate is the **actual codebase**
(verified by inspection below), not the phase reports.

---

## 3. Current V3 Architecture (verified)

The intended layer structure exists and is real:

| Layer | Location | Verified evidence |
|---|---|---|
| Entry | `backend/main.py` (legacy + V3 dual mount); `backend/main_v2.py` (standalone V3) | `main.py:22-34,260-262` imports `api.router`; `main_v2.py:16` `app = create_app()` |
| API | `backend/api/*` (23 routers) | `api/router.py:27-51,164-186` assembles the V3 router |
| Engines | `backend/engines/*` (11 modules) | `calculation.py`, `factor_matching.py`, `matching_stages.py`, `validation.py`, `processing_workflow.py`, `report_generation.py`, `extraction.py`, `ai_extraction.py`, `benchmarking.py`, `workflow.py` |
| Domain | `backend/domain/*` (17 modules) | `calculation.py`, `matching.py`, `factor.py`, `validation.py`, `report.py`, `workflow.py`, `operations.py`, `partners.py`, `entity.py`, `staff.py` … |
| Data | `backend/data/*` (25 repositories) | `emission_factors.py`, `emissions_logs.py`, `reports.py`, `manual_extraction.py`, `review_queue.py`, `consultants.py`, `suppliers.py`, `processing_entities.py`, `staff.py`, `roles.py` … |
| Infra | `backend/infra/*` (7 modules) | `supabase.py` (service-role client + asyncpg pool), `event_bus.py`, `audit_logger.py`, `llm_client.py`, `search_index.py`, `config.py` |
| Core | `backend/core/*` (4 modules) | `exceptions.py` (CarbonTallyError hierarchy), `logging.py`, `types.py`, `config.py` |
| Auth | `backend/auth.py` (shared) | `auth.py:99,187-593` `get_current_user`, `require_admin`, `require_org_member`, `require_org_admin`, `require_entity_member`, `require_role`/`require_permission` factories |
| Composition | `backend/api/dependencies.py` | Per-request engine/repository wiring (verified lines 26–386) |

**Not conforming to the "ONE V3 app" requirement** (`api/router.py:194` builds a
second app through `create_app()`; `main_v2.py` serves it independently). The
governing plan (D1/D2) explicitly rejects a second app.


---

## 4. Backend Conformity

### 4.1 Duplicate application entry points

| Entry point | Status | Evidence |
|---|---|---|
| `backend/main.py` (`app`) | Deployed monolith; mounts legacy `routes/**` + V3 `api.router` | `main.py:211-262` |
| `backend/main_v2.py` (`app`) | Second, standalone V3 app (uvicorn `--port 8001`) | `main_v2.py:5,16`; referenced only in its own docstring and `api/__init__.py:20` |
| `backend/main copy.py` | Dead copy — never imported | tree listing; no importers |
| `backend/main copy 2.py` | Dead copy — never imported | tree listing; no importers |

Classification: **DUPLICATE / TRANSITIONAL** (entry points), **LEGACY** (copies).

### 4.2 Duplicate engines / capability implementations

| Capability | V3 canonical | Legacy / duplicate copies | Classification |
|---|---|---|---|
| Calculation | `engines/calculation.py` (SHA-256 snapshot + `verify()`, `CalculationSink` → `data/emissions_logs.py`) | `utils/emissions.py:144 calculate_emissions_with_defra`; `process_emissions.py`; frontend `App.js:952-954`; `report_generator.py` (FPDF inline) | **DUPLICATE** (legacy copies) |
| Factor matching | `engines/factor_matching.py` + `engines/matching_stages.py` (alias/exact/fuzzy/keyword/natural-key/semantic) over `infra/search_index.py` | `utils/emissions.py` DEFRA lookup; frontend `App.js:56 DEFRA_FACTORS`; `admin/` `DefraFactors.js` direct Supabase table access | **DUPLICATE** |
| Validation | `engines/validation.py` (stable VAL codes) + `engines/processing_workflow.py validate_processing_item` | `utils/emissions.py` informal checks | **DUPLICATE** |
| Processing workflow | `engines/processing_workflow.py` + `api/v3_processing_workflow.py` + `api/v3_operations.py` (start/extract/map/validate/calculate/qc/review) | `routes/admin/reviews.py`, `routes/admin/assignments.py`, `routes/admin/workload.py` (parallel legacy queue/assignment/SLA) | **DUPLICATE** (parallel pipeline) |
| Emissions | `api/v3_emissions.py` + `data/emissions_logs.py` + `calculation_snapshots` | `routes/emissions.py`, `routes/organizations/data.py` | **DUPLICATE** |
| Reporting | `engines/report_generation.py` + `api/v3_reports.py` + `data/reports.py` (`report_generation_queue`) | `routes/reports.py` + `report_generator.py` (FPDF, inline) | **DUPLICATE** |
| Authentication | `auth.py` (single) — V3 reuses via `api/dependencies.py:29-36` | none (no second JWT path) | **V3 CANONICAL** |
| Organization authorization | `auth.py` guards + `api/dependencies.py ensure_org_access` + `operations_auth.py` + `consultant_auth.py` | legacy inline checks in `routes/organizations/*` | **TRANSITIONAL** (legacy inline still live) |

### 4.3 Duplicate DB access

- Legacy sync REST: `database.py get_supabase_client()` — used by `main.py`, all
  `routes/**`, `auth.py`, `utils/*`, `services/email_service.py` (grep-verified,
  60+ callers).
- V3 asyncpg: `infra/supabase.py get_service_pool()` — used only by `data/*`
  repositories and `api/dependencies.py` (verified: **no** `api/`, `engines/`,
  `domain/`, `infra/` module calls `get_supabase_client(` directly — the grep for
  that pattern in those directories returned zero matches).

Classification: **DUPLICATE** (two data-access mechanisms by design), with the
V3 repository layer **V3 CANONICAL** for all V3 surfaces.

### 4.4 Legacy services still imported

- `backend/services/email_service.py` + `backend/services/email.js` — legacy
  email path; V3 notifications exist separately (`api/v3_notifications.py` +
  `data/notifications.py`).
- `backend/utils/emissions.py`, `utils/organization_utils.py`,
  `utils/staff_workload.py`, `utils/audit_logger.py`,
  `utils/document_classifier.py` remain imported by legacy routes (grep-verified).
- `backend/report_generator.py`, `backend/pdf_engine.py` — legacy reporting/OCR
  (`report_generator.py` imports `fpdf`; `routes/reports.py` mounts it).

Classification: **LEGACY** (transitional) / **DUPLICATE** (`utils/emissions.py`).

### 4.5 Legacy routes still mounted

`main.py:211-255` mounts **all** `routes/**` modules (public + admin +
organizations). Confirmed prefixes (grep): `/api/waitlist`, `/api/upload`,
`/api/reports`, `/api/glossary`, `/api/users`, `/api/notifications`,
`/api/documents`, `/api/drafts`, `/api/reference`, `/api/logs`, `/api/emissions`,
`/api/feedback`, `/api/customer-documents`, `/api/customer/verifications`,
`/api/communication`, `/api/customer/dashboard`, `/api/admin/*` (analytics,
assignments, audit, audit-logs, beta, bulk, dashboard, defra, document-types,
email/templates, extraction, logs, permissions, reviews, review_history, settings,
staff, workload), `/api/organizations/*` (management, members, assets, data,
analytics, dashboard, files, team, metadata, exports, bulk).

Duplicate legacy route prefixes (overlapping implementations): `/api/documents`
(`documents_main.py` + `document_activity.py`), `/api/drafts` (`drafts.py` +
`drafts_enhanced.py`), `/api/admin/reviews` (`reviews.py` + `review_history.py`),
`/api/admin/audit` + `/api/admin/audit-logs` (`audit_logs.py` stale).

Classification: **LEGACY** (mounted, still consumed), **DUPLICATE** (overlaps).


---

## 5. Backend Consolidation (one authoritative implementation — traced)

For each capability the actual chain (Frontend → API route → service/engine →
repository → database) and any bypasses:

| Capability | Chain (verified) | Bypasses |
|---|---|---|
| **Calculation** | V3 frontend `v3/api.js` → `POST /api/v3/emissions/calculate` (`api/v3_emissions.py`) or `/api/v3/ops/items/{id}/calculate` (`api/v3_operations.py:616`) → `engines/calculation.py` → `data/emissions_logs.py` (snapshot + log, SHA-256) | Legacy frontend `App.js:952-954` computes `volume*factor` client-side; `utils/emissions.py:144`; legacy `routes/reports.py` + `report_generator.py` inline FPDF |
| **Factor matching** | `POST /api/v2/factor-match` (`api/business.py`) or auto-match in `POST /api/v3/emissions/calculate` (no explicit factor) → `engines/factor_matching.py` (staged pipeline) over `infra/search_index.py` → `data/emission_factors.py` + `data/customer_factors.py` (approved-first, D-cf-5) | `App.js:56 DEFRA_FACTORS` map; `admin/` direct Supabase queries to `defra_conversion_factors` |
| **Validation** | `engines/validation.py` (VAL codes) + `engines/processing_workflow.py validate_processing_item` used by `/api/v3/processing/*` and `/api/v3/ops/items/{id}/validate` (blocking findings open `issues`) | `utils/emissions.py` informal checks; legacy `routes/admin/extraction.py` bespoke checks |
| **Processing workflow** | `api/v3_processing_workflow.py` + `api/v3_operations.py` → `engines/processing_workflow.py` → `data/manual_extraction.py` (`manual_extraction_batches`/`manual_extraction_items`) + `data/review_queue.py` (`manual_review_queue`) + `data/issues.py` | Legacy `routes/admin/reviews.py`/`assignments.py`/`workload.py` run a **second, parallel** queue on the same tables |
| **Emissions** | `api/v3_emissions.py` → engines → `data/emissions_logs.py` + `data/report_versions.py`; history reads `calculation_snapshots` (append-only) | Legacy `routes/emissions.py`, `routes/organizations/data.py` write legacy tables independently |
| **Reporting** | `api/v3_reports.py` → `engines/report_generation.py` → `data/reports.py` (`report_generation_queue`) + `report_versions`; content reads `emissions_logs` via `find_by_org` | Legacy `routes/reports.py` + `report_generator.py` (FPDF) — still mounted and consumed by the legacy dashboard |
| **Authentication** | `auth.py` `get_current_user` (Supabase JWT + service-role REST) — single path reused by `api/dependencies.py`, `api/operations_auth.py`, `api/consultant_auth.py` | None (one JWT path). Note: `auth.py` itself uses the legacy sync REST client (`auth.py:77-97`) |
| **Organization authorization** | `auth.py` `require_org_member/require_org_admin` + `api/dependencies.py ensure_org_access` + repo-level SQL org scoping + `operations_auth.py require_staff/require_internal_staff/require_entity_scope` + `consultant_auth.py require_consultant/ensure_consultant_org_access` | Legacy `routes/organizations/*` inline checks (legacy surface only) |

**Consolidation verdict:** V3 canonical chains are singular and authoritative for
their surfaces; legacy copies remain operational and are still the deployed
customer/admin UI's source of truth. This is the documented transitional state,
**not** consolidation completion.


---

## 6. API Conformity

### 6.1 Canonical V3 routers (all mounted in `main.py` via `api.router`)

| Router module | Prefix | Verdict |
|---|---|---|
| `api/business.py` | `/api/v2` (factor-match, calculate, validate, generate-report, health) | V3 CANONICAL |
| `api/admin_aliases.py` | `/api/v2/admin/aliases` | V3 CANONICAL |
| `api/admin_audit.py` | `/api/v2/admin/audit` | V3 CANONICAL |
| `api/admin_imports.py` | `/api/v2/admin/imports` | V3 CANONICAL |
| `api/admin_providers.py` | `/api/v2/admin/providers` | V3 CANONICAL |
| `api/admin_entities.py` | `/api/v2/admin/entities` | V3 CANONICAL |
| `api/customer_factors.py` | `/api/v3/customer-factors` | V3 CANONICAL |
| `api/issues.py` | `/api/v3/issues` | V3 CANONICAL |
| `api/v3_organizations.py` | `/api/v3/organizations` | V3 CANONICAL |
| `api/v3_documents.py` | `/api/v3` (documents) | V3 CANONICAL |
| `api/v3_review.py` | `/api/v3/admin` (review history) | V3 CANONICAL |
| `api/v3_verifications.py` | `/api/v3/verifications` | V3 CANONICAL |
| `api/v3_notifications.py` | `/api/v3/notifications` | V3 CANONICAL |
| `api/v3_exports.py` | `/api/v3/exports` | V3 CANONICAL |
| `api/v3_consultants.py` | `/api/v3/consultants` | V3 CANONICAL |
| `api/v3_processing.py` | `/api/v3/processing-entities` | V3 CANONICAL |
| `api/v3_processing_workflow.py` | `/api/v3/processing` | V3 CANONICAL |
| `api/v3_emissions.py` | `/api/v3/emissions` | V3 CANONICAL |
| `api/v3_reports.py` | `/api/v3/reports` | V3 CANONICAL |
| `api/v3_manual_extraction.py` | `/api/v3/manual-extraction` | V3 CANONICAL |
| `api/v3_qc.py` | `/api/v3/qc` | V3 CANONICAL |
| `api/v3_suppliers.py` | `/api/v3/suppliers` | V3 CANONICAL |
| `api/v3_operations.py` | `/api/v3/ops` | V3 CANONICAL |

### 6.2 Legacy routes still mounted and consumed

All legacy prefixes in §4.5 remain mounted. **Actively consumed** (verified by
frontend/admin source):
- Legacy customer UI (`frontend/src/**`): `/api/waitlist` (`services/emailService.js`),
  `/api/notifications` (`hooks/useNotifications.js`, `services/NotificationService.js`),
  `/api/drafts` (`hooks/useManualEntry.js:329`), `/api/documents`,
  `/api/batches`, `/api/organizations/*`, `/api/reports`, `/api/reference`,
  `/api/logs` (`admin/src/components/admin/LogViewer.jsx`), `/api/admin/*`.
- Old admin app (`admin/src/**`): `/api/admin/queue/stats`, `/api/admin/reviews/*`,
  `/api/admin/staff`, `/api/batches/{id}/status`, `/api/drafts/save`,
  `/api/organizations/assets`, `/api/reference/fuel-types`, `/api/logs/*`.
- **V3 frontend → legacy**: `frontend/src/v3/api.js:45-51` calls
  `/api/organizations/members/user/{id}` (`resolveV3Organization`), used by
  `AdminPage.jsx`, `ReportsPage.jsx`, `ReportDetailPage.jsx`. This is the **only**
  V3-frontend legacy call found.

### 6.3 Duplicate routes

- `/api/documents` (documents_main + document_activity) — overlapping prefixes.
- `/api/drafts` (drafts + drafts_enhanced).
- `/api/admin/reviews` (reviews + review_history).
- `/api/admin/audit` vs `/api/admin/audit-logs` (stale audit_logs).
- `/health` (legacy `main.py:288`) vs `/api/v2/health` (V3 `api/router.py:64`).
- Legacy `routes/emissions.py` prefix `/api` — bare prefix collides with the
  `/api`-prefixed surface of `routes/upload.py`.

**API verdict:** the canonical surface is one coherent `/api/v3/*` (+ `/api/v2/*`)
contract; the legacy `/api/*`, `/api/admin/*` and `/api/organizations/*` trees
remain mounted and consumed — **transitional by design**, not yet removed.


---

## 7. Frontend Conformity

### 7.1 V3 frontend (canonical)

`frontend/src/v3/` — `api.js` (thin fetch client), `admin/` (AdminPage +
Profile/Members/Security/Suppliers/Facilities tabs), `consultant/`
(ConsultantPage), `ops/` (OperationsPage, OpsDashboard, OperatorQueue,
ReviewQueue, QcQueue, StaffRoster, WorkItemWorkspace), `reports/` (ReportsPage,
ReportDetailPage). Registered routes in `App.js:1961-1995`: `/reports`,
`/reports/:id`, `/organization`, `/consultant`, `/ops`. All V3 screens consume
`/api/v3/*` **except** `resolveV3Organization` (§6.2).

### 7.2 Legacy frontend (still deployed as the primary customer UI)

`frontend/src/**` root (App.js monolith ≈2,000 lines, LandingPage, Dashboard,
UploadManager, ManualEntry*, OrganizationMetadata, AssetManager, PDFIngestionPortal,
hooks/, services/, supabaseClient.js, context/). Conformity violations:

- **Client-side calculation**: `App.js:56` hardcoded `DEFRA_FACTORS` map;
  `App.js:952-954` computes `volume * factor`. **LEGACY — violates the rule that
  the frontend must never be authoritative for calculation.**
- **Hardcoded Supabase URL/anon key** in `supabaseClient.js` (legacy pattern).
- **Duplicate API clients**: `v3/api.js` + legacy `services/*` and `hooks/*`
  each with their own `API_URL` fetch wrappers.
- **Legacy auth flows**: `Login.js`, `BetaLogin`, `BetaSignup`, `MagicLink`,
  `AuthCallback`, `CompanyNamePrompt` — Supabase direct, not V3 API.
- **Legacy admin UI**: old `admin/` CRA app (carbontally-admin) — ManualReviewQueue,
  StaffReviewQueue, WorkHub, Users, Organizations, DefraFactors, Analytics,
  LogViewer, Assignments, direct Supabase table access (`DefraFactors.js` reads
  `defra_conversion_factors` directly). This is a **separate app** in the repo
  root, still the operational staff UI.

### 7.3 Duplicate screens / routes

- Reports: V3 `v3/reports/ReportsPage` vs legacy dashboard report views.
- Ops: V3 `v3/ops/*` vs old admin `ManualReviewQueue`/`StaffReviewQueue`/`WorkHub`.
- Admin: V3 `v3/admin/AdminPage` vs old admin app + legacy `TeamManagement.js`.
- `App copy.js`, `LandingPage copy.jsx`, `CarbonTallyDemo copy.jsx`,
  `FileUploadHero copy.jsx`, `App copy.css` — dead copies (REMOVE candidates).

### 7.4 Stale factor maps

- `App.js:56 DEFRA_FACTORS` — stale/hardcoded, duplicates the DB factor set.
- Old admin `DefraFactors.js` — reads the DB directly (no V3 factor API).

**Frontend verdict:** the V3 frontend is structurally sound and consumes V3 APIs
(one legacy dependency); the legacy frontend + old admin app remain the deployed
customer/ops UI and violate the no-frontend-calculation rule. Replacement, not
removal, is required before they are retired.

---

## 8. Database Conformity

### 8.1 V3 repository mapping (all verified against real tables)

`data/emission_factors.py` → `emission_factors` + `import_batches.provider_key`;
`data/emissions_logs.py` → `emissions_logs` + `calculation_snapshots`;
`data/reports.py` → `report_generation_queue` (+ `report_versions`);
`data/manual_extraction.py` → `manual_extraction_batches` /
`manual_extraction_items`; `data/review_queue.py` → `manual_review_queue`;
`data/issues.py` → `issues`; `data/processing_entities.py` → `processing_entities`;
`data/consultants.py` → `consultant_profiles` / `consultant_firms` /
`consultant_clients` / `consultant_tasks`; `data/suppliers.py` → `suppliers`;
`data/staff.py` → `staff_profiles`; `data/roles.py` → `roles`; `data/upload_batches.py`
→ `upload_batches`; `data/customer_factors.py` → `customer_factors`;
`data/factor_aliases.py` → `factor_aliases`. **No repository writes to a table
that does not exist** (schema files: `supabase/migrations/*`, V3M1–V3M6).

### 8.2 Legacy tables still used by legacy routes (sync REST)

`defra_conversion_factors`, `glossary`, `upload_batches`, `documents`,
`organization_members`, `staff_profiles`, `notifications`, `drafts`,
`organization_metadata`, `organizations`, `emissions`/legacy emissions tables,
`waitlist`, `feedback`, `logs`, `email_templates`, `manual_review_queue` (legacy
admin reviews), `processing_queue/assignments/steps` (dormant), etc.

### 8.3 Schema-use issues (verified in code)

| Issue | Evidence | Classification |
|---|---|---|
| `facility_id` round-trips through `metadata` JSONB | `data/emissions_logs.py:26-30,38,53-55` — no `facility_id` column | **TRANSITIONAL** (documented; column proposed) |
| `page_count` stored inside `generated_content` JSONB | `data/reports.py:4-6,36` — table has no column | **TRANSITIONAL** |
| `_SYSTEM_UUID` placeholder for NOT NULL actor columns | `data/emissions_logs.py:22-24` | **PARTIAL** (documented review point) |
| `upload_batches.entity_id` never written by V3 code | Phase 8 report §23; ops flows use `manual_review_queue.entity_id` only | **PARTIAL** (follow-on) |
| Manual-extraction batches/items have **no entity column** | `data/manual_extraction.py` columns; schema | **GAP** (blocks entity-scoped pipeline; design decision) |
| Item→snapshot link missing | `api/v3_operations.py:698-700` — `engine.calculate` persists snapshot/log, item stores only `calculated_emissions_kg_co2e` | **GAP** (provenance) |
| Legacy JSON-blob results | `manual_review_queue.auto_extraction_result/manual_extraction_result` JSONB | **LEGACY** (by design) |
| Duplicate legacy `emissions`/reporting tables vs `emissions_logs` | legacy `routes/emissions.py`, `routes/organizations/data.py` | **LEGACY** |

### 8.4 Missing relationships (no schema change proposed unless approved)

- `emissions_logs → manual_extraction_items` (no item_id on the log) — blocks
  item→report traceability.
- `manual_extraction_batches/items → processing_entities` (no entity_id column) —
  blocks entity-scoped pipeline (explicit design decision in
  `operations_auth.py:21-22`).
- `upload_batches.entity_id` never populated — entity upload flow incomplete.

**Database verdict:** V3 repositories conform to the real schema; the legacy
surface still reads/writes legacy tables; the two JSONB round-trips and the
`_SYSTEM_UUID` placeholder are documented transitional points. No schema change
was required or made in Phases 3–8.

---

## 9. Multi-Tenant Security Architecture

### 9.1 Authorization chains (verified)

| Persona | Chain | Verification |
|---|---|---|
| Customer | `auth.get_current_user` → `require_org_member()` / `require_org_admin()` → `ensure_org_access()` (`api/dependencies.py`) → repo SQL `WHERE organization_id = $1` | Org-scoped everywhere in `/api/v3/organizations`, `/api/v3/reports`, `/api/v3/emissions`, `/api/v3/verifications`, `/api/v3/manual-extraction` |
| Consultant | `require_consultant()` (`api/consultant_auth.py`) → firm membership + `ensure_consultant_org_access` per org/client (`v3_consultants.py:59-74`) | Mirrors RLS helper `is_org_consultant` |
| CarbonTally Admin | `require_admin()` (`auth.py`) | `/api/v3/qc`, `/api/v3/processing-entities`, `/api/v2/admin/*` |
| Operator/Reviewer/QC | `require_staff()` (`api/operations_auth.py`) → real `roles.permissions` via `staff_profiles.role_id` + `require_internal_staff()` (entity_id NULL) + per-item/batch re-authorization (`_get_item_and_batch`, `ensure_batch_operator_access`, `ensure_entity_review_scope`) | `operations_auth.py:48-59,62-140`; verified in `v3_operations.py` every endpoint |
| Processing Company | `require_entity_scope()` — entity staff can only touch their own `entity_id` work | `operations_auth.py:100-111`; entity dashboard `v3_operations.py:341` |

### 9.2 Browser-supplied ids are re-authorized server-side (verified)

- `/api/v3/ops/items/{id}/workspace|start|extract|map|validate|calculate|qc` →
  `_get_item_and_batch(context, repos, item_id)` re-checks entity scope + batch
  assignment on every call (`v3_operations.py:185-233,418-705`).
- `/api/v3/consultants/*` re-checks client ownership + org grant
  (`v3_consultants.py:59-74`).
- `/api/v3/organizations/*`, `/api/v3/reports/*`, `/api/v3/emissions/*` call
  `ensure_org_access` with the caller's `AuthUser` against the requested
  `organization_id` (`api/dependencies.py`).

### 9.3 RLS state

- **Deny-by-default floor + allow storey** exist as migrations
  (`supabase/migrations/20260803000000_rc2_rls.sql`, `20260807070000_add_new_table_rls.sql`,
  `20260810050000_v3m6_entity_rls.sql`), including consultant tenancy guards and
  column-restricted PII.
- **Service-role bypasses RLS by design** (`infra/supabase.py:7-14` — service-role
  client + `postgres` superuser pool). All tenant isolation for V3 surfaces is
  **enforced in-code**, not in-DB.
- **Not verified**: whether the RLS migrations are applied to the live DB
  (integration tests not run; Phase 8 §19).
- Legacy routes use the same service-role client with **inline, non-uniform**
  checks — legacy org/admin endpoints are only as safe as their ad-hoc guards.

### 9.4 Findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| S1 | V3 surfaces enforce org/entity/consultant isolation server-side on every id | §9.2 | — (good) |
| S2 | Live-DB RLS application unverified | integration not run | **P0 to verify** |
| S3 | QC surface guarded by `require_admin` only (no staff-with-permission) and `qc_stats` hardcodes approved/rejected = 0 | `api/v3_qc.py:34-44,47-52` | P2 (thin surface) |
| S4 | `roles.permissions` is authoritative; `AuthUser.permissions` is not trusted by ops auth | `operations_auth.py:54-58` | — (good) |
| S5 | No rate limiting mounted (`middleware/rate_limit.py` exists but is not wired in `main.py` or `api/router.py`) | grep verified | P1 (production) |
| S6 | MFA/TOTP not implemented; external-auth parity untested | plan §17; no code | P1 (production) |

---

## 10. Processing Pipeline Integration

Traced actual path (V3 surfaces):

```
SOURCE (file_url on batch/item)
  → EXTRACTION     POST /api/v3/ops/items/{id}/extract   (staff can_process)
  → MAPPING        POST /api/v3/ops/items/{id}/map       (facility/asset/supplier/factor selection)
  → VALIDATION     POST /api/v3/ops/items/{id}/validate  (validation engine; blocking findings → issues, revert to mapping)
  → CALCULATION    POST /api/v3/ops/items/{id}/calculate (CalculationEngine → snapshot + emissions_log persisted; item stamped)
  → REVIEW         manual_review_queue (assign/complete)  + customer review (customer_approved on item)
  → QC             POST /api/v3/ops/items/{id}/qc + /api/v3/qc/items/{id}/review (quality_score)
  → EMISSIONS      emissions_logs / calculation_snapshots (written at CALCULATION)
  → REPORT         /api/v3/reports → ReportGenerationEngine reads emissions_logs
```

### 10.1 Which steps are connected

**All steps are connected and functional at the API level** for
manually-created batches/items (verified in `v3_operations.py` and
`data/manual_extraction.py`). State transitions are enforced via
`ITEM_STATUS_FLOW` / `can_transition_item_status` (`domain/partners.py`,
`v3_operations.py:165`), persisted on `manual_extraction_items.status`.

### 10.2 Which are only independently implemented

- **Automatic extraction/OCR** is independent (`engines/ai_extraction.py`,
  `engines/extraction.py`) — not wired to the ops pipeline; ops extraction is
  manual data entry.
- **Legacy pipeline** (`routes/upload.py` → `routes/admin/extraction.py` →
  `routes/admin/reviews.py`/`assignments.py`) is a **parallel, disconnected**
  pipeline over legacy tables (`documents`, `upload_batches`, `manual_review_queue`)
  — no link into `emissions_logs`.
- **Approval hand-off**: there is **no step** that propagates QC/customer
  approval from the item into `emissions_logs`; logs are created at the calculate
  step and never updated by later stages.

### 10.3 Where data is persisted / state transitions occur

- Batches/items: `manual_extraction_batches` / `manual_extraction_items`
  (status transitions, extracted/mapped/calculated fields, QC + customer stamps).
- Snapshot + log: `calculation_snapshots` + `emissions_logs` (at calculate).
- Issues: `issues` (validation findings via `work_item_id`).
- Review: `manual_review_queue` (+ SLA columns).
- Reports: `report_generation_queue` + `report_versions`.

### 10.4 Where the pipeline can currently break / integrity gaps

1. **QC/customer rejection does not retract or flag the emissions log/snapshot**
   created at calculate time → a report can include rejected work. (`qc_review`/
   `customer_review` in `data/manual_extraction.py` update only the item; report
   `find_by_org` reads all logs.)
2. **Item ↔ snapshot provenance missing** — no `snapshot_id`/`emissions_log_id`
   stored on the item (`v3_operations.py:698-700`).
3. **No automated source→item creation** — batches/items are created manually via
   `/api/v3/manual-extraction`; uploads (`upload_batches`) are not connected.
4. **Manual-extraction batches/items lack `entity_id`** — entity staff cannot run
   the pipeline (documented design).
5. **No async/worker** — everything synchronous; large OCR/CSV/AI/report work has
   no queued execution (report generation is synchronous inside the request).

### 10.5 Can a complete real end-to-end workflow execute today?

**Partially.** Within the V3 surface, a staff operator can create a batch/item,
run extract→map→validate→calculate→review→QC→report against the live DB and the
API will persist every step. **However:** (a) it has never been exercised
end-to-end against a live DB (integration/E2E not run); (b) rejection integrity
(10.4.1) is unresolved; (c) automatic extraction/OCR is not wired; (d) uploads do
not feed the pipeline. **A production-grade, verified end-to-end workflow does
not yet exist.**

---

## 11. Split-Screen Workspace

Inspection of `frontend/src/v3/ops/WorkItemWorkspace.jsx` and the backend
contract `api/v3_operations.py:418-478` (+ Phase 3 `/api/v3/processing` workspace):

| Element | Functional? | Evidence |
|---|---|---|
| Source document rendering | **PARTIAL** — the pane shows a `file_url` link + JSON metadata; no PDF/text rendering inside the pane | `WorkItemWorkspace.jsx:39-45`; workspace `source` = `{file_url, file_name, document_type, page_count, viewer_url}` (`v3_operations.py:439-445`) |
| Structured data panel | **YES** — extracted/mapped/calculated data rendered as JSON, editable via role actions | `WorkItemWorkspace.jsx:46-49` |
| Extraction | **YES** — `extractItem` posts extracted_data | `WorkItemWorkspace.jsx` renderActions → `api.js extractItem` |
| Mapping | **YES** — `mapItem` + `getMappingOptions` (facilities/assets/suppliers/factors) | `api.js:349-368`; `v3_operations.py:481-503` |
| Validation | **YES** — `validateItem` runs the validation engine; findings + issues shown | `api.js:370-371`; `v3_operations.py:582-613` |
| Review | **YES** — review queue assign/complete + customer review | `v3_operations.py:775-844` |
| QC | **YES** — `qcReviewItem` + QC fields (quality_score, qc_by, qc_at, qc_notes) | `api.js:379-383`; `v3_operations.py:703-737` |
| Role-specific controls | **YES** — `renderActions` render prop layers controls per persona | `WorkItemWorkspace.jsx:11,63` |
| Source coordinates/spans | **NO** — no text-layer spans, no `extraction_spans` table, no coordinate highlight | workspace has no span payload; no spans model in `domain/` |

**Verdict:** the split-screen workspace is a **functional structured-data +
document-metadata** workspace with a real end-to-end action contract. The
document *viewer* (actual PDF/OCR text layer) and **coordinate span highlighting
remain placeholders** (documented Phase-2 follow-on in the consolidation plan
§14 and legacy plan §12/D7).

---

## 12. Emissions / Calculation Provenance

### 12.1 Verified authoritative chain

```
CalculationEngine.calculate (engines/calculation.py)
  → CalculationSnapshot (SHA-256 content_hash, domain/calculation.py)
  → EmissionsLogsRepository.save_snapshot + create  (data/emissions_logs.py)
  → emissions_logs.snapshot_id links log ↔ snapshot
  → ReportGenerationEngine reads emissions_logs.find_by_org and verify()-checks
    snapshots in the provenance section (engines/report_generation.py:564-629)
```

Snapshot columns (`data/emissions_logs.py:43-48`): id, organization_id, activity,
activity_type, quantity, quantity_unit, co2e_multiplier, co2e_kg, scope, date,
factor_id, factor_source, factor_set, import_batch_id, reporting_year,
methodology, algorithm_version, content_hash, calculated_at, calculated_by,
request_id, factor_kind, customer_factor_id. **Full factor provenance is
snapshotted.**

### 12.2 Findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| P1 | Frontend never calculates in the V3 surface (api.js fetches results only) | `v3/api.js:1-4` | — (good) |
| P2 | Legacy frontend **does** calculate client-side (hardcoded factors) | `App.js:56,952-954` | **LEGACY — remove with legacy UI** |
| P3 | Ops pipeline snapshot/log has no item link back (no `snapshot_id` on `manual_extraction_items`) | `v3_operations.py:698-700` | P1 (provenance) |
| P4 | QC/customer rejection does not flag/retract the persisted log → report data can include rejected work | §10.4.1 | **P0/P1 (integrity)** |
| P5 | `facility_id` round-trips through `metadata` JSONB | `data/emissions_logs.py:38,53-55` | P1 (schema cleanliness; proposed column) |
| P6 | Legacy reporting path recomputes inline (FPDF) without snapshots | `routes/reports.py` + `report_generator.py` | **LEGACY — remove with legacy reporting** |
| P7 | `_SYSTEM_UUID` placeholder for actor columns | `data/emissions_logs.py:22-24` | P2 (audit attribution) |

---

## 13. Reporting Conformity

### 13.1 V3 reporting (canonical)

- `api/v3_reports.py` — org-scoped lifecycle `QUEUED → GENERATING → READY/FAILED`
  on `report_generation_queue`, `report_versions` versioning, single supported
  report type (`annual`), content + download from persisted `generated_content`.
- `engines/report_generation.py` — structured 12-section JSON content built from
  persisted `emissions_logs` + org metadata + validation + benchmarking + snapshot
  verification (provenance section).
- `api/v3_exports.py` — CSV/JSON exports over the same org-scoped data.

**V3 reporting uses authoritative snapshotted data** (§12.1) and is the correct
canonical path.

### 13.2 Findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| R1 | Legacy `routes/reports.py` + `report_generator.py` (FPDF, inline, client-supplied dates) still mounted and consumed by the legacy dashboard | `main.py:213`; grep | **LEGACY — superseded; retirement depends on V3 UI re-pointing** |
| R2 | Report content reads all logs for org/period with **no approval/QC filter** (see §12 P4) | `engines/report_generation.py:171-175` | P0/P1 (integrity) |
| R3 | Legacy frontend report entry points (dashboard) still call `/api/reports/*` | `App.js`/dashboard code | **LEGACY** |
| R4 | Only one report type (`annual`) is engine-backed; legacy labels (summary/documents/staff/…) are deliberately unsupported | `v3_reports.py:58-60` | By design (documented) |
| R5 | Sync generation inside the request (no worker) — acceptable for now, scales poorly | `v3_reports.py:15-25` | P2/P3 |

---

## 14. Known Gaps (classified, not all Phase 9)

| Gap | Classification / lifecycle stage | Evidence |
|---|---|---|
| Processing Company — partial | Entities CRUD + staff entity scope exist; entity-scoped pipeline blocked by missing `entity_id` on manual-extraction tables; entity dashboard thin | `v3_processing.py`, `operations_auth.py:100-111`, Phase 8 §5 | **P1** (schema decision + pipeline) |
| SLA/escalation engine | Settings read-only (`GET /api/v3/ops/sla/settings`); no update endpoint; no background breach/escalation | `v3_operations.py:846-853`; Phase 8 §9 | **P1** (ops) |
| `upload_batches.entity_id` propagation | Never written by V3 code | Phase 8 §23 | **P1** (data) |
| Integration tests (live DB) | Not executed — **P0** | Phase 8 §19; `tests/integration/*` present | **P0** |
| Browser/E2E tests | Not executed — **P0** | Phase 8 §21 | **P0** |
| MFA/TOTP | Not implemented — **P1** (production security) | plan §17; no code | **P1** |
| Source coordinate highlighting | Not implemented (needs `extraction_spans`, Phase-2) — **P2** | consolidation plan §14/D7 | **P2** |
| System-wide audit logging | V3 audit exists (`data/audit.py`, `api/admin_audit.py`, `infra/audit_logger.py`); legacy routes largely unaudited — **P2** | grep | **P2** |
| Production RLS hardening | Migrations exist, live-DB application unverified, service-role bypass documented — **P1** | §9.3 | **P1** |
| Security testing | None — **P2** (after RLS) | plan §17 | **P2** |
| Performance testing | None — **P2/P3** | no benchmark suite | **P2/P3** |
| Synthetic document testing | None (OCR/PDF corpus) — **P2** | no fixture corpus | **P2** |
| Legacy elimination | Pending plan §15 approvals (D3/D5) — **P1/P2** | legacy plan §10 | **P1/P2** |

---

## 15. Legacy Inventory (per CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md)

Inspected modules — classification with V3-replacement verification:

### 15.1 RETAIN (transitional — required until V3 surface replaces them)

| Module | Reason |
|---|---|
| `backend/auth.py` | Single JWT/RBAC surface (V3 reuses it) |
| `backend/database.py` | Still used by `auth.py` and every legacy route; retire only after auth re-pointing |
| `backend/routes/**` | Transitional mount; consumed by legacy frontend + old admin |
| `backend/config.py` | Legacy config; superseded by `core/config.py` + `infra/config.py` but still required by legacy app |
| `backend/middleware/rate_limit.py` | Valid middleware — currently **unmounted**; should be wired, not deleted |
| `backend/utils/email.py` | Valid email helper (migrate into V3 notification service) |
| `backend/utils/document_classifier.py` | Retain as fallback for AI extraction (REFACTOR per plan) |
| `backend/utils/staff_workload.py` | Valid workload helper (REFACTOR into V3 ops engine) |
| `frontend/` (legacy root) + `admin/` | Reference + deployed UI until V3 UI is primary |

### 15.2 REIMPLEMENT (needed by V3, poor/duplicate implementation)

| Module | V3 replacement (verified) |
|---|---|
| `backend/utils/emissions.py` (calc/match/validate) | `engines/calculation.py`, `engines/factor_matching.py`, `engines/validation.py` |
| `backend/report_generator.py` + `routes/reports.py` (FPDF inline) | `engines/report_generation.py` + `api/v3_reports.py` + `data/reports.py` |
| `routes/admin/reviews.py` / `assignments.py` / `workload.py` | `api/v3_operations.py` + `api/v3_processing_workflow.py` + `data/review_queue.py` |
| Frontend `App.js` `DEFRA_FACTORS` + client calc | `/api/v3/emissions/calculate` + factor API |
| `routes/customer_documents.py` verification | `api/v3_verifications.py` |
| `routes/notifications.py` | `api/v3_notifications.py` |

### 15.3 ARCHIVE (reference only)

`process_emissions.py`, top-level `glossary.py`, `pdf_engine.py` (OCR reference),
`backend/supabase/` local stack config, `services/email.js`, `current_project_structure.txt`,
`create_admin_dashboard.py`, `admin_log_viewer.feature.txt`, `admin-dashboard.zip`.

### 15.4 REMOVE (obsolete/duplicate — after approval; V3 replacement verified)

| Module | V3 replacement exists? |
|---|---|
| `main copy.py`, `main copy 2.py` | Yes — `main.py` (single app) |
| `requirements copy.txt` | Yes — `requirements.txt` |
| `glossary copy.py` | Yes — `glossary.py` |
| `frontend/src/App copy.js`, `LandingPage copy.jsx`, `CarbonTallyDemo copy.jsx`, `FileUploadHero copy.jsx`, `App copy.css` | Yes — originals |
| `routes/customer_verifications.py` (stale) | Yes — `api/v3_verifications.py` |
| `routes/customer_dashboard.py` | Partial — V3 ops dashboard + reports replace |
| `routes/admin/audit_logs.py` (stale) | Yes — `api/admin_audit.py` + `data/audit.py` |
| `routes/admin/document-types.py` | Partial — reference data endpoint needed first |
| `routes/communication.py` | **No** — messaging surface must be decided before removal |
| `_v3m12_*`, `_phase10_selfcheck.py`, `_cf_verify*`, probe/scratch files | N/A (debug artifacts) |

**Deletion dependencies:** no REMOVE may proceed before (a) the V3 UI is the
primary deployed surface for that capability, (b) approval of plan decisions D1–D9,
(c) verification that the V3 replacement endpoint is consumed. `routes/communication.py`
and `routes/admin/document-types.py` need explicit replacement decisions.

---

## 16. Testing State

### 16.1 Verified this session

| Suite | Result | Evidence |
|---|---|---|
| Phase 8 (`test_operations_auth.py` + `test_v3_operations.py` + `test_v3_qc.py`) | **54 test functions** (18+31+5) | grep count of `def test_` |
| Full unit suite (unit/api + unit/engines + unit/domain + unit/infra + unit/core) | **778 test functions** → ≈900 parametrized cases, **RC=0, 0 failures** per Phase 8 report §20 | grep count + Phase 8 report |
| Phase 5 runtime verification | **40/40 PASS** (recorded) | Phase 5 report |

### 16.2 Unverified

- **Integration (live DB)**: `tests/integration/*` (incl. `test_v3m1_v3m2_processing_entities.py`,
  `test_v3_rls_behavior.py`, `test_v3_repositories.py`) — **not run**.
- **Browser / E2E**: no browser test run for V3 pages; `v3/__tests__/api.test.js`
  covers client methods only (static).
- **OCR/PDF**: `engines/ai_extraction.py` + `engines/extraction.py` unit-tested;
  no synthetic-document corpus, no live OCR run.
- **Storage**: Supabase Storage upload/download not exercised.
- **Realtime**: event bus unit-tested; no Supabase Realtime integration test.
- **External authentication**: Google OAuth / magic-link flows not tested.
- **Production-like environment**: no prod-config smoke test.

---

## 17. Integration Readiness

**NOT READY.** Integration verification is the single largest open gap:
- Live-DB integration suites for the Phase 8 repositories and V3M1–M6 migrations
  have **not executed** (Phase 8 §19).
- No end-to-end pipeline run against a real Postgres (source → … → report).
- No RLS behaviour verification against the applied schema
  (`tests/integration/test_v3_rls_behavior.py` exists, unrun).

Blocking before integration can be trusted: P0.1, P0.3 (integrity), P0.5 (see §20).

---

## 18. Security Readiness

**NOT READY for production.** In-code isolation is strong (verified §9.2), but:
- RLS migrations exist; **live-DB application and behaviour unverified** (P0).
- Service-role bypass means every V3 repository is trusted to scope SQL; a
  regression here is invisible without the RLS integration suite.
- No rate limiting wired (`middleware/rate_limit.py` unused); no MFA/TOTP;
  credential rotation policy undocumented; legacy routes use ad-hoc guards.

---

## 19. Production Readiness

**NOT READY.** P0 (integration/E2E/integrity) + P1 (RLS hardening, MFA, rate
limit, legacy frontend calculation retirement, legacy reporting retirement,
`upload_batches.entity_id`, item↔snapshot provenance, facility_id column) must
land before production. The unit-green state is necessary but not sufficient.

---

## 20. Priority Matrix (P0/P1/P2/P3)

Legend — Issue | Evidence | Affected component | Why it matters | Recommended action | Owning phase | Dependencies

### P0 — must fix before integration/E2E

| # | Issue | Evidence | Affected | Why | Action | Phase | Dependencies |
|---|---|---|---|---|---|---|---|
| P0.1 | Live-DB integration + RLS verification not executed | Phase 8 §19; `tests/integration/*` unrun | `data/*`, `infra/supabase.py`, V3M1–M6 | Every repo SQL string is unproven against the real schema; service-role isolation is unverified | Start local Supabase/Postgres; run `tests/integration/*`; fix failures | Phase 9 (first) | Healthy DB env |
| P0.2 | Two application entry points (`main.py` dual-mount vs `main_v2.py`) | `main_v2.py:16`, `api/router.py:194`, `api/__init__.py:20` | deployment, OpenAPI contract | Two apps drift; violates D1/D2 | Decide D1/D2: single `main.py` app = legacy mount + V3 router; archive `main_v2.py` | Phase 9 | Approval |
| P0.3 | QC/customer rejection does not flag/retract `emissions_logs` | `data/manual_extraction.py` (item-only updates); `engines/report_generation.py:171-175` (no filter) | ops pipeline, reporting | Reports can include rejected work — data integrity | Add approved-state handling: rejection sets log/snapshot status or excludes from report input; add test | Phase 9 | Schema review (additive) |
| P0.4 | No verified end-to-end pipeline run | §10.5 | whole V3 surface | "Works on paper" until proven | Scripted E2E: create batch→extract→map→validate→calculate→QC→review→report on live DB | Phase 9 | P0.1, P0.3 |
| P0.5 | V3 frontend calls legacy `/api/organizations/members/user/{id}` | `frontend/src/v3/api.js:45-51` | V3 admin/reports pages | V3 surface depends on legacy endpoint; blocks clean legacy retirement | Add `GET /api/v3/me` (profile + primary org) and re-point `resolveV3Organization` | Phase 9 | None |

### P1 — must fix before production

| # | Issue | Evidence | Affected | Why | Action | Phase | Dependencies |
|---|---|---|---|---|---|---|---|
| P1.1 | Production RLS hardening (apply + verify migrations; user-scoped query discipline; MFA; credential rotation) | §9.3, plan §17 | DB, auth | Direct-client isolation and defense-in-depth | Apply RLS migrations; run RLS suite; add MFA/TOTP; rotate credentials | Phase 10 / security | P0.1 |
| P1.2 | Legacy frontend authoritative calculation + hardcoded factor map | `App.js:56,952-954` | customer UI | Violates no-frontend-calculation; stale factors | Replace legacy dashboard paths with V3 API; remove map | Phase 9 (UI re-point) | V3 UI coverage |
| P1.3 | Legacy FPDF reporting path still mounted/consumed | `routes/reports.py`, `report_generator.py` | reporting | Duplicate, non-snapshot, inline | Retire after V3 reports UI re-points | Phase 9/10 | P1.2 |
| P1.4 | `upload_batches.entity_id` + per-item assignment not written | Phase 8 §22-23 | data model | Entity flows incomplete | Propagate entity_id; persist per-item `assigned_to` | Phase 9 | Schema decision |
| P1.5 | Item ↔ snapshot/emissions_log provenance link missing | `v3_operations.py:698-700` | provenance | Forensic trace from report→item impossible | Store `snapshot_id` on item (additive column or link row) | Phase 9 | Approval |
| P1.6 | `facility_id` JSONB round-trip | `data/emissions_logs.py:38,53-55` | schema | Query/analysis friction | Add `facility_id` column (approved proposal) | Phase 10 | Approval |
| P1.7 | Rate limiting not wired; QC surface thin (admin-only guard, fake stats) | §9.4 S3/S5 | api | Ops exposure; QC stats misleading | Mount `rate_limit.py`; align QC guard + stats | Phase 9 | None |
| P1.8 | SLA/escalation engine | `v3_operations.py:846-853` read-only | ops | SLA columns unused; no escalation | Settings update endpoint + breach runner | Phase 9/10 | — |
| P1.9 | Legacy security surface (ad-hoc org/admin guards on `/api/organizations/*`, `/api/admin/*`) | §9.3 | legacy routes | Legacy endpoints are a blast radius | Re-point consumers to V3; then retire legacy routes | Phase 10 | P1.2/P1.3 |

### P2 — important, follow production

| # | Issue | Evidence | Why | Action | Phase |
|---|---|---|---|---|---|
| P2.1 | System-wide audit coverage (legacy routes unaudited) | §14 | Compliance | Extend `AuditLogger` into remaining legacy surfaces before retirement | 10 |
| P2.2 | Source coordinate spans (`extraction_spans`) + real document viewer | §11 | Operator UX | Implement Phase-2 spans; text-layer rendering | 10/11 |
| P2.3 | Legacy elimination (plan §15 + D3/D5 per-module) | §15 | Codebase | Approve + execute removal in dependency order | 10 |
| P2.4 | Security testing (auth matrix, isolation, JWT abuse) | §14 | Assurance | Automated security suite after RLS verified | 10 |
| P2.5 | Synthetic document corpus (OCR/PDF) | §16.2 | Extraction confidence | Corpus + regression tests | 11 |
| P2.6 | Performance testing (bulk/batch) | §14 | Scale | Benchmark bulk calculate/report | 11 |
| P2.7 | `_SYSTEM_UUID` actor attribution policy | `data/emissions_logs.py:22-24` | Audit accuracy | Clean actor/column policy | 10 |

### P3 — future enhancement

| # | Issue | Why | Action |
|---|---|---|---|
| P3.1 | Async worker infrastructure (`processing_jobs`, report queue consumer) | Scale + UX | Supabase-backed job table + worker (plan D8) |
| P3.2 | Realtime pipeline progress via Supabase Realtime | Ops UX | Publish item/batch events |
| P3.3 | Additional report types (summary/documents/…) + PDF rendering step | Product | Engine extension after queue worker |
| P3.4 | External auth parity + magic-link hardening | Adoption | Auth phase |
| P3.5 | Advanced benchmarking/insights + carbon-reduction-plan surfaces | Product | Post-platform |


---

## 21. Phase 9 Readiness Decision

# **READY WITH CONDITIONS**

The V3 architecture is real, layered, and unit-verified; the canonical engines
and repositories are in place and the V3 API surface is complete for the Phases
3–8 personas. **Phase 9 may begin only after the following blocking conditions
are met** (they are the P0 set):

1. **P0.1 — Live-DB integration + RLS verification executed and green.**
   The `tests/integration/*` suite (repositories, V3M1–M6 migrations, RLS
   behaviour) must run against the real local Postgres and pass.
2. **P0.2 — Single-app decision (D1/D2) made and implemented.** One entry point
   (`main.py` = legacy transitional mount + V3 router), `main_v2.py` archived —
   or the decision explicitly deferred with a recorded reason.
3. **P0.3 — QC/customer rejection integrity fixed.** Rejected work must not
   surface in `emissions_logs`/reports (flag/retract/exclude + test).
4. **P0.4 — One scripted end-to-end pipeline run** (batch → extract → map →
   validate → calculate → QC → review → report) executed against the live DB.
5. **P0.5 — V3 frontend legacy dependency removed** (`/api/v3/me` + re-point
   `resolveV3Organization`).

Non-blocking but expected inside Phase 9: the P1.2–P1.9 platform/ops items.

---

## 22. Recommended Phase 9 Scope

Priority order (first → last), all conditioned on §21:

1. **Integration hardening** (P0.1, P0.4): run/fix `tests/integration/*`,
   repository SQL review, migration verification.
2. **Pipeline integrity** (P0.3, P1.5): approved-state handling for logs,
   item↔snapshot linkage.
3. **Single-app consolidation** (P0.2): entry-point unification, error contract
   harmonisation, `main_v2.py` archiving.
4. **Frontend re-pointing** (P0.5, P1.2): `/api/v3/me`, legacy dashboard → V3
   endpoints, remove client-side calculation and `DEFRA_FACTORS` from the
   deployed UI.
5. **Ops completeness** (P1.4, P1.7, P1.8): `upload_batches.entity_id`,
   per-item assignment persistence, rate limiting mount, SLA settings update +
   breach runner, QC surface alignment.
6. **V3 browser test pass** (new): run `npm test` + a browser smoke pass over
   `/organization`, `/consultant`, `/ops`, `/reports`.
7. **Legacy retirement prep** (P1.3, P1.9): switch legacy report/ops consumers to
   V3; begin per-module removal under plan §15 with D3/D5 approval.

**Explicitly out of scope for Phase 9:** RLS production enforcement + MFA
(Phase 10), synthetic-document corpus and performance (P2), worker
infrastructure (P3).

---

## 23. Recommended Post-Phase-9 Work

1. **Phase 10 — Production security** (P1.1): apply/verify RLS on live DB,
   user-scoped query discipline, MFA/TOTP, credential rotation, security
   testing suite (P2.4), system-wide audit coverage (P2.1).
2. **Phase 10 — Legacy elimination** (P2.3): execute plan §15 removals in
   dependency order after V3 UI coverage confirmed; archive reference material.
3. **Phase 10/11 — Data model completion** (P1.6, P2.7): `facility_id` column,
   actor/`_SYSTEM_UUID` policy, `extraction_spans` for coordinate highlighting
   (P2.2).
4. **Phase 11 — Quality & scale**: synthetic document corpus (P2.5),
   performance testing (P2.6), browser/E2E automation, then async workers +
   realtime (P3.1/P3.2) and product enhancements (P3.3–P3.5).

---

## 24. Exact Next Actions

1. Record this gate decision and the P0 list for review/approval (no code).
2. Approve P0.2 (single-app decision) and the additive schema changes implied by
   P0.3/P1.5 (approved-status handling, item↔snapshot link).
3. Stand up the local Supabase/Postgres environment and execute
   `tests/integration/*` (P0.1).
4. Fix the integration failures, then run the scripted end-to-end pipeline
   smoke test (P0.4).
5. Implement P0.3 (rejection integrity) with unit + integration tests.
6. Implement `/api/v3/me` and re-point `resolveV3Organization` (P0.5); run the
   V3 frontend unit tests and a browser smoke pass.
7. Then, and only then, begin the P1 scope in §22.

---

**Final statement:** This gate was plan/audit only. No application code, tests,
database, RLS, `.env`, migrations, or files were modified. Phase 9 was not
started. The conformity verdict is **READY WITH CONDITIONS** (P0 list in §21).

