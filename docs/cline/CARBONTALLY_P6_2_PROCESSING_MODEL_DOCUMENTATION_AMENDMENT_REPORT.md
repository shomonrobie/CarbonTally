# CarbonTally — P6-2 Processing Model Documentation Amendment Report

**Prompt Ref:** `CT-P6-2D-MODEL-DOC-20260910-001`
**Response Ref:** `CT-P6-2D-MODEL-DOC-20260910-001-R`
**Date/time:** 10 September 2026, approx. 17:49–18:05 local (Asia/Dhaka +0600)
**Task type:** DOCUMENTATION-ONLY AMENDMENT — no code, schema, migration, RLS,
permission, billing, UI, workflow or test change.

---

## 1. Executive Summary

Four authoritative documents were amended, additively, to express the processing
model that the architecture and implementation **already** have, and to record the
Product Owner's decision to **withdraw** the proposed `CONSULTANT`
`processing_origin` value:

1. `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` — new
   *Processing model — dimensional clarification* subsection in §9, plus an
   actor-vs-origin clarification next to the existing origin sentence.
2. `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` — new *Scope of the origin
   concept* clarification at the end of §4.
3. `CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` — a
   terminology amendment note after §13 clarifying every "consultant origin" phrase.
4. `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` — a new ratified-PO-decision section
   (`## P6-2D Ratified PO Decision — 2026-09-10`,
   `PO-P6-2D-D7b-R-20260910`, **WITHDRAWN / REJECTED AS PROPOSED**), a D7 framing
   clarification, a D5 supersession note, and a header pointer.

**Nothing was implemented.** The withdrawal *removes* a proposal and therefore
requires no code, schema, migration, RLS, permission, billing, UI, workflow or test
change. No `processing_origin` value, CHECK constraint or routing was altered; no
database or code file was touched.

**Post-edit consistency review:** the four amended documents are now consistent (no
document states or implies `CONSULTANT = processing_origin`,
`processing_origin = actor`, `processing_origin = processing mode`, or that mode is
determined by actor). **One residual stale statement remains in a document this
task was instructed not to rewrite** —
`CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` §22
("consultant origin value") — reported in §12. Hence the verdict:

### `DOCUMENTATION AMENDMENT COMPLETE — ADDITIONAL CLARIFICATION REQUIRED`

(the clarification required is the single non-target-document wording item in §12;
the four required amendments are complete)

## 2. Source Reconciliation Used

`docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_RECONCILIATION_REPORT.md`
(`CT-P6-2D-MODEL-RA-20260910-001`, verdict `CLARIFICATION REQUIRED — PO RATIFICATION
BLOCKED` scoped to D7b). Its evidence base:

- `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §3/§4 — origin = internal-vs-PE
  manual capacity, immutable, routing-driving; *"Internal or PE?"*.
- Blueprint V1.3 l.497/l.1349 — *"PEs are additional controlled processing capacity,
  not the exclusive source of manual processing"*.
- `api/processing_mode.py` — `item_is_automatic` (actor-independent, fail-closed;
  docstring designates D7 as the home of final mode provenance).
- `services/automatic_extraction.py`, `services/automatic_processing.py`,
  `domain/automatic_processing.py` — PDF/CSV/XLSX/OCR extraction, confidence gates
  (0.5 extract / 0.6 map), `mark_blocked` → `manual_review`.
- `api/v3_processing_workflow.py`, `api/v3_operations.py`, `api/v3_pe.py`,
  `data/manual_extraction.py` — the four actor surfaces and origin write-once
  (`mark_pe_origin_if_unset`).
- `data/emissions_logs.py`, `data/audit.py` — provenance (actor / factor / source /
  machine).

## 3. PO Decision Applied

> **WITHDRAW the proposed `CONSULTANT` value from `processing_origin`.**

Applied as a **policy decision only**: recorded in the PO decision register
(`PO-P6-2D-D7b-R-20260910` → **WITHDRAWN / REJECTED AS PROPOSED**) and propagated as
terminology clarification into the Blueprint, the V1.2 origin model and the P6-2
consultant architecture. **Not implemented** — and, being a withdrawal, requiring
nothing to be implemented.

## 4. Documents Amended

| # | Document | Amendment |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | §9: new *Processing model — dimensional clarification* subsection (7-concept table, four actors, actor/mode matrix, PE-as-manual-capacity, input-type independence, automatic→manual fallback, origin meaning) + clarification blockquote next to the existing origin sentence |
| 2 | `docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` | §4: new *Scope of the origin concept (clarification, 10 September 2026)* paragraph |
| 3 | `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` | §13: terminology amendment note (blockquote) after the P6-2F bullet |
| 4 | `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | Header pointer; D5 supersession note; D7 framing clarification; **new** `## P6-2D Ratified PO Decision — 2026-09-10` section with `PO-P6-2D-D7b-R-20260910` |

