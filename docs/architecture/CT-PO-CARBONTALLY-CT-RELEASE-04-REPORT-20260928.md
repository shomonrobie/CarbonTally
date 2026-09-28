# CT-RELEASE-04 — Reproducible Canonical Rebuild from a Clean Checkout (implementation report)

**Date:** 2026-09-28
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Task ID:** CT-RELEASE-04-20260928-CLEAN-CHECKOUT-CANONICAL-REBUILD
**Starting SHA:** `b313fc2242b1deca0370ac48749549f5bb435a11`
**Ending SHA:** `5a0c5af` (the CT-RELEASE-04 report commit — see §15; the
task-local bookkeeping note that follows it names its own SHA)
**Status:** REPRODUCIBILITY INFRASTRUCTURE **IMPLEMENTED · EXECUTED TWICE FROM TWO
INDEPENDENT CLEAN CHECKOUTS ON DISPOSABLE TARGETS**; **NOT INDEPENDENTLY VERIFIED**;
no production, live or investor-demo system was touched

> **INDEPENDENT VERIFICATION NOT PERFORMED.** Every result below was produced by
> the implementing agent's own harness on disposable infrastructure. `TESTED` and
> `VERIFIED` here mean "the named command, run from a clean checkout of the named
> commit, reproduced the stated result" — not "independently accepted"
> (AGENTS.md §73).

---

## 1. Task and scope

CT-VERIFY-03 (independent verification of CT-SCHEMA-02/03) found that the
*verified* canonical 92-migration rebuild was not reproducible from the
repository: the verification depended on files that existed only in the
developer's worktree. CT-RELEASE-04 closes that gap so that

```bash
git clone <repo> && cd <repo>
bash e2e/environment/scripts/canonical_schema_rebuild.sh --profile ct-implement-02
```

on a clean checkout of HEAD reproduces the canonical environment with no
untracked file, ignored file, developer-specific path, second worktree or
manually prepared SQL.

| Layer | In scope | Out of scope (unchanged) |
|---|---|---|
| Schema | **none** — no migration was added, changed or applied to any durable database | live/production migration (R-11, external blocker) |
| Rebuild tooling | `e2e/environment/` runner, verifier, fixtures, README, CLI config | product/application code (none touched) |
| Data | none | investor-demo dataset (not read, not written, not reseeded) |
| Docs | this report | all other documentation backlogs |

No business policy was invented; no Product Owner decision was required or taken.

---

## 2. What CT-VERIFY-03 found, and how each item is closed

| # | CT-VERIFY-03 finding (worktree-scoped dependency) | Closure in this change-set | Proof |
|---|---|---|---|
| 1 | `canonical_schema_verify.py` treated the uncommitted D32 revision as an *allowed* deviation **relative to the worktree**, so `changed == allowed` held only in the worktree that held the revision | the provenance check is now **HEAD-scoped**: an authorised revision may differ from `HEAD` only while `HEAD` does not contain it (`allowed` is derived from the HEAD file set) | `PASS migration_set_only_authorised_revision — files differing from HEAD: none (allowed: [])` in both runs (§10, §11) |
| 2 | `d32_search_path_regression.sh` read the *pre-revision* D32 file back out of `git HEAD`; once the revision landed at HEAD that read returned the **revised** file, silently degrading F-02 to a vacuous pass | the pre-revision artefact is now a **committed, hash-pinned fixture**; the script asserts its sha256, its git blob, and that it differs from the current migration, before running | `13 passed, 0 failed` with all assertions live (§12) |
| 3 | The D32 operator step (`d32_storage_operator.sql`) and its behavioural proof (`verify_d32_policy_semantics.sql`) existed only as untracked worktree files | both committed | `PHASE C` executed from the clean clone in both runs (§10, §11) |
| 4 | `e2e/environment/supabase/migrations` was a **53-file copy** of the canonical chain that had drifted from `supabase/migrations` | replaced by a symlink to the canonical chain, so it cannot drift again | `120000 blob d66cc4f` → resolves to 92 files (§6) |
| 5 | The D32 revision migration (`supabase/migrations/20260823000000_d32_private_documents_storage.sql`) was the worktree-only file the rebuild pivoted on | committed at HEAD — the rebuild is HEAD-scoped, so committing it is what makes a clean checkout self-consistent | `blob 0ab9190`; §11 provenance lines |
| 6 | `apply_migrations.sh`, `bootstrap.sh`, `reset.sh`, `config.toml` and the README described/executed a superseded CLI-driven flow | corrected to the real flow (CLI is platform-only, `[db.migrations] enabled = false`) and the reproducibility guarantee documented | `e2e/environment/README.md` § *Reproducibility (CT-RELEASE-04)* |

