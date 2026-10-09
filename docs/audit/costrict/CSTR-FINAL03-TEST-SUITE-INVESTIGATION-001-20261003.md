# CSTR-FINAL03-TEST-SUITE-INVESTIGATION-001 — Read-Only Investigation of the 7 Unit-Suite Failures and 8 Skips

**Investigator:** CoStrict (independent investigator — **not** the implementation agent)
**Date:** 2026-10-03
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled` · **HEAD:** `cabdca8380415e73a25cf23eb393d0b15c0af391` (unchanged)
**Boundary:** READ-ONLY. No file, test, migration, configuration, skip marker or database row was
created, modified or removed. No package was installed. No deploy, production/Render/Vercel contact,
commit, push, stash, reset or checkout occurred. No remediation was performed or proposed as authorised.

---

## 1. Task ID

**CSTR-FINAL03-TEST-SUITE-INVESTIGATION-001** — identify, reproduce, root-cause and FINAL-03-classify
all **7 failures** and all **8 skips** behind the latest unit-suite result.

The R1 remediation (`CT-FINAL03-RLS-R1-001 — INDEPENDENTLY VERIFIED`) and the FINAL-03 RLS remediation
were **not** reopened.

---

## 2. Scope and read-only boundary

### Investigated

* the current `tests/unit` result (reproduced from scratch, not copied from a report);
* every failing and skipped node, individually;
* the implementation, fixtures, migrations and git history behind each;
* repository/git state before and after the investigation;
* whether any finding is caused by, or relevant to, FINAL-03.

### Not performed (boundary)

* No mutation of any kind. Diagnostics that would have required mutation were **not** run (recorded
  in §12): notably, the DSN-gated live database suites were **not** executed, and the two FINAL-03
  migrations were not touched, moved or renamed to simulate the "without FINAL-03" case. That case was
  instead evaluated by **replaying each test's own predicate** over the live migration filename list
  with the two FINAL-03 names excluded (pure computation, no file change).
* No remediation, no patch, no fix, no test update, no migration, no skip removal, no rename.

---

## 3. Baseline test-suite result (reproduced)

Command (from `/home/shomonrobie/ct_93d5cdd/backend`, project interpreter `./.venv/bin/python`,
Python 3.14.4; no extra `-q` because `backend/pyproject.toml` sets `addopts = "-q"`):

```
./.venv/bin/python -m pytest tests/unit --no-header -rf --junitxml=/tmp/cstr_tsi_unit.xml
```

Start `2026-10-03T03:01:08+06:00`, finish `2026-10-03T03:08:11+06:00`.

**Final pytest summary: `7 failed, 4767 passed, 8 skipped, 14 warnings in 416.71s (0:06:56)` (exit 1).**

Machine-readable corroboration (`/tmp/cstr_tsi_unit.xml`):

```
<testsuite name="pytest" errors="0" failures="7" skipped="8" tests="4782" time="416.623" timestamp="2026-10-03T03:01:09.354484+06:00" />
```

| Metric | Value |
|---|---|
| collected | **4,782** |
| passed | **4,767** |
| failed | **7** |
| skipped | **8** |
| errors | **0** |
| warnings | 14 (deprecation warnings only; no warnings-as-errors) |
| duration | 416.71 s (JUnit: 416.623 s) |

Reproduced status classification (from the XML): `{P: 4767, s: 8, F: 7}` — no errors, no xfails.
The result matches the authorized baseline exactly.

> Scope note: the run was `tests/unit` only, as mandated. `backend/pyproject.toml` sets
> `testpaths = ["tests/unit", "tests/integration"]`, so a bare `pytest` would additionally collect
> `tests/integration` (including FINAL-03's own live suite) and could change the skip count.
> That was **not** run (out of scope / would touch database-gated suites); see §12.

---

## 4. Complete list of the 7 failures

| # | Node ID (exact) |
|---|---|
| F1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` |
| F2 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` |
| F3 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` |
| F4 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` |
| F5 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` |
| F6 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` |
| F7 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` |

Per-module outcome from the XML (evidence that most tests in each file still pass):

| Module | P | F | s |
|---|---|---|---|
| `tests.unit.data.test_d17_provider_ownership_migration_revision` | 15 (TestD32Revision 10, TestD35Revision 5) | — | — |
| `tests.unit.data.test_d17_provider_ownership_migration_revision.TestRevisionScope` | 1 | 1 | 1 |
| `tests.unit.data.test_i1_insight_migration` | 8 | 1 | — |
| `tests.unit.data.test_i2_insight_authorization_contracts` | 6 | 1 | — |
| `tests.unit.data.test_p17_migrations` | 45 | 1 | — |
| `tests.unit.engines.test_extraction_suggestions` | 4 | 3 | — |
| `tests.unit.services.test_p12_impl_01_invoice_extraction` | 69 | — | — |
| `tests.unit.backup.test_jobs` (all classes, incl. `TestMigrationAlignment`) | 83 | — | — |

---

## 5. Detailed investigation of each failure

### F1 — D17 `test_migration_ordering_is_unchanged`

