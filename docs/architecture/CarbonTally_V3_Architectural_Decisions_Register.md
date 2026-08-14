# CarbonTally V3 Architectural Decisions Register

**Version:** 1.1
**Date:** 2026-08-11 (v1.1) · 2026-08-10 (v1.0)
**Status:** REGISTER COMPLETE — READY FOR IMPLEMENTATION GATE
**Mode:** **DOCUMENTATION-ONLY.** No code, database, migration, RLS, Storage, API, frontend or test changes were made. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

**v1.1 update (2026-08-11):** ADR-V3-002 and ADR-V3-014 are now **DECIDED** — the four
customer-factor sub-decisions (D-cf-2 snapshot FK → O1, D-cf-3 approval authority → Organization
Admin/Owner, D-cf-5 factor precedence → approved customer factor first, R3 consultant access →
existing consultant-client relationship/RLS model) are resolved, and V3M-4 is **DECIDED — READY
FOR IMPLEMENTATION** (provider-independent emission-factor architecture; individual provider
imports remain separate implementation tasks). See §5 (ADR-V3-002/014/015), §6, §9, §10 and §X.

---

## 1. Purpose

This register is the central, authoritative record of architectural decisions for
CarbonTally V3. It exists so that Cline or future developers do **not** independently
redesign the architecture feature-by-feature during implementation. Every major V3
decision is recorded here with:

- an explicit status (DECIDED / PROVISIONALLY DECIDED / OPEN / INVESTIGATE / DEFERRED / REJECTED),
- the evidence and source document/section that supports it,
- the current architecture it builds on,
- the constraints that must not be violated,
- the dependencies that must be resolved first, and
- the implementation impact on DB / Backend / API / Frontend / RLS.

Decisions recorded in this register are **not** implementation instructions. V3
implementation may begin only when the Implementation Gate (§10) is satisfied.

---

## 2. Status Legend

| Status | Meaning |
|---|---|
| **DECIDED** | The architecture is settled on the evidence; implementation of this decision does not require further architecture work. |
| **PROVISIONALLY DECIDED** | The architectural direction is established and evidence-backed, but one or more blocking dependencies (OPEN sub-decisions) must be resolved before it may be implemented. **Provisionally-decided architecture is for planning only — it is NOT authorization to implement DB, API, RLS, backend, or frontend changes until all blocking dependencies are resolved.** |
| **OPEN** | No decision has been made. The source material explicitly leaves it to human decision (or provides insufficient evidence). Must be resolved before the affected implementation can proceed. |
| **OPEN SUB-DECISION** | A specific sub-question of a PROVISIONALLY DECIDED ADR that remains unresolved and blocks the affected functionality of that ADR. |
| **INVESTIGATE** | A risk or unknown that must be investigated before implementation; the answer may change the decision. |
| **DEFERRED** | Deliberately postponed to a later V3 phase; not blocking current implementation. |
| **REJECTED** | An approach was considered and explicitly rejected by the source evidence. Do not resurrect without a new decision. |

---

## 3. Architectural Principles

Established by cross-referencing the three source documents. These principles are
binding on all V3 implementation work.

1. **V3 is an extension of V2.1, not a rewrite.** The canonical processing pipeline
   (validation → normalisation/match → calculation → CO₂e outputs) already exists as
   engines and repositories and is carried into V3 largely unchanged.
   Source: V3 IA §1, §6, §28.

2. **Do not duplicate existing domain infrastructure.** Where the current system already
   has a working mechanism (matching, calculation, snapshots, audit, SLA, workload,
   assignment history, escalation, configuration), V3 extends it — it does not create a
   parallel system.
   Sources: V3 IA §28 (REUSE verdicts); CF Audit §29 (components that must NOT be created);
   Queue Audit §11 Option D rejection.

3. **Prefer extending proven active structures over creating parallel ones.** The active
   structures (`manual_review_queue`, `review_assignment_history`, `customer_verifications`,
   `queue_settings`, `sla_*`, `staff_workload`, `calculation_snapshots`, `factor_aliases`
   RLS pattern) are the extension targets.
   Sources: Queue Audit §18; CF Audit §5, §8.

4. **Separate human Work Items from technical processing state machines.** Human
   operational work is represented by Work Items; technical pipelines
   (`document_processing_queue`, `report_generation_queue`) are state machines, not human
   work queues. Do not collapse these concepts.
   Source: Queue Audit §18, §1.

5. **Queues are logical where possible.** A queue is a filtered view over Work Items
   (e.g. "pending and unassigned"), not a new physical table per queue.
   Source: Queue Audit §6, §11.

6. **Preserve existing RLS boundaries and the factor baseline.** `emission_factors`
   (global reference, 7,049 rows, natural key, authenticated SELECT USING(true)) is
   immutable. Existing tenant/org RLS is never weakened.
   Sources: CF Audit §2.1, §19, §29, §33; V3 IA §9.

7. **Do not redesign engines unnecessarily.** Matching, calculation and validation
   engines are extended, never replaced. Customer factors enter as an additional
   candidate source; no second engine.
   Sources: CF Audit §6, §7, §28, §29; V3 IA §10, §11.

8. **Do not implement unresolved architecture decisions.** Decisions marked OPEN or
   INVESTIGATE (or with unresolved OPEN SUB-DECISIONS) are not implemented until resolved.
   Source: V3 IA §27 ("Cline must not make these autonomously"); §29 (no migration until human decisions taken).

---
## 4. Decision Summary Matrix

| ID | Decision | Status | Architectural Direction | Implementation Impact |
|----|----------|--------|-------------------------|-----------------------|
| ADR-V3-001 | Processing Entity Architecture | **DECIDED** ✅ | **Option B — dedicated `processing_entities` table**; `staff_profiles.entity_id IS NULL` = CarbonTally internal processing; `entity_id` populated (= `processing_entities.id`) = Processing Entity staff. | DB NEW (V3M-1); RLS NEW (entity policies); Backend/API NEW |
| ADR-V3-002 | Customer-Owned Emission Factors | **DECIDED** ✅ | Dedicated `customer_factors` table (Option B); 4 sub-decisions resolved (D-cf-2 O1 snapshot FK; D-cf-3 org Admin/Owner approval; D-cf-5 approved-customer-first precedence; R3 existing consultant-client RLS model). | DB NEW (table + snapshot-FK); RLS NEW; Backend/API EXTEND + NEW |
| ADR-V3-003 | Work Item / Queue Architecture | **PROVISIONALLY DECIDED** | Canonical Work Item abstraction over `manual_review_queue`; logical queues; technical state machines separate; no fifth queue. | DB none (unless entity scope); Backend NEW (domain layer); API EXTEND |
| ADR-V3-004 | Document Processing State Machine | **PROVISIONALLY DECIDED** | `document_processing_queue` remains a technical state machine; needs an active producer (V3 document work type); not the canonical human queue. | DB none; Backend NEW (producer); API EXTEND |
| ADR-V3-005 | Assignment & Reassignment | **PROVISIONALLY DECIDED** | Reuse `review_assignment_history` as the attribution mechanism; reconcile dormant `reassignment_history`/`processing_assignments` before retirement. | DB none; Backend EXTEND; API EXTEND |
| ADR-V3-006 | SLA / Priority / Escalation / Capacity | **PROVISIONALLY DECIDED** | Reuse existing `queue_settings`/`sla_*`/`staff_workload`/`business_hours`/escalation; extend for entity scope. No duplicate systems. | DB CONDITIONAL (entity scope); Backend EXTEND |
| ADR-V3-007 | Auto Assignment | **PROVISIONALLY DECIDED** | AutoAssignmentEngine is backend orchestration over existing config/capacity/priority; no new tables; skills unresolved. | DB none; Backend NEW (engine); API NEW |
| ADR-V3-008 | Customer Review / Approval | **PROVISIONALLY DECIDED** | Keep `customer_verifications`; approval vocabulary exists but is wired to a dormant queue — REPOINT at Work Items when built. | DB none; Backend EXTEND; API EXTEND |
| ADR-V3-009 | Issue Management | **DECIDED** | **Option B — First-Class Issue Management Model**: Issue is a first-class operational domain object, distinct from Conversation; conversations may be associated where communication is required. Implementation pending. | DB CONDITIONAL (issues table); Backend NEW; API NEW; RLS NEW |
| ADR-V3-010 | RLS / Security / Tenant Isolation | **PROVISIONALLY DECIDED** | Extend existing org RLS; entity RLS per ADR-V3-001 (now DECIDED — implementation pending); legacy permissive policies flagged **INVESTIGATE/HARDEN**; no weakening. | RLS EXTEND (conditional); INVESTIGATE |
| ADR-V3-011 | Work Item Identity & Work Types | **PROVISIONALLY DECIDED** | Work Item = atomic unit; work_type distinguishes review/extraction/QC work; no new identity scheme (existing PKs). | DB none; Backend NEW (domain) |
| ADR-V3-012 | Batch vs Atomic Work Item | **DECIDED** | Batch = grouping (`upload_batches`), Work Item = atomic (`manual_review_queue` rows); never conflate. | DB none |
| ADR-V3-013 | Audit / History Strategy | **PROVISIONALLY DECIDED** | `review_assignment_history` + `domain_events` + `audit_trail` + snapshots; consolidate duplicate history surfaces at the work-item boundary. | DB none; Backend EXTEND |
| ADR-V3-014 | Snapshot / Provenance for Customer Factors | **DECIDED** ✅ | `calculation_snapshots` reused unchanged; provenance via `factor_source='CUSTOMER'`; snapshot FK option **O1** adopted (nullable `factor_id` + `factor_kind` + optional `customer_factor_id`, exactly-one-source check) — D-cf-2 resolved. | DB CONDITIONAL (O1 FK); Backend EXTEND |
| ADR-V3-015 | Factor Provider Architecture | **DECIDED** | DEFRA/SEAI stay; EPA (IE) fits with no schema change; ADEME/IPCC/EU DEFERRED (country CHECK + natural-key widening only if they enter). **Provider-independent architecture confirmed (V3M-4 DECIDED — READY FOR IMPLEMENTATION):** no separate factor database, no provider-specific calculation engine; future providers use the same provider/import architecture as separate implementation tasks. | DB none (unless deferred providers enter) |
| ADR-V3-016 | Queue Consolidation & Retirement | **DEFERRED** | `processing_queue` family retires only after Work Item model + document work type + re-pointing are done. Dependency chain gated. | DB none until chain completes |

