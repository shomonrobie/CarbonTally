# CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A

**Closing CT-05 gap G-1 — the ratified client-access ceiling on the two remaining
Organisation-plane operations (`approve_final`, `correct_submitted_data`), and the
inert-profile fixture correction it exposed**

- **Date:** 2026-10-08
- **Status:** Implemented and tested — **READY FOR INDEPENDENT VERIFICATION**
  (deliberately not a PO-acceptance verdict; AGENTS.md §73)
- **Closes:** `docs/architecture/CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05.md`
  **§23.1 G-1** — "*`approve_final` and `correct_submitted_data` are classified by
  the ratified §8.2 matrix but are not yet ceiling-bound on the Organisation plane*"
- **Ratified basis (no new business policy is taken here):**
  - `docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md` §8.2 (the client
    capability matrix) and **P-6** ("profile enforcement is SERVER-SIDE"), §8.3
    ("Planes B and C are the same Organisation surface"), §16;
  - `backend/domain/relationship_access.py` — the same pure policy module the
    ceiling and Plane C both call (CT-CONSULTANT-MODEL-IMPLEMENTATION-03);
  - AGENTS.md §14, §17, §25, §44, §45, §65, §70, §72, §73, §74.

---

## 1. Scope

CT-05 (`…-REMEDIATION-05`) made the client-access **profile** a live term of the
Organisation-plane ceiling for exactly two operations — `upload_document`
(`api/upload_gate.py`) and `edit_master_data` (facility/asset/vehicle writes) — and
recorded the two remaining matrix operations as an implementation follow-up (G-1)
rather than a policy question, because the ratified §8.2 matrix already answers
them:

| operation | OFF | READ_ONLY | COLLABORATIVE | MANAGED | RETAINED |
| --- | --- | --- | --- | --- | --- |
| `approve_final` | ✗ | ✗ | ✓ (also client-role gated) | ✗ | ✗ |
| `correct_submitted_data` | ✗ | ✗ | ✓ | ✗ | ✗ |

This task binds **those two operations** on the Organisation-plane routes that
perform them. It changes **no policy**, adds **no capability**, alters **no RLS
policy**, adds **no column/table/index** and writes **no migration** (AGENTS.md
§66): the existing `consultant_clients.client_access_profile` /
`retained_read_only` columns and the existing `api/client_access_guard.py` ceiling
already carried the requirement.

---

## 2. Production changes — five enforcement points

`enforce_client_operation(current_user, repos, organization_id, <operation>)` is
the *same* chokepoint CT-05 introduced; 05A adds five call sites. Each one is
placed **after** every pre-existing authorization decision (identity, tenant,
organisation role, consultant capacity, entitlement) and **before** the first
state check or write, so a denied request is zero-mutation.

| # | Route | Handler | Operation | Ceiling runs |
| --- | --- | --- | --- | --- |
| 1 | `POST /api/v3/processing/items/{item_id}/customer-review` | `api/v3_processing_workflow.py::customer_review_item` | `approve_final` | after `ensure_customer_approval_authority`, before the CT-QC prerequisite, the D37 charge and the `customer_review` / issue / audit / notification writes |
| 2 | `POST /api/v3/processing/items/{item_id}/extract` | `api/v3_processing_workflow.py::extract_item` | `correct_submitted_data` | after `_get_checked_item` (membership + organisation role + consultant capacity + FIN-06 entitlement), before `_require_transition` and `save_extracted_data` |
| 3 | `POST /api/v3/processing/jobs/{job_id}/review` | `api/v3_automatic_processing.py::review_job` | `approve_final` | after `_checked_job` and the `require_org_admin` client-role gate, before `complete_review`, the item stamp and the audit entry |
| 4 | `POST /api/v3/processing/jobs/{job_id}/confirm` | `api/v3_automatic_processing.py::confirm_job` | `correct_submitted_data` | after `_authorize_consultant_job_action(permission="confirm_automation")`, before the stage checks, the correction writes, `reenqueue` and the audit entry |
| 5 | `PUT /api/v3/manual-extraction/items/{item_id}` | `api/v3_manual_extraction.py::update_item` | `correct_submitted_data` | after `ensure_org_access` + `ensure_manual_processing_allowed`, before the `update_item` / audit / notification writes |

