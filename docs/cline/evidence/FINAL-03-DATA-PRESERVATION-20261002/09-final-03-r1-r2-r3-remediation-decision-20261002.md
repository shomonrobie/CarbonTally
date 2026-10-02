# FINAL-03 — R-1 / R-2 / R-3 + 9 BROWSER-ACCESSED TABLES: REMEDIATION DECISION (2026-10-02)

**STATUS: `ASSESSMENT ONLY — NO SQL · NO MIGRATION · NO RLS CHANGE · NO PRODUCTION CHANGE · NO DEPLOY · NO AUTH/SETTINGS/TOKEN CHANGE`**

- Companion to (and derived from) `08-final-03-p2-p5-p6-rls-decision-package-20261002.md` (§C.0–C.4 classifies all **47** RLS-disabled tables; §C.3 defines **R-1…R-6**).
- Repository `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`, HEAD `cabdca8380415e73a25cf23eb393d0b15c0af391`.
- This pass is **read-only**. Nothing was created, applied, deployed or written except this evidence file.
- Purpose: convert **R-1** (`system_settings`), **R-2** (`staff_roles.permissions`), **R-3** (token material) and the **9 browser-accessed RLS-disabled tables** into a concrete, implementation-ready decision the owner can authorise without guessing.

---

## 0. INVARIANTS THIS ASSESSMENT RELIES ON (all re-verified this pass)

| # | Invariant | Evidence (this pass) |
|---|---|---|
| I-1 | `anon` holds **NONE** on all 47 tables | package `08` §C.0 (F5), from `05-rls-prohibition-and-storage.txt`; corroborated by the absence of any `GRANT … TO anon` for these tables in the migration set |
| I-2 | `authenticated` holds **DML** on 45/47 (`consultant_billing` = SELECT only; `emission_factors` = none) | package `08` §C.0 (F3b) |
| I-3 | `service_role` holds **ALL** on all 47 → RLS cannot break backend paths | package `08` §C.0 (F7) |
| I-4 | **The backend never authenticates as `authenticated`.** Every backend `.from_(…)` call and repository runs on the **service-role** client | `backend/database.py:19` (`SUPABASE_SERVICE_KEY = os.getenv(...)`), `:28` (`def get_supabase_client`), `:42` (hard-fails without the service key), `:53` (`supabase_key = SUPABASE_SERVICE_KEY.strip()`), `:57` (`create_client`) |
| I-5 | PostgREST grants a role exactly what the **role** holds — there is no per-table gate; any authenticated JWT can query every table in I-2 | package `08` §C.0 (F8) |
| I-6 | Policies on RLS-disabled tables are **inert** (PostgreSQL ignores policies until `ENABLE ROW LEVEL SECURITY`) | `conversation_participants` (3 policies, `20260822010000…:199-209`, `20260902040000…:139-143`), `manual_extraction_items` (1 policy, `20260821020000…:102-115`); a repo-wide search for `ENABLE ROW LEVEL SECURITY` on these table names returns **no match** |
| I-7 | The browser clients run as `authenticated` (anon key + user session) | `admin/src/supabaseClient.js:59` (`createClient(supabaseUrl, supabaseAnonKey)`) |

**Consequence of I-3 + I-4:** every "enable RLS + policy" remedy below is **app-side only** for the backend. No backend route, service, repository or worker changes behaviour when RLS is enabled, because none of them run as `authenticated`.

---

## 1. R-1 — `system_settings` (CRITICAL)

### 1.1 Schema fact that reframes the finding

`supabase/migrations/00000000000000_init_schema.sql:2022-2084`:

```
setting_key   VARCHAR UNIQUE NOT NULL,
setting_value JSONB   NOT NULL,
… ~60 legacy platform columns (default_currency, session_timeout_minutes,
  audit_log_retention_days, data_retention_days, document_retention_days,
  backup_retention_days, login_attempts_max, two_factor_required, …)
```

There is **no `settings_json` column and no `max_file_size_mb` / `allowed_file_types` / `enable_auto_repair` / `max_batch_files` / `max_total_batch_size_mb` / `require_2fa` / `max_login_attempts` column** anywhere in the migration set (repo-wide search for `settings_json` and `max_file_size_mb` in `supabase/migrations/*.sql` → **zero matches**).

The backend's authoritative model is **one row per `setting_key`** (`backend/data/settings.py:23,31,36,41,46,53,59`): `platform_retention`, `analytics_ga4`, `platform_notifications`, `upload_policy`, `email_provider`, `backup_policy` — written with `INSERT … ON CONFLICT (setting_key) DO UPDATE` (`backend/data/settings.py:662-688`).

### 1.2 Every read/write path (exhaustive for this pass)

| # | Path | Direction | Auth context | Evidence |
|---|---|---|---|---|
| P1 | Admin browser page `Settings.js` — `select('*').single()` | READ | `authenticated` (any logged-in user; no server-side admin gate on the page) | `admin/src/pages/admin/Settings.js:67-71` |
| P2 | Admin browser page — `insert({...})` "create defaults" | WRITE | as P1 | `admin/src/pages/admin/Settings.js:117-131` |
| P3 | Admin browser page — `upsert({...},{onConflict:'id'})` "save" | WRITE | as P1 | `admin/src/pages/admin/Settings.js:155-182` |
| P4 | `/api/v3/settings/{retention,upload-policy,notification-sender,email-provider,analytics}` GET+PUT | READ+WRITE | **`require_admin()`** (every write; all GETs except analytics) | `backend/api/v3_settings.py:214,224,251,273,308,331,367,387,421,445,480`; guards `:216,227,276,310,334,369,390,423,448,483` |
| P5 | `GET /api/v3/settings/analytics` | READ | **public by design** (GA4 measurement id only — non-secret, needed before sign-in) | `backend/api/v3_settings.py:11-14` (docstring), `:251` (no `require_admin`) |
| P6 | `backend/data/settings.py` repository (asyncpg, service-role `DATABASE_URL`) | READ+WRITE | service role | `backend/data/settings.py:203,241,263,337,358,398,420,460,502,541,575,616,664` |
| P7 | Legacy `GET /api/admin/settings/settings-history` | READ | `require_admin()` | `backend/routes/admin/settings.py:38-55` |
| P8 | Legacy `POST /api/admin/settings/reset` (`.update(...).eq('id','1')`) | WRITE | `require_admin()` | `backend/routes/admin/settings.py:119-159` |
| P9 | `routes/upload.py:get_system_settings()` (legacy flags; reads `settings_json`) | READ | service role | `backend/routes/upload.py:60,77`; callers `:189,260` |
| P10 | Production **email provider** selection (`resend` \| `smtp`) | READ | service role | `backend/services/email_provider.py:9-14,55-56,504-521` |
| P11 | Production **email sender** identity (`From`) | READ | service role | `backend/services/email_sender.py:31,34,39`, `backend/services/v3_email.py:28-60` |
| P12 | Retention enforcement / backup policy / upload policy / GA4 bootstrap | READ | service role / API | `backend/services/retention.py:4`, `backend/utils/upload_limits.py:4`, `backend/backup/policy.py:194`, `frontend/src/lib/analytics/ga4.js:89` |

### 1.3 The five determinations

**1. Which operations does the browser actually need?** *Reads only — and even those are already served by admin-gated endpoints.* P2/P3 (the writes) are **already non-functional**: they submit `settings_json`, `max_file_size_mb`, …, none of which exist, and omit the `NOT NULL` `setting_key` / `setting_value` pair → PostgREST rejects them today. **The browser write path is dead code that has been dead since the `setting_key`/`setting_value` model landed.**

**2. Which operations must be backend/admin-only?** All writes (P4, P6, P8) and the sensitive reads (P10 provider, P11 sender, P12 policy). These are already backend-only: the only writers in the repository are `data/settings.py` (service role) and the `require_admin()` API.

**3. Can browser writes be removed entirely?** **Yes, with no loss of functionality.** The three call sites (P1–P3) can be deleted or re-pointed at the existing `GET/PUT /api/v3/settings/*` endpoints. Neither option is an architectural redesign — the API and repository already exist and are the only functioning path (`admin/src/App.js:73` is the only route to the legacy page).

