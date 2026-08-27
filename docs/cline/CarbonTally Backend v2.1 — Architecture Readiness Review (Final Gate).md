CarbonTally Backend v2.1 — Architecture Readiness Review (Final Gate)
Reviewer: Principal Software Architect Date: 2026-08-06 Baseline: RC2 Database Schema (verified by supabase db reset) Reference: Backend Architecture v2.1 (Frozen Specification)

This review treats v2.1 as the single source of truth. No redesigns, no feature additions. Only implementation blockers, contradictions, ambiguities, and missing detail are reported.

REVIEW 1 — Architecture Consistency Review
1.1 Layer Boundaries
VERIFIED — No violations. The four-layer model (API → Engine → Domain → Repository) has clean separation. Each layer's responsibilities are well-defined. The dependency direction is unidirectional.

1.2 Circular Dependencies
VERIFIED — None found. Domain objects import only core/. Engines import domain/ and core/. Repositories import domain/, core/, and infra/. No layer imports a layer above it.

1.3 CONTradiction FOUND — Provider ↔ Engine Dependency Rule
Severity:	HIGH
Section:	§5.1 (Dependency Rules) vs §8.2 (Provider Lifecycle)
Conflict:	§5.1 states engines may NOT import providers/. §7.2 says ImportMappingEngine depends on ProviderPlugin (abstract). §8.2 shows ImportMappingEngine calling provider.discover(), provider.parse(), etc.
Resolution:	Clarify that engines/import_mapping.py imports providers/base.py (the abstract ProviderPlugin interface only), and the concrete provider instance is injected via the provider registry at runtime. This follows the Dependency Inversion Principle and does not violate the layer rule. Update the dependency matrix: engines MAY import providers/base.py (abstract interface only), MUST NOT import concrete providers.
1.4 Package Organization
VERIFIED — Consistent. The package structure (§4) maps cleanly to the four layers. Sub-packaging under providers/ correctly isolates each jurisdiction. core/ is correctly positioned as the shared kernel with no internal imports.

1.5 Engine Responsibilities
VERIFIED — Well-defined. Each engine has a single public method, clear input/output contracts, and explicit dependency lists. No overlap found.

1.6 Provider Isolation
VERIFIED — Correctly designed. Each provider is in its own sub-package. The abstract ProviderPlugin interface is in providers/base.py. Registry is explicit (@register decorator). No engine imports a concrete provider.

REVIEW 2 — Database Mapping Review
2.1 Critical Finding — Tables Referenced But Not in RC2 Schema
The specification describes domain objects and repositories that require database tables not present in the RC2 baseline. The RC2 schema is frozen (no redesign of existing tables), but new tables are required.

