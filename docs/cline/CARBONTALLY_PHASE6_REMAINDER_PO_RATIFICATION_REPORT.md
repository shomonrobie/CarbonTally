# CarbonTally — Phase-6 Remainder PO Ratification Report

**Prompt Ref:** `CT-PHASE6-PO-RAT-20260910-001`
**Response Ref:** `CT-PHASE6-PO-RAT-20260910-001-R`
**Date/time:** 10 September 2026, approx. 18:20–18:45 local (Asia/Dhaka +0600)
**Task type:** PRODUCT-OWNER DECISION RECORD — documentation only

---

## 1. Executive Summary

The Product Owner's ratification of the remaining Phase-6 decision package has been
recorded durably. Eleven decisions are now ratified policy, recorded in
`docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` in a new section
(`## P6 Remainder Ratified PO Decisions — 2026-09-10`), each stating its **PO policy
decision** separately from its **implementation status**.

| Ref | Subject | Selection |
|---|---|---|
| `PO-PHASE6-D6-R-20260910` | Entitlement timing | A |
| `PO-PHASE6-D7-R-20260910` | Firm + processing-mode provenance | A |
| `PO-PHASE6-D7b-R-20260910` | Consultant `processing_origin` value | **WITHDRAW / REJECT AS PROPOSED** (prior) |
| `PO-PHASE6-D7c-R-20260910` | Historical backfill | A |
| `PO-PHASE6-D8-20260910` | Consultant conversation model | B |
| `PO-PHASE6-D11-20260910` | Consultant lifecycle notifications | A |
| `PO-PHASE6-BILL-DEFER-20260910` | Automatic job-review billing | A (deferred) |
| `PO-PHASE6-D4-20260910` | PE ↔ Consultant handoff | A (out of scope) |
| `PO-PHASE6-F-ACC-20260910` | P6-2F acceptance standard | A |
| `PO-PHASE6-F-ENV-20260910` | P6-2F E2E environment | A |
| `PO-PHASE6-CAMPAIGN-20260910` | Unified Phase-6 remainder campaign | A |

**No implementation was performed.** This record establishes the decision baseline
(Checkpoint 0) from which the future implementation contract
(`CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001`, **not created here**) will be written.
The Master Roadmap was **not** modified; no code, schema, migration, RLS, billing,
frontend, test, fixture, demo-data or configuration file was touched.

**Verdict: `PO RATIFICATION RECORDED — READY FOR IMPLEMENTATION CONTRACT`**

## 2. PO Authority

The Product Owner is the final policy authority for CarbonTally. This task **records**
PO decisions; it does not make, reinterpret or extend them. Authority hierarchy used:
PO (policy) → Blueprint V1.3 (architecture) → Master Roadmap V1.0 (roadmap, unmodified)
→ phase-specific architecture documents → PO decision registers → implementation /
verification reports / prompt-history (evidence). The register entries created here are
authoritative **PO policy**, explicitly distinct from implementation status.

## 3. Authoritative Processing Model

Recorded as authoritative and preserved (not redefined) by this task:

**Actors** — four principal processing actors: **Organisation**, **Consultant**,
**CarbonTally Internal**, **Processing Entity**; a system/automatic worker may perform
machine processing.

**Processing mode** — independent of actor: **Automatic** / **Manual**. Consultant ≠
Manual; Organisation ≠ Automatic; CarbonTally Internal ≠ Automatic. Processing Entity is
*additional controlled manual-processing capacity*, and manual processing is **not**
exclusively performed by PEs.

**Input types** — PDF, CSV, XLS/XLSX, images; independent of actor, processing mode and
workflow state.

**Automatic → manual fallback** — an existing foundational CarbonTally pattern
(automatic extraction/mapping → confidence/validation gates → success continues; or
unresolved/low-confidence work → human correction, extraction or mapping → continue).
**Not** a new Phase-6 feature.

**Processing origin** — **not** actor identity and **not** processing mode; it identifies
the **manual-processing capacity/control path**: CarbonTally Internal vs Processing
Entity. Its CHECK constraint, immutability and routing semantics remain unchanged.

## 4. D6 Decision — Entitlement timing (`PO-PHASE6-D6-R-20260910`, **A**)

