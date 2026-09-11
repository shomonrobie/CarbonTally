# CarbonTally Master Project Roadmap V1.0

**Status:** RATIFIED / AUTHORITATIVE — PRODUCT OWNER RATIFIED (10 September 2026)
**Date (draft):** 10 September 2026 · **Date (ratified):** 10 September 2026
**Document type:** Master Project Roadmap (product governance)
**Architecture authority (unchanged):** `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
**Repository state at ratification:** branch `main`, HEAD `16391217103b98dcea520070c5a22c68f12fe607` (`1639121`), no commits made by this documentation task.

> This is the **authoritative product roadmap**, ratified by the Product Owner. It
> governs product phase names, phase ordering, high-level phase objectives,
> dependencies, roadmap status and implementation sequencing. It does **not**
> override the Final Architecture Blueprint and it creates no implementation work
> beyond the ratified Phase-6 sequence.

---

## 0. Product Owner Ratification Record

The Product Owner reviewed the `MASTER ROADMAP RECONSTRUCTION — COMPLETION REPORT`
and ratified the following decisions on **10 September 2026**:

| # | Ratified decision |
|---|---|
| 1 | **Phase 1 = UNRESOLVED** — no authoritative product Phase-1 artifact exists; no Phase-1 name or scope invented; this historical documentation gap **must not block** continuation of the current Phase 6 implementation sequence. |
| 2 | **Phase 7 — Auditor / Assurance** — official product-roadmap name. Detailed scope **NOT** defined; no Phase-7 implementation, architecture, roles, workflows, APIs, schema or UI authorized. Detailed design to be handled later as a separate PO-approved phase-design process. |
| 3 | **Phase 8 — Advanced Analytics** — official product-roadmap name. Same restrictions as Phase 7 (scope NOT defined; nothing authorized). |
| 4 | **Phase 6 sequence ratified:** `P6-2C → P6-2D → P6-2E → P6-2F` — not to be reordered. Current position: P6-2B **CLOSED** · P6-2C **NEXT** · P6-2D **REMAINING** · P6-2E **REMAINING** · **P6-2F = FINAL Phase-6 UI/UX + E2E security acceptance gate**. No Phase-7 or Phase-8 work may be inserted into Phase 6. |
| 5 | **Authority rules confirmed** — this roadmap governs product sequencing; `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` remains the architecture source of truth and is not replaced or overridden; phase-specific specifications govern their implementation gates; implementation reports describe what was implemented; independent verification reports establish what was verified. |
| 6 | **Legacy phase numbering** — only the Phase numbering defined by this Master Project Roadmap represents the official product implementation roadmap. Other Phase-N numbering in historical, technical, audit, migration, security or UX documents must not be interpreted as CarbonTally product phases. Those historical documents are **not** deleted or rewritten. |
| 7 | **Promotion** — the draft (`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0_DRAFT.md`) is promoted to this ratified `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`, preserving the complete evidence and history of the draft. |

**Document history / promotion record**

| Version | Status | Date | Note |
|---|---|---|---|
| V1.0 DRAFT | DRAFT — awaiting PO ratification | 2026-09-10 | `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0_DRAFT.md`; all content preserved in this ratified document |
| V1.0 | **RATIFIED / AUTHORITATIVE** | 2026-09-10 | This document (promoted from the draft; PO-ratified) |

Draft/final relationship is unambiguous: **this file is the single authoritative
roadmap.** The draft file was superseded by promotion; its complete content,
evidence index and legacy-numbering disambiguation are preserved here verbatim.

---

## 1. Document Authority

- This is the **Master Project Roadmap** for CarbonTally, **ratified by the
  Product Owner** (see §0).
- It is the **authoritative product sequencing document**: phase names, phase
  objectives, product dependencies, status and implementation order.
- It does **not** replace, downgrade or reinterpret the Final Architecture
  Blueprint, which remains the architecture source of truth.
- It does **not** erase or rename historical/technical phase numbering
  (see §15).
- Phase-specific documents continue to govern their own defined implementation
  gates; this roadmap governs sequencing and status, not architecture.


## 2. Authority and Precedence

Authority chain (ratified):

```text
Product Owner decisions
        ↓
