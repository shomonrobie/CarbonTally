# CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008

**Task ID:** `CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008`
**Title:** CarbonTally Phase 8 + Phase 8-X Gate 0 Governance Consolidation — Resolve Naming, Refresh DM-7, Formalize Existing Forensic Evidence
**Date:** 2026-09-12
**Type:** DOCUMENTATION-ONLY governance consolidation — **no implementation**
**Verdict:** `G0 GOVERNANCE CONSOLIDATION COMPLETE — READY FOR PO REVIEW`

**Evidence discipline:** each material statement is tagged **[R]** repository fact · **[E]** prior
established evidence · **[D]** PO/ratified decision · **[I]** interpretation · **[REC]** recommendation ·
**[U]** unresolved.

---

## 1. Task ID
`CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008`.

## 2. Objective
Close Gate 0 governance items **G0-B** (Phase 8 naming/scope), **G0-F** (historical PDF/IMAGE line-item
treatment) and **G0-I** (`DM-7` refresh), and **formalize** the already-established line-item and
emission-factor forensic findings into durable repository documents — **without any implementation**.

## 3. Scope
Documentation only. Created two forensic reports; made minimal targeted updates to the Disclosure Model
Decision Record (terminology disposition + `DM-7` refinement + forensic references) and the comprehensive
readiness roadmap (evidence/conflict resolutions); produced this mandatory report.

## 4. Non-goals
No B1/B2/B3/B4/P1/P2/X1/X2 implementation; no schema/migration; no API/frontend; no extraction/OCR/AI; no
calculation; no FactorMatchingEngine/factor data; no report generation/template/narrative; no RLS/auth/
billing; no legacy reporting; no Phase 8-X change; no production change; no historical re-extraction; no
`evidence_line_items`; no `source_line_item_id`; no implementation prompt; no commit; no push.

## 5. Evidence reviewed
| Source | Kind |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md` | [D] |
| `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | [D] |
| `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (esp. §1, §6 `DM-7`, §10) | [D] |
| `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` | [D] |
| `docs/cline/reports/CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007.md` | [D] |
| `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (Phase 8 wording, line 26) | [D] |
| `CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md` + `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md` | [D] |
| Regulatory verification suite; lifecycle spec; open-decision closure | [D]/[V] |
| `backend/services/automatic_extraction.py`, `extraction_suggestions.py`, `ai_document_extraction.py`, `automatic_processing.py`, `api/v3_operations.py`, `api/v3_processing_workflow.py`, `engines/calculation.py`, `engines/factor_matching.py`, `data/emission_factors.py`, `core/units.py`, `domain/evidence.py` | [R] |
| `docs/ChatGPT/chat_history/phase 8 implementaion chat history 01.md` §§16–22 | [E] |

## 6. G0-B — naming/scope analysis
- **[R]** `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md:26` records *"Phase 8 — Advanced Analytics —
  official product-roadmap name. Same restrictions as Phase 7 (scope NOT defined; nothing
  authorized)"*. This is the ratified master-roadmap label; it terminates the ratified roadmap at
  Phase 8.
- **[R]** This programme operates a reporting/disclosure architecture (D1–D17) and a 20-decision
  Disclosure Model, and uses "Phase 8" for that work.
- **[R]** The Phase 8-X discovery (§16) lists eight "Phase 8 capabilities" **as task-prompt context**,
  not as a ratified scope.
- **[D]** **Disposition adopted (per task §4 preferred disposition):** the programme this record governs
  is the **Phase 8 Reporting / Disclosure programme**; `Phase 8 — Advanced Analytics` remains the
  historical master-roadmap label; Phase 8-X remains separately bounded; **no third definition adopted**.
- **[R]** The Master Roadmap was **not modified**.

## 7. G0-F — historical line-item analysis
The established forensic evidence ([E], now formalized in the line-item forensic report) distinguishes:
1. CSV/XLSX already persist `line_items[]`; some AI paths can too. **[R]**
2. PDF/IMAGE deterministic extraction produces a flat single record; an 8-line invoice can become 1
   object. **[R]/[E]**
3. Flat historical PDF/IMAGE records **cannot** be deterministically converted to line-level evidence by
   reading existing JSONB. **[E]**
4. OCR/text-available records need a **separately implemented and verified re-parsing/extraction
   capability** to reconstruct lines. **[E]**
5. No silent historical re-extraction; no manufactured line-level provenance. **[D]**

---

## 8. DM-7 update
**[D]** `DM-7` in the Decision Record was **refreshed** (Decision Record §6) with an explicit
"Refinement — historical line-item boundary (Gate 0 — G0-F / G0-I)" that preserves: deterministic backfill
where line-item structure already exists; idempotency; non-destructive behaviour; no silent historical
re-extraction; separate authorisation for any historical re-parsing/extraction; honest treatment of
records where line identity cannot be established. The refinement **clarifies** the existing ruling and
**does not create a 21st decision**. `DM-7` status remains **RATIFIED**. No other decision changed;
`E1-COV` remains **CONDITIONAL**.

