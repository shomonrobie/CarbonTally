# CT-STEP2-MULTILINE-PROVENANCE-MAPPING-026 — Multi-Line PDF → Mapping → EF → Calculation → Report Provenance

Bounded implementation task. P1 was **not** activated; production was **not** touched or verified.

---

## 1. Task ID

`CT-STEP2-MULTILINE-PROVENANCE-MAPPING-026`

## 2. Baseline

| Item | Value |
| --- | --- |
| Branch / worktree | `p8-release-reconciled` · `/tmp/ct_step2` |
| Baseline SHA | `f0c4d76` (`HEAD == origin`, clean at task start) |
| Predecessors | forensic `022`, remediation `023` (`e1f5c9d`), production verification `025` (`PASS`) |
| Not reopened | candidate detection (023) — untouched by this task |

## 3. Code-trace findings (existing chain, traced before editing)

```text
A candidate representation      services/extraction_fidelity.build_line_items()  (P1 line_items[])
B extraction result             services/automatic_extraction._make_extraction_result()
C evidence/provenance           manual_extraction_items + data/evidence_line_items.py (B2 ordinal→line id)
D persistence                   data/document_processing.py (queue metadata, partial_extraction)
E activity normalisation        services/automatic_extraction._detect_activity / core.units
F activity matching             services/automatic_processing._map() → domain.matching.MatchRequest
G factor matching               MatchingEngine (+ _prefer_aggregate_factor); factors / customer_factors
H calculation                   services/automatic_processing._calculate/_calculate_line → CalculationRequest
I calculation provenance        domain/calculation.py (source_item_id, source_line_item_id),
                                calculation snapshots, CalculationMethodology
J report generation             domain/disclosure*.py, services/disclosure_finalisation.py
K report-line provenance        disclosure projection/line-item references (existing)
L source trace-back             job.file_name, source_item_id, source_line_item_id, evidence_line_items
M supplier/date propagation     extracted_data["supplier"|"date"] → header dict in _calculate
```

Existing machinery is complete enough to express the required chain — **no parallel provenance system
was created and no schema change was made.**

## 4. Existing evidence/provenance machinery identified (reused, not replaced)

`extraction_fidelity` coverage + `line_items[]`; `evidence_line_items` ordinal→line-id lookup
(`get_by_ordinals`); `ManualExtractionItem`/`manual_extraction_items` (extracted/mapped/calculated);
`document_processing_queue.source_item_id`; `CalculationRequest.source_item_id` **and**
`source_line_item_id`; calculation snapshots (dedupe by deterministic request id); factor identity
(`factor_id`, `factor_kind`, `customer_factor_id`); disclosure/report modules.

## 5. Exact first-loss point (proved by trace + failing test, not assumed)

Three connected breaks, all **after** candidate detection:

1. **`extraction_fidelity.build_line_items` (extraction boundary).** A candidate row with a unit but no
   resolved activity keyword carried **no textual evidence at all** (`description` was added only when
   both activity and unit were missing). The row existed with quantity+unit+`source_line` but nothing a
   downstream stage could match on.
2. **`services/automatic_processing._map` (mapping stage).** `activity = line.get("activity")`; with no
   activity the row was appended to `reasons` and **`continue`d without any mapping entry**, so the row
   silently vanished from `mapped_lines` — and because entries were appended positionally without
   identity, the mapping list could drift out of alignment with `line_items` (no `source_ordinal`,
   `line_number` or `source_line` was carried).
3. **`services/automatic_processing._calculate_line` (calculation stage).** The calculation record's
   `activity` was `line["activity"] or header["activity"]` — for a description-only row on a multi-row
   document both are empty, and the engine rejected it:

   ```text
   calculation blocked: line 5: activity must not be empty
   ```

   i.e. **one unresolvable row blocked the entire five-row document at calculation** (reproduced in
   `test_calculation_carries_per_row_provenance` before the repair).

## 6. Implementation changes (generic; no oracle-specific hard-coding)

| File | Change |
| --- | --- |
| `backend/services/extraction_fidelity.py` | every candidate now carries its **literal source description** (source evidence), not only rows that matched nothing — source text only, never a synthesised activity |
| `backend/services/automatic_processing.py` | new module helpers `_line_identity`, `_mapping_input_text`, `_unresolved_mapping_entry`; `_map()` uses the row's own text as mapping input, carries `source_ordinal`/`line_number`/`source_line` on every entry, and records **explicitly unresolved** entries (`status: "unmapped"` + reason, no factor) instead of dropping rows; `_calculate_line()` falls back to the row's preserved source text for the calculation record's `activity` |

No activity name, file name, row count, supplier or invoice value is hard-coded; no factor was invented;
no schema, rollout, EF dataset, report generator or UI was modified.

## 7. Five-row oracle results

```text
5 candidates → 5 distinct line items
source_line == the five source rows, in source order (line_number 1..5)
quantities 5362.2 / 4434.4 / 60.0 / 163.2 / 24620.5
units      kwh / l / t / m³        (canonicalised later: kwh / litres / tonnes / cubic metres)
description carried for all five (including "Power consumption", which has no keyword match)
page = 1 with page_basis = document (no page invented)
```

