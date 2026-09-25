# P17 Full Branch Preservation Report

**Document ID:** `CT-PO-P17-GIT-PRESERVE-02-20260925`
**Task ID:** `P17-GIT-PRESERVE-02-20260925`
**Date:** 2026-09-25
**Operation type:** Git history preservation (push) — **no development, no code change, no migration, no database change**

---

## 1. Task Identity

| Item | Value |
|---|---|
| Task ID | `P17-GIT-PRESERVE-02-20260925` |
| Date | 2026-09-25 |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD before operation | `d24a5671d536c4394145f85bb739181669382c6c` |
| HEAD after operation | `d24a5671d536c4394145f85bb739181669382c6c` (unchanged — the push transmitted commits; it created none) |
| Production contacted | **NO** |

### 1.1 Pre-flight identity verification (step 3)

| Check | Expected | Observed | Result |
|---|---|---|---|
| `pwd` / `git rev-parse --show-toplevel` | `/home/shomonrobie/ct_93d5cdd` | `/home/shomonrobie/ct_93d5cdd` | PASS |
| `git branch --show-current` | `p8-release-reconciled` | `p8-release-reconciled` | PASS |
| `git rev-parse HEAD` | P17 checkpoint | `d24a5671d536c439414f85bb739181669382c6c` | PASS (see §1.2) |

### 1.2 Discrepancy found and resolved — malformed P17 SHA in the task header (DISCLOSED)

The task header states the P17 checkpoint as:

```
d24a5671d536c439414f85bb739181669382c6c      <- 39 characters (INVALID as a Git object name)
```

The actual HEAD is:

```
d24a5671d536c4394145f85bb739181669382c6c      <- 40 characters (valid)
```

The header string is **one character short** — it is missing the `5` at offset 19. Evidence:

* Byte comparison: `expected_len=39`, `actual_len=40`, `SHA_MATCH=DIFFERENT`, with a single-character insertion
  offset from index 19; `git` reported `fatal: Not a valid object name` for the header string, because a 39-hex
  object id cannot exist.
* The intended commit is nonetheless **unambiguous**, verified by five independent properties:

| Property | Value | Matches task expectation |
|---|---|---|
| Short SHA | `d24a567` | YES (`d24a567…`) |
| Commit message | `docs(p17): establish scope2 scope3 accounting architecture contract` | YES (P17 architecture contract) |
| **Sole parent** | `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be` | YES — exactly the P16 checkpoint named in the header |
| Files introduced | the six P17 architecture artifacts (3,202 insertions, 6 files) | YES |
| Author / date | shomonrobie / 2026-09-25 13:38:42 +0600 | YES (same session as P17) |

**Conclusion:** the header SHA is a one-character transcription error in the task prompt, not a repository
discrepancy. There was nothing in the repository to repair, and no repair was attempted. Preservation proceeded
against the real commit. Had HEAD been a *different commit*, the operation would have been stopped (stop condition 3).

---

## 2. Remote Before Preservation

| Item | Value |
|---|---|
| Remote name | **`github`** |
| Remote URL | `https://github.com/shomonrobie/CarbonTally.git` |
| Remote branch | `refs/heads/p8-release-reconciled` |
| Remote SHA (before) | `790923f19b5087d610f8ae9e7df442017ccfbf2c` |
| Verified by | `git ls-remote github refs/heads/p8-release-reconciled` **and** `git fetch github p8-release-reconciled` |

### 2.1 Remote configuration finding — the tracked upstream is a DEAD LOCAL PATH

The repository has **two** configured remotes:

| Remote | URL | State |
|---|---|---|
| `origin` | `/tmp/ct_step2` (local path) | **BROKEN** — `ls: cannot access '/tmp/ct_step2': No such file or directory` |
| `github` | `https://github.com/shomonrobie/CarbonTally.git` | healthy |

And the branch is configured to track the broken one:

```
git config --get branch.p8-release-reconciled.remote  ->  origin
git config --get branch.p8-release-reconciled.merge   ->  refs/heads/p8-release-reconciled
git branch -vv  ->  p8-release-reconciled d24a567 [origin/p8-release-reconciled: ahead 137]
```

**Findings that materially change the task's starting assumptions:**

1. `origin` (which the branch "tracks") is an ephemeral `/tmp` worktree path that no longer exists. It is **not** a
   preservation target: pushing to it would neither preserve anything durably nor reach any external host.
2. The stale `origin/p8-release-reconciled` ref reports `93d5cdd` — this is the "previously reported published remote
   tip". It is **not** the real remote tip.