Master Project Roadmap            (this document layer — RATIFIED / AUTHORITATIVE)
        ↓
Final Architecture Blueprint      (architecture source of truth)
        ↓
Phase-specific specifications     (phase / gate scope + stop conditions)
        ↓
Implementation reports            (what was actually implemented)
        ↓
Verification reports              (what was independently verified)
```

Clarifications:

- **Architecture** decisions remain governed by the Final Architecture Blueprint
  and its explicit frozen amendments. The roadmap does **not** override
  architecture.
- The **roadmap does not automatically become architecture**; a roadmap change
  that alters architecture requires an architecture decision and an updated
  blueprint version.
- Where an older document conflicts with the Final Architecture Blueprint, the
  blueprint's own §32 rule applies (blueprint wins for architecture; ratified PO
  policy wins where the blueprint does not explicitly decide; security
  invariants cannot be weakened; implementation reports describe what exists and
  do not override architecture; historical proposals remain history only).
- **Product Owner decisions** take precedence for product policy and roadmap
  decisions.

## 3. Product Roadmap Definition

In **this** document, a **Phase** means:

> a **product implementation phase** — a named, sequenced stage of building the
> CarbonTally product, with a product objective, an authoritative phase
> specification, an implementation status, and (where defined) gates and
> acceptance criteria.

A Phase is **not**:

- an audit/workstream numbering inside a technical document;
- a migration step of a past backend consolidation;
- a security-assessment or UX-analysis section;
- a QA-harness phase.

Only the Phase numbering defined in **this** Master Project Roadmap constitutes
the CarbonTally **product implementation roadmap** (see §15).

Phase status vocabulary used here: `COMPLETE` · `COMPLETE — VERIFIED` ·
`IN PROGRESS` · `NOT STARTED` · `DESIGN COMPLETE — AWAITING PO APPROVAL` ·
`DEFERRED` · `UNRESOLVED`.

## 4. Phase 1

**Result of investigation:**

```
UNRESOLVED — NO AUTHORITATIVE PRODUCT PHASE-1 ARTIFACT LOCATED
```

- No repository artifact was found that defines a **product** Phase 1 (name,
  objective, specification or acceptance criteria).
- Predecessor numbering exists only in unrelated lineages (e.g. V2.1 build
  "Phase 1 — Domain Layer + Core"; V3-consolidation "Phase 1 — Backend
  Inventory"; a read-only assessment prompt "PHASE 1 — READ-ONLY";
  Platform-Master audit "Phase 1 — Repository Discovery").
- Product Phase 2 (`CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md`) and the QA
  forensic triage reference a preceding phase, but **no product Phase-1
  artifact is named**.
- Per instruction, **no Phase 1 name or scope has been invented**.

**Status:** UNRESOLVED (documentation gap — see §18).

## 5. Phase 2

**Name:** Phase 2 — Product Requirement Completion (D–M domains)
**Authoritative source:** `docs/cline/CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md`
("CarbonTally V3 — Phase 2 (D–M) Requirement Completion Matrix"; baseline HEAD
`58285e6`; last updated 2026-08-30; status legend ✅ / 🟡 / ❌ / ⛔).

**Objective (as documented):** complete the product requirement domains
D–M — Communication (D), Consultant application (E), Processing Entity
application (F), Universal workspace UX (G), Scalable table system (H), Internal
operations queue (I), Organisation/master data (J), Retention (K), Search (L),
Error/UX quality (M).

**Evidence:** the completion matrix itself (per-requirement implementation,
runtime and test columns), plus the QA forensic triage
(`docs/cline/CARBONTALLY_QA_V1_2_FORENSIC_TRIAGE.md`) which explicitly
references "the previous Phase 2 completion report".

**Status:** COMPLETE (as documented in the matrix; residual 🟡/❌ rows remain
recorded *inside* that matrix and are not re-scoped here).

---

## 6. Phase 3

**Name:** Phase 3 — Runtime Stability & Fail-Closed Routing
**Authoritative source:** `docs/cline/CARBONTALLY_V3_PHASE3_RUNTIME_STABILITY_REPORT.md`
("Phase 3: Runtime Stability & Fail-Closed Routing (Completion Report)";
date 2026-08-31; source of truth = `docs/cline/CARBONTALLY_QA_V1_2_FORENSIC_TRIAGE.md`).

**Objective (as documented):** remove runtime instability and restore
server-authoritative, fail-closed post-login routing — specifically the backend
file-descriptor leak (P1-A), fail-closed post-login routing via a
server-authoritative context resolver (P1-B), and local Realtime restoration
(P3), with regression coverage and live verification.

**Evidence:** the Phase 3 completion report (root causes, remediation, live
verification) and the QA forensic triage it draws on.

**Status:** COMPLETE (completion report). Its checkpoint is
`16391217103b98dcea520070c5a22c68f12fe607` — which is also the **current
repository HEAD** (see §18, governance observation).

---

## 7. Phase 4 — Individual User Architecture

**Name:** Phase 4 — Individual User Architecture
**Authoritative sources:**
`docs/architecture/CARBONTALLY_PHASE4_INDIVIDUAL_USER_ARCHITECTURE_DESIGN.md`
and `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §33.1 (Individual User
Architecture — Design Gate).