## 8. Mapping results (row by row)

| # | Row | Mapping input used | Result |
| --- | --- | --- | --- |
| 1 | Gas usage | canonical activity from extraction | mapped (stub engine) |
| 2 | Diesel supply | canonical activity | mapped |
| 3 | Waste disposal | canonical activity | mapped |
| 4 | Water supply | canonical activity | mapped |
| 5 | Power consumption | **literal source description** (no canonical keyword) | reaches the matcher; matched/unmatched is the engine's decision — never fabricated |

Every mapped entry carries `source_ordinal` (1–5), `line_number`, `source_line`, `status`, `factor_id`,
`factor_kind`, `mapping_confidence`, `activity`, `unit`, `methodology`, `stages_executed`. An
unresolvable row yields `{"status": "unmapped", "reason": …, "source_ordinal": n, "source_line": …}`
**without** `factor_id`/`mapping_confidence`.

## 9. Emission factors (per mapped row)

The stub matcher returns one factor; each mapped line records the factor identity it matched
(`factor_id`, `factor_kind`), and the calculation engine resolves that id (`factors.get`) — so the factor
used is traceable from the mapping record and the calculation request. **No factor was created or
altered**; the authoritative EF dataset was not touched.

## 10. Calculation results

`_calculate` now completes for all five rows (`review`), with per-row:

```text
quantity      5362.2 / 4434.4 / 60.0 / 163.2 / 24620.5
source_item_id      "item-1"            (all rows)
source_file         "multi_row_invoice.pdf"
source_line_item_id "line-item-1-1" … "line-item-1-5"   (resolved per ordinal, B2 lookup)
factor              factor identity per request
```

## 11. Report provenance results

**Not exercised end-to-end.** No report was generated in this task (report rendering/UI were out of the
authorised scope). What *is* verified is that every calculation request now carries the identifiers a
report→source trace needs (`source_item_id`, `source_line_item_id`, `source_file`, activity, quantity,
unit, factor identity) and that the existing disclosure/report modules consume calculation snapshots.
Report-rendering provenance therefore remains **implementation-supported but not re-verified** — stated
as a limitation, not claimed as done.

## 12. Source → report trace evidence

```text
source line "Waste disposal 60 t €105.8140 €6,348.8400"
  → candidate line_item (#3, quantity 60.0, unit t, source_line preserved)
  → mapping entry (source_ordinal 3, line_number 3, source_line, factor_id, status mapped)
  → calculation request (quantity 60.0, source_item_id item-1, source_line_item_id line-item-1-3)
  → calculation snapshot id (engine)
```
Verified by `test_mapping_preserves_each_rows_own_identity` and
`test_calculation_carries_per_row_provenance`.

## 13. Report → source trace evidence

```text
calculation snapshot → source_item_id (extraction item) → evidence_line_items ordinal → line id
                     → source_file (document) → source_line (verbatim source row)
```
The reverse direction resolves through the same three identifiers; asserted on the calculation requests.
`line_number` (extractor order) is carried **separately** from page (`page`/`page_basis`) — line number
is never conflated with a PDF page or a visual table row, and no line number is invented when absent.

## 14. "Power consumption" taxonomy/EF finding

* The row has **no canonical activity keyword** in the current taxonomy
  (`services/automatic_extraction._detect_activity`).
* After this repair the row travels intact (description + quantity + unit + source line) and the
  **existing matcher is asked** about the literal source text; if the engine cannot match it, the row is
  preserved as unresolved and the document routes to manual review with a truthful reason.
* Whether the authoritative factor dataset contains a usable factor for this description was **not
  established here** (no production EF lookup and no real matcher run in this task) — so the honest
  statement is: *`Power consumption` is now reachable and mappable-if-the-data-supports-it; the
  taxonomy/EF coverage question itself remains open* and is proposed as a follow-up rather than invented.

## 15. Tests

New suite: `backend/tests/unit/services/test_multiline_provenance_mapping.py` — **16 tests, all pass**,
covering the required items 1–17 at the level the existing harness supports (five distinct rows; each
row's quantity/unit/description/source evidence; source order; no positional blending; mapping input
contract; identity never invented; unresolved entries carry no factor; mapping identity preservation;
description-only row reaches the matcher; calculation per-row provenance; single-line document
unchanged; shadow mode unchanged).

## 16. Regression results

```text
focused 026 suite                        16 passed
tests/unit/services (all service suites) passed (no failures; includes the 023 P1 suite)
extraction / automatic-processing / parsing suites  passed
tests/unit (broader)                     still running at report time — not used as evidence
integration suites                       NOT run (destructive conftest TRUNCATE, F-046-1)
576-PDF corpus regression                not re-run (candidate detection was not modified by 026
                                         except the additive `description` key; the 023 sweep stands)
pre-existing failures                    none observed; no newly introduced failures
```

## 17. Schema limitations

