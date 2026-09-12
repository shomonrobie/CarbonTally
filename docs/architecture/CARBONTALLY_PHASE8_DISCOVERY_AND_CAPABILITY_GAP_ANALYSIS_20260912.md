# CarbonTally — Phase 8 Advanced Analytics

## Discovery, Existing-System Archaeology & Capability Gap Analysis

**Prompt ID:** `CT-P8-DISCOVERY-20260912-008`
**Date:** 2026-09-12
**Status:** DISCOVERY / ARCHAEOLOGY ONLY — **no implementation authorised by this document**
**Repository HEAD at discovery:** `03e606f8a248d3f80ab9bab77555ae8260623bbd` (branch `main`)
**Preceding governance:** Phase 7 — CLOSED — INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS

> This document inspects what **already exists** in CarbonTally and determines what can be
> reused, extended, refactored or must be genuinely built for Phase 8. It writes no code,
> creates no migration, configures no LLM, and changes no production state.

**Method:** repository archaeology only. Every claim below is grounded in a named file,
table, endpoint or migration in the current tree. Where the repository cannot support a
claim, the statement is explicitly marked **UNVERIFIED** rather than inferred.

---

## 1. Executive Summary

### 1.1 The headline finding

Phase 8's foundation is **much stronger than assumed on the analytics side, and much
weaker than assumed on the reporting-volume side**. Those two facts pull in opposite
directions and must both be stated plainly.

**Strong (reuse):**

1. **A real analytics substrate already exists.** `ReportingRepository`
   (`backend/data/reporting.py`, ~1,200 lines) computes SQL aggregates directly over live
   tables; `EmissionsLogsRepository.aggregate()` already groups by **year / month / scope /
   facility / asset**; `v3_reporting.py` exposes 15 dashboards across customer, consultant,
   processing-entity and internal-staff surfaces. P8-1 is largely an **extension** of
   existing infrastructure, not a greenfield build.
2. **A real, tested LLM provider abstraction already exists.** `backend/infra/llm_client.py`
   (an OpenAI/Anthropic-compatible chat-completions client, dependency-free, transport-
   injectable) plus `backend/infra/ai_runtime.py` (environment-configured provider/model
   selection, truthful `provider_label()` derivation including `openrouter`, durable
   provider/model attribution). **The Phase 8 requirement "do not permanently couple to one
   LLM provider" is already satisfied architecturally.** This must be reused, not rebuilt.
3. **A canonical AI-assistant architecture already exists**:
   `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` (633 lines) defines a
   tiered assistant per persona, an `AssistantGateway`, a **tool registry**, prompt-injection
   defence, audit logging, a seven-phase roadmap and eight open PO decisions.
4. **A commercial/allowance substrate already exists** for future AI quota control:
   `billing_plans` (`included_credits`, `processing_limits`, `features`),
   `billing_credit_ledger` (append-only, balance = `SUM(credit_delta)`, idempotent via
   `external_reference`), `billing_commercial_config` (versioned rules), and
   `usage_tracking`.
5. **Evidence and provenance are already first-class.** `calculation_snapshots` is an
   append-only forensic record with `factor_id`, `co2e_multiplier`, `content_hash`,
   `algorithm_version`; `domain/evidence.py` (D33.1) already classifies evidence as

**Weak (must build / must correct):**

6. **The Product Owner's belief of "~80–90 audit-ready reports" is NOT supported by the
   repository.** The V3 report engine composes exactly **one** structured report —
   `SUPPORTED_REPORT_TYPES = {"annual": …}` — a 12-section annual emissions report
   (`backend/api/v3_reports.py:63`, `backend/engines/report_generation.py:65`). The legacy
   `/api/v2` monolith advertises `SECR`, `CSRD`, `ISSB`, `AUDITOR_EXCEL` and six generic
   labels, but those are **legacy, unmounted from the V3 router, template/placeholder-backed
   and not audit-ready**. **This is a material correction and requires PO acknowledgement.**
7. **Report versioning exists; report *approval* and *customer editing* do not.** The
   `report_versions` table records generation snapshots (`is_current`, `version_number`,
   `content`) but has **no** draft/reviewed/approved state, no approver, no timestamp and no
   final-lock. There is no edit endpoint and no approval endpoint in `v3_reports.py`
   (7 routes: types, list, create, detail, content, versions, download, pdf — all read or
   generate; no approve/edit).
8. **Net-zero has no data model at all.** No targets, baselines, trajectories, initiatives or
   scenarios exist in the schema, backend or API. The only artefact is a **public marketing
   page** (`frontend/src/CarbonReductionPlan.jsx`, 65 lines, an unfilled pre-launch draft).
9. **No anomaly detection exists anywhere** (zero repository hits outside vendored code).
10. **Ask CarbonTally does not exist as a product capability.** No routes, no tables, no tool
    layer, no query audit. The existing public Assistant is a **deterministic FAQ matcher**
    with no provider configured and no customer-data access.

### 1.2 Consequence for planning

| Phase 8 area | Honest position |
|---|---|
| P8-1 Advanced Analytics | **Mostly extension** of `ReportingRepository` + `v3_reporting` (Tier 1 reuse) |
| P8-2 Ask CarbonTally | **New product capability**, on an **existing** LLM abstraction and an **existing** canonical design |
| P8-3/4 Reports + versioning/approval | Engine and version table exist; **editing, approval lifecycle and final-PDF state are new** |
| P8-5 Net-Zero Planning | **New architecture required** (no data model) — PO-gated |
| P8-6 Data Quality Intelligence | **Strong reuse** (validation, issues, evidence completeness); aggregation + anomaly detection are new |
| P8-7 Disclosure Intelligence | **Not recommended for Phase 8 core** — no framework engine exists |
| P8-8 Benchmarking & Management Insights | **Internal-only engine exists**; external peer benchmarking is unsupported |

### 1.3 Reconciliation with prior discovery

This document **does not supersede**
`docs/cline/prompt-history/CT-P7P8-ROLE-REPORT-CATALOGUE-20260912-002.md` (634 lines; the
prior role × report/analytics catalogue). It **extends** it by covering what that task
explicitly did not: the report-generation architecture, net-zero, data quality, the
LLM/provider layer, Ask CarbonTally, privacy/data-flow, and commercial/AI-usage control.
Where the prior catalogue already classified an item (Class A–G), that classification is
**adopted and cited**, not re-derived.

---

## 2. Phase 8 Scope (as inspected)

The PO's working capability map, restated as the object of this archaeology:

* **P8-1 Advanced Carbon Analytics** — scope 1/2/3, category, time-series, entity/site,
  activity, hotspots, comparisons, trends, anomalies, drill-down, historical, management insights.
* **P8-2 Ask CarbonTally** — natural-language questions over **authorised** data.
* **P8-3 Intelligent Entity-Specific Reports** — narrative from the entity's real approved data.
* **P8-4 Report Versioning & Approval** — generated / customer-edited / reviewed / approved / final PDF.
* **P8-5 Net-Zero Planning** — baseline, targets, trajectory, progress, gap-to-target, initiatives, scenarios.
* **P8-6 Carbon Data Quality Intelligence** — missing data, estimated vs primary, extraction
  quality, anomalies, evidence coverage, factor concerns. **No invented confidence score.**
* **P8-7 Disclosure / Reporting Intelligence** — framework support for target markets.
* **P8-8 Internal Benchmarking & Management Insights** — historical benchmarking, intensity
  metrics, target progress, hotspot comparison, management insight.

**Explicitly excluded from this task (per prompt):** implementing anything, installing or
connecting an LLM, schema changes, Ask CarbonTally implementation, report-generation
implementation, modifying billing/subscription, or changing messaging.

### 2.1 Critical architectural decision carried into Phase 8

The PO has decided CarbonTally has **two conceptually separate conversational experiences**:

| | A. Internal Conversations | B. Ask CarbonTally |
|---|---|---|
| Purpose | Human ↔ Human | Human → CarbonTally analytical intelligence |
| Substrate today | Supabase Realtime messaging (**exists**) | **Does not exist** |
| Examples | customer↔customer, customer↔consultant, consultant↔client, staff↔staff | emissions questions, evidence questions, calculation explanations |
| Governance | existing relationship / membership / capability / scope rules | must be a **separate product capability and data domain** |

**Archaeology conclusion (§9, §11): the two must not share tables, routes or services.**
The existing messaging domain is `conversations` / `messages` / `message_activity_log`
with human participants and `v3_messaging.py` routes. Ask CarbonTally must have its own
persistence and must never appear as a conversation participant. A chat-*like UI* is
permitted; a chat *data model* is not. **No messaging change is made or proposed by this
discovery.**

---

## 3. Existing Architecture (relevant to Phase 8)

### 3.1 Layers that already exist

| Layer | Location | Relevance to Phase 8 |
|---|---|---|
| Domain objects (pure, frozen dataclasses) | `backend/domain/` (26 modules incl. `calculation`, `evidence`, `benchmarking`, `report`, `validation`, `issue`, `messaging`, `billing`) | Reuse directly; new analytics domain objects follow this pattern |
| Engines (deterministic business logic) | `backend/engines/` — `calculation`, `validation`, `benchmarking`, `report_generation`, `pdf_render`, `factor_matching`, `matching_stages`, `extraction`, `ai_extraction`, `processing_workflow` | **The analytical core already exists** |
| Repositories (SQL over live tables) | `backend/data/` (37 modules incl. `reporting`, `emissions_logs`, `reports`, `report_versions`, `evidence`-supporting `exports`, `issues`, `audit`) | Primary reuse surface for P8-1/P8-6 |
| API surfaces | `backend/api/` — `v3_reporting`, `v3_reports`, `v3_emissions`, `v3_exports`, `v3_qc`, `v3_review`, `v3_messaging`, `v3_billing`, `v3_commercial`, `v3_operations` | Mounted unconditionally except V3 (`main.py:260-262`, conditional on `V3_API_AVAILABLE`) |
| Frontend V3 shell | `frontend/src/v3/` — customer / consultant / ops / pe / reports / admin / messaging | New Phase 8 UI belongs inside this shell, on D21 tokens |
| RLS | `supabase/migrations/20260803000000_rc2_rls.sql`, plus V3M6/entity and D-series policy migrations | **Not to be weakened**; AI tool layer must reuse it |

### 3.2 Provenance chain that Phase 8 must read (not re-derive)

```
source document (organization_files / customer_documents)
  → extraction item (manual_extraction_items / document_processing_queue payload)
  → mapping + factor selection (emission_factors, factor_aliases, customer_factors)
  → calculation (engines/calculation.py)
  → calculation_snapshots  ← append-only forensic record (content_hash, factor_id, algorithm_version)
  → emissions_logs         ← org-scoped result rows
  → evidence record        ← domain/evidence.py (COMPLETE / PARTIAL / UNAVAILABLE)
  → report_generation_queue + report_versions
  → audit_trail (append-only, Phase 7 taxonomy)
```

**Phase 8 principle carried forward:** analytics and AI read this chain. Nothing in Phase 8
is permitted to compute emissions independently of it.

---

## 4. Existing Analytics (P8-1 archaeology)

### 4.1 What already exists — verified

**Aggregation substrate** (`backend/data/emissions_logs.py`):

| Method | Grouping / output |
|---|---|
| `aggregate(org, period, group)` | groups by **scope / month / facility / asset / year** |
| `aggregate_by_activity(org, period)` | per-activity totals |
| `aggregate_by_supplier(org, period)` | per-supplier totals |
| `count_by_scope(org, year)` | scope counts |
| `find_by_org`, `list_snapshots`, `get_snapshot`, `count_snapshots` | org/period listing + calculation history |
| `find_snapshot_by_request_id`, `snapshot_count_for_factor`, `factor_usage_span` | factor provenance/usage analysis |

