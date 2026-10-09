# CT-READINESS-02 Phase A — Real Investor & Customer Readiness Baseline

- **Task ID:** CT-READINESS-02-20260927-PHASE-A-REAL-READINESS-BASELINE-INDEPENDENT-VERIFICATION
- **Nature:** INDEPENDENT READ-ONLY AUDIT — factual baseline only. No fixes, no code/schema/migration/config/test change, no deploy, no push, no commit.
- **Date:** 2026-09-27
- **Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
- **HEAD (local) == GitHub `p8-release-reconciled` (`github` remote):** `cb70fd6bbbcf7f0d780a3624a1686cc7d6db3d8ea`
- **Full report (33 sections):** [`CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md`](CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md)
- **Final verdict:** `CT_READINESS_02_PHASE_A_BASELINE_INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS`

---

## 1. Purpose

Establish the **real, evidenced** readiness baseline of the canonical CarbonTally platform before investor/customer-readiness implementation (Phase B) begins. Prior percentages were treated as claims only and were **not** reproduced.

## 2. Method (what was actually executed)

| Evidence class | Executed |
| --- | --- |
| Route introspection | `api.router.create_app()` → `openapi()`: **332 paths (315 under `/api/v3`)** |
| Backend unit tests | **executed** (`backend/tests/unit`, 233 files) |
| Backend e2e tests | **executed** (in-memory world) |
| Frontend jest | **executed** (targeted sample) |
| Database | **read-only** catalog + aggregate `SELECT` on configured local DB `ct_local_93d5cdd` (port 54426): 135 public tables |
| Config | `.env` **key names only**; listening-port/process probe |
| Code tracing | domain / services / engines / api headers and routes |
| Live app / browser E2E | **NOT executed** — no `:8000`/`:3000` services, no credentials |
| Integration/RLS suites | **NOT executed** — destructive `TRUNCATE … CASCADE` (AGENTS §55.1) |

## 3. The core answer

> **"If an investor or a real customer interacted with CarbonTally today, what can they actually accomplish end-to-end?"**

At HEAD `cb70fd6`, **every journey stage exists as route + UI + backend + schema**, but **nothing is end-to-end verified in the audited environment**, because:

- the canonical local DB (`ct_local_93d5cdd`) contains **no pipeline data** — `emission_factors=0`, `suppliers=0`, `customer_documents=0`, `calculation_snapshots=0`, `emissions_logs=0`, `evidence_line_items=0`, `report_versions=0`, `disclosure_requirement_versions=0`; and
- no live stack or credentials were available to exercise authentication, RLS, calculation or reporting.

**What works (verified present):** the customer workspace shell and all core routes; the fail-closed server-authoritative workspace resolver (`/api/v3/me/context`); a durable, resumable, idempotent automatic-processing pipeline; a single canonical calculation engine with strict Scope 2 (method never inferred) and unified Scope 3 (15-category taxonomy with honest status) semantics; a fail-closed, tenant-free capability truth surface; a six-state report lifecycle; an organisation-scoped supplier resolver that refuses cross-tenant candidates.

**What does not currently work / cannot be shown:** a credible investor demonstration (no corpus, no factors, no results, no reports, capability surface returns 503 locally); a verified real-customer end-to-end workflow (workspace resolution is configurably broken; manual review is entitlement-gated and its e2e suite is red); and a green regression suite (9 unit + 20 e2e + 1 frontend failures at HEAD).

## 4. Journey baseline (stage → highest evidence reached)