**Objective (as documented):** resolve whether CarbonTally supports
individual/personal-user identity and workspaces, **as a design gate**, before
any implementation. The blueprint §33.1 states: *"The next project
implementation phase after V1.2 acceptance is Phase 4 — Individual User
Architecture. This phase is a design-before-implementation gate. It is not an
authorization to create an individual/personal workspace."* No individual
workspace, personal data store, personal subscription model or new
actor/authorization surface may be introduced before an explicit PO architecture
decision.

**Evidence:** the Phase-4 design document (candidate architectures A–D,
security/data-ownership/billing/onboarding analysis, §21 PO decisions required)
with document status:
`PHASE 4 DESIGN COMPLETE — AWAITING PRODUCT OWNER APPROVAL`.

**Status:** DESIGN COMPLETE — AWAITING PO APPROVAL (**design-before-
implementation gate**; implementation NOT started and NOT authorized).
Blueprint §33 lists "individual/personal-user workspace architecture" and
related items under "What This Blueprint Does Not Decide".

---

## 8. Phase 5 — D38 / D39 / D40

**Name:** Phase 5 — Work Management (D38), Conversations (D39),
Notifications (D40)
**Authoritative sources:**
`docs/architecture/CARBONTALLY_PHASE5_D38_D39_D40_PREIMPLEMENTATION_PLAN.md`;
`docs/architecture/CARBONTALLY_PHASE5_WS0_BASELINE_AND_RESUME_NOTES.md`;
`CARBONTALLY_PHASE5_WS1_D38_IMPLEMENTATION_REPORT.md`;
`CARBONTALLY_PHASE5_WS2_D39_IMPLEMENTATION_REPORT.md`;
`CARBONTALLY_PHASE5_WS3_D40_IMPLEMENTATION_REPORT.md`;
`CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md`;
`CARBONTALLY_PHASE5_WS4_UI_BROWSER_IMPLEMENTATION_REPORT.md`.

**Objective (as documented):** implement the D38 work-item assignment model,
D39 conversations/messaging and D40 notifications, with UI/browser
implementation and final acceptance.

**Evidence:** the WS0–WS4 workstream reports; the WS4 final acceptance report
records `WS4 FINAL ACCEPTANCE — GATE 1 PASS (3 SEP 2026) + GATE 2 PASS
(3 SEP 2026)`.

