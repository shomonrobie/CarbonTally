# CarbonTally V3 Architecture Specification v1.0

**STATUS: DRAFT — ARCHITECTURE SYNTHESIS**
**IMPLEMENTATION: NOT AUTHORIZED**
**DATABASE CHANGES: NONE**
**Date:** 2026-08-11 (v1.1) · 2026-08-10 (v1.0) · Branch: `main`
**Mode:** Documentation-only. No code, database, migration, RLS, API, frontend or test
changes were made. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

**v1.1 update (2026-08-11):** ADR-V3-002 and ADR-V3-014 are now **DECIDED** — the four
customer-factor sub-decisions (D-cf-2 → O1, D-cf-3 → Organization Admin/Owner approval,
D-cf-5 → approved-customer-first precedence, R3 → existing consultant-client RLS model) are
resolved, so **V3M-3 is DECIDED — READY FOR IMPLEMENTATION**. **V3M-4 is DECIDED — READY FOR
IMPLEMENTATION** (provider-independent emission-factor architecture; individual provider
imports remain separate implementation tasks). See §16, §27, §28, §31, §32 and §33.

This document synthesizes the approved CarbonTally V3 architectural decisions
(`docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md`) into one coherent
system architecture. It is a **skeleton (Phase 0)** — sections are declared below and filled
in subsequent phases. Cross-reference the source documents; do not reproduce them.

**Decision status vocabulary used throughout:**
DECIDED (approved) · PROVISIONALLY DECIDED (direction approved; implementation details/
dependencies remain) · OPEN (requires an explicit decision) · DEFERRED (intentionally
postponed) · IMPLEMENTATION DETAIL (resolvable during technical design without changing
architecture).

---

## 1. Executive Summary

CarbonTally V3 is an **operational and multi-entity extension of V2.1**, not a rewrite.
The V2.1 engine stack (matching, calculation, validation, extraction, workflow, report
generation), the 19-route v2.1 API, and the RC2 + M1–M8 schema are carried into V3 largely
unchanged. V3 adds three genuinely new surfaces: the **Processing Entity** model
(ADR-V3-001 — Option B, dedicated `processing_entities` domain), **customer-owned emission
factors** (ADR-V3-002 — DECIDED, READY FOR IMPLEMENTATION), and the **operational control plane**
(Work Items, logical queues, assignment, SLA, issues — ADR-V3-003 … ADR-V3-016).

Approved decisions (per the V3 decision baseline): ADR-V3-001 (Processing Entity — Option B),
ADR-V3-002 (Customer-Owned Factors — sub-decisions resolved v1.1), ADR-V3-009 (Issue
Management — Option B first-class Issue), ADR-V3-012 (Batch vs atomic Work Item), ADR-V3-014
(Snapshot/Provenance — O1), ADR-V3-015 (Factor Provider Architecture — provider-independent,
V3M-4). All remaining ADRs retain their exact register status (DECIDED / PROVISIONALLY DECIDED /
OPEN / DEFERRED). DECIDED does **not** mean implemented; PROVISIONALLY DECIDED does **not**
authorize implementation.

The central architectural convention is the Processing Entity dimension: **CarbonTally
internal processing = `staff_profiles.entity_id IS NULL`**; external processing staff =
`staff_profiles.entity_id = processing_entities.id`. Entity ownership is recorded on the
atomic Work Item; queues are logical views; issues are first-class and distinct from
conversations; customer organization isolation is preserved untouched.

## 2. Purpose and Scope

**Purpose.** Translate the approved CarbonTally V3 Architectural Decisions Register into one
coherent, cross-referenced system architecture that later phases (schema design, RLS,
backend/API, frontend) can implement against — without re-deriving decisions.

**In scope.** The V3 domain model; organization and Processing Entity architecture; identity,
RBAC, RLS/security; work management; document processing; extraction; validation/QC; issue
management; emission-factor and customer-owned-factor architecture; matching/calculation;
customer review/approval; SLA/KPI/escalation; assignment/auto-assignment; configuration;
audit/history/lineage; storage/data access; communication; reporting/export; API/backend;
database and migration impact; operational scenarios; dependencies and implementation order;
remaining open/provisional decisions; architecture baseline; implementation gate.

**Out of scope.** Implementation code, SQL, RLS statements, API contracts, frontend code,
package installation, migrations, and anything not backed by the approved decisions.
This document records **conceptual architecture only** — it does not invent database columns,
enums, API routes, or RLS policies.

**Document contract.** Each section distinguishes DECIDED / PROVISIONALLY DECIDED / OPEN /
DEFERRED / IMPLEMENTATION DETAIL. Conflicts between sources are identified and preserved as
open architectural questions unless a DECIDED ADR resolves them.

## 3. Architectural Principles

Binding principles from the ADR Register §3 (cross-referenced from the V3 IA, the CF Audit
and the Queue Audit):

1. **V3 is an extension of V2.1, not a rewrite.** The canonical pipeline
   (validation → normalisation/match → calculation → CO₂e outputs) already exists and is
   carried into V3 largely unchanged. *(V3 IA §1, §6, §28)*
2. **Do not duplicate existing domain infrastructure.** Extend existing mechanisms; never
   create parallel systems. *(V3 IA §28; CF Audit §29; Queue Audit §11)*
3. **Prefer extending proven active structures.** `manual_review_queue`,
   `review_assignment_history`, `customer_verifications`, `queue_settings`, `sla_*`,
   `staff_workload`, `calculation_snapshots`, `factor_aliases` are the extension targets.
   *(Queue Audit §18; CF Audit §5, §8)*
4. **Separate human Work Items from technical processing state machines.** Do not collapse
   Work Item / Logical Queue / Technical State Machine. *(Queue Audit §18)*
5. **Queues are logical where possible.** A queue is a filtered view over Work Items, not a
   new physical table. *(Queue Audit §6, §11)*
6. **Preserve existing RLS boundaries and the factor baseline.** `emission_factors`
   (7,049 rows, natural key, global read) is immutable; existing tenant RLS is never
   weakened. *(CF Audit §2.1, §19, §29; V3 IA §9)*
7. **Do not redesign engines unnecessarily.** Matching, calculation and validation are
   extended, never replaced. *(CF Audit §6–§7, §28–§29; V3 IA §10–§11)*
8. **Do not implement unresolved architecture decisions.** OPEN / INVESTIGATE / unresolved
   PROVISIONALLY DECIDED dependencies are not implemented until resolved. *(V3 IA §27, §29)*



## 4. Source Documents and Decision Authority

**Decision authority hierarchy:**

| Level | Source | Role |
|---|---|---|
| 1 — Highest authority for V3 decisions | `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` | Approved ADRs (DECIDED / PROVISIONALLY DECIDED / OPEN / DEFERRED) |
| 2 — Focused evidence | `docs/audit/CarbonTally_V3_Customer_Factors_Impact_Analysis.md`, `docs/audit/CarbonTally_V3_Queue_Architecture_Audit.md`, `docs/audit/CarbonTally_V3_Processing_Entity_Architecture_Decision_Analysis.md`, `docs/audit/CarbonTally_V3_Processing_Entity_Open_Questions_Classification.md` | Detailed analysis and evidence behind the ADRs |
| 3 — Broad baseline | `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md` | V2.1 baseline, requirement matrix, migration inventory (V3M-1…V3M-5), human decisions H1–H14 |
| 4 — Implementation reality | Current repository (`supabase/migrations/`, `backend/`, `frontend/`, `admin/`) | Current-state verification; never overrides a DECIDED ADR |

**Decision status rules:**
- **DECIDED** — architecture approved; implementable once the Implementation Gate (§33) is satisfied. Does **not** mean implemented.
- **PROVISIONALLY DECIDED** — direction approved; blocking dependencies must be resolved before implementation.
- **OPEN** — requires an explicit decision; not implemented.
- **DEFERRED** — intentionally postponed.
- **IMPLEMENTATION DETAIL** — resolvable during technical design without changing architecture.

**Conflict handling.** If sources conflict, the conflict is identified and preserved as an
open architectural question unless a DECIDED ADR resolves it. Recorded source conflicts from
the V3 IA (§5.3) — HDPE-vs-emission-factor providers (two separate axes, not a real
conflict); benchmarking internal-only (Phase 9 decision authoritative); API versioning
(needs an explicit decision) — are carried forward here. No conflict is silently resolved.

**Note on ADR-V3-001 status:** ADR-V3-001 (Processing Entity — Option B, dedicated
`processing_entities` domain) is **DECIDED** in both the V3 decision baseline and the ADR
Register (reconciled — register §4 matrix, §5 entry, §6.1, §9.1, §9.4, §10A and §X all record
DECIDED — Option B; the NULL-internal convention `staff_profiles.entity_id IS NULL` is
consistent across both documents). The specification and the register agree; the earlier
C1 status divergence is resolved.

## 5. Current V2.1 Baseline

Verified current state (see §4 sources; repository traced):

| Surface | Current state |
|---|---|
| Engines (8) | matching, calculation, extraction, AI extraction, workflow, validation (A1–A9), benchmarking (internal-only), report generation — complete |
| Repositories (9) | domain access layer over RC2 + M1–M8 tables |
| API | 19 v2.1 routes (`/api/v2/…`): health, business, admin; error envelope; JWT via legacy `auth.py`; org isolation |
| Database | RC2 schema (~100 tables) + M1–M8 (import_batches, calculation_snapshots, domain_events, factor_aliases, dpq workflow columns, new-table RLS) |
| Factor baseline | `emission_factors` = 7,049 (DEFRA-DESNZ/GB 7,029 + SEAI/IE 20, batch-linked) |
| Tenancy | `organizations` (customer tenant) + `organization_members` (owner/admin/member/viewer); `is_org_member()` RLS helper |
| Staff | `staff_profiles`/`staff_roles` — **internal CarbonTally staff only**; no entity/org FK |
| Human work | `manual_review_queue` (atomic items) + `upload_batches` (grouping) + `review_assignment_history` (attribution) |
| Work-management config | `queue_settings`, `sla_definitions`, `sla_compliance`, `business_hours`, `staff_workload`, `staff_performance`, `dashboard_metrics` |
| Technical queues | `document_processing_queue` (state machine; no active producer), `report_generation_queue` (output store), dormant `processing_queue` family |
| Approval | `customer_verifications`/`customer_review_log` (active); `approval_requests`/`approval_decisions` (dormant, FK-bound to `processing_assignments`) |
| Communication | `conversations`/`conversation_participants`/`messages`/`notifications` (org-scoped) |
| Consultant axis | `consultant_profiles`/`consultant_firm_members`/`consultant_clients` (separate from staff and from Processing Entities) |
| Customer factors | **None** — no org-owned factor surface; `factor_aliases` are synonyms only |

**Key baseline conclusions:** (1) the canonical pipeline already exists and is reused; (2) no
Processing Entity concept exists anywhere (Babui is `raw_user_meta_data.company_name` only);
(3) customer-owned factors are absent; (4) the migration is CONDITIONAL — required only if
the entity model, customer factors, or non-GB/IE providers enter scope (V3 IA §29).



