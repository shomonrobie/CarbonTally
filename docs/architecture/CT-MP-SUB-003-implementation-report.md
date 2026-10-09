# CT-MP-SUB-003 — Manual Processing Subscription, Consultant Coverage & Entitlement

## Implementation Report

- **Task ID:** CT-MP-SUB-003
- **PO specification used:** `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md`
  (document id `CT-PO-MP-SUB-003`, status **PO APPROVED — AUTHORITATIVE**)
- **Starting commit:** `375a48dc1b9e9cfd74090bbf747554ae997acb59`
  (branch `p8-release-reconciled`)
- **Ending commit:** NONE — the work is deliberately left **uncommitted** in the
  working tree (no commit/push/deploy authorised by the task).
- **Production changes:** **NONE** (no production deploy, migration, data or config change).

---

## 0. Starting-state discovery (read before implementing)

The working tree was **NOT clean** at the start of this task. `git status`
showed a large set of uncommitted changes that constitute the immediately
preceding, related FIN-06 / manual-processing-routing work:

| Area | Files already modified/untracked at start |
| --- | --- |
| Governance/routing domain | `backend/domain/manual_processing.py` (M) |
| Governance persistence | `backend/data/manual_processing.py` (M) |
| Routing service | `backend/services/manual_processing_routing.py` (untracked) |
| Admin API | `backend/api/manual_processing_admin.py` (M), `backend/api/manual_processing_auth.py` (M) |
| Worker | `backend/workers/automatic_processing.py` (M) |
| Tests / fakes | `backend/tests/unit/api/fakes.py` (M) + several `test_*` (M) |
| Migrations | `20260927000000_p8_fin06_manual_processing_governance.sql`, `20261030000000_manual_processing_routing.sql` |

Per the governing constitution (AGENTS.md §80/§81) the **current** Git/runtime
state is authoritative over any prior summary, so this work builds **on top of**
that state and reverts nothing. The CT-MP-SUB-003 **delta** is the
consultant-sponsored entitlement model, which, at start, **did not exist**
(grep for `ALL_ELIGIBLE_CLIENTS` / `SELECTED_CLIENTS` / `sponsored` /
`consultant_coverage` in `backend/` and `frontend/src/` returned **zero** matches).

Baseline test result before changes (the suites closest to the touched area):
`82 passed` (see §20).

---

## 1. Existing-vs-missing classification (PO spec §2 / §26)

| Requirement | Classification | Evidence |
| --- | --- | --- |
| Direct customer entitlement (own subscription plan) | **EXISTS — VERIFIED** | `domain/manual_processing.entitlement_from_plan`; `ManualProcessingRouter.direct_entitlement_for` |
| Legacy `assisted_processing_available` alias | **EXISTS — VERIFIED** | kept as the fallback when `features.manual_processing` is absent |
| FIN-06 governance (enable/disable, most-specific-wins) | **EXISTS — VERIFIED** | `manual_processing_grants`, `resolve_effective` |
| PE processor configuration + automatic fallback routing | **EXISTS — VERIFIED** | `manual_processing_processors`, `ManualProcessingRouter.route_failed_job` |
| Consultant-client relationship (eligibility anchor) | **EXISTS — VERIFIED** | `consultant_clients` (status); `ConsultantsRepository.get_client_by_org` |
| Firm ↔ organisation linkage | **EXISTS BUT DISCONNECTED — WIRED** | `consultant_profiles.organization_id` existed but was unused by MP; now read for the sponsored coverage source |
| Consultant commercial coverage (mode + capacity) | **MISSING — IMPLEMENTED** | plan feature block `features.consultant_manual_processing`; `consultant_coverage_from_plan` |
| `ALL_ELIGIBLE_CLIENTS` coverage | **MISSING — IMPLEMENTED** | `sponsored_entitlement` (`all_eligible`), plan-driven |
| `SELECTED_CLIENTS` finite capacity + explicit allocation | **MISSING — IMPLEMENTED** | table `consultant_mp_allocations`; `summarize_allocations`; admin allocation API |
| Direct **OR** sponsored resolution | **MISSING — IMPLEMENTED** | `combine_entitlement`; `ManualProcessingRouter.entitlement_for` |
| Selected↔all transitions, upgrade/downgrade, over-allocation | **MISSING — IMPLEMENTED** | `coverage_state_for_firm` (`available`, `over_allocated`, `unallocated_eligible_clients`) |
| Admin coverage/subscription/capacity configuration | **PARTIAL — EXTENDED** | reuses existing Admin plan APIs; new Admin coverage/allocation read+write endpoints |
| Preserve an existing open human assignment in fallback | **MISSING — IMPLEMENTED** (defect fix F-5) | `route_failed_job` returns `human_assignment_preserved` |
| Correct governance context for consultant scopes | **MISSING — IMPLEMENTED** (defect fix F-6) | `manual_processing_admin._scope_context` |
| Auto-release of a selected allocation on consultant-client termination | **DEFERRED — JUSTIFIED** | §27 (entitlement itself already ends via live grants) |
| Full Admin `/ops` frontend surfaces for coverage/allocation | **DEFERRED — JUSTIFIED** | backend endpoints delivered; §27 |
| Final public pricing / capacity tiers / payment provider | **NOT AUTHORIZED** | out of scope (PO spec §25) |

