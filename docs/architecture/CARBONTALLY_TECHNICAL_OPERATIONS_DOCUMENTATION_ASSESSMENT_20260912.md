# CarbonTally — Technical Operations Documentation Assessment

**Prompt Ref:** `CT-P7-CLOSURE-20260912-006`
**Date:** 2026-09-12
**Document type:** Repository assessment + recommendation (no implementation).
**Companion:** `docs/architecture/CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md`

> This is an **assessment**, not a manual. It determines what technical operations/troubleshooting documentation already exists, classified **DOCUMENTED / PARTIALLY DOCUMENTED / NOT DOCUMENTED / NOT APPLICABLE**, and recommends a minimum useful operations manual. Nothing here invents commands or recovery steps: where a procedure cannot be verified from the repository, it is marked **UNVERIFIED**.

---

## 1. Purpose and Scope

Assess CarbonTally's existing operational documentation against the subsystems a future maintainer must troubleshoot, and recommend the smallest useful operations documentation set.

## 2. Repository Evidence Inspected

| Area | Evidence (actual repository) |
|---|---|
| Docs tree | `docs/architecture` (many `CARBONTALLY_*`), `docs/audit`, `docs/cline/prompt-history`, `docs/legal`, `docs/guides` (**empty**), `docs/api` (**empty**), `docs/standalone`, `docs/business`, `docs/Pricing`, `docs/Final*`, `docs/Robbie`; **`docs/operations` does not exist** |
| Existing ops-adjacent docs | `docs/architecture/CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md`, `…DEPLOYMENT_READINESS_20260911.md`, `…MIGRATION_SAFETY_PLAN_20260911.md`, `…PRECOMMIT_GATE_20260911.md`, `…RELEASE_MANIFEST_20260911.md`, `…RELEASE_BOUNDARY_AUDIT_20260911.md`, `…READINESS_AUDIT_20260911.md`, `…SUPABASE_RECONCILIATION_20260911.md`, `…AUTHENTICATION_ACCESS_SPEC_20260911.md`, `…POST_PUBLICATION_CHANGELOG_20260911.md`, `…BACKUP_ARCHITECTURE_20260911.md`, `…BACKUP_RESTORE_ROADMAP_V1.0.md`, `…BACKUP_IMPLEMENTATION_PHASE1_20260911.md`, `…BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md`, `…BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md` |
| Backend | `backend/main.py`, `backend/main_v2.py`, `backend/api/**` (router, deps, middleware), `backend/domain/**` (24 modules), `backend/data/**` (37 repos), `backend/engines/**` (12), `backend/services/**`, `backend/infra/**` (supabase, config, llm_client, ai_runtime, audit_logger, event_bus, search_index), `backend/workers/automatic_processing.py`, `backend/core/**` (logging, exceptions, types, units), `backend/middleware/rate_limit.py`, `backend/backup/**` |
| Frontend | `frontend/src/**`, `frontend/src/v3/**`, `frontend/src/App.js`, `frontend/src/Login.js`, 22 test files |
| DB | `supabase/migrations/**` (**54** SQL files), `supabase/seed.sql`, `supabase/config.toml`, `supabase/tools` |
| Deploy config | `vercel.json` (SPA rewrites + legacy `/admin`); **no `render.yaml` / `Procfile` / `Dockerfile`** in the repo |
| CI/CD | `.github/workflows/playwright.yml` only |
| Tests | `backend/tests/unit` (125 files), `integration` (30), `e2e` (4); `frontend/src/**/__tests__` (22); root `tests/example.spec.ts`; `qa_harness/**`; `e2e/environment/**` |
| Tools | `tools/{carbon_data_factory, migration_generator, schema_auditor, load_tester, benchmark_runner, seed_investor_demo, documentation_generator, provision_tesseract_local.sh}` |
| Health | `GET /health` (`main.py:302`), `GET /api/v2/health` (`router.py:77`), `GET /api/v3/health/realtime` (`v3_health.py:111`) |
| Email | `backend/services/v3_email.py` (+ `email_service.py`, `email.js`) — Resend, no-op stub when `RESEND_API_KEY` unset |
| Config | `backend/config.py` (legacy), `backend/infra/config.py` (typed), `backend/infra/supabase.py` (URL/key/DB URL) |