## 6. V3 Domain Architecture

### 6.1 Core domain model

The V3 domain is a set of **distinct concepts** (never interchangeable). All terms follow the
ADR Register and the focused audits; no database columns are invented here.

| Domain concept | Definition / distinction |
|---|---|
| **Customer / Organization** | A tenant that owns data (`organizations`). Data owner; not a processor. |
| **Processing Entity** | A contracted Human Data Processing Entity (`processing_entities` domain, ADR-V3-001 Option B). A processor; never a customer. |
| **User** | An identity anchor (`users`). Belongs to exactly one access axis (customer org member, entity staff, CarbonTally staff, or consultant). |
| **Processing Entity Staff** | A user whose `staff_profiles.entity_id` points at a Processing Entity. Entity-scoped access only. |
| **CarbonTally Internal Staff** | A user with `staff_profiles.entity_id IS NULL`. Internal processing + platform operations; authorized cross-entity visibility. |
| **Consultant** | A customer-facing advisor (`consultant_profiles`/`consultant_clients`). Separate axis — not a processor, not staff. |
| **Batch** | Operational grouping of documents (ADR-V3-012: batch = grouping). |
| **Document** | A customer source file (`customer_documents`) attached to a batch; the processing subject. |
| **Work Item** | Atomic unit of human operational work (canonical surface over `manual_review_queue`; ADR-V3-003). |
| **Logical Queue** | A routing/visibility mechanism — a filtered view over Work Items (e.g. "CarbonTally queue", "Entity A queue"). Not a table. |
| **Assignment** | Binding of a Work Item to a worker/supervisor; attribution preserved in `review_assignment_history` (ADR-V3-005). |
| **Issue** | First-class operational problem/exception/defect object requiring tracking, ownership, escalation, resolution (ADR-V3-009, Option B). **Not** a conversation. |
| **Conversation** | Communication between authorized parties (customer ↔ Customer Service; entity-internal; CarbonTally ↔ entity). May be associated with an Issue. |
| **Emission Factor** | CarbonTally-managed reference factor (`emission_factors`, global, 7,049 rows). |
| **Customer-Owned Factor** | A factor owned by a customer organization (`customer_factors` domain, ADR-V3-002 — DECIDED). Separate from CarbonTally factors. |
| **Calculation** | `quantity × multiplier` producing CO₂e, recorded immutably in `calculation_snapshots` (ADR-V3-014). |
| **Report** | Structured processed-data output (`report_generation_queue` = technical output store). |

### 6.2 Work Item / Logical Queue / Technical State Machine

- **Work Item** = actual human operational work (atomic, assignable, attributable).
- **Logical Queue** = routing/visibility mechanism (filtered view over Work Items).
- **Technical State Machine** = system processing state (`document_processing_queue`,
  `report_generation_queue`); not a human work queue.

These three concepts are kept distinct and never collapsed (ADR-V3-003; Queue Audit §18).

### 6.3 Overall V3 domain model (diagram 1)

```
                       CARBONTALLY V3 PLATFORM
                                   │
     ┌─────────────────────────────┼─────────────────────────────┐
     ▼                             ▼                             ▼
CUSTOMER ORG                 PROCESSING ENTITY              CONSULTANT
(owns data)                  (processes work)               (advises customer)
     │                             │                             │
     ▼                             ▼
  DOCUMENT ──► WORK ITEM ──► ASSIGNMENT ──► WORKER / SUPERVISOR
     │           │                            (staff, entity-scoped)
     │           ├── LOGICAL QUEUE (view over work items)
     │           └── ISSUE (first-class) ◄── CONVERSATION (may be associated)
     ▼
  CALCULATION ──► CALCULATION_SNAPSHOT (immutable lineage)
     │
     ▼
  REPORT (report_generation_queue)
     │
     ▼
  EMISSION FACTOR (CarbonTally-managed)  ·  CUSTOMER-OWNED FACTOR (org-scoped)
```

### 6.4 Customer → Document → Work Item (diagram 2)

```
CUSTOMER ORGANIZATION
   │  uploads source files
   ▼
BATCH  (grouping; ADR-V3-012 batch = grouping)
   │
   ▼
DOCUMENT (customer_documents — the processing subject)
   │
   ▼
WORK ITEM (atomic human work; entity_id = processor, NULL = CarbonTally internal)
   │
   ▼
LOGICAL QUEUE  (filtered view: "CarbonTally queue" / "Entity A queue")
   │
   ▼
ASSIGNMENT  (assigned_to worker; attribution in review_assignment_history)
   │
   ▼
WORKER / SUPERVISOR  (staff_profiles; entity-scoped)
```



## 7. Organization and Processing Entity Architecture

### 7.1 Approved decision (ADR-V3-001 — Option B)

**Processing Entity = a dedicated `processing_entities` domain** (no company name hard-coded;
entities are data rows with lifecycle status and contract metadata). CarbonTally's own
internal processing operation is represented by the **`entity_id IS NULL` convention**.

**Architectural convention (not implementation):**
```
staff_profiles.entity_id IS NULL          = CarbonTally internal processing
staff_profiles.entity_id = <entity id>    = external Processing Entity staff
manual_review_queue.entity_id             = owning Processing Entity (NULL = CarbonTally)
upload_batches.entity_id                  = batch-level entity allocation (nullable)
```

The **customer `organizations` table is never used to represent a Processing Entity** — the
two are distinct domains (data owner vs processor). Customer organization isolation is
preserved untouched.

**PROVISIONALLY DECIDED clarifications (from the Open Questions Classification):**
- Contract metadata is part of the Processing Entity domain; exact commercial fields/pricing/
  contract schema are deferred to the V3 schema design phase.
- Entity onboarding is controlled by authorized CarbonTally personnel; entities cannot
  self-activate; lifecycle supports active / remediation-suspended / terminated;
  suspension/termination never deletes historical work, audit, performance or issue history;
  active/assigned work has a defined reassignment/disposition process; entity user access
  respects entity lifecycle. Exact states/authority/RBAC matrix deferred to V3 design.

### 7.2 Organization vs Processing Entity (diagram 3)

```
CUSTOMER ORGANIZATION (data owner)          PROCESSING ENTITY (processor)
┌──────────────────────────────┐            ┌──────────────────────────────┐
│ organizations                │            │ processing_entities          │
│ + organization_members       │            │   lifecycle: active /         │
│ + customer_documents         │            │   suspended / terminated      │
│ + emissions_logs             │            │   contract metadata (deferred)│
│ owner/admin/member/viewer    │            ├──────────────────────────────┤
│ is_org_member() RLS          │            │ staff_profiles.entity_id = id │
└──────────────┬───────────────┘            │ is_entity_member() RLS (new)  │
               │  uploads                    └──────────────┬───────────────┘
               ▼                                             │  processes
     WORK ITEMS (organization_id = customer,                │
                  entity_id = A | B | C | D | NULL) ◄───────┘
               │
               └── entity staff NEVER become organization_members
                   (no customer-org access; entity sees only its assigned work)
```

### 7.3 Processing Entity → Staff → Work Item (diagram 4)

```
PROCESSING ENTITY A  (processing_entities row)
        │
        ├── Entity Admin / Manager   (staff_profiles.entity_id = A)
        │        │
        │        ├── Supervisor      (entity-scoped role)
        │        │        │
        │        │        ├── Worker 1   (staff_profiles.entity_id = A)
        │        │        ├── Worker 2   ── assigned_to ──┐
        │        │        └── Validator                    │
        │        └── (entity staff never see Entity B)     │
        │                                                 ▼
        │                                      WORK ITEM  (manual_review_queue:
        │                                        organization_id = customer,
        │                                        entity_id = A, assigned_to = Worker 2)
        │                                                 │
        └── logical "Entity A queue"  =  work items where entity_id = A
CARBONTALLY INTERNAL  =  staff_profiles.entity_id IS NULL
        └── logical "CarbonTally queue" = work items where entity_id IS NULL
```

### 7.4 Issue vs Conversation (diagram 5)

```
ISSUE  (first-class operational object — ADR-V3-009 Option B)
   • the operational problem / exception / defect / escalation / resolution workflow
   • requires tracking, ownership, escalation, action, resolution
   • carries issue_type, severity, priority, status, owner, assignee, SLA,
     escalation, resolution, audit/history, timestamps
   • entity/customer/work-item/document/batch context where applicable
        ▲
        │ may be associated (optional)
        │
CONVERSATION  (communication between authorized parties)
   • customer ↔ Customer Service            (org-scoped, existing channel)
   • CarbonTally Operations ↔ Entity Manager (separate internal channel)
   • Entity-internal (Manager ↔ Supervisor ↔ Worker)
   • NEVER customer ↔ Processing Entity direct

ISSUE ≠ CONVERSATION   (distinct concepts; never interchangeable)
```

**Design boundary:** a Processing Entity sees only the work it is authorized to process
(entity-scoped); it never gains unrestricted access to the customer's organization; customers
communicate only via CarbonTally Customer Service.



## 8. Identity, RBAC and Access Architecture

### 8.1 Access axes (conceptual — never interchangeable)

V3 distinguishes **four access axes** (see §6.1; ADR-V3-010 PROVISIONALLY DECIDED).
A User belongs to exactly one access axis; the axes are not interchangeable:

| Axis | Identity anchor | Scope | Access model |
|---|---|---|---|
| **Customers** | `users` + `organization_members` | Organization (own org) | `owner/admin/member/viewer` roles; `is_org_member()` RLS (existing) |
| **CarbonTally internal staff** | `users` + `staff_profiles`/`staff_roles` | System | `staff_profiles.entity_id IS NULL` (ADR-V3-001 convention); authorized cross-entity visibility for platform operations |
| **Processing Entity staff** | `users` + `staff_profiles` | Processing Entity | `staff_profiles.entity_id = processing_entities.id`; entity-scoped access only (ADR-V3-001, conditional) |
| **Consultants** | `consultant_profiles`/`consultant_firm_members`/`consultant_clients` | Client org (assigned) | Existing consultant axis; separate from staff and from Processing Entities |

**Access scopes** (context for every authorization decision):
- **System** — CarbonTally platform administration, cross-entity operational visibility.
- **Organization** — the customer tenant (data owner).
- **Processing Entity** — the contracted processing organization (processor).
- **User** — individual identity (staff member, org member, consultant).

### 8.2 Current identity/RBAC state

- Authentication: existing JWT flow (`backend/auth.py`); `AuthUser`, `get_current_user`, `require_admin` (Phase 10). No new authentication system is introduced (ADR-V3-010).
- Staff roles: `staff_profiles`/`staff_roles` today represent **CarbonTally internal staff only** — no entity/org FK (V3 IA §5; ADR-V3-001).
- Customer roles: `organization_members` (owner/admin/member/viewer) with `is_org_member()` RLS helper (V2.1 baseline).
- Consultant axis: `consultant_profiles`/`consultant_firm_members`/`consultant_clients` — **investigation item** whether consultants are also `organization_members` of client orgs (ADR-V3-002 SUB-DECISION R3; ADR-V3-010 INVESTIGATE).
- No Processing Entity dimension exists today (ADR-V3-001 **DECIDED** — Option B, dedicated `processing_entities`; register reconciled).

