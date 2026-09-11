# CarbonTally P6-2C — Approval-Boundary Hardening — Independent Verification Report

1. **Verification Ref:** `CT-P6-2C-IV-20260910-001`
2. **Implementation Contract Ref:** `CARBONTALLY-P6-2C-IC-20260910-001`
3. **Implementation Report Ref/path:** `docs/cline/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_REPORT.md`
   (prompt-history: `docs/cline/prompt-history/CT-P6-2C-IMPL-20260910-001.md`)
4. **Verification date/time:** 2026-09-10, approx. 16:20–16:55 local (Asia/Dhaka +0600).
   Evidence anchor: independent full-suite completion marker `/tmp/iv_full2.done`
   written 16:35 local during this verification.
5. **Verifier role:** Independent Verification Agent (not the implementation agent).
6. **Repository:** `/home/shomonrobie/carbon_tally`, branch `main`,
   HEAD `16391217103b98dcea520070c5a22c68f12fe607` (short `1639121`) — **unchanged**
   before/after verification. Nothing committed, pushed, reverted or cleaned.

---

## 6. Documents inspected

| # | Document |
|---|---|
| 1 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` |
| 2 | `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` |
| 3 | `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` (incl. `## P6-2C Ratified PO Decisions — 2026-09-10`) |
| 4 | `docs/architecture/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md` (§11–§15, §19, §20) |
| 5 | `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` |
| 6 | `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` |
| 7 | `docs/cline/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_REPORT.md` |
| 8 | `docs/cline/prompt-history/CT-P6-2C-IMPL-20260910-001.md` |
| 9 | `docs/cline/prompt-history/CT-P6-2C-RA-20260910-001.md`, `CT-P6-2C-PO-20260910-001.md` |
| 10 | `docs/cline/CARBONTALLY_P6_2A_VERIFICATION_REPORT.md`, `CARBONTALLY_P6_2A_R1_INDEPENDENT_REVERIFICATION_REPORT.md` |
| 11 | `docs/cline/CARBONTALLY_P6_2B_1_…_INDEPENDENT_VERIFICATION_REPORT.md`, `…P6_2B_2…`, `…P6_2B_3…` |
| 12 | `docs/cline/CARBONTALLY_P6_2B_4_CT_QC_PREREQUISITE_IMPLEMENTATION_REPORT.md` |

PO decisions re-read from the register (authoritative product policy):
`PO-P6-2C-D1-20260910` = **A**, `PO-P6-2C-D2-20260910` = **A**,
`PO-P6-2C-D3-20260910` = **A** (all three marked **RATIFIED**).

## 7. Code inspected

**Production (read-only; nothing modified by this verification)**

- `backend/api/v3_processing_workflow.py` — `_STAGE_PERMISSION` (l.80–94),
  `_get_checked_item` (l.160–189), `start_item` (l.355–390),
  `customer_review_item` (l.843–940), `consultant-review` (l.545)
- `backend/domain/partners.py` — `WORKFLOW_STAGES` (l.33), `ITEM_STATUS_FLOW`
  (l.95–112), consultant capability flags (l.160–175)
- `backend/api/processing_mode.py` — `item_is_automatic`, `ensure_manual_ct_qc_prerequisite`
- `backend/api/consultant_auth.py` — `CONSULTANT_PERMISSIONS` mapping (`extract`→`can_extract` l.51, `submit`→`can_submit` l.56), `ensure_consultant_processing_authorized`
- `backend/api/v3_automatic_processing.py` — `review_job` (`POST /jobs/{job_id}/review`, l.466–545)
- `backend/api/v3_operations.py` — ops stage/summary surfaces, `submit-review` (l.1956), `review/*` routes
- `backend/api/v3_pe.py` — PE `pe-review` route (l.371)
- `backend/services/billing.py` — `charge_processing` (l.693), single charge path
- `backend/api/dependencies.py`, `backend/auth.py` (`require_org_admin`), `backend/api/operations_auth.py`
- `backend/data/manual_extraction.py` (item status writes, origins)

**Tests**

- `backend/tests/unit/api/test_p6_2c_approval_boundary.py` (new, 30 tests — inspected;
  **no `monkeypatch`/`patch`/`MagicMock`** anywhere: it drives the real HTTP surface)
- `backend/tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py` (fixture patterns),
  plus P6-2A/P6-2B/P6-1B/P6-1C and the §14 regression suites.

