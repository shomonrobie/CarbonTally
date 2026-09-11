# CarbonTally — Production Backup Phase 1.1 — Independent Verification

**Prompt Ref:** `CT-PROD-BACKUP-P1.1-IV-20260911-001`
**Verification Date:** 2026-09-11
**Implementation under verification:** `CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001`
**Findings source:** `CT-PROD-BACKUP-IV-20260911-001` (F1–F12)
**Decisions baseline:** `CT-PROD-BACKUP-DECISIONS-20260911-002` (D1–D5, ratified)
**Branch / HEAD:** `main` / `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged; Phase 1.1 is working-tree only)
**Verifier:** Cline — independent verification agent (verification-only; no fixes applied)

## VERDICT

## `P1.1 VERIFIED — PASS WITH NON-BLOCKING FINDINGS`

Eleven of the twelve findings are **VERIFIED REMEDIATED** by independent evidence (my own harnesses against
real disposable PostgreSQL, plus source inspection). **F10 is PARTIALLY REMEDIATED**: eighteen of the
nineteen adversarial `backup_id` forms listed in the verification brief are rejected at both the validator
and the service, but an explicit **empty string** is silently replaced by a generated UUID instead of
failing closed. That is a **security-neutral** protocol inconsistency (the substituted identifier is
`s uuid4().hex`, so no unsafe storage key can result) and is reported as new finding **N1 / P3**. No
blocking regression was found: every previously verified artifact, crypto, failure-safety, snapshot and
concurrency property still holds.

---

## 1. Verification scope and methodology

**Objective:** independently determine whether F1–F12 were actually remediated, without trusting the
implementation report or reusing the implementation agent's tests as the primary evidence.

**Method (independent evidence, not the author's tests):**

1. **Source inspection** of every Phase-1.1 change: the shared `_exportable_table_filter` (applied to the
   tables, columns, constraints **and** indexes queries — aliases `c`/`c`/`c`/`t`), the columns query
   (`attidentity`, `attgenerated`, collation `CASE`, `col_description`), the tables query (`relkind`,
   `is_partitioned`, `relpersistence`, `obj_description`), `_SEQUENCES_SQL` (`pg_depend` ownership,
   deptype `a`/`i`, `LIMIT 1`), `_PARTITIONS_SQL` (`pg_inherits` + `pg_get_partkeydef` + `relpartbound`),
   `_normalize_columns`, `validate_schemas`, `validate_backup_id`, `StoredObject` digest fields,
   `_verify_published`/`_discard_published`, and the service's validation order.
2. **Purpose-built harnesses written by the verifier** (in `/tmp`, never in the repository) that create
   their own disposable loopback databases and exercise the real exporter/service/crypto/storage code:
   `/tmp/p11iv_core.py` (F1, F3–F9, §17 artifact integrity, §17 failure safety, §17 concurrency, §18
   snapshot), `/tmp/p11iv_units.py` (F2, F10, F11 with verifier-authored store doubles),
   `/tmp/p11iv_emptyid.py` (empty-string identifier probe).
3. **Independent oracles** rather than fixture constants: row counts compared against `COUNT(*)` computed
   from `pg_class`/`count(*)`; catalog assertions read from the produced `catalog.json`; the artifact
   decrypted in memory and its tar/gzip/checksum structure inspected directly.
4. **Independent test execution** of the author's suites with my own counting.

**Production-safety posture:** the only database ever used was loopback `127.0.0.1:54426`; every harness
created and dropped a uniquely named `ct_p11iv*`/`ct_p11ivu*` database. No production credential, endpoint
or object was used.

## 2. F1–F12 results (independent evidence)

| Finding | Verdict | Key independent evidence |
|---|---|---|
| **F1** partition double-export | **VERIFIED REMEDIATED** | Disposable DB with `events` (LIST partition, 3 leaves, 6 rows across leaves). Inventory contains `events` (row_count 6) and **no** `events_a/b/c`; no `data/public__events_*.copy` members; exported table set == `Count(*)` oracle exactly; every per-table count == oracle; `total_rows (21) == oracle sum (21)`; the parent payload contains ids `[1,2,3,4,5,6]` **exactly once each**. Source: the identical predicate (`relkind`, `NOT relispartition`, `relpersistence <> 't'`) is applied to the tables, columns, constraints *and* indexes queries |
| **F2** credential-schema capture | **VERIFIED REMEDIATED** | All seven schemas (`auth`, `storage`, `vault`, `realtime`, `supabase_functions`, `supabase_migrations`, `pgbouncer`) refused at settings with the schema named in `details.denied_schemas`; case-insensitive; a wrong override phrase does not unlock; the exact phrase does; the **exporter refuses before touching the database** (proved with a connection double that raises on any call); a **hand-built `BackupSettings(schemas=("auth",))` bypassing `from_env` is still refused by the service** with nothing published; against a real DB the default artifact contains **no** `auth` member and **no** credential marker, while the deliberate override path genuinely exports `auth__scaffold.copy` containing the synthetic marker |
| **F3** identity columns | **VERIFIED REMEDIATED** | `ident_always.id` → `ALWAYS`; `ident_bydefault.id` → `BY DEFAULT`; `no_identity.id` → `None`; DDL contains both `GENERATED ALWAYS AS IDENTITY` and `GENERATED BY DEFAULT AS IDENTITY` |
| **F4** generated columns | **VERIFIED REMEDIATED** | `gen_demo.lower_base`: `generated_kind = "STORED"`, `generation_expression = lower(base)`, `default_expression = None`; sibling `plain_default` keeps `default_expression = "7"` and `generated_kind = None`; DDL renders the generated form and does **not** emit `DEFAULT lower(base)` |
| **F5** collation | **VERIFIED REMEDIATED** | `coll_demo.c` → `pg_catalog."C"`; `coll_demo.d` → `None` (no false explicitness); DDL contains `COLLATE` |
| **F6** UNLOGGED | **VERIFIED REMEDIATED** | `logged_demo.persistence = 'p'`, `unlogged_demo.persistence = 'u'`; DDL emits `CREATE UNLOGGED TABLE IF NOT EXISTS`; a session TEMP table was created and is **absent** from the inventory (and lives only in a `pg_temp*` schema) |
| **F7** sequence ownership | **VERIFIED REMEDIATED** | `serial_demo_id_seq.owned_by = public.serial_demo.id`; `ident_always_id_seq.owned_by = public.ident_always.id` (deptype `i`); `seq_free.owned_by = None`; current state still captured (`seq_free.last_value = 55`, `is_called = true`); the `nextval` column default is unchanged; state and ownership are separate fields |
| **F8** partition metadata | **VERIFIED REMEDIATED** | `catalog.json → partitions` holds 3 rows with `partition_key = "LIST (kind)"`, `parent_qualified_name = public.events` and bounds `FOR VALUES IN ('a'\|'b'\|'c')`; the parent carries `is_partitioned = true`; DDL summarises the partition relationships |
| **F9** comments | **VERIFIED REMEDIATED** | Table comment and column comment both present in `catalog.json` and rendered as `COMMENT ON TABLE`/`COMMENT ON COLUMN` in `ddl.sql` |
| **F10** `backup_id` validation | **PARTIALLY REMEDIATED** | **18 of 19** listed adversarial forms rejected at the validator **and** at the service (traversal, `..`, `.`, `a..b`, `backups/escape`, `backups\escape`, absolute POSIX/Windows paths, `backup id`, tab, newline, NUL, leading/trailing space, 129 chars, `special!@#$%`, unicode `ид`, `id.with.dot`, `%2e%2e`, `a/b/c`); **non-string** values rejected; rejection occurs **before** any database work (exploding connection) and **before** any staging directory is created; valid ids accepted and used verbatim. **However** an explicit **empty string** is silently replaced by a generated UUID rather than failing closed → see **N1** |
| **F11** digest semantics | **VERIFIED REMEDIATED** | A: ETag/MD5-only provider succeeds and the object is retained; **A2**: a deliberately wrong native ETag still succeeds (never compared to SHA-256); B: a correct provider-declared SHA-256 is honoured; C: with no provider SHA-256 the **application read-back** runs and equals the application ciphertext SHA-256; D: a provider-declared mismatch raises `BackupIntegrityError`, the published object is **deleted**, and no orphan remains; E: a corrupt read-back raises and discards; a failing discard still surfaces the integrity failure; read-back can be disabled deliberately; source contains **no** `provider_checksum ==`/`!=` comparison |
| **F12** documentation accuracy | **VERIFIED REMEDIATED** | Every behaviour I measured matches the documentation's §0 remediation table and §8 limitations; static scan finds **no** claim that restore/PITR/production recovery exists or that a production backup was taken, and 7 explicit "not implemented / unimplemented / NOT SATISFIED" statements are present |

