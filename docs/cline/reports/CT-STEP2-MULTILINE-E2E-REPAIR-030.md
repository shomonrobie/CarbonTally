# CT-STEP2-MULTILINE-E2E-REPAIR-030 — E2E Completion (Objective Defects, Then Calculation → Report → Source)

Bounded task. **No code change was made** — the remaining mapping blocker is now root-caused to an exact
code location, but its resolution requires a PO policy choice (Gross CV vs Net CV), so the calculation-sink
and report stages were deliberately **not** exercised. P1 untouched; no production access.

---

## 1. Task ID

`CT-STEP2-MULTILINE-E2E-REPAIR-030`

## 2–3. Baseline and final SHA

| Item | Value |
| --- | --- |
| Branch / worktree | `p8-release-reconciled` · `/tmp/ct_step2` |
| Baseline SHA (this task) | `b3be14a` (verified `HEAD == origin`, clean) |
| Final HEAD | the report commit (reported in the completion response) |

## 4. 029 findings incorporated

Five-row extraction intact; real service path (`_map` → `FactorMatchingEngine` → index → alias resolver →
`_prefer_aggregate_factor`) exercised over 7,049 real DEFRA-DESNZ 2025 factors; Rows 2/3/4 mapped; Row 3
aggregate preference demonstrably applied; Rows 1 and 5 unresolved; unit safety per 027.

## 5. Objective defects identified (030 adds the precise root cause)

```text
DEFECT (natural gas — CODE DEFECT, root-caused)
  Request: activity 'Natural gas', unit 'kWh'
  NaturalKeyStage.execute() builds the RC2 natural key as
      (reporting_year, activity, country, request.unit or "", request.scope or "")
  and asks the index for an EXACT natural key.  The authoritative factor rows carry the QUALIFIED
  spelling ('kWh (Gross CV)' / 'kWh (Net CV)'), so a request carrying 'kWh' can never match; the keyword
  stage likewise passes request.unit through verbatim.
  The SAME question is answered tolerantly elsewhere in the codebase:
      core.units.unit_matches_with_qualifier('kWh', 'kWh (Gross CV)') -> True
      EmissionFactorsRepository.find_by_activity(..., unit_qualifier_tolerant=True) -> 20 candidates
  So 'kWh' vs 'kWh (Gross CV)' is an ALREADY-ESTABLISHED, documented compatibility (P2 EF-E / D-B T2)
  which the index/search path does not apply  →  the defect is an INCONSISTENT APPLICATION of an existing
  rule, not a missing capability.

REMAINING PRODUCT DECISION (blocks acceptance of the fix)
  Two unit-compatible AGGREGATE natural-gas factors exist, both satisfying the qualifier rule:
      … Natural gas (100% mineral blend) (kg CO2e) [kWh (Gross CV)]   0.18494
      … Natural gas (100% mineral blend) (kg CO2e) [kWh (Net CV)]     0.20489
  Choosing between Gross CV and Net CV for a source row that says only "kWh" is not established by the
  existing policy/data  →  PRODUCT DECISION REQUIRED.  Per §24 I did not invent a Gross-vs-Net preference,
  and per §3 I did not invent a confidence value.

MINIMAL GENERIC FIX IDENTIFIED (not applied in this window)
  Make the index/search path honour the existing qualifier rule — apply
  core.units.unit_matches_with_qualifier to unit filtering (as the repository layer already does with
  unit_qualifier_tolerant=True) instead of comparing 'kWh' to 'kWh (Gross CV)' verbatim.  No new confidence
  convention, no new ranking, no activity special-casing.  Applied WITHOUT the Gross-vs-Net decision it
  would silently select whichever qualified candidate the index enumerates first — an unreviewed change to
  reported emissions, hence the stop.
```

## 6. Objective defects fixed

**None.** The single root-caused code defect cannot be applied safely until the Gross-vs-Net selection is
decided, because the fix alone would make an arbitrary qualified factor selectable. Nothing else met the bar
“objective defect fixable from existing architecture within this window”.

## 7. Natural-gas result

```text
staged matcher                    no_match (0.000)   ← natural-key/keyword unit filter (§5)
_prefer_aggregate_factor          no_match           ← early return on non-matched result (029)
find_by_activity(unit-tolerant)   20 candidates, 8 aggregate, unit-compatible via umq()
selection                         STILL UNRESOLVED — no factor fabricated, row evidence preserved
defect status                     CODE DEFECT root-caused + minimal generic fix identified
policy status                     PRODUCT DECISION REQUIRED (Gross CV vs Net CV)
```

