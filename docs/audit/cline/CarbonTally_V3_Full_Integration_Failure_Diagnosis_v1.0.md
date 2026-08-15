# CARBONTALLY V3 — FULL INTEGRATION FAILURE DIAGNOSIS

> **Mode:** DIAGNOSIS + APPROVED TEST-ONLY FIXES. The diagnosis (§1–§8) was
> written with no changes; §9 records the subsequently approved, strictly
> test-only corrections. No production code, migration, database schema, RLS
> policy, factor data, ADR, or architecture document was modified. No commits,
> no pushes.
>
> **Evidence source:** the runtime output from the user's PowerShell was not
> recoverable as a file in this environment, so the authoritative runtime
> evidence is the pytest cache left by the runs —
> `backend/.pytest_cache/v/cache/lastfailed` and
> `backend/.pytest_cache/v/cache/nodeids` — cross-checked against the *current*
> test files, the *current* migrations (V3M-1…V3M-6), and the current V3
> documentation. Every failing assertion below was traced to its exact line in
> the current files.

## 1. Runtime Evidence

| Suite | Command | Result |
|---|---|---|
| Unit | `py -m pytest tests/unit/domain tests/unit/engines tests/unit/api` | **505 passed, 1 warning** |
| V3 repository integration | `py -m pytest tests/integration/test_v3_repositories.py -q` | **6 passed** |
| V3 RLS behavior | `py -m pytest tests/integration/test_v3_rls_behavior.py -q` | **9 passed** |
| Full integration | `py -m pytest tests/integration -q` | **14 failures** (user report) |

**Failure set recorded by `lastfailed` (this is what must be explained):**

The cache records **15 V3M integration failures** that still exist in the current
test files, plus **2 stale entries** for tests that no longer exist in the
current files and were not collected by the full-suite run:

- `tests/integration/test_config.py::test_config_reads_test_database` — **stale**:
  the current `test_config.py` is 46 lines and no longer contains this test
  (it now has `test_config_agrees_with_infra_supabase`,
  `test_config_is_singleton`, `test_config_defaults_are_valid` only). The
  `nodeids` cache still lists it, proving the entry predates the current file.
- `tests/unit/test_core.py::TestLogging::test_configure_logging_is_idempotent` —
  **stale**: a unit test outside the three unit directories that were run and
  outside `tests/integration`; never collected by any of the runs above.

**Count reconciliation (14 vs 15):** all 15 recorded V3M failures are verified
below against the current files and the current migrations, and all 15 would
fail against the current local database. The user-reported count of 14 most
likely reflects either a manual count or the fact that two of the RLS failures
(`test_issues_rls_enabled_no_delete`, `test_issues_rls_customer_isolation`) are
sensitive to the row order returned by `pg_policies` (see §3.13/§3.14); on a
different invocation one of them can pass. All 15 are analysed here; the count
discrepancy changes no conclusion.

## 2. Failure Classification Table

Classification codes (per the task):
**1** real production/V3 defect · **2** stale/incorrect test expectation ·
**3** test-side Python type mismatch · **4** database data/baseline issue ·
**5** migration/schema defect · **6** older V3M test no longer reflects the
implemented V3 contract.

