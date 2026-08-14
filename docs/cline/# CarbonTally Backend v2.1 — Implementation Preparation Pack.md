CarbonTally Backend v2.1 — Implementation Preparation Pack
Version: 2.1.0
Status: FROZEN — Single Source of Truth for Implementation
Date: 2026-08-06
References: Backend Architecture v2.1 (FROZEN), Architecture Readiness Review (Final Gate)

Table of Contents
Database Migration Plan
Domain Model Catalogue
Repository Interface Catalogue
Dependency Injection Graph
Package and Folder Structure
Implementation Order
Traceability Matrix
Readiness Review Issue Resolution
1. Database Migration Plan
1.1 Migration Order (Phase 0 — Must Complete Before Any Application Code)
All migrations follow Supabase convention: {timestamp}_{description}.sql. Every migration is idempotent.

#	Migration File	Description	Dependencies
M1	{ts}_add_import_batches.sql	CREATE TABLE IF NOT EXISTS public.import_batches	None
M2	{ts}_add_emission_factors_import_batch.sql	ALTER TABLE emission_factors ADD COLUMN import_batch_id UUID + FK → import_batches(id) + index	M1
M3	{ts}_add_calculation_snapshots.sql	CREATE TABLE IF NOT EXISTS public.calculation_snapshots	None
M4	{ts}_add_emissions_logs_snapshot.sql	ALTER TABLE emissions_logs ADD COLUMN snapshot_id UUID + FK → calculation_snapshots(id) + index	M3
M5	{ts}_add_domain_events.sql	CREATE TABLE IF NOT EXISTS public.domain_events + indexes	None
M6	{ts}_add_factor_aliases.sql	CREATE TABLE IF NOT EXISTS public.factor_aliases + unique index	None
M7	{ts}_add_dpq_workflow_columns.sql	ALTER TABLE document_processing_queue ADD COLUMN workflow_error_count INT DEFAULT 0, ADD COLUMN workflow_next_retry_at TIMESTAMPTZ	None
M8	{ts}_add_new_table_rls.sql	RLS policies for import_batches, calculation_snapshots, domain_events, factor_aliases	M1, M3, M5, M6
1.2 Table Definitions
M1 — import_batches

Column	Type	Constraints
id	UUID PK	DEFAULT extensions.uuid_generate_v4()
provider_key	VARCHAR	NOT NULL
provider_version	VARCHAR	NOT NULL
source_file	TEXT	NOT NULL
source_checksum	VARCHAR(64)	NOT NULL
reporting_year	INTEGER	NOT NULL
status	VARCHAR	NOT NULL DEFAULT 'pending', CHECK IN ('pending','importing','completed','failed','rolled_back')
rows_total	INTEGER	DEFAULT 0
rows_imported	INTEGER	DEFAULT 0
rows_skipped	INTEGER	DEFAULT 0
rows_duplicate	INTEGER	DEFAULT 0
errors	JSONB	nullable
is_active	BOOLEAN	NOT NULL DEFAULT FALSE
created_at	TIMESTAMPTZ	DEFAULT NOW()
created_by	UUID	nullable
rolled_back_from	UUID	FK → import_batches(id), nullable
updated_at	TIMESTAMPTZ	DEFAULT NOW()
M2 — emission_factors.import_batch_id

Column: import_batch_id UUID (nullable — existing rows have no batch)
FK: REFERENCES import_batches(id) ON DELETE SET NULL
Index: CREATE INDEX idx_emission_factors_import_batch ON emission_factors(import_batch_id)
Guard: ADD COLUMN IF NOT EXISTS; constraint guarded via DO block checking pg_constraint
M3 — calculation_snapshots

Column	Type	Constraints
id	UUID PK	DEFAULT extensions.uuid_generate_v4()
organization_id	UUID	NOT NULL, FK → organizations(id) ON DELETE CASCADE
activity	VARCHAR	NOT NULL
activity_type	VARCHAR	NOT NULL
quantity	NUMERIC	NOT NULL, CHECK (quantity >= 0)
quantity_unit	VARCHAR	NOT NULL
co2e_multiplier	NUMERIC	NOT NULL
co2e_kg	NUMERIC	NOT NULL, CHECK (co2e_kg >= 0)
scope	VARCHAR	nullable
date	DATE	NOT NULL
factor_id	UUID	NOT NULL, FK → emission_factors(id)
factor_source	VARCHAR	nullable
factor_set	VARCHAR	nullable
import_batch_id	UUID	FK → import_batches(id), nullable
reporting_year	INTEGER	NOT NULL
methodology	VARCHAR	NOT NULL
algorithm_version	VARCHAR	NOT NULL
content_hash	VARCHAR(64)	NOT NULL
calculated_at	TIMESTAMPTZ	DEFAULT NOW()
calculated_by	VARCHAR	nullable
request_id	UUID	nullable
M4 — emissions_logs.snapshot_id

Column: snapshot_id UUID (nullable)
FK: REFERENCES calculation_snapshots(id) ON DELETE SET NULL
Index: CREATE INDEX idx_emissions_logs_snapshot ON emissions_logs(snapshot_id)
M5 — domain_events

Column	Type	Constraints
id	UUID PK	DEFAULT extensions.uuid_generate_v4()
event_type	VARCHAR	NOT NULL
occurred_at	TIMESTAMPTZ	NOT NULL DEFAULT NOW()
correlation_id	UUID	NOT NULL
aggregate_id	UUID	NOT NULL
aggregate_type	VARCHAR	NOT NULL
payload	JSONB	NOT NULL
created_at	TIMESTAMPTZ	DEFAULT NOW()
Indexes: idx_domain_events_correlation (correlation_id), idx_domain_events_aggregate (aggregate_type, aggregate_id)

M6 — factor_aliases

