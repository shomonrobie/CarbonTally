# CT-PROD-BACKUP-IV-20260911-001

**Prompt Ref:** `CT-PROD-BACKUP-IV-20260911-001`
**Datetime:** 2026-09-11 (independent verification executed same day)
**Mode:** INDEPENDENT VERIFICATION — READ-ONLY (no implementation changes)
**Implementation under verification:** `CT-PROD-BACKUP-IMPLEMENTATION-20260911-001`
**Decisions reference:** `CT-PROD-BACKUP-DECISIONS-20260911-002` (D1–D5, ratified)
**Repository:** CarbonTally · branch `main` · **HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged)
**Verifier:** Cline (independent verification pass)

## VERDICT

## B. INDEPENDENT VERIFICATION PASS WITH NON-BLOCKING FINDINGS

D1, D2, D3, D4, D5, snapshot consistency, artifact integrity and failure safety **all pass** on
independently obtained evidence. No P0/P1 implementation defect was found, no unauthorised production
access occurred and no unexpected repository modification was made. Twelve findings were recorded, all
P2/P3 — including **one P2 current to the schema** (comments not captured) and **two P2s material to any
future restore** (partition double-count; identity-column capture).

---

## 1. Scope and independence method

The mandate was to determine whether the implemented Backup Foundation actually satisfies its stated
architectural and security claims — **not** to re-run the author's tests and declare success. Accordingly:

* the implementation was inspected at source level (all 9 modules, all 5 test files);
* repository-wide static searches were run for every prohibited technique and secret class;
* **independently written harnesses** (in `/tmp`, never in the repository) created their own disposable
  databases and exercised the real code paths: snapshot semantics, end-to-end export, storage-boundary
  content, determinism, tamper behaviour, failure injection, concurrency, temp hygiene and catalog
  coverage;
* the author's suites were additionally re-run to verify the claimed counts;
* every claim that could be measured was measured, and two of my own initial harness results were
  **root-caused as harness defects rather than reported as implementation defects** (see §7).

## 2. Files inspected

```
backend/backup/{__init__,errors,settings,catalog,exporter,artifact,crypto,storage,service}.py
backend/tests/unit/backup/{test_artifact,test_crypto,test_storage_and_settings,test_service}.py
backend/tests/integration/backup/test_exporter_local.py
backend/requirements.txt ; backend/pyproject.toml (pytest config) ; backend/.gitignore
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md   (Part 2, D1–D5)
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md
docs/cline/prompt-history/CT-PROD-BACKUP-IMPLEMENTATION-20260911-001.md
supabase/migrations/**       (grep: PARTITION BY / IDENTITY / GENERATED / COLLATE / UNLOGGED / COMMENT ON / OWNED BY)
backend/routes/**            (restore-endpoint search)
backend/infra/supabase.py    (connection path only)   backend/_phaseA_selfcheck.py (pre-existing subprocess user, context only)
```

## 3. Files changed by this verification

```
NONE — no implementation, test, migration, configuration or architecture document was modified.
```

Created (documentation artifact only, as required by the mandate):

```
docs/cline/prompt-history/CT-PROD-BACKUP-IV-20260911-001.md   (this file)
```

Temporary harnesses were written under `/tmp` only (`iv2.py`, `iv3.py`, `iv_cov.py`, `iv_cov2.py`,
`iv_auth.py`) and never inside the repository. No staging, commit, reset, push or deploy was performed:
`git rev-parse HEAD` is unchanged and `git diff --cached --name-only` is empty.

## 4. Commands and tests executed (with results)

