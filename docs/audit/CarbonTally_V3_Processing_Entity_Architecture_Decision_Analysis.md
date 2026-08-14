# CarbonTally V3 Processing Entity Architecture
# Decision Analysis

**Status:** READ-ONLY DECISION ANALYSIS — RECOMMENDATION ONLY. NO IMPLEMENTATION.
**Date:** 2026-08-10 · Branch: `main`
**Mode:** Read-only. No code, database, migration, RLS, Storage, API, frontend or test
changes were made. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

**Purpose:** Provide the evidence and the single recommended option needed to resolve
**ADR-V3-001 — Processing Entity Architecture** (currently OPEN and the primary V3
implementation blocker). This document does **not** update the Architectural Decisions
Register and does **not** implement the recommended architecture.

**Sources (all cross-checked):**
- `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md` (V3 IA) — §8 (V3M-1/V3M-2), §27 (H1), §29
- `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` (ADR Register) — ADR-V3-001 (OPEN), ADR-V3-003, ADR-V3-010
- `docs/audit/CarbonTally_V3_Queue_Architecture_Audit.md` (Queue Audit) — §3, §10, §14–§17
- `docs/audit/CarbonTally_V3_Customer_Factors_Impact_Analysis.md` (CF Audit) — org-isolation pattern, §9, §19
- `docs/cline/CarbonTally_Platform_Processing_Architecture_Master_v1.md` (Master v1) — target HDPE/processing-provider architecture
- Repository schema: `supabase/migrations/00000000000000_init_schema.sql`, RC1/RC2 RLS, `backend/auth.py`

**Consistency rule applied:** no existing DECIDED ADR is contradicted. PROVISIONALLY DECIDED
dependencies (ADR-V3-003 Work Item, ADR-V3-006 SLA, ADR-V3-010 RLS) are identified.

---

## 1. Executive Summary

CarbonTally V3 must support **multiple independent Human Data Processing Entities**
(processing companies contracted to perform human data-processing work), alongside
CarbonTally's **own internal processing operation**, with full entity-level isolation,
management, assignment, SLA/KPI, audit and lifecycle control.

**Current state (traced, not assumed):** the repository has **no processing-entity
concept at all**. `organizations` is a **customer tenant** table (60+ customer/billing/
compliance columns); `staff_profiles` is an **internal-only staff** model; Babui exists only
as `raw_user_meta_data.company_name` metadata. There is no `entity_id` anywhere, no
entity-level RLS, and no entity capacity/SLA. The work-management mechanics V3 needs
(`manual_review_queue` work items, `upload_batches`, `review_assignment_history`,
`queue_settings`, `sla_*`, `staff_workload`) already exist — **only the entity dimension is
missing** (Queue Audit §10).

**Options evaluated:** A) reuse `organizations` with an `org_type` discriminator;
B) dedicated `processing_entities` table; C) parent organization + processing entity
relationship; D) any other repository-supported architecture.

**Recommendation: OPTION B — dedicated `processing_entities` table** (V3 IA H1-a / V3M-1),
with:
- `processing_entities` as a first-class table (no company name hard-coded; Babui is data).
- `staff_profiles` **reused** as the single worker table, extended with a **nullable
  `entity_id`** (`NULL` = CarbonTally internal worker; set = entity worker) — no second
  worker table.
- Work items (`manual_review_queue`) and batches (`upload_batches`) gain a **nullable
  `entity_id`** — entity ownership is recorded **on the atomic work item** (and optionally
  at batch level for entity-allocation).
- A new RLS helper **`is_entity_member(entity_id)`** (deny-by-default; entity staff see only
  their own entity). CarbonTally internal staff retain cross-entity visibility via their
  existing staff role.
- **Customer org isolation is preserved untouched**: a Processing Entity sees only the
  specific work items/documents assigned to it — never the customer's organization.

**Why Option B:** the entity is a *first-class business object* (a contracted processing
supplier), not a customer; `organizations` is semantically a customer tenant and reusing it
(Option A) conflates the two roles (task §4 critical distinction), pollutes RLS
(`is_org_member` semantics), and forces entity staff into customer `organization_members`
role checks. Option B is additive, deny-by-default, future-scalable (adding Entity N is a
data operation), and matches the Master v1 target architecture. Migration complexity is
**Medium** (V3M-1) vs **Low–Medium** (V3M-2 Option A) — the additional cost buys correct
isolation semantics.

**Recommended ADR-V3-001 decision text and remaining open questions are in §23–§24.**

---
## 2. Current Architecture

### 2.1 Trace of the relevant structures (from `init_schema.sql`, RC1/RC2, `backend/auth.py`)

