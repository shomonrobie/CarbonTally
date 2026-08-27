# CarbonTally V3 — Git History Secret Remediation Plan

**Task type:** CONTROLLED REPOSITORY-ONLY HISTORY CLEANUP — **PLANNING / READ-ONLY SCOPE VERIFICATION STAGE.**
**Executed in this task:** Complete read-only investigation of the known credential-bearing artifacts in Git history. **NO history rewrite, NO force push, NO commit, NO application/database/dependency changes were performed.**
**Status:** Plan complete — **HARD STOP. Awaiting Product Owner approval before the actual rewrite.**
**Date:** 2026-08-25

---

## 1. Executive Summary

Four known credential-bearing artifact paths exist in the reachable history of the private CarbonTally repository (`origin/main`), and one of them (`backend - backup.zip`) is still present in the current release tree (`9458067`):

1. `tools/carbon_data_factory/deeepseek_api.txt` — LLM-provider API key (already **revoked**; removed from HEAD in `878bd0f`, still in history at `2d23fb8`).
2. `.env` (root) — historical env file containing `SUPABASE_SERVICE_KEY` + `RESEND_API_KEY` categories (present `8b59378`→`a16ba01`, removed from HEAD).
3. `backend - backup.zip` — tracked archive containing `backend - backup/.env` (with `SUPABASE_SERVICE_KEY` + `RESEND_API_KEY` categories) and `backend - backup/tests/.env.test`; present `2d23fb8`→HEAD (still in the current tree).
4. `backend - backup/.env` — path *inside* the zip; covered by removing the archive (not a standalone Git path).

One candidate, `frontend/.env` (contains only `REACT_APP_API_URL` — not a confirmed secret), is recommended for inclusion with PO confirmation.

The D20–D37 release content is fully preserved by this scope: the four paths are not part of the release manifest, and all legitimate release files were verified present in `9458067`. The release commit's **SHA will change** after the rewrite (identical tree minus the removed paths).

Recommended rewrite method: **git-filter-repo** (not currently installed — install the standalone script in the execution phase); documented fallback: `git filter-branch --index-filter` (71 linear commits, single `main` branch, 4 paths, single developer).

---

## 2. Current Git Baseline

| Item | Value |
|---|---|
| Branch | `main` (only local branch) |
| HEAD | `9458067c073bdaedae2a621b9cee42e419f14a75` — `feat(v3): commit D20-D37 commercial platform release` |
| origin/main | `9458067c073bdaedae2a621b9cee42e419f14a75` |
| Local/remote sync | `0 0` (fully synchronized) |
| Commit count | 71 (linear history, **0 merges**) |
| Working tree | 546 modified, 151 deleted, 55 untracked, 0 staged (unstaged residue predates this task; untouched) |
| Tags | `rc2-final` (lightweight, `2d23fb8`), `v2.1-phase4` (annotated, `a13fd10`), `v2.1.1-phase3` (annotated, `a57c224`) |
| Other refs | `refs/cline/checkpoints/*` (146 local-only checkpoint refs) |

**Repository is PRIVATE** (`https://github.com/shomonrobie/CarbonTally.git`). A complete external backup of the working directory exists (PO-provided) and must remain untouched.

## 3. Repository Privacy Context

- Repository visibility: **PRIVATE**.
- Single-developer, single-branch workflow; no external collaborators identified; no CI/pr-agent integration confirmed.
- Impact of a history rewrite (all SHAs change) is therefore low-blast-radius but still requires the force-update protocol in §14.

## 4. Known Credential-Bearing Artifacts

| # | Path | Credential type (categories only — SECRET VALUE NOT REPRODUCED) | Status |
|---|---|---|---|
| 1 | `tools/carbon_data_factory/deeepseek_api.txt` | LLM-provider API key (blob begins `sk-`; 35-byte blob) | **REVOKED** by PO; removed from HEAD (`878bd0f`); still in history |
| 2 | `.env` (root) | Environment file with `SUPABASE_SERVICE_KEY`, `RESEND_API_KEY`, `SUPABASE_URL`, `REACT_APP_API_URL`, `VITE_*` categories | Development-stage; removed from HEAD (`a16ba01`) |
| 3 | `backend - backup.zip` | Zip archive containing `backend - backup/.env` (with `SUPABASE_SERVICE_KEY`, `RESEND_API_KEY`, `SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`, `VITE_*`) and `backend - backup/tests/.env.test` | **Still tracked at HEAD** (present in `9458067` tree) |
| 4 | `backend - backup/.env` | Same env categories (inside the archive) | Covered by removing the zip |

