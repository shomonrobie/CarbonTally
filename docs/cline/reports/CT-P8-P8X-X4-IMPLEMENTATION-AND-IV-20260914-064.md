# CT-P8-P8X-X4 — X4 AGGREGATION LAYER (FAILURES + SLA) — IMPLEMENTATION + INDEPENDENT VERIFICATION

**Report ID:** `CT-P8-P8X-X4-IMPLEMENTATION-AND-IV-20260914-064`
**Date:** 2026-09-14/15 · **Stage:** Phase 8-X **X4** (Phase 8-X X1/X2 delivered and PO-closed)
**Authority:** PO decision — *"X4 CONTRACT APPROVED — IMPLEMENTATION AUTHORIZED"* against
`CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914.md`, with rulings `X4-D1`…`X4-D5`.
**Status:** **IMPLEMENTED + SELF-VERIFIED — READY FOR PO REVIEW/CLOSURE** (not PO-closed).

---

## 1. Files changed (X4 only)

| File | Change |
|---|---|
| `backend/services/operational_intelligence.py` (**new**, 259 lines) | Pure composition functions (`aggregate_queue_rows`, `aggregate_sla`, `aggregate_worker_liveness`) + `OperationalIntelligenceService` (`summary`/`failures`/`sla`). Read-only |
| `backend/api/v3_operations.py` | **One** read-only route `GET /api/v3/ops/operational-intelligence` (X4-D5) + a 6-line import. X1's two endpoints unchanged |
| `backend/tests/unit/services/test_operational_intelligence.py` (**new**) | Per-metric unit tests, SLA cases, liveness cases, truncation, X4/X1 consistency, redaction |
| `backend/tests/unit/api/test_x4_operational_intelligence.py` (**new**) | Endpoint ALLOW/DENY authorization + payload/redaction + route-shape tests |
| `backend/tests/integration/test_operational_intelligence_x4_runtime.py` (**new**) | Real-PostgreSQL direct SQL cross-checks, redaction fixture, truncation, SLA not-configured, worker UNKNOWN→HEALTHY, read-only proof |

**Not changed:** no migration, no table/view/column, no RLS, no permission model, no frontend file, no
X1 semantics, no X2 alerting, no factor-matching, no calculation/processing engine.

## 2. Exact implementation behaviour

One internal-only `GET` returning a single aggregate object. Every metric is the approved one, computed
by the **existing** X1 predicates or read from an **existing** column/setting:

| Approved metric | Implementation |
|---|---|
| `failed_jobs` | count of rows whose persisted `stage == 'failed'` |
| `retry_exhausted_jobs` | count via X1's `is_retry_exhausted` (`attempt_count >= max_attempts`) |
| `stuck_locked_jobs` | count via X1's `is_stuck` (lock held past `DEFAULT_STALE_AFTER_SECONDS`) |
| `blocked_jobs` / `manual_review_jobs` | counts of those persisted stages, in their **own buckets** — never merged into failures |
| `error_rate_by_stage` | `{stage: count}` of rows with `workflow_error_count > 0` — **a count, not a rate; no denominator** (X4-D3) |
| `sla_configured` / `sla_hours` | `queue_settings.is_configured()` + the configured `sla_hours` (**value shown only when configured**) |
| `sla_breached_items` | `count_sla_breached()` — the persisted `sla_breached = true` flag (**flag-only**, X4-D4) |
| `sla_state` | `configured` \| `not_configured` \| `unknown` (unknown = settings read failed) |
| `queue_depth_by_stage` | X1's `stage_distribution` |
| `open_vs_closed` | counts against X1's `OPEN_STAGES` / `CLOSED_STAGES` |
| `worker_liveness` | X1's `classify_worker_liveness` + worker id (so failures are never read as "live" while the worker is dead) |
| *(supporting)* `truncated`, `read_limit`, `rows_examined`, `stale_after_seconds`, `scope`, `x4_scope`, `evaluated_at` | honesty/context fields |

**Honesty rules implemented:** when SLA is not configured, `sla_breached_items` is `null` and the
breach count is **not even read** from the database (verified). When the worker never ticked,
liveness is `UNKNOWN`. When the read returns exactly the 2,000-row bound, `truncated: true`
(X4-D2). The read uses X1's own bound so `truncated` is meaningful.

