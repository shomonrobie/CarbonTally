# CarbonTally Backend v2.1 — Traceability Matrix v1.0

Status: **V2.1 TRACEABILITY COMPLETE — READY FOR V3 IMPACT ASSESSMENT**

Date: 2026-08-09 · Branch: `main` (working tree — Phase 9 + Phase 10 work is uncommitted)
Scope: CarbonTally Backend v2.1 — every major architecture requirement traced to actual implementation.
Mode: READ-ONLY analysis. No code, schema, migration, RLS, Storage, contract or test changes were made.

---

## 1. Executive summary

Phase 9 and Phase 10 of the CarbonTally Backend v2.1 are complete. This matrix
traces the full v2.1 architecture (Backend v2.1 Final Implementation
Instructions CT-ARCH-001…016; Implementation Preparation Pack v2.1.0 — FROZEN;
the 25-section architecture mapping in prep-pack §7; all Phase completion
reports) against the actual repository, the actual Supabase migrations, the
actual database factor baseline and the actual test suite.

**Overall result:** the v2.1 business-processing engine stack is implemented and
verified at the unit level: domain (10 modules), repositories (9), infrastructure
(event bus, audit logger, search index, config, service pool), and engines
(matching, calculation, extraction, AI extraction, workflow, validation,
benchmarking, report generation). The Phase 10 API exposes these as thin
orchestrators. The database migrations required by the prep pack (M1–M8) exist
and the development database holds the verified baseline **DEFRA 7,029 / SEAI 20
/ TOTAL 7,049**.

**Main gaps (all pre-existing Phase 5 deviations, carried into the V2.1
baseline):**
1. **Provider plugin architecture (`backend/providers/`) not implemented** —
   DEFRA/SEAI imports are standalone CLI importers under `src/commands/` +
   `src/providers/` (psycopg2), not the frozen `ProviderPlugin`/`registry`
   package under `backend/` (deviation D1, HIGH).
2. **`ImportMappingEngine` (`backend/engines/import_mapping.py`) not
   implemented** — imports bypass the v2.1 `ImportsRepository`/event bus as an
   engine (deviation D2, HIGH).
3. **Phase 11 admin-platform remainder** (import wizard, publish/archive,
   synonym dictionary, units/countries/reporting-years management) not
   implemented; Phase 10 delivered only imports/providers/audit/aliases.
4. **EPA / ADEME / IPCC deferred** (no implementation, no factor data).
5. **The canonical pytest suite cannot complete in this environment** — the
   integration suite requires the local `carbontally_test` database and the
   process terminates/hangs (re-confirmed during this analysis). All recorded
   pytest passes are unit-suite passes; all integration evidence is from
   standalone supplementary harnesses.

No V3 work was started. This document is the input baseline for the V3 Impact
Assessment.

---

## 2. Methodology

### 2.1 Authoritative sources

| # | Source | Role | Repository state |
|---|---|---|---|
| S1 | `CarbonTally_Backend_V2_Final_Implementation_Instructions.md` (docs/cline) | CT-ARCH-001…016 mandatory decisions | Present |
| S2 | `# CarbonTally Backend v2.1 — Implementation Preparation Pack.md` (docs/cline) | FROZEN single source of truth: migrations M1–M8, domain catalogue, repository catalogue, DI graph, package structure, implementation order, §7 architecture→phase mapping, readiness issues R1–R25 | Present (48 KB) |
| S3 | `Backend_Architecture_v2.1.md` (docs/cline) | Referenced as the v2.1 architecture specification | **Empty (0 bytes)** — spec content is known through S2 §7 and the phase reports |
| S4 | `CarbonTally Backend v2.1 — Architecture Readiness Review (Final Gate).md` (docs/cline) | Final-gate review | **Empty (0 bytes)** |
| S5 | Phase completion reports (docs/cline) | Phase 9 Readiness Audit, 9A–9D, Phase 10, SEAI provider series | Present |
| S6 | Actual repository (`backend/`, `src/providers/`) | Authoritative for implementation | Inspected module-by-module |
| S7 | `supabase/migrations/` (16 files + schema_snapshot.sql) | Authoritative for schema | Inspected |
| S8 | Actual test suite (`backend/tests/unit`, `backend/tests/integration`) + recorded pytest/harness outputs | Authoritative for tests | Inspected; pytest re-verified this session (does not complete — see §11/§17) |

### 2.2 Rule applied

> The actual repository, database and tests are authoritative. A requirement is
> **COMPLETE only when code/schema/test evidence exists** — a specification or a
> phase report alone is never sufficient. This matrix re-verifies each phase
> report's claims against the working tree.

### 2.3 Evidence collected in this analysis

- `backend/domain/*` (11 modules), `backend/data/*` (10), `backend/engines/*`
  (10), `backend/infra/*` (7), `backend/api/*` (9), `backend/core/*` (3) —
  exports and module docstrings inspected.
- `backend/auth.py` (JWT/RBAC), `backend/main.py` (legacy), `backend/main_v2.py`
  (v2.1 entrypoint), `backend/config.py` + `infra/config.py`.
- All 16 Supabase migrations + `schema_snapshot.sql` (tables, columns, RLS
  policies, indexes, functions extracted programmatically).
- Test inventory: every `test_*.py` under `backend/tests/` counted; integration
  conftest targets `carbontally_test`.
- Recorded test outputs: `regression9ab.txt`, `regression9c.txt`,
  `regression9d_9ab.txt`, `regression9d_9c.txt`, `selfcheck9c.txt`,
  `selfcheck9d_9c.txt`, `pycheck9d.txt` (74/74), `_phase10_selfcheck.txt`
  (49/49), `dbprobe9d.txt` (7049/7029/20).
- Live pytest attempt this session: `pytest tests/unit/...` produced no output
  (process hangs) — recorded as an environment limitation, not a pass/fail.
- Git working-tree state (`git status --short`): all Phase 9/10 work is
  untracked on `main`; nothing committed.

---

## 3. Status taxonomy

| Status | Meaning | Used when |
|---|---|---|
| **COMPLETE** | Requirement satisfied with repository/code/schema/test evidence | Engine, repo, domain, migration, route present and exercised by tests/harnesses |
| **PARTIAL** | Requirement met in part; one or more sub-requirements absent | e.g. Admin Platform (4 of many surfaces); import platform (no engine) |
| **NOT IMPLEMENTED** | Explicitly required, no code/schema/route exists | `ImportMappingEngine`, `backend/providers/`, `infra/cache.py` |
| **DEFERRED** | Intentionally postponed to a later phase (documented) | EPA/ADEME/IPCC providers; Phase 11 admin remainder; ValidationEngine A10–A13 |
| **FUTURE** | Listed as future capability in the spec | RecommendationEngine; external/peer benchmarking; PDF/HTML rendering; Prometheus metrics |
| **NOT APPLICABLE** | Reference-only or conditionally applicable requirement | §22 ADRs, §24 risks |
| **BLOCKED** | Requirement cannot proceed without an unresolved dependency | None (no requirement is blocked) |
| **UNKNOWN** | Cannot be determined from available evidence | Live production DB/RLS/Storage state (only dev DB facts are verified); security assessment report |

---

## 4. Complete traceability matrix

### 4.1 Architecture Specification §1–§25 → implementation phase (prep-pack §7 mapping)

