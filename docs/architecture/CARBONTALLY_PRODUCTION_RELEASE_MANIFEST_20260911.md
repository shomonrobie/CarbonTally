# CarbonTally — Production Release Manifest & Migration Reconciliation

**Prompt Ref:** `CT-PROD-RELEASE-MANIFEST-20260911-001` · **Date:** 2026-09-11
**Mode:** READ-ONLY / INSPECTION-ONLY (no stage, commit, push, reset, clean, migration, deploy or file change)
**HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (unchanged) · **Branch:** `main`
**Predecessor:** `CT-PROD-RELEASE-BOUNDARY-AUDIT-20260911-001`

## 1. Executive summary

The Release-1 file set **can now be staged safely** using explicit paths — every production
file has been identified **by name**, not by directory glob. Three findings materially
narrow the risk:

* `backend/api/router.py` **imports and mounts the new routers** (`api.v3_pe` line 52,
  `api.v3_context` line 62, `api.v3_health` line 63) → those files are co-commit mandatory.
* `backend/infra/ai_runtime.py` (untracked, brand-new) is **imported by production code**
  (`backend/services/automatic_processing.py:50`, `backend/workers/automatic_processing.py:162`)
  — a broad directory glob would have been needed to catch it; it is now named explicitly.
* The single deleted frontend source file (`frontend/src/StaffDashboard.jsx`) has **zero
  remaining imports**, so that deletion is safe (no build break).

Two items resist repository-only determination: the **live production migration state**
(no production credentials are used here, so all 17 migrations are `UNKNOWN` vs live), and
whether **`admin/src/**`** ships in Release 1 (evidence now strongly says yes — see §6).

## 2. R1-PROD — exact backend files (modified)

```
backend/main.py                       (app entrypoint)
backend/database.py                   (pool / connection handling)
backend/auth.py                       (auth wire behaviour)
backend/core/exceptions.py            (4xx/5xx mapping)
backend/api/router.py                 (mounts the new routers — MANDATORY co-commit)
backend/api/consultant_auth.py        (consultant authorization helper)
backend/api/v3_consultants.py         (consultant surface  + D7 provenance)
backend/api/v3_processing_workflow.py (approval → D6 charge; item lifecycle)
backend/api/v3_operations.py          (internal ops/QC)
backend/api/v3_qc.py                  (CT-QC decisions → D11 qc_outcome)
backend/api/v3_review.py              (review workflow)
backend/api/v3_messaging.py           (D8 conversations)
backend/api/v3_documents.py           (document/storage boundary)
backend/api/v3_manual_extraction.py   (manual extraction)
backend/api/v3_organizations.py       (organisation surface)
backend/api/v3_commercial.py          (commercial surface)
backend/api/v3_reporting.py           (reporting from persisted emissions)
backend/api/v3_automatic_processing.py(automatic processing entry)
backend/data/billing.py               ← THE P0-2 BILLING FIX (line 854)
backend/data/consultants.py           (firm provenance persistence)
backend/data/manual_extraction.py     (items/assignments/effective entity)
backend/data/notifications.py         (D11 durable notifications, event_key)
backend/data/messaging.py             (D8 conversations)
backend/data/audit.py                 (audit trail)
backend/data/document_processing.py   (document processing records)
backend/data/emissions_logs.py        (emissions persistence)
backend/data/tenant.py                (tenant scoping helpers)
backend/domain/billing.py             (entitlement/charge domain)
backend/domain/partners.py            (state machine + role vocab)
backend/domain/audit.py               (audit domain)
backend/domain/automatic_processing.py(automatic workflow domain)
backend/engines/calculation.py        (calculation engine)
backend/services/billing.py           (D6 entitlement gate + charge, +117 lines)
backend/services/automatic_processing.py (imports infra.ai_runtime)
backend/services/automatic_extraction.py (extraction orchestration)
backend/workers/automatic_processing.py  (imports infra.ai_runtime)
```

## 3. R1-PROD — exact backend files (new / untracked)

