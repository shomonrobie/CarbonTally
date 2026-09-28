# CT-VERIFY-04 — Independent verification of CT-RELEASE-04 clean-checkout canonical rebuild

**Date:** 2026-09-28
**Task ID:** CT-VERIFY-04-20260928-INDEPENDENT-REBUILD-REPRODUCIBILITY-VERIFICATION
**Verifier role:** INDEPENDENT VERIFIER (did not implement CT-RELEASE-04; no access to, and no
reliance on, the implementer's worktree files, evidence directories, disposable containers or
conclusions)
**Repository verified:** `/home/shomonrobie/ct_93d5cdd`
**Branch verified:** `p8-release-reconciled`
**HEAD verified (exact):** `61cf279dfb41f5da9f9324cf4e75a9397fddc17b`

**VERDICT:** `CT_RELEASE_04_INDEPENDENTLY_VERIFIED_PASS_WITH_LIMITATIONS`

---

## 1. Task and target question

> Can an independent verifier obtain a clean checkout of the CT-RELEASE-04 repository state and,
> without access to the implementer's worktree-only files, reproduce the canonical 92-migration
> schema and the associated D32/F-02 verification properties deterministically?

**Answer: YES**, on the local repository object store, with the bounded limitations in §17.

No production, live, investor-demo or durable database was read or written. No repository change
was made other than this report. Nothing was pushed, rebased, reset, amended or force-pushed.

---

## 2. Repository topology established first

The task desk is the workspace `/home/shomonrobie/carbon_tally`, but the CT-RELEASE-04 change-set
lives in a **different repository**: `/home/shomonrobie/ct_93d5cdd`. This was established, not
assumed:

| Fact | Value |
|---|---|
| Workspace repository | `/home/shomonrobie/carbon_tally`, branch `main`, HEAD `20b7a928bb73fdfacf8271ff537a8fd245f62c79` — **contains no CT-RELEASE-04 commit** (`git cat-file -t 61cf279` → `could not get object info`) |
| Subject repository | `/home/shomonrobie/ct_93d5cdd` — a full clone (own `.git` directory), remotes `github → https://github.com/shomonrobie/CarbonTally.git`, `origin → /tmp/ct_step2` |
| Subject HEAD | `61cf279dfb41f5da9f9324cf4e75a9397fddc17b`, branch `p8-release-reconciled` |
| Implementation report reviewed | `docs/architecture/CT-PO-CARBONTALLY-CT-RELEASE-04-REPORT-20260928.md` (29100 bytes, tracked at HEAD) |

### 2.1 Starting repository state (recorded before any action)

```
$ git status --short --untracked-files=no
 M .gitignore
```

` M .gitignore` is **pre-existing and unrelated** to CT-RELEASE-04 (§15 of the implementation
report). It was deliberately left untouched throughout. Many untracked files also pre-exist
(`.costrict/`, `8`, `=`, `probe_out*.txt`, `docs/architecture/CT-PO-CARBONTALLY-*`, …); none was
removed, added or absorbed.

### 2.2 Commit chain of the change under test

```
61cf279 (HEAD -> p8-release-reconciled) CT-RELEASE-04: record the third rebuild, executed at the final HEAD
00af1a6 CT-RELEASE-04: record the implementation / report SHAs in the report
5a0c5af CT-RELEASE-04: implementation report
c3a8df5 CT-RELEASE-04: commit the canonical-rebuild support set so a clean HEAD rebuilds
b313fc2 CT-IMPLEMENT-03: scope the runner E2E assertions to the schedule under test (N-3)   <- reported starting SHA
```

All five SHAs above resolve to the subjects the implementation report names. `git diff --name-only
c3a8df5..HEAD -- e2e/ supabase/` is **empty**, confirming no post-`c3a8df5` commit touches a path the
rebuild reads (independently re-checked, not taken from the report).

### 2.3 Remote state — the report's commits are unpushed

| Ref | SHA |
|---|---|
| `github/p8-release-reconciled` (remote) | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| local `p8-release-reconciled` | `61cf279dfb41f5da9f9324cf4e75a9397fddc17b` |
| remote tip is an ancestor of local HEAD | YES |
| commits local is ahead of remote | **19** |

`b313fc2`, `c3a8df5`, `5a0c5af`, `00af1a6`, `61cf279` are **all unreachable from the remote tip**.
This is disclosed by the implementation report (§13, "Push to any remote — not performed") and
consequently bounds the meaning of "clean checkout" — see §17.1 and §19.1.

---

## 3. Independence controls applied

| Control | Implementation |
|---|---|
| No implementer environments | Never connected to `ct_rel04a*`, `ct_rel04b*`, `ct_rel04c*`, `/tmp/ct_rel04_clean`, `/tmp/ct_rel04_clean2`, `/tmp/ct_rel04*_evidence`, or any `CT-SCHEMA-01` / `CT-IMPLEMENT-02` / `CT-IMPLEMENT-03` / `CT-VERIFY-03` target |
| No implementer evidence | `/tmp/ct_rel04a*`, `/tmp/ct_rel04b*`, `/tmp/ct_rel04c*` were never opened. Evidence was generated into a fresh tree `/tmp/ct_verify04/` |
| Fresh clone paths | `/tmp/ct_verify04/cleanA`, `/tmp/ct_verify04/cleanB`, `/tmp/ct_verify04/provA` — none of the implementer's clone paths was reused |
| Fresh disposable targets | New prefixes `ct_verify04` and `ct_verify04b`; new volumes; ports `55520` and `55521`. Name-collision pre-checked (no container, volume or env file existed) |
| Fresh fingerprints | Every fingerprint in this report was recomputed with my own tooling (§9, §10); the implementer's numbers were used only as expectations to test |
| Naming discipline | `/tmp/ct_rel04_clean*` was not used at all, so no "unless absolutely unavoidable" exception was needed |

---

## 4. Clean-clone details

Two **independently created** clean clones were made with a real transport (`file://`, `--no-local`,
`--single-branch`), so objects were fetched rather than shared by hardlink:

```bash
git clone --no-local --single-branch --branch p8-release-reconciled \
          file:///home/shomonrobie/ct_93d5cdd /tmp/ct_verify04/cleanA
git clone --no-local --single-branch --branch p8-release-reconciled \
          file:///home/shomonrobie/ct_93d5cdd /tmp/ct_verify04/cleanB
```

| Property | cleanA | cleanB |
|---|---|---|
| `git rev-parse HEAD` | `61cf279dfb41f5da9f9324cf4e75a9397fddc17b` | `61cf279dfb41f5da9f9324cf4e75a9397fddc17b` |
| `git branch --show-current` | `p8-release-reconciled` | `p8-release-reconciled` |
| `git status --short` | **empty (0 lines)** | **empty (0 lines)** |
| `supabase/migrations/*.sql` | 92 | 92 |
| migration-set fingerprint | `36d5d85b…37944` | `36d5d85b…37944` |

### 4.1 Support-set completeness in the clean clone (claimed, then confirmed)

Independently inspected in `cleanA` (not assumed from the report):

| Path | Result |
|---|---|
| `e2e/environment/scripts/canonical_schema_rebuild.sh` | PRESENT |
| `e2e/environment/scripts/apply_migrations.sh` | PRESENT |
| `e2e/environment/scripts/canonical_schema_verify.py` | PRESENT |
| `e2e/environment/scripts/d32_storage_operator.sql` | PRESENT |
| `e2e/environment/scripts/verify_d32_policy_semantics.sql` | PRESENT |
| `e2e/environment/scripts/d32_search_path_regression.sh` | PRESENT |
| `e2e/environment/scripts/fixtures/d32_pre_revision_ct_schema_01.sql` | PRESENT |
| `e2e/environment/supabase/migrations` | PRESENT, `lrwxrwxrwx` → `../../../supabase/migrations` |
| `e2e/environment/supabase/config.toml` | PRESENT |
| `supabase/migrations/20260823000000_d32_private_documents_storage.sql` | PRESENT |

All ten are **tracked at HEAD** (`git cat-file -e HEAD:<path>` succeeds for each). The symlink is
committed with Git mode `120000` (`git ls-tree HEAD e2e/environment/supabase/migrations` →
`120000 blob d66cc4f0f837129edd1a462e9e42994ae0db7e4b`), and resolves to the canonical directory: 92
files through the symlink and 92 files in the canonical directory — identical, by construction.

### 4.2 No machine-specific path dependency

```
$ grep -rn '/home/' e2e/ supabase/migrations/     -> no matches (exit 0, no output)
$ grep -rn 'ct_rel04\|ct_verify0' e2e/            -> no matches
```

`REPO_ROOT` is derived repository-locally in every script that needs it:

* `apply_migrations.sh:52-55` — `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`, `REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"`, `SOURCE_DIR="$REPO_ROOT/supabase/migrations"`
* `canonical_schema_rebuild.sh:51` — `SCRIPT_DIR` from `$0`; every phase file is sourced from `"$SCRIPT_DIR"/…`
* `d32_search_path_regression.sh:47-49` — `SCRIPT_DIR`/`REPO_ROOT` derived the same way
* `canonical_schema_verify.py:42-43` — `REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]`, `MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"`

Confirmed at runtime: PHASE B and PHASE D both printed
`source=/tmp/ct_verify04/cleanA/supabase/migrations` (Run A) and
`source=/tmp/ct_verify04/cleanB/supabase/migrations` (Run B) — i.e. every migration was read from the
clone, never from the developer worktree.

The only absolute `/tmp` uses are legitimate and non-load-bearing: the disposable-target env file
`/tmp/<prefix>.env`, and the *default* evidence/log directories. Both were overridden per run with
`--evidence`.

---

## 5. Developer-worktree isolation test (REQUIRED, and performed)

Modes were recorded **before** any change, then the six support scripts **and** the `fixtures/`
directory were made unreadable in the developer worktree `/home/shomonrobie/ct_93d5cdd`:

| Path | Mode before | Mode during | Mode restored |
|---|---|---|---|
| `…/canonical_schema_rebuild.sh` | 644 | 000 | 644 |
| `…/apply_migrations.sh` | 644 | 000 | 644 |
| `…/canonical_schema_verify.py` | 644 | 000 | 644 |
| `…/d32_storage_operator.sql` | 644 | 000 | 644 |
| `…/verify_d32_policy_semantics.sql` | 644 | 000 | 644 |
| `…/d32_search_path_regression.sh` | 644 | 000 | 644 |
| `…/fixtures/` (directory) | 755 | 000 | 755 |

Verified unreadable as the owning user before the runs
(`cat …/canonical_schema_rebuild.sh` → `Permission denied`; `ls …/fixtures` → `Permission denied`),
and applied for **all three** dependent executions: Run A, Run B and the F-02 regression.

**Result: all three succeeded while the developer worktree's copies were mode 000.**
The rebuild therefore does not depend on the developer worktree. (During the mode-000 window
`git status` reports the affected files as ` M` — a stat-failure artefact, not a content change; see
§16.)

---

## 6. Fresh disposable database targets

| Property | Run A | Run B |
|---|---|---|
| Prefix | `ct_verify04` | `ct_verify04b` |
| Container (Postgres) | `ct_verify04_pg` id `e51584203856e5161484271c9162c8ee27277a5c4b75faf744683d5beca14dbf` | `ct_verify04b_pg` id `df721996ce69d72c70df6e523c6c611fc49132f27b4f9fa1abc7122ec0eaaabc` |
| Storage sidecar | `ct_verify04_storage` (Up) | `ct_verify04b_storage` (Up) |
| Volume | `ct_verify04_pgdata` created `2026-09-28T11:24:16+06:00` | `ct_verify04b_pgdata` created `2026-09-28T11:32:34+06:00` |
| Host port | `127.0.0.1:55520` | `127.0.0.1:55521` |
| Image | `public.ecr.aws/supabase/postgres:17.6.1.159` | same |
| PostgreSQL version | `PostgreSQL 17.6 … 64-bit`, `server_version=17.6` | `PostgreSQL 17.6 …`, `server_version=17.6` |
| Labels | `ct.schema02.disposable=true`, `ct.schema02.task=CT-SCHEMA-02-20260927` | same |
| Evidence dir | `/tmp/ct_verify04/evA` | `/tmp/ct_verify04/evB` |

