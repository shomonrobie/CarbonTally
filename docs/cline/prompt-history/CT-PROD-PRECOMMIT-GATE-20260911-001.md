# CT-PROD-PRECOMMIT-GATE-20260911-001

**Prompt Ref:** `CT-PROD-PRECOMMIT-GATE-20260911-001` · **Date:** 2026-09-11
**Mode:** READ-ONLY pre-commit gate (no stage, commit, push, reset, clean, migration, DB or deploy action)
**Repository:** CarbonTally · **Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (verified; matches expectation)
**Durable output:** `docs/architecture/CARBONTALLY_PRODUCTION_PRECOMMIT_GATE_20260911.md`

## 1. Scope

Determine, read-only, whether the exact Release-1 manifest is internally complete and whether
any P0/P1 release blocker remains before a RELEASE-COMMIT authorization. Verify git state,
manifest integrity at file level, the billing/D6 path, the 17 migrations, schema compatibility,
router/startup integrity, frontend↔backend compatibility, the admin control plane, secrets,
deletion safety, dependency closure, the P6-2F and Phase-7/8 boundaries, and production
configuration; then produce a blocker matrix, a proposed staging boundary and a verdict
(PASS / PASS WITH PO DECISIONS / BLOCKED). Hard read-only constraints respected throughout.

## 2. Response summary

**Verdict: `PRE-COMMIT GATE — PASS WITH PO DECISIONS`** — no technical P0 commit blocker;
three PO decisions and one manifest correction remain.

**Git state:** branch `main`; HEAD `16391217103b98dcea520070c5a22c68f12fe607` (unchanged since
the manifest); **staged 0**; 248 untracked entries (247 + this record), 286 modified, 152
deleted. No unexpected changes appeared between audits.

**Manifest integrity:** every dependency class present at file level — including
`backend/infra/ai_runtime.py` (confirmed imported by production:
`services/automatic_processing.py:50`, `workers/automatic_processing.py:162`) and the router
co-commit set (`router.py` imports `api.v3_pe:52`, `api.v3_context:62`, `api.v3_health:63`, plus
support modules `pe_auth`, `processing_mode`, `audit_helpers`).

**Billing / D6 — PASS.** `backend/data/billing.py:854` is
`date_trunc('month', $2::timestamptz)::date`; isolated `information_schema` shows
`usage_tracking.usage_date = date`, `usage_month = date`, `ai_files_processed = integer` → the
expression is type-compatible and both earlier failures are eliminated. All D6 dependencies are
in the release set.

**Migrations.** 17 files, order strictly 1 → 17 (no duplicate timestamps); `work_item_assignments`
exists and `notifications.event_key` exists in the isolated schema, confirming the objects these
migrations define are the ones production code requires. **LIVE MIGRATION STATE = UNKNOWN** (no
production credentials; read-only task; not inferred) → a **deployment** prerequisite, **not** a
commit blocker.

**Router / startup — PASS.** An AST-based static scan of every non-test backend module resolved
**all** local imports; the only unresolved names anywhere were inside `backend/.venv/`
third-party packages (onnxruntime internals). No missing application module, no evident
circular import.

**Frontend / backend — PASS with one warning.** The frontend calls the v3 contract
(`/api/v3/commercial/*`, `/api/v3/billing/orders/*`, processing/consultants/pe/ops/notifications)
and all those routers are in the release. **Warning:** `frontend/src/supabaseClient.js` carries a
production Supabase fallback URL and `v3/api.js` defaults to `http://localhost:8000` → production
builds must set `REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`.

**Admin — PASS WITH CORRECTION.** `admin/src/**` is the **legacy v1** admin app (calls
`/api/admin/*`, `/api/organizations/*`, `/api/drafts/*`, `/api/reference/*`, `/api/waitlist/*`,
`/api/logs/*`; **no** `/api/v3/billing|commercial` calls). **P0-4 is nonetheless supported** by
`frontend/src/v3/admin/**` + `frontend/src/v3/customer/BillingPage.jsx` calling
`/api/v3/commercial/*` and `/api/v3/billing/*` (backend provisioning routes confirmed: `config`,
`credits/grant|adjust|refund|reverse|rollover`, `orders`, `organizations`). The Release
Manifest's rationale that the legacy admin app closes P0-4 is **corrected**; release *content* is
unaffected because both trees sit inside the Release-1 set.

**Secrets — PASS.** `git check-ignore -v` proves `.env.e2e`, `tests/e2e/.env.personas` and
`backend/.env` are ignored; no secret path appears in `git status`; the E2E tree is outside the
backend package and the CRA build inputs.

**Deletions — PASS.** 152 = `.windsurf/skills` (69) + `.claude/skills` (69) + `output/**` (13) +
`frontend/src/StaffDashboard.jsx` (1). No deletion is required by Release 1; `StaffDashboard.jsx`
has zero remaining imports. Default (exclude all 152) stands.

## 3. Blocker matrix (summary)