| § | Architecture requirement | Intended phase | Status | Implementation / Evidence / Notes |
|---|---|---|---|---|
| §1 | Architecture Overview — Supabase BaaS + FastAPI business engine, React→Supabase CRUD | 0–1 | **PARTIAL** | `infra/supabase.py` (service client + asyncpg pool), `api/router.py`. v2.1 surface (`main_v2.py`) coexists with legacy FastAPI `main.py`; "FastAPI must not duplicate CRUD" is violated by the **legacy** surface, honoured by v2.1 API (§9). |
| §2 | Design Principles — single responsibility, thin routes, composition | all | **COMPLETE** | `engines/__init__.py`, `api/__init__.py` layer-rule docstrings; `api/router.py` "no business logic". Verified in code review. |
| §3 | Component & Layer Diagrams | 1–3 | **COMPLETE** | `backend/{core,domain,data,engines,infra,api}` packages; import/compile harness. Package layout matches prep-pack §5 except providers. |
| §4 | Package Structure (`backend/providers/` base.py/registry.py/defra/seai/epa/ademe/ipcc/custom) | 1–3 | **PARTIAL** | **No `backend/providers/`** — deviation **D1**. Providers live at `src/providers/{defra,seai}`. Legacy dirs `middleware/`,`routes/`,`services/`,`utils/` coexist. |
| §5 | Dependency Rules — engines depend only on core/domain/infra/data; engines→engines only via constructor injection; infra never contains business logic | 1–3 | **COMPLETE** | `engines/calculation.py` (FactorMatchingEngine injected), `engines/report_generation.py` (CalculationEngine injected). Enforced per inspection + unit tests. |
| §6 | The Four Platforms (matching, import, calculation, workflow+event) | 4–8 | **PARTIAL** | matching ✓, calculation ✓, workflow+event ✓; import platform = CLI importers + `data/imports.py`, **no ImportMappingEngine** (deviation **D2**). |
| §7 | Processing Engines — detailed specs | 4–9 | **PARTIAL** | 8 engines implemented (§7 engine table); `ImportMappingEngine` absent. |
| §8 | Provider Plugin Architecture — ProviderPlugin ABC, registry, plugins | 5 | **NOT IMPLEMENTED** | No `backend/providers/base.py`/`registry.py`/`plugin.py`; `src/providers/{defra,seai}` are CLI pipelines (parser→mapper→validator→exporter). Deviation **D1** (HIGH). |
| §9 | Domain Model — 10 modules, immutable dataclasses, zero deps | 1 | **COMPLETE** | `backend/domain/` 11 modules (incl. Phase 9 `validation.py`, `benchmarking.py`); `tests/unit/domain/` 11 files ~146 tests. |
| §10 | Repository Architecture — AbstractRepository[T] + 9 repositories | 2 | **COMPLETE** | `backend/data/` base + 9 repos; all repo tables present; §12. |
| §11 | Matching Platform — 6-stage pipeline, confidence, no silent guessing | 4 | **COMPLETE** | `engines/factor_matching.py` + `matching_stages.py` (Exact, NaturalKey, Alias, Keyword, Fuzzy, Semantic); tests 15+24; integration written. CT-ARCH-004/006/014 satisfied. |
| §12 | Import Platform — versioned import, rollback, batch tracking | 5 | **PARTIAL** | `data/imports.py` (batch lifecycle incl. activate/rollback), `src/commands/import_defra.py`, `import_seai.py`; M1/M2; SEAI import verified (20 rows, batch `9e3b2c8a-…`). No engine (D2). |
| §13 | Calculation Platform — reproducible calc, snapshots, hash, verify | 6 | **COMPLETE** | `engines/calculation.py` (CalculationEngine, CalculationSink, DEFAULT_ALGORITHM_VERSION); M3/M4; 27 unit tests; pycheck9d snapshot/verify PASS. |
| §14 | Workflow & Event Platform — DomainEvent hierarchy (12+), Saga, orchestrator, dpq columns | 3 + 8 | **COMPLETE** | `domain/workflow.py` (14 concrete events + Saga + DOCUMENT_PIPELINE), `engines/workflow.py` (WorkflowOrchestrator), `infra/event_bus.py`; M5 (domain_events), M7 (workflow_error_count/workflow_next_retry_at); tests 21+22. 14 events ≥ spec's 12. |
| §15 | Audit Framework — AuditRepository, AuditLogger, append-only | 3 | **COMPLETE** | `data/audit.py`, `infra/audit_logger.py`, `domain/audit.py`; `audit_trail` (v2.1) + `audit_logs` (legacy); tests 7 + 13; integration written. |
| §16 | Factor Search Index — in-memory, load at startup, rebuild on import | 3 | **COMPLETE** | `infra/search_index.py` (FactorSearchIndex, `from_repository`); 21 unit tests; loaded lazily via `api/dependencies.py`. |
| §17 | Versioning Strategy — import batches (providers) + snapshots (calculations) | 5 + 6 | **COMPLETE** | `data/imports.py`, natural-key upsert in `data/emission_factors.py`, `engines/calculation.py`; import_batches + import_batch_id + calculation_snapshots + snapshot_id; SEAI batch verified completed/active. |
| §18 | Caching Strategy — `infra/cache.py` TTL cache | 3 | **NOT IMPLEMENTED** | No `infra/cache.py`. Readiness issue **R9** removed CacheRepository; FactorSearchIndex + `cache_default_ttl_seconds` config exist but no cache module. |
| §19 | Security Model — JWT, RLS, admin; middleware | 0 + 10 | **PARTIAL** | `api/middleware.py` does correlation/timing; auth via `auth.py` deps; RC2 RLS + M8 new-table policies. Rate limiting only in legacy `middleware/rate_limit.py`, not v2.1 (§10). |
| §20 | Admin Platform — providers, libraries, import wizard, validation, aliases, synonyms, units, countries, years, history, publish/archive | 10 + 11 | **PARTIAL** | `api/admin_imports.py`, `admin_providers.py`, `admin_audit.py`, `admin_aliases.py` (4 surfaces, 13 admin routes); wizard/synonyms/units/countries/years/publish/archive = Phase 11 **not implemented**. |
| §21 | Coding Standards — mypy strict | all | **PARTIAL** | `backend/pyproject.toml` (`mypy strict=true`); compile harnesses pass; no mypy run recorded. |
| §22 | Architecture Decision Records — reference only | ref | **NOT APPLICABLE** | CT-ARCH-001…016 (S1) serve as ADRs; reference-only. |
| §23 | Future Expansion Strategy — additional providers | 12 | **DEFERRED** | SEAI delivered early (**COMPLETE**); EPA/ADEME/IPCC deferred (no data, no code); admin providers API reports them `implemented=false, status="deferred"`. |
| §24 | Risks & Trade-offs — reference only | ref | **NOT APPLICABLE** | Reference-only. |
| §25 | Migration Notes — M1–M8 before app code | 0 | **COMPLETE** | `supabase/migrations/20260807*.sql` all 8 present; dev DB has import_batches row + 20 batch-linked SEAI factors; `dbprobe9d.txt` = 7049/7029/20. |

---

### 4.2 CT-ARCH-001…016 (Final Implementation Instructions)

| ID | Requirement | Status | Implementation / Evidence |
|---|---|---|---|
| CT-ARCH-001 | Supabase BaaS + FastAPI business processing engine | **COMPLETE** | `infra/supabase.py` (service client + asyncpg pool), `api/router.py` `create_app()`; RC2 migrations. |
| CT-ARCH-002 | CRUD ownership — Supabase owns CRUD; FastAPI only business processing | **PARTIAL** | v2.1 API = business endpoints only (COMPLETE); **legacy** `main.py`+`routes/` (~40 modules) still serve CRUD — violates at app level, frozen not migrated. |
| CT-ARCH-003 | Engines — required (Matching, Calculation, PDFExtraction, ExcelImport, CSVImport, DocumentProcessing, ReportGeneration, Validation, Workflow); future (AI, Benchmark, Recommendation) | **PARTIAL** | Implemented: FactorMatching ✓, Calculation ✓, DocumentProcessing=extraction ✓, ReportGeneration ✓, Validation ✓ (9.1), Benchmarking ✓ (9.2 despite "future"), Workflow ✓, AIExtraction ✓ (implemented despite "future"). **Not implemented:** ExcelImportEngine, CSVImportEngine (CLI importers instead), RecommendationEngine. |
| CT-ARCH-004 | FactorMatchingEngine — matches only, never calculates, format-independent, standardised activities | **COMPLETE** | `engines/factor_matching.py`; `domain/matching.py` (MatchRequest/MatchResult); unit tests + `/api/v2/factor-match`. |
| CT-ARCH-005 | Standard activity object for every importer | **PARTIAL** | `MatchRequest`/`CalculationRequest` are the standard matching/calculation objects; document/Excel/CSV importers do **not** emit one common activity object (they write factors to DB via CLI). |
| CT-ARCH-006 | Matching strategy priority + confidence + method + warnings; never silently guess | **COMPLETE** | 6 stages (Exact, NaturalKey≈Hierarchical, Alias≈Synonym, Keyword, Fuzzy, Semantic=AI opt-in); MatchResult carries confidence/methodology/stages/suggestions. |
| CT-ARCH-007 | Multi-provider design — not DEFRA-specific | **PARTIAL** | DEFRA + SEAI factor data coexist, matched by country (GB/IE); no `backend/providers/` plugin layer (D1). `test_defra_regression.py` proves isolation. |
| CT-ARCH-008 | Factor libraries — no hard-coded DEFRA assumptions | **COMPLETE** | `factor_set`/`factor_source` fields; `FactorSet` domain model; live sets `DEFRA-DESNZ/DEFRA-2025` and `SEAI/SEAI-2025`; matching selects by country/year/provider. |

