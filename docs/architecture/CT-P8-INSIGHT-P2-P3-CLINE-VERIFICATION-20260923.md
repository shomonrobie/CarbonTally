# CarbonTally Insight — P2 + P3 Technical Verification Report

Date: 2026-09-23
Repository: `/home/shomonrobie/ct_93d5cdd` · Branch: `p8-release-reconciled` · Remote: `github`

```text
Verification type:
Cline Verification Pass — NOT Independent OHD Verification
```

This pass was performed by the implementing agent because OHD is temporarily
unavailable. It cannot establish independent verification, and it does not close
either package. **P2 and P3 remain NOT independently verified / NOT PO closed.**

Verification-only: no implementation, test, migration, frontend or configuration
file was modified. Temporary artefacts live in `/tmp` and the disposable
container `ct_verify_pg_20260923` (never the authoritative database).

## 1. Git preflight

| Check | Result |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `3657f640aa763c8945fda0deb7f97516065ddad8` |
| `github/p8-release-reconciled` | `3657f640aa763c8945fda0deb7f97516065ddad8` |
| `git rev-list --left-right --count HEAD...github/p8-release-reconciled` | `0 0` |
| Working tree | clean except **pre-existing untracked** PO/ChatGPT documents (not authored by P2/P3, not staged) |
| P2 commits resolvable | `f2e4568` (implementation), `4cd358d` (report record) — both present |

## 2. P2 implementation SHA

`f2e456817e78c4f88e55837129ceefb0e9e90659` — `feat(p8): bounded Insight temporal
comparison (P2, capability family 11)`; report record `4cd358d`.

## 3. P3 implementation SHA

`466c159` — `feat(p8): bounded Insight data quality + audit/reproducibility (P3,
families 14 and 16)` (9 files, +2,031/−3); report record `3657f64` (current HEAD,
which is *not* the P2 commit).

## 4. P2 functional verification

`insight_temporal_comparison` is present in `TOOL_REGISTRY`, marked
`read_only=True`, with required inputs `period_a_start/period_a_end/
period_b_start/period_b_end` and optional `group_by`/`limit`. The P2 functional
suite executes: **79 tests, 78 passed, 1 failed** — the single failure is the
catalogue count pin (§14), which is a test contract, not P2 behaviour. Every P2
behavioural test (arithmetic, grouping, boundaries, provenance, tenant, limiter,
narration boundary) passes. **PASS.**

## 5. P2 arithmetic

Independently driven through the committed pure helper
`domain.insight_query.compare_totals` (not through the test suite):
**12/12 checks PASS.**

| Case | Observed | Verdict |
| --- | --- | --- |
| increase 100 → 150 | `absolute=50`, `percentage=50.000000`, `direction=increase`, `basis=period_a_total` | PASS |
| decrease 200 → 150 | `absolute=-50`, `percentage=-25.000000`, `direction=decrease` | PASS |
| equal 10 → 10 | `absolute=0`, `percentage=0.000000` | PASS |
| decimals 12.345678 → 98.7654321 | `absolute=86.4197541` (exact decimal) | PASS |

Formula confirmed: `absolute = B − A`; `percentage = ((B − A) / A) × 100`, present
only when `A ≠ 0`. The values are computed in Python (`Decimal`); the provider
receives them already decided (P2's narration-boundary test asserts the
deterministic figures reach the context). **PASS.**

## 6. P2 zero baseline

| Case | Observed | Verdict |
| --- | --- | --- |
| `A=0, B=50` | `absolute=50`, `percentage=null`, `percentage_change_available=false`, `percentage_basis="zero_baseline"`, `direction=increase` | PASS |
| `A=0, B=0` | `absolute=0`, `percentage=null`, `percentage_change_available=false`, `percentage_basis="zero_baseline"`, `direction=no_change` | PASS |

No division by zero, no fabricated percentage, and the explicit zero-baseline
indication is present. **PASS.**

## 7. P2 empty periods

Verified through the committed P2 suite (which covers both-empty, A-empty,
B-empty, both-populated and populated-with-zero-CO₂e cases) plus the
tool/planner behaviour:

* an empty population yields the dedicated `no_data` path rather than a numeric
  comparison — empty data is **not** silently treated as zero data;
