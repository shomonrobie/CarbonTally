# CarbonTally — PO Insight Capability Coverage Matrix

## 2026-09-22 · Planning / governance artifact

**Status:** MATRIX PRODUCED — **PLANNING ONLY. AUTHORIZES NOTHING.**
**Role:** PO-controlled coverage and planning artifact for CarbonTally Insight and its supporting carbon-accounting capabilities.
**Baseline:** repository `p8-release-reconciled` at `8916f82bb71dd8e3ef3050b4b1185507dd5b14cb` (see §16 for verification detail).
**Companion reports:** `docs/architecture/CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` (forensic preflight), `docs/architecture/CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md` (implementation record for this matrix).

---

# 1. Purpose and status

## 1.1 Purpose

This matrix is the authoritative **coverage and planning** artifact that maps, for every Insight capability family:

**Question → Capability Family → Deterministic engine → Required data → Evidence requirement → Answer state → Current implementation → Verification status → Dependencies → Authorization status**

It exists so that the PO can authorise the next bounded package without re-deriving the capability landscape, and so that no future package can claim coverage that does not exist.

## 1.2 What this document is not

* It is **not** an implementation specification.
* It **does not** authorise any capability, package, migration, API, frontend or deployment.
* It is **not** a Product Owner closure of any capability.
* It is **not** a competitive or certification claim.
* It does **not** convert `APPROVE` / `APPROVED IN PRINCIPLE` entries in the PO Insight Capability Decision Matrix into implementation authorization.

## 1.3 Status vocabulary (used exactly, never interchangeably)

| Term | Meaning used in this matrix |
| --- | --- |
| **EXISTS** | Implemented in repository code and independently verified. |
| **PARTIAL** | A deterministic foundation exists; the complete capability does not. |
| **MISSING** | The capability is not implemented. |
| **PO DECISION REQUIRED** | Engineering cannot responsibly proceed until the PO resolves the accounting / product / governance rule. |
| **NOT AUTHORIZED** | Outside the current authorization boundary, regardless of what code may exist. |
| **DEFERRED** | The PO has deliberately postponed the capability. |
| **ANSWERABLE** | A representative question can currently be answered truthfully. |
| **UNSUPPORTED** | The platform does not currently possess the required deterministic capability. |
| **NO DATA** | The capability exists but the authoritative data required is currently absent. |
| **INFERENCE** | A reasoned conclusion drawn from verified facts; explicitly *not* a repository-established fact. |

---

# 2. Source hierarchy and conflict register

## 2.1 Authority order applied

1. **Actual running behaviour / database state** (not exercised in this documentation task).
2. **Actual API contract** (`backend/api/**`, live OpenAPI).
3. **Current Git source** — `backend/**`, `frontend/src/**`, `supabase/migrations/**`.
4. **Current migrations and tests** — including the live migration-chain and concurrency verification recorded by OHD.
5. **Ratified PO decisions** — `CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md`, `CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`.
6. **Frozen UX/design architecture** — the D-series decisions.
7. **Product references** — `CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`, `CarbonTally_Insight_Question_Library_2026-09-22.md`.
8. **Forensic preflight** — `CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md`.

Where code and a PO record disagree, **code establishes what is implemented**; a PO record establishes **what is authorized and what the product intends**. Neither is allowed to override the other silently — see §2.3.

## 2.2 INS-01 precedence rule

The PO Insight Capability Decision Matrix (source 5) **predates INS-01**. The INS-01 post-closure reconciliation states this explicitly and requires its statuses to be read together with the closure record:

> “The original PO capability matrix predates INS-01 and therefore contains statuses that must now be interpreted together with this closure record.” — `CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` §6

Therefore, for any capability row within the closed INS-01 scope, **the closure reconciliation supersedes the earlier `NOT IMPLEMENTED` wording**, and this matrix records the closure status.

## 2.3 Conflict register (identified, not silently reconciled)

| # | Conflict | Sources | Authoritative resolution | Residual action |
| --- | --- | --- | --- | --- |
| X-1 | Capability rows C-01, C-02, C-04, C-05, C-14, C-18 read **“NOT IMPLEMENTED”**, while discovery, aggregation (7 dimensions incl. supplier), scope grouping and aggregate→evidence provenance are **implemented and OHD-verified** | PO Capability Decision Matrix §2 vs INS-01 closure §6 and commits `e4ea325` / `f1a7cce` | **Closure record §6 governs** (explicit precedence statement) | Matrix records `CLOSED — FOUNDATION`; no remediation; the earlier matrix is **not** edited (untracked PO document) |
| X-2 | C-14 lists required discovery states as no match / one match / multiple matches / invalid / authz / provider failure; the implemented vocabulary expresses these as `no_data`, `success`, `multiple_matches`, `invalid_input`, `not_authorized`, `provider_unavailable` at the **tool** layer and fifteen states at the **answer** layer | PO Capability Matrix §3.1 vs `backend/domain/insight_tool.py::ToolStatus` + `backend/domain/insight_interaction.py::AnswerStatus` | The two layers are deliberately distinct and both were verified by OHD — **no substantive conflict; a mapping is required** | Mapping documented in §7 |
| X-3 | Aggregation dimensions approved in PO matrix §3.2 are scope, month, year, activity, asset, facility (**no supplier**); the implemented tuple includes **supplier** | PO Capability Matrix §3.2 vs `backend/domain/insight_query.py:85-93` | The INS-01 authorization explicitly included supplier; the closure records **seven** verified dimensions | Recorded; the supplier dimension is structurally present but returns `NO DATA` today (§4 family 9) |
| X-4 | The X2 alerting and X7 API-runtime-metrics **contract records** state “IMPLEMENTATION BLOCKED — PO DECISION REQUIRED”, while `backend/services/operational_alerting.py`, `backend/services/api_metrics.py`, `backend/data/api_metrics.py`, `backend/domain/api_metrics.py` and their tests exist and are wired in `backend/main.py` | Contract documents vs Git source | **Git source governs what exists**; the contract records govern authorization state | `PO DECISION REQUIRED` (**D-28**) to reconcile the records |
| X-5 | `AGENTS.md` §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md`; that file does not exist in this checkout (real demo infra: `tools/demo_lab/manifest.json`) | AGENTS.md vs repository filesystem | Filesystem governs | `PO DECISION REQUIRED` if the constitution text is to be corrected (not authorized here) |
| X-6 | Rate limiting appears as **NOT AUTHORIZED** (SEC-01) in the PO matrix, while INS-01 explicitly authorized and closed technical rate limiting | PO Capability Matrix §2 (SEC-01) vs INS-01 closure §8.7 and §11 | **INS-01 supersedes SEC-01 for technical rate limiting only**; commercial controls remain unauthorized | Recorded; SEC-01 is read as “technical rate limiting: CLOSED; commercial: NOT AUTHORIZED” |

**No conflict in this register has been silently resolved in code, in either PO document, or in this matrix.**

---

# 3. INS-01 verified baseline

**INS-01 status: CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED** (OHD verdict: PASS WITH NON-BLOCKING OBSERVATIONS). Not reopened by this matrix.

## 3.1 Commit record

| Artifact | SHA |
| --- | --- |
| Preflight | `c7cd9cc2ff56e288c830bb5d204118a06aa31104` |
| Implementation | `e4ea3254c6a709df0e9cedcd8c719515363b4358` |
| Implementation + report | `cbc529dd8974d3ec16595fc5c6981c5217b43c24` |
| Independent OHD verification report | `f1a7cce557fbe0d2a8684bf24a6080cf8392df9b` |

## 3.2 The seven authorized tools (closed catalogue — no eighth tool exists or is implied)

| # | Tool name (defined once in `backend/domain/insight_query.py` / `backend/domain/insight_tool.py`) | Kind |
| --- | --- | --- |
| 1 | `report_lookup` | Ratified I3 (pre-INS-01) |
| 2 | `report_version_lookup` | Ratified I3 (pre-INS-01) |
| 3 | `report_evidence_lookup` | Ratified I3 (pre-INS-01) |
| 4 | `calculation_snapshot_lookup` | Ratified I3 (pre-INS-01) |
| 5 | `insight_discovery` | INS-01 — bounded discovery |
| 6 | `insight_aggregation` | INS-01 — bounded aggregation |
| 7 | `insight_aggregate_provenance` | INS-01 — aggregate → calculation provenance |

Each tool has a **closed input schema** and a **declared output allowlist**; dispatch is closed. `ToolStatus` remains the six-value vocabulary (`success`, `no_data`, `not_authorized`, `invalid_input`, `provider_unavailable`, `error`) and reference kinds remain four. Ambiguity is an **I4 answer state**, never a tool status.

## 3.3 Verified bounded contract values (from `backend/domain/insight_query.py`)

| Constant | Value | Meaning |
| --- | --- | --- |
| `MAX_DISCOVERY_RESULTS` | 25 | discovered matches returned |
| `MAX_AGGREGATE_GROUPS` | 50 | aggregation groups returned |
| `MAX_PROVENANCE_SNAPSHOTS` | 100 | provenance snapshots returned |
| `MAX_PERIOD_DAYS` | 3,660 | maximum queryable period |
| `MIN_ACTIVITY_TERM_LENGTH` | 3 | minimum literal activity search term |
| `MAX_TEXT_FILTER_LENGTH` | 128 | maximum literal text filter |
| `MAX_TOLERANCE_KG` / `MAX_TOLERANCE_PERCENT` | `1000000000` / `100` | explicit amount-tolerance ceilings |
| `AGGREGATION_DIMENSIONS` | `scope`, `month`, `year`, `activity`, `supplier`, `facility`, `asset` | closed group-by vocabulary |
| `MAX_TOOL_CALLS_PER_INTERACTION` | 4 (I5 projection) | per-interaction tool-call bound |
| `MAX_QUESTION_LENGTH` / `MAX_IDEMPOTENCY_KEY_LENGTH` | 2,000 / 128 | I4 input bounds |
| `MAX_PROVIDER_ATTEMPTS` | 2 | bounded provider retries |

Exact amount matching uses **zero tolerance**; any tolerance must be explicit. Activity matching is **literal escaped containment** — never wildcard, never fuzzy. Supplier / facility / asset lineage resolves through `EXISTS` over `emissions_logs.snapshot_id = calculation_snapshots.id` (see the accepted defence-in-depth observation, INS-01 closure §8.1 — **not reopened here**).

## 3.4 Verified answer-state vocabulary (fifteen — from `backend/domain/insight_interaction.py::AnswerStatus`)

`success` · `zero` · `no_data` · `not_authorized` · `insufficient_data` · `needs_clarification` · `multiple_matches` · `tool_failure` · `provider_unavailable` · `partial` · `rate_limited` · `refused` · `ungrounded` · `invalid_input` · `error`

Plus the narration states (`NarrationState`): `not_attempted`, `completed`, `unavailable`, `skipped`. Narration is **suppressed for ambiguous results**; ambiguity is never silently resolved to a candidate.

## 3.5 Verified technical rate limiting (closed; security control, not a commercial entitlement)

| Scope | Sustained | Burst | Cap | Max concurrent |
| --- | --- | --- | --- | --- |
| Per user | 20 / minute | 5 | 25 | 2 |
| Per organisation | 100 / minute | 20 | 120 | 10 |

PostgreSQL-backed (no Redis), one atomic statement per transition, `LEASE_SECONDS = 120` with stale-lease recovery, environment-only configuration with server-side safety ceilings (**a client cannot raise them**), enforced on **both** `POST /api/v3/insight/interactions` and `POST /api/v3/insight/tools/invoke` (anti-bypass), returning `429` + `Retry-After`. Concurrency refusals persist `rate_limited` + audit; bucket refusals create no Layer-2 row (anti-flood).

## 3.6 Other verified INS-01 surfaces

* **Query planner** — `backend/services/insight_query_planner.py`: bounded, deterministic, no provider, no SQL, no tenant resolution, no authorization decision in its source.
* **Shared Source Evidence Viewer** — reused unchanged; **no second viewer**, no new route, no new permission, no weakened RLS; the navigation chain runs through the already-authorised reference kinds. Confirmed by the PO as a **core platform capability** (closure §7).
* **Aggregation basis** — kg CO₂e from `emissions_logs.calculated_kg_co2e` only; mixed-unit quantity totals are deliberately **not** exposed; the period total comes from the existing `aggregate()` so a truncated group list can never fabricate a complete total.
* **Verification depth** — OHD applied the migration live inside the real 79-file chain (78 clean; the single unrelated failure is `20260823000000_d32_private_documents_storage.sql` requiring the Supabase Storage schema), achieved 75/75 schema checks, 30/30 live concurrency checks, and proved idempotency across three applications.
* **Pre-existing defects (not attributed to INS-01, not remediated here):** the stale migration-count pin in `backend/tests/unit/data/test_d17_provider_ownership_migration_revision.py`; three `test_review_sla_surfaces.py` assertions; and the separately tracked cross-tenant factor-metadata exposure (`snapshot_count_for_factor()` / `factor_usage_span()` via `GET /api/v3/emissions/factors/{factor_id}` — closure §8.6).

---

# 4. Nineteen-family capability coverage matrix

## 4.0 Summary

| # | Capability family | Status | Evidence depth | Insight exposure today | Accounting decision needed | PO decision IDs | Proposed package | Demo | Prod |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Identified Calculation | **EXISTS** | E3 | 4 ratified tools | no | — | — | HIGH | HIGH |
| 2 | Discovery | **EXISTS** | E2/E3 | `insight_discovery` | no | — | — | HIGH | HIGH |
| 3 | Aggregation | **EXISTS** | E1 | `insight_aggregation` | no | — | — | HIGH | HIGH |
| 4 | Aggregate Provenance | **EXISTS** | E2→E3 | `insight_aggregate_provenance` | no | — | — | HIGH | HIGH |
| 5 | Scope Analysis | **PARTIAL** | E1/E2 | scope grouping only | yes (comparison semantics) | D-11 | P2 | HIGH | HIGH |
| 6 | Scope 3 Categories 1–15 | **MISSING** | none | none | **yes — blocking** | D-13 | P7 | MED–HIGH | HIGH |
| 7 | Scope 2 Methodology | **MISSING** | none (market-based) | none | **yes — blocking** | D-10 | P8a | HIGH | HIGH |
| 8 | Scope 1 Decomposition | **MISSING** | none | none | **yes — blocking** | D-15 | P8b | HIGH | HIGH |
| 9 | Supplier Intelligence | **PARTIAL (NO DATA)** | E1/E2 | supplier dimension → `no_data` | **yes — blocking** | D-09 | P6 | HIGH | HIGH |
| 10 | Facility / Asset Intelligence | **PARTIAL** | E1/E2 | facility/asset dimension + labels | no | — | (fold into P2) | HIGH | HIGH |
| 11 | Temporal Comparison | **MISSING** | E1/E2 (basis exists) | none | yes (basis) | D-11 | P2 | HIGH | HIGH |
| 12 | Variance / Attribution | **MISSING** | none | none | **yes — blocking** | D-12 (+D-13) | P9 | HIGH | HIGH |
| 13 | Emission Factor Intelligence | **PARTIAL** | E2 | factor fields inside `calculation_snapshot_lookup` | yes (history scope) | D-13 | P3 / later | HIGH | HIGH |
| 14 | Data Quality Intelligence | **MISSING** | E1/E2 (signals exist) | none | yes (signal definitions) | D-14 | P3 | HIGH | HIGH |
| 15 | Methodology / Boundary Intelligence | **MISSING** | E1/E2 | none | **yes — blocking** | (no D-ID yet → new) | not sequenced | MED | HIGH |
| 16 | Evidence / Audit Intelligence | **PARTIAL** | E3 / E4 *not* claimed | `report_evidence_lookup` + viewer | yes (E4 scope) | D-16 | P3 | HIGH | HIGH |
| 17 | General Carbon-Accounting Knowledge (Mode E) | **MISSING** | E0 | none | **yes — blocking** | D-17 | P10a | MED | MED–HIGH |
| 18 | Reporting / Disclosure Assistance | **PARTIAL** | E2/E3 | `report_lookup`, `report_version_lookup`, `report_evidence_lookup` | yes (frameworks) | D-18 | P10b | MED | MED–HIGH |
| 19 | Decision / Reduction Intelligence | **MISSING** | none | none | **yes — blocking** | D-19 | P10c | LOW–MED | MED |

**Counts:** EXISTS **4** · PARTIAL **6** (one of which is data-empty) · MISSING **9**. Accounting-decision-blocked: families **6, 7, 8, 9, 12, 15, 17, 19**.

**Per-family detail follows. Each block records every required matrix field.**

## 4.1 Family 1 — Identified Calculation

**Business purpose:** explain a specific, already-calculated emissions figure and let the user reach its evidence.
**Representative questions (QL §24, §28, §33):** “Why is this calculation 2,469 kg CO₂e?”; “What activity, quantity and unit produced this?”; “Which factor was used for this line?”
**Deterministic engine:** `engines/calculation.py` (server-authoritative, `RESULT_PRECISION`); immutable `calculation_snapshots`; lookup via `data/emissions_logs.get_snapshot`.
**Authoritative data:** `public.calculation_snapshots`, `public.emissions_logs`, `public.evidence_line_items`, `public.reports` / `report_versions`.
**Insight exposure:** the four ratified I3 tools — `calculation_snapshot_lookup` (primary), `report_lookup`, `report_version_lookup`, `report_evidence_lookup`.
**Answer states:** `success`, `zero`, `no_data`, `not_authorized`, `invalid_input`, `multiple_matches` (ambiguous identifier), `tool_failure`, `error`; plus `rate_limited` / `refused` at the interaction layer.
**Evidence depth:** **E3** — snapshot → `source_line_item_id` → Shared Source Evidence Viewer.
**Viewer path:** reference (`source_line_item_id`) → `/evidence/line-items/{lineItemId}`.
**Status:** **EXISTS** (verified pre-INS-01; I3/I4/I5/I6 closures).
**Already implemented:** calculation engine; immutable snapshots carrying factor provenance (`factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `factor_set`, `co2e_multiplier`, `methodology`, `algorithm_version`); four tools; viewer handoff.
**Exact missing capability:** none for the single-record case.
**Schema change required:** no. **Accounting-policy decision required:** no.
**PO decision IDs:** C-09 (factor explanation) remains approved-in-principle for *expansion* only; D-13 governs factor-history scope.
**Dependencies:** none beyond INS-01.
**Proposed package:** none outstanding.
**Security / tenant isolation:** organisation-scoped reads; I2 authorization; DM-6 evidence gating; references are locators, never grants.
**Verification requirements:** preserved by regression; any change requires ALLOW **and** DENY tenant tests.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** CLOSED under INS-01.

