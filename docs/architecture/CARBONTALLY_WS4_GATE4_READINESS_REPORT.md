# CarbonTally WS4 — Gate 4 Definition + Readiness Report (Post-Gate-3 Reconciliation)

- **Date:** 4 September 2026
- **Nature:** Analysis / readiness only — **no code, SQL, RLS, API, UI, D38/D39/D40, workflow, architecture, migration or commit/push changes were made.**
- **Status recorded:** **Gate 3 = PASSED / ACCEPTED** (PO accepted; executed on the real stack with 63/63 checks, 0 failures).

---

## 1. Current WS4 Status

WS4 (Phase 5 final acceptance) is proceeding under the running acceptance log in `docs/architecture/CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md`, which records, in order: **Gate 1 — internal-origin terminal E2E: PASS**; **Gate 2 — PE-origin terminal E2E: PASS**; **Gate 3 — multi-PE / single-batch provenance fixture: previously BLOCKED (architectural conflict), resolved by the approved item-level assignment model (4A–4E) and now PASSED** (`docs/architecture/CARBONTALLY_WS4_GATE3_FINAL_ACCEPTANCE_REPORT.md`). The approved model is proven across DB/RLS, D38 service, HTTP/API, Operations UI, PE UI/access, real authenticated sessions, real PostgreSQL state, audit/provenance, cross-PE security, PE↔Internal reassignment, immutable processing origin and cleanup/baseline restoration. D38/D39/D40 are PO-approved; V1.2 is frozen.

The same running log records that the remaining intended acceptance work after the terminal gates is a **fixture-level human/automated provenance matrix (Gates 4–6)** and various verification/routine gates (a full backend regression re-run and frontend/responsive checks appear in the log under other gate numbers — see §7). WS5 and Phase 6 have not started.

## 2. Gate 3 Acceptance

**Gate 3 = PASSED / ACCEPTED.**

The accepted report (`CARBONTALLY_WS4_GATE3_FINAL_ACCEPTANCE_REPORT.md`) proves the canonical one-batch fixture (A→Alpha default, B→Beta item, C→Alpha item → reassigned Beta, D→Internal, plus default-fallback and UI-assigned items) with 63/63 checks across seed/initial HTTP+DB (22), mutation HTTP+DB (22) and real-browser passes (19), including full cleanup to the exact data baseline. Per the task authority rule, Gate 3 is **not re-run** and its evidence is **not repeated** in this report; it is treated as valid unless a future change invalidates it (see §8).

### Regression protection (task §8)
Gate 3 acceptance should remain valid: its evidence is unaffected by later WS4 *verification-only* gates. The following future changes would invalidate it and would require a targeted re-run of the affected evidence rather than the full suite: changes to the item-level assignment model or effective-assignment rule; the D38 ledger schema or mutation contracts; RLS/work_item_effective helpers; PE/internal processing authorization paths (`pe/items`, `pe/batches`, `ops/items/.../start`); origin immutability handling (`processing_origin`/`processing_entity_id`); the Operations/PE UI surfaces that display batch default / item assignment / effective processor; or resets/reseeds of the investor demo dataset. Gate 3 itself is **not** re-run in this analysis.

## 3. Original Gate 4 Definition

### Conflict identified
Two different gate-numbering schemes exist in the repository, and “Gate 4” has a different meaning in each:

| Scheme | Document | Gate 4 meaning | Status of that item |
| --- | --- | --- | --- |
| **WS4 UI browser report scheme** (historical, UI-centric continuation) | `CARBONTALLY_PHASE5_WS4_UI_BROWSER_IMPLEMENTATION_REPORT.md` | “D38→D40 browser proof” (notification inbox, unread state, target navigation) | Already **closed** in that continuation (“Closed in this continuation: Gate 1 (Operations D38 UI), Gate 4 (D38→D40 browser proof), Gate 6 (two-session verification)…”) |
| **WS4 final-acceptance scheme** (the numbering the PO has ratified for Gates 1–3) | `CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md` | First part of the **“Fixture-level human/automated provenance matrix (Gates 4–6)”** | **Not started** — the group was listed under “Gates still unexecuted this session” as item 5, with “mechanism assessment stands” |