**Authorization:** `require_staff()` → `require_internal_staff()` → `ensure_staff_permission(..., "can_view_all")`
— identical to X1. No new permission model; no RLS change; the frontend is not a boundary.
**No per-organisation breakdown** and no error text, filenames or URLs are returned.

---

## 3. Tests and verification results

| Suite | Result |
|---|---|
| X4 unit + service (`tests/unit/services/test_operational_intelligence.py`) | **26 passed** |
| X4 endpoint ALLOW/DENY/payload/route (`tests/unit/api/test_x4_operational_intelligence.py`) | **10 passed** |
| X4 runtime, real PostgreSQL on disposable clone (`tests/integration/test_operational_intelligence_x4_runtime.py`) | **6 passed** |
| X1 + X2 regression, unit (`tests/unit/domain/test_operational_health.py`, `…/test_operational_alerts.py`, `tests/unit/workers/test_x2_alert_wiring.py`) | **passed** |
| X1 + X2 regression, real DB on the same clone (X1 + X2 runtime suites) | **8 passed** |
| Broader API regression (`tests/unit/api`, full suite) | **exactly 2 failures — both the pre-existing `F-X1-2` EF-E test-double tests; every other test passed, including all 10 X4 endpoint tests.** (The first full run additionally flagged one X4 test-side flake, fixed in-task — see `F-X4-4` in §4) |

**Verification against each PO-required item**

| Required | Evidence |
|---|---|
| Unit coverage for each approved metric | named tests per metric (failed, retry-exhausted, stuck, blocked, manual-review, error-by-stage, queue depth, open-vs-closed, all four SLA fields, worker liveness, truncation) |
| Configured SLA case | unit + endpoint + **real DB**: `sla_state=configured`, `sla_hours=48`, breach count SQL-cross-checked |
| Not-configured SLA case | unit + endpoint + **real DB**: `not_configured`, `sla_breached_items=null`, `sla_hours=null`, breach count **never read** |
| Worker `UNKNOWN` | unit + endpoint + **real DB** (no heartbeat → `UNKNOWN`; recorded → `HEALTHY`) |
| Explicit truncation | unit (exact bound), endpoint (2000 rows), **real read path** (`limit=3` over 4 rows) |
| Direct SQL cross-checks, disposable environment | `failed=2`, `exhausted=1`, `blocked=1`, `manual_review=1`, `stuck=1`, `sla_breached=2` — each equal to an independently written SQL count |
| Redaction fixture (`last_error` with an e-mail) | unit + endpoint + **real DB**: e-mail, error text, filenames, URLs absent; failure still counted |
| Authorization ALLOW | internal staff with `can_view_all` → **200** |
| Authorization DENY | staff without `can_view_all` → **403**; PE/entity staff → **403**; non-staff customer → **403**; unauthenticated → **401** |
| X4/X1 consistency (no duplication) | shared predicates asserted equal in unit **and** over real rows |
| F-046-1 discipline | target was disposable clone **`ct_x4_20260914`** (template `carbontally_qa_phase8`); QA read-only; demo/production untouched |

**Explicit non-verification (not claimed):** no production verification, no live-browser UI
verification (X5 out of scope), no load/performance testing.

## 4. Findings

| ID | Severity | Finding | Action |
|---|---|---|---|
| `F-X4-1` | **Information / test-infra** | The dedicated integration database **`carbontally_test` has a stale schema**: its `document_processing_queue` lacks the V3 queue columns (`stage`, `attempt_count`, `max_attempts`, `lock_token`, `locked_at`, `last_error`, `ingested_at`). The conftest only checks that `organizations` exists, so a default-configured X1/X4 integration run would fail on missing columns rather than skip. | **Not fixed** (outside X4 scope). X4 verification used a disposable clone from the current-schema QA database. Recommend re-provisioning `carbontally_test` as separate test-infrastructure work |
| `F-X4-2` | **None (test-side; fixed in-task)** | The first runtime cross-check compared a `uuid.UUID` value with a `str` org id, so the local recomputation saw 0 rows while the SQL cross-check passed. **Test bug only — no implementation defect** | Fixed inside the X4 integration test (`str(...)` normalisation) |
| `F-X4-4` | **Information (test-side; fixed in-task)** | Independent verification caught a **time-dependent test fixture**: the endpoint test's stub heartbeat was timestamped at *module import*, so during the ~9-minute full `tests/unit/api` run it aged past the 300 s stale window and the liveness assertion flaked (`STALE` vs `HEALTHY`). It passed when the file ran alone. **Test bug only — the implementation correctly reported `STALE` for a genuinely old tick** | Fixed: the stub now timestamps its tick **per request**, so the assertion is deterministic regardless of suite duration. Re-run of the file: **10 passed** |
| `F-X1-2` | pre-existing | EF-E test-double drift (2 failures in `tests/unit/api/test_v3_phase_c_regressions.py`) | **Untouched** — PO-excluded; unchanged |
| `F-X4-3` | **Information** | **No stop-condition was triggered:** no schema change was required; no new business/metric definition was needed; every approved metric was supported by an existing authoritative source; no new permission/RLS model was needed; the 2,000-row bound is representable honestly via `truncated` | None |

