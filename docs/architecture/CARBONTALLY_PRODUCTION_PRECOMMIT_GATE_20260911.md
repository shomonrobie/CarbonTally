# CarbonTally — Production Pre-Commit Gate

**Prompt Ref:** `CT-PROD-PRECOMMIT-GATE-20260911-001` · **Date:** 2026-09-11
**Mode:** READ-ONLY pre-commit gate (no stage, commit, push, reset, clean, migration, DB or deploy action)
**Repository:** CarbonTally · **Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (verified — matches expectation, unchanged)
**Authorities:** Blueprint V1.3 → Roadmap V1.0 → phase decision docs → Release Manifest 20260911 → implementation/verification reports

## 1. Executive conclusion

The Release-1 boundary is **technically coherent and safe to stage**. Static verification found
**no unresolved P0 commit blocker**: the backend local-module dependency closure is complete,
the billing fix is present and schema-type-compatible, the router dependencies are proven,
secrets are provably excluded, and the P0-4 provisioning surface exists.

One correction and three Product Owner decisions remain:

* **Correction to the Release Manifest:** `admin/src/**` is the **legacy v1 admin app** (it calls
  `/api/admin/*`, `/api/organizations/*`, `/api/drafts/*`, `/api/reference/*` and uses
  `REACT_APP_API_URL || 'http://localhost:8000'`). It is **not** the P0-4 provisioning surface.
  The real v3 provisioning surface is **`frontend/src/v3/admin/**`** plus
  **`frontend/src/v3/customer/BillingPage.jsx`**, which call `/api/v3/commercial/*` and
  `/api/v3/billing/*` (routers `/api/v3/commercial` and `/api/v3/billing` confirmed, offering
  subscriptions, plans, organizations, config, payments, credits grant/adjust/refund/reverse/
  rollover and orders). Both trees are already inside the Release-1 set, so release content is
  unaffected — only the rationale changes.
* **PO decisions:** (1) whether the legacy `admin/src/**` plus its `/admin/*` Vercel route are in
  Release 1; (2) whether the 152 tracked deletions stay excluded (recommended: yes);
  (3) when live migration reconciliation occurs.

**Verdict: `PRE-COMMIT GATE — PASS WITH PO DECISIONS`.**

## 2. Git state (verified)

