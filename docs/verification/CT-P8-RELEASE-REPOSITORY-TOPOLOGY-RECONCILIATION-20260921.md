# CT-P8 — Release Repository Topology Reconciliation

**Type:** READ-ONLY reconciliation (evidence only). **No changes were made** — no branch switch, merge, cherry-pick,
reset, rebase, force-push, prune, remote edit, file copy/delete, deploy or production migration (§15).
**Date:** 2026-09-21
**Final status:** `TOPOLOGY DIVERGENCE REQUIRES PO DECISION` (§14)

---

## 1. Checkouts inventoried

All three directories exist on this machine:

1. `/home/shomonrobie/carbon_tally`
2. `/home/shomonrobie/carbon_tally_p8_release`
3. `/home/shomonrobie/ct_93d5cdd`

## 2. Repository roots and 3. branches / 4. HEADs

| # | Directory | Repo root | `.git` | Kind | Branch | HEAD | Dirty paths |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `carbon_tally` | `/home/shomonrobie/carbon_tally` | own `.git` (common `.git`) | **independent clone** | `main` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | **299** |
| 2 | `carbon_tally_p8_release` | `/home/shomonrobie/carbon_tally_p8_release` | own `.git` (common `.git`) | **independent clone** | `p8-release-reconciled` | `0be7438ddbd1f05c004246cbafc844cbdb1af319` | **20** |
| 3 | `ct_93d5cdd` | `/home/shomonrobie/ct_93d5cdd` | own `.git` (common `.git`) | **independent clone** | `p8-release-reconciled` | `ee5b0b3b15d8fce737be27f65c387f3c8e54de9f` | **0 (clean)** |

`git rev-parse --git-common-dir` returns `.git` for each, and each `git worktree list` reports only its own path as
non-prunable — so **all three are separate clones**, not linked worktrees of one another.

## 5. Remotes and 6. upstreams

| Directory | Remote | URL | Branch upstream |
| --- | --- | --- | --- |
| `carbon_tally` | `origin` | `https://github.com/shomonrobie/CarbonTally.git` | `origin/main` |
| `carbon_tally_p8_release` | `origin` | `https://github.com/shomonrobie/CarbonTally.git` | `origin/p8-release-reconciled` |
| `ct_93d5cdd` | **`github`** | `https://github.com/shomonrobie/CarbonTally.git` | **`origin/p8-release-reconciled`** |
| `ct_93d5cdd` | `origin` | **`/tmp/ct_step2`** (local filesystem path — dead) | — |

**All GitHub remotes point at the same repository** (`shomonrobie/CarbonTally`), but they are **named differently**
(`origin` vs `github`) and `ct_93d5cdd` additionally carries a stale **local-path** remote named `origin`, which is what
its release branch is configured to track. Pushes during Phase 8 were made explicitly to `github`.

## 7. Worktree relationships

* `carbon_tally` (parent clone) lists two **prunable** worktrees: `/tmp/ct_step2 [p8-release-reconciled]` @ `93d5cddd`
  and `/tmp/fx12_pub_wt [fx12-publish]` @ `f1a1cf8`. Neither directory is part of this task's inventory.
* `carbon_tally_p8_release` and `ct_93d5cdd` each list only themselves.

## 8. Commit-presence matrix

Legend: **P** = commit object present locally; **–** = absent.

| Commit | Subject (short) | `carbon_tally` | `carbon_tally_p8_release` | `ct_93d5cdd` |
| --- | --- | --- | --- | --- |
| `ee5b0b3` | post-closure deployment-state reconciliation | – | – | **P** |
| `551f121` | PO I2 closure record (I2 CLOSED — VERIFIED PASS at 177dff5) | – | – | **P** |
| `0848671` | post-closure deployment readiness audit | – | – | **P** |
| `a11c7d5` | OHD independent re-verification of the I2 remediation | – | – | **P** |
| `177dff5` | **remediate OHD I2 FAIL** (the verified I2 application revision) | – | – | **P** |
| `20b7a92` | `carbon_tally` local `main` tip | **P** | – | **P** (present, **not** an ancestor of the release HEAD) |
| `2f56562` | GitHub `refs/heads/main` tip | **P** | **P** | **P** (ancestor of the release HEAD) |
| `93d5cddd` | `carbon_tally` local `p8-release-reconciled` tip | **P** | – | **P** (ancestor of the release HEAD) |
| `0be7438` | `carbon_tally_p8_release` HEAD | **P** | **P** | **P** (ancestor of the release HEAD) |

