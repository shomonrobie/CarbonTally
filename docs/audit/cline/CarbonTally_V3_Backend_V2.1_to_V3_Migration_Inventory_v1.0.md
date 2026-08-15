---
Document Type: Migration Inventory
Project: CarbonTally
Architecture Decision: Backend V2.1 → V3
Version: 1.0
Status: FINAL
Audit Mode: READ-ONLY INVENTORY (no code changed during this step)
Created: 2026-08-14
Author: Cline
Related ADR: ADR-V3-001, ADR-V3-002, ADR-V3-003, ADR-V3-004, ADR-V3-009, ADR-V3-014
---

# CarbonTally V3 — Backend V2.1 → V3 Migration Inventory v1.0

**Purpose:** classify every existing V2.1 backend component against its V3
target before any code is changed. This is the Phase 1 inventory step of the
evolutionary upgrade. No code was modified to produce this document.

**Classification vocabulary:**
1. KEEP — reuse unchanged (V3 architecture reuses it)
2. EXTEND — reuse and add V3 capability
3. REPOINT — keep the code, wire it to a different V3 surface
4. REFACTOR — restructure in place (no behaviour change)
5. NEW V3 COMPONENT — build against the settled architecture
6. DEPRECATE LATER — leave working, remove in a controlled later cleanup
7. NO CHANGE — nothing to do

**Decision status rule applied:** ADR-register items that are DECIDED are
implementable; items that are PROVISIONALLY DECIDED / DEFERRED / OPEN are
preserved as-is and the boundary is documented, never invented.

---

## 1. Backend Packages Overview

| Package | Location | Role | V3 Action |
|---|---|---|---|
| API layer | `backend/api/` | v2.1 FastAPI surface (19 routes), composition root, contracts | **EXTEND** — add V3 routers, contracts, repo wiring |
| Auth | `backend/auth.py` | JWT + Supabase roles/permissions; `AuthUser` | **EXTEND** — entity scope (`entity_id`, `require_entity_member`) |
| Core | `backend/core/` | exceptions, logging, types | **NO CHANGE** |
| Domain | `backend/domain/` | 11 pure frozen-dataclass modules | **EXTEND** — add `entity.py`, `customer_factor.py`, `issue.py`; extend `calculation.py`, `matching.py` |
| Data | `backend/data/` | 9 repositories over service-role asyncpg pool | **EXTEND** — add 3 repositories; extend `emissions_logs.py` |
| Engines | `backend/engines/` | 8 business engines | **EXTEND** — matching, calculation, validation, report_generation; KEEP extraction, ai_extraction, benchmarking, workflow |
| Infra | `backend/infra/` | supabase pool, event bus, audit logger, search index, llm client | **NO CHANGE** |
| Legacy app | `backend/main.py` + `backend/routes/**` | Legacy monolith (~40 route modules, ~400 endpoints) | **DEPRECATE LATER** — frozen; do not add V3 code |
| v2.1 entry | `backend/main_v2.py` | `create_app()` → V2.1 API | **EXTEND** — V3 routes registered on the same factory |
## 2. Domain Layer

| V2.1 Component | File | Current Role | V3 Target | Action |
|---|---|---|---|---|
| `AuditEntry`, `AuditQuery`, `AuditTrail` | `domain/audit.py` | Audit aggregate | Reused unchanged | KEEP |
| Benchmarking objects | `domain/benchmarking.py` | Phase 9B contract | Reused unchanged | KEEP |
| `CalculationSnapshot`, `EmissionLog`, `CalculationResult`, `VerificationResult` | `domain/calculation.py` | Calculation contracts | Customer-factor provenance (O1) | **EXTEND** |
| Document/extraction objects | `domain/document.py` | Extraction contracts | Reused unchanged | KEEP |
| `EmissionFactor`, `gas_coverage`, `FactorSet` | `domain/factor.py` | Factor model | Reused unchanged | KEEP |
| Matching objects | `domain/matching.py` | Matching pipeline contracts | Customer-factor candidates (D-cf-5) | **EXTEND** |
| Organization objects | `domain/organization.py` | Org aggregate | Reused unchanged | KEEP |
| Provider objects | `domain/provider.py` | Import contracts | Reused unchanged | KEEP |
| Report objects | `domain/report.py` | Report contracts | Reused unchanged | KEEP |
| Validation objects | `domain/validation.py` | Phase 9A contract | Customer-factor rules (additive) | **EXTEND** (engine-level) |
| Workflow events/definition | `domain/workflow.py` | Event + pipeline definitions | Reused unchanged (dpq producer OPEN) | KEEP |
| — | NEW `domain/entity.py` | — | `ProcessingEntity` (ADR-V3-001 DECIDED) | **NEW V3 COMPONENT** |
| — | NEW `domain/customer_factor.py` | — | `CustomerFactor` (ADR-V3-002 DECIDED) | **NEW V3 COMPONENT** |
| — | NEW `domain/issue.py` | — | `Issue` (ADR-V3-009 DECIDED) | **NEW V3 COMPONENT** |

