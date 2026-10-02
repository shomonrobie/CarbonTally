# CT-FINAL-02 — Independent Verification & Closure Gate

**Independent verification report — 2026-09-29**

This report is the output of an **independent verification and closure gate** for
CT-FINAL-02. It is not an implementation report; it re-derives the evidence
behind each claim in
`docs/architecture/CT-FINAL-02-20260929-EMAIL-AND-UPLOAD-CONFIGURATION-REPORT.md`
and states, per area, only what the evidence actually supports.

Nothing was committed, pushed, deployed, migrated or mutated. All database work
used **disposable** containers only.

---

## 1. Repository identity

| Field | Value |
| --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD | `cabdca8380415e73a25cf23eb393d0b15c0af391` |
| Base for CT-FINAL-02 | same commit (`cabdca8…`, CT-FINAL-01 final report) |
| Commits made by this verification | **none** |
| Pushes | **none** |
| Deployment / migration applied | **none** |

The CT-FINAL-02 change set is **uncommitted working-tree changes on top of
`cabdca8`**. This was independently confirmed: a pristine `git worktree` created
at `HEAD` (used for the A/B pre-existing-failure proof, §17) contained **none** of
the CT-FINAL-02 edits.

---

## 2. Working-tree state

State recorded **before** and **after** this verification — **identical**.

| Measure | Before | After |
| --- | --- | --- |
| Branch | `p8-release-reconciled` | `p8-release-reconciled` |
| HEAD | `cabdca8…` | `cabdca8…` |
| Tracked modified files | 24 | 24 |
| Untracked files (`--exclude-standard`) | 869 | 869 |
| Staged changes | none | none |
| `git worktree list` | primary only | primary only |

Tracked modified files present (unrelated to CT-FINAL-02 are preserved and were
**not** touched): `.gitignore`, `admin/src/components/admin/DefraFactorModal.js`,
`admin/src/components/admin/ImportDefraModal.js`,
`admin/src/pages/admin/DefraFactors.js`, `backend/api/v3_discovery.py`,
`backend/api/v3_organizations.py`, `backend/api/v3_settings.py`,
`backend/data/settings.py`, `backend/routes/notifications.py`,
`backend/services/email_service.py`, `backend/services/operational_alerting.py`,
`backend/services/v3_email.py`, `backend/tests/unit/api/fakes.py`,
`backend/tests/unit/test_ct_implement_01_remediation.py`, `backend/utils/email.py`,
three `docs/architecture/CT-*-REPORT.md` files, `frontend/App_.js`,
`frontend/src/App.js`, `frontend/src/components/ManualEntryStandalone.jsx`,
`frontend/src/v3/__tests__/review-api.test.js`, `frontend/src/v3/api.js`,
`frontend/src/v3/ops/SettingsTab.jsx`.

Untracked additions that belong to CT-FINAL-02 and remain uncommitted:
`backend/services/email_provider.py`,
`backend/tests/unit/api/test_ct_final_02_email_provider.py`,
`frontend/src/v3/__tests__/settings-tab-email-provider.test.jsx`, plus numerous
unrelated pre-existing untracked artefacts (`8`, `=`, `.costrict/`,
`.p18_audit_tmp/`, many `docs/` bundles). **None** of these were staged, reverted,
cleaned, stashed or otherwise disturbed.

---

## 3. Scope verified

Independent verification covered:

* the email **provider** abstraction and its persistence, API, runtime selection,
  validation, authorization and security properties;
* a controlled **end-to-end SMTP delivery** through the canonical CarbonTally
  mailer (local disposable SMTP server), because no A2Hosting credentials exist;
* the **sender identity** configuration path;
* the **upload policy** (three configurable values, platform ceilings, runtime
  enforcement on every ingress path);
* the **Supabase storage/RLS** boundary (read-only inspection + a minimal
  unauthenticated probe);
* **D-7** (inactive organisation) current implementation state;
* the **local** Supabase stack and the **live/shared** Supabase availability;
* the **factor library** (canonical count, retired table, structure, uniqueness);
* the **CT-FINAL-01 regression** set and the full backend/frontend test suites.