| Concept | Table/Mechanism | Verified facts | Verdict |
|---|---|---|---|
| Customer tenant | `organizations` | **Customer tenant root**: 60+ columns — name, subscription_status/tier, billing, VAT, SECR/ESRS/ISSB flags, financial_year_end, SIC/NAICS/NACE, reporting standards. **No type discriminator.** | **Customer-only semantics.** Reusing as entity host mixes roles. |
| Org membership | `organization_members` | `organization_id`, `user_id`, `role CHECK IN ('owner','admin','member','viewer')`, `is_active` | Customer-role vocabulary only. |
| User | `users` | auth.users mirror; `user_type` free text; `is_active` | Identity anchor. |
| Staff | `staff_profiles` | `user_id`, `first_name/last_name/email`, `role_id → staff_roles`, `role` (legacy text), `skills JSONB`, `max_concurrent_tasks`, `is_active`, `permissions` | **Internal CarbonTally staff only.** No org/entity FK. |
| Staff roles | `staff_roles` (+ legacy `roles`) | `name`, `permissions JSONB`, `is_active` | Internal RBAC vocabulary. |
| Consultant | `consultant_profiles` / `consultant_clients` / `consultant_firm_members` | Firm + client-grant + members (`client_access UUID[]`, `role`, `permissions`) | **Separate** consultant axis — distinct from entities. |
| Processing entity | — | **None exists.** Babui = `auth.users.raw_user_meta_data.company_name` (verified in backup dump). | **The gap.** |
| Work items | `manual_review_queue` | Atomic human work: `organization_id`, `batch_id`, `assigned_to/by`, `priority_score`, `sla_deadline/sla_breached`, `escalation_level`, `data_entry JSONB`, `review_time_seconds` | Active canonical surface (ADR-V3-003). |
| Batch | `upload_batches` | `organization_id`, `total_files/processed_files`, `status`, `batch_type`, `manual_extraction_batch_id` | Grouping anchor (ADR-V3-012). |
| Assignment history | `review_assignment_history` | `review_id`, `assigned_by/to`, `previous_assigned_to`, `action`, `note` | Active attribution (ADR-V3-005). |
| SLA | `sla_definitions`, `sla_compliance`, `business_hours`, per-item `sla_deadline` | Config + records + working hours | Reusable (ADR-V3-006). |
| Workload/capacity | `staff_workload`, `staff_performance`, `staff_daily_performance`, `team_performance`, `dashboard_metrics` | Per-staff + team metrics | Reusable; **entity capacity missing**. |
| Escalation | `manual_review_queue.escalation_level`, `customer_verifications.is_escalated` | Item + customer escalation | Reusable. |
| Queue config | `queue_settings` (key/value JSONB), `system_settings` | auto_assign, max_reviews, sla_hours, escalation_hours, priority_weights | Reusable. |
| Customer comms | `conversations`/`conversation_participants`/`messages`/`notifications` | org-scoped chat | **Customer ↔ Customer Service** channel. |
| RLS helpers | `is_org_member()`, `is_org_active()`, `is_org_admin_or_owner()`, `is_org_consultant()` | org-membership based (RC1/RC2) | **No entity helper.** |
| Tenant RLS | `*_tenant_select/insert/update/delete` | org-gated via `is_org_member` (+`is_org_consultant` on SELECT) | Customer isolation solid. |
| Technical queues | `document_processing_queue`, `report_generation_queue`, dormant `processing_queue` family | state machines / output store | Outside entity decision (ADR-V3-004). |

### 2.2 How CarbonTally staff are currently represented

`backend/auth.py` (v2.1 + legacy) builds `AuthUser` by checking (1) `staff_profiles`
(`is_staff=True`, role/permissions/skills/accuracy_rate) and (2) `organization_members`
(`is_org_member=True`, org role). Staff are **internal and org-unbounded** — a staff user can
access any organization (see `require_org_access`: `if current_user.is_staff: return
current_user`). There is **no entity affiliation on staff**.

### 2.3 Can the current organization model safely represent Processing Entities?

**Not without a discriminator, and not cleanly even with one.**
- `organizations` is a customer tenant (billing/subscription/compliance semantics).
  A Processing Entity is a **contracted processing supplier** — none of those customer
  columns apply.
- `organization_members.role` CHECK is the customer vocabulary
  (`owner/admin/member/viewer`); entity roles (Manager/Supervisor/Validator/Worker) are a
  different vocabulary.
- `is_org_member()` would then mean "customer-org member OR entity member" — the same helper
  serving two tenant kinds weakens the boundary the RLS is meant to enforce.
- Work items carry `organization_id` = **customer** org; an entity needs its own dimension
  (`entity_id`), which `organizations` reuse does not provide per-row without ambiguity.

**Conclusion:** the current organization model can represent **customers** safely; it cannot
represent **Processing Entities** safely without a distinct object.

---

## 3. Business Requirement

V3 must support (Master v1 §7–§10, §16–§19; task §1):

- CarbonTally's own internal processing operation (staff-based, today).
- **Multiple external Human Data Processing Entities** (contract processors), added/removed
  over time without code deployment.
- Entity-level: users, roles, dashboards, workload, assignment, SLA/KPI, performance,
  issues, audit — independent per entity.
- Entity lifecycle: ACTIVE / SUSPENDED / REMEDIATION / TERMINATED with work, historical
  records and audit preserved.
- **Entity isolation** (Entity A ⊄ Entity B work; no cross-entity, no unrelated customers,
  no CarbonTally administrative data).
- Customer communication **only via CarbonTally Customer Service** — entities never speak to
  customers directly (Master v1 §15, §33, §45).
- Multi-entity allocation: 500 docs split across Entities A–D + CarbonTally internal (100
  each); worker unavailability → partial completion (30/70) reassignment with **attribution
  preserved** (Master v1 §25–§26, Queue Audit §10).

---
## 4. Architectural Options

| Option | Description | Basis in evidence |
|---|---|---|
| **A** | Reuse `organizations` with an organization/entity type discriminator (`org_type` VARCHAR + CHECK, backfill existing orgs to `'customer'`). Entity staff = `organization_members` rows on the entity-typed org; reuse `is_org_member()` RLS. | V3 IA §8 V3M-2 (H1-b); V3 IA §27 H1-b |
| **B** | Dedicated **`processing_entities`** first-class table (contract metadata, lifecycle status) + nullable `entity_id` on `staff_profiles` / `manual_review_queue` / `upload_batches` (+ optional other work tables) + new `is_entity_member()` RLS (deny-by-default). | V3 IA §8 V3M-1 (H1-a); V3 IA §27 H1-a; Queue Audit §10, §14–§17; Master v1 §7–§10 |
| **C** | Parent `organizations` row + child `processing_entities` referencing the parent (CarbonTally-as-parent). | No direct repository support; evaluated for completeness |
| **D** | Any other architecture supported by repository evidence. | Evaluated — see §8 |

The V3 IA records exactly two viable tenant models (H1-a, H1-b) plus "no entity concept"
today. Option C and D are evaluated against repository evidence, not invented for
completeness.

---

## 5. Option A Analysis

