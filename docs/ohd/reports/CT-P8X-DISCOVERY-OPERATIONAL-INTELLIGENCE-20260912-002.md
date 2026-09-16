---
Document Type: OHD Task Report
Project: CarbonTally
Prompt ID: CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002
Status: COMPLETE
Created: 2026-09-12
---

# OHD Task Report — CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002

## 1. Prompt ID

`CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002`

## 2. Objective

Perform a comprehensive, evidence-based **discovery and
implementation-boundary analysis** for **Phase 8-X — Operational Intelligence**
(a bounded extension/workstream of Phase 8, not a new Phase 9), establishing what
operational intelligence already exists, what is partial, what is missing, what
belongs in Phase 8-X, what does not, the dependencies/blockers, and a bounded
implementation sequence for later Cline execution.

Discovery, architecture and project-boundary only. **No implementation.**

## 3. Repository Areas Inspected

| Area | What was inspected |
|---|---|
| Backend application entry | `backend/main.py` (startup/shutdown lifespan, health endpoints, error handler, bind config, `routes_count`) |
| Backend API layer | `backend/api/` — router prefixes for all 20 registered routers; `v3_operations.py` (49 endpoints), `admin_audit.py`, `admin_providers.py`, `admin_aliases.py`, `admin_imports.py`, `v3_billing.py`, `v3_commercial.py`, `v3_health.py`, `operations_auth.py`, `dependencies.py`, `middleware.py`, `router.py` |
| Workers | `backend/workers/automatic_processing.py` in full (docstring, `start`/`stop`, `_run_loop`, `_tick`, `_process_one`, `_build_service`, singleton) |
| Infrastructure layer | `backend/infra/` — `supabase.py` (`get_database_url`, `get_service_client`, `get_service_pool`, `close_service_pool`), `event_bus.py`, `audit_logger.py`, `ai_runtime.py`, `llm_client.py`, `search_index.py`, `config.py` |
| Services layer | `backend/services/` — `retention.py`, `billing.py`, `work_items.py`, `v3_email.py`, `storage.py`, `automatic_processing.py`, `consultant_lifecycle.py` |
| Core layer | `backend/core/logging.py`, `core/exceptions.py` |
| Legacy modules | `backend/database.py` (legacy Supabase singleton) |
| Error/middleware | `backend/middleware/rate_limit.py` |
| Backup capability | `backend/backup/` (8 modules: service, exporter, crypto, catalog, storage, artifact, settings, errors) |
| Frontend | `frontend/src/App.js` (routing), `frontend/src/v3/ops/**` (26 files), `frontend/src/v3/admin/AdminPage.jsx`, `frontend/src/v3/customer/DashboardPage.jsx`, `frontend/src/components/*`, `frontend/src/lib/realtime/manager.js` |
| Deployment/runtime config | repository root scan (`render.yaml`/`Procfile`/`Dockerfile` **absent**), `runtime.txt`, `vercel.json`, `frontend/vercel.json`, `supabase/config.toml`, `backend/requirements.txt`, `backend/pyproject.toml` |
| Database definitions | local dev catalog (116 public tables) via read-only `psql`; `supabase/migrations/**` (55 files); `database/rc1`, `database/rc2` |
| Verification tooling | `qa_harness/`, `independent_audit/`, `saas-assurance/` (as reuse candidates) |
| Dependency/vendor check | `backend/requirements.txt`, `backend/requirements-dev.txt`, `frontend/package.json` (observability scan) |

## 4. Documents Inspected

| Document | Use |
|---|---|
| `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md` | Primary operations reference — read §1–22 including health checks, env-var reference, logging/diagnostics, worker, DB safety, triage, backup/restore status, incident escalation, known-UNVERIFIED, "never do this" |
| `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` | Deployment configuration record — read §1–6 (access result, repository evidence, VERIFIED, NOT VERIFIED, sensitive/omitted, operational implications) |
| `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | Phase-naming/scope evidence (§4 "Phase 1", phase table lines 24–27, §5–§8) |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md` | Backup/restore status (via ops doc §18 and file presence) |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` (+ 3 sibling backup docs) | Backup capability existence |
| `docs/architecture/CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` | RLS dependency boundary (production baseline) |
| `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md` | RLS hold state (deferred/not authorized) |
| `docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md` | Historical operational-intelligence baseline (unratified identifier; lineage only) |
| `docs/architecture/CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` | Phase 7 closure lineage |
| `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md`, `..._MIGRATION_SAFETY_PLAN_20260911.md`, `..._READINESS_AUDIT_20260911.md` | Production/migration state |
| `AGENTS.md` | Governance: RLS policy, database change policy, auditability, admin control plane (§31), D19/D21/N1/N3 frozen decisions |
| `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | Actor/workspace access model |