3. The real remote (`github`) is at **`790923f`**, which is **112 commits ahead of `93d5cdd`** and a strict descendant
   of it. So 112 commits of P12 work were already published; the genuinely unpublished range is far smaller than the
   "ahead 137" figure implies.
4. `github` was therefore determined to be the only remote capable of satisfying the task objective, and it is a
   **configured** remote that already carries the branch — it was not invented.
5. Because the branch's upstream is broken, a bare `git push` would have targeted `origin`. All pushes were issued
   with an **explicit remote and refspec**.

**No remote configuration was modified** (setting upstream tracking or deleting the dead `origin` would be a
repository-configuration change, outside the scope of a preservation task).

---

## 3. Local Branch State

| Item | Value |
|---|---|
| Local HEAD | `d24a5671d536c439414f85bb739181669382c6c` |
| Branch | `p8-release-reconciled` |
| Working-tree status | **1 modified, 18 untracked, 0 staged** |
| Modified file | `.gitignore` (pre-existing modification — **not** committed) |
| Untracked files | 18 (pre-existing — **none** committed, **none** deleted) |
| Staged changes | **0** (nothing staged before the report commit in §14) |

Untracked files present before the operation (all left untouched):

```
.costrict/
8
=
costrict-p3-ov-01-independent-re-verification.txt
docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md
docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22-Insight-Strategy-v2.md
docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22.md
docs/ChatGPT/carbontally_handoff.md
docs/architecture/CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md
docs/architecture/CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md
docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md
docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md
docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md
docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md
docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md
docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md
docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md
docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md
```

> The previous report recorded 17 untracked files; the count is now **18** because an additional **Product-Owner**
> document (`CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md`) appeared in the working tree between
> sessions. It was **not** created by this task and was **not** committed. A Git push transmits **commits**, never
> untracked files, so its presence does not affect preservation — it is recorded because it is not yet protected by
> any commit.

---

## 4. Complete Unpublished Commit Range

Range: `790923f19b5087d610f8ae9e7df442017ccfbf2c..d24a5671d536c439414f85bb739181669382c6c`

| Metric | Value |
|---|---|
| `git rev-list --count 790923f..HEAD` | **25** |
| `git diff --stat 790923f..HEAD` | **71 files changed, 22,125 insertions(+), 27 deletions(-)** |

**Complete inventory — every commit, oldest first (no commit omitted):**

| # | SHA | Date | Author | Message | Programme | From prior reports |
|---|---|---|---|---|---|---|
| 1 | `cbadc23` | 2026-09-24 | Cline | docs(p12): investor demo data journey audit (CSV PASS / PDF PARTIAL, supplier reuse NOT IMPLEMENTED) | P12 | No |
| 2 | `327f8e3` | 2026-09-24 | Cline | docs(p12): link demo-journey audit addendum into step-2 final verification record | P12 | No |
| 3 | `25873f6` | 2026-09-24 | Cline | docs(p12): fix displaced evidence-manifest table row in demo-journey audit | P12 | No |
| 4 | `3134a59` | 2026-09-24 | Cline | docs(p12-doc-03): canonical synthetic PDF corpus for investor demo (Robinsons Recycling Services Ltd -> Sustainable Direct Group, FY2025+FY2026) | P12 | No |
| 5 | `0fee936` | 2026-09-24 | Cline | docs(p12-doc-03): record actual after-SHA in canonical corpus report | P12 | No |
| 6 | `feb996c` | 2026-09-24 | Cline | test(p12-gap-02): canonical PDF extraction, supplier attribution and multi-year reuse acceptance (supplier 0/6, line-items 0/6, reuse FAIL) | P12 | No |
| 7 | `7594e61` | 2026-09-24 | Cline | docs(p12-decision-01): PDF extraction, waste semantics, supplier resolution and propagation product contract (design only, no implementation) | P12 | No |
| 8 | `ad07cd4` | 2026-09-24 | Cline | feat(p12-impl-01): PDF extraction foundation - supplier/customer headers, billing period, date normalisation, trustworthy line items | P12 | No |
| 9 | `6462f47` | 2026-09-24 | Cline | docs(p12-data-01): canonical PDF precision contract - 3-layer forensic analysis, recommended contract C+E, no code change | P12 | No |
| 10 | `6c98d8f` | 2026-09-24 | shomonrobie | feat(p12): implement auditable waste and supplier resolution | P12-IMPL-02 | No |
| 11 | `b52635b` | 2026-09-24 | shomonrobie | docs(p12): record P12-IMPL-02 commit hash in report and artifact | P12 | No |
| 12 | `b1a313d` | 2026-09-24 | shomonrobie | docs(p14): carbon accounting competitive capability and scope 1/2/3 coverage audit (read-only) | P14 | No |
| 13 | `00c0397` | 2026-09-24 | shomonrobie | docs(p16): core accounting journeys - live-path evidence and defect findings | P16 | No |

