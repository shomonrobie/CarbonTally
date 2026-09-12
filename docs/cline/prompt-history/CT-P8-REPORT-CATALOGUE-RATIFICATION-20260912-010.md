# CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010

**Prompt ID:** `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010`
**Date:** 2026-09-12
**Task purpose:** Convert Phase 8 findings, recommendations and explicit PO decisions into a
formal decision register / product-and-report ratification that becomes the baseline for later
implementation.
**Type:** DOCUMENTATION / SPECIFICATION / GOVERNANCE ONLY. No implementation authorised.
**Task status:** `COMPLETED — RATIFICATION ONLY`

## Scope

Ratify, as a decision baseline: the V3 report catalogue and type/instance/version/artifact
distinction; assurance positioning; the Auditor / Assurance Reviewer boundary; the RBAC **+ scope**
report authorization model; system-controlled vs editable content; the report lifecycle; the
approval model; the frozen final PDF/artifact model; the four admin/management reporting surfaces;
canonical analytics/reporting architecture and anti-duplication; the Ask CarbonTally boundary; the
AI narrative boundary; legacy reporting disposition; and deferred/future capabilities.

**Hard boundary observed:** no application code, database, migration, RLS, API route, frontend,
report engine, PDF rendering, AI/LLM code, billing/entitlement logic or production change; no
push; no defect fixed (all recorded as future work).

## Repository State at Start

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `687c9711240c6b042d02482f1d258ec2b8ddc170` |
| Relation to origin | 6 commits ahead of `origin/main` (`9e13236…`), **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

## Authoritative Inputs Reviewed

| ID | Document | Contribution |
|---|---|---|
| S1 | `docs/architecture/CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` | Phase 8 capability matrix, gaps, P1–P31 |
| S2 | `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` | Lifecycle baseline, states, transitions, overlay, PDF/hash, schema Options A–D |
| S3 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | Architecture source of truth: §5 Actor Model, §13 Authorization, §14 RLS, §16 Ops/Admin separation |
| S4 | `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | PO-ratified sequencing; §0 ratification record; §10/§11 phase status; §13 current position; §18 open governance |
| S5 | `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | Canonical AI architecture (tiered personas, AssistantGateway, tool registry, provider abstraction) |
| S6 | `docs/architecture/CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` | Explicit non-claims; `not_assurance: true`; "AUDIT EVIDENCE READINESS"; no auditor role created |
| S7 | `docs/cline/prompt-history/CT-P7P8-ROLE-REPORT-CATALOGUE-20260912-002.md` | Prior role × report/analytics catalogue (Class A–G) |
| S8 | `AGENTS.md` | Operating constitution (authorization, evidence, RLS, no-authority-by-existence) |
| — | Current repository source | Verified implementation reality |

## What Was Ratified

### Catalogue and positioning
* **V3 catalogue = `annual` only** (12 sections). The "80–90 audit-ready reports" statement is
  **withdrawn** as non-authoritative.
* **Type / instance / version / artifact** distinction ratified as mandatory vocabulary.
* **Legacy labels** (`SECR`, `CSRD`, `ISSB`, `AUDITOR_EXCEL` + 6 generic) are **not** live V3
  types and are **not revived**; legacy surface **disposition DEFERRED**.
* **Assurance positioning** ratified: CarbonTally is **not** an auditor, verifier, assurance
  provider or certification body; it **supports** assurance with evidence.
* **Auditor / Assurance Reviewer boundary** ratified: may view/inspect (reports, versions,
  calculations, evidence, provenance, audit history), comment, request evidence, raise findings;
  must **not** edit calculations/factors/ledger/evidence/provenance/snapshots/system facts, and
  must **not** approve or finalize. External PDF/DOCX editing is **outside the system of record**;
  no auditor report editor is created.

### Authorization
* **RBAC + scope is mandatory**: RBAC decides *what actions*; scope decides *which* reports/data.
  **RBAC alone never grants unrestricted report access.**
* Every report operation is authorization-controlled (view/list/inspect/edit/comment/submit/
  request-changes/approve/revoke/finalize/download/artifact).
* **Server-side enforcement** is mandatory; the frontend is UX only.
* **RLS**: report tables must gain explicit RLS or a documented deliberate justification; no
  existing RLS weakened.
* Scope rules ratified for Customer (org), Consultant (ACTIVE grant only), PE (entity/portfolio),
  Auditor (explicitly assigned) and CarbonTally staff/admin (capability-based, no blanket
  privilege).

### Lifecycle, approval, artifact
* Lifecycle `GENERATE → DRAFT → EDIT → REVIEW → APPROVE → FINAL → FROZEN PDF` with six stored
  version states; `EDITED` is an event.
* **Approved/final versions immutable**; material post-approval changes create a **new version**
  requiring review/approval.
* **Approval roles**: Customer Owner + Customer Admin; Member/Viewer never; consultant and
  CarbonTally staff approval **PO-gated**.
* **Report approval is distinct** from PE/processing approvals; PE approval tables must not be
  repurposed.
* **Frozen final PDF** ratified with the **two-hash model** (canonical content hash for approval;
  PDF byte hash for the stored artifact).