```
git rev-parse HEAD ; git ls-tree -r --name-only HEAD | grep backup     # Phase 1 NOT committed
git status --short ; git diff --stat ; git diff -- backend/requirements.txt
git diff --name-only -- backend/                                       # ONLY requirements.txt
grep -rnE 'subprocess|pg_dump|pg_restore|os\.system|os\.popen|shell=True|asyncio\.create_subprocess|docker' --include='*.py' backend/
grep -rniE 'ct_backup|bypassrls|create role|alter role' --include='*.py' --include='*.sql' backend/ supabase/
grep -rniE 'restore|pg_restore|recovery' backend/backup/ backend/routes/
grep -rniE 'eyJ|service_role_key|sb_secret|BEGIN .*PRIVATE KEY|password\s*=|api[_-]?key\s*='  (Phase-1 files)
grep -c <attr> backend/backup/catalog.py   # attidentity/attgenerated/attcollation/relpersistence/relacl/attacl/partkeydef/pg_description/OWNED
python -m pytest tests/unit/backup tests/integration/backup -q         # 58 passed
python -m pytest tests/unit -q                                         # 1709 passed, 0 skipped, 0 failed
/tmp/iv3.py     (harness: snapshot, e2e, artifact, data, crypto, failure, temp, concurrency, determinism)
/tmp/iv_cov2.py (catalog coverage + partition double-count probe)
/tmp/iv_auth.py (is the `auth` exclusion enforced, or only a config default?)
psql -tAc "select datname from pg_database where datname like 'ct_iv_%' or datname like 'ct_backup_it_%'"   # 0 leftovers
```

| Suite / harness | Result |
|---|---|
| `tests/unit/backup` + `tests/integration/backup` | **58 passed / 0 failed** — author claimed 58: **confirmed** |
| `tests/unit` (full regression) | **1709 passed / 0 skipped / 0 failed / 0 errors** — author claimed 1709: **confirmed** |
| Independent harness `/tmp/iv3.py` | **9/9 areas PASS** (snapshot, e2e, tar metadata, COPY data, crypto, failure, temp, concurrency, determinism) |
| Disposable databases left behind | **0** |

## 5. Independent evidence summary (part 1)

| Area | Result | Key evidence (measured, not asserted) |
|---|---|---|
| **D1** asyncpg exporter | **PASS** | `copy_from_query` used; `_format_copy_opts(format=None)` returns `''` → `COPY (…) TO STDOUT` = PostgreSQL **default text** format; only `pg_get_*` helpers used; **no** `subprocess`/`pg_dump`/`docker`/`os.system`/`shell=True` in Phase-1 code (matches are docstrings asserting absence; the sole repo `subprocess` is the pre-existing `_phaseA_selfcheck.py`) |
| **D2** storage boundary | **PASS** | Independent spy store captured the single `put_object` payload: starts with the envelope magic, is **not** a readable gzip archive, contains no plaintext marker, contains no key material, and its SHA-256 equals `record.ciphertext_sha256`. No cloud SDK imported or installed |
| **D3** encryption | **PASS** | AES-256-GCM; 12-byte nonce (base64 len 16) fresh per call; wrong key → `BackupIntegrityError`; last-byte ciphertext flip → rejected; **same-length header mutation → rejected** (proves the header really is GCM associated data); metadata exposes only `{envelope_version, algorithm, key_id}`; key required **before** any DB/storage work; masked in `repr` |
| **D4** restore boundary | **PASS** | No restore function/module/endpoint/CLI; `git diff --name-only -- backend/` = `requirements.txt` only → **no route added**; the only `/restore` routes (glossary, organisation files) are pre-existing (`077c866`) and unrelated; no permission or approval workflow added |
| **D5** `ct_backup` boundary | **PASS** | Only match inside `backend/backup/` is the read-only catalog select `r.rolbypassrls AS bypasses_rls`; **no** `CREATE ROLE`/`ALTER ROLE`/`GRANT`; repo-wide search for executable `CREATE ROLE ct_backup` = **none**; the proposed SQL exists only in the architecture doc (l.943/946) marked `PROPOSED — NOT EXECUTED` |
| **Snapshot consistency** | **PASS** | Inside the exporter's exact kwargs the server reports `transaction_isolation = repeatable read`, `transaction_read_only = on`; a concurrent **committed** INSERT was invisible inside the snapshot and visible outside it. Catalog reads, every COPY and the sequence reads share that one transaction |
| **Artifact format** | **PASS** | All six v1 members present and named as documented; machine-readable `backup_format {name, version=1}`; manifest counts/inventory consistent; `ddl.sql` present |
| **Checksums** | **PASS** | Per-member checksums verify; `sha256(decrypted archive) == record.archive_sha256` (computed independently over the pre-encryption bytes); `sha256(stored) == record.ciphertext_sha256`; the three layers are not confused |
| **Temp / failure safety** | **PASS** | Staging dir observed at cleanup with mode **0700**; removed on success, on storage failure, on broken connection and when the key is missing; spy store proves **nothing is published** on any failure; missing key refuses before any DB work (`copy_calls == []`) |
| **Determinism** | **PASS** | Two runs with identical `created_at`/`backup_id` produced **byte-identical** plaintext archives and identical manifests; tar members sorted with `mtime=0/uid=0/gid=0/uname=''/gname=''/mode=0600`; gzip `FLG=0` and `MTIME=0`; ciphertext differs by design (fresh nonce) |
| **Concurrency** | **PASS** | Two concurrent exports → distinct object keys and staging dirs; each stored artifact carries its own `backup_id`; object key deterministic for a fixed id |


