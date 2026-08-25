---
Document Type: V3 Conformity & Legacy Elimination Plan
Project: CarbonTally
Architecture: CarbonTally V3 (canonical)
Version: 1.0
Status: PLAN (read-only — nothing deleted or modified)
Created: 2026-08-15
Author: Cline
Aligned With: docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md
---

# CarbonTally V3 — Conformity & Legacy Elimination Plan

> Plan only. No application code was modified and nothing was deleted during this phase. Every classification below is a recommendation awaiting review/approval before any deletion.

Labels used: **V3** (canonical/retain), **LEGACY** (not authoritative), **MIGRATE** (needed by V3), **REFACTOR** (useful but needs V3 adaptation), **ARCHIVE** (reference only), **REMOVE** (obsolete/duplicate), **PROPOSED**.

Policy principle: CarbonTally V3 is the canonical product. Legacy code is source material for requirements and edge cases — it is NOT authoritative and must NOT be mechanically copied, wrapped, or preserved. Where a requirement is valid but the implementation is poor, REIMPLEMENT cleanly under V3.

## 1. V3 Canonical Architecture

**V3** target (aligned with `CarbonTally_Backend_V3_Migration_Plan_v1.0.md`, which designates the v2.1 API as the authoritative layer):

```text
One FastAPI application (single OpenAPI contract)
  api/           thin routers + auth guards + serialisation
  engines/       stateless business logic (calculation, factor matching, validation,
                 report generation, extraction, workflow, benchmarking, QC)
  domain/        immutable typed models + contracts
  data/          repositories (asyncpg over service-role pool)
  infra/         supabase client/pool, event bus, audit logger, search index, llm client, config
  core/          exceptions, config, logging, types
  auth.py        single authentication/RBAC surface
  + background workers (PROPOSED) for OCR/CSV/batch/AI/report jobs
```

- Frontend and admin are V3 products built against this single API; they are reference material, not authorities.
- The authoritative workflow: `UPLOAD → EXTRACTION → MAPPING → FACTOR MATCHING → CALCULATION → VALIDATION → REVIEW → VERIFICATION → QC → REPORT → EXPORT`.
- The frontend must never implement authoritative calculation or factor matching.

## 2. Legacy Modules Inventory

Inventory of the current `backend/` tree with classification (details in §4–§7):

| Module / path | Role | Classification |
|---|---|---|
| `main.py` (+ `routes/`, `routes/admin/`, `routes/organizations/`) | live legacy monolith | **LEGACY** — required for transition; reimplement/retire per §4 |
| `main_v2.py` | v2.1 entrypoint (create_app) | **V3** (engine layer) — integrate, not a second app |
| `api/`, `engines/`, `domain/`, `data/`, `infra/`, `core/` | v2.1 layered backend | **V3** (canonical) — review and migrate forward |
| `auth.py`, `database.py`, `config.py` | auth + Supabase access + config | **V3** (`auth.py` reused); `database.py` legacy access helper — superseded by `infra/supabase.py` + `data/*` |
| `utils/` (email, emissions, document_classifier, staff_workload, organization_utils) | shared helpers | **MIGRATE/REFACTOR** — email/workload helpers valid; emissions helpers superseded by engines |
| `report_generator.py`, `pdf_engine.py` | inline PDF/OCR | **LEGACY** — reporting moves to queued engine; OCR to worker |
| `process_emissions.py`, `glossary.py` (top-level) | scripts | **ARCHIVE** |
| `main copy.py`, `main copy 2.py` | dead monolith copies | **REMOVE** (after approval) |
| `requirements copy.txt` | duplicate | **REMOVE** |
| `routes/admin/audit_logs.py`, `routes/admin/dashboard.py`, `routes/admin/document-types.py` | stale, un-imported route modules | **ARCHIVE/REMOVE** (duplicates of admin/audit + v2.1 admin) |
| `routes/customer_verifications.py`, `routes/customer_dashboard.py`, `routes/communication.py` | stale, un-imported | **ARCHIVE/REMOVE** (verification reimplemented under V3) |
| `middleware/rate_limit.py` | unused middleware | **REFACTOR** (wire into V3 app) |
| `tests/unit/*`, `tests/integration/*` | v2.1 tests | **V3** (extend for consolidated API) |
| `backend/supabase/`, probe scripts (`_v3m12_*`, `_phase10_selfcheck.py`, `_p10diag*`) | local tooling | **ARCHIVE** |
| `verify_startup.py` | Render readiness harness | **V3** (keep) |
| `frontend/`, `admin/` | old UIs | **LEGACY reference** (rebuilt per V3 personas) |

