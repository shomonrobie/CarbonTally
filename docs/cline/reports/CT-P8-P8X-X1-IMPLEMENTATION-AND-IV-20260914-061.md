# CT-P8-P8X-X1 — OPERATIONAL HEALTH (WORKER/QUEUE VISIBILITY + WORKER HEARTBEAT) — IMPLEMENTATION + INDEPENDENT VERIFICATION

**Task:** Phase 8-X `X1` (`…043`) — bounded first release
**Authority:** PO decisions of 2026-09-14 — item 1 (approved bounded set: **worker/queue visibility + health/worker heartbeat**; runtime/deployment introspection excluded), item 2 (provider/production access **deferred**), item 3 (**reuse existing infrastructure first**; assess feasibility before any migration), and the follow-up instruction to *"continue Phase 8-X X1 implementation exactly within the already authorized scope"*
**Date:** 2026-09-14 · **Type:** IMPLEMENTATION + INDEPENDENT VERIFICATION
**Verdict:** **IMPLEMENTED — INDEPENDENTLY VERIFIED — READY FOR PO CLOSURE** (not self-closed)

---

## 1. Scope actually delivered (and nothing else)

| Deliverable | Status |
|---|---|
| M1 **queue/worker visibility** read model + endpoint | **done** |
| M2 **worker heartbeat** (tick write + liveness read) + endpoint | **done** |
| M2 **`/health` pool-path correction** | **done** |
| Runtime/deployment introspection | **NOT built** (excluded by PO item 1) |
| Alerting / X2 | **NOT built** (X1 observes only) |
| Provider console / production DB access | **NOT requested, obtained or used** (PO item 2) |
| New database migration for the heartbeat | **NOT needed** — reuse proved sufficient (see §2) |

## 2. Feasibility outcome (PO item 3) — reuse was sufficient

`docs/architecture/CARBONTALLY_PHASE8X_X1_FEASIBILITY_20260914.md` records that the
authoritative 8-X document itself states M1 needs *"no schema change required"*, and that
**`dashboard_metrics`** (existing, with `expires_at`) supplies heartbeat storage. **No new
migration was created and no separate authorisation gate was triggered.**

## 3. Files changed

| File | Change |
|---|---|
| `backend/domain/operational_health.py` | **new** — pure classification (M1 queue summary; M2 liveness) |
| `backend/data/document_processing.py` | +3 methods on the existing queue repository: `queue_visibility_rows`, `record_worker_heartbeat`, `latest_worker_heartbeat` |
| `backend/api/v3_operations.py` | +2 internal-staff endpoints (below) |
| `backend/workers/automatic_processing.py` | +heartbeat tick on **every** loop tick (including idle ticks) |
| `backend/main.py` | `/health` now also exercises the **asyncpg pool** path |
| `backend/tests/unit/domain/test_operational_health.py` | **new** — 19 pure tests |
| `backend/tests/integration/test_operational_health_x1_runtime.py` | **new** — 5 integration tests |

**No migration. No schema change. No RLS change. No production change.**

## 4. The X1 API surface (exactly two endpoints)

