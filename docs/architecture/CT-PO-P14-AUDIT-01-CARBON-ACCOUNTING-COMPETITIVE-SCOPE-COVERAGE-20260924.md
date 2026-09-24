# CT-PO-P14-AUDIT-01 — Carbon Accounting Competitiveness, Scope 1/2/3 Coverage, Data Quality, Auditability and Reporting Gap Analysis

**Task ID:** P14-AUDIT-01-20260924-CARBON-ACCOUNTING-COMPETITIVE-SCOPE-COVERAGE
**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Baseline commit:** `b52635bf9ea0ca2c4d0804f4db9859c67b612f30`
**Audit type:** READ-ONLY. No product code, schema, RLS, migration, corpus, oracle, Step-3 UI or production change was made.

---

## 0. Production prohibition and audit safety

* Production was never contacted. All CarbonTally evidence was gathered from the **local Demo Lab**
  (`carbontally_demo_local` on `127.0.0.1:54426`) plus static inspection of the working tree.
* Every database statement issued was **read-only** (catalogue queries, `SELECT`/`COUNT`/`GROUP BY`).
  No row was inserted, updated, deleted or manufactured (§AC).
* No destructive harness was run. `backend/tests/integration/conftest.py` performs
  `TRUNCATE … RESTART IDENTITY CASCADE` (invariant **F-046-1**), so integration suites were **not
  executed** against any data-bearing database. Where an integration test is cited below it is cited
  as *existing code*, not as a run performed by this audit.
* Working-tree state at audit time: modified `.gitignore` plus untracked `.costrict/`, `8`, `=`,
  `costrict-p3-ov-01-independent-re-verification.txt`, `docs/ChatGPT/*` — all **pre-existing noise**,
  none created by this audit.

## 1. Method, and what "audited" means here

For every capability the audit demanded five separable questions, and they are answered separately
throughout: **documented? code? route? factors? verified end-to-end?**

| Evidence class | How it was established |
|---|---|
| `DOCUMENTED ONLY` | text in `docs/` or docstrings with no matching code |
| `CODE EXISTS` | symbol present in the working tree (read-only inspection) |
| `ROUTE WIRED` | an HTTP route or data-layer call path reaches the symbol |
| `FACTORS` | rows verified in `emission_factors`/`customer_factors` with the required unit/scope/country |
| `END-TO-END VERIFIED` | a persisted result proves extraction → mapping → factor → calculation → persistence → evidence → reporting |

A capability is **never** marked verified because a function exists. Where the demo database holds no
result for a capability it is marked `NOT VERIFIED` and the missing fixture is described.

**Honesty constraints observed:** the demo database is small (§2). Absence of rows is reported as *not
exercised*, which is not the same as *broken*. Presence of schema is reported as *modelled*, which is
not the same as *working*.

## 2. Live data baseline (read-only counts, `carbontally_demo_local`)

| Table | Rows | Significance |
|---|---|---|
| `emission_factors` | **7049** | all `reporting_year = 2025`; `GB` 7029 / `IE` 20 |
| `customer_factors` | **0** | no customer custom factor configured anywhere |
| `emissions_logs` | **2** | both `Scope 1`; 0 with `supplier_id`, 0 with `data_source`, 0 with `confidence_score` |
| `calculation_snapshots` | **2** | both `Scope 1`, `DEFRA-DESNZ`/`DEFRA-2025`, `direct_multiply`, `factor_kind=emission_factor` |
| `manual_extraction_items` | **23** | 21 `extracted`, 1 `mapped`, 1 `calculated` |
| `evidence_line_items` | **23** | source-evidence rows (P12-IMPL-01) |
| `suppliers` | **1** | supplier master effectively unexercised |
| `manual_review_queue` | **0** | queue modelled, never used |
| `audit_trail` | **95** | `processing_audit_trail` 0, `review_audit_trail` 0 |
| `report_versions` | **4** | `report_version_artifacts` **0** |
| `disclosure_frameworks` | **3** | `GHG_PROTOCOL` (primary), `UK_SECR`, `ESRS_E1` |
| `disclosure_report_purposes` | **4** | Annual Carbon Report, Management Report, UK SECR Report, ESRS E1 Quantitative |
| `disclosure_values` | **0** | no disclosure value ever projected |
| `disclosure_requirement_versions` | **0** | no regulatory requirement content seeded |
| `activity_categories` | **0** | GHG Protocol scope/category taxonomy **unpopulated** |
| `product_categories` / `supplier_categories` | **0 / 0** | same taxonomy columns, unpopulated |
| `organizations` / `facilities` / `assets` / `organization_members` | **4 / 1 / 1 / 8** | multi-organisation data exists |
| `customer_documents` | **0** | — |
| public base tables | **141** | large modelled surface |

## 3. Scope coverage at a glance (evidence-based)

| Scope | Factors in DB | Calculation path | Live verified result | Audit verdict |
|---|---|---|---|---|
| **Scope 1** | 2549 (DEFRA 2531 + SEAI 18) | yes — `engines/calculation.py` | **2 snapshots + 2 log rows** | Credible, narrowly verified |
| **Scope 2** | 354 (346 electricity, 8 heat, 8 steam, **0 cooling**) | yes, but **no dual-method** | **0 rows** | Partial — dual reporting not implemented |
| **Scope 3** | 4090 across 30 factor families | yes, **no category model** | **0 rows** | Factor-rich, structurally weak |
| Outside of Scopes | 56 | n/a | 0 | presentation only |

## 4. §A — How mature platforms describe scope coverage

Surveyed public capability descriptions (accessed **2026-09-24**):

| Platform | URL | Scope statement (source wording, abbreviated) |
|---|---|---|
| Watershed | `https://watershed.com/platform` | "All scopes and required ESG metrics covered"; FAQ — "purpose-built methodologies for **all 15 Scope 3 emissions categories**"; "2.3 million built-in emissions factors, covering 95% of the global GDP"; "Full calculation transparency and lineage"; "activity-based scope 3.1" |
| Persefoni | `https://www.persefoni.com/` | "Scope 1, 2, and 3 carbon footprints"; "Complete scope 3 footprints with the data you have – **spend-based estimates to actuals**"; "Assurance-grade GHG emissions reporting"; "Every calculation method aligned to the world's most trusted carbon accounting standards"; "Scope 3 Supplier Engagement"; "Financed emissions accounting" |
| Climatiq | `https://www.climatiq.io/` | "1.7M+ scientifically-vetted emission factors covering **spend- and activity-based** emission calculations"; "300+ global regions"; "140+ trusted datasets including ecoinvent, EXIOBASE, and IEA"; factors "expressed in CO2e … taking into account **Global Warming Potential in 100 years (GWP 100)**"; workstreams "Purchased Goods & Services", "Product Carbon Footprint", "Freight & Shipping" |
| Sweep | `https://www.sweep.net/platform` | "Carbon Accounting … across Scope 1, 2, and 3 … follows GHG Protocol standards"; "Flexible data model fits **multiple entities, business units, and geographies**"; "Scales to thousands of suppliers"; "**Multi-framework support**: CSRD, ISSB, GRI, CDP, SB253, TCFD"; "Complete data lineage, **immutable audit trails**" |
| Normative | `https://normative.io/` and `/carbon-accounting/` | **NOT RETRIEVED — HTTP 403 (bot-blocked) on both attempts.** No Normative claim is asserted anywhere in this report. |

Standards sources:

| Standard | URL | Requirement summary (source wording, abbreviated) |
|---|---|---|
| GHG Protocol Corporate Standard | `https://ghgprotocol.org/corporate-standard` | seven Kyoto gases (CO₂, CH₄, N₂O, HFCs, PFCs, SF₆, NF₃); "designed to develop a **verifiable** inventory"; base-year adjustments; "Required gases and GWP values"; programme/policy-neutral |
| GHG Protocol Scope 2 Guidance | `https://ghgprotocol.org/scope-2-guidance` | standardises "purchased or acquired **electricity, steam, heat and cooling**"; "New requirements for accounting for emissions from energy contracts and instruments (such as renewable energy credits)"; "**Eight Scope 2 Quality Criteria** that all contractual instruments must meet in order to be a reliable data source for the scope 2 **market-based method**" |
| GHG Protocol Scope 3 Standard | `https://ghgprotocol.org/standards/scope-3-standard` | "Corporate Value Chain (Scope 3) Accounting and Reporting Standard … assess their entire value chain"; supplier-engagement guidance; GWP values; sample inventory reporting template. The retrieved extract did not enumerate the 15 category names; category names used below are the standard's own numbering as listed in this task. |

**Neutral capability requirements translated from the above** (deliberately *not* vendor-specific
implementations): multi-scope accounting; category-level Scope 3 completeness; both Scope 2 methods
with contractual instruments; large geographically-resolved factor coverage with versioning and GWP
provenance; spend-based *and* activity-based estimation; supplier data collection; data lineage and
immutable audit trails; multi-entity consolidation; multi-framework disclosure; AI that proposes but
remains reviewable.

## 5. §B — Scope 1 audit

| # | Capability | Documented | Code | Route | Factors | Verified |
|---|---|---|---|---|---|---|
| 1 | Stationary combustion | yes | yes | yes | **`Fuels` 486, `Bioenergy` 49** (Scope 1) | 1 snapshot (`Natural gas P5 [kWh]`) |
| 2 | Mobile combustion | yes | yes | yes | **`Delivery vehicles` 648, `Passenger vehicles` 624, `SECR kWh pass & delivery vehs` 383** | not verified |
| 3 | Fugitive emissions | partial | yes | yes | **`Refrigerant & other` 359** (Scope 1) | not verified |
| 4 | Process emissions | no | no | no | **no process/industrial-process factor family exists** | **NOT IMPLEMENTED** |
| 5 | Fuel/activity unit handling | yes | yes | yes | kWh, kWh (Gross/Net CV) 155/155, litres 152, kg 405, tonnes 379, cubic metres 13, GJ 39 | verified structurally |
| 6 | Factor selection | yes | yes — `factor_matching.py` + `factor_selection_policy.py` | yes | 2549 Scope 1 rows | verified |
| 7 | Geographic relevance | yes | yes | yes | `country` GB 7029 / IE 20 | GB only in practice |
| 8 | Reporting year | yes | yes | yes | `reporting_year` **2025 only** | structurally yes |
| 9 | Factor source | yes | yes | yes | `DEFRA-DESNZ` 2531, `SEAI-2025` 18 | verified in both snapshots |
| 10 | Calculation method | yes | yes | yes | `direct_multiply` | verified (`methodology` column) |
| 11 | Evidence | yes | yes | yes | 23 `evidence_line_items` with raw quantity/unit/description | verified (raw values preserved) |
| 12 | Manual review | yes | yes | yes | `activity_clarifications`, `manual_review_queue`, `manual_extraction_items.status` | modelled; 0 clarifications/adjudications recorded |
| 13 | Reporting | yes | yes | yes | report `scopes` section + `emissions_summary` | 4 `report_versions`; **0 artifacts** |

## 6. §C — Scope 2 audit (dedicated)

GHG Protocol Scope 2 = purchased/acquired **electricity, steam, heat, cooling**, and requires **both**
location-based and market-based reporting with eight quality criteria for contractual instruments.

