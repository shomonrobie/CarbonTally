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
