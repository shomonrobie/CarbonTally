# CarbonTally — Analytics & Integrations — Google Analytics 4 (GA4)

**Task type:** bounded implementation
**Date:** 2026-09-13
**Scope:** Google Analytics 4 only, via Google's `gtag.js`
**Reference roadmap:** `docs/architecture/CarbonTally_Marketing_Analytics_Architecture_12_24_Month_Plan.md` (and its copy at the repository root)

This document describes the GA4 integration that has been implemented. It does not describe, and must not be
read as authorising, any other analytics or marketing provider.

---

## 1. What is implemented

* A single **Analytics & Integrations** administration area containing **Google Analytics** configuration:
  an **Enabled** flag and a **Measurement ID**.
* Configuration is persisted through CarbonTally's **existing** platform settings mechanism (no new settings
  subsystem, no new database table, no migration).
* Conditional loading of Google's `gtag.js`: GA4 is loaded only when it is enabled, correctly configured,
  running in an analytics environment, and permitted by the visitor's existing cookie choice.
* Focused tests for the loading decisions, the consent/environment gates, the Admin authorization boundary and
  the fail-safe behaviour.

### Explicitly NOT implemented

Google Tag Manager, PostHog, LinkedIn Insight Tag, Meta Pixel, Microsoft Clarity, Hotjar, Intercom or any other
support/onboarding platform, a custom analytics event taxonomy, a marketing attribution system, a CarbonTally
analytics dashboard, any server-side Google Analytics API, and any speculative database table or UI section for
future providers. These remain roadmap items in the reference plan and require separate authorisation.

---

## 2. Where GA4 is configured

**CarbonTally Admin → Operations → Settings → Analytics & Integrations.**

That surface already hosts the platform-wide configuration capability (N3 retention), is reachable only by
internal staff with staff-admin capability, and is backed by the existing platform settings API. The analytics
section is additive: the retention section is unchanged.

| Layer | File |
| --- | --- |
| Admin UI | `frontend/src/v3/ops/SettingsTab.jsx` |
| Frontend API client | `frontend/src/v3/api.js` (`getAnalyticsSettings`, `updateAnalyticsSettings`) |
| API | `backend/api/v3_settings.py` (`GET`/`PUT /api/v3/settings/analytics`) |
| Persistence | `backend/data/settings.py` (`SettingsRepository.get_analytics` / `update_analytics`) |

### The Measurement ID

The Measurement ID is entered in the Admin field and stored as plain configuration. It is **not** a secret: it is
publicly visible in the page source of any site that runs GA4, so it is not stored as a credential and no Google
service-account credentials, OAuth clients or API secrets are involved in this task.

Accepted form: `G-` followed by 4–20 uppercase alphanumeric characters (for example `G-XXXXXXXXXX`). The value is
trimmed and upper-cased before storage. Universal Analytics identifiers (`UA-…`) and Google Tag Manager container
identifiers (`GTM-…`) are **rejected** — they are not GA4 measurement IDs and cannot configure GA4.

### How Analytics is enabled and disabled

* **Enabled** is an explicit on/off setting. Turning it off stops GA4 from loading. The stored Measurement ID is
  retained, so the provider can be re-enabled without re-entering it.
* Enabling analytics **without** a valid Measurement ID is rejected (`422`), so a half-configured provider is
  never persisted. This is the same validation posture as the existing retention settings surface.

---

## 3. Persistence

GA4 configuration is stored in the **existing** `system_settings` table, under its own row:

| Column | Value |
| --- | --- |
| `setting_key` | `analytics_ga4` |
| `setting_type` | `analytics_integrations` |
| `description` | `Analytics & Integrations provider configuration (Google Analytics 4)` |
| `setting_value` (JSONB) | `{"enabled": <bool>, "ga4_measurement_id": <string\|null>}` |
| `updated_by` / `updated_at` | The updating admin and the update time (existing convention) |

`setting_value` is the table's generic JSONB column, so **no schema change and no migration are required**, and no
provider-specific table is created. The table's `setting_key` is unique, so the upsert is idempotent.

Fail-closed read behaviour: if the row is absent, the payload is unparseable, or the value is malformed, the
configuration is reported as *disabled with no Measurement ID* — the read never raises on stored data.

---

## 4. API contract

Both endpoints are served from the existing V3 platform settings router. No new HTTP API surface was invented.

### `GET /api/v3/settings/analytics` — public read

Deliberately **unauthenticated**: CarbonTally's public marketing surface must decide whether to load GA4 *before*
a visitor signs in. The response is trimmed to the two non-secret provider fields — it never returns retention
values, internal actor identifiers or any tenant data.

