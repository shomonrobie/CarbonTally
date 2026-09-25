# P17 PO Document Git Preservation Report

**Document ID:** `CT-PO-P17-GIT-PRESERVE-03-20260925`
**Task ID:** `P17-GIT-PRESERVE-03-20260925`
**Date:** 2026-09-25
**Operation:** scope-limited Git preservation of exactly three Product-Owner governance documents
**No development · no architecture change · no reconciliation · no code change · no database change**

---

## 1. Task Identity

| Item | Value |
|---|---|
| Task ID | `P17-GIT-PRESERVE-03-20260925` |
| Date | 2026-09-25 |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| Remote | `github` — `https://github.com/shomonrobie/CarbonTally.git` |

### 1.1 Pre-flight repository verification

| Check | Expected | Observed | Result |
|---|---|---|---|
| `pwd` / `git rev-parse --show-toplevel` | `/home/shomonrobie/ct_93d5cdd` | `/home/shomonrobie/ct_93d5cdd` | PASS |
| `git branch --show-current` | `p8-release-reconciled` | `p8-release-reconciled` | PASS |
| `git rev-parse HEAD` | already-preserved state `aced6e7…` | `aced6e7e77a31f314365693a36b839c8643a6e14` | PASS |
| Remote `github` available / unambiguous | yes | present and reachable | PASS |

### 1.2 Whitelist path discrepancy found and resolved (DISCLOSED)

The task whitelist item 3 was stated **without its directory prefix**:

```
CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md        <- does NOT exist
docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md   <- exists (20,237 bytes)
```

Verified facts:

* The stated root-level path does **not** exist (`[ -f ]` → MISSING; `ls CarbonTally*.md` → no such file).
* `find . -name 'CarbonTally_PO_Carbon_Accounting_Management_Decision*' -not -path './.git/*'` returns **exactly one**
  match — `./docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md`.
* The previous preservation report (P17-GIT-PRESERVE-02) also named that same `docs/architecture/` path as the
  unprotected PO document.

**Resolution:** because the intended file is unambiguous (one match only, same basename, same document) and because
the stated path could not be staged at all, the correctly-located file was staged and committed. **Exactly three
files** were staged and committed — no fourth file, and no file outside the three intended documents. Had there been
more than one candidate for that basename, the operation would have been stopped and reported instead.

---

## 2. Starting State

| Item | Value |
|---|---|
| Starting HEAD | `aced6e7e77a31f314365693a36b839c8643a6e14` |
| Starting remote SHA (`github/p8-release-reconciled`) | `aced6e7e77a31f314365693a36b839c8643a6e14` (matches expected starting point exactly) |
| Divergence check | `git merge-base github/p8-release-reconciled HEAD` = `aced6e7…` → **no divergence**; `unpushed = 0` |
| Working tree | **1 modified** (`.gitignore`, pre-existing) · **18 untracked** · **0 staged** |

---

## 3. Exact Whitelist

The only files authorised by the task:

1. `docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md`
2. `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md`
3. `CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` *(corrected at execution to
   `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` — see §1.2)*

---

## 4. Verification of the Three Files

| # | File (as executed) | Exists | Size | Initial Git state | Tracked? | In local HEAD? | In remote? | Preservation required |
|---|---|---|---|---|---|---|---|---|
| 1 | `docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md` | YES | 78,724 B | untracked (`??`) | NO | NO | NO | **YES** |
| 2 | `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | YES | 32,082 B | untracked (`??`) | NO | NO | NO | **YES** |
| 3 | `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | YES | 20,237 B | untracked (`??`) | NO | NO | NO | **YES** |

Checks used: `[ -f ]`, `git ls-files --error-unmatch` (tracked/untrusted test), `git cat-file -e HEAD:<path>`,
`git cat-file -e github/p8-release-reconciled:<path>`.

**Result:** all three were untracked, absent from local HEAD and absent from the remote — i.e. **none was already
preserved**, and none required a duplicate copy or any modification. **No file content was edited, normalised,
reformatted, reordered or regenerated** at any point.