### Surfaces and architecture
* **Four admin/management reporting surfaces** ratified as a capability family (CarbonTally Admin,
  Organization Admin, Consultant Admin, PE Admin), all reusing one canonical layer.
* **Anti-duplication**: one aggregation layer, one report engine, one export surface, one PDF
  renderer, one LLM abstraction, one evidence vocabulary, one authorization contract, one audit
  ledger; no data warehouse/derived summary tables.
* **Ask CarbonTally** ratified as a separate conversational domain from human↔human messaging,
  tool-mediated and authorization-scoped.
* **AI narrative** ratified as **candidate content only**, provider-abstracted, never required.

## Key Findings and Contradictions Reported

1. **Governance finding — Master Roadmap status is stale**: roadmap §0/§11/§14 say Phase 8 scope
   is undefined and "NOT AUTHORIZED", and §13 still reports Phase 6 as the current phase, while
   the PO has since authorised Phase 7 closure and the Phase 8 discovery → spec → ratification
   sequence. Recorded as **A-ROAD (PO DECISION REQUIRED)**; the roadmap was **not** amended.
2. **Potential contradiction, reconciled**: lifecycle spec §22.2 sets PE access to *customer report
   instances/versions* = **No**, while this task ratifies PE Admin **portfolio reporting**.
   Reconciled as consistent (portfolio management reporting vs customer report documents), with
   **A-PE** raised in case the PO intended otherwise.
3. **Phase 7 position vs Phase 8 auditor boundary**: Phase 7 explicitly created **no** auditor
   role/table and disclaims assurance; this task ratifies a **future** reviewer capability
   boundary while keeping the non-claim. No conflict, but the access model does not exist.
4. Defects recorded (not fixed): no RLS on report tables; report lifecycle entirely unaudited;
   `is_current` multiply-true; no approval/review/edit capability; PDF never stored and not
   byte-reproducible; frontend "Version" column always `v1`; `download_report` docstring drift;
   `usage_tracking.reports_generated` never incremented; `report_comments` dormant with no
   `comment_type` vocabulary; legacy surface undisposed.

## Files Created

* `docs/architecture/CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` (25 sections)
* `docs/cline/prompt-history/CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010.md` (this record)

## Files Modified

* **None.**

## Change Statements

```text
Code changes:            NONE
Database changes:        NONE
Migrations:              NONE
RLS changes:             NONE
API changes:             NONE
Frontend changes:        NONE
Report-engine changes:   NONE
PDF changes:             NONE
AI / LLM changes:        NONE
Billing changes:         NONE
Messaging changes:       NONE
Production changes:      NONE
Push:                    NONE
```

## Verification Performed

1. Both required documents confirmed to exist.
2. Only documentation files were created/changed by this task.
3. No application code modified.
4. No database changes.
5. No migrations created or modified.
6. No RLS changes.
7. No API/frontend changes.
8. No production changes.
9. Unrelated worktree changes preserved (counts restored exactly; selective staging only).
10. Ratification reviewed against S1 (Phase 8 discovery).
11. Ratification reviewed against S2 (Phase 8 reporting lifecycle specification).
12. Git status checked.
13. Exact starting HEAD recorded.
14. Exact ending HEAD recorded.
15. Nothing pushed.

## Final Git State

* Ending HEAD: recorded in the completion report.
* Commit: one documentation-only commit
  (`docs: ratify Phase 8 report catalogue, lifecycle, and access model`), 2 files.
* Push status: **NOT PUSHED**.
* Unrelated modified/untracked work: **PRESERVED** (208 modified / 52 untracked restored; no
  reset / clean / stash / checkout).

## Unresolved PO Decisions

**Carried forward (A1–A13)**: narrative allowlist; consultant/staff approval; review-gate and
one/two-step approval; approval revocation; comment visibility; draft deletion; change-request
blocking; retention/deletion; download auditing; staleness/data-as-of; finalization billing;
evidence drill-down in the final report; legacy live PDF route.

**New (A-PE, A-AUD, A-AUD2, A-LEG, A-RLS, A-ROAD, A-ASSUR, A-STAFF, A-COMMENT)**: PE access to
customer report documents; auditor assignment/granting model; reviewer finding record type; legacy
disposition and future framework report types; report-table RLS approach; Master Roadmap update;
assurance-readiness scoring; staff capabilities for report operations; comment visibility
granularity.

## Recommended Next Task

**Exactly one:** `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011` — **Phase 8 Open-Decision
Closure & Implementation Authorisation Package**: a short, PO-facing decision sheet that resolves
the open items (A1–A13, A-PE, A-AUD, A-AUD2, A-LEG, A-RLS, A-ROAD, A-ASSUR, A-STAFF, A-COMMENT)
and, if the PO elects to proceed, authorises **implementation step S1 only** (correctness fixes:
the `is_current` invariant, `current_version` in the list payload, docstring drift) — with no
schema, RLS, API or frontend work. It unblocks implementation without pre-empting any policy choice
and remains documentation-only unless the PO separately authorises S1 coding. **Not begun.**

*End of record.*
