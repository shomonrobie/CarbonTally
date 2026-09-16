# CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006

**Task reference:** `CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006`
**Title:** CarbonTally Phase 8 — Disclosure Model Decision Record
**Date / time:** 2026-09-12 (session start `2026-09-12T20:14:48+06:00`; Asia/Dhaka)
**Type:** DOCUMENTATION / GOVERNANCE only — **no implementation**
**Role:** Implementation/discovery agent
**Deliverables:** `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` + this report

---

## 1. Task reference and objective

Create the **authoritative Markdown Decision Record** for the 20 ratified Phase 8 Disclosure Model
decisions and their relationship to the already-ratified D1–D17 reporting architecture. This is a
documentation/governance task: **no application code, schema, migration, API, frontend, extraction,
OCR/LLM, calculation, evidence-persistence, RLS, legacy-reporting, S4 or Phase 8-X work** was permitted or
performed.

---

## 2. Scope executed

| In scope (done) | Out of scope (not done) |
|---|---|
| Inspect Phase 8 documentation | Application code changes |
| Inspect git/worktree state | DB schema / migrations |
| Create the Decision Record | API / frontend changes |
| Create this mandatory report | Extraction / OCR / LLM changes |
| Report findings | Calculation / evidence-persistence changes |
| — | RLS changes; legacy-reporting changes |
| — | S4 Narrative Overlay; Phase 8-X |
| — | Investigating/fixing the 8→1 extraction issue |
| — | Creating `evidence_line_items`; creating an implementation prompt |
| — | Commit; push |

---

## 3. Initial git / worktree state (recorded before starting)

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Branch | `main` (`main...origin/main [ahead 14]`) |
| Staged | **0** |
| Modified (` M`) | **208** — all pre-existing, unrelated (e.g. `.agents/skills/**`, `admin/**`, `CarbonTally_DB_Schema_V3M2.sql`, `API_ENDPOINTS.md`, `config.toml`, `supabase/config.toml`) |
| Untracked | **62** collapsed entries (`--untracked-files=all` larger) — pre-existing |
| Both target files | **Did not exist** before this task |

No reset, checkout, clean, revert, stash or stage of unrelated files was performed.

---

## 4. Repository documents inspected