The gate was **not** closed merely because the implementation report says
"complete", unit tests pass, or the UI exists.

---

## 4. Email provider verification

**Source inspected:** `backend/services/email_provider.py`,
`backend/services/v3_email.py`, `backend/data/settings.py`,
`backend/api/v3_settings.py`.

| Claim | Evidence | Status |
| --- | --- | --- |
| Two providers implemented (`resend`, `smtp`) | `SUPPORTED_PROVIDERS = ("resend","smtp")`; `DEFAULT_PROVIDER = "resend"`; SMTP adapter uses stdlib `smtplib` + `EmailMessage` | **IMPLEMENTED** |
| Provider is configuration, not hard-coded | `send_transactional_email(..., settings_repo=…)` resolves the persisted provider via `resolve_configured_provider`; `send_platform_email` resolves it through `platform_settings_repo()` for non-request callers | **WIRED** |
| Configuration persisted in existing `system_settings` row `email_provider` | `update_email_provider()` issues `INSERT … ON CONFLICT (setting_key) DO UPDATE … RETURNING`; round-tripped on real Postgres (§5) | **PERSISTED** |
| Runtime selection actually changes the email path | Proven end-to-end with the SMTP provider (§5): rows persisted `provider=smtp`, delivery used the SMTP adapter | **RUNTIME ENFORCED** |
| Validation | `normalise_provider_config` refuses unknown provider, scheme/port in host, port outside 1–65535, non-boolean TLS, credential var outside `ALLOWED_CREDENTIAL_ENVS`, and secret-looking fields | **IMPLEMENTED / TESTED** |
| Admin-only | `GET`, `POST /validate`, `PUT` all `Depends(require_admin())` | **IMPLEMENTED** |
| Denied for non-admin | CT-FINAL-02 suite asserts 403 for org owner / consultant / processing-entity staff, 401 anonymous | **TESTED** |
| Fail closed, no cross-provider fallback | `deliver_email_sync` returns `(False, reason)` when the selected provider is unconfigured | **TESTED** |
| Only one module imports a provider SDK | Repo-wide assertion test; independently, `grep 'import resend'` matched only `email_provider.py` | **VERIFIED** |

Independently run CT-FINAL-02 suite: **71 passed**.

**Residual note (not a CT-FINAL-02 regression):** `services/email_service.py`
contains unreachable dead code — a second `return True` after the real `return` in
`send_beta_confirmation_email` (`backend/services/email_service.py:202`). It has no
runtime effect (the module was previously unimportable and has no callers) but is a
cleanliness defect worth recording.

---

## 5. Real SMTP delivery verification

### 5.1 A2Hosting external delivery — BLOCKED

The A2Hosting mailboxes `hello@carbontally.co.uk` and
`notifications@carbontally.co.uk` **do** now exist, but no usable **SMTP
credential/configuration for CarbonTally** is available in this environment:

* `RESEND_API_KEY`, `CT_SMTP_PASSWORD`, `SMTP_PASSWORD` are **unset** in the
  process environment;
* `backend/.env` lists a `RESEND_API_KEY` **name whose value is empty** (length 0)
  and contains **no** SMTP variable at all;
* no A2Hosting host/user/password is configured anywhere.

Per the governance rule, no credential was requested in chat, none was printed,
and none was placed in this report.

> **`BLOCKED — required SMTP credential/configuration unavailable`** (external
> A2Hosting end-to-end delivery). No successful external delivery is claimed.

### 5.2 Controlled end-to-end delivery through the canonical CarbonTally service — PASS

To prove the **implemented SMTP provider path** independently of external
credentials, a controlled test was run using a **disposable local SMTP server**
(mailpit, `mailpit:v1.30.2`) and the **disposable** Postgres clone
`ct_final01_pg` (used read/write inside a scope that was fully cleaned up).

Path exercised — **the actual CarbonTally implementation**, not a standalone
script:

