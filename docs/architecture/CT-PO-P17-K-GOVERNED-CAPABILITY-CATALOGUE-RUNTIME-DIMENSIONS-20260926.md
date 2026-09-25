# P17-K — Governed Capability Catalogue + P17 Runtime Dimensions

**Task ID:** `P17-K-20260926-GOVERNED-CAPABILITY-CATALOGUE-RUNTIME-DIMENSIONS`
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Date:** 2026-09-26
**Authority:** `CT-PO-P17-DECISION-03` §18.1 Tier 2 item 7, §20.3 (the P17-K task definition), §5.3 (`M-1`), §11.1/§11.2, §10.3 (`SC-4`), §18.2 (`F-1`/`F-2`), §18.3 (`AG-1`…`AG-8`), §19.4 rows 8–9.

---

## 1. Task identity

### 1.1 What this task is

`CT-PO-P17-DECISION-03` froze the P17 capability contract and recorded, as an
explicit non-claim, that **"the governed requirement catalogue populated —
NOT DONE — 0 rows (`PR-2`)"**. It then named this task as the next step:

> **`P17-K` — "Governed capability catalogue + P17 runtime dimensions"**
> … *make the frozen contract backed at runtime for the 15 categories (and the
> Scope 1/2 requirements), without inventing any model.*

P17-K therefore does two things, and only two:

1. **Applies the five already-authorised P17 migrations to a disposable clone**
   and verifies the runtime dimensions they declare (`PR-1`).
2. **Authors the governed `disclosure_requirement_versions` catalogue** so every
   Scope 1 / Scope 2 / Scope 3 requirement carries a persisted
   `carbontally_capability` value **exactly as `M-1` maps it** (`PR-2`).

### 1.2 What this task is not

Explicitly out of scope, per `CT-PO-P17-DECISION-03 §20.3`:

| Not in P17-K | Rule |
|---|---|
| any Scope 3 category **applicability** model | `F-1`, PO-3 |
| any new capability **vocabulary**, enum, status column or coverage field | `F-2`, PO-7 |
| any **surface UI** (customer or investor) | §18.1 Tier 3 |
| any **marketing, sales, deck, FAQ or website** change | `CM-4`, §14 |
| any **commercial / pricing / packaging** commitment | §15 |
| any change to `P17-DECISION-01`/`-02` decisions, RLS, API routes or UI | §18.4 |

### 1.3 Verdict language used in this report

`IMPLEMENTED` ≠ `TESTED` ≠ `VERIFIED` ≠ `ACCEPTED` (`AGENTS.md §73`). Each verdict
below says exactly which one it is, and §23 states the task verdict.

---

## 2. Baseline

| Item | Value |
|---|---|
| Expected starting SHA | `28ff2c0` |
| **Actual starting SHA** | **`28ff2c0bd9b66ca747ca0d0ef1abc6585b7da7bd`** — **MATCH** |
| Branch | `p8-release-reconciled` (1 commit ahead of `origin` — not pushed) |
| Pre-existing working-tree state | ` M .gitignore` plus untracked `.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, `docs/architecture/P17-PRODUCT-01 … .md` — **preserved untouched**, not staged, not absorbed |
| Demo database | `carbontally_demo_local` @ `127.0.0.1:54426` — **read-only use only** |
| Disposable clone created for this task | **`ct_p17k_20260926`** (`ct_` prefix ⇒ permitted under `F-046-1`) |
| Production | **never contacted** |

---

## 3. Authoritative sources

### 3.1 Contract and decision authority

| Source | What it fixed here |
|---|---|
| `CT-PO-P17-DECISION-03-…-20250926.md` | the `M-1` mapping; the 4/6/3/2 rollup; `SC-4`; `F-1`/`F-2`; `AG-1`…`AG-8`; `§19.4` rows 8–9; the P17-K definition |
| `CT-PO-P17-DECISION-02-…-20250925.md` | the Scope 2 / Scope 3 truth positions (`§14.4`–`§14.6`) |
| `CT-PO-P17-DECISION-01-…-20250925.md` | the four truth levels `L1`–`L4`; capability vs applicability separation |
| `p17_scope3_category_matrix_20250925.json` (via `DECISION-03 §11`) | the authoritative 15-category `architecture_status` matrix |
| `P17-PRODUCT-01` — … Product Specification | the product-contract dimensions (P17-10) |
| `CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` | the **PQ-6 evidence** for the framework-version row (`§4` S1; `§9.0`) |
| `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md §7` | `PQ-6` — version rows must be evidenced, never invented |

### 3.2 The governed vocabulary — read, not restated

The catalogue uses the vocabularies that **already exist**; this task added none.

```python
# backend/domain/disclosure.py (verbatim)
REQUIREMENT_CLASSES      = ("REQUIRED", "CONDITIONAL", "OPTIONAL", "NOT_APPLICABLE",
                            "CUSTOMER_INPUT_REQUIRED", "UNDETERMINED",
                            "NOT_SUPPORTED", "FUTURE")                    # L47-56 (8)
CARBONTALLY_CAPABILITIES = ("SUPPORTED", "PARTIALLY_SUPPORTED",
                            "STRUCTURED_INPUT_REQUIRED", "EXTERNAL_INPUT_REQUIRED",
                            "MISSING_CAPABILITY", "FUTURE",
                            "NOT_APPLICABLE_TO_PRODUCT")                  # L60-68 (7)
```

Both are **CHECK-enforced in the database** on
`disclosure_requirement_versions` (created by
`20260914000000_p8_b1_disclosure_model_foundation.sql`), so the vocabulary is a
schema fact, not a convention (§7.1).

### 3.3 The PQ-6 evidence basis for the framework-version row

`disclosure_requirement_versions.framework_version_id` is `NOT NULL`, so a
requirement cannot exist without a version row. `PQ-6` allows a version row to be
seeded **only** where the identity/version information is supported by
authoritative evidence, and forbids inventing one: *"Version rows MUST NOT be
invented."* The evidence exists in the repository and was used **verbatim** — no
new research, no new claim:

| Fact seeded | Source (verbatim) |
|---|---|
| version identity: **`Corporate Accounting and Reporting Standard (2004 revised edition)`** (+ Scope 2 Guidance 2015; Scope 3 Standard; Feb-2013 gases/GWP amendment) | `CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` **§9.0 "Framework inventory (verified versions)"** — the column is literally titled *"Authoritative version to bind"* |
| `source_tier = 1`, `source_url = https://ghgprotocol.org/corporate-standard` | idem **§4 source register, S1** (tier 1) |
| `status = 'IN_FORCE'` | idem §9.0 — the Corporate Standard *is* the in-force accounting foundation (D8) |
| `legal_reference = NULL` | GHG Protocol is a **voluntary** standard, not a legal instrument — nothing invented |
| `authoritative_source_date = NULL`, `applicable_from = NULL` | the evidence record names the **edition** but establishes no machine-checkable date; asserting one would breach PQ-6. The record's read date (2026-09-12) is **verification provenance** (recorded here), not the source's own date |

**Companion standards are deliberately NOT given their own version rows.** The
evidence record names the Scope 2 Guidance (2015) and the Corporate Value Chain
(Scope 3) Standard as companions but supplies no authoritative **version label or
date** for them; a version row each would be invented. They are named in each
requirement's `source_locator` instead (see §19, limitation L-2).



---

## 4. Migration inventory

### 4.1 The five pre-existing P17 migrations (verified present, unmodified)

