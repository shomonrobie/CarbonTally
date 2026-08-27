# CarbonTally V3 — Git History Secret Remediation Execution Report

**Status: PARTIAL EXECUTION — REWRITE COMPLETE & VERIFIED LOCALLY; PUSH STOPPED BEFORE PUSH per Phase 5 (new credential-bearing artifacts discovered requiring Product Owner decision).**
**Date:** 2026-08-25

---

## 1. Executive Summary

The approved 3-path history rewrite was performed successfully on a **separate mirror** and fully verified locally:

- `tools/carbon_data_factory/deeepseek_api.txt`, `.env`, and `backend - backup.zip` are **absent from the rewritten tree and from all reachable rewritten history** (0 objects).
- `frontend/.env` was **preserved** (out of scope).
- D20–D37 content is fully preserved (16 key files verified in the new HEAD); tree equivalence vs old `9458067` confirmed **byte-for-byte except the single removed `backend - backup.zip`**.
- New canonical main/release SHA: `0812b015e1184d2b84c525181c85805672dfa1e8` (70 commits; empty `878bd0f` correctly dropped). fsck clean.
- **The remote was NOT updated.** The post-rewrite secret scan (Phase 5) discovered **two NEW credential-bearing tracked artifacts outside the approved manifest**:
  1. `create_admin_dashboard.py` — contains a hard-coded `REACT_APP_SUPABASE_SERVICE_KEY=<value>` (line 163) in the **current tracked tree**.
  2. `frontend/.env` — the `8b59378` version (blob `67a7e17d`, 273 B) contains `SUPABASE_SERVICE_KEY` and `RESEND_API_KEY` with values (contradicting the earlier "no confirmed secret" classification for that version).
- Per the task instruction ("If NEW credential-bearing tracked artifacts are discovered: DO NOT expand the rewrite automatically. STOP BEFORE PUSH, report, request PO decision"), **the force-update was not performed.** A PO decision is required before push.

No secret values are reproduced anywhere in this report.

## 2. Authorization

Product Owner approved the remediation plan (`docs/audit/cline/CARBONTALLY_GIT_HISTORY_SECRET_REMEDIATION_PLAN.md`) with the explicit manifest: remove exactly the three paths `tools/carbon_data_factory/deeepseek_api.txt`, `.env`, `backend - backup.zip`; `frontend/.env` is OUT OF SCOPE.

## 3. Approved Manifest

```
tools/carbon_data_factory/deeepseek_api.txt
.env
backend - backup.zip
```

## 4. Explicit Exclusions

- `frontend/.env` — NOT removed (preserved in rewritten history; commits `7ca9533`, `06880d0` (rewritten `8b59378`), `cccaa24` (rewritten `a16ba01`) still reference it).
- No `*.env`/`*.zip`/`*backup*`/`*secret*`/`*key*` pattern filtering — exact paths only.

## 5. Pre-Rewrite Baseline

| Item | Value |
|---|---|
| Branch | `main` (only branch) |
| HEAD / origin/main | `9458067c073bdaedae2a621b9cee42e419f14a75` |
| Commit count | 71 (linear, 0 merges) |
| Working tree | 546 modified / 151 deleted / 56 untracked / 0 staged (untouched) |
| Remote | `https://github.com/shomonrobie/CarbonTally.git` (private) |
| Tags | `rc2-final` (`2d23fb8…`), `v2.1-phase4` (`be405d8…`), `v2.1.1-phase3` (`ae1d685…`) |

## 6. Backup / Rollback Artifacts

- `git bundle create /tmp/carbontally_pre_rewrite.bundle --all` — **verified** ("The bundle records a complete history").
- Pre-rewrite SHA records: `/tmp/carbontally_shas_old.txt` (71 SHAs), `/tmp/carbontally_refs_old.txt`, `/tmp/carbontally_heads_old.txt`.
- PO external full-folder backup — untouched (authoritative fallback).
- Rollback method (§22): restore from the bundle/mirror and force-push back to `9458067`.

## 7. Rewrite Environment

- Separate mirror: `git clone --mirror https://github.com/shomonrobie/CarbonTally.git /tmp/carbontally_rewrite.git` (contains only `refs/heads/main` + 3 tags — exactly what GitHub advertises; no checkpoint refs).
- The live development working directory was **never** rewritten.
- Tool: `git-filter-repo` standalone script downloaded to `/tmp/git-filter-repo` (official repository source; version `31ebad4c8fb3`; no system/package installation performed).

## 8. Rewrite Method

