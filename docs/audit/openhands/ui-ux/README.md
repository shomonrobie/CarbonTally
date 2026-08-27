# CarbonTally V3 — MASTER UX REVIEW PACKAGE (README)

| | |
|---|---|
| Document type | Canonical OpenHands UX documentation directory (README) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | **CANONICAL / CONSOLIDATED** — final authoritative UX documentation set; pending Product Owner / independent review |
| Date | 2026-08-24 |
| Mode | **DOCUMENTATION-ONLY.** No application code, backend, Supabase, database, schema, migration, RLS, API, configuration, deployment, package files, tests or production data were modified. |

> **Consolidation notice (final cleanup):** this directory is the single
> canonical home of the authoritative CarbonTally V3 UX documentation. The
> interim `MASTER_UX_REVIEW_PACKAGE/` subfolder (previous task) was flattened
> into this directory; all its unique content was promoted here and its
> redundant copies removed. Duplicate/older-generation UX documents are not
> part of this directory. This README was previously the review-package
> README and now serves as the canonical directory README.

---

## A. Purpose of this package

This directory consolidates the complete CarbonTally V3 Master UX
Reconciliation deliverables so the Product Owner (and any independent
reviewer) can inspect the whole UX package in one place. It contains:

- the product decision baseline **D1–D21** (frozen) plus **N1–N3**
  (approved; register §24–§26) — labelled reference copy; authoritative
  source remains `docs/ChatGPT/`,
- the AI Assistant architecture (public prototype + authenticated tiered
  model) as part of the authoritative set,
- the reconciled target-UX specification (screens, workflows, interactions),
- the implementation gap matrix (P0/P1/P2/P3) with engineering dependencies,
- the unified design system specification (D21 + D21.1–D21.9),
- the final reconciliation report,
- a small set of supporting evidence documents (with source paths in §L),
- integrity manifests.

This package is a **design/reconciliation authority, not a claim that all
target UX already exists in production.** Every document distinguishes
CURRENT IMPLEMENTATION from TARGET UX and labels gaps accordingly.

## B. Authority hierarchy

1. Product Owner Decision Register (D1–D21) — authoritative source:
   `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`
   (the copy in this package is a labelled reference copy only).
2. Explicit Product Owner decisions in the current task.
3. Approved Master UX Recommendation / reconciliation
   (`MASTER_UX_RECOMMENDATION.md`).
4. Approved UX/design documents (this package / `docs/audit/openhands/ui-ux/`).
5. Current application / database / API implementation.
6. Earlier audits and historical reports.
7. Older / superseded documents.

An older document never overrides a newer explicit Product Owner decision.

## C. Recommended reading order

