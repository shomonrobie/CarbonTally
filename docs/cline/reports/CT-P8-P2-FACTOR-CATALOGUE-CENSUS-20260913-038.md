# CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038

**Task ID:** `CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038` (type **F** — forensic, **read-only**)
**Date:** 2026-09-14 (executed under `CT-P8-CONTINUE-SEQUENTIAL-EXECUTION-20260914-001`)
**Authority:** master execution authorisation + PO continuation instruction naming `…038`
**Environment:** local **non-production** QA database `carbontally_qa_phase8` + local repository · Git HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · no commits
**Tool:** `tools/p2_census/p2_factor_catalogue_census.py` (read-only, reproducible, guards below)

---

## 1. Scope executed

Exactly the task's in-scope list: read-only `SELECT`s against the factor catalogue and the mapping-option query paths, counting factors per activity/unit, exact-vs-substring matching differences, qualified-unit factors excluded by exact-unit equality, and coverage of the extraction label vocabulary — with a structured findings table and the exact queries used. **No write, no factor-data change, no application code change, no migration, no production access.**

## 2. Safety posture — proven, not asserted

| Guard | Evidence |
|---|---|
| Session is **read-only at the database level** | every run executes inside `BEGIN TRANSACTION READ ONLY` |
| **Production is refused** | with `…/carbontally_production` ⇒ `CensusRefused: refusing production-looking database 'carbontally_production'` |
| **Explicit acknowledgement required** | without `CARBONTALLY_P2_CENSUS_ALLOW=non-production` ⇒ `CensusRefused: … no production access is authorised for this task` |
| No secrets emitted | output is counts/vocabularies/paths only (AGENTS §68/§78) |
| Exit status | `CENSUS_EXIT=0` against the non-production QA database |

## 3. Findings — structural (code-level, environment-independent)

| # | Finding | Evidence |
|---|---|---|
| **P2-C1** | **EF-E is structurally live in three product code paths**, each calling `find_by_activity(… unit=unit …)` with **exact** unit equality, so eligible qualifier-bearing factors such as `kWh (Gross CV)` are excluded. | `api/v3_emissions.py:549` · `api/v3_processing_workflow.py:1113` (**the processing mapping picker**) · `services/automatic_processing.py:872` |
| **P2-C2** | **D23's qualifier-tolerant mechanism exists and is applied on two surfaces only.** | `unit_substring=True` at `api/v3_operations.py:975`, `:1585`; parameter + substring branch at `data/emission_factors.py:122/143` |
| **P2-C3** | **Call-site census:** 11 `find_by_activity(` sites — **4 qualifier-tolerant**, **7 exact-only**, of which **3 are product surfaces** (C1) and 4 are test sites (`tests/integration/test_emission_factors.py` ×3, `tests/unit/services/test_automatic_processing.py` ×1). | the census tool's call-site walk |
| **P2-C4** | `units_equivalent` deliberately applies **no** substring/qualifier rule (documenting that the qualifier rule belongs to callers) — so this is a **caller** gap, not a helper bug. | `backend/core/units.py:95–103` |

**Interpretation:** EF-E is **confirmed and still open** as a caller-level defect, and its fix mechanism is **already present**; adopting it on the three product sites is **P2 remediation** and explicitly out of scope here.


## 4. Findings — catalogue data (local non-production; **not** a magnitude measurement)

Exact queries used (all `SELECT`, read-only):

```
SELECT count(*)::int FROM public.emission_factors;                                    -- 15
SELECT count(*)::int FROM public.emission_factors WHERE unit LIKE '%(%';              --  0
SELECT count(*)::int FROM public.emission_factors WHERE unit IS NULL;                 -- 14
SELECT unit, count(*)::int FROM public.emission_factors WHERE unit IS NOT NULL
  GROUP BY unit ORDER BY 2 DESC, unit;                                                -- 1 unit ('kWh')
SELECT count(DISTINCT activity_type)::int FROM public.emission_factors;               -- 15
SELECT reporting_year, count(*)::int FROM public.emission_factors GROUP BY 1;         -- (2025, 15)
SELECT factor_source, count(*)::int FROM public.emission_factors GROUP BY 1;          -- (NULL,14),(DEFRA-DESNZ,1)
SELECT count(*)::int FROM public.emission_factors
  WHERE activity_type ILIKE '%'||$1||'%' AND unit = $2;                               -- exact  = 1
SELECT count(*)::int FROM public.emission_factors
  WHERE activity_type ILIKE '%'||$1||'%' AND unit ILIKE '%'||$2||'%';                 -- substr = 1
```