**Phase 8 capability specifications: NOT FOUND.** A targeted search for the named
Phase 8 capabilities (Advanced Carbon Analytics, CarbonTally Insight, Net-Zero,
etc.) matched only **UI mockups** (`docs/architecture/UI/**`, `UI2/**`), not
ratified specification documents. Recorded as an evidence gap (§21 A-1).

## 5. Database / Schema Areas Inspected

Read-only inspection of the **local dev database** (`supabase_db_carbon_ledger`,
`default_transaction_read_only=on`) to enumerate `public` tables and the columns
of 24 operational tables; plus the migration storey.

Operational tables examined (with column-level detail): `document_processing_queue`
(79 cols), `system_settings` (60 cols), `report_generation_queue` (28),
`processing_queue` (20), `import_batches` (17), `audit_logs` (17), `notifications`
(17), `work_item_assignments` (17), `ai_content_history` (16), `staff_performance`
(14), `audit_trail` (13), `activity_logs` (12), `processing_logs` (12),
`notification_delivery` (11), `usage_tracking` (11), `team_performance` (11),
`processing_audit_trail` (11), `login_history` (10), `staff_workload` (10),
`domain_events` (8), `email_logs` (8), `activity_feed` (7), `queue_settings` (7),
`dashboard_metrics` (7).

Migrations examined for operational relevance: `20260829000000_v3m9_durable_automatic_processing.sql`,
`20260902030000_phase5_work_item_assignments.sql`, `20260902050000_phase5_notification_event_key.sql`,
`20260913000000_p8_report_lifecycle_status.sql`, `20260824020000_d37_0_*`,
`20260824030000_d37_master_commercial_billing.sql`.

**No schema was modified.** Local database access was read-only.

## 6. Existing Capabilities Identified

**Substantial existing operational intelligence was found** — the discovery's
most important structural result. Highlights (full detail in the main document §3–§5):

1. **Four health endpoints** — `/`, `/health` (PostgREST `glossary` probe),
   `/api/v2/health`, `/api/v3/health/realtime` (Realtime websocket readiness).
2. **Durable worker** — in-process asyncio loop; `document_processing_queue`;
   poll 1.0 s / batch 3; stale-lock reclaim 300 s; durable stage/attempt/error model.
3. **Durable event store** — `domain_events` with `correlation_id`, written by
   `infra/event_bus.py` handlers.
4. **Append-only audit** — `audit_trail` + `AuditLogger` (Phase 7 taxonomy).
5. **Staff operations API** — `/api/v3/ops/*`, **49 endpoints**.
6. **Admin APIs** — `/api/v2/admin/{audit,providers,aliases,imports}`.
7. **Billing/usage** — `/api/v3/billing` (10 endpoints), `/api/v3/commercial`,
   `services/billing.py`, `usage_tracking`.
8. **AI usage + cost already captured** — `ai_content_history` (tokens, cost,
   model, latency), plus `ai_*` fields on the processing queue and report queue.
9. **Report generation ops** — `report_generation_queue` (`status`,
   `progress_percentage`, `current_step`, `error_log`, `ai_cost`).
10. **Import ops** — `import_batches` (`rows_total/imported/skipped/duplicate`, `errors`, `status`).
11. **Delivery ops** — `notification_delivery`, `email_logs`, `notifications` (with `event_key` idempotency).
12. **Auth ops data** — `login_history` (`is_successful`, `failure_reason`).
13. **SLA** — `sla_definitions`, `sla_compliance`, settings alert flags, `SlaTab.jsx`.
14. **QC / issues triage** — `qc_*`, `issues`, `CtQcTab.jsx`, `IssuesTriageTab.jsx`.
15. **Staff workload/performance** — 4 tables + `StaffRoster.jsx`.
16. **Retention (N3)** — configurable, server-side enforced, dry-run default,
    audit/evidence excluded.
