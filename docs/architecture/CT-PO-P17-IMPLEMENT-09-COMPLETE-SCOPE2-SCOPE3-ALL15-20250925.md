# P17-IMPLEMENT-09 — Complete Scope 2 + Scope 3 (all 15 categories): real-PostgreSQL hardening

**Task ID:** `P17-IMPLEMENT-09-20260925-COMPLETE-SCOPE2-SCOPE3-ALL15`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `1d438ff4d8d0bd8a05a92144cf27e984cafc9d24` (verified with `git rev-parse HEAD` before any edit)
**Nature:** IMPLEMENTATION. No UI/marketing change, **no migration**, no RLS change, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-09-20260925-COMPLETE-SCOPE2-SCOPE3-ALL15`

## 2. Starting SHA

`1d438ff4d8d0bd8a05a92144cf27e984cafc9d24` — the IMPLEMENT-08 SHA-recording commit.
Working tree before work: clean apart from the pre-existing `.gitignore` modification and
unrelated untracked files (§23). The four earlier P17 commits (`73c8b9c`, `e966357`,
`c399615`, `4505e6f`…`7739ed7`) were verified present; nothing was rewritten.

## 3. Ending SHA

`0c33055719d0337a365c02e156c05db6b5af9f01` — the commit that recorded this report (§4).

## 4. Every commit SHA

| # | SHA | Message |
|---|---|---|
| 1 | `75377cc0cf9efa05a2eb1653b3fcdef9fcd468a5` | `fix(p17-09): persist Scope 2/3 logs against the real P17 schema, and verify on real PostgreSQL` |
| 2 | `0c33055719d0337a365c02e156c05db6b5af9f01` | `docs(p17): record IMPLEMENT-09 report (PARTIAL — real-PG verified, applicability model deferred)` |
| 3 | *(SHA-recording commit)* | `docs(p17): record IMPLEMENT-09 commit SHAs` — created after this report; its own SHA cannot appear inside itself, so it is named rather than numbered (same convention as the IMPLEMENT-08 report) |

**Not pushed.** No amend/rebase/reset/force-push; all prior P17 history preserved.
Verification commands and their results are in §4.1.

### 4.1 Report/SHA verification

```
$ git log --oneline -3
<sha> docs(p17): record IMPLEMENT-09 commit SHAs
0c33055 docs(p17): record IMPLEMENT-09 report (PARTIAL — real-PG verified, applicability model deferred)
75377cc fix(p17-09): persist Scope 2/3 logs against the real P17 schema, and verify on real PostgreSQL

$ git log --oneline -1 -- docs/architecture/CT-PO-P17-IMPLEMENT-09-COMPLETE-SCOPE2-SCOPE3-ALL15-20250925.md
0c33055 docs(p17): record IMPLEMENT-09 report (...)

$ git status --porcelain | grep -v '^??'
 M .gitignore      # pre-existing, deliberately NOT committed
