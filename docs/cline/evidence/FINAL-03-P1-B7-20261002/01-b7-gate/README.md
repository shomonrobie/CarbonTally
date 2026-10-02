# `01-b7-gate/` — live evidence for cutover gate **P1 (B7)**

Gate P1 as specified in `CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md` §1:

> **B7 is fixed and verified.** The backup worker no longer leases a pooled connection without
> releasing it (`backend/backup/jobs.py`, and the same idiom in `backend/backup/service.py`); a missing
> backup table is a terminal, backed-off condition, not a per-tick error.
> *Shown by:* the fix is present in the frozen commit; the backup unit + integration suites are green;
> the canonical drill completes; a ≥10-minute soak against a schema-complete database shows **no**
> connection growth (no `/health` timeout).

The defect is FINAL-02 §15.2 (measured 2026-10-02, pre-fix). This folder is the post-fix evidence.

## 1. The defect and the fix (working tree, uncommitted)

| | Pre-fix (§15.2) | Post-fix (this pass) |
| --- | --- | --- |
| Lease site | `backend/backup/jobs.py:_pool_connection_factory` — `return await pool.acquire()` | the lease is returned to the pool on every path |
| Same idiom | `backend/backup/service.py` (create-backup path) | same correction |
| Missing table | `asyncpg.exceptions.UndefinedTableError` raised **every tick** — traceback per tick, unbounded | `backend/backup/worker.py:is_missing_backup_table()` (SQLSTATE `42P01` + `backup_` relation name) → **one** structured report, then back-off (`DEFAULT_MISSING_TABLE_BACKOFF_SECONDS`), re-armed after a successful tick |
| Observed effect | ≈1 connection per worker tick, monotonic; `/health` and DB-backed routes time out ≈45 s after start | flat pool (`size == idle`), `/health` responsive for the whole soak, 0 timeouts |

Mechanical cause, for the record: `await pool.acquire()` on an asyncpg `Pool` does not hand back a
bare connection *and* a release handle — `PoolAcquireContext.__await__` completes the acquire, so a
connection obtained that way is never released. The fix keeps the acquire/release paired on every
path, including the exception and cancellation paths (see the §4 node ids below).

`lease-site-grep.txt` is the raw step-2 grep of both files.

## 2. Artifact inventory

| Artifact | What it is | Produced by | Result |
| --- | --- | --- | --- |
| `soak-b7-schema-complete.json` / `.log` | **600 s soak, schema-complete database** (`ct_b7_schema_1790937075`, a schema-only clone of `ct_local_93d5cdd` with both BACKUP migrations applied: 136 public tables, `backup_jobs` with `kind`/`backup_set_id`/`verification_status`) | `tools/b7_pool_soak.py --duration 600 --label schema-complete --database-url … --allow-backup-tables --out …` | **CLEAN — 5/5 clauses true**, `verdict_as_expected: true`; 393 lease shortfalls observed / **393 cleared** (0 permanent) |
| `soak-b7-after-rev1.json` / `.log` | **600 s soak, migration-behind database** (`ct_local_93d5cdd`, no `backup_*` tables) — the §15.2 rehearsal condition | same tool, harness revision 1 | **CLEAN — 5/5 clauses true** (`verdict_as_expected: true`; 2,905 statements, 2 shortfalls / 2 cleared, `health_timeouts: 0`) |
| `soak-b7-after-rev2.json` / `.log` | the same run re-taken with the **final** harness revision (the shipped tool) | same tool, final revision | **CLEAN — 5/5 clauses true** (`verdict_as_expected: true`; 2,902 statements, 1 shortfall / 1 cleared, `health_timeouts: 0`) |
| `soak-b7-control-prefix.json` / `.log` | **control**: the pre-fix idiom (`return await pool.acquire()`) exercised by the same detector, run with `--legacy-idiom --expect-leak` | same tool, control mode | **leak reproduced** — 3 permanent shortfalls in `elapsed_s = 6.6` (the run self-stops on the 3rd), **0 cleared**; that the detector fires on a real leak is what makes a `clean` verdict above non-vacuous |
| `drill-post-fix-source-ct_final02_src.txt` | canonical recovery drill against **the same source DB as the FINAL-02 §16.5 record** | `tools/backup_recovery_drill.py --source ct_final02_src --target … --keep-target` | **completes, EXIT=0**; phases 1–2 clean; phase 3 `94 applied / 1 already present / 1 failed = 20260801000000_rc2_constraints.sql`; phase 4 the known harness truncate refusal — **identical to §16.5** |
| `drill-post-fix-source-ct_local_93d5cdd.txt` | the same drill against another local source | same tool, other `--source` | completes, EXIT=0; phases 1–2 clean; phase 3 failures are that source's own `auth.*` / `storage.buckets.file_size_limit` gaps |
| `p1-suite-counts.txt` | collection counts of the canonical backup suites | `pytest --collect-only -q` | `tests/unit/backup` **253** + `tests/integration/backup` **22** = **275** |
| `p1-b7-test-nodeids.txt` | the 12-node B7 regression module | `pytest --collect-only -q tests/unit/backup/test_b7_connection_lease.py` | 12 tests collected |
| `junit-backup-suites.xml` / `pytest-backup-suites.stdout.txt` | authoritative suite result, both paths, one run (re-taken at the end of this pass; XML `timestamp="2026-10-02T17:09:54.458948+06:00"`) | `pytest -q -p no:cacheprovider --junitxml=…` | **275 tests, 0 failures, 0 errors, 0 skipped, EXIT=0** (XML attributes: `tests="275" failures="0" errors="0" skipped="0"`) |
| `clone-dsn-used.txt` | the loopback DSN of the schema-complete clone | `mkclone.sh` | loopback-only, disposable |
| `lease-site-grep.txt` | step-2 grep evidence | `grep -n … backend/backup/jobs.py backend/backup/service.py` | the release sites are present on every path |

