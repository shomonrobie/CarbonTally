# CARBONTALLY — PHASE 8-X X7 API RUNTIME METRICS: BOUNDED CONTRACT (reconciliation)

**Document ID:** `CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915`
**Prompt:** `CT-P8X-X5-GATE-01` §6 · **Stage:** Phase 8-X **X7** (8-X discovery `S2`, Stage X7)
**Status:** **CONTRACT PREPARED — IMPLEMENTATION BLOCKED: PO DECISION REQUIRED** (see §13–§14)

---

## 1. What was inspected

* 8-X discovery document **Stage X7**: *"API runtime metrics (S2) — capture request volume, status
  distribution, latency, slow/error endpoints"*, and the `S2` inventory row: *"Requires new
  instrumentation; **no APM exists**. Valuable but larger than M-items"*.
* Authoritative X1 / X2 / X4 / X5 contracts and implementation/IV reports (all PO-closed).
* Runtime instrumentation in the repository: **`backend/main.py` registers CORS middleware only —
  there is no request-timing middleware, no metrics middleware and no APM**; a repository-wide search
  finds **no `perf_counter`/`process_time` in application code** (only inside vendored packages).
* Existing telemetry persistence: the generic `dashboard_metrics` store is written **only** by X1's
  worker heartbeat (`data/document_processing.py`, identities in `domain/operational_health.py`);
  X2's 90-day operational-metric retention already governs that store.
* Current repository/worktree state: X4 (`a71a46a`) and X5 (`137765f`) are banked; all other work is
  uncommitted and out of scope.

## 2–3. Metrics and API scope (what X7 may cover)

| # | Authorised metric (from `S2`) | Derivable without a new decision? |
|---|---|---|
| M1 | **Request volume** (count of API requests) | Definitionally yes; **the observation window is undefined** (see §4) |
| M2 | **Status distribution** (2xx/3xx/4xx/5xx classes) | Yes — HTTP status classes are a standard, non-invented vocabulary |
| M3 | **Latency** (per-request duration) | Measurement is mechanical; **the reported statistic (average? p95?) and its window are undefined** |
| M4 | **Slow endpoints** | **Requires an invented threshold** ("what is slow?") — the PO's X2 precedent is that thresholds are PO-supplied values, never invented (`PX-6`) |
| M5 | **Error endpoints** (routes with most 4xx/5xx) | Derivable from M2 once the window is fixed |

**API scope:** the application's own HTTP surface (`/api/v3/...` routes), observed at the ASGI layer.
**Explicitly not covered:** non-HTTP runtime, background-worker internal timings, database latency,
provider/edge latency, or per-tenant request attribution.

## 4. Read-time versus persisted (the blocking determination)

| Option | Effect | What it costs |
|---|---|---|
| **A — in-process, per-worker, read-time** | Counters/duration aggregates held in memory, exposed by one internal endpoint; **no persistence, no schema change, no retention** | Counters **reset on every restart/deploy** and are **per worker/process**, so in the multi-worker production topology an operator sees **one slice**, not the service. Any rolling window or p95 needs an **invented window parameter** |
| **B — persisted aggregates in the existing store** | Periodic snapshots written to the existing generic `dashboard_metrics` (free-form identity columns → **no new table/column/migration**), governed by X2's existing 90-day operational-metric retention | Requires an **invented flush interval**, a decision on **cross-worker aggregation identity**, and a decision that the X2 retention policy governs these rows |

**Neither option is determined by the authoritative record.** Both need at least one PO value or
semantic decision (§14), and M4 needs a PO-supplied threshold under either option.

## 5. Aggregation · 6. Freshness · 7. Retention

* **Aggregation:** in-process aggregation is trivial but per-process; persistence would need an agreed
  aggregate (per route-template, per status class, per interval) plus cross-worker merge semantics.
* **Freshness:** option A is live-but-partial (per process, since start); option B is periodic (as
  fresh as the flush interval — an undecided parameter).
* **Retention:** option A **has no retention surface** (nothing persisted → no new policy needed);
  option B **inherits** X2's existing 90-day operational-metric policy (no new policy invented).

