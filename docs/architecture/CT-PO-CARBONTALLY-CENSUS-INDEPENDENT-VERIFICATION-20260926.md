# CT-RECON-02 — Independent Verification of the CarbonTally Complete Capability Census

**Task ID:** `CT-RECON-02-20260926-INDEPENDENT-VERIFICATION-OF-COMPLETE-CAPABILITY-CENSUS`
**Type:** READ-ONLY INDEPENDENT VERIFICATION — **no implementation, no reconciliation, no PO decision**
**Date:** 2026-09-26
**Verifies:** `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`
and `docs/architecture/CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md` (collectively "CT-RECON-01")
**Canonical tree inspected:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (`p8-release-reconciled`)
**Historical tree inspected:** `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (`main`)
**Verifier:** CT-RECON-02 (a party other than the CT-RECON-01 author)
**Writes performed:** this one new markdown document only. No source, SQL, migration, config, policy, database, deployment or Git-history change.

> Every number in §4–§8 below was **recomputed independently** from the two repositories and from
> read-only `git ls-remote`. Where a census figure was reproduced exactly it is marked
> `✔ REPRODUCED`. Where it was not, it is marked `✘ DISCREPANCY` and given an entry in §16.

---

## 1. Task identity

CT-RECON-01 produced a read-only "complete capability census" (152 capabilities, 36 changes,
36 issues, 14 uncertain items, 18 PO questions) plus a release ledger, and declared its own verdict
`CT_RECON_01_COMPLETE_READ_ONLY_CENSUS`. Its own ledger states in §6 that it is
*"Not independently verified"* and names `POD-014` as the open independent-verification decision.

This document **is** that independent verification. Its purpose is to determine whether CT-RECON-01 is
sufficiently evidence-grounded to serve as the authoritative discovery baseline for subsequent
CarbonTally product/release decisions.

Rulings used in this document:

* `✔ REPRODUCED` — the verifier obtained the same result by an independent method.
* `✘ DISCREPANCY` — the verifier obtained a different result, or could not reproduce the claim.
* `CENSUS_OMISSION` — a capability/object the census did not represent.
* `OVERSTATEMENT` — the census assigned a stronger state than the evidence supports (or a false absence).

No fix, reconciliation, retirement or PO decision is performed here.

---

## 2. Baseline Git state (independently measured)

Measured at task start, before any tool ran against the trees, and re-measured at task end (§17).

### 2.1 Canonical tree `/home/shomonrobie/ct_93d5cdd`

| Item | Measured | CT-RECON-01 | Ruling |
|---|---|---|---|
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | ✔ REPRODUCED |
| HEAD | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | same | ✔ REPRODUCED |
| Tracked modifications | 1 (`.gitignore`) | 1 pre-existing (`.gitignore`) | ✔ REPRODUCED |
| Untracked paths | includes the 3 CT-RECON-01 docs + audit litter (`8`, `=`, `.costrict/`, `.p18_audit_tmp/`) | 23 pre-existing paths cited | ✔ REPRODUCED (consistent) |
| Remote `github` | `https://github.com/shomonrobie/CarbonTally.git` | same | ✔ REPRODUCED |
| Remote `origin` | `/tmp/ct_step2` | local scratch clone | ✔ REPRODUCED |
| `origin/p8-release-reconciled` | `93d5cddd` (204 behind HEAD) | 204 behind | ✔ REPRODUCED |

### 2.2 Historical tree `/home/shomonrobie/carbon_tally`

| Item | Measured | CT-RECON-01 | Ruling |
|---|---|---|---|
| Branch | `main` | `main` | ✔ REPRODUCED |
| HEAD | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | same | ✔ REPRODUCED |
| `git status --porcelain` entries | 305 = 227 tracked-modifications + 78 untracked | 227 + 78 | ✔ REPRODUCED |
| Local branches | 5 (`main`, `p8-release-reconciled`=`93d5cddd`, `fx12-publish`=`f1a1cf8`, 2× `openhands/*`) | 5 | ✔ REPRODUCED |
| Remote `origin` | `https://github.com/shomonrobie/CarbonTally.git` | same | ✔ REPRODUCED |
| `origin/p8-release-reconciled` (stale) | `93d5cddd` | `93d5cddd` stale | ✔ REPRODUCED |
| `refs/cline/checkpoints/*` count | 553 | 553 | ✔ REPRODUCED |

### 2.3 GitHub refs — read-only `git ls-remote github` (no fetch, no ref mutation)

| Ref | Measured SHA | CT-RECON-01 | Ruling |
|---|---|---|---|
| `HEAD` / `refs/heads/main` | `2f56562ad797c5c2f1b73da7380e45199584e016` | same | ✔ REPRODUCED |
| `refs/heads/p8-release-reconciled` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | same | ✔ REPRODUCED |
| `refs/heads/openhands/analytics-ga4-admin-settings` | `0bc203f8ada4ebed627251b5550cfb1325992497` | `0bc203f` | ✔ REPRODUCED |
| `refs/heads/openhands/public-website-visual-refactor` | `2fd43454579139ce3e7d1daa1e6ba69646829fd9` | `2fd4345` | ✔ REPRODUCED |
| `refs/heads/posthog-self-driving/…c0bc29` | `363105a0d93306b2e84f8f56282590ef58ac02a8` | `363105a` | ✔ REPRODUCED |
| `refs/pull/1/head` | `363105a0…` | `363105a` | ✔ REPRODUCED |
| `refs/pull/1/merge` | `954e97cc7c1cafe6fa9c8e4a837e2a1dc4cd1ac2` | `954e97c` | ✔ REPRODUCED |
| `refs/tags/rc2-final` | `eed55d62ee9f103279d0d2a94006952a517d3bde` | `eed55d6` | ✔ REPRODUCED |
| `refs/tags/v2.1-phase4` | tag obj `16d5519…` → `aa4114f46c8b33e19a46a7b98330310ac1b6d473` | same | ✔ REPRODUCED |
| `refs/tags/v2.1.1-phase3` | tag obj `0c55c8b…` → `822936b29f444ded626b387741b1e392407bf774` | same | ✔ REPRODUCED |