```json
{ "settings": { "enabled": true, "ga4_measurement_id": "G-XXXXXXXXXX" } }
```

### `PUT /api/v3/settings/analytics` — `require_admin()`

Protected by CarbonTally's existing internal-admin authorizer (role `admin`/`system_admin`, or an explicit
superuser permission). Processing Entity staff are refused by that authorizer regardless of role name, and
unauthenticated callers receive `401`.

Request:

```json
{ "enabled": true, "ga4_measurement_id": "G-XXXXXXXXXX" }
```

Validation failures return `422` with an explanatory message: a malformed identifier, or `enabled: true` with no
identifier.

---

## 5. Conditional loading at runtime

The loader is `frontend/src/lib/analytics/ga4.js`, mounted once for the whole application (both the public
marketing surface and the authenticated application) by `frontend/src/components/AnalyticsBootstrap.jsx`, which
renders nothing.

**All four conditions must hold** for `gtag.js` to be loaded and GA4 initialised:

| Condition | Detail |
| --- | --- |
| Admin setting | `enabled` is true |
| Measurement ID | present and a valid GA4 ID (`G-…`) |
| Environment | the deployment is an analytics environment (§6) |
| Consent | the visitor has accepted cookies (§7) |

Behaviour by case:

* **Disabled** — `gtag.js` is not loaded, GA4 is not initialised, and normal CarbonTally operation is unaffected.
* **Enabled + valid Measurement ID + production + consent** — `gtag.js` is loaded from
  `https://www.googletagmanager.com/gtag/js?id=<id>` and GA4 is initialised with the configured ID.
* **Enabled + missing/invalid Measurement ID** — GA4 is not loaded or initialised; the application behaves
  normally.
* **Any error** — a failed configuration request, a blocked script, or a storage failure is swallowed. Analytics
  is never a dependency for CarbonTally's own operation. The configuration request is bounded (5s) so analytics
  can never hang the page.

Loading is idempotent: a second evaluation (for example after the visitor accepts cookies on a later page)
reuses the already-injected tag instead of adding another.

---

## 6. Environment separation

Production and non-production deployments can point at the same backend and therefore the same Admin settings
row. To prevent development or staging traffic from being sent to the production GA property merely because an
Admin toggled the setting, the **deployment** gates traffic:

```
REACT_APP_ENVIRONMENT=production
```

GA4 loads only when this build-time variable is exactly `production`. An unset or unrecognised value suppresses
analytics entirely (fail closed). This follows the existing frontend environment convention
(`process.env.REACT_APP_*`) and adds no new configuration mechanism.

**Operational prerequisite:** set `REACT_APP_ENVIRONMENT=production` in the production frontend deployment's
environment settings only. Development, QA and staging deployments must leave it unset. The Admin surface states
plainly when the current deployment is not an analytics environment, so an admin is never left guessing why
enabling the setting had no visible effect.

---

## 7. Privacy and consent

CarbonTally's existing cookie-consent mechanism is respected and **not** duplicated.

* The consent record remains the existing `cookieConsent` `localStorage` entry, and
  `frontend/src/CookieBanner.jsx` remains the **only** place a visitor makes that choice.
* `frontend/src/lib/consent.js` is the shared contract for that record (key, accepted/declined values, the change
  event, read and record helpers). Analytics reads this record; it does not introduce a second consent system.
* GA4 loads **only** when the recorded choice is `accepted`.
* When the choice is not accepted, the analytics configuration endpoint is **not contacted at all** — no request
  is made on behalf of analytics for a visitor who has not consented.
* A choice made after the application has loaded is honoured: the consent helper dispatches a change event (and
  listens for cross-tab `storage` events), and the bootstrap re-evaluates on that signal.

The banner's own behaviour is unchanged (same prompt, same accept/decline outcomes). The only change is that the
recorded value is also announced through the shared consent event.

---

## 8. Data-collection boundary

This integration sends **no CarbonTally business data**. It configures only GA4's standard page view, with the
measurement ID as the single argument — there are **no custom events**, no event parameters, no user IDs, no
user-level profiling and no marketing pixels.

Never sent to analytics: passwords, authentication tokens, API keys, service credentials, signed URLs, uploaded
files, document or evidence contents, activity quantities, emissions results, emission factors, report contents,
customer financial information, private organisation information or any other sensitive application data.

---

## 9. Testing

### Frontend (`frontend/src/lib/analytics/ga4.test.js`, `frontend/src/components/AnalyticsBootstrap.test.jsx`)