## 3. Clause-by-clause result

Soak clauses, as evaluated by the tool on the collected timeline (`clauses` in the JSON):

| Clause | `schema-complete` (600 s) | `after-rev2` (600 s) | `control-prefix` |
| --- | --- | --- | --- |
| `no_leased_connection_kept` | **true** | **true** | **false** (fires) |
| `health_pool_path_responsive` | **true** | **true** | **true — not fired**, and that is *not* exculpatory: the control stops itself once 3 permanent shortfalls are seen (`elapsed_s = 6.6`), long before §15.2's ≈45 s time-out horizon, so this clause never gets a chance to fire |
| `worker_loop_alive_for_the_whole_soak` | **true** | **true** | **true** |
| `missing_schema_reported_once` | **true** (schema present ⇒ expect **0** reports; 0 observed) | **true** (schema absent ⇒ expect **1** report; 1 observed) | n/a |
| `missing_schema_not_a_per_tick_error` | **true** | **true** (`worker_per_tick_failures = 0`) | n/a |
| **verdict** | **CLEAN (expected clean)** | **CLEAN (expected clean)** | **violations detected (expected)** — leak reproduced: **3** shortfalls observed, **0** cleared; EXIT=0 because the control is run with `--expect-leak` |

The control's decisive number is **3 observed / 0 cleared**: with the pre-fix idiom every shortfall
becomes permanent. Its `health_pool_path_responsive = true` is an artifact of the tool's early stop, not
of health — which is exactly why the control's *reason* for stopping is recorded here.

Headline numbers, schema-complete run: 2,862 worker statements over 600 s, **0** `missing-table`
errors, **318** `no-op` outcomes (`BackupJobConflictError` = the correct "someone else holds the job"
behaviour), `pool_size_max = 2`, `pool_idle_min = 1` (i.e. `size == idle` throughout),
`db_connections_max = 3`, 2,862 `/health` probes, `health_max_ms = 33.9`, **`health_timeouts = 0`**,
`worker_missing_table_reports = 0`.

Headline numbers, migration-behind run (harness revision 1 — `soak-b7-after-rev1.json`): 2,905 statements, `missing-table` on every statement (the
schema is genuinely absent — expected, and the point of the run), `worker_missing_table_reports = 1`
across 120 worker attempts, `worker_per_tick_failures = 0`, **`health_timeouts = 0`**, and the pool
*shrinks back to `size == idle == 1`* late in the run — the opposite of §15.2's monotonic growth.

Headline numbers, **`after-rev2`** (the final harness, authoritative — `soak-b7-after-rev2.json`):
`elapsed_s = 600.1`, database `ct_local_93d5cdd`, `backup_tables_present = []`, `statements = 2902` (all
`missing-table`), `lease_shortfalls_observed = 1`, `lease_shortfalls_cleared = 1`, `pool_size_max = 2`,
`pool_idle_min = 1`, `db_connections_max = 3`, `health_probes = 2902`, `health_max_ms = 41.5`,
**`health_timeouts = 0`**, `worker_attempts = 120`, `worker_missing_table_reports = 1`,
`worker_per_tick_failures = 0`, `violations = []`, `verdict = clean`, `expected = clean`,
`verdict_as_expected = true`.

**Transient vs permanent shortfalls.** The detector records a "shortfall" when a lease is not returned
immediately, and only counts it as a leak if it persists through quiescence. Schema-complete: 393
observed, **393 cleared** (0 permanent). Migration-behind: 2 observed / 2 cleared on harness revision 1
(`soak-b7-after-rev1.json`) and 1 observed / 1 cleared on the final revision — never a permanent one.
Control: 3 observed, **0 cleared** — every one permanent, which is why the verdict is not trustworthy
without the control.

## 4. Suites

`tests/unit/backup` + `tests/integration/backup` = **275 tests, 0 failures, 0 errors, 0 skipped,
EXIT=0** (`junit-backup-suites.xml` is authoritative; this terminal's shell integration swallows the
stdout summary line — FINAL-02 Appendix A — so the `.stdout.txt` and the XML should be read together).