```
SettingsRepository.update_email_provider(provider=smtp, host=127.0.0.1, port=11025,
                                         use_tls=False, credential_env=CT_SMTP_PASSWORD)
SettingsRepository.update_notification_sender(email_sender="notifications@carbontally.co.uk")
  → persisted in system_settings (real Postgres)
services.v3_email.send_transactional_email(to_email="hello@carbontally.co.uk", settings_repo=repo)
  → resolve provider + sender from the persisted rows
  → services.email_provider.deliver_email
  → smtp adapter (smtplib) → local SMTP server
```

Observed results:

```
PERSISTED_PROVIDER  {"provider":"smtp","smtp_host":"127.0.0.1","smtp_port":11025,
                     "smtp_username":null,"smtp_use_tls":false,"credential_env":"CT_SMTP_PASSWORD"}
READ_BACK_PROVIDER  {"provider":"smtp","smtp_host":"127.0.0.1","smtp_port":11025,
                     "smtp_use_tls":false,"credential_env":"CT_SMTP_PASSWORD"}
PERSISTED_SENDER    {"email_sender":"notifications@carbontally.co.uk"}
DELIVERY_RESULT     {"delivered": true, "reason": "sent"}
mailpit receipt     FROM=notifications@carbontally.co.uk  TO=hello@carbontally.co.uk
                    SUBJECT="CT-FINAL-02 independent SMTP verification"
REMAINING_SETTINGS  ["platform_retention"]        # no residue
```

Distinguishing the three levels honestly:

| Level | Result |
| --- | --- |
| SMTP submission accepted by the provider | **Confirmed** (mailpit `SMTPAccepted` = 1) |
| Mailbox delivery confirmed | **Confirmed** (message present in the mailpit mailbox store) |
| Application-level delivery confirmed | **Confirmed** (`delivered=true, reason="sent"`) |
| External A2Hosting delivery | **BLOCKED** (§5.1) |

This proves the CT-FINAL-02 chain
`configuration → persistence → canonical mailer → SMTP adapter → configured
sender → recipient` end-to-end at the application level. It does **not** claim
A2Hosting delivery.

---

## 6. Sender identity verification

`notifications@carbontally.co.uk` was configured through
`SettingsRepository.update_notification_sender` and, without any code change, the
canonical mailer applied it as the SMTP **From** address (`FROM=notifications@
carbontally.co.uk` in §5.2). Sender validation
(`services/email_sender.normalise_email_sender`) restricts the platform sender to
`carbontally.co.uk` and rejects header-injection/multi-address values. Sender
configuration is **admin-only** and **persisted** in the
`platform_notifications` row.

**Status: PASS** (configurable + applied at runtime + persisted).

---

## 7. Email secret/security verification

| Property | Evidence | Status |
| --- | --- | --- |
| Secrets never returned by a GET | `describe_provider_config` reports only `credential_configured` (a boolean); CT-FINAL-02 test `test_no_credential_value_ever_appears_in_a_response` / `test_describe_never_returns_a_credential_value` | **PASS** |
| Secrets not exposed in frontend state/DOM | `SettingsTab.jsx` has no credential input; renders only which variable is set; Jest test asserts no credential value in the DOM | **PASS** |
| Secrets not logged | `_scrub()` replaces the password with `***` before a failure reason is returned; test `test_delivery_never_leaks_the_credential_in_its_failure_reason` | **PASS** |
| Non-admin cannot modify | `require_admin()` on all three endpoints; DENY matrix tests (owner/consultant/PE/anonymous) | **PASS** |
| Credentials not stored insecurely | Row stores only the provider + the allow-listed env-var *name*; request model `extra="forbid"`; `_email_provider_from_row` drops a non-allow-listed variable even if a row is hand-edited | **PASS** |
| Invalid/incomplete SMTP fails safely | `deliver_email_sync` returns `(False, reason)`; no unlimited/fallback behaviour | **PASS** |
| Credential allow-list | `ALLOWED_CREDENTIAL_ENVS = {RESEND_API_KEY, CT_SMTP_PASSWORD, SMTP_PASSWORD}` re-checked in `credential_value()`; arbitrary names (e.g. `AWS_SECRET_ACCESS_KEY`) return `None` | **PASS** |
| `_UNSET` semantics / provider switching | `data/settings.py` distinguishes omitted (`_UNSET` → keep) from explicit `None` (→ clear); `_merge_provider_update` re-points the credential variable to the new provider's default when switching, so a stale variable is not read — covered by `test_switching_provider_re_points_the_credential_variable` and `test_an_empty_string_clears_a_stored_transport_value` | **PASS** |

