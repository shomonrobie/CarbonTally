# CarbonTally — Final Product Decision Register

> **Purpose:** Historical decision reconstruction — the authoritative input for the final
> CarbonTally Architecture Blueprint. Read-only; no implementation.
> **Date:** 2026-09-01
> **Git HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (branch `main`)
> **Method:** Full recursive review of `docs/` (537 files), migration records, and implementation
> evidence. Authority ranking: explicit Product Owner decision → later PO clarification →
> approved/frozen architecture → consistent established architecture → Cline recommendation →
> OHD recommendation → current implementation.
> **Golden rule applied:** the newest-looking document is NOT automatically correct. Every source
> was classified (CURRENT / SUPERSEDED / OBSOLETE / PROPOSAL / INVESTIGATION / IMPLEMENTATION
> RECORD / UNKNOWN) with evidence. No document was deleted or modified.

---

# 1. Executive Summary

CarbonTally's decision history is **well-documented and largely consistent**, but it is spread
across multiple overlapping registers with **two different decision-numbering schemes**, and it
contains a small number of **genuine conflicts** that must be surfaced rather than silently
reconciled.

The authoritative decision set is:

1. **AGENTS.md** — the current project constitution; contains the most recent ratified Product
   Owner decisions (customer-factor self-approval §16, consultant operating model §10, PE operating
   model §8/§12, N1 messaging §28, N3 retention §42, admin separation §31, white-label §64,
   security §44–§45, V3-canonical/legacy-temporary §9/§79).
2. **Product Owner Decision Register v1** (2026-08-26; identical copies in
   `docs/audit/openhands/` and `docs/ChatGPT/`) — the consolidated product/policy baseline
   (market, identity, PE legal model, no-download, AI-first, extraction workflow, factors,
   traceability, retention direction, legacy-route removal, public website, admin control plane,
   customer final approval, terminology).
3. **D1–D21 frozen UX/product register** (2026-08-24, in `docs/audit/openhands/ui-ux/`) +
   **N1–N3** supplements — APPROVED / FROZEN UX and product-model decisions (viewer permissions,
   customer processing participation, consultant model, owner/admin model, approver role, PE
   validation/review/QC, report model, multi-org consultant context, custom factors, invitation
   acceptance, payment provider-neutrality, public pricing, waitlist, consultant acquisition,
   retention, AI governance, master data, workflow-first navigation, split-screen workbench,
   responsive strategy, unified design system).
4. **Ratified business decisions recorded in the V3 Actor/Workspace/Access Model** (2026-08-20):
   the PE operating model (§6.1), the strictly non-customer-facing PE boundary (§35), and the
   final consultant commercial model (§37) — all RESOLVED / RATIFIED.
5. **ADR-V3-001…016 register + V3 Architecture Specification v1.0** — the approved architecture
   decisions (PE dedicated table Option B; customer factors; work-item model; dpq state machine;
   issues first-class; factor provider architecture V3M-4; customer-factor precedence D-cf-5;
   snapshot provenance O1).
6. **CL-66 Admin Control Plane decision + ratified D-P2-02/03/04** (2026-08-30) — V3 `/ops` is
   the canonical staff/admin application; legacy admin CRA is deprecated-but-quarantined; QC has
   limited authority; destructive retention enforcement deferred.
7. **Migration records** — the D15/D19/D21/D22/D27/D32/D33/D35/D37 migrations plus V3M-1…V3M-11
   implement the approved decisions and carry the most recent ratified decisions (system_admin
   superset V3M8; PE manager role; durable automatic processing V3M9; org-membership uniqueness
   V3M10; operational indexes V3M11; audit immutability; tenant org_id NOT NULL; consultant
   revocation roles WS6/SEC-0003).

**Principal conflicts surfaced (not silently resolved):**

- **Two D-numbering schemes.** The 2026-08-20 Actor-model register used D14–D22 for
  processing/consultant decisions (D15 = consultant grant, D19 = consultant transition, D21 =
  white-label, D22 = PE assignment); the 2026-08-24 frozen register re-uses D1–D21 for UX/product
  decisions (D15 = retention, D19 = workbench, D21 = design system). The frozen register asserts
  "no duplicate decision numbers were created"; historically the same numbers were used with
  different meanings. Migrations follow the Actor-era numbering (d15/d19/d21/d22…).
- **Customer-factor self-approval.** ADR-V3-002 v1.1 (2026-08-11) recorded "self-approval
  prohibited"; AGENTS.md §16 records a later ratified PO decision: **Customer Owner MAY
  self-approve**. The later PO clarification supersedes.
- **Admin control plane surface.** CL-66 D-P2-02 (2026-08-30) made V3 `/ops` the canonical staff/
  admin surface and quarantined the legacy `/admin` CRA. The recent product requirements re-state
  a "dedicated `/admin` control-plane application/surface". Whether the final blueprint builds a

---

# 2. Research Method

1. Enumerated the entire `docs/` tree (537 files) and removed non-decision artifacts (UI HTML
   mockups, screenshots, generated scratch, xlsx/pdf binaries).
2. Read the decision-critical documents in full or in key sections: the three PO register copies,
   the ADR register, the V3 Architecture Specification, the Actor/Workspace/Access Model, the
   MASTER UX reconciliation + recommendation, the Admin Control Plane decision, the PE Messaging
   decision, the Platform Processing Architecture Master, the Staff Roles doc, the early
   `docs/Final/*` proposals, migration files, and representative Cline/OHD phase and audit
   reports.
3. Cross-checked every meaningful decision against: (a) explicit status words (LOCKED / APPROVED /

**UX/design:** `docs/audit/openhands/ui-ux/MASTER_UX_DECISION_RECONCILIATION_REPORT.md` · `MASTER_UX_RECOMMENDATION.md` · `UI_UX_IMPLEMENTATION_MATRIX.md` · `MASTER_SCREEN_INVENTORY.md` · `UI_UX_OPTION_A/B/C_*.md` · `docs/architecture/CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md` (supporting evidence) · `docs/architecture/CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md` · `docs/cline/CarbonTally UI/UX Design Principles & Guidelines v1.0.md` · `docs/Final/UI_UX-Final_Guideline.md`.

**Cline reports (implementation/audit):** the ~60 files in `docs/audit/cline/` (V3 phases 1–8, Phase A–C, D20–D37, V3M migration records, RV1/RV2 remediation, security, billing D36/D37, OCR, investor demo, backup/migration reconciliation) — classified as IMPLEMENTATION RECORD / INVESTIGATION.

**OHD/OpenHands independent audits:** `docs/audit/openhands/*` (persona acceptance, security acceptance, PE security, UI/UX visual, website prelaunch, post-restoration acceptance, QA report, Cline implementation backlog, previous-session copies).

**Early / historical:** `docs/Final/*` (Multi-Company Management Strategy, Consultant Firm Team Management, Final Database Schema Analysis & Recommendation, final_prodcut_viability_report, UI_UX-Final_Guideline) · `docs/Final_Kimi/*` (RC1 independent database audit; UK/IE compliance; production hardening plan) · `docs/cline/archive` and `docs/cline/prompts/*` (historical task instructions) · `docs/architecture/changelog.md` (V2.0 July 2026) · `docs/Pricing/*`, `docs/legal/*` (drafts), `docs/business/*`, `docs/standalone/*`, `docs/sample_bills/*`.

**Migration/schema records:** `supabase/migrations/` (41 files, RC2 base through V3M-11), `database/rc1`/`database/rc2`, `v3_schema.sql`, `docs/cline/CarbonTally_DB_Schema_V3M2.md`, `docs/architecture/DB_Migration/*`.

---

# 3. Sources Reviewed

**Product Owner / ratified baselines:** AGENTS.md · `docs/audit/openhands/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (identical to `docs/ChatGPT/…`) · `docs/audit/openhands/ui-ux/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (D1–D21 + N1–N3) · `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` (CL-66; D-P2-02/03/04) · `docs/cline/CARBONTALLY_PE_MESSAGING_PO_DECISION.md` · migrations `20260831040000_consultant_revocation_roles.sql` (WS6/SEC-0003) and `20260828010000_v3m8_system_admin_role_model.sql` (PO Decision 2).

**Approved architecture:** `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` (ADR-V3-001…016) · `docs/architecture/CarbonTally_V3_Architecture_Specification_v1.0.md` · `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` · `docs/cline/CarbonTally_Platform_Processing_Architecture_Master_v1.md` · `docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` · `docs/architecture/RBAC.md` · `docs/architecture/API_DOCUMENTATION.md`/`API_ENDPOINTS.md`/`API_SUMMARY.md` · `docs/architecture/customer_dashboard_architecture.md` · `docs/architecture/RealTImeImplementation` · `docs/architecture/TechnologyStack.md` · `docs/architecture/ARCHITECTURE_DECISIONS.md` · `docs/architecture/DB_Migration/*`.

  new dedicated `/admin` V3 surface or continues with `/ops` is a PO decision (see §39).
- **PO register copy inconsistency.** The ui-ux register's header claims its authoritative source
  is `docs/ChatGPT/…`, but that file currently contains the 26-Aug consolidated register (a
  different document). The D1–D21 source-of-record file was not placed as claimed.

**Implementation gaps against approved design** (recorded, not reinterpreted as new requirements):
PE entity-scoped extraction is assignment-based (D22 implemented); the manual-extraction pipeline
cannot yet be entity-scoped for *multiple extraction companies*; the consultant lifecycle
in-place transition (D19 Actor-era) and export/import are NOT implemented; full white-label
rendering NOT implemented; retention UI/periods NOT implemented (deferred); PE operational
messaging threads NOT implemented (N1 model approved; entity-scoped implementation decision open);
legacy routes still mounted (removal gated on dependency inventory); calculation-snapshot
API-only for consultants holds; AI extraction not yet wired into the durable automatic pipeline
(deterministic extraction only).


---

# 4. Source Authority Classification

| Source | Type | Authority level | Status |
|---|---|---|---|
| `AGENTS.md` (repo root) | Constitution | L1 (current ratified PO decisions) | CURRENT |
| PO Decision Register v1 (26 Aug) — `docs/audit/openhands/…` = `docs/ChatGPT/…` | PO baseline | L1 | CURRENT |
| D1–D21 + N1–N3 register — `docs/audit/openhands/ui-ux/…` | Frozen UX/product baseline | L1/L3 | CURRENT (its "authoritative copy in docs/ChatGPT" claim is UNMATCHED — see §33) |
| Actor/Workspace/Access Model (20 Aug) | Approved architecture + ratified decisions | L1 (ratified §6.1/§35/§37) + L4 | CURRENT |
| ADR register (v1.1, 11 Aug) | Approved architecture | L3 | CURRENT (DECIDED items); PROVISIONALLY DECIDED items pending |
| V3 Architecture Specification v1.0 (v1.1) | Approved architecture | L3 | CURRENT |
| Admin Control Plane decision CL-66 + D-P2-02/03/04 (30 Aug) | Ratified implementation decision | L1/L3 | CURRENT |
| Platform Processing Architecture Master v1 | Master reference | L4 | CURRENT (reference; supersedes nothing) |
| MASTER UX reconciliation + recommendation + implementation matrix (24 Aug) | Reconciled UX baseline | L3/L4 | CURRENT |
| Migration files V3M-1…11, D15/D19/D21/D22/D27/D32/D33/D35/D37 | Implementation records carrying ratified decisions | L4 (implemented) | CURRENT |
| Cline phase/audit reports (`docs/audit/cline/*`) | Implementation records / investigations | L5 | IMPLEMENTATION RECORD |
| OHD audits (`docs/audit/openhands/*`) | Independent findings | L6 | INVESTIGATION / FINDINGS |
| `docs/Final/*` (Multi-Company Strategy, Consultant Firm Team Management, DB Schema Recommendation, viability) | Early strategy docs | L5 (recommendation) | SUPERSEDED / PROPOSAL (superseded by ratified D3/D8/D37 etc.) |
| `docs/Final_Kimi/*` (RC1 audit, UK/IE compliance, hardening) | Independent audits (v1 era) | L6 | SUPERSEDED (RC1 → RC2 → V3) |
| `docs/architecture/UI`, `UI2` HTML mockups | Early static UI mockups | L6 | OBSOLETE (pre-dating D21) |
| `docs/architecture/ARCHITECTURE_DECISIONS.md`, `RBAC.md`, `changelog.md`, `db_change.md` | Early docs | L4/L5 | PARTIALLY SUPERSEDED (pre-V3; keep as history) |
| `docs/cline/prompts/*`, `docs/cline/archive` | Historical task instructions | — | TEMPORARY INSTRUCTIONS / OBSOLETE |
| `docs/legal/*` (incl. draft retention policy) | Legal drafts | — | DRAFT (informative; not ratified product policy) |
| `docs/Pricing/*` | Pricing analyses | L5 | PROPOSAL / EVOLVING (D12 GBP indicative governs public pricing) |
| `docs/business/*`, `docs/sample_bills/*`, `docs/styles/*` | Business/evidence artifacts | — | SUPPORTING / NOT DECISIONS |
| `docs/standalone/*` | QA-harness portability analyses | L5 | INVESTIGATION (QA tooling, not product) |

   FROZEN / DECIDED / PROVISIONALLY DECIDED / DEFERRED / RATIFIED / RESOLVED / PROPOSED /
   NOT IMPLEMENTED); (b) the decision-authority hierarchy; (c) the current implementation
   (schema, migrations, routers, UI).
