# CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922

**Task:** Read-only master program preflight — Insight expansion, L7 (data lifecycle), L8 (resilience + commercial), and investor-demo readiness.
**Kind:** FORENSICS / PLANNING ONLY. This document **authorizes nothing**. It contains no implementation, no migration, no policy and no commercial decision.
**Repository:** `/home/shomonrobie/ct_93d5cdd` · branch `p8-release-reconciled` · remote `github`
**Baseline HEAD at preflight start:** `f1a7cce557fbe0d2a8684bf24a6080cf8392df9b`
**Labels:** **EXISTS** (verified in code) · **PARTIAL** · **MISSING** · **PO DECISION REQUIRED** · **NOT AUTHORIZED** · **INFERENCE** (reasoned from verified facts).

---

# 1. Executive summary

**The platform is substantially further along than the Insight roadmap implies, and the binding constraint on the next phase is governance, not engineering.**

Verified findings that change how the remaining work should be planned:

1. **INS-01 is closed and independently verified, including the database work.** OHD applied the migration live inside the real 79-file chain (78 applied cleanly), ran 75/75 schema checks and 30/30 live concurrency checks, and proved idempotency across three applications. The limitation recorded in the implementation report (“SQL not executed”) is therefore **closed by independent verification**, not outstanding.
2. **L7 is not greenfield.** A configurable retention capability already exists end to end: `system_settings` retention columns (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days`), the API `GET/PUT /api/v3/settings/retention` (`backend/api/v3_settings.py:72,82`), the server-side enforcer `backend/services/retention.py`, and the deployment entry point `python -m tools.enforce_retention [--apply]` (dry-run by default). The gaps are specific: only **two** of the five configured domains are enforced; there is **no legal hold**, **no organisation/account deletion path**, **no storage-object deletion propagation**, and the Insight conversation/interaction ledgers have **no delete surface by design** (deferred to I7 in code comments).
3. **L8-A is further along than assumed.** Phase 8-X delivered a real-data-path health probe (`/health`, `backend/main.py`), operational alerting (`backend/services/operational_alerting.py`), API runtime metrics (`backend/services/api_metrics.py` + `backend/data/api_metrics.py`, registered in `main.py`, with unit and live integration tests), and a backup/recovery drill tool (`tools/backup_recovery_drill.py`) with a drill record in `docs/operations/`. Technical rate limiting is closed under INS-01.
4. **L8-B is a configurable commercial *data model*, not a billing system.** Versioned plans (`BillingPlansRepository.publish_new_version`), commercial config, a credit ledger with balances, subscriptions, assisted/managed orders with approve/cancel, storage usage, a payment *record* type and idempotency keys exist in `backend/data/billing.py`, `backend/domain/billing.py`, `backend/api/v3_billing.py` and two D37 migrations — with **no payment-service-provider integration** (a repository search finds no Stripe/PayPal/Gocardless/Adyen SDK; `domain/billing.py:270` describes a future PayPal/Wise/card intent; `data/billing.py:398` only preserves Stripe-named columns). Production billing therefore remains **PO DECISION REQUIRED**, not partially built.
5. **The demo stack is real and repeatable:** `tools/demo_lab/` (lab.py, provision.py, stack.py, storage.py, verify.py, `run_demo_lab.sh`, `reset_demo_lab.sh`, T3 scenario harness, factor seeding) plus `tools/carbon_data_factory/`, `tools/generate_synthetic_documents.py` and seven investor-demo verification records in `docs/demo-investor/` (DR-001…DR-007). The lab never reseeds the investor dataset — that boundary is asserted in its README and reset script.
6. **Two documentation-vs-code divergences exist and must not be resolved by assumption:** the X2 alerting and X7 metrics *contract records* describe their status as “IMPLEMENTATION BLOCKED / PO DECISION REQUIRED”, while **implementation, tests and wiring exist in the repository**; and `AGENTS.md` §54 points at `tools/seed_investor_demo/DEMO_IDENTITIES.md`, which **does not exist in this checkout** (the real demo manifest is `tools/demo_lab/manifest.json`). Per the source-of-truth hierarchy the code is authoritative, but the records should be reconciled by the PO/OHD rather than silently edited.

**Recommended immediate next step (proposal only):** the PO-announced next planning artifact — the **CarbonTally Insight Capability Coverage Matrix** (`CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` §15) — because it is the prerequisite for every subsequent package boundary, and §4–§5 of this preflight supply the family-by-family evidence it needs.

---

# 2. Verified repository baseline

| Item | Verified value |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD (preflight start) | `f1a7cce557fbe0d2a8684bf24a6080cf8392df9b` — `docs(p8): independent OHD verification of Insight discovery, aggregation, provenance and rate limiting` |
| `github/p8-release-reconciled` | `cbc529dd8974d3ec16595fc5c6981c5217b43c24` |
| Alignment | **`1 0` — local HEAD is one commit AHEAD of the remote**: the OHD verification commit `f1a7cce` is local-only |
| Working tree | Clean except untracked PO/ChatGPT-supplied documents (listed below) |
| Recent history | `f1a7cce` (OHD verification) → `cbc529d` (report) → `e4ea325` (implementation) → `c7cd9cc` (preflight) → `7f97b55` → `669669a` |
| Migrations tracked at HEAD | **79** `.sql` files under `supabase/migrations/` |
| Pre-existing test failures (established by OHD at baseline and HEAD) | **4**: the stale migration-count pin `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`, plus three assertions in `test_review_sla_surfaces.py` |

**Untracked, PO-supplied (must remain unmodified and uncommitted unless separately authorized):** `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`, `…2026-09-22.md` (v1), `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`, `docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`, `docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md`, and three `docs/ChatGPT/…` history documents.

**Durability note (PO requirement, `…Post-Closure_Reconciliation…` §12):** the closure requires the OHD verification report to be pushed “without content modification, together with this PO closure record”. The OHD report is committed locally (`f1a7cce`) and **becomes published by the documentation push this task performs**; the PO closure record remains untracked and is **not** committed here, because §14 of this task permits only this preflight report. `PO DECISION REQUIRED` if the closure record and the PO reference documents are to be committed.

---

# 3. INS-01 closure confirmation

**Status: CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED. OHD verdict: PASS WITH NON-BLOCKING OBSERVATIONS.** Confirmed against the repository, not against memory:

* implementation `e4ea3254c6a709df0e9cedcd8c719515363b4358` on preflight `c7cd9cc2ff56e288c830bb5d204118a06aa31104`; final implementation/report `cbc529dd8974d3ec16595fc5c6981c5217b43c24` — all present in history;
* the OHD verification report `docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-OHD-VERIFICATION-20260922.md` (388 lines) is **tracked in git** at `f1a7cce`;
* the INS-01 migration `supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` was applied **live** inside the real chain: 78 of 79 migrations applied cleanly; the single failure (`20260823000000_d32_private_documents_storage.sql`, `relation "storage.buckets" does not exist`) is an environment prerequisite of an older, unrelated migration (Supabase Storage creates that schema) and occurred **before** the verified migration (OHD §5.1);
* 75/75 schema checks and 30/30 live concurrency/atomicity checks passed; idempotency was proven across three applications; the seven-name tool CHECK and the fifteen-value answer CHECK were verified; both limiter tables exist with RLS enabled and no policy;
* INS-01 accepted eight non-blocking carry-forward observations (`…Post-Closure_Reconciliation…` §8.1–§8.8). **This preflight does not reopen them** and proposes no remediation — including the defence-in-depth `EXISTS` organisation-predicate observation (§8.1), the stale tool-registry comment (§8.3), the limiter-table cleanup question (§8.5), and the still-unverified live deployed HTTP end-to-end (§8.8).

**INFERENCE:** future packages may treat the INS-01 surfaces (seven tools, fifteen answer states, bounds 25/50/100, limiter defaults 20/5/2 and 100/20/10) as **verified platform foundations** and build on them without re-verifying them.

## 3.1 Reconciled facts this preflight adds

| Fact | Evidence | Effect on planning |
| --- | --- | --- |
| `AGENTS.md` §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md` | repository-wide `find` (excluding `.venv`) returns nothing; the real demo infra is `tools/demo_lab/` with `manifest.json` | Documentation drift; the demo identity manifest for **this** checkout is `tools/demo_lab/manifest.json` |
| X7 API-runtime-metrics contract says “IMPLEMENTATION BLOCKED — PO DECISION REQUIRED” | `docs/architecture/CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915.md` §Status vs `backend/services/api_metrics.py`, `backend/data/api_metrics.py`, `backend/main.py:274-288`, `tests/unit/services/test_api_metrics_x7.py`, `tests/integration/test_api_metrics_x7_runtime.py` | Code is authoritative: X7 appears implemented and wired; the record is stale. `PO DECISION REQUIRED` only to reconcile the record |
| X2 alerting contract says “IMPLEMENTATION BLOCKED AT THE `PX-6` GATE” | `docs/architecture/CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md` §2 vs `backend/services/operational_alerting.py`, `tests/integration/test_operational_alerting_x2_runtime.py`, `backend/data/notifications.py` | Same divergence; the contract’s named config columns (`sla_breach_alert_enabled`, `sla_breach_alert_recipients`, `sla_default_hours`) have **no code references** — the live alerting configuration surface must be established by inspection, not assumed |
| A real production incident is documented | `tests/integration/test_pdf_ocr_memory_runtime.py` — “Render API OOM, 512 MiB limit, 2026-09-17 → 2026-09-19”; `backend/pdf_engine.py:49` references the F-070-D incident | Incident provenance exists in tests; **no incident-response runbook** was found in `docs/operations/` |

---

# 4. Insight capability coverage assessment (all 19 families)

Method: for each family the table records what the **repository** provides (engine, data model, evidence path, Insight reachability) and what is missing. “Engine” means a deterministic server-side computation over authoritative data — never an LLM path. “Insight reachable” means an I3 tool exists (the catalogue is the seven tools verified in §3).

## 4.1 Families 1–10

| # | Family | Deterministic engine / data model (verified) | Evidence depth | Insight reachable? | Missing / gap | New schema? | Accounting-policy decision? | I7/I8? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Identified Calculation** | `data/emissions_logs.get_snapshot`, immutable `calculation_snapshots`, `engines/calculation.py` | **E3** (snapshot → `source_line_item_id` → viewer) | **EXISTS** — `calculation_snapshot_lookup` | none for the single-record case | no | no | no |
| 2 | **Discovery** | `search_snapshots` / `count_matching_snapshots` + `domain/insight_query.py` | E2/E3 (candidate ids + evidence lines) | **EXISTS** — `insight_discovery` | facility/asset need a linked log row; supplier data empty | no | no | no |
| 3 | **Aggregation** | `aggregate_groups` (7 allowlisted dimensions) + existing `aggregate()` for the period total | **E1** (CO₂e by dimension; no per-group ids) | **EXISTS** — `insight_aggregation` | no scope/category *filter*; no cross-tab; no summed quantity (by design) | no | no (basis fixed at kg CO₂e) | no |
| 4 | **Aggregate Provenance** | `list_group_snapshots` / `count_group_snapshots` | **E2 → E3** | **EXISTS** — `insight_aggregate_provenance` | provenance covers log-linked snapshots only | no | no | no |
| 5 | **Scope Analysis** | scope grouping via `aggregate_groups(dimension="scope")`; scope views also in `api/v3_emissions.py:284` (`/scope-breakdown`), legacy `routes/emissions.py:224`, `routes/organizations/dashboard.py:68` | E1/E2 | **PARTIAL** — grouping exists, **filtering does not** | scope filter across other dimensions; scope comparison | no | **PO DECISION REQUIRED** (comparison semantics) | no |
| 6 | **Scope 3 Categories 1–15** | none. Legacy `backend/utils/emissions.py:132,141,171` only sets a coarse `ghg_protocol_category` ("Other"); `domain/disclosure.py` carries `scope_hint` only | none | **MISSING** | versioned taxonomy, assignment rule, storage, historical semantics, per-category reporting | **yes** | **yes** — GHG Protocol baseline taxonomy + assignment policy | no |
| 7 | **Scope 2 Methodology** | `SCOPE2_METHODS = ("LOCATION_BASED","MARKET_BASED")` exists only as a disclosure vocabulary (`domain/disclosure.py`, `disclosure_requirement_versions.scope2_method_hint`); no market-based total, no instrument register, no residual mix | none for market-based | **MISSING** | method dimension on calculations, contractual-instrument store, factor hierarchy, dual reporting | **yes** | **yes** — eligibility, instrument quality, residual mix | no |
| 8 | **Scope 1 Decomposition** | none (no stationary/mobile/fugitive/process classification anywhere in the repository) | n/a | **MISSING** | classification dimension + decomposition rule | **yes** | **yes** — decomposition schema and rule | no |
| 9 | **Supplier Intelligence** | `aggregate_groups(dimension="supplier")` + `group_labels` over `public.suppliers`; discovery `EXISTS` on `emissions_logs.supplier_id`; `data/suppliers.py` (incl. `remove`) | E1/E2 | **PARTIAL** — dimension exists, **data empty** | **no write path populates `emissions_logs.supplier_id`** (re-confirmed INS-01 §11, OHD §18); capture lives upstream on `manual_extraction_items.mapped_supplier_id` | column exists; a persistence/backfill policy is required | **PO DECISION REQUIRED** — capture point, confidence/approval rule, backfill, lineage | no |
| 10 | **Facility / Asset Intelligence** | `aggregate_groups(dimension="facility"/"asset")` over `metadata->>'facility_id'` and `asset_id`, labelled from `public.facilities`/`public.assets`; master-data UI `frontend/src/v3/admin/{FacilitiesTab,LocationsTab}.jsx` | E1/E2 | **PARTIAL** (foundation) | snapshot-native attribution; comparisons/changes absent | no for the foundation | no (attribution already deterministic) | no |

## 4.2 Families 11–19

| # | Family | Deterministic engine / data model (verified) | Evidence depth | Insight reachable? | Missing / gap | New schema? | Accounting-policy decision? | I7/I8? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | **Temporal Comparison** | period aggregation exists; `data/reporting.py:785` zero-filled monthly trend; legacy `report_generator.py` YoY narrative (not an Insight surface) | E1/E2 | **MISSING** as an Insight capability | an explicit bounded two-period comparison (absolute + percentage change) on one authoritative basis | no | **PO DECISION REQUIRED** — aligned periods, restatement handling, percentage basis | no |
| 12 | **Variance / Attribution** | none — no factor/activity/methodology/boundary attribution engine exists | n/a | **MISSING** | attribution methodology and deterministic decomposition | **yes** (likely) | **yes** — attribution methodology and restatement rules | no |
| 13 | **Emission Factor Intelligence** | snapshot stores `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `factor_set`, `co2e_multiplier`, `methodology`, `algorithm_version`; `data/factors.py`, `data/customer_factors.py`, `data/aliases.py`, `engines/matching_stages.py` | E2 | **PARTIAL** — the factor *used* is explainable; candidate history is not | historical factor metadata (unit/country/reporting-year/activity-type at calculation time), candidate/stage history, factor-change attribution | **yes** for a full factor-history contract | **PO DECISION REQUIRED** — what historical factor metadata must be retained | no |
| 14 | **Data Quality Intelligence** | `completeness_score` in two distinct places: organisation-profile completeness (`routes/organizations/metadata.py:525`, `management.py:1177`) and extraction completeness (`services/automatic_extraction.completeness_score`, used at `services/ai_document_extraction.py:243`); validation issues (`engines/validation.py`, `issues` table, `/issues` UI); review queue | E1/E2 | **MISSING** | a bounded quality summary over authoritative records (missing/unmapped/unresolved/blocked) | no (reads existing issue/queue tables) | **PO DECISION REQUIRED** — which quality signals are authoritative | no |
| 15 | **Methodology / Boundary Intelligence** | `calculation_snapshots.methodology`; `domain/disclosure.py` requirement versions; `data/reporting.py`; organisation profile/boundary fields | E1/E2 | **MISSING** | explicit methodology/boundary explanation contract; organisational vs operational boundary as first-class data | **yes** (boundary model) | **yes** — boundary definition and consolidation approach | no |
| 16 | **Evidence / Audit Intelligence** | `audit_trail` (append-only: `data/audit.py:294` `save` inserts only; `delete` documented as never used), `api/admin_audit.py` (list/export/correlation/by-id), `evidence_line_items`, viewer `/evidence/line-items/{id}`, `report_evidence_lookup` | **E3 / E4 partial** | **PARTIAL** | a bounded “reproduce this number” contract tying snapshot → factor → evidence → approval | no | **PO DECISION REQUIRED** — what constitutes an audit package (E4) | no |
| 17 | **General Carbon-Accounting Knowledge (Mode E)** | **none** — no knowledge store, no embeddings, no RAG (`services/insight_context.py` states no embeddings/vector search) | E0 | **MISSING** | governed, versioned knowledge source with citations, kept separate from customer data | **yes** | **yes** — source governance, versioning, citation policy | no (but needs content governance) |
| 18 | **Reporting / Disclosure Assistance** | real engine: `engines/reporting` + `data/reporting.py`, `report_versions`, `report_version_artifacts`, `data/report_artefacts.py`, disclosure projection, `api/v3_reports.py`, exports `api/v3_exports.py` | E2/E3 | **PARTIAL** — `report_lookup`, `report_version_lookup`, `report_evidence_lookup` | mapping a question to the correct report/obligation and explaining coverage gaps | no for the assistance layer | **PO DECISION REQUIRED** — frameworks/obligations in scope | no |
| 19 | **Decision / Reduction Intelligence** | none in the backend (no reduction-target or scenario model) | n/a | **MISSING** | reduction/abatement modelling on authoritative data | **yes** | **yes** — target/scenario methodology and recommendation framing | no |

**Coverage summary:** **EXISTS 4** (1–4) · **PARTIAL 6** (5, 9, 10, 13, 16, 18) · **MISSING 9** (6, 7, 8, 11, 12, 14, 15, 17, 19).

**INFERENCE (the ordering insight this preflight contributes):** five of the nine MISSING families (6, 7, 8, 12, 15) are blocked on **accounting taxonomy/model decisions**, while four (11, 14, 16-audit, 18-assistance) can be built on data that **already exists**. That split drives the package sequence in §11: the decidable work can proceed now; the taxonomy work cannot start until the PO decides.

---

# 5. Question Library coverage mapping

`docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md` (971 lines; the v2 architecture confirms it is a **coverage and acceptance catalogue, not a feature list**). Mapping rule applied: each question maps to a capability **family** (§4), a deterministic engine, an evidence requirement and an answer state — never to a bespoke handler.

| Question-Library area | Representative questions | Family | Deterministic engine today | Answer state today | Status |
| --- | --- | --- | --- | --- | --- |
| Identified calculation / factor used / source | “Why is this calculation 2,469 kg CO₂e?”, “Which factor was used?” | 1, 13 | `calculation_snapshot_lookup` + snapshot factor fields | `success` / `no_data` / `multiple_matches` / `not_authorized` | **ANSWERABLE** for a referenced record |
| Discovery by date/amount/activity/scope/period | “Which calculation was ~20,000 kg CO₂e on 2024-02-02?” | 2 | `insight_discovery` (planner + bounded filters) | `success` / `no_data` / `multiple_matches` / `needs_clarification` | **ANSWERABLE** |
| Aggregation by scope/month/year/activity/supplier/facility/asset | “Emissions by facility in 2024”, “Totals by month” | 3 | `aggregate_groups` (7 dimensions) | `success` / `zero` / `no_data` / `invalid_input` | **ANSWERABLE** (supplier returns `no_data` on current data) |
| Aggregate provenance | “Which calculations make up Scope 1?” | 4 | `insight_aggregate_provenance` | `success` / `no_data` | **ANSWERABLE** |
| Scope comparison / contribution | “How does Scope 1 compare with Scope 3?” | 5 | scope grouping only | `needs_clarification` today | **NOT YET IMPLEMENTED** |
| Scope 3 categories | “What is our Category 1 footprint?”, “Which category is largest?” | 6 | none | `unsupported` | **NOT YET IMPLEMENTED** (schema + policy decision) |
| Scope 2 dual reporting | “What is our market-based Scope 2?”, “Which instruments cover it?” | 7 | disclosure hint only | `unsupported` | **NOT YET IMPLEMENTED** |
| Scope 1 decomposition | “How much of Scope 1 is fugitive?” | 8 | none | `unsupported` | **NOT YET IMPLEMENTED** |
| Supplier intelligence | “Which supplier contributed most?” | 9 | supplier dimension (empty data) | `no_data` | **PARTIAL** (`no_data` is the truthful state) |
| Facility / asset intelligence | “Which site emitted most?”, “Which asset changed?” | 10 | facility/asset dimension + labels | `success` / `no_data` | **PARTIAL** (comparison absent) |
| Temporal comparison | “Is this month higher than last month?”, “Year over year?” | 11 | none (legacy YoY narrative only) | `unsupported` | **NOT YET IMPLEMENTED** |
| Variance / attribution | “Why did emissions increase?”, “What caused the change?” | 12 | none | `unsupported` | **NOT YET IMPLEMENTED** |
| Data quality | “What data is missing?”, “Which records are unmapped?”, “How complete is our data?” | 14 | issues/queue/profile completeness exist but are not exposed to Insight | `unsupported` | **NOT YET IMPLEMENTED** (exposure gap only) |
| Methodology / boundary | “What methodology was used?”, “What is our organisational boundary?” | 15 | snapshot methodology exists; boundary model does not | `unsupported` | **NOT YET IMPLEMENTED** |
| Evidence / audit | “What supports this number?”, “Can it be reproduced?”, “What changed?” | 16 | `report_evidence_lookup` + viewer + append-only audit | `success` / `no_data` (partial) | **PARTIAL** (no audit-package contract) |
| Concept / standards knowledge | “What is market-based Scope 2?” | 17 | none | `unsupported` | **NOT YET IMPLEMENTED** (Mode E; v2 lists it as future) |
| Reporting / disclosure assistance | “Is our report ready?”, “What is missing for SECR?” | 18 | report + disclosure projection engines | `success` / `no_data` for *existing* reports | **PARTIAL** (no obligation mapping) |
| Decision / reduction | “How do we reach net zero by 2030?”, “What is the cheapest reduction?” | 19 | none | `unsupported` | **NOT YET IMPLEMENTED** |
| Consultant / auditor surfaces | consultant portfolio and auditor read surfaces | — | consultant APIs exist outside Insight; I2 supports client scoping | `not_authorized` for Insight | **DEFERRED / NOT AUTHORIZED** (capability matrix §4 item 14) |

**Answer-state discipline:** every row maps onto the existing fifteen I4 answer states (`success`, `zero`, `no_data`, `not_authorized`, `insufficient_data`, `needs_clarification`, `multiple_matches`, `tool_failure`, `provider_unavailable`, `partial`, `rate_limited`, `refused`, `ungrounded`, `invalid_input`, `error`). **INFERENCE:** no family in §4 requires a new answer state — “capability does not exist yet” is already represented by the planner’s `unsupported` outcome. If the PO wants a user-visible “not yet supported” state that is distinct from `invalid_input`, that is a **PO DECISION REQUIRED** (it would become a sixteenth state, i.e. an I4 contract change).

**Question Library size:** 426 candidate questions. Per v2 §9 the 426/426 metric is explicitly rejected as a completeness measure; the meaningful measures are capability-family coverage (4/19 EXISTS, 6/19 PARTIAL, 9/19 MISSING), representative-question acceptance tests, and truthful unsupported/no-data handling. **This preflight does not re-count or re-classify all 426 questions**; that mapping is the PO-announced next artifact (§16).

---

# 6. L7 forensic assessment (data lifecycle) — verified state

**Headline: L7 is partially implemented, deliberately narrow, and blocked on product decisions rather than on engineering.**

## 6.1 What exists (verified)

| Area | Verified implementation | Notes |
| --- | --- | --- |
| Configurable retention | `backend/data/settings.py` reads/writes the `system_settings` retention columns (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days`) under key `platform_retention`; unset is returned as `None` — **no value is invented** | `backend/api/v3_settings.py:72` `GET /api/v3/settings/retention`, `:82` `PUT` |
| Enforcement | `backend/services/retention.py` (`_ELIGIBLE_DOMAINS = ("document_retention_days", "operational_telemetry_retention_days")`, `build_policy()`, `enforce_retention()`); CLI `python -m tools.enforce_retention [--apply]`, **dry-run by default** | Only **two** of five configured domains are enforced |
| Document lifecycle | `backend/data/organization_files.py::expire_documents_older_than` → `UPDATE … SET deleted_at = NOW()`; **soft-delete only, rows never hard-deleted** | Consumed by the enforcer |
| Telemetry retention | `data/notifications.py::prune_operational_alerts_before`, `data/document_processing.py::prune_operational_metrics_before`; the X2/PX-7 domain default is **90 days detail / aggregates indefinitely** (schema default, not invented here) | Telemetry only |
| Never-purge invariant | `_TELEMETRY_EXCLUDED_TABLES = ("document_processing_queue", "processing_logs", "report_versions", "report_version_artifacts", "evidence_line_items", "calculation_snapshots", "emissions_logs", "audit_trail")`, exposed via `telemetry_excluded_tables()` so verification can assert it | Explicit audit/evidence invariant |
| Audit immutability | `backend/data/audit.py` — `save()` inserts only (append-only); `delete()` documented as unused (“audit is immutable”); `api/admin_audit.py` exposes list/export/correlation/by-id | Audit deliberately outside retention |
| Insight lifecycle | `backend/data/insight.py` and `backend/data/insight_interactions.py` have **no delete surface**; both raise `NotImplementedError` stating retention/deletion is deferred to I7 (PO Q12) | Explicit deferral, verified in code |
| Evidence lifecycle | `backend/data/evidence_line_items.py` documents “**no retention / soft-delete / purge / anonymisation** mechanism exists” (B2-D11) | Explicit non-implementation |
| Customer export | `backend/api/v3_exports.py`: `/api/v3/exports/emissions.csv`, `/emissions.json`, `/documents.csv`, **`/audit-package.json`** over `backend/data/exports.py` | An E4-shaped export surface already exists |
| Backup/recovery | `tools/backup_recovery_drill.py` + `docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md` | Drill tooling exists; the record is a document, not an automated gate |