### Authoritative source
For deciding the *next* WS4 gate after the PO-accepted Gate 3, the authoritative source is the **WS4 final-acceptance scheme** (`CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md`), because it is the numbering in which Gate 1 (internal terminal), Gate 2 (PE terminal) and Gate 3 (multi-PE provenance) were defined and accepted, and it is the running acceptance log the PO has ratified throughout 4A–4E. The historical UI-report scheme describes a different, already-closed sub-series and must not be substituted for the current Gate 4.

### What Gates 4–6 were originally intended to verify (preserved wording)
The preserved authoritative wording is a **group**: “Fixture-level human/automated provenance matrix (Gates 4–6) — mechanism assessment stands.” The supporting “Residual (non-blocking)” and assessment sections of the same log tie this group to:

- the **full human attribution matrix** (a complete ~11-action attribution over one continuous real run: actor, actor domain/entity, action, previous/next state, origin, timestamp — across claim/extract/map/validate/calculate/PE review/PE QC/CT QC/customer review/customer approval), which “was not compiled this session”; and
- the **automated-extraction provenance assessment** (deterministic/OCR machine attribution: actor/time exists; “Machine/provider/model/version attribution for automatic extraction is not currently represented in the audit contract”), classified **B/C — documented residual, not an acceptance blocker**; and
- **human-after-automation attribution** (“no evidence that saving/approving automated output rewrites the automated actor record; assessed at the mechanism level only”); and
- the V1.2 blueprint’s target provenance chain (§11 “Evidence and Provenance”: Source Document → Extracted Value → Mapped Activity → Emission Factor → Calculation → Immutable Snapshot → Review/QC → Approval), plus “processing-origin and stage-level provenance” requirements.

The repository does **not** preserve a verbatim per-gate itemization of Gate 4 vs Gate 5 vs Gate 6 within that group. Per the authority rule this is reported rather than invented (see §8/§10 for the smallest clarification).

## 4. Gate 4 Acceptance Criteria

**Draft (grounded in preserved wording; final wording requires PO ratification of the 4/5/6 split):** Gate 4 should prove, on a disposable fixture over a **continuous real run**, that the platform records complete **human processing provenance** and (where in scope) the **automated→human provenance transition**:

1. Every human action in the pipeline records actor identity, actor domain (CarbonTally internal staff / Processing Entity / customer), the action, the previous and next state, the item’s `processing_origin`/`processing_entity_id`, and a timestamp.
2. The ~11-action attribution chain is complete across an end-to-end run (e.g., claim → extract → map → validate → calculate → PE Review → PE QC → CT QC → customer review → customer approval) with **no unattributed state change**.
3. Assignment/reassignment attribution remains consistent with the accepted D38 ledger and `audit_trail` (no parallel audit mechanism).
4. Where automated extraction is exercised: the automated record (deterministic/OCR actor and timestamp) is preserved and is **not rewritten** when a human subsequently saves/approves the output; machine/provider/model/version attribution is reported as an explicit **documented residual** if not implemented (B/C, non-blocking), unless the PO expands scope.
5. Calculation provenance remains intact (immutable snapshot + source linkage), consistent with blueprint §11.

Components involved: manual-extraction items/batches, D38 ledger, `audit_trail`, processing-origin columns, calculation snapshots/evidence, PE and internal review/QC and customer-approval workflow endpoints, Operations and PE UI (attribution display), plus the automatic-processing job/extraction records if automated provenance is in scope.

## 5. Current Implementation Coverage

| Requirement area | Status | Notes |
| --- | --- | --- |
| Human actor attribution on D38/workflow actions | **Already implemented** (verified in Gates 1–3) | `audit_trail` rows with actor (`performed_by`), action type, `record_id`; D38 ledger `assigned_by`/`actor_domain`/`previous_*`/timestamps; origin immutability proven |
| ~11-action continuous attribution chain | **Verification only required** | Individual actions are implemented and each was verified in Gates 1–3; the single continuous “one fixture, full matrix” compilation is the remaining work |
| Automated-extraction machine provenance in the audit contract | **Requires implementation (small, bounded) IF ratified into Gates 4–6** | Deterministic/OCR actor/time + job records exist; machine/provider/model/version in the audit contract does not (documented B/C residual, previously classified non-blocking) |
| Human-after-automation preservation | **Verification only required** (mechanism exists) | Needs a real automated→human fixture run |
| Calculation snapshot/source provenance | **Already implemented** | Blueprint §11 chain supported by snapshots/source linkage from earlier WS acceptance |
| Attribution display (Ops/PE/customer UI) | **Already implemented** | Assignment/history/effective display accepted (Gates 1–3, WS4D) |