4. Recorded conflicts explicitly with both sides and a classification (CURRENT / SUPERSEDED /
   UNRESOLVED / PO DECISION REQUIRED).

---

# 5. Obsolete / Superseded Documents

| Document | Status | Reason |
|---|---|---|
| `docs/architecture/UI/*`, `UI2/*` (static HTML mockups) | OBSOLETE | Pre-date D21 unified design system; superseded by `frontend/src/v3/components/ui/` + tokens |
| `docs/architecture/changelog.md` (V2.0, July 2026) | SUPERSEDED | Pre-V3; V3 is canonical (AGENTS.md §9) |
| `docs/Final/CarbonTally - Multi-Company Management Strategy.md` (2 Aug) | SUPERSEDED / PROPOSAL | Recommended multi-company as "Version 2"; superseded by ratified D3/D8 consultant model + D37 hybrid commercial model |
| `docs/Final/Consultant Firm Team Management.md` | SUPERSEDED / PROPOSAL | Superseded by ratified consultant firm-member model (`consultant_firm_members`, `can_*` flags; D3/D8/D14) |
| `docs/Final/CarbonTally - Final Database Schema Analysis & Recommendation.md` | SUPERSEDED / PROPOSAL | Pre-dates RC1/RC2/V3 migrations; schema moved on (V3M-1…11) |
| `docs/Final/final_prodcut_viability_report.md` | OBSOLETE / PROPOSAL | Early viability analysis; not a product decision |
| `docs/Final_Kimi/*` (RC1 audit, hardening, UK/IE compliance, structural change) | SUPERSEDED | RC1-era; RC2 schema + V3 supersede (see `database/rc1` → `database/rc2` → `supabase/migrations/`) |
| `docs/architecture/ARCHITECTURE_DECISIONS.md`, `RBAC.md`, `db_change.md`, `filestructure.md`, `customer_dashboard_architecture.md`, `API_*.md` | PARTIALLY SUPERSEDED | Pre-V3/reference-era; retain as history; V3 ADR register + spec are the current authority |
| `docs/cline/archive/*`, `docs/cline/prompts/*`, `docs/ChatGPT/*prompts*` | TEMPORARY INSTRUCTIONS / OBSOLETE | Historical task prompts; not decisions |
| `docs/architecture/DB_Migration/migration_001…012` (identity/org access/org-man/supplier/doc/carbon/reporting/collab/platform-admin/RLS/index/cleanup) | SUPERSEDED | Early migration plan superseded by RC2 migrations + V3M migrations |
| `docs/architecture/RealTImeImplementation` | SUPERSEDED / OBSOLETE | Early Realtime notes; current Realtime = `useConversationRealtime` + N1 |
| `docs/architecture/AI_Prompts/…`, `chatGptPrompts.txt` | TEMPORARY INSTRUCTIONS | Historical prompts |
| `docs/architecture/CarbonTallyCustomerPortal.md` | PARTIALLY SUPERSEDED | Early customer-portal concept; superseded by D18/D19 customer UX |
| `docs/Pricing/CarbonTally_Pricing_Comparison_Baseline_v2.md` / `Unit_Economics_Baseline_v1` | SUPERSEDED / PROPOSAL | D12 GBP indicative pricing governs public surfaces; D37 commercial model governs billing |
| `docs/legal/draft/*` (DPA, MSA, retention, privacy, cookies, TOS, refunds) | DRAFT | Not ratified product policy; evidence for D15/N3/destructive-retention deferral |
| Early V2-era route designs (`routes/…` changelog entries) | OBSOLETE | V2.0 feature list (July 2026); V3 canonical |
| `docs/audit/openhands/previous-session/*` | SUPERSEDED copies | Duplicates of newer OHD reports (see §3) |
| Committed-baseline `PricingPage.jsx` (USD, proposed) | SUPERSEDED (in git history) | D12 record: GBP indicative direction supersedes the committed USD variant |

Documents **not** silently discarded: all are preserved in place; the reasons above are the record.

---

---

# 6. Current Authoritative Documents

1. **AGENTS.md** (repo root) — living constitution; final word on PO-ratified policy and agent
   rules.
2. **PO Decision Register v1** (26 Aug 2026) — `docs/audit/openhands/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (= `docs/ChatGPT/…`, md5-identical). Consolidated product/policy baseline.
3. **D1–D21 + N1–N3 register** (24 Aug 2026) — `docs/audit/openhands/ui-ux/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (+ `MASTER_UX_DECISION_RECONCILIATION_REPORT.md`, `MASTER_UX_RECOMMENDATION.md`, `UI_UX_IMPLEMENTATION_MATRIX.md`).
4. **V3 Actor/Workspace/Access Model** — ratified business decisions §6.1, §35, §37 and the four-axis access model.
5. **ADR register v1.1** + **V3 Architecture Specification v1.0 (v1.1)** — approved architecture; DECIDED items are the architecture authority.
6. **Admin Control Plane decision (CL-66)** with ratified **D-P2-02 / D-P2-03 / D-P2-04**.
7. **Migrations V3M-1…V3M-11 + D-series** — the implemented schema carrying the ratified decisions.
8. **WS6/SEC-0003** consultant revocation roles migration — ratified relationship-revocation model.


---

# 7. Complete Product Decision Register

Each entry: **ID · CATEGORY · DECISION · STATUS · AUTHORITY · SOURCE · DATE/ERA · EVIDENCE ·
CURRENT IMPLEMENTATION · IMPLEMENTATION GAP · SUPERSEDES · SUPERSEDED BY · CONFIDENCE.**
Statuses: CURRENT / SUPERSEDED / UNRESOLVED / PO DECISION REQUIRED. Confidence: HIGH/MED/LOW.

### D01 — Market scope (UK / Ireland / EU/EEA)
- **DECISION:** Initial market is UK, Ireland and EU/EEA; gradual launch, not unrestricted global.
- **STATUS:** CURRENT · **AUTHORITY:** L1 (PO) · **SOURCE:** PO-REG §1.1 (LOCKED).
- **IMPLEMENTATION:** country CHECK `('GB','IE')`; currency `('GBP','EUR')`; SEAI factor support.
- **GAP:** EU/EEA factor providers (ADEME/IPCC/EU residual) DEFERRED (ADR-V3-015).
- **CONFIDENCE:** HIGH.

### D02 — Public signup closed; controlled onboarding
- **DECISION:** Public production signup initially closed; request/beta access; onboarding
  controlled; later D35 self-service signup on `/signup` (no beta gate) with beta preserved as a
  controlled-cohort mechanism.
- **STATUS:** CURRENT (D35 supersedes the beta-gate era) · **AUTHORITY:** L1 · **SOURCE:** PO-REG
  §1.2/§1.3; D13; D35.
- **IMPLEMENTATION:** `/signup` self-service (creator→OWNER); `/beta/signup` optional.
- **GAP:** none material.
- **SUPERSEDES:** D34 "NOT READY — beta-gated signup" finding.
- **CONFIDENCE:** HIGH.

