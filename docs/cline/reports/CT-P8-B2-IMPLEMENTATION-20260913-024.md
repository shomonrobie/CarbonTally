# CT-P8-B2-IMPLEMENTATION-20260913-024

**Phase 8 — B2 Evidence / Line-Item Addressability — IMPLEMENTATION REPORT**

---

## A. Task identity

| Item | Value |
|---|---|
| Task ID | `CT-P8-B2-IMPLEMENTATION-20260913-024` |
| Date / time | 2026-09-13 (local workstation; run logs carry UTC timestamps) |
| Classification | **IMPLEMENTATION-ONLY** (no independent-verification authority) |
| Authoritative contract | `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` |
| Contract correction | `docs/cline/reports/CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021.md` (§20.3 corrected enumeration) |
| PO ratification (B2-D1…B2-D12) | `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` |
| Authorisation gate | `docs/cline/reports/CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019.md` — **COMPLETE — B2 IMPLEMENTATION MAY PROCEED** |
| Current-state recovery | `docs/cline/reports/CT-P8-CURRENT-STATE-RECOVERY-20260913-023.md` |
| Repository | `/home/shomonrobie/carbon_tally` (shared worktree; a parallel session is active — nothing outside B2's file list was touched) |

No contract conflict, unresolved decision or hard-stop condition was encountered
during implementation.

---

## B. Pre-implementation state (recorded before any change)

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Staged | 0 files |
| Tracked modifications | 208 (pre-existing, untouched) |
| Untracked | 76 entries (798 with `--untracked-files=all`) |
| Migrations on disk | 57 (now 59 — the two B2 files) |
| B1 migrations present | `20260914000000_p8_b1_disclosure_model_foundation.sql`, `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` (untracked; unapplied to dev/test) |
| `evidence_line_items` | did not exist in any environment |
| B2 migration files | did not exist (created by this task) |

No pre-existing worktree change was staged, committed, reverted, cleaned or
otherwise disturbed.

### B.1 Post-implementation worktree note (parallel session)

During this task a **parallel session** in the same shared worktree committed its
own, unrelated work: HEAD moved `19e4f01c…` → `37b19d13…`
(`feat(admin): admin-configurable Google Analytics 4 (Analytics & Integrations)`).
Verified after implementation:

* that commit contains **no** B2 file (`git show --stat HEAD | grep -iE 'b2|evidence_line_items|backfill_evidence'` → empty);
* **every** B2 artefact created/modified by this task is still untracked or
  unstaged (`staged = 0`), i.e. nothing of this task was captured by that commit;
* the B1 migration files' hashes are unchanged
  (`20260914000000…` `fd3a18a038bfe11b7fb098a3f52f09ed`,
  `20260915000000…` `0cdb37a8583c2b21799c68f00484012b`);
* no secret material was introduced into any file this task created or edited
  (pattern scan for keys/tokens/passwords → clean).

---

## C. Implemented changes

### C.1 Database (2 migrations, additive only)

| Path | Purpose | Contract |
|---|---|---|
| `supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql` | B2-1: create `public.evidence_line_items` (exact §7.1 DDL), the 4 inline constraints, 2 explicit indexes, RLS + privilege posture, 2 SELECT-only policies, table/column comments, B1-helper precondition check, one `BEGIN;…COMMIT;` | §7, §16, §18.1 |
| `supabase/migrations/20260916010000_p8_b2_provenance_line_links.sql` | B2-2: `calculation_snapshots.source_line_item_id` + `disclosure_value_evidence.source_line_item_id`, 2 guarded FKs (`ON DELETE SET NULL`), 2 indexes, comments; additive on existing tables only | §8.1, §9.1, §16.2, §18.1 |

B1 migration files were **not** modified (§18.3); both B1 migration-text guards
still hold (asserted by the new static test).

### C.2 Application code

| Path | Change | Contract |
|---|---|---|
| `backend/domain/line_items.py` (**new**) | Pure materialisation domain logic: recognised-key vocabulary, canonical payload/`payload_hash` (number normalisation incl. `100`/`100.0`/`100.00`), eligibility + ordinal rules, per-line optional interface (`page`/`line_reference`/`extraction_method`), ordinal decisions (`INSERT`/`SKIP_EXISTS`/`DIVERGENCE`), audit-action constants | §11.1–§11.3, §11.7, §17, §22.1(3) |
| `backend/data/evidence_line_items.py` (**new**) | Insert-only materialisation (`materialise_for_item`), Class-1 `backfill` (dry-run, batched, keyset-paginated, run report, divergence detection), reads (`list_for_item`, `get`, `get_by_ordinals`, `count_for_item`), best-effort audit, no UPDATE/DELETE path | §11.3, §11.4, §12.1–§12.3, §17, §22.1(4) |
| `backend/data/manual_extraction.py` | Forward hook `_materialise_evidence_lines` (best-effort, never raises) after a successful `save_extracted_data` (always) and `update_item(extracted_data=…)`; additive `extraction_method` keyword on both | §12.1, B2-D6 |
| `backend/domain/calculation.py` | `CalculationSnapshot.source_line_item_id`; `_canonical()` appends the line **only when set** (existing hashes byte-identical) | §8.1, §8.4 |
| `backend/engines/calculation.py` | `CalculationRequest.source_line_item_id`; `_build_snapshot` carries it | §13.1 |
| `backend/data/emissions_logs.py` | Snapshot INSERT and `_SNAPSHOT_COLUMNS` include the new column | §8.1, §13.1 |
| `backend/services/automatic_processing.py` | `_calculate_line` resolves `(source_item_id, idx+1)` → line id (guarded, best-effort) and passes it; the extraction sync passes its real `method_stamp` | §13.1, §13.2, §12.1 |
| `backend/api/v3_operations.py` | `_run_line_calculation` resolves all ordinals in one lookup (guarded) and passes the line id; the two human `save_extracted_data` sites pass `"manual"` | §13.1, §13.2, §12.1 |
| `backend/data/disclosure.py` | `link_value_evidence(..., source_line_item_id=None)`; written in the snapshot-branch upsert and the NULL-snapshot update/insert; when omitted but a snapshot is given it is taken **from the snapshot**; the branch's `$2..$7` parameter positions were deliberately preserved so no existing B1 expectation changes | §9.1–§9.3 |
| `backend/api/dependencies.py` | `RepositoryBundle.evidence_line_items` (additive field + construction) | §12.2, §13.2 |
| `backend/tools/backfill_evidence_line_items.py` (**new**) | Operational CLI: dry-run default, `--apply`, `--batch-size`, `--limit`, `--json`; non-zero exit on run errors | §11.4, §22.1(6) |
| `backend/tools/b2_clone_schema_harness.py` (**new**) | Disposable privileges-inclusive clone harness: `pg_dump --schema-only` (ACLs included) → B1 → B2 → re-apply; asserts the declared delta and nothing else, table/policy/RLS/row parity and idempotency | §18.5, §20.3, §22.1(10) |


### C.3 Tests

| Path | Change | Contract |
|---|---|---|
| `backend/tests/unit/data/test_b2_migration.py` (**new**, 14 tests) | Static: single transaction, exactly one new table, exact column shape, constraints (incl. `RESTRICT`, open `extraction_method`), 4 explicit indexes vs the constraint-backed identity index, 2 SELECT-only policies, privilege posture, B1-absent precondition, no trigger/retention artefact, no destructive statement, B2-2 additive-only, B1 files untouched | §20.1 |
| `backend/tests/unit/domain/test_evidence_line_items.py` (**new**, 18 tests) | Pure: eligibility, recognised keys, `raw_*`, canonical hash (key order, `100`/`100.0`/`100.00`), non-scalars, ordinal gaps, duplicate lines, per-line interface, decisions, module cannot re-extract | §20.1 |
| `backend/tests/integration/test_evidence_line_items_b2_runtime.py` (**new**, 21 tests) | Runtime acceptance: §20.2 tests 1–17, 19, 20 + the presence checks moved from B1's boundary test; skips when B2 is unprovisioned | §20.1, §20.2 |
| `backend/tests/integration/test_disclosure_b1_runtime.py` | **Amended** `test_b2_b3_b4_boundary_untouched` (split; B3/B4 guards unchanged; B2-absence assertions replaced by a B1-namespace check; B2 presence moved to the B2 suite) | §20.6, §27.2 |
| `backend/tests/unit/data/test_disclosure_sql_typing.py` | **Amended** `test_no_b2_b3_b4_objects_in_the_repository` (B3/B4 guards unchanged; B2 narrowed to the sanctioned link statements; no `evidence_line_items` DDL/DML) | §20.6, §27.2 |
| `backend/tests/unit/api/fakes.py` | Test-fake alignment with the contract's additive signatures: `MemoryManualExtraction.save_extracted_data(..., extraction_method=None)`, `RepositoryBundle.evidence_line_items`, `_EvidenceLinesStub` | §12.1 (test infrastructure only) |

`backend/tests/unit/data/test_disclosure_migration.py` (`test_no_b2_b3_b4_tables`,
`test_no_source_line_item_id_column`) is **unchanged and still passing** — the B1
migration file is byte-identical.

### C.4 Amendment before/after (§20.6(3))

**`test_disclosure_b1_runtime.py::test_b2_b3_b4_boundary_untouched`**

*Before* — documented B2's **absence** (plus the B3/B4 guard):

```python
assert not await pool.fetchval(
    "SELECT to_regclass('public.evidence_line_items') IS NOT NULL"
)
assert not await pool.fetchval(
    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
    "WHERE table_name = 'calculation_snapshots' "
    "AND column_name = 'source_line_item_id')"
)
assert not await pool.fetchval(   # B3/B4 guard — unchanged
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
    "WHERE table_schema = 'public' AND (table_name LIKE '%intensity%' "
    "OR table_name LIKE '%narrative%' OR table_name LIKE '%commentary%'))"
)
```

*After* — keeps the 11-table namespace assertion and the B3/B4 guard verbatim,
replaces the two B2-absence assertions with a B1-namespace check (“no
``line_number`` column in any ``disclosure_*`` table”), and **moves** the B2
presence assertions into `test_evidence_line_items_b2_runtime.py::test_00_…`.

**`test_disclosure_sql_typing.py::test_no_b2_b3_b4_objects_in_the_repository`**

*Before*: `assert "evidence_line_items" not in SQL_BLOCKS` **and**
`assert "source_line_item_id" not in SQL_BLOCKS` (plus the three B3/B4 guards).

*After*: the three B3/B4 guards are unchanged; `evidence_line_items` must still
never appear in the B1 repository's SQL; and `source_line_item_id` is allowed
**only** in the sanctioned link statements — every triple-quoted SQL block
containing it must be the `disclosure_value_evidence` link/upsert statement or
the snapshot-derived read. Every B3/B4 guard and the scope of the assertion are
preserved (narrowed, never weakened).

### C.5 Deliberate non-amendment

The B1 SQL-typing test also pins the NULL-snapshot branch's parameter positions
(`$5::uuid`/`$6::uuid`/`$7::uuid`). Rather than amend it, the new column was
appended as **`$8::uuid`** in that branch, so no B1 expectation changes. Only the
two artefacts the contract names in §20.6 were amended.


---

## D. Database changes

### D.1 Migration files

1. `supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql`
2. `supabase/migrations/20260916010000_p8_b2_provenance_line_links.sql`

Both are single-transaction (`BEGIN;…COMMIT;`), additive and re-appliable
(verified: apply `rc=0`, re-apply `rc=0`, zero schema diff).

### D.2 Objects created (provisioned-clone introspection, `carbontally_b2_harness`)

| Kind | Object |
|---|---|
| New table (1) | `public.evidence_line_items` (14 columns: `id`, `organization_id`, `source_item_id`, `source_file_id`, `line_number`, `source_page`, `row_reference`, `raw_description`, `raw_quantity`, `raw_unit`, `payload_hash`, `extraction_method`, `materialisation_kind`, `created_at`) |
| New columns on existing tables (2) | `calculation_snapshots.source_line_item_id` (nullable uuid), `disclosure_value_evidence.source_line_item_id` (nullable uuid) |
| FK constraints (5) | `evidence_line_items.organization_id → organizations` (**CASCADE**), `evidence_line_items.source_item_id → manual_extraction_items` (**RESTRICT** — B2-D1), `evidence_line_items.source_file_id → organization_files` (SET NULL), `calculation_snapshots_source_line_item_id_fkey` (**SET NULL**), `disclosure_value_evidence_source_line_item_id_fkey` (**SET NULL**) |
| Unique / identity | `evidence_line_items_identity_unique UNIQUE (source_item_id, line_number)` (constraint-backed — counted separately from the explicit indexes) |
| CHECKs (3) | `line_number >= 1`; `source_page IS NULL OR source_page >= 1`; `materialisation_kind IN ('FORWARD','BACKFILL')` (no CHECK on `extraction_method` — B2-D7) |
| Explicit indexes (4) | `idx_eli_org`, `idx_eli_source_file`, `idx_calculation_snapshots_source_line_item`, `idx_dve_source_line_item` |
| Policies (2) | `evidence_line_items_org_select` (**SELECT**, `to authenticated`, `p8_disclosure_is_org_member(organization_id)`); `evidence_line_items_entity_select` (**SELECT**, `to authenticated`, `work_item_effective_entity(source_item_id) IS NOT NULL AND is_entity_member(work_item_effective_entity(source_item_id))` — an exact mirror of `manual_extraction_items_entity_select`, B2-D3) |
| Triggers (0) | none — B2-D11 |
| Grants | `anon`: none; `authenticated`: `SELECT` only (TRUNCATE/TRIGGER/REFERENCES/MAINTAIN revoked); `service_role`: ALL |

### D.3 Delete semantics

* `evidence_line_items.source_item_id` → **`ON DELETE RESTRICT`**: deleting an
  extraction item that still has lines fails with a foreign-key violation and the
  lines remain intact (runtime test 19).
* The two consumer links and `source_file_id` → **`ON DELETE SET NULL**: a
  downstream record never loses its row.
* No cascade path to evidence lines exists anywhere; there is no soft-delete
  column, no retention/archival artefact (B2-D11).

### D.4 RLS / policy changes

Only the two **new** SELECT policies on the new table. No existing table's
grant, policy or RLS flag changed — independently proven by the harness
(table-scoped grant / policy / `relrowsecurity` parity across all 116
pre-existing tables).


---

## E. Materialisation

**Class-1 materialisation** (`backend/data/evidence_line_items.py` +
`backend/domain/line_items.py`):

* eligibility is a pure function of the persisted JSONB (§11.1):
  `extracted_data.line_items[]` must be an array; an empty array yields 0 rows and
  never falls back to the flat record; a flat record is ineligible and is never
  fabricated into a line;
* recognised keys only (`activity`, `description`, `item`, `quantity`, `unit`,
  `amount`, `currency`, `supplier`, `date`, `invoice_number`) with
  `raw_description`/`raw_quantity`/`raw_unit` derived as specified; ordinals are
  1-based and gaps are permanent;
* `payload_hash = sha256(canonical_json(recognised payload))` with number
  normalisation (`100`/`100.0`/`100.00` hash identically), so int/float drift
  cannot create a false divergence;
* the documented per-line interface (`page`, `line_reference`,
  `extraction_method`) is read when present and ignored when malformed; it has no
  producer today, so `source_page`/`row_reference` are normally NULL —
  `page_count` is never used as a page location (B2-D4; F-B2-7 stays a separate
  workstream).

**Forward hook** (B2-D6): one choke point —
`ManualExtractionRepository._materialise_evidence_lines` — invoked after a
successful `save_extracted_data` and after `update_item(extracted_data=…)`. It is
best-effort and **never raises** (a failed materialisation cannot break or roll
back an extraction save); the backfill is the safety net.

**Idempotency / rerun** (§11.3): insert-if-absent via
`ON CONFLICT (source_item_id, line_number) DO NOTHING` — never `DO UPDATE`. A
stored hash that differs from the currently derivable hash is a **DIVERGENCE**:
counted, reported per ordinal and audited, with no write, no update, no delete
and no renumbering (B2-D2).

**Amend-never-delete**: no `UPDATE`/`DELETE` statement for
`evidence_line_items` exists anywhere in the implementation; the repository's
`delete()` raises `NotImplementedError`; privileges deny `authenticated` writes;
ordinal decisions never touch an ordinal that has no current candidate.

**Class-1 backfill operation**: `EvidenceLineItemsRepository.backfill()`
(dry-run default, keyset-paginated by `manual_extraction_items.id`, batched,
resumable, run report) plus the CLI
`python -m tools.backfill_evidence_line_items [--apply] [--batch-size N] [--limit N] [--json]`.
It reads other tables read-only, inserts only missing lines, never re-extracts and
never touches `mapped_data`. **Execution against any environment remains
separately authorised**; in this task it was limited to a dry run on a disposable
clone.

---

## F. Tests (contract §20)

| Contract test | Result | Evidence |
|---|---|---|
| §20.1 `test_b2_migration.py` (static) | **PASS** — 14 tests | `pytest tests/unit/data/test_b2_migration.py -q` |
| §20.1 `test_evidence_line_items.py` (pure) | **PASS** — 18 tests | `pytest tests/unit/domain/test_evidence_line_items.py -q` |
| §20.1 `test_evidence_line_items_b2_runtime.py` (runtime) | **PASS** — 21 tests, `rc=0` | `INTEGRATION_DATABASE_URL=…carbontally_b2_clone_20260913 pytest … -q` |
| §20.1 Clone harness | **PASS** (`RESULT: PASS`, `rc=0`) | `python -m tools.b2_clone_schema_harness --source-url …/postgres` |
| §20.1/§20.6 B1 runtime suite on a B1+B2 database | **PASS** — 15 tests (incl. the amended boundary test) | `INTEGRATION_DATABASE_URL=…clone pytest tests/integration/test_disclosure_b1_runtime.py -q` |
| §20.2 #1 materialisation count/order | **PASS** | `test_01_forward_hook_materialises_count_and_order` (4 lines ⇒ ordinals 1–4, `FORWARD`, org = parent's, `csv` stamp, no `page_count`) |
| §20.2 #2 idempotency | **PASS** | `test_02_backfill_is_idempotent` (second run: 0 inserts, hashes identical) |
| §20.2 #3 identical duplicates stay distinct | **PASS** | `test_03_…` (2 rows, same hash, ordinals 1/2) |
| §20.2 #4 gaps | **PASS** | `test_04_…` (ordinals `1, 3`, `skipped_malformed=1`) |
| §20.2 #5 no `line_items` | **PASS** | `test_05_…` (0 rows, ineligible) |
| §20.2 #6 empty array, no flat fallback | **PASS** | `test_06_…` (`skipped_no_lines=1`, 0 rows) |
| §20.2 #7 snapshot linkage per ordinal | **PASS** | `test_07_…` (4 snapshots → 4 distinct lines; each line's `source_item_id` matches) |
| §20.2 #8 flat document | **PASS** | `test_08_…` (resolve empty, snapshot link NULL) |
| §20.2 #9 multiple calculations per line | **PASS** | `test_09_…` (2 snapshots → 1 line, row unchanged) |
| §20.2 #10 divergence | **PASS** | `test_10_…` (ordinal 2 divergent, stored rows unchanged, others unaffected) |
| §20.2 #11 forward-then-backfill | **PASS** | `test_11_…` (kind stays `FORWARD`, hashes identical) |
| §20.2 #12 RLS ALLOW/DENY | **PASS** | `test_12_…` (member 4 rows; cross-tenant 0; non-member 0; `anon` denied at privilege layer) + `test_12b_…` (PE-X sees its 4, PE-Y's 1 → 0; PE-Y → PE-X 0) |
| §20.2 #13 privileges | **PASS** | `test_13_…` (authenticated INSERT/UPDATE/DELETE → `InsufficientPrivilegeError`; service-role inserts) |
| §20.2 #14 historical immutability | **PASS** | `test_14_…` (`md5` unchanged; no retro-link) + `test_15_…` (evidence row `md5` unchanged after a backfill) |
| §20.2 #15 evidence linkage | **PASS** | `test_15_…` (column written; re-link idempotent; snapshot-derived when omitted; consistency invariant = 0 violations) |
| §20.2 #16 audit | **PASS** | `test_16_…` (1 forward event per document; exactly 1 summary event per run; 1 divergence event; no line values in payloads) |
| §20.2 #17 no re-extraction | **PASS** | `test_17_…` (static: no extractor/OCR/AI imports; runtime: `extracted_data`/`mapped_data` `md5` identical) |
| §20.2 #18 migration idempotency | **PASS** (harness, not faked in pytest) | `apply rc [0,0,0,0]`, `re-apply rc [0,0,0,0]`, `idempotent: True` |
| §20.2 #19 RESTRICT | **PASS** | `test_19_…` (`ForeignKeyViolationError`; 4 lines intact) |
| §20.2 #20 no retention artefact | **PASS** | `test_20_…` (0 triggers; exact 14-column set; RLS on; `delete()` raises) |
| §20.3 harness checks | **PASS** | `grants/policies/RLS/probe rows unchanged: True`; `declared delta only: True`; `idempotent: True`; `tables added by B2: ['evidence_line_items']`; `B1 delta on pre-existing tables: added=[] removed=[] changed=[]` |
| §20.4 whole unit suite | **PASS** — 0 failures | `python -m pytest tests/unit -q` (§F.1) |
| §20.4 whole integration suite | **PASS (subset argument)** — the 15 failures on the B2-provisioned clone are a **strict subset** of the 24 failures on `carbontally_test`; **no failure is unique to the B2 database** (`comm -23` empty) | §I F-024-6 |

**SKIPPED (declared, not a PASS)** — §20.7: the B2 runtime suite **skips** on the
dev/demo database and on `carbontally_test`, neither of which holds the B1/B2
schema. That standing gap is unchanged by this task and is exactly why the
disposable clone was provisioned.

**§20.5** — a skipped suite, a unit test alone, an upload or a static assertion are
not acceptance evidence. The acceptance evidence here is the provisioned-clone
runtime suite plus the harness diff.

### F.1 Commands (abridged)

```bash
# clone provisioning (§18.5) — the source database is read-only (pg_dump)
createdb -h 127.0.0.1 -p 54426 -U postgres carbontally_b2_clone_20260913
pg_dump -h 127.0.0.1 -p 54426 -U postgres --schema-only postgres > /tmp/b2_clone_schema.sql
psql -h 127.0.0.1 -p 54426 -U postgres -d carbontally_b2_clone_20260913 \
     -q -v ON_ERROR_STOP=1 -f /tmp/b2_clone_schema.sql
for pass in 1 2; do
  for m in 20260914000000_p8_b1_disclosure_model_foundation \
           20260915000000_p8_b1_correction_privileges_and_evidence_idempotency \
           20260916000000_p8_b2_evidence_line_items \
           20260916010000_p8_b2_provenance_line_links; do
    psql … -d carbontally_b2_clone_20260913 -q -v ON_ERROR_STOP=1 \
         -f supabase/migrations/$m.sql          # rc=0 on pass 1 AND pass 2
  done
done
# suites
INTEGRATION_DATABASE_URL=…carbontally_b2_clone_20260913 python -m pytest \
    tests/integration/test_evidence_line_items_b2_runtime.py -q   # 21 passed, rc=0
INTEGRATION_DATABASE_URL=…carbontally_b2_clone_20260913 python -m pytest \
    tests/integration/test_disclosure_b1_runtime.py -q            # 15 passed, rc=0
python -m pytest tests/unit -q                                    # see F.2
# harness + operational CLI (dry run — zero writes)
python -m tools.b2_clone_schema_harness --source-url …/postgres    # RESULT: PASS
DATABASE_URL=…carbontally_b2_clone_20260913 \
    python -m tools.backfill_evidence_line_items                  # dry run, rc=0
```

### F.2 Unit-suite result

`python -m pytest tests/unit -q` → **`rc=0`, 0 failures** (the run reached 100 %
with no `FAILED` lines). The files affected by the additively-changed signatures were also
re-run individually to `rc=0` before the full run: `test_v3_operations.py`,
`test_v3_d23_extraction_ux.py`, `test_v3_entity_extraction.py`,
`test_gate4_remediation_actor_provenance.py`, `test_phase1_core_regressions.py`,
`tests/unit/data`, `tests/unit/domain/test_evidence_line_items.py`.

The single test-infrastructure change this required is a *contract* consequence,
not a convenience (§20.4): `MemoryManualExtraction.save_extracted_data` and the
in-memory `RepositoryBundle` had to accept the contract's additive
`extraction_method` keyword and the new `evidence_line_items` field. The
*production* signatures remain strictly additive (defaulted keyword / added
field), so no existing production caller changes.

---

## G. Environment

| Question | Answer |
|---|---|
| Where were the migrations applied? | Disposable clones only: `carbontally_b2_clone_20260913` (`createdb` + `pg_dump --schema-only postgres \| psql`) and `carbontally_b2_harness` (created by the harness), both on the local Postgres `127.0.0.1:54426` |
| Was a disposable privileges-inclusive clone used? | **Yes** — ACLs/policies/RLS travel with `pg_dump --schema-only`, and the harness proves their parity before↔after |
| Were the dev/test databases modified? | **No.** `postgres` (dev/app) was only read by `pg_dump`; `carbontally_test` was used only as an integration baseline (unchanged behaviour) |
| Was the investor-demo data touched? | **No** |
| Was production touched? | **No** — no production connection, migration, data change or deployment |
| Are the two B2 migrations applied anywhere real? | **No** — they exist only in the disposable clones |
| Was B1 modified? | **No** — B1's files are byte-identical; B1 was applied only to the disposable clones as B2's dependency |

---

## H. Scope confirmation

| Boundary | Status |
|---|---|
| P1 (PDF/IMAGE extraction) untouched | **Confirmed** — no change to `automatic_extraction.py`, `extraction_suggestions.py`, `ai_document_extraction.py` or `api/v3_processing_workflow.py`; no OCR/AI/row-extraction/page-remediation logic added |
| P2 / EF-E untouched | **Confirmed** |
| S1 / S2 (A-RLS) / S3 / S4 / S5+ untouched | **Confirmed** — no report-table RLS change, no lifecycle change, no narrative/frozen-artefact work |
| B3 / B4 untouched | **Confirmed** — no framework/requirement mapping, projections, intensity, templates |
| Phase 8-X / Phase 9 untouched | **Confirmed** |
| Insight / I1 untouched | **Confirmed** — no insight tables, messages or interactions |
| RLS remediation untouched | **Confirmed** — only B2's own two SELECT policies were created; no unrelated policy altered, no FORCE RLS |
| Calculation / factor engine untouched | **Confirmed** — no formula, factor selection, conversion, rounding, methodology or request-id derivation change; `CalculationRequest` gained one optional field and the snapshot one optional column |
| New API / frontend | **None** — no endpoint, no UI, no response-shape change |
| Production deployment | **None** — no production migration, push or deploy |
| Git | **No commit, no push, no reset, no clean, no stash, no staging**; the 208 pre-existing modifications and every unrelated untracked file are intact |

---

## I. Remaining blockers / findings

| ID | Finding | Impact | Disposition |
|---|---|---|---|
| F-024-1 | Contract §11.2's BACKFILL attribution rung 2 (`manual_extraction_batches.ai_extraction_method`) **does not exist in the schema** — the extraction-method stamp is persisted only on `document_processing_queue.ai_extraction_method` (exactly as the contract's own F-B2-15 records). | none functional | The implemented chain is `queue.ai_extraction_method` → `unknown` (the contract's declared honest default). **No column was invented** and no schema/semantics were fabricated. Recorded for PO awareness; no PO decision required. |
| F-024-2 | The human-site method stamp could not be supplied at `backend/api/v3_processing_workflow.py`: task §7 forbids modifying that P1 file. | negligible (provenance label only) | Those saves record the queue-derived stamp, else the honest `unknown` (§11.2 permits `unknown` when a site cannot supply one). Bounded, documented deviation; the other human sites (`v3_operations.py`) pass `"manual"` and the automatic pipeline passes its real `method_stamp`. |
| F-024-3 | B2's line provenance is included in `CalculationSnapshot._canonical()` **only when set** (§8.4 "new snapshots only"), so pre-B2 `content_hash` values are byte-identical and request-id derivation is untouched (§8.4 prohibition respected). | none now; forward-looking note | Consequence to record for later readers: a consumer that reconstructs a `CalculationSnapshot` from a database row must carry `source_line_item_id`, otherwise a *line-aware* snapshot would look tampered. `_SNAPSHOT_COLUMNS` now returns the column. |
| F-024-4 | `EvidenceLineItemsRepository.delete()` raises `NotImplementedError` (B2 has no delete path; §12.3/B2-D11). | none | Intentional: a silent no-op would be a false affordance. Documented so no generic caller assumes a no-op. |
| F-024-5 | A **dry-run** backfill writes no audit row at all, so §11.4's "zero writes" is literally true; the real run writes exactly one summary event per run. | none | The run report carries `audit_written`, so a silent audit failure cannot be mistaken for success (§17). |
| F-024-6 | Pre-existing integration failures: the B2-provisioned clone reports 15 failures, all of which are a **strict subset** of the 24 failures reported by the same suite on `carbontally_test`; `comm -23` (clone-only) is **empty** — no failure is attributable to the B2 database or to this change. | pre-existing / environmental | Recorded, not fixed (outside B2 scope; §22.2 "broad RLS remediation"/unrelated suites). |
| F-024-7 | Dev/test databases still hold no B1/B2 schema, so the B2 runtime suite **SKIPS** there. | standing verification gap | A skipped suite is **not** a PASS; V2 evidence therefore comes from the disposable clones above (contract §18.5, §20.7). Unchanged by this task. |

No unresolved contract conflict, no reopened B2 decision and no hard-stop
condition was triggered. Nothing in the contract was silently resolved or
broadened.

---

## J. Final verdict

### `B2 IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT VERIFICATION`

Stated precisely, in the authorised vocabulary:

| State | Status |
|---|---|
| AUTHORISED | ✅ (`CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019`) |
| IMPLEMENTED | ✅ (2 migrations, domain + data layer, forward hook, backfill operation + CLI, calculation/evidence linkage, audit, tests, harness) |
| TESTED (implementation evidence) | ✅ 14 static + 18 pure + 21 runtime tests, harness PASS, B1 regression suite PASS, whole unit suite `rc=0`, integration failure-set subset argument |
| READY FOR INDEPENDENT VERIFICATION | ✅ |
| INDEPENDENT VERIFICATION | ⬜ **not performed here** (separate task, separate authority) |

**Not claimed:** independent verification, production readiness, acceptance, or
completion of any later batch (B3/B4/8-X/9) — none of which was implemented.
Implementation stopped at the authorised boundary; no commit, push or deployment
was performed.