**Factor availability (verified by query, not by row count alone):**

    Scope 2 total: 354 rows
      UK electricity                     4
      UK electricity for EVs           272
      SECR kWh UK electricity for EVs   68
      Heat and steam                     8
      Fuels (Scope 2)                    2
    keyword scan within Scope 2: electricity 346 | heat 8 | steam 8 | COOLING 0

| # | Capability | Status | Evidence |
|---|---|---|---|
| 1 | Electricity activity | **FACTORS + ROUTE** | 346 electricity factors; `unit` kWh 52 and kWh (Gross/Net CV) 310 |
| 2 | Purchased energy (heat/steam) | **FACTORS** | `Heat and steam` 8; `Fuels` Scope 2 2 |
| 3 | Location-based method | **NOT IMPLEMENTED as a method** | no location-based selection, no grid-region model, no labelled method substitution; grid factors exist implicitly (`UK electricity`) but nothing distinguishes a location-based result |
| 4 | Market-based method | **NOT IMPLEMENTED** | no code path except the validated label (row 5) |
| 5 | Contractual instruments (RECs/GOs/PPAs) | **LABEL ONLY** | `domain/disclosure.py:145` `SCOPE2_METHODS = ("LOCATION_BASED","MARKET_BASED")` + `validate_scope2_method()`; **no instrument table, no ingestion, no quality-criteria enforcement** |
| 6 | Renewable energy instruments | **NOT IMPLEMENTED** | no REC/GO/REGO/PPA/residual-mix table or column found |
| 7 | Supplier-specific factors | **PARTIAL** | `suppliers.emission_factor_scope2` exists; `customer_factors` can carry a customer multiplier — but `customer_factors` has **0 rows** and no electricity customer factor exists |
| 8 | Grid/location factors | **FACTORS ONLY** | `country` GB/IE; no grid region, no grid-mix region selection |
| 9 | Country/region | **PARTIAL** | `country` on factors and customer factors; no sub-national resolution |
| 10 | Reporting year | **PARTIAL** | `reporting_year` exists; **only 2025 populated** (DEFRA-2025, SEAI-2025) |
| 11 | Energy unit normalization | **YES (code)** | `core/units.resolve_unit_for_factor`; kWh/GJ present |
| 12 | kWh/MWh conversion | **PARTIAL** | kWh variants exist (kWh, Gross CV, Net CV, GJ); **no MWh unit in the factor set** |
| 13 | Factor unit compatibility | **YES (code)** | unit aliasing (CL-3/P12); mismatches pass through and the engine rejects |
| 14 | Factor provenance | **YES** | `factor_source`, `factor_set`, `factor_id` on snapshots |
| 15 | **Dual-method reporting** | **NOT IMPLEMENTED** | no dual-result storage; a single `scope` string per row; the disclosure layer can *name* a method, nothing computes two |
| 16 | Evidence | **CODE** | `evidence_line_items` (raw qty/unit/page/row); no Scope 2 row exists |
| 17 | Manual review | **CODE** | clarification machinery exists; unused for Scope 2 |
| 18 | Reporting | **CODE** | report `scopes` section aggregates by `scope`; no method split |

**§AD required representative Scope 2 test result:**

    SCOPE 2 E2E TEST FIXTURE MISSING

Evidence: (a) `emissions_logs` holds 2 rows, **all `Scope 1`**; (b) `calculation_snapshots` holds 2
rows, all Scope 1; (c) the only Scope 2-shaped fixtures are **repository-level, not journey-level** —
`tests/integration/test_emissions_logs.py` builds log entities with `unit="kWh"`, `scope="Scope 2"`,
while `tests/integration/test_calculation.py` uses the Scope **1** activity
`"Fuels > Gas fuels > Natural gas P5 (kg CO2e) [kWh]"`; (d) no fixture carries
purchased-electricity document → extraction → mapping → Scope 2 factor → calculation → evidence →
report. The existing Scope 2 tests assert persistence plumbing, not a carbon-accounting journey.

What a future test would need (not created here): a source artefact with a kWh quantity and billing
period; a facility with country/postcode; both a location-based and a market-based electricity factor;
and a method field on the calculation request so two results can be produced and reported together.

**Scope 2 verdict:** electricity/heat/steam *factors* and single-method *calculation* are structurally
possible, but CarbonTally **cannot currently demonstrate GHG Protocol-compliant Scope 2**, because
market-based accounting, contractual instruments, the eight quality criteria, residual mix and
dual-method storage are absent. "LOCATION_BASED"/"MARKET_BASED" exist only as a disclosure-layer label
## 7. §D — Scope 3: all 15 categories

Structural finding first, because it governs every row below:

    grep -rniE 'scope3_category|ghg_category' backend/ --include=*.py   -> NO MATCHES (production code)
    activity_categories.ghg_protocol_category                            -> column EXISTS, 0 ROWS
    product_categories.ghg_protocol_category                             -> column EXISTS, 0 ROWS
    supplier_categories.ghg_protocol_category                            -> column EXISTS, 0 ROWS

CarbonTally therefore has a **complete but unpopulated category taxonomy** and **no production code
that classifies an activity into a GHG Protocol category**. A Scope 3 total can be produced (it is a
`scope` string), but it **cannot be attributed to categories 1–15**, cannot show category completeness,
and cannot state why a category is excluded — all of which the Scope 3 Standard requires.

Status vocabulary per §D: `NOT_IMPLEMENTED`, `DOCUMENTED_ONLY`, `CODE_ONLY`, `PARTIAL`,
`END_TO_END_VERIFIED`, `NOT_APPLICABLE`. Below, **PARTIAL** means *factor families exist that
plausibly serve the category, but there is no category model, no category attribution and no
end-to-end verification*. The category↔family correspondence in the factors column is an **audit
inference from factor-family names**, not a verified mapping — that distinction is the point of this
section.

| Cat | Category | Doc | Code | Factors (family, count) | Calc | Category attribution | E2E | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Purchased goods and services | yes | generic | `Material use` 70 | generic | **none** | none | **PARTIAL** |
| 2 | Capital goods | no | no | none found | — | none | none | **NOT_IMPLEMENTED** |
| 3 | Fuel- and energy-related (not S1/S2) | yes | generic | `WTT-*` 796 (fuels 114, delivery 289, pass vehs 168, bioenergy 49, travel-air 28, travel-sea 3, heat/steam 3, UK elec 2) + `Transmission and distribution` 8 + `UK electricity T&D for EVs` 272 | generic | **none** | none | **PARTIAL** |
| 4 | Upstream transport and distribution | yes | generic | `Freighting goods` **1156** (+WTT delivery 289) | generic | **none** | none | **PARTIAL** |
| 5 | Waste generated in operations | yes | generic + waste policy | `Waste disposal` **134** | generic | **none** | none | **PARTIAL** (§8) |
| 6 | Business travel | yes | generic | `Business travel- air` 112, `- land` 672, `- sea` 12, `Hotel stay` 39 (+WTT 31) | generic | **none** | none | **PARTIAL** |
| 7 | Employee commuting | yes | generic | `Homeworking` **3 only** | generic | **none** | none | **PARTIAL (thin)** |
| 8 | Upstream leased assets | no | no | `Managed assets- vehicles` 948, `- electricity` 4 *(ambiguous: Cat 8 or Cat 13)* | generic | **none** | none | **PARTIAL / AMBIGUOUS** |
| 9 | Downstream transport and distribution | no | no | none found | — | none | none | **NOT_IMPLEMENTED** |
| 10 | Processing of sold products | no | no | none found | — | none | none | **NOT_IMPLEMENTED** |
| 11 | Use of sold products | no | no | none found | — | none | none | **NOT_IMPLEMENTED** |
| 12 | End-of-life treatment of sold products | no | no | none found (Cat 5 waste ≠ Cat 12) | — | none | none | **NOT_IMPLEMENTED** |
| 13 | Downstream leased assets | no | no | ambiguous with `Managed assets` | — | none | none | **NOT_IMPLEMENTED** |
| 14 | Franchises | no | no | none found | — | none | none | **NOT_IMPLEMENTED** |
| 15 | Investments (financed emissions) | no | no | none found | — | none | none | **NOT_IMPLEMENTED** |

Adjacent families not mapped to a category: `Water supply` 2, `Water treatment` 2.

**Tally:** END_TO_END_VERIFIED **0** · PARTIAL **7** (Cats 1, 3, 4, 5, 6, 7, 8) ·
DOCUMENTED_ONLY **0** (documentation narrates Scope 3 generally, but no category is documented-only in
a way that differs from its code status) · NOT_IMPLEMENTED **8** (Cats 2, 9, 10, 11, 12, 13, 14, 15) ·
NOT_VERIFIED (no E2E evidence) **15**.

**§AE at-minimum categories (1, 4, 5, 6, 7):** factor families exist for four of the five — Cat 4 is
the strongest (1156 rows), Cat 1 the weakest (70), Cat 7 thinnest (3). **None** of the five has a
category model, category attribution or an end-to-end verified result, and no representative fixture
for them exists in the demo database.

**Scope 3 verdict:** factor *breadth* is materially better than expected for upstream categories
(4090 rows), but the *accounting structure* the Scope 3 Standard requires — category boundaries,
category completeness and documented exclusion rationale — is **neither implemented in code nor
populated in data**, and **no Scope 3 calculation has ever been persisted** in the demo database.
## 8. §E — Waste / Scope 3 Category 5 (special attention)

**Chain audited:** document activity → waste type → treatment method → quantity → unit → geography →
factor → calculation → evidence.

`Waste disposal` = **134 Scope 3 factors**, structured `Waste disposal > <material> > <treatment route>
(kg CO2e) [tonnes]`. Observed **treatment routes**: Landfill, Composting, Incineration with Energy
Recovery, Closed-loop, Open-loop. Observed **materials**: Organic (garden / mixed food and garden),
Wood, Plastics (rigid / average), Paper and board (board / mixed), Books, Clothing, Metal (scrap /
steel cans), Aggregates, Asphalt, Average construction, Soils, Mineral oil, WEEE (small).

| Requested treatment | Supported? | Evidence |
|---|---|---|
| Landfill | **yes** | e.g. `Plastics: average plastic rigid - Landfill` |
| Incineration | **yes** | `- Incineration with Energy Recovery` routes for many materials |
| Waste-to-energy | **yes, by synonym** | DEFRA names this route "Incineration with Energy Recovery" |
| Composting | **yes** | `Books - Composting`, `Organic: garden waste - Composting` |
| Recycling | **yes, by synonym** | expressed as `- Open-loop` / `- Closed-loop` |
| Reuse | **NO explicit route** | no `Reuse` route observed |
| General waste | **NO generic route** | factors are always material + route specific |
| Mixed waste | **partial** | only as specific mixed materials (e.g. `Organic: mixed food and garden waste`) |
| Hazardous waste | **partial** | only via specific materials (e.g. construction asbestos); **no generic hazardous route** |

**Geography / year / unit:** `country` GB (all waste factors), `reporting_year` 2025,
`factor_source` DEFRA-DESNZ, `factor_set` DEFRA-2025, unit **`tonnes`** (mass-based; no volume-based
waste factors observed).

