# CarbonTally V3 — MASTER INDEX (UX)

| | |
|---|---|
| Document type | Master index for the CarbonTally V3 UX specification set |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | **CANONICAL** — this directory is the canonical OpenHands UX documentation set |
| Date | 2026-08-24 |

## 0. Canonical statements (binding)

- **This directory is the canonical OpenHands UX documentation set.**
  `docs/audit/openhands/ui-ux/` is the single authoritative home of the
  CarbonTally V3 UX specification (screens, workflows, interactions,
  design system, implementation matrix, reconciliation). The interim
  `MASTER_UX_REVIEW_PACKAGE/` subfolder was flattened into this directory.
- **The Product Owner Decision Register is authoritative elsewhere.**
  The register in this directory is a **reference copy**. The authoritative
  register is `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`.
  No competing, independently editable register is maintained here.
- **Current vs target implementation must remain distinguished.** Every
  document uses the implementation-status labels (IMPLEMENTED · PARTIALLY
  IMPLEMENTED · BACKEND READY / UI MISSING · UI READY / BACKEND MISSING ·
  DESIGN ONLY · PLANNED · BLOCKED · REQUIRES ENGINEERING DECISION). A missing
  feature is never rewritten as implemented.
- **Selected architecture:** Option B (workflow-first) + Option C
  (customer/onboarding/evidence) + Option A (Admin/control-plane).
- **D17** (organisation master data: Facilities, Locations, Assets, Vehicles,
  Suppliers) is included (decision register §19; screen inventory; workflow
  map; implementation matrix).
- **D19** (split-screen workbench with top workflow navigation and 40/60 ·
  50/50 · 60/40 presets) is included (decision register §21; ASCII designs;
  implementation matrix P0-1).
- **D21** (unified design system, incl. D21.1–D21.9) is included
  (`CARBONTALLY_V3_DESIGN_SYSTEM.md`).
- **AI Assistant** is included: `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`
  (public prototype + authenticated tiered model), governed by D16 — the
  assistant is never an alternative permission or workflow engine.
- **P0 implementation gaps** are identified in `UI_UX_IMPLEMENTATION_MATRIX.md`
  §1 (G-P0-1 … G-P0-9).
- **N1–N3 supplement D1–D21** (decision register §24–§26):
  - **N1 — Messaging Access and Communication Boundaries**: APPROVED / FROZEN
    (customer-org internal, consultant internal + active-client customers,
    Customer Support/Admin scoped support, PE Manager↔PE users + CarbonTally
    operational, no direct Customer↔PE chat — clarification via controlled
    workflow; RLS/API enforced, UI is not the boundary; assistant inherits
    the same permissions).
  - **N2 — Location Physical Data-Model Representation**: PO DIRECTION
    RESOLVED; ENGINEERING DECISION (no separate `locations` table required;
    dedicated table OR Facilities reuse, decided by engineering against the
    existing schema).
  - **N3 — Configurable Data Retention**: APPROVED PRODUCT MODEL;
    IMPLEMENTATION DETAIL REMAINS (configurable retention policies via
    Settings/Admin; server-side enforcement; no invented durations).
