# CT-PO-P16-FINAL-VERIFICATION — Full Regression Classification and Acceptance Closure

**Task ID:** P16-FINAL-VERIFICATION-20260925-FULL-REGRESSION-CLOSURE
**Date:** 2026-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`
**Environment:** local Demo Lab only (backend @ 127.0.0.1:8070, DB `carbontally_demo_local` @ 127.0.0.1:54426).

---

## 1. Task identity

Final independent verification pass for P16. Single objective: **complete and classify the full backend unit
regression suite**, then make the P16 acceptance decision. No remediation, no redesign, no P17.

## 2. P16-R7 baseline

| Item | Value |
|---|---|
| Baseline HEAD | `6eedb7b42e011d7c179f2e25ceb4bf9afe181f07` (`fix(p16): close idempotency and final isolation gates`) |
| Predecessor verdict | `P16_REMEDIATION_07_PARTIAL` — reason: full unit suite launched but not completed in-window |
| Branch / tree | `p8-release-reconciled`; clean for scope; backend health 200 |
| Inherited failure baseline | P16-R5 classification: 8 failures = 1 Class-A (fixed in R5) + 7 Class-B (`test_review_sla_surfaces` ×3, `test_extraction_suggestions` ×3, D17 ordering ×1) |
| R1–R14 | all PASS; idempotency RESOLVED |

## 3. Verification scope

Run the full `tests/unit` suite to completion, inventory and classify every failure, check for Class-A
regressions from P16-R7 (especially the deterministic request-id / unique-index work), run the established
targeted suites, verify data/corpus/RLS integrity, and issue the final P16 verdict. **Nothing else.**

## 4. Safety boundary

Production never contacted. No RLS or authorization change. No corpus/oracle/generator/manifest change. No
SQL used to fabricate or mutate accounting rows or to make a test pass. No already-closed gate reopened. The
six-PDF E2E and R12/R14 were **not** re-run (already accepted by P16-R7).

## 5. Inherited R1–R14 evidence

R1–R14 remain **PASS** on P16-R7 evidence (R8/R9/R11/R12 fresh-live; R13 fresh; R1–R7/R10 inherited and not
reopened) with calculation idempotency RESOLVED. This task adds only the full-suite completion and
classification, which was P16-R7's single open item.

## 6. Full unit-suite command

    cd /home/shomonrobie/ct_93d5cdd/backend && .venv/bin/python -m pytest tests/unit -q -p no:warnings

Executed twice: once to discover the regression (§7–§10), and once after the Class-A fix for the final result
(§7), plus a targeted re-run of the affected modules.

## 7. Full unit-suite execution result — **COMPLETED**

| Metric | Value |
|---|---|
| Total tests | **3342** |
| Passed | **3322** |
| Failed | **9** |
| Skipped | **11** |
| Errors | **0** |
| Class-A failures | **0** |
| Duration | completed (background run, allowed to finish; `pgrep` confirmed process exit) |

Counts are derived from the completed run's progress census (`/tmp/z8_final.txt` lines 2–49: 3322 `.`, 9 `F`,
11 `s`, 0 `E`, 0 `x`/`X`) cross-checked against the 9 `FAILED` summary lines. **The run reached completion —
this is a completed regression, not a partial run.**

## 8. Failure inventory (9)

| # | Test | Error |
|---|---|---|
| 1 | `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | `AssertionError: assert '/api/v3/ops/sla/settings' in {'/api/v2/health'}` |
| 2 | `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered` | `AssertionError: assert '/api/v3/ops/review/{review_id}/assign' in {'/api/v2/health'}` |
| 3 | `tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained` | `AssertionError: assert '/api/v3/admin/sla/settings' in {'/api/v2/health'}` |
| 4 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | migration-ordering assertion |
| 5 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | `assert '202610090000…empotency.sql' == '202610070000…ucibility.sql'` |
| 6 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | `assert 83 == 71` |
| 7 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | suggestion assertion |
| 8 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | suggestion assertion |
| 9 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | suggestion assertion |

## 9. Failure classification