* **File / class / function:** `backend/tests/unit/data/test_d17_provider_ownership_migration_revision.py:261-269`, `TestRevisionScope::test_migration_ordering_is_unchanged`.
* **Feature under test:** D17 provider-ownership migration revision — that the release migration ordering is unchanged by the D32/D35 revision.
* **Exact error:** `AssertionError: assert 98 == 71  +  where 98 = len([...98 migration names...])` at `:264`.
* **What it expects:** `len(names) == 71` (a snapshot of the migration chain at the D17 revision), then `versions == sorted(versions)`, `versions == sorted(set(versions))` (no duplicates) and `idx(D32) < idx(D35)`.
* **Immediate cause:** the live chain holds **98** migration files; 71 is a frozen count.
* **Deeper root cause:** the assertion encodes a historical chain size. Everything from `20260928000000_p8_fs_activity_clarifications.sql` onward (27 files) post-dates the D17 revision, so the count has been stale for many change-sets — not just FINAL-03.
* **Predicate replay without FINAL-03:** with the two FINAL-03 migrations excluded the chain still holds **96** files → `96 ≠ 71` → **still fails**. FINAL-03 contributes 2 of the 27 excess files.
* **Do the other assertions in the same test hold?** Yes: `versions == sorted(versions)` → True; `versions == sorted(set(versions))` (no duplicate timestamps) → True; `idx(D32) < idx(D35)` → True (`D32 = 20260823000000_d32_private_documents_storage.sql`, `D35 = 20260824010000_d35_self_service_onboarding.sql`).
* **Test last touched:** mtime 2026-09-22, last commit `2009d2f` (2026-09-16); tracked and **clean** (no working-tree modification).
* **Classification:** **test defect / stale expectation.** Not a migration defect: the ordering/no-duplicate properties the same test asserts still hold, and no historical migration is modified (`git status --porcelain -- supabase/` shows only untracked `??` new migrations, no `M` entry).
* **Verdict phrasing:** *the test is failing; the migrations are not broken.*
* **Impact:** production functionality — none; FINAL-03 security — none; FINAL-03 deployment — none; FINAL-03 data preservation — none; FINAL-03 backup/DR — none; FINAL-03 acceptance — none directly (see §9).

### F2 — I1 `test_i1_migration_is_the_latest_migration`

* **File / function:** `backend/tests/unit/data/test_i1_insight_migration.py:50-88`.
* **Feature under test:** I1 Insight persistence migration position ("I1 exists at its ratified position").
* **Exact error:** `AssertionError` at `:63` — the `later` list (all migrations after I1) is not a member of the six hard-coded literal lists (largest = 5 entries ending `20261007000000_p8_insight_data_quality_reproducibility.sql`). The failure message shows the actual list continuing past `20261008000000_p16r5_result_reportability_lifecycle.sql`, `…`.
* **What "latest" means here:** not the chain tip — the test allows I1 to be followed by an *enumerated* set of later migrations (`[]`, I2, I2+I4, I2+I4+rate-limit, that+data-quality). It is an allow-list snapshot.
* **Actual chain:** I1 (`20261001000000_p8_i1_insight_persistence.sql`) is followed by **22** migrations (last `20261029000000_ct_final_03_staff_workload_rls.sql`).
* **Predicate replay without FINAL-03:** **20** migrations after I1, last `20261027000000_ct_backup_02_backup_sets_and_verification.sql` — still not in any allowed list → **fails without FINAL-03**. The first "illegal" entry is `20261008000000_p16r5_…`, which predates FINAL-03 by ~3 weeks.
* **Test last touched:** mtime 2026-09-23, last commit `6605475` (2026-09-23); tracked and clean.
* **Classification:** **test defect / stale expectation** (allow-list snapshot never extended after the P16R5 work).
* **Verdict phrasing:** *the test is failing; the migration chain is behaving as designed (strictly increasing, unique timestamps).*
* **Impact:** none of the listed dimensions.

### F3 — I2 `test_i2_migration_is_the_latest_and_scoped_to_one_policy`

* **File / function:** `backend/tests/unit/data/test_i2_insight_authorization_contracts.py:71-94`.
* **Feature under test:** I2 Insight authorisation migration — position **and** policy scope.
* **Exact error:** `AssertionError: assert '202610290000...kload_rls.sql' == '202610070000...ucibility.sql'` at `:79` (`assert names[-1] == "20261007000000_p8_insight_data_quality_reproducibility.sql"`); the assertion message prints the last three names: `['20261027000000_ct_backup_02_backup_sets_and_verification.sql', '20261028000000_ct_final_03_rls_security_remediation.sql', '20261029000000_ct_final_03_staff_workload_rls.sql']`.
* **Expected vs actual position:** expected tip `20261007000000_p8_insight_data_quality_reproducibility.sql`; actual tip `20261029000000_ct_final_03_staff_workload_rls.sql`. Without FINAL-03 the tip would be `20261027000000_ct_backup_02_…` → **the tip assertion fails either way** (the chain already had 9 later migrations before FINAL-03).
* **Is the policy-scope half still valid?** **Yes — it passes.** Independently re-evaluated on `_I2_MIGRATION = 20261002000000_p8_i2_insight_authorization.sql` with the test's own helpers: `ddl.count("CREATE POLICY") == 1` ✅, `ddl.count("DROP POLICY") == 1` ✅, and none of `CREATE TABLE / ALTER TABLE / CREATE INDEX / GRANT / REVOKE` appears in the DDL ✅. Only the stale `names[-1]` assertion fails, and it fails before the scope block is reached.
* **Test last touched:** mtime 2026-09-23, last commit `6605475` (2026-09-23); tracked and clean.
* **Classification:** **test defect / stale expectation** on the position half only; the scope half is intact and passing.
* **Verdict phrasing:** *the test is failing; the I2 policy scope it also guards is still correct.*
* **Impact:** none of the listed dimensions; FINAL-03 security unaffected (I2 is a distinct earlier authorisation change-set).

### F4 — P17 `test_p17_does_not_reuse_or_edit_a_historical_timestamp`