Both were **brand-new** and this is enforced, not asserted: PHASE A of the runner fails closed unless
the target contains **0** `public` tables. Run A printed `fresh target public tables: 0`; the runner
also refuses to adopt an existing container/volume implicitly.

Pre-existing containers (including `ct_rel04a/b/c`, `ct_schema01/02`, `ct_impl01/02/02b`,
`ct_verify03`, `carbontally_demo_lab_*`, `supabase_*_carbon_ledger`, `hindsight-carbontally`) all
retained their original `RunningFor`/start state — **none was restarted or addressed**. The only two
Postgres endpoints this verification ever connected to were `127.0.0.1:55520` and
`127.0.0.1:55521`.

---

## 7. Migration results

Command (Run A; Run B identical except prefix/port/evidence):

```bash
cd /tmp/ct_verify04/cleanA
bash e2e/environment/scripts/canonical_schema_rebuild.sh \
     --prefix ct_verify04 --port 55520 --profile ct-implement-02 \
     --evidence /tmp/ct_verify04/evA
```

The committed script's own CLI was used unchanged. No argument was altered to make it pass.

| Stage | Run A | Run B |
|---|---|---|
| PHASE A | `PHASE A complete — platform layer present (storage.buckets, storage.objects, storage.foldername, auth.uid(), RLS on storage.objects)` | same |
| PHASE B (1–26) | `ALL_APPLIED applied=26 selected=26 source=/tmp/ct_verify04/cleanA/supabase/migrations` | `applied=26 selected=26 source=…/cleanB/supabase/migrations` |
| PHASE C operator | applied, then idempotency re-run OK | same |
| PHASE C semantics | `D32_SEMANTICS_RESULT pass=11 fail=0` | `D32_SEMANTICS_RESULT pass=11 fail=0` |
| PHASE D (27–92) | `ALL_APPLIED applied=66 selected=66 source=…/cleanA/supabase/migrations` | `applied=66 selected=66 source=…/cleanB/supabase/migrations` |
| chain totals | `applied=92 failed=0`, `distinct_files=92`, `ledger_rows_excluding_header=92` | ledger: 92 applied / 0 FAILED / 92 distinct |
| VERIFY | `=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===` | `=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===` |
| exit | `REBUILD VERIFIED — canonical schema reproduced`; rc `0` | `REBUILD VERIFIED …`; rc `0` |
| `^(FAIL|ABORT)` scan | 0 | 0 in `evB/verify.txt` |

`public.organization_members` was confirmed present after PHASE B (the D32 dependency), as the runner
asserts.

---

## 8. Schema inventory — independently determined

I did **not** read the verifier's expected counts as the answer. I ran my own implementation
(`/tmp/ct_verify04/indep_inv.py`), replicating the repository's canonical 12-class recipe with the
pinned rendering context `search_path = "$user", public, auth, extensions`, and separately ran my own
headline-count SQL.

Per-class rows and hashes (identical on both targets):

| Class | rows | sha256[:16] |
|---|---|---|
| A_schemas | 12 | `3b34dbbe3f5b4f3e` |
| B_tables | 379 | `330430f45617d48c` |
| C_columns | 4652 | `fe6ff790c47e9e40` |
| D_constraints | 798 | `d0d04127b83bbfce` |
| E_indexes | 569 | `1e1a2c351dc5f34b` |
| F_enums | 1 | `66b0463c35a783c0` |
| G_functions | 150 | `79d25d055502ec6b` |
| H_triggers | 100 | `e27fd1555237674b` |
| I_views | 3 | `719eae8c2fd3308a` |
| K_sequences | 1 | `ffe5afc1f09c4033` |
| L_rls | 233 | `1b79dbe7f080962e` |
| M_policies | 235 | `d08d59a13817b3d4` |

Headline counts, my own SQL, Run A target (`:55520`) and Run B target (`:55521`) — **identical**:

| Dimension | Independently observed | Prior canonical value | Match |
|---|---|---|---|
| public tables | 149 | 149 | ✅ |
| RLS-enabled public tables | 149 | 149 | ✅ |
| public tables without RLS | 0 | 0 | ✅ |
| policies (all schemas) | 235 | 235 | ✅ |
| policies granting anon/public | **0** | 0 | ✅ |
| foreign keys | 182 | 182 | ✅ |
| indexes | 569 | 569 | ✅ |
| public functions | 37 | 37 | ✅ |
| triggers (non-internal) | 100 | 100 | ✅ |
| columns (all schemas) | 4652 | 4652 | ✅ |
| policies in `public` / in `storage` | 231 / 4 | — | consistent (231+4 = 235) |
| `storage.buckets` `documents` rows / public | 1 / `false` | private, single | ✅ |
| `storage.objects` policies / RLS | 4 / `true` | 4, RLS on | ✅ |

Methodology note: my class SQL is a transcription of the repository's own `INVENTORY_CLASSES`
definition, because the fingerprint is only comparable if the recipe and the rendering context are
identical. I therefore did **not** invent a different recipe; instead I re-implemented the same recipe
in independent code, and cross-checked the underlying object inventory with separate count queries
written by me. Both converge.

---

## 9. Inventory fingerprint

Recomputed by my own code (sha256 of the concatenation of the 12 class blobs):

```
5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407
```

* Run A target (`:55520`): `5291cd91…c1407` ✅
* Run B target (`:55521`): `5291cd91…c1407` ✅
* Reported expected value: `5291cd91…c1407` — **matches**.

Independently consistent with the headline counts in §8: the same schema produced both the
fingerprint and the counts.

---

## 10. Migration-set fingerprints

