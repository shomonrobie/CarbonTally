# CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001

**Prompt Ref:** `CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001`
**Response Ref:** `CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001-R1`
**Datetime:** 2026-09-11 (implementation executed same day)
**Role:** CarbonTally implementation agent
**Mode:** BOUNDED IMPLEMENTATION — repository-only
**Baseline:** Phase 1 backup foundation (`CT-PROD-BACKUP-IMPLEMENTATION-20260911-001`) plus its independent
verification (`CT-PROD-BACKUP-IV-20260911-001`, verdict **PASS WITH NON-BLOCKING FINDINGS**)
**Decisions baseline:** `CT-PROD-BACKUP-DECISIONS-20260911-002` (D1–D5, ratified — **not reopened**)
**HEAD at start and end:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged; Phase 1/1.1 remain
working-tree only)
**Final status:** `P1.1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

## 1. Prompt (normative content)

The governing prompt directed a single tightly bounded operation: **remediate findings F1–F12 from the
independent verification of the Phase-1 backup foundation**. Its normative content, reproduced in structure:

**Authorised:** modify Phase-1 backup implementation files; modify Phase-1 backup tests; add narrowly
necessary backup tests; modify Phase-1 backup documentation; improve catalog capture; improve backup artifact
validation; improve backup storage-key validation; update `backend/requirements.txt` only if genuinely
required; run local/disposable database tests; run existing backup tests; run relevant unit/integration
tests; create the durable history artifact.

**Not authorised:** connect to production; read/write production data; create production roles or
`ct_backup`; execute production SQL; apply migrations; modify production RLS/Auth; create the production
`documents` bucket; load emission factors; **implement restore** (endpoints, CLI, jobs or drill); modify
billing; fix `DR-19`; modify unrelated application code; modify migration files; modify E2E infrastructure;
deploy; push; commit. *"If a change is not directly required by F1–F12, do not make it."* Also explicit: do
not redesign the backup architecture, add a cloud provider, add a backup framework, or replace `asyncpg`
with `pg_dump`.

**Required remediations.** F1 partition double-export — policy: export the partitioned parent's logical rows
and do not separately export its leaves; data exactly once; counts accurate; catalog sufficient; no false
restore claims; tests cover a real partitioned table; docs match. F2 credential-schema exposure — explicit
deny-list for credential-bearing/private Supabase schemas; do not rely on encryption as the boundary;
fail-closed; override must be unmistakable and not the default; no credential material in tests beyond the
minimum synthetic fixture. F3 identity columns — capture, distinguishing ALWAYS / BY DEFAULT / none, with a
regression test. F4 generated stored columns — distinguish an ordinary default from a generated expression;
never misrepresent. F5 column collation — capture when non-default; no misleading metadata. F6 UNLOGGED
persistence — capture; do not start capturing ephemeral temporary objects; document the policy. F7 sequence
`OWNED BY` — capture ownership, keeping state / ownership / `nextval` default distinct. F8 partition
key/bounds/relationship — structured catalog authoritative. F9 comments — table and column comments. F10
`backup_id` validation — strict allow-list before key construction; no `/`, `\`, `..`, absolute paths or
control characters; fail closed with a typed error. F11 digest semantics — provider-independent checksum
semantics; application SHA-256 authoritative; never compare incompatible digests; refactor the interface to
distinguish provider-native checksum from application SHA-256; verify by read-back or an explicit provider
guarantee; on post-publication failure attempt cleanup, return a typed failure and never report false
success; test the mismatch branch; no cloud SDK. F12 documentation — correct partitions, `auth` policy,
identity, generated, collation, unlogged, sequence ownership, partition metadata, comments, provider
checksum semantics, backup ID validation and restore limitations; **do not claim restore, PITR or solved
production recovery**.

**Architectural rule.** `catalog.json` remains the authoritative structured backup catalog; `ddl.sql`
remains informational; all newly captured metadata must appear in the structured catalog.

**Test requirements.** Partitioning (parent, leaf, exact row-count semantics, no duplicate logical export);
credential schema (default excludes `auth`; explicit dangerous request fails closed or follows the
documented override; no credential material in normal artifacts); identity; generated columns; collation;
UNLOGGED; sequence ownership; partition key/relationship/bounds; table and column comments; backup ID
(traversal, slash, backslash, absolute-shaped rejected; valid accepted); digest mismatch (branch executes,
typed error, cleanup attempted, no false success, final storage state documented). Do not weaken existing
tests or remove security assertions.

**Execution requirements.** Run backup unit tests, backup integration tests, the full `backend/unit`
regression and focused tests; report exact passed/failed/skipped/errors; fix only defects introduced by this
operation and document unrelated pre-existing failures without broadening scope. Database-backed tests must
use local, loopback, disposable, uniquely named databases and verify no disposable database remains.

**Security requirements.** No secrets committed; no passwords captured; no private credential material;
encryption remains mandatory; tag verification intact; staging permissions restrictive; storage boundary
receives ciphertext only; path traversal rejected; no cloud SDK; no subprocess/`pg_dump`/docker dependency.

**Change boundary.** Record Git status before and after; identify every changed/untracked file; do not stage,
commit, push or clean unrelated working-tree changes.

**Deliverables.** Update the existing Phase-1 backup documentation (no new master architecture document; no
unrelated reorganisation); create this history artifact; report an implementation status, a finding matrix,
exact regression counts, production safety, and the mandated no-change block (§11).

**Stop condition.** After implementing F1–F12, running the required tests, updating documentation and
creating the durable record — **STOP**. No commit, push, deploy or production contact; a separate
independent verification of Phase 1.1 follows.


## 2. Files changed (existing Phase-1 files — modified)

| File | Change |
|---|---|
| `backend/backup/settings.py` | Added `DENIED_SCHEMAS`, `DENIED_SCHEMA_OVERRIDE_PHRASE`, `DEFAULT_VERIFY_READBACK`, `validate_schemas()`; new `BackupSettings` fields `allow_denied_schemas` and `verify_readback` (both surfaced in `__repr__`); `from_env` now parses `CT_BACKUP_DENIED_SCHEMA_OVERRIDE` / `CT_BACKUP_VERIFY_READBACK` and validates schemas (F2, F11). |
| `backend/backup/errors.py` | Added typed `BackupValidationError` (`BACKUP_VALIDATION_ERROR`, HTTP 400) for fail-closed identifier validation (F10). |
| `backend/backup/artifact.py` | Added `BACKUP_ID_PATTERN` and `validate_backup_id()` (F10). |
| `backend/backup/catalog.py` | New/updated introspection: table `relkind`/`is_partitioned`/`persistence`/`comment`; column `attidentity`→`identity_kind`, `attgenerated`→`generated_kind`/`generation_expression`, non-default `collation`, `comment`; sequence `owned_by` via `pg_depend` (deptype `a`/`i`); new `_PARTITIONS_SQL` + `partitions` section; shared `_exportable_table_filter()` applying `relkind`, `NOT relispartition` (F1) and `relpersistence <> 't'` (F6) consistently to tables, columns, constraints and indexes; `_normalize_columns()`; DDL rendering for identity, generated, collation, UNLOGGED, comments, `OWNED BY` and partition metadata; `_sql_literal()`. |
| `backend/backup/exporter.py` | `export_schemas(..., allow_denied_schemas=False)` validates schemas **before** opening the snapshot (F2) and preserves typed errors. |
| `backend/backup/storage.py` | `StoredObject` digest refactor: `content_sha256` (application SHA-256, only when guaranteed) separated from `provider_checksum`/`provider_checksum_algorithm` (native ETag/MD5); providers updated accordingly; protocol docstring states the contract (F11). |
| `backend/backup/service.py` | Validate `backup_id` and schemas before any work (F10/F2); pass the override through to the exporter; new `_verify_published()` (provider-declared SHA-256 + application read-back) and `_discard_published()` cleanup with typed failure (F11); manifest inventory/counts include `partitions` (F8). |
| `backend/backup/__init__.py` | Public surface extended with `BackupValidationError`, `validate_backup_id`, `validate_schemas`, `DENIED_SCHEMAS`, `DENIED_SCHEMA_OVERRIDE_PHRASE`. |
| `backend/tests/unit/backup/test_service.py` | Extended fake-catalog fixture (identity/generated/collation/comment columns, `persistence`, comments, `owned_by`, partitioned parent, partition rows) and added `TestPhase11CatalogCapture` (7 tests); two stale index-based assertions made name-based. |
| `backend/tests/integration/backup/test_exporter_local.py` | Fixture extended with identity/generated/collation table, UNLOGGED table, owned sequence, real partitioned table (`events` + 3 leaves, 4 rows), comments and a synthetic `auth` scaffold; added `_exported_row_counts()` oracle and `TestPhase11Capture` (6 tests); stale sequence-index assertions made name-based. |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md` | New §0 Phase 1.1 remediation summary; corrected partition and `auth` limitations; new configuration entries; checksum-semantics section; limitations 12–15; verification summary updated (F12). |
| `docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001.md` | Created — this durable record. |