## 6.2 What is missing (verified absences)

| Missing capability | Evidence of absence | Consequence |
| --- | --- | --- |
| Enforcement of `audit_log_retention_days` | Not in `_ELIGIBLE_DOMAINS`; no code reference outside `data/settings.py` | The configured value is stored and surfaced but **has no effect** — it must not be presented as an active control |
| Enforcement of `data_retention_days`, `backup_retention_days` | Same: configured columns with no enforcer | Same truthfulness risk |
| Legal hold | Repository-wide search finds **no** `legal_hold` or hold semantics | A preservation order cannot be honoured today → **PO DECISION REQUIRED** |
| Organisation / account deletion | No organisation-deletion service, API or job found; `insight`/`insight_interactions` explicitly have no delete surface | A departing customer cannot be handled end to end → **PO DECISION REQUIRED** |
| Storage-object deletion propagation | `organization_files` / `report_artefacts` store `bucket` + object keys, but no object-delete path was found (only `data/suppliers.py::remove`, the unused `data/audit.py::delete`, and repository `delete` stubs) | Soft-deleted rows can leave live Storage objects → **PO DECISION REQUIRED** (and an explicit authorization, since it touches Storage) |
| Insight ledger retention | `data/insight.py` / `data/insight_interactions.py` raise on delete | Questions and answers are retained indefinitely by construction |
| Provider / privacy retention | No provider-retention surface found; `docs/legal/CARBONTALLY_THIRD_PARTY_PROCESSOR_REGISTER.md` exists as a register and provider use is configuration-gated (`CARBONTALLY_AI_*`) | **PO DECISION REQUIRED** — whether prompts/tool payloads are transmitted, for how long, to whom |
| Hard purge / anonymisation | Explicitly absent (soft-delete convention only) | **PO DECISION REQUIRED** — whether hard deletion is ever required |
| Backup/restore targets | `backup_retention_days` exists unenforced; a drill tool exists; **no RTO/RPO values** anywhere in the repository | **PO DECISION REQUIRED** (RTO/RPO), then plan accordingly |