## 8. Power-taxonomy result

Unchanged from 029 and **not** implemented: no existing taxonomy/alias entry establishes that “Power
consumption” denotes one specific canonical electricity activity, and two plausible authoritative targets
exist (`Electricity consumption (kg CO2) [kWh]`, `Gross electricity supply (kg CO2) [kWh]`) with different
scope implications. Per §4 no phrase-specific mapping was added → **TAXONOMY GAP / PRODUCT DECISION
REQUIRED**; Row 5 stays unresolved with its evidence intact.

## 9. Diesel selection analysis (no policy invented)

```text
input            'Diesel' + litres (4434.4)
selected         Bioenergy > Biofuel > Development diesel (kg CO2e) [litres] 0.03705
                 DEFRA-DESNZ / DEFRA-2025 · Scope 1 · 2025 · id c3afa542-1daf-419c-88ea-94252d4dba18
mechanism        matched by the existing staged pipeline at confidence 1.000; aggregate preference changed
                 nothing because the pick is already a whole-gas (non-component) factor
existing rule?   NO rule in code or data establishes that development/biofuel-derived factors are
                 ineligible for a generic "Diesel" activity
status           FACTOR-SELECTION POLICY GAP — left exactly as selected; no ranking invented
```

## 10. Waste selection analysis (no policy invented)

```text
input            'Waste' + tonnes (60)
first match      Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes] 3.5504  (component)
after aggregate  Fuels > Liquid fuels > Waste oils (kg CO2e) [tonnes] 3219.37916               (aggregate)
mechanism        the EXISTING aggregate-preference rule re-selected — it works when a match exists
existing rule?   the code establishes aggregate-over-component; it does NOT establish that "Waste disposal"
                 means waste oils rather than a waste-disposal activity
status           aggregate behaviour VERIFIED; semantic activity choice = PRODUCT DECISION REQUIRED
```

## 11. Authoritative EF evidence