### 8.3 Entity roles (conceptual — final names deferred)

Processing Entity users conceptually include Entity Admin/Manager, Supervisor, Validator, and Worker (ADR-V3-001 §7; PE Decision Analysis §7). The **final role names, transition authority, and RBAC matrix are explicitly deferred** to the V3 RBAC design phase (PE Open Questions Q6 — PROVISIONALLY DECIDED). No role names are invented here.

### 8.4 CarbonTally internal roles

CarbonTally internal users (System Admin, Operations, Customer Service, Internal Processing Staff) remain on the existing `staff_profiles`/`staff_roles` surface — **no duplicate RBAC system** is created. Internal processing staff are distinguished from Processing Entity staff purely by `staff_profiles.entity_id IS NULL` vs `= processing_entities.id` (ADR-V3-001 convention; architectural, not implementation).

### 8.5 RBAC direction (V3)

- **EXTEND** existing authorization helpers (`require_role`/`require_admin`) with entity-scoped checks (ADR-V3-010 Implementation Impact).
- Do **not** invent final role names or a new RBAC schema in this specification.
- Customer-factor operations are org-scoped (org member with sufficient role); approval authority is an **OPEN SUB-DECISION** (ADR-V3-002 D-cf-3).

---

## 9. RLS / Security Architecture

### 9.1 Conceptual isolation boundaries (no SQL policies written here)

```
CUSTOMER A  ──X──  CUSTOMER B                    (existing: is_org_member())
PROCESSING ENTITY A ──X── PROCESSING ENTITY B    (V3, per ADR-V3-001 — DECIDED: is_entity_member())
PROCESSING ENTITY  ──X──  unrelated customer data (entity sees only authorized work)
CARBONTALLY INTERNAL OPERATIONS ──▶ appropriate cross-entity visibility (system scope)
```

- **Customer isolation** — preserved untouched: `is_org_member()` on tenant tables (`manual_review_queue`, `upload_batches`, `customer_verifications`, `calculation_snapshots`, `emissions_logs`, `factor_aliases`); `emission_factors` global read stays `SELECT USING(true)` with service-role writes (ADR-V3-010; Principle 6).
- **Entity isolation** — deny-by-default + member-of-entity policies **only after** ADR-V3-001 resolves the entity model (conditional; no entity RLS exists or is added now).
- **Staff visibility** — broad `authenticated_read` on staff tables is a **flagged INVESTIGATE/HARDEN** item, not a change made here (Queue Audit §15–§16; ADR-V3-010).
- **Break-glass access** — conceptual per V3-015 (V3 IA §5.1); extend auth/RBAC, never weaken tenant RLS.

### 9.2 New/conditional RLS surfaces

| Surface | RLS pattern | Status |
|---|---|---|
| `customer_factors` (conceptual) | `is_org_member(organization_id)` select/insert/update; delete restricted / soft-deactivate (mirrors `factor_aliases` `select_own`) | **DECIDED** (ADR-V3-002); consultant clause resolved (R3 — existing consultant-client relationship/RLS model, no global access) |
| Work-item logical-queue views | org scope via existing patterns; entity scope per ADR-V3-001 (DECIDED) — implementation pending |
| Issues (first-class) | org/entity scope policies per ADR-V3-010 patterns | DECIDED architecture (ADR-V3-009); implementation pending |
| Legacy permissive queue policies | **INVESTIGATE first** — confirm no active dependency before tightening | INVESTIGATE (ADR-V3-010) |

### 9.3 Security constraints

- Must **not** weaken any existing RLS boundary (Principle 6).
- Must **not** add entity policies before ADR-V3-001.
- Must **not** assume the consultant membership model without investigation (ADR-V3-010).
- No RLS statements are written in this specification.

## 10. Work Management Architecture

### 10.1 Decision basis

ADR-V3-003 (PROVISIONALLY DECIDED): a canonical **Work Item** domain abstraction over the
active `manual_review_queue` surface; **queues are logical** (filtered views, not tables);
technical state machines remain separate; no fifth queue table. ADR-V3-012 (DECIDED):
**batch = grouping; Work Item = atomic**. ADR-V3-005 (PROVISIONALLY DECIDED):
`review_assignment_history` is the attribution mechanism.

### 10.2 Primary workflow (complete flow)

```
CUSTOMER
   ↓  uploads source files
UPLOAD
   ↓
BATCH            (upload_batches — grouping; ADR-V3-012)
   ↓
DOCUMENT         (customer_documents — processing subject)
   ↓
EXTRACTION METHOD
   ├── CSV/Excel         (automated import path)
   ├── AI extraction     (document_processing_queue technical stage)
   └── Human extraction  (Work Item → worker)
   ↓
EXTRACTED RAW DATA      (extraction result; data_entry / ai_extraction_result)
   ↓
VALIDATION              (ValidationEngine A1–A9)
   ↓
NORMALIZATION           (unit/scope/country normalization)
   ↓
FACTOR MATCHING         (FactorMatchingEngine — CarbonTally + customer factors)
   ↓
CUSTOMER REVIEW / APPROVAL (customer_verifications)
   ↓
CALCULATION             (quantity × multiplier)
   ↓
CO2e                    (calculation_snapshots — immutable)
   ↓
EXPORT / DASHBOARD / API (outputs)
```

### 10.3 Work Item / Logical Queue / Technical State Machine

| Concept | Role | Representation |
|---|---|---|
| **Work Item** | Actual human operational work — atomic, assignable, attributable, SLA'd | Canonical surface over `manual_review_queue` (ADR-V3-003) |
| **Logical Queue** | Routing/visibility mechanism — filtered view over Work Items | e.g. "CarbonTally queue" (`entity_id IS NULL`), "Entity A queue" (`entity_id = A`); not a table |
| **Technical State Machine** | System processing state | `document_processing_queue` (document pipeline), `report_generation_queue` (output); not human queues |

### 10.4 Human processing chain (no customer↔entity communication)

```
CUSTOMER
   ↓  (communication only via Customer Service)
CARBONTALLY          (allocation authority; operations)
   ↓
PROCESSING ENTITY    (contracted processor — entity-scoped)
   ↓
SUPERVISOR           (entity-internal assignment/QA authority)
   ↓
WORKER               (performs extraction; staff_profiles.entity_id = entity)
   ↓
EXTRACTION
   ↓
VALIDATION / QC      (ValidationEngine + QC surfaces; entity + CarbonTally layers)
   ↓
CARBONTALLY PROCESSING  (final CarbonTally validation/approval layer)
   ↓
CUSTOMER REVIEW      (customer_verifications — customer approves/rejects)
```

### 10.5 500-document multi-entity scenario (conceptual)

```
CUSTOMER uploads 500 documents
   ↓
BATCH (upload_batches; total=500)
   ↓
CarbonTally Operations allocates (entity_id set per Work Item):
   ├── 100 → CarbonTally internal  (entity_id IS NULL)
   ├── 100 → Processing Entity A
   ├── 100 → Processing Entity B
   ├── 100 → Processing Entity C
   └── 100 → Processing Entity D
   ↓
Each entity: Supervisor assigns Work Items to entity workers
   ↓
Completion is tracked per atomic Work Item (batch progress = count of remaining items)
```

### 10.6 Partial completion (Worker completes 30 of 100, becomes unavailable)

```
Worker receives 100 Work Items (entity-scoped assignment).
Worker completes 30 → completed (attributed to Worker; entity attribution preserved).
Worker becomes unavailable.
Remaining 70 → reassigned via review_assignment_history (new rows; history appended, never
overwritten) to other workers (within entity) or another entity (entity_id updated on pending
items + audit).
Preserved:
  - original worker attribution   (review_assignment_history)
  - processing entity attribution (work item entity_id retained on completed items)
  - assignment history            (append-only)
  - SLA                           (per-item sla_deadline/sla_breached + sla_compliance)
  - audit history                 (review_audit_trail / processing_audit_trail)
  - completed work                (never touched by reassignment)
```

---

## 11. Document Processing Architecture

### 11.1 Decision basis

ADR-V3-004 (PROVISIONALLY DECIDED): `document_processing_queue` (dpq) is a **technical
document-processing state machine**, not the canonical human work queue. Its stages span
AI extraction → manual extraction → QC → customer review. The final producer/consumer
architecture is **not yet decided** — no active backend route produces dpq rows today; wiring
is an OPEN/DEFERRED design question gated behind the V3 document work type.

### 11.2 dpq as technical state machine

| Aspect | State |
|---|---|
| Stage-prefixed state | ai_*, manual_*, qc_*, customer_* column groups (RC2-frozen "single processing-queue direction") |
| Status vocabulary | pending / processing / ai_extracted / manual_review / manual_extraction / qc / customer_review / approved / rejected / completed / failed |
| RLS | tenant policies via `is_org_member`; rc1 `dpq_claim_idx` partial index |
| Active producer | **None today** — legacy monolithic copies only; OPEN/DEFERRED |
| Verdict | KEEP as the document state machine (Queue Audit §17) |

### 11.3 Relationship to Work Items

A document's state machine runs **alongside** its Work Items (extraction items, QC items)
rather than replacing them (Queue Audit §18 hybrid). The V3 document work type, when wired,
becomes the active producer (ingestion → dpq → AI/manual/QC/customer stages). Dormant
`manual_extraction_batches`/`manual_extraction_items` fold into the dpq path when it is wired.

**Constraint:** dpq is never treated as the canonical human work queue; no active producer is
created before the work-type design is decided.



## 12. Extraction Architecture

### 12.1 Extraction methods

The primary workflow supports three extraction methods (see §10.2):

| Method | Path | Surface |
|---|---|---|
| **CSV/Excel** | Automated import path (document/CSV ingestion) | Import pipeline → raw data rows → validation |
| **AI extraction** | Technical AI stage of the document pipeline | `document_processing_queue` `ai_*` stage (ai_extraction_result, ai_confidence_score, ai_mapped_*); confidence-scored |
| **Human extraction** | Work Item executed by a worker | Work Item (`manual_review_queue`) → `data_entry` / `manual_extraction_result`; worker/entity attribution |

### 12.2 Human extraction flow

```
WORK ITEM (manual_review_queue; entity-scoped)
   ↓
WORKER opens assigned item + authorized source document (controlled access)
   ↓
EXTRACTION FORM (required fields; processing instructions)
   ↓
SAVE (partial state preserved — data_entry / manual_extraction_result)
   ↓
SUBMIT (work item completed; attributed to worker)
   ↓
AUTO-VALIDATION (ValidationEngine) / QC / review layers
```

### 12.3 AI extraction

AI extraction is a **technical stage** (dpq `ai_*`), not a human work item. Low-confidence or
failed AI results route to human extraction (dpq status → `manual_review`/`manual_extraction`).
The V3 document work type (producer wiring) is OPEN/DEFERRED (ADR-V3-004).

### 12.4 Attribution and recovery

- Worker attribution: completed items retain the worker (review_assignment_history).
- Partial work recovery: in-progress saved state is preserved for a reassigned worker where
  supported (Master v1 §27).