Nothing in this change-set alters schemas, RLS, migrations, application code or
business behaviour. It is a repository-integrity change only.

---

## 3. The committed support set

`c3a8df5` — *CT-RELEASE-04: commit the canonical-rebuild support set so a clean
HEAD rebuilds* — 65 files changed, 1403 insertions(+), 8630 deletions(−): 12
added/modified entries and 53 deletions (the drifted copy).

| File | Lines | Why it must be in the repository |
|---|---|---|
| `e2e/environment/scripts/canonical_schema_verify.py` | +14 / −5 | the verifier, including the now HEAD-scoped provenance rule (§4) |
| `e2e/environment/scripts/apply_migrations.sh` | +225 / −23 | the canonical runner; `REPO_ROOT` is derived from `${SCRIPT_DIR}/../../..`, i.e. clone-local |
| `e2e/environment/scripts/d32_storage_operator.sql` | +201 | the D32 operator step (PHASE C, provider privilege) |
| `e2e/environment/scripts/verify_d32_policy_semantics.sql` | +243 | the behavioural D32 policy-semantics proof (11 assertions) |
| `e2e/environment/scripts/d32_search_path_regression.sh` | +215 | the F-02 regression harness, now fixture-driven (§5) |
| `e2e/environment/scripts/fixtures/d32_pre_revision_ct_schema_01.sql` | +194 | the hash-pinned pre-revision D32 artefact (blob `66a8ddf`, sha256 `45d9eb87…5421798`) |
| `e2e/environment/supabase/migrations` | `120000` symlink | `→ ../../../supabase/migrations`, replacing the 53-file drifted copy (§6) |
| `supabase/migrations/20260823000000_d32_private_documents_storage.sql` | −121 / +121 | the P8-D17-D32-STORAGE-POLICY-VALIDATION-DETERMINISM-001 revision (blob `0ab9190`) |
| `e2e/environment/scripts/bootstrap.sh` | +37 / −9 | CLI platform-only provisioning |
| `e2e/environment/scripts/reset.sh` | +37 / −4 | ditto |
| `e2e/environment/supabase/config.toml` | +13 / −1 | `[db.migrations] enabled = false` — the CLI must not apply migrations |
| `e2e/environment/README.md` | +112 / −13 | the reproducibility guarantee and the corrected flow |

`canonical_schema_rebuild.sh` needed no change: it was already committed and is
location-relative. The fixture is **not** a migration — `apply_migrations.sh`
reads `supabase/migrations` only, and the migration-set fingerprint is computed
from that directory alone, so the fixture cannot enter the rebuild.

Not included in the commit: credentials, machine-specific paths, evidence
directories, `__pycache__`, or any unrelated worktree change.

---

## 4. Change 1 — the migration-set provenance check is now HEAD-scoped

`canonical_schema_verify.py` proves the canonical migration chain was not
tampered with by comparing the *working-tree* migration set against `HEAD`:

* `migration_set_only_authorised_revision` requires every file that differs from
  `HEAD` to be in an explicit `allowed` list;
* `migration_set_provenance_baseline_from_head` recomputes a recorded 89-file
  baseline anchor from `HEAD` minus the later additions.

The defect: `allowed` was a **fixed, worktree-authored list** naming the
uncommitted D32 revision. That made both checks pass only in the one worktree
where the revision was uncommitted, and made them unsatisfiable everywhere else
(a clean checkout has `changed = ∅`, but the fixed list still expected the D32
file). The check was therefore *worktree-scoped verification*, which is not
verification.

The fix: `allowed` is derived **from the HEAD file set** — a revision may differ
from `HEAD` only while `HEAD` does not yet contain it — so

