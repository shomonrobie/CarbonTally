# CT-MP-SUB-004 — PRODUCTION-READINESS PO FACT-FINDING 01

| Field | Value |
| --- | --- |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01` |
| **Type** | Read-only architecture / codebase fact-finding. **No implementation, no schema change, no migration, no commit, no push, no deploy, no production access.** |
| **Subject** | Decision preparation for the two open PO items from the production-readiness workstream: **P-1** (production performance SLO / NV-9) and **P-2** (Manual Processing notification behaviour / NV-10) |
| **Repository HEAD at time of work** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (`375a48d`, *"FINAL-03: freeze production cutover release"*, Sat Oct 3 03:49:51 2026 +0600) |
| **Branch** | `p8-release-reconciled` |
| **Date of work** | 2026-10-05 |
| **Working tree at start** | Pre-existing uncommitted work only (the CT-MP-SUB-004 implementation + FINAL-03 remediation set). **Nothing was staged, committed, reset or cleaned by this task.** |
| **Status** | **FACT-FINDING COMPLETE — READY FOR PO DECISIONS** |
| **Governance status (2026-10-05)** | **P-1 and P-2 have since been decided and are CLOSED.** See `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (P-1 CLOSED — no dedicated production SLO required for this release; P-2 CLOSED — proactive MP notifications not required; allocation/release remain audit-only). This report's findings are **unchanged**; only their *"remains a PO decision"* status is superseded (see §9). **Subsequent scope clarification (Notification fact-finding 02, 2026-10-05):** the P-2 evidence set above covers the Manual Processing **coverage allocation/release** surface; whether *a document batch entering Manual Processing* requires a notification remains **OPEN — PO DECISION REQUIRED** (see `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md` §7.3 / §8.2). |

---

## 1. Task identification

### 1.1 Purpose

Give the Product Owner enough verified evidence to make exactly two remaining
decisions for CT-MP-SUB-004 Manual Processing:

* **P-1** — is a production performance SLO required, and if so what values;
* **P-2** — must Manual Processing allocation/release emit a proactive
  user-facing notification.

The task does **not** solve those decisions, does **not** invent an SLO, does
**not** invent notification behaviour, and does **not** expand the architecture.

### 1.2 Scope

| In scope | Out of scope |
| --- | --- |
| Inventory + inspection of existing performance/SLO architecture | Writing any SLO |
| Inventory + inspection of the existing notification architecture | Writing any notification producer |
| Determining what NV-9 / NV-10 already satisfy | Re-verifying F-4/F-7/F-9/F-11/NV-5/NV-6 |
| Isolating the minimum residual PO question(s) | Accepting / certifying production readiness |
| Stating what a verifier should re-check afterwards | Independent verification itself |

### 1.3 Governing documents read first

| Document | Path | Status used here |
| --- | --- | --- |
| PROD-READINESS-01 report (authoritative for P-1/P-2 statements) | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md` | authorises F-4, F-7, F-9, F-11, NV-5, NV-6, NV-9, NV-10; §11/§12/§13 carry the P-1/P-2 statements |
| CT-MP-SUB-004 PO decision record | `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` | PD-1…PD-7 |
| CT-MP-SUB-004 independent verification report | `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` | defines the NV-n list (§19) and the findings (§18) |
| CT-MP-SUB-004-PD5-FIXTURE-01 report | `docs/architecture/CT-MP-SUB-004-PD5-FIXTURE-01-report.md` | fixture reused by NV-9 |
| CT-MP-SUB-004-PD5-VERIFY-01 report | `docs/architecture/CT-MP-SUB-004-PD5-VERIFY-01-report.md` | confirms NV-9/NV-10 were still open |
| CT-UX-MP-SUB-003 UI/UX specification ("D2") | `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | the authoritative UI/UX spec for these surfaces |
| Demo Lab README | `tools/demo_lab/README.md` | local stack / fixture conventions |
| `AGENTS.md` | repository root | the governing agent constitution |

> **Definitional note (important).** **`NV-9` and `NV-10` are not product
> requirements.** They are entries **9** and **10** of the *"Explicit list of
> anything NOT verified"* table in `CT-MP-SUB-004-independent-verification-report.md`
> §19 — i.e. the independent verifier's own list of open verification gaps:
>
> * `independent-verification-report.md:665` → `| NV-9 | Long-running/performance behaviour | Out of scope |`
> * `independent-verification-report.md:666` → `| NV-10 | Email/notification side-effects | None expected from this surface |`
>
> The PO instruction therefore authorised *closing two verification gaps*, not
> building two new features. This distinction drives the whole finding below.

### 1.4 Method and provenance key

Every material statement below is labelled with its provenance:

| Label | Meaning |
| --- | --- |
| **[AUTH]** | Existing authoritative CarbonTally architecture, ratified PO decision, or repository code/schema that already exists and is in use |
| **[IMPL]** | Behaviour produced by the current CT-MP-SUB-004 production-readiness implementation (uncommitted worktree) |
| **[CLINE]** | A claim made by Cline in `CT-MP-SUB-004-PROD-READINESS-01-report.md` |
| **[INFER]** | This task's inference from the evidence (explicitly **not** an established CarbonTally requirement) |

Commands used are listed in §8; nothing in the repository was modified except the
creation of this report file.

---

## 2. P-1 findings — existing performance / SLO architecture

### 2.1 Headline determination

> ## ⛔ NO EXISTING AUTHORITATIVE PRODUCTION SLO FOUND
>
> CarbonTally has **no ratified production latency, throughput, concurrency or
> availability SLO** anywhere in the repository — and this absence is
> **deliberate, explicitly recorded, and PO-owned**. Five independent
> authoritative artefacts state it in their own words (§2.2).

What CarbonTally **does** already have is a **measurement** standard (one
PO-supplied observation threshold, one derived statistic, one rolling window)
and two **workflow-turnaround** SLA mechanisms. None of those is a production
performance SLO, and none of them bounds the Manual Processing endpoints. The
distinction is the substance of this section.

### 2.2 Existing authoritative standards found — full inventory