```
backend/api/v3_pe.py                  (PE workspace routes; imported by router.py:52)
backend/api/v3_context.py             (workspace context; imported by router.py:62)
backend/api/v3_health.py              (health endpoints; imported by router.py:63)
backend/api/pe_auth.py                (PE identity/capability gates incl. can_process)
backend/api/processing_mode.py        (manual/automatic mode predicates)
backend/api/audit_helpers.py          (audit write helpers)
backend/domain/processing_origin.py   (origin vocabulary: CARBONTALLY_INTERNAL / PROCESSING_ENTITY)
backend/infra/ai_runtime.py           (AI attribution/extraction engine — IMPORTED BY PRODUCTION)
backend/services/consultant_lifecycle.py (D11 five-event emitter)
backend/services/work_items.py        (item↔assignment effective-entity logic)
backend/services/ai_document_extraction.py (AI/OCR extraction)
```

## 4. Router dependency check (proved, not assumed)

* **Required for startup:** `router.py` + `v3_pe`, `v3_context`, `v3_health` (imported at
  lines 52/62/63) and their support modules `pe_auth`, `processing_mode`, `audit_helpers`.
  Importing any of these without `router.py` (or vice-versa) raises at import time.
* **Required for Phase-6 endpoints:** `v3_consultants`, `v3_processing_workflow`, `v3_qc`,
  `v3_messaging`, `v3_operations`, `v3_review`, `v3_reporting`, `v3_documents`,
  `v3_manual_extraction`, `v3_automatic_processing` (all modified in this working tree).
* **Outside the proposed set:** none — every router module touched by the Phase-6 delta is
  included above, plus the new `services/*`, `domain/*`, `data/*` and `infra/ai_runtime.py`.
* `backend/api/*` is **not** safe as a blanket glob (it also holds nothing unrelated, but the
  rule stands): the file list above is authoritative.

## 5. R1-PROD — frontend, deploy config and admin

**Frontend modified (R1):** `frontend/src/v3/consultant/ConsultantPage.jsx`,
`customer/{DocumentsPage,ProcessingPage,ReviewDetailPage,ReviewPage}.jsx`,
`ops/{AuditConsoleTab,ExtractionPanel,OperationsPage,OperatorItemPage,PEEntityItemPage,ReviewItemPage}.jsx`,
`reports/ReportsPage.jsx`, `frontend/src/v3/v3.css` (plus the further `M` entries captured in
the inventory under `frontend/src/v3/**`).

**Frontend new (R1):**
```
frontend/src/services/apiClient.js              shared API client (new runtime dependency)
frontend/src/v3/pe/PEShell.jsx                  PE workspace shell
frontend/src/v3/pe/PEDedicatedHome.jsx          PE home
frontend/src/v3/pe/PeWorkItemsPage.jsx          PE work queue
frontend/src/v3/pe/PeMessagingPage.jsx          PE operational messaging (D8)
frontend/src/v3/pe/PeNotificationsBell.jsx      notifications UI
frontend/src/v3/pe/pe.css
frontend/src/v3/ops/CtQcTab.jsx                 CT-QC console
frontend/src/v3/ops/OpsAssignmentsTab.jsx       assignment console
frontend/src/v3/ops/OpsPeMessagingTab.jsx       PE messaging console
frontend/src/v3/ops/v12.css
```

**Deploy config (R1):** `vercel.json` (M) · root `package.json` (M) · `backend/main.py` (M).

**Admin (`admin/src/**`, 60 entries) — R1, evidence-based (PO confirmation advised).**
`admin/package.json` declares `"name": "carbontally-admin"` with `"homepage": "/admin"`, and
the modified `vercel.json` carries explicit `/admin/*` route rules — the admin control-plane
app **is wired into the production deployment target**. It is the surface for customer
provisioning, subscription/allowance provisioning and entitlement/billing administration
(the P0-4 readiness gap); excluding it would leave no operational way to provision a paying
customer's entitlement.

## 6. Migration reconciliation (17 new)

Repository holds **53** migrations; **17 are untracked/new**. Live production state:
**UNKNOWN** — this environment has **no production Supabase credentials** and the task is
read-only, so no live comparison was performed and none is inferred.

