# CarbonTally Backend V3 — Migration / Adaptation Plan v1.0

**Status:** AUDIT COMPLETE — READ-ONLY. No code, database, migration, RLS,
Storage, API contract, test or data was modified.
**Date:** 2026-08-14 · Branch: `main`
**Mode:** READ-ONLY audit of the existing CarbonTally Backend V2.1 against the
already-implemented V3 database (V3M-1/V3M-2/V3M-3/V3M-5/V3M-6) and the V3
architecture baseline.
**Factor baseline (unchanged):** DEFRA-DESNZ / GB / 2025 = 7,029 · SEAI / IE /
2025 = 20 · TOTAL = 7,049.

**Scope decisions honoured:**
- The V3 DATABASE MIGRATION IS COMPLETE. **No migration plan is created.**
- The Supabase-vs-FastAPI architectural principle is **not** redesigned:
  Supabase = auth, RLS, direct CRUD, simple queries, relationships, storage,
  realtime; FastAPI = business logic, factor matching, emission calculations,
  document processing, PDF/OCR, AI extraction, validation, benchmarking, report
  generation, workflow/orchestration, complex business operations.
- This document is the decision input for the remaining backend work only.

---

## 1. Executive Summary

### 1.1 What V2.1 already implements (the V3 reuse baseline)

Backend V2.1 (Phase 4–10, traceability matrix v1.0) is **implemented and
verified at the unit level**:

- **Domain layer (11 modules):** `domain/audit.py`, `domain/benchmarking.py`,
  `domain/calculation.py`, `domain/document.py`, `domain/factor.py`,
  `domain/matching.py`, `domain/organization.py`, `domain/provider.py`,
  `domain/report.py`, `domain/validation.py`, `domain/workflow.py` — pure,
  immutable, frozen dataclasses; no framework or DB imports.
- **Repository layer (9 repos):** `data/audit.py`, `data/documents.py`,
  `data/emission_factors.py`, `data/emissions_logs.py`, `data/events.py`,
  `data/factor_aliases.py`, `data/imports.py`, `data/organizations.py`,
  `data/reports.py` — persistence only, over the service-role asyncpg pool.
- **Engine stack (8 engines):** `engines/factor_matching.py` (+6 pipeline
  stages in `engines/matching_stages.py`), `engines/calculation.py`,
  `engines/extraction.py`, `engines/ai_extraction.py`, `engines/validation.py`,
  `engines/benchmarking.py`, `engines/report_generation.py`,
  `engines/workflow.py`.
- **Infrastructure:** `infra/supabase.py` (service-role client + asyncpg pool),
  `infra/event_bus.py`, `infra/audit_logger.py`, `infra/search_index.py`,
  `infra/llm_client.py`, `core/exceptions.py` (stable codes + HTTP mapping).
- **v2.1 API (19 routes):** `api/router.py` `create_app()` (served by
  `backend/main_v2.py`); thin business endpoints `/factor-match`, `/calculate`,
  `/validate`, `/benchmark`, `/generate-report`; admin endpoints
  `/admin/imports`, `/admin/providers`, `/admin/audit`, `/admin/aliases`;
  consistent error envelope; CO2/CO2e provenance preserved via `gas_coverage()`.
- **Auth/RBAC:** `backend/auth.py` — JWT bearer, `AuthUser`, `get_current_user`,
  `require_admin` (reused by the v2.1 API).
- **Factor data providers:** `src/commands/import_defra.py`,
  `src/commands/import_seai.py` + `src/providers/` (standalone CLI importers,
  psycopg2 — pre-existing deviations D1/D2, unchanged).

### 1.2 What V3 backend functionality is already implemented

**At the database level: everything.** V3M-1 (processing_entities +
`staff_profiles.entity_id`), V3M-2 (`manual_review_queue.entity_id` +
`upload_batches.entity_id`), V3M-3 (`customer_factors` + O1 snapshot FK
relaxation), V3M-5 (`issues`), V3M-6 (`is_entity_member()` + entity-scoped
SELECT policies) are applied and verified by three dedicated DB test suites.

**At the backend code level: essentially nothing V3-specific.** This is the
central finding of the audit. The files listed as "current V3 backend files"
are **V2.1 Phase 9/10 modules** that the V3 architecture *reuses*; none of them
reads or writes a V3 table. Concretely:

| "V3-looking" file | Actual identity | V3 status |
|---|---|---|
| `backend/api/*` | Complete V2.1 Phase 10 API | **FOUNDATION ONLY** — the V3 API surface is entirely absent |
| `backend/domain/validation.py`, `benchmarking.py` | Complete V2.1 Phase 9A/9B domain | **FOUNDATION ONLY** — reused unchanged; no V3 content |
| `backend/engines/validation.py`, `benchmarking.py`, `report_generation.py` | Complete V2.1 Phase 9A/9B/9C engines | **FOUNDATION ONLY** — reuse baseline; V3 extensions missing |
| `tests/integration/test_v3m1_v3m2_processing_entities.py` | V3M-1/V3M-2 DB verification | **COMPLETE** (as schema tests) |
| `tests/integration/test_v3m3_customer_factors.py` | V3M-3 DB verification | **COMPLETE** (as schema tests) |
| `tests/integration/test_v3m5_issues.py` | V3M-5 DB verification | **COMPLETE** (as schema tests) |

There is **no** `ProcessingEntity`, `CustomerFactor`, `Issue`, `WorkItem` or
`AutoAssignment` class anywhere in `backend/` (verified by repository-wide
search). No repository, engine, route, auth check, or audit call references
`processing_entities`, `customer_factors`, `factor_kind`,
`customer_factor_id`, `issues`, or `is_entity_member`.

### 1.3 What remains

1. **Customer-factor backend (P0).** Domain object, repository, CRUD/approve/
   deactivate API, matching candidate merge with approved-customer-first
   precedence (D-cf-5), calculation path, snapshot provenance
   (`factor_kind='customer_factor'` + `customer_factor_id`), validation rules,
   report provenance. The DB (V3M-3) is ready; no code reads or writes it.
2. **Processing-entity backend (P0).** Domain object, repository, admin API,
   entity lifecycle, entity-scoped staff resolution, and **entity_id
   propagation** into work items/batches (V3M-1/V3M-2 columns are written by
   no code path today).
3. **Entity-scoped auth/RBAC (P0).** `AuthUser`/`get_current_user` carry no
   `entity_id`; no `require_entity_member`/`require_entity_role` exists. The DB
   `is_entity_member()` helper exists but no backend call uses it.
4. **Issue service + API (P0).** The `issues` table is complete; no
   domain/service/route reads or writes it.
5. **Work-item service + assignment flows (P1).** Logical queues over
   `manual_review_queue` (entity-scoped), assign/reassign/complete/return.
6. **Calculation snapshot provenance for customer factors (P0).**
   `data/emissions_logs.py::save_snapshot` does not write `factor_kind` /
   `customer_factor_id`; the domain `CalculationSnapshot.factor_id` is a
   required `str`; `CalculationRequest` requires an `EmissionFactor`.
7. **Report/export + provenance extensions (P1).** Customer-factor provenance
   section; output-format export.
8. **Async ingestion `/process/*` + jobs (P1/OPEN).** The V3 architecture
   gates producer wiring on ADR-V3-004 (OPEN/DEFERRED).
9. **Audit entity scope (P1).** `entity_id` + actor-role on audit entries.
10. **Legacy surface retirement (P2).** `main.py` + `routes/**` (~47 modules,
    400+ endpoints) remain the primary deployed surface; consolidation is
    explicitly a later action in the V3 spec (§26.2).

### 1.4 Incremental migration or rewrite?

**Incremental migration — not a rewrite.** The V3 architecture specification,
ADR register, and V3 Impact Assessment all establish that V3 is an operational
and multi-entity **extension** of the V2.1 engine stack. Every V2.1 engine,
repository, domain object, and the 19-route API is carried into V3 largely
unchanged. The required work is *additive*:

- 3 new domain modules (`entity.py`, `customer_factor.py`, `issue.py`),
- 3 new repositories (`processing_entities.py`, `customer_factors.py`,
  `issues.py`),
- 1 new engine (`auto_assignment.py`, orchestration only) + a `WorkItem`
  service,
- ~20–25 new/extended API routes,
- extension of 4 existing engines (matching, calculation, validation,
  report_generation) and 2 repositories (`data/emissions_logs.py`,
  `data/audit.py`),
- extension of `auth.py`/`api/dependencies.py` with entity-scoped checks.

No existing V2.1 engine, repository, or route contract is deleted or redesigned.

---

## 2. Current Backend V2.1 Architecture

### 2.1 Layer map (as actually implemented)