Recomputed independently by a different tool path from the verifier's Python — a shell
`sha256sum` listing hashed with `sha256sum`, which is the canonical recipe:

```bash
cd <repo> && sha256sum supabase/migrations/*.sql | sha256sum
```

| Fingerprint | Independently computed | Reported expectation | Match |
|---|---|---|---|
| 92-migration canonical set | `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` | `36d5d85b…37944` | ✅ |
| 89-migration baseline anchor (92 minus the three `ct02_*` migrations) | `40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` | `40b168b3…03c30` | ✅ |
| CT-SCHEMA-01 pre-revision anchor (89 files with `20260823000000_d32_…` replaced by the committed fixture) | `d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c` | `d73e1e2b…8cb26c` (verifier's historical anchor) | ✅ |
| sha256 of the `{file, sha256_16}` listing of the 92 migrations (both runs) | `ad61d39d406616c8e3d65e9780cc5e614eb31d2e2d8988cd916f3355a5ee4efd` (identical in A and B) | — | consistency check |

Structural checks on the canonical set:

* 92 `.sql` files — exactly as claimed.
* No duplicate version prefixes (`ls | sed 's/_.*//' | sort | uniq -d` → empty).
* Deterministic order confirmed (`LC_ALL=C sort -c` on version prefixes passes).
* Endpoints: first `00000000000000_init_schema.sql`, last `20261023000000_ct02_scheduled_reporting.sql`.
* No unexpected migration files.

A measurement caveat worth recording, because it is a real trap: computing the baseline anchor with
**absolute** paths (`sha256sum /tmp/.../supabase/migrations/*.sql`) yields a different hash
(`aeb88cd2…`) than the canonical relative-prefix listing. The recipe is path-prefix sensitive by
design. My first pass hit this; the corrected, canonical-form value is the `40b168b3…` reported
above. This is a measurement artefact of mine, not a discrepancy in CT-RELEASE-04.

---

## 11. HEAD-scoped provenance — adversarial result

Code inspection (`canonical_schema_verify.py:439-447`): `allowed` is derived from the **HEAD file set**
and not from any hard-coded worktree list:

```python
head_names = <git ls-tree -r --name-only HEAD supabase/migrations, *.sql basenames>
changed    = <files reported by: git status --porcelain -- supabase/migrations>
allowed    = [m for m in (AUTHORISED_MIGRATION_REVISION, *CT_IMPLEMENT_02_MIGRATIONS) if m not in head_names]
check("migration_set_only_authorised_revision", changed == allowed, …)
```

Because the authorised D32 revision **and** the three `ct02_*` migrations are all present in HEAD,
`allowed` necessarily evaluates to `[]` at this HEAD; the check is therefore satisfied only when
nothing differs from HEAD.

Empirical adversarial results (executed in the disposable clone `/tmp/ct_verify04/provA`, nothing
committed, fully restored afterwards):

| Case | Mutation | Expected | Observed |
|---|---|---|---|
| A — clean HEAD | none | PASS, `changed=[]`, `allowed=[]` | **PASS** — `files differing from HEAD: none (allowed: [])`; rc 0 (`9 pass, 0 fail`) |
| B1 — unrelated *existing* migration modified | appended a comment to `00000000000000_init_schema.sql` | FAIL | **FAIL**, rc 1 — `migration_set_only_authorised_revision` (`changed=['00000000000000_init_schema.sql']`), plus `migration_set_fingerprint_matches_recorded` (actual `43588f98…`) and `baseline_migration_set_unchanged` (actual `792daba7…`); `6 pass, 3 fail` |
| B2 — new *unauthorised* migration added | created `20261024000000_ct_verify04_rogue.sql` | FAIL | **FAIL**, rc 1 — `migration_count` (93 files), `migration_set_only_authorised_revision` (`changed=['…_rogue.sql']`); `4 pass, 5 fail` |
| B3 — already-committed D32 revision modified | appended a line to `20260823000000_d32_private_documents_storage.sql` | FAIL | **FAIL**, rc 1 — `migration_set_only_authorised_revision` (`changed=['20260823000000_d32_private_documents_storage.sql']`, `allowed=[]`); `6 pass, 3 fail` |
| Restore | `git checkout -- supabase/migrations/` | PASS | **PASS** — `git status --short` 0 lines; rc 0 (`9 pass, 0 fail`) |

**The CT-VERIFY-03 defect is genuinely closed.** The check cannot silently become false-green when
the authorised revision has landed in HEAD: at a clean HEAD it passes *because* `changed` is empty
(not because a worktree-authored `allowed` list happened to match), and every deviation from HEAD —
committed or not — fails closed.

Secondary observation (bounded, not a defect): `allowed` is computed by **filename presence in HEAD**,
so an uncommitted revision of a file whose name already exists in HEAD is indistinguishable from an
unauthorised modification and fails (case B3). That is the conservative, fail-closed direction. The
positive `allowed != []` branch is consequently unreachable in the current history without rewriting
history (forbidden), so it could not be exercised — see §17.3.

---

## 12. F-02 regression — the previous false-green, attacked

### 12.1 Fixture identity (independently recomputed)

| Artefact | Independently computed | Reported expectation | Match |
|---|---|---|---|
| `fixtures/d32_pre_revision_ct_schema_01.sql` sha256 | `45d9eb87da8aec7bd824b858d7a55af6c2c6d340da2d8d01e91401c6e5421798` | `45d9eb87…5421798` | ✅ |
| same file, `git hash-object` (Git blob) | `66a8ddf87e9eaca36a2135214fec9c0afd8334bb` | `66a8ddf87e9eaca36a2135214fec9c0afd8334bb` | ✅ |
| current `supabase/migrations/20260823000000_d32_private_documents_storage.sql` sha256 / blob | `a7b36637177fc6ac439dd99b46d20a3463908dc1bf3228c521f428f3952f1e1f` / `0ab91907867598f48e77c8c1614ef01ab5f598e2` | blob `0ab9190` | ✅ |
| `cmp` fixture vs current migration | **DIFFERENT** | must differ | ✅ |

### 12.2 Proof the fixture is *genuinely* pre-revision (the strongest available test)

I reconstructed the CT-SCHEMA-01 89-file baseline and substituted the committed fixture for the D32
file. The resulting migration-set fingerprint is:

```
d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c
```

which is **exactly** the CT-SCHEMA-01 pre-revision anchor the verifier records. The fixture is
therefore byte-identical to the pre-revision artefact, and not a paraphrase of it. Conversely, the
same 89 files with the *current* D32 file give `40b168b3…03c30`. The regression cannot degenerate into
a self-comparison: the two artefacts provably differ, and the script additionally asserts the fixture
sha256, asserts the fixture's Git blob, and aborts if `fixture_sha == migration_sha` **before**
touching the target.

### 12.3 Regression execution

```bash
cd /tmp/ct_verify04/cleanA
bash e2e/environment/scripts/d32_search_path_regression.sh \
     --host 127.0.0.1 --port 55520 --db postgres --password <fresh> \
     --evidence /tmp/ct_verify04/regressA
```

Run **against the fresh Run A target**, from the **clean clone**, with the developer worktree's
`d32_search_path_regression.sh` **and** `fixtures/` at mode `000`:

```
=== RESULT: 13 passed, 0 failed ===   (rc 0)
```

Assertions that matter, verbatim from my run:

* fixture identity printed from the clone:
  `fixture sha256=45d9eb87da8aec7bd824b858d7a55af6c2c6d340da2d8d01e91401c6e5421798 blob=66a8ddf87e9eaca36a2135214fec9c0afd8334bb … current=a7b36637177fc6ac439dd99b46d20a3463908dc1bf3228c521f428f3952f1e1f`
* `PASS R1_pre_revision_as_provider_role (rejected: … missing the approved org-scope fragment)`
* `PASS R2_pre_revision_as_migration_role (rc=0)`, `PASS R2b_pre_revision_forced_pg_catalog (rc=0)`
* `PASS R3_revised_as_provider_role`, `R4_revised_forced_auth_public`, `R5_revised_forced_pg_catalog`, `R5b_revised_provider_forced_auth`
* `PASS R6a_pre_revision_accepts_lookalike_function (rc=0)` and
  `PASS R6b_revised_rejects_lookalike_function (rejected: … does not call the approved session-identity function auth.ui…)`
  — the look-alike `myauth.uid()` is accepted pre-revision and **rejected** post-revision: the
  validation was not weakened.
* `PASS R7_revised_rejects_missing_fragment (rejected: … missing the approved org-scope fragment)`
* `PASS R8 target restored (4 storage.objects policies)`, `PASS R8 documents bucket still private and single`, `PASS R9_revised_final_pass (rc=0)`

Ambient contexts recorded in the run, which are what triggered F-02 originally:
`supabase_admin: "$user", public, auth, extensions` vs `postgres: "$user", public, extensions`.

---

## 13. D32 semantics

`verify_d32_policy_semantics.sql` (11 assertions, executed against the disposable target):

| Execution | Result |
|---|---|
| Run A, inside the rebuild | `D32_SEMANTICS_RESULT pass=11 fail=0` |
| Run B, inside the rebuild | `D32_SEMANTICS_RESULT pass=11 fail=0` |
| Standalone by me against the Run A target | rc 0, `D32_SEMANTICS_RESULT pass=11 fail=0` (one `NOTE delete_policy_verified_structurally`, as designed) |

Final policy state on the Run A target, read directly from `pg_policies`:

```
d32_documents_delete_org_member :: DELETE :: authenticated
d32_documents_insert_org_member :: INSERT :: authenticated
d32_documents_select_org_member :: SELECT :: authenticated
d32_documents_update_org_member :: UPDATE :: authenticated
```

No fifth `storage.objects` policy; no anon/public-granting policy anywhere in the database (0).

---

## 14. D32 operator idempotency

The `d32_storage_operator.sql` operator step was executed **four** times on the same disposable target
(twice inside the rebuild — the initial application and the script's own in-script re-run — plus two
further explicit executions by me):

| Object count | before | after exec #3 | after exec #4 |
|---|---|---|---|
| `storage.objects` policies | 4 | 4 | 4 |
| `documents` bucket rows | 1 | 1 | 1 |
| `documents` bucket `public` | `f` | `f` | `f` |
| `storage.objects` rows | 0 | 0 | 0 |
| public tables | 149 | 149 | 149 |

Executions #3 and #4 both returned rc 0. No bucket duplication, no policy duplication, no state
corruption, no schema inconsistency. The runner's own assertion (`before == after == 4`,
`buckets == 1`) also passed inside both rebuilds.