The 12-node B7 module (`p1-b7-test-nodeids.txt`) covers: the pre-fix control double reproducing the
leak; lease return across repeated tick cycles; a tick never holding a connection *between* ticks;
lease return on the normal export path, on the raising path and on the **cancelled** path; an injected
bare connection keeping its own lifecycle; an injected acquire context being entered and released;
`is_missing_backup_table` matching only `backup_*` relations and recognising the asyncpg
`UndefinedTableError`; report-once + back-off; and re-arming after a successful tick.

**Count reconciliation (resolve this before quoting any number).** FINAL-02 §16.1 and FINAL-03 §5
quote **"275 unit + 22 integration"**. Measured decomposition:

- **275 = the four-path unit composite of FINAL-02 §16.1:** `tests/unit/backup` **241** +
  `tests/unit/api/test_backup_admin_api.py` **17** + `tests/unit/tools/test_backup_export.py` **8** +
  `tests/unit/tools/test_backup_recovery_drill_guard.py` **9**. The **241** is the **pre-fix** count:
  the B7 module is untracked (`?? backend/tests/unit/backup/test_b7_connection_lease.py`) and was
  excluded to reproduce the recorded figure.
- **22 = `tests/integration/backup`.**
- **Post-fix, the same four-path composite is 287**, because the new B7 module adds **12** tests to
  `tests/unit/backup` (**241 → 253**).
- **Coincidence to watch:** the *two-path* run `tests/unit/backup` + `tests/integration/backup` also
  totals **275** (**253 + 22**). That is not the §16.1 figure, and the two must not be conflated —
  always report the paths with the count. FINAL-02 §16.6's *314* is a third, different set (the seven
  §4.1 matrix files).

Collection counts as measured (all `--collect-only -q`, this working tree):
`p1-suite-counts.txt` and `p1-count-reconciliation.txt`.


## 5. Drill

The canonical drill (`tools/backup_recovery_drill.py`, four phases) **completes** in both post-fix runs,
EXIT=0. Against `ct_final02_src` — the exact source of the FINAL-02 §16.5 record — the outcome is
reproduced in detail: phase 1 artifact ≈968 KB, ciphertext-only, envelope v1/AES-256-GCM/key-v1, 154
members, 152 checksums verified, 149 tables; phase 2 `pg_dump` 3,240,188 B → `pg_restore` rc=1 with only
`permission denied for table secrets` (a Supabase-internal object), `missing_tables: []`,
`row_count_mismatches: {}`, every index/constraint/policy/RLS/bucket delta 0; phase 3 96 migrations →
**94 applied, 1 already present, 1 failed = `20260801000000_rc2_constraints.sql`** (the known
data-dependent, immutable-migration case); phase 4 the known harness truncate refusal. That the drill is
*unchanged* by the fix is the point: the fix is drill-neutral, and the drill — which drives the
production `BackupService`, i.e. the code whose lease idiom was repaired — completes without any pool
exhaustion.

## 6. Gate position

**P1's measurable clauses are verified locally. P1 is NOT yet satisfied as a gate.** Reason, precisely:
the gate's first clause is *"the fix is present in the **frozen commit**"*, and this pass was not
authorized to commit (that is gate **P2**), so no frozen commit exists — `00-freeze/` is deliberately
absent. The three verifiable clauses were met: suites green (275/275, EXIT=0), the drill completes, and
a 10-minute soak on a schema-complete database shows no connection growth and no `/health` timeout.

Deliberately **not** claimed here:

- **The B4/D-7 35/35 matrix was not re-run.** FINAL-02 §17's ordered action 1 lists it after the fix;
  this pass did not re-run it, so it stands exactly as §16.3 recorded it.
- **No production and no non-loopback database was contacted.** Every run was `127.0.0.1` and `ct_*`.
- **Independence.** This is the implementer's own evidence; P1's acceptance belongs to the independent
  verifier (CoStrict / OHD), and nothing here asserts their verdict.

## 7. Reproduce

```bash
R=/home/shomonrobie/ct_93d5cdd
EV=$R/docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate

# suites (authoritative)
cd $R/backend && .venv/bin/python -m pytest -q -p no:cacheprovider \
  --junitxml=$EV/junit-backup-suites.xml tests/unit/backup tests/integration/backup

# soak, migration-behind database (default; refuses non-loopback and non-ct_* DBs)
cd $R && backend/.venv/bin/python tools/b7_pool_soak.py --duration 600 --label after-rev2 \
  --out /tmp/b7_soak_after_rev2.json

# soak, schema-complete clone (refused without --allow-backup-tables: the tables exist)
cd $R && backend/.venv/bin/python tools/b7_pool_soak.py --duration 600 --label schema-complete \
  --database-url "$(cat $EV/clone-dsn-used.txt)" --allow-backup-tables --out /tmp/b7_soak_schema.json

# control: the pre-fix idiom, the same detector (exit 0 *because* it detects violations)
cd $R && backend/.venv/bin/python tools/b7_pool_soak.py --legacy-idiom --expect-leak --duration 300 \
  --label control-recheck --out /tmp/b7_control_recheck.json

# canonical drill
cd $R && backend/.venv/bin/python tools/backup_recovery_drill.py --source ct_final02_src \
  --target ct_b7_drill_f02src_1790937500 --keep-target
```