| 14 | `0fe349f` | 2026-09-24 | shomonrobie | docs(p16): record core accounting journeys commit hash | P16 | No |
| 15 | `a12d156` | 2026-09-24 | shomonrobie | fix(p16r): operator factor precedence, factor safety, supplier propagation, FY year governance | P16-R1/R2/R3 | No |
| 16 | `2b5f46f` | 2026-09-24 | shomonrobie | docs(p16r): record remediation commit hash | P16 | No |
| 17 | `5cb234d` | 2026-09-24 | shomonrobie | chore(p16r2): grant can_review to internal admin reviewer; RD-1/RD-3 live acceptance | P16-R2 | No |
| 18 | `54235cc` | 2026-09-24 | shomonrobie | docs(p16r2): record acceptance-completion commit hash | P16 | No |
| 19 | `b87ff38` | 2026-09-24 | shomonrobie | fix(p16r3): resolve extraction item by document identity, not file name | P16-R3 | No |
| 20 | `fb4301e` | 2026-09-24 | shomonrobie | fix(p16r4): authorize PO-ratified validated -> calculated transition | P16-R4 | No |
| 21 | `155013d` | 2026-09-25 | shomonrobie | fix(p16): final acceptance closure | P16-R5 | No |
| 22 | `1e10023` | 2026-09-25 | shomonrobie | fix(p16): close final acceptance gates | P16-R6 | No |
| 23 | `6eedb7b` | 2026-09-25 | shomonrobie | fix(p16): close idempotency and final isolation gates | P16-R7 | No |
| 24 | `9c96cbf` | 2026-09-25 | shomonrobie | test(p16): complete full regression classification and close P16 acceptance | **P16 FINAL VERIFICATION** | Yes |
| 25 | `d24a567` | 2026-09-25 | shomonrobie | docs(p17): establish scope2 scope3 accounting architecture contract | **P17 ARCHITECTURE** | Yes |

**Classification summary:** P17 = 1 · P16 = 12 · P14 = 1 · P12 = 11 · unresolved/suspicious = **0**

**Suspicious-commit check (step 12):** every commit is an ordinary project commit by a known project author
(`shomonrobie`, `Cline`), with a coherent message belonging to a known programme, on a single linear chain, each a
strict descendant of the remote tip. **No commit was found that is accidental, generated, unrelated or inconsistent
with the expected project history.** Nothing was deleted or rewritten. No stop condition was triggered.

**Linearity:** `git merge-base 790923f HEAD` = `790923f19b5087d610f8ae9e7df442017ccfbf2c` — the remote tip is the
direct merge base, so the range is a **simple linear fast-forward** with no merge commits requiring reconciliation.

---

## 5. P16 Preservation

**P16 checkpoint:** `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be`
(`test(p16): complete full regression classification and close P16 acceptance`)

| Verification | Command | Result |
|---|---|---|
| Exists in local branch history | `git merge-base --is-ancestor 9c96cbf… p8-release-reconciled` | **YES — ancestor** |
| Was in the unpublished range before push | present in `git log 790923f..HEAD` (position 24 of 25) | **YES** |
| Was absent from the remote before push | `git merge-base --is-ancestor 9c96cbf… 790923f` | **NOT in remote tip** — i.e. genuinely unpublished |
| Reachable from the remote AFTER push | `git merge-base --is-ancestor 9c96cbf… github/p8-release-reconciled` | **YES** |
| Sole parent of the P17 commit | `git rev-parse HEAD^` | `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be` |
| Rewritten / amended | — | **NO** |

**Conclusion:** the P16 final verification checkpoint was unpublished, is now published, and remains reachable. It was
neither rewritten nor replaced.

---

## 6. P17 Preservation

**P17 checkpoint (actual HEAD):** `d24a5671d536c439414f85bb739181669382c6c`
(`docs(p17): establish scope2 scope3 accounting architecture contract`)

(For the one-character discrepancy between this value and the literal in the task header, see §1.2.)