---

## 15. Two-run determinism

Two **independent** clean clones and two **fresh** disposable targets:

| Measure | Run A (`cleanA`, `:55520`) | Run B (`cleanB`, `:55521`) | Verdict |
|---|---|---|---|
| migrations applied | `applied=92 failed=0`, `distinct_files=92` | 92 applied / 0 failed / 92 distinct | identical |
| PHASE B / D | 26/26, 66/66 (from `cleanA`) | 26/26, 66/66 (from `cleanB`) | identical |
| verifier result | `94 pass, 0 fail` | `94 pass, 0 fail` | identical |
| `FAIL` lines in verify output | 0 | 0 | identical |
| migration-set fingerprint | `36d5d85b…37944` | `36d5d85b…37944` | **identical** |
| inventory fingerprint (mine) | `5291cd91…c1407` | `5291cd91…c1407` | **identical** |
| 89-migration baseline anchor | `40b168b3…03c30` | `40b168b3…03c30` | identical |
| D32 semantics | `pass=11 fail=0` | `pass=11 fail=0` | identical |
| `migration_set_only_authorised_revision` | `changed` none, `allowed: []` | `changed` none, `allowed: []` | identical |
| per-migration `{file, sha256_16}` set | `ad61d39d…ee4efd` | `ad61d39d…ee4efd` | **identical (92 rows)** |
| raw ledger sha256 | `cb7c4457…` | `a0a470a2…` | **differs — expected** |

