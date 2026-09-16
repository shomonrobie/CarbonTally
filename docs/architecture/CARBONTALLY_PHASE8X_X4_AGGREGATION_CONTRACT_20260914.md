# CARBONTALLY — PHASE 8-X X4 AGGREGATION LAYER: BOUNDED CONTRACT (reconciliation + proposal)

**Document ID:** `CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914`
**Date:** 2026-09-14 · **Stage:** Phase 8-X **X4** (`G-20`, M3, S3–S6 in the 8-X discovery document)
**Status:** **CONTRACT PREPARED — NOT AUTHORISED FOR IMPLEMENTATION. NO CODE WAS WRITTEN.**
**Authority to prepare:** PO decision 2026-09-14 (X4 contract preparation/reconciliation only;
implementation requires separate PO authorisation).

**Proposed first release:** *failures + SLA* — an internal, read-only aggregation/read model answering
**"what is failing and what is breaching SLA"**, reusing existing persisted data. Usage / imports /
notification-delivery / AI activity are **excluded** from this release (they remain separate bounded
increments) because no existing decision authorises them as part of X4's first release.

---

## 1. Reconciled current state (what already exists)

Verified against the repository — X4 must **reuse** all of this and duplicate none of it:

| Existing capability | Location | What it provides |
|---|---|---|
| X1 queue/worker visibility | `data/document_processing.py::queue_visibility_rows` (limit 2000) · `latest_worker_heartbeat` | persisted queue rows + ONE heartbeat row in `dashboard_metrics` |
| X1 classification (pure) | `domain/operational_health.py` | `OPEN_STAGES` (queued, ingesting, extracting, mapping, validating, calculating, review, blocked, manual_review) · `CLOSED_STAGES` (completed, failed) · `is_retry_exhausted` (`attempt_count >= max_attempts`) · `is_stuck` (lock held past window) · `stage_distribution`, `summarise_queue` · `DEFAULT_STALE_AFTER_SECONDS = 300` |
| X1 endpoints | `api/v3_operations.py` | `GET /api/v3/ops/operational-health/queue`, `GET …/operational-health/worker` (`require_staff` + `require_internal_staff`) |
| X2 alert domain (pure) | `domain/operational_alerts.py` | conditions `QUEUE_BACKLOG`, `WORKER_STALE`, `SLA_BREACH`, `RETRY_EXHAUSTED`; PO constants `BACKLOG_WAITING_THRESHOLD = 100`, `WORKER_STALE_SECONDS = 900`, `ALERT_COOLDOWN_SECONDS = 3600`, `DELIVERY_MAX_ATTEMPTS = 3` |
| X2 alert service | `services/operational_alerting.py` | `_queue_summary()` (via `queue_visibility_rows`), `_worker_liveness()`, `_sla_input()` → `queue_settings.is_configured()` / `get_settings()` + `processing.count_sla_breached()` |
| X2 SLA signal | `data/document_processing.py::count_sla_breached` | `SELECT count(*) FROM public.processing_queue WHERE coalesce(sla_breached,false)` |
| Existing ops SLA precedent | `data/reporting.py` (~line 699) | deadline-based breach query using `sla_deadline` / `sla_breached` — a **different, pre-existing** semantic (see §5) |
| PO SLA ruling (X2) | `domain/operational_alerts.py` module docstring | *"SLA breach: use the existing configured SLA setting"*; if absent → **not evaluable**, **no fabricated breach** |
| Telemetry retention (X2) | `services/retention.py` + migration `20260924000000_p8x_x2_operational_telemetry_retention.sql` | 90-day retention for operational **metrics**; `document_processing_queue` is explicitly **not** touched |

**Data sources (all pre-existing tables):** `public.document_processing_queue` (`status` check
constraint: pending, processing, ai_extracted, manual_review, manual_extraction, qc, customer_review,
approved, rejected, completed, failed; plus `created_at`, `updated_at`, `completed_at` and the V3
queue columns `stage`, `attempt_count`, `max_attempts`, `workflow_error_count`, `last_error`,
`locked_at`, `lock_token`, `ingested_at`) · `public.processing_queue` (`sla_deadline`,
`sla_breached`, `queue_status`) · `public.dashboard_metrics` (heartbeat) · `public.queue_settings`
(configured SLA hours).