**Status counts:** DECIDED 6 · PROVISIONALLY DECIDED 9 · OPEN 0 · INVESTIGATE 0 · DEFERRED 1 · REJECTED (see §8).

---
## 5. Detailed Decisions

### ADR-V3-001 — Processing Entity Architecture

**Status:** **DECIDED — Option B** ✅

**Decision**
**Option B — dedicated `processing_entities` table.** Processing Entities are a first-class
domain and are **never** represented by the customer `organizations` table (data owner vs
processor distinction). The approved architectural convention:
- `staff_profiles.entity_id IS NULL` = CarbonTally internal processing.
- `staff_profiles.entity_id` populated (= `processing_entities.id`) = staff member belonging
  to a Processing Entity.

Decision reviewed and approved by the architecture/product owner.

**Why**
The Processing Entity Decision Analysis evaluated the candidate models against the repository
and recommended **Option B**; Options A (`organizations.org_type` discriminator) and C
(parent-org + entity child) were **rejected** (PE Decision Analysis §5–§8, §22). The Open
Questions Classification validated that no architecture-blocking question prevents the
decision — Q5 (CarbonTally-internal representation) is already answered by the NULL
convention (PE Open Questions Classification — Recommendation). No `processing_entities`
structure exists in the schema today; the multi-entity (500-doc) case requires this decision
(Queue Audit §10). The V3 IA §27 H1 human decision is now recorded as resolved.

**Current Architecture**
- CarbonTally organization = `organizations` tenant row; staff = `staff_profiles` +
  `organization_members`; no entity concept.
- All work-item/queue/SLA structures are org-scoped, not entity-scoped.
- No `entity_id` on `manual_review_queue`, `upload_batches`, or any work table.

**V3 Direction**
- NEW dedicated `processing_entities` table (V3 IA §8 V3M-1; PE Decision Analysis §22):
  lifecycle status (active / remediation-suspended / terminated) + contract metadata
  (exact commercial fields deferred to V3 schema design — Q1).
- `staff_profiles.entity_id` nullable FK → `processing_entities(id)`; `NULL` = CarbonTally
  internal processing (Q5 convention).
- Entity scope on work tables (V3M-2: `manual_review_queue`, `upload_batches`) follows the
  dependent ADRs (V3-003 work-item scope, V3-006 SLA, V3-010 RLS).
- Entity-scoped RLS: deny-by-default + `is_entity_member()` (per ADR-V3-010).

**Provisionally decided clarifications (part of the DECIDED record — exact fields/authority finalized in V3 design):**
- **Entity contract metadata (Q1):** Processing Entities have a contractual/commercial
  relationship with CarbonTally; contract metadata is recognized as part of the Processing
  Entity domain. Exact commercial fields, pricing structures and detailed contract schema are
  deferred to the V3 architecture/schema design phase. (Classification: PROVISIONALLY DECIDED.)
- **Entity onboarding/offboarding workflow + authority (Q6):** onboarding is controlled by
  authorized CarbonTally personnel; Processing Entities cannot self-activate; lifecycle
  supports operational states including active, remediation/suspended and terminated;
  suspension/termination must NOT delete historical work, audit, performance or issue history;
  active/assigned work must have a defined reassignment/disposition process on
  suspension/termination; entity users' operational access must respect entity lifecycle.
  Exact lifecycle states, transition authority and the RBAC matrix are finalized during V3
  architecture/RBAC design. (Classification: PROVISIONALLY DECIDED.)
- Source: `docs/audit/CarbonTally_V3_Processing_Entity_Open_Questions_Classification.md` (§24 Q1, Q6 — owner clarification).

**Constraints**
- Must NOT implement the entity model in this register (documentation-only).
- Must NOT create `entity_id` columns or entity RLS without a DB-change plan and migration
  design (V3M-1/V3M-2) approved at the Implementation Gate (§10).
- Must preserve existing org isolation while adding the entity boundary (no weakening).
- Must NOT resurrect rejected options (A — `organizations.org_type`; C — parent org) without
  a new decision.

**Dependencies**
- Resolved: V3 IA §27 H1 (human decision) — recorded as DECIDED — Option B.
- Dependent sub-decisions belong to other ADRs: Q2 (entity_id on dpq/manual_extraction/report
  tables) → ADR-V3-004/016; Q3 (entity SLA) → ADR-V3-006; Q4 (entity capacity) →
  ADR-V3-007/006; Q7 (`is_entity_member` RLS) → ADR-V3-010; Q8 (issue entity context) →
  ADR-V3-009; Q9 (storage access) → ADR-V3-010/V3-016.
- Q10 (migration sequencing) = IMPLEMENTATION DETAIL (§28.2 order).
- ADR-V3-001 no longer blocks ADR-V3-003/006/010 entity scope at the gate.

**Implementation Impact**
- **DB:** NEW — `processing_entities` + `staff_profiles.entity_id` (V3M-1); entity scope on
  work tables (V3M-2) — designed before any migration (§10 gate).
- **RLS:** NEW — entity-scoped policies (deny-by-default + `is_entity_member()`) per
  ADR-V3-010 pattern.
- **Backend:** NEW — `ProcessingEntity` domain/repo/API.
- **API:** NEW — entity-ops routes.
- **Frontend:** entity-admin surfaces (later phase).

---

### ADR-V3-002 — Customer-Owned Emission Factors

**Status:** **DECIDED** ✅

**Decision**
Customer-owned factors are implemented as a dedicated org-scoped **`customer_factors`**
table, kept fully separate from the global CarbonTally-managed `emission_factors` reference.
Matching and calculation engines are **extended** (customer candidates merged alongside
CarbonTally candidates; `factor_source='CUSTOMER'` provenance), never duplicated. The
unavoidable schema change is the `calculation_snapshots.factor_id` FK relaxation.

The four previously OPEN SUB-DECISIONS are now **RESOLVED** (v1.1, 2026-08-11) and this ADR
is **DECIDED — READY FOR IMPLEMENTATION** (V3M-3). Decision reviewed and approved by the
architecture/product owner.

**Why**
The focused audit demonstrates: (a) `emission_factors` is global authenticated-read
reference data whose natural key has no org dimension — adding org rows breaks the global
model, RLS, and import provenance (CF Audit §10 Option A REJECTED); (b) the engines are
ownership-agnostic and candidate-set-agnostic, so extension is minimal (CF Audit §6, §7, §8);
(c) the org-isolation RLS pattern already exists in `factor_aliases` (`is_org_member()`) and
is reusable (CF Audit §9); (d) the minimum change set is one new table + snapshot-FK
resolution + engine extensions + ~7 additive routes (CF Audit §30).

**Current Architecture**
- All factors resolve from global `emission_factors` (7,049 rows); no customer-factor path
  exists in v2.1 matching, calculation, or legacy processing.
- `calculation_snapshots.factor_id` is NOT NULL with FK → `emission_factors(id)` — this is
  the single schema obstacle (CF Audit §7, §16).
- `factor_aliases` provides org-scoped synonyms only (not values).
- Legacy CSV processing silently overwrites customer-supplied factor values with the
  CarbonTally factor (CF Audit §5) — no validation, no detection of mismatches.

**V3 Direction**
- New `customer_factors` table (org FK NOT NULL, activity_type, co2e_multiplier, unit,
  scope, country, reporting_year, factor_source, source_reference, status, version,
  effective_from/to, metadata, created_by/at, updated_at) with immutable version discipline.
- RLS `customer_factors_select_own` USING `is_org_member(organization_id)` (+ insert/update
  member; delete restricted/soft-deactivate) — CF Audit §9, §19, §30.
- Matching EXTEND: merge ACTIVE customer factors as candidates — CF Audit §15.
- Calculation EXTEND: accept customer factor; snapshot provenance `factor_source='CUSTOMER'`,
  `import_batch_id=NULL`, `customer_factor_id` reference — CF Audit §16, §17.
- API: ~7 additive routes (`POST/GET/PUT/deactivate/approve` + extended `factor-match` and
  `calculate`) — CF Audit §18.
- Lifecycle: DRAFT → ACTIVE → ARCHIVED/INACTIVE (soft-deactivate to protect snapshots);
  version bump on update; factor-level review before customer use (CF Audit §8, §13).
- Customer-factor validation rules (value ≥ 0, unit, scope, source, conflict with reference
  factor) extend the ValidationEngine (CF Audit §12, V3 IA §12).

**RESOLVED SUB-DECISIONS (v1.1 — 2026-08-11 — each was an OPEN SUB-DECISION; all are now DECIDED)**

| Sub-decision | ID in CF Audit | Resolution |
|---|---|---|
| **Approval authority** — who approves a customer factor | D-cf-3 | **Organization Admin/Owner approves** customer-owned factors. Staff may **create/edit/validate factor drafts** but **cannot approve their own factor** (self-approval prohibited). |
| **Snapshot FK option** — how do `calculation_snapshots` reference customer factors | D-cf-2 / §16 | **Option O1 adopted**: `factor_id` nullable + `factor_kind` + optional `customer_factor_id` with an **exactly-one-source check**; provenance resolves to either `emission_factors` or `customer_factors`; immutable calculation provenance preserved (ADR-V3-014). |
| **Factor precedence** — customer factor vs CarbonTally factor on both-match | D-cf-5 / §15 | **Deterministic precedence:** (1) approved customer factor → (2) CarbonTally factor matching → (3) unresolved / manual review. **Never silently replace an approved customer factor.** |
| **Consultant access / RLS membership model** | R3 / D-cf-6 | Consultants may access customer factors **only for organizations they are authorized to access through the existing consultant-client relationship/RLS model**. **No global consultant access.** |

