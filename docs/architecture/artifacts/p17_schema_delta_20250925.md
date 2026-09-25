# CT-PO-P17 — Proposed Schema Delta (Architecture Only)

**Artifact:** `p17_schema_delta_20250925.md`
**Task ID:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`
**Baseline commit:** `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be`
**Environment:** local Demo Lab (`carbontally_demo_local` @ `127.0.0.1:54426`), read-only inspection

> **This document PROPOSES schema changes. It does not implement them, and no migration was created or applied by this task.**
> Production is untouched and is not authorised by this task.

---

## 0. Ground rules applied

1. **Inspect before proposing.** The live schema was enumerated read-only: **141 public tables**, **83 migrations** under `supabase/migrations/`, latest migration `20261009000000_p16r7_calculation_request_idempotency.sql`.
2. **Reuse before extending.** A capability is extended or created only when the existing model genuinely cannot carry it (§4 lists what is deliberately reused unchanged).
3. **Additive only.** No historical migration is modified. No existing column, row, value, index or policy is dropped or rewritten.
4. **Historical rows are never rewritten and never fabricated.** Where a new dimension is mandatory for new writes it is added as a `NOT VALID` CHECK, so existing rows are exempt from validation while every subsequent INSERT/UPDATE is enforced. This preserves the P16 discipline: the 34 existing snapshots and 34 existing emissions rows keep their exact values, scope, category-less/method-less state and reportability.
5. **Every new table follows the established RLS convention** (`supabase/migrations/20260807070000_add_new_table_rls.sql`): RLS ENABLED, `GRANT ALL` to `service_role`, `SELECT/INSERT/UPDATE/DELETE` to `authenticated`, `REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN` from `authenticated`, `anon` gets nothing, policies reuse `public.is_org_member(uuid)`.
6. **No speculative tables.** Nothing is proposed that a named P17 phase does not need.

---

## 1. Migration numbering and sequencing

| Order | Proposed filename | Phase | Why here |
|---|---|---|---|
| 1 | `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | P17-A | Adds the canonical dimensions (`scope2_method`, `scope3_category`), `energy_type`, `data_quality`, the `facility_id` FK, the boundary/origin properties and the factor-eligibility columns. Everything downstream depends on these. |
| 2 | `20261011000000_p17c_contractual_instruments_and_allocations.sql` | P17-C | The new instrument + allocation entities; must follow P17-A so the market-based method dimension exists first. |
| 3 | `20261012000000_p17d_scope3_category_taxonomy.sql` | P17-D | Seeds the 15 canonical categories (reference data) and any category FK. |
| 4 | `20261013000000_p17h_estimation_and_assumption_records.sql` | P17-H | Estimation/assumption records used by categories 7, 11, 12 and 14. |
| 5 | `20261014000000_p17h_boundary_and_consolidation.sql` | P17-H | Organisation consolidation approach + double-counting detector support. |

**Numbering rules honoured:** strictly increasing timestamps after `20261009000000`; one migration per coherent change set; no reuse of an existing timestamp; no edit to any historical file.

**Known consequence (already-failing tests).** Two suites assert "latest migration" / migration-count expectations:
`backend/tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` and
`backend/tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy`.
Both are **already failing as Class-E stale expectations** on the P16 baseline (P16-FINAL-VERIFICATION §8–§9: migration count observed as 83 against an expected 71). Adding P17 migrations advances those expectations further. The correct action in an implementing phase is to **update the stale expectation to the new, correct value** — a legitimate test-expectation advance, reported as such, never a suppression.

---

## 2. EXTEND — existing tables

### 2.1 `calculation_snapshots` — the authoritative calculation record

