# CT-PROD-DEPLOYMENT-READINESS-20260911-001

**Prompt Ref:** `CT-PROD-DEPLOYMENT-READINESS-20260911-001` · **Datetime:** 2026-09-11
**Mode:** READ-ONLY Production Deployment Readiness Audit (no deploy, no migration, no DB change, no push)
**Repository:** CarbonTally · **Branch:** `main` · **Release-1 commit:** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
(`release: establish CarbonTally production release 1`)
**Deliverable:** `docs/architecture/CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md`

## 1. Release-1 commit verification

branch `main` · HEAD `daad396…` · message exact · 485 files changed / 111 289 insertions /
767 line-deletions · **0 file deletions inside the commit** · **17 migrations** present · billing fix
present (`git show HEAD:backend/data/billing.py` → `date_trunc('month', $2::timestamptz)::date`) ·
`backend/infra/ai_runtime.py` present · v3 admin/provisioning present (`/api/v3/commercial`,
`/api/v3/billing`, `frontend/src/v3/admin/**`) · **0 `.env` files in the commit** · no private
credential committed · one **publishable** Supabase key exists as an in-source frontend fallback
(value not reproduced; publishable by design) · staged = 0 · **no push**.

Migration inventory: **53 tracked** in `supabase/migrations/`; **36** at `HEAD~1`; **17 new in
Release-1**; 0 modified / 0 untracked migration files.

## 2. Production target findings

| Target | Finding |
|---|---|
| Supabase project | ref **`pvwiojoyaqywtydzcpbg`** identified from `supabase/.temp/project-ref` + `backend/supabase/.temp/project-ref` + frontend default |
| Supabase credentials | **UNKNOWN / NOT AVAILABLE** — every local `DATABASE_URL` is `127.0.0.1`; `SUPABASE_ACCESS_TOKEN`/`PGHOST`/`PGPASSWORD` unset |
| Backend | `PARTIAL` — `https://carbontally-api.onrender.com` (Render) from the CORS list; `runtime.txt` = `python-3.11.9`; **no `render.yaml`/`Procfile`/`Dockerfile`/`build.sh` in repo → build+start config UNKNOWN** |
| Frontend | `PARTIAL/UNKNOWN` — Vercel (`carbontally.co.uk`, `www.carbontally.co.uk`, `*-frontend.vercel.app`, `*-admin.vercel.app`); `vercel.json` present but **no buildCommand/outputDirectory**, and `frontend/build`/`admin/build` are git-ignored + uncommitted with no `public/` → rewrites unsatisfiable from the committed repo alone |
| Worker | `IDENTIFIED` — **no separate worker service**; in-process asyncio worker started by the FastAPI lifespan, DB-durable job state |
| Auth | Supabase Auth/GoTrue; committed config holds **localhost only** → production redirect/origin settings UNKNOWN |
| Storage | private `documents` bucket; **bucket creation not in any migration** (only `UPDATE storage.buckets`) |
| AI/OCR | `CARBONTALLY_AI_BASE_URL/_API_KEY/_MODEL` (optional, fail-closed); `pytesseract`+`pdf2image` need **system** `tesseract-ocr` + `poppler-utils` |
| Billing | **no external payment provider** in source; plan catalogue + commercial config are **migration-seeded** |
| Email | `RESEND_API_KEY` |

`PRODUCTION TARGET = PARTIALLY UNKNOWN` (reported, not guessed).

## 3. Migration reconciliation

**Live/read-only attempt:** `timeout 30 supabase migration list --linked < /dev/null` →
`unexpected login role status 544: Failed to create login role: Connection terminated due to
connection timeout`. **No production session was established**, so no production change was
possible. All 17 Release-1 migrations = **`REPOSITORY_ONLY`** (live `UNKNOWN`); the production delta
is **`UNKNOWN`** pending read-only production access.

**Local evidence proving history ≠ schema (the reason objects must be checked):**
dev `:54426` → 116 tables / 174 policies / **46 recorded migrations** / **4 non-canonical `version`
values** (`<version>_<name>.sql`, applied out-of-band); E2E `:55326` → 116 tables / **175 policies** /
**26 recorded migrations** (max recorded `20260822010000`).

## 4. Schema findings

