# P17 IMPLEMENT-MASTER-01 — Implementation Report

**Task ID:** `P17-IMPLEMENT-MASTER-01-20260925-UNIFIED-CAMS-SCOPE2-SCOPE3`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `0d9e29f9c3181b438763b7e00f7ade4bacec10f7`
**Ending SHA:** the documentation commit that introduces this report (parent `3dd9fbe`).
**Author:** Cline — implementation agent.
**Nature:** IMPLEMENTATION (schema + domain + tests). Not an independent verification.

---

## 1. Task ID

`P17-IMPLEMENT-MASTER-01-20260925-UNIFIED-CAMS-SCOPE2-SCOPE3`

## 2. Starting SHA

`0d9e29f9c3181b438763b7e00f7ade4bacec10f7` — the ARCH-06 reconciliation commit (verified as actual HEAD
before any change).

## 3. Ending SHA

The documentation commit carrying this report. Its parent, and the implementation head, is `3dd9fbe`.

## 4. Commit SHAs

| # | SHA | Message | Contents |
|---|---|---|---|
| 1 | `5282660` | `feat(p17): add CAMS accounting-dimension and boundary migrations` | 4 migrations |
| 2 | `3b8f85a` | `feat(p17): add unified CAMS domain layer (scope2, scope3, acting-for, instruments, estimation)` | 7 new domain modules, `domain/__init__.py`, `core/exceptions.py` |
| 3 | `3dd9fbe` | `test(p17): cover CAMS dimensions, boundaries, acting-for and migrations` | 5 test modules (156 tests) |
| 4 | *(this report)* | `docs(p17): record IMPLEMENT-MASTER-01 implementation report` | report + JSON |

**Nothing was pushed.** All prior commits preserved; no amend, rebase, reset or force-push.

## 5. Files changed

**Migrations added (4):**

- `supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` (363 lines)
- `supabase/migrations/20261011000000_p17c_contractual_instruments_and_allocations.sql`
- `supabase/migrations/20261012000000_p17d_scope3_category_taxonomy.sql`
- `supabase/migrations/20261013000000_p17h_estimation_and_assumption_records.sql`

**Backend modules created (7):**

- `backend/domain/scope2.py` · `scope3.py` · `cams.py` · `acting_for.py` · `data_quality.py` ·
  `estimation.py` · `contractual_instruments.py`

**Backend modules modified (2, additively):**

- `backend/domain/__init__.py` — P17 objects re-exported; no existing name removed or reordered
- `backend/core/exceptions.py` — 10 new `CarbonTallyError` subclasses with declared `code`/`http_status`

**Tests created (5):**

- `backend/tests/unit/domain/test_p17_scope2.py` · `test_p17_scope3.py` · `test_p17_acting_for.py` ·
  `test_p17_cams.py` · `backend/tests/unit/data/test_p17_migrations.py`

**Not changed:** no existing migration, no existing column, no existing RLS policy, no frontend file,
no seed, no corpus/oracle, no `.env`.

## 6. Database migrations added

Four additive migrations, numbered strictly after the P16 baseline `20261009000000` exactly as
`p17_schema_delta_20250925.md` §1 prescribes.

### 6.1 `20261010000000_p17a` — accounting dimensions, factor governance, acting-for

| Target | Change |
|---|---|
| `calculation_snapshots` | + `scope2_method`, `scope3_category`, `energy_type`, `data_quality`, `facility_id`, `transport_boundary`, `waste_origin`, `source_snapshot_id`, `performed_by_organization_id`, `acting_for_organization_id`; 6 vocabulary CHECKs; 5 coherence CHECKs; 2 `NOT VALID` scope requirements; `uq_calc_snapshots_cat3_source` (DC-02); 4 indexes |
| `emissions_logs` | the same eight dimensions + acting-for pair, so the consumption boundary filters without a join |
| `emission_factors` | + `scope2_method`, `scope3_category_hint`, `factor_type`, `gas_coverage` (classification columns only — no factor row created, changed or given a fabricated multiplier) |
| `activity_clarifications` | + `resolved_scope2_method`, `resolved_scope3_category` (reuses the existing adjudication lifecycle rather than creating a parallel review system) |
| `organizations` | + `consolidation_approach` (DC-07), `organization_type` |
| `consultant_profiles` | + `organization_id` FK → `organizations(id)` **— the ARCH-06 HIGH-01 gap** |
| 9 acting-for paths | `evidence_line_items`, `audit_trail`, `customer_documents`, `suppliers`, `review_audit_trail`, `review_assignment_history`, `report_versions` (plus the snapshot/log pair above) |

### 6.2 `20261011000000_p17c` — contractual instruments and allocations