| Column | Type | Null | Constraint | Purpose |
|---|---|---|---|---|
| `scope2_method` | text | yes | `CHECK (scope2_method IS NULL OR scope2_method IN ('LOCATION_BASED','MARKET_BASED'))` | Dual-method identity; reuses the frozen B1 disclosure vocabulary verbatim. |
| `scope3_category` | smallint | yes | `CHECK (scope3_category IS NULL OR scope3_category BETWEEN 1 AND 15)` | GHG Protocol category identity 1–15. |
| `energy_type` | text | yes | `CHECK (energy_type IS NULL OR energy_type IN ('electricity','heat','steam','cooling','fuel'))` | Scope 2 energy type (required for Scope 2). |
| `data_quality` | text | yes | `CHECK (data_quality IS NULL OR data_quality IN ('primary_measured','primary_supplier','secondary_estimated','spend_based_estimated','modelled'))` | Data-quality dimension (no numeric uncertainty — deferred). |
| `facility_id` | uuid | yes | `REFERENCES public.facilities(id)` | Real, indexable, FK-constrained site dimension (today JSONB-only on the log, absent on the snapshot). |
| `transport_boundary` | text | yes | `CHECK (... IN ('upstream','downstream'))` | DC-04 (category 4 vs 9). |
| `waste_origin` | text | yes | `CHECK (... IN ('operations','sold_product_eol'))` | DC-05 (category 5 vs 12). |
| `source_snapshot_id` | uuid | yes | `REFERENCES public.calculation_snapshots(id)` | Category 3 derivation link (DC-02) and general derived-result provenance. |

**Scope-rules (added `NOT VALID` so historical rows are never rewritten):**

```sql
ALTER TABLE public.calculation_snapshots
  ADD CONSTRAINT calc_snapshots_scope2_method_required
  CHECK (scope <> 'Scope 2' OR scope2_method IS NOT NULL) NOT VALID;
ALTER TABLE public.calculation_snapshots
  ADD CONSTRAINT calc_snapshots_scope3_category_required
  CHECK (scope <> 'Scope 3' OR scope3_category IS NOT NULL) NOT VALID;
ALTER TABLE public.calculation_snapshots
  ADD CONSTRAINT calc_snapshots_category_scope_consistency
  CHECK (scope3_category IS NULL OR scope = 'Scope 3') NOT VALID;
ALTER TABLE public.calculation_snapshots
  ADD CONSTRAINT calc_snapshots_method_scope_consistency
  CHECK (scope2_method IS NULL OR scope = 'Scope 2') NOT VALID;
```

**Derived-result uniqueness (additive):**

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_calc_snapshots_cat3_source
  ON public.calculation_snapshots (source_snapshot_id)
  WHERE scope3_category = 3 AND source_snapshot_id IS NOT NULL;
