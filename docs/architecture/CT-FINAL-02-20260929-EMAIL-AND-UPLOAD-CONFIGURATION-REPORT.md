# CT-FINAL-02 — Admin-configurable email delivery provider/sender and upload policy, end-to-end

**Implementation & verification report — 2026-09-29**

| Field | Value |
| --- | --- |
| Task | CT-FINAL-02 — make the email delivery provider/sender **and** the upload policy admin-configurable end-to-end, then run release verification |
| Repository | `/home/shomonrobie/ct_93d5cdd` (working tree) |
| Branch | `p8-release-reconciled` |
| Base commit | `cabdca8380415e73a25cf23eb393d0b15c0af391` (CT-FINAL-01 final report) |
| New commits | **none** — nothing committed, nothing pushed |
| Deployment | **none** — no deploy, no migration applied to any shared/production environment |
| Schema change | **none required** — verified against a real Postgres (`system_settings`) |
| External email delivery | **NOT YET VERIFIED** (no provider credential, no live send attempted) |

---

## 1. Executive summary

CT-FINAL-01 made the **notification sender** and the **upload limits** admin
configuration in the backend. CT-FINAL-02 closes the two remaining halves of the
same requirement:

1. **The delivery provider itself is now configuration, not hard-coded.** A new
   canonical abstraction (`backend/services/email_provider.py`) implements two
   providers **end-to-end** — `resend` (the existing platform provider) and
   `smtp` (any SMTP submission service, standard library only) — and every
   transactional email path in the application now goes through it.
   The provider, its non-secret SMTP transport settings and the referenced
   credential variable are persisted in the existing `system_settings` row
   `email_provider` and are managed from the Admin Dashboard
   (`ops → Settings → Email delivery`) through three new admin-only endpoints.

2. **No credential can reach the database, the API response, or the logs.**
   Credentials are read from the allow-listed environment variables
   (`RESEND_API_KEY`, `CT_SMTP_PASSWORD`, `SMTP_PASSWORD`) at delivery time. The
   stored row contains only the provider selection and the *name* of the
   variable; the API refuses an unknown (secret-looking) field outright with
   `422`; the description endpoints report only *whether* the variable is
   present (a boolean); and a failing SMTP login is scrubbed of the password
   before the reason is returned.

3. **Delivery fails closed and never lies.** An unconfigured provider returns
   `(delivered=False, reason)`; delivery is **never** silently re-routed to
   another provider (a deployment configured for SMTP with a missing SMTP
   credential does *not* quietly send via Resend); and the legacy helpers
   (`utils.email`, `routes.notifications`, `services.email_service`) no longer
   report a fabricated success — they return the honest result.

4. **The last direct provider coupling in the backend was removed.** Only
   `services/email_provider.py` imports the Resend SDK (lazily, inside the
   adapter function). This is asserted by a repository-wide regression test.

5. **Upload policy is now editable in the Admin Dashboard** (CT-FINAL-01 built
   the backend policy + enforcement; CT-FINAL-02 adds the control-plane UI and
   re-verifies the enforcement wiring and the CT-FINAL-01 suite).

Verification performed here: **116 new/regression tests pass** (71 CT-FINAL-02
backend, 45 CT-FINAL-01 backend, 36 frontend), the upsert statement and schema
were exercised against a **real Postgres** (`ct_final01_pg`, disposable, inside a
rolled-back transaction — no residue), and the full `tests/unit` sweep shows
**7 failures that were A/B-proven pre-existing** by running the identical tests
against a pristine `HEAD` worktree.

Not verified here, and not claimed: a real delivery through Resend or a real
SMTP server (no credential, and sending live email from a verification run is
not appropriate), and end-to-end browser operation of the new panels.

---

## 2. Starting baseline (measured, not assumed)

Before changing anything, the current tree was inspected:

| Check | Result |
| --- | --- |
| `backend/services/email_provider.py` | existed in the working tree but was **syntactically invalid** (a stray indented fragment at EOF left by an interrupted edit) |
| `backend/services/email_service.py` | **pre-existing `IndentationError` at HEAD**, and unreferenced by any Python/JS/TS/Markdown file in the repo (proven by repo-wide grep) |
| Provider call sites | `routes/notifications.py` still used the Resend SDK directly with a hard-coded sender; `utils/email.py` mutated `resend.api_key`; `services/email_service.py` did both |
| `system_settings` columns | `setting_key varchar` (UNIQUE), `setting_value jsonb`, `setting_type`, `description`, `updated_by uuid`, `updated_at`, `created_at` — verified by read-only query on `ct_final01_pg` |
| Admin UI | **no** UI called `/api/v3/settings/upload-policy` or `/notification-sender` (grep over `admin/src` and `frontend/src` returned nothing) |