## 8. Files changed by the implementation (independently established)

Established by filesystem mtime windowing (implementation window
`2026-09-10 15:30–16:10`) **and** `git status`, not by trusting the report:

| Path | git | mtime | Role |
|---|---|---|---|
| `backend/api/v3_processing_workflow.py` | ` M` | 15:43:40 | **only production change** (S1 + S2/S3) |
| `backend/tests/unit/api/test_p6_2c_approval_boundary.py` | `??` (new) | 15:48:18 | new focused suite |
| `docs/cline/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_REPORT.md` | `??` (new) | 15:57:17 | report |
| `docs/cline/prompt-history/CT-P6-2C-IMPL-20260910-001.md` | `??` (new) | 15:57:56 | prompt history |

Also inside that window (documentation authoring for the same initiative, not
production code): the P6-2C implementation **contract**, the P6-2C **PO**
prompt-history record, and the P6-2 decision **register** amendment.

`find` over the whole repository for the window returned **no other file** —
in particular no frontend, no schema, no migration, no service, no other API
module and no existing test.

## 9. Files confirmed unchanged (independent evidence)

| File (contract §12 "MUST remain unchanged") | Last modified | Verdict |
|---|---|---|
| `backend/domain/partners.py` | 2026-09-10 13:09:38 | unchanged by P6-2C (13:09 = P6-2B-4 session) |
| `backend/api/processing_mode.py` | 2026-09-10 13:09:42 | unchanged by P6-2C |
| `backend/api/consultant_auth.py` | 2026-09-06 20:20 | unchanged |
| `backend/api/v3_automatic_processing.py` | 2026-09-06 16:01 | unchanged |
| `backend/services/billing.py` | 2026-09-06 20:20 | unchanged |
| `backend/api/v3_pe.py` | 2026-09-04 18:31 | unchanged |
| `backend/api/dependencies.py` | 2026-08-30 18:33 | unchanged |
| `backend/auth.py` | 2026-09-01 11:35 | unchanged |
| `backend/api/v3_operations.py` | 2026-09-10 13:13 | unchanged by P6-2C (P6-2B-4 session) |
| all `supabase/**` (schema / migrations / RLS) | — | `find supabase -newermt 2026-09-10` ⇒ **empty** |
| all existing tests | `test_p6_2b_4_…` = 13:14:00 | unchanged by P6-2C; only the new suite is new today |

The working tree contains a **large pre-existing Phase-6 change set** (657
entries, e.g. `frontend/**`, `tools/carbon_data_factory/**`, `supabase/config.toml`,
`.agents/skills/**`). None of it falls in the P6-2C window and none of it is
attributable to P6-2C.

---

## 10. S1 verification — `calculated → approved` is automatic-processing-only

**Result: PASS (contract-compliant, PO-D1).**

Code (`customer_review_item`, `backend/api/v3_processing_workflow.py` l.880–910),
observed order:

1. `_get_checked_item(...)` → 404 / org isolation (`ensure_processing_org_access`)
2. PE-origin guard (`PROCESSING_ENTITY` ⇒ must be `ct_qc_approved`/`customer_review`/`approved`) → 403
3. `_require_transition(item, target)` → **409** for illegal transitions
4. **P6-2C guard:** `if item.status == "calculated": if not await item_is_automatic(repos, item): 403`
5. P6-2B-4 `ensure_manual_ct_qc_prerequisite(...)` → 403
6. rejection-reason 422, then the **D37 charge** (`charge_processing`, l.920), then mutation + audit

Guard ordering verified: the new guard runs **after** the state-machine check
(409 semantics preserved — independently reproduced: `pending → approved` = 409)
and **before** the CT-QC guard and the D37 charge, so every denial is
zero workflow/billing mutation (independently reproduced: status stayed
`calculated`, ledger unchanged, no item audit entries).

Route-level authorization is `Depends(require_org_admin())` (l.851), so the
transition's existence confers **no** authority. Runtime evidence (independent
probe, own fixtures): manual `calculated` approval → **403**; automatic
`calculated` approval → **200** with exactly one 1-credit charge (500 → 499);
`ct_qc_approved` (manual) approval → **200** (legitimate path intact).

The transition itself was **kept** in `ITEM_STATUS_FLOW` (`calculated → approved`
still reachable only through the authorised paths) as PO-D1 requires; no state
was added, removed or re-typed.