```

**Indexes:** `(organization_id, scope3_category)`, `(organization_id, scope2_method)`, `(organization_id, facility_id)`.

**Historical rows:** all 34 snapshots (6 Scope 1 reportable, 2 Scope 1 superseded, 25 Scope 3 reportable, 1 Scope 3 not_for_reporting) receive **NULL** for every new column. They satisfy the `NOT VALID` constraints, remain byte-identical, and are explicitly documented as having no category or method. **No backfill is performed and no category or method is fabricated for history.**

### 2.2 `emissions_logs` — the row consumed by reporting

Mirrors §2.1 exactly for consumption-boundary filtering without a join: `scope2_method`, `scope3_category`, `energy_type`, `data_quality`, `facility_id` (FK), `transport_boundary`, `waste_origin`, `source_snapshot_id`, plus the same `NOT VALID` scope-rules and the same indexes.

**FK note.** `facility_id` exists today only as `metadata->>'facility_id'` (`backend/data/emissions_logs.py:221`, and `_LOG_COLUMNS` does not include the column). Adding the real column does **not** remove or change the JSONB behaviour for historical rows. The implementing phase must decide whether new writes populate both; the recommendation is to treat the column as authoritative and keep the JSONB key for backward compatibility until a separate cleanup is authorised.

### 2.3 `emission_factors` — factor governance

| Column | Type | Null | Constraint | Purpose |
|---|---|---|---|---|
| `scope2_method` | text | yes | same vocabulary CHECK | Marks a factor as location-eligible, market-eligible or both (`NULL` = not yet classified). |
| `scope3_category_hint` | smallint | yes | `BETWEEN 1 AND 15` | A **proposal only**; the category is confirmed on the activity and the hint must never be treated as authoritative. |
| `factor_type` | text | yes | `CHECK (... IN ('primary','secondary','component','upstream','outside_of_scopes'))` | Primary/secondary/component classification (the P14 audit found no such column; a `factor_status` enum exists but is unused). |
| `gas_coverage` | text | yes | `CHECK (... IN ('CO2','CO2e'))` | Makes the existing `domain/factor.py::gas_coverage()` derivation (SEAI = CO2-only) explicit and queryable. |

**Deliberately NOT proposed:** no new factor rows, no fabricated multipliers, no 2026 factor set, no residual-mix values. The 7,049 existing rows are untouched and stay `NULL` in the new columns until a later, separately authorised classification pass.

### 2.4 `activity_clarifications` — manual-review decisions

Add nullable `resolved_scope2_method` (same CHECK) and `resolved_scope3_category` (1–15 CHECK), so an operator decision that selects or confirms a method or category is recorded in the **existing** adjudication lifecycle (which already provides versioning, `supersedes_id`, `is_current`, `evidence_signature`, `re_evaluation_required`) rather than in a parallel review system.

### 2.5 `organizations` — accounting boundary

Add nullable `consolidation_approach` (`OPERATIONAL_CONTROL` | `FINANCIAL_CONTROL` | `EQUITY_SHARE`), reusing the existing `CONSOLIDATION_APPROACHES` vocabulary in `backend/domain/disclosure.py`. Required for DC-07 and for categories 8/13. `NULL` means "not yet decided" and must fail closed wherever a category depends on it.

---

## 3. NEW — unavoidable domain entities

### 3.1 `contractual_instruments` (P17-C)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid PK | no | |
| `organization_id` | uuid | no | FK organizations; **the claimant tenant**. The RLS tenant key. |
| `instrument_type` | text | no | CHECK in the generic vocabulary (energy_attribute_certificate, guarantee_of_origin, supplier_specific_contract, ppa, rec, green_tariff, other). |
| `identifier` | text | no | certificate/contract serial. |
| `issuer` | text | yes | issuing/provider entity. |
| `source_facility` | text | yes | generation/source facility where available. |
| `geography` | text | no | market/geography of validity. |
| `generation_period_start` / `generation_period_end` | date | yes | generation period. |
| `vintage_year` | integer | yes | generation vintage. |
| `quantity` | numeric | no | `CHECK (quantity > 0)`. |
| `unit` | text | no | FK units(code) — must reconcile against consumption units. |
| `valid_from` / `valid_to` | date | yes | validity window. |
| `retirement_status` | text | no | CHECK in ('active','retired','cancelled'), default 'active'. |
| `retirement_reference` | text | yes | cancellation/retirement reference. |
| `evidence_item_id` | uuid | yes | FK evidence_line_items — the instrument's own source evidence. |
| `created_by` / `created_at` / `updated_at` | | | audit |

* **Unique:** `(organization_id, instrument_type, identifier)` — one instrument identity per tenant.
* **Indexes:** `(organization_id, geography, vintage_year)`, `(organization_id, retirement_status)`.
* **RLS:** SELECT/INSERT/UPDATE/DELETE org-scoped via `is_org_member(organization_id)`; `anon` none.

**Why new:** no comparable entity exists anywhere in the 141-table inventory. Scope 2 market-based accounting backed by instruments is not expressible without it.

### 3.2 `instrument_allocations` (P17-C)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid PK | no | |
| `organization_id` | uuid | no | must equal the parent instrument's `organization_id` |
| `instrument_id` | uuid | no | FK contractual_instruments(id) |
| `calculation_snapshot_id` | uuid | yes | FK calculation_snapshots(id) — the market-based result it supports |
| `emissions_log_id` | uuid | yes | FK emissions_logs(id) |
| `allocated_quantity` | numeric | no | `CHECK (allocated_quantity > 0)` |
| `allocated_unit` | text | no | FK units(code) |
| `allocation_period_start` / `_end` | date | no | applicable consumption period |
| `claim_reference` | text | yes | claim/record reference |
| `created_by` / `created_at` | | | audit |

* `UNIQUE (instrument_id, allocation_period_start, allocation_period_end, calculation_snapshot_id)` — one allocation of one instrument to one result.
* **Cross-tenant claim impossibility:** `organization_id` is on the row and RLS denies other tenants; a composite FK to `(id, organization_id)` on the parent makes a mismatched pair structurally impossible.
* **Quantity reconciliation:** `sum(allocated_quantity per instrument) <= instrument.quantity` cannot be expressed as a single-row CHECK. It must therefore be enforced by a service-level guard **plus** a deterministic database test, and the implementing phase must state that explicitly rather than implying the database alone guarantees it.

### 3.3 `scope3_categories` (P17-D) — reference seed, exactly 15 rows

`category` (smallint PK, 1–15), `slug` (unique text), `name` (text), `is_downstream` (boolean), `description` (text), `created_at`.

Seeded from the GHG Protocol category names and used as the controlled vocabulary behind the `scope3_category` CHECK. Seeding 15 named categories is **reference data, not implementation**: no methodology, factor, calculation or result is implied.

### 3.4 `estimation_records` (P17-H)

`id`, `organization_id`, `calculation_snapshot_id` (FK), `estimation_method` (text, CHECK), `inputs` (jsonb), `assumptions` (jsonb), `factor_id` (FK, nullable), `source_reference` (text), `actor_user_id`, `created_at`.

Required by the no-silent-estimation rule for categories 7, 11, 12 and 14 and for any estimated line elsewhere.

### 3.5 Explicitly deferred entities (NOT part of this delta)

| Entity | Why deferred |
|---|---|
| `sold_products` | Needed by categories 9–13; the product/boundary model needs a PO decision before it is designed. |
| `investments` / `investees` | Category 15 needs the bounded-methodology decision first. |
| `franchises` | Category 14 needs the franchise operating-model decision. |
| `residual_mix_factors` | FRAMEWORK_SPECIFIC reference data that does not exist and must not be fabricated. |

---

## 4. REUSE with no schema change

`calculation_snapshots` (provenance, hash, request-id uniqueness, reportability), `emissions_logs` (reportability lifecycle), `evidence_line_items`, `disclosure_values` / `disclosure_value_evidence` (the reporting projection already filters `reportability_status = 'reportable'`), `activity_clarifications` (versioned adjudication lifecycle), `suppliers` + `supplier_resolution`, `facilities`, `assets`, `manual_extraction_items`, `review_*`, `report_versions` / `report_version_artifacts`, `customer_factors`, `factor_aliases`, `units`, `audit_trail`.

---

## 5. Explicitly NOT changed

* No historical migration is edited.
* No RLS policy is dropped, weakened or replaced.
* No existing column is renamed, retyped or dropped.
* No existing row's value, scope, reportability or category is modified.
* No factor row is inserted, updated or deleted.
* No production migration is applied; no production database is contacted.

---

## 6. Backfill strategy

**None, by design.** Historical Scope 1/Scope 3 rows keep `NULL` method/category. Rationale: the P16 discipline requires that an accounting value's dimensions are never invented after the fact; attributing a category to the 25 historical Scope 3 rows would be a fabricated accounting assertion.

A later, **separately authorised** phase may attribute those rows **only** through the audited clarification/adjudication workflow, with an actor and a reason per row. That work is explicitly out of scope here.

---

## 7. Rollback strategy

| Change | Rollback |
|---|---|
| Additive nullable columns | `DROP COLUMN IF EXISTS` — no pre-existing data is affected |
| `NOT VALID` CHECK constraints | `DROP CONSTRAINT IF EXISTS` — history was never validated, so dropping invalidates nothing |
| Unique indexes | `DROP INDEX IF EXISTS` |
| New tables | `DROP TABLE IF EXISTS` — they hold only P17 data; the nullable FKs on existing tables must be dropped first |
| Seed rows (`scope3_categories`) | `DELETE FROM scope3_categories WHERE category BETWEEN 1 AND 15` — reference data only |

**Rollback ordering** reverses the forward order: dependent FKs and indexes first, then columns, then tables, then seeds.

---

## 8. Tenant / RLS delta summary

| Object | RLS | Policies | Cross-tenant behaviour |
|---|---|---|---|
| `contractual_instruments` | ENABLE | SELECT/INSERT/UPDATE/DELETE org-scoped via `is_org_member(organization_id)` | Deny |
| `instrument_allocations` | ENABLE | same, plus the parent-org equality constraint | Deny |
| `scope3_categories` | ENABLE | SELECT to `authenticated` (org-independent reference data); no write policy | Read-only; holds no tenant data |
| `estimation_records` | ENABLE | org-scoped DML | Deny |
| New columns on existing tables | already ENABLEd | covered by the existing row policies | Unchanged |

No application path may use the service role to bypass tenant isolation.

---

## 9. What the implementing phase must verify (per migration)

1. The migration applies cleanly and **re-running it is a no-op** (idempotent).
2. Before/after: the 34 snapshots and 34 emissions rows are unchanged in every pre-existing column.
3. Each `NOT VALID` constraint **rejects a new invalid insert** (proven by an actual attempt) while accepting the historical rows.
4. RLS is enabled on every new table; `anon` has zero privileges; `authenticated` has DML but not TRUNCATE/TRIGGER/REFERENCES/MAINTAIN.
5. Cross-tenant read and insert are denied on each new table (four-cell matrix).
6. Each unique index holds under a duplicate attempt.
7. No production contact; the migration is applied only to the Demo Lab or a disposable clone, never to a data-bearing environment whose loss matters (invariant F-046-1).

---

## 10. ARCH-02 reconciliation — schema delta amendments

**Authority:** `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md`. These amendments incorporate the PO
decisions on customer-owned data, organization capabilities, the governed lifecycle, acting-for context and the
customer/consultant operating model. **No migration is created by ARCH-02.**

### 10.1 EXISTING — no new entity (removes a previously assumed requirement)

| Requirement | Disposition | Evidence |
|---|---|---|
| consultant ↔ client relationship | **EXISTS — REUSE** (`public.consultant_clients`) | Columns: `id, consultant_id, organization_id, status, relationship_origin, engagement_requested_at, engagement_decided_by, engagement_decided_at, suspended_at, ended_at, ended_by, lifecycle_updated_at, billing_plan, billing_cycle, notes, tags, created_by`. 2 live rows. Used by `data/consultants.py`, `api/consultant_auth.py`, `api/v3_consultants.py`, `api/dependencies.py`, `data/reporting.py`, `api/insight_authz.py`. |
| consultant organization identity | **EXISTS — REUSE** (`consultant_profiles`, `consultant_firm_members`) | 1 profile, 2 firm members. |
| organization membership + role | **EXISTS — REUSE** (`organization_members`: `user_id, role, is_active`) | 8 rows. |
| global/org defaults and retention | **EXISTS — REUSE** (`system_settings`, `organization_metadata`) | Do not duplicate settings storage. |

**Conclusion:** no `consultant_client_relationship` table may be created — it already exists as `consultant_clients`.
The PO's conceptual model maps onto it, with an extension for delegated capabilities (§10.2).

### 10.2 Capability / organization-policy representation (P17-0 decision; recommendation recorded)

An existing **scope-based governance primitive** was discovered:

```
public.manual_processing_grants
  scope_type text CHECK (scope_type IN ('organization','consultant_firm','consultant_client'))
  scope_id   uuid   -- organizations.id | consultant_profiles.id | consultant_clients.id
  enabled    boolean NOT NULL
  reason     text
  set_by     uuid NOT NULL        set_at, updated_at
  UNIQUE (scope_type, scope_id)
