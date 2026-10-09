# CT-FEATURE-01 / Deliverable 2 — CarbonTally Configuration Catalogue

**Task ID:** `CT-FEATURE-01-20260927-CARBONTALLY-COMPLETE-FEATURE-AND-FUNCTIONALITY-CATALOGUE-FROM-SCHEMA-CODE-AND-HISTORICAL-EVIDENCE`
**Type:** READ-ONLY forensic discovery — **no implementation, no migration, no seed, no deployment, no push**
**Date:** 2026-09-27
**Canonical tree:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (branch `p8-release-reconciled`)
**Companion documents:** feature catalogue (deliverable 1), traceability (3), gap analysis (4), discovery report (5)

---

## 0. Scope and reading rules

This catalogue records **every configuration surface that changes CarbonTally
behaviour** — what can be configured, where the value lives, what the live value
is, who may change it, and whether the value is actually read by running code.

1. **Configuration ≠ feature.** A feature is catalogued in deliverable 1; here it
   appears only when it exposes a configurable value.
2. **"Configurable" is proven by a read path**, not by the existence of a column.
   A typed column that no code reads is recorded as `SCHEMA_ONLY` and listed in
   §6 as inert, not counted as a working control.
3. **Live values are quoted from the flagship local database** (`postgres`) as read
   on 2026-09-27, with the caveat in §1.3: the flagship ledger stops at
   `20260903010000`, so a value can be *configured* and still not be the value a
   release-tree build would read.
4. **No secret, key, token or signed URL is reproduced.** Where a value is
   sensitive (service keys, JWT secrets, DB URLs) only the *variable name* and its
   purpose are recorded.
5. **Defaults are not policy.** A documented fallback in code (e.g. SLA 48 h) is
   recorded as a fallback, not as an approved value — the platform's own
   `is_configured()` guard exists precisely to distinguish the two
   (`backend/data/queue_settings.py`).

### 0.1 Configuration classes used throughout

| Class | Surface | Where the value lives |
|---|---|---|
| **C1** | Platform settings rows | `system_settings` (key/value row + typed columns) |
| **C2** | Commercial configuration | `billing_commercial_config`, `billing_plans` |
| **C3** | Queue / SLA configuration | `queue_settings`, `sla_definitions`, `sla_compliance` |
| **C4** | Runtime environment variables | process environment (backend / frontend / admin) |
| **C5** | Build-time variables | injected into bundles by the build tooling |
| **C6** | Code constants / hard-coded policy | source files (must be justified, never policy) |
| **C7** | Policy configuration | RLS policies, grants, storage policy |
| **C8** | Administrative surfaces | admin control plane, ops tabs, settings APIs |

---

## 1. Method and sources

### 1.1 Sources inspected

| Source | What was taken from it |
|---|---|
| `supabase_db_carbon_ledger` (PostgreSQL 17.6), database `postgres` | live table/column inventory, live configuration values, row counts, RLS counts, migration ledger |
| `supabase/migrations/*.sql` (89 files) | declared settings columns, PO-approved defaults, environment constraints |
| `backend/data/settings.py`, `queue_settings.py`, `billing.py` | the actual read/write paths for each setting |
| `backend/api/v3_settings.py`, `v3_commercial.py`, `v3_operations.py` | which configuration is exposed by API and behind which guard |
| `backend/routes/admin/settings.py`, `routes/upload.py` | legacy administrative and upload-limit reads |
| `backend/config.py`, `tools/demo_lab/backend.env.example` | environment-variable contract |
| `frontend/src`, `admin/src` | build-time variables actually referenced |

### 1.2 Commands used (read-only)

```sql
-- inventory
select table_name from information_schema.tables where table_schema='public' and (... ilike '%setting%' ...);
select table_name, column_name, data_type, column_default from information_schema.columns where table_schema='public' and ...;
select setting_key, setting_value, audit_log_retention_days, ... from public.system_settings;
select config_key, config_value from public.billing_commercial_config;
select setting_key, setting_value, description from public.queue_settings;
```