Those two broken modules were repaired as part of this task (see §4.3) because
"every email path uses the configured provider" cannot be asserted while a
module that hard-codes the provider is in the tree, and because a module that
cannot be imported is a real defect.


---

## 3. What was implemented

### 3.1 Canonical provider abstraction — `backend/services/email_provider.py` (new)

One module owns provider selection, credential resolution and delivery:

* `SUPPORTED_PROVIDERS = ("resend", "smtp")`, `DEFAULT_PROVIDER = "resend"`
  (unchanged behaviour for every existing deployment when nothing is configured).
* `ALLOWED_CREDENTIAL_ENVS = {"RESEND_API_KEY", "CT_SMTP_PASSWORD", "SMTP_PASSWORD"}`
  — a *security control*, not a convenience: an arbitrary variable name would let
  an administrator exfiltrate an unrelated secret to a host of their choosing.
* `normalise_provider_config()` validates and canonicalises the configuration and
  **refuses**: an unknown provider, a malformed hostname/port, a credential
  variable outside the allow-list, or a credential submitted as an ordinary
  setting (`api_key`, `password`, `secret`, `credential`, …).
* `credential_value(env_name)` re-checks the allow-list before reading the
  environment, so no caller can widen the readable set.
* `describe_provider_config()` returns the selected provider, the referenced
  variable, `credential_configured` (**a boolean** — the value is never read into
  the response), the non-secret SMTP transport fields, and `stored_invalid`.
* `provider_readiness()` names every reason delivery would fail (no network call,
  no email sent) so "validate" can never report a provider as usable when it
  would fail at the first send.
* `deliver_email_sync()` / `deliver_email()` (off-loop via `asyncio.to_thread`,
  because SMTP is blocking) select the adapter and **fail closed**.
* `platform_settings_repo()` gives non-request callers (legacy helpers,
  background jobs) a best-effort settings repository; any failure yields `None`
  and the documented defaults apply — configuration being unavailable must never
  stop configuration being *safe*.

`resend` is imported lazily inside `_resend_client()`, so no module or test needs
the package (or a network) at import time.

### 3.2 Persistence and merge semantics — `backend/data/settings.py`

* New row key `email_provider`, new `get_email_provider()` /
  `update_email_provider()` using the same `INSERT … ON CONFLICT (setting_key) DO
  UPDATE … RETURNING` shape as the retention and upload-policy rows (no new
  table, no migration).
* `_email_provider_from_row()` maps the row defensively: a missing, unparseable
  or malformed payload yields `None` per field, and a credential variable outside
  the allow-list is dropped even if the row was edited by hand.
* A module-level `_UNSET` sentinel distinguishes **"field omitted"** (keep the
  stored value) from **"explicit `None`"** (clear it). Without that distinction an
  unused SMTP transport could never be removed, because a cleared field would
  silently revert to its previous value.

### 3.3 Admin API — `backend/api/v3_settings.py`

Three endpoints, all `Depends(require_admin())`:

| Method | Path | Behaviour |
| --- | --- | --- |
| `GET` | `/api/v3/settings/email-provider` | describes the provider **in force** (default provider when unconfigured), the credential *variable*, whether it is present, the allow-listed `credential_options`, and `readiness` |
| `POST` | `/api/v3/settings/email-provider/validate` | validates a candidate configuration **without persisting it**; returns `{valid, errors, settings}` — `settings` always describes what is actually in force, never the rejected candidate |
| `PUT` | `/api/v3/settings/email-provider` | validates the *merged* configuration, then persists; anything invalid is `422` and **nothing is stored** (fail closed) |

Implementation details that matter:

* the request model sets `model_config = ConfigDict(extra="forbid")`, so a
  credential sent as an ordinary field is rejected with `422` rather than
  silently dropped or stored;
* an omitted/`null` field keeps its stored value; an **empty string clears** it;
* switching provider without naming a credential variable **re-points** the
  reference to that provider's default variable — a stale `CT_SMTP_PASSWORD`
  left over from a previous selection would otherwise be read for Resend and the
  newly selected provider would fail closed for the wrong reason;
* `provider` is only accepted with a complete transport (`smtp_host` is required
  for SMTP — the provider is never half-configured).

