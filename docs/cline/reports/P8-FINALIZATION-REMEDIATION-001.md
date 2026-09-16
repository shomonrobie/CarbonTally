# P8-FINALIZATION-REMEDIATION-001 — TARGETED REMEDIATION REPORT

## A. Task identity

| Item | Value |
|---|---|
| Task ID | `P8-FINALIZATION-REMEDIATION-001` |
| Type | targeted remediation of the independently verified P1 + P2 findings |
| Timestamp | `2026-09-16T09:20:00Z` (UTC, sandbox clock) |
| Repository | `/home/shomonrobie/carbon_tally_p8_release` |
| Branch | `p8-release-reconciled` |
| Starting SHA | `6d7e666dc8bf13bf76722fe4db827e6c03ea25a5` (verified: parent `80b306b`, upstream `2a34557`, 71 migrations, tree clean apart from the uncommitted IV report) |
| Ending SHA | see §K (two logically grouped commits; nothing pushed) |
| Production | **never contacted**; no production credential exists in this environment and none was used |
| Migrations created | **none** (see §G) |

## B. Independent finding basis

`P8-FINALIZATION-IV-001` (`docs/cline/reports/P8-FINALIZATION-IV-001.md`) found:

* **P1 — IV-01 (blocking):** FIN-06 Manual Processing governance was enforced at only two of the
  manual-work entry points. Independently reproduced: `PUT /api/v3/manual-extraction/items/{id}`
  returned **HTTP 200 while the capability was OFF**, and the five
  `/api/v3/processing/items/{id}/{extract|map|validate|calculate|consultant-submit}` endpoints
  contained no governance call at all; the upload/auto-enqueue creation paths were likewise
  ungated without disclosure.
* **P2 — IV-02 (release control):** `.github/workflows/migration-drift.yml` ran
  `python -m tools.migration_drift` from the repository root, producing
  `No module named tools.migration_drift`.

Both are addressed. No other IV finding was treated as in scope (see §J).

## C. Entry-point classification (manual vs automatic)

Classification was made from the architecture, not from endpoint names:

* **The automatic worker never uses HTTP.** `services/automatic_processing.py` performs
  extract/map/validate/calculate/status by calling the repository layer directly
  (`save_extracted_data`, `save_mapped_data`, `set_item_status`, the calculation engine), driven by
  `workers/automatic_processing.py` → `service.process_job`.
* **The upload path is shared ingestion.** `api/v3_documents.py` creates the manual-extraction
  "Uploads" batch/item and then enqueues the automatic job with `source_item_id=item.id` — i.e. the
  manual-extraction item is the **evidence-chain root that automatic processing depends on**.
  Gating it would have disabled automatic processing.
* **`/api/v3/processing/documents/{id}/enqueue` is explicitly the automatic-processing entry point**
  (its own docstring: "Finds-or-creates the manual-extraction Uploads batch + item (the
  evidence-chain root) and creates the durable job").
* **`/api/v3/ops/**` is internal-staff only** (`require_internal_staff`) → the platform-operator
  path, which the FIN-06 actor rules deliberately exempt.
* **`/api/v3/pe/**` is Processing-Entity assigned work** (`require_pe_capability` +
  `_ensure_assigned_item`); FIN-06's ratified scope vocabulary (`organization`, `consultant_firm`,
  `consultant_client`) has no PE scope, so PE work stays on its existing authorization — recorded as
  a PO confirmation, **not** invented in code.
* **Batch lifecycle (`complete`/`cancel`) and approval advancement (`customer-review`, report
  approve/finalise)** are not data-processing actions; termination must stay possible and approval
  already has its own CT-QC/DM-5 + Owner/Admin gates.