```


## 5. Files created

| File | Purpose |
|---|---|
| `backend/tests/integration/test_p17_09_scope2_scope3_persistence_runtime.py` | The **real-PostgreSQL round-trip**: 34 tests over the real services, engine, repositories and P17 schema |
| `docs/architecture/CT-PO-P17-IMPLEMENT-09-COMPLETE-SCOPE2-SCOPE3-ALL15-20250925.md` | This report |

## 6. Files modified

| File | Change |
|---|---|
| `backend/data/emissions_logs.py` | `create()` gains `accounting_dimensions` (appended last, default `None`) and writes the ten P17 dimension columns in the INSERT — **defect 1 fix** |
| `backend/engines/calculation.py` | `_persist_log` passes `accounting_dimensions` to `create()`; `CalculationSink` protocol and `from_match_result` gain the supplier/dimension plumbing |
| `backend/api/accounting_context_auth.py` | New `resolve_authorized_supplier()` — resolves a supplier CLAIM against the resolved data owner |
| `backend/api/v3_scope3.py` | Resolves + validates the claimed supplier; passes the validated id through |
| `backend/api/v3_scope2.py` | Accepts `supplier_id`, resolves it the same way, passes it through |
| `backend/services/scope3_calculation.py` | Passes `supplier_id` into the canonical request (it was accepted and silently dropped) |
| `backend/services/scope2_calculation.py` | `Scope2Input.supplier_id` + pass-through |
| `backend/tests/integration/verify_p17_08_scope3_persistence_schema.py` | Certifies any F-046-1-permitted target (`carbontally_test` **or** a `ct_*` clone); checks the full P17 column set on both tables, the RLS posture and the DC-09 function; refuses protected names |
| `backend/tests/integration/test_emissions_logs.py` | Supplies the method a Scope 2 log must state (P17 CHECK), and preserves it across a read-modify-write |
| `backend/tests/unit/{api/fakes.py, api/test_p17_06_*, api/test_p17_08_*, engines/test_calculation.py, engines/test_customer_factor_integration.py, engines/test_p17_04_*, services/test_p17_05_*, services/test_p17_07_*}` | Interface adaptation: the sink doubles accept `accounting_dimensions` |
| `src/providers/seai/tests/test_defra_regression.py` | Same interface adaptation for the SEAI provider's sink double |

`backend/engines/calculation.py` is the canonical bridge; no second engine, no second
repository and no new table was introduced anywhere in this task.

---

## 7. The two defects the real-PostgreSQL round-trip exposed

This is the substantive content of the task. Both defects were invisible to every unit
and API test in the repository because those tests use in-memory sink doubles. Both were
confirmed against a real PostgreSQL instance, and both are now fixed and re-verified.

### 7.1 BLOCKING — the canonical write path could not persist a Scope 2/3 result

`supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`
adds to `public.emissions_logs`:

```sql
emissions_logs_scope2_method_required  : (scope <> 'Scope 2') OR scope2_method IS NOT NULL
emissions_logs_scope3_category_required: (scope <> 'Scope 3') OR scope3_category IS NOT NULL
```

declared **`NOT VALID`** — historical rows are exempt, **every new row is enforced**.

`EmissionsLogsRepository.create()` inserts the operational log, and was written (before
P17) with only the pre-P17 columns. P17-IMPLEMENT-04 added the dimensions to `save()` —
the *later* UPDATE — and not to `create()`. The engine's order is
`save_snapshot → create → save`, so the first statement already violated the constraint:

```
asyncpg.exceptions.CheckViolationError: new row for relation "emissions_logs"
violates check constraint "emissions_logs_scope3_category_required"
```

**Consequence, before the fix:** every successful Scope 2 and Scope 3 calculation was
rejected by PostgreSQL. Because the failure was a raw database exception it would have
surfaced to the user as a technical error (AGENTS.md §46), and *no Scope 2 or Scope 3
emissions result could exist in a P17 database at all.* This is precisely what
IMPLEMENT-08 could not see while its only target was a stale, un-migrated database.

**Fix (smallest correct change):** `create()` gains
`accounting_dimensions: Optional[AccountingDimensions] = None`, appended **last** with a
default so every pre-existing positional or keyword caller is byte-for-byte unchanged, and
writes the ten dimension columns in the same INSERT. `CalculationEngine._persist_log`
passes the same `AccountingDimensions` object it already passed to `save()`, so the
snapshot/log pair remains structurally unable to disagree.

**Evidence the fix is load-bearing:** with this change stashed, **24 of the 34**
real-PostgreSQL tests fail (all the positive persistence paths); with it, **34/34 pass**
(§19).

### 7.2 `supplier_id` was accepted and silently discarded

The `POST /api/v3/scope3/calculate` body and `Scope3Input` both carry `supplier_id`, and
`build_request()` never forwarded it. The claim was therefore accepted, reported as
successful, and **dropped**: `emissions_logs.supplier_id` stayed NULL. Scope 2 had no
supplier field at all. `emissions_logs.supplier_id` carries **no foreign key**, so nothing
in the database would have caught it — and an arbitrary cross-tenant supplier id would
have been stored silently.

**Fix:** the supplier is a **claim** and is resolved server-side against the resolved
data-owning organization by the new `resolve_authorized_supplier()`; a supplier belonging
to another organization is refused with **422**, deliberately indistinguishable from one
that does not exist. The validated id then reaches `emissions_logs.supplier_id` through
`CalculationRequest.from_match_result(..., supplier_id=...)`. `None` stays NULL: an
unresolved supplier is never invented.

---

## 8. Scope 2 implementation matrix

| Capability | Status | Evidence |
|---|---|---|
| Electricity | **VERIFIED** | `energy_type` persisted on snapshot + log |
| Heat | **VERIFIED** | parametrized round-trip test |
| Steam | **VERIFIED** | parametrized round-trip test |
| Cooling | **VERIFIED** | parametrized round-trip test |
| `fuel` is not a Scope 2 energy type | **VERIFIED** | refused by the domain guard, nothing persisted |
| Location-based | **VERIFIED** | `scope2_method='LOCATION_BASED'` persisted on both rows |
| Market-based | **VERIFIED** | `scope2_method='MARKET_BASED'` persisted; instrument loaded server-side |
| Contractual instruments | **VERIFIED** | instrument persisted through the real repository; eligibility enforced |
| Allocation | **VERIFIED** | `instrument_allocations` row written only after the snapshot exists (FK `ON DELETE RESTRICT`) |
| DC-09 over-allocation | **VERIFIED** | `p17_instrument_over_allocated()` = `false` at full allocation; the domain guard refuses the next unit |
| Ineligible (retired) instrument | **VERIFIED** | refused, nothing persisted |
| Wrong-scope factor | **VERIFIED** | `AccountingDimensionError`, nothing persisted |
| Wrong factor year | **IMPLEMENTED** · **TESTED** (unit, P17-05) | factor-governance check in the service |
| Evidence / provenance | **IMPLEMENTED** · **TESTED** | source refs, factor id/kind, facility, attribution persisted |
| Data quality | **IMPLEMENTED** · **TESTED** | `primary_measured` persisted on both rows |
| Supplier-specific evidence | **IMPLEMENTED** · **VERIFIED** as of this task | the utility/energy supplier now reaches the log |
| Reporting identity | **PARTIAL** | `scope2_method` / `energy_type` are persisted and returned by the API, but are **not yet exposed by the analytics read projection** (§24) |
| Scope 2 UI | **NOT IN SCOPE** | §23 |

## 9. Scope 3 — 15-category implementation matrix

Architecture statuses are reported **verbatim** from `domain/scope3.py`. Nothing in this
task upgraded a status.

| Cat | Category | Architecture status | Pathway adopted by its contract | Result identity persisted |
|---|---|---|---|---|
| 1 | Purchased goods and services | `PARTIAL` | ACTIVITY_FACTOR (also ESTIMATION) | **VERIFIED** |
| 2 | Capital goods | `NOT_IMPLEMENTED` | ACTIVITY_FACTOR, gated on `capitalisation_declared` | **VERIFIED** |
| 3 | Fuel- and energy-related activities | `SUPPORTED` | ACTIVITY_FACTOR (DC-02 derivation) | **VERIFIED** |
| 4 | Upstream transportation and distribution | `SUPPORTED` | ACTIVITY_FACTOR (also ESTIMATION) | **VERIFIED** |
| 5 | Waste generated in operations | `SUPPORTED` | ACTIVITY_FACTOR (also ESTIMATION) | **VERIFIED** |
| 6 | Business travel | `SUPPORTED` | ACTIVITY_FACTOR (also ESTIMATION) | **VERIFIED** |
| 7 | Employee commuting | `PARTIAL` | ESTIMATION (also ACTIVITY_FACTOR) | **VERIFIED** |
| 8 | Upstream leased assets | `PARTIAL` | ACTIVITY_FACTOR (DC-07) | **VERIFIED** |
| 9 | Downstream transportation and distribution | `PARTIAL` | ACTIVITY_FACTOR (DC-04) | **VERIFIED** |
| 10 | Processing of sold products | `NOT_IMPLEMENTED` | ESTIMATION | **VERIFIED** |
| 11 | Use of sold products | `DEFERRED` | ESTIMATION (explicit use-phase assumption) | **VERIFIED** |
| 12 | End-of-life treatment of sold products | `PARTIAL` | ACTIVITY_FACTOR (DC-05) + estimation record | **VERIFIED** |
| 13 | Downstream leased assets | `PARTIAL` | ACTIVITY_FACTOR (DC-07) | **VERIFIED** |
| 14 | Franchises | `DEFERRED` | ESTIMATION (explicit allocation basis) | **VERIFIED** |
| 15 | Investments | `DEFERRED` | ESTIMATION (explicit attribution basis) | **VERIFIED** |

All fifteen are exercised by the real-PostgreSQL round-trip: `scope3_category`, `scope`,
`methodology`, `data_quality`, `reporting_year`, `factor_id`, the boundary declarations and
the acting-for/performed-by pair are asserted on the **stored row**, for every category
(§19, §20).

**What "VERIFIED" means here, and what it does not.** It means the category's identity,
methodology label, data-quality classification, factor provenance, boundary declaration and
attribution can be accepted, validated, calculated and **persisted** on real PostgreSQL
without double counting or fabrication. It does **not** mean every GHG Protocol calculation
method named in the product specification is implemented for that category. The honest
per-category gaps are in §9.1 — no architecture status was changed to manufacture a PASS.


### 9.1 Per-category gaps that remain

* **1** — supplier-specific, average-data and spend-based labels are declared by the
  contract; the persisted `methodology` column still records the engine methodology
  (`direct_multiply`). Supplier **PCF/EPD ingestion** and the hybrid method are **DEFERRED**.
* **2** — capitalisation is a **required declaration**, i.e. exactly the discriminator the
  taxonomy recorded as absent; the status stays `NOT_IMPLEMENTED`. Fixed-asset-register
  ingestion and an automatic capitalisation-boundary control are **DEFERRED**.
* **3** — implemented as a DC-02 derivation hard-linked to its source Scope 1/2 snapshot,
  with a partial unique index preventing a second derivation. **VERIFIED**.
* **4 / 9** — tonne-km / distance-based / mode-specific modelling is **PARTIAL**; distance,
  mass, mode and shipment are carried in `inputs`, not as first-class columns.
* **5** — `material` + `treatment_route` are required and the origin is persisted via
  `waste_origin`; per-material route factor families are **PARTIAL**.
* **6** — the **business-trip grouping/journey layer** required by P17-PRODUCT-01 §16 is
  **DEFERRED**: each leg can be calculated and audited independently, but nothing groups
  seven activities into one persisted journey.
* **7** — an explicit, labelled estimate with a persisted estimation record. Survey import
  (CSV/XLSX) and aggregate extrapolation are **DEFERRED**.
* **8 / 13** — the consolidation-approach discriminator is *required* by the guard, but
  `consolidation_approach` is **not a persisted column**, so the decision is not recoverable
  from the stored row alone (§24).
* **10** — estimation-only by design: no processing-specific factor family exists and none
  was invented. `NOT_IMPLEMENTED` remains the reported status.
* **11** — the use-phase/lifetime assumption is **required and persisted** in the estimation
  record; a product/lifetime model is **DEFERRED**.
* **12** — the DC-05 origin `sold_product_eol` is required and persisted; route-specific
  factor families are **PARTIAL**.
* **14** — the allocation basis is **required and persisted**; the franchise operating model
  is **DEFERRED**, and `NOT_APPLICABLE` is **NOT IMPLEMENTED** as a first-class
  organizational state (§24).
* **15** — the attribution basis is **required and persisted**. **PCAF-aligned methods are
  NOT implemented**; only equity-share attribution is supported. `DEFERRED` stands.

## 10. Methodology per category

`domain/scope3_contracts.py` declares, per category, which methodologies may be claimed:
`supplier_specific`, `average_data`, `spend_based`, `distance_based`, `asset_specific`,
`survey_based`, `extrapolated`, `proxy_data`, `industry_average`, `modelled`. A request
naming a methodology outside its category's tuple is refused before anything is written.

**Persisted on the result row today:** the *calculation* methodology
(`calculation_snapshots.methodology`, e.g. `direct_multiply`), the specificity
classification (`data_quality`), and — for estimates — the *estimation* method on
`estimation_records.estimation_method`. The category's methodology tuple is a
contract-level declaration, not a per-row column. Recorded as a limitation in §24 rather
than presented as complete.

## 11. Input / source types per category

| Cat | Declared source channels (P17-PRODUCT-01) | Required inputs enforced today |
|---|---|---|
| 1 | supplier invoice, PO, procurement export, ERP, supplier PCF, EPD, statement, CSV/XLSX, manual | activity, quantity, unit + a source reference |
| 2 | asset invoice, ERP, fixed-asset register, supplier PCF/EPD, procurement | + `capitalisation_declared` |
| 3 | existing Scope 1/2 activity | + `source_snapshot_id` (DC-02) |
| 4 | freight invoice, manifest, carrier statement, logistics CSV, ERP | + `transport_boundary='upstream'` |
| 5 | waste invoice, transfer note, supplier statement, weight record | + `material`, `treatment_route`, `waste_origin='operations'` |
| 6 | Booking.com / Agoda / Expedia / Concur / Navan / Expensify / Trainline / Uber / Bolt / receipts / CSV / manual | + `trip_purpose` |
| 7 | employee survey, HR data, travel survey, commuting app, parking records, manual | + an estimation basis (method + inputs/assumptions) |
| 8 | lease contracts, property records, utility bills, landlord data | + `consolidation_approach` |
| 9 | customer / logistics data | + `transport_boundary='downstream'` |
| 10 | customer/supplier questionnaire, processing statement, production data, industry average | + an estimation basis |
| 11 | product, units sold, lifetime, use profile, geography | + `use_phase_assumption` |
| 12 | sold-product composition + end-of-life route | + `material`, `treatment_route`, `waste_origin='sold_product_eol'` |
| 13 | lease / lessee data | + `consolidation_approach` |
| 14 | franchise entity, location, operational period, Scope 1/2 activity | + `allocation_basis` |
| 15 | portfolio, investee emissions, PCAF-style data, annual reports | + `attribution_basis` |

The channels above are canonical-target declarations: a CSV/XLSX/PDF channel reaches the
same canonical activity through the existing extraction/mapping pipeline. This task added
**no** external API integration (per the task contract) and **no** channel-specific code
path.


## 12. Evidence / provenance

Every result in the round-trip answers the product specification's evidence questions from
**stored rows**, not from a log line:

| Question | Where it is stored | Asserted |
|---|---|---|
| What did we receive? | `calculation_snapshots.source_file` / `source_page`, `source_item_id`, `source_line_item_id`, `source_snapshot_id` | yes (cat 1, cat 3) |
| What did we extract / interpret? | `calculation_snapshots.activity`, `activity_type`, `quantity`, `quantity_unit` | yes |
| Which scope / category? | `scope`, `scope2_method` / `scope3_category`, `energy_type` | yes, all 15 categories + Scope 2 |
| Which methodology? | `methodology` (+ `data_quality`, `estimation_records.estimation_method`) | yes |
| Which factor, and which vintage? | `factor_id`, `factor_kind`, `factor_set`, `factor_source`, `reporting_year` | yes |
| Which organisation owns the data? | `organization_id` on snapshot **and** log | yes |
| Who performed the action? | `performed_by`, `performed_by_organization_id` | yes |
| Who were they acting for? | `acting_for_organization_id` (snapshot **and** log) | yes |
| What calculation snapshot resulted? | `emissions_logs.snapshot_id` → `calculation_snapshots.id` | yes |
| Which supplier? | `emissions_logs.supplier_id` | yes |
| Immutability of the result | `content_hash`, `algorithm_version` | yes |

The round-trip also asserts that the snapshot and the log carry **identical** dimension
values, because the engine writes both from one `AccountingDimensions` object.

## 13. Data-quality model

**Implemented vocabulary (5 values, enforced by a database CHECK):** `primary_measured`,
`primary_supplier`, `secondary_estimated`, `spend_based_estimated`, `modelled`. Three are
estimates and therefore require a persisted estimation record (`is_estimated()` is the
single predicate the system uses).

**Deliberately NOT implemented, and not faked:** the product specification lists eight
labels (`PRIMARY`, `SUPPLIER_SPECIFIC`, `ACTIVITY_BASED`, `AVERAGE_DATA`, `SPEND_BASED`,
`ESTIMATED`, `MANUAL`, `UNRESOLVED`). The mapping is intentional and documented:
`PRIMARY → primary_measured`, `SUPPLIER_SPECIFIC → primary_supplier`,
`AVERAGE_DATA → secondary_estimated`, `SPEND_BASED → spend_based_estimated`, `MODELLED`
covers modelled. `ACTIVITY_BASED`, `MANUAL` and `UNRESOLVED` **have no member**, and
`PRIMARY` is not distinguishable from `UNRESOLVED`.

Extending the vocabulary is a **schema change** (the CHECK constraint plus the
`DATA_QUALITY_VALUES` contract), which this task's no-migration boundary and the "do not
invent business policy" rule put out of scope. It is recorded as **DEFERRED with a stated
reason**, not silently aliased: a spend-based figure is not presented as activity-based
data.

## 14. Estimation model

* `estimation_records` is the **single** estimation table (P17-H); this task created no
  second one.
* A record cannot exist without a real calculation: the FK is
  `calculation_snapshot_id → calculation_snapshots(id) ON DELETE CASCADE`, and the route
  writes the record only **after** the calculation has been persisted.
* `EstimationRecordsRepository.record()` is idempotent per calculation
  (`WHERE NOT EXISTS` plus the `uq_estimation_records_snapshot` index), so a retry cannot
  double the evidence.
* The database refuses an unsubstantiated record:
  `estimation_records_substantiated_check` requires `inputs` or `assumptions` to be a
  non-empty object. **VERIFIED** on real PostgreSQL — the round-trip writes one record,
  asserts every stored field, then proves the second write returns `None` and the row count
  stays 1.
* Categories 7, 11, 12 and 14 adopt an estimation pathway (`_ESTIMATION_CATEGORIES`), and
  any category whose data quality is an estimate also requires a record. A missing record is
  **refused** (`EstimationRecordRequiredError`) with **nothing persisted** — asserted.

## 15. Manual-review model

Manual review is a **controlled success path**, not an error:

* When a required input or boundary declaration is absent the service returns
  `CLARIFICATION_REQUIRED` with the exact `missing_fields`, the category, the contract's
  `refusal_reason` and its `manual_review_conditions` guidance. The HTTP layer maps this to
  **422** with that structured payload.
* **Nothing is persisted** for a clarification. The round-trip asserts the snapshot count is
  unchanged after five clarification cases (cat 4, 5, 8 and 13 boundaries; cat 3 source
  snapshot).
* The service never invents a value to make a request succeed, and a *present but invalid*
  input (a contradictory boundary, an unsupported methodology, an estimation pathway
  claiming measured data) raises rather than being softened into a clarification.


## 16. Supplier attribution

**Owned by the canonical path, not duplicated.** `emissions_logs.supplier_id` is the
pre-existing P12 column and `_ANALYTICS_DIMENSION_EXPRESSIONS["supplier"]` the existing
grouping expression; no second supplier system was built.

This task closes the gap between *claim* and *storage*:

1. The route resolves the claimed supplier **server-side** through
   `resolve_authorized_supplier(repos, supplier_id, data_owner)`.
2. A supplier that does not exist **or belongs to another organization** is refused with
   **422** — deliberately indistinguishable, so the response confirms nothing about another
   tenant's master data. This matters because `emissions_logs.supplier_id` has **no foreign
   key**: without the check an arbitrary id would be stored.
3. The validated id is carried by `CalculationRequest.from_match_result(..., supplier_id=)`
   into `emissions_logs.supplier_id`. `None` writes NULL — an unresolved supplier is never
   invented.
4. **VERIFIED** on real PostgreSQL for Scope 3 (round-trip) and Scope 2 (four energy types),
   including the "no supplier claimed → NULL" case.

**Not implemented:** the `transaction_provider` vs `underlying_supplier` distinction
(P17-PRODUCT-01 §5 — Booking.com vs Hotel ABC). The model holds one supplier reference per
result. Recorded as **DEFERRED** (§24); it is a genuine part of the business-travel contract
and has not been faked by treating the booking platform as the emissions-producing supplier.

## 17. Boundary / double-counting controls

**Domain layer (reused unchanged, never re-implemented):** `assert_boundary_complete()` in
`domain/scope3.py` implements DC-02, DC-04, DC-05 and DC-07 as one fail-closed guard — a
missing declaration refuses, and a contradictory declaration refuses (`upstream` on
category 9, `downstream` on category 4, and likewise for waste origins).

**Storage layer — this is what makes the control structural rather than advisory.** All
verified against real PostgreSQL:

| Invariant | Object | Verified |
|---|---|---|
| Cat 4 `upstream` / cat 9 `downstream` | `calc_snapshots_transport_boundary_scope_check` (`NOT VALID`, enforced on new rows) | **VERIFIED** — a direct INSERT of a cat-5 row with `transport_boundary='upstream'` raises `CheckViolationError` |
| Cat 5 `operations` / cat 12 `sold_product_eol` | `calc_snapshots_waste_origin_scope_check` | enforced |
| Scope 2 requires a method; Scope 3 a category | `calc_snapshots_scope2_method_required`, `calc_snapshots_scope3_category_required` (+ the same on `emissions_logs`) | **VERIFIED** — this is the constraint that exposed defect 7.1 |
| `energy_type` only on Scope 2 | `calc_snapshots_energy_type_scope_check` | enforced |
| Cat 3 derived from one Scope 1/2 source **once** | partial unique index `uq_calc_snapshots_cat3_source (source_snapshot_id) WHERE scope3_category = 3` | **VERIFIED** — a second derivation from the same source raises `UniqueViolationError`; the count stays 1 |
| One result per idempotency key | unique index `uq_calc_snapshots_request_id` | **VERIFIED** — a repeated request raises `UniqueViolationError`; the canonical lookup resolves the first |
| An instrument quantity cannot be claimed twice | `assert_allocation_within_quantity` (DC-09) + `p17_instrument_over_allocated()` + `instrument_allocations_unique` | **VERIFIED** — the detector reports `false` at full allocation; the guard refuses the next unit |

**Cat 1 ↔ Cat 2** is controlled by the required `capitalisation_declared` discriminator;
**DC-07 (Cat 8 ↔ Cat 13)** by the required consolidation approach. Neither value is
recoverable from the stored result row alone (§24).

## 18. Database changes

**None. No migration was added, altered, applied or reverted**, and no table, column, index,
policy or grant was created by this task anywhere. Every structure the round-trip depends on
already existed in these committed migrations:

`20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`,
`20261011000000_p17c_contractual_instruments_and_allocations.sql`,
`20261012000000_p17d_scope3_category_taxonomy.sql`,
`20261013000000_p17h_estimation_and_assumption_records.sql`.

The change is in the **application's use of** an existing schema: the canonical INSERT now
supplies the dimension columns the schema already required of a new row.

## 19. API changes

| Endpoint | Change | Type |
|---|---|---|
| `POST /api/v3/scope3/calculate` | `supplier_id` is now **resolved and authorized** (422 if not available to the caller's organization) and persisted | behaviour fix; no schema change; response shape unchanged |
| `POST /api/v3/scope2/calculate` | New optional `supplier_id` field, resolved and authorized the same way | additive request field |

No route was added, renamed or removed. No response field was removed. The deterministic
UUID5 `request_id` derivation is untouched. `estimation_record_id` remains as added by
IMPLEMENT-08.


## 20. Real PostgreSQL verification

**Result: PASS** — with the exact target and scope stated, so the claim cannot be read as
broader than it is.

### 20.1 Target and its F-046-1 status

| Item | Value |
|---|---|
| Target used | `ct_p17_09_verify_20260925` — a **disposable clone** created for this task from `ct_p17_migcheck_20260925` (`CREATE DATABASE … TEMPLATE …`) |
| Why that name | F-046-1 permits exactly a `ct_*` disposable clone or `carbontally_test` |
| Why not `carbontally_test` | It is still at a **pre-P17** schema (§20.4) and was **not modified** |
| Destructive setup acknowledged | the shared `pool` fixture runs `TRUNCATE … RESTART IDENTITY CASCADE`; the clone is disposable by construction |
| Production / demo / investor / QA contacted | **NO** |

### 20.2 Schema probe — every structure `present`

`backend/tests/integration/verify_p17_08_scope3_persistence_schema.py` was upgraded to
certify any F-046-1-permitted target and to check the full P17 structure. Output:

```
TARGET postgresql://***@127.0.0.1:54426/ct_p17_09_verify_20260925
CONNECTED database= ct_p17_09_verify_20260925
TABLE calculation_snapshots / emissions_logs / estimation_records /
      contractual_instruments / instrument_allocations / scope3_categories /
      suppliers                                             = present (all)
