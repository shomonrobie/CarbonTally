# CarbonTally V3 — Test Database Diagnostic v1.0

**Status:** DIAGNOSTIC COMPLETE — ROOT CAUSE IDENTIFIED
**Date:** 2026-08-11 · Scope: read-only diagnostic of the integration-test
database configuration (`carbontally_test`). No migration, schema, test,
environment, or database changes were made.

---

## 1. Current Test Database Configuration

The backend integration suite obtains its database exclusively from
`backend/tests/integration/conftest.py`:

```python
TEST_DB_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test",
)
```

Key behaviours of that conftest (read, lines 1–77):

- **Default target is hard-coded** to `postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test`
  (the *dedicated integration-test database* on the local Supabase stack).
- The **session-scoped `pool` fixture** connects to that URL and immediately
  executes `TRUNCATE ... RESTART IDENTITY CASCADE` on 15 tables — including
  `emission_factors` — so every assertion is deterministic and no test data
  ever leaks into the authoritative database.
- `os.environ["DATABASE_URL"]` is **forced** (not `setdefault`) to `TEST_DB_URL`
  so a stale shell `DATABASE_URL` can never redirect repository pools at the
  authoritative database.
- The conftest explicitly documents the *authoritative application database*
  as `postgresql://postgres:postgres@127.0.0.1:54326/postgres` and states it
  "must not be truncated by tests".

The same default is used by:

- `src/providers/seai/tests/conftest.py` (line 18–21) — same URL, via
  `INTEGRATION_DATABASE_URL` or the same literal default.
- The V3M-1/V3M-2 integration test
  (`backend/tests/integration/test_v3m1_v3m2_processing_entities.py`) — inherits
  `tests.integration.conftest` (imports `new_id` from it) and therefore the
  session `pool`/truncate fixture.

## 2. Evidence for `carbontally_test`

The dedicated test database has been **referenced and used by prior verified
work**, and is not an invention of the V3M-1/V3M-2 task:

| Source | Evidence |
|---|---|
| `docs/cline/CarbonTally-SEAI-Provider-Implementation-v1.0.md` §8 | "All tests ran against the dedicated isolated database **`carbontally_test`** on the local Supabase stack (`postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test`)." Documents baseline (as found): DEFRA=19, SEAI=0, total=19; after SEAI import: DEFRA=19, SEAI=20, total=39; full acceptance: DEFRA-DESNZ/GB 7,029, SEAI/IE 20, total 7,049. |
| `docs/cline/CarbonTally-Phase9D-Integration-Verification-v1.0.md` §17 | Integration-test command `cd backend && python -m pytest tests/integration` targets `carbontally_test` via `INTEGRATION_DATABASE_URL`; session TRUNCATE isolation mechanism documented. |
| `backend/tests/integration/conftest.py` | Hard-coded default + truncate list (15 tables incl. `emission_factors`). |
| `src/providers/seai/tests/conftest.py` | Same default; cleans only SEAI rows between tests (preserves DEFRA). |
| `backend/_v3m12_probe*.py` (scratch) | Pre-application probes that connect to `.../postgres` (DEV) and `.../carbontally_test` (TEST); `_v3m12_probe3.txt` shows the DEV probe succeeded (`factor_total: 7049`, DEFRA 7,029, SEAI 20) and the TEST probe header printed with no successful result line — consistent with `carbontally_test` not existing at that time. |

**Conclusion:** `carbontally_test` was a real, previously-provisioned database
on the local Supabase stack used by the SEAI provider suite (and targeted by
the backend integration suite). It is the **intended** integration target.
## 3. Existing Test Database Workflow

**There is NO repository mechanism that creates `carbontally_test`.** Search
across the full repository found:

- **No** `CREATE DATABASE carbontally_test`, `createdb ... carbontally_test`,
  or `pg_dump ... | psql carbontally_test` script/command anywhere.
- **No** Makefile/CI/`package.json`/documented step that provisions the test
  database.
- The only "test setup" scripts present are **data-seeding** helpers
  (`backend/tests/setup_test_data.py`, `setup_test_orgs.py`, `verify_setup.py`),
  which populate rows *inside* an already-existing database — they do not
  create the database itself.
- The conftest fixture **connects** to `carbontally_test` but does **not**
  create it (asyncpg `create_pool` fails with `InvalidCatalogNameError` when
  the database is absent — exactly the observed error).

The established pattern in prior sessions was therefore: the developer
provisioned `carbontally_test` **manually** (as a sibling database on the same
local Postgres instance at port 54326, seeded/cloned from the dev database),
then the suites ran against it. This manual step is **not captured anywhere
in the repository** — a reproducibility gap that this diagnostic confirms.

## 4. Supabase Local Database Configuration

- `supabase/config.toml` (read, lines 22–33): `project_id = "carbon_ledger"`,
  `[db] port = 54326`, `shadow_port = 54320`, `major_version = 17`.
- `supabase db reset` is the repository's documented migration workflow
  (prep-pack §1.4 / §0.2; used for the development database). A `db reset`
  replays the full migration chain **into the primary `postgres` database** of
  the local stack.
- `supabase db reset` **does not** create or manage a sibling
  `carbontally_test` database. Sibling databases on the local stack are
  outside the Supabase CLI's migration lifecycle.
- The development database (`postgres`) is confirmed present and healthy: the
  probe artifact `_v3m12_probe3.txt` shows `factor_total: 7049`
  (DEFRA 7,029 · SEAI 20) — the factor baseline is intact.

## 5. Root Cause

**`database "carbontally_test" does not exist` is caused by the test database
no longer existing on the local Supabase Postgres instance (port 54326).**