`public.emission_factors` (local authoritative DB via the repository's own `DATABASE_URL`): 7,049 rows,
`reporting_year` 2025, `factor_source` DEFRA-DESNZ, `factor_set` DEFRA-2025 — read-only; nothing created,
modified, substituted or invented.

## 12. Unit compatibility

`kwh→kWh`, `l→litres`, `t→tonnes`, `m³→cubic metres`; every selection inside 027 semantics (same-unit alias
or same-base qualifier); qualifier compatibility via the existing `unit_matches_with_qualifier`; no
cross-family coercion; no physical conversion introduced.

## 13–15. Calculation engine, sink and persisted snapshots — NOT EXERCISED

The real `CalculationEngine` → `EmissionsLogsRepository` sink was **not** run and no snapshot was persisted:

* the mapping state is not yet stable (Rows 1 and 5 policy-blocked; Row 1’s defect pending its policy), so
  persisting calculations would write audit artefacts for a pipeline about to change;
* exercising the sink honestly needs a disposable organisation / extraction-item graph in the local
  database, and building that graph plus report generation plus the bidirectional trace exceeds this bounded
  window;
* consequently `source_item_id` / `source_line_item_id` / `source_ordinal` / `line_number` / `source_line`
  were **not** verified through persisted records here (they remain covered by the 026-verified service path
  and its 16 tests). **No sink or snapshot evidence is claimed.**

## 16–22. Report generation and bidirectional provenance — NOT DEMONSTRATED

No report was generated, so there are no report rows to trace:

```text
actual report                NOT GENERATED
report → calculation         NOT DEMONSTRATED
calculation → source         NOT DEMONSTRATED (no persisted calculation)
source → report              NOT DEMONSTRATED
supplier ('Pure Energy PLC') present in extracted_data; NOT proven at report level
date ('2026-05-08')          present in extracted_data; NOT proven at report level
invoice reference            'Ref No.: PWR/2026/8130' present in the raw document text; NO established field
                             on the mapped/calculated row set — the disappearance point was NOT localised,
                             because the document-metadata → extracted → mapped → calculated → report
                             propagation trace was not completed in this window
```
No metadata, location or provenance value was fabricated anywhere.

## 23. Page / line / row semantics

Kept distinct on every candidate: `line_number` (CarbonTally source line/ordinal), `page` with the honest
`page_basis = "document"` (this text layer has no true page boundary), verbatim `source_line`, and
`source_ordinal` on the mapping entry. No PDF page, invoice line number or table row was manufactured; the
location that cannot be established is reported as unavailable.

## 24. Unresolved / policy-dependent rows

Rows 1 and 5 remain explicit and auditable (description, quantity, unit, `source_line`, ordinal preserved;
no `factor_id`, no calculated emissions; truthful per-line block reason). The three mapped rows are not
erased by them, and no partial mapping is persisted.

## 25. Tests

**No new tests were added**, because no code was modified — asserting a policy I may not choose would be
misleading (§15, §24). Exercised in this window: the real, database-backed, read-only service-path runner
over the authoritative EF dataset (mapping + aggregate preference) and the existing suites (§26–28). No stub
test is presented as real integration.

## 26. 023 regression

Intact — `candidate_lines = 5`, `line_items = 5` on the oracle, source values unchanged.

## 27. 026 regression

`tests/unit/services/test_multiline_provenance_mapping.py` — 16/16 passed (re-run in 029; no code changed).

## 28. 027 regression

`tests/unit/test_units_family_compat.py` + `test_units.py` + `test_units_qualifier.py` — 75 passed, 0 failed.

## 29. 576-PDF regression

**NOT RUN** — no extraction code was touched in 030 (or 029), so the 023 sweep result stands unchanged. This
is stated explicitly rather than assumed current.

## 30. Database environment

Local authoritative database only (`supabase_db_carbon_ledger` on `127.0.0.1`, reached through the
repository's own `DATABASE_URL`), **read-only** in every query this task executed. No migration, no write, no
schema change.

## 31. Production safety

**NO production mutation and NO production deployment** — no production access, uploads, jobs, queue
operations, production DB writes, production report generation, EF changes, configuration/Render/Vercel
changes or deploys. Protected job `9ef61662-1c0a-497a-b5e9-c179e2134784` untouched.

## 32. P1 status

**`shadow`, unchanged** — no rollout flag, allowlist, feature flag or environment variable was modified.

## 33. Commits

No code or test commit. **Report commit only** —
`docs/cline/reports/CT-STEP2-MULTILINE-E2E-REPAIR-030.md`, pushed to `origin/p8-release-reconciled` (SHA in
the completion response).

## 34. Remaining product decisions

1. **Gross CV vs Net CV** for a source row whose unit is the unqualified `kWh` (blocks the natural-gas fix).
2. **Power-consumption synonym** — which canonical electricity activity (and scope) the phrase denotes.
3. **Diesel preference** — may development/biofuel-derived factors satisfy a combustion diesel row?
4. **Waste activity preference** — waste oils vs waste-disposal/landfill for “Waste disposal”.
5. **Invoice-reference semantics** — which existing field should carry `Ref No.` (none established).

## 35. Final verdict

### `PARTIAL`

030 advanced the investigation materially and invented **no** policy: the natural-gas blocker is now
root-caused to an exact code location (natural-key/keyword unit filtering that uses `request.unit` verbatim
while the qualifier-tolerant rule exists and is used elsewhere), the minimal generic fix is identified, and
the reason it must wait is a genuine product decision (Gross CV vs Net CV) that would otherwise silently
change reported emissions. Rows 2/3/4 remain mapped to real authoritative factors, Row 3’s aggregate
preference is verified working, unit safety holds under 027, and Rows 1/5 stay truthful and auditable.

This is **not** `PASS — E2E MULTI-LINE PIPELINE VERIFIED`, because the required end-to-end evidence is
absent: the **calculation sink was not exercised**, **no snapshot was persisted**, **no actual report was
generated**, and **report → source / source → report provenance was not demonstrated**. The failed
all-or-nothing behaviour was not masked by altering product semantics.

## 36. Next PO gate

1. **Decide Gross CV vs Net CV** (or authorise a documented default with rationale). Then apply the
   identified generic fix — qualifier-aware unit filtering in the index/search path — with regression tests
   covering the natural-gas row alongside the existing suite.
2. **Decide the power-consumption synonym** (+ scope), then implement through the existing taxonomy/alias
   mechanism with tests.
3. **Decide the diesel and waste preference rules.**
4. **Decide invoice-reference semantics** (which existing field carries it) — no schema change is authorised
   in this task.
5. Then authorise the completion task: run the oracle through `_calculate` with the **real sink** against a
   disposable organisation/item graph in the local database and **generate an actual report**, proving
   report → snapshot → `source_line_item_id` → source row plus supplier/date traceability.