| Stage | Route/Endpoint | Persistence | Highest evidence | Class |
| --- | --- | --- | --- | --- |
| Authentication | `/login`, `/auth/callback` | Supabase auth | code-traced | C |
| Workspace load | `GET /api/v3/me/context` | memberships | ROUTE-VERIFIED + unit | B (config-blocked locally) |
| Org/tenant context | `/home`, `/organization` | 25 orgs | DB-OBSERVED | B |
| Supplier management | `/organization` (tab) | 0 rows | code-traced | C |
| Upload/storage | `/documents` | 0 rows | code-traced | C |
| Extraction | `/processing/:id` | schema | UNIT-EXECUTED (3 FAIL) | C |
| Mapping/factors | `/processing/:id` | 0 factors | DB-OBSERVED | C |
| Validation | `/issues` | 3 issues | code-traced | B |
| Manual review | `/review/:id` | 0 rows | E2E-EXECUTED (20 FAIL) | C |
| Calculation | `POST /api/v3/scope2|3/calculate` | 0 snapshots | code-traced | B |
| Evidence | `/evidence/line-items/:id` | 0 rows | code-traced | B |
| Reporting | `/reports/:id` | 0 rows | ROUTE-VERIFIED | B/C |

## 5. Scope 3 category matrix (authoritative status → verification status)

Authoritative status from `backend/domain/scope3.py`: `SUPPORTED [3,4,5,6]`, `PARTIAL [1,7,8,9,12,13]`, `DEFERRED [11,14,15]`, `NOT_IMPLEMENTED [2,10]`. The unified service **raises** for non-supported categories.

| # | Category | Status |
| --- | --- | --- |
| 1 | Purchased goods & services | PARTIALLY VERIFIED |
| 2 | Capital goods | NOT IMPLEMENTED |
| 3 | Fuel- & energy-related activities | CODE-ONLY |
| 4 | Upstream transport & distribution | CODE-ONLY |
| 5 | Waste generated in operations | CODE-ONLY |
| 6 | Business travel | CODE-ONLY |
| 7 | Employee commuting | PARTIALLY VERIFIED |
| 8 | Upstream leased assets | PARTIALLY VERIFIED |
| 9 | Downstream transport & distribution | PARTIALLY VERIFIED |
| 10 | Processing of sold products | NOT IMPLEMENTED |
| 11 | Use of sold products | NOT IMPLEMENTED |
| 12 | End-of-life of sold products | PARTIALLY VERIFIED |
| 13 | Downstream leased assets | PARTIALLY VERIFIED |
| 14 | Franchises | NOT IMPLEMENTED |
| 15 | Investments | NOT IMPLEMENTED |

**No category reached `VERIFIED E2E`** — persistence runtime tests were not executed and the canonical DB holds 0 snapshots.

## 6. Investor / customer scorecard (no overall winner)

| Domain | Status | Primary blocker |
| --- | --- | --- |
| Architecture / governance | B | dependency drift; e2e suite red |
| Core accounting engine | B | no executed persistence test |
| Factor governance | B | 0 factors loaded |
| Supplier / attribution | C | no rows; no E2E |
| Evidence / provenance | B | 0 rows |
| Scope 1 | B | no live run |
| Scope 2 | B | no live run |
| Scope 3 framework | B | category E2E gaps |
| Scope 3 actual category E2E | C/D | 5 categories unimplemented |
| Capability truth surface | B | catalogue not provisioned → 503 |
| Demo data / canonical corpus | D | DB empty; corpus + identity manifest absent |
| Full investor journey | C | prior-env browser evidence only |
| Customer-ready E2E workflows | C | no live stack/credentials |
| Consultant workflows | C | entitlement-gate e2e failures |
| Admin / operations | B/C | admin gated by build config |
| Reporting | B/C | 0 report rows |
| Insight | B | LLM narration dependency absent |
| Security / tenant isolation | U/C | RLS suites not executed |
| Independent verification | B | live runtime absent |

## 7. Executed-test results at HEAD (summary)

- **Backend unit:** 9 FAILED — 3 `test_review_sla_surfaces` (FastAPI lazy-`_IncludedRouter` route-enumeration drift; OpenAPI still registers 332 paths), 3 migration "latest/ordering" assertions broken by newer migrations, 3 `test_extraction_suggestions` (date-format / empty-suggestion contract drift).
- **Backend e2e (in-memory):** 20 FAILED — **one cause:** 403 `Manual processing is not enabled for this organisation` (consultant review/QC/approval/notification/deeplink/deny/invariant workflows).
- **Frontend jest (sampled):** 1 FAILED / 5 PASSED — DR-007 Issue-3 "Mapped activity" display regression persists at HEAD; evidence-trail passes.
- **Integration + live E2E:** NOT EXECUTED (safety-restricted / dependency-blocked).