**Constraints**
- Must NOT put customer factors in `emission_factors` (REJECTED — CF Audit §10 Option A).
- Must NOT create a second matching/calculation engine, second snapshot system, second
  approval system, new factor enums, or a separate `customer_calculation_snapshots` table
  (CF Audit §29).
- Must NOT change the 7,049 factors, `emission_factors` schema/RLS/natural key, the 19 v2.1
  route contracts, or the error envelope (CF Audit §33 Q15).
- Must NOT weaken `emission_factors` global RLS.
- Must NOT silently replace an approved customer factor with a CarbonTally factor (D-cf-5
  precedence is deterministic — approved customer factor wins).
- Must NOT grant consultants global factor access (R3 — access is via the existing
  consultant-client relationship/RLS model only).

**Dependencies**
- ADR-V3-001 (entity dimension) — customer factors are org-scoped today; entity scope later.
- ADR-V3-008 (approval layers) — factor approval sits inside the approval architecture
  (approval authority now DECIDED — Organization Admin/Owner, D-cf-3).
- ADR-V3-010 (RLS) — consultant clause now DECIDED (R3 — existing consultant-client model).
- All four OPEN SUB-DECISIONS are RESOLVED (v1.1) — no open dependency remains for V3M-3.

**Implementation Impact**
- **DB:** NEW `customer_factors` table + RLS + snapshot-FK resolution (O1) — V3M-3 (DECIDED — READY FOR IMPLEMENTATION).
- **RLS:** NEW policies (org isolation via `is_org_member`; consultant access via the
  existing consultant-client relationship/RLS model — no global access clause).
- **Backend:** NEW `CustomerFactor` domain + `CustomerFactorsRepository`; EXTEND matching
  (candidate merge with approved-customer-first precedence), calculation (customer branch),
  and validation.
- **API:** ~7 NEW customer-factor routes + EXTEND `factor-match`/`calculate` +
  `CalculationSnapshotOut` provenance exposure (approval route enforces D-cf-3 authority).
- **Frontend:** customer-factor management UI (later phase).

---
### ADR-V3-003 — Work Item / Queue Architecture

**Status:** **PROVISIONALLY DECIDED**

**Decision**
Human operational work uses a canonical **Work Item** domain abstraction. The existing
**`manual_review_queue`** is the de-facto active human work-item store and is the extension
target. **Queues are logical** (filtered views over Work Items), not new physical queue
tables. Technical state machines (`document_processing_queue`, `report_generation_queue`)
remain separate. A full standalone Queue Management subsystem is **NOT required** at this
stage. No fifth queue table is created.

**Why**
The Queue Audit inventory shows 14+ queue-like structures; the four named queues have
distinct natures (§3.1–3.5). `manual_review_queue` is the only actively-used human work-item
store (produced/consumed by 9+ backend routes and the admin frontend, with status, priority+
SLA+escalation, assignment, audit, customer interaction, batch linkage) — Queue Audit §3.4.
Options A (status quo) and D (full subsystem) are explicitly rejected (§11). The V3 IA
reaches the same conclusion independently: "select ONE work-item queue surface … rather than
add new queue tables" (V3 IA §17); H4 records the consolidation decision as required.

**Current Architecture**
- `processing_queue` — dormant generic worker queue (RC1 claim index + RLS + SLA columns; no
  active producer/consumer) — Queue Audit §3.1.
- `document_processing_queue` — technical document AI-extraction state machine (stage-prefixed
  columns; constrained by RC1/RC2; no active producer) — Queue Audit §3.3.
- `manual_review_queue` — active human work-item store (pending/assigned/in_progress/
  completed/rejected + priority_score, SLA deadline, escalation_level, batch_id) —
  Queue Audit §3.4.
- `report_generation_queue` — report output persistence/status (v2.1 ReportsRepository) —
  Queue Audit §3.5.
- No Work Item vs Queue distinction exists today; every table embeds its own `status`.

**V3 Direction**
- **Work Item** = the canonical unit of human work (atomic, assignable, prioritised, SLA'd,
  audited). Initial implementation is a **domain abstraction over the existing
  `manual_review_queue` surface** — no new physical table is strictly required
  (Queue Audit §11 Option C).
- **Logical Queue** = a filtered view over Work Items ("pending and unassigned",
  "entity A queue", "CarbonTally queue") — Queue Audit §6.
- **Technical State Machine** = document processing (`document_processing_queue`) and report
  generation (`report_generation_queue`) stay outside the Work Item surface — Queue Audit §18.
- Entity scope (a "Entity A queue") follows ADR-V3-001 (now DECIDED — implementation pending V3M-1) — Queue Audit §10.

**Constraints**
- Must NOT create a fifth queue table or a separate `work_items` table without a decision
  (Queue Audit §11; V3 IA §17 "must not add a fifth queue without a decision").
- Must NOT build a full Queue Management subsystem (Queue Audit §11 Option D rejected).
- Must NOT duplicate `queue_settings`, SLA, workload, assignment-history, or audit structures
  (Queue Audit §16).
- Must NOT collapse Work Item / Logical Queue / Technical State Machine into one concept.

**Dependencies**
- ADR-V3-001 — entity scope for multi-entity allocation (Queue Audit §10, §11 C).
- ADR-V3-004 — document work type wiring (dpq producer) for the extraction work type.
- ADR-V3-005 — assignment/reassignment attribution.
- ADR-V3-016 — retirement of `processing_queue` family (after this ADR's model lands).

**Implementation Impact**
- **DB:** none initially; CONDITIONAL nullable `entity_id` if ADR-V3-001 resolves to entity scope.
- **Backend:** NEW WorkItem domain/service layer over existing tables/routes.
- **API:** EXTEND assignment/review routes to expose logical queues; NEW work-item endpoints.
- **RLS:** unchanged at org scope; entity policies per ADR-V3-001 (now DECIDED — implementation pending).
- **Frontend:** queue views become logical-queue consumers (later phase).

---

### ADR-V3-004 — Document Processing State Machine

**Status:** **PROVISIONALLY DECIDED**

**Decision**
`document_processing_queue` is a **technical document-processing state machine**, not the
canonical human work queue. Its stages span AI extraction → manual extraction → QC →
customer review. The final producer/consumer architecture for it is **not yet decided**
(no active backend route produces dpq rows today); that wiring is an OPEN/DEFERRED design
question gated behind the V3 document work type.

**Why**
The Queue Audit establishes: dpq is a wide stage-prefixed state table (`ai_*`, `manual_*`,
`qc_*`, `customer_*` column groups) with an 11-stage status vocabulary, constrained by RC1
and RC2, but with **no active producer** — only legacy monolithic copies wrote it
(Queue Audit §3.3). The V3 IA treats dpq as the v2.1 workflow queue to EXTEND
(V3 IA §6.1 "Processing" row). Design docs describe staff/customer workspaces against it,
but no active route consumes it. It must therefore be kept as the document-state machine
and wired to an active producer when the document work type lands — without being mistaken
for the human work-item store.

**Current Architecture**
- dpq: `ai_*` (extraction result, confidence, mapped ids), `manual_*` (request/assigned/
  result/notes), `qc_*` (required/by/at/notes/approved), `customer_*` (reviewed/approved/
  rejection), plus `calculated_emissions_kg_co2e`, `emission_factor_used`, `batch_id`,
  `processing_cost` (Queue Audit §3.3).
- Status vocabulary: `pending|processing|ai_extracted|manual_review|manual_extraction|
  qc|customer_review|approved|rejected|completed|failed`.
- RC2 freeze named dpq the "single processing-queue direction" (frozen ADR) — the wide
  stage-prefixed columns are the deliberate alternative to split stage tables.
- RLS: tenant policies via `is_org_member`; rc1 added `dpq_claim_idx` partial index.
- No active backend producer or consumer route found (Queue Audit §3.3).

**V3 Direction**
- **Keep** dpq as the technical document state machine (Queue Audit §17 verdict: KEEP).
- Wire an **active producer** when the V3 document-extraction work type is defined
  (ingestion → dpq → AI/manual/QC/customer stages).
- Relate dpq stages to Work Items: a document's state machine runs alongside its Work
  Items (extraction items, QC items) rather than replacing them (Queue Audit §18 hybrid).
- Dormant `manual_extraction_batches`/`manual_extraction_items` fold into the dpq path when
  it is wired (Queue Audit §4.2, §17).

**Constraints**
- Must NOT treat dpq as the canonical human work queue (Queue Audit §3.3 verdict).
- Must NOT create an active producer before the work-type design is decided — mark OPEN/DEFERRED.
- Must NOT delete dpq or its constrained CHECK (RC1/RC2 dependency).

**Dependencies**
- ADR-V3-003 — the Work Item model it interoperates with.
- ADR-V3-001 — entity scope if documents become entity-scoped.
- Open: producer/consumer architecture for V3 document work type.

**Implementation Impact**
- **DB:** none.
- **Backend:** NEW document work-type producer/consumer (after design).
- **API:** EXTEND ingestion routes (V3-001 `/process/*`) when producer lands.
- **RLS:** unchanged.

---
### ADR-V3-005 — Assignment & Reassignment

**Status:** **PROVISIONALLY DECIDED**

**Decision**
**`review_assignment_history`** is the active attribution mechanism for assignment and
reassignment of human work and is the reuse target. The dormant `reassignment_history`
(targeting the dormant `processing_assignments` id-space) and `processing_assignments` are
retained but not extended; their reconciliation with `review_assignment_history` is an
**unresolved architectural issue** that must be settled before any retirement.

**Why**
The Queue Audit traces `review_assignment_history` as actively written by
`assignments.py`/`reviews.py` (assign/unassign/reassign) and consumed by admin dashboard,
analytics and audit surfaces (Queue Audit §3.4, §12). `reassignment_history` targets the
dormant `processing_assignments` id-space — a parallel history that is not in the active
path (Queue Audit §16). The V3 IA requires assignment/reassignment "with attribution
preserved" (V3 IA §5.1 V3-005) and EXTENDs the legacy assignment surfaces (V3 IA §18,
§28). V3 must not create a third assignment-history mechanism.