## 8. Scope / tenancy · 9. Authorization · 10. Privacy

* **Scope/tenancy:** internal operational metrics only; **no per-tenant attribution**, no
  per-organisation breakdown (mirrors the X4 boundary).
* **Authorization:** the existing internal-only chain, unchanged
  (`require_staff` → `require_internal_staff` → `can_view_all`). No new permission model.
* **Privacy:** metrics must be **route templates only** — never raw paths containing identifiers,
  never query strings, never request/response bodies, headers, tokens, user ids, IPs or error text.
  Anything that could carry PII is excluded by construction and must be asserted by test.

## 11. Schema / migration requirement

**None required under either option.** Option A persists nothing; option B reuses the existing generic
metric store (its `metric_type` / `metric_name` / `metric_value` / `expires_at` columns already
support arbitrary operational metrics — as X1's heartbeat demonstrates). **No migration is proposed.**

## 12. Verification strategy (for whichever option is approved)

Unit tests for the aggregation (including the never-observed state) · API tests for the single
internal endpoint (ALLOW internal staff with `can_view_all`; DENY non-`can_view_all`, PE staff,
customer, unauthenticated) · **privacy/redaction test** proving no raw path, query string, body,
token or PII appears · read-only proof (option A) or bounded-write proof (option B) · freshness
labelling test (restart / "since" semantics) · regression run of the affected suites ·
**no production verification claimed**; F-046-1 discipline for any database-backed test.

## 13. Explicit exclusions

Usage/customer-behaviour analytics · import analytics · notification-delivery analytics · AI activity ·
business KPIs · provider/infrastructure/edge monitoring · provider/runtime/deployment introspection ·
per-tenant analytics · new calculation or factor-matching engines · S8 · I1 · D16 · RLS steps 3–5 ·
N3 retention domains · P1/P2 evidence work · S6 `new_version` · Phase 9 · **OHD**. Not a route to any
of these.

## 14. Stop-condition assessment — genuine stop conditions triggered

| Stop condition | Triggered? |
|---|---|
| New PO/business decision | **YES** — metric semantics (ephemeral per-process vs persisted) and aggregation identity are undetermined |
| New metric definition not already authorised | **YES** — M4 "slow endpoints" needs a **threshold**; M1/M3 need a **window/statistic**. The PO's X2 ruling forbids inventing thresholds |
| Material ambiguity in the authoritative record | **YES** — `S2` fixes metric names but leaves persistence, aggregation, window and threshold undefined |
| Inability to implement honestly | **YES for M4 / windowed statistics** without those values |
| New schema/table/column/migration | No (neither option needs one) |
| RLS/security change · new permission model · new retention policy · provider access · external evidence · reopening closed work · inability to isolate X7 changes | No |

⇒ **X7 is BLOCKED at the contract stage. No X7 code was written and no instrumentation was added.**

## 15. The PO decision required (plain English)

1. **Ephemeral or persisted?** Approve option **A** (in-process, per-worker counters that reset on
   restart, clearly labelled as one worker's slice) **or** option **B** (periodic snapshots into the
   existing operational-metric store, retained under X2's existing 90-day policy).
2. **If B: what flush interval** is authorised (e.g. every N minutes), and should each worker write
   its own series or one merged series?
3. **If latency/windowed statistics are wanted** (average, p95, rolling windows): what window is
   approved (e.g. rolling last-N requests vs last N minutes)?
4. **`slow endpoint` threshold:** what response time (in ms) defines "slow"? *(No value is invented
   here — X2's precedent is that thresholds are PO-supplied.)*
5. **Confirm the coverage boundary:** all `/api/v3/**` routes, route templates only, with no
   per-tenant attribution and no query-string/body capture.

**Recommendation:** approve **A first** with the approved threshold for "slow" and **no windowed
statistics** — it is the smallest honest increment, needs no persistence decision and no retention
change, and its limitation (per-worker, reset on restart) is explicit and self-describing. Move to B
only if cross-worker, restart-surviving history is genuinely required.