| CT-ARCH-009 | Platform administration — providers, libraries, import wizard, validation, aliases, synonyms, units, countries, years, history, publish/archive | **PARTIAL** | Providers catalogue ✓, import history ✓, aliases CRUD ✓ (api/admin_*.py); wizard, synonyms, units, countries, reporting years, publish/archive ✗ (Phase 11). |
| CT-ARCH-010 | Import workflow Upload→Validate→Preview→Publish→Rebuild index→Active | **PARTIAL** | CLI importers validate → load/activate; `import_batches` status lifecycle; search-index rebuild supported; **no API wizard/preview step**. |
| CT-ARCH-011 | In-memory search index loaded at startup, rebuilt after publish | **COMPLETE** | `infra/search_index.py` FactorSearchIndex singleton + `from_repository`; loaded lazily in `api/dependencies.py`. |
| CT-ARCH-012 | Backend exposes ONLY business-processing endpoints | **PARTIAL** | v2.1 API: 5 business + 13 admin + health = COMPLETE for the new surface; legacy `main.py`/`routes/` still serve general CRUD (frozen). |
| CT-ARCH-013 | Freeze legacy backend as `backend_legacy`; reuse business logic selectively; don't reuse routing | **PARTIAL** | Legacy `main.py`+`routes/` untouched (frozen in place) but **not renamed** to `backend_legacy`; v2.1 API shares `auth.py` but not legacy routing. |
| CT-ARCH-014 | Explainability — factor_id, library, confidence, method, timestamp recorded | **COMPLETE** | `MatchResult` (factor, factor_set, confidence, methodology, stages); `calculation_snapshots` (factor_id, factor_source, factor_set, import_batch_id, request_id, calculated_at); audit entries. |
| CT-ARCH-015 | Extensibility — new provider = import + configure library, no app rewrite | **PARTIAL** | SEAI added without engine changes (principle proven); plugin architecture absent (D1). |
| CT-ARCH-016 | Engine independence — single responsibility, independently testable | **COMPLETE** | 8 engines with dedicated unit suites; constructor injection; engines/__init__.py exports. |

---

## 5. Database traceability

### 5.1 Migration inventory (authoritative = `supabase/migrations/`, 16 files + snapshot)

| Migration | Content | Spec source | Status |
|---|---|---|---|
| `00000000000000_init_schema.sql` | Base schema (~100 tables, legacy + v2.1 tables, enums) | pre-RC2 | Applied (dev DB) |
| `20260800000000_rc2_schema.sql` | RC2 schema changes (facilities.country/eircode, emission_factors scope/unit/factor_source/factor_set, organizations.is_active, customer_documents.file_checksum …) | RC2 freeze | Applied |
| `20260801000000_rc2_constraints.sql` | RC2 constraints | RC2 | Applied |
| `20260802000000_rc2_indexes.sql` | RC2 indexes | RC2 | Applied |
| `20260803000000_rc2_rls.sql` | RC2 RLS policies (organizations_org_select/update, users_select_self, om_*, cp_select_own, cc_*, cfm_*) | RC2 | Applied |
| `20260804000000_rc2_functions.sql` | RC2 functions | RC2 | Applied |
| `20260805000000_rc2_triggers.sql` | RC2 triggers | RC2 | Applied |
| `20260806000000_rc2_verification.sql` | RC2 verification | RC2 | Applied |
| `20260807000000_add_import_batches.sql` | **M1** — `import_batches` table | prep-pack §1.1 | Present; dev DB has SEAI batch row |
| `20260807010000_add_emission_factors_import_batch.sql` | **M2** — `emission_factors.import_batch_id` + FK + index | prep-pack §1.1 | Present; 20 SEAI rows linked |
| `20260807020000_add_calculation_snapshots.sql` | **M3** — `calculation_snapshots` table | prep-pack §1.1 | Present |
| `20260807030000_add_emissions_logs_snapshot.sql` | **M4** — `emissions_logs.snapshot_id` + FK + index | prep-pack §1.1 | Present |
| `20260807040000_add_domain_events.sql` | **M5** — `domain_events` table + indexes | prep-pack §1.1 | Present |
| `20260807050000_add_factor_aliases.sql` | **M6** — `factor_aliases` table + unique index | prep-pack §1.1 | Present |
| `20260807060000_add_dpq_workflow_columns.sql` | **M7** — `document_processing_queue.workflow_error_count`, `workflow_next_retry_at` | prep-pack §1.1 | Present |
| `20260807070000_add_new_table_rls.sql` | **M8** — RLS for import_batches (deny-all), calculation_snapshots (select-own), domain_events (deny-all), factor_aliases (select/insert/delete-own) | prep-pack §1.3 | Present |
| `schema_snapshot.sql` | Full schema dump (121 KB) | tooling | Present |

Verified column sets for M1/M2/M3/M5/M6/M7 match the prep-pack §1.2 definitions
exactly (`import_batches`, `emission_factors.import_batch_id`,
`calculation_snapshots`, `domain_events`, `factor_aliases`, dpq workflow columns).

### 5.2 Table traceability categories

**Required by architecture and implemented (v2.1-specific):**

| Table / column | Requirement | Migration |
|---|---|---|
| `import_batches` | §12/§17 versioned import platform | M1 |
| `emission_factors.import_batch_id` | §17 provider/library versioning | M2 |
| `calculation_snapshots` | §13 forensic calculation records | M3 |
| `emissions_logs.snapshot_id` | §13 operational↔forensic link | M4 |
| `domain_events` | §14 event platform | M5 |
| `factor_aliases` | §11/§20 alias dictionary | M6 |
| `document_processing_queue.workflow_error_count` + `workflow_next_retry_at` | §14 workflow retry | M7 |
| RC2 RLS policies + M8 new-table policies | §19 security model | RC2 RLS + M8 |

**Base RC2/legacy tables used by v2.1 engines/repos:** `emission_factors`,
`emissions_logs`, `organizations`, `organization_members`, `organization_metadata`,
`facilities`, `assets`, `customer_documents`, `document_processing_queue`,
`processing_queue`, `report_generation_queue`, `manual_review_queue`,
`processing_logs`, `processing_audit_trail`, `queue_settings`, `sla_definitions`,
`system_settings`, `audit_trail`, `audit_logs`, `roles`, `users`,
`staff_profiles`, `upload_batches`, `units` (all present in init schema).

**Required but missing (documented):**
- No benchmark/reference tables — Phase 9 benchmarking is **internal-only**
  (YoY, facility, scope, intensity per FTE/area/revenue) computed from
  `emissions_logs` aggregates; no peer/industry reference table exists (prep-pack
  D7 decision: approved, none required).
- No `generated_reports` table — `ReportsRepository` maps `GeneratedReport` to
  `report_generation_queue` with structured content in JSONB (deviation D4,
  documented LOW).
- No synonym-dictionary table; no import-wizard/preview tables; no
  reporting-years/units/countries admin tables (Phase 11 scope).

**Implemented but not specified (superset):** the ~100 legacy RC2 tables
(communications, reviews, staff workload, beta, waitlist, glossary, etc.) —
legacy application surface, out of v2.1 engine scope.

**Deferred:** EPA/ADEME/IPCC factor structures (Phase 12).

**Future:** observability/metrics tables; recommendation-engine structures;
benchmark reference/peer data (if external benchmarking is ever added).