**Is "waste" alone sufficient?** **No — and that is correct.** The taxonomy is
family > material > **treatment route**, and the canonical corpus names a stream but never a route.
Measured spread between plausible routes for one material:

    4.68568 / 1.00835 = 4.647x

Auto-selecting a route would be guessing. The `D-FS-4` shared-token guard in
`engines/factor_selection_policy.py` is preserved, and waste lines route to clarification where an
operator selects the factor.

**§AF — current P12 waste implementation status (verified, not assumed):**

| Item | Status |
|---|---|
| Category 5 factor coverage (material × route) | **FACTORS PRESENT** (134 rows; 155 rows match waste/recycl including `Waste oils` fuels) |
| GHG Protocol **category attribution** for waste | **NOT IMPLEMENTED** (`activity_categories` empty) |
| Automatic waste resolution | **deliberately NOT implemented** (would be guessing) |
| Clarification routing for ambiguous waste | **CODE EXISTS**; auditable record shape present |
| Waste line → calculation → emissions | **NOT VERIFIED** (0 Scope 3 snapshots; P12-IMPL-02 journey not executed) |
| Supplier attribution on waste lines | **partially wired** (P12-IMPL-02 added the `emissions_logs.supplier_id` write path; 0 rows of evidence) |
| `activity_clarifications` rows recorded | **0** — record shape modelled, no clarification persisted in the demo DB |

**§E verdict:** Category 5 is the **best-prepared Scope 3 category in factor terms** and the only one
with a governed, auditable uncertainty path — but it has **no category attribution and no verified
calculation**, so it is `PARTIAL`, not complete. P12-IMPL-02 does **not** complete Category 5: it
proves extraction breadth (6/6 documents, 21 line items) and adds supplier resolution, while the waste
## 9. §F — Supplier data audit

**Modelled (verified columns).** `suppliers` holds ~58 columns, including carbon-specific ones:

    name, type, supplier_category_id, address_line1..postcode, country, vat_number, company_number,
    tax_id, registration_number, is_certified, certification_type, certification_expiry,
    annual_emissions_scope1, annual_emissions_scope2, annual_emissions_scope3,
    emission_factor_scope1, emission_factor_scope2, emission_factor_scope3, emission_factor_unit,
    supplier_rating, risk_score, compliance_status, contract_start/end, payment_terms, ...

So **supplier-provided scope 1/2/3 emissions and supplier-specific factors are modelled per supplier**.

| # | Capability | Status | Evidence |
|---|---|---|---|
| 1 | Supplier master | **CODE + 1 ROW** | `suppliers` (1 row in demo DB) |
| 2 | Supplier identity | **CODE** | name/postcode/VAT/company number; consumed by the P12-IMPL-02 resolver |
| 3 | Supplier-specific emissions | **MODELLED, UNUSED** | `annual_emissions_scope1/2/3`, all NULL |
| 4 | Supplier activity data | **NOT IMPLEMENTED** | no supplier activity submission table |
| 5 | Supplier-provided factors | **MODELLED, UNUSED** | `emission_factor_scope1/2/3`, `emission_factor_unit` |
| 6 | Supplier questionnaires | **NOT IMPLEMENTED** | no questionnaire/survey table |
| 7 | Supplier data exchange / portal | **NOT IMPLEMENTED** | no invite/upload surface for suppliers |
| 8 | Primary data | **NOT DISTINGUISHABLE in practice** | `emissions_logs.data_source` is **NULL on every row** |
| 9 | Estimated data | **NOT DISTINGUISHABLE in practice** | same column; no `PRIMARY`/`SECONDARY`/`ESTIMATED` enum vocabulary found |
| 10 | Supplier-specific vs average factors | **MODEL PRESENT** | `customer_factors` + `emission_factor_id` provenance; `customer_factors` = 0 rows |
| 11 | Supplier engagement | **NOT IMPLEMENTED** | no engagement workflow found |
| 12 | Supplier attribution | **PARTIAL** | `mapped_supplier_id` + `emissions_logs.supplier_id` (writable since P12-IMPL-02) + `insight_query` dimension; **0 populated rows** |
| 13 | Supplier data quality | **MODELLED, UNUSED** | `risk_score`, `compliance_status`, `supplier_rating` |
| 14 | Supplier evidence | **PARTIAL** | evidence lines attach to the extraction item, not to a supplier record |
| 15 | Supplier correction workflow | **CODE (existing)** | `save_mapped_data(..., mapped_supplier_id, ...)` + `ops_map:applied` audit (P12-IMPL-02) |

**The required distinction:**

| Distinction | Possible today? | Why |
|---|---|---|
| Primary supplier data | **no** | no populated `data_source`, no supplier submission path |
| Activity-based estimate | **partial** | activity factors exist, but the *estimate* nature is not recorded anywhere |
| Spend-based estimate | **no** | no currency/spend factors exist (units are physical only); a currency-unit guard exists at `engines/calculation.py:94` |
| Manually corrected data | **yes** | `extracted_data` vs `mapped_data` + `ops_map:applied` audit + `activity_clarifications.original_activity`/`selected_factor_id` |

**§F verdict:** the supplier *model* is unusually rich — it already anticipates supplier-specific
factors and emissions — but the supplier *workflow* is essentially unbuilt: no collection, no
engagement, and no primary/estimated distinction in the data. Supplier attribution is wired through the
write path (P12-IMPL-02) yet **0 emissions rows carry a supplier**.

## 10. §G — Data quality audit

| Concept | CarbonTally artefact | Status |
|---|---|---|
| Data-quality flag | `emissions_logs.data_source`, `emissions_logs.confidence_score` | **MODELLED, 0 POPULATED** |
| Confidence score | `emissions_logs.confidence_score`; `document_processing_queue.ai_confidence_score`; `ai_mapping_confidence` | **MODELLED**; a legacy average score is computed in `utils/emissions.py:404–489` |
| Completeness | `disclosure.py` `EVIDENCE_COMPLETENESS_STATES = ("COMPLETE","PARTIAL","UNAVAILABLE")` | **CODE EXISTS** (disclosure layer) |
| Review status | `manual_extraction_items.status`, `.qc_by/.qc_at/.qc_notes`, `.quality_score`, `.customer_approved`, `.customer_rejection_reason`; `manual_review_queue.status/priority/sla_*` | **CODE EXISTS**; queue has **0 rows** |
| Blocking validation findings | `engines/validation.py` + open-issue lifecycle | **CODE EXISTS** (previously verified) |
| Audit readiness / package | `data/reporting.py::audit_readiness_from_counts`, `audit_readiness(org_id)`, `audit_package(...)` | **CODE EXISTS** |
| Primary vs secondary data | — | **NOT IMPLEMENTED** (see §F) |
| Temporal representativeness | — | **NOT FOUND** |
| Geographic representativeness | — | **NOT FOUND** |
| Technological representativeness | — | **NOT FOUND** |
| Uncertainty | — | **NOT FOUND** (no uncertainty column on factors or snapshots) |
| Anomaly detection | — | **NOT IMPLEMENTED** in production code (Persefoni advertises anomaly detection; CarbonTally has only `engines/benchmarking.py`, which is explicitly *internal/self-referential* Phase 9 scope) |
| Outlier detection | — | **NOT FOUND** |

**§G verdict:** CarbonTally's equivalent of "data quality" is **state-based, not score-based** — review
status, QC actor, approval state, validation findings, evidence-completeness states, plus an audit-
readiness aggregate. That is a legitimate and arguably more auditable design than a numeric confidence
score, and §G explicitly warns against automatically adding one. The genuine gaps are that the
quality *columns that do exist* (`data_source`, `confidence_score`, `quality_score`) are unpopulated,
## 11. §H — Emission factor management

**Verified `emission_factors` columns:** `id, reporting_year, activity_type, co2e_multiplier,
created_at, updated_at, unit, scope, factor_source, factor_set, country, region_deprecated,
import_batch_id`.

| # | Capability | Status | Evidence |
|---|---|---|---|
| 1 | Factor source | **YES** | `factor_source` (`DEFRA-DESNZ`, `SEAI-2025`) + `factor_set` (`DEFRA-2025`, `SEAI-2025`) |
| 2 | Factor version | **PARTIAL** | `factor_set` encodes the edition (`DEFRA-2025`); no explicit version integer on library factors (`customer_factors.version` does exist) |
| 3 | Publication year | **PARTIAL** | `created_at`/`updated_at` present; **not exposed as a publication year** |
| 4 | Validity year | **PARTIAL** | `reporting_year` (**2025 only**); library factors have no `effective_from`/`effective_to` (customer factors do) |
| 5 | Country | **YES** | `country` GB 7029 / IE 20 |
| 6 | Region | **PARTIAL** | `region_deprecated` exists but is deprecated; no active region/grid dimension |
| 7 | Unit | **YES** | 15 distinct units (see §J) |
| 8 | Scope | **YES** | Scope 1 2549 / Scope 2 354 / Scope 3 4090 / Outside of Scopes 56 |
| 9 | Activity | **YES** | hierarchical `activity_type`, e.g. `Waste disposal > Construction > Aggregates - Landfill (kg CO2e) [tonnes]` |
| 10 | Methodology | **NOT ON FACTORS** | methodology lives on the *snapshot* (`direct_multiply`) |
| 11 | Calculation method | **YES (engine)** | `CalculationMethodology.DIRECT_MULTIPLY`; `calculation_snapshots.methodology` |
| 12 | GWP | **IMPLICIT ONLY** | factors are pre-computed CO2e; **no per-gas/GWP column**. Climatiq states "GWP 100" explicitly; CarbonTally cannot expose a GWP basis |
| 13 | Uncertainty | **NOT FOUND** | no uncertainty column on factors or snapshots |
| 14 | Quality flags | **NOT FOUND on factors** | an unused `factor_status(verified/unverified)` enum exists in the DB |
| 15 | Custom factors | **YES — full lifecycle model** | `customer_factors`: `status`, `version`, `effective_from/to`, `source_reference`, `methodology`, `category`, `country`, `reporting_year`, `factor_source`, `activity_type`, `co2e_multiplier`, `unit`, `scope` — **0 rows** |
| 16 | Factor updates | **CODE** | `api/admin_imports.py` (`provider` = `defra`/`seai`) → `import_batch_id` |
| 17 | Factor deprecation | **PARTIAL** | `region_deprecated` only; no general retirement state on library factors |
| 18 | Factor provenance | **YES** | `factor_id` + `factor_source` + `factor_set` + `import_batch_id` + snapshot `content_hash` |

**§AG / §AH — DEFRA, Irish/SEAI and Customer Custom verification:**

| Dimension | DEFRA | SEAI (Irish) | Customer Custom |
|---|---|---|---|
| Source | `DEFRA-DESNZ` | `SEAI-2025` (provider in `admin_providers.py`) | `customer_factors.factor_source` |
| Country | `GB` 7029 | `IE` **20** | `customer_factors.country` |
| Year | 2025 | 2025 | `reporting_year` + `effective_from/to` |
| Activity | 30 families | **Scope 1 ×18 + Scope 2 ×2 only** | free-form `activity_type` |
| Unit | 15 units | within Scope 1/2 units | `unit` |
| Scope | S1/S2/S3/Outside | **S1 + S2 only** | `scope` |
| Resolution | matching engine | matching engine | **explicit `customer_factor` path in the calculation engine** |
| Provenance | `factor_set`/`factor_source` on snapshot | same | `factor_kind='customer_factor'` + `customer_factor_id` |

