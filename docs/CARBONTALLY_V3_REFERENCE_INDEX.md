# CarbonTally V3 — Central Reference Index

**Purpose.** Single entry point for the CarbonTally V3 reference material that
must be shared across agents (Cline, OpenHands, OpenRouter/GPT and future
tools). This index maps every important document to its **category**,
**authority tier** and **status** so that an agent can determine, at a glance,
what it may rely on, what it must verify, and what is explicitly *not* an
instruction to implement.

**Maintainer note.** This index is updated when reference documents are
added, superseded or retired. It is itself a living document and should be
kept in sync with the canonical repository.

---

## 1. Authority hierarchy

Documents in this repository belong to distinct authority tiers. A document's
tier decides how much weight it carries relative to the code:

| Tier | Meaning | Weight |
|---|---|---|
| 1. PRODUCT OWNER DECISION | Explicit decisions by the Product Owner (Decision Register). Binding unless a later PO decision supersedes it. | Highest — binding |
| 2. ARCHITECTURE / CURRENT IMPLEMENTATION | Architecture records that describe the current canonical implementation (ADR register, actor/workspace access model, schema/RLS docs, API docs). | Authoritative for *current* design; must match the code |
| 3. IMPLEMENTATION / VERIFICATION EVIDENCE | Reports of what was built, migrated, verified or QA'd (Cline phase/finalization reports, QA reports, release reports). | Evidence — verify against current code before relying |
| 4. SECURITY / REGULATORY AUDIT | Independent security, privacy, data-residency and legal-policy audits. | Evidence + recommendation; **not** automatic requirements |
| 5. RESEARCH / RECOMMENDATION | Factor research, market/legal policy research, candidate data packages. | Non-binding; requires explicit PO approval to implement |
| 6. HISTORICAL / SUPERSEDED | Older records superseded by newer ones, or describing removed behavior. | Reference only — do not treat as current |

**Rules of thumb:**

- An audit finding does **not** automatically become a Product Owner decision.
- A research recommendation does **not** automatically become a CarbonTally
  requirement.
- A historical document does **not** automatically represent the current
  architecture.

> **Before implementing or recommending a CarbonTally architectural,
> authorization, workflow, UI/UX, Processing Entity, regulatory,
> emission-factor, billing, security, extraction, mapping or calculation
> change, review the relevant documents in this index and verify the current
> canonical implementation.**

Verification always means checking against, in order:

1. the latest Product Owner decisions (`docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`);
2. the current canonical code (`backend/`, `frontend/`);
3. the current database/schema and RLS implementation (`supabase/migrations/`);
4. current implementation/verification evidence (`docs/audit/cline/`, `docs/audit/openhands/`).

---

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| AUTHORITATIVE | Binding decision or canonical record of current implementation |
| CURRENT | Describes the present state; consistent with the code |
| AUDIT EVIDENCE | Independent audit record; findings require verification |
| RESEARCH | Non-binding research; requires PO approval before implementation |
| IMPLEMENTATION EVIDENCE | Record of work performed / verified |
| HISTORICAL | Older record; kept for reference |
| SUPERSEDED | Replaced by a newer document |
| DUPLICATE | Same/similar content exists elsewhere |
| NOT FOR IMPLEMENTATION | Explicitly not a specification to implement |

---

## 3. Category index

1. **Product Owner decisions** — binding decisions (Decision Register).
2. **Architecture** — ADR register, actor/workspace/access model, tech stack, RBAC, API docs.
3. **Database / data model** — schema documentation, migration records, RLS records.
4. **Security / RLS** — security audits, RLS and authorization analyses, hardening reports.
5. **Regulatory / privacy / data residency** — UK/Ireland/EU GDPR, data residency, transfer research.
6. **Processing Entity policy** — PE legal/policy/operational research and the no-download decision.
7. **Extraction / mapping / calculation** — capability audits and recovery audits.
8. **CSV / Excel mapping** — capability records for spreadsheet ingestion/mapping.
9. **Custom Emission Factors** — customer custom factor capability and impact analysis.
10. **UI/UX** — authenticated platform audit, website pre-launch reports, visual QA.
11. **Emission-factor research** — multiregional and UK-launch factor research packages.
12. **Implementation / QA evidence** — Cline phase and finalization reports, QA reports.
13. **Historical / superseded material** — legacy records kept for reference.

---

## 4. Document table