Required object set enumerated per migration (org/membership unique index; consultant firms +
`can_*` capabilities + engagement/provenance columns; processing entities; grants;
`work_item_assignments`; `manual_extraction_items` origin/mode/provenance columns;
conversations/messages columns; notifications `event_key`+`actor_domain`+unique index; QC dual-origin
columns; all `billing*` + `customer_subscriptions` + `usage_tracking`; storage policies;
provenance/evidence + automation columns; audit immutability; operational indexes).
**Live status `UNKNOWN` for every item.** Drift risks to confirm in production:
`usage_tracking.usage_month` must be `date`; notifications unique event-key index;
`assets.org_id NOT NULL`; org-membership unique index; automation columns + write-once guard.
Locally verified (reference only): 116 tables, 174/175 policies, 7 049 `emission_factors`.

## 5. RLS / security findings

Production RLS **not inspectable** → all items `UNKNOWN`. Local reference: 116 tables with RLS
enabled; 174 (dev) / 175 (E2E) policies; migration DDL holds 21 `ENABLE ROW LEVEL SECURITY` and
68 `CREATE POLICY` statements. **No RLS altered, no policy created, no grant issued.** Production
action = verification only: confirm RLS on every tenant table, then re-run the negative matrix
(Customer A→B, Client A→B, Consultant A→B, Consultant A→B's client, PE A→B, PE→prohibited document,
Viewer→write, Member→admin, Staff→Staff Admin, Staff Admin→System Admin, Customer/PE→internal ops).

## 6. Environment / configuration findings

`REQUIRED 12` · `READY 4` · `UNKNOWN 4` · `BLOCKER-RISK 1`. Key items: `REACT_APP_API_URL`
(default `http://localhost:8000`), `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`, backend
`SUPABASE_URL`/service-role/JWT secret, `DATABASE_URL`, `RESEND_API_KEY`, `CARBONTALLY_AI_*`, OCR
system binaries, storage bucket, CORS, worker runtime, frontend/backend build config. CORS is
hard-coded (`backend/config.py`) and includes the ineffective literal `https://*.onrender.com`.
The frontend has hard-coded **production** fallbacks (`frontend/src/supabaseClient.js`) so a build
without env silently targets production.

## 7. Provisioning findings

Path traced (not executed): authorised admin → `/api/v3/commercial` (plans, subscriptions,
subscription status, credits grant/adjust/refund/reverse/rollover, orders + complete, entitlement,
config) + `/api/v3/billing` (assisted/managed orders, approve/cancel) → organisation →
`customer_subscriptions` → allowance/credits → entitlement (`/entitlement/{org}`) → D6 processing
gate (fail-closed `403 No active processing entitlement`). **Provisioning is possible without manual
SQL**; a temporary documented SQL fallback is acceptable, **copying demo rows is not**. Nothing was
created.

## 8. Demo-data classification

**A. NEVER MIGRATE** — every demo/test/customer-specific table (975 organisations, 1 125
memberships, 917 consultant-clients, 11 PEs, extraction items, notifications, conversations,
billing/usage rows, E2E personas/secrets, `local_backups/**`, `backups/**`).
**B. POSSIBLY REQUIRED REFERENCE DATA** — only the **emission-factor library** (7 049 rows) needs
loading, from the authoritative DEFRA source; `billing_plans`, `billing_commercial_config`,
`staff_roles` are **migration-seeded** and need no data migration.
**C. PRODUCTION-CREATED** — first org, users/memberships, firms/PEs, subscription, allowance,
assets, buckets, customer documents.
**D. UNKNOWN** — any live production row set.


## 9. Storage findings

The `documents` bucket must be **created** (the migration only flips it private and adds policies).
No committed binaries; local files are demo/E2E fixtures only. Nothing copied, uploaded or signed.

## 10. Billing findings

`customer_subscriptions` / `billing_credit_ledger` exist locally with **0 rows**; D6 entitlement
fail-closed implemented; the D6 approval-time charge is **fixed and committed**
(`date_trunc('month', $2::timestamptz)::date`); idempotency via `billing_idempotency_keys`;
`usage_tracking.usage_month` must be `date`; **no payment provider** (collection out-of-band).
Nothing charged; no subscription created.

## 11. OCR / AI findings

PDF parsing is ready in code; **OCR requires external system binaries** (`tesseract-ocr`,
`poppler-utils`) with no Dockerfile/build config in the repo → environment dependency; AI extraction
is optional/fail-closed; factor matching is **blocked by the missing factor-data path**; the
automatic-processing worker is durable with retries but requires an always-on runtime. No production
processing executed.

## 12. Backup / PITR findings

Production backups and PITR **`UNKNOWN`** (Supabase-managed; nothing in-repo); restore procedure,
migration recovery and recovery owner **NOT DEFINED** in the repository; only local dump artefacts
exist (`backups/*.dump`, `backups/seed.sql`, `backend/carbon_tally_backup*.sql`, `local_backups/**`).
No destructive restore test performed.

