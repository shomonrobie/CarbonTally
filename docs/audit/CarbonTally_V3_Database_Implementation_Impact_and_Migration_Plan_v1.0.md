# CarbonTally V3 Database Implementation Impact & Migration Plan

**Status:** READ-ONLY DATABASE IMPACT ASSESSMENT — PLANNING ONLY. NO IMPLEMENTATION.
**Date:** 2026-08-10 · Branch: `main`
**Mode:** Read-only. No migration, schema, RLS, backend, API, frontend, seed-data or test
changes were made. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

**Authoritative sources cross-referenced:**
- `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` (ADR-V3-001…016)
- `docs/architecture/CarbonTally_V3_Architecture_Specification_v1.0.md` (§1–§33)
- `docs/audit/CarbonTally_V3_Customer_Factors_Impact_Analysis.md`
- `docs/audit/CarbonTally_V3_Queue_Architecture_Audit.md`
- `docs/audit/CarbonTally_V3_Processing_Entity_Architecture_Decision_Analysis.md`
- `docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md` (V3 IA §8, §27, §29)

**Current-state source of truth (repository):**
- `supabase/migrations/00000000000000_init_schema.sql` (baseline schema)
- `supabase/migrations/20260807000000…20260807070000` (M1–M8)
- `database/rc1/004_rc1_rls.sql`, `database/rc2/004_rc2_rls.sql` (RLS storeys)
- `tools/carbon_data_factory/schema.txt`, `supabase/migrations/schema_snapshot.sql`

---

## 1. Executive Summary

The approved V3 architecture (register + specification) requires **three genuinely new
database domains** and **no change to the factor baseline**:

| Domain | New structure | Status | Migration |
|---|---|---|---|
| Processing Entities | `processing_entities` table + `staff_profiles.entity_id` + entity FK on work tables | ADR-V3-001 **DECIDED** — implementation pending | V3M-1, V3M-2 |
| Issues | First-class `issues` model | ADR-V3-009 **DECIDED** — implementation pending (design before migration) | V3M-5 |
| Customer-owned factors | `customer_factors` table + snapshot-FK relaxation | ADR-V3-002 **PROVISIONALLY DECIDED** — blocked by 4 OPEN SUB-DECISIONS | V3M-3 |

Everything else in the V3 operational model is achieved by **extending or reusing the
existing active structures** (`manual_review_queue`, `upload_batches`,
`review_assignment_history`, `customer_verifications`, `queue_settings`, `sla_*`,
`staff_workload`, `calculation_snapshots`, `factor_aliases`, `domain_events`) — never by
duplicating them (Principle 2, register §3).

**Key conclusions:**
1. **No factor data migration.** The 7,049-factor baseline (`emission_factors`:
   DEFRA/GB 7,029 + SEAI/IE 20) is untouched and is not migrated by any V3 change.
2. **The only unavoidable existing-schema change** is the `calculation_snapshots.factor_id`
   NOT NULL FK → `emission_factors` relaxation required for customer-factor provenance
   (ADR-V3-014; OPEN SUB-DECISION D-cf-2).
3. **All V3M migrations are additive and backward-compatible**; no table is dropped; dormant
   structures are retired (archived/left inert) only after a dependency chain completes
   (ADR-V3-016).
4. **The migration is CONDITIONAL** on the open decisions (V3 IA §29): the entity table
   (V3M-1/V3M-2) is unblocked by ADR-V3-001 (DECIDED), the issues table (V3M-5) by
   ADR-V3-009 (DECIDED), and the customer-factors table (V3M-3) by the 4 OPEN SUB-DECISIONS.
5. No migration file is created in this document.

---

## 2. Current V2.1 Database Baseline

Verified from the repository migrations (init schema + M1–M8 + RC1/RC2):

| Area | Current structure | Verified |
|---|---|---|
| Factor reference | `emission_factors` (7,049 rows; 7,029 DEFRA/GB + 20 SEAI/IE batch-linked); natural key `(reporting_year, activity_type, country, unit, scope)`; `CHECK (country IN ('GB','IE'))`; `import_batch_id` FK → `import_batches` (M2) | ✅ |
| Import provenance | `import_batches` (M1): provider_key, provider_version, source_checksum, status, is_active, rolled_back_from | ✅ |
| Calculation provenance | `calculation_snapshots` (M3): **factor_id NOT NULL FK → emission_factors ON DELETE RESTRICT**; import_batch_id FK; content_hash; append-only | ✅ |
| Emissions | `emissions_logs` (org-scoped; `snapshot_id` FK → calculation_snapshots, M4) | ✅ |
| Events | `domain_events` (M5): append-only, correlation_id, aggregate (type,id) | ✅ |
| Aliases | `factor_aliases` (M6): org-scoped/global, unique `(COALESCE(org, 0000…), alias_text)` | ✅ |
| DPQ workflow | `document_processing_queue.workflow_error_count`, `workflow_next_retry_at` (M7) | ✅ |
| New-table RLS | M8: import_batches/domain_events deny-by-default; calc_snapshots select-own; factor_aliases select/insert/delete-own (via `is_org_member`) | ✅ |
| Tenancy | `organizations` (tenant root, 60+ columns, no entity dimension), `organization_members` (owner/admin/member/viewer), `users` | ✅ |
| Staff | `staff_profiles` (user_id, role_id → `staff_roles`, is_active, skills JSONB, max_concurrent_tasks — **no entity_id**), `staff_roles` (name, permissions JSONB) | ✅ |
| Human work | `manual_review_queue` (status, assigned_to/by, priority+score, sla_deadline, sla_breached, escalation_level, batch_id, data_entry, customer_* fields) — **active** | ✅ |
| Batches | `upload_batches` (batch grouping anchor; batch_type; manual_extraction_requested) — **active** | ✅ |
| Attribution | `review_assignment_history` (review_id, assigned_by/to, previous_assigned_to, action, note) — **active** | ✅ |
| Technical queues | `document_processing_queue` (state machine; no active producer), `report_generation_queue` (output store) | ✅ |
| Dormant legacy | `processing_queue`/`processing_assignments`/`processing_steps`, `reassignment_history`, `approval_requests`/`approval_decisions`, `qc_checks`/`qc_errors` (FK-bound to `processing_assignments`), `manual_extraction_batches`/`manual_extraction_items` | ✅ |
| Approval | `customer_verifications` (org-scoped; submitted/verified/rejected/revision_requested; is_escalated) — **active**; `customer_review_log` | ✅ |
| Communication | `conversations`/`conversation_participants`/`messages`/`notifications` (org-scoped chat) | ✅ |
| Config/SLA | `queue_settings` (key/value JSONB), `sla_definitions`, `sla_compliance`, `business_hours`, `staff_workload`, `staff_performance`, `dashboard_metrics` | ✅ |
| Feedback | `user_feedback` (type, title, description, severity, status, assigned_to) — legacy feedback, not an Issue model | ✅ |
| RLS helpers | `is_org_member`, `is_org_active`, `is_org_admin_or_owner`, `is_org_consultant` (RC2, SECURITY DEFINER) | ✅ |
| RLS patterns | `*_tenant_select/insert/update/delete` on org-bearing tables (RC1/RC2); reference `authenticated_read`; users self; org_members self/admin; consultant firm-tenanted | ✅ |
| RLS gaps | staff tables **deny-by-default for authenticated** (RC2 §8: staff RBAC "v1.1 concern"); legacy permissive policies flagged **INVESTIGATE** (Queue Audit §15–§16) | ✅ |
| New tables | **`processing_entities`/`issues`/`customer_factors` do NOT exist** anywhere in the schema | ✅ |