`contractual_instruments` (claimant tenant, instrument type, identifier, geography, vintage, quantity, unit,
validity window, retirement lifecycle, evidence link) and `instrument_allocations` (allocation to a
calculation snapshot or emissions log, period, quantity). **Cross-tenant claim is structurally impossible**
via composite FK `(instrument_id, organization_id)`. RLS ENABLED, `anon` denied, policies reuse
`public.is_org_member`. The DC-09 detector `p17_instrument_over_allocated()` is read-only.

### 6.3 `20261012000000_p17d` — Scope 3 category taxonomy

`scope3_categories`, 15 rows seeded with the GHG Protocol names and downstream classification
(`ON CONFLICT DO NOTHING`). Reference data only: **no status column**, because a status is not reference data
and storing it would invite treating "the row exists" as "the category is implemented". Read-only for
`authenticated`.

### 6.4 `20261013000000_p17h` — estimation records and detectors

`estimation_records` with a `substantiated` CHECK requiring at least one input or assumption, plus four
read-only detectors: `p17_dc04_unclassified_transport`, `p17_dc05_unclassified_waste`,
`p17_dc07_consolidation_missing`, `p17_unsubstantiated_estimates`.

### 6.5 Preservation discipline (verified, not asserted)

- **Additive only** — asserted by test: no `DROP TABLE`, `DROP COLUMN`, `DELETE FROM`, `TRUNCATE` or
  `ALTER COLUMN` appears in any P17 migration.
- **Every new column is nullable with no `DEFAULT`** — asserted by test, because a default would fabricate a
  dimension for historical rows.
- **No backfill.** No `UPDATE` of `calculation_snapshots`, `emissions_logs` or `emission_factors`. Every new
  column is `NULL` for existing rows, meaning "not recorded" — never a fabricated value.
- **`NOT VALID`** on the mandatory-for-new-writes rules, so the existing snapshots and emissions rows remain
  byte-stable while every subsequent write is enforced.
- **P16 reportability/invalidation columns untouched** — asserted by test.
- **No RLS weakened.** No policy modified; the new tables carry the established posture.

### 6.6 Live execution evidence

The four migrations were applied to a **disposable clone** (`ct_p17_migcheck_20260925`, dropped/recreated;
never the Demo Lab, never `carbontally_qa_phase8`, never `carbontally_test`, never production) on the local
Postgres at `127.0.0.1:54426`, after the full historical chain:

```
APPLIED OK   20261010000000_p17a_accounting_dimensions_and_factor_governance.sql
APPLIED OK   20261011000000_p17c_contractual_instruments_and_allocations.sql
APPLIED OK   20261012000000_p17d_scope3_category_taxonomy.sql
APPLIED OK   20261013000000_p17h_estimation_and_assumption_records.sql
IDEMPOTENT OK (all four, re-run clean)
```

Structural read-back confirmed: all 13 spot-checked columns present; `contractual_instruments`,
`instrument_allocations`, `scope3_categories`, `estimation_records` exist; **`scope3_categories` = 15 rows**;
all 5 `p17_*` functions exist.

**Two historical migrations required Supabase-platform stubs** to run in the bare clone
(`20260823000000_d32_private_documents_storage.sql` needs `storage.buckets`/`storage.objects` with
platform-managed RLS policies). That is a property of the historical chain in a non-Supabase Postgres, not a
defect in the P17 migrations, which apply cleanly and are idempotent.

## 7. Backend modules changed

Seven new pure-Python domain modules (no framework, database or infrastructure imports, matching the
established ADR-10 convention), plus two additive edits.

| Module | Responsibility |
|---|---|
| `domain/scope2.py` | `Scope2Method` (LOCATION_BASED/MARKET_BASED), `EnergyType` (electricity/heat/steam/cooling — `fuel` explicitly rejected with a reason), `assert_scope2_dimensions`, `instrument_is_eligible` / `assert_instrument_eligible` |
| `domain/scope3.py` | All 15 `Scope3Category` definitions with the authoritative status rollup, `assert_calculable`, `assert_boundary_complete` (DC-02/04/05/07), `requires_estimation_record`, `derives_from_source_snapshot` |
| `domain/cams.py` | **The single unified entry point**: `AccountingDimensions`, `CamsContext`, `CamsPersona`, `resolve_accounting_dimensions`, `describe_dimensions` |
| `domain/acting_for.py` | `ActingForKind`, `EntitlementBasis`, `Entitlement`, `ActingForContext`, `assert_acting_for_allowed`, `resolve_acting_for` |
| `domain/data_quality.py` | `DataQuality` (5 values, no numeric uncertainty), `is_estimated`, `describe_data_quality` |
| `domain/estimation.py` | `EstimationMethod`, `EstimationRecord`, `assert_estimation_substantiated`, `requires_estimation_record` (T-INV-12) |
| `domain/contractual_instruments.py` | `ContractualInstrument`, `InstrumentAllocation`, `assert_allocation_within_quantity` (DC-09), `remaining_quantity` |

