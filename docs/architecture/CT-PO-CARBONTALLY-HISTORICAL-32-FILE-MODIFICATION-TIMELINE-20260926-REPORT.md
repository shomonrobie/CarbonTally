# CT-RECON-03A — Forensic Report (Historical 32-File Modification Timeline)

**Task ID:** `CT-RECON-03A-20260926-HISTORICAL-32-FILE-MODIFICATION-TIMELINE`
**Companion:** `docs/architecture/CT-PO-CARBONTALLY-HISTORICAL-32-FILE-MODIFICATION-TIMELINE-20260926.md`
**Type:** READ-ONLY forensic summary — **no disposition decision**
**Date:** 2026-09-26

---

## 1. Task identity

Read-only forensic timeline of the 32 substantive uncommitted changes in the historical repository
`/home/shomonrobie/carbon_tally`, establishing *when* they were last written, *what committed history
surrounds them*, and *whether they cluster into recognisable development batches* — to support a later
Product Owner memory-reconciliation. No fate is decided.

## 2. Starting repository state

| Repo | Branch | HEAD | Status |
|---|---|---|---|
| `/home/shomonrobie/carbon_tally` | `main` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | 305 entries (227 M + 78 ??) |
| `/home/shomonrobie/ct_93d5cdd` | `p8-release-reconciled` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | 1 tracked mod (`.gitignore`) + untracked docs |

Both matched the task specification exactly.

## 3. 32-file derivation

Independently re-derived (not copied from CT-RECON-01/02):

```
git diff --ignore-all-space --name-only  → 32 paths
git diff --ignore-all-space --stat       → 32 files, 774 insertions(+), 71 deletions(-)
```

✔ Exact match with the expected figures. **All 32 are tracked modifications** (` M`); none are untracked.

## 4. Methodology

Baseline (`rev-parse`/`branch`/`status`) → whitespace-insensitive diff derivation → `stat` filesystem
mtimes → per-file `git status`/`cat-file` → per-file last commit (`git log -1`) → per-file diff shape
(`--numstat`, `-U0` hunks) → read-only content-equivalence probes against historical commits `93d5cddd`
and `f1a1cf8` and against canonical HEAD → Git windows + checkpoint distribution →
mtime/content clustering. Temporary output only under `/tmp/`.

## 5. Major findings

1. **Filesystem mtimes cluster in three waves:** 2026-09-13 (two intra-day groups), 2026-09-14 (three
   groups), 2026-09-15 (one group); plus a long tail on 2026-08-15, 2026-08-21, 2026-08-24, 2026-09-01.
2. **Sub-second simultaneity** in several groups (seven admin files within **0.111 s**; two pairs within
   **0.002 s**) — a `DIRECTLY VERIFIED` observation consistent with programmatic batch writes
   (mechanism `INFERRED`).
3. **Decisive content finding:** **11** of the 32 working-tree files are byte-equivalent (ignoring
   line endings) to commit **`93d5cddd`** — the historical **`p8-release-reconciled`** tip
   (2026-09-19), which is **NOT an ancestor of `main`**. So this content is *not unique to the working
   tree*: equivalent bytes are committed on that branch.
4. **6** of those 11 (`v3_reports.py`, `conftest.py`, `test_report_versions.py`, `test_reports.py`,
   `test_v3_report_lifecycle.py`, `ReportDetailPage.jsx`) are also **content-identical in canonical HEAD**
   → incorporation `STRONGLY CORRELATED` (content identity; not proven authorship).
5. **21** of the 32 differ from `93d5cddd`, `f1a1cf8` and `main` — no committed equivalence found.
6. Working-tree content is **much newer** than the last commit for several paths (e.g. admin files last
   committed 2026-07-21…2026-08-06 but written 2026-09-13).
7. **Anomaly:** `frontend/src/App.js` carries a 1-line deletion relative to **HEAD itself**, with an mtime
   (2026-09-15) predating that HEAD commit (2026-09-16) — recorded as fact, cause `UNKNOWN`.

## 6. Temporal batches

