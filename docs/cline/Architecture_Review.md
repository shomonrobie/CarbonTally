The Architecture Review is complete. Since I'm in plan mode (no file modifications allowed), here is the full document:

CarbonTally — Architecture Review
Author: Lead Software Architect Date: 2026-08-06 Scope: Complete backend (60+ modules), frontend, admin dashboard Database Baseline: RC2 (supabase db reset ✅ verified, emission_factors table live)

1. Existing Architecture
1.1 Structure at a Glance

backend/
├── main.py                    FastAPI app — 31 routers, CORS, health
├── auth.py                    549 lines — JWT + 13 dep factories
├── config.py                  50 lines — static config
├── database.py                162 lines — singleton Supabase client
├── pdf_engine.py              339 lines — PyMuPDF text extraction
├── process_emissions.py       106 lines — standalone fuel-card processor
├── report_generator.py        1072 lines — FPDF report builder
├── glossary.py                172 lines — 5 endpoints
│
├── routes/                    30 route files, ~30K lines, ~280 endpoints total
│   ├── emissions.py          2474 lines — 24 endpoints
│   ├── communication.py      2326 lines — 22 endpoints
│   ├── customer_documents.py 2072 lines — 22 endpoints
│   ├── reports.py            1968 lines — 17 endpoints
│   ├── upload.py             1904 lines — 12 endpoints
│   └── ... (26 more files)
│
├── utils/                     utilities — factor lookup, email, doc classifier
├── middleware/                rate limiter
├── tests/                     test suite (8 files)
│
└── [STALE]
    ├── main copy.py           old monolith
    ├── main copy 2.py         older monolith (~3800 lines)
    └── glossary copy.py
1.2 Current Data Flow

Client → FastAPI route → Supabase table API (inline)
                           ↓
                  Supabase (PostgreSQL RC2)
There is no service layer and no repository pattern. Every route file contains raw supabase_client.from_("table").select().eq().execute() calls interleaved with business logic, validation, and response formatting.

1.3 Key Business Functions — Where They Live
Function	Current Location	Lines
Factor lookup	utils/emissions.py::get_emission_factor()	45
Factor matching (activity → DB label)	utils/emissions.py::ACTIVITY_TYPE_MAPPING	24
Emissions calculation	utils/emissions.py::calculate_emissions_with_defra()	80
Fuel / utility / scope3 processing	utils/emissions.py	~210
Report generation	report_generator.py::EnhancedSustainabilityReportGenerator	1072
Upload pipeline	routes/upload.py (12 endpoints)	1904
OCR text extraction	pdf_engine.py::PDFExtractor	339
Document classification	utils/document_classifier.py::classify_document()	145
Intensity ratios	report_generator.py::calculate_intensity_ratios()	50
Staff workload	utils/staff_workload.py	171
Email dispatch	utils/email.py	651
Audit logging	utils/audit_logger.py	148
2. Critical Problems
P1 — Factor Matching Engine references a table that no longer exists
File: backend/utils/emissions.py (lines 45–110)

get_emission_factor() queries defra_conversion_factors — a table renamed to emission_factors in RC2. Every call will fail with relation "defra_conversion_factors" does not exist.
Matches on activity_type alone, ignoring the widened RC2 natural key (reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}')).
The hardcoded ACTIVITY_TYPE_MAPPING dict maps ~15 flat labels ("Diesel (DERV)") — but RC2/DEFRA 2025 uses hierarchical labels ("Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e) [litres]"). Every lookup will miss.
No per-row unit/scope/country disambiguation.
Impact: All emissions calculations across every route silently return zero or raise.

P2 — No Service Layer — Business Logic Dispersed Across 30 Route Files
~450 blocks of inline Supabase queries duplicated across route files.
Same patterns (select...eq('organization_id',...).order(...).execute()) copied dozens of times.
No shared query logic, no consistent error handling, no caching.
Multi-step workflows (create upload batch → insert emissions_logs → update status) are implemented inline with zero atomicity.
P3 — Routes Are Far Too Large
File	Lines	Should Be
routes/emissions.py	2474	~300
routes/communication.py	2326	~400
routes/admin/staff.py	2251	~400
routes/customer_documents.py	2072	~400
routes/reports.py	1968	~300
routes/upload.py	1904	~500
Each file crams Pydantic models, validation, business logic, Supabase queries, and response formatting into a single module.

P4 — Triple Supabase Client Factory
File	Function	Singleton?
database.py	get_supabase_client()	✅ Yes
auth.py	get_supabase_client()	❌ No (creates new client per call)
config.py	Config.get_supabase_client()	❌ No
Routes import from database.py (correct), but auth.py duplicates the function.

P5 — Calculation Engine is Distributed Across Four Locations
utils/emissions.py::calculate_emissions_with_defra() — general-purpose
utils/emissions.py::process_fuel_data() — fuel-specific
report_generator.py::calculate_intensity_ratios() — intensity metrics
Inline in routes/upload.py / routes/emissions.py — per-endpoint calculations
No single orchestrator. Logic risks divergence and inconsistent rounding/methodology.

