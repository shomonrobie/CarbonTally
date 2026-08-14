# CarbonTally — V3 Impact Assessment v1.0

Status: **V3 IMPACT ASSESSMENT COMPLETE — READY FOR ARCHITECTURE DECISIONS**

Date: 2026-08-09 · Branch: `main` (V2.1 Phase 9/10 work uncommitted)
Mode: **READ-ONLY analysis.** No code, database, migration, RLS, Storage policy,
API contract, test or data was modified. The development database baseline is
unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).
Baseline: `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md`
(`V2.1 TRACEABILITY COMPLETE — READY FOR V3 IMPACT ASSESSMENT`).

---

## 1. Executive Summary

V3, as documented in the repository, is **not a rewrite of V2.1** — it is an
operational and multi-entity extension of a V2.1 engine stack that is already
substantially complete. The central V3 architecture (the *canonical processing
pipeline* in the V3 prompt) already exists as engines and repositories; the
genuinely new V3 surface is the **external Human Data Processing Entity (HDPE)
model**, **customer-supplied/selected factors**, and the **operational control
plane** (assignment, reassignment, QC, SLA, issues, entity lifecycle).

Key conclusions:

1. **V2.1 reuse is high.** The domain layer (11 modules), repositories (9),
   engines (8 — matching, calculation, extraction, AI extraction, workflow,
   validation, benchmarking, report generation), infrastructure (event bus,
   audit logger, search index, service pool) and the 19-route v2.1 API can be
   carried into V3 largely unchanged. The v2.1 engines already implement the
   "single CarbonTally Processing Engine" requirement (validation →
   normalisation/match → calculation → CO₂e outputs).

2. **The V3 entity model is the principal new requirement.** No
   `data_processing_entities` structure exists anywhere in the schema — Babui is
   currently only a `company_name` string in `auth.users.raw_user_meta_data`.
   Entity identity, entity-scoped staff/roles, entity-scoped assignment/queue
   tables, entity RLS and entity lifecycle are all absent. Whether this is a new
   table or an `organizations`-as-tenant extension is a human architecture
   decision (see §27).

3. **Customer-supplied/selected factors are not implemented.** V2.1 matching and
   calculation resolve factors exclusively from the global `emission_factors`
   reference (`CalculationRequest` requires a matched `EmissionFactor`; there is
   no custom-factor path). The schema has no org-owned factor table. The only
   customer-scoped factor surface today is org-scoped `factor_aliases`
   (synonyms, not factor values).

4. **Multi-provider factor expansion is bounded by two real constraints.**
   `emission_factors.country` is constrained by `CHECK (country IN ('GB','IE'))`
   (K1, active in RC2), and the natural-key unique index is
   `(reporting_year, activity_type, country, unit, scope)` — it does **not**
   include `provider_key`/`factor_set`. EPA (IE) fits today; ADEME (FR), IPCC
   (global) and EU residual-mix factors would **violate the country CHECK**, and
   two providers in the same country/year/activity (e.g. SEAI + EPA IE) would
   collide on the natural key.

5. **The V3 migration decision is CONDITIONAL.** Most documented V3 requirements
   (unified pipeline, lineage, five-layer review, QC, SLA/KPI, issues via
   existing conversations/escalation, versioning via existing tables, retention)
   can be implemented on the existing schema with code-level work. A database
   migration becomes **required** only if (a) the HDPE entity model, (b)
   customer-supplied factor values, or (c) non-GB/IE factor providers enter the
   V3 scope — each of which is a human decision documented in §8/§27.

6. **Inherited V2.1 deviations matter for V3.** D1 (no `backend/providers/`
   plugin architecture), D2 (no `ImportMappingEngine`), D13 (legacy surface not
   renamed) and D14 (integration test gap) all shape V3; none blocks V3 at the
   code level, but D1/D2 determine how provider and import work is built.

7. **The legacy application is the largest untapped V3 asset.** 47 legacy route
   modules and ~20 operational tables (staff, workload, assignments, reviews,
   review history, QC, SLA, queues, conversations) already implement much of the
   V3 operational control plane for CarbonTally-internal staff. V3 must decide
   whether to extend this legacy surface or rebuild it v2.1-native (see §17, §22).

No V3 implementation, schema change, or migration was created or recommended for
immediate execution. This document is the decision input only.

---

## 2. Assessment Scope

This assessment covers, against the completed V2.1 baseline:

- V3 architecture/source material identification (§3);
- full V3 requirements inventory separated into **documented** vs **inferred**
  (§5);
- component-level REUSE/EXTEND/MODIFY/REPLACE/NEW/DEFER/RETIRE analysis for
  architecture, engines, data, API, security, processing (§6);
- database impact per requirement (A–F) and the V3 migration decision (§7–§8);
- dedicated factor-architecture, matching, calculation, validation,
  benchmarking, reporting, API, security, processing, human-in-the-loop,
  integration, provider, testing and deviation analyses (§9–§23);
- V3 scope boundary, implementation order, risks and human decisions (§24–§27);
- final impact summary and migration verdict (§28–§29).

Explicitly **out of scope** (documented): audited assurance/certification,
formal ESG reporting architecture, audit-opinion functionality (V3 prompt §3),
and the V3 prompt's own 56-section output format (the task deliverable structure
in this prompt governs). No frontend or database changes are analysed for
implementation — only impact.

---

## 3. Sources and Authority

### 3.1 V3 source material located

| # | Source | Type | Authority for |
|---|---|---|---|
| VS1 | `docs/cline/prompts/CarbonTally V3 — Final Architecture & Impact Assessment Prompt.md` (46 KB) | V3 task prompt containing the **canonical V3 architecture** and 37 audit areas | Primary V3 source — TARGET V3 architecture diagram (§6A) and operational requirements (§6B–§28) |
| VS2 | `docs/cline/CarbonTally_Platform_Processing_Architecture_Master_v1.md` (53 KB, 2026-08-08) | Architecture-discussion baseline for the business/entity model | HDPE model: entity lifecycle, two management levels, batch=grouping / work-item=atomic, assignment history, QC, approval separation, provider isolation/offboarding, audit, break-glass |
| VS3 | `docs/cline/CarbonTally_Backend_Module_Inventory_V3.md` (457 KB) | Module inventory — **analysis aid only**; heuristic, may contain false positives | Cross-checking module/table existence (verified against code in this assessment) |
| VS4 | `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md` | V2.1 baseline (authoritative) | All V2.1 status claims; deviations D1–D14; deferred/future items |
| VS5 | `docs/cline/# CarbonTally Backend v2.1 — Implementation Preparation Pack.md` | FROZEN V2.1 implementation spec | Phase 12 providers, Phase 11 admin remainder, future items, R21/R22 |
| VS6 | `docs/cline/CarbonTally_Backend_V2_Final_Implementation_Instructions.md` | CT-ARCH-001…016 | Provider expansion (007/015), admin platform (009/010), API philosophy (012) |
| VS7 | `docs/cline/CarbonTally-Phase10-API-Admin-v1.0.md` + Phase 9A–9D + SEAI series | Phase completion reports | Verified implementation/limits evidence |
| VS8 | `docs/CarbonTally Complete Customer Feature List.md` | Customer feature list | Mentions "Custom factors" as a feature (context for V3-002) |
| VS9 | `docs/business/…Viability Report…` | Commercial context | "custom emission factor mapping" under enterprise pricing (context, not a requirement) |
| VS10 | `database/rc1/*`, `database/rc2/*` | Older frozen SQL snapshots (superseded by `supabase/migrations/`) | Historical schema evidence; **not authoritative** for current state |

### 3.2 No formal V3 specification exists

There is **no standalone "CarbonTally V3 Architecture Specification"**. The V3
material consists of (a) the V3 audit/task prompt (VS1) — which *describes* the
target architecture and *asks* for an audit rather than prescribing a fixed
feature list — and (b) the Platform Processing Architecture Master (VS2), which
is explicitly an architecture-discussion baseline. The `CarbonTally V3 — Final
Architecture & Impact Assessment Prompt.md` is the closest thing to a V3
requirement statement and is treated here as the **primary documented source**.
Where the prompt says "eventually support" or "potential", those items are
classified as **documented aspiration**, not committed V3 scope, and flagged for
human scoping (§5, §24, §27).

### 3.3 Source discipline

- Every V3 requirement in §5 is tagged with its source class
  (V3 specification / V2.1 future item / V2.1 traceability deviation / phase
  roadmap / repository evidence / explicitly deferred / inference).
- No inference is silently promoted to a requirement. Inferred items are listed
  separately in §5.2 and §24.
- Where sources conflict (e.g. the V3 prompt's "Human Data Processing Entities
  do NOT become emission-factor providers" vs the V2.1 Phase 12 emission-factor
  provider roadmap) the conflict is recorded, not reconciled (§5.3).

---

## 4. V2.1 Baseline

Condensed from `CarbonTally-v2.1-Traceability-Matrix-v1.0.md` (full traceability
in that document). Verified against the repository in this assessment.