**Policy ratified:** non-charging submission preflight + canonical approval-time
enforcement. (1) consultant submission performs a **non-charging** entitlement
availability check; (2) submission **does not consume** entitlement; (3) final approval
performs the **canonical authoritative** check; (4) approval remains the authoritative
enforcement/consumption point; (5) entitlement remains owned by the **client
Organisation**; (6) processing **actor** and processing **mode** do not transfer
ownership. **Not** ratified: entitlement redesign, consultant/actor-owned entitlement, or
charging at submission.

**Implementation status:** **PRE-EXISTING** — the existing codebase already performs the
non-charging check at consultant submission and the canonical charge at customer
approval. No code change is required or made by this record.

## 5. D7 Decision — Firm + processing-mode provenance (`PO-PHASE6-D7-R-20260910`, **A**)

**Policy ratified:** preserve **durable firm provenance for consultant processing
actions**, while preserving **processing-mode provenance separately** where the existing
architecture requires it. Firm identity is captured **at action time**, derived
**server-side** from the authorised consultant/grant relationship, **never
actor-supplied**; historical provenance stays **stable** across membership/grant changes.
**Actor · firm · processing mode · processing origin · workflow state · entitlement must
remain distinct.**

**Explicit non-decisions:** no database field name prescribed; `processing_origin` must
**not** represent mode; Consultant must **not** be added to `processing_origin`; D7
option (c) (extending the origin vocabulary) remains **excluded**.

**Implementation status:** **NOT IMPLEMENTED** — the exact representation is deferred to
the implementation contract after code/schema inspection.

## 6. D7b — Prior Withdrawal (`PO-PHASE6-D7b-R-20260910`)

**Status: WITHDRAWN — NOT AN OPEN DECISION.** Previously ratified as **WITHDRAW /
REJECT AS PROPOSED** (recorded in `## P6-2D Ratified PO Decision — 2026-09-10` and
re-listed in the remainder table). Explicitly recorded as *not to be implemented*: no
`CONSULTANT` processing-origin value; no CHECK-constraint change; no origin vocabulary
expansion; no consultant-specific `review` / `pe_review` routing; no queue semantics
based on consultant-as-origin; no processing-origin reinterpretation.
**Implementation status: NOT IMPLEMENTED / NO CODE CHANGE REQUIRED.**

## 7. D7c Decision — Historical backfill (`PO-PHASE6-D7c-R-20260910`, **A**)

**Policy ratified:** **no historical provenance backfill** — do not infer missing firm
or mode provenance, do not fabricate it, leave historical records unchanged where
provenance was never captured, and apply new provenance **prospectively**. Applies to the
firm/mode provenance introduced under D7.
**Implementation status:** **NOT IMPLEMENTED** — no migration, no historical record
modification, and no backfill is authorised.

## 8. D8 Decision — Consultant conversation model (`PO-PHASE6-D8-20260910`, **B**)

**Policy ratified:** **reuse the existing conversation model.** No dedicated consultant
conversation kind unless later evidence demonstrates a concrete product/security
requirement the existing model cannot satisfy; consultant participation continues through
the existing authorisation/grant model; no unnecessary schema expansion; conversation
authorisation must not be weakened.
**Implementation status:** **PRE-EXISTING reuse model** (consultants already participate
via the active grant). **No new kind is authorised** ⇒ no schema change.

## 9. D11 Decision — Consultant lifecycle notifications (`PO-PHASE6-D11-20260910`, **A**)

**Policy ratified:** lifecycle notifications for consultant **accepted**, **submitted to
QC**, **QC outcome**, **customer decision** and **rework**, using deterministic
idempotent **event keys**, the **existing** idempotent notification infrastructure,
**server-side** recipient derivation from the **actual workflow relationship**, and no
data leakage across organisations, firms or unauthorised actors.
**Explicit non-decision:** exact event constants/keys and the recipient matrix are **not**
defined here — the implementation contract must derive them from the existing
architecture and code; no recipient identities are invented in this record.
**Implementation status:** **NOT IMPLEMENTED** (only the notification infrastructure
pre-exists).

## 10. Billing Decision — Automatic job-review billing (`PO-PHASE6-BILL-DEFER-20260910`, **A**)

**Policy ratified:** **remain deferred.** During P6-2D/P6-2E/P6-2F: no redesign of
automatic job-review billing; no change to current billing semantics; no new charge; no
removed charge; no resolution of the broader billing-policy question. Extends the
deferral already recorded in `PO-P6-2C-D3-20260910`.
**Status: DEFERRED — no change.** A future, separate PO billing-policy decision owns it.