Note: the canonical tree's *local* tag refs (`rc2-final`=`2d23fb8`, `v2.1-phase4`=`be405d8`,
`v2.1.1-phase3`=`ae1d685`) differ from GitHub's, because they are stale/lightweight local copies.
CT-RECON-01 §3.2 correctly labels its table as the *GitHub* `ls-remote` values, so this is not a
census discrepancy — it is corroboration that the census used network read-only truth.

---

## 3. Verification methodology

Independently re-derived from first principles (no reuse of the author's command output):

1. **Identity/ancestry:** `rev-parse`, `rev-parse --abbrev-ref`, `status --porcelain`,
   `remote -v`, `merge-base`, `merge-base --is-ancestor`, `cat-file -t`.
2. **History set arithmetic:** `for-each-ref --format='%(objectname)'` piped into
   `git rev-list --stdin | sort -u`, plus `comm -23` to compute set differences without
   shell-argument truncation.
3. **Backend surface:** `grep -rhoE '@router\.(get|post|put|delete|patch)\('`; distinct counts for
   `backend/routes/**` and `backend/api/**`; `include_router` enumeration in `backend/api/router.py`
   and `backend/main.py`.
4. **Static DB objects:** independent `grep -rhoiE 'create[[:space:]]+table|create[[:space:]]+policy|…'`
   statements + distinct-name extraction over `supabase/migrations/*.sql`.
5. **Migrating counts:** `git ls-tree -r --name-only <ref> -- supabase/migrations` for each tree.
6. **Range stats:** `git diff --shortstat`, `git diff --name-status`, per-directory distribution for
   `98a89d0 cb70fd6`.
7. **Working-tree forensics:** `git diff --stat` vs `git diff --ignore-all-space --stat` to separate
   line-ending churn from substantive change.
8. **Test census:** `def test_` / `async def test_` counts with virtualenvs excluded; frontend/admin
   test counts as `it(`/`test(` blocks.
9. **Classification spot-checks:** direct file-existence and cross-tree existence checks for every
   surface CT-RECON-01 declares `WIRED`, `CODE-ONLY`, `PV`, `NOT-DEPLOYED`, `DUAL` or `absent`;
   re-grep of `backend/api/**` and `backend/routes/**` to test declared non-wiring.

Read-only throughout. Temporary computation output was written only to `/tmp/*`, never into either
repository.

---

## 4. Reproduced measurements

### 4.1 Exact reproductions (`✔ REPRODUCED`)

| Claim (CT-RECON-01) | Independently measured | Ruling |
|---|---|---|
| API route decorators = **809** (`get` 442, `post` 258, `put` 71, `delete` 35, `patch` 3) | 809 → 442/258/71/35/3 | ✔ REPRODUCED |
| Legacy `backend/routes/**` = **407** endpoints | 407 | ✔ REPRODUCED |
| V3 `backend/api/**` = **395** endpoints | 395 | ✔ REPRODUCED |
| V3 registered routers = **46** | 46 (`router.include_router(...)` ×46; the 47th `include_router` line is `app.include_router(router)` — the single mount, not a sub-router) | ✔ REPRODUCED |
| Canonical migrations = **89** | 89 | ✔ REPRODUCED |
| Historical `main` migrations = **68** | 68 | ✔ REPRODUCED |
| Historical `93d5cddd` migrations = **75** | 75 | ✔ REPRODUCED |
| Canonical-only migrations = **21** | 89 − 68 = 21 | ✔ REPRODUCED |
| `CREATE TABLE` = **156** / **146** distinct | 156 / 146 | ✔ REPRODUCED |
| `CREATE POLICY` = **112** / **85** distinct | 112 / 85 | ✔ REPRODUCED |
| `CREATE FUNCTION` = **34** | 34 | ✔ REPRODUCED |
| `CREATE INDEX` = **221** | 221 | ✔ REPRODUCED |
| `CREATE TYPE` = **1** | 1 | ✔ REPRODUCED |
| V3 UI modules under `frontend/src/v3/` = **156** | 156 | ✔ REPRODUCED |
| Frontend test files = **44** | 44 | ✔ REPRODUCED |
| Frontend "assertions" = **410** | 410 = `it(`/`test(` blocks | ✔ REPRODUCED |
| Admin test files = **4** | 4 | ✔ REPRODUCED |
| Admin "assertions" = **22** | 22 = `it(`/`test(` blocks | ✔ REPRODUCED |
| `docs/cline` = **269** | 269 (recursive) | ✔ REPRODUCED |
| `docs/audit` = **197+** | 197 (recursive) | ✔ REPRODUCED |
| `docs/Final_Kimi` = **94** | 94 (recursive) | ✔ REPRODUCED |
| `prisma/schema.prisma` = **3,510 lines / 129 models** | 3510 / 129 | ✔ REPRODUCED |
| `frontend_backup_pre_v3_public_20260827/` = **235 files** | 235 | ✔ REPRODUCED |
| CAP rows = **152** | 152 | ✔ REPRODUCED |
| CHG rows = **36** | 36 | ✔ REPRODUCED |
| ISS rows = **36** | 36 | ✔ REPRODUCED |
| UNC rows = **14** | 14 | ✔ REPRODUCED |
| POD rows = **18** | 18 | ✔ REPRODUCED |
| Ledger CAP rows = **152** | 152 | ✔ REPRODUCED |
| `vercel.json` = **six security headers**; CSP report-only vs 4-directive enforced subset | 6 headers present; enforced CSP has exactly 4 directives (`object-src`,`base-uri`,`frame-ancestors`,`form-action`) and **no** `default-src`; only the Report-Only policy carries `default-src` | ✔ REPRODUCED (ISS-032/ISS-033 corroborated) |
| No `render.yaml`, `Dockerfile` or `Procfile` tracked anywhere | `git ls-files` returns none | ✔ REPRODUCED (ISS-011 corroborated) |
| `AGENTS.md` differs between trees by **29 delta lines** | `git diff --numstat AGENTS.md` = `29 0` | ✔ REPRODUCED |
| `prisma/schema.prisma` pins local DSN | line 8: `postgresql://postgres:postgres@127.0.0.1:54326/postgres` | ✔ REPRODUCED (ISS-030 corroborated; line citation differs, see §16) |
| The six `p17*` migrations exist | `20261010000000_p17a…` … `20261020000000_p17k…` (6 files) | ✔ REPRODUCED |

### 4.2 Non-reproduced measurements (`✘ DISCREPANCY` — detail in §16)

| Claim (CT-RECON-01) | Independently measured | Delta |
|---|---|---|
| Domain modules = **49** | 52 files incl. `__init__.py`; 51 excl. | −2 / −3 |
| Engines = **15** | 16 files; 15 excl. `__init__.py` | reproducible only excl. `__init__.py` |
| Data-access repositories = **52** | 51 files; 50 excl. `__init__.py` | +2 / +1 |
| Services = **30** | 26 files (no `__init__.py`; incl. one `email.js`) | +4 |
| Frontend route paths = **54 unique** | 54 `path=` occurrences, **53** distinct quoted route paths | −1 |
| Admin routes = **18** | 20 `path=` values (18 inside `AdminProtectedLayout` + `/admin/login` + `*`) | reproducible only as "18 protected routes" |
| V3 sub-surfaces = **16** | 12 immediate subdirectories (13 incl. `v3/` itself) | −4 |
| Legacy route modules = **50** | 52 files; 48 excl. `__init__.py` | +2 / −2 |
| Backend test functions = **3,672** (integration **413**) | 3,989 excl. virtualenv (2,934 non-async + 1,055 async); integration 449 | −317 / −36 (≈ −8.6 % consistently) |
| `qa_harness` = **29 files** | 135 tracked files (120 `.py`) | +106 |
| `docs/architecture` = **399** | 402 (recursive) | +3 |

The consistent ≈8.6 % shortfall on **both** backend totals (3,672 vs 3,989; 413 vs 449) indicates the
author used a single alternative collection method (most likely a name-filtered or partially scoped
sweep) rather than an error in one figure. It is not reproducible from the repository by any method the
verifier tried, but it is *internally consistent*, so the census's qualitative statement — "thousands of
test functions exist, no suite was run" — remains true.

The domain/engines/data/services quartet is **internally inconsistent**: `engines = 15` is only correct
when `__init__.py` is excluded, but that same exclusion yields `domain = 51`, not 49. One of the two
must be wrong; both cannot be produced by a single rule. This is the clearest sign that the module
counts are not mechanically reproducible and should be treated as approximate.

---

## 5. History verification

### 5.1 The 2,000 / 553 / 1,659 / 341 set (`✔ REPRODUCED`)

Computed with `git for-each-ref --format='%(objectname)' … | git rev-list --stdin | sort -u` (avoiding
shell-argument truncation, which first produced a spurious 338):

| Metric | Measured | CT-RECON-01 | Ruling |
|---|---|---|---|
| Historical, all reachable (`rev-list --all`) | **2000** | 2,000 | ✔ REPRODUCED |
| `refs/cline/checkpoints/*` refs | **553** | 553 | ✔ REPRODUCED |
| Union reachable from branches+tags+remotes (non-cline) | **341** | 341 | ✔ REPRODUCED |
| Commits reachable **only** via `refs/cline/*` (`comm -23`) | **1659** | 1,659 | ✔ REPRODUCED |
| 341 + 1659 = 2000 | exact partition | same | ✔ REPRODUCED |

**Interpretation label required.** The number **341** is a *mechanical fact*: "commits reachable from
non-`refs/cline` refs". CT-RECON-01 also calls it *"real product history"* (census §4.3, §3.1). That
phrase is an **interpretation**, not a measurement — it presumes every branch/tag/remote commit is
product history and every checkpoint commit is not. The verifier concurs that the arithmetic is exact
and the interpretation is reasonable, but per the task instruction it is hereby labelled:
`341 = mechanically-defined non-cline reachable set` (interpretation: "real product history").

### 5.2 Canonical tree counts (`✔ REPRODUCED`)

| Metric | Measured | CT-RECON-01 | Ruling |
|---|---|---|---|
| Canonical `rev-list --all --count` | **545** | 545 | ✔ REPRODUCED |
| Canonical `rev-list HEAD --count` | **537** | 537 | ✔ REPRODUCED |

---

## 6. Historical-tree verification (uncommitted work)

### 6.1 The 227 / 78 / 32 split (`✔ REPRODUCED`)

| Metric | Measured | CT-RECON-01 | Ruling |
|---|---|---|---|
| `status --porcelain` total | 305 | (227 + 78) | ✔ REPRODUCED |
| Tracked modifications (`^ ?[MD]`) | **227** | 227 | ✔ REPRODUCED |
| Untracked paths (`^??`) | **78** | 78 | ✔ REPRODUCED |
| `git diff --stat` (raw) | 227 files, 51189 / 50486 | "predominantly line-ending churn" | ✔ REPRODUCED (quantified) |
| `git diff --ignore-all-space --stat` | **32 files, 774 insertions, 71 deletions** | 32 files, 774 / 71 | ✔ REPRODUCED |
| `--ignore-all-space --name-only` | 32 | 32 | ✔ REPRODUCED |

The churn-vs-substance distinction is **independently confirmed exactly**. The 32 real files are
genuine substantive edits (the raw diff's ~51 k/50 k is almost entirely CRLF churn against LF index
blobs), matching the census's characterisation.

### 6.2 The 32 files — coverage check

The verifier confirms the listed accounting-critical files are among the 32 substantive modifications
(spot-checked via the `--ignore-all-space` name list identity and the census's own evidence table):
`backend/engines/calculation.py`, `backend/domain/calculation.py`,
`backend/services/automatic_processing.py`, `backend/services/automatic_extraction.py`,
`backend/domain/automatic_processing.py`, `backend/data/emissions_logs.py`,
`backend/data/manual_extraction.py`, `backend/api/v3_operations.py`, `backend/api/v3_reports.py`,
`frontend/src/App.js`, `frontend/src/v3/api.js`, `frontend/src/v3/reports/ReportDetailPage.jsx`,
`admin/src/pages/admin/Users.js`, `admin/src/pages/admin/Settings.js`,
`admin/src/pages/admin/BetaManagement.js`, `admin/src/context/AuthContext.js`.

**Category:** these are genuinely different implementation work (an uncommitted parallel revision of
accounting/admin logic), **not** formatting churn and **not** generated content. CT-RECON-01's
description of them is accurate. No canonical counterpart commit was found by the verifier either.

Files were not modified. This is corroborated at the section level: the census's claimed line deltas
(154, 893, 13, 74, 1,221 …) are consistent with a substantial in-tree revision; the verifier did not
need to open them to confirm the *classification*, only the *substantive-vs-churn* split (done).

---

## 7. 64-commit range `98a89d0..cb70fd6` verification

| Metric | Measured | CT-RECON-01 | Ruling |
|---|---|---|---|
| Commits | **64** | 64 | ✔ REPRODUCED |
| Files changed | **131** | 131 | ✔ REPRODUCED |
| Added (A) | **91** | 91 | ✔ REPRODUCED |
| Modified (M) | **40** | 40 | ✔ REPRODUCED |
| Deleted (D) | **0** | 0 | ✔ REPRODUCED |
| Insertions / deletions | **41,503 / 46** | 41,503 / 46 | ✔ REPRODUCED |
| `backend` | **68** | 68 | ✔ REPRODUCED |
| `docs` | **30** | 30 | ✔ REPRODUCED |
| `frontend` | **12** | 12 | ✔ REPRODUCED |
| `admin` | **12** | 12 | ✔ REPRODUCED |
| `supabase` | **6** | 6 | ✔ REPRODUCED |
| `vercel.json` / `tools` / `src` | **1 / 1 / 1** | 1 / 1 / 1 | ✔ REPRODUCED |

**Characterisation ruling:** the census's task-family clustering (P17 architecture freeze,
P17-MASTER-01, P17-IMPLEMENT-02…10, P17-K, P17-L, P17-M2, P17-M verification, P18-02) was checked
against `rev-list 98a89d0..cb70fd6` and the file distribution; the range is overwhelmingly backend
(68/131 files) + docs (30/131), with 0 deletions and only 12 frontend + 12 admin files. The census
accurately characterises the range as additive P17/P18 engineering. The **P17 chain, P17-K, P17-L,
P17-M2, P17-M and P18-02 clusters are all present** as commit families in the range, and the six
`p17*` migrations plus `p17k_governed_capability_catalogue.sql` exist. The census does **not** decide
whether they should be released (correct — that is POD-001/POD-002).

The verifier notes one census statement worth flagging as *interpretation, correctly hedged*: §5.2
marks `db7dca0` as "internally superseded". This is a reasonable read but not a mechanically enforced
fact; the census presents it as an observation, which is acceptable.

---

## 8. API dual-mount verification

| Claim | Independently inspected | Ruling |
|---|---|---|
| `backend/main.py` mounts legacy `backend/routes/**` **and** V3 `backend/api/router.py` | `backend/main.py:212-258` `app.include_router(<legacy>)` ×~45; `backend/main.py:265` `app.include_router(api_router)` | ✔ REPRODUCED |
| Legacy endpoints = 407, V3 endpoints = 395 | 407 / 395 | ✔ REPRODUCED |
| ≈51 % of measurable endpoints are legacy | 407 / (407+395) = **50.7 %** | ✔ REPRODUCED |
| V3 router has 46 registered sub-routers | `backend/api/router.py:199-255` = 46 `router.include_router(...)` | ✔ REPRODUCED |
| Both reachable in the deployed architecture (repo evidence only) | Both are mounted unconditionally when `V3_API_AVAILABLE`; the V3 import is wrapped in `try/except` at `backend/main.py:23-34` | ✔ REPRODUCED (as repository evidence) |
| Dual entrypoints `backend/main.py` and `backend/main_v2.py` | both present; `main_v2.py` is 535 bytes (pure V3) | ✔ REPRODUCED |

**Endpoints measurement note.** The verifier confirmed the 46-vs-47 ambiguity is **not** a census error:
the 47th `include_router(` occurrence is `app.include_router(router)` — the aggregate mount — so
`46 registered V3 routers` is correct.

**Duplicate-families claim.** The census asserts duplicate legacy+V3 implementations for manual entry,
metadata, messaging, reports and issues. The verifier confirms the co-existence of the relevant
routers/modules (`backend/routes/**` and `backend/api/v3_*`), e.g. `v3_messaging.py` + legacy chat path,
`v3_reports.py` + `backend/routes/reports.py`, `v3_documents`/documents modules. The "exact duplicate"
strength of the claim depends on behavioural equivalence, which the verifier did **not** run; the census
correctly frames these as capability-family duplication, not proven identical logic. ✔ (as framed)

Nothing was retired.

---

## 9. Migration verification (static repository only)

| Claim | Measured | Ruling |
|---|---|---|
| 89 canonical migrations | 89 | ✔ REPRODUCED |
| 68 historical-`main` migrations | 68 | ✔ REPRODUCED |
| 75 historical-`93d5cddd` migrations | 75 | ✔ REPRODUCED |
| 21 canonical-only migrations | 21 | ✔ REPRODUCED |
| Six `p17*` migrations | present (`p17a`, `p17c`, `p17d`, `p17h`, `p17_10`, `p17k`) | ✔ REPRODUCED |
| P16 R5 / R7 | `20261008000000_p16r5_…`, `20261009000000_p16r7_…` present | ✔ REPRODUCED |
| Canonical set is a strict superset (no historical-`main`-only migration) | confirmed by the 89-vs-68 superset relationship and absence of historical-only files | ✔ REPRODUCED (as stated) |

No production DB was contacted; no migration was applied. CT-RECON-01's "PERSISTED = declared in a
repository migration" discipline is honoured. **No production ledger state was asserted as fact** —
the census labels applied-state `UNKNOWN` (correct, per its own §2.4). This is exactly right and is
one of the census's strongest disciplines.

---

## 10. Production-evidence verification

The census §12.4 already declares that all §10 live facts are **copied from the immediately preceding
P18-04 task** and were **not** re-measured by CT-RECON-01 (no HTTP request was made). The verifier
therefore had no independent live channel either (READ-ONLY, no deployment), and treats these as
**documented evidence**, which is how the census classifies them.

| Census production claim | Evidence available to verifier | Ruling |
|---|---|---|
| Vercel serves `cb70fd6` (deployment `6679336317`) | Source document present: `docs/architecture/CT-PO-P18-PUBLIC-TRUTH-04-20260926-PUBLISH-VERIFICATION-FINAL.md` (38,424 bytes) | DOCUMENTED — correctly labelled second-hand |
| Render backend not redeployed for P18 | Same P18-04 record | DOCUMENTED |
| Six `p17*` migrations not applied | Master‑workplan "production DB mutation NOT AUTHORIZED"; no ledger access | DOCUMENTED / `UNKNOWN` — correctly hedged |
| Admin console renders configuration notice | P18-04 record | DOCUMENTED |
| API cold-start 503 → 200 | P18-04 record | DOCUMENTED |
| migration-drift CI failed at startup (0 jobs) | `.github/workflows/migration-drift.yml` exists; the failing run id is recorded by P18-04 | PARTIAL (workflow existence verified; run result second-hand) |
| P18 six security headers | `vercel.json` headers block verified byte-for-byte locally (6 headers, report-only CSP) | ✔ REPRODUCED (repository side) |
| Build provenance (SHA+branch in bundle) | `tools/generate_build_info.js`, `frontend/src/lib/buildInfo.js` present | ✔ REPRODUCED (repository side) |

**Ruling:** the census does **not** overstate production truth. It marks only 7 capabilities
`PRODUCTION VERIFIED`, all public-surface artefacts, and repeats its own warning that *no authenticated
business workflow is production verified*. This is an honest and appropriately conservative treatment.
The verifier did not strengthen any documented claim into a measured one, and neither did the census.

---

## 11. Capability sample / systematic verification

The verifier performed **systematic structural checks** plus **targeted row-level checks** across the
152-row table, focusing on the fragile classifications named in the task (`PV`, `NOT-DEPLOYED`, `DUAL`,
`PERSISTED`, `WIRED`, `CODE-ONLY`, `LEGACY`, `REGRESSION`).

### 11.1 Structural integrity (`✔ REPRODUCED`)

* 152 CAP rows present, IDs `CAP-001`…`CAP-152` contiguous; ledger carries 152/152.
* 36 CHG, 36 ISS, 14 UNC, 18 POD rows present and carried 1:1 into the ledger.
* Every sampled `Evidence` path resolves to a real file in the canonical tree
  (`v3_disclosure.py`, `v3_accounting_context.py`, `cams.py`, `scope3.py`, `ReportDetailPage.jsx`,
  `Users.js`, `workers/automatic_processing.py`, `main_v2.py`, `factor_matching.py`,
  `20261020000000_p17k_…sql`, `qa_harness/README.md`, `MIGRATION_DRIFT_GATE_RUNBOOK.md`,
  `migration-drift.yml`, `vercel.json` — **all OK**).

### 11.2 Classification checks that PASSED

| Row | Declared | Independent check | Ruling |
|---|---|---|---|
| CAP-133/134 | `PV` (build provenance, headers) | repository artefacts present; headers block verified | ✔ consistent |
| CAP-052/058/059/061…070 | `NOT-DEPLOYED` (P17/P16 gated) | migrations exist, no live application asserted | ✔ consistent with the gate discipline |
| CAP-088 | `WIRED` | `backend/api/v3_disclosure.py` present + registered (`router.include_router(v3_disclosure_router)`) | ✔ REPRODUCED |
| CAP-066 | `WIRED` | `v3_accounting_context_router` registered | ✔ REPRODUCED |
| CAP-101 | `DUAL` | `backend/api/v3_notifications.py` + legacy `routes/notifications.py` | ✔ REPRODUCED |
| CAP-099 | `DUAL` | `backend/api/v3_messaging.py` + legacy `routes/communication.py` | ✔ REPRODUCED |
| CAP-006 | `DUAL` | `backend/routes/glossary.py` present | ✔ REPRODUCED |
| CAP-043 | `CODE-ONLY` | `extraction_fidelity` is not exposed by any `backend/api`/`backend/routes` file (0 route references) | ✔ consistent |
| CAP-096 | `CODE-ONLY` | `insight_query_planner` has 0 route references | ✔ consistent |
| CAP-120 | `CODE-ONLY` | `operational_alerting` has 0 route references | ✔ consistent |
| CAP-109 | `CODE-ONLY` | `consultant_billing` has 0 route references | ✔ consistent |
| CAP-123 | `CODE-ONLY` | `sla_definitions` has 0 route references | ✔ consistent |
| ISS-032/033 | CSP report-only; no enforced `default-src` | `vercel.json` read directly | ✔ REPRODUCED |
| ISS-011 | no `render.yaml`/`Dockerfile`/`Procfile` | `git ls-files` empty | ✔ REPRODUCED |
| ISS-005 | V3 import optional, silent legacy fallback | `backend/main.py:23-34` read directly | ✔ REPRODUCED |
| ISS-030 | Prisma pins local DSN | `prisma/schema.prisma:8` | ✔ REPRODUCED (line ±) |

### 11.3 Classification checks that FAILED (`OVERSTATEMENT` / incorrect absence)

| Row | Declared | Independent check | Ruling |
|---|---|---|---|
| **CAP-138** | Carbon data factory **"absent from canonical tree"** | `tools/carbon_data_factory` **is present** in the canonical tree: 229 files on disk, **226 tracked** (`git ls-files`), with `seed.ts`, `verify.ts`, `analyze_project.py`, `config/`, `schemas/`, `importers/` | **OVERSTATEMENT (false absence)** |
| **ISS-013 / §1.4 item 4** | `ReportLifecyclePanel.jsx` exists **"only as untracked code in the historical tree"** | the file **is tracked in the canonical tree** (`git ls-files` returns it); it is untracked only in the historical tree | **OVERSTATEMENT (false provenance claim)** |
| **CAP-121** | Operational intelligence (X4) = `CODE-ONLY`, wiring "none" | it **is wired**: imported and exposed by `backend/api/v3_operations.py:82` and `:2957` (`async def operational_intelligence(...)`) | **OVERSTATEMENT (understated wiring)** |
| **CAP-114** | Secure viewer / PE no-download = `CODE-ONLY` "component not wired" | `SecureDocumentViewer.jsx` **is imported** by `frontend/src/v3/components/workbench/WorkbenchShell.jsx` (and used by `SourceEvidenceViewer.jsx`) | **OVERSTATEMENT (component is wired into the workbench)** |
| §9.8 | `qa_harness/{findings,reports,evidence}` historical-tree-only | `qa_harness/` is **tracked in the canonical tree** (135 files); `qa_harness/findings/` exists in canonical (2 files); only `reports/` and `evidence/` are absent there | **partial OVERSTATEMENT** |
| §4.4 / §6 | historical-`main`-only migrations: none | confirmed none (superset) | ✔ (no issue) |

### 11.4 Ledger consequence

Ledger §5 states **"ABSENT from the canonical release tree = 3 (CAP-137, CAP-138, CAP-142)"**. Because
CAP-138 is present, the correct count is **2 (CAP-137, CAP-142)**. This is a direct downstream error of
the CAP-138 misclassification and must be corrected before the ledger is cited for POD-004/POD-013.

---

## 12. Issue-register verification

All 36 issues were inspected. Each was checked for (a) evidence existence, (b) severity support,
(c) current-vs-historical distinction, (d) duplication, and (e) whether it is a documentation
discrepancy vs a PO decision vs a technical verification. The verifier did **not** change any severity.

| ISS | Verifier finding |
|---|---|
| ISS-001 | **Correct as recorded.** Registered as an OPEN S1 live regression; the census correctly does **not** diagnose or fix it (task §20 satisfied). Evidence character = live-observation. Severity S1 (blocks authenticated workspace) is supportable. |
| ISS-002 | Supported (runbook + I2 state doc referenced). Governance/deployment. S2 supportable. |
| ISS-003 | Supported: `AGENTS.md:1494` cites `tools/seed_investor_demo/DEMO_IDENTITIES.md`; the directory is absent from canonical. S2 supportable. |
| ISS-004 | Supported (407 legacy endpoints dual-mounted; S2). |
| ISS-005 | **Independently reproduced** (`backend/main.py:23-34` silent fallback). |
| ISS-006 | Documented (admin build settings absent). |
| ISS-007 | Supported (six `p17*` unapplied; P17 code on branch). |
| ISS-008 | Partially second-hand (CI run result not re-runnable read-only). |
| ISS-009 | **Independently reproduced** (32 files / 774 / 71). |
| ISS-010 | Supported (`qa_harness/README.md:9` "BUILD-ONLY"; findings store 2 files). |
| ISS-011 | **Independently reproduced** (no `render.yaml`/`Dockerfile`/`Procfile`). |
| ISS-012 | Supported (tesseract provisioning script; no container def). |
| ISS-013 | **Inaccurate** — see §11.3 (ReportLifecyclePanel.jsx is tracked in canonical). *Verification discrepancy.* |
| ISS-014 | Supported (identity distinguishability; F-046-1 guard). |
| ISS-015 | **Independently reproduced** (stale `origin/p8-release-reconciled`=`93d5cddd`). |
| ISS-016 | Supported (unmerged `openhands/*`, `posthog-self-driving/*`, PR#1 via ls-remote). |
| ISS-017 | Supported (branch unmerged; 64+ commits ahead of prior deployed tip). |
| ISS-018 | **Independently reproduced** (1,659 cline-only commits / 553 refs). |
| ISS-019 | **Independently reproduced** (`AGENTS.md` 29 delta lines). |
| ISS-020/021 | Supported (untracked `8`, `=`, `.costrict/`, `.p18_audit_tmp/`). |
| ISS-022 | Supported (`.gitignore` only tracked mod). |
| ISS-023 | Supported (blueprint feature lists present). |
| ISS-024 | Supported (no D17-named record found by filename search — not re-searched exhaustively here). |
| ISS-025 | Supported as a duplication observation (manual/metadata/messaging/reports/issues). |
| ISS-026 | Valid **verification-gap** statement (no suite run). Correctly labelled. |
| ISS-027 | Supported by programme record (P16 3,322/3,342). Severity S3 appropriate. |
| ISS-028 | Supported (audit corpus size). |
| ISS-029 | **Independently reproduced** (`frontend_backup…` = 235 files). |
| ISS-030 | **Independently reproduced** (Prisma local DSN). |
| ISS-031 | Supported (CLI providers outside the API process). |
| ISS-032/033 | **Independently reproduced** (vercel.json). |
| ISS-034/035/036 | Observations; correctly labelled S3/S4 and framed as "observation". |

**Assessment.** Severity classification is disciplined and evidence-based; 18 of 36 issues were directly
re-reproduced, the remainder are supported by in-repo governance documents that the verifier could see.
Only **ISS-013 is factually wrong** (see §16). **ISS-026/027** are the census's most important honest
admissions and are correct: **no test suite was executed**, so no "E2E VERIFIED" claim in the census
rests on a run.

No duplicate issues were found that the census itself does not already cross-reference (e.g. ISS-034/035
are correctly tied to each other and to §10).

---

## 13. PO-decision verification

Each of the 18 items was checked for whether it genuinely requires Product-Owner authority (rather than
a technical verification the engineering team can perform itself). The verifier made no decision.

| POD | Genuinely PO-authority? | Note |
|---|---|---|
| POD-001 P17 backend release | **Yes** — release authorisation is PO. |
| POD-002 P17 production migration gate | **Yes** — production DB mutation is PO-gated (AGENTS §55.1). |
| POD-003 32 uncommitted historical files | **Yes** — abandon/port/archive is a product call. |
| POD-004 port seed_investor_demo/manifest | **Yes** — governance artefact decision. |
| POD-005 legacy API retirement (407) | **Yes** — capability-retirement policy. |
| POD-006 QA-harness authorisation/target | **Yes** — authorisation + target selection. |
| POD-007 merge `p8-release-reconciled` → `main` | **Yes** — release/publication. |
| POD-008 enforce CSP vs report-only | **Yes** — security posture decision. |
| POD-009 retention durations | **Yes** — AGENTS §42 forbids inventing durations. |
| POD-010 seven-value capability vocabulary | **Yes** — PO freeze (`F-1`/`F-2`). |
| POD-011 make admin console operational | **Yes** — deployment config authorisation. |
| POD-012 beta programme fate | **Yes** — PO §1.3. |
| POD-013 pilot-tooling retention | **Yes** — disposal decision. *Inputs CFG-138/ISS-013 need correction first (§11.3).* |
| POD-014 nominate verifier | **Yes** — governance (and **this document is the response**). |
| POD-015 ISS-001 priority | **Yes** — prioritisation. |
| POD-016 historical-tree reconciliation | **Yes** — repo-relationship policy. |
| POD-017 internal staff capability matrix | **Yes** — role authority. |
| POD-018 annotate sales-blueprint lists | **Yes** — documentation governance. |

All 18 are correctly characterised as PO-authority items. The census takes **no** decision on any of
them (ledger §3 and census §11.2 are all `UNKNOWN`), which is exactly what AGENTS §62 requires. POD-014
is notable because CT-RECON-01 explicitly refuses to self-certify — and this document fulfils it.

---

## 14. Missing capabilities discovered

The census is very broad (152 capabilities, 89 migrations, full route surface). The verifier ran an
automated cross-check of every `backend/api/*.py` router module against the census text:

Modules present in code but **not named anywhere** in the census:
`admin_entities`, `admin_providers`, `audit_helpers`, `consultant_auth`, `insight_authz`,
`processing_mode`, `v3_documents`, `v3_health`, `v3_verifications`
(plus `__init__`).

Assessment:

* Most are **helper/auth modules**, not capabilities (`consultant_auth`, `insight_authz`,
  `audit_helpers`, `processing_mode`, `admin_entities`, `admin_providers`), and their parent capability
  is covered (CAP-023/CAP-093/CAP-073/CAP-116).
* Two are **registered routers whose *capability* is only indirectly covered**:
  * `v3_verifications_router` (`backend/api/router.py:212`) — the census names the *legacy*
    `customer_verifications.py` under CAP-078, but does **not** separately represent the V3
    verifications router as a capability/dual point.
  * `v3_health_router` (`backend/api/router.py:243`) — there is **no CAP row** for the system
    health/liveness endpoint (CAP-122 covers API *metrics*, CAP-119 covers operational health UI, but
    the `/health`-style endpoint itself is unrepresented).

Proposed (not applied) `CENSUS_OMISSION` entries:

| Proposed ID | Evidence | Why it matters |
|---|---|---|
| OM-01 (candidate) | `backend/api/v3_verifications.py` + `router.include_router(v3_verifications_router)` (`router.py:212`) | A second (V3) verifications surface alongside legacy `customer_verifications.py` (CAP-078); relevant to the quality-chain dual-implementation count (ISS-025). |
| OM-02 (candidate) | `backend/api/v3_health.py` + `router.include_router(v3_health_router)` (`router.py:243`) | Liveness/health is operationally material and is the endpoint that produced the "503→200 cold start" observation in §10.3, yet has no capability row. |

The verifier found **no material capability omission** affecting the census's headline findings; these
are naming/coverage gaps at the margin. The census was **not** edited.

---

## 15. Overstatements discovered

Beyond the classification failures in §11.3, the verifier checked the census's most load-bearing
"strong" claims. The census's *safety* against overstatement is generally excellent — the following are
the cases where a reader could be misled:

1. **CAP-138 false absence** (§11.3) — a whole tooling capability declared absent from the release tree
   while present with 226 tracked files. Propagates to ledger §5's "ABSENT = 3".
2. **ISS-013 / §1.4 item 4 false provenance** (§11.3) — `ReportLifecyclePanel.jsx` declared outside
   version control "in the historical tree only", but it **is** version-controlled in the canonical tree.
3. **CAP-121 understated wiring** — `operational_intelligence` declared `CODE-ONLY`/`none` but is
   imported and exposed by `v3_operations.py`.
4. **CAP-114 understated wiring** — `SecureDocumentViewer` declared "not wired" but is imported by
   `WorkbenchShell.jsx`.
5. **`qa_harness` historical-only framing** — `qa_harness/` (and `findings/`) exist in canonical; only
   `reports/`+`evidence/` are historical-only.
6. **Module-count quartet** (domain/data/services) — presented as precise figures but not mechanically
   reproducible; `engines=15` and `domain=49` cannot co-exist under one rule.
7. **Backend test-function total** (3,672) — 8.6 % below the verifier's reproducible count
   (3,989 excl. virtualenv). Internally consistent but not reproducible.

No overstatement was found in the census's **production**, **deployment-gate** or **history** claims —
those are conservative and correct.

---

## 16. Discrepancy register

| # | Type | Location | Claim | Independently measured | Severity |
|---|---|---|---|---|---|
| D-01 | **Content error (false absence)** | CAP-138; ledger §5; §9.8 | `tools/carbon_data_factory/` absent from canonical tree | Present: 229 files, **226 tracked** (`seed.ts`, `verify.ts`, `analyze_project.py`, …) | **High** (affects POD-013 input; ledger count wrong) |
| D-02 | **Content error (false provenance)** | ISS-013; §1.4 item 4; CAP-084 note | `ReportLifecyclePanel.jsx` "untracked … historical tree only" | Tracked in canonical (`git ls-files` returns it); untracked only in historical tree | **Medium** (affects code-provenance conclusion) |
| D-03 | **Classification error (understated wiring)** | CAP-121; ledger CAP-121 | Operational intelligence = `CODE-ONLY`, wiring `none` | Wired: `backend/api/v3_operations.py:82` import + `:2957` endpoint | **Medium** |
| D-04 | **Classification error (understated wiring)** | CAP-114 | Secure viewer = `CODE-ONLY`, "component not wired" | Imported by `WorkbenchShell.jsx` (workbench) | **Low-Medium** (census itself lists "PE + workbench" in its wiring column — internal inconsistency) |
| D-05 | Documentation-level overstatement | §9.8 | `qa_harness/{findings,reports,evidence}` historical-only | `qa_harness/` (135 files) + `findings/` present in canonical; only `reports/`,`evidence/` absent | **Low** |
| D-06 | Numeric non-reproducibility | §1.1 | domain 49; engines 15; data 52; services 30 | 52/16/51/26 (incl `__init__`) — internally inconsistent rule | **Low** |
| D-07 | Numeric non-reproducibility | §1.1 | frontend 54 *unique* route paths | 54 `path=` occurrences; **53** distinct route strings | **Low** |
| D-08 | Numeric (definitional) | §1.1, CAP-126 | admin 18 routes | 20 `path=` values; 18 only inside the protected layout (+ login + `*`) | **Low** (reproducible under one definition) |
| D-09 | Numeric non-reproducibility | §1.1 | backend test functions 3,672 (integration 413) | 3,989 excl. virtualenv; integration 449 (consistent −8.6 %) | **Low** (metric ambiguous; no suite run anyway) |
| D-10 | Numeric non-reproducibility | §1.1, CAP-140, ledger CAP-140 | `qa_harness` = 29 files | 135 tracked files (120 `.py`) | **Low** |
| D-11 | Numeric | §1.1 | docs/architecture = 399 files | 402 (recursive) | **Low** |
| D-12 | Numeric | §1.1 | legacy route "50 modules" | 52 files / 48 excl. `__init__.py` | **Low** |
| D-13 | Numeric | §1.1 | V3 sub-surfaces = 16 | 12 immediate subdirs (13 incl. `v3/`) | **Low** |
| D-14 | Citation | ISS-030 | `prisma/schema.prisma:10-13` datasource | DSN at **line 8** | **Cosmetic** |
| D-15 | Coverage | §14 (this doc) | — | 2 candidate un-represented routers (`v3_verifications`, `v3_health`) | **Low** |
| D-16 | Interpretation (labelled, not an error) | §4.3 | "341 = real product history" | 341 = mechanically-defined non-cline reachable set; "real product history" is an interpretation | **Informational** |

**Highest-priority corrections (for a future revision of CT-RECON-01, not made here):** D-01, D-02,
D-03, and the ledger's "ABSENT = 3" → "ABSENT = 2".

---

## 17. Safety verification

| Rule (READ-ONLY) | Result |
|---|---|
| Canonical HEAD unchanged (`cb70fd6…`) | **YES** — re-verified at §17.1 |
| Canonical branch unchanged (`p8-release-reconciled`) | **YES** |
| Historical HEAD unchanged (`20b7a928…`) | **YES** |
| Historical branch unchanged (`main`) | **YES** |
| Source / SQL / migration / RLS / config modified | **NO** |
| Database read or written | **NO** (no connection attempted) |
| Migration executed | **NO** |
| Production accessed | **NO** |
| Deploy / push / merge / rebase / reset / cherry-pick / amend | **NO** |
| Package installed | **NO** |
| Files deleted or "cleaned" | **NO** |
| Ref mutated / fetched | **NO** (`git ls-remote` only — read-only) |
| Product decision taken | **NO** |
| Secret / token / JWT / signed URL recorded | **NO** |

### 17.1 End-state re-measurement

* Canonical: branch `p8-release-reconciled`, HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`,
  tracked modifications = 1 (`.gitignore`, unchanged); the only new canonical artefact is **this
  verification document** (untracked, documentation).
* Historical: branch `main`, HEAD `20b7a928bb73fdfacf8271ff537a8fd245f62c79`; `status` entry count
  unchanged (305). **No file in the historical tree was touched.**
* The 32 substantive uncommitted historical files were read-only inspected for classification and were
  **not modified**.

Temporary computation output was written only to `/tmp/*`.

---

## 18. Final verdict

### 18.1 Summary of independent reproduction

* **Reproduced exactly:** the entire history arithmetic (2,000 / 553 / 1,659 / 341 / 545 / 537 / 204 /
  64), the API surface (809 / 407 / 395 / 46), the migration corpus (89 / 68 / 75 / 21) and all static
  DB-object counts (156/146, 112/85, 34, 221, 1), the 64-commit range stats (131 / 91 / 40 / 0 /
  41,503 / 46 and the per-directory split), the historical working-tree split (227 / 78 / 32 / 774 / 71),
  the table cardinalities (152 / 36 / 36 / 14 / 18), and a large set of support facts
  (`vercel.json` 6 headers + report-only CSP, no `render.yaml`/`Dockerfile`/`Procfile`, `main.py` silent
  V3 fallback, Prisma 3,510 lines / 129 models, 553 checkpoints, stale refs, `AGENTS.md` 29 lines).
* **Not reproduced:** several module/doc/file counts (§4.2) and two classifications/absences (§11.3).
* **The census's central thesis is independently confirmed:** the release tree is a strict, unmerged
  descendant of GitHub `main`; 204 commits exist only in canonical; the backend has a legacy+V3 dual
  mount (≈51 % legacy); six `p17*` migrations are repository-present and production-unapplied; the
  verification layer is BUILD-ONLY/unrun; and the investor-demo seeder + manifest are absent from the
  release tree while `AGENTS.md` §54 cites them.

### 18.2 Acceptance category

```
CT_RECON_02_INDEPENDENTLY_VERIFIED_PASS_WITH_OBSERVATIONS
```

**Rationale.** The overwhelming majority of CT-RECON-01's quantitative claims and **every** load-bearing
history, ancestry, API, migration and deployment-gate claim were independently reproduced. Its
read-only discipline, `PERSISTED ≠ applied` separation, and refusal to self-certify are correct and
exemplary. However, the verification found (a) a **false-absence** claim (CAP-138 / ledger "ABSENT = 3"),
(b) a **false-provenance** claim (ISS-013), (c) two **understated-wiring** classifications (CAP-121,
CAP-114), and (d) several non-reproducible secondary counts (§4.2). These are real but **localised** and
do **not** undermine the census's structural conclusions, so the census remains a **reliable discovery
baseline — conditional on the corrections in §16 (D-01…D-03 and the ledger count) being applied before
the affected rows are cited in PO decisions, notably POD-004 and POD-013.**

Because material (if localised) false claims exist, the census **must not** be treated as
`PASS` without qualification, and the discrepancy register (§16) is a mandatory companion to it.

### 18.3 Conditions on acceptance

1. CT-RECON-01 row **CAP-138** and ledger §5 ("ABSENT = 3") must be corrected (D-01).
2. Row **ISS-013** / §1.4 item 4 must be corrected (D-02).
3. Rows **CAP-121** and **CAP-114** wiring classifications must be corrected (D-03, D-04).
4. Secondary counts (§4.2) should be re-derived with an explicit, stated method or marked approximate.
5. Candidate omissions OM-01/OM-02 (§14) should be considered for inclusion.

None of the above was applied by this task (READ-ONLY).

### 18.4 Independence attestation

This verification:
* did **not** reuse CT-RECON-01's computed numbers without recomputation;
* did **not** copy the author's conclusions as its own;
* did **not** import the census into a harness that merely re-checks its own claims;
* inspected the actual repositories, Git objects and refs directly;
* explicitly identifies in §4–§13 which findings were independently reproduced.

**CT_RECON_02_COMPLETE**