* **File / function:** `backend/tests/unit/data/test_p17_migrations.py:107-114`.
* **Feature under test:** P17 migration governance — no reuse/edit of historical timestamps.
* **Exact error:** `AssertionError: unexpected migration after the P16 baseline: 20261029000000_ct_final_03_staff_workload_rls.sql` at `:112`.
* **What it considers problematic:** any migration whose timestamp is greater than `_P16_BASELINE = 20261009000000` that is **not** a member of the fixed six-migration P17 set.
* **Which migrations violate the predicate:** **9** with FINAL-03 present — `20261021000000_ct02_audit_ledger_hardening`, `20261022000000_ct02_report_sharing`, `20261023000000_ct02_scheduled_reporting`, `20261024000000_ct_final_01_documents_bucket_size_limit`, `20261025000000_ct_step2_documents_bucket_size_alignment`, `20261026000000_ct_backup_01_backup_jobs`, `20261027000000_ct_backup_02_backup_sets_and_verification`, `20261028000000_ct_final_03_rls_security_remediation`, `20261029000000_ct_final_03_staff_workload_rls`; **7 without FINAL-03** (the same list minus the last two).
* **Are those migrations legitimate?** Yes — each is a separate authorized work package (CT-02 audit/reporting, FINAL-01, STEP2, BACKUP-01/02, FINAL-03), and all use their own fresh, unique timestamps. There is **no timestamp reuse**: `versions == sorted(set(versions))` holds across all 98 files (F1 evidence), and `supabase/migrations` contains no modified historical file.
* **Did the issue exist before FINAL-03?** Yes, for 7 of the 9 offenders; the first offender (`20261021…ct02`) predates FINAL-03 by a week.
* **Test last touched:** mtime 2026-09-26, last commit `ba19ccd` (2026-09-26); tracked and clean.
* **Classification:** **test defect / stale expectation** — a snapshot rule ("everything newer than the P16 baseline belongs to P17") that later legitimate features cannot satisfy by construction. It is **not** a genuine migration-governance violation: the real governance properties (unique, strictly increasing, never-edited historical files) hold.
* **Verdict phrasing:** *the test is failing; migration governance itself is healthy.*
* **Impact:** none of the listed dimensions.

### F5 — `test_suggest_parses_clean_invoice`

* **File / function:** `backend/tests/unit/engines/test_extraction_suggestions.py:23-34` (`assert d["date"] == "15/01/2026"` at `:30`; also `assert out["unresolved"] == []` at `:34`).
* **Implementation under test:** `backend/services/extraction_suggestions.py::suggest` (`:112-242`), which delegates to `engines.extraction.DocumentExtractionEngine` and `engines.invoice_extraction`.
* **Fixture / input:** the module-level `_CLEAN` invoice text (supplier, invoice number, `Invoice date: 15/01/2026`, `Electricity consumption: 12500 kWh`, net/total amounts).
* **Expected vs actual (reproduced read-only, no mutation):**

  | Key | Test expects | Actual |
  |---|---|---|
  | `date` | `"15/01/2026"` | `"2026-01-15"` (plus `date_raw: "15/01/2026"`) |
  | `unresolved` | `[]` | `['billing_period']` |
  | supplier / invoice_number / quantity / unit / activity / amounts | as asserted | match (plus `net_amount`, `gross_amount`, `extraction_evidence: {'supplier_source': 'labelled'}`) |

* **Immediate cause:** date normalisation to ISO (with the printed value preserved as `date_raw`).
* **Deeper root cause:** **fixture/test drift, not an implementation regression.** `services/extraction_suggestions.py` is **tracked, unmodified** (clean working tree) and last changed by commit `ad07cd4` — *"feat(p12-impl-01): PDF extraction foundation - supplier/customer headers, billing period, date normalisation, trustworthy line items"* (2026-09-24). The failing test file is **older**: last commit `077c866` (2026-08-27), mtime 2026-09-19 — five days **before** the P12-IMPL-01 change — and was never updated. The new contract is itself asserted by a newer, currently **green** suite: `backend/tests/unit/services/test_p12_impl_01_invoice_extraction.py` (`69 passed`), which explicitly requires `data["date"] == "2026-02-02"`, `data["date_raw"] == "Feb 02, 2026"` (`:118-122`) and `data["extraction_evidence"]["supplier_source"] == "labelled"` (`:38-39`).
* **Production impact:** the function **is** used by production paths — `backend/api/v3_documents.py:138-149` (upload text-extraction → `suggested_data` in the response) and `backend/services/automatic_extraction.py:39`. The observed behaviour is the *intended* P12 contract (ISO date + raw preserved); the front-end reads the date from `invoice_date || date` (`frontend/src/v3/customer/ProcessingItemWorkspace.jsx:94-106`), which accepts either form.
* **Classification:** **test defect / stale expectation** (two stale expectations in one test).
* **Impact:** none of the listed dimensions.

### F6 — `test_suggest_missing_fields_leave_unresolved`

* **File / function:** `backend/tests/unit/engines/test_extraction_suggestions.py:50-59` (failing assertion `:54`).
* **Input:** `"We hope you enjoyed your stay. Please remit 42.00 soon.\n"` (no supplier, invoice number, date, quantity/unit or activity keyword).
* **Exact error:** `AssertionError: assert {'extraction_evidence': {...}} == {}` — *"Left contains 1 more item"*.
* **Actual output (reproduced):** `suggested_data = {'extraction_evidence': {'supplier_header': {'strategy': 'header_block', 'candidates': [], 'reason': 'no candidate line'}}}`, `unresolved = ['activity', 'billing_period', 'date', 'invoice_number', 'quantity/unit', 'supplier']`.
* **Immediate cause:** the implementation always records a diagnostic `extraction_evidence` block when the supplier-header strategy runs (`extraction_suggestions.py:152-159`, attached at `:234-235`), so `suggested_data` is never empty for non-empty input.
* **Is the "never fabricate" intent preserved?** **Yes** — no field value is invented: zero resolvable fields, and the unresolved list carries all six unresolved items (`:206-232`). The test's *semantic* intent still holds; only its `== {}` literal is now too strict.
* **Test last touched:** same stale file as F5 (mtime 2026-09-19).
* **Classification:** **test defect / stale expectation** (unresolved-field semantics are correct; the dict carries diagnostics).
* **Impact:** none of the listed dimensions.

