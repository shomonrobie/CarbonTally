# CarbonTally — Production Backup Implementation, Phase 1 (+ Phase 1.1 remediation)

**Prompt Refs:** `CT-PROD-BACKUP-IMPLEMENTATION-20260911-001` · `CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001`
**Date:** 2026-09-11
**Mode:** BOUNDED IMPLEMENTATION + LOCAL/DISPOSABLE VERIFICATION (PO authorization explicitly granted)
**Repository:** CarbonTally · branch `main` · **HEAD / Release-1:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged)
**Ratified architecture:** `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` **Part 2** (D1–D5) — **not modified by this work**
**Independent verification of Phase 1:** `docs/cline/prompt-history/CT-PROD-BACKUP-IV-20260911-001.md` (verdict: PASS WITH NON-BLOCKING FINDINGS)

> **Scope honesty:** this is the **export foundation only**. Restore (D4), scheduling, the admin UI, retention
> automation, Storage-object backup and every production provisioning step remain **unimplemented and
> unauthorised**. Nothing in production was contacted, read, dumped, altered or provisioned.
> **There is no restore capability, no PITR claim and no production recovery claim anywhere in this design.**

---

## 0. Phase 1.1 remediation summary (findings F1–F12)

Phase 1.1 is a bounded remediation of the independent verification findings. It changes capture and
validation behaviour only — it does **not** redesign the architecture, add a provider, add a framework, or
implement restore.

| Finding | Remediation |
|---|---|
| **F1** partitions exported twice | Partition **leaves are excluded** (`NOT relispartition`); the **parent** is exported once and its COPY carries every partition row. Applied to tables, columns, constraints and indexes so the exported table set is self-consistent. Row counts now match a database oracle exactly. |
| **F2** `auth` credential capture | A **fail-closed schema deny-list** (`auth`, `storage`, `vault`, `realtime`, `supabase_functions`, `supabase_migrations`, `pgbouncer`) enforced at **both** the settings and exporter layers; the only way through is the explicit administrative override `CT_BACKUP_DENIED_SCHEMA_OVERRIDE=I_UNDERSTAND_THIS_EXPORTS_CREDENTIAL_MATERIAL`. Encryption is **not** treated as the boundary. |
| **F3** identity columns | `identity_kind` captured (`ALWAYS` / `BY DEFAULT` / `None`) and rendered as `GENERATED … AS IDENTITY` in `ddl.sql`. |
| **F4** generated columns | `generated_kind = "STORED"` plus a separate `generation_expression`; `default_expression` is `None` for generated columns, so they can never be mistaken for an ordinary default. |
| **F5** collation | Non-default column collation captured as a qualified name (e.g. `pg_catalog."C"`); the default collation is reported as `None` rather than as noise. |
| **F6** UNLOGGED state | `persistence` captured (`p` / `u`); `ddl.sql` emits `CREATE UNLOGGED TABLE`. Session-temporary objects are never captured (`relpersistence <> 't'`). |
| **F7** sequence ownership | `owned_by` captured via `pg_depend` (deptype `a` and `i`, so identity sequences included), kept **separate** from sequence current state (OID-2). |
| **F8** partition metadata | New authoritative `partitions` section: parent, `pg_get_partkeydef` key, every leaf and its `relpartbound` bounds. |
| **F9** comments | Table comments (`obj_description`) and column comments (`col_description`) captured in the structured catalog and rendered as `COMMENT ON …` in `ddl.sql`. |
| **F10** `backup_id` validation | Strict allow-list `^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$` (no dots, separators, absolute paths, whitespace or control characters) validated in the service **before** any work, raising the new typed `BackupValidationError`. **N1 remediation (2026-09-11):** only `None` means "not supplied"; an explicitly supplied **empty string** now reaches the validator and is rejected (it was previously treated as omitted and silently replaced by a generated id). |
| **F11** digest semantics | `StoredObject` now separates `content_sha256` (application SHA-256 — populated only when the provider guarantees it) from `provider_checksum`/`provider_checksum_algorithm` (native ETag/MD5, **never** compared to SHA-256). Publication is verified by provider-declared SHA-256 **and** an application read-back (default on); any mismatch **discards** the published object and raises a typed failure, so a failed verification can never be reported as a successful backup. |
| **F12** documentation | This document and the module docstrings corrected to match measured behaviour; restore remains explicitly unimplemented. |