| # | Finding | Value |
|---|---|---|
| **P2-D1** | local catalogue size | **15 factors**, 15 distinct activities, year 2025 only |
| **P2-D2** | **qualified-unit factors** (the EF-E vocabulary) | **0** — the qualifier population is absent locally |
| **P2-D3** | **NULL-unit factors** | **14 of 15** — a real local data-quality gap, surfaced by the census (recorded, not fixed) |
| **P2-D4** | distinct units | **1** (`kWh`) |
| **P2-D5** | exact-vs-substring delta | **0** for `kWh`; `kWh (Gross CV)` returns 0 in **both** modes |
| **P2-D6** | extraction vocabulary vs catalogue units | 17 extractor tokens; **1 matched** (`kwh`); 16 unmatched (`m3`, `litre`, `kg`, `tonne`, `mile`, `km`, `night`, `therm`, `gallon`, `gbp`, `eur`, `usd`, `£`, `mwh`, `liter`, `ton`) |

**Interpretation (deliberately conservative):** P2-D5's zero delta exists **because the qualifier vocabulary is absent locally — not because EF-E is fixed**. P2-D6's "unmatched" list is dominated by **P2-D3's NULL units**, so it **cannot** separate genuine coverage gaps (**EF-A**) from unit-normalisation gaps (**EF-D**) in this environment. Both remain **unquantified**, and inventing them would violate the task's evidence standard.

## 5. EF-A / EF-D / EF-E separation — as far as the available evidence reaches

| Defect | Status after this census | Basis |
|---|---|---|
| **EF-E** (exact-unit exclusion of eligible factors) | **STRUCTURALLY CONFIRMED, still open; fix mechanism already present** | P2-C1…P2-C4 (environment-independent) |
| **EF-A** (genuine coverage gaps) | **NOT QUANTIFIABLE here** | needs the real catalogue; local catalogue is a 15-row seed with 14 NULL units |
| **EF-D** (unit-normalisation gaps) | **NOT QUANTIFIABLE here** | same dependency; local unit vocabulary is a single value |

## 6. Carried-forward obligations (explicit)

1. **P2 remediation** (separate authorised batch): adopt qualifier-tolerant unit matching on the three product sites (P2-C1) by reusing D23's existing mechanism. **Not performed here**; no factor data may change.
2. **Magnitude measurement** of EF-E/EF-A/EF-D requires a **read-only session against the real factor catalogue**, which this task's scope forbids (production boundary). Until then the customer-visible **magnitude remains unquantified**.
3. **P2-D3** (14/15 NULL units) is recorded for the environment/seed owner — it is **not** a claim about production data.

## 7. Repository state

| Item | Value |
|---|---|
| HEAD | `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged) · staged 0 · **no commits** |
| Added by this task | `tools/p2_census/p2_factor_catalogue_census.py` (read-only tool) + this report |
| Product code changed | **none** — no application, test, schema or data change |
| Production | untouched; no migration; no backfill |

## 8. Verdict

### `…038 P2 READ-ONLY CENSUS COMPLETE — EF-E STRUCTURALLY CONFIRMED IN 3 PRODUCT PATHS WITH THE FIX MECHANISM ALREADY PRESENT; EF-A/EF-D MAGNITUDE CARRIED FORWARD (REAL CATALOGUE REQUIRED, PRODUCTION BOUNDARY RESPECTED)`

The census achieved its purpose: it **quantified the structural EF-E exposure exactly**, showed it is **independent** of both the P1 extraction-shape work and the local catalogue's completeness, and it **refused to invent** what only the real catalogue can answer.