| Batch | Files | Mtime range (filesystem, +0600) | Common area | Content origin | Strength |
|---|---|---|---|---|---|
| A | 4 | 2026-09-13 12:54:35 → 12:56:51 | backend accounting / manual-extraction data | all == `93d5cddd` | STRONGLY CORRELATED |
| B | 10 | 2026-09-13 13:58:16 → 13:59:56 | admin console (deps + source) | none == `93d5cddd` | DIRECTLY VERIFIED (sub-second) |
| C | 2 | 2026-09-14 12:16:34 | Phase 8 report integration tests | both == `93d5cddd`, both canonical-identical | STRONGLY CORRELATED |
| D | 5 | 2026-09-14 13:01:43 → 15:32:04 | automatic processing + harness guard + AGENTS | 2 of 5 == `93d5cddd` | STRONGLY CORRELATED |
| E | 4 | 2026-09-14 21:08:03 → 21:19:51 | Phase 8 report lifecycle (API+UI+tests) | 3 of 4 == `93d5cddd`, same 3 canonical-identical | STRONGLY CORRELATED |
| F | 3 | 2026-09-15 09:40:39 → 21:26:47 | frontend API client + operations | none == `93d5cddd` | WEAKLY CORRELATED |
| G | 4 | 2026-08-15 → 2026-09-01 | miscellaneous / generated / config | none == `93d5cddd` | WEAKLY CORRELATED |

Total 4+10+2+5+4+3+4 = **32** ✔. No product meaning is assigned to any batch.

## 7. Limitations

* **Filesystem mtime ≠ development date.** It only proves *when the current file was last written on this
  machine*. Original authoring, intent and business-context dates are `UNKNOWN`.
* Content-equality comparisons ignore whitespace (so CRLF-vs-LF churn is neutralised) but they prove only
  *byte equivalence*, not authorship or intent.
* Cline checkpoints are **temporally associated** with the mtime days (checkpoint counts: 2026-09-13 = 19,
  2026-09-14 = 33, 2026-09-15 = 39) but are **not** established as the source of any modification
  (`NO CLEAR ASSOCIATION`).
* "no incorporation established" for 26 paths means only that the content differs from canonical — not
  that canonical lacks the feature.
* No database, environment or runtime access was used; no test was run.

## 8. Questions for Product Owner (recall only — not decisions)

1. Do you recall an **admin-console** change around **2026-09-13 ~14:00** (10 files) that was never
   committed on `main`?
2. Do you recall an **accounting / calculation-snapshot** change around **2026-09-13 ~12:55** (4 files)
   that ended up on the `p8-release-reconciled` line?
3. Do you recall deliberately **populating the working tree from `p8-release-reconciled`** (11 files match
   `93d5cddd`)?
4. Do you recall the **Phase 8 report-lifecycle** implementation around **2026-09-14 ~21:10** (4 files)?
5. Do you recall a **durable-processing / test-harness-guard / `AGENTS.md` (+29 lines)** change around
   **2026-09-14 13:01–15:32**?
6. Do you recall a **2026-09-15 frontend-API / operations** change, and a one-line `App.js` edit?
7. Are the long-tail files (`import_summary.md`, `CarbonTally_DB_Schema_V3M2.sql`, `requirements.txt`,
   `supabase/config.toml`) recognisable as generated artefacts or local configuration?
8. Can you recognise any of the seven batches (A–G) as intended work, experiments, config, or generated
   output? (Recall only — no disposition requested.)

## 9. Safety verification

| Check | Result |
|---|---|
| Historical HEAD/branch/status unchanged | **VERIFIED** (HEAD `20b7a928…`, `main`, 305 entries) |
| Canonical HEAD/branch unchanged | **VERIFIED** (HEAD `cb70fd6…`, `p8-release-reconciled`) |
| Source/SQL/migration/RLS/config modified | **NO** |
| Files deleted/renamed/moved | **NO** |
| checkout/stash/reset/commit/amend/branch/tag/ref mutation | **NO** |
| fetch/pull/push/merge/rebase/cherry-pick | **NO** |
| Database/Supabase/production/Vercel/Render access | **NO** |
| Package installation | **NO** |
| Temp files inside either repository | **NO** (all `/tmp/`) |
| Repository writes | **2 permitted Markdown reports only** |

**Non-decision statement:** this report does not determine whether any historical file should be retained,
deleted, ported, merged, archived, or abandoned; those decisions require Product Owner input and/or a
later technical reconciliation task.

## 10. Final verdict

```
CT_RECON_03A_COMPLETE_READ_ONLY_TIMELINE
```

All 32 substantive files were independently enumerated and given a full timeline record (master table and
per-file notes in the companion document). Evidence was collected read-only; nothing was modified.
Limitations are stated above.

**STOP — forensic report complete.**