**Critical nuance found (CO₂ vs CO₂e):** `backend/api/contracts.py` carries `gas_coverage` — "`CO2` for
SEAI CO2-only factors, `CO2e` for DEFRA" — and states it "preserves the CO2-only (SEAI) vs CO2e (DEFRA)
distinction". SEAI factors are therefore **not always CO2e**, and any aggregation mixing them with
DEFRA CO2e factors compares CO₂ with CO₂e unless the caller honours `gas_coverage`. The schema
anticipates the risk; the emissions path does not visibly enforce it.

**Precedence verification (§AG — automatic DEFRA/SEAI selection must not override a configured
customer factor):**

* `engines/calculation.py` implements a dedicated `customer_factor` path: exactly one of
  `factor`/`customer_factor` is set, `factor_kind` records which was used, `customer_factor_id` is
  persisted, and a customer-factor calculation stores **NULL `emission_factor_id`** (O1) so provenance
  cannot be confused with a library factor.
* Because the customer factor must be *explicitly supplied* on the request, an automatic DEFRA/SEAI
  match cannot silently displace it in the engine.
* Measured limitation: `customer_factors` is **empty (0 rows)**, so precedence is **code-verified but
  not data-verified**; `tests/integration/test_v3m3_customer_factors.py` exists but was **not run**
  (destructive per F-046-1).

## 12. §I, §J, §K — Factor selection, unit normalization, geography

### §I Factor selection: determinism and ambiguity behaviour

Evidence: `engines/factor_matching.py`, `engines/matching_stages.py`,
`engines/factor_selection_policy.py`, `engines/activity_clarification.py`.

| Dimension | Considered? | Evidence |
|---|---|---|
| activity | **yes** | activity-text matching with per-taxonomy-family budget (`_POLICY_FAMILY_CAP`; family = text before ` > `) so no single family monopolises candidates |
| scope | **yes** | `factor_selection_policy.py` scope/family rules; `activity_clarifications.scope` |
| country/region | **partial** | `country` on factors; explicit country **filtering in the matcher not verified** here |
| reporting year | **partial** | `reporting_year` exists; explicit year filtering not verified (only 2025 exists) |
| factor source | **yes** | `factor_source`/`factor_set` persisted on the snapshot |
| unit | **yes** | `core/units.resolve_unit_for_factor` + aliasing |
| customer configuration | **yes** | explicit `customer_factor` path (§11) |

**Ambiguity → REQUEST REVIEW, never GUESS:** `factor_selection_policy.py` refuses a shared/generic
token (e.g. bare `Waste`) as evidence for a specific factor (`D-FS-4`) and blocks rather than picks;
`activity_clarification.py` routes the line to `activity_clarifications`, whose record carries
`original_activity`, `source_evidence_ref`, `clarification`, `clarification_type`, `policy_input`,
`eligible_groups`, `eligible_group_count`, `outcome_status`, `selected_factor_id`,
`selected_factor_name`, `actor_id`, `actor_scope`, `version`, `supersedes_id`, `is_current`,
`re_evaluation_required`.

**Determinism:** `match_request_id` + snapshot `content_hash` + `algorithm_version` make a selection
reproducible, and the factor is persisted by id/source/set. Caveat: `activity_clarifications` holds
**0 rows**, so this path has never run on real data.

### §J Unit normalization

Units in the factor set (15 distinct):

    km 2515 | miles 2181 | tonne.km 754 | kg 405 | tonnes 379 | passenger.km 205 |
    kWh (Gross CV) 155 | kWh (Net CV) 155 | litres 152 | kWh 52 | Room per night 39 |
    GJ 39 | cubic metres 13 | per FTE Working Hour 3 | million litres 2

| Dimension | Status | Evidence |
|---|---|---|
| Supported units | **15** | distance, mass, volume, energy, passenger-km, tonne-km, occupancy-time, per-FTE intensity |
| Conversion logic | **CODE** | `core/units.resolve_unit_for_factor` + alias table (`L`↔litres, `t`↔tonnes, `m3`↔cubic metres, kWh variants) |
| Factor-unit compatibility | **CODE** | alias resolution, then engine rejection on genuine mismatch |
| Unsupported units | **rejected** | mismatch passes through and the engine raises (CL-3/PRC-2 pattern) |
| Manual review on conflict | **CODE** | validation findings / clarification route |
| Raw unit preserved | **YES** | `evidence_line_items.raw_unit`/`raw_quantity`/`raw_description`; `extracted_data.unit` |
| Normalized unit preserved | **YES** | `calculation_snapshots.quantity_unit`; `emissions_logs.unit` |
| Currency (£/€/$) | **guard only** | `engines/calculation.py:94` uses `is_currency_unit`; **no spend/currency factors exist** |
| MWh / gallons | **NOT PRESENT** | not in the factor set |

**No silent conversion of incompatible units was found — the design fails closed.**

### §K Geographic resolution

| Dimension | Status | Evidence |
|---|---|---|
| Country | **YES (factor level)** | `emission_factors.country` GB/IE; `customer_factors.country` |
| Region | **DEPRECATED** | `emission_factors.region_deprecated` |
| Site / facility | **MODELLED** | `facilities` (1), `assets` (1); `mapped_facility_id`/`mapped_asset_id` |
| Grid region | **NOT IMPLEMENTED** | no grid-region dimension — decisive for Scope 2 location-based |
| Supplier location | **PARTIAL** | `suppliers.postcode/city/county/country`; used by resolution, not by factor selection |
| Customer location | **PARTIAL** | `organizations` + metadata; not a factor-selection input |

## 13. §L — Temporal resolution

| Dimension | Status | Evidence |
|---|---|---|
| Activity date | **YES** | `emissions_logs.start_date`/`end_date`; snapshot `date` |
| Billing period | **YES** | P12-IMPL-01 extracted billing periods 6/6 |
| Reporting year | **YES** | `calculation_snapshots.reporting_year`; `emission_factors.reporting_year` |
| Factor year | **2025 ONLY** | a single populated year: `DEFRA-2025`, `SEAI-2025` |
| Factor validity period | **customer factors only** | `customer_factors.effective_from/effective_to`; library factors have none |

**What happens when activity year ≠ factor year? NOT VERIFIED — and this is a live risk.** No
year-mismatch guard, warning or review trigger was found in the mapping/calculation path, and since only
**2025** factors exist, an FY2026 (or FY2024) activity has **no year-matched library factor**. The
canonical investor corpus holds **FY2025 ×3 and FY2026 ×3** documents, so this bears directly on the demo
narrative. Per §L the minimum acceptable behaviour is *warn* or *request review*; the honest current
statement is **unknown / unverified**.

## 14. §M — Organizational boundaries

| Concept | Status | Evidence |
|---|---|---|
| Organizations | **YES** | `organizations` (4 rows); multi-tenant architecture + RLS |
| Facilities | **YES** | `facilities` (1); `mapped_facility_id` |
| Assets | **YES** | `assets` (1); `mapped_asset_id` |
| Suppliers | **YES** | `suppliers` (1) |
| Business units | **NOT FOUND** | no business-unit table/column located (Sweep advertises this) |
| Reporting entities | **PARTIAL** | `processing_entities` is a *processing* concept, not a reporting-entity concept |
| Operational control / financial control / equity share | **NOT IMPLEMENTED** | no consolidation-approach field found |
| Consolidation / multi-entity roll-up | **NOT FOUND** | `data/reporting.py` aggregates per `organization_id`; no cross-entity roll-up |
| Consultants managing clients | **YES** | `consultant_profiles`, `consultant_firm_id`, `consultant_portfolio()`, `consultant_client_detail()` |
| Processing-entity separation | **YES** | `processing_entities`, `processing_entity_id`, `pe_reviewed_by/at`, `pe_qc_by/at` |
| Private-equity / fund portfolio | **NOT SUPPORTED** | no entity above `organizations`; no financed-emissions model |

**Verdict:** the model comfortably supports *one organisation → many facilities → many assets → many
suppliers*, *consultant → many clients*, and *PE work assignment*. It does **not** model business units,
consolidation approaches or portfolios, and **multi-entity reporting** (a rolled-up group inventory) is
absent. Per §M this is reported as a gap, not redesigned.

## 15. §N — Attribution

| Attribution | Persisted | Queryable | Reportable | Evidence |
|---|---|---|---|---|
| organization | **yes** | yes | yes | `organization_id` everywhere; `insight_query` scope dimension |
| facility | **yes** | partial | partial | `mapped_facility_id`; `emissions_logs.metadata.facility_id` |
| asset | **yes** | partial | partial | `asset_id`; `mapped_asset_id` |
| supplier | **yes (writable)** | yes (dimension) | partial | `mapped_supplier_id`; `emissions_logs.supplier_id`; `insight_query` `supplier_id` — **0 populated rows** |
| business unit | **no** | no | no | not modelled |
| category (Scope 3) | **no** | no | no | taxonomy empty; no category column on emissions |
| scope | **yes** | yes | yes | `emissions_logs.scope`, snapshot `scope`, `canonical_scope()` normaliser |
| reporting period | **yes** | yes | yes | `start_date`/`end_date`/`reporting_year`; `emissions_trend()` |
| country | **partial** | partial | no | on factors/customer factors; not carried onto `emissions_logs` |
## 16. §O — Audit trail (first-class audit)

**Design evidence.** `calculation_snapshots` is the audit spine:

    activity, activity_type, quantity, quantity_unit, co2e_multiplier, co2e_kg, scope, date,
    factor_id, factor_source, factor_set, import_batch_id, reporting_year, methodology,
    algorithm_version, content_hash, calculated_at, calculated_by, request_id,
    factor_kind, customer_factor_id, source_item_id, source_file, source_page, performed_by,
    source_line_item_id

plus `emissions_logs.snapshot_id`, `evidence_line_items` (`raw_description`, `raw_quantity`, `raw_unit`,
`source_page`, `line_number`, `row_reference`, `payload_hash`, `extraction_method`,
`materialisation_kind`), and audit tables `audit_logs`, `audit_trail` (**95 rows**),
`processing_audit_trail` (0), `review_audit_trail` (0).

