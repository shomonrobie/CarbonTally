# CT-P8-P8X-X7 — API RUNTIME METRICS: IMPLEMENTATION + INDEPENDENT VERIFICATION

**Report ID:** `CT-P8-P8X-X7-IMPLEMENTATION-AND-IV-20260915-066`
**Prompt ID: `CT-P8X-X7-GATE-02`**
**Stage:** Phase 8-X **X7** (`S2`) · **Date:** 2026-09-15 · **Branch:** `main` · **Baseline HEAD:** `137765f`

---

## A. PO decisions (recorded exactly)

| ID | Decision |
|---|---|
| **X7-D1** | **B — PERSISTED SNAPSHOTS** in the existing generic `dashboard_metrics` operational-metric store; no new table/telemetry store; must survive worker/process restart |
| **X7-D2** | **5 MINUTES** flush interval; no shorter cadence unless required for correctness |
| **X7-D3** | **ONE MERGED SERIES**; no per-worker series; if cross-worker aggregation cannot be honest, STOP rather than represent one worker as global |
| **X7-D4** | **P95** latency, exposed as `p95_latency_ms`; never relabelled as average |
| **X7-D5** | **ROLLING 60 MINUTES** window, with exact semantics documented |
| **X7-D6** | **1,000 ms** slow threshold (`>= 1000`); route templates not raw URLs; no query strings/bodies/tokens/credentials/PII/raw error text |
| **X7-D7** | **ALL `/api/v3/**`** routes; normalised route identities; no per-tenant/customer/PE/entity attribution; no query-string or body capture |

## B. Contract reconciliation — how the decisions map to the contract

| Contract item | Resolution |
|---|---|
| §4 read-time vs persisted | Resolved by `X7-D1` → persisted snapshots (option B) |
| §5 aggregation | Resolved by `X7-D2`/`X7-D3` → 5-minute slots merged into **one** series row |
| §6 freshness | Read model reports `persisted_at` plus `pending_local_slots`, so freshness is never overstated |
| §7 retention | Unchanged: X2's existing policy governs `dashboard_metrics` (verified in the runtime suite) |
| §8 tenancy · §9 authorization · §10 privacy | Unchanged boundaries: internal-only chain, aggregates only, route templates only |
| §11 schema | **None required** — verified against the live column set (`metric_type`, `metric_name`, `metric_value` jsonb NOT NULL, `period`, `expires_at`, `created_at`); the store holds the payload with no migration |
| §12 verification | Executed (see §D) |
| §14 stop conditions | **All cleared** by `X7-D1`…`X7-D7`, including the honesty question `X7-D3` itself raises (see §C aggregation) |

## C. Implementation

**Files changed (backend only — no frontend work; X5 owns the UI):**

| File | Change |
|---|---|
| `backend/domain/api_metrics.py` **(new)** | Pure domain: PO constants (`SLOW_THRESHOLD_MS=1000`, `WINDOW_SECONDS=3600`, `FLUSH_INTERVAL_SECONDS=300`, `SLOT_SECONDS=300`), `slot_key`, `status_class`, `is_slow`, `record_sample`, `prune_slots`, `aggregate_slots`, bucket-histogram p95, `UNMATCHED_ROUTE` |
| `backend/data/api_metrics.py` **(new)** | `ApiMetricsRepository` over `dashboard_metrics`: `merge_slots` (row-locked read-merge-write of the single series), `read_series`, `count_series_rows` |
| `backend/services/api_metrics.py` **(new)** | `ApiMetricsService`: in-process slot accumulator, `flush_due`/`flush`/`flush_if_due`, `observe_request`, `read`; process-wide registry; `route_template`; `monotonic_ms` |
| `backend/api/router.py` | One `@app.middleware("http")` hook in `create_app` (beside the existing `RequestContextMiddleware`) + one import |
| `backend/main.py` | Best-effort startup initialisation of the service (+ `app.state`); a pool failure disables the feature and never blocks startup |
| `backend/api/v3_operations.py` | One **read-only** internal endpoint `GET /api/v3/ops/api-runtime-metrics` + 3 import lines |
| 3 new test files | 15 unit + 7 endpoint/authz/privacy + 5 runtime tests |