## 4.2 Family 2 — Discovery

**Business purpose:** find the authoritative calculation(s) matching a bounded, user-specified criterion.
**Representative questions (QL §25, §36, §37):** “Which calculation was ~20,000 kg CO₂e on 2024-02-02?”; “Find the diesel entries in March”; “Show me the records for facility X”.
**Deterministic engine:** `backend/domain/insight_query.py` (closed filter vocabulary + reason codes) + `data/emissions_logs.search_snapshots` / `count_matching_snapshots`.
**Authoritative data:** `calculation_snapshots` + `emissions_logs` (with `EXISTS` lineage to `suppliers` / `facilities` / `assets`).
**Insight exposure:** **`insight_discovery`**.
**Answer states:** `success`, `zero`, `no_data`, `multiple_matches`, `needs_clarification`, `insufficient_data`, `invalid_input`, `not_authorized`, `tool_failure`, `rate_limited`.
**Evidence depth:** E2/E3 (candidate identifiers → evidence lines).
**Viewer path:** discovered snapshot → source line item → viewer.
**Status:** **EXISTS** (INS-01; OHD-verified).
**Already implemented:** seven bounded match dimensions (date/range, amount ± explicit tolerance, activity, scope, supplier, facility, asset, reporting period); literal escaped activity containment; period bound; 25-result bound; deterministic ordering.
**Exact missing capability:** nothing within the authorized discovery contract.
**Schema change required:** no. **Accounting-policy decision required:** no.
**PO decision IDs:** C-14 (discovery) — satisfied by INS-01; D-11 only if comparison-style extensions are later authorized.
**Dependencies:** none beyond INS-01.
**Proposed package:** none outstanding (extensions require separate authorization).
**Security / tenant isolation:** org-scoped predicates; no cross-tenant search; no arbitrary query; no model-generated SQL.
**Verification requirements:** regression of the discovery suite plus tenant negatives.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** CLOSED under INS-01.

## 4.3 Family 3 — Aggregation

**Business purpose:** total authoritative emissions by an approved dimension over a bounded period.
**Representative questions (QL §3, §4, §5, §26):** “What were our emissions in 2025?”; “Emissions by facility in 2024”; “Totals by month”; “Which supplier contributed most?” (see family 9).
**Deterministic engine:** `data/emissions_logs.aggregate_groups` (closed dimension allowlist) plus the existing `aggregate()` for the period total.
**Authoritative data:** `emissions_logs.calculated_kg_co2e` (labels from `facilities` / `assets` / `suppliers`).
**Insight exposure:** **`insight_aggregation`** — dimensions `scope`, `month`, `year`, `activity`, `supplier`, `facility`, `asset`.
**Answer states:** `success`, `zero`, `no_data`, `invalid_input` (unsupported dimension), `not_authorized`, `tool_failure`, `rate_limited`.
**Evidence depth:** **E1** (per-group totals; group→calculation drill-down is family 4).
**Viewer path:** aggregate → family 4 provenance → snapshot → viewer.
**Status:** **EXISTS** (INS-01; OHD-verified).
**Already implemented:** seven dimensions; 50-group bound; truncation-honest totals; kg CO₂e basis only; label lookup through a closed table/key map (INS-01 closure §8.4 — pattern retained).
**Exact missing capability:** dimension *filtering* (e.g. “by facility **within** a scope”); cross-tabulation (explicitly not authorized).
**Schema change required:** no. **Accounting-policy decision required:** no (basis already fixed at kg CO₂e).
**PO decision IDs:** C-01, C-02, C-04, C-05 (previously `NOT IMPLEMENTED`; superseded by closure §6 per §2.2).
**Dependencies:** none beyond INS-01.
**Proposed package:** filtering / cross-tabulation would need a **new** authorization (not sequenced).
**Security / tenant isolation:** org-scoped; no raw source text to the provider; bounded results.
**Verification requirements:** regression of the aggregation suite; tenant negatives; truncation honesty.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** CLOSED under INS-01 (supplier dimension structurally present, currently `NO DATA`).

## 4.4 Family 4 — Aggregate Provenance

**Business purpose:** show which calculations make up an aggregate and provide the path from a total to its evidence.
**Representative questions (QL §28, §29, §34):** “Which calculations make up Scope 1?”; “Which records support this total?”; “Can you prove this number?” (partial — see family 16).
**Deterministic engine:** `data/emissions_logs.list_group_snapshots` / `count_group_snapshots`.
**Authoritative data:** `emissions_logs.snapshot_id` → `calculation_snapshots` (+ evidence lines).
**Insight exposure:** **`insight_aggregate_provenance`**.
**Answer states:** `success`, `no_data`, `invalid_input`, `not_authorized`, `tool_failure`, `rate_limited`; a truncated component list is reported as truncated rather than silently reduced.
**Evidence depth:** **E2 → E3** (bounded component identifiers resolve through the viewer).
**Viewer path:** provenance component → snapshot → source line item → viewer.
**Status:** **EXISTS** (INS-01; OHD-verified).
**Already implemented:** 100-snapshot bound; deterministic ordering; org-scoped; satisfies the PO-matrix requirement that an aggregate intended for assurance use must identify its contributing records (C-18 / capability matrix §3.9) **as a foundation**.
**Exact missing capability:** provenance covers **log-linked** snapshots only (by construction).
**Schema change required:** no. **Accounting-policy decision required:** no.
**PO decision IDs:** C-18 (satisfied as a foundation).
**Dependencies:** family 3.
**Proposed package:** none outstanding.
**Security / tenant isolation:** org-scoped; identifiers are references, not grants.
**Verification requirements:** regression of the provenance suite; tenant negatives; bound assertions.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** CLOSED under INS-01.

## 4.5 Family 5 — Scope Analysis

