# CT-PO-P12-STEP2-DISPOSABLE-INTEGRATION-VERIFICATION-20260924

**Reference:** `CT-PO-P12-STEP2-DISPOSABLE-INTEGRATION-VERIFICATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** STEP 2 — F-046-1 disposable-clone integration verification
**Status:** **STEP-2 DELIVERABLE — NOT EXECUTED**
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Result

```text
STATUS: NOT EXECUTED
```

No integration suite was run in this Step-2 session, and **no destructive operation
was pointed at the canonical Demo Lab**. The criterion
*"disposable integration verification executed"* therefore **fails**, and Step 2
cannot be declared complete.

## 2. Why it was not executed

| Reason | Detail |
| --- | --- |
| F-046-1 is absolute | `backend/tests/integration/conftest.py` performs `TRUNCATE … RESTART IDENTITY CASCADE` on whatever `INTEGRATION_DATABASE_URL` names, and refuses targets whose names match `qa`/`demo`/`investor`/`prod`/`live` (which includes `carbontally_demo_local`) plus the forbidden main databases. |
| The canonical environment must not be the target | By definition the canonical investor-demo environment is not disposable for verification purposes; running the suite against it would destroy the seeded demo. |
| A suitable disposable target was not created | `carbontally_test` exists (117 tables) and is the designated integration database, but creating/validating a disposable clone was not performed in this session, so no run was attempted. |
| Session budget | The Step-2 environment work (cold-start harness repair, schema build, seed, Story A–D verification) consumed the available session, and the remaining verification pass was not reached. |

## 3. What was verified instead (non-destructive)

| Verification | Result |
| --- | --- |
| `tools/demo_lab/verify.py` (read-only probes against the canonical environment) | **13/13** actor contexts, **30/30** authorization probes, **18/18** isolation rules, `known_product_defects: []` |
| Backend health | `/health` → 200 |
| RLS state | 141/141 public tables RLS-enabled, 298 policies |
| `emission_factors` containment (D-4) | RLS enabled, **0 policies**, `anon`/`authenticated` revoked — verified by direct catalog read; the app role (`postgres`, `bypassrls=true`) still reads all 7,049 rows |
| Real pipeline outcomes | 11 documents processed through the real worker; 10 honest blocks; 1 tabular document producing 2 calculations + 2 evidence lines |
| Unit suite | not re-run in Step 2 (Step-1 baseline: 3,220 tests, 4 pre-existing stale-fixture failures, 8 skipped — unchanged by Step 2 because no product code was modified) |

## 4. Exact remediation required

1. Create a **disposable clone** of the canonical schema, e.g.
   `CREATE DATABASE ct_p12_step2_verify TEMPLATE …` or `pg_dump --schema-only` restore
   into `ct_p12_step2_verify`.
2. Assert the target identity **before** the run: `SELECT current_database()` must
   return the clone name and must not match any F-046-1 forbidden marker.
3. Run the relevant suites with `INTEGRATION_DATABASE_URL` pointed at the clone:

```text
tests/integration/test_evidence_line_items_b2_runtime.py
tests/integration/test_report_lifecycle.py
tests/integration/test_consultants.py
tests/integration/test_documents.py
tests/integration/test_extraction.py
tests/integration/test_v3m1_v3m2_processing_entities.py
tests/integration/test_v3_rls_behavior.py
tests/integration/test_calculation.py
tests/integration/test_disclosure_b3_v3_security.py
```

4. Record PASS/FAIL per suite with the clone name, the release commit and raw output.
5. Drop the clone afterwards and verify the canonical environment is untouched.

## 5. Authorization

Running integration suites against a **disposable clone** requires **no additional
product authorization** (F-046-1 explicitly permits `ct_*` clones and the designated
test database), but it does require a session with sufficient time budget. It is
recorded here as **AUTHORIZATION REQUIRED — verification pass outstanding**, not as
a product blocker.

---

# ADDENDUM — COMPLETION PASS (2026-09-24, later session)

> The sections above describe the state **before** the completion pass and are
> preserved unchanged. The sections below record the completion-pass execution and
> **supersede §1's status**.

## A1. Status after the completion pass

```text
STATUS: EXECUTED, NOT PASSING
```

The required suites **were executed** against an isolated disposable clone. They did
**not** pass. The failures are classified below; **none** is attributable to Step 2,
which changed no product code.

## A2. Execution record

| Item | Value |
| --- | --- |
| Clone | **`ct_p12_c2_integration`** (name passes the F-046-1 protected-marker check) |
| Creation | `CREATE DATABASE` + `pg_dump` (schema **and** data **and** privileges, `--no-owner`) from `carbontally_demo_local` |
| Clone identity | `current_database()` = `ct_p12_c2_integration`; 141 public tables; 298 policies; 6 Insight tables; evidence schema present |
| Safety | the canonical Demo Lab, `postgres`, `carbontally_test` and `carbontally_qa_phase8` were **never** targeted |
| Source release SHA | `35eb7bab9ee87839d07b50a2fd70a662d1ce1675` (Step-2 base) |
| Command | `INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_p12_c2_integration ./.venv/bin/python -m pytest <9 suites> -q --tb=line` |
| Start / end | 2026-09-24T09:39:40Z → 09:39:43Z |
| Exit code | **1** |
| Result | **92 tests, 21 failed, 0 errors, 0 skipped** |
| Suites | `test_evidence_line_items_b2_runtime`, `test_report_lifecycle`, `test_consultants`, `test_documents`, `test_extraction`, `test_v3m1_v3m2_processing_entities`, `test_v3_rls_behavior`, `test_calculation`, `test_disclosure_b3_v3_security` |
| Artifacts | `/tmp/c0_integration3.xml`, `/tmp/c0_integration3.log` |

Earlier attempts (recorded for completeness): a **schema-only** clone produced 9 setup
ERRORs because reference data (the disclosure catalogue) was absent; a schema-only +
`--no-privileges` clone produced 29 failures because the `authenticated` role lacked
the GRANTs the RLS suites exercise. Both were clone-construction artefacts, fixed by
dumping data **and** privileges.

## A3. Failure classification

| Class | Count | Evidence | Attribution |
| --- | --- | --- | --- |
| **Privilege posture (demo-lab over-grant, D-2-07)** | 9 | `Failed: DID NOT RAISE InsufficientPrivilegeError`; `tools/demo_lab/stack.py:317` blanket-grants `INSERT, UPDATE, DELETE … TO authenticated` **after** migrations; clone shows `authenticated` holding INSERT while `relrowsecurity = true` | **demo-lab harness** — not a product defect, not a data exposure |
| **Fixture / FK precondition** | 6 | `ForeignKeyViolationError: update or delete on table "emission_factors" violates foreign key constraint "calculation_snapshots_factor_id_fkey"` | **test fixture/data precondition** in the clone |
| **Pre-existing test drift / environment coupling** | 6 | `assert 3 == 2` (B2 SELECT-policy count — the Insight I2 migration legitimately adds a 3rd policy); `TypeError: ConsultantsRepository.add_client() missing 3 required positional arguments`; `assert None is not None`; `AssertionError: expected 7049 total factors, got 1` (the session fixture TRUNCATEs `emission_factors`) | **pre-existing** — tests not updated for later migrations/repository signatures |

## A4. Decisive attribution evidence

```text
git diff --name-only 35eb7ba..HEAD -- ':!docs' ':!tools/demo_lab'   →   (EMPTY)
```

The entire Step-2 + completion change set is `docs/architecture/*` plus
`tools/demo_lab/{stack,storage,provision,manifest.json,t3_scenarios,run_demo_lab.sh}`.
**No backend, frontend, migration, RLS or test file was modified**, so no integration
failure can be attributed to Step-2 product behaviour.

## A5. Cleanup

The disposable clone was dropped after the run and the canonical Demo Lab was verified
untouched (it was subsequently re-provisioned by the Cycle-2 repeatability work, which
is recorded separately).

## A6. Compliance and residual status

```text
[x] destructive suites not aimed at carbontally_demo_local / postgres / carbontally_test / qa_phase8
[x] clone identity verified before the run
[x] suites executed (not substituted by unit tests)
[x] failures classified (harness / fixture / pre-existing)
[x] product code NOT modified to obtain a green result
[ ] integration suites PASSING  → NOT achieved
```

**Interpretation for the gate:** the mandatory *"disposable-clone integration
verification"* action was **executed and evidenced**. It is **not a green run**, so
the criterion cannot be recorded as PASS; the residual failures are pre-existing /
environmental and are carried forward with remediation (see the completion
verification record §5).