1. `README.md` (this file).
2. `CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (D1–D21, frozen).
3. `MASTER_UX_DECISION_RECONCILIATION_REPORT.md` (full target-UX narrative).
4. `MASTER_INDEX.md` (doc map + reading order + P0 priorities).
5. `MASTER_WORKFLOW_MAP.md` (state flows).
6. `MASTER_SCREEN_INVENTORY.md` (every screen).
7. `MASTER_UI_UX_ASCII_DESIGNS.md` (interaction designs).
8. `CARBONTALLY_V3_DESIGN_SYSTEM.md` (visual/component rules).
9. `UI_UX_IMPLEMENTATION_MATRIX.md` (gaps + acceptance criteria).
10. `UI_UX_OPTION_A/B/C_*.md` (historical options, preserved).
11. `supporting-evidence/` (on demand).

## D. Which document answers which question

| Question | Document |
|---|---|
| What are the frozen product decisions? | `CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` |
| What is the target UX overall? | `MASTER_UX_DECISION_RECONCILIATION_REPORT.md` |
| How do I navigate the doc set? | `MASTER_INDEX.md` |
| Who can do what? | `MASTER_UX_DECISION_RECONCILIATION_REPORT.md` §28 + `supporting-evidence/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` |
| Where do users navigate? | `MASTER_SCREEN_INVENTORY.md` |
| How does processing work? | `MASTER_WORKFLOW_MAP.md` |
| How does the split-screen workbench behave? | `MASTER_UI_UX_ASCII_DESIGNS.md` |
| How do statuses appear? | `CARBONTALLY_V3_DESIGN_SYSTEM.md` §5 |
| How does mobile behave? | `CARBONTALLY_V3_DESIGN_SYSTEM.md` §9 + ASCII designs |
| What is implemented / missing? | `UI_UX_IMPLEMENTATION_MATRIX.md` |
| What are the acceptance criteria? | `UI_UX_IMPLEMENTATION_MATRIX.md` |
| What depends on backend/API/database/security? | `UI_UX_IMPLEMENTATION_MATRIX.md` (per-row dependencies) |
| What are the design-system rules? | `CARBONTALLY_V3_DESIGN_SYSTEM.md` |
| How is evidence traced? | `supporting-evidence/CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md` |
| What is the vocabulary/status terminology? | `supporting-evidence/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` |
| What is the AI Assistant architecture? | `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` |
| What can the public assistant claim? | `supporting-evidence/CARBONTALLY_V3_CUSTOMER_FAQ.md` + `supporting-evidence/CARBONTALLY_V3_FAQ_CAPABILITY_MATRIX.md` |
| What authenticated UX do assistant phases 3–7 integrate into? | `supporting-evidence/CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md` |

## E. D1–D21 status

**All D1–D21 = APPROVED / FROZEN.** No decision remains marked unresolved; no
decision was re-opened or re-numbered. See the decision register for the
per-decision records (Decision / Status / Rationale / UX consequence /
Implementation consequence / Dependencies / Historical reference).

**N1–N3 supplement D1–D21** (register §24–§26): N1 Messaging access
(APPROVED / FROZEN), N2 Locations physical representation (PO DIRECTION
RESOLVED; engineering decision), N3 Configurable retention (APPROVED PRODUCT
MODEL; implementation detail remains). No PO product decision remains
unresolved for the UX baseline.

## F. Selected UX architecture

**Option B (workflow-first) as the platform + Option C (modern/guided) for
customer/onboarding/evidence surfaces + Option A (enterprise/control-plane)
for CarbonTally Admin.** Processing workbenches use a split-screen layout with
**top workflow navigation** (D19); the whole product uses **one unified design
system** (D21) built on the existing CarbonTally visual identity.

## G. P0 implementation gaps

From `UI_UX_IMPLEMENTATION_MATRIX.md` §1 (P0):

1. G-P0-1 Secure extraction / document viewer workbench (top workflow nav,
   split panes, 40/60·50/50·60/40 presets, confidence, source↔field links,
   autosave, lock states).
2. G-P0-2 Customer Review & Approve UI.
3. G-P0-3 Custom Factors UI.
4. G-P0-4 Operations issues triage.
5. G-P0-5 Universal evidence trail UI.
6. G-P0-6 Approver-role implementation.
7. G-P0-7 Workflow-consistency fixes (nav labels, status vocabulary).
8. G-P0-8 Responsive workbench (tray-based mobile/tablet).
9. G-P0-9 Design-system token consolidation.

Each row includes current implementation, DB/API/FE support, engineering
dependencies, acceptance criteria and PO decision dependency.

## H. AI Assistant relationship to the master UX

The AI Assistant architecture is an authoritative member of this set:
**`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`** (public prototype +
authenticated tiered model; source path recorded in §L). It is governed by
**D16 (AI Provider / AI Governance)** and covered in:

- `CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` §18 (D16);
- `MASTER_UX_DECISION_RECONCILIATION_REPORT.md` §25 (AI Assistant UX);
- `MASTER_WORKFLOW_MAP.md` §11 (AI assistance in workflows);
- `CARBONTALLY_V3_DESIGN_SYSTEM.md` (confidence indicators, §7).

The architecture preserves the required three-tier distinction:

1. **PUBLIC ASSISTANT** — public knowledge only (approved customer FAQ);
   deterministic prototype, no data access.
2. **AUTHENTICATED ROLE-SCOPED ASSISTANT** — customer/consultant/PE/staff/
   admin personas, each scoped to the caller's own authorised data (one
   active client for consultants; assigned work only for PE; staff role
   permissions; admin-only tools).
3. **NORMAL CARBONTALLY WORKFLOWS** — the assistant is a front-end over
   existing authorization, never an alternative permission or workflow
   engine; every authenticated tool call goes through the same API/RLS path
   as the UI, and state-changing actions stay inside the normal workflow
   approval gates.

Summary: AI may assist navigation, explanation, contextual help, document
assistance, extraction suggestions, workflow guidance. AI must NOT be
authoritative for calculations, factor selection, evidence, approval,
security, organisation boundaries or compliance certification. Human review
and server-authoritative business rules remain authoritative.

## I. Product Owner decisions (N1–N3) — now approved

The three items previously flagged as NEW PO DECISION REQUIRED have been
**reviewed and approved by the Product Owner** and are recorded in the
decision register §24–§26 (and reflected in this directory's register
reference copy):

| # | Decision | Status |
|---|---|---|
| N1 | **Messaging Access and Communication Boundaries** — customer-org internal; consultant internal + active-client customers; Customer Support/Admin scoped support; PE Manager↔PE users + CarbonTally operational; **no direct Customer↔PE chat** (controlled clarification workflow); RLS/API enforced, UI is not the boundary; assistant inherits the same permissions. | **APPROVED / FROZEN** |
| N2 | **Location Physical Data-Model Representation** — Locations stays a first-class D17 concept; no separate physical `locations` table is required; dedicated table OR Facilities reuse is an **engineering decision** against the existing schema. | **PO DIRECTION RESOLVED; ENGINEERING DECISION** |
| N3 | **Configurable Data Retention** — retention is configurable via Settings/Admin control plane; no invented durations; server-side enforcement. | **APPROVED PRODUCT MODEL; IMPLEMENTATION DETAIL REMAINS** |

No PO product decision remains unresolved for the UX baseline. Remaining open
items are **engineering implementation decisions** (reconciliation report
§33) and AI assistant programme decisions
(`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §13).