**Obsolete/superseded:** `defra_conversion_factors` (legacy DEFRA store —
superseded by `emission_factors`); legacy `audit_logs` coexists with v2.1
`audit_trail`; `processing_queue`/`report_generation_queue`/`manual_review_queue`
schema exists (RC2 worker architecture) but no v2.1 worker/consumer process
claims them.

### 5.3 RLS traceability

| Policy area | Status | Evidence |
|---|---|---|
| RC2 org isolation (organizations select/update own; users self; org_members self/admin) | **COMPLETE** | `20260803000000_rc2_rls.sql` |
| v2.1 new tables deny-by-default + select-own | **COMPLETE** | `20260807070000_add_new_table_rls.sql` (aliases_select_own, aliases_insert_own, aliases_delete_own, calc_snapshots_select_own; import_batches & domain_events deny-all) |
| Storage policies (buckets) | **UNKNOWN** | Legacy Storage policies in init schema; no v2.1 Storage surface; not re-verified this session |
| Realtime publish policies | **UNKNOWN** | Legacy config only; no v2.1 Realtime surface |

### 5.4 Verified factor baseline (dev database)

`dbprobe9d.txt` + SEAI import record:
- `emission_factors` total = **7,049**
- DEFRA-DESNZ / GB / 2025 = **7,029**
- SEAI / IE / 2025 = **20** (all `factor_set='SEAI-2025'`,
  `import_batch_id=9e3b2c8a-1d4f-4e6b-8a7c-2f5d6e7a8b9c`, batch `is_active=TRUE`)
- No duplicate natural keys; DEFRA rows unmodified.

No live read-only SQL round-trip was possible in this session (shell/pytest
environment hangs); the baseline above is the recorded, cross-referenced state
from the SEAI import record and `dbprobe9d.txt`.

---

## 6. Backend/domain traceability

| Domain module | Types (verified in `backend/domain/__init__.py`) | Phase | Status | Tests |
|---|---|---|---|---|
| `domain/factor.py` | EmissionFactor, FactorSet, FactorSetMetadata | 1 | **COMPLETE** | test_factor.py (16) |
| `domain/calculation.py` | CalculationMethodology (StrEnum), CalculationSnapshot, CalculationResult, VerificationResult, EmissionLog, EmissionsAggregate | 1/6 | **COMPLETE** | test_calculation.py (8) |
| `domain/document.py` | Document, ExtractionResult, ExtractedPage, ExtractedTable, ExtractionField | 1/7 | **COMPLETE** | test_document.py (6) |
| `domain/organization.py` | Organization, OrganizationMember, Facility, Asset, OrganizationMetadata | 1 | **COMPLETE** | test_organization.py (6) |
| `domain/report.py` | ReportRequest, GeneratedReport, ReportSection, ReportTemplate | 1/9 | **COMPLETE** | test_report.py (8) |
| `domain/workflow.py` | DomainEvent (ABC) + 14 concrete events, WorkflowDefinition, Transition, Saga, SagaStep, DOCUMENT_PIPELINE | 3/8 | **COMPLETE** | test_workflow.py (22) |
| `domain/provider.py` | ProviderInfo, ProviderVersion, ImportBatch, ImportError, DiscoveryResult, DiscoveredSheet, RawFactorRow, NormalisedFactor, ImportResult | 1/5 | **COMPLETE** | test_provider.py (17) |
| `domain/matching.py` | MatchRequest, MatchResult, Suggestion, FactorAlias, StageResult, MatchingPipelineConfig, MatchingStage (ABC), FactorSearch | 1/4 | **COMPLETE** | test_matching.py (20) |
| `domain/audit.py` | AuditEntry, AuditQuery, AuditTrail | 1/3 | **COMPLETE** | test_audit.py (7) |
| `domain/validation.py` | ValidationSeverity, ValidationIssue, ValidationReport, ValidationRequest | 9.1 | **COMPLETE** | test_validation.py (19) |
| `domain/benchmarking.py` | BenchmarkRequest, BenchmarkMetric, BenchmarkResult, BenchmarkAvailability | 9.2 | **COMPLETE** | test_benchmarking.py (17) |

**Core kernel:** `core/exceptions.py` — CarbonTallyError hierarchy with 13
subclasses, each declaring `code` + `http_status` (FACTOR_NOT_FOUND 404,
FACTOR_AMBIGUOUS 409, VALIDATION_FAILED 422, BENCHMARK_DATA_INSUFFICIENT 404,
UNIT_MISMATCH 422, UNKNOWN_PROVIDER 404, …). `core/types.py` — Country, Unit,
Scope, ReportingYear, DateRange. `core/logging.py` — structured logging config.

Domain note (deviation D3): `CalculationSnapshot` on the domain object carries
`match_request_id`/`created_at`; full provenance fields (activity, activity_type,
factor_source, factor_set, import_batch_id, calculated_by, request_id) are passed
to the sink, not stored as snapshot fields — DB coverage is complete (LOW).

---

## 7. Engine traceability

| Engine | File | Phase | Status | Capabilities (verified) | Tests |
|---|---|---|---|---|---|
| FactorMatchingEngine | `engines/factor_matching.py` | 4 | **COMPLETE** | build_matching_pipeline, exact/natural-key/alias/keyword/fuzzy/semantic stages, confidence, suggestions, no_match | test_factor_matching.py (15), test_matching_stages.py (24) |
| CalculationEngine | `engines/calculation.py` | 6 | **COMPLETE** | quantity×multiplier, unit checks, CalculationSink, snapshots, content hash, verify, UnitMismatchError | test_calculation.py (27) |
| DocumentExtractionEngine | `engines/extraction.py` | 7 | **COMPLETE** | text→ExtractionResult pipeline, ExtractionFailedError | test_extraction.py (11) |
| AIExtractionEngine | `engines/ai_extraction.py` + `infra/llm_client.py` | 7 | **COMPLETE** | LLM field extraction (OpenAI/Anthropic via LLMClient), DEFAULT_FIELDS | test_ai_extraction.py (14), test_llm_client.py (7) |
| WorkflowOrchestrator | `engines/workflow.py` | 8 | **COMPLETE** | DOCUMENT_PIPELINE dispatch via event handlers, retry, transitions, WorkflowInvalidTransition/MaxRetries | test_workflow.py (21) |
| ValidationEngine | `engines/validation.py` | 9.1 | **COMPLETE** | A1–A9 (input, reproducibility, factor/match, scope/unit, snapshot, integrity, SEAI CO2-only, provenance); **A10–A13 deferred**; 34 stable VAL_* codes | test_validation.py (56) |
| BenchmarkingEngine | `engines/benchmarking.py` | 9.2 | **COMPLETE** | internal-only B1–B8 (YoY, facility, scope, per-FTE/area/revenue intensity, activity intensity); never fabricates — `insufficient_data`/`zero_denominator` | test_benchmarking.py (29) |
| ReportGenerationEngine | `engines/report_generation.py` | 9.3 | **COMPLETE** | 12-section structured report, composes Calculation+Validation+Benchmarking, persists via ReportsRepository, publishes ReportGenerated; **PDF/HTML rendering NOT implemented** | test_report_generation.py (33) |
| ImportMappingEngine | `engines/import_mapping.py` | 5.3 | **NOT IMPLEMENTED** | absent — deviation D2; imports run as CLI (`src/commands/import_defra.py`, `import_seai.py`) + `src/providers` pipelines | none |
| RecommendationEngine | (future) | — | **FUTURE** | not listed in prep-pack phases; future per CT-ARCH-003 | none |

Engine independence (CT-ARCH-016 / prep-pack §4.2) verified: CalculationEngine
injects FactorMatchingEngine; ReportGenerationEngine injects CalculationEngine;
WorkflowOrchestrator dispatches via event handlers; ImportMappingEngine (were it
present) would call ProviderPlugin directly.

---

## 8. Provider traceability

