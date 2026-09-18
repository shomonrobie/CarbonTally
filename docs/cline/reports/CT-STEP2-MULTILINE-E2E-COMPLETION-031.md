# CT-STEP2-MULTILINE-E2E-COMPLETION-031 — Factor-Set Context, Mapping, Calculation, Report, Provenance

Bounded implementation. **One code change landed** (effective factor-set context). The calculation sink,
report generation and bidirectional provenance were **not** exercised. P1 untouched; no production access.

## 1–2. Baseline / final SHA
Worktree `/tmp/ct_step2`, branch `p8-release-reconciled`; baseline `f11d0db3921282bacdf6481ef456801af6434e80`
(verified `HEAD == origin`, clean); final HEAD = report commit (see completion response).

## 3–7. Factor-set architecture findings (new in 031)
```text
DATA MODEL ALREADY EXISTS: public.emission_factors carries factor_source, factor_set, country;
  data/emission_factors.py reads them; natural key = (year, activity, country, unit, scope);
  find_by_activity(country=…) filters COALESCE(ef.country,'GB').
AUTHORITATIVE SETS (local dataset, read-only): GB | DEFRA-DESNZ | DEFRA-2025 | 7 029  ← DEFAULT
                                                IE | SEAI       | SEAI-2025  |    20  ← alternative
CONTEXT HOOK ALREADY WIRED: MatchRequest.preferred_provider exists and every stage passes it into its
  search call (engines/factor_matching.py:201; engines/matching_stages.py:65,164,261,335).
THE GAP (CODE DEFECT — hard-coded jurisdiction): _map() built MatchRequest(country="GB", …) as a LITERAL
  and never set preferred_provider, pinning the pipeline to GB/DEFRA so an SEAI/IE document could not
  select its set — the "DEFRA assumptions in mapping logic" the PO decision forbids. Generic, not row-specific.
FIX APPLIED (services/automatic_processing.py): DEFAULT_FACTOR_COUNTRY="GB" / DEFAULT_FACTOR_PROVIDER=
  "DEFRA-DESNZ" plus factor_set_context(metadata) resolving document override (factor_country /
  factor_provider) → PO default; _map() now passes the effective country + preferred_provider into
  MatchRequest. No jurisdiction is inferred from activity text; a future set is added as data, not code.
```

## 8–9. Natural gas / Gross-vs-Net
Root cause (030, unchanged): `NaturalKeyStage` composes the RC2 key with `request.unit` verbatim and the
keyword stage filters the same verbatim unit, so `kWh` cannot meet factors keyed `kWh (Gross CV)` /
`kWh (Net CV)` — while the codebase already answers that tolerantly (`unit_matches_with_qualifier` True;
`find_by_activity(..., unit_qualifier_tolerant=True)` → 20 candidates, 8 aggregate).
**NOT FIXED in this window**: the fix touches the shared search/index path used by every match, and after
it the row still presents two unit-compatible aggregates (`… [kWh (Gross CV)] 0.18494`, `… [kWh (Net CV)]
0.20489`), so applying it without the Gross/Net decision would silently select whichever the index
enumerates first. Per §26 that was not invented; row unresolved, ambiguity preserved.
**Largest remaining technical item.**

## 10. Power consumption
No existing taxonomy/alias entry establishes that the phrase denotes one canonical electricity activity;
two plausible targets exist (`Electricity consumption (kg CO2) [kWh]`, `Gross electricity supply (kg CO2)
[kWh]`) with different scope implications → **TAXONOMY GAP / PRODUCT DECISION REQUIRED**; no phrase-specific
mapping added; row preserved unresolved.

## 11–13. Diesel / Waste / Water
```text
Diesel ('Diesel'+litres, DEFRA): Bioenergy > Biofuel > Development diesel (kg CO2e) [litres] 0.03705,
  Scope 1, c3afa542-…, confidence 1.000; aggregate preference changed nothing (already non-component);
  no existing rule excludes development/biofuel factors ⇒ FACTOR-SELECTION POLICY REQUIRED; left untouched.
Waste ('Waste'+tonnes): component CH4 (3.5504) → EXISTING aggregate preference re-selected Waste oils
  (kg CO2e) [tonnes] 3219.37916 — rule verified; semantic choice = PRODUCT DECISION REQUIRED.
Water ('Water'+m³): Water supply (kg CO2e) [cubic metres] 0.1913, Scope 3 — sound.
All rows inherit the SAME effective factor set (org/document level); no per-row mixing introduced.
```

## 14–16. Extraction, real mapping, authoritative EF
Extraction intact (`candidates = 5`, `line_items = 5`, source values unchanged). Real service path
exercised (real engine, stages, index, alias resolver, aggregate preference). EF read-only: 7 049 rows,
2025, sets per §3–7; nothing created, modified, substituted or invented. Units normalise correctly and
selections stay inside 027 semantics (same-unit alias / same-base qualifier); no cross-family coercion.