Column	Type	Constraints
id	UUID PK	DEFAULT extensions.uuid_generate_v4()
organization_id	UUID	FK → organizations(id) ON DELETE CASCADE, nullable (NULL = global alias)
alias_text	VARCHAR	NOT NULL
target_activity_type	VARCHAR	NOT NULL
target_provider_key	VARCHAR	NOT NULL
created_by	UUID	nullable
created_at	TIMESTAMPTZ	DEFAULT NOW()
Unique index: idx_factor_aliases_unique ON factor_aliases (COALESCE(organization_id, '00000000-0000-0000-0000-000000000000'::uuid), alias_text)

1.3 RLS Policies (M8)
Table	Policy Name	Role	Perm	Expression
import_batches	(none)	authenticated	ALL	deny-by-default
import_batches	(none)	service_role	ALL	bypasses RLS
calculation_snapshots	calc_snapshots_select_own	authenticated	SELECT	organization_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())
calculation_snapshots	(none)	authenticated	INSERT/UPDATE/DELETE	deny-by-default
domain_events	(none)	authenticated	ALL	deny-by-default
domain_events	(none)	service_role	ALL	bypasses RLS
factor_aliases	aliases_select_own	authenticated	SELECT	org_id IS NULL OR org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())
factor_aliases	aliases_insert_own	authenticated	INSERT	org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())
factor_aliases	aliases_delete_own	authenticated	DELETE	org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())
1.4 Migration Verification Checklist
 supabase db reset completes without errors
 All new tables appear in information_schema.tables
 All new columns appear in information_schema.columns
 All new FKs appear in pg_constraint with convalidated = true
 All new indexes appear in pg_indexes
 All new RLS policies appear in pg_policies
 supabase db diff shows zero differences
2. Domain Model Catalogue
2.1 File Map