```

with the explicit comment: *"The ratified scope vocabulary: no duplicate tenancy concept is invented."*

**Architectural recommendation (not implemented):** represent the PO capability model by adding a **capability-key
dimension** to this ratified three-scope pattern — a sibling table
`organization_accounting_capabilities(scope_type, scope_id, capability_key, enabled, reason, set_by, set_at)` reusing
the same scope vocabulary and the same admin-set + reason semantics — **or**, if P17-0 concludes that
`manual_processing_grants` is the correct single home, extend that table rather than creating a second policy system.
Either way the decision must be taken in P17-0 and recorded before P17-A.

**Prohibited:** a global boolean feature flag; a duplicate policy system; new tenancy vocabulary.

**Capability keys to reconcile at P17-0:** `customer_accounting_enabled`, `scope1_customer_entry`,
`scope2_customer_entry`, `scope3_customer_entry`, `customer_edit_submission`, `customer_upload_evidence`,
`customer_supplier_data`, `customer_review`, `customer_approval`, `staff_review_required`, `staff_approval_required`,
plus the consultant delegated-access keys of UIUX-01 §16 (per-scope data entry, evidence upload, supplier data,
calculations, review, reporting preparation, final reporting approval).

### 10.3 Acting-for / operator-vs-owner context (NEW — implementation dependency)

A `grep` for `acting_for` / `on_behalf` across `backend/**` and `frontend/src/**` returns **no application matches**
(only third-party library code). `audit_trail` carries `performed_by` + `metadata`, and `processing_audit_trail`
carries `performed_by`, `performed_by_staff`, `performed_by_type` — partial actor context exists, but there is **no
acting-for organization dimension**.

Recommended additive columns (nullable; historical rows untouched):

| Table | Column | Purpose |
|---|---|---|
| `calculation_snapshots` | `performed_by_organization_id` (FK organizations, nullable) | the organization the operator represented |
| `calculation_snapshots` | `acting_for_organization_id` (FK organizations, nullable) | the client organization being operated for |
| `emissions_logs` | the same two | consumption-boundary parity |
| audit writer / `audit_trail` | `acting_for_organization_id`, `actor_organization_id` | audit context |
| `evidence_line_items` | `contributed_by_organization_id` (nullable) | who contributed the evidence |

Ownership must remain `organization_id` (the client organization). The acting-for columns are **context**, never
ownership.

### 10.4 Governed lifecycle (EXTEND — do not create a parallel state machine)

UIUX-01 §42 states: *"The exact state machine must follow the accounting contract and existing P16 lifecycle. The UI
must not invent a conflicting lifecycle."* The repository already holds: `customer_documents.status`
(`uploaded|pending|processing|processed|manual_review|verified|approved|rejected|failed`), the
`manual_extraction_items` status flow (`ITEM_STATUS_FLOW`: `mapped → validated → calculated`, plus the automatic
pipeline's `validating`/`calculating`), the `report_versions` lifecycle, and the P16 result reportability triplet
(`reportable | not_for_reporting | superseded`).

**Architectural decision:** the PO lifecycle (`DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED →
REPORTABLE`, with `REJECTED / CORRECTION REQUIRED / INVALIDATED / SUPERSEDED`) is realised by **mapping onto these
existing machines**, with at most additive states where a genuine gap exists (notably explicit `DRAFT`/`SUBMITTED`
submission provenance and an explicit approval gate before a result may become reportable). P17-0 must produce that
mapping table. **No new lifecycle table is proposed by ARCH-02.**

### 10.5 Summary of the ARCH-02 delta

| Item | Disposition |
|---|---|
| consultant-client relationship entity | **EXISTS — REUSE** (`consultant_clients`); no new table |
| capability / policy representation | **P17-0 DECISION** (recommendation: capability-key dimension on the ratified three-scope pattern) |
| acting-for / actor-organization context | **NEW** additive columns on existing tables |
| lifecycle | **EXTEND / MAP** existing state machines; no parallel lifecycle |
| ownership fields | **NO CHANGE** — `organization_id` remains the owner; acting-for is context only |
| audit context | **EXTEND** the existing audit model |
| UI/UX | no schema implication beyond the above; UI is a phase deliverable, not a schema change |
| migrations created by ARCH-02 | **NONE** |





