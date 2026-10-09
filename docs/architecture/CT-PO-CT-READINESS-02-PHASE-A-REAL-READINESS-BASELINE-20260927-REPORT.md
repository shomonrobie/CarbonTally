# CT-READINESS-02 Phase A — Real Investor & Customer Readiness Baseline (INDEPENDENT VERIFICATION REPORT)

- **Task ID:** CT-READINESS-02-20260927-PHASE-A-REAL-READINESS-BASELINE-INDEPENDENT-VERIFICATION
- **Nature:** INDEPENDENT, READ-ONLY audit. No implementation, no fix, no source/schema/migration/config change, no deploy, no push, no commit.
- **Date:** 2026-09-27
- **Repository:** `/home/shomonrobie/ct_93d5cdd`
- **Branch:** `p8-release-reconciled`
- **HEAD (local):** `cb70fd6bbbcf7f0d780a3624a1686cc7d6db3d8ea`
- **GitHub `p8-release-reconciled` (authoritative `github` remote):** `cb70fd6bbbcf7f0d780a3624a1686cc7d6db3d8ea`
- **Companion baseline document:** [`CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md`](CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md)
- **Env labels used:** `CODE-TRACED` · `ROUTE-VERIFIED` · `UNIT-EXECUTED` · `E2E-EXECUTED` · `FRONTEND-EXECUTED` · `DB-OBSERVED` · `CONFIG-OBSERVED` · `PRIOR-EVIDENCE` · `NOT-VERIFIED`

---

## 1. Task identity

Independent verification of the **factual current readiness baseline** of the canonical CarbonTally platform at HEAD `cb70fd6`, answering:

> "If an investor or real customer interacted with CarbonTally today, what can they actually accomplish end-to-end, what can they not, and what remains unverified?"

Prior readiness percentages (Architecture ~95%, Scope 2 ~70%, Full investor journey ~40%, etc.) were treated as **claims only** and were not reproduced. This report establishes measured state.

## 2. Safety boundary

Performed strictly read-only: repository inspection, route/OpenAPI introspection, unit/e2e/frontend **test execution**, and read-only `SELECT` catalog queries against the configured local DB. Not performed: source/schema/migration/SQL/RLS/test/config/.env edits, deploy, push, commit, merge, rebase, reset, stash, file delete/rename, production or production-DB contact, record creation, adversarial security probing.

**§55.1 restatement (carried forward, required):** the project integration harness (`backend/tests/integration/conftest.py`) performs destructive setup (`TRUNCATE … RESTART IDENTITY CASCADE`). The harness must **never** target a persistent environment whose data matters (persistent QA, investor demo, production, or any authoritative data-bearing environment); integration suites must target a disposable clone (`ct_*`) or `carbontally_test`. The fixture enforces this in code, refusing targets whose name matches `qa`/`demo`/`investor`/`prod`/`live` (or the forbidden main DBs) with an explicit `F-046-1` error before any destructive statement executes. **This audit did not run the integration harness and did not set `INTEGRATION_DATABASE_URL`.**

## 3. Repository identity

| Item | Value | Evidence |
| --- | --- | --- |
| Repository root | `/home/shomonrobie/ct_93d5cdd` | `git rev-parse --show-toplevel` |
| Branch | `p8-release-reconciled` | `git rev-parse --abbrev-ref HEAD` |
| Local HEAD | `cb70fd6bbbcf7f0d780a3624a1686cc7d6db3d8ea` | `git rev-parse HEAD` |
| GitHub HEAD (`github` remote) | `cb70fd6bbbcf7f0d780a3624a1686cc7d6db3d8ea` | `git ls-remote github refs/heads/p8-release-reconciled` |
| Local vs GitHub | **AGREE** | SHA equality |
| `github` remote | `https://github.com/shomonrobie/CarbonTally.git` | `git remote -v` |
| `origin` remote | `/tmp/ct_step2` (local, **not** GitHub) | `git remote -v` |
| Tracked modifications | `M .gitignore` (pre-existing) | `git diff --name-status` |
| Staged changes | none | `git diff --cached --name-status` |
| Untracked entries | 34 (pre-existing) | `git status --porcelain` |

**Note (independence / safety):** a sibling audit document `CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927.md` (+ its `-REPORT.md`) appeared in the workspace during this session and was **not** created by this task. Its two key claims were independently re-measured here (§5, §25) and corroborated; it is treated as an evidence source, not authority.

## 4. Evidence methodology

Truth ladder applied: `DOCUMENTED ≠ CODE EXISTS ≠ ROUTE WIRED ≠ AVAILABLE ≠ PERSISTED ≠ E2E VERIFIED ≠ INDEPENDENTLY VERIFIED ≠ PRODUCTION READY`.

Methods actually executed:
1. **Repository/route introspection** — `api.router.create_app()` built; `app.openapi()` enumerated (`OPENAPI`: 332 paths total, 315 under `/api/v3`).
2. **Test execution** — backend `tests/unit` (executed), backend `tests/e2e` in-memory world (executed), frontend `react-scripts test` (executed, targeted).
3. **Read-only DB catalog/aggregate queries** — connected to the configured local DB (`ct_local_93d5cdd`, port 54426): table inventory (135 public tables) and key row counts.
4. **Config observation** — `.env` **key names only** (values never printed); listening-port/process probe.
5. **Static code tracing** — domain/service/engine/api headers and route definitions.
6. **Prior report cross-checks** — `docs/demo-investor/DR-00x`, `CT-PO-CT-READINESS-01`, `CT-PO-P17-*` used as hints and re-verified where possible.