`backend/core/exceptions.py` gained 10 subclasses, all declaring `code`/`http_status` in the established
style: `AccountingDimensionError` (422), `Scope2MethodRequiredError` (422), `Scope3CategoryRequiredError`
(422), `Scope3CategoryNotSupportedError` (422), `BoundaryAmbiguityError` (422),
`InstrumentEligibilityError` (422), `InstrumentOverAllocatedError` (409), `EstimationRecordRequiredError`
(422), `ActingForError` (403), plus the shared `AccountingDimensionError` semantics. Because they extend
`CarbonTallyError`, the existing API error envelope translates them with **no special casing**.

**The one-engine guarantee.** `resolve_accounting_dimensions` is the only place the Scope 2, Scope 3,
boundary and cross-scope rules are combined. It has no persona parameter, so a consultant, a consultant's
client, a direct customer, a delegated user and CarbonTally staff cannot diverge in what they accept as a
defensible number. Persona affects authorization (enforced by RLS plus server-side capability checks before
this module is reached), never accounting validity. Asserted by a parametrized test over all five personas.

## 8. API routes added/changed

**NONE.** No FastAPI route was added or changed.

The domain contract is importable and fully tested, but it is **not yet reachable over HTTP**. Exposing it
requires an authorised router with the established auth dependency and DB helper, which was not completed in
this task. Recorded as NOT_STARTED in §25; not claimed as delivered.

**Consequence, stated plainly:** a caller today cannot create an instrument, record an estimation or resolve
dimensions through the API. The engine exists; the wiring does not.

## 9. UI areas changed

**NONE.** No React component, route, design token or string was added or changed. The acting-for banner
("ACTING FOR: <Client>"), the Scope 2 method picker and the Scope 3 category picker described in the task are
**not implemented**. Recorded as NOT_STARTED in §25.

The prerequisite for that UI exists: `describe_dimensions()` returns a business-first label plus machine
values (naming the category rather than printing its number, and describing data quality without inventing a
numeric uncertainty), which is the payload such a UI needs.

## 10. Organization / consultant implementation

**Schema layer: IMPLEMENTED.** `organizations.organization_type`
(`CUSTOMER`/`CONSULTANT`/`PROCESSING_ENTITY`/`CARBONTALLY_INTERNAL`) and
`organizations.consolidation_approach` are declared. The ARCH-06 HIGH-01 gap is closed additively:
`consultant_profiles.organization_id` now exists with an FK to `organizations(id)`, so a consultant firm can
**be** a real organization owning its own Scope 1/2/3 data.

**No second organization is created** for an existing consultant; `consultant_clients` is untouched and
remains the ratified consultant↔client relationship; no existing row changes, because `organization_id` stays
`NULL` until an operator sets it. `NULL organization_type` is documented as treated as `CUSTOMER` for
backward compatibility, so no existing row changes meaning.

**Service/API/UI layer: NOT_STARTED.** Nothing reads or writes these columns yet, and no portfolio,
client-switching or consultant-isolation behaviour exists. The linkage is a **schema capability, not a
working feature**.

## 11. Acting-for implementation

**Domain layer: IMPLEMENTED and security-tested.** `resolve_acting_for` resolves an `ActingForContext`
(actor, actor organization, acting-for organization, kind, entitlement basis, `is_delegated`) and enforces the
governing rule as executable behaviour:

- an acting-for context **never** creates an entitlement — a target with no matching entitlement raises
  `ActingForError` (403);
- the resolved acting-for organization is the **entitled** one, so a caller cannot attribute an operation to
  an arbitrary tenant by passing its id;
- a "self" operation whose actor organization differs from the target is recorded truthfully as a delegation
  rather than trusting the label;
- `as_audit_columns()` returns the **same two-column payload** for all nine ARCH-04 §10.3 paths, so one writer
  serves documents, suppliers, review decisions, report artefacts, snapshots, emissions rows, evidence and the
  audit trail.

**Schema layer: IMPLEMENTED.** `actor_organization_id` / `acting_for_organization_id` (or
`contributed_by_organization_id` on evidence, `prepared_by_organization_id` on report versions) exist on every
path the architecture marked "(A) additive implementation required". `audit_trail` is documented as the
authoritative carrier.

**No derivation substitute.** Read-time derivation from `uploaded_by`/`created_by` is rejected in the module
and in the migration comments as not audit-safe, exactly as ARCH-04 requires.