## 6.3 L7 implications (INFERENCE from verified facts)

1. Retention is **soft-delete only** and audit/evidence is never purged, so the platform favours auditability over erasure. That is defensible for an audit-oriented product but **cannot satisfy an erasure request** unless the PO decides how those obligations rank.
2. Three of the five configured retention domains are **unenforced**; a settings surface listing them could imply a compliance posture that does not exist. Either enforcement or an explicit “configured but not enforced” presentation is needed before any customer-facing claim.
3. Storage objects sit outside the database soft-delete boundary, so today's only deletion path is partial.

## 6.4 L7 work that needs no PO decision

Extending enforcement to PO-configured domains using the **existing** soft-delete pattern, surfacing an explicit enforced/not-enforced state, and unifying partial deletion for the file bucket are engineering tasks over existing structures. **Durations, legal hold, erasure scope, export scope and backup/recovery targets are all PO DECISION REQUIRED** — this preflight invents none of them.

---

# 7. L8-A — technical resilience / security / operations

**Headline: substantial Phase 8-X delivery already exists; the residual gaps are operational *policy* (SLO, incident, alerting configuration) rather than missing mechanisms.**

| Area | Verified state | Residual gap |
| --- | --- | --- |
| Rate limiting / concurrency | **CLOSED under INS-01** — PostgreSQL-backed buckets + leases, live-verified 30/30, enforced on both execution routes | none (do not duplicate) |
| Health checks | `GET /health`, `backend/main.py:322` — probes Supabase connectivity **and** the DB pool independently and reports `healthy`/`degraded` (X1-M2 required the real data path) | No readiness/liveness split; no dependency-degradation matrix |
| API runtime metrics | `backend/services/api_metrics.py`, `backend/data/api_metrics.py`, `backend/domain/api_metrics.py` (5-minute flush, rolling 60-minute window, `prune_slots`), registered at `backend/main.py:274-288`; tests `tests/unit/services/test_api_metrics_x7.py` and `tests/integration/test_api_metrics_x7_runtime.py` | The X7 contract record still says BLOCKED (§3.1); no external APM/monitoring integration found |
| Operational alerting | `backend/services/operational_alerting.py` + `tests/integration/test_operational_alerting_x2_runtime.py`; notification and delivery stores in `backend/data/notifications.py` (`prune_operational_alerts_before`) | The X2 contract record says BLOCKED; the contract's named config columns (`sla_breach_alert_enabled`, `sla_breach_alert_recipients`, `sla_default_hours`) have **no code references** → the live configuration surface must be inspected, and thresholds/recipients are **PO DECISION REQUIRED** (PX-6 forbade inventing them) |
| Observability | Structured logging across services, the canonical append-only `audit_trail`, ops surfaces (`/ops/operational-health` in the frontend), the X5 ops-console contract | No SLO-bound dashboards or alerting policy document found |
| Auditability | `audit_trail` append-only (`data/audit.py`), `api/admin_audit.py` list/export/correlation/by-id, `AuditRepository.export_csv` | none |
| Backup / recovery | `tools/backup_recovery_drill.py`; `docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md` | No RTO/RPO targets and no restored-verification cadence → **PO DECISION REQUIRED** |
| Incident handling | Incident provenance exists only inside tests: Render OOM 512 MiB (2026-09-17→19) in `tests/integration/test_pdf_ocr_memory_runtime.py`; `backend/pdf_engine.py:49` references F-070-D | **No incident-response runbook** in `docs/operations/`; severity/on-call/communication policy is **PO DECISION REQUIRED** |
| Deployment discipline | `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`, `docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md`, `.github/workflows/migration-drift.yml`, `frontend/vercel.json`, root `vercel.json` | Production deployment remains **NOT AUTHORIZED** (G0-D) |
| Operational configuration / secrets | 127 `os.getenv` call sites; provider access configuration-gated (`CARBONTALLY_AI_BASE_URL/API_KEY/MODEL`); no tracked `.env` | No secrets-management policy (ownership/rotation) → **PO DECISION REQUIRED** |
| Error handling | Fail-closed tool errors, bounded provider retries (`MAX_PROVIDER_ATTEMPTS = 2`), truthful answer states | No error-budget/circuit-breaker policy |
| SLO/SLA surfaces | SLA columns/tables are referenced by the X2 contract (`system_settings.sla_default_hours`, `sla_definitions`) but **no code references were found**, and `sla_definitions` had 0 rows at audit time | **PO DECISION REQUIRED** — committed SLO/SLA targets are a commercial commitment (§8) |