`backend/requirements.txt` was **not** changed: no new dependency was required (F1–F12 use only `asyncpg`,
`cryptography`, `hashlib`/`re` and the existing standard library).


## 3. Tests added

**`backend/tests/unit/backup/test_p1_1_remediation.py` (new file, 45 tests).**
`TestSchemaDenyList` (F2: default is public-only; `auth`/`storage`/`vault`/`realtime` refused; check is
case-insensitive; the exact override phrase is required; the override is never the default; helper
behaviour; the exporter refuses **before touching the connection** — proven with a connection double that
raises if any method is called; the exporter proceeds only with the override; hand-built `BackupSettings`
that bypass `from_env` still cannot export a denied schema). `TestBackupIdValidation` (F10: 18 rejected
forms including traversal, slash, backslash, absolute path, whitespace, newline, NUL, leading `-`/`_`,
empty, over-length and dotted; 5 accepted forms; non-string rejected; the service rejects a hostile id
before any database work; a valid id is accepted and produces no path characters). `TestDigestSemantics`
(F11: an ETag-only provider never false-trips and the object is retained; a provider-declared SHA-256
mismatch discards the published object and raises; a bad read-back discards and raises; read-back happens
by default; read-back can be disabled explicitly; the default is `True`; a failing discard still surfaces
the integrity error rather than masking it).