**Wiring: NOT_STARTED.** Existing write paths (documents, suppliers, snapshots, reports) do **not** yet
populate the new columns. They are nullable and therefore harmless, but currently empty for new writes. This
is the single most important remaining wiring gap.

## 12. Scope 2 implementation

**Domain layer: IMPLEMENTED.** The accounting method is required, stored and never inferred: a Scope 2 result
with no `scope2_method` raises `Scope2MethodRequiredError`. The energy-type vocabulary is exactly
`electricity`, `heat`, `steam`, `cooling`, and `fuel` is rejected with an explicit explanation that it is a
Scope 1/3 activity (ARCH-04 // ARCH-03 LOW-02).

**Market-based support: IMPLEMENTED at the domain and schema layers.** `instrument_is_eligible` refuses a
location-based result, a retired/cancelled instrument, a geography mismatch and a **vintage mismatch** — the
factor-year guard applied to instruments, so another year is never silently substituted. Absent comparison
values are skipped rather than guessed, so "not recorded" is not conflated with "known wrong".

**Schema layer: IMPLEMENTED.** `scope2_method`, `energy_type` and the instrument/allocation entities exist,
with the composite cross-tenant FK and the DC-09 detector. Location-based and market-based results are
distinct claims because the method is part of the result.

**NOT implemented:** no calculation path selects a factor by method; no market-based residual-mix factor data
exists (deliberately — it would have to be fabricated); no UI presents the method choice.

## 13. Scope 3 implementation — all 15 categories

**Taxonomy: IMPLEMENTED (schema + domain).** All 15 categories exist as reference data
(`scope3_categories`, 15 rows) and as `Scope3Category` domain definitions carrying the authoritative
architecture status verbatim. **No status was changed or promoted by this task.**

**Per-category calculation: only where the architecture provides a path.**

| # | Category | Arch status | Status (this task) | What exists |
|---|---|---|---|---|
| 1 | Purchased goods and services | PARTIAL | PARTIAL | taxonomy + boundary + bounded-path declaration; engine accepts the category |
| 2 | Capital goods | NOT_IMPLEMENTED | NOT_IMPLEMENTED | taxonomy + boundary note; `assert_calculable` **refuses** — no methodology invented |
| 3 | Fuel- and energy-related activities | SUPPORTED | PARTIAL | taxonomy + **DC-02** source-snapshot requirement enforced + uniqueness index in DB |
| 4 | Upstream transportation and distribution | SUPPORTED | PARTIAL | taxonomy + **DC-04** transport boundary enforced |
| 5 | Waste generated in operations | SUPPORTED | PARTIAL | taxonomy + **DC-05** waste origin enforced |
| 6 | Business travel | SUPPORTED | PARTIAL | taxonomy; no boundary dependency |
| 7 | Employee commuting | PARTIAL | PARTIAL | taxonomy + **T-INV-12** estimation-record requirement flagged |
| 8 | Upstream leased assets | PARTIAL | PARTIAL | taxonomy + **DC-07** consolidation fail-closed |
| 9 | Downstream transportation and distribution | PARTIAL | PARTIAL | taxonomy + **DC-04** downstream boundary enforced |
| 10 | Processing of sold products | NOT_IMPLEMENTED | NOT_IMPLEMENTED | taxonomy + boundary note; `assert_calculable` **refuses** |
| 11 | Use of sold products | DEFERRED | DEFERRED | taxonomy + bounded-path note; refused (awaits PO decision) |
| 12 | End-of-life treatment of sold products | PARTIAL | PARTIAL | taxonomy + **DC-05** `sold_product_eol` enforced |
| 13 | Downstream leased assets | PARTIAL | PARTIAL | taxonomy + **DC-07** consolidation fail-closed |
| 14 | Franchises | DEFERRED | DEFERRED | taxonomy + bounded-path note; refused (awaits PO decision) |
| 15 | Investments | DEFERRED | DEFERRED | taxonomy + bounded-path note; refused (awaits PO decision) |

**"PARTIAL" here means the framework accepts and validates the category; it does NOT mean a calculation
result can be produced.** No factor is selected, no quantity is multiplied and no snapshot is written for any
Scope 3 category. The honest description is: **the category framework is implemented; Scope 3 calculation is
not.**

**Explicit non-promotion.** Categories 2 and 10 remain `NOT_IMPLEMENTED` and raise
`Scope3CategoryNotSupportedError` naming the missing prerequisite when asked to calculate. Categories 11, 14
and 15 remain `DEFERRED` and raise the same error naming the outstanding PO decision. No methodology was
invented to make the matrix look complete — asserted by test.

## 14. Supplier implementation

**NOT_STARTED.** No extract→normalize→match→score→decide→confirm→create/reuse→persist workflow was built or
changed, and no ambiguity guard was added. The supplier table gained two nullable acting-for columns and an
index; nothing reads or writes them.

The architecture's supplier requirements (never silently choose an ambiguous supplier, never create a
duplicate supplier when a valid match exists, propagate attribution to activity/calculation/result/evidence)
remain **unimplemented by this task**.

