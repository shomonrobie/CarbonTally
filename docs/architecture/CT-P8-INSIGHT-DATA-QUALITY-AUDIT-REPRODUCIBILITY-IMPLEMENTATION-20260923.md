# CarbonTally Insight — P3 Data Quality + Audit/Reproducibility Implementation

Date: 2026-09-23
Package: **P3 — Data Quality + Audit/Reproducibility**
Repository: `/home/shomonrobie/ct_93d5cdd` · Branch: `p8-release-reconciled` · Remote: `github`

## 1. Authorization

PO P3 implementation authorization (2026-09-23): bounded **Data Quality
Intelligence** (family 14) and **Audit/Reproducibility Intelligence** (family 16),
running in parallel with the still-open independent OHD verification of P2.

Constraints honoured: no P2 modification, no new accounting methodology, no
composite quality score, no new answer state, no L7/L8, no billing, no
retained-data mutation, no deployment, no P12, no RAG.

## 2. Starting SHA

`4cd358d` (`docs(p8): record P2 commit SHA and push result in the
temporal-comparison implementation report`) — branch aligned `0 0` with
`github/p8-release-reconciled` before the first edit; P2 present and frozen
(`f2e4568` + migration `20261006000000_p8_insight_temporal_comparison.sql`).

## 3. Final SHA

Recorded in §22 after the P3 commit.

## 4. Files changed

| File | Change |
| --- | --- |
| `backend/domain/insight_quality.py` | **new** — P3 contract: tool names, `MAX_QUALITY_RECORDS`, condition names, bases, pure `order_issue_codes` / `summarise_report` / `snapshot_from_row` |
| `backend/services/insight_tools.py` | +2 `ToolDefinition`s, dispatch branches, `_data_quality`, `_calculation_reproducibility`, `_reproducibility_data`, `_quality_engine`, `_validation_issue_dict`, `_PROVENANCE_CODES`, `_QUALITY_CHECKS` |
| `backend/services/insight_query_planner.py` | P3 intents (`_QUALITY`, `_REPRODUCIBILITY`, `_UUID`), `REASON_SNAPSHOT_REQUIRED`, two bounded plan branches placed **after** the frozen P2 branch |
| `backend/services/insight_interactions.py` | `_PLANNED_TOOLS` += the two P3 tools |
| `backend/domain/insight_interaction.py` | I4 argument allowlists for the two P3 tools |
| `supabase/migrations/20260923000000_p8_insight_data_quality_reproducibility.sql` | **new** — additive widening of `ci_tool_calls_tool_name_check` 8 → 10 |
| `backend/tests/unit/api/test_p8_insight_data_quality.py` | **new** — 48 P3 tests |
| `backend/tests/unit/api/test_v3_insight_i3_tools.py` | catalogue pin updated to the authorized ten (shared I3 test, not a P2 test) |
| `docs/architecture/CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md` | this report |

No other file changed. `insight_temporal_comparison`, its tests, its migration and
its frontend were not touched.

## 5. P3 capability implemented

Two bounded I3 tools, both read-only, deterministic, organisation-scoped:

1. `insight_data_quality` — a bounded scan of the organisation's stored
   calculations in one explicitly bounded period.
2. `insight_calculation_reproducibility` — the reproducibility/traceability
   conditions of one identified calculation.

## 6. Deterministic quality signals

**P3 invented no quality rule.** Every finding is emitted by machinery that
already existed; P3 only aggregates and projects it:

| Existing mechanism | Findings it produces |
| --- | --- |
| `ValidationEngine.validate_input` (A1) | `VAL_INPUT_ACTIVITY_EMPTY`, `VAL_INPUT_QUANTITY_NEGATIVE`, `VAL_INPUT_YEAR_RANGE`, `VAL_INPUT_UNIT_MISSING` |
| `ValidationEngine.validate_snapshot` (A2) | `VAL_CALC_MISMATCH`, `VAL_CALC_ROUNDING_TOLERANCE`, `VAL_HASH_EMPTY`, `VAL_HASH_MISMATCH` |
| `ValidationEngine.validate_snapshot` (A5) | `VAL_SNAPSHOT_PROVENANCE_MISSING`, `VAL_SNAPSHOT_BATCH_MISMATCH`, `VAL_SNAPSHOT_SOURCE_MISMATCH`, `VAL_FACTOR_ORPHAN` |
| `ValidationEngine.verify_snapshots` (A9) | the existing batch entry point over a snapshot set |

