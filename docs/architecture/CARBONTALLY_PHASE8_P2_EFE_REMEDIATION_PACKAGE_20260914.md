# CarbonTally — Phase 8 · P2 (EF-E) 
## P2 EF-E REMEDIATION PACKAGE — preparation only

**Task:** `CT-P8-P2-EF-E-REMEDIATION-PACKAGE-PREPARATION` (PO-authorised **preparation only**)
**Date:** 2026-09-14 · **Authority:** PO authorisation "P2 EF-E REMEDIATION PACKAGE PREPARATION" under `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-050`
**Evidence base:** P2 census `CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038.md` · EF-E forensic `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` (§9, §11) · D23 (`CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md:226`) · current code
**Boundary respected:** **no product code, factor data, matching behaviour, migration, DB data or production change was made.** This document prepares the contract; it implements nothing and chooses no new policy.
**Operational invariant (F-046-1):** the integration harness performs destructive setup (`TRUNCATE … RESTART IDENTITY CASCADE`); it must never target a persistent/authoritative database — integration verification below must run against a **disposable clone** (`ct_int_20260914` or a fresh `ct_*`). Enforcement is now in code (`conftest.py` refuses `qa`/`demo`/`investor`/`prod`/`live` targets).
**Phase boundary:** **No Phase 9. Phase 8-X remains inside Phase 8.**

---

## 1. The EF-E defect, restated precisely

**EF-E = selection-side exact-unit equality hides eligible qualifier-bearing factors.**
The factor *vocabulary* contains qualified units such as `kWh (Gross CV)`. A lookup filtered by the *base* unit `kWh` therefore finds **none** of them, because the filter is `ef.unit = <normalised unit>`.

**The decisive asymmetry (newly established by this trace):**

| Side | Behaviour today | Evidence |
|---|---|---|
| **Selection** (`find_by_activity`) | **exact** `ef.unit = $n` unless the caller opts into `unit_substring=True` | `data/emission_factors.py:28-36` |
| **Calculation** (`resolve_unit_for_factor`) | **already qualifier-tolerant**: `if unit in factor_unit_s or factor_unit_s in unit: return factor_unit_s` | `core/units.py`, `resolve_unit_for_factor` |

So once a qualified factor *is* selected, the engine accepts and applies it correctly (`kWh` vs `kWh (Gross CV)`). **EF-E is therefore purely a selection/visibility defect — not a calculation defect** — which bounds the remediation: nothing in the calculation engine, `EmissionFactor.calculate_emissions`, snapshot provenance or artefact integrity needs to change.

**Ratified constraint from D23:** *"`core/units.normalize_unit` — REUSE AS-IS — single normaliser (D23); **do not add a second**."* Any remediation must therefore **reuse** the existing normaliser and must **not** introduce a parallel unit-alias or unit-matching vocabulary (this also satisfies AGENTS §23, "do not duplicate unit-alias logic").

## 2. The three affected paths — traced current behaviour

| # | Path | Surface | Current call | Consequence of EF-E | Severity |
|---|---|---|---|---|---|
| **S1** | `api/v3_emissions.py:549` | `GET /api/v3/factors` — **factor search/browse API** (authenticated org member) | `find_by_activity(query or "", unit=unit, year=…, country=…, provider=…, limit=limit)` → then `filter_factors(...)` | a user filtering by `unit=kWh` **never sees** `kWh (Gross CV)` factors that exist | **High — user-visible invisibility** |
| **S2** | `api/v3_processing_workflow.py:1113` | `GET /items/{item_id}/mapping-options` — the **manual-processing mapping picker** (extraction-derived activity/unit) | `find_by_activity(activity, unit=unit, limit=20)` when `activity` is present, else `[]` | the picker omits eligible qualified factors; worse, the surrounding guidance is computed as `has_factors = bool(factors) or bool(relevant)` → an EF-E miss can produce a **misleading "no factor" dead-end** for a unit that does have (qualified) factors | **High — this is the surface the forensic flagged** |
| **S3** | `services/automatic_processing.py:872` | `_prefer_aggregate_factor(...)` in the **automatic pipeline** | `find_by_activity(activity, unit=unit, limit=20)`, used only to prefer an **aggregate** factor over a per-component sub-factor (`of CH4/N2O/CO2/CO2e per unit`) | if the aggregate candidate is qualified, it is not found, so the pipeline **keeps the sub-component factor** (component-only multiplier) instead of the aggregate | **Medium — mapping *quality*, not a dead end** (guarded: `result.status != "matched"` returns early, exceptions are logged and never break mapping) |