The raw ledger differs only because `ledger_canonical.tsv` carries a per-migration `seconds` column;
the identity that matters (per-file content hash and the resulting migration-set fingerprint) is
byte-identical. This mirrors, and independently confirms, the implementer's note that the ledger hash
is not a determinism signal.

Determinism was **not** tested by rebuilding one database twice: the two runs started from two
independent clones and two brand-new targets.

### 15.1 Final-HEAD result

The report's final HEAD is `61cf279`. The repository's actual HEAD at verification time is
`61cf279dfb41f5da9f9324cf4e75a9397fddc17b` — **identical; the repository has not advanced.** Both
clean clones were created from that HEAD and both runs executed at it, so the result applies to the
commit graph as it stands now, not merely to the change under test.

---

## 16. Repository / worktree integrity

| Check | Result |
|---|---|
| Developer repo (`ct_93d5cdd`) `git status --short --untracked-files=no` | ` M .gitignore` only — the **pre-existing, unrelated** modification, untouched |
| `git diff --name-only` (whole repo, tracked) | `.gitignore` only |
| `git diff --stat -- e2e/ supabase/ docs/` | empty (before this report was added) |
| `git diff --cached --name-only` | empty (nothing staged until the report commit) |
| Support-file content after chmod/restore | all seven `UNCHANGED` — `git hash-object <file>` equals `git rev-parse HEAD:<file>` |
| Workspace repo (`carbon_tally`) | untouched; 227 pre-existing tracked modifications remain as found; HEAD still `20b7a928…` |
| `git reset` / `rebase` / `amend` / `force-push` / push | none performed |
| Commits created | only the verification-report commit (§20) |
| Production / live / investor-demo / durable DB modified | none |
| Product code, migrations, RLS policies, frontend, backend modified | none |

---

## 17. Limitations

1. **Clean-checkout obtainability is bounded by the unpushed state.** The CT-RELEASE-04 commits are
   local-only (19 commits ahead of `github/p8-release-reconciled`). At the remote tip `cb70fd6`:
   `canonical_schema_rebuild.sh`, `canonical_schema_verify.py`, `d32_storage_operator.sql`,
   `verify_d32_policy_semantics.sql`, `d32_search_path_regression.sh` and
   `fixtures/d32_pre_revision_ct_schema_01.sql` are **ABSENT**; `e2e/environment/supabase/migrations`
   is a `040000 tree` rather than a `120000` symlink; and `supabase/migrations` holds **89**, not 92,
   files. An independent party cloning the shared remote today would therefore **not** be able to run
   this rebuild. My verification therefore used a clone of the **local repository object store**
   (`file://…/ct_93d5cdd`), which is a genuine clean clone of the verified commit (empty
   `git status`, no untracked/ignored files, objects fetched rather than hardlinked) — but it is not a
   clone of the shared remote. The implementation report discloses that nothing was pushed (§13); this
   limitation is a scoping bound on the *operational* guarantee, not a contradiction of any claim.
2. **Cold-cache image availability not tested.** The pinned images
   (`public.ecr.aws/supabase/postgres:17.6.1.159`, `…/storage-api:v1.69.0`) were already present
   locally. The runs prove *repository* completeness, not that the rebuild works on a machine that has
   never pulled those images. The implementation report records the same limitation.
3. **The positive `allowed != []` provenance branch was not exercised.** In the current history
   `allowed` is always `[]` because both the authorised D32 revision and the `ct02_*` migrations are in
   HEAD (and the D32 filename has existed in HEAD throughout). Exercising the "authorised revision is
   present as an uncommitted change while HEAD lacks the filename" case would require rewriting
   history, which is forbidden. I verified the fail-closed direction instead (cases B1–B3).
4. **Out of scope and untested:** the destructive integration harness (AGENTS.md §55.1), application /
   API / UI behaviour, data seeding, the `--profile ct-schema-02` 89-migration rebuild as a standalone
   run (only its fingerprint anchor was recomputed), and any live/production migration (R-11).
5. **Same images and same runner.** I used the committed script's own CLI unchanged, on the same
   pinned images. This is the intended test, but it means image-level differences were not varied.
6. `e2e/environment/scripts/__pycache__/` exists in the developer worktree (ignored). Not a
   reproducibility risk; noted for completeness.

---

## 18. Residual risks

1. The unpushed state (§17.1) means the reproducibility guarantee is not yet durable across machines
   or CI. Until `p8-release-reconciled` is pushed (a separately authorised action), the guarantee is
   confined to this repository.
2. Nothing *enforces* the clean-clone property in CI: a future commit could reintroduce a
   worktree-only dependency and no build would fail. A clean-clone rebuild job is the durable control.
3. Duplicated rebuild tooling elsewhere would be untested by this verification. A repository-wide
   search found exactly one copy of `canonical_schema_rebuild.sh` and one of
   `d32_search_path_regression.sh` (both under `e2e/environment/scripts/`).
4. The inventory fingerprint is path-prefix and `search_path` sensitive (§10 note; the verifier pins
   the rendering context deliberately). Any future change to the pinned context or the relative
   prefix would change the fingerprint without any schema change; that must be treated as a
   methodology change, not a schema regression.

---

## 19. Verification matrix

