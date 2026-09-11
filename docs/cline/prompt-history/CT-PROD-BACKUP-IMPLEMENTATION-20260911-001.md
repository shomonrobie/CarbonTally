# CT-PROD-BACKUP-IMPLEMENTATION-20260911-001

**Prompt Ref:** `CT-PROD-BACKUP-IMPLEMENTATION-20260911-001` · **Datetime:** 2026-09-11
**Response Ref:** `CT-PROD-BACKUP-IMPLEMENTATION-20260911-001-R1`
**Mode:** BOUNDED IMPLEMENTATION + LOCAL/DISPOSABLE VERIFICATION (PO authorization explicitly granted)
**Repository:** CarbonTally · branch `main` · **HEAD / Release-1:** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Documentation artifact:** `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md`
**Status:** implementation complete; `tests/unit/backup` 55 passed; `tests/integration/backup` 3 passed
**Verdict:** `IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT VERIFICATION` (no blocking or non-blocking
findings; see §7 for the recorded limitations and production prerequisites)

---

## 1. Prompt (summary of the authorized scope)

The PO explicitly authorized **Backup Foundation Phase 1**: implement a secure, testable,
production-compatible backup **export** foundation that can later be connected to a private off-site object
store and a separately authorized restore workflow, usable on CarbonTally's existing **native
Render/Python** architecture. Required: domain/module foundation; a pure-Python `asyncpg` logical export
(D1 — no Docker, no CLI, no `pg_dump` subprocess); catalog/schema reconstruction (OID-1); sequence state
(OID-2); a versioned artifact format with manifest/checksums/encryption metadata; compression + safe
temp-file handling (OID-6); application-level authenticated encryption via `cryptography`/AES-GCM (D3/OID-4);
SHA-256 integrity; a narrow object-storage abstraction (D2/OID-3) with local/mock providers; unit and
integration tests on local/disposable infrastructure; documentation; and this durable history. Explicitly
forbidden: contacting or dumping production, creating production credentials/keys/roles/buckets, uploading
artifacts off-site, implementing restore/scheduling/UI/Storage-object backup, executing migrations 22→53,
`DR-16`, `DR-19`, P6-2F, Phase 7/8, `/demo`, `/investors`, deploying, pushing or committing. Stop conditions
included: production credentials/DB access required, a migration change required, `pg_dump`/Docker/subprocess
required, consistency unachievable, encryption unachievable, partial artifacts indistinguishable, an
unrelated architecture change required, a critical regression, or a new PO decision needed.

---

## 2. Files created (plus one minimal edit)

```
backend/backup/__init__.py
backend/backup/errors.py
backend/backup/settings.py
backend/backup/catalog.py
backend/backup/exporter.py
backend/backup/artifact.py
backend/backup/crypto.py
backend/backup/storage.py
backend/backup/service.py

backend/tests/unit/backup/__init__.py
backend/tests/unit/backup/test_artifact.py
backend/tests/unit/backup/test_crypto.py
backend/tests/unit/backup/test_storage_and_settings.py
backend/tests/unit/backup/test_service.py
backend/tests/integration/backup/__init__.py
backend/tests/integration/backup/test_exporter_local.py

docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md
docs/cline/prompt-history/CT-PROD-BACKUP-IMPLEMENTATION-20260911-001.md   (this file)
```

**One existing tracked file was edited (minimal, justified):** `backend/requirements.txt` — added
`cryptography>=41.0.0` with an explanatory comment. `cryptography` was previously available only as a
transitive dependency; D3 encryption must not depend on that (OID-4). Additions only — no existing
line was removed or re-pinned (the sole diff artefact is that the pre-existing final line `pydantic[…]`
lost its missing-at-EOF newline).

Total: **9 modules (2,022 lines)**, **7 test files (1,017 lines)**, **2 documents**, 1 one-line
dependency declaration.


## 3. Files intentionally **not** changed

No migration, no `backend/config.py`, no `backend/main.py` (the worker/API are not wired in Phase 1), no
router, no frontend, no `vercel.json`, no Supabase config, no existing test, and no existing documentation
(the ratified Part 1/Part 2 architecture documents were not modified). No `ct_backup` role or SQL was
created. `backend/requirements.txt` gained **one** declaration (see §2) — nothing else in the repository's
existing tracked files was altered by this phase.