**No contract reinterpretation occurred.** The single deviation is the PO's own ruling `X4-D5`
(one endpoint instead of the contract §9 draft of three), implemented exactly as ruled.

## 5. Environment / database / migration impact

* **Migrations: none.** The newest migration remains `20260924000000_p8x_x2_operational_telemetry_retention.sql` (X2).
* **Schema / RLS / permissions: unchanged.** No table, view, column, policy, grant or role touched.
* **Disposable clone created:** `ct_x4_20260914` (template `carbontally_qa_phase8`, read-only use of the
  template). It is a test artefact and may be dropped at any time.
* **QA (`carbontally_qa_phase8`): not modified** — read only, as the clone template.
* **Investor demo / production: not touched.** No production verification is claimed.
* **Retention: unchanged** — X4 persists nothing; the X2 90-day telemetry policy is untouched.
* **Frontend: zero files changed by X4** (the S6 frontend work from the previous task is unchanged).

## 6. Boundary confirmation

Not begun / untouched by X4: **X5** · **X7** · **X8** · S6 `new_version` · RLS steps 3–5 · S8 · I1 ·
D16/legacy · `F-X1-2` · `F-B3-7` · `F-4A1B-1` · B4-D12 · production/G0-D · provider/runtime/deployment
introspection · Phase 9 · **OHD findings (entirely out of scope)**. Also excluded as ruled: usage,
import, notification-delivery and AI-activity metrics; trends/time windows; the deadline-derived SLA
metric; per-organisation breakdown; any new engine.

## 7. Proposed commit boundary

A single self-contained X4 commit (when separately authorised):

```
backend/services/operational_intelligence.py                                  (new)
backend/api/v3_operations.py                                                  (1 route + 1 import)
backend/tests/unit/services/test_operational_intelligence.py                  (new)
backend/tests/unit/api/test_x4_operational_intelligence.py                    (new)
backend/tests/integration/test_operational_intelligence_x4_runtime.py         (new)
docs/cline/reports/CT-P8-P8X-X4-IMPLEMENTATION-AND-IV-20260914-064.md          (this report)
```

**No commit or push was performed.** Work is uncommitted pending PO review.
**Status: READY FOR PO REVIEW/CLOSURE — not PO-closed.**

---

## 8. PO CLOSURE (2026-09-14) — transcription of the PO decision

> ### X4 — IMPLEMENTED, INDEPENDENTLY VERIFIED, **PO-CLOSED**
> *"I hereby PO-close X4 (Failures + SLA Aggregation)."* The verification PASS is accepted **for the
> approved X4 scope**.

Recorded as explicit **limitations/findings — not defects in X4**:

| Item | Status per PO closure |
|---|---|
| `F-X4-1` — stale `carbontally_test` schema | Test-infrastructure issue; **remains separate remediation** |
| `F-X1-2` — pre-existing EF-E test-double drift | **Remains separately excluded** |
| Production verification | **None was performed and none is claimed** |
| Production authorisation | **Not implied by this closure** |
| Excluded Phase 8 / Phase 8-X work | **Not accepted as complete by this closure** |

The X4 contract (`CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914.md`) and this
implementation/IV report are retained as the **authoritative record**.

**Closure status:** X4 is **PO-CLOSED**. X5, X7, X8 and every deferred/held item remain
**not started** and **not closed**.



