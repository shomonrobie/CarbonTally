# CT-PROD-RELEASE-MANIFEST-20260911-001

**Prompt Ref:** `CT-PROD-RELEASE-MANIFEST-20260911-001` · **Date:** 2026-09-11
**Mode:** READ-ONLY / INSPECTION-ONLY (no stage, commit, push, reset, clean, migration, deploy or code change)
**Repository:** CarbonTally · **Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (confirmed, unchanged)
**Durable output:** `docs/architecture/CARBONTALLY_PRODUCTION_RELEASE_MANIFEST_20260911.md`

## 1. Scope

Produce an exact **file-level Release-1 manifest** and reconcile the 17 new migrations against
production state if inspectable read-only. Classify every candidate (R1-PROD / R2-TEST /
R3-E2E / R4-DOC / R5-GENERATED / R6-SECRET / R7-UNRELATED / R8-UNCERTAIN); trace the Phase-6
production delta (D6, D7, D8, D11, origin, consultant, PE, billing, frontend); confirm the
billing fix; verify the router dependency; build include / commit-but-not-deploy / exclude /
PO-decision lists; run a release risk check; answer ten final questions. Hard stop
conditions respected: no staging, commit, push, reset, clean, migration application,
database alteration or deployment.

## 2. Response summary

**Billing fix confirmed (uncommitted).** `backend/data/billing.py` line 854 —
`date_trunc('month', $2::timestamptz)::date` replacing `to_char($2, 'YYYY-MM')`; dependency
`backend/services/billing.py` (M, +117 lines).

**Router dependency proved.** `backend/api/router.py` imports `api.v3_pe` (line 52),
`api.v3_context` (line 62), `api.v3_health` (line 63) and mounts them → those new files plus
`pe_auth.py`, `processing_mode.py`, `audit_helpers.py` must co-commit with `router.py` or the
app fails at import.

**Hidden production file found.** `backend/infra/ai_runtime.py` (untracked) is imported by
production code — `backend/services/automatic_processing.py:50`,
`backend/workers/automatic_processing.py:162` — and would be missed by a services/api-only
mental model. Now named explicitly in the R1 list.

**Admin control plane = R1 (evidence-based).** `vercel.json` contains `/admin/*` route rules;
`admin/package.json` declares `name: carbontally-admin`, `homepage: /admin` → the admin app is
wired into the production deployment target and is the provisioning surface for the P0-4
entitlement/subscription gap. PO confirmation advised.

**Deletions de-risked.** The 152 tracked deletions are `.windsurf/skills/**` (69),
`.claude/skills/**` (69), `output/{json,reports,sql}/**` (13) and
`frontend/src/StaffDashboard.jsx` (1). `grep` proves `StaffDashboard.jsx` has **zero remaining
imports**, so accepting that deletion cannot break the build. Default: exclude all deletions
from Release 1.

**Migrations.** 53 in the repo, 17 untracked/new — all required by current production code
(incl. `phase5_work_item_assignments` → `public.work_item_assignments`, and
`phase5_notification_event_key` → `event_key`). Application order = numeric 1 → 17.
**Live production state: UNKNOWN** — no production Supabase credentials exist in this
environment and the task is read-only, so no live comparison was performed or inferred.

## 3. Migration findings

| Migration | Object / purpose | Live status |
|---|---|---|
| `20260902030000_phase5_work_item_assignments.sql` | creates `public.work_item_assignments` + 3 indexes | UNKNOWN (PE workspace depends on it) |
| `20260902050000_phase5_notification_event_key.sql` | `event_key` + `ix_notifications_recipient_inbox` | UNKNOWN (D11 keys depend on it) |
| `20260910120000_p6_2d_consultant_provenance.sql` | consultant firm provenance (D7) | UNKNOWN |
| the other 14 | membership/indexes/immutability/tenant/roles/dual-origin/gates/engagement/permissions | UNKNOWN |

**All 17 = `UNKNOWN` vs live; reconcile read-only first, then apply 1 → 17.**

## 4. Release manifest (exact lists are in the report §9–§13)