domain/
├── __init__.py                  # Re-exports all public types
├── factor.py                    # EmissionFactor, FactorSet, FactorSetMetadata
├── calculation.py               # CalculationSnapshot, CalculationResult, VerificationResult, CalculationMethodology (StrEnum)
├── document.py                  # Document, ExtractionResult, ExtractedPage, ExtractedTable, ExtractionField
├── organization.py              # Organization, Facility, Asset, OrganizationMetadata
├── report.py                    # ReportRequest, GeneratedReport, ReportSection, ReportTemplate
├── workflow.py                  # WorkflowState, WorkflowDefinition, DomainEvent (ABC), 12 concrete events, Transition, Saga
├── provider.py                  # ProviderInfo, ProviderVersion, ImportBatch, ImportError, DiscoveryResult, DiscoveredSheet, RawFactorRow, NormalisedFactor, ImportResult
├── matching.py                  # MatchRequest, MatchResult, Suggestion, FactorAlias, StageResult, MatchingPipelineConfig, MatchingStage (ABC)
└── audit.py                     # AuditEntry, AuditTrail
2.2 Complete Inventory
domain/factor.py
Type	Kind	Key Fields / Methods
EmissionFactor	@dataclass(frozen=True)	id: str, reporting_year: int, activity_type: str, co2e_multiplier: Decimal, unit: Optional[str], scope: Optional[str], factor_source: str, factor_set: str, country: str, provider_key: str, import_batch_id: str, natural_key: tuple[str,...]; methods: calculate_emissions(quantity, unit) → Decimal, with_new_year(year) → EmissionFactor
FactorSet	@dataclass(frozen=True)	provider_key: str, reporting_year: int, version: str, factors: tuple[EmissionFactor,...], metadata: FactorSetMetadata; methods: find_by_natural_key(key) → Optional[EmissionFactor], search_by_activity(act, unit) → list[EmissionFactor]
FactorSetMetadata	@dataclass(frozen=True)	row_count: int, checksum: str, imported_at: datetime, source_path: str
domain/calculation.py
Type	Kind	Key Fields / Methods
CalculationMethodology	StrEnum	DIRECT_MULTIPLY="direct_multiply", DISTANCE_BASED="distance_based", SPEND_BASED="spend_based", AREA_BASED="area_based", MASS_BALANCE="mass_balance"
CalculationSnapshot	@dataclass(frozen=True)	id: str, organization_id: str, activity: str, activity_type: str, quantity: Decimal, quantity_unit: str, co2e_multiplier: Decimal, co2e_kg: Decimal, scope: Optional[str], date: date, factor_id: str, factor_source: str, factor_set: str, import_batch_id: str, reporting_year: int, methodology: str, algorithm_version: str, content_hash: str, calculated_at: datetime, calculated_by: str, request_id: str; methods: verify_reproducibility(recomputed) → bool, build_content_hash() → str
CalculationResult	@dataclass(frozen=True)	co2e_kg: Decimal, co2e_tonnes: Decimal, snapshot: CalculationSnapshot, factor_used: EmissionFactor, methodology: CalculationMethodology
VerificationResult	@dataclass(frozen=True)	match: bool, discrepancy: Optional[Decimal], tampered: bool
domain/matching.py
Type	Kind	Key Fields / Methods
MatchingStage	ABC	Abstract methods: name: str (property), execute(request, index) → StageResult
MatchRequest	@dataclass(frozen=True)	id: str, activity: str, unit: Optional[str], country: str, reporting_year: int, scope: Optional[str], organization_id: Optional[str], preferred_provider: Optional[str], max_stages: int = 6
StageResult	@dataclass(frozen=True)	stage_name: str, matched: bool, factor: Optional[EmissionFactor], confidence: float, score: float, reason: str, provider: Optional[str], is_definitive: bool
MatchResult	@dataclass(frozen=True)	status: str ("matched"/"no_match"/"ambiguous"), factor: Optional[EmissionFactor], confidence: float, methodology: str, provider: Optional[str], stages_executed: tuple[str,...], suggestions: tuple[Suggestion,...], processing_time_ms: int, request_id: str; static: no_match(suggestions, stages) → MatchResult
Suggestion	@dataclass(frozen=True)	factor: EmissionFactor, score: float, reason: str, stage: str
FactorAlias	@dataclass(frozen=True)	id: str, organization_id: Optional[str], alias_text: str, target_activity_type: str, target_provider_key: str, created_by: str, created_at: datetime
MatchingPipelineConfig	@dataclass	stages: tuple[str,...], fuzzy_threshold: float = 0.85, keyword_min_confidence: float = 0.80, semantic_enabled: bool = False, semantic_min_confidence: float = 0.70, max_suggestions: int = 10, prefer_provider: Optional[str], restrict_country: Optional[str]
domain/provider.py
Type	Kind	Key Fields
ProviderInfo	@dataclass(frozen=True)	key: str, name: str, jurisdiction: str, country_codes: tuple[str,...], website: str, license: str, latest_version: str, publisher: str, language: str, documentation_url: Optional[str]
ProviderVersion	@dataclass(frozen=True)	provider_key: str, version: str, release_date: date, status: str, import_batch_id: str, row_count: int, checksum: str
ImportBatch	@dataclass(frozen=True)	id: str, provider_key: str, provider_version: str, source_file: str, source_checksum: str, reporting_year: int, status: str, rows_total: int, rows_imported: int, rows_skipped: int, rows_duplicate: int, errors: tuple[ImportError,...], is_active: bool, created_at: datetime, created_by: str, rolled_back_from: Optional[str]; methods: activate() → ImportBatch, rollback(replaced_by) → ImportBatch
ImportError	@dataclass(frozen=True)	row_number: int, field: str, message: str, severity: str
DiscoveryResult	@dataclass(frozen=True)	provider_key: str, provider_version: str, source_path: str, source_checksum: str, reporting_year: int, sheets: tuple[DiscoveredSheet,...]
DiscoveredSheet	@dataclass(frozen=True)	name: str, sheet_type: str, max_row: int, max_col: int, header_row: Optional[int], columns: tuple[tuple[str,int],...]
RawFactorRow	@dataclass(frozen=True)	sheet_name: str, row_number: int, cells: dict[str, Any]
NormalisedFactor	@dataclass(frozen=True)	provider_key: str, reporting_year: int, activity_type: str, co2e_multiplier: Decimal, unit: Optional[str], scope: Optional[str], country: str, metadata: dict
ImportResult	@dataclass(frozen=True)	batch: ImportBatch, rows_imported: int, rows_skipped: int, rows_duplicate: int, errors: tuple[ImportError,...], artifacts: dict
domain/workflow.py
Type	Kind	Key Fields
DomainEvent	ABC, @dataclass(frozen=True)	event_id: str, occurred_at: datetime, correlation_id: str, aggregate_id: str, aggregate_type: str
DocumentUploaded	extends DomainEvent	document_id: str, organization_id: str, storage_path: str
ExtractionRequested	extends DomainEvent	document_id: str
ExtractionCompleted	extends DomainEvent	document_id: str, page_count: int, confidence: float
FieldsExtracted	extends DomainEvent	document_id: str, fields: dict, confidence: float
CalculationRequested	extends DomainEvent	match_request_id: str, organization_id: str
CalculationCompleted	extends DomainEvent	snapshot_id: str, co2e_kg: Decimal
ReportGenerated	extends DomainEvent	report_id: str, organization_id: str, storage_url: str
ImportStarted	extends DomainEvent	batch_id: str, provider_key: str
ImportCompleted	extends DomainEvent	batch_id: str, rows_imported: int
ImportRolledBack	extends DomainEvent	batch_id: str, replaced_by: str
FactorMatched	extends DomainEvent	request_id: str, factor_id: str, confidence: float
FactorNotFound	extends DomainEvent	request_id: str, activity: str, unit: Optional[str]
ValidationFailed	extends DomainEvent	entity_type: str, entity_id: str, errors: list
WorkflowStateChanged	extends DomainEvent	entity_type: str, entity_id: str, from_state: str, to_state: str
WorkflowDefinition	@dataclass(frozen=True)	name: str, states: tuple[str,...], transitions: tuple[tuple[str,str],...]; method: can_transition(from, to) → bool
Transition	@dataclass(frozen=True)	workflow_id: str, from_state: str, to_state: str, applied_at: datetime, applied_by: str
Saga	ABC	Abstract: steps: list[SagaStep], compensations: list[SagaStep]; execute(), compensate()
WorkflowState	@dataclass(frozen=True)	entity_type: str, entity_id: str, current_state: str, previous_state: Optional[str], error_count: int, max_retries: int, next_retry_at: Optional[datetime]
domain/document.py
Type	Kind	Key Fields
Document	@dataclass(frozen=True)	id: str, organization_id: str, filename: str, storage_path: str, file_type: str, status: str, uploaded_at: datetime, uploaded_by: str
ExtractionResult	@dataclass(frozen=True)	raw_text: str, pages: tuple[ExtractedPage,...], tables: tuple[ExtractedTable,...], metadata: dict, confidence: float
ExtractedPage	@dataclass(frozen=True)	page_number: int, text: str, confidence: float
ExtractedTable	@dataclass(frozen=True)	page_number: int, rows: tuple[tuple[str,...],...], headers: tuple[str,...]
ExtractionField	@dataclass(frozen=True)	field_name: str, value: Any, confidence: float, source: str
domain/organization.py
Type	Kind	Key Fields
Organization	@dataclass(frozen=True)	id: str, name: str, country: str, is_active: bool, created_at: datetime
Facility	@dataclass(frozen=True)	id: str, organization_id: str, name: str, address: Optional[str], postcode: Optional[str]
Asset	@dataclass(frozen=True)	id: str, facility_id: str, organization_id: str, name: str, asset_type: str
OrganizationMetadata	@dataclass(frozen=True)	total_floor_area_sqm: Optional[float], occupied_floor_area_sqm: Optional[float], fte_count: Optional[int], annual_revenue_gbp: Optional[Decimal], sector: Optional[str]
domain/report.py
Type	Kind	Key Fields
ReportRequest	@dataclass(frozen=True)	organization_id: str, report_type: str, reporting_year: int, template_id: Optional[str], sections: tuple[str,...], options: dict
GeneratedReport	@dataclass(frozen=True)	id: str, organization_id: str, report_type: str, reporting_year: int, storage_url: str, file_size_bytes: int, generated_at: datetime, page_count: int
ReportSection	@dataclass(frozen=True)	section_id: str, title: str, content: str, order: int
ReportTemplate	@dataclass(frozen=True)	id: str, name: str, report_type: str, structure: dict
domain/audit.py
Type	Kind	Key Fields
AuditEntry	@dataclass(frozen=True)	id: str, timestamp: datetime, engine: str, engine_version: str, action: str, request_id: str, user_id: str, organization_id: Optional[str], input_summary: dict, output_summary: dict, decision: str, confidence: Optional[float], processing_time_ms: int, status: str, error_code: Optional[str], correlation_id: str, metadata: dict
AuditTrail	@dataclass(frozen=True)	entries: tuple[AuditEntry,...], correlation_id: str
3. Repository Interface Catalogue
3.1 Repository Base Class
File: data/base.py