## 11. D4 Scope Decision — PE ↔ Consultant handoff (`PO-PHASE6-D4-20260910`, **A**)

**Policy ratified:** **D4 remains outside Phase 6.** No explicit PE↔Consultant handoff
workflow and no new state transitions, assignment semantics or authorisation flows for
this purpose; existing workflows remain unchanged.
**Status: OUT OF SCOPE — no change.**

## 12. P6-2F Acceptance Decision (`PO-PHASE6-F-ACC-20260910`, **A**)

**Policy ratified:** full Phase-6 acceptance is required. P6-2F is the final Phase-6
UI/UX and E2E security acceptance gate, covering (as applicable): Organisation,
Consultant, Processing Entity and CarbonTally-Internal workflows; authentication;
authorisation; organisation isolation; consultant grant boundaries; capability
enforcement; CT-QC boundaries; processing-origin integrity; provenance; entitlement;
billing invariants; notification behaviour; UI workflows; negative security scenarios;
IDOR resistance; alternate-route resistance; actor-injection resistance;
replay/idempotency; E2E browser workflows; and the full regression suite.
**Hard rule:** P6-2F **cannot self-certify**; **mandatory independent verification** is
required and the final verdict must be **evidence-based**, not merely implementation
completion.
**Implementation status:** policy for a future gate — **NOT IMPLEMENTED**.

## 13. P6-2F Environment Decision (`PO-PHASE6-F-ENV-20260910`, **A**)

**Policy ratified:** dedicated, **isolated** E2E environment with **synthetic/test
data** — no production customer data; no destructive production operations; dedicated
test identities; representative Organisation/Consultant/PE/Internal roles; realistic
authentication and authorisation; RLS exercised where applicable; reproducible fixtures;
safe test billing/ledger behaviour; resettable data; security-negative tests may exercise
denied operations; no real customer data mutation.
**Hard rule:** production security must **not** be weakened to make E2E tests pass.
**Implementation status:** policy for a future gate — **NOT IMPLEMENTED**.

## 14. Unified Campaign Decision (`PO-PHASE6-CAMPAIGN-20260910`, **A**)

**Policy ratified:** one overall Phase-6 remainder campaign with **mandatory hard
internal checkpoints** — not one uninterrupted implementation session:

```text
CP0 PO ratification
 → P6-2D impl → focused tests → regression → evidence → INDEPENDENT VERIFICATION → STOP if failed
 → P6-2E impl → focused tests → regression → evidence → INDEPENDENT VERIFICATION → STOP if failed
 → P6-2F (FRESH session) → UI impl → E2E/security acceptance → full regression → STOP if failed
 → MANDATORY INDEPENDENT VERIFICATION → FINAL PHASE-6 ACCEPTANCE
```

P6-2F must run in a **fresh implementation session**; no checkpoint may be silently
skipped; failure blocks progression until resolved and independently verified.
**Implementation status:** **NOT IMPLEMENTED** — the campaign has not started; this
record is CP0 only.

## 15. Frozen P6-2C Invariants (must not be reopened)

Recorded verbatim in the register: `calculated → approved` remains
automatic-processing-only; consultant review claiming uses the existing canonical
`can_submit` resolution; consultant source claiming uses the existing canonical
`can_extract` resolution; `_STAGE_PERMISSION` remains the single stage-gating mapping;
approval remains organisation-admin controlled; billing remains after the applicable
approval guard; no new role/capability/permission is created by the P6 remainder unless
separately authorised; billing semantics remain unchanged unless separately authorised;
existing RLS/security boundaries remain unchanged.

## 16. Explicit Non-Decisions

Not authorised by this PO package: adding `CONSULTANT` to `processing_origin`;
redefining `processing_origin`; redesigning automatic processing, manual processing or
the automatic→manual fallback; changing P6-2C approval/review/source semantics; billing
redesign; PE↔Consultant handoff; **new roles or capabilities without a separate PO
decision**; RLS redesign; destructive migration; historical provenance
fabrication/backfill; demo-data redesign.

## 17. Implementation Boundaries

No implementation is authorised by this record. The only documentation changed was the
P6-2 PO Decision Register plus the two new `docs/cline/` artefacts. Backend, frontend,
tests, Supabase schema, migrations, RLS, auth, capabilities, permissions, billing
implementation, processing-workflow implementation, processing-origin implementation,
fixtures, demo data and configuration are **untouched**.

## 18. Dependencies

