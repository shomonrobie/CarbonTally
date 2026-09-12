# CarbonTally — Phase 8 Product & Report Ratification

**Prompt ID:** `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010`
**Date:** 2026-09-12
**Repository HEAD at ratification:** `687c9711240c6b042d02482f1d258ec2b8ddc170` (branch `main`)
**Status:** **RATIFICATION / DECISION REGISTER — DOCUMENTATION ONLY**
**Implementation authorised by this document:** **NONE**

---

## 1. Document Purpose

This document converts the Phase 8 discovery findings, the Phase 8 reporting lifecycle
specification, and the Product Owner's explicit decisions into a **single formal decision
baseline** for Phase 8.

It exists to answer three questions for every significant area:

| Question | Column in §22 |
|---|---|
| What does CarbonTally do **today**? | *Current Reality* |
| What is CarbonTally **now authorised/intended** to do? | *Ratified Direction* |
| What must be **built or changed later**? | *Future Implementation Consequence* |

**This task does not implement anything.** It writes no code, no migration, no RLS policy, no
API route, no frontend, no report-engine change, no PDF change and no AI change. It fixes no
defects. Every gap it discovers is recorded as **future implementation work**, not repaired.

**Status vocabulary used throughout:**

| Status | Meaning |
|---|---|
| `RATIFIED` | Product Owner has decided the direction in this document or an already-ratified authority |
| `DEFERRED` | Valid capability, intentionally not in the immediate baseline |
| `FUTURE` | Ratified direction that has no implementation today; requires later authorised work |
| `PO DECISION REQUIRED` | Genuine unresolved product/policy choice; not silently decided here |
| `UNVERIFIED` | Repository evidence is insufficient; no inference offered |

**Rule applied:** a thing is **not** `RATIFIED` merely because it exists in code. Existing
implementation is *evidence*, not authorisation.

---

## 2. Scope and Non-Scope

### 2.1 In scope (ratification only)

* The authoritative V3 report catalogue and the report type/instance/version/artifact distinction.
* Assertion/assurance positioning and the Auditor / Assurance Reviewer boundary.
* The RBAC **+ scope** authorization model for report access.
* System-controlled facts vs editable narrative.
* The report lifecycle and version states.
* The approval model and its separation from PE/processing approvals.
* The frozen final PDF / artifact model.
* The four administrative/management reporting surfaces (capability family).
* Canonical analytics/reporting architecture and anti-duplication rules.
* The Ask CarbonTally conversational boundary.
* The AI narrative boundary.
* Legacy reporting disposition.
* Deferred/future capabilities.

### 2.2 Explicit non-scope

* No implementation of any kind (see §25).
* No schema, migration, RLS, API, frontend, PDF, AI or billing change.
* No defect remediation (defects are recorded, not fixed).
* No scope change to Phase 9+ capabilities (net-zero planning, disclosure frameworks, PCF/LCA, etc.).
* No redesign of messaging, billing/subscription, or the calculation engine.

---

## 3. Source Documents Reviewed

| # | Document | Role in this ratification |
|---|---|---|
| S1 | `docs/architecture/CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` | Phase 8 archaeology: capability matrix, reuse/gap findings, P1–P31 decisions |
| S2 | `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` | Lifecycle baseline: 6 states, transitions, overlay model, PDF/hash model, schema Options A–D |
| S3 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | **Architecture source of truth**: §5 Actor Model, §13 Authorization, §14 RLS, §16 Ops/Admin separation |
| S4 | `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | PO-ratified sequencing; phase names/status; §0 ratification record; §18 open governance items |
| S5 | `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | Canonical AI assistant architecture: tiered personas, AssistantGateway, tool registry, provider abstraction, 7 phases, open PO decisions |
| S6 | `docs/architecture/CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` | Phase 7 closure: explicit non-claims, `not_assurance: true`, "AUDIT EVIDENCE READINESS", no auditor role created |
| S7 | `docs/cline/prompt-history/CT-P7P8-ROLE-REPORT-CATALOGUE-20260912-002.md` | Prior role × report/analytics catalogue (Class A–G classification) |
| S8 | `AGENTS.md` | Project operating constitution (authorization, evidence, RLS, absence-of-authority rules) |
| — | Current repository source | Verified implementation reality (reporting API, engine, repositories, schema, migrations, RLS scans, audit taxonomy, frontend) |

### 3.1 Authority precedence applied