GitHub state, read with `git ls-remote` (no local writes, no fetch):

```
refs/heads/main                 = 2f56562ad797c5c2f1b73da7380e45199584e016
refs/heads/p8-release-reconciled = ee5b0b3b15d8fce737be27f65c387f3c8e54de9f
```

## 9. Divergence analysis

All objects needed for the comparison exist in the release checkout, so ancestry was tested there (`git merge-base --is-ancestor`):

| Commit | Relative to release HEAD `ee5b0b3` | Interpretation |
| --- | --- | --- |
| `0be7438` (`carbon_tally_p8_release` HEAD) | **ancestor** | that checkout is simply **behind**; it has **no unique commits** |
| `93d5cddd` (`carbon_tally` local `p8-release-reconciled`) | **ancestor** | stale local release branch, **no unique commits** |
| `2f56562` (GitHub `main`) | **ancestor** | GitHub main is fully contained in the release branch (`HEAD..2f56562` = **0**; release branch is **165** commits ahead of main) |
| `20b7a92` (`carbon_tally` local `main`) | **NOT an ancestor** | contains commit(s) **not present in the release history** |

Additional divergence evidence:

* `carbon_tally`: local `main` vs GitHub `main` → `git rev-list --left-right --count` = **`4  5`** (4 commits only local, 5 only on GitHub). Both tips carry the **same subject line** (`fix(frontend): retire legacy onboarding and use org member cha…`) with different SHAs, consistent with a locally **rewritten/amended** commit → local `main` is materially divergent from GitHub `main`.
* `carbon_tally`: its local `p8-release-reconciled` is **4 commits behind its own `main`**.
* `carbon_tally` dirty tree = **299 paths**, spread across application and tooling trees: `admin` 71, `.agents` 69, `tools` 31, `docs` 24, **`backend` 15**, `demodatagen` 13, `qa_harness` 6, `frontend` 6, `output` 5, `e2e` 5 → substantial **uncommitted work**, including `backend/` and `frontend/`.
* `carbon_tally_p8_release` dirty tree = **20 paths, all untracked documentation/artifacts** (`artifacts/` and 18 × `docs/cline/reports/P8-*.md`, several titled `P8-PRODUCTION-MIGRATION-*`). **No application working-tree changes** there.

## 10. PO closure document presence

File: `docs/architecture/CARBONTALLY_P8_I2_INSIGHT_CLOSURE.md`

| Checkout | On disk | Tracking | Blob |
| --- | --- | --- | --- |
| `carbon_tally` | yes | **untracked** (`??` on `main`) | none at `HEAD` or at its local release branch |
| `carbon_tally_p8_release` | **no** | — | none |
| `ct_93d5cdd` | yes | **tracked** | `a94ba68d7d59180384b9634a8965d2bbcd2c707b` at `HEAD` **and** on `refs/heads/p8-release-reconciled` |

Content identity: sha256 `4ebfbe393da70dd4d3d0137a22e4f62fd7a3a019cd7cdba09d589b7031d7c073` (same value as the PO-provided file), contains `> **I2 CLOSED — VERIFIED PASS at 177dff5**`.

Commit `551f121` (the PO closure commit) exists **only** in `ct_93d5cdd`, and GitHub `refs/heads/p8-release-reconciled` includes it (its tip `ee5b0b3` is a descendant).

## 11. I2 application revision integrity

* `177dff5` (OHD-verified I2 application revision) exists **only** in `ct_93d5cdd`. `backend/api/insight_authz.py` is present only there and **absent** in the other two checkouts — there is therefore **no divergent copy** of the I2 application code anywhere else; the others simply lack the Insight work.
* Blobs recorded at `177dff5` (release checkout):