| Layer | V2.1 state (evidence) |
|---|---|
| Domain | 11 modules, immutable dataclasses, zero deps (`backend/domain/*`) |
| Repositories | 9 async repositories over the service-role asyncpg pool (`backend/data/*`) |
| Infra | EventBus, AuditLogger, FactorSearchIndex, LLMClient, AppConfig, Supabase service client + pool (`backend/infra/*`) |
| Engines | 8 COMPLETE (matching, calculation, extraction, AI extraction, workflow, validation A1–A9, benchmarking internal-only, report generation 12-section structured) |
| DB | RC2 schema (~100 tables) + M1–M8 (import_batches, import_batch_id, calculation_snapshots, snapshot_id, domain_events, factor_aliases, dpq workflow cols, new-table RLS) |
| DB baseline | `emission_factors` = 7,049 (DEFRA-DESNZ GB 7,029 + SEAI IE 20 batch-linked) |
| API | 19 routes (`/api/v2/…`): health, 5 business, 13 admin (imports, providers, audit, aliases); error envelope; correlation ID; JWT via legacy `auth.py`; org isolation |
| Auth/RBAC | Legacy `backend/auth.py` (HTTPBearer JWT, require_role/permission/admin, require_org_access) |
| Legacy app | `backend/main.py` + 47 route modules (staff, workload, assignments, reviews, QC, SLA, queues, communications, reports, org management) — untouched, coexists |
| Tests | unit pytest PASS (api/domain/engines/infra); integration suite written but **unexecuted** (DB unavailable); supplementary harnesses 49/49, 74/74, 33/33, 44/44, 31/31 |
| Deviations | D1 (no `backend/providers/`), D2 (no ImportMappingEngine), D3–D12 (minor), D13 (legacy not renamed), D14 (integration verification gap) |
| Deferred/Future | EPA/ADEME/IPCC; Phase 11 admin remainder; RecommendationEngine; external benchmarking; PDF/HTML; `/process/*`; R20–R22 endpoints; `infra/cache.py`; metrics |

---

## 5. V3 Requirements Inventory

### 5.1 Documented V3 requirements (V3-001…V3-010)

| V3 ID | Requirement | Source | Business purpose | Current V2.1 capability | Gap | Priority | Impact classes |
|---|---|---|---|---|---|---|---|
| **V3-001** | Single canonical processing pipeline (CSV/Excel/AI-extraction/human-extraction/manual/API → one engine → validation → normalisation → matching → customer review → calculation → CO₂e) | VS1 §6A (authoritative diagram) | All inputs converge; no duplicate calculation engines | Engines exist (extraction → matching → calculation → validation → report). Missing: ingestion API (`/process/*`), human/AI extraction wiring | Ingestion + workflow wiring only | **High (core)** | API NEW; workflow EXTEND; no DB change |
| **V3-002** | Customer-supplied emission factors (factor column in CSV/Excel; customer supplies own value) | VS1 §8; VS8; VS9 | Customers bring own factors; validate/compare/accept/review | **None.** Matching/calculation use global `emission_factors` only; `CalculationRequest` requires a matched DB factor | Representation + validation + review all missing | **High** | DB CONDITIONAL; engine EXTEND; API NEW |
| **V3-003** | External Human Data Processing Entity model (multi-entity ops; Babui first) | VS1 §12–§15; VS2 §5–§10, §18–§19 | Contracted external workforce with isolation | **None.** Staff model is internal (`staff_profiles`); Babui = `company_name` metadata only | Entity identity, staff/roles, ops, isolation all missing | **Critical** | DB REQUIRED (conditional); domain NEW; RLS EXTEND; API NEW |
| **V3-004** | 500-doc multi-entity allocation (batch=grouping, work item=atomic) | VS1 §11; VS2 §23–§24 | Split large batches across entities/workers; per-item attribution | Legacy `upload_batches`, `manual_review_queue`, `review_assignment_history` (staff-centric) | Entity/worker-item allocation model | **High** | DB CONDITIONAL; workflow EXTEND |
| **V3-005** | Assignment/reassignment preserving attribution (worker failure) | VS1 §15; VS2 §25–§27 | Reassign incomplete work, never erase history | Legacy `review_assignment_history`, `reassignment_history`, `staff_workload` | Entity-scoped reassignment + partial-work recovery | **High** | DB CONDITIONAL; API EXTEND |
| **V3-006** | Five validation/approval layers (extraction → entity validation → entity approval → CT validation → customer review/approval) | VS1 §16; VS2 §29–§32 | Separate worker/entity/CT/customer approval | v2.1 ValidationEngine (A1–A9) + `customer_verifications`, `manual_review_queue` statuses | No entity validation/approval layer; no customer approve/reject flow | **High** | workflow EXTEND; API NEW; no DB change |
| **V3-007** | Issue management (type/severity/priority/status/owner/assignee/context/SLA/escalation/audit) | VS1 §18 | Track exceptions | Legacy `user_feedback`, `conversations`/`messages`, `approval_requests/decisions`, `manual_review_queue.escalation_level` | No unified issue entity | **Medium** | DB CONDITIONAL; API NEW |
| **V3-008** | Configuration hierarchy SYSTEM→CARBONTALLY→ENTITY→SUPERVISOR→WORKER (lower never overrides security/SLA/QC/compliance) | VS1 §19–§20 | Per-level settings with invariants | Legacy `system_settings`, `queue_settings` | No entity/team/worker config; no override invariants | **Medium** | DB CONDITIONAL; config EXTEND |
| **V3-009** | Auto-assignment strategies (manual/round-robin/least-loaded/capacity/skill/priority/SLA) | VS1 §21 | Automated allocation | Legacy manual assignment endpoints | No auto-assignment engine | **Medium** | engine NEW; no DB change |
| **V3-010** | QC (sampling, correction, rejection, rework, QC metrics) | VS1 §22; VS2 §30–§31 | Quality gates | Legacy `qc_checks`, `qc_checklists`, `qc_errors`, `staff_performance` | Entity-scoped QC + configurable sampling | **Medium** | DB CONDITIONAL; API EXTEND |

| **V3-011** | SLA/KPI/performance monitoring (provider + worker) | VS1 §23; VS2 §35–§36 | Ops visibility | Legacy `sla_definitions`, `sla_compliance`, `staff_workload`, `staff_performance`, `team_performance`, `dashboard_metrics`, `business_hours` | Entity-level SLA/KPI; provider capacity | **Medium** | DB CONDITIONAL; API EXTEND |
| **V3-012** | Data lineage/provenance with acquisition methods (CSV_UPLOAD/EXCEL_UPLOAD/AI_EXTRACTION/HUMAN_EXTRACTION/MANUAL_ENTRY/API) | VS1 §25 | Trace document→extraction→validation→factor→calc→CO₂e | v2.1 lineage strong: `calculation_snapshots`, `domain_events`, `audit_trail`, `emissions_logs.metadata`+`data_source` | Acquisition-method tagging not standardised | **High** | REUSE + EXTEND; no DB change |
| **V3-013** | Versioning/reprocessing (correction, re-extraction, remap, recalculation; preserve history) | VS1 §26; VS2 §55 | Historical integrity | `report_versions`, `draft_entries`, `customer_verifications`, append-only snapshots/events | Document-version workflow | **High** | workflow EXTEND; no DB change |
| **V3-014** | Data retention/deletion (cancellation, retention, Storage deletion, export-before-deletion) | VS1 §27 | Compliance/lifecycle | Legacy `delete_old_audit_logs` fn, user-deletion scrub fn (RC2 functions) | **Business policy undefined** — human decision, not invented | **Medium** | DB CONDITIONAL; API NEW |
| **V3-015** | Security/isolation at 10 levels incl. entity boundaries, break-glass access | VS1 §28; VS2 §41, §52, §54 | Entity↔entity, worker↔unassigned, customer↔entity isolation | v2.1 org isolation + RLS + legacy RBAC; **no entity boundary** | Entity RLS/policies + break-glass | **Critical** | RLS EXTEND; DB CONDITIONAL |
| **V3-016** | Storage security for entity/worker-scoped document access | VS1 §28 | Data minimisation | Legacy Storage policies (init schema) | Entity/worker-scoped Storage policies | **High** | Storage EXTEND |
| **V3-017** | Customer factor selection + recalculation on change | VS1 §7 | Customer picks factor; change triggers recalc | **None** in v2.1 API/engines | Full capability missing | **High** | engine EXTEND; API NEW; DB CONDITIONAL |
| **V3-018** | Customer communication via Customer Service only (no customer↔entity) | VS1 §17; VS2 §33–§34 | Single communication boundary | Legacy `conversations`/`messages`/`notifications` | Entity-communication boundary enforcement | **Medium** | API/RBAC EXTEND |
| **V3-019** | Outputs: CSV/Excel/JSON/API/dashboard | VS1 §6A | Deliver processed data | Legacy exports (`organizations/exports.py`, `export_history`); v2.1 report content structured | Output endpoints on v2.1 API | **High** | API NEW; no DB change |
| **V3-020** | No audited assurance/certification/ESG-reporting architecture | VS1 §3 | Scope guard | n/a — **do not build** | n/a | **Boundary** | DEFER/NOT APPLICABLE |

### 5.2 Inferred / architectural-recommendation items (NOT promoted to requirements)