## 5. Exact Sections Amended (anchored, additive)

| Document | Anchor | Added content | Lines |
|---|---|---|---|
| Blueprint V1.3 | after the "processing origin must be preserved…" sentence in §9 | `> **Clarification (10 September 2026):**` blockquote (5 lines) | 510–514 |
| Blueprint V1.3 | immediately before `# 10. Automatic Processing` | `### Processing model — dimensional clarification (documentation amendment, 10 September 2026)` subsection (≈72 lines) | 516–588 |
| V1.2 dual-origin | end of §4, after "…never derived solely from the mutable current batch assignment." | `**Scope of the origin concept (clarification, 10 September 2026).**` paragraph | 176–192 |
| P6-2 consultant architecture | end of §13, after the P6-2F bullet | `> **Documentation amendment (10 September 2026) — "consultant origin" terminology.**` blockquote | 576–594 |
| PO register | after the P6-2C amendment bullet in the header | `- **P6-2D amendment (10 September 2026):**` bullet | 15–22 |
| PO register | D5 "Documented recommendation" bullet | `- **Note (10 September 2026):**` origin-value supersession note | 145–152 |
| PO register | D7 "Consequences" bullet | `- **P6-2D amendment (10 September 2026) — framing clarification:**` note | 202–211 |
| PO register | before `## Final Recommendation` | `## P6-2D Ratified PO Decision — 2026-09-10` section | 422–467 |

All amendments are **additive**: no existing sentence, table, routing statement,
decision or workflow design text was deleted or rewritten. Total added ≈ 200
documentation lines across four files.

## 6. Processing Model Clarification

The Blueprint §9 subsection now documents, in the authoritative architecture
document, that:

- CarbonTally has **four principal processing actors** — Organisation, Consultant,
  CarbonTally internal and Processing Entity — plus the system/automatic worker;
- **automatic vs manual is an independent dimension** (not an actor category), with
  an explicit actor/mode matrix: Organisation, Consultant and internal staff each
  participate in **both** modes where authorised; Processing Entities are a
  **manual** capacity;
- **Consultant = manual**, **Processing Entity = manual in the generic sense**,
  **Organisation = automatic** and **CarbonTally internal = automatic** must **not**
  be stated or implied;
- **PEs are additional controlled manual-processing capacity**, not the exclusive
  source of manual processing (preserving the existing §9 sentence);
- **input type** (PDF, CSV, XLS/XLSX, image) is independent of actor, mode and state;
- the **automatic → manual fallback** is an existing architectural/workflow pattern:
  automatic extraction/mapping → confidence/validation gates → success continues, or
  unresolved/insufficient-confidence results move to human correction/manual
  processing and then continue (CSV/Excel and PDF cases both described; no new states
  or capabilities invented);
- the **seven concepts** (actor, processing mode, input type, workflow state,
  processing origin, provenance, entitlement) are tabulated as distinct, with
  entitlement owned by the client organisation.

## 7. `processing_origin` Clarification

Stated in **both** the Blueprint §9 and the V1.2 §4 clarification:

> `processing_origin` identifies the **manual-processing capacity/control path**
> (CarbonTally internal vs Processing Entity). It is **not** actor identity and
> **not** processing mode.