**Business purpose:** let a user understand emissions by scope and compare scope contributions.
**Representative questions (QL §4, §5, §6, §26):** “What is our Scope 1 vs Scope 2 vs Scope 3 split?”; “Which scope grew?”; “How much of our total is Scope 3?”
**Deterministic engine:** scope grouping via `aggregate_groups(dimension="scope")`. Separate, non-Insight scope views also exist in `backend/api/v3_emissions.py:284` (`/scope-breakdown`) and legacy `backend/routes/emissions.py:224`, `backend/routes/organizations/dashboard.py:68`.
**Authoritative data:** `emissions_logs.scope` (`core.types.Scope`) + `calculated_kg_co2e`.
**Insight exposure:** scope **grouping** only — no scope *filter*, no scope comparison.
**Answer states:** `success`, `zero`, `no_data`, `invalid_input`; a *comparison* question currently yields a clarification / unsupported outcome.
**Evidence depth:** E1 (grouping) / E2 (via family 4).
**Viewer path:** scope group → family 4 provenance → snapshot → viewer.
**Status:** **PARTIAL**.
**Already implemented:** scope as a closed aggregation dimension with labels; canonical scope validation (`canonical_scope`) refusing invalid scope values.
**Exact missing capability:** scope as a **filter** combined with other dimensions; scope comparison over time.
**Schema change required:** no. **Accounting-policy decision required:** yes — comparison semantics are the PO's decision.
**PO decision IDs:** **D-11** (temporal comparison semantics) also governs scope comparison; capability-matrix **C-02** (scope-filtered aggregation) remains an approved-but-unimplemented dimension.
**Dependencies:** INS-01 aggregation; for comparison, the P2 contract.
**Proposed package:** **P2** — a bounded comparison package could carry a scope dimension *if the PO scopes it that way* (not assumed).
**Security / tenant isolation:** org-scoped; scope is **not** an authorization boundary and must never be treated as one.
**Verification requirements:** filter correctness, canonical scope rejection, tenant negatives.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** grouping CLOSED under INS-01; filtering / comparison **NOT AUTHORIZED**.

## 4.6 Family 6 — Scope 3 Categories 1–15

**Business purpose:** report and analyse Scope 3 by the fifteen GHG Protocol categories.
**Representative questions (QL §6, §7–§21):** “What is our Category 1 footprint?”; “Which Scope 3 category is largest?”; “How much of Category 6 is air travel?” (fifteen dedicated QL sections).
**Deterministic engine:** **none.** The only related code is legacy: `backend/utils/emissions.py:132,141,171` sets a coarse `ghg_protocol_category` (including the literal `'Other'`), and `backend/domain/disclosure.py` carries `scope_hint` values. Neither is a taxonomy engine.
**Authoritative data:** none for categories (a category dimension does not exist on snapshots or logs).
**Insight exposure:** none — an aggregation by category is unrepresentable (`invalid_input` / unsupported dimension).
**Answer states:** unsupported / `invalid_input` today; must never be answered by inference.
**Evidence depth:** none.
**Viewer path:** not applicable until the dimension exists.
**Status:** **MISSING**.
**Already implemented:** nothing first-class.
**Exact missing capability:** versioned taxonomy, deterministic assignment rule, storage on the calculation lineage, historical semantics for already-calculated data, category-level aggregation and reporting.
**Schema change required:** **yes** — versioned taxonomy + references from logs/snapshots.
**Accounting-policy decision required:** **yes — blocking.** The PO capability matrix §3.3 approves GHG Protocol Categories 1–15 as the baseline and states: *“Do not silently infer categories from free text”*, requiring taxonomy version, mapping source/rule, confidence/status, and defined historical behaviour.
**PO decision IDs:** **D-13**; capability-matrix **C-03**.
**Dependencies:** supplier/value-chain data (family 9) for several categories; factor provenance (family 13) for methodology-linked categories.
**Proposed package:** **P7**.
**Security / tenant isolation:** a taxonomy must be organisation-owned where customer-specific, globally versioned where standard; assignments must be immutable once referenced by a calculation; no cross-tenant leakage of customer category mappings.
**Verification requirements:** taxonomy versioning, deterministic assignment, historical stability, category totals reconciling to scope totals, tenant negatives.
**Investor-demo relevance:** **MED–HIGH** (commonly asked; must not be faked). **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED** (approved in principle only; no bounded authorization exists).

## 4.7 Family 7 — Scope 2 Methodology

**Business purpose:** report Scope 2 under both location-based and market-based methods, with contractual-instrument awareness.
**Representative questions (QL §5, §31, §33):** “What is our market-based Scope 2?”; “Which instruments cover our electricity?”; “Why do our two Scope 2 figures differ?”
**Deterministic engine:** **none for market-based.** `backend/domain/disclosure.py` defines `SCOPE2_METHODS = ("LOCATION_BASED", "MARKET_BASED")` as a *disclosure vocabulary* (validated at `domain/disclosure.py:253`) and `disclosure_requirement_versions.scope2_method_hint` carries a hint. The PO capability matrix is explicit: *“The current disclosure `scope2_method_hint` must not be treated as a calculation engine.”*
**Authoritative data:** none for method-aware calculation; no contractual-instrument store; no residual-mix source.
**Insight exposure:** none.
**Answer states:** unsupported; a method question must never be answered from the hint.
**Evidence depth:** none for market-based.
**Viewer path:** not applicable until instruments exist.
**Status:** **MISSING**.
**Already implemented:** disclosure vocabulary + validation only.
**Exact missing capability:** a method dimension on calculations; contractual-instrument storage and quality handling; applicable factor hierarchy; residual-mix handling; methodology versioning; dual reporting.
**Schema change required:** **yes**.
**Accounting-policy decision required:** **yes — blocking** (PO capability matrix §3.6 approves dual reporting as a product target but does not define instrument eligibility, residual mix, or versioning behaviour).
**PO decision IDs:** **D-10**; capability-matrix **C-15** / §3.6.
**Dependencies:** factor hierarchy and factor history (family 13); disclosure/reporting surfaces (family 18).
**Proposed package:** **P8a**.
**Security / tenant isolation:** instrument documents are evidence-bearing and must flow through DM-6 and the existing viewer; instrument ownership is organisation-scoped.
**Verification requirements:** method resolution, dual totals, instrument eligibility, historical version retention, tenant negatives.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.8 Family 8 — Scope 1 Decomposition