* **RELEASE-1-INCLUDE** — `backend/{api,data,domain,services,infra,engines,workers}` production
  files enumerated **by name** (incl. the billing fix and `backend/infra/ai_runtime.py`),
  `backend/{main,database,auth}.py`, `backend/core/exceptions.py`, the 17 migrations, the
  `frontend/src/**` modified + new UI files (`services/apiClient.js`, `v3/pe/**`,
  `v3/ops/{CtQcTab,OpsAssignmentsTab,OpsPeMessagingTab}.jsx`, `v3/consultant/ConsultantPage.jsx`,
  `v3/customer/**`, `v3/reports/ReportsPage.jsx`, `v3.css`), `vercel.json`, root `package.json`,
  and `admin/src/**`.
* **COMMIT-BUT-NOT-DEPLOY** — `backend/tests/**` (incl. new `tests/e2e/**`,
  `tests/integration/**`), `tests/e2e/**`, `qa_harness/{tests,browser,scripts,config}/**`,
  `e2e/environment/**`, `docs/**` (60 architecture + 69 prompt-history new), frontend test files.
* **EXCLUDE** — `output/**`, `screenshots/**`, `agent_swarm_v2_artifacts/**`,
  `qa_harness/{evidence,reports}/**`, `backend/test_results.json`, `test_results*.json`,
  `v1.9.txt`, `v3_schema.sql`, `test_endpoints.py`, caches, `.env*`/`.env.personas`
  (**SECRET / SENSITIVE — EXCLUDE**), agent tooling and unrelated trees (`agent_swarm/**`,
  `saas-assurance/**`, `demodatagen/**`, `tools/**`), plus the 152 deletions by default.
* **PO-DECISION-REQUIRED** — admin inclusion (recommended **INCLUDE**), the deletions
  (recommended **exclude**), live migration reconciliation, and the unrelated tooling trees.

## 5. Risks

**P0:** billing fix omitted · `router.py` split from `v3_pe`/`v3_context`/`v3_health` ·
`git add -A` sweeping deletions · migrations applied out of order or against unknown live
state. **P1:** `infra/ai_runtime.py` omission (now named) · E2E config leakage · ~400
generated artifacts · frontend env defaults still pointing at the production Supabase project.
**P2:** documentation volume · test fragmentation.

## 6. Files inspected

`backend/api/router.py`, `backend/data/billing.py`, `backend/services/billing.py`,
`backend/infra/ai_runtime.py` (+ importers), `backend/api/**`, `backend/data/**`,
`backend/domain/**`, `backend/services/**`, `backend/engines/calculation.py`,
`backend/workers/automatic_processing.py`, `backend/main.py`, `backend/database.py`,
`backend/auth.py`, `backend/core/exceptions.py`, `backend/tests/**`,
`supabase/migrations/**` (53), `frontend/src/**` (modified + untracked), `admin/package.json`
(+ `admin/` listing), `vercel.json`, root `package.json`, `e2e/environment/**`, `tests/e2e/**`,
`.gitignore`, `e2e/environment/.gitignore`, `docs/**`.

## 7. Commands used (read-only only)

`git rev-parse HEAD` · `git log --oneline -6` · `git status --porcelain=v1` (with
`grep`/`cut`/`awk`/`sort`/`uniq`) · `git ls-files --others --exclude-standard -- <paths>` ·
`git diff --stat` · `git diff -U2` · `git diff --cached --name-only` · `git check-ignore -v` ·
targeted `grep`/`head`/`ls` on the files above.

## 8. Explicit no-change confirmation

```
Repository modified by this task: NO   (documentation files only)
staged: 0    commit: NO    push: NO    reset: NO    clean: NO
migration applied: NO     database altered: NO     deployment: NO
E2E / RLS / fixtures / secrets: unchanged
HEAD: 16391217103b98dcea520070c5a22c68f12fe607 (unchanged)
```

## 9. Verdict

**RELEASE MANIFEST COMPLETE — READY FOR PO REVIEW AND A RELEASE-COMMIT PROMPT**

Open items: live migration reconciliation (requires read-only production DB access) and the
two confirmations in report §13 (`admin/src/**`, deletions). No verification, release,
deployment or production-readiness claim is made; P6-2F remains **NOT VERIFIED / NOT CLOSED**.

