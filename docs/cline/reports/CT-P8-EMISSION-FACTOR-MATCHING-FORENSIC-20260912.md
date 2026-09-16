# CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912

**Task identity:** `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912` (formalized under governance task `CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008`)
**Status:** FORMALIZED FORENSIC RECORD — **READ-ONLY; NOTHING IMPLEMENTED**
**Date:** 2026-09-12
**Repository baseline:** branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c`
**Evidence tags:** **[R]** repository fact · **[V]** verified · **[U]** unresolved · **[I]** interpretation · **[REC]** recommendation

---

## 1. Purpose and read-only nature

This document **formalizes the emission-factor matching forensic findings already established** during
the September-12 2026 Phase 8 investigation (chat-history addendum §§16–22), so they exist as a durable
repository record rather than only as transient investigation output.

**This is NOT a new investigation.** No code was executed, no test was run, no database query was issued.

**Absolute non-goals (respected):** no factor-matching code change; no FactorMatchingEngine change; no
emission-factor data change; no mapping-API change; no schema/migration; no RLS/auth/billing change; no
commit; no push; no implementation prompt.

---

## 2. Evidence sources

| # | Source | Kind |
|---|---|---|
| 1 | `backend/data/emission_factors.py` (`find_by_activity` `:114–168`; `is_active` predicate `:225`) | [R] |
| 2 | `backend/api/v3_operations.py` (`:945–988`, `:1554–1601`, picker inputs `:959–960`) | [R] |
| 3 | `backend/api/v3_processing_workflow.py` (`:1099–1135`, `:1109–1110`, `:1113`) | [R] |
| 4 | `backend/core/units.py` (`UNIT_ALIASES` `:27–78`, `normalize_unit` `:81–92`, `units_equivalent`, `mapping_no_factors_reason` `:156–179`) | [R] |
| 5 | `backend/engines/factor_matching.py` (`FactorMatchingEngine` `:64+`, `build_matching_pipeline` `:292–329`) | [R] |
| 6 | `backend/domain/matching.py` (`MatchingPipelineConfig` `:194–207`) | [R] |
| 7 | `backend/api/dependencies.py` (`:478–488`), `backend/engines/matching_stages.py` (`:34–50`) | [R] |
| 8 | `frontend/src/v3/api.js` (`:559`, `:664`, `:1501`), `frontend/src/v3/ops/ExtractionPanel.jsx` (`:218`), `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` (`:139`, `:579–580`) | [R] |
| 9 | `backend/tests/unit/test_units.py` (`:103`) | [R] |
| 10 | `docs/ChatGPT/chat_history/phase 8 implementaion chat history 01.md` §§16–22 | [V] prior established evidence |

---

## 3. Observed symptom

The processing/mapping surface displayed a "no factors" message for an extracted item. The forensic
finding: **the message was honest and the matcher was not wrong.** For the observed pair
`(activity="Waste", unit="cubic metres")` no valid factor exists in any physical-unit catalogue. The
**input was defective** (a cross-line mixture — see the line-item forensic report). The message is
produced by a messaging helper, not by a matcher error.

---

## 4. Mapping-picker architecture — two separate mechanisms [R]

**The decisive finding: the Mapping-stage picker does NOT use CarbonTally's FactorMatchingEngine.**

```text
extracted.activity / .unit (flat)
  → GET …/mapping-options
  → v3_operations.py:945–988 (ops, entity-scoped)  |  :1554–1601 (ops)
  → v3_processing_workflow.py:1099–1135 (processing / PE / consultant)
  → search_activity = activity or extracted["activity"]
    search_unit     = unit     or extracted["unit"]
  → data/emission_factors.py::find_by_activity(...)   ← DIRECT SQL
       SELECT … FROM emission_factors ef
        LEFT JOIN import_batches ib ON ib.id = ef.import_batch_id
       WHERE ef.activity_type ILIKE '%' || $1 || '%'
         [AND ef.unit ILIKE '%' || normalize_unit($2) || '%']   -- substring
         [AND ef.unit = normalize_unit($2)]                     -- exact
       ORDER BY (ef.unit = $2) DESC, ef.reporting_year DESC, ef.activity_type
       LIMIT 20
  → has_factors = bool(factors) or bool(relevant customer factors)
  → core/units.py:176–179  mapping_no_factors_reason(...)   ← the message helper