| # | File | Creates / changes | Applied to the clone |
|---|---|---|---|
| P17-A | `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | 8 accounting dimensions + 2 acting-for columns on `calculation_snapshots`, mirrors on `emissions_logs`; factor-governance columns; resolver columns; org consolidation/type; acting-for on 7 paths | ✅ `rc=0` |
| P17-C | `20261011000000_p17c_contractual_instruments_and_allocations.sql` | `contractual_instruments` + `instrument_allocations` with the composite cross-tenant FK | ✅ `rc=0` |
| P17-D | `20261012000000_p17d_scope3_category_taxonomy.sql` | `scope3_categories` — the governed 15-row category taxonomy (reference data) | ✅ `rc=0` |
| P17-H | `20261013000000_p17h_estimation_and_assumption_records.sql` | `estimation_records` + boundary/consolidation work | ✅ `rc=0` |
| P17-10 | `20261014000000_p17_10_product_contract_reporting_dimensions.sql` | `scope3_method`, `transaction_provider`; **widened** 9-value `data_quality`; four reporting indexes | ✅ `rc=0` |

**No `p17b` / `p17e` / `p17f` / `p17g` file exists** — the lettering is sparse by
design and the gap implies no outstanding work item (`DECISION-03 §17.3` `PR-1`).

### 4.2 The one new migration this task adds

| File | Kind | Adds schema? |
|---|---|---|
| `20261020000000_p17k_governed_capability_catalogue.sql` | **reference data only** | **No** table, column, enum, CHECK, index, policy or grant. Two guarded `INSERT`s into two pre-existing tables + three fail-loud `DO` guards + a verification checklist |

Its timestamp (`20261020000000`) is strictly after `20261014000000` and after the
P16 baseline (`20261009000000`), and it is registered in the P17 series tuple in
`backend/tests/unit/data/test_p17_migrations.py`, so that series' additive-only
and no-destructive-statement guarantees now cover it.

### 4.3 Why a migration rather than only a Python loader

The repository has both precedents: `disclosure_frameworks` /
`disclosure_report_purposes` identities are seeded **in the B1 migration *and* in**
`backend/data/disclosure.py::seed_reference_identities`; the P17-D category
taxonomy is seeded **only** by a migration. The P17-K catalogue is *governed
reference data behind a deployment gate* (`DECISION-03 §18.1` Tier 1 item 5 makes
the P17 deltas "a **deployment** gate"), so the migration is the correct carrier.
It is the single source of truth for the catalogue content: the tests read the
migration (unit) and the database (integration) rather than restating either.

### 4.4 Ordering and dependency pre-conditions (all enforced in SQL)

| Pre-condition | Enforced by | Failure mode if absent |
|---|---|---|
| the `GHG_PROTOCOL` framework identity exists (Phase 8 B1) | `DO` guard §0 of the P17-K migration | `RAISE EXCEPTION` — *"the GHG_PROTOCOL framework identity is absent"* |
| the governed Scope 3 taxonomy has exactly 15 rows (P17-D) | `DO` guard §3 | `RAISE EXCEPTION` — *"the governed Scope 3 taxonomy is incomplete"* |
| the catalogue is complete **and correctly mapped** | `DO` guard §4 (post-condition) | `RAISE EXCEPTION` — *"governed capability catalogue incomplete"* / *"Scope 3 capability rollup is … but the frozen matrix requires 4/6/3/2"* / *"a market-based Scope 2 requirement was recorded with producible capability"* |

These guards exist because of a **real defect caught during this task** — §6.2.

---

## 5. Pre-migration disposable schema state

Clone created for this task: **`ct_p17k_20260926`**.

**How it was created (and what was *not* done to the demo database).**
`CREATE DATABASE … TEMPLATE carbontally_demo_local` was **rejected by PostgreSQL**
because the demo database has 2 other live sessions (postgrest/realtime):

```
ERROR:  source database "carbontally_demo_local" is being accessed by other users
DETAIL:  There are 2 other sessions using the database.
```

Rather than terminate the demo environment's connections
(`AGENTS.md §55`: never disturb the investor demo), the clone was built by a
**read-only `pg_dump --schema-only`** piped from the container's own `pg_dump`:

```
docker exec supabase_db_carbon_ledger pg_dump -U postgres -d carbontally_demo_local \
  --schema-only --no-owner  →  psql -d ct_p17k_20260926
```

Result: **141 public tables, 15 `disclosure_*` tables, the 2 `p8_disclosure_*`
helpers, and the `extensions` schema — a faithful copy of the demo schema.**
The restore reported **0 errors**.

Measured pre-migration state on the clone (`SELECT`-only):

| Probe | Value |
|---|---|
| `public` base tables | **141** |
| P17 dimension columns on `calculation_snapshots` | **NONE** |
| P17 dimension columns on `emissions_logs` | **NONE** |
| P17 tables (`contractual_instruments`, `instrument_allocations`, `estimation_records`, `scope3_categories`) | **0 of 4 present** |
| `disclosure_frameworks` / `_framework_versions` / `_requirement_versions` / `_report_purposes` rows | `0 / 0 / 0 / 0` |
| columns named `architecture_status` (anywhere) | **0** |
| applicability-related tables | **1** — `disclosure_applicability_assessments` (pre-existing B1, tenant-side) |

This reproduces `DECISION-03 §3.9` exactly: **`PR-1` was outstanding and `PR-2` was
empty at the start of P17-K.**

---

## 6. Migration execution

### 6.1 The chain applied (disposable clone only)

```
20260914000000_p8_b1_disclosure_model_foundation.sql  → rc=0, 0 errors  (idempotent; seeds the 3 D1 identities + 4 D6-R purposes)
20261010000000_p17a_…                                 → rc=0, 0 errors
20261011000000_p17c_…                                 → rc=0, 0 errors
20261012000000_p17d_…                                 → rc=0, 0 errors
20261013000000_p17h_…                                 → rc=0, 0 errors
20261014000000_p17_10_…                               → rc=0, 0 errors
20261020000000_p17k_…                                 → rc=0, 0 errors
```

Every statement ran under `psql -v ON_ERROR_STOP=1`. The B1 migration was run
**first** because the clone is schema-only: B1 is idempotent
(`CREATE TABLE IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`,
`DROP POLICY IF EXISTS` + `CREATE POLICY`, `ON CONFLICT (code) DO NOTHING`) and
is the sanctioned path that establishes the `disclosure_frameworks` identities the
catalogue hangs off. Zero errors, `framework_rows = 3` afterwards — matching the
demo database's identity set exactly.

### 6.2 A defect was found by this pass — and fixed at both levels

**The first application of the P17-K migration produced a WRONG catalogue.**

Cause: the Scope 3 `INSERT` joined the 15-row `VALUES` capability map with
`CROSS JOIN` and **no `category` predicate**. Because the generated
`requirement_code` came from the *taxonomy* (`c.category`) while the capability
came from the map (`m.*`), the statement was a 15 × 15 cross product; and because
`ON CONFLICT (framework_version_id, requirement_code) DO NOTHING` silently keeps
whichever row arrives first, **every category received the first map row's
capability (`PARTIALLY_SUPPORTED`)**. The result had the right *shape* (18 rows)
and the wrong *content*.

It was caught by the §10 verification set — `F. distinct persisted values` showed
only 3 capability values where 4 were expected, and the per-row listing showed all
15 categories identical.

**Two independent fixes were made, at different levels:**

1. **The statement** — `AND m.category = c.category` (the required per-category
   join), with a comment recording why.
2. **The guard** — the post-condition was strengthened from a *row count* to a
   **rollup assertion**, because a catalogue of the right size and the wrong
   mapping is the more dangerous failure and is invisible to a count:

   ```sql
   IF (n_sup, n_part, n_fut, n_miss) <> (4, 6, 3, 2) THEN
       RAISE EXCEPTION 'P17-K: Scope 3 capability rollup is %/%/%/% but the frozen matrix requires 4/6/3/2 …';
   END IF;
   ```

   plus a Scope 2 guard (`GP-S2-MB` may never be recorded as producible).

This is recorded rather than silently absorbed (`AGENTS.md §80`), and it is why
§7's evidence comes from a **full clone rebuild** rather than from a patch
re-application.

### 6.3 Idempotency

Re-running the P17-K migration on the already-seeded clone:

```
requirement_versions before=18  after=18   (rc=0, 0 errors)
```

Re-running the B1 migration is likewise a no-op (`frameworks_inserted = 0`).


---

## 7. Post-migration schema state

### 7.1 Measured after the chain (clone `ct_p17k_20260926`)

| Probe | Result |
|---|---|
| P17 tables present | **4 of 4** — `contractual_instruments`, `instrument_allocations`, `estimation_records`, `scope3_categories` |
| P17 dimension columns on `calculation_snapshots` | **12 of 12** (all eight P17-A dimensions + `performed_by_organization_id` + `acting_for_organization_id` + P17-10's `scope3_method` + `transaction_provider`) |
| P17 dimension columns on `emissions_logs` | **12 of 12** — mirror parity |
| Required CHECK/enum constraints | **12 of 12** named constraints present |
| RLS enabled | `disclosure_requirement_versions` ✅, `disclosure_framework_versions` ✅, `scope3_categories` ✅, `contractual_instruments` ✅, `instrument_allocations` ✅, `estimation_records` ✅ |
| `framework_versions` / `requirement_versions` rows | **1 / 18** |
| `requirement_mappings` / `purpose_requirements` / `applicability_assessments` / `disclosure_values` rows | **0 / 0 / 0 / 0** (deliberately untouched — out of P17-K scope) |
| duplicate `(framework_version_id, requirement_code)` groups | **0** |
| duplicate `requirement_code` groups | **0** |
| columns named `architecture_status` | **0** |
| applicability-related tables | **1** — unchanged from pre-migration (`disclosure_applicability_assessments`) |
| tables created by the **P17-K** migration | **0** (P17-A/C/D/H/10 create 4; the P17-K migration creates none) |

### 7.2 The governed vocabulary, read back from the catalog

`pg_get_constraintdef` returns, byte-for-byte, the governed sets:

```
carbontally_capability ∈ {SUPPORTED, PARTIALLY_SUPPORTED, STRUCTURED_INPUT_REQUIRED,
                          EXTERNAL_INPUT_REQUIRED, MISSING_CAPABILITY, FUTURE,
                          NOT_APPLICABLE_TO_PRODUCT}                                     # 7
requirement_class      ∈ {REQUIRED, CONDITIONAL, OPTIONAL, NOT_APPLICABLE,
                          CUSTOMER_INPUT_REQUIRED, UNDETERMINED, NOT_SUPPORTED, FUTURE}  # 8
