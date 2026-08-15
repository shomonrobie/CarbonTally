---
Document Type: Implementation Record (Phases 1–8)
Project: CarbonTally
Architecture Decision: Backend V2.1 → V3
Version: 1.0
Status: COMPLETE (implementation)
Created: 2026-08-14
Author: Cline
Related ADR: ADR-V3-001, ADR-V3-002, ADR-V3-009, ADR-V3-014
---

# CarbonTally V3 — Backend V2.1 → V3 Migration Phase Records

Companion to `CarbonTally_V3_Backend_V2.1_to_V3_Migration_Inventory_v1.0.md`
(inventory) and `CarbonTally_V3_Backend_V2.1_to_V3_Migration_Report_v1.0.md`
(overall report). This record logs, per phase, what was migrated, preserved,
extended, repointed, and left deferred, and which tests prove the migration.

## Phase 1 — Backend Inventory (no code)

- Produced the full V2.1 component inventory with KEEP/EXTEND/REPOINT/REFACTOR/
  NEW/DEPRECATE-LATER classification.
- **Preserved:** every V2.1 component classification decision (documented in
  the inventory).
- **Deferred (not built):** dpq producer/consumer, `/process`/`/jobs`, Work
  Item service, auto-assignment, SLA (per ADR statuses).
- No code changed.

## Phase 2 — Composition / Core Services

- **New:** `domain/entity.py`, `domain/customer_factor.py`, `domain/issue.py`
  (pure frozen dataclasses + lifecycle transition tables mirroring V3M-1/3/5
  CHECKs).
- **New:** `data/processing_entities.py`, `data/customer_factors.py`,
  `data/issues.py` (service-role repositories, explicit columns, hard-delete
  refused at the repository boundary).
- **Extended:** `domain/__init__.py`, `data/__init__.py`, `backend/auth.py`
  (`AuthUser.entity_id`, `require_entity_member`), `api/dependencies.py`
  (`RepositoryBundle` + re-exports), `api/contracts.py` (V3 contracts),
  `api/router.py` (3 new routers).
- **Proof:** `tests/unit/domain/test_entity.py`, `test_customer_factor.py`,
  `test_issue.py`; `tests/integration/test_v3_repositories.py`;
  `tests/unit/api/fakes.py` (`MemoryEntities`, `MemoryCustomerFactors`,
  `MemoryIssues`).

## Phase 3 — Document / Processing Backend

- **Preserved:** `DocumentExtractionEngine`, `AIExtractionEngine`,
  `WorkflowOrchestrator` unchanged. No document-processing architecture was
  invented (ADR-V3-004 producer/consumer is OPEN/DEFERRED).
- **Boundary documented:** the workflow pipeline continues to resolve
  CarbonTally-managed factors; customer-factor matching (D-cf-5) is wired only
  at the API surface (`api/dependencies.get_matching_engine`), so the existing
  document pipeline behaviour is unchanged.
- No code changes to the document pipeline.

## Phase 4 — Factor Matching + Calculation

- **Extended:** `engines/factor_matching.py` — D-cf-5 approved-customer-first
  candidate pre-check (single active candidate → matched; multiple →
  ambiguous; none → CarbonTally pipeline). `domain/matching.py` — `MatchResult`
  carries `factor_kind`/`customer_factor_id`.
- **Extended:** `engines/calculation.py` — `CalculationRequest` factor union
  (emission factor XOR customer factor), `_compute_co2e` for the customer path
  with identical `RESULT_PRECISION`, O1 snapshot provenance passed through;
  `domain/calculation.py` — `CalculationSnapshot` O1 fields + hash canonical
  form, `CalculationResult.customer_factor`, `EmissionLog.factor_id` Optional;
  `data/emissions_logs.py` — `save_snapshot` writes `factor_kind`/
  `customer_factor_id`, `create` accepts NULL `emission_factor_id`.
- **Proof:** `tests/unit/engines/test_customer_factor_integration.py`
  (precedence, draft exclusion, ambiguity, O1 provenance, exactly-one-source).

## Phase 5 — Customer / Consultant / Processing Entity

- **New:** `api/admin_entities.py` (CarbonTally-internal entity CRUD +
  lifecycle transitions, audited), `api/customer_factors.py` (draft CRUD,
  org-admin approve with no self-approval, soft deactivate — D-cf-3/D-cf-4).
- **Extended:** `api/business.py` `/calculate` — optional `customer_factor_id`
  with org-isolation + active-only checks.
- **Preserved:** the consultant model untouched (consultants are neither
  Processing Entities nor CarbonTally staff).
- **Proof:** `tests/unit/api/test_v3_entities.py`,
  `tests/unit/api/test_v3_customer_factors.py`.

## Phase 6 — Customer Review / Output

- **New:** `api/issues.py` — customer-facing issue surface (`entity_id IS
  NULL`), entity-scoped listing (`require_entity_member`), CarbonTally triage,
  transition authority + reopen stamping (ADR-V3-009).
- **Extended:** `engines/report_generation.py` provenance section tags the
  `CUSTOMER` source for customer-factor logs (V3-012 lineage); V3 contracts for
  issues added.
- **Proof:** `tests/unit/api/test_v3_issues.py`; report provenance covered by
  static review (no behavioural regression to the 12-section skeleton).

## Phase 7 — Test Migration

- **New:** 8 test files (3 domain, 1 engine, 3 API contract, 1 integration).
- **Updated (protocol-driven only):** `tests/unit/engines/test_calculation.py`
  and `src/providers/seai/tests/test_defra_regression.py` sink signatures;
  `tests/unit/api/fakes.py`; `tests/integration/conftest.py` (V3 truncate
  list). No existing V2.1 test was discarded.

## Phase 8 — Integration Verification

- **Deferred to a runnable environment:** the pytest suites could not be
  executed in this session (shell/process unavailable). Static verification
  covered imports, protocols, dataclass field ordering, contract models and
  cross-module references.
- **Target commands:** `python -m pytest tests/unit/domain tests/unit/engines
  tests/unit/api` and `python -m pytest
  tests/integration/test_v3_repositories.py` (needs the local
  `carbontally_test` database).

---

**Test matrix (proof per area):** authentication/authorization —
`test_v3_issues.py` (entity member allow/deny); tenant isolation —
`test_v3_customer_factors.py` (org scoping, approve authority, no
self-approval); processing-entity isolation — `test_v3_entities.py`,
`test_v3_issues.py`; factor matching — `test_customer_factor_integration.py`;
calculation provenance — `test_customer_factor_integration.py`; issues
lifecycle — `test_v3_issues.py`; audit/domain events — V2.1 suites preserved
plus per-route audit calls reviewed statically.