## J. Current implementation vs target state

- The package labels every deliverable with implementation-status vocabulary:
  IMPLEMENTED · PARTIALLY IMPLEMENTED · BACKEND READY / UI MISSING · UI READY
  / BACKEND MISSING · DESIGN ONLY · PLANNED · BLOCKED · REQUIRES ENGINEERING
  DECISION.
- Missing features are never rewritten as implemented. Known gaps (e.g.
  Customer Review & Approve UI, Custom Factors UI, Vehicles, distinct
  Locations, audit console, chat RLS) are recorded as gaps with engineering
  dependencies.
- The live application runs some uncommitted public-site changes; this is
  noted in the reconciliation report but never overrides the frozen decisions.

## K. Known limitations of the reconciliation

1. **Authenticated live UX inspection** was performed via read-only API
   probes with minted local demo tokens, not a browser session: the running
   frontend targets the hosted Supabase project, so local demo logins are not
   possible through the browser UI. Public pages were inspected in the
   browser.
2. **Canonical repo carries an older document generation.** The canonical
   repo (`/home/shomonrobie/carbon_tally`) currently contains uncommitted,
   older-generation UX documents at the same relative paths (e.g. the
   pre-consolidation `docs/audit/openhands/ui-ux/` "REGENERATION 2" set and
   the 26-Aug decision register under `docs/ChatGPT/`). Those were **not**
   used as sources and **not** modified; this directory (the consolidated
   set) supersedes them when merged.
3. **Live vs committed baseline:** the live app includes uncommitted
   public-site changes (Platform/Services/Processing/Consultants/Pricing/
   Contact pages, GBP pricing). The committed baseline remains the primary
   implementation evidence.
4. **Responsive verification** is limited (D28 F6): true phone-width capture
   was not fully exercised.
5. **Entity-staff demo identity** does not persist (a transient fixture was
   used in prior work); entity workspace evidence is from code + prior audit
   captures.
6. **Chat** could not be exercised end-to-end because current RLS blocks it;
   N1 now defines the messaging access model, so the remaining work is
   engineering implementation of the conversation RLS/API (N1-F), not a
   product decision.
7. **AI Assistant** has no production UI surface in the current
   implementation; the public prototype exists in the OHD `website_candidate`
   export and the architecture is specified (this directory), with the
   extraction suggestion engine present in the backend.