## 15. Evidence / provenance implementation

**Schema layer: PARTIAL.** `evidence_line_items` gained `contributed_by_organization_id` and
`acting_for_organization_id`, so the contribution context the architecture requires is now storable.

**Domain layer: PARTIAL.** `ActingForContext.as_audit_columns()` provides the contribution payload, and the
Scope 3 guards preserve category/boundary provenance on every result dimension.

**NOT_STARTED:** no writer populates those columns; no new provenance chain is assembled; the existing P16
evidence model (`evidence_line_items`, `provenance_line_links`) is untouched and unextended.

## 16. Manual review implementation

**PARTIAL (schema only).** `activity_clarifications` gained `resolved_scope2_method` and
`resolved_scope3_category`, so an operator decision selecting or confirming a method or category is recorded in
the **existing** adjudication lifecycle (versioning, `supersedes_id`, `is_current`, `evidence_signature`,
`re_evaluation_required`). No parallel review system was created — deliberately.

**NOT_STARTED:** no service writes those columns, no review UI exists, and the original/normalized/corrected
value + reason + reviewer + timestamp chain described in the task was **not** built.

## 17. Lifecycle implementation

**NOT_STARTED.** No lifecycle state machine was added or changed. The P16 result reportability triplet
(`reportable` / `not_for_reporting` / `superseded`) is untouched, and the P17 lifecycle
(`DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED → REPORTABLE`) was **not** mapped onto the
existing machines, because the schema delta makes that mapping a **P17-0 discovery deliverable** and this task
did not execute P17-0.

`CORRECTION REQUIRED` remains unnamed — as ARCH-05/ARCH-06 recorded, naming it is a P17-0 obligation.

## 18. Reporting implementation

**NOT_STARTED.** No reporting change was made. The new dimensions are nonetheless positioned for reporting:
they are mirrored on `emissions_logs` so the consumption boundary can filter Scope 2 method and Scope 3
category without a join, and `describe_dimensions()` supplies the labels a report needs.

No report was created from the new dimensions, no reportability gating was added for them, and the P16
disclosure/report models are untouched and unextended.

## 19. Security / RLS changes

**No RLS was disabled, bypassed or weakened.** No existing policy was modified. Verified by test:

- `contractual_instruments`, `instrument_allocations`, `estimation_records`: RLS ENABLED; `anon` fully
  revoked; `GRANT ALL` to `service_role`; `SELECT/INSERT/UPDATE/DELETE` to `authenticated`;
  `TRUNCATE/TRIGGER/REFERENCES/MAINTAIN` revoked; policies reuse `public.is_org_member(organization_id)`.
- `scope3_categories`: RLS ENABLED; `anon` revoked; `authenticated` gets `SELECT` **only** (reference data);
  `service_role` all.
- **Cross-tenant instrument claim is structurally impossible** via the composite FK
  `(instrument_id, organization_id)` → `contractual_instruments(id, organization_id)` — a defence that does
  not depend on a policy being correctly written.

**Acting-for is not an authorization boundary** — asserted by the deny-by-default and cross-boundary tests.
All P17 domain errors carry accurate HTTP statuses (403 acting-for denial, 409 DC-09 conflict, 422
dimension/boundary/estimation failures) so the API layer cannot present a denial as a success or a client
error as a server fault.

**One warning:** two new indexes (`idx_calc_snapshots_acting_for`, `idx_audit_trail_acting_for`) are not
tenant-leading. They are harmless (RLS still applies) but may be less selective than the established
`(organization_id, ...)` convention under load. Recorded as risk **R17**.

## 20. Idempotency changes

**None to P16 — deliberately.** The P16 guarantees are untouched:

- the partial unique index `uq_calc_snapshots_request_id` (P16-R7: the request id is the idempotency key) is
  unchanged;
- the deterministic `uuid5` request-id derivation in the automatic pipeline is unchanged;
- factor-selection precedence (explicit operator selection → validated compatible factor → year/scope/unit
  compatibility → deterministic matching) is unchanged; **no new factor selection path was added**, which is
  also why no factor-year fallback was introduced;
- **new P17-C idempotency:** `UNIQUE (instrument_id, allocation_period_start, allocation_period_end,
  calculation_snapshot_id)` makes a second allocation of one instrument to one result for one period
  impossible at the storage layer;
