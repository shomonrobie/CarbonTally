# CarbonTally — Residual P6-2B D7b Origin-Wording Clarification Report

**Prompt Ref:** `CT-P6-2D-MODEL-DOC-20260910-002`
**Response Ref:** `CT-P6-2D-MODEL-DOC-20260910-002-R`
**Date/time:** 10 September 2026, approx. 18:02–18:20 local (Asia/Dhaka +0600)
**Task type:** DOCUMENTATION-ONLY CLARIFICATION — no code, schema, migration, RLS,
permission, capability, billing, frontend, workflow, test or data change.

---

## 1. Executive Summary

The residual live-looking stale proposal in
`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`
(a `CONSULTANT` value on `processing_origin`) has been **clarified in place with two
small additive notes** — one at the §21 design item that carried the recommendation,
one at the §22 workstream bullet that read as an instruction — plus a short inline
parenthetical where the descriptive phrase "consultant-origin processing" appears in §6.

Both notes state that the `CONSULTANT` `processing_origin` proposal is **withdrawn**
(`PO-P6-2D-D7b-R-20260910`), that `processing_origin` keeps its established meaning
(manual-processing capacity/control path: CarbonTally internal vs Processing Entity),
that a consultant is an **actor** and not an origin value, that automatic/manual
processing remains an **independent dimension**, that the authoritative definitions
are in Blueprint V1.3 / V1.2 dual-origin / the PO decision register, and that **no
P6-2B routing, QC or state-machine semantics change**.

No text was deleted; the historical recommendation and workstream wording are
preserved verbatim and merely annotated. Historical evidence documents were **not**
touched. Validation confirms no remaining wording anywhere instructs a future
implementation to add `CONSULTANT` to `processing_origin`.

**Verdict: `DOCUMENTATION CLARIFICATION COMPLETE — READY FOR PO RATIFICATION`.**

## 2. Stale Wording Found

| # | Location | Stale wording (preserved verbatim) | Why it read as live |
|---|---|---|---|
| 1 | §21, `P6-2B-P3 (design)`, lines ~404–407 | "(`CONSULTANT` value vs reuse `CARBONTALLY_INTERNAL`). Recommendation from the earlier P6-2 analysis: **a distinct `CONSULTANT` origin**; additive, affects only queues/labels/guard parity." | An open design item whose **recommendation** was to add a `CONSULTANT` origin value |
| 2 | §22, `P6-2B-2 — Origin + CT-QC guard parity`, line ~415 | "**consultant origin value** and queue labelling; customer-review guard parity." | A workstream bullet which, unannotated, instructs adding a consultant origin value |
| 3 | §6, item 4, line ~130 | "from `calculated` (or after **consultant-origin processing**)." | Ambiguous phrase readable as a `processing_origin` value |

Nothing else in the document proposes an origin value: line ~288
(`CONSULTANT_PERMISSIONS`) is the consultant **capability-map** identifier, and line
~318 ("immutable `processing_origin` set from batch carrier at claim/extract") is the
correct, unchanged V1.2 origin statement.

## 3. Location(s)

`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`
(closed-gate P6-2B architecture document; last modified 2026-09-06 before this task):
§6 item 4; §21 P6-2B-P3; §22 P6-2B-2.

## 4. Clarification Applied

1. **§21 P6-2B-P3** — appended a nested note: *"Clarification (10 September 2026) —
   this recommendation is superseded.* The proposed `CONSULTANT` **`processing_origin`
   value is withdrawn** by the Product Owner (`PO-P6-2D-D7b-R-20260910`, recorded in
   `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`). `processing_origin` retains its
   established meaning: the **manual-processing capacity/control path** (CarbonTally
   internal vs Processing Entity). It is **not** actor identity, **not** processing
   mode and **not** a consultant vocabulary. A consultant is an **actor**;
   automatic vs manual processing remains an **independent dimension**. Only the
   **queue/label visibility and CT-QC guard-parity** aspects of this item remain
   relevant. Authoritative current definitions: Blueprint V1.3 §9, V1.2 dual-origin
   §4, PO decision register."
2. **§22 P6-2B-2** — appended a nested note: *"Clarification (10 September 2026):*
   'consultant origin value' in this bullet is **withdrawn** — no `CONSULTANT` value
   is added to `processing_origin` … what remains applicable is **queue/label
   visibility** … plus **customer-review guard parity** … **No P6-2B routing, QC or
   state-machine semantics are changed by this clarification** … Authoritative
   definitions: Blueprint V1.3 §9, V1.2 dual-origin §4, PO decision register."
3. **§6 item 4** — appended an inline italic parenthetical: *("Consultant-origin
   processing" here means processing performed **by a consultant actor** — it is not
   a `processing_origin` value; see the clarification note in §22.)*