| Verification | Command | Result |
|---|---|---|
| Is the final pushed HEAD | `git rev-parse HEAD` = `git rev-parse github/p8-release-reconciled` | **YES — identical** |
| Descendant of the P16 checkpoint | `git merge-base --is-ancestor 9c96cbf… d24a567` | **YES** |
| Reachable from the remote AFTER push | `git merge-base --is-ancestor d24a567… github/p8-release-reconciled` | **YES** |
| Amended / replaced | — | **NO** (the commit was transmitted byte-identically) |

**Chain confirmed:**

```
P16 FINAL (9c96cbf, parent of HEAD)
        ↓
P17 ARCHITECTURE (d24a567)
        ↓
CURRENT HEAD (d24a567 — the push created no new commit on the branch)
```

---

## 7. P17 Artifacts Verified

All six artifacts are present in the tree of commit `d24a567` (verified with `git ls-tree -r --name-only d24a567`):

| # | Path | Present |
|---|---|---|
| 1 | `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | YES |
| 2 | `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` | YES |
| 3 | `docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json` | YES |
| 4 | `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` | YES |
| 5 | `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` | YES |
| 6 | `docs/architecture/artifacts/p17_schema_delta_20250925.md` | YES |

The commit introduced exactly these six files (`git show --stat d24a567` → `6 files changed, 3202 insertions(+)`).
**None was modified by this task.**

---

## 8. Push Operation

| Item | Value |
|---|---|
| Remote | `github` (`https://github.com/shomonrobie/CarbonTally.git`) |
| Branch / refspec | `p8-release-reconciled:p8-release-reconciled` (explicit refspec — required because the configured upstream `origin` is broken) |
| Command | `git push github p8-release-reconciled:p8-release-reconciled` |
| Old remote SHA | `790923f19b5087d610f8ae9e7df442017ccfbf2c` |
| New remote SHA | `d24a5671d536c439414f85bb739181669382c6c` |
| Commits pushed | **25** |
| Server output | `To https://github.com/shomonrobie/CarbonTally.git` / `790923f..d24a567  p8-release-reconciled -> p8-release-reconciled` |
| Fast-forward confirmation | **YES** — the update was reported as a two-dot range (`790923f..d24a567`), with **no** `+` prefix and **no** "forced update" message |
| Exit status | `0` |

A two-dot (`A..B`) update line means the remote ref advanced by fast-forward. A non-fast-forward or forced update
would have been reported as `+ A...B (forced update)` and would have been **rejected** by Git absent `--force`,
which was never used.

---

## 9. Post-Push Verification

Independent verification performed **against the server**, not merely against local tracking refs:

| # | Evidence | Result |
|---|---|---|
| 1 | `git ls-remote github refs/heads/p8-release-reconciled` | `d24a5671d536c439414f85bb739181669382c6c  refs/heads/p8-release-reconciled` |
| 2 | `git fetch github p8-release-reconciled` | succeeded (`From https://github.com/shomonrobie/CarbonTally`) |
| 3 | `git rev-parse github/p8-release-reconciled` | `d24a5671d536c439414f85bb739181669382c6c` |
| 4 | `git merge-base --is-ancestor 9c96cbf… github/p8-release-reconciled` | YES (P16 reachable remotely) |
| 5 | `git merge-base --is-ancestor d24a567… github/p8-release-reconciled` | YES (P17 reachable remotely) |
| 6 | `git rev-list --count github/p8-release-reconciled..HEAD` | **0** — nothing remains unpublished |
| 7 | `git rev-list --count 790923f..d24a567` | **25** — the complete intended range |

`git ls-remote` reads the ref directly from the server, so the remote branch state is confirmed rather than inferred
from a stale local ref.

---

## 10. Untracked/Unrelated Work Safety

| Requirement | Status |
|---|---|
| `git add -A` used | **NO** |
| `git add .` used | **NO** |
| `git clean` used | **NO** |
| `git reset --hard` used | **NO** |
| `git stash --all` used | **NO** |
| Unrelated files committed | **NO** — the only commit created by this task contains one file (§14) |
| Pre-existing untracked files deleted | **NO** — all 18 remain present |
| Pre-existing unrelated modification (`.gitignore`) committed | **NO** — still shown as ` M` and untouched |
| Another repository touched | **NO** — `/home/shomonrobie/carbon_tally` was neither read from, written to, committed, merged nor pushed |
| Files added to `.agents/skills/**` in the other workspace | **NO** |