* in a clean checkout of HEAD (nothing can differ from HEAD) → `allowed = []`,
  `changed = []` → PASS;
* in a worktree that is ahead of its own `HEAD` with the authorised revision
  still uncommitted → `allowed = [that revision]` → PASS;
* any other difference from `HEAD` → the recorded baseline anchor no longer
  matches → FAIL, unchanged from before.

The property being proved is unchanged; only its frame of reference moved from
"this developer's worktree" to "the commit under test". The explanatory comment
block in the verifier was updated to state the frame of reference explicitly.

## 5. Change 2 — the F-02 regression no longer reads its own target out of git

`d32_search_path_regression.sh` reproduces F-02 by re-creating the **pre-revision**
D32 migration against a live target and showing that the drift detector rejects
it. It previously obtained that pre-revision SQL with `git show HEAD:…`, which is
correct only while the revision is *not* at `HEAD`. Once the revision landed, that
command returned the revised file — the regression would have been comparing the
fixed artefact against itself and passing vacuously.

The script now reads a committed fixture and asserts its identity **before** doing
anything with the target:

* sha256 `45d9eb87da8aec7bd824b858d7a55af6c2c6d340da2d8d01e91401c6e5421798`
* git blob `66a8ddf87e9eaca36a2135214fec9c0afd8334bb`
* it must **differ** from the current migration (`blob 0ab9190`) — i.e. the
  regression can never silently degenerate into a self-comparison again

The fixture is a frozen artefact of the CT-SCHEMA-01-verified pre-revision file,
not a second source of truth for any migration.

## 6. Change 3 — `e2e/environment/supabase/migrations` is a symlink, not a copy

That path held a 53-file copy of the canonical chain that had drifted from
`supabase/migrations` (which itself had moved on to 92 files). A duplicate copy of
a migration chain is a drift generator, and nothing needs it: the runner reads
`$REPO_ROOT/supabase/migrations` and the CLI no longer applies migrations at all
(`[db.migrations] enabled = false`). It is now a symlink,
`120000 blob d66cc4f → ../../../supabase/migrations`, so it resolves to the
canonical chain (92 files) by construction and can never drift again.

## 7. Changes 4–5 — the D32 revision, and the CLI/README corrections

The D32 revision is committed at `HEAD`
(`supabase/migrations/20260823000000_d32_private_documents_storage.sql`,
blob `0ab9190`). This is the file the whole rebuild pivots on: with it at `HEAD`
the HEAD-scoped provenance rule in §4 is satisfiable in a clean checkout, and the
92-file chain is what the fingerprint asserts.

`bootstrap.sh`, `reset.sh`, `config.toml` and `README.md` were corrected to the
flow that actually reproduced the canonical environment: the Supabase CLI
provisions the **platform** only (`auth.*`, `storage.*`) and the application layer
is applied by `apply_migrations.sh` in the dependency-ordered phases (A platform
→ B migrations 1–26 → C D32 operator + behavioural proof → D migrations 27–92).
The README gained the *Reproducibility (CT-RELEASE-04)* section stating the
clean-checkout guarantee, the fixture's role and hash, and the platform-only CLI
rule.

---

## 8. Verification method

The point of CT-RELEASE-04 is reproducibility, so the verification was designed so
that the *developer worktree cannot have contributed anything*:

| Control | How it was enforced |
|---|---|
| Independent checkout | `git clone --single-branch` of the repository into `/tmp/ct_rel04_clean` and `/tmp/ct_rel04_clean2` — a **separate working tree**, not a second worktree of the same one |
| Clean tree | `git status --short` empty in both clones; `HEAD = c3a8df55e2e6f4484c6344edd33b1b78842846b3` in both |
| No path leakage | no `/home/shomonrobie` reference exists anywhere under `e2e/` or `supabase/migrations` in either clone; `REPO_ROOT` derives from `${SCRIPT_DIR}/../../..` |
| **Originals deliberately unusable** | before either run, every support file in the *developer* worktree was set to mode `000` (`chmod 000` on the six scripts **and** on `fixtures/`), so nothing in either run could have read the files whose worktree-only existence CT-VERIFY-03 flagged. The listing was captured as evidence (`----------` for all seven). Modes were restored to `644`/`755` afterwards and `git status e2e/` is clean |
| Disposable targets | two brand-new labelled containers (`ct_rel04a`, `ct_rel04b`) on private host ports, created by the runner itself; no durable environment was addressed |
| Chain provenance | the verifier's own `migration_set_*` and `inventory_fingerprint_*` checks, printed and quoted verbatim below |