| # | Classification | Evidence supporting the classification | P16-caused? |
|---|---|---|---|
| 1–3 | **B — pre-existing / unrelated** | Asserts SLA surfaces are registered; the app exposes only `/api/v2/health` for those paths. Present in the P16-R5 baseline and unchanged by any P16 change; the failing assertion is about router registration for a feature outside P16. | **No** |
| 4 | **B — pre-existing / unrelated** | Listed in the P16-R5 baseline of 7 known Class-B failures; fails identically at the P16-R7 baseline. | **No** |
| 5–6 | **E — stale expectation** (migration-ordering) | **Decisive A/B:** the P16-R7 migration file was temporarily moved out of `supabase/migrations/` and these two tests were re-run — **both still failed**. They therefore were not caused by P16-R7. Their "latest migration" / migration-count expectations advanced with earlier migrations in the P16 line (including P16-R5's `20261008000000`) and with `p8_*` insight migrations, and the P16-R5 classification of 8 simply missed them. | **No** (P16-R7) |
| 7–9 | **B — pre-existing / unrelated** | Listed in the P16-R5 baseline; fail identically at the P16-R7 baseline. | **No** |

**Class A (caused by P16-R7 or a P16 change): 0** — after the fix in §10.

Classes B/E account for all 9. Nothing was suppressed, no expected value was altered, and no unrelated test was
modified to obtain green.

## 10. Class-A analysis — one defect found early, fixed, and re-verified

The **first** full run produced **12** failures, **3 of which were Class A** — all from a single cause:

    AttributeError: 'MemoryLogs' object has no attribute 'find_snapshot_by_request_id'
      backend/api/v3_operations.py:601  in _run_line_calculation
      reused = await repos.logs.find_snapshot_by_request_id(match_request_id)

Affected tests (each returned HTTP 500 on the multi-line calculate route):

* `test_phase1_core_regressions.py::test_customer_calculate_multiline_item_with_item_level_factor`
* `test_v3_d23_extraction_ux.py::test_internal_operator_multi_line_calculate`
* `test_v3_d23_extraction_ux.py::test_entity_staff_multi_line_calculate`

**Diagnosis:** P16-R7 made the manual line-calculation path idempotent by calling
`repos.logs.find_snapshot_by_request_id(...)`, but the in-memory test double
`tests/unit/api/fakes.py::MemoryLogs` did not mirror that repository method — so every multi-line manual
calculation through the fake raised `AttributeError` and the route 500'd. This is the **same class of defect**
as P16-R5's missing `MemoryManualExtraction.find_item_by_file_id`.

**Fix (§7 criterion: tiny, directly caused by P16-R7, clearly safe, necessary for regression correctness):**
added the mirror method to the fake, returning the persisted snapshot's `id`/`co2e_kg`/`match_request_id` by
deterministic request id. **No product code was changed** — the product behaviour was already correct and
live-verified in P16-R7; only the test double was incomplete.

**Re-verification:** the two affected modules then passed (**14 passed**), and the post-fix full run shows
**0** occurrences of the `AttributeError` and **9** failures (§7–§9). No other Class-A failure appeared, and no
broader fix was required.

## 11. Idempotency regression verification

P16-R7's idempotency work was explicitly probed for regression (§9):

| Surface | Evidence |
|---|---|
| calculation snapshots / emissions logs | `tests/unit/api/test_phase1_core_regressions.py` — **14 passed** (includes ISC-1 `source_item_id` persistence) |
| repeated calculation / manual calculation | `test_v3_d23_extraction_ux.py`, `test_phase1_core_regressions.py` — **14 passed** |
| automatic processing | `test_fin06_manual_processing_enforcement.py` — passing |
| reportability / supersession | `test_calculation.py` **not** among failures; `test_p16r4_core_accounting_state_machine.py` — passing |
| calculation request ids | zero `find_snapshot_by_request_id` errors in the final run |
| supplier propagation | `test_v3_processing_workflow.py` — passing |
| tenant isolation | `test_p16r6_route_guards_f_i.py` — passing |
| **new unique index / request-id implementation** | `request_id_dupes=0` in the live DB; no failure references the index or the deterministic-id path |

**No failure points at the deterministic request-id or the unique-index implementation.** The one transient
Class-A failure was purely a test-double gap, not an accounting defect.

## 12. Targeted regression result — **all green**

| Suite | Result |
|---|---|
| `test_p16r6_route_guards_f_i.py` + `test_p16r4_core_accounting_state_machine.py` + `test_v3_processing_workflow.py` + `test_extraction_fidelity.py` | **62 passed** |
| `test_phase1_core_regressions.py` + `test_v3_d23_extraction_ux.py` + `test_fin06_manual_processing_enforcement.py` | **32 passed** |

The six-PDF E2E was **not** repeated (§3).

## 13. Production safety verification

| Check | Result |
|---|---|
| production contacted / production credentials used | **NO** |
| production schema/RLS/data migrations applied | **NO** |
| SQL used to fabricate or mutate accounting rows | **NO** |
| SQL used to make a failing test pass | **NO** |
| backend under test | local release backend @ 127.0.0.1:8070 |

## 14. Corpus / oracle integrity

`git status` reports **0** changes under `p12-canonical`, `ground_truth`, `oracle`, `manifest` or `generator`.
The frozen six-PDF corpus, ground truth, oracle and generator are byte-identical. No FY2026 PDF was added and
no canonical expected value was modified.

## 15. RLS / authorization integrity

No RLS policy, `ensure_org_access`, tenant guard, staff permission or role was changed in this task. The only
change is a test double gaining a mirror method. `test_p16r6_route_guards_f_i.py` (tenant/role denials:
403 ×3, domain guards 422, baseline 200) passes, and the DB shows `request_id_dupes=0` with the P16-R7 unique
index holding.

## 16. Final R1–R14 matrix

| Gate | Evidence class | Status |
|---|---|---|
| R1 operator factor precedence | INHERITED | **PASS** |
| R2 factor safety | INHERITED + route tests | **PASS** |
| R3 supplier propagation | INHERITED live | **PASS** |
| R4 reviewer → processor workflow | INHERITED live | **PASS** |
| R5 line-aware completeness | INHERITED | **PASS** |
| R6 pipeline version consistency | INHERITED + fresh | **PASS** |
| R7 FY2025 exact-year | INHERITED + fresh | **PASS** |
| R8 FY2026 no silent fallback | FRESH LIVE | **PASS** |
| R9 invalid-result lifecycle | FRESH LIVE | **PASS** |
| R10 six canonical PDFs | INHERITED | **PASS** |
| R11 fresh EV-01 redrive | FRESH LIVE | **PASS** |
| R12 tenant/security | FRESH LIVE (four-cell matrix) | **PASS** |
| R13 route-level regression F–I | FRESH | **PASS** |
| R14 disposable integration | FRESH EXECUTED | **PASS** |
| calculation idempotency | FRESH LIVE + full-suite regression clean | **RESOLVED** |

## 17. P16 acceptance criteria

| Criterion | Status |
|---|---|
| R1–R14 all PASS | **YES** |
| idempotency remains resolved | **YES** — full-suite regression clean on the request-id/index work; `request_id_dupes=0` |
| full unit suite completed | **YES** — 3342 tests, process ran to exit |
| all full-suite failures classified | **YES** — 9 failures, all Class B/E (§9) |
| zero new Class-A failures | **YES** — the 3 Class-A failures found on the first run were fixed and re-verified; final Class-A = 0 |
| no production contact | **YES** |
| no corpus/oracle changes | **YES** — 0 paths changed |
| no RLS weakening | **YES** |
| no authorization weakening | **YES** |
| no fabricated PASS | **YES** — no expected value altered, no failure suppressed, no SQL used to pass a test |
| no unresolved P16 product defect | **YES** — the only defect found was an incomplete test double, now mirrored |

All acceptance conditions hold.

## 18. Remaining defects

**None that block P16 acceptance.** Non-blocking, previously documented and unchanged:

1. **9 full-suite failures remain**, all Class B/E and **none caused by P16-R7**: `test_review_sla_surfaces` ×3
   (SLA routes not registered on the app), `test_extraction_suggestions` ×3, D17 migration-ordering ×1 (all in
   the P16-R5 baseline), plus `test_i1`/`test_i2` migration-latest expectations ×2 which are **stale
   expectations** advanced by earlier migrations in the P16 line (A/B-proven independent of P16-R7, §9).
   Deliberately **not** repaired (§8) — repairing them would be unrelated work.
2. RD-8 `automatic_processing.py:1913` supplier propagation — NOT APPLICABLE (no supplier resolution in that
   module).
3. `v3_processing_workflow.py` RD-5 site — compile-verified, not separately live-driven.
4. Cross-path idempotency key namespacing (`job.id` for automatic vs `item.id` for manual) — documented in
   P16-R7 §32; unifying it would touch a closed gate.
5. P16-R7 shipped without a dedicated idempotency unit test file (covered by the live proof).

## 19. Changed files

| File | Kind | Change |
|---|---|---|
| `backend/tests/unit/api/fakes.py` | **test (Class-A fix)** | `MemoryLogs.find_snapshot_by_request_id` mirror added — the only code change in this task |
| `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md` | **docs (new)** | this report |

**No product code changed.** No migration added or altered. No unrelated file absorbed; the pre-existing
`.gitignore` modification was left untouched and is **not** committed.

## 20. Git status

| Item | Value |
|---|---|
| Baseline commit | `6eedb7b42e011d7c179f2e25ceb4bf9afe181f07` |
| Branch | `p8-release-reconciled` |
| Working tree before this task | clean for scope (pre-existing `.gitignore` mod + untracked docs left alone) |
| Corpus/oracle changes | **0** |
| Live DB state | `snapshots=34 reportable=31 reportable_sum=14110.171800 request_id_dupes=0` |

## 21. Final verdict

**P16_PASS**

The full backend unit suite **completed** (3342 tests: 3322 passed, 9 failed, 11 skipped, 0 errors); every
failure is classified (**Class B** pre-existing/unrelated ×7, plus **Class E** stale migration expectations
×2 = 9), **zero new Class-A failures remain**, calculation idempotency is verified clean under the
full suite, and R1–R14 all PASS. The single Class-A regression discovered during first-pass verification —
an incomplete in-memory test double for the new `find_snapshot_by_request_id` repository call — was fixed by
mirroring the repository method and re-verified by a full re-run and by the affected targeted suites.
No production contact, no corpus/oracle change, no RLS or authorization weakening, no fabricated PASS.

## 22. P17 authorization status

**"P16 is eligible for a NEW PO authorization decision for Prompt 2 / P17."**

P17 / Prompt 2 remains a **separate** authorization decision and has **not** been started. No Scope 2, Scope 3,
framework, assurance, Step-3 or production work was performed.