**Baseline conclusions:** the org/tenant RLS model is solid; staff RBAC is deny-by-default;
three new domains are required; the factor baseline is immutable.

---

## 3. V3 Database Change Summary

| V3M | Purpose | Type | Tables | Unblocked by | Status |
|---|---|---|---|---|---|
| **V3M-1** | Processing Entity foundation | ADD | `processing_entities` (NEW); `staff_profiles.entity_id` (EXTEND) | ADR-V3-001 (DECIDED) | CONDITIONAL — ready for design |
| **V3M-2** | Entity relationship on work items | ADD | `entity_id` on `manual_review_queue`, `upload_batches` (EXTEND) | ADR-V3-001 → V3M-1 | CONDITIONAL |
| **V3M-3** | Customer factors + snapshot FK | ADD | `customer_factors` (NEW); `calculation_snapshots.factor_id` FK relaxation | ADR-V3-002 OPEN SUB-DECISIONS (D-cf-2/3/5, R3) | CONDITIONAL — blocked |
| **V3M-5** | First-class Issues | ADD | `issues` (NEW) + RLS | ADR-V3-009 (DECIDED); design first | CONDITIONAL — design pending |
| **V3M-4** | Deferred-provider widening (T3) | EXTEND | `emission_factors` country CHECK + natural key | H3 decision | CONDITIONAL — DEFERRED |

**No-change domains:** `emission_factors` (7,049 immutable), `emissions_logs`,
`organizations`/`organization_members`/`users`, `factor_aliases`, `import_batches`,
`domain_events`, `conversations`, `customer_verifications`, `queue_settings`, `sla_*`,
`business_hours`, `staff_workload`, `report_generation_queue`, `document_processing_queue`.
**Retire-later domains:** `processing_queue` family, `reassignment_history`,
`approval_requests`/`approval_decisions`, `manual_extraction_batches`/`items` (ADR-V3-016
chain — never deleted before re-pointing).

---

## 4. Processing Entity Changes

**Why:** ADR-V3-001 (DECIDED — Option B): Processing Entities are a first-class domain,
never represented by `organizations`. Multi-entity allocation (500-document scenario) and
entity isolation require the dedicated table.

**Approved convention (register §5; spec §7.1):**
```
staff_profiles.entity_id IS NULL      = CarbonTally internal processing
staff_profiles.entity_id = <pe.id>    = Processing Entity staff
```

### 4.1 `processing_entities` (NEW — V3M-1)

| Aspect | Detail |
|---|---|
| Existing structure | none |
| Required V3 structure | `processing_entities`: id UUID PK, name, legal/contract metadata (exact commercial fields deferred — Q1), lifecycle status VARCHAR+CHECK (active / remediation-suspended / terminated — Q6; exact values finalized in design), timestamps, created_by |
| Migration type | ADD (new table) |
| Dependency | ADR-V3-001 (DECIDED); V3 IA §8 V3M-1; PE Decision Analysis §22 |
| Risk | Medium (new dimension; wide RLS blast radius — mitigated by deny-by-default + additive policies) |

### 4.2 `staff_profiles.entity_id` (EXTEND — V3M-1)

| Aspect | Detail |
|---|---|
| Existing structure | `staff_profiles` (user_id, role_id, is_active, skills, max_concurrent_tasks) |
| Required V3 structure | add `entity_id UUID NULL REFERENCES processing_entities(id)` — NULL = CarbonTally internal (Q5 convention) |
| Migration type | ADD (nullable column + FK + index) — additive |
| Dependency | V3M-1 (processing_entities must exist first) |
| Risk | Low (nullable; existing internal staff remain `entity_id IS NULL`) |

### 4.3 Worker/entity + work-item/entity relationships (V3M-2)

