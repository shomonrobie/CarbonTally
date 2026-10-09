# CarbonTally — Historical 32-File Technical Reconciliation — Report

**Date:** 2026-09-27
**Companion (full technical record):** `docs/architecture/CT-PO-CARBONTALLY-HISTORICAL-32-FILE-TECHNICAL-RECONCILIATION-20260926.md`
**Nature:** read-only technical reconciliation. No historical file was deleted or modified during this task.
**Verdict:** `CT_RECON_03B_COMPLETE_TECHNICAL_RECONCILIATION_WITH_UNRESOLVED_ITEMS`

---

## 1. What was asked and what was measured

Reconcile the 32 files that the historical repository `/home/shomonrobie/carbon_tally` (branch `main`, HEAD
`20b7a928`) carries as **working-tree modifications** against the canonical repository
`/home/shomonrobie/ct_93d5cdd` (branch `p8-release-reconciled`, HEAD `cb70fd6`), and state for each file whether
the delta is incorporated, superseded, obsolete, non-substantive or unresolved — without deleting or modifying
anything.

Repository state at measurement — historical: **305** porcelain entries (227 ` M`, 78 `??`), mtimes 2026-07-21 …
2026-09-15; canonical: **30** entries (1 ` M .gitignore`, 29 `??`), no uncommitted source modifications.

## 2. Method in one paragraph

Per file: whitespace-insensitive numstat of the historical worktree against `20b7a928`; distinct non-blank
added/removed lines; set-membership of added lines against **both** the canonical worktree file and the canonical
`HEAD:<path>` blob (reported byte-for-byte identically, so canonical worktree = canonical commit); content probes
against canonical ancestors (`93d5cddd`, `f1a1cf8`) to detect already-committed canonical content; canonical path
lineage and newest touching commit; then symbol-, object- and call-site-level resolution of every disposition in
§5 of the full record. No test was executed, no database inspected and no application started.

## 3. Result — all 32 accounted for

| Classification | Count |
|---|---|
| `INCORPORATED` — unqualified | 13 |
| `INCORPORATED` — with `ADVANCED` / `RESIDUAL` qualifier | 5 |
| `SUPERSEDED` | 12 |
| `NOT_SUBSTANTIVE` | 1 |
| `NEEDS_REVIEW` | 1 |
| `OBSOLETE` | 0 |
| **Total** | **32** |

**Loss risk:** `HIGH` 0 · `MEDIUM` 0 · `LOW` 15 · `NONE` 17. **No historical delta carries a HIGH or MEDIUM
business-capability loss risk.** Twelve files matched 100 % of their added lines in the canonical worktree and
blob; twelve files are byte-equal to canonical ancestor `93d5cddd`, i.e. already-committed canonical content.

## 4. The substantive content is in canonical

* Backend provenance/calculation/evidence — `source_line_item_id` (emissions logs L102 / L570 / L575 / L820 /
  L856 / L997), `_materialise_evidence_lines` + `extraction_method` (manual_extraction L450 / L472 / L481 / L500 /
  L503 / L517 / L541), `PIPELINE_VERSION = "v3-auto-1.2"` (L45), `CalculationSnapshot` / `CalculationRequest`
  dimensions, the B2 §13.2 `get_by_ordinals` lookup (L1822–1841, request assembly L1928), and
  `save_extracted_data(..., "manual")` at both API call sites (L1163–1165, L1740–1742).
* P1 extraction fidelity — the historical `_extract_pdf` hook is superseded by the canonical
  `_apply_p1_fidelity(...)` (L378), which is tenant-aware and covers the image path the historical change missed.
* Report lifecycle (P8-S6) — API, panel, action map (`REPORT_LIFECYCLE_ACTION_CALLS` L211), report-detail mount
  (L17 / L234), CSS and all three test files are present in canonical.
* Harness safety — the F-046-1 refusal is enforced in canonical `conftest.py` (L44 / L51 / L109 / L115–124,
  commit `0d21e46`).
* Schema — the historical SQL dump's delta (white-label column, processing-entity FK / index / RLS policies) is
  delivered canonically as `d21_white_label_branding.sql` and `d22_processing_work_assignment.sql`, with canonical
  strictly wider (it adds the index).

## 5. Retired content is retired by decision

Twelve files are `SUPERSEDED`. Ten are one uncommitted PostHog instrumentation set on the admin app (its helper
`admin/src/analytics.js` is untracked; the SDK commit `363105a` is not an ancestor of `HEAD` and lives only on
`remotes/github/posthog-self-driving/…`): canonical adopts **GA4, admin-configurable** (`37b19d1`, an ancestor)
and contains **no** analytics client at all (`captureEvent` / `identifyUser` / `posthog` = 0 hits in application
source). One is the monolithic SQL dump (mechanism superseded by migrations). One is the root `requirements.txt`
un-pinning, superseded by capability-equivalent canonical manifests that are a superset. A single file's delta is
one deleted blank line.

## 6. Open items (all LOW risk, all decisions)

1. **HIST-01** — the F-046-1 §55.1 policy text is **absent from canonical `AGENTS.md`** although the invariant is
   enforced in canonical code. Decision: port the text.
2. **HIST-32** — canonical `supabase/config.toml` still declares the 5432x ports while canonical's own harness
   depends on the **5442x** family (`conftest.py` L40 `54426`, L58 `54425`, plus five scripts); the historical
   `[db.migrations] enabled = false` has no canonical counterpart. Decision: align the config, decide the flag.
3. **HIST-30** — `output/reports/import_summary.md` (2026-08-15, `DEFRA-2025`, 7,029 factor rows) is a generated
   artefact with **no generator** in canonical and no consumer. Decision: keep as evidence or rebuild the
   importer; verify the factor rows in the database separately.

Informational: the admin app now emits **no** product-analytics events (the retired taxonomy is recorded in the
full report so it can be re-mapped); live-database verification of D21/D22 and the B2 evidence-line-items schema
is a separate DB-verification task; the one blank-line delta (HIST-26) must not be carried anywhere.

## 7. Required statement and hygiene

> **No historical file was deleted or modified during this task.**

* **Historical repository unchanged:** 305 porcelain entries before and after, all 32 paths still present in
  their original state, no file created there, nothing committed.
* **Canonical repository:** two **new untracked** documents (this report and its companion) were added, taking
  the porcelain count from 30 to 32. The only tracked modification remains the pre-existing ` M .gitignore`. No
  tracked file was modified, nothing was deleted, no commit was made and nothing was pushed. Pre-existing
  untracked entries were left exactly as found.
* **Secrets:** no secrets, credentials, tokens, JWTs or signed URLs are recorded in this document set.
* **Limits:** this is a read-only reconciliation of *repository content*. It contains no runtime, API, browser,
  database or test execution, and it asserts **no** acceptance verdict — `IMPLEMENTED`, `TESTED`, `VERIFIED` and
  `ACCEPTED` remain distinct.
* **Next step:** independent QA by a separate agent (the full record's §6.6 lists the six follow-ups).