## 2. Proposed first-release scope

One read-only aggregation service — `services/operational_intelligence.py` (the path named in the
8-X discovery document) — plus internal read endpoints. It **composes** existing X1/X2 inputs; it does
not re-implement classification, does not evaluate or dispatch alerts, and creates no engine.

| # | Metric | Definition | Source | Authority |
|---|---|---|---|---|
| M1 | `failed_jobs` | rows whose persisted `stage` is `failed` (`CLOSED_STAGES`) | `document_processing_queue` via existing `queue_visibility_rows()` | X1 vocabulary |
| M2 | `retry_exhausted_jobs` | rows where `attempt_count >= max_attempts` (existing predicate) | same | X1 `is_retry_exhausted` |
| M3 | `stuck_locked_jobs` | rows holding a `lock_token` whose `locked_at` age ≥ the existing stale window | same | X1 `is_stuck` + `release_stale_locks` window |
| M4 | `blocked_jobs` / `manual_review_jobs` | rows in the persisted `blocked` / `manual_review` **stages**, reported as their **own labelled buckets** — never as "failures" | same | X1 `OPEN_STAGES` |
| M5 | `error_rate_by_stage` | rows with `workflow_error_count > 0`, grouped by persisted stage | same | persisted column |
| M6 | `sla_configured` + `sla_hours` | whether the SLA setting is configured, and its value | `queue_settings.is_configured()/get_settings()` | PO ruling (X2) |
| M7 | `sla_breached_items` | count of rows flagged `sla_breached = true` | `processing_queue` via existing `count_sla_breached()` | X2 first-release signal |
| M8 | `sla_state` | `configured` \| `not_configured` \| `unknown` — gates whether any breach figure may be shown at all | derivation of M6 | PO ruling (X2): never fabricate a breach |
| M9 | `queue_depth_by_stage` / `open_vs_closed` | per-stage counts (existing `stage_distribution`/`summarise_queue`) | X1 | X1 vocabulary |
| M10 | `worker_liveness` | existing heartbeat state (`HEALTHY`/`STALE`/`UNKNOWN`) + age, so failure figures are never read as "live" while the worker is dead | `dashboard_metrics` | X1/X2 vocabulary |

**Trend counts (windowed)** — M1/M2/M7 over a time window — are **proposed but gated on PO decision
`X4-D1`** (§6), because a window is a business definition and no window has been approved for X4.
Windowing can only use `created_at` / `updated_at` / `completed_at`; **there is no `failed_at`
column**, so "failures in the last N hours" is an approximation unless the PO accepts `updated_at`
as the moment of failure.

**No metric is proposed whose source or meaning does not already exist.** Every figure above is an
existing predicate, an existing column, or an existing configured setting.

## 3. Aggregation definitions

* Aggregation is **read-time over persisted rows** (the existing `queue_visibility_rows()` read
  path). No materialised summary table, no snapshot writes, no background aggregator.
* Counts are computed by the **existing pure classifiers** (`is_retry_exhausted`, `is_stuck`,
  `stage_distribution`, `summarise_queue`) so X4 and X1 can never disagree about the same row.
* **Bounded read:** X4 inherits the existing `limit=2000` read bound. If the true population exceeds
  it, the response must say so explicitly (e.g. `truncated: true`) rather than silently reporting a
  partial population as the whole. *(Part of proposed decision `X4-D2`.)*
* Error **text** is never returned: `last_error` is used only as an aggregate/boolean signal (counts
  by stage). This satisfies the X4 stage requirement for a **redaction review** for error text and
  email addresses, and keeps PII — e-mail addresses commonly appear inside OCR error strings — out of
  the payload entirely.

## 4. Failure semantics