**Current Architecture**
- `review_assignment_history` — active (queue/start/complete/reorder/escalate/SLA-monitor/
  reassign via `admin/assignments.py`, `admin/reviews.py`).
- `processing_assignments`/`processing_steps` — dormant (children `qc_checks`,
  `approval_requests` FK here) — Queue Audit §3.2.
- `reassignment_history` — dormant; targets dormant assignment id-space — Queue Audit §16.
- Duplicate SLA logic (per-table `sla_deadline` vs `sla_definitions`/`sla_compliance`) and
  duplicate audit (`review_assignment_history` vs `reassignment_history` vs
  `review_audit_trail` vs `processing_audit_trail`) exist (Queue Audit §16).

**V3 Direction**
- Reuse `review_assignment_history` as the single attribution record for human work.
- Supervisor intervention (reassign) keeps attribution via the same history with
  actor/role captured (V3 IA §6.1 audit EXTEND).
- Reconcile `reassignment_history` + `processing_assignments` against the work-item model
  (ADR-V3-003) before any retirement; `qc_checks`/`approval_requests` must be re-pointed
  first (Queue Audit §17 dependency chain).

**Constraints**
- Must NOT create a new assignment-history table.
- Must NOT retire `reassignment_history`/`processing_assignments` until the Work Item model
  lands and their children are re-pointed (Queue Audit §17).
- Must NOT lose attribution on reassignment.

**Dependencies**
- ADR-V3-003 — canonical work-item surface.
- ADR-V3-001 — entity-scoped workers (entity assignment).
- ADR-V3-016 — retirement ordering.

**Implementation Impact**
- **DB:** none (existing history reused).
- **Backend:** EXTEND assignment service for attribution/actor-role.
- **API:** EXTEND `/queue/assign`, `/queue/reassign`.
- **RLS:** none.

---

### ADR-V3-006 — SLA / Priority / Escalation / Capacity

**Status:** **PROVISIONALLY DECIDED**

**Decision**
The SLA / priority / escalation / capacity architecture **already exists** across
`queue_settings`, `sla_definitions`, `sla_compliance`, `business_hours`, `staff_workload`
and the escalation fields on work items. V3 **reuses** this infrastructure and **extends**
it (entity-level SLA/KPI, provider capacity) — it does **NOT** create duplicate SLA,
escalation, workload, or queue-configuration systems.

**Why**
The Queue Audit catalogues the full existing configuration and metrics surface
(Queue Audit §6, §13): `queue_settings` (max_reviews_per_staff, sla_hours, escalation_hours,
priority_weights, auto_assign flag), `sla_definitions` (document_type, priority_level,
sla_hours, escalation_hours), `sla_compliance` (deadline, is_breached, breach_time_minutes),
`business_hours`, `staff_workload` (workload_score, capacity_percentage, daily counters),
plus per-item `priority`/`priority_score`/`escalation_level`/`sla_deadline` on
`manual_review_queue`. The V3 IA requirement V3-011 (entity-level SLA/KPI, provider capacity)
is **Medium** with "DB CONDITIONAL; API EXTEND" (V3 IA §5.1). Duplicate SLA logic across
tables is flagged as existing overlap to consolidate, not to replicate (Queue Audit §16).

**Current Architecture**
- Priority: `manual_review_queue.priority` + `priority_score`; ordering `priority_score DESC,
  created_at` in `assignments.py`.
- SLA: `sla_definitions` (config) + `sla_compliance` (records) + `business_hours`
  (working days/hours) + per-item `sla_deadline`/`sla_breached` on the queue item.
- Escalation: `escalation_level`, `sla_breached`, `escalated_at`, customer-notification
  flags; `customer_verifications.is_escalated`.
- Capacity: `staff_workload` maintained by `reviews.py::update_staff_workload`.
- Configuration: `queue_settings` (key/value JSONB) read/written by `workload.py`.

**V3 Direction**
- Reuse all of the above unchanged for org-scoped operations.
- Entity-level SLA/KPI and provider capacity ONLY when ADR-V3-001 resolves the entity model
  (V3-011: "DB CONDITIONAL; API EXTEND").
- Consolidate duplicate SLA logic (per-table deadlines vs sla_definitions) at the work-item
  boundary (Queue Audit §16, §18).

**Constraints**
- Must NOT create duplicate SLA, escalation, workload, or queue-configuration systems
  (Queue Audit §13, §16; RULE 3).
- Must NOT change `queue_settings` semantics without a config-ownership decision.
- Must NOT implement entity-level SLA/capacity before ADR-V3-001.

**Dependencies**
- ADR-V3-001 — entity-scoped SLA/KPI/capacity.
- ADR-V3-003 — work-item boundary for SLA consolidation.

**Implementation Impact**
- **DB:** none at org scope; CONDITIONAL entity-scope columns after ADR-V3-001.
- **Backend:** EXTEND SLA/capacity computation for entity scope (later).
- **API:** EXTEND dashboard/analytics for entity-level KPI (later).
- **RLS:** none.

---
### ADR-V3-007 — Auto Assignment

**Status:** **PROVISIONALLY DECIDED**

**Decision**
An **AutoAssignmentEngine** is a **backend orchestration capability, not a new queue system.**
All its building blocks already exist (configuration, capacity, priority); the engine
orchestrates them. **Skills do not currently exist** and are an unresolved requirement.
The engine is NOT implemented in this register.

**Why**
The Queue Audit establishes: `queue_settings.auto_assign_enabled`/`max_reviews_per_staff`/
`sla_hours`/`escalation_hours`/`priority_weights` exist and are managed by `workload.py`;
`staff_workload` provides capacity counters; `priority_score` + `created_at` order the
queue; **no skill dimension exists anywhere**; and no auto-assignment engine exists
(Queue Audit §12). V3-009 in the V3 IA is marked "engine NEW; no DB change" (V3 IA §5.1).
The engine should support manual / round-robin / least-loaded / capacity / skill /
priority / SLA strategies per V3-009.

**Current Architecture**
- Config: `queue_settings` (auto_assign_enabled, max_reviews_per_staff, sla_hours,
  escalation_hours, priority_weights) — read/written by `admin/workload.py`.
- Capacity: `staff_workload` (workload_score, capacity_percentage, daily counters) —
  maintained by `reviews.py::update_staff_workload`.
- Priority: `manual_review_queue.priority` + `priority_score`.
- Skills: **none** anywhere.
- Engine: **does not exist.**

**V3 Direction**
- Implement the engine as a NEW backend service orchestrating existing
  config + capacity + priority — no new tables (V3 IA §5.1 V3-009; Queue Audit §12).
- Add a skills dimension **only if** a documented requirement justifies it (currently not
  documented — unresolved).

**Constraints**
- Must NOT build the engine as a new queue/schema system (Queue Audit §12).
- Must NOT invent a skills model without evidence.
- Must NOT implement the engine in this register.

**Dependencies**
- ADR-V3-001 — entity-scoped assignment (engine targets entity workers) — now DECIDED (implementation pending V3M-1).
- ADR-V3-003 — work-item surface the engine assigns over.
- ADR-V3-006 — SLA/capacity inputs.

**Implementation Impact**
- **DB:** none.
- **Backend:** NEW AutoAssignmentEngine (orchestration service).
- **API:** NEW auto-assign control endpoints.
- **RLS:** none.

---

### ADR-V3-008 — Customer Review / Approval

**Status:** **PROVISIONALLY DECIDED**

**Decision**
The **`customer_verifications`** surface (plus `customer_review_log`) is the customer-approval
layer and is kept and extended. The dormant approval infrastructure
(`approval_requests`/`approval_decisions`, wired to the dormant `processing_assignments`) is
**REPOINT** (deferred): its approval vocabulary is reused, but re-pointed at the canonical
Work Item when approval layers are built. No duplicate approval system is created.

**Why**
`customer_verifications` is active and RC2-hardened (organization_id NOT NULL, REPLICA
IDENTITY FULL for realtime) and already carries the escalation concept
(`is_escalated`, `escalation_reason`) (Queue Audit §4.4). The five-layer approval
separation (worker submission ≠ entity approval ≠ CarbonTally validation ≠ customer
approval) is a core V3 requirement (V3 IA §18; §5.1 V3-006) and `customer_verifications`
already serves the customer layer. `approval_requests`/`approval_decisions` carry the
generic approval vocabulary (`approval_type`, `status`, `priority`, `notes`,
`sla_deadline`, `decision_by`, `decision`, `reason`) but their FK points at the dormant
`processing_assignments` (Queue Audit §4.3) — hence REPOINT, not delete or duplicate.

**Current Architecture**
- `customer_verifications`: customer_document_id, organization_id, customer_member_id,
  status, submitted/verified/rejected/revision-requested timestamps+actors, is_escalated,
  escalation_reason, metadata (Queue Audit §4.4).
- `customer_review_log`: customer review audit trail.
- `approval_requests`/`approval_decisions`: generic approval vocabulary; FK →
  `processing_assignments` (dormant) (Queue Audit §4.3).
- `manual_review_queue.escalation_level` + `customer_verifications.is_escalated` cover
  escalation (Queue Audit §4.4).

**V3 Direction**
- Keep `customer_verifications` as the customer-approval surface; extend for V3-021
  (customer approve/reject on processed results) (V3 IA §18).
- Repoint `approval_requests`/`approval_decisions` at the canonical Work Item (ADR-V3-003)
  when approval layers are built (Queue Audit §4.3, §17).
- Factor approval (customer-factor review, ADR-V3-002 sub-decision D-cf-3 — now DECIDED:
  Organization Admin/Owner approval, no self-approval) reuses this approval pattern
  (CF Audit §29 point 5: reuse `approval_requests` pattern with
  `approval_type='FACTOR'`).

**Constraints**
- Must NOT create a duplicate approval system (CF Audit §29 point 5; Queue Audit §16).
- Must NOT delete `approval_requests`/`approval_decisions` (dormant, FK-bound children).
- Must NOT wire approval layers before ADR-V3-003's work-item surface exists.