---

## 5. Staging Verification

Staging command (explicit paths only — no `.`, no `-A`, no `--all`, no wildcards):

```
git add -- docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md \
           docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md \
           docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md
```

`git diff --cached --name-status`:

```
A  docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md
A  docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md
A  docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md
```

`git diff --cached --stat`: **3 files changed, 4315 insertions(+)**

**Explicit statement: only the three whitelisted documents were staged.** Verified by count and by name:
`staged_A = 3`, `staged_M = 0`, `unstaged_M = 1` (`.gitignore`, not staged), `untracked = 15`
(18 − 3 = 15, exactly the three files moving from untracked to staged). No other path appeared staged at any point.

---

## 6. Commit

| Item | Value |
|---|---|
| Commit SHA | `5eaf8d0c185633448d8a5e7fd45295292abf682a` (short `5eaf8d0`) |
| Commit message | `docs(po): preserve p17 governance decisions and ux standard` |
| Parent | `aced6e7e77a31f314365693a36b839c8643a6e14` (previous preserved HEAD — **not** amended) |
| Files in commit | **exactly 3** |
| Lines | 4,315 insertions, 0 deletions |
| Amend used | **NO** |
| `git commit -am` used | **NO** |
| P17 architecture commit modified | **NO** |

`git diff-tree --no-commit-id --name-status -r HEAD`:

```
A  docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md
A  docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md
A  docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md
```

`files_in_commit = 3` — **nothing else entered the commit.** No application code, no migration, no UI, no
configuration, and no P17-ARCH-01 architecture artifact.

---

## 7. Push

| Item | Value |
|---|---|
| Remote | `github` (`https://github.com/shomonrobie/CarbonTally.git`) |
| Branch / refspec | `p8-release-reconciled:p8-release-reconciled` (explicit refspec — the configured upstream `origin` is broken, see §9) |
| Command | `git push github p8-release-reconciled:p8-release-reconciled` |
| Previous remote SHA | `aced6e7e77a31f314365693a36b839c8643a6e14` |
| New remote SHA | `5eaf8d0c185633448d8a5e7fd45295292abf682a` |
| Server output | `To https://github.com/shomonrobie/CarbonTally.git` / `aced6e7..5eaf8d0  p8-release-reconciled -> p8-release-reconciled` |
| Fast-forward result | **YES** — two-dot update (`aced6e7..5eaf8d0`), **no** `+` prefix, **no** "forced update" message |
| Exit status | `0` |
| Force / force-with-lease | **NOT USED** |

---

## 8. Independent Verification of the Remote

Verification was performed against the **server**, not merely against a local tracking ref:

| # | Evidence | Result |
|---|---|---|
| 1 | `git ls-remote github refs/heads/p8-release-reconciled` | `5eaf8d0c185633448d8a5e7fd45295292abf682a  refs/heads/p8-release-reconciled` |
| 2 | `git fetch github p8-release-reconciled` | succeeded |
| 3 | `git rev-parse github/p8-release-reconciled` | `5eaf8d0c185633448d8a5e7fd45295292abf682a` |
| 4 | Previous remote HEAD preserved | `git merge-base --is-ancestor aced6e7… github/p8-release-reconciled` → **YES** |
| 5 | New commit reachable remotely | remote ref equals `5eaf8d0…` → **YES** |
| 6 | File 1 present in the remote commit | `git cat-file -e github/p8-release-reconciled:<path>` → **PRESENT_REMOTE** |
| 7 | File 2 present in the remote commit | **PRESENT_REMOTE** |
| 8 | File 3 present in the remote commit | **PRESENT_REMOTE** |
| 9 | No unrelated files pushed | `git diff-tree --no-commit-id --name-only -r github/p8-release-reconciled \| wc -l` → **3** |
| 10 | Nothing left unpushed | `git rev-list --count github/p8-release-reconciled..HEAD` → **0** |