Database: `supabase/migrations/` + `database/rc1|rc2/` + `CarbonTally_DB_Schema_V3M2.sql` are the V3 data-model baseline — do not redesign to fit legacy code.

## 3. Classification of Every Relevant Legacy Module

| Component | Original purpose | V3 needs it? | Better V3 impl? | Code quality | Tested? | Recommended action |
|---|---|---|---|---|---|---|
| `routes/` (customer + admin + org) | live API surface | Yes (transition) | Yes (v2.1 engine layer) | LOW (inline logic, JSON blobs) | NO unit tests | **REIMPLEMENT** under V3 API; keep mounted only during transition |
| `database.py` | sync service-role client | Superseded | `infra/supabase.py` + `data/*` | LOW | NO | **REMOVE** (after auth.py re-pointed) |
| `utils/emissions.py` | factor math / CSV processing | Yes (requirements) | `engines/calculation.py` + matching | LOW (hardcoded map) | NO | **REIMPLEMENT** — never the authority |
| `utils/email.py`, `utils/staff_workload.py`, `utils/organization_utils.py` | email + workload + org helpers | Yes | Same logic, typed | MEDIUM | NO | **REFACTOR** into services/repositories |
| `utils/document_classifier.py` | keyword classifier | Yes (extraction input) | `engines/ai_extraction.py` | MEDIUM | NO | **REFACTOR** (kept as fallback classifier) |
| `report_generator.py`, `pdf_engine.py` | inline PDF + OCR | Yes (reports/OCR) | queued `report_generation` + worker OCR | LOW | NO | **REIMPLEMENT** (queued, typed) |
| `routes/admin/reviews.py`, `assignments.py`, `workload.py` | review/assignment/SLA | Yes | engine-level queue | LOW–MEDIUM | NO | **REIMPLEMENT** |
| `routes/admin/audit_logs.py`, `dashboard.py`, `document-types.py` | admin views | Some | v2.1 `admin_audit` / new dashboards | LOW | NO | **ARCHIVE/REMOVE** (duplicates) |
| `routes/customer_verifications.py`, `customer_dashboard.py`, `communication.py` | customer views | Yes (verification) | new `verification` API | LOW | NO | **REIMPLEMENT** verification; rest **REMOVE** |
| `main copy.py`, `main copy 2.py` | historical monoliths | No | — | LOW | NO | **REMOVE** (git history retains) |
| `frontend/`, `admin/` | current UIs | Yes (requirements) | V3 persona UIs | MEDIUM (monolith App.js) | LOW | **REFACTOR/REBUILD** per V3 UX |

## 4. main.py Assessment

**LEGACY — not canonical.**

- Provides the live routes the current frontends call; required temporarily for migration, never as a V3 target.
- Weaknesses: inline business logic; JSON-blob results; synchronous service-role REST calls per request; calculation partly in the frontend; stale/un-imported modules; known defects (`staff.py` `Client` import, `workload.py` concatenation); duplicate route implementations (reviews vs review_history; audit vs admin_audit).
- Value to retain: endpoint inventory, business requirements, workflow semantics, customer expectations — used as the specification source for V3 reimplementation.
- **Recommendation:** freeze as transition surface; migrate capability to the V3 API layer; retire per the approved deletion plan (§15). Do not add new V3 logic to `routes/`.