| # | Artefact | Exact evidence (path + symbol/line) | What it actually is | Is it a production SLO? |
| --- | --- | --- | --- | --- |
| 1 | **Phase 9 baseline §33 "Availability & SLO/SLA Intelligence"** [AUTH] | `docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md:831` → *"No SLO/SLA values are ratified by this baseline."* (the section lists uptime / error budget / latency objectives as *future discovery* items only) | A **statement that no SLO values exist** | **No** — explicitly disclaims SLO values |
| 2 | **P8 I5/I8 PO decision & authorization §8 "SLOs"** [AUTH] | `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md:746` → *"**NOT YET AUTHORIZED — PO/PRODUCT DECISION REQUIRED**"* … *"**No numerical SLO may be invented by Cline.**"*; `:815` lists *"3. SLO targets;"* among eight preconditions for any I8 authorization | A **PO reservation**: SLO targets are a prerequisite the PO has not yet supplied, and agents are forbidden to invent one | **No** — and it forbids agent invention |
| 3 | **Capability coverage matrix — gap G-21** [AUTH] | `docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md:1072` → *"**G-21 \| No committed SLO** or configured alert thresholds/recipients … \| **D-26 (commercial) / L8-A governance**"*; `:1138` → *"**L8-A**: SLO/SLA commitments, alert thresholds/recipients, incident runbook…"* | An **open commercial/governance gap**, formally tracked with a named owner | **No** — recorded as missing |
| 4 | **8-X discovery G10** [AUTH] | `docs/architecture/CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md:252` → *"\| G10 **No availability/SLO definition** \| none \| **MISSING** \|"* | Confirms **no availability/SLO definition exists** | **No** — recorded MISSING |
| 5 | **X7 API runtime metrics contract** [AUTH] | `docs/architecture/CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915.md:94–97` (stop conditions: *"M4 'slow endpoints' needs a **threshold**; M1/M3 need a **window/statistic**. The PO's X2 ruling forbids inventing thresholds"*); `:103–115` (the six values the PO had to supply) | The **contract that forced** a PO decision on latency semantics | **No** — it is the contract written *before* the decision |
| 6 | **X7 API runtime metrics — PO decisions `X7-D1…X7-D7`, implemented** [AUTH] | `backend/domain/api_metrics.py:22` `SLOW_THRESHOLD_MS = 1000` *(X7-D6 — "a request is slow at or above 1,000 ms")*; `:25` `WINDOW_SECONDS = 3600` *(X7-D5 — rolling 60-minute window)*; `:28` `FLUSH_INTERVAL_SECONDS = 300` *(X7-D2)*; `:34–40` one merged series `API_RUNTIME` / `api_v3_rolling_60m` *(X7-D1/D3)*; `:43` `INSTRUMENTED_PREFIX = "/api/v3/"` *(X7-D7)*. Consumed by `backend/services/api_metrics.py`; surfaced read-only by `backend/api/v3_operations.py` | **The only PO-supplied latency number in the repository**: 1,000 ms = "slow", observed as **p95 over a rolling 60 minutes** — a **monitoring/observability** standard | **Observability threshold, NOT an SLO.** No target, no budget, no consequence, no per-endpoint bound |
| 7 | **X1/X4 configured queue SLA** [AUTH] | `backend/data/queue_settings.py` (`sla_hours`, default `48`; `is_configured()` distinguishes configured from defaulted); `backend/services/operational_intelligence.py:122` `aggregate_sla(...)` with `sla_state` ∈ `configured`/`not_configured`/`unknown` and the **`X4-D4` flag-only** rule (`:10`, `:156`); PO-closed in `docs/cline/reports/CT-P8-P8X-X4-IMPLEMENTATION-AND-IV-20260914-064.md` | A **queue-turnaround SLA in hours** for processing items, read from the persisted `sla_breached` flag | **No** — a workflow-turnaround signal, not an API latency/throughput SLO (and it reports `not_configured` honestly) |
| 8 | **`sla_definitions` / `sla_compliance` tables** [AUTH] | DDL `supabase/migrations/00000000000000_init_schema.sql:1974` and `:1988` (RC2 legacy schema); referenced in code only by `backend/routes/reports.py` and `backend/routes/admin/dashboard.py`; **0 rows at audit** (matrix `:1072`); no CT-MP-SUB-004 route touches them | **Legacy, unconfigured** SLA reference tables | **No** — empty and unrelated to these endpoints |
| 9 | **X5 operations console / X7 reporting surface** [AUTH] | `docs/architecture/CARBONTALLY_PHASE8X_X5_OPS_CONSOLE_CONTRACT_20260915.md`; `backend/api/v3_operations.py` (read-only X7 endpoint) | Read-only **operational visibility** | **No** |
| 10 | **External (non-authoritative) performance proposal** [INFER: not CarbonTally-ratified] | `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/08_performance_plan.md` (tier plans: `:118` *"Baseline throughput metrics captured per worker type (jobs/min, p95 job duration)"*; `:64` a *"300 ms sustained"* search trigger; `:105` *"Concurrent active users \| ~10% of seats at peak"*); `CarbonTally_RC2_Architecture_Freeze.md` (*"pooler sizing review at ~500 concurrent tenants"*) — both inside the `Final_Kimi/…_Audit_Report/` **agent-audit** folder | An **external audit artefact** that *assumes* scale numbers and *proposes* triggers | **No.** It sits outside `docs/architecture/`, is **not referenced** by `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` or `ARCHITECTURE_DECISIONS.md` (grep: no hits), and contains no ratified PO decision. Listed only so it is not mistaken for a standard |

**Numeric performance references that actually exist in ratified code (complete
list):** `SLOW_THRESHOLD_MS = 1000` (X7-D6), `WINDOW_SECONDS = 3600` (X7-D5),
`FLUSH_INTERVAL_SECONDS = 300` (X7-D2), `queue_settings.sla_hours = 48`
(X1/X4, configurable). Every other performance number in the repository is
either an external-audit assumption (row 10) or a feature-local test budget (§2.3).

### 2.3 What CT-MP-SUB-004 actually implemented and measured (NV-9) [IMPL]

**Tooling:** `tools/demo_lab/perf_mp_baseline.py` (226 lines, new in this
workstream). Its own docstring states the status of its numbers exactly:

* `perf_mp_baseline.py:23–26` → *"THRESHOLDS: these are LOCAL Demo-Lab
  INTERACTIVE budgets (the UI must render its data within roughly one second on
  a developer workstation), **NOT** a production throughput/latency SLO. No
  production-scale SLO exists in the repository; if one is required it is a PO
  decision."*