Both clones were at the same commit, so the two runs also serve as a determinism
check of the rebuild itself.

## 9. Preconditions observed in a clean checkout

| Property | Value |
|---|---|
| `HEAD` | `c3a8df55e2e6f4484c6344edd33b1b78842846b3` |
| `git status --short` | empty (no untracked, no modified, no staged) |
| `supabase/migrations` | 92 files |
| `e2e/environment/supabase/migrations` | symlink `→ ../../../supabase/migrations`, resolving to the same 92 files |
| support scripts present | `apply_migrations.sh`, `canonical_schema_rebuild.sh`, `canonical_schema_verify.py`, `d32_storage_operator.sql`, `verify_d32_policy_semantics.sql`, `d32_search_path_regression.sh`, `fixtures/d32_pre_revision_ct_schema_01.sql` — all present |
| fixture identity in the clone | sha256 `45d9eb87…5421798`, git blob `66a8ddf` |
| machine-specific paths | none found under `e2e/` or `supabase/migrations` |

## 10. Run 1 — from clean clone A, with the worktree originals disabled

```
bash e2e/environment/scripts/canonical_schema_rebuild.sh \
     --prefix ct_rel04a --port 55510 --profile ct-implement-02 \
     --evidence /tmp/ct_rel04a_evidence
```

| Stage | Result |
|---|---|
| PHASE A — platform | `PHASE A complete — platform layer present (storage.buckets, storage.objects, storage.foldername, auth.uid(), RLS on storage.objects)` |
| PHASE B — migrations 1–26 | `ALL_APPLIED applied=26 selected=26 source=/tmp/ct_rel04_clean/supabase/migrations` — `public.organization_members` present (D32 dependency satisfied) |
| PHASE C — D32 operator + semantics | operator step OK and idempotent on re-run (4 policies, 1 bucket unchanged); `D32_SEMANTICS_RESULT pass=11 fail=0` |
| PHASE D — migrations 27–92 | `ALL_APPLIED applied=66 selected=66 source=/tmp/ct_rel04_clean/supabase/migrations` |
| chain totals | `applied=92 failed=0`, `distinct_files=92` |
| VERIFY | `=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===` |
| fingerprints | `inventory_fingerprint_actual — 5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407`; `migration_set_fingerprint_actual — 36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` |
| provenance | `PASS migration_set_only_authorised_revision — files differing from HEAD: none (allowed: [])` |
| baseline anchor | `PASS baseline_migration_set_unchanged — the 89 CT-SCHEMA-01/02 migrations still reproduce 40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` |
| exit | `REBUILD VERIFIED — canonical schema reproduced` |
| abort/FAIL scan | `grep -cE '^(FAIL|ABORT)' /tmp/ct04_run1.log` → `0` |

The runner sourced every phase file from
`/tmp/ct_rel04_clean/e2e/environment/scripts/` — i.e. from the clean clone — while
the same-named files in the developer worktree were unreadable.

## 11. Run 2 — from clean clone B, and determinism

A **second, independent clone** of the same commit was built on a second
disposable target (`--prefix ct_rel04b --port 55511`, evidence
`/tmp/ct_rel04b_evidence`), again with the developer worktree's support files
still at mode `000`.