| Requirement | Status | Evidence |
|---|---|---|
| original input | **YES** | `evidence_line_items.raw_*`; item `extracted_data` |
| extracted value | **YES** | `manual_extraction_items.extracted_data` |
| normalized value | **YES** | snapshot `quantity`/`quantity_unit`; `emissions_logs.raw_quantity`/`unit` |
| manual correction | **YES** | `mapped_data` + `activity_clarifications.original_activity` → `selected_factor_id` |
| calculation formula | **PARTIAL** | `methodology=direct_multiply` + `algorithm_version`; no stored expression |
| factor | **YES** | `factor_id`, `factor_source`, `factor_set` |
| factor version | **PARTIAL** | edition via `factor_set`; no version integer |
| user | **YES** | `calculated_by`, `performed_by`, `extracted_by`, `qc_by`, `customer_reviewed_by`, audit `actor` |
| timestamp | **YES** | `calculated_at`, `created_at`, `updated_at`, audit timestamps |
| approval | **PARTIAL** | `customer_approved`; report version approve/finalise routes; `review_audit_trail` empty |
| report version | **YES** | `report_versions` (4) + `report_version_artifacts`; `IMMUTABLE_REPORT_VERSION_STATUSES = ("APPROVED","FINAL")` (D15) |
| data deletion / change | **PARTIAL** | `audit_trail` records status transitions; no verified change-diff or soft-delete record for emissions |
| recalculation | **PARTIAL** | one production reference: `services/automatic_processing.py:1793` — "G6-D: a correction-driven recalculation reaches review again; notify" |

**"Can CarbonTally explain exactly how this number was produced?" — YES, for a calculated row, from
persisted data.** For both live snapshots the chain is reconstructible: `factor_id` +
`factor_source=DEFRA-DESNZ` + `factor_set=DEFRA-2025` + `co2e_multiplier` + `quantity` +
`quantity_unit` + `methodology=direct_multiply` + `content_hash` + `algorithm_version` +
`source_item_id` → `emissions_logs.snapshot_id` → `evidence_line_items`. **Honest caveat:** this is
established from schema plus 2 rows, not from an application route executed in this audit, and
`source_line_item_id` population and `report_version_artifacts` (0 rows) remain unproven.

## 17. §P — Manual review

**Is uncertain data routed to review rather than guessed?** **Yes, by design.** Mechanisms verified:

* Unknown / ambiguous activity → `factor_selection_policy.py` block → `engines/activity_clarification.py`
  → `activity_clarifications` (auditable, versioned, revisable via `supersedes_id`/`re_evaluation_required`).
* Missing / invalid data → `engines/validation.py` findings with an open-issue lifecycle.
* Extraction uncertainty → `manual_extraction_items.status` (`extracted` → `mapped` → `calculated`) and
  `manual_review_queue` (status, priority, `priority_score`, `sla_deadline`, `sla_breached`,
  `escalation_level`, `assigned_to`, `assigned_by`, `review_time_seconds`, `data_entry`).
* The auditability invariant is also enforced at the extraction layer (P12-IMPL-01/02): the system
  fails closed instead of fabricating.

| Requirement | Status | Evidence |
|---|---|---|
| review queue | **MODELLED (0 rows)** | `manual_review_queue` with SLA/priority/escalation fields |
| reason | **YES** | `activity_clarifications.clarification`, `clarification_type`, `policy_input`; validation findings |
| original value | **YES** | `activity_clarifications.original_activity`; `extracted_data` |
| source evidence | **YES** | `activity_clarifications.source_evidence_ref`; `evidence_line_items` |
| corrected value | **YES** | `selected_factor_id`/`selected_factor_name`; `mapped_data`; `mapped_supplier_id` |
| actor | **YES** | `actor_id` + `actor_scope` (clarifications); `_record_item_action_audit(actor=…)` |
| timestamp | **YES** | `created_at`/`updated_at` on clarifications; audit rows |
| downstream recalculation | **PARTIAL** | correction-driven recalculation exists (`automatic_processing.py:1793`); no verified end-to-end correction→new snapshot proof |
| audit history | **PARTIAL** | `audit_trail` 95 rows; `review_audit_trail` **0 rows**; clarification versioning supports history but has never been used |

**Verdict:** manual review is **structurally complete and *more* auditable than a typical
"status + note" implementation** (versioned clarification records with actor scope and supersession),
but it is **operationally unexercised**: 0 queue rows, 0 clarification rows, 0 review-audit rows.
## 18. §Q — Calculation transparency

**CarbonTally can show, for a persisted record:**

    activity data (quantity) × unit conversion (quantity_unit) × emission factor (co2e_multiplier) = co2e_kg

**and additionally** — verified column by column on `calculation_snapshots`:

| Transparency element | Column | Live example (snapshot `f452ee2c-1212-431b-9250-61cc0ddbf4a3`) |
|---|---|---|
| activity data | `quantity` | `12181.4` |
| unit conversion | `quantity_unit` | `kWh (Net CV)` |
| emission factor | `co2e_multiplier` | present (factor `aef1f0bb-4e48-4e4b-a079-c1e827964d07`) |
| result | `co2e_kg` | `2469.169780` |
| factor source | `factor_source` | `DEFRA-DESNZ` |
| factor year | `factor_set` + `reporting_year` | `DEFRA-2025` |
| scope | `scope` | `Scope 1` |
| methodology | `methodology` | `direct_multiply` |
| geography | factor `country` | `GB` — **on the factor row, not on the snapshot** |
| calculation version | `calculated_at`, `content_hash`, `algorithm_version` | hash `ef6d19f14f…` |
| actor | `calculated_by` / `performed_by` | `3fd0f325-16a1-5b53-8fb8-27929cf218fa` |
| source evidence | `source_item_id`, `source_line_item_id`, `source_file`, `source_page` | item `0193ba83-…`, line `9252ca02-…`, file `p12imp_org-a-multi-site-gas-2025.csv`, **page NULL** |

**Verdict: strong.** This is a genuine persisted, reproducible audit record — the closest CarbonTally
comes to the "full calculation transparency and lineage" Watershed advertises. Weaknesses: **geography
is not carried onto the snapshot** (a result cannot self-describe its factor jurisdiction), and
**`source_page` is NULL** on the observed rows.

## 19. §R — Evidence / Source Evidence Viewer

**Verified chain (all identifiers real, read from the demo DB):**

    source document     p12imp_org-a-multi-site-gas-2025.csv      (file name on item + snapshot)
    -> extraction item  0193ba83-ae82-4b08-a03f-4241005fe8e0      (status: calculated)
    -> evidence line    item 0193ba83..., line 1, raw "Natural gas" 12181.4 kwh, method csv, FORWARD
    -> mapped activity  mapped_data.activity = Natural gas, factor_id, mapping_confidence
    -> factor           aef1f0bb-4e48-4e4b-a079-c1e827964d07      (DEFRA-2025, Scope 1)
    -> calculation      snapshot f452ee2c-1212-431b-9250-61cc0ddbf4a3 (co2e 2469.169780, hash ef6d19f14f)
    -> emissions        emissions_logs b96b19f6-26aa-4d96-95e8-e8680a7f4b10 (2469.169780, snapshot linked)
    -> reporting        report section aggregation by scope + insight dimensions

**Arithmetic reconciliation performed during this audit:**

    2469.169780 (log 1) + 1706.734000 (log 2) = 4175.903780
    manual_extraction_items.calculated_emissions_kg_co2e = 4175.9037799999996423139236867427825927734375

The stored item total reconciles with the two persisted emission logs. **This is a verified end-to-end
Scope 1 chain**, not an inference.

**Manually corrected value (§R explicit test):** the demo DB contains exactly **one** `mapped` item —
`3248eaf8-3d9c-41e1-8066-fa19c3f9f10d`, file `t3imp_uk-gas__ORG_022_british_gas_202511.pdf`, factor
`aef1f0bb-…`, `mapped_data.mapping_confidence = 1.0`. It carries mapping output but **no calculation**,
so a corrected value can be observed at the mapping layer yet **cannot** be traced through to a
recalculated result. `activity_clarifications` is empty, so the clarification-based correction path has
no live instance at all.

**Chain gaps found (honest):** `source_page` NULL on both snapshots; `source_page`/`row_reference` NULL
on evidence lines **even where `extraction_method = det:pdf_table`**; `supplier_id` NULL on both logs and
`mapped_supplier_id` NULL on both items; `report_version_artifacts` = 0; and P12's known read-path
observability gap (`GET /api/v3/customer-documents/{id}/extraction` → 404) was not re-tested here.

## 20. §V — Data lineage (concrete test)

| Arrow | Actual model / table | Actual code path | Actual route | Actual persisted identifier |
|---|---|---|---|---|
| INPUT DOCUMENT | `manual_extraction_items.file_name`/`file_url`; storage object | upload → queue | document upload routes | `p12imp_org-a-multi-site-gas-2025.csv` |
| → RAW EXTRACTION | `evidence_line_items.raw_*`; `extracted_data` | `engines/extraction.py`, `engines/invoice_extraction.py`, `services/extraction_suggestions.py` | processing routes | `0193ba83-ae82-4b08-a03f-4241005fe8e0` |
| → NORMALIZED ACTIVITY | `mapped_data.activity`/`unit`; snapshot `quantity`/`quantity_unit` | `engines/factor_matching.py`, `matching_stages.py`, `core/units` | extraction map routes | item `0193ba83-…`; line `9252ca02-1a5a-452d-8943-047f8ff35045` |
| → MANUAL REVIEW *(when needed)* | `activity_clarifications`; `manual_review_queue` | `factor_selection_policy.py` → `activity_clarification.py` | ops map routes | **not exercised (0 rows)** |
| → SUPPLIER | `mapped_supplier_id`; `emissions_logs.supplier_id` | `save_mapped_data`; `engines/supplier_resolution.py` | supplier + ops map routes | **NULL on this record — arrow unproven** |
| → FACTOR | `emission_factors` + snapshot `factor_id`/`factor_source`/`factor_set` | `engines/calculation.py` | calculate routes | `aef1f0bb-4e48-4e4b-a079-c1e827964d07` |
| → CALCULATION | `calculation_snapshots` | `CalculationEngine.calculate` → `_persist_log` | ops/PE calculate routes | `f452ee2c-…`, `47b346f5-…` |
| → EMISSIONS | `emissions_logs` | `EmissionsLogsRepository.create`/`save` | — | `b96b19f6-…`, `647218e4-…` |
| → EVIDENCE | `evidence_line_items.payload_hash` | materialisation | evidence routes | line `9252ca02-…` |
| → REPORT | `report_versions` | `engines/report_generation.py`, `data/report_versions.py` | `/api/v3/reports/*` | 4 report versions, **0 artefacts** |

**Every arrow is established except:** (a) **SUPPLIER** (NULL on the only journey record),
(b) **MANUAL REVIEW** (0 rows anywhere), (c) **→ REPORT** (versions exist, no generated artefact), and
## 21. §S — Reporting

**Surface verified:** `api/v3_reports.py` (types, list, create, get, content, **versions**, download, pdf,
versions/submit, request-changes, reject, approve, finalize) and `api/v3_disclosure.py`
(reports/{id}/disclosure, disclosure lines, **project**, intensity GET/POST, applicability GET/POST,
narrative GET/PUT, **finalisation-check**, **approve**, **finalise**, **frozen-artefact**,
frozen-artefact/signed-url). Data/engines: `engines/report_generation.py`, `data/report_versions.py`,
`data/report_artefacts.py`, `data/disclosure*.py`.