Environment was **not** a live stack: no backend API (`:8000`) and no frontend dev server (`:3000`) were running.

## 5. Customer journey definition and stage-by-stage baseline

Journey traced: CUSTOMER → Authentication → Workspace load → Org/tenant context → Supplier management → Document upload/storage → Extraction → Supplier resolution → Mapping → Validation → Review → Customer approval → Calculation → Evidence/provenance → Emissions result → Reporting → Customer-visible output.

| Stage | Route | UI | Backend | DB persistence | Authz | Test | E2E verified | Recovery | Class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Authentication | `/login`, `/auth/callback` | yes | Supabase auth | `users`/`auth` | n/a | — | NOT-VERIFIED | partial | C |
| Workspace load | `/api/v3/me/context` | yes | yes | reads memberships | token required | unit | NOT-VERIFIED | fail-closed | B (config-blocked locally) |
| Org/tenant context | `/home`, `/organization` | yes | yes | 25 orgs | RLS + API | integration (not run) | NOT-VERIFIED | — | B |
| Supplier mgmt | `/organization` (Suppliers tab) | yes | `v3_suppliers.py` | `suppliers`=0 | org-scoped | unit | NOT-VERIFIED | fail-closed | C |
| Upload/storage | `/documents` | yes | `v3_documents.py` | `customer_documents`=0 | org-scoped | unit | NOT-VERIFIED | partial | C |
| Extraction | `/processing`, `/processing/:itemId` | yes | `automatic_extraction.py` | `manual_extraction_items` | org-scoped | 3 unit FAIL | NOT-VERIFIED | yes | C |
| Supplier resolution | — | in workspace | `supplier_resolution.py` | `suppliers` | org-scoped | unit PASS | NOT-VERIFIED | fail-closed | B |
| Mapping/factors | `/processing/:itemId` | yes | `factor_matching.py` | `emission_factors`=0 | org-scoped | unit PASS | NOT-VERIFIED | manual-review | C (no factors loaded) |
| Validation | `/issues` | yes | `validation.py` | `issues`=3 | org-scoped | unit | NOT-VERIFIED | — | B |
| Manual review | `/review`, `/review/:itemId` | yes | `v3_review.py` | `manual_review_queue`=0 | entitlement-gated | 20 e2e FAIL | NOT-VERIFIED | yes | C |
| Customer approval | `/review/:itemId` | yes | review workflow | `approval_*` | customer role | e2e FAIL | NOT-VERIFIED | — | C |
| Calculation | `/processing/:itemId` | yes | `engines/calculation.py` | `calculation_snapshots`=0 | org-scoped | integration (not run) | NOT-VERIFIED | idempotent | B |
| Evidence/provenance | `/evidence/line-items/:id` | yes | `v3_evidence.py` | `evidence_line_items`=0 | re-auth on read | unit | NOT-VERIFIED | — | B |
| Emissions result | `/emissions` | yes | `v3_emissions.py` | `emissions_logs`=0 | org-scoped | integration (not run) | NOT-VERIFIED | — | B |
| Reporting | `/reports`, `/reports/:id` | yes | `v3_reports.py`/`v3_reporting.py` | `report_versions`=0 | org-scoped | integration (not run) | NOT-VERIFIED | lifecycle | B/C |
| Customer output | `/reports/:id` | yes | disclosure/artefact | 0 rows | org-scoped | — | NOT-VERIFIED | — | C |

**Baseline conclusion:** every stage exists as route + UI + backend + schema. **None** is end-to-end verified in the audited environment because (a) the canonical local DB carries **no pipeline data** and (b) no live stack was running. Classes are therefore dominated by **B/C (implemented, workflow-not-verified)**.

## 6. Authentication / workspace

- Frontend lands post-login via [`goToWorkspace`](../ct_93d5cdd/frontend/src/v3/api.js:140) → [`resolvePostLoginPath`](../ct_93d5cdd/frontend/src/v3/api.js:130) → `GET /api/v3/me/context` (fail-closed: an API/network failure **throws**, never routes to `/onboarding`).
- Backend [`me_context`](../ct_93d5cdd/backend/api/v3_context.py:33): precedence staff → entity-staff → consultant → customer org member → new-user; a resolution failure raises HTTP 500 (never "new user"). Route present in OpenAPI.
- **Google/Gmail login → "Failed to load your workspace":** the string lives in [`AuthCallback.js:43`](../ct_93d5cdd/frontend/src/AuthCallback.js:43) and [`Login.js:45`](../ct_93d5cdd/frontend/src/Login.js:45), each emitted when `goToWorkspace()` rejects.
- **New, independent root-cause candidate (CONFIG-OBSERVED):** `backend/.env` `SUPABASE_URL=http://127.0.0.1:19999` — **port 19999 is NOT listening** (only `8888`, `54423`, `54425`, `54426` listen). Backend token validation against Supabase would therefore fail → `/me/context` 500 → the workspace error. Additionally, `frontend/src/supabaseClient.js` **hardcodes a remote Supabase default** (`REACT_APP_SUPABASE_URL || 'https://<project>.supabase.co'`) so frontend and backend can point at different Supabase instances → session accepted client-side but rejected server-side.
- **AUTHENTICATION E2E = NOT VERIFIED** (no credentials; services not started). The failure is reproducible **by configuration** but was **not** reproduced over HTTP.