### 4.1 Product Owner decisions

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` | Product Owner decisions | PRODUCT OWNER DECISION | The current PO baseline: launch markets, one-account-one-role, Processing Entity no-download, portal processing, quality chain (PE QC → CT QC → Customer Final Approval), legacy-route retirement, factor architecture, website policy, engineering priorities | AUTHORITATIVE |

### 4.2 Architecture

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` | Architecture | ARCHITECTURE / CURRENT IMPLEMENTATION | ADR-V3-001…016 and D-series records | CURRENT |
| `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | Architecture | ARCHITECTURE / CURRENT IMPLEMENTATION | Authoritative actor/workspace/access analysis (§§30–50) incl. D22/D23/D25/D26/D32/D37 | CURRENT |
| `docs/architecture/API_DOCUMENTATION.md`, `API_ENDPOINTS.md`, `API_SUMMARY.md` | Architecture | ARCHITECTURE / CURRENT IMPLEMENTATION | API surface reference | CURRENT |
| `docs/architecture/CarbonTally_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` | Architecture | ARCHITECTURE / CURRENT IMPLEMENTATION | Canonical terminology and domain vocabulary | CURRENT |
| `docs/architecture/ARCHITECTURE_DECISIONS.md`, `TechnologyStack.md`, `RBAC.md`, `filestructure.md`, `changelog.md` | Architecture | ARCHITECTURE / CURRENT IMPLEMENTATION | Supporting architecture/decisions records | CURRENT / HISTORICAL (verify per file) |
| `docs/architecture/UI/`, `docs/architecture/UI2/` | Architecture | ARCHITECTURE / CURRENT IMPLEMENTATION | Static HTML UI mockups / design demos (legacy reference; not the live app) | HISTORICAL |

### 4.3 Database / data model

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `CarbonTally_DB_Schema_V3M2.sql` (repo root) | Database / data model | ARCHITECTURE / CURRENT IMPLEMENTATION | V3M2 schema snapshot | CURRENT |
| `docs/architecture/DB_Migration/*.sql`, `MIGRATION_*.sql` | Database / data model | ARCHITECTURE / CURRENT IMPLEMENTATION | Migration records (documentation of the migration sequence) | HISTORICAL / CURRENT (verify per file) |
| `supabase/migrations/**` | Database / data model | ARCHITECTURE / CURRENT IMPLEMENTATION | **The authoritative schema + RLS source of truth** | AUTHORITATIVE |

### 4.4 Security / RLS

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/CARBONTALLY_V3_PE_SECURITY_AUDIT.md` | Security / RLS | SECURITY / REGULATORY AUDIT | Processing-Entity workforce authorization chain, document/storage security, RLS storey, assignment/QC gates, issues storey | AUDIT EVIDENCE |
| `docs/audit/openhands/CARBONTALLY_V3_INDEPENDENT_PRODUCT_PLATFORM_AUDIT_FLASH.md` | Security / RLS | SECURITY / REGULATORY AUDIT | Independent product & platform security audit (flash) | AUDIT EVIDENCE |
| `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_PLATFORM_UI_UX_AUDIT.md` | Security / RLS + UI/UX | SECURITY / REGULATORY AUDIT + UI/UX | Authenticated platform UI/UX audit incl. role-gating, document access and RLS enforcement verification | AUDIT EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_MASTER_COMPLETION_SECURITY_HARDENING_REPORT.md` | Security / RLS | IMPLEMENTATION / VERIFICATION EVIDENCE | Master completion + security hardening record | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_GIT_HISTORY_SECRET_REMEDIATION_EXECUTION_REPORT.md`, `…_EXPANDED_SCOPE_REPORT.md`, `…_PLAN.md` | Security / RLS | IMPLEMENTATION / VERIFICATION EVIDENCE | Git-history secret remediation plan and execution records (no values reproduced) | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT.md` | Security / RLS | IMPLEMENTATION / VERIFICATION EVIDENCE | Local Supabase setup and key-handling audit | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_ARCHITECTURE_CONFORMITY_GATE.md` | Security / RLS | IMPLEMENTATION / VERIFICATION EVIDENCE | Architecture conformity gate incl. service-role/RLS analysis | IMPLEMENTATION EVIDENCE |

### 4.5 Regulatory / privacy / data residency

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/CARBONTALLY_V3_INDEPENDENT_REGULATORY_AND_DATA_RESIDENCY_AUDIT.md` | Regulatory / privacy / data residency | SECURITY / REGULATORY AUDIT | UK/EU GDPR, data-residency, transfer and PE-processing regulatory audit | AUDIT EVIDENCE |
| `docs/Final_Kimi/` (Kimi UK/IE compliance audit reports) | Regulatory / privacy | SECURITY / REGULATORY AUDIT | Kimi agent UK/IE compliance audit reports | AUDIT EVIDENCE (verify latest version) |

### 4.6 Processing Entity policy

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/CARBONTALLY_V3_BANGLADESH_PROCESSING_ENTITY_LEGAL_POLICY_RESEARCH.md` | Processing Entity policy | REGULATORY / POLICY RESEARCH | Bangladesh PE legal/policy/operational research; distinguishes legal obligation, regulatory guidance, contractual requirement, customer expectation, internal policy, future architecture | RESEARCH / NOT LEGAL ADVICE |
| `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (§§2–3) | Processing Entity policy | PRODUCT OWNER DECISION | No-download decision, assignment control, quality chain | AUTHORITATIVE |

### 4.7 Extraction / mapping / calculation

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/extraction-mapping-calculation/CARBONTALLY_V3_EXTRACTION_MAPPING_CALCULATION_CAPABILITY_AUDIT.md` | Extraction / mapping / calculation | IMPLEMENTATION / AUDIT EVIDENCE | Capability audit of extraction→mapping→calculation in the current code | AUDIT EVIDENCE (not a rewrite instruction) |
| `docs/audit/openhands/extraction-recovery/CARBONTALLY_V3_HISTORICAL_EXTRACTION_RECOVERY_AUDIT.md` | Extraction / mapping / calculation | IMPLEMENTATION / AUDIT EVIDENCE | Historical PDF/image/OCR extraction recovery audit (PO §5.2 engineering direction) | AUDIT EVIDENCE |

### 4.8 CSV / Excel mapping

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (§5.1) | CSV / Excel mapping | PRODUCT OWNER DECISION | CSV/Excel/XLSX mapping is an existing capability and must be preserved | AUTHORITATIVE |
| `docs/audit/openhands/extraction-mapping-calculation/CARBONTALLY_V3_EXTRACTION_MAPPING_CALCULATION_CAPABILITY_AUDIT.md` | CSV / Excel mapping | IMPLEMENTATION / AUDIT EVIDENCE | Verifies the current CSV/Excel ingestion state | AUDIT EVIDENCE |

### 4.9 Custom Emission Factors

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (§6.2) | Custom Emission Factors | PRODUCT OWNER DECISION | Customer Custom Emission Factors already implemented; preserve | AUTHORITATIVE |
| `docs/audit/CarbonTally_V3_Customer_Factors_Impact_Analysis.md` | Custom Emission Factors | IMPLEMENTATION / AUDIT EVIDENCE | Impact analysis of the customer-factor capability | AUDIT EVIDENCE |

### 4.10 UI/UX

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_PLATFORM_UI_UX_AUDIT.md` | UI/UX | SECURITY / REGULATORY AUDIT + UI/UX | Authenticated platform UI/UX + role-model + workflow audit | AUDIT EVIDENCE |
| `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md` | UI/UX | IMPLEMENTATION SPECIFICATION (proposed) | Implementation-ready UX architecture + IA for the authenticated platform (customer, consultant, staff, PE, admin); requires PO approval of §22 decisions before implementation | PROPOSED |
| `docs/audit/openhands/CARBONTALLY_V3_WEBSITE_PRELAUNCH_REFACTOR_REPORT.md` | UI/UX (website) | IMPLEMENTATION / AUDIT EVIDENCE | Public website pre-launch refactor report (second pass) | IMPLEMENTATION EVIDENCE |
| `docs/audit/openhands/CARBONTALLY_V3_WEBSITE_PRELAUNCH_REFACTOR_REPORT_FLASH.md` | UI/UX (website) | IMPLEMENTATION / AUDIT EVIDENCE | Public website pre-launch refactor report (flash pass) | IMPLEMENTATION EVIDENCE |
| `docs/audit/openhands/QA_REPORT_V3_FINAL.md` | UI/UX (website) | IMPLEMENTATION / VERIFICATION EVIDENCE | Final public-site UX/visual QA report | IMPLEMENTATION EVIDENCE |
| `docs/audit/openhands/screenshots/**` | UI/UX (website) | IMPLEMENTATION / VERIFICATION EVIDENCE | Reference screenshots for the website audit packages (root, `v2/`, `final/`) | IMPLEMENTATION EVIDENCE |

### 4.11 Emission-factor research

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/multiregional-factors/CARBONTALLY_V3_MULTIREGIONAL_FACTOR_CANDIDATES.json` | Emission-factor research | RESEARCH / RECOMMENDATION | Candidate factor metadata (research artifact; NOT a seed file) | RESEARCH / NOT FOR IMPLEMENTATION |
| `docs/audit/openhands/multiregional-factors/CARBONTALLY_V3_MULTIREGIONAL_FACTOR_RESEARCH_REPORT.md` | Emission-factor research | RESEARCH / RECOMMENDATION | Multiregional factor research report | RESEARCH / NOT FOR IMPLEMENTATION |
| `docs/audit/openhands/multiregional-factors/CARBONTALLY_V3_MULTIREGIONAL_FACTOR_SOURCE_MATRIX.md` / `.xlsx` | Emission-factor research | RESEARCH / RECOMMENDATION | Factor source matrix (markdown + spreadsheet) | RESEARCH / NOT FOR IMPLEMENTATION |
| `docs/audit/openhands/uk-launch-factor-research/CARBONTALLY_V3_UK_LAUNCH_FACTOR_CANDIDATES.json` | Emission-factor research | RESEARCH / RECOMMENDATION | UK-launch candidate factor metadata | RESEARCH / NOT FOR IMPLEMENTATION |
| `docs/audit/openhands/uk-launch-factor-research/CARBONTALLY_V3_UK_LAUNCH_FACTOR_COVERAGE_RESEARCH.md` | Emission-factor research | RESEARCH / RECOMMENDATION | UK-launch factor coverage gap research | RESEARCH / NOT FOR IMPLEMENTATION |
| `docs/audit/openhands/uk-launch-factor-research/CARBONTALLY_V3_UK_LAUNCH_FACTOR_GAP_MATRIX.xlsx` | Emission-factor research | RESEARCH / RECOMMENDATION | UK-launch factor gap matrix | RESEARCH / NOT FOR IMPLEMENTATION |

> **Factor-data clarification.** The production database currently holds
> `7049` rows in `emission_factors`. The research packages above are
> **not** seed files; do not import them, and do not treat the previously
> observed `emission_factors = 0` in an isolated test environment as evidence
> of lost production factor data.

### 4.12 Implementation / QA evidence

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/cline/CARBONTALLY_V3_PLATFORM_FINALIZATION_REPORT.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | Latest Cline platform finalization report | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_4_REPORT.md` … `PHASE_8_REPORT.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | V3 phase implementation reports | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_D20_D37_RELEASE_STAGING_REPORT.md`, `…_RELEASE_COMMIT_PUSH_REPORT.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | D20–D37 release staging and commit/push records | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_FINAL_PRE_COMMIT_VERIFICATION.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | Final pre-commit verification | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_FRONTEND_RUN_REPORT.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | Frontend run verification | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_IDENTITY_WORKSPACE_ONBOARDING_AUDIT.md`, `…_IMPLEMENTATION_REPORT.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | Identity/workspace/onboarding audit + implementation | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_N8N_PACKAGE_CHANGE_INVESTIGATION.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | n8n package change investigation | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CARBONTALLY_V3_RESUMPTION_AFTER_POWER_LOSS.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | Resumption record after power loss | IMPLEMENTATION EVIDENCE |
| `docs/audit/cline/CarbonTally_V3_Phase1_Backend_Consolidation_Report_v1.0.md`, `…_Processing_Workflow_Report_v1.0.md`, `…_New_Capabilities_Report_v1.0.md`, `…_Legacy_Capability_Reimplementation_Report_v1.0.md`, `…_Local_Codebase_Product_UX_Architecture_Audit_v1.0.md` | Implementation / QA | IMPLEMENTATION / VERIFICATION EVIDENCE | V3 backend consolidation / workflow / capability / legacy reimplementation / local audit records | IMPLEMENTATION EVIDENCE |

### 4.13 Historical / superseded material

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/Final/`, `docs/Final_Kimi/` (older variants), `docs/cline/` (older v2.1 records), `docs/architecture/UI/` (older mockups) | Historical | HISTORICAL / SUPERSEDED | Pre-V3 and legacy reference material | HISTORICAL / SUPERSEDED (verify per file) |
| Older website refactor report variants | Historical | HISTORICAL / SUPERSEDED | `CARBONTALLY_V3_WEBSITE_PRELAUNCH_REFACTOR_REPORT_FLASH.md` (2026-08-24) precedes `CARBONTALLY_V3_WEBSITE_PRELAUNCH_REFACTOR_REPORT.md` (2026-08-25); both are kept for evidence, the 2026-08-25 report is the later pass | DUPLICATE / SUPERSEDED (relationship documented) |
| `docs/audit/openhands/extraction-recovery/CARBONTALLY_V3_HISTORICAL_EXTRACTION_RECOVERY_AUDIT.md` | Historical | IMPLEMENTATION / AUDIT EVIDENCE | Records historical extraction capability; do not treat as current code state | HISTORICAL / AUDIT EVIDENCE |

### 4.14 Customer-facing product documentation

| Document | Category | Authority | Purpose | Status |
|---|---|---|---|---|
| `docs/audit/openhands/CARBONTALLY_V3_CUSTOMER_FAQ.md` | Customer-facing product documentation | CURRENT PRODUCT (evidence-backed) | Plain-English FAQ of what CarbonTally does today, what is planned, and what it does not do; every claim traced to the capability matrix | CURRENT |
| `docs/audit/openhands/CARBONTALLY_V3_FAQ_CAPABILITY_MATRIX.md` | Internal evidence matrix | AUDIT / IMPLEMENTATION EVIDENCE | Backing matrix for the customer FAQ: claim → evidence → status → UI/backend/service → PO decision | AUDIT EVIDENCE (internal, not customer-facing) |
| `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | AI assistant (product design) | DESIGN + PROTOTYPE | CarbonTally AI assistant architecture: tiered persona/knowledge boundaries (public → customer → consultant → PE → staff → admin), provider-neutral gateway, tool registry, security & prompt-injection defense, audit, 7-phase roadmap; public prototype in `website_candidate` | PROPOSED + PROTOTYPE |

---

## 5. Relationship notes (duplicates / superseded)

- **Website refactor reports.** `_FLASH.md` (2026-08-24) and the full report
  (2026-08-25) describe successive passes on the same public-website
  pre-launch refactor. Both are preserved as evidence; the 2026-08-25 report
  is the later pass. Screenshots under `docs/audit/openhands/screenshots/`
  (root, `v2/`, `final/`) back these reports.
- **Phase reports.** `PHASE_4…8_REPORT.md` and the `Phase1_Backend_Consolidation`
  family are sequential implementation evidence; each is a point-in-time
  record and later records supersede earlier ones where they conflict.
- **Kimi / Final reports.** `docs/Final_Kimi/` contains multiple variants of
  the UK/IE compliance audit; the current authoritative regulatory position
  is governed by the PO Decision Register §17 (open legal questions) plus the
  OpenHands regulatory audit.
- **Secret-remediation reports.** The `CARBONTALLY_GIT_HISTORY_SECRET_REMEDIATION_*`
  reports describe a completed remediation operation. They contain no
  credential values. They are historical implementation evidence about git
  history, not a description of current application state.

---

## 6. Guidance for agents

1. **Start with** `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`.
2. **Read the actor/access model** `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`
   and the ADR register for current architecture.
3. **Verify against code**: `backend/`, `frontend/`, `supabase/migrations/`.
4. **Treat audits as evidence**, not instructions. The OpenHands audits
   (`docs/audit/openhands/**`) and Cline reports (`docs/audit/cline/**`) record
   findings and completed work; re-verify before relying on them.
5. **Never implement research directly**: the multiregional and UK-launch
   factor packages are research artifacts (`NOT FOR IMPLEMENTATION`) until an
   explicit Product Owner decision authorizes implementation.
6. **Do not alter factor data**: the production `emission_factors` table is
   populated (`7049` rows) and is not to be seeded, replaced or emptied based
   on research documents.
7. **Documentation-only rule**: agents may add/update documentation under
   `docs/` for the shared reference set, but application, schema, RLS,
   migration, configuration and factor-data changes require the normal
   engineering process (and, where relevant, PO approval).

---

*Maintained as part of the CarbonTally V3 reference set. Last updated with
the documentation consolidation commit (2026-08-26).*