**Instrumentation architecture (minimum necessary, PO §4):** the existing middleware layer measures one instrumented request; the route is read from `scope["route"].path` **after** routing (so it is the template); unmatched requests become `<unmatched>` — the raw path is never stored. Only `/api/v3/**` is instrumented. Instrumentation can never break or delay a request (failures are logged and swallowed; the exception path records 5xx then re-raises the original).

**Metric definitions:** `request_volume` (count) · `status_distribution` (2xx/3xx/4xx/5xx counts; unknown statuses collapse to 5xx rather than being dropped) · `p95_latency_ms` · `slow_requests` / `slow_routes` (≥ 1,000 ms) · `error_requests` / `error_routes` (4xx+5xx). **No rate, percentage or denominator-dependent metric exists anywhere.**

**Persistence (`X7-D1`):** one `dashboard_metrics` row (`metric_type='API_RUNTIME'`, `metric_name='api_v3_rolling_60m'`, `period='rolling_60m'`) whose jsonb payload maps wall-clock 5-minute slots → per-route counters/histograms. Survives restart (verified).

**Flush behaviour (`X7-D2`):** at most one flush per 300 s, triggered opportunistically by request activity (`flush_if_due`) — recorded data is persisted within the cadence **without a background task and without inventing an operational parameter**. Empty buffers never write.

**Aggregation (`X7-D3`):** slots are keyed by **wall-clock slot, not worker identity**, and merged into the single row under a `FOR UPDATE` lock — any number of instrumented processes merge into one series and concurrent flushes cannot lose a slot. p95 is computed at read time from the **merged** bucket histogram, so no cross-worker merge of pre-computed percentiles is needed. Multi-worker topologies contribute to the same series instead of creating per-worker rows.

**p95 semantics (`X7-D4`/`X7-D5`):** fixed-bucket histogram (≤10/25/50/100/250/500/1000/2500/5000/10000 ms + overflow), so `p95_latency_ms` is the **upper bound of the bucket containing the 95th observation** — conservative, bounded in memory, mergeable, and labelled `p95_latency_ms_resolution = "bucket_upper_bound"`. Never presented as exact.

**Read API (PO §6):** `GET /api/v3/ops/api-runtime-metrics` on the existing ops surface — internal-only (`require_staff` → `require_internal_staff` → `can_view_all`), read-only, aggregates only, no raw telemetry rows, no tenant/entity breakdown. **No frontend work.**

**Privacy/security controls:** route templates only; `UNMATCHED_ROUTE` sentinel; no query strings, bodies, headers, tokens, credentials, e-mails, identifiers or raw error text; no IP capture; **no RLS change; no new permission model.**

---

## D. Verification

| Suite | Result |
|---|---|
| X7 unit (domain + service + persistence stubs) | **15 passed** |
| X7 endpoint (authz + privacy + route shape) | **7 passed** |
| X7 runtime — real PostgreSQL, disposable clone `ct_x7_20260915` | **5 passed** |
| Regression — X1 · X2 · X4 · X7 suites together | **83 tests, no failures** |

**Coverage of the PO's required verification:**

* **Instrumentation:** only `/api/v3/**` recorded (a `/health` request is ignored); route **templates** stored (`/api/v3/reports/{report_id}`); an unmatched request carrying a UUID and `?token=secret` stores only `<unmatched>` (asserted: no identifier, no `token`, no `secret` persisted).
* **Metrics:** volume, status distribution, `p95_latency_ms`, slow count/threshold, error count — plus the negative assertion that **no** rate/percentage/ratio key exists.
* **Window:** a 30-minute-old slot counts; a 90-minute-old slot is excluded from the aggregate **and pruned from the persisted payload** (asserted on the real row).
* **Persistence/restart:** a fresh service instance (empty buffer) reads the earlier window back — `series_present: true`, correct volume/5xx/slow/error and `persisted_at`.
* **Aggregation (`X7-D3`):** two independent service instances flushing the same slot yield **exactly one row** with merged counters (2 requests; not 2 rows).
* **Security:** internal staff with `can_view_all` → **200**; without → **403**; PE/entity staff → **403**; non-staff customer → **403**; unauthenticated → **401**; the response body contains no token/query/body/e-mail/user-id/organisation/tenant/entity/IP token.
* **Retention:** X2's `prune_operational_metrics_before` counts the X7 row as in scope (`eligible_metrics ≥ 1`); a past-cutoff prune deletes nothing and the live row remains → **X7 adds and changes no retention policy**. X1's heartbeat and the X7 series coexist as distinct identities in one store.
* **Read-only:** the endpoint is a single `GET`; no write route exists on that path.
* **Not verified / not claimed:** **no production verification**, no live-browser/UI verification (X7 has no UI by ruling), no load/stress testing.