## 5. main_v2.py Assessment

**V3 (canonical engine layer) — NOT automatically correct; review required.**

- `main_v2.py` is an intermediate entrypoint that is already superseded by `api/router.py::create_app()`; the migration plan already designates the v2.1 API as authoritative. It must not remain a second competing application — it becomes part of the ONE V3 app.
- Strengths: layered `core/domain/engines/data/infra`; stateless engines; reproducible calculation (SHA-256 snapshots + `verify()`); staged factor matching; validation with stable `VAL_*` codes; structured report generation; asyncpg repositories; single composition root in `api/dependencies.py`; error envelope.
- Review points before acceptance (per the quality policy): correctness tests (`tests/unit/engines`, `tests/unit/api`, `tests/integration`) must be green and cover the V3 schema assumptions (RC2/V3M*); verify each engine against the V3 database baseline; improve anything that does not conform (e.g., `page_count` stored in JSONB, `facility_id` round-tripping through `metadata`, `_SYSTEM_UUID` placeholders in `emissions_logs.py`).
- **Recommendation:** adopt as the V3 backend skeleton; fix review findings; do not preserve `main_v2.py` as an entrypoint — serve the same app through the consolidated entrypoint.

## 6. Old Frontend Assessment

**LEGACY reference — not canonical.**

- `frontend/` is a CRA 5 / React 18 / MUI v9 app; `App.js` is a ~1,945-line monolith mixing routing, business logic, a hardcoded DEFRA factor map and inline components. It is the current customer UI and documents real workflows/terminology.
- Value: landing/onboarding, upload, manual entry, document status, org management, glossary, beta/magic-link flows, realtime notifications, chat widget.
- Weaknesses: frontend-authoritative calculation; hardcoded factors; monolith structure; hardcoded Supabase URL/anon key; no multi-persona support.
- **Recommendation:** rebuild per V3 personas and UX on the consolidated API; reuse interaction patterns, not code.

## 7. Old Admin Assessment

**LEGACY reference — not canonical.**

- `admin/` is a structured CRA app (React 18, Tailwind, TanStack Query, chart.js) with admin + staff pages (Reviews, ManualReviewQueue, StaffReviewQueue, WorkHub, Users, Organizations, DefraFactors, Analytics, LogViewer, Assignments, etc.) and an `AuthContext` + `RealtimeContext`.
- Value: review/assignment/SLA interaction model, staff dashboards, factor management, audit/log viewers — the specification for the V3 operations persona.
- **Recommendation:** refactor/replace to conform to V3 roles (Super Admin, Operations Manager, Data Entry Operator, Reviewer, QC Operator, Support) and V3 workflows; keep functionality that V3 requires.

## 8. Duplicate Functionality

| Capability | Copies found | Resolution |
|---|---|---|
| App factories | `main.py`, `api/router.py::create_app`, plus dead `main copy.py` / `main copy 2.py` | ONE V3 app; **REMOVE** copies |
| Calculation | `App.js` hardcoded map, `utils/emissions.py`, `process_emissions.py`, `engines/calculation.py` | **V3** engine only; **REMOVE** the rest |
| Factor matching | `utils/emissions.py` lookup vs `engines/factor_matching.py` pipeline | **V3** engine only |
| Validation | `utils/emissions.py` informal checks vs `engines/validation.py` (`VAL_*`) | **V3** engine only |
| Reporting | `routes/reports.py` + `report_generator.py` (FPDF) vs `engines/report_generation.py` + `data/reports.py` | **V3** queued engine only |
| Audit | `routes/admin/audit.py`, stale `audit_logs.py`, v2.1 `api/admin_audit.py` + `data/audit.py` | **V3** audit API + repository only |
| Review routes | `reviews.py` vs `review_history.py` prefix overlap | consolidate under V3 review API |
| Customer verification | `customer_documents.py` endpoints vs stale `customer_verifications.py` | **V3** verification API only |
| Database access | `database.py` (sync REST) vs `infra/supabase.py` (pool) + `data/*` | **V3** repository layer only |
| Document classifier | `utils/document_classifier.py` vs `engines/ai_extraction.py` | retain classifier as fallback (REFACTOR) |