1. Current runtime/repository reality (primary evidence).
2. Ratified Product Owner decisions (roadmap §0, AGENTS.md, this task's PO instruction, S6 closure).
3. Architecture source of truth (S3 Blueprint).
4. Phase 8 discovery + lifecycle specification (S1, S2).
5. Prior catalogues and historical audits (S7 and earlier — context only).

**Not applied as authority:** the informal "80–90 audit-ready reports" statement, and any
legacy label or code path treated as though it were a live V3 product type.

---

## 4. Current V3 Report Catalogue

### 4.1 The "80–90 reports" statement is withdrawn

The informal claim that CarbonTally already contains approximately **80–90 audit-ready reports**
is **not authoritative**, is **not supported by the repository**, and **must not be carried
forward**. It must not be used in planning, sales material, or product documentation.

### 4.2 Authoritative current catalogue

**The authoritative current V3 report catalogue is exactly one report type:**

```text
annual
```

| Property | Value | Evidence |
|---|---|---|
| Catalogue | `SUPPORTED_REPORT_TYPES = {"annual": …}` | `backend/api/v3_reports.py:63` |
| Structure | **12-section structured annual emissions report** | `backend/engines/report_generation.py:65` |
| Enforcement | `validate_report_type()` → **HTTP 422** for anything else | `v3_reports.py` |
| Discovery surface | `GET /api/v3/reports/types` returns that single entry | `v3_reports.py` |
| Test guard | `test_supported_report_types_are_real_engine_types()` | `backend/tests/unit/api/test_v3_reports.py` |

The twelve sections are: `metadata`, `organization`, `period`, `totals`, `scopes`, `activities`,
`validation`, `benchmarking`, `provenance`, `calculation`, `lineage`, `generation`.

### 4.3 What must not be counted as report types

None of the following are report types:

* **customer report instances** (one generated report for one organisation + reporting year);
* **report versions** (content snapshots of an instance);
* **generated or exported artifacts** (PDF/JSON/CSV outputs of a version);
* **dashboard views or analytics endpoints** (e.g. `/emissions/dashboard`, `/reporting/*`);
* **legacy labels** from unmounted code.

Counting instances, versions, artifacts or dashboards as "reports" is what produced the
unsupported 80–90 figure. **This conflation is now prohibited.**

### 4.4 Legacy labels — not authoritative, not revived

`SECR`, `CSRD`, `ISSB`, `AUDITOR_EXCEL`, and the generic labels `summary`, `documents`,
`emissions`, `staff`, `organization`, `custom` exist **only** in
`backend/routes/reports.py` — a 2,097-line legacy monolith that is **not mounted** by
`backend/api/router.py` — together with `backend/report_generator.py` (an FPDF SECR-oriented
generator reading via a legacy path).

**Ratified:** these labels must **not** be represented as currently authoritative V3 report
types, and must **not** be revived as live V3 report types by this ratification (§20).
**Future report types may be deliberately introduced later**, through proper product decisions.

---

## 5. Report Type / Instance / Version / Artifact Distinction

This distinction is **mandatory** and is now ratified as product vocabulary.

| Concept | Definition | Current representation | Status |
|---|---|---|---|
| **Report type / template** | The kind of report the engine can produce | `SUPPORTED_REPORT_TYPES` → `annual`; `report_templates` table exists (dormant) | `RATIFIED` |
| **Customer report instance** | One generated report for one `organization_id` + `reporting_year` + `report_type` | `report_generation_queue.id` (there is **no** `public.reports` parent table) | `RATIFIED` |
| **Report version** | An immutable content snapshot of an instance at a point in time | `report_versions` row (`report_id` + `version_number`, `UNIQUE`) | `RATIFIED` |
| **Generated / exported artifact** | A rendered deliverable produced from a version (PDF/JSON/CSV) | JSON attachment via `/download`; PDF bytes via `/pdf` (not stored) | `RATIFIED` |

### 5.1 Consequences

1. A "report" in product language means a **customer report instance**.
2. A report's agreed content is expressed by a **version**, never by the instance row.
3. An **artifact** is an output of a version and is never itself a report type.
4. Counts of reports for management purposes must state which of the four concepts they count.

---

## 6. Assurance Positioning

### 6.1 Ratified position

**CarbonTally is not, and must never claim to be:**

* an independent GHG auditor;
* an independent verifier;
* an assurance provider;
* a certification body;
* a regulatory certification authority.

**CarbonTally may produce:**

* evidence-backed carbon reporting;
* traceable calculations and calculation provenance;
* supporting evidence and evidence-traceable records;
* audit/assurance-**supporting** packages;
* **assurance-ready** reporting artifacts.

**CarbonTally must not claim** that its own report approval or finalization constitutes
independent audit, independent verification, assurance, or certification.

**Any external assurance or certification remains the responsibility of the appropriate
qualified external party.**

### 6.2 Authority for this position

This is not new policy — it is the **already-ratified** Phase 7 position
(`CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` §5), which:

* lists the same four non-claims and the prohibited wording set;
* records that the readiness indicator is labelled **"AUDIT EVIDENCE READINESS"**;
* records that every Phase 7 payload carries `not_assurance: true` plus a notice;
* records that **no auditor role or table was created**.

### 6.3 Binding wording rules

**Prohibited product wording:** "CarbonTally is independently assured"; "CarbonTally is
certified"; "CarbonTally is a certified verifier"; "CarbonTally is GDPR compliant".

**Required framing:** *auditability*, *evidence traceability*, *provenance*, *investigation
support*, *assurance-supporting evidence*, *audit-ready / assurance-ready* — never *assurance*,
*verified*, *audited*, *certified*.

### 6.4 Three-way distinction

| | Position |
|---|---|
| **Current reality** | CarbonTally produces an annual report with validation, benchmarking, provenance, calculation and lineage sections. Report approval does not exist at all. |
| **Ratified direction** | CarbonTally **supports** external assurance with evidence; its approval/finalization is a **customer assertion lifecycle**, never assurance. |
| **Future implementation** | Any UI or label introduced by the report lifecycle must avoid assurance wording; approval screens must state that approval is the customer's own assertion, not third-party verification. |

---

## 7. Auditor / Assurance Reviewer Boundary

### 7.1 What is being ratified

A **future** *Auditor / Assurance Reviewer* capability is ratified **as a design boundary**.
It is an externally-scoped review capability that may be granted to an appropriate qualified
external party so they can inspect CarbonTally's evidence and provenance.

**This ratifies the boundary, not an implementation.** No auditor role, table, invitation model,
API or UI exists today — this is `FUTURE`.

### 7.2 Permitted actions (ratified allowlist)

An authorised Auditor / Assurance Reviewer **may**:

* view **authorised** reports;
* view report versions;
* inspect CarbonTally calculations;
* inspect evidence;
* inspect factor provenance;
* inspect relevant audit history;
* add review comments;
* request additional evidence;
* raise findings / issues.

### 7.3 Prohibited actions (ratified denylist)

The reviewer must **not** be able to edit:

* CarbonTally calculations;
* emission factors;
* underlying authoritative ledger data;
* evidence records;
* provenance;
* calculation snapshots;
* system-controlled report facts.

The reviewer must also **not**:

* approve a CarbonTally report;
* finalize a CarbonTally report;
* change an approved or final CarbonTally version.

**Rationale:** if an external reviewer could approve or finalize, the resulting approval would
look like third-party assurance created inside CarbonTally — directly contradicting §6. Approval
and finalization remain the customer's assertion lifecycle. The reviewer's *findings and
comments* are the external party's input, delivered outside CarbonTally's approval gate.

### 7.4 External document editing — explicitly outside the system of record

An auditor may **export** a CarbonTally report as PDF/DOCX and edit that file **externally**.
That external document is **outside CarbonTally's system of record**. Such editing:

* must **not** be treated as editing the CarbonTally report or version;
* must **not** alter any CarbonTally content hash, version state or artifact;
* confers **no** CarbonTally approval or finalization.

**Ratified:** CarbonTally must **not** create an auditor "report editor" capability merely to
support external document editing. No such capability is authorised.

### 7.5 Three-way distinction

| | Position |
|---|---|
| **Current reality** | **No auditor role, table, workspace, invitation model or API exists.** Phase 7 explicitly created none. Evidence/audit reads are internal-staff and owner/admin only (`ensure_org_audit_access`). |
| **Ratified direction** | A scoped, read-only + comment + findings capability for an authorised external reviewer, with no edit/approve/finalize rights, and external document editing outside the system of record. |
| **Future implementation** | A new trust/access model: reviewer identity, explicit scoping to organisation/entity/report/version, RLS-aware read access, comment/finding capture, and audit of reviewer actions. Prior catalogue classified this as **Class C/G (new capability + PO/governance decision)** — see S7 §9. |

---

## 8. RBAC + Report Scope Authorization Model

### 8.1 The ratified architectural decision

**Report access must always be authorization-controlled.**

> **RBAC/capability determines *what actions* a role may perform.
> Organization/entity/relationship scope determines *which* reports and data those actions may
> target.**
>
> **RBAC alone must never grant unrestricted report access.**

The conceptual authorization chain is ratified as:

```text
Identity
  → Role / Capability
    → Organization / Entity / Relationship Scope
      → Report Permission
        → Server-Side Authorization / RLS
          → Data
```

This extends Blueprint §13 (*"identity + scope + resource + action"* per actor family) and §5
(organization-scoped customer access; consultant active-grant access; PE entity/assignment-scoped
access; staff permission-based access; separate admin plane).

### 8.2 Every report operation must be authorization-controlled

Ratified as an architectural requirement — every meaningful report operation is
authorization-controlled, including, as applicable:

`view` · `list` · `inspect version` · `inspect evidence` · `inspect calculations` ·
`edit narrative` · `comment` · `submit for review` · `request changes` · `approve` ·
`revoke approval` · `finalize` · `download` · `access final artifact`

**Corollary:** there is no "report endpoint that is safe because it is read-only". Listing is an
authorization operation; version inspection is an authorization operation; artifact access is an
authorization operation.

### 8.3 Scope rules by actor family

#### 8.3.1 Customer — organisation-scoped

Customer users are restricted to their **authorized organization scope** (Blueprint §5.1).
Conceptual permissions:

| Capability | Owner | Admin | Member | Viewer |
|---|---|---|---|---|
| View permitted organisation reports | ✅ | ✅ | ✅ | ✅ (read-only) |
| View versions / evidence / calculations | ✅ | ✅ | ✅ | ✅ |
| Edit permitted narrative | ✅ | ✅ | per policy (§24) | ❌ |
| Review / comment | ✅ | ✅ | per policy (§24) | ❌ |
| **Approve** | ✅ | ✅ | ❌ | ❌ |
| Finalize | per explicit product permission (§24) | per explicit product permission (§24) | ❌ | ❌ |
| Download final artifact | ✅ | ✅ | ✅ | ✅ |

**Ratified:** Members and Viewers do **not** approve. Members' editing/commenting rights are
**per explicit permission** (§24 A1). Owner and Admin approval is ratified (§11).

#### 8.3.2 Consultant — active-grant-scoped

Consultants may access customer reports **only within active, authorized consultant-client
grants.**

**Ratified:** holding a `CONSULTANT` role does **not** grant access to all customer
organizations. Consultant access remains **tenant/client scoped** to ACTIVE grants; SUSPENDED and
ENDED relationships carry no access (Blueprint §5.2; D15 active-grant model).

#### 8.3.3 Processing Entity — entity/portfolio-scoped

PE users may access reports only for **authorized portfolio entities within their permitted PE
scope.**

**Ratified:** PE access must **not** imply unrestricted customer-organization access
(Blueprint §5.3, §7, §8).

**Reconciliation with the lifecycle specification (important):** the Phase 8 lifecycle
specification (§22.2) recorded PE access to **customer report instances/versions** as **"No"**.
This ratification preserves that: PE has **no access to customer report instances or versions**.
The PE Admin reporting surface (§16) is a **different thing** — PE-scoped *portfolio management
reporting over the PE's own authorized entities*, not access to customer report documents. These
two statements are consistent; see §16.1. If the PO intends PE users to open customer report
documents, that is a **new decision** and is flagged in §24.

#### 8.3.4 Auditor / Assurance Reviewer — explicitly assigned and scoped

Auditor/Assurance Reviewer access must be **explicitly assigned/scoped** to the relevant
**organization / entity / report / report version**, as appropriate to the future product design.

**Ratified:** holding an auditor role does **not** grant global report access (§7).

#### 8.3.5 CarbonTally Staff/Admin — capability-based

CarbonTally staff/admin access must remain **capability-based** (Blueprint §5.4, §5.5, §16).

**Ratified:** staff/admin access must **not** automatically imply:

* customer report editing;
* customer data mutation;
* assurance approval.

Any privileged operational access must be **explicitly authorized and auditable**. Operations
(`/ops`) must not silently become the universal administrator interface, and Admin (`/admin`)
must not become the ordinary operational workbench (Blueprint §16: *"Shared domain services are
acceptable. Shared UI primitives are required. Shared privilege is not."*).

### 8.4 Server-side enforcement is mandatory

**Ratified:** frontend visibility is **UX only** and is **not** an authorization boundary.

Future implementation must enforce report authorization **server-side**, using CarbonTally's
existing authorization contract and appropriate database/RLS protections.

**Current reality (verified defect — recorded, not fixed):** the report tables
(`report_generation_queue`, `report_versions`, `report_comments`, `report_templates`) have
**no RLS enabled and no policy**, while 21 RLS enablements exist elsewhere in the schema
(including `calculation_snapshots`). Report authorization today rests **entirely** on API-layer
guards (`require_org_member()` + `ensure_org_access(...)`). This is not a UI-boundary violation,
but reports have **no defence-in-depth**, unlike carbon data.

**Future implementation consequence:** report-lifecycle tables must gain explicit RLS **or**
carry a documented, deliberate application-level authorization justification (AGENTS.md §67).
**No existing RLS may be weakened** to make the lifecycle work (Blueprint §14: *"No security
migration may weaken existing tenant/entity isolation."*).

---

## 9. System-Controlled Facts vs Editable Narrative

### 9.1 The ratified separation

The report must clearly separate **authoritative CarbonTally content** from **permitted narrative
content**. This is the single most important integrity rule of the report lifecycle.

#### 9.1.1 CarbonTally-controlled authoritative content — NOT freely editable

| Content | Source |
|---|---|
| Reporting period | `content.period` |
| Organizational boundary | `content.organization` |
| Scope 1 / 2 / 3 values | `content.scopes` |
| Activity data represented in the report | `content.activities` |
| Emission factors | `content.provenance` + factor records |
| Methodology | `content.calculation.methodology` |
| Calculations | `calculation_snapshots` (referenced, never copied) |
| Evidence | `domain/evidence.py` (referenced) |
| Provenance | `content.provenance` |
| Validation / QC results | `content.validation`, `issues`, review/QC |
| Benchmark information | `content.benchmarking` |
| Lineage | `content.lineage` |
| Authoritative carbon facts (totals, units, `gas_coverage` labels) | `content.totals` |

**Verified:** every key produced by `ReportGenerationEngine` inside the twelve sections is
system-controlled. There is **no editable field anywhere** in the current engine output.

#### 9.1.2 Editable narrative / presentation content

| Content | Nature |
|---|---|
| Management commentary | Customer narrative |
| Organisational context | Customer narrative |
| Explanation of operational changes | Customer narrative |
| Initiatives | Customer narrative |
| Reduction actions | Customer narrative |
| Future plans | Customer narrative |
| Bounded section notes | Customer narrative |

The exact field allowlist is **`PO DECISION REQUIRED`** (§24 A1) — this ratification fixes the
**principle and the namespace boundary**, not the final key list.

### 9.2 Binding rules

1. **Narrative editing must never modify underlying authoritative carbon facts.**
2. Narrative is stored in a **separate layer** from system content — not merged into it.
3. Narrative is validated server-side by **allowlist** (never blocklist); it must be rejected if
   it contains a system key or a path into a system section.
4. **Any future AI-generated narrative is candidate content only** (§19).
5. If a carbon fact is wrong, the underlying carbon workflow must correct it and the report must
   be **regenerated as a new version** — a narrative edit is not a carbon-data correction.

### 9.3 Three-way distinction

| | Position |
|---|---|
| **Current reality** | System content is generated and persisted in `report_generation_queue.generated_content`. A dormant `user_edits JSONB` column exists but is **written by nothing** and is **not even exposed** by the repository mapper. There is no editable namespace. |
| **Ratified direction** | A bounded, plain-text, allowlisted narrative layer separate from immutable system content. |
| **Future implementation** | Add a version-scoped narrative store, allowlist validation, and render-time composition; do **not** build it on the report-scoped `user_edits` column (it cannot survive multiple versions). |

---

## 10. Report Lifecycle

### 10.1 Ratified lifecycle

The baseline is the Phase 8 reporting lifecycle specification (S2), ratified here unchanged:

```text
GENERATE → DRAFT → EDIT → REVIEW → APPROVE → FINAL → FROZEN PDF
```

**Stored version states (ratified):**

| State | Meaning |
|---|---|
| `DRAFT` | Version exists; not yet put forward |
| `REVIEWED` | Submitted for review and reviewed |
| `CHANGES_REQUESTED` | Review outcome requiring changes |
| `REJECTED` | Review or approval outcome declining the version |
| `APPROVED` | Authorised version (version-bound approval) |
| `FINAL` | Deliverable frozen (artifact produced and immutable) |

**`EDITED` is an event/action, not a persistent state.** `SUPERSEDED` and "current version" are
**derived**, not stored.

### 10.2 Ratified invariants

1. **Approved and final versions are immutable.**
2. **Material changes after approval/finalization create a NEW report version** and require the
   appropriate review/approval process.
3. Invalid transitions are rejected server-side (`DRAFT → APPROVED`; `APPROVED → FINAL` without
   approval).
4. Every transition is **auditable** (actor, UTC timestamp, version, from-state, to-state).
5. Approval is **version-bound** — a new version does not inherit a prior approval.
6. A prior approval is **superseded, never erased or rewritten**.
7. Exactly one version per report is the "current version".

### 10.3 No contradiction found

The lifecycle was reviewed against current repository evidence. **No contradiction requiring PO
clarification was found.** The existing generation-queue vocabulary
(`pending`/`generating`/`completed`/`failed`) is a **generation** state machine and remains
separate from the **version** state machine. The two must be displayed distinctly and must not be
conflated.

### 10.4 Three-way distinction

| | Position |
|---|---|
| **Current reality** | Only the generation queue states exist. There is **no** draft/review/approve/final state, **no** transition out of `completed`/`failed`, and **no** version status column. |
| **Ratified direction** | The six-state version lifecycle above, with version-bound approval and immutability after approval/finalization. |
| **Future implementation** | Add version state to the version record; implement guarded transitions; emit audit events; correct the existing `is_current` defect (multiple `is_current=TRUE` rows are currently possible). |

---

## 11. Approval Model

### 11.1 Ratified position

**Report approval is a customer report lifecycle concept.** It is **distinct** from:

* PE processing approvals;
* assignment approvals;
* unrelated workflow approvals.

**Ratified:** existing PE/processing approval tables
(`approval_requests`, `approval_decisions`) must **not** be repurposed as the report approval
mechanism.

**Verified justification:** `approval_requests.assignment_id` is
`NOT NULL REFERENCES public.processing_assignments(id)` — report approvals have no assignment, and
repurposing would conflate two authorization domains and risk loosening PE-scoped policies.

### 11.2 Ratified approval roles

| Actor | May approve? |
|---|---|
| **Customer Owner** | ✅ **RATIFIED** |
| **Customer Admin** | ✅ **RATIFIED** |
| Customer Member | ❌ **RATIFIED (no)** |
| Customer Viewer | ❌ **RATIFIED (no)** |
| Consultant | **PO DECISION REQUIRED** unless explicitly authorized later |
| Internal CarbonTally staff | **PO DECISION REQUIRED** unless explicitly authorized later |

**Note on staff/consultant approval:** permitting CarbonTally staff to approve a customer's report
would create an assurance-like impression that §6 prohibits. The recommendation remains **no**;
the decision is reserved to the PO (§24).

### 11.3 Ratified approval properties

Approval must be:

* **version-bound** (records `version_id` + `version_number`);
* **auditable** (actor identity, UTC timestamp, decision, optional rationale);
* **explicit** (a distinct deliberate action, never implicit).

### 11.4 Ratified non-claim

**Approval must never be described as independent assurance.** Approval is the customer
organisation's own assertion about its own reporting period. Approval UI wording must reflect
that (§6.3).

### 11.5 Three-way distinction

| | Position |
|---|---|
| **Current reality** | **No approval mechanism exists at all.** Report generation requires only `require_org_member()`. `report_versions` has no status, approver or timestamp column. No approval endpoint exists. |
| **Ratified direction** | Owner + Admin approval, version-bound, audited, distinct from PE approvals, never framed as assurance. |
| **Future implementation** | Add approval columns/state to the version record; implement approve / request-changes / reject / revoke; require an expected content hash so stale approval is impossible; audit every decision. |

---

## 12. Frozen Final PDF / Artifact Model

### 12.1 Ratified model

* **Finalization creates a frozen final PDF.**
* The PDF represents a **specific CarbonTally report version**.
* The final artifact is **stored privately** (no public URL).
* The **exact PDF bytes are integrity-protected using a hash.**
* The **canonical report content has its own content identity/hash.**

```text
APPROVED version (version_id, version_number, content_hash)
        ↓ finalize
Render PDF from: approved version content + server-authorized brand
        ↓
Store object ONCE (private)
        ↓
Record: artifact identity, storage reference, byte size, PDF byte hash,
        renderer metadata, brand context, source version_id
        ↓
FINAL — never re-rendered, never overwritten
```

### 12.2 Two-hash distinction (ratified — this is mandatory)

| Hash | Over what | Purpose | Reproducible? |
|---|---|---|---|
| **Canonical content hash** | A canonical, normalised serialisation of the **version content**, with volatile keys excluded (e.g. `generation.generated_at`) | Ties **approval** and the artifact to exact content | **Must be** |
| **Final PDF byte hash** | The **exact stored PDF bytes** | Tamper detection for the specific stored file | Not required |

**Ratified:** approval records the **canonical content hash**; the artifact record stores the
**PDF byte hash**. Conflating them would either make approval unverifiable or make the artifact
hash meaningless.

**Verified basis for this distinction:** the engine output is **non-deterministic** (the
`generation` section embeds `datetime.now(timezone.utc).isoformat()`), and PDF bytes are
**non-reproducible** (reportlab writes `/CreationDate` and a document `/ID`; the footer embeds
`date.today()`). Therefore no claim that "the same report always produces identical PDF bytes"
may be made.

### 12.3 External edits are outside the system of record

External edits to **exported** PDF/DOCX files are **outside CarbonTally's system of record**
(§7.4). They do not change any CarbonTally hash, version state or artifact, and confer no
approval or finalization.

### 12.4 Three-way distinction

| | Position |
|---|---|
| **Current reality** | The PDF is **rendered on demand and never stored** (`render_branded_pdf` returns bytes). `report_generation_queue` has unused `final_report_url` / `final_report_file_name` / `final_report_size_bytes` columns that the PDF path never populates. The PDF identifies report type + year but **not the version**. No artifact hash exists. |
| **Ratified direction** | One frozen, privately-stored PDF per finalised version, with a PDF byte hash plus a separate canonical content hash, immutably associated to that version. |
| **Future implementation** | Add a finalize step that renders from the approved version, stores the artifact privately, records both hashes and the source `version_id`, and serves the **stored** artifact (never a fresh render) for final downloads. Make finalize idempotent. |

### 12.5 Known documentation defect (recorded, not fixed)

`download_report`'s docstring states *"no PDF rendering exists in V3 — documented backend gap"*
while the `GET /{id}/pdf` route **does** exist. This is **documentation drift**, not a functional
defect. It must be corrected when the lifecycle is implemented.

---

## 13. Four Admin / Management Reporting Surfaces (Ratified Capability Family)

### 13.0 What is being ratified

The Phase 8 capability family for administrative and management reporting is ratified as **four
distinct capability surfaces**, each defined by the **actor's scope** and the **decisions they
need to make** — not by a separate reporting engine.

**This ratifies capability scope, not implementation.** None of the four surfaces is authorised
to be built by this task.

### 13.1 Surface A — CarbonTally Admin

Platform operational intelligence, for the CarbonTally privileged control plane (`/admin`,
Blueprint §5.5, §16):

* organizations;
* users;
* consultants;
* PE firms / entities;
* report processing;
* calculation processing;
* evidence / QC readiness;
* failures;
* AI usage;
* plan / allowance;
* billing / usage;
* operational audit / security information.

**Scope rule:** CarbonTally-wide **capability-based** access. This is *not* a licence to read or
edit customer carbon content; it is platform operational intelligence (S7 §13).

## 14. Organization Admin Reporting

Customer management reporting, for the customer organisation's own administrators:

* emissions;
* Scope 1 / 2 / 3;
* trends;
* facilities / entities;
* activity / category;
* data quality;
* evidence readiness;
* unresolved issues;
* report status;
* approved / final reports;
* later: reduction progress;
* management insights.

**Scope rule:** strictly **own organisation** (`ensure_org_access` semantics). The Viewer role
reads only; Members edit/comment only per explicit permission (§24 A1).

**Three-way distinction:**

| | Position |
|---|---|
| **Current reality** | Partially exists: `/api/v3/reporting/customer-dashboard` (emissions, documents, processing, issues, reports, `attention`), `/emissions-trend`, `/member-activity`, plus `/api/v3/emissions/dashboard` and `/scope-breakdown`. No "evidence readiness" roll-up, no report-status roll-up beyond counts, no reduction progress (no target model). |
| **Ratified direction** | A named Organization Admin management surface over the canonical data. |
| **Future implementation** | Extend `ReportingRepository` with evidence-coverage, data-quality and report-status aggregates; build the UI in the V3 customer shell on D21 tokens. |

---

## 15. Consultant Admin Reporting

Portfolio / client management reporting, for a consultant firm:

* client reporting status;
* data completeness;
* evidence readiness;
* QC issues;
* reports awaiting review / approval;
* deadlines / status;
* portfolio operational insights.

**Scope rule:** **strictly respect active consultant-client grants.** SUSPENDED and ENDED
relationships are counted but never detailed. A `CONSULTANT` role alone grants no cross-client
access.

**Three-way distinction:**

| | Position |
|---|---|
| **Current reality** | Exists in part: `/api/v3/reporting/consultant-portfolio` (portfolio counts + active-client detail), `/consultant-client/{client_id}`, and per-client surfaces in `v3_consultants.py` (dashboard/reports/documents/evidence/issues/processing). |
| **Ratified direction** | A named Consultant Admin portfolio surface over the canonical data, active-grant scoped. |
| **Future implementation** | Add portfolio roll-ups (evidence readiness, QC issues, reports awaiting review/approval, deadlines) and an emissions roll-up across active clients only. |

---

## 16. PE Admin Reporting

Portfolio management reporting, for a Processing Entity's administrators:

* portfolio entities;
* emissions;
* Scope 1 / 2 / 3;
* year-over-year trends;
* evidence readiness;
* reporting status;
* later: targets / reduction progress;
* portfolio insights.

**Scope rule:** **strictly respect authorized PE / entity scope** (`require_entity_scope` +
active-entity checks).

### 16.1 Reconciliation — PE portfolio reporting vs customer report documents

| Statement | Meaning |
|---|---|
| Lifecycle spec (S2) §22.2: PE access to **customer report instances/versions** = **No** | PE may not open a customer's report document |
| §16 above: PE Admin **portfolio reporting** = ratified capability | PE may see **management reporting over its own authorized portfolio entities** |

These are **consistent, not contradictory**: portfolio reporting is *aggregated, entity-scoped
management information*, whereas a customer report instance/version is a *customer deliverable*.

**If the PO intends PE users to open customer report documents, that is a new decision** —
flagged in §24 (A-PE).

**Three-way distinction:**

| | Position |
|---|---|
| **Current reality** | Exists in part: `/api/v3/ops/entities/{id}/performance` (batches, items, quality, staff, SLA) and `/api/v3/ops/entities/{id}/audit-activity`, plus `PEDedicatedHome` / `PEManagerDashboard` frontend surfaces. No emissions/scope/YoY portfolio analytics; PE has no customer report access. |
| **Ratified direction** | A named PE Admin portfolio surface, entity-scoped, reusing canonical emissions/calculation/evidence data. |
| **Future implementation** | Add PE-scoped emissions/scope/YoY aggregates and evidence-readiness/results roll-ups through the canonical reporting layer. |

---

## 17. Canonical Analytics / Reporting Architecture (Anti-Duplication)

### 17.1 The ratified anti-duplication rules

Phase 8 must preserve **exactly one** of each of the following:

| # | Rule | Verified current asset |
|---|---|---|
| 1 | **One canonical aggregation/analytics layer** | `ReportingRepository` (`backend/data/reporting.py`) + `EmissionsLogsRepository.aggregate()` (`data/emissions_logs.py`) |
| 2 | **One authoritative report engine** | `ReportGenerationEngine` (`engines/report_generation.py`) |
| 3 | **One canonical export/artifact approach** | `/api/v3/exports/*` (CSV/JSON) + `engines/pdf_render.render_branded_pdf` |
| 4 | **One LLM/provider abstraction** | `infra/llm_client.py` + `infra/ai_runtime.py` |
| 5 | **One evidence/provenance vocabulary** | `domain/evidence.py` (COMPLETE / PARTIAL / UNAVAILABLE) + `calculation_snapshots` |
| 6 | **One authorization contract** | `ensure_org_access`, `require_org_member`, `require_consultant`, `ensure_consultant_org_access`, `require_entity_scope`, `ensure_staff_permission` + RLS |
| 7 | **Two separate conversational domains** | Human↔human messaging (`conversations`/`messages`, `v3_messaging.py`) vs Ask CarbonTally (own domain) |
| 8 | **No parallel calculation engines** | `engines/calculation.py` is authoritative |
| 9 | **No parallel audit architecture** | `audit_trail` (append-only) + Phase 7 taxonomy |

### 17.2 Explicit prohibitions

**Ratified — the following must NOT be created:**

* a second reporting or analytics engine;
* a second export implementation;
* a second PDF renderer;
* a second LLM client or provider configuration path;
* a second evidence or confidence scoring model;
* a second audit ledger;
* a data warehouse or derived summary tables for analytics
  (consistent with the existing D30 property in `v3_reporting.py`: *"no derived summary tables,
  no N+1, no analytics warehouse"* — i.e. compute over live tables);
* a second authorization model for reports;
* four separate calculation/reporting engines for the four admin surfaces (§13.5).

### 17.3 Specific reuse warnings

| Warning | Reason |
|---|---|
| Do **not** repurpose `approval_requests`/`approval_decisions` for reports | FK-bound to `processing_assignments`; different domain; risks loosening PE policies (§11.1) |
| Do **not** build the narrative overlay on `report_generation_queue.user_edits` | Report-scoped, not version-scoped; cannot survive multiple versions (§9.3) |
| Do **not** resurrect `emissions_logs.confidence_score` as a report/evidence quality metric | Not part of the V3 evidence model; prompt prohibition |
| Do **not** create an auditor report editor | External document editing is outside the system of record (§7.4) |
| Do **not** put report lifecycle state into `report_generation_queue.status` | That column is the **generation** state machine; version state is separate (§10.3) |

---

## 18. Ask CarbonTally Boundary

### 18.1 Ratified separation

**Ask CarbonTally remains a distinct conversational domain from Human ↔ Human messaging.**

| | Human ↔ Human | Ask CarbonTally |
|---|---|---|
| Purpose | Person ↔ person | Person → CarbonTally analytical intelligence |
| Substrate | Supabase Realtime messaging (`conversations`/`messages`) | **Does not exist** — own domain |
| Governance | existing relationship/membership/capability/scope rules | controlled tools over the authorized API surface |

**Ratified:** the two must **not** share tables, routes or services. A chat-*like* UI is
permitted; a chat *data model* is not.

### 18.2 Ratified conceptual architecture

```text
User
 → Ask CarbonTally UI
   → intent / query understanding
     → controlled AI / orchestration layer
       → authorized CarbonTally tools
         → authorization / RLS / domain layer
           → authoritative data
             → structured result
               → LLM explanation
                 → answer + evidence
```

### 18.3 Ratified prohibitions for the LLM

The LLM must **never**:

* directly calculate carbon;
* independently select emission factors;
* invent values;
* invent evidence;
* bypass authorization;
* access unrestricted database contents;
* alter authoritative CarbonTally data.

### 18.4 Ratified answer-quality requirements

Ask CarbonTally must **distinguish**:

* **zero**;
* **no data**;
* **insufficient data**;
* **uncertainty**.

Ask CarbonTally must **respect report lifecycle state** and must **never** describe a
`DRAFT`, `REVIEWED`, `CHANGES_REQUESTED` or `REJECTED` report as approved or final.

### 18.5 Three-way distinction

| | Position |
|---|---|
| **Current reality** | No Ask CarbonTally capability exists: no route, no persistence, no tool layer, no query audit. A **deterministic public FAQ assistant** exists (`frontend/src/public/assistant/*`) with no provider and no customer-data access. The canonical design exists in S5 (tiered personas, `AssistantGateway`, tool registry, 7-phase roadmap). |
| **Ratified direction** | A separate, tool-mediated, authorization-scoped analytical capability; never ordinary messaging; never a database path to the model. |
| **Future implementation** | Assistant gateway + tool registry + query audit + rate limiting, built on the existing canonical design (S5) and the existing provider abstraction. **Not authorised by this task** (§25). |

---

## 19. AI Narrative Boundary

### 19.1 Ratified status of AI-generated narrative

**Future AI-generated report narrative is CANDIDATE CONTENT ONLY.**

It must use the **existing** CarbonTally AI architecture / provider abstraction
(`infra/llm_client.py`, `infra/ai_runtime.py`). No second AI path may be created (§17).

### 19.2 Ratified prohibitions

AI must **not**:

* alter system-controlled carbon facts;
* calculate emissions;
* choose emission factors;
* invent evidence;
* alter provenance;
* bypass authorization;
* directly write authoritative report or calculation data.

### 19.3 Ratified flow

AI output must pass through **appropriate deterministic/domain controls** before becoming part of
an authorized report version:

```text
Authoritative data → deterministic report structure → approved system facts
   → AI narrative (candidate) → human review/edit in the NARRATIVE overlay
   → customer approval → frozen final report
```

**Ratified:** AI output can only ever populate the **narrative overlay**. It can never write
system content (`content`), and it can never approve or finalize.

### 19.4 AI must never be required

A report must remain producible, approvable and finalisable **with deterministic narrative only**.
AI assistance is an enhancement, never a dependency.

### 19.5 Latent reuse opportunity (recorded only)

`report_generation_queue` already contains `ai_model_used`, `ai_tokens_used`, `ai_cost` and
`ai_processing_time_ms` columns. If AI narrative is ever implemented, provider/model attribution
should reuse these rather than a new schema.

### 19.6 Do not implement

**No AI narrative capability is authorised by this task.** No provider is configured; no key
added; no SDK installed; nothing connected.

### 19.7 Three-way distinction

| | Position |
|---|---|
| **Current reality** | The only LLM consumer is **AI document extraction** (opt-in, deterministic fallback when unconfigured). Report narrative is a fixed template with no AI. A **pre-existing local `ollama` runtime exists in the development environment but is not referenced, configured or used by CarbonTally**. |
| **Ratified direction** | AI narrative is candidate-only, provider-abstracted, gated behind human review and the deterministic domain controls. |
| **Future implementation** | Narrative generation service (deterministic template first), then optional AI assistance behind the existing abstraction once the Phase 8 AI safety preconditions are satisfied. |

---

## 20. Legacy Reporting Disposition

### 20.1 Accurate description of legacy reporting

| Legacy artefact | What it is | Mounted? |
|---|---|---|
| `backend/routes/reports.py` (2,097 lines) | Legacy report monolith: `/report_status` advertising `["SECR","CSRD","ISSB","AUDITOR_EXCEL"]`; six generic types (`summary`, `documents`, `emissions`, `staff`, `organization`, `custom`); 10 metrics; template CRUD; scheduling; sharing; DEFRA factor import | **NOT mounted** by `backend/api/router.py` |
| `backend/report_generator.py` (1,071 lines) | FPDF `EnhancedSustainabilityReportPDF` — SECR-oriented narrative, YoY comparison, methodology notes, efficiency measures, intensity ratios — reading via a legacy client, not the authoritative chain | Legacy path |
| Legacy admin CRA analytics | Legacy operational analytics screens | Legacy |

### 20.2 Ratified positions

1. **`RATIFIED`:** legacy report **labels must not be revived as live V3 report types** by this
   ratification, and must not be represented as currently authoritative.
2. **`DEFERRED`:** the **retirement/disposition** of the legacy monolith and the legacy generator
   is **deferred**. No deletion, no rewrite and no revival is authorised.
3. **`PO DECISION REQUIRED`:** whether `SECR` (or any other framework) should later become a
   formal V3 report type; and whether the legacy surface should be progressively retired,
   retained as an unmounted ancestor, or archived.

### 20.3 Why no silent decision is made

AGENTS.md §79 prohibits removing legacy functionality without determining whether it is still
referenced or part of the application contract. The legacy monolith is **not mounted**, but its
disposition is a **product** decision, not a documentation decision.

### 20.4 Three-way distinction

| | Position |
|---|---|
| **Current reality** | Legacy code exists, is unmounted, and is not authoritative. No legacy report label produces a V3 report. |
| **Ratified direction** | Legacy labels are not live product types; legacy surface disposition is deferred pending a PO decision. |
| **Future implementation** | None authorised. Any retirement work must be a separate, explicitly authorised task with a dependency inventory. |

---

## 21. Deferred / Future Capabilities

The following are **not part of the immediate implementation baseline**. They are recorded so
that discovery recommendations are **not** mistaken for implementation authorisation.

| Capability | Status | Basis |
|---|---|---|
| **Net-zero planning** (baseline, targets, trajectory, gap-to-target, initiatives, scenarios) | `DEFERRED` — **no data model exists**; requires PO methodology decisions | S1 §7 |
| **Anomaly detection** | `DEFERRED` — no design, no methodology, high false-positive risk in carbon data | S1 §4.2, §8.2 |
| **Estimated-vs-primary data classification** | `DEFERRED` — needs a schema + policy decision; must not resurrect legacy `confidence_score` | S1 §8.2 |
| **Disclosure framework engine** (SECR/CSRD/ESRS/ISSB/SBTi/…) | `DEFERRED` — no framework model exists; framework names today appear only as legacy labels/prose | S1 §13 |
| **Supplier portal / supplier engagement / primary supplier data collection** | `DEFERRED` — new external actor family; product-scale | S1 §15 |
| **External peer benchmarking** | `DEFERRED` — no reference dataset; the benchmarking engine is internal-only | S1 §14.2 |
| **Climate projects / removals** | `DEFERRED` — no model | S1 §16 |
| **Scenario modelling** | `DEFERRED` — depends on net-zero planning | S1 §23.4 |
| **Target-progress modelling** | `DEFERRED` — depends on targets | S1 §23.4 |
| **PCF / LCA** | `DEFERRED` — different discipline; **not recommended** without commercial evidence | S1 §16.2 |
| **Cross-tenant aggregates** | `DEFERRED` — PO-gated; requires an anonymisation policy | S1 §23.4; S7 §10.5 |
| **Broader ESG functionality** | `DEFERRED` — outside current product identity | S1 §23.5 |
| **Individual staff / PE performance scoring** | `DEFERRED` — personnel governance sensitivity | S1 §23.4; S7 §10.4 |
| **Auditor / Assurance Reviewer capability** | `FUTURE` — boundary ratified (§7); implementation requires a new access model | §7.5 |

**Ratified:** none of the above is authorised for implementation by this document. Converting a
discovery recommendation into implementation authorisation requires a separate PO decision.

---

## 22. PO Decision Register

Statuses: `RATIFIED` · `DEFERRED` · `FUTURE` · `PO DECISION REQUIRED` · `UNVERIFIED`.
**No item is `RATIFIED` merely because it exists in code.**

### 22.1 Catalogue, positioning and the reviewer boundary

| ID | Decision | Status | Current Reality | Ratified Direction | Future Implementation Consequence |
|---|---|---|---|---|---|
| D-01 | **V3 report catalogue** | `RATIFIED` | Exactly one type: `annual` (12 sections), 422 for anything else | The authoritative catalogue **is** `annual`; the "80–90 reports" claim is withdrawn | None directly; blocks any catalogue expansion until separately authorised |
| D-02 | **Legacy report labels** | `RATIFIED` (no revival) / `DEFERRED` (disposition) | `SECR`/`CSRD`/`ISSB`/`AUDITOR_EXCEL` + 6 generic labels exist only in an **unmounted** monolith | Not live V3 types, not authoritative; **not revived**; disposition deferred | None authorised; any retirement requires a separate authorised task |
| D-03 | **Type / instance / version / artifact distinction** | `RATIFIED` | Conflated in the informal figure; correct in code | Mandatory four-concept distinction (§5) | Product copy, counts and analytics must state which concept they mean |
| D-04 | **Assurance positioning** | `RATIFIED` | Phase 7 closure already states the same four non-claims; `not_assurance: true` in payloads | CarbonTally is **not** auditor/verifier/assurance provider/certification body; it **supports** assurance with evidence | No assurance wording in any new report lifecycle UI |
| D-05 | **Auditor / Assurance Reviewer access** | `RATIFIED` (boundary) / `FUTURE` (implementation) | **No auditor role, table, workspace or API exists** (Phase 7 created none) | Explicitly assigned and scoped to organisation/entity/report/version; **never global** | New trust/access model + RLS-aware reads + reviewer-action audit |
| D-06 | **Auditor editing prohibition** | `RATIFIED` | No such capability exists (nothing to restrict) | Reviewer may **not** edit calculations, factors, ledger data, evidence, provenance, snapshots or system facts | Server-side deny paths; negative tests |
| D-07 | **Auditor approval / finalization prohibition** | `RATIFIED` | No approval/finalization exists at all | Reviewer may **not** approve, finalize, or change approved/final versions | Approval/finalization authority must exclude the reviewer role |
| D-08 | **External document editing** | `RATIFIED` | Exported files are plain files | Exported PDF/DOCX editing is **outside the system of record**; no auditor "report editor" is created | None to build; explicit non-goal |

### 22.2 Authorization model

| ID | Decision | Status | Current Reality | Ratified Direction | Future Implementation Consequence |
|---|---|---|---|---|---|
| D-09 | **RBAC requirement** | `RATIFIED` | API guards inspect org membership + role | RBAC/capability determines **what actions** a role may perform | Capability checks at the endpoint/service layer |
| D-10 | **Scope / relationship requirement** | `RATIFIED` | `ensure_org_access`, active-grant and entity-scope guards | Scope determines **which** reports/data the actions may target; **RBAC alone never grants unrestricted access** | Every report query must be scope-filtered, never role-only |
| D-11 | **Server-side enforcement** | `RATIFIED` | API-layer enforcement exists; frontend hides controls | Frontend is **UX only**; authorization is **server-side** | Deny-by-default on every report operation (§8.2 list) |
| D-12 | **RLS requirement/consideration** | `RATIFIED` (requirement) / `UNVERIFIED` (approach) | **No RLS on any report table**; 21 RLS enablements exist elsewhere incl. `calculation_snapshots` | Report tables must gain explicit RLS **or** a documented deliberate application-level justification; **no existing RLS weakened** | Migration to enable + scope policies, or a governed justification |
| D-13 | **Customer report access** | `RATIFIED` | Org-scoped via `require_org_member` + `ensure_org_access` | Owner/Admin/Member/Viewer access per matrix; **Owner + Admin approve**; Member/Viewer never | Role matrix enforced server-side; Viewer read-only |
| D-14 | **Consultant-client scope** | `RATIFIED` | `require_consultant` + `ensure_consultant_org_access` (ACTIVE grant) | Consultant role alone grants **nothing**; access is active-grant-scoped only | Ended/suspended grants denied; negative tests |
| D-15 | **PE entity scope** | `RATIFIED` | `require_entity_scope` + active-entity checks | PE is entity/portfolio-scoped; **must not imply unrestricted customer-org access** | PE analytics entity-scoped; see D-16 |
| D-16 | **PE access to customer report documents** | `PO DECISION REQUIRED` | PE cannot access customer reports today (no PE report routes) | Lifecycle spec: **No**. Portfolio reporting (§16) is a **separate** ratified capability | If PO intends PE to open customer report documents, a new scoped access model is required |
| D-17 | **CarbonTally staff/admin capability scope** | `RATIFIED` | Capability-based (`require_staff`, `ensure_staff_permission`, `can_*` flags); `/ops` ≠ `/admin` | Does **not** imply customer report editing, customer data mutation or assurance approval; privileged access must be explicit and auditable | Staff capabilities enumerated per endpoint; no blanket admin shortcut |

### 22.3 Content, lifecycle, approval and artifact

| ID | Decision | Status | Current Reality | Ratified Direction | Future Implementation Consequence |
|---|---|---|---|---|---|
| D-18 | **Customer narrative editing** | `RATIFIED` (principle) / `PO DECISION REQUIRED` (allowlist) | **No editing path exists**; `user_edits JSONB` is dormant and unexposed | A bounded, plain-text, allowlisted narrative layer, separate from system content | Version-scoped narrative store + allowlist validation + composition; not `user_edits` |
| D-19 | **System fact immutability** | `RATIFIED` | System content is generated and persisted; nothing editable | All 12 engine sections are system-controlled; narrative can never alter carbon facts | Server-side rejection of any overlay touching a system key |
| D-20 | **Report lifecycle** | `RATIFIED` | Only generation states exist (`pending`/`generating`/`completed`/`failed`) | `GENERATE → DRAFT → EDIT → REVIEW → APPROVE → FINAL → FROZEN PDF`; six stored version states; `EDITED` is an event | Add version state + guarded transitions; keep version state separate from generation status |
| D-21 | **Post-approval versioning** | `RATIFIED` | No approval exists | Approved/final versions are **immutable**; any material change creates a **new version** requiring review/approval; prior approval is superseded, never erased | New-version creation path; immutability guards; no in-place mutation of approved content |
| D-22 | **Frozen final PDF** | `RATIFIED` (model) / `FUTURE` (implementation) | PDF rendered on demand, **never stored**; `final_report_*` columns unpopulated; PDF does not identify the version | One frozen, privately-stored PDF per finalised version, bound to that version, with a **PDF byte hash** and a separate **canonical content hash** | Finalize step (render → store privately → hash both → associate); idempotent; serve the stored artifact |
| D-23 | **Approval roles** | `RATIFIED` (Owner + Admin; Member/Viewer excluded) / `PO DECISION REQUIRED` (consultant & staff) | **No approval mechanism exists**; generation requires only `require_org_member()` | Owner + Admin approve; Member/Viewer never; consultant/staff approval reserved to the PO | Approval columns + endpoints; version-bound; audited; stale-approval blocked by expected content hash |
| D-24 | **Separation from PE approvals** | `RATIFIED` | `approval_requests.assignment_id` is `NOT NULL REFERENCES processing_assignments(id)` | PE/processing approval tables must **not** be repurposed for report approval | Purpose-built report-approval state on the version record; PE tables untouched |
| D-25 | **Legacy live PDF route** | `PO DECISION REQUIRED` | `GET /{id}/pdf` renders on demand; a docstring wrongly claims no V3 PDF rendering exists | Not decided — whether the live-render route is retained for drafts alongside the frozen-artifact route | Either keep both (draft live-render + final stored artifact) or replace; needs a PO call |

### 22.4 Surfaces, architecture, AI and deferrals

| ID | Decision | Status | Current Reality | Ratified Direction | Future Implementation Consequence |
|---|---|---|---|---|---|
| D-26 | **Four admin reporting surfaces** | `RATIFIED` (capability family) / `FUTURE` (implementation) | One shared layer (`ReportingRepository` + `v3_reporting.py`) already serves customer/consultant/PE/staff | CarbonTally Admin, Organization Admin, Consultant Admin, PE Admin — each scope-bound, all reusing the canonical layer | Extend the existing repository per surface; **no** per-surface engines |
| D-27 | **Canonical reporting/analytics architecture** | `RATIFIED` | One aggregation layer, one report engine, one export surface, one PDF renderer, one LLM abstraction, one evidence vocabulary, one audit ledger | Preserve exactly one of each; no parallel engines; no data warehouse or derived summary tables | Anti-duplication review at each implementation step (§17) |
| D-28 | **Ask CarbonTally separation** | `RATIFIED` (boundary) / `FUTURE` (implementation) | **Does not exist**; the public FAQ assistant is deterministic with no provider and no data access | A separate conversational domain from human↔human messaging; tool-mediated; authorization-scoped; never a DB path to the model | Assistant gateway + tools + query audit + rate limiting, on the existing canonical design |
| D-29 | **AI narrative boundary** | `RATIFIED` (boundary) / `PO DECISION REQUIRED` (deterministic-first timing) | The only AI use is opt-in document extraction; report narrative is a fixed template | AI narrative is **candidate content only**; may populate only the narrative overlay; provider-abstracted; never required | Narrative service (deterministic first), then optional AI behind `infra/` once safety preconditions are met |
| D-30 | **Deferred capabilities** | `DEFERRED` | Net-zero, anomalies, disclosure frameworks, supplier portal, peer benchmarking, PCF/LCA, climate projects, scenario/target modelling, cross-tenant aggregates, broader ESG, staff performance scoring — **none exist** | Remains deferred; discovery recommendations are **not** implementation authorisation | None authorised; each requires a separate PO decision and phase-design |

### 22.5 Register summary

| Status | Items |
|---|---|
| `RATIFIED` | D-01, D-03, D-04, D-06, D-07, D-08, D-09, D-10, D-11, D-13, D-14, D-15, D-17, D-19, D-20, D-21, D-24, D-27 |
| `RATIFIED` (with a deferred/future or undecided component) | D-02, D-05, D-12, D-18, D-22, D-23, D-26, D-28, D-29 |
| `FUTURE` (implementation) | D-05, D-22, D-26, D-28, D-29 |
| `DEFERRED` | D-02 (disposition), D-30 |
| `PO DECISION REQUIRED` | D-16, D-18 (allowlist), D-23 (consultant/staff), D-25, D-29 (timing) |
| `UNVERIFIED` | D-12 (which RLS approach will be chosen) |

**Reading the table:** where a row shows two statuses, the first governs the **direction** and the
second governs the **implementation state**. No row with a `PO DECISION REQUIRED` or `UNVERIFIED`
component is authorised for implementation.

---

## 23. Implementation Prerequisites

Nothing in this ratification authorises implementation. If and when implementation is separately
authorised, the following prerequisites must be satisfied **first**.

### 23.1 Governance prerequisites

| # | Prerequisite | Status |
|---|---|---|
| G1 | Explicit PO authorisation for a specific implementation step | **OUTSTANDING** |
| G2 | Resolution of the open PO decisions in §24 | **OUTSTANDING** |
| G3 | Reconciliation of the Master Roadmap's stale status (§23.4) | **PO DECISION REQUIRED** |
| G4 | A decision on the report-table RLS approach (enable + policies, or governed justification) | **OUTSTANDING** |
| G5 | Legal review of retention/deletion for reports and artifacts | **OUTSTANDING** |

### 23.2 Technical preconditions (in dependency order)

| # | Precondition | Why it must come first |
|---|---|---|
| T1 | **Fix the `is_current` multiple-true defect** (partial unique index, or derive current = `MAX(version_number)`) | Do not extend a table whose existing invariant is provably violable |
| T2 | **Correct the report-table RLS position** (enable + org-scoped policies, or document the deliberate justification) | The lifecycle adds writes; they must not be built on an unscoped base |
| T3 | **Surface `current_version` in the report list payload** | The frontend "Version" column currently always falls back to `v1` |
| T4 | **Add version state** to the version record (six states) with guarded transitions | Everything in §10/§11 depends on it |
| T5 | **Emit audit events** for every lifecycle transition into `audit_trail` | The lifecycle is currently completely unaudited; `CAT_REPORT` already exists, so no taxonomy change is needed |
| T6 | **Separate narrative storage** (version-scoped, allowlisted) | Required before any editing or AI narrative |
| T7 | **Private artifact storage + two-hash model** | Required before any finalization |
| T8 | **Server-side authorization for every report operation** (§8.2) | Frontend visibility is not a boundary |
| T9 | **Negative security tests** (PE denial, Viewer denial, cross-org, cross-grant, stale approval, final immutability) | Evidence that the ratified boundaries actually hold |

### 23.3 Explicitly not prerequisites

* No data warehouse.
* No new analytics engine.
* No new PDF renderer.
* No LLM provider configuration.
* No billing/subscription change.
* No messaging change.

### 23.4 Governance finding — the roadmap status is stale

**Finding (recorded, not resolved):** `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` §0 (ratified
10 Sep 2026) and §11/§14 state that Phase 8 is *"FUTURE — ROADMAP NAME RATIFIED; DETAILED SCOPE
NOT DEFINED"* and *"NOT STARTED — NOT AUTHORIZED"*; §13 still reports *"CURRENT PRODUCT PHASE:
Phase 6"*; and §18 item 8 records an obsolete HEAD as carrying all uncommitted work.

Since then, the PO has separately authorised Phase 7 implementation and closure, and the Phase 8
discovery → lifecycle specification → this ratification sequence. **The roadmap's status table is
therefore stale relative to PO-authorised work.**

**This is a `PO DECISION REQUIRED` governance item:** whether to update the Master Roadmap phase
status/current position (a separate bounded documentation task). This ratification does **not**
amend the roadmap; the roadmap remains authoritative for **phase names and sequencing**
(§0 decision 5: the roadmap governs sequencing while the Blueprint governs architecture).

---

## 24. Open PO Decisions

Only **genuine** unresolved decisions are listed. Where the PO has already decided, no question is
invented.

### 24.1 Carried forward from the lifecycle specification (still open)

| ID | Question | Recommendation on record |
|---|---|---|
| **A1** | Exact **narrative field allowlist**: which keys, types, length limits, formatting, and who may edit (Owner/Admin/Member/consultant) | Bounded plain-text allowlist (§9.1.2); numeric values are a PO call |
| **A2** | May a **consultant** approve a client's report? May **internal CarbonTally staff** approve? | **No** to both — staff approval would imply assurance (§11.2) |
| **A3** | Is **review** a mandatory gate, or may approval follow directly from `DRAFT`? One-step or two-step approval? | Keep review as a required state |
| **A4** | May a Customer Owner **revoke** an approval, and under what conditions? | Permit before finalization with a recorded reason; never after |
| **A5** | Are review comments **internal-only** or **customer-visible** (per `visibility`)? | Split internal / shared |
| **A6** | May a customer **delete a draft version**? | Permit `DRAFT` only; preferably soft-discard |
| **A7** | Do unresolved **`change_request` comments block approval**? | Yes |
| **A8** | **Retention/deletion** policy for report instances, versions, comments and artifacts; may a `FINAL` report ever be deleted? | `APPROVED`/`FINAL` never deleted; periods need legal review |
| **A9** | Is **download** of a report/final PDF an audited event? | Yes |
| **A10** | **Staleness / data-as-of** behaviour when source carbon data changes after approval | Flag stale; display "data snapshot as of"; never silently change an approved report |
| **A11** | Is report **finalization billable / entitlement-gated**? | Out of scope here; `usage_tracking.reports_generated` exists but is never incremented |
| **A12** | Should the final report expose **calculation/evidence drill-down** to the reader? | Yes, subject to the viewer's authorization |
| **A13** | Should the **legacy live-render `GET /{id}/pdf`** route be replaced by, or kept alongside, the frozen-artifact route? | Keep the legacy route for drafts; frozen route for `FINAL` |

### 24.2 New decisions arising from this ratification

| ID | Question | Why it is open |
|---|---|---|
| **A-PE** | Do **PE users open customer report documents**, or only see PE-scoped portfolio reporting? | The lifecycle specification says no customer report documents; §16 ratifies PE portfolio reporting. Both are consistent, but the PO may have intended otherwise (§8.3.3, §16.1) |
| **A-AUD** | What is the **assignment model** for an Auditor / Assurance Reviewer (scoping to organisation / entity / report / version), who may grant it, and for how long? | §7 ratifies the boundary; the access model is explicitly left to future design (§7.5) |
| **A-AUD2** | Are reviewer **findings / requests-for-evidence** recorded as `issues`, or as a reviewer-specific record? | `issues` exists and is distinct from messaging and QC, but a reviewer record may be preferable |
| **A-LEG** | **Legacy surface disposition**: retain unmounted as an ancestor, progressively retire, or archive? And should `SECR` (or another framework) later become a formal V3 report type? | AGENTS.md §79 forbids silent removal or revival (§20.2) |
| **A-RLS** | Which approach for report-table RLS: enable + org-scoped policies, or a documented deliberate application-level authorization? | Security-architecture call with migration implications (§8.4, D-12) |
| **A-ROAD** | Update the **Master Roadmap** to reflect Phase 7 closure and the Phase 8 design sequence? | §23.4 governance finding |
| **A-ASSUR** | Is **assurance-readiness scoring** ever a product feature (i.e. a numeric score)? | Prior catalogue Class G; a score risks implying assurance (§6) |
| **A-STAFF** | Which **staff capabilities** (beyond the existing `can_*` flags) are needed for report operations, if any? | §8.3.5 requires explicit, auditable privilege |
| **A-COMMENT** | Should reviewer/customer comment visibility be **per-comment** or per-thread? | Interacts with A5 and the dormant `report_comments.comment_type`, which has no vocabulary today |

---

## 25. Explicit Non-Implementation Boundary

### 25.1 What this task did

* Reviewed the authoritative inputs (S1–S8) and current repository evidence.
* Produced this ratification and decision register.
* Created **two documentation files only**:
  * `docs/architecture/CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md`
  * `docs/cline/prompt-history/CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010.md`
* Recorded defects and governance gaps as **future work**, fixing none.

### 25.2 What this task did NOT do

```text
Code changes:            NONE
Database changes:        NONE
Migrations:              NONE
RLS changes:             NONE
API changes:             NONE
Frontend changes:        NONE
Report-engine changes:   NONE
PDF-rendering changes:   NONE
AI / LLM changes:        NONE
Billing changes:         NONE
Messaging changes:       NONE
Production changes:      NONE
Push to remote:          NONE
```

### 25.3 Defects discovered — recorded, NOT fixed

| # | Defect / gap | Severity | Where recorded |
|---|---|---|---|
| 1 | **No RLS on any report table** (no defence-in-depth for reports) | High | §8.4, D-12, T2 |
| 2 | **Report lifecycle entirely unaudited** (`v3_reports.py` makes no audit calls) | High | §10.4, T5 |
| 3 | **`is_current` can be multiply-true** | High | §10.4, T1 |
| 4 | **No approval / review / edit capability at all** | High | §11.5, §9.3 |
| 5 | **PDF never stored; not byte-reproducible; does not identify the version** | Medium-High | §12.2, §12.4 |
| 6 | **No auditor access model exists** (Phase 7 created no role/table) | Medium (future capability) | §7.5 |
| 7 | **Frontend "Version" column always falls back to `v1`** (list omits `current_version`) | Low | T3 |
| 8 | **`download_report` docstring drift** ("no PDF rendering exists in V3") | Low (docs) | §12.5 |
| 9 | **`usage_tracking.reports_generated` never incremented** | Low | A11 |
| 10 | **`report_comments` dormant; `comment_type` has no vocabulary; no version binding, org scope or visibility** | Medium | §16.1 |
| 11 | **Master Roadmap status stale** (Phase 6 current; Phase 8 "not authorised") | Medium (governance) | §23.4, A-ROAD |
| 12 | **Legacy reporting surface unmounted but undisposed** | Low-Medium | §20.2, A-LEG |

**No stop condition was triggered.** No implementation was required to answer any question; no
production access, credential or database mutation was needed; no conflict was found between the
lifecycle specification and the current repository; and the unrelated worktree changes were
preserved.

### 25.4 The governing statements

> **CarbonTally reports are authoritative presentations of CarbonTally's persisted,
> provenance-preserved carbon data. Customer narrative may explain that data, but customer
> narrative must never become the source of the data. Approval freezes the meaning of the report
> version; finalization freezes the deliverable.**

> **Report access is authorization-controlled: RBAC decides what a role may do; scope decides what
> it may do it to.**

> **CarbonTally supports assurance; it does not provide it.**

```text
PHASE 8 PRODUCT & REPORT RATIFICATION COMPLETE
STATUS:                       RATIFICATION / DOCUMENTATION ONLY
IMPLEMENTATION AUTHORISED:    NO
V3 REPORT CATALOGUE:          annual (1 type, 12 sections) — RATIFIED
ASSURANCE POSITION:           support, never provide — RATIFIED
AUDITOR BOUNDARY:             no edit / no approve / no finalize — RATIFIED
AUTHORIZATION MODEL:          RBAC + scope + server-side + RLS — RATIFIED
REPORT LIFECYCLE:             6 version states, immutable after approval — RATIFIED
APPROVAL ROLES:               Owner + Admin (consultant/staff PO-gated) — RATIFIED
FROZEN FINAL PDF:             two-hash model — RATIFIED (implementation FUTURE)
FOUR ADMIN SURFACES:          ratified capability family, one shared layer
ASK CARBONTALLY:              separate domain, tool-mediated — RATIFIED (FUTURE)
AI NARRATIVE:                 candidate content only — RATIFIED (FUTURE)
DEFERRED CAPABILITIES:        net-zero, anomalies, disclosure, supplier, PCF/LCA, and more
CODE / DB / RLS / API / FE:   NONE
MIGRATIONS / PRODUCTION:      NONE
LLM / PROVIDER / KEY:         NONE
```

*End of ratification.*