- No schema invented; extraction results remain on the existing extraction-result surfaces.

---

## 13. Validation and QC Architecture

### 13.1 Automated validation

The v2.1 **ValidationEngine** (A1–A9 rules) is **REUSED** as the automated layer
(validation → normalisation → matching → calculation). It is extended only for
customer-factor validation (value ≥ 0, unit, scope, source, conflict with reference factor)
when customer factors enter scope (ADR-V3-002). Automated validation reduces unnecessary
human review but never silently approves records failing required rules.

### 13.2 Human QC

| QC dimension | What is checked |
|---|---|
| **Extraction QC** | supplier, date, description, quantity, unit, amount, source accuracy |
| **Carbon mapping QC** | activity/category, scope, emission factor, factor source, unit conversion, calculation, mapping correctness |

QC surfaces (existing): `qc_checks`/`qc_errors`/`qc_checklists` (schema), Work Item
`review_audit_trail`, dpq `qc_*` stage. QC sampling percentages are configurable; exceptions
receive 100% review (Master v1 §30–§31).

### 13.3 QC within the workflow layers

QC is a **layer** between worker submission and CarbonTally processing (see §10.4):
worker submission ≠ entity/QC approval ≠ CarbonTally validation ≠ customer approval.
QC failures enter the exception/Issue path (§14) and may return work for correction/rework.

**Status:** Validation/QC architecture is REUSE + EXTEND (no new engine); entity-scoped QC and
configurable sampling remain PROVISIONALLY DECIDED (ADR-V3-010/006 dependency).



## 14. Issue Management Architecture

### 14.1 Decision basis

ADR-V3-009 (**DECIDED** — Option B): an **Issue** is a **first-class operational domain
object**. An Issue is **not** a conversation. The Issue represents the operational problem,
exception, defect, escalation or resolution workflow. Conversations may be associated with an
Issue where communication is required. Issue Management is architecturally decided;
**implementation remains pending**.

### 14.2 Issue lifecycle elements (conceptual — no schema invented)

| Element | Architectural behaviour |
|---|---|
| **Creation** | Issue raised from operational problems/exceptions (QC failures, extraction errors, escalation triggers, validation exceptions) |
| **Ownership** | An Issue has an owner accountable for resolution |
| **Assignment** | Issue assigned to an assignee (entity worker/supervisor, CarbonTally staff, or Customer Service depending on surface) |
| **Priority** | Issue priority for ordering/triage (reuses the existing priority/priority_score vocabulary concept) |
| **Severity** | Severity classification of the operational impact |
| **SLA** | Issue SLA deadline/breach reuses the existing SLA infrastructure (ADR-V3-006) |
| **Escalation** | Escalation path within/up from the owning surface |
| **Resolution** | Defined resolution action; resolved state |
| **Reopening** | Resolved issue may be reopened on recurrence/error |
| **Audit** | Issue history preserved (audit/history strategy — ADR-V3-013) |
| **Associated Work Item** | Issue may reference a Work Item |
| **Associated Document** | Issue may reference a document |
| **Associated Batch** | Issue may reference a batch |
| **Associated Processing Entity** | Issue may carry entity context (entity-scoped surface) |

### 14.3 Issue vs Conversation

- **Issue** = operational problem requiring tracking, ownership, escalation, action, resolution.
- **Conversation** = communication between authorized parties; may be associated with an Issue.
- Issue and Conversation are **distinct concepts, never interchangeable** (see §7.4 diagram 5).

### 14.4 Communication boundary (issues)

- Customer-facing issues → Customer Service (org-scoped, customer-visible status).
- Entity/operational issues → CarbonTally Operations ↔ Processing Entity (entity-scoped,
  internal).
- Entity issue surfaces are entity-scoped; never customer-visible.

**Status:** DECIDED (architecture); implementation pending (issues model designed before any
migration). Existing issue/feedback structures (`user_feedback`, `qc_errors`,
rejection/correction surfaces) are retained, not replaced.

---

## 15. Emission Factor Architecture

### 15.1 Three distinct factor surfaces

```
CARBONTALLY-MANAGED FACTORS        CUSTOMER-OWNED FACTORS          FACTOR PROVIDERS
(emission_factors — global DB)     (customer_factors — org-owned)  (DEFRA, SEAI, future)
       │                                   │                              │
       └───────────────┬───────────────────┘                              │
                       ▼                                                    │
               FACTOR MATCHING (candidate merge — §17)                      │
                       ▼                                                    │
                   CALCULATION (snapshot/provenance — §17)                  │
                                                                             │
   Provider = the SOURCE (DEFRA, SEAI);  a customer factor is NOT a provider
```

The three surfaces are **distinct concepts and never interchangeable** (ADR-V3-002, ADR-V3-015):

| Surface | Owner | Scope | Purpose |
|---|---|---|---|
| **CarbonTally-managed factors** | CarbonTally | global (`emission_factors`, 7,049 rows) | the CarbonTally emission-factor database (DEFRA 7,029 + SEAI 20) |
| **Customer-owned factors** | Customer organization | org-isolated (`customer_factors`, conceptual — §16) | customer/supplier/contract-specific factors; **never** auto-promoted to the global DB |
| **Factor providers** | DEFRA / SEAI (+ future) | source of CarbonTally-managed factors | provider identity via `import_batches.provider_key` + `factor_source`/`factor_set` (ADR-V3-015) |

### 15.2 Provider baseline and roadmap

| Provider | Country | Status | Evidence |
|---|---|---|---|
| **DEFRA** | GB | COMPLETE — 7,029 factors, batch-linked | `emission_factors`; V2.1 baseline (§5) |
| **SEAI** | IE | COMPLETE — 20 factors, batch-linked, CO2-only | `emission_factors`; SEAI reports |
| **EPA (IE)** | IE | Fits today with **no schema change** (new import batch + factors) | ADR-V3-015; V3 IA §9 |
| **ADEME (FR)** | FR | DEFERRED (import task) — violates `CHECK (country IN ('GB','IE'))` and the RC2 natural-key index; provider-independent architecture DECIDED (V3M-4) | ADR-V3-015; V3 IA §9, H3/T3 |
| **IPCC (global)** | global | DEFERRED (import task) — same country-CHECK/natural-key constraints; architecture DECIDED (V3M-4) | ADR-V3-015 |
| **EU residual mix** | EU | DEFERRED (import task) — same constraints; architecture DECIDED (V3M-4) | ADR-V3-015 |
| HDPE processing entities | — | **NEVER** emission-factor providers (separate axis) | ADR-V3-015; V3 IA §5.3, §20 |

### 15.3 Schema sufficiency (V3)

- The current `emission_factors` schema (7,049 rows; natural key `(reporting_year, activity_type, country, unit, scope)`; `CHECK (country IN ('GB','IE'))`) **accommodates additional GB/IE-valid providers with no migration** (V3 IA §9; ADR-V3-015).
- Provider identity is already derivable: `import_batches.provider_key` + `factor_source`/`factor_set`/`reporting_year`/`country`/`scope`/`unit` (V3 IA §9).
- CO2 vs CO2e provenance is preserved via the shared `gas_coverage()` classifier (SEAI → kg CO2; DEFRA → kg CO2e; mixed → kg CO2/CO2e mixed) — never relabelled (V2.1 Phase 9; CF Audit §7).
- **Provider-independent architecture (V3M-4 — DECIDED, v1.1):** CarbonTally uses a single provider-independent emission-factor architecture. The existing provider architecture remains authoritative; DEFRA and SEAI are existing provider implementations; future providers use the **same provider/import architecture** — **no separate factor database and no provider-specific calculation engine**. Individual provider imports remain **separate implementation tasks**.
- **No new provider is introduced in this specification.**

### 15.4 Constraints

- Must **not** change the 7,049 factors or the RC2 natural-key index for committed providers (ADR-V3-015).
- Deferred providers (FR/global/EU) are separate implementation tasks: each entry requires its own scoping decision and the T3 constraint work (country-CHECK widening + natural-key widening with `provider_key` + matching-precedence policy). The provider-independent architecture itself is DECIDED (V3M-4).
- Customer libraries are a **distinct surface** from provider libraries (ADR-V3-002).

## 16. Customer-Owned Factor Architecture

### 16.1 Decision basis

ADR-V3-002 (**DECIDED** — v1.1): customer-owned factors use a **dedicated `customer_factors` domain** (CF Audit §8 Option B RECOMMENDED; Option A — extending global `emission_factors` — **REJECTED**: it breaks the global natural-key model, global RLS, and import provenance, and leaks org data). The four previously OPEN SUB-DECISIONS (D-cf-2/3/5, R3) are **resolved** (see §16.5), so the customer-factor feature is **DECIDED — READY FOR IMPLEMENTATION (V3M-3)**. The conceptual domain:

```
customer_factors  (conceptual domain — no final columns invented)
  • organization_id        → tenant ownership (org-isolated)
  • name / description     → customer-facing label
  • activity_type, category, unit, scope, country, reporting_year
  • factor_value (co2e_multiplier), source, source_reference
  • methodology, effective_from / effective_to
  • status, version, metadata
  • created_by / created_at / updated_at
```

(Field list is conceptual, from CF Audit §6; the audit determines actual required fields during schema design.)

### 16.2 Ownership and isolation

- **Organization ownership**: every customer factor belongs to exactly one customer organization; never globally visible (CF Audit §5).
- **RLS**: `is_org_member(organization_id)` select/insert/update; delete restricted / soft-deactivate (mirrors `factor_aliases`) (ADR-V3-002, now DECIDED).
- **Consultant access (R3 — RESOLVED, v1.1)**: consultants may access customer factors **only for organizations they are authorized to access through the existing consultant-client relationship/RLS model** — **no global consultant access**. No separate `is_consultant_of` clause is invented for a global factor surface.
- **Isolation proof**: Customer A must never see Customer B's factors (CF Audit §16).

### 16.3 Lifecycle and approval

- Lifecycle: **DRAFT → ACTIVE → ARCHIVED/INACTIVE** (soft-deactivate to protect historical calculations/snapshots); version bump on update (CF Audit §8, §13; ADR-V3-002).
- **Approval authority (D-cf-3 — RESOLVED, v1.1)**: **Organization Admin/Owner approves** customer-owned factors. Staff may **create/edit/validate factor drafts** but **cannot approve their own factor** (self-approval prohibited). This unblocks `POST /customer-factors/{id}/approve` and status transitions.
- Versioning: an update creates a new version; **a historical calculation must not silently change** when a customer later edits their factor (CF Audit §8, §12).

### 16.4 Matching, calculation and provenance

