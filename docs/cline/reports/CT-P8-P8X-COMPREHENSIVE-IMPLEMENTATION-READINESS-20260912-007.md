# CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007

**Task ID:** `CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007`
**Title:** CarbonTally Phase 8 + Phase 8-X Comprehensive Implementation-Readiness, Dependency, Parallelisation and Batch-Minimisation Assessment
**Date:** 2026-09-12
**Type:** READ-ONLY governance / discovery / planning — **no implementation**
**Role:** Senior software architect / technical lead
**Primary deliverable:** `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md`
**Verdict:** `DECISION READINESS COMPLETE — READY FOR PO REVIEW`

**Evidence discipline:** every material statement below is tagged **[R]** (repository fact), **[D]** (PO/ratified decision), **[V]** (verified), **[U]** (unresolved), **[I]** (interpretation) or **[REC]** (recommendation).

---

## 1. Task ID
`CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007`.

## 2. Task objective
Determine the **minimum practical number of safe implementation batches and independent-verification
gates** to complete the remaining Phase 8 and Phase 8-X scope, optimising for maximum reuse, safe
parallelisation, clear dependency ordering, independent verifiability, minimal regression risk and
preserved governance — **without implementing anything**.

## 3. Scope
Read-only inspection of Phase 8 and Phase 8-X governance documents, source, migrations, routes, services,
tests, frontend and configuration; production of (a) the architecture roadmap and (b) this report.

## 4. Non-goals
No code, schema, migration, API, route, frontend, extraction, OCR, AI prompt, calculation, factor
matching/data, report generation, template, narrative, RLS, auth, billing, legacy or Phase 8-X change.
No production migration, no data alteration, no branch, no commit, no push, no implementation prompt.
No re-opening of D1–D17 or the 20 Disclosure Model decisions. No judicial re-investigation of the 8→1
issue or the EF-E issue.

## 5. Evidence reviewed
See roadmap §3 for the full 15-entry register. Highlights: the D1–D17 ratification, the Disclosure Model
design + Decision Record, the regulatory verification suite, the lifecycle spec, the open-decision
closure, the S4 report, the **chat history §§20–21** (the only current source of the forensic evidence),
the Phase 8-X discovery + OHD companion, the RLS baseline/register, the Master Roadmap, and the relevant
source/migrations.

**[U]** Two referenced forensic artefacts **do not exist as files**: `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md`
and a September-12 emission-factor forensic/addendum report. The current equivalent evidence is the chat
history + disclosure-design §14. A proper forensic report should be filed.

---

## 6. Repository / current-state findings
- **[R]** The Disclosure Model is **entirely unimplemented**: zero hits for `disclosure_framework`,
  `disclosure_requirement`, `disclosure_value`, `disclosure_applicability`, `evidence_line_items`,
  `source_line_item_id` across `supabase/migrations/**` and `backend/**`.
- **[R]** The report-version lifecycle **is** implemented (`backend/domain/report_lifecycle.py`;
  `report_versions.status` migration; version-scoped endpoints).
- **[R]** `SUPPORTED_REPORT_TYPES` has exactly one entry (`annual`); the engine composes 12 sections.
- **[R]** No `purpose_code`; no narrative store; no operational-intelligence service; no worker heartbeat;
  no `/api/v3/ops/runtime/*`.
- **[R]** 55 migrations in repo; **1 p8-prefixed**.

## 7. Phase 8 findings
- **[D]** D1–D17 + 20 decisions are the fixed constraints.
- **[R]** Implemented/verified: lifecycle (S1/S3), report engine, calculation + snapshots, D33 evidence,
  CSV/XLSX line-items, factor catalogue + engine, auth/scope machinery.
- **[R]** Missing: the whole disclosure layer, `evidence_line_items`, narrative, SECR intensity model,
  per-gas/base-year/consolidation attribute, frozen-artefact handling.
- **[D]** `E1-COV` is **CONDITIONAL** (ESRS E1 identifiers unresolved) — preserved, not upgraded.
- **[R]** Legacy route `POST /api/reports/generate-enhanced-report` is live (D16; untouched).

## 8. Phase 8-X findings
- **[D]** Authoritative scope **exists** (Phase 8-X discovery + OHD companion): bounded extension, MUST
  M1–M6, SHOULD S1–S6, LATER L1–L7, stages X1–X8, blockers BL-1/BL-2, **12 PO decisions PX-1…PX-12**.