---

## 1. What was implemented

A secure, testable, production-compatible **logical backup export foundation** that runs on
CarbonTally's existing native Render/Python runtime:

| Component | Purpose |
|---|---|
| `backup.settings` | Environment-driven configuration; refuses to run without an encryption key |
| `backup.catalog` | Read-only PostgreSQL catalog introspection (OID-1) + best-effort DDL rendering |
| `backup.exporter` | Pure-Python logical export: one read-only `REPEATABLE READ` snapshot, `COPY`-streamed data, sequence state (OID-2) |
| `backup.artifact` | Versioned artifact format: deterministic tar/gzip, manifest, content checksums, archive reader/verifier |
| `backup.crypto` | AES-256-GCM authenticated encryption with an authenticated envelope header (D3) |
| `backup.storage` | Provider-neutral `ObjectStore` protocol + local filesystem and in-memory providers (D2/OID-3) |
| `backup.service` | Orchestration: temp dir → export → checksums → manifest → archive → **encrypt** → store → cleanup |
| `backup.errors` | Typed error hierarchy over `core.exceptions.CarbonTallyError` |

**Exact file locations**

```
backend/backup/__init__.py        public surface
backend/backup/errors.py          typed errors
backend/backup/settings.py        env config + key validation
backend/backup/catalog.py         catalog SQL + CatalogSnapshot + DDL rendering
backend/backup/exporter.py        snapshot export + COPY streaming + member collection
backend/backup/artifact.py        format constants, manifest, tar/gzip, checksums, archive reader
backend/backup/crypto.py          AES-256-GCM envelope (encrypt/decrypt/metadata)
backend/backup/storage.py         ObjectStore protocol + local + in-memory providers
backend/backup/service.py         BackupService orchestration + BackupRecord

backend/tests/unit/backup/test_artifact.py            artifact/format/checksum/archive
backend/tests/unit/backup/test_crypto.py              encryption, wrong key, tampering
backend/tests/unit/backup/test_storage_and_settings.py config + object-store providers
backend/tests/unit/backup/test_service.py             orchestration with a fake asyncpg connection
backend/tests/integration/backup/test_exporter_local.py  real local disposable PostgreSQL
```

**No new dependency was required** — `asyncpg 0.30.0` (COPY), `cryptography` (AES-256-GCM) and the standard
library (`tarfile`, `gzip`, `hashlib`, `json`) cover everything. **One declaration was added**:
`cryptography>=41.0.0` is now listed in `backend/requirements.txt` (it was previously present only
transitively) with an explanatory comment — a one-line change resolving OID-4 so a production install
cannot lose AES-GCM support silently.

---

## 2. Backup artifact format (versioned)

`BACKUP_FORMAT_NAME = "carbontally-logical-backup"`, `BACKUP_FORMAT_VERSION = 1`,
`EXPORTER_VERSION = "0.1.0"` (`backup/artifact.py`). The version travels **inside** the artifact
(`manifest.json → backup_format`) so any future release can decide compatibility.

> **Phase 1.1 note:** the format version stays `1`. Phase 1.1 only *adds* keys to the structured catalog
> (`identity_kind`, `generated_kind`, `generation_expression`, `collation`, `persistence`, `comment`,
> `owned_by`, `partitions`, table `relkind`/`is_partitioned`), which is additive and therefore
> backwards-compatible for a v1 consumer; no structural change was made to the envelope, the archive layout
> or the existing member names.

Archive members:

| Member | Content |
|---|---|
| `manifest.json` | format/version, `backup_id`, `created_at`, exporter version, safe database identity, inventory, counts, compression + encryption metadata, integrity semantics, limitations |
| `catalog/catalog.json` | structured catalog extraction (schemas, tables, columns, constraints, indexes, sequences, functions, triggers, policies, views, extensions, safe role metadata) — **authoritative** |
| `catalog/ddl.sql` | best-effort DDL reconstruction — **informational only** |
| `catalog/sequences.json` | sequence definitions **and current state** (`last_value`, `is_called`) — OID-2 |
| `data/<schema>__<table>.copy` | PostgreSQL `COPY … TO STDOUT` **text** payload, one file per base table |
| `integrity/checksums.sha256` | `"<sha256>  <member path>"` lines, sorted |