T = TypeVar("T")

class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: str) -> Optional[T]: ...
    @abstractmethod
    async def save(self, entity: T) -> T: ...
    @abstractmethod
    async def delete(self, id: str) -> None: ...
3.2 EmissionFactorsRepository
File: data/emission_factors.py
Aggregate Root: EmissionFactor

Method	Signature	Purpose
get	(id: str) → Optional[EmissionFactor]	Single factor by ID
find_by_natural_key	(year: int, activity_type: str, country: str, unit: Optional[str], scope: Optional[str]) → Optional[EmissionFactor]	Exact RC2 natural-key lookup
find_by_activity	(activity: str, unit: Optional[str], year: Optional[int], country: Optional[str], provider: Optional[str], limit: int) → list[EmissionFactor]	Keyword/activity search
bulk_upsert	(factors: list[EmissionFactor]) → int	Idempotent natural-key upsert; returns inserted count
get_active_set	(provider: str, year: int) → list[EmissionFactor]	All active factors for a provider + year
deactivate_by_batch	(batch_id: str) → int	Set import_batch_id = NULL for all factors in a batch
load_all_for_index	() → list[EmissionFactor]	Every active factor (for search index loading)
count_by_provider	(provider: str) → int	Total factor count for a provider
save	(entity: EmissionFactor) → EmissionFactor	Single factor upsert
delete	(id: str) → None	(Rarely used — factors are deactivated, not deleted)
3.3 EmissionsLogsRepository
File: data/emissions_logs.py
Aggregate Root: EmissionLog (operational record)

Method	Signature	Purpose
create	(org_id: str, factor_id: str, quantity: Decimal, unit: str, scope: Optional[str], date: date, asset_id: Optional[str], facility_id: Optional[str], snapshot_id: str) → EmissionLog	Insert one emissions record
find_by_org	(org_id: str, period: DateRange) → list[EmissionLog]	All logs for an org in a date range
aggregate	(org_id: str, period: DateRange, group_by: str) → EmissionsAggregate	Sums, scope breakdowns
count_by_scope	(org_id: str, year: int) → dict[str, int]	Counts per scope
get	(id: str) → Optional[EmissionLog]	Single log by ID
save	(entity: EmissionLog) → EmissionLog	Update
delete	(id: str) → None	(Not used in normal flow)
3.4 OrganizationsRepository
File: data/organizations.py

Method	Signature	Purpose
get_by_id	(org_id: str) → Optional[Organization]	Organization + metadata
get_members	(org_id: str) → list[OrganizationMember]	Members with roles
get_metadata	(org_id: str) → Optional[OrganizationMetadata]	Floor area, FTE, revenue
get_facilities	(org_id: str) → list[Facility]	All facilities
get_assets	(org_id: str) → list[Asset]	All assets
update_metadata	(org_id: str, data: OrganizationMetadata) → OrganizationMetadata	Upsert metadata
get	(id: str) → Optional[Organization]	(inherited)
save	(entity: Organization) → Organization	(inherited)
delete	(id: str) → None	(inherited)
3.5 DocumentsRepository
File: data/documents.py

Method	Signature	Purpose
create_from_upload	(org_id: str, storage_path: str, filename: str, file_type: str) → Document	Create document record
update_status	(doc_id: str, status: str) → Document	Update processing status
get_pending_extraction	() → list[Document]	Documents ready for extraction
get_by_org	(org_id: str) → list[Document]	All docs for an org
get	(id: str) → Optional[Document]	(inherited)
save	(entity: Document) → Document	(inherited)
delete	(id: str) → None	(inherited)
3.6 ImportsRepository
File: data/imports.py
Aggregate Root: ImportBatch

Method	Signature	Purpose
create_batch	(provider: str, version: str, year: int, source: str, checksum: str, created_by: str) → ImportBatch	Create pending batch
complete_batch	(batch_id: str, total: int, imported: int, skipped: int, duplicates: int, errors: list[ImportError]) → ImportBatch	Mark as completed
fail_batch	(batch_id: str, errors: list[ImportError]) → ImportBatch	Mark as failed
activate_batch	(batch_id: str) → ImportBatch	Set is_active = TRUE
deactivate_batch	(batch_id: str) → ImportBatch	Set is_active = FALSE
rollback_batch	(batch_id: str, replaced_by: str) → ImportBatch	Rollback with replacement
get_active	(provider: str, year: int) → Optional[ImportBatch]	Currently active batch
get_history	(provider: str) → list[ImportBatch]	Full history for a provider
get	(id: str) → Optional[ImportBatch]	(inherited)
save	(entity: ImportBatch) → ImportBatch	(inherited — domain objects are immutable; save maps fields to UPDATE)
delete	(id: str) → None	(Not used — batches are immutable)
3.7 ReportsRepository
File: data/reports.py