| Aspect | Detail |
|---|---|
| Existing structure | `manual_review_queue.assigned_to` (worker UUID); no entity dimension |
| Required V3 structure | `manual_review_queue.entity_id UUID NULL REFERENCES processing_entities(id)`; `upload_batches.entity_id UUID NULL` (batch-level allocation) |
| Migration type | ADD (nullable columns) |
| Dependency | V3M-1 |
| Risk | Low–Medium (no existing data affected; NULL = CarbonTally internal) |

### 4.4 Assignment/entity attribution + lifecycle + historical attribution

| Aspect | Detail |
|---|---|
| Existing structure | `review_assignment_history` (active attribution) |
| Required V3 structure | reuse `review_assignment_history` unchanged; entity attribution derived from `staff_profiles.entity_id` of the assignee + work-item `entity_id` (no new history table) |
| Entity lifecycle | Q6 principles: suspension/termination **never deletes** historical work/audit/performance/issue history; active work has a defined reassignment/disposition process; entity access respects lifecycle |
| Migration type | NO CHANGE (reuse) + lifecycle enforced in backend/RLS (not a new table) |
| Risk | Low (existing attribution intact) |

**Constraints (register ADR-V3-001):** must NOT implement in this document; must NOT create
`entity_id`/entity RLS without an approved DB-change plan + migration design (V3M-1/V3M-2);
must preserve org isolation; must NOT resurrect rejected Options A/C.

---
## 5. Work Management Changes

**Why:** ADR-V3-003/011/012 (Work Item / Logical Queue / Technical State Machine separation;
batch=grouping, Work Item=atomic) and ADR-V3-005/006/007 (assignment attribution, SLA/capacity
reuse, auto-assignment orchestration). The canonical human Work Item is a **domain
abstraction over the existing `manual_review_queue` surface** — no new physical queue table,
no fifth queue, no Queue Management subsystem (Queue Audit §11 Option C; Options A/D rejected).

### 5.1 Per-structure verdict (Queue Audit §17 reconciled)

| Structure | Current role | V3 action | Migration type |
|---|---|---|---|
| `manual_review_queue` | canonical human work-item store (active) | **KEEP + EXTEND** (`entity_id` in V3M-2) | ADD (nullable col) |
| `upload_batches` | batch grouping anchor (active) | **KEEP + EXTEND** (`entity_id` in V3M-2) | ADD (nullable col) |
| `review_assignment_history` | assignment attribution (active) | **KEEP** (single attribution record) | NO CHANGE |
| `reassignment_history` | dormant; targets `processing_assignments` id-space | **REPOINT/RETIRE LATER** (reconcile before retirement; ADR-V3-005/016) | NONE now |
| `processing_queue`/`processing_assignments`/`processing_steps` | dormant legacy worker queue | **RETIRE LATER** (inert/archived after dependency chain; ADR-V3-016) | NONE now |
| `document_processing_queue` | technical document state machine; **no active producer** | **KEEP** (technical state machine; producer wiring OPEN/DEFERRED — ADR-V3-004) | NO CHANGE |
| `report_generation_queue` | technical report output store (active) | **KEEP** (specialized output mechanism — outside Work Management) | NO CHANGE |
| `staff_workload` | per-worker capacity (active) | **KEEP** (entity aggregate later) | NO CHANGE |
| `queue_settings` | queue config key/value (active) | **KEEP** (auto-assignment inputs) | NO CHANGE |
| `sla_definitions`/`sla_compliance`/`business_hours` | SLA infra (active) | **KEEP** (per-item + entity-scoped later) | NO CHANGE |
| `qc_checks`/`qc_errors` | QC records (FK-bound to dormant `processing_assignments`) | **REPOINT** at Work Items when QC layering lands | NONE now |
| `approval_requests`/`approval_decisions` | dormant approval vocabulary (FK-bound to `processing_assignments`) | **REPOINT** at Work Items when approval layers are built (ADR-V3-008) | NONE now |
| `manual_extraction_batches`/`manual_extraction_items` | dormant; fold into dpq path | **RETIRE LATER** / fold into dpq producer (ADR-V3-004) | NONE now |

### 5.2 Key findings

- **No Work Item table is created** — the Work Item is the domain abstraction over
  `manual_review_queue` rows (register ADR-V3-003/011; spec §10.3).
- **`internal_tasks`/`task_assignments` (intent-only) must NEVER be created** (ADR-V3-016).
- **Dependency chain for retirement** (ADR-V3-016): Work Item model → active document work
  type (dpq producer) → approval/QC re-pointed → then dormant structures left inert/archived.
- Entity scope on work items is `entity_id IS NULL` = CarbonTally internal (Q5).

---

## 6. Issue Management Changes

**Why:** ADR-V3-009 (DECIDED — Option B): an Issue is a first-class operational domain
object, distinct from a Conversation. Implementation (issues model) is designed before any
migration (register §5 ADR-V3-009; spec §14).

### 6.1 Explicit distinctions

| Concept | Current structure | V3 role |
|---|---|---|
| **Issue** | **none** (no issue entity anywhere) | NEW first-class operational object (V3M-5) |
| **Conversation** | `conversations`/`conversation_participants`/`messages` (org-scoped chat, active) | KEEP unchanged; may be **associated** with an Issue; never becomes the Issue |
| **Validation Error** | ValidationEngine A1–A9 per-record rule failures | KEEP (per-record result; not an issue entity) |
| **QC Error** | `qc_errors`/`qc_checks` (per-QC-pass records) | KEEP (per-pass record; Issue may reference) |
| **User feedback** | `user_feedback` (type/title/description/severity/status) | KEEP as-is; not the Issue model; not deleted |
| **Escalation** | `escalation_level`, `sla_breached`, `customer_verifications.is_escalated` | KEEP (reused by Issues for SLA/escalation) |