### 3.4 Canonical mailer and call-site migration

`backend/services/v3_email.py` now resolves **both** the sender and the provider
from platform configuration:

* `resolve_configured_provider(settings_repo)` → the persisted provider config
  (fail-open to the documented default, never to "no provider");
* `send_transactional_email(..., settings_repo=...)` is the canonical path for
  request-scoped callers (it applies the admin-configured sender *and* provider);
* `send_platform_email(...)` is the canonical entry point for callers with **no**
  request scope — it resolves the platform settings itself through
  `platform_settings_repo()`.

Every email call site was migrated to that path:

| Call site | Before | After |
| --- | --- | --- |
| `api/v3_organizations.py` (org-created confirmation) | `send_transactional_email(settings_repo=…)` | unchanged, now also provider-aware |
| `api/v3_discovery.py` (adoption verification code) | `send_transactional_email(settings_repo=…)`, local `resolve_configured_sender` import removed | unchanged, now also provider-aware |
| `services/operational_alerting.py` | `send_transactional_email(settings_repo=…)` | unchanged; still raises on an honest failure instead of faking success |
| `routes/notifications.py` (`send_email` + 3 call sites) | direct Resend SDK, hard-coded From, synchronous | `async`, routes through `send_platform_email`, returns the honest result |
| `utils/email.py` (`send_email` + 9 template senders) | direct Resend SDK, module-level `resend.api_key` mutation | routes through `send_platform_email`; stale `os`/`json` imports removed |
| `services/email_service.py` (2 senders) | direct Resend SDK, module-level `resend.api_key`, **and a pre-existing `IndentationError`** | instantiates cleanly, routes through `send_platform_email`, returns the honest result |

`services/email_service.py` was dead code (no Python/JS/TS/Markdown file
references it) and could not be imported at `HEAD`; it is now valid and
provider-agnostic. Its two senders became `async` (documented here) — this cannot
regress a caller, because no caller could previously import the module.

### 3.5 Admin Dashboard UI

* `frontend/src/v3/api.js` — seven new client functions for upload policy,
  notification sender and email provider (GET / validate / PUT).
* `frontend/src/v3/ops/SettingsTab.jsx` — two new control-plane panels:
  **Upload policy** (per-file, files-per-batch, batch-total, with the effective
  values, the documented defaults and the ratified ceilings shown) and
  **Email delivery** (provider selection, SMTP host/port/username/STARTTLS, the
  credential *variable* chosen from the server-published allow-list,
  Validate / Save, the delivery-readiness blocking issues, and the platform From
  address). No credential input exists anywhere in the UI, and no credential
  value is ever displayed — the panel shows only whether the referenced variable
  is present in the environment.
* The panels are separate load/save state blocks (as with GA4), so a failure in
  one configuration surface cannot block the others.

### 3.6 Upload policy

CT-FINAL-01 delivered the canonical policy (`utils/upload_limits.py`), its
persistence and its server-side enforcement on the ingress paths. CT-FINAL-02
adds the Admin Dashboard control surface and re-verifies the enforcement points
and the CT-FINAL-01 regression suite. Enforcement is unchanged and remains
server-side; the UI is never the limit boundary.

---

## 4. Files changed

### 4.1 Modified (tracked, working tree)

```
backend/api/v3_discovery.py                  |   8 +-
backend/api/v3_organizations.py              |   9 +-
backend/api/v3_settings.py                   | 191 ++++++++++-
backend/data/settings.py                     | 132 ++++++++
backend/routes/notifications.py              |  49 ++-
backend/services/email_service.py            |  55 +--
backend/services/operational_alerting.py     |  11 +-
backend/services/v3_email.py                 | 135 +++++---
backend/tests/unit/api/fakes.py              |  48 +++
backend/utils/email.py                       |  43 +--
frontend/src/v3/__tests__/review-api.test.js |  14 +
frontend/src/v3/api.js                       |  52 +++
frontend/src/v3/ops/SettingsTab.jsx          | 434 +++++++++++++++++++++++-
13 files changed, 1060 insertions(+), 121 deletions(-)
```

### 4.2 Added

```
backend/services/email_provider.py                                  (provider abstraction)
backend/tests/unit/api/test_ct_final_02_email_provider.py           (CT-FINAL-02 regression suite)
frontend/src/v3/__tests__/settings-tab-email-provider.test.jsx      (UI regression suite)
docs/architecture/CT-FINAL-02-20260929-EMAIL-AND-UPLOAD-CONFIGURATION-REPORT.md  (this report)
```