**No finding was classified REGRESSED.** §17/§18 properties re-verified below.


## 3. New finding N1 (F10 residual)

**ID:** N1 · **Classification:** P3 (non-blocking; security-neutral) · **Fix owner:** implementation agent
(this verifier must not fix it)

**Description.** `BackupService.create_backup` resolves the identifier as
`resolved_id = validate_backup_id(backup_id) if backup_id else uuid.uuid4().hex`
(`backend/backup/service.py:145`). Because the guard is **truthiness**, an explicitly supplied **empty
string** never reaches `validate_backup_id` — which itself *does* reject `""` — and is instead treated as
"identifier not supplied"; the backup then proceeds and **succeeds**.

**Evidence (independent).**

* `/tmp/p11iv_units.py` — `svc.create_backup(backup_id="")` reached the database (my exploding connection
  fired) instead of raising `BackupValidationError`; every other adversarial form raised as expected.
* `/tmp/p11iv_emptyid.py` — against a real disposable database: `RESULT: backup SUCCEEDED for backup_id=''`,
  generated key `backups/e58726c0f5514db08ad0507f4270cf92/carbontally-logical-backup-v1.tar.gz.enc`,
  id segment matching `^[0-9a-f]{32}$` and containing **no traversal**.
* Source: `artifact.validate_backup_id` documents and enforces "is empty → raise", so the two layers
  disagree about the same value.