**Not affected (verified, out of scope):** the customer-factor side of S2 is org-scoped by construction — `customer_factor_mapping_options(repos, org_id)` → `repos.customer_factors.get_active_for_org(org_id)` (`api/dependencies.py:388`). The remediation must not touch it.

## 3. Exact matching semantics today

```python
# data/emission_factors.py  (find_by_activity)
if unit is not None:
    unit_norm = normalize_unit(unit) or unit          # D23 single normaliser
    params.append(unit_norm)
    if unit_substring:
        clauses.append(f"ef.unit ILIKE '%' || ${len(params)} || '%'")   # D23 tolerant mode
    else:
        clauses.append(f"ef.unit = ${len(params)}")                     # exact (EF-E)
    unit_match_clause = f"(ef.unit = ${len(params)}) DESC"              # exact first, then year, activity
```

* **Ordering already prefers exact matches** even in tolerant mode (`(ef.unit = $n) DESC`), so tolerance can be added **without disturbing ranking**.
* `unit=None` bypasses the clause entirely → **no EF-E effect when no unit filter is supplied**.
* `normalize_unit` resolves aliases (`L`→`litres`, `m3`→`cubic metres`, …) **before** matching, in both modes.
* Established tolerant usages: `api/v3_operations.py:975` and `:1585` (`unit_substring=True`) — the operator-facing surfaces.


## 4. Evaluation of the D23 `unit_substring` mechanism

| Aspect | Assessment |
|---|---|
| **Semantics** | `ef.unit ILIKE '%' \|\| <normalised unit> \|\| '%'` — case-insensitive substring containment. For `kWh` it finds `kWh`, `kWh (Gross CV)`, `kWh (Net CV)` — the intended qualifier tolerance. |
| **Alias safety** | The pattern is built from the **normalised** unit, so abbreviation hazards are largely removed first (`L`→`litres`, `m3`→`cubic metres`). |
| **Over-match risk (must be handled)** | Blanket substring is **unsafe for short/unaliased units**: a normalised `t`, a bare abbreviation, or any 1–2 character unit could match unrelated vocabulary. This is the mechanism's single greatest risk and the reason the contract pins **scope + normalisation + exact-first ranking**, and offers a stricter alternative. |
| **Consistency with this codebase** | `resolve_unit_for_factor` already implements qualifier tolerance as **containment** (`unit in factor_unit or factor_unit in unit`) on the calculation side — so containment is the *established* semantic here, not a new invention. |
| **D23 constraint** | D23 requires reusing `normalize_unit` as-is and **not adding a second** normaliser; D23's SQL branch is the sanctioned tolerant mechanism and adds no new vocabulary. |
| **Ranking impact** | None — `(ef.unit = $n) DESC` keeps exact matches first, so results stay deterministic and the best factor still surfaces on page one. |
| **Migration/DB impact** | **None** — query construction only; no schema, index, column or data change. |

**Alternative (stricter) semantics — for PO consideration:**
match the base unit **or** the base unit followed by a parenthetical qualifier, i.e. `unit = <base> OR unit ILIKE <base> || ' (%'`. Narrower than substring (it adds qualifier-bearing variants **only**), removes the short-unit over-match risk, and still fixes EF-E for the real vocabulary (`kWh (Gross CV)`). It is not implemented anywhere today, so it would be a **new centralised rule** in `core/units.py` rather than a reuse — a trade-off the PO should weigh.

## 5. The remediation contract (smallest safe change)

**C1 — matching semantics.** For a normalised query unit `u`, `find_by_activity(unit=…)` must return:
1. **exact** matches `unit = u` (unchanged), ranked first;
2. plus, where qualifier tolerance is enabled for that surface, factors whose unit is `u` **plus a qualifier**;
3. **never** factors whose unit is an unrelated unit that merely contains `u` (mitigated by normalisation + the C2 rule choice).