## 9. Functionality Worth Migrating (MIGRATE / REIMPLEMENT)

1. Upload, batch, documents, files, org, members, assets, facilities, exports (requirements) → V3 API on the repository layer.
2. Review queue + assignment + workload/SLA → V3 queue engine (reuse `manual_review_queue`).
3. Customer verification (approve/reject/correct) → V3 verification pipeline.
4. Email notifications (`utils/email.py`, `routes/notifications.py`) → V3 notification service (Resend).
5. Realtime document status → V3 events + Supabase Realtime.
6. Glossary, reference data, waitlist, beta, feedback → V3 simple CRUD.
7. Audit trail → V3 `AuditRepository` + `admin_audit` API.
8. Factor admin (DEFRA) + importers → v2.1 `admin_imports` / `admin_providers` + provider plugins.

## 10. Functionality That Should Be Removed (REMOVE — after approval)

- `main copy.py`, `main copy 2.py`, `requirements copy.txt`, top-level probe/scratch files (`_v3m12_*`, `_phase10_selfcheck.py`, `_p10diag*`, `import9c.txt`, `pycheck9c/d.txt`, `_cf_verify.txt`, `tmp_*.txt`, `current_project_structure.txt`).
- `database.py` (superseded by `infra/supabase.py` + `data/*`) after `auth.py` re-pointing.
- Hardcoded frontend DEFRA factor map and frontend calculation code once `/api/v3/calculate` exists.
- Stale route modules once their capability is reimplemented: `customer_verifications.py`, `customer_dashboard.py`, `communication.py`, `admin/audit_logs.py`, `admin/document-types.py` (and `admin/dashboard.py` if superseded).
- Duplicate legacy engines: `utils/emissions.py` (replaced), `report_generator.py`/`pdf_engine.py` (replaced by queued reporting + worker OCR).

## 11. Functionality That Should Be Archived (ARCHIVE)

- `process_emissions.py`, `glossary.py` (top-level scripts), `backend/supabase/` local stack config, `pdf_engine.py` (OCR reference), `main copy*.py` are retained in git history anyway; if offline copies are wanted, move to a clearly non-runtime `archive/` directory.
- `current_project_structure.txt`, `create_admin_dashboard.py` — historical reference only.
- The old `frontend/` and `admin/` remain as reference until their V3 replacements are delivered; then archive.

## 12. Proposed V3 Directory / Application Structure

**PROPOSED** canonical layout (single application):

```text
backend/
  main.py                # single entrypoint (includes api.router + transition mount of legacy routes)
  auth.py                # unified auth/RBAC
  api/                   # thin V3 routers (v3/*), dependencies, contracts, middleware
  engines/               # stateless business logic (+ new qc engine, manual-extraction engine)
  domain/                # immutable models (+ verification, qc, span models)
  data/                  # repositories (+ consultants, manual_extraction, qc, suppliers)
  infra/                 # supabase, event bus, audit, search, llm, config, workers (new)
  core/                  # exceptions, config, logging, types
  tests/unit|integration
  (legacy routes/ kept only during transition, then removed)
frontend/                # V3 customer UI (rebuilt)
admin/                   # V3 operations UI (rebuilt per personas)
```

## 13. API Consolidation Plan

**PROPOSED.** One FastAPI application exposing one OpenAPI contract:

- Keep `/api/v2/*` and `/api/v3/*` (engine endpoints, customer-factors, issues, entities) mounted — they are V3.
- Add `/api/v3/*` for: auth/profile, organizations, members, documents, uploads, batches, extractions, factor-match, calculate, validate, verifications, reports, exports, suppliers, facilities, assets, consultants (firm/team/clients/tasks), processing-entities, manual-extraction, review, QC, staff, assignments, SLA, performance, notifications, admin, system.
- Legacy `/api/*` (main.py routes) remain mounted **only during migration** for frontend compatibility; they are transitional, not architectural. Remove per §15 once re-pointed.
- Frontend must consume only `/api/v3/*` and never calculate authoritatively.