17. **Backup export capability** — encrypted/checksummed logical export (`backend/backup/**`).
18. **Internal ops UI** — 26 files under `frontend/src/v3/ops/` incl. dashboard,
    audit console, SLA, commercial, QC, settings tabs.
19. **Request correlation + error envelope** — `request_id` surfaced in V3 errors.
20. **Rate limiting** — middleware + `system_settings.api_rate_limit`.

## 7. Missing / Partial Capabilities Identified

**Gaps (main document §6, G1–G16):**

* **MISSING:** unified failure store/view (errors fragmented across 6 tables);
  worker liveness/health/backlog surface; version/build introspection endpoint;
  API runtime metrics (no latency/volume/error capture); incident model;
  availability/SLO definition; operational-brain read-only production role.
* **DEFECT:** `/health` does not test the `asyncpg` pool data path (verified);
  no startup configuration validation.
* **PARTIAL:** alerting (config keys exist but are never evaluated); admin
  control plane UI (`AdminPage.jsx` is customer org-admin, not internal `/admin`);
  structured logging (text stdio only, no retention control); auth-failure
  aggregation; provider/dependency health; service-recovery runbooks.
* **DEFERRED (own roadmap):** backup scheduling, storage backup, restore, RTO/RPO.
* **ABSENT ENTIRELY:** any third-party observability/APM tooling — verified: **no**
  Sentry, Prometheus, OpenTelemetry, Datadog, New Relic, Grafana or statsd in
  `backend/requirements.txt`, `backend/requirements-dev.txt`, `frontend/package.json`
  or `backend/main.py`, and no metrics/monitoring/telemetry module in application code.

## 8. Runtime Incident Findings

**Reported symptom:** the automatic-processing worker failed to obtain a database
pool because `DATABASE_URL` / `SUPABASE_DB_URL` was not configured, after which
the backend shut down.

**Findings (main document §11):**

| # | Finding | Status |
|---|---|---|
| 1 | The worker needs the DSN because `_tick()` → `get_repositories()` → `get_pool()` → `get_service_pool()` → `get_database_url()`, which **raises `RuntimeError` when the var is absent**. The pool underpins **every** repository, so the dependency is **architectural, not worker-specific**. | **VERIFIED** |
| 2 | It is **not a stale code path** — the worker is the current, migration-backed durable mechanism (`v3m9`) started from the app lifespan. | **VERIFIED** |
| 3 | **`start()` never touches the pool** (it only creates an asyncio task), so the `main.py` try/except commented *"worker must never block startup"* **cannot catch this failure** — the guard gives **false reassurance**. | **VERIFIED** |
| 4 | The failure is **caught** by `_run_loop`'s `except Exception` (*"the loop must never die"*) and logged every poll interval. **The worker does not crash the process.** | **VERIFIED (code path)** |
| 5 | **`/health` uses the PostgREST client (`glossary` probe), not the pool.** With `DATABASE_URL` unset it can still report `"healthy"` while all V3 repository endpoints and the worker are non-functional. **Health-check blind spot.** | **VERIFIED** |
| 6 | The repository's production env artefacts list `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` but **no `DATABASE_URL`/`SUPABASE_DB_URL`** — incomplete relative to what the code requires. Render's *actual* env vars are **NOT VERIFIED**. | **VERIFIED (repo) / UNVERIFIED (platform)** |
| 7 | No drop-in alternative DB path exists: only `/health` and legacy modules use the PostgREST service client; the repository layer has **no** service-role-REST fallback. | **VERIFIED** |
| 8 | **Why the backend shut down is NOT established by repository evidence.** Candidate mechanisms: platform restart/deploy/OOM, health-path mismatch (Render health path UNVERIFIED), a different component failing at startup, or operator action. | **INFERRED / UNKNOWN** |

**Classification:** configuration debt **and** deployment debt **with an
architecture dimension**. Explicitly **not** classified as a stale path or a
worker code bug, and the shutdown is **not** attributed to the worker.

