# P17 Architecture Reconciliation — Final Report

**Document ID:** `CT-PO-P17-ARCH-02-RECONCILIATION-20250925`
**Task ID:** `P17-ARCH-02-20260925-RECONCILE-FREEZE`
**Date:** 2025-09-25

> **This document supersedes the unreconciled P17 implementation baseline for all future P17 implementation.**
> It does **not** overwrite, replace or reinterpret the historical `CT-PO-P17-ARCH-01-*` contract, which remains
> byte-identical and historically identifiable. ARCH-01 answers "what was contracted"; ARCH-02 answers "what is the
> reconciled, currently-authoritative baseline".

---

## 1. Task Identity

| Item | Value |
|---|---|
| Task ID | `P17-ARCH-02-20260925-RECONCILE-FREEZE` |
| Date | 2025-09-25 |
| Type | **Architecture reconciliation only** — no product implementation |
| Authority hierarchy applied | PO decisions > UI/UX standard > ARCH-01 contract > phase plan > acceptance matrix > schema delta > Scope 2/3 matrices > P16 baseline > existing code as current-state evidence |
| Implementation performed | **NO** |
| Migrations created | **NO** |
| Production contacted | **NO** |

---

## 2. Repository / Branch / Starting SHA

| Item | Value |
|---|---|
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| Starting SHA | `98a89d0c1ab0e850d4ca44e348a66da0515dc691` |
| Remotes | `github` (real: `https://github.com/shomonrobie/CarbonTally.git`) and `origin` (broken local path `/tmp/ct_step2`) |
| P17-ARCH-01 commit | `d24a5671d536c439414f85bb739181669382c6c` — confirmed reachable (short `d24a567`) |
| Working tree at start | 1 modified (`.gitignore`, pre-existing) + 15 pre-existing untracked files |

**Note on the task-supplied checkpoint string.** The task header again quoted the ARCH-01 SHA as a **39-character**
string (not a valid Git object name; `fatal: Not a valid object name`). The real commit is the 40-character
`d24a5671d536c439414f85bb739181669382c6c`, confirmed by short SHA, message, sole parent `9c96cbf` (the P16
checkpoint) and its six-artifact tree. No repository state was "repaired"; the reconciliation proceeded against the
verified commit.

---

## 3. Source Documents Inspected

Every source below was read from the **actual repository**, not from memory.