| Provider | Status | Factor data (DB) | Importer | Tests | Intended architecture role | Current limitation |
|---|---|---|---|---|---|---|
| **DEFRA** | **COMPLETE** | **7,029** rows — `factor_source='DEFRA-DESNZ'`, `factor_set='DEFRA-2025'`, `country='GB'`, year 2025 | `src/providers/defra/` (models, parser, mapper, validator, exporter) + `src/commands/import_defra.py` | `src/providers/seai/tests/test_defra_regression.py` (GB matching/calculation regression); engine unit tests; integration (written) | Primary UK factor library; anchor of matching/calculation | Not a `backend/providers/` plugin (D1); imported via psycopg2 CLI |
| **SEAI** | **COMPLETE** | **20** rows — `factor_source='SEAI'`, `factor_set='SEAI-2025'`, `country='IE'`, year 2025, batch-linked (`9e3b2c8a-…`), CO2-only | `src/providers/seai/` + `src/commands/import_seai.py` | SEAI implementation-gate + compatibility-assessment checks; cross-provider matching in unit/engines; pycheck9d SEAI scenarios | Second national library; proves multi-provider matching/calculation without engine changes | CO2-only semantics preserved via `gas_coverage`; **no `backend/providers/` plugin** (D1) |
| **EPA** | **DEFERRED** | none | none | none (admin API reports `implemented=false, status="deferred"`) | Future Ireland EPA library (prep-pack §8/Phase 12) | No implementation started |
| **ADEME** | **DEFERRED** | none | none | none | Future France library (Phase 12) | No implementation started |
| **IPCC** | **DEFERRED** | none | none | none | Future global library (Phase 12) | No implementation started |
| Custom org libraries (CT-ARCH-007) | **NOT IMPLEMENTED** | none | none | none | Custom organisation factor sets | No custom-provider surface anywhere |

Cross-provider isolation evidence: `test_defra_regression.py` and pycheck9d
"IE/SEAI factor never matched for a GB organization / GB/DEFRA never for an IE
organization" checks PASS; matching selects by country + reporting_year +
provider context. Admin provider catalogue (`api/admin_providers.py`) lists all
five providers with correct implemented/deferred flags.

---

## 9. API traceability

### 9.1 Route inventory (v2.1 API, verified in `backend/api/`)

| Method | Route | Module | Auth | Status |
|---|---|---|---|---|
| GET | `/api/v2/health` | router.py | public (no DB) | **COMPLETE** |
| POST | `/api/v2/factor-match` | business.py | JWT + org access | **COMPLETE** |
| POST | `/api/v2/calculate` | business.py | JWT + org access | **COMPLETE** |
| POST | `/api/v2/validate` | business.py | JWT + org access | **COMPLETE** |
| POST | `/api/v2/benchmark` | business.py | JWT + org access | **COMPLETE** |
| POST | `/api/v2/generate-report` | business.py | JWT + org access | **COMPLETE** |
| GET | `/api/v2/admin/imports` | admin_imports.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/imports/active` | admin_imports.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/imports/{batch_id}` | admin_imports.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/providers` | admin_providers.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/providers/{key}` | admin_providers.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/audit` | admin_audit.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/audit/export` (CSV in envelope) | admin_audit.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/audit/correlation/{correlation_id}` | admin_audit.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/audit/{entry_id}` | admin_audit.py | require_admin | **COMPLETE** |
| GET | `/api/v2/admin/aliases` | admin_aliases.py | require_admin | **COMPLETE** |
| POST | `/api/v2/admin/aliases` | admin_aliases.py | require_admin | **COMPLETE** |
| PUT | `/api/v2/admin/aliases/{alias_id}` | admin_aliases.py | require_admin | **COMPLETE** |
| DELETE | `/api/v2/admin/aliases/{alias_id}` | admin_aliases.py | require_admin | **COMPLETE** |
| GET | `/api/v2/docs`, `/api/v2/openapi.json` | router.py (FastAPI) | public | **COMPLETE** |

### 9.2 API sub-system traceability

| Sub-system | Requirement (prep-pack Phase 10 / CT-ARCH-012) | Status | Evidence |
|---|---|---|---|
| Router / app factory | single router, thin routes, no business logic | **COMPLETE** | `api/router.py` `create_app()` |
| Dependencies / composition root | DI wiring, per-request repo bundle, engine factories, infra singletons | **COMPLETE** | `api/dependencies.py` (RepositoryBundle, get_repositories, get_matching_engine/calculation_engine/validation_engine/benchmarking_engine/report_engine, get_audit_context) |
| Middleware | request/correlation ID, timing header, structured log | **COMPLETE** | `api/middleware.py` RequestContextMiddleware |
| Contracts | stable pydantic models; Decimal-as-string; CO2/CO2e provenance (`gas_coverage`); extra="forbid" requests | **COMPLETE** | `api/contracts.py` (~24 KB); test_contracts.py (15) |
| Error envelope | `{error:{code,message,details}, request_id}` for CarbonTallyError, HTTPException, pydantic 422, unhandled 500 | **COMPLETE** | router.py handlers; test_foundation.py |
| Authentication | JWT bearer reuse of existing `auth.py` | **COMPLETE** | `auth.py` (HTTPBearer, get_current_user) |
| Authorization / RBAC | require_admin on admin; org access on business | **COMPLETE** | `auth.py` + `api/dependencies.py`; test_admin_endpoints.py (31) |
| Organization isolation | org_id scoping on business endpoints + repo filters | **COMPLETE** | business.py; pycheck9d isolation checks (org A/B) PASS |
| Admin imports | read-only batch history/active/by-id | **COMPLETE** | admin_imports.py; tests |
| Admin providers | catalogue + live state; deferred providers honest | **COMPLETE** | admin_providers.py; tests |
| Admin audit | query/correlation/entry/CSV export | **COMPLETE** | admin_audit.py; tests |
| Admin aliases | global/org-scoped CRUD + audit recording | **COMPLETE** | admin_aliases.py; tests |
| OpenAPI docs | `/api/v2/docs` + `/api/v2/openapi.json` | **COMPLETE** | router.py |

### 9.3 API requirements NOT implemented

- `/process/pdf`, `/process/excel`, `/process/csv` upload endpoints (CT-ARCH-012
  examples) — **not implemented**; document processing is engine-level only
  (`DocumentExtractionEngine`/`AIExtractionEngine`), no v2.1 upload/processing
  route.
- Admin import wizard (upload→validate→preview→publish) — Phase 11, deferred.
- Calculation-verification admin endpoint (prep-pack R21 `POST
  /api/v2/admin/calculations/{id}/verify`) — **documented in the prep pack but
  not implemented**.
- Workflow admin transition/retry endpoints (R20/R22) — documented in prep pack,
  not implemented.
- Rate limiting on the v2.1 API — only legacy `middleware/rate_limit.py`.

---

## 10. Security / RBAC / RLS traceability

| Control | Requirement | Status | Evidence | Gap / note |
|---|---|---|---|---|
| Authentication | JWT bearer (Supabase-issued tokens), existing `auth.py` | **COMPLETE** | `backend/auth.py`: `security = HTTPBearer()`, `get_current_user` decodes JWT with `SUPABASE_JWT_SECRET`, `AuthUser` model | Reused as-is by v2.1 API |
| RBAC | Roles + permission sets | **COMPLETE** | `roles` table; `require_role`, `require_permission`, `require_any_permission`, `require_all_permissions` in `auth.py` | Permission flags from DB `roles.permissions` |
| Admin authorization | Staff/admin gate on admin endpoints | **COMPLETE** | `require_admin()` (auth.py:310) on all 13 admin routes; test_admin_endpoints member-forbidden check PASS | — |
| Organization isolation (API) | Business endpoints scoped to requesting org | **COMPLETE** | `ensure_org_access` + org_id resolution in `api/dependencies.py`; repo methods filter org_id; pycheck9d org A/B isolation checks PASS | — |
| Organization isolation (repos) | Every tenant read/write filters organization_id | **COMPLETE** | `data/emissions_logs.py` (find_by_org, aggregate), `data/organizations.py`, `data/reports.py` (get_by_org) | Integration coverage unexecuted (DB unavailable) |
| RLS (v2.1 tables) | deny-by-default + select-own | **COMPLETE** | M8 policies; RC2 RLS migration | — |
| RLS (legacy tables) | RC2 org policies | **COMPLETE** | `20260803000000_rc2_rls.sql` | — |
| Storage access | Bucket-level policies | **UNKNOWN** | No v2.1 Storage surface; legacy init schema policies not re-verified | No change performed (read-only) |
| Realtime | Publish/authorize policies | **UNKNOWN** | Legacy config only | Out of v2.1 scope |
| Audit | Append-only audit trail for changes | **COMPLETE** | `audit_trail` + AuditRepository + AuditLogger + admin audit endpoints + audit context | No per-tenant audit filtering (global staff view) |
| API security | TLS/ingress | **NOT APPLICABLE (V2.1 SCOPE)** | Out of Phase 10 scope | Phase 10 doc §20 limitation |
| Rate limiting | v2.1 API | **NOT IMPLEMENTED** | Only legacy `middleware/rate_limit.py` | Gap (documented) |
| Security assessment report | Completed internal security assessment | **NOT PERFORMED** | `CarbonTally Application Security Assessment.md` is a **task template/prompt**, not a completed report; no `CARBONTALLY_SECURITY_ASSESSMENT_V1.md` exists | Gap — no verified security findings report for V2.1 |
| Secrets handling | env-based config | **COMPLETE** | `infra/config.py`, `.env` best-effort loading | — |