- **No PO product decision remains unresolved** for the UX baseline.
  Remaining open items are **engineering implementation decisions**
  (reconciliation report §33) and the AI assistant programme decisions
  (`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §13).

## 1. Purpose

This index is the top-level navigation for the authoritative CarbonTally V3 UX
specification. It provides the authority hierarchy, reading order, D1–D21
status, target architecture, role model, workflow model, master-data model,
split-screen decision, responsive strategy, design-system location, P0
priorities and the Cline implementation handoff.

## 2. Authority hierarchy

1. Product Owner Decision Register (D1–D21) — `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`
2. Explicit Product Owner decisions in the current task
3. Approved Master UX Recommendation / reconciliation — `MASTER_UX_RECOMMENDATION.md`
4. Approved UX/design documents (this directory)
5. Current application/database/API implementation
6. Earlier audits and historical reports
7. Older/superseded documents

## 3. Reading order

| Step | Document |
|---|---|
| 1 | `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (D1–D21) |
| 2 | `docs/CARBONTALLY_V3_REFERENCE_INDEX.md` (this set's index) |
| 3 | `MASTER_UX_DECISION_RECONCILIATION_REPORT.md` (full narrative target UX + reconciliation) |
| 4 | `MASTER_WORKFLOW_MAP.md` (state flows) |
| 5 | `MASTER_SCREEN_INVENTORY.md` (every screen) |
| 6 | `MASTER_UI_UX_ASCII_DESIGNS.md` (interaction designs) |
| 7 | `CARBONTALLY_V3_DESIGN_SYSTEM.md` (D21 rules) |
| 8 | `UI_UX_IMPLEMENTATION_MATRIX.md` (gaps, priorities, acceptance criteria) |
| 9 | `UI_UX_OPTION_A_ENTERPRISE.md` · `UI_UX_OPTION_B_WORKFLOW_FIRST.md` · `UI_UX_OPTION_C_MODERN_GUIDED.md` (historical options, preserved) |

## 4. D1–D21 status

All D1–D21 are **APPROVED / FROZEN**. See the decision register §2 for the
summary table and §3–§23 for the per-decision records.

## 5. Target architecture

**Selected:** Option B (workflow-first platform) **+** Option C (modern/guided
customer/onboarding/evidence surfaces) **+** Option A (enterprise/control-plane
for CarbonTally Admin). The three historical options are no longer unresolved
alternatives — they are composed as above.

## 6. Role model

- Customer org: owner / admin / member / viewer.
- Consultant firm: owner / manager / consultant / viewer.
- CarbonTally staff: operator / reviewer / qc_specialist / admin.
- Processing Entity staff: entity-scoped work-assignment access.
- CarbonTally Admin: platform administration (distinct from org admin, D4).

## 7. Workflow model

Upload → Classification → Extraction → Mapping → Validation → PE Review/QC →
CarbonTally QC → Calculation → Evidence → Customer Review → Customer Approval
→ Reporting. Plus assignment/clarification/correction/rejection/rework/issues/
billing/onboarding/AI escalation/admin configuration. Backend state model:
`backend/domain/partners.py` (ITEM_STATUSES, BATCH_STATUSES, WORKFLOW_STAGES).

## 8. Master-data model

Organisation → Locations → Facilities → {Assets, Vehicles}; Suppliers
org-scoped (D17). Facilities/Assets/Suppliers implemented; Locations (distinct)
and Vehicles = target surfaces with implementation gaps.

## 9. Split-screen decision

Mandatory for source+structured-data workflows (D19): top workflow navigation,
two panes, presets 40/60 · 50/50 · 60/40. PE no-download boundary preserved.

## 10. Responsive strategy

Desktop primary for processing; tablet adaptive; mobile monitoring + light
review (D20).

## 11. Design system

`CARBONTALLY_V3_DESIGN_SYSTEM.md` — one unified system (D21) across all
surfaces; built on the existing `v3.css`/`App.css` CarbonTally identity.

## 12. P0 priorities

From `UI_UX_IMPLEMENTATION_MATRIX.md` (P0 rows):

1. Secure extraction / document viewer (D19 workbench).
2. Customer Review & Approve UI (D2/D5).
3. Custom Factors UI (D9).
4. Operations issues triage (ADR-V3-009 issue surface).
5. Universal evidence trail UI (D33).
6. Approver-role implementation (D5).
7. Workflow-consistency fixes (statuses/navigation copy).
8. Responsive workbench (D20).
9. Design-system consistency (D21 token consolidation).

## 13. Cline implementation handoff

1. **Read first:** the decision register (D1–D21) — everything is frozen.
2. **Target UX:** `MASTER_UX_DECISION_RECONCILIATION_REPORT.md`.
3. **Workflows:** `MASTER_WORKFLOW_MAP.md` — reconcile with
   `backend/domain/partners.py` statuses before building.
4. **Screens:** `MASTER_SCREEN_INVENTORY.md` + `MASTER_UI_UX_ASCII_DESIGNS.md`.
5. **Design rules:** `CARBONTALLY_V3_DESIGN_SYSTEM.md` (do not invent a new
   visual identity; extend the `ct-`/v3 vocabulary).
6. **Gaps:** `UI_UX_IMPLEMENTATION_MATRIX.md` — implement P0 first; each row
   has acceptance criteria and engineering dependencies.
7. **Status discipline:** never claim a target feature as implemented without
   current code/API/database evidence. Use the implementation-status labels:
   IMPLEMENTED · PARTIALLY IMPLEMENTED · BACKEND READY / UI MISSING · UI READY
   / BACKEND MISSING · DESIGN ONLY · PLANNED · BLOCKED · REQUIRES ENGINEERING
   DECISION.

*End of master index. Documentation-only.*