| # | Document | Status | Notes |
|---|---|---|---|
| 1 | `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | INSPECTED | 118,016 B; 57 sections |
| 2 | `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` | INSPECTED | 17,524 B; phases P17-A…P17-J |
| 3 | `docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json` | INSPECTED | 33 classified Scope 2 fields |
| 4 | `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` | INSPECTED | 15 categories × 16 fields |
| 5 | `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` | INSPECTED | 10 gates, 12 invariant tests, 11 DC controls |
| 6 | `docs/architecture/artifacts/p17_schema_delta_20250925.md` | INSPECTED | 9 sections + ARCH-02 §10 |
| 7 | `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md` | INSPECTED | verdict `P16_PASS`; 3,342-test regression; R1–R14 |
| 8 | `docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md` | INSPECTED | 78,724 B; 77 sections |
| 9 | `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | INSPECTED | 32,082 B; 51 sections |
| 10 | `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | INSPECTED **(path corrected)** | 20,237 B; the task named a root path that does not exist |
| 11 | `docs/architecture/CT-PO-P17-GIT-PRESERVE-02-20250925.md` | **MISSING at that path** | actual file is `...-02-20260925.md` (22,571 B), inspected |
| 12 | `docs/architecture/CT-PO-P17-GIT-PRESERVE-03-20250925.md` | **MISSING at that path** | actual file is `...-03-20260925.md` (12,596 B), inspected |

**Missing-artifact handling.** Three of the twelve named paths did not exist as written (item 10 lacked its
`docs/architecture/` prefix; items 11–12 carried the wrong date). No content was invented: the three **equivalent
committed files** were located by inspection and used, and each discrepancy is recorded here and in the
machine-readable matrix. All five governance documents are confirmed **tracked** in Git.

**Existing-first discovery also inspected (read-only):** the live Demo Lab schema
(`carbontally_demo_local` @ `127.0.0.1:54426`; 141 public tables, 83 migrations) — `consultant_clients`,
`consultant_profiles`, `consultant_firm_members`, `organization_members`, `roles`, `manual_processing_grants`,
`organization_metadata`, `system_settings`, `audit_trail`, `processing_audit_trail`, `calculation_snapshots`,
`emissions_logs`, `evidence_line_items`, `suppliers`, `customer_documents`, `activity_clarifications`, disclosure and
report tables — plus `backend/**` modules and the `frontend/src` tree.

---

## 4. Existing Architecture Summary (ARCH-01, verified)

* **Unified spine (AD-P17-01):** one accounting pipeline — `emission_factors` → matching/selection →
  `calculation_snapshots` → `emissions_logs` → evidence → reportability → reporting/disclosure. No parallel engine.
* **Scope 2 dual-method (AD-P17-03/04):** `scope2_method` REQUIRED per Scope 2 result, vocabulary
  `LOCATION_BASED`/`MARKET_BASED` reused verbatim from the frozen disclosure contract; both methods coexist and
  neither overwrites the other.
* **Scope 3 category identity (AD-P17-02):** category is a property of the activity/result, **never** of the factor;
  all 15 categories; boundary/origin properties separate 4/9, 5/12 and 8/13, which share factor families.
* **Contractual instruments (AD-P17-05):** a first-class org-scoped entity plus an allocation/claim ledger;
  `instrument exists` ≠ `instrument valid for claim`; cross-tenant claim and over-allocation structurally denied.
* **Factor governance (AD-P17-06):** no silent factor-year fallback on any path; four production call sites present
  unlabelled cross-year candidates (latent, verified).
* **Reportability (P16-RD-4 reuse):** `reportable | not_for_reporting | superseded`.
* **Idempotency (P16-R7 reuse):** the deterministic request id is the idempotency key, backed by
  `uq_calc_snapshots_request_id`.
* **Schema delta:** additive dimensions on `calculation_snapshots`/`emissions_logs` guarded by `NOT VALID` CHECKs so
  the 34 historical snapshots/logs are never rewritten or backfilled; four new entities proposed
  (`contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records`).
* **Tenancy:** RLS + API authorization, fail-closed, ALLOW and DENY tested.
* **ARCH-01 closing status:** `PARTIAL — PREREQUISITE DECISIONS REQUIRED`, because post-contract PO records existed
  that required reconciliation. **This document resolves that condition.**

---

## 5. PO Amendments Reconciled

Machine-readable form (16 areas × 5 columns): `artifacts/p17_architecture_reconciliation_20250925.json`.

### 5.1 Material amendments

| # | Area | ARCH-01 | PO amendment | Reconciled decision | Implementation impact | Acceptance impact |
|---|---|---|---|---|---|---|
| 1 | Unified CAMS | AD-P17-01/13 already mandated one shared core | POST-ARCH §2/§37: one CAMS; no separate engines/factor/reportability/audit/evidence systems | **CONFIRMED** as normative and testable | no new engine; P17-0 inventories existing systems | `AC-CAMS-01` added |
| 2 | Customer data ownership/contribution | not modelled | POST-ARCH §5/§6, PO-CAMS §2/§4: customers own and contribute their data when enabled | **ADOPTED** — a contributor entry path feeds the *same* governed pipeline | contributor surfaces + source-actor provenance (B/C/E/F/G) | `AC-CUST-01`, `AC-CUST-03` |
| 3 | Organization capabilities | not modelled | POST-ARCH §7, UIUX-01 §15: per-organization CarbonTally-controlled capability set | **ADOPTED** as an organization-level capability plane; representation deferred to P17-0 with a recommendation | P17-0 decision → capability dimension + admin surface + server enforcement | `AC-CUST-02`; disabled-state requirement |
| 4 | Customer authority | not modelled | POST-ARCH §8, PO-CAMS §9: permission ≠ authority | **ADOPTED** as an explicit server-enforced prohibition set | per-phase authorization boundaries + negative tests | `AC-CUST-03` |
| 5 | Lifecycle / reportability | P16 triplet reused for results | POST-ARCH §9, UIUX-01 §42: the governed lifecycle + rejection/correction/invalidation/supersession; not automatically reportable | **MAPPED** onto existing state machines; additive states only where a real gap exists | P17-H extended; P17-0 produces the mapping table | `AC-LIFECYCLE-01` |
| 6 | Consultant/client relationship | referenced generically | POST-ARCH §13: the client remains an independent organization; explicit relationship | **RESOLVED BY DISCOVERY** — `consultant_clients` already implements it | reuse + extend for delegated capabilities | `AC-DELEG-01` |
| 7 | Acting-for context | not modelled | POST-ARCH §14/§16/§22/§23, UIUX-01 §6/§64 | **ADOPTED** as a persisted context dimension (not just a UI indicator) | NEW additive columns on snapshots/logs/evidence/audit | `AC-ORGCTX-01`, `AC-AUDIT-01` |
| 8 | Report/evidence ownership | implicitly org-scoped | POST-ARCH §24/§25, UIUX-01 §64/§65 | **CONFIRMED** as an explicit invariant | no ownership column change; context fields only | `AC-ORGCTX-01` |
| 9 | UI/UX | largely out of phase scope | UIUX-01 §58/§59/§74/§76, POST-ARCH §41/§50, PO-CAMS §6/§23 | **AMENDED** — UI/UX is in-phase scope; no backend-only PASS | phase scope/effort significantly increased | A7 + `AC-UIUX-01` |
| 10 | Scope 2 method identity | method REQUIRED per result | POST-ARCH §27, UIUX-01 §21–§24 | **UNCHANGED**, reinforced: never inferred from factor metadata; both methods visibly distinct | P17-A schema + B/C paths + UI | `AC-S2METHOD-01` |
| 11 | Scope 2 contractual instruments | validation/allocation defined; framework rules deferred | POST-ARCH §27, UIUX-01 §23 | **UNCHANGED**; UI surface added; framework rules stay deferred | P17-C architecture unchanged; UI added | `AC-S2INST-01` |
| 12 | Scope 3 category identity | category is an activity property; 15 categories | POST-ARCH §28, UIUX-01 §25–§27 | **UNCHANGED**, reinforced; all 15 individually addressable; no zero-substitution | D/E/F/G architecture unchanged; per-category UI | `AC-S3CAT-01` |
| 13 | Factor governance | no silent year fallback; 4 call sites flagged | (no direct PO amendment) | **UNCHANGED**; the 4 call sites become a P17-A remediation dependency | P17-A must close it | `T-INV-10` unchanged |
| 14 | Security / RLS | fail closed; ALLOW + DENY | POST-ARCH §35/§36, UIUX-01 §44/§63 | **CONFIRMED** + cross-client negative matrix | authorization work in B/C; RLS unchanged unless P17-0 finds a gap | `AC-DELEG-01`, `AC-CUST-03` |
| 15 | Reporting | scope/method/category/reportability distinct | POST-ARCH §24, UIUX-01 §38/§39 | **UNCHANGED**; a reportable-only reporting workspace is a phase deliverable | P17-I unchanged; UI added | reporting criteria + UIUX verdict |
| 16 | Deferred items | extensive deferred list | POST-ARCH §28/§50, UIUX-01 §76 | **PRESERVED UNCHANGED** — nothing promoted | none | deferred status carried into reports |

### 5.2 Contradictions resolved

| # | Contradiction | Resolution (by authority order) |
|---|---|---|
| C1 | ARCH-01 treated UI/UX as largely out-of-scope; the PO/UIUX standard makes it mandatory in-phase | PO records win → UI/UX is in-phase scope; phase plan §16 amended |
| C2 | The ARCH-01 phase plan had no discovery/modelling phase; the PO requires existing-first discovery before implementation | a new **P17-0** gate was added ahead of P17-A |
| C3 | The PO lifecycle has 7+ states; P16 has a 4-state item flow and a 3-state reportability triplet | UIUX-01 §42 defers explicitly to the accounting contract and the existing P16 lifecycle → **mapping**, not replacement |
| C4 | The PO names a `consultant_client_relationship`; the repository already has `consultant_clients` | no duplication — the existing entity *is* the relationship |
| C5 | "Customer capability" could be read as a global flag; the PO requires per-organization control | capability is per-organization and CarbonTally-controlled; global flags are prohibited |

---

## 6. Unified CAMS Model

**Normative statement.** CarbonTally operates **one** Unified Carbon Accounting Management System covering Scope 1,
Scope 2 and Scope 3, serving CarbonTally Admin/Staff, direct customer organizations, consultant organizations,
consultant-managed client organizations and delegated users through the **same accounting core**.

```
CAMS  (one product, one accounting domain, one engine)
  |
  +-- Plane A  CarbonTally Admin/Staff management plane
  +-- Plane B  Organization carbon-accounting workspace (direct customer AND consultant client)
  +-- Context  Consultant operating context layered on Plane B (portfolio + delegated client operation)
  |
  Shared: engine | factors | snapshots | evidence | suppliers | review | reportability | audit | reporting
```

**Hard constraints (acceptance-testable).**

1. No separate accounting engine for staff / customer / consultant / consultant client.
2. No separate factor system, reportability system, audit system or evidence system.
3. What differs between contexts is exactly: **actor, organization context, role, capability, delegated
   relationship, workflow authority** — never accounting logic.
4. The same Scope 1/2/3 domain objects are used everywhere.

**Reconciliation note.** This confirms AD-P17-01/AD-P17-13 as previously written; no architectural change was
required. What is **new** is that this is now an explicit *acceptance criterion* (`AC-CAMS-01`) and that the three
PO operating models (Managed / Collaborative / Self-Service, POST-ARCH §11) are configurations of this one product,
not separate products.

---

## 7. Organization / Consultant / Client Model

### 7.1 Model

| Concept | Representation | Status |
|---|---|---|
| Organization (tenant, data owner) | `organizations` | **EXISTS — VERIFIED** |
| Membership + customer role | `organization_members` (`user_id`, `role`, `is_active`) | **EXISTS — VERIFIED** |
| Consultant organization identity | `consultant_profiles` + `consultant_firm_members` | **EXISTS — VERIFIED** |
| Consultant ↔ client relationship | **`consultant_clients`** (`consultant_id`, `organization_id`, `status`, `relationship_origin`, `engagement_requested_at/decided_by/decided_at`, `suspended_at`, `ended_at`, `lifecycle_updated_at`) | **EXISTS — VERIFIED** (2 live rows) |
| Delegated capability per client | not yet modelled per capability | **PARTIAL — EXTEND** (P17-0 decision) |
| Acting-for context | not modelled | **MISSING — NEW** |

> ⚠ **CORRECTED BY ARCH-04** (ARCH-03 finding **HIGH-01**): the row "Consultant organization identity" was classified
> `EXISTS — VERIFIED`, which **over-claimed**. `consultant_profiles` is keyed by `user_id` and carries **no
> `organization_id`**, `organizations` has no `organization_type`, and no `organization_relationship` table exists.
> The correct classification is **PARTIAL — MISSING LINKAGE**. The row is preserved above as the historical ARCH-02
> record; see the **ARCH-04 Addendum** at the end of this document. `consultant_clients` (the relationship) remains
> correctly classified `EXISTS — VERIFIED`.

```
Green Advisory (organization_id = A)          ← consultant, itself a full CarbonTally org
        |
        |  consultant_clients (relationship; status=active, relationship_origin, engagement lifecycle)
        v
ABC Manufacturing (organization_id = B)       ← independent client organization, remains the OWNER of
                                                 accounting data, evidence, calculations, reports,
                                                 reportability state and history
```

### 7.2 Non-negotiable properties

1. **A consultant client is an independent organization** (`organization_id = B`), never a sub-workspace owned by the
   consultant (POST-ARCH §13 "HARD PRODUCT DECISION").
2. **A consultant is itself a first-class CarbonTally organization** with its own Scope 1/2/3, evidence, suppliers,
   calculations, reviews and reports (POST-ARCH §12, §19; UIUX-01 §66).
3. **Consultant access is delegated access**, explicitly authorized and auditable — never ownership (POST-ARCH §14).
4. **Delegated access is per client and revocable.** Client A access must not imply Client B access; a read-only
   client relationship must not grant write; "consultant = client admin" is explicitly **not** the general rule
   (POST-ARCH §18).
5. **The consultant portfolio is a management layer on top of CAMS**, not a second accounting system (POST-ARCH §17).
6. **Client switching must revalidate authorization server-side**; a `?client_id=` selection is never the security
   boundary (UIUX-01 §63).
7. **The consultant's own accounting must never mix with a client's** (UIUX-01 §66).

### 7.3 Acting-for context (new)

Every relevant accounting operation must retain enough context to distinguish: **actor · actor organization ·
acting-for organization · data owner · object owner · action · timestamp · reason · downstream accounting effect**
(POST-ARCH §22, §23, §10).

**Architectural decision.** Acting-for is a **persisted context dimension**, not a UI label. The UI banner
(`ACTING FOR: ABC MANUFACTURING`) is required for usability but is **not** an authorization mechanism — backend and
database authorization remain mandatory (UIUX-01 §6; POST-ARCH §35).

**Ownership is unaffected:** `organization_id` remains the client organization for data, evidence, calculations and
reports. Acting-for/organization context is additive metadata (schema delta §10.3).

> ⚠ **EXTENDED BY ARCH-04** (ARCH-03 finding **MEDIUM-01**): the propagation scope stated here (snapshots, logs,
> evidence, audit writer) was **narrower than `AC-AUDIT-01` requires**. `AC-AUDIT-01` covers **every** material
> accounting change, so propagation must also cover **source/activity documents** (`customer_documents`),
> **suppliers**, **review/approval decisions** (`review_audit_trail`, `review_assignment_history`) and **report
> artefacts** (`report_versions`, `report_version_artifacts`). Schema delta §10.3 now carries a per-path (A)/(B)
> disposition. The governing rule is unchanged: **acting-for is context, not an authorization boundary.**

---

## 8. Customer Accounting Model

### 8.1 Contribution

Customers are **not merely document suppliers**. When enabled, a customer organization is a first-class contributor to
its own carbon accounting data: entering activity data, uploading evidence, correcting permitted submissions,
providing supplier information, participating in review, viewing calculations and data quality, and preparing
reporting information (PO-CAMS §4; POST-ARCH §5).

**Invariant:** customer data enters the **same governed pipeline** —
`CUSTOMER DATA → INGESTION → NORMALIZATION → VALIDATION → FACTOR/METHODOLOGY → CALCULATION → REVIEW → REPORTABILITY →
REPORTING` (POST-ARCH §6). **No customer permission may create an uncontrolled shortcut around this pipeline.**

### 8.2 Capabilities

Customer accounting is an **organization-level capability**, CarbonTally-controlled, per organization — never a global
hardcoded switch (POST-ARCH §7). The approved conceptual set:

`customer_accounting_enabled` · `scope1_customer_entry` · `scope2_customer_entry` · `scope3_customer_entry` ·
`customer_edit_submission` · `customer_upload_evidence` · `customer_supplier_data` · `customer_review` ·
`customer_approval` · `staff_review_required` · `staff_approval_required` (plus the consultant delegated-access keys of
UIUX-01 §16).

**Capability semantics (defined, because the PO record requires this):**

| Property | Definition |
|---|---|
| Scope | `organization` (direct customer or client), `consultant_firm` or `consultant_client` — the ratified three-scope vocabulary already used by the governance plane |
| Owner / authority | **CarbonTally-admin-controlled**; a customer may not self-enable a capability that grants accounting authority |
| Interaction with roles | a capability **gates** a role's action; a role never grants authority that a capability has disabled |
| Interaction with delegation | a consultant's effective authority is the **intersection** of client-org capability ∩ delegated client capability ∩ role |
| Interaction with reportability | `staff_approval_required` / `customer_approval` determine **whether and by whom** a result may reach `APPROVED`→`REPORTABLE`; a capability never bypasses validation, factor governance or review |

**Representation is deliberately deferred to P17-0** (schema delta §10.2). The architectural requirement is recorded;
the exact table/column form is not invented here because an equivalent ratified scope-based governance primitive
already exists and must not be duplicated.

**Disabled behaviour is an acceptance requirement:** a disabled capability must be explained in the UI, never rendered
as a misleading empty table, and must be denied by the backend independently (UIUX-01 §43, §44, §72).

### 8.3 Permission ≠ accounting authority

Customer permission to enter data does **not** authorize: changing governed methodology; modifying
CarbonTally-controlled emission factors; bypassing validation; bypassing mandatory review; making invalid
calculations reportable; silently mutating historical accounting results; accessing another organization;
manipulating accounting snapshots; altering platform accounting governance (POST-ARCH §8; PO-CAMS §9).

```
DATA CONTRIBUTION                      ACCOUNTING GOVERNANCE
(what a customer/consultant may do     (what only CarbonTally governance and
 to the DATA they own)                  authorised roles may do to the ACCOUNTING)
  - enter activity data                  - methodology / factor governance
  - upload evidence                      - validation rules
  - propose corrections                  - review & approval gates
  - supply supplier data                 - reportability determination
  - view their calculations              - snapshot immutability
                                         - cross-organization access
```

### 8.4 Lifecycle and reportability

Customer-entered data passes the governed lifecycle and is **not automatically reportable**. Rejection, correction,
invalidation and supersession must exist, and customer submission must never silently bypass required accounting
controls (POST-ARCH §9; PO-CAMS §7). Customer edits preserve actor, timestamp, original value, new value, reason,
source/evidence, resulting calculation impact and reportability impact; historical results never silently mutate
(POST-ARCH §10).

---

## 9. Scope 1

**Preserved from P16 — no redesign.** P17 depends on the following verified P16 controls, all of which must remain
intact (POST-ARCH §45; PO-CAMS §24; P16 final verification = `P16_PASS`):

| Control | P17 dependency |
|---|---|
| calculation correctness (server-side, reproducible) | all Scope 2/3 paths reuse the same engine |
| operator factor precedence + factor safety (component factors never used as totals) | extended to Scope 2/3 factor selection |
| factor year/scope guards | extended to every Scope 2/3 candidate path |
| supplier attribution (org-scoped, fail-closed resolver) | extended to Scope 2 providers and categories 1/4/5 |
| reportability lifecycle (`reportable` / `not_for_reporting` / `superseded`) | reused, never replaced |
| invalidation + supersession | reused for method/category corrections |
| calculation idempotency (deterministic request id + unique index) | extended with the new dimensions |
| tenant isolation + cross-organization authorization | extended to consultant/client and customer contexts |
| auditability (`audit_trail`, `processing_audit_trail`, `evidence_line_items`) | extended with acting-for context |

**Not changed by this reconciliation:** the Scope 1 activity taxonomy, the calculation engine, factor matching, or the
existing Scope 1 evidence/reporting path.

**Coverage honesty.** Scope 1 E2E-verified coverage remains **stationary combustion of natural gas** (6 reportable
snapshots, 12,527.711 kg CO₂e). Mobile combustion, fugitive emissions and process emissions remain **NOT E2E
VERIFIED**; process emissions remain **not implemented**. None of this is upgraded by the reconciliation.

---

## 10. Scope 2

### 10.1 Method identity — the resolved correctness issue

**Requirement.** The calculation/result must be able to distinguish the accounting method, and the method must **not**
be inferred solely from factor metadata.

**Reconciled architecture (unchanged from ARCH-01, now acceptance-bound).**

* `scope2_method` is a **REQUIRED persisted dimension** on every Scope 2 result
  (`calculation_snapshots.scope2_method` and `emissions_logs.scope2_method`), constrained to
  `LOCATION_BASED | MARKET_BASED` — the vocabulary reused verbatim from the frozen disclosure contract.
* `scope2_method` is part of the deterministic **idempotency key**, so changing the method produces a *new* result
  rather than reusing the other method's snapshot.
* `scope2_method` is a **report dimension**; a market-based figure may never be aggregated or displayed under a
  location-based label, and vice versa (`AC-S2METHOD-01`).
* History is protected by `NOT VALID` CHECKs: the 34 existing snapshots/logs receive NULL and are never rewritten.

### 10.2 Energy types, facility and grid

* **Energy types (required, explicit):** `electricity | heat | steam | cooling` (ARCH-04 // ARCH-03 LOW-02 — the
  authoritative Scope 2 vocabulary is these **four** purchased-energy types; this line previously added `fuel`, which
  is **not** a Scope 2 energy type. Fuel-borne energy is a Scope 1/Scope 3 activity identified by the activity/factor,
  and a Scope 1/Scope 3 row carries `energy_type = NULL`). `cooling` currently has **zero** factors in the library, so
  a cooling activity must resolve to a **fail-closed review state** — never a fabricated result (POST-ARCH §27
  requires cooling "where applicable").
* **Facility:** a real `facility_id` FK to `facilities` for new writes (replacing JSONB-only attribution);
  `facilities` already carries `country`, `region`, `postcode`, `latitude`, `longitude`, `meter_mpan_mprn`.
* **Grid/region:** location-based accounting requires an explicitly resolved grid location, or an explicit recorded
  reason for national (country) resolution. Region-level factors do not exist today and remain deferred.

### 10.3 Location-based and market-based

* **Location-based:** exact reporting-year grid factor, matching country/geography, persisted factor provenance.
* **Market-based:** a valid allocated contractual instrument, or an evidenced supplier-specific factor; residual mix
  is **deferred** (FRAMEWORK-SPECIFIC); otherwise a **controlled review state** — never a location factor silently
  reused as a market factor.
* **Both methods coexist** for the same activity; UIUX-01 §24 requires an explicit comparison view and unmistakable
  methodological distinction.

### 10.4 Contractual instruments

The conceptual distinction is preserved: **INSTRUMENT EXISTS ≠ INSTRUMENT IS VALID FOR CLAIM.** Retained validation
concepts: tenant ownership; validity (window/geography/vintage/period); allocation; over-allocation prevention; claim
eligibility; evidence; accounting period; relationship to the market-based calculation. REGO/REC/residual-mix
framework rules remain **deferred**; no expansion is authorised here. UIUX-01 §23 adds the instrument surface
(type, issuer, coverage period, quantity, unit, applicable facility, evidence, validation status) — presented as a
governed instrument, never a free-text field.

### 10.5 Factor governance, evidence, reportability

* **Factor governance:** no silent cross-year fallback; candidates must expose reporting year, factor year, scope,
  geography, methodology, unit, factor set/source and applicability. The four call sites presenting unlabelled
  cross-year candidates are classified as an **implementation remediation requirement for P17-A** (not fixed here).
* **Evidence:** the activity's evidence plus, for a market claim, the **instrument's own** evidence.
* **Reportability:** reused P16 lifecycle; a Scope 2 result may not appear in reporting unless its reportability state
  permits it.

---

## 11. Scope 3

### 11.1 All 15 categories preserved

The full 15-category model is retained. **Scope 3 is not reduced to the categories that currently hold persisted
data**, and **category identity is a first-class accounting dimension** — a factor family must **never** be treated as
the category identity.

| # | Category | Architecture status |
|---|---|---|
| 1 | Purchased Goods and Services | PARTIAL |
| 2 | Capital Goods | NOT_IMPLEMENTED |
| 3 | Fuel- and Energy-Related Activities | SUPPORTED |
| 4 | Upstream Transportation and Distribution | SUPPORTED |
| 5 | Waste Generated in Operations | SUPPORTED (only category with persisted results) |
| 6 | Business Travel | SUPPORTED |
| 7 | Employee Commuting | PARTIAL |
| 8 | Upstream Leased Assets | PARTIAL |
| 9 | Downstream Transportation and Distribution | PARTIAL |
| 10 | Processing of Sold Products | NOT_IMPLEMENTED |
| 11 | Use of Sold Products | DEFERRED |
| 12 | End-of-Life Treatment of Sold Products | PARTIAL |
| 13 | Downstream Leased Assets | PARTIAL |
| 14 | Franchises | DEFERRED |
| 15 | Investments | DEFERRED (bounded `attribution_equity_share` only; PCAF deferred) |

### 11.2 Boundaries and the shared-factor finding

Categories **4/9** (inbound/outbound transport), **5/12** (operational waste vs sold-product end-of-life) and **8/13**
(lessee/lessor assets) **share factor families outright**. Therefore boundary/origin is a persisted property of the
activity, and the separations are enforced by the double-counting controls DC-04, DC-05 and DC-06 (unchanged).

### 11.3 Per-category requirements retained

For every category the reconciled baseline retains: canonical category identity · activity boundary · data
requirements · supplier involvement · evidence · estimation methodology where applicable · factor requirements ·
review · reportability · double-counting controls · **customer contribution** · **UI/UX requirements**.

> ⚠ **NARROWED BY ARCH-04** (ARCH-03 finding **LOW-04**): "customer contribution" and "UI/UX requirements" are
> **cross-cutting global requirements**, not per-category matrix fields. The Scope 3 matrix carries neither as a
> per-category field. They are now defined once in the matrix's new `cross_cutting_requirements` block, with acceptance
> via `AC-CUST-01/02/03`, `AC-ORGCTX-01`, `AC-AUDIT-01`, `AC-S3CAT-01` and `AC-UIUX-01`. Read this sentence as
> "the baseline retains these requirements **for every category, as cross-cutting requirements**" — not as a claim that
> each category row carries its own copy of those fields.

**Customer/consultant contribution per category (new emphasis):** POST-ARCH §28 requires that customers and
authorised consultants can contribute relevant data, with category-specific workflows and distributed contributors
(procurement, finance, facilities, HR, travel, logistics, waste, suppliers). UIUX-01 §25–§27 require category
navigation, a category overview, and a category detail workspace. Every contribution carries **source-actor**
provenance and passes the same governed pipeline (§8).

**Missing-data rule (UIUX-01 §26):** *"Do not represent 'no data' as 'zero emissions'."* A category with no data must
display as no data, not as a zero-emission result.

### 11.4 Methodology discipline

Methodologies are **not invented** for categories the PO explicitly defers. Category 11 (use of sold products),
14 (franchises) and 15 (investments) remain DEFERRED pending a PO decision; categories 2 and 10 remain
NOT_IMPLEMENTED pending a methodology and input-contract decision. Where an estimate is legitimately used, the
estimate is a persisted, first-class artefact (method, inputs, assumptions, factor, source, actor, timestamp) — no
silent estimation, and no arbitrary quantity invented for missing data.

### 11.5 Double-counting

All eleven ARCH-01 controls (DC-01…DC-11) are preserved unchanged, including: Scope 1 vs Scope 2; Scope 2 vs
category 3 derivation with a uniqueness constraint; category 1 vs 2; 4 vs 9; 5 vs 12; 8 vs 13; organisational-boundary
overlap; supplier vs estimated data (better data **supersedes** rather than adds); instrument double-claim;
repeat-calculation idempotency (extended with the new dimensions); and no reporting view materialising its own
emissions.

---

## 12. Security / Tenant Model

| Layer | Reconciled requirement |
|---|---|
| **Ownership** | Every accounting object is owned by an `organization_id`. A consultant never becomes the owner. |
| **API authorization** | `actor + organization context + role + capability + delegated relationship = permitted action` (POST-ARCH §35). Existing primitives retained: `require_auth`, `require_org_member`, `require_staff`, `require_internal_staff`, `ensure_org_access`, `ensure_staff_permission(can_review/can_process)`, `_entity_workspace_guard`, `consultant_auth.py`. |
| **RLS** | RLS remains enabled on the ratified table set with `is_org_member()` policies. No policy is weakened by this reconciliation. New P17 tables follow the established RLS/privilege convention. |
| **Delegated access** | Authorized and auditable; **per client**; revocable; revocation effective server-side; Client A access must not imply Client B (POST-ARCH §18, §36). |
| **Acting-for** | Persisted context; never the authorization boundary; the UI banner is not a security control. |
| **Frontend** | Explicitly **not** an authorization mechanism (POST-ARCH §35; UIUX-01 §44, §63). Disabled controls and hidden routes are not authorization. |
| **Cross-client / cross-tenant** | `AC-DELEG-01` and `AC-CUST-03` require ALLOW **and** DENY evidence, including a cross-client matrix (consultant A → client B), consultant → own-org confusion, and client → another organization. |
| **Service role** | Must not be used to bypass tenant isolation on normal application paths. |

**Acceptance rule:** every security-sensitive capability must be tested for **both** the permitted case and the denied
case. An unexpected ALLOW is a serious finding.

---

## 13. UI/UX Architecture

**The approved UI/UX standard is part of the accounting architecture, not a later presentation concern**
(UIUX-01 §58, §59, §74, §76; POST-ARCH §41; PO-CAMS §6, §23).

### 13.1 What the reconciliation changes

| Before (ARCH-01) | After (ARCH-02) |
|---|---|
| UI/UX largely out of phase scope; "Step 3 UI" implied later | **UI/UX is in-phase deliverable scope** for every affected phase |
| Acceptance could be satisfied by backend + route evidence | **Backend-only is not completion** for UI/UX-scoped requirements (UIUX-01 §58) |
| A capability flag could be considered "done" without its UX | A capability flag **without** its user experience is not a feature (UIUX-01 §59) |
| No explicit UX verdict | Every phase reports a **UIUX-01 §74 verdict** (`UIUX_PASS` / `UIUX_PARTIAL` / `UIUX_FAIL` / `UIUX_BLOCKED`) |

### 13.2 Required UX properties (architectural, not cosmetic)

* **Organization context** visible on every accounting screen (UIUX-01 §5).
* **Acting-for context** visible throughout the client workflow when a consultant operates for a client (UIUX-01 §6),
  and **server-enforced independently**.
* **Data owner / operator / acting-for** distinguishable in evidence, activity data, supplier data, calculations,
  reports and audit history (UIUX-01 §64).
* **Report ownership** shown as report-organization vs prepared-by (UIUX-01 §65).
* **Client switching** that revalidates authorization (UIUX-01 §13, §63).
* **Scope navigation** for Scope 1/2/3 and **category navigation** for all 15 Scope 3 categories (UIUX-01 §17, §21, §25).
* **Data collection, evidence, suppliers, review queue, exceptions, calculations, calculation provenance,
  reportability, reporting, audit/history, data quality and capability settings** surfaces (UIUX-01 §28–§43).
* **Truthful state communication:** `DRAFT…REPORTABLE / REJECTED / INVALIDATED / SUPERSEDED` (UIUX-01 §42);
  reportability must never be implied by the mere existence of a calculation (UIUX-01 §38); missing data is never
  rendered as zero emissions (UIUX-01 §26, §41); loading, empty, error, disabled-capability and permission-denied
  states are required (UIUX-01 §43–§47).
* **Review/approval authority** must not be implied by visibility: approval is a separate capability (UIUX-01 §68).
* **Controlled overrides** must be explicit, with reason + evidence and an audit record — no silent overrides
  (UIUX-01 §69); destructive/accounting actions require confirmation explaining downstream consequences (UIUX-01 §70).
* **Accessibility** and **responsive** baselines preserved (UIUX-01 §52, §53).

### 13.3 Discovery is a precondition, not an implementation step

UIUX-01 §54/§55/§57 require a repository inventory and an **existing-vs-missing matrix** before any UI or backend
change; §56 requires a **UX acceptance matrix** across Staff / Direct Org / Consultant Own / Consultant Client /
Client User / Disabled State / Audit / Backend Auth / UI Complete. Both are produced in the new **P17-0** phase. The
ASCII screens are a **standard to map against**, explicitly not permission to rebuild the application (UIUX-01 §57),
and duplicate navigation/UX systems are prohibited (UIUX-01 §60, §61).

**This reconciliation creates no UI code.** It records UI/UX as architecture and acceptance scope.

---

## 14. Schema Reconciliation

Full detail: `artifacts/p17_schema_delta_20250925.md` §10. **No migration is created by ARCH-02.**

| Item | Disposition |
|---|---|
| consultant ↔ client relationship | **EXISTS — REUSE** (`consultant_clients`, 2 rows, full lifecycle). No new relationship entity. |
| consultant identity / firm membership | **EXISTS — REUSE** (`consultant_profiles`, `consultant_firm_members`) |
| membership + role | **EXISTS — REUSE** (`organization_members.user_id`, `.role`, `.is_active`) |
| capability / organization policy | **P17-0 DECISION**; recommendation: a capability-key dimension on the ratified three-scope pattern (`organization` \| `consultant_firm` \| `consultant_client`) already used by `manual_processing_grants`. Prohibited: a global flag or a duplicate policy system. |
| acting-for / actor-organization context | **NEW** additive nullable columns on `calculation_snapshots`, `emissions_logs`, `evidence_line_items` and the audit writer. Ownership stays `organization_id`. |
| governed lifecycle | **EXTEND / MAP** existing state machines (`customer_documents.status`, `ITEM_STATUS_FLOW`, `report_versions`, P16 reportability). No new lifecycle table. |
| ownership fields | **NO CHANGE** |
| audit context | **EXTEND** the existing audit model |
| ARCH-01 schema delta (dimensions, `NOT VALID` constraints, four new entities, migration slots) | **UNCHANGED** |

**Duplicate models explicitly prohibited:** a second consultant-client relationship; a second capability/policy
system; a second lifecycle; a second reportability model; a customer/consultant/client/staff calculation engine.

---

## 15. Phase Plan Reconciliation

Full detail: `CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` §16.

| Change | Detail |
|---|---|
| **NEW prerequisite phase P17-0** | Discovery + existing-vs-missing mapping + capability-model reconciliation + lifecycle mapping table. **Blocks P17-A and every later phase.** No code changes. |
| **UI/UX in-phase** | P17-B … P17-I each deliver the applicable UI/UX in the same phase. |
| **Capability + disabled/permission states** | Scope and acceptance additions across B/C/E/F/G/H/I. |
| **Lifecycle** | Every entry path (staff, customer, consultant) exhibits the governed lifecycle; P17-H extended. |
| **Acting-for** | Persisted context + acceptance criterion, principally in B/C/H. |
| **Client-org isolation** | Consultant-delegated operation and cross-client denial are explicit phase criteria. |
| **No backend-only PASS** | Applies to all delivery phases. |
| **Verdict vocabulary** | The UIUX-01 §74 verdict is added alongside PASS/PARTIAL/FAIL/BLOCKED/DEFERRED. |
| **Unchanged** | Phase order A→B/C→D→E/F/G→H→I→J; migration slots `20261010000000`…`20261014000000` (proposals only); P17-A schema scope; DC controls; idempotency; reportability; the P16 non-regression requirement. |

**Guard against premature implementation:** P17-A may not be authorised until (a) P17-0 completes, and (b) this
reconciled baseline is independently verified. The phase plan now states this explicitly.

---

## 16. Acceptance Matrix Reconciliation

Full detail: `artifacts/p17_acceptance_matrix_20250925.json` → `reconciliation_arch02`.

**Added:** the **P17-0 `DISCOVERY_AND_MAPPING` gate**; seven global acceptance amendments (including *no backend-only
acceptance* and *no flag-without-UX*); and twelve new criteria — `AC-CAMS-01`, `AC-ORGCTX-01`, `AC-CUST-01`,
`AC-CUST-02`, `AC-CUST-03`, `AC-DELEG-01`, `AC-LIFECYCLE-01`, `AC-S2METHOD-01`, `AC-S2INST-01`, `AC-S3CAT-01`,
`AC-UIUX-01`, `AC-AUDIT-01`.

**Preserved unchanged:** the ten ARCH-01 phase gates (P17-A…P17-J), the twelve invariant tests (T-INV-01…T-INV-12),
the eleven double-counting controls (DC-01…DC-11), the END-TO-END VERIFIED rule and the P16 reportability reuse
requirement.

**Acceptance language.** Acceptance remains **END-TO-END**: UI → API → authorization → domain/service → database →
audit/provenance → calculation/reportability → **UI reflects final state** (UIUX-01 §58). A backend-only
implementation must **not** qualify as PASS where UIUX-01 requires UI/UX.

---

## 17. Deferred Items

**All legitimately deferred items are preserved. Nothing was silently promoted by this reconciliation.**

| Item | Status preserved |
|---|---|
| Numeric uncertainty / confidence values | DEFERRED |
| Residual mix | FRAMEWORK-SPECIFIC / DEFERRED |
| REGO / REC / GO jurisdiction-specific instrument rules | FRAMEWORK-SPECIFIC / DEFERRED |
| Grid-region-level location factors | DEFERRED |
| Spend-based estimation as a default | PO DECISION REQUIRED |
| Category 2 (capital goods) methodology | PO DECISION REQUIRED |
| Category 10 (processing of sold products) methodology | PO DECISION REQUIRED |
| Category 11 (use of sold products) methodology | PO DECISION REQUIRED |
| Category 14 (franchises) operating model | PO DECISION REQUIRED |
| Category 15 (investments) beyond `attribution_equity_share` (incl. PCAF) | FRAMEWORK-SPECIFIC / DEFERRED |
| Sold-product entity | DEFERRED |
| Framework/disclosure content (requirement sets, official identifiers) | DEFERRED |
| CarbonTally Insight redesign | DEFERRED |
| Factor-library expansion (2026 set, new families) | DEFERRED |
| SEAI expansion | DEFERRED (Version 4) |
| Production deployment | NOT AUTHORISED |

**One item changed category:** "Step 3 UI as a separate workstream" is no longer deferred — UI/UX is **folded into the
phases** as in-phase scope. This is not a promotion of deferred work but the removal of an artificial separation that
the PO standard explicitly rejects (UIUX-01 §58, §76).

---

## 18. Implementation Prohibition

> **No P17 implementation was performed.**

No P17-A, no Scope 2 implementation, no Scope 3 implementation, no migrations, no schema change, no API routes, no
service or engine change, no factor change, no UI code, no RLS change, no seed data, no test changes. This task
produced architecture and documentation artifacts only:

* `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` (new)
* `docs/architecture/artifacts/p17_architecture_reconciliation_20250925.json` (new)
* `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` (§15 status + new §16)
* `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` (`reconciliation_arch02`)
* `docs/architecture/artifacts/p17_schema_delta_20250925.md` (new §10)
* `docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json` and
  `.../p17_scope3_category_matrix_20250925.json` (minimal reconciliation pointers only)

**P17-ARCH-01 was not modified** and remains byte-identical.

---

## 19. Production Safety

> **No production system was contacted or modified.**

No production database access, no migration, no deployment, no production API call, no infrastructure change. All
discovery used the local Demo Lab (`carbontally_demo_local` @ `127.0.0.1:54426`) read-only, plus static inspection of
the working tree. The integration harness (which truncates its target — invariant F-046-1) was **not** run.

---

## 20. Known Remaining Risks

| # | Risk / open question | Impact | Required action |
|---|---|---|---|
| R1 | **Capability representation is undecided** (extend the ratified three-scope governance primitive vs a new table). | Blocks P17-A if unresolved; a wrong choice creates a duplicate policy system. | P17-0 decision, recorded with rationale. |
| R2 | **Acting-for has no existing implementation**; it is genuinely new and touches the audit and calculation write paths. | Medium-high: affects idempotency digest inputs and audit semantics. | P17-0/P17-A design; must not alter historical rows; must be included in the request-id digest decision. |
| R3 | **The lifecycle mapping is not yet produced.** The PO lifecycle must be shown satisfiable by the existing machines without a parallel state machine. | High: a mapping failure could force a state-machine change to a P16-verified area. | P17-0 deliverable before P17-H. |
| R4 | **The UI inventory is incomplete.** `frontend/src` is a flat legacy JSX tree plus `v3/` and `components/`; the true reuse map is unknown. | High: UI/UX is now in-phase scope, so an unknown baseline risks effort underestimation or duplicate UX. | P17-0 §54/§55/§56 matrices. |
| R5 | **The four factor-candidate call sites remain unfixed** (unlabelled cross-year candidates). | Latent today (all factors are 2025); becomes an accounting defect at the second factor year. | P17-A remediation. |
| R6 | **The `roles` table is empty** while authority actually lives in `staff_roles` / `organization_members.role`. | Medium: a capability/role model built on the wrong table would be wrong. | P17-0 must establish which authority source is canonical. |
| R7 | **Scope 2 factor coverage is thin** (4 + 2 grid kWh rows; zero cooling; 340 EV/transport rows) and region-level factors do not exist. | Medium: several Scope 2 journeys will land in fail-closed review rather than producing numbers. | Accept review-state outcomes; do not fabricate factors. |
| R8 | **Effort is materially larger than ARCH-01 implied**, because UI/UX is now in-phase for every affected phase. | High (planning). | Re-estimate at P17-0 close; consider splitting E/F/G further. |
| R9 | **Disclosure/reporting is "exists but disconnected"** (`disclosure_values` = 0, `report_version_artifacts` = 0). | Medium: P17-I must produce a real artefact, not merely wire routes. | P17-I gate unchanged (real artefact required). |
| R10 | **Independent verification of this reconciliation has not occurred.** | Blocks implementation authorisation. | An independent architecture verification/freeze review must follow. |

---

## 21. Final Status

**`P17_ARCH_RECONCILED_READY_FOR_VERIFICATION`**

Rationale: the reconciliation is **internally coherent**; every approved PO decision has been incorporated with an
explicit before/after record (§5); implementation dependencies are identified (§14, §20); acceptance criteria are
updated (§16); deferred items are preserved (§17); and **no known architectural contradiction remains** — all five
identified contradictions are resolved in §5.2.

**This status is not `P17_ARCH_RECONCILED_PASS`, and implementation is NOT authorised.**

**Independent verification is mandatory next.** Cline reconciliation is **not independent acceptance**. This baseline
must be independently verified and frozen before any P17 implementation — including P17-0 and P17-A — is authorised.

---

## Document Control

**Document:** `CT-PO-P17-ARCH-02-RECONCILIATION-20250925`
**Task:** `P17-ARCH-02-20260925-RECONCILE-FREEZE`
**Starting SHA:** `98a89d0c1ab0e850d4ca44e348a66da0515dc691`
**Supersedes:** the *unreconciled implementation baseline* of `P17-ARCH-01` (which remains preserved and unmodified)
**Reconciled status:** `P17_ARCH_RECONCILED_READY_FOR_VERIFICATION`
**Implementation authorised:** NO · **Migrations created:** NONE · **Production:** NOT CONTACTED
**Independent verification required:** YES

---

# ARCH-04 ADDENDUM — reconciliation of independent ARCH-03 findings

**Date:** 2025-09-25 (added after independent verification — ARCH-02's original findings above are preserved unchanged)
**Added by:** `P17-ARCH-04-20260925-RECONCILE-INDEPENDENT-FINDINGS`
**Independent source:** `CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` — verdict **`P17_ARCH_FREEZE_PARTIAL`**
**Correction authority:** `docs/architecture/CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md`

## A4.1 Why this addendum exists

ARCH-02 was independently verified and returned **`P17_ARCH_FREEZE_PARTIAL`** with seven findings. This addendum
records the **before/after classification** for each, so the historical record remains auditable: the original ARCH-02
claims stand above as written, and every correction is dated and attributed. ARCH-02's text is **not** rewritten as
though the findings had been known in advance.

## A4.2 Before / after classification

| # | Area as claimed by ARCH-02 | ARCH-03 finding | Before | After | Reason |
|---|---|---|---|---|---|
| HIGH-01 | Consultant organization identity (`consultant_profiles` + `consultant_firm_members`) | Consultant-organization identity over-claimed | `EXISTS — VERIFIED` | **`PARTIAL — MISSING LINKAGE`** | `consultant_profiles` is keyed by `user_id` with no `organization_id`; no FK to `organizations`; `consultant_clients.consultant_id` → `consultant_profiles(id)`; no `organization_type`; no `organization_relationship` table. The consultant's **own** accounting has no verified organization to be recorded under. The PO decision (consultant is a first-class organization) is unchanged; the **linkage** is what is missing. |
| MEDIUM-01 | Acting-for columns on snapshots, logs, evidence, audit writer | Propagation narrower than `AC-AUDIT-01` | 4 paths | **8 paths** with per-path (A)/(B) disposition | `AC-AUDIT-01` covers every material accounting change; `customer_documents`, `suppliers`, `review_audit_trail`/`review_assignment_history` and `report_versions`/report artefacts also lack acting-for context. |
| MEDIUM-02 | P17-E gate: "one E2E result per category (1,2,3,4,5)" | Contradiction with category 2 = NOT_IMPLEMENTED | no caveat | **status-conditional acceptance** | P17-F/P17-G already carried "where the category is not DEFERRED" language; P17-E did not, contradicting ARCH-02 §11.1 and the matrix `status_rollup`. |
| LOW-01 | Tenant key (`organization_id` in the schema delta; `claimant_organization_id` in the matrix/DC-09) | Two names for one role | inconsistent | **canonical conceptual name + explicit physical mapping** | `claimant_organization_id` is the precise conceptual name for the claim owner; the proposed physical column is `organization_id`. One-to-one mapping documented (schema delta §10.6). |
| LOW-02 | `energy_type` vocabulary | 5 values here, 4 in the matrix | inconsistent | **4 values (authoritative)** | `fuel` is not a Scope 2 energy type; it is a Scope 1/Scope 3 activity. Excluded from the vocabulary. |
| LOW-03 | `post_contract_po_decisions` fields in the acceptance JSON | Stale metadata | `APPROVED_PO_DECISIONS_REQUIRING_RECONCILIATION`, `reconciliation_performed: false` | **`RECONCILED_BY_ARCH_02_WITH_ARCH_04_CORRECTIONS`** | ARCH-02 had already reconciled the PO records, so the fields contradicted `reconciliation_arch02`/`current_verdict` in the same file. |
| LOW-04 | §11.3 claim that per-category baseline "retains customer contribution and UI/UX requirements" | Implied per-category fields that do not exist | over-broad wording | **narrowed to cross-cutting requirements** | The Scope 3 matrix carries these globally, not per category. Defined once in the matrix's `cross_cutting_requirements` block. |

## A4.3 Corrections that become P17-0 obligations (not implemented here)

1. **Consultant ↔ organization identity/linkage** — a **mandatory P17-0 decision** (authoritative organization identity
   model for the consultant firm, its users/members, its client organizations and its own Scope 1/2/3 ownership;
   extend existing structures vs additive linkage). No implementation in P17-0.
2. **Acting-for propagation map** — P17-0 must produce the per-path map (owner · actor · actor organization ·
   acting-for organization · persisted? · safely derivable? · additive implementation required?) for source/activity
   documents, suppliers, review/approval decisions, report artefacts, calculations, evidence and the audit trail.
3. **Acceptance consistency check** — P17-0 must verify that phase acceptance criteria are internally consistent with
   category status, deferred scope, PO methodology decisions and E2E requirements.
4. **Lifecycle** — the mapping table must explicitly name `CORRECTION REQUIRED` (or document its existing rework-edge
   representation) rather than leaving the state unnamed (ARCH-03 §11 residual).

## A4.4 Addendum scope statement

This addendum is a **documentation correction only**. It creates no column, no table, no migration, no code and no UI.
It does not authorise P17-0 or P17-A. `ARCH-01`, the ARCH-03 report and the P16 final verification were **not**
modified.