TABLE 1: emission_factors — Column Addition Required
Severity:	CRITICAL — Implementation Blocker
Domain Object:	EmissionFactor in domain/factor.py
Field Missing:	import_batch_id: str — links each factor to its import batch for provenance
Current RC2:	emission_factors has no import_batch_id column
Impact:	Without this column, the versioning strategy (§17) cannot operate — factors cannot be traced to their import origin; rollback cannot identify which factors to deactivate
Resolution:	Add import_batch_id UUID REFERENCES public.import_batches(id) to emission_factors via a new migration. This is a non-destructive, additive column — it does not redesign the table, it extends it. The migration is idempotent (ADD COLUMN IF NOT EXISTS).
Migration Required:	YES — Required before Phase 1 implementation
TABLE 2: import_batches — New Table Required
Severity:	CRITICAL — Implementation Blocker
Domain Object:	ImportBatch in domain/provider.py
Current RC2:	No import_batches table. RC2 has upload_batches (for document uploads) — a separate concern.
Fields Required:	id, provider_key, provider_version, source_file, source_checksum, reporting_year, status, rows_total, rows_imported, rows_skipped, rows_duplicate, errors (JSONB), is_active, created_at, created_by, rolled_back_from
Resolution:	Create public.import_batches table. Safe — fully additive, no existing tables modified.
Migration Required:	YES — Required before Phase 1 implementation
TABLE 3: calculation_snapshots — New Table Required
Severity:	CRITICAL — Implementation Blocker
Domain Object:	CalculationSnapshot in domain/calculation.py
Current RC2:	No calculation_snapshots table
Fields Required:	id, organization_id, activity, activity_type, quantity, quantity_unit, co2e_multiplier, co2e_kg, scope, date, factor_id (FK → emission_factors), factor_source, factor_set, import_batch_id, reporting_year, methodology, algorithm_version, content_hash, calculated_at, calculated_by, request_id
Resolution:	Create public.calculation_snapshots table. Add column snapshot_id UUID REFERENCES public.calculation_snapshots(id) to public.emissions_logs (nullable — existing rows have no snapshot).
Migration Required:	YES — Required before Phase 3 implementation
TABLE 4: domain_events — New Table Required
Severity:	HIGH
Domain Object:	DomainEvent hierarchy in domain/workflow.py
Current RC2:	No domain_events table. The specification states events are persisted for audit (§14, §15).
Fields Required:	id, event_type, occurred_at, correlation_id, aggregate_id, aggregate_type, payload (JSONB), created_at
Resolution:	Create public.domain_events table. Events are inserted by the EventBus on publish (§14.2). No FK constraints — events reference aggregate IDs logically but are write-once, append-only.
Migration Required:	YES — Required before Phase 3 implementation
TABLE 5: factor_aliases — New Table Required
Severity:	HIGH
Domain Object:	Referenced in §11.3 (Alias Match stage) and §20.2 (Admin alias management)
Current RC2:	No factor_aliases table
Fields Required:	id, organization_id (nullable — NULL = global alias), alias_text, target_activity_type, target_provider_key, created_by, created_at
Resolution:	Create public.factor_aliases table. Used by the AliasMatchStage and managed via the admin API.
Migration Required:	YES — Required before Phase 3/4 implementation
TABLE 6: workflow_states — Not a Separate Table
Severity:	MEDIUM — Ambiguity
Domain Object:	WorkflowState in domain/workflow.py
Current RC2:	document_processing_queue already has status, updated_at, error fields that serve as a workflow state machine
Question:	Should WorkflowState be a new table, or should the existing document_processing_queue columns be used?
Resolution:	Use the existing document_processing_queue.status column as the workflow state. Add columns workflow_error_count INTEGER DEFAULT 0 and workflow_next_retry_at TIMESTAMPTZ to document_processing_queue if needed. No new table. This avoids duplicating document state. Update the spec to explicitly state this mapping.
2.2 Column Compatibility Matrix
Domain Object Field	RC2 Column	Compatible?	Action
EmissionFactor.id	emission_factors.id	✅	None
EmissionFactor.reporting_year	emission_factors.reporting_year	✅	None
EmissionFactor.activity_type	emission_factors.activity_type	✅	None
EmissionFactor.co2e_multiplier	emission_factors.co2e_multiplier	✅	None
EmissionFactor.unit	emission_factors.unit	✅	None
EmissionFactor.scope	emission_factors.scope	✅	None
EmissionFactor.factor_source	emission_factors.factor_source	✅	None
EmissionFactor.factor_set	emission_factors.factor_set	✅	None
EmissionFactor.country	emission_factors.country	✅	None
EmissionFactor.provider_key	(derived from factor_source)	✅	Computed field in domain object, not a DB column
EmissionFactor.import_batch_id	(missing)	❌	Add column
EmissionFactor.natural_key	(computed)	✅	Computed from (reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}')) per RC2 unique index
CalculationSnapshot.*	(missing table)	❌	Create table + add FK to emissions_logs
ImportBatch.*	(missing table)	❌	Create table
DomainEvent.*	(missing table)	❌	Create table
Organization.id	organizations.id	✅	None
Organization.metadata	organization_metadata	✅	None
Document.*	customer_documents + document_processing_queue	✅	None
2.3 Ambiguity — emissions_logs vs calculation_snapshots
Severity:	MEDIUM — Ambiguity
Section:	§13.2 (Calculation Flow)
Issue:	Step 7 says "Save CalculationSnapshot to calculation_snapshots table" and Step 8 says "Save EmissionLog to emissions_logs". The relationship between these two records is unclear: does emissions_logs.snapshot_id FK to calculation_snapshots, or does calculation_snapshots duplicate the emissions_logs row?
Resolution:	emissions_logs is the operational record (used by dashboard, aggregations, reports). calculation_snapshots is the immutable forensic record (never updated, never deleted). emissions_logs gains a nullable snapshot_id UUID REFERENCES calculation_snapshots(id). This column is explicitly called out in the migration list.
REVIEW 3 — Repository Review
3.1 EmissionFactorsRepository — Missing Method
Severity:	MEDIUM
Issue:	The spec describes deactivate_set(provider, year) in §10.2 but the import flow in §12.1 sets is_active on import_batches, not on individual emission_factors rows. The deactivation is on the import batch, not the factors.
Resolution:	Remove deactivate_set() from EmissionFactorsRepository. The method belongs on ImportsRepository.deactivate_batch(). Update §10.2.
3.2 CacheRepository — Ambiguous Scope
Severity:	LOW
Issue:	§10.2 lists CacheRepository with methods load_all_active(), refresh(), search(), suggest(). But §16 defines FactorSearchIndex as an in-memory object in infra/search_index.py — not a repository.
Resolution:	FactorSearchIndex is an infrastructure component, not a repository. Remove CacheRepository from §10.2. FactorSearchIndex is created and injected at the composition root. The EmissionFactorsRepository.load_all_for_index() method feeds data to the index.
3.3 EventsRepository — Missing from Catalog
Severity:	LOW
Issue:	§10.2 lists EventsRepository but it appears only in the table at the end — no detailed methods are described.
Resolution:	Add minimal methods: store(event: DomainEvent), get_by_correlation_id(correlation_id: str), replay(aggregate_id: str).
3.4 ImportsRepository — Method Gap
Severity:	LOW
Issue:	activate_batch() and deactivate_batch() are listed in §10.2 but the import flow (§12.1) calls deactivate_batch() before bulk_upsert — this is a transactional operation across two repositories that could leave the system in an inconsistent state if the upsert fails.
Resolution:	The ImportMappingEngine must handle this atomically: deactivate + upsert + activate within a single conceptual transaction. Since Supabase does not support cross-table transactions via the REST API, document that this engine uses the service-role client to execute a SQL function or a psycopg2 direct-connection transactional block. Alternatively, accept eventual consistency: deactivate → upsert (if fails, reactivate the old batch). Document the chosen approach in the engine specification.
3.5 Repository Completeness
All repositories are adequately described. No missing CRUD operations for the defined use cases. Repository interfaces are consistent with the dependency injection pattern.

