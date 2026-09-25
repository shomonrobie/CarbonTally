# CT-PO-P17-IMPLEMENT-10 — Product Contract: Applicability, Category Reporting, Data Quality, Provider/Supplier Attribution

**Task ID:** `P17-IMPLEMENT-10-20260925-PRODUCT-CONTRACT-APPLICABILITY-REPORTING-SUPPLIER`
**Repository:** CarbonTally `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Timestamp:** 2025-09-25 (local session)
**Author:** Cline — *implementation agent*. **Not** an independent verifier.
**Supersedes nothing.** This report sits alongside (and does not amend) the P17-09 report.

---

## 1. Task ID

`P17-IMPLEMENT-10-20260925-PRODUCT-CONTRACT-APPLICABILITY-REPORTING-SUPPLIER`

## 2. Starting SHA

```
4a342c5687b99264f32a4dfb0b4d142fd1bd0bcd
```

**Verified before any change.** This matches the required starting baseline
exactly (`4a342c5687b99264f32a4dfb0b4d142fd1bd0bcd`), so the task proceeded. The
SHA is the P17-09 documentation-only commit `docs(p17): record IMPLEMENT-09 commit
SHAs`.

## 3. Ending SHA

```
PENDING — recorded in §24 at the end of this report
```

The literal ending SHA is embedded by the immediately following
documentation-only commit, exactly as P17-09 did.

## 4. Working-tree state

### 4.1 At task start

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| HEAD | `4a342c5687b99264f32a4dfb0b4d142fd1bd0bcd` (matches the required baseline) |
| Tracked modifications | `.gitignore` — **pre-existing, not touched by this task** |
| Untracked | 18 pre-existing files (`.costrict/`, stray `8`/`=`/`costrict-*.txt`, `docs/ChatGPT/*`, several P17 governance documents including `P17-PRODUCT-01`, two `CarbonTally_Insight_*` documents) — **not touched by this task** |

### 4.2 At task end

Changed (tracked):

```
backend/api/v3_scope2.py
backend/api/v3_scope3.py
backend/core/exceptions.py
backend/data/emissions_logs.py
backend/domain/accounting_dimensions.py
backend/domain/data_quality.py
backend/domain/insight_query.py
backend/domain/scope3_contracts.py
backend/engines/calculation.py
backend/services/scope2_calculation.py
backend/services/scope3_calculation.py
backend/tests/integration/verify_p17_08_scope3_persistence_schema.py
backend/tests/unit/data/test_p17_migrations.py
backend/tests/unit/data/test_p8_insight_analytics_sql.py
backend/tests/unit/domain/test_p17_cams.py
```

Created (new):

```
supabase/migrations/20261014000000_p17_10_product_contract_reporting_dimensions.sql
backend/tests/unit/domain/test_p17_10_product_contract.py
backend/tests/unit/services/test_p17_10_scope3_methodology.py
backend/tests/integration/test_p17_10_contract_dimensions_runtime.py
docs/architecture/CT-PO-P17-IMPLEMENT-10-PRODUCT-CONTRACT-APPLICABILITY-REPORTING-SUPPLIER-20250925.md
```

`.gitignore` remains modified exactly as it was at the baseline; no pre-existing
untracked file was modified, removed or absorbed.

## 5. Authoritative documents read

| Document | How read |
|---|---|
| `docs/architecture/P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product Specification.md` | **Read in full** (all 1,374 lines, in three ranges) |
| `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | Targeted searches (`applicab`, `data_quality`, `transaction_provider`, P17 workstream letters, endpoint table) |
| `docs/architecture/CT-PO-P17-ARCH-06-RECONCILIATION-20250925.md` | **Read in full** (481 lines) |
| `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | Targeted reads (§17–§24 capability/UX/security/no-duplicate-model sections) + searches |
| `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | Targeted searches (`applicab`, `data quality`, `provider`, `methodolog`) |
| `docs/architecture/CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md` | Targeted searches |
| `docs/architecture/artifacts/p17_*.json`, `p17_schema_delta_20250925.md` | Searched for the applicability vocabulary and status semantics |
| `docs/architecture/CT-PO-P17-IMPLEMENT-09-COMPLETE-SCOPE2-SCOPE3-ALL15-20250925.md` | Read the data-quality, methodology, supplier-attribution and deferred-items sections |
| `AGENTS.md` | Read |
| Current implementation: `domain/accounting_dimensions.py`, `domain/data_quality.py`, `domain/scope3_contracts.py`, `domain/scope3.py`, `domain/insight_query.py`, `domain/calculation.py`, `engines/calculation.py`, `data/emissions_logs.py`, `services/scope2_calculation.py`, `services/scope3_calculation.py`, `api/v3_scope2.py`, `api/v3_scope3.py`, `api/accounting_context_auth.py`, `supabase/migrations/20261010000000_p17a_*.sql`, `20261013000000_p17h_*.sql` | Read |
| Migration inventory | `ls supabase/migrations` (latest at baseline: `20261013000000_p17h_estimation_and_assumption_records.sql`) |

## 6. Product-contract decisions discovered

This section is the substance of the task: the authoritative contract was
established **before** any code changed, and one objective could not be grounded.

### 6.1 The applicability / organization-status model is NOT in the authoritative contract — STOPPED

Task §4 requires implementing "the authoritative organization/category
applicability lifecycle from P17-PRODUCT-01", and lists `CALCULATED`,
`ESTIMATED`, `UNDER_REVIEW`, `NO_DATA_YET`, `NOT_APPLICABLE` and
`EXCLUDED_WITH_REASON`, while explicitly instructing: *"Do not assume these are
database enum values until the Product Specification confirms the intended
model"* and *"If the specification and architecture documents disagree: DO NOT
silently choose one. Record the contradiction and stop the affected
implementation decision for PO review."*

**Evidence (no inference):**

| Search | Scope | Result |
|---|---|---|
| `grep -n -i 'applicab'` | `P17-PRODUCT-01` (all 1,374 lines) | **ZERO matches.** The word "applicab*" does not appear in the authoritative product specification at all. |
| `grep -rn 'NO_DATA_YET'` | entire repository (`*.md`, `*.py`, `*.sql`, `*.json`, `*.ts`, `*.tsx`; `.venv`/`node_modules` excluded) | 3 matches, **all in `CT-PO-P17-IMPLEMENT-09-...md`** — i.e. only in the P17-09 report's own prose |
| `grep -rn 'EXCLUDED_WITH_REASON'` | entire repository | 3 matches, all in the same P17-09 report |
| `grep -rn 'UNDER_REVIEW'` / `NOT_APPLICABLE` | `docs/architecture` | No hit in `P17-PRODUCT-01`, `ARCH-01`, `ARCH-05`, `ARCH-06`, `POST-ARCH-DECISIONS`, the PO-CAMS decision, or the P14 investor-acceptance contract. The only `NOT_APPLICABLE` hits are in **Phase 8 *disclosure* documents**, where the vocabulary is a different domain entirely (`requirement_class`, `carbontally_capability`, and `disclosure_applicability_assessments` with `APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`) — regulatory *disclosure requirement* applicability, not Scope 2/3 category applicability. |
| `grep -rno 'NOT_APPLICABLE\|NO_DATA_YET\|EXCLUDED_WITH_REASON\|UNDER_REVIEW'` | `docs/architecture/artifacts/*.json` | No matches at all. The status vocabularies present are architecture/documentation statuses (`NOT_IMPLEMENTED`, `PARTIAL`, `END_TO_END_VERIFIED`), which are *governance* states about capability maturity, not runtime product states. |

**Conclusion.** The six-value applicability vocabulary is **not part of the
authoritative product contract**. It appears only in the P17-IMPLEMENT-09
implementation report — which sits near the bottom of the AGENTS.md §2
source-of-truth hierarchy and, per AGENTS.md §80, is *historical unless
independently reverified*. Implementing it would have been inventing product
policy (AGENTS.md §62), so per task §0.8, §1, §4 and the STOP CONDITIONS the
**applicability portion of this task is STOPPED and recorded as
PO DECISION REQUIRED**, not implemented and not faked (§6.2).


### 6.2 What the authoritative documents DO say about organization-facing state

Two authoritative, but different, concepts exist — neither is the six-value model:

1. **PO-CAMS §19 "Organization Capability Management UX"** defines an
   organization-level capability model with ON/OFF controls
   (`Customer Carbon Accounting`, `Scope 1/2/3 Customer Entry`, `Customer
   Evidence Upload`, `Customer Supplier Data`, `Customer Editing`, `Customer
   Review`, `Staff Review Required`, `Staff Approval Required`), and the PO
   states the list is **not frozen**: *"The final control list must be reconciled
   with the actual P17 architecture and existing authorization system."*
2. **PO-CAMS §18** requires capability-awareness: *"If Scope 3 customer entry is
   disabled, the customer should not receive a misleading empty Scope 3
   management interface."*

So the authoritative organization-facing requirement is a **capability** model
whose enumeration the PO explicitly defers. Implementing an enumeration would be
a PO decision, and no `organization_capabilit*` / `organization_settings` /
feature-flag mechanism exists in the current schema or code to extend (searched
`supabase/migrations` and `backend/`). Recorded as **PO DECISION REQUIRED**.

### 6.3 The authoritative contracts that WERE implemented

| Objective (task §3) | Authoritative source | Verdict |
|---|---|---|
| 1. Organization-facing applicability/status model | none found | **STOPPED — PO DECISION REQUIRED** (§6.1) |
| 2. Category-level reporting/read projections | `P17-PRODUCT-01` **§29 "Reporting model"** (must expose Scope 1, Scope 2 location/market, Scope 3 Cat 1–15, plus Data quality, Methodology, Manual-review % and Unresolved %) — normative, not hedged | **IMPLEMENTED** |
| 3. Data-quality vocabulary reconciliation | `P17-PRODUCT-01` **§7** (8 classifications, introduced "For example") + **§29/§30** (normative reporting buckets) | **IMPLEMENTED (widened, non-destructively)** |
| 4. `transaction_provider` vs `underlying_supplier` | `P17-PRODUCT-01` **§5 "Transaction provider vs actual supplier"** (explicit, normative) + §4 canonical-activity field list | **IMPLEMENTED** |
| 5. Persisted/reportable category metadata | `P17-PRODUCT-01` **§25** ("Which methodology?"), **§29** ("Methodology"), **§34** ("category-specific methodology" is a must-have) | **IMPLEMENTED** |

#### 6.3.1 §5 — the provider/supplier contract

The specification's §4 canonical activity model lists `supplier_id`,
`supplier_name` and `transaction_provider` as separate fields; §5 then fixes the
semantics:

```
Booking.com
      ↓
Hotel ABC

Store:
  transaction_provider = Booking.com
  underlying_supplier  = Hotel ABC
  activity_type        = hotel_accommodation
```

with `Trainline → SNCB/CFL`, `Uber → taxi/private-hire activity`,
`Expedia → airline`, and the stated purpose: *"This prevents CarbonTally from
confusing where someone purchased something with what generated the emissions."*

**Naming reconciliation (documented, not a contradiction).** §5 names the second
field `underlying_supplier`, while §4's field list names the supplier fields
`supplier_id` + `supplier_name`. The semantic is unambiguous and consistent —
the *emissions-generating* party — so the existing `emissions_logs.supplier_id`
is the underlying supplier and `transaction_provider` is the new, separate
field. No second supplier concept was created. `transaction_provider` is
deliberately a **text name, not a supplier foreign key**: §4 gives it no `_id`
suffix, and a booking platform has no reason to exist in the reporting tenant's
own `suppliers` master data. This is also why it cannot be used to forge a
cross-tenant reference — there is no foreign key to forge.


#### 6.3.2 §7 — the data-quality contract, and what P17-09 got wrong

`P17-PRODUCT-01` §7 lists:

```
PRIMARY   SUPPLIER_SPECIFIC   ACTIVITY_BASED   AVERAGE_DATA
SPEND_BASED   ESTIMATED   MANUAL   UNRESOLVED
```

introduced by the words **"For example:"** and followed by *"And ideally a more
granular data-quality score later."*

So the list is **illustrative**, not a closed enumeration — P17-09's phrasing
("the Product Specification apparently calls for 8") overstated it. **However**,
the same specification states the reporting requirement normatively and without
hedging:

* §29 requires the reporting layer to expose, in addition to the scope/category
  breakdowns: *Data quality · Methodology · Primary vs secondary · Estimated % ·
  **Manual-review %** · **Unresolved %** · Evidence coverage*; and
* §30's investor dashboard is specified as `Primary data · Activity based ·
  Average data · Spend based · Estimated · Manual review`, with the explicit rule
  *"Those percentages would be derived from actual data, not demo decoration."*

Four of those classifications (`ACTIVITY_BASED`, `ESTIMATED`, `MANUAL`,
`UNRESOLVED`) had **no member** in the P17-A vocabulary, so the §29/§30 reporting
requirement was unsatisfiable. The correct action was therefore to make all eight
classifications expressible — which is what §8.2 implements — while being precise
here that §7's list is illustrative and that the *driver* is §29/§30.

#### 6.3.3 §6/§29/§34 — the methodology contract, and a real defect

P17-PRODUCT-01 §4 lists `methodology` in the canonical activity model; §6 defines
a category-specific methodology hierarchy; §25 asks "Which methodology?"; §29
requires the reporting layer to expose Methodology; §34 lists "category-specific
methodology" as a must-have.

Forensics (§7.3) found that the implementation **could not persist eight of the

## 7. Existing-state forensics

### 7.1 One engine, one pathway (preserved)

The canonical path was identified and reused without duplication:
`CalculationRequest.from_match_result` → `CalculationEngine.calculate` →
`CalculationSink.save_snapshot` / `create` → `save`, through
`data.emissions_logs.EmissionsLogsRepository`. `domain/accounting_dimensions.py`
is the validated carrier of the P17 dimension columns; its docstring already
declared that the P17 vocabularies are deliberately duplicated to fail fast in
front of the database CHECKs.

### 7.2 The data-quality vocabulary was duplicated — and had drifted

`domain/data_quality.py` owned the vocabulary, but
`domain/accounting_dimensions.py` held a **second literal copy**
(`DATA_QUALITY_VALUES`). This is the drift hazard AGENTS.md §23/§4 warns about,
and it bit during implementation: widening the vocabulary in the owning module
left the copy narrow, so a database-accepted classification was refused in the
domain. Fixed by deriving the copy (§8.2). The migration-text test still asserts
the P17-A file's five values, which remains a truthful statement about that
historical file.

### 7.3 The methodology defect (confirmed empirically, not asserted)

A read-only probe (no database, no writes) established the exact
contract-versus-engine vocabulary overlap:

```
CalculationMethodology (engine boundary):
    ['area_based', 'direct_multiply', 'distance_based', 'mass_balance', 'spend_based']

Scope 3 contract methods across all 15 categories:
    ['asset_specific', 'average_data', 'distance_based', 'extrapolated',
     'industry_average', 'modelled', 'proxy_data', 'spend_based',
     'supplier_specific', 'survey_based']

overlap (accepted by the engine): ['distance_based', 'spend_based']

contract-valid methods the engine CANNOT persist:
    ['asset_specific', 'average_data', 'extrapolated', 'industry_average',
     'modelled', 'proxy_data', 'supplier_specific', 'survey_based']
```

Each was refused with `ValidationFailedError: unknown calculation methodology
'supplier_specific'` (and likewise for the other seven). **Cause:**
`services/scope3_calculation.py` validated the requested method against the
category contract and then passed that same product string to
`CalculationRequest.methodology`, a field whose normaliser only accepts
`CalculationMethodology` values.

### 7.4 Surfaces inspected for the reporting requirement

The existing analytics read projection is
`EmissionsLogsRepository._ANALYTICS_DIMENSION_EXPRESSIONS` (allowlisted SQL
expressions) gated by `domain.insight_query.AGGREGATION_DIMENSIONS`, consumed by
`services.insight_tools` through `repos.logs.aggregate_groups(...)`. It exposed
`scope`, `month`, `year`, `activity`, `supplier`, `facility`, `asset` — and none
of `scope3_category`, `scope2_method`, `scope3_method`, `energy_type`,
`data_quality` or `transaction_provider`. This is the projection that was
extended; no second result table or analytics store was created.

### 7.5 Database state

`carbontally_test` remains **stale/pre-P17 and was not touched** (task §0.5).
Verification used a disposable clone created from the P17-09 clone
(`CREATE DATABASE ... TEMPLATE ct_p17_09_verify_20260925`), which is
F-046-1-permitted (`ct_*`).

### 7.6 Implementation plan formed before any code changed

1. Reconcile the contract (§6) and stop the ungrounded portion.
2. Additive migration for the two new dimensions + the widened data-quality
   vocabulary.
3. Domain: widened vocabulary + §29/§30 reporting projection; the two new
   dimensions with fail-closed validation; one source of truth per vocabulary.
4. Fix the methodology-persistence boundary (product method → `scope3_method`;
   engine arithmetic label derived deterministically).
5. Persistence: write both new columns in the SAME INSERT as the row; extend the

## 8. Applicability implementation

**NOT IMPLEMENTED — STOPPED.** See §6.1 for the evidence. No applicability
lifecycle, status enum, table, column or service was created, and no
`NOT_APPLICABLE` / `NO_DATA_YET` / `EXCLUDED_WITH_REASON` / `UNDER_REVIEW`
concept exists in the product as a result of this task.

This is a deliberate, rule-mandated outcome, not an omission: task §0.8 ("Do not
alter architecture/product status documents merely to make implementation appear
complete"), task §4 ("Do not assume these are database enum values until the
Product Specification confirms the intended model"), task §1 ("DO NOT GUESS THE
PRODUCT CONTRACT"), and the STOP CONDITIONS ("authoritative product contract
contradiction") all require the affected work to stop and be documented rather
than invented.

**Existing lifecycle preserved unchanged.** The
`DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED → REPORTABLE`
accounting lifecycle was not modified, and no second lifecycle was introduced.
The pre-existing *disclosure* applicability model
(`disclosure_applicability_assessments`) was neither reused nor altered — it is a
different domain.

## 9. Data-quality vocabulary decision

**DECISION: widen additively to nine persisted classifications so that all eight
classifications named in P17-PRODUCT-01 §7 are expressible, and add the §29/§30
reporting projection.** No existing value was removed and no stored row was
invalidated.

Rationale, stated precisely:

* §7's list is introduced with **"For example"**, so it is illustrative rather
  than a closed enumeration. P17-09's claim that the specification "calls for 8"
  is therefore imprecise, and this report says so rather than repeating it.
* §29 and §30 nevertheless state the reporting requirement **normatively**: the
  report must distinguish "Manual-review %" and "Unresolved %", and the investor
  dashboard is specified as `Primary data · Activity based · Average data · Spend
  based · Estimated · Manual review` — *"derived from actual data, not demo
  decoration"*. Four of those buckets had no expressible classification.
* Therefore the four missing product classifications were added
  (`activity_based`, `estimated`, `manual`, `unresolved`) while the five P17-A
  values were preserved verbatim. `modelled` is retained deliberately: §7's list
  is illustrative, category 15's contract method vocabulary already uses
  `modelled`, and removing it would invalidate stored rows.

### 9.1 The widened vocabulary

| Value | Classification | Estimate? | §29/§30 reporting bucket |
|---|---|---|---|
| `primary_measured` | metered/measured at source | no | Primary data |
| `primary_supplier` | declared by the supplier/utility | no | Primary data |
| `secondary_estimated` | estimated from average/secondary data | **yes** | Average data |
| `spend_based_estimated` | derived from spend | **yes** | Spend based |
| `modelled` | produced by a model | **yes** | Estimated |
| `activity_based` | **new** — derived from an activity-based factor | no | Activity based |
| `estimated` | **new** — a labelled estimate with a persisted basis | **yes** | Estimated |
| `manual` | **new** — established by controlled human review | no | Manual review |
| `unresolved` | **new** — not determined; carried as unknown | no | Unresolved |

### 9.2 What was deliberately NOT collapsed

Data quality remains **distinct** from applicability, lifecycle status,
estimation status and reportability, as task §5 requires. The additions preserve
the discriminations that matter:

* `activity_based` is **NOT** an estimate. It is activity data (the §6 hierarchy
  places "activity-based factor" *above* "average-data methodology"), so treating
  it as an estimate would have imposed a T-INV-12 obligation the contract does not.
* `manual` describes **who** established the value, not how precisely — it is not
  an estimate.
* `unresolved` is the explicit admission that **no value was established**, which
  is categorically different from a low-quality estimate.
* `estimated` **is** an estimate by definition and therefore **does** require a
  persisted estimation record (T-INV-12), asserted on real PostgreSQL (§16).

The estimate predicate is therefore now
`{secondary_estimated, spend_based_estimated, modelled, estimated}` — four values,
and the single predicate the rest of the system uses.

### 9.3 The §29/§30 reporting projection (pure, deterministic, total)

Added to `domain/data_quality.py`:

* `PRODUCT_DATA_QUALITY_BUCKETS` — the ordered §30 bucket list plus an explicit
  `UNCLASSIFIED` bucket;
* `reporting_bucket(value)` — a **total** projection of every persisted value
  onto exactly one bucket. `None` and any unrecognised value map to
  `UNCLASSIFIED` rather than being folded into a quality bucket or silently
  dropped, so a report can never overstate the quality of its data;
* `quality_mix(counts)` — aggregates persisted classification counts into the
  §29/§30 mix. Percentages are computed **only** when the total is non-zero; with
  no results every percentage is `None` rather than `0`, because "no data" and
  "0% of the data" are different statements. No numeric uncertainty band is
  produced anywhere — that remains the explicitly deferred fabricated-precision
  risk the module already refused.

`modelled` is mapped to the `Estimated` bucket (documented and asserted): it is
an estimate produced by a model, and §30 has no bucket of its own for it.

   allowlisted read projection.

## 10. Methodology persistence decision

**DECISION: persist the category methodology as a first-class controlled dimension
(`scope3_method`), and fix the boundary defect that made it unp persistable.**
P17-PRODUCT-01 §29/§34 require it; task §8 permits it explicitly ("implement it
explicitly; use controlled vocabulary / methodology identity").

### 10.1 Why a new column rather than widening the engine vocabulary

The existing `calculation_snapshots.methodology` column records the **engine
arithmetic label** (`direct_multiply`, `distance_based`, `spend_based`,
`area_based`, `mass_balance`) and is consumed by existing reporting and tests.
The category method is a **different fact** — the accounting method that was
selected. Conflating them in one column would have re-defined existing values.

The Scope 2 path already separates exactly these two facts (`scope2_method`
carries `LOCATION_BASED`/`MARKET_BASED` while `methodology` stays
`direct_multiply`), so `scope3_method` is the symmetric extension of an
established P17 pattern, not a new concept.

### 10.2 The fix

* `AccountingDimensions.scope3_method` — new, optional, Scope-3-only.
* Domain validation is **fail-closed**: the value must be in the frozen contract
  union (`SCOPE3_METHODS`, derived from the fifteen contracts so it cannot drift)
  or a `Scope3MethodNotSupportedError` (422) is raised; the service additionally
  validates against the **category's own** contract vocabulary; and the database
  enforces both the vocabulary and the Scope-3-only rule.
* **No silent methodology fallback.** A stated method is *stored in full* in
  `scope3_method`. The engine arithmetic label is then derived by an explicit,
  named, documented and tested projection
  (`engines.calculation.engine_methodology_for`): `spend_based` and
  `distance_based` keep their own arithmetic label because they genuinely change
  the arithmetic; every other product method (`supplier_specific`,
  `average_data`, `extrapolated`, `survey_based`, `asset_specific`,
  `industry_average`, `modelled`, `proxy_data`) really is `quantity × factor`, so
  its honest arithmetic label is `direct_multiply`. The distinction those eight
  methods carry is preserved in full on `scope3_method` and in the estimation
  record — it is not inferred, and nothing is guessed after the fact.
* An **absent** method stays `NULL`. It is never defaulted to the first entry of
  the contract's list, asserted by test at both unit and real-PG level.

### 10.3 No migration was needed for the engine label

`calculation_snapshots.methodology` already existed and is unchanged; this
decision adds a column, it does not alter an existing one.

## 11. Provider vs supplier implementation

**IMPLEMENTED** per P17-PRODUCT-01 §5.

| Aspect | Implementation |
|---|---|
| Carrier | `AccountingDimensions.transaction_provider` → `calculation_snapshots.transaction_provider` + `emissions_logs.transaction_provider` |
| Type | `text`, nullable, no default — **a NAME, not a suppliers FK** (§6.3.1) |
| Validation | fail-closed in the domain: non-blank when supplied, ≤ 200 characters, no control characters; the database repeats the shape guard |
| Underlying supplier | unchanged: `emissions_logs.supplier_id`, resolved server-side by `resolve_authorized_supplier` (P17-09) |
| Never equated | the provider is **never** copied into `supplier_id` and is never derived **from** it — asserted by unit and real-PG tests |
| Unresolved supplier | stays `NULL` while the provider is still recorded — never guessed |
| Wrong-tenant | the provider is not an id, so there is no cross-tenant reference to forge; a *supplier* id in the payload is still resolved and refused per P17-09 |
| Acting-for | carried unchanged; owner remains `organization_id` |
| Original source preserved | `transaction_provider` is stored as supplied; nothing about the source document is rewritten |

Contract scenarios explicitly tested: provider only; provider **and** underlying
supplier; unresolved underlying supplier with a known provider; known supplier
with **no** provider; consultant acting-for client; direct customer; product
method + provider + supplier together.

6. API/services: carry the new facts; resolve nothing from the payload.
7. Tests: unit + real PostgreSQL on a disposable clone; negative control.

ten methods the fifteen category contracts permit.** That is a genuine
product-contract defect, not a nice-to-have, and it is the defect this task fixes.


## 12. Reporting/read projection implementation

**IMPLEMENTED by extending the existing projection — no duplicate result table.**

* **Source of truth:** the canonical `emissions_logs` rows, which mirror the
  authoritative `calculation_snapshots` dimensions. Nothing was copied, and no
  analytics store or second result table was created (task §7, AGENTS.md §4/§21).
* **Refresh semantics:** there is **no projection to refresh**. The read path
  aggregates the canonical rows at query time, so it can never be stale and there
  is no in-flight state to reconcile. This is why "stale/missing projection
  behaviour" (task §7) is structurally impossible rather than merely untested.
* **Where:** `data/emissions_logs.py::_ANALYTICS_DIMENSION_EXPRESSIONS` (the
  allowlisted SQL expressions) and
  `domain/insight_query.py::AGGREGATION_DIMENSIONS` (the closed caller-facing
  vocabulary), which a test asserts are **exactly equal** so they cannot drift.
* **Dimensions added:** `scope3_category`, `scope3_method`, `scope2_method`,
  `energy_type`, `data_quality`, `transaction_provider`.
* **Existing dimensions preserved:** `scope`, `month`, `year`, `activity`,
  `supplier`, `facility`, `asset`.
* **Tenant isolation:** every query remains `organization_id`-scoped and bounded;
  no dimension changes that. A real-PG test asserts a second tenant sees empty
  aggregations for all four new dimensions while the owner sees the rows.
* **Reportability cannot be bypassed:** the projection is a **read** over
  `emissions_logs`; the P16-R5 reportability columns on `calculation_snapshots`
  are untouched and a test asserts a fresh result is not reportable merely because
  it exists. A read projection cannot make anything reportable.
* **Sensitivity:** every added expression is a fixed SQL literal with no
  statement separator, placeholder or line break, and an unknown dimension is
  still refused — the pre-existing assertion now covers the widened set.

### 12.1 What the projection now exposes (§29 mapping)

| §29/§30 requirement | Read path |
|---|---|
| Scope 1 | group by `scope` (existing) |
| Scope 2 location-based / market-based | group by `scope2_method` (**new**), values `LOCATION_BASED`/`MARKET_BASED` |
| Scope 2 energy type | group by `energy_type` (**new**) |
| Scope 3 category 1–15 | group by `scope3_category` (**new**) |
| Methodology | `scope3_method` (**new**) on the log; `methodology` on the snapshot read surface |
| Data quality + Estimated % / Manual-review % / Unresolved % | group by `data_quality` (**new**) → `quality_mix()` (§29/§30 buckets) |
| Supplier / provider | group by `supplier` (existing) and `transaction_provider` (**new**) |
| Evidence / provenance | existing `list_group_snapshots` provenance path, unchanged |
| Organization ownership / acting-for | existing `organization_id` scoping + the P17 acting-for columns |

`_SNAPSHOT_COLUMNS` was also extended with `scope2_method`, `scope3_category`,
`scope3_method`, `energy_type`, `data_quality` and `transaction_provider`, so a
provenance read can name the method, the category and the purchase channel.

## 13. Scope 2 impact

**No regression.** The P17-09 verified Scope 2 behaviour is intact and re-verified
on the P17-10 clone (§16):

* electricity / heat / steam / cooling energy types, location-based and
  market-based, contractual-instrument eligibility and allocation,
  retired-instrument rejection, wrong-scope factor rejection, tenant isolation.

Changes are additive only:

* `api/v3_scope2.py` and `services/scope2_calculation.py` gained
  `transaction_provider` (carried unchanged into the dimensions).
* The response now also reports `data_quality_bucket`, `supplier_id` and
  `transaction_provider`, and the read projection can group by `scope2_method`
  and `energy_type` (a real-PG test asserts both).
* `scope3_method` is explicitly **refused** on a Scope 2 result by the domain,
  by a `NOT VALID` database CHECK (enforced on new rows), and by a real-PG test.

## 14. Scope 3 impact

**No regression, plus a defect fixed.** All fifteen categories retain the real-PG
persistence identity P17-09 established, and each is re-driven through the real
service in the P17-10 unit suite. In addition:

* every one of the ten contract methods can now be stored on a real row — the
  regression proof for §7.3;
* the new `data_quality` classifications persist;
* the boundary/estimation rules are untouched: estimation-pathway categories
  still refuse a measured classification and still require a persisted estimation
  record (asserted for every category).

**No architecture status was upgraded.** The category statuses reported by the
contract (`NOT_IMPLEMENTED`, `DEFERRED`, `PARTIAL`) are unchanged, and
`assert_calculable` still refuses `NOT_IMPLEMENTED`/`DEFERRED` categories. A
category that could not record its method can now do so; that is a persistence
fix, not a maturity upgrade.

**Category-specific deeper work remains deferred** (task §11): the Category 6
journey layer, Category 15 PCAF depth, Category 2 capitalisation control beyond
the existing required discriminator. None was in scope here because none is
required by the *cross-cutting* reporting contract this task closes.


## 15. Tenant/security verification

| Scenario | Result | Evidence |
|---|---|---|
| A. Direct customer writes/reads own data | **PASS** — owner sees its rows | real-PG `test_cross_tenant_read_projection_cannot_leak_and_stays_isolated` (owner count = 1) |
| B. Consultant acts for authorized client | **PASS** — owner, `performed_by` and `acting_for` stored as three distinct facts | real-PG `test_consultant_acting_for_client_records_both_facts` |
| C. Consultant cannot access unauthorized client | **PASS** — a second tenant's aggregations are empty for every new dimension, and its snapshot count is 0 | real-PG |
| D. Cross-tenant supplier/provider id rejected | **PASS** — `transaction_provider` is a name, so there is no id to forge; a forged `supplier_id` is still refused by P17-09's `resolve_authorized_supplier` (unchanged, re-exercised) | unit + real-PG |
| E. Cross-tenant evidence rejected | **PASS** — unchanged; the new dimensions add no evidence path | — |
| F. Forged organization id rejected | **PASS** — ownership is taken from the resolved context; the payload organization is never trusted (unchanged) | — |
| G. Read projection cannot leak another organization | **PASS** — every `aggregate_groups` call is `organization_id`-scoped; a second tenant receives empty results for `scope3_category`, `scope3_method`, `data_quality`, `transaction_provider` | real-PG |
| Vocabulary enforced by the database, not only the domain | **PASS** — a raw `UPDATE ... scope3_method='invented_method'` raises `CheckViolationError` on both tables | real-PG `test_database_refuses_a_method_outside_the_vocabulary` |
| A blank provider is refused by the database | **PASS** — `CheckViolationError` | real-PG `test_database_refuses_a_blank_transaction_provider` |
| `scope3_method` on a Scope 2 row is refused | **PASS** — `CheckViolationError` (NOT VALID: history exempt, new writes enforced) | real-PG `test_database_refuses_scope3_method_on_a_scope2_row` |

No payload value can override a server-resolved ownership decision: the new
`transaction_provider` is a bounded-length name with no foreign key, and
`scope3_method` is validated against a frozen vocabulary the caller cannot widen.

## 16. Real PostgreSQL verification

**Target:** `ct_p17_10_verify_20260925` — a **disposable clone** created with
`CREATE DATABASE ct_p17_10_verify_20260925 TEMPLATE ct_p17_09_verify_20260925`.
Its name contains none of the protected markers (`qa`, `demo`, `investor`,
`prod`, `live`) and it is not a prohibited main database, so it is
**F-046-1-permitted**. `carbontally_test` was **not** touched.

**Migration applied:** `20261014000000_p17_10_product_contract_reporting_dimensions.sql`
with `ON_ERROR_STOP=1`, exit code 0. **Re-run: exit code 0, zero errors —
idempotent.**

| Verification (task §13) | Result |
|---|---|
| 1. Schema exists | **PASS** — 4/4 new columns present, 0 MISSING |
| 2. RLS exists/enabled | **PASS** — `relrowsecurity` true on both tables; new columns inherit the posture (no policy changed) |
| 3. Normal Scope 2 row | **PASS** — location-based electricity with energy type, supplier and provider |
| 4. Market Scope 2 row | **PASS** — re-verified by the P17-09 suite on this clone (38/38) |
| 5. Normal Scope 3 row | **PASS** |
| 6. Estimated Scope 3 row | **PASS** — estimation record still required and still written |
| 7. `NOT_APPLICABLE` / `NO_DATA_YET` | **NOT REPRESENTED** — deliberately: no authoritative model exists (§6.1) |
| 8. Supplier-linked row | **PASS** — `supplier_id` stored |
| 9. Provider + supplier row | **PASS** — both stored, distinct, neither derived from the other |
| 10. Unresolved supplier row | **PASS** — supplier `NULL`, provider recorded |
| 11. Consultant acting-for row | **PASS** — owner / performed-by / acting-for three distinct facts |
| 12. Category-level reporting projection | **PASS** — grouped by `scope3_category`, `scope3_method`, `data_quality`, `transaction_provider` |
| 13. Cross-tenant read rejection | **PASS** |
| 14. Cross-tenant write rejection | **PASS** (database CHECK refusals above) |
| 15. Idempotency | **PASS** — a repeat raises `UniqueViolationError` on `uq_calc_snapshots_request_id`; snapshot and log counts stay 1/1 |
| 16. Lifecycle/reportability protection | **PASS** — a fresh result is not `REPORTABLE`/`APPROVED`; `invalidated_reason`/`superseded_by_snapshot_id` are `NULL` |

**Round-trip proof (input → calculation → canonical persistence → read
projection):** `test_category_reporting_projection_reads_the_new_dimensions`
drives two categories with two distinct methods through the real service, then
reads them back through the real organization-scoped projection and asserts the
group keys (`{"1","4"}`), the two methods, the data quality **and** the aggregated
tonnage (100 kg × 2.5 = 250.000000 kg CO₂e each).

### 16.1 Schema probe

`tests/integration/verify_p17_08_scope3_persistence_schema.py` was extended to
certify the P17-10 objects. On the clone it reports **62
`present`/`enabled`/`allowed` lines and 0 `MISSING`**, including all four new
columns, all eight new constraints, and all nine data-quality values present in
the widened CHECK. **Negative control:** pointed at `carbontally_demo_local` it
**REFUSES** with the F-046-1 message before inspecting anything.



## 17. Migration status

**ONE additive migration required and created:**
`supabase/migrations/20261014000000_p17_10_product_contract_reporting_dimensions.sql`
(192 lines).

| Discipline | Status |
|---|---|
| Additive only | ✅ 4 `ADD COLUMN IF NOT EXISTS` plus constraint/index work; no `DROP TABLE`, `DROP COLUMN`, `DELETE FROM`, `TRUNCATE` or `ALTER COLUMN` |
| Idempotent | ✅ `IF NOT EXISTS` / `DROP CONSTRAINT IF EXISTS`; re-run exit 0, zero errors |
| New columns nullable, no default | ✅ asserted via `information_schema` |
| No backfill | ✅ no `UPDATE` of any accounting table |
| Non-destructive vocabulary change | ✅ `data_quality` CHECK **widened** to a strict superset (5 → 9); the migration test asserts every P17-A value is still allowed |
| New-write-only rules `NOT VALID` | ✅ `scope3_method` scope guards; historical rows exempt |
| RLS | ✅ no table created, **no policy altered**, no RLS weakened |
| Migration ordering | ✅ `20261014000000` follows `20261013000000` (the baseline latest); no historical timestamp reused |
| Applied to a disposable clone | ✅ `ct_p17_10_verify_20260925` (F-046-1) |
| Applied to production | **NO** — never contacted |
| Applied to `carbontally_test` | **NO** — deliberately left stale |

## 18. Tests run

| Suite | Result |
|---|---|
| P17-10 unit — domain (`tests/unit/domain/test_p17_10_product_contract.py`) | **pass** (incl. 15 parametrised per-category method cases) |
| P17-10 unit — service, real service + engine + contracts (`tests/unit/services/test_p17_10_scope3_methodology.py`) | **23 passed** |
| P17-10 real PostgreSQL (`tests/integration/test_p17_10_contract_dimensions_runtime.py`) | **30 passed** |
| P17-09 real PostgreSQL + `test_emissions_logs` (regression, same clone) | **38 passed** |
| P17 unit selection (`pytest tests/unit -k p17`) | **488 tests, 0 failures, 0 errors, 0 skipped** |
| Wider unit (`tests/unit/{api,services,domain,engines,data}`) | **3457 tests, 9 failures, 0 errors, 8 skipped** |
| Schema probe on the clone | **62 present/enabled/allowed, 0 MISSING** |
| Probe negative control at `carbontally_demo_local` | **REFUSED (F-046-1)** — as required |

### 18.1 Negative control on the fix (the tests are load-bearing)

The methodology projection in `services/scope3_calculation.py` was temporarily
reverted to the pre-fix expression
(`methodology=request.methodology or "direct_multiply"`), and the new suites were
re-run **without changing any test**:

| Run | Result with the fix **reverted** |
|---|---|
| P17-10 real PostgreSQL | **17 of 30 FAILED** |
| P17-10 unit (service) | **17 of 23 FAILED** |

The fix was then restored and both suites returned to green. This proves the new
tests detect the defect rather than merely describing the current code.

### 18.2 Honest caveat on the vocabulary tests

Two pre-existing assertions in `tests/unit/domain/test_p17_cams.py`
(`test_data_quality_vocabulary_is_exactly_five_values`,
`test_exactly_three_classifications_are_estimates`) asserted the *old* five-value
vocabulary and therefore had to change — the contract changed, not the standard
of proof. They were rewritten with **equal strictness** (exact tuple/set
equality) against the corrected vocabulary and renamed accordingly, and the new
migration test proves the database CHECK was **widened, not narrowed**, so no
stored row was invalidated. No assertion was deleted, skipped, xfailed or
weakened, and nothing was relaxed to obtain GREEN.

The pre-existing `test_p17_07` assertion that a `distance_based` request persists
`methodology == "distance_based"` still holds exactly, because that method keeps
its own engine arithmetic label (§10.2). The eight methods that previously could
not persist at all are now covered by the new unit and real-PG tests instead of
by an assertion that the refusal was acceptable.

## 19. Baseline failures vs new failures

| Baseline (P17-09) | This task (P17-10) | New failures |
|---|---|---|
| 9 unit failures in `{api,services,domain,engines,data}` | **the same 9** | **ZERO** |
| 8 skipped | 8 skipped | — |
| 3382 passed (~) | 3457 tests (the new tests added) | — |

The nine, with root cause, exactly as P17-09 recorded them:

| File | Count | Classification |
|---|---|---|
| `engines/test_extraction_suggestions.py` | 3 | Pre-existing invoice-suggestion engine; unrelated to Scope 2/3 or to any file this task touched |
| `api/test_review_sla_surfaces.py` | 3 | Pre-existing route-registration assertions; this task touches no route registration |
| `data/test_d17_provider_ownership_migration_revision.py`, `data/test_i1_insight_migration.py`, `data/test_i2_insight_authorization_contracts.py` | 3 | **Pre-existing by construction** — they assert a migration is the *latest* and a fixed migration *count*, which the P17 migration series legitimately superseded |

**Independently proven pre-existing (not assumed):** the three
migration-inventory tests were re-run with only the P17-10 migration temporarily
moved out of the inventory — **all three still failed**, so this task's migration
did not cause them. The other six touch code paths (`routes/`, extraction
suggestions) this task never modified.

They were **not fixed**: task §14 instructs that unrelated failures not be fixed
unless necessary, and they are outside this task's scope. They are reported
accurately rather than hidden.

## 20. P17-05/06/07/08/09 regression

| Suite | Result |
|---|---|
| P17-05 Scope 2 calculation | **pass** (inside the 488) |
| P17-06 contractual-instrument repository / Scope 2 market API | **pass** |
| P17-07 Scope 3 framework, all fifteen categories | **pass** — including the pre-existing assertions that an unsupported methodology is refused and that `distance_based` persists as `distance_based` |
| P17-08 Scope 3 API persistence | **pass** |
| P17-09 real-PG Scope 2 + Scope 3 round-trip | **38/38 pass on the P17-10 clone** (its own 34 plus `test_emissions_logs`' 4) |
| P17 migrations contract suite | **pass**, extended with the P17-10 assertions |

No P17-05…P17-09 behaviour regressed.

## 21. Remaining limitations

Stated plainly; nothing here is implied to be solved.

1. **Organization-facing applicability model — NOT IMPLEMENTED, PO DECISION
   REQUIRED.** No `NOT_APPLICABLE` / `NO_DATA_YET` / `EXCLUDED_WITH_REASON` /
   `UNDER_REVIEW` concept exists, because none is in the authoritative contract
   (§6.1). The honest organisational concept the PO has defined is the §19 ON/OFF
   capability list, whose enumeration the PO explicitly defers.
2. **Organization accounting capabilities — NOT IMPLEMENTED.** PO-CAMS §18
   requires capability-awareness; no capability/settings/feature-flag mechanism
   exists to extend, and the control list is not frozen. PO DECISION REQUIRED.
3. **`NOT_IMPLEMENTED` still reaches the product.** Category architecture
   statuses remain reported verbatim and `assert_calculable` still refuses those
   categories — correct, but there is still no *customer-facing* way to express
   "this category does not apply to us", which is what item 1 would provide.
4. **The data-quality store holds nine values** — the eight §7 names plus the
   retained P17-A `modelled`. Deliberate (§9), but it means the store is a
   superset of the product bucket vocabulary; the projection in §9.3 maps them.
5. **No numeric data-quality score or uncertainty band.** Deliberately absent —
   the platform does not measure it.
6. **`transaction_provider` is free text.** Bounded, control-character-checked and
   non-blank, but there is no controlled provider catalogue: the specification
   names providers as examples, not as an enumeration.
7. **Category-specific depth remains deferred** (task §11): the Category 6
   journey layer, Category 15 PCAF data-quality depth, Category 2 capitalisation
   control beyond the required discriminator, and provider *integrations*
   (`P17-PRODUCT-01` §34 explicitly excludes them from this stage).
8. **`emissions_logs.supplier_id` still has no foreign key** (pre-existing,
   P17-09). Server-side authorization remains the only guard, deliberately.
9. **`carbontally_test` is still stale/pre-P17**, so the wider *integration*
   suite is not authoritative; local integration verification is on a disposable
   `ct_*` clone only. Infrastructure item, unchanged by this task.
10. **Not independently verified.** Every claim here is this agent's own evidence.
11. **The `modelled` → `Estimated` bucket mapping** is a judgement made here and
    documented; if the PO wants `modelled` reported separately, that is a PO
    decision (§9.3).
12. **No UI.** This task is server-side only. §29's reporting requirement is
    satisfiable *from* the read layer, but no page renders it (task §17: no UI
    scope creep).


## 22. Investor-readiness implications

**This task does not make CarbonTally investor-ready, and does not claim to**
(task §16). What it changes is the *product-contract foundation*:

* the platform can now **record and report which accounting methodology** each of
  the fifteen Scope 3 categories used — previously impossible for eight of the ten
  contract methods, a first-order credibility gap for any Scope 3 claim;
* the **purchase channel is no longer confusable with the emissions-generating
  supplier** (`Booking.com` vs the hotel), a real-world Scope 3 accuracy
  requirement and a common competitor talking point;
* the **data-quality mix required by §29/§30 can be derived from stored data**
  ("Primary data / Activity based / Average data / Spend based / Estimated /
  Manual review"), which both the §29 reporting requirement and the §30 investor
  dashboard depend on;
* the **category-level reporting projection** now exists over the canonical rows.

What remains before any stronger claim: the organization-facing applicability and
capability models (PO decisions), a persisted investor corpus/demo journey (a
separate acceptance task per task §16), a current P17-migrated `carbontally_test`
so the wider integration suite is meaningful, and independent verification.

## 23. Production-contact statement

**Production was NEVER contacted.** Specifically:

* no production database was contacted, read, modified, migrated, seeded,
  truncated or written to;
* no production API, production Supabase project, production customer
  organisation or production storage was contacted;
* **`carbontally_test` was not modified** (task §0.5) — it remains stale/pre-P17;
* the investor demo database (`carbontally_demo_local`) was **not** modified, and
  the schema probe **refused** it when pointed at it as a negative control;
* the only database written to was the disposable clone
  `ct_p17_10_verify_20260925`, which is F-046-1-permitted;
* no migration was executed against any non-disposable target;
* nothing was pushed to any remote.

## 24. Exact commits

Created in logical order; **not pushed**.

| Order | Subject | Contents |
|---|---|---|
| 1 | `feat(p17-10): persist category methodology, purchase channel and the widened data-quality vocabulary` | migration, domain, engine, persistence, services, API, tests |
| 2 | `docs(p17): record IMPLEMENT-10 report (PARTIAL — methodology/provider/data-quality/reporting landed; applicability stopped for a PO decision)` | this report |
| 3 | `docs(p17): record IMPLEMENT-10 commit SHAs` | the literal SHAs in §3 |

Starting SHA: `4a342c5687b99264f32a4dfb0b4d142fd1bd0bcd`
Ending SHA: recorded in the third commit and in §3.

*Note: `.gitignore` is a pre-existing modification and is deliberately NOT
committed, exactly as P17-09 recorded.*

## 25. Final truthful verdict

```
P17_IMPLEMENTATION_PARTIAL
```

**Why not COMPLETE.** One of the five stated objectives could not be grounded in
the authoritative product contract and was therefore **stopped rather than
guessed**: the organization-facing applicability model (task §4). The
organization capability model that *is* authoritative is explicitly not frozen by
the PO. Both are recorded as **PO DECISION REQUIRED** with evidence. Per task §20,
`COMPLETE` must not be selected merely because tests are green.

**Why not BLOCKED.** The four objectives that *are* grounded in the authoritative
contract were implemented, persisted and verified on real PostgreSQL, and none of
the task's STOP CONDITIONS (unsafe database target, production target, tenant
isolation regression, lifecycle/reportability regression, inability to safely
verify persistence) was triggered.

### 25.1 Status vocabulary — what is and is not true

| Status | Applies to |
|---|---|
| **IMPLEMENTED** | `scope3_method`; `transaction_provider`; the widened data-quality vocabulary; the §29/§30 bucket projection; the extended category-level read projection; the methodology-persistence defect fix |
| **PERSISTED** | all of the above, on real rows in `calculation_snapshots` and `emissions_logs` |
| **E2E VERIFIED** | the new dimensions through `input → calculation → canonical persistence → read projection`, on real PostgreSQL |
| **REAL-PG VERIFIED** | 30/30 P17-10 + 38/38 P17-09/`emissions_logs` on `ct_p17_10_verify_20260925`; schema probe 62/62 with 0 MISSING; migration idempotent |
| **NOT IMPLEMENTED** | the applicability lifecycle; the organization capability model |
| **PO DECISION REQUIRED** | the applicability model; the capability control list; whether `modelled` reports separately |
| **DEFERRED** | Category 6 journey layer; Category 15 PCAF depth; Category 2 capitalisation control beyond the discriminator; provider integrations; numeric data-quality score |
| **NOT INDEPENDENTLY VERIFIED** | everything in this report |
| **NOT PRODUCTION READY** | as a consequence of the above |

`NOT_APPLICABLE` and `NO_DATA_YET` are, by design, **not** product statuses after
this task — their absence is the finding, not an omission.

**END OF REPORT.**