- **Matching**: EXTEND the existing FactorMatchingEngine to merge ACTIVE customer factors as candidates alongside CarbonTally factors (CF Audit §14; ADR-V3-002) — no second matching engine.
- **Factor precedence (D-cf-5 — RESOLVED, v1.1)**: **deterministic precedence** — (1) approved customer factor → (2) CarbonTally factor matching → (3) unresolved / manual review. **An approved customer factor is never silently replaced by a CarbonTally factor.**
- **Calculation**: EXTEND the existing CalculationEngine with a customer-factor branch; ownership-agnostic (CF Audit §15) — no second calculation engine.
- **Provenance**: recorded as `factor_source='CUSTOMER'`, `factor_set='CUSTOMER'`, `import_batch_id=NULL`, plus a `customer_factor_id` reference (ADR-V3-014); the calculation snapshot answers *"which exact factor was used?"* (CF Audit §17).
- **Snapshot FK (D-cf-2 — RESOLVED, v1.1)**: `calculation_snapshots.factor_id` NOT NULL FK → `emission_factors` is relaxed per **Option O1** — nullable `factor_id` + `factor_kind` + optional `customer_factor_id` with an **exactly-one-source check**; `calculation_snapshots` then supports provenance to either `emission_factors` (CarbonTally) or `customer_factors` (customer-owned), preserving immutable calculation provenance (ADR-V3-014).

### 16.5 Resolved sub-decisions (DECIDED — v1.1; each was previously OPEN)

| Sub-decision | ID | Resolution |
|---|---|---|
| Approval authority | D-cf-3 | **Organization Admin/Owner approves** customer-owned factors; staff create/edit/validate drafts but cannot approve their own factor |
| Snapshot FK option | D-cf-2 | **Option O1 adopted** — nullable `factor_id` + `factor_kind` + optional `customer_factor_id`, exactly-one-source check |
| Factor precedence | D-cf-5 | **Deterministic:** (1) approved customer factor → (2) CarbonTally factor matching → (3) unresolved / manual review; never silently replace an approved customer factor |
| Consultant access / RLS membership model | R3 / D-cf-6 | Consultants access customer factors **only** via the existing consultant-client relationship/RLS model; **no global consultant access** |

### 16.6 Constraints

- Must **not** put customer factors in `emission_factors` (REJECTED).
- Must **not** create a second matching/calculation engine, second snapshot system, second approval system, new factor enums, or a `customer_calculation_snapshots` table (CF Audit §29).
- Must **not** change the 7,049 factors, `emission_factors` schema/RLS/natural key, or the 19 v2.1 route contracts.
- Must **not** weaken `emission_factors` global RLS.
- Must **not** silently replace an approved customer factor with a CarbonTally factor (D-cf-5 precedence is deterministic).
- Must **not** grant consultants global factor access (R3 — existing consultant-client relationship/RLS model only).
- No final columns are invented in this specification.

## 17. Matching and Calculation Architecture

### 17.1 Canonical pipeline

```
Input Data
    ↓
Validation (ValidationEngine A1–A9 — §13.1)
    ↓
Normalization (units/scope/country/reporting-year)
    ↓
Factor Matching (candidate merge: CarbonTally factors + ACTIVE customer factors)
    ↓
Factor Selection (provider precedence / factor precedence — see below)
    ↓
Calculation (CalculationEngine — ownership-agnostic)
    ↓
Snapshot / Provenance (calculation_snapshots; immutable)
    ↓
CO2e  (with CO2 vs CO2e provenance preserved)
```

### 17.2 Factor matching (EXTEND — not redesigned)

- The existing **FactorMatchingEngine** is candidate-set-agnostic: it can conceptually support CarbonTally factors, customer factors, and (later) supplier-specific factors **without duplicating the engine** (CF Audit §14; ADR-V3-002).
- **Minimum extension**: merge ACTIVE customer factors as candidates (org-scoped) alongside CarbonTally-managed factors; respect the existing dimensions — country, provider/source, factor_set, reporting_year, scope, unit, activity type (CF Audit §14; ADR-V3-015).
- **Provider precedence** — multi-provider precedence policy is **OPEN** (ADR-V3-015 — for a scoped deferred provider). Customer-vs-CarbonTally precedence is **DECIDED** (D-cf-5, v1.1): **(1) approved customer factor → (2) CarbonTally factor matching → (3) unresolved / manual review** — an approved customer factor is never silently replaced.
- **Ambiguous matches** — presented as candidates for customer review (target V3 concept; CF Audit §3 use case D). The selected factor is recorded in the calculation snapshot.

### 17.3 Calculation (EXTEND — not redesigned)

- The existing **CalculationEngine** is ownership-agnostic: customer-owned factors can be used **without a second calculation engine** (CF Audit §15).
- **Snapshot guarantees**: `calculation_snapshots` preserves factor ID, co2e_multiplier value, unit, source, factor_set, import_batch_id, methodology, algorithm_version, and content_hash — verified for reproducibility (CF Audit §7, §17; ADR-V3-014).
- **Customer-factor branch**: provenance `factor_source='CUSTOMER'`, `factor_set='CUSTOMER'`, `import_batch_id=NULL`, `customer_factor_id` reference (ADR-V3-014); snapshot FK relaxation is **DECIDED — Option O1** (D-cf-2 resolved, v1.1 — §16.5).
- **CO2 vs CO2e**: provenance preserved via `gas_coverage()` — SEAI CO2-only results stay kg CO2; mixed aggregations are labelled kg CO2/CO2e mixed; **no CO2→CO2e conversion without an approved methodology** (V2.1 Phase 9; CF Audit §7).
- **Historical stability**: snapshots are immutable; a later customer-factor edit creates a new version and never silently changes past calculations (CF Audit §8, §12; ADR-V3-002).

### 17.4 Constraints

- Must **not** redesign or replace matching/calculation/validation engines (Principle 7; CF Audit §6–§7, §29).
- Must **not** create `customer_calculation_snapshots` (REJECTED — CF Audit §29; ADR-V3-014).
- Must **not** change historical snapshots (immutable).

## 18. Customer Review and Approval

### 18.1 Decision basis

ADR-V3-008 (PROVISIONALLY DECIDED): the **`customer_verifications`** surface (plus
`customer_review_log`) is the customer-approval layer and is kept and extended. Dormant
`approval_requests`/`approval_decisions` are **REPOINT** (deferred) at the canonical Work Item
when approval layers are built. No duplicate approval system.

### 18.2 Five-layer approval separation

```
WORKER SUBMISSION     (worker completes work)
        ↓
ENTITY / QC APPROVAL  (entity supervisor/QA)
        ↓
CARBONTALLY VALIDATION (CarbonTally processing layer)
        ↓
CUSTOMER APPROVAL      (customer_verifications — customer accepts/rejects)
```

Each layer is a separate concept; a Processing Entity cannot approve customer acceptance on
behalf of the customer (Master v1 §32).

### 18.3 Customer review surface

`customer_verifications` (active, RC2-hardened, org-scoped): status
submitted → verified/rejected/revision_requested/escalated; carries escalation flags.
`customer_review_log` records the review audit trail. Customer rejection/correction flows
into reprocessing/versioning (ADR-V3-013; V3 IA V3-013).

### 18.4 Customer communication boundary

Customer communicates **only** with CarbonTally Customer Service. Customer review/approval
happens on the processed result; no direct customer ↔ Processing Entity interaction.

## 19. SLA / KPI / Escalation Architecture

### 19.1 Decision basis

ADR-V3-006 (PROVISIONALLY DECIDED): the SLA / priority / escalation / capacity architecture
**already exists** and is **reused and extended** — never duplicated. Existing surface:
`queue_settings` (auto_assign_enabled, max_reviews_per_staff, sla_hours, escalation_hours,
priority_weights), `sla_definitions` (document_type, priority_level, sla_hours,
escalation_hours), `sla_compliance` (deadline, is_breached, breach_time_minutes),
`business_hours` (working days/hours/timezone), `staff_workload` (workload_score,
capacity_percentage), per-item `priority`/`priority_score`/`escalation_level`/`sla_deadline`
on Work Items, `customer_verifications.is_escalated`.

### 19.2 SLA

- **Per-item SLA**: Work Item `sla_deadline`/`sla_breached` computed from `sla_definitions`
  + `business_hours`.
- **SLA records**: `sla_compliance` tracks deadline/breach/breach-time.
- **Entity-level SLA**: entity-scoped scope over the same structures (conditional on
  ADR-V3-001/006 resolution); no duplicate SLA system.

### 19.3 KPI / performance

| Metric surface | Existing structure | V3 use |
|---|---|---|
| Worker productivity/accuracy | `staff_performance`, `staff_daily_performance` | entity-scoped aggregation via `staff_profiles.entity_id` |
| Team performance | `team_performance` | per-entity grouping |
| Entity capacity | `staff_workload` per worker | entity aggregate (sum of member workers) |
| Dashboards | `dashboard_metrics` | entity-scoped metrics rows |

### 19.4 Escalation

- Work Item escalation: `escalation_level`, `sla_breached`, escalation timestamps; customer
  notification flags.
- Customer escalation: `customer_verifications.is_escalated`/`escalation_reason`.
- Entity operational escalation → CarbonTally Operations (internal, entity-scoped).
- No new escalation system; existing fields + routes are reused/extended.

**Constraint (ADR-V3-006):** must NOT create duplicate SLA, escalation, workload, or
queue-configuration systems; must NOT implement entity-level SLA/capacity before ADR-V3-001
resolution.

---

## 20. Assignment and Auto-Assignment

### 20.1 Decision basis

ADR-V3-005 (PROVISIONALLY DECIDED): `review_assignment_history` is the active attribution
mechanism; dormant `reassignment_history`/`processing_assignments` are reconciled before
retirement. ADR-V3-007 (PROVISIONALLY DECIDED): an **AutoAssignmentEngine** is a backend
orchestration capability, **not** a new queue system; building blocks already exist.

### 20.2 Assignment chain

```
CARBONTALLY OPERATIONS  → allocates batch/Work Items to Processing Entity (entity_id)
        ↓
ENTITY SUPERVISOR       → assigns Work Items to entity workers (within entity only)
        ↓
WORKER                 → claims/processes assigned Work Items
        ↓
(reassignment)         → review_assignment_history new rows; attribution preserved
```

- **Attribution**: `review_assignment_history` (assigned_by/to, previous_assigned_to, action,
  note) — append-only; history is never overwritten (Master v1 §26).
- **Supervisor intervention / reassignment**: same mechanism; entity-scoped.
- **Partial completion (30/70)**: 30 completed stay attributed to the worker; 70 reassigned
  via new history rows; completed work untouched (§10.6).
- **Entity replacement**: pending items re-pointed (entity_id + audit); completed/historical
  records retained (Master v1 §38).

### 20.3 Auto-assignment (conceptual — not implemented here)

The engine orchestrates **existing** inputs (ADR-V3-007; Queue Audit §12):

| Input | Existing source |
|---|---|
| queue | canonical Work Item surface (ADR-V3-003) |
| workload | `staff_workload` (per worker) |
| capacity | staff capacity; entity aggregate |
| priority | `priority`/`priority_score` on Work Items |
| SLA | `sla_deadline`/`sla_compliance` + `business_hours` |
| availability | worker active status |
| entity | `entity_id` scope (which workers/items are eligible) |
| skills | **none today** — skills dimension introduced only if a documented requirement justifies it (OPEN) |

**Constraint:** no new queue subsystem; no skills model invented; engine targets entity workers
only after ADR-V3-001 resolution.