| ID | Claim | Independent test | Result | Evidence |
|---|---|---|---|---|
| V01 | clean clone contains the complete support set | clone + per-file existence + `git cat-file -e HEAD:<path>` | **PASS** | §4.1; all 10 present and tracked |
| V02 | 92 migrations present | `ls supabase/migrations/*.sql \| wc -l`, duplicate/order/endpoint checks | **PASS** | §10; 92 files, no dupes, deterministic |
| V03 | canonical migration symlink correct | `git ls-tree` mode `120000` + `readlink` + both counts | **PASS** | §4.1; `→ ../../../supabase/migrations`, 92 = 92 |
| V04 | no machine-path dependency | `grep -rn '/home/' e2e/ supabase/migrations/`; `REPO_ROOT` inspection | **PASS** | §4.2; no matches; clone-local `REPO_ROOT` |
| V05 | worktree files unnecessary | `chmod 000` on six scripts + `fixtures/`, run rebuild twice + F-02 from clean clones, then restore | **PASS** | §5; all runs succeeded; modes restored exactly |
| V06 | fresh DB rebuild succeeds | two brand-new targets, PHASE A freshness assertion | **PASS** | §6, §7; `fresh target public tables: 0` |
| V07 | 92 migrations / 0 failures | runner ledger over the whole chain | **PASS** | §7; `applied=92 failed=0`, `distinct_files=92` |
| V08 | canonical inventory reproduced | my own 12-class query set + my own count SQL | **PASS** | §8; 149/149/0/235/0/182/569/37/100/4652 |
| V09 | inventory fingerprint matches | my own independent implementation | **PASS** | §9; `5291cd91…c1407` on both targets |
| V10 | migration fingerprint matches | shell `sha256sum` listing recipe | **PASS** | §10; `36d5d85b…37944` |
| V11 | 89 baseline preserved | recompute over the 92-set minus the three `ct02_*` | **PASS** | §10; `40b168b3…03c30` |
| V12 | HEAD-scoped provenance works | clean-HEAD run; code inspection of `allowed` derivation | **PASS** | §11 case A; `changed` none, `allowed: []` |
| V13 | unrelated migration mutation fails | B1 modify existing, B2 add rogue, B3 modify committed D32 | **PASS** (all three FAILed as required) | §11 B1–B3, rc 1 each; restore re-PASSed |
| V14 | F-02 fixture is genuinely pre-revision | sha256, Git blob, `cmp` vs current, and CT-SCHEMA-01 anchor reconstruction | **PASS** | §12.1–12.2; `45d9eb87…` / `66a8ddf…`; anchor `d73e1e2b…` reproduced from the fixture |
| V15 | F-02 regression passes | run against fresh target from clean clone with worktree fixtures mode 000 | **PASS** | §12.3; `13 passed, 0 failed`, rc 0 |
| V16 | D32 semantics pass | in-rebuild (both runs) + my standalone execution | **PASS** | §13; `pass=11 fail=0` ×3 |
| V17 | D32 role/search_path protection works | R1/R2/R2b (pre-revision role-sensitivity), R3–R5b (revised path-independence), R6a/R6b (look-alike), R7 (drift) | **PASS** | §12.3; pre-revision rejected as provider, accepted as postgres; look-alike accepted pre / rejected post |
| V18 | D32 operator is idempotent | four executions with before/after object counts | **PASS** | §14; policies 4→4, bucket 1 (private), 0 objects |
| V19 | two independent rebuilds deterministic | two independent clones + two fresh targets | **PASS** | §15; identical 92/0/94/0, both fingerprints, anchor, semantics, and per-file hash set |
| V20 | final HEAD reproduces | actual HEAD `61cf279` used for both clones/runs | **PASS** | §15.1; no HEAD drift |
| V21 | no production/live/demo touched | container start-state comparison, port bindings, disposable labels, brand-new targets | **PASS** | §6; only `:55520`/`:55521`; all pre-existing containers untouched |
| V22 | verifier introduced no repository changes | `git status`, `git diff --name-only`, `git diff --cached`, per-file blob comparison | **PASS** | §16; only `.gitignore` (pre-existing) + this report |

---

## 20. Commands used (representative, exact)

```bash
# 0. repository state
cd /home/shomonrobie/ct_93d5cdd
git status --short --untracked-files=no ; git branch --show-current ; git rev-parse HEAD
git log --oneline --decorate -14

# 1. clean clones
git clone --no-local --single-branch --branch p8-release-reconciled \
          file:///home/shomonrobie/ct_93d5cdd /tmp/ct_verify04/cleanA
git clone --no-local --single-branch --branch p8-release-reconciled \
          file:///home/shomonrobie/ct_93d5cdd /tmp/ct_verify04/cleanB

# 2. worktree isolation (recorded, applied, restored)
stat -c '%a %n' <six scripts> e2e/environment/scripts/fixtures  > /tmp/ct_verify04/modes_before.txt
chmod 000 <six scripts> e2e/environment/scripts/fixtures
#
# 3. canonical rebuild, Run A / Run B
cd /tmp/ct_verify04/cleanA && bash e2e/environment/scripts/canonical_schema_rebuild.sh \
     --prefix ct_verify04  --port 55520 --profile ct-implement-02 --evidence /tmp/ct_verify04/evA
cd /tmp/ct_verify04/cleanB && bash e2e/environment/scripts/canonical_schema_rebuild.sh \
     --prefix ct_verify04b --port 55521 --profile ct-implement-02 --evidence /tmp/ct_verify04/evB
#
# 4. restore modes exactly
while read -r m f; do chmod "$m" "$f"; done < /tmp/ct_verify04/modes_before.txt

# 5. independent fingerprints
cd <repo> && sha256sum supabase/migrations/*.sql | sha256sum          # 36d5d85b…37944
cd /tmp/ct_verify04/b89    && sha256sum supabase/migrations/*.sql | sha256sum   # 40b168b3…03c30
cd /tmp/ct_verify04/anchor && sha256sum supabase/migrations/*.sql | sha256sum   # d73e1e2b…8cb26c
python3 /tmp/ct_verify04/indep_inv.py 55520 <pw>   # inventory fingerprint + own count SQL

# 6. adversarial provenance (disposable clone only)
git clone … /tmp/ct_verify04/provA
python3 e2e/environment/scripts/canonical_schema_verify.py --profile ct-implement-02 --migration-set-only
#   with: clean / modified existing migration / added rogue migration / modified committed D32
git checkout -- supabase/migrations/

# 7. F-02 regression, from the clean clone, fresh target
bash e2e/environment/scripts/d32_search_path_regression.sh \
     --host 127.0.0.1 --port 55520 --db postgres --password <fresh> --evidence /tmp/ct_verify04/regressA

# 8. D32 semantics standalone + idempotency
psql -h 127.0.0.1 -p 55520 -U postgres       -f …/verify_d32_policy_semantics.sql
psql -h 127.0.0.1 -p 55520 -U supabase_admin -f …/d32_storage_operator.sql    # ×2, counts compared
```