**L8-A conclusion:** the mechanisms are largely present; what remains is a **governance layer** (SLO targets, alert thresholds/recipients, incident runbook, secrets policy, restore cadence) that an implementer must not invent.

---

# 8. L8-B — commercial / billing

**Headline: a real, configurable commercial *data model* and admin/user API exist; there is no payment-provider integration and no production billing, and the commercial stage is not authorized.**

## 8.1 What exists (verified code, not inference)

| Layer | Verified artefacts |
| --- | --- |
| Domain | `backend/domain/billing.py`: `BillingPlan`, `CommercialConfig`, `CreditLedgerEntry`, `Subscription`, `BillingOrder`, `StorageUsage`, `PaymentRecord`, `IdempotencyKey` |
| Repositories | `backend/data/billing.py`: `BillingPlansRepository` (versioning: `publish_new_version`, `history`, `get_current_by_code`, `get_version`), `BillingCommercialConfigRepository` (`get_default_billing_mode`, `update_version`), `BillingCreditLedgerRepository` (`record`, `balance`, `list_for_org`), `SubscriptionsRepository` (`get_active_for_org`, `upsert_active`, `update_status`), `BillingOrdersRepository` (`create`, `update_status`, `mark_approved`, `mark_completed`), `StorageUsageRepository`, plus payment / idempotency / usage repositories |
| API | `backend/api/v3_billing.py`: `GET /me`, `GET /me/credits`, `GET /me/orders`, `GET /me/orders/{id}`, `GET /me/payments`, `POST /me/storage/refresh`, `POST /orders/assisted`, `POST /orders/{id}/approve`, `POST /orders/{id}/cancel`, `POST /managed/orders` |
| Migrations | `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql`, `supabase/migrations/20260824030000_d37_master_commercial_billing.sql` |
| Frontend | `frontend/src/v3/customer/BillingPage.jsx`; public `/pricing` and `/billing` routes |
| Commercial design records | `docs/business/` (commercial viability report, assisted/managed processing specification, direct-merchant commercial architecture) and `docs/Pricing/` (comparison baseline, unit economics, draft pricing strategy) |

**Existing code is not production billing.** The order flow is *assisted/managed* (an operator approves), and payment is represented by a `PaymentRecord` intent/confirmation rather than a settled transaction.

## 8.2 What is missing (verified absences)

| Missing | Evidence |
| --- | --- |
| Payment-service-provider integration | No Stripe/PayPal/Gocardless/Adyen/Paddle SDK or client anywhere in `backend/` or `frontend/src/` (search returned only column-naming comments) |
| Webhooks / event ingestion | No provider webhook route or signature-verification code found |
| Invoice generation / delivery | No invoice artefact or billing-document generator found (report artefacts are a separate concern) |
| Automated dunning / billing-failure handling | No retry/suspension automation found; `Subscription.update_status` is operator-driven |
| Refunds | No refund API or flow found |
| Overage metering and charging | `StorageUsageRepository` exists; no overage charge path found — and X2 explicitly keeps commercial usage metering unauthorized |
| Entitlement enforcement | No plan-entitlement gate was found on feature routes; the only limit currently enforced is the INS-01 **technical** rate limiter, which is explicitly not an entitlement |
| Tax / VAT handling | None found |
| Commercial SLO/DR commitments | None (§7) |

## 8.3 The separation this preflight insists on

* **Existing code (verified):** billing domain, repositories, admin/user billing API, two D37 migrations, billing UI, commercial design records.
* **Production-ready commercial capability: absent** — no PSP, no invoicing, no dunning, no refunds, no entitlements, no tax, no committed SLO.
* **PO DECISION REQUIRED** (§12): payment provider, billing model, plan/price catalogue, entitlement semantics, overage handling, refunds/credits policy, invoicing/tax, commercial usage metering, and whether the assisted/managed flow is the permanent model or a stopgap.

**Do not infer that the existence of subscription/plan/credit tables constitutes a production billing system** — that inference is rejected here explicitly.

---

# 9. Investor-demo readiness assessment

This is **not** a production-release authorization. It separates **demo-critical** from **production-critical** from **nice-to-have**, using only verified repository evidence.

## 9.1 Demo infrastructure that exists (verified)