| Endpoint | Authority | Returns |
|---|---|---|
| `GET /api/v3/ops/operational-health/queue` | internal staff only (`require_internal_staff` + `can_view_all`) | aggregate backlog: totals, open vs finished, stage distribution, stuck claims, retry-exhausted, `last_error` count, `workflow_error_count`, oldest waiting age |
| `GET /api/v3/ops/operational-health/worker` | internal staff only | heartbeat identity + `HEALTHY`/`STALE`/**`UNKNOWN`** liveness and age |

Both are **read-only**: the heartbeat is written by the **worker process**, so no API caller
can forge a healthy tick. Responses are aggregate — no per-job customer detail is exposed.
Authority matches the 8-X authority matrix (internal staff, global scope); the frontend is
never the boundary.

## 5. Honesty rules enforced (not merely documented)

* **`UNKNOWN` ≠ healthy.** No tick ever recorded ⇒ `UNKNOWN`; the endpoint never reports a
  healthy worker that has not proved liveness.
* **Liveness reports; it does not act.** No alert is raised and no action is taken — alert
  recipients/thresholds are X2 (`PX-6`) and were not decided here.
* **Malformed tick raises.** An unparseable tick raises rather than silently degrading to
  `UNKNOWN`, so a real fault cannot hide behind an "unknown" state.
* **No invented retention.** The heartbeat maintains exactly **one** current row (update in
  place), so the metric store does not grow per tick and no retention duration had to be invented.
* **No fabricated data.** Every figure comes from columns the queue already persists; an empty
  queue reports honest zeros and `oldest_waiting_age_seconds = null`, never a placeholder.


---

## 6. Independent verification

### 6.1 Test evidence (executed)

| Suite | Where | Result |
|---|---|---|
| `tests/unit/domain/test_operational_health.py` (**new**) | pure, no DB | **19 / 19 PASS** |
| `tests/integration/test_operational_health_x1_runtime.py` (**new**) | disposable clone `ct_x1_20260914` | **5 / 5 PASS** |
| Phase 8 integration regression (report_versions · report_lifecycle · s1s3_iv_invariants · s2_is_current_invariant · X1) | disposable clone | **29 / 29 PASS** |
| `tests/unit/api/test_operations_auth.py` (the ops authority surface I extended) | pure | **18 / 18 PASS** |
| Full `tests/unit` sweep | pure | **2 FAILED — both attributed to `F-X1-2` (pre-existing, *not* X1); see §7.2** |

### 6.2 Independent checks

| # | Check | Evidence | Result |
|---|---|---|---|
| V1 | The two new routes are the **only** new surface | router inspection → `/api/v3/ops/operational-health/queue`, `/api/v3/ops/operational-health/worker` | **PASS** |
| V2 | Heartbeat round-trip on a real database | write → read → classify `HEALTHY` | **PASS** |
| V3 | The heartbeat does not grow the store | 4 writes ⇒ exactly **1** row (no invented retention) | **PASS** |
| V4 | Honest absence | no rows ⇒ `None` and liveness **`UNKNOWN`**, never `HEALTHY` | **PASS** |
| V5 | Queue read model reads only existing columns | returned key set == the 13 declared queue fields; `total_jobs == len(rows)`, `open ≤ total`, `stuck ≤ total` | **PASS** |
| V6 | API contract is aggregate-only | summary key set asserted exactly; no per-job customer detail exposed | **PASS** |
| V7 | **F-046-1 negative control** | suite deliberately pointed at `carbontally_qa_phase8` → harness **refused**, all tests ERRORed before touching data | **PASS (guard holds)** |
| V8 | X1 observes, never acts | classifier returns only `{state,last_tick,age_seconds,stale_after_seconds}`; no alert path exists | **PASS** |
| V9 | Honest edge cases | unclaimed job never "stuck"; completed work never inflates backlog age; `ingested_at` preferred over `created_at` | **PASS** |
| V10 | Compile/import of every changed module | AST + import of domain/data/api/worker/main | **PASS** |

## 7. Findings

### 7.1 `F-X1-1` — **defect found by verification and fixed in scope**

> `latest_worker_heartbeat()` returns the tick from a **JSONB payload** (an ISO-8601 **string**), but the classifier's timestamp coercion accepted only `datetime`/`None` — so the worker-health endpoint would have **raised on its first real read**. The unit tests could not see this; the **integration test did**.
> **Fixed:** `_as_datetime` now parses ISO-8601 (including a trailing `Z`), and still **raises** on unparseable input so a malformed tick can never masquerade as `UNKNOWN`. A unit test locking this exact case was added (the 19th test).

### 7.2 `F-X1-2` — **pre-existing failure, NOT caused by X1 — recorded, not fixed (out of scope)**

`tests/unit/api/test_v3_phase_c_regressions.py::TestCl44MappingOptionsCustomerFactors` → **2 FAILED**:

```
TypeError: MemoryFactors.find_by_activity() got an unexpected keyword argument 'unit_qualifier_tolerant'
  backend/api/v3_processing_workflow.py:1116
```

* **Cause:** the **earlier P2 EF-E remediation** changed the mapping-picker call site to pass `unit_qualifier_tolerant=…`; the in-memory test double `MemoryFactors.find_by_activity()` in `tests/unit/api/fakes.py` was never updated. It is **test-double drift introduced by the closed EF-E batch**.
* **Not X1:** X1 touches `domain/operational_health.py`, `data/document_processing.py`, the appended endpoints in `api/v3_operations.py`, `workers/automatic_processing.py` and `main.py` — **none of which appears in this traceback**, and the failing keyword exists only because of EF-E.
* **Disposition:** recorded as a **real defect requiring a bounded remediation task** (a one-line test-double signature update + re-run) belonging to the EF-E batch's remediation. **Not applied here**, because fixing another batch's test double during X1 would expand X1 beyond the PO's bounded set; the mission rule *"record it for separate disposition"* is applied deliberately.

## 8. Limitations (honest)

* No alerting and no runtime/deployment introspection — excluded by the PO's bounded set; no provider or production access used.
* The queue read model is bounded by `limit` (default 2000, newest-first); with a larger queue the figures describe the window read, not the whole table — stated, not hidden.
* The heartbeat is observational: a dead worker shows an aging `STALE` tick; X1 takes no action.
* Verified on **QA + disposable clones**; production untouched and unauthorised. No browser/E2E pass.
* The full `tests/unit` tree is **not fully green** because of `F-X1-2` (§7.2), a pre-existing EF-E artefact. Reported rather than glossed: **X1's own suites are green and the X1 change set is not implicated.**

## 9. Verdict and status

**X1 (bounded set) — IMPLEMENTED AND INDEPENDENTLY VERIFIED — READY FOR PO CLOSURE.**
Not self-closed: closure is a PO act. X1 does not extend to X2 (alerting), and no `PX` decision has been pre-empted.

## 10. Repository / worktree state

| Item | Value |
|---|---|
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` |
| Migrations added | **none** (reuse proven — no migration gate) |
| Application files changed | 5 (domain · data · api · worker · main) |
| Tests added | 2 files (19 unit + 5 integration) |
| Commits | **none** |
| Clones | `ct_x1_20260914` (disposable) |
| Production / investor demo | untouched |
| F-046-1 | enforced **and negative-control tested** (§6.2 V7) |
## 11. PO closure (2026-09-14)

> **PO DECISION: "Phase 8-X X1 — PO CLOSED / ACCEPTED."** The implementation and independent
> verification as reported above are **accepted as complete**, including `F-X1-1` as an in-scope
> defect discovered and fixed during X1.

* **Status: CLOSED — PO ACCEPTED.** No self-closure was performed; this section transcribes the decision.
* **`F-X1-2`: NOT authorised under X1.** Recorded as a **separate bounded remediation item associated with the prior P2 EF-E batch** — see its carried-findings record; **not fixed now.**
* **Boundaries preserved:** X2 not authorised · runtime/deployment introspection not authorised ·
  provider-console access not authorised · production access/modification not authorised ·
  S6 pending its own PO decision · RLS steps 3–5 unauthorised · `F-X1-2` remediation separate ·
  **OHD findings fully out of scope until all Phase 8 and Phase 8-X work is complete and closed.**


