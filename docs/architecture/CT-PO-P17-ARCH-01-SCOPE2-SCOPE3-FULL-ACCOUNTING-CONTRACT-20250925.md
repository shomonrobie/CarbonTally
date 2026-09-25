# CT-PO-P17-ARCH-01 — Full Scope 2 + Full 15-Category Scope 3 Implementation and Architecture Contract

**Task ID:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Baseline commit:** `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be`
**Environment:** local / development only — Demo Lab (`carbontally_demo_local` @ `127.0.0.1:54426`) + read-only static inspection
**Production contacted:** **NO**
**Implementation started:** **NO**

**Companion artifacts**
* `docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json`
* `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json`
* `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json`
* `docs/architecture/artifacts/p17_schema_delta_20250925.md`
* `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md`

---

## 1. Task identity

This task establishes the **architecture and implementation contract** for P17: credible Scope 2 accounting
(location-based and market-based, with contractual instruments) and full 15-category GHG Protocol Scope 3
accounting on the P16-complete CarbonTally baseline.

It is an **architecture task**. It defines the domain contract, the data-model delta, the processing workflows, the
evidence and provenance requirements, factor governance, manual-review requirements, reporting requirements,
security requirements, phase sequencing and acceptance gates. It does **not** implement any of it.

---

## 1.1 Environment reconciliation (mandatory disclosure)

The task header names `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md`, branch `p8-release-reconciled` and
P16 final commit `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be`.

Verified state:

| Item | Task header | Verified actual |
|---|---|---|
| IDE workspace | `/home/shomonrobie/carbon_tally` | `/home/shomonrobie/carbon_tally` exists but is on **`main` @ `20b7a92`**, contains **no** `CT-PO-*` document, and **does not contain** commit `9c96cbf` (`git cat-file -t 9c96cbf` → `fatal: git cat-file: could not get object info`) |
| P16 baseline tree | — | `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled` @ **`9c96cbf`** (`test(p16): complete full regression classification and close P16 acceptance`), containing all 40 `CT-PO-*` documents including `CT-PO-P16-FINAL-VERIFICATION-20250925.md` |
| Ancestry | — | `ct_93d5cdd` is a clone of the same GitHub repository; `93d5cdd` (the published `p8-release-reconciled` tip) is an ancestor of `9c96cbf` (136 local commits ahead) |

**Decision.** All P17 work in this task was performed in `/home/shomonrobie/ct_93d5cdd` (the only tree that contains
the stated P16 baseline). Nothing was written to `/home/shomonrobie/carbon_tally`, whose 227 pre-existing modified
`.agents/skills/**` files were not touched, absorbed or committed.

**Consequence for the reader.** Every path in this contract is relative to `/home/shomonrobie/ct_93d5cdd`.

---

## 2. P16 baseline

Read and relied upon (all in `ct_93d5cdd`):

* `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md` — verdict **P16_PASS**
* `CT-PO-P16-IMPLEMENT-01-CORE-ACCOUNTING-JOURNEYS-20260924.md`
* `CT-PO-P16-REMEDIATION-01 … -07` (including `-05` reportability lifecycle, `-06` RD-4 authorization, `-07` idempotency)
* `CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md` and `CT-PO-P14-AUDIT-01-…`
* `CT-PO-P12-DECISION-01-…`, `CT-PO-P12-IMPL-01/02-…` (PDF extraction, waste semantics, supplier resolution, auditable review)

**P16 final verdict facts (inherited, not re-derived):** full backend unit suite completed — 3,342 tests, 3,322 passed,
9 failed (all Class B/E, none Class-A), 11 skipped, 0 errors; R1–R14 all PASS; calculation idempotency RESOLVED with
`request_id_dupes=0`; six-PDF corpus / ground truth / oracle byte-identical; no production contact.

**P16 contracts this task treats as frozen inputs:**

| Contract | Source | Content |
|---|---|---|
| Reportability lifecycle | `20261008000000_p16r5_result_reportability_lifecycle.sql` | `reportable \| not_for_reporting \| superseded` on `calculation_snapshots` and `emissions_logs`, with the invalidation-described CHECK |
| Calculation idempotency | `20261009000000_p16r7_calculation_request_idempotency.sql` | `uq_calc_snapshots_request_id`; the request id is the idempotency key |
| Deterministic request id | `api/v3_operations.py::_run_line_calculation`; `services/automatic_processing.py` | `uuid5(NAMESPACE_DNS, f"{item.id}::calc::{idx}::c1::{digest}")` over the STABLE inputs |
| Item state machine | `domain/partners.py::ITEM_STATUS_FLOW` (P16-R4) | `mapped → validated → calculated`; `mapped → calculated` prohibited |
| Manual review | `activity_clarifications` + `activity_clarifications` adjudication lifecycle (F-039-1) | versioned, superseding, evidence-signature-aware operator decisions |
| Supplier resolution | `engines/supplier_resolution.py` (P12-IMPL-02) | org-scoped, fail-closed: exact / unresolved / confirm_creation / ambiguous |
| Waste semantics | P12-IMPL-02 §9 | material + treatment route required; ambiguity → clarification, never a guess (observed 4.647× spread between plausible routes) |

---

## 3. P17 authorization boundary

**Authorised by this task:** documentation-only changes defining the P17 contract.

**Not authorised:** implementation of any P17 phase; production migrations; production deployment; new factors;
fabricated instruments, categories, methods, suppliers or estimates; Step 3; any claim of framework compliance,
assurance readiness or regulatory compliance.

**Rule.** Implementation of the P17 feature set must not begin until this contract is complete **and** a subsequent
task explicitly authorises exactly one phase.

---

## 4. Current accounting capabilities

Evidence classes (P14 reconciliation rule, reused verbatim): **DOCUMENTED** | **CODE EXISTS** | **ROUTE WIRED** |
**FACTOR AVAILABLE** | **PERSISTED** | **END-TO-END VERIFIED**. Only END-TO-END VERIFIED counts as acceptance.

| Capability | Class achieved today | Evidence |
|---|---|---|
| Scope 1 stationary combustion (natural gas) | END-TO-END VERIFIED | 6 reportable snapshots/logs, 12,527.711 kg CO2e reportable |
| Calculation snapshot provenance | END-TO-END VERIFIED | `calculation_snapshots` (factor id/source/set/year, quantity, unit, methodology, algorithm version, `content_hash`), 34 rows |
| Calculation reproducibility check | ROUTE WIRED | `POST /api/v3/emissions/calculations/{id}/verify` |
| Result reportability lifecycle | END-TO-END VERIFIED | 34 rows classified: 6 S1 reportable, 2 S1 superseded, 25 S3 reportable, 1 S3 not_for_reporting |
| Calculation idempotency | END-TO-END VERIFIED | deterministic request id + unique index; repeat calculation reproduced 4,175.90378 without doubling |
| PDF extraction → item → mapping → calculation → evidence | END-TO-END VERIFIED for the waste slice | 23 `manual_extraction_items`, 67 `evidence_line_items`, 34 snapshots |
| Manual review / clarification | END-TO-END VERIFIED on the waste path | 9 `activity_clarifications` rows, all `semantic_activity` / `selected` |
| Supplier resolution + propagation | END-TO-END VERIFIED | 1 supplier; 25 emissions rows with `supplier_id` |
| Waste (Scope 3, no category) | PERSISTED, NOT CATEGORISED | 25 reportable rows, 1,582.460460 kg CO2e, factor `Waste disposal > Construction > Metals - Landfill` |
| Scope 2 location-based | NOT PRESENT | 0 Scope 2 snapshots, 0 Scope 2 logs |
| Scope 2 market-based | NOT PRESENT | 0 rows; no instrument entity exists |
| Contractual instruments | NOT PRESENT | no table, no column, no code |
| Scope 3 category dimension | NOT PRESENT | no `scope3_category` / `category_number` column or code anywhere (`grep` across `*.py`, `*.sql`, `*.ts`, `*.tsx`) |
| Scope 3 category-per-category reporting | NOT PRESENT | reporting aggregates by scope only |
| Disclosure values / report artefact | ARCHITECTURE ONLY | `disclosure_values` = 0; `report_version_artifacts` = 0; `report_versions` = 4 |
| CarbonTally Insight (read side) | CODE EXISTS + route | insight repositories read `emissions_logs.supplier_id` as a dimension |

**Reading rule.** The 25 reportable Scope 3 rows are the platform's only persisted Scope 3 result. They carry **no
category**, which is precisely the gap P17-D closes for new writes — and precisely why no historical row may be
retro-attributed by inference (§6 of the schema delta).

---

## 5. Current factor inventory

Read-only inventory of `carbontally_demo_local` (7,049 rows). **All rows are `reporting_year = 2025`.**

| scope | factor_source | year | country | rows |
|---|---|---|---|---|
| Scope 1 | DEFRA-DESNZ | 2025 | GB | 2,531 |
| Scope 1 | SEAI | 2025 | IE | 18 |
| Scope 2 | DEFRA-DESNZ | 2025 | GB | 352 |
| Scope 2 | SEAI | 2025 | IE | 2 |
| Scope 3 | DEFRA-DESNZ | 2025 | GB | 4,090 |
| Outside of Scopes | DEFRA-DESNZ | 2025 | GB | 56 |

**Scope 2 families (354 rows):**

| family | rows | units |
|---|---|---|
| UK electricity for EVs | 272 | km, miles, tonne.km |
| SECR kWh UK electricity for EVs | 68 | km, miles, tonne.km |
| Heat and steam | 8 | kWh |
| UK electricity | 4 | kWh |
| Fuels | 2 | kWh |

**Consequence for Scope 2:** only **4 + 2** rows are actually grid-consumption electricity factors in kWh; the
EV/T&D rows are distance/passenger-mile factors that belong to Scope 2 *vehicle charging* or Scope 3 T&D, and
`cooling` has **zero** coverage. A "354 Scope 2 factors" statement without this breakdown is misleading, and the P14
audit's warning ("do not present Scope 2 as complete merely because electricity factors exist") is confirmed.

**Scope 3 families (4,090 rows, 22 families):** Freighting goods 1156, Managed assets- vehicles 948,
Business travel- land 672, WTT- delivery vehs & freight 289, UK electricity T&D for EVs 272,
WTT- pass vehs & travel- land 168, Waste disposal 134, WTT- fuels 114, Business travel- air 112, Material use 70,
WTT- bioenergy 49, Hotel stay 39, WTT- business travel- air 28, Business travel- sea 12,
Transmission and distribution 8, Managed assets- electricity 4, WTT- business travel- sea 3, Homeworking 3,
WTT- heat and steam 3, WTT- UK electricity 2, Water supply 2, Water treatment 2.

**Structural finding.** No family is bound to a downstream boundary and several families are shared across
categories (categories 4/9, 5/12, 8/13). **Factor count is therefore not category coverage** — the same conclusion
P14 reached, now demonstrated at family level. This is the evidence basis for AD-P17-02.

**Absent reference data (must not be fabricated):** residual-mix factors; any 2026 factor year; any capital-goods,
downstream-processing, use-phase, franchise or sector/investment factor set; any grid-region-level factor
differentiation beyond country (`GB`/`IE`).

---

## 6. Current Scope 1 baseline

* Activities E2E proven: **stationary combustion of natural gas** (fuel card / utility bill CSV and PDF paths).
* Persisted: 6 reportable + 2 superseded Scope 1 snapshots; reportable total **12,527.711340** kg CO2e; superseded
  history retained and inspectable.
* Provenance: `emissions_logs.snapshot_id` → `calculation_snapshots` (factor id/source/set/year, quantity, unit,
  `content_hash`, `algorithm_version`) → `source_item_id` / `source_line_item_id` → `evidence_line_items`.
* **Not E2E verified** (P14 §4): mobile combustion, fugitive emissions, process emissions. Process emissions are
  **not implemented**.
* Factor-year governance: exact-year behaviour proven on the natural-key/pipeline path (P16-R1/R7/R8).
  **Latent gap found by this task:** four production call sites present cross-year candidate sets to an operator
  (see §7.4 and §29).

---

## 7. Scope 2 gap analysis

### 7.1 What exists

* A `scope` column (`text`) on `emission_factors`, `calculation_snapshots` and `emissions_logs`, holding `'Scope 2'`
  for Scope 2 candidates. It is not a CHECK-constrained vocabulary.
* A canonical scope vocabulary in code: `core/types.py::Scope` (`Scope 1 | Scope 2 | Scope 3 | Outside of Scopes`)
  and the alias normaliser `api/v3_emissions.py::normalize_scope`.
* A dual-method **disclosure** vocabulary: `domain/disclosure.py::SCOPE2_METHODS = ("LOCATION_BASED", "MARKET_BASED")`
  plus the `scope2_method_hint` CHECK on the B1 disclosure tables. It governs disclosure requirements only.
* Electricity/heat/steam factors: 4 + 2 grid kWh rows, 8 heat/steam kWh rows, plus 340 EV/transport rows.
* Supplier attribution plumbing (`emissions_logs.supplier_id`, resolver, 25 populated rows).
* The full provenance / evidence / reportability / idempotency machinery (§2).

### 7.2 What is missing (P14-confirmed, still true at this baseline)

1. No location-based calculation path.
2. No market-based calculation path.
3. No method dimension on any accounting result.
4. No contractual-instrument entity, allocation, claim or validation.
5. No residual-mix data or handling.
6. No grid-region resolution (country only).
7. No real Scope 2 fixture, result or report line.
8. No reporting distinction between the two methods at the accounting layer.

### 7.3 Additional gaps found by this task (new)