All values: **SECRET VALUE NOT REPRODUCED** in this report and in all analysis artifacts.

---

## 5. Historical Commit Inventory

| Path | Added in | Removed from HEAD in | Present in commit range (reachable from origin/main) |
|---|---|---|---|
| `tools/carbon_data_factory/deeepseek_api.txt` | `2d23fb8` (2026-08-06) | `878bd0f` (2026-08-24) | `2d23fb8` → `a909cbe` (11 commits) |
| `.env` (root) | `8b59378` (2026-07-21) | `a16ba01` (2026-07-21) | `8b59378` → `a16ba01` (2 commits) |
| `frontend/.env` (candidate) | `7ca9533` / `8b59378` (2026-07-21) | `a16ba01` (2026-07-21) | `7ca9533` → `a16ba01` (16 commits) |
| `backend - backup.zip` | `2d23fb8` (2026-08-06) | **not removed** | `2d23fb8` → `9458067` (13 commits incl. current release) |

## 6. Affected Branches / Tags

- **Branches:** only `main` / `origin/main` (no other branches).
- **Tags (all three are reachable from origin/main and affected):**
  - `rc2-final` → `2d23fb8` — contains artifacts #1, #3 (not #2, not #4).
  - `v2.1-phase4` → `a13fd10` — contains artifacts #1, #3.
  - `v2.1.1-phase3` → `a57c224` — contains artifacts #1, #3.
- **Local-only refs:** `refs/cline/checkpoints/*` (146) hold copies of the removed blobs locally; they must be pruned locally after the rewrite (they are never pushed, so no remote impact).
- **Merges:** 0 (linear history) — simplifies the rewrite.

## 7. Credential Status

| Artifact | Credential status |
|---|---|
| DeepSeek key | **REVOKED** (PO assertion). Historical copies remain in `2d23fb8`+ and in the three tags; also in some local checkpoint refs. |
| `.env` / `frontend/.env` | Development-stage credentials; not believed live; new production credentials will be generated later (PO decision). |
| `backend - backup.zip` / inner `.env` | Development-stage credentials; same handling. |

## 8. Exact Remediation Manifest

Paths to REMOVE from all history (confirmed credential-bearing):

1. `tools/carbon_data_factory/deeepseek_api.txt`
2. `.env`
3. `backend - backup.zip` (covers inner `backend - backup/.env` and `backend - backup/tests/.env.test`)

Candidate (PO confirm — recommended INCLUDE; content is only `REACT_APP_API_URL`, not a confirmed secret):

4. `frontend/.env`

**Explicitly OUT OF SCOPE** (flagged, not in manifest, not to be filtered by name-pattern):
- `backend/carbon_tally_backup.sql`, `backend/carbon_tally_backup_data.sql` — DB dumps present in origin/main history (2 objects); not PO-approved for this remediation; recommend separate review.
- `backups/*` — objects exist only in local checkpoint refs (0 in origin/main history); local-only prune.
- Any other file merely containing words like `key`/`token`/`password`/`secret` — excluded per PO scope ("no broad security remediation campaign").

---

## 9. D20–D37 Preservation Requirements

Verified in commit `9458067c073bdaedae2a621b9cee42e419f14a75` (all present):

- Backend: `backend/api/v3_billing.py`, `backend/services/billing.py`, `backend/main.py`, `backend/api/router.py` ✅
- Frontend: `frontend/src/App.js`, `frontend/src/v3/customer/BillingPage.jsx`, `frontend/src/v3/ops/CommercialTab.jsx` ✅
- Migrations: `supabase/migrations/20260824030000_d37_master_commercial_billing.sql` (+ all 9 other D-series migrations) ✅
- Tests: `backend/tests/unit/api/test_billing_core.py` etc. ✅
- Documentation: D27–D37 reports ✅