**Status:** IN PROGRESS / ACCEPTANCE PARTIAL (as documented). The WS4 final
acceptance report explicitly records remaining **execution gaps**, not
architecture gaps — terminal-state browser E2E for both origins (through
Customer Approval), the multi-PE batch/item provenance fixture, and a full
backend regression re-run in that session — and states: *"Do not declare WS4
complete. Authorize one further isolated closure run..."*. A subsequent WS4
resume/closing execution log is present in the same artifact.

**Next action:** PO decision on authorising the documented WS4 closure run
(recorded here, not actioned).

## 9. Phase 6 — Consultant Workflow

**Objective (as documented).** Make the Consultant a first-class operating
actor: consultant identity/membership and engagement relationships, scoped
client-organization access, consultant processing actions on the shared engines,
consultant review and submission to CarbonTally QC, and the correct boundaries
(consultants never perform CarbonTally QC or Customer Approval). Source:
`CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md` §1/§27 and
`CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` §1/§13.

**Authoritative specification paths**

| Artifact | Role |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md` | Phase-6 readiness; §27 workstreams **P6-0…P6-6**; §28 tests; §30 verdict |
| `docs/architecture/CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md` | P6-0 PO policy ratification (D-1…D-7); §14 sequence |
| `docs/architecture/CARBONTALLY_PHASE6_P0_1_COMMERCIAL_CONSULTANT_CLARIFICATION.md` | Phase-6 commercial clarification |
| `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` | P6-2 architecture; §13 sequence **P6-2A…P6-2F**; §14 verification plan |
| `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` | P6-2B architecture; §22 workstreams **P6-2B-1/-2/-3 → P6-2C…F** |
| `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | PO decisions D1–D11 and their P6-2x mapping |
| `docs/architecture/CARBONTALLY_P6_1B_CONSULTANT_MEMBERSHIP_WORKSPACE_AUTHORIZATION.md` | P6-1B membership/workspace authorization |
| `docs/architecture/CARBONTALLY_P6_BILL_0_…`, `CARBONTALLY_P6_BILL_1_…` | Consultant commercial/entitlement reconciliation + implementation |
| `docs/cline/CARBONTALLY_P6_1C_ENGAGEMENT_CONFIRMATION_REPORT.md` | P6-1C engagement confirmation |
| `docs/cline/CARBONTALLY_P6_2A_…`, `…P6_2A_R1_…`, `…P6_2B_1_…`, `…P6_2B_2_…`, `…P6_2B_3_…`, `…P6_2B_4_…` | Implementation/verification reports |

**Completed gates (verified against the named artifacts)**

| Gate | Name | Evidence verdict | State |
|---|---|---|---|
| P6-0 | Decision ratification package | `PHASE 6 POLICY RATIFIED — IMPLEMENTATION READY` | COMPLETE |
| P6-1B | Consultant membership/team/workspace authorization | implementation doc + suite | IMPLEMENTED (no independent verification artifact located) |
| P6-1C | Consultant engagement confirmation | implementation report | IMPLEMENTED (no independent verification artifact located) |
| P6-2A (+R1) | Consultant processing authorization contract | initial `P6-2A VERIFICATION FAILED — BLOCKING FINDINGS`; after R1 remediation `P6-2A RE-VERIFICATION PASSED — READY FOR PO ACCEPTANCE` | COMPLETE — VERIFIED |
| P6-2B-1 | Consultant Review | `P6-2B-1 VERIFICATION PASSED — READY FOR PO ACCEPTANCE` | COMPLETE — VERIFIED |
| P6-2B-2 | Consultant Submission | `P6-2B-2 VERIFICATION PASSED — READY FOR PO ACCEPTANCE` | COMPLETE — VERIFIED |
| P6-2B-3 | CarbonTally QC decision | `P6-2B-3 VERIFICATION FAILED — BLOCKING FINDINGS` (blocker discovered) | CLOSED THROUGH P6-2B-4 |
| P6-2B-4 | Mandatory CT-QC prerequisite for manual processing | implemented; independent verification PASSED (performed in-session; no verification artifact on disk) | IMPLEMENTED + VERIFIED / CLOSED |