```
/tmp/git-filter-repo --path tools/carbon_data_factory/deeepseek_api.txt --path .env \
    --path 'backend - backup.zip' --invert-paths --force
```
- Parsed 71 commits; new history written; old objects repacked/cleaned.
- Result: **70 commits** (the `878bd0f` "Remove exposed API key file" commit became empty after removing the deepseek path and was dropped by filter-repo — expected).
- `frontend/.env` untouched by the filter (exact-path semantics).

## 9. Removed Historical Paths

| Path | Pre-rewrite commits | Post-rewrite |
|---|---|---|
| `tools/carbon_data_factory/deeepseek_api.txt` | `2d23fb8` (add), `878bd0f` (remove) | absent from tree + all reachable history (0 objects) |
| `.env` | `8b59378` (add), `a16ba01` (remove) | absent (0 objects) |
| `backend - backup.zip` | `2d23fb8` (add) → present at `9458067` | absent from tree + history (0 objects); removed from the release tree as intended |

## 10. Old/New Commit Mapping

- Old main HEAD `9458067c073bdaedae2a621b9cee42e419f14a75` → New `0812b015e1184d2b84c525181c85805672dfa1e8`.
- All 70 rewritten commits carry new SHAs; commit count 71 → 70 (one empty commit removed).
- The 3-path removal touched 13 commits' trees (range `2d23fb8`→HEAD) plus deepseek/.env ranges earlier in history; the rewrite re-SHA'd every affected commit.

---

## 11. Old/New Main HEAD

- OLD: `9458067c073bdaedae2a621b9cee42e419f14a75`
- NEW: `0812b015e1184d2b84c525181c85805672dfa1e8` (subject: `feat(v3): commit D20-D37 commercial platform release`)

## 12. Old/New D20–D37 Release SHA

- OLD: `9458067c073bdaedae2a621b9cee42e419f14a75`
- NEW: `0812b015e1184d2b84c525181c85805672dfa1e8` (same release content; only `backend - backup.zip` removed from the tree)

## 13. Tag Rewrite Results

| Tag | OLD SHA | NEW SHA | Type |
|---|---|---|---|
| `rc2-final` | `2d23fb892921cbc41d6c0c20b7660e86fc968178` | `be83cfb988fdd06c44810852e18eb984d7af368c` | lightweight (commit) |
| `v2.1-phase4` | `be405d85b53e6145bc8deff7195d2542eb3cb902` | `7a07dcc75f33a687842479088484b5c17475d089` | annotated (tag object) |
| `v2.1.1-phase3` | `ae1d68557e55704b1f99eea097f62555fd47dc4a` | `7d8d60bb8f14753c11f8496c3b353d57500e3ca7` | annotated (tag object) |

All three tags now point to rewritten commits (which no longer contain the three paths).

## 14. Tree Equivalence Verification

`git ls-tree -r --name-only <old-HEAD> | LC_ALL=C sort` vs `git ls-tree -r --name-only <new-HEAD> | LC_ALL=C sort`:
```
292d291
< backend - backup.zip
```
**Only `backend - backup.zip` differs** (removed). All other 1,508 tracked files are identical. (An earlier locale-collation artifact that appeared as a `backend/data/base.py` "reorder" was confirmed to be a `sort` collation issue and disappears under `LC_ALL=C`.)

## 15. D20–D37 Preservation Verification

All 16 spot-checked release files are present in the new HEAD (`0812b015`): `backend/api/v3_billing.py`, `backend/api/v3_commercial.py`, `backend/services/billing.py`, `backend/data/billing.py`, `backend/domain/billing.py`, `backend/main.py`, `backend/api/router.py`, `frontend/src/App.js`, `frontend/src/v3/customer/BillingPage.jsx`, `frontend/src/v3/ops/CommercialTab.jsx`, D20 + D37-master migrations, `test_billing_core.py`, `test_commercial_settings.py`, D37 master report, public-website audit report. Commit count 70; `git fsck --full` clean.

## 16. Secret Scan Results

**Approved artifacts — GONE:** 0 objects for the three approved paths across all reachable rewritten history; blob-string scan for `sk-…`/`SUPABASE_SERVICE_KEY=`/`RESEND_API_KEY=` value patterns found **no matches in any approved-path blob** (they were removed).

**NEWLY DISCOVERED credential-bearing tracked artifacts (Phase 5 — action: STOP BEFORE PUSH, PO decision required):**