**Scope decision recorded:** the health-path correctness, startup self-check and
worker-visibility aspects **belong in Phase 8-X** (M2/M5); **fixing** the missing
variable / Render config / worker code is a **separate bounded remediation task**
and was **not performed**. §11.8 of the main document lists the eight questions a
future remediation task must investigate.

## 9. Authorization / Tenancy Findings

* The authoritative staff chain is documented in `backend/api/operations_auth.py`:
  authenticated user → `staff_profiles` (active) → `staff_roles.permissions`
  (jsonb) → scope by `staff_profiles.entity_id` (`NULL` = internal staff,
  populated = PE staff).
* Every `/api/v3/ops/*` endpoint passes `require_staff()` or
  `require_internal_staff()` and **re-authorizes each item/batch/entity**;
  browser-supplied ids are never trusted. PE staff are structurally excluded from
  the manual-extraction pipeline.
* **Existing authorization is sufficient** for the proposed operational surfaces
  that read existing data through the backend.
* **New design required** for: deployment/config introspection (must expose
  *presence*, never values), runtime metrics (aggregation-only, no tenant-activity
  leakage), and correlation-id exposure.
* **Recommendation recorded:** all Phase 8-X runtime/infrastructure surfaces are
  **internal-staff-only**; no customer- or PE-facing runtime surface in the
  initial release.
* **Tenancy:** operational tables are **mixed-scope** (org-scoped vs global).
  Operational views must be explicit about scope and must never become a
  cross-tenant leakage path.
* **RLS dependency recorded** as **DEPENDENCY — SEPARATE RLS SECURITY GATE**
  (main document §8.5): backend reads are unaffected (backend holds `BYPASSRLS`),
  but any **new** table proposed in Phase 8-X would require RLS policy design at
  creation time, and `domain_events` / `import_batches` are already RLS-enabled
  with zero policies (service-only).

## 10. Duplication Findings

Eleven overlaps identified (main document §10, D1–D11). Material ones:

| ID | Overlap | Recommendation |
|---|---|---|
| D1 | `audit_trail` (authoritative, Phase 7) vs `audit_logs` vs `activity_logs` | Treat `audit_trail` as authoritative; do not create a third |
| D2 | 6 domain `*_activity_log` tables + `processing_audit_trail` + `review_audit_trail` | Legitimate per-domain, but **aggregate rather than add more** |
| D4 | `document_processing_queue` (authoritative) vs `processing_queue` (legacy-looking parallel queue) | Verify before reuse; do not build on both |
| D6 | `usage_tracking` vs `billing_*` (7) vs AI cost fields | One aggregation layer; no fourth counter |
| D7 | `staff_performance` vs `team_performance` vs `staff_daily_performance` vs `staff_workload` | Consolidate the read model |
| D10 | Four health endpoints with differing semantics | Consolidate/document semantics; do not add a fifth |
| D11 | `dashboard_metrics` (business dashboard data) | **Not** runtime telemetry — do not conflate |

**Guiding principle recorded: aggregate, do not duplicate.** No consolidation was
performed (out of scope for discovery).

## 11. Proposed Phase 8-X Boundary

**MUST (initial release):** M1 worker & queue operational visibility ·
M2 health-path correctness + worker liveness · M3 unified failure visibility ·
M4 operations-console extension · M5 runtime/deployment introspection +
startup self-check · M6 operational runbooks.

**SHOULD:** S1 threshold evaluation + alert dispatch · S2 API runtime metrics ·
S3 AI runtime/cost ops · S4 delivery ops · S5 import ops · S6 auth-failure ops.

**LATER:** L1 incident model · L2 availability/SLO · L3 backup/restore visibility ·
L4 external monitoring/APM · L5 anomaly detection · L6 composite health score ·
L7 internal admin control plane.

**OUT OF SCOPE:** RLS remediation · migration-backlog adjudication · replacing
calculation/factor/report/audit architecture · Phase 8 product analytics
(Insight, net-zero, disclosure) · generic SIEM/enterprise monitoring marketing ·
cross-tenant customer analytics · automatic production remediation ·
backup/restore implementation · **fixing the `DATABASE_URL` issue**.

## 12. Proposed Implementation Sequence