| Asset | Verified state |
| --- | --- |
| Demo lab | `tools/demo_lab/` — `lab.py`, `lab_env.py`, `provision.py`, `stack.py`, `storage.py`, `verify.py`, `manifest.json`, `seed_factors.py`, `t3_scenarios.py`, `t3_extract_probe.py`, `t3_manifest.json`, `run_demo_lab.sh`, `reset_demo_lab.sh`, `backend.env.example` |
| Repeatability / reset | `run_demo_lab.sh` (stack + provision + verify; optional `--backend`, `--factors`) and `reset_demo_lab.sh` (removes the lab DB, containers and lab auth users; `--purge-state` also clears local credentials/evidence). The README states every step is **idempotent** and that the developer's Supabase stack and the **investor demo dataset are never reseeded, truncated or altered** |
| Identities | `tools/demo_lab/manifest.json` (keys: `lab`, `namespace`, `email_domain`, `comment`, `organizations`, `processing_entities`, `consultant_firm`, `actors`) — real role-bearing identities so the application resolves each actor's entity/role |
| Document corpus | `tools/generate_synthetic_documents.py`, `tools/carbon_data_factory/`, and the T3 harness with a curated corpus id (`t3-uk-curated-v1`) plus an acceptance probe (`_accepts`, `select_candidate`) that *decides whether a document is acceptable* rather than forcing success |
| OCR provisioning | `tools/provision_tesseract_local.sh`; OCR failure modes are documented in code (`backend/pdf_engine.py`), with the Render memory incident captured in `tests/integration/test_pdf_ocr_memory_runtime.py` |
| Verification records | `docs/demo-investor/DR-001…DR-007` (customer journey, frontend runtime/browser, CORS/browser, deep browser, remaining investor workflow, report refresh, defect triage) |
| QA harness (independent) | `qa_harness/` with `scripts/{preflight,run_api,run_db,run_browser,run_agents,run_all,audit_openapi_bindings,reclassify}.py`; the README marks it **BUILD-ONLY** — it must not be run against the application until a checkpoint is authorized |
| Collateral | `docs/Pricing/`, `docs/business/`, `docs/legal/` (risk register, policy consistency audit, processor register), `docs/operations/` |
| Topology artefacts | root `vercel.json`, `frontend/vercel.json`, `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` |

**Boundary respected:** `carbon_tally_synthetic_documents_generator` is external/offline/pinned. `tools/generate_synthetic_documents.py` and `tools/demo_lab/t3_scenarios.py` were **read only**; nothing was fetched, vendored or modified.

## 9.2 Must work (demo-critical)

| Capability | Verified state | Blocking risk |
| --- | --- | --- |
| Authentication | Supabase Auth; `/login`, `/signup`, `/auth/callback`, `/auth/magic`, `/beta-login`; TOTP MFA architected | none observed |
| Customer workspace | `frontend/src/v3/customer/*` with `/dashboard/*`, `/documents`, `/emissions`, `/reports`, `/issues`, `/messaging` routes | none observed |
| Upload → extraction → mapping → calculation | `services/automatic_extraction.py`, `services/ai_document_extraction.py`, `engines/{matching_stages,calculation,validation}.py`, processing + review queues | OCR environment dependency (Tesseract provisioning) |
| Deterministic calculation | `engines/calculation.py` with `RESULT_PRECISION`, immutable `calculation_snapshots` | none observed |
| Evidence trace | `evidence_line_items` + `/evidence/line-items/{lineItemId}` + `SourceEvidenceViewer.jsx` + DM-6 depth gating | none observed |
| Report | `engines/reporting`, `report_versions`, `report_version_artifacts`, `/reports`, `/reports/:id` | report-artefact bucket provisioning is a documented operational prerequisite |
| Insight (family 1) | `/insight`, `InsightPage.jsx`, `InsightInteraction.jsx`, `InsightAnswerState.jsx`, `InsightReferences.jsx` | none observed |
| Bounded discovery / aggregation / provenance | INS-01 closed + OHD-verified (75/75 schema, 30/30 concurrency) | none observed |
| Source Evidence Viewer separation | confirmed core capability (PO closure §7) | none observed |
| Security / tenant isolation | I2 boundary, RLS suites (live tests exist), consultant/PE/internal boundaries | live RLS verification needs a database (skipped in unit runs) |
| Meaningful failure states | fifteen I4 answer states including `no_data`, `zero`, `multiple_matches`, `rate_limited`, `provider_unavailable`; extraction/validation issue states | none observed |

## 9.3 Must be truthful (demo-critical, non-negotiable)

* no fabricated emissions — the answer path is deterministic and narration is bounded to tool output (verified);
* no invented evidence — the viewer resolves only authoritative line items and re-authorizes; a reference grants nothing;
* no unsupported accounting classifications — Scope 3 categories, market-based Scope 2 and Scope 1 decomposition **do not exist** (§4), so those questions must return an unsupported/no-data state rather than a guess;
* no “AI calculated this” behaviour — narration is suppressed for ambiguous results and the system prompt forbids inventing values, with INS-01 tests asserting the boundary;
* no unsupported audit-certification claims — the append-only ledger and `/audit-package.json` exist but **no certification exists**, and the platform must not claim one;
* no production-readiness claim — the operations records and PO records all state production is unauthorized.

## 9.4 Truthful limitations a demo must narrate, not hide

1. **Supplier analytics return `no_data`** — no write path populates `emissions_logs.supplier_id` (§4 family 9, INS-01 §11, OHD §18).
2. **Scope 3 / market-based Scope 2 / Scope 1 decomposition / variance / temporal comparison** are unimplemented → `unsupported`.
3. **Two retention domains are unenforced** and several lifecycle operations are absent (§6) — the demo must not imply erasure or legal-hold capability.
4. **A curated corpus legitimately contains documents that fail or need manual review**; the principle “a truthful demo is preferable to a fabricated successful result” applies to extraction as well as to Insight.

## 9.5 Nice-to-have (demo polish) versus production-critical

* **Nice-to-have:** navigation/dashboard/visual consistency, empty/loading/error-state polish, demo-data richness, a repeatable demo script — the v3 shell already provides tokens, components, `DataTable`, `StateViews`, `Alert` and the full route surface.
* **Production-critical (never justified by demo needs alone):** live RLS verification on a real database, OCR capacity (512 MiB Render OOM incident), deploy-time migration-drift gating, backup/restore cadence, secrets policy, SLO/alerting configuration, complete L7 lifecycle, billing/PSP, environment promotion gates.

**Risk to control explicitly:** demo polish expanding into production work. Presentation-only changes must be bounded as such, and the investor-demo gate (§17) must not be read as production authorization.

---

# 10. Implementation dependency graph

Derived from §4 (what each family needs) plus the v2 roadmap (§18) and the repository's actual prerequisites. Arrows mean “must exist first”.

```
INS-01 FOUNDATION (closed, verified)
  ├── Identified Calculation / Discovery / Aggregation / Aggregate Provenance / Rate limiting
  │
  ├─(A) NO NEW TAXONOMY NEEDED ──────────────────────────────────────────────
  │    • Capability Coverage Matrix (planning artifact, PO-announced next gate)
  │    • Temporal Comparison (family 11)   ← needs only comparison semantics
  │    • Data-Quality exposure (family 14) ← reuses issues/queue/completeness
  │    • Audit/reproducibility contract (family 16, E4) ← reuses audit + viewer
  │    • Reporting/disclosure assistance (family 18) ← reuses the report engine
  │
  ├─(B) BLOCKED ON ACCOUNTING TAXONOMY DECISIONS ─────────────────────────────
  │    Supplier persistence (family 9) → supplier intelligence / variance
  │    Scope 3 taxonomy (family 6) → Scope 3 analytics → Scope 3 reporting
  │    Scope 2 method dimension (family 7) → market-based totals → dual reporting
  │    Scope 1 decomposition (family 8)
  │    Primary/secondary provenance (family 13 extension) → factor history
  │    Methodology & boundary model (family 15)
  │
  (A) + (B) converge → Variance / Attribution (family 12)
        ← needs a stable taxonomy AND a defined comparison basis AND restatement rules
  │
  Knowledge layer (family 17) is INDEPENDENT of (A)/(B) but needs content governance
  Decision / Reduction intelligence (family 19) needs variance + taxonomy + knowledge
  │
  L7   — partially independent: enforcement/erasure/export need PO values, not Insight
  L8-A — independent: SLO/incident/alerting policy, secrets, restore cadence
  L8-B — independent of Insight: commercial decisions + PSP choice
  ↓
  INVESTOR-DEMO GATE — needs only (A)-level capability + polish + truthful limitation handling
```

**Verified dependency facts that constrain this graph**

1. **Aggregate → evidence hardening is a prerequisite for honest variance.** `insight_aggregate_provenance` exists and is bounded at 100, so a causal statement can name its contributing snapshots — this prerequisite is already satisfied.
2. **Variance cannot precede taxonomy AND comparison.** Attribution needs a stable dimension to decompose along (Scope 3 category, Scope 1 class, primary/secondary, Scope 2 method) and a defined comparison basis. Neither exists today.
3. **Supplier analytics cannot precede supplier persistence** — the dimension is structurally present but permanently empty until a write path or backfill is authorized (§4 family 9).
4. **Factor-change attribution cannot precede factor-history retention** — the snapshot preserves the factor *used*, not a candidate/stage history (§4 family 13).
5. **L7 and Insight have exactly one coupling:** Insight ledger retention is explicitly deferred to L7 (`data/insight.py` and `data/insight_interactions.py` both raise `NotImplementedError` citing I7/Q12), so a retention package must cover the Insight ledgers or state why it does not.
6. **The investor-demo gate does not depend on L7 or L8-B.** It depends on (A)-level capability plus truthful state handling; L7/L8-A matter only where a demo promises lifecycle or operational guarantees.
7. **The Capability Coverage Matrix is a planning artifact, not an implementation dependency** — but the PO has named it the next gate, and the package boundaries in §11 assume its question→family mapping is ratified.