### 6.2 Required V3 structure (V3M-5 — conceptual, no schema invented)

| Aspect | Detail |
|---|---|
| Existing structure | none (no unified issue entity; Queue Audit §6) |
| Required V3 structure | `issues` (NEW, designed before migration): issue_type, severity, priority, status, owner, assignee, organization/customer context, processing-entity context (conditional on V3M-1), work-item/document/batch context, SLA, escalation, resolution, reopening, audit/history, timestamps; relationship to work items/documents/batches/processing entities/customers |
| Migration type | ADD (new table + RLS) — designed after ADR-V3-009 and the Work Item boundary (ADR-V3-003) |
| Dependency | ADR-V3-009 (DECIDED); ADR-V3-003 (work-item boundary); ADR-V3-001 (entity context); ADR-V3-006 (SLA reuse) |
| Risk | Medium (new domain; RLS org/entity scope per ADR-V3-010 patterns) |

**Constraints:** do NOT force `conversations` to become the Issue model; do NOT delete or
modify existing issue/feedback structures (`user_feedback`, `qc_errors`, rejection/
correction surfaces); no final columns/enums defined here.

---
## 7. Customer Factor Changes

**Why:** ADR-V3-002 (PROVISIONALLY DECIDED) — dedicated org-owned `customer_factors` domain
(Option B; Option A — extending global `emission_factors` — **REJECTED**). ADR-V3-014
(snapshot/provenance for customer factors).

### 7.1 Existing structure vs required structure

| Aspect | Existing structure | Required V3 structure | Migration type |
|---|---|---|---|
| Customer factor storage | **none** (no customer-factor surface; `emission_factors` is global) | `customer_factors` (NEW, org-scoped): organization_id FK NOT NULL, activity_type, co2e_multiplier, unit, scope, country, reporting_year, factor_source='CUSTOMER', source_reference, status, version, effective_from/to, metadata, created_by/at, updated_at | ADD (new table; V3M-3) |
| Organization ownership | `organizations`/`organization_members`/`is_org_member()` | RLS `is_org_member(organization_id)` select/insert/update; delete restricted / soft-deactivate (mirrors `factor_aliases` RLS) | ADD policies (V3M-3) |
| Factor matching | `FactorMatchingEngine` (candidate-set-agnostic) | EXTEND: merge ACTIVE customer factors as candidates (CF Audit §14) — no new table for matching | NO CHANGE (backend EXTEND) |
| Calculation | `CalculationEngine` (ownership-agnostic) | EXTEND: customer-factor branch; provenance `factor_source='CUSTOMER'`, `factor_set='CUSTOMER'`, `import_batch_id=NULL`, `customer_factor_id` reference | NO CHANGE (backend EXTEND) |
| Snapshot provenance | `calculation_snapshots.factor_id` NOT NULL FK → `emission_factors` (ON DELETE RESTRICT) | **FK relaxation required** (O1 recommended: nullable `factor_id` + `factor_kind` + optional `customer_factor_id`, exactly-one-source check) | EXTEND (V3M-3) — **the only unavoidable existing-schema change** |

### 7.2 OPEN SUB-DECISIONS blocking V3M-3 (register ADR-V3-002)

| Sub-decision | ID | Blocks |
|---|---|---|
| Approval authority | D-cf-3 | customer-factor approval route + status transitions |
| Snapshot FK option | D-cf-2 | `customer_factors` migration design + calculation provenance |
| Factor precedence (customer-first assumed, not decided) | D-cf-5 | matching merge behaviour + config flag |
| Consultant access / RLS membership model | R3 / D-cf-6 | whether `customer_factors` RLS needs an `is_consultant_of` clause |

### 7.3 Constraints

- Must NOT put customer factors in `emission_factors` (REJECTED — CF Audit §10 Option A).
- Must NOT create `customer_calculation_snapshots`, a second matching/calculation engine,
  a second approval system, or new factor enums (CF Audit §29; ADR-V3-014).
- Must NOT change the 7,049 factors, `emission_factors` schema/RLS/natural key, or the
  19 v2.1 route contracts.
- No final columns are invented in this document (conceptual only).

---

## 8. RBAC Changes

**Why:** ADR-V3-010 (PROVISIONALLY DECIDED) — extend the existing org-isolation model with
entity scope; no new RBAC system; final entity role names deferred to the V3 RBAC design
(ADR-V3-001 Q6).

### 8.1 Existing RBAC surface

| Structure | Current role | V3 action |
|---|---|---|
| `users` | identity anchor (auth.users mirror) | **KEEP** |
| `organization_members` | org membership (owner/admin/member/viewer) + `is_org_member()` RLS helper | **KEEP** (customer axis unchanged) |
| `staff_profiles` | internal staff profiles (role_id → `staff_roles`, permissions JSONB) | **EXTEND** — `entity_id` nullable FK (V3M-1) distinguishes CarbonTally-internal (`NULL`) from Processing Entity staff |
| `staff_roles` | staff role definitions (name, permissions JSONB) | **KEEP** (no new role rows required by the register); entity-scoped roles **conceptual/deferred** (Q6) |
| `roles` | legacy role vocabulary (reference `authenticated_read`) | **KEEP** |
| `consultant_profiles`/`consultant_firm_members`/`consultant_clients` | consultant axis (RC2-C6 firm tenancy) | **KEEP** (separate axis; membership model INVESTIGATE — R3) |
| `auth.py` / `api/dependencies.py` (backend) | `get_current_user`/`require_admin`/`ensure_org_access` | **EXTEND** (entity-scoped authorization checks) — backend, not DB |

### 8.2 V3 RBAC findings