- **CP0 (this record)** is the precondition for the implementation contract.
- **P6-2D** depends on: D6 (policy ratified; behaviour pre-existing), D7 (provenance),
  D7c (no backfill), and the frozen P6-2C invariants.
- **P6-2E** depends on **P6-2D** (notification payloads carry firm/origin context) and on
  D11 (event vocabulary) and D8 (reuse — no schema).
- **P6-2F** depends on P6-2C + P6-2D + P6-2E, on the acceptance standard (F-ACC), the
  isolated environment (F-ENV), and a **fresh session**; its verdict depends on mandatory
  independent verification.
- **Not dependencies:** Phase 7/8; D4 (out of scope); automatic job-review billing
  (deferred); automatic-processing redesign.

## 19. Required Next Contract

A **separate, later task** must create the implementation contract (identifier
`CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001` or the finally approved identifier),
based on this ratified PO record plus the existing authoritative architecture. It must
define, at minimum: the D7 provenance representation (after code/schema inspection), the
D11 event constants and recipient matrix, the P6-2D/P6-2E/P6-2F scopes, the checkpoint
structure, security/workflow/authorization/billing/provenance/audit/RLS invariants, the
regression baseline, rollback/stop conditions, out-of-scope items and acceptance
criteria. **It is deliberately not created in this task.**

## 20. Risks

| # | Risk | Assessment / mitigation |
|---|---|---|
| R1 | The D7 policy being implemented by touching `processing_origin` | Explicitly excluded in the register (D7 non-decision + frozen D7b withdrawal) |
| R2 | Interpretation drift on the campaign checkpoints | The register records the exact checkpoint chain and the fresh-session rule for P6-2F |
| R3 | Treating D6's pre-existing behaviour as "newly implemented" | Implementation status explicitly recorded as PRE-EXISTING, no code change |
| R4 | D11 event vocabulary being invented during implementation | Register states the contract must derive keys/recipients from existing architecture; none invented here |
| R5 | Scope creep into billing redesign or D4 | Both explicitly deferred/out-of-scope with no change authorised |
| R6 | E2E work weakening production security or touching revenue data | F-ENV hard rule recorded (isolated env, synthetic data, no production mutation) |
| R7 | Future edits re-proposing a consultant origin value | Blueprint §9, V1.2 §4, the P6-2/P6-2B notes and this register all state the boundary |

## 21. Evidence Sources

Register: `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` (D1–D11 rows; Decision Table;
Cross-Dependencies; `## P6-2C Ratified PO Decisions`; `## P6-2D Ratified PO Decision`;
new `## P6 Remainder Ratified PO Decisions`). Model of record: Blueprint V1.3 §9
(*Processing model — dimensional clarification*); V1.2 dual-origin §4 (*Scope of the
origin concept*). Evidence chain: the Phase-6-remainder readiness analysis, the
processing-model reconciliation report, the documentation-amendment report, the residual
origin-wording clarification report, the P6-2C verification report, and the P6-2C RA/PO/
IMPL/IV prompt-history records. Reconciliation findings (D6 pre-existing; D7 gap; D8
reuse; D11 absent; PE manual-only; fallback implemented) were established from code
inspection and are summarised in the register entries.

## 22. Git State

| Point | Branch | HEAD | Working tree |
|---|---|---|---|
| Before (18:20) | `main` | `1639121` | 662 porcelain entries |
| After (18:45) | `main` | `1639121` | **663** porcelain entries (+1 = the new ratification report; the modified register was already untracked, and the prompt-history file sits inside the already-untracked `prompt-history/` directory) |

Unchanged in the working tree: the Master Roadmap (mtime 2026-09-10 15:10, i.e.
predating this task), all P6-2C/P6-2D artefacts, the Blueprint, V1.2, the P6-2/P6-2B
architecture documents, and all code/schema/test/configuration files. No commit, no push,
no revert.

## 23. Final Verdict

### `PO RATIFICATION RECORDED — READY FOR IMPLEMENTATION CONTRACT`

All eleven decisions are recorded consistently, with PO policy distinguished from
implementation status; no authority conflict remains; the roadmap is unmodified; and no
implementation was performed.

## 24. Stop-Condition Confirmation

**The task completed normally.** No stop condition was triggered: no implementation or
schema change was needed or made; no unexpected modification occurred; no document
outside the three permitted files was changed; no authority conflict was found; and no
decision was made or reinterpreted by the agent. **NO IMPLEMENTATION WAS PERFORMED.**



