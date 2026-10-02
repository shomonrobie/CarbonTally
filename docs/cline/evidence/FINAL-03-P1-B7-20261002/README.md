# FINAL-03 evidence pack — P1 / B7 remediation (2026-10-02, second pass)

This folder is the **live evidence** for cutover-package gate **P1** of
`docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md` §1, whose specification is
FINAL-02 §15.2 (the defect) and §17 (the position matrix). It is written to the §5 folder layout of
that package, and contains **only** the folders that the current pass can honestly fill.

| Folder | Contents | State in this pass |
| --- | --- | --- |
| `01-b7-gate/` | step 2 grep, backup-suite JUnit XML, soak timelines, drill report | **populated (this pass)** |
| `00-freeze/` | step 1 SHA, tag, `git status --porcelain` | **intentionally absent** — no commit was made or authorized in this pass, so there is no frozen SHA to record (that is gate **P2**, and the reason P1 is evidenced but not *satisfied*) |
| `02-b2prime/` … `08-pack/` | steps 3–22 | **absent** — not attempted in this pass; they require production access or owner decisions |

## What this pass did and did not do

- **Did:** reproduce model/harness evidence for gate P1 against local, loopback-only databases — two
  post-fix soaks (a schema-complete clone and the migration-behind database) plus a second
  migration-behind soak re-taken with the **final** harness revision, a pre-fix control, the canonical
  recovery drill (twice: against a fresh source and against the exact source of the FINAL-02 §16.5
  record), the canonical backup test suites (JUnit XML + captured stdout, EXIT=0), and the count
  reconciliation of the "275" figures.
- **Did not:** commit, stage, push, reset or clean anything; touch any production system; connect to
  any non-loopback database; change any product code, configuration, migration or test in the working
  tree as part of *this* evidence pass.

The remediation code itself (`backend/backup/jobs.py`, `backend/backup/service.py`,
`backend/backup/worker.py`, the new B7 test module and the revised soak tool) is **present in the
working tree and uncommitted**, exactly like the rest of the BACKUP file set listed in FINAL-02 §16.7.
That is why the correct gate statement is *"P1's clauses are verified locally; P1 is not yet satisfied
as a gate"* — see `01-b7-gate/README.md` §"Gate position".

## Contents of `01-b7-gate/` (final)

| Artifact | Result |
| --- | --- |
| `soak-b7-schema-complete.{json,log}` | 600 s, schema-complete clone — **CLEAN, 5/5 clauses** |
| `soak-b7-after-rev1.{json,log}` | 600 s, migration-behind, harness rev 1 — **CLEAN, 5/5 clauses** |
| `soak-b7-after-rev2.{json,log}` | 600 s, migration-behind, **final** harness — **CLEAN, 5/5 clauses** (`verdict_as_expected: true`) |
| `soak-b7-control-prefix.{json,log}` | pre-fix control — **leak reproduced** (so a clean verdict is not vacuous) |
| `junit-backup-suites.xml`, `pytest-backup-suites.stdout.txt` | two-path suite run — **275 tests, 0 failures, 0 errors, 0 skipped, EXIT=0** |
| `drill-post-fix-source-ct_final02_src.txt` | drill reproduces FINAL-02 §16.5 exactly |
| `drill-post-fix-source-ct_local_93d5cdd.txt` | drill against another local source — completes |
| `lease-site-grep.txt` | release site present on every lease path |
| `p1-suite-counts.txt`, `p1-count-reconciliation.txt`, `p1-b7-test-nodeids.txt` | counts and the "275" decomposition |