### D03 — One account, one role (no dual-scope identity)
- **DECISION:** One person = one CarbonTally account = one role; must not simultaneously be PE
  staff + customer member + consultant.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §2.1 (LOCKED); Actor Model §3.
- **IMPLEMENTATION:** single auth identity; `staff_profiles.entity_id` vs `organization_members`
  vs `consultant_firm_members` are separate families.
- **GAP:** schema does not forbid a user holding rows in multiple families (enforcement is
  application-level) — note for blueprint.
- **CONFIDENCE:** HIGH.

### D04 — CarbonTally controls Processing Work assignment
- **DECISION:** Assignment by authorized CarbonTally staff or automated controls; PE cannot

### D07 — PE no-download of source documents
- **DECISION:** PE staff must NOT download/store customer source documents; access via portal;
  no raw storage credentials; no arbitrary customer storage objects.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §3.3 (LOCKED); Actor Model §35.
- **IMPLEMENTATION:** private documents bucket + short-lived signed URLs; `SecureDocumentViewer`
  with `allowDownload=false` for PE; server-side re-authorization.
- **GAP:** browser-level signed-URL download-scope defect found in functional audit (P1) — the
  intent is intact, the viewer is broken; see D44.
- **CONFIDENCE:** HIGH.

### D08 — Bangladesh / international human processing policy-gated
- **DECISION:** Bangladesh PE processing NOT automatically prohibited but gated on legal/
  contractual/transfer/security/operational controls; special-category data default: do not send
  to Bangladesh PEs.
- **STATUS:** CURRENT (POLICY GATED) · **AUTHORITY:** L1 · **SOURCE:** PO-REG §3.4/§3.5.
- **IMPLEMENTATION:** none (no real PE processing yet).
- **GAP:** legal gate not yet exercised; counsel confirmation pending.
- **CONFIDENCE:** HIGH (policy), legal items open.

### D09 — Internal/local AI first; external AI controlled
- **DECISION:** Prefer deterministic Python processing + internal/local AI before external AI
  providers; external providers only through an approved/configurable provider architecture;
  AI assist-only, never authoritative for calculations/factors/evidence/approval/security.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §4.1/§4.2 (LOCKED); D16 (FROZEN).
- **IMPLEMENTATION:** `AIExtractionEngine` (suggestion-only) wired to legacy workflow engine;
  durable pipeline currently uses deterministic `extract_document`; no external AI provider
  configured.
- **GAP:** durable automatic pipeline does not yet use the AI extraction engine (functional
  audit P1) — deterministic extraction gates most uploads to manual review.
- **CONFIDENCE:** HIGH.

### D14 — Customer-factor approval authority (self-approval) — CONFLICT RESOLVED
- **DECISION (EARLIER, ADR v1.1 D-cf-3):** "Staff may create/edit/validate drafts but cannot
  approve their own factor (self-approval prohibited); Organization Admin/Owner approves."
- **DECISION (LATER, ratified PO):** **Customer Owner MAY self-approve a custom factor.** Customer
  Member not unless separately authorized; Viewer not.
- **STATUS:** SUPERSEDED (by later PO clarification) → CURRENT = owner self-approval allowed.
- **AUTHORITY:** L1 (later PO) supersedes L3 (ADR). **SOURCE:** AGENTS.md §16; ADR register
  D-cf-3; migration V3M-3 evidence.
- **IMPLEMENTATION:** customer-factor approval API owner/admin-gated.
- **CONFIDENCE:** HIGH.

### D15 — Traceability / row-level evidence chain (locked)
- **DECISION:** Preserve row-level traceability; do NOT replace with a parallel evidence system;
  human corrections retain original + corrected values with reviewer/time/reason; finalized
  calculation evidence immutable.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §7.1/§7.2/§7.3 (LOCKED);
  D33 evidence-traceability migration.
- **IMPLEMENTATION:** `calculation_snapshots` immutable (`content_hash`, `request_id`,
  `source_item_id`); `emissions_logs.snapshot_id`; evidence trail UI; audit immutability
  migration `20260831020000`.
- **GAP:** minor (document-state duality — see D46).
- **CONFIDENCE:** HIGH.

### D16 — Retention direction (locked) + N3 configurable retention + D-P2-04 defer destructive
- **DECISION:** Retention must support customer-specific policies; do not invent retention
  durations; retention configurable through Settings/Admin control plane; enforcement server-side;
  **destructive retention deletion DEFERRED** to a dedicated phase (dependency analysis, legal
  review, evidence preservation, audit logging, grace periods, backups, legal holds, customer
  notification). No automatic destructive deletion active.
- **STATUS:** CURRENT (APPROVED PRODUCT MODEL; destructive enforcement DEFERRED) · **AUTHORITY:**

### D21 — Canonical terminology
- **DECISION:** Use established terms: Customer Organisation, Processing Entity, PE Staff,
  Processing Work, Human Processing/Review, Validation, QC, Evidence, Emission Factor, Custom
  Emission Factor, Factor Matching, Calculation, CarbonTally Staff; do not casually replace with
  "client/worker/outsourcing company".
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §19; V3 Glossary.
- **CONFIDENCE:** HIGH.

### D22 — Four access axes (never interchangeable)
- **DECISION:** Customers (org roles) / CarbonTally internal staff (`entity_id IS NULL`) /
  Processing Entity staff (`entity_id` populated) / Consultants (firm + client grants) are four
  distinct access axes.
- **STATUS:** CURRENT · **AUTHORITY:** L3/L4 · **SOURCE:** Spec §8.1; ADR-V3-001/010; Actor Model.
- **IMPLEMENTATION:** `organization_members`, `staff_profiles.entity_id`, `consultant_firm_members`
  / `consultant_clients`, `is_org_consultant`, `is_entity_member`.
- **CONFIDENCE:** HIGH.

### D23 — PE architecture: dedicated table, Option B (ADR-V3-001)
- **DECISION:** Dedicated `processing_entities` table; `staff_profiles.entity_id IS NULL` =
  CarbonTally internal; populated = PE staff; PE never represented by `organizations`; lifecycle
  active/remediation/suspended/terminated; suspension/termination never deletes history; entity
  RLS deny-by-default + `is_entity_member`.
- **STATUS:** CURRENT (DECIDED) · **AUTHORITY:** L3 (approved) · **SOURCE:** ADR-V3-001;
  V3M-1 migration.
- **IMPLEMENTATION:** implemented (V3M-1/V3M-6/D22/D24).
- **GAP:** multi-entity manual-extraction scoping (D31).
- **CONFIDENCE:** HIGH.

### D24 — PE work-assignment model (D22, ratified 20 Aug)
- **DECISION:** One org may be served by multiple processing parties simultaneously; no permanent
  org↔entity assignment; CarbonTally controls assignment; entity receives only its assigned work;

### D29 — Consultant operating model (D3/D8, ratified)
- **DECISION:** Consultants are first-class operators (not read-only advisers); manage a portfolio
  of client organisations; active-client context explicit; firm roles owner/manager/consultant/
  viewer with `can_*` permission flags; consultant team management; can create customers; operate
  client workspaces.
- **STATUS:** CURRENT (APPROVED/FROZEN) · **AUTHORITY:** L1 · **SOURCE:** D3/D8/D14; AGENTS.md §10.
- **IMPLEMENTATION:** `ConsultantPage` + `/api/v3/consultants/*` (31 endpoints); firm/client
  grants; client switcher.
- **CONFIDENCE:** HIGH.

### D30 — Consultant client access + relationship revocation (D15 Actor-era; WS6/SEC-0003)
- **DECISION:** Consultant client access is governed by the ACTIVE consultant-client relationship
  (RLS + API); **Owner/Admin/Manager may revoke; Member/Viewer may not**; revocation removes
  active access but NEVER deletes client data; revocation preserves provenance (soft lifecycle
  `status='ended'` + audit).
- **STATUS:** CURRENT (RATIFIED + IMPLEMENTED) · **AUTHORITY:** L1 · **SOURCE:** Actor Model §34;
  migration `20260831040000` (WS6/SEC-0003); D15.
- **IMPLEMENTATION:** `consultant_clients` lifecycle; `is_consultant_firm_revoker`; RLS scoping.
- **CONFIDENCE:** HIGH.

### D31 — Consultant commercial model: HYBRID, managed-service default (ratified 20 Aug)
- **DECISION:** Hybrid = direct CarbonTally customers + consultants as CarbonTally customers;
  **default = consultant-led MANAGED SERVICE** (Mode A); client does NOT automatically access
  CarbonTally; Mode B co-branded and Mode C full white-label are FUTURE; client may later become a
  direct customer via in-place transition (preferred, preserve org/data identity); export/import
  future.
- **STATUS:** CURRENT (RESOLVED) · **AUTHORITY:** L1 · **SOURCE:** Actor Model §37; D14; AGENTS.md
  §11/§64.
- **IMPLEMENTATION:** consultant grants + client lifecycle + white-label foundation (branding
  config, brand context, report branding).
- **GAP:** in-place direct-customer transition NOT implemented; export/import NOT implemented;
  full white-label rendering (reports/email/domains/portal) NOT implemented.

### D35 — Durable automatic document processing (V3M9)
- **DECISION:** Automatic document processing must be durable, server-side, resumable,
  idempotent, observable, retryable, failure-aware, persisted; deterministic calculation request
  IDs; duplicate-prevention; manual-review gates; evidence persistence.
- **STATUS:** CURRENT (DECIDED + IMPLEMENTED) · **AUTHORITY:** L3/L1 · **SOURCE:** V3M9 migration;
  AGENTS.md §19; Phase A reports.
- **IMPLEMENTATION:** dpq durable columns (stage, attempt_count, max_attempts, last_error,
  locked_at/lock_token, per-stage outputs, snapshot id, source_item_id); worker claim loop.
- **GAP:** extraction-quality gate blocks most uploads (functional audit P1; see D09/D41).
- **CONFIDENCE:** HIGH.

### D36 — Customer factors domain (ADR-V3-002 DECIDED)
- **DECISION:** Dedicated `customer_factors` table (Option B); lifecycle DRAFT→ACTIVE→
  ARCHIVED/INACTIVE (soft-deactivate, versioned); snapshot provenance O1 (`factor_kind` +
  exactly-one-source); precedence D-cf-5.