## 9. Line-item forensic formalisation
**[R]** Created `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` — a durable
consolidation of the **already-established** evidence (not a new investigation). It documents: PDF/IMAGE
path; CSV/XLSX line-item path; deterministic PDF suggestion behaviour; activity-keyword selection
(tuple-order, whole-document); quantity/unit candidate selection (first match); why cross-line field
mixing occurs; AI extraction path; completeness gating/suppression; persistence findings; API findings;
frontend findings; calculation findings; provenance findings; historical-data implications; root-cause
classification; Phase 8 impact; recommended bounded remediation; non-goals; limitations.

**Classification preserved [E]:** **Primary = A (extraction); consequences = E/F; subsidiary = D;
excluded = B (persistence collapse), C (API collapse).**

## 10. Emission-factor forensic formalisation
**[R]** Created `docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` — a durable
consolidation of the **already-established** findings (§§16–22 of the chat-history addendum). It
documents: picker behaviour; direct SQL vs the FactorMatchingEngine; the three mapping-options surfaces
and their inconsistent unit semantics; unit normalisation; exact vs substring lookup; the EF-E defect;
why EF-E is independent of the 8→1 extraction defect; factor-catalogue evidence limitations; what is
confirmed vs unverified; recommended bounded remediation; non-goals.

**Conclusions preserved [E]:** **FactorMatchingEngine is NOT the root cause of the 8→1 invoice issue**;
**EF-E is a separate confirmed picker defect**; **EF-E must remain a separate implementation batch
(P2)**; no factor-data change is authorised.

## 11. Decision Record changes
| Change | Location | Nature |
|---|---|---|
| Added §1.1 "Terminology governing this record (Gate 0 — G0-B)" | §1 | New subsection — terminology disposition |
| Added forensic + report references to document control | Header | Reference only |
| Refreshed `DM-7` with the historical PDF/IMAGE re-parsing boundary | §6 `DM-7` | Refinement (no new decision, status unchanged) |
| Rewrote §10.3 as "Identified dependency — now formalized (Gate 0)" | §10.3 | Reference + root-cause confirmation |
| Updated §10.4 to reflect the refreshed `DM-7` | §10.4 | Consistency |

**No other decision was altered. No 21st decision was introduced. `E1-COV` unchanged (CONDITIONAL).**

## 12. Comprehensive roadmap changes
| Change | Location | Nature |
|---|---|---|
| Evidence row 10 → formalized forensic reports | §3 | Reference update |
| "Referenced-but-absent evidence" → **RESOLVED (Gate 0)** | §3 | Status update |
| "Evidence-conflict noted" → **RESOLVED (Gate 0)** | §3 | Status update |
| Risks R1/R2/R3 → resolved / recorded | §27 | Status update |
| G0-B/G0-F/G0-I rows → resolved/recorded | §29 | Status update |
| BL-D severity P1 → P2 (disposition recorded) | §23 | Minor correction |

**The 8-batch / 7-verification-gate recommendation was NOT changed** (no genuine contradiction was
discovered). The roadmap was not redesigned.

## 13. Files created
1. `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md`
2. `docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md`
3. `docs/cline/reports/CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md` (this report)