P6 — Document Pipeline Has No Orchestrator
Upload → extraction → review → emissions is six independent steps across six modules with no unified state machine, retry, or error recovery.

P7 — Two Separate Admin Dashboards
admin/ — React CRA, active.
admin-dashboard/ — Second dashboard (Minimal UI), appears to be a prototype or abandoned clone.
P8 — Stale Copy Files
backend/main copy.py, backend/main copy 2.py, backend/glossary copy.py, frontend/src/components/FileUploadHero copy.jsx, frontend/src/components/CarbonTallyDemo copy.jsx.

P9 — No Shared Types Between Backend and Frontend
Backend Pydantic models and frontend state types are defined independently — guaranteed schema drift.

P10 — Tests Reference Old Table
tests/setup_test_data.py, test_all_endpoints.py, etc. reference defra_conversion_factors and old column names.

P11 — "AI" Does Not Exist
pdf_engine.py is a PyMuPDF (fitz) text extractor — not OCR, not AI. Document classification uses keyword matching. The schema has ai_extraction_result / ai_confidence_score columns but no AI service populates them.

3. Recommended Architecture
3.1 Target Layered Architecture

┌──────────────────────────────────────────┐
│  API Layer (routes/)  — thin, 100-400 LOC│
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│  Service Layer (business/)               │
│  ┌───────────┐ ┌───────────┐ ┌─────────┐│
│  │Factor     │ │Calculation│ │Document ││
│  │Matching   │ │Engine     │ │Pipeline ││
│  └───────────┘ └───────────┘ └─────────┘│
│  ┌───────────┐ ┌───────────┐ ┌─────────┐│
│  │Report     │ │Notification│ │Audit      ││
│  │Service    │ │Service    │ │Service    ││
│  └───────────┘ └───────────┘ └─────────┘│
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│  Repository Layer (data/)                │
│  Typed Supabase access, query abstraction │
│  EmissionFactors │ EmissionsLogs │ Orgs   │
│  Documents │ Reference                    │
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│  Infrastructure                          │
│  database.py  │ config.py  │ auth.py     │
│  email.py     │ pdf_engine.py            │
└──────────────────────────────────────────┘
3.2 Proposed Package Structure

backend/
├── main.py                      [KEEP]
├── config.py                    [KEEP + fix CORS duplicate]
├── database.py                  [KEEP — single singleton]
├── auth.py                      [REFACTOR — remove duplicate client]
│
├── schemas/                     [NEW — Pydantic models extracted from routes]
│   ├── emissions.py
│   ├── documents.py
│   └── organizations.py
│
├── business/                    [NEW — service layer]
│   ├── calculation_engine.py     FactorMatchingEngine facade
│   ├── factor_matching.py        RC2-native hierarchical factor lookup
│   ├── document_pipeline.py      Upload → classify → extract → review
│   ├── report_service.py         SECR / CSRD / ISSB report builders
│   ├── organization_service.py   Org CRUD + member management
│   ├── notification_service.py   Email + in-app dispatch
│   └── audit_service.py          Typed audit trail
│
├── data/                        [NEW — repository layer]
│   ├── emission_factors.py       Typed RC2 emission_factors access
│   ├── emissions_logs.py         Typed emissions_logs access
│   ├── organizations.py          Org / member / asset queries
│   ├── documents.py              customer_documents / DPQ
│   └── reference.py              Units, categories, glossary
│
├── routes/                      [REFACTOR — thin, delegate to services]
├── utils/                       [SLIM — keep pure infrastructure]
└── tests/                       [UPDATE for RC2]
4. Refactoring Roadmap
Phase 1 — Critical Fixes (Must Be Done First)
#	Task	Files	Effort
1.1	Update factor lookup for RC2 — query emission_factors not defra_conversion_factors, use widened natural key, add hierarchical matching.	utils/emissions.py → business/factor_matching.py	5h
1.2	Remove hardcoded ACTIVITY_TYPE_MAPPING — replace with ILIKE + unit/scope disambiguation	utils/emissions.py	3h
1.3	Fix unit_fkey — RC2 drops emissions_logs_unit_fkey; code references to units(code) FK are stale	utils/emissions.py, routes/upload.py	1h
1.4	Consolidate Supabase client — remove duplicate from auth.py, import from database.py	auth.py	30m
1.5	Delete stale files — 7 files + admin-dashboard/	Root	15m
1.6	Fix CORS duplicate (www.carbontally.co.uk twice in ALLOWED_ORIGINS)	config.py	5m
Phase 2 — Repository Layer (Foundation)
#	Repository	Table(s)	Effort
2.1	EmissionFactorsRepository	emission_factors	2h
2.2	EmissionsLogsRepository	emissions_logs	2h
2.3	OrganizationsRepository	organizations, organization_members, assets, facilities, organization_metadata	2h
2.4	DocumentsRepository	customer_documents, document_processing_queue	2h
2.5	ReferenceDataRepository	units, activity_categories, glossary	1h
Phase 3 — Service Layer (Business Logic Migration)
#	Service	Moves from	Effort
3.1	FactorMatchingEngine	utils/emissions.py	4h
3.2	CalculationEngine	utils/emissions.py, report_generator.py, inline in routes	4h
3.3	DocumentPipeline	routes/upload.py, routes/admin/extraction.py	4h
3.4	ReportService	report_generator.py	3h
3.5	OrganizationService	routes/organizations/	2h
3.6	NotificationService	utils/email.py, routes/notifications.py	2h
3.7	AuditService	utils/audit_logger.py	1h
Phase 4 — Route Slimming (Delegate to Services)
After services exist, every route file shrinks to 100–400 lines:

Route File	Current	Target
routes/emissions.py	2474	~300
routes/upload.py	1904	~500
routes/reports.py	1968	~300
routes/customer_documents.py	2072	~400
routes/communication.py	2326	~400
routes/admin/staff.py	2251	~400
All others	500–1500	100–400
Phase 5 — Tests + Frontend
#	Task	Effort
5.1	Update tests for RC2 (emission_factors, new column names)	4h
5.2	Update admin/src/ table references (defra_conversion_factors → emission_factors)	2h
5.3	Update frontend/src/ table references	1h
5.4	Add unit tests for CalculationEngine + FactorMatchingEngine	4h
5. Factor Matching Engine — Specific Design
The FactorMatchingEngine must bridge the gap between user-provided activity names ("Diesel") and RC2 hierarchical labels:

Old: "Diesel (DERV)" → co2e_multiplier = 2.54 New: "Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e) [litres]" → co2e_multiplier = 2.54000


class FactorMatchingEngine:
    def __init__(self, repo: EmissionFactorsRepository): ...

    async def find(
        self,
        activity: str,              # User input: "Diesel"
        consumption_unit: str,       # "litres", "kWh", "tonnes"
        country: str,                # "GB" / "IE"
        reporting_year: int,         # 2025
        scope: Optional[str] = None, # "Scope 1"
        fuzzy: bool = True,          # Allow ILIKE fallback
    ) -> FactorMatchResult:
        """
        1. Exact natural key: (year, activity_type, country, unit, scope)
        2. ILIKE hierarchical: WHERE activity_type ILIKE '%Diesel%' AND unit = 'litres'
        3. Disambiguate multiple matches by scope
        4. Fallback to most recent year
        5. Cache result set per (reporting_year, country)
        """
Cache: the full 7029-row DEFRA set fits in ~6MB JSON; load on startup, refresh on import.

6. Calculation Engine — Specific Design

class CalculationEngine:
    def __init__(
        self,
        factor_engine: FactorMatchingEngine,
        emissions_repo: EmissionsLogsRepository,
    ): ...

    async def calculate(
        self,
        org_id: str,
        activity: str,
        quantity: Decimal,
        unit: str,
        date: date,
        scope: str,
        country: str = "GB",
    ) -> EmissionCalculation:
        """quantity × co2e_multiplier → co2e_kg → record in emissions_logs"""

    async def aggregate(
        self, org_id: str, period: DateRange
    ) -> EmissionsAggregate:
        """Scope totals, activity breakdown, trend vs prior period"""

    async def intensity_ratios(
        self, org_id: str, total_tonnes: float
    ) -> IntensityMetrics:
        """kgCO2e/m², per FTE, per revenue"""
7. Files to DELETE
File	Reason
backend/main copy.py	Old monolith
backend/main copy 2.py	Older monolith (~3800 lines)
backend/glossary copy.py	Duplicate
backend/process_emissions.py	Subsumed by CalculationEngine
frontend/src/components/FileUploadHero copy.jsx	Duplicate
frontend/src/components/CarbonTallyDemo copy.jsx	Duplicate
admin-dashboard/ (entire directory)	Superseded by admin/
8. Migration Impact Summary
RC2 Change	What Breaks
defra_conversion_factors → emission_factors	All references in utils/emissions.py, routes, admin/, frontend/, tests
defra_factor_id → emission_factor_id	emissions_logs queries in routes, report generator joins
Hierarchical activity labels	All hardcoded ACTIVITY_TYPE_MAPPING entries
Widened unique key (year, activity_type, country, unit, scope)	Duplicate detection, upserts need all 5 fields
units(code) FK dropped (RC2-H2)	Code relying on emissions_logs_unit_fkey validation
9. Summary
Priority	Action	Effort Estimate
P0	Fix factor matching engine for RC2	5h
P0	Consolidate Supabase client + delete stale files	1h
P1	Create repository layer (5 files)	9h
P1	Create service layer (7 services)	20h
P2	Extract schemas + refactor routes	34h
P3	Update tests + frontend table references	7h
P4	Shared types between backend ↔ frontend	4h
Total estimated effort: ~80 hours (~2 weeks)

End of Architecture Review