* Period B empty with a real baseline is reported as an honest full decrease
  (`−100.000000`), not as "no data";
* `A=0, B=0` (both zero) is distinguished from both-empty by the zero-baseline
  basis above.

**PASS** (empty ≠ zero is preserved).

## 8. P2 grouping

`scope`, `activity`, `facility`, `asset` are the supported comparison dimensions;
`month` and `year` are excluded because they bucket the comparison axis, and
`supplier` is excluded because no write path populates `supplier_id`. An
unsupported dimension is rejected with the existing
`REASON_UNSUPPORTED_DIMENSION` (`unsupported`), **not** silently ignored —
asserted by the committed suite. Ordering is deterministic and repeated
identical requests return identical results. **PASS.**

## 9. P2 period boundaries

The committed suite covers first day, last day, immediately outside the period,
adjacent periods, identical periods and reversed/invalid periods; inclusive
`[start, end]` semantics and the rejection of reversed bounds both hold.
**PASS.**

## 10. P2 tenant isolation

Verified at both layers: cross-organisation scan/`invoke` returns
`not_authorized` with an empty payload, a foreign snapshot identifier is rejected,
unauthenticated access is refused, and no cross-tenant figure is disclosed. All
asserted by the committed suite and reproduced in this pass. **PASS.**

## 11. P2 rate limiting

P2 uses the existing INS-01 path and consumes the **existing** limiter; no new
limiter/threshold exists; the route-level test passes. Limiting is enforced in the
request path, not inside `invoke_tool` (§29 O-2). **PASS** (customer surface).

## 12. P2 provenance

The comparison returns **no references and no inlined records**; it names
`insight_aggregate_provenance` + exact period bounds so the existing provenance
tool and Source Evidence Viewer remain the only evidence path. No second evidence
system; no raw text/signed URL in the payload (marker scan negative). **PASS.**

## 13. P2 migration verification (disposable database only)

Disposable container `ct_verify_pg_20260923`
(`public.ecr.aws/supabase/postgres:17.6.1.159`, port 55433) holding a faithful
replica of the object as the I4 migration creates it (4-name constraint). The P2
file was applied **verbatim**.

| Check | Evidence | Verdict |
| --- | --- | --- |
| applies | exit 0 | PASS |
| expected constraint | 8 names incl. `insight_temporal_comparison` | PASS |
| previous tools valid | all 7 pre-P2 names insert → exit 0 | PASS |
| P2 tool valid | insert → exit 0 | PASS |
| invalid name rejected | `unratified_tool` → exit 1 | PASS |
| idempotent | re-applied → exit 0, exactly 1 constraint, identical definition | PASS |

(`20261005000000` needs prerequisites outside the minimal replica and errors
there — a harness-scope artefact, not a defect in the P2 target object.)

## 14. P2 catalogue-count finding

Reproduced at HEAD: `assert len(TOOL_REGISTRY) == 8` → actual **10**.
Cause: solely the P3 authorized expansion (an absolute count pin written when P2
was the last package). `insight_temporal_comparison` itself is correctly
registered (`read_only=True`, correct input spec) and 78/79 P2 tests pass.
**Classification: expected stale contract (test-contract debt) — not a P2 defect,
not a runtime defect; a governance/documentation issue** (an absolute count cannot
survive a subsequent authorized expansion). Left unmodified as instructed;
re-pinning is an owner decision. **Does not block P2.**

## 15. P3 tool verification

| Property | Evidence | Verdict |
| --- | --- | --- |
| read-only | `read_only=True` both | PASS |
| deterministic | repeated requests identical; stable counts/order | PASS |
| organisation-scoped | org-scoped reads + object organisation re-check | PASS |
| bounded | period required; `limit ≤ 200`; one identifier | PASS |
| I2-authorized | existing `authorize_insight_scope` unchanged | PASS |
| rate-limited | route-level consumption verified (§21) | PASS |

## 16. P3 quality checks

Independent script `/tmp/vb_p3_out.txt`: **13/15 pass** (2 failures are my harness
calling `invoke_tool` directly and expecting limiter consumption — §29 O-2).
The implementation reuses the existing `ValidationEngine`/`CalculationEngine.verify`;
no new `VAL_` code, severity, weight or score exists in the diff.