Determinism: tar member metadata is normalised (`mtime=0`, `uid/gid=0`, empty `uname/gname`, mode
`0o600`), members are stored in **sorted path order**, gzip is written with `mtime=0`, and the manifest is
serialised with sorted keys. Two exports of identical content therefore produce a **byte-identical
archive** (proven by `test_artifact_is_deterministic_for_a_fixed_identity`).

The delivered object is the **encrypted** envelope only:
`backups/<backup_id>/carbontally-logical-backup-v1.tar.gz.enc`.

**What is deliberately *not* claimed:** `catalog/ddl.sql` is *not* asserted to be a restorable dump. The
manifest records this in its `limitations` list.

---

## 3. Encryption design (D3)

* **Algorithm:** AES-256-GCM (`cryptography`), key = 32 bytes from `CT_BACKUP_ENCRYPTION_KEY` (base64).
* **Envelope:** `b"CTBKP1\n"` + JSON header (`v`, `alg`, `key_id`, base64 `nonce`) + `\n` +
  ciphertext‖tag. **The header bytes are GCM associated data**, so version/algorithm/key-id/nonce
  tampering fails authentication.
* **Nonce:** 96-bit random per artifact (never reused).
* **Key rules enforced by construction:** the key is required before any work starts; it is never
  hard-coded, never logged (`BackupSettings.__repr__` masks it), never written into the artifact,
  manifest or object metadata, and never returned to a caller — only the **key id** is recorded.
* **Rotation readiness:** the manifest and envelope carry `key_id`, so a future implementation can select
  the correct key per artifact; rotation itself is not implemented here.

**Checksum semantics (three distinct, documented values):**

| Value | Meaning | Where |
|---|---|---|
| content checksums | SHA-256 per member over **plaintext** member bytes | `integrity/checksums.sha256` (inside the archive), verified by `verify_content_checksums` |
| `archive_sha256` | SHA-256 of the **compressed plaintext archive** (immediately before encryption) | `BackupRecord.archive_sha256`; semantics recorded in the manifest |
| `ciphertext_sha256` | SHA-256 of the **stored encrypted envelope** | `BackupRecord.ciphertext_sha256` + object metadata; re-verified against the provider's own reported digest after upload |

---

## 4. Snapshot / consistency strategy

* The whole export runs inside **one read-only `REPEATABLE READ` transaction**
  (`connection.transaction(isolation="repeatable_read", readonly=True)`), so every catalog query and every
  `COPY` observes a single consistent snapshot.
* **Failure behaviour:** any failure (connection, transaction, catalog, COPY, or staged-file write) is
  normalised to `BackupExportError`; the service removes its temporary directory in `finally` and
  **nothing is published**. A partial artifact cannot exist, so it cannot be mistaken for a valid backup.
* **Retries are safe:** the export is read-only and idempotent; a retry produces a fresh artifact.
* **Row ordering:** deterministic **when the table has a primary key** (`ORDER BY` the key columns) and
  unspecified otherwise — recorded per table as `ordered_by_primary_key` in the manifest.
* **Partitioned tables** are recorded by their parent (`relkind='p'`); partition children are not
  individually recursed (documented limitation).


---

## 5. Object-storage boundary (D2 / OID-3)

`backup.storage` defines a **narrow provider-neutral protocol**:

```python
class ObjectStore(Protocol):
    async def put_object(key, data, *, content_type=..., metadata=None) -> StoredObject
    async def get_object(key) -> bytes
    async def head_object(key) -> StoredObject
    async def list_objects(prefix="") -> list[StoredObject]
    async def delete_object(key) -> None
```

Two providers ship: `LocalFilesystemObjectStore` (root `0o700`, objects `0o600`, atomic publish via
`os.replace`, **key-escape rejection**) and `InMemoryObjectStore` (unit tests). A future off-site provider
(for example S3-compatible) implements the same protocol; **no other module changes**.

