# CarbonTally — Production Release Boundary Audit

**Prompt Ref:** `CT-PROD-RELEASE-BOUNDARY-AUDIT-20260911-001` · **Date:** 2026-09-11
**Role:** read-only release-boundary auditor (no staging, commit, reset, clean or file changes)
**Repository:** CarbonTally · **Branch:** `main` · **HEAD confirmed:** `16391217103b98dcea520070c5a22c68f12fe607` (matches the reported HEAD — no discrepancy)
**Related:** Production Readiness Audit `CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md` (addresses P0-1 only)

## 1. Executive conclusion

The working tree is **not** committable as-is, but the release boundary **is** identifiable.
It contains the complete, already-authorized Phase-6 production runtime, the P0-2 billing
fix, 17 new migrations and the production UI changes — mixed with a large amount of **agent
tooling, generated evidence and disposable artifacts** that must never be deployed, plus
**152 tracked-file deletions** that a naive `git add -A` would silently include.

Every production-critical change was located and traced. What remains uncertain is **not** the
identity of the production code, but three boundary decisions that belong to the Product
Owner: (a) whether the `admin/` control-plane app ships in release 1, (b) whether the 225
agent-skill deletions are intended, and (c) the **applied / not-applied status of the 17 new
migrations in the real production database** — which the repository cannot establish.

**Verdict: B — RELEASE BOUNDARY PARTIALLY IDENTIFIED / PO DECISIONS REQUIRED.**

## 2. Exact working-tree counts

| Metric | Value |
|---|---|
| `git status --porcelain` entries | **684** |
| — untracked entries (`??`) | **246** |
| — modified tracked (` M`) | **286** |
| — deleted tracked (` D`) | **152** |
| untracked **files** (`git ls-files --others --exclude-standard`) | **1210** |
| staged files | **0** |

**682 vs 684 resolved:** `git status --short | wc -l` was 682 during the Production
Readiness Audit; it is 684 now because that audit **added two documentation files** (the
readiness report + its prompt-history record). Nothing else changed.

## 3. Change inventory by area

`.windsurf/skills` 78 · `.claude/skills` 78 · `.agents/skills` 69 · `admin/src` 60 ·
`docs/architecture` 59 · `frontend/src` 51 · `backend/tests` 44 · `docs/cline` 32 ·
`tools/carbon_data_factory` 29 · `backend/api` 20 · `docs/audit` 19 ·
`supabase/migrations` 17 · `output/**` 17 · `backend/{data,services,domain}` 20 ·
`demodatagen/**` 9 · root junk 5.

Untracked directories: `saas-assurance/packages` 187 · `qa_harness/evidence` 138 ·
`agent_swarm_v2_artifacts/screenshots` 85 · `e2e/environment` 74 · `docs/cline` 68 ·
`docs/architecture` 59 · `qa_harness/reports` 55 · `backend/tests` 44 ·
`screenshots/**` ≈80 · `qa_harness/{tests,browser,scripts,config}` ≈77.

## 4. Billing fix trace (P0-2)

```
 M backend/data/billing.py        3 +-        ← the SQL fix
 M backend/services/billing.py  117 +++++--   ← D6 entitlement gate + charge path
-            VALUES ($1, $2, to_char($2, 'YYYY-MM'), $3)
+                    date_trunc('month', $2::timestamptz)::date, $3)
```

* file: `backend/data/billing.py` · component: `UsageTrackingRepository.record`
* **committed? NO** — uncommitted working-tree modification
* dependencies: `backend/services/billing.py`, `backend/domain/billing.py`,
  `backend/api/v3_processing_workflow.py`, and the pre-existing `usage_tracking` table with
  its `usage_month` **date** column
* tests: `backend/tests/unit/api/test_billing_core.py` (modified) + the live E2E
  acceptance path

## 5. Phase-6 production runtime (R1)

**New files:** `backend/api/{pe_auth,processing_mode,v3_context,v3_health,v3_pe,audit_helpers}.py` ·
`backend/domain/processing_origin.py` ·
`backend/services/{ai_document_extraction,consultant_lifecycle,work_items}.py`