## 4. Commands executed

```
# discovery (read-only)
.venv/bin/python -V ; .venv/bin/python -c "import cryptography, pytest, asyncpg"
grep/ls on backend/{core,infra,data,workers,api}, backend/requirements.txt, pyproject.toml
PGPASSWORD=postgres psql -h 127.0.0.1 -p 54426 -c "select rolcreatedb, rolsuper …"   # local capability check
.venv/bin/python -c "import backup"                                                  # package import check
# verification
.venv/bin/python -m pytest tests/unit/backup tests/integration/backup -q
.venv/bin/python -m pytest tests/unit -q                                             # full unit regression
grep -rniE 'subprocess|pg_dump|docker|shell=True|service_role|password|secret|token|https?://' backend/backup
```

## 5. Tests executed and results

| Suite | Result |
|---|---|
| `tests/unit/backup` | **55 passed**, 0 failed |
| `tests/integration/backup` (real local disposable PostgreSQL) | **3 passed**, 0 failed |
| `tests/unit` (full backend unit regression) | **1,709 collected; run exit 0; 100 % progress; zero failures; no skips** |

Coverage against the required list: artifact versioning ✔ · manifest generation ✔ · checksum
generation/verification ✔ · encryption/decryption round trip ✔ · wrong-key failure ✔ · ciphertext tamper
detection ✔ · compression/decompression round trip (gzip **and** none) ✔ · temp cleanup on success ✔ ·
temp cleanup on failure ✔ · empty table handling ✔ · NULL values ✔ · representative scalar types ✔ ·
sequence capture ✔ · schema/catalog extraction ✔ · deterministic manifest/artifact behaviour ✔ ·
partial/failed export produces no valid artifact ✔ · local disposable DB export end-to-end ✔ · local
object-storage adapter round trip ✔.

## 6. Compliance with the ratified decisions (D1–D5) — independently inspected

| Decision | Evidence (code, not claims) |
|---|---|
| **D1** — pure-Python `asyncpg`, no Docker/CLI/`pg_dump`/subprocess | `backup/exporter.py` uses `connection.copy_from_query`; `backup/catalog.py` uses parameterised catalog SQL; `grep -rniE 'subprocess\|pg_dump\|docker\|shell=True' backend/backup` matches **only docstrings asserting their absence**; production code contains no `subprocess` usage |
| **D2** — abstraction only, no production storage | `backup/storage.py` exposes a `Protocol` plus `LocalFilesystemObjectStore`/`InMemoryObjectStore`; no cloud SDK added; no bucket or credential created |
| **D3** — encryption **before** the storage boundary | `BackupService._publish` builds the archive → `crypto.encrypt(...)` → `store.put_object(envelope)`; unit **and** integration tests assert the stored bytes are an envelope with no plaintext markers and are not the key |
| **D4** — restore stays out of scope | no restore function, module, endpoint or CLI; restore documented as unimplemented; no existing capability or role broadened |
| **D5** — production role not created | no SQL was executed against any server other than the disposable test database; no `CREATE ROLE`/`GRANT`/`REVOKE` appears in the implementation (the proposed SQL exists only in the architecture document, marked `PROPOSED — NOT EXECUTED`) |

## 7. Architectural findings, decisions and risks

**Findings (from discovery):** `asyncpg 0.30.0` is installed and exposes `copy_from_table`/`copy_from_query`;
`cryptography 50.0.0` is present but **undeclared** in `requirements.txt`; the repository has **no**
production `subprocess`/`tempfile` usage (this package introduces the first temp-file handling, guarded);
the existing worker pattern, audit log, notification and admin authorization models are reusable but were
**not** wired in Phase 1; no `boto3`/`botocore` is installed (OID-3 remains open).

**Implementation decisions taken (all within scope):**
1. **Deterministic artifact** — normalised tar metadata, sorted members, `mtime=0` gzip, sorted-key JSON, so
   identical content yields a byte-identical archive (testable and diff-friendly).
2. **Three distinct checksum values** documented rather than one ambiguous "checksum".
3. **Authenticated header** — the envelope header is GCM associated data, so header tampering fails
   authentication instead of silently selecting the wrong key.