## 3. Repository (Data) Layer

| V2.1 Component | File | Current Role | V3 Target | Action |
|---|---|---|---|---|
| `AuditRepository` | `data/audit.py` | Audit write/query | Reused unchanged | KEEP |
| `DocumentsRepository` | `data/documents.py` | `customer_documents` persistence | Reused unchanged | KEEP |
| `EmissionFactorsRepository` | `data/emission_factors.py` | Factor reads + index load | Reused unchanged | KEEP |
| `EmissionsLogsRepository` | `data/emissions_logs.py` | Logs + snapshot persistence | O1 snapshot provenance | **EXTEND** |
| `EventsRepository` | `data/events.py` | Domain events | Reused unchanged | KEEP |
| `FactorAliasesRepository` | `data/factor_aliases.py` | Alias lookup | Reused unchanged | KEEP |
| `ImportsRepository` | `data/imports.py` | Batch lifecycle | Reused unchanged | KEEP |
| `OrganizationsRepository` | `data/organizations.py` | Org aggregate reads | Reused unchanged | KEEP |
| `ReportsRepository` | `data/reports.py` | Report lifecycle | Reused unchanged | KEEP |
| — | NEW `data/processing_entities.py` | — | Entity CRUD/lifecycle (V3M-1) | **NEW V3 COMPONENT** |
| — | NEW `data/customer_factors.py` | — | Customer-factor CRUD (V3M-3) | **NEW V3 COMPONENT** |
| — | NEW `data/issues.py` | — | Issue CRUD (V3M-5) | **NEW V3 COMPONENT** |

## 4. Engine Layer

| V2.1 Component | File | Current Role | V3 Target | Action |
|---|---|---|---|---|
| `FactorMatchingEngine` + 6 stages | `engines/factor_matching.py`, `engines/matching_stages.py` | Matching pipeline over search index | Approved-customer-first candidates (D-cf-5) | **EXTEND** |
| `CalculationEngine` | `engines/calculation.py` | Reproducible calculation + snapshots | Factor union + O1 snapshot provenance | **EXTEND** |
| `DocumentExtractionEngine` | `engines/extraction.py` | Text → structured extraction | Reused unchanged (dpq wiring OPEN) | KEEP |
| `AIExtractionEngine` | `engines/ai_extraction.py` | LLM field extraction | Reused unchanged (dpq wiring OPEN) | KEEP |
| `WorkflowOrchestrator` | `engines/workflow.py` | Document pipeline orchestration | Reused unchanged (producer OPEN) | KEEP |
| `ValidationEngine` | `engines/validation.py` | A1–A9 data quality | Customer-factor rules (additive) | **EXTEND** |
| `BenchmarkingEngine` | `engines/benchmarking.py` | Internal benchmarking | Reused unchanged | KEEP |
| `ReportGenerationEngine` | `engines/report_generation.py` | 12-section structured report | Customer-factor provenance | **EXTEND** |
| — | NEW `engines/auto_assignment.py` | — | ADR-V3-007 — **PROVISIONALLY DECIDED** | **NOT BUILT** (deferred) |
## 5. API Layer

| V2.1 Component | File | Current Role | V3 Target | Action |
|---|---|---|---|---|
| Router/app factory | `api/router.py` | 19 v2.1 routes + error envelope | Register V3 routers | **EXTEND** |
| Business endpoints | `api/business.py` | 5 business endpoints | Customer-factor input (backward-compatible) | **EXTEND** |
| Admin imports | `api/admin_imports.py` | Batch reads | Reused unchanged | KEEP |
| Admin providers | `api/admin_providers.py` | Provider catalogue | Reused unchanged | KEEP |
| Admin audit | `api/admin_audit.py` | Audit search | Reused unchanged | KEEP |
| Admin aliases | `api/admin_aliases.py` | Alias CRUD | Reused unchanged | KEEP |
| Contracts | `api/contracts.py` | JSON models + serialisers | V3 contracts | **EXTEND** |
| Composition root | `api/dependencies.py` | RepositoryBundle + engine factories | Wire V3 repos/services | **EXTEND** |
| Middleware | `api/middleware.py` | Request context | Reused unchanged | KEEP |
| — | NEW `api/admin_entities.py` | — | Processing-entity admin API (ADR-V3-001 DECIDED) | **NEW V3 COMPONENT** |
| — | NEW `api/customer_factors.py` | — | Customer-factor API (ADR-V3-002 DECIDED) | **NEW V3 COMPONENT** |
| — | NEW `api/issues.py` | — | Issue API (ADR-V3-009 DECIDED) | **NEW V3 COMPONENT** |
| — | NEW `api/process.py` + jobs | — | Async ingestion (ADR-V3-004 OPEN) | **NOT BUILT** (deferred) |