```
HTTP
 │
 ├── ENTRY POINT A — backend/main.py (LEGACY monolith, deployed)
 │      FastAPI app; imports routes/ (15 public + 14 admin + 11 org = ~40 modules);
 │      direct Supabase REST CRUD via legacy client; ~400+ endpoints; mislabels
 │      itself api_version "v3" in /api/health (line 257).
 │
 └── ENTRY POINT B — backend/main_v2.py (v2.1 API, additive)
        app = create_app() from api/router.py
        → api/router.py        thin router, error envelope, no business logic
        → api/business.py      5 business endpoints (factor-match, calculate,
                                validate, benchmark, generate-report)
        → api/admin_*.py       imports, providers, audit, aliases (read/admin)
        → api/contracts.py     stable JSON models (CO2/CO2e provenance)
        → api/dependencies.py  composition root (per-request repos/engines,
                               infra singletons, auth reuse)
        → api/middleware.py    RequestContextMiddleware (correlation id)
              │
              ▼
        engines/ (8)   ── protocol/constructor injection ──▶ data/ (9 repos)
        domain/ (11)   ← domain objects consumed by engines and repos
        infra/         event_bus · audit_logger · search_index · llm_client · supabase pool
        core/          exceptions · logging · types
        auth.py        JWT + Supabase roles/permissions (HTTPBearer)
```

### 2.2 Actual runtime entry point

- **The v2.1 API is served by `backend/main_v2.py`** (`uvicorn main_v2:app`).
  `backend/api/__init__.py` documents that the legacy `main.py`/`routes`
  application is left untouched so the two surfaces coexist (prep-pack §5).
- **The legacy `backend/main.py` remains the pre-existing deployed surface** and
  imports the full `routes/` package (~40 modules); `routes/__init__.py`
  enumerates them. Its `/api/health` response claims `api_version: "v3"`, which
  is inaccurate — it is the V2.1/legacy surface, not V3.

### 2.3 Duplicate / legacy backend layers (do NOT delete — plan only)

| Layer | Location | Relationship to V3 |
|---|---|---|
| Legacy monolith app | `backend/main.py` + `backend/routes/**` (~40 modules, ~400+ endpoints) | CT-ARCH-002 violation (CRUD in FastAPI); spec §26.2 says **RETIRE LATER** |
| Orphaned copies | `backend/main copy.py`, `backend/main copy 2.py` | Dead copies; P2 cleanup |
| Legacy REST admin routes | `backend/routes/admin/` (staff, defra, extraction, reviews, assignments, workload, review_history, audit, beta, analytics, settings, bulk, email_templates) | Already implement much of the V3 operational plane for CarbonTally-internal staff — **the largest untapped V3 asset** (V3 IA §1.7); reuse, not rewrite |
| CLI factor importers | `src/commands/import_defra.py`, `src/commands/import_seai.py` + `src/providers/` | D1/D2 deviations; no `backend/providers/` plugin arch, no `ImportMappingEngine`; provider-independent architecture DECIDED (V3M-4) but imports remain CLI |
| Dormant tables | `processing_queue`, `processing_assignments`, `processing_steps` | ADR-V3-016 retirement DEFERRED; not entity-scoped (V3M-2) |
| Legacy report renderers | `report_generator.py` / `pdf_engine.py` / `report_templates` | PDF/HTML rendering DEFERRED (V3 spec §25) |

### 2.4 What this means for V3

The V3 architecture is already mapped onto this structure (spec §26.2): the
v2.1 API (`main_v2.py`) is the natural home for V3 routes; engines/repos are
extended in place; the legacy surface stays frozen and is retired later. No
V3 work should target `backend/main.py` or `backend/routes/**`.

---

## 3. V3 Backend Readiness Assessment

Classification vocabulary: COMPLETE (done) · PARTIAL (some done) · MISSING
(nothing) · LEGACY (exists only in the legacy surface) · REQUIRES INTEGRATION
(done in isolation, needs wiring) · REQUIRES REFACTOR (done but must change).

| # | V3 requirement | Classification | Evidence / gap |
|---|---|---|---|
| 1 | Canonical processing pipeline (validation → normalisation/match → calculation → CO₂e) | **COMPLETE** | Engines factor_matching, calculation, validation, workflow; verified Phase 9A–9D |
| 2 | 19 v2.1 route contracts + error envelope (regression guard) | **COMPLETE** | `api/router.py`, `api/contracts.py`; contract tests pass |
| 3 | CO2/CO2e provenance preservation | **COMPLETE** | `domain/factor.py::gas_coverage`; used in contracts, validation, benchmarking, reports |
| 4 | Factor alias dictionary (global + org-scoped) | **COMPLETE** | `data/factor_aliases.py`, `api/admin_aliases.py`, `RepositoryAliasResolver`; alias stage active |
| 5 | `processing_entities` table + `staff_profiles.entity_id` | **COMPLETE (DB)** / **MISSING (backend)** | V3M-1 applied; no `ProcessingEntity` domain/repo/API |
| 6 | Entity scope on work tables (`manual_review_queue`, `upload_batches`) | **COMPLETE (DB)** / **MISSING (backend)** | V3M-2 applied; no code path writes `entity_id` |
| 7 | Entity-scoped RLS (`is_entity_member`) | **COMPLETE (DB)** / **MISSING (backend auth)** | V3M-6 applied; `AuthUser` has no `entity_id`; no `require_entity_member` |
| 8 | Entity admin API + lifecycle (onboarding/offboarding, status) | **MISSING** | No routes, no domain, no repo |
| 9 | Entity staff resolution / entity-scoped roles (Manager/Supervisor/Worker/Validator) | **MISSING** | Final role names/RBAC deferred (spec §8.3); no backend support |
| 10 | `customer_factors` table + O1 snapshot relaxation | **COMPLETE (DB)** / **MISSING (backend)** | V3M-3 applied; no `CustomerFactor` domain/repo/API |
| 11 | Customer-factor matching precedence (D-cf-5 approved-first) | **MISSING** | `FactorMatchingEngine` only searches `emission_factors` via `FactorSearchIndex`; no customer-factor candidate merge |
| 12 | Customer-factor calculation path | **MISSING** | `CalculationRequest` requires `EmissionFactor` (`engines/calculation.py`); snapshot persistence has no `customer_factor_id` |
| 13 | Customer-factor snapshot provenance (O1) | **REQUIRES INTEGRATION** | DB columns exist; `data/emissions_logs.py::save_snapshot` does not write `factor_kind`/`customer_factor_id`; `CalculationSnapshot.factor_id` domain field is required `str` |
| 14 | Customer-factor approval workflow (D-cf-3 org-admin approves; no self-approval) | **MISSING** | No API/service; DB enforces vocabulary only |
| 15 | Customer-factor validation rules (value ≥ 0, unit, scope, source, conflict flag) | **MISSING** | `ValidationEngine` has no customer-factor rules |
| 16 | `issues` table | **COMPLETE (DB)** / **MISSING (backend)** | V3M-5 applied; no `Issue` domain/service/API |
| 17 | Issue lifecycle transitions (assign/escalate/resolve/reopen) + SLA | **MISSING** | Transition authority is an API concern per V3M-5 header; nothing exists |
| 18 | Work Item abstraction over `manual_review_queue` (logical queues) | **MISSING** | `manual_review_queue` written only by legacy `routes/admin/*`; no v2.1-native WorkItem service |
| 19 | Assignment / reassignment / completion (ADR-V3-005 attribution) | **LEGACY** | `routes/admin/assignments.py`, `review_assignment_history` tables exist; not v2.1-native, no entity scope |
| 20 | Auto-assignment engine (ADR-V3-007 orchestration) | **MISSING** | No engine |
| 21 | Batch → entity allocation (500-doc scenario, `upload_batches.entity_id`) | **MISSING** | No backend flow sets entity allocation |
| 22 | Customer review / approval (`customer_verifications`) | **LEGACY** | Legacy route surface; no v2.1-native review endpoints |
| 23 | Report generation (12 sections, structured) | **COMPLETE** | `engines/report_generation.py` verified (Phase 9C) |
| 24 | Report customer-factor provenance (`factor_source='CUSTOMER'`) | **MISSING** | Report provenance section only handles `emission_factors` |
| 25 | Report export (CSV/Excel/JSON) | **MISSING** | Spec §25/§26.3 marks output adapters as EXTEND |
| 26 | Async ingestion `/process/*` + jobs status | **REQUIRES INTEGRATION / OPEN** | Producer wiring gated on ADR-V3-004 (OPEN/DEFERRED in spec §11) |
| 27 | Audit scope: `entity_id` + actor-role | **REQUIRES REFACTOR** | `infra/audit_logger.py`, `data/audit.py` are org/entity agnostic; entry has no entity_id column path |
| 28 | Provider-independent factor architecture (V3M-4) | **COMPLETE (architecture)** / **LEGACY (imports)** | ADR-V3-015 DECIDED; provider catalogue endpoint exists; imports remain CLI (D1/D2); EPA/ADEME/IPCC deferred |
| 29 | Legacy operational surface (staff/workload/assignments/QC/SLA) | **LEGACY** | `routes/admin/*` implements much of the V3 control plane for internal staff; reuse decision pending |
| 30 | dpq as technical state machine | **LEGACY / OPEN** | No active producer (spec §11.2); wiring OPEN/DEFERRED |

**Overall verdict: the V3 backend is ~0% implemented as a distinct V3 surface.
The reusable V2.1 baseline is ~100% complete and needs no rewrite. The V3 work
is additive on top of it.**