## 7. Supplier management

- Domain [`supplier_resolution.py`](../ct_93d5cdd/backend/engines/supplier_resolution.py:1): org-scoped, pure/deterministic, fail-closed — `exact` only auto-persists; two candidates within margin → `ambiguous` (operator); none → `confirm_creation`; blank → `unresolved`; a candidate from another org → `cross_tenant_candidate` rejected.
- API `backend/api/v3_suppliers.py` exists; table `suppliers` exists but **0 rows** locally.
- UI: no `/suppliers` route — supplier management is the `SuppliersTab` under `/organization` (docs reference `/documents/:id` absent; `/suppliers` absent — both `PO DECISION REQUIRED` if a dedicated surface is wanted).
- **Class: C** (code exists, workflow not verified).

## 8. Document ingestion

- Routes `/documents` (list/inline), `backend/api/v3_documents.py`; storage via `backend/services/storage.py`. `customer_documents=0`, `organization_files=0`.
- Canonical corpus: `docs/sample_bills/` holds **8 PDFs** (Scope 1/2/3 samples, incl. `uk_waste_transfer_note.pdf`). "Robinsons Recycling Services Ltd" appears only in P12 tests/artefacts — **not** as corpus files in this repo. No `DEMO_IDENTITIES.md` exists at the AGENTS §54 path `tools/seed_investor_demo/DEMO_IDENTITIES.md` (corpus/identity manifest **absent**).
- **Class: C.**

## 9. Extraction

- [`automatic_extraction.py`](../ct_93d5cdd/backend/services/automatic_extraction.py:1): PDF via `pdfplumber` → Tesseract OCR fallback; scanned PDF/image → Tesseract → **ONNX fallback** (`rapidocr_onnxruntime`) when Tesseract absent.
- Dependency import probe: `pdfplumber`, `rapidocr_onnxruntime`, `pytesseract`, `onnxruntime`, `pdf2image`, `PIL`, `numpy` = all present. `tesseract` binary **not** on PATH → ONNX path is the effective OCR route.
- Extraction pipeline [`automatic_processing.py`](../ct_93d5cdd/backend/services/automatic_processing.py:1): durable, stateless-per-job, persisted stage markers, crash-resumable, deterministic `match_request_id` (no duplicate calculations), gates on extraction confidence / factor match / blocking validation, stops at `review`.
- **Unit failures (UNIT-EXECUTED):** [`test_extraction_suggestions.py`](../ct_93d5cdd/backend/tests/unit/engines/test_extraction_suggestions.py:30) 3 tests FAIL — `suggest()` returns ISO date `2026-01-15` where the test expects `15/01/2026`, and returns non-empty `suggested_data` where the test expects `{}`. Test/behaviour drift.
- Explicit distinction: automatic extraction = code present; manual-review = entitlement-gated; successful persistence = UNVERIFIED (0 rows); customer-visible completion = UNVERIFIED.
- **Class: C.**

## 10. Mapping / factor resolution

- `backend/engines/factor_matching.py`, `factor_selection_policy.py`, `domain/factor.py`, `domain/customer_factor.py`. Customer-factor precedence and factor provenance/version handling are code-present.
- `emission_factors = 0` in the canonical local DB → mapping **cannot execute** locally. Repository seed files exist but do not equal DB population (AGENTS §12 respected).
- **Class: C** (code + governance present, no factors loaded, no E2E).

## 11. Manual review

- `manual_review_queue` table (0 rows), `v3_review.py`, `v3_manual_extraction.py`.
- **E2E evidence (E2E-EXECUTED):** the P6-2F suite returned, for consultant review/submit/QC/customer-approval/notification/deeplink/deny/invariant tests, HTTP 403 with body `{"error":{"code":"FORBIDDEN","message":"Manual processing is not enabled for this organisation. A CarbonTally administrator must enable it."}}`. **All 20 e2e failures share this single cause.** Manual review is a deliberate **entitlement-gated** controlled path; the fixture does not enable the entitlement.
- Manual review is a **controlled success path**, not a failure — but the consultant review workflow is **not verified at HEAD** in the current fixture.
- **Class: C.**

## 12. Calculation

- Canonical write path `backend/engines/calculation.py` (`CalculationRequest.from_match_result` → snapshot + emissions log).
- Scope 2 [`scope2_calculation.py`](../ct_93d5cdd/backend/services/scope2_calculation.py:1): method **never inferred** (missing method refused); market-based **never silently downgraded**; contractual-instrument eligibility + over-allocation guard.
- Scope 3 [`scope3_calculation.py`](../ct_93d5cdd/backend/services/scope3_calculation.py:1): one unified pathway for 15 categories; no per-category engine; refuses estimation labelled measured and estimated classification without an `EstimationRecord`.
- `calculation_snapshots=0`, `emissions_logs=0` locally → not executed. Integration tests exist (`test_calculation.py`, `test_p17_09_scope2_scope3_persistence_runtime.py`) but are destructive → **NOT EXECUTED**.
- **Class: B.**