## 14. Database Compatibility Assessment

**V3 baseline (do not redesign):** `supabase/migrations/` + `database/rc1|rc2/` + `CarbonTally_DB_Schema_V3M2.sql`.

- Compatible with V3: `emission_factors`, `factor_aliases`, `customer_factors`, `issues`, `consultant_*`, `processing_entities`, `manual_extraction_*`, `suppliers`, `report_generation_queue`, `emissions_logs`, `manual_review_queue`, `staff_profiles`, `organization_members`, RLS helpers (`is_org_member`, `is_org_consultant`).
- Legacy assumptions to drop (do NOT reintroduce structures): the legacy routes' reliance on sync REST + JSON blobs; frontend-side factor math; `_SYSTEM_UUID` placeholder writes in `data/emissions_logs.py` (needs a real actor column policy); `facility_id` round-tripping via `metadata` (confirm column addition if needed).
- **PROPOSED additive migrations (require explicit approval):** QC review table (or QC status on `manual_review_queue`), extraction span/coordinate table (Phase-2 split-screen), generic `processing_jobs` table for async workers. All additive and backward-compatible.

## 15. Deletion Plan

> Nothing is deleted until this plan is reviewed and approved. Deletions are executed only after the replacement capability is verified in V3.

| File/module | Purpose | Why obsolete | Replacement | Dependencies | Tests affected | Risk | Action |
|---|---|---|---|---|---|---|---|
| `main copy.py`, `main copy 2.py` | historical monoliths | dead, not imported | git history | none | none | low | **REMOVE** |
| `requirements copy.txt` | duplicate deps | duplicate | `requirements.txt` | none | none | low | **REMOVE** |
| `database.py` | sync REST client | superseded by `infra/supabase.py` + `data/*` | V3 repositories | `auth.py`, `routes/*` (until re-pointed) | legacy endpoint tests | medium | **REMOVE** after re-pointing |
| `utils/emissions.py`, `process_emissions.py` | legacy calculation | superseded by engines | `engines/calculation.py` | routes/upload, org/data | none (no unit tests) | low | **REMOVE** after V3 calculate |
| `report_generator.py`, `pdf_engine.py` | inline PDF/OCR | superseded | queued reporting + worker OCR | routes/reports, upload | none | medium | **REMOVE** after replacement |
| stale routes (`customer_verifications.py`, `customer_dashboard.py`, `communication.py`, `admin/audit_logs.py`, `admin/document-types.py`, `admin/dashboard.py`) | unwired modules | duplicates of V3 surfaces | V3 APIs | none | none | low | **REMOVE** |
| probe/scratch files (`_v3m12_*`, `_phase10_selfcheck.py`, `_p10diag*`, `import9c.txt`, `pycheck9c/d.txt`, `_cf_verify.txt`, `tmp_*.txt`, `current_project_structure.txt`) | local tooling | not runtime | — | none | none | low | **REMOVE** or **ARCHIVE** |
| legacy `routes/` tree | live API | retired after migration | `/api/v3/*` | frontends (until re-pointed) | legacy endpoint tests | high | **REMOVE** last, after green V3 API + frontend switch |

## 16. Migration Plan

**PROPOSED order** (each step ends with tests green before the next):