**None encountered — no schema change was made or required.** The required relationship
(row → mapping → factor → calculation → source) is representable with existing columns/tables
(`document_processing_queue.source_item_id`, `manual_extraction_items`, `evidence_line_items`
ordinals, calculation-snapshot `source_item_id`/`source_line_item_id`). The repairs were
propagation/use repairs, exactly as §5 prefers.

## 18. Unresolved product/data gaps and findings

1. **`Power consumption` taxonomy coverage** — unreachable by keyword; now reachable via its preserved
   source text. Whether a valid factor exists is **not established** (no authoritative EF lookup was
   performed). Needs a taxonomy/EF-coverage decision, not a code invention.
2. **Unit-alias coercion finding (evidence, not fixed).** `core.units.resolve_unit_for_factor` maps
   across unit families:

   ```text
   resolve_unit_for_factor("t",   "litres") -> "litres"      <-- coercion across families
   resolve_unit_for_factor("l",   "litres") -> "litres"      (correct alias)
   resolve_unit_for_factor("m3",  "cubic metres") -> "cubic metres"   (correct alias)
   resolve_unit_for_factor("kwh", "litres") -> "kwh"         (correctly left alone)
   ```

   A `tonnes` row reconciled against a `litres` factor can therefore present a *compatible-looking*
   unit instead of being rejected as a mismatch. This is inside the "unit compatibility" concern of
   this task, but correcting alias semantics changes calculation inputs for every document and requires
   its own bounded fix + tests — **deliberately not changed here** (no silent scope expansion; §16/§17).
   Proposed: `CT-STEP2-UNIT-ALIAS-027`.
3. **Report-rendering provenance** not re-verified end-to-end (§11).
4. **Real world-mapping verification** (real matcher + real EF dataset) was not performed: the focused
   suite uses the established stub-matcher harness. Production verification of this repair, if wanted,
   is a separate bounded task.

## 19. P1 rollout state

**Remains `shadow` — unchanged.** No environment variable, allowlist, `shape_mode`, feature flag or
rollout status was read-as-mutable or written; `services/extraction_fidelity.shape_mode`/`rollout_status`
were not modified by this task (only `build_line_items`' record content). The task exercised the
*internal* pipeline path in tests only, which §12 explicitly permits. Production `shadow` remains as
verified in `025` (`coverage.mode = "shadow"`).

## 20. Production state

**Production was not changed and was not verified by this task.**

```text
production uploads: 0   jobs created: 0   jobs requeued/retried/unlocked: 0
database writes: 0      schema changes: 0  rollouts/flags: 0   EF dataset changes: 0
deployments: 0          config changes: 0  Render changes: 0
protected job 9ef61662-1c0a-497a-b5e9-c179e2134784: untouched (not read, not requeued)
```

## 21. Git commits (this task)

| Commit | Content |
| --- | --- |
| *(implementation)* | `services/extraction_fidelity.py` + `services/automatic_processing.py` — candidate source evidence, mapping row identity/unresolved entries, calculation activity fallback |
| *(tests)* | `backend/tests/unit/services/test_multiline_provenance_mapping.py` (16 tests) |
| *(report)* | this file |

All pushed to `origin/p8-release-reconciled`; the exact SHAs are reported in the completion response.

## 22. Final verdict

### `IMPLEMENTED — PARTIAL`

The existing multi-row chain is demonstrably repaired **through mapping → factor → calculation** (five
candidates reach five identity-preserving mapping entries, and calculations complete per row carrying
`source_item_id`/`source_line_item_id`/factor identity), and the pre-repair failure
`calculation blocked: line 5: activity must not be empty` no longer occurs.

It is **PARTIAL**, not `IMPLEMENTED + VERIFIED`, because:

* **report-generation/report-line provenance was not exercised end-to-end** (§11) — the report stage is
  out of the authorised scope and no report was generated;
* **`Power consumption` factor coverage is unproven** (§14/§18.1) — the row is now reachable, but whether
  the authoritative data supports a mapping is an open product/data question;
* **the unit-alias coercion finding** (§18.2) is recorded, not fixed;
* the **real matcher + real EF dataset** path was not exercised (stub harness only).

## 23. Recommended next PO gate

1. **Accept the mapping/calculation provenance repair** as implemented (row identity + unresolved
   preservation + per-row calculation provenance) with the caveats above; P1 stays in `shadow`.
2. Decide the **`Power consumption`** question: either confirm the canonical activity/factor that should
   serve it (then a bounded generic taxonomy/matcher improvement can be scheduled), or accept it as an
   unresolved row that routes to manual review.
3. Authorise **`CT-STEP2-UNIT-ALIAS-027`** to review and correct `resolve_unit_for_factor` family
   coercion (with regression tests) — this is a calculation-correctness risk independent of this task.
4. If end-to-end report provenance must be proven, authorise a bounded task that generates a report from
   a synthetic multi-row document in a disposable environment and walks report → snapshot →
   `source_line_item_id` → source row.
5. Production verification of this repair remains a separate bounded task (P1 stays shadow; the
   protected job must not be requeued).