---

# 11. Proposed bounded implementation packages

Each package below is **independently authorizable**. **None is authorized by this document.** Complexity is indicative (S/M/L); every package carries its own Cline → OHD → PO gate.

`DB` = database impact · `API` = API impact · `PoD` = PO decisions required · `CX` = complexity · `D` = demo relevance · `P` = production relevance.

| ID | Package | Objective (bounded) | Prerequisites | DB | API | PoD | Exclusions | CX | D | P |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **P1** | Capability Coverage Matrix (planning) | Produce the PO-announced matrix: Question → Family → engine → data → evidence depth → answer state → implementation → verification → dependencies → authorization | none | none | none | none | no code/schema/capability claims | S | indirect | low |
| **P2** | Temporal Comparison (family 11) | Bounded two-period comparison (absolute + percentage) per allowlisted dimension on kg CO₂e, with provenance | INS-01; **D-11** | none | **I3 catalogue change + migration** (tool-name CHECK) | D-11 | attribution/causes, restatement | M | **HIGH** | HIGH |
| **P3** | Data-Quality + Audit/Reproducibility exposure (families 14, 16) | Deterministic quality summary (unmapped/unresolved/blocked/incomplete) plus a “reproduce this number” chain ending at the existing viewer | **D-14**, **D-16** | none | I3 catalogue change + migration | D-14, D-16 | sampling/anomaly detection, certification claims, new evidence store | M | **HIGH** | HIGH |
| **P4** | L7 lifecycle (enforcement, erasure, export) | Make retention truthful: enforce PO-approved domains on the existing soft-delete pattern, surface enforced/not-enforced, implement approved erasure/export scope incl. Storage propagation | **D-01…D-07** | possible (legal hold / deletion ledger) | settings + export surfaces | D-01…D-07 | policy values, regulatory claims, unapproved Storage surgery | L | MEDIUM | HIGH |
| **P5** | L8-A operational governance | SLO targets, alert thresholds/recipients via the existing settings surface, incident runbook, secrets policy, restore cadence | **D-08…D-12** | none expected | none expected | D-08…D-12 | invented thresholds, new infrastructure | M | LOW | HIGH |
| **P6** | Supplier persistence (family 9) | Populate `emissions_logs.supplier_id` at a PO-approved capture point with approved confidence/approval and backfill policy | **D-09** | none (column exists) unless a backfill ledger is required | none | D-09 | inferred suppliers, LLM assignment, invented confidence | M–L | **HIGH** | HIGH |
| **P7** | Scope 3 Category taxonomy (family 6) | Versioned GHG-Protocol-baseline taxonomy, deterministic assignment, storage, category aggregation/reporting | **D-13** | **HIGH** (versioned taxonomy + references) | new dimension/filters | D-13 | market-based Scope 2, Scope 1 decomposition, primary/secondary, invented semantics | L | MED–HIGH | HIGH |
| **P8** | Scope 2 market-based (P8a) + Scope 1 decomposition (P8b) | Method dimension with instrument/residual-mix handling; Scope 1 stationary/mobile/fugitive/process | **D-10, D-15**; versioning pattern proven in P7 | **HIGH** | new dimensions/filters | D-10, D-15 | invented instrument-quality rules, unchosen residual-mix source | L (split) | **HIGH** | HIGH |
| **P9** | Variance / Attribution (family 12) | Deterministic decomposition of period-to-period change into approved components, with provenance | P2, P7/P8 stability, **D-12** | possible | I3 catalogue change + migration | D-12 | causal narrative, LLM-generated causes | L | **HIGH** | HIGH |
| **P10** | Knowledge (17) / Reporting assistance (18) / Decision intelligence (19) | Three separable packages: governed standards knowledge with citations; obligation-aware reporting assistance; reduction/scenario intelligence | **D-17, D-18, D-19**; (19) also P9 | depends | separate I3 changes | D-17…D-19 | certification claims, untraceable recommendations | L each | MED | MED–HIGH |
| **P11** | L8-B commercial billing | Either a real billing capability (PSP, webhooks, invoicing, dunning, refunds, entitlements, tax) or formally adopt assisted/managed as permanent | **D-20…D-26** | **EXTREME** risk surface (money) | webhook + billing routes | D-20…D-26 | invented prices/plans/refunds/tax; implementer-chosen PSP | L+ | LOW | HIGH |
| **P12** | Investor-demo readiness gate (delivery) | Repeatable, truthful demo using `tools/demo_lab` + T3 harness: scripted path, pre-demo verification, explicit truthful-limitation script | none outstanding for (A)-level capability; re-check DR-001…DR-007 | none | none | none | production deployment, investor-dataset reseed, fabricated success, synthetic-generator changes | M | **CRITICAL** | LOW |

**Per-package repository areas, security/evidence impact, tests and OHD focus**

| ID | Repository areas | Security impact | Evidence impact | Tests / OHD acceptance focus |
| --- | --- | --- | --- | --- |
| P1 | `docs/architecture/` only | none | none | every row cites code; no family claimed without engine + evidence path |
| P2 | `domain/insight_query.py`, `services/{insight_query_planner,insight_tools}.py`, `data/emissions_logs.py`, `frontend/src/v3/insight/*` | both periods org-authorised | E1/E2 (+E3 via the existing provenance tool) | two-period correctness, ordering, zero-basis percentage, tenant negatives, migration assertion; no narrated causality |
| P3 | `data/{issues,review_queue,disclosure_projection,emissions_logs}.py`, `services/insight_tools.py`, `frontend/src/v3/insight/*` | org-scoped, no raw content | E2/E3 (E4 only as the PO defines) | counts vs fixtures, tenant negatives, no-raw-content, chain resolution |
| P4 | `services/retention.py`, `data/{settings,organization_files,insight,insight_interactions}.py`, `api/{v3_settings,v3_exports}.py`, `tools/enforce_retention.py`, ops runbook | **HIGH** — irreversible erasure, audited | the never-purge invariant must survive | dry-run vs apply, configured vs unconfigured, invariants, propagation, isolation |
| P5 | `docs/operations/*` plus configuration of `services/{operational_alerting,api_metrics}.py` | secrets policy, alert recipients | telemetry retention already bounded (X2/PX-7) | thresholds from configuration, metrics read surface, drill execution |
| P6 | log write path (`data/emissions_logs.py`), extraction mapping, `data/suppliers.py` | organisation-owned identities | supplier provenance must be authoritative | write-path persistence, idempotent backfill, aggregation with data, isolation |
| P7 | new domain module + migration, mapping/validation engines, snapshot/log dimension, reporting/disclosure | taxonomy immutable once used | category provenance joins the snapshot chain | versioning, assignment determinism, historical stability, reporting totals |
| P8 | calculation engine (method-aware factors), instrument/decomposition storage, reporting/disclosure, Insight dimensions | instruments are evidence-bearing (viewer + DM-6) | instrument/document provenance required | method resolution, dual totals, decomposition totals, evidence linkage |
| P9 | new domain/service + Insight tool (+ possible snapshot-history migration) | unchanged (org-scoped reads) | every component traced to snapshots | decomposition determinism, restatement handling, provenance |
| P10 | knowledge store/projection, reporting engines, scenario model | knowledge must never blend into customer data | citations, E1–E3 discipline | citation integrity, no fabricated customer facts, traceability |
| P11 | `domain/billing.py`, `data/billing.py`, `api/v3_billing.py`, migrations, `frontend/src/v3/customer/BillingPage.jsx` | webhook security, idempotency, isolation, PCI-scope avoidance | payment records must be authoritative | webhook signature/idempotency, entitlement enforcement, failure handling, isolation |
| P12 | `tools/demo_lab/*`, `docs/demo-investor/*`, presentation-only polish | none (lab-local) | limitations stated, not hidden | pre-demo verification run; scenario coverage |

**Sequencing recommendation (INFERENCE):** **P1 → P2 → P3 → P12** are unblocked today and together produce visible capability plus a credible demo; **P4/P5** are unblocked only by PO values; **P6–P11** each require a taxonomy or commercial decision first. High-risk domains (taxonomy redesign, L7 lifecycle, commercial billing, production deployment) are deliberately **not** combined in any package.

---

# 12. PO decisions required before implementation

Nothing in the “options” column is a recommendation unless labelled; where a decision already exists it is cited. **Cline may not decide any row in this table.**

## 12.1 L7 / data lifecycle