| Path | Evidence (values REDACTED) | In current tree? | In rewritten history? |
|---|---|---|---|
| `create_admin_dashboard.py` | line 163: `REACT_APP_SUPABASE_SERVICE_KEY=<REDACTED>` (literal assignment; 0 `os.getenv` occurrences) | YES — tracked at new HEAD | YES |
| `frontend/.env` | `8b59378` version (blob `67a7e17d`, 273 B): keys `SUPABASE_SERVICE_KEY`, `RESEND_API_KEY` (with values) | NO (removed from HEAD in `a16ba01`) | YES (preserved — out of scope) |
| `docs/sample_bills/*.pdf` (2 files) | matched `sk-…` pattern inside binary PDF content — **probable false positives** (unchanged legitimate sample documents; not treated as confirmed credentials) | YES | YES |

These artifacts existed identically **before** the rewrite (they are unchanged by it); they were newly surfaced by the post-rewrite scan. Per the task, the rewrite is **not** auto-expanded. No secret values are reproduced.

---

## 17. Remote Update Result

**NOT PERFORMED — STOPPED BEFORE PUSH** (Phase 5). The mirror (`/tmp/carbontally_rewrite.git`) contains the verified rewritten history at `0812b015…` but was **not** pushed to `origin`. The planned commands (`git push --force-with-lease origin main` + tag updates) were **not** executed.

## 18. Remote Verification

**NOT APPLICABLE** — no remote update occurred. `origin/main` on GitHub remains at `9458067c073bdaedae2a621b9cee42e419f14a75` (old history). No claim is made that GitHub internals were purged.

## 19. Normal Development Repository Alignment

**NOT PERFORMED** — deferred with the push (alignment must follow the remote update so the dev repo tracks the new canonical history). The live repo remains at `9458067…` with its working tree untouched (546 modified / 151 deleted / 56 untracked / 0 staged).

## 20. Final Git Status (live repo — unchanged)

- HEAD: `9458067c073bdaedae2a621b9cee42e419f14a75`; origin/main identical; `0 0` sync; 71 commits; 0 staged; working tree residue unchanged.
- Mirror (rewritten): `0812b015…`; 70 commits; fsck clean; 3 approved paths absent; tags rewritten.
- Rollback bundle: `/tmp/carbontally_pre_rewrite.bundle` (verified).

## 21. Remaining Security / Repository Items

1. **PO decision required** on the two newly discovered credential-bearing tracked artifacts (`create_admin_dashboard.py` current-tree value; `frontend/.env` 8b59378 version) — whether to (a) extend the rewrite to include them, (b) handle them separately (e.g., scrub `create_admin_dashboard.py` + add it to a future cleanup), or (c) accept.
2. After PO decision: resume the push (`--force-with-lease origin main` + tags), then align the dev repo, then prune local `refs/cline/checkpoints/*` + `gc --prune=now`.
3. Unchanged local `refs/cline/checkpoints/*` (146) still reference old objects locally (never pushed).
4. `backend/carbon_tally_backup*.sql` DB dumps remain in history (out of scope; separate review flagged in the plan).
5. GitHub internal unreachable-object GC is not claimed.

## 22. Rollback Status

Rollback is **available and intact**: `/tmp/carbontally_pre_rewrite.bundle` (complete history at old SHAs), PO external backup, and the untouched live repo at `9458067…`. The mirror can be discarded or kept. No rollback was needed.

## 23. Canonical New Baseline

**Pending PO decision.** The rewritten main at `0812b015e1184d2b84c525181c85805672dfa1e8` (70 commits, 3 approved paths removed) becomes the canonical baseline **only after** the PO decides on the Phase 5 findings and the push is executed. Until then, `9458067…` remains the live/remote baseline.

## 24. Final Recommendation

1. PO reviews the Phase 5 findings (§16) and decides on `create_admin_dashboard.py` and `frontend/.env`.
2. On approval, resume: force-with-lease push of `main` + 3 tags from the mirror → verify remote → align the dev repo (non-destructive) → prune local checkpoint refs → `gc --prune=now`.
3. The rewritten release SHA `0812b015…` becomes the new canonical D20–D37 baseline.

## 25. HARD STOP

- Verified: the live repo and remote are **unchanged** at `9458067c073bdaedae2a621b9cee42e419f14a75`; no push, no force-update, no commit, no application/database/Supabase/Resend/dependency changes, no D38 work, no unrelated cleanup.
- The rewrite is complete and verified **only in the mirror** (`/tmp/carbontally_rewrite.git`).
- **STOP — awaiting Product Owner decision on the Phase 5 findings before any remote update.**

---


---

## 14. PRODUCT OWNER AUTHORIZATION — REMOTE REPLACEMENT COMPLETED