**Impact.** **No security impact** — the substituted identifier is `uuid4().hex`, so the storage key is
always a single flat, safe segment with no traversal, separator or attacker influence. The impact is
behavioural: a caller passing an empty value (unset form field, empty CLI argument) receives a *silently
generated* identifier and a successful backup instead of the typed fail-closed error the validator promises,
which can hide caller bugs and defeats the intent of supplying a deterministic id.

**Recommended (for a separately authorised fix, not performed here):** treat only `None` as "not supplied"
(`validate_backup_id(backup_id) if backup_id is not None else uuid.uuid4().hex`) and add a service-level
regression test for `""` — the current tests cover the validator but not this path.

**Not raised:** no P0/P1/P2 issues were found. No path traversal, key injection, plaintext leak,
digest-confusion, RLS/tenant or failure-safety issue was observed.

## 4. Regression re-verification (§17 and §18)

| Property | Result | Evidence |
|---|---|---|
| AES-256-GCM, magic prefix, ciphertext-only boundary | PASS | Spy store: one payload starting `CTBKP1`; decryption reproduces the archive |
| Stored bytes are not plaintext | PASS | Envelope is not a readable gzip stream and contains no fixture markers |
| No key material in the artifact | PASS | Raw key and base64 key both absent from stored bytes |
| Fresh 96-bit nonce | PASS | Two encryptions of identical plaintext differ; header nonce decodes to 12 bytes |
| Authenticated header (AAD) | PASS | Same-length header mutation rejected (`BackupIntegrityError`) |
| Wrong key / ciphertext tamper | PASS | Both rejected |
| SHA-256 consistency | PASS | Decrypted-archive hash == `archive_sha256`; stored hash == `ciphertext_sha256`; per-member checksums verify |
| Deterministic plaintext archive | PASS | Byte-identical archives for a fixed identity; sorted members; normalised tar metadata; gzip `FLG=0`, `MTIME=0` |
| Temp directory permissions | PASS | Staging directory observed at cleanup with mode `0700` |
| Cleanup on success / storage failure / connection failure | PASS | No staging material remains; failure paths publish nothing |
| Missing key fails before DB work | PASS | `BackupConfigurationError` with an exploding connection factory; nothing published |
| Concurrency isolation | PASS | Distinct keys; each artifact carries its own `backup_id` |
| Snapshot consistency | PASS | `repeatable read` + `read only`; concurrent committed row invisible inside, visible outside |
| Catalog + COPY + sequence state in one snapshot | PASS (source) | All three run inside the single read-only `REPEATABLE READ` transaction |

## 5. Regression results (independent execution)