Method	Signature	Purpose
create_generation_request	(org_id: str, report_type: str, year: int, template_id: Optional[str]) → GeneratedReport (status=pending)	Create report request
complete_generation	(report_id: str, storage_url: str, file_size: int, page_count: int) → GeneratedReport	Mark as completed
get_by_org	(org_id: str) → list[GeneratedReport]	All reports for an org
get	(id: str) → Optional[GeneratedReport]	(inherited)
save	(entity: GeneratedReport) → GeneratedReport	(inherited)
delete	(id: str) → None	(inherited)
3.8 AuditRepository
File: data/audit.py

Method	Signature	Purpose
record	(entry: AuditEntry) → AuditEntry	Append one audit entry
query	(filters: AuditQuery) → list[AuditEntry]	Search audit trail
export_csv	(filters: AuditQuery) → str	Export to CSV
get_by_correlation	(correlation_id: str) → list[AuditEntry]	All entries for one request
get	(id: str) → Optional[AuditEntry]	Single entry
save	(entity: AuditEntry) → AuditEntry	(inherited — append-only, save = insert)
delete	(id: str) → None	(Not used — audit is immutable)
3.9 EventsRepository
File: data/events.py

Method	Signature	Purpose
store	(event: DomainEvent) → DomainEvent	Append one event
get_by_correlation	(correlation_id: str) → list[DomainEvent]	All events for a request
replay	(aggregate_id: str) → list[DomainEvent]	Replay events for an aggregate
get	(id: str) → Optional[DomainEvent]	Single event
save	(entity: DomainEvent) → DomainEvent	(inherited — append-only)
delete	(id: str) → None	(Not used — events are immutable)
3.10 FactorAliasesRepository
File: data/factor_aliases.py

Method	Signature	Purpose
find_by_alias	(alias: str, org_id: Optional[str]) → Optional[FactorAlias]	Lookup alias → target
get_global_aliases	() → list[FactorAlias]	All global aliases
get_org_aliases	(org_id: str) → list[FactorAlias]	Org-specific aliases
get	(id: str) → Optional[FactorAlias]	(inherited)
save	(entity: FactorAlias) → FactorAlias	(inherited — insert)
delete	(id: str) → None	(inherited)
4. Dependency Injection Graph
4.1 Wiring Diagram

┌─────────────────────────────────────────────────────────────────────┐
│  COMPOSITION ROOT  (api/dependencies.py)                            │
│                                                                      │
│  get_service_supabase() → Client (singleton, service-role)          │
│  get_event_bus()        → EventBus (singleton)                      │
│  get_search_index()     → FactorSearchIndex (singleton)             │
│  get_audit_logger()     → AuditLogger (singleton)                   │
│  get_alias_registry()   → AliasRegistry (singleton)                 │
│                                                                      │
│  REPOSITORIES (new instance per request — stateless)                 │
│  ┌─ EmissionFactorsRepository(supabase)                              │
│  ├─ EmissionsLogsRepository(supabase)                                │
│  ├─ OrganizationsRepository(supabase)                                │
│  ├─ DocumentsRepository(supabase)                                    │
│  ├─ ImportsRepository(supabase)                                      │
│  ├─ ReportsRepository(supabase)                                      │
│  ├─ AuditRepository(supabase)                                        │
│  ├─ EventsRepository(supabase)                                       │
│  └─ FactorAliasesRepository(supabase)                                 │
│                                                                      │
│  ENGINES (new instance per request — stateless)                      │
│  ┌─ FactorMatchingEngine                                              │
│  │   ├── factor_repo: EmissionFactorsRepository                      │
│  │   ├── search_index: FactorSearchIndex                             │
│  │   ├── alias_registry: AliasRegistry                               │
│  │   ├── event_bus: EventBus                                         │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  ├─ CalculationEngine                                                │
│  │   ├── factor_repo: EmissionFactorsRepository                      │
│  │   ├── logs_repo: EmissionsLogsRepository                          │
│  │   ├── org_repo: OrganizationsRepository                           │
│  │   ├── snapshots_repo: (via EmissionsLogsRepository or dedicated)  │
│  │   ├── matching_engine: FactorMatchingEngine                       │
│  │   ├── event_bus: EventBus                                         │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  ├─ ImportMappingEngine                                              │
│  │   ├── factor_repo: EmissionFactorsRepository                      │
│  │   ├── imports_repo: ImportsRepository                             │
│  │   ├── event_bus: EventBus                                         │
│  │   ├── audit_logger: AuditLogger                                   │
│  │   └── [provider: ProviderPlugin] — injected at call time          │
│  │                                                                    │
│  ├─ DocumentExtractionEngine                                         │
│  │   ├── documents_repo: DocumentsRepository                         │
│  │   ├── event_bus: EventBus                                         │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  ├─ AIExtractionEngine                                               │
│  │   ├── documents_repo: DocumentsRepository                         │
│  │   ├── llm_client: LLMClient                                       │
│  │   ├── event_bus: EventBus                                         │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  ├─ ReportGenerationEngine                                           │
│  │   ├── reports_repo: ReportsRepository                             │
│  │   ├── org_repo: OrganizationsRepository                           │
│  │   ├── logs_repo: EmissionsLogsRepository                          │
│  │   ├── calculation_engine: CalculationEngine                       │
│  │   ├── event_bus: EventBus                                         │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  ├─ ValidationEngine                                                 │
│  │   ├── logs_repo: EmissionsLogsRepository                          │
│  │   ├── org_repo: OrganizationsRepository                           │
│  │   ├── factor_repo: EmissionFactorsRepository                      │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  ├─ BenchmarkingEngine                                               │
│  │   ├── logs_repo: EmissionsLogsRepository                          │
│  │   ├── org_repo: OrganizationsRepository                           │
│  │   └── audit_logger: AuditLogger                                   │
│  │                                                                    │
│  └─ WorkflowOrchestrator                                             │
│      ├── workflows_repo: (uses DocumentsRepository + EventsRepository)│
│      ├── event_bus: EventBus                                         │
│      └── audit_logger: AuditLogger                                   │
└─────────────────────────────────────────────────────────────────────┘
4.2 Engine-to-Engine Dependencies