`processing_mode.item_is_automatic` semantics were **not** changed
(`processing_mode.py` mtime 13:09, i.e. untouched by this task); the S1 guard
only *reuses* it. Independent predicate evidence: a `calculated` item whose
automatic job has **no** machine output (`automation_extracted_data is None`)
is still refused (403) — the shortcut cannot be opened by merely attaching a
job record.

## 11. S2 verification — consultant `review` claim requires an existing capability

**Result: PASS (contract-compliant, PO-D2).**

- `_STAGE_PERMISSION` now contains `"review": "submit"` (l.90–94; the comment
  cites PO-P6-2C-D2 and the contract ref).
- `start_item` passes `permission=_STAGE_PERMISSION.get(payload.stage)` into
  `_get_checked_item`, which calls the **canonical** resolver
  `ensure_consultant_processing_authorized(...)` — no duplicated authorization
  logic; `_STAGE_PERMISSION` has exactly **one** consumption site (l.370).
- `submit` resolves to the **existing** `can_submit` flag
  (`api/consultant_auth.py` l.56; the flag is pre-existing, declared in
  `domain/partners.py` l.171 in the P6-2A capability block). **No new
  capability, role, permission or flag was created**; `consultant_auth.py` is
  untouched (2026-09-06).
- Runtime: zero-capability consultant with an active grant ⇒ `review` claim
  **403** (zero mutation, no item audit); consultant **with** `can_submit` ⇒
  **200** and the item advanced to `customer_review`; consultant holding only
  `extract/map/validate/calculate` ⇒ **403**.
- **The gap was real — proven independently (in-memory counterfactual, no file
  changed):** with the `review` key temporarily removed from the map (the
  pre-P6-2C state) the zero-capability consultant claimed `review` ⇒ **200** and
  the item moved to `customer_review`; with the key present ⇒ **403**. This was
  not a 422 dead path (`WORKFLOW_STAGES` already contained `review`).
- Org-member and internal-staff paths are unaffected (member stage claims still
  behave as before; staff `review` claim still requires `can_review` → 403
  without it).

## 12. S3 verification — `source` claim requires `can_extract`

**Result: PASS (contract-compliant).**

- `_STAGE_PERMISSION` contains `"source": "extract"`. `source` is in
  `WORKFLOW_STAGES`, so pre-P6-2C it was a reachable, unguarded consultant claim.
- `extract` maps to the **existing** `can_extract` (`consultant_auth.py` l.51;
  declared `partners.py` l.166). No new capability or privilege.
- Runtime: consultant without `can_extract` ⇒ `source` claim **403**; with
  `can_extract` ⇒ **200** (item `pending → extracting`).
- Counterfactual: with the `source` key removed ⇒ **200** (gap real, now closed).

## 13. S4 verification — Operations / PE parity

**Result: PASS (regression-protected; verified by behaviour, not by expecting a code change).**

- **Operations cannot bypass the approval boundary.** The item-approval route is
  `require_org_admin()`; independent probe: non-admin internal staff (with
  `can_review`/`can_process`) ⇒ **403** and PE-scoped staff identity ⇒ **403**.
- **Ops stage-claim parity.** `POST /api/v3/ops/items/{id}/start` with
  `stage="review"` and staff lacking `can_review` ⇒ **403** (observed).
- **PE cannot bypass.** PE staff on the customer approval route ⇒ **403**;
  PE-origin protection intact (independent probe: an item with
  `processing_origin = PROCESSING_ENTITY` at `calculated` ⇒ **403**, i.e. the
  PE guard still runs *after* the new S1 guard rather than being short-circuited
  by it).
- **No expansion of Operations/PE permissions**: `v3_operations.py` (13:13) and
  `v3_pe.py` (2026-09-04) were not modified in the P6-2C window, and no new
  permission keys appear anywhere (`_STAGE_PERMISSION` is the only map touched,
  single consumption site).

## 14. P6-2B-4 security invariants (regression)