- **Processing Entity scope** fits into the existing model by adding `staff_profiles.entity_id`
  (V3M-1) + entity-scoped authorization checks — no `entity_members`-style table is required
  by the register (entity membership is expressed by `staff_profiles.entity_id`, consistent
  with the Q5 convention).
- **Final entity role names, transition authority and RBAC matrix are explicitly deferred**
  (Q6) — no roles created in this document.
- **UNKNOWN / INVESTIGATE:** consultant membership model (R3) — whether consultants reach
  client data via `consultant_clients` or `organization_members`; legacy staff-table RLS
  posture (RC2 §8 staff RBAC is "v1.1 concern").

---
## 9. RLS Changes

**Why:** ADR-V3-010 (PROVISIONALLY DECIDED, INVESTIGATE flags) — V3 **extends** the existing
org-isolation RLS model; it never weakens any policy. Entity-level RLS is per ADR-V3-001
(DECIDED) and is designed with deny-by-default + `is_entity_member()`.

### 9.1 Existing RLS posture (verified)

| Table | Current RLS | Notes |
|---|---|---|
| Org-bearing tables | `*_tenant_select/insert/update/delete` via `is_org_member` (+ `is_org_consultant` on SELECT) | RC1/RC2; solid |
| `emission_factors` | reference `authenticated_read` (SELECT USING true); writes service-role | **NO CHANGE** |
| `calculation_snapshots` | `calc_snapshots_select_own` (select only) | **KEEP** |
| `factor_aliases` | `aliases_select_own/insert_own/delete_own` | **KEEP** (RLS pattern reused for `customer_factors`) |
| `import_batches`/`domain_events` | deny-by-default (no policies) | **KEEP** |
| `organizations`/`organization_members` | org select/update; self/admin member policies | **KEEP** |
| staff tables (`staff_profiles` etc.) | deny-by-default for authenticated (RC2 §8) | **EXTEND** — entity-scoped access per V3M-1 |
| Legacy permissive policies on active queue structures | **flagged INVESTIGATE/HARDEN** (Queue Audit §15–§16) | **INVESTIGATE first** — confirm no active dependency before tightening |

### 9.2 Conceptual V3 RLS changes (no SQL written)

| Boundary | Requirement |
|---|---|
| Customer A ✗ Customer B | existing `is_org_member()` — preserved |
| Processing Entity A ✗ Processing Entity B | NEW deny-by-default + `is_entity_member()` (per ADR-V3-001, V3M-1/V3M-2) |
| Processing Entity ✗ unrelated customer data | entity sees only authorized work (work-item `entity_id` + org scope) |
| CarbonTally internal operations | authorized cross-entity visibility (system scope; `entity_id IS NULL` internal) |
| `customer_factors` | org-scoped policies via `is_org_member()` (mirrors `factor_aliases`); consultant clause per R3 investigation |
| `issues` | org/entity scope policies per ADR-V3-010 patterns |

### 9.3 Overly-permissive legacy policies (INVESTIGATE, not changed)

- Legacy permissive policies on `manual_review_queue` and other active queue structures
  coexist with the RC2 tenant policies (Queue Audit §15–§16) — **INVESTIGATE** before any
  hardening.
- Broad `authenticated_read` on reference/staff tables — staff RBAC is a "v1.1 concern"
  (RC2 §8) — **INVESTIGATE** as part of the V3 security pass.

---

## 10. Configuration Changes

**Why:** ADR-V3-006 (PROVISIONALLY DECIDED) — configuration already exists and is reused;
no duplicate configuration system (Queue Audit §13, §16).

| Structure | Current role | V3 action |
|---|---|---|
| `queue_settings` (key/value JSONB) | auto_assign, max_reviews, sla_hours, escalation_hours, priority_weights | **KEEP** (auto-assignment inputs, §20) |
| `sla_definitions` | per-document-type SLA | **KEEP** (per-item SLA; entity-scoped later per ADR-V3-001) |
| `sla_compliance` | SLA records (deadline/breach) | **KEEP** |
| `business_hours` | working days/hours/timezone | **KEEP** |
| `staff_workload` | per-worker capacity | **KEEP** (entity aggregate later) |
| `system_settings` | platform settings | **KEEP** |
| Entity-scoped configuration (capacity/SLA/auto-assign/QC/hours/escalation/notification/workflow) | **none today** | extend existing key-value patterns per ADR-V3-001; **no new config system** |

**Constraint:** config-ownership of `queue_settings` semantics is unresolved (ADR-V3-006) —
do not change semantics without a decision.

---

## 11. Audit and History Changes

**Why:** ADR-V3-013 (PROVISIONALLY DECIDED) — reuse the existing layered audit stack; no new
audit system, no duplicate history surfaces.

| Structure | Current role | V3 action |
|---|---|---|
| `review_assignment_history` | assignment attribution (active, append-only) | **KEEP** (single attribution record) |
| `domain_events` (M5) | append-only event store (EventBus) | **KEEP** (event/audit records) |
| `audit_trail`/`audit_logs` | audit records (legacy) | **KEEP** |
| `calculation_snapshots` (M3) | immutable calc provenance (content_hash + verify) | **KEEP** (+ optional `CalculationSnapshotOut` provenance exposure — API EXTEND) |
| `review_audit_trail`/`processing_audit_trail` | per-table review/processing trails | **KEEP** (consolidate duplicate surfaces at work-item boundary later) |
| `reassignment_history` | dormant duplicate of assignment history | **REPOINT/RETIRE LATER** (reconcile before retirement; ADR-V3-005/016) |
| `customer_review_log` | customer approval trail | **KEEP** |
| `import_batches` | factor import provenance | **KEEP** |
| Entity scope + actor-role on audit entries | absent | **EXTEND** audit payload/scope (V3 IA §6.1 "Audit EXTEND") |