## 5.1 Independent evidence summary (part 2) — capture coverage and data fidelity

| Area | Result | Key evidence |
|---|---|---|
| **Catalog capture (OID-1)** | **PASS WITH FINDINGS** | Captured: schemas, tables, columns (type/nullable/default/ordinal), PK, FK (with definition text), unique/check/exclusion constraints, indexes incl. partial predicates, sequences + state, functions (`pg_get_functiondef`), triggers, RLS-enabled flag, policies, views/**matviews**, extensions, safe role metadata (never passwords), `serial` defaults (`nextval(...)`). **Not captured** (0 occurrences in `catalog.py`): `attidentity`, `attgenerated`, `attcollation`, `relpersistence`, `relacl`/`attacl` (ACLs are documented), `pg_get_partkeydef`, `pg_description`, sequence OWNED BY → findings F3–F9. Helpers actually used: `pg_get_constraintdef`, `pg_get_expr`, `pg_get_functiondef`, `pg_get_function_identity_arguments`, `pg_get_indexdef`, `pg_get_triggerdef`, `pg_get_viewdef` |
| **Sequence state (OID-2)** | **PASS** | Fixture `setval('public.seq_demo', 777, true)`: `last_value=777`, `is_called=true` appear in both the manifest inventory and `catalog/sequences.json`, associated with the correct sequence |
| **Data export fidelity** | **PASS** | Row counts equal the **PostgreSQL oracle per table**; embedded real newline escaped (`\n`) so physical line count stays exact; tab, backslash, `"`, `'`, comma, NULL (`\N`), emoji (UTF-8 byte-exact), combining mark, accents, bytea hex, empty string, NULL-only row, empty table, no-PK table, quoted mixed-case identifiers all correct |
| **Dependency / security** | **PASS** | asyncpg 0.30.0 satisfies `>=0.30.0`; cryptography 50.0.0 satisfies `>=41.0.0`; **no** boto3/botocore/aioboto3/google-cloud/azure/minio/docker/psycopg installed or imported by Phase 1; no secrets, keys, tokens or production URLs in Phase-1 code or docs |
| **Suite quality** | **PASS WITH GAPS** | The author's boundary tests genuinely bind what they claim — e.g. the same-length header mutation test would fail if the header were not authenticated; `copy_calls == []` proves no database work happens before the key check; the storage-boundary test asserts magic-prefix, absence of plaintext markers and digest equality. **Gaps:** no test covers a partitioned table (F1), identity/generated/collation columns (F3–F5), comments (F9), or the post-publish digest-mismatch branch (F11) |

## 6. Findings (part 1)

### F1 — Partitioned tables are exported twice (parent **and** each leaf), inflating counts
* **Class:** P2 — correctness/reliability (artifact metadata; future restore fidelity)
* **Evidence:** measured `pg_class` relkinds `parted='p'`, `parted_a='r'`, `parted_b='r'`; the exporter filter is `relkind IN ('r','p')` (`catalog._TABLE_KINDS`), so parent **and** leaves qualify. Probe inventory: `parted rows=2`, `parted_a rows=1`, `parted_b rows=1` → `counts.rows = 7` against an independent physical-row oracle of `5`. COPY on a partitioned parent returns **all** partition rows (verified: parent = 2), so a naive restore of parent + leaves would **duplicate** data.
* **Affected files:** `backend/backup/catalog.py` (`_TABLE_KINDS`), `backend/backup/exporter.py`, implementation doc §8.5
* **Already documented?** **Partially and inaccurately** — the doc states “Partition children are not individually recursed (`relkind='p'` parents are captured)”, which the measurement contradicts; the count inflation and duplication consequence are not disclosed.
* **Current-schema impact:** **latent** — `grep -rn 'PARTITION BY' supabase/migrations/` = 0 matches.
* **Recommended action:** decide the Phase-2 policy (leaves only, or parents only), make `counts.rows` unambiguous, correct the documentation, add a partitioned-table integration test.

### F2 — The `auth`-schema exclusion is a configuration default, not an enforced guard
* **Class:** P2 — security hardening + documentation accuracy
* **Evidence:** `DEFAULT_SCHEMAS = ('public',)` → default export contains no `auth` object (marker absent). With `CT_BACKUP_SCHEMAS=public,auth` the probe produced `data/auth__users.copy` **containing the credential-like marker**, and `encrypted_password` was captured as a column.
* **Affected files:** `backend/backup/settings.py`, `backend/backup/catalog.py`, implementation doc §8.7
* **Already documented?** **Incorrectly phrased** — “intentionally excluded … avoids exporting password hashes” reads as an enforced rule; in code it is only a default value with no deny-list.
* **Mitigations:** artifact is encrypted (D3); requires explicit operator action; no scheduler/UI exists in Phase 1.
* **Recommended action:** enforce a deny-list for credential-bearing schemas (`auth`, `storage`, `vault`, …) with a documented override, and correct the documentation.

### F3 — IDENTITY columns are not captured
* **Class:** P2 — future restore fidelity
* **Evidence:** `attidentity` = **0** occurrences in `catalog.py`; PostgreSQL held `attidentity = 'a'`; the captured record for `ident.id` is `{'data_type': 'integer', 'default_expression': None, 'not_null': True, …}` and `ddl.sql` renders no `IDENTITY`.
* **Consequence:** a restore would create a plain `integer NOT NULL` with no default/sequence → identity-dependent inserts fail.
* **Documented?** No. **Current-schema impact:** latent (0 identity columns in migrations).
* **Recommended action:** capture `attidentity` (+ sequence options) and render `GENERATED … AS IDENTITY`.


### F4 — `GENERATED … STORED` columns are captured as an ordinary DEFAULT
* **Class:** P3 · **Evidence:** `attgenerated` = **0** occurrences; `basic.slug` captured as `{'data_type': 'text', 'default_expression': 'lower(note)'}` with no generated marker → a restore would emit `DEFAULT lower(note)` (overridable) instead of a generated column. **Documented?** No. **Impact:** latent (no generated columns in the current schema).

### F5 — Column collation is not captured
* **Class:** P3 · **Evidence:** `attcollation` = **0** occurrences; `basic.name` (declared `COLLATE "C"`) is captured as plain `text`, losing comparison/ordering semantics on restore. Undocumented; latent (no `COLLATE` in migrations).

### F6 — UNLOGGED persistence is not captured
* **Class:** P3 · **Evidence:** `relpersistence` = **0** occurrences; a restore would create LOGGED tables. Undocumented; latent (no `UNLOGGED` in migrations).

### F7 — Sequence OWNED BY linkage is not captured
* **Class:** P3 · **Evidence:** no `pg_get_serial_sequence`/owned-by query; captured sequence fields are `{schema, name, qualified_name, start_value, increment_by, min_value, max_value, cache_size, is_cycled}` only → a restore cannot re-attach a sequence to its column. Partially mitigated because `serial` defaults (`nextval(...)`) *are* captured. Undocumented; latent.

### F8 — Partition key and bounds are not captured
* **Class:** P3 · **Evidence:** `pg_get_partkeydef` = **0** occurrences; the partition strategy cannot be reconstructed (relates to F1). The doc mentions children only. Latent.

### F9 — Table and column comments (COMMENT ON) are not captured
* **Class:** P3 — but **current to the schema** · **Evidence:** `pg_description` = **0** occurrences, while `grep -rn 'COMMENT ON' supabase/migrations/` finds real comments on `public.calculation_snapshots` (table, column `co2e_multiplier`) and column `performed_by`. Those comments would not survive a restore. **Documented?** No.

### F10 — No validation of a caller-supplied `backup_id` when building the object key
* **Class:** P3 — hardening (latent)
* **Evidence:** `create_backup(backup_id="../../escape-attempt")` produced the key `backups/../../escape-attempt/carbontally-logically… `. The local filesystem provider **correctly refused** the traversal (`BackupStorageError`, and no file was created outside its root). **Reachability in Phase 1:** none — there is no API/UI and `backup_id` defaults to `uuid4().hex`.
* **Recommended action:** validate/sanitise `backup_id` in the service (e.g. `[A-Za-z0-9_-]`), which also protects future providers and any presigned-URL logic.

### F11 — Post-publish digest guard is untested and provider-specific; a failure leaves an orphan object
* **Class:** P3 / E (evidence gap)
* **Evidence:** `service._publish` raises `BackupIntegrityError` when `stored.sha256 != ciphertext_sha256` **after** a successful `put_object`, so the object is already stored (no compensating delete). `grep` across `tests/` finds **no** test exercising this branch. Local/in-memory providers report a true SHA-256, but common cloud providers report MD5/ETag (not SHA-256, and not even MD5 for multipart uploads), so a future provider could trip a false failure while orphaning a valid artifact.
* **Recommended action:** define per-provider digest semantics (compare only when the provider documents SHA-256), best-effort delete on post-publish validation failure, and add a test.

### F12 — Documentation accuracy corrections required
* **Class:** P2 — documentation accuracy (bundle of F1/F2 plus omissions)
* **Evidence:** implementation doc §8.5 (partitions) and §8.7 (`auth`) do not match measured behaviour (F1, F2); the limitations list omits the capture gaps F3–F9.
* **Note:** the document is otherwise accurate and honest — it discloses the absence of restore, ACL capture, extension internals, ordering determinism, Storage-object coverage and database-size measurement, and it records the two defects found during implementation.
* **Minor hygiene note (P3):** the author's implementation history artifact contains a local-loopback developer credential in a quoted command (`PGPASSWORD=postgres … -p 54426`). It is the Supabase CLI's well-known local default on 127.0.0.1, not a production secret, and the file is untracked — but it should not be carried into any committed document.

## 7. Harness defects found and corrected during this verification

To keep the verification honest, two of my own first-pass results were investigated and found to be **harness**
problems, not implementation defects — they are recorded rather than discarded:

1. **False “snapshot not held”** — my first probe ran `SHOW transaction_isolation` before any data statement
   and inserted concurrently straight after; PostgreSQL fixes the REPEATABLE READ snapshot at the first
   **data** statement, so the concurrent row was legitimately visible. The corrected probe reads data
   first and then confirms the concurrent insert stays invisible (PASS).
2. **False “row count / unicode mismatch”** — my first harness inserted a probe row into `pk_table` (state
   pollution) and wrote an emoji inside a **raw** Python string (so PostgreSQL stored the literal
   `\U0001F600`). Corrected by isolating the snapshot table and sending adversarial values as real
   parameterised values; all data-fidelity assertions then passed. Two similarly unsound *substring*
   probes (`"identity"`, `"unlogged"`, `"owned"`) were replaced with explicit field inspection — the
   substrings were matching the catalog's top-level `identity` block, the table name `unlogged_t`, and the
   sequence name `seq_owned`.


## 8. DR-20 status

## NOT SATISFIED — restore drill still required.

Phase 1 demonstrably produces an encrypted, checksummed, deterministically archived, off-site-ready artifact,
but `DR-20` additionally requires a **proven restore into a disposable/recovery environment**. No restore
capability exists (D4 — verified absent), so `DR-20` cannot be satisfied by this work.

## 9. Migration 22 → 53 authorization status

## NOT AUTHORIZED.

Nothing in this verification changes that, and it must not be inferred from the Phase-1 PASS.

## 10. Recommended next bounded operation (requires separate PO authorization)

**Minimum next step:** a bounded **Phase-1.1 “catalog capture completeness + documentation correction”**
operation addressing F1–F12, before any restore work:

1. resolve the partitioned-table double-count policy and make `counts.rows` unambiguous (F1);
2. enforce a credential-schema deny-list and correct the `auth` claim (F2);
3. capture `attidentity`, `attgenerated`, `attcollation`, `relpersistence`, sequence OWNED BY, comments and
   partition key/bounds, or document each as an explicit, accurate limitation (F3–F9);
4. validate `backup_id` (F10) and settle the provider-digest semantics + add coverage (F11);
5. correct implementation-doc limitations §8.5/§8.7 and extend the list (F12).

Restore implementation (D4) and the `DR-20` drill remain a **separate** later authorization, as do the
`ct_backup` role, off-site provisioning and the encryption-key custody work.

## 11. Stop-condition confirmation

**No stop condition was triggered.** No production credentials, production database access or production SQL
were required; no migration was changed or executed; no `pg_dump`/Docker/subprocess was needed; the snapshot,
encryption, integrity and failure-safety behaviours all verified; no unrelated architecture change was needed;
no critical regression appeared (1,709 pre-existing unit tests still pass); no ambiguity required a new PO
decision. **No remediation was implemented** — the mandate was to verify, and the findings are recorded for a
separately authorized follow-up.

## 12. Production-safety verification

| Item | Status |
|---|---|
| Contacted production database | **NO** |
| Read/dumped production data | **NO** |
| Created production backup / role / storage / key | **NO** |
| Altered production schema / RLS / grants / Auth | **NO** |
| Executed migrations | **NO** |
| Deployed / pushed / committed / staged | **NO** |
| Repository files modified | **NONE** (only this documentation artifact was created) |
| Databases used | Local **loopback** PostgreSQL 17.6 only, each created and dropped by the harness (0 leftovers) |

Supporting evidence: `DATABASE_URL`, `SUPABASE_DB_URL` and `SUPABASE_URL` are **unset** in the working
environment, and `infra.supabase.get_database_url()` resolves to `postgresql://***@127.0.0.1:54426/postgres`
— so even the default (non-injected) connection path is loopback, not production. Every harness pass injected
its own connection factory to a uniquely named disposable database.

**Advisory (P3, for the future scheduling phase):** the default factory would consult whatever `DATABASE_URL`
is present, and there is no environment tagging or guard that refuses to run against an unexpected host. A
Phase-3 scheduler should require an explicit target (and ideally refuse non-production hosts unless
deliberately overridden).

## 13. No-change confirmation

```
Implementation modified:      NO       Tests modified:            NO
Migrations modified:          NO       Architecture docs:        NO
Configuration modified:       NO       Credentials/keys created:  NO
Git commit / push / deploy:   NO       Staged changes:            0
HEAD:                         daad396523ac693352cc2f4ebb7fc58814a9e60b (unchanged)
Untracked Phase-1 paths:      backend/backup/, backend/tests/{unit,integration}/backup/, the two Phase-1 docs
Modified tracked file:        backend/requirements.txt (Phase 1 — one dependency declaration)
```

All other working-tree changes (362 files) are **pre-existing and unrelated**: the only modified file anywhere
under `backend/` is `requirements.txt`, so no Phase-1 code changed any existing backend file.