Severity, field and message are the engine's own. The scan performs the A1 input
completeness, A2 recomputation, A2 content-hash and A5 provenance checks, and
states them in `checks_performed`.

Two honesty mechanisms were added after test-driven review:

* the stored `activity` column is validated **as retained** (no fallback to
  `activity_type`), so a populated sibling column cannot mask an empty activity —
  the engine's own empty-activity rule decides;
* when the referenced factor cannot be resolved, the factor-dependent unit rule
  cannot run: the record is counted in `records_with_unresolved_factor` rather
  than silently reported as clean ("not checked" never reads as "checked").


## 7. Reproducibility semantics

Ten named conditions, each a structural presence question or an existing engine
result — none is a new rule:

`calculation_snapshot_retained`, `calculation_result_retained`,
`calculation_inputs_retained`, `factor_reference_retained`,
`methodology_and_algorithm_retained`, `source_lineage_retained`,
`evidence_resolvable`, `recomputation_matches`, `content_hash_matches`,
`factor_provenance_consistent`.

`recomputation_matches` and `content_hash_matches` come from the **existing**
`CalculationEngine.verify` (`VerificationResult.match` / `.tampered` /
`.discrepancy` — Backend v2.1 §13). No second calculation engine and no
reimplemented formula exists in P3.

`reproducible` is `match and not tampered`. A limitation is reported as a
limitation: `unsatisfied_conditions` plus the reason `reproducibility_limitation`.
A non-reproducible result is **not** presented as "incorrect", and nothing claims
certification, audit approval, assurance-readiness or compliance.

## 8. Population/filter semantics

Only two selection surfaces exist, both already bounded by the architecture:

* one inclusive calendar period (`start_date`, `end_date`, required) — the
  existing `validate_period` + `DateRange` semantics;
* one record identifier (`snapshot_id`, required) for the record-level check.

There is no grouping, no dimension selector, no free-text filter, no arbitrary
column, no arbitrary table and no unrestricted search in P3. Supplying an unknown
key is an `invalid_input` rejection. The scan is bounded by
`MAX_QUALITY_RECORDS = 200` (the **existing** I3 result bound, so no new product
limit was invented); exceeding it is reported via `population_truncated` /
`population_exceeds_bound`, and every count describes only the records actually
checked. A grouped scan was deliberately not implemented: the bounded
organisation-scoped snapshot read the contract uses does not expose a
facility/asset dimension, and inventing a wider query was not authorized.

## 9. Tool contract

Both tools are in `TOOL_REGISTRY`, declared `read_only=True`, with an explicit
`ToolInputSpec`, an explicit output-field list and the existing `i2-boundary`
authorization statement. `insight_data_quality` returns `reference_kinds=()`.
`insight_calculation_reproducibility` returns `("calculation_snapshot",
"evidence_line_item")` references. Nothing in either result exposes raw document
text, OCR content, signed URLs or arbitrary database fields.

## 10. Answer-state handling

**No new answer state was added and no existing state changed meaning.** The I4
vocabulary remains the existing statuses; the distinct P3 semantics are carried
by status + reason + structured fields:

| P3 semantic | Representation |
| --- | --- |
| good/verified condition | `success` (`all_checks_passed`, or all conditions satisfied) |
| deficiency | `success` + `reason="findings_reported"` + per-code counts (a finding is the answer, not an error) |
| no data | `no_data` (`no_rows_in_period`, `snapshot_not_found`) |
| not applicable / not checkable | `success` + `checkable=false` / `uncheckable_records` (never a pass) |
| not authorized | `not_authorized` |
| invalid input | `invalid_input` |
| error | existing error path |