| Decision ID | Topic | Why required | Options / questions | Cline may not decide |
| --- | --- | --- | --- | --- |
| **D-01** | Retention durations per domain | `document_retention_days` and `operational_telemetry_retention_days` are enforced; `audit_log_retention_days`, `data_retention_days`, `backup_retention_days` are configured but **unenforced** (`services/retention.py::_ELIGIBLE_DOMAINS`) | Which domains become enforced? What duration for each (or “not enforced by design”)? Does the audit-log domain stay outside retention permanently? | any duration |
| **D-02** | Deletion semantics | Soft-delete is the only convention in use (`deleted_at`); no hard purge or anonymisation exists | Is hard deletion ever required? Is anonymisation required instead? What is the customer-visible effect of a soft-deleted document? | any deletion mode |
| **D-03** | Legal hold | No hold semantics exist anywhere in the repository | Is legal hold in scope at all? If yes: who may place/release a hold, what does it override, how is it surfaced? | existence, authority, semantics |
| **D-04** | Erasure scope (organisation / account deletion) | No organisation-deletion path exists; `insight`/`insight_interactions` have no delete surface | What must be erased on customer exit? What must be retained for audit/statutory reasons? What happens to reports, snapshots, evidence and audit rows? | erasure scope and its limits |
| **D-05** | Storage-object propagation | `organization_files`/`report_artefacts` reference buckets/objects; no object-delete path found | Must storage objects follow the database soft-delete? On what trigger, with what audit record and what signed-URL implications? | propagation policy |
| **D-06** | Export scope | `api/v3_exports.py` already exposes emissions CSV/JSON, documents CSV and an `audit-package.json` | Is the current export set the complete customer-facing export, or is a formal “export on request” scope required (incl. Insight ledgers, evidence, audit)? | export scope |
| **D-07** | Provider / privacy retention | Provider use is configuration-gated; no provider-retention surface exists; `docs/legal/CARBONTALLY_THIRD_PARTY_PROCESSOR_REGISTER.md` is a register, not a policy | Are prompts/tool payloads transmitted at all in production? For how long, to whom, under what processor terms? Is narration retention different from interaction retention? | any provider/privacy retention rule |
| **D-08** | Backup retention + RTO/RPO | `backup_retention_days` is unenforced; a drill tool exists; no RTO/RPO values exist | What are the committed RTO/RPO? What backup cadence and retention? What restore-verification cadence must be evidenced? | any RTO/RPO or cadence |

## 12.2 Accounting taxonomy / capability policy

| Decision ID | Topic | Why required | Options / questions | Cline may not decide |
| --- | --- | --- | --- | --- |
| **D-09** | Supplier persistence | `emissions_logs.supplier_id` is never written (INS-01 §11, OHD §18) | At what point is supplier captured authoritatively (extraction mapping, manual review, customer entry)? What confidence/approval rule applies? Is historical backfill permitted, and from where? | capture point, confidence, backfill |
| **D-10** | Scope 2 market-based methodology | Only a disclosure vocabulary exists (`SCOPE2_METHODS`, `scope2_method_hint`) | Which instruments qualify? What residual-mix source/version? How are location-based and market-based reported together? How is a changed instrument handled historically? | instrument quality, residual mix, dual reporting |
| **D-11** | Temporal comparison semantics | No comparison capability exists; a comparison must define its basis | Are periods the reporting period or the calendar period? How are restatements and partial periods handled? Is percentage change computed on the aggregate or per dimension? | comparison basis |
| **D-12** | Variance / attribution methodology | No attribution engine exists | Which components may be attributed (activity, factor, methodology, boundary, data availability, restatement)? In what order? What is the residual/unexplained policy? | attribution methodology |
| **D-13** | Scope 3 taxonomy + factor-history retention | No Scope 3 category dimension exists; the snapshot preserves the factor used but not candidate/stage history | Which taxonomy version(s)? What assignment rule and who approves it? What historical category semantics apply to already-calculated data? Which extra factor metadata must be retained at calculation time? | taxonomy, assignment, factor-history retention |
| **D-14** | Authoritative data-quality signals | Two unrelated `completeness_score` notions exist (organisation profile vs extraction) plus validation issues and queues | Which signals are authoritative for customer-facing quality reporting, and how are they named? Is the organisation-profile score in scope at all? | signal selection and naming |
| **D-15** | Scope 1 decomposition | No classification exists | Which decomposition classes are required (stationary/mobile/fugitive/process or other)? Applied where (snapshot, log, factor, activity)? | decomposition model |
| **D-16** | Audit package (E4) definition | `audit-package.json` exists but no contract defines its content | What must an E4 package include (calculation, factor, evidence, approval, methodology, version)? Who may obtain it? Export or on-screen surface? | package content and audience |
| **D-17** | Knowledge-source governance (Mode E) | No knowledge layer exists | Which standards sources may be used, under what licence, at which versions, with what citation requirement and review cycle? How is it kept separate from customer data? | sources, licensing, versioning, citations |
| **D-18** | Reporting/disclosure frameworks in scope | Disclosure infrastructure exists (`domain/disclosure.py`, requirement versions) but no obligation mapping for questions | Which frameworks/obligations are in scope, at which versions, and who owns the mapping? | frameworks and versions |
| **D-19** | Decision / reduction methodology | No target/scenario model exists | What target/scenario methodology is acceptable, and what framing may Insight use (no recommendation without a deterministic basis)? | methodology and framing |

## 12.3 Commercial (L8-B) and operations (L8-A)

| Decision ID | Topic | Why required | Options / questions | Cline may not decide |
| --- | --- | --- | --- | --- |
| **D-20** | Payment provider | No PSP integration exists | Which provider (if any), and under what commercial/PCI posture? | provider selection |
| **D-21** | Billing model | The assisted/managed order flow exists; `CommercialConfig.get_default_billing_mode` implies a configurable mode | Is assisted/managed permanent, or is self-service subscription required? What is the invoicing model? | billing model |
| **D-22** | Plans, prices and packaging | Versioned plans exist as data; no price catalogue is authorized | What plans/prices/packaging are authoritative, and where may they be configured (admin plane only)? | plans and prices |
| **D-23** | Entitlements | No entitlement enforcement exists; the only enforced limit is the INS-01 technical rate limiter, explicitly not an entitlement | Which features are plan-gated, and what is the enforcement point (server-side, per organisation)? | entitlements |
| **D-24** | Overage, credits, refunds | Credit ledger and storage usage exist; no overage charge, refund or credit policy exists | How are overages handled? What refund/credit rules apply? Who may issue credits? | all commercial rules |
| **D-25** | Billing failure handling | No dunning automation | What happens on payment failure (grace period, suspension, notification)? | failure policy |
| **D-26** | Commercial SLO/SLA and usage metering | SLA structures referenced by the X2 contract have no code references; commercial usage metering is explicitly unauthorized | What commitments may be published, and what is metered to support them? | commitments and metering |

## 12.4 Repository / record governance

| Decision ID | Topic | Why required | Options / questions | Cline may not decide |
| --- | --- | --- | --- | --- |
| **D-27** | Committing the PO reference documents | Five PO documents plus three `docs/ChatGPT/…` history documents are **untracked**; the INS-01 closure asks for the OHD report to be pushed “together with this PO closure record” | Should the PO closure record and/or the v2 reference, question library and capability matrix be committed, and with what classification? | repository-durability choice |
| **D-28** | Reconciling the X2/X7 contract records | Both records say “IMPLEMENTATION BLOCKED” while implementation, wiring and tests exist | Update the records to the verified code state (and by whom), or treat the implementation as unverified pending re-audit? | record reconciliation |
| **D-29** | Reviewer/SLA pre-existing failures | OHD established three `test_review_sla_surfaces.py` assertions failing at baseline and HEAD | Accept and track as pre-existing, or authorize remediation? | remediation authority |

**Existing decisions cited (not re-opened):** customer-factor self-approval (AGENTS.md §16); consultant operating model (§10–§11); PE boundary (§12); N3 retention configurability and server-side enforcement (§42); INS-01 technical rate limiting thresholds supersede the earlier “I8 thresholds not authorized” wording for **technical** rate limiting only (INS-01 closure §8.7); the never-purge invariant for audit/evidence (code + `services/retention.py` docstring); the technical-vs-commercial separation (INS-01 closure §11).

---

# 13. Security and data-protection considerations

| Area | Verified position | Consideration for the next packages |
| --- | --- | --- |
| Tenant isolation | Org-scoped predicates throughout the Insight analytics SQL; I2 authorization; RLS as the platform layer | Every new dimension (Scope 3 category, supplier, facility, asset, method) must be organisation-owned and versioned immutably once used |
| Customer factor precedence | `factor_kind`/`customer_factor_id` preserved in snapshots; approved customer factors take precedence | Factor-history work must not silently replace an approved customer factor (AGENTS.md §15) |
| Provenance chain | snapshot → source line item → evidence → viewer, with the viewer as the only evidence authority | The audit/reproducibility package must resolve through the viewer, never through a new evidence surface |
| Never-purge invariant | 8 tables explicitly excluded from every retention rule; audit is append-only | Any L7 erasure work must state precisely how it coexists with this invariant — a PO decision, not an implementation convenience |
| Insight ledger | No delete surface; verbatim question/answer retained by construction | Provider/privacy retention (D-07) must account for this store, and any change is a schema + API decision |
| Signed URLs / Storage | Objects referenced by bucket/key; no deletion path | Erasure propagation (D-05) must preserve “authorize before signing” and never log signed URLs |
| Provider boundary | Provider calls are configuration-gated; narration is bounded by tool output; ambiguity suppresses narration | Knowledge-layer work (P10) must not weaken the “LLM never the source of truth” boundary |
| Rate limiting | Closed under INS-01; server-configured with safety ceilings; anti-bypass on both execution routes | Future Insight tools must join the same enforcement path — a new route without the limiter would be a regression |
| Commercial surfaces | The billing API exists and idempotency keys are already modelled | A PSP integration (P11) introduces webhook authentication, replay defence and PCI-scope avoidance — a separate authorization |
| Cross-tenant factor metadata (pre-existing) | `snapshot_count_for_factor()` / `factor_usage_span()` exposure via `GET /api/v3/emissions/factors/{factor_id}` remains separately tracked (INS-01 closure §8.6) | Not reopened here; factor-intelligence work must neither depend on nor worsen it |