**Remaining gates (sequencing preserved — do not reorder)**

| Order | Gate | Name (as documented) | State |
|---|---|---|---|
| 1 | **P6-2C** | Approval-boundary hardening (`calculated→approved` latent map) + workflow finalisation; D9 regression guards | NOT STARTED — **NEXT** |
| 2 | P6-2D | Entitlement availability at submit (D6) + consultant firm/origin provenance (D7) | NOT STARTED |
| 3 | P6-2E | D39 conversation kind (D8) + D40 notification vocabulary (D11) | NOT STARTED |
| 4 | P6-2F | `/consultant` processing UI (D19/D21) + E2E security acceptance | NOT STARTED — **FINAL PHASE 6 GATE** |

- **Next gate:** `P6-2C`.
- **Final Phase 6 acceptance gate:** `P6-2F` (readiness §27 P6-6: "Stop:
  acceptance report; no Phase 6 work continues beyond defined scope").
- No additional Phase-6 gates are created here. No Phase 7/8 work is inserted
  into Phase 6.

**Deferred items identified by authoritative Phase-6 documents**

| Item | Recorded deferral |
|---|---|
| Consultant firm/origin provenance + origin-specific queue labelling (D7) | deferred to P6-2D ("NOT implemented" in P6-2B-1/2/3 reports) |
| Processing-entitlement timing/availability at submit (D6) | deferred to P6-2D |
| D39 consultant conversation kind (D8) + D40 notification vocabulary (D11) | deferred to P6-2E |
| CT-QC rejection/rework hardening refinements beyond the canonical rework loop | deferred (future) |
| PE ↔ Consultant handoff (D4) | deferred / "missing by design"; register allows scoping out — PO decision |
| `/consultant` processing UI + E2E acceptance | P6-2F |
| Latent `calculated→approved` map entry | P6-2C |

**Explicitly not done here:** Phase 6 is **not** redesigned; its sequencing,
gate names and acceptance conditions are reproduced from the existing
authoritative documents only.

## 10. Phase 7 — Auditor / Assurance

```text
Product Owner roadmap decision:
Auditor / Assurance   (RATIFIED — official product-roadmap name)

Detailed scope:
NOT YET DEFINED

Status:
FUTURE — ROADMAP NAME RATIFIED; DETAILED SCOPE NOT DEFINED

Implementation:
NOT STARTED — NOT AUTHORIZED
```

- The name is **Product-Owner ratified** (§0); its detailed scope is **not yet
  defined** and nothing is authorized — no implementation, architecture, roles,
  workflows, APIs, schema or UI.
- No authoritative repository document was located that defines a **product**
  Phase 7 or the scope of "Auditor / Assurance"; the name-only authority comes
  from the Product Owner roadmap context.
- No features, gates, roles, workflows, reports, APIs, database changes or
  acceptance criteria have been invented.
- Detailed scope will be defined later through a **separate PO-approved Phase-7
  phase-design process**.
- Legacy documents using a different "Phase 7" numbering must not be used to
  infer this phase's scope (see §15).

## 11. Phase 8 — Advanced Analytics

```text
Product Owner roadmap decision:
Advanced Analytics   (RATIFIED — official product-roadmap name)

Detailed scope:
NOT YET DEFINED

Status:
FUTURE — ROADMAP NAME RATIFIED; DETAILED SCOPE NOT DEFINED

Implementation:
NOT STARTED — NOT AUTHORIZED
```

- The name is **Product-Owner ratified** (§0); its detailed scope is **not yet
  defined** and nothing is authorized — no implementation, architecture, roles,
  workflows, APIs, schema or UI.
- No authoritative repository document was located that defines a **product**
  Phase 8 or the scope of "Advanced Analytics"; the name-only authority comes
  from the Product Owner roadmap context.
- No features, gates, roles, workflows, reports, APIs, database changes or
  acceptance criteria have been invented.
- Detailed scope will be defined later through a **separate PO-approved Phase-8
  phase-design process**.
- Legacy documents using a different "Phase 8" numbering must not be used to
  infer this phase's scope (see §15).

## 12. Phase Dependencies

Confirmed product sequence (as established by the documents cited per phase):

```text
Phase 4  (Individual User Architecture — design gate)
   ↓
Phase 5  (D38 / D39 / D40)
   ↓
Phase 6  (Consultant Workflow)
   ↓
Phase 7  (Auditor / Assurance — name ratified; scope undefined)
   ↓
Phase 8  (Advanced Analytics — name ratified; scope undefined)
```

- Phase 5 → Phase 6 → Phase 7 → Phase 8 is the PO-stated product sequence.
- The Phase-4 **design gate** sits before implementation phases; its outcome is
  awaiting PO approval.
- **Phase 1** relationship is unresolved (§4) and is **not** inferred here.
- No dependencies beyond those supported by the cited documents are asserted.
- In particular, **Phase 7 / Phase 8 are not dependencies of remaining Phase 6
  gates** (P6-2C…P6-2F).

## 13. Current Project Position

```text
CURRENT PRODUCT PHASE:
Phase 6 — Consultant Workflow

CURRENT GATE:
P6-2B closed

NEXT GATE:
P6-2C

PHASE 6 FINAL ACCEPTANCE:
P6-2F
```

Verified against: readiness §27 (P6-0…P6-6), P6-2 §13 (P6-2A…P6-2F), P6-2B §22
(P6-2B-1/-2/-3 → P6-2C…F), and the per-gate implementation/verification reports
listed in §9. P6-2B-3's blocker was closed through P6-2B-4.

## 14. Phase Authority Map

| Phase | Name | Authoritative Source | Status | Next Action |
|---|---|---|---|---|
| 1 | *(unresolved)* | none located | UNRESOLVED — NO AUTHORITATIVE PRODUCT PHASE-1 ARTIFACT LOCATED (PO-ratified; does not block Phase 6) | none required — PO ratified as an accepted documentation gap |
| 2 | Product Requirement Completion (D–M) | `docs/cline/CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md` | COMPLETE (as documented) | none (residual rows recorded inside the matrix) |
| 3 | Runtime Stability & Fail-Closed Routing | `docs/cline/CARBONTALLY_V3_PHASE3_RUNTIME_STABILITY_REPORT.md` | COMPLETE | none |
| 4 | Individual User Architecture | `docs/architecture/CARBONTALLY_PHASE4_INDIVIDUAL_USER_ARCHITECTURE_DESIGN.md` + Blueprint §33.1 | DESIGN COMPLETE — AWAITING PO APPROVAL | PO decision on the §21 design options |
| 5 | D38 / D39 / D40 | `CARBONTALLY_PHASE5_*` plan + WS0–WS4 reports | IN PROGRESS / ACCEPTANCE PARTIAL (WS4 Gate 1 + Gate 2 PASS; documented execution gaps) | PO decision on the WS4 closure run |
| 6 | Consultant Workflow | `CARBONTALLY_PHASE6_*` + `CARBONTALLY_P6_*` artifacts | IN PROGRESS (P6-2B closed) | **P6-2C** |
| 7 | Auditor / Assurance | PO-ratified name (no repository artifact defines scope) | FUTURE — NAME RATIFIED; SCOPE NOT DEFINED | PO-approved Phase-7 phase-design process (separately authorized) |
| 8 | Advanced Analytics | PO-ratified name (no repository artifact defines scope) | FUTURE — NAME RATIFIED; SCOPE NOT DEFINED | PO-approved Phase-8 phase-design process (separately authorized) |

## 15. Legacy Phase Numbering Warning

The repository contains **multiple, mutually incompatible uses of "Phase N"**.
They are **not interchangeable** and are **not** part of this product roadmap:

| Lineage | Where it lives | What its "Phase 7 / Phase 8" means |
|---|---|---|
| Product implementation phases | **this document** | the only product roadmap numbering |
| V2.1 backend build (git commit phases) | `docs/cline/CarbonTally Backend v2.1 — …(Final Gate).md`, `# …Preparation Pack.md`, `docs/RECONSTRUCTED_TASK_HISTORY.md` | Phase 7 = Document Processing + AI; Phase 8 = Workflow Orchestrator |
| V3 backend consolidation phases | `docs/audit/cline/CARBONTALLY_V3_PHASE_6/7/8_REPORT.md`, `CarbonTally_V3_Backend_Migration_Phase_Records_v1.0.md` | Phase 7 = Test Migration / Consultant-Multi-client; Phase 8 = Integration Verification / Internal Ops–QC |
| Platform Master audit phases (1–16) | `docs/cline/CarbonTally_Platform_Processing_Architecture_Master_v1.md` §68–83 | Phase 7 = Backend/Service Role Audit; Phase 8 = Batch/Work Item Audit |
| Security-assessment phases | `docs/cline/CarbonTally Application Security Assessment.md` | Phase 7 = Security Headers/Logging; Phase 8 = Threat Model |
| Standalone-product migration phases (0–11) | `docs/standalone/MIGRATION_PLAN.md` | Phase 7 = AI gateway; Phase 8 = Generic example profile |
| OpenHands UX / AI-assistant phases | `docs/audit/openhands/**` | UX "Phase 7: reports/CSV-Excel/accessibility. Phase 8: legacy cleanup"; assistant "PHASE 7 — Admin assistant" |
| Gap-assessment implementation phases (1–6) | `docs/architecture/CARBONTALLY_BLUEPRINT_IMPLEMENTATION_GAP_ASSESSMENT.md` §16 | Phase 6 = legacy-route removal + PE privacy |

**Rule:**

> **Only the Phase numbering defined in the CarbonTally Master Project Roadmap
> constitutes the product implementation roadmap.** Historical, technical, audit,
> security, migration, QA and UX phase numbers must **not** be used to infer
> product roadmap status, scope or sequencing.

Historical documents are **not** renamed, deleted, merged or rewritten by this
roadmap; this section exists to **disambiguate**, not to erase history.

## 16. Change-Control Rule

> No Product Phase name, order, scope, dependency or status may be changed merely
> through implementation-agent inference.

A material roadmap change requires, in order:

1. a **Product Owner** decision;
2. an update to **this roadmap** (versioned);
3. the appropriate **phase/specification** update;
4. implementation **only after** the updated authority is established.

This applies equally to adding a phase, reordering gates, inserting future
phase work into the current phase, or redefining acceptance conditions.

## 17. Relationship to Final Architecture Blueprint

- Architecture source of truth (unchanged; not modified by this ratification):
  `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
  (`APPROVED — ARCHITECTURE FREEZE`, canonical version V3, blueprint version
  V1.3, purpose: "Single authoritative architecture source of truth for
  implementation").
- **Division of authority:**
  - **Master Project Roadmap (this layer)** = product sequencing, phase names,
    phase objectives, dependencies, status, implementation order.
  - **Final Architecture Blueprint** = architectural source of truth,
    architectural invariants, system shape, trust boundaries, technology
    architecture, security architecture, target architecture.
- The roadmap does **not** override the blueprint; the blueprint is **not**
  treated as a complete phase roadmap.
- Phase-specific documents govern their own defined implementation gates.
- PO ratification governs unresolved roadmap decisions.
- Any roadmap change that alters architecture additionally requires an
  architecture decision and an updated blueprint version (blueprint §32).

## 18. Open Governance Items

Recorded only — no solutions invented, nothing actioned:

1. **Phase 1 product-lineage gap** — no authoritative product Phase-1 artifact
   located (§4). **PO-ratified as UNRESOLVED**; does not block the current
   Phase-6 sequence.
2. **Phase 7 detailed scope** — undefined; the **name is PO-ratified** (§10).
3. **Phase 8 detailed scope** — undefined; the **name is PO-ratified** (§11).
4. **Phase 6 exit criteria** — no consolidated single artifact; functional exit
   is the P6-2F stop condition plus the P6-2 §14 verification plan.
5. **Verification artifacts missing on disk** — P6-2B-4 independent verification
   (performed in-session only); P6-1B and P6-1C have no independent verification
   report located.
6. **Phase 4 decision pending** — design complete; awaiting PO approval
   (blueprint §33.1 gate).
7. **Phase 5 acceptance residual** — WS4 Gate 1 + Gate 2 PASS with documented
   execution gaps; PO closure-run decision pending.
8. **Uncommitted roadmap execution** — the current repository HEAD is
   `16391217103b98dcea520070c5a22c68f12fe607`, which is also the Phase-3 report's
   checkpoint; all subsequent Phase 4/5/6 work is uncommitted. *(Governance
   observation only — no commit made by this task.)*
9. **Blueprint documentation hygiene** (a separate bounded doc job; not fixed
   here): §32 self-refers to "v1.2" while the header is V1.3; the §32 conflict
   list is duplicated; a §31.2 amendment block appears after §33.
10. **No designated roadmap home** — no `docs/project|governance|roadmap|handover`
    directory exists; this ratified roadmap is placed in `docs/architecture/`.

---

## Evidence Index (documents used to build this roadmap)

**Product phases:** `CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md`;
`CARBONTALLY_V3_PHASE3_RUNTIME_STABILITY_REPORT.md`;
`CARBONTALLY_QA_V1_2_FORENSIC_TRIAGE.md`;
`CARBONTALLY_PHASE4_INDIVIDUAL_USER_ARCHITECTURE_DESIGN.md`;
`CARBONTALLY_PHASE5_D38_D39_D40_PREIMPLEMENTATION_PLAN.md` + `…PHASE5_WS0…WS4…`;
`CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md`;
`CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md`;
`CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`;
`CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`;
`CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`;
`CARBONTALLY_P6_1B_CONSULTANT_MEMBERSHIP_WORKSPACE_AUTHORIZATION.md`.

**Architecture:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
(§30 current gates, §32 authority rule, §33/§33.1 what it does not decide +
Phase-4 design gate, §34 target state).

**Implementation / verification:** `docs/cline/CARBONTALLY_P6_1C_…`,
`…P6_2A_…`, `…P6_2A_R1_…`, `…P6_2B_1_…`, `…P6_2B_2_…`, `…P6_2B_3_…`,
`…P6_2B_4_…`.

**Legacy-lineage evidence (disambiguation only):**
`docs/audit/cline/CARBONTALLY_V3_PHASE_6/7/8_REPORT.md`,
`CarbonTally_V3_Backend_Migration_Phase_Records_v1.0.md`,
`CarbonTally_Platform_Processing_Architecture_Master_v1.md`,
`CarbonTally Application Security Assessment.md`,
`docs/standalone/MIGRATION_PLAN.md`, `docs/audit/openhands/**`,
`docs/RECONSTRUCTED_TASK_HISTORY.md`.

---

## Ratification Block (Product Owner — completed)

```
Roadmap:        CarbonTally Master Project Roadmap V1.0
Status:         RATIFIED / AUTHORITATIVE
Ratified by:    Product Owner            Date: 10 September 2026
Decision:       [x] RATIFIED AS-IS

Ratified points:
  Phase 1:                            UNRESOLVED (ratified; does not block Phase 6)
  Phase 7 (Auditor / Assurance):      name RATIFIED; detailed scope NOT defined
  Phase 8 (Advanced Analytics):       name RATIFIED; detailed scope NOT defined
  Phase 6 sequence P6-2C → D → E → F: RATIFIED (not to be reordered)
```

*End of ratified roadmap. This document is authoritative as of 10 September 2026.
No Phase-7 or Phase-8 scope is defined here; both require their own separately
authorized PO-approved phase-design process. The next authorized Phase-6 gate is
**P6-2C**; the final Phase-6 acceptance gate is **P6-2F**.*