```

and the **distinct persisted values** are a strict subset — no drift, no extra
token:

```
capability : FUTURE, MISSING_CAPABILITY, PARTIALLY_SUPPORTED, SUPPORTED
class      : CONDITIONAL, REQUIRED
```

`AG-1` asserts set-equality between the database CHECK and `domain/disclosure.py`,
so the two cannot silently diverge.

---

## 8. Capability catalogue implementation

### 8.1 The single most important distinction in this report

> **PRODUCT CAPABILITY ≠ CUSTOMER APPLICABILITY.**
>
> Every value written by P17-K is a statement about **what CarbonTally offers**
> (`L1`). Not one of them is a statement about **what applies to a customer**
> (`L2`), whether a customer *has* data (`L3`), or what a result's quality is
> (`L4`). The catalogue contains **no organisation, facility, period or figure**,
> and carries **no tenant key** (§13).

| | Product capability (what P17-K writes) | Customer applicability (what P17-K does **not** write) |
|---|---|---|
| Subject | a requirement version (global catalogue row) | an organisation × requirement × period |
| Column | `disclosure_requirement_versions.carbontally_capability` | `disclosure_applicability_assessments.assessed_status` |
| Vocabulary | the 7 `CARBONTALLY_CAPABILITIES` | `APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED` |
| Owner | CarbonTally | the tenant's disclosure assessment |
| Rows written by P17-K | **18** | **0** |
| Answers | *"Can the product produce it?"* | *"Is this requirement in play for this tenant?"* |

### 8.2 What the catalogue is

One framework-version row plus **18 governed requirement rows**:

| Requirement code | Scope | Rows |
|---|---|---|
| `GP-S1` | Scope 1 | 1 |
| `GP-S2-LB`, `GP-S2-MB` | Scope 2 — one row **per method** (the method is part of a result's identity, `SC-1`) | 2 |
| `GP-S3-CAT-01` … `GP-S3-CAT-15` | Scope 3 categories 1–15 | 15 |
| | **total** | **18** |

Category **names** are not restated: they are joined from the governed P17-D
taxonomy (`public.scope3_categories`, 15 rows), so one database holds exactly one
naming of a category. `display_order` is `1`, `2`, `3` for Scope 1/2 and
`100 + category` for Scope 3.

### 8.3 What every row deliberately carries

| Field | Value | Why |
|---|---|---|
| `official_identifier` | **`NULL` for all 18** | no authoritative requirement identifier was readable (GHG Protocol Chapter 9 is a non-extractable binary PDF); inventing one would breach `D17`/`PQ-6` |
| `identifier_status` | `UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION` | the structural guard that permits a NULL official id while recording *why* |
| `source_tier` | `1` | the concept-level requirement set is `[V]` tier-1 (evidence record `§12`), while the exact wording remains `[U]` |
| `source_locator` | e.g. `GHG Protocol Corporate Value Chain (Scope 3) Standard — category 7` | the requirement's home in the authoritative texts |
| `authoritative_text_ref` | names Chapter 9 and records that it was **not readable** | provenance *and* the limitation, on the row |
| `requirement_class` | `REQUIRED` (Scope 1/2), `CONDITIONAL` (Scope 3) | the **framework's** classification (evidence record rows `GP-S1`/`GP-S2` = R, `GP-S3` = C) |
| `value_kind`, `is_quantitative`, `unit_hint`, `period_semantics` | `QUANTITATIVE`, `TRUE`, `kgCO2e`, `ANNUAL` | the requirement's shape |
| `scope_hint` | `'Scope 1'` / `'Scope 2'` / `'Scope 3'` | exactly the values `emissions_logs.scope` / `calculation_snapshots.scope` use, because the projection service uses this as a **scope selector** (`services/disclosure_projection.py:102` → `load_calculation_rows`) |
| `purpose_hint` | `NULL` | binding requirements to report purposes is B3's `disclosure_purpose_requirements` (0 rows by design) — **not** P17-K's scope |

### 8.4 The product outcome is *derived*, never *stored as the framework class*

`requirement_class` is **never** set to `NOT_SUPPORTED` or `FUTURE`. Those are
**product outcomes**, produced by the existing engine at projection time:

```python
# backend/domain/disclosure_projection.py::derive_effective_class  (L246-269)
if applicability_status == "DOES_NOT_APPLY":          return "NOT_APPLICABLE"
if applicability_status == "UNDETERMINED":            return "UNDETERMINED"
if applicability_status == "CUSTOMER_INPUT_REQUIRED": return "CUSTOMER_INPUT_REQUIRED"
if carbontally_capability in UNSUPPORTED_CAPABILITIES:   # MISSING_CAPABILITY | NOT_APPLICABLE_TO_PRODUCT | FUTURE
    return "FUTURE" if carbontally_capability == "FUTURE" else "NOT_SUPPORTED"