Both notes satisfy all six required statements (withdrawal; retained meaning;
consultant = actor not origin value; mode independence; authoritative references; no
routing change). **Two insertions + one parenthetical; zero deletions** (one stray
blank line before `## 22` was restored).

## 5. Historical Documents Preserved

Deliberately **not** modified (historical evidence):

- `docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md` (D7b as a
  plan item — historically accurate at its time).
- `docs/cline/CARBONTALLY_P6_2B_1_CONSULTANT_REVIEW_IMPLEMENTATION_REPORT.md` and the
  other P6-2B reports.
- All prompt-history records.
- The reconciliation report and the previous amendment report.
- Superseded Blueprint versions V1.0/V1.1/V1.2.

No historical document was judged to require a *correction* rather than historical
preservation — so no stop condition was triggered.

## 6. Consistency Validation

**P6-2B document (post-edit) — target-term scan** (`grep -n 'consultant origin\|consultant-origin\|CONSULTANT\|processing_origin\|queue labelling\|queue labeling'`):

| Occurrence | Status |
|---|---|
| l.130–132 "consultant-origin processing" | **Contextualised** by the inline note (means processing by a consultant actor, not an origin value) |
| l.288 `CONSULTANT_PERMISSIONS` | Consultant capability-map identifier — unrelated to origin; unchanged |
| l.318 "immutable `processing_origin` set from batch carrier at claim/extract" | Correct, consistent with V1.2 §4; unchanged |
| l.405–406 "a distinct `CONSULTANT` origin" | **Historical recommendation, preserved** and immediately marked **superseded/withdrawn** (l.408–420) |
| l.430 "consultant origin value and queue labelling" | **Historical workstream wording, preserved** and immediately marked **withdrawn** (l.432–443) |
| any "add `CONSULTANT` to `processing_origin`" instruction | **None remaining** (targeted grep returned no matches) |

**Authoritative documents (targeted consistency scan):** Blueprint V1.3 l.581 states
"`processing_origin` is not actor identity and is not processing mode"; V1.2 §4 keeps
the two-value vocabulary, immutability and routing; the register records
`PO-P6-2D-D7b-R-20260910` (withdrawal) plus the D5 supersession and D7 framing notes.
No contradiction was found between the clarified P6-2B document and those authorities.

**Historical scope:** the scan was deliberately limited to the P6-2B architecture
document plus the three current authoritative documents and the register; no broad
historical rewrite or re-scan-and-edit was performed.

## 7. Files Changed

| File | Change |
|---|---|
| `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` | +nested clarification note under §21 P6-2B-P3 (l.408–420); +nested clarification note under §22 P6-2B-2 (l.432–443); +inline parenthetical in §6 item 4 (l.130–132); restored one blank line before `## 22` |
| `docs/cline/CARBONTALLY_P6_2D_RESIDUAL_ORIGIN_WORDING_CLARIFICATION_REPORT.md` | **new** (this report) |
| `docs/cline/prompt-history/CT-P6-2D-MODEL-DOC-20260910-002.md` | **new** (durable task-history record) |

## 8. Files Unchanged

**No code, test, schema, migration, RLS, permission, capability, billing, frontend,
configuration, fixture or data file was touched** (verified by a repo-wide mtime scan
of `backend/`, `frontend/`, `supabase/` and `tools/` — zero hits). Also unchanged: the
three amended authoritative documents from the previous task, the PO register, the
roadmap, the P6-2C artefacts, the reconciliation and amendment reports, all P6-2B
implementation/verification reports, all prompt-history records, and the pre-existing
working-tree change set.

## 9. Git State

| Point | Branch | HEAD | Working tree |
|---|---|---|---|
| Before (18:02) | `main` | `1639121` | 661 porcelain entries |
| After (18:20) | `main` | `1639121` | 662 porcelain entries (+1 = this new report; the P6-2B architecture document was already untracked, and the prompt-history file sits inside the already-untracked `prompt-history/` directory) |

**No unexpected implementation files changed** (mtime scan clean). No commit, no push,
no revert, no cleanup of pre-existing changes.

## 10. Final Verdict

### `DOCUMENTATION CLARIFICATION COMPLETE — READY FOR PO RATIFICATION`

The stale authoritative wording has been clarified; no contradiction remains in the
P6-2B architecture document or between it and the current authoritative documents;
and no wording anywhere instructs a future implementation to add `CONSULTANT` to
`processing_origin`. No implementation, D7 implementation or D7b implementation is
claimed.

## 11. Stop-Condition Confirmation

**The task completed normally.** No stop condition was triggered: no architecture,
enum, CHECK constraint, routing, queue behaviour, permission, capability, RLS,
workflow, code, test, migration, billing or frontend change was needed or made; no
authority-vs-authority conflict was discovered; no historical document required a
correction rather than preservation; no unexpected implementation file changed; and
nothing was committed or pushed.