**Critical distinction observed:** a Git push transmits **commits**, never ordinary untracked working-tree files.
Therefore preservation was achieved entirely by transmitting the existing commit chain, and no catch-all commit was
created to "capture" untracked files.

---

## 11. History Integrity

| Integrity property | Status |
|---|---|
| Force push (`--force`) | **NO** |
| Force-with-lease (`--force-with-lease`) | **NO** |
| Rebase | **NO** |
| Reset (`--hard` or otherwise) | **NO** |
| `git commit --amend` | **NO** |
| History rewrite of any kind | **NO** |
| Merge performed | **NO** |
| Existing commits deleted | **NO** |
| Branches switched / checked out | **NO** — the whole operation ran on `p8-release-reconciled` |
| Working tree modified by Git operations | **NO** |
| P16 preserved | **YES** — `9c96cbf` unchanged, reachable remotely |
| P17 preserved | **YES** — `d24a567` unchanged, reachable remotely |
| Repository configuration changed | **NO** (the broken `origin` remote was left exactly as found) |

---

## 12. Production Safety

| Item | Status |
|---|---|
| Production contacted | **NO** |
| Production deployed | **NO** |
| Production database changed | **NO** |
| Production migration run | **NO** |
| Production infrastructure modified | **NO** |
| Production APIs contacted | **NO** |
| Application code modified | **NO** |
| Migrations created | **NO** |
| P17-A started | **NO** |
| PO decisions reconciled | **NO** |
| UI modified | **NO** |

The only remote operations were Git **read** operations (`fetch`, `ls-remote`) and one Git **history-preservation**
write (`push` of already-committed history) against the project's own GitHub repository.

---

## 13. Final Verdict

**P17_FULL_BRANCH_PRESERVED**

The complete local `p8-release-reconciled` history — **25 previously unpublished commits** (P12, P14, P16 and P17) —
was pushed to the project's real remote and independently verified. The remote branch now points to
`d24a5671d536c439414f85bb739181669382c6c`, from which both the P16 checkpoint `9c96cbf…` and the P17 checkpoint
`d24a567…` are reachable. Nothing remains unpublished. No force, no rebase, no reset, no amend, no history rewrite, no
unrelated file committed, no other repository touched, no production contact.

---

## 14. Additional Findings and Recommendations (non-blocking)

1. **The branch's configured upstream is broken.** `branch.p8-release-reconciled.remote = origin`, and `origin` is
   `/tmp/ct_step2`, which no longer exists. Consequences: `git branch -vv` reports a misleading "ahead 137"; a bare
   `git push` targets a dead path; and the "remote tip `93d5cdd`" figure in the previous report was the stale
   `origin/*` ref, not reality (the true tip was `790923f`, 112 commits further on).
   **Recommendation (requires separate authorisation — not done here):** point the upstream at `github`
   (`git branch --set-upstream-to=github/p8-release-reconciled`) and/or remove the dead `origin` remote.
2. **A Product-Owner document is still unprotected by any commit.** `docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md`
   (plus the other 17 untracked items) exist only in this working tree. A push cannot preserve them. If they are
   durable project records they should be committed in a separate, deliberate, scope-limited task — **not** by this
   preservation task, and never via `git add -A`.
3. **The task header's P17 SHA is malformed** (39 hex characters; see §1.2). Future task headers should quote the
   40-character SHA.
4. **`github/main` and `origin/main` disagree** locally (`2f56562` vs `20b7a92`), reflecting stale tracking refs from a
   different fetch time. This is outside the scope of preserving `p8-release-reconciled` and was **not** acted on.

### 14.1 Report commit

This report is committed as a **separate normal commit containing exactly one file**, after the preservation push, so
that it neither altered the preserved checkpoint nor mixed unrelated content. It is then pushed by a second
**fast-forward, non-force** push. If that push were to fail, the preservation itself would already be complete and
verified.

---

## Document Control

**Document:** `CT-PO-P17-GIT-PRESERVE-02-20260925`
**Task:** `P17-GIT-PRESERVE-02-20260925`
**Operation:** branch preservation push (no development of any kind)
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Remote:** `github`
**Remote before:** `790923f19b5087d610f8ae9e7df442017ccfbf2c` · **Remote after:** `d24a5671d536c439414f85bb739181669382c6c`
**Commits preserved:** 25 · **Force push:** NO · **History rewritten:** NO · **Production:** NOT CONTACTED
**Verdict:** **P17_FULL_BRANCH_PRESERVED**