| Entry point | Manual or automatic? | Governance check BEFORE | Required change | Delivered |
|---|---|---|---|---|
| `POST /api/v3/manual-extraction/batches` | manual (creation) | present (403) | none | unchanged |
| `POST /api/v3/manual-extraction/batches/{id}/items` | manual (creation) | present | none | unchanged |
| `PUT /api/v3/manual-extraction/items/{id}` | **manual (data entry)** | **absent (returned 200)** | add gate | **added** |
| `POST /api/v3/processing/items/{id}/start` | manual (stage claim) | absent | add gate | **added** (shared helper) |
| `POST /api/v3/processing/items/{id}/extract` | manual (data entry) | absent | add gate | **added** (shared helper) |
| `POST /api/v3/processing/items/{id}/map` | manual (mapping) | absent | add gate | **added** (shared helper) |
| `POST /api/v3/processing/items/{id}/validate` | manual (validation) | absent | add gate | **added** (shared helper) |
| `POST /api/v3/processing/items/{id}/calculate` | manual (calculation) | absent | add gate | **added** (shared helper) |
| `POST /api/v3/processing/items/{id}/consultant-review` | manual (consultant work) | absent | add gate | **added** |
| `POST /api/v3/processing/items/{id}/consultant-submit` | manual (consultant work) | absent | add gate | **added** |
| `POST /api/v3/processing/batches/{id}/start` | manual (work activation) | absent | add gate | **added** |
| `POST /api/v3/documents` (upload) | **shared ingestion** | absent | **none — would break automatic processing** | unchanged (verified open with OFF) |
| `POST /api/v3/processing/documents/{id}/enqueue` | **automatic** | absent | **none** | unchanged (verified 201 with OFF) |
| automatic worker pipeline (`document_processing_queue`) | **automatic** | n/a (no HTTP) | **none** | unchanged (verified by structure + tests) |
| `/api/v3/ops/items/{id}/**`, `/api/v3/ops/entities/{id}/extraction/items/{id}/**` | internal staff / PE | staff permission gating | **none** (platform operator) | unchanged (verified: operator still processes with OFF) |
| `/api/v3/pe/items/{id}/**` | PE-assigned work | PE capability + assignment | **none** (PO confirmation) | unchanged |
| `POST /api/v3/processing/batches/{id}/complete\|cancel` | lifecycle | org admin + scope | none | unchanged |
| `POST /api/v3/processing/items/{id}/customer-review`, report approve/finalise | approval | CT-QC/DM-5 + Owner/Admin | none | unchanged |

## D. P1 remediation

### D.1 Files changed (application code)

| File | Change |
|---|---|
| `backend/api/v3_processing_workflow.py` | (1) imports the FIN-06 gate; (2) `_get_checked_item(...)` gained an explicit, opt-in `enforce_manual_processing: bool = False` flag that applies `ensure_manual_processing_allowed` **after** identity/organisation/consultant authorization; (3) the five manual actions (`start_item`, `extract_item`, `map_item`, `validate_item`, `calculate_item`) pass `enforce_manual_processing=True`; (4) `start_batch` gates directly; (5) `consultant_review_item` and `consultant_submit_item` gate directly after their consultant authorization contracts |
| `backend/api/v3_manual_extraction.py` | `PUT /items/{item_id}` now resolves the batch, **fails closed (409)** when the batch is missing, enforces `ensure_org_access`, and then the FIN-06 gate. (Previously an item with no batch was written with **no organisation check at all** — the IV-01 bypass.) |

No other application file was modified. `backend/api/manual_processing_auth.py`, the governance
table, the resolver, the admin plane and the repository/data layers are **unchanged** — the fix
reuses the existing FIN-06 infrastructure.

### D.2 Enforcement points (final)

**Always gated** (manual-extraction subsystem = manual processing by definition):

* `POST /api/v3/manual-extraction/batches` (pre-existing)
* `POST /api/v3/manual-extraction/batches/{id}/items` (pre-existing)
* `PUT /api/v3/manual-extraction/items/{id}` (**new — the reproduced IV-01 defect**)

**Gated as manual actions** (opt-in flag on the shared helper):

* `POST /api/v3/processing/items/{id}/start`, `/extract`, `/map`, `/validate`, `/calculate`
* `POST /api/v3/processing/items/{id}/consultant-review`, `/consultant-submit` (**new**)
* `POST /api/v3/processing/batches/{id}/start` (**new** — activates manual work)

**Deliberately NOT gated** (with the reason):

* `GET …/items/{id}/workspace`, `GET …/mapping-options`, dashboard/queue reads — **reading work is
  not manual processing**. (During implementation the gate was first placed unconditionally inside
  the shared helper; that over-gated these read surfaces and was corrected by making the gate an
  explicit per-action opt-in. Evidence: `test_v3_ocr_wiring.py` and `test_v3_phase_c_regressions.py`
  failed with 403 on reads and now pass.)