## 14. Files modified
1. `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (targeted: §1.1, header refs, `DM-7`, §10.3, §10.4)
2. `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` (targeted: §3, §23 BL-D, §27, §29)

No other file was created or modified. No source code, schema, migration, API or frontend file was
touched. `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` was **not** modified.

---

## 15. Verification performed

| # | Check | Result |
|---|---|---|
| A | `DM-7` contains the explicit historical PDF/IMAGE re-parsing boundary | **PASS** — Decision Record §6 refinement items 1–5 |
| B | Phase 8 terminology consistent with the governance disposition | **PASS** — Decision Record §1.1 records the governing terminology; roadmap R1/G0-B and BL-D updated |
| C | No 21st Disclosure Model decision introduced | **PASS** — still 20; the `DM-7` change is labelled a refinement, status unchanged |
| D | `E1-COV` remains CONDITIONAL | **PASS** — not touched |
| E | Line-item forensic report contains the established 8→1 root cause | **PASS** — Primary A; consequences E/F; subsidiary D; excluded B/C |
| F | Emission-factor forensic report preserves EF-E as an independent defect | **PASS** (§§9, 11) |
| G | No implementation files modified | **PASS** — only 5 Markdown documents |
| H | No schema/migration/API/frontend/extraction/calculation/factor/RLS/legacy/Phase 8-X change | **PASS** |
| I | No unrelated pre-existing work altered | **PASS** — 208 pre-existing modifications preserved unchanged |
| J | No implementation prompt created | **PASS** |

Additional checks: no `APPEND` scaffold markers remain in the new/edited files; all new files contain
their mandated sections; the two forensic reports explicitly state they formalize existing evidence.

---

## 16. Git / worktree before and after

| Item | Before (task start `20:39:50`) | After (task end `20:44:50`) |
|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (unchanged) |
| Branch | `main` (ahead 14) | `main` (ahead 14) |
| Staged | 0 | **0** |
| Modified (tracked, ` M`) | 208 | **208 (unchanged)** |
| Tracked docs changed by this task (`git diff --name-only`) | — | **0** (the two edited architecture docs are **untracked**, so they do not appear in the tracked diff) |
| Untracked (porcelain entries) | 64 | **64** (unchanged — new files are inside the already-untracked `docs/cline/reports/`) |

- `git status --porcelain -uall` shows the three new/edited report files as untracked additions:
  `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md`, `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md`,
  `CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md`.
- The two **modified** architecture documents were **already untracked** before this task (created in
  earlier Phase 8 tasks); they remain untracked and their edits are therefore invisible to the tracked
  diff. **Verified: zero tracked files were modified.**
- **208 pre-existing modifications preserved unchanged. No unrelated file altered. No reset, checkout,
  clean, stash or revert. No commit, no push, no secrets.**

## 17. Confirmation that no implementation occurred
Confirmed. No code, schema, migration, API, frontend, extraction, OCR, AI-prompt, calculation,
factor-matching, factor-data, report-generation, template, narrative, RLS, auth, billing, legacy or
Phase 8-X change was made. No historical re-extraction; no `evidence_line_items`; no
`source_line_item_id`; no production change; no implementation prompt. The change set is **five Markdown
documents** (three created, two minimally edited).

## 18. Remaining PO decisions
| Item | Status after this task |
|---|---|
| **G0-B** (Phase 8 naming/scope) | **Resolved for this programme** (Decision Record §1.1). Residual: optional Master-Roadmap governance update (PX-1) |
| **G0-F** (historical PDF/IMAGE treatment) | **Recorded** in `DM-7` §6 refinement |
| **G0-I** (`DM-7` refresh) | **DONE** |
| **G0-A** (ESRS E1 evidence closure) | **Open** — PO/evidence |
| **G0-C** (approve batch plan) | **Open** — PO |
| **G0-D** (34-migration production strategy) | **Open** — PO/deployment |
| **G0-E** (B2 scope) | **Open** — PO |
| **G0-G** (Phase 8-X PX-2/PX-4/PX-5/PX-6/PX-7) | **Open** — PO |
| **G0-H** (RLS stays separate) | Recorded; confirmation open |
| **PX-1 … PX-12** (Phase 8-X) | **Open** — PO |

## 19. Final governance state
- **Phase 8 implementation programme** (reporting/disclosure, D1–D17 + 20 decisions): terminology
  **governs implementation tasks**; **implementation NOT AUTHORISED**.
- **Phase 8-X**: separately bounded; **implementation NOT AUTHORISED**.
- **Master Roadmap**: wording **preserved**; no silent rewrite.
- **`DM-7`**: refreshed with the deterministic-backfill vs separately-authorised-re-parsing boundary.
- **P1** (extraction fidelity) and **P2** (EF-E): remain **separate** implementation batches.
- **B1–B4**: **NOT AUTHORISED**.
- **RLS**: separate security workstream. **D16**: separate legacy disposition.
- **Forensic evidence**: now durable repository documents.
- **Decisions unchanged**: still **20** Disclosure Model decisions; `E1-COV` **CONDITIONAL**.

## 20. Final verdict

### `G0 GOVERNANCE CONSOLIDATION COMPLETE — READY FOR PO REVIEW`

**Basis:** the three Gate 0 items (G0-B, G0-F, G0-I) are closed as documentation:
- **G0-B** — the Phase 8 terminology disposition is recorded (Decision Record §1.1); the master-roadmap
  wording is preserved; no third definition was created.
- **G0-F / G0-I** — `DM-7` now carries the explicit historical PDF/IMAGE re-parsing boundary.
- The line-item and emission-factor forensic findings are **formalized** as durable repository reports,
  preserving the established classifications (Primary = A; consequences = E/F; subsidiary = D; excluded
  = B, C; and EF-E as an independent, separately-batched defect).
- All existing ratified decisions are preserved; no 21st decision; `E1-COV` unchanged.
- **No implementation occurred**; the worktree is preserved.

*STOP — documentation-only governance consolidation complete. No B1/P1/P2/X1 begun; no implementation
prompt created; nothing committed or pushed.*