| Capability | Status | Evidence |
|---|---|---|
| Scope 1/2/3 in reporting | **YES (as a `scope` grouping)** | `report_generation.py` section `("scopes","Scope summaries")` + `_scopes_section(...)`; `canonical_scope()` |
| total emissions | **YES** | `emissions_summary()`, `_scopes_section` |
| tCO2e | **PARTIAL** | canonical stored unit is `kg CO2e`; tCO2e is presentation only |
| reporting period | **YES** | date ranges + `reporting_year`; `emissions_trend(months)` |
| comparative years | **PARTIAL** | year is a comparison dimension; one factor year + one live period → unverified |
| categories | **NO** | Scope 3 taxonomy empty; no category section |
| organizational entities | **PARTIAL** | per-organisation only; no group roll-up (§14) |
| facilities | **PARTIAL** | facility dimension in aggregation; `mapped_facility_id` |
| suppliers | **CODE ONLY** | supplier is an Insight dimension; `data/reporting.py:394` filters `mapped_supplier_id`; **0 rows** |
| methodology | **PARTIAL** | snapshot `methodology`/`algorithm_version`; report data-sources narrative |
| factor provenance | **PARTIAL** | snapshot provenance strong; **0 report artefacts** embed it |
| data quality | **PARTIAL** | `audit_readiness()`, `audit_readiness_from_counts()` |
| manual adjustments | **PARTIAL** | corrections traceable in records; no "manually adjusted" report line |
| approvals | **YES (routes)** | version submit/request-changes/reject/approve/finalize; disclosure finalisation-check/approve/finalise |
| report versioning | **YES** | `report_versions` (**4**), artefacts (0), `IMMUTABLE_REPORT_VERSION_STATUSES` (D15) |
| export | **CODE** | download + PDF routes; frozen-artefact signed-URL route |
| audit support | **PARTIAL** | `audit_readiness()`, `audit_package()`, `org_audit_activity()`; `review_audit_trail` empty |

**Presentation layer or auditable record? Both exist in design; the auditable half is unproven.**
Versioning, immutability states, approval/finalisation/freeze routes and signed-URL artefacts are exactly
what an auditable reporting record needs — yet `report_version_artifacts = 0` and `disclosure_values = 0`
mean **no report has ever been produced, frozen or evidenced** here. Defensible statement: *the
## 22. §T — Reporting frameworks

| Framework | Support status | Evidence |
|---|---|---|
| GHG Protocol | **DOCUMENTED + MAPPED (seed)** | `disclosure_frameworks` row `GHG_PROTOCOL`, `is_primary_foundation = true` |
| UK SECR | **MAPPED (seed) only** | row `UK_SECR` (`jurisdiction_statute`); purpose "UK SECR Report"; **no requirement content** (`disclosure_requirement_versions` = 0) |
| ESRS E1 (CSRD) | **MAPPED (seed) only** | row `ESRS_E1` (`eu_standard`); purpose "ESRS E1 Quantitative Report"; `activity_categories.esrs_e1_category` **column exists, 0 rows** |
| ISSB / IFRS S2 | **COLUMN ONLY** | `activity_categories.issb_category`, `product_categories.issb_category` unpopulated |
| CDP | **NOT FOUND** | no framework row, no code |
| SBTi | **NOT FOUND** | no target-setting model |
| PCAF (financed emissions) | **NOT FOUND** | no financed-emissions model |
| TCFD / GRI / SB 253 | **NOT FOUND** | no rows or code |

**§T discipline applied:** CarbonTally is **not** claimed compliant with any framework merely because a
field exists. On the DOCUMENTED / IMPLEMENTED / MAPPED / VERIFIED ladder: GHG Protocol is
**DOCUMENTED + MAPPED** (seed row plus scope/category columns); UK SECR and ESRS E1 are **MAPPED only** —
`domain/disclosure.py` states the seeds carry "identities ONLY; no regulatory content"; and **no**
framework reaches IMPLEMENTED or VERIFIED in this environment. The separation between *accounting
methodology* (GHG Protocol — genuinely implemented for Scope 1) and *disclosure requirements*
(SECR/ESRS/ISSB — scaffold) is real and correctly drawn in the schema.

## 23. §U — Multi-year and recalculation

| Capability | Status | Evidence |
|---|---|---|
| Maintain multiple reporting years | **PARTIAL** | `reporting_year` on factors/snapshots/customer factors; **only 2025 factors populated** |
| Preserve historical calculations | **YES (design)** | immutable-by-intent snapshots with `content_hash` + `algorithm_version`; report versions immutable when APPROVED/FINAL (D15) |
| Update factors without silently changing history | **PARTIAL** | snapshots pin `factor_id`/`co2e_multiplier` so history is not rewritten — but there is **no factor-version/validity model** per activity and no recalculation policy document was found |
| Rerun calculations | **PARTIAL** | one production reference: correction-driven recalculation (`automatic_processing.py:1793`); no general "recalculate year" capability |
| Preserve previous report versions | **YES (routes + rows)** | `report_versions` (4), version routes, immutability states; artefacts 0 |
| Identify methodology changes | **PARTIAL** | `algorithm_version` + `methodology` per snapshot; no change-log |
| Identify factor changes | **PARTIAL** | `factor_set`/`import_batch_id` distinguish epochs; no per-factor change record |
| Compare years | **PARTIAL** | year is a comparison dimension; unverified with one factor year |

**Why this matters here:** the canonical investor corpus is **FY2025 ×3 + FY2026 ×3**. With only
**DEFRA-2025/SEAI-2025** loaded and no year-mismatch policy (§13), FY2026 documents have **no
year-matched factor** and no defined behaviour. Survivable for a single demo period; a genuine gap for a
multi-year investor story.

## 24. §AI — AI / automation governance

| Competitor approach (public wording) | CarbonTally equivalent |
|---|---|
| Watershed: "AI agents to clean, transform, and analyze your data"; "Automated PDF ingestion and processing"; "built-in human review and transparent calculations"; "Clear audit trail and AI-output sourcing" | `engines/ai_extraction.py`, `engines/invoice_extraction.py` (deterministic), `services/extraction_suggestions.py`; `document_processing_queue.ai_confidence_score` / `ai_mapping_confidence`; `mapped_data.mapping_confidence` (observed = 1.0); `manual_review_queue` + `activity_clarifications` as the human gate |
| Persefoni: "Anomaly Detection … detect statistical anomalies for key data sets such as electricity consumption"; "Natural Language based Emission Factor Mapping … (Coming Soon)" | **No anomaly detection in production code.** `engines/benchmarking.py` is explicitly self-referential/internal (Phase 9 scope) |
| Climatiq: "Custom AI for fast mapping — Mapping Agent … without sacrificing control" | `engines/factor_matching.py` + `matching_stages.py` + `factor_selection_policy.py` with candidate budgets and refusal on ambiguous tokens |
| Sweep: "AI-assisted mapping works with your data as it is"; "AI-powered automation handles mapping, validation, and workflows" | Same as above, plus `engines/validation.py` findings and clarification routing |

**Is CarbonTally's approach safely governed? Yes, and this is a genuine strength.** The verified
governance pattern is: **automation proposes → policy decides → ambiguity blocks → a human resolves with
an auditable record.** Concretely:

* `factor_selection_policy.py` refuses shared/generic tokens (bare `Waste`, `D-FS-4`) rather than
  guessing — the opposite of silent AI invention.
* `activity_clarification.py` + `activity_clarifications` capture the original activity, the reason, the
  eligible groups, the selected factor, the actor (with `actor_scope`) and supersession history.
* P12-IMPL-01 replaced heuristic PDF guessing with a deterministic invoice-table parser (`PIPELINE_VERSION`
  `v3-auto-1.2`), and P1 remains **shadow, unpromoted**.
* Verification observed in data: one mapped item carries `mapping_confidence = 1.0`, i.e. confidence is
  *recorded* rather than used to bypass review.

Residual gaps: `ai_confidence_score`/`ai_mapping_confidence` are **nullable and unpopulated** in the
automated records observed, and no threshold policy governing when confidence forces review was verified
## 25. §W — Investor-readiness benchmark (three levels, deliberately not mixed)

### W1. INVESTOR DEMO (10–15 minute demonstration)

| Requirement | Status | Evidence |
|---|---|---|
| Upload a realistic supplier PDF | **PASS** | P12-IMPL-01: 6/6 canonical PDFs, 21 line items |
| Extract supplier/customer/ref/date/period | **PASS** | 6/6 each (P12-IMPL-01) |
| Extract line items with quantity/unit | **PASS** | 21/21 units, 0 false positives |
| **Refuse to guess** when uncertain | **PASS (differentiator)** | waste blocks at clarification; `D-FS-4`; 4.647× spread |
| Show where a number came from | **PASS** | verified snapshot chain (§19) with `content_hash` |
| Scope 1 result end-to-end | **PASS** | 2 snapshots + 2 logs; item total reconciles |
| Scope 2 story | **FAIL** | fixture missing; dual-method absent |
| Scope 3 story | **FAIL** | 0 Scope 3 results; no category attribution |
| Supplier reused across documents | **FAIL (not demonstrated)** | resolver unit-tested; 0 suppliers resolved on real documents |
| Waste line reaches a number | **FAIL** | blocks at clarification; 0 clarification rows |
| Report produced from real data | **FAIL** | `report_version_artifacts = 0` |
| Multi-year FY2025 + FY2026 | **FAIL** | only 2025 factors; no year-mismatch policy |

### W2. PILOT / EARLY CUSTOMER (safe real-customer use)

| Requirement | Status |
|---|---|
| Manual-review queue with assignment/SLA | MODELLED, **0 rows** |
| Auditable correction → recalculation → new snapshot | PARTIAL (one recalculation reference; unverified) |
| Scope 2 location + market based | NOT IMPLEMENTED |
| Factor-year alignment policy | MISSING |
| Scope 3 category completeness reporting | MISSING |
| Primary vs estimated data distinction | MISSING (column only) |
| Multi-entity / consolidation reporting | MISSING |
| Report artefact generation and retention | NOT EXERCISED |
| Tenant-isolation regression green | PARTIAL (12/92 disposable-integration failures carried) |

### W3. PRODUCTION / ASSURANCE

| Requirement | Status |
|---|---|
| Immutable, versioned, signed report artefacts | ARCHITECTED, **0 artefacts** |
| Regulatory requirement content (SECR/ESRS/ISSB) | NOT SEEDED (`disclosure_requirement_versions = 0`) |
| Reviewer/QC audit trail in use | EMPTY (`review_audit_trail = 0`) |
| GWP/gas breakdown, uncertainty | ABSENT |
| External assurance support / verification programme | ABSENT (Watershed advertises an assurance programme; Sweep advertises immutable trails for assurance) |
## 26. §X — Competitor-inspired capability matrix

Competitor values use `YES` / `PARTIAL` / `NOT FOUND` / `NOT DISCLOSED` from **public pages only**;
CarbonTally values use the §D vocabulary with evidence. **No ranking is implied.** Normative is
`NOT RETRIEVED` in every row because both fetch attempts returned HTTP 403.