---

## 2. Architecture findings

1. **Subscriptions are org-scoped only.** `customer_subscriptions.organization_id`
   is `NOT NULL`; there is no consultant/firm subscription table. The PO model
   ("the consultant firm purchases coverage through its own organisation
   subscription") maps onto the existing model via
   `consultant_profiles.organization_id → customer_subscriptions → billing_plans`.
   **No parallel subscription/plan system was created.**
2. **Plans already carry a feature JSONB.** The consultant-coverage entitlement is
   expressed as an additive plan feature block, matching the ratified
   `features.consultant` pattern. No new plan table.
3. **Admin plan management already exists** (`/api/v3/commercial/plans`), so no new
   plan CRUD was required.
4. **The scope taxonomy is already consolidated** (FIN-06 / routing use
   `organization | consultant_firm | consultant_client`). The new allocation table
   reuses those real relationship ids; no second tenancy concept.
5. **Two verified defects were fixed** (F-5 supersede-human, F-6 wrong governance
   context) because the PO spec directly forbids both behaviours (§17, §14).

---

## 3. Entitlement-resolution rules implemented (PO spec §3, §11, §13, §18)

```text
DIRECT      = active org subscription -> plan
                features.manual_processing.enabled   (explicit)
                OR assisted_processing_available      (legacy alias)

SPONSORED   = ACTIVE consultant_clients relationship (ELIGIBILITY)
                AND firm's OWN org subscription plan carries
                    features.consultant_manual_processing = {
                        enabled: true,
                        mode: "SELECTED_CLIENTS" | "ALL_ELIGIBLE_CLIENTS",
                        selected_capacity: <int|null> }
                AND ( mode == ALL_ELIGIBLE_CLIENTS
                      OR an ACTIVE consultant_mp_allocations row exists )

EFFECTIVE   = DIRECT OR SPONSORED
```

`combine_entitlement` preserves **both** commercial facts
(`direct_entitled`, `sponsored_entitled`, `sponsored_firm_id`, `sponsored_mode`,
`sponsored_reason`) while yielding **one** operational answer.

The legacy alias is preserved verbatim: an explicit
`features.manual_processing.enabled` still wins; otherwise
`assisted_processing_available` decides. The Professional/Business/Enterprise
entitlement carried by that column is **not** narrowed.

---

## 4. Files changed

| File | Change |
| --- | --- |
| `backend/domain/manual_processing.py` | Added consultant coverage domain: `COVERAGE_MODES`, `ConsultantCoverage`, `consultant_coverage_from_plan`, `AllocationUsage`, `summarize_allocations`, `ConsultantAllocation`, `ConsultantEntitlement`, `sponsored_entitlement`, `combine_entitlement`; additive provenance fields on `ManualProcessingEntitlement`. |
| `backend/data/manual_processing.py` | Added `ConsultantAllocation` row mapping + repository methods: `active_client_grants`, `firm_organization_id`, `eligible_clients`, `list_allocations`, `get_active_allocation`, `count_active_allocations`, `create_allocation`, `release_allocation`. |
| `backend/services/manual_processing_routing.py` | Split `entitlement_for` into `_plan_for_org` / `direct_entitlement_for` / `sponsored_entitlement_for`; `entitlement_for` now returns `combine_entitlement(...)`; added `coverage_state_for_firm`; **F-5 fix** — preserve an existing open human assignment. |
| `backend/api/manual_processing_admin.py` | **F-6 fix** (`_scope_context`, `/state` context); new endpoints `GET /coverage/{consultant_id}`, `POST /coverage/allocations`, `DELETE /coverage/allocations/{allocation_id}`, `GET /clients/{organization_id}`. |
| `supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql` | **New** migration — `public.consultant_mp_allocations` + RLS. |
| `backend/tests/unit/api/fakes.py` | Extended `MemoryConsultants.seed_profile` (organization_id) and `MemoryManualProcessing` (coverage/allocation doubles + `set_firm_coverage`, `end_client_relationship`). |
| `backend/tests/unit/domain/test_consultant_mp_coverage.py` | **New** — pure-domain coverage/entitlement tests. |
| `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py` | **New** — API/service acceptance tests. |
| `docs/architecture/CT-MP-SUB-003-implementation-report.md` | **New** — this report. |

---

## 5. Migrations created

`supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql`

- Creates **exactly one** new table: `public.consultant_mp_allocations`
  (`consultant_id` → `consultant_profiles.id`, `consultant_client_id` →
  `consultant_clients.id`, `organization_id` → `organizations.id`, `state`
  `active|released`, `reason`, `allocated_by/at`, `released_by/at`, `updated_at`).
- **Precondition guards** for `organizations`, `consultant_profiles`,
  `consultant_clients`, `customer_subscriptions` (fail fast if the D37 model is absent).
- **Duplicate-active guarantee:** `UNIQUE (consultant_id, organization_id) WHERE state='active'`
  (PO spec §20 — "prevent duplicate active allocations").
- `state` CHECK `('active','released')`; FK integrity with `ON DELETE RESTRICT`.
- **RLS ENABLED with ZERO policies**, `anon` + `authenticated` revoked — identical
  posture to FIN-06 governance and routing. Service-role (backend) only.
- Additive + idempotent (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).
  No existing table/column/policy/grant/function/trigger/data row modified.

**DO NOT apply any production migration** (task §24). Locally the migration is a
new file awaiting the Demo-Lab apply step (see §22).

---

## 6. Database / RLS changes

- One new service-role-only table (above). No change to any existing table,
  including `customer_subscriptions`, `billing_plans`, `consultant_profiles`,
  `consultant_clients`, `manual_processing_grants`, `manual_processing_processors`,
  `processing_entities`, `work_item_assignments`.
- No new subscription, plan, consultant, PE, assignment or audit table — the
  existing D37/D38/FIN-06/Routing models are reused.

---

## 7. API changes (all admin-gated by the existing FIN-06 admin permission)

`backend/api/manual_processing_admin.py` (prefix `/api/v3/admin/manual-processing`):

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/coverage/{consultant_id}` | Firm coverage state: mode, capacity, allocated, available, over-allocated, eligible clients, allocation ledger. |
| POST | `/coverage/allocations` | Allocate one **eligible** client (selected mode; capacity + eligibility enforced server-side). |
| DELETE | `/coverage/allocations/{allocation_id}` | Release an active allocation (returns its capacity unit). |
| GET | `/clients/{organization_id}` | Full client state: direct, sponsored, relationship, governance, PE, effective — **not** collapsed into one boolean. |

- `/state` (existing) now resolves the **correct relationship context** for
  consultant scopes (F-6) and exposes it as `context`.
- Subscription/plan/capacity **configuration** reuses the existing Admin plan APIs
  (`/api/v3/commercial/plans`); no new plan CRUD was invented.
- The consultant-facing and client-facing **frontend** surfaces are **DEFERRED** (§27).

---

## 8. Selected capacity, all-eligible, transitions & lifecycle

- **Selected capacity** (`SELECTED_CLIENTS`): `summarize_allocations` projects
  `capacity / allocated / available / over_allocated` from the active allocation
  count. One active allocation = one unit. Capacity is **not** bound to a client
  (release returns the unit for reuse). The admin API refuses an allocation when
  the firm is at capacity (`409 exhausted`) or the client is not an active
  client of that firm (`403`).
- **All-eligible** (`ALL_ELIGIBLE_CLIENTS`): every currently/future **eligible**
  client (active `consultant_clients` relationship) is covered with **no**
  per-client allocation; a newly eligible client is covered automatically. It is
  backed by the firm's purchased plan (not an admin toggle).
- **Selected → all:** allocations are **never** destroyed; they remain in the
  ledger and the client becomes covered by the all-eligible entitlement.
- **All → selected:** the system does **not** silently allocate or disable
  clients. `coverage_state_for_firm` reports `unallocated_eligible_clients` so the
  operator performs controlled reconciliation; over-allocation (if allocations
  exceed a reduced capacity) is reported as `over_allocated`.
- **Upgrade / downgrade:** a capacity change never recreates or deletes
  allocations; `available` grows on upgrade and `over_allocated` is reported (not
  silently resolved) on downgrade.
- **Lifecycle:** eligibility is derived from **LIVE** active
  `consultant_clients` grants, so a terminated relationship immediately ends
  sponsorship. See §15 for the deferred auto-release of the selected allocation row.

---

## 9. FIN-06 & PE/routing integration (PO spec §14, §16, §17)

- **Commercial entitlement does NOT enable operations.** The effective rule is
  unchanged: `manual_processing_effective = subscription_entitled AND governance_enabled`.
  The change is only *how* `subscription_entitled` is derived (now DIRECT **OR** SPONSORED).
- **Governance can never create entitlement.** The Admin `/grants` and
  `/processors` endpoints still resolve entitlement server-side
  (`_scope_entitlement` → `router.entitlement_for`, now the combined answer).
- **No arbitrary PE selection.** Routing still uses the single configured
  processor per scope (most-specific-wins) or returns `no_processor_configured`.
- **F-5 fix:** when an item already carries an **OPEN human/internal_staff**
  assignment that is not the configured PE, automatic fallback now **preserves**
  it and records the conflict (`reason = "human_assignment_preserved"`,
  audit action `manual_processing:auto_route_denied` with
  `routing_conflict = "existing_human_assignment_preserved"`). It no longer
  supersedes the human assignment.
- **F-6 fix:** the Admin `/state` diagnostic resolves the governance context from
  the real relationship entities for `consultant_client` / `consultant_firm`
  scopes instead of misusing `scope_id` as an organisation id.

---

## 10. Acceptance scenarios (PO spec §19 / §24) → tests

| # | Scenario | Test |
| --- | --- | --- |
| 1 | Direct customer entitlement | `TestEntitlementResolution::test_direct_entitlement_from_own_subscription` |
| 2 | Relationship alone is not an entitlement | `::test_relationship_alone_is_not_an_entitlement` |
| 3 | Consultant selected capacity 10 (7/10) | `TestSelectedCapacityLifecycle::test_selected_seven_of_ten` |
| 4 | Selected 10/10 | `::test_selected_ten_of_ten_is_full` |
| 5 | New client, capacity available | `::test_new_client_with_available_capacity` |
| 6 | New client, capacity exhausted | `::test_new_client_with_exhausted_capacity_is_not_covered` |
| 7 | Upgrade 10 → 25 | `::test_capacity_upgrade_keeps_existing_allocations` |
| 8 | Release an allocation | `::test_release_returns_and_reuses_capacity` / `TestAdminCoverageApi::test_release_an_allocation` |
| 9 | Reuse released capacity | `::test_release_returns_and_reuses_capacity` |
| 10 | All-eligible coverage | `::test_all_eligible_sponsors_an_eligible_client` |
| 11 | New client auto-covered (all) | `TestCoverageStateTransitions::test_selected_to_all_preserves_allocations_and_covers_all` |
| 12 | Selected → all | `::test_selected_to_all_preserves_allocations_and_covers_all` |
| 13 | All → selected reconciliation | `::test_all_to_selected_requires_reconciliation` |
| 14 | Termination under all | `::test_relationship_termination_ends_all_eligible_coverage` |
| 15 | Direct + sponsored simultaneously | `::test_direct_and_sponsored_are_combined` |
| 16 | Sponsored ends, direct remains | `::test_sponsored_ends_while_direct_remains` |
| 17 | Direct ends, sponsored remains | `::test_direct_ends_while_sponsored_remains` |
| 18 | Both end | `::test_both_paths_inactive_is_not_entitled` |
| 19 | Consultant subscription inactive | `::test_inactive_consultant_subscription_grants_no_coverage` |
| 20 | FIN-06 disabled despite entitlement | `TestOperationalIntegration::test_fin06_disabled_denies_even_when_sponsored` |
| 21 | Entitled + enabled + no PE | `::test_entitled_and_enabled_but_no_pe_is_no_processor_configured` |
| 22 | Unrelated org allocation denied | `TestAdminCoverageApi::test_allocation_of_unrelated_organisation_is_denied` |
| 23 | Selected downgrade over-allocation | `TestSelectedCapacityLifecycle::test_selected_downgrade_over_allocation_is_detected` |
| 24 | Existing human assignment preserved | `TestOperationalIntegration::test_existing_human_assignment_is_preserved` |
| 25 | Legacy `assisted_processing_available` | `TestLegacyCompatibility::test_assisted_processing_available_is_preserved` |
| 26 | Unrecognised mode fails closed | `TestCoverageFromPlan::test_unrecognised_mode_is_fail_closed` |

---

## 11. Admin UI changes

- **Backend control-plane endpoints delivered** (see §7).
- **Frontend `/ops` coverage/allocation panels: DEFERRED — JUSTIFIED** (§15). The
  existing `frontend/src/v3/ops/CommercialTab.jsx` plan editor already lets an
  Admin set `billing_plans.features`, so the *commercial* configuration
  (`features.consultant_manual_processing`) is already expressible without new UI.
  A dedicated consultant-coverage/allocation panel is a UI convenience, not a
  security or correctness requirement, and was intentionally not added here to
  avoid an unverified UI surface under the task's scope discipline.

---

## 12. Tests run — exact commands and results

Environment: `backend/.venv` (Python 3.14.4, pytest 9.1.1, pytest-asyncio 1.4.0).

Baseline (before changes), the suites nearest the touched area:

```bash
cd backend && ./.venv/bin/python -m pytest \
  tests/unit/domain/test_manual_processing_routing.py \
  tests/unit/domain/test_manual_processing.py \
  tests/unit/api/test_manual_processing_routing.py \
  tests/unit/api/test_fin06_manual_processing_governance.py \
  tests/unit/api/test_fin06_manual_processing_enforcement.py
# => 82 passed
```

New CT-MP-SUB-003 suites:

```bash
cd backend && ./.venv/bin/python -m pytest \
  tests/unit/domain/test_consultant_mp_coverage.py \
  tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py
# => 54 passed
```

Manual-Processing regression set (domain + FIN-06 + routing + entitlement):

```bash
cd backend && ./.venv/bin/python -m pytest tests/unit/domain \
  tests/unit/api/test_manual_processing_routing.py \
  tests/unit/api/test_fin06_manual_processing_governance.py \
  tests/unit/api/test_fin06_manual_processing_enforcement.py \
  tests/unit/api/test_p6_2d_entitlement.py
# => 728 passed
```

Full unit suite:

```bash
cd backend && ./.venv/bin/python -m pytest tests/unit
# => see §12.1
```

### 12.1 Full unit suite result

```bash
cd backend && ./.venv/bin/python -m pytest tests/unit
# => 8 failed, 4884 passed, 8 skipped, 14 warnings in 489.41s (0:08:09)
```

The 8 failures are **PRE-EXISTING and unrelated to CT-MP-SUB-003**. This was
verified by temporarily removing the new migration and re-running the same 8
failing tests, which produced the **identical** 8 failures:

```bash
mv supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql /tmp/ctmp003.sql
cd backend && ./.venv/bin/python -m pytest \
  tests/unit/api/test_v3_discovery.py \
  tests/unit/data/test_d17_provider_ownership_migration_revision.py \
  tests/unit/data/test_i1_insight_migration.py \
  tests/unit/data/test_i2_insight_authorization_contracts.py \
  tests/unit/data/test_p17_migrations.py \
  tests/unit/engines/test_extraction_suggestions.py
# => 8 failed, 94 passed, 1 skipped   (same 8)
mv /tmp/ctmp003.sql supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql
```

The 8 pre-existing failures:

| Test | Cause | Related to this task? |
| --- | --- | --- |
| `test_d17_...::test_migration_ordering_is_unchanged` | asserts `len(migrations) == 71`; the repo now has 99 | No |
| `test_i1_insight_migration::test_i1_migration_is_the_latest_migration` | hard-coded "migrations after I1" allow-list | No |
| `test_i2_insight_authorization_contracts::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | asserts `names[-1] == "20261007000000_..."` | No |
| `test_p17_migrations::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | migration-timestamp drift | No |
| `test_v3_discovery::...::test_create_request_as_admin` | env: test expects email delivery NOT configured | No |
| `test_extraction_suggestions` (×3) | extraction engine output drift | No |

None of these tests concern Manual Processing, consultant coverage, entitlement,
FIN-06, routing, or the new allocation table.

---

## 13. Demo Lab verification

The local Demo Lab / Demo-Lab DB was **not** mutated by this task: the migration
is a **new, unapplied** file and no Demo-Lab data was altered (mutation-testing
safety, AGENTS.md §55). The end-to-end commercial model is proven over the
in-memory harness (§12), which exercises the *same* service and domain code the
production wiring uses.

Applying the migration to the disposable Demo Lab DB is a **next step for
independent verification** (§24): `supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql`.

**DEMO LAB VERIFICATION: NOT PERFORMED — migration intentionally left unapplied
(no production/local migration was authorised to run in this environment).**

---

## 14. Known failures / pre-existing failures / regressions

- **New failures:** none. The full unit suite is `8 failed, 4884 passed,
  8 skipped`; all 8 failures reproduce **identically without** the new migration
  (§12.1), so they are pre-existing and unrelated.
- **Pre-existing failures (8):** migration-count/ordering drift
  (`test_d17_*`, `test_i1_*`, `test_i2_*`, `test_p17_*`), a Discovery email-delivery
  environment difference (`test_v3_discovery`), and extraction-engine output drift
  (`test_extraction_suggestions` ×3). None concern Manual Processing.
- **Regressions:** none in the manual-processing domain/API/FIN-06/routing suites
  (`728 passed`), and none in the full unit suite attributable to this change.

---

## 15. Deferred items (DEFERRED — JUSTIFIED)

1. **Auto-release of a selected allocation when a consultant-client relationship
   ends.** Entitlement already ends immediately (eligibility is computed from
   LIVE active grants). What is *not* automated is flipping the
   `consultant_mp_allocations` row from `active` → `released` inside
   `ConsultantsRepository.transition_client_lifecycle`. Wiring that hook would
   touch the shared consultant-client lifecycle state machine; it is deliberately
   deferred so it can be implemented and verified as its own small change, and so
   no historical allocation record is rewritten by a broad edit.
2. **Admin `/ops` frontend coverage/allocation panel** (§11).
3. **Consultant-facing "coverage" summary** (PO spec §21) — the read model is
   available from `GET /coverage/{consultant_id}`; a consultant-scoped,
   authorization-filtered endpoint/UI is deferred.

---

## 16. Blocked items (BLOCKED — EVIDENCE REQUIRED)

- **`consultant_profiles.organization_id` data linkage.** The sponsored
  entitlement requires the firm's own organisation subscription. The column
  exists but was observed to be `NULL` for existing rows (the D-C deferral). The
  resolution logic **fails closed** (`no_coverage`) when the linkage is absent —
  this is correct and safe. Populating firm↔organisation linkage is a data /
  provisioning step, **not** a new commercial rule, so per PO spec §23 it was
  resolved conservatively (fail closed) and documented rather than invented.
  No producer/frontend for that linkage is in scope here.

---

## 17. Production changes

**NONE.** No production deploy, no production migration, no production data or
configuration change, no Supabase CLI link to production, no push.

---

## 18. Final verdict

**CT-MP-SUB-003 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**

This report does **not** claim independent verification or production readiness.