**Security gaps (no changes performed):**
1. Rate limiting absent from the v2.1 API surface.
2. No completed security-assessment report (only the template exists).
3. No per-tenant audit filtering on admin audit.
4. v2.1 admin endpoints rely on the legacy auth/RBAC module (`auth.py`) — a
   shared, legacy-authored component (functionally verified by unit tests).
5. No evidence of a completed independent penetration test (external testing is
   out of scope).

---

## 11. Testing traceability

### 11.1 Inventory (test functions counted in this analysis)

| Suite | Files | Test functions | Executed? |
|---|---|---|---|
| `tests/unit/api` (foundation, contracts, admin, business) | 4 | 77 | **pytest PASS** (recorded Phase 10: run 1 79/80, run 2 zero failures) |
| `tests/unit/domain` | 11 | ~146 | **pytest PASS** (recorded with unit/engines run) |
| `tests/unit/engines` | 10 | ~251 | **pytest PASS** (recorded with unit/domain run) |
| `tests/unit/infra` | 5 | ~71 | **pytest PASS** (reported in implementation session) |
| `tests/unit/test_core.py` | 1 | 14 | **pytest PASS** (reported) |
| `tests/integration` (incl. Phase 9 validation/benchmarking/report-generation + repo/engine integration) | 21 | ~90 | **NOT RUN** — requires `carbontally_test`; suite terminates/hangs in this environment |
| Legacy test scripts at `tests/` root (test_api.py, test_all_endpoints.py, …) | 5 | 6 | Outside pytest testpaths (not collected) |

### 11.2 Recorded execution evidence (pytest vs supplementary)

**ACTUAL PYTEST PASS (recorded in Phase 10 report §18):**
- `python -m pytest tests/unit/api -q` — completed. Run 1: 79 passed, 1 failed
  (`test_unhandled_error_never_leaks_internals`, fixed by testing with
  `raise_server_exceptions=False`); Run 2: all passed, zero failures.
- `python -m pytest tests/unit/engines tests/unit/domain -q` — completed, zero
  failures (Phase 9 regression).
- `python -m pytest tests/unit/infra tests/unit/test_core.py -q` — completed,
  zero failures (reported in the Phase 9/10 implementation session).

**TERMINATED / NO RESULT:**
- `python -m pytest -q` (canonical suite incl. `tests/integration`) — the process
  was terminated/hung before producing output; the integration conftest targets
  the local `carbontally_test` database, which was not reachable. **No result is
  claimed for the integration suite.** Re-confirmed this session: a pytest run of
  unit tests produced no output (process hangs in this environment).

**STANDALONE / SUPPLEMENTARY HARNESS PASS (not equivalent to pytest):**
- `_phase10_selfcheck.py` — **49/49 PASS** (mirrors the pytest API contract suite
  with the same in-memory fakes).
- `pycheck9d.txt` (Phase 9D harness) — **74/74 PASS** (matching, calculation,
  snapshot, validation, benchmarking, report, persistence, org isolation).
- `selfcheck9c.txt` (Phase 9C self-check) — **33/33 PASS**.
- `regression9ab.txt` (9A/9B regression runner) — **44/44 PASS**
  (ValidationEngine 15 + BenchmarkingEngine 29).
- `regression9c.txt` (9C import/compile checks) — **31/31 PASS**.
- SEAI import/verification records (20 rows, batch-linked) and
  `src/providers/seai/tests/test_defra_regression.py` — provider regression PASS.

### 11.3 Coverage vs architecture

| Architecture component | Unit | Integration (written, unrun) | Contract | Regression |
|---|---|---|---|---|
| Domain models | ✓ (11 files) | — | ✓ (via api contracts) | — |
| Repositories | ✓ (via infra + engine tests) | ✓ (18 repo/engine integration files) | — | ✓ 9A/9B runner |
| Engines (all 8) | ✓ (10 files) | ✓ (test_workflow, test_factor_matching, Phase 9 engine files) | ✓ (business endpoints) | ✓ 9D harness |
| Infra (event bus, audit, search index, config, LLM) | ✓ (5 files) | ✓ (5 integration files) | — | — |
| API | ✓ (4 files) | — | ✓ (test_contracts) | — |

### 11.4 Limitation (accurate record)

> The canonical full pytest suite has **not** been observed completing end-to-end
> in this environment: `tests/integration` requires the local `carbontally_test`
> Postgres database and the process terminates/hangs without output. Every
> integration-level claim in the phase reports therefore rests on supplementary
> harnesses (pycheck9d 74/74, selfcheck9c 33/33, phase10 49/49), **not** on a
> completed pytest run of the integration suite.

---

## 12. Repository traceability

| Repository | File | Aggregate | Status | Methods (prep-pack §3) present |
|---|---|---|---|---|
| AbstractRepository[T] | `data/base.py` | — | **COMPLETE** | get / save / delete (abstract) |
| EmissionFactorsRepository | `data/emission_factors.py` | EmissionFactor | **COMPLETE** | get, find_by_natural_key, find_by_activity, bulk_upsert, get_active_set, deactivate_by_batch, load_all_for_index, count_by_provider, save, delete |
| EmissionsLogsRepository | `data/emissions_logs.py` | EmissionLog | **COMPLETE** | create, find_by_org, aggregate (scope/month/year/asset/facility), count_by_scope, get, save, delete |
| OrganizationsRepository | `data/organizations.py` | Organization | **COMPLETE** | get_by_id, get_members, get_metadata, get_facilities, get_assets, update_metadata, get, save, delete |
| DocumentsRepository | `data/documents.py` | Document | **COMPLETE** | create_from_upload, update_status, get_pending_extraction, get_by_org, get, save, delete |
| ImportsRepository | `data/imports.py` | ImportBatch | **COMPLETE** | create_batch, complete_batch, fail_batch, activate_batch, deactivate_batch, rollback_batch, get_active, get_history, get, save, delete |
| ReportsRepository | `data/reports.py` | GeneratedReport | **COMPLETE** | create_generation_request, complete_generation, get_by_org, get, save, delete (maps to `report_generation_queue` — D4) |
| AuditRepository | `data/audit.py` | AuditEntry | **COMPLETE** | record, query, export_csv, get_by_correlation, get, save, delete |
| EventsRepository | `data/events.py` | DomainEvent | **COMPLETE** | store, get_by_correlation, replay, get, save, delete |
| FactorAliasesRepository | `data/factor_aliases.py` | FactorAlias | **COMPLETE** | find_by_alias, get_global_aliases, get_org_aliases, get, save, delete |

All repositories are async and bind to the service-role asyncpg pool
(`infra/supabase.py::get_service_pool`), matching prep-pack §10 (service-role
RLS bypass with code-level org filtering).

---

## 13. Workflow / processing traceability