**Status: PASS** (application level). External credential handling could not be
exercised because no real credential exists (§5.1).

---

## 8. Upload policy verification

Source: `backend/utils/upload_limits.py`, `backend/api/v3_settings.py`,
`backend/data/settings.py`.

Defaults (effective when nothing is configured) and ratified ceilings,
independently reproduced:

| Value | Default | Ratified ceiling |
| --- | --- | --- |
| Max individual file size | **6 MB** | **10 MB** |
| Max files per batch | **50** | **50** |
| Max aggregate batch size | **500 MB** | **500 MB** |

Configurability: `PUT /api/v3/settings/upload-policy` (admin-only) validates via
`validate_upload_policy` then persists to `system_settings` (`upload_policy` row).
`GET` returns effective + configured + defaults + caps.

`validate_upload_policy` independently probed: **refuses** zero, negative,
non-numeric, `bool`, float, and any value above the ratified cap; accepts positive
integers within the cap.

**Current configured values:** none — `ct_final01_pg.system_settings` contains only
`platform_retention`, so the **documented defaults (6 / 50 / 500 MB) are in force**.
The defaults were read from the implementation, not assumed.

**Status: PASS** for all three configurable values; **TESTED** (CT-FINAL-01 suite,
45 passed).

---

## 9. Upload runtime enforcement

Enforcement is server-side. Independently obtained call-site map:

```
backend/api/v3_documents.py:236,293            resolve_policy + enforce_single_file   (current documents API)
backend/routes/upload.py:109,147,181,252,394,676  resolve_policy / enforce_single_file (legacy API, 5 ingress paths + test-upload)
backend/routes/organizations/files.py:564,812,851 resolve_policy + enforce_batch + enforce_single_file
backend/routes/reports.py:1318                 resolve_policy + enforce_single_file
backend/api/v3_consultants.py:1300             resolve_policy
```

Directly probed enforcement behaviour (effective default 6 MB / 50 files / 500 MB):

| Probe | Result |
| --- | --- |
| single file exactly 6 MB | allowed |
| single file 6 MB + 1 | `UPLOAD_FILE_TOO_LARGE` (HTTP 413) |
| unknown size (`None`) | `UPLOAD_SIZE_UNKNOWN` (refused, never bypasses) |
| batch of 51 files | `UPLOAD_TOO_MANY_FILES` (HTTP 400) |
| configured limit lowered to 1 MB, file 2 MB | `UPLOAD_FILE_TOO_LARGE` (configured value enforced at runtime) |

Bypass search: there are **no** direct-to-Supabase-storage uploads from the
frontend or admin apps (`grep` found none). All backend `storage…upload()` calls
are either on the guarded ingress paths above (checked before any write) or are
server-generated artefacts (`report_artefact_storage`, `disclosure_finalisation`)
that are not user ingress. `validate_file_upload` uses the resolved
`configured_limit_mb` (not a route-local constant).

**Status: PASS** for enforcement coverage and behaviour. Caveat: enforcement was
verified by code inspection + unit suite + direct function probes; not every
route was driven through live HTTP in this run.

---

## 10. Supabase Storage / RLS verification

Read-only inspection of the local Supabase stack and the disposable clone:

* `storage.objects` carries exactly the four D32 policies for the `authenticated`
  role: `d32_documents_select_org_member`, `…_insert_…`, `…_update_…`,
  `…_delete_org_member` (present in both the local stack and `ct_final01_pg`).
* The `documents` bucket is **private** (`public=false`).
* On the disposable `ct_final01_pg` the bucket per-file ceiling is pinned to
  **`file_size_limit = 10485760` (10 MiB)** — matching the ratified storage
  ceiling migration `20261024000000_ct_final_01_documents_bucket_size_limit.sql`.
* Minimal unauthenticated probe: `GET /storage/v1/object/list/documents` →
  **HTTP 400** (denied), both with and without the anon API key.