**Data-protection position (INFERENCE; no legal conclusion drawn):** the platform currently retains audit, evidence, snapshots and Insight ledgers indefinitely by construction and has no erasure path. That is a **deliberate, PO-visible posture** only if the PO confirms it through D-01…D-07; until then it is an emergent property, and an unenforced retention setting could mislead a customer. This preflight asserts no regulatory requirement.

---

# 14. Accounting and governance considerations

1. **The deterministic core is sound.** Calculation is server-authoritative, snapshots are immutable, unit normalization is central, and factor provenance is preserved. Nothing in §4 suggests the core must change; the gaps are analytical and taxonomic.
2. **The nine MISSING families split into two governance classes** (§4/§10): taxonomy/policy-blocked (Scope 3, Scope 2 market-based, Scope 1 decomposition, variance, boundary/methodology) and exposure-only (temporal comparison, data quality, audit package, reporting assistance). Only the second class can be authorized without new accounting policy.
3. **Do not infer GHG Protocol semantics.** The repository holds a coarse legacy `ghg_protocol_category` and a disclosure vocabulary; neither is a ratified taxonomy. Scope 3 categories, market-based instruments, residual mix and Scope 1 classes must be specified by the PO.
4. **Versioning is the recurring architectural pattern.** Wherever a taxonomy or method is introduced it must be versioned and immutable once referenced by a calculation, and historical calculations must retain the applicable version — already exemplified by `disclosure_requirement_versions` and `report_versions`. This is the single most important design principle for the next phase.
5. **Answer-state honesty is already enforced and must be preserved.** The closed fifteen-state vocabulary, suppressed narration on ambiguity and the `no_data`/`zero` distinction make “no answer” a contract-defined outcome; new capabilities must extend the same discipline rather than adding a parallel mechanism.
6. **No certification may be claimed.** Audit trail, evidence chain and an `audit-package.json` export exist, but no accreditation, assurance opinion or standard certification exists for CarbonTally. Communication must say what the system *can show*, not what it *is certified for*.
7. **Evidence depth must be stated per answer.** The E0–E4 scale (v2 §11) supplies the language; today's families sit at E1–E3, with E4 reserved for a PO-defined package (D-16).

---

# 15. Explicitly non-authorized areas

This preflight does **not** authorize, and does not begin:

* any implementation of the remaining Insight capability families (§4) or any new I3 tool;
* any new database table, column, CHECK widening or migration;
* any L7 retention value, legal hold, erasure, deletion-propagation or export-scope change;
* any L8-A SLO, alert threshold, recipient list, incident or secrets policy;
* any L8-B price, plan, entitlement, overage, refund, credit, invoice, dunning or payment-provider decision or code;
* production deployment, environment promotion or production configuration;
* investor-demo implementation beyond the *assessment* in §9 — in particular, no change to `tools/demo_lab`, the investor dataset, or the external pinned synthetic generator;
* remediation of any INS-01 non-blocking observation (closure §8.1–§8.8) or of the pre-existing defects in §2;
* consultant Insight and auditor direct Insight (still **DEFERRED / NOT AUTHORIZED** per the capability matrix);
* I7 as a stage and I8 as a stage (except that INS-01's technical rate limiter remains closed, as recorded).

**The only change made by this task is the creation of this report.** No application code, migration, test, frontend, configuration or infrastructure file was modified.

---

# 16. Recommended next package

**Recommendation (proposal only — the PO decides):** **P1 — the Insight Capability Coverage Matrix**, immediately followed by **P12 — Investor-Demo Readiness Gate** as the next bounded delivery package, with **P2 (Temporal Comparison)** as the first new-capability package and **P3 (Data-Quality + Audit/Reproducibility)** as its pair.

Rationale, tied to verified evidence:

1. The PO has already named the Capability Coverage Matrix as the next controlled planning task (`…Post-Closure_Reconciliation…` §15), and §4–§5 of this preflight are the evidence base it needs. It is zero-risk (docs only) and unblocks every later package boundary.
2. **P2** and **P3** are the only new-capability packages that require **no accounting-policy decision** (§10 branch A) and they reuse existing engines, tables and the existing viewer. They answer question categories the Question Library plainly contains (YoY/MoM change; completeness/missing data; “what supports this number?”, “can it be reproduced?”).
3. **P12** converts the existing demo lab into a repeatable, truthful demonstration — the closest thing to immediate commercial value, with no schema, API or policy change.
4. **P4/P5** should be scheduled only once D-01…D-08 are answered, because they are irreversible or commitment-bearing.
5. **P6–P11** must not start before their taxonomy/commercial decisions, and each requires separate authorization.

**Explicitly not recommended next:** billing/PSP work (no decisions, extreme risk surface), Scope 3/Scope 2/Scope 1 taxonomy work (policy-blocked), production deployment (unauthorized), or any attempt to remediate the accepted INS-01 observations.

---

# 17. Proposed Cline / OHD acceptance gates

## 17.1 Investor-demo release gate (proposed; NOT production authorization)

**Must work (verified end-to-end on the demo environment, in this order):** authentication (all demo personas) → customer workspace → upload → extraction → mapping → validation → deterministic calculation → evidence trace to source → report → Insight identified-calculation explanation → bounded discovery → bounded aggregation → aggregate provenance → Source Evidence Viewer → tenant/boundary isolation → meaningful failure states (including at least one `no_data`/`unsupported` and one `rate_limited` demonstration).

**Must be truthful:** no fabricated emissions; no invented evidence; no unsupported accounting classification; no “AI calculated this” framing; no audit-certification claim; no production-readiness claim; every presenter claim traceable to a screen the audience can see.

**Should be polished:** navigation, dashboard, visual consistency (D21 tokens), empty/loading/error states, demo data (T3 corpus + seeded factors), and a scripted, repeatable demo flow with a documented reset (`reset_demo_lab.sh`) and a pre-demo verification run (`verify.py`).

**Gate mechanics (proposed):** a pre-demo verification run recorded with Git SHA, database identity and the scenario list; DR-001…DR-007 findings re-checked; a truthful-limitation script reviewed before the demo; and an explicit acknowledgement that passing this gate is **not** production authorization.

## 17.2 Per-package Cline → OHD → PO gate (proposed)

| Stage | Cline does | OHD does | PO does |
| --- | --- | --- | --- |
| Authorize | confirms scope, exclusions and required decisions | — | issues a bounded authorization citing the package ID |
| Preflight (if required) | inspects current code/schema and lists exact touch points | — | — |
| Implement | smallest correct change; adds regression tests; runs unit/API/security suites; states exactly what changed | — | — |
| Verify | freezes a commit and reports limitations | independently reproduces against the frozen commit — including **live database** verification on a **disposable** target (F-046-1), negative tenant tests, and a baseline-vs-HEAD failure comparison | — |
| Close | — | issues PASS / PASS WITH NON-BLOCKING OBSERVATIONS / FAIL with evidence | closes the package or requires remediation; records carry-forward observations |

**Mandatory OHD evidence for any package:** Git SHA at start/end; disposable-database identity and destruction; migration-chain result if schema changed; baseline-vs-HEAD failure sets; ALLOW **and** DENY cases for security-relevant changes; and an explicit statement of anything not exercised.

## 17.3 Standing constraints carried into every future package

* **F-046-1** — the integration harness performs destructive setup; it may only ever target a disposable `ct_*` clone or the dedicated test database, never persistent QA, the investor demo, or production.
* **Investor-demo safety** — the demo dataset is never reseeded, truncated or altered for a test.
* **Never-purge invariant** — audit and evidence tables stay outside retention unless the PO changes it explicitly.
* **No invented policy** — durations, thresholds, plans, prices, taxonomies and legal semantics are always PO decisions.
* **Evidence destination** — the Shared Source Evidence Viewer remains the single evidence destination; no second viewer.
* **Boundary** — the deterministic engine remains the source of truth; the LLM remains an explanation layer.

---

## Appendix A — Verification of this task's own repository impact

| Check | Result |
| --- | --- |
| Files created by this task | `docs/architecture/CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` (this report) — **the only change** |
| Application code / migrations / tests / frontend / configuration / infrastructure modified | **none** |
| Migrations created | **none** |
| Secrets introduced | **none** — no credentials, tokens, signed URLs or keys appear in this report |
| Working tree at end | clean except the pre-existing untracked PO/ChatGPT reference documents and this new report (then committed) |
| Push target | `github/p8-release-reconciled` |
| Note | the local-only OHD commit `f1a7cce` is an ancestor of this report's commit and therefore becomes published by this push, satisfying the PO's documentation-durability requirement for the OHD report; the PO closure record remains untracked pending **D-27** |

**Preflight status: COMPLETE — report produced for PO review. No implementation performed. Awaiting PO authorization of the first bounded package.**