- **STATUS:** CURRENT (DECIDED — READY/IMPLEMENTED) · **AUTHORITY:** L3 · **SOURCE:** ADR-V3-002;
  V3M-3.
- **CONFIDENCE:** HIGH.

### D37 — Issues first-class (ADR-V3-009)
- **DECISION:** Issue = first-class operational domain object (defect/exception/escalation),
  distinct from conversations; lifecycle open→in_progress→on_hold/escalated→resolved→closed.
- **STATUS:** CURRENT (DECIDED; implementation pending at decision time, later implemented) ·
  **AUTHORITY:** L3 · **SOURCE:** ADR-V3-009; `issues` table.
- **IMPLEMENTATION:** `issues` table + `/api/v3/issues` + IssuesTriageTab.
- **CONFIDENCE:** HIGH.

### D38 — Assignment/reassignment attribution (ADR-V3-005)
- **DECISION:** Reuse `review_assignment_history` as attribution; reconcile dormant
  `reassignment_history`/`processing_assignments` before retirement; D22 records assignment via
  V3 `audit_trail` (dormant family untouched).

### D41 — Billing/subscription: provider-neutral (D11/D37), configurable (D37-0), GBP indicative (D12)
- **DECISION:** Provider-neutral payment architecture (no hard-coded Stripe; adapters later);
  subscriptions/entitlements/credit-ledger/orders/payment records; storage metering; idempotency;
  no live payment-provider integration performed or claimed; configurable commercial plans;
  public pricing GBP indicative pre-launch (Starter £49 / Pro £149 / Business £399 / Custom).
- **STATUS:** CURRENT (APPROVED/FROZEN + IMPLEMENTED) · **AUTHORITY:** L1/L3 · **SOURCE:** D11/D12;
  D36; D37-0; D37.
- **IMPLEMENTATION:** `/api/v3/billing/*`, `/api/v3/commercial/*`; plans/orders/ledger/storage/
  payments tables.
- **GAP:** provider adapters (PayPal/Wise/card) future; live checkout absent by design.
- **CONFIDENCE:** HIGH.

### D42 — Security / RLS / tenant isolation (ADR-V3-010)
- **DECISION:** Extend existing org RLS; entity RLS deny-by-default + `is_entity_member`; never
  weaken tenant isolation; FORCE RLS deferred to separate security investigation (known decision);
  legacy permissive policies flagged investigate/harden.
- **STATUS:** CURRENT (PROVISIONALLY DECIDED; FORCE RLS DEFERRED) · **AUTHORITY:** L3/L1 ·
  **SOURCE:** ADR-V3-010; AGENTS.md §44/§45/§67; known-decisions list.
- **IMPLEMENTATION:** org/consultant/entity RLS helpers; entity SELECT-only storeys.
- **GAP:** latent name-string `require_admin`/`is_admin` over-grant risk (no entity admin staff
  provisioned); FORCE RLS not yet applied.
- **CONFIDENCE:** HIGH.

### D43 — Admin/Staff role separation + QC limited authority + system_admin superset
- **DECISION:** Staff/operations separate from Admin; QC has limited internal quality-control
  authority (never customer approval); `system_admin` is a superset of `admin`
  (can_manage_billing added); `pe_manager` staff role; permission keys
  `can_process/can_review/can_manage_staff/can_manage_billing/can_view_all`.
- **STATUS:** CURRENT (RATIFIED) · **AUTHORITY:** L1 · **SOURCE:** D-P2-03; V3M8 migrations;
  CL-66.
- **IMPLEMENTATION:** `staff_roles.permissions`; `require_admin` = admin/system_admin;

### D48 — Workflow-first navigation + split-screen workbench (D18/D19 frozen)
- **DECISION:** D18 workflow-first authenticated navigation (no admin left-nav inside customer
  UX); D19 split-screen processing workbench with TOP workflow navigation (Queue→Extract→Map→
  Validate→Review→QC→Evidence), pane presets, no left sidebar inside workbench; D20 responsive/
  mobile tray strategy.
- **STATUS:** CURRENT (APPROVED/FROZEN) · **AUTHORITY:** L1 · **SOURCE:** D1–D21 register
  (D18/D19/D20); implementation `WorkbenchShell`/`WorkflowNav`.
- **CONFIDENCE:** HIGH.

### D49 — Design system (D21) + master data (D17) + locations (N2)
- **DECISION:** D21 unified design system on existing identity; D17 master data hierarchy
  Organisation → Locations → Facilities → {Assets, Vehicles}, Suppliers org-scoped (product/UX
  relationship, not mandated physical schema; users not forced to configure everything); N2
  Locations physical representation = PO DIRECTION RESOLVED / engineering decision.
- **STATUS:** CURRENT (APPROVED/FROZEN; N2 engineering detail open) · **AUTHORITY:** L1 ·
  **SOURCE:** D1–D21 register D17/D21/N2.
- **IMPLEMENTATION:** Facilities/Assets/Suppliers/Vehicles tables + tabs; Locations not yet a
  distinct entity.
- **GAP:** Locations distinct entity missing (implementation matrix G-P1-3).
- **CONFIDENCE:** HIGH.

### D50 — AI assistant (public visitor) vs authenticated messaging
- **DECISION:** CarbonTally Assistant is primarily a public visitor feature; authenticated users
  get the authenticated messaging experience; assistant inherits applicable permissions if exposed
  authenticated; do not substitute visitor-only functionality for internal messaging.
- **STATUS:** CURRENT (APPROVED) · **AUTHORITY:** L1 · **SOURCE:** AGENTS.md §29; OHD AI assistant
  architecture.
- **CONFIDENCE:** HIGH.

### D51 — White-label model (D21 white-label foundation; AGENTS.md §64)
- **DECISION:** White-labelling is presentation/integration over the existing platform; no
  separate deployments/databases/duplicate tenants; custom domains via existing web platform;
  customers/consultants own their domains/DNS/email; CarbonTally provides integration/
  verification.
- **STATUS:** CURRENT (foundation IMPLEMENTED; full rendering FUTURE) · **AUTHORITY:** L1 ·
  **SOURCE:** AGENTS.md §64; Actor Model §37.8/§37.13; D14.
- **IMPLEMENTATION:** branding config + brand context + report-branding context + email-sender
  config foundation.
- **GAP:** rendered reports/outbound email/custom domains/client portal not implemented.
- **CONFIDENCE:** HIGH.

### D52 — DataSecurity public page
- **DECISION:** DataSecurity is a public page.
- **STATUS:** CURRENT (RATIFIED) · **AUTHORITY:** L1 · **SOURCE:** known decisions; implementation
  `/data-security`.
- **CONFIDENCE:** HIGH.

### D53 — Investor demo data preservation + local credentials
- **DECISION:** Investor demo dataset (50 direct orgs, 911 client owners, 50 consultants, 3 PEs,
  5 internal staff, 1,185 demo identities) is valuable test infrastructure; never reset/truncate
  casually; credentials local-only, never committed; mutation testing isolated + cleaned up.
- **STATUS:** CURRENT (RATIFIED) · **AUTHORITY:** L1 · **SOURCE:** AGENTS.md §54–§56; DEMO
  IDENTITIES manifest.
- **IMPLEMENTATION:** seeded demo DB (verified intact: 1,183 demo users, 7,049 factors).
- **GAP:** creds-file password stale vs provisioned fallback (operational, not product).
- **CONFIDENCE:** HIGH.

  OperationsPage permission-aware tabs.
- **CONFIDENCE:** HIGH.

### D44 — Private documents storage + signed URLs (D32)
- **DECISION:** Documents bucket PRIVATE; access only via short-lived signed URLs; storage RLS;
  authz before issuing signed URLs.
- **STATUS:** CURRENT (IMPLEMENTED) · **AUTHORITY:** L1/L3 · **SOURCE:** D32 report; migration
  `20260823000000_d32_private_documents_storage.sql`; AGENTS.md §68.
- **IMPLEMENTATION:** private bucket; signed URLs; non-member 403; legacy public URLs blocked.
- **GAP:** signed-URL download-scope renders preview broken in browser (functional audit P1) —
  security intent intact.
- **CONFIDENCE:** HIGH.

### D45 — Evidence traceability (D33)
- **DECISION:** Calculation snapshots carry provenance (`factor_id`/`factor_kind`/
  `customer_factor_id`/`source_item_id`); evidence trail UI.
- **STATUS:** CURRENT (IMPLEMENTED) · **AUTHORITY:** L1/L3 · **SOURCE:** D33 reports; ADR-V3-014.
- **CONFIDENCE:** HIGH.

### D46 — Database immutability & integrity hardening (V3M10/11 + audit immutability)
- **DECISION:** Org membership uniqueness (V3M10); operational indexes (V3M11); audit/activity
  immutability; tenant org_id NOT NULL; 7,049 emission factors preserved.
- **STATUS:** CURRENT (IMPLEMENTED) · **AUTHORITY:** L4 (ratified via migration records) ·
  **SOURCE:** migrations `20260831*`.
- **CONFIDENCE:** HIGH.

### D47 — UI foundation = existing D21 primitives (not shadcn)
- **DECISION:** Existing CarbonTally V3 UI primitives (hand-rolled `v3/components/ui/` + tokens)
  are the current UI foundation; do not assume shadcn/ui should replace them (known decisions);
  DataTable/pagination/search/sort/filter evaluated for canonical standardisation (no uncontrolled
  duplication).
- **STATUS:** CURRENT (D21 APPROVED/FROZEN) · **AUTHORITY:** L1/L3 · **SOURCE:** D21; known
  decisions; implementation.
- **IMPLEMENTATION:** `v3/components/ui/*` (12 primitives), tokens.css, DataTable.
- **GAP:** component duplication persists (functional/forensic audits); convergence is an
  engineering direction, not a ratified decision.
- **CONFIDENCE:** HIGH.

- **STATUS:** PROVISIONALLY DECIDED / PARTIAL · **AUTHORITY:** L3 · **SOURCE:** ADR-V3-005.
- **CONFIDENCE:** MED.

### D39 — Messaging boundaries (N1, APPROVED/FROZEN)
- **DECISION:** N1: Customer internal/support messaging; Consultant internal/support/authorised
  active-client messaging; CarbonTally authorised support/admin; PE = operational CarbonTally
  messaging; NO unrestricted Customer↔PE; UI is never the security boundary; server-enforced.
  Current implementation: PE denied 403 on org messaging (correct). Entity-scoped PE operational
  messaging threads NOT implemented; the Phase B PO-decision note asks whether to build them.