**Boundary guarantee:** the service calls `put_object` with the **encrypted envelope only**. Tests assert
the stored bytes start with the envelope magic, contain no plaintext markers and are not the key. No
production bucket, credential or provider was created, selected or contacted, and **no cloud SDK was
added**.

**Checksum semantics across the boundary (Phase 1.1, finding F11).** `StoredObject` deliberately separates
two digests:

* `content_sha256` — the **application SHA-256** of the stored bytes. A provider may populate it only if its
  contract guarantees a SHA-256 (the local and in-memory providers do).
* `provider_checksum` / `provider_checksum_algorithm` — the provider's **native** value (an S3-style ETag, an
  MD5, …). It is recorded and logged but **never** compared against an application SHA-256, so a provider
  that reports ETag/MD5 cannot false-trip the integrity guard.

After publication the service verifies the object: first a provider-declared SHA-256 when one is offered,
then (by default) an **application read-back** that recomputes the SHA-256 of the stored bytes. On any
mismatch it attempts to **discard** the just-published object, logs clearly if that discard fails, and
raises a typed `BackupIntegrityError` — a failed verification is never reported as a successful backup.

---

## 6. Configuration / secrets expected

| Variable | Required | Purpose |
|---|---|---|
| `CT_BACKUP_ENCRYPTION_KEY` | **yes** (else the service refuses to run) | base64 32-byte AES-256 key — supply from Render secret custody |
| `CT_BACKUP_KEY_ID` | no (default `key-v1`) | non-secret key label recorded in the envelope/manifest |
| `CT_BACKUP_OBJECT_STORE` | no (default `local`) | `local` or `memory` — **no production provider exists yet** |
| `CT_BACKUP_LOCAL_ROOT` | no (default `/tmp/ct_backup_store`) | local provider root |
| `CT_BACKUP_TEMP_ROOT` | no | parent for temporary export material |
| `CT_BACKUP_SCHEMAS` | no (default `public`) | schemas to export — **denied schemas are refused** (F2) |
| `CT_BACKUP_DENIED_SCHEMA_OVERRIDE` | no (unset = refused) | must equal exactly `I_UNDERSTAND_THIS_EXPORTS_CREDENTIAL_MATERIAL` to permit a credential-bearing schema (F2) |
| `CT_BACKUP_VERIFY_READBACK` | no (default `1`) | read each stored object back and re-verify the application SHA-256 (F11); `0` disables that deliberate trade-off |
| `CT_BACKUP_COMPRESSION` / `_LEVEL` | no (default `gzip` / `6`) | compression choice |

`backup_id` is **not** configuration: when a caller supplies one it must match
`^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$` (F10), otherwise the operation fails closed with
`BackupValidationError` before any database or storage work. Only `None` means "not
supplied" and receives a generated identifier; an explicitly supplied **empty string**
is supplied-but-invalid and is therefore rejected (N1 remediation).

The database connection uses the **existing** `DATABASE_URL`/`SUPABASE_DB_URL` path via
`infra.supabase.get_service_pool()`. The ratified **D5** intent is a dedicated read-only `ct_backup` role
with `BYPASSRLS` and SELECT-only grants; that role was **not created** (production prerequisite), and the
connection factory is injectable so switching to it later requires no change to the exporter.

---

## 7. Local / disposable verification method

```bash
cd backend
.venv/bin/python -m pytest tests/unit/backup tests/integration/backup -q
```

* **Unit tests need no database** — a fake `asyncpg` connection exercises the whole orchestration path.
* **Integration tests** require a **loopback** PostgreSQL (default
  `postgresql://postgres:postgres@127.0.0.1:54426/postgres`, override with `CT_BACKUP_TEST_DSN`). They
  **skip** if the DSN is not loopback, if the server is unreachable, or if a disposable database cannot be
  created; they create their **own uniquely named database** (`ct_backup_it_<hex>`), never mutate an
  existing database, and drop only that database.
