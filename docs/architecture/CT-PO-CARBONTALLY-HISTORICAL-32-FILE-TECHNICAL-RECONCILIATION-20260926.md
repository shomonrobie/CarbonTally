# CT-RECON-03B — CarbonTally Historical 32-File Technical Reconciliation

**Task ID:** `CT-RECON-03B-20260926-HISTORICAL-32-FILE-TECHNICAL-RECONCILIATION`
**Type:** READ-ONLY TECHNICAL RECONCILIATION — **no disposition decision, no file moved, no code changed**
**Date:** 2026-09-26
**Historical repository (primary subject):** `/home/shomonrobie/carbon_tally` — branch `main` — HEAD `20b7a928bb73fdfacf8271ff537a8fd245f62c79`
**Canonical repository (comparison target):** `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled` — HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`
**Writes performed:** two new Markdown documents in `docs/architecture/` of the canonical tree only. No source, SQL, migration, RLS, configuration, database, Git-history, reference or working-tree change. No file was deleted, copied, merged, stashed, checked out or modified.
**Population source:** the independently verified CT-RECON-03A report (`CT-PO-CARBONTALLY-HISTORICAL-32-FILE-MODIFICATION-TIMELINE-20260926.md`, verdict `CT_RECON_03A_COMPLETE_READ_ONLY_TIMELINE`). The population was **not** redefined. It was re-derived once, independently, as a control (`git diff --ignore-all-space --name-only` ⇒ 32 paths; `git diff --ignore-all-space --stat | tail` ⇒ `32 files changed, 774 insertions(+), 71 deletions(-)`) and matched the 03A population exactly, file for file.

> **Purpose.** CT-RECON-03A asked the Product Owner to recognise the 32 files *from memory*. The PO does not
> remember them, so memory was excluded and is not used anywhere in this document. Every statement below is
> derived from repository evidence: working-tree diffs against the historical HEAD, committed history in both
> repositories, symbol/call-site inspection of the current canonical code, migrations, tests and
> configuration.

---

## 1. Scope and question answered

For each of the 32 historical working-tree files this document answers, using repository evidence only:

1. **A** — what the working-tree change actually is (substantive additions/removals, whether it is only whitespace/formatting, the functions/classes/routes/components/tests/configuration it touches);
2. **B** — its historical lineage (historical `main` HEAD, `93d5cddd`, `f1a1cf8`, `20b7a928`, `refs/cline/checkpoints/*`, later commits on the same path);
3. **C** — the canonical comparison, *including moved / renamed / refactored / split / rewritten* implementations, not just same-filename lookup;
4. **D** — call-site analysis (imports, callers, route registration, frontend consumers, repositories, tests, DB objects, migrations, configuration), separating **CODE EXISTS** / **CODE IS WIRED** / **CODE IS TESTED** / **CODE IS CURRENTLY USED**;
5. **E** — later replacement detection across the whole canonical history, with commit SHA and symbol evidence;
6. **F** — tests and behaviour (equivalent current tests, newer tests, untested, no longer represented).

Classification vocabulary (fixed by the task): `INCORPORATED`, `SUPERSEDED`, `PARTIALLY_INCORPORATED`,
`STILL_MISSING_FROM_CANONICAL`, `OBSOLETE`, `ENVIRONMENT_GENERATED_OR_DEPENDENCY_ONLY`, `NEEDS_REVIEW`,
plus one factual shape label `NOT_SUBSTANTIVE` used only where a diff carries no substantive content at all
(a blank line). **No disposition (KEEP/DELETE/PORT/MERGE/ARCHIVE) is recommended.**

---

## 2. Repositories, baselines and control measurements

| Item | Historical | Canonical |
|---|---|---|
| Path | `/home/shomonrobie/carbon_tally` | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `main` | `p8-release-reconciled` |
| HEAD | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| `git status --porcelain` total | 305 (227 tracked ` M` + 78 untracked `??`) | 30 (1 tracked ` M` = pre-existing `.gitignore`, 29 untracked) |
| Substantive change set | 32 files / 774 insertions / 71 deletions (whitespace-insensitive) | n/a |

Control re-derivation, whitespace-insensitive (`--ignore-all-space`):

```
HISTORICAL  git diff --ignore-all-space --name-only            → 32 paths
HISTORICAL  git diff --ignore-all-space --stat | tail          → 32 files changed, 774 insertions(+), 71 deletions(-)
HISTORICAL  git diff --ignore-all-space --numstat (32 paths)   → reproduced per file in §4
```

All 32 paths are **tracked modifications** (` M`) present in `20b7a928`; none of them is an untracked file.
Per-file working-tree mtimes (evidence of *when last written*, not of intent) are recorded in §5.

No production system, database, Supabase instance, Vercel endpoint, Render endpoint, branch, tag or
reference was created, moved or contacted. All scratch artefacts were written to `/tmp/` only.

---

## 3. Method and the limits of the measurements

**Technique.** For each of the 32 files the following read-only probes were executed:

```
git diff --ignore-all-space --numstat  -- <path>        # substantive size vs the historical HEAD
git diff --ignore-all-space -U0        -- <path>        # hunk headers (where the change lands)
git diff --ignore-all-space            -- <path>        # full patch body
git status --porcelain                 -- <path>        # tracked vs untracked
git log -1 --format='%h|%ad|%s'        -- <path>        # last committed historical version
diff -w <worktree> (<ref>:<path>)                       # equality probes vs 93d5cddd / f1a1cf8 / 20b7a928
diff -w <worktree> (<canonical path>)                   # equality probe vs the canonical worktree
git -C <canonical> cat-file -e HEAD:<path>              # canonical HEAD blob presence
git -C <canonical> log --oneline -- <path>              # full canonical lineage (count + first + last)
# whitespace-normalised line-set membership of every ADDED line against
# the canonical worktree file and the canonical HEAD blob
# plus symbol-level greps across canonical source, tests, migrations, config
```

**Verbatim-line metric — and its limit.** The added-line incorporation rate (§5) is a *whitespace-insensitive
set-membership* measure. It over-reports for generic lines (`});`, `</div>`, `return` can match coincidentally)
and under-reports for re-implemented lines (the same logic written with a different parameter or variable name
does not match verbatim). Therefore:

* a **high** rate (>= 90 %) is treated as strong evidence of incorporation, but is always corroborated by
  symbol-level evidence before a classification is assigned;
* a **low** rate is **not** by itself evidence of loss — the canonical implementation may have been rewritten
  or restructured. Every low-rate file in this set was resolved by symbol/call-site inspection (§5);
* no classification in this document rests on the metric alone, on file age, on filename similarity, on
  commit date, on coding style, or on the mere existence of a newer file.

**Historical content origin (relevant to several classifications).** For a subset of the 32 files the
historical *working-tree* content is whitespace-identical to commit `93d5cddd` (a canonical ancestor), while
the historical tracked baseline (`20b7a928`) is older. Those files therefore combine “already-committed
canonical content” with “a working-tree-only delta relative to `20b7a928`”. Both aspects are reported
separately in §5 so that neither is mistaken for the other.


---

## 4. Master reconciliation table (32 files)

The plan for this section called for a single 32-row table carrying every field. Rendered that way the table
is unreadable, so the same fields are split across **Table 4A (measurement)** and **Table 4B
(disposition)**, both keyed by the same stable IDs `HIST-01 … HIST-32`. Nothing is dropped: the long-form
evidence for every field named in the task brief (purpose, commits, call sites, tests, DB/migration
dependency, reachability, incorporation evidence, supersession evidence, loss risk, next action) is carried
per file in §5, and Table 4B carries the classification, confidence and canonical equivalent.

**ID scheme.** `HIST-nn` follows the deterministic path-sorted population boundary established and verified
in the 32-file scope check (§1). IDs are stable and must be reused in any follow-up document.

**Table 4A column definitions**

| Column | Meaning |
|---|---|
| `Δ +/−` | additions / deletions from the whitespace-insensitive numstat of the historical **working tree** against the historical tracked baseline `20b7a928` (the historical file's own committed state). This is the historical *delta under investigation*, not the file size. |
| `distinct A/D` | distinct non-blank added / removed lines after whitespace-stripping and de-duplication (the basis of the incorporation metric). |
| `verbatim wt/HEAD` | added lines present verbatim in the **canonical worktree file** / in the **canonical `HEAD:<path>` blob**. Equal counts confirm the canonical working tree carries the same content as `cb70fd6`. |
| `vs 93d5cddd` | whether the historical working-tree content is byte-identical (`SAME`) or different (`DIFF`) from canonical ancestor `93d5cddd`. `SAME` means the file's historical working-tree content is already-committed canonical content, and only the delta against `20b7a928` is historical. |
| `canon n` | number of canonical commits that touch the path (canonical branch `p8-release-reconciled`). |
| `newest canon commit` | the most recent canonical commit that touches the path (`git log -1 --format=%h`). |

**Reading rule.** A low `verbatim` ratio is **not** evidence of loss (§3); every low-ratio row in this table
was resolved by symbol-, call-site- or object-level inspection in §5, and each disposition states the
concrete evidence. No row is classified on the metric, on file age, on filename similarity or on style.

### 4.1 Table 4A — measurement (historical working tree vs `20b7a928`; canonical = `cb70fd6`)

| ID | Historical path (worktree, branch `main`) | Δ +/− | distinct A/D | verbatim wt/HEAD | vs `93d5cddd` | canon n | newest canon commit |
|---|---|---|---|---|---|---|---|
| HIST-01 | `AGENTS.md` | 29/0 | 21/0 | 1/1 | DIFF | 1 | `5a1e45e` |
| HIST-02 | `CarbonTally_DB_Schema_V3M2.sql` | 16/0 | 7/0 | 1/1 | DIFF | 1 | `cfabe26` |
| HIST-03 | `admin/package-lock.json` | 132/2 | 83/1 | 15/15 | DIFF | 1 | `a16ba01` |
| HIST-04 | `admin/package.json` | 2/0 | 2/0 | 0/0 | DIFF | 2 | `cb70fd6` |
| HIST-05 | `admin/src/components/admin/ImportDefraModal.js` | 7/0 | 7/0 | 0/0 | DIFF | 1 | `a16ba01` |
| HIST-06 | `admin/src/components/admin/ReviewExtractionModal.js` | 8/0 | 8/0 | 2/2 | DIFF | 1 | `a16ba01` |
| HIST-07 | `admin/src/components/admin/ReviewWorkflow.js` | 17/0 | 10/0 | 2/2 | DIFF | 1 | `987500a` |
| HIST-08 | `admin/src/context/AuthContext.js` | 12/0 | 10/0 | 0/0 | DIFF | 3 | `cb70fd6` |
| HIST-09 | `admin/src/index.js` | 21/0 | 17/0 | 0/0 | DIFF | 2 | `cb70fd6` |
| HIST-10 | `admin/src/pages/admin/BetaManagement.js` | 4/0 | 4/0 | 0/0 | DIFF | 4 | `425671a` |
| HIST-11 | `admin/src/pages/admin/Settings.js` | 7/0 | 7/0 | 5/5 | DIFF | 2 | `9c68ab1` |
| HIST-12 | `admin/src/pages/admin/Users.js` | 5/0 | 5/0 | 2/2 | DIFF | 3 | `2d23fb8` |
| HIST-13 | `backend/api/v3_operations.py` | 3/2 | 1/1 | 1/1 | DIFF | 19 | `6eedb7b` |
| HIST-14 | `backend/api/v3_reports.py` | 15/2 | 11/2 | 11/11 | SAME | 4 | `eb6a0c2` |
| HIST-15 | `backend/data/emissions_logs.py` | 6/3 | 6/2 | 3/3 | SAME | 15 | `0f248ad` |
| HIST-16 | `backend/data/manual_extraction.py` | 63/1 | 43/1 | 41/41 | SAME | 5 | `b87ff38` |
| HIST-17 | `backend/domain/automatic_processing.py` | 1/1 | 1/1 | 0/0 | SAME | 4 | `ad07cd4` |
| HIST-18 | `backend/domain/calculation.py` | 21/4 | 20/3 | 20/20 | SAME | 6 | `5713073` |
| HIST-19 | `backend/engines/calculation.py` | 8/0 | 8/0 | 8/8 | SAME | 11 | `0f248ad` |
| HIST-20 | `backend/services/automatic_extraction.py` | 51/0 | 44/0 | 33/33 | DIFF | 8 | `653d5a3` |
| HIST-21 | `backend/services/automatic_processing.py` | 22/2 | 21/2 | 20/20 | DIFF | 18 | `999e4fb` |
| HIST-22 | `backend/tests/integration/conftest.py` | 20/0 | 18/0 | 17/17 | SAME | 5 | `0d21e46` |
| HIST-23 | `backend/tests/integration/test_report_versions.py` | 5/1 | 5/1 | 5/5 | SAME | 3 | `eb6a0c2` |
| HIST-24 | `backend/tests/integration/test_reports.py` | 9/5 | 9/5 | 9/9 | SAME | 3 | `eb6a0c2` |
| HIST-25 | `backend/tests/unit/api/test_v3_report_lifecycle.py` | 112/0 | 63/0 | 62/62 | SAME | 2 | `eb6a0c2` |
| HIST-26 | `frontend/src/App.js` | 0/1 | 0/0 | n/a | DIFF | 29 | `fb3eba1` |
| HIST-27 | `frontend/src/v3/api.js` | 40/1 | 25/0 | 24/24 | DIFF | 21 | `fb3eba1` |
| HIST-28 | `frontend/src/v3/reports/ReportDetailPage.jsx` | 7/0 | 6/0 | 5/5 | SAME | 3 | `eb6a0c2` |
| HIST-29 | `frontend/src/v3/reports/reports.css` | 65/0 | 49/0 | 49/49 | DIFF | 4 | `6cd36fc` |
| HIST-30 | `output/reports/import_summary.md` | 47/27 | 38/27 | 3/3 | DIFF | 1 | `2d23fb8` |
| HIST-31 | `requirements.txt` | 12/12 | 12/12 | 0/0 | DIFF | 4 | `a16ba01` |
| HIST-32 | `supabase/config.toml` | 7/7 | 7/7 | 1/1 | DIFF | 1 | `2d23fb8` |

**Two corrections to raw-artefact readings, recorded for reproducibility.** HIST-14 and HIST-28 are `SAME`
against `93d5cddd` **and** `SAME` against the canonical worktree, i.e. their historical working-tree
content is already-committed, already-canonical content. Any earlier or derived reading that labels either
file `DIFF` is measuring a different probe (their `f1a1cf8`/`HEAD`-blob comparisons) and must not be used as
the authoritative relation.

### 4.2 Table 4B — disposition per historic delta

**Classification vocabulary** (applied strictly; a file is only placed in the first two classes when the
canonical repository contains a concrete, nameable successor or replacement):

| Classification | Test that must be satisfied |
|---|---|
| `INCORPORATED` | The substance of the historical delta is present in canonical (`cb70fd6`) — verified by verbatim line match **and** a symbol/object/call-site that realises the same behaviour. May be qualified `ADVANCED` (canonical implements it more completely) or `RESIDUAL` (a measurable sub-element is not carried). |
| `SUPERSEDED` | A newer, ratified decision or mechanism in canonical replaces the historical approach, so re-applying the historical delta would contradict canonical state. Requires a nameable decision/mechanism **and** evidence that the old approach is absent by design. |
| `OBSOLETE` | The historical delta addresses an architecture canonical no longer contains, so the delta has nothing to attach to. Requires obviated-architecture evidence. *(Not used for any file in this population.)* |
| `NEEDS_REVIEW` | No concrete successor and no obviating evidence could be established from repository state alone; left open for a human decision. |
| `NOT_SUBSTANTIVE` | The historical delta carries no meaningful content (whitespace/blank-line only). |

**Confidence** = strength of the *canonical-side* evidence: `HIGH` = named symbol/object/decision verified in
canonical source; `MEDIUM` = strong but partial (e.g. capability coverage rather than line identity);
`LOW` = inference only. **Loss risk** = risk that a *business or security capability* is absent from canonical
because the historical delta was not carried; `NONE` where the delta is measurement-only or already
canonical, `LOW`/`MEDIUM` where only a non-business capability (analytics, generated artefact, environment
config) is affected. No row in this population reaches `HIGH` loss risk.


| ID | Path | Classification | Conf | Canonical equivalent / replacement | Loss risk | Next action |
|---|---|---|---|---|---|---|
| HIST-01 | `AGENTS.md` | `INCORPORATED` + `RESIDUAL` (doc gap) | HIGH | F-046-1 invariant enforced in `backend/tests/integration/conftest.py` (`FORBIDDEN_MAIN_DB_NAMES` L44, `PROTECTED_PERSISTENT_MARKERS` L51, refusal L115–124); policy §55.1 text **absent** from canonical `AGENTS.md` | LOW | PO/eng decision: port §55.1 into canonical `AGENTS.md` so the constitution states the invariant its own code already enforces |
| HIST-02 | `CarbonTally_DB_Schema_V3M2.sql` | `SUPERSEDED` (delivery mechanism) | HIGH (definitions) / UNVERIFIED (live DB) | `d21_white_label_branding.sql` L21 `white_label_enabled`; `d22_processing_work_assignment.sql` L25 `entity_id`, L34–35 FK→`processing_entities` `ON DELETE RESTRICT`, L40–41 index, L88–95 / L102–112 entity RLS policies (canonical is a superset: it adds the index) | LOW | none required; live-database object presence remains a separate DB-verification item |
| HIST-03 | `admin/package-lock.json` | `SUPERSEDED` | HIGH | the posthog dependency tree (`posthog-js`, `@posthog/react` + `@posthog/{browser-common,core,types}`, `dompurify`, `fflate`, `preact`, `query-selector-shadow-dom`, `web-vitals`, `web-vitals-soft-navs`, `core-js`) is a client-analytics provider canonical does not adopt | LOW | none required; keep the file at its committed canonical state |
| HIST-04 | `admin/package.json` | `SUPERSEDED` | HIGH | same provider decision; canonical `admin/package.json` instead gained `"prebuild": "node ../tools/generate_build_info.js ."` in `cb70fd6` (build provenance) | LOW | none required |
| HIST-05 | `admin/src/components/admin/ImportDefraModal.js` | `SUPERSEDED` | HIGH | GA4 provider decision (`37b19d1`, an ancestor of `HEAD`); canonical admin contains no analytics client (`captureEvent`/`identifyUser`/`posthog` = 0 hits outside `node_modules`) | LOW | none required; consider recording the retired event taxonomy for a future GA4 event mapping |
| HIST-06 | `admin/src/components/admin/ReviewExtractionModal.js` | `SUPERSEDED` | HIGH | as HIST-05 (event `extraction_review_completed`) | LOW | none required |
| HIST-07 | `admin/src/components/admin/ReviewWorkflow.js` | `SUPERSEDED` | HIGH | as HIST-05 (events `review_started` / `review_completed` / `review_reassigned`). Canonical `'review_completed'` hits are notification/activity *types* (`admin/src/components/layout/TopBar.js`, `frontend/src/components/ActivityFeed.jsx`), **not** analytics events | LOW | none required |
| HIST-08 | `admin/src/context/AuthContext.js` | `SUPERSEDED` | HIGH | as HIST-05 (identity calls `identifyUser`/`resetAnalytics`); canonical `AuthContext.js` was last changed by `cb70fd6` for fail-closed auth/config, an unrelated concern | LOW | none required |
| HIST-09 | `admin/src/index.js` | `SUPERSEDED` | HIGH | as HIST-05; the PostHog SDK install exists only on the unmerged branch `remotes/github/posthog-self-driving/featanalytics-install-posthog-sdk-in-c0bc29` (`363105a`, not an ancestor of `HEAD`) | LOW | none required |
| HIST-10 | `admin/src/pages/admin/BetaManagement.js` | `SUPERSEDED` | HIGH | as HIST-05 (event `beta_invite_sent`) | LOW | none required |
| HIST-11 | `admin/src/pages/admin/Settings.js` | `SUPERSEDED` | HIGH | as HIST-05 (event `settings_updated`). Canonical `Settings.js` retains an unrelated GDPR-copy checkbox `anonymize_analytics`, which is UI copy, not an analytics client | LOW | none required |
| HIST-12 | `admin/src/pages/admin/Users.js` | `SUPERSEDED` | HIGH | as HIST-05 (event `staff_user_created`) | LOW | none required |

| HIST-13 | `backend/api/v3_operations.py` | `INCORPORATED` | HIGH | `save_extracted_data(item_id, payload.extracted_data, context.profile.user_id, "manual")` at canonical L1163–1165 and L1740–1742 (verbatim) | NONE | none required |
| HIST-14 | `backend/api/v3_reports.py` | `INCORPORATED` | HIGH | identical content in canonical (worktree and `HEAD:<path>`); 11/11 added lines verbatim | NONE | none required |
| HIST-15 | `backend/data/emissions_logs.py` | `INCORPORATED` (`ADVANCED`) | HIGH | `source_line_item_id` in canonical at L102, L570, L575, L820, L856 and in the snapshot join at L997 | NONE | none required |
| HIST-16 | `backend/data/manual_extraction.py` | `INCORPORATED` | HIGH | canonical L14 `EvidenceLineItemsRepository`, L15 `MATERIALISATION_FORWARD`, L450/L517 `extraction_method` kwarg, L472/L541 call sites, L481 `_materialise_evidence_lines`, L500 `materialise_for_item`, L503 `materialisation_kind=MATERIALISATION_FORWARD` | NONE | none required |
| HIST-17 | `backend/domain/automatic_processing.py` | `INCORPORATED` (`ADVANCED`) | HIGH | same file, same location: canonical L45 `PIPELINE_VERSION = "v3-auto-1.2"` vs historical `v3-auto-1.1` (value advanced, mechanism identical) | NONE | none required |
| HIST-18 | `backend/domain/calculation.py` | `INCORPORATED` | HIGH | 20/20 added lines verbatim in canonical worktree and blob | NONE | none required |
| HIST-19 | `backend/engines/calculation.py` | `INCORPORATED` | HIGH | 8/8 added lines verbatim in canonical worktree and blob | NONE | none required |
| HIST-20 | `backend/services/automatic_extraction.py` | `INCORPORATED` + `ADVANCED` | HIGH | canonical generalises the same hook into `_apply_p1_fidelity(...)` (def at L378), importing `services.extraction_fidelity as p1` (L403) and using `p1.shape_mode` / `rollout_status` / `classify` / `ai_fanout_plan` / `build_line_items`; the function's own docstring records that the historical wiring covered only `_extract_pdf` and left scanned multi-line images collapsed | NONE | none required |
| HIST-21 | `backend/services/automatic_processing.py` | `INCORPORATED` | HIGH | canonical L1822–1841 reproduces the B2 §13.2 ordinal→materialised-line lookup via `evidence_line_items.get_by_ordinals` and threads `source_line_item_id` into the request at L1928 | NONE | none required |
| HIST-22 | `backend/tests/integration/conftest.py` | `INCORPORATED` | HIGH | canonical newest commit on path is `0d21e46 fix(p8-f046-1): enforce the protected-persistent-target refusal in the integration harness`; guard verified at L44 / L51 / L109 / L115–124 | NONE | none required |
| HIST-23 | `backend/tests/integration/test_report_versions.py` | `INCORPORATED` | HIGH | identical content in canonical; 5/5 added lines verbatim | NONE | none required |
| HIST-24 | `backend/tests/integration/test_reports.py` | `INCORPORATED` | HIGH | identical content in canonical; 9/9 added lines verbatim | NONE | none required |
| HIST-25 | `backend/tests/unit/api/test_v3_report_lifecycle.py` | `INCORPORATED` | HIGH | identical content in canonical (the +112-line lifecycle test block); 62/63 verbatim | NONE | none required |
| HIST-26 | `frontend/src/App.js` | `NOT_SUBSTANTIVE` | HIGH | delta is the deletion of **one blank line** inside the `/ops/operational-health` comment block; the route itself exists in canonical at L2231–2236 | NONE | none required |
| HIST-27 | `frontend/src/v3/api.js` | `INCORPORATED` | HIGH | canonical exports `REPORT_LIFECYCLE_ACTION_CALLS` at L211, consumed by the lifecycle panel | NONE | none required |
| HIST-28 | `frontend/src/v3/reports/ReportDetailPage.jsx` | `INCORPORATED` | HIGH | canonical L17 imports and L234 mounts `ReportLifecyclePanel` | NONE | none required |
| HIST-29 | `frontend/src/v3/reports/reports.css` | `INCORPORATED` | HIGH | 49/49 added lines verbatim in canonical worktree and blob | NONE | none required |
| HIST-30 | `output/reports/import_summary.md` | `NEEDS_REVIEW` | MEDIUM–HIGH | no generator for this path exists anywhere in canonical (`backend/`, `tools/`, `scripts/` searched for `import_summary` → 0 hits); canonical blob is the older `2d23fb8` version. The historical working tree holds a *newer* run record (2026-08-15, 7,029 factors, DEFRA-2025, workbook SHA-256) | LOW | human decision: treat as a one-off evidence artefact (no action) or reconstruct the importing tool; DB-level verification of the imported factor set is required before any claim about current factor data |
| HIST-31 | `requirements.txt` | `SUPERSEDED` | MEDIUM–HIGH | capability-equivalent canonical manifests: root `requirements.txt` (12 pinned deps) and `backend/requirements.txt` (the same 12 as ranges **plus** `reportlab`, `python-dotenv`, `pypdf2`, `supabase`, `PyJWT`, `asyncpg`, `openpyxl` and an OCR comment) — a superset of the historical delta | LOW | none required; note the historical root-level un-pinning was not adopted (canonical root stays pinned) — a dependency-posture choice, not a business policy |
| HIST-32 | `supabase/config.toml` | `INCORPORATED` + `RESIDUAL` | HIGH (ports) / MEDIUM (flag) | the 5442x port remap **is** the environment canonical depends on: `backend/tests/integration/conftest.py` L40 `…127.0.0.1:54426/carbontally_test`, L58 `SUPABASE_URL=http://127.0.0.1:54425`, plus `ct_*` / `carbontally_test` DSNs throughout the integration suite. Residual: historical `[db.migrations] enabled = false` is not in canonical `config.toml` (unchanged since `2d23fb8`) | LOW | PO/eng decision: align canonical `supabase/config.toml` local ports with the 5442x stack its own harness assumes, and decide the `db.migrations` flag explicitly rather than by inheritance |



---

## 5. Per-file findings

Entries use a fixed template so that every field required by the task brief is answered for every file:
**purpose** of the historical delta, **delta as measured**, **historical commit context**, **canonical
equivalent and call sites**, **tests**, **database/migration dependency**, **reachability**,
**incorporation or supersession evidence**, **loss risk and next action**.

**Reading rules that apply to every entry**

* "Historical" always means the **working tree** of `/home/shomonrobie/carbon_tally` (branch `main`, HEAD
  `20b7a928`) as measured in §2, not the committed historical file.
* `SAME` against `93d5cddd` means the historical working-tree content is **already-committed canonical
  content**; in those cases the delta against `20b7a928` is *behind* canonical, and the file cannot be a
  source of un-adopted canonical change (§3).
* Integration tests in `backend/tests/integration/**` are **destructive-setup** suites. Any execution of them
  requires a disposable `ct_*` clone or `carbontally_test`, per AGENTS.md §55.1 / F-046-1. No test was
  executed for this read-only task (§2, control measurements).

### 5.1 Cluster A — client-analytics retirement (HIST-03 … HIST-12)

All ten files belong to one uncommitted, working-tree-only change set: adding PostHog client instrumentation
to the **admin** React app (the admin SPA is part of the canonical build — canonical root `package.json`
builds both apps). The instrumentation routes through an **untracked** helper (`git status --porcelain`
reports `?? admin/src/analytics.js`, 548 bytes) that wraps `captureEvent` / `identifyUser` / `resetAnalytics`;
nine tracked files were edited to call it and one dependency pair was declared. The delta was therefore never
committed in the historical repository either, and its helper module is part of no commit.

**Shared supersession evidence (applies to HIST-03 … HIST-12).**

1. **Provider decision, not a lost feature.** The adopted analytics capability in canonical is Google
   Analytics 4, configured from the admin application: `docs/architecture/CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md`
   and `frontend/src/lib/analytics/ga4.js` (+ `ga4.test.js`) are present, and commit `37b19d1`
   (`feat(admin): admin-configurable Google Analytics 4 (Analytics & Integrations)`, 2026-09-13) **is an
   ancestor of `cb70fd6`** (verified with `git merge-base --is-ancestor`).
2. **The PostHog delta was never merged.** Commit `363105a`
   (`feat(analytics): install PostHog SDK on the public frontend`, 2026-09-14) is **not** an ancestor of
   `HEAD`; its work lives only on `remotes/github/posthog-self-driving/featanalytics-install-posthog-sdk-in-c0bc29`.
   (`0bc203f` carries the same subject line as `37b19d1` but is likewise not an ancestor of `HEAD`.)
3. **No analytics client exists in canonical application source.** `grep` for `captureEvent`, `identifyUser`,
   `resetAnalytics` and `posthog` across `admin/src`, `frontend/src` and `backend` returns **zero** hits
   outside `node_modules` (the only `posthog` strings in the canonical tree are `react-icons` icon exports).
4. **No event names survived.** None of the historical event names is emitted anywhere in canonical
   application source. The single apparent exception is `'review_completed'`, which in canonical is a
   **notification/activity type** (`admin/src/components/layout/TopBar.js`, `AdminNotificationBell.jsx`,
   `frontend/src/components/ActivityFeed.jsx`, `frontend/src/services/NotificationService.js`) — a
   pre-existing unrelated feature, explicitly *not* evidence of analytics incorporation.

**Consequence.** These ten rows are classified `SUPERSEDED`: re-applying the delta would reintroduce a
retired provider. The residual capability question — custom product events are not emitted at all, so the
admin funnel (DEFRA imports, review actions, invites, staff creation, settings changes, login/logout) is
uninstrumented — is recorded once here and is a **product-analytics decision**, not a business-workflow
defect: no workflow, data, provenance or security behaviour depends on it. Loss risk for each row is `LOW`.

#### HIST-03 — `admin/package-lock.json`

* **Purpose of the delta.** Declare and lock the PostHog client dependency tree for the admin app.
* **Delta as measured.** Δ `132/2`; 83 distinct added / 1 removed line; verbatim match 15/83 in both the
  canonical worktree and the canonical `HEAD` blob — the 15 matches are coincidental generic JSON lines
  (`}`, `"devOptional": true`, common `"integrity"` values), not dependency identity.
* **Content.** `@posthog/react ^1.10.6` and `posthog-js ^1.430.3` plus transitive entries
  `@posthog/browser-common 0.8.3`, `@posthog/core 1.53.2`, `@posthog/types`, `dompurify ^3.4.13`,
  `fflate ^0.4.8`, `preact`, `query-selector-shadow-dom`, `web-vitals`, `web-vitals-soft-navs`,
  `tailwindcss/node_modules/yaml`, `core-js ^3.49.0`.
* **Historical commit context.** Last historical commit on the path: `a16ba01` (2026-07-21) "Add admin
  dashboard, update structure, remove sensitive files"; relation to `93d5cddd`: `DIFF`.
* **Canonical equivalent and call sites.** None. Canonical `admin/package-lock.json` is unchanged since
  `a16ba01` (canonical lineage `n=1`) and contains **no** posthog entries.
* **Tests / DB dependency / reachability.** No test references the lock file; no database dependency;
  reachable only through `npm install` in `admin/`, which canonical never performs for these packages.
* **Evidence.** Cluster A items 1–3.
* **Loss risk / next action.** `LOW` (a declaration for a retired provider) / none required.

#### HIST-04 — `admin/package.json`

* **Purpose of the delta.** Add the two direct PostHog dependencies to the admin manifest.
* **Delta as measured.** Δ `2/0`; 2 distinct added lines; verbatim match 0/2.
* **Content.** `"@posthog/react": "^1.10.6"` and `"posthog-js": "^1.430.3"` in `dependencies` (hunks at
  manifest lines 7/13).
* **Historical commit context.** Last historical commit on the path `a16ba01` (2026-07-21); `DIFF` vs
  `93d5cddd`.
* **Canonical equivalent and call sites.** Canonical `admin/package.json` (canonical lineage `n=2`) has
  instead acquired a **build-provenance** script, `"prebuild": "node ../tools/generate_build_info.js ."`,
  added by `cb70fd6` together with `window.__CARBONTALLY_BUILD_INFO__` — an unrelated concern, and no
  substitute for the analytics dependency.
* **Tests / DB dependency / reachability.** Canonical admin tests (`admin/src/*.test.js`; `cb70fd6` reports
  22 passing) contain no PostHog references; no database dependency; reachable via `npm run build` / `start`.
* **Evidence.** Cluster A items 1–3. Facet note: `cb70fd6` changed `scripts` only, and `scripts` do not
  enter the dependency graph, so the lock file's unchanged state is consistent and is not drift.
* **Loss risk / next action.** `LOW` / none required.

#### HIST-05 — `admin/src/components/admin/ImportDefraModal.js`

* **Purpose of the delta.** Emit a product-analytics event when a DEFRA factor import completes.
* **Delta as measured.** Δ `7/0`; 7 distinct added lines; verbatim match 0/7 (none of the added lines exists
  in canonical).
* **Content.** `import { captureEvent } from '../../analytics';` (line 6) and
  `captureEvent('defra_factors_imported', {…})` (line 100) inside the import success path.
* **Historical commit context.** Last historical commit on the path `a16ba01` (2026-07-21); `DIFF` vs
  `93d5cddd`.
* **Canonical equivalent and call sites.** No analytics call; the DEFRA-import modal still exists in
  canonical and its **business** effect (factors persisted through the admin import path) is unaffected. The
  canonical DEFRA factor-set notion is present elsewhere (`DEFRA-2025` is referenced by multiple canonical
  integration tests).
* **Tests / DB dependency / reachability.** No test asserts the event; no DB change; reachable from the admin
  UI when the modal is opened and an import succeeds.
* **Evidence.** Cluster A items 1–4 (`'defra_factors_imported'` → 0 hits in canonical source).
* **Loss risk / next action.** `LOW` / none required.

#### HIST-06 — `admin/src/components/admin/ReviewExtractionModal.js`

* **Purpose of the delta.** Emit an event when a staff member completes an extraction review.
* **Delta as measured.** Δ `8/0`; 8 distinct added lines; verbatim match 2/8 (the 2 matches are generic JSX
  lines; the substantive added lines do not exist in canonical).
* **Content.** `import { captureEvent } from '../../analytics';` (line 16) and
  `captureEvent('extraction_review_completed', {…})` (line 154).
* **Historical commit context.** Last historical commit on the path `a16ba01` (2026-07-21); `DIFF` vs
  `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics. The review action's real canonical
  consequences are server-side (`backend/api/v3_operations.py` review endpoints and their audit records),
  which the event never drove.
* **Tests / DB dependency / reachability.** No test asserts the event; no DB change; reachable when the
  extraction-review modal completes.
* **Evidence.** Cluster A items 1–4 (`'extraction_review_completed'` → 0 hits in canonical source).
* **Loss risk / next action.** `LOW` / none required.

#### HIST-07 — `admin/src/components/admin/ReviewWorkflow.js`

* **Purpose of the delta.** Emit events at the three staff review transitions.
* **Delta as measured.** Δ `17/0`; 10 distinct added lines; verbatim match 2/10.
* **Content.** `import { captureEvent } from '../../analytics';` (line 6), `captureEvent('review_started', …)`
  (line 48), `captureEvent('review_completed', …)` (line 85), `captureEvent('review_reassigned', …)`
  (line 106).
* **Historical commit context.** Last historical commit on the path `987500a` (2026-07-23) "Major update:
  Staff dashboard, Review assignment, Beta management"; `DIFF` vs `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics; canonical review transitions are
  server-authoritative and unchanged.
* **Tests / DB dependency / reachability.** No test asserts these events; no DB change; reachable from the
  staff review UI.
* **Evidence.** Cluster A items 1–4, **with the explicit caveat** on `'review_completed'`: canonical hits are
  notification/activity **types** (`TopBar.js`, `ActivityFeed.jsx`, `NotificationService.js`), a pre-existing
  feature, not an analytics event.
* **Loss risk / next action.** `LOW` / none required.

#### HIST-08 — `admin/src/context/AuthContext.js`

* **Purpose of the delta.** Identify the signed-in user and emit login/logout events.
* **Delta as measured.** Δ `12/0`; 10 distinct added lines; verbatim match 0/10.
* **Content.** `import { captureEvent, identifyUser, resetAnalytics } from '../analytics';` (line 5), plus
  `identifyUser(...)` at lines 40, 51, 82, 180, `resetAnalytics()` at 57, `captureEvent('user_logged_in', …)`
  at 181 and `captureEvent('user_logged_out', …)` at 203.
* **Historical commit context.** Last historical commit on the path `9c68ab1` (2026-07-27) "Major update:
  Manual Entry, Staff Review Queue, Admin Assignment, Document Status, and Log Viewer"; `DIFF` vs
  `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics. Canonical `AuthContext.js` has since been
  changed by `cb70fd6` for a different purpose — Supabase configuration is reported rather than thrown at
  import time, and `AuthContext` / `isAdminOrStaff` fail closed. Security behaviour is therefore *stronger*,
  not weaker, in canonical; the analytics delta is orthogonal.
* **Tests / DB dependency / reachability.** `cb70fd6` added admin tests for the fail-closed behaviour
  (`admin/src/App.configNotice.test.js`, `admin/src/supabaseClient.test.js`) but none references analytics;
  no DB change; reachable on every admin sign-in/out.
* **Evidence.** Cluster A items 1–4 (`identifyUser` / `resetAnalytics` → 0 hits in canonical source).
* **Loss risk / next action.** `LOW` / none required.

#### HIST-09 — `admin/src/index.js`

* **Purpose of the delta.** Initialise the PostHog SDK at admin bootstrap and wrap the app in its provider
  and error boundary.
* **Delta as measured.** Δ `21/0`; 17 distinct added lines; verbatim match 0/17.
* **Content.** `import posthog from 'posthog-js';` (line 8),
  `import { PostHogErrorBoundary, PostHogProvider } from '@posthog/react';` (line 9),
  `REACT_APP_POSTHOG_PROJECT_TOKEN` / `REACT_APP_POSTHOG_HOST` reads (lines 11–12),
  `posthog.init(...)` (lines 14–16), a **hard throw** when either variable is missing (line 23), and the
  `<PostHogProvider><PostHogErrorBoundary>` wrapper (lines 38–53).
* **Historical commit context.** Last historical commit on the path `a16ba01` (2026-07-21); `DIFF` vs
  `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics. Canonical `admin/src/index.js` (lineage
  `n=2`) was changed by `cb70fd6` to publish build provenance before render — the opposite posture to the
  historical delta's hard throw: canonical **reports** missing provenance/configuration (`UNKNOWN`, a
  controlled `AdminConfigNotice`) instead of crashing the app.
* **Tests / DB dependency / reachability.** No canonical test references PostHog; no DB change; reachable at
  admin bootstrap.
* **Evidence.** Cluster A items 1–3, plus item 2: the SDK installation exists only on the unmerged branch
  `remotes/github/posthog-self-driving/featanalytics-install-posthog-sdk-in-c0bc29` (`363105a`, not an
  ancestor of `HEAD`).
* **Loss risk / next action.** `LOW` / none required. Note for the record: had this delta been adopted, a
  missing *analytics* environment variable would have become fatal to the **entire admin application**
  (a top-level `throw` before render), which contradicts the canonical posture established in `cb70fd6`
  (configuration problems are reported through a controlled notice; missing provenance is reported as
  `UNKNOWN`). Not carrying this delta is consistent with canonical behaviour rather than a loss.

#### HIST-10 — `admin/src/pages/admin/BetaManagement.js`

* **Purpose of the delta.** Emit an event when a beta invite is sent.
* **Delta as measured.** Δ `4/0`; 4 distinct added lines; verbatim match 0/4.
* **Content.** `import { captureEvent } from '../../analytics';` (line 20) and
  `captureEvent('beta_invite_sent', {…})` (line 86).
* **Historical commit context.** Last historical commit on the path `425671a` (2026-07-24) "fix: beta login3."
  (path lineage in the historical repo: `425671a`, `34b81e9`, `a34b2f0`, `987500a`); `DIFF` vs `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics. Beta/invite behaviour itself is a
  server-side capability in canonical and was not driven by this event.
* **Tests / DB dependency / reachability.** No test asserts the event; no DB change; reachable from the beta
  management screen.
* **Evidence.** Cluster A items 1–4 (`'beta_invite_sent'` → 0 hits in canonical source).
* **Loss risk / next action.** `LOW` / none required.

#### HIST-11 — `admin/src/pages/admin/Settings.js`

* **Purpose of the delta.** Emit an event when organisation/platform settings are saved.
* **Delta as measured.** Δ `7/0`; 7 distinct added lines; verbatim match 5/7 in both canonical worktree and
  blob — the 5 matches are the generic form/section lines that also exist in canonical `Settings.js`; the 2
  substantive lines (the import and the call) are absent.
* **Content.** `import { captureEvent } from '../../analytics';` (line 7) and
  `captureEvent('settings_updated', {…})` (line 187).
* **Historical commit context.** Last historical commit on the path `9c68ab1` (2026-07-27); `DIFF` vs
  `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics. Canonical `Settings.js` retains only the
  pre-existing GDPR copy control `anonymize_analytics` (a checkbox label — UI copy, not an analytics
  client); this is not a substitute and is called out here so it is not mistaken for one.
* **Tests / DB dependency / reachability.** No test asserts the event; no DB change; reachable from the admin
  settings screen.
* **Evidence.** Cluster A items 1–4 (`'settings_updated'` → 0 hits in canonical source).
* **Loss risk / next action.** `LOW` / none required.

#### HIST-12 — `admin/src/pages/admin/Users.js`

* **Purpose of the delta.** Emit an event when a staff user is created.
* **Delta as measured.** Δ `5/0`; 5 distinct added lines; verbatim match 2/5.
* **Content.** `import { captureEvent } from '../../analytics';` (line 6) and
  `captureEvent('staff_user_created', {…})` (line 144).
* **Historical commit context.** Last historical commit on the path `2d23fb8` (2026-08-06) "CarbonTally RC2
  Final database baseline"; `DIFF` vs `93d5cddd`.
* **Canonical equivalent and call sites.** None for analytics. The privileged operation the event observed —
  creating users / assigning roles — is server-authorised in canonical (AGENTS.md §14); the event was
  observational only and never part of the authorisation path.
* **Tests / DB dependency / reachability.** No test asserts the event; no DB change; reachable from the admin
  users screen.
* **Evidence.** Cluster A items 1–4 (`'staff_user_created'` → 0 hits in canonical source).
* **Loss risk / next action.** `LOW` / none required.

### 5.2 Cluster B — report-lifecycle visibility (P8-S6) and its frontend/test surfaces

Canonical introduced the report lifecycle as commit `eb6a0c2` (`feat(p8-s6): publish report-lifecycle
visibility (server-authoritative allowed_actions + panel)`), which is the newest canonical commit on
`backend/api/v3_reports.py`, `backend/tests/integration/test_report_versions.py`,
`backend/tests/integration/test_reports.py`, `backend/tests/unit/api/test_v3_report_lifecycle.py` and
`frontend/src/v3/reports/ReportDetailPage.jsx`. Five of the historical files in this cluster
(HIST-14, HIST-23, HIST-24, HIST-25, HIST-28) are `SAME` as canonical ancestor `93d5cddd` **and** `SAME`
as the canonical working tree: they therefore carry **already-committed canonical content**, and the delta
this reconciliation measures is only their movement relative to the older historical baseline `20b7a928`.
For these files the reconciliation question is trivially closed — nothing in them is un-adopted work — but
they are retained in the population and reported individually because they were part of the historical
working-tree change set and must not be omitted from the count.

#### HIST-13 — `backend/api/v3_operations.py`

* **Purpose of the delta.** Stamp manual (human) extraction writes with the method `"manual"` so downstream
  materialisation records the correct extraction method.
* **Delta as measured.** Δ `3/2`; 1 distinct added / 1 distinct removed line; verbatim match 1/1 in both
  canonical worktree and blob. Hunks land on `entity_extraction_save` (L1108) and `extract_item` (L1684),
  with an addition at `ops_work_complete` (L2815→2816).
* **Content.** the fourth positional argument of `repos.manual_extraction.save_extracted_data(...)` becomes
  `"manual"` at both call sites.
* **Historical commit context.** Last historical commit on the path `45a329b` (2026-09-15) "feat(phase8): wire
  B2 evidence line items and B1 disclosure routes"; `DIFF` vs `93d5cddd`.
* **Canonical equivalent and call sites.** Present and identical. Canonical
  `backend/api/v3_operations.py` L1163–1165 and L1740–1742 both read
  `save_extracted_data(item_id, payload.extracted_data, context.profile.user_id, "manual")`. Sibling
  canonical code consumes the stamp: `backend/data/manual_extraction.py` forwards `extraction_method` into
  `EvidenceLineItemsRepository.materialise_for_item(...)`.
* **Tests.** The B2 runtime path is covered canonically by
  `backend/tests/integration/test_evidence_line_items_b2_runtime.py` (integration; destructive-setup rules
  apply). No test asserts the literal string `"manual"` at the API layer.
* **Database / migration dependency.** No schema change; the argument feeds an existing column via the B2
  evidence-line materialisation (see §5.3, HIST-16).
* **Reachability.** Reached from the internal-staff manual extraction save endpoint and the PE/entity
  extraction save endpoint — i.e. from real workspace actions, not dead code.
* **Evidence of incorporation.** Verbatim line identity (1/1) **and** the receiving symbol
  (`save_extracted_data(..., extraction_method=...)`) named in §5.3 HIST-16, including canonical line
  numbers. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-14 — `backend/api/v3_reports.py`

* **Purpose of the delta.** Expose report-lifecycle state (`allowed_actions`, status transitions) through the
  list/version endpoints so the UI can render server-authoritative actions.
* **Delta as measured.** Δ `15/2`; 11 distinct added / 2 removed lines; verbatim match **11/11** in both the
  canonical worktree and the canonical `HEAD` blob; probes: `SAME` vs `93d5cddd`, `SAME` vs canonical
  worktree.
* **Content.** `list_report_versions` gains the lifecycle block (hunks at L398→398+7, L409, L412→412+7).
* **Historical commit context.** Last historical commit on the path `19e4f01` (2026-09-12) "feat: implement
  Phase 8 report lifecycle foundation"; the historical working tree is *ahead* of that commit and *equal* to
  canonical `93d5cddd`.
* **Canonical equivalent and call sites.** Identical content, and continued development on top of it
  (canonical lineage `n=4`, newest `eb6a0c2`). Consumed by `frontend/src/v3/api.js` and the lifecycle panel
  (§5.4, HIST-27/HIST-28).
* **Tests.** `backend/tests/unit/api/test_v3_report_lifecycle.py` (unit) and
  `backend/tests/integration/test_report_versions.py` (integration, destructive-setup rules apply) both exist
  in canonical.
* **Database / migration dependency.** Reads report-version lifecycle columns; no new migration is introduced
  by this delta.
* **Reachability.** Live authenticated API surface for report version listings.
* **Evidence of incorporation.** Byte-equality with canonical ancestor content plus 11/11 verbatim lines;
  canonical worktree equality proves the change is in the canonical working tree and not merely in history.
  `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

### 5.3 Cluster C — backend provenance, calculation dimensions and evidence lines

These files carry the P16/P17/B2/P12 backend substance: emissions-snapshot provenance, evidence-line
materialisation, the automatic pipeline version stamp, calculation dimensions/attribution threading, the B2
ordinal→line-id lookup, and the P1 extraction-fidelity hook. HIST-15 … HIST-19 and HIST-21 are `SAME` against
`93d5cddd`, i.e. the historical working tree already holds committed canonical content; HIST-20 is `DIFF`
because canonical has since refactored the same hook into a reusable helper. In every row the receiving
canonical symbols were located by name and line number, and canonical test coverage for the same behaviour
exists (file names cited per entry; **no test was executed for this report**).

#### HIST-15 — `backend/data/emissions_logs.py`

* **Purpose of the delta.** Thread `source_line_item_id` through the emissions/snapshot persistence layer so a
  calculated emission is traceable to the materialised evidence line that produced it.
* **Delta as measured.** Δ `6/3`; 6 distinct added / 2 removed lines; verbatim match 3/3 against both the
  canonical worktree and the canonical blob; `SAME` vs `93d5cddd`.
* **Content.** `_SNAPSHOT_COLUMNS` gains the line-id column (L57); the repository gains a lookup by
  `source_line_item_id` and organisation (L464–467), an added statement at L494→497, and the snapshot join
  exposes `cs.source_line_item_id` in the L520+ region.
* **Historical commit context.** Last historical commit on the path `daad396` (2026-09-11) "release: establish
  CarbonTally production release 1"; the working tree is at/after `93d5cddd`.
* **Canonical equivalent and call sites.** Present and **wider**: canonical L102 lists `source_line_item_id`
  in the column set, L570/L575 perform the line-item lookup, L820 and L856 write it in the snapshot path, and
  L997 exposes `cs.source_line_item_id` in the join. Canonical lineage `n=15`, newest `0f248ad`
  (`feat(p17-10): persist category methodology, purchase channel and widened data-quality vocabulary`).
* **Tests.** `backend/tests/integration/test_emissions_logs.py` exists in canonical (integration;
  destructive-setup rules apply).
* **Database / migration dependency.** Persists a column on the snapshot/emissions structures established by
  the B2 migration work; `backend/tests/unit/data/test_b2_migration.py` covers that migration revision.
* **Reachability.** On the canonical calculation write path (calculation → snapshot → emissions), i.e. live
  business data, not dead code.
* **Evidence of incorporation.** 3/3 verbatim plus six named canonical locations, i.e. canonical implements the
  same provenance chain *more* completely (`ADVANCED`). `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-16 — `backend/data/manual_extraction.py`

* **Purpose of the delta.** The B2 materialisation path: add an **additive, defaulted** `extraction_method`
  keyword and materialise evidence lines from saved extraction data, so manual/staff extraction also produces
  traceable evidence lines.
* **Delta as measured.** Δ `63/1`; 43 distinct added / 1 removed line; verbatim match **41/41** in both the
  canonical worktree and blob; `SAME` vs `93d5cddd`. Hunks: imports at L11/L12/L18, repository body at
  L420→426, L438→445, L441→457, L446→493, L448→495, L460→514.
* **Content.** `EvidenceLineItemsRepository` import, `MATERIALISATION_FORWARD` import, the `extraction_method`
  keyword (documented as additive with a default per B2 §12.1), `_materialise_evidence_lines(...)`, and its
  call from `save_extracted_data(...)`.
* **Historical commit context.** Last historical commit on the path `daad396` (2026-09-11); the working tree
  matches canonical ancestor `93d5cddd`.
* **Canonical equivalent and call sites.** Present with matching semantics: canonical L14
  `from data.evidence_line_items import EvidenceLineItemsRepository`, L15
  `from domain.line_items import MATERIALISATION_FORWARD`, L450/L517 `extraction_method: Optional[str] = None`,
  L472/L541 the materialisation calls, L481 `async def _materialise_evidence_lines`, L500
  `EvidenceLineItemsRepository(self._pool).materialise_for_item(...)`, L503
  `materialisation_kind=MATERIALISATION_FORWARD`. Its callers are the API sites of HIST-13.
* **Tests.** `backend/tests/integration/test_evidence_line_items_b2_runtime.py` (integration) and
  `backend/tests/unit/data/test_b2_migration.py` (unit, migration revision) exist in canonical.
* **Database / migration dependency.** Depends on the B2 evidence-line-items schema; the keyword is additive
  with a default, so the change is backwards compatible by construction (the canonical docstring says so).
* **Reachability.** Reached from the manual/PE extraction save endpoints (HIST-13) — a live workspace path.
* **Evidence of incorporation.** 41/41 verbatim lines **and** all six receiving symbols present at named
  canonical lines. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-17 — `backend/domain/automatic_processing.py`

* **Purpose of the delta.** Advance the automatic-pipeline version stamp recorded with processing jobs.
* **Delta as measured.** Δ `1/1`; 1 distinct added / 1 removed line; verbatim match 0/1 — **expected**, because
  the canonical value has advanced again; `SAME` vs `93d5cddd`. Hunk at L45 (context line
  `from domain.workflow import WorkflowDefinition`).
* **Content.** `PIPELINE_VERSION` moves to the historical release value (`v3-auto-1.1`); the historical working
  tree equals canonical ancestor `93d5cddd`.
* **Historical commit context.** Last historical commit on the path `daad396` (2026-09-11); working tree matches
  `93d5cddd`.
* **Canonical equivalent and call sites.** Same file, same symbol, same location: canonical L45 reads
  `PIPELINE_VERSION = "v3-auto-1.2"  # P12-IMPL-01: deterministic PDF invoice-header + item-table shaping`.
  Canonical lineage `n=4`, newest `ad07cd4` (`feat(p12-impl-01): PDF extraction foundation`).
* **Tests.** `backend/tests/unit/services/test_automatic_processing.py` and
  `backend/tests/unit/services/test_p12_impl_01_invoice_extraction.py` exist in canonical.
* **Database / migration dependency.** The constant is a stamp written into job/audit records, so the value
  affects provenance labels, not schema.
* **Reachability.** Read by the durable automatic-processing job path.
* **Evidence of incorporation.** Identical symbol at the identical line with a **later** value carrying an
  explicit rationale comment — adopted, then advanced. `INCORPORATED` (`ADVANCED`), confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. (Because the metric is a literal value the verbatim ratio
  is 0/1 here; classification rests on symbol-level evidence, not on the ratio — §3.)

#### HIST-18 — `backend/domain/calculation.py`

* **Purpose of the delta.** Extend `CalculationSnapshot` so a result carries its accounting dimensions and
  attribution, and persist them through the canonical write.
* **Delta as measured.** Δ `21/4`; 20 distinct added / 3 removed lines; verbatim match **20/20** in both the
  canonical worktree and blob; `SAME` vs `93d5cddd`. Hunks: L60→61+6, L63→69+12 (class `CalculationSnapshot`),
  L78→93+3.
* **Content.** new snapshot fields with their defaults/typed declarations.
* **Historical commit context.** Last historical commit on the path `bb6cd7d` (2026-08-30) "P1 fix:
  customer-factor calculations blocked report generation forever (O1)"; working tree at/after `93d5cddd`.
* **Canonical equivalent and call sites.** Present and continued: canonical lineage `n=6`, newest `5713073`
  (`feat(p17): thread accounting dimensions and attribution through the canonical write`).
* **Tests.** `backend/tests/integration/test_calculation.py` plus the P17 unit tests
  (`backend/tests/unit/services/test_p17_05_scope2_calculation.py`,
  `test_p17_07_scope3_framework.py`, `test_p17_10_scope3_methodology.py`) exist in canonical.
* **Database / migration dependency.** The new snapshot fields correspond to persisted snapshot columns; the
  P17 migration tests (`backend/tests/unit/data/test_p17_migrations.py`) exist in canonical.
* **Reachability.** On the authoritative server-side calculation write path (AGENTS.md §25) — live business
  data.
* **Evidence of incorporation.** 20/20 verbatim lines plus the successor commit that continues the same
  `CalculationSnapshot` write. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-19 — `backend/engines/calculation.py`

* **Purpose of the delta.** Extend `CalculationRequest`/`CalculationEngine` so the engine accepts and forwards
  the same dimensions (the request-side half of HIST-18).
* **Delta as measured.** Δ `8/0`; 8 distinct added lines; verbatim match **8/8** in both canonical worktree and
  blob; `SAME` vs `93d5cddd`. Hunks: L167→168+7 (class `CalculationRequest`), L500→508+1
  (class `CalculationEngine`).
* **Content.** additional request fields and the engine-side assignment that carries them into the result.
* **Historical commit context.** Last historical commit on the path `daad396` (2026-09-11); working tree
  matches `93d5cddd`.
* **Canonical equivalent and call sites.** Present; canonical lineage `n=11`, newest `0f248ad` (`p17-10`).
  The request object is constructed in `backend/services/automatic_processing.py` (§5.3 HIST-21) and by the
  `backend/domain/calculation.py` callers.
* **Tests.** `backend/tests/integration/test_calculation.py`,
  `backend/tests/unit/services/test_p17_05_scope2_calculation.py`.
* **Database / migration dependency.** Indirect, through the snapshot persistence of HIST-15 / HIST-18.
* **Reachability.** Every authoritative calculation request passes through this class — the highest-traffic
  business path in the platform.
* **Evidence of incorporation.** 8/8 verbatim lines in both canonical worktree and blob. `INCORPORATED`,
  confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-20 — `backend/services/automatic_extraction.py`

* **Purpose of the delta.** Wire the **P1 extraction-fidelity** hook into PDF extraction: classify how
  trustworthy the deterministic text layer is, record coverage, and build trustworthy line items when the
  document is a multi-line suspect.
* **Delta as measured.** Δ `51/0`; 44 distinct added lines; verbatim match **33/44**; `DIFF` vs `93d5cddd` and
  `DIFF` vs the canonical worktree — canonical has since restructured the hook. Hunks inside
  `def _extract_pdf(content: bytes) -> dict`: L240→241+38, L241→280+10, L248→297+3.
* **Content.** import of the fidelity module, `classify(...)`-driven judgement, a coverage dict, and
  `build_line_items(...)` output used as the extracted structure.
* **Historical commit context.** Last historical commit on the path `daad396` (2026-09-11); the working-tree
  change was *production-side P1 wiring*, not yet committed.
* **Canonical equivalent and call sites.** Present **and generalised**: canonical defines a reusable
  `_apply_p1_fidelity(...)` (def L378) which executes `from services import extraction_fidelity as p1` (L403)
  and uses `p1.shape_mode(organization_id=...)` (tenant-aware controlled rollout), `p1.rollout_status(...)`,
  `p1.classify(...)`, `judgement.as_coverage()`, `p1.ai_fanout_plan(...)` and `p1.build_line_items(...)`.
  Its docstring explicitly records the limitation of the historical wiring: *"previously only `_extract_pdf`
  was wired, so a scanned multi-line IMAGE (or a single-page image invoice) was still silently collapsed."*
  The module itself ships in canonical as `backend/services/extraction_fidelity.py`.
* **Tests.** Canonical carries focused P1 coverage: `backend/tests/unit/services/test_extraction_fidelity.py`,
  `test_p1_image_path.py`, `test_p1_controlled_rollout.py`, `test_p1_row_candidates_multiline.py`,
  `test_pod1_bounded_ai_fanout.py`, plus `test_multiline_provenance_mapping.py`. `test_p1_image_path.py` is
  precisely the path the canonical docstring says the historical change did **not** cover.
* **Database / migration dependency.** None introduced by the delta; judgement/coverage data travels in job
  metadata and audit evidence.
* **Reachability.** On the automatic document-processing pipeline (AGENTS.md §18–§20), i.e. live processing.
* **Evidence of incorporation (and advancement).** All receiving symbols are present and named; the canonical
  version is tenant-aware (`shape_mode` / allowlist rollout), applies to more document paths, and has
  dedicated tests for the path the historical wiring missed. `INCORPORATED` + `ADVANCED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-21 — `backend/services/automatic_processing.py`

* **Purpose of the delta.** B2 §13.2: resolve a line's materialised evidence-line id at calculation time (a
  **lookup, never an insert**) and thread it into the `CalculationRequest`; best-effort, so B2 can never break
  a calculation.
* **Delta as measured.** Δ `22/2`; 21 distinct added / 2 removed lines; verbatim match **20/20** in both
  canonical worktree and blob; `DIFF` vs `93d5cddd` (canonical has since added further gates). Hunks: L454,
  L871→872+2, L873→875, L1067→1070+17, L1135→1155+1.
* **Content.** the `source_line_item_id: Optional[str] = None` resolution block (whose comment states that an
  unresolvable/absent line leaves the snapshot link NULL — "the honest value"), the deliberate swallowing of
  resolver failures so that calculation proceeds, and `source_line_item_id=source_line_item_id` added to
  `CalculationRequest`.
* **Historical commit context.** Last historical commit on the path `daad396` (2026-09-11).
* **Canonical equivalent and call sites.** Present: canonical L1822–1841 reproduce the B2 §13.2 comment and
  the `self._repos.evidence_line_items.get_by_ordinals(job.source_item_id, [idx + 1])` lookup with its
  best-effort guard, and L1928 passes `source_line_item_id=source_line_item_id` into `CalculationRequest`.
  The resolver itself is `backend/data/evidence_line_items.py` L307 `get_by_ordinals` / L333
  `materialise_for_item`. Canonical lineage `n=18`, newest `999e4fb` (`feat(p8): shared Source Evidence Viewer
  + Insight evidence handoff`); the same file has since gained, among others, the WS4 Gate 5 attempted-model
  attribution (canonical L1066–1090).
* **Tests.** `backend/tests/integration/test_evidence_line_items_b2_runtime.py`,
  `backend/tests/unit/data/test_b2_migration.py`, `backend/tests/unit/services/test_automatic_processing.py`.
* **Database / migration dependency.** Depends on the B2 evidence-line-items schema; by design a missing
  schema or row degrades to a NULL link rather than a failure (the B2 principle that provenance must never
  block calculation).
* **Reachability.** The durable automatic-processing calculation path — every automatically processed line
  passes through it.
* **Evidence of incorporation.** 20/20 verbatim lines **and** the named resolver in a second module, plus a
  later canonical commit extending the same file. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

### 5.4 Cluster D — harness safety invariant (HIST-01, HIST-22)

#### HIST-22 — `backend/tests/integration/conftest.py`

* **Purpose of the delta.** Encode the F-046-1 operational invariant in code: refuse any integration target
  whose database name matches a protected/persistent marker, **before** the destructive `TRUNCATE … RESTART
  IDENTITY CASCADE` setup runs.
* **Delta as measured.** Δ `20/0`; 18 distinct added lines; verbatim match **17/17** in both the canonical
  worktree and the canonical `HEAD` blob; `SAME` vs `93d5cddd`; hunks at L45→46+7 and L107→115+13.
* **Content.** extension of the forbidden-name tuple and the refusal branch inside the `pool` fixture.
* **Historical commit context.** Last historical commit on the path `9458067` (2026-08-25) "feat(v3): commit
  D20-D37 commercial platform release".
* **Canonical equivalent and call sites.** Present and authoritative in canonical:
  `FORBIDDEN_MAIN_DB_NAMES = ("postgres", "supabase_db_carbon_ledger")` (L44),
  `PROTECTED_PERSISTENT_MARKERS = ("qa", "demo", "investor", "prod", "live")` (L51), the refusal at L109/L115
  and the explicit `F-046-1` message at L117–124. Canonical's newest commit on the path is `0d21e46`
  (`fix(p8-f046-1): enforce the protected-persistent-target refusal in the integration harness`).
* **Tests.** This *is* test infrastructure; its enforcing behaviour is exercised implicitly by every
  integration run against a permitted target.
* **Database / migration dependency.** None (no schema change), but the guard's whole purpose is to protect
  databases — including the investor-demo database — from destructive setup (AGENTS.md §55, §55.1).
* **Reachability.** Executed whenever the integration `pool` fixture is created.
* **Evidence of incorporation.** 17/17 verbatim lines **and** the header comment citing *"PO operational
  control F-046-1 (2026-09-14)"* **and** a dedicated canonical commit implementing it. `INCORPORATED`,
  confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. The related documentation gap is tracked once, on
  HIST-01.

#### HIST-01 — `AGENTS.md`

* **Purpose of the delta.** Add the F-046-1 policy paragraph (§55.1, *TEST-HARNESS TARGET SAFETY*) to the
  agent operating constitution: destructive-setup harnesses must never be pointed at persistent environments;
  integration suites must target a disposable `ct_*` clone or `carbontally_test`; target identity must be
  verified before each suite; the invariant is enforced in code and must be restated in all subsequent
  implementation and verification reports.
* **Delta as measured.** Δ `29/0`; 21 distinct added lines (whitespace-stripped set); verbatim match **1/21**
  against both the canonical worktree and the canonical `HEAD` blob; `DIFF` vs `93d5cddd`. Single hunk
  `@@ -1544,0 +1545,29 @@` inserted after the "BLOCKED — SAFE MUTATION NOT AVAILABLE" passage.
* **Content.** the complete §55.1 section, including the explicit `TRUNCATE … RESTART IDENTITY CASCADE`
  warning, the `qa`/`demo`/`investor`/`prod`/`live` refusal list, the `F-046-1` error name, and the
  carry-forward requirement.
* **Historical commit context.** Last historical commit on the path `5a1e45e` (2026-09-11) "release: publish
  reconciled CarbonTally development state" (hist path lineage `n=1`); the addition is working-tree-only.
* **Canonical equivalent and call sites.** **Split outcome.** (a) The *invariant itself* is incorporated and
  enforced in canonical `backend/tests/integration/conftest.py` (HIST-22: `FORBIDDEN_MAIN_DB_NAMES`,
  `PROTECTED_PERSISTENT_MARKERS`, `F-046-1` refusal, dedicated commit `0d21e46`). (b) The *policy text* is
  **absent** from canonical `AGENTS.md`: `grep` for `55.1`, `F-046-1`, `PROTECTED_PERSISTENT` and `TRUNCATE`
  in the canonical `AGENTS.md` returns **zero** hits, and the canonical file has only one commit on the path
  (`5a1e45e`, canonical lineage `n=1`).
* **Tests.** No test asserts documentation content; the invariant's enforceable half is covered by HIST-22.
* **Database / migration dependency.** None for the text; the invariant protects databases (AGENTS.md §55).
* **Reachability.** The canonical `AGENTS.md` is the operating constitution read by every agent session, so the
  gap is reachable by every future session.
* **Evidence of classification.** Concrete code evidence for the invariant (item a) **plus** a measured absence
  of the text (item b). This is the only row in the population with a genuine partial outcome: `INCORPORATED`
  + `RESIDUAL` (documentation gap), confidence `HIGH` for both halves because both were measured directly.
* **Loss risk / next action.** `LOW` — no business, data or security capability is missing, since the guard is
  enforced in code; the risk is that a future agent session reading only `AGENTS.md` will not know the
  invariant exists. Next action: **PO/eng decision** — port §55.1 into the canonical `AGENTS.md` (documentation
  alignment, not a behaviour change). Note the canonical constitution's §55.1 text would need to be written
  against the canonical wording, not copied blindly, since the historical text references historical section
  numbers.

#### HIST-23 — `backend/tests/integration/test_report_versions.py`

* **Purpose of the delta.** Integration coverage for the report-version round-trip and the lifecycle
  assertions introduced by P8-S6.
* **Delta as measured.** Δ `5/1`; 5 distinct added / 1 removed line; verbatim match **5/5** in both the
  canonical worktree and blob; `SAME` vs `93d5cddd`; hunks `@@ -0,0 +1,4 @@` and L37→41.
* **Content.** an added header/import prologue (4 lines) and a changed assertion inside
  `test_create_and_roundtrip_version`.
* **Historical commit context.** Last historical commit on the path `c86b83c` (2026-09-12) "fix: harden Phase 8
  report version correctness".
* **Canonical equivalent and call sites.** Identical; canonical lineage `n=3`, newest `eb6a0c2` (P8-S6).
* **Tests / DB dependency / reachability.** This **is** a test file. It is an integration test: it requires a
  database, and the canonical harness performs destructive setup, so per AGENTS.md §55.1 / F-046-1 it may only
  be run against a disposable `ct_*` clone or `carbontally_test`. It depends on the report-version schema.
* **Evidence of incorporation.** 5/5 verbatim lines plus byte-equality with canonical content.
  `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. (No test was executed for this task.)

#### HIST-24 — `backend/tests/integration/test_reports.py`

* **Purpose of the delta.** Integration coverage for report lifecycle transitions and request attribution
  (`mark_generating`, `mark_failed` error persistence, `created_by`/name recording).
* **Delta as measured.** Δ `9/5`; 9 distinct added / 5 removed lines; verbatim match **9/9** in both canonical
  worktree and blob; `SAME` vs `93d5cddd`; hunks at `@@ -0,0 +1,4 @@`, L94, L98, L106, L122, L127.
* **Content.** added prologue plus adjustments to the four named lifecycle tests.
* **Historical commit context.** Last historical commit on the path `9458067` (2026-08-25) "feat(v3): commit
  D20-D37 commercial platform release".
* **Canonical equivalent and call sites.** Identical; canonical lineage `n=3`, newest `eb6a0c2` (P8-S6).
* **Tests / DB dependency / reachability.** Test file; requires a database; destructive-setup rules apply
  (disposable target only).
* **Evidence of incorporation.** 9/9 verbatim lines plus byte-equality. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. (No test was executed for this task.)

#### HIST-25 — `backend/tests/unit/api/test_v3_report_lifecycle.py`

* **Purpose of the delta.** Unit-level coverage for the server-authoritative report lifecycle
  (`allowed_actions` and its transition rules) added by P8-S6.
* **Delta as measured.** Δ `112/0`; 63 distinct added lines; verbatim match **62/63** in both canonical worktree
  and blob; `SAME` vs `93d5cddd`; single hunk `@@ -520,0 +521,112 @@` appended after
  `test_version_listing_exposes_status`.
* **Content.** a new +112-line test block; the single non-verbatim line is a whitespace/format variance (the
  file is otherwise byte-equal to canonical).
* **Historical commit context.** Last historical commit on the path `19e4f01` (2026-09-12) "feat: implement
  Phase 8 report lifecycle foundation".
* **Canonical equivalent and call sites.** Identical and current; canonical lineage `n=2`, newest `eb6a0c2`
  (P8-S6). Its frontend counterpart exists as `frontend/src/v3/__tests__/report-lifecycle-panel.test.jsx`
  (5,901 bytes) alongside `frontend/src/v3/reports/ReportLifecyclePanel.jsx` (7,656 bytes).
* **Tests / DB dependency / reachability.** Unit test at the API layer — it does not require the destructive
  integration fixture; it was still not executed for this read-only task.
* **Evidence of incorporation.** 62/63 verbatim lines (all but a whitespace variance) and the matching
  frontend counterpart. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. (No test was executed for this read-only task; the
  frontend counterpart was likewise not executed.)

### 5.5 Cluster E — frontend report-lifecycle surfaces (HIST-26 … HIST-29)

#### HIST-26 — `frontend/src/App.js`

* **Purpose of the delta.** None observable: the delta is the deletion of a single blank line inside a JSX
  comment block.
* **Delta as measured.** Δ **`0/1`**; distinct added `0`, distinct removed `0`; single hunk
  `@@ -2181 +2180,0 @@`; verbatim match n/a (there is no added line). `DIFF` vs `93d5cddd` for the whole file.
* **Content.** one removed blank line in the `/ops/operational-health` comment region.
* **Historical commit context.** Last historical commit on the path is `20b7a92` (2026-09-16) — the historical
  repository's own `HEAD` — "fix(frontend): retire legacy onboarding and use org member chat identity"; the
  whitespace edit is working-tree-only, on top of `HEAD`.
* **Canonical equivalent and call sites.** The subject matter of the surrounding comment is present and live in
  canonical: `frontend/src/App.js` L2231–2236 documents and routes `/ops/operational-health` as a `Navigate`
  to `/ops?tab=operational-health` inside the ops console (canonical lineage `n=29`, newest `fb3eba1`).
* **Tests / DB dependency / reachability.** No test, no DB dependency; the route is reachable in the ops
  console.
* **Evidence of classification.** The delta carries no added content at all, and the block it edits exists in
  canonical. `NOT_SUBSTANTIVE`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. This delta should **not** be carried into canonical: it
  is a whitespace edit with no semantic content.

#### HIST-27 — `frontend/src/v3/api.js`

* **Purpose of the delta.** Publish the report-lifecycle action map so the UI can present
  server-authoritative allowed actions, plus adjacent API helper work.
* **Delta as measured.** Δ `40/1`; 25 distinct added / 0 removed lines; verbatim match **24/24** in both
  canonical worktree and blob; `DIFF` vs `93d5cddd`. Hunks: L169→170+40 (immediately after `getReportTypes`)
  and one replacement at L509 (the `getOperationalIntelligence` line).
* **Content.** the lifecycle action-map block and related export wiring.
* **Historical commit context.** Last historical commit on the path `137765f` (2026-09-15) "feat(phase8x): X5
  operations console extension (operational health, read-only)".
* **Canonical equivalent and call sites.** Present and consumed: canonical L211 exports
  `REPORT_LIFECYCLE_ACTION_CALLS`; `frontend/src/v3/reports/ReportLifecyclePanel.jsx` imports it (L13) and uses
  it at L75/L80 when dispatching an action; `frontend/src/v3/__tests__/report-lifecycle-panel.test.jsx` imports
  it as `calls` (L16/L26) and mocks it. Canonical lineage `n=21`, newest `fb3eba1`.
* **Tests.** `frontend/src/v3/__tests__/report-lifecycle-panel.test.jsx` (canonical; not executed here).
* **Database / migration dependency.** None (a client-side map over server-provided `allowed_actions`).
* **Reachability.** Called from the report detail page after `ReportDetailPage.jsx` loads versions.
* **Evidence of incorporation.** 24/24 verbatim lines **and** three named consumers/importers in canonical.
  `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-28 — `frontend/src/v3/reports/ReportDetailPage.jsx`

* **Purpose of the delta.** Mount the report-lifecycle panel on the report detail page.
* **Delta as measured.** Δ `7/0`; 6 distinct added lines; verbatim match **5/5** in both canonical worktree and
  blob; `SAME` vs `93d5cddd`; hunks L16→17 (after the `EvidenceTrail` import) and L229→231+6.
* **Content.** the `ReportLifecyclePanel` import and its JSX mount with `reportId`, `versions` and an
  `onChanged={load}` refresh callback.
* **Historical commit context.** Last historical commit on the path `077c866` (2026-08-27) "feat: finalize v3 ux
  and promote public website".
* **Canonical equivalent and call sites.** Present: canonical L17
  `import ReportLifecyclePanel from './ReportLifecyclePanel';` and L234
  `<ReportLifecyclePanel reportId={id} versions={versions} onChanged={load} />`. Canonical lineage `n=3`,
  newest `eb6a0c2` (P8-S6).
* **Tests.** `frontend/src/v3/__tests__/report-lifecycle-panel.test.jsx` covers the panel itself; no page-level
  mount assertion was found in this read-only pass (recorded as an unknown, not as a gap).
* **Database / migration dependency.** None (reads through `frontend/src/v3/api.js`).
* **Reachability.** The report detail route — a live authenticated customer/consultant surface.
* **Evidence of incorporation.** 5/5 verbatim lines plus byte-equality with canonical content **and** the
  import/mount at named canonical lines. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required.

#### HIST-29 — `frontend/src/v3/reports/reports.css`

* **Purpose of the delta.** Styling for the report detail / lifecycle surfaces (report metadata layout).
* **Delta as measured.** Δ `65/0`; 49 distinct added lines; verbatim match **49/49** in both canonical worktree
  and blob; `DIFF` vs `93d5cddd`; single hunk `@@ -0,0 +1,65 @@` (a block added to the file).
* **Content.** the report-detail CSS block (metadata/layout rules).
* **Historical commit context.** Last historical commit on the path `077c866` (2026-08-27) "feat: finalize v3 ux
  and promote public website".
* **Canonical equivalent and call sites.** Present, and subsequently revised: canonical lineage `n=4`, newest
  `6cd36fc` (`fix(p8): remediate F-07 report metadata layout (CT-STEP2-FINAL-STABILIZATION-012)`), i.e. the same
  block was later tuned by the F-07 remediation. 49/49 verbatim confirms the historical content is present.
* **Tests / DB dependency / reachability.** No test asserts CSS; no DB dependency; reachable on the report detail
  route.
* **Evidence of incorporation.** 49/49 verbatim lines in both the canonical worktree and blob, plus a later
  canonical commit working on the same block. `INCORPORATED`, confidence `HIGH`.
* **Loss risk / next action.** `NONE` / none required. Because the block was later remediated under F-07, the
  canonical layout is the newer authority and the historical block must not be re-applied over it.

### 5.6 Cluster F — schema artefact, generated artefact, manifests, environment config (HIST-02, HIST-30 … HIST-32)

#### HIST-02 — `CarbonTally_DB_Schema_V3M2.sql`

* **Purpose of the delta.** Bring the monolithic schema dump in line with the database it was dumped from, so
  the dump contains the D21 white-label column and the D22 processing-entity assignment objects.
* **Delta as measured.** Δ `16/0` (blank-line-inclusive) / 7 distinct added lines; verbatim match **1/7** in both
  the canonical worktree and blob; `DIFF` vs `93d5cddd`; hunks at L719→720+2, L1595→1598, L1635→1639+3,
  L4463→4470+4, L5009→5020+6.
* **Content (all added lines, in order).** `"white_label_enabled" boolean DEFAULT false,` in
  `public.consultant_profiles`; `"entity_id" "uuid",` in `public.manual_extraction_batches`;
  `COMMENT ON COLUMN "public"."manual_extraction_batches"."entity_id" IS 'Processing Entity allocated this
  batch (NULL = CarbonTally internal; ADR-V3-001 Q5)…'`; `ALTER TABLE ONLY … ADD CONSTRAINT
  "manual_extraction_batches_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES
  "public"."processing_entities"("id") ON DELETE RESTRICT;`;
  `CREATE POLICY "manual_extraction_batches_entity_select" ON … FOR SELECT TO "authenticated" USING
  (("entity_id" IS NOT NULL) AND public.is_entity_member(entity_id));`;
  `CREATE POLICY "manual_extraction_items_entity_select" ON … USING (EXISTS (SELECT 1 FROM
  "public"."manual_extraction_batches" …))`; plus one blank line.
* **Historical commit context.** Last historical commit on the path `cfabe26` (2026-08-15) "checkpoint:
  CarbonTally V3 baseline" (this commit is also the canonical path's only commit); the delta is
  working-tree-only.
* **Canonical equivalent and call sites.** The same objects are delivered canonically as **versioned
  migrations**: `supabase/migrations/20260821010000_d21_white_label_branding.sql` (L21
  `ADD COLUMN IF NOT EXISTS white_label_enabled boolean NOT NULL DEFAULT false`, with the comment at L23) and
  `supabase/migrations/20260821020000_d22_processing_work_assignment.sql` (L25 `ADD COLUMN IF NOT EXISTS
  entity_id UUID`, L34–35 the `manual_extraction_batches_entity_id_fkey` FK → `public.processing_entities`
  `ON DELETE RESTRICT`, L40–41 `idx_manual_extraction_batches_entity_id`, L43–45 the column comment, L88–95
  `manual_extraction_batches_entity_select`, L102–112 `manual_extraction_items_entity_select`). Canonical is a
  **superset** of the dump's delta: the index on `entity_id` exists in D22 and not in the dump.
* **Tests.** Canonical migration-revision/unit tests exist in the same family
  (`backend/tests/unit/data/test_b2_migration.py`, `test_d17_provider_ownership_migration_revision.py`,
  `test_p17_migrations.py`); no D21/D22-specific test file was identified in this read-only pass, which is
  recorded as an unknown rather than claimed as coverage.
* **Database / migration dependency.** This row *is* the schema layer. Per AGENTS.md §66, migrations are the
  canonical delivery mechanism and ad-hoc production-only modifications are prohibited, so the dump must not be
  treated as a source of truth.
* **Reachability.** The objects are reachable through the tables/policies they define; the dump file itself is a
  historical artefact of a database state.
* **Evidence of classification.** The historical textual delta and the canonical migration definitions match
  object-for-object by name and definition, with canonical strictly wider. Classification `SUPERSEDED`
  (delivery mechanism superseded by migrations), confidence `HIGH` at the definition level and explicitly
  `UNVERIFIED` at the live-database level.
* **Loss risk / next action.** `LOW`. No action required for the file. Two separate follow-ups are recorded, not
  asserted: (a) live-DB verification that D21/D22 are applied (belongs to DB verification, not to this file
  reconciliation); (b) if the monolithic dump is still used as an onboarding/reference artefact, it is stale
  relative to canonical migrations and should be regenerated or explicitly deprecated — **PO/eng decision**.

#### HIST-30 — `output/reports/import_summary.md`

* **Purpose of the delta.** Replace the committed RC2-era DEFRA import summary with a later, richer run record
  produced by the factor-import tooling.
* **Delta as measured.** Δ `47/27`; 38 distinct added / 27 removed lines; verbatim match **3/38** in both the
  canonical worktree and blob; `DIFF` vs `93d5cddd`; the whole file is rewritten (hunks at L1, L3, L5, L7, L9,
  L19, L23).
* **Content.** the historical working-tree file is a **newer generated artefact**: `Generated: 2026-08-15T00:13:20`,
  execution time 6m 50s, workbook `ghg-conversion-factors-2025-flat-format.xlsx`, workbook
  `SHA-256 8bfdb45b…6de94`, reporting year 2025, factor set `DEFRA-2025`, sheets processed 2, rows scanned
  8,742, rows parsed 8,740, rows with a DEFRA ID 8,740, rows with a factor value 7,029. The committed version it
  replaces was `Generated: 2026-08-06T05:12:27` (imported 7,029 of 8,740).
* **Historical commit context.** Last historical commit on the path `2d23fb8` (2026-08-06) "CarbonTally RC2 Final
  database baseline"; the newer summary is working-tree-only and was never committed in the historical
  repository either.
* **Canonical equivalent and call sites.** **No canonical equivalent and no generator.** Canonical
  `output/reports/import_summary.md` is the older `2d23fb8` blob, and a search for `import_summary` across
  canonical `backend/`, `tools/` and `scripts/` returns **0 hits** — so the tool that produced the historical
  artefact is not in the canonical repository. The *subject matter* is canonical: the `DEFRA-2025` factor-set
  notion is referenced by multiple canonical integration tests (`test_emission_factors.py`,
  `test_factor_matching.py`, `test_calculation.py`, `test_emissions_logs.py`, `test_search_index.py`,
  `test_workflow.py`, `test_evidence_line_items_b2_runtime.py`, …).
* **Tests / DB dependency / reachability.** No test reads the artefact. Its content describes data that lives in
  the database (the imported factor rows), so verifying it is a **database** verification, outside the scope of
  this read-only file reconciliation. Reachability: none — no code path reads or regenerates it.
* **Evidence of classification.** The delta is a generated output with no generator present in canonical and no
  code path consuming it; there is neither a concrete successor implementation nor obviating-architecture
  evidence that would license `SUPERSEDED`. Hence `NEEDS_REVIEW`, confidence `MEDIUM–HIGH` for the measurement
  itself.
* **Loss risk / next action.** `LOW` (the platform loses a point-in-time evidence artefact, not a capability).
  Next action — **PO/eng decision**: (a) accept it as a one-off evidence artefact and record it as such; or
  (b) reconstruct/restore the importer tool that produced it (also the reproducible way to re-derive factor
  data); and separately (c) confirm by database inspection that the 7,029 `DEFRA-2025` factor rows exist in the
  target environment. None of (a)–(c) is asserted as required by this report.

#### HIST-31 — `requirements.txt`

* **Purpose of the delta.** Relax the root Python dependency pins from exact versions to lower bounds.
* **Delta as measured.** Δ `12/12`; 12 distinct added / 12 removed lines; verbatim match **0/12** (the change is
  an operator change per line, so no line can match); `DIFF` vs `93d5cddd`.
* **Content.** all twelve entries flip `==` → `>=`: `fastapi>=0.109.0`, `uvicorn>=0.27.0`, `pandas>=2.1.4`,
  `numpy>=1.26.4`, `python-multipart>=0.0.6`, `pdfplumber>=0.10.3`, `pytesseract>=0.3.10`,
  `pdf2image>=1.16.3`, `Pillow>=10.2.0`, `python-magic>=0.4.27`, `resend>=0.5.1`, `fpdf2>=2.7.9`. (The committed
  version had no trailing newline; the working-tree version adds one.)
* **Historical commit context.** Last historical commit on the path `a16ba01` (2026-07-21) "Add admin dashboard,
  update structure, remove sensitive files"; historical path lineage `n=4` (`a16ba01`, `8b59378`, `6344456`,
  `35dbcd6`).
* **Canonical equivalent and call sites.** Canonical carries **two** manifests covering a superset of the same
  capability set: root `requirements.txt` (12 entries, **pinned** with `==`) and `backend/requirements.txt`
  (the same twelve names as `>=` **plus** `reportlab`, `python-dotenv`, `pypdf2`, `supabase`, `PyJWT`,
  `asyncpg`, `openpyxl`, and an OCR-fallback comment). The historical ranged style therefore already exists
  canonically at the backend location, with more packages.
* **Tests / DB dependency / reachability.** Deployment/install manifests: consumed by the backend build and by
  any root-level install. No test asserts manifest content.
* **Evidence of classification.** Name-by-name capability coverage by canonical manifests, with canonical
  strictly wider; the only thing not adopted is the ranged style **at the root**. Classification `SUPERSEDED`
  (equivalent canonical manifests), confidence `MEDIUM–HIGH` — `MEDIUM` because line-level identity is
  impossible here and the judgement rests on package-name/version coverage rather than a verbatim match.
* **Loss risk / next action.** `LOW`. No action required. Recorded as a **dependency-posture observation**, not a
  policy assertion: canonical keeps the root manifest pinned while the backend manifest uses lower bounds; if the
  intent is for the root manifest to be ranged as well, that is a deliberate configuration change (**eng
  decision**), not a lost capability.

#### HIST-32 — `supabase/config.toml`

* **Purpose of the delta.** Remap the local Supabase CLI port family away from the standard 5432x range, and
  disable migrations for local `db push`/`reset`.
* **Delta as measured.** Δ `7/7`; 7 distinct added / 7 removed lines; verbatim match **1/7** in both the
  canonical worktree and blob; `DIFF` vs `93d5cddd`; seven single-line replacements at L9, L24, L26, L41, L55,
  L123, L135.
* **Content.** `api` port `54325 → 54425`; `db` port `54326 → 54426`; `db.shadow_port` `54320 → 54420`;
  `db.pooler` port `54329 → 54429`; `studio` port `54323 → 54423`; `local_smtp` port `54324 → 54424`; and
  `[db.migrations] enabled` `true → false`.
* **Historical commit context.** Last historical commit on the path `2d23fb8` (2026-08-06) "CarbonTally RC2 Final
  database baseline"; the remap is working-tree-only.
* **Canonical equivalent and call sites.** **The remap is the environment canonical depends on, and it is
  encoded in canonical code rather than in canonical `config.toml`.**
  `backend/tests/integration/conftest.py` L40 defaults the DSN to
  `postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test` (the remapped `db` port) and L58 sets
  `SUPABASE_URL=http://127.0.0.1:54425` (the remapped `api` port); disposable `ct_*` / `carbontally_test` DSNs on
  port `54426` appear throughout the integration and verification scripts
  (`verify_activity_clarifications_rls.py`, `verify_p17_08_scope3_persistence_schema.py`,
  `test_i4_live_migration_and_persistence.py`, `test_p17l_capability_truth_surface_runtime.py`,
  `test_p17m2_governed_catalogue_selection_runtime.py`). Meanwhile canonical `supabase/config.toml` is unchanged
  since `2d23fb8` and still declares the standard 5432x ports — so the historical remap is *functionally
  incorporated in the harness* but *not present in the canonical CLI configuration*.
* **Tests / DB dependency / reachability.** The port family determines which local database the harness reaches;
  `[db.migrations] enabled = false` affects local `supabase db reset/push` behaviour only. Nothing in canonical
  depends on the historical file being present.
* **Evidence of classification.** Port-level incorporation is proven by canonical code paths naming the remapped
  ports (two defaults plus five further scripts). The `db.migrations` flag has **no** canonical counterpart, so
  that sub-element is a genuine residual. Classification `INCORPORATED` + `RESIDUAL`, confidence `HIGH` for the
  ports and `MEDIUM` for the flag.
* **Loss risk / next action.** `LOW`. Next action — **PO/eng decision** (environment configuration): align
  canonical `supabase/config.toml` with the 5442x family its own harness expects, and decide the
  `[db.migrations] enabled` value explicitly — setting it to `false` makes local `db push`/`reset` skip
  migrations, which interacts with canonical migration discipline (AGENTS.md §66) and should therefore be an
  intentional choice rather than an inherited default. This row contains no business logic and no security
  boundary.

---

## 6. Summary, open items and verdict

**Finding an entry.** §5 is grouped by **cluster** (§5.1 analytics retirement, §5.2 report lifecycle, §5.3
backend provenance/calculation/evidence, §5.4 harness safety, §5.5 frontend lifecycle surfaces, §5.6 schema /
generated / manifest / environment), not by ID order. Every ID is present exactly once, and the tables in §4
give the ID, path and disposition, so an ID can be located from §4 without reading §5 linearly. IDs
`HIST-01 … HIST-32` are stable and are intended to be reused by any follow-up work.

### 6.1 Classification totals (32 of 32 accounted for)

| Classification | Count | IDs |
|---|---|---|
| `INCORPORATED` (unqualified) | 13 | HIST-13, 14, 16, 18, 19, 21, 22, 23, 24, 25, 27, 28, 29 |
| `INCORPORATED` + qualifier (`ADVANCED` / `RESIDUAL`) | 5 | HIST-01 (RESIDUAL: policy text), HIST-15 (ADVANCED), HIST-17 (ADVANCED), HIST-20 (ADVANCED + broader path coverage), HIST-32 (RESIDUAL: `db.migrations` flag) |
| `SUPERSEDED` | 12 | HIST-02 (migration delivery mechanism), HIST-03, 04, 05, 06, 07, 08, 09, 10, 11, 12 (analytics provider), HIST-31 (equivalent manifests) |
| `NOT_SUBSTANTIVE` | 1 | HIST-26 (blank-line-only delta) |
| `NEEDS_REVIEW` | 1 | HIST-30 (generated artefact, no generator in canonical) |
| `OBSOLETE` | 0 | — (no row met the obviated-architecture test) |
| **Total** | **32** | 18 `INCORPORATED` + 12 `SUPERSEDED` + 1 `NOT_SUBSTANTIVE` + 1 `NEEDS_REVIEW` |

**Loss risk totals.** `HIGH` **0** · `MEDIUM` **0** · `LOW` **15** (the 12 `SUPERSEDED` rows, HIST-01, HIST-30,
HIST-32) · `NONE` **17** (the 13 unqualified `INCORPORATED` rows, the 3 `ADVANCED` qualifiers HIST-15/17/20, and
HIST-26). Stated plainly: **no historical delta in this population carries a HIGH or MEDIUM business-capability
loss risk.** Every `LOW` row concerns a non-business capability — analytics instrumentation, a generated
artefact, a documentation paragraph, an environment configuration file or a dependency-manifest style.

**Verbatim-identity totals (measurement, not classification).** 12 of the 32 files matched **100 %** of their
distinct added lines in both the canonical working tree and the canonical `HEAD` blob (HIST-14 11/11, 15 3/3,
16 41/41, 18 20/20, 19 8/8, 21 20/20, 22 17/17, 23 5/5, 24 9/9, 27 24/24, 28 5/5, 29 49/49); one more is at 98 %
(HIST-25 62/63) and one at 75 % (HIST-20 33/44, the restructured P1 hook). The remaining low ratios were each
resolved by symbol- or object-level evidence and are explained in §5 (HIST-01 1/21 policy text absent; HIST-02
1/7 delivery mechanism; HIST-03 15/83 coincidence; HIST-17 0/1 value advanced; HIST-30 3/38 generated artefact;
HIST-31 0/12 operator change; HIST-32 1/7 partial).

**Cross-cutting structural fact.** 12 of the 32 historical files are `SAME` as canonical ancestor `93d5cddd` —
HIST-14, HIST-15, HIST-16, HIST-17, HIST-18, HIST-19, HIST-21, HIST-22, HIST-23, HIST-24, HIST-25 and HIST-28 —
meaning their historical working-tree content is **already-committed canonical content** and their measured
deltas are simply movements relative to the older historical baseline `20b7a928`. This is the strongest
structural finding of the reconciliation: a substantial part of the "historical 32" is not un-adopted work at
all.

### 6.2 Highest-risk list (all that remains open, in priority order)

No `HIGH` or `MEDIUM` loss-risk row exists, so this list is exhaustive of everything that remains open. All
three items are **decisions for CarbonTally**, not defects to be fixed blindly, and none of them blocks the
verdict below.

| # | Item | Risk | Evidence | Decision needed |
|---|---|---|---|---|
| 1 | **HIST-01** — the F-046-1 §55.1 policy paragraph is absent from canonical `AGENTS.md`, while the invariant it describes is enforced in canonical `conftest.py` (`0d21e46`). A future agent session reading only the constitution will not know the invariant exists. | `LOW` | `grep` for `55.1` / `F-046-1` / `PROTECTED_PERSISTENT` / `TRUNCATE` in canonical `AGENTS.md` = 0 hits; guard present at `conftest.py` L44 / L51 / L109 / L115–124 | PO/eng: port the §55.1 text into the canonical constitution (documentation only) |
| 2 | **HIST-32** — canonical `supabase/config.toml` still declares the standard 5432x ports while canonical's own harness depends on the 5442x family (`conftest.py` L40 `54426`, L58 `54425`, plus five further scripts); the historical `[db.migrations] enabled = false` has no canonical counterpart. | `LOW` | canonical code naming 5442x vs unchanged `config.toml` (last commit `2d23fb8`) | PO/eng: align the canonical local config with the port family in use; decide `db.migrations` explicitly |
| 3 | **HIST-30** — the newer `output/reports/import_summary.md` (2026-08-15, `DEFRA-2025`, 7,029 factor rows) is a generated artefact with **no generator** in canonical and no consumer. | `LOW` | `grep import_summary` across canonical `backend/`, `tools/`, `scripts/` = 0 hits; canonical blob is the older `2d23fb8` version | PO/eng: accept as an evidence artefact, or reconstruct the importer; separately verify the factor rows in the database |

**Recorded as informational, not as defects.** (a) The ten analytics rows (HIST-03 … HIST-12) leave the admin
application with **no** product-analytics events at all — DEFRA imports, review transitions, invites, staff
creation, settings changes and sign-in/out are uninstrumented; the retired taxonomy is recorded in §5.1 so it
can be re-mapped if wanted, and the choice of provider/custom events is a product decision. (b) `HIST-02` opens
a **separate database-verification item**: that the D21 and D22 objects are actually applied in the intended
environment (definition-level equivalence was verified; live-DB state was not, and is out of scope here).
(c) `HIST-26` must **not** be carried anywhere: it is a blank line.

### 6.3 What this reconciliation does not establish

* **No runtime verification.** No application was started, no API called, no browser driven. Nothing here is
  evidence of current *behaviour*; it is evidence of *repository content*.
* **No database verification.** The live database was not inspected. All DB-level statements concern migration
  *definitions*, not applied state (HIST-02, HIST-15, HIST-16, HIST-21, HIST-30, HIST-32).
* **No test execution.** No unit, integration, frontend or QA-harness suite was run; test *files* were located by
  name only. In particular, no destructive-setup integration suite was pointed at any database — the
  AGENTS.md §55.1 / F-046-1 invariant was respected by not running them at all.
* **No acceptance language.** This is a technical reconciliation. It does not claim CarbonTally is accepted,
  complete or release-ready, and it does not re-verdict any product capability. `IMPLEMENTED`, `TESTED`,
  `VERIFIED` and `ACCEPTED` remain distinct (§73).
* **Population boundary.** Only the 32 files established in §1 are covered — the historical repository's
  working-tree modification set against `20b7a928`. The untracked helper `admin/src/analytics.js` is discussed as
  context for HIST-03 … HIST-12 but is not itself a row. Anything outside this boundary (older history, other
  branches such as `remotes/github/posthog-self-driving/…`, and untracked files in either repository) is out of
  scope.
* **Metric limits.** The incorporation ratio is a whitespace-insensitive set-membership measure with the
  over/under-reporting behaviour described in §3; it is reported, never relied on alone.
* **Commit-graph limits.** Ancestry statements were made with `git merge-base --is-ancestor` against `cb70fd6`
  and hold for that revision only.

### 6.4 Repository state and required statement

* **Canonical working tree** (`/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`, HEAD `cb70fd6`):
  **32** porcelain entries after this task versus **30** before it; the difference is the **two** new untracked
  documents created by this task (this report and its companion `-REPORT.md`). The only tracked modification is
  the pre-existing ` M .gitignore`. **No tracked source file was modified, no file was deleted, no commit was
  created and nothing was pushed.** The pre-existing untracked entries (`.costrict/`, `.p18_audit_tmp/`, the
  `docs/ChatGPT/**` and other `docs/architecture/**` drafts, and two stray one-character files named `8` and `=`)
  were left exactly as found: they are not part of this task and were not touched.
* **Historical working tree** (`/home/shomonrobie/carbon_tally`, branch `main`, HEAD `20b7a928`): **305**
  porcelain entries (227 ` M`, 78 `??`) before and after. All 32 files remain present with their original
  content and mtimes, and no file was created in that repository. Per-path re-checks (`git status --porcelain --
  <path>`) confirm each of the 32 is still reported in its original state.

> **No historical file was deleted or modified during this task.**

### 6.5 Verdict

**`CT_RECON_03B_COMPLETE_TECHNICAL_RECONCILIATION_WITH_UNRESOLVED_ITEMS`.**

The *reconciliation itself is complete*: all 32 files in the population have a measured delta, a canonical
counterpart determination, per-file evidence, a classification with a stated confidence, a loss-risk rating and
a next action — 32 of 32 accounted for, with §6.1's totals summing exactly to the population size. The
`_WITH_UNRESOLVED_ITEMS` qualifier records that **three items remain open for a CarbonTally decision** (§6.2),
each `LOW` risk, none of which is a business, data, provenance or security capability loss:

* `HIST-01` — documentation gap in the canonical constitution (the invariant is enforced in code);
* `HIST-32` — residual environment-configuration misalignment (`supabase/config.toml` versus the 5442x port
  family the canonical harness assumes) plus an undecided `db.migrations` flag;
* `HIST-30` — an orphaned generated artefact with no canonical generator.

No item in the population was found to be an un-adopted change to a live business workflow: every substantive
backend/frontend delta is `INCORPORATED` (13 verbatim, 4 advanced beyond the historical version), every retired
delta is `SUPERSEDED` against a nameable canonical decision, one row is a blank line, and one row is a generated
artefact.

### 6.6 Follow-up work this report deliberately does not perform

1. Port the §55.1 text into the canonical `AGENTS.md` (HIST-01) — documentation change, PO/eng approval.
2. Align canonical `supabase/config.toml` with the 5442x family and decide `db.migrations` (HIST-32).
3. Decide the fate of `output/reports/import_summary.md` and verify the `DEFRA-2025` factor rows in the database
   (HIST-30) — a database-verification task, not file reconciliation.
4. Decide whether admin product-analytics events are wanted at all, and under which provider (HIST-03 … HIST-12).
5. Independently verify in the intended environment that D21/D22 (and the B2 evidence-line-items schema) are
   applied (HIST-02, HIST-15, HIST-16, HIST-21).
6. Independent QA of all of the above by a separate agent, per the OHD/QA cycle (§60): this report is a Cline
   implementation artefact and must be re-tested, not accepted on its own word (§73, §74).