| Measure | Run 1 (clone A) | Run 2 (clone B) | Verdict |
|---|---|---|---|
| migrations applied | 92 (26 + 66), `failed=0` | 92 (26 + 66), `failed=0` | identical |
| verifier checks | 94 pass / 0 fail | 94 pass / 0 fail | identical |
| canonical inventory fingerprint | `5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407` | `5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407` | **identical — matches the recorded canonical value** |
| migration-set fingerprint | `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` | `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` | **identical** |
| 89-migration baseline anchor | `40b168b3…03c30` | `40b168b3…03c30` | identical, unchanged by this change-set |
| `migration_set_only_authorised_revision` | `files differing from HEAD: none (allowed: [])` | `files differing from HEAD: none (allowed: [])` | PASS in a clean checkout — **the CT-VERIFY-03 defect is gone** |
| `migration_set_provenance_baseline_from_head` | PASS (`head_set=92 files`) | PASS (`head_set=92 files`) | identical |
| per-run ledger sha256 | `9bc33011…` | `e765ccaf…` | **differs — expected, see below** |

The per-run ledger file (`ledger_canonical.tsv`) records a `seconds` column per
migration, so its file hash is timing-dependent and is *not* a determinism signal;
the identity that matters (the per-migration `sha256_16` of every file, and the
resulting migration-set fingerprint) is identical across the runs. Recording the
difference here rather than presenting a single hash as "reproducible" is
deliberate.

## 12. F-02 `search_path` regression on the run-1 target

```
bash e2e/environment/scripts/d32_search_path_regression.sh \
     --host 127.0.0.1 --port 55510 --db postgres --password <from /tmp/ct_rel04a.env> \
     --evidence /tmp/ct_rel04a_regress
```

`=== RESULT: 13 passed, 0 failed ===`, exit code `0`. The assertions that matter
for the CT-VERIFY-03 finding:

| Assertion | Evidence |
|---|---|
| fixture identity asserted before use | the run succeeded with the fixture read from `/tmp/ct_rel04_clean/e2e/environment/scripts/fixtures/` while the developer worktree's `fixtures/` directory was mode `000` |
| the pre-revision artefact is genuinely pre-revision | `PASS R1_pre_revision_as_provider_role (rejected: D32 policy drift: d32_documents_select_org_member is missing the approved org-scope fragment)` |
| a look-alike function is accepted only pre-revision | `PASS R6a_pre_revision_accepts_lookalike_function (rc=0)`, `PASS R6b_revised_rejects_lookalike_function (rejected: … does not call the approved session-identity function auth.…)` |
| the revised file is required | `PASS R3_revised_as_provider_role (rc=0)`, `PASS R4_revised_forced_auth_public (rc=0)`, `PASS R5b_revised_provider_forced_auth (rc=0)` |
| the target is left as found | `PASS R8 target restored (4 storage.objects policies)`, `PASS R8 documents bucket still private and single`, `PASS R9_revised_final_pass (rc=0)` |

This is the check that was silently vacuous before the change: it now proves the
detector distinguishes pre-revision from revised rather than comparing a file with
itself.

---

## 13. Not performed / limitations

| Item | Status | Why |
|---|---|---|
| Independent re-verification by a second agent | **NOT PERFORMED** | out of scope for this task; the clean-clone procedure in §8–§12 is written to be re-runnable by an independent verifier |
| Push to any remote | **not performed** | explicitly out of scope (AGENTS.md §70); the commit is local |
| Any production / live / investor-demo database or storage | **not touched** | the only targets were the two disposable labelled containers created by the runner |
| Full 1,185-identity demo audit, application/API/E2E suites | not run | unrelated to a tooling change; the suites do not exercise the rebuild path |
| `ct-schema-02` profile (89-migration baseline) rebuild | not re-run | the 89-migration baseline anchor is asserted *inside* the 92-migration run (`baseline_migration_set_unchanged`, `migration_set_provenance_baseline_from_head`), which is the stronger statement |
| A "clean checkout" on a machine that has never built this project | not possible here | Docker images were already present locally; the runs therefore prove *repository* completeness, not image-availability from a cold cache |
| Disposable targets torn down | **no — deliberately left running** | so an independent verifier can re-run §12 against them. Teardown: `docker rm -f ct_rel04a_pg ct_rel04a_storage ct_rel04b_pg ct_rel04b_storage && docker volume rm ct_rel04a_pgdata ct_rel04b_pgdata` (add `rm -f /tmp/ct_rel04a.env /tmp/ct_rel04b.env`, which hold the disposable target passwords) |

## 14. Security, isolation and secret handling