**Preservation guarantee:** none of the removal paths in §8 intersect the D20–D37 release manifest. `backend - backup.zip` is an older tracked file inherited into the release tree (not part of the staged release set); its removal is the PO's explicit intent. The rewritten release commit will contain the identical release content with only the four paths absent, and its **SHA will differ** from `9458067`.

## 10. Recommended Rewrite Method

- **Primary — `git-filter-repo`:** NOT currently installed (`git filter-repo` is not a git command; no `filter_repo` python module; pip package absent). In the execution phase, obtain the **standalone single-file script** (`git-filter-repo` from the official repository, a pure-Python script with no third-party deps) or `pip install git-filter-repo`, then run on a fresh clone:
  ```
  git clone --mirror <origin> /tmp/carbontally_rewrite.git
  cd /tmp/carbontally_rewrite.git
  git filter-repo --path tools/carbon_data_factory/deeepseek_api.txt --path .env \
      --path 'backend - backup.zip' --path frontend/.env --invert-paths --force
  ```
  `--invert-paths` removes exactly the listed paths from every commit. filter-repo rewrites all refs (incl. tags) and drops the filtered blobs from the object store.
- **Fallback — `git filter-branch --index-filter`** (documented reason for use): `git-filter-repo` is unavailable and installing it may not be possible in the execution environment; the repository is small (71 linear commits, 0 merges), single branch `main`, only 4 paths, single developer. Command:
  ```
  git filter-branch --index-filter 'git rm --cached --ignore-unmatch \
      tools/carbon_data_factory/deeepseek_api.txt .env "backend - backup.zip" frontend/.env' \
      --tag-name-filter cat -- --all
  ```
  Caveats acknowledged: slower, requires `git repack`/`git gc --prune=now` afterwards to drop the old blobs, and `--tag-name-filter cat` re-points tags.
- **Not used:** BFG (not installed; filter-repo is preferable). `filter-branch` only as the documented fallback.

## 11. Backup Strategy

1. PO external working-directory backup — untouched (authoritative rollback source).
2. Before any rewrite, create local repository snapshots:
   - `git bundle create /tmp/carbontally_pre_rewrite.bundle --all` (captures all refs incl. tags and checkpoints)
   - and/or `git clone --mirror /home/shomonrobie/carbon_tally /tmp/carbontally_pre_rewrite_mirror.git`
3. Record `9458067` + all 71 commit SHAs + tag SHAs before rewriting (e.g., `git rev-list HEAD > /tmp/shas.txt; git for-each-ref`).
4. Perform the rewrite ONLY on the separate mirror/clone in `/tmp` (§7 safety), never on the live working directory.

## 12. Rewrite Procedure (EXECUTION PHASE — NOT PERFORMED NOW)

1. Verify §11 backups exist and checksum-verify the bundle.
2. Clone/mirror into `/tmp` (separate from the live working tree).
3. Install/obtain `git-filter-repo` (standalone script) on the mirror; or use the documented `filter-branch` fallback.
4. Run the path-removal rewrite (§10) on the mirror.
5. Verify on the mirror (see §13) before any remote update.
6. Force-update the private remote (§14).
7. Align the live working repo: `git fetch origin`, move `main` to the new `origin/main`, remove the (now-untracked) `backend - backup.zip` from the working tree, prune local `refs/cline/checkpoints/*`, expire reflogs, `git gc --prune=now`.
8. Re-run §13 verification on the live repo.

---

## 13. Post-Rewrite Verification

On the mirror (and later on the live repo):