The chain of facts:

1. The integration conftest **hard-codes** `carbontally_test` as the default
   target and **does not create it** — it only connects to it.
2. `carbontally_test` is a **manually-provisioned sibling database**; it was
   previously present (SEAI suite §8, Phase 9D §17) but is **not** reproduced
   by any repository script.
3. `supabase db reset` (the just-completed reset) replays migrations **only
   into `postgres`** — it neither creates nor restores `carbontally_test`.
4. Therefore, after the stack/reset lifecycle, `carbontally_test` is absent
   and `asyncpg.create_pool(.../carbontally_test)` raises
   `InvalidCatalogNameError: database "carbontally_test" does not exist`.

This is an **environment/test-configuration problem** (as stated in the task),
not a V3M-1/V3M-2 migration defect and not a test-code defect in the V3M tests.


## 6. Recommended Fix

**Create and populate `carbontally_test` as a clone of the (already-reset,
migration-complete) development database `postgres`.** Because `supabase db
reset` has already replayed the full chain (including V3M-1 + V3M-2) into
`postgres`, cloning it yields a test DB with:

- the complete migration chain (init schema → RC1/RC2 → M1–M8 → V3M-1 → V3M-2),
- the factor baseline (DEFRA 7,029 · SEAI 20 · total 7,049),
- no extraneous test data.

Recommended commands (to be executed in a session with a functional shell):

```bash
# Option A — template clone (simplest; requires no active connections to postgres)
createdb -h 127.0.0.1 -p 54326 -U postgres \
  -T postgres carbontally_test

# Option B — dump/restore clone (use if Option A conflicts with active connections)
pg_dump -h 127.0.0.1 -p 54326 -U postgres -d postgres -Fc -f /tmp/carbontally_dev.dump
createdb -h 127.0.0.1 -p 54326 -U postgres carbontally_test
pg_restore -h 127.0.0.1 -p 54326 -U postgres -d carbontally_test /tmp/carbontally_dev.dump
```

Then verify:

```bash
psql "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test" \
  -c "SELECT count(*) FROM public.emission_factors"        # expect 7,049
psql "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test" \
  -c "SELECT to_regclass('public.processing_entities')"    # expect processing_entities
psql "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test" \
  -c "SELECT column_name FROM information_schema.columns WHERE table_name='staff_profiles' AND column_name='entity_id'"
```

And optionally run the SEAI/backend integration suites:

```bash
cd backend && python -m pytest tests/integration/test_v3m1_v3m2_processing_entities.py -q
```

**Secondary observation (flag for the fix session, not resolved here):** the
backend integration conftest's session fixture **truncates `emission_factors`
with CASCADE** at session start, while the V3M test
`test_factor_baseline_unchanged` asserts the 7,049 baseline. When the suite
runs, the truncation removes the factors before the baseline assertion unless
the test DB is re-seeded after truncation (or the baseline test is designed to
run against a preserved snapshot). This tension must be handled during the
fix/verification session (e.g., re-import factors after truncate, or order the
baseline test to run before/independently of the truncate fixture). It does
not cause the current `InvalidCatalogNameError`.

## 7. Whether a Separate Test Database Is Actually Necessary

**YES — a separate test database is required and is the correct architecture.**

Evidence:

1. **The conftest truncates 15 tables with CASCADE at session start**, including
   `emission_factors` (7,049 rows). Running the integration suite against the
   development database (`postgres`) would **destroy the authoritative factor
   baseline** and all development data. The conftest explicitly forbids this
   ("must not be truncated by tests").
2. The SEAI provider suite **cleans SEAI rows** (`clean_seai`) between tests
   while preserving DEFRA rows — a behaviour that is only safe inside a
   disposable test database, not the development database.
3. This is the repository's established, documented convention (SEAI report
   §8, Phase 9D §17) and matches the V3M test file's own docstring ("never the
   authoritative development database").

Alternative (not recommended, documented for completeness): running tests
against `postgres` is **not safe** because of the truncation behaviour and the
factor-baseline invariant. A dedicated, disposable test database is the
correct target. The repository gap is that **no script provisions it** — the
fix should include capturing the provisioning step (see §8).

## 8. Exact Next Command / Action

1. **Recreate the test database** (one of):
   - `createdb -h 127.0.0.1 -p 54326 -U postgres -T postgres carbontally_test`
   - or the dump/restore Option B in §6.
2. **Verify** the test DB has the full schema + factor baseline (SELECTs in §6).
3. **Run the V3M-1/V3M-2 integration test**:
   `cd backend && python -m pytest tests/integration/test_v3m1_v3m2_processing_entities.py -q`
4. **Resolve the truncate-vs-baseline tension** noted in §6 (re-seed
   `emission_factors` after session truncation or adjust ordering) so
   `test_factor_baseline_unchanged` (assert 7,049) passes.
5. **Recommended follow-up (documentation, not this task):** add a small
   repository script or documented command (e.g.
   `database/v3/create_test_db.sql` or a shell helper) that recreates
   `carbontally_test` from `postgres` after every `supabase db reset`, so the
   test-DB provisioning step is reproducible and no longer manual.

---

**Diagnostic limitations (recorded honestly):** this session's development
shell is non-functional (every command, including `echo`/`psql`, fails with
"Command completion could not be observed"), so no live SQL was executed. All
findings are based on read-only file inspection of the repository (conftest,
config, prior verified reports, probe artifacts). The root cause is
nevertheless fully determined: `carbontally_test` is a manually-provisioned
sibling database that the reset did not recreate, and no repository mechanism
exists to reproduce it.