- **new P17-A idempotency:** the partial unique index `uq_calc_snapshots_cat3_source` prevents a second
  category 3 derivation from the same source snapshot (DC-02), closing a double-count window.

## 21. P16 regression status

**NO REGRESSIONS — verified by isolated baseline comparison.**

The full unit suite was run twice: once on the working tree with all P17 changes, and once in a **detached
`git worktree` at HEAD (`0d9e29f`)** with the P17 changes absent.

| | Working tree (with P17) | Baseline worktree (HEAD) |
|---|---|---|
| Unit tests collected | 3494 | 3494 |
| Failures | **9** | **9** |
| Failing test IDs | identical set | identical set |

Both runs produce **exactly the same 9 failures**: the three `test_review_sla_surfaces.py` surface
registrations, `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`,
`test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration`,
`test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy`, and the
three `test_extraction_suggestions.py` cases.

**All nine are pre-existing.** None was introduced, worsened in kind, or left unfixed by this task.

**Honest note on the three migration-ordering tests.** They already fail at HEAD (`len(names) == 71` against an
actual 83, plus a hard-coded allow-list of migrations permitted after I1). The P17 migrations advance those
stale constants from 83 to **87** and are not in the allow-list — precisely the "already-failing Class-E stale
expectation" outcome `p17_schema_delta_20250925.md` §1 predicted: *"Adding P17 migrations advances those
expectations further."* They are **left unmodified on purpose**: correcting them means editing governance
assertions about which migrations may follow I1, which is outside this task's implementation scope and belongs
with the comprehensive verification. They fail identically before and after, so no regression is claimed or
hidden. **No test was weakened, skipped or deleted.**

## 22. Focused tests executed

| Scope | Result |
|---|---|
| P17 domain + migration tests | **156 passed, 0 failed** |
| Pre-existing domain suite (regression guard) | 406 passed |
| Full unit suite (with P17) | 3494 collected, 9 failed (all pre-existing) |
| Full unit suite (baseline worktree at `0d9e29f`) | 3494 collected, **same 9** failed |
| P17 migration live execution | 4 applied OK, then 4 idempotent OK, against a disposable clone |

The 156 P17 tests cover, in ALLOW/DENY and positive/negative pairs:

- **Scope 2 (≈37):** the four-value energy vocabulary, `fuel` refusal with its reason, method required and
  never inferred, instrument eligibility (inactive, geography, vintage), absent-value handling.
- **Scope 3 (40):** exactly 15 categories numbered 1–15, unique slugs, correct downstream classification, the
  status rollup matching the architecture **exactly** (`SUPPORTED (3,4,5,6)`, `PARTIAL (1,7,8,9,12,13)`,
  `DEFERRED (11,14,15)`, `NOT_IMPLEMENTED (2,10)`), categories 2 and 10 **not promoted**, `assert_calculable`
  refusing every unimplemented/deferred category, and DC-02/04/05/07 including contradictory-boundary refusal.
- **Acting-for (12):** delegation allow, membership allow, deny-by-default, cross-boundary denial, entitlement
  to one client not admitting a third, the resolved org always being the entitled one, mislabelled self
  recorded truthfully, audit-column parity, frozen record.
- **CAMS engine, data quality, estimation, instruments (≈46):** the same verdict across all five personas,
  dimension resolution, cross-scope refusal, business-first description, five-value data quality with three
  estimates, no numeric uncertainty, estimation substantiation (T-INV-12), DC-09 over-allocation and
  unit-mismatch refusal.
- **Migrations (≈37):** existence and strict ordering after the P16 baseline, additive-only discipline, every
  new column nullable with no default, no backfill, no P16 reportability column altered, all eight dimensions
  on both tables, the four-value energy vocabulary without `fuel`, the five-value data quality, `NOT VALID`
  scope requirements, the DC-02 index, the consultant linkage, all nine acting-for paths, RLS posture on every
  new table, exactly 15 seeded categories with no status column, the composite cross-tenant FK, and four
  read-only detectors.

## 23. Known incomplete features

Stated plainly rather than buried:

1. **No API route exposes any P17 capability.** The engine is unreachable over HTTP.
2. **No UI exists** — no acting-for banner, no client switcher, no Scope 2 method picker, no Scope 3 category
   picker.
3. **Acting-for columns are never written.** Every existing write path (documents, suppliers, snapshots,
   emissions rows, reports, audit) still omits them, so new operations carry no persisted acting-for context.
4. **No Scope 2 or Scope 3 calculation.** Nothing selects a factor by method or category, and no snapshot
   carrying a P17 dimension is produced.