- **STATUS:** N1 CURRENT; entity-scoped PE messaging implementation = PO DECISION REQUIRED ·
  **AUTHORITY:** L1 (N1) · **SOURCE:** AGENTS.md §28; D1–D21 register §24 (N1); PE Messaging PO
  Decision (2026-08-31).
- **IMPLEMENTATION:** org-scoped conversations; `_authorize_org_actor`; Realtime
  `useConversationRealtime`.
- **GAP:** no `entity_id` on conversations; PE messaging absent (by design until decision).
- **CONFIDENCE:** HIGH (N1); implementation decision open.

### D40 — Notifications
- **DECISION:** Notifications recipient-scoped; mark-read/read-all; Realtime delivery.
- **STATUS:** CURRENT (implementation) · **AUTHORITY:** L4 · **SOURCE:** implementation; PO-REG
  demo/onboarding context.
- **CONFIDENCE:** HIGH.

- **CONFIDENCE:** HIGH.

### D32 — Customer/consultant processing separate from internal operations
- **DECISION:** Customer/consultant processing and internal CarbonTally operations are separate
  concerns (separate API families, separate UI surfaces).
- **STATUS:** CURRENT (APPROVED) · **AUTHORITY:** L1 · **SOURCE:** AGENTS.md §7/§9; D2/D3;
  implementation `/api/v3/processing/*` vs `/api/v3/ops/*`.
- **CONFIDENCE:** HIGH.

### D33 — Calculation snapshots API-only for consultants
- **DECISION:** Calculation snapshots are API-only for consultants (consultants read persisted
  snapshots; no client-side calculation).
- **STATUS:** CURRENT (APPROVED) · **AUTHORITY:** L1 · **SOURCE:** task-known decision; ADR-V3-014;
  implementation (immutable snapshots; `v3_emissions`/`consultant` read surfaces).
- **IMPLEMENTATION:** snapshot immutable; consultant evidence/reports read server data.
- **CONFIDENCE:** HIGH.

### D34 — Work Item model (ADR-V3-003) + dpq state machine (ADR-V3-004)
- **DECISION:** Canonical Work Item abstraction over `manual_review_queue`; technical pipelines
  (`document_processing_queue`, `report_generation_queue`) are state machines, NOT human queues;
  logical queues (filtered views), no fifth queue; ADR-V3-012: batch = grouping, Work Item =
  atomic.
- **STATUS:** PROVISIONALLY DECIDED (direction approved; implementation of the canonical Work Item
  layer pending) · **AUTHORITY:** L3 · **SOURCE:** ADR-V3-003/004/012/016; Spec §13.
- **IMPLEMENTATION:** dpq durable state machine (V3M9); manual_review_queue still the work item
  store; no canonical Work Item domain yet.
- **GAP:** canonical Work Item abstraction not implemented; queue consolidation (ADR-V3-016)
  DEFERRED until chain completes.
- **CONFIDENCE:** MED-HIGH.

  entity staff access = assigned work only; no `organizations.processing_entity_id`.
- **STATUS:** CURRENT (RATIFIED + IMPLEMENTED D22) · **AUTHORITY:** L1 · **SOURCE:** Actor Model
  §6.1/§30; migration d22.
- **IMPLEMENTATION:** `manual_extraction_batches.entity_id`; `assign_batch`; entity extraction
  workspace; entity-scoped issues.
- **GAP:** manual-extraction batches/items lack entity scoping → "multiple extraction companies"
  not operational (Actor Model §6.2).
- **CONFIDENCE:** HIGH.

### D25 — PE strictly non-customer-facing (ratified 20 Aug)
- **DECISION:** PE MUST NOT contact customers/consultants directly; all communication mediated by
  CarbonTally; PE has work access only, never org membership/context; no customer-facing
  communication authority.
- **STATUS:** CURRENT (RATIFIED) · **AUTHORITY:** L1 · **SOURCE:** Actor Model §35; PO-REG §3.
- **IMPLEMENTATION:** PE denied org/messaging surfaces (403 verified); mediated clarification via
  entity-scoped issues.
- **GAP:** no entity↔CarbonTally operational messaging threads yet (D39); latent name-string
  `require_admin` risk recorded (§33/§34) before entity provisioning at scale.
- **CONFIDENCE:** HIGH.

### D26 — Customer model: org roles owner/admin/member/viewer
- **DECISION:** Org tenancy with CHECK roles `owner|admin|member|viewer`; viewer read-only (D1);
  owner/admin mutations (D4); owner/admin approver (D5).
- **STATUS:** CURRENT (APPROVED/FROZEN) · **AUTHORITY:** L1 · **SOURCE:** D1/D2/D4/D5; Actor Model
  §3/§13.
- **IMPLEMENTATION:** `organization_members.role` CHECK; `require_org_admin` / `require_org_member`.
- **CONFIDENCE:** HIGH.

### D27 — Customer processing participation (D2)
- **DECISION:** Distinguish customer decision-making / review / approval from CarbonTally
  operational processing and PE operational processing; five-layer approval separation.
- **STATUS:** CURRENT (APPROVED/FROZEN) · **AUTHORITY:** L1 · **SOURCE:** D2.
- **CONFIDENCE:** HIGH.

### D28 — Customer approver = owner/admin (D5)
- **DECISION:** Customer approval authority is owner/admin; members/viewers cannot approve.
- **STATUS:** CURRENT (APPROVED/FROZEN) · **AUTHORITY:** L1 · **SOURCE:** D5; Actor Model §16.
- **IMPLEMENTATION:** `APPROVER_ROLES = ['owner','admin']` in customer workspace; backend gate.
- **CONFIDENCE:** HIGH.

  L1 · **SOURCE:** PO-REG §8.1; D15 (frozen); N3; D-P2-04.
- **IMPLEMENTATION:** `/api/v3/settings/retention` persists config; no destructive deletion.
- **GAP:** retention UI + periods + deletion mechanics not implemented (deferred by decision).
- **CONFIDENCE:** HIGH.

### D17 — Legacy routes removal
- **DECISION:** Remove obsolete legacy application/document routes; do not hide unsafe routes in
  UI; verify V3 dependencies first; legacy remains temporarily (AGENTS.md §79: dependency
  inventory before removal); legacy public/unauthenticated document/upload surfaces must not
  remain for real personal data.
- **STATUS:** CURRENT (direction LOCKED; removal gated) · **AUTHORITY:** L1 · **SOURCE:** PO-REG
  §9.1/§9.2; AGENTS.md §79; CL-66 guardrails.
- **IMPLEMENTATION:** legacy routes still mounted in `main.py`; legacy admin CRA quarantined
  (CL-66).
- **GAP:** removal pending dependency inventory (explicit gate).
- **CONFIDENCE:** HIGH.

### D18 — Public website (OHD site; messaging rules)
- **DECISION:** New OpenHands public website intended to replace current site after independent
  review; temporary isolation allowed; integrate into canonical deployment once approved; website
  must communicate what CarbonTally does, not internal dev progress; capability claims truthful;
  positioning deliberately evolving (emissions data processing middleware).
- **STATUS:** CURRENT (DECIDED) · **AUTHORITY:** L1 · **SOURCE:** PO-REG §10.1–§10.4.
- **IMPLEMENTATION:** public routes in `frontend/src` (Landing, Pricing, Privacy, DataSecurity,
  Glossary, Contact, etc.).
- **GAP:** pending independent review/approval of the OHD site variant.
- **CONFIDENCE:** HIGH.

### D19 — Admin control plane = configurable operational policy
- **DECISION:** Admin Dashboard should be the central control plane for configurable operational
  policy (PEs, AI providers, factor sets, retention, subscriptions/billing, feature controls,
  operational policies); do not hard-code configurable business policy. **CL-66 D-P2-02:** V3
  `/ops` is the canonical staff/admin application; legacy admin CRA deprecated-but-quarantined
  (no new features).
- **STATUS:** CURRENT (D-P2-02 ratified; "dedicated /admin" re-assertion is UNRESOLVED — §39)
  · **AUTHORITY:** L1 · **SOURCE:** PO-REG §11.1; CL-66.
- **IMPLEMENTATION:** `/ops` Commercial/Entities/SLA/Staff/Roles/QC/Issues tabs; legacy `admin/`
  CRA not running locally (functional audit).
- **GAP:** unified admin console (P1-6 gap); admin CRA reachability; see §34.
- **CONFIDENCE:** HIGH (D-P2-02), PO DECISION on final surface.

### D20 — Customer final approval (locked)
- **DECISION:** Customer approval is the final customer-facing approval step; chain PE → CT → Customer.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §12; D2/D5.
- **IMPLEMENTATION:** owner/admin approve/reject gate; QC cannot approve (D-P2-03).
- **CONFIDENCE:** HIGH.


### D10 — Extraction target workflow (locked)
- **DECISION:** Upload → File Classification → PDF/Image → OCR when required → internal/local AI
  assisted extraction → human correction → mapping → PE Validation/Review/QC → CarbonTally
  Validation/Review/QC → Calculation → Evidence → Customer Final Approval.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §5.3 (LOCKED).
- **IMPLEMENTATION:** durable pipeline implements enqueue→ingest→extract→map→validate→calculate;
  gates + evidence present.
- **GAP:** end-to-end unattended success gated at extraction completeness (P1); see D09/D41.
- **CONFIDENCE:** HIGH.

### D11 — Do not over-claim production capability
- **DECISION:** Never publicly claim PDF/image/OCR/AI capabilities beyond what is actually
  production-wired and verified (engine exists ≠ route wired ≠ end-to-end tested ≠ production
  verified).
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §5.4 (LOCKED); D16.
- **IMPLEMENTATION:** website copy uses "AI-assisted help" with human review.
- **GAP:** functional audit found the durable auto pipeline gated (capability claim risk).
- **CONFIDENCE:** HIGH.

### D12 — Factor architecture: DEFRA + SEAI + customer custom, unified
- **DECISION:** Single unified factor architecture; DEFRA/SEAI/customer custom are not separate
  architectures; provider-independent architecture DECIDED (V3M-4); DEFRA/SEAI existing;
  ADEME/IPCC/EU deferred (country CHECK + natural-key widening only if they enter).