Real module behaviour, no analytics mocks: measurement-ID validation and normalisation; the production-only
environment gate (including an unset value failing closed); the load decision for disabled / missing / invalid /
non-production / unconsented configurations; injection of `gtag.js` with the correct URL and `async`; that GA4 is
initialised with the measurement ID and nothing else; idempotent loading; failure tolerance when the tag cannot be
injected; fail-safe configuration retrieval (error response, network failure, malformed payload, no API URL); that
no request is made without consent; and the consent contract (record, read, change events, unreadable storage).
45 + 5 tests.

### Backend (`backend/tests/unit/api/test_v3_settings_analytics.py`)

Route registration; the write route requires the internal-admin authorizer; the read route carries **no**
authentication dependency (an asserted, deliberate decision, not an oversight); identifier normalisation and
rejection of `UA-…`, `GTM-…` and malformed values; fail-closed row mapping (absent row, unparseable payload,
malformed value); API round-trip through the contract; the public read returning only the two non-secret fields;
and HTTP-level authorization (`403` for a customer member, `403` for Processing Entity staff, `401` for an
unauthenticated caller) plus validation (`422`). 28 tests.

### Admin UI (`frontend/src/v3/__tests__/settings-tab-analytics.test.jsx`)

The retention surface still renders and loads unchanged (no regression); analytics configuration is not exposed
to staff without admin capability; the configured state renders; the non-production deployment is stated plainly;
saving calls the platform settings API with the entered configuration; and an invalid identifier cannot be
submitted. 6 tests.

### Results

```
backend  : 33 passed  (28 analytics + 5 existing retention)
frontend : 52 passed  (ga4 47, bootstrap 5)  + 6 passed (admin UI)
```

The suite-wide picture is recorded in the task report; the pre-existing in-flight failures in the working tree at
the time of implementation were unrelated to this change (see §11).

---

## 10. Files changed

| File | Change |
| --- | --- |
| `backend/data/settings.py` | analytics read/update on the existing `system_settings` row |
| `backend/api/v3_settings.py` | public `GET` + admin `PUT /api/v3/settings/analytics`, ID validation |
| `backend/tests/unit/api/test_v3_settings_analytics.py` | new — API, authorization, fail-closed tests |
| `frontend/src/lib/consent.js` | new — shared contract for the existing consent record |
| `frontend/src/lib/analytics/ga4.js` | new — GA4 gating, retrieval and loading |
| `frontend/src/lib/analytics/ga4.test.js` | new — loader behaviour tests |
| `frontend/src/components/AnalyticsBootstrap.jsx` | new — mount point (renders nothing) |
| `frontend/src/components/AnalyticsBootstrap.test.jsx` | new — mount integration tests |
| `frontend/src/CookieBanner.jsx` | records the choice through the shared consent contract |
| `frontend/src/index.js` | mounts the bootstrap |
| `frontend/src/v3/api.js` | analytics settings client functions |
| `frontend/src/v3/ops/SettingsTab.jsx` | Analytics & Integrations section |
| `frontend/src/v3/__tests__/settings-tab-analytics.test.jsx` | new — Admin UI tests |
| `docs/architecture/CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md` | this document |

No database migration, no RLS change, no new table, and no change to any other analytics/marketing surface.

---

## 11. Known limitations

* **Consent withdrawal is not offered.** The existing banner asks once and has no post-choice withdrawal control;
  adding one would be a new consent UI, which is outside this task's boundary. GA4 is therefore loaded only after
  an explicit accept, and a visitor who declines is never contacted, but a visitor who later changes their mind
  cannot currently revoke from the UI.
* **Single-page route changes** rely on GA4's own *enhanced measurement* (a property setting in Google
  Analytics), because custom events are out of scope. No application-side page-view events are sent.
* **The Admin measurement-ID rule is intentionally shape-based** (`G-` plus 4–20 uppercase alphanumerics). It
  rejects obviously invalid values (including `UA-…` and `GTM-…`) but cannot verify that a well-formed ID exists
  in a Google property.
* **The public read is unauthenticated by design.** It exposes only the enabled flag and the Measurement ID —
  both already visible in a page's source when GA4 is loaded — and never any other settings or tenant data.

---

## 12. Deployment checklist

1. Confirm the production frontend deployment sets `REACT_APP_ENVIRONMENT=production`.
2. Confirm development/QA/staging deployments do **not** set it.
3. In CarbonTally Admin → Operations → Settings → Analytics & Integrations, enter the GA4 Measurement ID and
   enable Google Analytics.
4. Accept cookies on the production site and verify `gtag.js` is requested with the configured ID, and that the
   realtime report in the GA4 property receives the page view.
5. Confirm the setting is disabled in non-production environments, or that it has no effect there.