Routes 3 and 4 are the automatic-processing mirror of routes 1 and 2 — the same
human decision recorded on the durable job **and** stamped onto the source item —
so they carry the identical ceiling; otherwise the profile would be bypassable by
choosing the automatic pipeline. Route 5 rewrites the organisation's own
`extracted_data`/`mapped_data`, i.e. exactly "correcting submitted data".

The `map` / `validate` / `calculate` / `start` handlers on the same router are
**deliberately left unbound**: `map_factors` / `recalculate` are PO-9
(every-profile-forbidden) and are already refused by the pre-existing role and
entitlement guards, and binding them would broaden CT-05A beyond G-1. This is
pinned by a test (§7, `TestEnforcementCoverageInvariant`).

---

## 3. Frontend reflection (presentation only)

| File | Change |
| --- | --- |
| `frontend/src/v3/customer/ReviewDetailPage.jsx` | `canApprove = isApprover && clientAccess.can('approve_final')`; the Approve/Reject block is gated on it, and a client whose profile forbids final approval sees an explanation ("Your client access level does not permit final approval … you can still review this item, its evidence and its reports") instead of a silently missing control |
| `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | `profileAllowsCorrection` / `profileAllowsApproval` fold into `editableExtraction` and `canDecide` |

Both read the `client_access.capabilities` block of `GET /api/v3/me/context`
(`api/v3_context.py::_client_access_view`, CT-05). The view is **absent** for a
direct customer, a consultant and staff, so their surfaces are unchanged. Nothing
here is authorization: `api/client_access_guard.py` denies the request regardless
of what the browser renders (AGENTS.md §44).

---

## 4. Test-only fixture correction (root cause of the observed failures)

Binding `approve_final` made a **previously inert** test seed operationally
visible. `backend/tests/unit/api/fakes.py::seed_client` is **deny-by-default**
(`client_access_profile="off"`, matching the DB default) — added by
CT-CONSULTANT-MODEL-IMPLEMENTATION-03 (F-3/F-4). Until 05A, no Organisation-plane
route consulted the profile, so a suite that seeded a relationship and then
approved as the client *appeared* to pass. Now the ceiling binds, and those
suites were correctly denied.

Two fixtures were therefore given the profile **the scenario already assumed**
(`collaborative` is the only §8.2 profile that admits `approve_final`, and it is
the profile that models "the client operates its own approval step"):

| File | Change |
| --- | --- |
| `backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py` | `_seed_consultant_submission(..., *, profile="collaborative")` → `world.consultants.seed_client(..., client_access_profile=profile)`; plan features seeded with `manual_processing: {enabled: true}` |
| `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | `_seed_grant(..., *, profile="collaborative")` → explicit `client_access_profile`; explicit manual-processing entitlement; same plan-feature seeding |

**This is a test-fixture correction, not a production change**: no application
behaviour was relaxed to make a test pass, and no assertion was weakened — the
fixtures now *state* the access level the scenario depends on instead of
inheriting a deny-by-default one. Negative/profile-specific cases pass their own
value through the same parameter. Production code contains no reference to these
fixtures.

---

## 5. Tests

### 5.1 Backend — `backend/tests/unit/api/test_ct_client_plane_auth_closure_05a.py` (**new**)

**8 classes, 46 tests, all passing.**

```bash
cd backend && .venv/bin/python -m pytest \
  tests/unit/api/test_ct_client_plane_auth_closure_05a.py -o addopts="" -q
# 46 passed, 1 warning in 10.36s   (exit 0)
```

| Class | Coverage |
| --- | --- |
| `TestRatifiedCeiling` | the §8.2 cells for both operations are read from the ratified policy module, not re-declared |
| `TestApproveFinalCeiling` | `POST …/items/{id}/customer-review`: MANAGED / READ_ONLY / OFF / RETAINED denied (403 + `CLIENT_OPERATION_DENIED_DETAIL`); COLLABORATIVE allowed; direct customer, consultant and staff unaffected |
| `TestApproveFinalJobReviewCeiling` | `POST …/jobs/{id}/review`: same ceiling on the automatic-processing mirror |
| `TestCorrectSubmittedDataCeiling` | `POST …/items/{id}/extract`: same ceiling for corrections |
| `TestManualExtractionUpdateCeiling` | `PUT /api/v3/manual-extraction/items/{id}`: same ceiling |
| `TestConfirmJobCorrectionCeiling` | `POST …/jobs/{id}/confirm`: same ceiling |
| `TestIsolationAndAuthentication` | unauthenticated (401) on both families; foreign organisation decided by the tenant guard, never by the ceiling; the ceiling never *grants* |
| `TestEnforcementCoverageInvariant` | every 05A route binds `enforce_client_operation(...)` for the right operation **and** the call precedes the mutation (source order); `map`/`validate`/`calculate`/`start` stay unbound; the backend still has exactly one client-authorization system |