## 6. Authentication / Authorization

| V2.1 Component | File | Current Role | V3 Target | Action |
|---|---|---|---|---|
| `AuthUser` | `auth.py` | JWT user + org/staff context | Add `entity_id` | **EXTEND** |
| `get_current_user` | `auth.py` | Token → AuthUser | Resolve entity staff | **EXTEND** |
| `require_admin` / `require_staff` / `require_role` / `require_permission` | `auth.py` | RBAC guards | Reused unchanged | KEEP |
| `require_org_member` / `require_org_admin` / `require_org_access` | `auth.py` | Org isolation | Reused unchanged | KEEP |
| — | NEW `require_entity_member` | — | Entity staff check (ADR-V3-001) | **NEW V3 COMPONENT** |

## 7. Infrastructure

| V2.1 Component | File | Current Role | V3 Target | Action |
|---|---|---|---|---|
| Supabase service pool | `infra/supabase.py` | asyncpg service-role pool | Reused unchanged | KEEP |
| EventBus | `infra/event_bus.py` | In-process pub/sub | Reused unchanged | KEEP |
| AuditLogger | `infra/audit_logger.py` | Engine side-effect audit | Reused unchanged | KEEP |
| FactorSearchIndex | `infra/search_index.py` | In-memory factor index | Reused unchanged | KEEP |
| LLMClient | `infra/llm_client.py` | AI extraction transport | Reused unchanged | KEEP |

## 8. Tests

| V2.1 Component | Location | Current Role | V3 Target | Action |
|---|---|---|---|---|
| Domain unit tests | `tests/unit/domain/` | V2.1 domain | Keep; add entity/customer_factor/issue | **EXTEND** |
| Engine unit tests | `tests/unit/engines/` | V2.1 engines | Keep; add customer-factor matching/calculation | **EXTEND** |
| API contract tests | `tests/unit/api/` | 19 routes over in-memory fakes | Add V3 routes over extended fakes | **EXTEND** |
| Repository integration | `tests/integration/` | V2.1 repos over `carbontally_test` | Add V3 repo integration | **EXTEND** |
## 9. Deferred / Preserved Boundaries (do not invent)

| Area | ADR status | Repository state | Action |
|---|---|---|---|
| dpq producer/consumer + `/process/*` + `/jobs/*` | ADR-V3-004 OPEN/DEFERRED | no producer, no consumer, no endpoints | **Preserve existing behaviour; leave isolated** |
| Work Item / logical queue model | ADR-V3-003 PROVISIONALLY DECIDED | `manual_review_queue` active legacy surface | **Preserve; no new queue system** |
| Auto-assignment | ADR-V3-007 PROVISIONALLY DECIDED | absent | **Not built** |
| SLA/priority/escalation | ADR-V3-006 PROVISIONALLY DECIDED | legacy surfaces | **Not built** |
| Assignment/reassignment model | ADR-V3-005 PROVISIONALLY DECIDED | legacy `review_assignment_history` | **Preserve legacy** |
| Audit entity scope | ADR-V3-013 PROVISIONALLY DECIDED | generic `audit_trail` columns | **Preserve; use generic entity_type/entity_id** |
| Queue retirement | ADR-V3-016 DEFERRED | dormant `processing_queue` family | **Not touched** |
| Provider plugin architecture | ADR-V3-015 DECIDED (arch) | CLI importers (D1/D2) | **Preserve; imports are separate tasks** |

## 10. Summary of Actions

| Action | Count | Items |
|---|---:|---|
| KEEP | 24 | domain audit/benchmarking/document/factor/organization/provider/report/workflow; all 9 repos except emissions_logs; extraction/ai_extraction/workflow/benchmarking engines; all infra; admin imports/providers/audit/aliases; RBAC guards |
| EXTEND | 10 | domain/calculation, domain/matching, data/emissions_logs, engines/matching, engines/calculation, engines/validation, engines/report_generation, api/router, api/contracts, api/dependencies, api/business, auth.py |
| NEW V3 COMPONENT | 9 | domain/entity, domain/customer_factor, domain/issue, data/processing_entities, data/customer_factors, data/issues, api/admin_entities, api/customer_factors, api/issues |
| DEPRECATE LATER | 2 | legacy `main.py` + `routes/**`, orphaned copies |
| NOT BUILT (deferred) | 5 | dpq producer/consumer, `/process`/`/jobs`, WorkItem service, auto-assignment, SLA |

---

**End of Phase 1 inventory. No code was changed during this step.**