### F7 — `test_suggest_no_fabrication_on_garbage`

* **File / function:** `backend/tests/unit/engines/test_extraction_suggestions.py:78-82` (failing assertion `:81`).
* **Input:** `"asdf qwerty !!!! 12345 zzz yyy"`.
* **Exact error:** `AssertionError: assert {'extraction_evidence': {...}} == {}` (identical shape to F6).
* **Actual output (reproduced):** `suggested_data = {'extraction_evidence': {'supplier_header': {'strategy': 'header_block', 'candidates': [], 'reason': 'no candidate line'}}}`; `unresolved` has 6 entries (so the sibling assertion `len(out["unresolved"]) >= 4` at `:82` would pass).
* **Immediate / deeper cause:** as F6 — the added evidence key, not fabricated values. The garbage-protection intent (no invented field values) is intact.
* **Classification:** **test defect / stale expectation.**
* **Impact:** none of the listed dimensions.

**F5-F7 common finding:** all three are stale assertions in the *oldest* extraction test file against the deliberately changed P12-IMPL-01 contract; the same behaviour is asserted (and green) in `test_p12_impl_01_invoice_extraction.py`. No evidence of an implementation regression: the implementation file is tracked/clean, and no other test in the file group regressed (4 passed in the old file + 69 passed in the new one).

---

## 6. Complete list of the 8 skips