* `perf_mp_baseline.py:48–56` → `BUDGETS` (declared in the script, p95, ms):
  `customer_entitlement 500`, `consultant_coverage 500`, `admin_coverage 500`,
  `admin_client_search 500`, `allocate 750`, `release 750`.
* `perf_mp_baseline.py:58–63` → `REQUIRED_INDEXES` =
  `uq_consultant_mp_allocations_active`, `idx_consultant_mp_allocations_firm`,
  `idx_consultant_mp_allocations_org` (existence asserted with
  `lab.psql_scalar("SELECT indexname FROM pg_indexes …")`, `:184–188`).
* `perf_mp_baseline.py:66–71` → the percentile helper computes **p50 and p95**
  from 12 (default) samples; there is **no p99**, and no throughput/concurrency
  measurement. Measurement is **end-to-end** against the running local stack
  (gateway + FastAPI + Supabase Postgres) using **real password-grant logins**.
* `perf_mp_baseline.py:196–200` → the evidence payload self-describes its scale:
  `"data_scale": "fixture-scale (a handful of rows), NOT production scale"`.

**Measured result** (12 iterations, live local stack) — [CLINE]
`CT-MP-SUB-004-PROD-READINESS-01-report.md` §11 table: `customer_entitlement`
p50 106 ms / p95 154 ms; `consultant_coverage` 89/103; `admin_coverage` 76/100;
`admin_client_search` 71/81; `allocate` 79/94; `release` 78/88 — **6/6 budgets
PASS + 3/3 index assertions**, run EXIT=0. Evidence is written outside the
repository by `lab.EVIDENCE_DIR` (= `$DEMO_LAB_STATE_DIR/evidence`, default
`~/ct_local_env/demo_lab/evidence`); the run cited in §11 is
`mp_perf_baseline_20261005T020040Z.json`, with `mp_perf_baseline_latest.json`
alongside it (both verified present on this workstation).

The measured endpoints are the four Manual Processing routes registered in
`backend/api/v3_manual_processing_coverage.py` — `@router.get("/organizations/{organization_id}/manual-processing")` `:124`,
`@router.get("/consultants/me/manual-processing/coverage")` `:248`,
`@router.post("/consultants/me/manual-processing/allocations")` `:266`,
`@router.delete("/consultants/me/manual-processing/allocations/{allocation_id}")` `:377`
— plus two Admin routes in `backend/api/manual_processing_admin.py`:
`@router.get("/coverage/{consultant_id}")` `:648`, and
`@router.get("/organizations")` `:896` (the F-11 name search).

### 2.4 Relationship between the existing standards and these budgets [INFER]

| Question | Answer |
| --- | --- |
| Does CT-MP-SUB-004 conform to an existing platform SLO? | **There is no platform SLO to conform to.** The only ratified latency constant is X7-D6's **1,000 ms "slow"** observation threshold, and all six measured p95 values sit **below** it — so the surface is not flagged slow by the existing instrumentation. |
| Are the budgets feature-specific or inherited? | **Feature-specific.** They are new constants declared inside `perf_mp_baseline.py`; they inherit *nothing* from X7 or X4. The 500 ms read / 750 ms write split is this workstream's own engineering choice, documented as such. |
| Is there any conflict with an existing standard? | **No conflict found.** The budgets are *stricter* than the X7-D6 observation threshold, which is consistent, not contradictory. |
| Should the budgets become contractual? | **That is exactly the unanswered PO question** — see §6. An agent must not promote a local test budget to a commercial commitment. |

### 2.5 What the Demo Lab can and cannot establish

| Establishable locally (already established) | **Not** establishable from the Demo Lab |
| --- | --- |
| Correctness + relative latency of the six hot paths on one developer workstation | Any **absolute** production latency (different CPU, network RTT to Supabase, cold caches) |
| p50 / p95 and the latency ordering between operations | **p99** — 12 samples cannot support a p99 claim |
| That the hot-query index set exists | **Sustained request rate / throughput** under load |
| That the N+1 batch read (F-11/NV-9) collapsed client-name resolution to one query (`test_ct_mp_sub_004_prod_readiness.py` asserts `calls["get_many"] == 1`, `calls["get"] == 0`) | **Concurrent-user** behaviour, queue contention, pooler / connection-limit behaviour |
| That the allocate→release write pair returns 200 and restores the fixture baseline | **Instance sizing / autoscaling / cost** — commercial + infrastructure decisions |
| — | Any **production-topology** measurement: no APM exists (X7 contract §1 — *"there is no request-timing middleware, no metrics middleware and no APM"*), and no load-test tooling exists in the repository |

No load-testing infrastructure exists: `tools/b7_pool_soak.py` is a local
connection-pool soak helper, and `backend/tests/integration/` contains runtime
*correctness* tests (e.g. `test_api_metrics_x7_runtime.py`,
`test_operational_intelligence_x4_runtime.py`), **not** performance tests.

### 2.6 Conclusion for P-1

* **NO EXISTING AUTHORITATIVE PRODUCTION SLO FOUND** — confirmed against five
  authoritative statements (§2.2 rows 1–5).
* CT-MP-SUB-004's NV-9 work **closes the verification gap** (a reproducible,
  honest local baseline with declared budgets exists and passes) but
  **cannot and does not create a production SLO**.
* A PO decision **is** still required **if and only if** the business wants a
  committed production performance target for these (or any) endpoints. That is
  a commercial/operational commitment the repository explicitly reserves to the
  PO (`CT-MP-SUB-004-PROD-READINESS-01-report.md` §13 P-1;
  `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md:746`).

---

## 3. P-2 findings — existing notification architecture

### 3.1 Determination: an authoritative notification system already exists

> ## ✅ YES — CARBONTALLY ALREADY HAS AN AUTHORITATIVE, PO-RATIFIED, DURABLE NOTIFICATION ARCHITECTURE
>
> It is not a stub. It is a ratified capability (**D40**, with the **D11**
> event vocabulary and the **X2** alerting extension), persisted in first-class
> tables, exposed through authenticated read APIs, populated by **best-effort
> producers on the canonical action paths**, deduplicated by a real unique
> index, delivered in-product **and** by email, with recorded delivery outcomes
> and a bounded retry policy. **Nothing about it needs to be redesigned** — and
> per the task's governance rule, it must not be.

### 3.2 Exact architecture — files, tables, routes