## 13. Scope 1

- Scope 1 is the operational baseline; factor pathway + calculation + emissions + evidence are code-present (single canonical engine). No Scope-1-specific gap found in code beyond the general pipeline blockers. Not E2E verified locally (0 rows, no live stack).
- **Class: B.**

## 14. Scope 2

- location-based: implemented; market-based: implemented with strict instrument gating; contractual instruments: `domain/contractual_instruments.py` + `v3_scope2.py` + persistence runtime test present (not executed).
- API: `POST /api/v3/scope2/calculate`.
- **Class: B** (market-based completeness is code-present and fail-closed; not E2E verified).

## 15. Scope 3 category matrix

Authoritative status rollup from [`domain/scope3.py`](../ct_93d5cdd/backend/domain/scope3.py:9): `SUPPORTED [3,4,5,6]`, `PARTIAL [1,7,8,9,12,13]`, `DEFERRED [11,14,15]`, `NOT_IMPLEMENTED [2,10]`. The unified service **raises** (`assert_calculable`) for non-supported categories rather than inventing a number.

| # | Category | Taxonomy | Calc method | Factor pathway | Input | Validation | Persistence | Reporting | E2E test | E2E exec | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Purchased goods & services | yes | partial (bounded) | bounded | yes | yes | yes | yes | yes | no | PARTIALLY VERIFIED |
| 2 | Capital goods | yes | none (raises) | none | — | boundary | slot | — | — | no | NOT IMPLEMENTED |
| 3 | Fuel- & energy-related (FERA) | yes | yes | yes | yes | yes | yes | yes | yes | no | CODE-ONLY |
| 4 | Upstream transport & distribution | yes | yes | yes | yes | yes | yes | yes | yes | no | CODE-ONLY |
| 5 | Waste generated in operations | yes | yes | yes | yes | yes | yes | yes | yes | no | CODE-ONLY |
| 6 | Business travel | yes | yes | yes | yes | yes | yes | yes | yes | no | CODE-ONLY |
| 7 | Employee commuting | yes | partial (bounded) | bounded | yes | yes | yes | yes | yes | no | PARTIALLY VERIFIED |
| 8 | Upstream leased assets | yes | partial (bounded) | bounded | yes | yes | yes | yes | yes | no | PARTIALLY VERIFIED |
| 9 | Downstream transport & distribution | yes | partial (bounded) | bounded | yes | yes | yes | yes | yes | no | PARTIALLY VERIFIED |
| 10 | Processing of sold products | yes | none (raises) | none | — | boundary | slot | — | — | no | NOT IMPLEMENTED |
| 11 | Use of sold products | yes | none (deferred) | none | — | boundary | slot | — | — | no | NOT IMPLEMENTED |
| 12 | End-of-life of sold products | yes | partial (bounded) | bounded | yes | yes | yes | yes | yes | no | PARTIALLY VERIFIED |
| 13 | Downstream leased assets | yes | partial (bounded) | bounded | yes | yes | yes | yes | yes | no | PARTIALLY VERIFIED |
| 14 | Franchises | yes | none (deferred) | none | — | boundary | slot | — | — | no | NOT IMPLEMENTED |
| 15 | Investments | yes | none (deferred) | none | — | boundary | slot | — | — | no | NOT IMPLEMENTED |

Status vocabulary: **VERIFIED E2E** (none), **PARTIALLY VERIFIED** (1,7,8,9,12,13 — bounded pathways, tests present, not executed), **CODE-ONLY** (3,4,5,6), **NOT IMPLEMENTED** (2,10,11,14,15). No category was marked VERIFIED E2E because the persistence runtime tests were not executed and the local DB has 0 snapshots.

## 16. Evidence / provenance

- `domain/evidence.py`, `api/v3_evidence.py`; routes `/api/v3/emissions/{log_id}/evidence`, `/api/v3/evidence/line-items/{line_item_id}`; `evidence_line_items` table exists (0 rows); frontend `SourceEvidenceViewer` reachable from the workspace and from Insight (a stored evidence id is a **locator**, backend re-authorises on every read).
- Chain represented + persisted schema; **not retrievable with live data** locally. **Class: B.**

## 17. Reporting

- `domain/report.py`, `domain/report_lifecycle.py` (six ratified states: `DRAFT→REVIEWED→APPROVED→FINAL`, `CHANGES_REQUESTED`/`REJECTED`; `SUPERSEDED` derived), `domain/report_artefact.py`, `engines/report_generation.py`.
- API surface (ROUTE-VERIFIED): `/api/v3/reports`, `/reports/types`, `/reports/{id}`, `/content`, `/versions`, `/submit`, `/approve`, `/request-changes`, `/reject`, `/download`, `/finalise`, `/frozen-artefact`, `/disclosure*`, plus `/api/v3/reporting/*` (customer dashboard, emissions trend, audit-readiness, ops reporting).
- `report_versions=0`, `report_generation_queue=0` locally. Prior `DR-006/DR-007` browser evidence (different env, SHA `51716c1`) reported `READY 3` reports; **not re-verified at HEAD**.
- Distinction: report **code** is complete; a usable **reporting journey** is NOT independently verified here. **Class: B/C.**