**Reuse `organizations` + `org_type` discriminator (V3M-2 / H1-b).**

**What it is.** Add `organizations.org_type VARCHAR CHECK (org_type IN ('customer','entity'))`
(default `'customer'`); an entity is an `organizations` row with `org_type='entity'`; entity
users are `organization_members` on that row; existing `is_org_member()` RLS gates both kinds.

**Why it appears attractive.** Minimal schema delta (one column + CHECK); reuses the entire
tenant RLS machinery (`is_org_member`/`is_org_consultant`, `*_tenant_*` policies); existing
org-scoped routes continue to work; migration risk **Low–Medium** (V3M-2).

**Why it fails the critical distinction (task §4).** A Processing Entity and a Customer
Organization are **different business roles**:
- `organizations` is a **customer tenant**: subscription_tier, trial dates, billing_address,
  vat_region, SECR/ESRS/ISSB flags, financial_year_end, reporting_standard, SIC/NAICS/NACE.
  None of these apply to a processing supplier; they actively mis-describe one.
- `organization_members.role` CHECK = `owner/admin/member/viewer` (customer vocabulary).
  Entity roles — Manager, Supervisor, Validator, Worker — are a different set. Forcing entity
  staff into `organization_members` either pollutes the customer role CHECK or duplicates the
  role concept.
- **RLS ambiguity**: `is_org_member()` would return TRUE for both "member of customer org"
  and "member of entity org". Every existing org-gated policy (`manual_review_queue`,
  `upload_batches`, `customer_documents`, `emissions_logs`, …) would then admit entity staff
  **unless each policy is rewritten with an `org_type` clause**. That is not a small change —
  it is a wide RLS surface with a **high leak risk** if one policy is missed. The CF Audit
  rejected exactly this pattern for customer factors (CF Audit §10 Option A: conditional
  policies on a shared table = "high leak risk").
- **Worker/queue privacy**: `manual_review_queue` is org-readable; making entity staff org
  members would expose the customer's queue rows to the entity under `is_org_member` unless
  every policy is split. Worker-level `assigned_to` privacy is already application-level only
  (Queue Audit §15) — Option A would not improve it.

**Multi-entity test (§5).** A single customer batch of 500 docs split across 4 entities +
CarbonTally: work items carry `organization_id` = customer; an entity-typed org cannot be
both the customer-owner and the processor of the same rows without an extra `processor_id`
dimension anyway. Option A only relabels the row host; it does not add the **entity ownership
dimension** on work items. The split still requires new columns — so Option A does **not**
avoid the schema work.

**Verdict:** Option A is the *cheapest-looking* but semantically conflates Customer and
Processing Entity, requires rewriting every org policy to be type-aware, and does not deliver
entity ownership on work items. **Rejected** (see §8 and comparison matrix).

---
## 6. Option B Analysis

**Dedicated `processing_entities` table (V3M-1 / H1-a) + nullable entity FK on staff and
work tables + `is_entity_member()` RLS.**

**What it is.**
- `processing_entities`: first-class table — `name`, contract metadata (legal entity, country,
  contract status, effective/termination dates, service level), **lifecycle status**
  (ACTIVE/SUSPENDED/REMEDIATION/TERMINATED as data values — no new enum type required),
  `is_active`, timestamps, `metadata JSONB`. **No company name is hard-coded**; Babui is one
  data row.
- `staff_profiles.entity_id` **nullable UUID → processing_entities** — `NULL` = CarbonTally
  internal worker; set = entity worker. **No second worker table**; the internal staff model
  is preserved and entity workers are the same table scoped by entity.
- `manual_review_queue.entity_id` **nullable** — **entity ownership is recorded on the atomic
  work item** (per ADR-V3-003 canonical Work Item; Queue Audit §17 KEEP/EXTEND).
- `upload_batches.entity_id` **nullable** — batch-level entity allocation for the
  CarbonTally→entity handoff.
- New RLS helper `is_entity_member(entity_id)` — deny-by-default; TRUE only for users whose
  `staff_profiles.entity_id = p_entity`. Entity staff see only their entity's work.
- CarbonTally internal staff keep cross-entity visibility through their staff role (existing
  `is_staff` path in `auth.py`) — no duplicate RBAC (task §8).

**Why it fits current V2.1.** Additive nullable columns; all active work-management mechanics
are reused unchanged (ADR-V3-003, ADR-V3-005, ADR-V3-006). No existing table is renamed,
dropped or rewritten. Customer tenant RLS is **untouched** — `is_org_member()` keeps its
customer meaning.

**Why it fits V3.** Matches the first-class Processing Entity in Master v1 §7–§10; the
`NULL`-entity convention represents the **CarbonTally internal processing operation**
(logical "CarbonTally queue" = work items with `entity_id IS NULL`), so CarbonTally internal
and entity work share one Work Item model with a discriminating column.

**Multi-entity test (§5).** 500 docs → batch + 500 `manual_review_queue` rows, each with
`organization_id` (customer) and `entity_id` (A/B/C/D or NULL for CarbonTally). Entity
allocation is a data write. Worker A completes 30/100; unavailability → `/queue/reassign`
writes `review_assignment_history` (30 stay attributed to A; 70 → B/C); entity performance
rolls up from `staff_workload`/`staff_performance` **scoped by entity**. All mechanics already
exist (Queue Audit §10); only the entity column + RLS helper are new.

**Verdict:** Option B delivers the required isolation with the least conceptual confusion and
a deny-by-default RLS boundary. Migration **Medium** (V3M-1) — new table + nullable FKs,
backward-compatible. **Recommended.**

---

## 7. Option C Analysis

**Parent `organizations` row + child `processing_entities` referencing the parent
(CarbonTally-as-parent).**

Under this model `processing_entities.parent_organization_id → organizations.id` where the
parent is CarbonTally's own platform organization; every entity is a child of that parent.