| Layer | Exact artefact | Evidence |
| --- | --- | --- |
| **Tables (DDL)** | `public.notifications` (per-recipient rows) and `public.notification_delivery` (per-attempt delivery tracking) | `supabase/migrations/00000000000000_init_schema.sql:1409` and `:1429`; comments `:1427`/`:1443`. Columns: `notifications(id, recipient_type, recipient_id, notification_type, title, message, priority, link, metadata, is_read, read_at, is_dismissed, dismissed_at, created_at, updated_at)`; `notification_delivery(id, notification_id FK→notifications ON DELETE CASCADE, channel, status, sent_at, delivered_at, opened_at, error_message, metadata, created_at, updated_at)` |
| **Idempotency columns + index** | `notifications.event_key`, `notifications.actor_domain`; unique partial index **`uq_notifications_event_key`** = `UNIQUE (recipient_id, event_key) WHERE event_key IS NOT NULL` | migration `supabase/migrations/20260902050000_phase5_notification_event_key.sql:11–16` |
| **Legacy email tables** | `public.email_templates` (`:134`), `public.email_logs` (`:1748`), `public.notification_templates` (`:1748` area, `:151`) | same init schema |
| **Repository (data layer)** | `backend/data/notifications.py` — `NotificationsRepository`. Key methods: `list_for_user` `:37`, `count_for_user` `:60`, `create` `:71`, `mark_read` `:100`, `mark_all_read` `:109`, **`create_idempotent`** `:116`, `support_staff_user_ids` `:169`, `entity_participant_user_ids` `:180`, `internal_ops_user_ids` `:213`, `email_for_user` `:229`, `record_delivery` `:237`, `prune_operational_alerts_before` `:270` | read directly |
| **Domain model** | `backend/domain/operations.py:160` `class Notification` — *"A row of `notifications` (real schema: per-recipient rows)"* | read directly |
| **Read API (in-product inbox)** | `backend/api/v3_notifications.py` — `GET /api/v3/notifications` (`list_notifications`, clamped `limit 1..500`, newest-first), `POST /api/v3/notifications/{id}/read`, `POST /api/v3/notifications/read-all` | `:13` prefix; registered in `backend/api/router.py:39,223` |
| **Wiring** | `notifications: NotificationsRepository` on the `RepositoryBundle` | `backend/api/dependencies.py:67,354,461` |
| **Frontend inbox** | `frontend/src/v3/NotificationsPage.jsx`; PE bell `frontend/src/v3/pe/PeNotificationsBell.jsx` (+ `PEShell.jsx`); bell on shared shells in `frontend/src/v3/components/V3Layout.jsx`; legacy preferences UI `frontend/src/components/NotificationSettings.jsx` | file inventory |
| **Personal-notification settings API** | `backend/api/v3_settings.py:317` (platform email sender config: shows *which address* notifications come from, never the provider secret) | grep |

### 3.3 Producer model — where notifications originate, and how

There is **no outbox table and no notification queue**. Producers write the
notification row **directly**, in the same request/worker path, as a
**best-effort side effect after the business action and its immutable audit have
committed**. This is the ratified convention, stated verbatim in several places:

| Producer | File / symbol | Ratified statement of the convention |
| --- | --- | --- |
| D38 work-item assignment | `backend/services/work_items.py:191` `_notify_assignee(repos, *, user_id, event_key, item_id, action, actor_domain)` → `repos.notifications.create_idempotent(...)` `:198`, `notification_type="work_item.assigned"`, `link=f"/ops/items/{item_id}"`, wrapped in `try/except` + `_log.warning` | *"The assignment/audit are already committed; a notification failure must not fail the business action but is logged so it is detectable."* |
| D40/D39 PE ↔ Ops messaging | `backend/api/v3_messaging.py:519–526` (`support_staff_user_ids()` / `entity_participant_user_ids(...)` → `create_idempotent`) | D39 boundaries (N1): PE→CarbonTally only |
| D11 consultant lifecycle (5 events) | `backend/services/consultant_lifecycle.py` — `_emit(...)` `:63`, plus resolvers `_firm_recipient_user_ids` `:105`, `_engaged_firm_ids` `:122`, `_internal_ops_recipient_user_ids` `:139` | module docstring `:44–61`: *"Durable, not ephemeral… The in-process `EventBus` is deliberately NOT used (fire-and-forget, non-durable)"*; *"Deterministic, server-generated keys"*; *"Server-derived recipients only… A request can never choose a recipient"*; *"Best effort, never fatal"*; *"Emitted only after a successful transition"* |
| X2 operational alerting | `backend/services/operational_alerting.py` (`OperationalAlertingService`); thresholds in `backend/domain/operational_alerts.py` | docstring `:8–20`: recipients = internal staff with `can_view_all`; dedup via `create_idempotent`; *"delivery is in-product + email, and a failed email is retried 3 times over ~15 minutes"*; *"a notification failure must never break processing"* |
| Backup outcomes (BACKUP-01/02) | `backend/main.py:333` `_notify_backup_outcome(...)`; `backend/api/v3_backups.py:187` | `v3_backups.py:177–183`: *"Idempotent notification (best effort)… reporting a successful backup as failed because a notification queue was unavailable would be a lie."* |
| Discovery / other | `backend/api/v3_discovery.py:691` (`repos.notifications.create(...)`) | pre-existing |

**Existing supported event categories** (`notification_type` values established
by code, not invented here): `work_item.assigned` (D38/D40);
`consultant.lifecycle.accepted` / `.submitted_to_qc` / `.qc_outcome` /
`.customer_decision` / `.rework` (D11 — `consultant_lifecycle.py:90–92`);
`pe_msg.message` / `pe_msg.ops_reply` (D39); `ops_alert_%` (X2 operational
alerts, also the retention scope in `prune_operational_alerts_before`); `backup`
(BACKUP-01/02). The column is free-form `VARCHAR` with **no CHECK constraint**
(`docs/cline/CARBONTALLY_P6_2E_INDEPENDENT_VERIFICATION_REPORT.md:402`).

### 3.4 Recipient resolution

Recipients are **always derived server-side from the authoritative
relationship**; there is **no client notification-creation endpoint** (D40
implementation report §7 — *"verified 405"*). Existing resolvers:

| Resolver | File / symbol | Recipient set |
| --- | --- | --- |
| `support_staff_user_ids()` | `backend/data/notifications.py:169` | active **internal** staff (`entity_id IS NULL`) whose role grants `can_manage_staff` |
| `internal_ops_user_ids()` | `:213` | active internal staff whose role grants `can_view_all` (the PO-approved X2 set, `PX-6` decision 3) |
| `entity_participant_user_ids(conversation_id, entity_id, exclude_user)` | `:180` | PE staff participants of an **own-entity** conversation |
| `_firm_recipient_user_ids` / `_engaged_firm_ids` | `backend/services/consultant_lifecycle.py:105,122` | active firm members / firms holding an **active** consultant-client grant |
| `organizations.get_members(...)`, `consultants.list_firm_members(...)`, `consultants.list_active_client_grants(...)` | (named in `CARBONTALLY_P6_2E_INDEPENDENT_VERIFICATION_REPORT.md:401`) | org members / firm members / active grants |

### 3.5 Delivery mechanism

| Aspect | Finding |
| --- | --- |
| In-product | The row **is** the in-product notification; read via `GET /api/v3/notifications` (D40.2 — *"list/read/read-all + pagination + realtime"*) |
| Email | `backend/routes/notifications.py:73` `send_email(...)` → `from services.v3_email import send_platform_email` (**CT-FINAL-02 EMAIL-CONFIG-01**): delivery goes through the canonical platform mailer with the **admin-configured** provider (Resend or SMTP) and sender; *"a provider that is not configured reports a failed delivery instead of a fabricated success"* |
| Email services | `backend/services/v3_email.py` (182 lines), `email_provider.py` (538), `email_sender.py` (151), `email_service.py` (366) |
| Realtime | `frontend/src/context/RealtimeContext.jsx` (bell/badge refresh) — note its `:276` comment: the browser `supabase.from('notifications')` read/write was **removed** because of deny-by-default RLS, i.e. the product already treats this table as RLS-gated |
| Practical note [INFER] | D11/D38/D40 producers create the **in-product row only**; the in-product **+ email** fan-out is what X2's alerting service adds. A future MP producer's channel choice is therefore a real decision, not a foregone conclusion |

### 3.6 Retry and failure behaviour

| Aspect | Finding (exact) |
| --- | --- |
| Producer-level failure | **Swallowed and logged** — the business action is already committed (`work_items.py:208`, `v3_backups.py:197`, `consultant_lifecycle.py` `_emit`) |
| Email delivery retry | X2: **up to 3 attempts**, configurable delay (default ≈300 s ⇒ ~15 min), then `notification_delivery.status='failed'` + `error_message` + attempt count, and the loop **stops** (`domain/operational_alerts.py` → `DELIVERY_MAX_ATTEMPTS` / `DELIVERY_RETRY_WINDOW_SECONDS`; verified in `docs/cline/reports/CT-P8-P8X-X2-IMPLEMENTATION-AND-IV-20260914-062.md` — *"O4 — failing sender ⇒ exactly 3 attempts, then `notification_delivery.status='failed'` with the provider error recorded; no 4th attempt — **PASS**"*) |
| Delivery recording | `NotificationsRepository.record_delivery(...)` `:237` — *"Failures are recorded honestly (`status='failed'` + `error_message`); nothing is silently swallowed."* |
| Transactionality | **Notification delivery is NOT transactional with the business operation** — by ratified design (best-effort, post-commit) |
| Duplicate prevention | `create_idempotent` + `uq_notifications_event_key`; the DB index is the final boundary (`ON CONFLICT (recipient_id, event_key) WHERE event_key IS NOT NULL DO NOTHING`) |
| Observability / audit | Every X2 dispatch writes a canonical append-only `audit_trail` entry (`operational_alerting.py:44` `AUDIT_ACTION = "operational_alert_dispatched"`); other producers rely on the existing audit record of the business action itself |
| Business operation independent of delivery? | **Yes, by design** — a ratified invariant, not an accident |

### 3.7 Existing notification tests (reuse targets)

| Test | File | What it covers |
| --- | --- | --- |
| D11 lifecycle producer vocabulary + idempotency | `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | five events, deterministic keys, server-derived recipients, replay safety (`test_d11_service_layer_replay_is_idempotent`) |
| D40 inbox API | `backend/tests/unit/api/test_v3_notifications.py` | list / pagination / read / read-all |
| X2 alerting runtime (real DB) | `backend/tests/integration/test_operational_alerting_x2_runtime.py` | recipient resolution, 3-attempt failure path, delivery rows |
| CT-FINAL-01 notification sender | `backend/tests/unit/api/test_ct_final_01_notification_sender.py` | platform mailer / honest failure |
| E2E Phase-6 allow / deny / deeplink / invariants | `backend/tests/e2e/test_p6_2f_{allow_workflows,deny_matrix,deeplink_iv_n6,invariants}.py` | notification behaviour under the Phase-6 acceptance gate — `PO-PHASE6-F-ACC-20260910` requires *"notification behaviour"* in the acceptance scope |
| Idempotency fake | `backend/tests/unit/api/fakes.py:2980` | in-memory stand-in for `uq_notifications_event_key` |
| Notification events CRUD | `backend/tests/unit/api/test_v3_legacy_reimplementation.py` | D25 repository/API alignment |
| CT-MP-SUB-004 audit-only behaviour | `backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py` (`class TestNV10NotificationBehaviour`) | the three MP cases — see §4 |

### 3.8 The Manual Processing surface today: **no producer exists** [AUTH + IMPL]

Verified by direct grep of the four MP implementation files:

```
grep -rn 'notifications\|create_idempotent\|Notification' \
  backend/api/manual_processing_admin.py backend/api/manual_processing_auth.py \
  backend/data/manual_processing.py backend/domain/manual_processing.py