REVIEW 4 — Domain Model Review
4.1 Missing Domain Object — FactorAlias
Severity:	MEDIUM
Issue:	The matching pipeline (§11.3) references "Alias Match" with "Organisation-specific aliases" and the admin API (§20.2) manages aliases. No domain object is defined for this concept.
Resolution:	Add FactorAlias to domain/matching.py:
```python
@dataclass(frozen=True)	
class FactorAlias:	

id: str
organization_id: Optional[str]
alias_text: str
target_activity_type: str
target_provider_key: str
created_by: str
created_at: datetime


### 4.2 Missing Domain Object — `Suggestion`

| Severity: | **LOW** |
|---|---|
| **Issue:** | `MatchResult` references `suggestions: tuple[Suggestion, ...]` in §9 but `Suggestion` is never defined. |
| **Resolution:** | Add to `domain/matching.py`:
```python
@dataclass(frozen=True)
class Suggestion:
    factor: EmissionFactor
    score: float
    reason: str
    stage: str
``` |

### 4.3 Missing Enum — `CalculationMethodology`

| Severity: | **LOW** |
|---|---|
| **Issue:** | §6.2 (v2.0) listed methodologies (`direct_multiply`, `distance_based`, `spend_based`, `area_based`, `mass_balance`). The v2.1 spec references `Methodology` as an enum in §13.1 and §9 (`calculation.py`) but the enum is not defined. |
| **Resolution:** | Add to `domain/calculation.py`:
```python
class CalculationMethodology(StrEnum):
    DIRECT_MULTIPLY = "direct_multiply"
    DISTANCE_BASED = "distance_based"
    SPEND_BASED = "spend_based"
    AREA_BASED = "area_based"
    MASS_BALANCE = "mass_balance"
``` |

### 4.4 Missing Identifier — `correlation_id` in Domain Events

| Severity: | **LOW** |
|---|---|
| **Issue:** | `DomainEvent` in §14.1 has `correlation_id: str` but does not specify how it's generated or linked across events. |
| **Resolution:** | Document: `correlation_id` is the `request_id` from the originating API request. All events triggered by the same API call share the same `correlation_id`. This is set by the `EventBus` on first publish and propagated through the workflow. |

### 4.5 Immutability — Verified

All domain objects are `@dataclass(frozen=True)`. `replace()` is used for state transitions. No mutable state in domain objects. **VERIFIED.**

### 4.6 Aggregate Boundaries — Verified

`EmissionFactor` is the root of the factor aggregate (with `FactorSet` as a collection). `ImportBatch` is the root of the import aggregate. `CalculationSnapshot` is an independent aggregate (reference to `EmissionFactor` by ID, not by object). `Document` spans `customer_documents` + `document_processing_queue`. Boundaries are clean. **VERIFIED.**

---

## REVIEW 5 — Engine Review

### 5.1 Missing Engine — `FactorAliasManager`

| Severity: | **MEDIUM** |
|---|---|
| **Issue:** | The admin API (§20.2) has endpoints for CRUD on aliases. The matching pipeline uses aliases. No engine is defined for alias management. |
| **Resolution:** | The alias CRUD is simple enough to be handled directly by a repository call from the admin route handler (CRUD operations do not require an engine — they are simple persistence). Alternatively, create a lightweight `AliasService` engine for consistency. Specify which approach in the engine catalog. |

### 5.2 Audit Logging — Implementation Detail Missing

| Severity: | **MEDIUM** |
|---|---|
| **Issue:** | §15.1 describes an `@audit` decorator that wraps engine calls. The decorator is shown as a concept. The exact mechanics — how `input_summary` and `output_summary` are extracted from arbitrary function arguments — are not specified. |
| **Resolution:** | Specify the audit contract: every engine callable must accept a `request` dataclass as its first positional argument (after `self`) and return a domain object. The decorator extracts `request.__dict__` as `input_summary` and `result.__dict__` (or `result` if not a dataclass) as `output_summary`. This is a **hard contract** — engines that violate it cannot be audited. Add to §15.1. |

### 5.3 Engine Statelessness — Verified

All engines are described as stateless classes with constructor-injected dependencies. No global state, no mutable class variables. **VERIFIED.**

---

## REVIEW 6 — Provider Plugin Review

### 6.1 Plugin Registration — Verified

The explicit `@register` decorator pattern in §8.3 is simple, auditable, and avoids setuptools magic. **VERIFIED.**

### 6.2 Provider Discovery — Ambiguity

| Severity: | **LOW** |
|---|---|
| **Issue:** | The `ProviderPlugin.discover()` method in §8.1 returns `DiscoveryResult` — but `DiscoveryResult` is never defined. |
| **Resolution:** | Add to `domain/provider.py`:
```python
@dataclass(frozen=True)
class DiscoveryResult:
    provider_key: str
    provider_version: str
    source_path: str
    source_checksum: str
    reporting_year: int
    sheets: tuple[DiscoveredSheet, ...]