9. **Energy type is not modelled.** `electricity | heat | steam | cooling | fuel` is only inferable from factor
   family text. `cooling` has **zero** factors, so a cooling activity must route to controlled review.
10. **Facility/site is not a real dimension.** `emissions_logs.metadata->>'facility_id'` only; no column, no FK, no
    index, and `calculation_snapshots` has no facility dimension at all — even though `facilities` carries exactly
    the fields Scope 2 needs (`country`, `region`, `postcode`, `latitude`, `longitude`, `meter_mpan_mprn`).
11. **Cross-year factor candidates are unlabelled at four production call sites** (§7.4).
12. **The method identity cannot be recorded today.** Because any factor can be used as either a location-based or a
    market-based factor, an operator cannot record *which* accounting method a Scope 2 result represents. This is the
    single largest correctness risk in Scope 2.

### 7.4 The factor-year gap (verified, concrete)

| Call site | Call | Effect |
|---|---|---|
| `backend/api/v3_operations.py:1039` | `repos.factors.find_by_activity(activity, unit=..., limit=20, unit_substring=True)` | no `year=` → all years |
| `backend/api/v3_operations.py:1650` | same | no `year=` → all years |
| `backend/api/v3_processing_workflow.py:1156` | `find_by_activity(activity, unit=unit, limit=20, unit_qualifier_tolerant=True)` | no `year=` → all years |
| `backend/services/automatic_processing.py:1615` | same | no `year=` → all years |

`data/emission_factors.py::find_by_activity` then orders candidates `..., ef.reporting_year DESC, ef.activity_type`
(line 173) — newest year first, silently. Today the gap is latency-only because all 7,049 factors are 2025. It
becomes an accounting defect the moment a second factor year is imported — which P17 factor-year governance requires.

**P17-A obligation:** either pass the year (preferred), or present cross-year candidates only with an explicit,
labelled year plus an explicit operator decision. "No silent factor-year fallback" (P16-R8) must hold on *every*
candidate path, not only the natural-key path.

---

## 8. Scope 2 canonical domain

The full field-by-field decision matrix is `artifacts/p17_scope2_domain_matrix_20250925.json` (33 fields, each marked
REQUIRED / CONDITIONALLY_REQUIRED / OPTIONAL / DERIVED, with current status and target).

### 8.1 Architectural decisions

| ID | Decision |
|---|---|
| **AD-P17-01** | Scope 2 and Scope 3 are **accounting dimensions over the existing pipeline**, not parallel accounting systems. Reuse `emission_factors` → matching/selection → `calculation_snapshots` → `emissions_logs` → evidence → reportability → reporting/disclosure. No new accounting engine, no new snapshot table, no new reportability model. |
| **AD-P17-02** | **Scope 3 category is a property of the activity/result, never of the factor.** A factor may carry a `scope3_category_hint`, but the persisted result's category is resolved explicitly (deterministic rule with a recorded basis, or an operator decision). No category is inferred from free text. |
| **AD-P17-03** | **Scope 2 method is a required dimension of every Scope 2 result.** Vocabulary reused verbatim from the frozen disclosure contract: `LOCATION_BASED` / `MARKET_BASED`. |
| **AD-P17-04** | **Dual-method coexistence, never replacement.** A method change produces a new result with a different idempotency key; the previous result is superseded through the existing P16 lifecycle, never overwritten. |
| **AD-P17-05** | **Contractual instruments are a first-class org-scoped entity** with an allocation/claim ledger; an instrument is claimable by exactly one organisation and cannot be over-allocated. |
| **AD-P17-06** | **No silent factor-year fallback on any path**, including candidate presentation. |
| **AD-P17-07** | **Boundary and origin are explicit properties** where a factor family is shared across categories (4/9 inbound-outbound, 5/12 operational-EoL waste, 8/13 lessee-lessor). |
| **AD-P17-08** | **Energy type is an explicit controlled value** on a Scope 2 activity, never inferred from factor text at calculation time. |
| **AD-P17-09** | **Facility becomes a real dimension** (FK `facilities`) for new writes while history is left untouched. |
| **AD-P17-10** | **Data quality is an explicit dimension** with a controlled vocabulary; numeric uncertainty is **deferred** and recorded as deferred. |
| **AD-P17-11** | **Estimated values require a persisted estimation record** (method, inputs, assumptions, factor, source, actor, timestamp). |
| **AD-P17-12** | **Framework disclosure stays separate** from accounting data; P17 supplies accounting primitives, not a framework schema. |
| **AD-P17-13** | **One Unified Carbon Accounting Management System.** Staff/Admin, direct customer, consultant and consultant-client actors are distinguished by *identity, organization context, role, capability and delegated relationship* — never by separate accounting engines, schemas, tables or result pipelines (post-contract PO decisions D1 §2/§21, D2 §2/§37). No P17 phase may fork the accounting core. |

### 8.2 Canonical Scope 2 activity

```
Scope 2 activity
  organization (REQUIRED, tenant key)
  reporting_period (REQUIRED)
  facility_id (CONDITIONALLY REQUIRED: multi-site orgs, site-specific supply/meter)
  energy_type (REQUIRED: electricity | heat | steam | cooling | fuel)
  quantity + unit (REQUIRED; unit must match the factor unit)
  country / grid_location (REQUIRED / CONDITIONALLY REQUIRED for LOCATION_BASED)
  supplier_id (CONDITIONALLY REQUIRED)
       |
       +---> [ LOCATION_BASED result ]  activity x location factor  (factor year governed)
       +---> [ MARKET_BASED result   ]  activity x market factor    (instrument or supplier evidence)
```

Both branches persist as separate `calculation_snapshots` + `emissions_logs` rows carrying their own
`scope2_method`, their own deterministic request id, their own evidence links and their own reportability state.

**Rejected designs (see the matrix for the full list):** a single overwritable Scope 2 value; a parallel Scope 2
accounting table; encoding the method inside the methodology string; inferring the method from factor metadata.

---

## 9. Scope 2 location-based contract

**Definition.** `emissions = activity_quantity (in the factor's unit) × location_factor`, where the location factor
is a grid/geography emission factor of the **exact** reporting year and the matching country/geography.

**Inputs.** Scope 2 activity (§8.2) + resolved grid location (facility → region/country, or an explicit recorded
national-resolution decision) + reporting year + energy type.

**Factor selection.** Deterministic, auditable, persisted:
1. activity/energy type must be eligible (electricity/heat/steam; `cooling` currently has no factors → review);
2. unit compatibility per the central `core/units.py` normalisation (qualified variants such as `kWh (Net Gross CV)`
   handled by the existing EF-E rule — no new alias logic);
3. **exact** reporting year, or a controlled review state — never a silent nearest-year substitution;
4. geography = the resolved location's country (GB/IE today) with the resolution basis recorded;
5. the selected factor is persisted on the snapshot (`factor_id`, `factor_source`, `factor_set`, `reporting_year`).

**Outputs.** `calculation_snapshots` + `emissions_logs` rows with
`scope = 'Scope 2'`, `scope2_method = 'LOCATION_BASED'`, `energy_type`, `facility_id`, `reportability_status =
'reportable'`, and a deterministic request id namespaced by the method.

**Review triggers.** No eligible factor for energy type/unit; no location factor for the resolved grid location;
factor-year mismatch; ambiguous facility/grid resolution; `cooling` requested.

**Prohibitions.** No use of a market/contractual factor; no substitute of a national factor for a required regional
one without an explicit recorded decision; no cross-methodology reuse of a prior snapshot.

**Idempotency.** `request_id = uuid5(NS_DNS, "<item|activity>::calc::<ordinal>::c1::<digest>")` where `<digest>`
covers the stable inputs **including `scope2_method` and `energy_type`**. A repeat run reuses the existing snapshot;
changing the method yields a different key and therefore a new, coexisting result.

---

## 10. Scope 2 market-based contract

**Definition.** `emissions = activity_quantity × market_factor`, where the market factor derives from a contractual
instrument, a supplier-specific factor, or a supplier/residual-mix disclosure — **each with its own evidence**.

**Factor/instrument selection (deterministic order, all steps recorded):**
1. a valid allocated contractual instrument covering the period/geography → instrument-derived market factor;
2. else a supplier-specific market factor with a supplier evidence document;
3. else a residual-mix/grid-supplier factor **if such data exists** — it does not today, so this step fails closed;
4. else → **controlled review** (never a location factor silently used as the market factor).

**Validity gates (see §11).** Instrument exists is **not** the same as instrument valid for the claimed activity.
A market-based result requires: a valid instrument (or an evidenced supplier factor), an allocation whose quantity
does not exceed the eligible consumption, geography and period coverage, and a retirement/claim status that permits
the claim.

**Outputs.** Rows with `scope = 'Scope 2'`, `scope2_method = 'MARKET_BASED'`, the same activity/period/facility
dimensions as the location-based result, plus the instrument/allocation link and the market factor provenance.

**Dual-method guarantees.**
* A change of method **never** overwrites or invalidates the other method's result; both are readable side by side.
* A repeat of the same method with identical inputs is a no-op (idempotency).
* Changing the method on existing inputs produces a **new** result; if an operator intends to correct rather than
  add, the previous result is superseded through the existing lifecycle with a reason, actor and timestamp.
* It must be **impossible to mistake a market-based result for a location-based one**: the method is a persisted
  column, a CHECK-constrained value, a report dimension, and part of the idempotency key.

**Reporting treatment.** Both methods are reportable simultaneously; a report presents both and never presents a
market-based figure under a location-based label (or vice versa).

**Explicit non-goals.** No residual-mix dataset; no framework-specific certificate rule engine (REGO/REC/PCAF-style
scoring) without separate ratification.

---

## 11. Contractual-instrument contract

**Entities.** `contractual_instruments` (the claimable instrument) and `instrument_allocations` (the claim), per the
schema delta §3.1–§3.2.

**Instrument types (generic controlled vocabulary).** `energy_attribute_certificate`, `guarantee_of_origin`,
`supplier_specific_contract`, `ppa`, `rec`, `green_tariff`, `other`. Jurisdiction-specific classes map onto these;
their rule sets are **FRAMEWORK_SPECIFIC** and deferred.

**Required properties.** identifier, issuer, source facility (where available), geography, generation period,
vintage, quantity + unit, validity window, retirement status + reference, own evidence item, claimant organisation.

**Validation rules (each must be a real check, not a convention):**

| ID | Rule | Failure behaviour |
|---|---|---|
| I-1 | Instrument exists and belongs to the claiming organisation | deny (RLS) / controlled review |
| I-2 | Not already claimed by a different organisation | **deny** — cross-tenant claim impossible |
| I-3 | `sum(allocations) ≤ instrument.quantity` in a common unit | deny the over-allocation |
| I-4 | Allocation period falls within the instrument's validity/generation coverage where the market requires it | controlled review |
| I-5 | Allocation geography matches the instrument's valid geography | controlled review |
| I-6 | Vintage is acceptable for the applicable consumption period under the governing framework | controlled review, with the governing source named |
| I-7 | Instrument evidence document is present and not expired/invalid | controlled review — **never** silent acceptance |
| I-8 | Instrument not retired/cancelled in a way that forbids the claim | deny / controlled review |
| I-9 | Allocation is bound to a specific activity/snapshot and one reporting period | deny |
| I-10 | The allocated quantity does not exceed the eligible consumption of that activity/period | deny |