## 3. Method and Classification Legend

Each subsystem is classified from **repository evidence**:

* **DOCUMENTED** — a current document exists that a maintainer could act on.
* **PARTIALLY DOCUMENTED** — some relevant material exists (architecture/readiness/verification docs) but no consolidated operational/troubleshooting procedure.
* **NOT DOCUMENTED** — no operational documentation found.
* **NOT APPLICABLE** — the subsystem does not exist.
* **UNVERIFIED** — a specific command/value cannot be confirmed from the repository.

## 4. Module-by-Module Assessment

| # | Subsystem | Classification | What exists | What is missing | Implementation lives in | Extend existing? | New runbook? | Oper. risk if undocumented |
|---|---|---|---|---|---|---|---|---|
| 1 | Vercel (frontend hosting) | PARTIALLY DOCUMENTED | `vercel.json`; deployment-readiness/release-manifest docs | No consolidated Vercel project/rewrites/env reference; project settings not in repo | `vercel.json` | Yes | Add section | Medium |
| 2 | Render (backend hosting) | **NOT DOCUMENTED (UNVERIFIED)** | None (no `render.yaml`/`Procfile`/`Dockerfile`) | Start command, health path, build command | *(not in repo)* | — | Yes — capture | **High** |
| 3 | Supabase (DB/Auth/Storage/Realtime) | PARTIALLY DOCUMENTED | `supabase/config.toml`; `SUPABASE_RECONCILIATION`; `MIGRATION_SAFETY_PLAN`; `AUTH_ACCESS_SPEC` | Project ref/region, RLS/Realtime troubleshooting | `supabase/**`, `backend/infra/supabase.py` | Yes | Yes | High |
| 4 | PostgreSQL (schema/migrations) | PARTIALLY DOCUMENTED | 54 migrations; `docs/standalone/MIGRATION_BASELINE_REPORT.md`; migration-safety plan | Consolidated migration procedure + drift/rollback limits | `supabase/migrations/**` | Yes | Yes | High |
| 5 | Storage (documents) | PARTIALLY DOCUMENTED | D32 private-documents migration; `services/storage.py`; backup roadmap (storage backup NOT implemented) | Bucket/RLS/signed-URL troubleshooting | `backend/services/storage.py` | Yes | Yes | Medium–High |
| 6 | Environment variables / secrets | PARTIALLY DOCUMENTED | `.env*` local; keys enumerated in code | Consolidated env-var reference (name → purpose → required) | `auth.py`, `infra/supabase.py`, `infra/config.py` | Yes | Yes | High |
| 7 | Backend startup / routing / DI | PARTIALLY DOCUMENTED | `main.py`, `main_v2.py`, `api/router.py`, Blueprint; legacy-conformity plan | Startup/DI troubleshooting | `backend/main*.py`, `backend/api/**` | Yes | Yes | Medium |
| 8 | Backend error handling / logging | PARTIALLY DOCUMENTED | `core/exceptions.py`, `core/logging.py`, request middleware, error envelope | Log locations/levels, correlation-id, error-code catalogue | `backend/core/**`, `api/middleware.py` | Yes | Yes | Medium |
| 9 | Background jobs / worker | PARTIALLY DOCUMENTED | `workers/automatic_processing.py` (lifespan loop, `FOR UPDATE SKIP LOCKED`, stale-lock recovery) | Worker restart/stuck-job/backlog recovery | `backend/workers/**`, `services/automatic_processing.py` | Yes | Yes | **High** |
| 10 | Frontend build/deploy/config | PARTIALLY DOCUMENTED | CRA build (compiles); `vercel.json`; `REACT_APP_*` | Build/deploy troubleshooting | `frontend/**` | Yes | Yes | Medium |
| 11 | Frontend auth/runtime | DOCUMENTED | `CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md`; `AUTH_ACCESS_SPEC` | Minor runtime-config notes | `frontend/src/Login.js`, `v3/api.js` | Yes | No | Low |
| 12 | Carbon calculation engine | PARTIALLY DOCUMENTED | `engines/calculation.py`, `domain/calculation.py`; evidence/provenance principles; Phase 7 docs | "Unexpected result" investigation procedure | `backend/engines/calculation.py` | Yes | Yes | **High** (carbon correctness) |
| 13 | Emission factors / importers (DEFRA, SEAI) | PARTIALLY DOCUMENTED | `tools/carbon_data_factory`, `src/providers/defra/parser.py`, `MIGRATION_BASELINE_REPORT` | Import failure/duplicate/rollback + factor versioning procedure | `data/emission_factors.py`, `tools/**`, `src/providers/**` | Yes | Yes | High |
| 14 | Ingestion / extraction / OCR | PARTIALLY DOCUMENTED | `engines/extraction.py`, `ai_extraction.py`, `services/automatic_*`; Blueprint §9/§10; `provision_tesseract_local.sh` | Extraction/OCR failure triage, reprocessing | `backend/engines`, `backend/services` | Yes | Yes | Medium–High |
| 15 | Manual extraction / batch / validation / review / QC | PARTIALLY DOCUMENTED | WS4/Gate reports; P6 architecture docs; `domain/partners.py` state machine | Workflow triage runbook | `api/v3_operations.py`, `domain/partners.py` | Yes | Yes | Medium |
| 16 | Reporting / export | PARTIALLY DOCUMENTED | `engines/report_generation.py`, `pdf_render.py`, `api/v3_reports.py`, `v3_exports.py` | Report-generation failure triage | `backend/engines/**`, `backend/api/**` | Yes | Yes | Medium |
| 17 | Audit trail / evidence / package | DOCUMENTED | Phase 7 implementation + independent verification reports; evidence-principles doc | Runbook for investigating via console/package | `domain/audit.py`, `data/audit.py`, `data/reporting.py` | Yes | Light | Medium |
| 18 | Authentication / RBAC / RLS | DOCUMENTED | `AUTH_ACCESS_SPEC_20260911.md`, `docs/RBAC.md`, `CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`, `ADMIN_CONTROL_PLANE_DECISION.md` | RLS-denial troubleshooting procedure | `backend/auth.py`, `backend/api/*_auth.py` | Yes | Light | Medium |
| 19 | Email (Resend) | **NOT DOCUMENTED** | `services/v3_email.py` (documented in code) | Delivery-failure/config troubleshooting | `backend/services/v3_email.py` | Yes | Yes | Medium |
| 20 | Testing infrastructure | PARTIALLY DOCUMENTED | 125 unit / 30 integration / 4 e2e backend; 22 frontend; `qa_harness/**`; CI Playwright | How to run suites/gates; expected baselines | `backend/tests/**`, `qa_harness/**` | Yes | Yes | Medium |
| 21 | CI/CD | PARTIALLY DOCUMENTED | `.github/workflows/playwright.yml` only | Backend/frontend CI gates | `.github/workflows/**` | Yes | Yes | Medium |
| 22 | Deployment / release procedure | DOCUMENTED (partial) | `RELEASE_MANIFEST`, `PRECOMMIT_GATE`, `DEPLOYMENT_READINESS`, `RELEASE_BOUNDARY_AUDIT`, `POST_PUBLICATION_CHANGELOG` | Consolidated release runbook + post-deploy checks | `docs/architecture/**` | Yes | Consolidate | Medium |
| 23 | Backup / restore / DR | PARTIALLY DOCUMENTED | `BACKUP_ARCHITECTURE`, `BACKUP_RESTORE_ROADMAP` (restore **NOT IMPLEMENTED**), backup IV reports, `backend/backup/**` | Restore procedure (none exists), RTO/RPO | `backend/backup/**` | Yes | Yes | **High** |
| 24 | Incident handling / escalation | **NOT DOCUMENTED** | None found | Incident runbook, escalation rules | — | — | Yes | Medium–High |
| 25 | Health checks / post-deploy verification | PARTIALLY DOCUMENTED | `/health`, `/api/v2/health`, `/api/v3/health/realtime`; deep-link deploy verify record | Health-check + post-deploy checklist | `backend/main.py`, `api/router.py`, `api/v3_health.py` | Yes | Yes | Medium |