CalculationEngine
└── FactorMatchingEngine           (injected)

ReportGenerationEngine
└── CalculationEngine              (injected)

WorkflowOrchestrator
└── [dispatches to all engines via event handlers, not direct calls]

ImportMappingEngine
└── [calls ProviderPlugin methods directly — no engine-to-engine]
Rule: Engines call other engines ONLY through constructor injection (not through the event bus for request-response flows like calculation needing a factor match). The event bus is used for fire-and-forget side effects, not for synchronous request handling.

4.3 Infrastructure Singletons
Component	Scope	Initialization
Client (Supabase service-role)	Process singleton	infra/supabase.py::create_service_client()
EventBus	Process singleton	Created empty, handlers registered at startup
FactorSearchIndex	Process singleton	load(all_active) at startup; rebuilt on import events
AuditLogger	Process singleton	Wraps AuditRepository
LLMClient	Process singleton	Wraps OpenAI/Anthropic API
AliasRegistry	Process singleton	Loads from FactorAliasesRepository at startup
5. Package and Folder Structure

backend/
├── main.py                         # App factory (Uvicorn entry point)
│
├── api/                            # Route layer
│   ├── __init__.py
│   ├── router.py                   # Single FastAPI router
│   ├── dependencies.py             # Composition root — all DI wiring
│   ├── middleware.py               # JWT validation, request ID, audit context
│   └── contracts.py                # Pydantic request/response schemas
│
├── engines/                        # Business processing engines
│   ├── __init__.py
│   ├── factor_matching.py          # FactorMatchingEngine
│   ├── calculation.py              # CalculationEngine
│   ├── import_mapping.py           # ImportMappingEngine
│   ├── extraction.py               # DocumentExtractionEngine
│   ├── ai_extraction.py            # AIExtractionEngine
│   ├── report_generation.py        # ReportGenerationEngine
│   ├── validation.py               # ValidationEngine
│   ├── benchmarking.py             # BenchmarkingEngine
│   └── workflow.py                 # WorkflowOrchestrator
│
├── domain/                         # Domain model (pure Python, zero deps)
│   ├── __init__.py
│   ├── factor.py                   # EmissionFactor, FactorSet
│   ├── calculation.py              # CalculationSnapshot, CalculationMethodology, etc.
│   ├── document.py                 # Document, ExtractionResult, etc.
│   ├── organization.py             # Organization, Facility, Asset, etc.
│   ├── report.py                   # ReportRequest, GeneratedReport, etc.
│   ├── workflow.py                 # DomainEvent hierarchy, WorkflowDefinition, etc.
│   ├── provider.py                 # ProviderInfo, ImportBatch, DiscoveryResult, etc.
│   ├── matching.py                 # MatchRequest/Result, MatchingStage (ABC), etc.
│   └── audit.py                    # AuditEntry, AuditTrail
│
├── data/                           # Repository layer
│   ├── __init__.py
│   ├── base.py                     # AbstractRepository[T]
│   ├── emission_factors.py         # EmissionFactorsRepository
│   ├── emissions_logs.py           # EmissionsLogsRepository
│   ├── organizations.py            # OrganizationsRepository
│   ├── documents.py                # DocumentsRepository
│   ├── imports.py                  # ImportsRepository
│   ├── reports.py                  # ReportsRepository
│   ├── audit.py                    # AuditRepository
│   ├── events.py                   # EventsRepository
│   └── factor_aliases.py           # FactorAliasesRepository
│
├── infra/                          # Infrastructure components
│   ├── __init__.py
│   ├── supabase.py                 # Service-role client singleton
│   ├── event_bus.py                # In-process publish/subscribe
│   ├── search_index.py             # FactorSearchIndex (inverted index)
│   ├── cache.py                    # TTL cache
│   ├── llm_client.py               # OpenAI/Anthropic API client
│   ├── audit_logger.py             # Decorator-based audit logging
│   ├── config.py                   # All env vars + configuration
│   └── metrics.py                  # Prometheus metrics (future)
│
├── providers/                      # Emission factor provider plugins
│   ├── __init__.py
│   ├── base.py                     # ProviderPlugin (ABC)
│   ├── registry.py                 # @register decorator + get()
│   ├── defra/
│   │   ├── __init__.py
│   │   └── plugin.py               # DEFRAProvider(ProviderPlugin)
│   ├── seai/
│   │   ├── __init__.py
│   │   └── plugin.py               # SEAIProvider(ProviderPlugin)
│   ├── epa/
│   │   ├── __init__.py
│   │   └── plugin.py               # EPAProvider(ProviderPlugin)
│   ├── ademe/
│   │   ├── __init__.py
│   │   └── plugin.py               # ADEMEProvider(ProviderPlugin)
│   ├── ipcc/
│   │   ├── __init__.py
│   │   └── plugin.py               # IPCCProvider(ProviderPlugin)
│   └── custom/
│       ├── __init__.py
│       └── plugin.py               # CustomProvider(ProviderPlugin)
│
├── core/                           # Shared kernel
│   ├── __init__.py
│   ├── exceptions.py               # CarbonTallyError hierarchy
│   ├── types.py                    # Country, Unit, Scope, Year primitives
│   └── logging.py                  # structlog configuration
│
└── tests/
    ├── unit/
    │   ├── domain/                 # One test file per domain entity
    │   ├── engines/                # One test file per engine (mocked repos)
    │   └── providers/              # One test file per provider
    ├── integration/
    │   ├── conftest.py             # Test Supabase setup
    │   ├── test_repositories.py    # Repository integration
    │   ├── test_matching.py        # End-to-end matching
    │   ├── test_calculation.py     # Calculation + snapshots
    │   ├── test_import.py          # Import pipeline
    │   └── test_workflow.py        # Workflow + events
    ├── contracts/
    │   ├── test_api_contracts.py   # OpenAPI schema validation
    │   └── provider_plugin_contract.py  # Shared provider test suite
    └── fixtures/
        ├── seed_factors.py         # Test factor data
        ├── seed_orgs.py            # Test organization data
        └── seed_documents.py       # Test document data