**SQL reporting substrate** (`backend/data/reporting.py`, class `ReportingRepository`):

| Method | Purpose |
|---|---|
| `emissions_summary(org, …)` | period totals with optional scope filter |
| `emissions_trend(org, months=12)` | zero-filled monthly trend |
| `document_summary`, `processing_summary`, `issues_summary`, `report_summary` | per-domain counts |
| `consultant_portfolio`, `consultant_client_detail` | consultant scoping over **active** grants |
| `platform_overview`, `queue_aging`, `review_reporting`, `qc_reporting`, `entity_performance` | internal + PE ops analytics |
| `member_activity` | per-member authoring counts |
| `org_audit_activity`, `entity_audit_activity`, `audit_readiness`, `audit_package` | Phase 7 audit surfaces |
| `stage_distribution`, `completed_ratio`, `audit_readiness_from_counts` | pure helpers |

**Benchmarking engine** (`backend/engines/benchmarking.py`, 692 lines + `domain/benchmarking.py`):
metrics `total`, `per_fte`, `per_area`, `per_revenue`, `activity_intensity`; groups
`year`, `facility`, `scope`, `month`, `asset`; explicit availability states
(`available`, `not_available`, `zero_denominator`, `invalid_denominator`,
`insufficient_data`, `incompatible_unit`, `incompatible_period`). **Internal/self-referential
only** — the domain doc states plainly there is *no external reference dataset and no
benchmark reference table*.

**Exposed endpoints** (verified in `v3_reporting.py`, `v3_emissions.py`):

* Customer: `/api/v3/reporting/customer-dashboard`, `/emissions-trend`, `/member-activity`,
  `/audit-readiness`, `/audit-activity`; `/api/v3/emissions/dashboard` (scope, month, asset,
  facility, supplier, activity), `/scope-breakdown`, `/calculations`, `/calculations/{id}`,
  `/{log_id}/evidence`, `/factors`.
* Consultant: `/api/v3/reporting/consultant-portfolio`, `/consultant-client/{id}`,
  `/consultant-client/{id}/audit-activity`.
* PE: `/api/v3/ops/entities/{id}/performance` (batches, items, quality, staff, SLA).
* Internal staff: `/api/v3/ops/reporting/platform|aging|review|qc|audit`,
  `/api/v3/ops/entities/{id}/audit-activity`.

**Frontend**: `DashboardPage` (Recharts bar chart + trend + member activity),
`EmissionsPage` (calculation history + evidence panel), `ReportsPage`, plus ops/PE/consultant
dashboards — all reading verified V3 surfaces, with no client-side calculation.

### 4.2 What is missing or partial

| Capability | Status | Evidence |
|---|---|---|
| Scope 1/2/3 breakdown | **Existing** | `/emissions/scope-breakdown` |
| Category / activity breakdown | **Existing** | `aggregate_by_activity` |
| Time-series (monthly) | **Existing** | `emissions_trend`, `aggregate(group="month")` |
| Entity / site (facility) analysis | **Existing** | `aggregate(group="facility")`, `aggregate(group="asset")` |
| Activity analysis | **Existing** | `aggregate_by_activity` |
| Contributor / hotspot **ranking** | **Partial** | breakdowns exist; no ranked "top N hotspot" surface |
| Comparisons (period-over-period) | **Partial** | `BenchmarkingEngine` B1 foundation; no comparison endpoint |
| Cross-entity / cross-site **comparison** | **Missing** | no comparative endpoint |
| Trends (YoY narratives) | **Partial** | engine foundation only |
| **Anomalies** | **MISSING** | zero hits repository-wide |
| Drill-down (dashboard → result → evidence) | **Partial** | evidence per result exists; consolidated drill-down journey does not |
| Historical analysis | **Partial** | depends on production population — **UNVERIFIED** |
| Management insights | **Missing** | no insight/narrative layer |
| Consolidated analytics navigation | **Missing** | analytics is spread across 6+ surfaces, no unified Analytics workspace |

### 4.3 Verdict for P8-1