**Business purpose:** decompose Scope 1 into stationary, mobile, fugitive and process emissions.
**Representative questions (QL §4, §31):** “How much of Scope 1 is fugitive?”; “What share is mobile combustion?”; “How much process emissions do we have?”
**Deterministic engine:** **none** — no stationary/mobile/fugitive/process classification exists anywhere in the repository.
**Authoritative data:** none (Scope 1 exists as a scope value only).
**Insight exposure:** none.
**Answer states:** unsupported; must never be inferred from activity wording.
**Evidence depth:** none.
**Viewer path:** not applicable until the classification exists.
**Status:** **MISSING**.
**Already implemented:** nothing.
**Exact missing capability:** a governed decomposition model (classification dimension, where it applies, and the rule that establishes it).
**Schema change required:** **yes** (subject to the PO's chosen model — snapshot, log, factor or activity level).
**Accounting-policy decision required:** **yes — blocking** (PO capability matrix §3.7 approves decomposition and requires: *“Where a category is not applicable or cannot be determined, the system must say so rather than infer it.”*).
**PO decision IDs:** **D-15**; capability-matrix **C-16** / §3.7.
**Dependencies:** none strictly; sharing the versioning pattern proven in the Scope 3 package is recommended (**INFERENCE**).
**Proposed package:** **P8b**.
**Security / tenant isolation:** unchanged (org-scoped reads); any classification must be immutable once referenced.
**Verification requirements:** decomposition totals reconciling to Scope 1; explicit “not applicable / undetermined” handling; tenant negatives.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.9 Family 9 — Supplier Intelligence

**Business purpose:** attribute emissions to suppliers and compare supplier contributions.
**Representative questions (QL §22, §26):** “Which supplier contributed most to our footprint?”; “How have supplier emissions changed?”; “What do we buy from this supplier that generates emissions?”
**Deterministic engine:** `aggregate_groups(dimension="supplier")` over `emissions_logs.supplier_id` with `group_labels` resolving `public.suppliers`; discovery `EXISTS` lineage on the same column; `backend/data/suppliers.py` (including `remove`).
**Authoritative data:** `emissions_logs.supplier_id` (a column that the **emission write path never populates**), plus `public.suppliers`. Capture exists upstream on `manual_extraction_items.mapped_supplier_id` (`backend/data/manual_extraction.py:36,114,531`) and `ai_mapped_supplier_id` in `backend/data/document_processing.py:42`.
**Insight exposure:** supplier aggregation and supplier discovery filters — **both currently return `NO DATA`** because the key is unpopulated.
**Answer states:** `no_data` (the truthful current state); `success` once populated.
**Evidence depth:** E1/E2 (supplier group → family 4 provenance → viewer).
**Viewer path:** supplier group → snapshot → source line item → viewer.
**Status:** **PARTIAL (structural foundation; data-empty)**.
**Already implemented:** the dimension, label resolution, discovery filters, supplier master-data CRUD.
**Exact missing capability:** population of `emissions_logs.supplier_id` from governed, approved extraction/mapping; confidence/approval semantics; backfill policy; historical verification.
**Schema change required:** **no for the column** (it exists); possibly yes for a backfill ledger if the PO requires one.
**Accounting-policy decision required:** **yes — blocking** (PO capability matrix §3.4: propagate governed supplier identity into authoritative calculation lineage; define confidence/approval; define backfill; verify historical data before enabling analytics).
**PO decision IDs:** **D-09**; capability-matrix **C-06**, **C-07** (conditional), **C-08** (variance, only after C-06/C-07).
**Dependencies:** extraction/mapping governance; for supplier variance, families 11–12.
**Proposed package:** **P6**.
**Security / tenant isolation:** supplier identity is organisation-owned master data; supplier analytics must never expose another tenant's supplier relationships.
**Verification requirements:** write-path persistence, idempotent backfill, tenant negatives, truthful `no_data` before population.
**Investor-demo relevance:** **HIGH** (with the truthful limitation that analytics are empty until persistence is authorized). **Production relevance:** **HIGH**.
**Authorization status:** structural foundation CLOSED under INS-01; persistence **NOT AUTHORIZED**.

## 4.10 Family 10 — Facility / Asset Intelligence

**Business purpose:** attribute emissions to facilities and assets, and compare their contributions.
**Representative questions (QL §25, §26):** “Which site emitted most this year?”; “What did asset X emit?”; “Which facility changed?”
**Deterministic engine:** `aggregate_groups(dimension="facility" / "asset")` over `calculation_snapshots.metadata->>'facility_id'` and `asset_id`, with catalogue labels from `public.facilities` / `public.assets`; discovery `EXISTS` lineage for facility/asset filters.
**Authoritative data:** `calculation_snapshots.metadata` (JSONB), `public.facilities`, `public.assets`, `emissions_logs.asset_id`; master data maintained through `frontend/src/v3/admin/{FacilitiesTab,LocationsTab,VehiclesTab}.jsx`.
**Insight exposure:** facility and asset aggregation + discovery filters (both operational).
**Answer states:** `success`, `zero`, `no_data`, `invalid_input`.
**Evidence depth:** E1/E2.
**Viewer path:** facility/asset group → family 4 provenance → snapshot → viewer.
**Status:** **PARTIAL (foundation)**.
**Already implemented:** two dimensions, label resolution, master-data CRUD, deterministic lineage via the snapshot.
**Exact missing capability:** snapshot-native (rather than metadata-derived) attribution; facility/asset **change** analysis; comparisons.
**Schema change required:** no for the foundation.
**Accounting-policy decision required:** no (attribution is already deterministic), **provided** the PO does not require attribution semantics beyond the existing lineage.
**PO decision IDs:** C-04 (month/year/asset/facility aggregation) — satisfied as a foundation.
**Dependencies:** family 3.
**Proposed package:** change/comparison work would fold into **P2** if the PO scopes it there (**INFERENCE**, not assumed).
**Security / tenant isolation:** org-scoped reads; facility/asset identifiers are organisation-owned.
**Verification requirements:** dimension correctness, label resolution, tenant negatives.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** CLOSED under INS-01 as a foundation; further analytics **NOT AUTHORIZED**.

## 4.11 Family 11 — Temporal Comparison

**Business purpose:** state how emissions changed between two defined periods.
**Representative questions (QL §26):** “Is this month higher than last month?”; “How did we do year over year?”; “What changed since the last reporting period?”
**Deterministic engine:** period aggregation exists (family 3); `backend/data/reporting.py:785` provides a zero-filled monthly trend for reporting; the legacy `backend/report_generator.py` produces YoY narrative text (**not** an Insight surface and not a deterministic Insight answer).
**Authoritative data:** `emissions_logs` period totals.
**Insight exposure:** **none** — no comparison tool exists.
**Answer states:** unsupported / clarification today; `success` with absolute and percentage change once implemented.
**Evidence depth:** E1/E2 (both periods resolvable; each side traceable via family 4).
**Viewer path:** comparison side → family 4 provenance → snapshot → viewer.
**Status:** **MISSING** as an Insight capability (its *data basis* already exists).
**Already implemented:** period aggregation; monthly trend data for reports.
**Exact missing capability:** a bounded two-period comparison operation on one authoritative basis, with explicit change semantics.
**Schema change required:** **no**.
**Accounting-policy decision required:** **yes** (comparison basis — reporting vs calendar period, restatement/partial-period handling, aggregate-level vs per-dimension percentage).
**PO decision IDs:** **D-11**; capability-matrix **C-11** (approved in principle) and §3.8.
**Dependencies:** INS-01 aggregation; provenance for honest traceability.
**Proposed package:** **P2**.
**Security / tenant isolation:** both periods must be authorised for the same organisation; no cross-period tenant leakage.
**Verification requirements:** deterministic ordering, zero-basis percentage handling, no-overlap rules, tenant negatives, and no narrated causality (that belongs to family 12).
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.12 Family 12 — Variance / Attribution

**Business purpose:** explain *why* a change occurred, decomposed into deterministic components.
**Representative questions (QL §26, §29, §31):** “Why did emissions increase?”; “Was it volume or factor?”; “Did a methodology change move the number?”
**Deterministic engine:** **none** — no factor/activity/methodology/boundary attribution engine exists.
**Authoritative data:** would require stable taxonomy dimensions (families 6–8, 13) plus comparable periods (family 11).
**Insight exposure:** none.
**Answer states:** unsupported; the PO matrix requires that *“If the stored evidence cannot establish causation, the answer must explicitly report that limitation.”*
**Evidence depth:** none today; would be E2/E3 once built.
**Viewer path:** component → snapshot → viewer (end state).
**Status:** **MISSING**.
**Already implemented:** nothing (legacy report-trend narration is not attribution).
**Exact missing capability:** deterministic decomposition of change into activity/quantity, factor, methodology, boundary, data-availability and restatement components, with explicit uncertainty reporting.
**Schema change required:** **likely yes** (history sufficient to decompose factor/methodology movement).
**Accounting-policy decision required:** **yes — blocking** (PO capability matrix §3.8 lists the components; it does not define ordering, residual handling or restatement rules).
**PO decision IDs:** **D-12** (plus **D-13** for factor history, **D-11** for the comparison basis).
**Dependencies:** **P2** (comparison), taxonomy stability (families 6–8), factor history (family 13).
**Proposed package:** **P9**.
**Security / tenant isolation:** unchanged (org-scoped reads); component identifiers are references, not grants.
**Verification requirements:** decomposition determinism, reconciliation to the total change, explicit residual/limitation reporting, tenant negatives.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.13 Family 13 — Emission Factor Intelligence

**Business purpose:** explain which factor was used, from where, with which methodology, and how factor choice affects results.
**Representative questions (QL §23, §33):** “Which factor was used for this diesel line?”; “What is the source and year of that factor?”; “Why was this factor chosen over another?”; “Did the factor change?”
**Deterministic engine:** `engines/factor_matching.py`, `engines/factor_selection_policy.py`, `engines/matching_stages.py`, `backend/data/factors.py`, `backend/data/customer_factors.py`, `backend/data/aliases.py`. The snapshot persists `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `factor_set`, `co2e_multiplier`, `methodology`, `algorithm_version`.
**Authoritative data:** `calculation_snapshots` factor fields, `public.emission_factors`, `customer_factors`, aliases.
**Insight exposure:** **partial** — factor fields are returned inside `calculation_snapshot_lookup`; there is no factor-specific tool, no candidate history and no factor-change analysis.
**Answer states:** `success` / `no_data` for the factor **used**; unsupported for candidate history and factor movement.
**Evidence depth:** **E2** (the factor used is explainable from the snapshot; candidate/stage history is not retained).
**Viewer path:** factor explanation → snapshot → source line item → viewer.
**Status:** **PARTIAL**.
**Already implemented:** deterministic matching/selection; customer-factor precedence with `customer_factor_id`; provenance fields on the immutable snapshot.
**Exact missing capability:** historical factor metadata sufficient to explain the exact factor basis (unit, country, reporting year, activity type at calculation time) where not already captured; candidate/stage history; factor-change attribution.
**Schema change required:** **yes for a full factor-history contract**; possibly not, if the PO's D-13 answer is satisfied by the snapshot fields already retained (**the PO must decide**).
**Accounting-policy decision required:** **yes** — capability matrix §3.10: *“Candidate alternatives may only be discussed if their history was actually retained.”*
**PO decision IDs:** **D-13**; capability-matrix **C-09** (explanation expansion), **C-10** (factor-change attribution), §3.10.
**Dependencies:** family 1 (snapshot read path); families 11/12 for change attribution.
**Proposed package:** a **read-only** expansion of already-retained fields could ride with **P3**; factor-**history schema** work is separate and **not authorized**.
**Security / tenant isolation:** customer factors are organisation-owned; must **not** depend on or worsen the separately tracked cross-tenant factor-metadata exposure (closure §8.6).
**Verification requirements:** provenance fidelity, customer-factor precedence preserved, tenant negatives, no candidate claim without retained history.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** snapshot-level explanation CLOSED under INS-01; expansion **NOT AUTHORIZED**.

## 4.14 Family 14 — Data Quality Intelligence

**Business purpose:** tell a user what is missing, unmapped, unresolved or blocked in their data.
**Representative questions (QL §27, §37):** “What data is missing?”; “Which records are unmapped?”; “How complete is our data?”; “What is blocking my reporting?”
**Deterministic engine:** signals exist but are not joined into one quality view: validation issues (`engines/validation.py`, the `issues` table, `/issues` UI), the review queue, and `completeness_score` in **two unrelated places** — organisation-profile completeness (`backend/routes/organizations/metadata.py:525`, `backend/routes/organizations/management.py:1177`) and extraction completeness (`backend/services/automatic_extraction.completeness_score`, used at `backend/services/ai_document_extraction.py:243`).
**Authoritative data:** `issues`, processing/review queue tables, extraction records, organisation profile fields.
**Insight exposure:** none.
**Answer states:** unsupported today; counts-based (`success` / `zero` / `no_data`) once exposed.
**Evidence depth:** E1/E2 (counts and identifiers; identifiers resolve through existing routes).
**Viewer path:** quality item → affected record → viewer (where applicable).
**Status:** **MISSING** (as an Insight capability; the underlying signals exist).
**Already implemented:** validation issues, review queue, two distinct completeness notions.
**Exact missing capability:** a bounded, deterministic quality summary over authoritative records with **PO-approved signal definitions**.
**Schema change required:** **no** (reads existing stores).
**Accounting-policy decision required:** **yes** — which signals are customer-facing and how they are named (the two `completeness_score` notions must not be conflated).
**PO decision IDs:** **D-14**; capability-matrix **C-12** (evidence/quality selection, approved bounded) and **C-13** (primary/secondary classification — a **separate** concept, not the same thing).
**Dependencies:** none blocking; benefits from family 16.
**Proposed package:** **P3**.
**Security / tenant isolation:** org-scoped counts only; no raw source text to the provider; no cross-tenant aggregation.
**Verification requirements:** counts traceable to a query, tenant negatives, no conflation of the two completeness scores, no raw content exposure.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.15 Family 15 — Methodology / Boundary Intelligence

**Business purpose:** explain the methodology applied and the organisational/operational boundary behind a figure.
**Representative questions (QL §31, §40):** “What methodology was used for this number?”; “What is our organisational boundary?”; “Which facilities are in scope this year?”
**Deterministic engine:** **partial primitives only** — `calculation_snapshots.methodology`, `backend/domain/disclosure.py` requirement versions, and organisation profile / boundary fields with their completeness scoring. There is **no first-class boundary model** and no methodology-explanation contract.
**Authoritative data:** `calculation_snapshots.methodology`, disclosure requirement versions, organisation profile.
**Insight exposure:** none.
**Answer states:** unsupported today.
**Evidence depth:** E1/E2 at best.
**Viewer path:** not applicable until a methodology/boundary contract exists.
**Status:** **MISSING**.
**Already implemented:** the methodology value on each snapshot; disclosure requirement versioning.
**Exact missing capability:** a governed methodology/boundary explanation contract and, for organisational vs operational boundary, a first-class boundary model.
**Schema change required:** **yes** for a boundary model.
**Accounting-policy decision required:** **yes — blocking** — boundary definition and consolidation approach are accounting policy and nothing in the repository establishes them.
**PO decision IDs:** **no D-ID exists yet in the master preflight register** → a **new** PO decision is required. This matrix records the gap rather than inventing one.
**Dependencies:** disclosure/reporting (family 18) for framing.
**Proposed package:** **not sequenced** (no decision → no package).
**Security / tenant isolation:** unchanged (org-scoped); boundary definitions are organisation-owned.
**Verification requirements:** to be defined after the PO decision.
**Investor-demo relevance:** **MED**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.16 Family 16 — Evidence / Audit Intelligence

**Business purpose:** prove a number — show its calculation, factor, source, lineage and audit record, and state what limits the claim.
**Representative questions (QL §28, §29, §34):** “What supports this number?”; “Which source document?”; “Can this be reproduced?”; “Is there an audit event for the intervention?” (QL 424–426).
**Deterministic engine:** `audit_trail` (append-only: `backend/data/audit.py` `save()` inserts only; `delete()` documented as never used), `backend/api/admin_audit.py` (list / export / correlation / by-id), `evidence_line_items`, the `report_evidence_lookup` tool, and `GET /api/v3/exports/audit-package.json` (`backend/api/v3_exports.py:90` over `backend/data/exports.py`).
**Authoritative data:** `audit_trail`, `evidence_line_items`, `calculation_snapshots`, `emissions_logs`, `report_versions` / `report_version_artifacts`.
**Insight exposure:** `report_evidence_lookup` + references + viewer handoff. There is **no** bounded “reproduce this number” Insight contract.
**Answer states:** `success`, `no_data`, `not_authorized`, `invalid_input`, `partial`; audit-package semantics are `PO DECISION REQUIRED`.
**Evidence depth:** **E3 today** — **E4 is NOT claimed**, because E4 is a PO-defined package (D-16) and the existence of `/audit-package.json` alone does not establish it.
**Viewer path:** the Shared Source Evidence Viewer — `/evidence/line-items/{lineItemId}` (the **single** evidence destination).
**Status:** **PARTIAL**.
**Already implemented:** append-only audit ledger with export and correlation; evidence line items; the viewer; the audit-package JSON export; DM-6 depth gating.
**Exact missing capability:** an Insight-level “reproduce this number” contract and a **PO-defined** E4 audit-package scope.
**Schema change required:** **no** for the current chain; possibly yes if the PO's E4 definition requires more.
**Accounting-policy decision required:** **yes** — what constitutes an audit package, who may obtain it, and whether it is an export or an on-screen surface.
**PO decision IDs:** **D-16**; capability-matrix **C-12** (evidence selection) and §3.9 (aggregate → evidence).
**Dependencies:** families 1–4.
**Proposed package:** **P3**.
**Security / tenant isolation:** references are **locators, never grants**; the viewer re-authorizes; DM-6 governs depth; no signed URLs in prompts; audit is append-only.
**Verification requirements:** chain resolution on a sample set, tenant negatives (a reference from another tenant must not resolve), no certification claim, bound assertions.
**Investor-demo relevance:** **HIGH**. **Production relevance:** **HIGH**.
**Authorization status:** **NOT AUTHORIZED** beyond the closed INS-01 evidence handoff.

## 4.17 Family 17 — General Carbon-Accounting Knowledge (Mode E)

**Business purpose:** answer standards/concept questions without touching customer data.
**Representative questions (QL §35 Mode E, §39, §40):** “What is the difference between Scope 1 and Scope 2?”; “What is primary vs secondary data?”; “What does a methodology mean?”
**Deterministic engine:** **none** — no knowledge store, no embeddings, no vector search, no RAG. `backend/services/insight_context.py` explicitly documents that no embeddings/vector search/RAG exist.
**Authoritative data:** none; concept authority is external (GHG Protocol, ISO 14064-1:2018), which the repository cites as references only.
**Insight exposure:** none.
**Answer states:** unsupported — E0 questions have no governed path today.
**Evidence depth:** **E0**, and it must remain clearly separated from customer-specific data.
**Viewer path:** not applicable (E0 has no customer evidence).
**Status:** **MISSING**.
**Already implemented:** nothing.
**Exact missing capability:** a governed, versioned, citable knowledge source separated from customer data, with a review cycle.
**Schema change required:** **yes**.
**Accounting-policy decision required:** **yes — blocking** (source selection, licensing, versions, citation policy, review cycle).
**PO decision IDs:** **D-17**; capability-matrix **C-19** (approved as *future*) and §3.11.
**Dependencies:** none technically; governance is the gate.
**Proposed package:** **P10a**.
**Security / tenant isolation:** knowledge must never blend into customer data; any authenticated exposure must inherit I2/I3/I4/I5/I6 permissions.
**Verification requirements:** citation integrity, version pinning, no fabricated customer facts, explicit separation from customer answers.
**Investor-demo relevance:** **MED**. **Production relevance:** **MED–HIGH**.
**Authorization status:** **NOT AUTHORIZED**.

## 4.18 Family 18 — Reporting / Disclosure Assistance

**Business purpose:** connect a question to the relevant report/disclosure output and expose coverage gaps.
**Representative questions (QL §32, §29):** “Is our report ready?”; “What is missing for our disclosure?”; “What does our published report say about Scope 2?”; “Which report version covers 2024?”
**Deterministic engine:** real reporting exists — `engines/report_generation.py`, `backend/data/reporting.py`, `report_versions`, `report_version_artifacts`, `backend/data/report_artefacts.py`, disclosure projection (`backend/domain/disclosure.py` + requirement versions), `backend/api/v3_reports.py`, exports in `backend/api/v3_exports.py`.
**Authoritative data:** `reports`, `report_versions`, `report_version_artifacts`, disclosure requirement versions, `emissions_logs`/snapshots underpinning the report.
**Insight exposure:** **partial** — `report_lookup`, `report_version_lookup`, `report_evidence_lookup` let a user reach existing reports and their evidence; there is **no** obligation/framework mapping and no coverage-gap explanation.
**Answer states:** `success` / `no_data` for *existing* reports; unsupported for framework/obligation questions.
**Evidence depth:** E2/E3 (report → version → evidence).
**Viewer path:** report → version → calculation → evidence (the existing path).
**Status:** **PARTIAL**.
**Already implemented:** report generation, versioning, artefacts, disclosure projection, report reachability from Insight.
**Exact missing capability:** mapping a question to the applicable framework/obligation and explaining what the data does or does not cover.
**Schema change required:** **no** for the assistance layer itself.
**Accounting-policy decision required:** **yes** — which frameworks/obligations are in scope and who owns the mapping.
**PO decision IDs:** **D-18**.
**Dependencies:** disclosure projection; families 6–8 for the dimensional content a framework would require.
**Proposed package:** **P10b**.
**Security / tenant isolation:** reports are organisation-scoped; disclosure projections must not leak another tenant's data; no signed URLs in prompts.
**Verification requirements:** report/version resolution correctness, tenant negatives, framework mapping traceability.
**Investor-demo relevance:** **MED**. **Production relevance:** **MED–HIGH**.
**Authorization status:** report reachability CLOSED under INS-01; assistance **NOT AUTHORIZED**.

## 4.19 Family 19 — Decision / Reduction Intelligence

**Business purpose:** support reduction planning on authoritative data (targets, scenarios, abatement).
**Representative questions (QL §40 “future analytical questions”, §26):** “How do we reach a reduction target?”; “What is the largest abatement opportunity?”; “What would happen if we switched fuel?”
**Deterministic engine:** **none** — no reduction-target model, no scenario modelling, no abatement library exists in the backend.
**Authoritative data:** none.
**Insight exposure:** none.
**Answer states:** unsupported.
**Evidence depth:** none (a future capability would need at least E1/E2 with explicit scenario provenance).
**Viewer path:** not applicable; any future recommendation must still trace to deterministic data.
**Status:** **MISSING**.
**Already implemented:** nothing (note: a public `/carbon-reduction-plan` **page** exists in the frontend route table; the route's existence is **not** evidence of a deterministic reduction engine, and this matrix does not treat it as one).
**Exact missing capability:** target/scenario modelling on authoritative data, with explicit methodology.
**Schema change required:** **yes**.
**Accounting-policy decision required:** **yes — blocking** (target/scenario methodology and what framing Insight may use).
**PO decision IDs:** **D-19**. **No capability-matrix C-ID exists for this family** — it is not in the PO capability matrix's row set; recorded as a gap, not an approval.
**Dependencies:** **P9** (variance/attribution), taxonomy stability, knowledge layer for methodology framing.
**Proposed package:** **P10c**.
**Security / tenant isolation:** unchanged (org-scoped); scenario data is organisation-owned.
**Verification requirements:** scenario determinism, explicit assumption surfacing, no untraceable recommendation.
**Investor-demo relevance:** **LOW–MED** (aspirational; must not be demoed as implemented). **Production relevance:** **MED**.
**Authorization status:** **NOT AUTHORIZED** (no PO decision, no package).

---

# 5. Question Library coverage

## 5.1 How the Question Library is used

`docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md` (971 lines) contains **426 numbered candidate questions** across 43 sections, plus six **evidence modes** (§35: A authoritative numeric, B calculation explanation, C evidence navigation, D comparative analysis, E conceptual guidance, F audit challenge).

It is a **coverage and acceptance catalogue**, *not* a list of 426 implementations. Per the v2 architecture §9 the 426/426 count is explicitly **rejected as a completeness metric**:

> “A more meaningful metric is: capability-family coverage; representative-question coverage; deterministic answer coverage; evidence coverage; verified coverage; truthful unsupported/no-data handling.”

**This matrix therefore maps Question-Library *sections* to capability families and records representative questions — it does not create 426 feature rows, and it does not justify bespoke handlers.**

## 5.2 Section → family map

| QL § | Question-Library section | Mapped family/families | Current answerability of representative questions |
| --- | --- | --- | --- |
| §3 | Executive / overall footprint | 3 (+1, 4) | **ANSWERABLE** |
| §4 | Scope 1 questions | 3, 5 (+8 decomposition part) | **PARTIAL** — totals answerable; decomposition **UNSUPPORTED** |
| §5 | Scope 2 questions | 3, 5 (+7 market-based part) | **PARTIAL** — location-based totals answerable; market-based **UNSUPPORTED** |
| §6 | Scope 3 questions | 3, 5 (+6 categories) | **PARTIAL** — Scope 3 totals answerable; categories **UNSUPPORTED** |
| §7–§21 | Scope 3 Categories 1–15 (fifteen sections) | 6 | **UNSUPPORTED** |
| §22 | Supplier questions | 9 (+11/12 for variance) | **NO DATA** today (dimension exists, key unpopulated) |
| §23 | Emission-factor questions | 13 (+1) | **PARTIAL** — factor used answerable; candidates/history **UNSUPPORTED** |
| §24 | Calculation-method questions | 1, 13, 15 | **PARTIAL** — per-calculation method answerable; methodology/boundary framing **UNSUPPORTED** |
| §25 | Activity / input questions | 2, 3, 10 | **ANSWERABLE / PARTIAL** (facility/asset attribution via snapshot metadata) |
| §26 | Trend / variance / hotspot questions | 11, 12 (+3, 9, 10) | **UNSUPPORTED** for change and attribution; hotspots answerable via aggregation |
| §27 | Data-quality questions | 14 | **UNSUPPORTED** (signals exist, not exposed) |
| §28 | Evidence / provenance questions | 4, 16 (+1) | **PARTIAL / ANSWERABLE** at E2–E3 |
| §29 | External auditor questions | 16, 18 (+1, 4) | **PARTIAL** — no E4 package (D-16); auditor direct access **DEFERRED** |
| §30 | Consultant questions | — | **DEFERRED / NOT AUTHORIZED** for Insight (consultant APIs exist outside Insight) |
| §31 | Boundary and methodology questions | 15 (+7, 8) | **UNSUPPORTED** |
| §32 | Reporting / disclosure questions | 18 | **PARTIAL** — existing reports reachable; framework mapping **UNSUPPORTED** |
| §33 | Factor-selection challenge questions | 13 | **PARTIAL** — the factor used is explainable; rejection reasoning/history **UNSUPPORTED** |
| §34 | Evidence-quality challenge questions | 16, 14 | **PARTIAL** |
| §35 | Evidence modes A–F | A→3/1; B→1/13; C→16; D→11/12; E→17; F→16 | A, B, C **available**; D **UNSUPPORTED**; E **UNSUPPORTED**; F **PARTIAL** |
| §36 | Questions that should trigger clarification rather than guessing | all families | **SUPPORTED** — the fifteen-state vocabulary and the planner honour clarification instead of guessing |
| §37 | Questions that must be answered “no authoritative data found” | all families | **SUPPORTED** — `no_data` is a contract outcome (and is today's truthful supplier answer) |
| §38–§40 | Personas / industry patterns / architecture implications | — | Implications captured in §4, §9, §14 |
| §41 | Product rule: ASK → VERIFY → EXPLAIN → TRACE | all | **PRESERVED** — see §5.3 |
| §42–§43 | Governance reminder / core principle | — | **PRESERVED** — see §15 and §17 |

## 5.3 Preservation of ASK → VERIFY → EXPLAIN → TRACE

| Stage | Where it is enforced today (verified) |
| --- | --- |
| **ASK** | Bounded intent recognition in `backend/services/insight_query_planner.py` — closed schema, no SQL generation, no tenant choice, no authorization decision, no calculation |
| **VERIFY** | I2 authorization + closed I3 tool dispatch + organisation-scoped deterministic SQL with positional parameters |
| **EXPLAIN** | Bounded provider narration over tool output only; suppressed on ambiguity; `NarrationState` records truthfully why narration did not run |
| **TRACE** | References (locators) → Shared Source Evidence Viewer; DM-6 depth gating |

**The LLM is never the source of truth** — no family in §4 may be implemented in a way that lets a model produce a carbon figure.

## 5.4 Answerability summary

| Class | Representative coverage |
| --- | --- |
| **ANSWERABLE NOW** | families 1–4 representative questions; scope/month/year/activity/facility/asset aggregation; evidence and provenance within E2–E3 |
| **PARTIAL** | factor-used explanation; per-calculation methodology value; facility/asset analytics beyond aggregation; report reachability; evidence-quality challenges |
| **NO DATA** | every supplier question (a data gap, not a capability gap) |
| **UNSUPPORTED / NOT IMPLEMENTED** | Scope 3 categories; market-based Scope 2; Scope 1 decomposition; temporal comparison; variance/attribution; data-quality exposure; methodology/boundary; concept knowledge; reduction intelligence |
| **DEFERRED / NOT AUTHORIZED** | consultant Insight personas; auditor direct Insight |

**INFERENCE:** no exact percentage of the 426 questions is asserted here, because that would require classifying all 426 individually. Section-level and representative-question mapping is what the evidence supports; a per-question classification can be recorded in a later revision once the PO wants that granularity.

---

# 6. Evidence-depth matrix

Levels are those defined by the architecture reference §11. **E4 is not claimed anywhere in this matrix.**

| Family | E0 | E1 | E2 | E3 | E4 | Current maximum (verified) | Viewer destination |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Identified Calculation | — | — | ✔ | ✔ | PO-defined | **E3** | `/evidence/line-items/{id}` |
| 2 Discovery | — | — | ✔ | ✔ | PO-defined | **E2/E3** | via discovered snapshot |
| 3 Aggregation | — | ✔ | (via 4) | — | PO-defined | **E1** | via family 4 |
| 4 Aggregate Provenance | — | — | ✔ | ✔ | PO-defined | **E2→E3** | `/evidence/line-items/{id}` |
| 5 Scope Analysis | — | ✔ | (via 4) | — | PO-defined | **E1** | via family 4 |
| 6 Scope 3 Categories | — | — | — | — | — | **none** | n/a |
| 7 Scope 2 Methodology | — | — | — | — | — | **none** (market-based) | n/a |
| 8 Scope 1 Decomposition | — | — | — | — | — | **none** | n/a |
| 9 Supplier Intelligence | — | ✔ | (via 4) | — | PO-defined | **E1/E2, empty data** | via family 4 |
| 10 Facility / Asset | — | ✔ | (via 4) | — | PO-defined | **E1/E2** | via family 4 |
| 11 Temporal Comparison | — | ✔ | ✔ (per side) | (per side) | PO-defined | **not implemented** | via family 4 |
| 12 Variance / Attribution | — | — | — | — | — | **none** | n/a |
| 13 Emission Factor Intelligence | — | — | ✔ | (via 1) | PO-defined | **E2** | via family 1 |
| 14 Data Quality | — | ✔ (signals) | (possible) | — | PO-defined | **not exposed** | existing item routes |
| 15 Methodology / Boundary | — | ✔ (partial) | (partial) | — | PO-defined | **not exposed** | n/a |
| 16 Evidence / Audit | — | — | ✔ | ✔ | **PO decision** | **E3** | `/evidence/line-items/{id}` |
| 17 Concept Knowledge | ✔ | — | — | — | — | **E0 (no path)** | n/a |
| 18 Reporting / Disclosure Assistance | — | ✔ | ✔ | ✔ | PO-defined | **E2/E3** | via report chain |
| 19 Decision / Reduction | — | — | — | — | — | **none** | n/a |

**Evidence principles binding every future package (verified today):**

1. **One destination only.** The Shared Source Evidence Viewer is the single evidence destination (v2 §15; PO closure §7). **No Insight-only viewer may be created**; a future Evidence Center must reuse the same destination.
2. **References are locators, never grants** — authorisation is re-established when the viewer resolves a reference.
3. **DM-6 depth gating** governs how deep an evidence view goes.
4. **No signed URLs in prompts.**
5. **Aggregate → evidence first, then claims.** PO matrix §3.9 requires an aggregate intended for audit/assurance use to identify its contributing records; family 4 satisfies this **as a foundation**, which is why no family here is described as “fully audit-ready”.

---

# 7. Answer-state matrix

## 7.1 The two layers (deliberately distinct — never merged)

| Layer | Vocabulary | Count | Defined in |
| --- | --- | --- | --- |
| Tool status | `success`, `no_data`, `not_authorized`, `invalid_input`, `provider_unavailable`, `error` | **6** | `backend/domain/insight_tool.py::ToolStatus` |
| Answer state | see §7.2 | **15** | `backend/domain/insight_interaction.py::AnswerStatus` |
| Narration state | `not_attempted`, `completed`, `unavailable`, `skipped` | **4** | `backend/domain/insight_interaction.py::NarrationState` |

## 7.2 The fifteen answer states and their triggers

| State | Meaning | Triggered today by (verified) |
| --- | --- | --- |
| `success` | authoritative answer produced | tools returning `success` |
| `zero` | an aggregate is genuinely zero | aggregation reason `zero_total` |
| `no_data` | the requested data is not present | tools returning `no_data`; also today's supplier answers |
| `not_authorized` | requester is not authorised | I2 denial / tool `not_authorized` |
| `insufficient_data` | data exists but cannot support the answer | planner / tool input insufficiency |
| `needs_clarification` | a required parameter is undeterminable | reasons such as `amount_tolerance_required`; planner ambiguity |
| `multiple_matches` | several authoritative records matched | discovery reason `multiple_matches` (**the single INS-01 addition**) |
| `tool_failure` | a tool failed | tool `error` mapped to failure semantics |
| `provider_unavailable` | provider path unavailable | reserved; never manufactured by the four non-provider tools |
| `partial` | only a bounded subset is available | bounded / truncated results |
| `rate_limited` | the technical limiter refused | **429** paths on both execution routes |
| `refused` | request refused on policy grounds | policy refusal paths |
| `ungrounded` | narration could not be grounded in tool output | grounding checks |
| `invalid_input` | input failed typed validation | typed validation / planner rejection |
| `error` | unexpected failure | tool `error` |

(PO capability matrix §3.1 required discovery states map as: no match → `no_data` / `zero`; one match → `success`; multiple matches → `multiple_matches`; invalid input → `invalid_input`; authorization failure → `not_authorized`; provider/internal failure → `provider_unavailable` / `tool_failure` / `error`. See conflict **X-2**, §2.3.)

## 7.3 Answer-state behaviour required of every family

| Requirement | Status |
| --- | --- |
| Ambiguity must never be silently resolved to a candidate | **PRESERVED** — `multiple_matches` + suppressed narration |
| Narration suppressed for ambiguous results | **PRESERVED** (I4, closure §6) |
| `zero` distinct from `no_data` | **PRESERVED** |
| Unsupported capabilities must not masquerade as `success` | **PRESERVED** — families 6, 7, 8, 11, 12, 14, 15, 17 and 19 have no path to `success` today |
| Failure modes truthful (`tool_failure` / `error` / `provider_unavailable`) | **PRESERVED** |
| Security states rank above content states | **PRESERVED** — this is why `multiple_matches` ranks below every security/failure state and above `tool_failure` / `partial` / `no_data` / `success` |
| A user-visible “capability not yet implemented” state distinct from `invalid_input` | **PO DECISION REQUIRED** if the PO wants it (would be a sixteenth state, i.e. an I4 contract change) |

---

# 8. Security and tenant-isolation matrix

## 8.1 Verified platform controls that bind every family

| Control | Verified mechanism |
| --- | --- |
| Tenant isolation | organisation-scoped predicates on every analytics query; the parameter is bound to the caller's organisation |
| Authorization | I2 authorization (`backend/api/insight_authz.py`) — evaluated **server-side**, never from the UI |
| Tool allowlists | closed I3 dispatch with declared output allowlists |
| Persistence allowlists | I4 typed-only projection — no arbitrary column persistence |
| Bounded context | I5 (`MAX_TOOL_CALLS_PER_INTERACTION = 4`; the tool-name projection was widened 4 → 7 for the INS-01 catalogue) |
| Conversation semantics | I6 creator-private conversation rules |
| Evidence | DM-6 depth gating; the viewer re-authorises; references are locators |
| Result bounds | 25 discovery / 50 aggregation / 100 provenance / 3,660-day period |
| SQL safety | fixed literals + positional parameters; **no model-generated SQL**; no arbitrary query surface |
| Rate limiting | per-user 20/5/2 and per-org 100/20/10 (closed under INS-01), enforced on **both** execution routes |
| Provider isolation | provider calls configuration-gated; narration bounded to tool output; no signed URLs in prompts |
| Audit | append-only `audit_trail`; limiter refusals audited |

## 8.2 Per-family isolation requirements beyond the baseline

| Family | Additional requirement |
| --- | --- |
| 1–4 | unchanged — regression only |
| 5 Scope Analysis | scope is **not** an authorization boundary and must never become one |
| 6 Scope 3 | taxonomy versioned; customer mappings organisation-owned; assignments immutable once referenced |
| 7 Scope 2 | instrument documents are evidence-bearing → DM-6 + viewer; instrument ownership org-scoped |
| 8 Scope 1 | classification immutable once referenced |
| 9 Supplier | supplier identity is org-owned master data; no cross-tenant supplier comparability |
| 10 Facility / Asset | identifiers org-owned; no cross-tenant master-data leakage |
| 11 Temporal Comparison | both periods must be authorised for the **same** organisation |
| 12 Variance | component identifiers are references, not grants |
| 13 Factor Intelligence | customer factors org-owned; must not depend on or worsen the separately tracked cross-tenant factor-metadata exposure (INS-01 closure §8.6) |
| 14 Data Quality | org-scoped counts only; no raw content; no cross-tenant aggregation |
| 15 Methodology / Boundary | boundary definitions org-owned |
| 16 Evidence / Audit | references never grant; the viewer re-authorises; no certification claim; no signed URLs logged or prompted |
| 17 Knowledge (Mode E) | knowledge must never blend into customer data; any authenticated exposure inherits I2–I6 |
| 18 Reporting / Disclosure | reports org-scoped; projections must not leak other tenants |
| 19 Reduction | scenario data org-owned; no untraceable recommendation |

## 8.3 Security negative tests required for any new family work

Every future package touching a family above must include **ALLOW and DENY** cases for at least: cross-organisation access; cross-consultant client access; Processing Entity boundary; viewer/unauthorised-member denial; and role-restricted write. **An unexpected ALLOW is a serious security finding.**

---

# 9. PO decision dependencies

Two ID systems are in play and are **not interchangeable**:

* **C-nn** — capability decisions in `CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md` (capability-level intent; mostly `APPROVE` / `APPROVED IN PRINCIPLE`, several `DEFER`).
* **D-nn** — the open decision register in `CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` §12 (the specific unresolved values and policies).

**`APPROVE` ≠ implementation authorization.** The capability matrix itself states: *“No Cline task may interpret ‘APPROVE’ as permission to implement all dependent capabilities at once.”*

## 9.1 Which D decision each family needs

| Family | Open decision required | D-ID | Blocking? |
| --- | --- | --- | --- |
| 5 Scope Analysis | comparison semantics | D-11 | for comparison only |
| 6 Scope 3 Categories | taxonomy version, assignment rule, historical semantics, factor-history scope | D-13 | **yes** |
| 7 Scope 2 Methodology | instruments, residual mix, dual reporting | D-10 | **yes** |
| 8 Scope 1 Decomposition | classes + where applied | D-15 | **yes** |
| 9 Supplier Intelligence | capture point, confidence, backfill, lineage | D-09 | **yes** |
| 11 Temporal Comparison | period basis, restatements, percentage basis | D-11 | **yes** |
| 12 Variance / Attribution | component list, ordering, residual, restatements | D-12 (+D-11, D-13) | **yes** |
| 13 Factor Intelligence | which historical factor metadata must be retained | D-13 | **yes** for history |
| 14 Data Quality | which signals are authoritative + naming | D-14 | **yes** |
| 15 Methodology / Boundary | boundary definition + consolidation | **none exists → new decision required** | **yes** |
| 16 Evidence / Audit | E4 package scope, audience, surface | D-16 | **yes** for E4 |
| 17 Knowledge (Mode E) | sources, licensing, versions, citations, review cycle | D-17 | **yes** |
| 18 Reporting / Disclosure | frameworks/obligations in scope + owner | D-18 | **yes** |
| 19 Decision / Reduction | target/scenario methodology, framing limits | D-19 | **yes** |
| 1–4, 10 | none | — | no |

## 9.2 Non-family decisions that still gate this programme

| Decision | D-ID | Affects |
| --- | --- | --- |
| Retention durations per domain | D-01 | L7, and therefore the Insight ledger lifecycle |
| Deletion semantics | D-02 | L7 + Insight ledger |
| Legal hold | D-03 | L7 |
| Erasure scope / account deletion | D-04 | L7 + Insight ledger |
| Storage-object propagation | D-05 | L7 |
| Export scope | D-06 | L7 + family 16 (E4 as export vs surface) |
| Provider / privacy retention | D-07 | narration across families 1–19 + the Insight ledger |
| Backup retention + RTO/RPO | D-08 | L8-A |
| Commercial decisions (provider, model, plans, entitlements, overage, refunds, failure handling, SLA) | D-20…D-26 | L8-B |
| Committing the untracked PO reference documents | D-27 | repository durability |
| Reconciling the X2/X7 contract records | D-28 | L8-A record truth |
| Pre-existing reviewer/SLA failures | D-29 | regression baseline |

## 9.3 Decision rules this matrix applies

1. **No invented values.** Where the repository does not establish a duration, threshold, rule, taxonomy or price, the matrix says `PO DECISION REQUIRED`.
2. **No capability policy inferred from code.** The existence of `SCOPE2_METHODS`, `ghg_protocol_category` or `scope_hint` does **not** establish an accounting policy.
3. **No production inference from demo readiness**, and **no production inference from `APPROVE`**.
4. **No new D-ID invented for an existing decision** — and where a genuine gap exists (family 15) the gap is recorded rather than papered over.

---

# 10. Package dependency map

## 10.1 The planning sequence (from the master preflight — restated, **not authorized here**)

```
P1 — Capability Coverage Matrix            ← THIS DOCUMENT is the P1 deliverable
        ↓
P2 — Temporal Comparison
        ↓
P3 — Data Quality + Audit/Reproducibility
        ↓
P12 — Investor-Demo Readiness Gate

then, each gated by its own decisions:
L7 governance decisions                     → P4
L8-A governance decisions                   → P5
Supplier decision                           → P6
Scope 3 decision                            → P7
Scope 2 / Scope 1 decisions                 → P8 (P8a / P8b)
P2 + taxonomy stability + variance decision → P9
Knowledge / reporting / reduction decisions → P10 (P10a / P10b / P10c)
Commercial decisions                        → P11
```

## 10.2 Dependency edges that actually constrain ordering (verified)

| Edge | Why it is real |
| --- | --- |
| **P2 → P9** | attribution requires a defined comparison basis |
| **P7/P8 → P9** | attribution requires a stable dimension to decompose along |
| **D-13 (factor history) → factor attribution in P9** | the snapshot retains the factor *used*, not candidate/stage history |
| **P6 → supplier variance** | the supplier dimension returns `NO DATA` until persistence exists (family 9) |
| **P3 ↔ family 16** | the audit/reproducibility contract and the data-quality summary share the same authoritative stores |
| **L7 ↔ Insight ledger** | `backend/data/insight.py` and `backend/data/insight_interactions.py` raise `NotImplementedError` citing I7/Q12 — a retention package must cover the Insight ledgers or state why it does not |
| **P2/P3 → P12** | the demo gate can only promise what is implemented |
| **L8-B ⟂ families 1–19** | commercial work is independent of Insight capability work |
| **L8-A ⟂ families 1–19** | operational governance is independent of Insight capability work |

## 10.3 What is *not* a dependency (avoiding false sequencing)

* Families **1–4** and **10** require no new decisions — regression only.
* Family **14** (data quality) needs **no schema change** — it reads existing stores.
* Family **11** needs **no schema change** — the data basis exists.
* Family **16**'s **E3** chain needs no schema change; only **E4** might, depending on **D-16**.
* Family **17** has no dependency on any other family — only governance.

## 10.4 Exclusions preserved in the sequence

High-risk domains are **never combined** in one package: accounting taxonomy redesign (P7/P8), L7 data lifecycle (P4), commercial billing (P11) and production deployment remain separate authorizations.

---

# 11. Investor-demo capability map

**This section is an assessment, not an implementation plan, and passing its gate would not constitute production authorization.** The demo infrastructure that exists (verified) is `tools/demo_lab/` (lab, provision, stack, storage, verify, `run_demo_lab.sh`, `reset_demo_lab.sh`, the T3 corpus harness, factor seeding) with verification records `docs/demo-investor/DR-001…DR-007`.

## 11.1 Demoable now (verified capability)

| Family | Demo behaviour |
| --- | --- |
| 1 Identified Calculation | ask about a specific calculation → deterministic figures → open evidence |
| 2 Discovery | “find the calculation with this amount/date/activity”, including the `multiple_matches` honesty state |
| 3 Aggregation | totals by scope / month / year / activity / facility / asset |
| 4 Aggregate Provenance | “which calculations make up this total?” → bounded component list |
| 5 Scope Analysis (totals only) | scope split |
| 10 Facility / Asset | per-site and per-asset totals |
| 16 Evidence (E3) | report → version → calculation → source line → viewer |
| 18 Reporting (existing reports) | open an existing report and reach its evidence |
| Platform | authentication/personas, tenant isolation, answer states (incl. `rate_limited`), truthful `no_data` |

## 11.2 Demoable only with an explicit truthful limitation

| Family | Limitation the presenter must state |
| --- | --- |
| 9 Supplier | supplier analytics return **no data** today because the emission write path does not populate the supplier key |
| 5 Scope Analysis | comparison between scopes is **not** implemented |
| 13 Factor Intelligence | the factor *used* is explainable; **candidate/rejection history is not retained** |
| 16 Evidence | **E3, not E4** — there is no audit package and **no certification** of any kind |
| 18 Reporting | existing reports are reachable; **framework/obligation mapping is not implemented** |
| L7 (if raised) | retention is configurable and only **two** domains are enforced; there is **no** legal hold, erasure or storage-object deletion path |

## 11.3 Not demoable — unsupported

| Family | Why |
| --- | --- |
| 6 Scope 3 Categories 1–15 | no taxonomy/dimension exists |
| 7 Scope 2 market-based | no method-aware calculation exists |
| 8 Scope 1 decomposition | no classification exists |
| 11 Temporal Comparison | no comparison capability exists |
| 12 Variance / Attribution | no attribution engine exists |
| 14 Data Quality (as an Insight answer) | signals exist but are not exposed to Insight |
| 15 Methodology / Boundary | no boundary model / explanation contract |
| 17 Concept knowledge | no governed knowledge layer |
| 19 Decision / Reduction | no target/scenario model |

**Rules for the demo (non-negotiable):** no fabricated emissions; no invented evidence; no unsupported accounting classification presented as fact; no “AI calculated this” framing; no audit-certification claim; no production-readiness claim; every claim traceable to a screen the audience can see.

## 11.4 Production-critical but deliberately excluded from demo readiness

Live RLS verification against a real database; OCR capacity (the documented Render 512 MiB OOM incident); deploy-time migration-drift gating; backup/restore cadence including a documented restore verification; secrets-ownership policy; SLO/alerting thresholds and recipients; incident-response runbook; the complete L7 lifecycle; billing/PSP; I7/I8 as stages; production deployment. **None of these may be implied by a demo.**

---

# 12. L7 / L8 dependency map

Nothing in this section is implemented or authorized by this matrix. It records **what exists** versus **what remains governance**, and how each relates to Insight.

## 12.1 L7 — data lifecycle

### Existing mechanism (verified)

| Capability | Evidence |
| --- | --- |
| Configurable retention | `system_settings` columns (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days`) read/written by `backend/data/settings.py`; unset returned as `None` |
| Retention API | `GET` / `PUT /api/v3/settings/retention` (`backend/api/v3_settings.py:72,82`) |
| Server-side enforcement | `backend/services/retention.py` (`_ELIGIBLE_DOMAINS`, `build_policy`, `enforce_retention`); CLI `python -m tools.enforce_retention` (dry-run by default) |
| Document lifecycle | `organization_files.expire_documents_older_than` — **soft-delete only** (`deleted_at`) |
| Never-purge invariant | `_TELEMETRY_EXCLUDED_TABLES` — 8 tables incl. `audit_trail`, `evidence_line_items`, `calculation_snapshots`, `emissions_logs` |
| Export | `/api/v3/exports/emissions.csv`, `/emissions.json`, `/documents.csv`, `/audit-package.json` |
| Backup/recovery | `tools/backup_recovery_drill.py` + `docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md` |

