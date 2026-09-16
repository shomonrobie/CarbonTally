---
Document Type: Phase 8-X Discovery & Implementation-Boundary Analysis (DISCOVERY ONLY)
Project: CarbonTally
Prompt ID: CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002
Status: DISCOVERY COMPLETE — NO IMPLEMENTATION
Created: 2026-09-12
Companion report: `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md`
---

# CarbonTally — Phase 8-X Operational Intelligence: Discovery & Implementation Boundary

> **Discovery only.** Nothing in this document is authorized for implementation.
> It defines a proposed boundary for PO review. No code, schema, migration, RLS,
> grant, function, configuration or production change was made.

---

## 1. Executive Summary

**Phase 8-X — Operational Intelligence** is the bounded extension of Phase 8
that organises operational *visibility* around the CarbonTally platform. It is
**not** a new Phase 9, and it does **not** replace or redefine the Phase 8
product roadmap.

**The single most important finding is that Phase 8-X is overwhelmingly a
*consolidation, exposure and correctness* workstream — not a greenfield build.**

Repository evidence shows CarbonTally already persists most of the operational
signal a platform of this kind needs:

| Operational signal | Already persisted? | Where |
|---|---|---|
| Durable job state (stage, attempts, last error, locks) | **YES** | `document_processing_queue` (79 columns) |
| Durable domain events with `correlation_id` | **YES** | `domain_events` |
| Append-only audit trail (Phase 7 taxonomy) | **YES** | `audit_trail` + `infra/audit_logger.py` |
| Usage / allowance counters | **YES** | `usage_tracking`, `billing_*` |
| AI usage + cost + model + latency | **YES** (scattered across 3 tables) | `ai_content_history`, `document_processing_queue.ai_*`, `report_generation_queue.ai_*` |
| Report generation progress + `error_log` | **YES** | `report_generation_queue` |
| Import batch results + `errors` | **YES** | `import_batches` |
| Email/notification delivery state | **YES** | `notification_delivery`, `email_logs` |
| Auth outcomes + failure reason | **YES** | `login_history` |
| SLA definitions + compliance | **YES** | `sla_definitions`, `sla_compliance` |
| Staff/queue workload + performance | **YES** | `staff_workload`, `staff_performance`, `team_performance` |
| Retention configuration + enforcement | **YES** | `system_settings` + `services/retention.py` |
| Staff operations API | **YES** (49 endpoints) | `backend/api/v3_operations.py` |
| Internal operations UI | **YES** | `frontend/src/v3/ops/**` (26 files) |

What is **missing** is not the data. It is:

1. **aggregation** — the signal is fragmented across ~24 operational tables with
   no single read model;
2. **runtime/health correctness** — the health surface does not test the real
   data path (§11);
3. **worker liveness** — the worker has no status surface at all;
4. **alerting** — threshold *configuration* exists (`system_settings`), but no
   threshold evaluation or dispatch exists;
5. **deployment/runtime introspection** — no version/build endpoint, and the
   Render deployment is not reproducible from the repository;
6. **any third-party observability tooling** — **none exists anywhere**
   (verified: no Sentry/Prometheus/OpenTelemetry/Datadog in
   `backend/requirements.txt`, `frontend/package.json`, or `backend/main.py`).

**Consequently the recommended Phase 8-X shape is:** reuse the existing tables,
the existing `/api/v3/ops/*` authorization chain, the existing ops frontend, the
existing notification and audit mechanisms, and the existing retention service —
and add a thin **read-only aggregation layer** plus three small correctness
fixes. New frameworks, new stores and new dashboards should be explicitly
out of scope.

**Two discrepancies require PO attention** (§19): the master roadmap names
Phase 8 as "Advanced Analytics" with **scope NOT defined**, conflicting with the
8-capability Phase 8 list stated in this task; and the recent runtime incident
does **not** match its reported symptom (§11).

---

## 2. Phase 8-X Definition

**Phase 8-X — Operational Intelligence** is a **bounded extension/workstream of
Phase 8**. It provides authorized operational visibility into the CarbonTally
platform and its runtime, without becoming:

* a replacement for the carbon/calculation/factor domain;
* a customer-facing analytics product (that is Phase 8);
* a replacement for Phase 7 audit/evidence architecture;
* a replacement for CarbonTally Insight;
* a second audit system;
* a generic SIEM or enterprise monitoring platform.

**Two-part structure (analysed separately in §4 and §5):**

* **A. Platform Operational Intelligence** — application/business-platform
  operational state (organizations, users, consultants, PE, processing,
  calculation, evidence/QC readiness, failures, AI usage, plans/allowances,
  billing/usage, operational audit/security, administrative visibility).
* **B. System Runtime / Infrastructure Operational Intelligence** — API/runtime
  health, worker health, crash/stall detection, dependency failures, DB
  connectivity, deployment diagnostics, runtime configuration, availability,
  SLOs, backup/restore visibility, incidents, alerting, recovery, provider
  visibility.

**Ratified project-sequencing context:** Phase 8 remains the active product
roadmap; Phase 8-X follows it; the RLS security gate is separate (§18).

---

## 3. Existing Capability Inventory

Evidence is taken from current code, migrations, database definitions and
documentation. Each row cites the artefact that establishes it.

### 3.1 Backend operational surfaces

| Capability | Implementation | Evidence |
|---|---|---|
| Health — legacy root | static `status:"healthy"`, `routes_count` | `backend/main.py:289-300` |
| Health — legacy `/health` | **PostgREST** probe of `glossary`; `healthy`/`degraded` | `backend/main.py:302-320` |
| Health — V3 | `HealthResponse` at `/api/v2/health` | `backend/api/router.py:77-78` |
| Health — Realtime readiness | websocket probe of `/realtime/v1`; `up`/`down`/`degraded`/`unconfigured` | `backend/api/v3_health.py:20-160` |
| Staff operations API | `/api/v3/ops/*` — **49 endpoints** (me, dashboard, organizations, staff, entities, entity dashboard, operator queues, item workspaces, extraction, review, QC) | `backend/api/v3_operations.py:79` |
| Admin APIs | `/api/v2/admin/audit` (4), `/api/v2/admin/providers` (2), `/api/v2/admin/aliases`, `/api/v2/admin/imports` | `backend/api/admin_*.py` |
| Billing/usage API | `/api/v3/billing` (10 endpoints) | `backend/api/v3_billing.py:26` |
| Commercial API | `/api/v3/commercial` (billing config, org list, usage output) | `backend/api/v3_commercial.py:41,446,795` |
| Settings/retention API | `/api/v3/settings/retention` | `backend/services/retention.py` docstring |
| Request correlation + error envelope | `RequestContextMiddleware`, `request_id` in V3 error envelope | `backend/api/middleware.py`, `api/router.py` |
| Error taxonomy | `CarbonTallyError` + handler | `backend/main.py:263`, `core/exceptions.py:13` |
| Rate limiting | middleware | `backend/middleware/rate_limit.py`; `system_settings.api_rate_limit` |
| Durable worker | in-process asyncio; claims `document_processing_queue` via `FOR UPDATE SKIP LOCKED`; poll 1.0 s / batch 3; stale lock 300 s | `backend/workers/automatic_processing.py:1-66,88-110` |
| Event bus (in-process) | fire-and-forget pub/sub; handlers persist to `domain_events` | `backend/infra/event_bus.py:1-14` |
| Audit logger | decorator-based; writes to `AuditRepository` → `audit_trail`; never breaks the wrapped op | `backend/infra/audit_logger.py:1-20` |
| Retention enforcement (N3) | server-side, dry-run default, soft-delete only, **audit/evidence excluded** | `backend/services/retention.py:1-30` |
| Backup export capability | encrypted, checksummed logical export | `backend/backup/{service,exporter,crypto,catalog,storage,artifact,settings}.py` |
| AI runtime | provider config + deterministic fallback when unconfigured | `backend/infra/ai_runtime.py`, `infra/llm_client.py`; worker `_build_service` fallback |
| Email | Resend-backed; **no-op stub when `RESEND_API_KEY` unset** | `backend/services/v3_email.py` |