**Dependencies**
- ADR-V3-003 — work-item re-pointing target.
- ADR-V3-001 — entity approval layer (now DECIDED — implementation pending).
- ADR-V3-002 — factor approval authority (sub-decision D-cf-3 — now DECIDED: Organization Admin/Owner).

**Implementation Impact**
- **DB:** none.
- **Backend:** EXTEND verification workflow; NEW approval-layer wiring (after ADR-V3-003).
- **API:** EXTEND customer review/approval endpoints (V3-021).
- **RLS:** none at org scope.

---
### ADR-V3-009 — Issue Management

**Status:** **DECIDED**

**Decision**
**Option B — First-Class Issue Management Model.** CarbonTally V3 treats an **Issue** as a
first-class operational domain object. An Issue is **not** the same thing as a conversation.
The Issue represents the operational problem, exception, defect, escalation or resolution
workflow. Communication/conversations may be associated with an Issue where communication is
required. V3 Issue Management is architecturally decided; implementation remains pending.

*Architectural decision made by product/architecture owner: Option B — First-Class Issue Management Model.*

**Why**
V3-007 "Issue Management" was originally recorded as Medium / "DB CONDITIONAL; API NEW" with
H7 (dedicated `issues` table vs conversations-based) unresolved (V3 IA §5.1, §27 H7;
V3M-5 preliminary inventory). The Queue Audit confirmed no unified issue entity exists today —
`user_feedback`, validation errors, QC errors, extraction errors, rejection/correction
mechanisms, audit/history and escalation all exist as separate mechanisms with different
shapes (Queue Audit §6). The product/architecture owner has now resolved H7: V3 adopts a
first-class Issue Management model (Option B). The earlier evidence that conversations and
escalation already exist (V3 IA §29 point 1) remains valid for communication/association but
does not substitute for a first-class Issue.

**Current Architecture**
- `user_feedback` — user feedback store (retained; not replaced by this decision).
- Validation errors — ValidationEngine A1–A9 rule failures (per-record, not an issue entity).
- QC errors — `qc_checks`/`qc_errors` (per-QC-pass records).
- Extraction errors — manual_review_queue errors/extraction notes.
- Rejection/correction — statuses on work items, `draft_entries`, `report_versions`.
- Audit/history — `domain_events`, `audit_trail`, `review_assignment_history`.
- Escalation — `escalation_level`, `sla_breached`, `customer_verifications.is_escalated`.
- Conversations — existing `conversations`/`messages`/`notifications` surface (unchanged).
- No unified issue entity anywhere (Queue Audit §6).

**V3 Direction**
An Issue is a first-class operational domain object with, where applicable: issue_type,
severity, priority, status, owner, assignee, organization/customer context, processing-entity
context, work-item context, document/batch context, SLA, escalation, resolution, reopening,
audit/history, timestamps, and relationship to work items / documents / batches / processing
entities / customers-or-organizations. Authorized communication is provided by associating
existing Conversation(s) with an Issue where required — Issue and Conversation remain separate
concepts. The Issue represents the operational problem requiring tracking, ownership,
escalation, action and resolution; a Conversation is communication between authorized parties.
This register does **not** invent final database columns or enums.

**Constraints**
- Do NOT implement the issues model in this register — implementation (DB, migration, RLS,
  API, backend, frontend, tests) is a separate later task.
- Do NOT redesign or modify the existing conversation system.
- Do NOT delete or modify existing issue/feedback structures (`user_feedback`, `qc_errors`,
  work-item rejection/correction surfaces).
- No final database columns or enums are defined here.

**Dependencies**
- ADR-V3-003 (work-item boundary) — issues attach to Work Items where applicable.
- ADR-V3-001 — processing-entity context per the DECIDED entity model (implementation pending V3M-1).
- ADR-V3-006 — issue SLA/escalation reuses the existing SLA infrastructure.

**Implementation Impact** (pending — not implemented)
- **DB:** CONDITIONAL — `issues` table per the first-class model (designed before any migration).
- **Backend:** NEW issue service (creation, classification, assignment, status, SLA,
  escalation, resolution, reopening, audit).
- **API:** NEW issue endpoints.
- **RLS:** issue org/entity scope policies (per ADR-V3-010 patterns).
- **Frontend:** issue workspaces (later phase).

---

### ADR-V3-010 — RLS / Security / Tenant Isolation

**Status:** **PROVISIONALLY DECIDED** (with **INVESTIGATE** flags)

**Decision**
V3 **extends** the existing org-isolation RLS model; it does **not** weaken any existing
policy. Customer visibility, worker visibility, consultant access and service-role
operations follow the established `is_org_member()` patterns. Entity-level RLS is
per ADR-V3-001 (now DECIDED — implementation pending). The **legacy permissive policies** found on active queue
structures are an **INVESTIGATE/HARDEN** item, not a mandate to change RLS in this register.

**Why**
The Queue Audit flags legacy permissive policies coexisting with the RC2 tenant policies on
active tables: `"Staff can insert queue items" WITH CHECK (true)`, `"Allow authenticated users
to update queue items"`, `"Allow authenticated users to view pending queue items"` on
`manual_review_queue`; broad `authenticated_read` on staff tables; RLS-less child tables at
RC1 (Queue Audit §15–§16). The V3 IA requires security/isolation at 10 levels incl. entity
boundaries and break-glass access (V3 IA §5.1 V3-015, "RLS EXTEND; DB CONDITIONAL"). The CF
Audit establishes the customer-factor RLS pattern (reuse `is_org_member`, mirror
`factor_aliases`) with a consultant-clause investigation (CF Audit §19, §31).

**Current Architecture**
- Org isolation: `is_org_member()` RLS helper; tenant policies on
  `manual_review_queue`, `upload_batches`, `customer_verifications`,
  `calculation_snapshots`, `emissions_logs`, `factor_aliases` (aliases_select_own).
- Global read: `emission_factors` SELECT USING(true) — service-role writes only.
- Legacy permissive policies exist in the dump on active queue structures
  (Queue Audit §15–§16) — **INVESTIGATE**.
- Staff tables use broad `authenticated_read` (Queue Audit §16).
- No entity boundary exists (ADR-V3-001).

**V3 Direction**
- Reuse `is_org_member()` for all new org-scoped policies (customer_factors, work-item views).
- Consultant access: mirror the RC2 org-isolation decision for emissions; the
  `is_consultant_of` clause follows the **existing consultant-client relationship/RLS model**
  — no global consultant access (ADR-V3-002 SUB-DECISION R3 now RESOLVED — v1.1).
- Entity RLS: deny-by-default + member-of-entity policies **only after** ADR-V3-001.
- Harden legacy permissive policies as part of the V3 security pass (INVESTIGATE first —
  confirm no active dependency before tightening).
- Break-glass access: extend auth/RBAC per V3-015 (V3 IA §5.1).

**Constraints**
- Must NOT weaken existing RLS (Principle 6: "Preserve existing RLS boundaries").
- Must NOT change RLS policies in this register (documentation-only).
- Must NOT assume consultant membership model without investigation.
- Must NOT add entity policies before ADR-V3-001.

**Dependencies**
- ADR-V3-001 — entity boundary.
- ADR-V3-002 — customer-factors RLS + consultant clause.
- INVESTIGATE: legacy permissive policies inventory; consultant membership model.

**Implementation Impact**
- **RLS:** EXTEND — new org-scoped policies (customer_factors); CONDITIONAL entity policies;
  hardening of legacy permissive policies after investigation.
- **DB:** none except conditional entity changes.
- **Backend:** EXTEND authorization (`require_role`/`require_admin` + entity-scoped roles).
- **API:** none.
- **Frontend:** none.

---
### ADR-V3-011 — Work Item Identity & Work Types

**Status:** **PROVISIONALLY DECIDED**

**Decision**
A **Work Item** is the atomic unit of human work with an existing row identity (the
`manual_review_queue` PK) — no new identity scheme is introduced. **work_type** distinguishes
the work a Work Item represents (manual review, document extraction, QC) using existing
status/type fields; the three-way distinction Work Item / Logical Queue / Technical State
Machine is preserved.

**Why**
The Queue Audit derives the Work Item concept from the active `manual_review_queue` surface
(status, priority, SLA, assignment, customer interaction, batch) and maps V3 work types onto
existing tables (review = manual_review_queue; extraction = dpq items; QC = qc_checks; report
= report_generation_queue) (Queue Audit §3.4, §7, §8). No parent/child work-item requirement
is documented; a document's state machine (dpq) runs alongside its Work Items rather than
nested inside them (Queue Audit §18). The V3 IA requires work-item allocation services
without specifying a new identity model (V3 IA §6.1, §28).

**Current Architecture**
- Identity: UUID PKs on existing tables; no global work-item id space.
- Work types today are implied by table membership (review vs dpq vs report).
- No parent/child work-item hierarchy exists or is documented.

**V3 Direction**
- Work Item domain abstraction over existing rows (ADR-V3-003); identity = existing PK.
- work_type representation via a typed field/abstraction in the WorkItem domain layer
  (review | extraction | qc | report-output), mapping to the owning table.
- Parent/child: **not required** — dpq state machine coordinates document stages; Work Items
  reference the document/batch (Queue Audit §18).
- Retry/reprocessing: existing reprocessing via workflow + snapshots (V3 IA §5.1 V3-013);
  no new retry state machine without evidence.

**Constraints**
- Must NOT invent a new global work-item id space.
- Must NOT create parent/child work-item tables without a documented requirement.
- Must NOT conflate Work Item identity with document identity (dpq).

**Dependencies**
- ADR-V3-003 — work-item surface.
- ADR-V3-004 — document work type.

**Implementation Impact**
- **DB:** none.
- **Backend:** NEW WorkItem domain type (typed work_type).
- **API:** EXTEND work-item endpoints.
- **RLS:** none.

---

### ADR-V3-012 — Batch vs Atomic Work Item