| Item | Value |
|---|---|
| branch | `main` |
| HEAD | `16391217103b98dcea520070c5a22c68f12fe607` — **matches expectation, unchanged since the manifest** |
| staged | **0** |
| untracked entries | **248** (247 + this gate's history file) |
| modified | **286** |
| deleted | **152** |
| unexpected changes | **none** — the only delta since the manifest is this task's documentation |

## 3. Release-1 manifest integrity (file-level verified)

Every dependency class the manifest enumerates is present at **file level**; nothing was
re-expanded into directory globs. Verified specifically:

* backend production files — enumerated in the manifest (§2/§3) and re-checked against
  `git status` here;
* **`backend/infra/ai_runtime.py`** — in the Release-1 list and confirmed imported by production
  (`backend/services/automatic_processing.py:50`,
  `backend/workers/automatic_processing.py:162`);
* router dependencies — `backend/api/router.py` imports `api.v3_pe` (line 52),
  `api.v3_context` (line 62), `api.v3_health` (line 63); support modules `pe_auth.py`,
  `processing_mode.py`, `audit_helpers.py` present;
* billing/D6/D7/D8/D11/origin/mode/consultant/PE/frontend/admin/`vercel.json`/package
  manifests/17 migrations — all present.

**No production dependency referenced by the Release-1 set is missing.**

## 4. Billing / D6 pre-commit check — **PASS**

```
backend/data/billing.py (845-856)
INSERT INTO public.usage_tracking (organization_id, usage_date, usage_month, ai_files_processed)
VALUES ($1, $2::timestamptz, date_trunc('month', $2::timestamptz)::date, $3)
```

Isolated-schema metadata (read-only `information_schema`):
`usage_tracking.usage_date = date` · `usage_tracking.usage_month = date` ·
`ai_files_processed = integer`.

`date_trunc('month', $2::timestamptz)` returns timestamptz → cast to **`date`** → matches the
column exactly; `$2::timestamptz` into a `date` column uses the standard assignment cast. Both
earlier failures (`AmbiguousFunctionError`; `usage_month is date but expression is text`) are
eliminated. D6 dependencies (`services/billing.py` +117 lines, `domain/billing.py`,
`api/v3_processing_workflow.py`, `data/tenant.py`, `database.py`) are all in the release set; no
missing imports and no production-only test dependency in the path.

**Classification: PASS.**

## 5. Migration pre-commit gate

17 migrations, repository-ordered **1 → 17** (timestamps strictly increasing, no duplicates):

```
1  20260831000000_v3m10_org_membership_unique.sql
2  20260831010000_v3m11_operational_indexes.sql
3  20260831020000_audit_activity_immutability.sql
4  20260831030000_tenant_org_id_not_null.sql
5  20260831040000_consultant_revocation_roles.sql
6  20260902020000_v1_2_dual_origin_workflow.sql
7  20260902030000_phase5_work_item_assignments.sql    ← creates public.work_item_assignments
8  20260902040000_phase5_pe_operational_messaging.sql
9  20260902050000_phase5_notification_event_key.sql   ← supplies notifications.event_key
10 20260903010000_ws4_gate3_4a_item_assignment_foundation.sql
11 20260905000000_gate4_actor_provenance.sql
12 20260905010000_gate5_t1_automation_provenance.sql
13 20260905020000_gate5_t6_automation_write_once_guard.sql
14 20260906010000_gate6_w1_automation_extracted_output.sql
15 20260906090000_p6_1c_consultant_engagement.sql
16 20260906100000_p6_2a_consultant_processing_permissions.sql
17 20260910120000_p6_2d_consultant_provenance.sql
```

Isolated-schema confirmation that objects the production code needs are defined by these
migrations: `work_item_assignments` **exists = 1** · `notifications.event_key` **present = 1**.

**LIVE MIGRATION STATE = UNKNOWN** — no production Supabase credentials exist here and the task
is read-only; no comparison was performed and none is inferred.

**Classification:** `REPOSITORY_ONLY` (17/17). The unknown is **not a commit blocker** (the
repository delta is self-consistent and ordered) but **is a deployment blocker**: reconcile live
state and apply 1 → 17 before production serves traffic.

## 6. Router / startup integrity — **PASS**

`backend/api/router.py` imports the new routers (`api.v3_pe:52`, `api.v3_context:62`,
`api.v3_health:63`) and mounts them alongside the modified Phase-6 routers. A full static import
scan of every non-test backend module resolved **all** local imports (`api.*`, `data.*`,
`domain.*`, `services.*`, `infra.*`, `core.*`, `engines.*`, `workers.*`, `auth`, `database`):
the only unresolved names anywhere were inside `backend/.venv/` third-party packages — **no
application module has an unresolved local import**. No circular import is evident statically,
and the app started successfully against this tree earlier in the project.

## 7. Frontend / backend compatibility — **PASS (one warning)**

The frontend calls the v3 contract directly (`/api/v3/commercial/*`, `/api/v3/billing/orders/*`,
`/api/v3/notifications`, `/api/v3/processing/*`, `/api/v3/consultants/*`, `/api/v3/pe/*`,
`/api/v3/ops/*`) — all present in the Release-1 backend routers. **WARNING (not a commit
blocker):** `frontend/src/supabaseClient.js` carries a **production Supabase fallback URL** and
`frontend/src/v3/api.js` defaults to `http://localhost:8000`; production builds must set
`REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` explicitly. No
secret value is printed here.

## 8. Admin control plane — **PASS WITH CORRECTION**

`admin/src/**` builds via `react-scripts build` and is routed by `vercel.json` at `/admin/*` — but
it consumes **v1-era endpoints** (`/api/admin/reviews/*`, `/api/admin/staff*`,
`/api/organizations/*`, `/api/drafts/*`, `/api/reference/*`, `/api/waitlist/*`, `/api/logs/*`)
and contains **no** `/api/v3/billing|commercial` calls.

**P0-4 is nevertheless supported**: `frontend/src/v3/admin/**` and
`frontend/src/v3/customer/BillingPage.jsx` call `/api/v3/commercial/*` and `/api/v3/billing/*`,
and the backend exposes the provisioning routes
(`/api/v3/billing/{config,credits/grant,credits/adjust,credits/refund,credits/reverse,
credits/rollover,orders,organizations}` and `/api/v3/commercial/**`). The provisioning surface is
therefore the **v3 admin area inside the main frontend**, not the legacy admin app. PO decision:
include the legacy admin app, or leave its deployment unchanged.

## 9. Secrets / sensitive-file check — **PASS**

`git check-ignore -v` proves exclusion: `e2e/environment/.env.e2e`
(`e2e/environment/.gitignore:2`) · `tests/e2e/.env.personas` and `backend/.env`
(`.gitignore:83:.env*`). No secret-named path appears in `git status`, and no credential, key,
token or signed URL appears anywhere in the Release-1 list. E2E configuration cannot reach a
production artifact: it lives in `e2e/environment/**` and `tests/e2e/**`, outside the backend
package and the CRA build inputs, and no production module imports it.

## 10. Deletion safety — **PASS**

152 deletions: `.windsurf/skills/**` (69) and `.claude/skills/**` (69) — agent tooling (R7) ·
`output/{json,reports,sql}/**` (13) — generated · `frontend/src/StaffDashboard.jsx` (1) — proven
to have **zero remaining imports**, so its deletion cannot break the build. **No deletion is
required by Release 1**; the default (exclude all 152) stands.

## 11. Production dependency closure

* **Backend:** `backend/main.py` → `api.router` → v3/ops/admin routers → `services/*` →
  `data/*` → `domain/*` → `infra.ai_runtime` → `core/*`, `auth`, `database`, `config`,
  `engines/calculation.py`, `workers/automatic_processing.py` — **closure complete**.
* **Frontend:** CRA entry → routes → `v3/api.js` + `services/apiClient.js` → feature pages
  (`v3/customer`, `v3/consultant`, `v3/pe`, `v3/ops`, `v3/admin`, `v3/reports`) — tracked in HEAD
  or listed in Release 1.
* **Deployment:** `vercel.json` (modified) → frontend + `/admin/*` routing; root `package.json`
  (modified) — both included.

## 12. Release-blocker matrix

| ID | Finding | Severity | Evidence | Class | Action |
|---|---|---|---|---|---|
| G1 | 17 migrations uncommitted; live state unknown | **P1** | 17 untracked migrations; no production credentials | **Deployment** blocker (not commit) | Reconcile live state; apply 1→17 before serving traffic |
| G2 | `admin/src` is legacy v1 (not the provisioning surface) | **P2** | v1 endpoint greps; no v3 billing/commercial calls | PO decision / post-launch | Decide inclusion; P0-4 covered by `frontend/src/v3/admin` |
| G3 | Frontend production Supabase fallback + localhost API default | **P1** | `supabaseClient.js`, `v3/api.js` | **Deployment** blocker | Set `REACT_APP_*` explicitly at build |
| G4 | 152 deletions could be swept by `git add -A` | **P0 (process)** | 69+69+13+1 | **Commit** blocker if globs used | Stage by explicit path only |
| G5 | Billing/usage SQL fix uncommitted | **P0 (process)** | `data/billing.py:854` | **Commit** blocker if omitted | Included in the Release-1 list |
| G6 | P6-2F evidence gaps (browser skips, D11 events, harness) | **E** | prompt history 001–017 | Evidence gap | No release action |
| G7 | P6-2F independent verification not performed | **E** | verification session | Evidence gap | No release action |
| G8 | Observability / backup / DR unverified | P1/P3 | readiness audit | Deployment prerequisite | Post-commit, pre-scale |

## 13. Final readiness checklist

* **Git** — HEAD correct (`1639121710…`); tree unchanged by this task; nothing staged; 152
  deletions excluded by default ✅
* **Production code** — backend closure complete ✅ · `ai_runtime.py` included ✅ · router deps
  complete ✅ · billing complete and schema-compatible ✅
* **Database** — 17 migrations identified ✅ · order correct ✅ · live state **UNKNOWN**
  (deployment prerequisite) · no mismatches observed
* **Frontend** — compatibility acceptable ✅ · production env vars must be supplied (**WARNING**)
* **Admin** — legacy admin app included and deployable ✅ · **P0-4 supported via
  `frontend/src/v3/admin` + `/api/v3/commercial|billing`** ✅
* **Security** — secrets excluded ✅ · E2E isolated ✅ · **no P0 security concern identified** ✅
* **P6** — no actual implementation defect blocking release ✅ · remaining P6-2F items are
  **evidence gaps (E)** ✅
* **P7/P8** — nothing from Phase 7 or Phase 8 is required for Release 1 ✅

## 14. Proposed staging boundary (NOT executed)

```text
git add -- backend/main.py backend/database.py backend/auth.py backend/core/exceptions.py
git add -- backend/api/router.py backend/api/consultant_auth.py backend/api/v3_pe.py \
           backend/api/v3_context.py backend/api/v3_health.py backend/api/pe_auth.py \
           backend/api/processing_mode.py backend/api/audit_helpers.py
git add -- backend/data/billing.py backend/services/billing.py backend/domain/billing.py \
           backend/domain/processing_origin.py backend/infra/ai_runtime.py
git add -- backend/services/consultant_lifecycle.py backend/services/work_items.py \
           backend/services/ai_document_extraction.py
git add -- supabase/migrations/2026*.sql          # the 17 named files, order 1 → 17
git add -- frontend/src/services/apiClient.js frontend/src/v3/pe frontend/src/v3/ops \
           frontend/src/v3/consultant/ConsultantPage.jsx frontend/src/v3/customer \
           frontend/src/v3/reports/ReportsPage.jsx frontend/src/v3/v3.css
git add -- vercel.json package.json
# commit-but-not-deploy
git add -- backend/tests tests/e2e qa_harness e2e/environment docs
```

* **Must remain unstaged:** the 152 deletions · `output/**` · `screenshots/**` ·
  `agent_swarm_v2_artifacts/**` · `qa_harness/{evidence,reports}/**` · root junk files · caches.
* **Must never be committed:** any `.env*` / `.env.personas` / credential or key material.
* **Never use `git add -A` or `git add -u`.**

## 15. Verdict

**`PRE-COMMIT GATE — PASS WITH PO DECISIONS`**

No technical P0 commit blocker exists. PO decisions required before the commit:
(1) scope of the legacy `admin/src/**` and its `/admin/*` route;
(2) confirmation that all 152 deletions stay out of Release 1;
(3) acknowledgement that live migration reconciliation (`UNKNOWN`) remains a **deployment**
prerequisite — reconcile and apply 1 → 17 before serving traffic.

## 16. Mandatory no-change confirmation

```
Repository modified by this task:   NO (documentation files only)
Source code modified:               NO
Tests modified:                     NO
Migrations modified:                NO
Database altered:                   NO
Files staged:                       0
Commit created:                     NO
Push performed:                     NO
Reset performed:                    NO
Clean performed:                    NO
Deployment performed:               NO
Secrets changed:                    NO
E2E environment changed:            NO
HEAD: 16391217103b98dcea520070c5a22c68f12fe607 (unchanged)
```

## 17. Commands used (read-only)

`git branch --show-current` · `git rev-parse HEAD` · `git status --porcelain=v1`
(+ `cut`/`sort`/`uniq`) · `git diff --cached --name-only` · `git ls-files --others
--exclude-standard -- <paths>` · `git check-ignore -v` · read-only `information_schema`
queries on the isolated Postgres (`:55326`) · `sed`/`grep` inspection of
`backend/data/billing.py`, `backend/api/router.py`, `backend/infra/ai_runtime.py`,
`admin/package.json`, `admin/src/**` endpoint usage, `frontend/src/v3/api.js`,
`frontend/src/supabaseClient.js`, `backend/api/v3_commercial.py`, `backend/api/v3_billing.py`,
`supabase/migrations/**` · and an **AST-based static import-closure scan** of every non-test
backend module. **No mutating command was issued.**

## 18. Files inspected

`docs/architecture/CARBONTALLY_PRODUCTION_RELEASE_MANIFEST_20260911.md` (and the two prior
audits), `backend/data/billing.py`, `backend/services/billing.py`, `backend/domain/billing.py`,
`backend/api/router.py`, `backend/api/v3_pe.py`, `backend/api/v3_context.py`,
`backend/api/v3_health.py`, `backend/api/pe_auth.py`, `backend/api/processing_mode.py`,
`backend/api/v3_commercial.py`, `backend/api/v3_billing.py`, `backend/infra/ai_runtime.py`,
`backend/services/automatic_processing.py`, `backend/workers/automatic_processing.py`,
`admin/package.json`, `admin/src/**` (API usage), `frontend/src/v3/api.js`,
`frontend/src/services/apiClient.js`, `frontend/src/supabaseClient.js`,
`frontend/src/v3/admin/**`, `frontend/src/v3/customer/BillingPage.jsx`, `vercel.json`,
`package.json`, `supabase/migrations/**` (53), `.gitignore`, `e2e/environment/.gitignore`.