**Evaluation against repository evidence:**
- No schema or doc describes a parent-org concept for processors. `organizations` has no
  self-referential parent FK; `consultant_clients` is the only existing "firm→client" grant
  pattern, and it is a consultant concept, not a processor one.
- The parent link adds **no isolation value**: it does not define who may work, what work,
  or which entity — it only records an ownership chain. The required boundaries (entity↔entity,
  entity↔customer) still need `entity_id` columns and entity RLS regardless.
- It complicates RLS (member-of-parent ≠ member-of-entity) and adds a mandatory FK to a
  parent row that has no functional role in the task's multi-entity scenario.
- "CarbonTally internal" is better modelled as `entity_id IS NULL` (Option B) than as a parent
  relationship.

**Verdict:** Option C is not supported by repository evidence and adds indirection without
delivering any of the required isolation. **Rejected.**

---

## 8. Option D Analysis

**Any other architecture supported by repository evidence.**

Candidates considered and rejected on evidence:
- **Consultant-style model** (clone `consultant_profiles`/`consultant_firm_members`/
  `consultant_clients` for processors): consultants are **customer-facing advisors** with
  client grants; processors are **worker-facing operational suppliers**. Different role,
  different isolation model, different work surface. Cloning the consultant pattern would
  create a parallel RBAC — contradicts ADR principle 2 (no duplicate infrastructure).
- **Extend `staff_profiles` only** (no `processing_entities` table, entity = a staff-role
  grouping): cannot represent entity contracts/lifecycle, no entity anchor for SLA/capacity/
  issues/performance, and no place for `is_entity_member` to bind. Rejected.
- **Global `entity_id` column on `organizations`** (a customer row points at its processor):
  conflates "which org owns the data" with "which entity processes it"; the customer
  relationship and the processing relationship are both needed on work items. Rejected.

**Verdict:** no separate Option D is justified. The repository supports exactly the
Option A/B/C spectrum; Option B is the recommended form.

---
## 9. Comparison Matrix

| Criterion | Option A (org_type) | Option B (processing_entities) | Option C (parent org) | Recommendation |
|---|---|---|---|---|
| Conceptual correctness (Customer ≠ Entity) | **Poor** — conflates two roles | **Excellent** — first-class entity | Poor — parent link adds nothing | **B** |
| Fits current V2.1 (additive, no rewrite) | Good (1 column) | Good (new table + nullable FKs) | Poor (new FK + no benefit) | **B** |
| RLS isolation (Entity A ⊄ Entity B) | Weak — needs every policy type-aware; leak risk | **Strong** — new `is_entity_member`, deny-by-default | Weak — parent membership ambiguous | **B** |
| Preserves customer org RLS untouched | No — org policies affected | **Yes** — `is_org_member` keeps customer meaning | Yes | **B** |
| Entity staff representation | Pollution of `organization_members` role CHECK | **Reuses `staff_profiles` + nullable entity_id** | Undefined | **B** |
| Work Item ownership | No entity dimension on items | **`entity_id` on atomic Work Item** | No | **B** |
| Assignment/attribution | Reuses history but ambiguity | **Reuses `review_assignment_history` scoped by entity** | Reuses but ambiguous | **B** |
| SLA/KPI/capacity | Entity SLA needs scope columns anyway | **Reuses sla_*/staff_workload with entity scope** | Same as A | **B** |
| Lifecycle | `org_type` + status on org | **Lifecycle status on processing_entities row** | On child | **B** |
| Migration complexity | Low–Medium (V3M-2) | Medium (V3M-1) | Low but worthless | **B** (cost justified) |
| Future scalability (Entity N) | Data op but semantics degrade | **Data op, clean** | Data op | **B** |
| Risk | High leak risk in RLS surface | Contained (new boundary) | Indirection | **B** |

**Conclusion:** Option B dominates on every criterion that matters; the only downside is
modestly higher migration effort (V3M-1 Medium vs V3M-2 Low–Medium), which buys correct
isolation semantics and zero disturbance to customer RLS.

---

## 10. RBAC Impact

**Critical distinction preserved (task §4):** Customer/Organization · Processing Entity ·
User · Entity Staff Member · Consultant · CarbonTally Internal Staff are **distinct
concepts** — never interchangeable.

| Concept | Representation (Option B) | RBAC surface |
|---|---|---|
| Customer / Organization | `organizations` + `organization_members` (unchanged) | Customer roles: owner/admin/member/viewer (`is_org_member`) |
| Processing Entity | `processing_entities` row | Entity membership via `staff_profiles.entity_id` |
| Entity Staff Member | `staff_profiles.entity_id` set | Entity-scoped roles (see below) |
| Consultant | `consultant_profiles`/`consultant_firm_members`/`consultant_clients` (unchanged) | Consultant grants (`client_access`) |
| CarbonTally Internal Staff | `staff_profiles.entity_id IS NULL` | Existing internal staff roles (`is_staff`) |

**Entity-scoped roles (conceptual — no roles created here).** Entity Admin, Entity Manager,
Supervisor, Validator, Worker (Master v1 §17, §19–§22) map onto the **existing
`staff_roles.permissions JSONB`** mechanism, but the permission check is evaluated **only when
`staff_profiles.entity_id = p_entity`**. The role vocabulary already exists as `staff_roles`
(name + permissions JSONB); the change is **scoping**, not a new RBAC system:
- CarbonTally internal staff with an operations role gain cross-entity visibility (Master v1
  §16 CarbonTally Operations Manager manages providers).
- Entity staff see **only their entity** — no other entity, no customer org, no CarbonTally
  admin data (Master v1 §19, §41).
- `backend/auth.py` `AuthUser` is extended with `entity_id` (from `staff_profiles`); the
  `is_staff` vs `is_org_member` paths are preserved, and a new `is_entity_member`/entity-role
  resolution is added. **No duplication of the RBAC system** (task §8: internal vs entity
  users distinguished without duplicating RBAC).