## 18. Insight

- API `v3_insight.py`, `v3_insight_tools.py`, `v3_insight_interactions.py`; services `insight_context/query_planner/tools/interactions/rate_limit`; domain `insight*.py`. Frontend `/insight`.
- LLM use is **optional**: [`insight_interactions.py`](../ct_93d5cdd/backend/services/insight_interactions.py:70) imports `infra.llm_client.LLMClient` and has an explicit `llm_client is None` branch; narration is injected via `narration_client()`. **No LLM/OpenRouter key exists** in the environment (env key names observed: `DATABASE_URL, PORT, REACT_APP_API_URL, BROWSER, ENVIRONMENT, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, SUPABASE_JWT_SECRET, RESEND_API_KEY, FOUNDER_EMAIL`). So deterministic tools/persistence work; **LLM narration is dependency-blocked**.
- Unit Insight API tests were **not** among the failures → pass. **Class: B.**

## 19. Consultant / acting-for

- `domain/acting_for.py`, `api/v3_accounting_context.py`, `api/v3_consultants.py`, `api/consultant_auth.py`, `api/consultant_branding.py`; tables `consultant_profiles=3`, `consultant_clients=3`, `consultant_firm_members`, `consultant_tasks`.
- **E2E consultant workflow FAILED (20 tests)** due to the manual-processing entitlement gate; the ACTING-FOR write-path and provenance invariants are therefore **not verified at HEAD**. P17 architecture alone is not accepted as readiness.
- **Class: C.**

## 20. Capability truth surface

- `GET /api/v3/capabilities` implemented in [`v3_disclosure.py`](../ct_93d5cdd/backend/api/v3_disclosure.py:705). Canonical selector [`select_governed_catalogue_version`](../ct_93d5cdd/backend/api/v3_disclosure.py:753) selects by **governed identity** (not status/label); payload is **tenant-free** (no tenant param/query) and **fail-closed** (503 on absent **or** ambiguous catalogue; no partial claim).
- Pure projection [`domain/capability_catalogue.py`](../ct_93d5cdd/backend/domain/capability_catalogue.py:1) imports vocabulary from `domain.disclosure`; asserts no Axis-A tokens; `SCOPE3_CATEGORY_COUNT = 15`.
- **Independent verification of P17-M3 findings:** canonical selection = **confirmed present**; fail-closed = **confirmed**; tenant-free projection = **confirmed** (no tenant argument).
- **DB-OBSERVED blocker:** `disclosure_requirement_versions = 0` (and `disclosure_framework_versions = 0`) → the endpoint would return **503 "catalogue is not provisioned"** in the canonical local environment — i.e. the surface exists but **serves no claim locally**. Frontend `/capabilities` + `/capabilities/product` routes exist.
- **Class: B** (implemented, unit-tested, not serving locally).

## 21. Admin / operations

- Ops/PE shells: routes `/ops`, `/ops/items/:id`, `/ops/review/:id`, `/ops/qc/:id`, `/pe`, `/pe/assignments`, `/pe/messages`, `/pe/items/:entityId/:itemId`; frontend `v3/ops/*`, `v3/pe/*`; `v3_operations.py` (`/ops/sla/settings`, reporting, review assign) registered.
- Separate `admin/` CRA app: [`admin/src/supabaseClient.js`](../ct_93d5cdd/admin/src/supabaseClient.js:1) reads `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY`; when missing, [`App.js:102`](../ct_93d5cdd/admin/src/App.js:102) renders `AdminConfigNotice` instead of the dashboard (P18/H2 hardening). **Admin therefore functions only when built with Supabase config; otherwise it renders the configuration notice only.** This is the previously recorded "admin configuration" behavior, and it is **by design**, not a crash.
- **Class: B/C.**

## 22. Investor demo readiness

- **Seeded (DB-OBSERVED, `ct_local_93d5cdd`):** 25 organisations, 16 organisation memberships, 658 `users` rows, 5 `staff_profiles`, 3 `consultant_profiles`, 3 `consultant_clients`, 7 `processing_entities`, 3 `issues`, 5 `customer_factors`, 3 `disclosure_frameworks`.
- **Empty (cannot be demonstrated):** `emission_factors=0`, `suppliers=0`, `customer_documents=0`, `organization_files=0`, `calculation_snapshots=0`, `emissions_logs=0`, `evidence_line_items=0`, `report_versions=0`, `report_generation_queue=0`, `assets/facilities/vehicles=0`, `disclosure_framework_versions=0`, `disclosure_requirement_versions=0`.
- Tooling for a demo exists (`tools/demo_lab/` incl. `reset_demo_lab.sh`, `run_demo_lab.sh`, `seed_factors.py`, `p12_canonical_corpus.py`, `t3_*`), but the **canonical corpus is not loaded** into this DB and no reusable identity manifest (AGENTS §54 `DEMO_IDENTITIES.md`) is present.
- A 10-step investor demo (customer→report) **cannot currently be run from the canonical local DB**. Prior browser demo evidence exists (`docs/demo-investor/DR-004..DR-007`, 9 documents, Scope 1 result `2469.16978 kg CO2e`, `READY 3` reports) but at a **different SHA/env** → `PRIOR-EVIDENCE`, not current HEAD.
- **Class: D/C.**