| ID | Finding | Severity | Class |
|---|---|---|---|
| G1 | 17 migrations uncommitted; live state unknown | P1 | **Deployment** blocker |
| G2 | `admin/src` is legacy v1, not the provisioning surface | P2 | PO decision / post-launch |
| G3 | Frontend production Supabase fallback + localhost API default | P1 | **Deployment** blocker |
| G4 | `git add -A` would sweep the 152 deletions | P0 (process) | Commit blocker only if globs used |
| G5 | Billing fix uncommitted | P0 (process) | Commit blocker only if omitted |
| G6/G7 | P6-2F browser skips / D11 evidence / harness / independent verification | E | Evidence gap — **not** a release blocker |
| G8 | Observability / backup / DR unverified | P1/P3 | Deployment prerequisite |

## 4. Proposed staging boundary (not executed)

Explicit-path `git add --` sets for the backend production files, the 17 migrations, the
`frontend/src` production UI files, `vercel.json` and root `package.json`; a separate
commit-but-not-deploy set (`backend/tests`, `tests/e2e`, `qa_harness`, `e2e/environment`,
`docs`); the 152 deletions, generated artifacts, caches and unrelated tooling must remain
unstaged; no credential may ever be committed. **`git add -A` / `-u` must never be used.**

## 5. Unresolved PO decisions

1. Scope of the legacy `admin/src/**` and its `/admin/*` Vercel route in Release 1.
2. Confirmation that all 152 deletions remain excluded from Release 1.
3. Acknowledgement that live migration reconciliation (`UNKNOWN`) is a **deployment**
   prerequisite — reconcile, then apply 1 → 17 before serving traffic.

## 6. Files inspected

`docs/architecture/CARBONTALLY_PRODUCTION_RELEASE_MANIFEST_20260911.md` (and the two prior
audits) · `backend/data/billing.py` · `backend/services/billing.py` · `backend/domain/billing.py` ·
`backend/api/router.py` · `backend/api/{v3_pe,v3_context,v3_health,pe_auth,processing_mode}.py` ·
`backend/api/v3_commercial.py` · `backend/api/v3_billing.py` · `backend/infra/ai_runtime.py` ·
`backend/services/automatic_processing.py` · `backend/workers/automatic_processing.py` ·
`admin/package.json` · `admin/src/**` (endpoint usage) · `frontend/src/v3/api.js` ·
`frontend/src/services/apiClient.js` · `frontend/src/supabaseClient.js` ·
`frontend/src/v3/admin/**` · `frontend/src/v3/customer/BillingPage.jsx` · `vercel.json` ·
`package.json` · `supabase/migrations/**` (53) · `.gitignore` · `e2e/environment/.gitignore`.

## 7. Commands used (read-only)

`git branch --show-current` · `git rev-parse HEAD` · `git status --porcelain=v1` (+ `cut`/`sort`/
`uniq`) · `git diff --cached --name-only` · `git ls-files --others --exclude-standard -- <paths>` ·
`git check-ignore -v` · read-only `information_schema` queries on the isolated Postgres
(`:55326`) · `sed`/`grep` inspection of the files above · **AST-based static import-closure scan**
of every non-test backend module. **No mutating command was issued.**

## 8. Migration findings

17 migrations, order 1 → 17 strictly by timestamp prefix; `work_item_assignments` and
`notifications.event_key` confirmed present in the isolated schema (the objects the PE and D11
code paths require). Live state for all 17 = **UNKNOWN** (not inferred). Absence of live-state
evidence is a **deployment** prerequisite, not a commit blocker, because the repository delta is
self-consistent, ordered and additive.

## 9. Production dependency findings

Backend closure **complete** (static scan). The previously hidden production module
`backend/infra/ai_runtime.py` is in the Release-1 list and its importers are confirmed. Router
co-commit set complete. Frontend closure resolves to tracked files or Release-1 entries.

## 10. Billing findings

SQL fix present and **schema-type-compatible** (`usage_month date` ← `date_trunc(...)::date`).
D6 dependency set complete. No production-only test dependency in the charge path. Replay is
guarded by the pre-existing `charge:item:<id>` idempotency key claim.

## 11. Admin findings

Legacy v1 admin app (deployable, `/admin/*` routed) is **not** the v3 provisioning surface;
P0-4 is served by `frontend/src/v3/admin/**` + `frontend/src/v3/customer/BillingPage.jsx` →
`/api/v3/commercial|billing`. Manifest rationale corrected; release content unchanged.

## 12. Security findings

No secret material inside the Release-1 boundary (ignore rules proven); E2E configuration cannot
reach a production artifact; **no P0 security concern identified**. The only configuration risk
is the production Supabase/API defaults in the frontend (G3) — a deployment-time environment
requirement, not a code defect.

## 13. P6 boundary findings

No actual P6 implementation defect blocks release. The remaining P6-2F items (three consultant
browser skips, D11 `accepted`/`qc_outcome`/`rework` evidence, harness re-runnability, a completed
pytest run, independent verification) are **E-class evidence gaps** and are **not** release
blockers. No P6-2F remediation was started. Nothing from Phase 7 or Phase 8 is required for
Release 1.

## 14. Final verdict

**`PRE-COMMIT GATE — PASS WITH PO DECISIONS`**

## 15. Mandatory no-change confirmation

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

No P6-2F remediation, Phase 7 or Phase 8 work was started. No verification or release claim is
made; P6-2F remains **NOT VERIFIED / NOT CLOSED**.