## E. Findings

| ID | Severity | Evidence | Resolution / status | In scope? |
|---|---|---|---|---|
| **`F-X7-1`** | **Medium — real defect found by IV and fixed** | `slot_key` floored only **seconds**, so 12:07:42 and 12:09:59 produced different slot keys — a wrong 5-minute boundary that would have fragmented the series and mis-windowed the rolling 60 minutes | **Fixed** in `domain/api_metrics.py` (epoch floored to the 300 s boundary); the test that exposed it now asserts both samples map to the 12:05 slot | Yes — X7 |
| **`F-X7-2`** | Low (test-side, fixed in-task) | The retention runtime test asserted a key that does not exist (`eligible`) | Fixed to `eligible_metrics`; the failure output proved the X7 row **is** in scope (1 eligible) | Yes — X7 test |
| **`F-X7-3`** | Information | **No stop condition triggered**: no schema/migration, no RLS, no permission model, no new retention policy, no new business/metric definition, no provider access, no per-tenant attribution, no closed workstream reopened; X7 changes are isolatable | None | — |
| **`F-X7-4`** | Information (documented limitation) | `p95_latency_ms` is **bucket-resolution** (upper bound of the containing bucket), and the flush is activity-triggered, so a fully idle service flushes nothing new (nothing new exists to flush) | Surfaced in the payload (`p95_latency_ms_resolution`, `pending_local_slots`) and in §C | — |

## F. Environment impact

| Item | Status |
|---|---|
| Database touched | **Yes — only the disposable clone `ct_x7_20260915`** (from `carbontally_qa_phase8` as a read-only template); rows removed in `finally` blocks |
| Migrations | **None added** (newest remains `20260924000000_p8x_x2_operational_telemetry_retention.sql`) |
| Schema changes | **None** — the existing store proved sufficient, so PO §3's stop condition did not trigger |
| RLS | **Unchanged** (no policy, grant or role touched) |
| Retention | **Unchanged** — reuses X2's; verified by test |
| QA (`carbontally_qa_phase8`) | **Not modified** (read only, as clone template) |
| Production | **Not accessed, not modified, not verified** |
| Investor demo | **Not accessed, not modified** |
| Unit tests | **No database access** (the endpoint suite patches `get_pool` and the repository class) |

## G. Commit status

**Not committed. Nothing pushed.**

**Proposed X7 commit boundary (exact):**
```
backend/domain/api_metrics.py                                          (new)
backend/data/api_metrics.py                                            (new)
backend/services/api_metrics.py                                        (new)
backend/api/router.py                                                  (X7 middleware hook + import only)
backend/main.py                                                        (X7 startup init only)
backend/api/v3_operations.py                                           (X7 route + 3 imports only)
backend/tests/unit/services/test_api_metrics_x7.py                     (new)
backend/tests/unit/api/test_api_metrics_x7_endpoint.py                 (new)
backend/tests/integration/test_api_metrics_x7_runtime.py               (new)
docs/cline/reports/CT-P8-P8X-X7-IMPLEMENTATION-AND-IV-20260915-066.md  (this report)
```

`router.py`, `main.py` and `v3_operations.py` are **mixed files** carrying pre-existing uncommitted X1/B2/S6-era work, so a clean X7 commit **requires precise partial staging** — the same blob-level technique already proven on X4 (`a71a46a`: `v3_operations.py` +41 lines only) and X5 (`137765f`). The authored X7 hunks are exactly: the middleware hook + import, the startup initialisation block, and the route + three imports.

**Why it was not committed in this pass:** implementation + verification + this report consumed the execution budget, and partially-staged staging is the one step where an error would corrupt history. The boundary is fully specified and can be executed on authorisation.

**Worktree:** `HEAD` = `137765f` · staged **0** · pre-existing uncommitted work **preserved** · **no reset, no clean, no rebase, no push**.

## H. X7 verdict

**X7 READY FOR PO REVIEW/CLOSURE**