## 23. Real customer readiness

- Present in code: tenant isolation model, authentication integration, authorization (RLS + server-side), workspaces, persistence, supplier management, processing pipeline, review, calculation, evidence, reporting, audit, recovery.
- **Verified:** unit suites largely pass (details §26); fail-closed guards confirmed by code.
- **Not verified:** live authentication/authorization, live RLS behaviour, live persistence, live reporting, in-workspace UX — no live stack and no credentials. Integration/RLS suites **NOT EXECUTED** (destructive). Frontend sampled test: 1 FAIL / 5 PASS.
- **Class: C.**

## 24. Security / tenant isolation

- **RLS:** 89 migration files under `supabase/migrations`; RLS integration tests exist (`test_v3_rls_behavior.py`, `verify_activity_clarifications_rls.py`) — **not executed** (destructive).
- **Fail-closed design confirmed by code:** supplier cross-tenant candidate rejection; scope-category refusal; capability 503; capability endpoint tenant-free; `me/context` fail-closed 500; evidence reads re-authorised.
- **Not performed:** adversarial/cross-tenant probing (read-only mandate). No unexpected-ALLOW was observed, and none was tested. **UNVERIFIED**, not assumed safe.

## 25. Known issue verification

| Known issue | Current status | Evidence |
| --- | --- | --- |
| Google login → "Failed to load your workspace" | **Reproducible by configuration**, not broken in code | `SUPABASE_URL` → dead port `19999`; frontend hardcoded remote default; `/me/context` fail-closed. NOT HTTP-reproduced |
| Migration drift | **CONFIRMED present** | No `supabase_migrations` ledger locally; 89 repo migrations; 14 outstanding (≥`20261001`); CI gate defect (see below) |
| CI migration-drift gate | **DEFECTIVE (CONFIRMED by inspection)** | [`.github/workflows/migration-drift.yml:47`](../ct_93d5cdd/.github/workflows/migration-drift.yml:47) uses `if: ${{ secrets.MIGRATION_DRIFT_DATABASE_URL != '' }}` — `secrets` is not a valid context in `if:`; sibling READINESS-01 reports `actionlint` rejects it (exit 1) and every sampled run failed with zero jobs |
| Admin configuration | **Present, by design** | `AdminConfigNotice` gate on missing `REACT_APP_SUPABASE_*` |
| Scope 2 market-based incompleteness | **No silent downgrade; instrument-gated** | `scope2_calculation.py`; not E2E verified |
| Scope 3 E2E gaps | **CONFIRMED** | 8 of 15 categories not SUPPORTED (2,10 NOT_IMPLEMENTED; 11,14,15 DEFERRED); no E2E executed |
| PDF extraction limitations | **Partial** | OCR via ONNX (Tesseract binary absent); 3 extraction-suggestion unit tests FAIL |
| Production migration uncertainty | **UNKNOWN** | No production DSN/evidence path |
| Reporting lifecycle | **Implemented, not E2E verified** | `report_lifecycle.py`; 0 rows locally |
| Demo reset/reseed | **Tooling present, corpus not loaded** | `tools/demo_lab/reset_demo_lab.sh`; DB empty |
| Consultant workflows | **Failing in e2e** | 20 failures, entitlement gate 403 |

## 26. End-to-end execution results

| Suite | Executed | Result |
| --- | --- | --- |
| Backend unit (`backend/tests/unit`, 233 files) | **YES** | **9 FAILED** (3 `test_review_sla_surfaces` — FastAPI lazy-include drift: `router.routes` holds `_IncludedRouter`, only `/api/v2/health` seen, yet OpenAPI registers 332 paths; 3 migration "is-latest/ordering" assertions broken by newer migrations; 3 `test_extraction_suggestions` behaviour/date-format) |
| Backend e2e in-memory (`backend/tests/e2e`) | **YES** | **20 FAILED**; all single-cause: 403 `Manual processing is not enabled for this organisation` (consultant review/QC/approval/notification/deeplink/deny/invariants) |
| Frontend jest (sampled: dr007 + evidence-trail) | **YES** | **1 FAILED / 5 PASSED** — [`dr007-investor-display-fixes.test.jsx:107`](../ct_93d5cdd/frontend/src/v3/__tests__/dr007-investor-display-fixes.test.jsx:107) "Mapped activity" did not contain "Natural gas" (DR-007 Issue-3 display regression persists at HEAD); `evidence-trail.test.jsx` PASSED |
| Backend integration (`backend/tests/integration`) | **NO — SAFETY-RESTRICTED** | Destructive `TRUNCATE … CASCADE`; §55.1. NOT EXECUTED |
| Live app / browser E2E | **NO — DEPENDENCY BLOCKED** | No `:8000`/`:3000` services; no credentials → AUTHENTICATION E2E = NOT VERIFIED |
| `qa_harness/scripts/run_all.py` | **NO** | Requires a reachable target stack (it SKIPs unreachable stages); no stack running |