## 11. Evidence/provenance path

P3 reuses `insight_aggregate_provenance` (named as `provenance_tool` in the
reproducibility result) and the **existing Shared Source Evidence Viewer** via the
returned `evidence_line_item` reference. Evidence resolvability is established
with the existing `evidence_line_items.count_for_item(source_item_id)` read for
the retained source item. No second evidence viewer, source-document route,
provenance store or audit ledger was created.

## 12. Tenant/security controls

Every read is organisation-scoped: the scan through `search_snapshots(org, …)` /
`count_matching_snapshots(org, …)`, the record check through `get_snapshot` plus
an explicit re-check of the row's `organization_id` against the authenticated
organisation ("a reference is a locator, never a grant"). I2 authorization is
unchanged and runs before execution. Negative coverage: cross-tenant scan,
foreign snapshot identifier, unauthenticated access, foreign evidence key,
injection-shaped keys.

## 13. Rate-limit integration

Both tools execute through the same `invoke_tool` path as the closed INS-01
package and therefore consume the **existing** limiter; no new limiter, no
threshold change, no concurrency change, no commercial quota and no billing
concept. Verified by
`test_quality_route_is_organisation_scoped_and_rate_limited` (asserts the shared
allowance was consumed).

## 14. Frontend changes, if any

**None.** The authorization made a minimal `/insight` integration conditional
("if necessary"). Both tools are reachable and usable through the existing
`/insight` interaction surface: the planner plans them, the orchestration
executes them and the narration layer narrates the deterministic result. A
structured P3 detail panel is **not** implemented (see §18) — stated as remaining
work, not claimed as delivered. No investor-demo or Demo Lab change.

## 15. Tests added

`backend/tests/unit/api/test_p8_insight_data_quality.py` — **48 tests**:
healthy record; empty activity; missing unit; unit rule not claimed without a
resolvable factor; recomputation mismatch; content-hash mismatch; A5 provenance
missing; multiple independent findings on one record; existing QC (open Issue)
count; combined findings; empty population; multi-record deterministic counts;
deterministic ordering; bound + truncation; over-bound rejection; checks stated;
reproducible calculation; missing replay input; unresolvable lineage; existing
mismatch comparison; tamper evidence; missing historical factor reported not
fabricated; evidence resolution; narration-boundary counts; deficiency never a
positive claim; no composite score; not-checked never passed; four planner
intents; P2/preexisting planner behaviour unchanged; pure-helper determinism;
`snapshot_from_row` refusal; migration static checks; catalogue contents.

## 16. Tests executed

P3 suite: **48 passed / 0 failed**.

Insight regression (P3 + P2 + P8 analytics + I1–I5 + migration/authorization/
planner suites, 13 files, 299 tests): **298 passed / 1 failed** (§17).

## 17. Baseline vs HEAD failures

| Failure | Status | Assessment |
| --- | --- | --- |
| `test_p8_insight_temporal_comparison.py::test_the_catalogue_gained_exactly_one_tool` — `assert len(TOOL_REGISTRY) == 8` | **newly failing, P3-induced** | A **P2-owned count pin** that a subsequent *authorized* package necessarily invalidates (P2 asserted "exactly one tool was added by P2"; P3 added two more under separate authorization). §25 forbids P3 from modifying P2 tests, so it is **left failing and reported** rather than silently re-pinned. Resolution belongs to the PO/P2 owner (re-pin the count, or re-express it as "the P2 tool is present"). No P2 behaviour is broken: P2's functional tests all pass. |
| `test_d17_provider_ownership_migration_revision.py` — stale migration-count pin (assert 80 == 71) | pre-existing (D-29), unchanged | Not touched; the new P3 migration adds one more file that the same stale pin would count. Out of P3 scope. |
| `frontend …/dr007-investor-display-fixes.test.jsx` | pre-existing (reproduces with P2 frontend edits stashed) | Not touched by P3 (no frontend change). |