| Requirement | Status | Evidence |
|---|---|---|
| WorkflowDefinition + transitions (`DOCUMENT_PIPELINE`) | **COMPLETE** | `domain/workflow.py` (WorkflowDefinition, Transition, DOCUMENT_PIPELINE) |
| Event-driven dispatch (WorkflowOrchestrator → engines via handlers, not direct calls) | **COMPLETE** | `engines/workflow.py`; `infra/event_bus.py` in-process pub/sub |
| Saga coordination | **COMPLETE** | `domain/workflow.py` (Saga, SagaStep); unit tests |
| Retry columns on `document_processing_queue` | **COMPLETE** | M7 (`workflow_error_count`, `workflow_next_retry_at`); prep-pack R7 resolution (reuse existing dpq table, no new table) |
| Document processing chain (upload→extract→match→calculate→validate→report) | **COMPLETE** (engine-level) | engines: extraction → factor_matching → calculation → validation → report_generation; DOCUMENT_PIPELINE orchestrates |
| DB-backed processing queues (`processing_queue`, `report_generation_queue`, `manual_review_queue`) | **PARTIAL** | Schema exists (RC2 init); `report_generation_queue` is the v2.1 report store (D4). **No v2.1 worker process** consumes the legacy claim-queues (RC2 worker architecture 05_worker_architecture.md is target-only) |
| Human review / workflow admin transition API | **NOT IMPLEMENTED** | prep-pack R20/R22 documented only; no `/api/v2/workflow/*` routes |
| Orphan/retry recovery | **NOT IMPLEMENTED** | prep-pack R22 documented as known limitation (eventually consistent, background task suggested) |

## 14. Audit / event / lineage traceability

| Requirement | Status | Evidence |
|---|---|---|
| Audit framework (§15) — AuditEntry, AuditQuery, AuditTrail | **COMPLETE** | `domain/audit.py`; `data/audit.py` (record/query/export_csv/get_by_correlation) |
| AuditLogger decorator-based recording | **COMPLETE** | `infra/audit_logger.py`; engine callables record `validation:completed`, `report:generated`, alias writes etc. |
| Audit context / correlation propagation | **COMPLETE** | `api/dependencies.py` (get_audit_context); `api/middleware.py` (request/correlation ID); audit entries carry request_id |
| Admin audit surface (query/export/correlation/entry) | **COMPLETE** | `api/admin_audit.py` (4 routes) |
| Event platform (§14) — DomainEvent hierarchy | **COMPLETE** | `domain/workflow.py` (14 concrete events) |
| EventsRepository + domain_events table | **COMPLETE** | `data/events.py` (store/get_by_correlation/replay); M5 |
| EventBus in-process pub/sub | **COMPLETE** | `infra/event_bus.py`; unit tests (17) |
| Lineage — factor provenance on snapshots | **COMPLETE** | `calculation_snapshots` (factor_id, factor_source, factor_set, import_batch_id, request_id); emissions_logs.snapshot_id (M4) |
| Lineage — import batch provenance | **COMPLETE** | `import_batches` + `emission_factors.import_batch_id` (M1/M2); SEAI rows batch-linked |
| CO2 vs CO2e provenance (`gas_coverage`) | **COMPLETE** | validation engine `gas_coverage()`; contracts preserve `gas_coverage`; SEAI CO2-only never relabelled CO2e (pycheck9d + api tests) |
| Report lineage (12-section report carries provenance + lineage) | **COMPLETE** | `engines/report_generation.py`; pycheck9d lineage checks PASS |

---

## 15. Deviations (consolidated)

| ID | Architecture requirement | Actual state | Impact | Severity | Recommended future action | Blocks V3? |
|---|---|---|---|---|---|---|
| **D1** | `backend/providers/` plugin architecture (ProviderPlugin ABC + registry + per-provider plugins) — prep-pack §5/§8, Phase 5.1/5.2 | Absent. DEFRA/SEAI are standalone CLI pipelines under `src/providers/` + `src/commands/` writing via psycopg2 | Adding EPA/ADEME/IPCC requires new CLI pipelines rather than registering plugins; matching/calculation unaffected (they read `emission_factors` via repository) | **HIGH** | Decide in V3 IA: implement `backend/providers/` plugins vs formalise the existing CLI importer pattern | No (data + engines already multi-provider; D1 affects import ergonomics) |
| **D2** | `ImportMappingEngine` (`backend/engines/import_mapping.py`) — Phase 5.3 | Absent. Imports bypass `ImportsRepository`/event bus as an engine; the CLI importers use `import_batches` directly | Import side-effects (events, audit via engine) not unified; batch lifecycle still correctly tracked | **HIGH** | V3: decide whether to build the engine or retain CLI importers (documented prep-pack R11 gap) | No (blocked nothing for Phases 6–10) |
| **D3** | `CalculationSnapshot` provenance fields on the domain object — prep-pack §2.2 | Snapshot carries `match_request_id`/`created_at`; provenance passed to sink, not stored on the object | Cosmetic; DB coverage complete | **LOW** | Align inventory/docstring | No |
| **D4** | `ReportsRepository` over a report table — prep-pack §3.8 | Maps `GeneratedReport` to `report_generation_queue`; `page_count` in JSONB | Report store uses legacy queue table as the report table | **LOW** | V3: consider `generated_reports` table only if the queue table proves limiting | No |
| **D5** | `infra/cache.py` (TTL cache) + `infra/metrics.py` — prep-pack §5 | Neither exists. FactorSearchIndex + config serve caching; no metrics | No Prometheus metrics; caching via index | **LOW** | V3: add cache + metrics if observability is required | No |
| **D6** | Benchmarking timing — CT-ARCH-003 lists Benchmark under Future; prep pack schedules Phase 9.2 | Resolved in favour of prep pack (later, single source of truth); implemented Phase 9.2 | None (resolution recorded) | **MEDIUM (resolved)** | n/a | No |
| **D7** | Benchmark reference data | None — Phase 9 benchmarking is internal-only (computed from `emissions_logs`); approved | External/peer benchmarking impossible until reference data added | **MEDIUM (resolved by scope decision)** | V3: add reference tables only if external benchmarking is wanted | No |
| **D8** | `Facility.eircode` (RC2 column) in `domain/organization.py` | Domain Facility lacks `eircode` | IE facility reporting would need the field | **LOW** | Add field when IE facility reporting is needed | No |
| **D9** | Prep-pack §5: `main.py` is the app factory | `main.py` is the legacy app; v2.1 factory is `main_v2.py` | Two entrypoints; documented deviation | **LOW** | Keep until legacy retirement | No |
| **D10** | Prep-pack §5 shows only 5 files under `api/` | Admin endpoints split across `api/admin_*.py` (composition) | None (single router assembles them) | **LOW** | n/a | No |
| **D11** | CSV export transport | CSV body returned inside the JSON envelope (no streaming transport) | Acceptable for Phase 10.2 scope | **LOW** | Add streaming in a later phase if required | No |
| **D12** | Active-batch semantics | No active batch returns `batch: null` (200), not 404 | Valid "no data yet" state, documented in OpenAPI | **LOW** | n/a | No |
| **D13** | CT-ARCH-013: freeze legacy as `backend_legacy` | Legacy app still named `backend/main.py` + `routes/` (frozen in place, not renamed) | Legacy surface remains reachable; two apps in one repo | **MEDIUM** | V3: retire/rename legacy surface per migration plan | No |
| **D14** | Canonical pytest suite completes | Integration suite cannot run in this environment (`carbontally_test` unreachable; process hangs) | Integration-level claims rest on supplementary harnesses | **HIGH (verification gap)** | Run the canonical suite where the test DB is reachable before relying on integration claims | **Yes — V3 IA must treat integration-level evidence as unverified** |

---

## 16. Deferred / Future items

### 16.1 Deferred (explicitly postponed, no implementation)

| Item | Source | Reason / note |
|---|---|---|
| EPA provider | prep-pack Phase 12 | Not started; admin catalogue reports `deferred` |
| ADEME provider | prep-pack Phase 12 | Not started |
| IPCC provider | prep-pack Phase 12 | Not started |
| Admin import wizard (upload/validate/preview/publish) | prep-pack Phase 11 + CT-ARCH-009/010 | Phase 11 not started |
| Synonym dictionary management | CT-ARCH-009 | Phase 11 |
| Units / countries / reporting-years admin surfaces | CT-ARCH-009 | Phase 11 |
| Publish/archive factor-library workflow | CT-ARCH-009/010 | Phase 11 |
| Calculation-verification admin endpoint | prep-pack R21 | Documented, not implemented |
| Workflow admin transition / human-review endpoints | prep-pack R20/R22 | Documented, not implemented |
| ValidationEngine A10–A13 (statistical anomaly, source-document completeness, AI confidence, import-file validation) | Phase 9 contract | Explicitly out of Phase 9 scope |
| `/process/pdf`, `/process/excel`, `/process/csv` endpoints | CT-ARCH-012 examples | Engine-level capability exists; upload/processing routes not implemented |