- **V3-I1** External integrations (accounting/ERP/sustainability platforms, webhooks) — VS1 §34 lists audit areas only; no integration contract exists → **inference** until scoped.
- **V3-I2** Provider-replacement operational test (Batch #1000 → Provider B) — VS2 §38 — documented architecture acceptance test, not a committed feature.
- **V3-I3** Subscription/usage billing evolution — VS1 §37 audit area; legacy `customer_subscriptions`/`usage_tracking` exist → **inference**.
- **V3-I4** Advanced analytics/forecasting/AI insights — AI extraction is documented; forecasting is **not** → inference.
- **V3-I5** External/peer/sector benchmarking — V2.1 Phase 9 decision deferred; not documented as V3 → inference (see §13).

### 5.3 Recorded source conflicts

| Conflict | Sources | Observation |
|---|---|---|
| HDPE vs emission-factor providers | VS1 §6A "Human Data Processing Entities do NOT become emission-factor providers" vs VS5 Phase 12 (EPA/ADEME/IPCC emission-factor providers) | **Not a real conflict** — two different "provider" concepts (processing entities vs factor libraries). Both are documented; the V3 IA keeps them separate (§9 vs §20). |
| V2.1 benchmarking internal-only vs external benchmarking | VS4/VS5 (Phase 9 decision) vs VS1 §13 audit wording | External benchmarking is **not** a documented V3 requirement; the Phase 9 decision (internal-only, no reference data) remains authoritative. |
| v2.1 API philosophy vs new `/process/*` upload endpoints | VS6 CT-ARCH-012 (business-processing only) vs VS1 §6A (CSV/Excel upload) | CT-ARCH-012's "no CRUD" refers to data CRUD; document/CSV **ingestion** is business processing. Needs an explicit API-versioning decision (§15), not a conflict. |

---

## 6. V2.1 → V3 Component Impact

Verdict scale: **REUSE** (no change) · **EXTEND** (build on existing) · **MODIFY**
(change existing) · **REPLACE** (rebuild) · **NEW** (genuinely new) · **DEFER**
(not for V3) · **RETIRE** (obsolete) · **UNKNOWN** (insufficient evidence).

### 6.1 Architecture layers

| Component | Verdict | Evidence / rationale |
|---|---|---|
| Domain layer | **REUSE** + **NEW** (small) | 11 modules reused unchanged. NEW domain types needed: `DataProcessingEntity`, `WorkItem`/`Assignment`, `Issue`, `CustomerFactor` (decision-dependent) |
| Engines | **REUSE**/**EXTEND** | 8 engines reused; CalculationEngine + ValidationEngine + WorkflowOrchestrator extended for customer factors and entity layers; ImportMappingEngine NEW-or-DEFER (D2 decision) |
| Repositories | **REUSE** + **NEW** | 9 reused; NEW repositories for entity/work-item/issue (decision-dependent) |
| Infrastructure | **REUSE** | EventBus, AuditLogger (extend scope field), FactorSearchIndex, config, service pool all reused |
| API | **REUSE** + **NEW** | 19 v2.1 routes unchanged; NEW ingestion (`/process/*`), entity-ops, issue, customer-factor, output endpoints |
| Authentication | **REUSE** | `auth.py` JWT reused; entity-scoped claims derived from new RBAC |
| Authorization | **EXTEND** | `require_role`/`require_admin` extended with entity-scoped roles and break-glass |
| Events | **REUSE** + **EXTEND** | EventBus + domain_events reused; new event types for work-item/assignment/issue lifecycle |
| Audit | **EXTEND** | AuditRepository/AuditLogger reused; add entity scope + actor-role to entries |
| Processing | **EXTEND** | WorkflowOrchestrator + document_processing_queue + manual_review_queue; add work-item allocation |
| Queues | **EXTEND** | Legacy `processing_queue`/`document_processing_queue`/`manual_review_queue`/`report_generation_queue` coexist and overlap — consolidation decision (see §17) |
| Configuration | **EXTEND** | `system_settings`/`queue_settings` reused; entity/team/worker-level settings conditional |
| Storage | **EXTEND** | Storage buckets + signed URLs; entity/worker-scoped policies |
| Background processing | **NEW** (decision) | No v2.1 worker/queue consumer exists (legacy claim-queues unused by v2.1). V3 async jobs (import, extraction, recalc) need a worker or in-process task runner |

### 6.2 Engines

| Engine | Verdict | V3 change |
|---|---|---|
| FactorMatchingEngine | **EXTEND** | Already country/provider-aware. Extend for: provider-key disambiguation if multiple providers per country; customer factor override input; provider precedence config. Semantic stage remains opt-in. |
| CalculationEngine | **EXTEND** | Accept a customer-supplied factor value path (validated); provenance records `factor_source='CUSTOMER'`; unchanged for standard factors. |
| ValidationEngine | **EXTEND** | New rules: customer-factor validation, provider-conflict checks, entity-QA validation inputs. A1–A9 unchanged. |
| BenchmarkingEngine | **REUSE** | Internal benchmarking unchanged. External/peer benchmarking is **inference only** (§13) — DEFER. |
| ReportGenerationEngine | **REUSE** + **EXTEND** | Structured 12-section content reused; output adapters (CSV/Excel/JSON/API) new; PDF/HTML DEFER. |
| ImportMappingEngine | **NEW** or **DEFER** | V2.1 D2: absent. V3 decision: build engine vs keep CLI importers (with/without event-bus side effects). |
| DocumentExtractionEngine | **REUSE** | Text extraction reused; human-extraction ingestion is a workflow concern. |
| AIExtractionEngine | **REUSE** | LLM extraction reused; hook into V3 pipeline as one acquisition path. |
| WorkflowOrchestrator | **EXTEND** | Add entity-layer stages, review/approval transitions, reassignment, issue escalation, reprocessing. |
| RecommendationEngine | **DEFER** | V2.1 future item; not documented as V3. |
| AutoAssignmentEngine | **NEW** | V3-009 — no equivalent exists (legacy is manual assignment only). |

### 6.3 Data structures

| Structure | Verdict | V3 change |
|---|---|---|
| `emission_factors` | **REUSE** (GB/IE); **MODIFY** (constraint/index) if FR/global/EU | country CHECK + natural-key index conditional (see §9) |
| `factor_aliases` | **REUSE** | Org-scoped aliases reused; possibly extended for entity-scoped? (aliases are org-scoped — sufficient) |
| `import_batches` | **REUSE** | Batch versioning reused for new providers |
| `calculation_snapshots` | **REUSE** | Forensic records reused; customer-factor provenance via factor_source |
| `emissions_logs` | **REUSE** | `data_source`, `metadata`, `supplier_id`, `product_category_id`, `verified_by/at` reused for lineage/validation |
| `activity_categories`, `product_categories`, `units` | **REUSE** | Reference tables reused |
| `organizations`, `facilities`, `assets` | **REUSE** | Tenant/facility/asset model reused; `organizations` possibly extended with `org_type` (decision D1) |
| `reports`, `report_templates`, `report_versions`, `report_comments` | **REUSE** | Report estate reused for V3-019 outputs/versioning |
| Processing queues (4 legacy + dpq) | **EXTEND** | Work-item allocation; consolidation decision (§17) |
| Audit tables (`audit_trail`, `audit_logs`, `*_activity_log`) | **REUSE** + **EXTEND** | Entity scope |
| Staff/operations tables (staff_profiles, staff_workload, staff_performance, processing_assignments, review_assignment_history, reassignment_history, qc_*, sla_*, approval_*, manual_review_queue) | **EXTEND** | Reuse as the basis for the entity-ops model; add entity scope conditional on D1 |
| Conversations/messages/notifications | **REUSE** | Customer-communication boundary enforcement |
| `customer_documents`, `upload_batches`, `manual_extraction_*` | **REUSE** | Document/ingestion surface reused |
| `data_processing_entities` (processing entity) | **NEW** (if D1 → new table) | Absent today; required for V3-003 |

---

## 7. Database Impact Assessment

Classification per V3 requirement: **A** no DB impact · **B** existing-column
reuse · **C** existing-table extension · **D** new table · **E** migration-only/
data migration · **F** unknown.

| V3 ID | Requirement | Class | Why / what changes |
|---|---|---|---|
| V3-001 | Unified pipeline | **A** | `customer_documents`, `upload_batches`, `document_processing_queue`, `processing_queue`, `manual_review_queue` already represent ingestion + processing. Engine pipeline exists. No schema change. |
| V3-002 | Customer-supplied factors | **C**/**D** | No org-owned factor structure exists. Options: (D) new `customer_factors(organization_id, activity_type, unit, co2e_multiplier, scope, factor_source, status, valid_year)`; (C) add `organization_id`+`provider_key` to `emission_factors` (breaks global natural-key semantics — needs key rebuild); (B) per-record reuse via `emissions_logs.metadata` + snapshot `factor_source='CUSTOMER'` (weak: no factor library, and `calculation_snapshots.factor_id` NOT NULL FK to `emission_factors` forces a synthetic row). **Decision-dependent.** |
| V3-003 | HDPE entity model | **C**/**D** | No entity structure. Options: (D) new `data_processing_entities` + `entity_id` on staff/assignment/queue tables; (C) `organizations`-as-tenant + `org_type` discriminator + reuse `organization_members`/`roles`. Both are schema changes. **Decision-dependent (D1).** |
| V3-004 | Multi-entity allocation | **C** (depends on V3-003) | Work-item allocation reuses `manual_review_queue`/`upload_batches`/`processing_assignments`; needs `entity_id`/`worker_id` scoping only if entity model chosen. |
| V3-005 | Reassignment attribution | **B** | `review_assignment_history`, `reassignment_history`, `staff_workload` already store attribution; extend for entity scope conditional. |
| V3-006 | Five-layer approval | **B** | `customer_verifications`, `manual_review_queue.status`, `approval_requests/decisions`, `processing_audit_trail` cover layers; no new table strictly required. |
| V3-007 | Issue management | **B**/**C** | Reuse `conversations`/`messages` (issue as typed thread) + `user_feedback` + `escalation_level`. A dedicated `issues` table is optional (decision-dependent). |
| V3-008 | Config hierarchy | **B**/**C** | `system_settings` (JSONB), `queue_settings` exist; entity/team/worker settings via generic `settings(key, scope_type, scope_id, value)` or per-level tables — decision-dependent. |
| V3-009 | Auto-assignment | **A** | Algorithmic; reads existing workload/queue tables. No schema change. |
| V3-010 | QC | **B** | `qc_checks`, `qc_checklists`, `qc_errors`, `staff_performance` reused; entity scoping conditional. |
| V3-011 | SLA/KPI | **B** | `sla_definitions`, `sla_compliance`, `staff_workload`, `staff_performance`, `team_performance`, `dashboard_metrics`, `business_hours` reused; entity-level metric scoping conditional. |
| V3-012 | Lineage | **B** | `emissions_logs.data_source` + `metadata` JSONB; `calculation_snapshots` provenance; `domain_events`; `audit_trail`. Acquisition methods map to `data_source` strings. No schema change. |
| V3-013 | Versioning/reprocessing | **B** | `report_versions`, `draft_entries`, `customer_verifications`, append-only snapshots/events reused. Document-version column on `customer_documents` optional. |
| V3-014 | Retention/deletion | **B**/**E** | RC2 functions already scrub users/delete old logs. Retention **policy** is a human decision; implementation may need policy-driven jobs, not schema. |
| V3-015 | Security isolation | **C** (depends on V3-003) | Entity RLS requires entity FK on the tables to be isolated. RLS policies are migration objects but follow the entity-model decision. |
| V3-016 | Storage security | **A** | Policy/Storage-layer change (not relational schema). |
| V3-017 | Customer factor selection | **B**/**C** | Selecting an existing factor = B (store `factor_id` selection, e.g. in `emissions_logs.emission_factor_id`/snapshot). Customer-supplied **value** = same question as V3-002. |
| V3-018 | Customer communication | **A** | Existing `conversations`/`messages`; enforcement is code/RBAC. |
| V3-019 | Outputs | **B** | `export_history` + legacy export routes; v2.1 report content JSONB. No schema change. |
| V3-020 | No assurance/ESG | **A** | Nothing to build. |

### 7.1 Evidence-grounded findings that could force migration

1. **`emission_factors.country` CHECK (`country IN ('GB','IE')`)** — active via
   `emission_factors_country_in_list` (RC1 K1; re-applied in
   `20260801000000_rc2_constraints.sql` and `database/rc2/002_rc2_constraints.sql`).
   Any factor with `country='FR'` (ADEME), `'EU'` (residual mix) or global
   (IPCC) **fails the constraint**. EPA Ireland (`'IE'`) is fine.
2. **`emission_factors` natural-key unique index** — RC2 widened it to
   `(reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))`.
   It does **not** include `provider_key` or `factor_set`. Two providers in the
   same country/year/activity/unit/scope (SEAI + EPA IE) **collide**.
3. **No org-owned/customer factor representation** — `factor_aliases` is
   synonym-only; `emission_factors` is global; `calculation_snapshots.factor_id`
   is NOT NULL FK to `emission_factors`.
4. **No entity structure** — no `data_processing_entities`; Babui exists only as
   `auth.users.raw_user_meta_data.company_name`.
5. **No unified issue table** — issues would reuse conversations or be new.
6. **`organizations` has no type discriminator** — using it as the entity tenant
   requires `org_type`.

### 7.2 CRITICAL RULE compliance

Per the task's critical rule, the assessment **does not propose a schema change
merely because it would be cleaner**. Every potential change above is tied to a
documented V3 requirement that cannot be met by existing structures: entity
isolation (V3-003/015) needs an entity identity column/table; customer factor
values (V3-002/017) need a customer-factor representation; non-GB/IE factor
providers (V2.1 Phase 12, carried to V3) are physically rejected by the active
country CHECK. JSONB/metadata reuse was evaluated for each (V3-002: rejected for
factor-library semantics; V3-007: conversations sufficient).

---

## 8. V3 Migration Decision

### Does V3 require a database migration?

### **CONDITIONAL — depends on unresolved architectural decisions**

V3 as currently documented **cannot be answered YES or NO with certainty**
because three of its core requirements have multiple viable representations, and
the choice determines whether schema change is needed.

**Migration is NOT required** for the majority of documented V3 requirements
(V3-001 pipeline, V3-005/006/010/011/012/013/018/019 via existing tables,
V3-009/014/016 as code/policy). These are implementable on the current schema.

**Migration IS required** if any of the following enter the V3 scope:

| Trigger | Schema change | Existing-schema alternative evaluated |
|---|---|---|
| **T1 — HDPE entity model (V3-003, V3-015)** | (D) `data_processing_entities` + `entity_id` FK on staff/assignment/queue/audit tables **or** (C) `organizations.org_type` + reuse `organization_members` + new roles | Rejected: no entity identity, membership, isolation or lifecycle exists; legacy staff model is CarbonTally-internal only |
| **T2 — Customer-supplied factor values (V3-002, V3-017)** | (D) `customer_factors` **or** (C) `emission_factors.organization_id` (+ key rebuild) | Rejected for library semantics; `emissions_logs.metadata` alone cannot serve as a factor library and `calculation_snapshots.factor_id` NOT NULL FK forces a row |
| **T3 — Factor providers beyond GB/IE (ADEME/FR, IPCC/global, EU residual)** | (C) relax/replace `emission_factors_country_in_list` CHECK; (C) widen natural-key index to include `provider_key` | Rejected: the active CHECK physically rejects non-GB/IE countries; the RC2 natural key cannot distinguish two providers in one country |
| **T4 — Dedicated issue table (V3-007)** | (D) `issues` table | Optional — conversations-based reuse is viable; no migration if reuse chosen |
| **T5 — Entity/team/worker config hierarchy (V3-008)** | (D) generic scoped-settings table | Optional — `system_settings`/`queue_settings` can be extended; no migration if so |

### Migration inventory (PRELIMINARY — NOT TO BE CREATED)

If T1–T3 are confirmed in scope, the minimum backward-compatible change set is:

| Migration ID | Purpose | Tables affected | Columns | Constraints | Indexes | RLS | Data migration | Backward compat | Dependencies | Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| V3M-1 (if T1-D) | Processing entity model | `data_processing_entities` (new) + entity FK on `staff_profiles`/`manual_review_queue`/`processing_assignments`/`upload_batches`/`conversations` | `entity_id` nullable UUID + FK | FK ON DELETE RESTRICT/SET NULL | index entity_id | entity-scoped policies (deny-by-default + member-of-entity) | none (new table) | yes (nullable FKs) | D1 decision | Medium |
| V3M-2 (if T1-C) | Org-as-entity discriminator | `organizations` + `organization_members` | `org_type` VARCHAR + CHECK | CHECK | index org_type | reuse org_members RLS + new entity policies | backfill existing orgs to 'customer' | yes | D1 decision | Low–Medium |
| V3M-3 (if T2) | Customer factor library | `customer_factors` (new) or `emission_factors` extension | organization_id, provider_key='custom', status | FK org, CHECK multiplier ≥ 0 | natural-key (org, year, activity, unit) | org-scoped RLS | none | yes | D2 decision | Medium |
| V3M-4 (if T3) | Multi-provider factor constraints | `emission_factors` | none (constraint change) | DROP/REPLACE `country_in_list` CHECK (or widen list) | widen natural-key index with `provider_key` | none | none (existing rows unaffected) | yes | provider-scope decision | Medium (index rebuild on 7,049 rows — small) |
| V3M-5 (if T4) | Issue management | `issues` (new) | org/entity/batch/document refs, type, severity, priority, status, owner, assignee, SLA, escalation | FK org | indexes | org+entity RLS | none | yes | D3 decision | Low |

**No migration file has been or will be created by this assessment.**

---

## 9. Emission Factor Architecture

Baseline: `emission_factors` (7,049 rows: DEFRA-DESNZ/GB 7,029 + SEAI/IE 20,
batch-linked), `import_batches`, `factor_aliases`, `calculation_snapshots`.

| Concern | Current state | V3 assessment |
|---|---|---|
| Provider identity | `import_batches.provider_key` (defra, seai, epa, ademe, ipcc, custom per M1 comment); factors derive provider via `import_batch_id`; `factor_source`/`factor_set` carry library identity | **Adequate.** Provider identity is derivable; EPA (IE) fits today |
| Country | `CHECK (country IN ('GB','IE'))` | **Bounded.** IE OK (EPA). FR/global/EU **rejected by the CHECK** (trigger T3) |
| Region | `region_deprecated` (retired RC1/RC2 C4) | **Do not revive.** A future EU/regional concept needs a deliberate decision (new region column or country='EU' semantics) |
| Natural key | RC2 index `(reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))` — no provider_key/factor_set | **Collision risk** for two providers in one country/year/activity (SEAI + EPA IE). Widening to include `provider_key` is trigger T3 |
| Versioning | `factor_set` (DEFRA-2025, SEAI-2025) + `import_batches` is_active/rolled_back_from | **Adequate** — reused as-is |
| Provenance | `factor_source`, `factor_set`, `import_batch_id`, source_checksum | **Adequate** |
| Aliases | `factor_aliases` (global + org-scoped synonyms) | **Adequate**; customer-supplied factor **values** are a different concept (V3-002) |
| Provider-specific metadata | None beyond factor_source/set | Adequate via JSONB `metadata` if ever needed (no change required) |
| CO2 vs CO2e | `co2e_multiplier` column carries both; `gas_coverage` discipline via factor_source | **Adequate**; labelling decision already recorded (SEAI gate) |

**Verdict:** the current schema **can accommodate additional providers without
migration for GB/IE-valid jurisdictions** (EPA Ireland works today — new import
batch + factors, no schema change). It **cannot** accommodate ADEME (FR), IPCC
(global) or EU residual-mix factors without relaxing the country CHECK (T3), and
two same-country providers require the natural-key widening. No schema change is
recommended unless those providers enter V3.

## 10. Factor Matching Impact

| V3 concern | Verdict | Detail |
|---|---|---|
| Multi-country matching | **REUSE** | FactorMatchingEngine is country/provider-aware (SEAI/DEFRA isolation proven) |
| Multiple providers per country | **EXTEND** | Needs `provider_key` in disambiguation when SEAI+EPA (IE) coexist; matching config (`prefer_provider`) already exists |
| Provider-specific terminology | **REUSE** | Aliases + keyword stages cover |
| Aliases | **REUSE** | Org-scoped aliases reused |
| Unit matching | **REUSE** | NaturalKey/Exact stages use unit; UnitMismatchError on calculate |
| Geography | **EXTEND** (conditional) | Country OK; region/EU geography only if T3 providers enter |
| Reporting year | **REUSE** | `reporting_year` in request + factor |
| Scope | **REUSE** | Scope-aware stages |
| Electricity | **REUSE** | Electricity factors present (DEFRA + SEAI) |
| CO2 vs CO2e | **REUSE** | `gas_coverage` provenance preserved through match/validate |
| Provider precedence | **EXTEND** | `prefer_provider` config exists; formal precedence policy needed for multi-provider countries |
| Ambiguous matches | **REUSE** | AMBIGUOUS/no_match + suggestions explicit |
| Customer-specific factors | **EXTEND** | New input path for customer-supplied/selected factors (V3-002/017) |

**Verdict: EXTEND (incremental).** No replacement. Matching remains the IP core.

## 11. Calculation Engine Impact

| V3 concern | Verdict | Detail |
|---|---|---|
| CO2/CO2e mixed datasets | **REUSE** | `gas_coverage` preserved; no relabelling (pycheck9d proven) |
| Unit conversion | **REUSE** | Unit mismatch → error; no silent conversion (existing contract) |
| Factor provenance | **REUSE** | `calculation_snapshots` carry factor_source/set/import_batch_id |
| Factor version | **REUSE** | factor_set + batch versioning in snapshot |
| Calculation snapshots | **REUSE** | Append-only forensic records + verify_reproducibility |
| Reproducibility | **REUSE** | content_hash + verify (Phase 6) |
| Historical calculations | **REUSE** | snapshots immutable; historical integrity intact |
| Future provider factors | **REUSE** | quantity × multiplier is provider-agnostic |
| Customer-supplied factor value | **EXTEND** | `CalculationRequest` currently requires a matched `EmissionFactor`; needs an optional customer-factor path with provenance `factor_source='CUSTOMER'` and validation (V3-002/017) |
| Recalculation on change | **EXTEND** | V3-017: re-run pipeline on factor/correction change; new snapshots append |

**Verdict:** the calculation architecture **remains valid**. Extension is
limited to the customer-factor input path and recalc triggers.

## 12. Validation Engine Impact

| V3 rule | Classification | Detail |
|---|---|---|
| A1–A9 (existing) | **REUSE** | Unchanged |
| Additional providers (GB/IE) | **REUSE** | Country/provider checks already provider-aware |
| Additional geographies (FR/global/EU) | **EXTEND** | Only if T3 providers enter; country-set checks extend |
| New factor types (customer factors) | **EXTEND** | Validate customer-supplied factor (value ≥ 0, unit, scope, source, conflict with reference factor) |
| New scopes/categories | **REUSE** | scope/unit consistency rules generic |
| New calculation methodologies | **REUSE** | `CalculationMethodology` enum extensible; methodology in request |
| Provenance | **REUSE** | gas_coverage + batch provenance checks (A5) |
| Provider conflicts | **EXTEND** | Flag when customer factor conflicts with matched reference factor |
| Historical factors | **REUSE** | Snapshot validation on old records |
| Data quality | **REUSE** | A1–A9 cover; A10–A13 remain deferred |
| API ingestion | **EXTEND** | Validate ingestion payloads (CSV rows, entity submissions) at the boundary |
| External integrations | **EXTEND** (future) | Validation of inbound data formats when integrations exist (V3-I1) |

**Verdict: EXTEND.** Existing A1–A9 core reused; new rules are additive.

## 13. Benchmarking Impact

| Capability | Documented V3? | Verdict |
|---|---|---|
| YoY, facility, scope, FTE/area/revenue, activity intensity (Phase 9 internal) | Yes (V2.1) | **REUSE** — unchanged |
| Sector benchmarking | **No** (inference V3-I5) | **DEFER** — requires reference data (V2.1 D7 decision stands) |
| Peer benchmarking | **No** | **DEFER** |
| Supplier benchmarking | **No** | **DEFER** |
| External datasets | **No** | **DEFER** |
| Geographic benchmarking | **No** (beyond internal) | **DEFER** |
| Industry datasets | **No** | **DEFER** |
| Forecasting | **No** (inference V3-I4) | **DEFER** |
| AI insights | **No** | **DEFER** |

**Verdict: REUSE for V3.** No documented V3 requirement adds external
benchmarking; the Phase 9 internal-only decision remains authoritative.

## 14. Reporting Impact

| V3 concern | Documented V3? | Verdict |
|---|---|---|
| Structured 12-section report (V2.1) | Yes | **REUSE** |
| Validation + benchmarking sections | Yes | **REUSE** |
| Provenance + lineage | Yes (V3-012) | **REUSE** + tag acquisition methods |
| CSV/Excel/JSON/API outputs | Yes (V3-019) | **EXTEND** — output adapters on v2.1 API + `export_history` reuse |
| PDF/HTML rendering | **No** (V2.1 future) | **DEFER** — legacy `report_generator.py`/`pdf_engine.py` remain unused |
| Richer report templates | **No** | **DEFER** — legacy `report_templates` exist but not V3-documented |
| Report versioning | Yes (V3-013) | **REUSE** — `report_versions`/`report_comments` |
| Comments | Partial (V3-013) | **REUSE** — `report_comments` |
| Approvals (customer review) | Yes (V3-006/021) | **EXTEND** — customer approve/reject on processed results |
| External reporting formats | **No** | **DEFER** — no V3-documented regulatory formats |
| Regulatory frameworks (SECR/ESRS/ISSB) | **No** | **DEFER** — columns exist on `organizations` (secr/esrs/issb_enabled) but no V3 requirement; do not build (V3-020 boundary) |
| Customer-specific reporting | **No** | **DEFER** |

**Verdict: REUSE + EXTEND (outputs, approval workflow).** PDF/regulatory
reporting remain future.

---

## 15. API Impact

### 15.1 Existing v2.1 routes

| Route group | V3 verdict | Detail |
|---|---|---|
| `GET /api/v2/health` | **REUSE** | Unchanged |
| Business: `/factor-match`, `/calculate`, `/validate`, `/benchmark`, `/generate-report` | **REUSE** + **EXTEND** | Contracts unchanged; `calculate` gains optional customer-factor input (V3-002/017); `/generate-report` gains output-format param (V3-019) |
| Admin: imports/providers/audit/aliases | **REUSE** | Unchanged; aliases remain the org-scoped synonym surface |
| `/api/v2/docs`, `/api/v2/openapi.json` | **REUSE** | Auto |

### 15.2 New V3 routes

| New API | V3 ID | Notes |
|---|---|---|
| `POST /api/v2/process/csv`, `/process/excel`, `/process/pdf`, `/process/documents` (ingestion) | V3-001 | CT-ARCH-012 business-processing ingestion; async job semantics |
| `GET /api/v2/jobs/{id}`, `GET /api/v2/jobs` | V3-001 | Async job status (import/extraction/recalc) |
| `POST /api/v2/customer-factors`, `GET/PUT/DELETE /api/v2/customer-factors/{id}` | V3-002/017 | Customer factor library CRUD (decision-dependent) |
| `POST /api/v2/entities`, entity staff/roles, entity lifecycle/offboarding | V3-003 | Entity-ops control plane (decision-dependent) |
| `POST /api/v2/work-items/{id}/assign`, `/reassign`, `/complete`, `/return` | V3-004/005 | Work-item allocation; entity-scoped |
| `POST /api/v2/reviews/{id}/approve|reject|return` | V3-006/021 | Entity + customer review layers |
| `GET/POST /api/v2/issues`, `PUT /api/v2/issues/{id}` | V3-007 | Issue management (decision-dependent) |
| `POST /api/v2/reports/{id}/export` (CSV/Excel/JSON) | V3-019 | Output adapters |
| `POST /api/v2/customer-reviews/{id}/approve|reject` | V3-006/021 | Customer review/approval |
| Entity ops dashboards/analytics | V3-011 | SLA/KPI endpoints |

### 15.3 API policy questions (human decisions)

1. **Versioning** — v3.0 namespace vs additive routes on v2.1. Recommended: **keep v2.1 API stable** and add V3 routes under a new prefix (e.g. `/api/v3/…`) or as extension modules; the 19 existing routes should not break (V2.1 consumers unaffected).
2. **Async vs sync** — ingestion/processing should be asynchronous (job semantics) given 500-document batches; v2.1 business endpoints stay sync.
3. **Webhooks** — V3-I1 inference; not a documented requirement → DEFER.
4. **Auth** — JWT bearer unchanged; entity-scoped tokens/claims follow the RBAC decision.

## 16. Security / RBAC / RLS Impact

| Control | V3 verdict | Detail |
|---|---|---|
| Authentication (JWT) | **REUSE** | `auth.py` HTTPBearer unchanged |
| RBAC | **EXTEND** | Legacy `roles`/`staff_roles`/`organization_members` reused; NEW entity roles (Manager/Supervisor/Worker/Validator) scoped to entity; consultant model preserved |
| Admin authorization | **REUSE** + **EXTEND** | `require_admin` unchanged; entity-scoped admin surface new |
| Organization isolation | **REUSE** | Existing org isolation + repo filters unchanged |
| **Entity isolation** | **NEW** (critical) | Entity↔entity, entity↔customer, worker↔unassigned-document boundaries do **not exist**. Requires entity identity + entity-scoped RLS + code-level filters + Storage policies (V3-003/015/016) |
| RLS | **EXTEND** | New entity policies; existing RC2/M8 policies unchanged; deny-by-default pattern reused |
| Storage | **EXTEND** | Entity/worker-scoped bucket policies + signed URLs (data minimisation per VS2 §42) |
| Audit | **EXTEND** | AuditLogger/audit_trail reused; add `entity_id` scope + actor-role; break-glass access audit (VS2 §54) |
| Service-role/background jobs | **REVIEW** (V3 task §52) | v2.1 repos use the service-role pool with code-level org filters — the same discipline must extend to entity scope; no change until entity model exists |
| Realtime | **UNKNOWN** | Legacy Realtime config; entity-scoped Realtime boundaries not designed |

**Security gaps for V3 (no changes performed):** entity isolation (absent),
break-glass mechanism (absent), per-entity audit scope (absent), Storage
entity-scoping (absent), rate limiting (absent on v2.1 API, legacy-only).

---

## 17. Processing / Queue Impact

| Concern | Current state | V3 verdict |
|---|---|---|
| Document processing | v2.1 engines + `document_processing_queue` (RC2) + legacy `processing_queue` | **EXTEND** — work-item model + ingestion jobs |
| Queue estate | **Four overlapping queues exist**: `processing_queue` (legacy), `document_processing_queue` (v2.1 workflow), `manual_review_queue` (human review), `report_generation_queue` (v2.1 report store) | **Consolidation decision required.** v2.1 workflow uses dpq; legacy routes use processing_queue + manual_review_queue. V3 must not add a fifth queue without a decision (§22 debt, §27 decision) |
| Batch processing | `upload_batches` (legacy) + v2.1 `import_batches` (factor imports — different concept) | **REUSE** — do not conflate factor import batches with processing batches |
| Manual review | `manual_review_queue` (rich: priority, SLA, escalation_level, customer_notified, data_entry JSONB) | **EXTEND** — becomes the work-item surface with entity scoping |
| Human extraction | `manual_extraction_batches`/`items` | **EXTEND** — entity extraction workflow |
| Assignments | `processing_assignments`, `review_assignment_history`, `reassignment_history` | **EXTEND** — entity scoping + attribution preserved |
| QA | `qc_checks`/`qc_checklists`/`qc_errors` | **EXTEND** — entity-scoped QA + sampling |
| Reprocessing | v2.1 reprocessing via workflow; legacy draft_entries | **EXTEND** — versioning + recalc |
| Asynchronous API jobs | **None** in v2.1 (sync endpoints) | **NEW** — job runner/worker for V3-001 ingestion (decision: worker process vs in-process tasks) |
| Webhooks | **None** | **DEFER** (V3-I1) |

**Conclusion:** the existing queue architecture is **sufficient in breadth but
overlapping in implementation**. V3 should select ONE work-item queue surface
(recommendation: extend `manual_review_queue`/dpq as the work-item store) rather
than add new queue tables, and explicitly retire or leave dormant the legacy
`processing_queue` until the legacy surface is migrated.

## 18. Human-in-the-Loop Impact

| Workflow | Current | V3 verdict |
|---|---|---|
| Extraction (human) | Legacy `manual_review_queue`/`manual_extraction_*` + staff routes | **EXTEND** — entity workers as extractors |
| Validation | v2.1 ValidationEngine (automated) | **REUSE** — automated layer unchanged; entity human validation is an approval-layer workflow |
| Mapping | Legacy manual review data_entry JSONB | **EXTEND** — entity mapping/QA workflow |
| QA | Legacy qc_* tables + staff_workload | **EXTEND** — entity-scoped QC + sampling (V3-010) |
| Approval | Legacy approval_requests/decisions + customer_verifications | **EXTEND** — five-layer separation (V3-006): worker submission ≠ entity approval ≠ CT validation ≠ customer approval |
| Correction/rework | Legacy draft_entries, review_history | **EXTEND** — reprocessing + versioning (V3-013) |
| Reassignment | Legacy reassignment_history | **EXTEND** — entity/worker reassignment with attribution (V3-005) |
| Internal staff workflow | Legacy admin/staff, workload, reviews | **REUSE** as the CarbonTally-internal half of the two-system model (VS2 §18) |
| Customer review | `customer_verifications` + `customer_review_log` | **EXTEND** — approve/reject on processed results (V3-021) |

**V3 verdict: EXTEND.** The legacy app already implements a staff-centric
human-in-the-loop model; V3's work is (a) introducing the entity dimension and
(b) enforcing the five-layer approval separation. No new human-workflow concept
is documented beyond these.

## 19. External Integrations

| Integration | Direction | Documented V3? | Auth | Data format | Frequency | DB/API impact | Verdict |
|---|---|---|---|---|---|---|---|
| Sustainability/carbon platforms | out | **No** (V3-I1 inference) | n/a | n/a | n/a | none | **DEFER** until scoped |
| Accounting/ERP systems | in | **No** | n/a | n/a | n/a | none | **DEFER** |
| Utility platforms | in | **No** | n/a | n/a | n/a | none | **DEFER** |
| External emission-factor sources (EPA/ADEME/IPCC/EU) | in | Yes (V2.1 Phase 12) | public | xlsx/CSV | annual | `import_batches` + factors (T3 conditional) | **Provider work** (§20) |
| Webhooks | both | **No** (V3-I1) | n/a | n/a | n/a | none | **DEFER** |
| API outputs for customers | out | Yes (V3-019) | JWT | JSON/CSV/Excel | on-demand | none (code only) | **EXTEND** |

**Conclusion:** no external system integration is documented as a committed V3
requirement. Only the emission-factor provider sources (V2.1 Phase 12) are real,
and they are data imports, not system integrations.

## 20. Provider Roadmap

| Provider | Current status (verified) | V3 requirement (documented) | Data available | Importer needed | Schema impact | Engine impact | Priority |
|---|---|---|---|---|---|---|---|
| DEFRA | **COMPLETE** — 7,029 GB factors; CLI importer | Reuse; keep current | Yes (imported) | none | none | none | — |
| SEAI | **COMPLETE** — 20 IE factors, batch-linked; CO2-only | Reuse; keep current | Yes (imported) | none | none | none | — |
| EPA (Ireland) | **DEFERRED** (V2.1 Phase 12) | Deferred item — candidate V3 | Published (source not in repo) | new CLI pipeline or plugin | **none** (IE passes country CHECK; natural-key OK unless SEAI overlaps) | matching EXTEND if same-activity overlap | Medium |
| ADEME (France) | **DEFERRED** | Deferred item — candidate V3 | Published (source not in repo) | new | **country CHECK violation (FR)** → T3 | matching EXTEND (FR geography) | Low–Medium |
| IPCC (Global) | **DEFERRED** | Deferred item — candidate V3 | Published | new | **country CHECK violation (global)** → T3 | matching EXTEND | Low |
| EU electricity/residual mix | **NOT LISTED** in V2.1 Phase 12 | **Not documented** in V2.1; VS1 mentions EU residual-mix only as future-factor example | n/a | n/a | **country CHECK violation (EU)** → T3 | matching EXTEND | Low (inference) |
| Custom org libraries | **NOT IMPLEMENTED** | V3-002/017 customer factors (related but distinct) | customer-supplied | new (customer factor surface) | T2 conditional | calculation/matching EXTEND | High (with V3-002) |

**Note (V3 prompt §6A):** Human Data Processing Entities are processing
providers, **not** emission-factor providers. These two "provider" axes are kept
separate throughout this assessment (§9 vs §20).

---

## 21. Testing Impact

### CURRENT TESTS (reuse as the V3 regression backbone)

| Suite | Current | V3 use |
|---|---|---|
| `tests/unit/api` (77) | pytest PASS | **REUSE** — unchanged; guards the 19 v2.1 routes that V3 must not break |
| `tests/unit/domain` (~146) | pytest PASS | **REUSE** |
| `tests/unit/engines` (~251) | pytest PASS | **REUSE** + extend for engine changes |
| `tests/unit/infra` (~71) + `test_core` (14) | pytest PASS | **REUSE** |
| `tests/integration` (21 files, ~90) | **written, unexecuted** (DB unavailable) | **BLOCKER for V3** — the integration suite must be executable before V3 work that touches DB/RLS |
| Supplementary harnesses (49/49, 74/74, 33/33, 44/44, 31/31) | standalone | **REUSE** as supplementary |

### NEW V3 TESTS REQUIRED

| Test area | V3 ID | Notes |
|---|---|---|
| Customer-factor unit tests (validation, provenance, conflict) | V3-002/017 | CalculationEngine + ValidationEngine extension |
| Entity model domain/repo tests | V3-003 | DataProcessingEntity lifecycle, isolation |
| Work-item assignment/reassignment tests (attribution preserved) | V3-004/005 | incl. partial-work recovery |
| Five-layer approval flow tests | V3-006/021 | worker→entity→CT→customer |
| Issue workflow tests | V3-007 | if issues table chosen |
| Auto-assignment strategy tests | V3-009 | round-robin/least-loaded/capacity |
| QC sampling tests | V3-010 | configurable sampling |
| Entity RLS/security tests | V3-015/016 | entity↔entity, worker↔unassigned, customer↔entity |
| Multi-provider matching tests (SEAI+EPA IE collision) | T3 | natural-key/provider disambiguation |
| Non-GB/IE provider constraint tests | T3 | country CHECK behaviour |
| Ingestion/`/process/*` contract tests | V3-001 | CSV/Excel/PDF ingestion + async jobs |
| Output export tests (CSV/Excel/JSON/API) | V3-019 | |
| Migration tests | T1–T5 | only if migrations are designed |
| RLS policy tests (entity) | V3-015 | |
| Security/authorization tests (break-glass, entity scope) | V3-015 | |
| End-to-end pipeline test (document→review→calc→output) | V3-001/019 | |
| Legacy regression (47 route modules) | — | confirm V3 changes do not break the legacy app |

**Note:** the **integration-suite executability gap (V2.1 D14) is a precondition
for V3** — entity RLS, work-item allocation and multi-provider factors are
database-integration-heavy and cannot be verified by supplementary harnesses
alone.

## 22. Deviation Analysis (V2.1 → V3)

| ID | V2.1 deviation | V2.1 status | V3 impact | Severity | Blocking? | Recommended action |
|---|---|---|---|---|---|---|
| D1 | No `backend/providers/` plugin architecture | HIGH (Phase 5) | New factor providers (EPA/ADEME/IPCC) continue as CLI importers; V3 decides plugin-vs-CLI formalisation | High | No | Decision: formalise CLI importer pattern OR build plugin layer before provider expansion |
| D2 | No `ImportMappingEngine` | HIGH (Phase 5) | V3 import side-effects (events/audit) remain ununified; customer-factor imports need a path | High | No | Decision: build engine or accept CLI + documented side-effect handling |
| D3 | `CalculationSnapshot` provenance on sink, not domain | LOW | Cosmetic; no V3 impact | Low | No | Leave |
| D4 | `ReportsRepository` → `report_generation_queue` | LOW | V3 output/export layer works on structured content; fine | Low | No | Leave |
| D5 | No `infra/cache.py`/`metrics.py` | LOW | V3 observability (SLA/KPI) would benefit from metrics; not required | Medium | No | Add metrics with V3-011 if scoped |
| D7 | No benchmark reference data | MEDIUM (scope decision) | External benchmarking remains out; matches V3 findings | Low | No | Keep deferred |
| D13 | Legacy not renamed `backend_legacy` | MEDIUM | Legacy ops surface (47 modules) is the reuse candidate for V3-003/004/005; coexistence must be deliberate | Medium | No | Explicit legacy-strategy decision before V3 ops work |
| D14 | Integration suite unexecuted | HIGH (verification gap) | **Blocks V3 verification** (entity/RLS/multi-provider are integration-heavy) | High | **Yes — for V3 verification** | Make `carbontally_test` runnable; run canonical suite |

## 23. Technical Debt Impact (material to V3 only)

| Debt | Evidence | V3 impact |
|---|---|---|
| Four overlapping queue surfaces (`processing_queue`, `document_processing_queue`, `manual_review_queue`, `report_generation_queue`) | init schema + v2.1 workflow + legacy routes | Must pick ONE work-item surface before V3-004/005; otherwise V3 adds a fifth |
| Legacy operational app (47 route modules) separate from v2.1 engine stack | `backend/routes/` | The entity-ops control plane (V3-003) must decide legacy-extension vs v2.1-native — a fork risk if both are extended in parallel |
| No entity abstraction | schema/code inspection | Core V3-003 gap |
| Customer-factor absence | `CalculationRequest` requires matched `EmissionFactor` | V3-002/017 gap |
| `emission_factors` country CHECK + natural-key without provider_key | RC2 constraints | T3 trigger |
| Legacy `report_generator.py`/`pdf_engine.py` duplicates v2.1 report content | files exist, unused | Not a V3 task (PDF deferred); leave dormant |
| Integration test environment unavailable | D14 | V3 verification blocker |
| v2.1 API sync-only | `api/business.py` | V3-001 async ingestion needs a job mechanism |
| No metrics/observability | `infra/` has no metrics module | V3-011 SLA/KPI monitoring depends on metrics |

---

## 24. V3 Scope Boundary

### MUST BE V3 (genuinely necessary — core)

| Item | V3 ID | Rationale |
|---|---|---|
| Single canonical processing pipeline + ingestion (`/process/*`) | V3-001 | Authoritative diagram; the product's core promise |
| Customer review/approval of processed results | V3-006/021 | Required by the canonical pipeline (APPROVE/REJECT) |
| External Human Data Processing Entity model | V3-003 | "Critical V3 requirement" (prompt §12); enables Babui |
| Entity isolation (RBAC/RLS/Storage/audit) | V3-015/016 | Non-negotiable security boundary for entities |
| Assignment/reassignment with attribution | V3-004/005 | The 500-doc multi-entity allocation example |
| Data lineage with acquisition methods | V3-012 | Auditability of all inputs |
| Customer-supplied factor handling | V3-002/017 | Explicitly audited in the prompt; feature-list item |
| Versioning/reprocessing preserving history | V3-013 | Historical integrity |
| Outputs CSV/Excel/JSON/API | V3-019 | Canonical pipeline outputs |

### SHOULD BE V3 (useful, not strictly required)

| Item | V3 ID | Rationale |
|---|---|---|
| Five-layer approval separation as explicit workflow states | V3-006 | Refines core; can phase in after entity model |
| Issue management | V3-007 | Operations need it for entity work; conversations-based MVP viable |
| Auto-assignment strategies | V3-009 | Efficiency; manual assignment is the MVP |
| QC sampling + metrics | V3-010/011 | Quality gates; legacy tables make it cheap |
| Entity/worker SLA/KPI dashboards | V3-011 | Operations visibility |
| EPA (Ireland) emission-factor provider | Phase 12 | Zero schema impact; fits today |

### SHOULD REMAIN FUTURE (must NOT enter V3)

| Item | Rationale |
|---|---|
| ADEME (FR), IPCC (global), EU residual-mix factors | Trigger T3 (country CHECK + natural key); not V3-required |
| External/peer/sector benchmarking | Not documented; needs reference data |
| PDF/HTML report rendering | Not documented; legacy renderers dormant |
| Regulatory frameworks (SECR/ESRS/ISSB) / audited assurance | Explicit V3-020 boundary — do not build |
| RecommendationEngine / AI insights / forecasting | Not documented |
| External system integrations (accounting/ERP/webhooks) | V3-I1 inference only |
| Subscription/billing evolution | V3-I3 inference |
| Custom factor-library management UI (beyond API) | Not documented |

## 25. Proposed Implementation Order

**Ordering is advisory; nothing is implemented.**

1. **Architecture decisions (HUMAN)** — the §27 decisions (entity tenant model,
   customer-factor representation, provider scope, queue consolidation, API
   versioning, legacy strategy) — gates everything below.
2. **Verification precondition** — make `carbontally_test` reachable and run the
   canonical suite (D14) before any V3 DB/RLS work.
3. **Foundation (no schema change)** — V3-001 ingestion + async job runner;
   V3-019 output adapters; V3-012 lineage tagging; V3-013 reprocessing/versioning.
4. **Customer factors (decision-gated)** — V3-002/017 extension of
   CalculationEngine/ValidationEngine + API; V3M-3 if a factor library is chosen.
5. **Entity model (decision-gated)** — V3-003 domain/repo/API + V3M-1 or V3M-2
   + entity RLS (V3-015) + Storage policies (V3-016).
6. **Operations plane** — V3-004/005 work-item assignment/reassignment;
   V3-006 approval layers; V3-007 issues; V3-009 auto-assignment; V3-010/011
   QC/SLA/KPI (reusing legacy tables).
7. **Provider work** — EPA (IE) import if scoped; D1/D2 decision on importer
   formalisation; V3M-4 only if FR/global/EU providers are later scoped.
8. **Testing** — new unit/contract/integration/RLS/security suites (§21).
9. **Security/RLS hardening** — break-glass, entity audit scope, rate limiting.
10. **Documentation** — update V2.1 baseline; record decisions as ADRs.

---

## 26. Risk Assessment

| Risk | Probability | Impact | Severity | Mitigation |
|---|---|---|---|---|
| Entity isolation misconfigured (entity↔entity / worker↔unassigned leak) | Medium | Data breach across processing entities | **Critical** | Entity RLS deny-by-default + code-level filters + Storage policies + entity-scoped tests before go-live (V3-015/016) |
| Natural-key collision when a second IE provider (EPA) overlaps SEAI | Medium | Wrong-factor matching for IE activities | **High** | Widening the natural key with `provider_key` (T3) before EPA import; matching precedence policy |
| Queue proliferation (fifth queue) without consolidation decision | High | Ops confusion, duplicated work-item state | **Medium** | One work-item surface decision (§17/§27) before V3-004 |
| Legacy/v2.1 fork on the ops plane (both extended in parallel) | Medium | Divergent operational logic; double maintenance | **High** | Legacy-strategy decision (D13) before V3 ops work |
| Integration suite still unexecutable at V3 start (D14) | High | V3 DB/RLS changes unverifiable | **High** | Fix `carbontally_test` environment as a V3 precondition |
| Customer-factor representation chosen without validation discipline | Medium | Unvalidated customer factors corrupt calculations | **High** | Customer-factor validation rules in ValidationEngine + audit provenance |
| ADEME/IPCC/EU scoped without T3 constraint work | Low (if deferred) | Insert failures on country CHECK | **Medium** | Keep those providers out of V3 scope (§24) |
| V3 scope creep (benchmarking/reporting/integrations) | Medium | V3 becomes an uncontrolled expansion | **High** | §24 boundary + §27 decisions enforced as gate |
| Breaking the 19-route v2.1 API during extension | Low | Existing consumers break | **High** | API versioning decision (§15.3); additive routes; contract tests |

## 27. Human Decisions Required

Cline must **not** make these autonomously. All are genuinely unresolved.

| # | Decision | Options | Why unresolved | Blocks |
|---|---|---|---|---|
| **H1** | Processing-entity tenant model | (a) new `data_processing_entities` table; (b) `organizations`-as-tenant with `org_type` | No entity concept exists; both are schema changes; affects RLS, staff model, every entity-scoped table | V3-003/004/005/015 (migration T1) |
| **H2** | Customer-factor representation | (a) `customer_factors` library; (b) `emission_factors` extension; (c) per-record metadata reuse | Three viable models with different semantics and snapshot-FK implications | V3-002/017 (migration T2) |
| **H3** | V3 provider scope (emission-factor providers) | EPA only vs EPA+ADEME+IPCC vs none | Determines country CHECK/natural-key migration (T3) | V3M-4; §20 |
| **H4** | Work-item/queue consolidation | Extend `manual_review_queue`/dpq vs new table vs legacy `processing_queue` | Four overlapping queues exist; no owner | V3-004/005 |
| **H5** | Legacy operations strategy | Extend legacy routes vs v2.1-native rebuild vs hybrid | 47 legacy modules vs v2.1 engine stack | V3-003 ops plane |
| **H6** | API versioning | `/api/v3/…` vs additive routes vs breaking v2.1 | V2.1 consumers; CT-ARCH-012 philosophy | §15.3 |
| **H7** | Issue management representation | Dedicated `issues` table vs conversations-based | V3-007 wording; legacy alternatives exist | V3M-5 (optional) |
| **H8** | V3 release boundary | Which MUST/SHOULD/FUTURE items enter | Prompt says "eventually support" for many | §24 |
| **H9** | External benchmarking inclusion | In vs out | Not documented; needs reference data | §13 |
| **H10** | Reporting scope | Structured outputs only vs templates/PDF | PDF not documented | §14 |
| **H11** | Data retention/deletion policy | retention periods, export-before-delete, Storage deletion | Business/legal policy — must not be invented | V3-014 |
| **H12** | Entity lifecycle states + offboarding sequence | adopt VS2 §9/§23 lifecycle vs custom | Business process definition | V3-003/004 |
| **H13** | Provider (HDPE) contract metadata | minimal vs contractual fields | VS2 §10 says "can be implemented later" | V3-003 |
| **H14** | Async job runner | worker process vs in-process tasks vs legacy queue consumer | No v2.1 worker exists | V3-001 |

---

## 28. Final V3 Impact Summary

### Reusable unchanged (REUSE)
- All 8 V2.1 engines' core contracts (matching pipeline, calculation ×, snapshot/hash/verify, A1–A9 validation, internal benchmarking, 12-section structured report).
- All 9 repositories and the AbstractRepository contract.
- Infra: EventBus, AuditLogger, FactorSearchIndex, AppConfig, Supabase service client + asyncpg pool.
- The 19 v2.1 API routes (kept stable; additive V3 routes).
- Legacy auth (`auth.py` JWT/RBAC), org isolation, RC2 + M1–M8 migrations, factor baseline (7,049), legacy operational tables (assignments, review history, QC, SLA, queues, conversations, reports).
- Legacy ops app (47 route modules) as the reuse candidate for the internal-half of the entity model.

### Requiring extension (EXTEND)
- CalculationEngine (customer-factor input path), ValidationEngine (customer-factor + provider-conflict rules), WorkflowOrchestrator (entity layers, approval states, reassignment, issues), FactorMatchingEngine (provider disambiguation/precedence), ReportGenerationEngine (output adapters).
- Auth/RBAC, audit (entity scope), RLS (entity policies), Storage (entity-scoped buckets), configuration, queue surfaces (one work-item model).

### Requiring modification (MODIFY)
- `emission_factors` constraints/index **only if** non-GB/IE providers or a second same-country provider enter scope (T3).
- `organizations` (add `org_type`) **only if** the org-as-tenant entity model is chosen (H1-b).
- Legacy app strategy (retire vs extend) — D13.

### New V3 components (NEW)
- Ingestion API (`/process/*`) + async job runner.
- Data Processing Entity model (domain + repo + API) — decision H1.
- Customer-factor surface (domain + repo + API) — decision H2.
- Work-item allocation/reassignment service.
- Issue service (if H7 → table) — decision-gated.
- AutoAssignmentEngine.
- Customer review/approval flow endpoints.
- Entity-ops dashboards/SLA-KPI (V3-011).

### New V3 database requirements
- None, **if** the entity model reuses conversations/org tables and customer factors stay per-record.
- **Conditional:** `data_processing_entities` (or `organizations.org_type`) for H1; `customer_factors` (or `emission_factors` extension) for H2; country-CHECK + natural-key widening for T3; `issues` for H7.

### Existing database modifications
- Only the T1/T2/T3 conditional set (V3M-1…V3M-5 preliminary inventory, §8). Backward-compatible nullable FKs; no data migration for existing 7,049 factors.

### API changes
- 19 routes stable; new V3 routes (§15.2); versioning decision (H6); async job semantics for ingestion.

### Provider changes
- DEFRA/SEAI untouched. EPA (IE) fits without schema change. ADEME/IPCC/EU conditional on T3. HDPE entities are a separate provider axis (§20).

### Engine changes
- Extensions only (§6.2); no engine replaced. ImportMappingEngine decision (D2).

### Security changes
- Entity isolation (RBAC/RLS/Storage/audit), break-glass, entity audit scope, rate limiting. No existing policy changed.

### Testing changes
- Reuse all V2.1 suites as regression; new suites in §21; **integration-suite executability (D14) is a V3 precondition.**

### Deferred items
- ADEME/IPCC/EU factors, external benchmarking, PDF/HTML, regulatory frameworks, integrations, webhooks, forecasting, subscription billing.

## 29. Final Migration Verdict

### `V3 DATABASE MIGRATION CONDITIONAL — HUMAN ARCHITECTURE DECISION REQUIRED`

**Evidence supporting the decision:**

1. **The majority of documented V3 requirements need no migration.** The
   canonical pipeline (V3-001), lineage (V3-012), five-layer review (V3-006),
   reassignment attribution (V3-005), QC (V3-010), SLA/KPI (V3-011),
   versioning (V3-013), outputs (V3-019), retention (V3-014) and
   auto-assignment (V3-009) are all implementable on the existing RC2 + M1–M8
   schema, reusing `emissions_logs`, `calculation_snapshots`, `domain_events`,
   `audit_trail`, `manual_review_queue`, `review_assignment_history`,
   `reassignment_history`, `qc_*`, `sla_*`, `report_versions`,
   `conversations`, `customer_documents` and `upload_batches`.
2. **Three core requirements are physically blocked by the current schema** and
   force migration **if and only if** they enter V3 scope:
   - **Entity model (V3-003/015):** no entity identity/isolation exists; Babui is
     `auth.users.raw_user_meta_data.company_name` only. → new table (H1-a) or
     `organizations.org_type` (H1-b).
   - **Customer-supplied factor values (V3-002/017):** no org-owned factor
     representation; `calculation_snapshots.factor_id` NOT NULL FK to the global
     `emission_factors` forbids a value-only path. → `customer_factors` (H2-a) or
     `emission_factors` extension (H2-b).
   - **Non-GB/IE providers (T3):** active `CHECK (country IN ('GB','IE'))`
     rejects FR/global/EU rows; the RC2 natural-key index
     `(year, activity_type, country, unit, scope)` cannot distinguish two
     providers in one country. EPA (IE) alone needs neither.
3. **No V3 data migration is required** in any branch: all candidate changes are
   additive/backward-compatible (nullable FKs, new tables, constraint/index
   replacement), and the existing 7,049 factors are untouched.

**Therefore: do NOT create any migration now.** The preliminary inventory
(V3M-1…V3M-5, §8) is provided only so that the H1–H3/H7/H11 decisions can be
made with full knowledge of the migration consequences. Once the human decisions
in §27 are taken, the confirmed subset becomes the migration design input —
designed and reviewed before any schema change.

## 30. Evidence / References

| # | Evidence | Used for |
|---|---|---|
| E1 | `docs/cline/prompts/CarbonTally V3 — Final Architecture & Impact Assessment Prompt.md` | Canonical V3 architecture (§6A); 20 documented requirements |
| E2 | `docs/cline/CarbonTally_Platform_Processing_Architecture_Master_v1.md` | HDPE model, lifecycle, isolation, QC, SLA, audit, break-glass |
| E3 | `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md` | V2.1 baseline, deviations D1–D14 |
| E4 | `supabase/migrations/` (16 files) | RC2 constraints (country CHECK, natural key), M1–M8 |
| E5 | `database/rc2/002_rc2_constraints.sql`, `database/rc1/002_rc1_constraints.sql` | K1 country CHECK, K5 natural-key UNIQUE |
| E6 | `supabase/migrations/00000000000000_init_schema.sql` | emissions_logs/manual_review_queue/organizations/staff/queues DDL |
| E7 | `backend/engines/calculation.py` | `CalculationRequest` requires matched `EmissionFactor` (no customer-factor path) |
| E8 | `backend/api/*` (router, business, admin_*) | 19 v2.1 routes; error envelope; org isolation |
| E9 | `backend/auth.py` | JWT/RBAC surface |
| E10 | `backend/routes/` (47 modules) | Legacy ops surface (assignments, workload, reviews, staff, QC) |
| E11 | `backend/tests/unit/api/*`, `_phase10_selfcheck.txt` (49/49), `pycheck9d.txt` (74/74) | Test baseline |
| E12 | `dbprobe9d.txt` + `CarbonTally-SEAI-Development-DB-Import-v1.0.md` | Factor baseline 7,049 (7,029 + 20) |
| E13 | `tools/carbon_data_factory/schema.txt`, `prisma/schema.prisma` | Dev-DB mirror (corroborating evidence only) |
| E14 | `docs/CarbonTally Complete Customer Feature List.md`, business viability report | "Custom factors" feature context |
| E15 | `docs/cline/CarbonTally-Phase9*-v1.0.md`, `CarbonTally-Phase10-API-Admin-v1.0.md`, SEAI series | Phase completion evidence |

---

**V3 IMPACT ASSESSMENT COMPLETE — READY FOR ARCHITECTURE DECISIONS**
