**C2 — qualifier tolerance rule.** Exactly one option, chosen by the PO (no silent pick):
* **Option T1 (reuse D23):** `unit_substring=True` — case-insensitive substring from the normalised unit. Minimal diff; consistent with the two existing tolerant surfaces.
* **Option T2 (strict qualifier pattern, recommended):** one centralised helper in `core/units.py` beside `normalize_unit` (satisfying D23's "single normaliser" rule) producing a qualifier-aware predicate — base unit, or base unit + parenthetical qualifier. No over-match; tiny new surface.

**C3 — ALLOW/DENY behaviour (all must hold).**
* **ALLOW:** filtering `unit=kWh` **sees** `kWh (Gross CV)` where tolerance is enabled; S2's picker returns non-empty candidates and stops emitting a misleading dead-end; S3 can prefer a qualified **aggregate** over a component factor.
* **DENY (unchanged):** genuinely incompatible units must still be excluded — `litres` must never match `kWh (Gross CV)`; currency/spend units must never match physical factors (`CURRENCY_UNITS`, ISC-9/CL-32); `unit=None` must keep bypassing the filter entirely.
* **UNCHANGED:** the calculation engine's `UNIT_MISMATCH` behaviour and `resolve_unit_for_factor` (already tolerant) are **not** modified.

**C4 — cross-tenant isolation (non-negotiable).**
* `emission_factors` is the **global system catalogue** (no `organization_id`), so the change cannot broaden tenant visibility.
* S2's **customer-factor** path (`customer_factor_mapping_options` → `get_active_for_org(org_id)`) is **not modified**; approved customer factors keep org-scoped isolation and D-cf-5 precedence.
* No RLS, grant, policy or organization-boundary mechanism is touched; no service-role shortcut is introduced.

**C5 — expected factor-selection behaviour.**
* Ranking unchanged: exact unit first, then `reporting_year DESC`, then `activity_type` (deterministic).
* S1/S2 return **supersets** of today's results (only previously-hidden qualified factors can appear).
* S3's preference pass may now select a **qualified aggregate** where it previously kept a sub-component factor; it still **never fabricates** a candidate (guards untouched).

**C6 — affected surfaces.** Exactly S1, S2, S3 **+** (Option T2 only) one helper in `core/units.py`. No other endpoint, service, engine, migration or table.

**C7 — regression requirements.** All extraction/mapping/emissions/factor suites stay green; the two existing `unit_substring=True` surfaces keep their behaviour; no existing test weakened or deleted (any amendment must be documented).

**C8 — blast radius.**
* **Product:** factor search (S1), picker candidates + guidance text (S2), automatic aggregate preference (S3). Results can only **gain** hidden candidates; nothing is removed.
* **Data/schema:** **zero** (no migration, no factor-data change, no backfill).
* **Security:** zero tenant-boundary change (C4); negative + cross-tenant tests required (§7).
* **Under-remediation risk:** if tolerance is enabled only on S1/S2, S3 keeps its medium-severity behaviour until separately authorised.

**C9 — migration/database impact.** **None.** No table, column, index, policy, grant, RLS flag or row is touched. F-046-1 therefore applies to the *verification runs* only.


## 6. Implementation specification (for the subsequent, separately-authorised batch)

| # | File | Change | Notes |
|---|---|---|---|
| I1 | `data/emission_factors.py` | when tolerance applies, build the unit clause from the **normalised** unit using the C2 rule; keep exact matches ranked first (`(ef.unit = $n) DESC` **unchanged**). Under Option T2, add the qualifier-aware predicate instead of the blanket `ILIKE '%…%'`. | the only SQL that changes; no schema change |
| I2 | `api/v3_emissions.py:549` | pass tolerance for the factor **search** surface (S1) | gated by §8 D-A |
| I3 | `api/v3_processing_workflow.py:1113` | pass tolerance for the **mapping picker** (S2); the `has_factors` guidance then reflects qualified factors too | highest user impact |
| I4 | `services/automatic_processing.py:872` | pass tolerance for the **aggregate preference** pass (S3) | gated by §8 D-A |
| I5 | `core/units.py` (**Option T2 only**) | add **one** qualifier-aware helper beside `normalize_unit`, reusing the existing alias table — no second normaliser (D23) | Option T1 needs no change here |

**Explicitly NOT changed:** `resolve_unit_for_factor` · `EmissionFactor.calculate_emissions` · the `CURRENCY_UNITS` rule · `customer_factor_mapping_options` / `get_active_for_org` · RLS, grants, policies · any migration · any factor row · any snapshot/provenance path · any frontend.

**Interface stability:** the repository signature already exposes `unit_substring: bool = False`; the specification prefers enabling tolerance **per call site**, so the default stays *exact* and no other caller's behaviour changes silently.

## 7. Verification plan (mandatory for the implementation batch)

**Unit (pure)**
1. `kWh` **matches** `kWh (Gross CV)` under the chosen rule (ALLOW).
2. `litres` **does not match** `kWh (Gross CV)` (**negative**).
3. alias handling: `L` matches `litres`; `m3` matches `cubic metres` (unchanged).
4. `unit=None` produces **no** unit clause (unchanged; negative control).
5. currency/spend units never match physical factors (**negative**, ISC-9/CL-32).
6. Option T2 only: a short/normalised unit such as `t` does **not** over-match unrelated vocabulary (**negative** — the §4 substring risk).

**Integration — disposable clone only (F-046-1)**
7. S1: `GET /api/v3/factors?unit=kWh` returns the qualified factor where one exists (ALLOW), response shape unchanged.
8. S2: `GET /items/{id}/mapping-options` returns non-empty candidates for an extraction-derived base unit and **no longer reports a false dead-end** (ALLOW).
9. S3: a component-factor match is upgraded to the **qualified aggregate** when one exists; when none exists the original result is **preserved unchanged** (negative control).
10. Determinism: exact-unit matches still rank **first**; year/activity ordering unchanged.

**Security — cross-tenant (mandatory)**
11. Org A's picker response contains **no** Org B customer factor (DENY) — customer path untouched.
12. `emission_factors` remains a **global** catalogue read for an authenticated member of any org (no per-org leakage; no RLS/policy change).
13. A caller lacking the required membership still receives **403/404** as today (no authorization change).

**Regression**
14. extraction / mapping / emissions / factor-search / customer-factor suites stay green; the two existing `unit_substring=True` surfaces behave identically.
15. No existing test weakened, skipped or deleted; any amendment documented.
16. Schema parity: **no** migration is added in the remedy batch, so the expected schema delta is **zero** (verify by table/index comparison before and after).

**Target discipline (F-046-1):** items 7–14 must run against a **disposable clone** (`ct_int_20260914` or a fresh `ct_*`); the harness truncates its target and now refuses `qa`/`demo`/`investor`/`prod`/`live` names.

## 8. PO decisions required (the implementation-authorisation gate)

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| **D-A** | **Scope:** which paths receive tolerance? | (a) **S1 + S2 only** (the user-visible surfaces) · (b) **S1 + S2 + S3** | **(b)** — S3's medium-severity "component factor retained" is a real mapping-quality defect and shares the identical mechanism; splitting it means a second batch for the same change |
| **D-B** | **Semantics:** which tolerance rule? | **T1** reuse D23 `unit_substring` · **T2** strict qualifier-aware helper | **T2** — precise, no short-unit over-match, centralised in `core/units.py`, consistent with D23 (it adds a *rule*, not a normaliser). **T1** is acceptable and lower-diff if maximum consistency with the two existing tolerant surfaces is preferred |
| **D-C** | **Case sensitivity:** tolerant matching is `ILIKE` (case-insensitive) while `resolve_unit_for_factor`'s containment is case-sensitive | (a) keep the asymmetry · (b) align the calculation helper later | **(a)** — the calculation side is already tolerant for the real vocabulary; changing it is outside the smallest safe scope |

**No option may be chosen silently; the package stops here.**

## 9. Verdict

### `P2 EF-E REMEDIATION PACKAGE COMPLETE (PREPARATION ONLY) — DEFECT TRACED TO THREE SELECTION-SIDE PATHS, CALCULATION SIDE PROVEN ALREADY TOLERANT, SMALLEST SAFE CONTRACT AND VERIFICATION PLAN SPECIFIED; HOLDING AT THE D-A/D-B/D-C IMPLEMENTATION-AUTHORISATION GATE`

**Nothing was implemented:** no product code, factor data, matching behaviour, migration, DB data or production change. F-046-1 restated and enforced. **No Phase 9; Phase 8-X remains inside Phase 8.**
