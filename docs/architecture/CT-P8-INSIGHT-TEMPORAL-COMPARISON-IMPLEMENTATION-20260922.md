# CT-P8-INSIGHT-TEMPORAL-COMPARISON — IMPLEMENTATION REPORT

**Document ID:** `CT-P8-INSIGHT-TEMPORAL-COMPARISON-IMPLEMENTATION-20260922`
**Package:** **P2 — Temporal Comparison** (CarbonTally Insight capability family 11)
**Authorization:** PO P2 implementation authorization (2026-09-22), bounded by the P1 capability coverage matrix (`CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md`, family 11 / package P2).
**Repository:** `/home/shomonrobie/ct_93d5cdd` · branch `p8-release-reconciled` · remote `github`
**Starting Git SHA:** `9f32a818692718f5d5aa26f5ca3e540f9c47f4eb`
**Date:** 2026-09-22
**Independent verification:** **NOT YET PERFORMED** — this report is Cline's implementation record only. See §24.

---

# 1. Authorization reference

| Item | Value |
| --- | --- |
| Package | **P2 — Temporal Comparison** (Insight family 11) |
| Authorization | PO P2 implementation authorization, 2026-09-22 |
| Planning artifact | `docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md` (§4 family 11, §9 D-ID register, §10 package sequence) |
| Predecessor | INS-01 (CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED) |
| Scope | bounded, deterministic, tenant-scoped, evidence-aware comparison of **two** explicitly defined periods on the authoritative CO₂e basis |

**Governing decisions applied.** The P2 authorization fixes the comparison semantics itself (two periods, `absolute = period_B − period_A`, `percentage = ((B − A) / A) × 100`, explicit zero-baseline behaviour, bounded grouping, deterministic ordering). It additionally requires that the unresolved parts of **D-11** are *not* invented: see §21.

---

# 2. What was implemented (exact capability)

One new bounded Insight capability, reachable through the existing authorized execution surfaces:

> Compare two explicitly bounded periods on the authoritative kg CO₂e basis, returning both period totals, the absolute change, the percentage change (or a truthful zero-baseline result), the direction, and optional bounded grouping by one supported category dimension.

Constraints held by construction:

* the comparison is **deterministic** — computed in Python from two authoritative repository reads, never by the provider;
* the **provider only narrates** a successful deterministic result (it receives the computed figures as bounded context, §17);
* the basis is **kg CO₂e from `emissions_logs.calculated_kg_co2e`**, the same column the verified aggregation tool uses; no mixed-unit quantity is summed and no factor/activity value is compared directly;
* **no new SQL** was added — the capability reads through the already-verified organisation-scoped `aggregate`, `aggregate_groups` and `group_labels` methods;
* **no new answer state** was introduced (§9);
* **no second evidence viewer, route or reference kind** was introduced (§12).

---

# 3. Files changed

## 3.1 Application code