### 4.3 Deliberately untouched

Unrelated modified files already present in this working tree (`.gitignore`,
`admin/src/components/admin/DefraFactorModal.js`, `ImportDefraModal.js`,
`admin/src/pages/admin/DefraFactors.js`, `frontend/App_.js`, `frontend/src/App.js`,
`frontend/src/components/ManualEntryStandalone.jsx`,
`backend/tests/unit/test_ct_implement_01_remediation.py`,
the three `docs/architecture/CT-*-REPORT.md` files, and numerous untracked
documents) were **not** staged, edited, reverted or absorbed by this task.

---

## 5. Security model and invariants

| Invariant | Mechanism | Test |
| --- | --- | --- |
| Credentials live **only** in the environment | the adapter reads the allow-listed variable at delivery time; nothing else reads a secret | `test_delivery_uses_the_selected_smtp_adapter_and_env_credential`, `test_only_allow_listed_credential_variables_are_readable` |
| An administrator cannot point the platform at an arbitrary secret | `ALLOWED_CREDENTIAL_ENVS` is re-checked in `credential_value()` **and** enforced in the API (`422`) **and** in the row reader (a hand-edited row is dropped) | `test_invalid_configurations_are_refused`, `test_put_refuses_invalid_configuration_and_stores_nothing` |
| A credential cannot be stored as a setting | `extra="forbid"` on the request model + secret-field rejection in `normalise_provider_config` | `test_a_credential_submitted_as_a_setting_is_refused`, `test_put_refuses_a_credential_smuggled_in_as_a_setting` |
| No credential appears in a response | the description reads only *presence*; responses were grepped for sentinel secret values | `test_no_credential_value_ever_appears_in_a_response`, `test_describe_never_returns_a_credential_value` |
| No credential appears in an error/log | `_scrub()` replaces the password with `***` before a reason is returned | `test_delivery_never_leaks_the_credential_in_its_failure_reason` |
| Delivery fails closed and never falls back | an unconfigured selected provider returns `(False, reason)`; a cross-provider fallback is asserted impossible | `test_delivery_is_fail_closed_and_never_falls_back_to_another_provider`, `test_canonical_mailer_is_honest_when_the_provider_is_unconfigured` |
| No fabricated success | every legacy helper returns the mailer's honest result | `test_notification_route_helper_never_fakes_a_success`, `test_utils_email_helper_routes_through_the_platform_mailer` |
| Only administrators may change it | `require_admin()` on GET, validate and PUT | `test_denied_for_non_admin_and_anonymous`, `test_an_organisation_owner_…`, `test_a_consultant_…`, `test_processing_entity_staff_…` |
| One provider adapter, no scattered coupling | repo-wide source assertion: no module except `email_provider.py` mentions `import resend` / `resend.Emails` | `test_no_module_outside_the_provider_adapter_imports_a_provider_sdk` |

---

## 6. Evidence — provider abstraction (commands and results)

```
$ python3 -c "from services import email_provider as ep; print(ep.normalise_provider_config(None))"
{'provider': 'resend', 'smtp_host': None, 'smtp_port': None, 'smtp_username': None,
 'smtp_use_tls': True, 'credential_env': 'RESEND_API_KEY'}

unknown provider                      -> ValueError: provider must be one of: resend, smtp
secret field                          -> ValueError: provider credentials must never be stored as settings…
arbitrary env (AWS_SECRET_ACCESS_KEY) -> ValueError: credential_env must be one of: CT_SMTP_PASSWORD, RESEND_API_KEY, SMTP_PASSWORD
smtp without host                     -> ValueError: smtp_host is required when the SMTP provider is selected…
host with scheme                      -> ValueError: smtp_host must be a hostname only (no scheme and no port)
bad port (0)                          -> ValueError: smtp_port must be an integer between 1 and 65535
bad tls type ("yes")                  -> ValueError: smtp_use_tls must be a boolean

configured_provider_name({"provider": "nope"}) -> 'resend'   (fail closed)
credential_value("AWS_SECRET_ACCESS_KEY")      -> None       (allow-list enforced)
deliver_email_sync(config=None)                -> (False, 'email delivery not configured (RESEND_API_KEY unset)')
deliver_email_sync(config={provider: smtp})    -> (False, 'email delivery not configured (SMTP provider selected without smtp_host)')
deliver_email_sync(smtp without credential)    -> (False, 'email delivery not configured (CT_SMTP_PASSWORD unset)')
```