### 3.2 Operational database assets

Representative operational tables (verified via local catalog; production holds
104 of the repository's 116 tables — see the separate RLS baseline):

| Domain | Tables |
|---|---|
| Job/queue | `document_processing_queue` (79 cols), `processing_queue` (20), `processing_logs` (12), `processing_audit_trail` (11), `processing_assignments`, `processing_steps`, `processing_time_log` |
| Events | `domain_events` (event_type, occurred_at, **correlation_id**, aggregate_id/type, payload) |
| Audit/activity | `audit_trail` (13), `audit_logs` (17), `activity_logs` (12), `activity_feed` (7) + 6 domain `*_activity_log` tables |
| Usage/billing | `usage_tracking` (11), `billing_*` (7 — **not in production**), `customer_subscriptions`, `consultant_billing` |
| AI | `ai_content_history` (16: tokens_used, cost, model_used, processing_time_ms) |
| Reports | `report_generation_queue` (28: status, progress_percentage, current_step, error_log, ai_cost), `report_versions`, `report_templates` |
| Imports | `import_batches` (17: rows_total/imported/skipped/duplicate, errors, status, rolled_back_from) |
| Notifications/email | `notifications` (17: event_key, actor_domain), `notification_delivery` (11: channel, status, sent/delivered/opened, error_message), `email_logs` (8) |
| Auth | `login_history` (10: is_successful, failure_reason, session_id) |
| SLA | `sla_definitions`, `sla_compliance`; `processing_queue.sla_breached` |
| QC | `qc_checks`, `qc_checklists`, `qc_errors`, `manual_review_queue` |
| Staff/ops | `staff_profiles`, `staff_roles` (permissions jsonb), `staff_workload`, `staff_performance`, `team_performance`, `staff_daily_performance`, `work_item_assignments` |
| Config | `system_settings` (60 cols), `queue_settings` |
| Metrics | `dashboard_metrics` |

### 3.3 Frontend operational surfaces

| Surface | Files |
|---|---|
| Operations console | `frontend/src/v3/ops/OperationsPage.jsx` + 25 siblings incl. `OpsDashboard.jsx`, `AuditConsoleTab.jsx`, `SlaTab.jsx`, `CommercialTab.jsx`, `CtQcTab.jsx`, `IssuesTriageTab.jsx`, `ProcessingEntitiesTab.jsx`, `SettingsTab.jsx`, `StaffRoster.jsx`, `StaffRolesTab.jsx`, `ReviewQueue.jsx`, `OperatorQueue.jsx`, `QcQueue.jsx`, `WorkItemWorkspace.jsx` |
| Routes | `/ops`, `/ops/items/:itemId`, `/ops/review/:itemId`, `/ops/qc/:itemId` (`frontend/src/App.js:2178-2205`) |
| Org administration | `frontend/src/v3/admin/AdminPage.jsx` — **customer organisation administration**, not an internal control plane |
| Customer dashboard | `frontend/src/v3/customer/DashboardPage.jsx` |

### 3.4 Operational documentation and tooling

| Artefact | Role |
|---|---|
| `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md` | 22-section operator reference (inventory, startup, health, env vars, logging, worker, DB safety, triage, backup status, incident escalation, "never do this") |
| `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` | Records Render configuration as **NOT VERIFIED / NO SAFE ACCESS** |
| `qa_harness/`, `independent_audit/`, `saas-assurance/` | Existing read-only verification tooling incl. a DB collector already emitting an `db_rls` packet |

---

## 4. Platform Operational Intelligence Assessment

Legend: **EX** production-ready · **EP** partial · **EN** existing/not operationalized · **MI** missing · **UN** unknown.

| # | Capability | Class | Current implementation | Tables / modules | UI | Authz | Auditability | Data source | Limitations | Next step |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Organization operational state (counts, activity, health per org) | **EP** | `/api/v3/ops/organizations` + org dashboard | `organizations`, `organization_metadata`, `emissions_logs` | OpsDashboard, ProcessingEntitiesTab | `require_staff()` | via `audit_trail` | pool | No cross-org operational aggregate view | Extend ops dashboard |
| A2 | User/identity operations | **EP** | staff/admin endpoints; `users` reads | `users`, `login_history`, `user_invitations` | StaffRoster | staff chain | partial | pool | Auth failures captured but never aggregated or surfaced | Auth-ops view (SHOULD) |
| A3 | Consultant operations | **EN** | consultant lifecycle notifications; `/api/v3/consultants` | `consultant_clients`, `consultant_firm_members`, `consultant_profiles` | consultant workspace | grant-scoped | `notifications` | pool | No operational consultant-portfolio health view | LATER |
| A4 | PE / entity operations | **EX** | `/api/v3/pe/*`, entity dashboards, entity-scoped authz | `processing_entities`, `processing_*`, `work_item_assignments` | PEManagerDashboard, ProcessingEntitiesTab | entity-scoped `require_staff()` | `processing_audit_trail` | pool | — | Extend |
| A5 | Processing/job operational state | **EP** | durable queue + worker; `/api/v3/ops/queues/operator`, `/items/*` | `document_processing_queue` (stage, attempt_count, max_attempts, last_error, locked_at, lock_token, workflow_error_count, workflow_next_retry_at, per-stage timestamps) | OperatorQueue, ReviewQueue, QcQueue | staff + per-item re-auth | `processing_audit_trail`, `domain_events` | pool | **No backlog/stuck/retry-exhaustion view; worker itself invisible** | **MUST** (§13 M1) |
| A6 | Calculation operations | **EP** | `calculation_snapshots`, `emissions_logs`; engine in worker | `calculation_snapshots`, `document_processing_queue.calculated_at` | Workspace pages | staff | snapshot provenance | pool | No calculation-job health/duration/retry view | MUST (within M1/M3) |
| A7 | Evidence / QC readiness | **EP** | `/api/v3/qc/*`, issues triage, `customer_approved`/`qc_approved` flags | `qc_*`, `issues`, `manual_review_queue`, `file_attachments` | CtQcTab, IssuesTriageTab, ReviewQueue | staff | `review_audit_trail` | pool | No readiness roll-up | SHOULD |
| A8 | Failure visibility | **EP** | scattered error columns | `document_processing_queue.last_error`, `report_generation_queue.error_log`, `import_batches.errors`, `email_logs.error_message`, `notification_delivery.error_message`, `processing_logs.error` | none aggregated | — | — | pool | **No unified failure store or view** | **MUST** (§13 M3) |
| A9 | AI usage / cost | **EP** | AI runtime + scattered cost fields | `ai_content_history` (tokens_used, cost, model_used), `document_processing_queue.ai_*`, `report_generation_queue.ai_*` | none | — | — | pool | **Three sources, no single AI ops view; no provider-health signal** | SHOULD (§13 S3) |
| A10 | Plans / allowances | **EN** | billing service + config tables | `billing_plans`, `billing_commercial_config`, `usage_tracking` | CommercialTab | `_require_billing_admin` | via audit | pool | 7 billing tables **absent from production** | SHOULD (blocked, §14) |
| A11 | Billing / usage operations | **EP** | `/api/v3/billing` (10), `/api/v3/commercial`, `usage_tracking` | `usage_tracking`, `billing_*`, `customer_subscriptions`, `consultant_billing` | CommercialTab | billing admin | via audit | pool | No usage/allowance anomaly or overage view | SHOULD |
| A12 | Operational audit/security info | **EP** | `audit_trail` + `/api/v2/admin/audit` (4) | `audit_trail`, `audit_logs`, `login_history` | AuditConsoleTab | `require_internal_staff()` | append-only | pool | Security-relevant runtime events not surfaced | SHOULD |
| A13 | Customer/workspace operational state | **EP** | per-org endpoints | `organizations`, `upload_batches`, `customer_documents` | customer DashboardPage | org-scoped | via audit | pool | No operator view of "customer is blocked on X" | SHOULD |
| A14 | Administrative operational visibility | **EP** | admin APIs + SettingsTab | `system_settings`, `queue_settings` | SettingsTab | `require_internal_staff()` | via audit | pool | **No internal admin control plane** (AGENTS.md §31 expects `/admin`) | SHOULD/LATER |
| A15 | SLA operations | **EX** | definitions + compliance + settings flags | `sla_definitions`, `sla_compliance`, `system_settings.sla_breach_alert_enabled/_recipients` | SlaTab | staff | via audit | pool | Alert flags **configured but not evaluated** | SHOULD (§13 S1) |
| A16 | Staff/queue performance | **EX** | precomputed + live tables | `staff_workload`, `staff_performance`, `team_performance`, `staff_daily_performance` | StaffRoster, OpsDashboard | staff | — | pool | Duplication (§10) | Consolidate |
| A17 | Import operations | **EP** | batch results + admin imports | `import_batches` (rows_*, errors, status, rolled_back_from) | none | `/api/v2/admin/imports` | via audit | pool | No import-ops view | SHOULD (§13 S5) |
| A18 | Notification/email operations | **EP** | delivery state + logs | `notification_delivery`, `email_logs`, `notifications` | NotificationsPage | user-scoped | — | pool | No delivery-ops view; provider (Resend) status unknown | SHOULD (§13 S4) |
| A19 | Cross-domain operational summaries | **MI** | — | — | — | — | — | — | **Does not exist** | MUST (aggregation) |

---

## 5. System Runtime / Infrastructure Operational Intelligence Assessment

Ownership legend: **[APP]** application-owned · **[PROV]** infrastructure/provider-owned ·
**[EXT]** requires external monitoring · **[ABS]** absent.

| # | Capability | Owner | Class | Current implementation | Evidence | Limitations | Next step |
|---|---|---|---|---|---|---|---|
| B1 | API runtime health | **[APP]** | **EP** | `/`, `/health`, `/api/v2/health`, `/api/v3/health/realtime` | `main.py:289-320`, `api/router.py:77`, `api/v3_health.py` | **`/health` probes PostgREST only, not the pool data path** (§11) | **MUST** fix (§13 M2) |
| B2 | Worker health / liveness | **[APP]** | **MI** | none — worker has no status surface | `workers/automatic_processing.py` (no health method) | Worker failure is **log-only** | **MUST** (§13 M2) |
| B3 | Worker crash detection | **[APP]** | **MI** | none | — | A crashed task is invisible; only log lines | MUST |
| B4 | Worker stall detection | **[APP]** | **EP** | stale-lock reclaim after 300 s (`stale_lock_seconds`); `locked_at`/`lock_token` | `automatic_processing.py:42,103` | Mechanism exists in the DB model but has **no visibility** | MUST |
| B5 | Database connectivity | **[APP]** | **EP** | `/health` → PostgREST `glossary` probe | `main.py:302-314` | **Does not verify the asyncpg pool path** used by all repositories | MUST |
| B6 | Supabase API/Realtime reachability | **[APP]** | **EX** | `/api/v3/health/realtime` (`up`/`down`/`degraded`/`unconfigured`) | `api/v3_health.py` | REST/auth reachability not separately reported | SHOULD |
| B7 | External dependency health (Resend, AI provider) | **[APP]** | **EN** | Resend: no-op stub when unset; AI: deterministic fallback | `services/v3_email.py`, `infra/ai_runtime.py` | Failure is silent-by-design; **no proactive provider status** | SHOULD |
| B8 | Deployment diagnostics | **[APP]**/**[PROV]** | **MI** | none in app; Render config **not in repository** | `CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` §2-4 | No `render.yaml`/`Procfile`/`Dockerfile`; build/start/health path **UNVERIFIED**; no version/build endpoint | **MUST** (§13 M5) |
| B9 | Runtime configuration diagnostics | **[APP]** | **EN** | `config.py`; env documented in ops quick reference §7 | `backend/config.py`, ops doc §7 | **No startup validation / self-check**; a missing `DATABASE_URL` is not detected at boot (§11) | **MUST** (§13 M5) |
| B10 | Availability | **[PROV]** | **[ABS]** | none | — | No measurement, no definition | LATER |
| B11 | SLOs / operational metrics | **[APP]**+**[EXT]** | **MI** | none | verified: no metrics code, no APM dependency | No latency/volume/error-rate capture anywhere | SHOULD (§13 S2) |
| B12 | Backups — status visibility | **[APP]**/**[PROV]** | **MI** | export capability exists; **no scheduled backups, no storage backup, no restore, no RTO/RPO, no drill** | `backend/backup/**`; ops doc §18; `CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md` | Supabase plan-level backup status not visible from repo | LATER (own roadmap) |
| B13 | Restore capability / visibility | **[PROV]**+**[APP]** | **[ABS]** | restore **not implemented** | ops doc §18 | — | LATER |
| B14 | Incidents | **[APP]** | **MI** | none; **manual** role-based escalation only | ops doc §19 | No incident record, state or history | LATER (§13 L1) |
| B15 | Alerting | **[APP]** | **EN** | config keys exist: `sla_breach_alert_enabled`, `sla_breach_alert_recipients`; notification delivery exists | `system_settings`, `notification_delivery`, `services/work_items.py:_notify_assignee` | **No evaluation or dispatch engine**; keys are inert for alerting | SHOULD (§13 S1) |
| B16 | Service recovery / operational readiness | **[APP]**/**[PROV]** | **EP** | worker restart resumes in-flight jobs (durable DB state); platform-level restart is provider-owned | worker docstring; v3m9 migration | Recovery behaviour undocumented in runbooks | SHOULD |
| B17 | Provider-level monitoring (Render/Supabase/Vercel) | **[PROV]** | **UN** | not verified from repository; **no provider access** | Render record §1, §4 | Platform log retention/export **UNVERIFIED**; no alert routes configured in code | PO decision (§19 PX-4) |
| B18 | External monitoring integration | **[EXT]** | **[ABS]** | none | verified: no Sentry/OTel/Prometheus/Datadog in dependencies or code | — | LATER |
| B19 | Runtime/provider visibility of Supabase production | **[PROV]** | **UN** | RLS baseline established 21/55 migrations applied | separate RLS baseline report | Production catalog is now readable read-only via the linked CLI | Reuse for drift detection |

**Discipline note:** items B10, B12, B13, B17, B19 are marked provider-owned or
external because the repository contains **no evidence** that CarbonTally
implements them. They are **not** claimed as implemented merely because a
provider may offer them.

---

## 6. Capability-Gap Matrix (consolidated)

| Gap | Evidence | Class |
|---|---|---|
| G1 No unified failure store/view across processing, report, import, email, notification | error columns in 6 tables; no aggregate surface | **MISSING** |
| G2 Worker has no liveness/health/backlog surface | `workers/automatic_processing.py` exposes only `start`/`stop` | **MISSING** |
| G3 `/health` does not test the pool data path | `main.py:302-320` uses `get_supabase_client()` | **DEFECT** |
| G4 No startup configuration validation | `main.py:268-287` starts the worker without validating env | **DEFECT** |
| G5 No version/build/runtime introspection endpoint | no such route; no build metadata in app | **MISSING** |
| G6 Deployment not reproducible from repository | no `render.yaml`/`Procfile`/`Dockerfile` | **MISSING (process)** |
| G7 No alert evaluation/dispatch despite config keys | `system_settings.sla_breach_alert_*` inert | **PARTIAL** |
| G8 No API runtime metrics (latency, volume, error rate) | no instrumentation; no APM dependency | **MISSING** |
| G9 No incident model | manual escalation only (ops doc §19) | **MISSING** |
| G10 No availability/SLO definition | none | **MISSING** |
| G11 Operational signal fragmented across ~24 tables with overlapping semantics | §10 | **DUPLICATION** |
| G12 No internal admin control plane UI | `AdminPage.jsx` is customer org-admin; AGENTS.md §31 expects `/admin` | **PARTIAL** |
| G13 Backup/restore visibility absent in-app | ops doc §18 | **DEFERRED (own roadmap)** |
| G14 No structured/JSON logging, no log retention control | `core/logging.py` text stdio handler | **PARTIAL** |
| G15 Auth-failure and security-event aggregation absent | `login_history` exists, never surfaced | **PARTIAL** |
| G16 No operational-brain read-only role for production verification | RLS baseline decision D-10 | **MISSING (dependency)** |

---

## 7. Operational Data-Model Assessment

Assessed for suitability as an operational-intelligence source. **No schema
change was made; any change below is a PROPOSAL ONLY.**

### 7.1 Strong sources (reuse as-is)

| Table | Strengths for ops intelligence | Limitation |
|---|---|---|
| `document_processing_queue` | 79 columns: `stage`, `attempt_count`, `max_attempts`, `last_error`, `locked_at`, `lock_token`, `workflow_error_count`, `workflow_next_retry_at`, `reprocess_count`, per-stage timestamps (`ingested_at`…`calculated_at`, `review_ready_at`), `pipeline_version`, AI fields, `calculation_snapshot_id`, org + batch linkage | Single very wide table; no separation between operational and business columns |
| `domain_events` | Durable event stream with `event_type`, `occurred_at`, **`correlation_id`**, `aggregate_id/type`, `payload` | RLS enabled with **0 policies** → service-only; no documented retention; no documented consumer/index strategy |
| `audit_trail` | Append-only, Phase 7 taxonomy, `performed_by`, old/new/changes | Audit ≠ runtime telemetry; must not be repurposed (§below) |
| `report_generation_queue` | `status`, `progress_percentage`, `current_step`, `error_log`, `ai_cost`, `ai_tokens_used` | Not present in production until Phase 8 report migrations apply |
| `import_batches` | `rows_total/imported/skipped/duplicate`, `errors`, `status`, `rolled_back_from` | No per-row failure detail |
| `notification_delivery` | `channel`, `status`, `sent_at`/`delivered_at`/`opened_at`, `error_message` | Provider-side (Resend) delivery detail limited |
| `login_history` | `is_successful`, `failure_reason`, `session_id` | Staff-scoped only (`staff_id`) |
| `usage_tracking` | Per-org per-day/month counters (AI files, batch uploads, manual pages, reports, storage bytes) | Overlaps `billing_storage_usage` |
| `staff_workload` / `staff_performance` / `team_performance` | Live + precomputed workload/throughput/QC pass rate | Three overlapping grains (§10) |
| `system_settings` | Retention, SLA alert flags, limits, backup frequency — the config source of truth | 60 columns; no schema-versioned config history |

### 7.2 Timestamps and correlation

* Per-stage timestamps already exist on the job row → **duration and stage-latency
  analysis is possible without schema change**.
* `domain_events.correlation_id` provides cross-domain correlation → **reuse for
  traceability** rather than inventing a new correlation scheme.
* `audit_logger` entries carry actor + before/after state.

### 7.3 Retention

* Retention **configuration** exists in `system_settings`
  (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`,
  `backup_retention_days`) and is enforced server-side by
  `services/retention.py` (dry-run default, soft-delete only, **audit/evidence
  explicitly excluded**).
* **No retention is defined for operational telemetry** (`domain_events`, worker
  logs, delivery records) — a Phase 8-X discovery item (§19 PX-7).

### 7.4 PROPOSAL ONLY — candidate schema additions (not authorized)

| Proposal | Rationale | Notes |
|---|---|---|
| Worker heartbeat (row in `system_settings`-style key/value, or a tiny table) | Worker liveness/stall detection with no new framework | Prefer a single-row heartbeat over a new table |
| Read-model **view** for unified failures (e.g. a `VIEW` over existing error columns) | Satisfies G1 with **no new table** | A view is not a data-duplication risk |
| Incident table + states (`detected`→`investigating`→`mitigating`→`resolved`→`closed`) | G9 | Defer; LATER (§13 L1) |
| Operational metric rollups | G8 | Only if in-process sampling proves insufficient |

**Every one of these requires a separate, authorized schema change. None is
implemented. Any new table would also require RLS policy design at creation
time** (§18).

---

## 8. Authorization and Tenancy Assessment

### 8.1 Existing authorization model (reuse)

`backend/api/operations_auth.py` documents the authoritative chain:

```text
authenticated user
  → staff_profiles (active)
  → permissions (staff_roles.permissions jsonb via staff_profiles.role_id)
  → scope: staff_profiles.entity_id
        NULL      = CarbonTally internal staff  → ops-wide surfaces
        populated = processing-entity staff     → entity-scoped surfaces only
```

* Every `/api/v3/ops/*` endpoint passes `require_staff()` or
  `require_internal_staff()` and **re-authorizes every item/batch/entity** the
  caller touches; browser-supplied ids are never trusted.
* PE staff are structurally unable to reach the manual-extraction pipeline.
* Operators (`can_process`) may only touch items in batches assigned to them.

### 8.2 Per-surface authorization assessment

| Proposed surface | Audience | Scope | Sensitive data | Backend-only? | Existing authz sufficient? |
|---|---|---|---|---|---|
| A5/M1 Job & queue operations | internal staff | global | customer-identifying | **Yes** (ops API) | **Yes** — `require_internal_staff()` |
| A8/M3 Unified failure view | internal staff | global | error text may embed customer data | **Yes** | Yes, but **error-text redaction review required** |
| A9/S3 AI usage & cost | internal + billing admin | global | prompts are customer content | **Yes** | Yes for aggregates; **content must stay out** |
| A10/A11 Usage & billing ops | billing admin | global | commercial | **Yes** | Yes — `_require_billing_admin` |
| A12 Security/audit ops | internal staff | global | security-sensitive | **Yes** | Yes — `require_internal_staff()` |
| A15 SLA ops | internal staff | global | customer-identifying | Yes | Yes |
| A17 Import ops | internal staff | global | reference data | Yes | Yes (`/api/v2/admin/imports`) |
| A18 Delivery ops | internal staff | global | **email addresses / PII** | **Yes** | Yes, but **prefer metadata over contents** |
| B1/B2/B3/B4 Runtime & worker | internal staff | global | none | **Yes** | Yes |
| B8/B9 Deployment & config | internal staff | global | **must never expose secrets** | **Yes** | New — design required |
| B11 Runtime metrics | internal staff | global | endpoint names may be sensitive | Yes | New — design required |
| Customer-visible operational state | customer | own org | own data only | Yes | Existing org-scoping |
| PE-visible operational state | entity staff | own entity | own entity only | Yes | Existing entity scoping |

**Recommendation:** all Phase 8-X runtime/infrastructure surfaces are
**internal-staff-only** (`entity_id IS NULL`). No customer-facing or
PE-facing runtime surface is proposed in the initial release.

### 8.3 New authorization design likely required

* **B8/B9 (deployment/config introspection)** — must expose *presence* of
  configuration, never values; requires a redaction contract.
* **B11 (runtime metrics)** — endpoint-level data can leak tenant activity
  patterns; requires aggregation-only design.
* **Correlation-id exposure** — if surfaced, correlation ids must not be usable
  as a cross-tenant join key.

### 8.4 Tenancy

* Operational tables are **mixed-scope**: some are org-scoped
  (`usage_tracking`, `document_processing_queue`), some are global
  (`domain_events`, `system_settings`, `staff_*`, `audit_trail`).
* Any operational read model must therefore be **explicit about scope** and must
  not become a cross-tenant aggregation surface for customer-visible consumers.
* **Operational reporting must never become a cross-tenant leakage mechanism.**

### 8.5 RLS dependency

> **DEPENDENCY — SEPARATE RLS SECURITY GATE**

For every proposed Phase 8-X capability, RLS is a dependency and **not** part of
Phase 8-X implementation:

* Existing operational tables are read through the backend, which holds
  `BYPASSRLS` (`postgres`/`service_role`) — so Phase 8-X reads work **today**
  without touching RLS.
* `domain_events` and `import_batches` have RLS **enabled with 0 policies**
  (service-only). Backend reads are unaffected; direct client reads are denied.
* **Any new table proposed in §7.4 must ship with RLS policy design at creation
  time**, per `AGENTS.md` RLS policy, and would therefore intersect the RLS
  programme.
* The verified production RLS posture (97/104 tables with RLS disabled; `anon`
  holding `GRANT ALL`) means **operational data is not currently protected at the
  database layer** — this is recorded, **not remediated here**, and preserved in
  `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md`.

**Do not implement or modify RLS in Phase 8-X.**

---

## 9. Frontend / UX Assessment

### 9.1 What already exists (extend, do not replace)

| Existing surface | Operational value | Evidence |
|---|---|---|
| `frontend/src/v3/ops/OperationsPage.jsx` + tabs | The internal operations console already exists | 26 files in `frontend/src/v3/ops/` |
| `OpsDashboard.jsx` | Staff/queue overview | 148 lines |
| `SlaTab.jsx` | SLA compliance view | — |
| `AuditConsoleTab.jsx` | Audit console | — |
| `CtQcTab.jsx`, `IssuesTriageTab.jsx` | QC + issues triage | — |
| `CommercialTab.jsx` | Billing/commercial view | — |
| `SettingsTab.jsx` | System/queue settings | — |
| `StaffRoster.jsx`, `StaffRolesTab.jsx` | Staff + workload | — |
| `OperatorQueue.jsx`, `ReviewQueue.jsx`, `QcQueue.jsx` | Queue state | — |
| `NotificationsPage.jsx` (`v3/`) | Notification surface | — |
| `components/StaffPresence.jsx`, `DashboardSummary.jsx` | Presence + summary widgets | — |

### 9.2 Assessment

* **A parallel operations dashboard must not be created.** The correct Phase 8-X
  approach is to add tabs/cards to the existing ops console.
* Existing status indicators are queue-centric. **There is no runtime/health card
  and no failure-aggregate card.**
* `AdminPage.jsx` is **customer organisation administration** (`"Organisation
  administration"`, `AdminPage.jsx:102`) — it is **not** the internal admin
  control plane that `AGENTS.md` §31 anticipates. This is a genuine gap (G12),
  not a duplicate.
* No UI changes were made. No UI redesign is proposed beyond extension.

---

## 10. Duplication / Consolidation Findings

CarbonTally has **several overlapping operational systems**. Consolidation is a
Phase 8-X objective; **no consolidation was performed.**

| # | Overlap | Evidence | Recommendation |
|---|---|---|---|
| D1 | **Audit systems**: `audit_trail` (Phase 7, append-only, authoritative) vs `audit_logs` (17 cols, legacy shape) vs `activity_logs` (12 cols) | table columns | Treat `audit_trail` as authoritative; do **not** create a third; classify `audit_logs`/`activity_logs` as legacy candidates |
| D2 | **Per-domain activity logs**: `document_activity_log`, `conversation_activity_log`, `message_activity_log`, `user_activity_log`, `staff_activity_log`, `verification_activity_log`, `review_audit_trail`, `processing_audit_trail` | table list | Domain-specific audit is legitimate; **but** operational views should aggregate rather than add more |
| D3 | **User-facing feed vs audit**: `activity_feed` (7 cols, `is_read`) vs audit tables | columns | Keep separate — feed is presentation, audit is governance |
| D4 | **Processing queues**: `document_processing_queue` (durable, 79 cols, worker-owned) vs `processing_queue` (20 cols, `sla_*`, `document_id`) | columns | `document_processing_queue` is authoritative for the automatic pipeline; `processing_queue` appears to be a legacy/parallel queue — **verify before reuse** |
| D5 | **Processing logs**: `processing_logs` vs `processing_audit_trail` vs queue error columns | columns | Prefer queue columns + `domain_events`; treat others as views over existing data |
| D6 | **Usage/billing**: `usage_tracking` vs `billing_*` (7 tables incl. `billing_storage_usage`) vs `ai_content_history` cost fields | columns | One aggregation layer; do not add a fourth counter |
| D7 | **Staff metrics**: `staff_performance`, `team_performance`, `staff_daily_performance`, `staff_workload` | columns | Four grains of the same signal; consolidate the read model |
| D8 | **Settings**: `system_settings` (60 cols) vs `queue_settings` (7 cols) | columns | Keep both if `queue_settings` is queue-scoped; document precedence |
| D9 | **Delivery**: `notifications` vs `notification_delivery` vs `email_logs` | columns | Legitimate layering (intent → delivery → provider); expose as one view |
| D10 | **Health surfaces**: `/`, `/health`, `/api/v2/health`, `/api/v3/health/realtime` | routes | Four health endpoints with different semantics; consolidate/document semantics rather than adding a fifth |
| D11 | **Metrics tables vs real metrics**: `dashboard_metrics` (stored) vs no runtime metrics | — | `dashboard_metrics` is business dashboard data, **not** runtime telemetry; do not conflate |

**Guiding principle for Phase 8-X: aggregate, do not duplicate.** Any proposed
operational surface must first be proven unable to be satisfied from existing
tables.

---

## 11. Recent Runtime Incident Assessment

**Reported symptom:** the automatic-processing worker attempted to obtain a
database pool and failed because `DATABASE_URL` / `SUPABASE_DB_URL` was not
configured; the backend subsequently shut down.

**This section is analysis only. Nothing was fixed, configured or reconfigured.**

### 11.1 Why the worker needs that configuration — VERIFIED

```text
worker._tick()
  → api.dependencies.get_repositories()        (dependencies.py:333-335)
    → get_pool() → get_service_pool()          (dependencies.py:330)
      → get_database_url()                     (infra/supabase.py:73-77)
         = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
      → if empty: raise RuntimeError(
          "DATABASE_URL is not configured; set DATABASE_URL or "
          "SUPABASE_DB_URL in the environment") (infra/supabase.py:136-137)
```

`get_service_pool()` builds the process-wide `asyncpg` pool used by **every**
repository (`backend/infra/supabase.py` module docstring). The dependency is
therefore **architectural, not worker-specific**: the entire V3 data path
requires the DSN. It is **not** a stale code path — the worker is the current,
migration-backed durable mechanism (`20260829000000_v3m9_durable_automatic_processing.sql`)
started from the app lifespan (`main.py:279-287`).

### 11.2 Is the failure actually fatal? — VERIFIED: NO

* `start()` only creates an asyncio task; it **never touches the pool**
  (`workers/automatic_processing.py:54-66`). Therefore the `try/except` at
  `main.py:286` — commented *"worker must never block startup"* — **cannot catch
  this failure**. The startup guard gives **false reassurance**.
* The pool is acquired lazily inside `_tick()`, which is wrapped by
  `_run_loop`'s `except Exception` — *"the loop must never die"*
  (`automatic_processing.py:88-97`).
* **Consequence (VERIFIED by code path):** the `RuntimeError` is **caught and
  logged every poll interval (1.0 s)**, and the loop continues. The worker does
  **not** crash the process.

### 11.3 Then why did the backend shut down? — INFERRED / UNKNOWN

The repository evidence does **not** explain a shutdown caused by the worker.
Candidate mechanisms, requiring production evidence:

1. **Platform-level shutdown** — Render restart, deploy, scale-down, OOM, or a
   health-path mismatch (Render's configured health path is **UNVERIFIED**).
2. **A different component raising** at import/startup (not the worker).
3. **The health path is a pool-backed V3 endpoint** that fails when
   `DATABASE_URL` is unset, causing the platform to mark the service unhealthy.
4. **Operator-initiated** shutdown/restart.

> **UNKNOWN / REQUIRES FURTHER INVESTIGATION** — the shutdown cause cannot be
> established from the repository. It must **not** be recorded as "the worker
> crashed the backend".

### 11.4 Health-check blind spot — VERIFIED (important)

`/health` probes Supabase through the **PostgREST client**, not the pool:

```text
supabase = get_supabase_client()
supabase.table("glossary").select("count", count="exact").limit(1).execute()
(main.py:302-314)
```

`get_service_client()` requires `SUPABASE_URL` + the service key — **not**
`DATABASE_URL`. Therefore **with `DATABASE_URL` unset, `/health` can still report
`"healthy"` while every V3 repository-backed endpoint and the worker are
completely non-functional.** This is a genuine correctness defect (G3) and a
strong Phase 8-X "MUST" item.

### 11.5 Conflict with the canonical production architecture — VERIFIED (partially)

* Canonical backend DB access = `asyncpg` pool via `DATABASE_URL`
  (`backend/infra/supabase.py`).
* The repository's production env file lists `SUPABASE_URL` and
  `SUPABASE_SERVICE_KEY` etc. but **no `DATABASE_URL` / `SUPABASE_DB_URL`**
  (recorded in `CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` §2,
  names only).
* Therefore **the repository's production configuration artefacts are
  incomplete relative to what the code requires.** Render's *actual* environment
  variables are **NOT VERIFIED** (no Render access).
* Alternative supported path: `get_service_client()` (PostgREST + service key)
  — but the repository layer is **not** implemented over it; only `/health` and
  a few legacy modules use it. There is **no drop-in alternative** for the
  repository layer.

### 11.6 Classification

**Configuration debt AND deployment debt, with an architecture dimension.**

* *Configuration*: a required secret is absent from the documented production
  env set.
* *Deployment*: the deployment is not reproducible from the repository, and
  there is no startup validation to fail fast and loudly (G4).
* *Architecture*: a single DB access strategy tied to a DSN secret, with no
  service-role-REST fallback for repositories, and no health probe on that path.

**Not** "stale code path". **Not** "code bug" in the worker.

### 11.7 Does it belong in Phase 8-X?

**Partially — and it is the clearest justification for Phase 8-X.**

| Aspect | Belongs in 8-X? |
|---|---|
| Health-path correctness (`/health` must test the pool) | **YES — MUST (M2)** |
| Startup configuration self-check (fail fast, no secrets leaked) | **YES — MUST (M5)** |
| Worker liveness/backlog visibility | **YES — MUST (M2)** |
| Deployment reproducibility (`render.yaml` etc.) | **YES — SHOULD (M5/docs)** |
| **Fixing** the missing env var / changing Render config / changing worker code | **NO — separate bounded remediation task** (§19 PX-9) |

### 11.8 What a future bounded remediation task must investigate

1. Whether `DATABASE_URL`/`SUPABASE_DB_URL` is present in Render (**requires platform access**).
2. Render's configured health-check path and restart policy.
3. Whether the shutdown correlates with a deploy/restart (platform log retention is **UNVERIFIED**).
4. Whether any other component fails at startup without the DSN.
5. Whether `RELOAD=false` is set in production (**UNVERIFIED**).
6. Whether `/health` should probe the pool, the PostgREST path, or both.
7. Whether a fail-fast startup validation should be mandatory.
8. Supabase pooler vs direct connection and connection-limit implications for `min_size=1, max_size=5`.

**Do not fix it in Phase 8-X.**

---

## 12. Proposed Operational-Intelligence Architecture

**Design principle: reuse first. No new frameworks, no new stores, no new
dashboards unless evidence proves necessity.**

```text
SOURCES OF OPERATIONAL TRUTH (existing)
  document_processing_queue   jobs: stage, attempts, last_error, locks, stage ts
  domain_events               durable events + correlation_id
  audit_trail                 append-only governance audit (Phase 7)
  usage_tracking / billing_*  usage + allowances
  ai_content_history (+2)     AI tokens, cost, model, latency
  report_generation_queue     report ops + error_log
  import_batches              import ops + errors
  notification_delivery       delivery + provider errors
  email_logs                  transactional email
  login_history               auth outcomes
  sla_compliance              SLA
  staff_workload/_performance workload
  system_settings             thresholds, retention, limits
         │
         ▼
AGGREGATION LAYER  (NEW, thin, read-only)
  backend/services/operational_intelligence.py
   - read-only projections over existing repositories
   - NO new event store, NO new queue, NO new scheduler
   - reuses RepositoryBundle (dependencies.get_repositories)
         │
         ▼
API  (EXTEND existing namespace)
  /api/v3/ops/runtime/*        health, worker, deployment, config-presence
  /api/v3/ops/operations/*     failures, backlog, queue health, SLA, usage
  guard: require_internal_staff()  + per-item re-authorization
         │
         ▼
FRONTEND  (EXTEND existing console)
  frontend/src/v3/ops/OperationsPage.jsx  → new tabs/cards
   - Runtime / Health tab
   - Failures tab
   - Worker & Queue health card on OpsDashboard
   NO second dashboard, NO new routing shell
         │
         ▼
ALERTING  (REUSE existing mechanisms)
  system_settings thresholds (sla_breach_alert_* exist)
  → notifications + notification_delivery (+ email via existing Resend path)
  → dispatched by an existing-scheduler-driven check, not a new service
         │
         ▼
AUDITABILITY  (REUSE)
  AuditLogger → audit_trail for every operational read that is sensitive
RETENTION  (REUSE)
  services/retention.py + system_settings keys (operational keys proposed)
FAILURE HANDLING  (REUSE)
  durable queue retry / stale-lock / dead-letter semantics already in the model
```

### 12.1 Design rules

* **Read-only first.** `Observe first. Act later.` No mutation of runtime state
  (retry/cancel/reprocess/replay) in the initial release.
* **No second source of truth.** Operational views **reference** authoritative
  domain records; they never duplicate emissions, factors, calculations,
  evidence or report facts.
* **Audit ≠ telemetry.** `audit_trail` stays the governance record; operational
  telemetry must not be written into it, and it must not be read as telemetry.
* **Sensitive-data minimisation.** No request payloads, tokens, secrets, message
  contents, document contents, or customer conversation content in operational
  data. Prefer metadata over contents.
* **Tenant-safe.** Global operational views are internal-staff-only.
* **No opaque health score.** Any composite score must have deterministic
  methodology, defined components, thresholds, explainability and auditability —
  never an AI-generated operational score.
* **Provider capabilities are not CarbonTally capabilities.** Items owned by
  Render/Supabase/Vercel are documented as provider-owned, and external
  monitoring is a deliberate later decision, not an assumed capability.

---

## 13. Must / Should / Later / Out-of-Scope Classification

### MUST HAVE — initial Phase 8-X release

| ID | Item | Reasoning |
|---|---|---|
| **M1** | Worker & queue operational visibility — backlog, stuck/claimed jobs, retry exhaustion, `workflow_error_count`, `last_error`, stage distribution, oldest-waiting age | Directly addresses the observed incident and the largest existing blind spot. **All data already exists** in `document_processing_queue`; no schema change required |
| **M2** | Health-path correctness + worker liveness — `/health` must exercise the pool path; expose worker heartbeat/last-tick | The verified defect (§11.4) means the current health signal can be wrong. Cannot manage a platform whose health probe does not test the real data path |
| **M3** | Unified failure visibility across processing → report → import → email/notification | Findings are fragmented across 6 tables with no aggregate surface (G1). Achievable with a read model, no new table |
| **M4** | Operations console extension (consume M1–M3 in the existing ops UI) | Reuses existing console; avoids a parallel dashboard |
| **M5** | Runtime/deployment introspection — version/build/commit, environment label, **configuration presence** (never values), startup self-check | The deployment is not reproducible and a required secret can be missing silently (§11.5). Highest-leverage low-cost fix |
| **M6** | Operational runbooks — worker/queue triage, startup failure triage, health-path triage | Ops doc §21 already lists "worker backlog/stuck-job triage procedure" as undocumented |

### SHOULD HAVE — important, not required for initial release

| ID | Item | Reasoning |
|---|---|---|
| **S1** | Threshold evaluation + alert dispatch (queue backlog, SLA breach, repeated failures, provider outage) | Config keys **already exist and are inert**; reuse `notifications`/`notification_delivery` |
| **S2** | API runtime metrics — request volume, status distribution, latency, slow/error endpoints | Requires new instrumentation; no APM exists. Valuable but larger than M-items |
| **S3** | AI runtime operations — provider health, request volume, failures, latency, tokens, cost, fallback events | Data exists in 3 places; needs aggregation, not new storage |
| **S4** | Email/notification delivery operations view | `notification_delivery` + `email_logs` already hold it |
| **S5** | Import operations view | `import_batches` already holds it |
| **S6** | Auth/authorization operations view — failure aggregation, suspicious patterns | `login_history` exists; needs surfacing + policy on what is recorded |

### LATER

| ID | Item | Reasoning |
|---|---|---|
| **L1** | Incident model + lifecycle | Real value, but requires a new table + RLS design; not required to observe runtime |
| **L2** | Availability definition + SLOs | Needs measurement (S2) first and a PO-agreed definition |
| **L3** | Backup/restore visibility | Depends on the separate backup roadmap (restore not implemented) |
| **L4** | External observability integration (Sentry-class/APM/platform alert routing) | A procurement/architecture decision; premature before in-app signal exists |
| **L5** | Operational anomaly detection | Needs stable baselines first |
| **L6** | Composite operational health score | Only with deterministic, explainable, auditable methodology |
| **L7** | Internal admin control plane (`/admin`) per AGENTS.md §31 | Larger architectural surface; distinct from operational intelligence |

### OUT OF SCOPE — explicitly outside Phase 8-X

* RLS remediation of any kind (separate security gate, §18).
* Production migration-backlog adjudication.
* Replacement of the calculation engine, factor management, report engine, or
  Phase 7 audit/evidence architecture.
* Customer-facing analytics, CarbonTally Insight product features, net-zero
  planning, disclosure intelligence (**Phase 8 product**).
* Generic ESG reporting; unrestricted SIEM; generic enterprise monitoring
  platform.
* Unrestricted customer-conversation access; cross-tenant customer analytics.
* Unrestricted AI database access; unrestricted log access.
* Automatic production remediation (self-healing actions).
* Backup/restore **implementation** (own roadmap).
* Fixing the `DATABASE_URL` configuration (§11.7).

---

## 14. Dependencies and Blockers

| ID | Item | Type | Notes |
|---|---|---|---|
| **BL-1** | **No Render/platform access** — deployment config, env vars, health path, restart policy, log retention all UNVERIFIED | **BLOCKER** (for B8/B9/B17 and for diagnosing §11) | Blocks *verification* of runtime/deployment intelligence, not the in-app work |
| **BL-2** | **No read-only production DB role** | **BLOCKER** (for production verification of operational read models) | RLS baseline decision D-10; production reads currently rely on the CLI's transient login role |
| **DEP-1** | Phase 8 report lifecycle work (S3) | **DEPENDENCY** | `report_generation_queue` operational visibility depends on Phase 8 report migrations being applied |
| **DEP-2** | RLS security gate | **DEPENDENCY — SEPARATE RLS SECURITY GATE** | Backend reads unaffected (BYPASSRLS); **new tables require RLS policy design**; production operational data is currently unprotected at the DB layer (§18) |
| **DEP-3** | Production migration drift (21/55 applied; 12 repo tables absent from production) | **DEPENDENCY** | Operational surfaces referencing Phase-8 tables (billing, `work_item_assignments`, `vehicles`) cannot be verified in production until the backlog is adjudicated |
| **DEP-4** | `DATABASE_URL` / pool configuration correctness | **DEPENDENCY** | Worker health work is only meaningful once the data path is configured correctly |
| **DEP-5** | Supabase production reachability + migration state | **DEPENDENCY** | Now readable read-only via the linked CLI (RLS baseline); provider-side retention/backup still provider-owned |
| **DEP-6** | Resend operational status | **DEPENDENCY** | Email is a no-op stub when unset; provider delivery detail is limited |
| **DEP-7** | AI provider configuration | **DEPENDENCY** | Deterministic fallback when unconfigured; failure is silent by design |
| **OPT-1** | External monitoring/APM purchase | **OPTIONAL FUTURE ENHANCEMENT** | L4 |
| **OPT-2** | Platform-level alert routing (Render/Vercel/Supabase notifications) | **OPTIONAL FUTURE ENHANCEMENT** | Provider-owned |
| **OPT-3** | Structured/JSON logging + log shipping | **OPTIONAL FUTURE ENHANCEMENT** | Improves diagnosis; not required for M-items |

---

## 15. Proposed Implementation Sequence (for later Cline execution)

**Not authorized. Each stage requires separate, bounded authorization.** The
sequence is ordered so that correctness precedes breadth, and reuse precedes
new surfaces.

### Stage X1 — Foundation and baseline (no schema change)
* **Objective:** freeze an operational-visibility matrix; inventory what each
  surface reads; document existing semantics (4 health endpoints, worker states,
  failure columns).
* **Bounded scope:** documentation + read-only code inspection only.
* **Dependencies:** none.
* **Verification:** matrix reviewed against code; zero code changes.
* **Stop condition:** if a needed signal proves absent from the schema, stop and
  raise a PO decision rather than adding a table.

### Stage X2 — Worker & queue operational visibility (M1)
* **Objective:** expose backlog, age, stage distribution, stuck/claimed jobs,
  retry exhaustion, `last_error`, reprocess counts.
* **Scope:** read-only projections over `document_processing_queue` via existing
  repositories; new ops endpoints under the existing namespace.
* **Dependencies:** DEP-4.
* **Verification:** seeded queue fixtures; counts reconcile to direct SQL;
  authorization negative tests (non-staff denied, PE staff entity-scoped).
* **Stop condition:** any proposed write/mutation of job state → stop (observe-first).

### Stage X3 — Health correctness & worker liveness (M2)
* **Objective:** `/health` exercises the pool path; worker exposes last-tick /
  heartbeat; startup self-check fails fast on missing required configuration.
* **Scope:** bounded changes to the health surface + worker status method.
* **Dependencies:** X2 (heartbeat design), DEP-4.
* **Verification:** start with `DATABASE_URL` unset → health must report
  **degraded**, not healthy; worker must report not-running; no secrets in output.
* **Stop condition:** if any change would require altering the worker's
  processing semantics → stop; that is a separate remediation task.

### Stage X4 — Aggregation layer: failures, SLA, usage, imports, delivery, AI (M3, S3–S6)
* **Objective:** one read-only service producing unified failure and operational
  summaries across existing tables.
* **Scope:** `services/operational_intelligence.py`; no new tables (views only if
  required and separately authorized).
* **Dependencies:** X1–X3; DEP-1, DEP-3.
* **Verification:** per-domain fixtures; cross-check to source tables;
  **redaction review** for error text and email addresses.
* **Stop condition:** if a unified view requires duplicating domain facts → stop.

### Stage X5 — Operations console extension (M4)
* **Objective:** surface X2–X4 in the existing ops console as tabs/cards.
* **Scope:** `frontend/src/v3/ops/**` extension only; no new dashboard shell.
* **Dependencies:** X2–X4.
* **Verification:** role-based UI tests; responsive/accessibility checks per D21
  and the project responsive matrix.
* **Stop condition:** if a parallel dashboard is proposed → stop.

### Stage X6 — Thresholds & alerting (S1)
* **Objective:** evaluate configured thresholds and dispatch via existing
  notifications.
* **Scope:** reuse `system_settings` keys + `notifications`/`notification_delivery`.
* **Dependencies:** X4; PO decision on thresholds and recipients (PX-6).
* **Verification:** threshold fixtures; duplicate-suppression test (reuse
  `event_key` idempotency); **no alert storms** (rate-limited dispatch).
* **Stop condition:** if alerting requires a new messaging framework → stop.

### Stage X7 — API runtime metrics (S2)
* **Objective:** capture request volume, status distribution, latency, slow/
  error endpoints, auth/authz failures.
* **Scope:** in-process instrumentation; **no request payload retention**.
* **Dependencies:** X4; PO decision on storage/retention (PX-7).
* **Verification:** load test; assert no PII/secret capture.
* **Stop condition:** if it requires a new metrics store/dependency not already
  approved → stop and raise the platform decision.

### Stage X8 — Testing, security verification, operational verification
* **Objective:** independent verification of every prior stage.
* **Verification approach:** positive + negative authorization matrix; tenant/entity
  isolation; secret-exposure test on introspection endpoints; e2e acceptance in
  `e2e/environment/`; operational rehearsal of M6 runbooks.
* **Stop condition:** any cross-tenant ALLOW, any secret exposure, or any
  unverified claim → halt that stage.

---

## 16. Phase 8 Relationship

| Statement | Status |
|---|---|
| Phase 8 remains the **active product roadmap** | **YES** |
| Phase 8-X is a **bounded extension/workstream** | **YES** |
| Phase 8-X **does not replace** Phase 8 | **YES** |
| Phase 8-X **does not retroactively redefine** completed Phase 8 work | **YES** |
| Operational intelligence **supports** the Phase 8 product platform | **YES** |
| Product capabilities and operational intelligence remain **separately traceable** | **YES** — different namespaces, different authorization audiences, different deliverables |

**Phase 8 product capabilities named in the task prompt** (not to be redefined
here): Advanced Carbon Analytics; CarbonTally Insight; Intelligent
Entity-Specific Reports; Report Versioning & Approval; Net-Zero Planning; Carbon
Data Quality Intelligence; Disclosure/Reporting Intelligence; Internal
Benchmarking & Management Insights.

**Discrepancy requiring PO note — see §19 PX-1:**
`docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md:26` records
**"Phase 8 — Advanced Analytics — official product-roadmap name. Same
restrictions as Phase 7 (scope NOT defined; nothing authorized)"**. Separately,
`backend/api/operations_auth.py` is titled *"V3 operations authorization
(Phase 8)"*. Neither matches the 8-capability Phase 8 list given in the task
prompt. This document **does not resolve** the discrepancy; it records it.

---

## 17. Future / Unassigned Capability Boundary

* **No Phase 9 is created, assigned or implied by this document.**
* Historical "Phase 9" labels exist in CarbonTally documentation (e.g.
  `docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md`,
  and V3 lineage migrations such as `20260822000000_p9_rls_recursion_fix.sql`).
  These are treated as **historical lineage only** and are **not** ratified phase
  numbers. That earlier baseline's identifier was never PO-ratified and is
  explicitly flagged as unobtained within that document.
* Capabilities identified beyond Phase 8-X (§13 **L1–L7**, and the OPT items in
  §14) are recorded as **FUTURE / UNASSIGNED** — not as Phase 9, and not as
  Phase 8-X commitments.
* `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` terminates the
  PO-ratified roadmap at Phase 8; nothing here extends it.

---

## 18. RLS Security-Gate Relationship

Two distinct workstreams, deliberately separated:

| | **Phase 8-X — Operational Intelligence** | **RLS Security Gate** |
|---|---|---|
| Nature | Product/platform operational visibility | Production database access-control remediation |
| Status | **Discovery (this document)** | **DEFERRED / NOT YET AUTHORIZED** |
| Implementation | **NOT authorized** | **NOT authorized** |
| Sequence | `RLS-4A → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification` (separate) | preserved in the hold register |
| Document | this document | `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md` |

* The verified RLS baseline (97 of 104 production tables with RLS disabled;
  `anon` holding `GRANT ALL`) **remains preserved and unremediated**.
* Phase 8-X **must not** remediate RLS. If RLS is a dependency for a proposed
  capability, it is recorded as **DEPENDENCY — SEPARATE RLS SECURITY GATE** (§8.5).
* The two workstreams **must not be silently combined**: combining an operational
  visibility change with a security remediation would make both unverifiable and
  would violate the ratified sequencing.
* Backend operational reads are unaffected by the RLS gap because the backend
  holds `BYPASSRLS`. This is a functional convenience, **not** a security
  mitigation, and must not be presented as one.

---

## 19. Explicit PO Decisions Still Required

| ID | Decision | Why it is needed |
|---|---|---|
| **PX-1** | Resolve the **Phase 8 naming/scope discrepancy**: roadmap V1.0 says "Phase 8 — Advanced Analytics, scope NOT defined"; the task states 8 ratified Phase 8 capabilities; `operations_auth.py` labels its work "Phase 8" | Determines what Phase 8-X is extending |
| **PX-2** | Confirm the **Phase 8-X MUST set** (§13 M1–M6) and the initial release boundary | Authorizes a bounded Cline prompt |
| **PX-3** | Confirm Phase 8-X is an **extension/workstream** and not a phase renumber | Prevents timeline/lineage confusion |
| **PX-4** | Authorize (or decline) **platform access** — Render API/console, and a **read-only production DB role** (RLS D-10) | **BL-1/BL-2**: without it, runtime/deployment intelligence cannot be verified |
| **PX-5** | Authorize **schema change** for a worker heartbeat, or require a **reuse-only** solution | Determines whether X3 needs a migration + RLS policy design |
| **PX-6** | Confirm **alert recipients, channels and thresholds** — including whether `sla_breach_alert_*` becomes live | S1 cannot be specified without it |
| **PX-7** | Confirm **retention** for operational data (telemetry, delivery records, runtime metrics) | Currently undefined; `services/retention.py` covers only configured domains |
| **PX-8** | Confirm operational surfaces remain **internal-staff-only** | Prevents customer-visible operational leakage |
| **PX-9** | Authorize a **separate bounded remediation task** for the `DATABASE_URL` configuration/deployment issue | Explicitly **not** Phase 8-X (§11.7) |
| **PX-10** | Decide whether an **incident model** is in scope now or LATER (L1) | New table + RLS design |
| **PX-11** | Decide whether **external monitoring/APM** is to be procured (L4) | Architecture + cost decision |
| **PX-12** | Confirm the **consolidation stance** for the duplicated audit/activity/metrics families (§10) | Determines whether Phase 8-X can deprecate legacy tables (it must not silently drop them) |

---

## 20. Recommended Next Step

**PO review of this boundary document**, specifically:

1. Resolve **PX-1** (Phase 8 naming/scope discrepancy) — it blocks a clean
   statement of what Phase 8-X extends.
2. Approve or adjust the **MUST set (M1–M6)**.
3. Decide **PX-4** (platform access) — it is the only hard blocker for the
   runtime half of the workstream.
4. Decide **PX-5** (heartbeat schema change vs reuse-only) — it determines
   whether Stage X3 needs a migration.
5. Issue a **bounded Cline prompt for Stage X1 and X2 only** (documentation +
   worker/queue visibility), which require **no schema change and no platform
   access**, and which address the largest verified blind spot.
6. Keep the **RLS security gate** and the **`DATABASE_URL` remediation** as
   separate, separately authorized workstreams.

**No implementation, schema change, migration, RLS change, configuration change
or production change was made in producing this document.**