Executed with `docker exec supabase_db_carbon_ledger psql -U postgres -d postgres -Atc "…"`.
**No** DDL, DML, `VACUUM`, `ANALYZE`, migration or configuration write was issued.

### 1.3 The environment caveat that governs every value below

| Fact (live, 2026-09-27) | Consequence for configuration |
|---|---|
| Flagship ledger `supabase_migrations.schema_migrations` = **46 rows**, newest `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | Any setting introduced by a later migration is **absent** in the flagship even though the release tree expects it |
| 89 migration files on disk → **43 unapplied** (`20260905000000` → `20261020000000`) | Settings introduced by those 43 files are `NOT-APPLIED` here |
| P17 schema exists only in disposable clone `ct_p17k_20260926` | P16-R/P17 configuration cannot be verified durably |
| 116/116 public tables have RLS enabled; **174** policies | Configuration administration is subject to RLS as well as API guards |

---

## 2. Configuration surface map

| Class | Surface | Storage object | Exposed by | Guard | Live state (flagship) |
|---|---|---|---|---|---|
| C1 | Retention policy (N3) | `system_settings` row `setting_key='platform_retention'` | `GET/PUT /api/v3/settings/retention` | `require_admin()` | **present**: audit 1 / data 365 / document 365 / backup 365 |
| C1 | Analytics & Integrations (GA4 only) | `system_settings` row `setting_key='analytics_ga4'` (`setting_value` JSONB) | `GET /api/v3/settings/analytics` (**public**), `PUT` admin | `require_admin()` on write | **present**: enabled, one GA4 measurement ID |
| C1 | Legacy typed platform settings (~50 columns) | `system_settings` typed columns | legacy `routes/admin/settings.py`, `routes/upload.py` | legacy admin auth | columns exist; **only retention/upload subsets are read** |
| C2 | Commercial configuration | `billing_commercial_config` (`config_key`/`config_value` + effective dating) | `/api/v3/commercial/*` | staff/admin authority | **7 keys live** (§3.3) |
| C2 | Subscription plans | `billing_plans` (versioned, effective-dated) | `/api/v3/commercial/*` | staff/admin authority | **6 rows live** (§3.4) |
| C2 | Credits | `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`, `customer_subscriptions`, `consultant_billing` | billing APIs | RLS + service authorization | all **0 rows** — billing never exercised |
| C3 | Review-queue SLA defaults | `queue_settings` row `setting_key='review_sla_defaults'` | `/api/v3/operations` (queues/SLA) | staff authority | **1 row live** (§3.2) |
| C3 | SLA catalogue / compliance | `sla_definitions`, `sla_compliance` | operations APIs | staff authority | tables exist (row counts not asserted here) |
| C4 | Runtime environment | process env | — | deployment | §4 |
| C5 | Build-time identity | bundle vars | — | build | §4.2 |
| C6 | Code constants | source | — | code review | §5.3 (PO-approved constants only) |
| C7 | RLS/grants/storage policy | 174 policies, 116 RLS tables | Supabase | DBA | **enabled everywhere** |
| C8 | Administrative surfaces | admin control plane + ops Settings tabs | UI | role-gated server-side | see deliverable 1 FTR-008/009/210 |

---

## 3. Live database configuration inventory (flagship `postgres`, read 2026-09-27)

### 3.1 `system_settings` — one table, two configuration models

The table carries **63 columns** and **2 rows**. The two models coexist and must
not be conflated:

| Model | Shape | Managed by | Rows live |
|---|---|---|---|
| **Key/value** | `setting_key` (unique), `setting_value` JSONB, `description`, `updated_by` | `data/settings.py` (analytics), `data/queue_settings.py` (SLA — different table), API `v3_settings.py` | `platform_retention`, `analytics_ga4` |
| **Typed columns** | ~50 named columns with `column_default` | legacy `routes/admin/settings.py`, `routes/upload.py`, the retention columns via `data/settings.py` | same 2 rows |

**Verified live values:**

| `setting_key` | typed `audit` | `data` | `document` | `backup` | `setting_value` (JSONB) |
|---|---|---|---|---|---|
| `platform_retention` | **1** | **365** | **365** | **365** | `{"audit_log_retention_days":1,"data_retention_days":365,"document_retention_days":365,"backup_retention_days":365}` |
| `analytics_ga4` | NULL | NULL | NULL | NULL | `{"enabled":true,"ga4_measurement_id":<set, withheld>}` |

Two facts a reader must take from this table:

1. **The retention values are duplicated** — typed columns *and* the JSONB payload
   carry the same four numbers. The API (`data/settings.py`) reads and writes the
   **typed columns** only. The JSONB copy is therefore a second source of truth
   that no verified write path maintains (finding **CFG-2**, §6).
2. **`audit_log_retention_days = 1`** — one day of audit retention against 365 for
   data, documents and backups. Raised as **POD-E**; tension with AGENTS §42.

**Typed columns present but with no verified read path in the release tree**
(inert configuration — no control is exposed and no behaviour changes):
`default_language`, `default_timezone`, `default_region`, `default_reporting_standard`,
`date_format`, `time_format`, `number_format`, `week_start_day`,
`default_emission_factor_year`, `carbon_tax_region`, `carbon_tax_rate`,
`carbon_tax_unit`, `emission_verification_required`, `emission_verification_standard`,
`sla_default_hours`, `sla_escalation_hours`, `sla_breach_alert_enabled`,
`sla_breach_alert_recipients`, `api_rate_limit`, `api_rate_limit_burst`,
`webhook_retry_count`, `webhook_retry_delay`, `webhook_timeout_seconds`,
`session_timeout_minutes`, `session_extend_on_activity`, `two_factor_required`,
`two_factor_method`, `password_expiry_days`, `password_min_length`,
`password_require_special`, `password_require_number`, `password_require_uppercase`,
`password_require_lowercase`, `login_attempts_max`, `login_attempts_lockout_minutes`,
`backup_frequency`, `backup_storage_location`.

**Typed columns with a verified read path:** `audit_log_retention_days`,
`data_retention_days`, `document_retention_days`, `backup_retention_days`
(read and written by `data/settings.py`), `default_currency`
(column default `'GBP'`), `default_emission_factor_set`.

**A third naming set exists and does not match the schema.** The legacy upload
router (`backend/routes/upload.py::get_system_settings`) asks
`system_settings` for `settings_json`, `max_file_size_mb`, `allowed_file_types`,
`enable_auto_repair`, `max_batch_files`, `max_total_batch_size_mb` and
`data_retention_days`. **None of the first six exist as columns** in the live
table, and the read is issued with `.maybe_single()` against a table that
currently holds **2 rows** — a shape PostgREST rejects, which sends the call down
the router's `except` branch. Every upload therefore runs on the router's
hard-coded fallbacks (50 MB per file, 20 files per batch, 200 MB per batch,
PDF/CSV/XLSX/JPG/PNG allowed, 365-day data retention) regardless of what is
stored. The `max_upload_size_mb` / `max_batch_size_mb` / `max_file_upload_daily`
/ `max_documents_per_batch` / `max_pages_per_document` columns are consequently
**never read by any code path found in either tree** (finding **CFG-3**, §6).

### 3.2 `queue_settings` — review/SLA defaults (one row, JSONB)

| Field | Live value | Source of truth |
|---|---|---|
| `sla_hours` | 48 | stored |
| `escalation_hours` | 24 | stored |
| `max_reviews_per_staff` | 5 | stored |
| `auto_assign_enabled` | true | stored |
| `priority_weights` | `{"high":1.0,"medium":0.6,"low":0.3}` | stored |

Repository: `backend/data/queue_settings.py`, key `review_sla_defaults`. The
repository deliberately exposes `is_configured()` and returns *documented
fallbacks* (identical numbers) when the row is absent, so that **an SLA alert can
never be raised from a fallback the PO has not approved** (its own docstring says
so). Surfaced to operations through `/api/v3/operations` (`"sla": …`).

> Configuration lesson worth carrying: this is the only settings surface in the
> catalogue that distinguishes *configured* from *not configured*, and it is the
> behaviour AGENTS §42/N3 expects of every configurable value.

### 3.3 `billing_commercial_config` — commercial configuration (7 keys live)

Versioned, effective-dated key/value rows (`config_key`, `config_value` JSONB,
`version`, `effective_from`, `effective_to`, `reason`, `created_by`,
`updated_by`). Repository: `backend/data/billing.py`; API: `/api/v3/commercial/*`.

| `config_key` | Live value (abridged) | What it configures |
|---|---|---|
| `default_billing_mode` | `{"mode":"CREDIT"}` | credit vs allowance as the default commercial mode |
| `credit_rules` | classes `simple` 1 / `standard` 2 / `complex` 4 / `exceptional` quoted | credits consumed per document class |
| `credit_policy` | rollover enabled; `expiry_months` **null**; `max_carryover_pct` **null**; emergency allowance enabled at 10 % | credit rollover and emergency allowance |
| `assisted_pricing` | simple 0.99 / standard 1.99 / complex 3.99 USD; exceptional `quoted: true` | per-document assisted-processing price |
| `structured_data_bands` | bands: 1/3/10/30/100 units then `custom` (1k / 10k / 50k / 250k / 1M rows) | structured-data (CSV/XLSX) unit bands |
| `storage` | unit GB, currency GBP, `included_bytes` 0, `markup_percent` 100, `additional_rate_per_gb` **null** | storage billing basis |
| `standard_allowance` | currency GBP, `monthly_processing_units` **null**, `additional_rate` **null** | standard-allowance basis |

**Reading this honestly:** the *mechanism* is implemented (`billing_commercial_config`
is read through `data/billing.py` with effective dating), but several commercial
values are **absent** (`null`) — storage per-GB rate, standard allowance size and
additional rate, credit expiry and carry-over cap. Nulls are not zero: they mean
**the commercial policy is not yet configured**, so any calculation depending on
them has no approved basis. PO decision required (POD-K, §7).

### 3.4 `billing_plans` — plan catalogue (6 rows live, versioned)

Plans are versioned rows with effective dating, so a plan change is a new version
rather than an edit. Live catalogue:

| Plan | Version | Currency | Price | Credits | Team limit | Storage included | Managed | Assisted |
|---|---|---|---|---|---|---|---|---|
| Starter | v1 | GBP | 0 | 10 | 3 | 10 GiB | no | no |
| Starter | v2 | USD | 49 | 100 | 3 | 20 GiB | no | no |
| Professional | v1 | GBP | 149 | 500 | 10 | 50 GiB | no | yes |
| Business | v1 | GBP | 299 | 1,500 | 25 | 200 GiB | yes | yes |
| Business | v2 | USD | 399 | 2,000 | 25 | 500 GiB | yes | yes |
| Enterprise | v1 | GBP | 0 | 0 | *unset* | 0 | yes | yes |

**Observations that belong in a configuration catalogue, not in a marketing page:**

1. **Two currencies in the live catalogue** (GBP v1 rows and USD v2 rows) while
   `system_settings.default_currency = 'GBP'`. This is a commercial-policy
   question, not a bug to be silently "fixed" (POD-L, §7).
2. **Starter v1 is superseded** (`effective_to` set) and Starter v2 is current —
   the versioning model works as designed and must be preserved.
3. **Enterprise** is price 0 / credits 0 with `custom: true` and
   `managed_processing_available: true` — a quotation-only plan.
4. `processing_limits` differ between v1 and v2 of the same plan
   (`structured_data_units` 2,000 → 5,000 for Business), demonstrating that plan
   shape changes are recorded as versions rather than overwritten.

---

## 4. Environment-variable catalogue (class C4/C5)

Variables were extracted from `os.getenv(...)`/`os.environ[...]` usage in both
trees and classified by **where they are read**. Names observed only inside
third-party libraries (libpq, ONNX Runtime, pytest, Sphinx, pydantic, NumPy) are
listed last and are **not** CarbonTally configuration.

### 4.1 Backend runtime variables (V3 infrastructure)

| Variable | Read at | Default | Purpose | Sensitive |
|---|---|---|---|---|
| `APP_ENV` / `ENV` | `backend/infra/config.py:117` | `development` | environment name driving infra behaviour | no |
| `LOG_LEVEL` | `backend/infra/config.py:123` | `INFO` | log verbosity | no |
| `EVENT_BUS_MAX_HANDLERS` | `backend/infra/config.py:125` | documented fallback | event-bus handler cap | no |
| `SEARCH_INDEX_DEFAULT_LIMIT` | `backend/infra/config.py:129` | documented fallback | default search page size | no |
| `AUDIT_DEFAULT_ACTOR` | `backend/infra/config.py:132` | `system` | actor recorded when no user context exists | no |
| `AUDIT_BATCH_SIZE` | `backend/infra/config.py:134` | documented fallback | audit write batching | no |
| `CACHE_DEFAULT_TTL_SECONDS` | `backend/infra/config.py:138` | documented fallback | default cache TTL | no |
| `DATABASE_URL` / `SUPABASE_DB_URL` | `backend/infra/supabase.py:76` | none | asyncpg connection for V3 repositories | **yes** |
| `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL` | `backend/infra/supabase.py:57` | none | Supabase project URL | no |
| `PORT` / `HOST` / `RELOAD` | `backend/main.py:456-458` | `8000` / `0.0.0.0` / `true` | uvicorn binding | no |
| `CARBONTALLY_AI_BASE_URL`, `CARBONTALLY_AI_MODEL`, `CARBONTALLY_AI_API_KEY` | `backend/infra/ai_runtime.py`, `services/insight_interactions.py` | model/base unset | AI runtime for Insight features | **API key yes** |
| `TESSERACT_CMD` | `backend/pdf_engine.py:85` | unset → `pytesseract` default | explicit OCR binary path; absence degrades gracefully (`tesseract_available()`), exactly as AGENTS §20 requires | no |

### 4.2 Backend legacy variables (`backend/config.py`)

| Variable | Default | Notes |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` | none | **service-role** credentials; must never be exposed to any browser bundle |
| `SUPABASE_SERVICE_ROLE_KEY` | none | alternative service-role name read elsewhere |
| `RESEND_API_KEY` | none | outbound email |
| `FOUNDER_EMAIL` | **hard-coded `shomonrobie@gmail.com`** | default notification recipient — a personal address compiled into the release tree (finding **CFG-6**) |
| `ALLOWED_ORIGINS`, `CORS_*` | **hard-coded list of 10 origins** in `config.py` | not environment-overridable; adding a frontend domain is a source change + redeploy |

**CORS, precisely:** `backend/main.py:175` passes `allow_origins=Config.ALLOWED_ORIGINS`
with `allow_credentials=True` and an explicit method/header list. Because
Starlette matches `allow_origins` by **exact string** and no
`allow_origin_regex` is configured, the entry `https://*.onrender.com` is
**inert** — it matches no real origin (finding **CFG-7**). The remaining nine
entries are explicit, so there is *no* credentialed wildcard origin; that is the
correct posture and should not be "simplified" later.

### 4.3 Frontend build-time variables (`frontend/src`, class C5)

`REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`
(anon key only — correct), `REACT_APP_GOOGLE_CLIENT_ID`, `REACT_APP_OAUTH_REDIRECT_URL`,
`REACT_APP_ENVIRONMENT`, and the build-identity trio
`REACT_APP_BUILD_BRANCH` / `REACT_APP_BUILD_COMMIT` / `REACT_APP_BUILD_TIME`.

### 4.4 Admin build-time variables (`admin/src`, class C5)

`REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`,
`REACT_APP_BUILD_BRANCH`, `REACT_APP_BUILD_COMMIT`, `REACT_APP_BUILD_TIME`.

> The admin control plane exposes **no** environment-specific switch beyond the
> API URL and build identity. Every admin capability is therefore governed by
> role/authorization in the API, not by deployment configuration. That is the
> correct security posture (AGENTS §31/§44) and is recorded so it is not
> "helpfully" replaced by a client-side flag.

### 4.5 Test-only variables (must never be production policy)

`TEST_API_URL`, `TEST_USER_EMAIL` / `TEST_USER_PASSWORD`,
`TEST_ORG_ADMIN_EMAIL` / `TEST_ORG_ADMIN_PASSWORD`,
`TEST_ADMIN_EMAIL` / `TEST_ADMIN_PASSWORD`.
Demo-lab generation contract: `tools/demo_lab/backend.env.example`
(`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`,
`SUPABASE_JWT_SECRET`, `TESSERACT_CMD`) — explicitly documented as **generated
outside the repository**, never committed.

### 4.6 Not CarbonTally configuration (observed passthrough only)

`PG*` (libpq), `ORT_*` / `ALLOW_RELEASED_ONNX_OPSET_ONLY` /
`TEMPORARILY_DISABLE_PROTOBUF_VERSION_CHECK` (ONNX Runtime),
`PYTEST_THEME*` / `PY_IGNORE_IMPORTMISMATCH` (pytest), `SPHINX_BUILD` (Sphinx),
`PYDANTIC_*` (pydantic), `NUMPY_*`, `ANDROID_*`, `DATABRICKS_RUNTIME_VERSION`,
`ASYNCPG_DEBUG_SERVER`, `HOME`/`SHELL`/`DISPLAY`/`WAYLAND_DISPLAY`/`PREFIX`/`PAGER`.
These appear in the grep because libraries read them; **none may be treated as a
CarbonTally behavioural setting.**

---

## 5. Who can change what (class C8) — authorization map

| Configuration | Endpoint | Guard (server-side, verified in source) | Additional layer |
|---|---|---|---|
| Retention policy (N3) | `GET/PUT /api/v3/settings/retention` | `Depends(require_admin())` | RLS on `system_settings` |
| Analytics & Integrations (GA4) | `GET /api/v3/settings/analytics` | **intentionally public** (browser must know before sign-in); response trimmed to `enabled` + `ga4_measurement_id` only | — |
| Analytics & Integrations (GA4) | `PUT /api/v3/settings/analytics` | `Depends(require_admin())` | RLS |
| Commercial configuration (12 endpoints incl. `PUT /config/{config_key}`, `POST /plans`, `PUT /plans/{plan_code}`, subscriptions) | `/api/v3/commercial/*` | `Depends(require_staff)` **plus** `_require_billing_admin(context)` → `require_internal_staff(context)` | RLS on billing tables |
| Review-queue SLA defaults | `/api/v3/operations` (queue/SLA surface) | staff authority (`require_staff` family) | RLS on `queue_settings` |
| Legacy platform settings | legacy `/api/admin/settings*` + `pages/admin/Settings.js` | legacy admin authorization | RLS |
| Ops settings UI | `ops/SettingsTab.jsx` | server-side guard is authoritative; UI is presentation only | — |

**Two rules this map exists to defend (AGENTS §7/§44):**

1. Commercial configuration is **internal-staff only** — a customer or consultant
   cannot read or change plans, credits, pricing or the commercial config, even
   though the tables live in the same database. The guard is
   `require_internal_staff`, not a UI condition.
2. The GA4 read is the **only** unauthenticated configuration read in the platform,
   and it is deliberately narrowed to two non-secret fields. It must never grow to
   return retention values, actor identifiers or tenant data (the docstring states
   this explicitly, and this catalogue records it as a durable constraint).

---

## 6. Configuration findings (evidence-based)

Severity uses the project's four-band convention. "Predicted" means verified by
schema-vs-SQL comparison rather than by executing the endpoint (read-only posture).

| ID | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| **CFG-1** | **HIGH** | `SettingsRepository.get_retention()/update_retention()` select and write `system_settings.operational_telemetry_retention_days`, but that column **exists in no durable local database** (flagship `information_schema` count = 0) because migration `20260924000000_p8x_x2_operational_telemetry_retention.sql` is **unapplied** (0 ledger rows for that version; newest ledger row `20260903010000`). `GET/PUT /api/v3/settings/retention` and the ops retention tab are therefore **predicted to fail with `UndefinedColumn`** against the durable flagship. | `backend/data/settings.py:26-29,64-93`; live column count; live ledger | VERIFIED (schema) / PREDICTED (runtime) |
| **CFG-2** | MEDIUM | Retention is stored **twice** in the same row — typed columns (audit 1 / data 365 / document 365 / backup 365) *and* `setting_value` JSONB with the same four numbers. The verified write path touches typed columns only, so the JSONB copy is an unmaintained second source of truth that will silently diverge. | live row dump; `data/settings.py` update path | VERIFIED |
| **CFG-3** | **HIGH** | Upload limits are **not configurable in practice**: `routes/upload.py` requests `settings_json`, `max_file_size_mb`, `allowed_file_types`, `enable_auto_repair`, `max_batch_files`, `max_total_batch_size_mb` — **none of the first six exist as columns** — and reads with `.maybe_single()` against a 2-row table, so the call errors into its fallback branch. Effective policy is the hard-coded 50 MB / 20 files / 200 MB / 365-day set; `max_upload_size_mb`, `max_batch_size_mb`, `max_file_upload_daily`, `max_documents_per_batch`, `max_pages_per_document` are read by **nothing**. | `backend/routes/upload.py:39-80`; live column list | VERIFIED (code+schema) |
| **CFG-4** | MEDIUM | **37 further typed settings columns are inert** (no read path in either tree): localisation (`default_language`, `default_timezone`, `date_format`, …), tax (`carbon_tax_*`, `default_tax_*`, `default_vat_rate`), password/session/2FA policy, webhook retry, API rate limits, legacy SLA and backup columns. They *appear* configurable in the schema and are not. | per-name grep across `backend/`, `frontend/src`, `admin/src` | VERIFIED |
| **CFG-5** | MEDIUM | `audit_log_retention_days = 1` against 365 for data, documents and backups. | live row | VERIFIED (POD-E) |
| **CFG-6** | LOW-MED | `FOUNDER_EMAIL` defaults to a **personal address compiled into the release tree** and is the default notification recipient when the variable is unset. | `backend/config.py:20` | VERIFIED |
| **CFG-7** | LOW | CORS is **hard-coded** (10 origins) and not environment-overridable; the entry `https://*.onrender.com` is **inert** because Starlette matches `allow_origins` exactly and no `allow_origin_regex` is set. No credentialed wildcard exists (correct), but the intended convenience does not work either. | `backend/config.py:23-36`; `backend/main.py:175-183` | VERIFIED |
| **CFG-8** | MEDIUM | Commercial configuration is **partially unset**: `storage.additional_rate_per_gb`, `standard_allowance.monthly_processing_units` and `.additional_rate`, `credit_policy.rollover.expiry_months` and `max_carryover_pct` are all `null`, while every billing transactional table holds **0 rows**. Commercial policy therefore has no approved basis for storage overage, allowance overage or credit expiry. | live `billing_commercial_config`; live row counts | VERIFIED (POD-K) |
| **CFG-9** | LOW-MED | The live plan catalogue mixes GBP (v1) and USD (v2) priced rows while `system_settings.default_currency = 'GBP'`. | live `billing_plans` | VERIFIED (POD-L) |
| **CFG-10** | MEDIUM | Every setting introduced by the 43 unapplied migrations is **unverifiable durably** (operational telemetry retention = CFG-1; plus P8X-X2 and P17 configuration). The retention migration itself records **"Production is PROHIBITED (G0-D open)"**, so those settings are QA-only by decision. | migration header; live ledger | VERIFIED (POD-A) |

---

## 7. Configuration decisions requiring the Product Owner

Continuing the register started in deliverable 1 (POD-A…POD-J):

| ID | Decision required | Why it is a PO decision, not an implementation choice | Current state |
|---|---|---|---|
| **POD-K** | Storage overage rate, standard-allowance size and overage rate, credit expiry and carry-over cap | These are **commercial terms**, not technical settings; the schema supports them and the values are absent | `null` live — CFG-8 |
| **POD-L** | Single currency per plan catalogue, or explicitly dual-currency plans | Pricing policy; the versioned plan model can express either | GBP + USD rows live — CFG-9 |
| **POD-M** | Which object is authoritative for upload limits (typed `system_settings` columns vs a key/value payload), and the approved limit values | The current hard-coded fallbacks (50 MB / 20 files / 200 MB) act as policy by accident | CFG-3 — no authoritative source today |
| **POD-N** | Retention values for audit, operational telemetry, data, documents and backups — including whether audit retention stays at 1 day and operational telemetry is initialised to the PO-approved 90 days | Retention is configurable by ratified decision (N3) and the current audit value is extreme | audit 1 / data 365 / document 365 / backup 365 — CFG-1, CFG-5 |
| **POD-O** | The platform notification sender/recipient identity for each environment | Prevents a personal address from functioning as platform policy | hard-coded default — CFG-6 |

Ratified decisions this catalogue **does** record (not open, and must not be
re-opened silently):

- **N3** — retention is configurable and enforced server-side; durations must never
  be invented by code.
- **PX-7 Option (a), 2026-09-14** — "Operational telemetry retention = configurable
  server-side, with an initial value of 90 days"; 90 must be expressed as a schema
  default, not a code literal, and `data_retention_days` must not be reused for it.
  (Source: `20260924000000_p8x_x2_operational_telemetry_retention.sql` header.)
- The same migration records **"Production is PROHIBITED (G0-D open)"** for the P8X
  workstream — an environment constraint this catalogue preserves rather than
  silently reversing.

---

## 8. Hand-back

| Item | Value |
|---|---|
| Document | `docs/architecture/CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` |
| Configuration surfaces catalogued | **8 classes** (C1–C8), **11 platform setting rows/keys**, **63 `system_settings` columns**, **7 commercial config keys**, **6 plan rows**, **5 queue/SLA fields**, **~45 environment variables**, **174 RLS policies** |
| Live values quoted | 2026-09-27, flagship `postgres` (PostgreSQL 17.6) |
| Settings rows live | `system_settings` 2 · `queue_settings` 1 · `billing_commercial_config` 7 · `billing_plans` 6 · billing transactional tables 0 |
| Findings raised | **CFG-1 … CFG-10** (2 HIGH: CFG-1, CFG-3) |
| PO decisions raised | **POD-K … POD-O** |
| Secrets reproduced | **None** |
| Writes performed | **None** — no DDL, DML, migration, seed, config change or deployment |
| Verification posture | Schema/code/live-value verification; endpoint execution deliberately not performed (read-only discovery) |
| Verdict for this deliverable | `CONFIGURATION_CATALOGUE_COMPLETE_WITH_OBSERVATIONS` |

**What is *not* claimed.** No configuration change was tested end-to-end. CFG-1 and
CFG-3 are verified at the schema/SQL level and *predicted* at runtime; confirming
them requires executing the affected endpoints, which this read-only pass did not
do. Until then they must be reported as "verified by inspection, not by execution".

<!--CTEOF-->