**Conceptual required changes (RBAC):** (1) `AuthUser.entity_id`; (2) entity-role check
helper (`require_entity_role(roles, entity_id)`); (3) entity admin management scope limited to
own entity; (4) CarbonTally Operations cross-entity role retained via internal staff role.

---

## 11. RLS Impact

Conceptual requirements (no RLS modified in this task):

| Boundary | Required behaviour | Mechanism |
|---|---|---|
| Entity A ⊄ Entity B | Entity staff never see another entity's work/users/queues/documents | New `is_entity_member(entity_id)` helper (deny-by-default) on entity-scoped columns |
| Entity ⊄ unrelated customers | Entity never sees customer org or other customers | Entity never becomes `organization_members`; customer tables keep `is_org_member` only |
| Entity ⊄ CarbonTally admin data | No access to `system_settings`, staff-role admin, audit admin, global factors | Existing deny-by-default / admin-only policies untouched |
| CarbonTally internal staff cross-entity | Authorized internal roles see all entities | Existing `is_staff` application path + service-role; policies grant internal roles explicitly (not via `is_org_member`) |
| Worker privacy within entity | Worker sees own assigned work, not entity-wide queue (application-level today; Queue Audit §15) | Entity-level RLS + route authorization; worker-scope RLS is a hardening option, not required for ADR-V3-001 |
| Service-role / background jobs | Must not bypass entity isolation | Backend scope checks mirror RLS (Master v1 §52) |

**Key point:** with Option B, **existing customer tenant RLS is not weakened and not
rewritten** — entity boundaries are a *new additive* policy surface. This satisfies ADR-V3-010
constraint "Must NOT weaken existing RLS". Option A would require rewriting the existing
tenant policies to be type-aware — the opposite.

---
## 12. Work Item Impact

Uses ADR-V3-003 (PROVISIONALLY DECIDED): canonical human Work Item + Logical Queues +
Technical State Machines.

**Minimum relationship:**
```
Processing Entity ──entity_id──▶ Work Item ──assigned_to──▶ Worker (staff_profiles)
     (upload_batches.entity_id)   (manual_review_queue row)   (entity_id = entity)
```

**Where entity ownership is recorded (no SQL designed):**
- **Atomic Work Item** (`manual_review_queue.entity_id`, nullable): the authoritative
  entity-ownership point. A Work Item belongs to exactly one entity (or CarbonTally when
  `entity_id IS NULL`).
- **Batch** (`upload_batches.entity_id`, nullable): CarbonTally→entity allocation handoff
  (CarbonTally Operations assigns batch→entity per Master v1 §37). Batch-level entity is a
  convenience/aggregation; the Work Item row is the source of truth for attribution.
- **Worker** (`staff_profiles.entity_id`, nullable): defines which entity a user belongs to;
  this scopes *who may claim/process* a Work Item.
- Entity ownership is **never** recorded on the customer `organizations` row — that stays the
  data owner; entity is a separate dimension.

**Logical queues** ("CarbonTally queue", "Entity A queue") become filtered views over the
canonical Work Item surface keyed on `entity_id` (ADR-V3-003). No new queue table.

**Consistency:** `entity_id` must be derivable from the assigned worker OR set explicitly at
allocation; the recommended invariant is **Work Item.entity_id = assigned worker's
staff_profiles.entity_id** when assigned, and `entity_id` set at allocation time when pending.
This keeps the 30/70 attribution test correct: a completed item retains its original
`entity_id` and assignment history regardless of later reassignment.

---

## 13. Assignment Impact

- **CarbonTally→Entity (batch/entity allocation):** CarbonTally Operations assigns a batch
  (or a subset of Work Items) to an entity — sets `upload_batches.entity_id` /
  `manual_review_queue.entity_id`. Records an audit event.
- **Entity→Worker (item assignment):** existing `POST /queue/assign` +
  `review_assignment_history` (ADR-V3-005) — unchanged mechanics, now scoped by entity:
  entity supervisors assign only within their entity.
- **Supervisor intervention:** `review_assignment_history` keeps attribution
  (assigned_by/to, previous_assigned_to, action, note). Entity supervisor = staff with
  Supervisor role and `entity_id = p_entity`.