| # | Document | Why |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md` | The D1–D17 register; the relationship source |
| 2 | `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | The design the 20 decisions rule on; terminology source |
| 3 | `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` | Regulatory basis; §24.11 closure status; §1/§6 |
| 4 | `docs/cline/reports/CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004.md` | Design report; §15 PO decisions; worktree verification |
| 5 | `docs/cline/reports/CT-P8-REPORTING-REGULATORY-EVIDENCE-CLOSURE-20260912-002.md` | Prior evidence-closure status |
| 6 | `docs/cline/reports/CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003.md` | G1–G5 outcome; ESRS status (§6–§7) |
| 7 | `docs/cline/reports/CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001.md` | Original verification verdict / PO decisions |
| 8 | `docs/ChatGPT/chat_history/phase 8 implementaion chat history 01.md` | Source of the 8-visible-lines → 1-extracted-item invoice example (§§20–21) |
| 9 | `docs/architecture/CARBONTALLY_PHASE8_*` (lifecycle spec, product ratification, open-decision closure, Phase 8-X boundary) | Terminology and boundary preservation |

Files 1, 2, 3, 4, 9 are **untracked** in git (created earlier in Phase 8), consistent with the Phase 8
worktree state.

---

## 5. D1–D17 relationship confirmed

**Confirmed: YES.** All seventeen ratified decisions were read from the primary ratification record and
mapped individually to the 20 Disclosure Model decisions in Decision Record §3. Every one of the 20
decisions is consistent with D1–D17; **no D1–D17 decision is reopened, weakened or replaced**.

Key mappings: D5 → `A1`/`A3`/`P3`; D10/D11 → `D11-CAT`; D7-R/D13 → `E1-COV`/`E1-VER`/`APPL`;
D8/D9 → `GP-CONS`/`GP-GAS`/`GP-S2M`/`GP-S3`/`GP-BY`; D12 → the `requirement_class` semantics and `DM-5`;
D14/D15 → `E1-VER`, `DM-7`; D16 → `LEG`; D4/D17 → `DM-1`.

---

## 6. All 20 decisions incorporated

| # | ID | Title | Status recorded |
|---|---|---|---|
| 1 | `A1` | Narrative allowlist | RATIFIED |
| 2 | `A3` | Narrative numeric limits | RATIFIED |
| 3 | `P3` | Customer-editable content | RATIFIED |
| 4 | `D11-CAT` | Intensity denominator catalogue | RATIFIED |
| 5 | `E1-COV` | ESRS E1 coverage | **CONDITIONAL** |
| 6 | `E1-VER` | ESRS E1 version | RATIFIED |
| 7 | `APPL` | Applicability | RATIFIED |
| 8 | `GP-CONS` | Consolidation | RATIFIED |
| 9 | `GP-GAS` | Per-gas reporting | RATIFIED |
| 10 | `GP-S2M` | Scope 2 | RATIFIED |
| 11 | `GP-S3` | Scope 3 | RATIFIED |
| 12 | `GP-BY` | Base year | RATIFIED |
| 13 | `LEG` | Legacy route | RATIFIED (execution: SEPARATE WORKSTREAM) |
| 14 | `DM-1` | Requirement codes | RATIFIED |
| 15 | `DM-2` | Purpose vs `report_type` | RATIFIED |
| 16 | `DM-3` | Reporting period | RATIFIED |
| 17 | `DM-4` | Benchmarking | RATIFIED |
| 18 | `DM-5` | Finalisation | RATIFIED |
| 19 | `DM-6` | Drill-down | RATIFIED |
| 20 | `DM-7` | Line-item population | RATIFIED |

**All 20/20 recorded** (19 `RATIFIED`, 1 `CONDITIONAL`), each with PO ruling, status, implementation
implication, acceptance criterion and deferred/separate boundary. **No decision was invented; none was
added beyond the 20.** These 20 are the 13 carried-forward decisions in the design report §15
(A1, A3, P3, D11-CAT, E1-COV, E1-VER, APPL, GP-CONS, GP-GAS, GP-S2M, GP-S3, GP-BY, LEG) plus the 7
design decisions DM-1…DM-7 — total 20.

---

## 7. Conflicts found

**No blocking conflict.** One **sharpening** was identified and recorded explicitly (not silently
reconciled):

| # | Item | Repo position (design doc §26.2 `DM-5` **recommendation**) | PO ruling in this task | Disposition |
|---|---|---|---|---|
| C-1 | `DM-5` finalisation policy | Recommended option (a): *"block on `REQUIRED` only, allow with recorded basis"* | Distinguishes **`CUSTOMER_INPUT_REQUIRED`** (block finalisation unless an approved workflow resolves it) from **`NOT_SUPPORTED`** (surface the limitation honestly) | The PO ruling **sharpens** the design recommendation. Recorded as PO-authoritative in Decision Record §6 `DM-5` (and §8), with an explicit *Sharpen note*. Not silently overwritten. |

Other observed differences were **reconciled as compatible expansions**, and are recorded rather than
hidden:

| # | Item | Observation | Disposition |
|---|---|---|---|
| C-2 | D2 chain wording | The task's D2 chain adds `CALCULATION / PROVENANCE`, `EVIDENCE`, `NARRATIVE CONTENT` explicitly vs the short form in the D1–D17 summary | **Compatible expansion** of the same chain; the D1–D17 document's own §2.2 detail already shows DATA → CALCULATION/PROVENANCE → EVIDENCE → DISCLOSURE MODEL → PRESENTATION. Recorded as the canonical chain wording |
| C-3 | Design status vs decisions | The design doc was `DESIGN OUTPUT — NOT IMPLEMENTED` and left `DM-*` open; this record now ratifies them | Intended progression, not a conflict. `CONDITIONAL` (`E1-COV`) preserved; Gate 5 stays NOT AUTHORIZED |
| C-4 | 12-section report | D3 presentation-template-only vs the legacy PDF generator's 6-section output (a pre-existing repo discrepancy noted in the design report §19 D-1) | Out of scope here; not resolved, not altered; no decision depends on it |

No conflict made accurate documentation impossible. **No regulatory identifier, threshold, limit or
denominator was invented.**

---

## 8. Evidence gaps

Carried forward unchanged and **not invented** (regulatory verification report §24.11; design §25):

| # | Gap | Status | Effect on the Decision Record |
|---|---|---|---|
| 1 | **ESRS E1 exact disclosure identifiers/titles** (Annex I to (EU) 2023/2772) | **[U]** — authoritative representation limitation | Drives `E1-COV` = **CONDITIONAL**; `DM-1` allows internal concept keys with an explicit unresolved marker |
| 2 | **GHG Protocol Corporate Standard Chapter 9** required/optional lists | **[U]** — PDF-only | Required-vs-optional classification is a PO/evidence call; no optional item promoted to mandatory |
| 3 | SECR SI's own "large" definition + CA 2006 s.465 numerics | **[U]** partial — verified parts captured (`>40,000 kWh`; 2-of-3 over two consecutive FYs; 6 Apr 2025 change) | Residual to close before the precise test is encoded; recorded as a boundary, not invented |
| 4 | Directive (EU) 2026/470 own application dates | **[U]** detail | Framework version recorded with OJ ref; exact amended dates to transcribe later |
| 5 | Irish competent authority designation | **[U]** context — no product requirement | No design impact |
| 6 | Whether the 2026 Simplified ESRS is in force | **[U]** forward-looking | Represented as `ADOPTED_NOT_IN_FORCE`; re-verify at each framework-version review |

**Evidence gaps were NOT closed by this task** (out of scope) and **no identifiers/thresholds/limits were
invented**. `E1-COV` remains the only `CONDITIONAL` decision.

---

## 9. Line-item traceability dependency recorded

**YES.** Standard: Decision Record §10. Recorded as a **Phase 8 implementation dependency / acceptance
invariant**, explicitly **not** as a new product decision.

- The intended chain (SOURCE DOCUMENT → SOURCE LINE → EXTRACTION LINE ITEM → FACTOR MAPPING → VALIDATION →
  CALCULATION SNAPSHOT → EMISSIONS → EVIDENCE → DISCLOSURE → REPORT) and the forward/reverse
  report → disclosure → calculation → evidence line → source traceability requirement are recorded.
- The **honesty invariant** is recorded: document-level-only evidence must **not** be dressed up as false
  line-level precision.
- The identified upstream risk — **8 visible source invoice line items → apparently only 1 extracted item**,
  with the retained item possibly semantically incorrect (e.g. a `Water` line's quantity paired with a
  `Waste` activity label) — is recorded **as a dependency/risk only**.
- **Not investigated, not reproduced, not fixed** in this task (hard scope boundary respected). A separate
  bounded discovery task is expected after PO review of this record.
- This was **not** turned into a 21st decision.

---

## 10. Exact files changed

| File | Action | Size | Detail |
|---|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` | **Created** | 42,169 bytes (715 lines) | Sections 1–19; all 20 decisions; semantic invariants; line-item dependency; boundaries; gate; change-control |
| `docs/cline/reports/CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006.md` | **Created** (this report) | — | Mandatory written report |