| # | Node ID (exact) | Skip reason (as recorded) |
|---|---|---|
| S1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_only_the_two_authorised_migrations_differ_from_the_release` | `release commit 32083ee not available locally` |
| S2 | `tests/unit/data/test_f_t1_001_audit_activity_sql_typing.py::test_repository_statements_execute_on_postgres` | `local Demo Lab database not configured (set DEMO_LAB_DATABASE_URL)` |
| S3 | `tests/unit/data/test_f_t1_001_audit_activity_sql_typing.py::test_organisation_filter_reads_only_the_requested_org` | `local Demo Lab database not configured (set DEMO_LAB_DATABASE_URL)` |
| S4 | `tests/unit/data/test_i2_insight_rls_live.py::test_client_may_persist_only_human_authored_messages` | `INSIGHT_RLS_TEST_DSN is not set (the live RLS test runs only against a disposable database)` |
| S5 | `tests/unit/data/test_i2_insight_rls_live.py::test_creator_private_visibility_holds_live` | same |
| S6 | `tests/unit/data/test_i2_insight_rls_live.py::test_cross_organisation_read_and_write_are_denied_live` | same |
| S7 | `tests/unit/data/test_i2_insight_rls_live.py::test_suspended_organisation_is_blocked_for_the_client_path` | same |
| S8 | `tests/unit/data/test_i2_insight_rls_live.py::test_service_role_writes_the_reserved_author_kind` | same |

Distribution: 1 + 2 + 5 = **8**. No other module in `tests/unit` contains a skip in this run
(verified from the JUnit XML across all 4,782 nodes).

---

## 7. Detailed investigation of each skip

### S1 — D17 release-comparison guard

* **Where declared:** **runtime `pytest.skip`** inside a loop — `test_d17_provider_ownership_migration_revision.py:239`, reached when `git show 32083ee:supabase/migrations/<name>` returns non-zero (`:238`).
* **What it is meant to do:** "Part C guard: no other migration may change in this revision" — compare every migration against release commit `RELEASE_SHA = "32083ee"` and assert only D32/D35 differ.
* **Why it actually skips (established, read-only):** the loop iterates the **current** 98 file names, but the release commit does not contain all of them. Verified:

  | Probe | Result |
  |---|---|
  | `git cat-file -t 32083ee` | `commit` — **the commit exists locally** |
  | `git show 32083ee:supabase/migrations/20260800000000_rc2_schema.sql` | exit 0 — the old path exists at that commit |
  | `git show 32083ee:supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql` | **exit 128** |
  | `git show 32083ee:supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql` | **exit 128** |
  | Count of current migrations absent at `32083ee` | **27** of 98 (everything from `20260928000000_p8_fs_activity_clarifications.sql` onward) |
  | Sibling `test_gate4_migration_is_untouched` (same file, same SHA) | **PASSED** in this run (its target migration does exist at the release commit) |

* **Root cause:** the skip reason is **inaccurate** — the release commit *is* available; the *paths* are not, because the guard iterates current names rather than the release-commit names. The guard therefore silently disables itself in the current repository state. The first absent migration (`20260928000000…`) long predates FINAL-03, so this skip is **not** FINAL-03-caused; without FINAL-03, 25 paths would still be absent.
* **Intentional?** The *gate* is intentional (a release-diff guard); the *vacuous outcome* is an unintended consequence of repository growth, and the message misreports why.
* **Production feature?** No — repository/integrity governance only.
* **Classification:** **D — TEST/REPOSITORY HYGIENE** (guard no longer executes; misleading skip reason). Consequence: the "no other migration changed in this revision" protection is currently **not** providing coverage — although the same property is independently supported by the fact that no historical migration file is modified (`git status --porcelain -- supabase/` → only `??` new files).

### S2, S3 — Demo-Lab SQL typing runtime guards

* **Where declared:** **`@pytest.mark.skipif(not os.environ.get("DEMO_LAB_DATABASE_URL"), reason="local Demo Lab database not configured (set DEMO_LAB_DATABASE_URL)")`** — `test_f_t1_001_audit_activity_sql_typing.py:160-163` and `:191-194` (declarative, module-level environment detection).
* **What they test:** that the statements `data/reporting.py` actually builds **prepare** against a real PostgreSQL (the exact operation that produced the F-T1-001 `uuid = text` HTTP 500), and that the organisation id is passed as a bind parameter.
* **Why they skip:** the environment variable `DEMO_LAB_DATABASE_URL` is not exported in the pytest process. The test file documents this deliberately (`:22-23`): *"It is skipped unless `DEMO_LAB_DATABASE_URL` is set, and performs no reads or writes beyond statement preparation"*.
* **Coverage retained in this run:** the file's static guards **ran and passed** (`6 passed`), including the cast guard and the parameterisation guards.
* **Intentional?** Yes — documented DSN gate; `DEMO_LAB_DATABASE_URL` is the documented Demo-Lab variable (`tools/demo_lab/seed_factors.py:124-144`).
* **Production feature?** Yes — the guarded property backs `GET /api/v3/reporting/audit-activity` (the F-T1-001 defect). The *static* half still protects the cast; only the *prepare-against-real-Postgres* half is unexecuted here.
* **Missing condition:** `DEMO_LAB_DATABASE_URL` pointing at a local Demo-Lab/disposable database. **Not set** by this investigation (environment change is outside the read-only boundary).
* **Classification:** **E — INTENTIONAL / ACCEPTABLE SKIP** (with a noted residual: the real-Postgres half of F-T1-001 was not re-executed in this environment).

### S4-S8 — Insight live-RLS suite (5 tests)

* **Where declared:** **runtime `pytest.skip`** inside the shared helper `_dsn()` — `test_i2_insight_rls_live.py:45-50`, called by the connection fixture at `:64` (skip text points at the five call sites: `:137, :160, :182, :198, :220`).
* **What they test:** the REAL Insight RLS policies on a real database — author-kind integrity, creator-private visibility, cross-organisation read/write denial, suspended-organisation blocking, service-role author-kind write.
* **Why they skip:** `INSIGHT_RLS_TEST_DSN` is not set. The file's docstring (`:9-17`) documents the gate as deliberate: fresh UUIDs per run, assertions scoped to the run's own rows, one transaction always rolled back, DSN refused unless it names a disposable database, and *"the suite skips when no DSN is configured — it never falls back to a persistent one."* The guard is additionally hardened: a DSN naming `postgres`, `carbon_ledger`, `carbontally`, `carbontally_demo_local`, `carbontally_qa_phase8` or containing `demo/qa/investor/prod/live` raises rather than running (`:36-57`) — consistent with AGENTS.md §55.1 / F-046-1.
* **Independent corroboration that these skips are the known, intended state:** `docs/verification/OHD-P8-I2-INSIGHT-AUTHORIZATION-REVERIFICATION-20260921.md:242` records *"Skipped tests: the five live-RLS tests (require `INSIGHT_RLS_TEST_DSN`; deliberately skipped without it). No other skips."*, and `:296` notes the suite total *"include[s] 8 skips unless a disposable DSN is exported (5 of them live-RLS tests)"* — i.e. the current 8-skip figure is a previously documented, unchanged condition. `docs/verification/OHD-P8-I3-INSIGHT-TOOLS-REVERIFICATION-20260921.md:203` shows `63 collected / 63 passed / 0 skipped` **when the DSN was set** — evidence the tests are functional, not broken.
* **Whole file skipped:** yes — this module contributes 5 skips and 0 passes; its live behaviour is therefore unverified in this environment.
* **Production feature?** Yes — Insight message authorisation (I1/I2) is an authenticated production feature. Note: this is **I2 Insight RLS**, a distinct earlier change-set from FINAL-03's 44-table RLS remediation (which has its own live suite, `tests/integration/test_final_03_rls_remediation_live.py`, DSN-gated by `FINAL_03_RLS_TEST_DSN`, last touched 2026-10-02, and already independently verified — 30 passed / 1 skipped live, 12 passed / 19 skipped static-only).
* **Missing condition:** `INSIGHT_RLS_TEST_DSN` naming a disposable database (e.g. a dedicated `carbontally_test`-style DB). **Not set** by this investigation, and the live tests were **not** executed (they perform live writes inside a rolled-back transaction, which is mutation outside the read-only boundary).
* **Material effect of the skip:** the field-level filtering of these five tests is already covered by **unit-level static/structural guards** in the same module family — the sibling `test_i2_insight_authorization_contracts.py` failed only on the position assertion and its policy-scope half **passes** (F3). So this is a *live-execution* coverage gap, not a total absence of coverage.
* **Classification:** **E — INTENTIONAL / ACCEPTABLE SKIP.**

---

## 8. Root-cause classification (summary)

| Root-cause class | Findings | Count |
|---|---|---|
| Test defect / stale expectation (frozen counts, allow-lists, chain-tip assertions, pre-P12 contract) | F1, F2, F3, F4, F5, F6, F7 | 7 |
| Repository/test hygiene (guard vacuous + inaccurate skip reason) | S1 | 1 |
| Intentional environment-gated skip (DSN absent, documented, hardened) | S2, S3, S4, S5, S6, S7, S8 | 7 |
| Production-code defect | — | 0 |
| Migration-chain / ordering defect | — | 0 |
| Dependency/tooling defect | — | 0 |
| Genuine data/fixture defect | — | 0 |
| Intentionally unsupported behaviour | — | 0 |
| Unknown / inconclusive | — | 0 |

**Not one of the 15 findings is a product-code defect or a migration-governance defect.** The four
migration-chain failures are assertions about *how many* and *which* migrations exist — never about
whether the migrations are correct. The three extraction failures are assertions about the *shape* of
a deliberately extended contract. The eight skips are gates (one degraded, seven by design).

---

## 9. FINAL-03 relevance classification

Every finding is assessed against: production functionality · FINAL-03 security · FINAL-03 deployment ·
FINAL-03 data preservation · FINAL-03 backup/DR · FINAL-03 acceptance.

* **F1-F4 (migration-chain assertions):** None asserts a FINAL-03 property. Each fails identically with
  the two FINAL-03 migrations excluded (96 ≠ 71; 20 ≥ allowed 5; tip = `20261027…` ≠ `20261007…`;
  7 post-baseline offenders), so FINAL-03 is demonstrably **not** the cause. FINAL-03's own migration
  governance was independently verified earlier and was not reopened (its two files' digests are
  unchanged, §10). **FINAL-03 acceptance:** these are pre-existing red tests unrelated to the
  FINAL-03 change-set; they do not attest any FINAL-03 property. Classification **C** (as expressed via
  the findings-level class **D** for test/hygiene issues).
* **F5-F7 (extraction suggestions):** no FINAL-03 relation of any kind (different subsystem, already
  committed in `ad07cd4` on 2026-09-24, unmodified since). **C**.
* **S1-S8 (skips):** none is caused by FINAL-03 (S1's first absent path is `20260928000000…`;
  S2/S3 gate on `DEMO_LAB_DATABASE_URL`; S4-S8 gate on `INSIGHT_RLS_TEST_DSN` for I2 Insight RLS, not
  FINAL-03's 44 tables). FINAL-03's own live suite is a separate file (see §7, S4-S8). **C** / **E**.
* **No finding is classified A (FINAL-03 BLOCKING) or B (FINAL-03 RELEVANT BUT NOT CURRENTLY BLOCKING):**
  none of the 15 is caused by FINAL-03, none is required for FINAL-03 acceptance, and the FINAL-03
  security properties are verified independently of them. The only *near-miss* worth the PO's attention
  is the **degraded migration-governance guard (S1)** plus the four stale migration-chain guards
  (F1-F4): together they mean migration-ordering governance is enforced by **less** automated coverage
  than the test count suggests — a repository-readiness observation, not a FINAL-03 blocker.
* **No finding is classified F:** every one of the 15 was reproduced or traced to a concrete,
  evidenced condition. Nothing was left to inference.

---

## 10. R1 non-regression confirmation

| Check | Evidence | Result |
|---|---|---|
| R1 test itself passes | JUnit node `tests.unit.backup.test_jobs.TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain` present with **no** `<failure>`/`<skipped>` child (self-closing) in `/tmp/cstr_tsi_unit.xml` | **PASS** |
| Owning class / file | `TestMigrationAlignment` 10 passed; `tests.unit.backup.test_jobs` 83 passed | **PASS** |
| No skip introduced by R1 | `grep -c "pytest.skip\|skipif\|xfail" backend/tests/unit/backup/test_jobs.py` → **0** | Confirmed |
| R1's change window | R1 edited only `backend/tests/unit/backup/test_jobs.py` (mtime 2026-10-03 01:56:43) + its report | Confirmed |
| None of the 7 failures caused by R1 | All 7 live in four other subsystems (migration-count tests ×4, extraction engine ×3); R1 touched only one test file and no production code; the 7 fail identically in the pre-R1 independent-verification baseline (9 failed/4,765 passed) less the R1 item | Confirmed |
| No skip caused by R1 | The 8 skips are declared in `test_d17_…` (mtime 2026-09-22), `test_f_t1_001_…` (2026-09-20) and `test_i2_insight_rls_live.py` (2026-09-21) — all **predate** R1 | Confirmed |
| FINAL-03 RLS migrations unmodified | digests recomputed this run: `20261028000000…` → `ca461c9c5be712b8c5bfaaa8200e2a3be83c5fb55990c3e118446b86904ecb15`; `20261029000000…` → `0775fa68388a5e697965b7500284a653df4a96336218ea5b2abbb2b98f7b1cb3` — identical to the R1-verification values; no `supabase/` file written | **Unchanged** |

The FINAL-03 RLS remediation and the R1 verification were **not** reopened.

---

## 11. Git / repository-state observations (read-only)

| Observation | Value |
|---|---|
| HEAD | `cabdca8380415e73a25cf23eb393d0b15c0af391` (unchanged before and after the investigation) |
| Branch | `p8-release-reconciled` |
| Last commit | `cabdca8` — *"docs(CT-FINAL-01): final security-fix and verification report"*, 2026-09-29 11:02:10 +0600 |
| Working tree | 181 porcelain entries; **123 untracked**; `git diff --stat` = `58 files changed, 4417 insertions(+), 790 deletions(-)` (pre-existing FINAL-01/02/03 + BACKUP + other WIP — not created or touched here) |
| `supabase/` status | only five untracked (`??`) migrations (`20261025…`, `20261026…`, `20261027…`, `20261028…`, `20261029…`); **no `M` (modified) entry** → no historical migration altered |
| Migration files | 98 `.sql` in `supabase/migrations`; timestamps unique and strictly increasing (asserted and independently re-evaluated) |
| Stash / reflog | `git stash list` empty; no new reflog entry from this work |
| Was anything written by this investigation? | **No.** `find . -newermt "2026-10-03 03:00:00"` (excluding `.git`, `.venv`, `node_modules`, `__pycache__`, `.pytest_cache`) → **empty**. Only `backend/.pytest_cache/` (pytest's own bookkeeping) and test artefacts written under `/tmp` changed |
| Artefacts produced | `/tmp/cstr_tsi_unit.xml` (JUnit XML), terminal transcripts — outside the repository |
| Deployment / production | not contacted; no deploy, no Render/Vercel access, no commit, no push |

---

## 12. Limitations

1. **No mutation was used to prove the "without FINAL-03" case.** Excluding the two FINAL-03
   migrations from the directory was evaluated by replaying each test's own predicate against the
   filename list minus those two names — it demonstrates the assertion outcome, not a real file-system
   state. No file was moved (boundary honoured).
2. **DSN-gated live suites were not executed.** `INSIGHT_RLS_TEST_DSN` (S4-S8) and
   `DEMO_LAB_DATABASE_URL` (S2, S3) were deliberately not set, and the live tests were not run: the
   Insight suite performs live RLS writes (inside a rolled-back transaction) and setting environment
   state is outside the read-only boundary. Consequence: their live behaviour was **not** re-verified
   here; the modules' static/structural guards and the historical independent verifications were used
   instead.
3. **`tests/integration` was not part of the baseline.** Only `tests/unit` was executed, as mandated.
   `pyproject.toml` sets `testpaths = ["tests/unit", "tests/integration"]`, so a bare `pytest` would
   collect more tests and possibly more skips — an unmeasured quantity in this investigation.
4. **"Pre-existing" is established relative to FINAL-03, not to the whole history.** For F1-F4 the
   predicate replay proves the failure is independent of FINAL-03; the specific change-set that first
   made each expectation stale was inferred from file/commit dates and the required migration ordering
   (e.g. F2/F3 stale since `20261008000000_p16r5…`; F4 stale since `20261021000000_ct02…`). No attempt
   was made to bisect commits (that would require checkouts — forbidden).
5. **Root causes for F5-F7 are attributed by construction and dates, not by bisect.** The
   implementation is clean/tracked and the newer contract suite passes, which is strong but not a
   bit-for-bit proof that only the P12-IMPL-01 commit changed the behaviour; a `git show` of the
   pre-P12 version of `extraction_suggestions.py` was not diffed (not needed for the conclusion, and
   the engine path also depends on `engines/extraction.py` and `engines/invoice_extraction.py`, all
   three last modified by the same commit).
6. **Whether `extraction_evidence` should be inside `suggested_data`** is a design question, not a
   defect finding. Evidence available: the API returns the whole dict
   (`api/v3_documents.py:143`), the customer workspace builds its form from an explicit 8-key mapping
   so the diagnostics key cannot reach `extracted_data` through that path
   (`frontend/src/v3/customer/ProcessingItemWorkspace.jsx:94-106`), and the module docstring states
   the value must not be written without human confirmation. No production impact was observed; the
   question is recorded as **PO/design decision material only** (§14).
7. **One skip's reason string is wrong (S1)**, but whether the intended guard should be re-based onto
   the release commit's own file list is a design choice — not resolved here.
8. **Warning count:** 14 deprecation warnings (Starlette/FastAPI `regex=`, `HTTP_422…`) — informational,
   not failures, and not investigated.

---

## 13. Consolidated findings table (all 15)

| ID | Test / Skip | Type | Root Cause | Production Impact | FINAL-03 Classification | Action Needed |
|---|---|---|---|---|---|---|
| F1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | Failing test (stale invariant) | Frozen `len(names) == 71`; chain is 98 (96 without FINAL-03). Other assertions in the test pass | None. Migration ordering/no-duplicate governance still holds | **D** (test/hygiene; not FINAL-03-caused) | Separate authorized test update (replace count with a growth-safe invariant) — PO decision |
| F2 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | Failing test (stale allow-list) | Hard-coded allow-list of ≤5 migrations after I1; actual 22 (20 without FINAL-03) | None | **D** | Separate authorized test update |
| F3 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | Failing test (stale tip assertion) | `names[-1] == 20261007000000_…`; actual tip `20261029000000_…` (fails without FINAL-03 too). Policy-scope half **passes** | None. I2 policy scope intact | **D** | Separate authorized test update (keep the scope assertions) |
| F4 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | Failing test (stale snapshot rule) | Requires every migration newer than `_P16_BASELINE=20261009000000` to be in the fixed P17 set; 9 offenders (7 without FINAL-03); no timestamp reuse exists | None. Historical migrations unmodified; timestamps unique/increasing | **D** | Separate authorized test update (assert uniqueness/monotonicity, not set membership) |
| F5 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | Failing test (stale expectation, ×2) | Test predates P12-IMPL-01 (`ad07cd4`, 2026-09-24); impl now returns ISO `date` (+`date_raw`) and `unresolved == ['billing_period']` | None. Behaviour is the intended, separately-tested P12 contract (69 passed) | **D** | Separate authorized test update |
| F6 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | Failing test (stale expectation) | `suggested_data == {}` no longer holds: the impl attaches an `extraction_evidence` diagnostics block; no values fabricated | None. Unresolved semantics intact (6 items listed) | **D** | Separate authorized test update |
| F7 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | Failing test (stale expectation) | Same as F6 — `extraction_evidence` key present on garbage input; zero field values invented | None | **D** | Separate authorized test update |
| S1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_only_the_two_authorised_migrations_differ_from_the_release` | Skip (runtime `pytest.skip`, `:239`) | Loop iterates **current** 98 names; **27** are absent at release commit `32083ee` (commit exists; paths do not) → guard self-disables with an inaccurate reason | None. Guard coverage degraded (repository integrity) | **D** (hygiene; misleading/vacuous guard) | Separate authorized hygiene item: re-base the comparison on the release commit's own file list and correct the reason string |
| S2 | `tests/unit/data/test_f_t1_001_audit_activity_sql_typing.py::test_repository_statements_execute_on_postgres` | Skip (`@pytest.mark.skipif`, `:160-163`) | `DEMO_LAB_DATABASE_URL` not set (documented DSN gate; statement-preparation only) | None. Static guards still run (6 passed) | **E** | Optional: run with a disposable DSN in CI |
| S3 | `tests/unit/data/test_f_t1_001_audit_activity_sql_typing.py::test_organisation_filter_reads_only_the_requested_org` | Skip (`@pytest.mark.skipif`, `:191-194`) | Same as S2 | None | **E** | Optional: same as S2 |
| S4 | `tests/unit/data/test_i2_insight_rls_live.py::test_client_may_persist_only_human_authored_messages` | Skip (runtime `pytest.skip` via `_dsn()`, `:45-50`; site `:137`) | `INSIGHT_RLS_TEST_DSN` not set (documented by-design gate; DSN must name a disposable DB; forbidden-DSN guard at `:36-57`) | None. Live RLS behaviour unexecuted here; structural coverage retained | **E** | Optional: provide a disposable DSN in CI (prior verifications show 63/63 pass when set) |
| S5 | `tests/unit/data/test_i2_insight_rls_live.py::test_creator_private_visibility_holds_live` | Skip (same gate; site `:160`) | Same as S4 | None | **E** | Optional: same as S4 |
| S6 | `tests/unit/data/test_i2_insight_rls_live.py::test_cross_organisation_read_and_write_are_denied_live` | Skip (same gate; site `:182`) | Same as S4 | None | **E** | Optional: same as S4 |
| S7 | `tests/unit/data/test_i2_insight_rls_live.py::test_suspended_organisation_is_blocked_for_the_client_path` | Skip (same gate; site `:198`) | Same as S4 | None | **E** | Optional: same as S4 |
| S8 | `tests/unit/data/test_i2_insight_rls_live.py::test_service_role_writes_the_reserved_author_kind` | Skip (same gate; site `:220`) | Same as S4 | None | **E** | Optional: same as S4 |