### Unenforced / absent (verified), with the governing decision

| Gap | Governing decision |
| --- | --- |
| `audit_log_retention_days`, `data_retention_days`, `backup_retention_days` configured but **not enforced** | **D-01** |
| Legal hold absent | **D-03** |
| No erasure / account-deletion path | **D-04** |
| No storage-object deletion propagation | **D-05** |
| Insight interaction/conversation ledger has **no delete surface** (`NotImplementedError`, deferred to I7) | **D-02 / D-04 / D-07** |
| Export scope not formally defined | **D-06** |
| Provider/privacy retention not defined | **D-07** |
| Backup retention + RTO/RPO not defined | **D-08** |

### Insight ↔ L7 edges

* Retention enforcement **must not** weaken the never-purge invariant without a PO decision — audit/evidence integrity underpins families 4 and 16.
* Any L7 package **must** address the Insight ledgers (or state why not), because those rows are retained indefinitely by construction today.
* E4 (family 16) may be an **export** or an **on-screen** surface — that choice is **D-06 / D-16** and interacts with L7's export scope.

## 12.2 L8-A — technical resilience / operations

| Existing (verified) | Remaining governance |
| --- | --- |
| `/health` probing Supabase **and** the DB pool independently (`backend/main.py:322`) | readiness/liveness split; dependency-degradation matrix |
| API runtime metrics — `services/api_metrics.py`, `data/api_metrics.py`, `domain/api_metrics.py`, wired at `main.py:274-288`, with unit and live integration tests | external monitoring/alerting integration (none found) |
| Operational alerting — `services/operational_alerting.py` + its runtime integration test; notification/delivery stores in `data/notifications.py` | **SLO/SLA targets** and alert **thresholds/recipients** (`PX-6` forbade inventing them) — `PO DECISION REQUIRED`; the X2/X7 contract records still read “BLOCKED” (**D-28**) |
| Technical rate limiting — **CLOSED under INS-01** (20/5/2 user, 100/20/10 org, both execution routes) | none — do not duplicate |
| Backup/recovery drill tool + drill document | **RTO/RPO** and restore-verification cadence (**D-08**) |
| Deployment records (`docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`, `MIGRATION_DRIFT_GATE_RUNBOOK.md`, `.github/workflows/migration-drift.yml`) | production deployment remains **NOT AUTHORIZED** |
| Configuration via 127 `os.getenv` sites; provider access configuration-gated; no tracked `.env` | **secrets-ownership/rotation policy**; **incident-response runbook** (none found, though the Render OOM incident is documented inside a test) |

