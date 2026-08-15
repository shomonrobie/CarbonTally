---
Document Type: Migration Report
Project: CarbonTally
Architecture Decision: Backend V2.1 → V3
Version: 1.0
Status: COMPLETE (implementation) — test execution limited by environment
Created: 2026-08-14
Author: Cline
Related ADR: ADR-V3-001, ADR-V3-002, ADR-V3-009, ADR-V3-014
---

# CarbonTally V3 — Backend V2.1 → V3 Migration Report v1.0

**Principle honoured:** V3 is an evolutionary upgrade of V2.1 — working V2.1
functionality is KEPT, engines are EXTENDED where V3 requires it, repositories
are REPOINTED, and NEW V3 components are added only where the settled
architecture requires them. Nothing working was replaced because of a version
number.

**Decision rule honoured:** ADR-register items that are DECIDED were
implemented. PROVISIONALLY DECIDED / DEFERRED / OPEN items were preserved as-is
and their boundaries documented — nothing was invented.

**Database:** untouched. The V3 database (V3M-1/2/3/5/6) is the source of
truth; no migration, schema, RLS or factor data was modified (factor baseline
unchanged: DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

---

## 1. V2.1 Components Migrated (KEEP / EXTEND)

| V2.1 component | Action | What happened |
|---|---|---|
| Domain layer (11 modules) | **KEEP** | `audit`, `benchmarking`, `document`, `factor`, `organization`, `provider`, `report`, `validation`, `workflow` unchanged |
| `domain/calculation.py` | **EXTEND** | `CalculationSnapshot` gains O1 provenance (`factor_kind`, `customer_factor_id`; `factor_id` now Optional); `CalculationResult` carries `customer_factor`; content-hash canonical form includes the factor source |
| `domain/matching.py` | **EXTEND** | `MatchResult` gains `factor_kind` + `customer_factor_id` (D-cf-5) |
| Repositories (8 of 9) | **KEEP** | unchanged |
| `data/emissions_logs.py` | **EXTEND** | `save_snapshot` writes O1 provenance columns; `create` accepts a NULL `emission_factor_id` (customer-factor path) |
| Engines: extraction, ai_extraction, benchmarking | **KEEP** | reused unchanged |
| `engines/workflow.py` | **KEEP** | unchanged (dpq producer/consumer is OPEN/DEFERRED — ADR-V3-004) |
| `engines/factor_matching.py` | **EXTEND** | D-cf-5 customer-factor candidate pre-check (approved-first) before the CarbonTally pipeline |
| `engines/calculation.py` | **EXTEND** | factor-union request, O1 snapshot persistence, customer-factor compute path with identical precision |
| `engines/validation.py` | **EXTEND** | additive `validate_customer_factor` rules (A-ext) |
| `engines/report_generation.py` | **EXTEND** | provenance section tags `CUSTOMER` source for customer-factor logs |
| v2.1 API routers | **KEEP** | all 19 routes + error envelope unchanged |
| `api/business.py` `/calculate` | **EXTEND** | optional `customer_factor_id` (mutually exclusive with `factor_id`), org-isolation check, active-only |
| `api/contracts.py` | **EXTEND** | match/calculation/snapshot contracts carry O1 provenance; V3 contracts added |
| `api/dependencies.py` | **EXTEND** | `RepositoryBundle` + re-exports for the 3 new repos + `require_org_admin`/`require_org_member`/`require_entity_member`; matching engine wired with customer-factor lookup |
| `api/router.py` | **EXTEND** | 3 new V3 routers registered on the same `create_app()` factory |
| `backend/auth.py` | **EXTEND** | `AuthUser.entity_id`; `require_entity_member` guard (V3 ADR-V3-001) |
| Infra (`infra/*`) | **KEEP** | unchanged |
| Legacy `main.py` + `routes/**` | **DEPRECATE LATER** | frozen, untouched |

## 2. V3 Components Activated

| V3 component | ADR | File(s) | Notes |
|---|---|---|---|
| Processing Entity domain | ADR-V3-001 (DECIDED) | `domain/entity.py` | lifecycle vocabulary + transition table (V3M-1 CHECK) |
| Processing Entity repository | ADR-V3-001 | `data/processing_entities.py` | CRUD + lifecycle; hard-delete refused |
| Processing Entity admin API | ADR-V3-001 | `api/admin_entities.py` | CarbonTally-internal (`require_admin`); lifecycle transition validation; audit via `AuditRepository` |
| Customer Factor domain | ADR-V3-002 (DECIDED) | `domain/customer_factor.py` | DRAFT→ACTIVE→INACTIVE/ARCHIVED (D-cf-3) |
| Customer Factor repository | ADR-V3-002 | `data/customer_factors.py` | org-scoped CRUD; ACTIVE-only candidate reads (D-cf-5) |
| Customer Factor API | ADR-V3-002 | `api/customer_factors.py` | create-draft, edit-draft, approve (org-admin, no self-approval), deactivate |
| Issue domain | ADR-V3-009 (DECIDED) | `domain/issue.py` | status transition table (V3M-5 CHECK) |
| Issue repository | ADR-V3-009 | `data/issues.py` | org/entity/internal scoped queries; hard-delete refused |
| Issue API + service | ADR-V3-009 | `api/issues.py` | customer-facing surface (`entity_id IS NULL`), entity-scoped list (`require_entity_member`), CarbonTally triage, transition authority + reopen |
| Snapshot provenance | ADR-V3-014 (DECIDED, O1) | `domain/calculation.py`, `engines/calculation.py`, `data/emissions_logs.py` | `factor_kind` + `customer_factor_id` (exactly-one-source) |
| Entity-scoped auth | ADR-V3-001 | `auth.py` | `AuthUser.entity_id`, `require_entity_member` |

## 3. Existing Engines Reused (no duplication)

`FactorMatchingEngine` (extended in place — no second engine),
`CalculationEngine` (extended in place — no second engine), `ValidationEngine`
(extended in place), `ReportGenerationEngine` (extended in place),
`DocumentExtractionEngine`, `AIExtractionEngine`, `BenchmarkingEngine`,
`WorkflowOrchestrator` — all reused. **No parallel V2.1/V3 engine was created.**

## 4. New Backend Components Created

| Component | Location |
|---|---|
| `ProcessingEntity` domain | `backend/domain/entity.py` |
| `CustomerFactor` domain | `backend/domain/customer_factor.py` |
| `Issue` domain | `backend/domain/issue.py` |
| `ProcessingEntitiesRepository` | `backend/data/processing_entities.py` |
| `CustomerFactorsRepository` | `backend/data/customer_factors.py` |
| `IssuesRepository` | `backend/data/issues.py` |
| `api/admin_entities.py` router | `/api/v3/admin/entities` |
| `api/customer_factors.py` router | `/api/v3/customer-factors` |
| `api/issues.py` router | `/api/v3/issues` |
| V3 contracts | `api/contracts.py` (entities, customer factors, issues, O1 provenance) |
| `require_entity_member` | `backend/auth.py` |

## 5. APIs Migrated / Added

- **Added:** `GET/POST /api/v3/admin/entities`, `GET/PUT /api/v3/admin/entities/{id}`;
  `GET/POST /api/v3/customer-factors`, `GET/PUT /api/v3/customer-factors/{id}`,
  `POST .../approve`, `POST .../deactivate`;
  `GET/POST /api/v3/issues`, `GET/PUT /api/v3/issues/{id}`,
  `GET /api/v3/issues/admin/entity/{entity_id}`, `GET /api/v3/issues/admin/open`.
- **Extended (backward-compatible):** `POST /api/v2/factor-match` (D-cf-5
  candidate merge; response carries `factor_kind`/`customer_factor_id`);
  `POST /api/v2/calculate` (optional `customer_factor_id`); snapshot contract
  carries O1 provenance.
- **NOT added (deferred):** `/process/*`, `/jobs/*` (ADR-V3-004 OPEN), Work Item
  service (ADR-V3-003 PROVISIONALLY DECIDED), auto-assignment (ADR-V3-007),
  SLA (ADR-V3-006).

## 6. Tests Added / Updated

| Test file | Type | Covers |
|---|---|---|
| `tests/unit/domain/test_entity.py` | UNIT | ProcessingEntity lifecycle/vocabulary |
| `tests/unit/domain/test_customer_factor.py` | UNIT | CustomerFactor lifecycle/vocabulary |
| `tests/unit/domain/test_issue.py` | UNIT | Issue lifecycle/vocabulary |
| `tests/unit/engines/test_customer_factor_integration.py` | UNIT | D-cf-5 precedence, draft exclusion, ambiguity, O1 snapshot provenance, exactly-one-source |
| `tests/unit/api/test_v3_entities.py` | API CONTRACT | entity admin CRUD + lifecycle transitions |
| `tests/unit/api/test_v3_customer_factors.py` | API CONTRACT | draft CRUD, approve (incl. no self-approval), deactivate |
| `tests/unit/api/test_v3_issues.py` | API CONTRACT | create/list/transition/reopen, entity isolation, admin triage |
| `tests/integration/test_v3_repositories.py` | INTEGRATION | V3 repos CRUD/lifecycle over `carbontally_test` |
| `tests/unit/api/fakes.py` | UPDATED | `MemoryCustomerFactors`, `MemoryEntities`, `MemoryIssues`; extended `RepositoryBundle` |
| `tests/unit/engines/test_calculation.py`, `src/providers/seai/tests/test_defra_regression.py` | UPDATED | sink protocol extended (O1 kwargs) |
| `tests/integration/conftest.py` | UPDATED | V3 tables in truncate list |

## 7. Tests Passing

**Environment limitation:** this session's shell/process execution is
unavailable, so the pytest suites could **not be executed here**. Verification
was by careful static review against the existing conventions (imports,
protocols, dataclass ordering, contract models). The suites must be run where
the environment permits:
`python -m pytest tests/unit/domain tests/unit/engines tests/unit/api` and,
where the local `carbontally_test` database is reachable,
`python -m pytest tests/integration/test_v3_repositories.py`.

Existing V2.1 tests were **not discarded**; they were updated only where the
extended protocol demanded it (sink signatures) and otherwise preserved.

## 8. Known Remaining Gaps

1. Customer-factor rules are validated at creation/edit via the additive
   `validate_customer_factor` surface; wiring it into an API validation step
   and conflict-with-reference detection is a follow-up.
2. The V3 repositories are integration-tested by file but not executed in this
   environment.
3. `is_entity_member` (V3M-6) is exercised via `AuthUser.entity_id` +
   `require_entity_member`; a direct RLS-behaviour test with an
   `authenticated` role is a follow-up.
4. Customer-factor calculations store `emission_factor_id = NULL` on the
   emissions log (documented O1 decision) — confirm downstream consumers
   handle the null.

## 9. Deferred Architecture Boundaries (not invented)

| Boundary | ADR status | State |
|---|---|---|
| dpq producer/consumer + `/process` + `/jobs` | ADR-V3-004 OPEN/DEFERRED | preserved; no producer/consumer/endpoints added |
| Work Item / logical queue model | ADR-V3-003 PROVISIONALLY DECIDED | `manual_review_queue` legacy surface preserved; no new queue |
| Auto-assignment, SLA, assignment model | ADR-V3-007/006/005 PROVISIONALLY DECIDED | not built |
| Audit entity scope | ADR-V3-013 PROVISIONALLY DECIDED | new services audit via generic `entity_type`/`entity_id` |
| Queue retirement | ADR-V3-016 DEFERRED | not touched |
| Provider plugin architecture | ADR-V3-015 DECIDED (arch) | CLI importers preserved; imports are separate tasks |

## 10. Recommended Next Implementation Phase

1. **Execute the test suites** in an environment with Python + the local
   `carbontally_test` database; fix any surfaced failures.
2. **Wire `validate_customer_factor`** into the customer-factor create/edit
   endpoints (validation-before-persist) and add reference-conflict flags.
3. **Integration + RLS-behaviour tests** for entity-scoped auth and
   customer-factor snapshot persistence (`authenticated` role).
4. **Decide ADR-V3-004** (dpq producer/consumer) and then wire the document
   pipeline (WorkflowOrchestrator) to an ingestion route — per the sequencing
   in `docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md` §15.
5. Continue the established phases: customer review/output adapters (Phase 6)
   and full integration verification (Phase 8).

---

**Scope discipline:** no application code, database, migration, RLS, Storage,
tests-other-than-those-above, or ADR decisions were modified outside this
migration. Nothing was committed or pushed. Factor baseline unchanged
(DEFRA 7,029 · SEAI 20 · TOTAL 7,049).