| File | Blob |
| --- | --- |
| `backend/api/insight_authz.py` | `63e0699d996f38a543ec3f2aad2ddda0a769a669` |
| `backend/api/v3_insight.py` | `6cb2fa4645e2c2932e05d1393e7eb840563c09a9` |
| `backend/data/insight.py` | `ec63b6f2a276aa510d5cc0ea6193258039d71115` |
| `backend/api/operations_auth.py` | `1494a524ce7bc36861d688474bf4779dc349ca74` |
| `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` | `58e7a3ab4997d8fb9cd1abe873e88305bb7e2a4d` |
| `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` | `28cbebadb43634d5783d0622235040217d824fe5` |

These are identical to the values previously recorded for the verified revision, and unchanged at `ee5b0b3`.

## 12. Authoritative release-branch determination

**Established from evidence:**

* **Authoritative release checkout:** `/home/shomonrobie/ct_93d5cdd` — the only checkout on `p8-release-reconciled` containing the Phase 8 work; **clean**; HEAD `ee5b0b3`, which **equals** GitHub `refs/heads/p8-release-reconciled` (`ee5b0b3`) as read with `git ls-remote`.
* **Authoritative remote for that branch:** **`github` → `https://github.com/shomonrobie/CarbonTally.git`** — the same GitHub repository the other checkouts address as `origin`.
* **`carbon_tally_p8_release`: STALE / SUPERSEDED — not authoritative** (its HEAD `0be7438` is an ancestor of the release HEAD; it contains no Insight commits, no closure document, and no unique commits). Its directory name is not evidence of authority.
* **`carbon_tally`: not the release checkout** — it is the general `main` working checkout, and its local `main` is materially divergent from GitHub `main`.
* **Configuration defect (reported, not fixed):** in `ct_93d5cdd` the release branch's configured upstream is `origin/p8-release-reconciled`, where `origin` is the **stale local path `/tmp/ct_step2`** — not GitHub. Phase 8 pushes were made explicitly to `github`, which is why GitHub is correctly up to date.

## 13. Unresolved ambiguity — requires PO decision

1. Two directories hold a branch named `p8-release-reconciled` with different heads (`0be7438` vs `ee5b0b3`) — the PO should declare `carbon_tally_p8_release` obsolete/superseded (evidence supports that) rather than leaving two candidates.
2. Fate of `carbon_tally`'s stale local `p8-release-reconciled` (`93d5cddd`), its **diverged local `main`** (`20b7a92`; 4 local-only commits vs GitHub), and its **299-path dirty tree** (including `backend/` and `frontend/`).
3. The **untracked** closure document sitting on `main` in `carbon_tally` (already committed on the release branch as `551f121`).
4. The release branch's **misconfigured upstream** (local path `origin` `/tmp/ct_step2`) and the two **prunable** `/tmp` worktrees registered in the parent clone.
5. The 18 untracked `docs/cline/reports/P8-PRODUCTION-MIGRATION-*` files in `carbon_tally_p8_release` are **unreviewed artifacts of unknown provenance in a non-authoritative checkout**; they must not be used as deployment evidence.

## 14. Deployment-state findings

* Render: **UNKNOWN** — no access, no manifest in the repository.
* Vercel: **UNKNOWN** — no access (and **no frontend change** is attributable to I1/I2, so no frontend deployment is required by those stages).
* Production migration state: **UNKNOWN** — no authorised read-only inspection path; deliberately not inferred from any local checkout, the Demo Lab, QA, the disposable test database, Git history or timestamps.

**No deployment, no production migration and no production data change was performed by this task.**

## 15. Statement of no changes

This task made **no changes** to any checkout: no branch switch, merge, cherry-pick, reset, rebase, force-push, prune, remote edit, file copy/delete, database change or deployment. The only repository change is **this report**, committed and pushed from the **already-established authoritative release checkout** (`ct_93d5cdd` → `github/p8-release-reconciled`), as permitted by the task.

**Final status: `TOPOLOGY DIVERGENCE REQUIRES PO DECISION`.**

The release-branch authority itself **is** established (`ct_93d5cdd` ↔ `github:p8-release-reconciled` = `ee5b0b3`, clean, containing `177dff5`, `a11c7d5`, `0848671`, `551f121`, `ee5b0b3`); what requires the PO decision is the surrounding topology: a stale duplicate release checkout, a stale local release branch, a materially diverged local `main`, a heavily dirty working tree, a misconfigured release-branch upstream, and the stale/prunable worktree and local-path remote state — none of which may be cleaned up without PO authorisation.