**Insight ↔ L8-A edges:** the limiter already covers both Insight execution routes, so any **new** Insight execution route must join the same limiter (a route without it would be a regression). Metrics and alert thresholds are operational policy and must not be invented inside an Insight package.

## 12.3 L8-B — commercial

> **Existing configurable commercial data model ≠ production billing.**

| Existing (verified in code) | What it actually is |
| --- | --- |
| `backend/domain/billing.py` — `BillingPlan`, `CommercialConfig`, `CreditLedgerEntry`, `Subscription`, `BillingOrder`, `StorageUsage`, `PaymentRecord`, `IdempotencyKey` | a **configurable data model** |
| `backend/data/billing.py` — plan versioning (`publish_new_version`, `history`, `get_version`), commercial config, credit ledger with `balance()`, subscriptions (`get_active_for_org`, `upsert_active`), assisted/managed orders (`create`, `update_status`, `mark_approved`, `mark_completed`), storage usage | repositories — **not** a billing service |
| `backend/api/v3_billing.py` — `/me`, `/me/credits`, `/me/orders`, `/me/orders/{id}`, `/me/payments`, `/me/storage/refresh`, `/orders/assisted`, `/orders/{id}/approve`, `/orders/{id}/cancel`, `/managed/orders` | an **operator-assisted** flow (an operator approves) |
| Migrations `20260824020000_d37_0_billing_security_and_configurable_subscription.sql` and `20260824030000_d37_master_commercial_billing.sql`; `frontend/src/v3/customer/BillingPage.jsx`; `docs/business/`, `docs/Pricing/` | schema + UI + commercial design records |

