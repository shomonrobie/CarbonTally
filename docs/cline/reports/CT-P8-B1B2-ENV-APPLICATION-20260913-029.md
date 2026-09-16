# CT-P8-B1B2-ENV-APPLICATION-20260913-029

**Task ID:** `CT-P8-B1B2-ENV-APPLICATION-20260913-029`
**Title:** Phase 8 — Controlled application of B1 + B2 to a dedicated non-production QA environment
**Date:** 2026-09-13
**Type:** OPERATIONAL APPLICATION + VERIFICATION (non-production only)
**Authorization:** PO blanket authorization `…050` §6 (dedicated persistent non-production QA environment; B1 → B2 in order; idempotency re-apply; runtime suites; **backfill NOT authorised**)

---

## 1. Objective and boundary

Make B1 (Disclosure Model foundation) and B2 (Evidence / line-item addressability) **real in a persistent non-production environment** so that Phase 8 runtime suites execute rather than skip, and so B3 can be built and verified against a provisioned schema.

**Boundary respected:** no production access; no investor-demo database; **no backfill execution**; no code/migration/test modification; no commit.

## 2. Environment created

| Item | Value |
|---|---|
| **Dedicated QA database** | `carbontally_qa_phase8` (new; persistent; non-production; same local PostgreSQL cluster `127.0.0.1:54426`) |
| Construction | production-shaped **schema-only** restore from the dev/application database (`pg_dump --schema-only --no-owner postgres` → 18,449-line script, restore rc=0) |
| Pre-existing tables after restore | **116** (matches the dev DB and the V1R parity target) |
| Restore warnings | 73 benign non-schema errors (63 default-privilege, 5 grant-option, 2 `realtime.list_changes`, 1 `log_min_messages`, 1 `pg_stat_statements_reset`, 1 `pg_reload_conf`) — the same class V1R recorded; **no schema-object failures** |
| Not used | production; the investor-demo dataset; `carbontally_test` (retained unchanged as the integration DB) |

## 3. Migration application (prescribed order)

| # | Migration | First apply | Re-apply |
|---|---|---|---|
| 1 | `20260913000000_p8_report_lifecycle_status.sql` (S3) | **rc=0** | **rc=0** |
| 2 | `20260914000000_p8_b1_disclosure_model_foundation.sql` | **rc=0** | **rc=0** |
| 3 | `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` | **rc=0** | **rc=0** |
| 4 | `20260916000000_p8_b2_evidence_line_items.sql` | **rc=0** | **rc=0** |
| 5 | `20260916010000_p8_b2_provenance_line_links.sql` | **rc=0** | **rc=0** |

Applied with `psql -v ON_ERROR_STOP=1`; every rc recorded (`/tmp/mig_rc.txt`, `/tmp/mig_rc2.txt`).

### 3.1 Post-application object inventory (live)

| Object | Present |
|---|---|
| `disclosure_*` tables (B1) | **11** |
| `evidence_line_items` (B2) | **1** |
| `calculation_snapshots.source_line_item_id` | **present** |
| `disclosure_value_evidence.source_line_item_id` | **present** |

## 4. Idempotency proof

* All five migrations re-applied: **rc=0** each.
* Schema captured before and after the re-apply (`pg_dump --schema-only`), both 18,908 lines.
* `diff` result: **only** the pg_dump per-invocation `\restrict`/`\unrestrict` nonce token differs. **Zero schema delta** → idempotent.

## 5. Runtime suites (executed, not skipped)

Environment: `INTEGRATION_DATABASE_URL=postgresql://…@127.0.0.1:54426/carbontally_qa_phase8`

| Suite | Command (abridged) | Result |
|---|---|---|
| B1 + B2 runtime integration | `pytest tests/integration/test_disclosure_b1_runtime.py tests/integration/test_evidence_line_items_b2_runtime.py -q` | **36 passed, 0 failed — EXIT=0** |
| B1/B2 unit + static | `pytest tests/unit/data/test_b2_migration.py tests/unit/domain/test_evidence_line_items.py tests/unit/data/test_disclosure_migration.py tests/unit/data/test_disclosure_sql_typing.py tests/unit/domain/test_disclosure.py -q` | **75 passed, 0 failed** |

**This is the first execution of the B1/B2 runtime suites in a persistent environment.** Previously they reported **SKIPPED** everywhere outside disposable clones — a skip that was never a PASS.

## 6. Findings

| # | Finding | Severity | Disposition |
|---|---|---|---|
| F-029-1 | The QA environment is a **local, developer-workstation** persistent database, not a cloud-hosted QA tier. It is non-production, isolated and persistent, satisfying §6's requirements, but it shares the workstation with the dev DB. | Low (informational) | Recorded; a hosted QA tier remains a deployment decision for the PO. |
| F-029-2 | The QA restore is **schema-only** (no application data). Tests that require pre-seeded rows (e.g. auth users) can fail for environmental reasons — classified per case (see `-030` F-030-1). | Low | Recorded; not a Phase 8 defect. |
| F-029-3 | B1's unique-index precondition (V1R R4: duplicate historical rows) did **not** trigger — the restored schema was clean. The precondition remains documented for any future data-bearing environment. | Low | Recorded. |

## 7. Explicitly not performed

* **Backfill execution — NOT performed** (not authorised; `…050` §6). No historical row was rewritten.
* No production migration, no production access, no investor-demo mutation.
* No commit; no migration authored; no code or test changed.

## 8. Verdict

### `B1 + B2 APPLIED TO carbontally_qa_phase8 — RUNTIME SUITES EXECUTED (36/36 PASS); IDEMPOTENT; BACKFILL NOT RUN`