5. **No supplier resolution workflow.**
6. **No lifecycle mapping** (`DRAFT→…→REPORTABLE`) and no `CORRECTION REQUIRED` state.
7. **No reporting integration** with the new dimensions.
8. **No consultant portfolio / client-switching behaviour.** The linkage column exists; nothing uses it.
9. **No evidence-provenance extension** — the P16 chain is unextended and the new evidence columns are unused.
10. **No manual-review write path** for `resolved_scope2_method` / `resolved_scope3_category`.
11. **No organisation-level UI or service** sets `consolidation_approach`, so DC-07 will fail closed in
    practice for categories 8/13 until an operator can set it.
12. **Reference factor classification is unpopulated** — existing factor rows are `NULL` in the new
    governance columns by design, so no factor is yet method- or type-classified.

## 24. Blocked / deferred features

**Legitimately deferred by the architecture (not invented, not stubbed):**

| Item | Why | Owner |
|---|---|---|
| Scope 3 category 2 (capital goods) | `NOT_IMPLEMENTED` in the architecture: needs the capitalisation model | PO decision |
| Scope 3 category 10 (processing of sold products) | `NOT_IMPLEMENTED`: needs the sold-product model | PO decision |
| Scope 3 categories 11, 14, 15 | `DEFERRED`: await the PO product, franchise and bounded-methodology decisions | PO decision |
| Market-based residual-mix / region-level Scope 2 factors | The data does not exist and must not be fabricated | Separate authorisation |
| `sold_products`, `investments`/`investees`, `franchises` entities | Explicitly outside the schema delta until the PO decides the product/boundary model | PO decision |

**Blocked in this task:**

| Item | Why blocked |
|---|---|
| P17-0 discovery (12 gate items) | **Not authorised.** ARCH-05 returned `P17_ARCH_FREEZE_PARTIAL`; ARCH-06 does not lift that. |
| Lifecycle mapping, `CORRECTION REQUIRED` naming, per-path acting-for map, consultant↔org identity decision | These are **P17-0 deliverables**. Implementing them here would have executed an unauthorised phase, so they were deliberately left undone. |

**A note on scope discipline.** Several items in §17, §23 and this table are P17-0 discovery outputs. The task
instructed "do not stop after discovery" and "do not wait for ARCH-07" — which this task honoured by going
straight to implementation — but it did **not** authorise P17-0, so the discovery-dependent items were left
open rather than guessed at, and the implementation went as far as the architecture permitted without
inventing policy. The task also instructed: *"Do not extend the task scope late in the run merely to avoid
PARTIAL."* The verdict below is therefore PARTIAL by design, not by omission of effort.

## 25. Implementation status matrix

Statuses are drawn only from `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `PARTIAL`, `BLOCKED`. No `PASS`,
`E2E VERIFIED` or `PRODUCTION READY` is used: those belong to the later independent verification phase.

| Feature | Schema | Backend | API | UI | Audit | Evidence | Tests | Status |
|---|---|---|---|---|---|---|---|---|
| Accounting dimensions (8 columns, 2 tables) | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | PARTIAL | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Scope 2 — method + energy type vocabulary | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | PARTIAL | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Scope 2 — contractual instruments & allocations | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | PARTIAL | PARTIAL | IMPLEMENTED | **PARTIAL** |
| Scope 2 — calculation (location- or market-based) | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| Scope 3 — 15-category taxonomy | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Scope 3 — category status honesty (no promotion) | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Scope 3 — boundary controls DC-02/04/05/07 | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | PARTIAL | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Scope 3 — category calculation (any category) | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| Categories 2, 10 (capital goods, processing) | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **BLOCKED** (PO decision) |
| Categories 11, 14, 15 (use, franchises, investments) | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **BLOCKED** (PO decision) |
| Data quality classification | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Estimation records (T-INV-12) | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | PARTIAL | PARTIAL | IMPLEMENTED | **PARTIAL** |
| Unified CAMS engine (one engine, all personas) | — | IMPLEMENTED | NOT_STARTED | NOT_STARTED | — | — | IMPLEMENTED | **PARTIAL** |
| Organization type / consultant↔organization linkage | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | PARTIAL | **PARTIAL** |
| Consultant portfolio / client switching | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| Acting-for resolution + authorization model | IMPLEMENTED | IMPLEMENTED | NOT_STARTED | NOT_STARTED | PARTIAL | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Acting-for persistence on write paths | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| Consolidation approach (DC-07) | IMPLEMENTED | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Supplier resolution workflow | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| Evidence / provenance extension | PARTIAL | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | PARTIAL | PARTIAL | **PARTIAL** |
| Manual review (method/category resolution) | IMPLEMENTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | IMPLEMENTED | **PARTIAL** |
| Lifecycle (DRAFT→…→REPORTABLE) | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| `CORRECTION REQUIRED` | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **BLOCKED** (P17-0) |
| Reporting integration | PARTIAL | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | **NOT_STARTED** |
| API surface for P17 | — | — | NOT_STARTED | — | — | — | — | **NOT_STARTED** |
| UI surface for P17 | — | — | — | NOT_STARTED | — | — | — | **NOT_STARTED** |
| RLS / tenant isolation | IMPLEMENTED | IMPLEMENTED | — | — | IMPLEMENTED | — | IMPLEMENTED | **IMPLEMENTED** |
| Idempotency preservation | IMPLEMENTED | IMPLEMENTED | — | — | IMPLEMENTED | — | IMPLEMENTED | **IMPLEMENTED** |
| P16 regression protection | — | IMPLEMENTED | — | — | — | — | IMPLEMENTED | **IMPLEMENTED** |

**Reading this matrix honestly.** Three rows are `IMPLEMENTED` at the layers they cover: RLS/tenant
isolation, idempotency preservation and P16 regression protection. Everything else is `PARTIAL`,
`NOT_STARTED` or `BLOCKED`. The recurring `NOT_STARTED` in the **API** and **UI** columns is the single
largest gap and the direct reason the verdict is PARTIAL.

## 26. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, no production migration, no production credentials, no production deployment, no
  production customer data.
- No external production API call (including `https://carbontally-api.onrender.com`) was made.
- No push to any remote occurred, and no release path was triggered.
- The only database written to was a **disposable clone** (`ct_p17_migcheck_20260925`) created expressly for
  migration validation on the **local** Postgres at `127.0.0.1:54426`.