**Application policy (6/50/500 MB) vs storage platform ceiling (10 MB) are kept
distinct** and are not conflated: the storage ceiling is the absolute per-object
limit at the storage layer; the application policy is the admin-configurable
server-side limit enforced before any object is written.

| Storage property | Status |
| --- | --- |
| Own authorized object access | **NOT VERIFIED** (no provisioned non-production user JWT) |
| Unauthorized user object denied | **NOT VERIFIED** (same blocker) |
| Unauthenticated private object denied | **PASS** (HTTP 400) |
| Organisation isolation / inactive-org behaviour | **NOT VERIFIED** (same blocker; see §11) |
| Direct upload cannot bypass authorization | **PARTIAL** — no direct frontend uploads exist; storage-layer ceiling pinned |

**Exact blocker:** verifying the authenticated user-isolation matrix requires real
user JWTs bound to provisioned `auth.users` + `organization_members` rows in a
non-production stack. Provisioning those users/memberships would mutate the local
stack and is outside this verification's authorization; authentication was **not**
weakened to complete the test.

---

## 11. D-7 verification (inactive organisation)

The selected product decision is **B — an inactive organisation denies all
organisation-scoped access unless re-enabled by a CarbonTally Admin.**

Independent determination of the **current** state:

* `public.is_org_active(p_org uuid)` is **defined** in migration
  `20260803000000_rc2_rls.sql:60` (“the org exists and is not archived/suspended”),
  **but it is referenced by no RLS policy.** `grep` across all 93 migrations finds
  it only in its definition and two comment/verification lists, and a
  `pg_policies` query returns **zero** policies whose expression mentions
  `is_org_active`.
* `public.is_org_member(p_org)` **does** include `coalesce(o.is_active,true)=true`,
  so RLS (JWT/`authenticated` paths) will deny membership of an inactive org — but
  only where RLS is in force.
* The back end authorises through `backend/auth.py`: `get_current_user`,
  `get_active_org_role`, `_org_admin_authority` and `enforce_org_path_scope`
  check the **membership** row’s `is_active`, but **never** `organizations.is_active`.
* The backend repositories read/write with the **service-role** pool
  (`infra/supabase.py`), which **bypasses RLS**.
* No backend code calls `is_org_active` (`grep` over `backend/**.py` → none).

Consequently an organisation owner/member of an **inactive** organisation is **not
denied** at the application layer (the path the API actually uses), which is
consistent with the CT-FINAL-01 live probe recorded in the implementation report
(“`ownerC → inactive orgC` returned `200`”).

| Sub-check | Status |
| --- | --- |
| Active organisation normal access | **PASS** (no regression observed) |
| Inactive organisation denies all org-scoped access | **NOT IMPLEMENTED / FAIL** |
| CarbonTally Admin can re-enable | not exercised (no UI/session); the `is_active` column exists and is writable by the app |
| After re-enable, access resumes | n/a (base state not implemented) |

**Status: `DEFERRED / PO DECISION` — the policy is not implemented.** This is a
genuine remaining implementation gap. No production code was changed to
“fix” it, per the closure-gate rule and the requirement not to reinterpret the
decision.

---

## 12. Local Supabase verification

The local Supabase stack (`project_id = carbon_ledger`) is running and was
inspected **read-only**:

| Check | Result |
| --- | --- |
| Migrations present in repo | **93** |
| `emission_factors` count | **7,049** |
| RLS enabled (public schema tables) | **116** tables |
| `documents` bucket | present, `public=false` |
| `storage.objects` policies | 4 (`d32_documents_*`, `authenticated`) |
| Retired `defra_conversion_factors` | **absent** |
| `storage.buckets.file_size_limit` (local stack) | unset (the stack predates the CT-FINAL-01 bucket migration); the **disposable clone** `ct_final01_pg` has it applied at 10 MiB |

**Not performed:** a from-scratch clean migration rebuild. It would require
tearing down / rebuilding a running stack and is out of scope for a non-mutating
verification; historical migrations were **not** edited to force a result.

**Status: PASS (inspection) · PARTIAL** (no clean rebuild performed).