Classification legend: **A** FINAL-03 blocking · **B** FINAL-03 relevant, not blocking · **C** pre-existing/unrelated · **D** test/repository hygiene · **E** intentional/acceptable skip · **F** inconclusive.
**Totals: A=0, B=0, C=0 (as the primary class; all 15 are FINAL-03-unrelated), D=8, E=7, F=0.**
(The four migration-chain failures and three extraction failures are FINAL-03-unrelated *and* hygiene issues; they carry the single primary class **D**, with FINAL-03 relevance recorded in the column above.)

---

## 14. Recommended follow-up decisions (for the PO — nothing implemented)

These are **recommendations only**; no fix, patch, migration, test edit or skip change was made.

1. **Authorise a single "stale migration-chain guard" hygiene item** covering F1-F4 (and optionally the
   four identical-pattern defects are the same class): replace frozen counts / chain-tip assertions /
   enumerated allow-lists with growth-safe invariants — adjacency, strict monotonicity, uniqueness, and
   "the file is not modified relative to its introducing commit". Do **not** fold this into FINAL-03.
2. **Authorise a test-refresh item for F5-F7** that re-bases `backend/tests/unit/engines/test_extraction_suggestions.py`
   onto the P12-IMPL-01 contract (ISO `date` + `date_raw`; assert the *absence of fabricated field
   values* rather than an empty dict; keep the "no side effects" test as is). The engine must not be
   changed without a PO/design decision.