- **STATUS:** CURRENT · **AUTHORITY:** L1/L3 · **SOURCE:** PO-REG §6.1 (LOCKED); ADR-V3-015
  (DECIDED); Spec V3M-4.
- **IMPLEMENTATION:** `emission_factors` (7,049 rows) + SEAI; `customer_factors` table;
  provider/import architecture; no separate factor DB; no provider-specific calculation engine.
- **GAP:** deferred providers require T3 constraints before entry.
- **CONFIDENCE:** HIGH.

### D13 — Customer custom factors preserved; factor resolution precedence
- **DECISION:** Customers create their own factors (preserved); resolution precedence:
  (1) approved customer factor → (2) CarbonTally factor matching → (3) unresolved/manual review;
  approved customer factor never silently replaced; provenance traceable.
- **STATUS:** CURRENT · **AUTHORITY:** L1/L3 · **SOURCE:** PO-REG §6.2/§6.3/§6.4 (LOCKED);
  ADR-V3-002 D-cf-5 (DECIDED).
- **IMPLEMENTATION:** `customer_factors` org-scoped; matching precedence implemented
  (`factor_kind`, `customer_factor_id`); snapshot exactly-one-source CHECK.
- **GAP:** none material.
- **CONFIDENCE:** HIGH.

  self-discover/claim customer work.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §2.2 (LOCKED); Actor Model §6.1/§30.
- **IMPLEMENTATION:** D22 batch-level `manual_extraction_batches.entity_id` + `assign_batch`
  (internal staff only; `assigned_to` XOR `entity_id`).
- **GAP:** none material (manual-extraction batches lack entity scoping for multiple extraction
  companies — see D31).
- **CONFIDENCE:** HIGH.

### D05 — PE may perform extraction/mapping/validation/review/QC; CarbonTally secondary review; Customer final approval
- **DECISION:** Quality chain = PE QC → CarbonTally QC → Customer Final Approval.
- **STATUS:** CURRENT · **AUTHORITY:** L1 · **SOURCE:** PO-REG §2.3/§12 (LOCKED); D2/D5/D6.
- **IMPLEMENTATION:** entity extraction workspace; `customer_approved` gates; approval
  owner/admin-only (D5); QC limited authority (D-P2-03).
- **GAP:** full PE→CT→Customer mediated workflow threading not yet built (see D39).
- **CONFIDENCE:** HIGH.

### D06 — PE legal model: subprocessor
- **DECISION:** Customer → CarbonTally → PE → PE Staff; PEs are CarbonTally subprocessors subject
  to counsel confirmation and transfer frameworks.
- **STATUS:** CURRENT (product model; legal confirmation outstanding — PO-REG §17) · **AUTHORITY:**
  L1 · **SOURCE:** PO-REG §3.1 (LOCKED PRODUCT MODEL).
- **IMPLEMENTATION:** `processing_entities` table + contract metadata JSONB (Q1 deferred fields).
- **GAP:** commercial/contract schema deferred; legal gate per PO-REG §13.14.
- **CONFIDENCE:** HIGH (model), legal items open.


# 8. Application Boundary Decisions

| Boundary | Decision | Status |
|---|---|---|
| Public website | OHD site intended to replace current site after independent review; truthful capability claims only (D18) | CURRENT |
| Customer application | Frontend customer workspace; org roles owner/admin/member/viewer; final approval by customer (D26/D27/D28) | CURRENT |
| Individual Organization | Org settings surface (profile/members/facilities/assets/vehicles/suppliers/custom factors/activity/security) inside the customer app (D17/D26) | CURRENT |
| Consultant | Separate consultant workspace; multi-client; managed-service default (D29/D30/D31) | CURRENT |
| Processing Entity | Separate boundary; dedicated entity workspace; non-customer-facing (D23/D24/D25) | CURRENT (implementation partial: entity extraction surface exists; multi-entity manual-extraction scoping open) |
| CarbonTally Staff | Internal operations workspace `/ops` (D43/D48) | CURRENT |
| CarbonTally Admin | `/ops` is canonical (D-P2-02); legacy `/admin` CRA quarantined; "dedicated /admin" final surface = PO DECISION (§39) | CURRENT w/ open item |

# 9. Role and Permission Decisions

- Customer roles `owner|admin|member|viewer` (D26); owner/admin mutations + approval (D4/D5).
- Consultant roles `owner|manager|consultant|viewer` + `can_*` flags (D29); revocation roles
  Owner/Admin/Manager (D30).
- Staff roles `operator|reviewer|qc_specialist|admin|system_admin|pe_manager` with permission keys
  (D43); four access axes never interchangeable (D22).
- PE entity staff via `staff_profiles.entity_id` (D23); entity lifecycle gates `is_entity_member`
  (D42).

# 10. PE Architecture Decisions

D06 (subprocessor model), D07 (no download), D08 (Bangladesh gated), D23 (dedicated table,
Option B), D24 (work-assignment model), D25 (strictly non-customer-facing), D05 (PE
extract/map/validate/review/QC + CarbonTally secondary + customer final approval).

**INTENDED:** separate PE application/access boundary; possible eventual separate
deployment/domain/IP; PE-side admin/manager/staff roles.
**CURRENT:** PE workspace inside `/ops` (entity branch); entity API boundary; no separate
deployment. **CONCLUSION:** implementation is correct on access/isolation; the separate
deployment/domain and PE-side administration surfaces are NOT yet implemented (FUTURE).

# 11. Customer Architecture Decisions

# 12. Consultant Architecture Decisions

D29 (operating model), D30 (client access + revocation), D31 (hybrid managed-service model),
D51 (white-label), D32 (separate processing). Consultant clients do NOT automatically use
CarbonTally (D31 — CRITICAL CORRECTION recorded in Actor Model §37.1).

# 13. Staff/Operations Decisions

D43 (roles/permissions + system_admin superset + QC limited authority), D48 (workflow-first ops
hub), D35 (durable processing). `/ops` is the canonical staff app (D-P2-02).


---

# 14. CarbonTally Admin Decisions

D19 (control plane for configurable policy), D-P2-02 (/ops canonical; legacy admin quarantined),
D-P2-03 (QC limited), D41 (billing configurable). **Open:** final dedicated `/admin` surface (§39).

# 15. Backend/API Decisions

- V3 = extension of V2.1, not a rewrite (ADR principles §3.1); do not duplicate existing domain
  infrastructure (principle 2); prefer extending proven active structures (principle 3).
- FastAPI layered V3 (routers → repositories → domain/engines); consistent error envelope;
  `limit/offset/total` pagination; server-authoritative calculation.
- Calculation snapshots API-only for consultants (D33).

# 16. V3/Legacy Decisions

- V3 canonical; legacy temporary compatibility (PO-REG §9; AGENTS.md §9/§79).
- Remove obsolete legacy routes after dependency verification (D17).
- Legacy admin CRA quarantined, not deleted (D-P2-02).

# 17. Database Decisions

- Tenant root `organizations`; org-scoped data; RLS helpers (is_org_member/is_org_consultant/
  is_org_admin_or_owner/is_entity_member/is_org_active) (D22/D42/D46).

# 18. Processing/Worker Decisions

D35 (durable automatic processing, claim/retry/gates), D34 (dpq = technical state machine;
canonical Work Item layer pending), D38 (assignment attribution), D05 (quality chain).

# 19. Document/Storage Decisions

D44 (private bucket + signed URLs), D07 (PE no-download), D10 (document lifecycle).
**Document-state duality** (customer_documents vs organization_files vs dpq) is an unresolved
engineering item (§32).

# 20. AI Extraction Decisions

D09 (internal/local AI first; external controlled), D11 (no over-claiming), D16 (AI assist-only,
never authoritative). **Gap:** AI extraction not wired into the durable pipeline (D09
implementation gap).


D26 (org roles), D27 (participation layers), D28 (approver owner/admin), D13/D36 (customer
factors), D20 (final approval), D32 (separate from internal ops). Customer app is the live
frontend workspace (§8).

# 21. Calculation Decisions

Server-authoritative calculation (D33); immutable snapshots with provenance (D15/D45);
unit normalisation + methodology derivation are engineering requirements (functional audit
defects B3/B4).

# 22. QC/Review Decisions

D05 (PE QC → CT QC → Customer approval), D-P2-03 (QC never customer-approval), D28 (customer
approver owner/admin), D37 (issues lifecycle).

# 23. Audit/Provenance Decisions

D15 (row-level traceability, immutable evidence), D45 (evidence traceability), D46 (audit
immutability migration); audit/activity tables remain separate (known decision).

# 24. Data Retention Decisions

D16/N3/D-P2-04 (configurable; no invented durations; destructive enforcement deferred).

# 25. Billing/Subscription Decisions

D41 (provider-neutral, configurable, GBP indicative, no live provider integration).

# 26. UI/UX Decisions

D48 (workflow-first navigation + split-screen workbench + responsive), D49 (master data),
D26/D27/D28 (customer UX), D29/D30/D31 (consultant UX), D23/D24/D25 (PE UX), D43/D48 (staff/admin UX).

# 27. Design System Decisions

---

# 28. DataTable/Pagination/Search/Sort/Filter Decisions

- Known decision #21: evaluate for canonical standardisation rather than uncontrolled duplication.
- Uniform server-side `limit/offset/total` contract implemented; DataTable is the canonical table
  component; ops queues still use parallel markup (convergence debt, engineering).
- **STATUS:** engineering direction, not a ratified PO decision.

# 29. Security Decisions

D42 (RLS/tenant isolation; FORCE RLS deferred), D07/D25 (PE boundary), D44 (private storage),
D52 (public DataSecurity page), AGENTS.md §44–§45 (security testing matrix; frontend never a
security boundary).

# 30. Infrastructure Decisions

- Supabase (Postgres/Auth/Storage/Realtime) + FastAPI + React/Vercel topology (TechnologyStack;
  architecture reports).
- PE may eventually use a separate deployment/domain/IP (known decision; FUTURE).
- Local investor-demo stack + credential mechanism (D53).
- QA Harness independent verification (AGENTS.md §51–§53; `qa_harness/`).