| Capability | Watershed | Persefoni | Normative | Climatiq | Sweep | CarbonTally | Evidence |
|---|---|---|---|---|---|---|---|
| Scope 1 | YES | YES | NOT RETRIEVED | NOT DISCLOSED | YES | **END-TO-END VERIFIED (narrow)** | 2 snapshots + 2 logs, DEFRA-2025 |
| Scope 2 | YES | YES | NOT RETRIEVED | NOT DISCLOSED | YES | **PARTIAL** | 354 factors; no dual-method; no fixture |
| Scope 3 | YES ("all 15") | YES | NOT RETRIEVED | YES (S3.1, freight) | YES | **PARTIAL ×7 / NOT_IMPLEMENTED ×8** | §7 |
| Scope 2 location + market based | NOT DISCLOSED | NOT DISCLOSED | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **LABEL ONLY** | `SCOPE2_METHODS` |
| Contractual instruments (REC/GO/PPA) | NOT DISCLOSED | NOT DISCLOSED | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **NOT IMPLEMENTED** | no table/column |
| Spend-based estimation | PARTIAL | **YES** | NOT RETRIEVED | **YES** | NOT DISCLOSED | **NOT IMPLEMENTED** | no currency factors |
| Factor library size | YES ("2.3 million") | NOT DISCLOSED | NOT RETRIEVED | YES ("1.7M+") | NOT DISCLOSED | **7049 rows (DEFRA 2025, GB/IE)** | `emission_factors` |
| Geographic coverage | YES ("95% of global GDP") | NOT DISCLOSED | NOT RETRIEVED | YES ("300+ regions") | YES ("geographies") | **2 countries (GB 7029 / IE 20)** | `country` |
| GWP basis exposed | PARTIAL ("Kyoto gas breakdowns") | NOT DISCLOSED | NOT RETRIEVED | **YES** ("GWP 100") | NOT DISCLOSED | **NOT FOUND** | no gas/GWP column |
| Factor versioning / provenance | YES (implied) | YES | NOT RETRIEVED | YES (datasets) | NOT DISCLOSED | **PARTIAL (provenance strong, version weak)** | `factor_set`, `import_batch_id` |
| Calculation transparency / lineage | **YES** | YES ("assurance-grade") | NOT RETRIEVED | YES ("full breakdown") | YES ("complete data lineage") | **CODE + VERIFIED (narrow)** | §19 snapshot chain + hash |
| Immutable audit trail | YES | YES | NOT RETRIEVED | NOT DISCLOSED | **YES** | **PARTIAL** | D15 immutability; `audit_trail` 95 / `review_audit_trail` 0 |
| Manual review / human-in-loop | **YES** | YES | NOT RETRIEVED | YES | NOT DISCLOSED | **CODE + auditable design, 0 rows** | `activity_clarifications`, `manual_review_queue` |
| Supplier engagement / portal | YES | **YES** | NOT RETRIEVED | NOT DISCLOSED | **YES** ("supplier portals") | **NOT IMPLEMENTED** | no portal/questionnaire |
| Supplier-specific factors | NOT DISCLOSED | YES | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **MODELLED, UNUSED** | `suppliers.emission_factor_scope1/2/3` |
| Primary vs estimated distinction | NOT DISCLOSED | YES ("estimates to actuals") | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **SCHEMA ONLY, NULL** | `emissions_logs.data_source` |
| Multi-entity / business units | NOT DISCLOSED | YES | NOT RETRIEVED | NOT DISCLOSED | **YES** | **PARTIAL** | orgs 4 / facilities 1 / assets 1 |
| Consolidation approaches | NOT DISCLOSED | NOT DISCLOSED | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **NOT IMPLEMENTED** | none found |
| Regulatory frameworks | YES (CSRD, CA) | YES (SB 253/261) | NOT RETRIEVED | NOT DISCLOSED | **YES** (CSRD/ISSB/GRI/CDP/SB253/TCFD) | **MAPPED (3 seeds)** | `disclosure_frameworks` |
| Report versioning / immutability | YES | NOT DISCLOSED | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **CODE, 0 artefacts** | `report_versions` 4 |
| AI extraction / mapping | YES ("agents") | YES (Copilot, NL mapping) | NOT RETRIEVED | YES ("Mapping Agent") | YES ("AI-assisted mapping") | **YES, governed** | policy block → clarification |
| Anomaly detection | NOT DISCLOSED | **YES** | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **NOT IMPLEMENTED** | none in production code |
| Financed emissions / PCAF | NOT DISCLOSED | **YES** | NOT RETRIEVED | NOT DISCLOSED | YES | **NOT IMPLEMENTED** | none found |
| Product carbon footprint | NOT DISCLOSED | NOT DISCLOSED | NOT RETRIEVED | **YES** (PCF Studio) | PARTIAL | **NOT IMPLEMENTED** | none found |
| Peer benchmarking | YES | NOT DISCLOSED | NOT RETRIEVED | NOT DISCLOSED | NOT DISCLOSED | **PARTIAL (internal only)** | `engines/benchmarking.py` |
## 27. §Y — CarbonTally scope matrix

Legend: `Y` = yes/verified present · `P` = partial · `N` = no/absent · `R` = route exists ·
`E2E` = end-to-end verified with a persisted result.

| Scope | Activity / Category | Documentation | Code | Factor | Route | Calculation | Persistence | Evidence | Reporting | E2E |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Stationary combustion | Y | Y | Y (Fuels 486, Bioenergy 49) | Y | Y | Y | Y | P | **Y** |
| S1 | Mobile combustion | Y | Y | Y (Delivery 648, Passenger 624) | Y | Y | Y | Y | P | N |
| S1 | Fugitive emissions | P | Y | Y (Refrigerant 359) | Y | Y | Y | Y | P | N |
| S1 | Process emissions | N | N | **N** | N | N | N | N | N | N |
| S2 | Electricity | Y | Y | Y (346) | Y | Y | Y | P | P | N |
| S2 | Heat / steam | Y | Y | Y (Heat and steam 8) | Y | Y | Y | P | P | N |
| S2 | Cooling | N | N | **N (0 rows)** | N | N | N | N | N | N |
| S2 | Location-based method | P | P | P (grid factors) | N | N | N | N | N | N |
| S2 | Market-based method | P | **N** | N | N | N | N | N | N | N |
| S2 | Contractual instruments | N | N | N | N | N | N | N | N | N |
| S3.1 | Purchased goods and services | Y | generic | P (Material use 70) | Y | Y | Y | P | N | N |
| S3.2 | Capital goods | N | N | N | N | N | N | N | N | N |
| S3.3 | Fuel- and energy-related activities | Y | generic | Y (WTT 796 + T&D 8 + EV T&D 272) | Y | Y | Y | P | N | N |
| S3.4 | Upstream transportation and distribution | Y | generic | Y (Freighting goods 1156) | Y | Y | Y | P | N | N |
| S3.5 | Waste generated in operations | Y | generic + policy | Y (Waste disposal 134) | Y | Y | Y | P | N | N |
| S3.6 | Business travel | Y | generic | Y (air 112, land 672, sea 12, hotel 39) | Y | Y | Y | P | N | N |
| S3.7 | Employee commuting | Y | generic | **P (Homeworking 3)** | Y | Y | Y | P | N | N |
| S3.8 | Upstream leased assets | N | N | P (Managed assets 948/4, ambiguous) | Y | Y | Y | P | N | N |
| S3.9 | Downstream transportation and distribution | N | N | N | N | N | N | N | N | N |
| S3.10 | Processing of sold products | N | N | N | N | N | N | N | N | N |
| S3.11 | Use of sold products | N | N | N | N | N | N | N | N | N |
| S3.12 | End-of-life treatment of sold products | N | N | N | N | N | N | N | N | N |
| S3.13 | Downstream leased assets | N | N | N (ambiguous with S3.8) | N | N | N | N | N | N |
| S3.14 | Franchises | N | N | N | N | N | N | N | N | N |
| S3.15 | Investments (financed emissions) | N | N | N | N | N | N | N | N | N |
| — | Water supply / treatment | P | generic | Y (2 + 2) | Y | Y | Y | P | N | N |
| — | Outside of Scopes (WTT/bioenergy presentation) | P | Y | Y (56) | Y | Y | Y | P | P | N |

**How to read "Code = generic":** the mapping/calculation/persistence/evidence machinery is shared and
real, but **nothing classifies the activity into a Scope 3 category** (`activity_categories` is empty and
no production code sets a category), so the category column reflects *inferred* applicability only.

## 28. §Z — Gap classification

| ID | Gap | Class | Evidence |
|---|---|---|---|
| G-01 | No GHG Protocol Scope 3 category model or attribution | **G4** (data-model) | `activity_categories` 0 rows; no `scope3_category` in code |
| G-02 | Scope 2 market-based method + contractual instruments absent | **G4 + G3** | only `SCOPE2_METHODS` label |
| G-03 | No cooling factor family | **G1** (factor/data) | 0 cooling rows in Scope 2 |
| G-04 | No Scope 2 end-to-end fixture or result | **G9** (verification) | 0 Scope 2 logs/snapshots |
| G-05 | No Scope 3 end-to-end result for any category | **G9** | 0 Scope 3 logs/snapshots |
| G-06 | Factor data limited to one year (2025) and two countries | **G1** | `reporting_year` 2025 only; GB/IE |
| G-07 | No factor-year mismatch policy (warn/block/review) | **G3/G8** | not found in mapping/calculation |
| G-08 | `source_page`/`row_reference` unpopulated on evidence lines and snapshots | **G5** (evidence) | `page -`, `row -` observed |
| G-09 | Supplier resolution not exercised on real documents; 0 populated supplier attribution | **G9 + G2** | `suppliers` 1; `supplier_id` 0 populated |
| G-10 | Manual-review queue/clarification/review-audit never exercised (0 rows) | **G8** | 0/0/0 |
| G-11 | Primary-vs-estimated data distinction unpopulated | **G5/G4** | `data_source` NULL everywhere |
| G-12 | No report artefact ever generated/frozen | **G6** | `report_version_artifacts` 0 |
| G-13 | Scope 3 documentation overstates implemented capability | **G0** (wording) | docs narrate Scope 3; code has no categories |
| G-14 | No regulatory requirement content for SECR/ESRS/ISSB | **G10** | `disclosure_requirement_versions` 0 |
| G-15 | Gas/GWP breakdown and uncertainty absent | **G5/G1** | no gas/GWP/uncertainty columns |
| G-16 | Geography not carried onto the calculation result | **G5** | `country` on factor only |
| G-17 | No multi-entity/consolidation roll-up or control approach | **G4 + G10** | no business-unit/consolidation model |
| G-18 | Spend-based estimation path absent | **G2/G1** | no currency factors |
| G-19 | Supplier engagement/portal/questionnaire absent | **G2** | no tables/routes |
| G-20 | Structure-only safeguards for tenant isolation vs 12/92 integration failures | **G7** (security) | carried Step-2 blocker |
| G-21 | Extraction read-path observability gap (404) | **G5** | P12 finding, not re-tested |
| G-22 | AI confidence values recorded but unused/unpopulated in automated rows | **G8** | `ai_confidence_score` NULL |
## 29. §AA — Prioritisation (CarbonTally only; no scores, no ranking)