**Remote verification: PASS.**

---

## 9. Untouched Work

| Statement | Status |
|---|---|
| `.gitignore` not modified by this task | **CONFIRMED** — it was already ` M` before the task began (first `git status` of the session) and remains uncommitted and unedited |
| `.gitignore` not staged | **CONFIRMED** (`staged_M = 0`) |
| Other untracked files not staged | **CONFIRMED** — 18 untracked → 15 untracked; the delta is exactly the 3 preserved files |
| Other untracked files not deleted | **CONFIRMED** — all remaining 15 are still present |
| No unrelated files committed | **CONFIRMED** — `files_in_commit = 3` |
| No application code changed | **CONFIRMED** — 0 paths under `backend/`, `frontend/`, `supabase/`, `admin/`, `src/` in the commit |
| No migrations created or changed | **CONFIRMED** |
| No UI changed | **CONFIRMED** |
| No P17 implementation started | **CONFIRMED** — no P17-A work, no code, no reconciliation |
| P17 architecture artifacts untouched | **CONFIRMED** — contract, phase plan, Scope 2 matrix, Scope 3 matrix, acceptance matrix and schema delta were not modified |
| `git clean` / `reset --hard` / `reset --mixed` / `stash --all` / `rebase` / `merge` / `cherry-pick` used | **NO to all** |
| `git add .` / `git add -A` / `git add --all` / `git commit -am` used | **NO to all** |
| Other repository (`/home/shomonrobie/carbon_tally`) touched | **NO** |
| Repository configuration changed | **NO** — the broken `origin` remote was left exactly as found |

Remaining untracked files after this task (15): `.costrict/`, `8`, `=`,
`costrict-p3-ov-01-independent-re-verification.txt`, four `docs/ChatGPT/*` files,
`docs/architecture/CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md`,
`docs/architecture/CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md`,
`docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md`,
`docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`,
`docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`,
`docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md`,
`docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`.

These were **not** touched and are **not** protected by any commit — a deliberate, documented residual risk for a
future scope-limited preservation task (never via `git add -A`).

**Note (unchanged from P17-GIT-PRESERVE-02):** `branch.p8-release-reconciled.remote = origin`, and `origin` points at
`/tmp/ct_step2`, which does not exist. Pushes therefore use the explicit `github` remote with an explicit refspec.
Changing the upstream would be a repository-configuration change and was **not** performed.

---

## 10. Production Safety

| Statement | Status |
|---|---|
| Production contacted | **NO** |
| Production deployed | **NO** |
| Production database changed | **NO** |
| Production migration run | **NO** |
| Production infrastructure modified | **NO** |
| Production APIs called | **NO** |

The only remote operations were Git reads (`fetch`, `ls-remote`, and `cat-file` against the remote ref) plus one
history-preservation write (`push`) to the project's own GitHub repository.

---

## 11. Final Verdict

**P17_PO_DOCUMENTS_PRESERVED**

All three Product-Owner governance documents — previously untracked and unprotected — are now committed and confirmed
present in the remote `github/p8-release-reconciled` branch at
`5eaf8d0c185633448d8a5e7fd45295292abf682a`, via a verified fast-forward push containing exactly those three files and
nothing else.

---

## Document Control

**Document:** `CT-PO-P17-GIT-PRESERVE-03-20260925`
**Task:** `P17-GIT-PRESERVE-03-20260925`
**PO-document commit:** `5eaf8d0c185633448d8a5e7fd45295292abf682a` (exactly 3 files)
**Remote before → after:** `aced6e7e77a31f314365693a36b839c8643a6e14` → `5eaf8d0c185633448d8a5e7fd45295292abf682a`
**Other files staged/committed:** NONE · **Force push:** NO · **History rewritten:** NO · **Production:** NOT CONTACTED
**This report** is committed as a **separate, report-only commit** and is **not** part of the three-document
preservation commit.