return requirement_class
```

Writing a product outcome into the framework classification would conflate the two
axes (`NS-1`, `PQ-3`). That is why a deferred category legitimately carries
`requirement_class = 'CONDITIONAL'` and still derives `FUTURE`.

### 8.5 The prerequisite text lives on the row

`M-6`/`IT-3`/`IT-5` require a **named** prerequisite for anything not fully
supported, and there is no dedicated prerequisite column. The prerequisite and the
bounded-scope statement are therefore carried in `description`, drawn from the
frozen `prerequisite_work` column of `DECISION-03 §11.2` — **without** using any
Axis-A token, so a surface cannot leak an internal status by copying row text
(§15, `AG-3`).

---

## 9. The seven governed capability values

The vocabulary is **exactly** `CARBONTALLY_CAPABILITIES` — 7 values, unchanged,
not renamed, not added to, not removed, not reinterpreted (`M-2`). P17-K uses
**4** of the 7, because for these 18 rows the other 3 would have been wrong:

| # | Governed value | Used? | Rows | Meaning in this catalogue |
|---|---|---|---|---|
| 1 | `SUPPORTED` | ✅ | `GP-S1`, `GP-S2-LB`, `GP-S3-CAT-03/04/05/06` | the product produces it on the defined acceptance path |
| 2 | `PARTIALLY_SUPPORTED` | ✅ | `GP-S3-CAT-01/07/08/09/12/13` | the product produces it **within a stated bound**; the bound and the prerequisite are on the row |
| 3 | `STRUCTURED_INPUT_REQUIRED` | ❌ unused | — | **deliberately unused**: `M-1` maps `PARTIAL → PARTIALLY_SUPPORTED`; the matrix's `/ STRUCTURED_INPUT_REQUIRED` form is an allowance for a *sub-requirement's* input dependency, not a category-level status. Taking the `M-1` arrow is the conservative, non-upgrading reading (§19, L-1) |
| 4 | `EXTERNAL_INPUT_REQUIRED` | ❌ unused | — | **deliberately unused**: `SC-4` permits `EXTERNAL_INPUT_REQUIRED` *or* `MISSING_CAPABILITY` for market-based Scope 2 **before** the instrument pathway is exercised. Because §8.3/§9.4-4 record that **no market-based engine exists at all**, `MISSING_CAPABILITY` is the faithful and non-upgrading value (§10) |
| 5 | `MISSING_CAPABILITY` | ✅ | `GP-S2-MB`, `GP-S3-CAT-02`, `GP-S3-CAT-10` | the product does not currently offer it; derives to `NOT_SUPPORTED` |
| 6 | `FUTURE` | ✅ | `GP-S3-CAT-11/14/15` | deferred pending a **named** decision/prerequisite; derives to `FUTURE` |
| 7 | `NOT_APPLICABLE_TO_PRODUCT` | ❌ unused | — | **deliberately unused**: asserting that CarbonTally is not the answering party for a requirement is a per-requirement PO decision that P17-K was not authorised to make. (`S3-4` shows where it *would* apply, and that it must never render as an applicability outcome.) |

> **Unused ≠ unavailable.** The three unused values remain governed,
> CHECK-enforced and available; they were simply not the correct value for any of
> the 18 rows under the frozen mapping. Recording this explicitly stops a future
> reader mistaking "absent from the catalogue" for "removed from the vocabulary".

Verified mechanically: the CHECK constraint's value set **equals**
`CARBONTALLY_CAPABILITIES` exactly (7), and the distinct persisted capability
values are exactly 4 — `SUPPORTED`, `PARTIALLY_SUPPORTED`, `FUTURE`,
`MISSING_CAPABILITY`.

---

## 10. Scope 2 mapping

### 10.1 The rows

| Requirement | `scope_hint` | `scope2_method_hint` | `requirement_class` | **PRODUCT CAPABILITY** (`carbontally_capability`) | Derived outcome | **CUSTOMER APPLICABILITY** |
|---|---|---|---|---|---|---|
| `GP-S1` — Scope 1 emissions | `Scope 1` | `NULL` | `REQUIRED` | **`SUPPORTED`** | `REQUIRED` | **not expressed** (0 rows) |
| `GP-S2-LB` — Scope 2, location-based | `Scope 2` | `LOCATION_BASED` | `REQUIRED` | **`SUPPORTED`** | `REQUIRED` | **not expressed** (0 rows) |
| `GP-S2-MB` — Scope 2, market-based | `Scope 2` | `MARKET_BASED` | `REQUIRED` | **`MISSING_CAPABILITY`** | **`NOT_SUPPORTED`** | **not expressed** (0 rows) |

### 10.2 Why Scope 2 is two rows and not one

`SC-1`: the method is part of a Scope 2 result's **identity**, not its metadata.
`SC-2`: it is never inferred or defaulted. `SC-3`: location-based and market-based
are never summed, netted or reconciled. A single "Scope 2" requirement row would
have to carry one method or none, and **either** would misstate the product.
Splitting by method is therefore the smallest honest representation, and it uses
the **pre-existing** CHECK-constrained `scope2_method_hint` column — no new column,
no new vocabulary, and crucially **no per-method applicability state** (`PO-6`,
resolved in substance by PO-3: the method is a *result dimension*, not an
applicability concept).

### 10.3 Why market-based is `MISSING_CAPABILITY` and not `SUPPORTED`

Three independent frozen rules forbid "supported":

| Rule | Statement |
|---|---|
| `SC-4` | market-based may be described as supported **only** where the contractual-instrument pathway is actually available; on the demo database it is not |
| §8.3 | *"Market-based is **not** implemented as an engine … A market-based Scope 2 total must **not** be claimed"* |
| §9.4 item 4 | *"**'Market-based Scope 2 is supported'** — no engine exists (`D-10`)"* is on the **prohibited** list |

`SC-4` allows `EXTERNAL_INPUT_REQUIRED` **or** `MISSING_CAPABILITY`. Because the
blocker is the **absence of an engine**, not the absence of inputs,
`MISSING_CAPABILITY` is the faithful value — and `SC-4`'s own instruction is
"**never** `SUPPORTED`". It derives to `NOT_SUPPORTED`, which is what the honest
statement *"CarbonTally does not currently support market-based Scope 2"* requires.

> **No Scope 2 figure may be produced from this mapping.** `SC-5` still holds
> (factor presence is not Scope 2 coverage), and `SC-6` still holds (a WTT line
> misrouted into Scope 2 is a claim defect). Scope 2 **end-to-end runtime
> acceptance** remains `P17-J`/`PR-3` — outstanding, and **not** claimed here.

### 10.4 What Scope 2 does **not** get from P17-K

| Not created | Rule |
|---|---|
| a Scope 2 applicability model | `F-1`; `PO-6` |
| an energy-type dimension in the catalogue (electricity/heat/steam/cooling) | that vocabulary already lives on `calculation_snapshots.energy_type` (P17-A, 4 values, `fuel` excluded). The requirement catalogue holds **requirements**, not energy types — adding four Scope 2 requirement rows would invent a segmentation the contract does not have |
| contractual-instrument records | `contractual_instruments` / `instrument_allocations` exist (P17-C applied) and are the correct home; the catalogue holds no tenant instrument data |

---

## 11. Scope 3 mapping — categories 1 to 15

### 11.1 The frozen rollup, reproduced from persisted rows

```
SUPPORTED            [3, 4, 5, 6]         →  4 of 15
PARTIALLY_SUPPORTED  [1, 7, 8, 9, 12, 13] →  6 of 15
FUTURE               [11, 14, 15]         →  3 of 15
MISSING_CAPABILITY   [2, 10]              →  2 of 15
```

Measured from the database: **`SUPPORTED = 4`, `PARTIALLY_SUPPORTED = 6`,
`FUTURE = 3`, `MISSING_CAPABILITY = 2`** — exact. The migration's own
post-condition asserts this arithmetic, so the wrong mapping fails the deployment
rather than shipping (§6.2).

### 11.2 The mapping, per category

The internal `architecture_status` column is the **mapping source only**; it is
**not stored** (`M-3`, `M-4`). The persisted value is the governed capability.

| # | Category | Internal `architecture_status` (**not persisted, not rendered**) | **PRODUCT CAPABILITY** (persisted `carbontally_capability`) | `requirement_class` | Derived outcome | Named prerequisite carried on the row | **CUSTOMER APPLICABILITY** |
|---|---|---|---|---|---|---|---|
| 1 | Purchased goods and services | `PARTIAL` | **`PARTIALLY_SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | canonical category dimension (P17-D); explicit methodology record for spend-based lines; **PO decision on spend-based authorisation** | **not expressed** |
| 2 | Capital goods | `NOT_IMPLEMENTED` | **`MISSING_CAPABILITY`** | `CONDITIONAL` | **`NOT_SUPPORTED`** | capital-goods methodology decision; category 1↔2 exclusion control; asset-level attribution | **not expressed** |
| 3 | Fuel- and energy-related activities | `SUPPORTED` | **`SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | category 3 source-snapshot derivation link + uniqueness (DC-02) | **not expressed** |
| 4 | Upstream transportation and distribution | `SUPPORTED` | **`SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | upstream/downstream boundary property (DC-04); mode vocabulary | **not expressed** |
| 5 | Waste generated in operations | `SUPPORTED` | **`SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | category dimension on the waste path (P17-D) | **not expressed** |
| 6 | Business travel | `SUPPORTED` | **`SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | WTT routing rule so WTT variants land in category 3 (DC-02) | **not expressed** |
| 7 | Employee commuting | `PARTIAL` | **`PARTIALLY_SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | estimation-record entity/contract (P17-H); **PO decision on average-data commuting estimates** | **not expressed** |
| 8 | Upstream leased assets | `PARTIAL` | **`PARTIALLY_SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | consolidation-approach dimension; DC-07 duplication detector | **not expressed** |
| 9 | Downstream transportation and distribution | `PARTIAL` | **`PARTIALLY_SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | boundary property + DC-04 detector; **PO decision on which outbound-logistics element is in scope** | **not expressed** |
| 10 | Processing of sold products | `NOT_IMPLEMENTED` | **`MISSING_CAPABILITY`** | `CONDITIONAL` | **`NOT_SUPPORTED`** | processing factor/methodology decision; processor-declaration contract; sold-product entity; DC-03 exclusion | **not expressed** |
| 11 | Use of sold products | `DEFERRED` | **`FUTURE`** | `CONDITIONAL` | **`FUTURE`** | **PO decision on a bounded use-phase methodology and product types**; assumption-set + sold-product entities | **not expressed** |
| 12 | End-of-life treatment of sold products | `PARTIAL` | **`PARTIALLY_SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | waste-origin property + DC-05 detector; sold-product entity; treatment-mix assumption record | **not expressed** |
| 13 | Downstream leased assets | `PARTIAL` | **`PARTIALLY_SUPPORTED`** | `CONDITIONAL` | `CONDITIONAL` | lease-direction property + DC-07 detector; consolidation-approach dimension | **not expressed** |
| 14 | Franchises | `DEFERRED` | **`FUTURE`** | `CONDITIONAL` | **`FUTURE`** | **PO decision on the franchise operating model**; franchise entity; allocation-basis contract | **not expressed** |
| 15 | Investments | `DEFERRED` | **`FUTURE`** | `CONDITIONAL` | **`FUTURE`** | **PO decision ratifying bounded `attribution_equity_share` and on PCAF**; investment entity; lag handling | **not expressed** |

### 11.3 The four things this table deliberately does **not** say

| Not said | Why |
|---|---|
| that all 15 categories are equally mature | `S3-1` — the four-way split is the honest expression; "15 categories" unqualified is on the prohibited list |
| that any category **applies to a customer** | PO-3 / `F-1`: the catalogue holds product capability only. Applicability is a future requirement-level concept the PO explicitly declined to build |
| that a category with no result is `0` | `S3-3`, `S3-5` — bounded/absent/deferred rows carry a governed value **and** a named prerequisite; never a zero |
| that factor count means coverage | `S3-6` — categories 4/9, 5/12 and 8/13 **share factor families**; the mapping is status-based, never factor-based |

### 11.4 Two structural consequences preserved

1. **`NOT_SUPPORTED` is about the product, never the customer** (`NS-1`). A
   customer with zero category-2 activity and a customer with substantial
   category-2 activity see the **same** catalogue row — because the row is a
   product statement. The product would have to say the same thing to both.
2. **A `PARTIAL` category was never written as `SUPPORTED`.** Checked
   mechanically: the persisted capability for every `PARTIAL`/`DEFERRED`/
   `NOT_IMPLEMENTED` category is the exact `M-1` image, and the `except`-based
   comparison against the frozen image returned **0 violations**.

---

## 12. P17 runtime dimensions

### 12.1 The dimensions verified present (not re-created)

Every dimension below already had an author (`P17-A`, `P17-C`, `P17-D`, `P17-H`,
`P17-10`). P17-K **verified** them and **added none** (`AGENTS.md §66`; `§18.1`
Tier 1 item 6).

| Dimension | Table(s) | Author | Verified |
|---|---|---|---|
| `scope2_method` | `calculation_snapshots`, `emissions_logs` | P17-A | ✅ + CHECK + `scope <> 'Scope 2' OR scope2_method IS NOT NULL` (`NOT VALID`) |
| `scope3_category` | both | P17-A | ✅ 1–15 CHECK + scope guard |
| `energy_type` | both | P17-A | ✅ 4 values, `fuel` excluded |
| `data_quality` | both | P17-A → **widened by P17-10** | ✅ 9 values (strict superset; no historical value removed) |
| `facility_id` | both | P17-A | ✅ |
| `transport_boundary` | both | P17-A | ✅ DC-04 discriminator |
| `waste_origin` | both | P17-A | ✅ DC-05 discriminator |
| `source_snapshot_id` | both | P17-A | ✅ DC-02 derivation link |
| `performed_by_organization_id` | both | P17-A | ✅ |
| `acting_for_organization_id` | both (+ 7 paths) | P17-A | ✅ |
| `scope3_method` | both | P17-10 | ✅ 10-value CHECK, scope-guarded |
| `transaction_provider` | both | P17-10 | ✅ 1–200 char shape guard |
| contractual instruments | `contractual_instruments`, `instrument_allocations` | P17-C | ✅ composite FK `(instrument_id, organization_id)` |
| estimation records | `estimation_records` | P17-H | ✅ |
| the category taxonomy | `scope3_categories` | P17-D | ✅ 15 rows |

**Verified count: 12 of 12 columns on both tables; 4 of 4 tables; 12 of 12 named
constraints; 6 of 6 tables with RLS enabled.**

### 12.2 Re-run of the `DECISION-03 §3.9` before/after check set