**Constraints:** no new audit/history system; no deletion of dormant history tables until
re-pointed (ADR-V3-016); snapshots immutable (ADR-V3-014).

---

## 12. Storage Impact

**Why:** Storage for entity/worker-scoped document access is a V3 requirement (V3 IA §5.1
V3-016), but **no redesign occurs in this phase**.

| Aspect | Current state | V3 impact |
|---|---|---|
| Document evidence storage | Supabase Storage buckets/objects; legacy Storage policies (init schema) | **KEEP** — no change in this phase |
| Entity/worker-scoped document access (signed URLs vs entity bucket) | **not resolved** | **INVESTIGATE** (PE Open Questions Q9; ADR-V3-010/V3-016) |
| Customer-factor evidence attachments | none | **DEFERRED** (CF Audit §19) |
| PDF/HTML report rendering & storage | deferred (Phase 10 boundary) | **DEFERRED** |

**Flagged INVESTIGATE:** Storage policy shape for per-assignment document access; whether
signed URLs suffice or an entity bucket is required. No Storage policy is changed in this
document.

---

## 13. Table-by-Table Impact Matrix

| Table | Current Role | V3 Action | Change Type | Risk | Dependency |
|---|---|---|---|---|---|
| `emission_factors` | global factor reference (7,049) | **NO CHANGE** (immutable baseline) | none | Low | none |
| `import_batches` | factor import provenance (M1) | **NO CHANGE** | none | Low | none |
| `calculation_snapshots` | immutable calc provenance (M3) | **EXTEND** (FK relaxation for customer factors) | ADD/alter | Medium | ADR-V3-002/014 (D-cf-2) |
| `emissions_logs` | org emission records | **NO CHANGE** | none | Low | none |
| `domain_events` | append-only event store (M5) | **NO CHANGE** (audit scope EXTEND at payload level) | none | Low | none |
| `factor_aliases` | org/global aliases (M6) | **NO CHANGE** (RLS pattern reused) | none | Low | none |
| `organizations` | tenant root | **NO CHANGE** (never represents a Processing Entity) | none | Low | none |
| `organization_members` | org membership | **NO CHANGE** | none | Low | none |
| `users` | identity anchor | **NO CHANGE** | none | Low | none |
| `staff_profiles` | internal staff | **EXTEND** — add `entity_id` nullable FK → `processing_entities` | ADD | Low–Med | V3M-1 (ADR-V3-001) |
| `staff_roles` | staff role definitions | **NO CHANGE** (entity roles deferred) | none | Low | none |
| `manual_review_queue` | canonical human Work Item store (active) | **EXTEND** — add `entity_id` nullable | ADD | Low–Med | V3M-2 (ADR-V3-001/003) |
| `upload_batches` | batch grouping anchor (active) | **EXTEND** — add `entity_id` nullable | ADD | Low | V3M-2 |
| `review_assignment_history` | assignment attribution (active) | **NO CHANGE** (reuse) | none | Low | none |
| `reassignment_history` | dormant duplicate | **REPOINT/RETIRE LATER** | none now | Low | ADR-V3-005/016 |
| `staff_workload` | per-worker capacity | **NO CHANGE** (entity aggregate later) | none | Low | none |
| `queue_settings` | queue config (key/value) | **NO CHANGE** | none | Low | none |
| `sla_definitions`/`sla_compliance`/`business_hours` | SLA infra | **NO CHANGE** | none | Low | none |
| `document_processing_queue` | technical state machine (no producer) | **NO CHANGE** (KEEP) | none | Low | ADR-V3-004 |
| `report_generation_queue` | technical output store | **NO CHANGE** (KEEP) | none | Low | none |
| `processing_queue`/`processing_assignments`/`processing_steps` | dormant legacy | **RETIRE LATER** (inert/archived) | none now | Low | ADR-V3-016 |
| `qc_checks`/`qc_errors` | QC records (FK → `processing_assignments`) | **REPOINT** at Work Items later | none now | Med | ADR-V3-016 |
| `approval_requests`/`approval_decisions` | dormant approval vocabulary | **REPOINT** at Work Items later | none now | Med | ADR-V3-008 |
| `customer_verifications`/`customer_review_log` | customer approval (active) | **NO CHANGE** (keep + extend at backend) | none | Low | none |
| `conversations`/`conversation_participants`/`messages`/`notifications` | org-scoped chat (active) | **NO CHANGE** (Issue ≠ Conversation) | none | Low | none |
| `user_feedback` | legacy feedback | **NO CHANGE** (not the Issue model) | none | Low | none |
| `manual_extraction_batches`/`manual_extraction_items` | dormant; fold into dpq | **RETIRE LATER** / fold into dpq producer | none now | Med | ADR-V3-004 |
| `processing_entities` (NEW) | — | **ADD** — entity domain | ADD | Med | ADR-V3-001 (V3M-1) |
| `customer_factors` (NEW) | — | **ADD** — org-owned factor domain | ADD | Med | ADR-V3-002 (V3M-3) |
| `issues` (NEW) | — | **ADD** — first-class Issue domain | ADD | Med | ADR-V3-009 (V3M-5) |
| `internal_tasks`/`task_assignments` (intent only) | — | **NEVER CREATE** (superseded by Work Item model) | none | — | ADR-V3-016 |

---

## 14. RLS Impact Matrix