**Modified:** `backend/api/{router,consultant_auth,v3_automatic_processing,v3_commercial,
v3_consultants,v3_documents,v3_manual_extraction,v3_messaging,v3_operations,v3_organizations,
v3_processing_workflow,v3_qc,v3_reporting,v3_review}.py` ·
`backend/data/{audit,billing,consultants,document_processing,emissions_logs,
manual_extraction,messaging,notifications,tenant}.py` ·
`backend/domain/{audit,automatic_processing,billing,partners}.py` ·
`backend/services/{automatic_extraction,automatic_processing,billing}.py`

**Critical dependency:** `backend/api/router.py` is modified and mounts the **new** routers
(`v3_pe`, `v3_health`, `v3_context`, `pe_auth`, `processing_mode`). Committing the new files
without `router.py` (or vice-versa) breaks application startup.

## 6. Decision traces

* **D6** — `backend/services/billing.py` (`ensure_processing_entitlement`, STANDARD allowance,
  `record`), `backend/domain/billing.py`, `backend/api/v3_processing_workflow.py`
  (`customer_review_item` → charge), `backend/data/billing.py`. **R1, present.**
* **D7** — `backend/domain/processing_origin.py` (new), `backend/api/v3_consultants.py`,
  `backend/api/v3_context.py`, `backend/data/consultants.py`, migration
  `20260910120000_p6_2d_consultant_provenance.sql` (new). **R1.** Origin vocabulary remains
  exactly `CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY`.
* **D8** — `backend/api/v3_messaging.py`, `backend/data/messaging.py` (modified): existing
  conversation model reused; **no** new conversation kind or table. **R1.**
* **D11** — `backend/services/consultant_lifecycle.py` (new), `backend/data/notifications.py`,
  migration `20260902050000_phase5_notification_event_key.sql` (new → `event_key`). Runtime
  **R1**; D11 tests and E2E notification fixtures are **R2/R3**.
* **PE work** — `backend/api/v3_pe.py`, `backend/api/pe_auth.py`,
  `backend/services/work_items.py`, migration
  `20260902030000_phase5_work_item_assignments.sql` (the `work_item_assignments` table the PE
  workspace authorizes against). **R1.**
* **P6-2F UI** — `frontend/src/**` (51 modified / 23 new), incl. the consultant item
  workspace. **Safe to deploy (R1):** API authorization and workspace access are verified
  (200); the outstanding issue is *control rendering* for three consultant specs, which the
  readiness audit classified **P1, not P0**. The UI is not half-built in a way that is unsafe
  to ship — it may simply not expose every action button.

## 7. Database / migration boundary

**17 untracked, new migrations** (none staged, none applied by this audit):

```
20260831000000_v3m10_org_membership_unique.sql
20260831010000_v3m11_operational_indexes.sql
20260831020000_audit_activity_immutability.sql
20260831030000_tenant_org_id_not_null.sql
20260831040000_consultant_revocation_roles.sql
20260902020000_v1_2_dual_origin_workflow.sql
20260902030000_phase5_work_item_assignments.sql        ← PE workspace depends on it
20260902040000_phase5_pe_operational_messaging.sql
20260902050000_phase5_notification_event_key.sql       ← D11 event_key depends on it
20260903010000_ws4_gate3_4a_item_assignment_foundation.sql
20260905000000_gate4_actor_provenance.sql
20260905010000_gate5_t1_automation_provenance.sql
20260905020000_gate5_t6_automation_write_once_guard.sql
20260906010000_gate6_w1_automation_extracted_output.sql
20260906090000_p6_1c_consultant_engagement.sql
20260906100000_p6_2a_consultant_processing_permissions.sql
20260910120000_p6_2d_consultant_provenance.sql
```

These are **required by the current production code** (assignment foundation, notification
`event_key`, consultant provenance/permissions, audit immutability). They are **R1 for the
repository**, but their **production application status is
`UNKNOWN — REQUIRES PO/DB VERIFICATION`**: the repository cannot tell whether they are already
applied in the live Supabase project. They must be applied in order, and only after
verification — never blindly.