## 21. Configuration Architecture

### 21.1 Decision basis

ADR-V3-006 (**PROVISIONALLY DECIDED**): the SLA / priority / escalation / capacity configuration **already exists** and is **reused and extended** — never duplicated (Queue Audit §13, §16; RULE 3). No new configuration system is created unless repository evidence requires it (PE Decision Analysis §14).

### 21.2 Existing configuration surface

| Configuration | Existing structure | V3 use |
|---|---|---|
| Queue/work-item behaviour | `queue_settings` (auto_assign_enabled, max_reviews_per_staff, sla_hours, escalation_hours, priority_weights) | reuse unchanged; auto-assignment inputs (§20) |
| SLA definitions | `sla_definitions` (document_type, priority_level, sla_hours, escalation_hours) | reuse; entity-scoped SLA per ADR-V3-001 (DECIDED) — implementation pending |
| Business hours | `business_hours` (working days/hours/timezone) | reuse for SLA computation |
| System settings | `system_settings` | platform-level configuration |
| Notifications | `notifications` configuration | per-recipient-type routing |
| Entity-scoped configuration (capacity/SLA/auto-assign/QC/working hours/escalation/notification/workflow) | **none today** — per ADR-V3-001 (DECIDED); implementation pending | extend existing key-value/config patterns; do **not** create a parallel config system |

### 21.3 Configuration direction

- Reuse the existing key/value and settings patterns for all org-scoped configuration (no change).
- Entity-scoped configuration reuses the same mechanisms scoped by entity (per ADR-V3-001 — DECIDED, implementation pending; no new configuration system).
- **Config-ownership decision**: who owns `queue_settings` semantics is an unresolved item (ADR-V3-006 constraint) — do not change semantics without a decision.

### 21.4 Constraints

- Must **not** create duplicate SLA, escalation, workload, or queue-configuration systems (ADR-V3-006; Queue Audit §13, §16).
- Must **not** change `queue_settings` semantics without a config-ownership decision.
- Must **not** implement entity-level configuration before ADR-V3-001.

---

## 22. Audit, History and Lineage

### 22.1 Decision basis

ADR-V3-013 (**PROVISIONALLY DECIDED**): audit/history **reuses the existing layered stack** — no new audit system, no duplicate history surfaces (Queue Audit §16; ADR-V3-013).

### 22.2 Layered audit/history stack

| Layer | Existing structure | Preserves |
|---|---|---|
| Assignment attribution | `review_assignment_history` (active) | who assigned/reassigned; previous assignee; action; note — append-only |
| Event/audit records | `domain_events`, `audit_trail`, AuditLogger/EventBus | who/what/when (audit entries; actor + role) |
| Calculation provenance | `calculation_snapshots` (immutable; content_hash + verify) | which exact factor (id, value, unit, source, factor_set, import_batch_id), methodology, algorithm_version |
| Per-table trails | `review_audit_trail`, `processing_audit_trail`, `customer_review_log`, `reassignment_history` (dormant) | review steps, processing steps, customer approvals, reassignments |
| Batch provenance | `import_batches` (factor imports) | factor import provenance (provider_key, checksum, counts) |

### 22.3 Lineage — "why did CarbonTally calculate this number?"

The lineage is answerable end-to-end from existing structures (V3 IA §5.1 V3-012 — "REUSE + EXTEND; no DB change"):

```
Input data (emissions_logs)
    ↓ extraction method (document_processing_queue stages / import path)
    ↓ normalized activity (emissions_logs normalization)
    ↓ selected factor (calculation_snapshots: factor_id, value, unit, source)
    ↓ factor ownership (CarbonTally-managed vs customer-owned — factor_source='CUSTOMER', customer_factor_id)
    ↓ factor source (provider_key / factor_source / factor_set)
    ↓ factor version (immutable version discipline; customer_factor version)
    ↓ calculation (snapshot: co2e_multiplier, methodology, algorithm_version)
    ↓ CO2e (gas_coverage provenance: kg CO2 / kg CO2e / mixed)
```

### 22.4 Direction and constraints

- **V3 direction**: single attribution record = `review_assignment_history` (ADR-V3-005); add entity scope + actor-role to audit entries; consolidate duplicate history surfaces (`reassignment_history`, `processing_audit_trail`) at the work-item boundary when the Work Item model lands (ADR-V3-013).
- Must **not** create a new audit/history system (ADR-V3-013).
- Must **not** delete dormant history tables until re-pointed (ADR-V3-016 dependency chain).
- Must **not** change historical snapshots (immutable; ADR-V3-014).

---

## 23. Storage and Data Access

### 23.1 Current state

- Supabase Storage provides object storage for customer documents (evidence/source files); bucket/object access is governed by Storage policies (V2.1 baseline).
- Report outputs: v2.1 `report_generation_queue` persists structured content; PDF/HTML **rendering remains out of scope** (Phase 10 boundary; V3 DEFERRED — Reporting/Export, §25).
- Customer-factor evidence attachments (methodology/source/supplier document/certificate) do **not** exist today (CF Audit §19 — future/deferred).

### 23.2 V3 considerations (no change now)

| Item | Status |
|---|---|
| Document evidence storage | existing Storage buckets/objects; unchanged |
| Entity-scoped storage access (signed URLs vs entity bucket) | **INVESTIGATE** — per ADR-V3-001 (now DECIDED); access pattern still to be resolved (PE Open Questions Q9; ADR-V3-010/V3-016) |
| Customer-factor evidence attachments | DEFERRED — not a Phase-V3-MVP storage requirement (CF Audit §19) |
| PDF/HTML report rendering & storage | DEFERRED — out of scope (V3 IA; Reporting/Export §25) |

### 23.3 Constraints

- Must **not** change Storage policies in this specification.
- Must **not** introduce entity-bucket access patterns before ADR-V3-001 resolves the entity model.
- Evidence requirements for customer factors are documented as a deferred item, not implemented.

## 24. Communication Architecture

### 24.1 Communication boundaries (mandatory)

```
CUSTOMER  ────────↔──────── CARBONTALLY CUSTOMER SERVICE    (existing org-scoped channel)
CUSTOMER  ────────X──────── Processing Entity               (NEVER direct)
CARBONTALLY OPERATIONS ──↔── PROCESSING ENTITY               (separate internal channel)
ENTITY MANAGER ──↔── SUPERVISOR ──↔── WORKER                 (entity-internal)
```

**Explicit rules:**
- Customers communicate **only** with CarbonTally Customer Service.
- **No direct customer ↔ Processing Entity communication** is exposed anywhere.
- CarbonTally Operations ↔ Processing Entity is an internal provider channel, separate from
  customer chat (Master v1 §45).
- Entity-internal communication (Manager ↔ Supervisor ↔ Worker) is entity-scoped and never
  customer-visible (Master v1 §46).

### 24.2 Channels

| Channel | Parties | Surface |
|---|---|---|
| Customer support | Customer ↔ Customer Service | `conversations`/`conversation_participants`/`messages`/`notifications` (org-scoped, existing) |
| CT ↔ Entity operations | CarbonTally Operations ↔ Entity Manager | separate internal conversation surface (entity-scoped); not customer chat |
| Entity-internal | Entity Manager ↔ Supervisor ↔ Worker | entity-scoped internal notes/chat |
| Notifications | per recipient type | `notifications` (recipient_type exists) |

### 24.3 Design rule

No message/conversation row may be visible to both a customer and a Processing Entity staff
member unless it is a CarbonTally-moderated operational thread. The recommended pattern is
**separate conversation surfaces per boundary** (customer / CT-entity / entity-internal)
rather than one chat with mixed participants.

### 24.4 Issues respect the boundary

- Customer-facing issues → Customer Service (customer-visible status).
- Entity/operational issues → CarbonTally Operations ↔ Entity (entity-scoped, internal).
- Entity issue surfaces never customer-visible (see §14.4, §7.4).



## 25. Reporting and Export

### 25.1 Decision basis

- **REUSE** the v2.1 structured-report architecture: `ReportGenerationEngine` (structured content), `ReportsRepository`, `report_generation_queue` (technical output mechanism — ADR-V3-003/004), `report_templates`/`report_versions`/`report_comments` (report-related DB structures).
- **PDF/HTML rendering is DEFERRED** (Phase 10 scope boundary; V3 §23). Reports remain structured content suitable for later rendering/API consumption — never a reporting UI.

### 25.2 Report content (V3)

The structured report composes (Phase 9 contract): metadata, organization, reporting period, emissions totals, scope summaries, activity summaries, validation results, benchmarking results, **provenance / factor information** (CO2 vs CO2e preserved via `gas_coverage` — SEAI kg CO2, DEFRA kg CO2e, mixed kg CO2/CO2e), calculation information, source/data lineage, generation metadata. Insufficient data is represented explicitly, never fabricated (Phase 9C).

### 25.3 V3 additions (conceptual)

| Capability | Status |
|---|---|
| Structured report content + API access (Phase 10) | REUSE unchanged |
| Customer-factor provenance in reports (`factor_source='CUSTOMER'`) | EXTEND (report provenance section; ADR-V3-002/014) |
| Report versioning / comments | existing structures REUSE |
| Approval of reports | within five-layer approval (customer_verifications; ADR-V3-008) |
| PDF / HTML rendering | DEFERRED — out of scope |
| Regulatory / external reporting formats (CSRD, ESOS, etc.) | FUTURE — no documented V3 requirement |
| Export (CSV/Excel) work type | FUTURE — work-type catalogue item (Queue Audit §8), not committed |

### 25.4 Constraints

- Must **not** implement rendering, templates for customer-facing PDF/HTML, or a reporting UI (Phase 10 boundary).
- Must **not** claim regulatory-framework compliance without a decision (V3 IA §14, §27).

---

## 26. API / Backend Architecture

### 26.1 Compatibility principle

- The **19 v2.1 route contracts** and the error envelope remain the **regression guard** (ADR-V3-002; V3 IA §21, §28). V3 API work is **additive and compatible**; API versioning is an **OPEN/DEFERRED** decision (V3 IA §15.3 H6).
- API routes **delegate to existing engines/repositories** — no business logic duplicated in route handlers (Phase 10 principle).

### 26.2 Backend module mapping (conceptual — no files created)