## L. Exact source path of every copied document

| File in package | Source path |
|---|---|
| `CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (reference copy, labelled) | `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` |
| `MASTER_INDEX.md` | `docs/audit/openhands/ui-ux/MASTER_INDEX.md` |
| `MASTER_SCREEN_INVENTORY.md` | `docs/audit/openhands/ui-ux/MASTER_SCREEN_INVENTORY.md` |
| `MASTER_WORKFLOW_MAP.md` | `docs/audit/openhands/ui-ux/MASTER_WORKFLOW_MAP.md` |
| `MASTER_UI_UX_ASCII_DESIGNS.md` | `docs/audit/openhands/ui-ux/MASTER_UI_UX_ASCII_DESIGNS.md` |
| `UI_UX_OPTION_A_ENTERPRISE.md` | `docs/audit/openhands/ui-ux/UI_UX_OPTION_A_ENTERPRISE.md` |
| `UI_UX_OPTION_B_WORKFLOW_FIRST.md` | `docs/audit/openhands/ui-ux/UI_UX_OPTION_B_WORKFLOW_FIRST.md` |
| `UI_UX_OPTION_C_MODERN_GUIDED.md` | `docs/audit/openhands/ui-ux/UI_UX_OPTION_C_MODERN_GUIDED.md` |
| `MASTER_UX_RECOMMENDATION.md` | `docs/audit/openhands/ui-ux/MASTER_UX_RECOMMENDATION.md` |
| `UI_UX_IMPLEMENTATION_MATRIX.md` | `docs/audit/openhands/ui-ux/UI_UX_IMPLEMENTATION_MATRIX.md` |
| `CARBONTALLY_V3_DESIGN_SYSTEM.md` | `docs/audit/openhands/ui-ux/CARBONTALLY_V3_DESIGN_SYSTEM.md` |
| `MASTER_UX_DECISION_RECONCILIATION_REPORT.md` | `docs/audit/openhands/ui-ux/MASTER_UX_DECISION_RECONCILIATION_REPORT.md` |
| `UI_UX_DELIVERABLE_MANIFEST.sha256` | `docs/audit/openhands/ui-ux/UI_UX_DELIVERABLE_MANIFEST.sha256` |
| `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` |
| `supporting-evidence/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` |
| `supporting-evidence/CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md` | `docs/architecture/CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md` |
| `supporting-evidence/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` | `docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` |
| `supporting-evidence/CARBONTALLY_V3_CUSTOMER_FAQ.md` | `docs/audit/openhands/CARBONTALLY_V3_CUSTOMER_FAQ.md` |
| `supporting-evidence/CARBONTALLY_V3_FAQ_CAPABILITY_MATRIX.md` | `docs/audit/openhands/CARBONTALLY_V3_FAQ_CAPABILITY_MATRIX.md` |
| `supporting-evidence/CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md` | `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md` |

All copies are verbatim except: the decision-register copy, which carries a
"REFERENCE COPY" header label (§1 of the copy); and the AI Assistant
architecture copy, which carries one N1 messaging addendum in its §10.1
security model (the canonical source in `docs/audit/openhands/` remains
byte-identical to its original). The authoritative register remains
`docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` and is
untouched. The FAQ / capability-matrix / blueprint copies are byte-identical
to their canonical sources in `docs/audit/openhands/`.

## M. Manifests (scope)

| Manifest | Scope | Verify with |
|---|---|---|
| `UI_UX_DELIVERABLE_MANIFEST.sha256` | The 13 reconciliation-phase deliverables (11 master UX documents + the authoritative register + the reference index), hashed from the repo root. Phase record. | `sha256sum -c UI_UX_DELIVERABLE_MANIFEST.sha256` (from the repo root) |
| `UI_UX_FINAL_MANIFEST.sha256` | **Every file in this consolidated directory** (21 files incl. README, AI Assistant architecture, both manifests except itself, supporting evidence). The authoritative current manifest. | `sha256sum -c UI_UX_FINAL_MANIFEST.sha256` (from this directory) |

Both currently verify `OK`.

*End of package README. Documentation-only.*