| # | Migration | Purpose / objects | Phase | R1? |
|---|---|---|---|---|
| 1 | `20260831000000_v3m10_org_membership_unique.sql` | org-membership uniqueness | P6-1 | Yes |
| 2 | `20260831010000_v3m11_operational_indexes.sql` | operational indexes | P6-1 | Yes |
| 3 | `20260831020000_audit_activity_immutability.sql` | audit immutability | P6-1 | Yes |
| 4 | `20260831030000_tenant_org_id_not_null.sql` | tenant org_id NOT NULL | P6-1 | Yes |
| 5 | `20260831040000_consultant_revocation_roles.sql` | consultant revocation roles | P6-1 | Yes |
| 6 | `20260902020000_v1_2_dual_origin_workflow.sql` | dual-origin workflow | P6-2B | Yes |
| 7 | `20260902030000_phase5_work_item_assignments.sql` | **`public.work_item_assignments`** + 3 indexes | P6-2B/PE | **Yes — PE workspace authorizes against it** |
| 8 | `20260902040000_phase5_pe_operational_messaging.sql` | PE operational messaging | P6-2B | Yes |
| 9 | `20260902050000_phase5_notification_event_key.sql` | **`event_key`** + `ix_notifications_recipient_inbox` | D11 | **Yes — D11 deterministic keys** |
| 10 | `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | assignment foundation | WS4 | Yes |
| 11 | `20260905000000_gate4_actor_provenance.sql` | actor provenance | Gate 4 | Yes |
| 12 | `20260905010000_gate5_t1_automation_provenance.sql` | automation provenance | Gate 5 | Yes |
| 13 | `20260905020000_gate5_t6_automation_write_once_guard.sql` | write-once guard | Gate 5 | Yes |
| 14 | `20260906010000_gate6_w1_automation_extracted_output.sql` | extracted output | Gate 6 | Yes |
| 15 | `20260906090000_p6_1c_consultant_engagement.sql` | consultant engagement (D11 `accepted`) | P6-1C | Yes |
| 16 | `20260906100000_p6_2a_consultant_processing_permissions.sql` | consultant processing permissions | P6-2A | Yes |
| 17 | `20260910120000_p6_2d_consultant_provenance.sql` | consultant firm provenance (D7) | P6-2D | Yes |

**Required order (IF deployment is later authorized):** exactly 1 → 17 by numeric prefix
(`IF NOT EXISTS` style observed in the assignment migration). **All 17 are `UNKNOWN` vs live
production** and must be reconciled against the live migration history first.

## 7. Phase-6 production delta trace (file-level)

| Capability | Production files |
|---|---|
| **A. D6 entitlement + approval charge** | `services/billing.py`, `domain/billing.py`, `data/billing.py` (**P0-2 fix**), `api/v3_processing_workflow.py`, `api/v3_commercial.py` |
| **B. D7 provenance** | `domain/processing_origin.py` (new), `api/v3_consultants.py`, `api/v3_context.py`, `data/consultants.py`, migration 17 |
| **C. D8 conversations** | `api/v3_messaging.py`, `data/messaging.py`, `frontend/src/v3/ops/OpsPeMessagingTab.jsx`, `frontend/src/v3/pe/PeMessagingPage.jsx`, migration 8 |
| **D. D11 five events** | `services/consultant_lifecycle.py` (new), `data/notifications.py`, `api/v3_qc.py`, `api/v3_processing_workflow.py`, migration 9, `frontend/src/v3/pe/PeNotificationsBell.jsx` |
| **E. Processing-origin integrity** | `domain/processing_origin.py`, `api/processing_mode.py`, `engines/calculation.py`, migrations 6/12/13 |
| **F. Consultant workflow** | `api/v3_consultants.py`, `api/consultant_auth.py`, `data/consultants.py`, `frontend/src/v3/consultant/ConsultantPage.jsx`, migrations 15/16/17 |
| **G. PE workflow** | `api/v3_pe.py`, `api/pe_auth.py`, `services/work_items.py`, `data/manual_extraction.py`, `frontend/src/v3/pe/**`, migration 7 |
| **H. Billing / usage tracking** | `data/billing.py` (fix), `services/billing.py`, `data/tenant.py`, `database.py` |
| **I. Frontend routes/UI** | the `frontend/src/v3/**` files in §5 (`PEShell.jsx` → PE routes, `CtQcTab.jsx` → QC console, `OpsAssignmentsTab.jsx` → assignments) |

## 8. Billing fix confirmation

```
backend/data/billing.py  (M)   line 854
+   date_trunc('month', $2::timestamptz)::date, $3)     ← CURRENT implementation
-   VALUES ($1, $2, to_char($2, 'YYYY-MM'), $3)         ← removed
backend/services/billing.py  (M, +117 lines)  ← D6 gate + charge path
```
Every production file required by the D6 charge path: `data/billing.py`,
`services/billing.py`, `domain/billing.py`, `api/v3_processing_workflow.py`,
`data/tenant.py`, `database.py` (plus the already-present `usage_tracking` schema).

## 9. RELEASE-1-INCLUDE (exact)

```
backend/main.py, backend/database.py, backend/auth.py, backend/core/exceptions.py
backend/api/{router,consultant_auth,v3_consultants,v3_processing_workflow,v3_operations,
  v3_qc,v3_review,v3_messaging,v3_documents,v3_manual_extraction,v3_organizations,
  v3_commercial,v3_reporting,v3_automatic_processing}.py              (modified)
backend/api/{v3_pe,v3_context,v3_health,pe_auth,processing_mode,audit_helpers}.py (new)
backend/data/{billing,consultants,manual_extraction,notifications,messaging,audit,
  document_processing,emissions_logs,tenant}.py                      (modified)
backend/domain/{billing,partners,audit,automatic_processing}.py      (modified)
backend/domain/processing_origin.py                                  (new)
backend/engines/calculation.py
backend/services/{billing,automatic_processing,automatic_extraction}.py (modified)
backend/workers/automatic_processing.py                              (modified)
backend/infra/ai_runtime.py                                          (new — imported by production)
backend/services/{consultant_lifecycle,work_items,ai_document_extraction}.py (new)
supabase/migrations/20260831000000_*.sql … 20260910120000_*.sql       (17 new)
frontend/src/services/apiClient.js                                   (new)
frontend/src/v3/pe/{PEShell,PEDedicatedHome,PeWorkItemsPage,PeMessagingPage,
  PeNotificationsBell}.jsx + pe.css                                  (new)
frontend/src/v3/ops/{CtQcTab,OpsAssignmentsTab,OpsPeMessagingTab}.jsx + v12.css (new)
frontend/src/v3/consultant/ConsultantPage.jsx
frontend/src/v3/customer/{Documents,Processing,ReviewDetail,Review}Page.jsx
frontend/src/v3/ops/{AuditConsoleTab,ExtractionPanel,OperationsPage,OperatorItemPage,
  PEEntityItemPage,ReviewItemPage}.jsx
frontend/src/v3/reports/ReportsPage.jsx, frontend/src/v3/v3.css      (modified)
vercel.json, package.json                                            (deploy config)
admin/src/**                                                         (control plane — §5)
```

## 10. COMMIT-BUT-NOT-DEPLOY

`backend/tests/**` (incl. new `backend/tests/e2e/**`, `backend/tests/integration/**`),
`tests/e2e/**`, `qa_harness/{tests,browser,scripts,config}/**`, `e2e/environment/**`,
`docs/architecture/**` (60 new), `docs/cline/**` (69 new), `docs/audit/**`,
`docs/standalone/**`, `frontend/src/**/__tests__/**`, `frontend/src/DataSecurity.test.jsx`.

## 11. EXCLUDE-FROM-RELEASE-1

```
output/**                     (json/ · reports/ · sql/ — generated)
screenshots/**                (~80 evidence images)
agent_swarm_v2_artifacts/**   (85 generated screenshots)
qa_harness/evidence/**        (138)      qa_harness/reports/**   (55)
backend/test_results.json     test_results.json   test_results_all.json
v1.9.txt   v3_schema.sql      test_endpoints.py
__pycache__/  .pytest_cache/  node_modules/  test-results/  playwright-report/
.env*  .env.personas          ← SECRET / SENSITIVE — EXCLUDE (git-ignored; never commit)
.windsurf/skills/**  .claude/skills/**  .agents/skills/**  .clinerules/hooks/**
agent_swarm/**  saas-assurance/**  demodatagen/**  tools/**
the 152 tracked deletions     ← DEFAULT: keep; do not delete in Release 1
```

## 12. Tracked deletions (152)

| Family | Count | Classification |
|---|---|---|
| `.windsurf/skills/**` | 69 | R7 unrelated agent tooling → **exclude the deletion** |
| `.claude/skills/**` | 69 | R7 unrelated agent tooling → **exclude the deletion** |
| `output/{json,reports,sql}/**` | 13 | R5 generated → deletion acceptable but not required |
| `frontend/src/StaffDashboard.jsx` | 1 | **Safe to accept** — `grep` proves **zero remaining imports**; its removal cannot break the build |

No deletion is required by the production implementation.

## 13. PO-DECISION-REQUIRED

| Item | Question | If INCLUDE | If EXCLUDE | Recommended default | Evidence |
|---|---|---|---|---|---|
| `admin/src/**` | Does the control plane ship in Release 1? | Operators can provision customers/subscriptions/allowances (closes P0-4) | No in-product entitlement provisioning; SQL runbook needed | **INCLUDE** | `vercel.json` routes `/admin/*`; `admin/package.json` name `carbontally-admin`, homepage `/admin` |
| 152 deletions | Accept agent-tooling/output deletions? | Repo loses `.windsurf`/`.claude` skills | Tooling preserved; deletion deferred | **EXCLUDE the deletions** | No production dependency; `StaffDashboard.jsx` proven unimported |
| 17 migrations vs live | Already applied in production? | — | — | **Verify read-only, then apply 1→17** | No production credentials here → UNKNOWN |
| `saas-assurance/**`, `agent_swarm/**`, `demodatagen/**`, `tools/**` | P6 artifact or later-phase work? | Adds unrelated material | Stays out | **EXCLUDE** | Not referenced by any production module |

## 14. Release risk check

**P0** — billing fix omitted; `router.py` split from `v3_pe`/`v3_context`/`v3_health`
(startup failure); `git add -A` sweeping in 152 deletions; migrations applied out of order or
against unknown live state. **P1** — `backend/infra/ai_runtime.py` missed (imported by
production but outside the obvious `services/`/`api/` sets — **now named in §9**); E2E config
leaking into production config; ~400 generated artifacts; `frontend/.env` defaults still
pointing at the production Supabase project if the deployment env is not set explicitly.
**P2** — documentation volume; test-suite fragmentation.

## 15. Final answers

1. **Staged safely now?** → **YES**, using the explicit file lists in §9 (never a directory
   glob, never `git add -A`).
2. **Any production files hidden in broad classifications?** → **NO** — the risk case
   (`backend/infra/ai_runtime.py`) is now named explicitly.
3. **Billing fix fully contained?** → **YES** — `data/billing.py` line 854 + `services/billing.py`,
   `domain/billing.py`, `api/v3_processing_workflow.py`, `data/tenant.py`, `database.py`.
4. **All D6/D7/D8/D11 dependencies included?** → **YES** — file-level trace in §7A–§7I.
5. **Exact migrations required?** → **All 17** (§6), applied 1→17 after reconciling live state.
6. **Is `admin/src` required for the first customer?** → **YES (evidence-based)** — it is the
   provisioning surface for the P0-4 gap and already routed in `vercel.json`.
7. **Must NOT be committed?** → §11 (secrets, generated artifacts, evidence dumps, caches,
   unrelated tooling, and the deletions by default).
8. **Committed but never deployed?** → §10 (tests, E2E infra, `qa_harness`, `docs/**`,
   `e2e/environment/**`).
9. **PO decisions remaining?** → §13 (four items).
10. **Ready for a RELEASE-COMMIT prompt?** → **YES** — the manifest is file-level and
    complete; close the live-migration reconciliation and the two confirmations first.

## 16. Commands used (all read-only)

`git rev-parse HEAD` · `git log --oneline -6` · `git status --porcelain=v1`
(+ `grep`/`cut`/`awk`/`sort`/`uniq`) · `git ls-files --others --exclude-standard -- <paths>` ·
`git diff --stat` · `git diff -U2` · `git diff --cached --name-only` · `git check-ignore -v` ·
targeted `grep`/`head`/`ls` of `backend/api/router.py`, `backend/data/billing.py`,
`backend/infra/ai_runtime.py`, `admin/package.json`, `vercel.json`,
`supabase/migrations/*.sql`, and `frontend/src/StaffDashboard.jsx` import references.
**No mutating Git, database, migration or deployment command was executed.**

## 17. No-change confirmation

```
Repository modified by this task: NO  (documentation files only)
staged: 0   commit: NO   push: NO   reset: NO   clean: NO
migration applied: NO   database altered: NO   deployment: NO
E2E / RLS / fixtures / secrets: unchanged
HEAD: 16391217103b98dcea520070c5a22c68f12fe607 (unchanged)
```

## 18. Verdict

**RELEASE MANIFEST COMPLETE — READY FOR PO REVIEW AND A RELEASE-COMMIT PROMPT**

Two confirmations remain before committing: live migration reconciliation (needs read-only
production DB access) and the `admin/src/**` / deletion confirmations (§13). No verification,
release, deployment or production-readiness claim is made; P6-2F remains **NOT VERIFIED /
NOT CLOSED**.