**P8-1 can be built primarily by extending existing reporting infrastructure.** Recommended
approach: add *derived* analytics (ranking, comparison, drill-down, trend/insight
aggregation) on top of `ReportingRepository` and `EmissionsLogsRepository`, plus a unified
Analytics UI in the V3 shell. **Do not create a second aggregation layer, a data warehouse,
or derived summary tables** (consistent with the D30 note in `v3_reporting.py`: "no derived
summary tables, no N+1, no analytics warehouse").

---

## 5. Existing Reporting (P8-3 / P8-4 archaeology)

### 5.1 Correcting the "80–90 reports" assumption

The PO believes CarbonTally already has approximately 80–90 audit-ready carbon-footprint /
net-zero reports for UK/DEFRA use. **This is not supported by the repository.**

**V3 (authoritative, mounted) — exactly one report type:**

```python
# backend/api/v3_reports.py:63
SUPPORTED_REPORT_TYPES: dict[str, str] = {
    "annual": "Annual emissions report (structured 12-section V3 report)",
}
```

The code comment is explicit: *"The engine composes one structured 12-section report
(annual emissions) from the persisted logs; the legacy generator's other labels
(summary/documents/staff/...) have no V3 engine backing and are deliberately not offered."*
`validate_report_type()` returns **HTTP 422** for anything else, and `/api/v3/reports/types`
returns that single entry.

**The 12 sections** (`backend/engines/report_generation.py:65`):
`metadata`, `organization`, `period`, `totals`, `scopes`, `activities`, `validation`,
`benchmarking`, `provenance`, `calculation`, `lineage`, `generation`.

**Legacy (NOT mounted in the V3 router) — larger label set:**

| Legacy source | Advertised set |
|---|---|
| `backend/routes/reports.py:233` | `available_reports = ["SECR", "CSRD", "ISSB", "AUDITOR_EXCEL"]`; `available_enhanced_reports = ["SECR"]` |
| `backend/routes/reports.py:1163` | `report_types`: `summary`, `documents`, `emissions`, `staff`, `organization`, `custom` |
| `backend/routes/reports.py:1180` | 10 metrics incl. `total_emissions`, `emissions_by_asset`, `verification_rate`, `activity_trend`, `sla_compliance` |
| `backend/routes/reports.py` | schedule frequencies, template categories/CRUD, sharing, DEFRA factor import, `AUDITOR_EXCEL` |

**Assessment of the legacy set:** `backend/routes/reports.py` is a **2,097-line legacy
monolith not mounted** by `backend/api/router.py` (the prior catalogue records the same:
*"legacy monolith — not mounted by `api/router.py`"*). `backend/report_generator.py`
(1,071 lines) is an FPDF `EnhancedSustainabilityReportPDF` focused on **SECR** narrative
(YoY comparison, methodology notes, efficiency measures, intensity ratios). These labels
describe **report *kinds*** and **dashboard views**, not 80–90 distinct audit-ready report
artefacts, and they read via a legacy direct-Supabase-client path rather than the
authoritative `emissions_logs` / `calculation_snapshots` chain.

**Conclusion:** the honest count of **V3-engine-produced, audit-traceable report types is
1 (annual, 12 sections)**. The "80–90 reports" figure cannot be substantiated and should be
retired from PO expectations until a report catalogue is formally defined and ratified.

### 5.2 Report generation architecture (existing)

| Concern | Existing implementation |
|---|---|
| Engine | `ReportGenerationEngine` (`engines/report_generation.py`, 853 lines) — structured JSON sections, no HTTP/PDF/HTML coupling |
| Inputs | `CalculationEngine` (verify), `ValidationEngine` (strict blocking respected), `BenchmarkingEngine`, `ReportsRepository`, `OrganizationsRepository`, `EmissionsLogsRepository`, `EventBus`, `AuditLogger` |
| Persistence | `report_generation_queue` (`pending` → `generating` → `completed` \| `failed` + `error_log`) |
| Lifecycle | Synchronous inside the request (documented: "no worker infrastructure") |
| Versioning | `report_versions` row written on every successful generation |
| Provenance | Mandatory CO2 vs CO2e labelling; SEAI CO2-only results never relabelled as CO2e; `insufficient_data` states instead of fabricated zeros |
| PDF | `engines/pdf_render.render_branded_pdf(...)` with **server-authorized** branding (`resolve_report_branding`) — CarbonTally / consultant / co-branded; a client-supplied brand is never accepted (D21/D27) |
| Export | Reuses `/api/v3/exports/*` (CSV/JSON) — explicitly **not** a second export implementation |
| API | `GET /types`, `GET ""`, `POST ""`, `GET /{id}`, `GET /{id}/content`, `GET /{id}/versions`, `GET /{id}/download`, `GET /{id}/pdf` |

### 5.3 Gaps for P8-3 / P8-4

| Capability | Status | Detail |
|---|---|---|
| Structured report generation | **Existing** | 12-section annual report from persisted data |
| PDF generation + branding | **Existing** | server-authorized brand; white-label ready |
| Narrative generation | **Partial / template-based** | sections are structured data + fixed prose; **no LLM narrative** |
| Entity-specific narrative | **Partial** | organization/site data present; no narrative authoring layer |
| Report **versioning** | **Partial** | `report_versions` exists (`version_number`, `content`, `is_current`, `notes`, `change_summary`) — but only records generations |
| Version **state** (draft/reviewed/approved) | **MISSING** | no `status` column, no approver columns |
| **Customer editing** | **MISSING** | no edit endpoint, no section-level authoring, no draft content store |
| **Approval workflow** | **MISSING** | no approve/reject endpoint, no approval identity/timestamp |
| Final/frozen PDF | **MISSING** | PDF is rendered on demand from content; no immutable final artefact |
| Report comments | **Dormant** | `report_comments` table exists in `init_schema.sql` with **zero** backend/frontend usage |
| Report templates (V3) | **Partial** | `ReportTemplate` domain object exists; no V3 template CRUD (legacy has one) |
| Report sharing | **Legacy only** | `/{id}/share` + `/shared` live in the unmounted legacy monolith |

### 5.4 Note on `approval_requests` / `approval_decisions`

`init_schema.sql:1374/1390` defines `approval_requests` and `approval_decisions` — but both
are keyed to **`processing_assignments`** (the processing/PE workflow), **not to reports**.
They must **not** be repurposed as the report-approval model. P8-4 therefore needs either a
purpose-built report-approval model or an evaluated extension of `report_versions` —
**a design decision, not a schema change in this task.**

---

## 6. Existing Calculation / Evidence Architecture (the authoritative source)

### 6.1 Authoritative tables

| Table | Role | Key provenance columns |
|---|---|---|
| `emissions_logs` | Org-scoped emissions result rows | `organization_id`, `asset_id`, `file_id`, `customer_document_id`, `supplier_id`, `product_category_id`, `emission_factor_id`, `unit`, `scope`, `data_source`, `calculated_kg_co2e`, `verified_by`, `verified_at`, `confidence_score` |
| `calculation_snapshots` | **Append-only forensic record of every calculation** | `activity`, `activity_type`, `quantity`, `quantity_unit`, `co2e_multiplier`, `co2e_kg`, `scope`, `date`, `factor_id`, `factor_source`, `factor_set`, `import_batch_id`, `reporting_year`, `methodology`, `algorithm_version`, `content_hash` (SHA-256), `request_id` |
| `emission_factors` / `factor_aliases` / customer factors | Factor resolution + precedence | `factor_source`, `factor_set`, `import_batch_id` |
| `audit_trail` | Append-only audit (Phase 7 taxonomy, immutability trigger) | actor/stage/taxonomy in `metadata` |
| `report_generation_queue` / `report_versions` | Report lifecycle + snapshots | see §5 |

The `calculation_snapshots` table comment is explicit: *"Immutable forensic record of every
emissions calculation. Append-only; never updated or deleted."* `content_hash` is *"SHA-256
hex digest of all calculation inputs for tamper detection and reproducibility verification."*

### 6.2 Evidence layer (D33.1)

`backend/domain/evidence.py` builds an **authorized evidence record** per emission result:

* Distinguishes **ORIGINAL** source data from **CarbonTally-derived** data.
* Classifies completeness honestly from persisted fields:
  `classify_evidence_completeness(has_document, has_item, has_calculation, has_factor, has_page)`
  → **COMPLETE** (document + line + page + calculation + factor), **PARTIAL** (valid chain,
  no exact page/location), **UNAVAILABLE** (no reliable provenance).
* Excludes the database and returns stable identifiers for auditors in a separate
  technical-details block.

Endpoint: `GET /api/v3/emissions/{log_id}/evidence` (org-scoped via `ensure_org_access`).
Frontend: `EvidenceRecordPanel.jsx`, `EvidenceTrail.jsx`.

> **Important for P8-6:** this is a **completeness classification derived from real persisted
> fields**, not a fabricated confidence score. Phase 8 must extend this vocabulary rather than
> invent a new one.

### 6.3 Suitability as the authoritative source for Phase 8

**Suitable — yes.** This chain is the correct single source for both advanced analytics and
Ask CarbonTally, because it is (a) org-scoped, (b) append-only, (c) hash-verifiable,
(d) factor-provenanced, and (e) already projected into an evidence record.

**Constraint discovered:** `emissions_logs.confidence_score` (0–100) is a **legacy column**
that is *not* used by the V3 evidence model and its population is **UNVERIFIED**. Phase 8
data-quality work must **not** resurrect it as a quality metric without a PO decision
(prompt: "Do not invent a confidence score").

---

## 7. Existing Net-Zero Functionality (P8-5 archaeology)

### 7.1 Repository-wide search result

Searched the entire repository for: `net zero`, `net-zero`, `target`, `reduction`,
`pathway`, `roadmap`, `scenario`, `decarbonisation/decarbonization`, `baseline`,
`trajectory`, `carbon_reduction`.

**Result: no net-zero data model exists.**

| Searched | Finding |
|---|---|
| `supabase/migrations/*.sql` for `net_zero` / `targets` / `initiatives` / `reduction_target` | **Zero matches** (no such tables) |
| `backend/**` (app code, excluding vendored) for net-zero / target / scenario / trajectory | **Zero real matches** |
| `frontend/src/**` | Only `frontend/src/CarbonReductionPlan.jsx` and marketing/glossary content |
| `docs/**` | Marketing/strategy prose only — no schema, no engine, no API |

### 7.2 What `CarbonReductionPlan.jsx` actually is

A **65-line public marketing page** at route `/carbon-reduction-plan` (CarbonTally's own
PPN 06/21 supplier obligation), and it is explicitly an **unfilled draft**. Its own header
comment states:

> *"Rewritten as a pre-launch DRAFT: specific emissions figures, a fixed publication date and
> a signed-off declaration cannot be truthfully published until the company has verified
> baseline data."*

The page text itself defers the baseline, the targets and the trajectory to a future date.
It is **not** net-zero functionality for customers. (Note the file also exists in
`website_candidate/` and `frontend_backup_pre_v3_public_20260827/`, i.e. it is public-site
content, not V3 application code.)

### 7.3 Verdict for P8-5

| Requirement | Status |
|---|---|
| Baseline | **MISSING** (no baseline model; historical emissions *rows* exist but no declared baseline) |
| Targets | **MISSING** |
| Reduction trajectory / pathway | **MISSING** |
| Progress tracking | **MISSING** |
| Gap-to-target | **MISSING** |
| Reduction initiatives | **MISSING** |
| Scenario modelling | **MISSING** |

This aligns with the prior catalogue, which classified *"Targets / target-vs-actual"* and
*"Scenario / reduction modelling, forecasting"* as **Class F (Unsupported) / Class G
(PO-gated)** — *"No target model… needs new architecture + PO decision."*

**P8-5 is the largest genuine new-build in Phase 8**, and it is **PO-gated**: a baseline/
target/scenario model requires product decisions (methodology, target basis, intensity
denominators, approved-baseline rules, who may set targets) that the repository cannot answer.

---

## 8. Existing Data-Quality / QC Functionality (P8-6 archaeology)

### 8.1 What exists — and it is substantial

**ValidationEngine** (`backend/engines/validation.py`, **1,159 lines**) with ~35 named,
stable rule codes, including:

* Input: `VAL_INPUT_ACTIVITY_EMPTY`, `VAL_INPUT_QUANTITY_NEGATIVE`, `VAL_INPUT_YEAR_RANGE`, `VAL_INPUT_UNIT_MISSING`
* Calculation: `VAL_CALC_MISMATCH`, `VAL_CALC_ROUNDING_TOLERANCE`, `VAL_HASH_EMPTY`, `VAL_HASH_MISMATCH`
* Matching: `VAL_MATCH_FACTOR_MISSING`, `VAL_COUNTRY_MISMATCH`, `VAL_PROVIDER_MISMATCH`, `VAL_MATCH_UNIT_MISMATCH`, `VAL_MATCH_NO_RESULT`, `VAL_MATCH_LOW_CONFIDENCE`
* Scope/unit: `VAL_UNIT_MISMATCH`, `VAL_SCOPE_MISMATCH`, `VAL_SCOPE_UNKNOWN`, `VAL_SCOPE_MISSING`, `VAL_SCOPE_FAMILY_MISMATCH`
* Provenance: `VAL_SNAPSHOT_PROVENANCE_MISSING`, `VAL_SNAPSHOT_BATCH_MISMATCH`, `VAL_SNAPSHOT_SOURCE_MISMATCH`, `VAL_FACTOR_ORPHAN`, `VAL_SNAPSHOT_LINK_MISSING`
* Period/org: `VAL_YEAR_MISMATCH`, `VAL_OUT_OF_PERIOD`, `VAL_ORG_NOT_FOUND`, `VAL_ORG_INACTIVE`, `VAL_ENTITY_NOT_IN_ORG`
* Metadata: `VAL_METADATA_MISSING`, `VAL_SOURCE_MISMATCH`

**Issue domain** (`backend/domain/issue.py`, V3M-5 table `issues`):

* Types: `defect`, `exception`, `escalation`
* Severities: `low`, `medium`, `high`, `critical`
* Statuses: `open`, `in_progress`, `on_hold`, `escalated`, `resolved`, `closed`
* Full transition table + `reopened_at`; **explicitly distinct from** conversations,
  `user_feedback` and `qc_checks`/`qc_errors`
* SLA columns; `sla_breached_open` surfaced in the customer dashboard `attention` block
* API: `GET/POST/PUT /api/v3/issues…`, `GET /admin/open`, `GET /admin/entity/{id}`

**Review and QC workflow** (exists and mounted):

* `v3_review.py`: `/review-queue`, `/{id}`, `/assign`, `/complete`, `/sla/settings` (GET/PUT)
* `v3_qc.py`: `/queue`, `/stats`, `/items/{id}/review`
* `v3_verifications.py` (customer verification surface)
* Ops workspace: `QcQueue`, `QcItemPage`, `ReviewQueue`, `ReviewItemPage`, `IssuesTriageTab`, `CtQcTab`

**Extraction quality**:

* `services/automatic_extraction.completeness_score(...)`
* `document_processing_queue.ai_confidence_score`; AI extraction envelopes carry
  `confidence` + `status` (`ok` / `no_text` / `error`) with explicit error detail
* `ConfidenceBadge.jsx` in the workbench

**Evidence coverage**: `classify_evidence_completeness(...)` (§6.2).

**Rejected / corrected data**: reviewer and QC decisions persist status and actor; review/QC
reporting endpoints expose counts.

### 8.2 What is missing or partial

| Capability | Status | Note |
|---|---|---|
| Missing-data detection | **Partial** | `VAL_MATCH_FACTOR_MISSING`, `VAL_METADATA_MISSING`, unmapped-item counts exist; no org-wide "coverage by period/facility" roll-up |
| Estimated vs primary data | **MISSING** | no such flag exists on `emissions_logs`/`calculation_snapshots`; `data_source` is free text and its population is **UNVERIFIED** |
| Extraction quality (aggregate) | **Partial** | per-item confidence exists; no aggregate extraction-quality view |
| Anomalies | **MISSING** | zero implementations |
| Evidence coverage (aggregate) | **Partial** | per-result completeness exists; no period/org coverage aggregate |
| Data-quality issues roll-up | **Partial** | `issues_summary` counts exist; no data-quality-specific taxonomy view |
| Calculation/factor concerns | **Existing foundation** | `VAL_FACTOR_ORPHAN`, `snapshot_count_for_factor`, `factor_usage_span` |
| Quality **score** | **Deliberately absent** | must not be invented (prompt + prior catalogue Class G) |

### 8.3 Verdict for P8-6

**The strongest reuse story in Phase 8 after P8-1.** Phase 8 should surface and aggregate what
already exists (validations, issues, review/QC, evidence completeness, extraction confidence)
rather than build a new quality engine. The genuinely new items are: an aggregate
data-quality view, estimated-vs-primary classification (**needs a PO decision and likely a
schema addition — out of scope here**), and anomaly detection (**new architecture**).

---

## 9. Existing Messaging (boundary for Ask CarbonTally)

### 9.1 Messaging architecture (human ↔ human) — verified

| Layer | Artefact |
|---|---|
| Tables | `conversations` (init_schema.sql:673), `messages` (:709), `message_activity_log` (:1803) |
| Migrations | `20260828000000_v3m8_messaging_unique_participants.sql`, `20260902040000_phase5_pe_operational_messaging.sql` |
| Backend API | `backend/api/v3_messaging.py` — org conversations: `POST /conversations`, `GET /conversations`, `GET/POST /conversations/{id}/messages`, `POST /conversations/{id}/read`; PE-scoped: `GET/POST /entity-conversations`, `GET/POST /entity-conversations/{id}/messages`, `POST /entity-conversations/{id}/read` |
| Domain / data | `backend/domain/messaging.py`, `backend/data/messaging.py` |
| Realtime | `frontend/src/v3/messaging/useConversationRealtime.js`; Supabase Realtime |
| Frontend | `customer/MessagingPage.jsx`, `consultant/ClientMessagingTab.jsx`, `ops/OpsMessagingTab.jsx`, `ops/OpsPeMessagingTab.jsx`, `pe/PeMessagingPage.jsx`, `components/chat/*` |
| Authorization | Relationship/membership/grant-scoped via existing helpers; **RLS-enforced server-side**; messaging is **not** an unrestricted channel (AGENTS.md §28) |

### 9.2 The required separation

The PO decision (§2.1) is that **Internal Conversations (human↔human)** and
**Ask CarbonTally (human→analytical intelligence)** are conceptually separate.

**Archaeology confirms the separation is achievable but must be explicit:**

| Concern | Human messaging | Ask CarbonTally (proposed) |
|---|---|---|
| Participants | Two or more **human** users | One human + CarbonTally |
| Persistence | `conversations` / `messages` | **separate** (own table(s)) |
| Semantics | Conversation status, read receipts, last_message_at | Query, tool calls, sources, answer, refusal |
| Realtime | Supabase Realtime broadcasts | Not required (request/response) |
| Audit | `message_activity_log` | **query + tool-call audit** (§10.3) |
| Authorization | participant/relationship based | **existing org/role/RLS scope per tool call** |

**Risks if merged:** (a) a system "participant" would pollute messaging relationships and
RLS; (b) AI answers could be mistaken for human statements; (c) messaging audit and AI audit
have different retention and policy needs (N3 retention domains). **Recommendation: keep them
separate. No messaging change is proposed.**

---

## 10. LLM Requirements (P8-2 / provider abstraction archaeology)

### 10.1 The decisive finding — the requirement is already met

The prompt requires: *"CarbonTally must not be permanently coupled to one LLM provider."*

**This is already true in code, today.**

**`backend/infra/llm_client.py`** (177 lines):

* Typed `LLMClient` for any **OpenAI/Anthropic-compatible** `…/chat/completions` endpoint.
* Constructor: `base_url`, `api_key`, `model`, `timeout_seconds` (default 30s), optional
  injectable `transport` (enables tests without network).
* `complete(prompt, *, system, temperature=0.0, max_tokens=512)` → assistant text.
* Validates non-empty base_url/api_key/model and positive timeout.
* **Dependency rule:** imports only from `core` (exceptions) — "contains no business logic."
* Every failure (connection, non-2xx, malformed body) surfaces as
  `AIExtractionFailedError` (HTTP 502) — **no silent success**.
* Default transport uses only the Python standard library (`urllib`), executed off the event
  loop via `asyncio.to_thread`.

**`backend/infra/ai_runtime.py`** (127 lines):

* Configuration via exactly three environment variables:
  * `CARBONTALLY_AI_BASE_URL` — OpenAI/Anthropic-compatible `…/v1` root
  * `CARBONTALLY_AI_API_KEY` — Bearer token; *"environment only; never stored in the
    database, never logged, never exposed to the frontend"*
  * `CARBONTALLY_AI_MODEL` — model identifier
* `configured_ai_extraction_engine()` — returns an engine **only when all three are set**;
  returns `None` (deterministic fallback) on any malformed config/import error, so the durable
  worker never breaks.
* `provider_label(base_url)` — **truthful, host-derived** provider label:
  `openai.com` → `openai`, `anthropic.com` → `anthropic`, **`openrouter.ai` → `openrouter`**;
  any other host returns its own hostname (never a fabricated canonical name).
* `configured_ai_attribution()` — provider/model/model_version facts for durable provenance;
  **never reads the API key**; `model_version` is `None` unless truthfully known (never guessed).

**Tests exist**: `backend/tests/unit/infra/test_ai_runtime.py` (no network, no secrets).

### 10.2 Where the abstraction logically lives

**Recommendation: keep and extend `backend/infra/`.** Phase 8's provider abstraction is an
**extension of `llm_client.py` + `ai_runtime.py`**, not a new subsystem. The natural Phase 8
shape is:

* `infra/llm_client.py` — transport/HTTP concern (already provider-neutral).
* `infra/ai_runtime.py` — configuration/attribution concern (already env-driven).
* **New**: an assistant gateway / tool-orchestration layer above them (see §11), which is a
  *domain* concern and must **not** be placed inside the LLM client.

### 10.3 Current LLM usage — important scope fact

The only **current** LLM consumer is **AI document extraction**:

* `workers/automatic_processing.py:162-164` calls `configured_ai_extraction_engine()`.
* `services/ai_document_extraction.py` composes deterministic document text + the LLM into a
  **candidate** `extracted_data` envelope shaped exactly like the deterministic extractor.
* It is **opt-in**: with no environment configuration the pipeline is fully deterministic.
* AI output is **candidate only** — it must still pass the deterministic completeness gate,
  factor matching, item validation and the canonical `CalculationRequest` boundary.
* Prompt text is bounded (`DEFAULT_MAX_TEXT_CHARS = 20_000`), `temperature=0.0`,
  `max_tokens=1024`, and the system prompt is fixed.
* *"Failures … return an `error` / low-confidence envelope instead of raising, so the durable
  caller represents them durably (blocked / manual review) — never a false success."*

**This is a strong precedent for Ask CarbonTally:** the LLM has never been trusted as a source
of truth, only as a *candidate proposal* that deterministic systems then validate.

### 10.4 Runtime verification (performed by this task)

| Check | Result |
|---|---|
| `CARBONTALLY_AI_*` / `OPENAI_*` / `ANTHROPIC_*` / `OPENROUTER_*` env vars set | **NONE SET** |
| LLM SDK packages in `backend/requirements.txt` / root `requirements.txt` | **NONE** (`openai` / `anthropic` / `ollama` / `litellm` / `langchain` all absent) |
| CarbonTally code referencing `ollama` | **NOT REFERENCED** |
| Pre-existing local `ollama` runtime in the development environment | **PRESENT but unused by CarbonTally** — `ollama serve` running as a pre-existing developer tool with `qwen2.5-coder` models. It is not invoked by, configured for, or referenced anywhere in CarbonTally, and involves no CarbonTally credential. Recorded for transparency only. |

**Conclusion: no LLM provider is connected to CarbonTally. This task installed, configured and
connected nothing.**

---

## 11. Ask CarbonTally Architecture (discovery level)

### 11.1 What already exists — the canonical design (must be reused, not replaced)

`docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` (633 lines) is the
**canonical AI architecture** and already specifies:

* A **tiered assistant model**: public → customer → consultant → PE → staff → admin, each with
  a different knowledge and access boundary.
* **First principle — no data leakage:** *"The chatbot must never become an alternate way to
  bypass CarbonTally permissions… A frontend restriction is not a security control: every
  authenticated tool call is enforced server-side against the same RLS/API policy."*
* **Tool architecture** (§7): an `AssistantGateway` with AuthN context, AuthZ gate, **tool
  registry (approved per persona)**, safety/policy layer, audit log, provider-neutral model.
* **Tool contract** (§7.3) — six rules: verified session; scope derived from the session,
  *never from free text*; call the existing authorized API/service (single code path); return
  only role-permitted fields; **log the tool call**; be idempotent/read-only for conversational
  use (state changes need explicit confirmation and normal approval gates).
* **Prompt-injection defence** (§7.4): document content is *untrusted data*; extracted text is
  never placed in the system prompt; retrieved snippets are quoted, length-limited and
  delimited; the system prompt is immutable by user/document content.
* **Model/provider abstraction** (§8): provider-neutral behind `handleQuery(request, context)
  -> { answer, sources[], toolCalls[], status }`; supports deterministic/local engine, hosted
  APIs, and self-hosted models; *"No provider key is ever embedded in frontend code."*
* **Security & audit** (§10): control matrix, per-conversation audit events (query, sources,
  tool calls + latency, feedback, fallback/deflection, refusal/injection-block), append-only
  logs restricted to admins, and **human escalation through the normal issue workflow**
  (*"not a side channel"*).
* **Seven-phase roadmap** (§11) with per-phase UI/backend/tools/knowledge/authorization/
  security/audit/testing, and **eight open PO decisions** (§13).

**Implemented today (PHASE 1 only):** the deterministic **public** FAQ assistant —
`frontend/src/public/assistant/assistantKnowledge.js` + `AssistantWidget.jsx` +
`assistant.css`. Its own header states: *"The website candidate intentionally has NO AI
provider configured and NO API key in frontend code. This module is a deterministic, local
knowledge-retrieval layer."* It knows only the public FAQ, attributes sources, deflects
account/data questions, and says "I don't have enough information" when unsure.

### 11.2 What is missing for Ask CarbonTally

| Missing piece | Detail |
|---|---|
| **A distinct product capability** | No route, no nav entry, no product surface. Must be separate from messaging (§9). |
| **Persistence** | No query/session/answer/tool-call tables. |
| **Assistant gateway** | `AssistantGateway` is designed but **not implemented** (`handleQuery` exists only as a JS function shape in the public prototype). |
| **Tool layer** | No server-side tool registry or tool implementations. |
| **Query audit** | No AI-specific audit events (Phase 7 taxonomy has no AI taxonomy — **PO/spec decision**). |
| **Rate limiting / allowances** | Design mentions per-user/session/persona rate limiting; nothing implemented (see §17 for the commercial substrate). |
| **Authenticated knowledge base** | No authenticated RAG/index; only the public FAQ JS module. |
| **Groundedness/threshold gate** | Designed (§6.4 step 6) but not implemented. |
| **Eval set** | No maintained question/answer eval set per persona. |

### 11.3 Recommended target architecture (conceptual, from the prompt + existing design)

```text
User
 ↓
Ask CarbonTally UI  (V3 shell; chat-like surface; NOT the messaging data model)
 ↓
Intent / query understanding
 ↓
AI agent / orchestrator  (AssistantGateway)
 ↓
Controlled CarbonTally tools  (tool registry, per-persona allowlist)
 ↓
Authorization + scope + RLS  (existing guards: ensure_org_access, consultant grants,
                              require_entity_scope, internal staff permissions)
 ↓
Domain / repository layer  (ReportingRepository, EmissionsLogsRepository, evidence, reports)
 ↓
Authoritative carbon data  (emissions_logs, calculation_snapshots, evidence, audit_trail)
 ↓
Structured result
 ↓
LLM explanation  (provider-neutral, via infra/llm_client.py)
 ↓
Answer + evidence links  (+ audit record)
```

```text
LLM Provider Abstraction  (ALREADY EXISTS: infra/llm_client.py + infra/ai_runtime.py)
 ├── OpenRouter        (provider_label → "openrouter")
 ├── Direct API        (openai / anthropic, or custom host)
 ├── Local LLM         (base_url = local endpoint)
 └── VPS/self-hosted   (base_url = custom host; label = hostname)
```

**Critical property preserved:** the gateway resolves authorization **before** any data
reaches the model, and the model receives **structured tool output**, never database access.

### 11.4 Can the existing security stack support this model? (gap analysis)

| Required control | Existing mechanism | Sufficient? |
|---|---|---|
| Authentication | Supabase Auth; `get_current_user` / `AuthUser` | **Yes** |
| Organisation scope | `ensure_org_access`, `require_org_member` | **Yes** |
| Consultant engagement scope | `require_consultant`, `ensure_consultant_org_access` (active grant only) | **Yes** |
| PE scope | `require_entity_scope`, entity membership helpers | **Yes** |
| Internal staff capability | `require_internal_staff`, `require_staff`, `ensure_staff_permission`, `can_view_all` / `can_review` / `can_manage_staff` | **Yes** |
| Server-side authorization (not UI) | Every mounted V3 guard runs server-side | **Yes** |
| RLS defence-in-depth | `rc2_rls.sql` + V3M6/D-series policies; helpers `is_org_member`, `is_org_consultant`, `is_entity_member` | **Yes** |
| Audit | `audit_trail` append-only + Phase 7 taxonomy | **Partial** — no AI/assistant taxonomy yet |
| Rate limiting / allowances | none for AI | **No** — must be added (substrate exists, §17) |
| Prompt-injection controls | none in code (design only) | **No** — must be added |
| Output filtering / PII minimisation | none for AI | **No** — must be added |
| Provider secrets management | `CARBONTALLY_AI_*` env-only, never in DB/logs/frontend | **Yes** (pattern established) |

**Conclusion: the existing authentication, RBAC, capability, organisation-scope, consultant-
grant, PE-scope and RLS layers are sufficient to enforce the required model.** The gaps are
**additive** (rate limiting, AI audit taxonomy, injection defence, output filtering) and none
of them requires weakening RLS. This is a strongly favourable finding.

---

## 12. Report-Authoring Architecture (P8-3 / P8-4, "Generate → Review → Customer Edit → Approve → Final PDF")

### 12.1 Required three-way separation

| Class | Fields | Must be | Rationale |
|---|---|---|---|
| **System-controlled** | calculated values, emission factors, activity data, evidence, provenance, calculation snapshots | **read-only to the customer; never editable** | Preserves analytical integrity and auditability (§15, §17, §25 of AGENTS.md) |
| **Customer-editable** | management commentary, organisational context, initiatives, explanations, future plans, narrative content | **editable, versioned, attributed** | The customer owns their narrative, not the numbers |
| **Approval-controlled** | final report version, approval identity, approval timestamp, final PDF | **immutable once approved** | Legal/assurance traceability |

### 12.2 What CarbonTally already supports

| Requirement | Existing | Notes |
|---|---|---|
| Structured generated content | **Yes** | `report_generation_queue.generated_content` JSONB, 12 named sections |
| Persisted version snapshots | **Yes** | `report_versions(content, version_number, is_current, created_by, notes, change_summary)` |
| Server-authorized branding on render | **Yes** | `resolve_report_branding` + `render_branded_pdf` |
| Section-level comments | **Table only** | `report_comments` (report_id, user_id, section_id, comment, is_resolved, resolved_by, resolution_notes) — **dormant, no API/UI** |
| System vs customer field separation | **Partial** | sections are structured, but nothing marks which fields are editable |
| Customer editing of narrative | **No** | no write path for any section |
| Draft/reviewed/approved state | **No** | no status column |
| Approval identity + timestamp | **No** | none |
| Final PDF freeze | **No** | on-demand render only |
| Immutable-after-approval | **No** | no lock |

### 12.3 Recommended Phase 8 shape (discovery only)

```text
GENERATE (ReportGenerationEngine → system-controlled sections, persisted)
   ↓
REVIEW (internal/consultant: comment via report_comments + review queue semantics)
   ↓
CUSTOMER EDIT (narrative-only overlay: commentary / context / initiatives / future plans)
   ↓
APPROVE (customer owner/admin; identity + timestamp captured; version state → approved)
   ↓
FINAL PDF (rendered from approved version + frozen; version state → final)
```

**Design constraint:** the customer-editable overlay must be stored as a **separate layer**
from the generated system content so that a customer edit can never mutate a calculated value
or its provenance. The existing `content`/`version` structure supports this; the *policy*
requires a PO decision on (a) which fields are editable, (b) who approves (owner only vs
owner/admin), and (c) whether an edit invalidates a prior approval.

---

## 13. Disclosure / Framework Support (P8-7 archaeology)

### 13.1 What actually exists

Searched for `DEFRA`, `SECR`, `GHG Protocol`, `CDP`, `SBTi`, `CSRD`, `ESRS`, `ISSB`, `TCFD`,
`UK/EU disclosure` across migrations, backend and docs.

| Framework | In migrations | In backend code | In frontend | Verdict |
|---|---|---|---|---|
| **DEFRA** | factor data only | `routes/reference.py`, `utils/emissions.py`, factor import; `routes/reports.py` `/defra-mapping`, `/defra-factors/{year}`, `/admin/import-defra-factors` | — | **Factor data + legacy import**, not a disclosure report |
| **SECR** | — | `report_generator.py` (`report_type="SECR"`), legacy `routes/reports.py` | — | **Legacy narrative generator only** |
| **CSRD / ESRS** | — | appears as a **legacy report label string** only | — | **Label only — not implemented** |
| **ISSB** | — | legacy label string only | — | **Label only** |
| **SBTi / CDP / TCFD** | — | no implementation found | — | **Not implemented** |
| GHG Protocol | — | referenced in report prose | — | **Methodology reference only** |

The only trace in `init_schema.sql` is incidental (framework words inside seed/reference
data), and the prior catalogue likewise found no framework engine.

### 13.2 Verdict for P8-7

**Not recommended for Phase 8 core.** There is **no disclosure-framework engine, no framework
data model, no framework-specific report, and no framework validation** anywhere in the
repository. Any claim that CarbonTally "supports SECR/CSRD/ESRS/ISSB" today rests on
**legacy labels and prose**, not implementation.

Building even one framework properly requires: a framework definition model, mapping rules
from scope/category to disclosure lines, completeness/compliance validation, framework-specific
narrative, and a reviewed/applied methodology — i.e. an **entire Phase of its own**, built on
reporting outputs that do not yet have approval lifecycle (§12). **Recommend: Discovery-only →
later Phase**, starting with the single framework that a PO decision confirms is commercially
required (most plausibly **SECR**, given DEFRA factors are already present and the legacy
generator already targets it).

---

## 14. Benchmarking (P8-8 archaeology)

### 14.1 What exists

`engines/benchmarking.py` (692 lines) + `domain/benchmarking.py` (195 lines):

* Metrics: `total`, `per_fte`, `per_area`, `per_revenue`, `activity_intensity`
* Groups: `year`, `facility`, `scope`, `month`, `asset`
* Availability vocabulary (7 explicit states) — **never silently substitutes or returns zero**
* Feeds the report's `benchmarking` section and preserves availability states in the report

**Scope limitation, stated in the code:** *"Benchmarking is **internal / self-referential**
(approved Phase 9 scope): every comparison is computed from the organisation's own
`emissions_logs` and `organization_metadata`. There is **no external reference dataset and no
benchmark reference table**."*

### 14.2 Verdict for P8-8

| Capability | Status |
|---|---|
| Historical benchmarking (self vs self, prior periods) | **Existing foundation** — extend |
| Intensity metrics (FTE/area/revenue/activity) | **Existing** (denominator availability is the limitation) |
| Hotspot comparison | **Partial** — breakdowns exist; no ranked comparison surface |
| Management insights | **Missing** — no insight layer |
| Target progress | **Missing** — no target model (§7) |
| **External peer / sector benchmarking** | **Unsupported** — no reference dataset; Class F/G per prior catalogue |

**Recommendation:** P8-8's internal half is a **low-risk extension**. External peer
benchmarking requires a licensed reference dataset and an agreed methodology — **defer, and
treat as PO-gated discovery only.**

---

## 15. Supplier / Value-Chain Engagement (discovery-only area)

### 15.1 What exists

| Item | Status |
|---|---|
| Supplier master data | **Exists** — `suppliers` table + `backend/api/v3_suppliers.py` (list, create, get, update, delete) + `admin/SuppliersTab.jsx` (D17 master data) |
| Supplier **breakdown** in analytics | **Exists** — `aggregate_by_supplier()` + `/emissions/dashboard.by_supplier` |
| Supplier attribution on emissions | **Exists** — `emissions_logs.supplier_id`, `document_processing_queue.ai_mapped_supplier_id` |
| Supplier portal | **NOT IMPLEMENTED** — no supplier identity, no supplier login, no supplier workspace |
| Supplier **engagement** (requests, reminders, submissions) | **NOT IMPLEMENTED** |
| Primary supplier data collection | **NOT IMPLEMENTED** |
| Value-chain / Scope 3 supplier-specific method | **NOT IMPLEMENTED** (Scope 3 activity data may be present as spend/quantity rows, but no supplier-data collection workflow) |

### 15.2 Recommendation

**Recommended: Later Phase.** CarbonTally already has suppliers as **master data** and can
attribute emissions to them — that is enough for P8-1/P8-8 analytics. A supplier *portal*
requires a new external identity type (a fourth actor family or a scoped invitation model),
its own authorization model, its own UI surface, and an engagement workflow. That is a
**product-scale** undertaking, not an analytics feature, and it would compete directly with
Phase 8's analytics focus. **Do not include in Phase 8 core.**

---

## 16. Product Carbon Footprint / LCA (discovery-only area)

### 16.1 What exists

| Item | Status |
|---|---|
| PCF (per-product footprint) | **NOT IMPLEMENTED** — no product model, no functional unit, no product BOM |
| LCA (life-cycle assessment) | **NOT IMPLEMENTED** — no life-cycle stage model, no cradle-to-gate/grave boundaries |
| `emissions_logs.product_category_id` | **Column exists** — a nullable FK-shaped reference with **no** product table behind it and **UNVERIFIED** population |
| `product_category` in reports | no implementation |

### 16.2 Recommendation

**Recommended: Not Recommended (for CarbonTally's current architecture and strategy).**

Reasoning grounded in the actual product: CarbonTally is an **organisational** emissions
platform (GHG Protocol corporate accounting; scope 1/2/3; DEFRA/SEAI factors; document →
extraction → mapping → validation → calculation → evidence → report). PCF/LCA is a
**different discipline** — it needs product BOMs, allocation rules, life-cycle stage
boundaries, product-level functional units and (typically) different factor sets (ecoinvent-
class). Attempting it would require a parallel data model alongside the corporate one and
would put the analytical integrity of the existing chain at risk. **Recommendation: decline
for the foreseeable roadmap; revisit only on explicit commercial evidence.**

---

## 17. Subscription / Usage / AI-Cost Foundation (P8-2 enablement archaeology)

### 17.1 What exists — and it is well-suited to AI allowances

| Artefact | Relevance to AI usage control |
|---|---|
| `billing_plans` | `included_credits`, `included_storage_bytes`, `team_member_limit`, `processing_limits` (JSONB), `features` (JSONB), `api_access`, `assisted_processing_available`, `managed_processing_available`; **versioned** (`plan_code` + `version` + `effective_from/to`) |
| `billing_credit_ledger` | **Append-only**; balance derived as `SUM(credit_delta)`; `entry_type`, `credit_delta`, `source`, `external_reference` (**idempotency**), `correlation_id`; explicitly *"authoritative and immutable"* |
| `billing_commercial_config` | Versioned commercial rule keys carrying structured JSONB — documented as covering *"credit rules, structured-data bands, storage, assisted pricing, **credit policy, standard allowance**"*; current value = row with `effective_to IS NULL` |
| `usage_tracking` | Org/month usage rows (`organization_id`, `usage_month`, unique index) |
| Storage metering | `billing_storage_usage` snapshot model + `POST /api/v3/billing/me/storage/refresh` |
| Subscription | `customer_subscriptions` with server-authoritative `lifecycle_status` (D37-0 lockdown: authenticated clients cannot write it) |
| Entitlement / reads | `v3_billing.py` (`/me`, `/me/credits`, `/me/orders`, `/me/payments`), `v3_commercial.py` |
| Admin configuration | staff `can_manage_billing` commercial surfaces; `ops/CommercialTab.jsx` |

### 17.2 Assessment

**This substrate can support AI query allowances, token/cost controls, per-organisation
usage limits and provider/model configuration without inventing a second commercial system.**

A natural (future, not-now) mapping:

| AI need | Existing mechanism to reuse |
|---|---|
| Per-organisation AI query allowance | `billing_plans.included_credits` / `features` + `billing_commercial_config` rule key |
| Consumption metering | new usage rows against existing `usage_tracking`/ledger patterns |
| Idempotent charge per query | `billing_credit_ledger.external_reference` (already designed for idempotency) |
| Cost visibility to customer | `GET /api/v3/billing/me/credits` + usage surfaces |
| Admin model/provider configuration | existing staff commercial/admin config surface |

**Constraint:** exactly *how* an AI query consumes a credit (per query? per 1k tokens? per
persona?) is a **commercial PO decision**, and rate limiting must be enforced **server-side**,
never in the UI. **No billing/subscription change is made by this task.**

### 17.3 Recommendation

**Secondary (Phase 8).** If Ask CarbonTally ships, an entitlement/usage gate should be part of
its first production phase — but the *commercial policy* must be decided before implementation.

---

## 18. Privacy / Data-Flow Considerations (if an external LLM is used)

### 18.1 What could leave CarbonTally

| Data category | Would it be sent? | Existing evidence |
|---|---|---|
| **Extracted line items** (activity, quantity, unit, date, cost) | **Yes** (already, to extraction) | `ai_document_extraction` sends bounded document text; structured line data is derived |
| **Raw document text** (invoices, bills, statements) | **Yes, already** — bounded to `DEFAULT_MAX_TEXT_CHARS = 20_000` | `services/ai_document_extraction.py` |
| Supplier / asset / facility **names** | **Potentially** (present within document text) | document text is the input |
| Organisation name and metadata | **Potentially** | within document text |
| Customer financial data (invoice amounts, tariffs, spend) | **Potentially** — invoices are the primary source documents | inherent to extraction |
| Evidence documents (stored files) | **No** — the extraction path sends *derived text*, not the stored file, and no signed URL is exposed | `docs` §68; no URL in prompt |
| Personally identifiable information | **Potentially** — invoices may contain personal names/addresses | inherent to source documents |
| Carbon activity/calculation results | **No today** (result data is not currently sent) | Phase 8 design would need to decide |

### 18.2 What the existing architecture already does to minimise exposure

* **Bounded input**: `DEFAULT_MAX_TEXT_CHARS = 20_000` clips the prompt.
* **Determinism-first**: with no provider configured, nothing leaves the platform at all.
* **Opt-in by environment**: the engine exists only when all three `CARBONTALLY_AI_*` vars are
  set; otherwise the pipeline is fully local.
* **No credential leakage**: the API key is never read by the attribution helper, never stored
  in the database, never logged, never exposed to the frontend.
* **Candidate-only output**: AI output cannot become a persisted result without passing
  deterministic validation and the canonical calculation boundary.
* **No raw content in logs**: `ai_document_extraction` documents that *"No credentials or raw
  document contents are logged or persisted."*

### 18.3 Assessment and what is missing

**The existing pattern already supports minimising what is sent** — bounded text, derived
rather than stored content, opt-in provider, no key exposure. What is **missing** for an
assessment-ready answer:

| Gap | Needed decision / work |
|---|---|
| No explicit **field-level minimisation policy** (which fields must be redacted before any LLM call) | **PO + legal review** |
| No **PII detection/redaction** step | new work |
| No **DPA / sub-processor register** for an external provider | **legal review** |
| No **data residency** decision (UK/IE/EU target market) | **PO + legal review** |
| No **customer disclosure** of AI processing in terms/privacy | **legal review** |
| No **retention policy** for AI queries/answers (N3 domain) | **PO decision** |
| No **opt-out** control for customer AI processing | **PO decision** |

### 18.4 Boundary statement

**This document makes no legal or compliance claim.** Items in §18.3 are recorded as
**questions requiring later review by the PO and legal counsel**, not as resolved positions
and not as statements that CarbonTally is or is not compliant. Note also the standing project
position (Phase 7): CarbonTally does not claim to be an auditor, verifier or certification
body.

---

## 19. Phase 8 Capability Matrix

**Legend:** Existing = implemented and usable · Partial = foundation exists · Missing = not implemented.
`Reuse` = adopt as-is · `Refactor` = adapt existing · `New` = build.
**Class** adopts the prior catalogue: A Existing · B Extension · C New · D Legacy · E Proposed · F Unsupported · G PO-gated.

| Capability | Existing | Partial | Missing | Reuse Candidate | Refactor | New Build | Recommendation |
|---|:-:|:-:|:-:|---|:-:|:-:|---|
| Advanced analytics — scope/category/time-series/entity/activity breakdowns | ✅ | | | `EmissionsLogsRepository.aggregate`, `aggregate_by_activity`, `v3_emissions` | | | **Core** — extend |
| Hotspot / contributor ranking | | ✅ | | breakdowns + `BenchmarkingEngine` | ✅ | | **Core** — ranked "top N" surface |
| Period / entity comparison | | ✅ | | `BenchmarkingEngine` B1 | ✅ | | **Core** — comparison endpoint |
| Drill-down (dashboard → result → evidence) | | ✅ | | `/emissions/{log_id}/evidence`, `EvidenceTrail` | ✅ | | **Core** — consolidate journey |
| Management insights layer | | | ❌ | — | | ✅ | **Secondary** — derived insight, no invention |
| Unified Analytics workspace (UI) | | | ❌ | `v3_reporting`, `ReportingRepository`, D21 tokens | ✅ | ✅ | **Core** (navigation, not new data) |
| Anomaly detection | | | ❌ | `ValidationEngine` codes as inputs | | ✅ | **Discovery-only → PO-gated** |
| **Ask CarbonTally** (product capability) | | | ❌ | canonical AI architecture doc | | ✅ | **Core (later sub-phase)** |
| LLM provider abstraction | ✅ | | | `infra/llm_client.py`, `infra/ai_runtime.py` | | | **Reuse — already exists** |
| AI agent / tool layer (gateway, registry) | | ✅ (design) | ❌ | `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §7 | ✅ | ✅ | **Core (later sub-phase)** |
| AI query audit | | ✅ (`audit_trail`) | ❌ | Phase 7 audit taxonomy | ✅ | ✅ | **Core — with Ask CarbonTally** |
| AI usage / allowance gating | | ✅ | ❌ | `billing_plans`, `billing_credit_ledger`, `usage_tracking` | ✅ | ✅ | **Secondary — PO commercial policy first** |
| Entity-specific intelligent report narrative | | ✅ | | `ReportGenerationEngine`, org/report data | ✅ | ✅ | **Core** |
| Customer report editing | | | ❌ | `report_comments` (dormant), sectioned content | ✅ | ✅ | **Core (P8-4)** |
| Report approval (identity/timestamp/state) | | | ❌ | `report_versions`, `is_current` | ✅ | ✅ | **Core (P8-4)** |
| Report versioning (states) | | ✅ | | `report_versions`, `data/report_versions.py` | ✅ | ✅ | **Core (P8-4)** |
| PDF generation | ✅ | | | `engines/pdf_render.render_branded_pdf` | | | **Reuse** |
| Final / frozen PDF artefact | | | ❌ | PDF render + storage | ✅ | ✅ | **Core (P8-4)** |
| Evidence drill-down | ✅ | | | `domain/evidence.py`, `/emissions/{log_id}/evidence` | | | **Reuse** |
| Evidence completeness aggregate | | ✅ | | `classify_evidence_completeness` | ✅ | ✅ | **Core (P8-6)** |
| Net-zero **targets** | | | ❌ | — | | ✅ | **Discovery-only → PO-gated** |
| Net-zero **baseline** | | | ❌ | `emissions_logs` history | | ✅ | **Discovery-only → PO-gated** |
| Reduction planning / initiatives | | | ❌ | — | | ✅ | **Deferred** |
| Scenario modelling | | | ❌ | — | | ✅ | **Deferred** |
| Data-quality aggregate view | | ✅ | | validation codes, issues, review/QC, evidence completeness | ✅ | ✅ | **Core (P8-6)** |
| Estimated vs primary data classification | | | ❌ | `data_source` (free text, unverified) | | ✅ | **Discovery-only → PO + schema decision** |
| Disclosure reporting (SECR/CSRD/ESRS/ISSB/SBTi) | | | ❌ | legacy labels only (Class D) | | ✅ | **Discovery-only → later Phase** |
| Internal benchmarking (self vs self) | ✅ | | | `engines/benchmarking.py` | | | **Core** — expose |
| Intensity metrics | ✅ | | | `per_fte`/`per_area`/`per_revenue`/`activity_intensity` | | | **Reuse** |
| Target progress | | | ❌ | depends on net-zero targets | | ✅ | **Deferred (follows targets)** |
| External peer benchmarking | | | ❌ | none; no reference dataset (Class F/G) | | | **Not Recommended now** |
| Supplier engagement / portal | | | ❌ | `suppliers` master data | | ✅ | **Later Phase** |
| Primary supplier data collection | | | ❌ | — | | ✅ | **Later Phase** |
| Product carbon footprint | | | ❌ | — | | ✅ | **Not Recommended** |
| LCA | | | ❌ | — | | ✅ | **Not Recommended** |
| Climate projects / removals | | | ❌ | — | | ✅ | **Not Recommended now** |
| Internal messaging separation (human↔human) | ✅ | | | `v3_messaging`, `conversations`/`messages` | | | **Preserve unchanged** |
| Broader ESG functionality | | | ❌ | — | | | **Not Recommended** |

---

## 20. Reuse / Refactor / New-Build Recommendations

### 20.1 Adopt as-is (foundations — do not rebuild)

| Component | Why |
|---|---|
| `EmissionsLogsRepository` (`data/emissions_logs.py`) | Already aggregates scope/month/facility/asset/year/activity/supplier over live rows |
| `ReportingRepository` (`data/reporting.py`) | Already the single shared reporting layer across all four actor families |
| `BenchmarkingEngine` + `BenchmarkingSurface` | Internal intensity/period logic with honest availability states |
| `ValidationEngine` rule codes | Canonical validation vocabulary (~35 stable codes) |
| `domain/evidence.py` (D33.1) | Evidence completeness vocabulary — do not invent a competing score |
| `engines/report_generation.py` (12-section engine) | The only authoritative report engine |
| `engines/pdf_render.render_branded_pdf` + `resolve_report_branding` | White-label PDF with server-authorized brand |
| `/api/v3/exports/*` | The single export implementation (CSV/JSON, org-isolated) |
| `infra/llm_client.py` + `infra/ai_runtime.py` | **The provider abstraction — already built and tested** |
| `audit_trail` + Phase 7 taxonomy + append-only trigger | Analytics/AI audit substrate |
| Existing authorization guards (`ensure_org_access`, `require_consultant`, `ensure_consultant_org_access`, `require_entity_scope`, `ensure_staff_permission`) | The authorization contract for AI tools |
| RLS policy set | Defence-in-depth; **never weaken** |
| `billing_plans` / `billing_credit_ledger` / `billing_commercial_config` / `usage_tracking` | AI allowance substrate |
| `conversations` / `messages` / `v3_messaging` | Human messaging — preserve, do not extend for Ask CarbonTally |

### 20.2 Extend / refactor

| Component | Extension needed |
|---|---|
| `ReportingRepository` | Add derived analytics queries (ranking, comparison, data-quality roll-up, evidence coverage) — **in the same repository, not a second one** |
| `report_versions` + `data/report_versions.py` | Add version **state** (draft/edited/reviewed/approved/final), approval identity/timestamp; wire the dormant `report_comments` |
| `v3_reports.py` | Add edit + approve surfaces; add narrative overlay |
| `v3_reporting.py` | Expose comparison/ranking/insight aggregations |
| Report rendering | Add a "final/frozen" artefact path rather than always rendering on demand |
| `infra/ai_runtime.py` | Add assistant-level provider/persona selection (public vs authenticated) — same env pattern |
| `audit_trail` taxonomy | Add an AI/assistant taxonomy (needs Phase 7-consistent spec) |
| Frontend V3 shell | Add an Analytics surface + Report authoring UI + (later) Ask CarbonTally panel, all on D21 tokens |

### 20.3 Genuinely new build

| Component | Why it cannot be reused |
|---|---|
| Assistant gateway + **controlled tool layer** | Does not exist in any form (design only) |
| Ask CarbonTally **persistence** (queries, tool calls, answers, audit) | No tables; must not reuse messaging tables |
| AI **rate limiting / allowance enforcement** (server-side) | Nothing exists for AI (billing substrate exists to hang it on) |
| Prompt-injection defence + output filtering | Design only |
| **Report approval workflow** engine | No report-approval model exists (must not reuse PE `approval_requests`) |
| Net-zero **target/baseline/scenario** model | Entirely absent |
| **Anomaly detection** | Entirely absent |
| Estimated-vs-primary data classification | No field/model; needs PO + schema decision |
| Disclosure-framework definition/mapping model | Entirely absent |

### 20.4 Explicit anti-duplication rules for Phase 8

1. **One aggregation layer** — no data warehouse, no derived summary tables (preserve the D30 property).
2. **One report engine** — do not create a second report generator; extend `ReportGenerationEngine`.
3. **One export engine** — reuse `/api/v3/exports/*`.
4. **One provider abstraction** — extend `infra/`, never fork it.
5. **One evidence vocabulary** — extend COMPLETE/PARTIAL/UNAVAILABLE; do not invent a score.
6. **Two conversational domains, separate storage** — messaging and Ask CarbonTally.
7. **One authorization contract** — AI tools call the same guarded services as the UI.

---

## 21. Ask CarbonTally — Proposed Minimum Tool Concept (design only, not implemented)

Each proposed tool below must satisfy the canonical tool contract
(`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §7.3). "Deterministic" means the tool's output
is a computed value from persisted data with no model involvement.

| # | Tool | Input | Output | Authorization requirement | Deterministic | Evidence returned | Audit required |
|---|---|---|---|---|---|---|---|
| 1 | `emissions_query` | org scope (from session), date range, optional scope/facility/asset | totals + row counts + reporting period | `ensure_org_access` (customer) · active grant (consultant) | **Yes** | period + method label | **Yes** |
| 2 | `scope_breakdown` | org, date range | Scope 1/2/3 (+ Outside of Scopes) totals | as above | **Yes** | factor sources | **Yes** |
| 3 | `category_breakdown` | org, date range, dimension (activity/asset/facility/supplier) | grouped totals | as above | **Yes** | source row refs | **Yes** |
| 4 | `period_comparison` | org, two periods, dimension | deltas/percentages + availability states | as above | **Yes** | both periods' provenance | **Yes** |
| 5 | `hotspot_analysis` | org, period, N | ranked contributors | as above | **Yes** | ranked source refs | **Yes** |
| 6 | `calculation_lookup` | snapshot id or log id | calculation detail | `ensure_org_access` | **Yes** | snapshot provenance | **Yes** |
| 7 | `factor_provenance` | factor id / snapshot id | factor id, source, set, import batch, multiplier, methodology, algorithm version, `content_hash` | org member | **Yes** | full chain | **Yes** |
| 8 | `evidence_lookup` | `log_id` | evidence record + completeness (COMPLETE/PARTIAL/UNAVAILABLE) + document/line/page refs | `ensure_org_access` | **Yes** | **Yes (primary purpose)** | **Yes** |
| 9 | `report_lookup` | org, period | report rows + lifecycle + version state | org member | **Yes** | report ids/versions | **Yes** |
| 10 | `data_quality_lookup` | org, period | validation codes, open issues, evidence completeness mix, extraction confidence | org member (QC internals only per role) | **Yes** | issue/validation refs | **Yes** |
| 11 | `target_progress_lookup` | org | target/baseline/progress | org member | **Yes** if net-zero model exists | baseline refs | **Yes** |
| 12 | `audit_actor_lookup` | org, item/period | who entered/changed data (actor + timestamp) | **role-gated** (see §22 / PO) | **Yes** | audit refs | **Yes** |

**Cross-cutting tool rules (non-negotiable):**

* **Scope comes from the session, never from the prompt.** A user cannot widen scope by asking.
* Every tool is **read-only** for conversational use. Any state-changing action requires
  explicit confirmation and the normal workflow approval gate.
* Every tool reuses an **existing guarded service/repository** — no new data path, no raw SQL
  constructed from model output.
* Every tool call is **audited** (who, when, tool, arguments, result status).
* Tools never return another tenant's data, credentials, secrets, signed URLs or raw storage paths.
* PE-scoped tools must preserve the **PE document boundary** (no download path, no raw content).

**Tool 12 note:** "Who entered or changed the underlying data?" is a legitimate PO-listed
example question, but exposing actor identity is **role/policy-sensitive**. It is listed as a
tool candidate with an explicit **PO decision required** (§24) rather than an assumed capability.

---

## 22. Non-Negotiable AI Safety Requirements (design requirements, not implementation)

These are **Phase 8 architectural requirements**, recorded now so that no later implementation
shortcut can quietly violate them.

### 22.1 The AI must NOT

* **invent emissions numbers** — every figure must come from a tool call over persisted data;
* **invent emission factors** — factors come only from `emission_factors` / customer factors;
* **invent evidence** — evidence comes only from `domain/evidence.py` over real provenance;
* **invent source documents** — no document reference may be synthesised;
* **bypass authorization** — no tool may run outside the caller's session scope;
* **retrieve another tenant's data** — cross-org access is a critical security failure;
* **alter carbon calculations** — the model never writes calculation state;
* **modify audit records** — audit is append-only and model-unreachable;
* **silently change historical results** — no write path to `emissions_logs` / `calculation_snapshots`;
* **claim assurance / certification** — must not present CarbonTally as an auditor, verifier,
  certification body, or as providing legal/professional assurance (consistent with the
  Phase 7 positioning and the canonical doc's §4.2 prohibition list);
* **present unsupported conclusions as facts** — interpretation must be marked as interpretation.

### 22.2 The AI should

* **state when data is unavailable** — and distinguish "no data" from "zero emissions";
* **distinguish calculated fact from interpretation**;
* **cite/identify the underlying evidence** (document, line, page, factor, snapshot);
* **identify uncertainty** — e.g. partial evidence completeness, ambiguous mapping;
* **request clarification** when the question is ambiguous (period, scope, entity);
* **respect user scope** — answer only within the caller's authorised boundary;
* **preserve auditability** — every query and tool call is reconstructable;
* **refuse safely** — on injection attempts, boundary probing, or out-of-scope requests.

### 22.3 Structural preconditions (must hold before any AI feature ships)

1. The provider abstraction is used (`infra/llm_client.py`) — no ad-hoc HTTP calls.
2. The gateway authorises **before** data is assembled.
3. Tools return structured, bounded data — never raw database rows, never files, never URLs.
4. Answers are grounded — ungrounded output converts to the conservative fallback message.
5. The audit trail records the query, the tools called, the sources used and the outcome.
6. A server-side rate limit / allowance check exists.
7. Prompt-injection defences exist for any untrusted text (document-derived text is untrusted).
8. Output filtering prevents credential/secret/internal-path disclosure.
9. An eval set exists per persona and runs in CI.
10. **The LLM is never the authorization boundary.**

---

## 23. Phase 8 Priority Recommendation

> Section mapping note: prompt §22 (report authoring) is covered at §12; prompt §21 (AI safety)
> at §22; prompt §23 (priorities) here; prompt §24 (competitor non-authority) at §26.5.

### 23.1 P8 Core — should definitely be implemented

| # | Capability | Why core | Primary reuse |
|---|---|---|---|
| C1 | **Unified customer Analytics surface** — scope/category/time-series/entity/activity breakdowns, period comparison, hotspot ranking, drill-down to evidence | Already-existing data; highest customer value; pure extension | `ReportingRepository`, `EmissionsLogsRepository`, `v3_emissions`, `v3_reporting` |
| C2 | **Data-quality & evidence-coverage intelligence** | Strongest reuse; gates trust in every number | `ValidationEngine`, `issues`, review/QC, `domain/evidence.py` |
| C3 | **Internal benchmarking exposure** (self-referential intensity + period comparison) | Engine already exists; low risk | `BenchmarkingEngine` |
| C4 | **Report versioning & approval lifecycle** (draft → edited → reviewed → approved → final PDF) | Required before any "intelligent report" claim; closes a real integrity gap | `report_versions`, `report_generation_queue`, `report_comments`, `pdf_render` |
| C5 | **Entity-specific report narrative on existing structured content** | The 12-section engine already produces the substrate | `ReportGenerationEngine` (deterministic first; narrative later) |
| C6 | **Ask CarbonTally foundation** — gateway, tool registry, read-only tools over existing guarded services, audit, conservative fallback (deterministic/local first, provider plugged in behind `infra/`) | Ordering the foundations first avoids building AI on an unsecured base | canonical AI architecture doc + `infra/llm_client.py` |

### 23.2 P8 Secondary — implement if architecture keeps it low-risk

| # | Capability | Condition |
|---|---|---|
| S1 | AI usage/allowance gating | PO commercial policy decided first |
| S2 | Management-insight summarisation (deterministic, no invention) | Only where it explains real figures |
| S3 | Consultant portfolio analytics roll-up (emissions + quality across **active** clients) | Must never surface ended relationships |
| S4 | Ops/PE throughput + cycle-time analytics | Extends `queue_aging`, `review_reporting`, `entity_performance` |
| S5 | Export/report depth for analytics (e.g. analytics CSV via existing export surface) | Reuse `/api/v3/exports/*` |

### 23.3 P8 Discovery-only — requires more research/design

| # | Capability | Why |
|---|---|---|
| D1 | **Net-zero planning** (baseline, targets, trajectories, gap-to-target) | No data model; methodology is a PO/product decision |
| D2 | **Anomaly detection** | No design, no methodology, high false-positive risk in carbon data |
| D3 | **Estimated vs primary data classification** | Needs a schema + policy decision (and must not resurrect legacy `confidence_score`) |
| D4 | **Disclosure frameworks** | Needs a framework model; start with one PO-confirmed framework |
| D5 | **AI actor-identity answers** ("who changed this?") | Personnel-visibility policy gate |
| D6 | Authenticated enterprise RAG (retrieval over the customer's own documents) | Security, cost and injection design all unresolved |

### 23.4 Future phase / deferred

| # | Capability | Rationale |
|---|---|---|
| F1 | Scenario modelling / reduction pathway modelling | Depends on D1; heavy methodology |
| F2 | Target-progress analytics | Follows D1 |
| F3 | Supplier engagement portal + primary supplier data collection | New external actor family; product-scale |
| F4 | External peer / sector benchmarking | Requires licensed reference dataset + agreed methodology |
| F5 | Climate projects / removals | New domain, no model |
| F6 | Individual staff/PE performance scoring | Personnel governance (Class G); keep workload framing only |
| F7 | Cross-tenant aggregates | PO-gated + anonymisation policy required |

### 23.5 Not recommended

| # | Capability | Rationale |
|---|---|---|
| N1 | Product carbon footprint (PCF) | Different discipline; needs product/BOM/allocation model |
| N2 | LCA | As above; life-cycle boundary model required |
| N3 | Cost-to-serve / margin analytics | No cost ledger; would be fabricated (Class F) |
| N4 | Capacity/demand forecasting | No capacity or demand model (Class F) |
| N5 | Geography/industry sector aggregates | Taxonomy not verified populated (Class F) |
| N6 | Broader ESG functionality | Outside CarbonTally's emissions-processing identity as currently built |

---

## 24. Open Decisions Requiring PO Confirmation

These are **PO DECISION REQUIRED** items. No implementation should pre-empt them.

### 24.1 Reporting correction (immediate)

| # | Decision |
|---|---|
| P1 | **Acknowledge the "80–90 reports" correction** (§5.1): the V3 engine produces **one** 12-section annual report type. Does the PO accept this as the current baseline, and should a formal **report catalogue** be defined and ratified before any expansion? |
| P2 | Confirm whether the **legacy report surface** (`backend/routes/reports.py`, `report_generator.py`, the SECR/CSRD/ISSB/AUDITOR_EXCEL labels) should be (a) treated as a behavioural ancestor only, (b) progressively retired, or (c) explicitly revived into V3. **No decision is implied here.** |

### 24.2 Report authoring (P8-3/P8-4)

| # | Decision |
|---|---|
| P3 | Which report sections/fields are **customer-editable** vs **system-controlled**? |
| P4 | Who may **approve** a report — customer Owner only, or Owner **and** Admin? (Note the ratified factor precedent: Owner **may** self-approve a customer factor.) |
| P5 | Does a post-approval edit **invalidate** the approval and require re-approval? |
| P6 | Is a **frozen final PDF** a required immutable artefact (with its own hash/version)? |
| P7 | Is the **report approval workflow** the same as, or distinct from, the existing processing/PE `approval_requests` model? (Recommendation: **distinct** — see §5.4.) |
| P8 | Is report narrative generation **AI-assisted** (needs §22 preconditions) or **deterministic template** first? |

### 24.3 Ask CarbonTally / AI

| # | Decision |
|---|---|
| P9 | **Product naming and entry points** — is "Ask CarbonTally" a nav surface in every workspace, or a per-persona capability? Does it reuse the "CarbonTally Assistant" name (canonical doc §13 decision 4)? |
| P10 | **Provider strategy** — hosted vs self-hosted, model tiering per persona, and cost-per-turn budget (canonical doc §13 decision 1). |
| P11 | **AI usage commercial policy** — per query, per token, per persona? Which plans include AI? (Reuses `billing_*`; §17.) |
| P12 | **May the assistant answer "who entered or changed this data?"** — i.e. is member/actor identity AI-visible to customers, viewers included, or Owner/Admin only? (Tool 12, §21.) |
| P13 | **AI audit & retention** — what is logged (query text? answers? tool payloads?) and for how long (N3 retention domain)? (canonical doc §13 decision 5.) |
| P14 | **Customer disclosure / opt-out** for AI processing; DPA and data-residency expectations for UK/IE/EU. (§18 — PO + legal.) |
| P15 | Does the public Assistant need to move from the deterministic FAQ prototype to a provider-backed assistant in Phase 8, or stay deterministic until later? |

### 24.4 Analytics scope & governance

| # | Decision |
|---|---|
| P16 | Exact **analytics scope per persona**, and which analytics are customer-facing vs internal-only (prior catalogue §19 Q9/Q19). |
| P17 | Is an **analytics entitlement gate** required (plan-based), and which analytics are gated? |
| P18 | Are **cross-tenant / peer / consultant-benchmarking** analytics permitted at all, and under what anonymisation policy? (Prior catalogue §19 Q11/Q13/Q14/Q15 — currently **unsupported**; no reference dataset.) |
| P19 | Is a new **analytics licence/permission model** required beyond `can_view_all`/`can_review` (prior catalogue §19 Q20)? |
| P20 | Are **individual staff / PE performance** analytics permitted (governance-sensitive; currently workload-framing only)? |

### 24.5 Net-zero & data quality

| # | Decision |
|---|---|
| P21 | **Net-zero scope** — is baseline/target/trajectory/gap-to-target in Phase 8 at all? Whose methodology (GHG Protocol Corporate + SBTi-aligned? near-term vs long-term?), what target basis (absolute vs intensity), and who may declare a baseline? |
| P22 | Are **scenario modelling** and reduction-pathway modelling in scope now or deferred? |
| P23 | **Estimated vs primary data classification** — is this a required concept, and does it justify a schema addition? |
| P24 | **Anomaly detection** — is it a product requirement, and what false-positive tolerance is acceptable? |
| P25 | Is a **data-quality score** ever permitted? (Prompt says do not invent one; the existing evidence-completeness vocabulary is the honest alternative.) |
| P26 | Is **evidence-completeness aggregation** customer-facing or internal-only? |

### 24.6 Disclosure

| # | Decision |
|---|---|
| P27 | Which disclosure framework(s), if any, are commercially required for the target market — and is SECR the first? |
| P28 | Does CarbonTally **produce** disclosure output or **support** the customer's own disclosure? (Consistent with the Phase 7 "support, not assure" positioning.) |

### 24.7 Discovery-only areas

| # | Decision |
|---|---|
| P29 | Supplier engagement / supplier portal — Phase 8, later, or not at all? |
| P30 | PCF/LCA — confirm decline, or is there commercial evidence to pursue? |
| P31 | Climate projects / removals — in scope at any point? |

---

## 25. Explicitly Deferred Capabilities

Deferred **by this discovery** — no work should be scheduled against these without a new PO decision:

1. **Scenario / pathway modelling** — depends on the net-zero model (P21/P22) which does not exist.
2. **Target-progress analytics** — depends on targets.
3. **Anomaly detection** — no methodology; high false-positive risk.
4. **Disclosure framework engine** — a full phase of its own.
5. **External peer / sector benchmarking** — no reference dataset.
6. **Supplier portal / primary supplier data collection** — new external actor family.
7. **PCF / LCA** — different discipline; not recommended.
8. **Climate projects / removals** — no model.
9. **Individual staff/PE performance scoring** — governance-sensitive.
10. **Cross-tenant aggregates** — PO-gated + anonymisation policy.
11. **Authenticated enterprise RAG over customer documents** — security/cost/injection design unresolved.
12. **Broader ESG functionality** — outside current product identity.
13. **Legacy report surface revival** — `AUDITOR_EXCEL` and the legacy `/api/v2` report monolith; treat as behavioural ancestor (Class D) pending P2.

---

## 26. Risks and Dependencies

### 26.1 Risks

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **Expectation misalignment on reports** — planning assumes 80–90 audit-ready reports that do not exist | High — scope and sales claims | Correct the record now (§5.1); define a ratified report catalogue before expansion (P1) |
| R2 | **AI treated as an authorization path** | Critical — tenant data leak | Enforce the canonical model: authorize → tool → data → model. Never `User → LLM → database` |
| R3 | **AI fabricating figures/factors/evidence** | Critical — destroys credibility | §22 rules; grounded answers only; deterministic tools; fallback on ungrounded output |
| R4 | **Prompt injection via document text** | High | Document content is untrusted data; never in the system prompt; delimited and length-bounded |
| R5 | **Duplicate analytics/reporting engines** | High — divergence, double maintenance | §20.4 anti-duplication rules |
| R6 | **Customer edit mutating system-controlled values** | High — integrity breach | Separate narrative overlay layer from generated content (§12) |
| R7 | **Net-zero scope creep** without a model | Medium-High | Keep as discovery-only until P21/P22 |
| R8 | **Production data depth UNVERIFIED** — analytics may promise history that is not populated | Medium-High | Verify applied migrations + population before promising depth (carried from prior catalogue R7) |
| R9 | **AI cost exposure** without allowance control | Medium | Decide commercial policy (P11) before shipping; enforce server-side limits |
| R10 | **Privacy/legal** — document text may contain PII/financial data | Medium-High | §18 — PO + legal review before provider enablement |
| R11 | **Messaging/AI model conflation** | Medium | Keep the two domains separate (§9) |
| R12 | **PE boundary erosion** via new analytics/AI surfaces | High | PE tools stay assignment-scoped, own-entity only; no document downloads |
| R13 | **Resurrecting legacy `confidence_score`** as a quality metric | Medium | Prohibited without a PO decision (§6.3, P25) |
| R14 | **Conditional V3 mounting** — if `V3_API_AVAILABLE` is false at boot, V3 routes (including reports/reporting) vanish | Medium | Pre-existing hazard documented in the operations record; verify at deploy time |

### 26.2 Dependencies

| Dependency | Needed for | Status |
|---|---|---|
| Production data population verification | Any claim of historical analytics depth | **UNVERIFIED** |
| PO decisions §24 | Almost all Phase 8 core work | **OUTSTANDING** |
| Report-approval data model decision (P7) | P8-4 | **OUTSTANDING** |
| Net-zero methodology decision (P21) | P8-5 | **OUTSTANDING** |
| Commercial AI policy (P11) | AI usage gating | **OUTSTANDING** |
| Legal/privacy review (P14) | Enabling an external provider | **OUTSTANDING** |
| AI audit taxonomy spec | AI query audit | **OUTSTANDING** |

### 26.3 Sequencing recommendation

**Reporting/analytics integrity before AI.** Ask CarbonTally is only as trustworthy as the
report/approval and evidence layers underneath it. Building the assistant first would place an
explanatory layer over workflows that cannot yet be approved or frozen.

### 26.4 What this discovery did NOT verify

* Production database population, applied-migration state and historical depth → **UNVERIFIED**.
* Whether `emissions_logs.confidence_score` / `data_source` are populated → **UNVERIFIED**.
* Live runtime behaviour of any endpoint (no production access attempted).
* Any Render/Vercel/Supabase production configuration (documented separately, UNVERIFIED).

### 26.5 Competitors are not the specification

Consistent with the prompt's principle, **no competitor product was used to derive scope.**
Competitor functionality is context only. The authority for Phase 8 is: (1) CarbonTally's
verified architecture, (2) its product strategy, (3) carbon-accounting integrity, (4) the
security/authorization architecture, (5) evidence/provenance requirements, (6) the UK/IE/EU
target market, and (7) ratified PO decisions.

---

## 27. Recommended Next Task

> **ONE task only. It is not begun by this document.**

### Recommended next task

**`CT-P8-REPORTING-LIFECYCLE-SPEC-20260912-009` — Phase 8 Report Versioning & Approval
Lifecycle specification (design-only, PO-decision-driven).**

**Why this one first:**

1. It addresses the **most material correction** in this archaeology (P1): CarbonTally has one
   real report type and **no approval lifecycle**, yet "audit-ready" reporting is the
   foundation of the entire Phase 8 promise.
2. It is the **lowest-risk, highest-reuse** Phase 8 core item: `report_generation_queue`,
   `report_versions`, `data/report_versions.py`, `report_comments` (dormant) and
   `render_branded_pdf` all already exist — no new report engine is implied.
3. It **unblocks P8-3** (entity-specific narrative), because narrative cannot be safely
   generated before it is clear which fields are system-controlled and which are editable.
4. It **de-risks Ask CarbonTally**: the assistant should only ever explain approved,
   provenance-preserved reporting output.
5. It is **specification-only**, so it can proceed without enabling any LLM, provider,
   migration or production change.

**Expected output:** a ratified specification covering the version state machine
(draft → edited → reviewed → approved → final), the system-controlled vs customer-editable
field split, approval identity/timestamp capture, frozen-final-PDF rules, `report_comments`
review usage, and the PO answers to P1–P8. **No implementation until that specification is
ratified.**

---

## Closing Statement

CarbonTally's Phase 8 foundation is **substantially better than a greenfield assumption on
analytics, provenance, evidence and LLM abstraction**, and **substantially weaker than
assumed on report volume, report approval and net-zero**. The correct Phase 8 strategy follows
directly from that evidence: **extend what exists, correct the record, decide the policy, and
never let the model become an authorization path or a source of truth.**

```text
PHASE 8 DISCOVERY COMPLETE
EXISTING ARCHAEOLOGY:  analytics substrate, reporting engine, evidence, validation,
                       benchmarking, messaging, billing/allowance, LLM abstraction — all found
KEY CORRECTION:        1 V3 report type (12 sections), not ~80–90 reports
STRONGEST REUSE:       ReportingRepository + EmissionsLogsRepository + infra/llm_client.py
LARGEST NEW BUILD:     Net-zero (no data model) + Ask CarbonTally gateway/tools + report approval
LLM INSTALLED:         NO        LLM PROVIDER CONNECTED: NO        API KEY ADDED: NO
CODE CHANGES:          NONE      DATABASE CHANGES: NONE            MIGRATIONS: NONE
PRODUCTION CHANGES:    NONE
IMPLEMENTATION AUTHORISED: NO
```

*End of discovery document.*