`DECISION-03 §3.9` established the demo database's P17 state by direct
`SELECT`-only inspection. That check set was re-run before and after the chain,
and the delta is exact:

| Check | Demo (before) | Clone (before) | Clone (after) |
|---|---|---|---|
| `calculation_snapshots.scope2_method` | ✗ | ✗ | **✓** |
| `calculation_snapshots.scope3_method` (P17-10) | ✗ | ✗ | **✓** |
| `calculation_snapshots.transaction_provider` | ✗ | ✗ | **✓** |
| `contractual_instruments` | ✗ | ✗ | **✓** |
| `instrument_allocations` | ✗ | ✗ | **✓** |
| `estimation_records` | ✗ | ✗ | **✓** |
| `scope3_categories` | ✗ | ✗ | **✓** |
| `disclosure_requirement_versions` rows | **0** | **0** | **18** |
| `disclosure_framework_versions` rows | **0** | **0** | **1** |

`PR-1` and `PR-2` are therefore **satisfied on a disposable clone** and remain
**outstanding on the demo/production environments**, which is the correct and
intended state: promoting them is the **deployment gate** (`DECISION-03 §18.1`
Tier 1 item 5), not a development act. `P17-K` did **not** promote them.

### 12.3 What the runtime dimensions do **not** prove

Applying a schema does not exercise it. `PR-3` (`P17-J` — Scope 2 end-to-end
runtime acceptance, matrix `S2-15`) remains **OUTSTANDING** and is **not** claimed
here. P17-K proves that the *dimensions the accounting contract needs can be
persisted*; it does **not** prove that a Scope 2 or Scope 3 end-to-end run
produces an accepted result.

---

## 13. RLS and security

### 13.1 No policy was changed, and none needed to be

P17-K creates no table and changes no policy, grant or role. The two tables it
writes already carry the **global-catalogue** posture established by the Phase 8
B1 migration:

| Table | RLS | `anon` | `authenticated` | Write |
|---|---|---|---|---|
| `disclosure_framework_versions` | **enabled** | `REVOKE ALL` | `SELECT` only (policy `USING (true)`) | service-role only |
| `disclosure_requirement_versions` | **enabled** | `REVOKE ALL` | `SELECT` only (policy `USING (true)`) | service-role only |

Verified on the clone: `relrowsecurity = true` for both, and no policy change was
made by the P17-K migration (`grep` of the migration shows no `CREATE POLICY`,
`ALTER TABLE … ENABLE ROW LEVEL SECURITY`, `GRANT` or `REVOKE`).

### 13.2 Why "read-any-authenticated, no tenant predicate" is the correct posture

This is a **product-level catalogue**, and `DECISION-03 §19.2` (`SEC-1`) requires
exactly this: the capability statement must be servable **without any tenant
context**, derived from governed catalogue facts only. A tenant-predicated policy
on a product catalogue would be a category error — and would also make the
investor surface impossible to serve truthfully.

### 13.3 `SEC-4` — the catalogue must not become a cross-tenant channel

A shared catalogue row is read by many tenants. `SEC-4` requires that a surface
never attach **tenant-specific state** to a shared row in a way another tenant can
see. P17-K's contribution to that property is structural and tested (§15 `AG-5`):

* the catalogue tables carry **no tenant key** at all (`organization_id` /
  `org_id` / `tenant_id` — zero columns);
* they have **no foreign key** to a tenant table (the only FK targets are
  `disclosure_frameworks` and `disclosure_framework_versions`);
* the capability payload is **byte-identical** under two different tenant
  contexts (isolation row 8);
* tenant state lives where it belongs — `disclosure_applicability_assessments`
  and `disclosure_values` — which P17-K does not touch (0 rows written).

### 13.4 What P17-K did **not** do to security

| Not done | Rule |
|---|---|
| no RLS disabled or bypassed | `AGENTS.md §67` |
| no service-role shortcut introduced | `SEC-2` |
| no new endpoint, route, policy, role or grant | `§19.1` |
| no signed URL, credential, token or storage path read or written | `§19.5` |
| no tenant table read during catalogue authoring | `SEC-1` |

---

## 14. Negative controls

### 14.1 Scope 2 market-based is `NOT_SUPPORTED`

Two independent controls assert it cannot be recorded as producible:

* the migration's own post-condition: `RAISE EXCEPTION` if `GP-S2-MB` carries
  `SUPPORTED` or `PARTIALLY_SUPPORTED`;
* the unit gate `test_ag_2_scope2_market_based_is_not_recorded_as_producible`,
  which additionally asserts that **no** producible capability literal follows
  `'MARKET_BASED', 3,` in the SQL.

Persisted result: `MISSING_CAPABILITY` → derives to `NOT_SUPPORTED`.

### 14.2 No applicability concept exists

| Probe | Result |
|---|---|
| tables matching `%appl%` / `%applicab%` | exactly **1** — `disclosure_applicability_assessments`, pre-existing, unchanged |
| rows P17-K wrote into it | **0** |
| `requirement_class = 'NOT_APPLICABLE'` rows | **0** |
| `'NOT_APPLICABLE'` / `'DOES_NOT_APPLY'` / `NO_DATA_YET` / `EXCLUDED_WITH_REASON` in the migration's executable SQL | **absent** |
| applicability vocabulary in catalogue row text | **absent** |

### 14.3 No Axis-A vocabulary is persisted or reachable

| Probe | Result |
|---|---|
| columns named `architecture_status` in the entire database | **0** |
| `PARTIAL` / `DEFERRED` / `NOT_IMPLEMENTED` as a persisted value in any catalogue column | **0** |
| those tokens anywhere in the migration's executable SQL (word-boundary, case-sensitive) | **absent** |
| those tokens anywhere in catalogue row text (`title`, `description`, `source_locator`), case-insensitive | **absent** — so a surface cannot leak an internal status even by copying prose |

### 14.4 The destructive test harness refuses persistent environments (F-046-1)

Run **live**, with `INTEGRATION_DATABASE_URL` pointed at the demo database:

```
RuntimeError: refusing to run the integration suite against 'carbontally_demo_local':
the name matches the protected persistent marker 'demo', and this fixture performs
DESTRUCTIVE setup (TRUNCATE … RESTART IDENTITY CASCADE). (PO operational control
F-046-1.) Create a DISPOSABLE clone first …
```

The refusal occurs **before** any `TRUNCATE`. Demo verified unchanged afterwards:

```
demo: orgs=4  snapshots=34  logs=34  tables=141  requirement_versions=0
```

The same rule set is asserted as a test
(`test_the_f046_1_probe_refuses_persistent_environments`), covering
`carbontally_demo_local`, `carbontally_qa_phase8`, `ct_investor_demo`,
`carbontally_prod`, `carbontally_live`, `postgres` and
`supabase_db_carbon_ledger`.

### 14.5 The migration fails loudly rather than silently

Three guards, each with its own test:

| Guard | Fails when |
|---|---|
| §0 pre-condition | the `GHG_PROTOCOL` identity is absent → *"the GHG_PROTOCOL framework identity is absent (rows = %)"* |
| §3 pre-condition | `scope3_categories` does not have 15 rows → *"the governed Scope 3 taxonomy is incomplete"* |
| §4 post-condition | fewer than 18 requirement rows → *"governed capability catalogue incomplete"* |
| §4 post-condition | the rollup ≠ 4/6/3/2 → *"Scope 3 capability rollup is %/%/%/% but the frozen matrix requires 4/6/3/2"* |
| §4 post-condition | market-based recorded as producible → *"a market-based Scope 2 requirement was recorded with producible capability"* |

The rollup guard exists **because** the §6.2 defect proved that a row-count
assertion is not sufficient protection against a wrong mapping.

---

## 15. Acceptance gates AG-1 … AG-8

`DECISION-03 §18.3` defines the gates for **any future capability surface**, and
`§20.3` step 4 requires P17-K to add them "as automated tests, including the two
new isolation tests". No surface exists yet (`§18.1` Tier 3), so each gate is
implemented **at the layer that exists today** — the governed catalogue and the
projection engine — and the surface-rendering branch is reported as **PENDING**,
never as satisfied.

**Files:** `backend/tests/unit/data/test_p17k_governed_capability_catalogue.py`
(22 tests, migration text + real vocabulary + real engine) and
`backend/tests/integration/test_p17k_governed_capability_catalogue_runtime.py`
(24 tests, real PostgreSQL on the disposable clone).

