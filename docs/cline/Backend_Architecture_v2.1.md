CarbonTally Backend Architecture v2.1 — Frozen Specification
Version: 2.1.0 Status: FROZEN — Implementation Reference Date: 2026-08-06 Author: Principal Software Architect Replaces: Backend v2.0 Technical Architecture Specification Database Baseline: RC2 (supabase db reset ✅, emission_factors schema verified)

Table of Contents
Architecture Overview
Design Principles
Component & Layer Diagrams
Package Structure
Dependency Rules
The Four Platforms
Processing Engines — Detailed Specifications
Provider Plugin Architecture
Domain Model
Repository Architecture
Matching Platform
Import Platform
Calculation Platform
Workflow & Event Platform
Audit Framework
Factor Search Index
Versioning Strategy
Caching Strategy
Security Model
Admin Platform
Coding Standards
Architecture Decision Records
Future Expansion Strategy
Risks & Trade-offs
Migration Notes from v2.0
1. Architecture Overview
1.1 Core Thesis
CarbonTally is a multi-provider carbon accounting platform where Supabase is the Backend-as-a-Service and FastAPI is the Business Processing Engine. The architecture must survive 10+ years, support unlimited emission-factor providers across every jurisdiction, and satisfy enterprise SaaS, ISO-audit, investor, and government grant requirements.

1.2 Layered Architecture (4-layer)

┌─────────────────────────────────────────────────────────┐
│  API Layer                                              │
│  Thin controllers. Validate input, delegate to engine,  │
│  return response. No business logic. No Supabase calls. │
│  ~50 lines per endpoint maximum.                         │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│  Engine Layer (Processing Engines)                      │
│  Pure business logic. Stateless. Orchestrates domain    │
│  objects. Never touches Supabase directly.               │
│  Depends on: Domain + Repositories (injected).          │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│  Domain Layer                                           │
│  Rich business objects with encapsulated behaviour.     │
│  No database dependencies. No framework imports.        │
│  Pure Python. Fully testable in isolation.              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│  Repository Layer                                       │
│  Typed data-access contracts (abstract interfaces).     │
│  Implementations use Supabase service-role client.      │
│  One repository per aggregate root or table group.      │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│  Infrastructure                                         │
│  Supabase client (service role), event bus, cache,      │
│  search index, API clients (LLM), config, logging.      │
└─────────────────────────────────────────────────────────┘
1.3 The Four Platforms
The system is organised into four self-contained platforms, each independently deployable as a Python package:

Platform	Purpose	Key Abstractions
Matching Platform	Provider-agnostic factor matching	MatchingPipeline, FactorSearchIndex, MatchResult
Import Platform	Version-controlled factor imports	ImportOrchestrator, ProviderPlugin, ImportBatch
Calculation Platform	Reproducible emissions calculations	CalculationEngine, CalculationSnapshot, Methodology
Workflow & Event Platform	Async orchestration + domain events	EventBus, WorkflowOrchestrator, Saga
2. Design Principles
Principle 1: Provider Agnosticism
Every emission-factor provider (DEFRA, SEAI, EPA, ADEME, IPCC, custom) is treated identically through a plugin interface. The core engine never contains provider-specific code. Adding a new provider requires only a new plugin implementation — zero changes to the matching, calculation, or reporting engines.

Principle 2: Immutable Data
Emission factors are never overwritten. Every import creates a versioned batch. Every calculation snapshots the factor used. Auditors can re-run any calculation from 2026 in 2036 and get the identical result.

Principle 3: Domain Over Database
Business logic lives in domain objects, not in SQL, not in stored procedures, and not in Supabase policies. The database is a persistence detail — the domain model is the truth.

Principle 4: Thin Contracts, Rich Domain
Route handlers are maximally 50 lines. Business logic lives in engines and domain objects. Repositories have typed, explicit interfaces. No dict returns — every return type is a dataclass.

Principle 5: Events for Decoupling
Engines do not call each other directly. Domain events are published after significant actions. Handlers subscribe to events. Adding a new side effect (e.g., "send Slack notification on calculation error") requires only a new event handler — zero changes to the calculation engine.

Principle 6: Audit by Default
Every engine action is automatically logged: input, output, processing time, confidence, engine version, decision rationale, and request ID. The audit trail is immutable. Nothing is opt-in.

Principle 7: AI Assists, Does Not Decide
AI extracts structured fields from unstructured documents. The Matching Engine — with deterministic, auditable logic — chooses the emission factor. AI never selects or returns a factor directly.

Principle 8: 10-Year Maintainability
Dependencies are standard, well-documented, and version-pinned. No "clever" metaprogramming. Every architectural decision has a written ADR. A developer joining in 2031 can understand the system from these documents.

3. Component & Layer Diagrams
3.1 Top-Level Component Diagram

┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                           │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Customer Portal  │  │ Admin Platform   │                     │
│  └────────┬─────────┘  └────────┬─────────┘                     │
│           │    @supabase/supabase-js   │                         │
└───────────┼───────────────────────────┼─────────────────────────┘
            │                           │
   ┌────────▼──────────┐     ┌──────────▼──────────┐
   │  CRUD (RLS)       │     │  Processing (JWT)   │
   │  Direct to        │     │  POST /api/v2/*     │
   │  Supabase         │     │  FastAPI            │
   └────────┬──────────┘     └──────────┬──────────┘
            │                           │
┌───────────▼───────────────────────────▼─────────────────────────┐
│                     Supabase Platform                             │
│  ┌──────────┐ ┌───────┐ ┌──────────┐ ┌───────┐ ┌─────────────┐ │
│  │ Auth     │ │Storage│ │ Realtime │ │  DB   │ │ Edge Fns    │ │
│  └──────────┘ └───────┘ └──────────┘ └───┬───┘ └──────┬──────┘ │
│                                         │              │         │
│                               Service Role Key     Triggers      │
└─────────────────────────────────────────┼──────────────┼────────┘
                                          │              │
┌─────────────────────────────────────────▼──────────────▼────────┐
│                    FastAPI Business Processing Engine             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     API Layer (routes/)                   │   │
│  │  50-line controllers, input validation, delegation.       │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │                   Engine Layer (engines/)                 │   │
│  │  FactorMatching │ Calculation │ Import │ Extraction      │   │
│  │  Report │ Validation │ Benchmarking │ Workflow           │   │
│  └──────────┬───────────────┬───────────────┬───────────────┘   │
│             │               │               │                    │
│  ┌──────────▼───────────────▼───────────────▼───────────────┐   │
│  │                Domain Layer (domain/)                     │   │
│  │  EmissionFactor │ Calculation │ Document │ Workflow       │   │
│  │  Organization │ Report │ Provider │ Audit                 │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │              Repository Layer (data/)                     │   │
│  │  EmissionFactorsRepo │ EmissionsLogsRepo │ OrgRepo        │   │
│  │  DocumentsRepo │ ImportsRepo │ AuditRepo │ CacheRepo      │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │           Infrastructure (infra/)                         │   │
│  │  SupabaseClient │ EventBus │ SearchIndex │ Cache │ Config │   │
│  │  LLMClient │ AuditLogger │ Metrics                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Provider Plugins (providers/)                │   │
│  │  DEFRA │ SEAI │ EPA │ ADEME │ IPCC │ Custom              │   │
│  │  Each: discover → parse → normalise → validate → import   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Shared Kernel (core/)                        │   │
│  │  exceptions.py │ types.py │ config.py │ logging.py        │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
3.2 Dependency Flow

api/ ──→ engines/ ──→ domain/ ──→ data/ ──→ infra/
 │                                              │
 └──────────────────────────────────────────────┘
                    all use
               core/ (exceptions, types, config)
Strict rule: Inner layers never import outer layers. domain/ never imports engines/ or api/. data/ never imports engines/. infra/ is the bottom — no other layer imports it directly (only data/ does via dependency injection).

3.3 Provider Plugin Isolation

engines/import_mapping.py
    │
    ├── imports ProviderPlugin (abstract)
    │
    └── calls provider.discover() / parse() / normalise() / validate() / import()
            │
            ├── providers/defra/plugin.py    → implements ProviderPlugin
            ├── providers/seai/plugin.py     → implements ProviderPlugin
            ├── providers/epa/plugin.py      → implements ProviderPlugin
            ├── providers/ademe/plugin.py    → implements ProviderPlugin
            ├── providers/ipcc/plugin.py     → implements ProviderPlugin
            └── providers/custom/plugin.py   → implements ProviderPlugin

No engine imports a concrete provider. Providers are discovered via
setuptools entry points or a registry module.
4. Package Structure

backend/
├── main.py                        App factory (30 lines)
│
├── api/                           Route handlers — thin controllers
│   ├── __init__.py
│   ├── router.py                  Single router, all endpoints
│   ├── dependencies.py            FastAPI dependencies (get_current_user, get_service_client)
│   ├── middleware.py               JWT validation, request ID, audit log, rate limit
│   └── contracts.py               Pydantic request/response models (shared with frontend)
│
├── engines/                       Processing engines — stateless, injectable
│   ├── __init__.py
│   ├── factor_matching.py         FactorMatchingEngine
│   ├── calculation.py             CalculationEngine
│   ├── import_mapping.py          ImportMappingEngine
│   ├── extraction.py              DocumentExtractionEngine
│   ├── ai_extraction.py           AIExtractionEngine
│   ├── report_generation.py       ReportGenerationEngine
│   ├── validation.py              ValidationEngine
│   ├── benchmarking.py            BenchmarkingEngine
│   └── workflow.py                WorkflowOrchestrator
│
├── domain/                        Domain model — rich objects, zero dependencies
│   ├── __init__.py
│   ├── factor.py                  EmissionFactor, FactorSet, ActivityType
│   ├── calculation.py             Calculation, CalculationSnapshot, Methodology
│   ├── document.py                Document, ExtractionResult, ExtractionField
│   ├── organization.py            Organization, Facility, Asset
│   ├── report.py                  Report, ReportSection, ReportTemplate
│   ├── workflow.py                WorkflowState, Transition, Saga
│   ├── provider.py                ProviderInfo, ProviderVersion, ImportBatch
│   ├── audit.py                   AuditEntry, AuditTrail
│   └── matching.py                MatchRequest, MatchResult, MatchingStage, StageResult
│
├── data/                          Repository interfaces + implementations
│   ├── __init__.py
│   ├── base.py                    AbstractRepository (generic interface)
│   ├── emission_factors.py        EmissionFactorsRepository
│   ├── emissions_logs.py          EmissionsLogsRepository
│   ├── organizations.py           OrganizationsRepository
│   ├── documents.py               DocumentsRepository
│   ├── imports.py                 ImportsRepository
│   ├── reports.py                 ReportsRepository
│   ├── audit.py                   AuditRepository
│   └── cache.py                   CacheRepository (factor search index)
│
├── infra/                         Infrastructure — concrete implementations
│   ├── __init__.py
│   ├── supabase.py                Supabase client factory (service role + singleton)
│   ├── event_bus.py               In-memory event bus (publish/subscribe)
│   ├── search_index.py            FactorSearchIndex (in-memory inverted index)
│   ├── cache.py                   TTL cache
│   ├── llm_client.py              OpenAI/Anthropic API client
│   ├── audit_logger.py            Structured audit logger (JSON → Supabase)
│   ├── config.py                  All configuration, env loading
│   └── metrics.py                 Prometheus metrics export
│
├── providers/                     Emission factor provider plugins
│   ├── __init__.py
│   ├── base.py                    ProviderPlugin (abstract base)
│   ├── registry.py                Provider registry + discovery
│   ├── defra/
│   │   ├── __init__.py
│   │   └── plugin.py              DEFRAProvider(ProviderPlugin)
│   ├── seai/
│   │   ├── __init__.py
│   │   └── plugin.py              SEAIProvider(ProviderPlugin)
│   ├── epa/
│   │   ├── __init__.py
│   │   └── plugin.py              EPAProvider(ProviderPlugin)
│   ├── ademe/
│   │   ├── __init__.py
│   │   └── plugin.py              ADEMEProvider(ProviderPlugin)
│   ├── ipcc/
│   │   ├── __init__.py
│   │   └── plugin.py              IPCCProvider(ProviderPlugin)
│   └── custom/
│       ├── __init__.py
│       └── plugin.py              CustomProvider(ProviderPlugin)
│
├── core/                          Shared kernel
│   ├── __init__.py
│   ├── exceptions.py              CarbonTallyError hierarchy
│   ├── types.py                   Shared primitives (Country, Unit, Scope, Year)
│   ├── config.py                  Config values (shared)
│   └── logging.py                 Logging setup
│
├── plugins.py                     Entry-point loading for providers
│
└── tests/
    ├── unit/
    │   ├── engines/
    │   ├── domain/
    │   └── providers/
    ├── integration/
    └── fixtures/
5. Dependency Rules
5.1 Layer Dependency Matrix
Layer	May Import	May NOT Import
api/	engines/, domain/, data/, core/, api/contracts.py	—
engines/	domain/, core/	api/, data/, infra/, providers/*
domain/	core/ only	api/, engines/, data/, infra/, providers/
data/	domain/, core/, infra/	api/, engines/, providers/
infra/	core/ only	api/, engines/, domain/, data/, providers/
providers/	domain/, core/, data/ (for import persistence)	api/, engines/
core/	Nothing	Everything else
*engines/import_mapping.py uses ProviderPlugin (abstract interface from providers/base.py). It does NOT import concrete providers. Providers are injected via the registry.

5.2 Dependency Injection Rule
Engines and repositories are instantiated via constructors with their dependencies:


class CalculationEngine:
    def __init__(
        self,
        factor_repo: EmissionFactorsRepository,
        logs_repo: EmissionsLogsRepository,
        org_repo: OrganizationsRepository,
        matching_engine: FactorMatchingEngine,
        event_bus: EventBus,
        audit_logger: AuditLogger,
    ):
        self.factor_repo = factor_repo
        self.logs_repo = logs_repo
        self.matching_engine = matching_engine
        self.event_bus = event_bus
        self.audit_logger = audit_logger
No engine instantiates its own dependencies. The API layer wires everything together via a composition root.

5.3 Composition Root

# api/dependencies.py — single place all objects are wired

def get_calculation_engine(
    supabase: Client = Depends(get_service_supabase),
) -> CalculationEngine:
    return CalculationEngine(
        factor_repo=EmissionFactorsRepository(supabase),
        logs_repo=EmissionsLogsRepository(supabase),
        org_repo=OrganizationsRepository(supabase),
        matching_engine=get_factor_matching_engine(supabase),
        event_bus=get_event_bus(),
        audit_logger=get_audit_logger(),
    )
6. The Four Platforms
6.1 Platform Boundaries

┌─────────────────────────────────────────────────────────────────┐
│                    MATCHING PLATFORM                             │
│                                                                  │
│  Responsibility: Given an activity description + unit +          │
│  country + year, find the best emission factor across all        │
│  registered providers.                                           │
│                                                                  │
│  Input:  MatchRequest(activity, unit, country, year, scope)      │
│  Output: MatchResult(factor, confidence, methodology, provider)  │
│                                                                  │
│  Components:                                                     │
│    FactorMatchingEngine                                          │
│    MatchingPipeline (staged: exact → natural key → keyword →     │
│                        fuzzy → semantic → human)                 │
│    FactorSearchIndex (in-memory inverted index)                  │
│    FactorAliasRegistry (synonyms + organisation-specific         │
│                          aliases)                                │
│                                                                  │
│  Providers used: all (factors loaded into unified index)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    IMPORT PLATFORM                               │
│                                                                  │
│  Responsibility: Ingest factor datasets from external            │
│  providers, validate, normalise, version, and load into the      │
│  database.                                                       │
│                                                                  │
│  Input:  ImportRequest(provider, file_path, options)             │
│  Output: ImportResult(batch, imported, skipped, errors)          │
│                                                                  │
│  Components:                                                     │
│    ImportMappingEngine                                           │
│    ProviderPlugin registry                                      │
│    ProviderPlugin (abstract): discover → parse → normalise       │
│                                → validate → import               │
│    ImportBatch (domain object — immutable version record)        │
│                                                                  │
│  Database: emission_factors, import_batches, import_errors       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CALCULATION PLATFORM                          │
│                                                                  │
│  Responsibility: Compute emissions (quantity × factor),          │
│  aggregates, intensity ratios, trends. Every calculation is      │
│  reproducible — stored with a complete snapshot of inputs.       │
│                                                                  │
│  Input:  CalculationRequest(org, activity, quantity, unit,       │
│                             date, scope)                         │
│  Output: CalculationResult(co2e_kg, snapshot, factor_used)       │
│                                                                  │
│  Components:                                                     │
│    CalculationEngine                                             │
│    CalculationSnapshot (immutable record of inputs + result)     │
│    Methodology (enum: direct_multiply, distance_based,           │
│                          spend_based, mass_balance)              │
│    CalculationRepository (persistence)                           │
│                                                                  │
│  Database: emissions_logs, calculation_snapshots                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW & EVENT PLATFORM                     │
│                                                                  │
│  Responsibility: Orchestrate long-running processes across       │
│  engines using domain events. Decouple engine-to-engine          │
│  communication. Provide audit trail via event sourcing.          │
│                                                                  │
│  Components:                                                     │
│    EventBus (publish/subscribe, in-process)                     │
│    WorkflowOrchestrator (state machine)                          │
│    Sagas (compensating transactions for rollback)                │
│    EventStore (persist events for audit)                         │
│                                                                  │
│  Events:                                                         │
│    DocumentUploaded → ExtractionRequested → ExtractionCompleted  │
│    → FieldsExtracted → CalculationRequested → CalculationCompleted│
│    → ReportGenerated                                             │
│                                                                  │
│  Database: domain_events, workflow_states                        │
└─────────────────────────────────────────────────────────────────┘
7. Processing Engines — Detailed Specifications
7.1 Engine Contract
Every engine:

Is a stateless class with constructor-injected dependencies
Has a single public async method (e.g., match(), calculate(), import_batch())
Returns a domain object (never a dict, never a Pydantic model for business output)
Publishes domain events after significant state changes
Never calls Supabase directly — goes through repositories
Never imports a concrete provider — uses ProviderPlugin interface
Logs via the audit framework (input, output, timing, decision)
7.2 Engine Catalog
Engine	File	Repository Dependencies	Provider Dependencies
FactorMatchingEngine	engines/factor_matching.py	EmissionFactorsRepo, CacheRepo	All (via index)
CalculationEngine	engines/calculation.py	EmissionFactorsRepo, EmissionsLogsRepo, OrgRepo	None (uses MatchingEngine)
ImportMappingEngine	engines/import_mapping.py	EmissionFactorsRepo, ImportsRepo	ProviderPlugin (abstract)
DocumentExtractionEngine	engines/extraction.py	DocumentsRepo, StorageRepo	None
AIExtractionEngine	engines/ai_extraction.py	DocumentsRepo	None
ReportGenerationEngine	engines/report_generation.py	ReportsRepo, OrgRepo, EmissionsLogsRepo	None
ValidationEngine	engines/validation.py	EmissionsLogsRepo, OrgRepo	None
BenchmarkingEngine	engines/benchmarking.py	EmissionsLogsRepo, OrgRepo	None
WorkflowOrchestrator	engines/workflow.py	WorkflowsRepo, DocumentsRepo	None
7.3 Engine Template

# engines/factor_matching.py

class FactorMatchingEngine:
    """Provider-agnostic factor matching engine.

    Matches user-provided activity descriptions to emission factors across
    all registered providers using a configurable multi-stage pipeline.
    """

    def __init__(
        self,
        factor_repo: EmissionFactorsRepository,
        search_index: FactorSearchIndex,
        alias_registry: FactorAliasRegistry,
        event_bus: EventBus,
        audit_logger: AuditLogger,
    ):
        self.factor_repo = factor_repo
        self.search_index = search_index
        self.alias_registry = alias_registry
        self.event_bus = event_bus
        self.audit_logger = audit_logger

    async def match(self, request: MatchRequest) -> MatchResult:
        """Execute the multi-stage matching pipeline and return the best match."""
        started = time.monotonic()
        pipeline = self._build_pipeline(request)

        for stage in pipeline:
            stage_result = await stage.execute(request, self.search_index)
            self.audit_logger.record_stage(request.id, stage.name, stage_result)

            if stage_result.is_definitive:
                result = MatchResult(
                    factor=stage_result.factor,
                    confidence=stage_result.confidence,
                    methodology=stage_result.methodology,
                    provider=stage_result.provider,
                    stages_executed=[s.name for s in pipeline],
                )
                self.audit_logger.record_match(request.id, result, time.monotonic() - started)
                await self.event_bus.publish(FactorMatchedEvent(request=request, result=result))
                return result

        # No match found — return with suggestions
        suggestions = await self.search_index.suggest(request.activity, request.unit)
        return MatchResult.no_match(suggestions=suggestions, stages_executed=[s.name for s in pipeline])

    def _build_pipeline(self, request: MatchRequest) -> list[MatchingStage]:
        """Build pipeline stages based on request options."""
        return [
            ExactMatchStage(),
            NaturalKeyStage(),
            AliasMatchStage(self.alias_registry),
            KeywordSearchStage(),
            FuzzyMatchStage(threshold=0.85),
            SemanticMatchStage(),  # Optional, only if requested
        ]
8. Provider Plugin Architecture
8.1 Abstract Provider Interface

# providers/base.py

from abc import ABC, abstractmethod
from domain.provider import ProviderInfo, ProviderVersion, ImportBatch
from domain.factor import EmissionFactor

class ProviderPlugin(ABC):
    """Abstract interface for emission-factor data providers.

    Each jurisdiction (DEFRA/UK, SEAI/IE, EPA/IE, ADEME/FR, IPCC/global)
    implements this interface. The ImportMappingEngine calls these methods
    in order during an import. No engine ever imports a concrete provider.
    """

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Static metadata: name, jurisdiction, country_codes, website, license."""
        ...

    @abstractmethod
    async def discover(self, source_path: str) -> DiscoveryResult:
        """Open the source file, enumerate worksheets, classify each sheet.

        Returns metadata about every sheet in the workbook. No emission
        factors are parsed yet — this is lightweight analysis only.
        """
        ...

    @abstractmethod
    async def parse(self, discovery: DiscoveryResult) -> list[RawFactorRow]:
        """Parse raw rows from the discovered data sheets.

        Returns a list of raw factor rows as published — no normalisation,
        no validation, no mapping to the database schema. Every published
        field is preserved verbatim.
        """
        ...

    @abstractmethod
    async def normalise(self, raw_rows: list[RawFactorRow]) -> list[NormalisedFactor]:
        """Normalise raw rows into provider-agnostic factor representations.

        Whitepsace normalisation, decimal parsing, unit standardisation,
        activity-type construction. No loss of information — original values
        are preserved in metadata.
        """
        ...

    @abstractmethod
    async def validate(self, factors: list[NormalisedFactor]) -> ValidationReport:
        """Provider-specific validation rules.

        Each provider may have additional checks beyond the shared
        ValidationEngine (e.g., DEFRA requires reporting_year presence,
        SEAI may require specific column combinations).
        """
        ...

    @abstractmethod
    async def map_to_schema(self, factors: list[NormalisedFactor]) -> list[EmissionFactor]:
        """Map normalised factors onto the RC2 emission_factors schema.

        This is the ONLY place where provider-specific mapping logic lives.
        The output EmissionFactor objects are schema-compliant and ready
        for persistence.
        """
        ...
8.2 Provider Lifecycle

                                 ProviderPlugin
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
              DEFRAProvider     SEAIProvider       EPAPProvider
              (providers/       (providers/        (providers/
               defra/plugin.py)  seai/plugin.py)    epa/plugin.py)

ImportMappingEngine calls:
  provider.discover(source)
  provider.parse(discovery)
  provider.normalise(raw_rows)
  provider.validate(factors)        ← provider-specific rules
  ValidatonEngine.validate(factors) ← universal rules
  provider.map_to_schema(factors)

Result: list[EmissionFactor] ready for idempotent database insert.
8.3 Provider Registration

# providers/registry.py

_registry: dict[str, type[ProviderPlugin]] = {}

def register(provider_class: type[ProviderPlugin]) -> None:
    _registry[provider_class.__name__] = provider_class

def get(provider_name: str) -> ProviderPlugin:
    cls = _registry.get(provider_name)
    if cls is None:
        raise UnknownProviderError(provider_name)
    return cls()

# providers/defra/plugin.py
@register
class DEFRAProvider(ProviderPlugin):
    ...

# providers/seai/plugin.py
@register
class SEAIProvider(ProviderPlugin):
    ...
Registration is explicit (decorator) rather than setuptools entry points — simpler, auditable, no magic.

8.4 Provider Metadata

# domain/provider.py

@dataclass(frozen=True)
class ProviderInfo:
    key: str                     # "defra", "seai", "epa"
    name: str                    # "UK Government GHG Conversion Factors"
    jurisdiction: str            # "United Kingdom"
    country_codes: tuple[str, ...]  # ("GB",)
    website: str
    license: str                 # "Open Government Licence v3.0"
    latest_version: str          # "2025.1"
    publisher: str               # "DESNZ"
    language: str                # "en"
    documentation_url: Optional[str]

@dataclass(frozen=True)
class ProviderVersion:
    provider_key: str
    version: str                 # "2025.1"
    release_date: date
    status: str                  # "active" | "superseded" | "deprecated"
    import_batch_id: str         # Foreign key to import_batches
    row_count: int
    checksum: str                # SHA-256 of the source file
9. Domain Model
9.1 Domain Objects — Rich, Not Anemic
Domain objects encapsulate behaviour, not just data. They are pure Python with zero framework imports.


# domain/factor.py

@dataclass(frozen=True)
class EmissionFactor:
    """An emission factor as stored in the RC2 emission_factors table.

    Immutable. Once created, never modified. A new version is a new object.
    """
    id: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: Decimal
    unit: Optional[str]
    scope: Optional[str]
    factor_source: str          # "DEFRA-DESNZ", "SEAI", "EPA"
    factor_set: str             # "DEFRA-2025", "SEAI-2024"
    country: str                # "GB", "IE"
    provider_key: str           # "defra", "seai"
    import_batch_id: str        # Which import created this
    natural_key: tuple[str, ...]

    def calculate_emissions(self, quantity: Decimal, quantity_unit: str) -> Decimal:
        """Compute kgCO2e from a quantity in the factor's unit."""
        if quantity_unit != self.unit:
            raise UnitMismatchError(self.unit, quantity_unit)
        return (quantity * self.co2e_multiplier).quantize(Decimal("0.000001"))

    def with_new_year(self, year: int) -> "EmissionFactor":
        """Create a copy with a different reporting year (for version tracking)."""
        return replace(self, reporting_year=year)


@dataclass(frozen=True)
class FactorSet:
    """A complete set of factors from one provider + year + version."""
    provider_key: str
    reporting_year: int
    version: str
    factors: tuple[EmissionFactor, ...]
    metadata: FactorSetMetadata

    def find_by_natural_key(self, key: tuple[str, ...]) -> Optional[EmissionFactor]:
        ...

    def search_by_activity(self, activity: str, unit: Optional[str] = None) -> list[EmissionFactor]:
        ...

# domain/calculation.py

@dataclass(frozen=True)
class CalculationSnapshot:
    """An immutable, auditable record of an emissions calculation.

    Contains everything needed to reproduce the result: the factor used,
    the input values, the methodology, and a content hash for tamper detection.
    """
    id: str
    organization_id: str
    activity: str
    activity_type: str              # The matched label
    quantity: Decimal
    quantity_unit: str
    co2e_multiplier: Decimal
    co2e_kg: Decimal
    scope: str
    date: date
    factor_id: str                  # emission_factors.id
    factor_source: str              # which provider
    factor_set: str                 # which version
    factor_version: str             # "2025.1"
    import_batch_id: str            # trace to import
    reporting_year: int
    methodology: str                # "direct_multiply"
    algorithm_version: str          # "2.1.0"
    content_hash: str               # SHA-256 of all inputs above
    calculated_at: datetime
    calculated_by: str              # engine instance ID
    request_id: str                 # trace to API request

    def verify_reproducibility(self, recomputed: Decimal) -> bool:
        """Check that a recalculation produces the identical result."""
        return recomputed == self.co2e_kg

    def build_content_hash(self) -> str:
        """Recompute the content hash for tamper detection."""
        canonical = f"{self.quantity}|{self.co2e_multiplier}|{self.factor_id}"
        return hashlib.sha256(canonical.encode()).hexdigest()

# domain/matching.py

@dataclass(frozen=True)
class MatchRequest:
    id: str                         # Request UUID
    activity: str                   # User-provided description
    unit: Optional[str]             # Desired unit
    country: str                    # "GB" | "IE"
    reporting_year: int
    scope: Optional[str]
    organization_id: Optional[str]
    preferred_provider: Optional[str]  # Override: "defra", "seai"
    max_stages: int = 6             # How many pipeline stages to run

@dataclass(frozen=True)
class StageResult:
    """Output of a single matching pipeline stage."""
    stage_name: str                 # "exact_match", "keyword_search", etc.
    matched: bool
    factor: Optional[EmissionFactor]
    confidence: float               # 0.0–1.0
    score: float                    # Stage-specific score
    reason: str                     # Human-readable explanation
    provider: Optional[str]         # Which provider the factor came from
    is_definitive: bool             # Should the pipeline stop here?

@dataclass(frozen=True)
class MatchResult:
    status: str                     # "matched" | "no_match" | "ambiguous"
    factor: Optional[EmissionFactor]
    confidence: float
    methodology: str                # Which stage produced the match
    provider: Optional[str]
    stages_executed: tuple[str, ...]
    suggestions: tuple[Suggestion, ...]
    processing_time_ms: int
    request_id: str

    @staticmethod
    def no_match(suggestions: list[Suggestion], stages_executed: list[str]) -> "MatchResult":
        ...

# domain/provider.py

@dataclass(frozen=True)
class ImportBatch:
    """An immutable record of a factor import.

    Imports are versioned — every import creates a new batch. Batches are
    never deleted or modified.
    """
    id: str
    provider_key: str
    provider_version: str         # "2025.1"
    source_file: str              # Storage path
    source_checksum: str          # SHA-256 of source file
    reporting_year: int
    status: str                   # "importing" | "completed" | "failed" | "rolled_back"
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_duplicate: int
    errors: tuple[ImportError, ...]
    is_active: bool               # Only one batch per provider+year is active
    created_at: datetime
    created_by: str
    rolled_back_from: Optional[str]  # If this was rolled back, the replacement batch ID

    def activate(self) -> "ImportBatch":
        """Mark this batch as the active version for its provider + year."""
        return replace(self, is_active=True, status="completed")

    def rollback(self, replaced_by: str) -> "ImportBatch":
        """Mark this batch as rolled back."""
        return replace(self, is_active=False, status="rolled_back", rolled_back_from=replaced_by)
10. Repository Architecture
10.1 Abstract Repository

# data/base.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class AbstractRepository(ABC, Generic[T]):
    """Typed repository contract. Implementations use Supabase service role."""

    @abstractmethod
    async def get(self, id: str) -> Optional[T]: ...

    @abstractmethod
    async def save(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: str) -> None: ...
10.2 Repository Catalog
Repository	Aggregate Root	Key Methods
EmissionFactorsRepository	EmissionFactor	find_by_natural_key(key), find_by_activity(activity, unit, year, country), bulk_upsert(factors), get_active_set(provider, year), deactivate_set(provider, year), load_all_for_index()
EmissionsLogsRepository	EmissionLog	create(org_id, factor_id, qty, unit, scope, date, asset_id, snapshot_id), find_by_org(org_id, period), aggregate(org_id, period, group_by), count_by_scope(org_id, year)
OrganizationsRepository	Organization	get_by_id(id), get_members(org_id), get_metadata(org_id), get_facilities(org_id), get_assets(org_id), update_metadata(org_id, data)
DocumentsRepository	Document	create_from_upload(org_id, storage_path, filename), update_status(doc_id, status), get_pending_extraction(), get_by_org(org_id)
ImportsRepository	ImportBatch	create_batch(provider, version, year, source, checksum), complete_batch(batch_id, stats), fail_batch(batch_id, errors), activate_batch(batch_id), rollback_batch(batch_id, replaced_by), get_active(provider, year), get_history(provider)
ReportsRepository	Report	create_generation_request(org_id, type, year, template), complete_generation(report_id, storage_url, stats), get_by_org(org_id)
AuditRepository	AuditEntry	record(entry: AuditEntry), query(filters), export_csv(filters)
CacheRepository	FactorSearchIndex	load_all_active(), refresh(), search(query, filters), suggest(partial, unit)
EventsRepository	DomainEvent	store(event: DomainEvent), replay(aggregate_id), get_by_correlation_id(correlation_id)
10.3 Example Repository Implementation

# data/emission_factors.py

class EmissionFactorsRepository(AbstractRepository[EmissionFactor]):
    """Emission factors data access — Supabase implementation."""

    def __init__(self, client: Client):
        self.client = client  # service-role Supabase client

    async def find_by_natural_key(
        self,
        reporting_year: int,
        activity_type: str,
        country: str,
        unit: Optional[str],
        scope: Optional[str],
    ) -> Optional[EmissionFactor]:
        result = (
            self.client.table("emission_factors")
            .select("*")
            .eq("reporting_year", reporting_year)
            .eq("activity_type", activity_type)
            .eq("country", country)
        )
        if unit is None:
            result = result.is_("unit", None)
        else:
            result = result.eq("unit", unit)
        if scope is None:
            result = result.is_("scope", None)
        else:
            result = result.eq("scope", scope)
        row = result.maybe_single().execute()
        if row.data:
            return self._to_domain(row.data)
        return None

    async def load_all_for_index(self) -> list[EmissionFactor]:
        """Load every active emission factor for the search index."""
        rows = self.client.table("emission_factors").select("*").execute()
        return [self._to_domain(r) for r in rows.data]

    def _to_domain(self, row: dict) -> EmissionFactor:
        """Map a Supabase row to a domain object."""
        return EmissionFactor(
            id=row["id"],
            reporting_year=row["reporting_year"],
            activity_type=row["activity_type"],
            co2e_multiplier=Decimal(str(row["co2e_multiplier"])),
            unit=row.get("unit"),
            scope=row.get("scope"),
            factor_source=row.get("factor_source", ""),
            factor_set=row.get("factor_set", ""),
            country=row.get("country", "GB"),
            provider_key=self._provider_from_source(row.get("factor_source", "")),
            import_batch_id=row.get("import_batch_id", ""),
            natural_key=(...),
        )
11. Matching Platform
11.1 Multi-Stage Matching Pipeline

MatchRequest
    │
    ▼
┌─────────────────────────┐
│ Stage 1: Exact Match    │  confidence=1.0, is_definitive=True
│ activity_type == input  │  Use when user provides the exact RC2 label.
└─────────┬───────────────┘
          │ no match
          ▼
┌─────────────────────────┐
│ Stage 2: Natural Key    │  Uses natural-key index.
│ (year, act, country,    │  User input decomposed into tokens.
│  unit, scope)            │  confidence=0.98
└─────────┬───────────────┘
          │ no match
          ▼
┌─────────────────────────┐
│ Stage 3: Alias Match    │  Organisation-specific aliases.
│ "Diesel" → "Fuels >     │  Admin-managed synonym table.
│  Liquid fuels > Diesel" │  confidence=0.95
└─────────┬───────────────┘
          │ no match
          ▼
┌─────────────────────────┐
│ Stage 4: Keyword Search │  In-memory inverted index.
│ ILIKE '%diesel%'        │  Tokenised, ranked by TF-IDF.
│ + unit filter           │  confidence=0.85 if top result dominates.
└─────────┬───────────────┘
          │ no match
          ▼
┌─────────────────────────┐
│ Stage 5: Fuzzy Match    │  Levenshtein distance on activity_type.
│ "deisel" → "diesel"     │  confidence=0.75 if distance < threshold.
└─────────┬───────────────┘
          │ no match
          ▼
┌─────────────────────────┐
│ Stage 6: Semantic AI    │  [OPTIONAL, admin-configurable]
│ Embedding similarity    │  Uses sentence-transformers or LLM API.
│ between descriptions.   │  confidence=0.70. Never definitively selects.
└─────────┬───────────────┘
          │ no match
          ▼
┌─────────────────────────┐
│ Stage 7: Human Review   │  Returns suggestions ranked by score.
│ Admin manually selects  │  Frontend shows MatchResult.suggestions.
│ from top-N candidates.  │  Admin selection creates a permanent alias.
└─────────────────────────┘
11.2 Stage Configuration
Each stage can be enabled/disabled per request or globally. Admin can configure thresholds:


# domain/matching.py

@dataclass
class MatchingPipelineConfig:
    stages: tuple[str, ...]              # ["exact_match", "natural_key", ...]
    fuzzy_threshold: float = 0.85
    keyword_min_confidence: float = 0.80
    semantic_enabled: bool = False
    semantic_min_confidence: float = 0.70
    max_suggestions: int = 10
    prefer_provider: Optional[str] = None  # "defra" — prefer this provider
    restrict_country: Optional[str] = None  # "GB" — only show factors for this country
11.3 AI Isolation Rule (Hard)

┌─────────────────────────────────────────────────────────┐
│                      AI ENGINE                           │
│                                                          │
│  Extracts structured fields ONLY from unstructured text:  │
│    • activity_description                                │
│    • unit                                                │
│    • quantity                                            │
│    • country                                             │
│    • supplier_name                                       │
│    • dates                                               │
│                                                          │
│  NEVER returns an emission factor.                       │
│  NEVER returns a co2e_multiplier.                        │
│  NEVER returns an emission_factors.id.                   │
└──────────────────────────┬──────────────────────────────┘
                           │
              Extracted fields (MatchRequest)
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   MATCHING ENGINE                        │
│                                                          │
│  Takes the extracted fields and runs the deterministic    │
│  multi-stage pipeline. The AI's output is just input.    │
│                                                          │
│  The Matching Engine — and ONLY the Matching Engine —    │
│  selects the emission factor. Every match is auditable,  │
│  reproducible, and deterministic given the same inputs.  │
└─────────────────────────────────────────────────────────┘
12. Import Platform
12.1 Versioned Import Flow

Admin uploads workbook → Supabase Storage
    │
    ▼
POST /api/v2/imports
    │
    ▼
ImportMappingEngine:
    1. Create ImportBatch (status = "importing")
    2. Deactivate current active batch for (provider, year)
       (sets is_active=FALSE — no deletion)
    3. Load provider plugin via registry
    4. provider.discover(source) → DiscoveryResult
    5. provider.parse(discovery) → list[RawFactorRow]
    6. provider.normalise(raw) → list[NormalisedFactor]
    7. provider.validate(factors) → ProviderValidationReport
    8. ValidationEngine.validate(factors) → UniversalValidationReport
    9. provider.map_to_schema(factors) → list[EmissionFactor]
   10. EmissionFactorsRepository.bulk_upsert(factors)
       (idempotent — natural-key upsert)
   11. Mark batch as "completed", activate it
   12. Publish ImportCompleted event
   13. FactorSearchIndex.refresh()
   14. Return ImportResult
12.2 Rollback

Admin initiates rollback:
    POST /api/v2/imports/{batch_id}/rollback
    │
    ▼
ImportMappingEngine:
    1. Load the ImportBatch to roll back
    2. Set is_active = FALSE, status = "rolled_back"
    3. Activate the previous batch for (provider, year)
       (or leave no active batch if none existed)
    4. Rebuild FactorSearchIndex from active batches only
    5. Publish ImportRolledBack event
    6. All calculations using factors from the rolled-back batch
       are unaffected (they store a snapshot) — the factors remain
       in the database, just not active for NEW matches.
12.3 ImportBatch Lifecycle

                  ┌──────────┐
                  │ CREATED  │
                  └────┬─────┘
                       │
                  import started
                       │
                  ┌────▼─────┐
                  │ IMPORTING│
                  └────┬─────┘
                       │
            ┌──────────┼──────────┐
            │          │          │
        success    validation   error
            │       failure      │
            │          │          │
       ┌────▼──┐  ┌───▼────┐  ┌──▼────┐
       │ACTIVE │  │ FAILED │  │ FAILED│
       └───┬───┘  └────────┘  └───────┘
           │
      rolled back
           │
      ┌────▼──────┐
      │ROLLED_BACK│
      └───────────┘
13. Calculation Platform
13.1 Reproducible Calculation
Every calculation produces a CalculationSnapshot — an immutable record containing:

Field	Purpose
quantity	The user-provided consumption
quantity_unit	The unit of consumption
co2e_multiplier	The exact factor value at time of calculation
factor_id	emission_factors.id — trace to the specific row
factor_source	Which provider (DEFRA, SEAI, etc.)
factor_set	Which version ("DEFRA-2025")
import_batch_id	Which import created this factor
reporting_year	The reporting year of the factor
methodology	Which calculation method was used
algorithm_version	The engine version
content_hash	SHA-256 of all inputs — tamper detection
13.2 Calculation Flow

CalculationRequest
    │
    ▼
CalculationEngine.calculate(request):
    1. Build MatchRequest from CalculationRequest fields
    2. Call FactorMatchingEngine.match(match_request) → MatchResult
    3. If not matched → raise FactorNotFoundError
    4. Compute: co2e_kg = quantity × matched_factor.co2e_multiplier
    5. Build CalculationSnapshot (all inputs + result)
    6. Compute content_hash
    7. Save CalculationSnapshot to calculation_snapshots table
    8. Save EmissionLog to emissions_logs (with snapshot_id FK)
    9. Publish CalculationCompleted event
   10. Return CalculationResult
13.3 Verification at Any Time

async def verify_calculation(snapshot_id: str) -> VerificationResult:
    """Re-run a historical calculation and verify the result matches."""
    snapshot = await snapshots_repo.get(snapshot_id)
    factor = await factor_repo.get(snapshot.factor_id)

    recomputed = snapshot.quantity * factor.co2e_multiplier

    if recomputed != snapshot.co2e_kg:
        return VerificationResult(match=False, discrepancy=recomputed - snapshot.co2e_kg)

    if snapshot.build_content_hash() != snapshot.content_hash:
        return VerificationResult(match=False, tampered=True)

    return VerificationResult(match=True)
14. Workflow & Event Platform
14.1 Domain Events

# domain/workflow.py

@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events."""
    event_id: str
    occurred_at: datetime
    correlation_id: str           # Links related events (e.g., same document processing)
    aggregate_id: str             # The entity this event is about
    aggregate_type: str

# Concrete events:
class DocumentUploaded(DomainEvent): ...
class ExtractionRequested(DomainEvent): ...
class ExtractionCompleted(DomainEvent): ...
class FieldsExtracted(DomainEvent): ...
class CalculationRequested(DomainEvent): ...
class CalculationCompleted(DomainEvent): ...
class ReportGenerated(DomainEvent): ...
class ImportStarted(DomainEvent): ...
class ImportCompleted(DomainEvent): ...
class ImportRolledBack(DomainEvent): ...
class FactorMatched(DomainEvent): ...
class FactorNotFound(DomainEvent): ...
class WorkflowStateChanged(DomainEvent): ...
class ValidationFailed(DomainEvent): ...
14.2 Event Bus

# infra/event_bus.py

class EventBus:
    """In-process publish/subscribe event bus.

    Handlers are registered by event type. Publishing is synchronous
    by default (for audit trail integrity). Async dispatch is available
    for fire-and-forget side effects.
    """

    def subscribe(self, event_type: type, handler: callable): ...

    async def publish(self, event: DomainEvent):
        """Publish an event. All handlers run. Audit event is stored."""
        await self._store_event(event)
        for handler in self._handlers_for(type(event)):
            try:
                await handler(event)
            except Exception:
                # Handler failures do not block other handlers
                # but ARE logged and surfaced in admin
                self.error_logger.log(handler_error)

# Example registrations:
event_bus.subscribe(ExtractionCompleted, trigger_ai_extraction)
event_bus.subscribe(CalculationCompleted, rebuild_dashboard_cache)
event_bus.subscribe(CalculationCompleted, check_benchmark_thresholds)
event_bus.subscribe(ImportCompleted, refresh_factor_search_index)
event_bus.subscribe(ImportRolledBack, refresh_factor_search_index)
event_bus.subscribe(FactorNotFound, notify_admin_of_missing_factor)
14.3 Document Processing Saga

User uploads PDF
    │
    ▼
DocumentUploaded
    │
    ├── handler: trigger_extraction(event)
    │       │
    │       ▼
    │   ExtractionCompleted
    │       │
    │       ├── handler: trigger_ai_extraction(event)
    │       │       │
    │       │       ▼
    │       │   FieldsExtracted
    │       │       │
    │       │       └── handler: auto_request_calculation(event)
    │       │               │
    │       │               ▼
    │       │           CalculationCompleted
    │       │               │
    │       │               ├── handler: update_dashboard(event)
    │       │               └── handler: check_thresholds(event)
    │       │
    │       └── handler: notify_staff_if_low_confidence(event)
    │
    └── handler: send_upload_confirmation(event)
14.4 Workflow State Machine

# domain/workflow.py

@dataclass(frozen=True)
class WorkflowDefinition:
    """A named workflow with valid states and transitions."""
    name: str
    states: tuple[str, ...]
    transitions: tuple[tuple[str, str], ...]   # (from_state, to_state)

    def can_transition(self, from_state: str, to_state: str) -> bool:
        return (from_state, to_state) in self.transitions

DOCUMENT_PIPELINE = WorkflowDefinition(
    name="document_pipeline",
    states=(
        "pending", "uploaded", "classifying", "extracting",
        "ai_matching", "matched", "customer_review",
        "reviewed", "calculating", "completed", "failed", "manual_review",
    ),
    transitions=(
        ("pending", "uploaded"),
        ("uploaded", "classifying"),
        ("classifying", "extracting"),
        ("extracting", "ai_matching"),
        ("ai_matching", "matched"),
        ("ai_matching", "manual_review"),
        ("matched", "customer_review"),
        ("customer_review", "reviewed"),
        ("customer_review", "manual_review"),
        ("reviewed", "calculating"),
        ("calculating", "completed"),
        ("*", "failed"),
    ),
)
15. Audit Framework
15.1 Automatic Audit
Every engine action is automatically audited. The audit framework wraps engine calls:


# infra/audit_logger.py

@dataclass(frozen=True)
class AuditEntry:
    id: str
    timestamp: datetime
    engine: str                     # "FactorMatchingEngine"
    engine_version: str             # "2.1.0"
    action: str                     # "match_factor", "calculate_emissions"
    request_id: str
    user_id: str
    organization_id: Optional[str]
    input_summary: dict             # Abbreviated input (redact PII)
    output_summary: dict            # Abbreviated output
    decision: str                   # Human-readable explanation
    confidence: Optional[float]
    processing_time_ms: int
    status: str                     # "success" | "error" | "no_match"
    error_code: Optional[str]
    correlation_id: str
    metadata: dict                  # Arbitrary additional context

class AuditLogger:
    """Automatically logs engine actions.

    Usage (decorator or context manager):
        @audit_logger.audit(engine="FactorMatchingEngine", action="match")
        async def match(self, request): ...
    """
    def audit(self, engine: str, action: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                started = time.monotonic()
                try:
                    result = await func(*args, **kwargs)
                    self._record(AuditEntry(
                        engine=engine, action=action, status="success",
                        processing_time_ms=int((time.monotonic() - started) * 1000),
                        ...
                    ))
                    return result
                except Exception as e:
                    self._record(AuditEntry(
                        engine=engine, action=action, status="error",
                        error_code=type(e).__name__,
                        ...
                    ))
                    raise
            return wrapper
        return decorator
15.2 Audit Trail Query
The audit trail is stored in the audit_logs table (accessible via Supabase RLS to admin only, and via the admin dashboard). Every audit entry links back to its originating request_id and correlation_id, enabling full trace:


API Request (request_id=abc123)
  → FactorMatchingEngine.match (correlation_id=abc123)
      → Stage 1: ExactMatchStage (confidence=0.0, no_match)
      → Stage 2: NaturalKeyStage (confidence=0.0, no_match)
      → Stage 3: KeywordSearch (confidence=0.88, MATCHED)
  → CalculationEngine.calculate (correlation_id=abc123)
      → result: 254.32 kgCO2e
  → ReportGenerationEngine.generate (correlation_id=abc123)
      → SECR report section 2 populated
16. Factor Search Index
16.1 In-Memory Inverted Index

# infra/search_index.py

class FactorSearchIndex:
    """In-memory inverted index for sub-millisecond factor lookups.

    Loads all active emission factors at startup and rebuilds on import.
    Provides exact natural-key lookup, keyword search, and fuzzy search
    without touching the database.
    """

    def __init__(self):
        self._natural_key_index: dict[tuple, EmissionFactor] = {}
        self._token_index: dict[str, set[str]] = {}  # token → set[factor_id]
        self._factors: dict[str, EmissionFactor] = {}  # factor_id → factor
        self._metadata: FactorSetMetadata = {}

    def load(self, factors: list[EmissionFactor]):
        """Build all indexes from a factor list."""
        self._natural_key_index = {}
        self._token_index = defaultdict(set)
        self._factors = {}
        for f in factors:
            self._factors[f.id] = f
            self._natural_key_index[f.natural_key] = f
            for token in self._tokenize(f.activity_type):
                self._token_index[token].add(f.id)

    def exact_natural_key(self, key: tuple[str, ...]) -> Optional[EmissionFactor]:
        """O(1) lookup by natural key."""
        return self._natural_key_index.get(key)

    def keyword_search(
        self, query: str, unit: Optional[str] = None, country: Optional[str] = None,
        provider: Optional[str] = None, limit: int = 10,
    ) -> list[tuple[EmissionFactor, float]]:
        """Token-based TF-IDF ranked search."""
        query_tokens = self._tokenize(query)
        scores = defaultdict(float)
        for token in query_tokens:
            if token in self._token_index:
                idf = math.log(len(self._factors) / len(self._token_index[token]))
                for factor_id in self._token_index[token]:
                    scores[factor_id] += idf
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = [self._factors[fid] for fid, _ in ranked[:limit]]
        if unit:
            results = [f for f in results if f.unit == unit]
        if country:
            results = [f for f in results if f.country == country]
        if provider:
            results = [f for f in results if f.provider_key == provider]
        return [(f, scores[f.id]) for f in results]

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Lowercase, split on non-alphanumeric, remove stop words, n-gram."""
        return set(re.findall(r'\w+', text.lower()))
16.2 Index Lifecycle

Application startup:
    FactorSearchIndex.load(all_active_factors)

Import completed:
    EventBus → ImportCompleted handler
    → FactorSearchIndex.load(all_active_factors)  # rebuild

Import rolled back:
    EventBus → ImportRolledBack handler
    → FactorSearchIndex.load(all_active_factors)  # rebuild
17. Versioning Strategy
17.1 Artifact Versioning
Artifact	Version	Format	Example
Architecture Spec	2.1.0	MAJOR.MINOR.PATCH	Breaking changes increment MAJOR
Engine version	2.1.0	Same as spec at release	Stored in every AuditEntry
API version	v2	URL prefix	/api/v2/...
Algorithm version	2.1.0	Same as engine	Stored in CalculationSnapshot
Factor set version	Provider-defined	DEFRA-2025, SEAI-2024.1	Per provider, per import batch
17.2 Database Schema Versioning
The RC2 database schema is versioned via Supabase migrations (supabase/migrations/). The currently active version is tracked in system_settings:


SELECT settings_json->>'active_schema_version' FROM system_settings;
-- "2.0.0-rc2"
Future schema changes follow the migration naming convention: {timestamp}_{description}.sql.

17.3 Provider Data Versioning
Every emission_factors row has an import_batch_id that links to import_batches. The import_batches table records:

provider_key: which provider
provider_version: the provider's own version string (e.g., "2025.1")
source_checksum: SHA-256 of the source file — independent verification possible
18. Caching Strategy
Cache	Scope	TTL	Invalidation Trigger
FactorSearchIndex	Process memory	Infinite (until import)	ImportCompleted, ImportRolledBack events
OrganizationMetadata	TTL cache	5 minutes	Any metadata update
MatchingPipelineConfig	TTL cache	1 minute	Admin changes config
ReportTemplate	TTL cache	10 minutes	Template update
GLossary	TTL cache	1 hour	Glossary update
BenchmarkData	Request-scoped	Per request	N/A (computed fresh)
No database query should be repeated within the same request. Repositories implement internal caching where appropriate.

19. Security Model
19.1 Authentication
Concern	Implementation
User auth	Supabase Auth (email/password, magic link, OAuth, MFA)
JWT verification	FastAPI validates JWT against Supabase Auth on every request
API key (backend-to-backend)	Not used. All processing requests come from authenticated frontend users.
19.2 Authorization
Layer	Mechanism
Frontend CRUD	Supabase RLS policies (164 policies, RC2 verified)
Frontend processing requests	JWT → FastAPI validates user identity → engine authorises by org membership
Backend data access	Service role key (bypasses RLS) — used only within FastAPI container
Admin operations	JWT + require_admin FastAPI dependency
19.3 Data Isolation
The service role key is stored in environment variables only — never in code or config files committed to git.
.env is in .gitignore. .env.example contains placeholder values.
The service role client is a singleton created at app startup.
20. Admin Platform
20.1 Provider Management
The admin dashboard (React) must support:

Feature	Description
Provider Registry	List all registered providers (DEFRA, SEAI, EPA, etc.) with metadata
Import History	Full history of every import: date, user, rows imported, errors, status
Import Validation	Preview validation results before committing; approve/reject imports
Rollback	Initiate rollback to a previous version; view rollback history
Quality Reports	Per-provider quality metrics: duplicate rate, missing factor rate, data freshness
Version Management	Activate/deactivate specific versions; compare two versions side by side
Factor Search	Search the full factor database across all providers and versions
Alias Management	Manage organisation-specific activity aliases (synonyms)
Matching Pipeline Config	Configure which stages are enabled, set thresholds
Audit Viewer	Search and filter the audit trail; export to CSV for external audit
20.2 Admin API Endpoints
Method	Path	Description
GET	/api/v2/admin/providers	List registered providers
GET	/api/v2/admin/providers/{key}	Provider details + import history
POST	/api/v2/admin/imports	Trigger a new import
GET	/api/v2/admin/imports	List import batches
GET	/api/v2/admin/imports/{id}	Import batch detail
POST	/api/v2/admin/imports/{id}/rollback	Rollback an import
GET	/api/v2/admin/audit	Query audit trail
GET	/api/v2/admin/audit/export	Export audit trail as CSV
GET	/api/v2/admin/aliases	List activity aliases
POST	/api/v2/admin/aliases	Create an alias
DELETE	/api/v2/admin/aliases/{id}	Delete an alias
GET	/api/v2/admin/matching-config	Get pipeline configuration
PUT	/api/v2/admin/matching-config	Update pipeline configuration
21. Coding Standards
21.1 Python
Python 3.12+. from __future__ import annotations in every file.
Type hints on every function signature. mypy --strict in CI.
Domain objects: @dataclass(frozen=True) — immutable, behaviour-rich.
API contracts: Pydantic v2 BaseModel for request/response validation.
Repositories: Abstract base classes with typed method signatures.
Engines: Classes with constructor injection, single public async method.
No dict returns from any engine or repository method — always a domain object or dataclass.
No print() — structlog for structured logging.
No raw **kwargs or *args in public interfaces.
ruff for linting + formatting. black-compatible config.
Imports: Absolute imports within the backend/ package. No relative imports.
21.2 File Organisation
One class per file (except small helper dataclasses grouped in the same file).
File name matches the primary class: calculation_engine.py → CalculationEngine.
__init__.py exports the public API of each package.
21.3 Testing
Unit tests: one test file per engine, one test file per domain object.
Mock repositories for unit tests. No Supabase connection needed.
Integration tests: real Supabase test DB, apply RC2 migrations before test run.
Contract tests: OpenAPI schema validation via schemathesis.
Coverage target: 90%+ on domain/, 85%+ on engines/.
22. Architecture Decision Records
ADR-1: Four-Layer Architecture
Decision: Strict 4-layer architecture: API → Engine → Domain → Repository. Domain layer has zero external dependencies.

Rationale: Each layer is independently testable. Domain logic survives database, framework, and API changes. Repositories can be swapped (e.g., Supabase → direct PostgreSQL) without touching business logic.

ADR-2: Provider Plugin Pattern
Decision: Emission factor providers are plugins implementing a ProviderPlugin abstract interface. The ImportMappingEngine imports only the abstract interface.

Rationale: Adding a new jurisdiction requires only a new plugin file. Zero changes to the matching, calculation, or reporting engines. Provider-specific logic is encapsulated and auditable.

ADR-3: Multi-Stage Matching Pipeline
Decision: Factor matching is a configurable staged pipeline (exact → natural key → aliases → keyword → fuzzy → semantic → human). Each stage produces a confidence score and can be independently enabled/disabled.

Rationale: Different stages have different performance/cost profiles. Simple matches are fast and free. AI-based matching is optional and expensive. Admin can configure the pipeline per organisation or globally.

ADR-4: AI Isolation
Decision: AI extracts structured fields from unstructured text. The Matching Engine — never the AI — selects the emission factor.

Rationale: Emission factor selection must be deterministic, auditable, and reproducible. AI output is non-deterministic and cannot produce an audit trail. By keeping AI as a field extractor only, we maintain auditability while leveraging AI for the hard problem of understanding invoices/bills.

ADR-5: Calculation Snapshots for Reproducibility
Decision: Every calculation stores a complete CalculationSnapshot containing all inputs, the factor used, a content hash, and the engine version.

Rationale: Auditors must be able to verify any calculation from any year. The content hash provides tamper detection. The snapshot is immutable and never purged.

ADR-6: Versioned Imports
Decision: Emission factor imports are versioned. emission_factors rows are never deleted or overwritten. An import_batches table tracks every import. Only one batch is "active" per (provider, year). Rollback deactivates the current batch and reactivates the previous one.

Rationale: Data provenance is critical for carbon accounting. Auditors must be able to trace any factor to its source import. A mistaken import must be reversible without data loss.

ADR-7: In-Process Event Bus
Decision: Domain events are published and handled via an in-process event bus. No external message queue.

Rationale: The system's event volume is low (dozens per minute). An external queue adds operational complexity without proportional benefit. The event bus is sufficient for decoupling engines, audit trail, and async side effects.

ADR-8: In-Memory Search Index
Decision: The emission factors table (~7000 rows per provider per year) is loaded into an in-memory inverted index at startup and rebuilt on import.

Rationale: Sub-millisecond lookups without database round-trips. The full dataset fits in ~6MB per provider. Cache invalidation is trivial (rebuild on import).

ADR-9: Supabase for CRUD, FastAPI for Processing
Decision: React communicates directly with Supabase for all CRUD. FastAPI exposes only processing endpoints. FastAPI uses the service role key for backend data access.

Rationale: Eliminates ~30K lines of CRUD route code. RLS provides database-level authorization. FastAPI focuses exclusively on business logic that cannot be expressed in SQL.

ADR-10: Domain Objects over ORM
Decision: Domain objects are plain Python dataclasses. No ORM (SQLAlchemy, Prisma). Repositories manually map between domain objects and Supabase responses.

Rationale: An ORM couples the domain model to the database schema. Manual mapping is explicit, auditable, and survives schema evolution without magic. The mapping code is ~10 lines per entity — well worth the explicitness.

23. Future Expansion Strategy
23.1 New Providers
Adding a new emission-factor provider (e.g., Netherlands, Germany, Australia):

Create providers/{country}/plugin.py implementing ProviderPlugin
Implement discover(), parse(), normalise(), validate(), map_to_schema()
Register via @register decorator
Write provider-specific tests
No changes to any engine, repository, or domain class
23.2 New Matching Stages
Adding a new matching pipeline stage (e.g., ML-based ranking):

Create engines/matching_stages/{new_stage}.py implementing MatchingStage
Add to MatchingPipelineConfig.stages as an available option
No changes to FactorMatchingEngine — it iterates over configured stages
23.3 New Calculation Methodologies
Adding a new calculation method (e.g., lifecycle analysis):

Add new Methodology enum value in domain/calculation.py
Implement the calculation logic in CalculationEngine._calculate_{method}()
No changes to any other engine
23.4 New Report Types
Adding a new report standard (e.g., TCFD, GRI):

Create a new report template in the report_templates table
Implement section builders in engines/report_generation.py
No changes to any other engine
24. Risks & Trade-offs
Risk	Mitigation
Service role key compromise	Key stored in env vars only. Rotate regularly. Audit all service-role queries.
In-memory index memory growth	7000 rows × N providers. At 100 providers, ~600MB. Acceptable. Add LRU eviction for inactive providers if needed.
Event handler failures	Handlers are fire-and-forget. Failures are logged but do not block the primary flow. Critical handlers can be made synchronous.
AI extraction cost	Each extraction costs ~$0.01-0.05. A customer uploading 100 documents/month = $1-5/month. Acceptable. Configurable to disable per organisation.
No external message queue	Sufficient for current volume. If throughput exceeds ~100 events/second, migrate to Redis/Kafka — the event bus interface abstracts the implementation.
Manual repository mapping	~10 lines per entity. Explicit, testable. No performance concern — mapping is not a bottleneck compared to network I/O.
Provider plugin discoverability	Explicit registry (decorator) is simpler and more auditable than setuptools entry points. Adding a provider requires one import in registry.py.
25. Migration Notes from v2.0
25.1 What Changes from v2.0
v2.0	v2.1
Engines call Supabase directly	Engines call repositories (abstract interfaces)
No domain layer	Rich domain objects with behaviour
Single DEFRA import engine	Provider plugin architecture with 6+ providers
Single-stage factor lookup	Multi-stage configurable matching pipeline
No calculation snapshots	Every calculation stores an immutable snapshot
No import versioning	Versioned imports with rollback
Direct engine-to-engine calls	Domain events via event bus
No formal audit framework	Automatic audit of every engine action
Factor lookup hits DB every time	In-memory inverted search index
Admin manages factors	Admin manages providers, imports, versions, aliases, and pipeline config
25.2 Migration Path
Repository layer first — extract all Supabase access from utils/emissions.py and route files into repositories. Engines continue to work (they call repositories instead of Supabase directly).
Domain layer — introduce domain objects. Repositories return domain objects instead of dicts.
Engine refactor — rewrite engines to use domain objects and repositories. Existing endpoints continue to work.
Provider plugins — extract DEFRA import logic into providers/defra/plugin.py. The existing import CLI becomes a thin wrapper.
Event bus — introduce incrementally. Start with CalculationCompleted for dashboard updates.
Search index — add as a cache layer in EmissionFactorsRepository. Transparent to engines.
Matching pipeline — replace the single get_emission_factor() function with the staged pipeline. Expose the old interface as a compatibility shim.
Calculation snapshots — add the calculation_snapshots table and start writing snapshots alongside existing emissions_logs rows.
25.3 Backward Compatibility
No breaking API changes. Existing endpoints (POST /calculate, POST /match-factor) continue to work with the same request/response contracts. New admin endpoints are additive.

End of Backend Architecture v2.1 — Frozen Specification