1. **Stabilise the single app** — fix Render blockers; `main.py` mounts `api.router` alongside legacy `routes/`; one OpenAPI.
2. **Expose engine endpoints** — `/api/v2` and `/api/v3` (factor-match, calculate, validate, report, customer-factors, issues, entities) reachable from the consolidated app.
3. **Typed contracts** — introduce typed verification/result contracts; stop new JSON-blob writes.
4. **Migrate legacy capability to V3** — upload/documents/batches/orgs/members/assets/facilities/exports → repository-backed `/api/v3/*`; review/assignment/SLA → engine-backed queue; verification pipeline; notifications service.
5. **Add new V3 surfaces** — consultants, processing-entities + manual-extraction, QC, suppliers (over existing schema); async workers for OCR/CSV/batch/AI/report.
6. **Frontend re-pointing** — customer UI then admin UI move to `/api/v3/*`; remove frontend calculation.
7. **Legacy retirement** — remove transitional `routes/` and legacy helpers per §15, then verify the single V3 app.
8. **Production security phase** — RLS enforcement, MFA, credential rotation, .env hygiene.

## 17. Testing Requirements

**V3** quality gate before any legacy module is removed and before Lovable consumes the API. Priority P0 → P2.

- **P0 — correctness gates:** unit tests for `engines/calculation` (reproducibility, snapshot hash, `verify()`), `engines/factor_matching` (confidence, customer-factor precedence), `engines/validation` (issue codes, strict mode), repositories; API contract tests for `/api/v3/*`; auth/RBAC tests (`require_*` guards); org isolation tests; upload/batch/document tests; report lifecycle; regression tests for every legacy endpoint still mounted.
- **P1 — isolation & new surfaces:** consultant isolation (RLS + service-role guard behaviour), processing-company isolation, manual-extraction, QC, suppliers, verification pipeline, async job lifecycle (retry/failure), provenance (snapshot reproducibility).
- **P2 — end-to-end & quality:** E2E across customer → ops → consultant → processing-company personas; performance for bulk/batch; migration rollback; frontend re-point regression.
- Existing suites: `tests/unit/{domain,engines,api,infra}`, `tests/integration/*` (need the local Supabase stack) — extend, do not duplicate.

## 18. Risks

1. Breaking the live frontends during consolidation — mitigated by transitional mounting + re-pointing last.
2. Two apps diverging further if the single-app step is delayed.
3. v2.1 engines not yet fully verified against the V3 schema — gate acceptance on tests.
4. QC and split-screen Phase-2 need schema changes (approval + additive migrations).
5. Async workers introduce new infrastructure (queue, retry) not present today.
6. Service-role backend bypasses RLS — production-phase risk, deferred by design.
7. Large-scale deletion without review could remove something still referenced — mitigated by the §15 plan and git history.
8. `_SYSTEM_UUID` placeholder and JSONB round-trips in `data/*` need a clean actor/column policy.

## 19. Decisions Requiring Approval

| # | Decision | Options | Recommended | Reason | Impact |
|---|---|---|---|---|---|
| D1 | Canonical backend | keep `main.py` / keep `main_v2.py` / **ONE V3 app** | ONE V3 app (v2.1 layer + migrated routes) | conforms to the migration plan; single OpenAPI | foundation |
| D2 | `main_v2.py` fate | keep as entrypoint / integrate / archive | integrate into the single app; archive the file | no second competing app | low |
| D3 | Legacy `routes/` | keep indefinitely / transitional mount then remove | transitional mount, then remove (step 7) | avoids frontend breakage | high if rushed |
| D4 | Legacy calculation + factor map | keep / reimplement only | reimplement on engines; remove frontend map | frontend never authoritative | medium |
| D5 | Deletions in §15 | approve whole / per-module | per-module, after replacement verified | safe elimination | low–high |
| D6 | QC schema | reuse `manual_review_queue` / new `qc_reviews` | new QC stage/table | QC needs distinct checklist+scoring | migration |
| D7 | Split-screen spans | JSONB / new `extraction_spans` table | new table (Phase 2) | queryable + versioned | migration |
| D8 | Async workers | Supabase job table / Redis-RQ | Supabase-backed `processing_jobs` | no new infra | migration |
| D9 | Production security | defer / now | defer to post-functional phase | stated policy | low |

> Nothing in this plan is executed until D1–D9 are reviewed and approved.