## 7. Evidence — admin API (authorization and validation matrix)

Executed through the real application (`api.router.create_app`) with the
in-memory dependency overrides, i.e. real routing and real dependencies:

```
GET  /api/v3/settings/email-provider   (staff admin) 200  provider=resend, is_default=True,
                                                          credential_configured=False,
                                                          readiness.ready=False + blocking issue
GET  /api/v3/settings/email-provider   (org member)  403
GET  /api/v3/settings/email-provider   (org owner)   403
GET  /api/v3/settings/email-provider   (consultant)  403
GET  /api/v3/settings/email-provider   (PE staff)    403
GET  /api/v3/settings/email-provider   (anonymous)   401
PUT  {smtp + host + username}                        200  persisted, credential_env=CT_SMTP_PASSWORD
PUT  {provider: "sendgrid"}                          422  nothing stored
PUT  {provider: "smtp"}                              422  (never half-configured)
PUT  {smtp_host: "https://mail.example.com"}         422
PUT  {smtp_port: 0 | 99999}                          422
PUT  {credential_env: "AWS_SECRET_ACCESS_KEY"}       422
PUT  {credential_env: "lower_case"}                  422
PUT  {api_key | password | credential}               422  (extra="forbid")
PUT  {provider: "resend"} after SMTP                 200  credential_env re-points to RESEND_API_KEY
PUT  {provider: "resend", smtp_host: ""}             200  transport cleared (stored smtp_host → null)
POST /api/v3/settings/email-provider/validate {smtp} 200  valid=false + errors, nothing persisted
POST /api/v3/settings/email-provider/validate {smtp complete}
                                                     200  valid=true, no write, readiness issues listed
```

Every rejection above was followed by a repository read proving **nothing was
written**.

## 8. Evidence — canonical mailer and legacy routing

```
send_transactional_email(settings_repo=<smtp, sender no-reply@carbontally.co.uk>)
  → (True, 'sent'); adapter called with from_email = configured sender, provider = smtp
send_transactional_email(settings_repo=<nothing configured>)
  → (False, reason)                       # honest, not a fake success
send_platform_email(...) with monkeypatched platform_settings_repo()
  → resolves the stored provider without a request scope and delivers via SMTP
routes.notifications.send_email(...)   → the canonical mailer is awaited; result returned
utils.email.send_email(...)            → the canonical mailer is awaited; result returned
services.email_service.send_beta_confirmation_email(...) → 2 canonical sends (user + founder)
services.email_service.send_beta_invite_email(...)       → 1 canonical send
```

```
$ grep -rn 'import resend\|resend\.' --include=*.py backend
backend/services/email_provider.py:372:        import resend  # type: ignore
backend/services/email_provider.py:375:    resend.api_key = api_key
```

## 9. Evidence — Admin Dashboard UI

```
$ CI=true npx react-scripts test --watchAll=false --testPathPattern='(settings-tab-email-provider|settings-tab-analytics|review-api)'
PASS src/v3/__tests__/settings-tab-email-provider.test.jsx
PASS src/v3/__tests__/settings-tab-analytics.test.jsx
PASS src/v3/__tests__/review-api.test.js
Test Suites: 3 passed, 3 total
Tests:       36 passed, 36 total
```

The new suite asserts: the configured upload limits and ratified ceilings are
shown; the policy saves through the admin endpoint; the provider, its transport
and the credential *options* render from server data; readiness blocking issues
are surfaced instead of a success claim; Validate posts without saving; Save
posts the provider and the From address; and no credential value appears
anywhere in the rendered DOM.

## 10. Evidence — persistence on a real Postgres (disposable stack, rolled back)

Target: `ct_final01_pg` (the CT-FINAL-01 **disposable clone**, per the F-046-1
invariant; the shared/investor-demo/production databases were never touched).

```
$ docker exec ct_final01_pg psql -U postgres -d postgres -c "\d system_settings"   # read-only
 setting_key   | character varying
 setting_value | jsonb
 setting_type  | character varying
 description   | text
 updated_by    | uuid
 updated_at    | timestamp with time zone
 created_at    | timestamp with time zone
CREATE UNIQUE INDEX system_settings_setting_key_key ON public.system_settings (setting_key)

$ docker exec … psql -c "BEGIN; INSERT INTO public.system_settings (…) VALUES ('email_provider', …)
                         ON CONFLICT (setting_key) DO UPDATE … RETURNING setting_key, setting_value; ROLLBACK;"
email_provider | {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": 587,
                  "smtp_use_tls": true, "smtp_username": "u@example.com",
                  "credential_env": "CT_SMTP_PASSWORD"}        ← INSERT path
email_provider | {"provider": "resend"}                          ← conflict/UPDATE path
ROLLBACK

$ docker exec ct_final01_pg psql -t -c 'select count(*) from system_settings'
1        (only the pre-existing platform_retention row — no residue)
```