**Absent (verified):** PSP integration (no Stripe/PayPal/Gocardless/Adyen/Paddle SDK anywhere); webhooks and signature verification; invoices; dunning; refunds; overage charging; entitlement enforcement on feature routes; tax/VAT; commercial SLO/DR.

**Governing decisions:** D-20 (provider), D-21 (model), D-22 (plans/prices), D-23 (entitlements), D-24 (overage/credits/refunds), D-25 (failure handling), D-26 (SLA/metering).

**Insight ↔ L8-B edge:** the INS-01 rate limiter is a **security control, not an entitlement** (closure §11). No family in §4 may be gated by a commercial quota until **D-23** is decided, and no billing work belongs inside an Insight package.

---

# 13. Current gaps

## 13.1 Capability gaps (ordered by blocking factor)

| # | Gap | Family | Nature |
| --- | --- | --- | --- |
| G-1 | No Scope 3 category taxonomy or assignment rule | 6 | **Accounting policy + schema** |
| G-2 | No market-based Scope 2 calculation or instrument model | 7 | **Accounting policy + schema** |
| G-3 | No Scope 1 decomposition classification | 8 | **Accounting policy + schema** |
| G-4 | Supplier key never populated on the emission write path | 9 | **Policy (capture/backfill)** |
| G-5 | No deterministic period comparison | 11 | Contract + PO comparison basis |
| G-6 | No variance/attribution engine | 12 | Methodology + schema likely |
| G-7 | Factor candidate/stage history not retained | 13 | Retention policy (**D-13**) |
| G-8 | Data-quality signals exist but are not exposed as an Insight answer | 14 | Exposure only |
| G-9 | No methodology/boundary explanation contract or boundary model | 15 | **Policy (no D-ID yet)** |
| G-10 | No Insight-level “reproduce this number” contract; E4 undefined | 16 | Policy (**D-16**) |
| G-11 | No governed concept-knowledge layer | 17 | Governance + schema |
| G-12 | No framework/obligation mapping for disclosure questions | 18 | Policy (**D-18**) |
| G-13 | No target/scenario model | 19 | Policy + schema |
| G-14 | No aggregation **filtering** by dimension (only group-by) | 3, 5 | Contract (new authorization) |
| G-15 | No cross-tabulation | 3 | Explicitly not authorized today |