### 16.2 Future (listed as future capability)

| Item | Source | Status |
|---|---|---|
| RecommendationEngine | CT-ARCH-003 | **FUTURE** — no code |
| AI/semantic ranking in matching | CT-ARCH-006; `SemanticMatchStage` | Implemented but `semantic_enabled=False` by default (opt-in) |
| External/peer/industry benchmarking | Phase 9 contract decision | **FUTURE** — requires reference data (D7) |
| PDF/HTML report rendering | Phase 9 contract; Phase 10 scope | **FUTURE** — structured content only; legacy `report_generator.py`/`pdf_engine.py` exist but are not wired to v2.1 |
| Prometheus metrics / observability | prep-pack §5 `infra/metrics.py` | **FUTURE** |
| Custom organisation factor libraries | CT-ARCH-007 | **NOT IMPLEMENTED** |
| v2.1 rate limiting | §19 security | **NOT IMPLEMENTED** (legacy only) |

---

## 17. Known limitations

1. **Canonical pytest cannot complete in this environment.** `pytest -q`
   (including `tests/integration`) terminates/hangs; re-confirmed this session.
   The integration conftest targets the local `carbontally_test` Postgres
   database. No integration-level pytest result exists for V2.1.
2. **Integration test suite is written but unexecuted** (21 files, ~90 tests).
   Phase 9.4 added `test_validation.py`, `test_benchmarking.py`,
   `test_report_generation.py` to that suite; they have not been run.
3. **No live read-only SQL round-trip was possible this session** — the verified
   factor baseline (7,049 / 7,029 / 20) is the recorded, cross-referenced state,
   not a fresh query.
4. **The referenced v2.1 architecture-spec documents are empty stubs** in the
   repository (`Backend_Architecture_v2.1.md`, `Architecture_Readiness_Review
   (Final Gate).md`, `Architecture_Review.md` — 0 bytes). Requirements were
   reconstructed from the FROZEN prep pack, CT-ARCH instructions and phase
   reports. The V3 IA should re-establish the authoritative spec baseline.
5. **No completed security-assessment report** — only the assessment template
   exists. Security status rests on code/RLS inspection, not a formal report.
6. **All Phase 9/10 work is uncommitted** on `main` (working-tree changes only).
   The V3 IA should not assume these files are committed/backed up.
7. **mypy strict is configured but no mypy run is recorded** for the full
   backend.
8. **No benchmark reference data** — external benchmarking is impossible until a
   reference dataset is sourced (D7).
9. **Legacy application surface remains live** (`main.py` + `routes/` ~40
   modules, legacy `report_generator.py`, `pdf_engine.py`) — the v2.1 API is an
   additive surface, not a replacement.
10. **No worker process** consumes the RC2 claim-queues; v2.1 workflow is
    in-process event-driven.

---

## 18. V2.1 current baseline

### 18.1 What is actually implemented (COMPLETE)
- **Domain:** 11 modules (`factor, calculation, document, organization, report,
  workflow, provider, matching, audit, validation, benchmarking`) — immutable
  frozen dataclasses, zero dependencies.
- **Repositories:** 9 repositories over the service-role asyncpg pool + base
  `AbstractRepository`.
- **Infrastructure:** Supabase service client + asyncpg pool, EventBus,
  FactorSearchIndex, AuditLogger, LLMClient, typed AppConfig.
- **Engines (8):** FactorMatchingEngine (6 stages), CalculationEngine (snapshots
  + hash + verify), DocumentExtractionEngine, AIExtractionEngine,
  WorkflowOrchestrator, ValidationEngine (A1–A9), BenchmarkingEngine (internal
  only), ReportGenerationEngine (12-section structured content).
- **Database (Phase 0):** migrations M1–M8 (import_batches, import_batch_id,
  calculation_snapshots, snapshot_id, domain_events, factor_aliases, dpq
  workflow columns, new-table RLS) on top of the RC2 schema.
- **API (Phase 10):** 19 routes — health, 5 business-processing endpoints, 13
  admin endpoints (imports, providers, audit, aliases); consistent error
  envelope; correlation/request IDs; JWT auth (legacy `auth.py` reused); org
  isolation; `/api/v2/docs` OpenAPI.
- **Providers:** DEFRA (7,029) and SEAI (20) factor data imported; cross-provider
  matching/calculation verified.

### 18.2 What is partially implemented
- Admin Platform: 4 of the CT-ARCH-009 surfaces (providers/import history/
  audit/aliases); import wizard, synonyms, units, countries, years,
  publish/archive missing.
- Import platform: batch lifecycle + versioning complete; no ImportMappingEngine
  (CLI importers instead).
- Security model: JWT/RBAC/RLS/audit complete; v2.1 rate limiting absent.
- Processing: engine-level pipeline complete; DB claim-queue workers absent.
- Legacy separation: legacy app frozen in place, not renamed `backend_legacy`.

### 18.3 What is deferred
- EPA, ADEME, IPCC providers; Phase 11 admin remainder; Validation A10–A13;
  `/process/*` upload endpoints; workflow/verification admin endpoints
  (R20/R21/R22).

### 18.4 What is future
- RecommendationEngine; semantic/AI ranking (opt-in); external benchmarking;
  PDF/HTML rendering; Prometheus metrics; custom organisation factor libraries.

### 18.5 Test baseline
- **pytest PASS (recorded):** unit/api (77–80 tests), unit/domain (~146),
  unit/engines (~251), unit/infra (~71), unit/test_core (14) — zero failures.
- **Supplementary harness PASS:** phase10 49/49; pycheck9d 74/74; selfcheck9c
  33/33; regression9ab 44/44; regression9c 31/31.
- **Not executed:** integration suite (21 files) — `carbontally_test` DB
  unreachable; canonical `pytest -q` terminates/hangs.

### 18.6 Database baseline
- Migrations M1–M8 present and applied to the dev database.
- `emission_factors` = **7,049** (DEFRA **7,029** GB + SEAI **20** IE,
  batch-linked, CO2-only preserved). Unchanged throughout Phases 9/10.
- RLS: RC2 policies + M8 deny-by-default/select-own policies for v2.1 tables.

### 18.7 Provider baseline
- DEFRA **COMPLETE**, SEAI **COMPLETE**, EPA/ADEME/IPCC **DEFERRED**, custom org
  libraries **NOT IMPLEMENTED**.

### 18.8 API baseline
- v2.1 surface: 19 routes, thin orchestration, no business logic duplication,
  no CRUD on the new surface, admin staff-only, org-isolated business endpoints.

### 18.9 Known architecture deviations
- D1 providers plugin architecture absent; D2 ImportMappingEngine absent; D13
  legacy not renamed; D14 integration verification gap (the only V3-blocking
  item — evidence, not code).

---

## 19. V2.1 readiness assessment for V3 impact analysis

The V2.1 baseline is **substantively complete and internally consistent** as the
authoritative input for the V3 Impact Assessment:

1. **What the V3 IA can rely on:** the domain/repository/infra/engine/API code
   inventory, the migration set (RC2 + M1–M8), the verified factor baseline
   (7,049), the recorded unit pytest results, and the 49/49 + 74/74 + 33/33
   supplementary harness evidence — all cross-checked against the working tree
   in this document.
2. **What the V3 IA must treat as open:** integration-level evidence (unrun),
   the empty architecture-spec stubs, the absence of a completed security
   assessment, and the uncommitted working-tree state.
3. **V3-blocking flag:** **D14** (integration verification gap) is the only
   item marked "blocks V3" — it is a verification gap, not a code defect; no
   requirement in the matrix is BLOCKED for code reasons.
4. **No V3 work was performed.** No V3 requirements analysis, table design,
   migration design, or recommendation of schema changes is contained in this
   document.

**V2.1 TRACEABILITY COMPLETE — READY FOR V3 IMPACT ASSESSMENT**

