This proves the exact statement the repository issues, the `ON CONFLICT` target
and the JSONB round-trip work against a real schema — **without writing to any
database**. It does not prove that the application server persists the row over
the wire; that requires a running API against a database (see §13).

## 11. Evidence — upload-policy enforcement coverage

```
$ grep -rn 'enforce_batch\|enforce_single_file\|resolve_policy' --include=*.py backend
api/v3_documents.py:236,293          resolve_policy + enforce_single_file   (canonical documents)
routes/upload.py:147,181,252,394,676 resolve_policy (5 paths) + enforce_single_file
routes/organizations/files.py:564,812,851  resolve_policy + enforce_batch + enforce_single_file
routes/reports.py:1318               resolve_policy + enforce_single_file
api/v3_consultants.py:1300           resolve_policy
```

Every ingress path that creates a storage object resolves the persisted policy
and enforces it before anything is written; the batch path enforces count,
per-file size and the aggregate total. The CT-FINAL-01 suite
(`test_ct_final_01_upload_limits.py`, 45 tests: below/at/above each limit,
malformed/zero/negative values, legacy parity, and the wiring assertions) still
passes unchanged after this task's edits.

## 12. Tests — commands and results

| Suite | Command | Result |
| --- | --- | --- |
| CT-FINAL-02 backend | `python3 -m pytest tests/unit/api/test_ct_final_02_email_provider.py -q` | **71 passed** |
| CT-FINAL-01 backend (regression) | `python3 -m pytest tests/unit/api/test_ct_final_01_upload_limits.py -q` | **45 passed** |
| Frontend (new + existing) | `CI=true npx react-scripts test --watchAll=false --testPathPattern='(settings-tab-email-provider\|settings-tab-analytics\|review-api)'` | **36 passed / 3 suites** |
| Full backend unit sweep | `python3 -m pytest tests/unit -q` | 7 failures — **all A/B-proven pre-existing** (§14) |

---

## 13. Environment limitations and honesty notes

1. **No live email was sent.** No `RESEND_API_KEY` and no SMTP credential are
   configured in this environment, and sending real email from a verification
   run is not appropriate. External delivery through either provider is
   therefore **NOT YET VERIFIED**. What *is* verified is the adapter selection,
   the sender/provider resolution, the credential lookup, the fail-closed
   behaviour, and the honest result contract (all with injected transports).
2. **No browser session was run.** The new Admin Dashboard panels are verified
   by Jest + Testing Library (real component, mocked API client) and by static
   review, not by a live browser against a running stack. No screenshot evidence
   exists for these two panels.
3. **No API server was started against a database.** The endpoints were executed
   in-process through the real FastAPI app with in-memory repositories; the
   repository SQL was separately validated against a real Postgres (§10). The
   combination is strong but is not a substitute for one end-to-end
   HTTP→Postgres round-trip, which is recorded as remaining work.
4. **No RLS/storage/JWT verification was re-run.** This task added **no** schema,
   no RLS policy, no storage policy and no JWT surface (the only new persisted
   value is a row in the existing `system_settings` table), so there is no new
   isolation surface to test. The CT-FINAL-01 isolation evidence
   (`docs/architecture/CT-FINAL-01-20260928-SECURITY-FIX-AND-FINALIZE-REPORT.md`
   §6) stands as recorded there; it was not re-derived here.