6. Implementation Order
Phase 0 — Database Migrations (2 days)
Goal: All 8 migrations applied and verified. Zero application code written.

Task	Duration	Depends On	Deliverable
0.1	Write M1–M8 SQL files	0.5d	None
0.2	Apply migrations (supabase db reset)	0.5d	0.1
0.3	Verify schema (tables, columns, FKs, indexes, RLS)	0.5d	0.2
0.4	Verify idempotency (supabase db reset × 2)	0.5d	0.2
Completion Criteria:

supabase db reset succeeds, supabase db diff shows zero diff
information_schema confirms all new objects
pg_policies confirms RLS on new tables
All 8 migrations recorded in supabase_migrations.schema_migrations
Phase 1 — Domain Layer + Core (3 days)
Goal: All domain objects, enums, ABCs, exceptions, and core types implemented and unit-tested. Zero infrastructure dependencies.

Task	Duration	Depends On	Deliverable
1.1	Implement core/ (exceptions, types, logging)	0.5d	None
1.2	Implement domain/factor.py, domain/provider.py	1d	1.1
1.3	Implement domain/calculation.py, domain/matching.py	0.5d	1.1
1.4	Implement domain/workflow.py	0.5d	1.1
1.5	Implement domain/document.py, domain/organization.py, domain/report.py, domain/audit.py	0.5d	1.1
1.6	Unit tests for all domain objects	0.5d	1.2–1.5
Completion Criteria: All domain objects compiled. All unit tests pass. mypy --strict passes on domain/ and core/.

Phase 2 — Repository Layer (4 days)
Goal: All 10 repositories implemented and integration-tested against a real Supabase test DB.

Task	Duration	Depends On	Deliverable
2.1	Implement infra/supabase.py	0.5d	Phase 0
2.2	Implement data/base.py	0.25d	2.1
2.3	Implement data/emission_factors.py, data/imports.py	1d	2.2
2.4	Implement data/emissions_logs.py, data/organizations.py	0.5d	2.2
2.5	Implement data/documents.py, data/reports.py, data/events.py, data/audit.py, data/factor_aliases.py	1d	2.2
2.6	Integration tests for all repositories	1d	2.3–2.5
Completion Criteria: All integration tests pass. Repositories correctly map between domain objects and DB rows.

Phase 3 — Infrastructure (2 days)
Goal: Event bus, search index, audit logger, config ready.

Task	Duration	Depends On	Deliverable
3.1	Implement infra/event_bus.py	0.5d	Phase 2
3.2	Implement infra/search_index.py	1d	Phase 2
3.3	Implement infra/audit_logger.py	0.25d	Phase 2
3.4	Implement infra/config.py	0.25d	Phase 2
Completion Criteria: Search index loads from real data. Event bus dispatches to handlers. Audit decorator records entries.

Phase 4 — Factor Matching Engine (5 days)
Goal: Working multi-stage pipeline. Exact match, natural key, keyword search, alias match implemented and tested.

Task	Duration	Depends On	Deliverable
4.1	Implement ExactMatchStage, NaturalKeyStage	1d	Phase 3
4.2	Implement KeywordSearchStage, AliasMatchStage	1d	Phase 3
4.3	Implement FuzzyMatchStage, SemanticMatchStage	1d	Phase 3
4.4	Implement FactorMatchingEngine + pipeline builder	1d	4.1–4.3
4.5	Integration tests for matching	1d	4.4
Completion Criteria: Matching pipeline returns correct factors for 20 test queries. Confidence scores in expected ranges. Pipeline configuration works.

Phase 5 — Import Platform (5 days)
Goal: DEFRA provider plugin + versioned import + rollback.

Task	Duration	Depends On	Deliverable
5.1	Implement providers/base.py, providers/registry.py	0.5d	Phase 2
5.2	Implement providers/defra/plugin.py	2d	5.1, Phase 4
5.3	Implement ImportMappingEngine	1.5d	5.2
5.4	Integration tests for import + rollback	1d	5.3
Completion Criteria: DEFRA 2025 workbook imported. 7029 factors in DB with batch tracking. Rollback deactivates batch. Search index refreshed.

Phase 6 — Calculation Engine (4 days)
Goals: Reproducible calculations with snapshots.

Task	Duration	Depends On	Deliverable
6.1	Implement CalculationEngine	2d	Phase 4, Phase 2
6.2	Implement snapshot + hash + verification	1d	6.1
6.3	Integration tests	1d	6.2
Completion Criteria: Calculation produces correct co2e_kg. Content hash verifiable. Snapshot persists.

Phase 7 — Document Processing + AI (5 days)
Task	Duration	Depends On	Deliverable
7.1	Implement DocumentExtractionEngine	2d	Phase 3
7.2	Implement AIDxtractionEngine + LLMClient	2d	7.1
7.3	Integration tests	1d	7.2
Phase 8 — Workflow Orchestrator (4 days)
Task	Duration	Depends On	Deliverable
8.1	Implement WorkflowOrchestrator	2d	Phase 7, Phase 3
8.2	Register event handlers	1d	8.1
8.3	Integration tests	1d	8.2
Phase 9 — Reports + Validation + Benchmarking (5 days)
Task	Duration	Depends On	Deliverable
9.1	Implement ValidationEngine	1d	Phase 6
9.2	Implement BenchmarkingEngine	1d	Phase 6
9.3	Implement ReportGenerationEngine	2d	Phase 6
9.4	Integration tests	1d	9.1–9.3
Phase 10 — API Layer + Admin Endpoints (5 days)
Task	Duration	Depends On	Deliverable
10.1	Implement api/router.py, api/dependencies.py, api/middleware.py	2d	All phases
10.2	Implement api/contracts.py	1d	All phases
10.3	Admin endpoints (imports, providers, audit, aliases)	1d	Phases 5, 8
10.4	Contract tests	1d	10.1–10.3