3. **Decide whether `extraction_evidence` should remain inside `suggested_data`** (it is returned by the
   upload response and consumed only through explicit field mappings today). Options: keep (diagnostics
   for review), or move to a sibling response key. Purely a design decision; no defect demonstrated.
4. **Authorise a decision on the S1 release-diff guard:** re-base the comparison on the release
   commit's own file list (so it runs instead of skipping) and correct the skip reason, or explicitly
   retire the guard. Until then, migration-integrity coverage is weaker than the suite implies.
5. **Decide whether CI should export disposable DSNs** for S2-S8 so the live halves execute
   (both suites are already hardened against persistent targets). If CI intentionally omits them,
   record that expectation so the "8 skips" figure is understood as by design rather than as failure.
6. **Consider whether a `pytest` invocation for FINAL-03 acceptance should include `tests/integration`**
   (the FINAL-03 live suite is not in the unit run; integration results are a separate reporting line).
7. **No action required** for production functionality, FINAL-03 security, deployment, data
   preservation, or backup/DR on the evidence gathered: no product-code defect was found in any of the
   15 findings.

---

## 15. Final verdict

**CSTR-FINAL03-TEST-SUITE-INVESTIGATION-001 — COMPLETE — ALL 7 FAILURES + 8 SKIPS CLASSIFIED**

* The baseline was reproduced from scratch: **4,767 passed / 7 failed / 8 skipped / 0 errors /
  4,782 collected, 416.71 s** (JUnit-corroborated), matching the authorised figures exactly.
* All **7 failures** were individually reproduced, root-caused and classified as **test-side staleness**
  (frozen migration counts/allow-lists/chain-tip assertions; a pre-P12-IMPL-01 extraction contract).
  None is a production-code defect, a migration defect, or a FINAL-03 issue; the four migration-chain
  failures fail identically with the two FINAL-03 migrations excluded.
* All **8 skips** were individually identified and traced: 1 degraded release-diff guard with an
  inaccurate reason (**D**), 2 `DEMO_LAB_DATABASE_URL` gates and 5 `INSIGHT_RLS_TEST_DSN` gates, both
  documented by design and hardened against persistent targets (**E**).
* Nothing is caused by **R1** (which passes, with no skip introduced); the FINAL-03 RLS migrations are
  byte-identical to their verified digests; no repository file was written by this investigation; HEAD
  is unchanged and no commit/push/deploy/production contact occurred.
* No **A** or **B** classification was warranted. No remediation was performed or authorized.
  FINAL-03 is **not** declared closed by this report.