| # | Invariant | Result |
|---|---|---|
| 1 | `reviewed → customer_review` blocked | **PASS** — `review` claim on a `reviewed` item ⇒ **409** (`ITEM_STATUS_FLOW` unmodified, l.109) |
| 2 | Manual work cannot bypass required CT-QC | **PASS** — manual `calculated` ⇒ 403 on the approval route; manual `calculated` + `review` claim ⇒ 403; `can_submit` consultant + manual item ⇒ 403 |
| 3 | CT-QC authority remains restricted | **PASS** — no CT-QC code, capability or route changed; `ct_qc_approved → approved` only after QC |
| 4 | PE-origin guard intact | **PASS** (see §13) |
| 5 | Unauthorised actors cannot approve | **PASS** (see §21 matrix) |
| 6 | State-machine semantics intact | **PASS** — invalid transition ⇒ **409** (previously and now); guard added *after* `_require_transition` |
| 7 | No alternate endpoint bypass | **PASS (with the observation in §23.2)** — job-review route: consultant 403, PE 403, unauthenticated 401, cross-org 403, non-existent job 404, member 403, owner 200 |
| 8 | No actor/identity injection bypass | **PASS** — payload cannot set actor; a consultant identity forged with `organization_id`/`is_org_member` still ⇒ **403** |
| 9 | No cross-firm/cross-org access | **PASS** — cross-org owner 403; cross-firm consultant (valid grant, wrong firm's client) 403 |
| 10 | Denied operations create no mutation | **PASS** — status unchanged, item audit list unchanged, ledger unchanged on every denial tested |
| 11 | Denied operations create no false success audit | **PASS** — no `customer_review`/approval audit entries on denials; a successful consultant review does write its audit entry |

## 15. Billing verification (PO-P6-2C-D3)

**Result: PASS — billing unchanged and not silently resolved.**

- `backend/services/billing.py` mtime **2026-09-06 20:20** (unchanged);
  `find` produced no other billing file in the P6-2C window.
- Exactly **one** charge call site in the workflow module:
  `BillingService(repos).charge_processing(...)` at l.920, inside
  `customer_review_item`, guarded by `if payload.approved:` and with the
  deterministic idempotency key `f"charge:item:{item.id}"`, positioned **after**
  every P6-2C/P6-2B-4/P6-2B guard.
- No new billing path introduced; no existing billing path removed.
- Authorised customer approval retains expected behaviour: automatic approval ⇒
  500 → 499 (single credit), `ct_qc_approved` approval ⇒ 500 → 499.
- Denied operations do not charge: manual `calculated` denial, all unauthorised
  actors, and PE-origin denial each left the ledger at its pre-call value.
- Duplicate approval ⇒ **no double charge** (first 200, second 409 by the
  state machine; ledger stayed 499) — consistent with the deterministic key.
- Automatic `POST /jobs/{job_id}/review` behaviour unchanged: it **stamps
  without charging** (owner 200, ledger stayed 500) — the pre-existing,
  PO-deferred policy was **not** silently changed.

## 16. Provenance / audit verification

**Result: PASS — no weakening.**

- `processing_origin` is **read** by the new guard path only indirectly
  (`item_is_automatic`); the PE-origin guard reads `get_item_origin` and still
  fires (403 on a PE-origin item), so the provenance read path is demonstrably
  live and unaltered.
- Independent probe on an allowed approval: the item's origin record was
  identical before and after (in the fixture it is `None` for a manually uploaded
  item — the point is that P6-2C neither writes nor rewrites provenance).
- `source_item_id` linkage was not touched: `get_by_item(job.source_item_id)`
  remains the lookup used by `item_is_automatic` (automatic items are correctly
  recognised ⇒ 200; non-machine items are not ⇒ 403).
- Audit: approved flow produced its audit entry; **denied** flows produced **no**
  success audit entries (checked both on the approval route and on stage claims).
  No append-only behaviour or audit-helper code was modified.
- No schema/migration/RLS/provenance change exists to weaken the above
  (`supabase/**` untouched; `data/manual_extraction.py` untouched).

## 17. RLS / authentication / authorization verification

**Result: PASS — unchanged boundaries.**

- No RLS, policy, migration or auth change: `find supabase -newermt 2026-09-10`
  is empty; `auth.py`, `dependencies.py`, `operations_auth.py` untouched.
- The frontend was not a factor (no frontend change); every result above was
  obtained through the real HTTP surface server-side.
- Tenant isolation re-proved at runtime: cross-organisation actor ⇒ 403,
  cross-firm consultant ⇒ 403, both with zero mutation.
- Unauthenticated access ⇒ 401 (auth dependency enforced before any logic).

## 18. Focused test results (run independently)

Command (executed by the verifier, from `backend/`):

```
.venv/bin/python -m pytest -q tests/unit/api/test_p6_2c_approval_boundary.py
```

**Actual result: 30 tests, 30 passed, 0 failed/error, EXIT 0.**

The implementation report claimed "30 passed" — **independently reproduced**.
The suite contains 30 `def test_…` functions and uses the real HTTP surface with
**no mocking of the guards**.

## 19. Regression test results (contract §14 group)

The verifier derived its own command from contract §14 rather than copying the
implementation report's, giving **24 suites**:

```
test_p6_2b_4_ct_qc_prerequisite, test_p6_2b_3_ct_qc_decision,
test_p6_2b_2_consultant_submission, test_p6_2b_1_consultant_review,
test_p6_2a_consultant_processing_authorization,
test_p6_2a_r1_b1_automation_confirm_retry,
test_p6bill1_entitlement_and_consultant_commercial,
test_v3_processing_workflow, test_phase1_core_regressions,
test_v3_operations, test_v3_qc, test_processing_origin_qc,
test_v1_2_dual_origin_workflow, test_v3_automatic_processing_jobs,
test_v3_automatic_processing_payload, test_automatic_processing (domain),
test_automatic_processing (services), test_operations_auth,
test_scope_aware_authorization, test_pe_auth, test_billing_core,
test_v3_consultants, test_p6_1b_membership_workspace_authorization,
test_p6_1c_engagement_confirmation
```

**Actual result: 418 tests, 0 failures/errors, EXIT 0.**

Discrepancy explanation (not a failure): the implementation report quoted
"23 suites / 408 tests". Contract §14 lists `test_automatic_processing.py` once,
which exists in **two** locations (`tests/unit/domain/…` and
`tests/unit/services/…`). The verifier ran **both** — the extra
`tests/unit/domain/test_automatic_processing.py` contributes exactly the
10-test difference (408 + 10 = 418). Same suites, same outcome, superset.

## 20. Full unit-suite result (run independently)

```
.venv/bin/python -m pytest -q tests/unit
```

**Actual result: 1,606 tests executed, 0 `F`/`E` progress markers, EXIT 0.**

Evidence: the run's progress output contains 23 progress lines
(22 × 72 dots + 22 dots = **1,606**), no failure/error markers, one pre-existing
environment-only warning (`RequestsDependencyWarning: urllib3 2.7.0 / chardet /
charset_normalizer`, a site-packages issue), and a completion marker with
`EXIT=0`.

The implementation report's "1,606 collected, EXIT 0" and the contract's
baseline of 1,576 + 30 = 1,606 are **independently confirmed**.

## 21. Negative security matrix (independently exercised)

Rows marked "probe" were executed by the verifier's own fixtures (not the
implementer's suite): `/tmp/iv_probe.py`, `/tmp/iv_probe2.py`,
`/tmp/iv_probe3.py`, `/tmp/iv_counterfactual.py`.

| Actor / path | Expected | Observed | Verdict |
|---|---|---|---|
| Consultant ⇒ `approved` | DENIED | 403 (probe 1) | PASS |
| PE ⇒ `approved` | DENIED | 403 (probe 2) | PASS |
| Operations (non-admin internal) ⇒ `approved` | DENIED | 403 (probe 3) | PASS |
| Org member ⇒ `approved` | DENIED | 403 (probe 4) | PASS |
| Viewer ⇒ `approved` | DENIED | 403 (probe 5; route gate `require_org_admin` denies all non-admin roles) | PASS |
| Unauthenticated ⇒ `approved` | 401 | 401 (probe 6) | PASS |
| Cross-org actor ⇒ `approved` | DENIED | 403 (probe 7) | PASS |
| Consultant + zero capability ⇒ `review` claim | DENIED | 403 (probe 8) | PASS |
| Consultant + wrong capability ⇒ `review` | DENIED | 403 (probe 9) | PASS |
| Consultant + `can_submit` ⇒ legitimate `review` | ALLOWED | 200, item → `customer_review` (probe 10) | PASS |
| Consultant without `can_extract` ⇒ `source` | DENIED | 403 (probe 11) | PASS |
| Consultant + `can_extract` ⇒ legitimate `source` | ALLOWED | 200, item → `extracting` (probe 12) | PASS |
| Manual calculated ⇒ automatic approval shortcut | DENIED | 403, zero charge/mutation/audit (probe 13) | PASS |
| Automatic calculated ⇒ authorised approval | ALLOWED | 200, single charge 500→499 (probe 14) | PASS |
| Manual without CT-QC ⇒ customer-review/approval | DENIED | 403 (probes 13, 2d) | PASS |
| `reviewed` ⇒ `customer_review` | 409 | 409 (probe 15) | PASS |
| Invalid transition (`pending → approved`) | EXISTING SEMANTICS (409) | 409 (probe 16) | PASS |
| Actor injection (forged org identity) | DENIED | 403 (probe 17) | PASS |
| Cross-org / IDOR (item + cross-firm grant) | DENIED | 403 (probes 7, 18) | PASS |
| Duplicate approval | NO UNINTENDED DUPLICATE CHARGE | 200 then 409; ledger 499 (probe 19) | PASS |
| Concurrent approval | SAFE / NO BYPASS | Not dynamically exercised — see §26.3 (deterministic idempotency key `charge:item:{id}`) | PASS (limited evidence) |
| Denied operation | NO UNAUTHORIZED MUTATION | status/audit/ledger unchanged (probes 8, 13, 20) | PASS |
| Denied operation | NO FALSE SUCCESS AUDIT | no approval audit entry (probes 8, 13) | PASS |
| Successful operation | EXPECTED AUDIT | consultant-review 200 wrote its audit entry (probe 25) | PASS |
| Provenance (`processing_origin`) | UNCHANGED | identical before/after; PE-origin guard still fires (probes 21, 24) | PASS |
| RLS | UNCHANGED | no `supabase/**` file modified today | PASS |
| Manual item via `/jobs/{id}/review` (no job) | DENIED | 404, no mutation, no charge (probe 2a) | PASS |
| `calculated` + non-machine job ⇒ item approval | DENIED | 403 (probe 2b) | PASS |
| `can_submit` consultant + manual item ⇒ `review` | DENIED | 403 — P6-2B-4 CT-QC still binds (probe 2d) | PASS |
| Consultant / PE / unauthenticated / cross-org ⇒ `/jobs/{id}/review` | DENIED | 403 / 403 / 401 / 403 (probe 3) | PASS |
| Owner ⇒ `/jobs/{id}/review` (automatic path) | ALLOWED, no charge | 200, ledger unchanged (probes 3i, 22) | PASS |
| Counterfactual (pre-P6-2C map): 0-cap consultant ⇒ `review` | (historical 200) | **200** without the fix; item → `customer_review` | gap was real |
| Counterfactual (pre-P6-2C map): 0-cap consultant ⇒ `source` | (historical 200) | **200** without the fix | gap was real |

Independent probe totals: part 1 **25/25 PASS**; part 2 **3/4** (the one "FAIL"
was the verifier's own wrong expectation — §23.2); part 3 **4/5** (the one
"FAIL" was a mis-written probe assertion; the observed 403 *was* the expected
result — §26.4).

## 22. Scope-drift check

**Result: PASS — no scope drift.**

The P6-2C change set is confined to the contract §11 targets: production text
changes exist **only** in `backend/api/v3_processing_workflow.py`; the only new
test is the §13 suite; the only new documents are the report and prompt-history
artefacts. Confirmed **absent**:

- P6-2D / P6-2E / P6-2F, Phase 7, Phase 8 — no related code touched
- UI/UX redesign or E2E UI acceptance — no `frontend/**` file in the window
- billing / subscription redesign — `services/billing.py` unchanged
- schema redesign, migration, RLS redesign — `supabase/**` unchanged
- new roles / capabilities / permissions — none added (one existing map edited)
- automatic-processing redesign — `v3_automatic_processing.py`, workers and
  services unchanged
- provenance / evidence architecture redesign — unchanged
- unrelated refactoring or opportunistic bug fixes — none found
- existing tests modified to make something pass — none

## 23. Findings

### 23.1 Non-blocking — report/actual implementation-window mismatch
The implementation report §3 states "approx. 16:30–17:10 local", whereas the
actual mtimes of every P6-2C artefact fall in **15:43–15:57** local. Purely
documentary (wall-clock recording); no effect on code, tests or security.

### 23.2 Non-blocking — observation: the automatic job-review route does not re-assert `item_is_automatic`
`POST /api/v3/processing/jobs/{job_id}/review` (`api/v3_automatic_processing.py`
l.466, unchanged: mtime 2026-09-06) is gated by `require_org_admin()` +
`_checked_job` org isolation + `job.stage == "review"`, and then stamps the
underlying item approved. It does **not** itself re-evaluate
`processing_mode.item_is_automatic`. Independent observation: an org **owner**
approving a synthetic job at `stage="review"` whose
`automation_extracted_data is None` returned **200**, while the *item* route
correctly refused the same item shape with **403**.

Assessment: this is **pre-existing, unchanged behaviour**; it requires no
unauthorised actor (org owner/admin only — consultant, PE, member and anonymous
are all denied), PO-P6-2C-D1 explicitly designates this route as the
*authorised* automatic approval path, and PO-P6-2C-D3 explicitly defers its
billing policy. It is **out of P6-2C's ratified scope**, not a contract
violation, and was deliberately **not** fixed (verification must not modify
code). Reported for PO awareness. Reachability of the scenario under the real
automatic pipeline was **not** established.

### 23.3 Non-blocking — precision of a report claim
The report's phrasing "zero capabilities ⇒ 403 on the `review` claim (previously
200)" is accurate **only for automatic items**; for a **manual** item the claim
was already refused pre-P6-2C by the P6-2B-4 CT-QC prerequisite. The independent
counterfactual confirms both cases (automatic ⇒ 200 pre-fix; manual ⇒ 403
pre-fix). The implementation is correct; only the report's generality is
imprecise.