Phase 12 — Additional Providers (ongoing, 5 days each)
Provider	Duration	Depends On
SEAI (Ireland)	5d	Phase 5
EPA (Ireland)	5d	Phase 5
ADEME (France)	5d	Phase 5
IPCC (Global)	5d	Phase 5
7. Traceability Matrix
Mapping every section of the Architecture v2.1 specification to its implementation phase.

Architecture §	Section Title	Implementation Phase
§1	Architecture Overview	Phase 0–1 (foundations)
§2	Design Principles	All phases (guiding principles)
§3	Component & Layer Diagrams	Phase 1–3 (structure)
§4	Package Structure	Phase 1–3 (structure)
§5	Dependency Rules	Phase 1–3 (enforced from start)
§6	The Four Platforms	Phases 4–8
§7	Processing Engines — Detailed Specs	Phases 4–9
§8	Provider Plugin Architecture	Phase 5
§9	Domain Model	Phase 1
§10	Repository Architecture	Phase 2
§11	Matching Platform	Phase 4
§12	Import Platform	Phase 5
§13	Calculation Platform	Phase 6
§14	Workflow & Event Platform	Phase 3 + Phase 8
§15	Audit Framework	Phase 3
§16	Factor Search Index	Phase 3
§17	Versioning Strategy	Phase 5 (imports), Phase 6 (snapshots)
§18	Caching Strategy	Phase 3
§19	Security Model	Phase 0 (migrations), Phase 10 (middleware)
§20	Admin Platform	Phase 10 + Phase 11
§21	Coding Standards	All phases
§22	Architecture Decision Records	Reference only
§23	Future Expansion Strategy	Phase 12
§24	Risks & Trade-offs	Reference only
§25	Migration Notes	Phase 0 (pre-work)
8. Readiness Review Issue Resolution Checklist
Every issue from the Architecture Readiness Review (Final Gate), resolved.

#	Severity	Issue	Resolution	Status
R1	HIGH	Provider ↔ Engine dependency rule contradiction (§5.1 vs §8.2)	Clarified: engines may import providers/base.py (abstract ProviderPlugin interface only). Concrete providers are injected. Dependency matrix updated.	✅ Resolved in §5.1 (updated)
R2	CRITICAL	import_batch_id column missing from emission_factors	Migration M2 adds this column + FK + index. Non-destructive.	✅ Resolved by M2
R3	CRITICAL	import_batches table missing	Migration M1 creates the table.	✅ Resolved by M1
R4	CRITICAL	calculation_snapshots table missing	Migration M3 creates the table.	✅ Resolved by M3
R5	HIGH	domain_events table missing	Migration M5 creates the table.	✅ Resolved by M5
R6	HIGH	factor_aliases table missing	Migration M6 creates the table.	✅ Resolved by M6
R7	MEDIUM	workflow_states — new table vs existing columns	Resolution: use existing document_processing_queue columns. M7 adds workflow_error_count and workflow_next_retry_at.	✅ Resolved by M7
R8	MEDIUM	emissions_logs vs calculation_snapshots relationship ambiguous	M4 adds snapshot_id FK from emissions_logs to calculation_snapshots. emissions_logs = operational; calculation_snapshots = forensic.	✅ Resolved by M4
R9	MEDIUM	CacheRepository vs FactorSearchIndex ambiguity	CacheRepository removed from repository catalog. FactorSearchIndex is an infrastructure component in infra/search_index.py.	✅ Resolved
R10	LOW	EventsRepository missing from detailed catalog	Added to §3.9 with all methods.	✅ Resolved
R11	LOW	ImportsRepository transactional gap	Documented: import engine uses Supabase for deactivate + upsert + activate. If Supabase REST doesn't support atomicity across these, implement as SQL function or accept eventual consistency with rollback safeguard.	✅ Documented
R12	MEDIUM	FactorAlias domain object missing	Added to domain/matching.py.	✅ Resolved
R13	LOW	Suggestion domain object missing	Added to domain/matching.py.	✅ Resolved
R14	LOW	CalculationMethodology enum missing	Added StrEnum to domain/calculation.py.	✅ Resolved
R15	LOW	correlation_id generation not specified	Documented: correlation_id = the request_id from the originating API call. Set by EventBus on first publish.	✅ Documented
R16	MEDIUM	AliasService engine missing	Resolution: alias CRUD is simple persistence; handled by FactorAliasesRepository called from admin route. No separate engine needed.	✅ Resolved
R17	MEDIUM	Audit decorator mechanics not specified	Hard contract: engine callables accept a request dataclass as first arg after self and return a domain object. Decorator extracts request.__dict__ and result.__dict__.	✅ Added to §15.1
R18	LOW	DiscoveryResult type missing	Added to domain/provider.py.	✅ Resolved
R19	MEDIUM	RawFactorRow and NormalisedFactor types missing	Added to domain/provider.py.	✅ Resolved
R20	LOW	Human review workflow not specified	Documented: frontend displays suggestions → admin selects → POST /api/v2/admin/aliases + POST /api/v2/workflow/{id}/transition.	✅ Documented
R21	LOW	Calculation verification endpoint missing	Added: POST /api/v2/admin/calculations/{id}/verify (admin-only).	✅ Added
R22	LOW	Orphan event recovery missing	Documented: background task queries stuck workflows (>1h). Admin retry endpoint. Known limitation — eventually consistent, not strictly consistent.	✅ Documented
R23	LOW	Workflow race condition handling unspecified	Documented: use updated_at as optimistic lock. UPDATE fails → re-read current state.	✅ Documented
R24	MEDIUM	RLS policies not specified for new tables	M8 defines RLS policies for all 4 new tables.	✅ Resolved by M8
R25	LOW	Shared provider test contract missing	Added: tests/contracts/provider_plugin_contract.py — abstract test class all providers must pass.	✅ Added
All 25 readiness review issues resolved. Zero blockers remain.