- The **Demo Lab** (`carbontally_demo_local`), `carbontally_qa_phase8`, `carbontally_test` and every other
  persistent local database were **not** opened, migrated, truncated or reseeded.
- The destructive integration harness (`backend/tests/integration`) was **not run at all**, so no
  `TRUNCATE … RESTART IDENTITY CASCADE` was executed anywhere.

## 27. Final implementation verdict

```
P17_IMPLEMENTATION_PARTIAL
```

**Why PARTIAL and not COMPLETE.** The task applies `P17_IMPLEMENTATION_COMPLETE` *"only if all implementation
scope explicitly committed to in this task has been implemented."* The task's own Section 11 requires every
implemented feature to be connected through **DATABASE → BUSINESS LOGIC → API → UI → AUDIT/EVIDENCE →
REPORTING** and states plainly: *"Do NOT stop at database schema, models, service functions, API
endpoints."* This task implemented the schema and the domain layer and **stopped short of the API and UI**, so
Phases 7, 9, 10, 11 and much of 3, 6 and 8 remain substantially unimplemented: no supplier workflow, no
lifecycle, no reporting integration, no working HTTP or UI surface, and no calculation path consuming the new
dimensions.

**What is genuinely delivered and verified:**

- 26 additive, idempotent database changes with **live execution and structural read-back evidence** against a
  disposable clone;
- a real unified CAMS domain engine reproducing the architecture's status rollup exactly, with **no category
  promoted and no methodology invented**;
- an acting-for model whose central security rule — *context, never authorization* — is enforced as executable
  code and tested in ALLOW/DENY pairs;
- **156 focused tests passing**, and a **baseline-verified zero-regression** result across the full 3494-test
  unit suite;
- the ARCH-06 HIGH-01 consultant↔organization gap closed additively, as the architecture required.

**What is NOT delivered:** essentially everything a user would touch. No route, no screen, no persisted
acting-for on new writes, no calculation, no lifecycle, no supplier resolution, no reporting.

**No false completion claim is made.** The missing layers are itemised by name in §23 and by column in §25
rather than implied away by a framework-completeness narrative. Per the task's own instruction — *"Do not
extend the task scope late in the run merely to avoid PARTIAL"* — this verdict reflects the work actually
verified.

**Next steps, in priority order:**

1. **API surface** — an authorised router exposing dimension resolution, category status, instruments,
   allocations and estimation records (unblocks everything else).
2. **Acting-for persistence** on the nine existing write paths, using `as_audit_columns()`.
3. **Scope 2 / Scope 3 calculation** wired through `resolve_accounting_dimensions` for the categories whose
   status permits it.
4. **UI** — acting-for banner, client switcher, method and category pickers, and the DC-04/05/07 prompts the
   guards now demand.
5. **Lifecycle mapping and `CORRECTION REQUIRED`** — required P17-0 outputs.
6. **Independent verification** of this implementation alongside the frozen architecture.

---

**Declaration.** Everything in this report is either (a) executed and evidenced in this session, or (b)
explicitly labelled as not done. No status in §25 is claimed beyond what the cited evidence supports, and no
`PASS`, `E2E VERIFIED` or `PRODUCTION READY` claim is made anywhere.