| Module | Action | V3 reason |
|---|---|---|
| `engines/` (matching, calculation, validation, benchmarking, report_generation) | **KEEP** | reused unchanged; extended only for customer factors (§17) |
| `engines/report_generation.py`, `data/reports.py` | **EXTEND** | customer-factor provenance in report content |
| `auth.py`, `api/dependencies.py` | **EXTEND** | entity-scoped authorization checks (ADR-V3-010) |
| `data/emissions_logs.py`, `data/organizations.py`, `data/emission_factors.py`, `data/factor_aliases.py`, `data/audit.py`, `data/imports.py` | **KEEP** | reused unchanged |
| `data/reports.py` | **EXTEND** | optional provenance exposure (`CalculationSnapshotOut`) |
| NEW `CustomerFactor` domain + `CustomerFactorsRepository` | **NEW** | ADR-V3-002 |
| NEW `WorkItem` domain/service layer | **NEW** | ADR-V3-003/011 — abstraction over `manual_review_queue`, no new table |
| NEW `AutoAssignmentEngine` | **NEW** | ADR-V3-007 — orchestration only, no new queue/schema |
| NEW `Issue` service | **NEW** | ADR-V3-009 — implementation pending design |
| NEW `ProcessingEntity` domain/service | **NEW** | ADR-V3-001 — conditional on the entity decision |
| `infra/event_bus.py`, `infra/audit_logger.py` | **KEEP** / **EXTEND** | audit scope: entity + actor-role (ADR-V3-013) |
| Legacy monolith (`backend/routes/`, `process_emissions.py`) | **RETIRE LATER** | superseded by the v2.1 API surface (outside this specification's action) |

### 26.3 Conceptual API additions

| Endpoint group | Status | Notes |
|---|---|---|
| Customer factors (`POST/GET/PUT/deactivate/approve`) | NEW (~7 additive routes) | ADR-V3-002; DECIDED (D-cf-2/3/5, R3 resolved v1.1) — approval route enforces D-cf-3 authority |
| `factor-match` / `calculate` | EXTEND | customer-factor candidates + provenance exposure |
| Work items / logical queues | NEW | ADR-V3-003/011 |
| Assignment / reassignment | EXTEND | existing `/queue/assign`, `/queue/reassign` (ADR-V3-005) |
| Auto-assign control | NEW | ADR-V3-007 |
| Issues | NEW | ADR-V3-009 — pending |
| Processing-entity admin | NEW | ADR-V3-001 — DECIDED (implementation pending V3M-1) |
| `ImportMappingEngine` endpoints (`/process/*`, V3-001) | NEW | OPEN/DEFERRED — producer wiring (ADR-V3-004) |

### 26.4 Constraints

- Must **not** change existing contracts or the error envelope.
- Must **not** create API code in this specification.

## 27. Database Architecture Impact

### 27.1 Classification (conceptual — no migration SQL, no final schema)

| Domain | Action | Notes |
|---|---|---|
| `emission_factors` (7,049) | **NO CHANGE** | immutable global factor DB; natural key + GB/IE CHECK preserved (ADR-V3-015) |
| `organizations`, `organization_members`, `emissions_logs`, `factor_aliases`, `conversations` | **NO CHANGE** | existing org/tenant surfaces |
| `manual_review_queue`, `upload_batches`, `review_assignment_history`, `customer_verifications`, `queue_settings`, `sla_*`, `business_hours`, `staff_workload`, `report_generation_queue`, `report_*` | **REUSE** | canonical Work Item / batch / attribution / approval / config / SLA / output surfaces (ADR-V3-003/005/006/008/012) |
| `processing_entities` (+ `staff_profiles.entity_id`, `entity_id` on work tables) | **NEW** | ADR-V3-001 Option B — dedicated entity domain; conditional until the entity decision is recorded |
| `customer_factors` | **NEW** | ADR-V3-002 — dedicated org-owned factor table; RLS `is_org_member` (Option A REJECTED); **DECIDED — READY FOR IMPLEMENTATION (V3M-3)** |
| `calculation_snapshots.factor_id` FK | **EXTEND** | snapshot-FK relaxation per **Option O1** (nullable `factor_id` + `factor_kind` + optional `customer_factor_id`, exactly-one-source check) — **DECIDED** (D-cf-2 resolved, v1.1) |
| `issues` | **NEW** | ADR-V3-009 — first-class Issue model; implementation pending design |
| `domain_events` / `audit_trail` / `review_assignment_history` | **EXTEND** | entity scope + actor-role on audit entries (ADR-V3-013) |
| `processing_queue` family, `reassignment_history`, `approval_requests`/`approval_decisions`, `manual_extraction_batches`/`items` | **RETIRE LATER** | ADR-V3-016 dependency chain — never deleted, consolidated/archived after re-pointing |
| `internal_tasks`/`task_assignments` (intent only) | **NEVER CREATE** | superseded by the Work Item model (ADR-V3-016) |

### 27.2 Deferred/conditional DB work

- Deferred providers (FR/global/EU): country-CHECK widening + natural-key widening with `provider_key` + precedence policy — **individual provider imports are separate implementation tasks** (V3M-4 DECIDED — provider-independent architecture; each entry needs its own scoping decision + T3 constraint work).
- Entity-scoped columns on work tables: **CONDITIONAL** on ADR-V3-001.
- `customer_factors` + snapshot-FK (O1): **DECIDED — READY FOR IMPLEMENTATION** (D-cf-2/3/5, R3 resolved, v1.1) — V3M-3.

### 27.3 Constraints

- No migration SQL and no final schema are written in this specification.
- Must **not** change the 7,049 factors, existing RLS boundaries, or the 19 v2.1 route contracts (ADR-V3-002 constraints).

## 28. Migration Architecture

### 28.1 Migration inventory (preliminary — derived, NOT created)

| ID | Purpose | Tables affected | Depends on | Status |
|---|---|---|---|---|
| **V3M-1** | Processing Entity foundation | `processing_entities` (NEW), `staff_profiles.entity_id` (EXTEND) | ADR-V3-001 decision | CONDITIONAL |
| **V3M-2** | Entity relationship on work items | `entity_id` on work/queue tables (EXTEND) | V3M-1 | CONDITIONAL |
| **V3M-3** | Customer factors + snapshot FK | `customer_factors` (NEW), `calculation_snapshots` FK relaxation (O1) | ADR-V3-002 **DECIDED** (D-cf-2/3/5, R3 resolved) | **DECIDED — READY FOR IMPLEMENTATION** |
| **V3M-4** | Provider-independent factor architecture (deferred-provider widening T3 when a provider is scoped) | `emission_factors` country CHECK + natural key (only when a specific provider import is scoped) | ADR-V3-015 (provider-independent architecture DECIDED); individual imports are separate tasks | **DECIDED — READY FOR IMPLEMENTATION** |
| **V3M-5** | First-class Issues | `issues` (NEW) + RLS | ADR-V3-009; work-item boundary (ADR-V3-003) | CONDITIONAL — DECIDED architecture |

All V3M items are conditional on the Implementation Gate (§33) — none is created in this
specification. As of v1.1: V3M-3 and V3M-4 are **DECIDED — READY FOR IMPLEMENTATION**;
V3M-5 is architecturally decided (design before migration). V3M-1 and V3M-2 are unchanged.

### 28.2 Dependency-aware migration order

Derived from ADR dependencies (not assumed):

```
1. Processing Entity foundation        (V3M-1)  — unblocks entity scope everywhere
2. RBAC / RLS                          — entity policies + customer-factors policies
3. Work Item ↔ entity relationship     (V3M-2)  — depends on 1
4. Assignment                          — reuse review_assignment_history (no migration)
5. SLA / KPI                           — entity scope (no migration at org scope)
6. Issue Management                    (V3M-5)  — depends on Work Item boundary
7. Customer Factors                    (V3M-3)  — DECIDED (sub-decisions D-cf-2/3/5, R3 resolved); depends on RLS plan
8. Calculation / snapshot changes      — snapshot-FK (O1) within V3M-3
9. API                                 — additive routes, after backend domains
10. Frontend                           — later phase
```

Parallel tracks: provider expansion (V3M-4) is **DECIDED — READY FOR IMPLEMENTATION** (provider-independent architecture); each individual provider import is a separate implementation task that runs when scoped, independently of the operational track; queue retirement (ADR-V3-016) runs **after** the Work Item model and dpq producer land.

### 28.3 Migration principles

- All migrations **backward compatible**; existing V2.1 data is not migrated except where a new FK/column requires defaulting (entity scope defaults to CarbonTally-internal `NULL`).
- Existing RLS is never weakened; new policies are additive.
- `internal_tasks`/`task_assignments` are **never created** (ADR-V3-016).
- No migration is created in this specification.

## 29. Operational Scenarios

### 29.1 Scenario catalogue

| # | Scenario | Architectural behaviour |
|---|---|---|
| **1** | **500-document batch** | One `upload_batches` grouping; 500 atomic Work Items; CarbonTally Operations allocates 100 each to Entities A/B/C/D and 100 to CarbonTally internal (entity_id = NULL). Batch-level progress aggregates Work Items (§10.3). |
| **2** | **Multiple Processing Entities** | Entity isolation via entity-scoped RLS (per ADR-V3-001 — DECIDED); Entity A sees only its Work Items; never other entities' or unrelated customer data (§9.1, §7.2). |
| **3** | **Worker partial completion (30/70)** | Worker completes 30 of 100 Work Items (attributed); 70 remain pending. Attribution to the worker and entity is preserved via `review_assignment_history` (§10.6, §20.2). |
| **4** | **Worker reassignment** | Remaining 70 reassigned via new `review_assignment_history` rows (assigned_by/to, previous_assigned_to, action); the original worker's 30 completed items stay attributed; entity performance remains accurate (§20.2). |
| **5** | **Entity suspension** | Lifecycle state suspended/remediation (PROVISIONALLY DECIDED Q6); active/assigned work has a defined reassignment/disposition process; historical work/audit/performance never deleted; entity users' operational access respects the lifecycle (§10.5, §7.2). |
| **6** | **Entity termination** | Lifecycle state terminated; queued/assigned/in-progress work dispositioned (reassigned); completed work, audit history, issues, and performance history remain attributable (PE Decision Analysis §16; ADR-V3-001 Q6). |
| **7** | **Customer factor selection** | Customer creates/activates a customer-owned factor; FactorMatchingEngine merges ACTIVE customer factors as candidates alongside CarbonTally factors; selection recorded in the calculation snapshot with `factor_source='CUSTOMER'` provenance (§16, §17). |
| **8** | **Customer rejects extracted data** | Customer review via `customer_verifications` (submitted → rejected/revision_requested); rejection/correction flows into reprocessing/versioning (ADR-V3-008, §18); never direct customer ↔ Processing Entity. |
| **9** | **Issue escalation** | First-class Issue (ADR-V3-009) with severity/priority/SLA/escalation; escalation within/up from the owning surface (customer issues → Customer Service; entity issues → CarbonTally Operations); reuses existing SLA/escalation infrastructure (§14, §19). |
| **10** | **Customer communication** | Customer ↔ CarbonTally Customer Service only (org-scoped `conversations`); CarbonTally Operations ↔ Entity via the separate internal channel; no direct customer ↔ Processing Entity communication (§24). |

### 29.2 Cross-cutting guarantees

- **Attribution** — never lost on reassignment, suspension, or termination (review_assignment_history).
- **Isolation** — customer/entity/consultant boundaries hold under every scenario (§9).
- **Provenance** — factor/calculation/approval/correction lineage preserved (§22).
- **No fabrication** — insufficient data is represented explicitly, never zeroed (Phase 9; §17).

## 30. Dependencies and Implementation Order

### 30.1 Dependency graph (derived from ADR dependencies)

```
ADR-V3-001 (Processing Entity)  ──►  RBAC/RLS (ADR-V3-010)  ──►  entity scope on Work Items (ADR-V3-003)
        │                                                    │
        │                                                    ├──► Assignment (ADR-V3-005)  ──►  SLA/KPI (ADR-V3-006)
        │                                                    │
        │                                                    └──► AutoAssignment (ADR-V3-007)
        │
        ├──► Issues (ADR-V3-009)  ◄── Work Item boundary (ADR-V3-003)
        │
        └──► Customer Factors (ADR-V3-002)  ──►  snapshot FK (ADR-V3-014)
        │         └── DECIDED (sub-decisions D-cf-2/3/5, R3 resolved — v1.1)
        │
        └──► DPQ producer (ADR-V3-004 — OPEN/DEFERRED)
```

### 30.2 Proposed implementation order (dependency-aware)

```
 1. Architecture decisions    resolve remaining OPEN blockers (H6 API versioning, dpq producer;
                              V3M-3/V3M-4 sub-decisions already RESOLVED — v1.1)
 2. Database changes          V3M-1 → V3M-2 → V3M-5 → V3M-3 (V3M-4 READY FOR IMPLEMENTATION —
                              individual provider imports are separate tasks; §28.2)
 3. RLS                       entity policies + customer-factors policies (additive, never weaker)
 4. Domain changes            ProcessingEntity, CustomerFactor, WorkItem, Issue domains
 5. Repository changes        CustomerFactorsRepository; extend audit scope
 6. Backend services          AutoAssignmentEngine, Issue service, entity service
 7. Engine changes            matching/calculation/validation extension for customer factors (§17)
 8. API                       additive routes (customer factors, work items, issues, entity admin)
 9. Security/RLS verification isolation tests per boundary
10. Testing                   new V3 suite + regression (19 v2.1 contracts; 7,049-factor baseline)
11. Integration               scenarios (§29) end-to-end
12. Documentation             update the register/specification as decisions resolve
```

Parallel/deferred: provider expansion (V3M-4 — DECIDED; each individual provider import is a separate implementation task); queue retirement (ADR-V3-016 after Work Item model + dpq producer); reporting rendering and frontend later.

### 30.3 Preconditions (carried from the register §10D)

- The integration test suite must be **executable** before V3 DB/RLS work begins (V3 IA §21, §26 D14).
- The 19 v2.1 route contracts and the 7,049-factor baseline remain the **regression guard** (V3 IA §21, §28).

## 31. Remaining Open / Provisional Decisions

### 31.1 Decision status snapshot (from the ADR Register)

| ADR | Title | Status | Blocks |
|---|---|---|---|
| V3-001 | Processing Entity | **DECIDED** (Option B — dedicated `processing_entities` table; register reconciled) | entity-scope implementation (V3M-1/V3M-2) |
| V3-002 | Customer-Owned Factors | **DECIDED** — 4 sub-decisions resolved (D-cf-2 O1, D-cf-3 org Admin/Owner, D-cf-5 approved-customer-first, R3 consultant model) | customer-factor DB/API/RLS/matching (V3M-3 READY FOR IMPLEMENTATION) |
| V3-003 | Work Item / Queue | **PROVISIONALLY DECIDED** | Work Item domain layer |
| V3-004 | Document Processing | **PROVISIONALLY DECIDED** — producer wiring OPEN/DEFERRED | dpq active producer |
| V3-005 | Assignment | **PROVISIONALLY DECIDED** — dormant-history reconciliation unresolved | retirement of dormant assignment tables |
| V3-006 | SLA / KPI / Escalation | **PROVISIONALLY DECIDED** — config-ownership item | entity-level SLA/capacity |
| V3-007 | Auto Assignment | **PROVISIONALLY DECIDED** — skills dimension OPEN | AutoAssignmentEngine (skills) |
| V3-008 | Customer Review/Approval | **PROVISIONALLY DECIDED** | approval layering |
| V3-009 | Issue Management | **DECIDED** (Option B) | issues implementation pending design |
| V3-010 | RLS / Security | **PROVISIONALLY DECIDED** — INVESTIGATE (legacy policies; emissions consultant model) | RLS hardening; emissions consultant clause |
| V3-011 | Work Item Identity | **PROVISIONALLY DECIDED** | typed work_type layer |
| V3-012 | Batch vs Atomic | **DECIDED** | — |
| V3-013 | Audit / History | **PROVISIONALLY DECIDED** | audit consolidation |
| V3-014 | Snapshot / Provenance | **DECIDED** — Option O1 adopted (D-cf-2 resolved, v1.1) | snapshot-FK migration (O1) |
| V3-015 | Factor Providers | **DECIDED** — provider-independent architecture (V3M-4); individual provider imports are separate tasks | a scoped provider import |
| V3-016 | Queue Retirement | **DEFERRED** | retirement execution |

### 31.2 OPEN items requiring a decision before implementation

| Item | ID | Where | Must resolve before |
|---|---|---|---|
| Provider import scope (a specific deferred provider, e.g. EPA/ADEME) | H3 / T3 | V3 IA §27 | the specific provider import (V3M-4 architecture itself is DECIDED) |
| API versioning | H6 | V3 IA §15.3 | additive-route release |
| dpq producer architecture | ADR-V3-004 | Queue Audit §3.3 | document work type |
| Skills dimension | ADR-V3-007 | Queue Audit §12 | auto-assignment (skills) |
| Config ownership (`queue_settings`) | ADR-V3-006 | Queue Audit §13 | config changes |
| Dormant history reconciliation | ADR-V3-005 | Queue Audit §16 | retirement of dormant tables |

### 31.3 Governance rule

> A PROVISIONALLY DECIDED architecture may be used for architectural planning but **MUST NOT be treated as authorization to implement** database, API, RLS, backend, or frontend changes until all blocking dependencies are resolved (register §10C).

## 32. V3 Architecture Baseline

### 32.1 What is DECIDED (architecture approved)

- **Processing Entity** — dedicated `processing_entities` domain (ADR-V3-001 Option B; decision baseline). Convention: `staff_profiles.entity_id IS NULL` = CarbonTally internal; `= processing_entities.id` = external entity staff.
- **Customer-Owned Factors** — dedicated `customer_factors` domain; sub-decisions resolved v1.1 (D-cf-2 O1 snapshot FK, D-cf-3 org Admin/Owner approval, D-cf-5 approved-customer-first precedence, R3 consultant-client RLS model) (ADR-V3-002).
- **Snapshot / Provenance** — `calculation_snapshots` single immutable record; snapshot-FK Option O1 (ADR-V3-014, D-cf-2 resolved).
- **Issue Management** — first-class Issue model, distinct from Conversation (ADR-V3-009 Option B).
- **Batch vs atomic Work Item** — batch = grouping (`upload_batches`); Work Item = atomic (`manual_review_queue` row) (ADR-V3-012).
- **Factor Provider Architecture** — provider-independent emission-factor architecture; DEFRA/SEAI committed; EPA fits without schema change; HDPE never a provider (ADR-V3-015; V3M-4 DECIDED — individual provider imports are separate implementation tasks).

### 32.2 What is PROVISIONALLY DECIDED (direction approved; implementation gated)

Work Item / logical queues (V3-003) · dpq state machine (V3-004) · assignment attribution (V3-005) · SLA/KPI reuse (V3-006) · AutoAssignmentEngine (V3-007) · customer review/approval (V3-008) · RLS extension + INVESTIGATE items (V3-010) · Work Item identity (V3-011) · audit/history consolidation (V3-013).

### 32.3 What is OPEN / DEFERRED

- OPEN: provider import scope for a specific deferred provider (H3/T3 — V3M-4 architecture is DECIDED); API versioning H6; dpq producer; skills; config ownership; dormant-history reconciliation.
- DEFERRED: queue retirement (V3-016); PDF/HTML rendering; regulatory reporting formats; customer-factor evidence storage; external/peer benchmarking.

### 32.4 Architecture baseline (decided + conditional)

```
ORGANIZATION (customer)  →  PROCESSING ENTITY (DECIDED — implementation pending V3M-1)  →  BATCH (upload_batches)
        →  WORK ITEM (manual_review_queue)  →  LOGICAL QUEUE  →  ASSIGNMENT
        →  WORKER / SUPERVISOR  →  SLA / KPI / AUDIT  →  COMPLETION

Technical state machines (separate):  document_processing_queue · report_generation_queue

Customer-owned factors:  customer_factors  →  Factor Matching (candidate merge)
        →  Calculation  →  Snapshot / Provenance (CUSTOMER; FK O1 — DECIDED)
```

### 32.5 Invariant baseline (unchanged)

`emission_factors` = 7,049 (DEFRA-DESNZ/GB 7,029 + SEAI/IE 20, batch-linked); 19 v2.1 route contracts; existing RLS boundaries; error envelope.

---

## 33. Implementation Gate

**Architecture Specification ≠ implementation authorization.**

Implementation of any V3 capability **may begin only after all of the following**:

1. **Architecture Specification reviewed** — this document reviewed and accepted by the product/architecture owner.
2. **Provisional decisions resolved where implementation requires them** — every PROVISIONALLY DECIDED ADR and OPEN SUB-DECISION that materially affects the work (per §31.2) is resolved; a PROVISIONALLY DECIDED architecture is **not** authorization to implement (governance rule §31.3). As of v1.1 the customer-factor sub-decisions (D-cf-2/3/5, R3) and the V3M-4 provider architecture are resolved — V3M-3 and V3M-4 are **DECIDED — READY FOR IMPLEMENTATION** at the architecture level, subject to the remaining gate conditions below.
3. **DB change plan approved** — the conditional migration sequence (§28.2) and each V3M item reviewed and approved; **no migration is created before this gate.**
4. **RLS plan approved** — new/conditional policies (§9.2) reviewed; existing boundaries never weakened.
5. **Backend plan approved** — module mapping (§26.2) and new services reviewed.
6. **API compatibility plan approved** — additive-routes plan (§26.3); the 19 v2.1 contracts and error envelope remain the regression guard.
7. **Migration sequence approved** — dependency-aware order (§28.2) and parallel tracks agreed.
8. **Preconditions met** — the integration test suite is executable (D14) before V3 DB/RLS work; regression guard confirmed.

Until the gate is satisfied, this specification remains **DRAFT — ARCHITECTURE SYNTHESIS**, implementation **NOT AUTHORIZED**, database changes **NONE**.

**No implementation changes were made as part of this specification.** No code, database, migration, RLS, Storage, API, frontend or test changes were made. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

---

*All sections 1–33 populated (Phase 0 skeleton; Phase 1 Domain; Phase 2 Operational Workflow;
Phase 3 Security, Data & Factor; Phase 4 Technical Architecture & Implementation Boundary).
STATUS: DRAFT — ARCHITECTURE SYNTHESIS. IMPLEMENTATION: NOT AUTHORIZED. DATABASE CHANGES: NONE.
v1.1 (2026-08-11): ADR-V3-002/014 DECIDED (customer-factor sub-decisions resolved) — V3M-3
READY FOR IMPLEMENTATION; V3M-4 DECIDED (provider-independent factor architecture; imports are
separate tasks). This specification is not an implementation authorization (see §33
Implementation Gate).*