* Nothing was committed that contains credentials, tokens, JWTs, signed URLs,
  passwords or connection strings. The runner generates disposable Storage key
  material per run and writes the target password to `/tmp/<prefix>.env` only;
  neither file is in the repository, and no such value appears in this report.
* The staged diff was scanned for secret-shaped content and for the developer's
  home path before committing: no matches.
* No RLS policy, migration, schema object or application authorization path was
  modified by this change-set — the only SQL moved into the repository is the D32
  operator step and the semantics proof that CT-SCHEMA-02/03 already verified.
* Disposable infrastructure only: labelled containers and volumes the runner names
  itself, on private host ports. No durable environment was addressed.

## 15. Git state and commits

| Commit | SHA | Subject |
|---|---|---|
| 1 | `c3a8df5` | `CT-RELEASE-04: commit the canonical-rebuild support set so a clean HEAD rebuilds` — **the change under test**; both clean-clone runs in §10–§11 were executed against this commit |
| 2 | `5a0c5af` | `CT-RELEASE-04: implementation report` — this document |
| 3 | (this commit; SHA recorded in the bookkeeping note below the table) | the same report, edited only to name commit 2's SHA — no content of substance changes |

| Property | Value |
|---|---|
| Branch | `p8-release-reconciled` (unchanged) |
| Starting SHA | `b313fc2242b1deca0370ac48749549f5bb435a11` |
| History rewritten / reset / amended / force-pushed | **no** |
| Commits pushed | **no** |
| `git status` after the change | `e2e/` clean; the only remaining worktree modification is a **pre-existing** `.gitignore` change that is not part of this task (below) |
| Files changed by commit 1 | 65 (12 added/modified, 53 deletions) — `+1403 / −8630` |

**The `.gitignore` worktree change was deliberately left untouched.** It is not
part of CT-RELEASE-04: it adds one line (`.aider*`) plus a CRLF re-write of the
file (`git diff --ignore-cr-at-eol --numstat .gitignore` → `1 0`). Absorbing an
unrelated local modification into this commit would have violated AGENTS.md §70,
so it remains uncommitted in the worktree and is recorded here instead.

**Bookkeeping note.** Commit 3 exists solely because a commit cannot contain its
own SHA. Its content is exactly the two edits above — the header *Ending SHA* line
and row 2 of this table — so a reader who checks out commit 3 sees a document whose
cited SHAs are all resolvable, and a reader who checks out commit 2 sees a document
identical in substance. Nothing after `c3a8df5` changes any file that the rebuild
reads: commits 2 and 3 touch `docs/` only, so the clean-clone result in §10–§11
still applies verbatim to the current `HEAD`.

## 16. Remaining work / residual risk

1. **Independent re-verification** of the clean-checkout claim by a party that did
   not write the change (the intended next step per AGENTS.md §60).
2. **Duplicated rebuild tooling** elsewhere in the repository: CT-RELEASE-04 fixed
   the `e2e/environment/` path only. Any other copy of these scripts (e.g. under a
   `qa_harness/` or CI path) must be checked by the same test — clone to a fresh
   path and run, with the developer worktree's copies made unreadable.
3. **CI enforcement**: nothing yet *fails a build* when a script gains a
   worktree-only dependency again. A clean-clone rebuild job is the durable control
   and is not implemented here.
4. **`--profile ct-schema-02`** remains available but was not re-run in this
   change-set (its baseline is asserted inside the 92-migration run).
5. The live-migration blocker (R-11) is untouched by this task; it remains external
   to CT-RELEASE-04.

## 17. Acceptance language

* **IMPLEMENTED** — the support set is committed; a clean checkout of
  `c3a8df5` contains everything the rebuild needs.
* **TESTED** — executed twice from two independent clean clones on disposable
  targets, with the developer worktree's copies of those files made unreadable:
  92 migrations, 0 failures, 94/94 verifier checks, canonical inventory fingerprint
  `5291cd91…c1407` and migration fingerprint `36d5d85b…37944` reproduced exactly,
  and 13/13 F-02 regression assertions passed.
* **VERIFIED** — *not claimed*. No independent agent has re-run this procedure.
* **ACCEPTED** — *not claimed*. Acceptance is the Product Owner's, not this
  agent's.