- **[R]** Signal already persisted across ~24 tables; the gaps are aggregation, worker liveness,
  health-path correctness, alerting, deployment introspection and any observability tooling.
- **[R]** Nothing implemented.
- **[R]** **PX-1** flags a Phase 8 **naming/scope discrepancy** (see §15).

## 9. Dependency findings
Critical path `G0 → B1 → B2 → B3 → B4`. Parallel-safe: **P1** (extraction), **P2** (EF-E), **X1**
(Phase 8-X X1–X3), **E1 evidence closure**. Must remain separate: P1 vs P2; Phase 8-X vs RLS; Phase 8 vs
D16; the 34-migration backlog vs feature work. No artificial dependencies created. (Roadmap §16.)

## 10. Parallelisation findings
Four parallel tracks are safe: extraction fixes, Phase 8-X, E1 evidence, and the Phase 8 core critical
path. **Do NOT** parallelise: P1+P2 (different root causes), Phase 8-X+RLS, E1-rows-by-inventing-IDs, or
backfill-by-re-extraction. (Roadmap §17.)

## 11. Batch-minimisation findings
Option A (3 batches) fails blast-radius/separation rules; Option C (13) adds gate overhead for no safety
gain; **Option B (8 batches / 7 gates) recommended**. Each batch is cohesive with an independent
rollback boundary. (Roadmap §19–§20.)

## 12. Recommended implementation sequence
`G0 → B1 → B2 → B3 → B4` (Phase 8 core) **in parallel with** `P1`, `P2` (fixes) and `X1 → X2` (Phase 8-X).
(Roadmap §25.)

## 13. Recommended verification gates
**7 gates** — V1 (B1), V2 (B2), V3 (B3), V4 (B4), VP (P1+P2, verified separately), VX1 (X1), VX2 (X2,
conditional) — preceded by the prerequisite **G0**. (Roadmap §21.)

## 14. Production blockers
**P0:** RLS baseline (97/104 tables RLS disabled, `anon` `GRANT ALL`) [V]; **34 outstanding production
migrations** incl. the P8 lifecycle migration [V]. **P1:** E1 evidence gap; Phase 8 naming discrepancy;
extraction 8→1; row-level evidence. **P2:** EF-E; D16 legacy; Phase 8-X runtime verification (BL-1/BL-2);
customer-shaped e2e calculation evidence (verify, not assume); subscription/allowance provisioning;
`DATABASE_URL` config. (Roadmap §23.)

## 15. Open evidence / PO decisions
Evidence-blocked [U]: ESRS E1 identifiers; GHG Protocol Ch.9 lists; residual SECR numerics.
PO-decision-blocked [D]: PX-1 (Phase 8 naming), PX-2/PX-4/PX-5/PX-6/PX-7 (Phase 8-X), plus G0-A…G0-I in
roadmap §29 — including the **`DM-7` wording conflict** (detail in the "Conflicts identified" block below).

## 16. Reuse recommendations
REUSE AS-IS: lifecycle, report engine, calculation+snapshots, factor catalogue/engine, D33 evidence,
CSV/XLSX line-items, ops API/console, auth/scope, audit, retention, notifications, billing, `normalize_unit`,
`activity_categories`. REUSE WITH EXTENSION: evidence→line, report engine→purpose projections, ops
console→tabs, retention→operational keys. REQUIRES CHANGE: the picker query (P2), extraction (P1),
`template_structure` (keep presentation-only). DO NOT REUSE: legacy `report_generator.py` / enhanced-report
route (D16). (Roadmap §7.)

---

## Conflicts identified (detail)