---

## 4. Processing Entity Integration

### 4.1 Database state (COMPLETE)

`processing_entities` (V3M-1): `id, name, description, status
('active'/'remediation'/'suspended'/'terminated'), metadata JSONB, created_at,
updated_at, created_by, updated_by`. `staff_profiles.entity_id` nullable FK
(ON DELETE RESTRICT); `manual_review_queue.entity_id` + `upload_batches.entity_id`
(V3M-2) — NULL = CarbonTally internal (positive convention).
V3M-6 added `is_entity_member(p_entity)` (SECURITY DEFINER, search_path pinned)
and entity-scoped **SELECT** policies on `processing_entities`,
`staff_profiles`, `manual_review_queue`, `upload_batches`, `issues`.
Entity **writes** remain service-role (deliberate — V3M-6 header).

### 4.2 Backend state (MISSING)

- No `domain/entity.py` (no `ProcessingEntity` object).
- No `data/processing_entities.py` repository.
- No entity management routes; no entity lifecycle workflow.
- `backend/auth.py::AuthUser` has **no `entity_id`**, so authenticated entity
  staff are indistinguishable from internal staff at the API boundary.
- No endpoint sets `manual_review_queue.entity_id` or `upload_batches.entity_id`
  (search confirms the only writers are legacy `routes/admin/*` which do not
  reference the column).
- No audit path records `entity_id`.

### 4.3 Modules that must change

| Module | Change |
|---|---|
| NEW `backend/domain/entity.py` | `ProcessingEntity` (frozen dataclass: id, name, description, status, metadata, timestamps); status vocabulary mirrors the CHECK; lifecycle helpers |
| NEW `backend/data/processing_entities.py` | CRUD over the service pool; `get`, `list`, `save`, `update_status`, `find_by_staff`; explicit column lists (repo conventions) |
| `backend/auth.py` | `AuthUser.entity_id: Optional[str]`; `get_current_user` resolves `staff_profiles.entity_id` for staff; new guards `require_entity_member(entity_id)`, `require_entity_role(...)` (role names still deferred, so a generic member check first) |
| NEW `backend/api/admin_entities.py` | Entity CRUD + lifecycle (activate/suspend/terminate), entity staff roster (CarbonTally-internal, service-role path; entity staff cannot self-administer per ADR-V3-001 Q6) |
| NEW `backend/api/work_items.py` | Assignment surface that writes `manual_review_queue.entity_id` (see §8) |
| `backend/api/dependencies.py` | Wire `ProcessingEntitiesRepository` into `RepositoryBundle`; entity-scoped dependency helpers |
| `backend/data/audit.py` / `infra/audit_logger.py` | Optional `entity_id` + actor-role on audit entries (ADR-V3-013) |
| `backend/api/middleware.py` | Attach entity context to `RequestContext` (entity_id derived from the token/staff row) |

### 4.4 Rules that must hold

- Entity staff **never** become `organization_members` (spec §7.2) — customer
  data stays invisible to them except through assigned work.
- `entity_id IS NULL` is a **positive** value (CarbonTally internal), never
  "unknown".
- Suspension/termination must not delete history; reassignment disposition for
  active work must be defined before lifecycle transitions are exposed.
- Entity-scoped INSERT/UPDATE/DELETE on work surfaces may stay
  service-role/application-gated until the WorkItem write flow (ADR-V3-003) is
  designed — the backend service is the enforcement point.

---

## 5. Customer Factor Integration

### 5.1 Database state (COMPLETE — V3M-3)

`customer_factors`: org-owned (FK `organization_id` ON DELETE CASCADE),
`name`, `description`, `activity_type`, `co2e_multiplier >= 0`, `unit`,
`scope`, `country IN ('GB','IE')`, `reporting_year`, `factor_source DEFAULT
'CUSTOMER'`, status (`draft`/`active`/`inactive`/`archived`), `version`,
per-version family UNIQUE index, `metadata`, timestamps, created_by/updated_by.
RLS: select = `is_org_member OR is_org_consultant`; insert/update =
`is_org_member`; **no delete policy** (soft-deactivate).
`calculation_snapshots`: `factor_id` now nullable; `factor_kind NOT NULL
DEFAULT 'emission_factor'`; `customer_factor_id` nullable FK ON DELETE RESTRICT;
exactly-one-source CHECK.

### 5.2 Backend state (MISSING)

- No `CustomerFactor` domain object; no `CustomerFactorsRepository`.
- No customer-factor routes (CRUD, approve, deactivate).
- **Matching engine** (`engines/factor_matching.py`) operates only over
  `FactorSearchIndex` (loaded from `emission_factors`) + alias resolution.
  There is no customer-factor candidate merge, so D-cf-5 (approved customer
  factor first) is **not implemented**.
- **Calculation engine** (`engines/calculation.py`): `CalculationRequest.factor`
  is typed `EmissionFactor`; the `CalculationSink.save_snapshot` signature has
  no `customer_factor_id`/`factor_kind`; the repository
  (`data/emissions_logs.py::save_snapshot`) inserts neither column. Domain
  `CalculationSnapshot.factor_id: str` is required, and the content hash
  canonical form uses `factor_id` only — no `customer_factor_id` branch.
- **Validation engine** has no customer-factor rules.
- **Report provenance** section has no `factor_source='CUSTOMER'` handling.
### 5.3 What remains (exact)

1. `domain/customer_factor.py` — `CustomerFactor` frozen dataclass
   (org_id, name, activity_type, co2e_multiplier, unit, scope, country,
   reporting_year, factor_source='CUSTOMER', status, version, metadata).
2. `data/customer_factors.py` — repository: `get_org_factors`, `get_active`,
   `save`, `update_status` (soft-deactivate), `get_version_family`,
   conflict-with-reference-factor lookup.
3. `api/customer_factors.py` — routes:
   `POST/GET /api/v3/customer-factors`, `GET/PUT/DELETE(soft) .../{id}`,
   `POST .../{id}/approve` (org-admin only, no self-approval — D-cf-3),
   `POST .../{id}/deactivate`. Status transitions DRAFT→ACTIVE→INACTIVE/ARCHIVED.
4. `engines/factor_matching.py` + `domain/matching.py` — candidate merge:
   resolve ACTIVE customer factors (org-scoped) for the request before/alongside
   CarbonTally factors; precedence (1) approved customer factor, (2)
   CarbonTally matching, (3) unresolved/manual review (D-cf-5). The engine stays
   candidate-set-agnostic — no second engine.
5. `engines/calculation.py` + `data/emissions_logs.py` — accept a
   `CustomerFactor` (or a unified factor union) in `CalculationRequest`; write
   `factor_kind='customer_factor'`, `factor_id=NULL`,
   `customer_factor_id=<id>`, `factor_source='CUSTOMER'`,
   `factor_set='CUSTOMER'`, `import_batch_id=NULL` into snapshots; extend
   `CalculationSnapshot` domain with optional `customer_factor_id`; update the
   content-hash canonical form.
6. `engines/validation.py` — customer-factor rules: multiplier ≥ 0, unit/scope
   sanity, source required, flag conflict with a matched reference factor
   (additive to A1–A9).
7. `engines/report_generation.py` — provenance section includes
   `factor_source='CUSTOMER'` rows.
8. `api/contracts.py` — `CustomerFactorOut`, `CustomerFactorCreate/Update`,
   `CustomerFactorApprovalIn`; extend `CalculationIn` with optional
   `customer_factor_id`.

### 5.4 Constraints

- Customer factors **never** enter `emission_factors` (REJECTED).
- No second matching/calculation/snapshot engine (REJECTED).
- `emission_factors` (7,049) and its RLS are untouched.
- An approved customer factor is never silently replaced by a CarbonTally
  factor.

---

## 6. Factor Alias Integration

### 6.1 Current state (essentially COMPLETE)

- `factor_aliases` table (M6) + RLS (M8): org-scoped and global aliases.
- `data/factor_aliases.py`: `find_by_alias` (org first, then global),
  `get_global_aliases`, `get_org_aliases`, `save`, `delete`.
- `engines/matching_stages.py::RepositoryAliasResolver` integrates aliases into
  the `alias_match` stage; `api/dependencies.py` wires it.
- `api/admin_aliases.py`: admin CRUD with audit entries.

### 6.2 V3 delta (small)

| Concern | Status | Required change |
|---|---|---|
| Alias lookup in matching | **COMPLETE** | None |
| Customer/organization scope | **COMPLETE** | Org-scoped + global precedence already correct |
| RLS | **COMPLETE** | M8 policies in place |
| Admin management | **COMPLETE** | `api/admin_aliases.py` |
| Alias ↔ customer-factor interplay | **REQUIRES INTEGRATION** | When customer factors enter matching, the alias stage must resolve aliases against the **customer-factor candidate set** too (an alias targeting an activity that only exists as a customer factor should not silently match the CarbonTally factor); deterministic precedence must be defined |
| Alias provenance in snapshots | **REQUIRES INTEGRATION** | `factor_aliases` are resolution aids, not factor values — snapshot provenance (V3-012) should tag the alias used (optional, P2) |

---