**Authorization received (2026-08-25):** the Product Owner authorized the expanded Git-history remediation to proceed toward remote replacement, with the approved expanded scope: `tools/carbon_data_factory/deeepseek_api.txt`, `.env`, `backend - backup.zip`, `create_admin_dashboard.py`, `frontend/.env`, and the verified rewritten mirror candidate `d4dcca1eb11f86bcae497815c8592d688a7e305f`.

## 15. FINAL PRE-PUSH VERIFICATION — PASS

| Gate | Result |
|---|---|
| 1. Live remote state (fetched) | ✅ origin/main = `9458067c073bdaedae2a621b9cee42e419f14a75`; no unexpected remote commits |
| 2. Rewritten mirror | ✅ `d4dcca1e…`; 70 commits; `git fsck --full` clean; 0 dangling credential-bearing objects for approved paths |
| 3. Five approved paths absent from rewritten reachable history | ✅ 0 objects each (`create_admin_dashboard.py` removed in full → no hard-coded service credential exists anywhere) |
| 4. No unexpected removals | ✅ byte-sorted tree equivalence vs `9458067` = exactly 2 removals (`backend - backup.zip`, `create_admin_dashboard.py`); all other 1,507 files identical |
| 5. Tags rewritten; no secret paths in tag histories | ✅ `rc2-final`→`eed55d62…`, `v2.1-phase4`→`16d5519d…`, `v2.1.1-phase3`→`0c55c8be…`; 0 secret-path objects each |
| 6. Rollback bundle | ✅ `/tmp/carbontally_pre_rewrite.bundle` exists, intact (135,395,572 bytes), NOT deleted |
| 7. Dev repository safety | ✅ dev working tree untouched (0 staged; 546 modified / 151 deleted / 58 untracked preserved) |

**PRE-PUSH VERIFICATION: PASS**

- **OLD REMOTE MAIN:** `9458067c073bdaedae2a621b9cee42e419f14a75`
- **NEW REMOTE MAIN:** `d4dcca1eb11f86bcae497815c8592d688a7e305f`
- **OLD TAG SHAs:** `rc2-final` `2d23fb89…` · `v2.1-phase4` `be405d85…` · `v2.1.1-phase3` `ae1d6855…`
- **NEW TAG SHAs:** `rc2-final` `eed55d62ee9f103279d0d2a94006952a517d3bde` · `v2.1-phase4` `16d5519de621bc9c28b5a9e65efa851be8b07d5f` (peels to `aa4114f4…`) · `v2.1.1-phase3` `0c55c8be5bace961eb00a8158f776812e0ce74b8` (peels to `822936b2…`)
- **D20-D37 PRESERVATION:** **PASS**
- **SECRET PATH REMOVAL:** **PASS**
- **ROLLBACK:** **PASS**

## 16. REMOTE REPLACEMENT (force-with-lease)

Executed from `/tmp/carbontally_rewrite_expanded.git` (origin re-added; `git fetch --no-tags origin main` recorded the lease baseline `9458067…`).

| Ref | Push result |
|---|---|
| `refs/heads/main` | `+ 9458067...d4dcca1 main -> main (forced update)` — `--force-with-lease=refs/heads/main:9458067…` |
| `refs/tags/rc2-final` | `+ 2d23fb8...eed55d6 rc2-final -> rc2-final (forced update)` — lease `2d23fb89…` |
| `refs/tags/v2.1-phase4` | `+ be405d8...16d5519 v2.1-phase4 -> v2.1-phase4 (forced update)` — lease `be405d85…` |
| `refs/tags/v2.1.1-phase3` | `+ ae1d685...0c55c8b v2.1.1-phase3 -> v2.1.1-phase3 (forced update)` — lease `ae1d6855…` |

`git push --force` was NOT used; every ref used **force-with-lease** with the exact expected old SHA. No remote tags were deleted.

## 17. POST-PUSH REMOTE VERIFICATION — PASS

- Immediate fetch: `origin/main` = `d4dcca1eb11f86bcae497815c8592d688a7e305f` ✅
- `git rev-list --left-right --count origin/main...HEAD` = `0 0` (synchronized) ✅
- All three rewritten tags point to the expected rewritten objects; both annotated tags peel to commits that are ancestors of rewritten HEAD (`aa4114f4…`, `822936b2…`) ✅
- Five approved secret-bearing paths: **0 objects reachable** in the remote rewritten history (mirror refs = remote refs) ✅
- `git fsck --full` clean; old `9458067…` reachable by no ref (dangling object in the local mirror only, purged by the documented gc) ✅
- Remote `ls-remote`: only `main` + 3 tags — no unexpected refs ✅