| Gate | What it requires | How P17-K implements it | Status |
|---|---|---|---|
| **AG-1** | every capability value rendered is a member of the governed CSV — the **7 × `M-1`** or the `REQUIREMENT_CLASSES` reached via `derive_effective_class` | (a) unit: parsed catalogue values ⊆ `CARBONTALLY_CAPABILITIES`; classes ⊆ `REQUIREMENT_CLASSES`; (b) integration: the DB **CHECK sets equal** the source constants; (c) every persisted value is a governed member | **VERIFIED** at the catalogue/projection layer |
| **AG-2** | every absent / unsupported / deferred / undetermined item carries a reason class / governed value — with `NOT_SUPPORTED` and `CUSTOMER_INPUT_REQUIRED` as **distinct** outcomes | unit + integration: `derive_effective_class` over **every persisted row** yields a governed outcome; `{CONDITIONAL, FUTURE, NOT_SUPPORTED}` observed; `NOT_SUPPORTED ≠ CUSTOMER_INPUT_REQUIRED` asserted explicitly; market-based pinned to `NOT_SUPPORTED` | **VERIFIED** at the catalogue/projection layer |
| **AG-3** | no Axis-A token is rendered on any non-internal surface | (a) no Axis-A token is a persisted **value**; (b) those tokens are **absent** from the migration's executable SQL; (c) they are absent from catalogue **row text** case-insensitively; (d) **no `architecture_status` column exists anywhere**, so it cannot be selected and rendered | **VERIFIED** at the catalogue layer; **rendering branch PENDING a surface** |
| **AG-4** | no `0` / `0 tCO₂e` / `N/A` / `—` / "not applicable" / "excluded" / "coming soon" for a non-produced item | (a) every row carries a governed capability value (never a placeholder or zero); (b) placeholder tokens absent from the whole migration file and from row text; (c) no fabricated emissions figure (`\d+ (kg|t) CO2e`) anywhere | **VERIFIED** at the catalogue layer; **rendering branch PENDING a surface** |
| **AG-5** | the investor surface contains **no** tenant identifier and issues **no** tenant-table query | (a) no tenant column on the catalogue tables; (b) **no FK path** from the catalogue to any tenant table; (c) the shipped catalogue query contains no tenant predicate, no `current_setting`, no `auth.uid`; (d) two distinct tenant contexts return **byte-identical** payloads | **VERIFIED** at the catalogue layer; **surface route/query audit PENDING** |
| **AG-6** | the same requirement shows the **same** value on both surfaces | (a) exactly one row and one capability value per `requirement_code`; (b) **no** per-surface variant column exists (`investor_capability` / `customer_capability`) and no `coverage` / `completeness` / `materiality` / `assurance` column exists | **VERIFIED** structurally (`CS-2` cannot be violated by construction); equality *test between surfaces* **PENDING surfaces** |
| **AG-7** | the four-way rollup is shown, not a total | (a) the rollup recomputed from the migration = `{SUPPORTED:4, PARTIALLY_SUPPORTED:6, FUTURE:3, MISSING_CAPABILITY:2}`; (b) the same recomputed from **persisted rows**; (c) no "all 15" / "15 categories supported" / total expression in executable SQL; (d) the migration itself refuses to deploy on a wrong rollup | **VERIFIED** at the catalogue layer; **rendering branch PENDING a surface** |
| **AG-8** | any illustrated result on the investor surface resolves to persisted data with provenance | (a) every row carries `source_locator` + `authoritative_text_ref` + `source_tier = 1`; (b) `official_identifier IS NULL` with `identifier_status = 'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION'` (an explicit marker, not a guessed id); (c) **no fabricated figure** exists in the catalogue | **VERIFIED** at the catalogue layer (no result is illustrated); **per-result provenance check PENDING a surface** |

### 15.1 The two load-bearing isolation tests (`§19.4` rows 8–9)

| Row | Boundary | Expected | Test |
|---|---|---|---|
| **8** | **Investor surface → any tenant data** | **DENY / IMPOSSIBLE** | `test_isolation_row_8_tenant_context_cannot_change_the_catalogue`, `test_isolation_row_8_the_catalogue_query_has_no_tenant_predicate`, `test_ag_5_the_catalogue_carries_no_tenant_column`, `test_ag_5_no_foreign_key_leads_from_the_catalogue_to_a_tenant` |
| **9** | **Any non-internal surface → Axis A vocabulary** | **ABSENT** | `test_isolation_row_9_axis_a_vocabulary_is_unreachable`, `test_ag_3_no_architecture_status_column_exists_anywhere`, `test_ag_3_no_axis_a_token_is_persisted`, `test_ag_3_no_applicability_vocabulary_is_persisted` |

These are not weakened, skipped, xfailed or relaxed. **Every gate that reports
`VERIFIED` is backed by an executing test**; nothing was asserted merely because
the suite ran (`AGENTS.md §73`, `§74`).

---

## 16. Real PostgreSQL verification

Environment: **`ct_p17k_20260926`** — a disposable clone of `carbontally_demo_local`
(`F-046-1`-permitted `ct_*` name; `current_database()` asserted in-suite). Every
statement below ran against that real PostgreSQL 17.6 instance.

| # | Check | Result |
|---|---|---|
| **A** | all required tables exist | **4 of 4** — `contractual_instruments`, `instrument_allocations`, `estimation_records`, `scope3_categories` |
| **B** | all required columns exist | **0 missing** on `calculation_snapshots` and **0 missing** on `emissions_logs` (12 checked on each) |
| **C** | required constraints exist | **12 of 12** named constraints present (`scope2_method` check + required, `scope3_category` check + required, `energy_type`, `data_quality`, `scope3_method`, `transaction_provider`, plus the two `disclosure_requirement_versions` vocabulary CHECKs) |
| **D** | RLS enabled where required | `true` for all six checked tables |
| **E** | capability/enum values match source **exactly** | CHECK value sets **equal** `CARBONTALLY_CAPABILITIES` (7) and `REQUIREMENT_CLASSES` (8) |
| **F** | no unexpected capability values | distinct persisted capabilities = `{SUPPORTED, PARTIALLY_SUPPORTED, FUTURE, MISSING_CAPABILITY}` — all members; no drift |
| **G** | governed catalogue rows exist | `framework_versions = 1`, `requirement_versions = 18`; `mappings = 0`, `purpose_requirements = 0`, `applicability = 0`, `values = 0` (untouched by design) |
| **H** | no duplicate catalogue rows | duplicate `(framework_version_id, requirement_code)` groups = **0**; duplicate `requirement_code` groups = **0** |
| **I** | all required category mappings exist | 15 category rows; missing categories = **NONE**; rollup 4 / 6 / 3 / 2; non-upgrade violations = **0**; exact-`M-1`-image violations (`EXCEPT`) = **0** |
| **J** | no applicability table/model introduced | applicability-related tables = **1** (pre-existing, unchanged); tenant keys on the catalogue = **0**; forbidden tokens as a persisted value = **0**; `NOT_APPLICABLE` class used = **0**; `architecture_status` columns = **0** |
| **K** | negative tenant isolation | catalogue tables carry no tenant key and no tenant FK; the payload is **byte-identical** under two distinct tenant contexts; the shipped query has no tenant predicate |
| **L** | demo database rejected by the safety probe | **REFUSED (F-046-1)** — live `RuntimeError` before any `TRUNCATE`; demo verified unchanged afterwards (`orgs=4, snapshots=34, logs=34, tables=141, requirement_versions=0`) |
| **M** | production never contacted | **no production DSN exists in this environment**; all work was against `127.0.0.1:54426` (a local Docker cluster). `carbontally_demo_local` was accessed **read-only** (schema dump + `SELECT`); `carbontally_test` was not used |

### 16.1 The exact persisted catalogue (verbatim from the database)

```
GP-S1        | SUPPORTED           | REQUIRED     | scope2=-
GP-S2-LB     | SUPPORTED           | REQUIRED     | scope2=LOCATION_BASED
GP-S2-MB     | MISSING_CAPABILITY  | REQUIRED     | scope2=MARKET_BASED
GP-S3-CAT-01 | PARTIALLY_SUPPORTED | CONDITIONAL  | scope2=-
GP-S3-CAT-02 | MISSING_CAPABILITY  | CONDITIONAL  | scope2=-
GP-S3-CAT-03 | SUPPORTED           | CONDITIONAL  | scope2=-
GP-S3-CAT-04 | SUPPORTED           | CONDITIONAL  | scope2=-
GP-S3-CAT-05 | SUPPORTED           | CONDITIONAL  | scope2=-
GP-S3-CAT-06 | SUPPORTED           | CONDITIONAL  | scope2=-
GP-S3-CAT-07 | PARTIALLY_SUPPORTED | CONDITIONAL  | scope2=-
GP-S3-CAT-08 | PARTIALLY_SUPPORTED | CONDITIONAL  | scope2=-
GP-S3-CAT-09 | PARTIALLY_SUPPORTED | CONDITIONAL  | scope2=-
GP-S3-CAT-10 | MISSING_CAPABILITY  | CONDITIONAL  | scope2=-
GP-S3-CAT-11 | FUTURE              | CONDITIONAL  | scope2=-
GP-S3-CAT-12 | PARTIALLY_SUPPORTED | CONDITIONAL  | scope2=-
GP-S3-CAT-13 | PARTIALLY_SUPPORTED | CONDITIONAL  | scope2=-
GP-S3-CAT-14 | FUTURE              | CONDITIONAL  | scope2=-
GP-S3-CAT-15 | FUTURE              | CONDITIONAL  | scope2=-
```

### 16.2 Test result summary

| Suite | Tests | Result |
|---|---|---|
| P17-K unit (`tests/unit/data/test_p17k_governed_capability_catalogue.py`) | **22** | **22 passed, 0 failed** |
| P17-K integration (`tests/integration/test_p17k_governed_capability_catalogue_runtime.py`) | **24** | **24 passed, 0 failed** |
| P17 migration-series unit (`test_p17_migrations.py`, now covering the P17-K migration) | **46** | **46 passed, 0 failed** |

`IMPLEMENTED` + `TESTED` + **real-PostgreSQL `VERIFIED`** for everything in §15
that is reported `VERIFIED`.

---

## 17. Regression suite