- **Worker unavailable (30/70):** `POST /queue/reassign` writes a **new**
  `review_assignment_history` row (Master v1 §26 "create additional history, do not
  overwrite"); the original 30 completed items remain attributed to Worker A; the remaining
  70 go to Workers B/C. **No historical record is modified.**
- **Partial-work recovery:** in-progress saved state (`data_entry`/`manual_extraction_result`)
  is preserved for the new worker where supported (Master v1 §27); the technical dpq state
  machine is untouched (ADR-V3-004).
- **Provider replacement (entity-level):** a whole entity's outstanding Work Items can be
  reassigned to another entity by updating `entity_id` on the pending items + audit —
  the "Batch #1000 → Provider B" acceptance test (Master v1 §38) works without touching
  completed records/history.

---

## 14. SLA/KPI Impact

Reuses existing infrastructure (ADR-V3-006 — PROVISIONALLY DECIDED; Queue Audit §6, §13).

| Entity capability | Reused structure | Change required |
|---|---|---|
| Entity SLA (deadline, breach) | Per-item `sla_deadline`/`sla_breached` on Work Items + `sla_compliance` records | Scope reports by `entity_id`; SLA definitions per entity where contracts differ (extend `sla_definitions` with entity scope, conditional) |
| Entity capacity | `staff_workload` per worker | Aggregate per entity (sum of member workers) — **no new table** |
| Entity productivity/quality | `staff_performance`, `staff_daily_performance`, `team_performance` | Aggregate/group by entity via `staff_profiles.entity_id` |
| Entity KPIs (throughput, correction rate, QC pass) | `dashboard_metrics` pattern | Entity-scoped metrics rows |
| Escalation | `escalation_level` on Work Item; `customer_verifications.is_escalated` | Entity escalation → CarbonTally Operations (internal); customer escalation stays Customer Service |
| Warnings/remediation/suspension | Lifecycle status on `processing_entities` + metrics | Status-driven warnings derived from SLA/quality |

**No duplicate SLA/KPI/workload system is created** (ADR-V3-006 constraint). The entity
dimension is added as a scoping key over existing structures.

---
## 15. Configuration Impact

Existing configuration surface (Queue Audit §13) supports entity scoping without a new
config system:

| Config | Existing table | Entity use |
|---|---|---|
| Capacity / auto-assign / SLA hours / escalation hours / priority | `queue_settings` (key/value JSONB) | Entity-scoped setting keys (e.g. `entity_{id}.sla_hours`) or a scoped-settings row pattern |
| SLA rules | `sla_definitions` | Entity-scoped definitions (conditional) |
| Working hours | `business_hours` | Per-entity working-hours/timezone (entity contracts differ) |
| Notifications / workflow / QC sampling | `system_settings` / `queue_settings` / `qc_checklists` | Entity-scoped variants |

**Decision:** do **not** create a new configuration system. V3 IA §8 T5 records
"generic scoped-settings table" as *optional*; `queue_settings` key/value JSONB already
supports entity-scoped keys, so a new table is **not required** by evidence. Entity-specific
configuration becomes part of the V3 config-ownership decision (V3-008, deferred), not a new
architecture.

---

## 16. Lifecycle Impact

**Entity lifecycle states** (Master v1 §9, §39): PENDING/ONBOARDING · ACTIVE · SUSPENDED ·
REMEDIATION · OFFBOARDING · TERMINATED. The task requires ACTIVE / SUSPENDED / REMEDIATION /
TERMINATION / TERMINATED.

**Existing status infrastructure:** the repository models status as **VARCHAR + CHECK columns**
(e.g. `manual_review_queue.status`, `customer_documents.status`, `processing_queue.queue_status`)
and `is_active BOOLEAN` flags — **no Postgres enum type is used**. A `processing_entities`
status VARCHAR (+ `is_active`) therefore fits the established convention. **No enum is
created** (task §6).

**Behaviour on SUSPENDED / REMEDIATION / TERMINATED:**

| State | New work | Queued work | Assigned/in-progress | Completed/historical |
|---|---|---|---|---|
| ACTIVE | ✅ allowed | normal | normal | retained |
| SUSPENDED | ⛔ stopped (allocation blocked) | held (not claimable) | allowed to finish or reassigned | retained |
| REMEDIATION | ⛔ stopped until remediated | held | allowed to finish / QC focus | retained |
| TERMINATED | ⛔ never | **reassigned to another entity / CarbonTally internal** | **reassigned or completed then closed** | **retained + attributable** |

**Historical integrity rules (task §16; Master v1 §39–§40):**
- Completed work, audit history, issues, performance history and contract/KPI records are
  **preserved** after suspension/termination — no cascade delete.
- The entity row is **never deleted** while attribution is required; entity is marked inactive.
- Work reassignment on termination updates `entity_id` on pending items + audit — historical
  completed items keep their original `entity_id` and assignment history (30/70 test holds).
- Worker records similarly remain for attribution (Master v1 §40: "do not delete the worker
  record if historical attribution is required").

**Implementation boundary:** lifecycle *rules* (who may allocate to a suspended entity, when
reassignment is forced) are enforced at the application/service layer; the entity status
column is the data anchor. This is consistent with the existing pattern (status columns +
route-level enforcement).

---
## 17. Customer Isolation Impact

**Requirement (task §10):** A Processing Entity sees only the work it is authorized to
process. It must **never** gain unrestricted access to the customer's organization.

**Conceptual access boundary (Option B):**
```
CUSTOMER ORG  (organizations, organization_members, customer_documents, emissions…)
   ▲  accessible ONLY to customer members, consultants, and authorized CarbonTally staff
   │
   │  (customer never grants entity membership)
   ▼
WORK ITEMS    (manual_review_queue rows with organization_id + entity_id)
   ▲  entity sees ONLY rows where entity_id = its own AND it is assigned/authorized
   │
   ▼
DOCUMENT      (customer_documents.file_url — private Storage, controlled access,
                signed URLs; Master v1 §47–§48)
```

**Enforcement points (conceptual):**
1. **Entity is never an `organization_members` row** — entity staff can never pass
   `is_org_member()` for the customer org. Customer table RLS is untouched.
2. **Entity visibility is `entity_id`-scoped** — new `is_entity_member(entity_id)` gates the
   work surface (Work Items, batch). Entity staff read only their entity's work.
3. **Document access is granted per-assignment** — a worker receives a controlled viewer /
   signed URL for the specific document attached to an assigned Work Item; the entity never
   lists the customer's document store (Storage policies, Master v1 §47–§48).
4. **CarbonTally internal staff** retain authorized cross-entity and customer visibility per
   their role — but through the existing staff path, never by becoming entity members.

**Multi-tenant guard:** the two dimensions stay orthogonal — `organization_id` (who owns the
data) vs `entity_id` (who processes it). A Work Item carries both; entity RLS checks only the
latter plus assignment. This is exactly the "Customer ↔ Processing Entity" separation the
task requires.

---

## 18. Communication Impact

**Requirement (task §11; Master v1 §15, §33, §45–§46):** Customers communicate only with
CarbonTally Customer Service. Customers do **not** directly communicate with Processing
Entities.

**Architecture boundary:**
```
CUSTOMER ──(conversations/messages, org-scoped)──▶ CUSTOMER SERVICE      [existing channel]
CUSTOMER ──(never)──▶ Processing Entity
CARBONTALLY OPERATIONS ──(internal provider channel)──▶ ENTITY MANAGER    [separate channel]
ENTITY MANAGER ──(internal)──▶ SUPERVISOR ──▶ WORKER                        [entity-internal]
```

**How it is enforced conceptually:**
- **Customer channel** = existing `conversations`/`conversation_participants`/`messages`
  (org-scoped, customer + Customer Service). Unchanged.
- **Entity internal channel** = separate conversations (entity-scoped), or entity-internal
  notes; **never customer-visible**. Master v1 §45–§46 requires provider↔CarbonTally and
  provider-internal communication to be distinct from customer chat.
- **Issues** (ADR-V3-009, now DECIDED — first-class Issue) must respect the boundary:
  - Customer-facing issues → Customer Service (org-scoped, customer-visible status).
  - Entity/operational issues → CarbonTally Operations ↔ Entity (entity-scoped, internal).
  - The Issue carries entity context where applicable (ADR-V3-009), but an entity's issue
    surface is entity-scoped and never customer-visible.
- **Notifications** keep recipient-type separation (`notifications.recipient_type` exists
  today) — customer notifications vs entity staff notifications are distinct.

**Design rule:** no message/conversation row may be visible to both a customer and an entity
staff member unless it is a CarbonTally-moderated operational thread. The recommended pattern
is separate conversation surfaces per boundary (customer / CT-entity / entity-internal) rather
than one chat with mixed participants.

---
## 19. Migration Impact

**Recommended path = V3M-1 (Option B), conditional on ADR-V3-001 (H1-a) being confirmed.**
No migration is created in this task.

| Element | Impact |
|---|---|
| New table `processing_entities` | New; no data migration (V3 IA §8 V3M-1: "none (new table)") |
| `staff_profiles.entity_id` nullable UUID + FK | Additive; existing staff rows keep `NULL` = CarbonTally internal |
| `manual_review_queue.entity_id` nullable + FK | Additive; existing rows `NULL` |
| `upload_batches.entity_id` nullable + FK | Additive |
| Indexes | `entity_id` indexes on the three tables (V3M-1) |
| Constraints | FK `ON DELETE RESTRICT/SET NULL` — entity not deletable while attributed work exists (supports lifecycle integrity) |
| RLS | New `is_entity_member()` helper + entity policies (deny-by-default) — additive, no existing policy rewritten |
| Backward compatibility | Yes — all changes nullable/additive (V3 IA §8 V3M-1 "yes") |
| Data migration | None for existing data; no backfill required (entity is new) |
| Risk | Medium (V3M-1) — new table + FK/index + new policy surface |

**Vs Option A (V3M-2):** backfills existing orgs to `'customer'` (a data migration touching
every existing tenant) and rewrites org RLS semantics — a wider blast radius on **live
customer data**, despite the lower raw DDL count.

**Do NOT create a migration now.** Per V3 IA §29 and ADR-V3-001 (OPEN), the confirmed
decision becomes the migration design input; this analysis only records the consequence.

---

## 20. Scalability Impact

**Requirement (task §17):** Entity A…Entity N without schema redesign; adding an entity is a
**data/configuration operation**, not a code deployment.

**How Option B satisfies this:**
- Adding Entity N = one `processing_entities` row + entity admin user(s) with
  `staff_profiles.entity_id = N`. No DDL, no code change.
- Entity removal = lifecycle transition to TERMINATED (data), not schema change.
- Entity-scoped settings = keys under `queue_settings`/config — no schema change.
- Logical queues keyed on `entity_id` are parameterised queries — N entities add no schema.
- Entity staff are rows in the existing `staff_profiles`/`staff_roles` model — scaling users
  does not scale tables.
- RLS helpers (`is_entity_member(entity_id)`) are data-parameterised — policy count stays
  constant as N grows.

**Boundary:** extremely large N (hundreds of entities) would warrant an index/caching review,
not a schema redesign — the same property as today's customer tenants. No new architectural
pattern is required by the task's Entity A–D scenario.

---
## 21. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Option B migration (V3M-1) touches `manual_review_queue`/`upload_batches` — active tables | Medium | Medium | Nullable additive columns; zero-copy for existing rows; verify RLS after |
| 2 | Entity RLS gap if `is_entity_member()` not applied to every entity-scoped surface | Medium | **High** (cross-entity leak) | Deny-by-default default; policy manifest test; only entity-scoped columns admit it |
| 3 | Legacy permissive RLS policies on `manual_review_queue`/`upload_batches` coexist (Queue Audit §15) | Medium | High | Resolve policy union as part of the RLS pass (ADR-V3-010 INVESTIGATE); do not rely on entity policies alone |
| 4 | Worker-level `assigned_to` privacy is application-level today (Queue Audit §15) | High | Medium | Entity-scope RLS is the V3 baseline; worker-scope hardening optional later |
| 5 | Service-role/background jobs bypass RLS (Master v1 §52) | Medium | High | Backend scope checks mirror RLS; entity checks in services, not just policies |
| 6 | "CarbonTally internal = NULL entity_id" convention accidentally treats unassigned work as internal | Low | Medium | Explicit allocation writes `entity_id` at batch→entity handoff; NULL only after explicit CarbonTally assignment |
| 7 | Suspension/termination rules not enforced at service layer | Medium | Medium | Lifecycle state machine in service; allocation guard rejects suspended/terminated entities |
| 8 | Issues (ADR-V3-009) entity scope drifts from this entity model | Low | Medium | Issue entity context follows `entity_id` convention; issue surface entity-scoped |
| 9 | Option A being chosen later would rewrite org RLS semantics (regression risk) | — | High | This analysis documents the rationale; decision should be made once |

---

## 22. Recommended Architecture

**Recommendation: OPTION B — dedicated `processing_entities` table** (V3 IA H1-a / V3M-1),
expressed as a stable architecture summary:

```
CUSTOMER / ORGANIZATION  (existing — untouched)
        │  uploads 500 documents → upload_batches (organization_id)
        ▼
BATCH  (upload_batches)  ── CarbonTally Operations assigns entity (entity_id, nullable)
        │
        ▼
WORK ITEM  (manual_review_queue: organization_id = customer, entity_id = A|B|C|D|NULL)
        │        ▲
        │        │ assigned_to → staff_profiles (entity_id matches work item entity_id)
        ▼        │
PROCESSING ENTITY (processing_entities row: lifecycle status, contract metadata, is_active)
        │
        ├── Entity staff (staff_profiles.entity_id = entity)
        ├── Logical Queue ("Entity A queue" = work items where entity_id = A)
        ├── Assignment (review_assignment_history) — attribution preserved
        ├── SLA/KPI (sla_*, staff_workload, staff_performance — entity-scoped views)
        ├── Issues (first-class, entity context; ADR-V3-009)
        ├── Audit (audit_trail/domain_events + actor/entity scope)
        └── Lifecycle (ACTIVE/SUSPENDED/REMEDIATION/TERMINATED — data values)
CARBONTALLY INTERNAL  =  staff_profiles.entity_id IS NULL  (logical "CarbonTally queue")
```

**Why it fits V2.1:** purely additive; reuses every active work-management structure.
**Why it fits V3:** first-class entity per Master v1; deny-by-default isolation; Entity N is
data. **RLS:** additive `is_entity_member` — no existing policy weakened. **RBAC:** scopes
existing `staff_roles`/`staff_profiles`; no duplicate system. **Work Item:** `entity_id` on
the atomic item. **Assignment:** existing history reused. **SLA/KPI:** entity-scoped views
over existing structures. **Lifecycle:** status VARCHAR + service enforcement.
**Migration:** V3M-1 Medium. **Scalability:** data-only. **Risks:** §21.

---
## 23. ADR-V3-001 Proposed Decision

*Proposed decision text for the product/architecture owner to confirm and record in the
Architectural Decisions Register (this task does NOT update the register):*

> **ADR-V3-001 — Processing Entity Architecture: DECIDED (Option B).**
> CarbonTally V3 introduces a **dedicated `processing_entities` table** as the first-class
> representation of Human Data Processing Entities (no company name hard-coded; entities are
> data rows with lifecycle status ACTIVE / SUSPENDED / REMEDIATION / TERMINATED and contract
> metadata). CarbonTally's internal processing operation is represented by
> `staff_profiles.entity_id IS NULL` (logical "CarbonTally queue"). Entity ownership is
> recorded on the atomic Work Item (`manual_review_queue.entity_id`, nullable) and at batch
> level (`upload_batches.entity_id`, nullable). Entity workers reuse `staff_profiles` with a
> nullable `entity_id`; entity roles reuse the existing `staff_roles` mechanism scoped by
> entity. Isolation is enforced by a new deny-by-default `is_entity_member(entity_id)` RLS
> helper; existing customer organization RLS is unchanged. Customer communication remains
> exclusively via CarbonTally Customer Service; entity communication is a separate internal
> surface. Implementation (DB migration V3M-1, RLS, backend, API) proceeds only after this
> decision is recorded and the ADR-V3-001 OPEN blocker is cleared.

**Constraints preserved:** no enum type (VARCHAR status); no new RBAC/config system; no
deletion of historical or attributed data; no weakening of customer RLS; no second worker
table; no fifth queue.

---

## 24. Remaining Open Questions

Questions that must be resolved at decision/implementation time (not invented here):

| # | Open question | Why it matters | Source |
|---|---|---|---|
| 1 | Entity contract metadata scope (minimal vs contractual fields) | `processing_entities` column set; can be minimal at first (V3-008) | V3 IA §27 H13; Master v1 §10 |
| 2 | `entity_id` on other work tables (dpq, manual_extraction, report_generation_queue) | Whether technical state machines also carry entity scope | Queue Audit §17 (dpq KEEP); ADR-V3-004 |
| 3 | Entity-level SLA definitions (per-entity `sla_definitions` vs entity-scoped keys in `queue_settings`) | Contract SLA variance | ADR-V3-006; Queue Audit §13 |
| 4 | Entity capacity model (aggregate of `staff_workload` vs explicit entity capacity row) | Auto-assignment + allocation inputs | ADR-V3-007; Master v1 §36 |
| 5 | CarbonTally internal representation: `entity_id IS NULL` vs a reserved "CarbonTally" entity row | Affects RLS/logical queue naming | This analysis §22 (recommends NULL) |
| 6 | Entity onboarding/offboarding workflow states (PENDING/ONBOARDING/OFFBOARDING) and who transitions them | Lifecycle authority | Master v1 §9, §39 |
| 7 | Whether `is_entity_member` also covers entity admins for user management of their entity | Entity-admin scope | This analysis §10 |
| 8 | Issue entity context: entity-scoped issue surface vs issues owned by CarbonTally with entity reference | ADR-V3-009 interaction | ADR-V3-009; §18 |
| 9 | Storage policy shape for per-assignment document access (signed URLs vs entity bucket) | Data minimisation | Master v1 §47–§48 |
| 10 | Migration sequencing (V3M-1 vs other V3 conditional migrations) | Dependency order | V3 IA §8, §29 |

---
## 25. Verification

1. File exists at `docs/audit/CarbonTally_V3_Processing_Entity_Architecture_Decision_Analysis.md` — **yes**.
2. All required sections (§1–§24) present — **yes**.
3. All four options evaluated; Option B recommended with evidence — **yes**.
4. No existing DECIDED ADR contradicted; PROVISIONALLY DECIDED dependencies identified
   (ADR-V3-003/005/006/010) — **yes**.
5. No source code, database, migration, RLS, Storage, API, frontend or test files modified — **yes**.
6. No migration created; no table/enum/role/model created — **yes**.
7. The Architectural Decisions Register was **not** updated — **yes**.
8. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049) — **yes**.

*End of decision analysis. READ-ONLY — no implementation performed.*