```

**"Matching" in the Mapping UI means: one SQL `ILIKE` substring test on `activity_type` plus a unit
predicate. No aliases, no synonyms, no fuzzy, no embeddings, no LLM, no ranking beyond
exact-unit-first and newest-year-first.** [R]

## 5. The six-stage matching engine is NOT used by the picker [R]

- `engines/factor_matching.py::FactorMatchingEngine` + `build_matching_pipeline`;
- stages (`domain/matching.py::MatchingPipelineConfig`): `exact_match`, `natural_key`, `alias_match`,
  `keyword_search`, `fuzzy_match` (+ `semantic_match`, disabled);
- consumers: `POST /api/v2/factor-match` (`api/business.py:70`) and `api/v3_emissions.py:549/608` — the
  **standalone match contract, not the item mapping picker**;
- customer-factor precedence is applied via `CustomerFactorLookup.get_active_for_org`.

**Consequence:** the 8→1 mapping symptom does **not** originate in `FactorMatchingEngine`; the picker
never calls it.

---

## 6. The three mapping-options surfaces — inconsistent unit semantics [R]

| Endpoint | File:line | `unit_substring` | Unit predicate |
|---|---|---|---|
| `GET /api/v3/ops/entities/{e}/extraction/items/{i}/mapping-options` | `v3_operations.py:962` | **True** | `ef.unit ILIKE '%<norm>%'` |
| `GET /api/v3/ops/items/{i}/mapping-options` | `v3_operations.py:1572` | **True** | `ef.unit ILIKE '%<norm>%'` |
| `GET /api/v3/processing/items/{i}/mapping-options` | `v3_processing_workflow.py:1113` | **False (default)** | `ef.unit = '<norm>'` **(exact)** |

`frontend/src/v3/api.js:1501` (`getProcessingMappingOptions`, used by `ProcessingItemWorkspace`) hits the
**exact** surface; `api.js:559/664` (`ExtractionPanel`) hit the **substring** surfaces.

## 7. Factor database vs matcher eligibility [R]

For the picker, "factor exists in the database" ≈ "factor is eligible". The picker's WHERE clause
contains **no** status, version, effective-date, source-activation, scope, gas, geography, year or tenant
filter:

- `year`/`country`/`provider` are optional parameters the three mapping endpoints **never pass** → all
  `None` → clauses omitted (`emission_factors.py:37–45`);
- `import_batches` is a **LEFT JOIN** so batch-less factors are still returned;
- the `is_active` predicate (`emission_factors.py:225`) belongs to a **different query** in the module and
  is **not part of the picker**;
- the global `emission_factors` catalogue is not tenant-scoped; only the *customer* factor list is
  org-scoped and filtered to `status='active'`.

**Therefore the only ways a present factor can fail to appear are:** (1) the activity predicate
(`activity_type` does not contain the extracted label), or (2) the unit predicate (substring vs exact).
This **excludes** status/version/activation/tenant exclusions as causes (and excludes EF-F).

## 8. Unit normalisation findings [R]

`backend/core/units.py`:
- `UNIT_ALIASES` (`:27–78`) — 1:1 alias → canonical (`m3`/`m³` → `cubic metres`; `l`/`litre(s)` →
  `litres`; `t`/`tonne(s)` → `tonnes`; `kwh` → `kWh`; `kwh (gross cv)` → **`kWh (Gross CV)`**; …);
- `normalize_unit` (`:81–92`) — applied **inside** `find_by_activity` before the SQL predicate; unknown
  values pass through unchanged;
- `units_equivalent` + `resolve_unit_for_factor` — used at **calculation** time to handle qualifier cases
  such as `kWh` ↔ `kWh (Gross CV)`.

**Three unit findings:**
1. On the **substring** surfaces, qualified units are included via `ILIKE '%<norm>%'`.
2. On the **exact** surface (`v3_processing_workflow.py:1113`), `ef.unit = '<norm>'` **excludes**
   qualifier-bearing factors such as `kWh (Gross CV)` even though they are compatible — the **EF-E**
   defect.
3. The calculation layer already resolves unit qualifiers, so the exclusion is a **lookup-surface**
   inconsistency, not a calculation defect.

## 9. The EF-E defect [V]

**EF-E — CONFIRMED (independent defect).** The processing mapping surface uses **exact** unit equality
while the other two surfaces (and the calculation-time resolver) are qualifier-tolerant. Result:
compatible factors whose unit carries a qualifier (e.g. `kWh (Gross CV)`) can be silently excluded on that
one surface, producing a misleading "no factors" message for a perfectly valid single-line item.

**Is EF-E independent of the 8→1 extraction defect? YES.** EF-E would affect a **correctly extracted
single-line electricity item** — it does not require any cross-line mixing. It is a factor-side/picker
lookup inconsistency.

---

## 10. Emission-factor forensic classification [V]

| Code | Assessment | Verdict |
|---|---|---|
| **EF-A** — factor genuinely absent | undecidable without live catalogue | **[U]** |
| **EF-B** — factor exists but activity does not match | contributing mechanism | **[V]** |
| **EF-C** — factor exists but unit does not match | contributing mechanism | **[V]** |
| **EF-D** — normalization/mapping insufficient | plausible, unverified | **[U]** |
| **EF-E** — query/filter incorrectly excludes an eligible factor | exact-unit equality on one surface | **CONFIRMED (independent defect)** |
| **EF-F** — importer/data-quality eligibility | **NOT SUPPORTED** — activation does not gate the picker | **Excluded** |
| **EF-G** — frontend/API issue | NOT SUPPORTED (message-quality caveat only) | **Excluded (caveat)** |
| **EF-H** — interaction with line-item extraction/persistence | **PRIMARY for the observed item** | **[V]** |
| **EF-I** — insufficient evidence | partial (live-catalogue questions only) | **[U]** |

**Conclusion for the observed item:** **EF-H (primary) + EF-B/EF-C (mechanism) + EF-E (independent
confirmed defect)**, with EF-D plausible-but-unverified and EF-A undecidable without database access.

## 11. Why EF-E must remain a separate implementation batch [D/REC]

- Different root cause from the extraction defect (a lookup-surface inconsistency, not extraction).
- Different blast radius (one query surface vs the extraction path).
- Combining them would blur verification: a correct single-line item can fail on EF-E while a
  multi-line item can fail on extraction.
- **EF-E is therefore batch P2; the extraction defect is batch P1.** They must **not** be bundled.

## 12. What is confirmed vs unverified

**Confirmed [V]:** the picker uses direct SQL, not the engine; three surfaces with inconsistent unit
semantics; EF-E exists; the mismatch message is a messaging helper; the matcher was not wrong for the
observed pair; the two issues are demonstrably related in this instance but not wholly reducible to each
other.

**Unverified [U]:** the live `unit`/`activity_type` vocabulary of the imported DEFRA/SEAI data (requires
a read-only DB session); EF-A and EF-D remain open for that reason; whether `is_active` is absent from
every method of the module (stated as "not part of the picker's clause set").

## 13. Recommended bounded remediation [REC]

1. **Factor-catalogue census (read-only `SELECT`s only)** — quantify EF-A vs EF-B/C vs EF-D and quantify
   EF-E (exact vs substring counts for a known unit). **Blocked** on an authorised read-only DB session.
2. **Unify the three mapping-options surfaces on one unit semantic** by passing `unit_substring=True` at
   `v3_processing_workflow.py:1113` so qualified-unit factors are not silently excluded. **Separate
   authorisation required — not implemented.**
3. **Read-only coverage report** for the extraction label vocabulary (separates genuine coverage gaps
   from pair-mismatch symptoms and from the path-dependent `Travel` vs `Business travel` inconsistency).

**No factor data change is authorised by this document.** No code was changed.

## 14. Explicit non-goals

No factor-matching code change; no FactorMatchingEngine change; no emission-factor data change; no
mapping-API change; no schema/migration; no RLS/auth/billing change; no extraction change; no commit; no
push; no implementation prompt.

## 15. Verdict

**`EMISSION-FACTOR MATCHING FORENSIC — FORMALIZED (READ-ONLY, NO IMPLEMENTATION)`**

Preserved conclusions: **the FactorMatchingEngine is NOT the root cause of the 8→1 invoice issue**;
**EF-E is a separate confirmed picker defect**; **EF-E must remain a separate implementation batch (P2)**;
**no factor-data change is authorised**.