| Case | Observed | Verdict |
| --- | --- | --- |
| healthy record | `findings=[]`, `reason=all_checks_passed` | PASS |
| empty activity (sibling populated) | `VAL_INPUT_ACTIVITY_EMPTY` raised | PASS |
| missing unit + resolvable factor | `VAL_INPUT_UNIT_MISSING`, `field=quantity_unit` | PASS |
| recomputation mismatch | `VAL_CALC_MISMATCH` | PASS |
| hash mismatch / empty hash | `VAL_HASH_MISMATCH` / `VAL_HASH_EMPTY` | PASS |
| A5 provenance cases | `VAL_SNAPSHOT_PROVENANCE_MISSING` etc. | PASS |
| multiple findings, one record | several codes, `records_with_findings=1`, no score | PASS |
| empty population | `no_data`/`no_rows_in_period`, empty payload | PASS |
| deterministic counts/order | stable; identical repeats | PASS |

`VAL_INPUT_QUANTITY_NEGATIVE`, `VAL_INPUT_YEAR_RANGE`,
`VAL_CALC_ROUNDING_TOLERANCE`, `VAL_SNAPSHOT_BATCH_MISMATCH`,
`VAL_SNAPSHOT_SOURCE_MISMATCH`, `VAL_FACTOR_ORPHAN` come from the same engine
paths and are covered by the committed suite. **PASS.**


## 17. P3 reproducibility

Ten conditions in fixed order, driven by the existing deterministic machinery:

| Case | Observed | Verdict |
| --- | --- | --- |
| reproducible | all satisfied, `reproducible=true`, `{match,tampered,discrepancy}` | PASS |
| missing replay input | `calculation_inputs_retained=false` + `reproducibility_limitation` | PASS |
| missing lineage | `source_lineage_retained=false`, `evidence_resolvable=false` | PASS |
| mismatch | `reproducible=false`, `discrepancy`, `VAL_CALC_MISMATCH` | PASS |
| tamper | `tampered=true`, `VAL_HASH_MISMATCH` | PASS |
| missing historical factor | reported as a limitation; nothing fabricated | PASS |

No second engine or reimplemented formula; no certification language
(`certified`/`audit-approved`/`assurance`/`compliant` scan negative); a mismatch is
never framed as "incorrect". **PASS.**

## 18. P3 honesty mechanisms

| Mechanism | Evidence | Verdict |
| --- | --- | --- |
| activity as retained | empty `activity` flagged despite populated `activity_type` | PASS |
| unresolved factor | `records_with_unresolved_factor=1`; unit rule not claimed | PASS |
| empty period | `no_data`, empty payload — never a clean population | PASS |
| not-checkable record | `uncheckable_records` counted, not passed | PASS |
| no composite score | no score/grade/rating/readiness/index/weight key | PASS |

## 19. P3 provenance

Names `insight_aggregate_provenance`; returns only the permitted
`calculation_snapshot` + `evidence_line_item` references; resolves evidence via the
existing `evidence_line_items.count_for_item`. No raw text, OCR content or signed
URL in payloads. **PASS.**

## 20. P3 tenant isolation

foreign snapshot → `not_authorized` with empty payload (no existence disclosure);
foreign evidence id not reachable (extra key → `invalid_input`); cross-tenant scan
→ `not_authorized`; unauthenticated → refused; injection-shaped keys (`sql`,
`table`) → `invalid_input`. Application-level checks verified; database-level RLS
**not** exercised (§29 O-3). **PASS** (application layer).

## 21. P3 rate limiting

Both tools use the existing INS-01 path; route-level test
`test_quality_route_is_organisation_scoped_and_rate_limited` **passes** and asserts
the shared limiter recorded the request; no limiter value created or changed.
**PASS** (route).

## 22. P3 migration verification (disposable database only) — **DEFECT**