| Suite | Command / environment | Result |
|---|---|---|
| **P17-K unit** | `pytest tests/unit/data/test_p17k_governed_capability_catalogue.py` | **22 passed, 0 failed** |
| **P17-K integration** | `…/ct_p17k_20260926 pytest tests/integration/test_p17k_…runtime.py` | **24 passed, 0 failed** |
| **P17-K integration — dirty-catalogue robustness** | same suite on `ct_p17k_ctl_20260926` (89 pre-existing requirement rows) | **24 passed, 0 failed** |
| **P17 migration series** | `pytest tests/unit/data/test_p17_migrations.py` (now covering the P17-K migration) | **46 passed, 0 failed** |
| **P17 unit selection** (P17-02…P17-10 suites) | 17 P17 test modules | **0 failures, 0 errors** |
| **Wider unit suite** | `pytest tests/unit` | **9 failures, 0 errors** — see §18; the documented baseline set, **not** claimed green |
| **P17-09 real PostgreSQL** | `…/ct_p17k_ctl_20260926` (a copy of the baseline's own clone chain) | **0 failures** — *before* **and** *after* applying the P17-K migration |
| **P17-10 real PostgreSQL** | idem | **0 failures** — *before* **and** *after* applying the P17-K migration |
| **F-046-1 safety probe** | `…/carbontally_demo_local` | **REFUSED** — live `RuntimeError`, before any `TRUNCATE` |

### 17.1 The orthogonality control (why the P17-09/10 result is trustworthy)

The P17-09/P17-10 baselines were recorded against an older clone chain. To show
that P17-K changes nothing for those suites, the exact baseline environment was
reproduced as a **copy** (`ct_p17k_ctl_20260926`, `TEMPLATE`-cloned from
`ct_p17_10_verify_20260925` — read-only on the source), and the suites run twice:

| Run | P17-K catalogue migration | P17-09 | P17-10 |
|---|---|---|---|
| 1 | **not applied** | 0 failures | 0 failures |
| 2 | **applied** | 0 failures | 0 failures |

The migration added exactly **18** rows on its own version label while leaving the
clone's **89** pre-existing requirement rows untouched (`89 → 107`). The P17-K
change is therefore **orthogonal** to the P17-09/10 contract.

### 17.2 The self-correcting effect of the control

The control clone's unrelated requirement rows exposed that the P17-K integration
suite's queries were **not scoped** to the catalogue P17-K governs — five gates
produced false failures there. The suite was therefore scoped to the evidenced
`version_label`, which is **strictly stronger** (it still catches the §6.2 defect,
and the exact-`M-1`-image check still uses `EXCEPT` against the frozen image), and
the migration's post-condition was scoped the same way. Both environments now
report **24 passed, 0 failed**.

---

## 18. Known baseline failures

`pytest tests/unit` reports **exactly 9 failures**, matching the documented
baseline for this suite family (`CT-PO-P17-IMPLEMENT-10 … §18` records *"Wider
unit … 3457 tests, 9 failures, 0 errors, 8 skipped"*). They are:

| # | Test | Domain |
|---|---|---|
| 1–3 | `tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`, `::test_canonical_ops_review_assign_registered`, `::test_canonical_ops_sla_surface_registered` | review/SLA route registration |
| 4 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | **"the latest migration"** assertion |
| 5 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | **"the latest migration"** assertion |
| 6 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | **"the latest migration"** assertion |
| 7–9 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved`, `::test_suggest_no_fabrication_on_garbage`, `::test_suggest_parses_clean_invoice` | extraction suggestion engine |

### 18.1 Proof that P17-K introduced none of them

Three of the nine are **migration-ordering** assertions, so a new migration
*plausibly could* have caused them. They were therefore tested directly: the final
P17-K migration was **moved aside** and the affected modules re-run.

> **Result — all 9 still fail with the migration absent.** The three
> "latest migration" tests were already failing because the pre-existing P17
> migrations (`20261010…`–`20261014…`) are already later than the I1/I2/D17
> migrations those tests assert are last. The file was restored immediately and
> verified present.

**Conclusion: P17-K introduces 0 new unit failures.** The known 9 remain and are
**not** reported as green.

### 18.2 New findings raised by this task (recorded, never silently absorbed)

| ID | Finding | Severity | Status |
|---|---|---|---|
| **P17K-F1** | **The P17-09/P17-10 integration suites are not reproducible-green on a clone of the *current* demo schema.** `calculation_snapshots.performed_by` carries a **validated** FK to `auth.users(id)` (added by the pre-existing Gate-4 migration `20260905000000_gate4_actor_provenance.sql`), while `test_p17_09…` supplies `"performed_by": new_id()` — a random UUID. On the current schema this yields FK violations (27 per suite); the **older clone chain lacks the FK**, which is why the recorded baselines (38 / 30 passed) were green. Verified: `pg_constraint` shows the FK on `carbontally_demo_local` and `ct_p17k_20260926`, and **NONE** on `ct_p17_migcheck_20260925` / `ct_p17_09_verify_20260925` / `ct_p17_10_verify_20260925` / `ct_local_93d5cdd`. | **verification-environment discrepancy** — pre-existing, outside P17-K's changed surface | **RECORDED — not fixed here.** Fixing it means changing a pre-existing test fixture or a ratified Gate-4 FK; neither is within P17-K's authorisation. Needs an implementation/PO decision. |
| **P17K-F2** | **Citation correction to `P17-DECISION-03 §12.1`.** The tenant applicability column is **`disclosure_applicability_assessments.assessed_status`** (CHECK `APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`), **not** `applicability_status`. The vocabulary `§12.1` names is correct; only the column name is wrong. Verified via `pg_get_constraintdef` on the clone. | documentation | **RECORDED.** `DECISION-03` is a committed freeze and was **not** edited by this task (`§18.4`). |
| **P17K-F3** | **Self-caught implementation defect** — the Scope 3 `CROSS JOIN` without a `category` predicate produced a catalogue of the right size and the wrong content. Fixed at statement level **and** guarded by a rollup post-condition. | **high** (silent wrongness) | **FIXED + TESTED** (§6.2) |
| **P17K-F4** | **Post-condition robustness** — an unscoped `count(*)` post-condition raises a false alarm in any database holding unrelated requirement rows. Scoped to the evidenced framework version. | medium | **FIXED + TESTED** (§17.2) |

---

## 19. Remaining limitations

Each limitation states what it does and does not affect, and whether a decision is
needed.

| ID | Limitation | Effect | Needs a PO decision? |
|---|---|---|---|
| **L-1** | **`STRUCTURED_INPUT_REQUIRED` is not used at category level.** `DECISION-03 §11.2` writes the governed capability for `PARTIAL` categories as `PARTIALLY_SUPPORTED` **/ `STRUCTURED_INPUT_REQUIRED`**. P17-K persisted the **`M-1` arrow** (`PARTIALLY_SUPPORTED`) for the category — an *implementation decision* within the frozen contract (`M-1` is the mapping rule; the slash form is an allowance for a sub-requirement's input dependency). The alternative is neither an upgrade nor a downgrade, but it is a different axis-meaning | a category whose bounded path depends on customer structured input reads `PARTIALLY_SUPPORTED` rather than `STRUCTURED_INPUT_REQUIRED` | No; **recorded** so the choice is visible and reversible only by a recorded decision |
| **L-2** | **Companion standards have no version rows.** The Scope 2 Guidance (2015) and the Corporate Value Chain (Scope 3) Standard are named in `source_locator` but not as `disclosure_framework_versions` rows, because the evidence record supplies no authoritative version label/date for them (`PQ-6` forbids inventing one) | a reader cannot query "which Scope 3 Standard version" as a first-class row | Needs the **PO-confirmed authoritative-evidence list** `PQ-6` requires |
| **L-3** | **`authoritative_source_date` is NULL** on the framework version row (the edition is named in `version_label`; no machine-checkable publication date exists in the evidence record) | D17's source date is not machine-asserted | Same list as L-2 |
| **L-4** | **`disclosure_requirement_mappings` = 0 rows.** Every catalogue requirement is **UNMAPPED**, so a projection today correctly yields an honest `UNRESOLVED`/reasoned value rather than a number (`disclosure_projection.unmapped_decision`) | capability is now **stated**; no value can yet be **produced** from the catalogue | No — that is B3 deliverable C / a later task; P17-K was not authorised to create mappings |
| **L-5** | **`disclosure_purpose_requirements` = 0 rows.** No requirement is bound to a report purpose | the catalogue is not yet reachable *per purpose* | No — B3 deliverable E |
| **L-6** | **The surface-rendering branches of `AG-3`…`AG-8` are PENDING.** They need a capability/investor surface (`§18.1` Tier 3), which this task was explicitly told not to build | the gates are enforced at the catalogue layer only | No — surfaces are a later, gated task |
| **L-7** | **Not promoted to demo or production.** `PR-1`/`PR-2` are satisfied **only** on the disposable clone | demo/production still show the pre-P17 state | No — this is the **deployment gate** (`§18.1` Tier 1 item 5), by design |
| **L-8** | **`PR-3` / `P17-J` outstanding** — no Scope 2 end-to-end runtime acceptance | no claim is made that a Scope 2 run is accepted | No — separate task |
| **L-9** | **`P17K-F1`** — the P17-09/10 integration baselines are not reproducible on a current-schema clone | every regression comparison must state which environment it used (done in §17) | **Yes** — fixture vs Gate-4 FK |
| **L-10** | **`P17K-F2`** — `DECISION-03 §12.1` mis-names the applicability column | a reader following `§12.1` literally would look for a column that does not exist | No; corrected here, freeze not edited |

### 19.1 What is deliberately **not** a limitation

* The catalogue is **complete for its scope**: 18 of 18 rows, exact `M-1` image,
  exact 4/6/3/2 rollup, zero duplicates.
* The vocabulary is **exact**: no token added, removed, renamed or reinterpreted;
  the DB CHECK equals the source constant set.
* **No applicability model exists**, and none was created (§14.2).

---

## 20. Investor and customer truth implications

P17-K builds **no surface** (`CM-4`, `§18.1` Tier 3). What it changes is that the
*knowledge the surfaces need now exists, is governed, and is provable*.

### 20.1 What the product can now truthfully answer

> **"What capabilities does CarbonTally offer?"**

| It can now answer | With |
|---|---|
| per-category capability in governed vocabulary | 15 persisted rows, each with a governed `carbontally_capability` |
| the **four-way** split, not a total | 4 / 6 / 3 / 2, derivable and test-locked (`AG-7`) |
| the bounded-scope statement for a `PARTIAL` category | carried on the row (`description`, from `§11.2 prerequisite_work`) |
| the **named prerequisite** for anything not fully supported | carried on the row — satisfying `IT-3`/`IT-5` when a surface arrives |
| Scope 2 **per method** | separate `LOCATION_BASED` / `MARKET_BASED` rows; market-based honestly `NOT_SUPPORTED` |
| **provenance per claim** | `source_locator` + `authoritative_text_ref` + `source_tier = 1` + an explicit unresolved-identifier marker |

### 20.2 What it still cannot answer (and must not pretend to)

| Question | State |
|---|---|
| *"Which Scope 3 categories apply to this customer?"* | **Cannot be answered — by design.** PO-3 refused the concept; the catalogue holds no applicability and no tenant state. Answering it would need a new PO decision (`F-1`) |
| *"How much CO₂e does category N produce for this customer?"* | **Not answerable from the catalogue** — `requirement_mappings = 0` (L-4) and no tenant values exist. A surface must show absence as absence (`S3-5`) |
| *"Is the customer's data complete / material / assured?"* | **Not answerable** — no coverage, completeness, materiality or assurance field exists **anywhere** in the catalogue (checked by `AG-6`), so such an investor claim is structurally impossible to source from it (`F-8`) |

### 20.3 The investor-surface contract is now *sourced*

`DECISION-03 §9.3` requires the investor surface to state *"what is supported …
with bounded-scope wording for `PARTIAL` and a named prerequisite for anything not
supported"*. Before P17-K that content had **no home** — `PR-2` was empty and a
surface would have had to invent it. It now has a governed home.

**This is a prerequisite being met, not a surface being cleared.** `§18.3`'s
rendering branches, `CS-1` (no tenant data) and `IN-2` (a reproducible
provenance-carrying path) remain obligations for the surface task, and `AG-3`…`AG-8`
are reported as PENDING there — not waived here.

---

## 21. Production safety statement

| Guarantee | Evidence |
|---|---|
| **Production was never contacted** | no production DSN exists in this environment; every statement ran against the local Docker cluster `127.0.0.1:54426` |
| **The demo database was not modified** | read-only `pg_dump --schema-only` + `SELECT`. After all work: `orgs=4, snapshots=34, logs=34, tables=141, framework_versions=0, requirement_versions=0, P17 dims=0` — identical to the pre-task state |
| **The demo database's sessions were not terminated** | the `TEMPLATE` clone was abandoned in favour of a schema-only restore rather than killing postgrest/realtime connections |
| **No destructive statement touched a persistent environment** | the harness's `TRUNCATE` ran only inside `ct_p17k_20260926` / `ct_p17k_ctl_20260926`; the live probe against demo was **refused before any statement** |
| **`carbontally_test` untouched** | not used |
| **No new schema in any persistent environment** | the P17 chain + P17-K were applied only to `ct_*` clones |
| **No secrets** | no credential, token, JWT, signed URL, storage path or connection string appears in this report or in the migration |
| **Not pushed** | committed locally only; the branch remains ahead of `origin` |

---

## 22. Commit list

| # | SHA | Scope | Files |
|---|---|---|---|
| 1 | **`4f8853b`** | `feat(p17-k)` — governed capability catalogue migration (18 rows, exact `M-1` image) | `supabase/migrations/20261020000000_p17k_governed_capability_catalogue.sql` (new, 347 lines) |
| 2 | **`ba19ccd`** | `test(p17-k)` — `AG-1`…`AG-8` acceptance gates + the two load-bearing isolation tests; P17-series registration | `backend/tests/unit/data/test_p17k_governed_capability_catalogue.py` (new), `backend/tests/integration/test_p17k_governed_capability_catalogue_runtime.py` (new), `backend/tests/unit/data/test_p17_migrations.py` (modified) — 3 files, `+992 −1` |
| 3 | **`9ae275b`** | `docs(p17-k)` — this implementation report | `docs/architecture/CT-PO-P17-K-GOVERNED-CAPABILITY-CATALOGUE-RUNTIME-DIMENSIONS-20260926.md` (new, 1093 lines) |
| 4 | _this commit_ | `docs(p17-k)` — record the commit SHAs in the report | this file |

Baseline: `28ff2c0`. All four commits are **local only** (`origin` is 4 commits
behind; **nothing was pushed**).

**Not staged, not committed, not modified:** `.gitignore` (pre-existing
modification) and every pre-existing untracked file (`8`, `=`, `.costrict/`,
`costrict-p3-ov-01-…`, `docs/ChatGPT/*`, and the other pre-existing untracked
planning documents).

---

## 23. Final verdict

### 23.1 Verdict

> ## `P17_K_IMPLEMENTATION_COMPLETE`
>
> **With `IMPLEMENTED` / `TESTED` / real-PostgreSQL `VERIFIED` distinguished
> exactly as the tables above state, and with the surface-rendering branches of
> `AG-3`…`AG-8` and `PR-3`/`P17-J` explicitly NOT claimed.**

### 23.2 Criterion-by-criterion

| Criterion (task §17) | Result |
|---|---|
| migrations safely applied to a disposable verification environment | ✅ 6 migrations, `rc=0`, `0` errors, on `ct_p17k_20260926` |
| required schema verified | ✅ 12/12 columns × 2 tables, 4/4 tables, 12/12 constraints, RLS on all checked |
| governed catalogue populated | ✅ 18 rows (1 framework version + 18 requirement rows) |
| exact seven-value vocabulary verified | ✅ DB CHECK **set-equals** `CARBONTALLY_CAPABILITIES`; 4 of 7 used, 3 deliberately unused and documented |
| all required category mappings verified | ✅ 15/15, exact `M-1` image, 0 `EXCEPT` violations |
| `AG-1` … `AG-8` pass | ✅ at the catalogue/projection layer (46 gate tests across 2 suites); **surface branches PENDING**, declared |
| real PostgreSQL verification pass | ✅ checks A–M of §16 |
| tenant isolation pass | ✅ no tenant key, no tenant FK, identical payload under two tenant contexts |
| P17 regression green against known baseline | ✅ P17 unit selection green; P17-09/P17-10 green on the baseline environment **before and after** this change; wider unit = the **known 9** (proven pre-existing), **not** claimed green |
| no applicability model introduced | ✅ 0 new tables; `NOT_APPLICABLE` class unused; no applicability vocabulary |
| no production contact | ✅ **NO** |

### 23.3 What "COMPLETE" does **not** mean

Using `AGENTS.md §73` language, for the avoidance of doubt:

* It does **not** mean the wider unit suite is green — the known **9** failures
  remain (§18) and are reported, not hidden.
* It does **not** mean any customer or investor surface conforms to the contract —
  **no such surface exists** (`§18.1` Tier 3).
* It does **not** mean Scope 2 or Scope 3 produce accepted end-to-end results —
  `PR-3`/`P17-J` is outstanding and no runtime result is claimed.
* It does **not** mean the catalogue is deployed — demo and production are
  unchanged; promotion is the deployment gate.
* It does **not** mean `P17K-F1`/`P17K-F2` are resolved — both are recorded as open
  findings for a decision.

`IMPLEMENTED`, `TESTED` and `VERIFIED` (against real PostgreSQL) for the P17-K
deliverable. **Not `ACCEPTED`** — acceptance requires an independent check
(`AGENTS.md §60`).

### 23.4 Where the frozen contract now stands

| `DECISION-03` prerequisite | Before P17-K | After P17-K |
|---|---|---|
| **`PR-1`** — P17 schema deltas applied | NOT APPLIED (demo) | **APPLIED + VERIFIED on a disposable clone** (promotion = the deployment gate) |
| **`PR-2`** — governed requirement catalogue authored | **EMPTY — 0 rows** | **18 rows**, exact `M-1` image, exact 4/6/3/2 rollup, provenance on every row |
| **`PR-3`** — Scope 2 E2E (`P17-J`) | OUTSTANDING | **OUTSTANDING** (unchanged, not claimed) |
| `§18.3` gates `AG-1`…`AG-8` | defined, no implementation | **implemented as tests**; catalogue layer VERIFIED, surface branches PENDING |

---

*End of `P17-K`. The task created one reference-data-only migration, two test
modules, one registry edit and this report. No table, column, enum, constraint,
index, policy, grant, API route, UI component or demo row was created, altered or
removed. Production was never contacted; nothing was pushed.*