| Suite | Result |
|---|---|
| `tests/unit/backup` | **107 passed**, 0 failed, 0 skipped, 0 errors (15 artifact · 16 crypto · 18 service · 13 storage/settings · 45 P1.1 remediation) |
| `tests/integration/backup` | **9 passed**, 0 failed, 0 skipped, 0 errors |
| Backup total | **116 passed** (matches the implementation's claim) |
| Full `tests/unit` | **1,761 passed**, 0 failed, 0 skipped, 0 errors (matches the implementation's claim) |
| Verifier harness `/tmp/p11iv_core.py` | **7/7 areas PASS** |
| Verifier harness `/tmp/p11iv_units.py` | **F2 PASS · F11 PASS · F10 FAIL** (single empty-string case = N1) |

## 6. Security review (§19)

| Check | Result |
|---|---|
| `subprocess` / `pg_dump` / `pg_restore` / `os.system` / `os.popen` / `shell=True` / `Popen` / docker in Phase-1.1 code | **None** — only docstrings asserting their absence |
| Cloud SDK / `psycopg` / docker imports | **None** |
| Plaintext key storage or key logging | **None**; only the non-secret `key_id` is recorded |
| Password/credential capture | **None**; the only `rolpassword` reference is a comment stating it is never selected |
| Production endpoints or credentials | **None** (`onrender.com`, `supabase.co`, `https://`, `service_role` absent) |
| New routes / restore capability | **None** (no `@router`/`@app`/restore symbols in the package) |
| Path traversal | Rejected at the provider **and** at the backup layer (18/19 forms; residual = N1, security-neutral) |
| Provider checksum confusion | **None** — `provider_checksum` is never compared to SHA-256 |
| New dependencies | **None**; `backend/requirements.txt` untouched by Phase 1.1 |
| New privileged roles | **None** — no `CREATE ROLE`/`GRANT` anywhere in the implementation |

## 7. Git / change boundary

**Before verification:** branch `main`; HEAD `daad396523ac693352cc2f4ebb7fc58814a9e60b`; staged `0`; 453
working-tree entries (pre-existing dirt preserved).

**After verification:** HEAD **unchanged**, staged **0**, no commit, no push, no deploy, no reset, no clean.
**Repository implementation and tests were NOT modified by this verification.** The only files this
verification created are the two durable artifacts in §9.

Backup-related working-tree paths (Phase 1 + 1.1):

```
M  backend/requirements.txt                        (Phase 1: one dependency declaration)
?? backend/backup/                                 (Phase 1 + 1.1 implementation)
?? backend/tests/unit/backup/                      (Phase 1 + Phase 1.1 tests)
?? backend/tests/integration/backup/               (Phase 1 + Phase 1.1 tests)
?? docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md
?? docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md
?? docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md  (this file)
?? docs/cline/prompt-history/CT-PROD-BACKUP-ARCHITECTURE-20260911-001.md
?? docs/cline/prompt-history/CT-PROD-BACKUP-DECISIONS-20260911-002.md
?? docs/cline/prompt-history/CT-PROD-BACKUP-IMPLEMENTATION-20260911-001.md
?? docs/cline/prompt-history/CT-PROD-BACKUP-IV-20260911-001.md
?? docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001.md
?? docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IV-20260911-001.md
```

## 8. DR-20 and migration status

## `DR-20 — NOT SATISFIED`

Phase 1.1 implements no restore capability (verified: no restore code, no routes) and no restore drill was
performed. `DR-20` requires a proven restore into a disposable/recovery environment.

## `MIGRATIONS 22→53 — NOT AUTHORIZED`

Nothing in this verification changes that, and it must not be inferred from this PASS.

## 9. Durable artifacts

* `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md` (this file)
* `docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IV-20260911-001.md` (verification history)

## 10. Verdict and recommended next step

## `P1.1 VERIFIED — PASS WITH NON-BLOCKING FINDINGS`

Eleven findings independently verified as remediated, one (F10) partially remediated with a
security-neutral P3 residual, no blocking regression and no production interaction.

**Recommended next step (separately authorised):** a very small bounded fix for **N1** — treat only `None`
as "not supplied" in `BackupService.create_backup`, add a service-level regression test for the empty
string, and note the nuance in the documentation. No restore work, provisioning or migration work is implied
or authorised by this verification.

## 11. No-change-to-production confirmation

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
Repository implementation modified: NO
Tests modified: NO
Git commit created: NO
Git push performed: NO
```