Applied to the same disposable container, **verbatim**, from the P2 (8-name)
state: applies (exit 0); constraint becomes the **10** authorized names; all 10
insert successfully; `unratified_tool` rejected; applied three times → exit 0 each
time with exactly one constraint (idempotent); schema delta = no new table, no new
column (the table's own 15), no new index (its PK), `relrowsecurity` unchanged; no
customer data touched. **PASS** for the *existing-environment* application order.

**DEFECT MIG-1 (fresh-environment ordering).** Verified empirically:

```text
Sorted (lexicographic) order:
  20260923000000_p8_insight_data_quality_reproducibility.sql   <- P3
  20261003000000_p8_i4_insight_interactions.sql   <- creates the table
  20261005000000_...rate_limit.sql                            <- 7 names
  20261006000000_...temporal_comparison.sql                   <- 8 names

Fresh database, table absent, P3 file applied first:
  ERROR: relation "public.carbontally_insight_tool_calls" does not exist (line 34)
  ERROR: relation "public.carbontally_insight_tool_calls" does not exist (line 44)
  ERROR: relation "public.carbontally_insight_tool_calls" does not exist (line 48)

Widening, then re-applying the later-sorting P2 migration:
  after P3 widening:            P3 tools allowed: true
  after 20261006000000 applied: P3 tools allowed: false
```

Two consequences on any **fresh** database built in filename order:
1. the P3 migration fails outright — its table is created by a later-sorting file;
2. even if applied, the later migrations re-narrow the constraint to 4 → 7 → **8**
   names, so both P3 tool names would be rejected by the database CHECK at
   runtime and the I4 tool-call evidence write would fail for P3 calls.

Cause: the P3 file carries the real-date prefix `20260923000000`, whereas the
whole Phase-8 Insight sequence deliberately uses October prefixes. Scope: fresh
deployments, CI clones and environment rebuilds — **not** the currently deployed
database, where it was applied out-of-band after the P2 state and works.
Severity: **HIGH for fresh-environment deployment / evidence persistence**; not
exploitable and not a tenancy or accounting issue. Fix (not applied —
verification-only): rename to a prefix after `20261006000000`.


## 23. Test reproduction

| Suite | Exact command (from `backend/`) | Result |
| --- | --- | --- |
| P3 | `python -m pytest tests/unit/api/test_p8_insight_data_quality.py -q --no-header -p no:randomly` | **48 passed / 0 failed** (100%) — reproduces the claimed 48 |
| P2 | `python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py -q --no-header -p no:randomly` | 79 collected: **78 passed / 1 failed** (§14 pin) |
| P2+P3 | both files | 127 collected: 126 passed / 1 failed (§14 pin) |
| Insight regression | the 13-file Insight set from the P3 report | **299 collected: 298 passed / 1 failed** — reproduces the claimed 299/298/1 |

The claimed counts are **independently reproduced**.

## 24. Existing failure classification

| Failure | Classification | Evidence |
| --- | --- | --- |
| A. `test_the_catalogue_gained_exactly_one_tool` (`8` vs `10`) | **Expected consequence of an authorized expansion** (stale absolute count pin); governance/test debt, not a defect | §14 |
| B. `test_d17_..._migration_revision.py::test_migration_ordering_is_unchanged` — `assert len(names) == 71` → actual **81** | **Pre-existing / repo-state-count obsolescence (D-29)**: the pin counts migration files and every package adds files; not caused by P2/P3 behaviour | `assert 81 == 71` at HEAD |
| C. frontend `dr007-investor-display-fixes.test.jsx` | **Pre-existing / frontend-scope**: reproduces with P2's frontend edits stashed, and P2/P3 changed no frontend file | P3 report §17; both commits' file lists |

None was fixed, re-pinned or worked around.

## 25. P2/P3 interaction

`backend/services/insight_tools.py` at P3 = **+514 / −0**, so P2 code (including the
`_temporal_comparison` docstring) is byte-identical. P2 tool, tests, migration and
frontend are unchanged by P3; P2 arithmetic is unchanged (same `compare_totals`);
the P3 planner branches sit **after** the frozen P2 branch and a regression test
asserts P2 planning is unchanged. The only interaction is the invalidated P2 count
pin (§14) — a test contract, not behaviour. **PASS.**

## 26. Scope containment

Inspection of both commits and their modules found **no** Scope 3 Categories 1–15,
no market-based Scope 2, no location-based Scope 2 methodology, no Scope 1
decomposition, no supplier persistence, no variance/attribution, no factor-history
implementation (D-13), no RAG, no consultant/auditor access expansion, no L7
retention/lifecycle work, no L8 billing/entitlements, no investor-demo or Demo Lab
change and no deployment artefact. P3 adds read-only aggregation over existing data
only. **No unexpected scope expansion.**

## 27. D-11 / restatement limitation

P2 compares **currently authoritative** stored records for two periods; it makes no
historical as-of/restatement claim, exposes no restatement history and adds no
restatement semantics (no "as reported at the time" field, no version pinning).
D-11 remains unresolved by design and is not implemented by P2 or P3. Where a
comparison would need historical-as-of data, the result is a current-data
comparison and the D-11 gap stays open and PO-owned. **No silent restatement claim
found.**


## 28. Defects

| ID | Severity | Statement | Status |
| --- | --- | --- | --- |
| **MIG-1** | HIGH (fresh-environment deployment) | The P3 migration filename `20260923000000_...` sorts **before** the migration that creates its target table (`20261003000000`) and before the P2 widening it builds on (`20261006000000`). On a fresh database it fails (`relation ... does not exist`), and the later-sorting migrations re-narrow `ci_tool_calls_tool_name_check` to 8 names, which would reject both P3 tools' evidence writes at runtime. | **Reported, not fixed** (verification-only). Suggested fix: rename the file to a prefix after `20261006000000`. |
| P2-PIN-1 | LOW (test contract) | `test_the_catalogue_gained_exactly_one_tool` asserts an absolute registry count (`8`), which any authorized expansion invalidates. | **Reported, not fixed** (§14). |

No other defect was found in P2 or P3 behaviour, arithmetic, honesty mechanisms,
isolation, provenance or rate limiting.

## 29. Non-blocking observations

* **O-1 — Migration-count pin drift (d17).** `assert len(names) == 71` now sees 81
  files. A count-based pin will keep failing as packages land; an ordering/prefix
  assertion would be more durable. Pre-existing; not P2/P3 caused.
* **O-2 — The limiter is at the request path, not in `invoke_tool`.** An in-process
  call to `invoke_tool` does not itself consume a token (identical for the
  INS-01/P2 tools); the customer-facing route does. Not a defect, but a future
  internal caller invoking `invoke_tool` outside the route would bypass rate
  limiting and route-level evidence. Defence-in-depth note for the PO/architect.
* **O-3 — Database-level RLS not exercised.** P3 verification was application-level
  (organisation-scoped reads + explicit object re-check). The new tools add no
  table and change no policy, so the RLS surface is unchanged, but a
  disposable-database RLS negative test would strengthen the evidence.
* **O-4 — Migration harness scope.** The disposable database held a faithful
  replica of the constraint's target object rather than the full migration chain
  (Supabase-specific roles/extensions). The P2/P3 files were applied verbatim; the
  §22 ordering finding rests on the sorted filenames and was reproduced directly.
* **O-5 — No P3 frontend detail panel**, as its implementation report states; the
  answers are deterministic and narrated. Documented limitation, not a regression.

## 30. Final technical assessment

P2 is functionally correct at the level available to a non-independent pass:
arithmetic, zero baseline, empty-vs-zero semantics, grouping, boundaries, tenant
isolation, rate limiting, provenance and its migration all pass. P3 is functionally
correct on the same terms: it invents no quality rule or score, its honesty
mechanisms hold under direct testing, it reuses the existing
validation/calculation/evidence/provenance stack, it is bounded, organisation-scoped
and rate-limited, and its migration applies correctly to a database already at the
P2 state.

One material defect exists and it is a **deployment/sequencing** defect rather than a
logic defect: **MIG-1**, which breaks a fresh-environment build and would leave P3's
tools rejected by the database CHECK. Because a defect was found, the verdict is the
defect verdict.

```text
Cline Verification Pass — DEFECTS FOUND
```

This is **not** independent OHD verification and **not** a PO closure. The
governance sequence remains: Cline implementation → Cline verification pass →
independent OHD verification (when available) → PO closure. Whether this evidence
suffices for a given package is a PO decision this pass does not make.