- Factor baseline 7,049 rows immutable; no destructive reconstruction (known decisions; D46).
- Additive V3 migrations (V3M-1…11) preserve existing data (D46).
- Customer factors dedicated table (D36); snapshot provenance O1 (D15/D45).

# 31. Decisions Intentionally Deferred

| Item | Status | Authority evidence |
|---|---|---|
| Retention destructive enforcement (periods, export-before-delete, Storage deletion) | DEFERRED to dedicated phase | D-P2-04; D15; N3; ADR-V3 §7 |
| Force RLS application | DEFERRED to separate security investigation | known decision; ADR-V3-010 |
| ADEME/IPCC/EU residual factor providers | DEFERRED import tasks (T3 constraints) | ADR-V3-015; Spec V3M-4 |
| Canonical Work Item domain + queue consolidation (processing_queue family retirement) | DEFERRED until dependency chain completes | ADR-V3-003/016 |
| Payment-provider adapters (PayPal/Wise/card) | FUTURE behind provider-neutral interface | D11/D37 |
| Full white-label rendering (reports/email/domains/portal) | FUTURE | D14; Actor Model §37 |
| Consultant in-place direct-customer transition + export/import | FUTURE / NOT IMPLEMENTED | Actor Model §37 |
| PE separate deployment/domain/IP | FUTURE (possible) | known decision |
| Legacy route removal + legacy admin retirement | GATED on dependency inventory | D17; AGENTS.md §79; CL-66 |
| PE contract/commercial metadata schema | DEFERRED to V3 schema design | ADR-V3-001 Q1 |

# 32. Decisions Still Unresolved

| Item | Nature | Evidence |
|---|---|---|
| Final admin control-plane surface: dedicated `/admin` V3 surface vs `/ops` | UNRESOLVED (PO DECISION REQUIRED) | CL-66 D-P2-02 vs current product-requirement wording (§39) |
| Entity-scoped PE ↔ CarbonTally operational messaging | UNRESOLVED (PO DECISION REQUIRED; N1 model approved, implementation decision open) | PE Messaging PO Decision (2026-08-31); N1 |
| Locations distinct physical entity | PO DIRECTION RESOLVED; ENGINEERING DECISION on representation | N2 |
| Document-state single source (`customer_documents` vs `organization_files` vs dpq) | ENGINEERING DECISION | functional/forensic audits |
| Manual-extraction multi-entity scoping ("multiple extraction companies") | ENGINEERING GAP | Actor Model §6.2 |
| Name-string `require_admin`/`is_admin` over-grant hardening | REQUIRES ENGINEERING DECISION before entity provisioning at scale | Actor Model §35.5; reconciliation §27 |
| Component/DataTable convergence scope | ENGINEERING DIRECTION (not yet a PO decision) | known decision #21 |

# 33. Conflicting Historical Decisions

1. **Customer-factor self-approval.**
   - Document A (ADR-V3-002 v1.1, D-cf-3): "cannot approve their own factor (self-approval prohibited)".
   - Later PO clarification (AGENTS.md §16): "Customer Owner MAY self-approve a custom factor."
   - **CONCLUSION: SUPERSEDED** by the later PO clarification. CURRENT = owner self-approval allowed;

4. **PE messaging.**
   - N1 (AGENTS.md §28): PE messaging = "operational CarbonTally messaging" (model approved).
   - Phase B note (2026-08-31): "PO DECISION REQUIRED" for entity-scoped PE messaging implementation.
   - **CONCLUSION:** N1 boundary is CURRENT; whether to implement entity-scoped PE threads is a
     PO decision (open).

5. **PO register copies.**
   - `docs/audit/openhands/...v1.md` and `docs/ChatGPT/...v1.md` are md5-identical (26-Aug register).
   - `docs/audit/openhands/ui-ux/...v1.md` is a DIFFERENT document (D1–D21 frozen) whose header
     claims its authoritative copy is in `docs/ChatGPT/` — which currently holds the other register.
   - **CONCLUSION: UNRESOLVED documentation inconsistency** (informational; does not change any
     decision). The D1–D21 source-of-record should be copied/designated explicitly.

6. **Legacy route removal vs retention of legacy.**
   - PO-REG §9.1: "Remove all obsolete legacy routes."
   - AGENTS.md §79 + CL-66: keep legacy until dependency inventory completes.
   - **CONCLUSION: reconciled —** the removal direction stands; the gate (dependency inventory)
     governs timing. Not a product conflict.

# 34. Current Implementation vs Approved Design

| # | INTENDED / APPROVED | CURRENT IMPLEMENTATION | CONCLUSION |
|---|---|---|---|
| 1 | Separate PE application/access boundary (dedicated, possibly separate deployment) | PE workspace inside `/ops`; entity API boundary; no separate deployment/domain | Partially matches; separate deployment + PE-side admin surfaces NOT built (FUTURE) |
| 2 | Automatic processing with AI-assisted extraction (internal/local AI first) | Durable pipeline uses deterministic extraction; AI engine wired only to legacy workflow engine | Does not yet match (gap) |
| 3 | Document preview renders source inline (D19/D32 intent) | Signed URLs download-scoped → preview blank in browser (functional audit P1) | Defect vs intent |
| 4 | Canonical shared table foundation; no uncontrolled duplication | DataTable + v3-ops-table + raw tables coexist | Convergence gap (engineering) |
| 5 | Admin control plane: /ops canonical (D-P2-02) | /ops tabs functional; legacy admin CRA not running locally | Matches D-P2-02; dedicated-/admin question open |
| 6 | Consultant client lifecycle + in-place direct-customer transition | Relationship lifecycle + revocation implemented; transition/export NOT implemented | Partially matches |
| 7 | Full white-label rendering | Foundation implemented only | Partially matches (FUTURE) |
| 8 | Retention configurable; destructive deferred | Settings API persists config; no destructive deletion | Matches |
| 9 | 7,049 emission factors preserved; no destructive schema reconstruction | Verified intact; additive migrations | Matches |

---

# 35. Architecture Requirements That Must Be Preserved

1. **PE is a third-party manual-processing company, NOT a customer** (D23/D24/D25) — dedicated
   table, separate access boundary, work-assignment based, strictly non-customer-facing.
2. **PE may eventually have a separate deployment/domain/IP** (known decision).
3. **PE-side admin/manager/staff roles** (Actor Model §6; ADR-V3-001) — final RBAC names deferred
   but the role families are required.
4. **CarbonTally Admin separate from PE Admin; Staff/Operations separate from Admin** (D43;
   AGENTS.md §13/§14).
5. **Customers use the customer application** (D26/D27/D28).
6. **Consultants use a consultant workspace and manage multiple clients** (D29).
7. **Consultant clients do not automatically become CarbonTally users** (D31 — critical).
8. **Revoking a consultant-client relationship does NOT delete/anonymize/destroy client data**
   (D30).
9. **Consultant Owner/Admin/Manager may revoke; Member/Viewer may not** (D30, WS6/SEC-0003).
10. **Customer/consultant processing and internal operations are separate** (D32).
11. **Calculation snapshots are API-only for consultants** (D33).
12. **V3 canonical; legacy temporary** (D17; AGENTS.md §9).
13. **7,049 emission factors preserved; no destructive schema reconstruction** (D46; known
    decisions).