Evidence tree (my own, independent of the implementer's): `/tmp/ct_verify04/`
(`cleanA`, `cleanB`, `provA`, `evA/`, `evB/`, `regressA/`, `b89/`, `anchor/`, `indep_inv.py`,
`runA.log`, `runA.rc`, `runB.rc`, `prov_case*.txt`, `idem_run3.txt`, `idem_run4.txt`,
`semantics_standalone.txt`, `modes_before.txt`).

---

## 21. Classification

Per the project's truthfulness standard:

| Statement | Status |
|---|---|
| Support set is committed and present in a clean checkout | **INDEPENDENTLY VERIFIED** |
| A clean checkout of `61cf279` reproduces the canonical 92-migration schema on a fresh disposable target | **INDEPENDENTLY VERIFIED** |
| The canonical inventory fingerprint and the migration-set fingerprint reproduce exactly | **INDEPENDENTLY VERIFIED** |
| The 89-migration baseline is unmodified | **INDEPENDENTLY VERIFIED** |
| The migration-set provenance check is HEAD-scoped and fails closed | **INDEPENDENTLY VERIFIED** |
| The F-02 regression uses a genuine pre-revision fixture and is no longer vacuous | **INDEPENDENTLY VERIFIED** |
| The D32 operator step is idempotent; the D32 semantic suite passes | **INDEPENDENTLY VERIFIED** |
| The rebuild is deterministic across two independent clean clones and fresh targets | **INDEPENDENTLY VERIFIED** |
| The verified state is obtainable from the shared remote | **NOT VERIFIED** — it is not on the remote (§17.1) |
| The rebuild works from a cold image cache | **NOT VERIFIED** (§17.2) |
| Production / live / investor-demo readiness | **NOT CLAIMED** — outside this task; production readiness, live-schema readiness and investor-demo readiness are explicitly not asserted here |

---

## 22. Final verdict

```
CT_RELEASE_04_INDEPENDENTLY_VERIFIED_PASS_WITH_LIMITATIONS
```

The central CT-RELEASE-04 property — *a clean checkout of `61cf279` rebuilds the canonical
92-migration schema deterministically, without the developer worktree* — is **independently
reproduced**, twice, on two independent clean clones and two brand-new disposable targets, with the
developer worktree's support files simultaneously unreadable:

CLEAN CLONE (`61cf279`, `git status` empty)
→ 92 migrations, 26 + 66, **0 failures**, every file read from the clone
→ fresh disposable PostgreSQL 17.6 target
→ D32 operator (idempotent) + 11/0 semantics
→ **94 PASS / 0 FAIL**
→ inventory fingerprint `5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407` ✔
→ migration fingerprint `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` ✔
→ 89-migration baseline `40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` ✔
→ HEAD-scoped provenance PASS (`changed` none, `allowed: []`); three adversarial mutations FAIL closed
→ F-02 regression **13 passed / 0 failed** with the fixture proven genuinely pre-revision
→ second independent clean clone reproduces it exactly
→ final HEAD reproduces it exactly

The limitations are bounded and are not failures of any CT-RELEASE-04 claim: the verified commit graph
is **local-only (unpushed)**, so "clean checkout" currently means a clone of this repository rather
than of the shared remote; cold-cache image availability and the positive `allowed != []` branch
remain unexercised.

**No defect in CT-RELEASE-04 was found.** Nothing was repaired, refactored or "fixed forward" during
this verification, and no repository change was made other than this report.

---

## 23. Executive summary

| Item | Result |
|---|---|
| Exact HEAD verified | `61cf279dfb41f5da9f9324cf4e75a9397fddc17b` (branch `p8-release-reconciled`); no drift from the report's final HEAD |
| Clean-checkout result | Two independently created clean clones of `file:///home/shomonrobie/ct_93d5cdd`, `git status --short` empty, complete support set, correct `120000` symlink |
| Fresh DB result | Two brand-new disposable targets (`ct_verify04` `:55520`, `ct_verify04b` `:55521`), PostgreSQL 17.6, both asserted empty before use |
| Migration result | 26/26 then 66/66 → **92 applied / 0 failed / 92 distinct**, each run, from its own clone |
| Inventory result | tables 149, RLS 149, RLS-free 0, policies 235, anon/public policies 0, FKs 182, indexes 569, functions 37, triggers 100, columns 4652 — independently determined |
| Fingerprint result | inventory `5291cd91…c1407`; migration-set `36d5d85b…37944`; 89-baseline `40b168b3…03c30`; CT-SCHEMA-01 anchor `d73e1e2b…8cb26c` |
| F-02 result | fixture `45d9eb87…` / blob `66a8ddf…`, provably pre-revision and distinct from the current migration; regression **13 passed, 0 failed** |
| Determinism result | Run A and Run B identical (92/0, 94/0, both fingerprints, anchor, 11/0 semantics, identical per-file hash set) |
| Repository changes made | only this report (`docs/architecture/CT-PO-CARBONTALLY-CT-VERIFY-04-INDEPENDENT-REPORT-20260928.md`); pre-existing `.gitignore` modification left untouched |
| Live/production touched | nothing — only two self-named disposable containers on `127.0.0.1:55520` / `:55521` |
| Verdict | `CT_RELEASE_04_INDEPENDENTLY_VERIFIED_PASS_WITH_LIMITATIONS` |
| Report path | `docs/architecture/CT-PO-CARBONTALLY-CT-VERIFY-04-INDEPENDENT-REPORT-20260928.md` |

Production readiness, live-schema readiness and investor-demo readiness are **not** claimed. This
verification covers only CT-RELEASE-04 reproducibility and the explicitly tested D32 / F-02 controls.