## 17–21. Calculation / sink / snapshot / provenance — NOT EXERCISED
The real `CalculationEngine` → `EmissionsLogsRepository` sink was **not** run and **no snapshot was
persisted**; factor-set provenance and source identity were therefore **not** verified through persisted
records. Honest reasons: the mapping state is not stable (Rows 1 and 5 policy-blocked), and exercising the
sink + report + bidirectional trace requires a disposable organisation/extraction-item graph in the local
database, which exceeded this task's execution window. Object-level field presence is **not** offered as
persistence or provenance evidence.

## 22–29. Report, supplier/date/invoice, page–line–row
```text
actual report · report→calculation · calculation→source · source→report        NOT DEMONSTRATED
supplier ('Pure Energy PLC') / date ('2026-05-08')  in extracted_data; NOT proven at report level
invoice reference 'Ref No.: PWR/2026/8130'  in raw text; NO established field on the mapped/calculated
  row set — the document→extracted→mapped→calculated→report trace was NOT completed, so the loss point is
  still not localised (no schema change attempted)
page/line/row  distinct and honest: line_number (source ordinal), page=1 + page_basis="document",
  verbatim source_line, source_ordinal on the mapping entry; nothing manufactured
```

## 30. Unresolved rows
Rows 1 and 5 explicit and auditable (description, quantity, unit, `source_line`, ordinal, per-line block
reason; no `factor_id`, no emissions). Mapped rows not erased; no partial mapping persisted.

## 31–35. Tests and regressions
```text
new focused suite tests/unit/services/test_factor_set_context.py — 6 passed (default GB/DEFRA-DESNZ;
  document override IE/SEAI; blank/non-dict tolerance; the _map request carries effective country +
  preferred_provider; no jurisdiction derived from activity text)
tests/unit/services  100% pass (includes the 023 P1 detector suite and the 026 provenance suite)
027 + existing units 100% pass (family-compat + units + qualifier)
023 intact (candidates = 5, items = 5) · 026 green (16 tests) · 027 green (75 tests)
576-PDF corpus  NOT RUN — no extraction code changed; the 023 sweep result is unchanged but is NOT
  re-asserted as current
```

## 36–38. Production / P1 / commits
**No production mutation and no deployment**: no production access, uploads, jobs, queue operations, DB
writes, report generation, EF changes, Render/Vercel/config changes or deploys; protected job
`9ef61662-1c0a-497a-b5e9-c179e2134784` untouched; all DB activity read-only against the **local** database.
**P1 = `shadow`.** Commits: (a) code+test — factor-set context (`services/automatic_processing.py`,
`tests/unit/services/test_factor_set_context.py`), (b) this report.

## 39. Remaining product decisions
1 Gross CV vs Net CV (blocks the natural-gas fix) · 2 power-consumption synonym + scope · 3 diesel
preference · 4 waste activity preference · 5 where the org factor-set setting / document override is
surfaced (pipeline hook now exists and is tested) · 6 invoice-reference field.

## 40. Remaining technical limitations
1 natural-gas qualifier fix identified but unapplied (shared search path; needs §39.1) · 2 sink/snapshot,
report generation and bidirectional provenance not exercised · 3 invoice-reference propagation not
localised · 4 local EF dataset used (production identity not established) · 5 corpus sweep not re-run ·
6 the mapping runner used a non-writing persistence double (mapping decisions real, persistence calls not).

## 41. Final verdict
### `PARTIAL`
One objective defect fixed generically — the effective factor-set context now flows from the document/PO
default into the matching request (constrained, not assumed), with two real factor sets already in the
authoritative data and future sets addable without code change. Extraction, real mapping, real EF matching,
aggregate preference and unit safety remain verified, and unresolved rows stay truthful.
Not `PASS`: the **calculation sink was not exercised**, **no snapshot was persisted**, **no actual report
was generated**, and **no report→source / source→report provenance was demonstrated** — all four are
mandatory PASS conditions; the natural-gas qualifier defect also remains unapplied pending §39.1.

## 42. Next PO gate
1 Decide **Gross CV vs Net CV** (or authorise a documented default); then the identified qualifier-aware
filtering fix can be applied in the shared search path with regression tests — the last mapping blocker for
Row 1. 2 Decide the power-consumption synonym (+scope), diesel preference, waste activity preference and
invoice-reference field. 3 Decide where the org factor-set setting / document override is surfaced.
4 Then authorise the completion task: oracle → `_calculate` with the **real sink** against a disposable
organisation/item graph → **generate an actual report** → prove report → snapshot → `source_line_item_id`
→ source row plus supplier/date traceability, with `factor_set` provenance on every calculation.