**Framework dependence.** Rules I-4, I-6, I-8 and I-9's specifics depend on the governing market/framework. Where the
requirement is framework-dependent it is marked **FRAMEWORK-SPECIFIC** and the governing source must be named in the
implementation (e.g. the market operator's issuance/retirement rules). **This contract does not invent regulatory
requirements.**

**Distinction preserved.** `instrument exists` ≠ `instrument is valid for the claimed reporting activity`. The
platform must be able to record the first without implying the second, and must never produce a market-based result
from an instrument that failed a validity gate.

---

## 12. Scope 2 reporting contract

**Report dimensions.** scope (`Scope 2`), **method** (`LOCATION_BASED` | `MARKET_BASED`), energy type, facility,
supplier/provider, factor source/set/year, geography, data quality, reportability status.

**Rules.**
1. Location-based and market-based results are **separate report lines**; neither may be substituted for the other.
2. A report may present either method alone only when the other is explicitly reported as not present/not applicable
   for that period — never silently omitted so that a single figure looks like "Scope 2".
3. Only `reportability_status = 'reportable'` rows enter aggregates (reusing the existing disclosure projection
   filter); superseded/not-for-reporting rows stay inspectable but excluded.
4. The instrument/allocation that backed a market-based figure must be resolvable from the report.
5. A Scope 2 total must always be accompanied by its method label **and** its factor year(s).

---

## 13. Scope 3 canonical domain

Full per-category contract: `artifacts/p17_scope3_category_matrix_20250925.json`.

**Every Scope 3 result MUST carry:** `scope = 'Scope 3'`, `scope3_category` (1–15), the canonical category name,
methodology, activity type, quantity, unit, factor (or an evidenced non-factor input), factor source, factor year,
geography, data quality/provenance, evidence, calculation snapshot and the emissions result — plus, where the
category requires it, the boundary/origin property.

**Rules.**
1. **No Scope 3 result without a category.** Enforced by a `NOT VALID` CHECK for new writes; a missing category is a
   controlled review state.
2. **No category inferred from activity text alone.** Category resolution is either a deterministic rule with a
   recorded basis or an explicit operator decision; a factor-level hint is a proposal only.
3. **No category changed in place.** A reclassification produces a new result and a supersession link.
4. **The 15 categories are never collapsed into a generic "Scope 3" activity type.** Each remains identifiable
   through source → extraction → mapping → methodology → factor → calculation → snapshot → emissions log → evidence
   → reporting → disclosure.
5. **Shared factor families do not imply shared categories** (§5, §33).

---

## 14. Category 1 — Purchased Goods and Services

* **Meaning.** Upstream (cradle-to-gate) emissions of purchased goods and services, excluding capital goods (2),
  fuel/energy (3), upstream transport (4) and waste (5).
* **Minimum input.** Reporting period; product/service description; supplier or supplier class; quantity **or** spend
  value (methodology-dependent); unit.
* **Accepted activity types.** Physical mass/volume/energy of a purchased commodity; spend on goods/services;
  a supplier-specific product factor activity.
* **Methodologies.** `supplier_specific` | `average_data` | `hybrid` | `spend_based` (**only** when no physical data
  exists **and** explicitly authorised and labelled as spend-based on the result).
* **Factor requirements.** Supplier-specific or secondary/industry-average factor with a published material or
  activity basis. Live coverage is thin: only `Material use` (70 rows) has a plausible category-1 basis.
* **Factor year.** Exact reporting year, or an explicitly recorded nearest-available-year decision via review.
* **Geography.** Factor country must match the purchase/consumption geography or the mismatch is an explicit decision.
* **Evidence.** Purchase invoice/line evidence (already modelled by `evidence_line_items`) + supplier identity
  evidence for supplier-specific factors.
* **Supplier.** Must resolve through the existing org-scoped resolver; ambiguity is a review state.
* **Review triggers.** No eligible factor; spend-based would be required but not authorised; ambiguous supplier;
  supplier-specific factor without supplier evidence; incompatible unit.
* **Output.** kg CO2e per line, `scope3_category = 1`, methodology (including `spend_based` where used) persisted.
* **Reporting dimensions.** category, methodology, supplier, facility, year, data quality.
* **Security.** Supplier and factor selection are org-scoped; supplier-specific factors are tenant assets.
* **E2E scenario.** `IA-S3-01` — one purchased-goods line from a canonical document → factor with explicit
  methodology → calculation → persisted with category 1 → evidence-linked → reportable.
* **Status: PARTIAL.** Prerequisites: category dimension (P17-D); a PO decision authorising (or refusing)
  spend-based estimation; explicit methodology recording.

---

## 15. Category 2 — Capital Goods

* **Meaning.** Upstream (cradle-to-gate) emissions of capital goods acquired in the period — a subset of purchased
  goods that is separately reported.
* **Minimum input.** Period; capital-good identification; supplier; quantity or value; the asset/facility it is
  attributed to.
* **Accepted activity types.** Capital asset acquisition; supplier embodied-emissions disclosure; asset-level spend.
* **Methodologies.** `supplier_specific` | `average_data` | `spend_based` (explicit only) | `asset_embodied`
  (requires an embodied dataset that does not exist).
* **Factor requirements.** No live capital-goods family exists. Delivery needs either a supplier-provided embodied
  figure (recorded as an explicit supplier figure **with evidence**, not as a factor) or a governed factor set.
* **Factor year.** Same strict rule; unavailability must fail closed rather than fall back to a general goods factor.
* **Geography.** Supplier/manufacturing geography.
* **Evidence.** Invoice/asset acquisition evidence; plus the supplier's embodied-emissions disclosure where used.
* **Supplier.** Same resolver; the capital-goods supplier is a first-class supplier record.
* **Review triggers.** No factor/supplier figure; capital-vs-expensed classification ambiguous; acquisition-vs-
  commissioning year treatment unclear; supplier figure without evidence.
* **Output.** kg CO2e per capital good, category 2, with the attribution method recorded.
* **Reporting dimensions.** category, supplier, asset, facility, year, data quality.
* **Security.** Asset records are org-scoped.
* **E2E scenario.** `IA-S3-02` — one capital good with a supplier embodied figure (with evidence) or an authorised
  spend-based calculation, persisted as category 2, with no double count against category 1.
* **Status: NOT_IMPLEMENTED.** Prerequisites: capital-goods methodology PO decision; DC-03 control; asset-level
  attribution dimension.

---

## 16. Category 3 — Fuel- and Energy-Related Activities (not in Scope 1 or 2)

* **Meaning.** Upstream (well-to-tank) emissions of purchased fuels/energy, transmission and distribution losses,
  and upstream electricity emissions not already counted in Scope 1 or Scope 2.
* **Minimum input.** A reference to the existing Scope 1/2 activity or snapshot; energy/fuel quantity; unit;
  fuel/energy type; period.
* **Accepted activity types.** Upstream fuel (WTT) for a Scope 1 fuel activity; T&D losses for a Scope 2 electricity
  activity; upstream electricity (WTT).
* **Methodologies.** `direct_multiply` against a WTT/T&D factor; `derive_from_source_activity` (quantity inherited).
* **Factor requirements.** Live families suffice: `WTT- fuels` (114), `WTT- UK electricity` (2),
  `WTT- heat and steam` (3), `WTT- bioenergy` (49), `Transmission and distribution` (8),
  `UK electricity T&D for EVs` (272). Selection must exclude WTT factors from Scope 1 arithmetic and non-WTT
  factors from category 3.
* **Factor year.** Must equal the source activity's reporting year, or the mismatch is a review state.
* **Geography.** Must match the source activity's country.
* **Evidence.** Normally derives from an already-evidenced Scope 1/2 activity; the derivation link is the additional
  evidence requirement and must be persisted.
* **Supplier.** Inherited from the source activity where known; never invented.
* **Review triggers.** Source activity unidentifiable; no WTT/T&D factor for the fuel/energy type; the upstream factor
  would double count an amount already inside Scope 1/2; T&D not applicable to a directly connected supply.
* **Output.** kg CO2e per derived line, category 3, with a persisted source link.
* **Reporting dimensions.** category, sub-type (upstream fuel | upstream electricity | T&D), source scope, facility, year.
* **Security.** The derivation link may only reference a source activity in the same organisation.
* **E2E scenario.** `IA-S3-03` — a WTT/T&D result derived from an existing Scope 1 or Scope 2 snapshot, persisted
  with category 3 and a persisted source link, provably not re-adding the Scope 1/2 quantity.
* **Status: SUPPORTED.** Prerequisite: the derivation link plus uniqueness constraint (DC-02).

---

## 17. Category 4 — Upstream Transportation and Distribution

* **Meaning.** Transportation and distribution of purchased products plus third-party inbound logistics the
  organisation pays for, including warehousing.
* **Minimum input.** Carrier/supplier; mode; distance **or** fuel/activity data; mass or volume; shipment period;
  origin; destination.
* **Accepted activity types.** Freighting goods by tonne.km/km/miles; carrier-supplied fuel or activity data;
  warehousing energy.
* **Methodologies.** `distance_based` | `fuel_based` | `supplier_specific`.
* **Factor requirements.** `Freighting goods` (1156) and `WTT- delivery vehs & freight` (289); units km, miles,
  tonne.km. The same families serve category 9, so the boundary must be an explicit recorded property.
* **Factor year.** Exact reporting year.
* **Geography.** Consistent with the shipment geography.
* **Evidence.** Carrier invoice/consignment evidence: mode, mass, distance/fuel, period.
* **Supplier.** Carrier/3PL resolves org-scoped.
* **Review triggers.** Ambiguous mode; incompatible unit (km vs tonne.km vs litres); ambiguous inbound/outbound
  boundary (DC-04); missing mass/distance; unresolved carrier.
* **Output.** kg CO2e per shipment, category 4, with mode, distance basis and boundary recorded.
* **Reporting dimensions.** category, carrier, mode, boundary (upstream), facility, year.
* **Security.** Carrier supplier records are org-scoped.
* **E2E scenario.** `IA-S3-04` — one inbound shipment with mode and tonne.km, persisted as category 4 with an
  explicit upstream boundary flag.
* **Status: SUPPORTED.** Prerequisites: boundary property + DC-04; a mode controlled vocabulary.

---

## 18. Category 5 — Waste Generated in Operations

* **Meaning.** Emissions from third-party disposal/treatment of waste generated by the organisation's owned or
  controlled operations.
* **Minimum input.** Waste material; quantity; unit; treatment route; period; waste service provider.
* **Accepted activity types.** Waste disposal by material and treatment route (landfill, open-loop, closed-loop,
  incineration with energy recovery, composting, anaerobic digestion).
* **Methodologies.** `direct_multiply` (material + treatment-route factor).
* **Factor requirements.** `Waste disposal` (134 rows, unit `tonnes`) is the correct base. The taxonomy is
  family > material > treatment route; a bare "Waste" activity has no unique factor and must not be auto-matched.
* **Factor year.** Exact reporting year.
* **Geography.** Factor country must match the disposal jurisdiction.
* **Evidence.** The waste transfer/service document; the clarification record is the evidence of the operator's
  treatment-route decision.
* **Supplier.** The waste service provider (live: `Robinsons Recycling Services Ltd`; `mapped_supplier_id`
  propagated to 25 emissions rows).
* **Review triggers.** Treatment route not printed; ambiguous material; multiple plausible routes with materially
  different factors (observed spread 4.647×); no eligible factor; unresolved provider.
* **Output.** kg CO2e per waste line, category 5, with the operator's selected factor/treatment route persisted as an
  adjudication.
* **Reporting dimensions.** category, waste material, treatment route, supplier, facility, operator decision, year.
* **Security.** Clarification/adjudication rows are org-scoped; effective-context reuse must never cross tenants.
* **E2E scenario.** `IA-S3-05` — **already partially proven**: ambiguous Waste → clarification → operator factor
  selection → calculation → 25 reportable rows / 1,582.460460 kg CO2e with 9 persisted `activity_clarifications`.
  P17 adds `category = 5` to this path and re-verifies it through reporting.
* **Status: SUPPORTED.** Prerequisites: category dimension on the waste path (P17-D); reporting/disclosure E2E.

---

## 19. Category 6 — Business Travel

* **Meaning.** Emissions from transportation of employees for business activities in vehicles not owned/operated by
  the organisation (air, rail, land, sea), plus accommodation.
* **Minimum input.** Travel mode; distance **or** spend/fuel data; passenger count; travel period; geography.
* **Accepted activity types.** passenger.km by mode; km by vehicle class; hotel room-nights.
* **Methodologies.** `distance_based` | `passenger_km_based` | `spend_based` (explicit only).
* **Factor requirements.** `Business travel- land` (672), `Business travel- air` (112), `Business travel- sea` (12),
  `Hotel stay` (39), plus WTT variants (which must route to category 3, not category 6).
* **Factor year.** Exact reporting year.
* **Geography.** Air/sea factors are geography-sensitive; a mismatch is a review state.
* **Evidence.** Booking/expense evidence with mode, distance/class and dates.
* **Supplier.** Travel provider/agency where available; not mandatory unless a supplier-specific factor is used.
* **Review triggers.** Ambiguous travel class (materially changes the factor); distance not stated; multiple legs on
  one line; ambiguous mode; a WTT variant selected for a category-6 line.
* **Output.** kg CO2e per trip/hotel line, category 6, with mode, class and distance basis recorded.
* **Reporting dimensions.** category, mode, class, geography, year, data quality.
* **Security.** Employee-level attribution is personal data; the default reporting dimension is aggregate.
* **E2E scenario.** `IA-S3-06` — one air trip and one hotel line from a canonical travel source, persisted as
  category 6.
* **Status: SUPPORTED.** Prerequisite: the WTT-vs-direct routing rule (DC-02).

---

## 20. Category 7 — Employee Commuting

* **Meaning.** Emissions from transportation of employees between home and worksite, including homeworking energy.
* **Minimum input.** Commuting mode; distance; frequency; employee count; period; occupancy where applicable.
* **Accepted activity types.** Average-data commuting by mode; survey-based distance/frequency; homeworking days.
* **Methodologies.** `average_data` | `survey_based_estimate` (explicit only) | `distance_based`.
* **Factor requirements.** `Homeworking` (3 rows) is directly usable. Private-car/rail commuting can draw on
  `Business travel- land` vehicle factors **only** as an explicitly recorded estimated methodology, because those
  factors are built for business travel. A commuting-specific factor set would be preferable and is not present.
* **Factor year.** Exact reporting year.
* **Geography.** National average factors assumed; a mismatch must be explicit.
* **Evidence.** Because commuting is normally estimated, **the estimation record is the mandatory evidence**: method,
  inputs, assumptions, factor, source, actor, timestamp.
* **Supplier.** None.
* **Review triggers.** No commute data (estimate required); estimated methodology not authorised; employee count or
  frequency missing; ambiguous mode mix; a business-travel factor reused without an explicit estimate record.
* **Output.** kg CO2e per mode/period, category 7, flagged estimated with its estimation record persisted.
* **Reporting dimensions.** category, mode, facility/site, year, data quality (secondary/estimated).
* **Security.** Home/work addresses are personal data and are never a reporting dimension; only aggregates leave the
  workflow.
* **E2E scenario.** `IA-S3-07` — an explicit average-data commuting estimate (with its persisted estimation record),
  stored as category 7 and marked secondary/estimated.
* **Status: PARTIAL.** Prerequisites: the estimation-record contract (P17-H); a PO decision on whether average-data
  commuting estimates are authorised at all.

---

## 21. Category 8 — Upstream Leased Assets

* **Meaning.** Emissions from operating assets the organisation leases (lessee position) that are **not** already in
  Scope 1 or Scope 2 under the chosen consolidation approach.
* **Minimum input.** Leased asset; asset type; lease relationship; activity/energy/fuel data; period; consolidation
  boundary treatment.
* **Accepted activity types.** Leased vehicle fuel/energy; leased building electricity; leased equipment energy.
* **Methodologies.** `direct_multiply` on asset activity data; `asset_energy_based`.
* **Factor requirements.** `Managed assets- vehicles` (948), `Managed assets- electricity` (4) and the `Fuels`
  family provide the basis. The governing issue is the **boundary**, not the factor.
* **Factor year.** Exact reporting year.
* **Geography.** Asset location.
* **Evidence.** Lease agreement (to establish the lessee relationship and consolidation treatment) + the asset's
  activity evidence.
* **Supplier.** Lessor where relevant.
* **Review triggers.** Consolidation approach not set; the asset already carries Scope 1/2 activity for the same
  period (DC-07); ambiguous lease-vs-owned classification; missing lease agreement.
* **Output.** kg CO2e per leased asset per period, category 8, with the consolidation approach recorded.
* **Reporting dimensions.** category, asset, asset type, consolidation approach, facility, year.
* **Security.** Lease and asset records are org-scoped; lessor and lessee data must not leak across tenants.
* **E2E scenario.** `IA-S3-08` — one leased asset recorded as category 8 with an explicit consolidation approach,
  plus a negative check proving the same activity period is not also in Scope 1/2.
* **Status: PARTIAL.** Prerequisites: the organisation consolidation-approach dimension (P17-H); DC-07 detector.

---

## 22. Category 9 — Downstream Transportation and Distribution

* **Meaning.** Transportation and distribution of sold products paid for by the organisation (outbound logistics),
  plus transport of sold products in vehicles not owned/controlled by the organisation.
* **Minimum input.** Sold product/shipment; carrier; mode; mass/volume; distance; origin; destination; period.
* **Accepted activity types.** Outbound freighting by tonne.km/km/miles; carrier-provided outbound activity data.
* **Methodologies.** `distance_based` | `fuel_based` | `supplier_specific`.
* **Factor requirements.** Reuses `Freighting goods` (1156) and `WTT- delivery vehs & freight` (289) — the **same**
  families as category 4. Categories 4 and 9 are separable only by an explicit boundary property.
* **Factor year.** Exact reporting year.
* **Geography.** Shipment geography.
* **Evidence.** Outbound consignment/invoice evidence.
* **Supplier.** Carrier/3PL resolves org-scoped.
* **Review triggers.** Inbound/outbound boundary undeterminable (DC-04); ambiguous mode; missing mass/distance;
  unresolved carrier.
* **Output.** kg CO2e per outbound shipment, category 9, with the downstream boundary recorded.
* **Reporting dimensions.** category, carrier, mode, boundary (downstream), year.
* **Security.** Downstream data may describe a customer's location; it is org-scoped.
* **E2E scenario.** `IA-S3-09` — one outbound shipment persisted as category 9 with a downstream boundary flag, plus
  a check proving it is not also counted in category 4.
* **Status: PARTIAL.** Prerequisites: boundary property + DC-04; a PO decision on which outbound-logistics element is
  in scope for the first delivery.

---

## 23. Category 10 — Processing of Sold Products

* **Meaning.** Emissions from third-party processing of intermediate products sold by the organisation, after sale
  and before final use. Distinct from category 1 (goods the organisation **buys**).
* **Minimum input.** Sold intermediate product; processor; quantity; processing activity; period.
* **Accepted activity types.** Downstream processing energy/fuel per unit sold; processor-declared processing emissions.
* **Methodologies.** `supplier_specific` (processor-declared) | `average_data` on processing type |
  `estimated_from_processing_energy`.
* **Factor requirements.** No live family represents downstream processing. Delivery needs a processor-declared figure
  (recorded as an explicit supplier figure with evidence) or a new governed processing factor set. A general goods
  factor must **not** be substituted.
* **Factor year.** Exact year, explicit.
* **Geography.** Processor location.
* **Evidence.** Processor declaration or processing activity evidence.
* **Supplier.** The processor resolves org-scoped as a supplier-like entity.
* **Review triggers.** No processing data; unresolved processor; the sold product is not an intermediate product;
  category 1/2 vs 10 boundary ambiguous (DC-03).
* **Output.** kg CO2e per sold product processed, category 10.
* **Reporting dimensions.** category, processor, sold product, year, data quality.
* **Security.** Downstream processor data is org-scoped; a processor that is another tenant's entity must not be
  linkable without authorisation.
* **E2E scenario.** `IA-S3-10` — one sold intermediate product with a processor-declared figure persisted as
  category 10 with evidence.
* **Status: NOT_IMPLEMENTED.** Prerequisites: processing methodology decision; the processor-declaration input
  contract; a sold-product entity; DC-03 exclusion.

---

## 24. Category 11 — Use of Sold Products

* **Meaning.** Emissions from the use of sold products by the end user, including direct (fuel/energy consuming) and
  indirect use-phase emissions, normally over the product's expected lifetime.
* **Minimum input.** Product type; units sold; expected use profile/lifetime; energy or fuel consumption per unit;
  factor; explicit assumptions.
* **Accepted activity types.** Direct use-phase fuel/energy per unit sold; lifetime-modelled use.
* **Methodologies.** `lifetime_use_based` (assumption-driven) | `supplier_specific` (product-declared use-phase figure).
* **Factor requirements.** Existing fuel/energy factors can price a product's use-phase fuel, but the product-lifetime
  consumption model does **not** exist and must not be invented. Every assumption is a first-class, persisted,
  auditable artefact.
* **Factor year.** Exact year for the pricing factor; the use-phase period is a separately recorded assumption, never
  conflated with factor year.
* **Geography.** The use-market geography materially affects grid/fuel mix and must be explicit.
* **Evidence.** Product specification / lifetime assumption record + energy-per-use evidence.
* **Supplier.** None, unless product-declared.
* **Review triggers.** Lifetime or use profile unknown; units sold unknown; no authorised assumption set for the
  product type; unknown use-phase geography.
* **Output.** kg CO2e per product type per period, category 11, with the full assumption set persisted.
* **Reporting dimensions.** category, product type, use market, assumption-set version, year, data quality.
* **Security.** Product and assumed-use data are commercially sensitive and org-scoped.
* **E2E scenario.** `IA-S3-11` — one sold product with an explicitly persisted lifetime/use assumption set, stored as
  category 11.
* **Status: DEFERRED.** Prerequisites: a PO decision authorising a bounded use-phase methodology and naming the
  product types in scope; an assumption-set entity; a sold-product entity.

---

## 25. Category 12 — End-of-Life Treatment of Sold Products

* **Meaning.** Emissions from third-party disposal/treatment of sold products at the end of their useful life.
* **Minimum input.** Sold product; quantity; material composition; waste/treatment route; geographic context; period.
* **Accepted activity types.** Sold-product material mass by treatment route.
* **Methodologies.** `material_composition_based` | `average_data` by product/waste category.
* **Factor requirements.** `Waste disposal` (134 rows) can price a route, but it is the **same** family as category 5.
  Separating 5 from 12 requires an explicit waste-origin property — structurally identical to the 4/9 problem.
* **Factor year.** Exact reporting year.
* **Geography.** End-of-life treatment jurisdiction; assumed treatment mixes must be explicit.
* **Evidence.** Material composition and the assumed treatment route, both explicitly recorded.
* **Supplier.** None (or the waste contractor where known).
* **Review triggers.** Composition unknown; unauthorised treatment-route assumption; ambiguous waste-origin boundary
  (DC-05); no factor for material/route.
* **Output.** kg CO2e per sold-product material, category 12, with the treatment assumption persisted.
* **Reporting dimensions.** category, product, material, treatment route, year, data quality.
* **Security.** Org-scoped; composition may be commercially sensitive.
* **E2E scenario.** `IA-S3-12` — one sold product with composition and an explicit treatment-route assumption,
  persisted as category 12 and **fail-closed where the route is not evidenced** (the P16 waste principle reused).
* **Status: PARTIAL.** Prerequisites: waste-origin property + DC-05; a sold-product entity; a treatment-mix
  assumption record.

---

## 26. Category 13 — Downstream Leased Assets

* **Meaning.** Emissions from the operation of assets the organisation **owns and leases out** (lessor position).
* **Minimum input.** Leased asset; lessee relationship; asset activity/energy/fuel data; period; boundary treatment.
* **Accepted activity types.** Lessor asset energy/fuel; asset-level activity.
* **Methodologies.** `direct_multiply` on asset activity data; `asset_energy_based`.
* **Factor requirements.** Same base as category 8 (`Managed assets-*`, `Fuels`). Categories 8 and 13 are separated
  only by the **direction** of the lease, which must be an explicit property of the lease relationship.
* **Factor year.** Exact reporting year.
* **Geography.** Asset location.
* **Evidence.** Lease agreement establishing the lessor position; asset activity evidence.
* **Supplier.** Lessee where relevant.
* **Review triggers.** Ambiguous lease direction (DC-06); the asset is already in Scope 1/2; missing asset activity.
* **Output.** kg CO2e per leased-out asset, category 13.
* **Reporting dimensions.** category, asset, lease direction, consolidation approach, year.
* **Security.** Lessee data belongs to another party; only aggregate asset emissions may be reported and lessee
  identity must not leak across tenants.
* **E2E scenario.** `IA-S3-13` — one leased-out asset persisted as category 13 with an explicit lessor/consolidation
  record plus a negative check against category 8 and Scope 1/2.
* **Status: PARTIAL.** Prerequisites: lease-direction property + DC-06; the consolidation-approach dimension.

---

## 27. Category 14 — Franchises

* **Meaning.** Emissions from the operation of franchises (businesses licensed to operate under the reporting
  organisation's brand), reported by the franchisor.
* **Minimum input.** Franchise relationship; franchise location; activity/energy/fuel data; period; allocation basis.
* **Accepted activity types.** Franchise site energy/fuel; franchise activity data.
* **Methodologies.** `franchisee_reported` | `average_data` by franchise type |
  `estimated_from_floor_area_or_activity`.
* **Factor requirements.** No franchise-specific family exists. Energy/fuel factors can price franchisee activity, but
  the franchise relationship and allocation basis are new domain data, and franchisee data must never be assumed
  equivalent to owned operations.
* **Factor year.** Exact reporting year.
* **Geography.** Franchise site geography.
* **Evidence.** Franchise agreement + franchisee activity/energy evidence.
* **Supplier.** The franchisee is a distinct party and must not be modelled as an ordinary supplier without an
  explicit decision.
* **Review triggers.** Missing franchise agreement; franchisee data unavailable (estimate required and must be
  explicit); ambiguous franchise-vs-owned classification; unset allocation basis.
* **Output.** kg CO2e per franchise per period, category 14, with the allocation basis and data source recorded.
* **Reporting dimensions.** category, franchise, franchise type, geography, year, data quality.
* **Security.** Franchisees may be separate legal entities and possibly separate tenants; cross-tenant read is denied
  by default and granted only through an explicit authorisation.
* **E2E scenario.** `IA-S3-14` — one franchise with an explicitly recorded allocation basis, persisted as category 14.
* **Status: DEFERRED.** Prerequisites: a PO decision on the franchise operating model (are franchisees tenants or
  external parties?); a franchise entity; the allocation-basis contract.

---

## 28. Category 15 — Investments

* **Meaning.** Emissions associated with the organisation's investments — equity, debt and project finance
  (financed emissions).
* **Minimum input.** Investment entity; investment type; ownership/exposure share; period; financial data **and/or**
  investee activity data; attribution method.
* **Accepted activity types.** Equity share of investee emissions; attributed share of investee activity/financial data.
* **Methodologies (bounded).** `attribution_equity_share` (investee activity × ownership share) is the **only**
  methodology this contract defines. PCAF-specific data-quality scoring, financed-emissions asset-class treatment and
  sector attribution rules are **DEFERRED / FRAMEWORK_SPECIFIC** and are **not** authorised here.
* **Factor requirements.** Investee activity would use existing activity factors. A financial-data-only approach
  (outstanding amount × sector factor) needs an economic-activity/sector factor set that does **not** exist, so
  financial-data-only financed emissions is DEFERRED.
* **Factor year.** Exact year for the investee activity. Investee reporting periods commonly lag; a lag must be an
  explicit recorded decision, never a silent substitution.
* **Geography.** Investee operation geography.
* **Evidence.** Investment record (holding, share, period) + investee emissions/activity evidence, or an explicit
  investee-reported figure with its source document.
* **Supplier.** The investee is **not** a supplier and must not be forced into the supplier model.
* **Review triggers.** Unknown ownership share; investee emissions unavailable; investee period lags the reporting
  year (explicit decision required); investment type outside the bounded methodology.
* **Output.** kg CO2e attributed per investment, category 15, with the attribution method and share persisted.
* **Reporting dimensions.** category, investment, investment type, attribution method, year, data quality.
* **Security.** Investee data is highly sensitive and may belong to another tenant; cross-tenant exposure is denied by
  default with an explicit authorisation path only.
* **E2E scenario.** `IA-S3-15` (bounded) — one equity investment with an explicit ownership share and an investee
  activity/emissions figure, calculated by `attribution_equity_share` only, persisted as category 15.
* **Status: DEFERRED.** Prerequisites: a PO decision ratifying the bounded `attribution_equity_share` methodology and
  explicitly deferring PCAF; an investment entity; the investee data-sharing authorisation model; the lag-handling
  decision.

**Explicit statement.** This contract does **not** claim generic "investment emissions" support. It defines a single
bounded attribution method and defers the rest.

---

## 28.1 Category status roll-up

| Category | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Status | PARTIAL | NOT_IMPL | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL | PARTIAL | PARTIAL | NOT_IMPL | DEFERRED | PARTIAL | PARTIAL | DEFERRED | DEFERRED |

* **SUPPORTED (4):** 3, 4, 5, 6 — factor base and an existing calculation path are sufficient.
* **PARTIAL (6):** 1, 7, 8, 9, 12, 13 — factor-supported or structurally derivable, with a boundary/data/dedup
  prerequisite.
* **DEFERRED (3):** 11, 14, 15 — require a ratified decision and/or reference data that does not exist.
* **NOT_IMPLEMENTED (2):** 2, 10 — no factor family, no methodology and no input contract exist.

**No blank is complete.** Per-category acceptance matrix: `artifacts/p17_acceptance_matrix_20250925.json`.

---

## 29. Factor governance

P17 preserves the P16 principle: **no silent factor-year fallback.**

### 29.1 Required factor metadata

factor source · factor set · reporting year · effective year · geography · unit · scope · **scope 3 category hint**
(proposal only) · **scope 2 method eligibility** · methodology · **factor type** (primary/secondary/component/
upstream/outside-of-scopes) · component-factor status (the existing `(kg CO2e of CH4 per unit)` markers) ·
factor provenance · version · source document.

### 29.2 Rules

1. **Exact year** or controlled review. No nearest-year, newest-year or any-year substitution — on any path.
2. **A factor mismatch produces controlled rejection, clarification, or an explicitly authorised operator override.**
   The override records actor, timestamp, reason, original factor, replacement factor and the mismatch dimension.
3. **The selected factor is persisted** on the snapshot (`factor_id`/`customer_factor_id`, `factor_source`,
   `factor_set`, `reporting_year`, `co2e_multiplier`, `factor_kind`) and the calculation uses the persisted selection.
4. **A later re-match must not silently replace an operator-selected factor.** A re-match produces a new candidate
   set; changing the used factor requires an explicit decision and, if the result changes, a new snapshot plus
   supersession.
5. **Component factors are never totals.** The P16-RD-2 defect class (a single-gas CH4 component used as a Scope 3
   total, 319.536000 kg CO2e) is currently marked `not_for_reporting` in the live data; the selection policy's
   component rule must continue to hold for every new Scope 2/3 path.
6. **`gas_coverage` must be honoured.** SEAI factors are CO₂-only while DEFRA factors are CO₂e; mixing them without
   honouring the distinction compares CO₂ with CO₂e. The dimension exists in code today
   (`domain/factor.py::gas_coverage`) but is not enforceable or queryable at the data layer — P17-A adds the column.
7. **No factor-value fabrication.** Missing coverage produces review, not invention.

---

## 30. Supplier attribution

P17 extends the P12-IMPL-02 foundation without breaking it.

**Preserved invariants.** org-scoped candidate filtering before scoring; fail-closed classification
(`exact` | `unresolved` | `confirm_creation` | `ambiguous`); only `exact` auto-persists; blank text is `unresolved`;
no candidate is `confirm_creation`; ties are `ambiguous`; the original extracted value is never overwritten;
`mapped_supplier_id` propagates to `emissions_logs.supplier_id`; multi-year identity reuse resolves to one supplier id.

**New attribution targets.**

| Target | Requirement |
|---|---|
| Scope 2 energy suppliers/providers | Attribute the supplier on the Scope 2 activity; the resolver is reused, not rebuilt |
| Instrument issuers | Recorded on the instrument; **not** required to be a supplier record unless a supplier-specific factor is used |
| Category 1 / 4 / 5 suppliers and carriers | Same resolver; carrier/3PL is a supplier |
| Supplier-specific emission factors | Must carry supplier identity evidence; a supplier-specific factor claim without supplier evidence is a review trigger |
| Primary (supplier-provided) data | Must be labelled `primary_supplier` in the data-quality dimension |

**Prohibitions.** No silent supplier creation; no silent choice among ambiguous candidates; no cross-tenant supplier
reuse; no forcing a non-supplier party (investee, franchisee) into the supplier model without an explicit decision.

---

## 31. Manual review

Manual review is a **controlled success path**, not a failure. The existing machinery is reused:
`activity_clarifications` with its adjudication lifecycle (versioned, `supersedes_id`, `is_current`,
`effective_context_key`, `evidence_signature`, `evidence_context`, `re_evaluation_required`) plus the ops
`map` / `validate` / `calculate` routes and their audit entries.

**Review states required by P17.**

| Trigger | Review kind | Resolution produces |
|---|---|---|
| ambiguous activity | `semantic_activity` (exists) | activity + factor selection |
| ambiguous unit | `semantic_unit` | unit / factor-unit reconciliation |
| ambiguous factor | `semantic_factor` | factor selection |
| ambiguous supplier | supplier resolution (`ambiguous`) | supplier confirmation/creation |
| **ambiguous Scope 3 category** | `scope3_category` (new) | explicit category 1–15 |
| waste treatment route | `semantic_activity` (exists) | factor + treatment route |
| **contractual-instrument validity** | `instrument_validity` (new) | accept / reject / request evidence |
| missing evidence | `evidence_required` | evidence attached or explicit rejection |
| **factor-year mismatch** | `factor_year` | explicit year decision or rejection |
| **boundary ambiguity** (4/9, 5/12, 8/13, Scope 1–2 overlap) | `boundary_origin` (new) | explicit boundary property |

**Every operator decision must retain:** actor, timestamp, the original extracted value, the corrected value, the
reason, the selected factor/category/method/boundary, the evidence, and the downstream calculation effect.
**The original extracted payload is never overwritten.**

---

## 32. Evidence and provenance

**Minimum immutable provenance chain (P17):**

```
REPORT (or disclosure value)
  -> reportable emissions result    (emissions_logs, reportability_status='reportable')
  -> calculation snapshot           (calculation_snapshots: factor id/source/set/year, quantity, unit,
                                     methodology, algorithm_version, content_hash, request_id)
  -> source activity                (source_item_id / source_line_item_id / source_snapshot_id for cat-3)
  -> source evidence                (evidence_line_items: file, page, line, row reference,
                                     raw description/quantity/unit, payload_hash, extraction method)
  -> extraction / mapping decisions (manual_extraction_items: extracted_data preserved beside mapped_data)
  -> factor                         (emission_factors row or customer_factor row)
  -> factor source / set / year / geography
  -> operator decisions             (activity_clarifications versions + audit entries)
  -> instrument + allocation        (market-based results only)
```

**Required support.** Source document; source page where available; source line/item; evidence snippet; extraction
method; mapping decision; factor provenance; operator decision; calculation version; data-quality classification.

**Prohibition.** "Audit ready" may not be claimed merely because `audit_trail` rows exist. The claim is available
only when the chain above resolves end-to-end for a specific result **and** has been independently verified.

---

## 33. Data quality

Explicit dimensions (investigated, defined, and — where data is absent — deferred rather than invented):

| Dimension | Values | Status |
|---|---|---|
| Primary vs secondary | `primary_*` vs `secondary_*` | defined (`data_quality`) |
| Measured vs estimated | `primary_measured` vs `secondary_estimated` | defined |
| Supplier-provided vs internally estimated | `primary_supplier` vs `secondary_estimated` | defined |
| Spend-based | `spend_based_estimated` | defined |
| Modelled | `modelled` | defined |
| Source completeness | evidence completeness on the value→evidence link | **existing** (`disclosure_value_evidence.evidence_completeness`) |
| Factor quality (type) | `factor_type` primary / secondary / component | defined (§29) |
| Geographic specificity | country vs region (currently country only) | **PARTIAL** — region-level factors absent |
| Temporal specificity | exact year vs explicitly recorded override | defined (§29) |
| Methodological specificity | `methodology` (existing) + method/category dimensions | defined |
| Evidence completeness | present / partial / unavailable | **existing** |
| Manual intervention | adjudication record + audit entry | **existing** |
| Numeric uncertainty | — | **DEFERRED** (documented; no numeric uncertainty values are invented) |

---

## 34. Reportability

P17 **reuses** the P16 lifecycle — `reportable | not_for_reporting | superseded` on both `calculation_snapshots` and
`emissions_logs`, with the invalidation-described CHECK (reason + actor + timestamp mandatory for a non-reportable
state) and the supersession link.

Rules:
1. A new P17 result is created `reportable` unless the accounting decision explicitly says otherwise.
2. Invalid results remain **historically inspectable** and are excluded from every aggregate.
3. A method change or a corrected re-calculation supersedes the previous result rather than deleting it.
4. No independent Scope 2/3 reportability model may be created.
5. Classification needs no new route: it is performed through the existing
   `POST /api/v3/emissions/calculations/{snapshot_id}/invalidate` under the P16-R6 authorization model
   (authenticated + active staff + internal staff + `can_review`), preserving the `ensure_org_access` tenant check.

---

## 35. Accounting boundaries

P17 relates to boundaries as follows.

| Boundary concept | Where it lives | P17 requirement |
|---|---|---|
| Organisational boundary | `organizations` | add `consolidation_approach` (`OPERATIONAL_CONTROL` / `FINANCIAL_CONTROL` / `EQUITY_SHARE`); MUST be explicit before categories 8/13 are reported |
| Operational boundary | activity/asset/facility dimensions | Scope 1/2 activities belong to owned/controlled operations; a Scope 3 activity must never duplicate one |
| Facilities/entities | `facilities`, `assets`, `processing_entities` | reused; `facility_id` becomes a real FK dimension |
| Leased assets | lease relationship + consolidation approach | direction (lessee/lessor) is explicit; DC-06/DC-07 apply |
| Suppliers | `suppliers` | upstream parties; org-scoped |
| Downstream relationships | sold products / customers | must not be inferred from the factor (categories 9/10/11/12) |
| Investments | new entity (deferred) | equity share only; no consolidation into Scope 1/2 |

**Double-counting paths are identified and enumerated in §47** with a prevention/detection mechanism per path.
The invariant: **one logical activity produces exactly one reportable result per method/category.**

---

## 36. Calculation architecture

```
SOURCE            document / statement / manual entry / carrier data / investee report
   |
EXTRACTION        pdf_engine / invoice_extraction / ai_document_extraction  (evidence_line_items retained)
   |
NORMALIZATION     core/units.normalize_unit (single central mechanism; no duplicated alias logic)
   |
CLASSIFICATION    scope, energy_type, category, boundary/origin, data quality   <-- P17 dimensions
   |
METHODOLOGY       direct_multiply | distance_based | spend_based | ... (existing enum)
   |
FACTOR SELECTION  factors.find_by_activity (year-explicit) -> factor_selection_policy.select_factor
   |              (deterministic; supplier/customer-factor precedence preserved)
   |
REVIEW            activity_clarifications adjudication (only when a trigger fires)
   |
VALIDATION        engines/validation.py + the new scope/method/category invariants
   |
CALCULATION       engines/calculation.py (unchanged arithmetic; authoritative, server-side)
   |
SNAPSHOT          calculation_snapshots (immutable, content_hash, deterministic request_id)
   |
REPORTABILITY     reportable | not_for_reporting | superseded
   |
REPORTING         disclosure projection -> report versions/artefacts
```

**Each transition has explicit inputs and outputs.** Where Scope 2/3 semantics differ materially from Scope 1 — the
method dimension, the category dimension, instrument/allocation handling, category-3 derivation — the logic belongs in
**domain-specific modules** (e.g. `engines/scope2_accounting.py`, `engines/scope3_category.py`,
`engines/instrument_validation.py`) rather than being buried inside the generic Scope 1 paths. The generic engine
(snapshot creation, hashing, persistence, idempotency, reportability) is shared and must not be forked.

---

## 37. Database architecture

Full delta: `artifacts/p17_schema_delta_20250925.md`.

**Inspection first.** 141 public tables, 83 migrations, latest `20261009000000`. For each requirement the delta
records: existing table reusable? existing column reusable? controlled vocabulary? new table required? relationship?
unique constraint? tenant boundary? RLS? audit requirement? lifecycle? index? migration dependency?

**Summary.**

| Requirement | Disposition |
|---|---|
| Scope 2 method dimension | EXTEND `calculation_snapshots`, `emissions_logs` (existing disclosure vocabulary reused) |
| Scope 3 category dimension | EXTEND the same two tables (+ NEW `scope3_categories` reference seed) |
| Energy type | EXTEND the same two tables (controlled vocabulary) |
| Data quality | EXTEND the same two tables |
| Facility dimension | EXTEND the same two tables (`facility_id` FK `facilities`); JSONB retained for history |
| Boundary/origin properties | EXTEND the same two tables (`transport_boundary`, `waste_origin`) |
| Category-3 derivation | EXTEND (`source_snapshot_id` self-FK + partial unique index) |
| Factor governance metadata | EXTEND `emission_factors` (`scope2_method`, `scope3_category_hint`, `factor_type`, `gas_coverage`) |
| Operator decisions on method/category | EXTEND `activity_clarifications` (resolved dimensions) |
| Accounting boundary | EXTEND `organizations` (`consolidation_approach`) |
| Contractual instruments + claims | NEW `contractual_instruments`, `instrument_allocations` |
| Estimation/assumption records | NEW `estimation_records` |
| Category taxonomy | NEW `scope3_categories` (15 reference rows) |
| Sold products / investments / franchises / residual mix | DEFERRED (no speculative tables) |

**No duplicate tables for concepts already represented.** No existing table is rebuilt. Every new table follows the
established RLS/privilege convention. Historical rows are protected by `NOT VALID` constraints and are never backfilled.

---

## 38. API architecture

**Principle: extend the existing surface before adding a new one.** The existing calculation surface is
`POST /api/v3/emissions/calculate` (with `CalculateIn`, `normalize_scope`, `require_org_member`), plus the ops item
routes (`/api/v3/ops/items/{id}/map|validate|calculate`), the clarification routes
(`/api/v3/activity-clarifications/...`), and the reportability route
(`POST /api/v3/emissions/calculations/{snapshot_id}/invalidate`).

**Recommended approach (smallest correct change).**

| Endpoint | Kind | Purpose |
|---|---|---|
| `POST /api/v3/emissions/calculate` | **extend** `CalculateIn` | Add optional `scope2_method`, `scope3_category`, `energy_type`, `facility_id`, `transport_boundary`, `waste_origin`, `data_quality`. When `scope = 'Scope 2'` the method becomes **required**; when `scope = 'Scope 3'` the category becomes required. |
| `POST /api/v3/ops/items/{item_id}/calculate` | **extend** | Same dimensions through the manual line-calculation path with the deterministic request id extended (§40). |
| `POST /api/v3/emissions/calculations/{snapshot_id}/invalidate` | **reuse** | Reportability/supersession (no change). |
| `POST /api/v3/accounting/instruments` | **new (P17-C)** | Register a contractual instrument with evidence. |
| `POST /api/v3/accounting/instruments/{id}/validate` | **new (P17-C)** | Run the validity gates (§11) and return the outcome. |
| `POST /api/v3/accounting/instruments/{id}/allocations` | **new (P17-C)** | Allocate (part of) an instrument to an activity/snapshot with quantity reconciliation. |
| `GET /api/v3/accounting/instruments/{id}` | **new (P17-C)** | Instrument + allocations + validity state. |
| `POST /api/v3/accounting/scope3/derivations` | **new (P17-E)** | Create a category-3 derivation from a source Scope 1/2 snapshot. |
| `GET /api/v3/accounting/provenance/{snapshot_id}` | **new (P17-H)** | Read the provenance chain for a result. |
| `GET /api/v3/reports/...` (existing disclosure/report surface) | **extend** | Method and category report dimensions. |

**These new endpoints are PROPOSED and unimplemented.** Before implementation they must be reconciled against the live
OpenAPI contract (locally `http://127.0.0.1:8070/api/v2/openapi.json`); no route may be invented at implementation time
merely because it is convenient.

**Per-endpoint contract requirements (all endpoints).** actor and authorization; input schema; output schema;
validation rules; error states (4xx for expected validation, 403 for authorization, 409 for state conflicts — never a
raw 500 for a user error); audit behaviour; idempotency behaviour.

---

## 39. RLS and tenant security

| New object | org ownership | actor access | staff access | consultant access | cross-tenant | service role | RLS policy | API authorization |
|---|---|---|---|---|---|---|---|---|
| `contractual_instruments` | `organization_id` NOT NULL | org member | internal staff via the existing staff context where authorised | through the client-org authorisation path only | **denied** | full (backend writes) | SELECT/INSERT/UPDATE/DELETE `is_org_member(organization_id)` | `require_org_member()` + `ensure_org_access` |
| `instrument_allocations` | `organization_id` NOT NULL, must equal parent | as above | as above | as above | **denied** | full | as above + composite parent FK | as above |
| `scope3_categories` | none (reference data) | read-only | read-only | read-only | n/a (no tenant data) | full | SELECT only; no write policy | any authenticated caller |
| `estimation_records` | `organization_id` NOT NULL | org member | internal staff where authorised | through the client-org path | **denied** | full | org-scoped DML | `require_org_member()` |
| New columns on existing tables | inherited | inherited | inherited | inherited | unchanged | unchanged | covered by the existing policies | unchanged |

**Default principle: FAIL CLOSED.** The UI is never the security boundary; a hidden control is not authorization.
The service role must not be used to bypass tenant isolation on normal application paths. Any change to RLS requires
regression testing of same-tenant allow **and** cross-tenant deny, plus role boundaries.

Security negative tests required for P17 (four-cell matrix plus role cases):
Customer A → Customer B; Consultant A → Consultant B; Consultant A → Consultant B's client; PE A → PE B;
PE → prohibited customer document; Viewer → write; Member → admin operation; Staff → Staff Admin operation;
Customer → internal operations; PE → internal operations. **Every unexpected ALLOW is a serious finding.**

---

## 40. Idempotency

P16-R7 established the mechanism; P17 preserves it and extends it to the new dimensions.

**Contract (unchanged mechanism, extended inputs).**
* The **request id is the idempotency key**.
* It is deterministic: `uuid5(NAMESPACE_DNS, f"{item.id}::calc::{idx}::c1::{digest}")` in the manual path;
  `uuid5(NAMESPACE_DNS, f"{job.id}::calc::{idx}::c1::{digest}")` in the automatic path.
* The digest covers the **stable** calculation inputs. P17 adds `scope2_method`, `scope3_category`, `energy_type` and
  the boundary/origin property, so a method or category change produces a **new** key and therefore a new, coexisting
  result — while an identical repeat still reuses the stored snapshot.
* Storage-level guarantee: `uq_calc_snapshots_request_id ON calculation_snapshots(request_id) WHERE request_id IS NOT NULL`
  closes the read-then-insert race.
* **Non-goal:** reorganising the existing key namespaces (`job.id` for automatic vs `item.id` for manual). P16-R7 §32
  recorded this as a known, documented limitation; unifying it would touch a closed gate and is out of scope.

**Per new calculation path, the implementing phase must define:** logical request identity; deterministic request id;
duplicate behaviour; concurrent-execution behaviour; supersession behaviour; reportability behaviour. **Never** create
two reportable results for the same logical calculation because a request was retried. **No** second, incompatible
idempotency mechanism may be introduced.

---

## 41. Reporting and Insight integration

**Accounting → reporting path (existing, extended).**

```
calculation_snapshots / emissions_logs  (reportable only)
        |
        v
data/disclosure_projection.py   (already filters reportability_status='reportable'; already accepts a scope_hint)
        |
        v
disclosure_values  +  disclosure_value_evidence   (value -> snapshot/log provenance already modelled)
        |
        v
report_versions / report_version_artifacts   (approval + finalisation lifecycle already exists)
```

**Integration points (exact, identified — Insight is NOT redesigned).**
1. `data/disclosure_projection.py::load_calculation_rows` / `load_emissions_rows` — extend the projection to carry and
   group by `scope2_method` and `scope3_category`, and to support a method/category filter alongside `scope_hint`.
2. `domain/disclosure.py::SCOPE2_METHODS` — already the vocabulary; report requirements that carry
   `scope2_method_hint` can now be satisfied from real accounting data.
3. `emissions_logs.supplier_id` — already a reporting and Insight dimension (P12-IMPL-02 §16).
4. `emissions_logs.metadata->>'facility_id'` / the new `facility_id` column — facility reporting dimension.
5. CarbonTally Insight reads `emissions_logs` through `domain/insight_query.py`; because the new dimensions are
   **columns on the same table**, Insight gains them without a redesign. Any Insight change beyond exposing the new
   dimensions is out of scope for P17.

---

## 42. Disclosure and framework separation

**ACCOUNTING DATA** (P17 core): scope, method, category, activity, quantity, unit, factor, factor provenance,
snapshot, emissions, evidence, reportability, data quality.

**DISCLOSURE / FRAMEWORK PRESENTATION** (later phase): frameworks, purpose versions, requirement versions, mappings,
applicability assessments, narrative, intensity ratios, official identifiers.

The boundary already exists in this repository: `disclosure_frameworks`, `disclosure_framework_versions`,
`disclosure_purpose_requirements`, `disclosure_requirement_versions`, `disclosure_requirement_mappings`,
`disclosure_applicability_assessments`, `disclosure_narrative_entries`, `disclosure_intensity_ratios`,
`disclosure_values`, `disclosure_value_evidence`, and `domain/disclosure.py` (whose `FRAMEWORK_SEEDS` carry
GHG Protocol / UK SECR / ESRS E1 identities only).

**Rules.**
1. P17 must **not** hard-code a framework-specific disclosure schema into the accounting core.
2. Accounting primitives are framework-agnostic: scope/method/category/quality — not CSRD/ESRS/SECR section numbers.
3. Where a requirement needs the method dimension, the existing `scope2_method_hint` mechanism is the seam.
4. Framework content (requirement sets, official identifiers, applicability) is a **separate later work package**.

---

## 43. Production-oriented architecture

Production is **not touched** by this task, nor by a P17 implementation until separately authorised. The architecture
is nonetheless designed to be production-viable.

| Concern | Approach |
|---|---|
| Migration strategy | Additive, idempotent migrations; `NOT VALID` constraints for new mandatory dimensions; Demo Lab / disposable clone first |
| Backward compatibility | Every new column nullable; no existing column/type/policy changed; historical rows valid under `NOT VALID`; existing routes keep working with the dimensions omitted |
| Data backfill | **None** (§44, §6 of the schema delta) |
| Feature flags | Where a phase changes existing report output, gate it behind explicit configuration so P16-verified paths stay demonstrable unchanged |
| Rollout sequencing | One phase per authorisation; migration + service + tests together; Demo Lab first |
| Observability | Reuse `audit_trail`, domain events, X7 API runtime metrics, X1 operational health; new paths emit the same signals |
| Audit logging | Every accounting decision (method, category, instrument, allocation, reportability, override) writes an audit entry with actor + timestamp + reason |
| Failure recovery | Persisted job state; resumable, idempotent, retry-safe; stale-lock recovery inherited |
| Idempotent jobs | Deterministic request ids for every new calculation path (§40) |
| Retry behaviour | Identical retry reuses the snapshot; a corrected payload produces a new result |
| Performance | Indexes per §37; batch paths must avoid N+1 candidate queries |
| Tenant isolation | §39, fail closed |
| Rollback | §7 of the schema delta |

---

## 44. Migration strategy

* **Sequence:** the five migrations of §1 of the schema delta, in the stated order, each strictly later than
  `20261009000000`.
* **Dependencies:** P17-A first (the other migrations are structurally independent but must not precede the dimension
  columns). P17-C's allocation FK references `calculation_snapshots`, which already exists. P17-D's taxonomy seed may
  accompany or follow the category column (the column itself is P17-A).
* **Backfill:** none (§43).
* **RLS sequencing:** each new table's migration enables RLS and applies grants **in the same migration** — never a
  later one — so no table is ever briefly un-protected.
* **Default privileges:** the established pattern exactly (service_role ALL; authenticated DML only; anon nothing;
  REVOKE TRUNCATE/TRIGGER/REFERENCES/MAINTAIN from authenticated).
* **Indexes/constraints:** created in the same migration as the columns they serve.
* **Historical migrations:** never modified.
* **Rollback concerns:** documented per object in §7 of the schema delta; the main risk is dropping a table a later
  phase depends on, so rollback must follow reverse dependency order.
* **Safety:** never apply a migration to a data-bearing environment whose loss matters. The integration harness
  truncates its target (invariant F-046-1), so it may only ever point at `carbontally_test` or a disposable `ct_*` clone.

---

## 45. Test strategy

| Layer | Purpose | Notes |
|---|---|---|
| UNIT | pure logic: category resolution, method validation, instrument validity gates, digest construction | `backend/tests/unit/**` (existing layout: `api`, `data`, `domain`, `engines`, `services`, `infra`, `workers`, `routes`, `tools`, `backup`) |
| INTEGRATION | real repository/DB behaviour | `carbontally_test` or a disposable clone only (F-046-1) |
| ROUTE | the real FastAPI routes with the real guards | follow `test_p16r6_route_guards_f_i.py` and `test_p16r4_core_accounting_state_machine.py` |
| RLS | policies + privileges per new table | four-cell matrix |
| TENANT ISOLATION | cross-tenant read/write denial on every new entity | negative tests mandatory |
| CALCULATION GOLDEN | expected value computed **independently** of the implementation | one per delivered Scope 2 method and per delivered Scope 3 category |
| FACTOR-YEAR | no silent year fallback on **every** candidate path, including the four §7.4 sites | negative test per path |
| MANUAL REVIEW | ambiguity → review → decision → audit → calculation → provenance | reuse and extend the adjudication suites for the new review kinds |
| EVIDENCE | the provenance chain resolves for each delivered journey | chain-walk assertions |
| IDEMPOTENCY | a repeat calculation does not change the reportable total; a method/category change does produce a new result | per new path |
| REPORTABILITY | non-reportable/superseded excluded from aggregates, readable by id | per new path |
| END-TO-END INVESTOR JOURNEYS | the journeys of §48 | Demo Lab only |

**Evidence discipline.** Expected values must not be derived from the implementation under test. A passing unit test is
not acceptance. Regression results must be classified (Class A caused-by-this-change vs Class B pre-existing vs Class E
stale expectation), following the P16-R5 / R7 / FINAL pattern.

---

## 46. Golden fixtures

Required deterministic fixtures (definition only — **not created by this task**). Every fixture must specify activity,
unit, quantity, factor, factor source, factor year, methodology, expected result, evidence and reporting dimensions.

| Fixture | Activity | Methodology | Expected value derivation |
|---|---|---|---|
| `G-S2-LOC-01` | purchased grid electricity, kWh, single site, GB, FY2025 | location-based | `kWh × DEFRA-2025 UK electricity (kg CO2e per kWh)`, computed externally and cross-checked against the published factor |
| `G-S2-MKT-01` | the **same** activity as `G-S2-LOC-01` | market-based | `kWh × market factor`; the fixture must assert the two results differ and both persist |
| `G-S2-INST-01` | activity partially covered by an instrument | market-based | covered quantity at the instrument rate + uncovered residual at the market/residual rate, with the allocation reconciled |
| `G-S3-01 … G-S3-15` | one activity per category | per §14–§28 | each computed independently from the factor value × quantity; for estimate-driven categories the expected value is computed from the **stated assumption set**, not from the code |
| `G-REVIEW-01` | ambiguous waste line | clarification | expected = the operator-selected factor × quantity, and the *original* value must remain visible |
| `G-YEAR-01` | FY2026 activity with only FY2025 factors | — | expected: **no result**, a controlled review state and no silent substitution |
| `G-IDEM-01` | any calculation, repeated identically | direct multiply | expected: unchanged reportable total and snapshot count |
| `G-SEC-01` | cross-tenant attempt on each new entity | — | expected: denial |

**Never derive an expected value from the implementation under test.**

---

## 47. Double-counting controls

Full table with detection and required tests: `artifacts/p17_acceptance_matrix_20250925.json → double_counting_controls`.

| ID | Risk | Control |
|---|---|---|
| DC-01 | Scope 1 vs Scope 2 | explicit `energy_type` + factor-family exclusion |
| DC-02 | Scope 2 vs Scope 3 category 3 | category-3 derivation must reference a source Scope 1/2 snapshot, with a **partial unique index** so one source yields at most one derivation; WTT/T&D families excluded from Scope 1/2 candidate sets |
| DC-03 | Category 1 vs Category 2 | capital-vs-expensed classification; mutually exclusive per source line |
| DC-04 | Category 4 vs Category 9 (**same factor family**) | explicit `transport_boundary`; exactly-one test |
| DC-05 | Category 5 vs Category 12 (**same factor family**) | explicit `waste_origin` |
| DC-06 | Category 8 vs Category 13 (**same factor family**) | explicit lease direction |
| DC-07 | Scope 1/2 vs a Scope 3 category (organisational boundary overlap) | consolidation approach + a same-asset/period detector |
| DC-08 | supplier data plus estimated data for the same activity | one reportable result per activity; better data **supersedes** |
| DC-09 | instrument claimed twice | claimant organisation on the instrument + allocation reconciliation |
| DC-10 | repeated calculation | deterministic request id + unique index (extended with the new dimensions) |
| DC-11 | multiple reporting views materialising their own emissions | aggregates are queries over the single authoritative result set |

**Structural statement.** Categories 4/9, 5/12 and 8/13 share factor families outright, so **no factor-level rule can
separate them**. The distinction must be a first-class, persisted property of the activity, tested by an
"appears in exactly one" assertion.

---

## 48. Investor journeys

Future E2E journeys (definition only; **none is claimed as passing**):

| ID | Journey | Demonstrates |
|---|---|---|
| `IA-S2-L` | location-based Scope 2 | real electricity → grid factor → persisted `LOCATION_BASED` result → method-labelled report line |
| `IA-S2-M` | market-based Scope 2 | same activity → market factor → persisted `MARKET_BASED` result coexisting with the location-based one |
| `IA-S2-C` | contractual instrument | register instrument → validate → allocate → market-based result → claim resolvable in the report → duplicate claim denied |
| `IA-S3-01 … IA-S3-15` | one per Scope 3 category | category-specific input → methodology → factor → calculation → persistence → category-labelled reporting |
| `IA-REVIEW` | ambiguous input → operator decision → calculation | fail-closed behaviour, original value preserved, decision audited, provenance intact |
| `IA-PROVENANCE` | source → factor → calculation → report | the full chain resolves for one result |
| `IA-SECURITY` | cross-tenant denial | every new entity denies cross-tenant read and write |
| `IA-IDEMPOTENCY` | repeat calculation does not double count | request-id reuse; unchanged reportable total |
| `IA-YEAR` | factor-year mismatch | controlled review, no silent substitution |

### 48.1 Manual-review golden journeys (required)

| # | Fixture | Trigger | Expected behaviour |
|---|---|---|---|
| 1 | ambiguous Scope 2 factor | two eligible location factors, different years | controlled review → operator selects → audit record → calculation → provenance |
| 2 | invalid contractual instrument | expired/missing evidence instrument | **no market-based result**; controlled review; result not created |
| 3 | ambiguous supplier | two near-identical org suppliers | controlled review → operator confirms → single supplier id reused |
| 4 | ambiguous Scope 3 category | an activity that could be category 1 or 2 | controlled review → explicit category → result carries it |
| 5 | ambiguous waste treatment | line without a printed route | clarification → operator selects route/factor → category 5 = 5 result |
| 6 | factor-year mismatch | FY2026 activity, FY2025 factors only | controlled review; no silent fallback |
| 7 | missing evidence | activity with no evidence line | review state; result cannot be accepted as reportable without evidence |

All seven must end with: controlled review → operator decision → audit record → calculation → provenance.

---

## 49. Implementation phases

Full plan: `CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md`.

| Phase | Title | Gate | Depends on |
|---|---|---|---|
| P17-A | Scope 2 canonical model + factor governance | `SCHEMA_AND_GOVERNANCE` | — |
| P17-B | Scope 2 location-based E2E | `SCOPE2_LOCATION_E2E` | A |
| P17-C | Scope 2 market-based + contractual instruments | `SCOPE2_MARKET_AND_INSTRUMENTS` | A (B recommended) |
| P17-D | Scope 3 canonical category model | `SCOPE3_CATEGORY_MODEL` | A |
| P17-E | Scope 3 categories 1–5 | `SCOPE3_CAT_1_5` | D |
| P17-F | Scope 3 categories 6–10 | `SCOPE3_CAT_6_10` | D |
| P17-G | Scope 3 categories 11–15 | `SCOPE3_CAT_11_15` | D |
| P17-H | Cross-category validation, double-counting controls, provenance | `INTEGRITY` | B/C, E/F/G |
| P17-I | Reporting / disclosure integration | `REPORTING` | H |
| P17-J | Independent P17 acceptance | `INDEPENDENT` | I |

**Critical path:** A → B → C → H → I → J. **P17-D** may proceed in parallel with B/C once A lands.
**All 15 categories appear** in the roadmap; a category that is `DEFERRED` or `NOT_IMPLEMENTED` must be reported as
blocked with its prerequisite named, never silently omitted.

---

## 50. Acceptance gates

Per-phase gates with `must_pass` lists: `artifacts/p17_acceptance_matrix_20250925.json → phase_gates`.

**Global acceptance rules.**
1. Only **END-TO-END VERIFIED** counts as acceptance (DOCUMENTED < CODE EXISTS < ROUTE WIRED < FACTOR AVAILABLE <
   PERSISTED < END-TO-END VERIFIED).
2. A phase is not closed because a migration applied, a route exists or a unit test passed.
3. Security acceptance requires both **ALLOW** and **DENY** cases.
4. Independent verification (P17-J) may not be performed by the implementer.
5. Production contact is a failure condition, not a risk.
6. A capability that is not E2E must be reported as not E2E.

---

## 51. Deferred items

| Item | Classification | Reason |
|---|---|---|
| Numeric uncertainty / confidence values | DEFERRED | No uncertainty data or ratified method; inventing numbers is prohibited |
| Residual mix | FRAMEWORK-SPECIFIC / DEFERRED | Reference data does not exist; market-specific rules needed |
| REGO / REC / GO jurisdiction-specific instrument rules | FRAMEWORK-SPECIFIC / DEFERRED | Depends on the governing market operator's rules |
| Grid-region-level location factors | DEFERRED | Factors are country-level (GB/IE) only; regional differentiation needs a factor set |
| Spend-based estimation (default) | PO DECISION REQUIRED | Permitted only explicitly per line until a policy is ratified |
| Capital goods (category 2) methodology | PO DECISION REQUIRED | Supplier figure vs spend-based vs new factor set |
| Processing of sold products (category 10) methodology | PO DECISION REQUIRED | Processor declarations vs a processing factor set |
| Use of sold products (category 11) methodology | PO DECISION REQUIRED | Bounded lifetime/use-phase methodology and its product scope |
| Franchises (category 14) operating model | PO DECISION REQUIRED | Are franchisees tenants or external parties? |
| Investments (category 15) beyond `attribution_equity_share` | FRAMEWORK-SPECIFIC / DEFERRED | PCAF scoring, asset-class treatment and sector attribution rules are explicitly not authorised |
| Sold-product entity (needed by 9–13) | DEFERRED | Requires the product/boundary decision |
| Framework disclosure content (requirement sets, official identifiers) | DEFERRED | Separate later work package; the accounting core stays framework-agnostic |
| CarbonTally Insight changes beyond exposing the new dimensions | OUT OF SCOPE | No redesign is required or authorised by P17 |
| Step 3 UI | NOT AUTHORISED | Separate authorisation |
| D19 workbench changes | PO REVIEW REQUIRED | Frozen UX |
| Factor library expansion (2026 set, new families) | DEFERRED | Requires a separately authorised import; no fabricated factors |
| SEAI expansion | DEFERRED to Version 4 | P14 contract §12 |
| Production deployment | NOT AUTHORISED | Separate authorisation |

---

## 52. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | The method dimension is adopted as a label but not enforced, so a market-based result can still be mistaken for location-based | High | CHECK constraints, required on write, part of the idempotency key, a report dimension, plus the dual-method invariant test |
| R2 | Category inferred from factor family → silent misclassification (4/9, 5/12, 8/13 share families) | High | AD-P17-02; explicit boundary/origin properties; "exactly one" tests |
| R3 | Historical rows backfilled with fabricated categories/methods | High | `NOT VALID` constraints; backfill prohibited; adjudication-only route for history |
| R4 | Instrument claimed twice, or over-allocated | High | Claimant org on the instrument row; allocation reconciliation; cross-tenant negative tests |
| R5 | Request-id digest not extended with the new dimensions → duplicate reportable results after a method/category change | High | DC-10 mandatory per phase |
| R6 | Cross-year factor candidates remain unlabelled (four §7.4 sites) | Medium-High | P17-A closes this explicitly; a negative test per path |
| R7 | A `DEFERRED`/`NOT_IMPLEMENTED` category reported as delivered | High (credibility) | Matrix status carried into every report; acceptance language rule |
| R8 | Framework compliance implied because the schema resembles one | High (legal/credibility) | §42 separation; explicit non-claims |
| R9 | Scope creep into Insight/UI redesign | Medium | Scope statements per phase; PO review for frozen UX |
| R10 | Migration advances the two already-failing migration-count tests | Low | Update the stale expectation in the same phase and report it |
| R11 | Destructive integration harness pointed at a data-bearing DB | Critical | Invariant F-046-1; disposable clone only |
| R12 | Facility dimension added but JSONB left inconsistent for new rows | Low-Medium | Explicit migration note; decide and test the write behaviour |
| R13 | Effort underestimation: 15 categories × (input contract + factor rule + evidence + tests) is the largest body of work in the programme | Medium | Phase split with per-category gates; DEFERRED categories are named, not half-attempted |
| R14 | `emission_factors` classification (method eligibility, category hint, factor type, gas coverage) is a large curation task over 7,049 rows | Medium | No fabrication; classify incrementally; default `NULL` (unclassified) and require explicit review where a NULL blocks a method |

---

## 53. Final architecture decision

The P17 architecture is defined, internally consistent, evidence-based and implementable in bounded phases. It reuses
the P16-verified accounting spine rather than duplicating it, adds exactly two canonical dimensions (method, category)
plus the supporting dimensions the audit evidence requires, and introduces only three genuinely unavoidable new
entities — contractual instruments, instrument allocations and estimation records — with a fourth as pure reference
data (the 15-category taxonomy).

**What is not claimed.** No Scope 2 or Scope 3 capability is implemented. No framework compliance. No assurance
readiness. No regulatory compliance. The 25 existing Scope 3 rows remain uncategorised by design.

**What is now decided.**

* Scope 2 is one activity with two coexisting, independently persisted, method-tagged results.
* Contractual instruments are a first-class org-scoped entity with a claim/allocation ledger whose invariants are
  enforceable and testable.
* Scope 3 category is a required, explicit, non-inferred dimension of every new Scope 3 result.
* Category separation is achieved by explicit boundary/origin properties, because factor families are shared.
* Factor year is governed on **every** path, closing the four-site gap this contract found.
* Reportability, idempotency, evidence, manual review and tenant isolation are reused, not re-invented.

---

## 54. Implementation authorization recommendation

**P17_ARCHITECTURE_STATUS: `PARTIAL — PREREQUISITE DECISIONS REQUIRED`**

**Why not `READY_FOR_IMPLEMENTATION`:** two authoritative **post-contract Product Owner decision records** were found
in the working tree that amend this contract and explicitly require reconciliation into it before affected
implementation begins (§57). They are:

* `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md`
* `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` — whose §51 names *this* contract as the foundational
  Scope 2 / Scope 3 contract and lists the reconciliation items it must incorporate

Neither document was created by this task and neither is committed by it. They exist, they are marked **APPROVED
PRODUCT-OWNER DECISIONS**, and they change the mandated scope of affected P17 phases: customer-owned data
contribution, accounting-governance-controlled reportability, organization capabilities, acting-for context, and
**complete UI/UX as a mandatory part of applicable feature delivery**. The P17 architecture does not *conflict* with
them — AD-P17-01 already mandates one shared accounting core, which is precisely their §2 product decision — but the
contract must be **amended** to incorporate them, and that amendment is not performed by this task.

**Recommended first implementation phase (unchanged, but gated):**

> **P17-A — Scope 2 canonical model + factor governance**
> Migration `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`
> Gate `SCHEMA_AND_GOVERNANCE`
> **Gated behind completion of the §57 reconciliation register** — the register may add columns (e.g. source actor /
> acting context) to the same migration, and one amendment is cheaper and safer than two migrations.

Reason P17-A remains the recommended first phase: it is the prerequisite of every other phase, it is fully specified
here, it fabricates nothing (additive columns + `NOT VALID` constraints + a governance fix touching no accounting
value), it is independently verifiable without new factor or instrument data, and it closes the one concrete,
currently verifiable defect this contract found — unlabelled cross-year factor candidates at four production call sites.

**PO decisions required later in the sequence (unchanged):**
(a) whether market-based reporting may rely on contractual instruments at P17-C; (b) whether location-based geography
may resolve at national level when no regional factor exists; (c) whether spend-based estimation is authorised at all
(affects categories 1 and 2). Each is recorded as an open question in the Scope 2 and category matrices.

**This task does not implement P17-A.** Implementation must be separately authorised **after** the §57 reconciliation.

---

## 55. Required final answers

**A. Is the P17 architecture sufficiently defined to begin implementation?**
Yes — `READY_FOR_IMPLEMENTATION`. The domain contract (33 classified Scope 2 fields), the 15-category contract
(16 fields each), the schema delta, the API contract, the RLS model, the idempotency extension, the acceptance matrix
and the phase plan are complete. Three PO decisions are required later and block only specific phases.

**B. What is the first implementation phase?**
**P17-A** (Scope 2 canonical model + factor governance; migration `20261010000000`; gate `SCHEMA_AND_GOVERNANCE`).

**C. What schema changes are actually required?**
* EXTEND `calculation_snapshots` and `emissions_logs` with `scope2_method`, `scope3_category`, `energy_type`,
  `data_quality`, `facility_id` (FK), `transport_boundary`, `waste_origin`, `source_snapshot_id`; add the
  `NOT VALID` scope-rules, the category-3 partial unique index and supporting indexes.
* EXTEND `emission_factors` with `scope2_method`, `scope3_category_hint`, `factor_type`, `gas_coverage`.
* EXTEND `activity_clarifications` with the resolved method/category; EXTEND `organizations` with
  `consolidation_approach`.
* NEW `contractual_instruments`, `instrument_allocations`, `scope3_categories` (15 reference rows),
  `estimation_records`.
* DEFERRED: sold products, investments, franchises, residual mix.

**D. Which existing tables/services should be reused?**
`calculation_snapshots`, `emissions_logs`, `emission_factors`, `customer_factors`, `factor_aliases`, `units`,
`evidence_line_items`, `manual_extraction_items`, `activity_clarifications` (+ adjudication lifecycle), `suppliers` +
`engines/supplier_resolution.py`, `facilities`/`assets`, the reportability lifecycle, the calculation engine and its
snapshot/hash/idempotency mechanics, `engines/factor_selection_policy.py`, `engines/validation.py`,
`data/disclosure_projection.py`, `disclosure_values`/`disclosure_value_evidence`, `report_versions`/
`report_version_artifacts`, and the existing auth/tenant guards.

**E. Which new domain entities are unavoidable?**
`contractual_instruments`, `instrument_allocations`, `scope3_categories` (reference), `estimation_records`. Nothing
else is proposed; sold products, investments and franchises are deferred pending PO decisions.

**F. What must remain frozen?**
Historical migrations; the canonical PDF corpus / ground truth / oracle / generator (byte-identical); all P16/P12/P14
reports; the `reportable | not_for_reporting | superseded` lifecycle; `uq_calc_snapshots_request_id` and the
deterministic-id mechanism; the `activity_clarifications` adjudication lifecycle; the supplier resolver contract; the
`SCOPE2_METHODS` disclosure vocabulary; RLS policies and privileges; the D17/D19/D21 frozen UX decisions.

**G. What acceptance evidence is mandatory?**
Only END-TO-END VERIFIED counts: a persisted chain source → input/extraction → mapping/category+method → factor →
calculation → snapshot/log → evidence → reportability → reporting, plus (a) before/after row integrity for every
migration, (b) `NOT VALID` constraint enforcement proofs, (c) negative tenant-isolation tests, (d) idempotency re-run
proofs per new path, (e) method/category dual-coexistence proofs, (f) independent verification at P17-J.

**H. Which Scope 2 capabilities are MUST-HAVE?**
Location-based calculation; market-based calculation; independent persistence of both; the method dimension enforced
on write; factor-year enforcement on every candidate path; contractual instrument registration + validation +
allocation with duplicate-claim and over-allocation denial; evidence/provenance; the manual-review path for an
ambiguous/invalid case; supplier/provider attribution; reuse of the reportability lifecycle; idempotency; tenant
isolation; method-distinct reporting; no silent fallback; independent verification.

**I. Which of the 15 Scope 3 categories are ready for implementation, and which need prerequisite work?**
* **Ready (SUPPORTED):** 3, 4, 5, 6.
* **Ready with a named prerequisite (PARTIAL):** 1 (spend-based decision + category dimension), 7 (estimation record +
  estimate authorisation), 8/13 (consolidation approach + lease direction), 9 (boundary property), 12 (waste-origin
  property).
* **Prerequisite work required (NOT_IMPLEMENTED):** 2 (capital-goods methodology + DC-03), 10 (processing methodology
  + processor-declaration contract + sold-product entity).
* **PO decision required (DEFERRED):** 11, 14, 15.

**J. What is the exact dependency order?**
P17-A → (P17-B → P17-C) and/or P17-D → P17-E/F/G → P17-H → P17-I → P17-J, with the critical path
A → B → C → H → I → J and P17-D able to run in parallel with B/C once A lands. All 15 categories are covered by
E/F/G; DEFERRED categories are carried as named, blocked items rather than omitted.

---

## 56. Task outcome

| Item | Value |
|---|---|
| Architecture status | `PARTIAL — PREREQUISITE DECISIONS REQUIRED` (post-contract PO reconciliation outstanding — §57) |
| Post-contract PO decisions discovered | **YES** — 2 records, not created by this task, not committed by it |
| Reconciliation into this contract | **NOT PERFORMED** — registered as §57 and required before affected implementation |
| Implementation started | **NO** |
| Production contacted | **NO** |
| Code changed | **NO** (documentation/artifact files only) |
| Migrations created | **NO** |
| Factors created/changed | **NO** |
| Corpus/oracle changed | **NO** |
| Independent verification | **NOT PERFORMED** (this is an architecture contract, not a verification task) |
| First phase recommended | P17-A (recommended only; not implemented; gated behind §57) |

---

## 57. Post-contract PO decision reconciliation register (MANDATORY before affected implementation)

Two **APPROVED PRODUCT-OWNER** decision records exist in the working tree that post-date the issue of this task and
amend it. They are **not** created, modified or committed by this task; they are recorded here because they are
authoritative and because they change mandated scope.

| Source | Path | Role |
|---|---|---|
| D1 | `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | Carbon accounting management + customer-owned emissions data |
| D2 | `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | Post-P17-ARCH-01 PO decision record — Unified Carbon Accounting Management System (CAMS); its §51 explicitly lists the reconciliation items this contract must incorporate |

### 57.1 Reconciliation items and their effect on this contract

| # | PO decision (source) | Effect on this contract | Sections to amend |
|---|---|---|---|
| 1 | **One Unified Carbon Accounting Management System**; no separate Staff / Customer / Consultant / Client accounting systems (D2 §2, §37; D1 §2, §21) | **Confirms** AD-P17-01. No architectural conflict. Must be stated explicitly as a P17 design constraint so no phase forks the core. | §8.1 (add AD-P17-13), §36 |
| 2 | **Customer-owned emissions data contribution**, enabled by CarbonTally; customers and consultants enter/manage their organisation's activity data (D1 §2, §4; D2 §5, §7, §28) | **NEW INPUT CHANNEL.** The pipeline gains a customer/collaborator entry point (`DRAFT`/`SUBMITTED` origin) that must flow through the same validation → factor → review → reportability path, with the source actor recorded. | §29, §31, §32, §36, §38 |
| 3 | **Customer data does not automatically become reportable**: `DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED → REPORTABLE`, with rejection/correction/invalidation/supersession (D1 §7; D2 §9) | **AMENDS §34.** The P16 reportability lifecycle remains the accounting-result state, but it must be reachable only through a governed submission/approval flow. Reconciliation must map the PO lifecycle onto the **existing** state machines (`customer_documents.status`, `manual_extraction_items` status flow / `ITEM_STATUS_FLOW`, `review_*`) rather than create a competing one. | §34, §31, §47 (DC-08) |
| 4 | **Customer permission ≠ accounting authority**; customers must not change governed methodology, factors, validation, mandatory review, reportability, snapshots or governance configuration, and must not access another organisation (D1 §9; D2 §7, §8) | **AMENDS §39.** Adds explicit prohibitions plus an organization-capability dimension: capability is CarbonTally-controlled, granular and enforced server-side. | §39, §31 |
| 5 | **Organization-level capabilities + capability management UX** (D2 §7, §42) | **NEW REQUIREMENT** — a capability model plus its management surface, honoured wherever an accounting action becomes capability-gated. | §38, §39, phase plan |
| 6 | **Acting-for / source-actor context must be recorded**; the audit trail captures acting context; a consultant acts for an authorised client (D2 §14, §18, §22, §23) | **AMENDS §32 and §40.** Provenance and the calculation record must carry the source actor and the acting organisation context, so an audit can attribute every contribution while the client organisation retains ownership of reporting and evidence (D2 §24, §25). | §32, §40, §47 (DC-10 digest inputs) |
| 7 | **Consultant organisations are first-class customers; consultant clients are independent organisations with their own data/evidence/calculations/reporting/audit; consultant access is delegated and client-specific** (D1 §11; D2 §12–§18) | **AMENDS §39.** Delegated client access must be honoured at the accounting layer; client-org data ownership and isolation are absolute. | §35, §39 |
| 8 | **Complete UI/UX required for all applicable features** — backend/domain only is insufficient (D1 §6, §23; D2 §41, §50) | **AMENDS THE PHASE PLAN SIGNIFICANTLY.** UI/UX becomes **mandatory scope inside** affected P17 phases (Scope 2 overview / dual-method views / instrument management / evidence; Scope 3 overview + Category 1–15 category-specific workflows; review and exception queues; reportability state; history; organization-context visibility). It may no longer be deferred wholesale to "Step 3". **Largest single reconciliation item.** | §49, phase plan §3–§10 |

| 9 | **Scope 2 product requirements**, including purchased **cooling where applicable** and governed instrument records rather than a text field (D1 §14; D2 §27) | **CONFIRMS** §9/§10/§11 and adds the explicit requirement that cooling, when requested and unsupported by factors, is a **fail-closed review state**, not a fabricated result. | §9, §14–§19 (UX scope) |
| 10 | **Scope 3 distributed data collection** across procurement / finance / facilities / HR / travel / logistics / waste / suppliers, with category-specific workflows (D1 §15; D2 §28) | **EXTENDS §13.** Category data may be contributed by multiple parties; every contribution requires source-actor capture and the same governed pipeline. | §13, §29, §31, §38 |
| 11 | **Supplier data enters the same controlled pipeline** with tenant-respecting attribution (D1 §16; D2 §29) | **CONFIRMS §30.** | §30 |
| 12 | **Mandatory existing-vs-missing discovery and classification; reuse over duplication** (D1 §5, §22, §26; D2 §38, §39, §40) | **ADDED GATE.** Each affected implementation phase must begin with a documented existing / partial / disconnected / duplicated / missing classification before changing code. | phase plan (all phases), §50 |
| 13 | **P16 controls must remain intact**; P16 regression protection (D1 §24; D2 §45) | **CONFIRMS** §2 and §46. | §2, §45 |
| 14 | **Reporting belongs to the client organization; evidence belongs to the organization whose accounting it supports** (D2 §24, §25) | **AMENDS §35 and §41.** Report and evidence ownership is the client organisation, never the consultant's. | §35, §41 |
| 15 | **PASS / PARTIAL / FAIL / BLOCKED / DEFERRED** acceptance vocabulary and mandatory report contents (D2 §47, §48) | **ALIGNS** with §50 and this report's format; adopt the five-way vocabulary verbatim in phase reports. | §45, §50 |
| 16 | **Production not authorised** (D1 §27; D2 §46) | **CONFIRMS** §3 and §43. | §3, §43 |

### 57.2 Reconciliation status

| Item | Status |
|---|---|
| D1/D2 discovered and registered | **DONE** (this §57) |
| Contract amendments to §8.1, §13, §29, §31, §32, §34, §35, §38, §39, §40, §41, §45, §49, §50 and the phase plan | **NOT DONE** — required before affected implementation |
| Highest-impact amendment | **Item 8 (mandatory UI/UX inside affected phases)** — changes phase scope, effort and gates; cannot be satisfied by schema work |
| Second highest | **Item 3 (governed submission/approval before reportability)** — changes when a result may enter a report aggregate |
| Recommended vehicle | a small documentation-only **reconciliation task** (e.g. `P17-RECON-01`) amending this contract and the phase plan, or an explicit PO ratification that specific items are already satisfied by existing P16/P12/P16-follow-on machinery (for items 3, 6 and 14 a partial mapping onto existing state machines and audit fields may suffice) |

### 57.3 Explicit non-claims

* This contract does **not** claim items 1–16 are implemented, reconciled or verified.
* This contract does **not** claim the existing `customer_documents` / item / review state machines already satisfy the
  PO reportability lifecycle — that mapping must be demonstrated, not assumed.
* This task **did not** modify D1 or D2, and did not commit them (they remain untracked working-tree files authored
  outside this task).
* **Production remains not authorised.**
