**No other file was created, modified, moved or deleted.** No pre-existing document was edited — including
the D1–D17 ratification record, the disclosure design, the regulatory verification report and every prior
Phase 8 report.

---

## 11. Confirmation that no implementation was performed

Confirmed. **No** application code, **no** database schema, **no** migration, **no** API, **no** frontend,
**no** extraction, **no** OCR/LLM, **no** calculation, **no** evidence-persistence, **no** RLS, **no**
legacy-reporting, **no** S4 (Narrative Overlay) and **no** Phase 8-X change was made. No `evidence_line_items`
was created; the 8→1 extraction issue was **not** investigated; no performance/benchmarking code was
touched; no implementation prompt was created. The change set is **two Markdown documents only**.

---

## 12. Final git / worktree state (recorded after completion)

| Item | Before | After | Change |
|---|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | **unchanged (no commit)** |
| Branch | `main` (`ahead 14`) | `main` (`ahead 14`) | unchanged |
| Staged | 0 | **0** | unchanged |
| Modified (` M`) | 208 | **208** | **unchanged** (all pre-existing / unrelated) |
| Untracked (porcelain entries) | 62 | **63** | **+1** = the new untracked Decision Record file |
| `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` | did not exist | `?? ` (untracked) | **new** |
| `docs/cline/reports/CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006.md` | did not exist | present inside pre-existing untracked `docs/cline/reports/` | **new** |

Recorded `2026-09-12T20:18:06+06:00`. No unrelated file was staged, reverted, cleaned, checked out or
modified. **No commit and no push were performed.** No secrets were introduced. `.gitignore`/`.clinerules`
were not modified.

---

## 13. Recommended next Phase 8 gate

1. **PO review of this Decision Record** (primary next step). The 20 decisions, the semantic invariants
   (`CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`; requirement ≠ applicability ≠ capability ≠ customer
   input), the boundaries and the `DM-5` sharpening are presented for ratification.
2. **Resolve `E1-COV`'s condition** — close the ESRS E1 identifier/coverage evidence gap so the only
   `CONDITIONAL` decision can move to `RATIFIED`.
3. **Then** issue a **separate bounded Cline discovery task** for the identified **8→1 multi-line invoice
   extraction** dependency (§9 / Decision Record §10) — investigation only, not a fix.
4. **Only after** PO review + evidence closure + the disclosure design is accepted as implementation-ready:
   consider **Gate 5 implementation authorisation** (Stage 1), with independent verification (ALLOW + DENY)
   as a mandatory component, and with S4 / D16 / RLS remediation / Phase 8-X remaining separate.

---

## 14. Final verdict

### `DECISION RECORD COMPLETE — READY FOR PO REVIEW`

**Basis:**

- D1–D17 relationship confirmed and documented; no ratified decision reopened (§5).
- All 20 Disclosure Model decisions incorporated, each with PO ruling, status, implementation implication,
  acceptance criterion and boundary (§6); 19 `RATIFIED`, 1 `CONDITIONAL` (`E1-COV`).
- The mandatory semantic invariants are stated explicitly (`NOT_SUPPORTED` vs `CUSTOMER_INPUT_REQUIRED`;
  requirement vs applicability vs capability vs customer input).
- The line-item traceability dependency is recorded as an acceptance invariant — **not** a new decision and
  **not** investigated.
- All required boundary, deferred-work, gate and change-control sections are present.
- The single observed sharpening (`DM-5`) is recorded explicitly — **no silent reconciliation**.
- Evidence gaps carried forward unchanged; **nothing invented**.
- **No implementation performed**; the change set is two Markdown documents; no commit and no push.

**This verdict is documentation-complete, not implementation-ready.** Gate 5 remains **NOT AUTHORIZED**.

*Awaiting PO review. STOP — no further work initiated.*