| Term | Meaning in X4 | Not to be confused with |
|---|---|---|
| **Failed** | persisted `stage = 'failed'` — terminal failure of a job | "rejected" (a review outcome) or "blocked" |
| **Retry-exhausted** | `attempt_count >= max_attempts` — all attempts used (X1 predicate) | not identical to failed: an exhausted job may still be sitting un-actioned |
| **Stuck** | lock held past the existing stale window (X1 predicate) | not a failure state — a stalled claim the queue's `release_stale_locks` already reclaims |
| **Blocked / manual review** | waiting for a human; **reported separately, never aggregated into "failures"** | — |
| **Completed** | `stage = 'completed'` | — |

No new failure taxonomy is introduced; X4 counts only the persisted vocabulary. **X4 does not compute
a "failure rate"** (a rate needs an approved denominator) unless the PO rules one in — proposed as
`X4-D3`.

## 5. SLA semantics

X4 reuses the **X2-approved** SLA model exactly — it does **not** invent an SLA:

1. The SLA **value** is the existing configured setting (`queue_settings.sla_hours`). X4 only reports
   it; X4 never sets it and never defaults it.
2. If the setting is **not configured**, X4 reports `sla_state = "not_configured"` and **no breach
   figure is shown or implied**. A missing configuration must never become a fabricated breach
   (PO ruling, X2).
3. The **breach signal** for this release is the persisted `processing_queue.sla_breached` flag — the
   same signal X2 evaluates.
4. **Known semantic split (needs a PO word — `X4-D4`):** a *second*, pre-existing SLA semantic exists
   in the codebase (`data/reporting.py` computes rows where `sla_deadline < now()` and the row is not
   completed). The two can differ. X4 reports the **flag** by default; the deadline-derived figure is
   **excluded** unless the PO asks for both. X4 will not silently reconcile or relabel them.
5. X4 covers **processing-queue SLA only**. `issues.sla_deadline` / `issues.sla_breached` and
   review/QC SLA surfaces are **out of scope** (different domain; would widen the batch).

## 6. Time windows (PO decision `X4-D1`)

No time window for X4 has been approved anywhere. Proposed, **subject to PO approval**:

* `last_24h` and `last_7d` for failure/retry/breach counts, windowed on `created_at`, with the failure
  window additionally reported on `updated_at` where the two differ.
* **If the PO declines windows**, the first release is **window-less**: current-state counts only
  (M1–M10, no trend figures). That is fully deliverable and needs no new definition.
* A query window implies no retention policy.

## 7. Tenant / entity scope and permissions

* **Internal only.** Every X4 endpoint uses the existing `require_staff()` + `require_internal_staff()`
  dependency chain — the same authority as X1's operational-health endpoints and X2's internal-only
  alerting (`PX-6` Option (a)). PE/entity staff gain **no** access; `require_entity_scope` is not used,
  because X4 is deliberately **not** entity-scoped.
* **Cross-organisation aggregates for internal operators.** X4 returns counts and distributions, not
  customer rows: no document contents, no file names, no signed URLs, no error text, and no
  per-organisation breakdown in this release (a per-org breakdown would be a new PO decision).
* **No RLS change and no bypass:** X4 reads through the same service-role repository path X1/X2
  already use; authorization stays in the application layer, unchanged.
* **The frontend is not a boundary** — there is no X5 console work in this release, so nothing is
  rendered; the endpoints are simply guarded.

## 8. Freshness expectations

* X4 is read-time aggregation: figures are as fresh as the underlying rows (no cache, no scheduled
  refresh in this release).
* Every response carries `evaluated_at` and the **worker liveness age** (M10), so an operator can see
  whether data is live or the worker is dead. X4 must never present stale figures as current.
* X4 inherits X1's `DEFAULT_STALE_AFTER_SECONDS = 300` for liveness display; X2's alerting threshold
  (`WORKER_STALE_SECONDS = 900`) stays **alerting-only** and is not reused as a display threshold.

## 9. API / read-model shape (proposed, bounded)