No unrelated failure is hidden and no failure was fixed by weakening a test. The
shared I3 catalogue pin (`test_v3_insight_i3_tools.py`) *was* updated, because
that is the established maintenance action for an authorized catalogue expansion
and it is not a P2-owned test.

## 18. Known limitations

1. **No frontend detail panel** for the two P3 tools (§14) — answers are
   delivered deterministically and narrated, but not yet rendered as a dedicated
   structured panel.
2. **Migration not executed.** F-046-1 forbids pointing the destructive
   integration harness at a persistent database, so
   `20260923000000_p8_insight_data_quality_reproducibility.sql` is verified
   **statically only** (constraint widening; idempotent `DROP … IF EXISTS` +
   `ADD`; no `CREATE TABLE`). Database-level verification remains an integration
   task on a disposable clone.
3. **No grouped quality scan** (§8) — a per-facility/asset breakdown would need a
   dimension the authorized bounded read does not expose.
4. **The A1 unit rule depends on factor resolution** — records whose factor
   cannot be resolved are counted, not judged (§6).
5. **QC state is exposed as the existing open-Issue count**, not a per-severity
   breakdown, because no bounded organisation-scoped per-severity count method
   exists; inventing one was out of scope.
6. **Historical factor history is not created** (no D-13 work): a missing
   historical factor is reported as a limitation, never fabricated.


## 19. Accounting-policy capabilities explicitly not implemented

Not created, decided or implied by P3: Scope 3 Categories 1–15, market-based
Scope 2, location-based Scope 2 methodology, Scope 1 decomposition, supplier
methodology or persistence, primary/secondary factor classification, variance
attribution, reduction methodology, reporting-framework compliance, and any
change to D-09/D-10/D-11/D-12/D-13/D-15/D-18/D-19. P3 inspects the quality and
lineage of data under the rules CarbonTally already has; it decides no accounting
rule. Also not implemented: retention/deletion/legal-hold (L7),
billing/entitlements (L8), P12, RAG, and any deployment.

## 20. P2 interaction/freeze confirmation

`git diff` for `backend/services/insight_tools.py` shows **insertions only** (0
deletions), so no P2 line — including the `_temporal_comparison` docstring — was
altered. `insight_temporal_comparison`, `domain/insight_query.py`,
`insight-comparison.test.jsx`, `InsightComparison.jsx` and
`20261006000000_p8_insight_temporal_comparison.sql` are untouched. P2 functional
tests pass unchanged. The planner's P3 branches are placed **after** the frozen P2
comparison branch, so P2 planning is unaffected (verified by test). The only P3
interaction with P2 is the invalidated P2 count pin (§17) — a test contract, not
behaviour.

## 21. Migration/schema changes

One additive, idempotent migration:
`20260923000000_p8_insight_data_quality_reproducibility.sql`. It widens
`ci_tool_calls_tool_name_check` from the eight authorized names to ten. No new
table, no new column, no new index, no RLS change, no answer-state change, no
quality-score table, no analytics warehouse, no duplicate provenance or audit
store, no data change, no destructive statement.

## 22. Git/push/alignment state

* Implementation commit: **`466c159`** — `feat(p8): bounded Insight data quality +
  audit/reproducibility (P3, families 14 and 16)`, 9 files changed,
  2,031 insertions / 3 deletions (the 3 deletions are the shared I3 catalogue
  pin's three replaced lines). No pre-existing untracked PO/ChatGPT document was
  staged or committed (verified: 0 such paths in the commit).
* Pushed to `github/p8-release-reconciled`: `4cd358d..466c159` (no force).
* Alignment after push:
  `git rev-list --left-right --count HEAD...github/p8-release-reconciled` → `0 0`
  (`HEAD` == `github/p8-release-reconciled` == `466c159`).
* `backend/services/insight_tools.py`: 514 insertions, **0 deletions** — P2 code
  is byte-identical (see §20).

## 23. Verification status

**OHD has NOT independently verified P3.** This is an implementation report: P3 is
implemented and tested by the implementing agent. Independent verification,
acceptance and any closure decision are separate OHD/PO decisions.

**Verdict: P3 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**