Every denial test also asserts the **zero-mutation** half: a denied request is
zero workflow, billing, issue, audit and notification change.

### 5.2 Frontend — `frontend/src/v3/__tests__/client-access-closure-05a.test.jsx` (**new**)

**3 suites, 8 tests, all passing** (run through the project's own test runner —
`react-scripts test` — not `jest` invoked directly, which has no CRA Babel config
and reports `Support for the experimental syntax 'jsx' isn't currently enabled`):

```bash
cd frontend && CI=true npx react-scripts test --watchAll=false \
  --testPathPattern='client-access-closure-05a'
# Test Suites: 1 passed, 1 total
# Tests:       8 passed, 8 total
```

| Suite | Tests |
| --- | --- |
| `CT-05A — the ceiling is applied per operation, not as a blanket block` | a capability the profile does not mention still fails **open** in the UI |
| `CT-05A §8.2 approve_final` | a MANAGED client owner is not offered Approve/Reject and is told why; an unrestricted owner keeps them; the review workbench hides the decision controls for a MANAGED client and keeps them otherwise |
| `CT-05A §8.2 correct_submitted_data` | a MANAGED client cannot save a correction and sees the explanation; a COLLABORATIVE client keeps the control; an unrestricted user keeps the control and its historical copy |

---

## 6. Regression status — backend full suite

Three full backend runs were executed during this task; the recorded baseline
failure set is `/tmp/_base_f.txt` (44 entries, the state before the CT-05A fixture
correction).

| Run | Result | Note |
| --- | --- | --- |
| run 1 (ceiling bound, fixtures **not** yet corrected) | `12 failed, 5304 passed, 8 skipped` (649.98s) | 4 failures attributable to CT-05A: `test_p6_2b_3_ct_qc_decision.py::test_org_owner_approves_ct_qc_approved_item_charge_at_approval`, `…::test_rejected_item_cannot_reach_customer_review_or_approval`, `test_p6_2e_consultant_lifecycle.py::test_customer_approval_emits_decision_event_for_firm`, `…::test_customer_rejection_emits_decision_event_only` |
| run 2 (after the fixture correction) | `8 failed, 5309 passed, 8 skipped` (929.21s) | the 4 above cleared |
| run 3 (repeat) | `8 failed, 5309 passed, 8 skipped` | identical set to run 2 |

Baseline comparison (`/tmp/ct05a_bset_cmp.txt`): the 8 remaining failures are a
**strict subset** of the 44-entry baseline set; the "in run 3 but NOT baseline"
section is **empty**. No failure is NEW or CT-05A-caused. The 8 are:

- `tests/unit/engines/test_extraction_suggestions.py` × 3;
- `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`,
  `test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration`,
  `test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy`,
  `test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp`;