Read-only GETs on the existing ops router, internal-only:

| Endpoint (proposed) | Returns |
|---|---|
| `GET /api/v3/ops/operational-intelligence/failures` | M1, M2, M3, M4, M5, M9 + `evaluated_at`, `truncated` |
| `GET /api/v3/ops/operational-intelligence/sla` | M6, M7, M8 + `evaluated_at` |
| `GET /api/v3/ops/operational-intelligence/summary` | both, composed (one call for an operator overview) |

No new writes, no admin/mutation endpoints, no alert dispatch. Endpoint names are provisional and
fixed at authorisation. X1's existing endpoints are **not** modified.

## 10. Schema change requirement

**None required.** X4 is read-time aggregation over existing tables and existing configured settings,
matching the 8-X discovery document's own scope note for X4 (*"no new tables; views only if required
and separately authorized"* — and no view is required for read-time aggregation). **No migration is
proposed.** A materialised read model would be a **new** schema change needing its own authorisation.

## 11. Retention implications

* **No new retention rule** and no change to the X2 90-day telemetry policy.
* X4 persists nothing, so it creates no new data to retain.
* `document_processing_queue` (the durable job record) and `processing_queue` remain outside any
  retention rule, exactly as X2 established — X4 does not alter that.

## 12. Verification plan (proposed)

1. **Unit (pure):** composition logic against fixtures for every metric M1–M10, including the
   not-configured SLA path and the worker-`UNKNOWN` path.
2. **Cross-check to source tables** (required by the X4 stage definition): every aggregate figure must
   equal a direct SQL count over the same rows, in a **disposable** environment.
3. **Redaction review** (required by the X4 stage definition): assert no error text, file name,
   e-mail address or signed URL appears anywhere in any X4 payload — including a fixture whose
   `last_error` contains an e-mail address.
4. **Authorization negative tests:** non-staff → denied; PE/entity staff → denied; unauthenticated →
   401; customer user → denied. Both ALLOW and DENY cases covered.
5. **No-duplication test:** X4's failure/retry counts must equal X1's classification of the same rows
   (they share the predicates), so the two can never disagree.
6. **F-046-1 discipline:** any database-backed test targets a disposable clone or `carbontally_test`;
   QA / investor demo / production are never touched. Fixtures are isolated and cleaned up.
7. **Explicit non-verification:** no live-browser UI verification (X5 is out of scope) and no
   production verification.

## 13. Explicit exclusions for this release

Usage analytics · import operations · notification/email delivery operations · AI activity ·
auth/authorization operations views · per-organisation breakdown · issue/review SLA · any X5 console or
frontend work · X7 API runtime metrics · X8 verification stage · alert dispatch or threshold changes
(X2 stays closed and unchanged) · new tables/views/migrations · retention changes · production/G0-D ·
provider/runtime/deployment introspection · S6 `new_version` · RLS steps 3–5 · S8 · I1 · D16/legacy ·
`F-X1-2` · `F-B3-7` · `F-4A1B-1` · B4-D12 · Phase 9 · **OHD findings**.

## 14. New PO decisions required

| ID | Decision | Recommendation |
|---|---|---|
| **X4-D1** | Time windows: approve `24h`/`7d`, or make the first release **window-less**? | **Window-less first**, then add approved windows — smallest surface, no new definitions |
| **X4-D2** | Accept an explicit `truncated` flag for the existing 2000-row read bound? | **Yes** — honesty over silently partial counts |
| **X4-D3** | Is a "failure rate" metric wanted? | **No for this release** — a rate needs an approved denominator |
| **X4-D4** | SLA: flag-only (X2 lineage) or also show the deadline-derived count from `data/reporting.py`? | **Flag-only**, with the deadline-derived figure explicitly deferred |
| **X4-D5** | Confirm the endpoint shape in §9 (names/grouping) at authorisation | As proposed; internal-only authority and F-046-1 unchanged |

**No threshold, KPI, retention period or business meaning is invented anywhere in this contract.**