## 24. Defects

**None.** No contract requirement failed, no PO decision was violated, and no
security or workflow invariant was found broken by P6-2C.

## 25. Risks

| Risk | Assessment |
|---|---|
| Future edit removes/renames the `review`/`source` map keys | The map is the single enforcement site; the new 30-test suite guards it |
| Future *new* consultant stage claims added without a capability | Absent keys mean no consultant capability check; PO-D2's principle must be re-applied at review time |
| §23.2 observation later found reachable in production | Would become a PO decision, not a P6-2C defect |
| Suite-count drift (23 vs 24) confusing future audits | Documented in §19; benign |

## 26. Evidence limitations

1. **No live Supabase / RLS integration run.** Verification used the repository's
   in-memory repository bundle over the real HTTP surface. The RLS/schema
   conclusion rests on (a) no `supabase/**` file modified and (b)
   organisation-isolation behaviour proven at the API layer — not a
   database-level RLS test.
2. **No browser/E2E UI verification** — explicitly out of P6-2C scope.
3. **Concurrency not stress-tested.** Duplicate approval was exercised
   sequentially (200 then 409, single charge). True parallel requests were not
   generated in the in-memory harness; the deterministic idempotency key
   `charge:item:{item_id}` plus the state-machine precheck are the supporting
   static evidence.