## 13. Monitoring findings

**No monitoring/alerting integration exists in the repository** (no Sentry/Rollbar/OTel/Prometheus/
Datadog). Application logging, platform logs and the audit trail are the only current visibility.
Minimum viable alerting (processing/billing/notification/auth) is a first-customer should-have.

## 14. Deployment sequence (documented only — 18 steps, none executed)

checkpoint/backup → establish read-only production access → reconcile all 53 migrations →
**verify schema objects (not just history)** → apply only the missing delta in order → **load the
emission-factor reference library** → create the private `documents` bucket → configure production
secrets → install OCR system binaries → deploy backend → deploy frontend → confirm the worker is
running → verify auth end-to-end → verify RLS + negative matrix → provision the first organisation
via `/api/v3/commercial` → controlled smoke test (upload → … → approve, incl. the D11 notification
and the D6 charge) → confirm backups/PITR + restore drill → enable alerting → monitor → release the
first customer.

## 15. Rollback findings

Git rollback is atomic (revert `daad396`), but **a code rollback loses the D6 billing fix and
reintroduces the approval 500** — unacceptable once traffic exists. Migrations are **forward-only
(no down-scripts; later migrations depend on earlier ones)** → migration rollback is effectively
irreversible; data rollback depends on the **unverified PITR** posture; billing reversals must go
through the commercial API, never ad-hoc SQL. Rollback is therefore **unsafe/incomplete by default**
and must be rehearsed on a copy before the first customer.

## 16. First-customer blockers

**MUST HAVE:** live reconciliation + delta apply (DR-01) · emission-factor load (DR-02) · production
secrets (DR-04) · object-level schema verification (DR-03) · backend+frontend deploy with working
build config (DR-05) · `documents` bucket (DR-08) · OCR binaries (DR-09) · provisioning path proven ·
RLS + negative matrix verified · one end-to-end processing proof · backups/PITR + restore drill
(DR-10) · rollback rehearsal (DR-13).
**SHOULD HAVE:** minimal alerting (DR-11) · env-driven CORS (DR-07) · remove frontend production
fallbacks (DR-06).
**CAN WAIT:** payment provider · repo hygiene (DR-12) · P6-2F evidence polish · Phase 7/8.


## 17. P6-2F boundary

P6-2F remains **NOT VERIFIED / NOT CLOSED** (the independent-verification report still carries
`NOT VERIFIED` on the DB/RLS-level rows and `IV-E2 — NOT CLOSED (BLK-2)` for live DB/RLS). Residual
gaps: browser-skip / D11-event / live-DB idempotency / fixture re-capture = **evidence gaps (E)**;
the D6 billing `to_char`/`usage_month` fix = **was a production defect, now fixed and committed**.
**No proven production defect remains open → no P6-2F residual is a launch blocker.** Not reopened;
no remediation performed.

## 18. Phase 7 / Phase 8 boundary

Phase 7 (Auditor/Assurance) and Phase 8 (Advanced Analytics): names PO-ratified, **scopes undefined,
nothing authorised**, **NOT required for the first controlled customer**. If launch claims use
*assurance/verified/audited* language, that is a **PO/business decision about the claims**, not an
implementation dependency. **Nothing implemented; no scope invented.**

## 19. Final verdict

**`DEPLOYMENT READINESS — READY WITH PREREQUISITES`**

**Git commit blocker: NONE.** The deployment blockers are prerequisites only (DR-01, DR-02, DR-04,
DR-03, DR-05, DR-08, DR-09) — none is an implementation defect in the Release-1 commit. The single
most material prerequisite is **DR-02: the emission-factor reference dataset is not reachable from a
clean Release-1 deployment path** (the 5.6 MB `output/sql/import_defra_2025.sql` factor set — 14 059
factor statements — sits inside the excluded `output/**` tree).

## 20. Explicit no-change confirmation

```text
Repository source modified: NO          (documentation files created by this audit ONLY)
Tests modified: NO
Migrations modified: NO
Git commit created: NO
Git push performed: NO
Production database altered: NO
Production migrations applied: NO
Production data created: NO
Demo data migrated: NO
Production deployment performed: NO
Secrets changed: NO
E2E environment changed: NO
```

**Read-only actions taken:** Git inspection; repository/config/documentation inspection; read-only
`psql` counts on the **local** stacks (`:54426`, `:55326`); and one attempted read-only
`supabase migration list --linked` which **failed at connection timeout with no session established**.
**No mutating Git, database, migration, deployment or data operation was performed at any point.**

