# CT-P8-INSIGHT-QUESTION-LIBRARY-CAPABILITY-GAP-20260922

**Task:** Second read-only forensic capability analysis, against the CarbonTally Insight Question Library.
**Kind:** Analysis / forensics. **No implementation. Nothing here authorizes work.**
**Date:** 2026-09-22 · **Author:** Cline (implementation agent).
**Baseline:** `docs/architecture/CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922.md` (commit `669669a`). This report extends that baseline; it does not restate it.
**Legend:** `[FACT]` code/repository-verified · `[REF]` requirement from the Question Library/reference · `[INFER]` reasoned from ≥2 verified facts · `[GOV]` governance decision required · `[BLOCKED]` cannot proceed without an unissued decision.

---

## 1. Executive summary

**Verdict.** CarbonTally's authoritative **data foundation is substantially broader than the Insight surface that can reach it**. For most Question-Library families the raw authoritative data exists in `emissions_logs`, `calculation_snapshots`, `evidence_line_items`, `manual_extraction_items`, `emission_factors`/`customer_factors` and the disclosure tables — and for several families a **deterministic backend aggregation already exists** (scope, activity, asset, facility, month, year, supplier, snapshot history). But **Insight can reach none of it**: the closed I3 catalogue exposes four identifier-only tools, so every aggregate/comparison/driver/data-quality question in the library is unreachable today, regardless of whether its backend foundation exists.

Three findings materially change the picture given in the first gap report and must not be glossed over:

1. **The supplier dimension is structurally wired but not populated.** `emissions_logs.supplier_id` exists in the schema with an FK to `public.suppliers`, and `aggregate_by_supplier()` joins and groups on it — but **no application write path ever sets it**: the only `INSERT INTO public.emissions_logs` in application code (`data/emissions_logs.py:126-142`) and the only `UPDATE` (`save()`, lines 419-446) both omit `supplier_id`. Unless legacy/DB-side data exists (DB contents not inspected — see §9.1), every supplier aggregate collapses to `supplier_id='none'` / `supplier_name='Unassigned'`. The supplier *relationship* is captured upstream (`manual_extraction_items.mapped_supplier_id`, `document_processing.ai_mapped_supplier_id`) and is **not propagated into the emission record**. This makes the entire supplier question family (§9) a **data-model/pipeline gap first and a governance gap second**.
2. **Scope 2 location-vs-market is modelled at the disclosure layer only.** `domain/disclosure.py` defines `SCOPE2_METHODS = ("LOCATION_BASED", "MARKET_BASED")` and the disclosure requirement schema constrains `scope2_method_hint` to exactly those two values — but neither `emissions_logs` nor `calculation_snapshots` has any scope-2-method column, and no emission-factor or snapshot field records a market-based instrument. The library's comparison question ("why are location-based and market-based Scope 2 different?") therefore cannot be answered from the calculation layer; it can only be answered from disclosure-layer rows *if* they are populated for both methods (not established by this analysis).
3. **A cross-tenant aggregate leak already exists in a factor endpoint.** `GET /api/v3/emissions/factors/{factor_id}` returns `usage.snapshot_count` and `usage.first/last_calculated_at` from `snapshot_count_for_factor()` / `factor_usage_span()`, whose SQL has **no `organization_id` predicate** (`data/emissions_logs.py:387-409`). These are platform-wide usage statistics exposed to any organisation member. Counts and timestamps only (no content, no customer data), so severity is low — but it is a pre-existing cross-tenant disclosure that a future analytical surface must not repeat, and it is exactly the "aggregate without organization restriction" pattern the task asks about.

**The central distinction, stated plainly.** For almost every family the answer to *"does CarbonTally possess the authoritative data + deterministic capability?"* is **yes or partly**, while the answer to *"can Insight invoke it?"* is **no**, for two independent reasons: the I3 catalogue is closed (governance), and — for date/amount/ambiguity-based questions — no discovery or ambiguity contract exists at all (contract).

---

## 2. Documents examined

* `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md` (971 lines; **currently untracked** in git) — read in full. 426 numbered example questions across 43 sections.
* `docs/architecture/CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922.md` (commit `669669a`) — the baseline this report extends.
* `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md` (untracked) — architecture requirements.
* `docs/architecture/CT-P8-PO-DECISION-INVENTORY-20260922.md` §0/§C, `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` §3.5/§5/§6/§8/§11, `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` §F, and the 2026-09-22 viewer closure — for the closed-contract and non-authorization facts.
* Code: enumerated in §27.

---

## 3. Baseline implementation state (as it bears on this analysis)

Not repeated from the baseline report; only the facts this analysis depends on, re-verified at HEAD `669669a`:

| Fact | Evidence |
| --- | --- |
| I3 = exactly four identifier-only tools (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`) | `domain/insight_tool.py:83-123`; `services/insight_tools.py:83-123` |
| I3 `ToolStatus` = 6 values; I4 `AnswerStatus` = 14 values; **no `multiple_matches`** | `domain/insight_tool.py:39-51`; `domain/insight_interaction.py:58-71` |
| Insight intent = deterministic keyword routing; parameter extraction = **UUIDs only** | `services/insight_tools.py:149-173`; `services/insight_interactions.py:174-190` |
| Insight narration = allowlisted tool output + bounded context; no aggregation input exists | `services/insight_interactions.py:415-447` |
| Insight UI is authenticated-only (`/insight`), 14 states, evidence handoff to the shared viewer | `frontend/src/App.js:2072`; `frontend/src/v3/insight/*` |
| No RAG/embeddings/vector search/LangChain anywhere; one provider abstraction | grep of application code (`infra/llm_client.py` only) |
| Code unchanged since the OHD-verified viewer HEAD | `git diff --name-only 5d5f7ed..HEAD -- backend/ frontend/ supabase/ prisma/` = empty |

**Deterministic backend capabilities that exist OUTSIDE Insight** (this is the crux of §19–§20). All are `[FACT]`:

| Capability | Where | Org-scoped in SQL? |
| --- | --- | --- |
| Period totals + `by_scope` + `by_month` + `by_asset` + `by_facility` + `by_supplier` + `by_activity` | `GET /api/v3/emissions/dashboard` (`api/v3_emissions.py:247-281`) | yes (`aggregate`, `aggregate_by_*`) |
| Scope 1/2/3 totals over a period | `GET /api/v3/emissions/scope-breakdown` (`:284-299`) | yes |
| Calculation history by period (bounded, newest-first) | `GET /api/v3/emissions/calculations` (`:307-330`) via `list_snapshots`/`count_snapshots` | yes |
| One calculation + its factor and customer-factor rows + provenance | `GET /api/v3/emissions/calculations/{snapshot_id}` (`:331-370`) | yes (post-read org check) |
| Factor search with provenance filters (year, country, scope, unit, source, set, provider) | `GET /api/v3/emissions/factors` (`:582-615`) | global factor catalogue (expected) |
| Factor detail + usage statistics | `GET /api/v3/emissions/factors/{factor_id}` (`:618-647`) | **usage stats are NOT org-scoped** (§22) |
| Emission → evidence chain with DM-6 gating and signed URL | `GET /api/v3/emissions/{log_id}/evidence` (`:372-560`) | yes |
| Reproducibility check (recompute and compare) | `POST /api/v3/emissions/calculations/{snapshot_id}/verify` (`:562`) | yes |
| Consultant client dashboard (scope/asset/facility) | `GET /api/v3/consultants/clients/{client_id}/dashboard` (`api/v3_consultants.py:1205-1230`) via `_authorized_client_org` | yes (consultant grant) |
| Consultant calculation history | `api/v3_consultants.py:1378-1379` | yes |
| Benchmarking (multi-year comparison, facility/business-unit) | `POST /api/v2/benchmark` (`api/business.py:13,186`) → `engines/benchmarking.py` | engine-level; legacy v2 surface |
| Evidence line resolution (viewer) | `GET /api/v3/evidence/line-items/{id}` (`api/v3_evidence.py:103`) | yes (SQL + API) |
| Data-quality-ish signals | `repos.reporting.audit_readiness` (`data/reporting.py:1100-1130`); `data/exports.py::_evidence_status`; `public.issues` (`data/issues.py`) | yes |

---

## 4. Question-library capability taxonomy

The 426 questions cluster into **20 capability families**. Question counts are indicative (a question can touch two families; the dominant intent is used).

| Family | § in library | ~Questions | Core intent |
| --- | --- | --- | --- |
| F1 Total footprint / scope distribution | §3 | 15 | totals by scope/year |
| F2 Scope 1 detail (fuel/combustion/fugitive/process) | §4 | 20 | scope-1 decomposition |
| F3 Scope 2 (location/market) | §5 | 20 | dual-reporting totals |
| F4 Scope 3 overall | §6 | 24 | scope-3 totals, changes, completeness |
| F5 Scope 3 categories 1–15 | §7–§21 | 105 | per-category totals, drivers, method |
| F6 Supplier analytics | §22 | 16 | supplier ranking/drivers/quality |
| F7 Emission-factor intelligence | §23, §33 | 43 | factor metadata, selection, change |
| F8 Calculation explanation | §24, §25 | 41 | how a figure was produced |
| F9 Activity/input questions | §25 | 20 | activity, quantity, unit, facility, supplier, source |
| F10 Trend / variance / hotspots | §26 | 18 | comparisons and attribution |
| F11 Data-quality intelligence | §27, §34 | 38 | missing evidence, estimates, secondary data |
| F12 Evidence / provenance | §28 | 21 | trace to document/line/snapshot |
| F13 External-auditor questions | §29 | 40 | verifiability, reproducibility, methodology |
| F14 Consultant investigation | §30 | 20 | hotspots, prioritisation, sampling |
| F15 Boundary / methodology | §31 | 12 | organisational/operational boundary |
| F16 Reporting / disclosure | §32 | 15 | report/version/disclosure context |
| F17 Factor-selection challenge | §33 | 16 | why this factor, alternatives, transformation |
| F18 Evidence-quality challenge | §34 | 15 | reconciliation, provenance gaps, manual intervention |
| F19 Clarification-required set | §36 | ~12 | ambiguity handling |
| F20 Concept / no-authoritative-data sets | §35-E, §37 | ~20 | governed knowledge; truthful "no data" |

`[FACT]` Of these, **only F12 (part) and F13 (part)** can be answered today, and only when the question carries an identifier. `[REF]` The library itself states that "the presence of a question in this document does **not** mean CarbonTally currently supports it" and that each capability needs its own deterministic contract and governance decision (§40, §42).

---

## 5. Scope 1 capability analysis

| Question (library §4) | Backend data | Deterministic backend | Insight | Verdict |
| --- | --- | --- | --- | --- |
| 21 "What are my Scope 1 emissions?" | `emissions_logs.scope='Scope 1'`, `calculated_kg_co2e`; snapshots likewise | `aggregate(org, period, "scope")` + `scope-breakdown` | not reachable | **Backend yes / Insight no** |
| 22 "Which activities are included in Scope 1?" | `calculation_snapshots.activity_type` + `scope` | `aggregate_by_activity` (**no scope filter**) | not reachable | backend partial (no scope filter) |
| 23 "Which facilities generate the most Scope 1?" | `metadata->>'facility_id'`, `asset_id` | `aggregate(..., "facility")` (**no scope filter**) | not reachable | backend partial |
| 24 "Which fuels contribute most to Scope 1?" | fuel identity lives in the `activity`/`activity_type` text (e.g. `Fuels > Liquid fuels > Diesel … [litres]`); **no fuel dimension column** | `aggregate_by_activity` groups by `activity_type` | not reachable | **partial foundation**: answerable only by string grouping, not by a governed fuel dimension |
| 25–28 stationary / mobile / fugitive / process | **Not modelled.** No combustion-type, fugitive or process classification exists in schema, domain or factor metadata — only `activity_type` free text | none | not reachable | **NOT CURRENTLY POSSIBLE FROM STORED DATA** without a classification decision and a derived/stored dimension |
| 29–40 calculation explanation and evidence | snapshot fields + factor row + evidence chain | `calculations/{id}`, `{log_id}/evidence`, `/verify` | not reachable | backend yes; **Insight blocked by the I3 contract** |
| Scope 1 trends | `emissions_logs.start_date` | `aggregate(..., "month"/"year")`, benchmarking engine | not reachable | backend yes, no Insight path |

`[FACT]` Scope 1 today is a **stored label**, not a decomposition. The only scope-1 sub-dimensions that exist are whatever `activity_type` string (or customer factor) the matching produced, plus unit/asset/facility. `[GOV]` A governed combustion-type/fugitive/process classification is **new data + new governance**, not a new query.

---

## 6. Scope 2 capability analysis

### 6.1 Location-based

| Question | Backend data | Deterministic backend | Verdict |
| --- | --- | --- | --- |
| Total Scope 2 | `scope='Scope 2'`, `calculated_kg_co2e` | `aggregate(..., "scope")`, `scope-breakdown` | backend yes / Insight no |
| Facility Scope 2 | `metadata->>'facility_id'` | `aggregate(..., "facility")` (no scope filter) | backend partial |
| Electricity consumption (kWh) | `raw_quantity` + `unit` for electricity activities | `aggregate` returns co2e only; **no kWh aggregation surface exists** (quantity is returned only by `aggregate_by_supplier`/`_by_activity`, neither scope-filtered nor exposed as an energy report) | partial: kWh totals are not exposed anywhere |
| Grid factor used | factor row for the snapshot (`factors.get`): `factor_source`, `factor_set`, `country`, `reporting_year`, `unit`, `scope`; snapshot keeps `factor_id`/`factor_source`/`factor_set`/`co2e_multiplier` | `calculations/{id}` returns the factor object | backend yes (for an identified calculation) |
| Geography / factor vintage | `emission_factors.country` / `.reporting_year` / `.factor_set` | `/factors` filters by country/year/set | backend yes (for an identified factor) |
| Trend | as Scope 1 | `aggregate(..., "month"/"year")` | backend yes / Insight no |
| Evidence | evidence chain + DM-6 | `{log_id}/evidence`, viewer | backend yes / Insight no |

### 6.2 Market-based

| Question | Finding |
| --- | --- |
| Market-based total | **Not available at the calculation layer.** `[FACT]` neither `emissions_logs` nor `calculation_snapshots` has a scope-2-method column, and no contractual-instrument, supplier-specific-electricity-factor or residual-mix concept exists in `emission_factors` (columns: `reporting_year, activity_type, co2e_multiplier, unit, scope, factor_source, factor_set, country, region_deprecated, import_batch_id`) or in `customer_factors`. |
| Supplier-specific electricity factors | **Not modelled as market-based.** A supplier factor could be entered as a *customer factor* (`factor_kind='customer_factor'`), but nothing marks it as market-based and there is no instrument/contract register. |
| Contractual instruments / residual mix | **Not modelled** — no concept and no data. |
| Disclosure-layer method hint | `[FACT]` `domain/disclosure.py:145 SCOPE2_METHODS = ("LOCATION_BASED","MARKET_BASED")`; the B1 disclosure migration constrains `disclosure_requirement_versions.scope2_method_hint` to exactly those two values; `disclosure_values` / `disclosure_value_evidence` are organisation-scoped tables with `value_status`, `value_kind`, `reporting_year` and evidence links. So a *disclosure-methodology* dimension exists — but it is a requirement/answer surface, **not a calculated Scope 2 method**. |

### 6.3 "Why are location-based and market-based Scope 2 different?"

`[FACT]` **Not answerable today.** The question needs (a) two computed Scope 2 figures under different methods, (b) the factor/instrument basis of each, and (c) a difference/attribution. CarbonTally stores (a) as a single un-methoded Scope 2 figure, has no instrument register for (b), and no reachable comparison capability for (c) — the benchmarking engine compares periods/facilities/business units, not accounting methods. `[GOV]` Answering it requires a market-based method definition, somewhere to record instruments/residual mix, a method dimension (or parallel disclosure-method computation), and explicit authorization.

---

## 7. Scope 3 overall capability analysis

| Question (library §6) | Backend data | Deterministic backend | Verdict |
| --- | --- | --- | --- |
| Total Scope 3 | `scope='Scope 3'` | `aggregate(..., "scope")`, `scope-breakdown` | backend yes / Insight no |
| Scope 3 **by category** | **No category dimension.** `[FACT]` no Scope 3 category field exists in schema, domain or services; `disclosure_requirement_versions` carries only `scope_hint` (no category enum) and no migration seeds categories; the only proxy is `activity_type` free text | none | **NEW DATA/SCHEMA REQUIRED** (governed category dimension), then aggregation |
| Category trends | as above | `aggregate(..., "month"/"year")` exists but is not category-aware | new capability |
| Category hotspots | as above | `aggregate_by_activity` (string grouping only) | partial foundation |
| Primary vs secondary data | **No primary/secondary flag anywhere.** Closest stored signals: `factor_kind` (`emission_factor` = CarbonTally catalogue vs `customer_factor` = customer-owned), `methodology`, `evidence_line_items.materialisation_kind` (`FORWARD`/`BACKFILL` = how the line was created, **not** data quality), `ai_confidence_score`, `ai_mapping_confidence`, `extraction_method` | none | **NEW DATA/SCHEMA REQUIRED**, or a PO-approved deterministic derivation rule |
| Estimated vs measured | partially derivable: `methodology='spend_based'` is persisted and set when a customer factor carries a currency unit (`engines/calculation.py:87-95`); `core/units.py` flags spend-based activities; `CalculationMethodology` = `direct_multiply \| distance_based \| spend_based \| area_based \| mass_balance` (`domain/calculation.py:21-28`) | snapshot `methodology` | **PARTIAL FOUNDATION** — "spend-based" is answerable; a general "estimated" concept is not |
| Supplier-specific data | captured upstream only (`manual_extraction_items.mapped_supplier_id`, `document_processing.ai_mapped_supplier_id`), **not** on the emission record | `aggregate_by_supplier()` (key unpopulated — §9) | **data-model gap** |
| Evidence completeness | `source_item_id`/`source_file`/`source_page`; `evidence_line_items`; readiness counts | `audit_readiness` (org-scoped), `_evidence_status` (per row) | backend yes (counts), but **not per category** |

---

## 8. Scope 3 categories 1–15

Column meanings: **DM** = represented as a first-class dimension in the data model; **EM** = emissions stored; **ACT** = activity data available; **SUP** = supplier information; **METH** = methodology; **FAC** = factor provenance; **EVID** = source evidence traceable; **AGG** = aggregation implemented; **INS** = exposed to Insight.

**Uniform findings applying to every category** (stated once rather than 150 times): `[FACT]`
* **DM = No for all 15.** No Scope 3 category dimension exists anywhere; `Scope 3` is the deepest stored classification.
* **EM = Yes**, but only as Scope 3 emissions attached to an `activity_type` (plus supplier/facility where present). A category total would have to be derived by mapping `activity_type` → category, which is not implemented and is a classification decision, not a query.
* **ACT = Yes** — `quantity`/`quantity_unit` on the snapshot; `raw_quantity`/`raw_unit` on the evidence line.
* **METH = Partial** — the snapshot stores `methodology` (5-value enum) and `algorithm_version`.
* **FAC = Yes for the *selected* factor** (`factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `factor_set`, `co2e_multiplier`); **No** for candidates/rejected factors.
* **EVID = Yes** where the chain is populated (source item/file/page, evidence line, viewer).
* **AGG = No for categories** (no category-aware aggregation exists). **INS = No.**

| Cat | Topic (library §) | Category-specific reality | Priority class |
| --- | --- | --- | --- |
| 1 | Purchased goods & services (§7) | spend-based vs activity-based derivable from `methodology`; "which suppliers contribute" blocked by §9; supplier-specific factors not marked as such | `NEW DATA/SCHEMA REQUIRED` (category) + supplier gap |
| 2 | Capital goods (§8) | same; no capital-asset register — `asset_id` is present only if supplied on the calculation | same |
| 3 | Fuel- and energy-related activities (§9) | "upstream of my electricity" needs a WTT/upstream-factor distinction — not modelled | same |
| 4 | Upstream transport (§10) | carrier/route/mode not modelled; tonne-km exists only as free-text quantity+unit where extracted | `NEW DATA/SCHEMA REQUIRED` |
| 5 | Waste (§11) | waste stream / treatment method not modelled (activity text only) | same |
| 6 | Business travel (§12) | travel mode/route not modelled; "distance vs spend" derivable from unit + `methodology` | same |
| 7 | Employee commuting (§13) | commuting mode and survey assumptions not stored | same |
| 8 | Upstream leased assets (§14) | lease register not modelled; facility link only | same |
| 9 | Downstream transport (§15) | as category 4 | same |
| 10 | Processing of sold products (§16) | sold-product register not modelled | same |
| 11 | Use of sold products (§17) | lifetime/use assumptions stored nowhere | same |
| 12 | End-of-life treatment (§18) | disposal-pathway assumptions stored nowhere | same |
| 13 | Downstream leased assets (§19) | tenant/asset register not modelled | same |
| 14 | Franchises (§20) | franchise locations not modelled | same |
| 15 | Investments / financed emissions (§21) | **PCAF-style investee/asset-class data entirely absent**; no financial-institution model | `NOT CURRENTLY POSSIBLE FROM STORED DATA` |

`[INFER]` Practical reading: category questions are answerable only if the organisation's `activity_type` strings happen to name the category — and even then no category total is computed, no category filter exists and nothing is exposed to Insight. `[REF]` The library itself records that GHG Protocol recommends collecting supplier methodology, factor/GWP data, assurance status and primary-data proportion — none of which CarbonTally stores.

---

## 9. Supplier capability analysis

### 9.1 Data availability — the decisive finding

| Layer | What exists | Evidence |
| --- | --- | --- |
| Schema | `public.suppliers` (name etc.); `emissions_logs.supplier_id UUID REFERENCES public.suppliers(id)`; `manual_extraction_items.mapped_supplier_id`; `document_processing_queue.ai_mapped_supplier_id`; `customer_documents.supplier_id` | `supabase/migrations/00000000000000_init_schema.sql:473, 596, 654, 798, 1152` |
| Extraction/mapping layer | supplier is captured and mapped (`mapped_supplier_id`, `ai_mapping_confidence`) | `data/manual_extraction.py:36,114,531-548`; `data/document_processing.py:42` |
| **Calculation write path** | **`supplier_id` is never written.** The only `INSERT INTO public.emissions_logs` in application code lists `organization_id, asset_id, emission_factor_id, start_date, end_date, raw_quantity, calculated_kg_co2e, created_by_user_id, created_at, updated_at, unit, scope, snapshot_id, metadata`; `save()` updates that same set. Neither includes `supplier_id`. | `data/emissions_logs.py:126-142` (insert); `419-446` (update) |
| Snapshot | no supplier column (`_SNAPSHOT_COLUMNS`) | `data/emissions_logs.py:53-59` |
| Read path | `aggregate_by_supplier()` groups by `l.supplier_id`, joins `public.suppliers` for the name, orders by co2e DESC | `data/emissions_logs.py:242-262` |
| Module claim | `api/v3_emissions.py:21-24` asserts "supplier via `emissions_logs.supplier_id`" as a real column mapping | `api/v3_emissions.py:21-24` |

`[FACT]` The supplier dimension is therefore **structurally wired but not populated by any application write path**. `[INFER]` Unless legacy data or a DB-side process populated it — the database was **not** inspected by this task — every `by_supplier` result collapses into one `'none'` / `'Unassigned'` bucket. This is a **pipeline/data-model gap** that precedes the governance gap: exposing supplier analytics to Insight would be meaningless until the relationship is persisted on the emission (or on the snapshot).

### 9.2 Capability answers

| Library question (§22) | Data | Backend | Scope/category filter | Period filter | Evidence | Insight | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 180 "Which suppliers generate the most Scope 3?" | key unpopulated | `aggregate_by_supplier` (co2e DESC) | **none** | yes (`start_date BETWEEN`) | component snapshots exist but the aggregate returns no ids | no | **partial foundation + data gap** |
| 181 "Top 10 suppliers by CO2e" | as above | same (no `LIMIT` — returns all, ordered) | none | yes | no ids returned | no | as above |
| 182 "Which supplier's emissions increased the most?" | as above | **no period-over-period supplier comparison** | none | n/a | n/a | no | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| 183/191/192 primary vs secondary / % primary | no primary/secondary flag | none | n/a | n/a | n/a | no | `NEW DATA/SCHEMA REQUIRED` |
| 184 "Which suppliers are still estimated using secondary factors?" | `methodology='spend_based'` exists on snapshots but is not linked to a supplier | none | n/a | n/a | n/a | no | new capability + data gap |
| 185/186 "Submitted / missing supplier data" | no supplier-submission model | none | n/a | n/a | n/a | no | `NOT CURRENTLY POSSIBLE FROM STORED DATA` |
| 187 "Which supplier records changed since the previous period?" | snapshots append-only; no supplier-level change tracking | none | n/a | n/a | platform audit trail exists | no | new capability |
| 188 "Which suppliers have the weakest evidence?" | evidence completeness is per snapshot but **not supplier-keyed** | `_evidence_status` per row; `audit_readiness` per org | none | n/a | yes per row | no | partial foundation |
| 189/190 supplier-specific / assured factors | customer factors exist but are not marked supplier-specific or assured | none | n/a | n/a | n/a | no | `NEW DATA/SCHEMA REQUIRED` |
| 193 "Which supplier data is outside the reporting period?" | dates exist on logs/snapshots | none (no "outside period" comparison) | n/a | n/a | n/a | no | new capability |
| 194 "Show the supplier document supporting this emission" | yes | `{log_id}/evidence`, viewer | n/a | n/a | full | not reachable | **backend yes / Insight no** |
| 195 "What should I ask this supplier to improve the data?" | advisory | none | n/a | n/a | n/a | no | not an authoritative-data answer (Mode E/F) |

`[FACT]` **No aggregation can be restricted to Scope 1/2/3 or to a Scope 3 category.** `aggregate_by_supplier` filters only `organization_id` + `start_date`; `aggregate()` filters the same plus a `group_by` **dimension** (not a filter). `[INFER]` Adding a scope/category *filter* to any aggregation is a **new deterministic capability** (a new bounded parameter), not a new query form of an existing one.

---

## 10. Activity capability analysis

`[FACT]` `aggregate_by_activity(org_id, period)` (`data/emissions_logs.py:264-283`) joins `calculation_snapshots cs` to `emissions_logs l` on `l.snapshot_id = cs.id`, filters `cs.organization_id = $1 AND l.start_date BETWEEN $2 AND $3`, groups by `cs.activity_type`, and returns `{activity_type, row_count, quantity, co2e_kg}` ordered by co2e DESC.

| Library question (§25) | Verdict |
| --- | --- |
| 235 "What activity produced this emission?" | **backend yes** for an identified snapshot (`activity`/`activity_type`, exposed via `calculations/{id}` and the I3 allowlist) |
| "What activity contributes most to my emissions?" (the task's specific question) | **Backend yes, with four limitations below**; **Insight: not reachable** (`BLOCKED BY I3`) |
| Activity trends (255/256/258) | no period-over-period activity comparison exists → `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| Activity by scope / by category | **not supported** — no scope filter on this method, and no category dimension exists |
| Activity by facility | **not supported** — facility groups via `aggregate(..., "facility")`, which is not crossed with activity (no cross-tab) |
| Activity by supplier | **not supported** (different group key; the supplier key is unpopulated — §9) |
| Activity-level evidence | **backend yes** per identified emission (evidence chain + viewer); **not reachable** by Insight |

**Limitations of `aggregate_by_activity` as an answer to "what contributes most?"** `[FACT]`
1. It groups by `cs.activity_type` — the **RC2 factor-catalogue label** (e.g. `Fuels > Liquid fuels > Diesel … (kg CO2e) [litres]`), i.e. a *factor-mapping* string, not a governed activity taxonomy.
2. It counts only snapshots with a **linked `emissions_logs` row** (inner join on `snapshot_id`); snapshots without a log are excluded.
3. Results carry **no identifiers** — `{activity_type, row_count, quantity, co2e_kg}` with no snapshot ids, so there is no per-group drill-down.
4. No scope/category/facility/supplier/unit filter and no `LIMIT` (all groups returned).

---

## 11. Facility / asset capability analysis

`[FACT]` Facility is **not a column** on `emissions_logs`: it is the `metadata->>'facility_id'` JSONB key written by `_log_metadata(facility_id)` (`data/emissions_logs.py:89-100`) and grouped by `aggregate(org, period, "facility")` as `COALESCE(metadata->>'facility_id','none')`. Asset **is** a column (`asset_id`), grouped by `aggregate(..., "asset")`.

| Library question (§3/§4) | Backend | Verdict |
| --- | --- | --- |
| Highest-emitting facility / facility comparison | `aggregate(..., "facility")`; benchmarking engine does facility-level comparison | backend yes / Insight no |
| Facility trends | per-period `aggregate(..., "facility")`; benchmarking multi-period | backend partial (no single facility time-series API) |
| Scope 1 / Scope 2 by facility | **not supported** — no scope filter exists on any aggregate | new capability (filter) |
| Scope 3 by facility | **not supported** — no category dimension and no scope filter | new capability + data |
| Activity by facility | not supported (no cross-tab) | new capability |
| Supplier emissions by facility | not supported (supplier key unpopulated; no cross-tab) | new capability + data |
| Evidence for facility results | evidence chain exists per emission; **no facility-level roll-up to evidence** | partial (per row only) |

`[FACT]` Facilities and assets are first-class master data (`facilities`/`assets` repositories; `engines/validation.py:964-985` validates that a log's `facility_id`/`asset_id` resolve), so facility **identity** is authoritative — what is missing is scope/category-filtered and cross-tabbed facility analytics, plus any aggregate→evidence drill-down.

---

## 12. Emission-factor capability analysis

### 12.1 What is stored, layer by layer

| Layer | Retained fields | Evidence |
| --- | --- | --- |
| Factor catalogue (`emission_factors`) | `reporting_year, activity_type, co2e_multiplier, unit, scope, factor_source, factor_set, country, region_deprecated, import_batch_id` (+ provider from the owning `import_batches`) | `supabase/migrations/00000000000000_init_schema.sql`; `data/emission_factors.py:17-20` |
| Customer factors (`customer_factors`) | `name, activity_type, co2e_multiplier, unit, scope, country, reporting_year, factor_source='CUSTOMER', status (draft/active/inactive/archived), version, description, metadata` | `data/customer_factors.py:20-22`; `domain/customer_factor.py:49-56,68-89` |
| Matching | `MatchRequest` (activity, country, reporting_year, unit, scope, organization_id, preferred_provider); `MatchResult` (`status`, `factor`, `confidence`, `methodology`, `provider`, `stages_executed`, `suggestions`, `request_id`, `factor_kind`, `customer_factor_id`) | `domain/matching.py:53-133`; `engines/factor_matching.py:117+` |
| Snapshot (historical) | `factor_id` **or** `customer_factor_id` + `factor_kind`, `factor_source`, `factor_set`, `co2e_multiplier`, `quantity`, `quantity_unit`, `methodology`, `algorithm_version`, `reporting_year`, `scope`, `date`, `content_hash`, `request_id` (= match request id) | `data/emissions_logs.py:53-59, 468-519` |
| Calculation-explanation API | snapshot **plus the factor row and customer-factor row as they exist now**, plus a provenance block | `api/v3_emissions.py:331-370` |
| Factor search / detail API | `/factors` with provenance filters (year, country, scope, unit, source, set, provider); `/factors/{id}` with `natural_key` + usage statistics | `api/v3_emissions.py:582-647` |

### 12.2 Library questions (§23, §33)

| Question | Verdict |
| --- | --- |
| 196–200 which factor / id / value / unit / source | **backend yes** for an identified calculation: `factor_id`/`customer_factor_id`, `co2e_multiplier` (the value used), factor row for unit/source |
| 201/202 year / vintage / geography | **backend yes via the factor row** (`reporting_year`, `country`, `factor_set`) — subject to the retention caveat in §12.3 |
| 203/204 factor type / methodology | **partial**: `factor_source`/`factor_set`/provider exist, but there is **no factor-type field** (spend-based vs activity-based vs supplier-specific); the closest artefact is the snapshot's derived `methodology` |
| 205 GWP basis | **NOT STORED.** Gas coverage is *derived*: `domain/factor.py::gas_coverage()` returns `"CO2"` for SEAI factors or activity labels containing `(kg CO2)`, else `"CO2e"` — a heuristic over `factor_source`/`activity_type` |
| 206–208 transformed / original unit / conversion | **partial**: the snapshot stores `quantity_unit` (post-normalisation) and the evidence line stores `raw_unit` (pre-normalisation), normalised by the central `core/units.normalize_unit`. **No factor-transformation or conversion-ratio record exists** |
| 209/210 why selected / were others considered | **partial.** Stored: `methodology`, `algorithm_version`, `request_id`. **Not stored: `stages_executed` and the candidate/suggestion set.** So "why this factor" can be narrated from retained fields but the ranked alternatives **cannot be reconstructed**. `find_snapshot_by_request_id()` exists but is unused |
| 211 primary vs secondary factor | **not stored** (§7) |
| 212 current for the reporting year | derivable by comparing factor `reporting_year` with the snapshot's `reporting_year` — derived, not stored |
| 213/214 factor changed / share of emissions change attributable to it | **NOT IMPLEMENTED.** No factor-version comparison and no attribution exist. `[INFER]` A deterministic attribution is computable in principle (two snapshots retain different `factor_id`s/multipliers), but the capability does not exist and "same activity" is itself a governance definition |
| 215 show the authoritative factor record | **backend yes** (`/factors/{id}`); Insight no |
| 216–218 geography / temporal / definition match | derivable by comparison; no capability exists |
| 405–411 transformation / GWP / gases / quality limitation / evidence | **NOT STORED** (no transformation, GWP, gas-list or quality-flag fields) |

### 12.3 Retention caveat — historical vs current (the key distinction)

`[FACT]` The snapshot preserves the **value actually used** (`co2e_multiplier`), the factor **identity** (`factor_id`/`customer_factor_id`), `factor_kind`, `factor_source`, `factor_set`, `methodology`, `algorithm_version`, `request_id`. It does **not** preserve the factor row's `unit`, `country`, `reporting_year`, `activity_type`, `provider_key` or any candidate set. The explanation API therefore resolves the factor **as it exists now**: if factor metadata is later edited (or the row removed), the *explanation* changes while the recorded *result* does not. `[INFER]` Any future factor-explanation answer must either state this limitation or the platform must snapshot factor metadata — a schema/data decision, not a query.

---

## 13. Calculation-explanation capability analysis

The library's question 219 ("How was this emission calculated?") maps onto `GET /api/v3/emissions/calculations/{snapshot_id}` + `POST /calculations/{snapshot_id}/verify` + `GET /{log_id}/evidence`, and onto the I3 `calculation_snapshot_lookup` allowlist. Three classes must be separated, as the task requires.

### 13.1 STORED authoritative facts (on the snapshot / line)

`activity`, `activity_type`, `quantity`, `quantity_unit`, `co2e_multiplier`, `co2e_kg`, `scope`, `date`, `reporting_year` (activity year), `methodology`, `algorithm_version`, `content_hash`, `factor_id` / `customer_factor_id` / `factor_kind` / `factor_source` / `factor_set`, `source_item_id`, `source_line_item_id`, `source_file`, `source_page`, `request_id`, `calculated_at`, `calculated_by`, `performed_by`, `import_batch_id`. `[FACT]` `data/emissions_logs.py:53-59`; `api/v3_emissions.py:331-370`.

### 13.2 DERIVABLE from existing facts (not stored as such)

* **reproducibility** — `POST /calculations/{snapshot_id}/verify` recomputes and compares (implemented, org-scoped). `[FACT]`
* **the factor's unit / geographic / temporal metadata** — resolved from the live factor row (§12.3 caveat).
* **CO2 vs CO2e** — derived heuristic (`gas_coverage()`).
* **spend-based vs not** — from `methodology`.
* **"was the value extracted, mapped or manually entered?"** — `evidence_line_items.extraction_method` (`'unknown'` default) + `materialisation_kind` (`FORWARD`/`BACKFILL`), and `manual_extraction_items` rows; `[INFER]` this answers question 246 *partially* (the line records the producing path where provable, else `unknown`).
* **"did the factor change?"** — comparable across snapshots, but no capability exists.
* **restatement** — no restatement concept exists; snapshots are append-only and a re-calculation creates a new snapshot with a new `request_id`.

### 13.3 NOT STORED

* formula/expression used (only the methodology label and multiplier);
* allocation applied (no allocation model);
* proxy/estimate flags as general concepts (only `spend_based`);
* supplier-specific vs average-data methodology markers;
* the factor **candidate set** and match stages (see §12.2);
* GWP/gas coverage as data;
* any record of a manual adjustment to a *calculated* figure after the fact (the audit trail records actions, not accounting adjustments);
* restatement history and its reasons.

### 13.4 Fields that exist in the database but are intentionally withheld from Insight

`[FACT]` The I3 snapshot allowlist (`services/insight_tools.py:75-81`) omits `source_file`, `source_page`, `factor_set`, `import_batch_id`, `request_id`, `performed_by`, `calculated_by`. The evidence-line allowlist (lines 66-69) omits `raw_description`, `raw_quantity`, `raw_unit`, `payload_hash`, `extraction_method`, `source_file_id`, `created_at`. Reports omit artefact URLs and actors (lines 54-64). `[INFER]` Some of these omissions are deliberate minimisation (raw content), others are simply "not named" — the code comment says *"omitted, not inferred"*. Any future widening is a **contract change requiring a PO decision**, not a bug fix.

---

## 14. Trend / variance capability analysis

| Analysis | (1) Data available? | (2) Deterministic comparison implemented? | (3) Attribution implemented? | (4) Reproducible? | (5) Evidenced? | (6) Insight can invoke? |
| --- | --- | --- | --- | --- | --- | --- |
| Month-over-month | yes (`start_date`, `by_month`) | **yes** (aggregate by month; two periods can be aggregated) | no | yes | per-row yes; aggregate no | **no** |
| Year-over-year | yes | **yes via `aggregate(..., "year")` and `POST /api/v2/benchmark`** | partial (benchmarking computes deltas) | yes | per-row yes | no |
| Period-to-period (arbitrary range) | yes | yes (two `aggregate` calls) | no | yes | per-row yes | no |
| Scope variance | yes | yes (`aggregate "scope"` twice) | no | yes | per-row | no |
| Category variance | **no category dimension** | no | no | n/a | n/a | no |
| Supplier variance | key unpopulated (§9) | no | no | n/a | n/a | no |
| Facility variance | yes | partial (per-period facility aggregate; benchmarking facility-level) | partial | yes | per-row | no |
| Activity variance | yes | no (no activity×period comparison) | no | yes | per-row | no |
| **Factor-change variance** | partially (two snapshots retain different factors/multipliers) | **no** | no | n/a | yes per snapshot | no |
| **Methodology-change variance** | `methodology` persisted per snapshot | **no** | no | yes | yes | no |

`[FACT]` **Attribution (question 261: "was the change caused by activity, factor, methodology, boundary or data availability?") is implemented nowhere.** Nothing in the codebase decomposes a variance into components. `[INFER]` A generic dashboard chart (which the emissions dashboard is) is **not** a governed analytical capability: it has no component decomposition, no reproducibility statement, no evidence linkage and no definition of the compared basis. The task's instruction not to conflate the two is therefore satisfied: the dashboard is a *capability pointer*, not an answer engine.

`[REF]` Library §26 requires exactly this decomposition; the library's own architecture section (§40) lists "variance explanation" and "period comparisons" as capability families that each need their own deterministic contract.

---

## 15. Data-quality capability analysis

| Library signal (§27, §34) | Stored? | Deterministically calculable? | Already aggregated? | Exposed to Insight? | Auditable? | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Missing evidence / provenance gaps | **yes** — `source_item_id`, `source_file`, `source_page`; `evidence_line_items` existence | yes (`_evidence_status` per row; `audit_readiness` per org) | **partially** — org-level counts only | no | yes | `FOUNDATION ALREADY EXISTS` at org level; per-record/per-dimension missing |
| Missing source line | yes (`source_line_item_id`, `evidence_line_items.id`) | yes | no | no | yes | partial foundation |
| Estimated activity data | **only** `methodology='spend_based'` + `core/units` spend cues | partially | no | no | yes | `PARTIAL FOUNDATION` |
| Secondary vs primary factor | **not stored** — `factor_kind` distinguishes catalogue-vs-customer, **not** primary-vs-secondary | no (would need a new rule/definition) | no | no | n/a | `NEW DATA/SCHEMA REQUIRED` (or a PO-approved rule) |
| Supplier estimate / missing supplier data | upstream only; no supplier-submission model | no | no | no | n/a | `NOT CURRENTLY POSSIBLE FROM STORED DATA` |
| Incomplete reporting period | derivable from data coverage vs a defined period | no capability | no | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| Incomplete category | **no category dimension** | no | no | no | n/a | `NEW DATA/SCHEMA REQUIRED` |
| Weak provenance / low-confidence extraction | **yes** — `ai_confidence_score`, `ai_mapping_confidence`, `completeness_score()` (0..1 over `activity|quantity|unit`), `extraction_method`, `materialisation_kind` (FORWARD/BACKFILL), `payload_hash`, processing-item confidence | yes (scorers exist) | no | no | yes | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| Manually adjusted records | **no adjustment model.** `manual_extraction_items` records human extraction/mapping and `public.issues` records validation/review items with status — but there is no "adjusted after calculation" concept | partially | no (issues are queryable per org) | no | yes | `PARTIAL FOUNDATION` |
| Factor-quality metadata | **not stored** (no quality flag, assurance status or vintage-representativeness field) | no | no | no | n/a | `NEW DATA/SCHEMA REQUIRED` |
| Extraction method per line | yes (`extraction_method`, default `'unknown'`) | yes | no | no | yes | exists but not reachable |

`[FACT]` The two strongest *existing* quality signals are (a) **evidence-chain completeness** (source item + file + page) and (b) **extraction/mapping confidence plus completeness score**. Neither is aggregated per category/supplier/facility, and neither is reachable by Insight.

---

## 16. Evidence / provenance capability analysis

Mapped onto the **existing** architecture — no second evidence model; the shared viewer and `evidence_line_items` are reused.

| Library question (§28, §34) | Verdict | Evidence |
| --- | --- | --- |
| 284 "Where did this number come from?" | backend yes for an identified emission; Insight no | `{log_id}/evidence`; `domain/evidence.py` |
| 285/286/287 source document / invoice / spreadsheet | backend yes (document via signed URL + viewer); "invoice"/"spreadsheet" are document kinds resolved through the same chain | `SourceEvidenceViewer`; DM-6 gates |
| 288 exact row | **partial** — CSV/XLSX rows derive from the producer's `source_row` (+ `source_sheet`); **no `line_reference` producer exists**, so `row_reference` is always NULL | `domain/evidence.py:63-160`; `services/automatic_extraction.py:673-683,787` |
| 289 which sheet | **yes for XLSX** (`extracted_data.source_sheet` → `kind: sheet_row`) | same |
| 290 which PDF page | **yes where the producer recorded a genuine per-line page** (`page_state='verified'`); historical page-count-derived values are retained but reported `unverified` | `domain/evidence.py:23-60,205-260` |
| 291/292 extracted vs mapped value used | **partial** — mapped value on the snapshot; raw extracted value on the evidence line (`raw_quantity`, `raw_unit`), **withheld from Insight** | `evidence_line_items`; I3 allowlist |
| 293 which snapshot produced the result | **yes** (`emissions_logs.snapshot_id`) | `data/emissions_logs.py:53-59` |
| 294 which report version contains the number | **yes** — report/version models and `report_lookup`/`report_version_lookup` | `services/insight_tools.py:283-325` |
| 295 trace result → original source | **yes** for an identified emission (chain implemented and OHD-verified) | viewer closure 2026-09-22 |
| 296 what changed between source and result | **not stored** (no diff model) | — |
| 297/298 evidence for a factor / for a classification | **partial** — factor provenance yes; there is no classification-evidence model | — |
| 299 evidence supporting a supplier's result | blocked by the supplier-key gap (§9) | — |
| 300–303 audit trail / who / when / what changed | **yes platform-wide** — canonical `public.audit_trail` (+ `public.issues` lifecycle); Insight exposes only its own interaction audit | `infra/audit_logger.py`; `data/audit.py` |
| 304 evidence still available | derivable (document existence / `is_active` / `deleted_at`) | `data/reporting.py:1100+` |
| 412–426 evidence-quality challenges | **partial**: line `raw_*` vs snapshot values allow reconciliation in principle, but **no capability exists**; period/entity/unit/scope checks exist only at validation time inside `engines/validation.py`, not as a queryable audit capability | `engines/validation.py` |

`[FACT]` Remaining evidence gaps: **no `line_reference` producer**, **no source→result diff model**, **no classification-evidence model**, **no adjustment history**, and **no aggregate→evidence drill-down** (aggregates return no ids).

---

## 17. External-auditor question analysis (library §29)

Note the library's own constraint: an external auditor "is **not** a CarbonTally platform user" and Insight "should only answer these from evidence that the customer has authorized and that CarbonTally actually holds". Auditor **identity** is explicitly denied Insight access (`api/insight_authz.py:245-246`, audited as an I2 decision), so any auditor-facing answer today would have to be produced by a customer/consultant and exported — which is outside Insight's current authorization.

| Bucket | Auditor questions | Basis |
| --- | --- | --- |
| **Directly verifiable today** | 305 source of a number; 306 reproduce the calculation; 307 activity data; 308 factor; 309 factor source; 310 factor year/version; 311 geography; 312 methodology; 315 reporting period; 338 methodology version; 339 factor database; 340 factor metadata; 341 calculation snapshot; 342 source document; 343 exact line item; 344 audit event for the change | All are stored and reachable **for an identified emission** via the calculation-detail, verify, evidence and viewer surfaces; the audit trail is canonical. `[FACT]` |
| **Verifiable after deterministic aggregation** | 316 primary vs secondary; 317 % primary; 320 which calculations were estimated; 328 which records are missing evidence; 329 which Scope 3 categories are incomplete; 333 trace a reported total to source records; 334 evidence chain for a sample; 335 evidence covers the same period; 336 which records are estimates; 337 basis for estimates | Underlying per-record evidence exists; org-level readiness counts exist (`audit_readiness`), but there is **no aggregation/selection capability** (no sampling, no category dimension, no per-dimension completeness, no aggregate→evidence drill-down) — and no Insight path. `[FACT]`/`[INFER]` |
| **Partially verifiable** | 313 organisational boundary; 314 operational boundary; 318 assumptions used; 319 material assumptions; 322 who approved the adjustment; 323 when the adjustment was made; 324 what changed after the original calculation; 331 which suppliers provided primary data; 332 which supplier factors are assured; 325–327 restatement history and its reason | Factor provenance and audit events exist, but boundary definition, assumption registers, adjustment approvals, restatement history, supplier assurance and primary/secondary status are **not stored**. `[FACT]` |
| **Not currently verifiable** | 321 which records were manually adjusted (no adjustment concept); 325/326/327 restatement and its reason; 330 which supplier data is missing | No stored basis. `[FACT]` |
| **Governance-blocked** | 306 (automated reproducibility *inside Insight*), 341/342/343 (snapshot/document/line as an Insight answer), 333 (a reported total as an Insight answer) | The capability or data exists; Insight may not use it: no I3 tool returns documents, pages or lines (I6 §F.1), the snapshot allowlist withholds `source_file`/`source_page`, and auditor principals are denied Insight entirely. `[GOV]` |

---

## 18. Consultant question analysis (library §30)

`[FACT]` Consultant scope **is** resolvable (`authorize_insight_scope` step 3 uses the platform's active consultant-client grant), but the I6 closure §F.2 records that **no consultant Insight surface is authorized**. Consultant-facing analytics today exist outside Insight: `GET /api/v3/consultants/clients/{client_id}/dashboard` (scope/asset/facility, org-scoped via `_authorized_client_org`) and the consultant calculation-history route.

| Consultant workflow (§30) | Backend state | Insight | Verdict |
| --- | --- | --- | --- |
| 345 hotspot identification (client) | `aggregate` scope/month/asset/facility + `aggregate_by_activity` exist; no scope/category filter, no ranking contract | no | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| 347 supplier prioritisation | blocked by the unpopulated supplier key (§9) | no | `PARTIAL FOUNDATION` + data gap |
| 346/353 category prioritisation / estimation dependence | no category dimension; only `methodology='spend_based'` | no | `NEW DATA/SCHEMA REQUIRED` |
| 348/349 spend-based → activity-based upgrade candidates | `methodology` identifies spend-based records; **no "could be upgraded" logic** | no | new capability |
| 350/351 supplier-specific factors; weak temporal/geographic representativeness | customer factors exist; factor metadata lacks quality/representativeness fields | no | `NEW DATA/SCHEMA REQUIRED` |
| 352/358/362 incomplete evidence; what to review before assurance; what to sample | org-level readiness counts exist; **no sampling or per-record selection contract** | no | new capability |
| 354 facility YoY anomalies | benchmarking engine compares facilities across years | no | exists but not reachable (legacy v2 surface) |
| 355/356/357 change caused by activity / factor / methodology | **no attribution anywhere** | no | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| 359/360 hotspot evidence | per-emission evidence exists; **no aggregate→evidence linkage** | no | partial |
| 361 material assumptions | assumptions are not stored | no | `NEW DATA/SCHEMA REQUIRED` |
| 363 what changed since the previous period | period aggregates exist; no diff/attribution contract | no | new capability |
| 364 which results cannot be independently reproduced | `POST /calculations/{id}/verify` exists **per snapshot**; no bulk/selection equivalent | no | exists but not reachable |

**No consultant UI is authorized by this analysis, and none is implied.**

---

## 19. Capability clustering / minimum deterministic service set

Each cluster names the **minimum deterministic capability** that would serve the broadest set of library questions, its priority class (task §20 vocabulary) and the questions it unlocks.

| Cluster | Minimum deterministic capability | Questions served | Priority class |
| --- | --- | --- | --- |
| **C-01 Scope aggregation** | period totals by scope (exists) | 21, 58, 59, 61, 181 | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| **C-02 Scope-filtered aggregation** | any aggregation restricted by scope | 23, 24, 25, 264–266 | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| **C-03 Scope 3 category dimension** | governed category on emissions (stored or derived) + category aggregation | 60, 63, 267, 329, 346, 353 | `NEW DATA/SCHEMA REQUIRED` |
| **C-04 Dimension aggregation** | group-by dimension (scope/month/year/asset/facility) (exists) | 8, 23, 253–260, 354 | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| **C-05 Activity aggregation** | top activities by co2e (exists, string-grouped) | 6, 22, 62, 255, 256 | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| **C-06 Supplier relationship persistence** | persist `supplier_id` (or supplier on the snapshot) from the existing mapping | 7, 71, 180–182, 188 | `PARTIAL FOUNDATION` (data gap) |
| **C-07 Supplier aggregation + filters** | supplier aggregation with scope/category/period filters (aggregation exists, key empty) | 180, 181, 192 | `PARTIAL FOUNDATION` + `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| **C-08 Supplier variance** | period-over-period supplier delta | 182, 187, 259 | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| **C-09 Factor explanation** | factor identity/value/metadata for an identified calculation (exists; retention caveat) | 196–202, 209, 215, 405 | `EXISTS BUT NOT INSIGHT-REACHABLE` + partial (metadata not snapshotted) |
| **C-10 Factor-change attribution** | factor set/version diff per activity + share of variance | 213, 214, 257, 356 | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| **C-11 Period comparison + variance attribution** | deterministic two-period comparison decomposed by activity/factor/methodology | 4, 5, 251–263, 355–357, 363 | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| **C-12 Evidence/quality selection** | per-dimension completeness + record selection (sampling) | 188, 269–283, 328, 358, 362 | `NEW DETERMINISTIC CAPABILITY REQUIRED` (org-level counts exist) |
| **C-13 Primary/secondary classification** | stored flag or PO-approved deterministic rule | 11, 12, 20, 73, 183, 191, 192, 272, 316, 317, 336 | `NEW DATA/SCHEMA REQUIRED` |
| **C-14 Discovery (date/amount/activity/supplier/facility/scope)** | bounded discovery contract + ambiguity state | 251, 281 and every "why was X" question | `NEW GOVERNANCE CONTRACT REQUIRED` (I3/I4) + new capability |
| **C-15 Scope 2 dual reporting** | market-based method + instrument register/residual mix + method dimension | 41–60, 364 | `NEW DATA/SCHEMA REQUIRED` |
| **C-16 Scope 1 decomposition (combustion/fugitive/process)** | classification on the emission or a governed derivation | 25–28, 30–36 | `NEW DATA/SCHEMA REQUIRED` |
| **C-17 Assumptions / restatement register** | stored assumptions, adjustment approvals, restatement history | 123, 127, 148, 151, 318, 319, 321–327 | `NOT CURRENTLY POSSIBLE FROM STORED DATA` |
| **C-18 Aggregate → evidence drill-down** | bounded contract returning component snapshot/line ids for an aggregate group | 333, 334, 359, 360 | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| **C-19 Concept answers (taxonomy H)** | governed carbon-accounting knowledge source | Mode E questions | `NEW GOVERNANCE CONTRACT REQUIRED` (not data) |

`[INFER]` The **minimum set unlocking the largest share of the library** is C-14 (discovery contract) plus C-01/C-04/C-05 (already existing — need reachability), C-11 (variance), C-02/C-03 (scope/category filtering and dimension) and C-06/C-07 (supplier persistence). C-03, C-13, C-15, C-16 and C-17 are **data/schema questions first**: no query work can substitute for them.

---

## 20. Backend vs Insight reachability matrix

Required summary table. `Insight currently reaches it?` = whether the **closed I3/I4 contracts** can invoke it today.

| Capability family | Backend data exists? | Deterministic backend exists? | Evidence trace exists? | Insight currently reaches it? | Governance required? | Status |
| --- | --- | --- | --- | --- | --- | --- |
| C-01 Scope aggregation | yes | yes | per row yes / aggregate no | **no** | yes (new tool) | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| C-02 Scope-filtered aggregation | yes | **no (no scope filter)** | per row | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| C-03 Scope 3 category dimension | **no** | no | n/a | no | yes | `NEW DATA/SCHEMA REQUIRED` |
| C-04 Dimension aggregation | yes | yes | per row | no | yes | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| C-05 Activity aggregation | yes | yes (string-grouped) | per row | no | yes | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| C-06 Supplier relationship | schema + upstream mapping; **not persisted on the emission** | no | partial | no | yes | `PARTIAL FOUNDATION` |
| C-07 Supplier aggregation + filters | key empty | aggregation yes; filters no | per row | no | yes | `PARTIAL FOUNDATION` |
| C-08 Supplier variance | key empty | no | n/a | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| C-09 Factor explanation | yes (snapshot + live factor row) | yes | yes | no | yes | `EXISTS BUT NOT INSIGHT-REACHABLE` (retention caveat) |
| C-10 Factor-change attribution | partial (two snapshots) | no | per snapshot | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| C-11 Period comparison / variance | yes | comparison yes, **attribution no** | per row | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| C-12 Evidence/quality selection | yes (per record); org-level counts | partial (`audit_readiness`) | yes | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| C-13 Primary/secondary classification | **no** | no | n/a | no | yes | `NEW DATA/SCHEMA REQUIRED` |
| C-14 Discovery (date/amount/…) | yes | date-ranged reads only; **no discovery contract** | yes | no | **yes (I3/I4)** | `NEW GOVERNANCE CONTRACT REQUIRED` |
| C-15 Scope 2 dual reporting | disclosure-layer hint only | no | n/a | no | yes | `NEW DATA/SCHEMA REQUIRED` |
| C-16 Scope 1 decomposition | **no** | no | n/a | no | yes | `NEW DATA/SCHEMA REQUIRED` |
| C-17 Assumptions / restatement | **no** | no | n/a | no | yes | `NOT CURRENTLY POSSIBLE FROM STORED DATA` |
| C-18 Aggregate → evidence drill-down | yes (component rows) | **no (aggregates return no ids)** | per row | no | yes | `NEW DETERMINISTIC CAPABILITY REQUIRED` |
| C-19 Concept answers | **no governed source** | no | n/a | no | yes | `NEW GOVERNANCE CONTRACT REQUIRED` |
| Evidence navigation (existing) | yes | yes (viewer route) | **FULL** | **partly** (reference handoff) | no (closed) | `FOUNDATION ALREADY EXISTS` |
| Calculation explanation (existing) | yes | yes | **FULL** | **yes** (`calculation_snapshot_lookup`) | no (closed) | `FOUNDATION ALREADY EXISTS` |
| Report / version context | yes | yes | FULL | **yes** | no (closed) | `FOUNDATION ALREADY EXISTS` |
| Data-quality signals (confidence/completeness) | yes | yes (scorers) | yes | no | yes | `EXISTS BUT NOT INSIGHT-REACHABLE` |
| Supplier document → evidence (per emission) | yes | yes | FULL | no | yes | `EXISTS BUT NOT INSIGHT-REACHABLE` |

---

## 21. Evidence-traceability matrix

For each analytical capability: **can a resulting number be traced back to calculation snapshots and then to source evidence?**

| Capability | Trace class | Basis |
| --- | --- | --- |
| Single identified emission → source | **FULL TRACE** | `emissions_logs.snapshot_id` → `calculation_snapshots` (source item/file/page) → `manual_extraction_items` → document → viewer (OHD-verified, PO-closed 2026-09-22) |
| Calculation explanation for an identified snapshot | **FULL TRACE** | snapshot + evidence chain + `evidence_line_items` + viewer route |
| Report version → evidence | **FULL TRACE** | `report_evidence_lookup` returns line/snapshot references; viewer resolves them |
| Scope totals (existing backend) | **PARTIAL TRACE** | component rows exist and are org-scoped, but the aggregate returns only a group key + co2e — no snapshot ids, so no drill-down from the *number* |
| Activity / facility / month / year / asset aggregates | **PARTIAL TRACE** | as above; each component row is fully traceable, the group is not |
| Supplier aggregates | **NO TRACE (in practice)** | the grouping key is unpopulated (§9) and the response carries no ids |
| Category totals | **NO TRACE** | the dimension does not exist |
| Scope-2 market-based totals | **NO TRACE** | no method dimension; disclosure hint only |
| Period comparison / variance | **NO TRACE for the variance; PARTIAL for its inputs** | two aggregates (partial trace each); no attribution objects exist to trace |
| Factor-change attribution | **NO TRACE** | no capability; snapshots retain factor identity so a *future* capability could trace components |
| Data-quality/completeness counts | **PARTIAL TRACE** | `audit_readiness` counts snapshots by evidence state but returns counts, not ids |
| Consultant client dashboard | **PARTIAL TRACE** | aggregate-only, same limitation |

`[INFER]` The pattern is consistent: **row-level provenance is excellent (FULL), aggregate-level provenance is absent (PARTIAL/NO)**. The library's auditor questions (333/334) target exactly the missing half.

---

## 22. Security analysis

`[FACT]` unless marked.

| Requirement | Finding |
| --- | --- |
| **Organization scoping of aggregates** | `aggregate()`, `aggregate_by_supplier()`, `aggregate_by_activity()`, `count_snapshots()`, `list_snapshots()`, `find_by_org()`, `list_for_line()` all carry `organization_id` in the SQL `WHERE`. `get_snapshot(snapshot_id)` and `list_for_file(file_id)` are **by-id reads without an org predicate**, used only behind an API-level `ensure_org_access` check (calculation detail; D33 evidence route) — defence in depth therefore rests on keeping that call-site discipline. |
| **Two aggregates are NOT org-scoped** | `snapshot_count_for_factor(factor_id)` and `factor_usage_span(factor_id)` have no `organization_id` predicate and are surfaced by `GET /api/v3/emissions/factors/{factor_id}` to any organisation member — disclosing **platform-wide counts and first/last calculation timestamps** for a factor (cross-tenant metadata; no content, no customer identifiers). `[INFER]` Severity low, **not** introduced by Insight, recorded so a future analytical surface does not copy the pattern. |
| **Object-level authorization** | Customer principals are bound to their own `organization_id`; consultants pass `ensure_consultant_org_access` / `_authorized_client_org`; PE and auditor principals are denied Insight outright; conversations are creator-visible only. No analytical route accepts a caller-supplied organisation without re-checking it. |
| **Parameter validation** | `group_by` is validated against the fixed `_GROUP_EXPRESSIONS` allowlist (`data/emissions_logs.py:43-49`) and raises otherwise — a *dimension* allowlist, not a filter. Periods are built from ISO dates (`build_period`; 422 on malformed input in the consultant route). `limit`/`offset` are bounded by `Query(..., ge=, le=)` on list routes. |
| **SQL-injection resistance** | All aggregates use positional parameters (`$1..$n`); the only interpolated fragments are compile-time constant column lists and the allowlist-mapped group expression. No user string reaches SQL as an identifier. |
| **Arbitrary-query prevention** | No SQL is generated from model output; the model receives no query interface; Insight tools accept identifiers only; `invoke_tool` rejects unratified names with `invalid_input`/`unratified_tool`. |
| **Signed evidence access** | Signed URLs are minted server-side with a TTL, gated on DM-6 depth on the evidence routes, never returned in list/report/aggregate responses, and never sent to the model. |
| **Data minimisation before LLM submission** | Allowlists at every boundary (tool output, persisted arguments/metadata, context projections, evidence-line fields, report fields); question truncated to 500 chars; context budget enforced pre-submission. No aggregate or quality surface currently feeds the model at all (all are unreachable), so a future aggregation→narration path must define its **own** minimisation contract. |
| **Aggregate → model risk (new, forward-looking)** | `[INFER]` A safe narration payload for an aggregate is the group key + co2e + count + period + explicit basis — **not** component rows, third-party names beyond the organisation's own scope, or raw line content. Design constraint for any future authorization, not a present defect. |
| **Rate limiting** | Unchanged and still absent (baseline report §9.7): the middleware exists but is never registered and `rate_limited` is never produced. Any new analytical surface inherits that absence. |
| **Error handling** | Aggregate/analytical routes return plain 422/403/404 messages; no SQL, stack trace, DSN or internal path is returned; denials are uniform. |

---

## 23. Governance gaps

Only decisions/authorizations that are **actually required** to make the library answerable, each with what it blocks.

| ID | Missing decision / authorization | Blocks |
| --- | --- | --- |
| **Q-1** | **A discovery contract** (bounded typed request covering date/amount/activity/supplier/facility/scope) — necessarily a new or widened I3 tool, plus the parameter-extraction question | every "why was X" question; all of C-14 |
| **Q-2** | **An ambiguity response state** (`multiple_matches` or equivalent) in the closed I3/I4 vocabularies | "which one do you mean" questions (library §36) |
| **Q-3** | **Amount tolerance** as a documented product rule | amount-based discovery |
| **Q-4** | **Date/timezone semantics** for matching | date-based discovery and comparisons |
| **Q-5** | **Authorization for Insight to use aggregation** (a bounded analytics contract: which dimensions, bounds, and what is returned) | C-01, C-02, C-04, C-05, C-07, C-18 |
| **Q-6** | **Allowed filter semantics** for aggregation (scope/category/period/unit) and permitted cross-tabs | C-02; facility/activity cross-tabs |
| **Q-7** | **A Scope 3 category taxonomy** (which mapping is authoritative — factor catalogue, activity label or customer declaration — and whether it is stored or derived) | C-03; categories 1–15 |
| **Q-8** | **A primary vs secondary data definition** (stored flag vs deterministic derivation) | C-13; auditor sampling questions |
| **Q-9** | **A market-based Scope 2 method definition plus instrument/residual-mix register** | C-15; the location-vs-market comparison |
| **Q-10** | **A Scope 1 decomposition taxonomy** (stationary/mobile/fugitive/process) | C-16 |
| **Q-11** | **Variance/attribution definitions** (comparability basis, whether re-calculations count, how activity vs factor vs methodology is separated, restatement handling) | C-10, C-11; library §26 |
| **Q-12** | **An aggregate→evidence drill-down contract** (what evidence may be exposed for a group, and at what DM-6 depth/bound) | C-18; auditor questions 333/334 |
| **Q-13** | **A supplier-persistence decision** (write `supplier_id` on the emission/snapshot from the existing mapping, with what confidence rule and backfill policy) | C-06, C-07, C-08; the whole supplier family |
| **Q-14** | **A bounded I8 authorization for rate limiting** (thresholds + acceptance criteria) | any customer-facing analytical surface at scale |
| **Q-15** | **Concept-answer governance** (a governed knowledge source, and how conceptual answers are separated from calculated facts) | C-19; Mode E |
| **Q-16** | **Persona decisions** (consultant surface; auditor handling) — already recorded as C-10/C-25 in the PO decision inventory | consultant and auditor families |

Already dispositioned and therefore **not** gaps: C-01 (ratified), C-02 (deferred), C-03 (deferred), C-04 (accepted), C-05 (ratified), I7, full I8, production deployment.

---

## 24. Explicit NOT IMPLEMENTED

Verified absent from the codebase (or from the reachable surface) at HEAD `669669a`:

1. Any discovery operation as a callable capability (date/amount/activity/supplier/facility/scope).
2. Amount matching or tolerance.
3. Date/timezone semantics for matching.
4. Structured parameter extraction beyond UUIDs.
5. `multiple_matches` (or equivalent) in either closed vocabulary.
6. Insight-reachable aggregation of any kind (dashboard/scope/activity/supplier/facility/month/year).
7. Scope or category **filters** on any aggregation.
8. A Scope 3 category dimension (stored or derived).
9. A primary vs secondary data flag or rule.
10. Scope 2 market-based totals, instrument register or residual mix.
11. Scope 1 combustion-type/fugitive/process decomposition.
12. Period-comparison **attribution** (activity vs factor vs methodology vs boundary).
13. Factor-change attribution across periods.
14. Aggregate→evidence drill-down (aggregates return no identifiers).
15. Supplier persistence on the emission/snapshot (`supplier_id` never written by application code).
16. Supplier variance, supplier data-quality or supplier submission tracking.
17. Assumption, adjustment and restatement registers.
18. Factor transformation / GWP / gas-list / quality metadata.
19. Insight rate limiting (`RateLimitMiddleware` unregistered; `rate_limited` never produced).
20. Carbon-accounting concept answers (taxonomy H / Mode E).

## 25. Explicit NOT AUTHORIZED

1. Any new or widened I3 tool — including a discovery tool (PO I5–I8 record §3.5; I6 closure §F.1).
2. Any change to the I3 six-value `ToolStatus` or the fourteen-value I4 `AnswerStatus`.
3. Any aggregation/comparison/contributor capability for Insight.
4. Supplier analytics for Insight (and any supplier-persistence change to the calculation path).
5. Scope 1/2/3 analytics for Insight, including market-based Scope 2.
6. Factor-discovery or factor-attribution capabilities for Insight beyond the existing read-only detail.
7. Concept-answer/RAG/vector-search capabilities.
8. Rate limiting thresholds (I8-A principles only; no concrete I8 authorization).
9. Consultant, internal-staff, auditor or PE Insight surfaces.
10. I7 (retention/deletion/export) and full I8.
11. Production deployment.
12. Any change to the Source Evidence Viewer, DM-6 implementation, or remediation of C-01/C-02/C-03 (2026-09-22 closure authorizes **none**).
13. Schema/migration changes of any kind, including the new dimensions identified above (they require their own authorization).

---

## 26. Recommended PO decision points

Dependency-ordered only; no prioritisation by business value.

1. **Confirm the status of the Question Library itself** — it is a design/reference document ("not implementation authorization") and is currently **untracked**. Whether it becomes a durable committed reference is a PO documentation decision.
2. **Decide the discovery contract first (Q-1/Q-2)**, because every other family's *question form* depends on it: the library's most common shape — "why was X on \<date\> / for \<amount\> / with \<supplier\>" — cannot be expressed to the platform today. Tolerance (Q-3) and timezone semantics (Q-4) parameterise it and must be decided with it.
3. **Decide whether Insight may use aggregation at all, and under what bounded contract (Q-5/Q-6).** Highest-leverage decision: scope, activity, facility, month and year aggregation already exist deterministically and need only an authorized bounded exposure path.
4. **Decide the data questions no query can substitute for** — Scope 3 category taxonomy (Q-7), primary/secondary definition (Q-8), Scope 2 market-based method + instruments (Q-9), Scope 1 decomposition (Q-10). Each is a classification/schema decision blocking an entire family.
5. **Decide supplier persistence (Q-13).** The relationship is already captured upstream; the decision is whether and how to persist it on the emission, and the backfill policy. Until then the supplier family is unanswerable regardless of governance.
6. **Decide variance/attribution definitions (Q-11)** and the aggregate→evidence drill-down contract (Q-12) — the latter is required before any auditor-facing answer built on an aggregate can be honest.
7. **Decide rate limiting (Q-14)** if analytical surfaces are to be customer-facing at scale (note the I8 prerequisites/acceptance-criteria gap).
8. **Decide personas (Q-16)** — consultant and auditor handling are separately recorded decisions.
9. Every decided item then follows the mandatory chain: bounded implementation authorization → implementation → OHD verification → PO closure → (separately) deployment authorization.

---

## 27. Files/code inspected

**Documents** — `CarbonTally_Insight_Question_Library_2026-09-22.md` (full, 971 lines); `CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922.md`; `CarbonTally_Insight_Architecture_Reference_2026-09-22.md`; `CT-P8-PO-DECISION-INVENTORY-20260922.md` (§0, §C); `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` (§3.5, §5, §6, §8, §11); `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` (§F); the 2026-09-22 viewer closure decision.

**Backend — data / domain / model**
`data/emissions_logs.py` (columns; `create`; `save`; `find_by_org`; `aggregate`; `aggregate_by_supplier`; `aggregate_by_activity`; `count_by_scope`; `count_snapshots`; `list_snapshots`; `list_for_file`; `list_for_line`; `get_snapshot`; `find_snapshot_by_request_id`; `snapshot_count_for_factor`; `factor_usage_span`) · `data/emission_factors.py` · `data/customer_factors.py` · `data/suppliers.py` · `data/issues.py` · `data/reporting.py` (`audit_readiness`) · `data/exports.py` (`_evidence_status`) · `data/disclosure.py` · `data/disclosure_projection.py` · `data/manual_extraction.py` · `data/document_processing.py` · `data/evidence_line_items.py` · `domain/factor.py` (`gas_coverage`) · `domain/customer_factor.py` · `domain/matching.py` · `domain/calculation.py` · `domain/disclosure.py` (`SCOPE2_METHODS`) · `domain/line_items.py` · `domain/evidence.py` · `domain/disclosure_exposure.py`

**Backend — engines / services**
`engines/factor_matching.py` · `engines/calculation.py` · `engines/validation.py` · `engines/benchmarking.py` · `engines/report_generation.py` · `services/automatic_extraction.py` (`_REQUIRED`, `completeness_score`) · `services/ai_document_extraction.py` · `services/automatic_processing.py` · `services/insight_tools.py` · `services/insight_interactions.py` · `services/insight_context.py` · `core/units.py`

**Backend — API / authorization**
`api/v3_emissions.py` (all routes, scope aliases, evidence route, factor routes) · `api/v3_consultants.py` (client dashboard/history) · `api/v3_evidence.py` · `api/v3_documents.py` · `api/insight_authz.py` · `api/v3_insight*.py` · `api/business.py` (v2 benchmark) · `api/router.py` · `api/dependencies.py` · `infra/audit_logger.py` · `infra/llm_client.py` · `middleware/rate_limit.py` · `main.py`

**Migrations** — `00000000000000_init_schema.sql` (suppliers, emission_factors, emissions_logs, manual_extraction_items, customer_documents) · `20260801000000_rc2_constraints.sql` · `20260802000000_rc2_indexes.sql` · `20260914000000_p8_b1_disclosure_model_foundation.sql` · `20260916000000_p8_b2_evidence_line_items.sql` · `2026100{1,2,3}000000_p8_i{1,2,4}_insight_*.sql`

**Frontend** — `src/App.js`; `src/v3/insight/*`; `src/v3/evidence/*`

**Search operations** — targeted greps for `supplier_id`, `facility_id`/`asset_id`, `market_based`/`location_based`, `scope3`/`category`, `tolerance`, `rate_limit`/`RateLimitMiddleware`, `spend_based`/`primary`/`secondary`/`estimated`, `SCOPE2_METHODS`, `snapshot_count_for_factor`/`factor_usage_span`, `INSERT INTO public.emissions_logs`, plus `awk` DDL extraction.

---

## 28. Exact relevant commit SHAs

| Item | SHA |
| --- | --- |
| **HEAD examined** | `669669a168f85fbbcb596fc233e2ad246dd146ff` |
| Baseline gap report (parent of this analysis) | `669669a` |
| I2 authorization boundary | `177dff5` |
| I3 tool catalogue + contract | `674fe07` |
| I3 service + remediations | `651f8c1` |
| I4 interactions + canonical audit | `310a62a` |
| I5 context assembly | `f9d91e1` |
| I6 UI | `09e2315` |
| Source Evidence Viewer + evidence kernel | `999e4fb` (OHD `5d5f7ed`; PO closure `ff354fc`/`0082247`) |
| AI document-extraction engine (last change) | `daad396` |
| Rate-limit middleware (last change; unregistered) | `077c866` |

---

## 29. Stop condition

**Analysis only; no implementation was performed.** No application code, schema, migration, API, I3 tool, I3/I4 status vocabulary, Insight UI, Source Evidence Viewer, RLS, authorization, aggregation, supplier analytics, scope analytics, factor discovery, concept-answer/RAG, rate limiting or deployment state was modified. Nothing here authorizes implementation, and the repository's closed decisions (I2–I6, the Source Evidence Viewer) were neither reopened nor reinterpreted. **No gap discovered by this analysis was fixed.**

**STOP — this report is the only artefact of this task.**

**Working tree:** clean except the two **untracked** PO-supplied reference documents (`CarbonTally_Insight_Architecture_Reference_2026-09-22.md`, `CarbonTally_Insight_Question_Library_2026-09-22.md`) and this new report.