## 6. D40 Dependency

Classification: **D — not part of the current WS4 acceptance criteria** for the authoritative Gate 4 (with the nuance that any *remaining* D40 notification work is best treated as C — optional/future). Rationale:
- The authoritative Gate 4 (provenance matrix) does not require D40 notifications.
- Under the historical UI-report numbering, “Gate 4 (D38→D40 browser proof)” was a notification **UI proof** and was already **closed** in that sub-series; the current WS4 final-acceptance log records D40 inbox/event evidence as accepted.
- The accepted Gate 3 report lists “D40 entity-assignment notifications” as a separate remaining item; nothing in Gates 4–6 wording requires it, and it is **not** a blocker for Gate 4.
- No notification implementation work is recommended as part of Gate 4 (per instruction, none was performed).

## 7. Remaining WS4 Work

| Item | Classification | Notes |
| --- | --- | --- |
| Gate 4–6 fixture-level human/automated provenance matrix | **Gate-required** | Needs per-gate itemization ratified by the PO before execution (see §8) |
| Full backend regression suite on the post-Gate-3 tree (log “Gate 9”) | **WS4-required, verification-only, non-blocking** | Earlier closure runs recorded ~1,516 passed / 16 environmental failures (missing test-env credentials, DB-mismatch expectations); focused D38/D39/D40/PE suites remain green |
| Frontend suite + six-width responsive matrix on the PE Validate control (log “Gates 10/11”) | **WS4-required, verification-only** | Frontend suite is green (200 tests, WS4D run); the PE Validate control at all six widths was not independently re-matrixed |
| Full persona browser matrix on the current UI | **WS4-required, gate-independent, verification-only** (if the PO requires a clean re-run on the post-Gate-3 tree) | Role matrices were partially verified across Gates 1–3/WS4D; no new roles were introduced |
| D40 entity-assignment notifications | **Optional/future (C)** | Explicitly excluded from Gate 3; separate bounded task if required before final WS4 acceptance |
| Automated extraction machine provenance in the audit contract | **Future phase / optional** unless ratified into Gates 4–6 | Documented B/C residual; not an acceptance blocker in prior assessments |
| WS5 / Phase 6 | **Future phase** | Not started; out of WS4 scope |

## 8. Gate 4 Readiness

**Gate 4 readiness: NOT READY — definition clarification required before execution.**

Reason: the authoritative record defines Gates 4–6 only as a grouped “fixture-level human/automated provenance matrix” and does not preserve an itemized Gate-4 criterion list, so executing “Gate 4” today would require inventing a definition (forbidden by the authority rule). Two different “Gate 4” meanings also exist across documents (§3); the authoritative reading is the provenance-matrix one.

Conditional sub-verdicts (to be confirmed by the PO clarification):
- **Human-provenance portion: READY (verification only).** Existing implementation (D38 ledger, `audit_trail`, origin columns, workflow actions, snapshots) is in place; only a continuous one-fixture attribution matrix run is missing.
- **Automated machine-provenance portion (if ratified into Gate 4–6): IMPLEMENTATION REQUIRED** — a small, bounded workstream to represent machine/provider/model/version attribution for automatic extraction in the durable/audit contract (previously classified B/C, non-blocking).

## 9. Required Implementation Workstreams, if any

If the PO ratifies automated-extraction machine provenance into Gate 4–6, the smallest bounded workstream would be: **an additive automatic-processing provenance workstream** that (a) records the machine/provider/model/version on the durable extraction/job record and in an audit-visible attribution field, (b) keeps human saves/approvals distinct (no rewriting of the automated actor), and (c) adds the focused regression/allowed + machine-attribution assertions — **without** changing the D38 assignee vocabulary (per the reconciliation note that automation is an executor, never an “assignee”). No implementation is recommended for the human-provenance portion.

## 10. Recommended Next Action

**Exactly one recommended next action:** obtain PO ratification of the Gate 4–6 scope — confirm (a) the authoritative numbering (WS4 final-acceptance scheme) and (b) the per-gate itemization of the fixture-level provenance matrix (human attribution matrix / automated provenance / human-after-automation), then authorise the next bounded task to execute **Gate 4 as a verification-only human-provenance matrix run on a disposable fixture** (no feature implementation), with any ratified automated machine-provenance item handled as a separate small bounded implementation workstream before that sub-test runs.