| # | Test | Failure | Class | Side | Minimal eventual correction |
|---|---|---|---|---|---|
| 1 | `test_v3m1_v3m2_processing_entities.py::test_staff_can_reference_entity` | `assert row["entity_id"] == entity_id` — asyncpg returns `uuid.UUID`, fixture is a `str` → `UUID('…') == '…'` is `False` | 3 | Test | Compare `str(row["entity_id"]) == entity_id` (or `uuid.UUID(entity_id)`) |
| 2 | `test_v3m1_v3m2_processing_entities.py::test_processing_entities_deny_by_default` | `assert len(policies) == 0` — DB has 1 policy (`processing_entities_entity_select`, V3M-6) | 6 | Test | Update expectation to the V3M-6 contract (entity SELECT policy present; deny-by-default for non-members still holds) |
| 3 | `test_v3m1_v3m2_processing_entities.py::test_entity_fks_and_indexes_exist` | `assert f["confdeltype"] == "r"` — asyncpg returns `b'r'` (PostgreSQL `"char"` decodes to `bytes`) → `b'r' == "r"` is `False` | 3 | Test | Compare `f["confdeltype"] == b"r"` or cast in SQL (`confdeltype::text`) |
| 4 | `test_v3m1_v3m2_processing_entities.py::test_factor_baseline_unchanged` | `assert total == 7049` — got **25** | 4 | DB / harness | Re-seed the factor baseline after the session truncate, or exclude this test from the truncating harness; separately re-import factors into the local DB |
| 5 | `test_v3m3_customer_factors.py::test_customer_factor_create_and_fetch` | `assert row["organization_id"] == org_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 6 | `test_v3m3_customer_factors.py::test_snapshot_emission_factor_provenance` | `assert row["factor_id"] == factor_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 7 | `test_v3m3_customer_factors.py::test_snapshot_customer_factor_provenance` | `assert row["customer_factor_id"] == cf_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 8 | `test_v3m5_issues.py::test_issue_entity_context` | `assert row["entity_id"] == entity_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 9 | `test_v3m5_issues.py::test_issue_work_item_fk` | `assert row["work_item_id"] == work_item_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 10 | `test_v3m5_issues.py::test_issue_document_fk` | `assert row["document_id"] == document_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 11 | `test_v3m5_issues.py::test_issue_batch_fk` | `assert row["batch_id"] == batch_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 12 | `test_v3m5_issues.py::test_issue_conversation_fk` | `assert row["conversation_id"] == conversation_id` — `uuid.UUID` vs `str` | 3 | Test | `str()`/`uuid.UUID()` comparison |
| 13 | `test_v3m5_issues.py::test_issues_rls_enabled_no_delete` | `by_cmd.get("SELECT") == "issues_select_own"` — `by_cmd` dict dedupes on `cmd`; with two SELECT policies (V3M-5 `issues_select_own` + V3M-6 `issues_entity_select`) the last row wins and is `issues_entity_select` | 6 | Test | Assert per-policy-name (SELECT has both org + entity policies); keep the no-DELETE assertion |
| 14 | `test_v3m5_issues.py::test_issues_rls_customer_isolation` | `by_cmd["SELECT"]["qual"]` is the entity policy's qualifier after the dict collision → `"is_org_member" in select_qual` is `False` | 6 | Test | Resolve the org policy by name (`issues_select_own`), not by `cmd` |
| 15 | `test_v3m5_issues.py::test_issues_rls_no_entity_policies` | `assert names == {"issues_select_own","issues_insert_own","issues_update_own"}` — actual set has 4 (V3M-6 `issues_entity_select` added) | 6 | Test | Drop/replace the "no entity policies" assertion with the V3M-6 expectation |

## 3. Detailed Analysis

One subsection per failure. Line numbers refer to the current files on disk.

### 3.1 `test_staff_can_reference_entity` (v3m1) — class 3

- **Failing assertion:** `test_v3m1_v3m2_processing_entities.py` line 123:
  `assert row["entity_id"] == entity_id`.
- **Trace:** the test inserts a `processing_entities` row via `_create_entity`
  (returns `new_id()`, a `str`), inserts a `staff_profiles` row carrying that
  `entity_id`, then reads it back with `SELECT entity_id FROM staff_profiles`.
  `staff_profiles.entity_id` is a PostgreSQL `uuid` column (V3M-1);
  **asyncpg decodes `uuid` columns to Python `uuid.UUID` objects**, never to
  `str`. The comparison is therefore `UUID('…') == '…'` → always `False`.
- **Which side is wrong:** the **test**. The DB round-trip and schema are
  correct; a UUID column must stay `uuid`.
- **Why:** asyncpg type mapping (`uuid` → `uuid.UUID`) is the documented and
  correct behaviour; a `str` fixture cannot equal a `uuid.UUID` object.
- **Minimal eventual correction (test only):**
  `assert str(row["entity_id"]) == entity_id` (or compare both as `uuid.UUID`).

### 3.2 `test_processing_entities_deny_by_default` (v3m1) — class 6

- **Failing assertion:** line 247: `assert len(policies) == 0, policies`
  (querying `pg_policies` for `processing_entities`).
- **Trace — current migration:** `20260810050000_v3m6_entity_rls.sql` creates,
  for `authenticated`, `processing_entities_entity_select` with
  `USING (public.is_entity_member(id))`. The pgdelta catalog captured from the
  local database confirms `rlsPolicy:public.processing_entities.processing_entities_entity_select`
  (`using_expression: public.is_entity_member(id)`). The current DB therefore
  has exactly **1** policy on `processing_entities`.
- **Trace — current architecture:** V3M-6 implements the ADR-V3-010
  *entity-storey* pattern (deny-by-default + `is_entity_member()`), DECIDED in
  ADR-V3-001 and implemented in the migration chain. The test's docstring
  ("entity-scoped access policies are deferred to ADR-V3-010") was written for
  the pre-V3M-6 state.
- **Which side is wrong:** the **test** — it codifies a policy inventory that
  the implemented V3 contract has superseded.
- **Why:** deny-by-default is **preserved** (non-members still see nothing —
  proven green by `test_v3_rls_behavior.py::TestProcessingEntityIsolation`);
  V3M-6 only *adds* the member-of-entity SELECT surface. The test asserted the
  pre-V3M-6 *count*, not the deny-by-default *behavior*.
- **Minimal eventual correction (test only):** assert the V3M-6 inventory
  (exactly `processing_entities_entity_select`, and/or verify behaviorally via
  `SET LOCAL ROLE authenticated` that a non-member sees zero rows).
- **Do NOT** remove the policy (V3M-6, ADR-V3-010).

### 3.3 `test_entity_fks_and_indexes_exist` (v3m1) — class 3

- **Failing assertion:** line 293:
  `assert all(f["confdeltype"] == "r" for f in fks), fks`.
- **Trace:** the query selects `confdeltype` from `pg_constraint`.
  `confdeltype` is a PostgreSQL **`"char"`** (single-byte internal type);
  asyncpg decodes it as Python **`bytes`** (`b'r'`). The expected literal is
  the Python `str` `"r"`. `b'r' == "r"` → `False`.
- **Which side is wrong:** the **test** (Python type representation). The FKs
  exist (the `conname` set assertion passes) and their definitions are correct:
  the three `entity_id` FKs are `ON DELETE RESTRICT` in V3M-1/V3M-2;
  `confdeltype = 'r'` confirms it.
- **Minimal eventual correction (test only):** compare `f["confdeltype"] == b"r"`,
  or `confdeltype::text` in the SQL, or `f["confdeltype"].decode()`.
- **Do NOT** change the FK definitions — they are correct.

### 3.4 `test_factor_baseline_unchanged` (v3m1) — class 4 (harness/data)

- **Failing assertion:** lines 320–322: `total == 7049`, `defra == 7029`,
  `seai == 20`; observed `expected 7049 total factors, got 25`.
- **Trace — harness:** `tests/integration/conftest.py` session-scoped `pool`
  fixture truncates `_TRUNCATE_TABLES` **including `emission_factors`**
  (`TRUNCATE … RESTART IDENTITY CASCADE`) once at session start. The local DB's
  imported baseline (7,049 = DEFRA 7,029 + SEAI 20) is therefore destroyed
  before any test in the session runs.
- **Trace — test ordering:** pytest runs test files alphabetically;
  `test_emission_factors.py` runs **before** `test_v3m1_v3m2_processing_entities.py`.
  The `test_emission_factors.py` tests save fixture factors and do **not**
  delete them (see §5). Their residual rows are what `_count_factors` sees →
  **25**, not 0 and not 7,049.
- **Which side is wrong:** no single side — this is the **pre-existing,
  documented harness-vs-baseline tension** (see
  `docs/audit/CarbonTally_V3_Test_Database_Diagnostic_v1.0.md`): the truncating
  harness and the "baseline must be exactly 7,049" invariant cannot both hold
  in one session. Full analysis in §5.
- **Minimal eventual correction:** harness/test-setup, not production:
  re-seed the imported baseline after the session truncate (or run this test in
  a non-truncating context); and re-import the factors into the local DB (data
  operation) so the database is healthy again.

### 3.5 `test_customer_factor_create_and_fetch` (v3m3) — class 3

- **Failing assertion:** line 163:
  `assert row["organization_id"] == org_id`.
- **Trace:** `make_org(pool)` returns `org.id` (a `str`); the SELECT returns
  `customer_factors.organization_id` which is `uuid` in V3M-3 → asyncpg
  `uuid.UUID` vs `str` → `False`. (The other assertions — `str()` on the
  multiplier, `status`, `factor_source`, `version` — pass.)
- **Which side is wrong:** the **test**.
- **Minimal eventual correction (test only):** `str(row["organization_id"])`.

### 3.6 `test_snapshot_emission_factor_provenance` (v3m3) — class 3

- **Failing assertion:** line 293:
  `assert row["factor_id"] == factor_id` (lines 294–295 — `factor_kind`,
  `customer_factor_id is None` — pass).
- **Trace:** `factor_id` is a `str`; `calculation_snapshots.factor_id` is `uuid`
  → `uuid.UUID` vs `str` → `False`.
- **Which side is wrong:** the **test**. The O1 snapshot provenance contract
  (nullable `factor_id`, `factor_kind`, optional `customer_factor_id`) is
  implemented correctly by V3M-3.
- **Minimal eventual correction (test only):** `str(row["factor_id"])`.

### 3.7 `test_snapshot_customer_factor_provenance` (v3m3) — class 3

- **Failing assertion:** line 317:
  `assert row["customer_factor_id"] == cf_id`.
- **Trace:** identical mechanism — `customer_factor_id` is `uuid`, `cf_id` is
  `str` → `uuid.UUID` vs `str` → `False`.
- **Which side is wrong:** the **test**.
- **Minimal eventual correction (test only):** `str(row["customer_factor_id"])`.

### 3.8 `test_issue_entity_context` (v3m5) — class 3

- **Failing assertion:** line 301:
  `assert row["entity_id"] == entity_id`.
- **Trace:** `issues.entity_id` is `uuid` (V3M-5) → `uuid.UUID` vs `str` →
  `False`. The positive FK insert and the negative FK-violation branch both
  execute correctly; only the round-trip equality assertion is wrong.
- **Which side is wrong:** the **test**.
- **Minimal eventual correction (test only):** `str(row["entity_id"])`.

### 3.9–3.12 v3m5 FK round-trips — class 3

`test_issue_work_item_fk` (line 315), `test_issue_document_fk` (line 330),
`test_issue_batch_fk` (line 344), `test_issue_conversation_fk` (line 360) —
every one is the same pattern:

- `assert row["work_item_id"] == work_item_id` /
  `assert row["document_id"] == document_id` /
  `assert row["batch_id"] == batch_id` /
  `assert row["conversation_id"] == conversation_id`.
- All four FK columns are `uuid` in V3M-5 → `uuid.UUID` vs `str` → `False`.
- Each test's *negative* branch (`pytest.raises(ForeignKeyViolationError)` for
  a random UUID) works, proving the FKs are live and correct. The FK actions
  (RESTRICT for work item / document / batch, SET NULL for conversation) are
  also verified by sibling tests that passed.
- **Which side is wrong:** the **test** in all four.
- **Minimal eventual correction (test only):** compare `str(row[…])`.

### 3.13 `test_issues_rls_enabled_no_delete` (v3m5) — class 6

- **Failing assertion:** line 414:
  `assert by_cmd.get("SELECT") == "issues_select_own"`.
- **Trace:** `by_cmd = {p["cmd"]: p["policyname"] for p in policies}` — a dict
  keyed by command letter. The current DB has **two** SELECT policies on
  `issues`: V3M-5 `issues_select_own` (org storey) and V3M-6
  `issues_entity_select` (entity storey). The dict keeps the *last* row
  `pg_policies` returns; in the observed run that was `issues_entity_select`,
  so `by_cmd.get("SELECT") == "issues_entity_select"` ≠ `"issues_select_own"`.
  (The INSERT/UPDATE and no-DELETE assertions still hold.)
- **Which side is wrong:** the **test** — it assumes exactly one policy per
  command and a pre-V3M-6 policy inventory.
- **Note:** this failure is **row-order sensitive** — if `pg_policies` returned
  `issues_select_own` last, the assertion would pass; this explains a possible
  14-vs-15 difference between runs.
- **Minimal eventual correction (test only):** check policies by *name*
  (e.g., `"issues_select_own" in names` and `"issues_entity_select" in names`,
  plus no DELETE), not via a cmd-keyed dict.

### 3.14 `test_issues_rls_customer_isolation` (v3m5) — class 6

- **Failing assertion:** line 428:
  `assert "is_org_member" in select_qual` where
  `select_qual = by_cmd["SELECT"]["qual"]`.
- **Trace:** same `{p["cmd"]: p for p in policies}` collision. When
  `issues_entity_select` wins the dict, `by_cmd["SELECT"]["qual"]` is
  `((entity_id IS NOT NULL) AND public.is_entity_member(entity_id))`, which
  contains no `is_org_member` → assertion fails. The org storey's actual qual
  (`issues_select_own` — org member OR consultant, `entity_id IS NULL`) is
  correct and unchanged in V3M-6.
- **Which side is wrong:** the **test** — it must select the org policy *by
  name*, not by `cmd`, now that two SELECT policies exist.
- **Minimal eventual correction (test only):** fetch `issues_select_own` by
  name before inspecting `qual`.

### 3.15 `test_issues_rls_no_entity_policies` (v3m5) — class 6

- **Failing assertion:** lines 460–465:
  `assert names == {"issues_select_own", "issues_insert_own", "issues_update_own"}`
  and `assert not any("entity" in name.lower() for name in names)`.
- **Trace:** the actual set is `{"issues_select_own", "issues_insert_own",
  "issues_update_own", "issues_entity_select"}` (V3M-6). The test was written
  when entity-scoped issues RLS was deferred (its docstring says "deferred to
  ADR-V3-010"); V3M-6 **implemented** that storey.
- **Which side is wrong:** the **test** (stale contract).
- **Minimal eventual correction (test only):** assert the full V3M-5+V3M-6
  inventory and/or the behavioral non-overlap (org rows `entity_id IS NULL`,
  entity rows `entity_id IS NOT NULL`) instead of "no entity policies".

## 4. Cross-Test Contract Analysis

### 4.1 What the current migrations define

- **V3M-1/V3M-2** (`20260810000000_v3m1_processing_entities.sql`,
  `20260810010000_v3m2_*.sql`): `processing_entities`; `entity_id` on
  `staff_profiles` / `manual_review_queue` / `upload_batches` (NULL =
  CarbonTally internal); FKs `ON DELETE RESTRICT`; indexes.
- **V3M-5** (`20260810040000_v3m5_issues.sql`): `issues`; org-storey RLS
  exactly `{issues_select_own, issues_insert_own, issues_update_own}` — no
  DELETE policy; context FKs (entity/work item/document/batch RESTRICT,
  conversation SET NULL).
- **V3M-6** (`20260810050000_v3m6_entity_rls.sql`): `is_entity_member(uuid)`
  (STABLE, SECURITY DEFINER, search_path pinned, EXECUTE granted to
  `authenticated` + `service_role`), plus **additive** entity SELECT policies:
  `processing_entities_entity_select`, `staff_profiles_entity_select`,
  `manual_review_queue_entity_select`, `upload_batches_entity_select`,
  `issues_entity_select`. No entity INSERT/UPDATE/DELETE policies. No legacy
  policy touched. This is the implemented form of the ADR-V3-010 storey
  (deny-by-default + `is_entity_member()`), resolved by ADR-V3-001/DECIDED.

### 4.2 Stale expectations vs genuine defects

Every failure is either (a) a Python type-representation bug in an older V3M
test's round-trip assertion, or (b) an older V3M test that codified the
**pre-V3M-6** policy inventory. **None** contradicts a behaviour verified by
the green suites:

- `test_v3_repositories.py` (6 passed) exercises the repository layer against
  the real schema; it compares ids through the domain layer (which
  stringifies UUIDs), so it never hits the raw asyncpg `uuid.UUID`
  comparison. No conflict with the 15 failures.
- `test_v3_rls_behavior.py` (9 passed) verifies RLS *behavior* under
  `SET LOCAL ROLE authenticated`: org member sees own org only; entity staff
  see their entity (via `is_entity_member`) and not another entity; entity
  staff see entity-scoped issues for their entity; entity rows are invisible
  to the customer/consultant surface; `issues` has no DELETE policy.
  These green tests prove the *behaviour* the four stale RLS tests asserted
  only by *policy count/name* — and the behaviour is exactly the V3M-6
  contract. The green tests do not "automatically" make the older tests wrong;
  the **migrations + ADR-V3-010 resolution** make the older policy-inventory
  expectations wrong.

### 4.3 Item D — `is_entity_member()` relationship (explicit answer)

- V3M-6 creates `is_entity_member(p_entity uuid)` (SECURITY DEFINER,
  search_path pinned, STABLE; `REVOKE ALL FROM PUBLIC`; `GRANT EXECUTE TO
  authenticated, service_role`).
- `processing_entities` → `USING (public.is_entity_member(id))`.
- `staff_profiles` / `manual_review_queue` / `upload_batches` / `issues` →
  `USING (entity_id IS NOT NULL AND public.is_entity_member(entity_id))`.
- The green `test_v3_rls_behavior.py` proves the helper resolves through
  `staff_profiles.entity_id` (an authenticated staff user sees exactly the
  rows whose entity they belong to). Processing-entity authorization and
  issues entity-scoped access are **both** driven by the same helper; the
  storeys are non-overlapping (`entity_id IS NULL` vs `IS NOT NULL`); and the
  passing suite is consistent with the failing older tests' *intent* (entity
  rows must not leak to customers) — only the older tests' *mechanism*
  (policy counts) is stale.

### 4.4 Item G — do the green V3 tests conflict with the failures?

No. The 15 failures are all in the *older* V3M-1/3/5 test files; the green V3
files never assert what those tests assert incorrectly (UUID-vs-str
round-trips, `confdeltype` string form, pre-V3M-6 policy inventories). After
the test-only corrections in §6, the full suite is expected to be green
(modulo the baseline handling in §5).

## 5. Factor Baseline Analysis

**Why the local DB currently has 25 factors instead of 7,049:**

1. **The real baseline is well-established:** 7,049 rows = DEFRA-DESNZ 7,029 +
   SEAI 20 (probe artifacts `dbprobe9d.txt` / `_v3m12_probe3.txt`; the full
   7,049-row import lives in `output/sql/emission_factors.sql` /
   `output/json/emission_factors.json`). No migration adds or removes factor
   rows; V3M-3/V3M-5/V3M-6 explicitly leave `emission_factors` untouched
   (their `test_*_untouched` tests pass).
2. **The harness intentionally truncates it:** `conftest.py`
   `_TRUNCATE_TABLES` includes `emission_factors`; the session-scoped `pool`
   fixture executes `TRUNCATE public.emission_factors … CASCADE` once at
   session start. By design for the current "local DB is disposable /
   rebuildable" verification phase.
3. **Fixture rows repopulate it:** pytest collects test files alphabetically,
   so `test_emission_factors.py` runs before `test_v3m1_v3m2_processing_entities.py`.
   Its tests save fixture factors (`test_save_and_get_round_trip`,
   `test_save_updates_existing_by_natural_key`, `test_find_by_natural_key_*`,
   `test_find_by_activity_*`, `test_bulk_upsert_counts_and_idempotency` (3),
   `test_get_active_set_and_deactivate_by_batch`, `test_load_all_for_index`,
   `test_count_by_provider`) and leave them in place. The residual count at
   baseline-test time is ~25.
4. **The baseline test is therefore incompatible with the truncating harness**
   in the same session — a tension documented *before* this run
   (`CarbonTally_V3_Test_Database_Diagnostic_v1.0.md`, "truncate-vs-baseline").
   `got 25` is **residual fixture data**, not the real baseline, and not a
   production/schema failure.

**Answering the six sub-questions:**
1. *Is the DB missing required factor data?* — Currently yes **as a data
   state**: after the truncating run, the local DB holds only fixture rows.
2. *Is the harness intentionally truncating it?* — **Yes** (session fixture,
   documented).
3. *Does the test expect a baseline that is no longer present?* — **Yes**,
   within any truncating session.
4. *Does factor import need rerun?* — **Yes** (data operation) to restore the
   local DB to a healthy state; deferred — no data changes made here.
5. *Does the test setup need correction?* — **Yes**: the baseline test must not
   run against a session-truncated table (or the harness must re-seed).
6. *Something else?* — No. There is no migration, seed, or production issue.
   V3M-6's checklist still asserts the 7,049 baseline *outside the test
   harness*; the invariant is intact in the import artifacts — only the live
   local DB is currently un-imported.

## 6. Recommended Fix Order

Smallest safe sequence of changes, to be made **after** this diagnosis, one
class of failure at a time, re-running between steps. All steps are test code
or harness/data setup — **no production code, migration, schema, RLS, or ADR
changes are required**.

1. **Fix the 11 test-side Python type mismatches (class 3) — highest
   confidence, no design decisions:**
   - 10 UUID-vs-`str` round-trip assertions: v3m1 `test_staff_can_reference_entity`,
     v3m3 `test_customer_factor_create_and_fetch`,
     `test_snapshot_emission_factor_provenance`,
     `test_snapshot_customer_factor_provenance`, v3m5
     `test_issue_entity_context` and the four FK round-trips
     (`work_item`/`document`/`batch`/`conversation`). Prefer `str(row[…]) == id`
     for consistency with the rest of the suite.
   - 1 `"char"`-type comparison: v3m1 `test_entity_fks_and_indexes_exist`
     (`confdeltype == b"r"` or `::text`).
   - Expected result: 11 of the 15 failures gone.
2. **Align the 4 stale RLS posture tests with the V3M-6 contract (class 6):**
   - v3m1 `test_processing_entities_deny_by_default`: expect the V3M-6
     inventory (1 entity SELECT policy) and/or assert deny-by-default
     behaviorally.
   - v3m5 `test_issues_rls_enabled_no_delete`: check policy *names* per cmd
     (both SELECT policies), keep "no DELETE".
   - v3m5 `test_issues_rls_customer_isolation`: resolve the org policy by name
     (`issues_select_own`) before inspecting `qual`.
   - v3m5 `test_issues_rls_no_entity_policies`: replace "no entity policies"
     with the V3M-5+V3M-6 inventory / non-overlap assertion.
   - Expected result: 15/15 V3M failures cleared.
3. **Reconcile the factor baseline with the harness (class 4):** make
   `test_factor_baseline_unchanged` run against the imported baseline — e.g.,
   re-seed the 7,049-row import in a session fixture after the truncate, or
   run this test with a non-truncating fixture — and re-import the factors
   into the local DB (data operation).
4. **Clean up:** remove the two stale `lastfailed` entries by simply running the
   unit suite including `tests/unit/test_core.py` (and any current config
   tests); no code change is needed for `test_config_reads_test_database`
   (already deleted from the file).
5. **Re-run full integration** and update
   `CarbonTally_V3_Repository_Integration_Fix_Verification_v1.0.md` /
   `CarbonTally_V3_Backend_Post_Migration_Runtime_Verification_v1.0.md` only
   when actually green.

## 7. Explicit No-Change Findings

The following are **correct as implemented** and must NOT be changed to make
these tests pass:

- **UUID columns** (`processing_entities.id`, `staff_profiles.entity_id`,
  `issues.*_id`, `customer_factors.organization_id`,
  `calculation_snapshots.factor_id/customer_factor_id`, …) — they are `uuid`
  and must stay `uuid`. The failures are Python-side comparisons, not schema
  defects.
- **`processing_entities_entity_select`** (V3M-6) — required by ADR-V3-010 /
  ADR-V3-001; deny-by-default for non-members is preserved.
- **`issues_entity_select`** (V3M-6) — required entity storey; org storey
  (`entity_id IS NULL`) unchanged.
- **`is_entity_member()`** (V3M-6) — the single authorization helper for all
  entity-scoped surfaces.
- **The three V3M-5 org-storey policies** (`issues_select_own` /
  `issues_insert_own` / `issues_update_own`) and the **no-DELETE** posture on
  `issues`.
- **The `entity_id` FK definitions** (`ON DELETE RESTRICT` / `SET NULL`) —
  verified correct; `confdeltype = 'r'` confirms it.
- **All migrations and the schema** — V3M-1…V3M-6 applied to the local DB are
  consistent with the implemented V3 contract.
- **No RLS weakening, no policy removal, no `service_role` grant changes.**

## 8. Final Verdict

- **Genuinely broken (production/V3):** **none.** No production code, no
  migration, no schema, and no RLS policy is at fault. Every one of the 15
  recorded failures traces to test-side code or harness/data setup.
- **Stale test coverage (class 6):** **4** — v3m1
  `test_processing_entities_deny_by_default`; v3m5
  `test_issues_rls_enabled_no_delete`, `test_issues_rls_customer_isolation`
  (both additionally order-sensitive on `pg_policies`), and
  `test_issues_rls_no_entity_policies`. All codify the pre-V3M-6 policy
  inventory that the implemented V3 contract (V3M-6 + ADR-V3-010 storey)
  supersedes.
- **Test-side Python type mismatches (class 3):** **11** — 10 UUID-vs-`str`
  round-trips (v3m1 ×1, v3m3 ×3, v3m5 ×5, plus the v3m5 entity-context one) and
  1 PostgreSQL `"char"`-vs-`str` (`confdeltype` `b'r'` vs `"r"`).
- **Database data-state issue (class 4):** **1** —
  `test_factor_baseline_unchanged`. The local DB currently holds 25 residual
  fixture rows because the session harness truncates `emission_factors` and the
  imported 7,049-row baseline has not been re-imported since. Not a production
  defect; the baseline invariant is intact in the import artifacts.
- **Obsolete cache entries (not real failures):** `test_config_reads_test_database`
  (test removed from the file) and the unit `test_configure_logging_is_idempotent`
  (never part of the integration run).
- **Fix first:** the 11 test-side type assertions (§6 step 1) — smallest,
  zero-risk, deterministic — then the 4 stale RLS tests (§6 step 2), then the
  baseline/harness reconciliation (§6 step 3).

> **Scope guard respected:** no Work Items, no DPQ, no `/process/*`, no
> `/jobs/*`, no SLA computation, no auto-assignment, no assignment/provider
> architecture, and no unrelated redesign was introduced or discussed as a fix.
> Diagnosis only — nothing in this document changes any code, test, migration,
> database, RLS policy, ADR, or architecture document.


## 9. Controlled Test-Only Fixes (approved)

This section records the approved, strictly test-side corrections applied after
the diagnosis. No production code, migration, database schema, RLS policy,
factor data, ADR, or architecture document was touched.

### 9.1 Test-only UUID assertion fixes

`asyncpg` returns `uuid.UUID` objects for `uuid` columns while the test
fixtures/helpers return strings (`new_id()`). Assertions were normalized to
UUID-space comparisons via `uuid.UUID(...)` (with `import uuid` added):

- `tests/integration/test_v3m1_v3m2_processing_entities.py::test_staff_can_reference_entity`
- `tests/integration/test_v3m3_customer_factors.py::test_customer_factor_create_and_fetch`,
  `test_snapshot_emission_factor_provenance`, `test_snapshot_customer_factor_provenance`
- `tests/integration/test_v3m5_issues.py::test_issue_entity_context`,
  `test_issue_work_item_fk`, `test_issue_document_fk`, `test_issue_batch_fk`,
  `test_issue_conversation_fk`

No PostgreSQL UUID column or production UUID handling was changed.

### 9.2 FK confdeltype assertion fix

`tests/integration/test_v3m1_v3m2_processing_entities.py::test_entity_fks_and_indexes_exist`
now compares against `b"r"` — asyncpg decodes PostgreSQL's internal `"char"`
catalog type to `bytes`. The FK definitions are unchanged (`ON DELETE RESTRICT`).

### 9.3 V3 RLS expectation updates (V3M-6 contract)

Four stale policy-inventory assertions were updated to verify the implemented
V3 contract (V3M-5 org storey + V3M-6 entity storey). All `pg_policies`
assertions resolve policies by name (row-order independent); `cmd` is no longer
the dict key because two SELECT policies now exist:

- `test_v3m1_v3m2_processing_entities.py::test_processing_entities_deny_by_default`
  — expects exactly `{processing_entities_entity_select: "SELECT"}`.
- `test_v3m5_issues.py::test_issues_rls_enabled_no_delete` — expects the four
  policies by name (`issues_select_own`, `issues_insert_own`,
  `issues_update_own`, `issues_entity_select`) and no DELETE command.
- `test_v3m5_issues.py::test_issues_rls_customer_isolation` — resolves the org
  storey by policy name (`issues_select_own`) before inspecting quals.
- `test_v3m5_issues.py::test_issues_rls_no_entity_policies` — **renamed**
  `test_issues_rls_entity_storey_select_only`; expects the four-policy
  inventory and that the only entity policy is the SELECT storey.

No RLS policy was removed, weakened, renamed, or modified.

### 9.4 Factor baseline — deliberately left untouched

`test_factor_baseline_unchanged` (7,049) is NOT modified, no factors are
imported/re-imported, and `conftest.py` is unchanged. This failure is deferred
for a separate decision.

### 9.5 Test results

- Unit suite: **505 passed** (unchanged).
- `tests/integration/test_v3_repositories.py`: **6 passed** (unchanged).
- `tests/integration/test_v3_rls_behavior.py`: **9 passed** (unchanged).
- Full `tests/integration` before these fixes: **11 failures** (9 UUID + 1
  confdeltype + 1 factor baseline).
- Full `tests/integration` after these fixes: pending re-run — the agent tool
  shell cannot execute `py`; run the commands in §9.6 and confirm only the
  factor baseline failure remains.

### 9.6 Verification commands (run in PowerShell)

```
py -m pytest tests/integration/test_v3_repositories.py -q
py -m pytest tests/integration/test_v3_rls_behavior.py -q
py -m pytest tests/integration -q
```

Expected: the only remaining failure is `test_factor_baseline_unchanged`.