## 5. Assessment Summary

Assessed subsystems: **25**.

| Classification | Count | Items |
|---|---|---|
| **DOCUMENTED** | **3** | Frontend auth/runtime (11); Audit/evidence (17); Authentication/RBAC/RLS (18) — plus deployment/release is strong-but-partial (22) |
| **PARTIALLY DOCUMENTED** | **19** | 1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 20, 21, 22, 23, 25 |
| **NOT DOCUMENTED** | **3** | Render hosting (2); Email/Resend (19); Incident handling/escalation (24) |
| **NOT APPLICABLE** | 0 | — |

> Counts: **DOCUMENTED 3 · PARTIALLY DOCUMENTED 19 · NOT DOCUMENTED 3** (deployment/release counted as partially documented because it is strong but not consolidated into an operating runbook).

### Highest-risk gaps

1. **Render backend hosting is undocumented in the repository** — no `render.yaml`/`Procfile`/`Dockerfile`, so the production start command/build/health path is **UNVERIFIED**. A redeploy cannot be reproduced from repo evidence alone.
2. **Backup/Restore/DR** — restore is **NOT IMPLEMENTED**, no proven restore drill, no RTO/RPO, storage objects not backed up (roadmap states this explicitly). Highest business-continuity risk.
3. **No consolidated operations/troubleshooting manual** (`docs/operations` does not exist; `docs/guides` empty).
4. **Background worker recovery** — the durable automatic-processing worker has no operational runbook (stuck jobs, backlog, stale locks).
5. **Carbon calculation & factor/importer troubleshooting** — no "unexpected result" or import-failure procedure (highest *correctness* risk).
6. **Email/Resend** operations undocumented.
7. **Incident/escalation** undocumented.