## 8. Classification of every change family

| Class | Content |
|---|---|
| **R1** Production release candidate | `backend/{api,data,domain,services}/**` (modified + new, incl. the billing fix), `supabase/migrations/**` (17 new), `frontend/src/**`, `vercel.json`, and — pending PO decision — `admin/src/**` |
| **R2** Test / verification support (keep in Git, not in the deployable artifact) | `backend/tests/**` (44 modified/new incl. `backend/tests/e2e/`, `backend/tests/integration/…`), `tests/e2e/**`, `qa_harness/{tests,browser,scripts,config}/**` |
| **R3** E2E infrastructure (reusable, **must not deploy**) | `e2e/environment/**` (74 files: isolated config, scripts, seed, `grant_*.sql`), `tests/e2e/**`, `backend/tests/e2e/**` |
| **R4** Documentation / evidence (durable history — commit) | `docs/architecture/**` (59), `docs/cline/**` + prompt history (100+), `docs/audit/**` (19), `docs/standalone/**` |
| **R5** Generated / local artifact (**exclude**) | `output/**` (17), `screenshots/**` (≈80), `agent_swarm_v2_artifacts/screenshots/**` (85), `qa_harness/evidence/**` (138), `qa_harness/reports/**` (55), `test_results*.json`, `v1.9.txt`, `v3_schema.sql`, `test_endpoints.py`, `__pycache__`/`.pytest_cache`/`node_modules`/Playwright output |
| **R6** Secret / sensitive (**EXCLUDE — never commit**) | `e2e/environment/.env.e2e` · `e2e/environment/.env.personas` · `tests/e2e/.env.personas` · `frontend/.env*` · `backend/.env` · any real Supabase service-role/anon keys, JWT secret, tokens. **Proof they cannot leak:** `git check-ignore -v` matches them (`.gitignore:83:.env*`; `e2e/environment/.gitignore:2-3`), and a scan of `git status` output found **no** secret-named entry |
| **R7** Unrelated pre-existing | `.windsurf/skills` (78), `.claude/skills` (78), `.agents/skills` (69) — agent tooling, the source of the **152 deletions** · `.clinerules/hooks` · `tools/**` (carbon_data_factory, seed_investor_demo) · `demodatagen/**` · `agent_swarm/v2` · `saas-assurance/**` (187 + 26) |
| **R8** Uncertain → PO decision | `admin/src/**` (60) · `saas-assurance/**` · `tools/**` · the 152 deletions' *intent* |

## 9. Production dependency chain

```
approval endpoint   backend/api/v3_processing_workflow.py      (modified)
      ↓
D6 gate + charge    backend/services/billing.py (117 lines) + backend/domain/billing.py
      ↓
usage write (P0-2)  backend/data/billing.py   ← date_trunc('month', …)::date
      ↓
schema              usage_tracking.usage_month (DATE) · customer_subscriptions
                     ← 17 new migrations (assignments, event_key, provenance, permissions)
      ↓
router mount        backend/api/router.py      (modified — REQUIRED with the new routers)
      ↓
UI consumption      frontend/src/**            (51 modified / 23 new)
```

**Rule:** commit as one coherent set — `router.py` + new backend modules + modified
data/domain/service layers + the 17 migrations + the frontend changes. Splitting them breaks
the deploy.

## 10. E2E / secrets / deployment boundary

* **E2E (R3)** — `e2e/environment/**` (74 files: isolated `supabase/config.toml`, scripts,
  `grant_*.sql`, `seed_e2e.py`) and `tests/e2e/**`. They belong in Git as reusable verification
  infrastructure and **must never be part of a deployed artifact**; no production runtime
  module imports them.
* **Secrets** — proven excluded: `git check-ignore` matches `e2e/environment/.env.e2e`
  (`e2e/environment/.gitignore:2`), `e2e/environment/.env.personas` (line 3) and
  `tests/e2e/.env.personas` (`.gitignore:83:.env*`). No secret-named entry appears in
  `git status`. → **SECRET / SENSITIVE — EXCLUDE** (they cannot enter the commit accidentally;
  only an explicit `git add -f` could defeat this).