**Status:** **DECIDED**

**Decision**
**Batch = grouping; Work Item = atomic.** The batch anchor is `upload_batches`; the atomic
work unit is the Work Item (a `manual_review_queue` row). "Batch" never means a single
monolithic processing unit, and `import_batches` (factor imports) is a different concept that
is never conflated with processing batches.

**Why**
`upload_batches` is the active batch grouping anchor (`batch_id` FK → `manual_review_queue`,
ON DELETE CASCADE; org-hardened by RC2-028; consumed by assignments/reviews/extraction and
admin batch progress) (Queue Audit §4.1). The V3 IA explicitly warns: "do not conflate factor
import batches with processing batches" (V3 IA §17). The multi-entity (500-doc) test case
maps directly onto per-item Work Items grouped by batch (Queue Audit §10).

**Current Architecture**
- `upload_batches`: id, organization_id, batch_name, total_files, processed_files, status,
  created_by_user_id, metadata, batch_type, estimated_processing_time, error_count,
  manual_extraction_requested, manual_extraction_batch_id (Queue Audit §4.1).
- `import_batches`: factor-import provenance (M1) — distinct domain (V3 IA §17).

**V3 Direction**
- Keep `upload_batches` as the grouping anchor; Work Items reference `batch_id`.
- Batch-level operations (progress, SLA by batch) aggregate Work Items; they never bypass
  the per-item surface.

**Constraints**
- Must NOT create a new batch table.
- Must NOT conflate `import_batches` with processing batches.

**Dependencies**
- ADR-V3-003 — work-item surface.

**Implementation Impact**
- **DB:** none.
- **Backend:** EXTEND batch/work-item aggregation.
- **API:** EXTEND batch endpoints.
- **RLS:** none.

---
### ADR-V3-013 — Audit / History Strategy

**Status:** **PROVISIONALLY DECIDED**

**Decision**
Audit/history reuses the existing layered stack: **`review_assignment_history`**
(assignment attribution), **`domain_events`** + **`audit_trail`** (event/audit records),
**`calculation_snapshots`** (immutable calc provenance), and per-table audit trails
(`review_audit_trail`, `processing_audit_trail`, `customer_review_log`). V3 consolidates
duplicate history surfaces at the work-item boundary instead of adding another audit system.