---

## 18. D20-D37 PRESERVATION — PASS

Confirmed post-push: byte-sorted tree equivalence vs old `9458067` shows **exactly 2 removals** (`backend - backup.zip`, `create_admin_dashboard.py`); all other 1,507 tracked files identical. 13/13 spot-checked release files present (billing api/service/data/domain, `main.py`, `router.py`, `App.js`, `BillingPage.jsx`, `CommercialTab.jsx`, D37 migration, tests, reports). No application files, migrations, frontend pages, backend modules, tests, schema, RLS policies, or documentation were removed.

## 19. SECRET-PATH VERIFICATION — PASS

| Path | Objects in rewritten reachable history |
|---|---|
| `tools/carbon_data_factory/deeepseek_api.txt` | 0 |
| `.env` | 0 |
| `backend - backup.zip` | 0 |
| `create_admin_dashboard.py` | 0 |
| `frontend/.env` | 0 |

`create_admin_dashboard.py` was **removed from all rewritten history** (obsolete/unused per the prior investigation), so no version of the hard-coded Supabase service credential exists anywhere in the rewritten repository — stronger than a scrubbed retained file.

## 20. ROLLBACK — PASS

`/tmp/carbontally_pre_rewrite.bundle` exists and is intact (135,395,572 bytes) — complete pre-rewrite history at old SHAs. **NOT deleted, NOT overwritten.** PO external full-folder backup untouched. Prior 3-path mirror `/tmp/carbontally_rewrite.git` (HEAD `0812b015…`) retained.

## 21. DEV-REPOSITORY ALIGNMENT — PROCEDURE PROVIDED, NOT EXECUTED

The developer working tree (546 modified EOL-only files, 151 deleted skill/artifact files, 58 untracked incl. both audit reports) contains unrelated/uncommitted work and was **not touched** during this phase. Per PO instruction, the safe non-destructive alignment procedure is provided below to run when the developer is ready — **no `git clean`, no `git reset --hard`, nothing destroyed**:

```
cd /home/shomonrobie/carbon_tally
git fetch origin
# Non-destructive alignment: moves main + index to the rewritten remote, leaves all working-tree files intact
git reset --mixed origin/main     # NOT --hard; no file is overwritten or deleted
# Final remediation step: remove the two credential-bearing files that become untracked after alignment
rm -f 'backend - backup.zip' create_admin_dashboard.py
# Verify
git status --short | wc -l   # expect 546 M + 151 D + 58 ?? (net minus the two removed files)
```

**Must be preserved manually (do not delete):** all 546 modified files (EOL normalization), all 151 deleted paths (prior cleanup), all 58 untracked files including both audit reports. After `reset --mixed`, the 546 modifications / 151 deletions still appear — their diff base is simply the new rewritten HEAD.

**Because alignment was not executed, local `refs/cline/checkpoints/*` pruning and the object `gc --prune=now` remain DEFERRED** (safe only after alignment is confirmed complete).

## 22. FINAL CANONICAL BASELINE

- **Remote (GitHub) `main`:** `d4dcca1eb11f86bcae497815c8592d688a7e305f` (70 commits)
- Release subject: `feat(v3): commit D20-D37 commercial platform release`
- Tags: `rc2-final` → `eed55d62…` · `v2.1-phase4` → `16d5519d…` (peel `aa4114f4…`) · `v2.1.1-phase3` → `0c55c8be…` (peel `822936b2…`)
- Old baseline superseded: `9458067c073bdaedae2a621b9cee42e419f14a75` (available only in the rollback bundle)

## 23. REMAINING CLEANUP (deferred — awaiting further PO instruction)

1. Dev-repo alignment via the §21 procedure (to be run by the developer/PO).
2. After alignment: local `refs/cline/checkpoints/*` (146 refs) prune + `git gc --prune=now` in the dev repo.
3. Mirror cleanup: `git gc --prune=now` in `/tmp/carbontally_rewrite_expanded.git` (purges the dangling old commit object).
4. GitHub internal unreachable-object GC is not claimed (GitHub-managed; runs on its own schedule).

## 24. HARD STOP

Remote replacement and post-push verification are **COMPLETE**. **STOPPED** — no application code, database, RLS, billing, D38, onboarding, or website work was performed, and none will begin until the separate **CARBONTALLY V3 — IDENTITY, ACTOR, WORKSPACE & ONBOARDING AUDIT** task is instructed by the Product Owner.

---

*End of updated execution report. SECRET VALUE NOT REPRODUCED.*