| Table | Current RLS | V3 Requirement | Action | Risk |
|---|---|---|---|---|
| Org-bearing tenant tables | `*_tenant_*` via `is_org_member` (+consultant on SELECT) | preserve | NO CHANGE | Low |
| `emission_factors` | reference `authenticated_read` (SELECT true) | preserve (global read) | NO CHANGE | Low |
| `calculation_snapshots` | `calc_snapshots_select_own` | preserve; org-scoped | NO CHANGE | Low |
| `factor_aliases` | `aliases_select_own/insert/delete` | preserve; **pattern reused for `customer_factors`** | NO CHANGE | Low |
| `import_batches`/`domain_events` | deny-by-default | preserve | NO CHANGE | Low |
| `staff_profiles` (+ entity scope) | deny-by-default (RC2 §8) | entity-scoped access (`entity_id`), deny-by-default + `is_entity_member()` | EXTEND | Med |
| `manual_review_queue`/`upload_batches` | tenant + legacy permissive (INVESTIGATE) | org scope preserved; entity scope per V3M-2 | EXTEND | Med |
| `customer_factors` (NEW) | none | `is_org_member(organization_id)` select/insert/update; delete restricted/soft-deactivate; consultant clause per R3 | NEW | Med |
| `issues` (NEW) | none | org/entity scope per ADR-V3-010 patterns | NEW | Med |
| Legacy permissive queue policies | permissive (Queue Audit §15–§16) | **INVESTIGATE/HARDEN** after dependency confirmation | INVESTIGATE | High |

---

## 15. Migration Dependency Graph

Derived from ADR dependencies + repository evidence (V3 IA §8; spec §28):

```
OPERATIONAL TRACK                          FACTOR TRACK (independent)
─────────────────────                      ──────────────────────────
ADR-V3-001 (DECIDED)
    │
    ▼
V3M-1  processing_entities (NEW)  ────────►  customer factor sub-decisions
    │  + staff_profiles.entity_id              (D-cf-2/3/5, R3 — OPEN)
    ▼                                          │
V3M-2  entity_id on work items          V3M-3  customer_factors (NEW)
    │   (manual_review_queue,                    + calculation_snapshots FK
    │    upload_batches)                         relaxation (O1)
    ▼                                          │
RLS:  is_entity_member() helper          factor matching EXTEND (backend)
    │   + entity policies (deny-by-default)    │
    ▼                                          ▼
assignment reuse (review_assignment_history)  calculation EXTEND + snapshot
    │                                          provenance (CUSTOMER)
    ▼
SLA / auto-assignment (reuse queue_settings,
    sla_*, staff_workload)

ISSUE TRACK:
ADR-V3-009 (DECIDED) ──► design (work-item boundary ADR-V3-003) ──► V3M-5 issues (NEW) + RLS

DEFERRED TRACK:
H3 decision ──► V3M-4 provider widening (T3) — independent, after H3

RETIREMENT TRACK (ADR-V3-016):
Work Item model → dpq producer (ADR-V3-004) → approval/QC re-pointed
   → then processing_queue family / reassignment_history / manual_extraction_* left inert
```

---

## 16. Migration Sequence

**Order derived from the dependency graph (§15).** All items are CONDITIONAL; none is created
by this document (V3 IA §29).

```
1.  V3M-1  processing_entities + staff_profiles.entity_id      (ADR-V3-001 DECIDED)
2.  RLS    is_entity_member() helper + entity policies          (deny-by-default; additive)
3.  V3M-2  entity_id on manual_review_queue, upload_batches     (entity scope on work items)
4.  (none) Assignment reuse — review_assignment_history (no migration)
5.  (none) SLA/KPI entity scope — reuse queue_settings/sla_*/staff_workload (no migration)
6.  V3M-5  issues (NEW) + RLS                                    (ADR-V3-009 DECIDED; design first)
7.  V3M-3  customer_factors (NEW) + snapshot-FK relaxation (O1)  (blocked by D-cf-2/3/5, R3)
8.  (none) Calculation/matching/validation backend EXTEND for customer factors
9.  (none) API additive routes (customer factors, work items, issues, entity admin)
10. (later) V3M-4 provider widening (T3) — after H3
11. (later) Queue retirement (ADR-V3-016) — after Work Item model + dpq producer
```

**Parallel tracks:** factor track (7–8) runs independently of the operational track (1–5);
issue track (6) depends on the work-item boundary; retirement (11) and provider widening
(V3M-4) run last.

---

## 17. Backward Compatibility

| Guarantee | Detail |
|---|---|
| All V3M changes additive | new tables + nullable columns + additive RLS policies; no table dropped, no column renamed |
| Existing data unaffected | `entity_id` columns default NULL (= CarbonTally internal); `customer_factors` empty until used; `issues` empty until used |
| Factor baseline preserved | `emission_factors` 7,049 rows (DEFRA 7,029 + SEAI 20) untouched; no factor data migration |
| Existing RLS not weakened | new policies are additive; org/tenant boundaries preserved; legacy policies only hardened after INVESTIGATE |
| Existing APIs not broken | the 19 v2.1 route contracts and error envelope are the regression guard (spec §26.1); V3 API work is additive |
| Snapshot FK relaxation (O1) | nullable `factor_id` is backward compatible — existing snapshot rows keep their factor_id; exactly-one-source check preserves integrity |

---

## 18. Data Migration Requirements

| Data | Requirement |
|---|---|
| `emission_factors` (7,049) | **NO data migration** — factors are the immutable baseline; no V3 change touches them |
| `staff_profiles` | no migration — existing internal staff remain `entity_id IS NULL` (the NULL convention means no backfill is needed) |
| `manual_review_queue`/`upload_batches` | no migration — existing rows default `entity_id IS NULL` = CarbonTally internal |
| `customer_factors` | no existing data (new table) |
| `issues` | no existing data (new table); existing `user_feedback`/`qc_errors`/validation errors are NOT migrated into issues (they remain separate) |
| `processing_queue` family / dormant structures | no data migration — left inert/archived; children re-pointed before any retirement |
| Consultant membership model | **INVESTIGATE** (R3) — no migration until the model is decided |

---

## 19. Rollback Considerations