| # | Conflict | Sources | Disposition |
|---|---|---|---|
| C-1 | **Phase 8 naming/scope.** The ratified `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md:26` records *"Phase 8 — Advanced Analytics — official product-roadmap name. Same restrictions as Phase 7 (scope NOT defined; nothing authorized)"*. Yet this programme treats Phase 8 as the **reporting/disclosure** architecture (D1–D17), and the Phase 8-X discovery references a third list of **8 Phase 8 capabilities** (Advanced Carbon Analytics; CarbonTally Insight; Intelligent Entity-Specific Reports; Report Versioning & Approval; Net-Zero Planning; Carbon Data Quality Intelligence; Disclosure/Reporting Intelligence; Internal Benchmarking). | **[R]/[D]** | **Recorded, not silently reconciled.** Requires **PO decision (PX-1)**: which definition is authoritative for "Phase 8" |
| C-2 | **`DM-7` wording.** The Decision Record's `DM-7` says historical line-item population uses "existing persisted extraction data **where possible**". This task's §4 states that historical PDF/IMAGE records **cannot** be populated deterministically and require a separately implemented re-parsing capability. The Decision Record does **not** contain that refinement. | **[D]/[task]** | **Recorded, not reconciled.** The Decision Record was **not** modified (read-only task). PO note / wording refresh requested (roadmap G0-I) |
| C-3 | **Referenced forensic reports absent.** The task cites `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` and a Sept-12 emission-factor forensic; neither exists as a file. | **[R]** | Evidence reconstructed from the chat history + design §14; a proper forensic report should be filed |
| C-4 | **Production migration state vs repo.** Repo has 55 migrations; production has 21 applied / 34 outstanding (verified). The Phase 8 lifecycle migration is therefore **not** in production. | **[V]** | Deployment blocker BL-B; not a documentation conflict |

**No conflict made a reliable roadmap impossible.** No regulatory identifier, threshold, deadline or
denominator was invented.

---

## 17. Schema / API / backend / frontend impact
Summarised in roadmap §22. In brief: **B1/B2** are additive schema; **B3/B4** are read-only/extend on the
existing spine; **P1/P2** change only localised existing code; **X1/X2** extend the existing ops namespace
and console. No change is recommended merely for elegance.

## 18. Historical data implications
Class-1 records (already carrying `line_items[]`) support **deterministic, idempotent** backfill; flat
PDF/IMAGE records **cannot** be populated deterministically; OCR-available records need a **separately
authorised** re-parsing task. **Invariant preserved:** no automatic historical re-extraction for
Disclosure Model population (`DM-7`); backfill is additive, idempotent, non-destructive; unmatched rows
stay unmatched; no row rewritten to manufacture provenance. (Roadmap §15.)

## 19. Git / worktree before and after

| Item | Before | After |
|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (unchanged; no commit) |
| Branch | `main` (ahead 14) | `main` (ahead 14) |
| Staged | 0 | 0 |
| Modified (` M`) | 208 | 208 (unchanged; all pre-existing) |
| Untracked (porcelain entries) | 63 | 64 (**+1** = the new roadmap file; this report is inside the already-untracked `docs/cline/reports/`) |

No reset/checkout/clean/revert/stash of unrelated work; no unrelated file staged; **no commit, no push**;
no secrets introduced.

## 20. Files created
1. `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md`
2. `docs/cline/reports/CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007.md` (this report)

No pre-existing file was modified, moved or deleted.

## 21. Confirmation that no implementation occurred
Confirmed. **No** code, schema, migration, API, route, frontend, extraction, OCR, AI-prompt, calculation,
factor-matching, factor-data, report-generation, template, narrative, RLS, auth, billing, legacy or
Phase 8-X change was made. No production migration was run; no production data altered; no branch
created; no commit; no push; no implementation prompt created. The change set is **two Markdown documents**.

## 22. Final verdict

### `DECISION READINESS COMPLETE — READY FOR PO REVIEW`

**Basis:** the remaining Phase 8 scope is one genuinely new layer (Disclosure Model) plus one upstream
correctness dependency (extraction) plus two small independent fixes; Phase 8-X is predominantly
consolidation over already-persisted signal. A reliable, safely-bounded roadmap can be produced:
**8 implementation batches**, **7 independent verification gates**, preceded by prerequisite gate **G0**.
Parallelisation opportunities (P1, P2, X1, E1 evidence) are identified with reasons; work that must remain
separate is stated. Blockers are **identified and sequenced** (RLS baseline; 34 outstanding migrations;
E1 evidence; the Phase 8 naming discrepancy) — none is unknown, and none is silently resolved. The verdict
is **not** BLOCKED because no missing evidence/PO decision prevents a reliable roadmap from being
produced; the required PO decisions are enumerated (roadmap §29).

*STOP — read-only assessment complete. No implementation begun.*