4. **One probe assertion was mis-written** by the verifier
   (`status == (403, 404)` compared an int to a tuple), printing FAIL for the
   cross-org job-review row although the observed 403 *was* the expected result
   with an unchanged ledger. Corrected by inspection.
5. **Probe fixtures are synthetic** — they exercise the real handlers but with
   in-memory repositories, reproducing logic/authorization rather than
   Postgres-level behaviour.

## 27. Final verdict

### P6-2C VERIFIED — PASS WITH NON-BLOCKING FINDINGS

All acceptance requirements pass: contract compliance, PO-D1/D2/D3 compliance,
focused/regression/full-unit test evidence, security-boundary evidence,
regression evidence and scope compliance. The three findings in §23 are
genuinely non-blocking (documentation precision; a pre-existing, admin-only,
PO-deferred observation outside P6-2C's ratified scope).

## 28. Independence statement

This verification was performed **independently**. The implementation agent's
"READY FOR INDEPENDENT VERIFICATION" statement and its test numbers were not
accepted as proof. The verifier (a) re-read the authoritative contract, the PO
register and prior P6-2A/P6-2B evidence; (b) inspected the live source rather
than a diff summary; (c) established the change set from filesystem mtimes and
`git status` rather than from the report; (d) executed the focused, regression
and full unit suites itself; (e) built its **own** HTTP-surface probes with its
own fixtures and matrix, including an in-memory counterfactual that reproduces
the pre-P6-2C behaviour to prove both authorization gaps were real; and (f)
recorded one disagreement with the report's precision (§23.3) and one flaw in
its own probe assertions (§26.4) rather than smoothing them over. No production
code, test, schema, RLS, billing, auth or configuration file was modified by
this verification; the only files created are this report and the mandatory
prompt-history record.