14. **Existing D21 UI primitives are the UI foundation; no shadcn assumption** (D47).
15. **DataTable/pagination/search/sort/filter evaluated for canonical standardisation** (known
    decision #21).
16. **Four access axes never interchangeable** (D22).
17. **Customer final approval; PE QC → CT QC → Customer** quality chain (D05/D20).
18. **Factor precedence: approved customer → CarbonTally → manual review** (D13/D36).
19. **Row-level traceability + immutable evidence** (D15/D45).
20. **Retention configurable, server-side, no invented durations, destructive deferred**
    (D16/N3/D-P2-04).
21. **AI assist-only, never authoritative** (D16/D09).
22. **No direct customer↔PE communication; all mediated by CarbonTally** (D25/N1).
23. **Private documents storage + signed URLs; PE no-download** (D44/D07).
24. **Security: UI never the security boundary; server-side authorization + RLS** (D42; AGENTS.md
    §44).
25. **DataSecurity is a public page** (D52).

# 36. Requirements That Are Obsolete

| Requirement | Obsolete because |
|---|---|
| "Consultant Client uses CarbonTally through the Consultant" | EXPLICITLY corrected (Actor Model §37.1): client does not automatically access CarbonTally |
| "One account per company; multi-company is Version 2" (early Final strategy) | Superseded by ratified D3/D8/D29 consultant model |
| Beta-only acquisition gate as the only signup | Superseded by D35 self-service signup; beta is a controlled cohort |
| Public USD pricing baseline | Superseded by D12 GBP indicative |
| Hard-coded Stripe billing columns | Superseded by D11/D37 provider-neutral billing |
| Legacy `processing_assignments`/`reassignment_history` as the assignment mechanism | Dormant; D22 uses V3 audit_trail; retirement per ADR-V3-005/016 |
| `customer_documents` as the sole document record (assumed) | V3 upload path writes `organization_files` + dpq; duality unresolved (§32) |
| Beta infrastructure/tables not required by V3 | PO-REG §1.3/§9.2 — remove if not required |
| Static HTML UI mockups (`docs/architecture/UI*`) | Pre-D21; obsolete |

# 37. Requirements That Were Proposed But Never Approved

- **Multi-Company Management "Version 2" strategy** (`docs/Final/…Multi-Company…`): PROPOSAL
  (Aug 2) — superseded by ratified consultant model.
- **Consultant Firm Team Management doc**: PROPOSAL — superseded by `consultant_firm_members`.
- **UI_UX_OPTION_A/B/C** individual options: each was a PROPOSAL; the approved composition is
  **B + C + A** (workflow-first + modern/guided customer + enterprise admin) — options preserved
  as historical.
- **Full white-label rendering, co-branded client portal, custom domains**: PROPOSED/FUTURE —
  not approved beyond the white-label foundation.
- **Payment-provider adapters (PayPal/Wise/card)**: PROPOSED/FUTURE — not implemented or claimed.
- **Export/import capability**: PROPOSED/FUTURE — not approved beyond direction.
- **Entity-scoped PE operational messaging threads**: PROPOSED — PO decision outstanding (§39).
- **Dedicated `/admin` V3 control-plane application** (as a NEW build): not ratified — CL-66 chose
  `/ops`; the requirement wording is open (§39).
- **Bangladesh PE processing**: POLICY GATED, not approved for live work.

| 10 | Calculation snapshots API-only for consultants | Immutable server-side snapshots; consultant read-only | Matches |

     Member not unless separately authorized; Viewer not.

2. **D-numbering schemes (Actor-era vs frozen UX register).**
   - Actor model (2026-08-20): D15=consultant grant, D19=consultant transition, D21=white-label,
     D22=PE assignment.
   - Frozen register (2026-08-24): D15=Data Retention, D19=Workbench, D21=Design System.
   - Frozen register asserts "no duplicate decision numbers were created"; both schemes exist in
     the repo and migrations use the Actor-era numbers.
   - **CONCLUSION: UNRESOLVED (naming collision).** The blueprint must reference decisions by name
     (or by both IDs) to avoid ambiguity. Recommend the frozen D1–D21 names for UX/product decisions
     and migration-era names (D15/D19/D21/D22/D27/D32/D33/D35/D37) for the implemented work items.

3. **Admin control plane surface.**
   - CL-66 D-P2-02 (2026-08-30): V3 `/ops` is the canonical staff/admin app; legacy `/admin` CRA
     deprecated/quarantined.
   - Current product-requirement wording: "CarbonTally Admin: dedicated `/admin` control-plane
     application/surface."
   - **CONCLUSION: UNRESOLVED — PO DECISION REQUIRED** (§39). Current ratified decision = `/ops`.


D47/D49 (existing D21 primitives canonical; no shadcn assumption); D21 token system; component
convergence is engineering direction.

# 38. FINAL CURRENT DECISION SET

These are the only decisions that should currently be treated as authoritative. They are the
foundation for the Architecture Blueprint.

**Product model**
- F-1 Market: UK / IE / EU-EEA, gradual launch; public signup controlled; self-service onboarding
  (D02, D35).
- F-2 One account, one role; four access axes never interchangeable (D03, D22).
- F-3 PE = third-party manual processor, not a customer; dedicated boundary; work-assignment
  based; CarbonTally controls assignment; entity receives only assigned work (D23/D24).
- F-4 PE strictly non-customer-facing; no direct customer↔PE communication; all mediated (D25).
- F-5 PE no-download of source documents; private storage + signed URLs (D07/D44).
- F-6 Quality chain: PE QC → CarbonTally QC → Customer final approval (D05/D20).
- F-7 Customer org roles owner/admin/member/viewer; owner/admin approve; viewer read-only
  (D26/D27/D28).
- F-8 Consultant = first-class operator, multi-client, managed-service default; clients do NOT
  automatically use CarbonTally; revocation by Owner/Admin/Manager; revocation never deletes data
  (D29/D30/D31).
- F-9 Customer/consultant processing separate from internal operations (D32).
- F-10 Calculation snapshots API-only for consultants; server-authoritative calculation (D33).
- F-11 Factor architecture unified (DEFRA/SEAI/custom); 7,049 factors preserved; precedence
  approved-customer → CarbonTally → manual review (D12/D13/D36/D46).
- F-12 Customer Owner MAY self-approve a custom factor (later PO clarification, D14).
- F-13 Retention configurable, server-side, no invented durations; destructive enforcement
  deferred (D16/N3/D-P2-04).
- F-14 AI assist-only, never authoritative; internal/local AI first; external AI controlled
  (D09/D11/D16).
- F-15 Billing provider-neutral, configurable, GBP indicative pre-launch (D41).
- F-16 DataSecurity is a public page (D52).

**Architecture**
- F-17 V3 canonical; legacy temporary; legacy routes removed only after dependency inventory
  (D17; AGENTS.md §9/§79).
- F-18 V3 = extension of V2.1, not a rewrite; do not duplicate existing domain infrastructure;
  extend proven structures (ADR principles).
- F-19 Layered FastAPI (routers → repositories → domain/engines); consistent error envelope;
  uniform `limit/offset/total` pagination; server-authoritative business rules.
- F-20 Durable, resumable, idempotent automatic processing with manual-review gates (D35).
- F-21 Row-level traceability; immutable calculation evidence; audit/activity tables separate

---

# 39. PRODUCT OWNER DECISIONS STILL REQUIRED

Only genuinely unresolved items. Do not re-list decided issues.

1. **Admin control-plane surface (P0 for the blueprint).** Ratified D-P2-02 makes V3 `/ops` the
   canonical staff/admin application and quarantines the legacy `/admin` CRA. The current product
   requirement wording calls for a "dedicated `/admin` control-plane application/surface".
   Decide: (a) keep `/ops` as the canonical admin surface (current decision), (b) build a new
   dedicated `/admin` V3 control-plane surface, or (c) revive/re-platform the legacy `admin/`
   CRA on the V3 API. This determines the §8 boundary and the admin application's shape.
2. **Entity-scoped PE ↔ CarbonTally operational messaging.** N1 approves the *boundary* (PE
   operational messaging only). Decide whether to implement entity-scoped conversation threads
   (schema + RLS + PE workspace surface) or keep PE messaging denied (current 403).
3. **Legacy-route removal gate.** Confirm the dependency inventory is the trigger for removing the
   405 legacy endpoints and the quarantined admin CRA, and the target timeline.
4. **QC authority final form.** D-P2-03 limited QC to internal quality control. Confirm whether QC
   becomes its own permission (`can_qc`) or remains a global-admin gate in the final blueprint.
5. **AI extraction in the durable pipeline.** Confirm the OpenRouter/`AIExtractionEngine` provider
   architecture should power the durable automatic extraction stage (with deterministic fallback)
   and its cost posture, before wiring (D09 implementation).

---

# 40. RECOMMENDED INPUT TO FINAL ARCHITECTURE BLUEPRINT

The blueprint must implement **§38 F-1…F-32** as the authoritative decision set, honour the
**four access axes** (F-2), the **PE boundary** (F-3…F-6), the **consultant managed-service model**
(F-8), the **separation of customer/consultant processing from internal ops** (F-9), **server-
authoritative calculation with API-only consultant snapshots** (F-10), the **unified factor
architecture** (F-11), the **D21 UI foundation** (F-25/F-26), **RLS + server-side authorization**
(F-22), **durable automatic processing** (F-20), **configurable retention with deferred
destructive enforcement** (F-13), **provider-neutral billing** (F-15), and **N1 messaging
boundaries** (F-28). It must close the recorded implementation gaps (§34) as engineering work —
**not** as new decisions — and it must first obtain PO answers to §39.

**Timeline of decision eras (for the blueprint's history section):**
- **V1 era (Jun–Jul 2026):** RC1 schema; Kimi audits; early proposals (`docs/Final`).
- **V2.0 (Jul 2026):** changelog v2.0.0 route/tables additions.

## Appendix — Evidence index

Key quoted sources (all read in this reconstruction): PO-REG §1–§20; D1–D21 + N1–N3 register
§1–§28; ADR-V3-001/002/003/004/005/006/009/010/012/014/015/016; Spec §6.1/§8.1/§13/§16.5/§33;
Actor Model §3/§5.1/§6.1/§9/§13–§16/§24–§26/§30–§37; MASTER reconciliation §2/§27–§33; CL-66
§1–§6; PE Messaging PO Decision §1–§6; Platform Processing Master §3/§6–§8/§37/§43–§47;
V3M-1/V3M-8/V3M-9/V3M-10/V3M-11 migrations; `20260831040000` (WS6/SEC-0003); D32/D33/D35/D36/D37
reports; OHD persona/security/PE audits; Kimi RC1 audit.

## Safety confirmation

Read-only task. No application files, database, migrations, RLS, packages, configuration, tests,
Docker, or infrastructure were modified. No documents were deleted, renamed, moved, or edited
except the creation of this report. No commits or pushes.

## END OF FINAL PRODUCT DECISION REGISTER

- **RC2 base (Aug 2026):** `00000000000000_init_schema` … `2026080707` (import batches,
  calculation snapshots, domain events, factor aliases, dpq workflow columns, RLS).
- **V3 architecture (Aug 2026):** ADR register + Specification v1.0/v1.1 (Aug 11: D-cf-2/3/5,
  V3M-3, V3M-4 DECIDED).
- **Aug 20 2026:** ratified PE operating model, PE boundary, consultant commercial model, D15
  active-grant.
- **Aug 21 2026:** D22 PE work assignment + D21 white-label foundation implemented.
- **Aug 22 2026:** D24 entity management UI; D27 customer lifecycle.
- **Aug 23–24 2026:** D32 private storage; D1–D21 frozen UX register; D35 onboarding; D37 billing.
- **Aug 26 2026:** consolidated PO Decision Register v1.
- **Aug 28–31 2026:** V3M8 system_admin/pe_manager roles; V3M9 durable processing; V3M10/11 +
  audit immutability + tenant NOT NULL; CL-66 D-P2-02/03/04; WS6/SEC-0003 consultant revocation.
- **Sep 2026 (current):** product-functional audits; blueprint preparation.

  (D15/D45/D46).
- F-22 RLS + server-side authorization; UI never a security boundary; FORCE RLS deferred (D42).
- F-23 Private documents bucket + short-lived signed URLs; authz before signing (D44).
- F-24 Admin control plane: `/ops` is the canonical staff/admin app (D-P2-02); legacy admin CRA
  quarantined; QC limited authority (D-P2-03); system_admin superset (D43).
- F-25 D21 design system = existing `v3/components/ui` primitives; no shadcn assumption; DataTable
  standardisation evaluated (D47; known decision #21).
- F-26 Workflow-first navigation + split-screen top-nav workbench + responsive tray (D48).
- F-27 Master data hierarchy Organisation → Locations → Facilities → {Assets, Vehicles}; Suppliers
  org-scoped (D17/D49).
- F-28 Messaging N1 boundaries (customer support; consultant authorised-client; CT staff/admin;
  PE operational only) (D39).
- F-29 White-label = presentation/integration over existing platform; foundation implemented; full
  rendering future (D51).
- F-30 PE may eventually have separate deployment/domain/IP (known decision).
- F-31 Investor demo data and local credentials preserved; no destructive reset (D53).
- F-32 QA Harness independent verification required (AGENTS.md §51–§53).