→ (no matches)
```

What the MP allocation paths **do** write is a **durable audit record** through
the existing audit infrastructure:

* `backend/api/v3_manual_processing_coverage.py:350` — `action="manual_processing:allocation_created"` (consultant allocate; `details` include `allocation_id`, `organization_id`, `consultant_client_id`, `reason`, `via: "consultant"`);
* `backend/api/v3_manual_processing_coverage.py:408` — `action="manual_processing:allocation_released"` (consultant release);
* `backend/api/manual_processing_admin.py:761` — `manual_processing:allocation_created` (admin allocate); `:804` — `manual_processing:allocation_released` (admin release).

**Therefore: no notification producer, and no notification, exists for
allocation/release.** This is the factual basis for the NV-10 classification in §4.

### 3.9 Explicitly *not* found

* No **outbox** table and no transactional-outbox pattern (grep for `outbox` → no application-code hits).
* No **notification-preferences** table/API governing *which* product events a user receives (the in-box has read/unread + pagination only; `frontend/src/components/NotificationSettings.jsx` is a legacy client-side UI).
* No **notification worker** — notifications are not queued or retried as a domain concept; only X2's bounded email retry and the processing queues exist.
* No **MP-specific notification requirement** in the MP governing documents:
  grep of `CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` for
  `notif|email|performance|latency|audit` → **no matches**; grep of
  `CarbonTally_Manual_Processing_Subscription_Options.md` for
  `notif|email|performance|latency|SLO` → **no matches** (only the phrase
  *"client slots available/used"*). The D2 UI/UX spec is **silent** on
  notifications for these surfaces.

---

## 4. NV-10 assessment — strict classification

The four categories are kept **disjoint**. "Already satisfied" describes what
exists **today**, independent of any new decision.

### 4.A — ALREADY SATISFIED (by the existing CarbonTally notification architecture)

**Nothing about the Manual Processing workflow's notification behaviour is
already satisfied by an existing MP-specific producer, because none exists
(§3.8).** What *is* already satisfied is the **architecture the decision would
reuse** — i.e. the capability, not the behaviour:

1. A durable, RLS-respecting, per-recipient notification store
   (`public.notifications` + `public.notification_delivery`) — [AUTH].
2. Idempotent creation with a server-supplied deterministic `event_key`
   (`create_idempotent` + `uq_notifications_event_key`) — [AUTH].
3. Server-side recipient derivation helpers, including exactly the sets a
   coverage-change event would need (firm members / active client grants /
   internal ops) — [AUTH] (`consultant_lifecycle.py:105,122,139`).
4. An authenticated in-product inbox + bell, incl. the PE shell — [AUTH].
5. A platform email path with an **honest** failure mode and a bounded retry
   policy — [AUTH] (`v3_email.send_platform_email`; X2 3-attempt rule).
6. A best-effort, post-commit producer convention that can never break the
   business action — [AUTH] (`work_items.py`, `v3_backups.py`,
   `consultant_lifecycle.py`).
7. **A durable audit record for every MP allocation/release state change**,
   which is what the MP surface *does* emit today — [AUTH].
8. An existing precedent for exactly this shape of event: **D11's
   `consultant.lifecycle.accepted`** notifies firm members / client org on an
   engagement transition. A coverage-grant event would be the same pattern
   applied to a different transition — [INFER: pattern, not an existing event].

### 4.B — PARTIALLY SATISFIED (exists, but does not cover the MP workflow)

| Item | State |
| --- | --- |
| Notification *infrastructure* | Complete and ratified — see 4.A. |
| Notification *coverage of the MP workflow* | **Absent.** No producer is wired to `consultant_allocate_client` (`v3_manual_processing_coverage.py:266`), `consultant_release_client` (`:377`), admin allocate (`manual_processing_admin.py:676`), or admin release (`:787`). |
| Documented behaviour for a reviewer | **Now satisfied by documentation + tests** rather than by a feature: `CT-MP-SUB-004-PROD-READINESS-01-report.md` §12 declares *audit-only*, and `test_ct_mp_sub_004_prod_readiness.py::TestNV10NotificationBehaviour` asserts it. So a reviewer **can** now tell "missing notification" from "defect": it is *intended*. |

### 4.C — NOT SATISFIED (genuinely does not exist)

1. **No notification is emitted when sponsored Manual-Processing coverage is
   granted** (consultant or admin allocate).
2. **No notification is emitted when it is withdrawn** (consultant or admin release).
3. **No recipient matrix exists** for these events (who should be told: the
   client org's owner/admin? the *consultant's* own team? internal ops? nobody?).
4. **No event-key namespace / `notification_type` vocabulary** exists for them
   (compare D11's `consultant.lifecycle.*` namespace).
5. **No copy/template** exists for such a message.

Items 1–5 are the *only* genuine gaps. Items 2–5 are consequences of item 1:
nothing exists because the decision "should anyone be told at all?" has not been
taken.

### 4.D — NOT ACTUALLY REQUIRED (identified as out of scope / not implied)

These were **not** requested by any authoritative document, and this
fact-finding finds no basis for treating them as requirements:

| Item | Why it is not required |
| --- | --- |
| A **new notification provider or channel** | The platform already has in-product + email via `send_platform_email`; a provider decision is not implied by NV-10. |
| A **new event/outbox framework** | The ratified producer convention is direct, best-effort, post-commit. Introducing an outbox would contradict D40/D11/X2 and violate the "do not redesign" rule. |
| A **new MP-specific notification bus / `EventBus`** | Explicitly rejected precedent: `consultant_lifecycle.py:46` — *"The in-process `EventBus` is deliberately NOT used (fire-and-forget, non-durable)."* |
| **Notifying on every allocate/release by default** | Nothing in D2, the MP subscription product doc, or the PO decision record requires it. The absence of a requirement is the finding. |
| **Dedicated per-recipient preferences for these events** | No preference model exists for any product event; inventing one is scope expansion. |
| **Replacing the audit records** | The audit trail is an existing invariant (AGENTS.md §17); a notification would be **additive**, never a replacement. |
| **Treating NV-10 as a defect to fix** | The independent verifier's own words were *"Email/notification side-effects — **None expected from this surface**"* (`independent-verification-report.md:666`). NV-10 was raised to make the behaviour *explicit*, not to demand a feature. |

---

## 5. Minimum PO decisions required

The question posed is answered strictly per item. **Neither question is answered
here.**

### P-1 — production performance SLO / NV-9

> ## PO DECISION REQUIRED

**Reason.** No authoritative production SLO exists anywhere in the repository,
and the repository explicitly reserves the value to the PO while forbidding
agent invention (§2.2 rows 1–5, esp. `CARBONTALLY_P8_I5_I8_…:746` —
*"No numerical SLO may be invented by Cline."*). CT-MP-SUB-004 could not and did
not create one.

**The smallest precise question the PO must answer:**

> **Is a committed production performance target required for the Manual
> Processing coverage operations?**
>
> * **If NO** → no further work; the existing local interactive budgets
>   (`tools/demo_lab/perf_mp_baseline.py`) and the X7 observability threshold
>   (p95 in a rolling 60 min vs 1,000 ms) remain the only performance references,
>   and NV-9 stays a local, non-contractual baseline. *No code change; P-1 closes.*
> * **If YES** → the PO must additionally supply **the values and their scope**
>   for at least: (a) the latency statistic(s) and target (e.g. p95/p99 in ms);
>   (b) the measurement population/window; (c) the endpoints in scope; and
>   (d) whether it is a commercial commitment (with consequences) or an internal
>   engineering objective.

Two existing PO-supplied anchors the PO may (but need not) adopt rather than
invent anew — reported here **as existing facts**, not as a recommendation:
**X7-D6 = 1,000 ms** ("slow", the only ratified latency number), and the
**X1/X4 queue-turnaround SLA** (`queue_settings.sla_hours`, default 48), which
covers *processing turnaround*, a different dimension from request latency.
Selecting or rejecting either is the PO's call.

### P-2 — Manual Processing notification behaviour / NV-10

> ## PO DECISION REQUIRED

**Reason.** CarbonTally already has an authoritative notification architecture
(§3) and already has an *audit-only* behaviour for MP that is documented and
tested. Whether MP should **additionally** emit a proactive user-facing
notification is a **new product behaviour** with recipient, consent, copy and
channel implications — the same class of decision the PO reserved for X2
(`PX-6`: *"no invented thresholds; no invented recipient lists"*) and D11
(*"the exact event constants/keys and the recipient matrix are not defined
here"*). An agent must not decide it.

**The smallest precise question the PO must answer:**

> **Should granting or withdrawing sponsored Manual-Processing coverage notify
> anyone?**
>
> * **If NO (retain audit-only)** → the current documented + tested behaviour
>   stands; **no code change is required** and P-2 closes. (Consistent with the
>   verifier's own note that none was expected.)
> * **If YES** → the PO must specify, minimally: (a) **which** transitions
>   (allocate only / release only / both / admin-only variants); (b) **which
>   recipients** (client org owner-admin via `organizations.get_members`, the
>   consultant firm's own members via `consultants.list_firm_members`,
>   CarbonTally internal ops via `support_staff_user_ids`, or a subset); and
>   (c) **which channel(s)** (in-product only, or in-product + email).

Nothing beyond (a)–(c) is needed: the event-key namespace, `notification_type`
values, producer placement, idempotency, best-effort semantics, retry policy and
tests all follow mechanically from the **existing** D11/D40/X2 precedent once
those three values are supplied — that is an implementation decision, not a PO
decision, and is **not** part of the question.

### Summary

| Item | Verdict |
| --- | --- |
| **P-1** | **PO DECISION REQUIRED** — "is any production performance target to be committed for these operations, and if so with what values?" |
| **P-2** | **PO DECISION REQUIRED** — "should coverage grant/withdrawal notify anyone, and if so which transitions, which recipients, which channels?" |

No third decision is required. Every other element previously flagged as
"pending a PO" is either already answered by existing ratified architecture
(recipient derivation, idempotency, delivery, retry, audit) or is an
implementation detail.

---

## 6. Recommended verification target (for CoStrict / OHD)

After the PO answers P-1 and P-2, an independent verifier should confirm
**exactly** the following — and nothing more.

### If P-1 = "no SLO required"
1. That no production SLO was asserted, implied or fabricated in the final
   report or in `tools/demo_lab/perf_mp_baseline.py` (its docstring must still
   carry the *"NOT a production … SLO"* disclaimer).
2. That `tools/demo_lab/perf_mp_baseline.py` still runs green on a correctly
   restarted local stack, and that the recorded p50/p95 match the declared
   `BUDGETS` (`perf_mp_baseline.py:48–56`).

### If P-1 = "SLO supplied"
3. That the statistic / window / endpoint scope in the code equals the PO's
   stated values, with **no** silent substitution, and that the X7 observability
   threshold (`SLOW_THRESHOLD_MS`) was **not** redefined.
4. That local measurement is **labelled** as non-production wherever reported.

### If P-2 = "no notification required"
5. `grep -rn 'notifications\|create_idempotent\|Notification' backend/api/manual_processing_admin.py backend/api/manual_processing_auth.py backend/data/manual_processing.py backend/domain/manual_processing.py` → **no matches** (audit-only preserved).
6. `pytest backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py -k NV10` → **PASS**, still asserting: an audit action is written for allocate/release/admin-allocate **and** the notification row count is unchanged, and no response body claims a notification.
7. That a real `public.notifications` row is **not** created by an allocate/release against the live stack.

### If P-2 = "notification required"
8. The implemented **recipient matrix** equals what the PO stated, resolved
   server-side only, with no request-supplied recipient (mirroring the D40 §7
   *"verified 405"* check that no client notification-creation endpoint exists).
9. Replay safety: a repeated allocate/release creates **no** second notification
   (`uq_notifications_event_key`), proven with an event-key test in the style of
   `test_p6_2e_consultant_lifecycle.py`.
10. Failure harmlessness: with a **failing** email sender the allocate/release
    still returns 200 and the failure is recorded honestly
    (`notification_delivery.status='failed'` + `error_message`) — the X2 precedent.
11. No cross-tenant leakage: a notification is never delivered to a client,
    consultant or PE outside the authorised relationship (negative test, in the
    style of the Phase-6 deny matrix).
12. That audit records are still written **in addition to** the notification
    (a notification must never replace provenance).

### In both cases
13. Re-run the CT-MP-SUB-004 targeted backend suite and the frontend MP suite;
    re-confirm the F-9 invariant (**0** duplicate active `(firm, org)` pairs) and
    the fixture baseline (**1** active allocation) on the live local DB.
14. Confirm the disclosed self-found regression in
    `CT-MP-SUB-004-PROD-READINESS-01-report.md` §17
    (`OrganizationsRepository.list_all` clobbered by the `get_many` edit, then
    restored) is genuinely repaired: read `backend/data/organizations.py` and
    confirm **both** `list_all` and `get_many` exist and are correct.

---

## 7. Evidence index (commands + observed results)

| # | Command (read-only) | Observed result |
| --- | --- | --- |
| 1 | `grep -rniE '\bSLO\b\|p95\|p99\|throughput\|load test\|latency target' docs/architecture/*.md` | only the statements in §2.2 (no ratified SLO values) |
| 2 | `grep -rn 'sla_definitions\|sla_compliance' supabase/migrations/*.sql` | DDL at `00000000000000_init_schema.sql:1974,1988`; no data-creation migration |
| 3 | `grep -rn 'SLOW_THRESHOLD_MS\|WINDOW_SECONDS\|FLUSH_INTERVAL_SECONDS' backend/domain/api_metrics.py` | `1000` / `3600` / `300` (X7-D6 / D5 / D2) |
| 4 | `grep -rn 'sla_hours\|sla_breach\|is_configured' backend/data/queue_settings.py` | `sla_hours` default `48`; `is_configured()` present |
| 5 | `ls -la ~/ct_local_env/demo_lab/evidence/ \| grep -i 'mp_\|perf'` | `mp_perf_baseline_20261005T020040Z.json` + `mp_perf_baseline_latest.json` present (also `mp_nv_ui_latest.json`, `mp_fixture_browser_latest.json`) |
| 6 | `grep -n 'notifications\|create_idempotent' backend/api/*.py` | producers/consumers listed in §3.2–3.3 |
| 7 | `grep -rn 'notifications\|create_idempotent\|Notification'` over the four MP files | **no matches** (§3.8) |
| 8 | `grep -rn 'manual_processing:' backend/ --include='*.py'` | the 8 MP audit actions, incl. `allocation_created` / `allocation_released` at the 4 allocation call sites |
| 9 | `grep -n 'event_key\|actor_domain' supabase/migrations/20260902050000_phase5_notification_event_key.sql` | `ADD COLUMN IF NOT EXISTS` + `uq_notifications_event_key` |
| 10 | `grep -niE 'notif\|email\|performance\|latency\|audit' docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | **no matches** — the D2 spec is silent |
| 11 | `grep -niE 'notif\|email\|performance\|latency\|SLO' docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` | **no matches** (only *"client slots available/used"*) |
| 12 | `git rev-parse HEAD` / `git branch --show-current` | `375a48dc1b9e9cfd74090bbf747554ae997acb59` / `p8-release-reconciled` |
| 13 | `git status --porcelain` | the pre-existing CT-MP-SUB-004 + FINAL-03 worktree changes only; **no change made by this task** |
| 14 | `git remote -v` / `test -f supabase/.temp/project-ref` | `github → …/CarbonTally.git`, `origin → /tmp/ct_step2` (local); **no project-ref file** |

---

## 8. Production-safety verification (explicit)

| Safety requirement | Result |
| --- | --- |
| No production database accessed | **✅ Confirmed.** Every database fact cited comes from repository DDL/migrations, from the **local** Demo Lab stack, or from previously recorded evidence artefacts under `~/ct_local_env/demo_lab/evidence/`. No production connection was opened by this task. |
| No production credentials used | **✅ Confirmed.** No credential file, token or secret was read or printed. Local lab credentials live outside the repository (`STATE_DIR` = `~/ct_local_env/demo_lab`) and were untouched. |
| No production migration applied | **✅ Confirmed.** No migration was created, edited or applied. |
| No production deployment | **✅ Confirmed.** Nothing was deployed; no deploy command was run. |
| No Supabase production link | **✅ Confirmed.** `supabase/.temp/project-ref` is **absent**; `supabase/config.toml` carries only the local `project_id = "carbon_ledger"`. Remotes are a GitHub URL and a local path; **nothing was fetched from or pushed to either**. |
| No commit | **✅ Confirmed.** Nothing was staged or committed. HEAD is unchanged at `375a48d`. |
| No push | **✅ Confirmed.** No push, no force-push, no history rewrite. |
| No application / schema / test change | **✅ Confirmed.** The **only** file created by this task is this report. No `.py`, `.jsx`, `.sql`, config, migration or test file was modified. |
| Demo Lab persistent fixture untouched | **✅ Confirmed.** No fixture apply/reset was run; no row was inserted, updated or deleted. |
| Local environment | **Left as found** (no restart and no state change performed by this task). |
| Secrets in this report | **None.** No token, key, connection string, signed URL or credential appears above. |

---

## 9. Final status

> # FACT-FINDING COMPLETE — READY FOR PO DECISIONS

> **Superseded for P-1/P-2 (2026-10-05).** The two decisions this report was
> preparing have now been made by the Product Owner and are **CLOSED**:
> **P-1 CLOSED** (no dedicated production SLO required for this release) and
> **P-2 CLOSED** (proactive MP notifications not required; allocation/release
> remain audit-only). Authoritative record:
> `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md`.
> The factual findings below are **unchanged**; the statements that P-1/P-2
> *"remain a PO decision"* record the position **at the time of this
> fact-finding** and are preserved as the historical record.

**What this task established**

1. **P-1:** **NO EXISTING AUTHORITATIVE PRODUCTION SLO FOUND.** CarbonTally has
   no ratified production latency / throughput / availability SLO, and five
   authoritative artefacts record that absence deliberately. The only ratified
   latency number is the X7 **observability** threshold (`1000 ms`, p95 over a
   rolling 60 min). CT-MP-SUB-004's NV-9 work is a **feature-local, explicitly
   non-production** baseline that passes. **P-1 remains a PO decision.**
2. **P-2:** CarbonTally **already has** an authoritative, PO-ratified, durable
   notification architecture (**D40 + D11 + X2**) with idempotency, server-side
   recipient derivation, in-product + email delivery, recorded failures and a
   bounded retry policy — **none of which needs redesign**. The Manual
   Processing surface emits **audit records only**; **no notification producer
   exists** for allocation/release, and the D2 UI/UX spec never required one.
   **P-2 remains a PO decision** about *whether* to notify.
3. **NV-10 assessment:** *not satisfied* = the absence of any MP notification
   producer and recipient matrix (a behaviour, not a defect); *already
   satisfied* = the entire architecture such an event would reuse, plus the
   audit-only behaviour that is now documented and tested; *not required* = a
   new provider, a new outbox/event framework, default notify-on-every-change,
   or per-event preference models.

**What this task explicitly does NOT claim**

* ❌ Not PO acceptance of P-1 or P-2 (both are stated as questions, unanswered).
* ❌ Not production readiness, deployment readiness or release approval.
* ❌ Not independent verification (this is a self-authored fact-finding report).
* ❌ Not an SLO, a notification design, or any new architecture.

**Next step (owner: PO).** Answer the two questions in §5. If either answer is
"no", that item closes with **no code change**. If either answer is "yes", the
supplied values go back to implementation as a bounded change against the
**existing** D11/D40/X2 precedent, followed by the §6 verification target.