## 7. Calculation Snapshot Integration

### 7.1 Does the existing calculation engine support V3 snapshots?

**For CarbonTally-managed factors: YES, fully.** `CalculationEngine` builds a
`CalculationSnapshot`, computes the SHA-256 content hash, persists via
`EmissionsLogsRepository.save_snapshot`, publishes events, and supports
`verify()` reproducibility. The DB O1 columns default to
`factor_kind='emission_factor'`, so existing inserts remain valid.

**For customer factors: NO.** Three concrete gaps:

1. **Domain**: `CalculationSnapshot.factor_id: str` (required) and
   `CalculationResult.factor_used: EmissionFactor` — no customer-factor branch.
   The content hash canonical form has no `customer_factor_id`/`factor_kind`.
2. **Engine**: `CalculationRequest` is typed to `EmissionFactor`
   (`engines/calculation.py`) — there is no union factor type.
3. **Persistence**: `data/emissions_logs.py::save_snapshot` inserts `factor_id`
   and omits `factor_kind`/`customer_factor_id` — a
   `factor_kind='customer_factor'` row cannot be written (the exactly-one-source
   CHECK would be violated if `factor_id` is NULL while `customer_factor_id` is
   also NULL).

### 7.2 What remains (exact)

| Layer | Change |
|---|---|
| `domain/calculation.py` | `CalculationSnapshot.customer_factor_id: Optional[str]`; content-hash canonical form includes `factor_kind` + `customer_factor_id`; `CalculationResult` factor union (`EmissionFactor | CustomerFactor`) |
| `engines/calculation.py` | `CalculationRequest.factor` accepts the union; `save_snapshot` call passes `factor_kind`, `customer_factor_id`, `factor_source='CUSTOMER'`, `factor_set='CUSTOMER'`, `import_batch_id=None` |
| `data/emissions_logs.py` | `save_snapshot` inserts `factor_kind`, `customer_factor_id` (column list already explicit; add columns + params); `create()` must tolerate the customer-factor path for `emissions_logs.emission_factor_id` (nullable column exists; decide NULL vs customer-factor-id strategy) |
| `api/contracts.py` | Snapshot responses expose `factor_kind`/`customer_factor_id`; `CalculationIn` accepts optional `customer_factor_id` |
| `engines/validation.py` | A9/verify extended to validate customer-factor snapshots (recompute against `customer_factors.co2e_multiplier` snapshot values) |
| Tests | Unit: snapshot hash determinism for both kinds; exactly-one-source persistence; verify() for customer-factor snapshots. Integration: write both row kinds against `carbontally_test` |

### 7.3 Provenance/immutability

V3M-3 preserves immutability: `customer_factor_id` FK is ON DELETE RESTRICT; a
later customer-factor edit creates a new version (`version` increment) and
never mutates past snapshots (ADR-V3-002 D-cf-4). The backend must enforce
"snapshots are append-only, never updated" on the customer-factor branch the
same way the emission-factor branch does today.

---

## 8. Issues / Review Queue Integration

### 8.1 Database state (COMPLETE — V3M-5/V3M-6)

`issues`: `issue_type` (defect/exception/escalation), `severity`, `priority`,
`status` (open/in_progress/on_hold/escalated/resolved/closed),
`escalation_level`, title/description, context FKs: `organization_id`
(CASCADE), `entity_id` (RESTRICT), `work_item_id`/`document_id`/`batch_id`
(RESTRICT), `conversation_id` (SET NULL), `assignee_id`, SLA timestamps
(`sla_deadline`/`sla_breached_at`), `reopened_at`, timestamps.
RLS: org storey (`is_org_member OR is_org_consultant AND entity_id IS NULL`)
for select/insert/update, **no delete**; entity storey (V3M-6) SELECT-only
(`entity_id IS NOT NULL AND is_entity_member(entity_id)`). Entity issue
surfaces are never customer-visible.

### 8.2 Backend state (MISSING)

No `Issue` domain, no repository, no service, no routes. No workflow raises an
Issue (QC failure → issue, extraction error → issue, escalation trigger → issue
— all are concepts only).

### 8.3 Required integration

| Component | Build |
|---|---|
| `domain/issue.py` | `Issue` frozen dataclass; status/severity/type vocab; transition table (open→in_progress→on_hold→escalated→resolved→closed, reopen) |
| `data/issues.py` | Repository: create, get, list (org-scoped + entity-scoped + CarbonTally-internal), update_status, assign, set_sla; explicit columns |
| `api/issues.py` | Org-facing routes (customer service surface, `entity_id IS NULL`): `GET/POST /api/v3/issues`, `PUT /api/v3/issues/{id}` (status/assignee/priority/severity). Entity-facing routes (service-role or entity-gated): issue view/assign/resolve for the entity's issues. CarbonTally-internal routes: cross-entity triage |
| `services/issues.py` (or engine) | Transition authority (mirrors customer-factors D-cf-3: the DB enforces vocabulary, the service enforces who may transition); escalation path; SLA deadline computation; `conversation_id` association (distinct from conversations) |
| Workflow hooks | `engines/workflow.py` + `engines/validation.py`: on blocking validation errors / extraction failures / QC failures → raise an Issue (defect/exception) rather than only publishing events; correlation via `work_item_id`/`document_id`/`batch_id` |
| Audit | Issue lifecycle recorded through `AuditRepository` (ADR-V3-013 — no new history table) |

### 8.4 Boundary rules

- Issue ≠ Conversation ≠ user_feedback ≠ qc_error (all kept distinct).
- Customer-facing issues are org-scoped and `entity_id IS NULL`; entity issues
  are entity-scoped and never customer-visible.
- No DELETE endpoint (soft lifecycle via status only).
- Assignment must respect the WorkItem/entity boundaries (an entity worker can
  only be assigned issues for their entity).

---

## 9. Supabase vs FastAPI Boundary

Architectural principle (unchanged): Supabase = auth, RLS, direct CRUD, simple
queries, relationships, storage, realtime. FastAPI = business logic and complex
operations. For every major backend operation:

| Operation | Classification | Rationale / placement |
|---|---|---|
| **organizations** — basic CRUD | **SUPABASE DIRECT CRUD** | `organizations` RLS (`is_org_member`) already gates it; today legacy routes duplicate this — the V3 target is direct client access |
| **organizations** — onboarding/lifecycle/offboarding, regulatory flags | **FASTAPI BUSINESS LOGIC** | Multi-step provisioning, validation, audit; `org_type`/consultant decisions pending (H1-b rejected) |
| **members** — invite/join/role assignment | **FASTAPI BUSINESS LOGIC** (invite) + **SUPABASE DIRECT** (read own memberships) | Invites need email/validation/audit; membership reads are simple RLS-filtered queries |
| **processing_entities** — all operations | **FASTAPI BUSINESS LOGIC** | Entity lifecycle is CarbonTally-internal; DB is deny-by-default for authenticated (only service-role + entity SELECT); entity staff cannot self-administer (ADR-V3-001 Q6) |
| **documents** — upload/list/read | **SUPABASE DIRECT + STORAGE** | Upload = Storage bucket + a metadata insert (RLS); document read = RLS-filtered query. V3 document work-type wiring (producer) stays FASTAPI/OPEN (ADR-V3-004) |
| **emission_factors** — read/search | **SUPABASE DIRECT** | Global read RLS `SELECT USING(true)`; the frontend can query directly |
| **emission_factors** — import/publish/activate | **FASTAPI BUSINESS LOGIC** | Import engine, batch activation, natural-key upsert, validation (today CLI `src/commands/*`; V3M-4 provider architecture DECIDED) |
| **factor_aliases** — org-scoped CRUD | **SUPABASE DIRECT** | M8 RLS (`factor_aliases_*_own`) already enforces org scope |
| **factor_aliases** — global CRUD | **FASTAPI BUSINESS LOGIC** (admin) | `api/admin_aliases.py` today; staff-only |
| **customer_factors** — read/draft/edit | **SUPABASE DIRECT** | V3M-3 RLS (`is_org_member`) allows select/insert/update by org members |
| **customer_factors** — approve/deactivate | **FASTAPI BUSINESS LOGIC** | D-cf-3 authority (org-admin, no self-approval); status-transition business rule |
| **customer_factors** — use in matching/calculation | **FASTAPI BUSINESS LOGIC** | Matching engine candidate merge + calculation + snapshot provenance |
| **issues** — customer-facing CRUD | **SUPABASE DIRECT** | V3M-5 org storey RLS permits it |
| **issues** — entity-scoped CRUD/transitions/escalation | **FASTAPI BUSINESS LOGIC** | Entity policies are SELECT-only; transition authority + SLA + escalation are business rules |
| **issues** — workflow-raised issues | **FASTAPI BUSINESS LOGIC** | Raised by validation/QC/extraction engines |
| **imports** — read batch history | **FASTAPI** (admin) | `import_batches` is deny-all for authenticated; service-role/admin surface (`api/admin_imports.py`) |
| **imports** — run import | **FASTAPI BUSINESS LOGIC** | Import engine (V3M-4); no schema change needed for GB/IE providers |
| **calculation_snapshots** — read | **SUPABASE DIRECT** | M8 `calc_snapshots_select_own` RLS |
| **calculation_snapshots** — write/verify | **FASTAPI BUSINESS LOGIC** | Calculation engine (reproducibility, hashing, immutability) |
| **reports** — generate | **FASTAPI BUSINESS LOGIC** | `ReportGenerationEngine` |
| **reports** — read/version/comment | **SUPABASE DIRECT** | Org RLS on `report_*` tables |
| **reports** — export | **FASTAPI BUSINESS LOGIC** | Output adapters (CSV/Excel/JSON) |
| **notifications** — read | **SUPABASE DIRECT** | `notifications.recipient_type`/RLS |
| **notifications** — send | **FASTAPI BUSINESS LOGIC** | Email providers, templates, delivery |
| **audit logs** — write | **FASTAPI BUSINESS LOGIC** | AuditLogger/engine side effects |
| **audit logs** — read/search | **FASTAPI** (admin) | Staff-only surface (`api/admin_audit.py`); audit rows have no per-tenant RLS |