* The integration fixture covers representative PostgreSQL scalars (uuid, text, integer, numeric, boolean,
  timestamptz, date, jsonb, `text[]`, bytea), NULLs, an empty table, a sequence with
  `setval(..., 42, true)`, a function, a trigger, an RLS-enabled table with a policy, a view, check/unique
  constraints, and **quoted mixed-case identifiers**.


---

## 8. Known limitations (Phase 1)

1. **No restore.** The artifact is export-only; no restore code path exists.
2. **Schema reconstruction without `pg_dump`** — `catalog/ddl.sql` is best-effort and *informational*; the
   authoritative record is `catalog/catalog.json`. A restore implementation must consume the structured
   catalog (functions/views/constraints/indexes/triggers/policies are captured verbatim via `pg_get_*`).
3. **Table/column ACLs are not dumped**; role **definitions are metadata only** (never passwords).
4. **Extension internals are not dumped** — names and versions are metadata.
5. **Partitioning is metadata, not duplicated data** — the parent's logical rows are exported once and the
   leaves are **not** exported separately; `catalog.json → partitions` records the key definition, the leaf
   relationships and the bounds. (Phase 1.1 corrected this: previously both the parent and the leaves were
   exported, which double-counted rows.)
6. **Row ordering** is deterministic only for tables with a primary key.
7. **Credential-bearing schemas are refused by default** (Phase 1.1, finding F2): `auth`, `storage`,
   `vault`, `realtime`, `supabase_functions`, `supabase_migrations` and `pgbouncer` are on a **fail-closed**
   deny-list enforced at both the settings and exporter layers. Requesting one raises unless the deliberate
   `CT_BACKUP_DENIED_SCHEMA_OVERRIDE` phrase is supplied; encryption is **not** relied upon as the boundary.
8. **Storage objects are not included** — Supabase documents that database backups contain metadata only,
   so a **separate paired job** is required (architecture §14).
9. **Database size is not measured** (the identity block deliberately omits `pg_database_size`) → cost and
   duration estimation remains `UNKNOWN`.
10. **No scheduling, retention expiry, admin API, admin UI or notification wiring.**
11. **No production object-store provider** — local and in-memory only.
12. **Comments are captured for tables and columns only** — comments on constraints, indexes, functions and
    other objects are not dumped. (Column storage/compression settings are likewise not captured.)
13. **Sequence ownership is metadata only** — `owned_by` is recorded alongside current state, but nothing
    re-attaches a sequence (there is no restore implementation).
14. **`ddl.sql` remains informational.** The authoritative record is `catalog.json`, which now also carries
    `identity_kind`, `generated_kind`, `generation_expression`, `collation`, `persistence`, `comment`,
    `owned_by` and the `partitions` section.
15. **Provider checksum semantics are provider-dependent by design (F11).** Application integrity is
    SHA-256 of the ciphertext; a provider-declared SHA-256 is honoured only when offered, and a native
    ETag/MD5 is recorded but never compared to SHA-256. Read-back verification costs one additional read per
    backup and can be disabled deliberately, but is **on** by default.

*(Defects found and fixed, recorded for transparency: `"char"` catalog columns returning `bytes` broke JSON
serialisation; a closed/failed connection leaked a raw driver exception instead of a typed error; the
independent verification then found partition double-counting, the unenforced `auth` exclusion, six capture
gaps, unvalidated `backup_id` and ambiguous provider-digest semantics — all remediated above and covered by
new tests.)*

## 9. Remaining production prerequisites (not done here)

1. **Create the `ct_backup` role** (`BYPASSRLS` + SELECT-only grants + `default_transaction_read_only = on`)
   — or confirm `BYPASSRLS` cannot be granted and fall back to per-table `FOR SELECT USING (true)` policies
   (`PROPOSED — NOT EXECUTED`; architecture Part 2 §P2.3 / OID-5). **Production SQL — requires separate
   authorization.**
2. **Provision the off-site destination** (private bucket, lifecycle expiry, write-scoped credential) and
   add its provider implementation (OID-3).
3. **Create and custody the encryption key** in a secret store separate from the artifact; document
   rotation and escrow (D3).
4. ~~Declare `cryptography` in `backend/requirements.txt`~~ — **done in this phase** (OID-4 resolved):
   `cryptography>=41.0.0` is declared explicitly.