| Change | Rollback approach |
|---|---|
| V3M-1 (`processing_entities`, `staff_profiles.entity_id`) | **ADD-only, reversible**: DROP the new table + DROP the nullable column returns the schema to V2.1; no data loss (existing rows untouched) |
| V3M-2 (`entity_id` on work tables) | DROP nullable columns — reversible |
| V3M-3 (`customer_factors` + snapshot-FK relaxation) | DROP `customer_factors`; restore `factor_id NOT NULL` after re-asserting every existing snapshot has factor_id set (O1 preserves this) |
| V3M-5 (`issues`) | DROP the `issues` table — reversible (no existing data) |
| RLS additions (`is_entity_member()`, entity/customer-factor policies) | DROP POLICY / DROP FUNCTION — reversible; existing policies untouched |
| Retirement of dormant structures (ADR-V3-016) | **No deletion in V3** — structures are left inert/archived; rollback = re-enable, no restore needed |

**General principle:** every V3M change is additive and reversible; the migration
transaction should be wrapped per-file (V2.1 M1–M8 convention) with a verification step.

---

## 20. Risks

| # | Risk | Source evidence | Mitigation |
|---|---|---|---|
| 1 | Entity RLS blast radius | ADR-V3-001; PE Decision Analysis §11 | deny-by-default + additive `is_entity_member()`; entity scope only on authorized tables |
| 2 | Legacy permissive queue policies conflict with entity isolation | Queue Audit §15–§16; ADR-V3-010 | INVESTIGATE before hardening; confirm no active dependency |
| 3 | `calculation_snapshots.factor_id` FK relaxation degrades integrity | ADR-V3-014; CF Audit §16 | O1 exactly-one-source check; immutable snapshots preserved |
| 4 | Customer-factor RLS leaks org data if consultant clause misdesigned | CF Audit §19, §31 (R3) | `is_org_member()` mirror of `factor_aliases`; consultant clause only after investigation |
| 5 | `processing_queue` family children block retirement | ADR-V3-016 (qc_checks/approval_requests FK-bound) | never delete until re-pointed; leave inert |
| 6 | New `issues` table duplicates `user_feedback`/`qc_errors`/validation errors | ADR-V3-009; Queue Audit §6 | distinct concepts; existing structures retained |
| 7 | Migration-order violation (entity_id before processing_entities) | V3 IA §8; spec §28.2 | dependency graph (§15) + sequence (§16) |
| 8 | Factor baseline drift during V3 | V2.1 traceability; spec §32.5 | regression guard: 7,049 baseline + 19 route contracts |
| 9 | Integration test suite not executable (D14) | V3 IA §21, §26; register §10D | precondition before any V3 DB/RLS work |

---

## 21. Unknowns / Investigation Items

| # | Item | Where | Decision needed before |
|---|---|---|---|
| U1 | Consultant membership model (`consultant_clients` vs `organization_members`) for factor/emissions access | R3 / D-cf-6; ADR-V3-002/010 | `customer_factors` RLS design |
| U2 | Customer-factor approval authority | D-cf-3; ADR-V3-002 | customer-factor status/API |
| U3 | Customer-factor snapshot FK option (O1 vs O2) | D-cf-2; ADR-V3-002/014 | V3M-3 design |
| U4 | Factor precedence (customer vs CarbonTally on both-match) | D-cf-5; ADR-V3-002 | matching merge design |
| U5 | `is_entity_member` admin coverage (entity admins vs entity staff) | PE Q7; ADR-V3-010 | entity RLS policy scope |
| U6 | Storage policy shape (signed URLs vs entity bucket) | PE Q9; ADR-V3-010/V3-016 | entity document access |
| U7 | Issue entity context (entity-scoped surface vs entity reference) | PE Q8; ADR-V3-009 | V3M-5 design |
| U8 | Legacy permissive queue policies inventory | Queue Audit §15–§16; ADR-V3-010 | RLS hardening pass |
| U9 | dpq producer/consumer architecture (V3 document work type) | ADR-V3-004 | document work type wiring |
| U10 | Entity contract metadata fields (commercial) | Q1; ADR-V3-001 | V3M-1 schema design |

---

## 22. Final Recommendation

1. **The V3 database migration is CONDITIONAL** (V3 IA §29), and the dependency picture is
   now clearer: the **entity migration (V3M-1/V3M-2) is unblocked** (ADR-V3-001 DECIDED), the
   **issues migration (V3M-5) is unblocked at the architecture level** (ADR-V3-009 DECIDED;
   design required first), and the **customer-factor migration (V3M-3) remains blocked** by
   the four OPEN SUB-DECISIONS (D-cf-2/3/5, R3).
2. **Recommended implementation order:** V3M-1 → RLS → V3M-2 → assignment/SLA reuse →
   V3M-5 → V3M-3 → backend/API extensions (spec §28.2; §16 of this document). V3M-4 and
   queue retirement run later, gated by H3 and ADR-V3-016 respectively.
3. **Preserve the factor baseline**: no V3 change requires or performs any `emission_factors`
   data migration; the 7,049-row baseline (DEFRA 7,029 · SEAI 20) is the regression guard.
4. **No new Queue Management subsystem** and **no Work Item table** — the canonical Work Item
   is the domain abstraction over `manual_review_queue` (ADR-V3-003/011).
5. **Before any migration file is written**, the register's Implementation Gate (§10) must be
   satisfied: DB-change plan approved, RLS plan approved, backend/API plans approved,
   migration sequence approved, and the integration suite executable (D14).

**This document is a planning artifact only. No migration, schema, RLS, backend, API,
frontend, seed-data or test change has been made. Factor baseline unchanged
(DEFRA 7,029 · SEAI 20 · TOTAL 7,049).**

