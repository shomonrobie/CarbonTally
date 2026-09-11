# CarbonTally — Production Backup P1.1 (N1) — Independent Verification

**Prompt Ref:** `CT-PROD-BACKUP-P1.1-N1-IV-20260911-001`
**Response Ref:** `CT-PROD-BACKUP-P1.1-N1-IV-20260911-001-R1`
**Datetime:** 2026-09-11
**Role:** Independent verification agent (verification-only; no implementation)
**Verifies:** `CT-PROD-BACKUP-P1.1-N1-MINFIX-20260911-001`
**Implementation report:** `docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-N1-IMPLEMENTATION-20260911-001.md`
**Implementation HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged before and after this verification)
**Scope:** N1 only. The complete Phase 1.1 verification (F1–F12) was **not** repeated.
**Final verdict:** **`N1 VERIFIED — PASS`**

---

## 1. Finding under verification

Phase 1.1 independent verification classified one residual item:

> **N1 — P3:** `service.py:145` used a truthiness guard, so an explicit empty string
> bypassed `validate_backup_id()` and was silently replaced with a generated UUID.
> Security-neutral (no traversal was possible) but an Evidence Gap: the validator was
> tested for `""` while the *service path* was not.

The code under test (current, `backend/backup/service.py:144-148`):

```python
# F10 / N1: only ``None`` means "not supplied"; an explicitly supplied value
# (including the empty string) must reach the validator and fail closed.
resolved_id = (
    validate_backup_id(backup_id) if backup_id is not None else uuid.uuid4().hex
)
```

Required contract verified here: `None` → generated id; `""` → supplied → validated → **rejected**;
valid id → works unchanged; other invalid ids → fail closed.

## 2. Independent instruments (fresh context)

| Instrument | Location | Nature |
|---|---|---|
| Independent harness | `/tmp/n1iv_harness.py` | Written for this verification. Own doubles, own fixture SQL, own oracles. Does **not** import or depend on the repository's test helpers or assertions. |
| Harness output | `/tmp/n1iv_harness_out2.txt` | Full evidence transcript (108 checks). |
| Regression runs | `/tmp/n1iv_s1.txt` (unit/backup), `/tmp/n1iv_s2.txt` (focused N1), `/tmp/n1iv_s3.txt` (integration/backup) | Raw pytest output incl. exit codes. |
| Immutability baseline | `/tmp/n1iv_state.txt` | SHA-256 of the N1 artifacts captured **before** verification. |