| File | Change |
| --- | --- |
| `backend/domain/insight_query.py` | added the tool name constant, the closed comparison-dimension vocabulary, direction/percentage-basis constants, the pure `compare_totals` helper, `TemporalDelta`, `validate_comparison_dimension`, `validate_comparison_periods` and `order_comparison_keys` |
| `backend/services/insight_tools.py` | added the `insight_temporal_comparison` `ToolDefinition`, the dispatch branch, `_temporal_comparison`, `_attach_comparison_groups` and `_group_total`, plus the comparison basis string |
| `backend/services/insight_interactions.py` | added the tool to `_PLANNED_TOOLS` so the I4 interaction path can execute it |
| `backend/domain/insight_interaction.py` | added the tool's bounded argument allowlist (`TOOL_ARGUMENT_ALLOWLIST`) so its arguments are persistable and nothing else is |
| `backend/services/insight_query_planner.py` | added the bounded comparison intent (neutral comparison word + exactly two explicit periods from the planner's existing month/year vocabulary) and one clarification reason |

## 3.2 Migration

| File | Change |
| --- | --- |
| `supabase/migrations/20261006000000_p8_insight_temporal_comparison.sql` | **new** — widens `ci_tool_calls_tool_name_check` from seven to eight authorized tool names. Additive, idempotent, no new table/column/index, no answer-state change, no RLS change, no destructive statement. See §22 |

## 3.3 Frontend

| File | Change |
| --- | --- |
| `frontend/src/v3/insight/InsightComparison.jsx` | **new** — the minimal comparison detail (both periods, absolute change, percentage or “not computable”, grouped table, truncation notice, provenance pointer) |
| `frontend/src/v3/insight/InsightInteraction.jsx` | renders `InsightComparison` for the comparison tool call, using the persisted bounded arguments |
| `frontend/src/v3/insight/insight.css` | added comparison styles using the established design tokens |
| `frontend/src/v3/__tests__/insight-comparison.test.jsx` | **new** — 4 frontend tests (§16) |

## 3.4 Tests changed (contract pins an authorized catalogue/migration change must update)

| File | Change | Why it is legitimate |
| --- | --- | --- |
| `backend/tests/unit/api/test_v3_insight_i3_tools.py` | registry expectation 7 → 8 tools | the catalogue contract test must reflect the authorized catalogue |
| `backend/tests/unit/data/test_i1_insight_migration.py` | added the P2 migration to the allowed “migrations after I1” set | the test enumerates authorized additions; INS-01 updated it the same way |
| `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` | “latest migration” expectation updated to the P2 migration | the pin names the latest migration; INS-01 updated it the same way |
| `backend/tests/unit/api/insight_analytics_fakes.py` | additive per-period totals/groups overrides | test support only; existing behaviour unchanged when no override is set |
| `backend/tests/unit/data/test_p8_insight_analytics_sql.py` | added the P2 migration assertions | static migration assertions, no database required |

## 3.5 Files deliberately **not** changed

`backend/data/emissions_logs.py` (no new SQL was needed), `backend/api/**` (no new route, no new endpoint model), `backend/api/insight_authz.py`, `backend/services/insight_rate_limit.py`, `backend/data/insight_rate_limit.py`, `backend/data/insight.py`, `backend/data/insight_interactions.py`, `tools/demo_lab/**`, the investor demo data, and every other module.

---

# 4. Tool contract

| Point | Value |
| --- | --- |
| Name | `insight_temporal_comparison` (defined once in `domain/insight_query.py`) |
| Operation | `temporal_comparison` |
| Purpose | compare two explicitly bounded periods on the authoritative kg CO₂e basis |
| Read-only | **yes** |
| Required inputs | `period_a_start`, `period_a_end`, `period_b_start`, `period_b_end` |
| Optional inputs | `group_by`, `limit` |
| Authorization | `i2-boundary: authorize_insight_scope + organisation-scoped query` |
| Output allowlist | `group_by`, `period_a`, `period_b`, `absolute_change_kg`, `percentage_change`, `percentage_change_available`, `percentage_basis`, `direction`, `groups`, `group_count`, `groups_truncated`, `empty_periods`, `comparison_dimensions`, `basis`, `provenance_tool` |
| Reference kinds | **none** (`()`) — no new reference kind and no inlined contributing record |
| Statuses | the closed I3 set: `success`, `no_data`, `not_authorized`, `invalid_input`, `error` |
| Catalogue size | **eight** tools (four ratified + three INS-01 + this one) |

**The catalogue gained exactly one tool.** No other tool contract, input schema, output allowlist or status vocabulary was modified.

---

# 5. Input / output semantics

## 5.1 Inputs

| Input | Accepted | Rejected |
| --- | --- | --- |
| `period_a_start` / `period_a_end` / `period_b_start` / `period_b_end` | ISO calendar dates (`YYYY-MM-DD`), each period inclusive, each ≤ 3,660 days (`MAX_PERIOD_DAYS`), start ≤ end | any missing bound (`missing_period`), non-date (`invalid_date`), reversed period (`invalid_date_range`), over-long period (`period_too_long`), or a non-string/non-integer value (`invalid_parameter_type`) |
| `group_by` | omitted (= overall comparison), or one of `scope`, `activity`, `facility`, `asset` | anything else → `invalid_input` / `unsupported_group_by` |
| `limit` | omitted (default 50), or 1…50 (`MAX_AGGREGATE_GROUPS`) | out of range / non-integer → `invalid_input` / `invalid_number` |
| any other key | — | rejected outright → `invalid_input` / `unknown_parameter` |

There is **no** free-text input, no SQL, no table/column name, no organisation selector inside the tool input (the organisation comes only from the I2 boundary) and no date-time string.

## 5.2 Output

```text
{
  "group_by": null | "scope" | "activity" | "facility" | "asset",
  "period_a": { "start_date", "end_date", "total_co2e_kg", "row_count" },
  "period_b": { "start_date", "end_date", "total_co2e_kg", "row_count" },
  "absolute_change_kg": "<decimal string>",        # period_B - period_A, always present
  "percentage_change": "<decimal string>" | null,  # six decimals, only when computable
  "percentage_change_available": true | false,
  "percentage_basis": "period_a_total" | "zero_baseline",
  "direction": "increase" | "decrease" | "no_change",
  "groups": [ { key, label, period_a_co2e_kg, period_b_co2e_kg,
                period_a_row_count, period_b_row_count,
                absolute_change_kg, percentage_change,
                percentage_change_available, percentage_basis, direction } ],
  "group_count": <int>,
  "groups_truncated": true | false,
  "empty_periods": [ "period_a" | "period_b", ... ],
  "comparison_dimensions": [ "scope", "activity", "facility", "asset" ],
  "basis": "<kg CO2e basis statement>",
  "provenance_tool": "insight_aggregate_provenance"
}
```

Values are returned as **strings** (decimal fidelity), matching the existing analytics tools. The period totals come from the existing organisation-scoped `aggregate()` read, so they are **complete even when the group list truncates** (honesty is expressed by `groups_truncated`).

## 5.3 Formula (fixed; not configurable)

```text
absolute_change   = period_B_total - period_A_total
percentage_change = ((period_B_total - period_A_total) / period_A_total) * 100   # only when period_A_total != 0
```

The percentage is quantised to six decimal places with `ROUND_HALF_UP`, so repeated identical requests produce identical strings. `direction` is derived from the sign of the same difference and can therefore never disagree with `absolute_change_kg`. Period A is always the **baseline** (for planned questions: the first-mentioned period).

---

# 6. Period semantics

* Periods are **explicit calendar date ranges**, both bounds required, both inclusive — exactly the semantics the verified aggregation contract already uses (the stored `DATE` columns carry no time zone, so a single day is an inclusive one-day range).
* **No time zone conversion** was introduced; **no natural-language date interpretation** happens in the tool. The tool receives already-structured bounds.
* The planner maps only the vocabulary it already understood before P2 — an explicit `Month YYYY` phrase, `YYYY-MM`, or a bare `20xx` year — and derives calendar bounds from it through the existing `_month_bounds` helper. No new date syntax was added, and an out-of-range month is skipped rather than corrected.
* Two periods are required. A comparison question naming fewer than two, or the same period twice, is a **clarification** (`comparison_periods_required`), never a guessed baseline.
* INS-01 discovery remains responsible for bounded *discovery*; P2 does not search for periods.

---

# 7. Zero-baseline semantics (the core truthfulness rule)

| Situation | Result |
| --- | --- |
| `period_A_total == 0`, `period_B_total > 0`, Period A has records | `absolute_change_kg` = B, `percentage_change` = **null**, `percentage_change_available` = false, `percentage_basis` = `"zero_baseline"`, direction `increase` |
| `period_A_total == 0` and `period_B_total == 0`, records exist | `success` with reason `zero_total`; `percentage_change` null; same `zero_baseline` basis |
| Period A has **no records** (`row_count == 0`), Period B has records | `success`; `empty_periods` includes `period_a`; absolute change still reported; percentage **not** computable |
| Period B has no records, Period A has records | `success`; `empty_periods` includes `period_b`; percentage is a genuine `-100.000000` and the zero `row_count` makes the absence visible |
| **Both** periods have no records | `no_data` / `no_rows_in_periods` — an absence of records is never presented as “0 vs 0” |

**No division by zero occurs, no infinite or arbitrary percentage is produced, and no new answer state was added.** The zero-baseline case is expressed with the existing vocabulary plus the explicit `percentage_change_available` / `percentage_basis` fields — which is exactly why a sixteenth state was not needed.

---

# 8. Grouping dimensions

**Supported (closed set):** `scope`, `activity`, `facility`, `asset` — the same organisation-scoped dimensions the verified aggregation tool exposes, on the same expressions (`_ANALYTICS_DIMENSION_EXPRESSIONS`), with labels resolved only from the organisation's own catalogue (`group_labels`; a key with no catalogue row simply has no label — none is invented).

**Deliberately excluded:**

| Excluded | Why |
| --- | --- |
| `month`, `year` | they bucket the very axis the comparison is defined on; two periods would share buckets, so the “change” would be meaningless rather than merely imprecise |
| `supplier` | structurally present, but the emission write path never populates `emissions_logs.supplier_id` (PO C-06 / **D-09** unresolved), so every row falls into the single placeholder bucket `none`. A comparison there would attribute change to a supplier identity that does not exist — the truthful limitation is preserved and supplier comparison waits on D-09 |
| any other value | rejected (`unsupported_group_by`), never silently dropped |

A group present in only one period is still reported, with the other side's authoritative total as zero **and** the per-period row counts that make the absence visible.

---

# 9. Answer-state behaviour (no new state)

| Case | Tool status | Reason | I4 answer state |
| --- | --- | --- | --- |
| ordinary comparison | `success` | — | `success` |
| both period totals genuinely zero (records exist) | `success` | `zero_total` | `zero` (existing mapping) |
| both periods have no records | `no_data` | `no_rows_in_periods` | `no_data` |
| bad/unsupported dimension, bad period, bad limit, unknown parameter | `invalid_input` | machine-readable reason | `invalid_input` |
| the I2 boundary denies the organisation | `not_authorized` | `not_authorized` | `not_authorized` |
| repository/programming failure | `error` | `internal_error` | `error` / `tool_failure` |
| allowance exhausted | — (HTTP 429 before execution) | — | `rate_limited` |
| zero baseline | `success` | — | `success` with `percentage_change_available = false` |

**`AnswerStatus` still holds exactly fifteen values** (`multiple_matches` remains the only analytics-era addition) and `ToolStatus` still holds exactly six; both are asserted by test. No sixteenth state was required, and none was created.

---

# 10. Result bounds

| Bound | Value | Use |
| --- | --- | --- |
| `MAX_AGGREGATE_GROUPS` | 50 | maximum comparison groups returned (shared with aggregation; **unchanged**) |
| `MAX_PERIOD_DAYS` | 3,660 | maximum length of **each** period (unchanged) |
| `MAX_RESULT_ITEMS` | 200 | the existing I3 output bound (unchanged) |
| `MAX_IDENTIFIER_LENGTH` | 128 | the existing input bound (unchanged) |

No bound was increased and no new product limit was invented. Truncation is **detected**, not assumed: each period's grouped read requests `limit + 1` rows, and `groups_truncated` is true when either period had more groups than the bound or when the ordered union exceeds it. The comparison's **period totals remain complete** in the truncated case because they come from the aggregate read rather than from the group list.

**Deterministic ordering.** Grouped output is ordered by the existing aggregation convention applied to the two-period set: the **largest of the two period totals descending**, then `group_key` ascending as the stable tie-break (`order_comparison_keys`). The rule is symmetric in (A, B), so swapping the periods cannot reorder the list; no database-default ordering, no LLM input and no random component is involved.

---

# 11. Evidence / provenance path

```text
comparison result
  → period aggregation (existing organization-scoped aggregate / aggregate_groups)
  → contributing calculation snapshots
  → existing evidence / provenance
  → Shared Source Evidence Viewer
```

* The comparison result carries `provenance_tool = "insight_aggregate_provenance"` plus both **exact** period bounds and the group keys, so every compared cell maps 1:1 onto an existing, already-verified provenance call (grouped: `group_by` + `group_key` + each period's bounds; ungrouped: the same call per group key obtained from the aggregation tool).
* The comparison tool itself returns **no** references and inlines **no** contributing records. This is deliberate: it keeps a single provenance architecture (no second evidence path), keeps the result inside its bound, and preserves the rule that references are locators, never grants.
* **No second evidence viewer, route, permission or RLS rule was created.** The Shared Source Evidence Viewer remains the only evidence destination, reached exactly as before through `insight_aggregate_provenance` → snapshot / evidence-line references.
* The comparison output contains no source text, no storage path, no object key and no URL; DM-6 depth gating is untouched (asserted by test).
* **Verified gap check (required by the authorization):** the existing provenance mechanism *can* express the comparison result without a new contract, because a comparison cell *is* an aggregation cell over a bounded period. No gap was found, so no STOP condition was triggered.

---

# 12. Security / tenant-isolation controls

| Control | Implementation |
| --- | --- |
| Authentication | the existing I3 route dependency (`require_insight_user`) |
| Authorization | `authorize_insight_scope` is resolved for every invocation by `services.insight_tools._authorize`; the tool never decides access itself |
| Organisation scoping | every read is `repos.logs.<method>(organization_id_from_access, …)`; the organisation is **never** taken from the tool input |
| Cross-tenant denial | a caller not authorised for the organisation receives `not_authorized` (tested); an unknown organisation likewise |
| No cross-tenant provenance | the comparison returns no references at all, and the provenance tool it points at is itself organisation-scoped |
| No cross-tenant labels | labels resolve only from `public.suppliers` / `facilities` / `assets` filtered by `organization_id` |
| No arbitrary SQL / identifiers | the dimension must be in the closed comparison vocabulary; all SQL lives in the pre-existing repository methods as fixed literals with positional parameters |
| No unrestricted query string | the input schema is closed; unknown parameters are rejected |
| Bounds | the shared bounds of §10, plus bounded input length |
| Fail-closed | any unexpected exception returns `error` / `internal_error` with diagnostics logged server-side only (tested) |
| No raw content | asserted by test (no source text, storage handle or URL in the output) |
| RLS | unchanged — no policy was added, altered or weakened |

---

# 13. Rate-limit integration

The comparison executes on the **existing** I3 invoke path (`POST /api/v3/insight/tools/invoke`), which already carries the closed INS-01 limiter:

* no new limiter, no separate quota, no threshold change, no concurrency change, no entitlement concept;
* the per-user (20/min, burst 5, cap 25, max concurrent 2) and per-organisation (100/min, burst 20, cap 120, max concurrent 10) limits apply unchanged;
* an exhausted allowance returns **429** with `Retry-After` **before** any comparison read (tested);
* a successful comparison demonstrably consumes the shared allowance (tested), so a new customer-facing execution path that bypassed the limiter would fail these tests.

---

# 14. Frontend changes

Minimal by design — only what makes the capability usable through the existing `/insight` surface:

| Requirement | Implementation |
| --- | --- |
| show Period A / Period B | both periods rendered with dates, totals and a “no records” marker when a side is empty |
| show absolute change | rendered from `absolute_change_kg` with the deterministic direction label |
| show percentage when computable | rendered from `percentage_change` **only** when it exists |
| represent zero-baseline percentage as unavailable | “Percentage change is not computable because the comparison baseline (Period A) is zero” — and **no** percentage is rendered |
| grouped rows | a table with both period totals, the change and the percentage, with “not computable” where no percentage exists; a truncation notice when `groups_truncated` |
| evidence / provenance navigation | the existing references block is untouched; the comparison names the provenance tool and its exact periods |
| loading / empty / error / rate-limited states | `LoadingState`; the tool's own non-success status text; an `Alert` with retry; a 429 surfaces through the existing error path |
| responsive / accessibility | token-based layout, `dt`/`dd` semantics, a real `<table>` with `scope="col"` headers, horizontal scroll at narrow widths |

**No redesign, no new dashboard, no new route, no second evidence viewer.** The detail is re-read through the already-authorized tool endpoint using the arguments the interaction record legitimately persists (PO Q6 metadata), so **no** change to the I4 persistence contract was needed.

---

# 15. Planner / natural-language boundary

* A **neutral** comparison word (`compare`, `compares`, `compared`, `comparison`, `versus`, `vs`, `difference between`, `change between`, `change from`) routes to the comparison contract. **Directional phrasings are deliberately not understood** (“higher than”, “lower than”, “up from”, “down from”): the planner does not interpret comparative direction, so such a question stays unsupported rather than being silently mapped onto a reversed baseline.
* Exactly **two** explicit periods are required, in textual order: the first is Period A (baseline), the second is Period B.
* A comparison word with fewer than two periods — including the same period twice — is a **clarification** (`comparison_periods_required`).
* A detected dimension outside the closed comparison set is an explicit **rejection** (`unsupported_group_by`), not a silently dropped grouping.
* No arbitrary date parsing, no arbitrary numeric parsing, no free-form query construction, no SQL generation, no hidden filter semantics and no inferred accounting classification were added.
* Verified non-regression: plain aggregation, discovery and provenance questions plan exactly as before (tested).

**Behaviour change to note (deliberate and bounded):** before P2, a question containing a comparison word plus a single period (e.g. “compare by facility 2024”) planned a **single-period aggregation**. It now returns a **clarification** asking for two periods. Rationale: silently answering an under-specified comparison request with a single-period total is the less truthful behaviour. No other planning behaviour changed.

---

# 16. LLM narration boundary

| Requirement | How it is held |
| --- | --- |
| the model may narrate a successful deterministic result | the I4 layer passes the bounded tool result to the provider as context |
| the model must not calculate the percentage | the percentage is computed in `compare_totals` and appears in the context already decided (tested) |
| the model must not invent missing values | when no percentage exists the context carries a null percentage plus the `zero_baseline` basis, and no percentage figure is present (tested) |
| the model must not invent causes | the context contains no causal vocabulary and the capability produces no attribution field (tested); causal decomposition is **P9**, not P2 |
| the tool decides validity, not the model | validity, bounds and zero-baseline handling all happen in Python before narration |
| no Scope 3 / market-based Scope 2 / Scope 1 / certification claims | none of those capabilities exists here; the comparison carries no such field and makes no such claim |

---

# 17. Tests added

## 17.1 Backend — `backend/tests/unit/api/test_p8_insight_temporal_comparison.py` (new)

**43 tests.** Structure:

| Group | Coverage |
| --- | --- |
| Pure contract | the formula, positive/negative/no change, six-decimal HALF_UP determinism, zero baseline (single and both), ordering symmetry with the key tie-break, closed dimension vocabulary, period validation |
| Tool behaviour | overall comparison and the full data shape; both periods empty → `no_data`; empty Period A → absolute change with no percentage; empty Period B → −100%; records present but zero totals → `zero_total`; single-day inclusive boundaries; bounded-period rejection; invalid period/dimension/limit; identical requests → identical results |
| Grouped comparison | both periods per group; union semantics with the absent side at zero; label resolution without invention; honest truncation at the shared bound; a limit above the bound refused; per-group zero baseline |
| Evidence | output allowlist; `reference_kinds == ()`; no raw content/storage/URL (plus a structural per-block key assertion); the provenance pointer and a working `insight_aggregate_provenance` handoff for the same period |
| Security | organisation-scoped success; cross-tenant denial; unknown-organisation denial; arbitrary SQL/column/parameter rejection; **429** with `Retry-After` on an exhausted allowance; the comparison consumes the shared allowance |
| Failure | repository failure → `error` / `internal_error` with no internal detail leaked |
| Vocabularies | the eight-tool catalogue; fifteen `AnswerStatus` values; six `ToolStatus` values; the comparison's persistable argument allowlist |
| LLM boundary | the narration context carries the deterministic values and no causal vocabulary; the zero-baseline context carries no percentage |
| Planner | two explicit months; two years; `YYYY-MM`; supported vs refused dimensions; clarification for an under-specified comparison; identical-period collapse; directional phrasing unsupported; non-regression for aggregation/discovery/provenance |

## 17.2 Backend — additions to existing suites

* `backend/tests/unit/data/test_p8_insight_analytics_sql.py` — two static P2-migration assertions (eight names with exactly one widening; additive/idempotent; no answer-state or tool-status vocabulary change).
* `backend/tests/unit/api/test_v3_insight_i3_tools.py` — the catalogue pin updated 7 → 8.
* `backend/tests/unit/data/test_i1_insight_migration.py` — the P2 migration added to the allowed “after I1” set.
* `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` — the “latest migration” pin updated.
* `backend/tests/unit/api/insight_analytics_fakes.py` — additive per-period totals/groups overrides (no behavioural change when unused).

## 17.3 Frontend — `frontend/src/v3/__tests__/insight-comparison.test.jsx` (new)

**4 tests.** Both periods + absolute change + percentage taken from the tool output (with the exact tool and argument re-read asserted); a zero baseline rendered as “not computable” with **no** percentage anywhere; per-group percentage only where computed; a non-success status presented truthfully without any figure.

---

# 18. Tests run — baseline vs HEAD

## 18.1 Method

* **HEAD** = this working tree (starting SHA `9f32a81` + the P2 change).
* **Baseline** = a pristine secondary checkout of `9f32a81` created with `git worktree add` (and removed afterwards), so the comparison uses the real pre-change tree rather than a stash.
* Backend: the complete `tests/unit` tree in both trees (`-q --tb=no`).
* Frontend: the complete jest suite at HEAD, plus a targeted baseline re-run of the one failing suite with the P2 frontend edits stashed.

## 18.2 Backend result

| Environment | Failures |
| --- | --- |
| **Baseline** (`9f32a81`) | **4** — `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`, plus `tests/unit/api/test_review_sla_surfaces.py::{test_canonical_ops_sla_surface_registered, test_canonical_ops_review_assign_registered, test_admin_legacy_compat_surface_retained}` |
| **HEAD** (with P2) | **1** — `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` |

**Interpretation (evidence-based; no claim beyond the evidence):**

* **No P2-caused failure was observed.** Every Insight-related suite passes at HEAD, including the new 43-test suite and the three catalogue/migration pins P2 legitimately updated. The one HEAD failure is the **pre-existing stale migration-count pin** already recorded by OHD and accepted as `D-29`: it asserts `len(migrations) == 71` and fails in **both** environments for that reason (baseline `assert 79 == 71`; HEAD `assert 80 == 71`). P2 changes the observed count by one but not the nature of the failure, and **remediation is not authorized**.
* **The three review-SLA differences are a secondary-worktree artifact, not a code difference.** In the baseline worktree the disputed routes are present when that tree's own `api.router` is imported directly (`/api/v3/ops/sla/settings` present among 320 registered paths), and P2 does not touch `api/router.py`, the ops/admin surface, or any review/SLA module; those tests pass in the primary checkout today. This is recorded as an **observation about the baseline methodology** (a `git worktree` run is not a perfect proxy for the primary checkout) for OHD to reproduce — not as a P2 finding.
* Because of that, the differing failure *counts* are **not** presented as a P2 improvement. The defensible statements are: (a) no new backend failure is attributable to P2; (b) the pre-existing stale-pin failure remains, unremediated.

## 18.3 Frontend result

| Environment | Result |
| --- | --- |
| HEAD, Insight-matching suites | **6 suites / 117 tests — all passed** (includes the new `insight-comparison` suite) |
| HEAD, complete jest suite | **42 suites / 457 tests — 456 passed, 1 failed** |
| Baseline re-run of the failing suite (P2 Insight edits stashed) | **the same failure reproduces** → pre-existing |

**The single frontend failure is pre-existing and unrelated:** `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` → “Issue 3 — customer review detail shows Mapped activity from `mapped_data.activity`” (expected “Natural gas”, received only “Mapped activity”). It exercises the **review-detail display**, which P2 does not touch, and it fails identically with the P2 frontend edits stashed. It is **reported here, not fixed** — remediation is outside the P2 authorization. *(This failure was not part of the previously recorded baseline set; it is newly **observed** here and is flagged for the PO/OHD.)*

## 18.4 What was **not** run, and why

| Not run | Reason |
| --- | --- |
| Database-executing tests (RLS-live, integration harness) | F-046-1: the integration harness performs destructive setup and must never target a persistent database. No disposable database was provisioned for this package, so the migration and SQL were verified **statically only** (§19) |
| Live HTTP end-to-end against a running deployment | no deployment is available in this environment |

---

# 19. Known limitations (stated, not hidden)

| # | Limitation | Consequence |
| --- | --- | --- |
| L-1 | **The P2 migration was verified statically, not executed.** No disposable database was provisioned for this package, so the widened CHECK was asserted only against the migration text. | Live migration-chain application and a schema assertion remain an **integration / OHD task**, exactly as INS-01 required. This is the principal residual verification gap. |
| L-2 | **The SQL itself was not executed.** The comparison reuses the already-verified `aggregate` / `aggregate_groups` / `group_labels` statements and adds none, so no *new* SQL risk exists — but the combination against a real database was not exercised here. | Integration verification. |
| L-3 | **Restatement semantics are not implemented** (D-11 partly unresolved — see §21). | A restated historical period may compare differently from its original publication; the tool does not detect or annotate that, and it says nothing about it. |
| L-4 | The `facility` dimension is snapshot-metadata-derived (the same basis the verified aggregation tool uses) and unattributed rows keep the documented `none` key. | A grouped comparison may contain a `none` bucket meaning “not attributed”; the key is rendered raw, never replaced by a fabricated label. |
| L-5 | Supplier comparison is not offered at all (D-09 unresolved). | Truthful absence rather than a misleading `none`-bucket comparison. |
| L-6 | The comparison is limited to **two** periods. | A multi-period trend is not part of P2 and is not claimed. |
| L-7 | No percentage is produced when the baseline is zero. | Deliberate truthfulness; a different treatment would need a PO decision. |
| L-8 | The planner does not interpret comparative direction. | “higher than” / “lower than” framing is unsupported rather than silently reversed. |
| L-9 | The frontend re-reads the tool result on demand, so a historical comparison is visible only while that tool call remains executable for the organisation. | The answer stays in the interaction record; only the structured detail re-read can fail, and it fails with an explicit, truthful error state. |

---

# 20. Explicitly unimplemented capabilities (not P2)

Confirmed **not** implemented, not touched and not claimed by this package:

* **variance / attribution and any causal decomposition** (P9) — no activity/factor/methodology/boundary/restatement/residual component exists in the output or the narration context;
* **Scope 3 Categories 1–15** (P7) — no taxonomy, no dimension, no assignment rule;
* **Scope 2 market-based** (P8a) — no instruments, no residual mix, no method dimension;
* **Scope 1 decomposition** (P8b) — no stationary/mobile/fugitive/process classification;
* **supplier persistence** (P6) — no write path, no backfill, no `supplier_id` population;
* **factor history / candidate-stage retention** (D-13) — unchanged;
* **data-quality Insight exposure** (P3 / D-14) — unchanged;
* **methodology / boundary model** (family 15) — unchanged;
* **knowledge / RAG (Mode E)**, **reporting-disclosure obligation mapping**, **decision/reduction intelligence** (P10) — unchanged;
* **L7** — retention, deletion, legal hold, erasure, storage lifecycle and Insight-ledger retention untouched;
* **L8** — SLO/SLA, alert thresholds, incident handling, secrets, backup/recovery, commercial billing, payment providers and entitlements untouched;
* **investor demo** — `tools/demo_lab/**`, the investor dataset and the external synthetic-document generator untouched;
* **production deployment** — none;
* **aggregation filtering / cross-tabulation** — not added (would need its own authorization);
* **INS-01 observations** — not reopened, not remediated;
* **the X2/X7 contract records and the pre-existing test failures** — not reconciled, not remediated.

---

# 21. D-11 status and the unresolved restatement limitation

**What D-11 covers** (P1 matrix §9.1; master preflight §12): temporal-comparison semantics — period basis, restatement handling, percentage basis.

| Sub-decision | Status after P2 |
| --- | --- |
| **Percentage formula / basis** | **Resolved by the P2 authorization itself**: `((B − A) / A) × 100`, with explicit zero-baseline behaviour. Implemented exactly; no alternative formula exists anywhere in the code |
| **Period basis** | **Resolved only in the bounded sense the authorization allows**: periods are *explicit calendar date ranges* supplied to the tool, and the planner uses only the pre-existing month/year vocabulary. Reporting-period semantics (e.g. a non-calendar reporting year) are **not** invented and not claimed |
| **Restatement handling** | **UNRESOLVED — deliberately not invented.** The department defines no restatement policy and the repository establishes none, so P2 compares what is *currently* authoritative for each period and **makes no claim** about restatements |

**Consequence, stated plainly:** if historical data has been restated (recalculated, corrected, re-imported, or had records added or removed after the fact), a P2 comparison shows the **current** authoritative totals for both periods and cannot tell the user that one side changed since it was first reported. This is a **known limitation**, recorded here and in the coverage matrix, and it requires a **PO decision (the remainder of D-11)** before it can be addressed.

**The authorization's stop condition was therefore not triggered:** P2 could be implemented correctly *without* inventing a restatement policy, so implementation proceeded and the limitation is recorded rather than papered over.

---

# 22. Migration details

| Item | Value |
| --- | --- |
| File | `supabase/migrations/20261006000000_p8_insight_temporal_comparison.sql` |
| Purpose | widen `ci_tool_calls_tool_name_check` from the seven authorized names to the **eight** now authorized |
| Statements | 2 × `ALTER TABLE public.carbontally_insight_tool_calls` (drop the constraint, re-add it widened) + 1 `COMMENT ON CONSTRAINT` |
| Idempotent | **yes** — `DROP CONSTRAINT IF EXISTS` precedes the re-add, so re-application is safe |
| New tables / columns / indexes | **none** |
| Answer-state vocabulary | **unchanged** — `ci_interactions_answer_status_check` is not referenced |
| Tool-status vocabulary | **unchanged** — `ci_tool_calls_tool_status_check` is not referenced |
| RLS changes | **none** |
| Data change / backfill | **none** |
| Destructive statement | **none** (no `DROP TABLE`, `DROP COLUMN`, `DELETE`, `TRUNCATE`, `UPDATE public.*`, `CREATE TABLE`) |
| Business-data schema change | **none** — no temporal-comparison table, no analytics cache, no materialised view, no new accounting dimension, no new evidence table, no new customer-data column |

Static assertions covering every row above were added to `tests/unit/data/test_p8_insight_analytics_sql.py`. **Live application inside the now-80-file chain remains for OHD** (see L-1).

---

# 23. Git / push / alignment state

| Item | Value |
| --- | --- |
| Starting HEAD | `9f32a818692718f5d5aa26f5ca3e540f9c47f4eb` |
| Branch | `p8-release-reconciled` |
| Remote | `github` |
| Files staged by P2 | only the files listed in §3 (no untracked PO/ChatGPT document is staged) |
| Commit | *(recorded in §23.1)* |
| Push target | `github/p8-release-reconciled` |
| Alignment after push | *(recorded in §23.1)* |
| Working tree after push | the pre-existing untracked PO/ChatGPT documents only |

### 23.1 Recorded outcome

| Item | Value |
| --- | --- |
| P2 implementation commit | `f2e456817e78c4f88e55837129ceefb0e9e90659` |
| Commit subject | `feat(p8): bounded Insight temporal comparison (P2, capability family 11)` |
| Commit content | **17 files, 2,415 insertions, 11 deletions** |
| Push result | `9f32a81..f2e4568  p8-release-reconciled -> p8-release-reconciled` (accepted) |
| Remote SHA after push | `f2e456817e78c4f88e55837129ceefb0e9e90659` |
| `git rev-parse HEAD` | `f2e456817e78c4f88e55837129ceefb0e9e90659` |
| `git rev-parse github/p8-release-reconciled` | `f2e456817e78c4f88e55837129ceefb0e9e90659` |
| `git rev-list --left-right --count HEAD...github/p8-release-reconciled` | **`0 0`** |
| `git status --short` | the pre-existing untracked PO/ChatGPT documents only; no tracked modification outstanding |
| Untracked PO/ChatGPT documents committed? | **no** (`git ls-files` count for those paths = 0) |

---

# 24. Independent verification status

**Independent OHD verification has NOT yet occurred for P2.**

This document is Cline's implementation record. It contains **no** acceptance verdict, no closure claim and no statement of production or investor readiness. Specifically:

* the migration was **not executed** anywhere (L-1) — live application remains unverified;
* the SQL combination was **not executed** against a database (L-2);
* the tenant-isolation cases are verified at the **service/API boundary with doubles**, not against live RLS;
* no live HTTP end-to-end request against a running deployment was made;
* the pre-existing failures (the stale migration-count pin; the DR-007 review-detail assertion) remain **open and unremediated**;
* the three review-SLA differences between the primary checkout and the secondary baseline worktree are recorded as a **methodology observation** for reproduction.

**Method note for the verifier:** the comparison was made against a pristine secondary `git worktree` of `9f32a81`. Because that run produced three failures that do not reproduce in the primary checkout (and whose routes are demonstrably registered by the baseline tree's own code), OHD should prefer either the primary checkout or a **separate clone with its own virtualenv** when attributing failures to a change.

---

**P2 implementation status: IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**