## 13.2 Platform gaps that affect Insight

| # | Gap | Evidence | Governing decision |
| --- | --- | --- | --- |
| G-16 | Three configured retention domains unenforced | `services/retention.py::_ELIGIBLE_DOMAINS` | D-01 |
| G-17 | No legal hold / erasure / storage propagation | repository-wide absence | D-03, D-04, D-05 |
| G-18 | Insight ledgers have no delete surface | `NotImplementedError` in `data/insight.py`, `data/insight_interactions.py` | I7 / D-02, D-04 |
| G-19 | Provider/privacy retention undefined | no provider-retention surface | D-07 |
| G-20 | No RTO/RPO or restore cadence | drill tool only | D-08 |
| G-21 | No committed SLO or configured alert thresholds/recipients | `services/operational_alerting.py` exists; SLA config columns unreferenced in code; `sla_definitions` had 0 rows at audit | D-26 (commercial) / L8-A governance |
| G-22 | No incident-response runbook | `docs/operations/` has no incident runbook; the Render OOM incident lives in a test | L8-A governance |
| G-23 | No secrets-ownership/rotation policy | 127 `os.getenv` sites; no tracked `.env` | L8-A governance |
| G-24 | No PSP/invoicing/dunning/refund/entitlement capability | verified absence | D-20…D-26 |
| G-25 | X2/X7 contract records contradict code (X-4) | docs vs code | D-28 |
| G-26 | `AGENTS.md` §54 references a non-existent demo manifest path (X-5) | filesystem | D-27-adjacent / new correction decision |
| G-27 | Pre-existing test failures (stale migration pin; three review-SLA assertions) | OHD baseline comparison | D-29 |
| G-28 | Pre-existing cross-tenant factor-metadata exposure | closure §8.6 | already tracked separately |

## 13.3 Gaps that are *not* real (avoid false work)

* **Families 1–4 are complete** within their authorized scope and need no remediation.
* **The deterministic core is sound** — no gap was found in calculation, snapshot immutability, or unit normalization that would block any family in §4.
* **Rate limiting is closed** — do not re-implement.
* **Evidence-destination architecture is correct** — do not build a second viewer.
* **The demo lab needs no rebuild** — it exists, is idempotent, and protects the investor dataset.

---

# 14. Recommended sequencing

**Recommendation only — the PO decides and authorizes.** Derived from §4 (what is blocked on what) and §10 (dependency edges).

| Order | Item | Why now | Blocked by |
| --- | --- | --- | --- |
| 1 | **P1 (this matrix)** | zero-risk planning artifact; unblocks every later boundary | — |
| 2 | **P2 — Temporal Comparison** | no schema change; the data basis exists; only **D-11** is needed | D-11 |
| 3 | **P3 — Data Quality + Audit/Reproducibility** | reuses existing stores; no schema change; only **D-14 / D-16** needed | D-14, D-16 |
| 4 | **P12 — Investor-Demo Readiness Gate** | converts existing capability into a repeatable, truthful demo; no schema/API change | order 2–3 preferred |
| 5 | **P5 / P4** (L8-A governance; then L7 lifecycle) | needed before any operational or lifecycle promise; each needs its decision set | D-08…D-12 (P5); D-01…D-07 (P4) |
| 6 | **P6 — Supplier persistence** | unlocks supplier analytics and unblocks supplier variance | D-09 |
| 7 | **P7 — Scope 3 taxonomy**, then **P8 (P8a Scope 2, P8b Scope 1)** | the largest accounting-model work; must follow its decisions exactly | D-13; D-10, D-15 |
| 8 | **P9 — Variance / Attribution** | requires comparison + taxonomy + variance methodology | D-12 (+ P2, P7/P8) |
| 9 | **P10a/b/c** (knowledge, reporting assistance, reduction) | governance-heavy; lowest structural risk to existing capability | D-17, D-18, D-19 |
| 10 | **P11 — Commercial billing** | extreme risk surface; independent of Insight | D-20…D-26 |

**Deliberately excluded from this recommendation:** production deployment (separate release authorization), consultant/auditor Insight personas (separate PO decisions), and remediation of accepted INS-01 observations (not authorized).

---

# 15. Explicit non-authorizations

Creating this matrix **did not and does not** authorize any of the following. All remain outside the authorization boundary.

## 15.1 Implementation

* any application, backend or frontend code change;
* any database table, column, index, constraint or **migration**;
* any API route, tool, schema or answer-state change;
* any test change;
* any configuration or environment change.

## 15.2 Capabilities

* Scope 3 Categories 1–15; market-based Scope 2; Scope 1 decomposition;
* supplier persistence or supplier-analytics enablement;
* temporal comparison; variance/attribution; factor-history expansion;
* data-quality Insight exposure; methodology/boundary model;
* audit/reproducibility (E4) package; governed knowledge layer (Mode E);
* reporting/disclosure obligation mapping; decision/reduction intelligence;
* aggregation filters or cross-tabulation;
* any **eighth** Insight tool.

## 15.3 Platform governance

* **L7**: retention durations, enforcement of the unenforced domains, legal hold, deletion, erasure, storage-object deletion, provider/privacy retention, backup/RTO/RPO, export scope, Insight-ledger lifecycle;
* **L8-A**: SLO/SLA commitments, alert thresholds/recipients, incident runbook, secrets policy, restore cadence, monitoring integration;
* **L8-B**: any payment provider, pricing, plan catalogue, entitlement, overage, refund, credit, invoice, dunning, tax or commercial SLA;
* **I7** and **full I8** as stages (INS-01 technical rate limiting remains closed as recorded);
* production deployment, environment promotion and production configuration.

## 15.4 Documentation and records

* modification of the untracked PO/ChatGPT-supplied documents (Question Library, architecture references, capability decision matrix);
* reconciliation of the X2/X7 contract records (X-4);
* correction of `AGENTS.md` §54 (X-5);
* remediation of the pre-existing test failures (D-29) or the pre-existing factor-metadata exposure (closure §8.6);
* reopening or remediating any INS-01 non-blocking observation (closure §8.1–§8.8);
* modification of `tools/demo_lab`, the investor demo dataset, or the external pinned synthetic-document generator.

## 15.5 Claims

* no certification, accreditation or assurance claim is made or implied;
* no competitive exclusivity claim is made;
* no production-readiness claim arises from anything in this document.

**The only changes made by the P1 task are the two documentation files named in §16.3.**

---

# 16. Verification requirements

## 16.1 Verification of this matrix (documentation-only package)

| Requirement | How it was satisfied |
| --- | --- |
| All 19 families present | §4.1–§4.19, each with the full required field set |
| Every substantive capability claim traceable to a source | source hierarchy §2.1; per-family citations to code paths, migrations, tests, PO records and the preflight |
| Implementation-status claims checked against code/history | symbol, route, constant and migration verification performed against the repository at `8916f82` (companion implementation report §6) |
| No future package described as already implemented | statuses distinguish EXISTS / PARTIAL / MISSING / NOT AUTHORIZED; `APPROVE` explicitly ≠ authorization (§9) |
| Unresolved PO decisions remain unresolved | §9.1–§9.2 list D-IDs without choosing options; family 15 records a **missing** decision rather than inventing one |
| Conflicts identified, not silently reconciled | §2.3 conflict register X-1…X-6 |
| Question Library treated as a coverage catalogue | §5.1 — no 426 row-by-row implementation list |
| INS-01 not reopened; no eighth tool invented | §3.2 (seven tools); §15 |
| E4 not claimed | §6 — the E4 column reads “PO-defined” / “PO decision” throughout |
| Single evidence destination preserved | §6 principle 1; §8.2 |
| Application tests | not required for a documentation-only package — **none were run and none were modified** |

## 16.2 Standing verification requirements for any future package

Every future package (P2–P12) must define, **before implementation**:

1. exact scope, permitted files/areas and prohibited changes;
2. required tests — unit, API, workflow, and **ALLOW + DENY** security cases;
3. evidence/provenance acceptance criteria (which E-level it claims and how it is demonstrated);
4. bound assertions for any new result-producing path;
5. a permanent implementation report;
6. independent OHD verification against a frozen commit, including a **disposable** database for any destructive test (F-046-1: never the investor demo, persistent QA or production);
7. PO closure.

## 16.3 Verification of the P1 task's own repository impact

| Check | Result |
| --- | --- |
| Files created by P1 | `docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md` and `docs/architecture/CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md` — **the only two changes** |
| Application code / migrations / tests / frontend / configuration modified | **none** |
| Migrations created | **none** |
| Untracked PO/ChatGPT documents staged or modified | **no** |
| Secrets introduced | **none** |
| Demo infrastructure / investor data / external synthetic generator touched | **no** |

---

# 17. PO approval boundary

## 17.1 What the PO is being asked to do with this document

1. **Review the coverage assessment** in §4 and §5 — in particular the **4 EXISTS / 6 PARTIAL / 9 MISSING** split, the data-empty supplier family, and the **missing decision for family 15**.
2. **Confirm or correct the conflict register** (§2.3) rather than leaving X-1…X-6 implicit.
3. **Resolve, or explicitly defer, the decisions** in §9.1–§9.2 that gate each family.
4. **Authorize the next bounded package** (§14 order 2 or 3) with its own scope, tests, permanent report and stop conditions.

## 17.2 What this document cannot do

* It cannot authorize implementation of any capability or package.
* It cannot close any capability.
* It cannot substitute for Cline implementation, OHD verification or PO closure.
* It cannot be cited as evidence that any capability is production-ready, certified, or commercially available.

## 17.3 Effect of PO approval

PO approval of this matrix establishes it as the **planning baseline** for subsequent bounded authorizations. Each authorization must still state its own scope, exclusions, tests, evidence requirements and stop conditions, and must still be followed by independent OHD verification and PO closure.

---

# Final status

| Item | Value |
| --- | --- |
| Matrix status | **PRODUCED — PLANNING / GOVERNANCE ONLY** |
| Families covered | **19 of 19** |
| Capability status split | EXISTS **4** · PARTIAL **6** · MISSING **9** |
| Tools in the catalogue | **7** (no eighth tool exists or is implied) |
| Answer states | **15** (unchanged by this document) |
| E4 claimed anywhere | **No** |
| Open PO decisions referenced | **D-01 … D-29**, plus one identified **missing** decision for family 15 |
| Conflicts identified | **6** (X-1 … X-6), none silently reconciled |
| Packages proposed (not authorized) | **P1 … P12** |
| Implementation performed | **none** |
| Authorization created | **none** |

---

> **This matrix is a planning and governance artifact. It does not authorize implementation of any capability or package. Each future package requires a separate bounded PO authorization followed by Cline implementation, independent OHD verification, and PO closure.**