5. **Storage-object backup** (separate paired job) before real customer documents exist (`DR-08`).
6. **Restore implementation + restore drill** — the `DR-20` evidence requirement is unchanged.

## 10. Explicitly unimplemented (out of scope; unchanged by this phase)

Restore (D4) · production restore · backup scheduling · admin backup UI · backup deletion/retention
automation · Supabase Storage-object backup · `ct_backup` role creation · production object storage ·
migrations 22 → 53 · `DR-16` · `DR-19` · P6-2F remediation · Phase 7 · Phase 8 · `/demo` · `/investors`.

## 11. Relationship to the ratified decisions and to `DR-20`

| Item | Status after Phase 1 |
|---|---|
| **D1** pure-Python `asyncpg` exporter | **Implemented and verified** — no Docker, no CLI, no `pg_dump`, no subprocess; native runtime retained |
| **D2** independent off-site private storage | **Interface implemented**; local/in-memory providers only; production provisioning untouched |
| **D3** application-level encryption before storage | **Implemented and verified** — AES-256-GCM; only ciphertext reaches the storage boundary |
| **D4** restore as a separate high-risk capability | **Not implemented**; no production restore path, and the existing authorization model was **not** broadened |
| **D5** dedicated restricted `ct_backup` role | **Not created**; the exporter supports injecting it (read-only snapshot + injectable connection factory) and the proposed least-privilege shape is documented |
| **`DR-20`** (recovery prerequisite for migrations 22 → 53) | **Partially advanced, NOT satisfied.** The capability now exists to produce an **encrypted, checksummed, off-site** artifact, but `DR-20` also requires a **proven restore into a disposable environment** — which needs the Phase-3 restore implementation. **Migrations 22 → 53 remain unauthorised.** |

## 12. Verification summary

**Phase 1 counts (as independently verified):** `tests/unit/backup` 55 passed; `tests/integration/backup`
3 passed; full backend unit regression 1,709 passed.

**Phase 1.1 counts (as implemented here):**

* `tests/unit/backup` — **107 passed** (the original 55, plus 7 catalog-capture tests and 45 Phase-1.1
  remediation tests covering the deny-list, `backup_id` validation and provider-digest semantics).
* `tests/integration/backup` — **9 passed** against a real **local disposable** PostgreSQL, now including a
  genuinely partitioned table (`events` + three leaves) whose row counts are compared against a database
  oracle, plus identity, generated, collation, UNLOGGED, sequence-ownership, comment and partition-metadata
  assertions and a real-database `auth` deny-list check.
* Backup suite total: **116 passed**.
* Full backend unit regression: recorded in the Phase 1.1 history artifact.

**Phase 1.1 test inventory** — `tests/unit/backup/test_p1_1_remediation.py` (F2, F10, F11),
`TestPhase11CatalogCapture` in `test_service.py` (F1, F3–F9 via the extended fake fixture) and
`TestPhase11Capture` in the integration suite (F1, F3–F9 against real PostgreSQL).

---
* `tests/unit/backup` — **55 passed** (artifact/format/checksums/archive determinism; encryption round-trip,
  wrong key, ciphertext **and** header tamper detection; configuration and provider behaviour; orchestration
  with a fake connection incl. temp cleanup on success/failure and "failed export publishes nothing").
* `tests/integration/backup` — **3 passed** against a real **local disposable** PostgreSQL (catalog +
  representative types + NULL/empty handling + sequence state + function/trigger/policy/view; full
  encrypted end-to-end artifact verified by decrypt → archive → checksums → manifest; broken-connection
  path publishes nothing).
* **Full backend unit regression** — `pytest tests/unit -q` → **1,709 tests collected, exit 0, 100 %
  progress, zero failures, no skips**: the existing suite is unaffected.
* Security scan of the new code: **no** `subprocess`, `pg_dump`, CLI, Docker or `shell=True` usage (the
  words appear only in docstrings asserting their absence); **no** secrets, keys, production URLs or
  credentials; the only integration DSN is loopback with a skip guard.
* No file outside `backend/backup/**`, `backend/tests/{unit,integration}/backup/**` and this phase's
  documentation was modified.