5. **No deployment, no commit, no migration applied** to any environment.
6. **The shared/live database was not read.** No `.env`, database URL or
   service key is present in this working tree (only `.venv`), so the live
   DEFRA/SEAI factor count (expected 7,049 in CT-FINAL-01's record) could not be
   re-confirmed read-only. It is **UNVERIFIED** here, and no shared database was
   contacted — which also honours the "read-only at most, never mutate" rule.
   The CT-FINAL-01 baseline (7,029 DEFRA / 20 SEAI / 7,049 total) is unchanged by
   this task, which performs no factor or schema changes at all.
7. **Session tooling limitation:** the interactive shell wedged twice during long
   heredocs. Every command in this report was therefore executed
   non-interactively with its output captured to a file, and the results quoted
   above are read from those captured outputs.

## 14. Pre-existing findings (disclosed, not caused by this task)

### 14.1 The full unit sweep has 7 failures — A/B proven pre-existing

```
$ cd /home/shomonrobie/ct_93d5cdd/backend && python3 -m pytest tests/unit -q
7 failed   (list below)

$ git worktree add /tmp/f2/head_wt HEAD          # pristine cabdca8, none of this task's edits
$ cd /tmp/f2/head_wt/backend && python3 -m pytest <the same 7 tests> -q
7 failed   (identical set, identical assertions)
```

| Failing test | Cause (from the A/B trace) |
| --- | --- |
| `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | asserts `len(migrations) == 71`; the repository now has 93 — a stale hard-coded count |
| `test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | its allow-list of "migrations after I1" is not updated for the later P16-R5/P17/CT-FINAL-01 migrations |
| `test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | same stale "latest migration" expectation |
| `test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | does not know `20261024000000_ct_final_01_documents_bucket_size_limit.sql` |
| `test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | expects `15/01/2026`; the engine now returns ISO `2026-01-15` |
| `test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | expects `suggested_data == {}`; the engine now also returns `extraction_evidence` |
| `test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | same shape expectation |

None of these touch email, settings, notifications or upload limits. They are
**test-expectation drift**, not product regressions, and they are outside
CT-FINAL-02's scope. They are recorded as a backlog finding rather than silently
"fixed": editing another workstream's ratified migration/test expectations would
be an unratified product decision.

### 14.2 `services/email_service.py` was invalid at HEAD — **fixed here**

It carried a pre-existing `IndentationError` (lines 18–20) and a second one in
`log_email_status`, was unreferenced anywhere in the repository, and imported the
Resend SDK at module level while mutating `resend.api_key`. It now imports
cleanly, is provider-agnostic, and returns honest delivery results. Because it
could not be imported at HEAD, no caller can be broken by the change; its two
senders are now `async` (a future caller must await them).

### 14.3 Stray tooling artefacts in the working tree (pre-existing)

`git status` shows unrelated untracked items (`8`, `=`, `.costrict/`,
`.p18_audit_tmp/`, `costrict-p3-ov-01-…txt`, several `docs/` bundles, a
`.~lock.*#` file). They were left exactly as found — not deleted, not staged.

---

## 15. Verification checklist (A–I)

| | Area | Evidence | Status |
| --- | --- | --- | --- |
| **A** | Files changed | §4; `git diff --stat HEAD` (13 tracked files, +1060/−121) plus 3 added files | **VERIFIED** |
| **B** | Database changes | none required; `system_settings` reuse confirmed by read-only schema query; the upsert was executed and rolled back with 0 residue | **VERIFIED** (no write to any persistent DB) |
| **C** | Migrations | none added or edited; `git status` shows no new `supabase/migrations/*.sql` | **VERIFIED** |
| **D** | API changes | 3 new admin-only endpoints; GET / POST-validate / PUT matrix incl. 401/403/422 and "nothing stored" after every rejection | **VERIFIED** |
| **E** | Frontend changes | 7 new client functions; 2 new panels; 36 Jest tests pass across 3 suites | **VERIFIED** (Jest + static review) |
| **F** | Tests | 71 new backend + 45 CT-FINAL-01 regression + 36 frontend = **152 passing**; the sweep's 7 failures A/B-proven pre-existing | **VERIFIED** |
| **G** | Runtime verification | endpoints executed through the real app in-process; provider/sender resolution, adapter selection and fail-closed delivery all exercised; **no live email, no live HTTP→DB round-trip** | **PARTIALLY VERIFIED** — external delivery **NOT YET VERIFIED** |
| **H** | Security verification | ALLOW/DENY matrix (admin vs member/owner/consultant/PE/anonymous); allow-listed credential variables only; secrets rejected with 422; no credential in responses, reasons or logs (sentinel probes); no provider fallback; single-adapter source assertion | **VERIFIED** (application level) |
| **I** | Git state | branch `p8-release-reconciled`, base `cabdca8`; **no commits, no pushes, no resets, no history rewrite**; unrelated working-tree changes preserved | **VERIFIED** |

---

## 16. Remaining limitations and recommended next steps

1. **Live delivery acceptance (external configuration).** With a real
   `RESEND_API_KEY` (or SMTP credentials) set in the deployment environment,
   send one email with the default provider and one with SMTP, and confirm the
   From address and the delivery result. Until then the external-delivery claim
   is **NOT YET VERIFIED**.
2. **One end-to-end HTTP→Postgres round-trip** against a disposable stack
   (`ct_*` clone) to observe the `email_provider` row being created by the API
   and read back after an application restart.
3. **Browser QA** of the two new Admin Dashboard panels (responsive widths,
   keyboard operation, the readiness/validation alerts) — no browser session was
   available in this environment.
4. **DT-1 — test-expectation drift (§14.1):** 7 pre-existing failures in the
   `tests/unit` sweep need an owner to refresh the stale migration/date/shape
   expectations. Not fixed here (another workstream's ratified expectations).
5. **D-7 — PO DECISION REQUIRED (carried forward, unchanged).** The CT-FINAL-01
   live isolation probe observed `ownerC → inactive orgC` returning `200`.
   Whether an inactive organisation should deny all org-scoped access to its own
   owner (until an administrator re-enables it) is a **product/security policy
   decision**, not an implementation detail. It was not changed here.

---

## 17. Verdict

| # | Item | Status |
| --- | --- | --- |
| 1 | Provider abstraction with two implemented providers (Resend + SMTP) | **IMPLEMENTED · TESTED · VERIFIED** (in-process) |
| 2 | Provider configuration persisted in `system_settings` (no migration) | **IMPLEMENTED · TESTED · VERIFIED** (SQL validated on real Postgres) |
| 3 | Admin-only GET / validate / PUT endpoints for the provider | **IMPLEMENTED · TESTED · VERIFIED** |
| 4 | Credentials never persisted, returned, logged or exposed to the UI | **IMPLEMENTED · TESTED · VERIFIED** |
| 5 | Allow-list prevents pointing the platform at an arbitrary secret | **IMPLEMENTED · TESTED · VERIFIED** |
| 6 | Fail-closed delivery, no cross-provider fallback, no fabricated success | **IMPLEMENTED · TESTED · VERIFIED** |
| 7 | Canonical mailer applies the admin-configured sender **and** provider | **IMPLEMENTED · TESTED · VERIFIED** |
| 8 | Every legacy/background email call site migrated | **IMPLEMENTED · TESTED · VERIFIED** |
| 9 | Single provider adapter in the backend (source assertion) | **IMPLEMENTED · TESTED · VERIFIED** |
| 10 | Admin Dashboard UI for provider + upload policy | **IMPLEMENTED · TESTED** (Jest) · **BROWSER QA NOT PERFORMED** |
| 11 | Upload policy editable from the Admin Dashboard | **IMPLEMENTED · TESTED · VERIFIED** |
| 12 | Upload limits still enforced server-side on every ingress path | **VERIFIED** (CT-FINAL-01 suite: 45/45 pass) |
| 13 | External email delivery through Resend / SMTP | **NOT YET VERIFIED** (no credential; no live send) |
| 14 | End-to-end HTTP→Postgres persistence round-trip | **NOT VERIFIED** (recorded as remaining work) |
| 15 | RLS / storage / JWT isolation for this change | **N/A** — no new schema, policy or auth surface (CT-FINAL-01 isolation evidence stands) |
| 16 | Full `tests/unit` sweep green | **NOT GREEN — 7 failures, all A/B-proven PRE-EXISTING** (§14.1) |
| 17 | `services/email_service.py` importable and provider-agnostic | **FIXED** — pre-existing defect (§14.2) |
| 18 | D-7 (inactive organisation access) | **PO DECISION REQUIRED** — unchanged, carried forward |
| 19 | Deployment | **NOT PERFORMED** (by instruction) |
| 20 | Repository state | **NOT COMMITTED** — working tree only, unrelated changes preserved |

**Bottom line:** the email delivery provider/sender and the upload policy are now
administrator-configurable end-to-end — configuration → persistence → canonical
mailer → selected adapter → honest delivery result — with credentials confined to
the environment and delivery failing closed. Everything testable in this
environment passes; **external email delivery and browser QA remain unverified**,
and nothing was committed or deployed.

---

## 18. Git state and artefacts

```
$ git rev-parse --abbrev-ref HEAD   → p8-release-reconciled
$ git rev-parse HEAD                → cabdca8380415e73a25cf23eb393d0b15c0af391
$ git worktree list                 → only the primary working tree (the A/B
                                      worktree used for §14.1 was removed)
```

Artefacts produced: this report; the three added source/test files (§4.2); the
captured command outputs of this session under `/tmp/f2/` (not committed).