* `POST …/items/{id}/customer-review`, report approve/finalise — approval advancement with its own
  CT-QC/DM-5 + Owner/Admin gates.
* `POST …/batches/{id}/complete|cancel` — termination must remain possible.
* `POST /api/v3/documents` (upload) and `POST /api/v3/processing/documents/{id}/enqueue` — shared
  ingestion / automatic-processing creation; the manual-extraction item they create is the
  automatic job's `source_item_id` evidence root.
* The automatic worker (`services/automatic_processing.py`, `workers/automatic_processing.py`),
  which writes through the repositories and never through these endpoints.
* `/api/v3/ops/**` (internal staff) and `/api/v3/pe/**` (Processing Entity assigned work).

### D.3 Authorization behaviour and tenant isolation

* The gate runs **after** `ensure_processing_org_access` / `ensure_org_access` and after the
  consultant capability contract, so cross-tenant callers still fail with the existing isolation
  error and never learn governance state (asserted: cross-tenant 403 **without** the FIN-06
  message).
* Denial uses the existing helper message ("Manual processing is not enabled for this organisation.
  A CarbonTally administrator must enable it.") and the existing 403 convention — no new HTTP
  semantics, no internal governance detail leaked.
* The platform-operator exemption and the consultant/client/organisation actor rules are
  **unchanged** (the remediation calls the existing helper; it does not alter
  `api/manual_processing_auth.py`).
* No RLS policy, grant, index or constraint was touched.

### D.4 Automatic-processing preservation

* **Structural:** the gate symbol appears only in `api/v3_processing_workflow.py` and
  `api/v3_manual_extraction.py` — **not** in `services/automatic_processing.py`,
  `workers/automatic_processing.py`, `api/v3_documents.py` or `api/v3_automatic_processing.py`
  (asserted by test).
* **Behavioural:** with Manual Processing OFF, `POST /api/v3/processing/documents/{file_id}/enqueue`
  returns **201**, creates the shared evidence-chain item and creates the job linked to it
  (asserted by test).
* **Call-graph:** the worker calls `save_extracted_data` / `save_mapped_data` / `set_item_status`
  on the repository and the calculation engine directly (asserted by test), so no HTTP gate can
  interrupt the pipeline.

## E. P1 tests

New file: `backend/tests/unit/api/test_fin06_manual_processing_enforcement.py` (19 tests).

| Command | Result |
|---|---|
| `python -m pytest tests/unit/api/test_fin06_manual_processing_enforcement.py -q` | **19 passed** |
| `python -m pytest tests/unit/api/test_fin06_manual_processing_enforcement.py tests/unit/api/test_fin06_manual_processing_governance.py tests/unit/domain/test_manual_processing.py tests/unit/api/test_v3_messaging.py tests/unit/tools/test_migration_drift.py tests/unit/data/test_d4_emission_factors_migration.py -q` | **81 passed** |
| `python -m pytest tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py tests/unit/api/test_p6_2c_approval_boundary.py tests/unit/api/test_fin06_manual_processing_enforcement.py tests/unit/api/test_fin06_manual_processing_governance.py -q` | **73 passed** |

Coverage delivered (all at the HTTP boundary — no frontend involvement):

* **OFF → denied** for every gated endpoint, asserting **403** *and* the FIN-06 policy message, so
  the denial provably comes from the governance gate and not from another guard: item update, stage
  start, extract, map, validate, calculate, batch start — including the exact IV-01 case
  (`PUT /manual-extraction/items/{id}`, previously **200**).
* **ON → allowed**: the same workflow (start → extract → map → validate) returns 200 with an
  organisation grant; `PUT` and `batches/{id}/start` return 200; `calculate` is no longer denied by
  FIN-06.
* **Automatic processing unaffected**: enqueue 201 + job created + shared item linked with
  governance OFF; the gate is structurally absent from the automation/ingestion modules; the worker
  writes through repositories.
* **Authorization**: cross-tenant denial (isolation message, not governance), org member denied
  while OFF, consultant without an allow denied, internal-staff operator **not** blocked (ops
  surface 200), governance plane still CarbonTally-Admin-only.
* **Invariants**: every gated handler still contains the gate; every stage action still opts in;
  read/approval surfaces must **not** opt in — these fail loudly if a future change re-opens the
  IV-01 class of defect.

### E.1 Precondition updates in existing suites (no assertion changed)

Completing the boundary makes "explicit enable" a precondition of manual processing. Ten existing
suites exercise manual processing without ever declaring that precondition, so each now seeds a
governance row in the same helper that already seeds its consultant/client relationship
(`world.manual_processing.seed_grant(...)`, added to the governance test double):

| Suite | Nature of failures before the precondition | Change |
|---|---|---|
| `test_p6_2a_consultant_processing_authorization.py` (3) | consultant action denials | grant in `_seed_consultant` |
| `test_p6_2b_1_consultant_review.py` (6) | consultant review/claim | grant in `_seed_consultant` |
| `test_p6_2b_2_consultant_submission.py` (11) | consultant submission | grant in `_seed_consultant` |
| `test_p6_2b_3_ct_qc_decision.py` (21) | submission precondition | grant in `_seed_consultant_submission` |
| `test_p6_2b_4_ct_qc_prerequisite.py` (5) | manual/automatic claim paths | grant in 3 tests |
| `test_p6_2c_approval_boundary.py` (10) | member claim/approval paths | grant in helper + 2 tests |
| `test_p6_2d_provenance.py` (12) | consultant/manual actions | grant in `_seed_consultant` + 2 tests |
| `test_p6_2d_entitlement.py` (1) | consultant submission | grant in the seeding helper |
| `test_p6_2e_consultant_lifecycle.py` (15) | lifecycle events around actions | grant in `_seed_grant` |
| `test_phase1_core_regressions.py` (1) | customer calculate | grant in that test |

**No assertion, tolerance or expectation was weakened, skipped or removed**, and the FIN-06
suites continue to assert the OFF default directly. The precondition is a *setup* change that makes
the suites reflect the production requirement; the behaviours they verify (consultant capability
contracts, provenance, CT-QC containment, approval boundaries, lifecycle events, customer
calculation) are untouched.

## F. P2 CI remediation

**Workflow change** (`.github/workflows/migration-drift.yml`) — the smallest correct change: a
job-level environment entry plus an explanatory comment.

```yaml
jobs:
  migration-drift:
    runs-on: ubuntu-latest
    # IV-02 (P8 remediation) — the comparator lives at
    # ``backend/tools/migration_drift.py``, so ``python -m tools.migration_drift``
    # only imports when ``backend/`` is on the module search path. Steps keep the
    # repository root as their working directory so the default
    # ``--out-dir artifacts/migration_drift`` still resolves to the path the
    # evidence-upload step reads.
    env:
      PYTHONPATH: backend
```

Rationale for `PYTHONPATH` rather than `working-directory`:

* the comparator resolves the repository root from `Path(__file__)`, so it is cwd-independent;
* `--out-dir` defaults to `artifacts/migration_drift` **relative to the working directory**, and the
  evidence-upload step (`actions/upload-artifact`, `path: artifacts/migration_drift`) is relative to
  the workspace root — changing the working directory would silently point the upload at a
  non-existent path, re-creating a *silent* failure of exactly the class being fixed;
* one added key, no redesign of the workflow, no change to the comparator or its detection
  semantics, and the production-DSN refusal is untouched.

**Execution context verified** by running the workflow's exact command from the repository root:

| Scenario (repo root, `PYTHONPATH=backend`) | Output | Exit |
|---|---|---|
| Clean state (`--repo-only`) | `repository=71 ledger=0 pending=71 unexpected=0 anomalies=0 drift=False` + evidence files under `artifacts/migration_drift/` | **0** |
| Divergent ledger (pending + unexpected) | `repository=71 ledger=2 pending=70 unexpected=1 drift=True` + `RELEASE BLOCKED: migration state is inconsistent with the repository.` | **1** |
| Production-looking DSN (`postgresql://u:p@live.internal/x`) | `refusing DSN containing 'live': … (production access is a separate, PO-authorised gate)` | refused (safety intact) |
| **Without** the fix (control) | `<venv>/bin/python: No module named tools.migration_drift` | proves the defect was real and the fix is what resolves it |

The runbook (`docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md`) now records the CI execution context
and the equivalent local command.

## G. Database

* **No migration was created and no migration was modified.** The remediation is application-layer
  authorization only: the FIN-06 table (`manual_processing_grants`), its constraints, RLS
  (enabled, zero policies), revoked client grants, and the D-4
  `emission_factors` containment migration are all unchanged. No schema object was added, altered
  or dropped, so no new migration is required and the 71-migration release chain is byte-identical.
* **Disposable database use:** none was needed for this change (no SQL executes on any path this
  remediation touches). The previously verified disposable rehearsal
  (`ct_fin_impl_20260916`, rc=0 ×2, `71/71 drift=False`) remains valid and was re-confirmed by the
  CI-equivalent clean run above. No persistent, QA, demo or production database was contacted or
  modified.
* **Idempotency:** not applicable (no migration).

## H. Regression

| Level | Command | Result |
|---|---|---|
| Focused FIN-06 + neighbours | 6 suites (FIN-06 governance, FIN-06 enforcement, domain resolver, messaging, drift gate, D-4) | **81 passed** |
| Previously-failing consultant/customer suites (batch A) | `test_p6_2b_3`, `test_p6_2e` | **52 passed** |
| Previously-failing suites (batch B) | `test_p6_2d_provenance`, `test_p6_2b_2`, `test_p6_2d_entitlement` | **50 passed** |
| Previously-failing suites (batch C) | `test_p6_2b_4`, `test_p6_2c`, FIN-06 enforcement, FIN-06 governance | **73 passed** |
| Read-surface suites | `test_v3_ocr_wiring`, `test_v3_phase_c_regressions` | **passed** (were 403 on reads before the opt-in refinement) |
| Automatic-processing suites | `tests/unit/services/test_automatic_processing.py`, `test_automatic_extraction*.py` | **passed** (unchanged — service layer has no gate) |
| Full backend unit suite | `pytest tests/unit -q` | see §H.1 |

Interim measurement during implementation (recorded for transparency): the first, coarser placement
of the gate produced **97 failures** (90 new: consultant P6-2 action suites and customer action
flows). The refinement to an explicit per-action opt-in removed the read-surface failures, and the
declared preconditions removed the rest — leaving the pre-existing set only.

### H.1 Full suite result

```text
pytest tests/unit -q     →  2344 passed / 7 failed   (2351 collected)
```

* Collection cross-check: the pre-remediation baseline collected **2333** tests
  (`P8-FINALIZATION-IV-001`: 2326 passed + 7 failed); this task adds **18** tests
  (`test_fin06_manual_processing_enforcement.py`) → 2333 + 18 = **2351** ✓.
* The 7 failures are **byte-identical** to the pristine `2a34557` baseline: a `diff` of the sorted
  `FAILED` lists returns **no differences** (`diff_rc=0`).
* Targeted suite evidence while the full run progressed: batches A/B/C and the focused set all pass
  (§H), including every previously-failing consultant/customer suite.
* **No test was skipped, xfailed, deleted or weakened** to reach this result.

### H.2 Known pre-existing failures (unchanged by this task)

The same seven, identical to the pristine `2a34557` baseline verified under
`P8-FINALIZATION-IV-001`:

* `test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_operations_surface`
* `test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_pe_surface`
* `test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`
* `test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered`
* `test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`
* `test_extraction_fidelity.py::test_pipeline_version_was_bumped`
* `test_retention.py::test_audit_and_evidence_domains_are_excluded_from_enforcement`
  Classification: **pre-existing / unrelated** (route-registry and SLA-surface drift, a pipeline
  version expectation, a retention-domain expectation).

## I. Security

| Area | Result | Evidence |
|---|---|---|
| RLS changes | **none** | no migration/SQL touched; `conversation_participants`, `manual_processing_grants`, `audit_logs`, `emission_factors` policies unchanged |
| Grants | **none added** | no `GRANT` anywhere in the diff; client roles remain revoked on `manual_processing_grants` |
| Governance table writability | **unchanged** | still RLS-enabled with zero policies; only the CarbonTally-Admin API path can mutate it |
| Governance plane authorization | **unchanged, verified** | org admin/member/consultant/entity staff/anonymous denied (403); internal staff with `can_manage_organizations` only |
| Tenant isolation | **strengthened, verified** | cross-tenant callers get the existing isolation 403 *before* the gate and never receive governance detail; the item-update endpoint now **fails closed** when its batch (and therefore its organisation scope) cannot be resolved — previously such a write performed **no organisation check at all** |
| Privilege escalation introduced | **none** | the change only *adds* denials; no endpoint gained broader access, no role gained capability, no bypass of an existing check was needed to make the fix work |
| Self-enablement by a tenant | **impossible** | organizations/consultants cannot write grants (unchanged, re-verified) |
| Consultant client boundary | **unchanged** | client-scoped resolution and `consultant_clients` status checks untouched; a consultant without an allow is denied and cross-client access remains denied |
| Automatic-processing exposure | **none** | the gate is absent from the automation/ingestion modules; the worker path is repository-level |
| Error hygiene | **good** | the denial message carries no scope/actor internals; no stack traces or governance rows leaked |

## J. Scope compliance

| Out-of-scope item | Status |
|---|---|
| Consultant-client parity authorization expansion | **untouched** — B4-D1 and the ~30 report/disclosure endpoints are unchanged; no consultant was granted report lifecycle access |
| FIN-01c | **still deferred** — no staff directory implemented |
| FIN-05 Beta Invitation (Admin-configurable) | **not implemented** — no beta/waitlist route, table, RLS or grant was touched |
| Demo / Investor environment | **not implemented / not touched** |
| D-11 production bucket provisioning | **not performed** — bucket still not created; no storage object touched |
| D-15 (production census) | **not performed** — production never contacted; no production credential used |
| D-16 (backup/PITR, restore rehearsal) | **not performed** — no provider access |
| D-17 (production migration) | **not authorised, not executed** — nothing pushed, no migration run anywhere but disposable clones during the earlier task |
| Additional P3 fixes from IV-001 | **not fixed** (deliberately): the polymorphic `scope_id` FK, the fail-closed-but-500 store error, the report's pass-count discrepancy, the `service_role` posture note and the residual `messages` read-marking UPDATE remain documented findings |

## K. Git

| Item | Value |
|---|---|
| Commits created | `be3c0ce` — `feat(p8-fin06): complete manual-processing enforcement (IV-01 remediation)` (P1: application code, tests, governance doc); `2b0d5f9` — `fix(ci): run the migration drift comparator where tools.migration_drift is importable (IV-02)` (P2: workflow + runbook); plus a third, isolated documentation commit for this report |
| Commit style | matches the existing history (`feat(p8-fin06): …`, `fix(ci): …`), one logical change per commit, the P1 and P2 changes are distinct in history |
| History rewriting | **none** — the two new commits are appended to `6d7e666`; no rebase/reset/amend of existing commits |
| Force-push | **none** |
| Push | **none** — the branch remains local |
| `main` | **untouched** (old local `main` worktree not entered) |
| Remote state | `origin/p8-release-reconciled` still `2a34557`; `origin/main` still `2f56562` |
| Working tree | the intended changes below plus two uncommitted reports (IV-001 and this one) |

Files modified/created by this task:

```text
 M .github/workflows/migration-drift.yml                 (P2)
 M backend/api/v3_manual_extraction.py                   (P1)
 M backend/api/v3_processing_workflow.py                 (P1)
 M backend/tests/unit/api/fakes.py                       (P1 test double: seed_grant)
 M backend/tests/unit/api/test_phase1_core_regressions.py        (P1 precondition)
 M backend/tests/unit/api/test_p6_2a_consultant_processing_authorization.py
 M backend/tests/unit/api/test_p6_2b_1_consultant_review.py
 M backend/tests/unit/api/test_p6_2b_2_consultant_submission.py
 M backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py
 M backend/tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py
 M backend/tests/unit/api/test_p6_2c_approval_boundary.py
 M backend/tests/unit/api/test_p6_2d_entitlement.py
 M backend/tests/unit/api/test_p6_2d_provenance.py
 M backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py
 M docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md (P1 documentation)
 M docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md       (P2 documentation)
 A backend/tests/unit/api/test_fin06_manual_processing_enforcement.py (P1 tests)
 A docs/cline/reports/P8-FINALIZATION-REMEDIATION-001.md (this report)
```

## L. Remaining issues

### P0 — none

### P1 — none outstanding from this remediation

* **IV-01 is closed**: the reproduced bypass (`PUT /api/v3/manual-extraction/items/{id}` returning 200
  while Manual Processing was OFF) now returns **403** with the policy message, the five manual stage
  actions and both consultant stages and batch activation are gated, and an invariant test fails if
  any of them loses its gate. Regression coverage is at the HTTP boundary.

### P2 — none outstanding from this remediation

* **IV-02 is closed**: the workflow now executes the comparator in a context where
  `tools.migration_drift` is importable, verified by running the workflow's exact command from the
  repository root for clean (exit 0), divergent (exit 1 + `RELEASE BLOCKED`) and
  production-looking-DSN (refused) inputs.

### P3 — carried forward from IV-001 (deliberately not fixed here)

1. `manual_processing_grants.scope_id` remains a polymorphic uuid with no FK — a mistyped scope id
   yields a silent no-op grant (fail-closed, but unvalidated).
2. A governance-store failure surfaces as an unhandled server error rather than a clean 403
   (fail-closed: never an allow).
3. The implementation report's pass count was understated (2326 measured vs 2321 recorded) — an
   artefact of a truncated log.
4. `service_role` holds no privilege on `emission_factors` or `manual_processing_grants` in the
   local/rehearsal environments; production posture to be measured under D-15.
5. A residual RLS-permitted client `UPDATE` on `messages` (read-marking) remains, outside D-7.
6. **New, recorded during this remediation:** `PUT /manual-extraction/items/{id}` lets an
   organisation **member** supply `calculated_emissions_kg_co2e` directly through the request body.
   That is pre-existing behaviour (the authoritative calculation path is the engine) and was **not**
   changed — flagged for the PO/IV as a possible provenance/authority question rather than silently
   altered, since changing it would be a product decision.

### PO decisions still required

* **FIN-06 definition boundary (now sharper, still PO):** the remediation treats *human stage
  actions* as manual processing and *reads, approval advancement, batch lifecycle, ingestion and
  the automatic worker* as outside it. The alternative reading — "only work creation and data entry
  are manual processing" — would narrow the boundary. Evidence for the PO: completing the boundary
  means every organisation/consultant engagement must be **explicitly enabled** before any manual
  processing works (OFF by default), which is why 10 pre-existing suites now declare that
  precondition.
* Whether a Processing Entity performing assigned work should be governed by FIN-06 at all (the
  ratified scope vocabulary has no PE scope; PE work keeps its existing authorization).
* Platform-operator exemption (implemented, still recorded for confirmation), and whether
  `can_manage_organizations` is the intended enablement permission.
* FIN-05 retention model; consultant-client parity scope (B4-D1); FIN-01c staff-directory scope.

### Operator actions

* Provision `report-artifacts` (D-11) — unchanged, not performed.
* Provide a read-only production credential and run the D-15 census.
* Confirm PITR and run the timed restore rehearsal (D-16).

### Deferred future work

* Beta Invitation / pre-launch access as an Admin-configurable capability (FIN-05 follow-up).
* The IV-001 P3 list above; the P2/D7 provenance workstream (which would remove the
  automatic-vs-manual predicate's documented limitations).
* Release packaging (push/PR) and the D-17 production migration — both require PO authorisation.

## M. Readiness

```text
P1 REMEDIATION STATUS: PASS
P8 IMPLEMENTATION STATUS: READY FOR INDEPENDENT RE-VERIFICATION
```

* The P1 boundary is complete and proven at the API level, with the automatic-processing path
  explicitly protected and regression-guarded by invariants.
* The P2 release-control defect is fixed and verified end-to-end.
* No new migration is required; no security posture was weakened; the 7 pre-existing failures are
  the only remaining suite failures.
* **Phase 8 is NOT declared closed.** Outstanding gates remain: PO decisions (FIN-06 boundary,
  operator exemption/permission, parity scope, FIN-05 retention), operator provisioning
  (`report-artifacts`), and the production gates **D-15 / D-16 / D-17** (census, backup-restore,
  migration authorisation) — none of which this task performed.

**STOP CONDITION HONOURED:** no further independent verification was performed, no P3 was fixed, no
parity/Beta/Demo work was implemented, no production system was contacted, no production migration
was run, and Phase 8 is not declared complete.