**4. Minimum RLS policy if browser access must remain?** **None is required — and none is recommended.** Minimum safe configuration is `ENABLE ROW LEVEL SECURITY` with **zero policies** (deny-all for `anon`/`authenticated`; `service_role` unaffected per I-3 → every backend path survives). If the owner insists on a browser read, the minimum is exactly one `FOR SELECT TO authenticated` policy gated on a **platform-admin predicate — which does not exist as SQL**: the migration set defines only org/entity/conversation helpers (`is_org_member`, `is_org_consultant`, `is_entity_member`, `is_conversation_participant`, `can_view_entity_conversation`). Adding one would be **new SQL re-deriving `staff_roles.permissions` inside the database** — strictly riskier than moving the read to the existing API. **Recommendation: deny-all + API.**

### 1.4 Recommended target state (NOT implemented)

| Item | Target |
|---|---|
| `system_settings` RLS | **enabled**, **zero policies** (deny-all for `anon`/`authenticated`) |
| Browser read | served by `GET /api/v3/settings/*` (`require_admin()`); legacy `Settings.js` re-pointed or retired |
| Browser write | **removed** (it never worked; nothing to preserve) |
| Provider/sender config | unchanged — DB setting + environment credential, admin-gated API |
| Residual owner decision | whether to keep the legacy settings page at all (product decision, not security) |

### 1.5 Severity if left as-is
**Critical.** Production has **1** row; `authenticated` holds DML with RLS off (I-2, I-5) → **any authenticated user can read every settings row and upsert any `setting_key`** — including `email_provider` and `platform_notifications`. The broken legacy UI does **not** constrain a direct PostgREST call. Per package `08` §E.3 this is simultaneously an **email-security control**: the production sender identity lives in this row.

---

## 2. R-2 — `staff_roles.permissions` (CRITICAL)

### 2.1 Every path

| # | Path | Direction | Verified authz | Evidence |
|---|---|---|---|---|
| Q1 | Browser direct table access | **NONE** | — | repo-wide search: `staff_roles` has **0** browser/PostgREST call sites |
| Q2 | Ops UI role catalogue (read) | READ via **backend API** | `require_staff` | `frontend/src/v3/ops/StaffRolesTab.jsx:2,16,29` (read-only by statement), `frontend/src/v3/ops/StaffRoster.jsx:34` → `GET /staff-roles` |
| Q3 | `GET /staff-roles` (catalogue + customer-org matrix) | READ | `require_staff` | `backend/api/v3_operations.py:2649-2659` |
| Q4 | **Authenticated-user role/permission resolution (every API request)** | READ | service role | `backend/auth.py:249-266` (`staff_profiles` → `staff_roles.select('name, permissions')`) |
| Q5 | Authoritative permission source for ops / insight / PE / messaging authz | READ | service role | `backend/api/operations_auth.py:57,72,158-173`, `:205-211` (`ensure_staff_permission`), `backend/api/insight_authz.py:30,134-143,254-266`, `backend/api/pe_auth.py:11`, `backend/api/v3_messaging.py:79` |
| Q6 | Repository reads | READ | service role (`DATABASE_URL`) | `backend/data/staff.py:241,249`, `backend/data/notifications.py:174,223` (`JOIN public.staff_roles sr`) |
| Q7 | **BACKUP-01 capability grant** | **WRITE** | migration role (`postgres`) — **not** browser, **not** `authenticated` | `supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql:173-185`: `UPDATE public.staff_roles SET permissions = permissions \|\| '{"can_manage_backups": true}'::jsonb, updated_at = NOW() WHERE name IN ('admin','system_admin') AND (permissions->>'can_manage_backups') IS DISTINCT FROM 'true'` |
| Q8 | Capability enforcement (consumer of the row Q7 writes) | READ | service role | `backend/auth.py:804-814` (`ADMIN_ROLE_NAMES = ('admin','system_admin')`, `can_manage_backups`) |

### 2.2 Determinations

- **Do authenticated browser users genuinely require direct write access?** **No — not even read access.** `staff_roles` has **zero** browser call sites (Q1); the ops UI reads the catalogue through a `require_staff` backend endpoint (Q2/Q3). Direct browser DML is pure attack surface.
- **Does BACKUP-01 create the risk?** It *writes the row*, but as a **migration-time statement** (Q7): RLS does not apply to it and it cannot be the vector. The risk is that the row it writes — and every permission the platform enforces (Q5, Q8) — is **DML-writable by any authenticated JWT** (I-2, I-5): one PostgREST `PATCH` can grant `can_manage_backups`, `can_process`, `can_manage_staff`, … to any role. The only guard today is a client-side UI.
- **Minimum safe authorization boundary:** **backend/admin-only + RLS enabled (zero policies).** The application-layer checks (`require_admin`, `require_staff`, `ensure_staff_permission`) are correct but *consume* `staff_roles.permissions` — so the catalogue must be protected **in the database**, not only in code.
- **Recommendation:** `ENABLE ROW LEVEL SECURITY` with **zero policies**, plus the standing rule that **staff-role resolution stays on the service-role client** (I-4). No app change: Q4/Q5/Q6 are service-role, Q7 is migration-time, Q2/Q3 go through the API.

### 2.3 Severity if left as-is
**Critical.** 1 row; the JSONB is the enforcement input for ops, insight, PE, messaging-support and backup capability gates; RLS off + authenticated DML ⇒ full permission-forgery surface.

---

## 3. R-3 — token material (HIGH)

### 3.1 `password_reset_tokens`

DDL (`supabase/migrations/00000000000000_init_schema.sql:332-341`): `user_id UUID`, `token VARCHAR UNIQUE NOT NULL`, `expires_at TIMESTAMPTZ`, `used BOOLEAN`, `used_at TIMESTAMPTZ`.

| Path | Direction | Auth | Evidence |
|---|---|---|---|
| Generation + store: `secrets.token_urlsafe(32)`, 1 h expiry, `upsert(…, on_conflict='user_id')` | WRITE | service role | `backend/routes/users.py:81` |
| Validation/consumption: `select('user_id, expires_at, used').eq('token', …).eq('used', False)` → `auth.admin.update_user_by_id` → `update({'used': True})` | READ+WRITE | service role | `backend/routes/users.py:125,163` |
| Browser access | **NONE** | — | repo-wide search: no `frontend/` or `admin/` reference to `password_reset_tokens` |

**Why it is currently readable:** not because of any browser path, but purely because `authenticated` holds **DML** while RLS is disabled (I-2, I-5). The moment one row exists, **any** holder of **any** authenticated JWT can `GET /rest/v1/password_reset_tokens?select=token,user_id` and redeem it through `POST /api/users/password-reset/confirm` — a complete account-takeover primitive, with no client-side filter involved.

**Minimum remediation (no auth redesign):** enable RLS + **zero policies**. No backend change and **no token-handling change**: the whole lifecycle is service-role (I-4). *(Optional hardening — store a salted hash instead of the token — is explicitly **out of scope** for FINAL-03 and is not required to close R-3.)*

### 3.2 `beta_access_codes`

DDL (`supabase/migrations/00000000000000_init_schema.sql:375-386`): `code TEXT UNIQUE NOT NULL`, `email TEXT`, `status TEXT`, `expires_at`, `used_at`, **`magic_token TEXT`**, `token_created_at`.

| Path | Op | Effective auth | Evidence |
|---|---|---|---|
| Signup page validates the invite code (`select('code,email,status,expires_at').eq('code',betaCode).single()`) | READ | **`anon`** — mount `useEffect`, runs **before** `signUp()` | `frontend/src/BetaSignup.jsx:35-39` |
| Signup page marks the code used (`update({status:'used',used_at})`) | WRITE | **`anon`** — still before the account exists | `frontend/src/BetaSignup.jsx:123-129` |
| Admin page looks a code up by email (resend magic link) | READ | `authenticated` (admin session) | `admin/src/pages/admin/BetaManagement.js:97-104` |
| Backend admin CRUD (list/create/status/delete/users/stats) | CRUD | **`require_admin()`** | `backend/routes/admin/beta.py:54,96,142,191,285,316,383,427,451` (guards `:56,99,146,194,287,319,387,430,453`) |
| Backend code-validation endpoint (works without a session) | READ | `get_current_user_optional` | `backend/routes/admin/beta.py:215-218` |