## 6. Recommended Technical Operations Manual (proposed, NOT created)

**Proposed path:** `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_TROUBLESHOOTING_AND_RECOVERY_MANUAL_V1.0.md`

**Do not create it yet.** This assessment shows much of the source material is **not yet verified enough** to author safe, command-level procedures (see §9). Author it only when each section's commands/values can be confirmed against the repository/running environment.

**Recommended structure (25 sections):**

1. System overview (actors, services, data flow)
2. Service inventory (Vercel, Render, Supabase, Resend, worker)
3. Deployment topology (public site vs `/app`, `/consultant`, `/pe`, `/ops`, `/admin`)
4. Environment/configuration (env-var reference; `backend/infra/config.py`, `infra/supabase.py`)
5. Health checks (`/health`, `/api/v2/health`, `/api/v3/health/realtime`)
6. Log locations & levels (`core/logging.py`, request correlation ids)
7. Common failure modes (index)
8. Backend/API troubleshooting (`api/router.py` error envelope, `core/exceptions.py`)
9. Frontend troubleshooting (build, `REACT_APP_*`, deep-link rewrites)
10. Database troubleshooting (connection pool, RLS, migrations)
11. Supabase troubleshooting (auth/REST/realtime/storage)
12. Authentication troubleshooting (`CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK` extension)
13. RLS/authorization troubleshooting (`auth.py`, `*_auth.py`, RLS helpers)
14. Document-processing troubleshooting (ingestion/extraction/OCR, `provision_tesseract_local.sh`)
15. Calculation-engine troubleshooting (snapshots, provenance, `content_hash`)
16. Factor/import troubleshooting (DEFRA/SEAI importers, versioning, duplicates)
17. Audit/evidence troubleshooting (Phase 7 console/package/hash)
18. Email troubleshooting (Resend config/delivery, no-op stub behaviour)
19. Deployment failures (Vercel/Render — **pending verified Render config**)
20. Safe rollback/recovery (app rollback vs migration rollback limits)
21. Backup/restore status & limitations (restore NOT implemented; storage not backed up)
22. Post-recovery verification (health + smoke + evidence)
23. Incident documentation template
24. Escalation rules
25. "Never do this in production" safety rules (see §7)