* **Frontend** — `vercel.json` modified (R1); the CRA build consumes only `REACT_APP_*`, and
  `e2e/**`/`backend/**` are not build inputs, so E2E infrastructure cannot leak into the bundle.
* **Backend** — entrypoint `backend/main:app` (uvicorn); `backend/tests/**` is not imported by
  the runtime, and the E2E tree lives outside `backend/`.
* **Supabase** — the 17 migrations are the schema delta; the E2E stack's `config.toml`
  (isolated ports) must never be used for production.

## 11. PROPOSED PRODUCTION RELEASE SET

```
backend/api/**          modified + NEW (pe_auth, processing_mode, v3_context, v3_health,
                        v3_pe, audit_helpers, router.py …)
backend/data/**         incl. billing.py  ← the P0-2 fix
backend/domain/**       incl. processing_origin.py, billing.py, partners.py
backend/services/**     incl. consultant_lifecycle.py, work_items.py,
                        ai_document_extraction.py, billing.py, automatic_*
backend/main.py, backend/requirements.txt   (only if modified — verify)
supabase/migrations/**  the 17 new files (apply order + production status PO-verified first)
frontend/src/**         51 modified + 23 new
vercel.json             deployment config (modified)
docs/architecture/**, docs/cline/**, docs/audit/**    durable history (R4)
backend/tests/**, tests/e2e/**, qa_harness/{tests,browser,scripts,config}/**   R2
e2e/environment/**      R3 — reusable E2E infrastructure, NOT deployed
```
**Conditional (PO decision):** `admin/src/**` (60 entries).

## 12. MUST NOT ENTER THE PRODUCTION RELEASE

**Excluded from the Git commit:** `output/**` · `screenshots/**` ·
`agent_swarm_v2_artifacts/**` · `qa_harness/evidence/**` · `qa_harness/reports/**` ·
`test_results*.json` · `v1.9.txt` · `v3_schema.sql` · `test_endpoints.py` · all `.env*` /
`.env.personas` (**SECRET / SENSITIVE — EXCLUDE**) · caches (`__pycache__`, `.pytest_cache`,
`node_modules`, Playwright output) · the **152 tracked deletions** (review individually — a
blanket `git add -A` would delete agent tooling).

**May exist in Git but must not be deployed:** `e2e/environment/**` · `tests/e2e/**` ·
`backend/tests/**` · `qa_harness/**` · `docs/**` · `tools/**` · `demodatagen/**` ·
`saas-assurance/**` · `agent_swarm/**` — repository/test/evidence content, never part of the
runtime artifact.

## 13. REQUIRES PRODUCT OWNER DECISION

| Item | Why uncertain | Evidence to resolve | Recommended default |
|---|---|---|---|
| `admin/src/**` (60) | Is the control-plane app in release 1? | PO scope decision; check which Vercel project targets it | Include only if already deployed; else defer |
| 152 deletions (`.windsurf`/`.claude`/`.agents` skills) | Whether agent-tooling removal is intended | PO confirmation + `git diff --summary` review | **Exclude** from the release commit |
| 17 migrations' status in production | Not determinable from the repo | Query the live Supabase migration table / `supabase migration list` | Verify, then apply **in order** — never assume |
| `saas-assurance/**`, `agent_swarm/v2`, `tools/**`, `demodatagen/**` | Unclear if P6 artifacts or later-phase work | PO classification | Exclude from release 1 |

## 14. Release risk analysis

| Risk | Severity |
|---|---|
| Billing fix omitted → production keeps the approval crash | **P0** |
| New routers committed without `backend/api/router.py` (or vice-versa) → app fails to start | **P0** |
| `git add -A` silently commits 152 deletions + agent tooling | **P0** |
| Migrations applied out of order / unverified → production schema drift | **P0** |
| E2E configuration reaching production config | P1 (currently prevented by ignore rules + separate trees) |
| ~400 generated artifacts bloating the release | P1 (hygiene, not safety) |
| Unrelated pre-existing modifications deployed | P1 |