**`backend/tests/unit/backup/test_service.py` — `TestPhase11CatalogCapture` (7 new tests).** Partition
parent exported and leaves absent; partition metadata and counts; no data member for leaves (rows exported
once); identity, generated, collation and column comment; table comment and UNLOGGED persistence; sequence
ownership; DDL rendering of identity, generated, collation, comments, `OWNED BY` and partition metadata.

**`backend/tests/integration/backup/test_exporter_local.py` — `TestPhase11Capture` (6 new tests)** against a
real loopback disposable PostgreSQL, including a genuinely partitioned table (`events` + `events_a/b/c`,
4 rows): partition parent exported once with **every per-table count compared to a database oracle built
from `pg_class`/`count(*)`** and no double counting; partition metadata authoritative in `catalog.json`;
identity, generated, collation and comments; UNLOGGED persistence; sequence ownership kept distinct from
state (including an identity sequence's internal dependency); credential-schema deny-list enforced on a real
database using a synthetic non-credential scaffold.

## 4. Commands executed

```
git rev-parse HEAD ; git branch --show-current ; git status --porcelain=v1           # before and after
python -m py_compile backup/*.py ; python -c "import backup"
python -m pytest tests/unit/backup -q
python -m pytest tests/integration/backup -q
python -m pytest tests/unit/backup tests/integration/backup -q                      # combined
python -m pytest tests/unit -q                                                      # full regression
python -m pytest tests/unit/backup tests/integration/backup --collect-only -q        # exact counts
psql -h 127.0.0.1 -p 54426 -tAc "select count(*) from pg_database where datname like 'ct_backup_it_%'"
```

## 5. Test results (exact)

| Suite | Collected / Result |
|---|---|
| `tests/unit/backup` | **107 passed**, 0 failed, 0 skipped, 0 errors |
| `tests/integration/backup` | **9 passed**, 0 failed, 0 skipped, 0 errors |
| Backup suite total | **116 passed** |
| Full `tests/unit` regression | **1,761 passed**, 0 failed, 0 skipped, 0 errors (1,709 pre-existing + 52 new) |
| Disposable databases left behind | **0** |

Breakdown of the unit backup suite by file: `test_artifact.py` 15 · `test_crypto.py` 16 ·
`test_service.py` 18 (11 original + 7 new) · `test_storage_and_settings.py` 13 ·
`test_p1_1_remediation.py` 45.


## 6. Findings, decisions and risks

**Findings remediated (F1–F12)** — as recorded in the finding matrix of the final report. Every remediation
is backed by a test and a documentation change. The two defects found during this operation itself were both
stale **test expectations** (an added sequence changing index 0; `format('%I.%I')` correctly quoting only
what needs quoting) — neither was an implementation defect, and both were corrected in the tests rather than
by changing behaviour.

**Decisions taken (all inside the authorised scope).**

1. **F1 policy:** export the partitioned **parent** once and exclude leaves via `NOT relispartition`, applied
   identically to tables, columns, constraints and indexes so the exported table set stays self-consistent.
   Chosen because the parent's COPY already returns every partition row, so leaf export duplicates data.
2. **F2 shape:** a deny-list constant plus a required exact override phrase, enforced at **two** layers
   (settings and exporter) so a direct exporter caller also fails closed, with the guard running before the
   snapshot opens.
3. **F4 representation:** `default_expression` is `None` for generated columns and the expression moves to
   `generation_expression`, making "ordinary default" and "generated" structurally distinguishable.
4. **F5 reporting:** the default collation is reported as `None` (no misleading metadata); a real non-default
   collation is reported fully qualified.
5. **F6 scope:** temporary objects are excluded explicitly (`relpersistence <> 't'`) rather than relying on
   the schema filter.
6. **F7 dependency types:** both `'a'` (serial ownership) and `'i'` (identity) `pg_depend` types are read in a
   `LIMIT 1` correlated subquery, so a sequence yields exactly one row.
7. **F11 verification:** the authoritative check is an **application read-back** (provider-independent,
   default on), with a provider-declared SHA-256 honoured only when offered; a native ETag/MD5 is recorded
   but never compared to SHA-256. On failure the object is discarded best-effort and a typed error is raised.
8. **`catalog.json` remains authoritative** (`ddl.sql` informational) — all new metadata was added to the
   structured catalog, not only to the DDL.

**Risks / trade-offs.**

* Read-back verification adds one storage read per backup (default on; can be disabled deliberately). For a
  large off-site artifact this is a bandwidth cost, accepted in exchange for provider-independent integrity.
* If the object store cannot delete, a failed artifact can be orphaned; the code logs that clearly and still
  returns a typed failure, and never reports success. Retention/scheduling must handle such orphans later.
* The deny-list is static: a future provider-private schema not on it would not be blocked automatically. It
  is deliberately narrow, and the default remains `public` only.
* `owned_by`, `collation`, `identity_kind`, `generated_kind`, `persistence`, `comment` and `partitions` are
  captured as **metadata only** — nothing in this phase consumes them, because there is no restore.
* Partition metadata is captured, but partition **data** exists only in the parent's payload; a restore
  implementation must recreate the parent and its partitions before loading.


## 7. Unresolved issues / explicitly deferred

* **Restore (D4)** — still unimplemented; no endpoints, CLI, jobs or drill were added. `DR-20` therefore
  remains **NOT SATISFIED** and migrations 22 → 53 remain **UNAUTHORISED**.
* Comments on objects other than tables and columns (constraints, indexes, functions) are not captured —
  documented as limitation 12 rather than silently omitted.
* Column storage/compression attributes are not captured — documented with the same limitation.
* **Remaining production prerequisites (unchanged):** the `ct_backup` role, the off-site private destination
  and its provider implementation, encryption-key custody/rotation, Storage-object backup, and the restore
  implementation plus drill.
* `DR-16`, `DR-19`, P6-2F, Phase 7, Phase 8, `/demo`, `/investors`, billing, E2E infrastructure and all
  migrations were **not** touched.

## 8. Security verification

* No secrets, keys, tokens or production URLs were added to any file.
* No real credential material appears anywhere: the F2 fixtures use a synthetic, clearly labelled
  non-credential scaffold (`auth.scaffold_credentials.synthetic_credential_column` =
  `'SYNTHETIC-NOT-A-CREDENTIAL'`).
* Encryption remains mandatory (the service still refuses without `CT_BACKUP_ENCRYPTION_KEY`) and the
  AEAD tag / associated-data behaviour is unchanged.
* The storage boundary still receives **ciphertext only**; staging directories remain `0700` and are removed
  on every exit path.
* Path traversal is now rejected at the backup layer (`BackupValidationError`) in addition to the provider's
  own key-escape refusal.
* No cloud SDK, `subprocess`, `pg_dump`, Docker or CLI dependency was introduced — no new dependency at all.
* Database-backed tests used **loopback, uniquely named, disposable** databases only, and **zero** were left
  behind.

## 9. Change boundary

**Before:** HEAD `daad396523ac693352cc2f4ebb7fc58814a9e60b`, branch `main`, staged `0`, 452
changed/untracked entries in an already-dirty tree (`backend/backup/`, the two backup test directories and
four backup documents present as untracked; `backend/requirements.txt` the only modified file under
`backend/`).

**After:** HEAD **unchanged**, staged **0**, nothing committed, pushed or deployed; no unrelated
working-tree change was altered or cleaned. Changes attributable to this operation:

* **Modified (11):** `backend/backup/{settings,errors,artifact,catalog,exporter,storage,service,__init__}.py`,
  `backend/tests/unit/backup/test_service.py`,
  `backend/tests/integration/backup/test_exporter_local.py`,
  `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md`.
* **Added (2):** `backend/tests/unit/backup/test_p1_1_remediation.py`,
  `docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001.md`.
* **Unchanged by this operation:** `backend/requirements.txt`, all migrations, E2E infrastructure, billing
  and every other application file.

## 10. Final status and stop-condition confirmation

**Final status:** `P1.1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

All twelve findings are remediated with tests and documentation; the required suites were run and reported
with exact counts; only files inside the authorised boundary were changed.

**No stop condition was triggered.** No production connection, credential, SQL, role, object or data was
required; no migration was changed or executed; restore remains unimplemented; no architecture change or new
dependency was needed; no critical regression appeared (1,761 unit tests pass, 0 failures); no ambiguity
required a new PO decision. The operation **stopped** as instructed — no commit, no push, no deploy, no
production contact — and the next step is a separate independent verification of Phase 1.1.

## 11. Mandated no-change-to-production confirmation

```text
Production database contacted: NO
Production database altered: NO
Production migrations applied: NO
Production data created: NO
Production roles created: NO
Production RLS modified: NO
Production Auth modified: NO
Production storage modified: NO
Production backup created: NO
Production restore performed: NO
Production deployment performed: NO
Git commit created: NO
Git push performed: NO
```