**Net effect for V3:** the new V3 tables split cleanly — `customer_factors`
reads and `issues` org storey are *Supabase-direct* surfaces (RLS already
correct), while entity lifecycle, customer-factor approval, issues entity
storey, matching/calculation/validation, reports, imports and audit remain
*FastAPI business logic*. No boundary redesign is needed; new code must simply
respect it.

---

## 10. API Assessment

### 10.1 Authoritative API layer

The **v2.1 API (`backend/api/`, served by `main_v2.py`)** is the authoritative
layer for V3. It has the thin-router/error-envelope/dependency-injection
structure that V3 routes must extend (spec §26). The legacy `main.py` +
`routes/**` surface is NOT the target for new V3 code.

### 10.2 Current v2.1 endpoints

| Router | Endpoints | Notes |
|---|---|---|
| `api/business.py` | `POST /api/v2/factor-match`, `/calculate`, `/validate`, `/benchmark`, `/generate-report` | Thin orchestrators; V3 extensions target |
| `api/admin_imports.py` | `GET /api/v2/admin/imports`, `/active`, `/{id}` | Read-only batch state |
| `api/admin_providers.py` | `GET /api/v2/admin/providers`, `/{key}` | Catalogue + live state |
| `api/admin_audit.py` | `GET /api/v2/admin/audit`, `/export`, `/correlation/{id}`, `/{id}` | Audit search/export |
| `api/admin_aliases.py` | `GET/POST /api/v2/admin/aliases`, `PUT/DELETE /{id}` | Alias CRUD + audit |
| `api/router.py` | `GET /api/v2/health` | Liveness |

### 10.3 Findings

1. **No V3 endpoints exist.** There is no `/process/*`, `/jobs`,
   `/customer-factors`, `/entities`, `/work-items`, `/issues`,
   `/reports/{id}/export`, or `/customer-reviews/*` surface anywhere in
   `backend/api/` (the legacy `routes/` surface has unrelated org/admin CRUD).
2. **No duplicate business endpoints.** The v2.1 business routes are
   single-source; legacy `routes/reports.py` etc. are separate legacy surfaces
   (frozen, not touched).
3. **CRUD that should be Supabase-direct (future) but today sits in FastAPI:**
   the legacy `routes/**` org CRUD (organizations/members/documents/emissions)
   duplicates Supabase-direct CRUD — a CT-ARCH-002 violation already documented.
   These are **not moved now** (frozen surface); V3 work must not add to them.
4. **Business endpoints that belong in FastAPI (V3 additions):**
   customer-factor approve/deactivate, entity lifecycle, issue transitions,
   work-item assign/reassign/complete, batch allocation, report export,
   async ingestion (when ADR-V3-004 resolves).
5. **Endpoints requiring V3 entity context:** work-item operations, entity
   staff/roster, entity-scoped issues, batch allocation. Each must resolve the
   caller's `entity_id` (via `AuthUser`) and enforce entity boundaries.
6. **Endpoints requiring V3 customer-factor support:** `/factor-match`
   (candidate merge), `/calculate` (optional `customer_factor_id`),
   `/validate` (customer-factor rules), `/generate-report` (provenance
   section). Contracts stay backward-compatible (optional fields only).

---

## 11. Engine Assessment

| Engine | CURRENT STATUS | V3 REQUIREMENT | REQUIRED CHANGE | DEPENDENCIES | TEST REQUIREMENTS |
|---|---|---|---|---|---|
| **`engines/factor_matching.py`** (+ `matching_stages.py`) | COMPLETE (V2.1 Phase 4): 6-stage pipeline over `FactorSearchIndex` + alias resolver | Candidate merge: CarbonTally + ACTIVE customer factors; D-cf-5 precedence approved-customer-first; no second engine | Add customer-factor candidate source to the pipeline (a new stage or a customer-factor index adapter); deterministic precedence rule; expose `customer_factor_id` in `MatchResult` | `domain/customer_factor.py`, `data/customer_factors.py`, `domain/matching.py` (MatchResult field) | Unit: precedence cases (approved customer > CarbonTally > unresolved); ambiguous candidate handling; no-match. Integration: org-scoped candidates against `carbontally_test` |
| **`engines/calculation.py`** | COMPLETE (V2.1 Phase 6): reproducibility, SHA-256 hash, snapshot persistence, verify() | Ownership-agnostic: customer factors usable without a second engine; O1 snapshot provenance | `CalculationRequest` factor union (`EmissionFactor \| CustomerFactor`); snapshot carries `factor_kind`/`customer_factor_id`; hash canonical form extended | `domain/customer_factor.py`, `domain/calculation.py`, `data/emissions_logs.py` | Unit: both factor kinds produce identical/deterministic hashes; customer-factor verify(); invalid exactly-one-source rejected. Integration: snapshot rows of both kinds persist |
| **`engines/extraction.py`** | COMPLETE (V2.1 Phase 7): deterministic text→structured extraction | Human extraction = Work Item; entity attribution | No engine change; Work Item/entity context is a workflow concern. Extraction result surfaces reused unchanged | None (orchestration only) | Regression only |
| **`engines/ai_extraction.py`** | COMPLETE (V2.1 Phase 7): LLM field extraction | AI extraction = technical dpq stage; low-confidence → manual review | No engine change. Routing low-confidence AI results to Work Items is a workflow concern (OPEN with ADR-V3-004) | None (orchestration only) | Regression only |
| **`engines/validation.py`** | COMPLETE (V2.1 Phase 9A): A1–A9 | Customer-factor rules: multiplier ≥ 0, unit/scope/source, conflict-with-reference flag; validate customer-factor snapshots | Add A-ext rules (additive); snapshot verification handles `factor_kind='customer_factor'` | `domain/customer_factor.py`, `domain/calculation.py` | Unit: new rules; conflict flag; customer-factor snapshot verify. Integration: validation run over mixed snapshot set |
| **`engines/benchmarking.py`** | COMPLETE (V2.1 Phase 9B): internal/self-referential B1–B8 | No documented V3 change (REUSE) | None | — | Regression only |
| **`engines/report_generation.py`** | COMPLETE (V2.1 Phase 9C): 12 structured sections | Customer-factor provenance section; output-format export (CSV/Excel/JSON) | Provenance section includes `factor_source='CUSTOMER'` rows; export adapter layer (additive) | `domain/customer_factor.py`, `api/contracts.py` | Unit: report with customer-factor provenance; export formats. Integration: generated report round-trip |
| **`engines/workflow.py`** | COMPLETE (V2.1 Phase 8): document pipeline orchestrator | Batch → entity allocation; entity-scoped work items; raise Issues on failures | Add allocation step (sets `upload_batches.entity_id`/`manual_review_queue.entity_id`); failure hooks raise Issues; entity context in run state | `domain/entity.py`, `domain/issue.py`, `data/processing_entities.py`, `data/issues.py` | Unit: allocation logic, entity-scoped stages, issue-raising hooks. Integration: 500-doc multi-entity scenario |
| **NEW `engines/auto_assignment.py`** | — | ADR-V3-007 orchestration (no new queue/schema) | NEW engine: worker load → assignment suggestions over `staff_workload`/`staff_profiles`; entity-scoped | `data/processing_entities.py`, staff repos, `manual_review_queue` | Unit: load-balancing logic; entity boundary. Integration: assignment rows created |
| **NEW WorkItem service** | — | ADR-V3-003/011 canonical Work Item over `manual_review_queue`; logical queues | NEW service: list (queue views), claim/assign/reassign/complete/return; writes `entity_id`; append-only `review_assignment_history` | `data/processing_entities.py`, `data/issues.py` (context), auth guards | Unit: state machine. Integration: entity-scoped queue reads; attribution preserved on reassign |

---

## 12. Data Layer Assessment

### 12.1 Repositories that MUST remain in FastAPI (they encapsulate business operations)