1. Known secret-bearing paths absent from all reachable history: `git log --all --oneline -- tools/carbon_data_factory/deeepseek_api.txt .env frontend/.env 'backend - backup.zip'` → empty.
2. Known credential strings absent from reachable objects: `git rev-list --all --objects | git cat-file --batch-check` + string scan (categories only) → no matches; plus `git grep` on all refs for the `sk-…` prefix → empty.
3. D20–D37 application files intact: re-run the §9 file presence check on the new HEAD.
4. New HEAD contains all legitimate files: `git diff --stat 9458067 <new-head>` → only the 4 removed paths differ.
5. No unrelated files removed: confirm the diff in (4) touches ONLY the manifest paths.
6. Working tree unaffected: live repo tree matches new HEAD after alignment; no unexpected changes.
7. Remote updated safely: origin/main == new HEAD; `0 0` sync.
8. No production code changed: application behavior identical (only history paths removed).
9. No database change occurred (nothing in this task touches the database).

## 14. GitHub Remote Update Procedure (EXECUTION PHASE — NOT PERFORMED NOW)

- Repository is **PRIVATE**, single-developer, linear main → low-risk force update.
- After mirror verification:
  ```
  git push --force origin main
  git push --force --tags origin
  ```
  (annotated tags `v2.1-phase4`/`v2.1.1-phase3` and lightweight `rc2-final` will point at their rewritten commits.)
- **No `--force-with-lease` needed** if the push is performed from the mirror immediately after verification (remote is known at `9458067`); otherwise use `--force-with-lease` from the live repo.
- Post-push: `git fetch origin && git rev-parse HEAD && git rev-parse origin/main` must match; `git rev-list --left-right --count origin/main...main` = `0 0`.

## 15. Risks

| Risk | Mitigation |
|---|---|
| All commit SHAs change (71 commits rewritten) | Expected; single-developer private repo; §11 backups |
| Release commit `9458067` replaced by a new SHA | Content preserved (identical tree minus 4 paths); report the new SHA to the PO |
| Annotated tags re-pointed | `--tag-name-filter cat` (fallback) / filter-repo default (primary) |
| Collaborator clones invalidated | Re-clone from rewritten remote; none confirmed |
| Local checkpoint refs (146) retain old blobs | Prune locally after rewrite; reflog expire + `gc --prune=now` |
| DB dumps (`backend/carbon_tally_backup*.sql`) remain in history | Out of scope; flagged for separate PO review |
| filter-branch fallback errors | Pre-verified on mirror; bundle rollback available |

## 16. Rollback Strategy

- Restore from the pre-rewrite bundle/mirror: `git clone /tmp/carbontally_pre_rewrite.bundle restore` (or restore the mirror), then `git push --force origin main` + `git push --force --tags` to return the remote to `9458067`/original SHAs.
- The PO external backup is the ultimate fallback.

## 17. Product Owner Decisions

1. Approve the execution-phase rewrite (this plan's §10–§14).
2. Approve inclusion of `frontend/.env` in the manifest (recommended) or restrict to the 3 confirmed paths.
3. Confirm force-push authorization for the private remote (main + tags).
4. Confirm the release baseline is re-recorded as the new rewritten HEAD SHA (replacing `9458067`).
5. Decide whether `backend/carbon_tally_backup*.sql` DB dumps in history warrant a later separate remediation.
6. Decide whether local `refs/cline/checkpoints/*` (146) should be pruned (recommended) as part of the execution phase.

## 18. Final Recommendation

Approve execution with the **3 confirmed paths + `frontend/.env`** (4 paths), using **git-filter-repo** (fallback: documented `filter-branch`), on a **separate mirror**, with the §11 backups, §13 verification, §14 force-update, and §16 rollback in place. All application, migration, test, documentation, and database content is preserved; only the four credential-bearing paths are removed from all history.

## 19. HARD STOP

Verified at the end of this planning stage:
- HEAD: `9458067c073bdaedae2a621b9cee42e419f14a75`; origin/main identical; 71 commits; 0 staged.
- **NO history rewrite, NO force push, NO commit, NO application/database/dependency changes occurred.**
- The only repository addition is this plan: `docs/audit/cline/CARBONTALLY_GIT_HISTORY_SECRET_REMEDIATION_PLAN.md`.
- STOP. Execution begins only after explicit Product Owner approval.

---

*End of plan. SECRET VALUE NOT REPRODUCED anywhere in this document.*