- `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
  (the CT-05 §18 F-4 environmental case: a locally-configured email provider makes
  the honest API answer `true` where the test asserts `false`).

No `.sql` migration was authored, modified or renumbered by this task: the five
untracked `supabase/migrations/*.sql` files present in the working tree belong to
earlier tasks (CT-03 / CT-04) and were not touched here, and no **tracked**
migration file is modified. That is consistent with the four migration-order
failures being pre-existing rather than caused by this closure.

The frontend **full** suite was **not** re-run during this task; the only known
failing suite remains `dr007-investor-display-fixes.test.jsx`, proven pre-existing
at HEAD in this document's CT-05 parent (§17/§18 F-3), and CT-05A does not touch
that area (its frontend change is two `can(...)` gates plus one explanation block).

---

## 7. Security verification — ALLOW / DENY

Every cell is decided **server-side** by `api/client_access_guard.py`; the UI
column records only what the presentation layer additionally does.

| Actor (org member) | Route | Operation | Server decision | UI |
| --- | --- | --- | --- | --- |
| Direct customer Owner | `…/customer-review`, `…/jobs/{id}/review` | `approve_final` | **ALLOW** (no relationship row → no ceiling) | controls shown |
| Direct customer Owner | `…/items/{id}/extract`, `PUT /manual-extraction/items/{id}`, `…/jobs/{id}/confirm` | `correct_submitted_data` | **ALLOW** | controls shown |
| **MANAGED client** Owner | all five routes | both operations | **DENY 403** (`CLIENT_OPERATION_DENIED_DETAIL`) | controls hidden **+ explanation** |
| **READ_ONLY client** | all five routes | both operations | **DENY 403** | hidden + explanation |
| **OFF / unknown profile** | all five routes | both operations | **DENY 403** (normalises to `off`) | hidden |
| **RETAINED** (post-relationship read-only) | all five routes | both operations | **DENY 403** | hidden |
| **COLLABORATIVE client** Owner | all five routes | both operations | **ALLOW** (the pre-05A behaviour, unchanged) | controls shown |
| Client Member (non-approver) | approval routes | `approve_final` | **DENY** by the pre-existing client-role gate (runs first) | hidden |
| Consultant principal operating its client | all five routes | both | ceiling returns `None` (not an org member); existing consultant authority decides | controls shown |
| Internal CarbonTally staff | any | any | unchanged bypass | unchanged |
| Processing Entity staff | PE plane | assigned work | unchanged | unchanged |
| Any client user → foreign organisation | any | any | **DENY** by `ensure_org_access` / RLS (ceiling not involved) | n/a |
| Unauthenticated | all five routes | any | **401** | n/a |

Frontend/server independence is preserved: re-enabling a hidden control in
devtools yields the identical `403`.

---

## 8. Negative testing (AGENTS.md §45)

| Negative case | Covered by | Status |
| --- | --- | --- |
| MANAGED client → final approval (item workbench route) | `TestApproveFinalCeiling` + FE suite | **DENY verified (403)** over the real route |
| MANAGED client → final approval (automatic job route) | `TestApproveFinalJobReviewCeiling` | **DENY verified (403)** |
| MANAGED client → correct submitted data (item workbench route) | `TestCorrectSubmittedDataCeiling` | **DENY verified (403)** |
| MANAGED client → correct submitted data (manual-extraction route) | `TestManualExtractionUpdateCeiling` | **DENY verified (403)** |
| MANAGED client → confirm/re-enqueue a job (correction gate) | `TestConfirmJobCorrectionCeiling` | **DENY verified (403)** |
| READ_ONLY / OFF / RETAINED client → any of the five | the class suite above | **DENY verified** |
| A denied request must leave **zero** mutation (workflow, billing, issue, audit, notification) | every denial test | **verified** |
| The ceiling must not restrict a legitimate actor (false positive) | COLLABORATIVE / direct customer / consultant / staff cases | **ALLOW verified** |
| Permission ordering: authorization precedes the mutation | `TestEnforcementCoverageInvariant` (source order) | **verified** |
| No second, parallel client-authorization system exists | `TestEnforcementCoverageInvariant` | **verified** |

Pre-existing boundaries (client→foreign org, client→internal operations,
consultant A→consultant B's client, PE A→PE B, viewer→write) are not re-derived
here; they are covered by the green portions of the full backend suite (§6).

---

## 9. Evidence index

| Evidence | Location |
| --- | --- |
| Backend closure tests (46 passed, exit 0) | `/tmp/ct05a_be_closure_rerun.txt`; `backend/tests/unit/api/test_ct_client_plane_auth_closure_05a.py` |
| Frontend closure tests (8 passed) | `/tmp/ct05a_fe_proper.txt` |
| Full-suite failure delta across three runs | `/tmp/ct05a_fail_delta.txt` |
| Baseline-vs-run-3 set comparison (empty "not baseline" section) | `/tmp/ct05a_bset_cmp.txt`; baseline `/tmp/_base_f.txt` |
| Route-binding anchors and router prefixes | `/tmp/ct05a_routes_besum.txt`, `/tmp/ct05a_route_bind.txt` |
| Fixture-correction diffs (test-only) | `/tmp/ct05a_fixture_diffs.txt` |
| `seed_client` deny-by-default definition and its callers | `/tmp/ct05a_seedcallers.txt`, `/tmp/ct05a_fakes_seed.txt` |
| Cross-repo references to this document / the 05A work | `/tmp/ct05a_docrefs.txt` |
| Migration check (no `.sql` file changed) | `/tmp/ct05a_mig.txt` |

These are local evidence paths from the implementing session, recorded for
traceability rather than as artefacts of record. The durable artefacts are the two
test modules and the source anchors in §2.

---

## 10. Limitations / remaining work

| # | Item | Nature |
| --- | --- | --- |
| L-1 | The live-lab browser verifier `tools/demo_lab/verify_ct05_client_plane_auth_browser.py` covers the **CT-05** defect scenario (managed-client upload + master data on the org plane) and does **not** yet carry a CT-05A case. | Verification depth, not a defect. A browser journey is not the cheapest proof here: all five routes load the resource *before* the ceiling is evaluated, so a bogus id yields `404`, not `403` — a denial check needs a real item/job in the right workflow state. The UI half is covered by the 8 frontend tests and the server half by 46 backend tests over the real routers. Extending the verifier (seed a `customer_review` / `review`-stage item for the managed-client identity, then assert hidden controls + `403`) is a follow-up. |
| L-2 | Other profiles (READ_ONLY / COLLABORATIVE / RETAINED) are covered at the API layer, not by a browser journey. | Same as CT-05 §23.1 G-4. |
| L-3 | CT-05 §23.1 **G-2** (member/role administration) and **G-3** (organisation profile / branding writes) remain unbound and remain **PO DECISION REQUIRED** — the ratified §8.2 matrix has no operation covering them. | Unchanged by this task; see CT-05 §23.2. The CT-05A invariant test pins that no accidental spill-over occurs on routes outside this closure's scope. |

---

## 11. Verdict and Git state

### Verdict

**IMPLEMENTED_AND_TESTED — READY FOR INDEPENDENT VERIFICATION.**

| Statement | Status |
| --- | --- |
| The ratified §8.2 ceiling is enforced server-side on all five Organisation-plane routes that perform `approve_final` / `correct_submitted_data` | **IMPLEMENTED** |
| Backend closure suite (46) + frontend closure suite (8) pass, and the full backend suite's remaining failures are a strict subset of the pre-task baseline | **TESTED** |
| Independent verification (OHD / QA Harness) of the CT-05A routes — including a browser journey if the lab fixture is extended | **NOT YET DONE** |
| Product-Owner acceptance | **NOT CLAIMED** (AGENTS.md §73) |

### Git state

- Branch `p8-release-reconciled`, HEAD `3fec874`. **Nothing was committed, reset,
  stashed, cleaned or force-pushed** (AGENTS.md §70).
- No secrets, tokens, signed URLs or credentials appear in this document or in the
  changes it describes.
- No database object was created or altered, no RLS policy was changed and no
  migration was written.
- The working tree contains this task's changes **plus** pre-existing uncommitted
  work from earlier tasks (CT-03, CT-04, manual-processing coverage, P8
  reconciliation, and the untracked `backend/api/client_access_guard.py` created by
  CT-05); this document does not claim otherwise.

### Recommended independent verification

1. `cd backend && .venv/bin/python -m pytest tests/unit/api/test_ct_client_plane_auth_closure_05a.py -o addopts="" -q`
   → expect `46 passed`.
2. `cd frontend && CI=true npx react-scripts test --watchAll=false --testPathPattern='client-access-closure-05a'`
   → expect `8 passed`.
3. Against the live Demo Lab (the lab serves the backend on its **own** port —
   `tools/demo_lab/lab.py` defines `BACKEND_PORT = 8070`, not 8000 — and the
   frontend on `:3000`): as the MANAGED client identity, confirm the item workbench
   and the review page offer **no** correction or approval control (with the
   explanation shown), and that a direct `POST` to
   `/api/v3/processing/items/{id}/customer-review` returns **403** for that
   identity, while the consultant operating the same client is unaffected.