## 7. Carbon-Accounting Safety Rule (mandatory for the future manual)

**Technical recovery ≠ carbon-accounting correction.** A developer must **not** silently alter:

* activity data; emission factors; mappings; calculations; historical results; evidence; audit records

…simply to make a system error disappear. Any correction that affects carbon results must **preserve provenance and auditability** and follow the appropriate workflow (correction → recalculation → new snapshot; original snapshot retained). The manual must state this explicitly in the "never do this in production" section.

## 8. No-Surveillance Principle

The audit/assurance capability exists for **accountability, traceability, security, investigation, evidence and governance**. Session duration (F2-3), where ever recorded, must **not** be framed or used as employee productivity scoring or surveillance. The manual must carry this principle.

## 9. UNVERIFIED Items (cannot be asserted from repository evidence)

| Item | Status |
|---|---|
| Render production **start command / build command / health path** | **UNVERIFIED** — no `render.yaml`/`Procfile`/`Dockerfile` in repo |
| Vercel project settings, domains, env configuration | **UNVERIFIED** — only `vercel.json` present |
| Exact environment-variable **values**, secrets, project refs | **UNVERIFIED** (values are local `.env*`, not in repo) |
| Supabase **region / availability / production reachability** | **UNVERIFIED** (prior reconciliation recorded production as unreachable/UNKNOWN) |
| **Restore** procedure & RTO/RPO | **UNVERIFIED / NOT IMPLEMENTED** |
| Whether migration 54 is applied in production | **UNVERIFIED** (Phase 7 migration explicitly NOT applied) |
| CI beyond Playwright (backend/frontend pipelines) | **UNVERIFIED** — only `playwright.yml` present |

## 10. Recommended Next Action

**Smallest logical next step:** author a **short, verified operations quick-reference** (not the full manual) covering only what is already verifiable from the repository — **service inventory, health checks, environment-variable reference, log locations, and the "carbon-accounting correction vs technical recovery" safety rule** — and, separately, **capture the Render deployment configuration** so manual section 19 becomes verifiable.

Do **not** begin the full 25-section manual, residual remediation, or Phase 8 as part of this task.

## 11. Update — Newly Verified Evidence (2026-09-12, `CT-OPS-QUICKREF-20260912-007`)

Minimal update; the original findings above are preserved.

| Item | Previous statement | Newly verified |
|---|---|---|
| Render hosting config | "no `render.yaml`/`Procfile`/`Dockerfile`; build+start UNKNOWN" | **Still no `render.yaml`/`Procfile`/`Dockerfile`, but a repo-root `runtime.txt` = `python-3.11.9` exists**, and the CORS allow-list references `https://carbontally-api.onrender.com` (`backend/config.py`). The Render **service settings remain UNVERIFIED** (no safe Render access). |
| Backend start path | "PARTIALLY DOCUMENTED" | **Verified from code**: ASGI `main:app`, Uvicorn, `HOST`/`PORT` env-driven (defaults `0.0.0.0`/`8000`), `RELOAD` defaults to `true`; startup starts the durable worker; shutdown stops it. The **Render-configured** command remains UNVERIFIED. |
| Health checks | "PARTIALLY DOCUMENTED" | **Verified**: `/`, `/health` (healthy/degraded), `/api/v2/health`, `/api/v3/health/realtime`. |
| Migrations at startup | not stated | **Verified: not run at startup.** |
| Backup restore | "restore NOT IMPLEMENTED" | **Re-confirmed**: no `restore` implementation in `backend/backup/*.py`; scheduled backups/restore drill/RTO/RPO not implemented. |
| `docs/operations` | "does not exist" | **Now created** with the quick reference and Render record (see §6/§7 of the new quick reference). The full 25-section manual is **still not created**. |

New artifacts: `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md`, `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`.

*End of assessment.*