COL calculation_snapshots.{scope2_method, scope3_category, energy_type, data_quality,
      facility_id, transport_boundary, waste_origin, source_snapshot_id,
      performed_by_organization_id, acting_for_organization_id} = present (all)
COL emissions_logs.{supplier_id, scope2_method, scope3_category, energy_type,
      data_quality, facility_id, transport_boundary, waste_origin, source_snapshot_id,
      performed_by_organization_id, acting_for_organization_id} = present (all)
COL estimation_records.{organization_id, calculation_snapshot_id, estimation_method,
      inputs, assumptions, scope3_category, acting_for_organization_id,
      actor_organization_id}                                = present (all)
FUNCTION p17_instrument_over_allocated                        = present
RLS scope3_categories / contractual_instruments / instrument_allocations /
      estimation_records                                      = enabled (all four)
```

**Negative control:** pointed at `carbontally_demo_local` the same probe refuses before
checking anything —

```
CONNECTED database= carbontally_demo_local
REFUSING: carbontally_demo_local is not an F-046-1-permitted target
          (expected 'carbontally_test' or a 'ct_' disposable clone)   [exit 3]
```

### 20.3 The round-trip

`backend/tests/integration/test_p17_09_scope2_scope3_persistence_runtime.py` — real
services, real engine, real repositories, real schema:

```
34 passed   (tests=34 failures=0 errors=0 skipped=0)
```

It proves, against stored rows: all **15** category identities; one normal activity/factor
category; one estimation category; one supplier-linked category; four boundary-controlled
cases; Scope 2 location-based (all four energy types) and market-based with a persisted
instrument + allocation; estimation records including idempotency; supplier attribution;
snapshot/log dimension agreement; cat-3 derivation uniqueness; request-id idempotency; and
tenant isolation between two organisations.

### 20.4 Before/after, and the state of `carbontally_test`

* Same clone, same tests, with this task's source change **stashed**: **24 failed / 34**.
  The round-trip is therefore what discovered and what proves the fix (AGENTS.md §74).
* `carbontally_test` (read-only probe, unchanged): `estimation_records`,
  `contractual_instruments`, `instrument_allocations`, `scope3_categories` and every P17
  dimension column are **MISSING**. It also lacks
  `supabase_migrations.schema_migrations` — it was bootstrapped by restore, not by
  migration. Its P17 upgrade is an **infra** action, not an implementation one (§24).


## 21. Test results

| Suite | Scope | Result |
|---|---|---|
| `tests/integration/test_p17_09_scope2_scope3_persistence_runtime.py` | real PostgreSQL, new | **34 passed, 0 failed** |
| `tests/integration/test_emissions_logs.py` | real PostgreSQL, repository | **4 passed, 0 failed** (was 4 failing on any P17 database) |
| `tests/integration/verify_p17_08_scope3_persistence_schema.py` | read-only probe | all `present`, RLS enabled ×4, negative control refuses |
| `tests/unit -k p17` | unit | **430 passed, 0 failed** |
| `tests/unit/{api,services,domain,engines,data}` | wider unit | **3382 passed, 8 skipped, 9 failed** (§23) |

## 22. P17-05 / 06 / 07 / 08 regression

Re-run in full after the change. The `-k p17` selection covers P17-02 through P17-08 and
reports **430 passed, 0 failed** — the same count as the IMPLEMENT-08 baseline:

| Suite | Files | Result |
|---|---|---|
| P17-05 Scope 2 calculation | `tests/unit/services/test_p17_05_scope2_calculation.py` | passed |
| P17-06 instrument repository + market API | `tests/unit/data/test_p17_06_*.py`, `tests/unit/api/test_p17_06_*.py` | passed |
| P17-07 unified Scope 3 framework | `tests/unit/services/test_p17_07_scope3_framework.py`, `tests/unit/domain/test_p17_scope3*.py` | passed |
| P17-08 Scope 3 API + estimation persistence | `tests/unit/api/test_p17_08_scope3_api.py` | passed |

No P17 assertion was weakened to accommodate the behaviour change. The seven sink-double
edits (§6) only add the new optional keyword argument. The P17-08 supplier test, which
asserts `request.supplier_id is None` by default, still holds — the field is unset unless a
caller supplies it.

## 23. Wider-suite results

`tests/unit/{api,services,domain,engines,data}`: **3399 tests → 3382 passed, 8 skipped,
9 failed**, and the nine failures are **exactly** the set already recorded as pre-existing
in the IMPLEMENT-08 report:

| Failing suite | Count | Assessment |
|---|---|---|
| `engines/test_extraction_suggestions.py` | 3 | Pre-existing invoice-suggestion engine, unrelated to Scope 2/3 |
| `api/test_review_sla_surfaces.py` | 3 | Pre-existing route-registration assertions |
| `data/test_d17_provider_ownership_migration_revision.py`, `data/test_i1_insight_migration.py`, `data/test_i2_insight_authorization_contracts.py` | 3 | Pre-existing by construction: they assert a migration is the *latest*, which the P17-01…08 migrations legitimately superseded. **This task adds no migration**, so it cannot have caused them |

**No new failure was introduced.** The wider *integration* suite (`tests/integration/*`) was
also run against the clone and is not green there; the cause is the target, not the change —
demonstrated by running a representative case against both databases:

```
test_v3_rls_behavior.py::…::test_org_member_sees_own_customer_factors
  carbontally_test (pre-P17)  → PASS
  ct_p17_09_verify (clone)    → FAIL (assert 0 == 1)
```

The clone is a migration-check lab (243 public policies vs 198) rather than a
restore-from-dump database, so suites that depend on its seed/role posture behave
differently. Those failures are classified **environment, not regression**, and were not
fixed here.


## 24. Known limitations

1. **`test_emissions_logs.py` was 4-failing on any P17 database** before this task (it
   inserted `scope='Scope 2'` logs without a method). Fixed as part of the interface work
   (§6); it is the reason the new `create(accounting_dimensions=…)` API exists.
2. **Reporting read projection.** `scope3_category`, `scope2_method`, `energy_type` and
   `data_quality` are persisted on `calculation_snapshots` / `emissions_logs` and returned by
   the calculation APIs, but are **not exposed by the analytics/Insight read projection**
   (`_ANALYTICS_DIMENSION_EXPRESSIONS`). Category-level *reporting* therefore still requires
   reading the calculation rows rather than the analytics surface. Carried forward from
   IMPLEMENT-08; still **DEFERRED**.
3. **Category methodology is not a per-row column** (§10): the persisted `methodology`
   records `direct_multiply`; the specificity lives in `data_quality` and, for estimates, in
   `estimation_method`. Reporting cannot state "average-data methodology" from the result row
   alone.
4. **`consolidation_approach` is not persisted** on the result (§17). DC-07 gating is
   enforced, but the decision is not recoverable from the stored row.
5. **Data-quality vocabulary is 5 values, not 8** (§13). Extending it is a schema change.
6. **`transaction_provider` / `underlying_supplier` is not modelled** (§16).
7. **No `NOT_APPLICABLE` organizational state.** The contract requires an organization to be
   able to distinguish `CALCULATED`, `ESTIMATED`, `UNDER_REVIEW`, `NO_DATA_YET`,
   `NOT_APPLICABLE` and `EXCLUDED_WITH_REASON`. That model is **NOT IMPLEMENTED**: there is
   no first-class per-organization category-applicability surface, so the requirement that
   `NOT_IMPLEMENTED` never appears as an organization-facing state is **not yet satisfied**.
   Recorded as **DEFERRED** (PO decision required), not papered over.
8. **`carbontally_test` is still pre-P17**, so the repository's default integration target
   cannot run the P17 suites without a `ct_*` clone (§20.4).
9. **The wider integration suite is not green on the verification clone** (§23). That
   suite's own target should be restored from a current dump before it is treated as
   authoritative.
10. **No migration was applied anywhere.** This task ran zero migrations (AGENTS.md §66,
    §70) and made no schema change.
11. **Scope 2 UI and the whole investor-demo UX surface are untouched** — deliberately, per
    the task's no-UI scope-creep rule. Nothing in this report should be read as an
    investor-facing acceptance claim.

## 25. Deferred items

| # | Item | Status | Why |
|---|---|---|---|
| 1 | Analytics read projection for `scope3_category` / `scope2_method` / `energy_type` / `data_quality` | **DEFERRED** | touches the shared analytics allow-list and its callers; a pure follow-on with no schema dependency |
| 2 | 8-value data-quality vocabulary | **DEFERRED** | requires a migration (CHECK constraint) — outside this task's no-schema-change boundary |
| 3 | `transaction_provider` vs `underlying_supplier` | **DEFERRED** | requires a new dimension (migration) plus a PO decision on how the pair is reported |
| 4 | Business-trip journey / grouping layer (Cat 6) | **DEFERRED** | requires a grouping entity; the legs are already independently auditable |
| 5 | Per-category methodology as a persisted column | **DEFERRED** | `methodology` is already the engine methodology; a second column is a schema decision |
| 6 | `consolidation_approach` persistence | **DEFERRED** | schema change |
| 7 | `NOT_APPLICABLE` / `NO_DATA_YET` / `EXCLUDED_WITH_REASON` states | **DEFERRED** | needs a PO decision on the applicability model |
| 8 | Cat 15 PCAF-aligned methods | **DEFERRED** | investment methodology is a PO/domain decision; equity-share attribution is what is supported |
| 9 | Cat 2 fixed-asset-register ingestion and automatic capitalisation boundary | **DEFERRED** | the explicit declaration is the current control |
| 10 | Deterministic per-category investor corpus | **PARTIAL** | the round-trip provides one deterministic canonical fixture per category at *service* level; a persisted, reportable investor corpus is not built |
| 11 | Repair the 9 pre-existing unit failures | **DEFERRED** | out of scope; reported with root cause (§23) |
| 12 | Restore/migrate `carbontally_test`; repair the wider integration suite's target | **DEFERRED (infra)** | not an implementation action, and mutating that database was not authorised here |

## 26. Production-contact statement

**No production, live, demo, investor, QA or customer environment was contacted, read,
modified, migrated, truncated, seeded or reset.** Every write in this task ran against one
disposable `ct_*` clone created for the purpose. The only reads of any other database were
the schema probe of `carbontally_test` — which was **not modified** — and of
`carbontally_demo_local`, which was the probe's **negative control** and was refused before
any structure was inspected. The F-046-1 guard was never bypassed; no RLS policy was
disabled; no service-role shortcut was used to hide a tenant or security problem.


## 27. Final verdict

> ### `P17_IMPLEMENTATION_PARTIAL`

**What genuinely advanced, and is VERIFIED:**

* The **real-PostgreSQL blocker left open by IMPLEMENT-08 is resolved**, and resolving it
  exposed a **blocking defect** that no unit or API test could see: the canonical write path
  could not persist a Scope 2 or Scope 3 result at all. That is fixed and re-verified
  (§7.1, §20).
* A second real defect — an accepted-and-discarded supplier claim, with a cross-tenant
  attribution hole — is fixed with server-side authorization (§7.2).
* All **15** Scope 3 categories and both Scope 2 methods are **VERIFIED** to persist their
  full accounting identity on real PostgreSQL, with boundary controls, estimation evidence,
  idempotency and tenant isolation asserted on stored rows (§8, §9, §19–§21).
* **No regression:** 430 P17 unit tests pass; the wider unit suite shows exactly the same
  9 pre-existing failures (§22, §23).

**Why the verdict is PARTIAL, not COMPLETE.** The task's §42 acceptance gate requires more
than persistence, and several of its clauses are **materially incomplete**:

1. **An organization-facing applicability model** (`CALCULATED` / `ESTIMATED` /
   `UNDER_REVIEW` / `NO_DATA_YET` / `NOT_APPLICABLE` / `EXCLUDED_WITH_REASON`) is **NOT
   IMPLEMENTED** (§24 item 7). `NOT_IMPLEMENTED` therefore still reaches the product as an
   architecture status — the exact thing the gate forbids. **PO decision required.**
2. **Per-category methodology is not persisted on the result** (§24 item 3), so
   category-level reporting cannot state the methodology used.
3. **Category-level reporting identity is not exposed by the analytics projection**
   (§24 item 2).
4. **The investor-corpus-readiness clause is only PARTIALLY met**: deterministic canonical
   fixtures exist per category at service level, but no persisted, reportable per-category
   corpus exists.
5. The **8-value data-quality model**, **transaction-provider modelling**, the **Cat 6
   journey layer**, **Cat 15 PCAF** and the **Cat 2 capitalisation control** remain
   **DEFERRED** (§25), each with a stated reason.

None of those was converted into a green tick, and no architecture or product status was
edited to obtain a PASS.

**Requirement index** (task-contract §43 → this report): 1 §1 · 2 §2 · 3 §3 · 4 §4 ·
5 §5 · 6 §6 · 7 §8 · 8 §9 · 9 §10 · 10 §11 · 11 §12 · 12 §13 · 13 §14 · 14 §15 · 15 §16 ·
16 §17 · 17 §18 · 18 §19 · 19 §20 · 20 §21 · 21 §22 · 22 §23 · 23 §24 · 24 §25 ·
25 §26 · 26 §27.

**IMPLEMENTED ≠ TESTED ≠ VERIFIED ≠ ACCEPTED.** Nothing here is an acceptance verdict: no
investor, PO or customer acceptance is claimed, and the platform is **not** described as
production-ready or investor-ready.

**INSPECT → VERIFY → IMPLEMENT → TEST → REPORT.**