## 15. Recommended release procedure (for the PO — NOT executed here)

```
1  Review the proposed release set (§11); resolve §13 decisions.
2  Verify production migration status against the live Supabase project.
3  Stage ONLY explicit approved paths — never `git add -A`.
4  Review the staged diff for deletions and secrets (`git diff --cached --stat`).
5  Confirm no .env*/credentials/generated artifacts are staged.
6  Run release tests (unit + e2e + acceptance harnesses).
7  Commit on a release branch; tag the release.
8  Deploy to staging; verify startup, one approval (P0-2) and RLS cross-tenant denial.
9  Deploy production; repeat the same checks.
10 Keep the E2E tree and tooling out of every deployed artifact.
```

## 16. Answers to the four critical questions

1. **Can the working tree be committed as-is? → NO.** It mixes 684 status entries across
   production code, 152 deletions of agent tooling (R7), ~400 generated artifacts (R5),
   unrelated tooling (`saas-assurance`, `agent_swarm`, `tools`, `demodatagen`) and
   documentation. A blanket commit would deploy unrelated work and delete tooling.
2. **Is the billing fix in the proposed release set? → YES.** `backend/data/billing.py`
   contains `date_trunc('month', $2::timestamptz)::date` replacing `to_char($2, 'YYYY-MM')`,
   with `backend/services/billing.py` (117 lines) and
   `backend/api/v3_processing_workflow.py` as dependencies — but it is **uncommitted**.
3. **Can the P6-2F E2E environment leak into production deployment? → NO.** Secret files are
   Git-ignored (`git check-ignore` matched `.env.e2e`, `.env.personas`); the E2E tree lives in
   `e2e/environment/**` and `tests/e2e/**`, outside the backend application package and outside
   the CRA build inputs; no production module imports E2E code.
4. **Smallest safe release containing the required functionality:**
   `backend/{api,data,domain,services}/**` + `supabase/migrations/**` (17, applied in order after
   verification) + `frontend/src/**` + `vercel.json` + durable `docs/**`, with
   `backend/tests/**`, `tests/e2e/**`, `e2e/environment/**`, `qa_harness/**` committed as
   non-deployed verification content and **everything else excluded**.

## 17. Commands used (read-only)

`git rev-parse HEAD` · `git log --oneline -6` · `git status --porcelain=v1` (with
`cut`/`awk`/`sort`/`uniq` aggregation) · `git ls-files --others --exclude-standard` ·
`git status --porcelain=v1 -- <paths>` · `git diff --stat` · `git diff -U2` ·
`git diff --cached --name-only` · `git check-ignore -v <paths>`.
**No mutating Git command was executed.**

Files inspected: `backend/data/billing.py`, `backend/services/billing.py`,
`backend/api/**`, `backend/domain/**`, `backend/services/**`, `backend/tests/**`,
`supabase/migrations/**`, `frontend/src/**`, `admin/src` (inventory), `vercel.json`,
`e2e/environment/**`, `tests/e2e/**`, `.gitignore`, `e2e/environment/.gitignore`,
`docs/**`, plus the Production Readiness Audit.

## 18. Git status / no-change confirmation

```
branch: main          HEAD: 16391217103b98dcea520070c5a22c68f12fe607
staged: 0             modified: 286   deleted: 152   untracked entries: 246
commit created: NO    push: NO       reset: NO      clean: NO
Repository modified by this audit: NO  (documentation files only)
Unrelated modifications preserved: YES
```

## 19. Verdict

**B — RELEASE BOUNDARY PARTIALLY IDENTIFIED / PO DECISIONS REQUIRED**

Release content is concretely identified (§11) and the exclusion boundary is explicit (§12).
Three PO decisions remain (§13: `admin/` inclusion, the 152 deletions' intent, production
migration status). No verification, release, deployment or production-readiness claim is made.