Additionally recorded: the two values remain exactly `CARBONTALLY_INTERNAL` and
`PROCESSING_ENTITY`; the CHECK constraint and the origin→stage routing (`review` vs
`pe_review`) are unchanged; the human actor is recorded separately
(`extracted_by`/`qc_by`/`customer_reviewed_by`, audit `performed_by`, snapshots); and
**no actor-domain value is added** to `processing_origin`. The Blueprint's
pre-existing origin sentence ("including which CarbonTally team/member or Processing
Entity performed each relevant stage") now carries an adjacent clarification so it
cannot be read as origin = actor identity.

## 8. D7 Clarification

The register's D7 row now carries a framing note: D7 concerns **firm provenance for
consultant processing actions** (and, where the architecture places it under D7, the
explicit recording of **processing-mode provenance**). It must **not** be represented
through `processing_origin`; D7 **option (c)** ("extend the `processing_origin`
vocabulary") is **excluded** by the D7b withdrawal; **Status: PENDING PO DECISION**.
No schema and no column name is prescribed (as instructed).

## 9. D7b Withdrawal

Recorded in the register as an authoritative PO decision:

- **Decision Ref:** `PO-P6-2D-D7b-R-20260910` · **Status:** RATIFIED (PROPOSAL
  WITHDRAWAL) · **PO selection:** WITHDRAW / REJECT AS PROPOSED.
- **Reasons recorded:** origin already has an established meaning (manual-processing
  capacity/control path); it is not actor identity; it is not processing mode; adding
  `CONSULTANT` conflates distinct domain concepts (actor / firm / mode / channel /
  workflow responsibility); it would needlessly alter a CHECK-constrained,
  routing-driving vocabulary.
- **Implementation status (explicit):** **NOT IMPLEMENTED / NO CODE CHANGE REQUIRED
  FOR THIS DECISION** — and it must **not** be reported as implemented. The register
  also records the D5 supersession pointer so no live recommendation to add a
  consultant origin value remains in that document.

## 10. D6 / D7c Preservation

- **D6 (entitlement timing):** unchanged — no edit. The register's D6 row is
  untouched; the established model (client-organisation ownership, non-charging
  submission-time availability check, canonical approval-time check) is preserved
  exactly. No entitlement behaviour was touched.
- **D7c (no historical provenance backfill):** unchanged — no edit, no backfill
  performed, no migration created, no historical record modified. The new P6-2D
  decision entry notes that D7c remains **pending** and is unaffected by the
  withdrawal.

## 11. Post-Edit Consistency Review

Read-only searches over `docs/architecture/*.md` (and `docs/cline/*.md` for
awareness) for `processing_origin`, `CONSULTANT`, `automatic`, `manual`,
`processing mode`, `processing-mode`, `Processing Entity`, `manual-processing
capacity`, `provenance`, `consultant origin` / `consultant-origin`.

| Check | Result |
|---|---|
| Any document stating/implying `CONSULTANT = processing_origin` | **None remaining in the four amended documents** (register records the withdrawal; D5 carries the supersession note; the P6-2 architecture carries the terminology note) |
| Any document stating/implying `processing_origin = actor identity` | **None.** The Blueprint's loose sentence now carries an adjacent clarification; V1.2 §4 states the distinction explicitly; V1.2 §5's provenance table already separated *who extracted* (`extracted_by`) from *internal or PE* (`processing_origin`) |
| Any document stating/implying `processing_origin = processing mode` | **None.** Both amended documents state the opposite explicitly |
| Any document contradicting "automatic/manual is independent of actor identity" | **None found** (`grep` for "consultant … manual processing" and org/automatic equivalence returned no matches; P6-2C/WS4 hits concern automatic-only approval and origin immutability, both consistent) |
| `processing_origin` vocabulary elsewhere | Consistent and unchanged: V1.2 §4 CHECK constraint (two values), WS4 Gate 3/4/6 reports (immutability; origin + `entity_id`), `domain/processing_origin.py`, P6-2C contract (PE-origin guard) |
| Markdown/format validation | **No markdown-lint or docs-validation command exists in the repository**; the only doc tooling (`tools/documentation_generator`) targets API docs and is not applicable. Validation was by anchored diff review and heading/structure inspection |

## 12. Contradictions Found

**Residual (reported, NOT silently rewritten — per instruction):**

1. **`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`**
   - §5 (line ~130): "consultant-origin processing)" — descriptive, predates the
     clarified vocabulary.
   - **§22 (line ~415): "P6-2B-2 — Origin + CT-QC guard parity: consultant origin
     value and queue labelling"** — a **stale proposal statement** that reads as
     adding a consultant value to `processing_origin`. Superseded: what P6-2B-2
     actually delivered was **CT-QC guard parity and queue/label visibility**, not an
     origin value.
   - **Recommended follow-up (out of scope here):** a one-line cross-reference note
     mirroring the P6-2 amendment note. This is **not** an authority conflict — no
     document asserts that an origin value exists; it is stale proposal wording in a
     closed-gate architecture document.
2. **Historical evidence files (not authority)** still containing the withdrawn D7b
   proposal: `docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md`
   (D7-3 / checkpoint text) and
   `docs/cline/CARBONTALLY_P6_2B_1_CONSULTANT_REVIEW_IMPLEMENTATION_REPORT.md`
   (line ~155). These are point-in-time records; the PO decision supersedes them and
   they must **not** be rewritten. Recorded for traceability.
3. **Superseded Blueprint versions** (`…_V1.0/V1.1/V1.2.md`) predate V1.3 and were not
   amended (V1.3 is the architecture authority).

**No authority-vs-authority conflict was found.** (The D7b issue was a
proposal-vs-architecture conflict, resolved by the PO's withdrawal.)

## 13. Files Changed

| File | Change |
|---|---|
| `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | +`> **Clarification (10 September 2026)**` blockquote (l.510–514); +`### Processing model — dimensional clarification` subsection (l.516–588) |
| `docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` | +`**Scope of the origin concept (clarification, 10 September 2026).**` paragraph (l.176–192) |
| `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` | +terminology amendment blockquote (l.576–594) |
| `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | +header bullet (l.15–22); +D5 note (l.145–152); +D7 note (l.202–211); +`## P6-2D Ratified PO Decision — 2026-09-10` (l.422–467) |
| `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_DOCUMENTATION_AMENDMENT_REPORT.md` | **new** (this report) |
| `docs/cline/prompt-history/CT-P6-2D-MODEL-DOC-20260910-001.md` | **new** (durable task-history record) |

## 14. Files Not Changed

**No code, test, schema, migration, RLS, permission, capability, billing, frontend,
configuration, fixture or demo-data file was touched.** Specifically unchanged: all
`backend/**`, all `frontend/**`, `backend/tests/**`, `supabase/**`,
`docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`,
`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`
(residual item §12.1 — reported, not rewritten),
`docs/architecture/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md`,
all P6-2A/2B/2C implementation and verification reports, the reconciliation report
(`CARBONTALLY_P6_2_PROCESSING_MODEL_RECONCILIATION_REPORT.md`), and the pre-existing
working-tree change set.

## 15. Git State

| Point | Branch | HEAD | Working tree |
|---|---|---|---|
| Before (17:49) | `main` | `1639121` | 660 porcelain entries |
| After (18:05) | `main` | `1639121` | 661 porcelain entries — the four amended architecture documents were already **untracked** (`?? docs/architecture/…`) so their edits add no entry; the +1 over the pre-edit 660 is the new `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_DOCUMENTATION_AMENDMENT_REPORT.md` (the prompt-history file sits inside the already-untracked `prompt-history/` directory) |

`git diff` is unavailable for untracked files, so the amendment was verified by
**anchored review of the edited regions** (§5) and by `grep`-based consistency checks
(§11). **No unexpected modifications**; the pre-existing working tree was not
reverted, cleaned or committed. No commit, no push.

## 16. Evidence Limitations

1. No markdown linter / docs validator exists in the repository, so structural
   validation was by inspection (headings, table pipes, blockquote integrity) rather
   than by a tool.
2. The target documents are **untracked** in git, so no VCS diff can be produced;
   amendment scope is evidenced by the recorded line ranges and reviewer-verified
   content reads.
3. The consistency review was `grep`-based over `docs/`; unusually-phrased contradictions
   could evade keyword search. The targeted searches covered the terms the PO specified.
4. Residual stale wording remains in one non-target document (§12.1) and in historical
   reports (§12.2) because amending them was outside this task's authority — so the
   corpus is not yet fully uniform.
5. No runtime verification applies (documentation-only task; no executable behaviour
   changed).

## 17. Final Verdict

### `DOCUMENTATION AMENDMENT COMPLETE — ADDITIONAL CLARIFICATION REQUIRED`

The four required documents now accurately express the original processing model and
the D7b withdrawal (verdict-defining work complete). The residual clarification
required is the single stale "consultant origin value" wording in
`CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` §22 (§12.1), which
this task was instructed **not** to rewrite silently.

**Not claimed:** this is **not** implementation completion, **not** D7 implementation
and **not** D7b implementation. D7b is withdrawn and requires no code; D7 and D7c
remain pending PO decisions.

## 18. Stop-Condition Confirmation

**The task completed normally.** No stop condition (prompt §13) was triggered: no
implementation change was needed or made; no schema change was needed; no policy
decision was made by the agent (the PO's withdrawal was merely recorded); no
authority-vs-authority conflict was discovered; no unexpected working-tree change
appeared; and no concept was guessed.