`X1` foundation/baseline (no schema change) → `X2` worker & queue visibility →
`X3` health correctness & worker liveness → `X4` aggregation layer (failures,
SLA, usage, imports, delivery, AI) → `X5` operations-console extension →
`X6` thresholds & alerting → `X7` API runtime metrics → `X8` testing/security/
operational verification.

Each stage is specified with objective, bounded scope, dependencies, verification
approach and **stop condition** (main document §15). Ordering rationale: correctness
before breadth; reuse before new surfaces; no schema change until X3's heartbeat
decision (PX-5).

## 13. Dependencies / Blockers

| ID | Item | Type |
|---|---|---|
| BL-1 | **No Render/platform access** — deployment config, env vars, health path, restart policy, log retention all UNVERIFIED | **BLOCKER** (blocks *verification*, not the in-app work) |
| BL-2 | **No read-only production DB role** | **BLOCKER** (production verification of operational read models) |
| DEP-1 | Phase 8 report lifecycle (report-queue visibility) | DEPENDENCY |
| DEP-2 | **RLS security gate** | **DEPENDENCY — SEPARATE RLS SECURITY GATE** |
| DEP-3 | Production migration drift (21/55 applied; 12 repo tables absent) | DEPENDENCY |
| DEP-4 | `DATABASE_URL`/pool configuration correctness | DEPENDENCY |
| DEP-5 | Supabase production reachability/state | DEPENDENCY |
| DEP-6 | Resend operational status | DEPENDENCY |
| DEP-7 | AI provider configuration (silent deterministic fallback) | DEPENDENCY |
| OPT-1..3 | External monitoring purchase; platform alert routing; structured logging/log shipping | **OPTIONAL FUTURE ENHANCEMENT** |

## 14. RLS Boundary Confirmation

Confirmed:

* Phase 8-X is **operational intelligence discovery/implementation**; RLS
  remediation is a **separate production security gate**.
* The verified RLS production baseline and the proposed remediation remain
  **preserved for future authorization** in
  `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md`
  and are recorded as **DEFERRED / NOT YET AUTHORIZED**.
* **No RLS remediation of any kind was performed.** No RLS was enabled or
  disabled; no policy created/altered/dropped; no grant or revoke issued; no
  `SECURITY DEFINER` function modified.
* RLS is recorded in this discovery **only** as a dependency
  (`DEPENDENCY — SEPARATE RLS SECURITY GATE`) and as a constraint on any future
  new table.
* The two workstreams are explicitly **not** recommended to be combined.

## 15. Files Created

| Path | Status |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md` | **CREATED** — 20 required sections (verified) |
| `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md` | **CREATED** — this report |

## 16. Files Modified

**NONE.** No existing file was modified, renamed, moved or deleted by this task.
Both created documents are new, untracked files.

## 17. Confirmation — No Implementation Performed

Confirmed: no implementation of any kind was performed. No Phase 8-X capability
was built. No application code was written or changed. No worker code changed. No
endpoint added. No UI added or changed. No alerting, metrics, heartbeat, incident
model or aggregation service was implemented. No `DATABASE_URL` fix was applied.
No environment variable was added.

## 18. Confirmation — No Database / Schema / RLS / Grant / Function Changes

Confirmed **NO** changes to: database schema; migrations (none created, modified
or applied); RLS (none enabled/disabled); policies (none created/altered/dropped);
grants (none granted/revoked); `SECURITY DEFINER` functions (none created/altered).
The only database interaction was **read-only** (`default_transaction_read_only=on`).

## 19. Confirmation — No Production Configuration or Data Changed

Confirmed: **no** production configuration change, **no** production data change,
**no** production access of any kind during this task. No Render, Vercel, Supabase
or Resend setting was touched. No migration was applied to any environment. No
secret was read, printed, stored or transmitted.

## 20. Git / Worktree Status

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD (start of task) | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| HEAD (end of task) | `19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** |
| Modified (tracked) files | **208** — unchanged; no tracked file touched |
| Untracked files | **56** at task start → **57** at task end. **Two files were created**, but `git status --short` collapses an untracked *directory* into one entry: the new architecture document adds one entry, while this report lands inside the already-untracked `docs/ohd/` directory so it does not add a further entry |
| Staged files | **0** |
| Commits created | **0** |
| Pushed | **NO** |
| Reset / clean / stash / discard | **NONE** |
| Unrelated work | **Preserved exactly** |