| Repository | Why it stays | V3 change |
|---|---|---|
| `data/emission_factors.py` | Natural-key upserts, batch linkage, index loading — import/publish business | None (reused unchanged; V3M-4 future imports reuse it) |
| `data/emissions_logs.py` | Snapshot persistence + immutable provenance (calculation engine sink) | `save_snapshot` writes `factor_kind`/`customer_factor_id`; `create`/`save` tolerate customer-factor path |
| `data/imports.py` | Batch lifecycle (active-batch semantics) | None |
| `data/audit.py` | Audit write/query (staff-only surface) | Optional `entity_id` scope |
| `data/events.py` | Domain-event persistence | None |
| `data/organizations.py` | Org aggregate read (used by engines) | None |
| `data/reports.py` | Report lifecycle + content persistence | Extend provenance exposure |
| `data/factor_aliases.py` | Alias lookup precedence (org then global) | None (keep; optional alias-provenance tagging) |
| `data/documents.py` | Document status transitions (engine sink) | None |
| NEW `data/customer_factors.py` | Org-scoped factor CRUD + ACTIVE lookup for matching | New |
| NEW `data/processing_entities.py` | Entity CRUD/lifecycle (service-role; deny-by-default table) | New |
| NEW `data/issues.py` | Issue persistence + scoped queries | New |
| NEW `data/work_items.py` (or extend `data/emissions_logs`-style queue repo) | WorkItem/`manual_review_queue` service surface (entity-scoped) | New |

### 12.2 CRUD that should move to Supabase direct access (do NOT perform the move)

| Table | Today | V3 target |
|---|---|---|
| `organizations` / `organization_members` basic reads | Legacy `routes/organizations/*` | Supabase direct (RLS `is_org_member`) |
| `customer_documents` read/list | Legacy routes | Supabase direct (+ Storage) |
| `emissions_logs` read | Legacy routes | Supabase direct (RLS) |
| `factor_aliases` org-scoped CRUD | `api/admin_aliases.py` (staff-only) | Supabase direct for org members (M8 RLS); global aliases stay FastAPI admin |
| `customer_factors` draft CRUD | — (no code) | Supabase direct for org members (V3M-3 RLS) |
| `issues` customer-facing CRUD | — (no code) | Supabase direct (V3M-5 org storey) |
| `calculation_snapshots` read | — | Supabase direct (M8 select-own) |

**Rule applied:** a repository stays in FastAPI only when it encapsulates
business operations (matching, calculation, validation, provenance, audit,
imports, entity lifecycle, issue transitions). Pure CRUD is pushed to Supabase
direct access with RLS. The move itself is out of scope for this plan — it is
listed here so new V3 code does not duplicate CRUD that RLS already covers.

---

## 13. Test Coverage

### 13.1 Existing suite map

| Suite | Location | Coverage | V3 relevance |
|---|---|---|---|
| Domain unit tests | `tests/unit/domain/` | validation, benchmarking, calculation, matching, factor, organization, report, audit, workflow objects | **Complete** for V2.1; must extend for `CustomerFactor`/`ProcessingEntity`/`Issue` |
| Engine unit tests | `tests/unit/engines/` | matching stages, calculation, validation, extraction, workflow | **Complete** for V2.1; extend for customer-factor merge/snapshot/validation rules |
| API contract tests | `tests/unit/api/` (in-memory fakes, DI overrides) | 19 v2.1 routes, error envelope, admin endpoints | **Complete** for V2.1; extend for V3 routes |
| Integration suite | `tests/integration/` (asyncpg against `carbontally_test`) | repositories: audit, documents, events, extraction, factor_aliases, factor_matching, imports, search_index, workflow, ai_extraction, llm_client, infra, organizations, config | **Partial** — requires the local `carbontally_test` DB; `pytest` canonical run has historically hung when the DB is unreachable (D14) |
| **V3 DB verification** | `tests/integration/test_v3m1_v3m2_processing_entities.py` | V3M-1/V3M-2 schema invariants, RLS, FKs, factor baseline 7,049 | **Complete** (DB layer) |
| **V3 DB verification** | `tests/integration/test_v3m3_customer_factors.py` | V3M-3 customer_factors schema, RLS, O1 snapshot relaxation, exactly-one-source | **Complete** (DB layer) |
| **V3 DB verification** | `tests/integration/test_v3m5_issues.py` | V3M-5 issues schema, RLS, lifecycle CHECKs, FKs | **Complete** (DB layer) |
| Supplementary harnesses | `backend/_phase10_selfcheck.py` (49/49), `pycheck9d.txt` (74/74) | In-memory API + engine checks | Historical evidence; not a pytest replacement |

### 13.2 Gap analysis

- **Complete coverage:** V2.1 domain/engines/API unit surfaces; V3 database
  schema invariants (the three V3 test files).
- **Partial coverage:** V2.1 integration suite (blocked on `carbontally_test`
  availability in some environments — the `.pytest_cache/v/cache/lastfailed`
  shows V3 test entries and unit failures from interrupted runs).
- **Missing tests:**
  - Backend↔V3DB integration: customer-factor CRUD through the repository,
    O1 snapshot writes through `save_snapshot`, entity CRUD/lifecycle through
    the repository, issue CRUD/transitions through the service, entity-scoped
    work-item flows.
  - Engine extension tests: matching precedence (D-cf-5), customer-factor
    calculation + hash + verify, validation A-ext rules, report provenance.
  - Auth/RBAC tests: `AuthUser.entity_id` resolution,
    `require_entity_member`, entity-boundary denials.
  - **End-to-end tests:** full V3 journey (customer uploads → batch → entity
    allocation → work items → entity completes → validation → customer
    factors → calculation → snapshot → report) across API + engines + DB.
  - RLS-behaviour tests with an `authenticated` role (V3M-6 entity SELECT
    policies; V3M-3/V3M-5 org storeys) — today's V3 tests assert policy
    existence, not authenticated-role behaviour.

### 13.3 Test strategy note

Every V3 test must keep the existing discipline: unit tests run in memory
(DI overrides, `tests/unit/api/fakes.py` pattern); integration tests run
against `carbontally_test` and never the authoritative database. The
`_TRUNCATE_TABLES` list in `tests/integration/conftest.py` must be extended
with `processing_entities`, `customer_factors`, `issues`, and
`manual_review_queue`/`upload_batches` once V3 repos write to them.

---

## 14. EXACT BACKEND V3 MIGRATION DELTA

Priority: **P0** = blocking V3 · **P1** = required production functionality ·
**P2** = cleanup/optimization.

