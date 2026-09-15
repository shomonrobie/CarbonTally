# CarbonTally Phase 8-X — X1 FEASIBILITY ASSESSMENT (PO decision 3: reuse-first)

**Task:** Phase 8-X `X1` (`…043`) — bounded first release
**Authority:** PO decisions of 2026-09-14 — item 1 (bounded set: **worker/queue visibility + health/worker heartbeat**; runtime/deployment introspection excluded), item 2 (provider/production access **deferred**), item 3 (**reuse existing infrastructure first**; "first perform the feasibility assessment. If a new additive/idempotent migration is genuinely required, stop and present the specific database change for separate PO authorisation")
**Date:** 2026-09-14 · **Type:** FEASIBILITY ASSESSMENT (read-only; no code, no migration, no schema change)

---

## 1. Question

Can the approved bounded X1 set — **worker/queue visibility** and **health/worker heartbeat** — be delivered using **existing** infrastructure, or does it genuinely require a new database migration?

## 2. Answer

> **Existing infrastructure is demonstrably sufficient. NO new database migration is required,
> so no new PO authorisation gate is triggered.**

## 3. Evidence

### 3.1 The authoritative 8-X document already states M1 needs no schema change

`docs/architecture/CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md`, §13:

* **M1** (line 671) — *"Worker & queue operational visibility — backlog, stuck/claimed jobs, retry exhaustion, `workflow_error_count`, `last_error`, stage distribution, oldest-waiting age … **All data already exists** in `document_processing_queue`; **no schema change required**."*
* **M2** (line 672) — *"Health-path correctness + worker liveness — `/health` must exercise the pool path; **expose worker heartbeat/last-tick**"*; finding **B2** (line 213) — *"Worker health / liveness … none — worker has no status surface … Worker failure is **log-only** … **MUST**"* → the deliverable is to **expose** a surface, not to invent storage.

### 3.2 Existing storage that X1 can read (verified live on `carbontally_qa_phase8`)

| Need | Existing infrastructure | Notes |
|---|---|---|
| Queue / backlog / stage / retry data | **`document_processing_queue`** (stage, `attempt_count`, `max_attempts`, `last_error`, `locked_at`, `lock_token`, `workflow_error_count`, `workflow_next_retry_at`, per-stage timestamps — per 8-X A5) | RLS enabled, **4 policies**; complete for M1 |
| Claimed / stuck detection | `locked_at` + `lock_token` on the same table; `manual_review_queue`; `processing_assignments` | no new columns needed |
| Worker activity history | `processing_logs` (RLS, 4 policies), `processing_audit_trail`, `domain_events`, `processing_time_log` | usable as last-tick inputs |
| **Explicit heartbeat storage** | **`dashboard_metrics`** (`id, metric_type, metric_name, metric_value, period, expires_at, created_at`) | an existing generic metric store **with expiry** — a heartbeat row is `metric_type`/`metric_value` + `expires_at`; RLS enabled, **0 policies** ⇒ app-layer-only (written/read by the backend service role), so **no RLS change is needed either** |
| Health surface | `main.py:302` `GET /health`; `api/v3_health.py` `GET /health/realtime` | M2 requires `/health` to exercise the **pool** path (the verified defect) — a code fix, not a migration |
| Ops API surface + authorization | `backend/api/v3_operations.py`, `backend/api/operations_auth.py` (`require_internal_staff()`), existing `/api/v3/ops/**` routes | 8-X A5/M1 authority = **internal staff**, global scope (§ rows 340–341) |

## 4. Consequence for the (excluded) parts

* **Runtime/deployment introspection** (8-X M5, B8/B9) — **excluded** by PO decision 1, and it is the
  part that would have needed provider access (deferred by decision 2). **Not assessed further, not built.**
* **Deployment reproducibility** (`render.yaml` etc., B8) — out of the approved set; would be a code/docs
  change, not a migration. **Not in X1.** 

## 5. Feasibility verdict by deliverable

| Deliverable | Migration required? | Basis |
|---|---|---|
| **Worker / queue visibility (M1)** | **NO** | authoritative doc: "no schema change required"; all fields exist |
| **Health-path correctness (M2, `/health` pool probe)** | **NO** | code fix in the existing health endpoint |
| **Worker heartbeat / last-tick (M2)** | **NO — reuse first** | derive from existing activity rows (`processing_logs` / `document_processing_queue` timestamps) and, if an explicit tick is wanted, write to the **existing** `dashboard_metrics` with `expires_at`. A dedicated `worker_heartbeats` table would be **avoidable**, so per PO decision 3 it must not be introduced |

## 6. Honest limitations of the reuse approach (flagged, not hidden)

1. A heartbeat derived only from activity rows cannot distinguish **"worker idle"** from **"worker dead"** — an explicit tick (written by the worker on each loop) is therefore preferred, and `dashboard_metrics` supports it without a schema change.
2. `dashboard_metrics` has **no RLS policies** (app-layer-only). Consequence: heartbeat rows must be written and read **through the backend** (service role), never from the browser — which matches the internal-staff-only authority required by 8-X.
3. `dashboard_metrics.period`/`expires_at` semantics must be used as designed (expiry = staleness), otherwise the heartbeat becomes a growing table; retention for it is governed by the existing retention configuration, **not** invented here.
4. The **worker process** (`workers/automatic_processing.py`) currently has **no health method** — adding the tick is an **implementation** change inside the authorised X1 scope (code, not schema).

## 7. Status

**X1 FEASIBILITY: COMPLETE — REUSE SUFFICIENT — NO MIGRATION GATE TRIGGERED.**
X1 implementation (bounded set) may proceed under the existing authorisation; implementation has
**not** been started by this assessment.