## 8. Database baseline (DB-OBSERVED)

`ct_local_93d5cdd` — 135 public tables. Populated: 25 organisations, 16 memberships, 658 `users`, 5 staff profiles, 3 consultant profiles, 3 consultant clients, 7 processing entities, 3 issues, 5 customer factors, 3 disclosure frameworks. **Empty:** emission_factors, suppliers, customer_documents, organization_files, calculation_snapshots, emissions_logs, evidence_line_items, report_versions, report_generation_queue, assets, facilities, vehicles, disclosure_framework_versions, disclosure_requirement_versions. **No migration ledger** (`supabase_migrations` absent); 89 repo migrations with 14 outstanding (≥ `20261001`).

## 9. Confirmed configuration findings

1. **Workspace-load failure is config-induced locally:** backend `SUPABASE_URL=http://127.0.0.1:19999` — **port not listening** (only 8888/54423/54425/54426). Login succeeds, `/api/v3/me/context` cannot validate the token → the "Failed to load your workspace" state. The frontend additionally **hardcodes a remote Supabase default**, so client and server Supabase instances can diverge.
2. **CI migration-drift gate is defective:** `.github/workflows/migration-drift.yml:47` uses `if: ${{ secrets.MIGRATION_DRIFT_DATABASE_URL != '' }}` — `secrets` is not a valid `if:` context; the gate cannot run (independently corroborated by sibling audit `actionlint` evidence).
3. **Admin is intentionally config-gated:** `admin/` renders `AdminConfigNotice` (not the dashboard) when `REACT_APP_SUPABASE_URL`/`ANON_KEY` are absent.
4. **Package/toolchain drift:** installed `fastapi 0.141.1` / `starlette 1.6.0` / `pydantic 2.13.5` vs pinned root `fastapi==0.109.0`; `backend/requirements.txt` uses `>=`. This explains the route-enumeration test failures.

## 10. Critical-path blockers

**A. Credible investor demo:** (1) canonical DB has no pipeline data *(BOTH)*; (2) capability surface returns 503 *(INVESTOR)*; (3) no corpus + no identity manifest *(INVESTOR)*; (4) no report to show *(INVESTOR)*; (5) consultant-workflow e2e red *(BOTH)*.

**B. Credible real-customer workflow:** (1) authentication/workspace Supabase configuration *(BOTH)*; (2) migration drift + missing P17 objects/seed rows *(BOTH)*; (3) no factors loaded *(CUSTOMER)*; (4) manual-processing entitlement gate *(CUSTOMER)*; (5) frontend & extraction test drifts *(CUSTOMER)*; (6) no live end-to-end verification path *(CUSTOMER)*.

**Not a blocker (code-level):** Scope 2 method discipline, supplier fail-closed resolution, capability fail-closed design, report-lifecycle vocabulary.

## 11. Safety verification

Read-only throughout: no source/migration/SQL/RLS/test/config edit; no deploy/push/commit/merge/rebase/reset/stash; no file delete/rename; no production contact; DB access limited to `SELECT`; integration (destructive) suite not run. Only the two mandated documents were created by this task. One local secret value was inadvertently surfaced in an early masked-config probe; it is not reproduced here and was not stored (recommend rotation if non-local). Sibling `CT-PO-CT-READINESS-01-*` files appeared during the session and were **not** authored by this task.

## 12. Baseline conclusion

**CarbonTally is NOT investor-ready and NOT customer-ready at HEAD `cb70fd6`.** Architecturally and code-wise the full journey is present, but it is **not demonstrable** on the canonical environment and is **not end-to-end verified**. Phase B should proceed in the dependency order in §31 of the full report — environment/identity configuration → schema/migration baseline → corpus & factors → entitlement gate → green suites → pipeline E2E → reporting/evidence → capability provisioning → Scope breadth → consultant/admin → polish.