**Why**
The Queue Audit inventories the active vs dormant audit structures: `review_assignment_history`
is active; `reassignment_history` is dormant; `review_audit_trail` vs `processing_audit_trail`
duplicate the concept (Queue Audit §16). The V3 IA REUSEs AuditRepository/AuditLogger and
extends the scope field with entity scope + actor-role (V3 IA §6.1 "Audit EXTEND"), and
requires attribution preserved on assignment/reassignment (V3 IA §5.1 V3-005). Lineage for
factors is already strong via snapshots/events/audit (V3 IA §5.1 V3-012: "REUSE + EXTEND; no
DB change").

**Current Architecture**
- `review_assignment_history` (active), `reassignment_history` (dormant),
  `review_audit_trail`, `processing_audit_trail`, `domain_events`, `audit_trail`,
  `customer_review_log`, `calculation_snapshots` (append-only, content_hash + verify).
- AuditLogger/EventBus reused (V3 IA §6.1).

**V3 Direction**
- Single attribution record: `review_assignment_history` (ADR-V3-005).
- Add entity scope + actor-role to audit entries (V3 IA §6.1).
- Consolidate duplicate history surfaces (`reassignment_history`,
  `processing_audit_trail`) at the work-item boundary when the Work Item model lands
  (Queue Audit §16, §17).

**Constraints**
- Must NOT create a new audit/history system.
- Must NOT delete dormant history tables until re-pointed (Queue Audit §17).

**Dependencies**
- ADR-V3-003, ADR-V3-005.

**Implementation Impact**
- **DB:** none.
- **Backend:** EXTEND AuditRepository/AuditLogger scope.
- **API:** none.
- **RLS:** none.

---

### ADR-V3-014 — Snapshot / Provenance for Customer Factors

**Status:** **DECIDED** ✅

**Decision**
`calculation_snapshots` remains the **single immutable forensic record** for all
calculations, customer-factor or not. Provenance for customer factors is recorded as
`factor_source='CUSTOMER'`, `import_batch_id=NULL`, `factor_set='CUSTOMER'`, plus a
`customer_factor_id` reference. The snapshot FK relaxation is the ADR-V3-002 sub-decision
(snapshot FK option, D-cf-2) — now **RESOLVED: Option O1 adopted** (v1.1). A separate
`customer_calculation_snapshots` table is **REJECTED**.

**Why**
Snapshots already freeze factor_id + co2e_multiplier + factor_source/factor_set/
import_batch_id + methodology + algorithm_version + content_hash and are verified for
reproducibility (CF Audit §7, §17). Lineage needs no new structures — only the FK resolution
and optional API exposure of provenance (CF Audit §17, §33 Q9). CF Audit §29 point 9
explicitly rejects a separate customer snapshot table.

**Current Architecture**
- `calculation_snapshots`: factor_id NOT NULL FK → emission_factors; immutable; content_hash
  + verify; org-scoped RLS (calc_snapshots_select_own).
- `CalculationSnapshotOut` API output omits provenance fields (factor_source/factor_set/
  import_batch_id are in the row but not the response) (CF Audit §7).

**V3 Direction**
- **Relax `factor_id` per Option O1** (DECIDED — D-cf-2 resolved): nullable `factor_id` +
  `factor_kind` + optional `customer_factor_id` with an exactly-one-source check — CF Audit
  §16. `calculation_snapshots` supports provenance to either `emission_factors` (CarbonTally)
  or `customer_factors` (customer-owned).
- Provenance always answerable: "which exact factor was used".
- Optionally expose provenance in `CalculationSnapshotOut` (CF Audit §18, §33 Q9).

**Constraints**
- Must NOT create `customer_calculation_snapshots` (REJECTED — CF Audit §29 point 9).
- Must NOT change historical snapshots (immutable).
- Must NOT relax the FK in a way that leaves a snapshot with neither source set — the
  exactly-one-source check preserves immutable provenance integrity.

**Dependencies**
- ADR-V3-002 (snapshot FK sub-decision — RESOLVED, O1, v1.1).
- ADR-V3-010 (RLS unchanged on snapshots).

**Implementation Impact**
- **DB:** snapshot-FK migration (O1) within V3M-3 — DECIDED — READY FOR IMPLEMENTATION.
- **Backend:** EXTEND calculation sink for customer factor provenance.
- **API:** EXTEND `CalculationSnapshotOut`.
- **RLS:** none.

---
### ADR-V3-015 — Factor Provider Architecture

**Status:** **DECIDED** ✅

**Decision**
DEFRA (GB, 7,029) and SEAI (IE, 20) are the committed factor providers and are reused
unchanged. **EPA (IE) fits today without any schema change** (new import batch + factors).
ADEME (FR), IPCC (global) and EU residual-mix factors are **DEFERRED** — they would violate
the active `CHECK (country IN ('GB','IE'))` and collide on the RC2 natural-key index
`(reporting_year, activity_type, country, unit, scope)`, so they enter only via a deliberate
decision to widen both (V3 IA §9, §20, §27 H3). HDPE processing entities are a **separate**
provider axis and are never emission-factor providers.

**V3M-4 resolution (v1.1 — 2026-08-11):** CarbonTally uses a **provider-independent
emission-factor architecture**. The existing provider architecture remains authoritative;
DEFRA and SEAI are existing provider implementations; future providers use the **same
provider/import architecture** (no separate factor database, no provider-specific calculation
engine). Individual provider imports remain **separate implementation tasks**.

**Why**
The V3 IA factor architecture analysis (V3 IA §9) proves the current schema accommodates
additional GB/IE-valid providers with no migration; EPA Ireland works today. Provider
identity is already derivable via `import_batches.provider_key` + `factor_source`/`factor_set`
(V3 IA §9). Widening country CHECK and natural key is trigger T3 / migration V3M-4 (V3 IA §8)
and is a human decision (H3). The HDPE-vs-factor-provider distinction is a recorded,
non-conflicting separation (V3 IA §5.3, §20 note).

**Current Architecture**
- `emission_factors` (7,049 rows; DEFRA 7,029 + SEAI 20; batch-linked; `import_batches`),
  `factor_aliases`, `calculation_snapshots`.
- `CHECK (country IN ('GB','IE'))` active (K1); natural-key UNIQUE index without
  provider_key/factor_set (RC2).
- Provider roadmap: DEFRA/SEAI COMPLETE; EPA deferred; ADEME/IPCC/EU deferred/not listed
  (V3 IA §20).

**V3 Direction**
- Reuse DEFRA/SEAI; add EPA (IE) via importer + batch when scoped (no schema change).
- Customer libraries (ADR-V3-002) are org-owned values, distinct from provider libraries.
- Deferred providers require: country-CHECK widening + natural-key widening with
  `provider_key` + matching precedence policy (V3 IA §10 "Provider precedence EXTEND") —
  applied as **V3M-4 (DECIDED — READY FOR IMPLEMENTATION)** when an individual provider
  import is scoped.
- **No separate factor database and no provider-specific calculation engine** are created
  (V3M-4 decision) — future providers reuse the existing provider/import architecture.

**Constraints**
- Must NOT import FR/global/EU providers before the relevant T3 constraint work
  (V3 IA §24, §29); individual provider imports are separate implementation tasks.
- Must NOT change the 7,049 factors or their natural key for the committed providers.
- Must NOT treat HDPE entities as emission-factor providers (V3 IA §5.3, §20).

**Dependencies**
- V3 IA §27 H3 (provider scope decision) — DEFERRED until a specific provider is scoped;
  the provider-independent architecture itself is now DECIDED (V3M-4, v1.1).
- ADR-V3-002 — customer libraries are a distinct surface.

**Implementation Impact**
- **DB:** none for committed providers; CONDITIONAL (T3) for a scoped deferred provider
  (V3M-4 — DECIDED — READY FOR IMPLEMENTATION).
- **Backend:** new provider importer pipeline per scoped provider (e.g. EPA) — separate task.
- **API:** none.
- **RLS:** none.

---

### ADR-V3-016 — Queue Consolidation & Retirement

**Status:** **DEFERRED** (dependency-gated)

**Decision**
Retirement of dormant queue structures is deliberately deferred until a dependency chain
completes. `processing_queue` (and, later, `processing_assignments`/`processing_steps`,
`reassignment_history`, `manual_extraction_batches`/`manual_extraction_items`,
`approval_requests`/`approval_decisions`) is **not deleted** — it is left inert/archived or
consolidated once the Work Item model, the active document work type (dpq producer), and
re-pointing of FK-bound children are done. The intent-only `internal_tasks`/`task_assignments`
(not in schema) must never be created — the Work Item model supersedes them.

**Why**
The Queue Audit establishes the exact retirement dependency chain: Work Item model approved →
active document work type (dpq producer) → approval/QC re-pointed → then the
`processing_queue` family can be retired — "never deleted; left as inert schema or archived"
(Queue Audit §17, §18). Children `qc_checks`/`approval_requests` FK to
`processing_assignments`, so premature deletion breaks the schema. The V3 IA likewise defers
queue consolidation to the work-item decision (V3 IA §17, §27 H4).

**Current Architecture**
- `processing_queue` family dormant; `document_processing_queue` KEEP (technical);
  `manual_review_queue` KEEP (canonical human); `report_generation_queue` KEEP (technical
  output) — Queue Audit §17 verdict table.
- `internal_tasks`/`task_assignments` are intent only (not in init schema) — Queue Audit §17.

**V3 Direction**
- Retire/consolidate per the dependency chain only; never delete — archive or leave inert.
- Keep `document_processing_queue`, `report_generation_queue`, `manual_review_queue` and
  `upload_batches` as the live estate (Queue Audit §17).

**Constraints**
- Must NOT delete any dormant table until its children are re-pointed (Queue Audit §17).
- Must NOT create `internal_tasks`/`task_assignments` (superseded by Work Item model).
- Must NOT add a fifth queue (ADR-V3-003).

**Dependencies**
- ADR-V3-003 (work-item model) → ADR-V3-004 (document work type) → ADR-V3-005
  (reassignment reconciliation) → this ADR.

**Implementation Impact**
- **DB:** none until the chain completes (inert schema or archival migration, later).
- **Backend:** none now.
- **API:** none.
- **RLS:** none.

---
## 6. Open Decisions Blocking Implementation

### 6.1 Blocking ALL V3 implementation

| ID | Open Decision | Why It Matters | Depends On | Must Resolve Before |
|----|---------------|----------------|------------|---------------------|
| *(none)* | ADR-V3-001 (Processing Entity) is now **DECIDED — Option B** (dedicated `processing_entities` table; NULL-internal convention). No decision currently blocks ALL V3 implementation. Remaining blockers are subsystem-specific (§6.2) and the Implementation Gate conditions (§10). | — | — | — |

### 6.2 Blocking specific V3 subsystems

| ID | Open Decision | Why It Matters | Depends On | Must Resolve Before |
|----|---------------|----------------|------------|---------------------|
| ADR-V3-004 | dpq **producer/consumer architecture** (V3 document work type) | Blocks the document-extraction work type wiring. | ADR-V3-003 | V3 document work type implementation |
| ADR-V3-010 — INV 1 | **Legacy permissive RLS policies** on active queue structures (inventory + any active dependency before hardening) | Security risk; hardening is a V3 security pass item. | Queue Audit §15–§16 | V3 security/hardening pass |
| ADR-V3-010 — INV 2 | **Consultant membership model** for emissions access (customer-factor consultant access is now RESOLVED — R3: existing consultant-client relationship/RLS model; no global access) | Determines RLS predicate shape for emissions. | CF Audit §19, §31; RC2 org-isolation decision | emissions consultant access |
| ADR-V3-007 | **Skills dimension** (documented requirement vs none) | Determines whether AutoAssignmentEngine adds a skills model. | None documented today | AutoAssignmentEngine design |

> **Resolved (v1.1 — 2026-08-11):** the four ADR-V3-002 OPEN SUB-DECISIONS (approval
> authority D-cf-3, snapshot FK D-cf-2 → O1, factor precedence D-cf-5, consultant access R3)
> are DECIDED and **no longer block V3M-3**. V3M-4 is also DECIDED (provider-independent
> factor architecture); individual provider imports remain separate implementation tasks.

---

## 7. Deferred Decisions

Deliberately postponed to a later V3 phase; not blocking current implementation.

| Decision | Current status | Source | Defer reason |
|---|---|---|---|
| Non-GB/IE factor providers (ADEME FR, IPCC global, EU residual-mix) | DEFERRED (imports) — architecture **DECIDED** | V3 IA §20, §24, §27 H3; ADR-V3-015 (V3M-4 resolved v1.1) | Provider-independent architecture is DECIDED; individual provider imports remain separate implementation tasks (each needs its own scoping + T3 constraint work) |
| External benchmarking (peer/sector) | DEFERRED | V3 IA §5.3, §13, §27 H9 | Not documented as V3; Phase 9 decision (internal-only) authoritative |
| Webhooks & external integrations (ERP/accounting/sustainability platforms) | DEFERRED | V3 IA §19, §27; V3-I1 | No integration contract exists |
| PDF/HTML report output | DEFERRED | V3 IA §27 H10 | PDF not documented; structured outputs only |
| Data retention/deletion policy (periods, export-before-delete, Storage deletion) | DEFERRED | V3 IA §27 H11; V3-014 | Business/legal policy — must not be invented |
| Subscription/usage billing evolution | DEFERRED | V3 IA V3-I3 | Legacy tables exist; not committed |
| Queue consolidation & retirement of dormant structures | DEFERRED | ADR-V3-016 | Dependency chain (Work Item model → document type → re-pointing) |
| Asynchronous job runner (worker vs in-process) | DEFERRED/OPEN | V3 IA §27 H14 | No v2.1 worker exists; needed only when ingestion lands |
| Entity contract metadata (minimal vs contractual fields) | DEFERRED | V3 IA §27 H13 | "Can be implemented later" (VS2 §10) |

---
## 8. Rejected Architectural Approaches

Approaches explicitly rejected by the source evidence. Do not resurrect without a new decision.

| Rejected approach | Evidence | Why rejected |
|---|---|---|
| **Multiple independent human queues** (each work surface gets its own queue) | Queue Audit §11 Option A (status quo = duplication); §16 (assignment+status+SLA+audit duplicated across `processing_queue`/`processing_assignments` vs `manual_review_queue`/`review_assignment_history`) | Duplicates state, SLA, assignment and audit; no shared Work Item model; the current 14+ queue-like structures already demonstrate the failure mode. |
| **Full dedicated Queue Management subsystem** (Work Items / Queues / Queue Rules / Routing / Capacity / SLA / Escalation / History tables) | Queue Audit §11 Option D; §13, §16 | Every subsystem part already exists as a table (`manual_review_queue` = work items, `queue_settings` = rules, `review_assignment_history` = history, `sla_*` = SLA, `staff_workload` = capacity, `escalation_level` = escalation). A full subsystem would duplicate all of it. Overkill for the V3 "five-layer approval" and "multi-entity allocation" requirements. |
| **Extending `emission_factors` for customer-owned factors** (org-owned rows in the global reference) | CF Audit §10 Option A (REJECTED); §29 point 1 | Breaks the global authenticated-read RLS model, the natural key (no org dimension), and CarbonTally import provenance; requires conditional policies on a table all customers read — high leak risk. |
| **Second matching / calculation / snapshot / approval systems** | CF Audit §29 points 2–5, 9; §28 | Duplicate engines create divergence; `quantity × multiplier` + snapshot + verify is reused unchanged; snapshots are the single forensic record; the `approval_requests` pattern is reused. |
| **`internal_tasks` / `task_assignments` tables** (intent-only, not in schema) | Queue Audit §17 | Never in the init schema; the Work Item model (ADR-V3-003) supersedes the intent. |
| **Reviving `region_deprecated`** for EU/regional geography | V3 IA §9 ("Do not revive") | Retired at RC1/RC2; a future EU/regional concept needs a deliberate new decision, not a revival. |
| **ADEME/IPCC/EU provider import without T3 constraint work** | V3 IA §24, §29 | Active country CHECK rejects FR/global/EU rows; insert failures. |

---
## 9. V3 Architecture Decision Baseline

### 9.1 Human operations surface (DECIDED / PROVISIONALLY DECIDED)

```
Organization  ──────────────── DECIDED (existing `organizations` tenant)
    ↓
Processing Entity  ─────────── DECIDED (ADR-V3-001 — Option B, dedicated
    │                           `processing_entities`); implementation pending (V3M-1)
    ↓
Batch  ─────────────────────── DECIDED (`upload_batches` — grouping anchor; ADR-V3-012)
    ↓
Work Item  ─────────────────── PROVISIONALLY DECIDED (canonical domain over
    │                           `manual_review_queue`; ADR-V3-003, ADR-V3-011)
    ↓
Logical Queue  ─────────────── PROVISIONALLY DECIDED (filtered views over Work Items;
    │                           "CarbonTally queue", "Entity A queue" — ADR-V3-003)
    ↓
Assignment  ────────────────── PROVISIONALLY DECIDED (`review_assignment_history`
    │                           attribution; ADR-V3-005)
    ↓
Worker / Supervisor  ───────── PROVISIONALLY DECIDED (staff_workload capacity; existing
    │                           RBAC; entity workers per ADR-V3-001 — DECIDED)
    ↓
SLA / KPI / Audit  ──────────── PROVISIONALLY DECIDED (queue_settings, sla_*,
    │                           staff_performance, review_assignment_history,
    │                           domain_events/audit_trail; ADR-V3-006, ADR-V3-013)
    ↓
Completion  ────────────────── via existing statuses (pending → … → completed/rejected)
```

### 9.2 Technical state machines (separate from the human surface)

```
document_processing_queue  ─── KEEP as technical document state machine
                               (AI → manual → QC → customer); producer OPEN
                               (ADR-V3-004); NOT the canonical human queue.
report_generation_queue   ─── KEEP as specialized report-output mechanism,
                               outside Work Management (Queue Audit §3.5).
```

### 9.3 Customer-owned factors (DECIDED — sub-decisions resolved v1.1)

```
customer_factors (NEW, org-scoped, RLS is_org_member)   ── ADR-V3-002
    ↓
Factor Matching (EXTEND: customer candidates + CarbonTally candidates; precedence DECIDED:
    approved customer factor → CarbonTally matching → unresolved/manual review)
    ↓
Factor Review (approval authority DECIDED — Organization Admin/Owner; staff cannot approve own)
    ↓
Calculation (EXTEND: factor_source='CUSTOMER'; snapshot FK DECIDED — O1)
    ↓
Snapshot / Provenance (calculation_snapshots reused; ADR-V3-014 — DECIDED)
```

### 9.4 What is decided vs conditional/open

| Layer | Status |
|---|---|
| Organization tenant, batch anchor, engine stack (matching/calculation/validation), committed providers (DEFRA/SEAI), snapshot/lineage machinery, org RLS pattern | DECIDED — build on unchanged |
| Work Item abstraction, logical queues, technical-state-machine separation, SLA/capacity reuse, auto-assignment orchestration, approval surfaces, audit consolidation | PROVISIONALLY DECIDED — planning only until blocking sub-decisions resolve |
| Customer-owned factors (ADR-V3-002 — table + snapshot-FK O1 + precedence + approval + consultant RLS) | **DECIDED** — sub-decisions resolved v1.1; implementation pending (V3M-3) |
| Issue Management model (ADR-V3-009 — Option B) | **DECIDED** — architecturally decided; implementation pending (issue model designed before any migration) |
| Processing Entity model (ADR-V3-001 — Option B, dedicated `processing_entities`) | **DECIDED** — implementation pending (V3M-1/V3M-2 migration design at the gate) |
| Factor Provider Architecture (V3M-4) | **DECIDED** — provider-independent architecture; individual provider imports are separate implementation tasks |
| dpq producer, emissions consultant RLS model, skills dimension, legacy-policy hardening | OPEN / INVESTIGATE — do not implement |

---

## 10. Implementation Gate

V3 implementation may begin only after the following conditions are met:

**A. Decisions blocking ALL V3 implementation (must be resolved first):**
- **None.** ADR-V3-001 (Processing Entity Architecture) is **DECIDED — Option B** (dedicated
  `processing_entities` table; `staff_profiles.entity_id IS NULL` = CarbonTally internal;
  populated = Processing Entity staff). It no longer blocks any V3-wide work. Remaining gates
  are the subsystem-specific blockers in B and the conditions in D (integration suite
  executable; regression guard).

**B. Decisions blocking only specific V3 subsystems (resolve before starting that subsystem):**
- **ADR-V3-002** — **DECIDED — READY FOR IMPLEMENTATION** (v1.1). The four OPEN
  SUB-DECISIONS (approval authority D-cf-3, snapshot FK option D-cf-2 → O1, factor
  precedence D-cf-5, consultant RLS model R3) are resolved. V3M-3 is unblocked at the gate.
- **V3M-4** — **DECIDED — READY FOR IMPLEMENTATION** (provider-independent factor
  architecture). Individual provider imports remain separate implementation tasks.
- **ADR-V3-010 INVESTIGATE items** — legacy permissive RLS policies (inventory + any active
  dependency before hardening) and the emissions consultant membership model — block the RLS
  hardening pass and the emissions consultant clause.
- **ADR-V3-004 producer design** — blocks the V3 document work type.

> **Issue Management (ADR-V3-009) is now architecturally DECIDED (Option B — First-Class
> Issue Management Model). It no longer blocks any V3 work at the gate. Its implementation
> (issues table, issue service, API, RLS) remains pending and is designed separately before
> any migration.**

**C. Governance rule (applies to every PROVISIONALLY DECIDED ADR):**
> A PROVISIONALLY DECIDED architecture may be used for architectural planning but
> MUST NOT be treated as authorization to implement database, API, RLS, backend,
> or frontend changes until all blocking dependencies are resolved.

**D. V3 preconditions (from the V3 IA, carried forward):**
- The integration test suite must be executable before V3 DB/RLS work begins
  (V3 IA §21, §26 D14).
- The 19 v2.1 route contracts and the 7,049-factor baseline remain the regression guard
  (V3 IA §21, §28).

---

**No implementation changes were made as part of this register.**
No code, database, migration, RLS, Storage, API, frontend or test changes were made. Factor
baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

---
## X. Cross-Document Consistency Matrix

| Topic | V3 Impact Assessment | Customer Factor Audit | Queue Audit | Final Decision Status |
|---|---|---|---|---|
| Processing Entity | §27 H1 resolved (Option B); V3M-1/V3M-2 conditional | N/A | §10: no entity dimension; conditional on V3-003 | **DECIDED** (ADR-V3-001 — Option B, dedicated `processing_entities`) — implementation pending (V3M-1) |
| Customer Factors | §9, §27 H2; V3M-3 conditional; V3-002/017 | §8 Option B RECOMMENDED; §10 Option A REJECTED; §16 snapshot FK; §30 min change set | N/A | **DECIDED** (ADR-V3-002) — dedicated `customer_factors` table; 4 sub-decisions resolved (D-cf-2 O1, D-cf-3 org Admin/Owner approval, D-cf-5 approved-customer-first precedence, R3 existing consultant-client RLS model) |
| Work Items | §6.1 NEW domain types; §17 one work-item surface; H4 | N/A | §11 Option C RECOMMENDED; §18 hybrid; `manual_review_queue` de-facto canonical | **PROVISIONALLY DECIDED** (ADR-V3-003) |
| Queues | §17 four overlapping queues; "no fifth queue" | N/A | §1, §3, §6: logical queues; §11 Option D rejected | **PROVISIONALLY DECIDED** (ADR-V3-003) |
| Assignment | §5.1 V3-005 attribution; §18 reassignment EXTEND | N/A | §12 `review_assignment_history` active; §16 duplication | **PROVISIONALLY DECIDED** (ADR-V3-005) |
| SLA/KPI | §5.1 V3-011 "DB CONDITIONAL; API EXTEND" | N/A | §6, §13: infrastructure exists; no duplication | **PROVISIONALLY DECIDED** (ADR-V3-006) |
| Issue Management | §5.1 V3-007; §27 H7 now resolved (Option B); V3M-5 conditional | N/A | §6: no unified issue entity | **DECIDED** (ADR-V3-009) — Option B, first-class Issue model; implementation pending |
| RBAC/RLS | §5.1 V3-015 "RLS EXTEND"; entity boundary | §19 customer_factors RLS; §31 consultant clause INVESTIGATE (now RESOLVED — R3: existing consultant-client model) | §15–§16 legacy permissive policies; INVESTIGATE | **PROVISIONALLY DECIDED** (ADR-V3-010) + INVESTIGATE (legacy policies; emissions consultant clause) |
| Calculation | §11 EXTEND for customer factors; snapshots reused | §7, §16, §17: ownership-agnostic; FK obstacle | N/A | **DECIDED** (ADR-V3-002/014) — customer-factor branch + snapshot-FK O1 (exactly-one-source) |
| Lineage | §5.1 V3-012 "REUSE + EXTEND; no DB change" | §16–§17 snapshots; provenance CUSTOMER | §16 audit duplication | **DECIDED** (ADR-V3-014 — O1, immutable provenance) / **PROVISIONALLY DECIDED** (ADR-V3-013 audit consolidation) |
| API | §15.3 versioning H6; 19 routes stable; additive routes | §18 ~7 additive routes; contracts unchanged | §3.4 consumer trace | **PROVISIONALLY DECIDED** (additive-only; H6 deferred) |

---

## Verification

1. File exists at `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` — **yes**.
2. All ten required ADRs exist (ADR-V3-001 … ADR-V3-010) plus six additional (011–016) — **yes**.
3. Every ADR has a status — **yes**.
4. Every OPEN/INVESTIGATE decision and OPEN SUB-DECISION is listed in §6 (blocking decisions) — **yes**.
5. ADR-V3-001 is consistently **DECIDED — Option B** (dedicated `processing_entities`; NULL-internal convention) across §4 matrix, §5 entry, §6.1, §9.1, §9.4, §10A and §X — **yes**; no OPEN/blocker reference to ADR-V3-001 remains in this register.
6. The Implementation Gate (§10) no longer treats ADR-V3-001 as an OPEN V3-wide blocker — **yes**.
7. ADR statuses are consistent: V3-002/009/012/014/015 **DECIDED**; V3-003…008/010/011/013 **PROVISIONALLY DECIDED**; V3-016 **DEFERRED** — **yes** (v1.1: ADR-V3-002 and ADR-V3-014 promoted to DECIDED after the four sub-decisions were resolved).
8. The Architecture Specification and this Register agree on ADR-V3-001 = DECIDED — Option B — **yes** (C1 conflict resolved); they also agree that ADR-V3-002/014 are DECIDED and V3M-3/V3M-4 are READY FOR IMPLEMENTATION (v1.1) — **yes**.
9. No source/schema/backend/frontend/test files were modified — **yes** (architecture documents only, v1.1).
10. No migration was created — **yes**.
11. No database was changed — **yes**.
8. No existing API contract was changed — **yes**.
9. No new architecture was invented without evidence — every decision is traceable to
   `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md`,
   `docs/audit/CarbonTally_V3_Customer_Factors_Impact_Analysis.md`,
   `docs/audit/CarbonTally_V3_Queue_Architecture_Audit.md`; the v1.1 resolutions are recorded
   per the architecture/product owner's direction.
10. The document is a concise decision register (16 ADRs), not an audit — **yes**.

*End of register. Documentation-only — no implementation performed.*
