| Priority | Component | V2.1 Status | V3 Requirement | Current V3 Status | Required Change | Tests |
|---|---|---|---|---|---|---|
| P0 | `domain/customer_factor.py` | N/A (absent) | CustomerFactor domain object (ADR-V3-002) | MISSING | NEW frozen dataclass: org_id, name, activity_type, co2e_multiplier≥0, unit, scope, country GB/IE, reporting_year, factor_source='CUSTOMER', status, version | Unit: validation, immutability, versioning |
| P0 | `data/customer_factors.py` | N/A (absent) | Customer-factor repository (V3M-3 table) | MISSING | NEW repo: get_org_factors, get_active (status='active'), save, update_status (soft-deactivate), version family, conflict lookup | Integration: CRUD + RLS against `carbontally_test` |
| P0 | `api/customer_factors.py` + contracts | N/A (absent) | Customer-factor API (CRUD + approve + deactivate; D-cf-3 authority) | MISSING | NEW routes: `POST/GET /api/v3/customer-factors`, `GET/PUT/DELETE(soft) /{id}`, `POST /{id}/approve`, `POST /{id}/deactivate`; contracts | API contract tests (in-memory) |
| P0 | `engines/factor_matching.py` + `domain/matching.py` | COMPLETE (V2.1) | Customer-factor candidate merge; D-cf-5 precedence | MISSING | EXTEND: candidate set = CarbonTally + ACTIVE customer factors; precedence approved-customer → CarbonTally → manual; `MatchResult` exposes customer_factor_id | Unit: precedence; Integration: org-scoped candidates |
| P0 | `engines/calculation.py` + `domain/calculation.py` | COMPLETE (V2.1) | Customer-factor calculation + O1 snapshot provenance | MISSING | EXTEND: factor union in `CalculationRequest`; snapshot `factor_kind`/`customer_factor_id`; hash canonical form; verify() both kinds | Unit: hashes, verify; Integration: snapshot rows |
| P0 | `data/emissions_logs.py` | COMPLETE (V2.1) | Persist O1 customer-factor snapshots | MISSING (columns unused) | EXTEND: `save_snapshot` writes `factor_kind`, `customer_factor_id`; customer-factor path for `emissions_logs` | Integration: both snapshot kinds persist |
| P0 | `domain/entity.py` + `data/processing_entities.py` | N/A (absent) | ProcessingEntity domain + repo (V3M-1) | MISSING | NEW: ProcessingEntity dataclass; repo CRUD + lifecycle + staff lookup | Unit + Integration |
| P0 | `api/admin_entities.py` + contracts | N/A (absent) | Entity admin API + lifecycle (ADR-V3-001 Q6) | MISSING | NEW routes: entity CRUD, activate/suspend/terminate, staff roster; CarbonTally-internal | API contract tests |
| P0 | `backend/auth.py` + `api/dependencies.py` + `api/middleware.py` | COMPLETE (V2.1) | Entity-scoped auth/RBAC (ADR-V3-010) | MISSING | EXTEND: `AuthUser.entity_id`; resolve staff entity; `require_entity_member`; request entity context | Unit: auth resolution; denial tests |
| P0 | `domain/issue.py` + `data/issues.py` + `api/issues.py` | N/A (absent) | Issue domain/repo/service/API (V3M-5) | MISSING | NEW: Issue dataclass + transition table; repo; service (transition authority, SLA); routes (org storey + entity storey) | Unit: transitions; Integration: lifecycle |
| P1 | NEW `services/work_items.py` (WorkItem) | N/A (absent) | WorkItem over `manual_review_queue`; logical queues (ADR-V3-003/011) | MISSING | NEW service: list queue views, assign/reassign/complete/return; writes `entity_id`; append-only `review_assignment_history` | Unit: state machine; Integration: entity queue |
| P1 | `engines/workflow.py` | COMPLETE (V2.1) | Batch→entity allocation; entity-scoped pipeline | MISSING | EXTEND: allocation step writes `upload_batches.entity_id`/`manual_review_queue.entity_id`; entity context in runs | Unit + Integration (500-doc scenario) |
| P1 | NEW `engines/auto_assignment.py` | N/A (absent) | Auto-assignment orchestration (ADR-V3-007) | MISSING | NEW: load-based suggestions, entity-scoped | Unit |
| P1 | `engines/validation.py` | COMPLETE (V2.1) | Customer-factor rules (A-ext) | MISSING | EXTEND: multiplier≥0, unit/scope/source, conflict flag; customer-factor snapshot verify | Unit; Integration |
| P1 | `engines/report_generation.py` + `data/reports.py` | COMPLETE (V2.1) | Customer-factor provenance section; export formats | MISSING | EXTEND: provenance `factor_source='CUSTOMER'`; CSV/Excel/JSON export adapters | Unit; Integration round-trip |
| P1 | `api/business.py` + `api/contracts.py` | COMPLETE (V2.1) | V3 extensions: calculate optional `customer_factor_id`; validate rules; report provenance | MISSING | EXTEND backward-compatibly | API contract tests |
| P1 | `data/audit.py` + `infra/audit_logger.py` | COMPLETE (V2.1) | Entity scope + actor-role in audit (ADR-V3-013) | MISSING | EXTEND: optional `entity_id`/actor-role on entries | Unit; Integration |
| P1 | NEW `api/process.py` + jobs | N/A (absent) | Async ingestion `/process/*`, `/jobs/*` (V3-001) | OPEN/DEFERRED (ADR-V3-004) | BUILD only after the producer decision; async job semantics | API contract + Integration |
| P1 | `api/reports.py` (v3) | N/A (absent) | `POST /api/v3/reports/{id}/export` | MISSING | NEW export endpoint (V3-019) | API contract tests |
| P2 | `backend/main.py` `api_version` label | LEGACY | Accuracy | INCORRECT | Change `/api/health` label to reflect reality (v2.1) — do not claim v3 | — |
| P2 | `tests/integration/conftest.py` | COMPLETE (V2.1) | V3 tables in truncate list | MISSING | EXTEND `_TRUNCATE_TABLES` with V3 tables when V3 repos write | Integration |
| P2 | Legacy `main.py` + `routes/**` | LEGACY | Consolidation | FROZEN | RETIRE LATER (spec §26.2); never add V3 code there | Regression |
| P2 | Orphaned `main copy.py` / `main copy 2.py` | LEGACY dead code | Cleanup | FROZEN | Remove in a later cleanup pass | — |
| P2 | D1/D2 provider plugin + ImportMappingEngine | PARTIAL (CLI importers) | Provider-independent architecture (V3M-4) | DECIDED, imports CLI | Build the v2.1 import engine/plugin surface when provider work is scoped | Engine + Integration |
| P2 | Alias provenance in snapshots | COMPLETE | V3-012 lineage tag | MISSING (optional) | Tag alias used during resolution | Unit |
---

## 15. IMPLEMENTATION SEQUENCE

Smallest safe sequence. No rewrite. Every step is independently shippable and
regression-safe (the 19 v2.1 contracts + error envelope stay green throughout).

### Step 1 — New domain objects (pure Python, zero risk)
- **Files:** NEW `domain/customer_factor.py`, NEW `domain/entity.py`,
  NEW `domain/issue.py`; EXTEND `domain/__init__.py`.
- **Changes:** frozen dataclasses + vocabularies + transition tables (no DB).
- **Dependencies:** none.
- **Tests:** `tests/unit/domain/test_customer_factor.py`,
  `test_entity.py`, `test_issue.py`.
- **Acceptance criteria:** pure-domain tests pass; no imports of data/api.

### Step 2 — New repositories
- **Files:** NEW `data/customer_factors.py`, NEW `data/processing_entities.py`,
  NEW `data/issues.py`; EXTEND `data/__init__.py`.
- **Changes:** persistence only (explicit column lists, service pool), mirroring
  `data/factor_aliases.py` conventions.
- **Dependencies:** Step 1.
- **Tests:** `tests/integration/test_customer_factors_repo.py`,
  `test_processing_entities_repo.py`, `test_issues_repo.py` against
  `carbontally_test`; extend `_TRUNCATE_TABLES`.
- **Acceptance criteria:** CRUD works; exactly-one-source/CHECK constraints
  surfaced; RLS-behaviour tests for `authenticated` role added.

### Step 3 — Entity-scoped auth
- **Files:** EXTEND `backend/auth.py`, `api/dependencies.py`,
  `api/middleware.py`.
- **Changes:** `AuthUser.entity_id`; staff row resolution; `require_entity_member`;
  request entity context.
- **Dependencies:** Step 2 (repo).
- **Tests:** `tests/unit/api/test_auth_entity.py` (resolution + denials).
- **Acceptance criteria:** an entity-staff token resolves to the entity; a
  non-member is denied; internal staff keep `entity_id=None`.

### Step 4 — Customer-factor API + engine integration
- **Files:** NEW `api/customer_factors.py`; EXTEND `api/router.py`,
  `api/contracts.py`, `api/business.py`, `engines/factor_matching.py`,
  `domain/matching.py`, `engines/calculation.py`, `domain/calculation.py`,
  `data/emissions_logs.py`, `engines/validation.py`, `engines/report_generation.py`.
- **Changes:** routes (CRUD/approve/deactivate — D-cf-3), matching candidate
  merge (D-cf-5), calculation factor union + O1 snapshot persistence +
  hash/verify, validation A-ext rules, report provenance section.
- **Dependencies:** Steps 1–3.
- **Tests:** unit (precedence, hashes, rules) + API contract + integration
  (snapshot rows of both kinds persist against `carbontally_test`).
- **Acceptance criteria:** a customer can manage factors; an approved factor
  wins over CarbonTally in matching; calculation persists an exactly-one-source
  customer-factor snapshot; report shows `factor_source='CUSTOMER'`; all 19
  v2.1 routes unchanged.

### Step 5 — Entity admin + work-item service
- **Files:** NEW `api/admin_entities.py`, NEW `services/work_items.py`;
  EXTEND `api/router.py`, `api/contracts.py`.
- **Changes:** entity CRUD/lifecycle (CarbonTally-internal); WorkItem service
  over `manual_review_queue` with entity_id writes and logical queues.
- **Dependencies:** Step 3.
- **Tests:** unit state machine + API contract + integration (entity-scoped
  queue reads; attribution preserved on reassign).
- **Acceptance criteria:** entity rows created/suspended via admin API; work
  items can be assigned to an entity and completed; queue views filter by
  entity.

### Step 6 — Issue service + workflow hooks
- **Files:** NEW `api/issues.py`, NEW `services/issues.py`; EXTEND
  `engines/workflow.py`, `engines/validation.py`.
- **Changes:** issue routes (org storey + entity storey), transition service,
  SLA computation, workflow/validation failure hooks raising issues.
- **Dependencies:** Steps 3, 5.
- **Tests:** unit transitions + integration lifecycle + API contract.
- **Acceptance criteria:** issues raised from validation failures; lifecycle
  transitions enforce authority; customer-facing vs entity-scoped isolation
  holds.

### Step 7 — Workflow allocation + auto-assignment
- **Files:** EXTEND `engines/workflow.py`; NEW `engines/auto_assignment.py`;
  EXTEND `api/dependencies.py` (wiring).
- **Changes:** batch→entity allocation writes `entity_id`; auto-assignment
  orchestration (ADR-V3-007).
- **Dependencies:** Steps 5, 6.
- **Tests:** unit + integration (500-doc multi-entity scenario).
- **Acceptance criteria:** a batch can be split across entities; allocation
  persists; auto-assignment respects entity boundaries and workload.

### Step 8 — Report export + audit entity scope
- **Files:** EXTEND `engines/report_generation.py`, `data/reports.py`,
  `api/reports.py`, `data/audit.py`, `infra/audit_logger.py`.
- **Changes:** export adapters (CSV/Excel/JSON), optional `entity_id`/actor-role
  on audit entries.