Harness design (independent of the repo's tests):

* **`ExplodingConnection`** — any attribute access raises `AssertionError("DATABASE WORK ATTEMPTED …")`,
  so "before database work" is demonstrated by construction, not merely asserted.
* **`CountingFactory`** — records every connection acquisition; the service receives it as
  `connection_factory`, so acquisition can be counted exactly.
* **`RecordingStore`** — records `put/get/head/list/delete`; **each call raises**, so any storage
  interaction during a rejection is an explicit harness failure rather than a silent pass.
* **Validator spy** — `backup.service.validate_backup_id` is replaced by a wrapper that delegates to the
  *real* `backup.artifact.validate_backup_id` and records every invocation. This proves which values reach
  the existing validator, and lets the service's error be compared byte-for-byte with the validator's own.
* **Oracle for the empty string** — the same value is passed to the validator directly and its message,
  `code` and `http_status` are compared against what the service raised.
* **Staging oracle** — a fresh `CT_BACKUP_TEMP_ROOT` per case; the directory listing must be empty both
  before and after, i.e. no staging material may be created at all.
* **Real-database part** — a **new** disposable database `ct_backup_n1iv_<hex>` on
  `127.0.0.1:54426` (loopback guard enforced; refused otherwise), with the harness's own fixture
  (`public.n1iv_items`, 2 rows, one sequence), real `LocalFilesystemObjectStore`, real AES-GCM service
  path, then dropped in `finally`.

## 3. Exact results — Part 1: no database at all (91 checks)

Thirteen supplied values × seven checks each:

| Value | Kind | Result |
|---|---|---|
| `""` | **the N1 case** | rejected |
| `"../escape-attempt"` | traversal | rejected |
| `"a/b"` | separator | rejected |
| `"id with space"` | whitespace | rejected |
| `"x" * 129` | over-length | rejected |
| `".hidden"` | leading dot | rejected |
| `" "` | whitespace-only | rejected |
| `"-leading-dash"` | invalid first character | rejected |
| `".."` | dot-dot | rejected |
| `0` | falsy but not `None` | rejected |
| `False` | falsy but not `None` | rejected |
| `[]` | falsy but not `None` | rejected |
| `b""` | falsy but not `None` | rejected |

Seven checks per value — all **PASS** for all thirteen:

1. rejected with `BackupValidationError`;
2. `code == BACKUP_VALIDATION_ERROR` and `http_status == 400`, equal to the validator's own values;
3. exception message **identical** to the direct validator failure;
4. the existing validator was invoked **exactly once, with that value** (spy evidence);
5. **zero** connections acquired (no database work at all);
6. **zero** storage interaction of any kind (`put/get/head/list/delete` all zero);
7. **no** staging material created (temp root empty before and after).

The four falsy-but-not-`None` values are the direct evidence that no truthiness shortcut remains: every
one of them now reaches the validator and fails closed.

## 4. Exact results — Part 2: real disposable local PostgreSQL (16 checks)

| Check | Result | Evidence |
|---|---|---|
| `None`: backup completed and returned a record | PASS | — |
| `None`: identifier is 32 lowercase hex characters | PASS | `id=9e92fdeb19a445da9c7e16abd573750e` |
| `None`: generated identifier passes the existing validator unchanged | PASS | `validate_backup_id(id) == id` |
| `None`: generated identifier is the one actually used for the artifact | PASS | `backups/9e92fdeb…/carbontally-logical-backup-v1.tar.gz.enc` |
| `None`: exactly one object published, matching the returned record | PASS | 1 published key |
| `None`: validator **not** invoked (an omitted id needs no validation) | PASS | `spy=[]` |
| `None`: successive omitted-id backups generate distinct identifiers | PASS | `9e92fdeb…` vs `34384d74…` |
| valid id `p11-iv-valid-01`: completed, used verbatim in the object key | PASS | `backups/p11-iv-valid-01/…` |
| valid id: a distinct artifact was published | PASS | 3 published keys |
| valid id: validator invoked exactly once with the supplied id (**positive control**) | PASS | `spy=[('p11-iv-valid-01', 'p11-iv-valid-01')]` |
| published artifacts are ciphertext (no plaintext table/data markers) | PASS | sizes `[2614, 2614, 2600]` |
| published bytes match the store's reported content SHA-256 | PASS | digests equal |
| real-DB context `backup_id=""`: rejected with `BackupValidationError` | PASS | — |
| real-DB context `backup_id=""`: **zero** connections acquired | PASS | `factory calls=0 db attempts=[]` |
| real-DB context `backup_id=""`: no extra artifact published | PASS | before = after = 3 |
| real-DB context `backup_id=""`: no staging material left behind | PASS | staging `[]` |

## 5. Exact results — Part 3 and harness total

* Part 3: **no disposable verification database left behind** — PASS (`ct_backup_n1iv_%` count = 0).
* **Harness total: 108/108 checks passed, 0 failed, harness exit code 0.**

### Harness self-correction (disclosed)

The first harness run reported **105/106**, failing one check because *the harness assertion was wrong*:
it asserted that `None` would invoke the validator (`len(SPY) == 1 and SPY[0][0] is None`). The correct
contract is that an omitted id needs **no** validation — the observed `spy=[]` was the implementation
being right and the check being wrong. The check was corrected to assert exactly that, and a **positive
control** was added (the valid-id case must show `spy` recording one call with that id) so that the `None`
observation is a proven absence rather than a broken spy. No implementation code was touched. This is
recorded because an overstated failure would otherwise be indistinguishable from a real defect.

## 6. Regression (required scope only)

The repository's own suites were run in this session, in addition to the independent harness:

| Suite | Command | Result | Exit |
|---|---|---|---|
| Focused N1 tests | `pytest tests/unit/backup/test_p1_1_remediation.py -q -k 'empty_string or omitted'` | **2 passed**, 0 failed, 0 errors, 0 skipped | 0 |
| Backup unit suite | `pytest tests/unit/backup -q` | **109 passed**, 0 failed, 0 errors, 0 skipped | 0 |
| Backup integration suite | `pytest tests/integration/backup -q` | **9 passed**, 0 failed, 0 errors, 0 skipped | 0 |

Counts were derived by parsing the raw pytest progress lines (`/tmp/n1iv_s1.txt`, `/tmp/n1iv_s2.txt`,
`/tmp/n1iv_s3.txt`), because this repository sets `addopts = "-q"` in `pyproject.toml`, which suppresses
the terminal summary line that would normally carry the "N passed" text. Raw output and exit codes are
preserved as evidence.

Backup total: **118 passed** (109 unit + 9 integration), matching the implementation report.
Not run, per the bounded scope: full `tests/unit`, End-to-end suites, and any unrelated roadmap work.

## 7. Production-safety confirmation

| Item | Status | Evidence |
|---|---|---|
| Production database contacted | **NO** | Harness enforces a loopback-only guard and refuses a non-loopback DSN; all connections were `127.0.0.1:54426`, to its own disposable database. |
| Production credentials used | **NO** | No variable whose **name** contains `supabase`/`render`/`backup` exists; `SUPABASE_*` / `RENDER_*` name count = 0; no `CT_BACKUP_ENCRYPTION_KEY` is set (the only substring match anywhere was a GPU device path inside an unrelated session variable's value). The harness generated its own ephemeral AES-256 key in-process. |
| Production storage touched | **NO** | Only a fresh temporary local store root per case; no provider client constructed or used. |
| Production backup created | **NO** | All artifacts were three ~2.6 KB files in a temporary local directory; no production artifact exists. |
| Migration applied | **NO** | `git status -- supabase/migrations/` → 0 entries; all DDL was confined to the harness's own disposable database, which was dropped. |
| Deployment / push / commit | **NO** | HEAD unchanged; staged changes 0; no remote interaction. |
| Disposable resources cleaned up | **YES** | `ct_backup_n1iv_%` = 0; `ct_backup%` (including the integration suite's `ct_backup_it_%`) = 0. |
| Network egress to production | **NO** | The harness uses `asyncpg` (loopback) and the local filesystem only; it performs no HTTP request and constructs no remote storage client. |

## 8. Was the repository implementation modified by this verification?

**No.** SHA-256 of the N1 artifacts was captured before verification and re-checked afterwards — both reads
are byte-identical:

| File | SHA-256 (before == after) |
|---|---|
| `backend/backup/service.py` | `dac88f7409d45b450431f5801e50ec5d7b6be11a9b5784fb643d14014ca629dc` |
| `backend/tests/unit/backup/test_p1_1_remediation.py` | `3bcfdaadf25c6da738c90ef53d3b6ffbd5c4a019684842d31fdbed68ca852b8d` |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md` | `5fec4a0eb45ea7cda343f0edeaaccf6701faa3d59eb5869d15ac1cea550532b7` |

No implementation file, test file or migration was created, edited or deleted. Only two new documents were
written (this report and its prompt-history record). HEAD remains
`daad396523ac693352cc2f4ebb7fc58814a9e60b`; nothing is staged; no commit, push or deployment occurred.
The verification instrument (`/tmp/n1iv_harness.py`) lives outside the repository by design, so it cannot
influence the artefact under test.

## 9. Classification of N1

| Attribute | Assessment |
|---|---|
| Original severity | **P3** (low) |
| Original class | Evidence Gap / validation-consistency — *not* an exploitable vulnerability |
| Exploitability before the fix | **None demonstrated.** An empty string cannot produce traversal, a separator or an absolute path; the pre-fix behaviour silently *substituted* a generated id rather than using an unsafe one. |
| Post-fix status | **CLOSED — REMEDIATED AND INDEPENDENTLY VERIFIED** |
| Post-fix security posture | Unchanged-or-better: every non-`None` value, including `""` and every other falsy type, now reaches the existing fail-closed allow-list before any database, staging or storage work. |
| Residual risk | **None identified within N1's scope.** The generated-id path is intact for omitted ids. |
| Residual workflow note | Raising instead of substituting is a deliberate fail-closed contract change; only test call sites call `create_backup`, so no Phase 1 caller is affected. |

## 10. Limitations, and what was *not* verified

* Only the Phase 1 `BackupService.create_backup` entry point was exercised. No other call path into the
  backup package exists in Phase 1 (no API route, scheduler or worker), so the guarantee extends exactly as
  far as that single entry point — which is what N1 was about.
* The verification exercised the encrypted-artifact path end-to-end against a real database, but did not
  re-run the full Phase 1.1 finding set (F1–F12); those remain as previously verified and are unaffected by
  this change.
* No restore, restore drill, production backup, migration, provisioning, DR-16/DR-19, P6-2F, Phase 6,
  Phase 7 or Phase 8 work was performed or assessed.

## 11. Verdict

All required checks passed:

1. `backup_id=None` continues to generate a valid backup id — **PASS** (real database; valid 32-hex id,
   used verbatim for the artifact, distinct across calls, no validation required).
2. `backup_id=""` reaches the existing validator, is rejected with the expected typed error, and touches
   neither the database, nor staging, nor storage — **PASS** (independent spy + oracle, exploding
   connection, recording store, empty temp root; re-confirmed in a full real-database configuration).
3. A representative valid `backup_id` continues to work — **PASS**.
4. A representative invalid non-empty `backup_id` continues to fail closed — **PASS** (plus eight further
   invalid forms and four falsy non-`None` values).
5. Regression: focused N1 = 2 passed; `tests/unit/backup` = 109 passed; `tests/integration/backup` =
   9 passed; all exit code 0 — **PASS**.
6. No production contact, credential, storage, backup, migration or deployment — **PASS**.

> **`N1 VERIFIED — PASS`**

**Production Backup P1.1 N1 is independently verified and ready to be parked. DR-20 remains NOT SATISFIED.
Migrations 22→53 remain NOT AUTHORIZED.**