**Test infrastructure sanity:** `actionlint` not on PATH here; `psql` present; backend venv Python 3.14.4 with pytest 9.1.1; installed `fastapi 0.141.1` / `starlette 1.6.0` / `pydantic 2.13.5` vs pinned root `fastapi==0.109.0` / `backend/requirements.txt fastapi>=0.109.0` — a **dependency-version drift** that directly explains the `test_review_sla_surfaces` failures (route enumeration).

## 27. Readiness classification matrix

Legend: **A** = E2E verified · **B** = implemented/partially verified · **C** = code exists, workflow not verified · **D** = architectural/documented only · **E** = not implemented · **U** = unknown.

| Capability | Class | Basis |
| --- | --- | --- |
| Architecture / governance | B | code + docs + test infra present; e2e suite not green |
| Core accounting engine | B | single canonical engine; not E2E executed |
| Factor governance | B | precedence/provenance in code; 0 factors loaded |
| Supplier / attribution | C | fail-closed resolver; no E2E; no rows |
| Evidence / provenance | B | schema + viewer + re-auth; no rows |
| Scope 1 | B | code path present; not E2E |
| Scope 2 | B | LB+MB+instruments; not E2E |
| Scope 3 framework | B | 15-cat taxonomy + status honesty + unified service |
| Scope 3 actual category E2E | C/D | 6 partial, 4 code-only, 5 not-implemented; none E2E |
| Capability truth surface | B | tenant-free + fail-closed; 503 locally (catalogue absent) |
| Demo data / canonical corpus | D/C | DB empty; corpus + identity manifest absent |
| Full investor journey | C | prior-env browser evidence only |
| Customer-ready E2E workflows | C | routes/UI/backends exist; not verified |
| Consultant workflows | C | e2e failing (entitlement gate) |
| Admin / operations | B/C | shells + tabs; admin gated by build config |
| Reporting | B/C | lifecycle + endpoints; no rows |
| Insight | B | deterministic path; LLM narration blocked |
| Security / tenant isolation | U/C | fail-closed confirmed by code; RLS not executed |
| Independent verification | B | this audit (with limitations) |

## 28. Investor / customer scorecard

Stated **without** an overall winner or marketing claim.

| Domain | STATUS | EVIDENCE | BLOCKERS | NEXT REQUIRED ACTION |
| --- | --- | --- | --- | --- |
| Architecture / governance | B | 315 v3 routes; domain/service/engine layering; 89 migrations | dep drift; e2e red | pin deps; green the suites |
| Core accounting engine | B | single write path + idempotency | no executed persistence test | run integration on disposable clone |
| Factor governance | B | precedence/factor provenance code | 0 factors loaded | load factors; verify mapping E2E |
| Supplier / attribution | C | fail-closed resolver | no rows; no E2E | seed suppliers; E2E |
| Evidence / provenance | B | schema+viewer+re-auth | 0 rows | E2E with real calc |
| Scope 1 | B | code path | no live run | E2E |
| Scope 2 | B | strict method/instrument gating | no live run | E2E market-based |
| Scope 3 framework | B | 15 cats + status + unified service | E2E gaps | category E2E for 3,4,5,6 |
| Scope 3 actual E2E | C/D | matrix §15 | 5 unimplemented | PO scope decision |
| Capability surface | B | tenant-free, fail-closed | catalogue not provisioned (503) | provision catalogue rows |
| Demo corpus | D | DB empty; manifest absent | no corpus/identities | load canonical corpus + manifest |
| Investor journey | C | prior-env evidence only | DB empty; capability 503 | rebuild demo on canonical DB |
| Customer E2E | C | routes/UI/backends | no live stack/creds | run live E2E |
| Consultant workflows | C | e2e failing | entitlement gate in fixture | fix fixture / enable entitlement |
| Admin/ops | B/C | shells + config gate | build config | configure admin build |
| Reporting | B/C | lifecycle+endpoints | 0 rows | generate + verify report |
| Insight | B | deterministic tools | no LLM key | decide narration scope |
| Security/tenancy | U/C | fail-closed code; RLS uninterrogated | no RLS run | run RLS suites on disposable clone |
| Independent verification | B | this report | live runtime absent | Phase B verification |

## 29. Critical-path blockers

**A. Credible investor demo**
1. **BOTH** — canonical local DB carries **no pipeline data** (0 factors/documents/snapshots/emissions/reports).
2. **INVESTOR** — capability surfaces would return **503** (catalogue unprovisioned) → capability pages show no claim.
3. **INVESTOR** — no canonical corpus loaded + no demo identity manifest.
4. **INVESTOR** — reporting journey yields nothing to show.
5. **BOTH** — consultant workflow e2e red (entitlement gate).

**B. Credible real-customer workflow**
1. **BOTH** — authentication/workspace configuration (backend `SUPABASE_URL` dead port; frontend/backend Supabase mismatch).
2. **BOTH** — migration drift (P17 objects/seed rows absent locally; no ledger; CI gate defective).
3. **CUSTOMER** — factor population required for mapping.
4. **CUSTOMER** — manual-processing entitlement gate blocks review workflows.
5. **CUSTOMER** — frontend display regression (dr007 Issue-3) + extraction-suggestion unit failures.
6. **CUSTOMER** — no live end-to-end verification path (services + credentials).