All pre-existing modified and untracked work was preserved. No file outside the
two created by this task was written, staged, reverted or removed.

## 21. Ambiguities and Evidence Gaps

| # | Gap | Disposition |
|---|---|---|
| A-1 | **Phase 8 naming/scope discrepancy.** `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md:26` states *"Phase 8 — Advanced Analytics — official product-roadmap name. Same restrictions as Phase 7 (scope NOT defined; nothing authorized)"*. The task prompt states 8 ratified Phase 8 capabilities. `backend/api/operations_auth.py` is titled *"V3 operations authorization (Phase 8)"*. | **Recorded, not resolved** → PO decision **PX-1** |
| A-2 | **No ratified Phase 8 capability specification found.** Targeted search matched only UI mockups, not specification documents. | Evidence gap; noted in main document §4 |
| A-3 | **Shutdown cause of the runtime incident is UNKNOWN.** Repository evidence shows the worker failure is non-fatal. | **UNKNOWN / REQUIRES FURTHER INVESTIGATION** (main document §11.3) |
| A-4 | **Render platform state entirely UNVERIFIED** (env vars, health path, restart policy, log retention). No Render access. | **BLOCKER BL-1**; PO decision **PX-4** |
| A-5 | **Documentation conflict:** the ops quick reference §10 states `supabase migration list --linked` is **PROHIBITED** (it creates a temporary login role — a mutation), whereas the separate RLS baseline discovery used exactly that command (with disclosure) to establish the authoritative 21-applied/34-outstanding migration state. | Recorded as a conflict; **not** silently resolved. The RLS discovery disclosed the transient login role explicitly |
| A-6 | **Ops doc §10 records production migration history as UNKNOWN** and effective schema ≈ migrations 1–21; the RLS baseline has since **verified 21 applied / 34 outstanding**. | Superseding evidence recorded; ops doc is not modified |
| A-7 | **Production column-level/default privileges** remain UNVERIFIED (from the RLS work) and are inherited by this discovery. | Limitation carried forward |
| A-8 | **`processing_queue` vs `document_processing_queue`** — which is live is not conclusively established from static inspection. | Marked "verify before reuse" (D4) |
| A-9 | **Local dev DB used as schema proxy** (116 tables) while production holds 104. | Qualified throughout; production differences taken from the RLS baseline |
| A-10 | **`dashboard_metrics` semantics** (business vs operational) not established beyond its columns. | Marked D11; do not conflate |
| A-11 | Provider capabilities (Render/Supabase/Vercel backup, monitoring, alerting) are **not** claimed as implemented. | Explicitly marked provider-owned/UNVERIFIED |

**No ambiguity required stopping the task.** None required any code, schema, RLS,
grant, function, configuration or production change.

## 22. Final Verdict

**`PHASE 8-X DISCOVERY COMPLETE — IMPLEMENTATION BOUNDARY READY FOR PO REVIEW`**

The boundary is ready for review with two explicit qualifications that the PO must
adjudicate: the **Phase 8 naming/scope discrepancy** (PX-1) and the **unresolved
cause of the runtime shutdown** (A-3). Neither blocks PO review; both block a
clean implementation prompt until decided.

---

## Appendix — Discovery Status Line

```text
PHASE 8-X — OPERATIONAL INTELLIGENCE
Discovery            : COMPLETE (read-only, evidence-based)
Implementation       : NOT AUTHORIZED
Code/schema/RLS      : UNCHANGED
Production           : UNCHANGED
Existing signal      : SUBSTANTIAL (jobs, events, audit, usage, AI cost,
                       reports, imports, delivery, auth, SLA, staff)
Primary gaps         : aggregation, worker liveness, health-path correctness,
                       alerting, deployment introspection, observability tooling
Blockers             : platform access (BL-1), read-only prod DB role (BL-2)
RLS                  : DEPENDENCY — SEPARATE RLS SECURITY GATE (deferred)
Open PO decisions    : PX-1 … PX-12
```