| Priority | Gap IDs | Factual basis |
|---|---|---|
| **INVESTOR BLOCKER** | G-04, G-05, G-09, G-10, G-12 | The demo cannot currently show a Scope 2 result, a Scope 3 result, an operator resolving an uncertain line, or a report from real data. Each is a *missing artefact*, not a missing architecture: the machinery exists but has produced 0 rows |
| **PILOT BLOCKER** | G-01, G-07, G-11, G-17, G-20, G-08 | A real customer needs category-level Scope 3 completeness, a factor-year policy, primary-vs-estimated labelling, multi-entity reporting, proven tenant isolation and page-level evidence |
| **PRODUCTION / ASSURANCE BLOCKER** | G-02, G-14, G-15, G-12, G-23 | Assurance needs contractual-instrument handling and dual Scope 2, framework requirement content, gas/GWP and uncertainty disclosure, immutable generated artefacts, and anomaly detection |
| **POST-DEMO ENHANCEMENT** | G-03, G-06, G-16, G-18, G-19, G-21, G-22 | Cooling factors, multi-year/multi-country factor load, country-on-result, spend-based estimation, supplier portal, extraction read-path, AI-confidence thresholds |
| **WORDING / DOC-SHORTFALL** | G-13 | Scope 3 documentation implies broader coverage than the code supports; correcting the wording is free and should be first |

## 30. §AB — Non-implementation record (audit only; no fix applied)

**1. Scope 3 category attribution** — FILE: `backend/domain/` (no category model) · FUNCTION: none
(grep `scope3_category|ghg_category` → no matches) · ROUTE: `backend/routes/reference.py` exposes
`activity_categories` (empty) · DATA MODEL: `activity_categories.ghg_protocol_category`; no category
column on `emissions_logs`/`calculation_snapshots` · EXPECTED: every Scope 3 emission attributable to one
of cats 1–15 with included/excluded rationale · ACTUAL: columns exist, 0 rows; emissions carry only a
free-text `scope` · FOLLOW-UP: populate the taxonomy + add category resolution (**PO decision + migration
required; not authorised here**).

**2. Scope 2 market-based accounting** — FILE: `backend/domain/disclosure.py:145,252` · FUNCTION:
`validate_scope2_method()` only · ROUTE: `/api/v3/reports/{id}/disclosure/*` · DATA MODEL: no
instrument/REC/GO/PPA/residual-mix table · EXPECTED: dual location + market results with the eight quality
criteria enforced · ACTUAL: one `scope` string per row; no method computation · FOLLOW-UP: PO decision +
schema work; **must not be improvised**.

**3. Factor-year mismatch policy** — FILE: `backend/engines/factor_matching.py`,
`factor_selection_policy.py`, `validation.py` · ROUTE: map/calculate routes · DATA MODEL:
`emission_factors.reporting_year` (2025 only) vs `calculation_snapshots.reporting_year` · EXPECTED:
warn / block / request review when activity year ≠ factor year · ACTUAL: no such rule found · FOLLOW-UP:
define with the PO — the FY2026 half of the investor corpus depends on it.

**4. Evidence location detail** — FILE: `backend/data/evidence_line_items.py` · FUNCTION: evidence-line
materialisation · ROUTE: evidence routes · DATA MODEL: `evidence_line_items.source_page`,
`.row_reference` (both NULL) · EXPECTED: a PDF evidence line names page/row so a reviewer can open the
source at the right place · ACTUAL: `page -`, `row -` even for `det:pdf_table` rows · FOLLOW-UP: populate
from the parser (P12-IMPL-01 already tracks pages internally).

**5. Supplier attribution on a real record** — FILE: `backend/engines/supplier_resolution.py`,
`backend/api/v3_operations.py` · FUNCTION: `classify()`, `_run_line_calculation` · ROUTE:
`POST /entities/{entity_id}/extraction/items/{item_id}/map` + internal ops map route · DATA MODEL:
`mapped_supplier_id` → `emissions_logs.supplier_id` · EXPECTED: an operator-confirmed supplier is
persisted and reaches the emission · ACTUAL: path wired and unit-tested; **0 rows populated**; no
automatic-pipeline caller · FOLLOW-UP: wire into `services/automatic_processing.py` and run the journey.

**6. Report artefact generation** — FILE: `backend/data/report_versions.py`, `report_artefacts.py`,
`api/v3_reports.py` · ROUTE: `/api/v3/reports/{id}/versions/*`, `/frozen-artefact` · DATA MODEL:
`report_versions` (4) → `report_version_artifacts` (0) · EXPECTED: an approved/finalised report produces
an immutable artefact · ACTUAL: versions exist, no artefact ever generated · FOLLOW-UP: exercise the
frozen-artefact path end-to-end.

## 31. §AC — Actual testing performed (read-only)

| Check | Method | Result |
|---|---|---|
| Factor scope/set/country/year/unit distributions | read-only SQL aggregates | §2, §5–§13 |
| Category taxonomy population | `SELECT` on 3 category tables | 0 rows each |
| Scope 2 fixture search | grep + integration-test inspection + log/snapshot scope query | `SCOPE 2 E2E TEST FIXTURE MISSING` |
| End-to-end chain for a real record | SQL join item → snapshot → evidence → log + arithmetic reconciliation | **verified** (§19), total 4175.903780 |
| Manually corrected value trace | query `status='mapped'` items | 1 item, **no** calculation → arrow unproven |
| Manual-review artefacts | counts on queue/clarifications/review-audit | 0 / 0 / 0 |
| Reporting artefacts | counts on versions/artefacts/disclosure values | 4 / 0 / 0 |
| Multi-entity data | counts orgs/facilities/assets/members | 4 / 1 / 1 / 8 |
| Integration suites | **not run** (destructive per F-046-1) | — |

## 32. §AJ — The 26 required answers

1. **Credible Scope 1 coverage?** **Yes, narrowly.** 2549 factors (stationary/mobile/fugitive), a complete
   calculation+provenance path, 2 verified end-to-end results. Process emissions absent.
2. **Credible Scope 2 coverage?** **No.** Factors exist, but market-based accounting, contractual
   instruments, grid-region resolution and dual-method storage are absent, and there is **no** Scope 2
   result or fixture. `SCOPE 2 E2E TEST FIXTURE MISSING`.
3. **Credible Scope 3 coverage?** **No, not as GHG-Protocol Scope 3.** 4090 upstream-leaning factors
   exist, but no category model, no category attribution, no supplier engagement, **zero** Scope 3 results.
4. **Categories genuinely end-to-end verified?** **Zero.** Cats 1, 3, 4, 5, 6, 7, 8 have factors and shared
   machinery only.
5. **Documented-only categories?** **None uniquely** — documentation narrates Scope 3 generally; no category
   is documented without at least factors.
6. **Factors but no application route?** **None entirely route-less** — the generic routes reach all factor
   families. What cats 2 and 9–15 lack is **factors**, not routes.
7. **Code but no verified factors?** The shared code is exercised for Scope 1 only; cat 3/4/6/7/8 factors
   exist but their category intent is unverified.
8. **Calculations but no evidence?** **None** — every calculation observed has evidence lines.
9. **Evidence but no reporting?** **Yes, at scale** — 23 evidence lines; **0 report artefacts**, 0
   disclosure values.
10. **Handles ambiguous data without guessing?** **Yes** — the strongest, most differentiated property found.
11. **Is manual review auditable?** **By design yes** (original value, reason, actor, actor scope,
    versioning, supersession); **operationally unproven** (0 rows).
12. **Do corrections trigger correct downstream recalculation?** **Unverified** — one production
    reference; the only mapped item never reached calculation.
13. **Supplier-specific data distinguished from estimates?** **No** — `data_source` NULL on every row.
14. **Factor provenance preserved?** **Yes** — `factor_id`, `factor_source`, `factor_set`,
    `import_batch_id`, `content_hash`, `factor_kind`, `customer_factor_id`; weakened by CO₂-vs-CO₂e
    (`gas_coverage`) not being enforced in the emissions path.
15. **Can it explain an individual calculation?** **Yes** — verified with real IDs and reconciled arithmetic.
16. **Historical calculations preserved?** **Yes by design**; no recalculation policy, one factor year.
17. **Multi-entity reporting?** **No** — no roll-up, business-unit model or consolidation approach.
18. **Supplier attribution?** **Partial** — write path wired (P12-IMPL-02), Insight dimension exists,
    **0 populated rows**.
19. **Location-based vs market-based demonstrated?** **No** — validated labels only.
20. **All documented Scope 3 categories demonstrable?** **No** — documentation implies more than the code supports.
21. **Relevant competitor capabilities?** Category-level Scope 3 completeness; dual-method Scope 2 with
    instruments; factor provenance/versioning/GWP transparency; lineage + immutable audit trails;
    primary-vs-estimated labelling; multi-entity consolidation; supplier data collection; framework
    disclosure content; governed AI with human review.
22. **Unnecessary for the current demo?** Financed emissions/PCAF, product carbon footprints, supplier
    portals, peer benchmarking, targets modelling, anomaly detection, 1.7M-factor libraries/300+ regions,
    CDP/GRI/TCFD mappings, spend-based estimation.
23. **Investor-demo blockers?** Scope 2 result; Scope 3 result; operator-resolved clarification on screen;
    supplier reuse demonstrated; report produced from real data; FY2026 factor-year handling.
24. **Pilot blockers?** Scope 3 category model + completeness; factor-year policy; primary-vs-estimated
    labelling; multi-entity reporting; page-level evidence; tenant-isolation regression green.
25. **Production/assurance blockers?** Market-based Scope 2 + instruments; framework requirement content;
    gas/GWP + uncertainty; immutable generated/signed artefacts; anomaly detection; assurance programme.
26. **What should NOT be implemented yet?** A numeric confidence score (state-based review exists); a
    parallel review system (one already exists and is richer); Scope 2/3 auto-matching that guesses;
    corpus/oracle changes; P1 promotion; reporting redesign; supplier-architecture redesign;
    financed-emissions/PCAF; product footprints.

## 33. Summary verdict

* **Unusually strong:** an auditable calculation spine (`calculation_snapshots` with hash, algorithm
  version, factor provenance and source links); a fail-closed ambiguity policy that refuses to guess; a
  versioned clarification record shape; a disclosure/reporting architecture with immutability states and
  frozen artefacts; a governed AI-proposes/human-resolves posture.
* **Not yet proven:** that any of it runs on Scope 2, on Scope 3, through manual review, through supplier
  attribution, or out to a report artefact. The demo database holds **2 Scope 1 results, 23 evidence
  lines, 1 supplier, 0 clarifications, 0 review-audit rows, 0 report artefacts, 0 disclosure values and
  0 customer factors**.
* **The gap is mostly *exercised capability*, not *modelled capability*** — the most useful finding for an
  investor conversation, and the reason this audit does **not** declare CarbonTally investor-ready.
  Scope 1 is demonstrable today; Scope 2 and Scope 3 are not.
* **Factor breadth is better than expected (7049 rows)** but limited to one year (2025) and two countries
  (GB/IE), with no gas/GWP or uncertainty transparency.
* **No framework compliance is claimed** — three framework seeds exist with no regulatory content, exactly
  the distinction this audit was required to preserve.

**STOP — audit complete. No implementation was performed and none is begun.**