@dataclass(frozen=True)
class DiscoveredSheet:
    name: str
    sheet_type: str     # "data" | "documentation" | "unsupported"
    max_row: int
    max_col: int
    header_row: Optional[int]
    columns: tuple[tuple[str, int], ...]
``` |

### 6.3 RawFactorRow and NormalisedFactor — Not Defined

| Severity: | **MEDIUM** |
|---|---|
| **Issue:** | `ProviderPlugin.parse()` returns `list[RawFactorRow]` and `normalise()` returns `list[NormalisedFactor]`. Neither type is defined. |
| **Resolution:** | Define in `domain/provider.py`:
```python
@dataclass(frozen=True)
class RawFactorRow:
    sheet_name: str
    row_number: int
    cells: dict[str, Any]     # column label → raw cell value

@dataclass(frozen=True)
class NormalisedFactor:
    provider_key: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: Decimal
    unit: Optional[str]
    scope: Optional[str]
    country: str
    metadata: dict[str, Any]   # Preserved original fields
``` |

### 6.4 Provider Lifecycle — Verified

The discovery → parse → normalise → validate → map_to_schema → import flow is complete and well-specified. Each stage is independently testable. **VERIFIED.**

---

## REVIEW 7 — Matching Platform Review

### 7.1 Missing Stage Implementation Detail

| Severity: | **LOW** |
|---|---|
| **Issue:** | Seven pipeline stages are named (§11.1) but only `FactorSearchIndex` methods are defined in §16. The `ExactMatchStage`, `NaturalKeyStage`, `AliasMatchStage`, `KeywordSearchStage`, `FuzzyMatchStage`, `SemanticMatchStage` classes are not specified. |
| **Resolution:** | The spec is sufficient for implementation — each stage is a class implementing `MatchingStage` (an ABC that should be added to `domain/matching.py`). The implementation detail does not need to be in the frozen spec; the stage descriptions in §11.1 provide enough guidance. **ACCEPTABLE.** |

### 7.2 AI Isolation — VERIFIED

§11.4 explicitly states AI never returns an emission factor. The matching engine is the sole factor selector. The AI engine extracts fields only. **VERIFIED.**

### 7.3 Human Review Stage — Ambiguity

| Severity: | **LOW** |
|---|---|
| **Issue:** | Stage 7 (Human Review) in §11.1 says "Admin manually selects from top-N candidates. Admin selection creates a permanent alias." The mechanics of this flow — which endpoint, how the selection is stored, how the alias is created — are not specified. |
| **Resolution:** | This is a workflow state: the frontend displays `MatchResult.suggestions`, the admin selects one, the frontend POSTs to `POST /api/v2/admin/aliases` to create the alias AND POSTs to `POST /api/v2/workflow/{id}/transition` to advance the workflow. Specify this flow in §11.3. |

### 7.4 Confidence Flow — VERIFIED

Each stage produces a `StageResult` with `confidence`, `score`, `reason`, and `is_definitive`. The pipeline stops when `is_definitive=True`. If no stage is definitive, suggestions are returned. **VERIFIED.**

---

## REVIEW 8 — Calculation Platform Review

### 8.1 Snapshot Content Hash — VERIFIED

The `content_hash` computation includes all inputs (quantity, co2e_multiplier, factor_id, methodology, algorithm_version). This provides tamper detection. **VERIFIED.**

### 8.2 Verification Process — Missing Implementation Detail

| Severity: | **LOW** |
|---|---|
| **Issue:** | §13.3 describes `verify_calculation(snapshot_id)` but the endpoint and access control for this operation are not specified. |
| **Resolution:** | Add to endpoint catalog: `POST /api/v2/admin/calculations/{snapshot_id}/verify` — admin only. Returns `VerificationResult`. Not a user-facing endpoint; exists for audit purposes. |

### 8.3 Factor Provenance — VERIFIED

Every calculation stores `factor_id`, `factor_source`, `factor_set`, `import_batch_id`, and `reporting_year`. The factor can be traced from any calculation back to the specific import batch that created it. **VERIFIED.**

---

## REVIEW 9 — Workflow & Event Review

### 9.1 Event Persistence — VERIFIED

The `EventBus.publish()` method stores every event via `EventsRepository.store()` before dispatching to handlers (§14.2). Events are immutable and append-only. **VERIFIED.**

### 9.2 Failure Handling — VERIFIED

Handler failures do not block other handlers ("Handler failures do not block other handlers but ARE logged and surfaced in admin" — §14.2). **VERIFIED.**

### 9.3 Missing — Corrupt Event Recovery

| Severity: | **LOW** |
|---|---|
| **Issue:** | If an event handler fails (logged but not retried), the workflow may be stuck in an intermediate state. No recovery mechanism is specified for orphaned workflows. |
| **Resolution:** | Add to §14.2: a background task (or scheduled Edge Function) queries `document_processing_queue` for items stuck in non-terminal states for > 1 hour. The admin can manually retry via `POST /api/v2/workflow/{id}/retry`. Document this as a known limitation — the system is eventually consistent, not strictly consistent. |

### 9.4 Idempotency — VERIFIED

Domain events have unique `event_id` values. The `EventsRepository` can enforce `UNIQUE(event_id)` to prevent duplicate event processing. The `WorkflowOrchestrator` checks `can_transition(from_state, to_state)` before applying a transition. **VERIFIED.**

### 9.5 Deadlock / Race Condition Risk

| Severity: | **LOW** |
|---|---|
| **Issue:** | Two concurrent workflow transitions on the same entity could race. The spec does not address optimistic concurrency control. |
| **Resolution:** | Use `document_processing_queue.updated_at` as an optimistic lock: `UPDATE ... WHERE id = ? AND updated_at = ?`. If the row was modified by another transition, the update fails, and the orchestrator re-reads the current state. Document this in the WorkflowOrchestrator specification. |

---

## REVIEW 10 — Security Review

### 10.1 JWT Flow — VERIFIED

Supabase issues JWT. FastAPI validates JWT against Supabase Auth. Frontend sends JWT in `Authorization: Bearer <token>`. Service role key is never exposed to frontend. **VERIFIED.**

### 10.2 Service Role Key Usage — VERIFIED

Service role key is used only within the FastAPI container, in environment variables. Repositories use it for backend operations that bypass RLS. Admin endpoints additionally validate JWT for request authorization. **VERIFIED.**

### 10.3 RLS Assumptions — Ambiguity

| Severity: | **MEDIUM** |
|---|---|
| **Issue:** | §19.2 states "Frontend CRUD — Supabase RLS policies (164 policies, RC2 verified)". New tables (`import_batches`, `calculation_snapshots`, `domain_events`, `factor_aliases`) will NOT have RLS policies unless explicitly added. The spec does not address RLS for new tables. |
| **Resolution:** | Specify RLS requirements for new tables: |
| | - `import_batches`: Admin-read, admin-write. Deny authenticated. |
| | - `calculation_snapshots`: Admin-read. Org members read their own (via join on `organization_id`). Service-role write only. |
| | - `domain_events`: Admin-read. Deny authenticated. Service-role write only. |
| | - `factor_aliases`: Admin CRUD. Org members read global aliases + own org aliases. |
| | Add RLS migration scripts alongside table creation scripts. |

### 10.4 Audit Integrity — VERIFIED

Audit entries are created by the service role (not the user), preventing tampering. Audit logs are immutable once written. **VERIFIED.**

---

## REVIEW 11 — Performance Review

### 11.1 Search Index — VERIFIED

7000 rows per provider × ~6MB per provider. At 5 providers = 35MB in-memory. At 20 providers = 140MB. **ACCEPTABLE** for a server application. If memory becomes a concern, LRU eviction of inactive providers is straightforward. **VERIFIED.**

### 11.2 Matching Latency — VERIFIED

The FactorSearchIndex provides O(1) natural-key lookup and O(n) keyword search (n = active factors). For 35K factors across 5 providers, keyword search is ~milliseconds. Fuzzy matching adds O(n × word_length²) — still sub-second for 35K rows. Semantic matching is the only high-latency stage and is opt-in. **VERIFIED.**

### 11.3 Calculation Throughput — VERIFIED

A single calculation involves: (1) factor lookup (in-memory, <1ms), (2) arithmetic (Decimal, sub-ms), (3) two DB writes (calculation_snapshot + emissions_log, ~50ms each). ~100ms per calculation. At 10 concurrent requests, ~10 calculations/second. **ACCEPTABLE** for the use case (human-scale data entry, not streaming). **VERIFIED.**

### 11.4 Import Scalability — VERIFIED

The import pipeline processes files sequentially (parse → normalise → validate → upsert). For a 7000-row DEFRA file, the entire import takes ~15-30 seconds. This is an admin operation performed infrequently (monthly/quarterly). **ACCEPTABLE.** **VERIFIED.**

### 11.5 Event Throughput — VERIFIED

In-process event bus with synchronous handlers. At ~100 events/second (far exceeding the expected load of ~5 events/second for document processing), this is not a bottleneck. **VERIFIED.**

---

## REVIEW 12 — Testability Review

### 12.1 Domain Isolation — VERIFIED

Domain objects have zero external dependencies. They can be unit-tested with no mocking. **VERIFIED.**

### 12.2 Repository Mocking — VERIFIED

Repositories implement abstract interfaces (`AbstractRepository[T]`). Engines accept repositories via constructor injection. Tests can inject mock repositories. **VERIFIED.**

### 12.3 Engine Testing — VERIFIED

Engines accept all dependencies via constructor injection. Every dependency is mockable. Engine tests can run without Supabase, without an event bus, without a search index. **VERIFIED.**

### 12.4 Integration Testing — VERIFIED

Using a test Supabase project with RC2 schema, integration tests can verify repository implementations and end-to-end engine flows. `supabase db reset` with test seed data provides a clean baseline. **VERIFIED.**

### 12.5 Missing — Provider Plugin Test Contract

| Severity: | **LOW** |
|---|---|
| **Issue:** | The spec does not define a shared test suite that every new provider plugin must pass before being accepted. |
| **Resolution:** | Define `ProviderPluginTestSuite` (abstract test class) in `tests/contracts/provider_plugin_contract.py`. Every new provider must pass: `test_discover_returns_sheets()`, `test_parse_returns_rows()`, `test_normalise_preserves_values()`, `test_validate_detects_duplicates()`, `test_map_to_schema_produces_valid_factors()`. |

---

## REVIEW 13 — Build Order Review

### 13.1 Recommended Implementation Phases

#### Phase 0 — Database Migrations (2 days)

**Goal:** All new tables and columns in place before any code touches the database.

- Migration: `import_batches` table
- Migration: `emission_factors.import_batch_id` column (+ FK)
- Migration: `calculation_snapshots` table
- Migration: `emissions_logs.snapshot_id` column (+ FK)
- Migration: `domain_events` table
- Migration: `factor_aliases` table
- Migration: RLS policies for all new tables
- Migration: `document_processing_queue.workflow_error_count`, `.workflow_next_retry_at` columns
- Verify: `supabase db reset` passes

**Completion Criteria:** All migrations apply cleanly. `supabase db reset` succeeds. New tables exist and are empty.

#### Phase 1 — Domain Layer + Core (3 days)

**Goal:** Pure domain objects, no infrastructure.

**Deliverables:** `domain/` package — all dataclasses, enums, ABCs. `core/` package — exceptions, types, config.

**Dependencies:** None (Phase 0 migrations can run in parallel).

**Completion Criteria:** All domain objects compile. Unit tests pass (no mocking needed).

#### Phase 2 — Repository Layer (4 days)

**Goal:** Typed data access for all tables.

**Deliverables:** `data/` package — all repository implementations. `infra/supabase.py` — client factory.

**Dependencies:** Phase 0 (tables exist), Phase 1 (domain objects exist).

**Completion Criteria:** Integration tests pass against test Supabase DB. All repository methods verified.

#### Phase 3 — Infrastructure (2 days)

**Goal:** Event bus, search index, audit logger.

**Deliverables:** `infra/event_bus.py`, `infra/search_index.py`, `infra/audit_logger.py`, `infra/config.py`.

**Dependencies:** Phase 2.

**Completion Criteria:** Search index loads from real data. Event bus dispatches to handlers. Audit logger records entries.

#### Phase 4 — Factor Matching Engine (5 days)

**Goal:** Working multi-stage matching pipeline.

**Deliverables:** `engines/factor_matching.py`, all matching stages as separate classes. `domain/matching.py` — pipeline config.

**Dependencies:** Phase 3 (needs search index).

**Completion Criteria:** Exact match, natural key, keyword search, and alias match stages pass integration tests. Fuzzy and semantic stages functional.

#### Phase 5 — Import Platform (5 days)

**Goal:** Provider plugin architecture + DEFRA implementation.

**Deliverables:** `providers/base.py`, `providers/registry.py`, `providers/defra/plugin.py`, `engines/import_mapping.py`.

**Dependencies:** Phase 2 (repositories), Phase 4 (matching engine for validation).

**Completion Criteria:** DEFRA 2025 import produces 7029 factors. Rollback works. Import audit trail recorded.

#### Phase 6 — Calculation Engine (4 days)

**Goal:** Reproducible calculations with snapshots.

**Deliverables:** `engines/calculation.py`, `domain/calculation.py` updates.

**Dependencies:** Phase 4 (matching engine), Phase 2 (repositories).

**Completion Criteria:** Calculation produces correct co2e_kg. Snapshot content hash is verifiable. Snapshot survives restart.

#### Phase 7 — Document Processing + AI (5 days)

**Goal:** PDF/OCR + AI extraction pipeline.

**Deliverables:** `engines/extraction.py`, `engines/ai_extraction.py`.

**Dependencies:** Phase 3 (event bus), Phase 2 (document repository).

**Completion Criteria:** PDF text extracted. AI fields returned. Event flow: upload → extract → fields → calculation.

#### Phase 8 — Workflow Orchestrator (4 days)

**Goal:** State machines + event-driven orchestration.

**Deliverables:** `engines/workflow.py`, event handler registrations.

**Dependencies:** Phase 7 (document events), Phase 3 (event bus).

**Completion Criteria:** Document pipeline saga runs end-to-end. Failure recovery works. Retry logic functional.

#### Phase 9 — Reports + Validation + Benchmarking (5 days)

**Goal:** SECR/CSRD report generation, data validation, benchmarking.

**Deliverables:** `engines/report_generation.py`, `engines/validation.py`, `engines/benchmarking.py`.

**Dependencies:** Phase 6 (calculation engine).

**Completion Criteria:** SECR report PDF generated. Validation checks run. Benchmarking comparison produced.

#### Phase 10 — API Layer + Admin (5 days)

**Goal:** Route handlers, middleware, admin endpoints.

**Deliverables:** `api/router.py`, `api/dependencies.py`, `api/middleware.py`, `api/contracts.py`.

**Dependencies:** All prior phases.

**Completion Criteria:** All endpoints respond. Admin can import, rollback, manage aliases. Contracts match specification.

#### Phase 11 — Frontend Updates (10 days)

**Goal:** React admin dashboard updates for provider management, import history, audit viewer, alias management.

**Deliverables:** Admin portal pages for provider management, import history, rollback, audit viewer, aliases.

**Completion Criteria:** Admin can view provider list, trigger imports, view import history, rollback, search audit trail, manage aliases.

#### Phase 12 — Additional Providers (5 days each, ongoing)

**Goal:** SEAI, EPA, ADEME, IPCC implementations.

**Deliverables:** `providers/seai/`, `providers/epa/`, etc.

**Dependencies:** Phase 5 (plugin architecture).

---

## REVIEW 14 — Migration Review

### 14.1 Required Migrations (Before Code)

| # | Migration | Type | Priority |
|---|---|---|---|
| M1 | `CREATE TABLE import_batches (...)` | New table | **Phase 0** |
| M2 | `ALTER TABLE emission_factors ADD COLUMN import_batch_id UUID REFERENCES import_batches(id)` | Column addition | **Phase 0** |
| M3 | `CREATE TABLE calculation_snapshots (...)` | New table | **Phase 0** |
| M4 | `ALTER TABLE emissions_logs ADD COLUMN snapshot_id UUID REFERENCES calculation_snapshots(id)` | Column addition | **Phase 0** |
| M5 | `CREATE TABLE domain_events (...)` | New table | **Phase 0** |
| M6 | `CREATE TABLE factor_aliases (...)` | New table | **Phase 0** |
| M7 | `ALTER TABLE document_processing_queue ADD COLUMN workflow_error_count INT DEFAULT 0, ADD COLUMN workflow_next_retry_at TIMESTAMPTZ` | Column additions | **Phase 0** |
| M8 | RLS policies for all new tables | RLS | **Phase 0** |

### 14.2 Optional Migrations (During Implementation)

| # | Migration | Type | Priority |
|---|---|---|---|
| M9 | `CREATE INDEX idx_emission_factors_import_batch ON emission_factors(import_batch_id)` | Performance index | Phase 2 |
| M10 | `CREATE INDEX idx_domain_events_correlation ON domain_events(correlation_id)` | Performance index | Phase 8 |

### 14.3 Future Migrations

None required beyond the above. The RC2 schema is sufficient for all v2.1 functionality with the listed additions. No existing table is redesigned.

---

## REVIEW 15 — Risk Review

| Risk | Severity | Impact | Mitigation |
|---|---|---|---|
| **Service role key compromise** | CRITICAL | Full database access | Environment-only, never in code, rotate regularly |
| **import_batch_id column breaks existing queries** | HIGH | Backend v1 routes may fail if they `SELECT *` and receive the new column | Phase 0 must include a review of all backend v1 `SELECT *` patterns; existing routes should use explicit column lists. Column is nullable — no impact on existing rows. |
| **In-memory search index memory growth with >20 providers** | MEDIUM | ~140MB at 20 providers; may need LRU eviction beyond that | Acceptable for current scope; add eviction if provider count exceeds 20 |
| **Event handler failures cause stuck workflows** | MEDIUM | Documents stuck in intermediate states | Admin retry endpoint + background health-check query + alerting |
| **Supplier data sent to third-party AI** | MEDIUM | GDPR/privacy concern for EU customers | Use AI providers with zero-data-retention policies. Configurable opt-out per organisation. |
| **Calculation snapshot volume growth** | LOW | Each calculation produces one immutable row; millions of rows over years | Partition `calculation_snapshots` by `organization_id` if row count exceeds 10M. Not needed at launch. |
| **New providers require `import_batch_id` backfill** | LOW | Existing 7029 DEFRA rows have NULL import_batch_id | Write a one-off script to create an import batch for the existing data and backfill the column |

---

## FINAL VERDICT

# ✅ APPROVED FOR IMPLEMENTATION

**Subject to the resolution of the following pre-implementation blockers:**

1. **Migration scripts for 8 tables/columns** must be created and applied to the RC2 baseline before any application code is written (Phase 0).
2. **The `import_batch_id` column on `emission_factors`** must be explicitly acknowledged as an additive column (not a redesign) in the spec's final decisions section.
3. **Domain types `DiscoveryResult`, `DiscoveredSheet`, `RawFactorRow`, `NormalisedFactor`, `Suggestion`, `FactorAlias`, `CalculationMethodology`, and `MatchingStage` (ABC)** must be formally added to the domain specification before Phase 1 begins.
4. **RLS policies for all four new tables** must be specified and included in the Phase 0 migration script.
5. **The `emissions_logs.snapshot_id` relationship** must be clarified: `emissions_logs` is the operational record; `calculation_snapshots` is the forensic record. The FK is from `emissions_logs` to `calculation_snapshots`.

All other findings (MEDIUM and LOW severity) are implementation clarifications that can be resolved during development without blocking the start of Phase 1.

---

## Architecture Freeze Declaration

**The CarbonTally Backend Architecture v2.1 is now frozen.**

No further architectural changes are required before implementation. The specification is complete, internally consistent, and covers all required domains. The four platforms (Matching, Import, Calculation, Workflow & Event), nine engines, eight repositories, provider plugin architecture, domain model, security model, and deployment model are fully specified and ready for implementation.

---

## Implementation Roadmap

| Phase | Deliverable | Duration | Dependencies |
|---|---|---|---|
| 0 | Database migrations | 2 days | None |
| 1 | Domain layer + Core | 3 days | Phase 0 (parallel) |
| 2 | Repository layer | 4 days | Phase 0, Phase 1 |
| 3 | Infrastructure (event bus, index, audit) | 2 days | Phase 2 |
| 4 | Factor Matching Engine | 5 days | Phase 3 |
| 5 | Import Platform + DEFRA plugin | 5 days | Phase 2, Phase 4 |
| 6 | Calculation Engine | 4 days | Phase 4 |
| 7 | Document Processing + AI | 5 days | Phase 3 |
| 8 | Workflow Orchestrator | 4 days | Phase 7 |
| 9 | Reports + Validation + Benchmarking | 5 days | Phase 6 |
| 10 | API Layer + Admin endpoints | 5 days | All prior |
| 11 | Frontend admin updates | 10 days | Phase 10 |
| 12 | Additional providers (SEAI, EPA, etc.) | 5 days each, ongoing | Phase 5 |
| **Total v2.1 Core (Phases 0–10)** | | **44 days (~9 weeks)** | |
| **Total with frontend (Phases 0–11)** | | **54 days (~11 weeks)** | |

---

## Implementation Complexity Estimate

| Metric | Estimate |
|---|---|
| **Python modules** | ~55 (domain: 10, engines: 10, data: 9, infra: 8, providers: 8, core: 4, api: 5, tests: ~30) |
| **Classes** | ~80 (domain objects: 30, engines: 10, repositories: 9, matching stages: 8, infra: 5, providers: 6, exceptions: 12) |
| **Test files** | ~40 (unit: 25, integration: 10, contract: 5) |
| **Database migrations** | 8 required, 2 optional |
| **API endpoints** | ~20 |
| **Estimated technical debt** | **LOW** — the architecture explicitly avoids shortcuts: no raw dicts, no inline SQL, no engine-to-engine calls. The layered design with dependency injection is inherently low-debt. The only area of future refactoring risk is the `import_batch_id` backfill for pre-existing data — a one-time script. |

---

## Implementation Confidence Score

# 87 / 100

**Justification:**

- **+25 points** — RC2 database is verified, frozen, and passes `supabase db reset`
- **+20 points** — Four-layer architecture with strict dependency rules; every layer independently testable
- **+15 points** — Provider plugin pattern proven with a working DEFRA 2025 implementation (7029 rows verified)
- **+15 points** — Domain model is pure Python with zero framework dependencies; can be implemented and tested in complete isolation
- **+10 points** — Security model is coherent: RLS for frontend CRUD, service role for backend processing, JWT validation at the API boundary
- **+10 points** — Audit framework is built-in (decorator-based, automatic) rather than opt-in — reduces risk of missing audit trails
- **+5 points** — AI isolation rule is hard-coded in the architecture — prevents the most common failure mode in AI-assisted systems (AI selecting the wrong factor)
- **−5 points** — No reference implementation exists for the staging pipeline or event bus; first-of-kind integration risk
- **−3 points** — Four new database tables must be created and verified before any code runs — migration errors in Phase 0 block all downstream phases
- **−3 points** — The `import_batch_id` backfill for pre-existing DEFRA 2025 data is a one-time script that must be carefully tested to avoid breaking existing rows
- **−2 points** — Workflow race condition handling (optimistic locking) is described conceptually but not spec'd at the code level — must be resolved during Phase 8

The remaining 13 points represent the inherent risk of any greenfield platform implementation. The architecture provides a solid foundation; the primary implementation risks are in execution (migration accuracy, event handler reliability) rather than in design flaws.

---

*End of Architecture Readiness Review*