**NOT A BLOCKER (code-level):** Scope 2 method discipline, supplier fail-closed resolution, capability fail-closed design, report lifecycle vocabulary.

## 30. Uncertainty register

| # | Unknown | Why unknown | Impact |
| --- | --- | --- | --- |
| U1 | Production migration state | no production DSN/evidence path | release risk |
| U2 | Live OAuth (Google) end-to-end | no credentials/services | journey-entry risk |
| U3 | Live RLS behaviour / cross-tenant denial | destructive suites not run | security unknown |
| U4 | Reporting output quality | 0 rows; not run | investor deliverable unknown |
| U5 | OCR fidelity on real scans | only dependency presence checked | extraction risk |
| U6 | Admin/ops runtime rendering | build config not present | ops usability unknown |
| U7 | Whether e2e/unit failures are env-drift-only | dep versions differ from pins | may mask real regressions |
| U8 | Hosted Supabase project referenced by frontend default | out of scope (no contact) | demo/env mismatch |
| U9 | Scope 3 category E2E execution | not run | breadth unknown |
| U10 | `qa_harness` full result | requires live stack | acceptance unknown |

## 31. Recommended implementation sequence

Ordered by dependency and evidence (recommendations only; **not implemented**). Optimise for a complete, demonstrable, auditable journey — not feature count.

1. **Environment/identity truth (BOTH):** reconcile `SUPABASE_URL` (backend) and frontend Supabase config so login→workspace resolves; confirm `/api/v3/me/context` returns `/home`.
2. **Schema baseline (BOTH):** decide and apply the P17/P16R migration boundary on the canonical DB; provision the migration ledger; fix the CI drift gate (`secrets` in `if:`).
3. **Canonical corpus + identities (INVESTOR):** load the six-PDF Robinsons FY2025/FY2026 corpus and a reusable identity manifest; make reset/reseed repeatable and isolated from production.
4. **Factors (BOTH):** load governed factors so mapping/calculation can run; verify customer-factor precedence.
5. **Manual-processing entitlement (BOTH):** enable per-org grant; fix the e2e fixture so consultant review/QC/approval/notification/deeplink/invariance suites go green.
6. **Test-suite green (BOTH):** pin dependencies (or fix route introspection), reconcile migration-latest assertions, fix extraction-suggestion contract, fix dr007 Issue-3 display regression.
7. **Core pipeline E2E (BOTH):** run ingestion→extraction→mapping→validation→review→calculation→evidence on a disposable clone; record results.
8. **Reporting + evidence output (INVESTOR):** generate a real report and verify lifecycle + evidence linkage + customer-visible output.
9. **Capability catalogue provisioning (INVESTOR):** provision `disclosure_requirement_versions` so `/api/v3/capabilities` serves a governed claim instead of 503.
10. **Scope breadth (BOTH):** Scope 2 market-based + Scope 3 categories 3,4,5,6 E2E; PO decision on 2/10/11/14/15.
11. **Consultant/admin operational breadth (BOTH):** verify consultant ACTING-FOR and admin/ops with real build config.
12. **Polish:** accessibility, responsive, empty/loading states — after the journey is provably complete.

## 32. Safety verification

- No source file edited; no migration/SQL/RLS edited; no test edited; no config/`.env` edited; no deploy/push/commit/merge/rebase/reset/stash; no file deleted/renamed; no production or production-DB contact; no records created.
- DB access was **read-only** (`SELECT` catalog/aggregate queries only).
- Test runs were **non-destructive** (unit/e2e in-memory/frontend); the destructive integration harness was **not** executed.
- Only the two mandated documents were created by this task.
- **Disclosure:** during an early masked-config probe, one secret value was inadvertently surfaced in command output. It is **not** reproduced here and has not been stored; subsequent probes printed **key names only**. (Recommend rotating the affected local secret if it is not purely local.)
- Sibling audit files (`CT-PO-CT-READINESS-01-*`) appeared during the session; they were not authored by this task.

## 33. Final verdict

```
CT_READINESS_02_PHASE_A_BASELINE_INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS
```

**Rationale.** A factual baseline was independently established from executed tests, route introspection, read-only database observation and code tracing, and the core question was answered: at HEAD `cb70fd6` the platform **contains** the full journey as route + UI + backend + schema, but **nothing is end-to-end verified** in the audited environment because the canonical local DB is empty of pipeline data and no live stack/credentials were available. Limitations are explicit (no live auth/RLS/reporting, integration suite not executed, dependency drift). CarbonTally is **not** declared investor-ready or customer-ready.

**The baseline from which Phase B may begin is: architecture and code are broadly present; the binding constraints are (1) environment/identity configuration, (2) database schema/seed baseline & migration drift, (3) demo corpus + factors, (4) the manual-processing entitlement gate, and (5) a suite of test/dependency drifts (9 unit, 20 e2e, 1 frontend) that must be resolved before any readiness claim can be substantiated.**
