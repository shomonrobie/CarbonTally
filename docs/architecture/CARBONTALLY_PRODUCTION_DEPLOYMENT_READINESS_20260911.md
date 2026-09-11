# CarbonTally — Production Deployment Readiness Audit

**Prompt Ref:** `CT-PROD-DEPLOYMENT-READINESS-20260911-001` · **Mode:** READ-ONLY / INSPECTION-ONLY
**Date:** 2026-09-11 · **Repository:** CarbonTally · **Branch:** `main`
**Release-1 commit:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` — `release: establish CarbonTally production release 1`
**Predecessors:** `CT-PROD-READINESS-AUDIT` · `CT-PROD-RELEASE-BOUNDARY-AUDIT` · `CT-PROD-RELEASE-MANIFEST` · `CT-PROD-PRECOMMIT-GATE` · `CT-PROD-RELEASE-COMMIT(-CORRECTION)`
**Authority:** Blueprint V1.3, Master Roadmap V1.0, Release Manifest 20260911, Pre-Commit Gate 20260911, Readiness Audit 20260911, the Release-1 commit.

> No deployment, migration, database change, user/org/subscription creation, Git push or data
> migration was performed. Production credentials were never used. No secret value is reproduced
> in this report.

---

## 0. Executive verdict

**`DEPLOYMENT READINESS — READY WITH PREREQUISITES`**

* **No implementation blocker** was found in the committed code. The Release-1 commit is
  internally coherent: the billing fix, the router dependency closure, all 17 migrations and the
  v3 provisioning surface are present, and the commit contains **no `.env` file and no private
  credential**.
* Deployment **cannot proceed blind**. Live production migration state is `UNKNOWN` (no
  production credential exists in this environment; the read-only reconciliation attempt failed
  at connection), and several **deployment prerequisites** must be executed deliberately before
  serving traffic — the most material being the **emission-factor reference dataset**, which is
  *not* reachable from a clean Release-1 deployment path.

Nothing here reopens P6-2F, Phase 7 or Phase 8.

---

## 1. Release-1 commit verification (read-only)

| Check | Result |
|---|---|
| branch | `main` |
| HEAD | `daad396523ac693352cc2f4ebb7fc58814a9e60b` |
| commit message | `release: establish CarbonTally production release 1` (exact) |
| commit stat | 485 files changed, 111 289 insertions(+), 767 deletions(-) — **0 file deletions inside the commit** (`git show --diff-filter=D` = **0**) |
| migrations in commit | **17** (verified by name) |
| billing fix in commit | **PRESENT** — `git show HEAD:backend/data/billing.py` contains `date_trunc('month', $2::timestamptz)::date` |
| `backend/infra/ai_runtime.py` in commit | **PRESENT** |
| v3 admin/provisioning in commit | **PRESENT** — `backend/api/v3_commercial.py` (`/api/v3/commercial`, plans/subscriptions/orders/credits/entitlement/config), `backend/api/v3_billing.py` (`/api/v3/billing`), `frontend/src/v3/admin/**`, `frontend/src/v3/customer/BillingPage.jsx` |
| `.env` / private credentials in commit | **0** (`git show --name-only HEAD \| grep -E '(^|/)\.env'` = 0) |
| publishable key in source | 1 **publishable** (browser-class) Supabase key as an in-source fallback in `frontend/src/supabaseClient.js` — see DR-06. Not a private-secret disclosure; RLS is the security boundary. Value not reproduced. |
| working tree after commit | `73 ?? · 152 D · 209 M`; staged = 0; the 152 excluded deletions remain **outside** the commit |
| push | **NOT PERFORMED** (`main…origin/main [ahead 29]`) |

**Migrations added by Release-1** (the release delta — 17 files, ordered):

```
20260831000000_v3m10_org_membership_unique.sql              UNIQUE index (org membership)
20260831010000_v3m11_operational_indexes.sql                 operational indexes
20260831020000_audit_activity_immutability.sql               immutability guard (functions/triggers)
20260831030000_tenant_org_id_not_null.sql                    assets.org_id NOT NULL
20260831040000_consultant_revocation_roles.sql               consultant revocation/role vocabulary
20260902020000_v1_2_dual_origin_workflow.sql                 manual_extraction_items + processing_origin,
                                                             processing_entity_id, pe_qc_*, pe_reviewed_*
20260902030000_phase5_work_item_assignments.sql              CREATE TABLE work_item_assignments (+ unique idx)
20260902040000_phase5_pe_operational_messaging.sql           conversations/messages + conversation_kind,
                                                             context, processing_entity_id
20260902050000_phase5_notification_event_key.sql             notifications + event_key, actor_domain (+ unique idx)
20260903010000_ws4_gate3_4a_item_assignment_foundation.sql   item-assignment foundation
20260905000000_gate4_actor_provenance.sql                    calculation_snapshots + performed_by
20260905010000_gate5_t1_automation_provenance.sql            document_processing_queue + automation_provider/model/version
20260905020000_gate5_t6_automation_write_once_guard.sql      write-once automation guard
20260906010000_gate6_w1_automation_extracted_output.sql      document_processing_queue + automation_extracted_data
20260906090000_p6_1c_consultant_engagement.sql               consultant_clients + relationship_origin, engagement_*
20260906100000_p6_2a_consultant_processing_permissions.sql   consultant_firm_members + can_extract/map/validate/
                                                             calculate/submit/confirm_automation
20260910120000_p6_2d_consultant_provenance.sql               manual_extraction_items + consultant_firm_id,
                                                             consultant_provenance_at, processing_mode
```

**Repository migration inventory:** 53 files tracked in `supabase/migrations/`; 36 existed at
`HEAD~1`, **17 are new in Release-1**. Working-tree migration files: 0 modified, 0 untracked.

## 2. Production targets

| Target | Determination | Evidence (no secrets) |
|---|---|---|
| **Production Supabase project** | `IDENTIFIED (ref only)` — project ref **`pvwiojoyaqywtydzcpbg`** | `supabase/.temp/project-ref`; `backend/supabase/.temp/project-ref`; frontend default. No production credential is stored in this environment |
| Production Supabase credentials | **UNKNOWN / NOT AVAILABLE** | every local `DATABASE_URL` points at `127.0.0.1` (dev `:54426`, root `:54326`); `SUPABASE_ACCESS_TOKEN`, `PGHOST`, `PGPASSWORD` all unset → live reconciliation failed at connection (§3) |
| **Backend target** | `PARTIAL` — `https://carbontally-api.onrender.com` (Render) | CORS allow-list `backend/config.py:23-35`; `runtime.txt` = `python-3.11.9`. **No `render.yaml`, `Procfile`, `Dockerfile`, `build.sh` or `nixpacks.toml` exists in the repository** → build/start commands and instance topology are **UNKNOWN** (external Render config) |
| **Frontend target** | `PARTIAL / UNKNOWN` — Vercel (consumer domains `carbontally.co.uk`, `www.carbontally.co.uk`) | `vercel.json` present. **`vercel.json` declares no `buildCommand`/`outputDirectory`, and `frontend/build` + `admin/build` are git-ignored and uncommitted (0 tracked files) with no `public/` tree present** → the rewrites (`/frontend/index.html`, `/admin/index.html`) cannot be satisfied from the committed repository alone. Frontend deploy settings are external/UNKNOWN (DR-05) |
| **Worker / runtime target** | `IDENTIFIED` — **no separate worker service**: the automatic-processing worker is an **in-process asyncio loop started by the FastAPI lifespan**, with durable job state in PostgreSQL | `backend/main.py` (lifespan) + `backend/workers/automatic_processing.py` (job state in DB; resumes on restart; never blocks startup) |
| Required API URL(s) | `REACT_APP_API_URL` (default `http://localhost:8000`) | `frontend/src/v3/api.js:7`, `frontend/src/services/apiClient.js` |
| Required Supabase URL(s) | `REACT_APP_SUPABASE_URL` (frontend) + `SUPABASE_URL` (backend) | `frontend/src/supabaseClient.js`; backend `Config` |
| Required auth configuration | Supabase Auth (GoTrue), single identity system | Blueprint V1.3 §4.1. Committed `supabase/config.toml` holds **local** values only (`site_url=http://localhost:3000`, `additional_redirect_urls=["https://localhost:3000"]`) → **production auth/redirect/origin settings = UNKNOWN** (Supabase dashboard) |
| Required storage configuration | Supabase Storage, **private** `documents` bucket + policies | `d32_private_documents_storage.sql` **only UPDATEs** `storage.buckets SET public=FALSE WHERE name='documents'` → bucket creation is **not** in the migration (DR-08) |
| Required AI configuration | `CARBONTALLY_AI_BASE_URL`, `CARBONTALLY_AI_API_KEY`, `CARBONTALLY_AI_MODEL` (env only; fail-closed when unset) | `backend/infra/ai_runtime.py:49-51, :119-120` |
| Required OCR configuration | **System binaries** `tesseract-ocr` (+ `poppler-utils` for `pdf2image`) | `backend/requirements.txt` (`pytesseract`, `pdf2image`, `pdfplumber`, `Pillow`) used by `backend/pdf_engine.py`, `backend/api/v3_documents.py`, `backend/routes/upload.py` |
| Required billing configuration | **No external payment provider** — internal ledger only | no Stripe/PayPal/GoCardless/Braintree reference in backend source; plan catalogue + commercial config are **migration-seeded** (§11) |
| Required email configuration | `RESEND_API_KEY` (+ `FOUNDER_EMAIL`) | `backend/config.py` |

> `PRODUCTION TARGET = PARTIALLY UNKNOWN`. The Supabase project ref and backend hostname are
> established from repository configuration; the backend build/start config, frontend build/output
> config, production auth/redirect settings, production secrets, backup/PITR settings and the
> production migration state **cannot be established safely from the repository and are reported
> `UNKNOWN` rather than guessed.**


## 3. Live Supabase migration reconciliation (highest-priority check)

**Attempted, read-only, and unsuccessful — no production session was established.**

```
timeout 30 supabase migration list --linked < /dev/null
  → unexpected login role status 544: Failed to create login role:
    Connection terminated due to connection timeout
```

The CLI is linked (`supabase/.temp/project-ref`) but no production DB credential/access token is
present in this environment. The attempt failed **before** any session existed → **no production
change was possible and none occurred.**

### 3.1 Production reconciliation table

All 17 Release-1 migrations are `REPOSITORY_ONLY` (present in the repository; live state not
inspectable). Per-migration status:

| # | Migration | Repo | Live | Status |
|---|---|---|---|---|
| 1 | `20260831000000_v3m10_org_membership_unique` | ✔ | not inspected | `UNKNOWN` |
| 2 | `20260831010000_v3m11_operational_indexes` | ✔ | not inspected | `UNKNOWN` |
| 3 | `20260831020000_audit_activity_immutability` | ✔ | not inspected | `UNKNOWN` |
| 4 | `20260831030000_tenant_org_id_not_null` | ✔ | not inspected | `UNKNOWN` |
| 5 | `20260831040000_consultant_revocation_roles` | ✔ | not inspected | `UNKNOWN` |
| 6 | `20260902020000_v1_2_dual_origin_workflow` | ✔ | not inspected | `UNKNOWN` |
| 7 | `20260902030000_phase5_work_item_assignments` | ✔ | not inspected | `UNKNOWN` |
| 8 | `20260902040000_phase5_pe_operational_messaging` | ✔ | not inspected | `UNKNOWN` |
| 9 | `20260902050000_phase5_notification_event_key` | ✔ | not inspected | `UNKNOWN` |
| 10 | `20260903010000_ws4_gate3_4a_item_assignment_foundation` | ✔ | not inspected | `UNKNOWN` |
| 11 | `20260905000000_gate4_actor_provenance` | ✔ | not inspected | `UNKNOWN` |
| 12 | `20260905010000_gate5_t1_automation_provenance` | ✔ | not inspected | `UNKNOWN` |
| 13 | `20260905020000_gate5_t6_automation_write_once_guard` | ✔ | not inspected | `UNKNOWN` |
| 14 | `20260906010000_gate6_w1_automation_extracted_output` | ✔ | not inspected | `UNKNOWN` |
| 15 | `20260906090000_p6_1c_consultant_engagement` | ✔ | not inspected | `UNKNOWN` |
| 16 | `20260906100000_p6_2a_consultant_processing_permissions` | ✔ | not inspected | `UNKNOWN` |
| 17 | `20260910120000_p6_2d_consultant_provenance` | ✔ | not inspected | `UNKNOWN` |

**The exact production migration DELTA cannot be stated without read-only production credentials.**
This remains a **deployment prerequisite** (as recorded by the Pre-Commit Gate).

### 3.2 Local reconciliation — proof that history alone is NOT authoritative

| Stack | `public` tables | RLS policies | `schema_migrations` rows | max recorded version | malformed `version` values |
|---|---|---|---|---|---|
| Local dev (`:54426`) | 116 | 174 | **46** | `20260903010000_ws4_…` | **4** (`<version>_<name>.sql` — applied out-of-band) |
| Isolated E2E (`:55326`) | 116 | **175** | **26** | `20260822010000` | 0 |

**Finding:** the E2E stack physically contains 116 tables and 175 policies — the schema of the
*later* migrations — while its history records only **26** migrations and stops at `20260822010000`;
the dev stack holds 4 non-canonical version strings. **Migration history is therefore not a
reliable proxy for applied schema in this project**, so production reconciliation MUST verify
*objects* (§4), not only history. See DR-03.


## 4. Production schema health (objects required by Release-1)

Live production schema was **not** inspected (no credential). The required object set is enumerated
from the Release-1 delta and must be verified object-by-object in production.

| Domain | Required objects | Source migration(s) | Live |
|---|---|---|---|
| organisations / memberships | `organizations`, `organization_members` + **unique** membership index | `v3m10` | `UNKNOWN` |
| consultant profiles / firms | `consultant_profiles`, `consultant_firms`, `consultant_firm_members` (+ capability cols), `consultant_clients` (+ engagement/provenance cols) | `p6_1c`, `p6_2a`, `p6_2d`, `consultant_revocation_roles` | `UNKNOWN` |
| processing entities | `processing_entities`, `entity_relationships`, `staff_roles` | `v3m1`, `v3m2`, `v3m8_pe_manager_role` | `UNKNOWN` |
| grants / capabilities | consultant→client grant structures; `can_extract/map/validate/calculate/submit/confirm_automation` | `d20_d15_active_consultant_grant`, `p6_2a` | `UNKNOWN` |
| work items / assignments | `work_item_assignments` (table + unique index) | `phase5_work_item_assignments` | `UNKNOWN` |
| processing mode / origin / consultant provenance | `manual_extraction_items`: `processing_origin`, `processing_entity_id`, `processing_mode`, `consultant_firm_id`, `consultant_provenance_at`, `pe_qc_*`, `pe_reviewed_*` | `v1_2_dual_origin_workflow`, `p6_2d` | `UNKNOWN` |
| conversations / messaging | `conversations`, `messages` + `conversation_kind`, `context`, `processing_entity_id` | `phase5_pe_operational_messaging` | `UNKNOWN` |
| notifications / event keys | `notifications` + `event_key`, `actor_domain` + **unique** event-key index | `phase5_notification_event_key` | `UNKNOWN` |
| QC structures | dual-origin QC columns; `ct_qc_approved` lifecycle; QC decision records | `v1_2_dual_origin_workflow`, `v3_qc` | `UNKNOWN` |
| subscriptions / allowances / entitlements | `customer_subscriptions`, `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`, `billing_idempotency_keys` | `d37_0`, `d37` | `UNKNOWN` |
| usage tracking (D6) | `usage_tracking` with `usage_month` of type **`date`** | `d37_0` (consumed by `backend/data/billing.py:845-856`) | `UNKNOWN` |
| storage-related structures | `storage.buckets` (`documents`, private) + storage RLS policies | `d32_private_documents_storage` | `UNKNOWN` |
| provenance / evidence | `calculation_snapshots` (+`performed_by`), `document_processing_queue` (+automation cols), evidence tables | `gate4`, `gate5_t1`, `gate6_w1`, `d33` | `UNKNOWN` |
| audit immutability | audit/activity immutability guards & functions | `audit_activity_immutability` | `UNKNOWN` |
| operational indexes | the `v3m11` operational indexes | `v3m11` | `UNKNOWN` |

**Locally verified as present (reference only — NOT a production claim):** 116 `public` tables,
174 (dev) / 175 (E2E) RLS policies, `usage_tracking`, all `billing*` tables, `work_item_assignments`,
`customer_subscriptions`, `emission_factors` (7 049 rows).

**Schema-drift risks to confirm in production:** (a) `usage_tracking.usage_month` must be `date`
(the D6 fix casts `date_trunc(...)::date`; a non-`date` column previously produced a 500);
(b) the `notifications` unique event-key index; (c) `assets.org_id NOT NULL`;
(d) the organisation-membership unique index; (e) `document_processing_queue` automation columns
and the write-once guard.

---

## 5. RLS / security production check

Production RLS could **not** be inspected (no credential) → **all items `UNKNOWN`**.

| Check | Local evidence (reference) | Production |
|---|---|---|
| RLS enabled on tenant tables | 116 `public` tables with RLS enabled (dev + E2E) | `UNKNOWN` |
| Policies exist | 174 (dev) / 175 (E2E) `public` policies | `UNKNOWN` |
| Migration-level policy DDL | 21 `ENABLE ROW LEVEL SECURITY` + 68 `CREATE POLICY` statements across the 53 migration files | — |
| Organisation isolation | Verified in the P6-2F isolated stack (PostgREST + real JWTs: cross-org = **200 with 0 rows**) — historical evidence, **not a production claim** | `UNKNOWN` |
| Consultant firm isolation / PE isolation / internal ops access / capability + entitlement enforcement | Application-level boundary 16/16 in the isolated stack (historical) | `UNKNOWN` |

**No RLS was altered, no policy created and no grant issued by this task.** The production action
is **verification only**: confirm RLS is enabled on every tenant table and that policies match the
migration set, then re-run the negative security matrix (Customer A→B, Client A→B, Consultant A→B,
Consultant A→B's client, PE A→B, PE→prohibited document, Viewer→write, Member→admin, Staff→Staff
Admin, Staff Admin→System Admin, Customer→internal ops, PE→internal ops) against production.


## 6. Production authentication

| Item | State | Note |
|---|---|---|
| Supabase Auth as single identity system | `READY (architecture)` | Blueprint V1.3 §4.1; GoTrue local container observed in both local stacks |
| Backend authentication | `REQUIRED` | backend validates Supabase-issued JWTs; requires `SUPABASE_URL`, `SUPABASE_ANON_KEY`/service key and `SUPABASE_JWT_SECRET` (names present in `backend/.env`) |
| Frontend Supabase configuration | `REQUIRED` | `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY` (see DR-06: production fallbacks are hard-coded) |
| Redirect / callback / allowed-origin URLs | `UNKNOWN` | committed config carries **localhost** values only; production values live in the Supabase dashboard |
| Email/password + Google OAuth + TOTP MFA | `READY (architecture)`; production policy for MFA `UNKNOWN` | local config shows `enable_signup=true`, `minimum_password_length=6`; production enforcement is a separate policy decision |
| Email delivery for auth | `REQUIRED` | `RESEND_API_KEY` configured for application email; Supabase Auth SMTP is a dashboard setting → `UNKNOWN` |

No users were created. Required production configuration is identified **by name only**.

---

## 7. Production environment configuration checklist

Never-printed values; state is presence/absence plus repository evidence.

| Variable / config | Required? | Current state | Action |
|---|---|---|---|
| `REACT_APP_API_URL` | Yes | `REQUIRED` — default `http://localhost:8000` in source | set to the production API origin at build time |
| `REACT_APP_SUPABASE_URL` | Yes | `REQUIRED` — source fallback = production project (DR-06) | set explicitly at build time |
| `REACT_APP_SUPABASE_ANON_KEY` | Yes | `REQUIRED` — source fallback = publishable key (DR-06) | set explicitly; keep RLS as the boundary |
| backend `SUPABASE_URL` | Yes | `REQUIRED` (name present in env files; no production value) | set in Render env |
| backend service-role credential (`SUPABASE_SERVICE_KEY` / `SUPABASE_SERVICE_ROLE_KEY`) | Yes | `REQUIRED` — **server-side only**; must never reach the frontend bundle | set as a secret in Render; rotate the key that appeared in local files |
| backend `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` | Yes | `REQUIRED` | set as secrets |
| `DATABASE_URL` | Only if used directly | `READY (local)` / `REQUIRED (prod)` | local values are `127.0.0.1`; production pooling connection TBD |
| `RESEND_API_KEY` | Yes | `REQUIRED` | set as secret |
| `CARBONTALLY_AI_BASE_URL` / `_API_KEY` / `_MODEL` | Conditional | `REQUIRED` **only if** AI extraction is enabled; fail-closed when unset | PO decision + set if enabled |
| OCR system binaries (`tesseract-ocr`, `poppler-utils`) | Yes | `BLOCKER-RISK` — not expressible in `requirements.txt`; **no `Dockerfile`/render build config in repo** | install at image/build level and verify in production (DR-09) |
| Billing provider configuration | No (internal ledger) | `READY (n/a)` | none — payment collection is out-of-band (§11) |
| Storage configuration | Yes | `REQUIRED` — `documents` bucket must exist and be private | create bucket + verify policies (DR-08) |
| CORS (`Config.ALLOWED_ORIGINS`) | Yes | `PARTIALLY READY` — production domains already listed, **but hard-coded in source and includes `https://*.onrender.com` which Starlette matches literally (ineffective)** | make env-driven; remove/replace the wildcard (DR-07) |
| Worker configuration | Yes | `READY (architecture)` — in-process worker; no separate service | ensure the API instance is always-on (worker stops when the API sleeps) |
| Frontend build config (build command / output dir) | Yes | `UNKNOWN` — not in `vercel.json` | define in the Vercel project (DR-05) |
| Backend build/start config | Yes | `UNKNOWN` — no `render.yaml`/`Procfile`/`Dockerfile` | define in the Render service (DR-02/DR-09) |

Class summary: `READY 4` · `REQUIRED 12` · `UNKNOWN 4` · `BLOCKER-RISK 1`.


## 8. Production provisioning path

Traced from the committed code (no provisioning performed):

```
Admin/Ops user (Supabase Auth identity, authorised role)
   │
   ├─ POST /api/v3/commercial/plans                (plan catalogue; migration-seeded defaults)
   ├─ POST /api/v3/commercial/subscriptions        (create subscription for an organisation)
   ├─ POST /api/v3/commercial/subscriptions/{id}/status
   ├─ POST /api/v3/commercial/credits/grant        (allowance / credit grant)
   ├─ POST /api/v3/commercial/credits/{adjust|refund|reverse|rollover}
   ├─ POST /api/v3/commercial/orders{,/{id}/complete}
   ├─ GET  /api/v3/commercial/entitlement/{organization_id}   (verify entitlement)
   ├─ GET/PUT /api/v3/commercial/config{,/{config_key}}        (commercial configuration)
   └─ GET  /api/v3/commercial/overview | ledger | organizations | payments | storage
Customer self-service:
   ├─ POST /api/v3/billing/orders/assisted | /managed/orders
   └─ POST /api/v3/billing/orders/{id}/approve | /cancel
```

* **Surface:** `/api/v3/commercial` + `/api/v3/billing` (backed by `frontend/src/v3/admin/**` and
  `frontend/src/v3/customer/BillingPage.jsx`).
* **Path to first customer:** create organisation → membership/users (Supabase Auth + membership
  rows) → subscription (`customer_subscriptions`) → allowance/credits → entitlement verified via
  `/entitlement/{org}` → processing permitted (D6 fail-closed `403 No active processing
  entitlement` until an active subscription/allowance exists).
* **Can this be done safely in production?** **Yes, through the API surface** — *provided* the
  Release-1 migrations are applied and the operator holds an authorised internal/admin role. No
  manual SQL is required for the normal path.
* **Manual-SQL fallback:** if the commercial API is unavailable on day 1, a **temporary,
  controlled, documented** provisioning procedure (single organisation + subscription + allowance,
  executed by an authorised operator and recorded in the audit trail) is acceptable — but
  **copying local demo rows is not.**
* **Not performed:** no organisation, subscription, allowance, credit, user or membership was
  created by this audit.

---

## 9. Demo data / reference data classification

Local inventory (read-only, dev stack `:54426`): 975 organisations · 1 125 org members ·
54 consultant-firm members · 917 consultant_clients · 11 processing entities · 260 extraction items ·
34 conversations · 52 messages · 7 049 emission factors · 6 billing-plan rows · 0 usage/credit/order
rows. This is the **investor demo** dataset (≈1 185 identities) and is test infrastructure.

### A. NEVER MIGRATE (demo / test / customer-specific — default for all local data)

`organizations`, `organization_members`, `users`, `auth.*` (identities, sessions),
`consultant_profiles`/`consultant_firms`/`consultant_firm_members`/`consultant_clients`,
`processing_entities`, `staff_profiles`/`staff_roles` assignments, grants/capabilities,
`manual_extraction_*`, `work_item_assignments`, `document_processing_queue`, `notifications`,
`conversations`, `messages`, `calculation_snapshots`, `emissions_logs`, `customer_subscriptions`,
`billing_orders`, `billing_credit_ledger`, `usage_tracking`, `billing_payment_records`,
`billing_idempotency_keys`, `billing_storage_usage`, `facilities`/`assets`/`vehicles`/`suppliers`,
all E2E personas/secrets/fixtures, and every local file in `local_backups/**`, `backups/**`.

### B. POSSIBLY REQUIRED REFERENCE DATA (only with explicit PO approval)

| Table | Purpose | Example record type | Why production requires it | Recreatable? | Migration actually necessary? |
|---|---|---|---|---|---|
| `emission_factors` (+ `factor_aliases`) | Factor matching / calculation | DEFRA 2025 factor rows (7 049 locally) | **Cannot map or calculate without factors** | Yes — from the authoritative DEFRA source | **YES — REQUIRED** (see DR-02) |
| `billing_plans` | Commercial plan catalogue | starter/business/professional/enterprise | Subscription/allowance creation | Yes — **already seeded by migration** (`d37_0`, `d37`) | **No** — arrives with migrations |
| `billing_commercial_config` | Commercial configuration defaults | config key/value defaults | Entitlement/billing behaviour | Yes — **migration-seeded** | **No** |
| `staff_roles` | Role vocabulary | role keys incl. PE manager | Role/capability resolution | Yes — **migration-seeded** (`v3m8_pe_manager_role`) | **No** |

**Conclusion:** the only reference-data class that must be *loaded* beyond migrations is the
**emission-factor library**. Everything else in class B is delivered by the migrations themselves.

### C. PRODUCTION-CREATED (deliberate provisioning)

First customer organisation · its users/memberships · consultant firm (if applicable) ·
processing entity (if applicable) · subscription · allowance/credits · facilities/assets/vehicles ·
storage buckets/objects · all customer documents and emissions data.

### D. UNKNOWN

Any live production row set (no credential). Nothing in the local database is assumed to be
production-required.


## 10. Storage / file data

| Item | Finding |
|---|---|
| Local Supabase Storage containers | present (`supabase_storage_*` for both local stacks) |
| Committed local files | none — `frontend/build`, `admin/build` are git-ignored; no `public/`; no storage objects are committed |
| Local file population | demo fixtures / E2E fixtures / generated artifacts only |
| Production-required reference **assets** | only the bucket definition + policies (no binary assets required) |
| Bucket provisioning | **NOT in a migration** — `d32` performs `UPDATE storage.buckets SET public=FALSE WHERE name='documents'` + policies, which **assumes the `documents` bucket already exists** → must be created explicitly in production (DR-08) |
| Authorization model | private bucket + server-side authorization + short-lived signed URLs; PE source-document access is browser-based and download-restricted (Blueprint V1.3 §4.4/§8) |

**No file was copied, uploaded, downloaded or signed by this audit.**

---

## 11. Billing / entitlement readiness

| Prerequisite | Status | Evidence |
|---|---|---|
| `customer_subscriptions` | `UNKNOWN (prod)`; table exists locally; **0 rows** locally | `d37_0`; local count 0 |
| Allowances / credits | `UNKNOWN (prod)`; `billing_credit_ledger` exists; **0 rows** locally | `d37` |
| Entitlement enforcement (D6) | `READY (code)` — fail-closed: `403 No active processing entitlement` when no active subscription | `/api/v3/commercial/entitlement/{org}`; readiness-audit evidence (historical, non-prod) |
| Usage tracking | `READY (code)` — `usage_tracking` written on approval | `backend/data/billing.py:845-856` |
| D6 approval-time consumption (**the Release-1 P0-2 fix**) | `FIXED & COMMITTED` — `date_trunc('month', $2::timestamptz)::date` | `git show HEAD:backend/data/billing.py` |
| Billing idempotency | `READY (code)` — `billing_idempotency_keys` | `backend/data/billing.py` (`IdempotencyRepository`) |
| Usage-month schema | `UNKNOWN (prod)` — must be `date` | drift risk §4 |
| Billing provider configuration | **None required** — no PSP integration exists; payment collection is out-of-band | no Stripe/PayPal/etc. in source |
| Plan catalogue + commercial config | `READY (delivered by migrations)` | `billing_plans` (6 rows locally), `billing_commercial_config` |

**Before the first customer can process data:** an active subscription + allowance/credit must
exist for the organisation, and `usage_tracking.usage_month` must be a `date` column. **No
subscription was created and nothing was charged.**

---

## 12. OCR / AI / automatic processing

| Component | Requirement | Status |
|---|---|---|
| PDF ingestion | `pdfplumber`, `pypdf2` (pure-Python) | `READY (code)` |
| Scanned PDF/image OCR | `pytesseract` **+ system `tesseract` binary**; `pdf2image` **+ `poppler`** | `REQUIRED — environment dependency` (**DR-09**); no `Dockerfile`/build config in repo |
| AI document extraction | `CARBONTALLY_AI_BASE_URL/API_KEY/MODEL`; **optional and fail-closed** when unset | `REQUIRED (conditional)` |
| Factor matching | DB factor library (`emission_factors`) | **`REQUIRED` — factor data not in a clean release path** (**DR-02**) |
| Automatic processing worker | in-process asyncio loop, DB-durable job state, resume on restart | `READY (code)` — needs an always-on runtime |
| Retries / failures / dead-letter | durable job state with attempt/error fields | `READY (code)` |
| Storage access for processing | service-role/signed access to the private bucket | `REQUIRED` (bucket + secret) |
| External service dependencies | AI provider endpoint (optional) | `UNKNOWN` |

**No production processing was executed.**

---

## 13. Backup / PITR / disaster recovery

| Item | Status |
|---|---|
| Production backups | **`UNKNOWN`** — Supabase-managed; no backup configuration or schedule exists in the repository |
| PITR availability | **`UNKNOWN`** — Supabase plan-dependent; not verifiable from the repository |
| Restore procedure | **`NOT DEFINED`** in the repository (only local dump scripts/artefacts: `backups/*.dump`, `backend/carbon_tally_backup*.sql`, `local_backups/**`) |
| Migration recovery strategy | **`NOT DEFINED`** — and complicated by DR-03 (history ≠ schema) |
| Rollback strategy | partially defined conceptually (§16); not rehearsed |
| Recovery owner / process | **`NOT DEFINED`** in-repo |

**Local-only backup artefacts (never to be used in production, never migrated):**
`backups/carbontally_v3_verified_2026-08-14.dump`, `backups/seed.sql`, `backups/source_factors`,
`backups/v3_verified_factor_baseline.txt`, `backend/carbon_tally_backup.sql`,
`backend/carbon_tally_backup_data.sql`, `local_backups/**`.
No destructive restore test was performed.

---

## 14. Monitoring / alerting

| Area | Current | Missing |
|---|---|---|
| Backend errors | application logging only | error tracking/alerting (**no Sentry/Rollbar/OTel/Prometheus dependency exists in the repo**) |
| Worker failures | in-DB job state + logs | alerting on failed/dead-letter jobs |
| Auth failures | GoTrue logs (platform) | alerting |
| Billing failures | application logs | alerting on charge/entitlement errors |
| Processing failures | durable job state | alerting |
| Storage failures | platform | alerting |
| OCR/AI failures | fail-closed logs | alerting |
| Database failures | platform | alerting |
| Suspicious authorization failures | audit trail rows | alerting/triage |

**Conclusion: no monitoring or alerting integration exists in the repository.** Minimum viable
alerting (processing/billing/notification failures + auth error spike) is a **first-customer
prerequisite** (DR-11).


## 15. Deployment architecture — exact sequence (DOCUMENTED ONLY, NOT EXECUTED)

1. **Freeze & checkpoint** — confirm HEAD `daad396`, working tree unchanged, and take a full
   production database checkpoint/backup **before any schema change**.
2. **Establish read-only production access** and **reconcile the live migration state against all
   53 repository migrations** (not only the 17) — recording per-migration `LIVE_APPLIED` /
   `REPOSITORY_ONLY` / `MISMATCH`.
3. **Verify schema OBJECTS, not just history** — because history has proven unreliable (§3.2),
   confirm every object in §4 exists or is created.
4. **Apply only the genuinely missing migrations, in strict version order 1 → 53** (the 17 of which
   are the Release-1 delta). Never re-apply an applied migration.
5. **Load the emission-factor reference library** from the authoritative DEFRA 2025 source
   (the tracked `output/sql/import_defra_2025.sql` lineage) and verify the row count and a sample
   match — **without** copying demo rows (DR-02).
6. **Create the private `documents` storage bucket** and verify its policies (DR-08).
7. **Configure production secrets/environment** — backend (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`,
   JWT secret, `DATABASE_URL`, `RESEND_API_KEY`, optional `CARBONTALLY_AI_*`), frontend build vars
   (`REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`) — **no secret in Git**.
8. **Install the OCR runtime dependencies** (`tesseract-ocr`, `poppler-utils`) in the backend image
   (DR-09).
9. **Deploy the backend** (Render) — verify build/start config, then `/` and `/health`.
10. **Deploy the frontend** (Vercel) — verify build/output config and that the public site and the
    authenticated app resolve correctly (DR-05).
11. **Confirm the worker is running** (in-process, always-on instance) and that a harmless job can
    be picked up.
12. **Verify authentication end-to-end** — signup/login, JWT issuance, redirect URLs, session
    refresh, MFA policy.
13. **Verify RLS + the negative security matrix** in production (§5) — every unexpected ALLOW is a
    stop-the-line security event.
14. **Provision the first organisation** through `/api/v3/commercial` (§8) — organisation,
    subscription, allowance, entitlement.
15. **Controlled smoke test** — one real, non-sensitive dataset: upload → ingest → extract → map →
    validate → calculate → evidence → review → approve, asserting the persisted D11 notifications
    and the D6 `usage_tracking` charge.
16. **Verify backups/PITR** are enabled and perform one **restore drill** on a copy (DR-10).
17. **Enable minimal alerting** (DR-11).
18. **Monitor, then release the first customer.**

**No step was executed by this task.**

---

## 16. Rollback plan

| Layer | Strategy | Limitation |
|---|---|---|
| Git | revert to `16391217103b98dcea520070c5a22c68f12fe607` (pre-Release-1) or `git revert daad396…` | a revert does **not** un-apply migrations or restore data; the release boundary is a single commit, so reverting is atomic for code |
| Frontend (Vercel) | redeploy the previous build / instant rollback to the prior deployment | requires a known-good previous deployment to exist |
| Backend (Render) | redeploy the previous image/commit | the billing fix would be **lost**, reintroducing the D6 approval 500 — so a rollback to pre-`daad396` code is *not* operationally acceptable once traffic exists |
| Migrations | **forward-only in practice** | the 17 Release-1 migrations contain `ADD COLUMN`/`CREATE TABLE`/`CREATE INDEX`/triggers/functions with **no down-migrations**; several later migrations *depend* on earlier ones → **no safe migration rollback path is defined** (DR-13) |
| Data | restore from backup/PITR | **PITR availability `UNKNOWN`** (§13) → data rollback is currently unproven |
| Billing | ledger rows are append-only history | reversing a real charge/entitlement must use the commercial API (`credits/reserve|refund|reverse|rollover`), never ad-hoc SQL; any rollback after a real charge needs a PO decision |
| Worker | restart/stop the API instance | in-flight DB-durable jobs resume on restart; a code rollback cannot un-write emitted notifications/charges |

**Unsafe/incomplete by default:** migration rollback is effectively irreversible (forward-only,
no down scripts), and data rollback depends on an unverified PITR posture. Rollback must therefore
be **rehearsed on a copy before the first customer** — not improvised during an incident.


## 17. First customer readiness

### MUST HAVE BEFORE FIRST CUSTOMER
1. **Live migration reconciliation + apply the missing delta** (all 53, ordered) — DR-01.
2. **Emission-factor library loaded** (7 049-class factor set from the authoritative source) — DR-02.
3. **Production secrets/environment configured** (backend + frontend build vars) — DR-04.
4. **Backend + frontend deployed with working build config**, health verified — DR-05/DR-02.
5. **Provisioning path proven** (organisation → subscription → allowance → entitlement) — §8.
6. **RLS + negative security matrix verified in production** — §5.
7. **One end-to-end processing proof on real data** with persisted provenance and the D6 charge.
8. **Backups/PITR confirmed and one restore drill completed** — DR-10.
9. **`documents` storage bucket created/private** — DR-08.

### SHOULD HAVE
10. OCR runtime dependencies installed and verified (DR-09).
11. Minimal alerting for processing/billing/notification failures (DR-11).
12. Env-driven CORS with the ineffective `*.onrender.com` wildcard removed (DR-07).
13. Frontend production fallbacks removed so a build cannot silently target production (DR-06).
14. Rollback rehearsal on a copy (DR-13).

### CAN WAIT UNTIL AFTER FIRST CUSTOMER
15. External payment-provider integration (payment collection is out-of-band today).
16. Repository hygiene: committed dump-like artefacts, large factor SQL in the tree, root scratch
    files (`_*.txt`), duplicate `docs/**` volume (DR-12).
17. P6-2F residual evidence items (§18) and Phase 7/8 (§19).
18. Advanced analytics, expanded reporting, accessibility sweep, retention-enforcement hardening.

---

## 18. P6-2F boundary (NOT reopened)

P6-2F remains **NOT VERIFIED / NOT CLOSED** (the independent-verification report still carries
`NOT VERIFIED` on the DB/RLS-level rows and `IV-E2 — NOT CLOSED (BLK-2)` for live DB/RLS). This
audit makes **no** verification claim and performs no remediation.

| Residual P6-2F gap | Classification |
|---|---|
| Browser specs previously skipped on consultant-surface control visibility | **evidence gap** (the run-reset fixtures `ITEM_A9`/`ITEM_A10` already exist to remove the skip) |
| D11 `accepted` / `qc_outcome` / `rework` notification evidence incomplete | **evidence gap** |
| Live-DB/RLS-level idempotency (`uq_notifications_event_key`) not exercised | **evidence gap** (usable as a deployment verification step) |
| Full pytest/browser suite not re-captured after the last fixture change | **evidence gap** |
| Billing `to_char`/`usage_month` D6 fix | **fixed and committed** — was a production defect, now closed (re-verify in production) |

**No proven production defect remains open from P6-2F.** Therefore **no P6-2F residual is a launch
blocker**; the items above are evidence gaps (E-class) or deployment verification steps.

---

## 19. Phase 7 / Phase 8

* **Phase 7 — Auditor / Assurance:** name PO-ratified, **detailed scope NOT defined and nothing
  authorised** (Master Roadmap V1.0 §10). **NOT required for the first controlled customer.**
* **Phase 8 — Advanced Analytics:** same — **NOT required**.

No current production dependency requires Phase 7 or Phase 8: the launch path (auth → RLS →
provisioning → processing → calculation → evidence → reporting) is complete in the Release-1
capability set. If public product claims use the words *assurance*/*verified*/*audited*, that is a
**PO/business decision about the claims**, not a reason to build Phase 7. **Nothing in either phase
was implemented.**


## 20. Final deployment blocker matrix

Severity: **P0** (prevents deployment) · **P1** (must be done before/at deployment) ·
**P2** (should be done) · **P3** (hygiene) · **E** (evidence gap, non-blocking).

| ID | Finding | Sev | Commit blocker | Deployment blocker | First-customer blocker | Required action |
|---|---|---|---|---|---|---|
| DR-01 | Live production migration state `UNKNOWN` (no production credential; read-only reconcile attempt failed at connection) | P0 | No | **YES** | **YES** | obtain read-only production access; reconcile all 53 migrations; apply only the missing delta 1→53 |
| DR-02 | **Emission-factor reference data not reachable from a clean Release-1 deployment path** (7 049 factors live locally; the 5.6 MB `output/sql/import_defra_2025.sql` factor set sits inside the excluded `output/**` tree) | P0 | No | **YES** | **YES** | load the factor library from the authoritative DEFRA 2025 source; verify row count + sample match |
| DR-04 | Production secrets/environment not representable from the repo (all `DATABASE_URL`s are localhost) | P0 | No | **YES** | **YES** | configure backend + frontend production env as secrets |
| DR-03 | Migration **history is not a reliable proxy** for applied schema (E2E: 116 tables/175 policies but only 26 recorded rows; dev: 4 non-canonical version strings) | P1 | No | **YES** | **YES** | reconcile by **objects** (§4) as well as history |
| DR-05 | Frontend deploy config unverifiable: `vercel.json` rewrites to `/frontend/index.html` & `/admin/index.html` but build outputs are git-ignored/uncommitted and no `public/` exists; no build command in-repo | P1 | No | **YES** | **YES** | define build command/output in the Vercel project; verify deployed routes |
| DR-08 | Private `documents` storage bucket is **not created by any migration** (only `UPDATE storage.buckets`) | P1 | No | **YES** | **YES** | create the bucket + verify policies in production |
| DR-09 | OCR requires **system binaries** (`tesseract-ocr`, `poppler-utils`) not expressible in `requirements.txt`; no `Dockerfile`/build config in repo | P1 | No | **YES** | **YES** | install in the backend image; verify OCR on a scanned PDF in production |
| DR-10 | Backups / PITR / restore procedure `UNKNOWN` or undefined in-repo | P1 | No | No | **YES** | confirm PITR/backups; perform one restore drill |
| DR-11 | No monitoring/alerting integration exists in the repo | P1 | No | No | **YES** (should-have) | add minimal alerting for processing/billing/notification/auth failures |
| DR-06 | Hard-coded production fallbacks in `frontend/src/supabaseClient.js` (production URL + publishable key) → a build without env silently targets production | P1 | No | No | Partial | make env-explicit at build time (key is publishable; RLS remains the boundary) |
| DR-13 | No migration down-scripts; rollback effectively irreversible; data rollback depends on unverified PITR | P1 | No | No | **YES** | rehearse deploy + rollback on a copy before the first customer |
| DR-07 | CORS hard-coded in `backend/config.py` incl. `https://*.onrender.com` (Starlette matches literally → ineffective) | P2 | No | No | No | make CORS env-driven; replace the wildcard with explicit origins |
| DR-02b | `supabase/seed.sql` is a **local pg_dump-style** file that must never be applied to production | P2 | No | No | No | ensure no deployment path runs `supabase/seed.sql` against production |
| DR-12 | Repository hygiene: committed dump-like artefacts (`backups/seed.sql` 7.3 MB UTF-16, `supabase/seed.sql`), 5.6 MB factor SQL inside an excluded tree, root scratch `_*.txt` files | P3 | No | No | No | post-launch cleanup; keep all of it out of any production data path |
| DR-14 | P6-2F residual evidence gaps (browser skips, D11 events, live-DB idempotency, fixture re-capture) | E | No | No | No | capture as evidence; not a launch blocker |

**Git commit blocker: NONE.**
**Deployment blockers: DR-01, DR-02, DR-04, DR-03, DR-05, DR-08, DR-09 — all prerequisites, none an implementation defect.**
**First-customer blockers: the above plus DR-10 and DR-13; DR-11 should-have.**


## 21. Final data migration decision

### Should local/demo Supabase data be migrated wholesale to production? **NO.**

* **Schema migration requirement:** apply the repository migration set to production in version
  order **after** reconciling live state — all 53 migrations form the schema; the 17 in Release-1
  are the release delta.
* **Exact migration delta:** **`UNKNOWN` until read-only production access exists** (§3.1). It
  cannot be inferred from migration history alone — locally, history already disagrees with the
  physical schema (§3.2).
* **Exact reference/master data — the only such class:** the **emission-factor library**
  (`emission_factors` + `factor_aliases`), loaded from the authoritative DEFRA 2025 source and
  **not** copied from the demo database. Plan catalogue, commercial config and role vocabulary
  arrive **with the migrations** (`billing_plans`, `billing_commercial_config`, `staff_roles`) and
  need no data migration.
* **Exact production records that must be created:** the first customer organisation, its
  users/memberships, any consultant firm / processing entity, its subscription, allowance and
  credits (via `/api/v3/commercial`), the private `documents` bucket, and all customer data
  thereafter.
* **Exact data that MUST remain local/E2E/demo:** everything in §9-A — all 975 demo organisations,
  1 125 memberships, 917 consultant-client relationships, 11 processing entities, all extraction
  items / notifications / conversations / billing and usage rows, all E2E personas and E2E secrets,
  and every file under `local_backups/**` and `backups/**`.

**No data migration was performed by this task.**

---

## 22. Required final outputs

* This report — `docs/architecture/CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md`
* Durable history — `docs/cline/prompt-history/CT-PROD-DEPLOYMENT-READINESS-20260911-001.md`

---

## 23. Mandatory no-change confirmation

```text
Repository source modified: NO
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

---

## FINAL VERDICT

## `DEPLOYMENT READINESS — READY WITH PREREQUISITES`

The Release-1 commit contains **no implementation blocker** and **no P0 defect**: its content is
complete and internally consistent, and it introduces no private-secret disclosure. Deployment is
nonetheless **not ready to execute blind** — the live migration delta is `UNKNOWN`, and a bounded
set of prerequisites (live reconciliation, the emission-factor reference load, production secrets,
object-level schema verification, backend/frontend build configuration, the private `documents`
bucket, OCR system binaries, backups/PITR confirmation and a rollback rehearsal) must be completed
first.

**No production target was modified. Awaiting Product Owner authorization for the next deployment
operation.**