---

## 13. Live / shared Supabase verification

* No Supabase credentials are present in the environment
  (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`,
  `SUPABASE_DB_URL` all **unset**).
* `backend/.env` points **only** at local endpoints:
  `SUPABASE_URL → http://127.0.0.1:19999`,
  `DATABASE_URL → postgresql://…@127.0.0.1:54426/postgres`.
* No `supabase.co` host is referenced anywhere in `backend/.env*`.
* The shared/live database was **not** contacted (so the “read-only at most” rule
  is honoured vacuously).

> **`UNVERIFIED — live/shared Supabase credentials or connection unavailable`.**
> The live factor count is **not** inferred from the local database.

**Status: NOT VERIFIED.**

---

## 14. Factor-library verification

Verified on the **local** Supabase stack (read-only):

| Check | Result |
| --- | --- |
| Total `emission_factors` | **7,049** |
| By source | **7,029 DEFRA-DESNZ** + **20 SEAI** = 7,049 |
| By factor set | DEFRA-2025 (7029), SEAI-2025 (20) |
| Distinct canonical key `(factor_source, activity_type, unit, reporting_year, country)` | **7,049** — i.e. **no duplicates** |
| NULLs in `activity_type` / `scope` / `unit` / `reporting_year` | **0 / 0 / 0 / 0** |
| Scope distribution | Scope 3 = 4090, Scope 1 = 2549, Scope 2 = 354, Outside of Scopes = 56 |
| Retired `defra_conversion_factors` | **absent** (not recreated, not used) |

Canonical structure columns: `id, reporting_year, activity_type, co2e_multiplier,
created_at, updated_at, unit, scope, factor_source, factor_set, country,
region_deprecated, import_batch_id`.

**Status: PASS** (local, 7,049 confirmed). *Live/shared 7,049:* **NOT VERIFIED**
(§13).

---

## 15. CT-FINAL-01 regression

| Area | Evidence | Status |
| --- | --- | --- |
| D-0 … D-6 (CT-FINAL-01 closures) | CT-FINAL-01 test files (`test_ct_final_01_d5_d6_runtime_defects.py`, `…_extraction_approval_atomicity.py`, `…_notification_sender.py`, `…_upload_limits.py`) pass | **PASS** |
| F-04 / PD-3 / PD-5 | covered by the passing CT-VERIFY/REMEDIATE unit suites | **PASS** |
| Notification configuration | `test_ct_final_01_notification_sender.py` passes; admin-only; persistent | **PASS** |
| Retention configuration | retention endpoints/tests unchanged and passing | **PASS** |
| Cross-tenant isolation | not re-derived live in this run (no JWT session); no change introduced by CT-FINAL-02 to that surface | **NOT RE-VERIFIED** (unchanged) |
| Upload-limits regression | 45/45 pass | **PASS** |

Combined CT-FINAL-01/02/verify/remediate run: **142 passed**. The seven
pre-existing unit-test failures were **not** "fixed" and were not caused by
CT-FINAL-02 (§17).

**Status: PASS** (no CT-FINAL-02 regression); cross-tenant isolation re-derivation
**NOT VERIFIED** this run.

---

## 16. Frontend / browser verification

* **Jest component tests** (real component, mocked API client): the three suites
  `settings-tab-email-provider.test.jsx`, `settings-tab-analytics.test.jsx`,
  `review-api.test.js` → **36 passed / 3 suites**. They assert the panels render
  the configured values and ratified caps, save through the admin endpoint,
  surface readiness issues, post Validate without saving, and display **no**
  credential value.
* Static review confirms two panels in `frontend/src/v3/ops/SettingsTab.jsx`:
  **Upload policy** (three values + caps + defaults) and **Email delivery**
  (provider selection, SMTP host/port/username/STARTTLS, credential-variable
  select, Validate/Save, platform From). Seven client functions in
  `frontend/src/v3/api.js` target the admin endpoints. No credential input exists.

| Sub-check | Status |
| --- | --- |
| Admin Settings loads | **NOT VERIFIED** (no browser session) |
| Email Delivery / provider selection / sender / validation / save | **NOT VERIFIED in browser** (Jest only) |
| Upload Policy panel / three values / validation / save / persistence-after-reload | **NOT VERIFIED in browser** (Jest only) |
| Authorization behaviour in browser | **NOT VERIFIED** |
| No credential values displayed | **PASS** (Jest DOM assertion + static review) |

> **`NOT VERIFIED — BROWSER ENVIRONMENT UNAVAILABLE`** for live browser QA.
> Playwright browser binaries **are** installed (`chromium`, `firefox`, `webkit`),
> but no authenticated full-stack session (running backend + frontend + Supabase
> with an admin login) is provisioned, and no admin test credentials exist. The
> frontend is therefore **not** called independently verified on the basis of unit
> tests alone.

---

## 17. Test results

Independently executed:

| Suite | Command | Result |
| --- | --- | --- |
| CT-FINAL-02 backend | `python3 -m pytest tests/unit/api/test_ct_final_02_email_provider.py` | **71 passed** |
| CT-FINAL-01 upload limits | `python3 -m pytest tests/unit/api/test_ct_final_01_upload_limits.py` | **45 passed** |
| CT-FINAL-01/02 + CT-VERIFY/REMEDIATE | combined run | **142 passed** |
| Frontend (new + existing) | `react-scripts test` (3 suites) | **36 passed / 3 suites** |
| Full backend unit sweep | `python3 -m pytest tests/unit` | **7 failed, 4398 passed, 8 skipped** (4413 collected) |

The full-sweep failures:

```
tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy
tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp
tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice
tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved
tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage
```

**A/B proof they are pre-existing:** a pristine `git worktree` at `HEAD`
(`cabdca8`, none of the CT-FINAL-02 edits) was created in `/tmp`, the identical
seven tests were run there, and the **same seven failed** (`7 failed, 4 passed`).
The worktree was removed afterwards. Classification:

| Failure | Classification |
| --- | --- |
| 4 migration/“latest migration” drift tests | **PRE-EXISTING FAILURE** (stale expectations vs. the current migration set) |
| 3 `extraction_suggestions` shape/date tests | **PRE-EXISTING FAILURE** (engine output drift) |
| any CT-FINAL-02 / email / settings / upload failure | **none** |

No test was modified to make anything pass.

---

## 18. Environment limitations

1. **No email credential.** No `RESEND_API_KEY` value and no SMTP credential are
   configured; `backend/.env`'s `RESEND_API_KEY` is empty. External delivery is
   **BLOCKED**; a local mailpit server was used for a controlled end-to-end test.
2. **No live/shared Supabase credential** — the hosted database could not be
   reached; its factor count is **UNVERIFIED**.
3. **No authenticated browser session / admin credentials** — live browser QA of
   the Admin panels is **NOT VERIFIED**.
4. **No clean migration rebuild** was performed on the local Supabase stack (it
   would require mutating/rebuilding a running stack).
5. **Authenticated storage/JWT isolation matrix** could not be run without
   provisioning non-production users (which would mutate the local stack).
6. `python3` in this environment is 3.14; the SMTP adapter uses only the standard
   library (`smtplib`, `email.message`) and worked under it.

---

## 19. Remaining blockers

| # | Blocker | Impact | Required to proceed |
| --- | --- | --- | --- |
| B1 | A2Hosting SMTP credential/configuration unavailable | External email delivery cannot be verified | Provide SMTP host/user/password securely in the deployment environment (never in chat) |
| B2 | Live/shared Supabase credentials unavailable | Live 7,049 factor count and live schema cannot be confirmed | Provide read-only live connection (read-only use) |
| B3 | No admin test credentials / authenticated session | Live browser QA of the Admin panels not possible | Provision a non-production admin login |
| B4 | D-7 not implemented | Inactive-organisation org-scoped access is not denied at the application layer | A PO decision + a scoped implementation (application-layer `organizations.is_active` enforcement) |
| B5 | Storage/JWT isolation matrix | Not re-derived for this change | Provision non-production users/orgs in a disposable stack |

None of these were worked around by weakening security, fabricating evidence, or
mutating shared data.

---

## 20. Closure verdict

CT-FINAL-02's **implementation claims that can be verified in this environment are
sound**: the email provider and sender are administrator-configurable and are
applied end-to-end through the canonical mailer (proven with a real SMTP transport
and mailbox receipt), the upload policy is configurable with enforced ratified
ceilings, secrets are confined to the environment, delivery fails closed, and the
CT-FINAL-02/CT-FINAL-01 suites pass with no regression.

However, the **closure gate is NOT satisfied**, because material parts of the
required evidence remain unattainable in this environment and one genuine
implementation gap remains:

* external **A2Hosting delivery is BLOCKED** (no credential);
* the **live/shared Supabase** factor library is **UNVERIFIED**;
* **live browser QA** of the Admin panels is **NOT VERIFIED**;
* **D-7** (inactive organisation denial) is **not implemented** and remains a PO
  decision;
* the authenticated **storage/JWT isolation** matrix was **NOT VERIFIED**.

**Gate state: OPEN.** CT-FINAL-02 may not be treated as independently verified /
closed until at least B1–B4 are resolved. No commit, push, deployment or
production change was performed.

---

## Final verdict table

| Area | Status | Evidence |
| --- | --- | --- |
| Email provider configurable | PASS | `email_provider.py` (resend+smtp); GET/validate/PUT admin-only; persisted `email_provider` row; 71 tests |
| Sender identity configurable | PASS | `email_sender.py`; `platform_notifications` row; From applied in §5.2 |
| Email secrets protected | PASS | allow-list + `extra="forbid"` + boolean presence; no secret in response/DOM/log; DENY matrix |
| A2Hosting SMTP configuration | BLOCKED | No SMTP credential/host/user/password available; `.env` SMTP vars absent |
| Real CarbonTally email send | PASS | Canonical `send_transactional_email` → SMTP → mailpit receipt; `delivered=true` |
| `notifications@carbontally.co.uk` sender | PASS | From header = `notifications@carbontally.co.uk` in mailpit |
| `hello@carbontally.co.uk` receipt | PASS (local mailpit) · BLOCKED (A2Hosting) | mailpit mailbox received the message; external mailbox not reachable |
| Upload file-size configurability | PASS | Default 6 MB, cap 10 MB; `PUT /upload-policy`; validated |
| Upload file-count configurability | PASS | Default 50, cap 50 |
| Upload aggregate-size configurability | PASS | Default 500 MB, cap 500 MB |
| Upload runtime enforcement | PASS | `resolve_policy`/`enforce_*` on all ingress paths; boundary probes; batch/count/unknown-size all enforced |
| Upload platform ceilings | PASS | `validate_upload_policy` refuses >caps, zero, negative, malformed, wrong types |
| Storage RLS | PARTIAL | 4 `d32_documents_*` policies present; unauth access denied (HTTP 400); JWT user matrix NOT VERIFIED |
| User isolation | NOT VERIFIED | No provisioned non-production user JWTs (blocker B5) |
| Organisation isolation | NOT VERIFIED | Same blocker; inactive-org behaviour not enforced at app layer (§11) |
| D-7 inactive organisation | DEFERRED / PO DECISION | `is_org_active` defined but unused; backend checks membership `is_active` only; service-role bypasses RLS |
| Local Supabase | PASS (inspection) · PARTIAL | 7049 factors; 116 RLS tables; documents bucket private; no clean rebuild performed |
| Live/shared Supabase | NOT VERIFIED | No credentials; `.env`/env point to localhost only |
| 7,049-factor library | PASS (local) · NOT VERIFIED (live) | 7029 DEFRA-DESNZ + 20 SEAI; key unique; no NULLs; retired table absent |
| CT-FINAL-01 regression | PASS | 45/45 + 142 combined; no CT-FINAL-02 regression |
| Frontend/Admin UI | PASS (Jest) · NOT VERIFIED (browser) | 36 tests / 3 suites; panels + client funcs present; no credential display |
| Browser QA | NOT VERIFIED | No authenticated full-stack session / admin credentials |
| Production deployment | NOT AUTHORIZED | No deployment permitted |