**Why it is currently readable:** `code` **and `magic_token`** are columns on a table with `authenticated` DML and RLS off → any authenticated JWT can dump the whole table (every code and magic token, regardless of the client's `eq('code', …)` filter — that filter is presentation, not authorization).

**Decisive detail for the remediation choice:** the two signup sites run **pre-authentication** (as `anon`), and `anon` holds **NONE** (I-1) — so they **already fail closed today**: the flow reports "Invalid beta access code" and never marks the code used. **No `authenticated` policy can serve a pre-auth read**, and an `anon` policy on a token table would be a public disclosure. The only correct remedy is the **existing backend endpoint** (`backend/routes/admin/beta.py:215`), which validates codes without a session.

**Minimum remediation (no auth redesign):** (1) enable RLS + **zero policies** on `beta_access_codes`; (2) point `BetaSignup.jsx` validation/mark-used at `GET /api/admin/beta/codes/validate/{code}` (`:215`, exists) plus an admin-gated status write; (3) point `BetaManagement.js:97-104` at `GET /api/admin/beta/codes` (`:54`, `require_admin()`, already returns codes). **Net app change: 3 call sites; no new endpoint needed for validation.**

### 3.3 Severity if left as-is
**High.** 0 rows today — but 0 rows is not a control: one row is one account takeover (`password_reset_tokens`) or one grantable beta/magic-link credential (`beta_access_codes`). Both close with RLS enablement and no authentication redesign.

---

## 4. THE NINE BROWSER-ACCESSED TABLES — 10-FIELD ASSESSMENT

Common facts for all nine (I-1…I-5): `anon` = NONE; `authenticated` = DML; `service_role` = ALL; RLS **disabled** on all nine; **RLS enablement cannot break any backend path** because every backend access is service-role (I-4). "Current policies: 0" unless stated.

### 4.1 `beta_access_codes` — token/invite material

| Field | Finding |
|---|---|
| 1. Browser operation(s) | READ `select('code,email,status,expires_at')` + WRITE `update({status:'used',used_at})` **pre-auth (`anon`)** — `frontend/src/BetaSignup.jsx:35-39,123-129`; READ `select('code').eq('email',…)` **`authenticated`** (admin) — `admin/src/pages/admin/BetaManagement.js:97-104` |
| 2. Backend operation(s) | Full admin CRUD + validate: `backend/routes/admin/beta.py:54,96,142,191,215,285,316,383,427,451` (`require_admin()`, validate = optional-auth) |
| 3. Authenticated role(s) | any `authenticated` user (the admin page has no server-side check of its own); `anon` for the two signup sites |
| 4. Ownership model | Invite/credential row keyed by email + `code`; **not** tenant-scoped; carries `magic_token` |
| 5. Direct browser access required? | **No.** Validation is an admin/onboarding function with an existing backend endpoint (`:215`); the admin read duplicates `GET /api/admin/beta/codes` (`:54`) |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | Any authenticated JWT can read **every** code and **`magic_token`** (R-3); the `eq('code',…)` filter is not a boundary |
| 9. Minimum policy/architecture | Enable RLS + **zero policies**; move validation/mark-used to the existing backend endpoint; re-point the admin read at the admin API. (An `anon` policy is **not** acceptable — it would publish the token table) |
| 10. REQUIRED before FINAL-03? | **YES** — token disclosure; fix is 1 enablement + 3 call-site changes, no new endpoint |

### 4.2 `beta_users` — authorisation list

| Field | Finding |
|---|---|
| 1. Browser operation(s) | READ `select('email').eq('email',…)` pre-auth (`frontend/src/BetaSignup.jsx:83-87`) and post-login (`frontend/src/BetaLogin.jsx:72-76`, `:135-139`); WRITE `insert({user_id,email,beta_code,access_level})` after `signUp()` (`frontend/src/BetaSignup.jsx:132-139` — `authenticated` **only if** the project issues a session immediately, otherwise `anon`) |
| 2. Backend operation(s) | Admin CRUD: `backend/routes/admin/beta.py:285-296,316-360,383-409,427-436,451-470` (`require_admin()`) |
| 3. Authenticated role(s) | any `authenticated` user (the two post-login checks); `anon` for the pre-signup pair |
| 4. Ownership model | Per-user (`user_id`, unique `email`, `access_level`, `invited_by`) — an access-control list, not tenant data |
| 5. Direct browser access required? | **No.** Both post-login checks re-implement a gate the backend can own; the pre-signup pair duplicates admin data |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | Full disclosure of the beta access list (emails, levels, inviter) **and** a self-grant path: any authenticated user can insert/update their own row with `access_level='beta'`, defeating the beta gate |
| 9. Minimum policy/architecture | Enable RLS + **one own-row SELECT policy** (`email = auth.jwt()->>'email'`) if the login check stays; the insert must move to the backend (a self-INSERT policy would preserve the self-grant path) |
| 10. REQUIRED before FINAL-03? | **YES** — authorisation data + 4 sites; the self-grant path is the strongest reason |

### 4.3 `conversation_participants` — messaging membership (LOWEST-RISK FIRST STEP)

| Field | Finding |
|---|---|
| 1. Browser operation(s) | **READ only, 3 sites:** `select('conversation_id').eq('user_id',…).eq('is_active',true)` — `frontend/src/lib/realtime/manager.js:397-408`; same + embedded `participants:conversation_participants(...)` join — `frontend/src/components/chat/ChatWidget.jsx:40-44,57-70`; `select('user_id').eq('conversation_id',…)` — `frontend/src/components/chat/ChatWindow.jsx:108-115`. **Browser writes were deliberately removed** (`ChatWidget.jsx:196-201`: *"The browser no longer writes `conversations` / `conversation_participants`"*) |
| 2. Backend operation(s) | Read: `backend/data/messaging.py:183-187`, `backend/routes/communication.py:1726-1729` (`require_org_member`). Write: server-authoritative creation in `backend/api/v3_messaging.py` (+ `data/notifications.py:185-187` PE participant lookup) |
| 3. Authenticated role(s) | any `authenticated` user (the reads are client-filtered by `user_id`, which is **not** a boundary) |
| 4. Ownership model | Membership row: `conversation_id` → conversation → `organization_id` (org members/consultants) or NULL-org entity conversations |
| 5. Direct browser access required? | **Yes for the 3 reads** (the chat UI legitimately needs the caller's own memberships) — and the intent is already expressed by existing policies |
| 6. Current RLS state | **disabled** (this is why 3 policies are inert — I-6) |
| 7. Current policies | **3**: `conversation_participants_select` (`20260822010000_d27_d19_customer_lifecycle.sql:199-203`, `USING can_view_conversation_participants(conversation_id)`), `conversation_participants_update_own` (`:205-209`), `conversation_participants_entity_select` (`20260902040000_phase5_pe_operational_messaging.sql:139-143`) |
| 8. Consequence of leaving disabled | Any authenticated JWT can enumerate **every** conversation's membership (who is in which thread) — the isolation the product already wrote is simply not applied |
| 9. Minimum policy/architecture | **Enable RLS only** — no new policy, no app change. The 3 existing policies already cover the 3 read shapes |
| 10. REQUIRED before FINAL-03? | **YES — but this is the cheapest item in the whole package** (1 row; enablement only). Cutover check: confirm the single production row satisfies the policy predicates for its legitimate reader before enabling, otherwise the chat UI returns empty |

### 4.4 `email_logs` — recipient PII / delivery log

| Field | Finding |
|---|---|
| 1. Browser operation(s) | **READ** `select('*').eq('type','beta_invite').order(…).limit(100)` — `admin/src/pages/admin/BetaManagement.js:57-66` (`authenticated`) |
| 2. Backend operation(s) | **Writes:** `backend/utils/email.py:log_email()` (service client), `backend/services/email_service.py:217`. **Reads:** `backend/routes/admin/logs.py:20,34,71,104,155` (all `require_admin()`) — the same data, already admin-gated |
| 3. Authenticated role(s) | any `authenticated` user (the admin page's `isAdmin` is client-side only) |
| 4. Ownership model | Recipient **email address** (PII) + delivery metadata; platform-scoped, no tenant column |
| 5. Direct browser access required? | **No** — `routes/admin/logs.py` already serves this data with `require_admin()` |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | Any authenticated JWT can read the whole delivery log (recipient addresses, subjects/metadata, failure messages) — a PII disclosure and a ready-made target list |
| 9. Minimum policy/architecture | Enable RLS + **zero policies**; re-point the admin page at `routes/admin/logs.py` (no new endpoint) |
| 10. REQUIRED before FINAL-03? | **YES** (PII). Cheap: 1 enablement + 1 client change |

### 4.5 `notifications` — per-recipient user data

| Field | Finding |
|---|---|
| 1. Browser operation(s) | `WorkHub.jsx:193-198` — `select('*').eq('user_id', userId).order('created_at').limit(10)`. **This call is already broken:** the DDL (`init_schema.sql:1409-1425`) has **`recipient_id` + `recipient_type`**, not `user_id` → PostgREST errors and `notifications` is `null` (the destructuring ignores `error`). `frontend/src/context/RealtimeContext.jsx:274-279` records that the legacy direct read/write was **removed** there because of deny-by-default RLS; `/api/v3/notifications` is authoritative |
| 2. Backend operation(s) | Producer/fan-out and per-recipient reads: `backend/api/v3_notifications.py`, `backend/data/notifications.py` (recipient-scoped server-side) |
| 3. Authenticated role(s) | any `authenticated` user |
| 4. Ownership model | Per-recipient (`recipient_id` + `recipient_type` = user/org) |
| 5. Direct browser access required? | **No** — the API is already declared authoritative and the direct site does not even execute |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** (the RealtimeContext comment describes the *intended* deny-by-default posture) |
| 8. Consequence of leaving disabled | Any authenticated JWT can read (and write) **every** recipient's notifications — message text, links, metadata |
| 9. Minimum policy/architecture | Enable RLS + **zero policies** and delete the broken `WorkHub.jsx` read; if a browser read must exist, one `recipient_id = auth.uid()` SELECT policy. The product already treats the API as the only channel |
| 10. REQUIRED before FINAL-03? | **YES** — enablement + 1 deletion; no functional loss (the deleted call never worked) |

### 4.6 `review_audit_trail` — audit integrity

| Field | Finding |
|---|---|
| 1. Browser operation(s) | **5 sites in one admin service:** INSERT `action:'assigned'` (`admin/src/services/reviewService.js:40-48`), INSERT `'started'` (`:68-74`), INSERT `'completed'` (`:122-129`), INSERT `'reassigned'` (`:183-192`), SELECT with `performer/assignee` embeds (`:135-144`) |
| 2. Backend operation(s) | Read/export the same table with `require_admin()`: `backend/routes/admin/review_history.py:113-124`, `:145-155` |
| 3. Authenticated role(s) | any `authenticated` user (the admin UI's role gate is client-side; the service writes with the caller's session) |
| 4. Ownership model | Audit rows keyed by `review_id` + `performed_by` (+ `performed_by_email`, `old_value`/`new_value`) — an integrity record, not tenant content (DDL `init_schema.sql:1870-1882`) |
| 5. Direct browser access required? | **No** — a `require_admin()` backend route for the same table already exists; the 4 writes are the anomaly |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | Any authenticated JWT can read the whole review trail **and insert forged entries** (`action`, `performed_by`, `new_value`) or remove evidence — an audit-integrity failure of the same family as R-5 |
| 9. Minimum policy/architecture | Enable RLS + **zero policies**; land the 4 inserts and the read through the existing `review_history`/review backend routes (or delete the direct writes if the backend already records the same events) |
| 10. REQUIRED before FINAL-03? | **YES** — audit integrity; 1 enablement + 5 client changes against endpoints that already exist |

### 4.7 `staff_workload` — HR/ops counters (**downgraded by new evidence**)

| Field | Finding |
|---|---|
| 1. Browser operation(s) | 1 site — `WorkHub.jsx:249-253` `select('*, staff_profiles(...)')…order('date')`. It requests `assigned_reviews, in_progress_reviews`, **neither of which exists** in the DDL (`init_schema.sql:1253-1264`: `assigned_tasks`, `in_progress_tasks`, `pending_tasks`, `completed_today`, `workload_score`, `capacity_percentage`) → the PostgREST read **fails today** (`workload` is `null`) |
| 2. Backend operation(s) | `backend/utils/staff_workload.py:99-102` (reads `workload_score` — works); `backend/routes/admin/workload.py:37-71`; **write** `backend/routes/admin/reviews.py:38-60` upserts `assigned_reviews` + `last_updated` — **both non-existent** → fails (caught and logged, never surfaced); `backend/routes/admin/staff.py:364-368` reads the same non-existent columns |
| 3. Authenticated role(s) | any `authenticated` user |
| 4. Ownership model | Per-staff daily counters (`staff_id` → `staff_profiles`) |
| 5. Direct browser access required? | **No** — and the current site does not function |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | Exposure is real but **latent**: 0 rows, and every code path touching the table either uses non-existent columns or is `require_admin()`-gated. No working read or write exists to leak or corrupt |
| 9. Minimum policy/architecture | Enable RLS + **zero policies** (free — backend is service-role); **plus** fix or delete the 3 non-existent-column references (`WorkHub.jsx:251`, `routes/admin/reviews.py:50`, `routes/admin/staff.py:365`). Deleting them is safe: they have never worked |
| 10. REQUIRED before FINAL-03? | **NO — owner decision, not a blocker** (see §6.0 downgrade note). Recommended as hygiene in the same RLS migration |

### 4.8 `system_settings` — platform configuration (see §1 for the full trace)

| Field | Finding |
|---|---|
| 1. Browser operation(s) | READ `select('*').single()` (`admin/src/pages/admin/Settings.js:67-71`); WRITE `insert` (`:117-131`) and `upsert(onConflict:'id')` (`:155-182`) — **both writes already fail** (non-existent columns + `setting_key`/`setting_value` are NOT NULL) |
| 2. Backend operation(s) | Admin API `backend/api/v3_settings.py` (guards `:216,227,276,310,334,369,390,423,448,483`); repository `backend/data/settings.py` (keys at `:23,31,36,41,46,53,59`); legacy `backend/routes/admin/settings.py:38-55,119-159`; `backend/routes/upload.py:60,77` |
| 3. Authenticated role(s) | any `authenticated` user for the browser sites; `require_admin()` for every API write |
| 4. Ownership model | Platform-wide configuration rows (`setting_key` unique) — includes the email provider/sender |
| 5. Direct browser access required? | **No** (reads are available through the admin API) |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | **R-1**: any authenticated JWT can read all settings and upsert `email_provider`/`platform_notifications` — repointing production email |
| 9. Minimum policy/architecture | Enable RLS + **zero policies**; retire or re-point the legacy page (no backend change) |
| 10. REQUIRED before FINAL-03? | **YES — highest priority** (also an email-security control per §E.3 of package `08`) |

### 4.9 `waitlist` — public-signup PII

| Field | Finding |
|---|---|
| 1. Browser operation(s) | READ `select('*').order('created_at')` (admin page, `admin/src/pages/admin/BetaManagement.js:34-50`); WRITE `update({status:'active',activated_at}).eq('email',…)` after `signUp()` (`frontend/src/BetaSignup.jsx:142-148`) |
| 2. Backend operation(s) | `backend/routes/waitlist.py:6,17,22` — `POST /` and `GET /` are **empty stubs (`pass`)**, so nothing in the backend reads or writes this table. The admin page's invite/unsubscribe/resubscribe calls (`BetaManagement.js:72,115,140,164`) target `/api/waitlist/{invite,unsubscribe,resubscribe}`, which **do not exist** → those actions 404 |
| 3. Authenticated role(s) | any `authenticated` user |
| 4. Ownership model | Public-signup PII keyed by unique `email`; **no `user_id`, no tenant** → no per-user predicate is possible |
| 5. Direct browser access required? | **No** — the admin read can be served by a backend endpoint; the write site belongs with the (currently stubbed) waitlist backend |
| 6. Current RLS state | **disabled** |
| 7. Current policies | **0** |
| 8. Consequence of leaving disabled | Any authenticated JWT can read every prospect's name/company/size/interests/email and can tamper with statuses (e.g. mark anyone `active`) |
| 9. Minimum policy/architecture | Enable RLS + **zero policies** + serve the admin list from the backend; if a direct admin read must remain, one admin-gated SELECT policy (requires the missing platform-admin SQL predicate — see §1.3-4) |
| 10. REQUIRED before FINAL-03? | **YES (recommended, PII)** — 0 rows today and the backend is a stub, so it is low-effort; the owner may accept with a written rationale |

---

## 5. THE REMAINING 38 TABLES — A / B / C / D

### 5.0 Classification rule (stated so it can be audited) and the mapping to package `08`

The 47 minus the nine = **38** tables, classified exactly once each:

| Class | Meaning used here | Test applied |
|---|---|---|
| **A** | intentionally platform/internal — **safe to remain non-RLS** | either `authenticated` holds *no* privileges (containment proven), or the content is tenant-agnostic reference/config data with nothing to isolate and no personal data |
| **B** | privileged backend-only — **safe to remain non-RLS *now*** | no browser call site, no live exposure, and the only writers are the platform (backend/migration); must be re-classified when the owning feature ships |
| **C** | **requires remediation before production** | live exposure evidence: a browser path, or credential/authorisation/PII/audit/financial content on a table any authenticated JWT can reach |
| **D** | **unclear → owner decision** | 0 rows, no browser path, no working code path — but the content the feature will hold is user/tenant material, so "accept and gate" vs "enable now" is a genuine choice |

**Mapping to the authoritative package (`08` §C.1/C.2) — no new taxonomy is invented and no numbers are bent to a baseline:** `C1 → A`, `C2 → B`, `C3 → C`, and the nine `C4` rows the package recommended raising to `C3` → **D** (recommendation preserved; only the *authority to choose* moves to the owner). Arithmetic: **A 3 + B 19 + C 16 + D 9 = 47**; the 38 assessed in this section are **A 3 + B 19 + C 7 + D 9**.

### 5.1 Class A — safe to remain non-RLS (3 tables)

| Table | Rows | Evidence | Why A |
|---|---|---|---|
| `emission_factors` | **7,049** | `authenticated` holds **no privileges** (applied `20260926000000…` hardening; package `08` C.0 F3b) | Containment is proven by grants, not by RLS — enabling RLS would add nothing. 65 `.py` / 19 sql refs, all service-role |
| `business_hours` | 0 | 0 `.py` / 1 sql refs; 0 sites; weekday/time config | Tenant-agnostic calendar configuration; no personal data, no rows, no path |
| `sla_definitions` | 0 | 0 `.py` / 1 sql refs; 0 sites | Tenant-agnostic per-document-type SLA thresholds; nothing to isolate |

### 5.2 Class B — privileged backend-only, safe to remain non-RLS **now** (19 tables)

All 19: **0 browser call sites**, **0 live exposure**, and every current writer is the backend (service-role) or a migration. Each must be re-classified **when its owning feature ships** — that gate is the whole point of class B.

| Table | Rows | Backend `.py` refs | Note |
|---|---|---|---|
| `approval_decisions` | 0 | 0 | unbuilt workflow; no route, no UI, no policy |
| `approval_requests` | 0 | 0 | as above |
| `dashboard_metrics` | 1 | 20 | aggregate metrics row; platform-scoped |
| `notification_delivery` | 0 | 4 | transport-level delivery records |
| `processing_assignments` | 0 | 1 | unbuilt workflow |
| `processing_audit_trail` | 0 | 0 | unbuilt workflow |
| `processing_steps` | 0 | 0 | reference/step definitions |
| `processing_time_log` | 0 | 0 | staff time entries (HR-sensitive once populated → re-classify at feature time) |
| `qc_checklists` | 0 | 0 | checklist definitions |
| `qc_checks` | 0 | 2 | QC records (→ re-classify at feature time) |
| `qc_errors` | 0 | 4 | QC error records (→ re-classify) |
| `queue_settings` | 0 | 28 | ops tuning config; backend-only today |
| `reassignment_history` | 0 | 1 | ops history |
| `review_assignment_history` | 0 | 11 | ops history |
| `sla_compliance` | 0 | 1 | ops records |
| `staff_daily_performance` | 0 | 0 | HR (→ re-classify) |
| `staff_performance` | 0 | 0 | HR (→ re-classify) |
| `team_performance` | 0 | 0 | HR (→ re-classify) |
| `verification_activity_log` | 0 | 3 | verification activity |

**Honest caveat (does not change the class):** because `authenticated` = DML and RLS is off (I-2, I-5), an authenticated JWT *can* write these tables directly even though no application path does. With 0 rows that is an integrity risk, not a disclosure. Enabling RLS on all 19 is **free** (backend = service-role, I-4); the class says "not required now", not "harmful to enable".

### 5.3 Class C — the 7 non-browser tables that require remediation (the nine browser tables are §4)

| Table | Rows | Reachable by | Evidence | Why C |
|---|---|---|---|---|
| `audit_trail` | **126** | any authenticated JWT (DML) | 37 `.py` / 14 sql refs; columns include `ip_address`, `user_agent`, `old_data`, `new_data`; an immutability trigger exists but **no row filter** | **R-5:** 126 live business-audit rows readable **and writable**; before/after payloads + IP/user-agent are PII/security telemetry |
| `staff_roles` | **1** | any authenticated JWT (DML) | `init_schema.sql:1220-1230` (`permissions JSONB NOT NULL`); 22 `.py` / 7 sql refs | **R-2:** the authoritative permission catalogue is forgeable by any authenticated JWT |
| `password_reset_tokens` | 0 | any authenticated JWT (DML) | `init_schema.sql:332-341` (`token UNIQUE NOT NULL`) | **R-3:** one row = one account takeover; no browser path, so enable-only |
| `manual_extraction_items` | **14** | any authenticated JWT (DML) | 88 `.py` / 15 sql refs; 1 policy (`20260821020000…:102-115`) **inert** (I-6); DDL `init_schema.sql:1139-1161` (`extracted_data`, `mapped_data`, `calculated_emissions_kg_co2e`) | **R-4:** 14 **retained customer rows** (linked to the 2 retained `manual_extraction_batches` by `batch_id`) whose isolation intent is defeated by RLS being off |
| `consultant_billing` | 0 | any authenticated JWT (**SELECT only**) | 0 `.py` / 5 sql refs | Financial rows with `consultant_id` and **no filter** → cross-consultant disclosure the moment rows exist |
| `consultant_tasks` | 0 | any authenticated JWT (DML) | 6 `.py` / 1 sql refs | Per-consultant **and per-client** rows (`consultant_id`, `client_id`) reachable without any ownership predicate |
| `login_history` | 0 | any authenticated JWT (DML) | 0 `.py` / 1 sql refs | Authentication telemetry (`ip_address`, `user_agent`, `session_id`, `is_successful`, `failure_reason`) readable/writable by any authenticated JWT |

**All 7 close with one `ENABLE ROW LEVEL SECURITY` and zero policies** (backend paths are service-role, I-4) — except `manual_extraction_items`, which must be **enable + keep its existing policy** so the retained rows stay reachable to their entity staff. That is the only C table needing care.

### 5.4 Class D — 9 tables requiring an owner decision

Common shape: **0 rows**, **0 browser call sites**, and (for 7) **0 backend references** — so no application code can read or write them today. The only actor that could populate them is a direct PostgREST call by any authenticated JWT (I-5). The content they will hold is user/tenant/staff material, so the package recommended raising them to "remediate".

| Table | Rows | Backend `.py` refs | Content the feature will hold |
|---|---|---|---|
| `conversation_activity_log` | 0 | 0 | per-conversation activity feed |
| `message_activity_log` | 0 | 0 | per-message activity |
| `report_comments` | 0 | 0 | user-authored commentary on a report |
| `report_versions` | 0 | 60 | report artefacts **and storage URLs** |
| `staff_activity_log` | 0 | 0 | per-staff behavioural log |
| `typing_status` | 0 | 0 | live presence |
| `user_activity_log` | 0 | 0 | per-user activity (DDL `init_schema.sql:1761-1770`: `ip_address`, `user_agent`) |
| `user_presence` | 0 | 0 | live presence |
| `verification_logs` | 0 | 0 | verification records over tenant evidence |

**The decision is a single one for all nine (D-6):** *accept as inert scaffolding now and re-classify when each feature ships* **or** *enable RLS on all nine in the same migration as §6.2*. **Recommendation: enable now.** It is free (no browser path to break; backend is service-role), it removes the "someone writes rows a feature does not yet guard" risk, and it makes the FINAL-03 statement honest ("47 RLS-disabled tables" becomes "0 RLS-disabled tables or N explicitly accepted").

---

## 6. PRODUCTION GATE — FINAL DECISION TABLE

### 6.0 Two evidence-driven changes of position (stated explicitly)

1. **`staff_workload` is downgraded from "blocking" to "owner decision".** Package `08` recorded 1 live browser site; this pass proves the site and its two backend counterparts reference **columns that do not exist** (`assigned_reviews`, `in_progress_reviews`, `last_updated`) and that the table has 0 rows → no working path exists to leak or corrupt (§4.7). *Exposure property still holds; required-before-production does not.*
2. **`waitlist` and `beta_users` browser writes are `anon` (already denied).** The pre-auth signup sites cannot be served by any `authenticated` policy (§3.2, §4.2), so the recommended remedy is a backend call, not a policy.

**Numbers are not being bent to the old baseline.** The former claim of `149 / 149 / 271` is **not** the measured state: measured is **134 → 150 public tables, 87 → 103 RLS-enabled, 47 → 47 RLS-disabled** (package `08` §C.0, §B.4). This assessment creates **no** table and **no** policy merely to make a count match; every migration proposed below is justified by a named path.

### 6.1 Findings R-1 … R-6

| Finding | Severity | Production impact | Required before FINAL-03? | Proposed remediation | New migration required? |
|---|---|---|---|---|---|
| **R-1** `system_settings` | **Critical** | Any authenticated JWT can read every settings row and upsert `email_provider` / `platform_notifications` → **production email can be repointed**; the legacy UI write is already dead, so the risk is direct PostgREST | **YES** | Enable RLS + **0 policies**; retire or re-point the 3 legacy sites (`Settings.js:67-71,117-131,155-182`) at the existing `require_admin()` API | **YES** — 1 enablement + app-side re-point (no backend change) |
| **R-2** `staff_roles.permissions` | **Critical** | The authoritative permission catalogue is DML-writable by any authenticated JWT → privilege forgery (`can_manage_backups`, `can_process`, `can_manage_staff`, …); BACKUP-01's grant is a row in this table | **YES** | Enable RLS + **0 policies**; keep staff-role resolution on the service-role client (already the case) | **YES** — 1 enablement, **no app change** |
| **R-3** token material (`password_reset_tokens`, `beta_access_codes`) | **High** | One row = one account takeover; `beta_access_codes` also exposes `magic_token`. No browser path on the former, 3 sites on the latter | **YES** | Enable RLS + **0 policies**; move the 3 beta sites onto the existing backend endpoints | **YES** — 2 enablements + 3 call-site changes |
| **R-4** retained/inert policy (`manual_extraction_items` 14 rows; `conversation_participants` 1 row) | **High** | 14 **retained customer rows** whose policy is inert; 1 conversation membership row world-readable; the product's own isolation intent is unenforced | **YES** | `manual_extraction_items`: enable **+ keep its existing policy**. `conversation_participants`: **enable only** (3 policies already present) | **YES** — 2 enablements, **no new policy** |
| **R-5** `audit_trail` (126 rows) | **High** | Before/after business audit + `ip_address`/`user_agent` readable **and writable** by any authenticated JWT; a trigger gives immutability but **no row filter** | **YES** | Enable RLS + **0 policies** (audit writers are service-role) | **YES** — 1 enablement, no app change |
| **R-6** 23 browser call sites / 9 tables would fail closed | **Medium** | Enabling RLS without the app changes below silently breaks those UI paths — **6 of the 23 sites are already dead** (`notifications`, `staff_workload`, 2 × `beta_access_codes` pre-auth, `system_settings` writes ×2), so the real migration cost is lower than package `08` assumed | **YES** (as the execution order for R-1…R-5) | Execute in this order: (1) `conversation_participants` enable-only; (2) `manual_extraction_items` enable+policy; (3) `system_settings`/`staff_roles`/token tables; (4) audits/logs/PII; (5) class D | **YES** — same migration set |

### 6.2 Every table classified **C** (16) — requires remediation

| Table | Severity | Production impact | Required before FINAL-03? | Proposed remediation | New migration required? |
|---|---|---|---|---|---|
| `system_settings` | **Critical** | R-1 — email repointing / full config disclosure | **YES** | §1.4: RLS + 0 policies; re-point/retire `Settings.js` | **YES** — enablement |
| `staff_roles` | **Critical** | R-2 — permission forgery | **YES** | RLS + 0 policies | **YES** — enablement |
| `password_reset_tokens` | **High** | R-3 — account takeover on first row | **YES** | RLS + 0 policies | **YES** — enablement |
| `beta_access_codes` | **High** | R-3 — `code` + `magic_token` disclosure; invite forgery | **YES** | RLS + 0 policies; 3 sites → existing backend endpoints | **YES** — enablement |
| `beta_users` | **High** | Beta access-list disclosure **and self-grant** (`access_level`) | **YES** | RLS + own-row SELECT policy *or* backend-only; insert → backend | **YES** — enablement (+1 policy if a browser read stays) |
| `conversation_participants` | Medium | R-4 — all memberships enumerable; 3 inert policies | **YES** | **Enable only** (3 policies exist) | **YES** — enablement, no new policy |
| `email_logs` | High | Recipient PII + delivery metadata to any authenticated JWT | **YES** | RLS + 0 policies; admin page → `routes/admin/logs.py` | **YES** — enablement |
| `notifications` | High | All recipients' notifications readable/writable | **YES** | RLS + 0 policies; delete the dead `WorkHub.jsx` read | **YES** — enablement |
| `review_audit_trail` | High | Trail readable **and forgeable** | **YES** | RLS + 0 policies; 5 sites → existing backend routes | **YES** — enablement |
| `staff_workload` | **Low (downgraded)** | Latent only: 0 rows, no working path (§4.7) | **NO — owner decision** | RLS + 0 policies (free) + delete the 3 dead column references | **YES** only if the owner takes the hygiene option |
| `waitlist` | Medium | Prospect PII readable/tamperable | **YES (recommended)** | RLS + 0 policies; admin list → backend | **YES** — enablement |
| `audit_trail` | High | R-5 — 126 rows of before/after audit read+write | **YES** | RLS + 0 policies | **YES** — enablement |
| `manual_extraction_items` | High | R-4 — 14 retained customer rows; policy inert | **YES** | **Enable + keep its existing policy** (entity-staff reachability) | **YES** — enablement only |
| `consultant_billing` | Medium | Cross-consultant billing disclosure (SELECT-only privilege) | **YES** | RLS + 0 policies | **YES** — enablement |
| `consultant_tasks` | Medium | Per-consultant/per-client task disclosure | **YES** | RLS + 0 policies | **YES** — enablement |
| `login_history` | Medium | Auth telemetry (`ip`, `user_agent`, `session_id`, failure reasons) read/write | **YES** | RLS + 0 policies | **YES** — enablement |

### 6.3 Every table classified **D** (9) — owner decision (D-6)

| Table | Severity | Production impact | Required before FINAL-03? | Proposed remediation | New migration required? |
|---|---|---|---|---|---|
| `conversation_activity_log` | Low (latent) | 0 rows / 0 code refs; would hold per-conversation activity | **OWNER DECISION (D-6)** | Enable now (free) *or* accept + gate at feature time | Only if "enable now" |
| `message_activity_log` | Low (latent) | 0 rows / 0 refs; per-message activity | **OWNER DECISION (D-6)** | as above | Only if "enable now" |
| `report_comments` | Low (latent) | 0 rows / 0 refs; user commentary | **OWNER DECISION (D-6)** | as above | Only if "enable now" |
| `report_versions` | Low (latent) | 0 rows; 60 backend refs; report artefacts + **storage URLs** | **OWNER DECISION (D-6)** | as above (recommended: enable now) | Only if "enable now" |
| `staff_activity_log` | Low (latent) | 0 rows / 0 refs; per-staff behavioural log | **OWNER DECISION (D-6)** | as above | Only if "enable now" |
| `typing_status` | Low (latent) | 0 rows / 0 refs; live presence | **OWNER DECISION (D-6)** | as above | Only if "enable now" |
| `user_activity_log` | Low (latent) | 0 rows / 0 refs; `ip_address`/`user_agent` columns | **OWNER DECISION (D-6)** | as above | Only if "enable now" |
| `user_presence` | Low (latent) | 0 rows / 0 refs; live presence | **OWNER DECISION (D-6)** | as above | Only if "enable now" |
| `verification_logs` | Low (latent) | 0 rows / 0 refs; verification records over tenant evidence | **OWNER DECISION (D-6)** | as above | Only if "enable now" |

### 6.4 Explicit category assignment (the four distinctions the owner asked for)

| Category | Members |
|---|---|
| **Security remediation required before production** | **C (16 tables)** and findings **R-1…R-6**. Of these, **15 tables are hard-blocking**; `staff_workload` is downgraded to owner-decision (§6.0). The blocking work is: **15 RLS enablements + 1 policy retention + 9 browser call-site moves/deletions** (the other 14 of the 23 sites are backend-only or already dead) |
| **Owner decision required** | **D-1** P2 freeze ratification · **D-2** RLS decision (accept the plan in §6.1–6.3 or accept risk in writing) · **D-3** step-7 gate replacement · **D-4** R-2: none (no choice needed) · **D-6** the **9 class-D tables** · the **`staff_workload` hygiene choice** · whether the legacy `Settings.js` / `BetaManagement.js` / `Waitlist` admin pages are retired |
| **Documentation-only discrepancy** | `149 / 149 / 271` is not the measured state (§6.0) · the ±1 org-linked total (**102** measured vs **101** cited, package `08` §B.3) · the ~6 dead browser call sites and the 3 dead `staff_workload` column references · `routes/waitlist.py` POST/GET being `pass` stubs while the admin page calls 3 non-existent endpoints · `upload.py` still reading the non-existent `settings_json` column. None of these is a security control and **none justifies a migration** |
| **Intentionally accepted architecture** | **Class A** (3): `emission_factors` (containment proven by grants), `business_hours`, `sla_definitions` · **Class B** (19) for as long as the feature is unshipped, with the standing re-classification gate · `service_role` = ALL on all 47 (I-3/I-4) is the deliberate backend trust model, **not** a defect · the public `GET /api/v3/settings/analytics` (GA4 id only) · `anon` = NONE everywhere (I-1) |

### 6.5 What one authorisable change-set would contain (assessment, not implementation)

1. **One new migration** (dated after `20261027000000`, explicitly owner-authorised) containing `ALTER TABLE … ENABLE ROW LEVEL SECURITY` for the C tables (excluding any the owner accepts) — **zero new policies**, except: keep the existing `manual_extraction_items` policy; and add **at most one** policy per table only where a browser read must survive (`conversation_participants` already covered; `beta_users` own-row; `waitlist` admin-only — the last needs a platform-admin predicate that does not exist today, which is itself a reason to move that read to the backend instead).
2. **App changes** (no backend redesign): re-point or delete the 23 sites — realistically **6 moves to existing backend endpoints + 6 deletions of dead paths + the `conversation_participants` reads left in place**.
3. **Class B and class D**: enable in the same migration if the owner chooses "enable now" (free, and it makes the count honest).
4. **No** auth change, **no** token-handling change, **no** `system_settings` value change, **no** `staff_roles` value change, **no** production data change.

---

## 7. P2 / P5 / P6 — READINESS REPORT ONLY (nothing executed)

### 7.1 P2 — freeze manifest: **OPEN (awaiting ratification)**

- The manifest is **reconciled but not committed**: `HEAD = cabdca8380415e73a25cf23eb393d0b15c0af391`, and **23 required paths are untracked**, so HEAD **is not deployable as-is** (package `08` §A.0/§A.7).
- Four ambiguities require a ruling (`AMBIG-1` `.gitignore` CRLF→LF + `+.aider*`; `AMBIG-2` `frontend/App_.js` zero importers; `AMBIG-3/4` the `docs/architecture/` include/exclude line) and **`PRECOND-1`** — a plaintext **local** (loopback, throwaway `ct_b7_schema_*`) DSN inside `docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/clone-dsn-used.txt` — **blocks the commit** until redacted or excluded.
- Exact commit procedure (branch + 5 grouped `git add` path-spec sets) is specified in package `08` §A.7 and was **not** run.
- **Decision needed:** D-1 (ratify as-is · amend · reject).

### 7.2 P5 — backup to the production object store: **OPEN — BLOCKING**

- **No `CT_BACKUP_*` value exists in this environment and none was invented.** The code **fails closed**: `CT_BACKUP_OBJECT_STORE` defaults to `local`; `CT_BACKUP_ENCRYPTION_KEY` has **no default** and must be standard-base64 decoding to exactly 32 bytes (AES-256), otherwise `BackupConfigurationError` is raised before any work starts (package `08` §D.1).
- **17 variables are required by the module (+2 used elsewhere)** — the owner brief named 8; the 9 extra (bucket identity, credentials, prefix, temp root, key id, schemas, compression, readback verification, prune/retention) are load-bearing.
- **10 owner inputs pending** (package `08` §D.2), the most important being the **encryption-key escrow/ownership answer**: *if the key is lost the backups are unrecoverable*.
- Acceptance path once supplied: run with `CT_BACKUP_OBJECT_STORE=s3` + `CT_BACKUP_VERIFY_READBACK=1` + encryption → confirm the manifest records the right `key_id` → **restore-verify into a scratch schema** (the pattern the local B7 gate already used).
- **Risk coupling:** P4 (managed PITR) is satisfied only by commitment, so **this backup is the only recovery path for the retained data** — and it is unproven in production (package `08` §G).
- **Decision needed:** D-4.

### 7.3 P6 — Render / Vercel / email identity: **OPEN — BLOCKING**

- **Render:** service identity (name/ID, region, plan, type), source repo + **branch** (must be the P2 freeze branch — which does not exist), build/start commands, health-check path, pool sizing, and the env set (release-critical list in package `08` §E.1; `DATABASE_URL` must be the **production service-role** DSN, not the read-only probe DSN used for this analysis).
- **Vercel:** project identity, production domain, build settings and the frontend env set; `REACT_APP_API_URL` is the cutover link and `REACT_APP_OAUTH_REDIRECT_URL` must match the deployed domain exactly (package `08` §E.2).
- **Email:** provider choice (`resend` \| `smtp`), **sender identity** (from-address + display name), SMTP transport parameters, and the matching secret (`RESEND_API_KEY` or `CT_SMTP_PASSWORD`) — provider *selection* and *sender* are **database** settings, only the secret is an env var (package `08` §E.3).
- **Security coupling:** because the sender configuration lives in `system_settings`, **P6 cannot be signed off until that row's production values are confirmed and its write access is gated** (R-1). The email cutover is therefore also a security control, not only a deploy task.
- **Decision needed:** D-5.

> **Readiness line (unchanged by this pass): `FINAL-03 DATA PRESERVATION PLAN READY — AWAITING P2/P5/P6 + RLS DECISION`, now with R-1/R-2/R-3 converted into an authorisable remediation.**

---

## 8. FILES INSPECTED (exact) AND EVIDENCE FOR EVERY PRODUCTION-IMPACTING CONCLUSION

### 8.1 Files inspected this pass

**Backend (`/home/shomonrobie/ct_93d5cdd/backend/`)** — `database.py`, `auth.py`, `api/v3_settings.py`, `api/operations_auth.py`, `api/insight_authz.py`, `api/pe_auth.py`, `api/v3_operations.py`, `api/v3_messaging.py`, `data/settings.py`, `data/staff.py`, `data/notifications.py`, `data/messaging.py`, `services/email_provider.py`, `services/email_sender.py`, `services/v3_email.py`, `services/email_service.py`, `services/retention.py`, `utils/email.py`, `utils/upload_limits.py`, `utils/staff_workload.py`, `utils/__init__.py`, `backup/policy.py`, `routes/upload.py`, `routes/users.py`, `routes/waitlist.py`, `routes/admin/settings.py`, `routes/admin/beta.py`, `routes/admin/logs.py`, `routes/admin/review_history.py`, `routes/admin/staff.py`, `routes/admin/reviews.py`, `routes/admin/workload.py`.

**Frontend / admin** — `admin/src/App.js`, `admin/src/supabaseClient.js`, `admin/src/pages/admin/Settings.js`, `admin/src/pages/admin/WorkHub.jsx`, `admin/src/pages/admin/BetaManagement.js`, `admin/src/services/reviewService.js`, `frontend/src/App.js`, `frontend/src/BetaSignup.jsx`, `frontend/src/BetaLogin.jsx`, `frontend/src/components/chat/ChatWidget.jsx`, `frontend/src/components/chat/ChatWindow.jsx`, `frontend/src/context/RealtimeContext.jsx`, `frontend/src/lib/realtime/manager.js`, `frontend/src/lib/analytics/ga4.js`, `frontend/src/v3/api.js`, `frontend/src/v3/ops/StaffRolesTab.jsx`, `frontend/src/v3/ops/StaffRoster.jsx`.

**Migrations / schema** — `supabase/migrations/00000000000000_init_schema.sql` (DDL extracts: `password_reset_tokens` 332-341, `beta_access_codes` 375-386, `beta_users` 390-400, `waitlist` 404-417, `conversation_participants` 695-705, `manual_extraction_items` 1139-1161, `staff_roles` 1220-1230, `staff_workload` 1253-1264, `notifications` 1409-1425, `email_logs` 1748-1757, `review_audit_trail` 1870-1882, `system_settings` 2022-2084, `queue_settings` 2089-2097), `20260821020000_d22_processing_work_assignment.sql`, `20260822010000_d27_d19_customer_lifecycle.sql`, `20260902040000_phase5_pe_operational_messaging.sql`, `20260924000000_p8x_x2_operational_telemetry_retention.sql`, `20261026000000_ct_backup_01_backup_jobs.sql`, plus repo-wide searches for `ENABLE ROW LEVEL SECURITY`, `settings_json`, `max_file_size_mb`, `magic_token`.

**Evidence documents** — `08-final-03-p2-p5-p6-rls-decision-package-20261002.md` (read in full), `03-schema-drift-and-rls.txt`, `05-rls-prohibition-and-storage.txt`, `07-production-public-tables.txt`.

### 8.2 Conclusion → exact evidence

| # | Production-impacting conclusion | Evidence |
|---|---|---|
| 1 | RLS enablement cannot break the backend (service-role everywhere) | `backend/database.py:19,28,42,53,57`; package `08` §C.0 F7 |
| 2 | Any authenticated JWT reaches every DML table via PostgREST | package `08` §C.0 F3b/F8; browser client `admin/src/supabaseClient.js:59` |
| 3 | **R-1** the browser write path is dead code (columns do not exist; `setting_key`/`setting_value` NOT NULL) | `admin/src/pages/admin/Settings.js:117-131,155-182`; `init_schema.sql:2022-2084`; repo-wide: no `settings_json`, no `max_file_size_mb` |
| 4 | **R-1** every settings write is already admin-only in the backend | `backend/api/v3_settings.py:216,227,276,310,334,369,390,423,448,483`; `backend/routes/admin/settings.py:38-55,119-159`; `backend/data/settings.py:662-688` |
| 5 | **R-1** production email provider/sender live in this table | `backend/services/email_provider.py:9-14,55-56`; `backend/services/email_sender.py:31,34,39`; `backend/services/v3_email.py:28-60` |
| 6 | **R-2** `staff_roles` has zero browser call sites; the UI reads it through an API | `frontend/src/v3/ops/StaffRolesTab.jsx:2,16,29`; `backend/api/v3_operations.py:2649-2659` |
| 7 | **R-2** the JSONB is the enforcement input (hence DB-level protection is required) | `backend/api/operations_auth.py:158-173,205-211`; `backend/auth.py:249-266,804-814`; `backend/api/insight_authz.py:134-143`; `backend/data/staff.py:241,249`; `backend/data/notifications.py:174,223` |
| 8 | **R-2** BACKUP-01 writes the catalogue at migration time (not a browser vector) | `supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql:173-185` |
| 9 | **R-3** `password_reset_tokens` is service-role only, browser-none | `backend/routes/users.py:81,125,163`; repo-wide search: no frontend reference; DDL `init_schema.sql:332-341` |
| 10 | **R-3** `beta_access_codes` exposes `code` **and `magic_token`**; 2 of 3 sites are pre-auth (`anon`) | `init_schema.sql:375-386`; `frontend/src/BetaSignup.jsx:35-39,123-129`; `admin/src/pages/admin/BetaManagement.js:97-104` |
| 11 | **R-3** a session-free validation endpoint already exists | `backend/routes/admin/beta.py:215-218`; list endpoint `:54` |
| 12 | **R-4** `conversation_participants` has 3 policies that are inert | `20260822010000_d27_d19_customer_lifecycle.sql:199-209`; `20260902040000_phase5_pe_operational_messaging.sql:139-143`; no RLS enablement for this table anywhere in the migration set |
| 13 | **R-4** `manual_extraction_items` has 1 inert policy over retained rows | `20260821020000_d22_processing_work_assignment.sql:102-115`; retention provenance package `08` §B.2/B.3 |
| 14 | **R-5** `audit_trail` = 126 rows, DML, no row filter | package `08` §C.1 row 3 |
| 15 | **R-6 / §4** the 23 browser sites and their exact operations | `admin/src/services/reviewService.js:40-48,68-74,122-129,135-144,183-192`; `admin/src/pages/admin/WorkHub.jsx:193-198,249-253`; `admin/src/pages/admin/BetaManagement.js:34-50,57-66,97-104`; `frontend/src/BetaSignup.jsx:35-39,83-87,123-129,132-139,142-148`; `frontend/src/BetaLogin.jsx:72-76,135-139`; `frontend/src/lib/realtime/manager.js:397-408`; `frontend/src/components/chat/ChatWidget.jsx:40-44,57-70`; `frontend/src/components/chat/ChatWindow.jsx:108-115`; `admin/src/pages/admin/Settings.js:67-71,117-131,155-182` |
| 16 | §4.5 `notifications` browser read targets a non-existent column (`user_id`) | `WorkHub.jsx:196` vs DDL `init_schema.sql:1409-1425` (`recipient_id`, `recipient_type`); intended posture at `frontend/src/context/RealtimeContext.jsx:274-279` |
| 17 | §4.7 `staff_workload` has no working path (3 non-existent columns, 0 rows) | `WorkHub.jsx:251`; `backend/routes/admin/reviews.py:50`; `backend/routes/admin/staff.py:365` vs DDL `init_schema.sql:1253-1264` |
| 18 | §4.9 the waitlist backend is stubs; 3 admin endpoints do not exist | `backend/routes/waitlist.py:6,17,22`; `admin/src/pages/admin/BetaManagement.js:72,115,140,164` |
| 19 | §4.4 `email_logs` already has an admin-gated backend reader | `backend/routes/admin/logs.py:20,34,71,104,155`; writes `backend/utils/email.py:log_email`, `backend/services/email_service.py:217` |
| 20 | §4.6 review-audit writes bypass the backend route that exists | `backend/routes/admin/review_history.py:113-124,145-155` |
| 21 | §4.3 browser writes to messaging membership were already removed (server-authoritative) | `frontend/src/components/chat/ChatWidget.jsx:196-201`; `backend/api/v3_messaging.py`; `backend/data/messaging.py:183-187` |
| 22 | §5 class A containment (`emission_factors` has no authenticated privileges) | package `08` §C.0 F3b + §C.1 row 13; `07-production-public-tables.txt` |
| 23 | Only two of the 47 hold data today (126 + 14 rows); one is org-linked | package `08` §B.3/B.4 |
| 24 | No migration enables RLS on any of the 47 (so enablement is always new work) | package `08` §C.0 (verified twice); re-verified this pass by table-scoped search |

---

## 9. HARD STOP — COMPLIANCE STATEMENT

**Nothing was implemented.** In this pass, and by this document:

- **no SQL** was written, **no RLS migration** was created, **no existing migration** was modified, **no migration** was applied;
- **no production** object was changed and no production row was written; the only production facts used are the read-only probes already recorded in package `08`;
- **no** local/demo data was modified; **no** Render or Vercel deployment was made;
- **no** authentication behaviour was changed; **`system_settings`**, **`staff_roles`** and **token handling** were **not** changed;
- the **only** artefact produced is this evidence document.

**The brief is converted into a decision.** R-1, R-2 and R-3 each now have: a traced path inventory, a determination of what the browser genuinely needs (nothing that cannot be served by an existing admin/backend endpoint — the previous browser writes are either already dead or pre-auth-and-denied), a minimum safe boundary (**RLS enabled with zero policies**, because the backend is service-role on every path), and a concrete recommended target state. All nine browser-accessed tables carry the ten required answers; the remaining 38 tables are classified A/B/C/D exactly once with stated tests; and the production gate is expressed as a decision table with the four categories separated. The next step is an **owner authorisation (D-2, D-6, plus the downgrade rulings)**, not more analysis.

*End of assessment.*


---