4. **Server-side identifier quoting** — identifiers come from `format('%I.%I', …)`; names are never
   hand-quoted, and COPY source queries use only server-produced identifiers plus constraint-parsed key
   columns.
5. **Typed failure normalisation** — every exporter failure becomes `BackupExportError`, so a partial export
   is never mistaken for success.
6. **Injectable connection factory** — lets a future D5 `ct_backup` role be used without touching the
   exporter.
7. **Compression kept inside `artifact.py`** rather than a separate module (a one-function module would add
   surface without cohesion).

**Defects found by testing and fixed (recorded rather than hidden):**
* `"char"` catalog columns (`pg_constraint.contype`, `pg_trigger.tgenabled`) arrive from asyncpg as
  **`bytes`**, breaking JSON serialisation and the primary-key lookup → fixed in `catalog._jsonable`.
* A **closed connection** leaked `asyncpg.InterfaceError` from `connection.transaction(...)` instead of a
  typed error → fixed by wrapping the export in a normalising `try/except` (`exporter.export_schemas`).
* Two **test expectations** were wrong (`format('%I.%I')` quotes an identifier only when needed) →
  corrected, and a mixed-case table added to prove server-side quoting of a name that *does* require it.

**Risks / limitations carried forward:** no restore; `catalog/ddl.sql` is informational only; ACLs, extension
internals and partition children are not captured; row order is deterministic only with a primary key;
database size is not measured; no scheduling/retention/UI; no production object-store provider;
`cryptography` remains an undeclared transitive dependency (OID-4).


## 8. Production prerequisites before this can be used on production

1. Authorize and create the **`ct_backup`** role (or the documented per-table-policy fallback) — production
   SQL, requiring separate authorization.
2. Provision the **off-site destination** and implement its `ObjectStore` provider (OID-3).
3. Create and custody the **encryption key** (separate store; rotation and escrow documented).
4. ~~Declare `cryptography` in `backend/requirements.txt`~~ — **done in this phase** (OID-4 resolved):
   `cryptography>=41.0.0` is declared explicitly.
5. Implement **restore** (D4) and run the restoration drill that `DR-20` requires.
6. Add **Storage-object** backup as a separate paired job before real customer documents exist.

## 9. Stop-condition confirmation

**No stop condition was triggered.** Production credentials were not required; no production database was
contacted, read, dumped or altered; no migration was changed or executed; `pg_dump`/Docker/subprocess were
not required (and are absent); a consistent snapshot was achieved with a read-only `REPEATABLE READ`
transaction; encryption was implemented and verified; partial artifacts are provably unpublishable; no
unrelated architecture change was needed; no critical regression appeared in the unit suite; and no
ambiguity required a new PO decision. The bounded scope was preserved throughout — adjacent issues
(`DR-16`, `DR-19`, `DR-08` object backup, admin-UI wiring) were **recorded, not fixed**.

## 10. Git status / commit / push

* HEAD remains `daad396523ac693352cc2f4ebb7fc58814a9e60b`; **no commit was created and nothing was pushed.**
* The working tree contains **only additions** in this phase's paths
  (`backend/backup/**`, `backend/tests/unit/backup/**`, `backend/tests/integration/backup/**`, `docs/**`).
  No pre-existing tracked file was edited; no unrelated file was touched.
* Remaining unrelated modified/deleted entries in the worktree are **pre-existing** and were not caused or
  altered by this phase.

## 11. Final status and verdict

| Item | Result |
|---|---|
| Scope executed | Backup Foundation **Phase 1** (export + encryption + integrity + storage abstraction + tests + docs) |
| Unit tests (`tests/unit/backup`) | **55 passed / 0 failed** |
| Integration tests (`tests/integration/backup`) | **3 passed / 0 failed** (real local **disposable** PostgreSQL) |
| Full unit regression (`tests/unit`) | **1,709 tests, exit 0, 100 % progress, zero failures, no skips** |
| Security scan of new code | clean — no subprocess/CLI/Docker, no secrets, no production URLs |
| Production contact | **none** |
| Migrations executed | **none** |
| Commit / push / deploy | **none** |

### Verdict

## `IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT VERIFICATION`

The system is **not** thereby production-backup-ready: the subsequent **independent verification** and the
**restore drill** (`DR-20`) are still required, and the production prerequisites in §8 remain outstanding.

See `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md`.