- **Dependencies:** Step 4.
- **Tests:** unit + API contract + integration.
- **Acceptance criteria:** report export returns all three formats; audit
  entries can be scoped to an entity.

### Step 9 — Async ingestion (only after the ADR-V3-004 producer decision)
- **Files:** NEW `api/process.py` + job status surface.
- **Changes:** `/process/*` + `/jobs/*` (V3-001) with async job semantics.
- **Dependencies:** Steps 4–8 (pipeline complete).
- **Tests:** API contract + integration.
- **Acceptance criteria:** CSV/Excel/PDF document ingestion runs as a job;
  status is pollable; results flow into the canonical pipeline.

### Step 10 — P2 cleanup (independent)
- Correct the `main.py` health label; extend test conftest; remove orphaned
  copies; retire legacy surface later (spec §26.2); provider-plugin/
  ImportMappingEngine when provider work is scoped.

---

## 16. WHAT IS ALREADY COMPLETE

These must NOT be rewritten:

1. **The full V2.1 domain layer** (`domain/` 11 modules) — reused unchanged.
2. **The full V2.1 repository layer** (`data/` 9 repos) — reused unchanged;
   only `emissions_logs.py` and `audit.py` get additive extensions.
3. **The full V2.1 engine stack** — matching, calculation, extraction,
   ai_extraction, validation, benchmarking, report_generation, workflow. Only
   matching/calculation/validation/report_generation get additive extensions.
4. **The v2.1 API** (`api/router.py`, `business.py`, `admin_*.py`,
   `contracts.py`, `dependencies.py`, `middleware.py`) — the 19 routes and the
   error envelope are the regression guard; V3 routes are added, nothing is
   changed or removed.
5. **`backend/auth.py`** JWT/RBAC surface — extended only with entity scope.
6. **`infra/`** — event bus, audit logger, search index, llm client, supabase
   service pool. Unchanged (audit logger extended additively).
7. **`core/`** — exceptions, logging, types. Unchanged.
8. **The V3 database migrations and their verification tests** — V3M-1,
   V3M-2, V3M-3, V3M-5, V3M-6 and `test_v3m1_v3m2_processing_entities.py`,
   `test_v3m3_customer_factors.py`, `test_v3m5_issues.py` are complete and are
   the schema guarantee; they remain the DB layer's tests.
9. **The `src/providers/` + `src/commands/` factor baseline** — 7,049 factors
   and the CLI importers are the verified data baseline (V3M-4 architecture
   DECIDED; imports remain separate tasks).
10. **The architectural documents** — V3 Architecture Specification, ADR
    Register, Impact Assessment, Platform Processing Master, DB Schema V3M2 —
    remain authoritative; no re-derivation.

---

## 17. WHAT CAN WAIT

Non-blocking cleanup/refactoring (do not do in the P0/P1 sequence):

1. **Legacy surface retirement** (`backend/main.py` + `routes/**`) — spec §26.2
   explicitly defers this. The legacy surface remains the pre-existing deployed
   app and stays frozen.
2. **CRUD-to-Supabase-direct migration** (§12.2) — moving org CRUD off the
   legacy FastAPI routes; a frontend/API coordination effort, not a backend V3
   prerequisite.
3. **Provider plugin architecture + ImportMappingEngine (D1/D2)** — required
   only when a new provider import is scoped (EPA/ADEME/IPCC deferred).
4. **API versioning decision (H6)** — `/api/v2` vs `/api/v3` namespace choice;
   additive routes work under either.
5. **Async ingestion `/process/*` + producer wiring (ADR-V3-004)** — OPEN/
   DEFERRED; the pipeline already supports the processing; only the producer
   decision and job surface are pending.
6. **Entity RBAC role names/matrix** (Manager/Supervisor/Worker/Validator) —
   final names deferred (spec §8.3); the generic `is_entity_member` check is
   sufficient for P0.
7. **Consultant membership investigation (ADR-V3-010 INVESTIGATE)** — whether
   consultants are also `organization_members`; affects nothing in the P0 set.
8. **Legacy permissive queue-policy hardening (ADR-V3-010 INVESTIGATE)** — DB/
   RLS concern, deferred.
9. **Queue retirement (ADR-V3-016)** — dormant `processing_queue` family;
   deferred.
10. **PDF/HTML report rendering, regulatory report formats, external
    benchmarking, forecasting** — explicitly DEFERRED by the V3 spec.
11. **Alias provenance tagging (P2)** — optional lineage enrichment.

---

## 18. FINAL V3 BACKEND READINESS

### 18.1 Completion estimate

Measured against the full "Backend V3" surface (V2.1 reuse baseline + the
genuinely new V3 surfaces), where the V2.1 baseline counts as complete because
the V3 architecture explicitly reuses it unchanged:

- **Complete: ≈ 60%** — V2.1 domain/repos/engines/infra/API (fully reusable,
  verified), CO2/CO2e provenance, the 19-route API, the V3 database migrations,
  and the three V3 DB-verification test suites.
- **Partial: ≈ 10%** — the V2.1 API is structurally V3-ready (thin router,
  DI, error envelope); matching/calculation/validation/report engines are
  extension points already; the V3 tests cover the DB storey; `main.py` health
  label misreports version.
- **Missing: ≈ 30%** — the entire V3-specific backend: customer-factor domain/
  repo/API/engines (P0), processing-entity domain/repo/API/auth (P0), issues
  service/API (P0), work-item service + allocation + auto-assignment (P1),
  report export + audit entity scope (P1), async ingestion (P1, gated).

### 18.2 P0 blockers (blocking V3)

1. Customer-factor backend (domain, repo, API, matching precedence D-cf-5,
   calculation + O1 snapshot provenance, validation rules).
2. Processing-entity backend (domain, repo, admin API, lifecycle).
3. Entity-scoped auth/RBAC (`AuthUser.entity_id`, `require_entity_member`).
4. Issue backend (domain, repo, service, API).
5. Wiring new repos into the composition root (`RepositoryBundle`).

Until these exist, the V3 database's new tables (`customer_factors`,
`processing_entities`, `issues`) are unreachable by any application code, and
`entity_id`/`factor_kind`/`customer_factor_id` columns are write-orphaned.

### 18.3 P1 work (required production functionality)

6. WorkItem service + entity allocation in workflow.
7. Auto-assignment engine (orchestration).
8. Customer-factor validation rules + snapshot verify.
9. Report provenance + export adapters; audit entity scope.
10. Async ingestion `/process/*` + jobs (after ADR-V3-004 producer decision).

### 18.4 P2 work (cleanup/optimization)

11. Legacy surface retirement; CRUD-to-Supabase-direct migration.
12. D1/D2 provider plugin + ImportMappingEngine when provider work is scoped.
13. `main.py` health label correction; orphaned-copy removal; test-conftest
    V3 tables; alias provenance tagging; API versioning decision.

---

## Appendix A — Evidence

| # | Evidence | Used for |
|---|---|---|
| E1 | `backend/api/*` (router, business, contracts, dependencies, middleware, admin_*) | v2.1 API structure; 19 routes; composition root |
| E2 | `backend/engines/*` (matching, matching_stages, calculation, extraction, ai_extraction, validation, benchmarking, report_generation, workflow) | Engine status and V3 extension points |
| E3 | `backend/domain/__init__.py` + modules | Full domain catalogue — no entity/customer-factor/issue objects |
| E4 | `backend/data/__init__.py` + `data/emissions_logs.py` | Repository catalogue; `save_snapshot` O1 gap |
| E5 | `backend/auth.py`, `backend/main.py`, `backend/main_v2.py`, `routes/__init__.py` | Entry points; legacy surface; auth surface |
| E6 | `supabase/migrations/20260810000000_v3m1*` … `20260810050000_v3m6*` | V3 DB ground truth |
| E7 | `backend/tests/integration/test_v3m1_v3m2_processing_entities.py`, `test_v3m3_customer_factors.py`, `test_v3m5_issues.py` | V3 DB test completeness |
| E8 | `tests/integration/conftest.py`, `tests/unit/api/conftest.py`, `tests/unit/api/fakes.py` | Test infra; truncate list gap |
| E9 | `docs/architecture/CarbonTally_V3_Architecture_Specification_v1.0.md` (§7–§27, §32–§33) | V3 requirements, module mapping, boundary |
| E10 | `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` | ADR statuses (V3-001/002/003/004/005/007/009/010/012/014/015) |
| E11 | `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md`, `CarbonTally-v2.1-Traceability-Matrix-v1.0.md` | V2.1 baseline, deviations D1/D2/D14, reuse verdicts |
| E12 | `src/commands/import_defra.py`, `src/commands/import_seai.py` | Provider import baseline (CLI, D1/D2) |
| E13 | `backend/.pytest_cache/v/cache/lastfailed`, `_phase10_selfcheck.py`, Phase 9D/10 docs | Test-state evidence |

---

**END OF AUDIT — READ-ONLY. No code, database, migration, RLS, Storage, API,
contract, test or data was modified. Factor baseline unchanged (DEFRA 7,029 ·
SEAI 20 · TOTAL 7,049).**






















