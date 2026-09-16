# CarbonTally Marketing & Analytics Architecture --- 12--24 Month Plan

**Document type:** OHD implementation specification\
**Purpose:** Define the minimum analytics/marketing architecture
CarbonTally should implement now and the controlled roadmap for the next
12--24 months.

## 1. Executive decision

CarbonTally should use a **privacy-conscious, configuration-driven
Analytics & Integrations architecture**.

### Install now

1.  **Google Analytics 4 (GA4)** --- website/product analytics
    foundation.
2.  A small **Analytics & Integrations** administration area in
    CarbonTally Admin, with provider-specific configuration for GA4.
3.  A configuration model that can accommodate future providers without
    implementing those providers now.

### Add after first paying customers / validated acquisition

1.  **Google Tag Manager (GTM)** --- when multiple marketing/analytics
    tags make centralized tag management worthwhile.
2.  **PostHog** --- when product-usage, funnels, feature adoption,
    experimentation, or deeper product analytics justify it.
3.  **LinkedIn Insight Tag** --- when LinkedIn advertising/campaign
    attribution is actually being used.
4.  **Microsoft Clarity or Hotjar** --- only when UX investigation
    requires it and sensitive CarbonTally application data can be
    reliably excluded/masked.
5.  **Customer-support/onboarding platform** such as Intercom --- when
    customer volume makes in-app support/onboarding operationally
    useful.

### Conditional / do not install by default

-   Meta Pixel: only if Meta advertising becomes an actual acquisition
    channel.
-   Other ad-network pixels (TikTok, Snapchat, etc.): do not install
    unless a concrete, approved business requirement exists.

### Never install by default

-   Unknown/opaque third-party tracking scripts.
-   Cryptocurrency/mining or unrelated telemetry.
-   Tools that capture carbon-accounting inputs, evidence, reports,
    credentials, secrets, or other sensitive application content without
    an explicit approved architecture.
-   Session recording on sensitive authenticated workflows unless data
    masking/exclusion is demonstrably effective.
-   Duplicate analytics systems collecting the same events without a
    defined purpose.
-   Advertising/retargeting pixels merely because they are popular.

------------------------------------------------------------------------

## 2. Architectural principles

1.  **Configuration over hard-coding:** provider IDs/configuration must
    be administrable where practical; no secrets in frontend source.
2.  **Provider isolation:** analytics integrations must not be coupled
    to the carbon calculation engine, FactorMatchingEngine, evidence
    model, disclosure model, report lifecycle, or auditability model.
3.  **Minimal collection:** collect only what is needed for the stated
    business purpose.
4.  **No sensitive data leakage:** never send emissions inputs, evidence
    contents, uploaded-document contents, report contents, credentials,
    tokens, signed URLs, or secrets to analytics providers.
5.  **Environment awareness:** production, staging, and development must
    not accidentally share analytics traffic. Environment separation
    should be handled by deployment/runtime configuration rather than an
    Admin user accidentally enabling production tracking in development.
6.  **Consent/privacy integration:** if CarbonTally has an existing
    consent/privacy mechanism, analytics must respect it. Do not invent
    a parallel consent system as part of GA4 implementation.
7.  **No broad refactoring:** create only the smallest reusable
    integration/configuration layer justified by the current
    requirement.
8.  **Auditability:** administrative changes to analytics configuration
    should use the existing Admin/audit conventions where applicable.
9.  **Fail closed:** missing or invalid provider configuration must
    result in the provider not loading; analytics failure must never
    break CarbonTally.
10. **No analytics dependency for core functionality:** CarbonTally must
    operate normally if every analytics provider is disabled or
    unavailable.

------------------------------------------------------------------------

## 3. Phase plan

### Phase A --- Now

Implement: - GA4 via `gtag.js`. - Admin-controlled GA4 enabled/disabled
setting. - Admin-controlled GA4 Measurement ID. - Conditional loading. -
Validation sufficient to prevent obviously invalid IDs/configuration. -
Existing privacy/consent integration if already available. - Focused
tests. - Minimal documentation.

Do not implement GTM, PostHog, LinkedIn, Meta, Clarity/Hotjar, or
support integrations in this phase.

### Phase B --- After first paying customers

Evaluate based on actual customer acquisition and product behavior: -
GTM if multiple tags/providers are needed. - PostHog if product
analytics gaps exist. - LinkedIn Insight Tag if LinkedIn campaigns are
active. - Clarity/Hotjar if UX research needs session/heatmap
evidence. - Support/onboarding tooling if customer volume warrants it.

Each provider should be introduced through the same Analytics &
Integrations architecture rather than through unrelated one-off code.

### Phase C --- Growth stage

Once acquisition channels and product usage are measurable: - Establish
a documented event taxonomy. - Define a canonical conversion funnel. -
Add only business-critical events. - Separate public marketing-site
analytics from authenticated product analytics where appropriate. -
Establish provider ownership, retention, privacy, and access rules. -
Review analytics data quality periodically.

------------------------------------------------------------------------

## 4. Recommended future conversion funnel

Do not implement this entire event taxonomy now. It is the target model
for later product analytics:

Visitor → Signup → Email verified → Workspace created → First
calculation → First report → Trial activation → Paid conversion →
Retention

Potential future events: - signup_completed - workspace_created -
first_calculation_completed - first_report_generated - trial_started -
subscription_started - subscription_cancelled - report_exported

Events must contain only non-sensitive metadata necessary for the
business purpose. Never include raw carbon activity data, evidence text,
document contents, emission factors, report contents, credentials, or
other sensitive payloads.

------------------------------------------------------------------------

## 5. Admin architecture recommendation

Create a single conceptual area:

**Admin → Analytics & Integrations**

Current provider:

**Google Analytics** - Enabled: ON/OFF - Measurement ID: `G-XXXXXXXXXX`

Future providers may use the same conceptual area, but their actual
settings should not be implemented until authorized.

The architecture should avoid creating five empty database tables or
speculative UI sections solely for future providers.

If the existing Admin Settings system already supports typed
configuration, reuse it.

If a database change is required, make the smallest additive change
consistent with the existing configuration architecture.

Do not create a parallel settings subsystem.

------------------------------------------------------------------------

## 6. GA4 implementation requirements

-   Use Google's `gtag.js` mechanism.
-   Do not hard-code the Measurement ID.
-   Load only when enabled, correctly configured, and permitted by the
    existing privacy/consent mechanism.
-   Analytics must fail safely.
-   Do not collect custom events in this implementation.
-   Do not send sensitive CarbonTally data.
-   Do not expose API secrets or service credentials.
-   Do not add server-side Google Analytics APIs.
-   Do not add a CarbonTally analytics dashboard.
-   Do not alter core application behavior when GA4 is unavailable.

------------------------------------------------------------------------

## 7. Security and privacy boundary

Analytics integrations are an external-data boundary.

The following must never be sent to third-party analytics/marketing
systems: - passwords - authentication tokens - API keys -
service-account credentials - signed URLs - uploaded files - document
text - evidence content - activity quantities - emissions calculations -
emission factors - report contents - customer financial data - private
organization data - personally sensitive information unless separately
approved and legally justified

Use opaque/non-sensitive identifiers only where there is an explicit and
documented reason.

------------------------------------------------------------------------

## 8. Implementation guardrails for OHD

Before modifying anything: 1. Inspect the repository and current Admin
Settings implementation. 2. Inspect existing privacy/cookie/consent
behavior. 3. Inspect current analytics/tracking code, if any. 4. Inspect
git status and identify unrelated in-progress work. 5. Do not reset,
clean, stash, revert, or overwrite unrelated work. 6. Do not touch
Cline's Phase 8 B2 implementation. 7. Do not stage unrelated files.

If the existing architecture cannot support the recommended GA4
configuration without a significant redesign: - stop, - document the
blocker, - propose the smallest safe change, - do not implement
speculative architecture.

------------------------------------------------------------------------

## 9. Testing and acceptance

At minimum verify: - GA4 disabled → `gtag.js` is not loaded. - GA4
enabled + valid Measurement ID → GA4 loads/configures correctly. - GA4
enabled + missing/invalid Measurement ID → GA4 does not load. - Existing
consent/privacy behavior is respected where applicable. - Analytics
provider failure does not break application startup or normal user
workflows. - Admin authorization prevents unauthorized configuration
changes. - Existing Admin Settings functionality remains intact. - No
sensitive CarbonTally data is included in analytics
configuration/events.

------------------------------------------------------------------------

## 10. Git and delivery boundary

For the initial GA4 implementation: - create a focused change set; -
stage only files required for GA4/Admin
configuration/documentation/tests; - do not include Phase 8 B2 or
unrelated work; - inspect the staged diff before commit; - commit with a
focused message; - push only that focused commit if OHD is explicitly
instructed to push.

The final report must list: - changed files, - settings added, - runtime
behavior, - tests and results, - commit hash, - exact files in the
commit, - confirmation that unrelated/Cline B2 work was not committed or
pushed.

------------------------------------------------------------------------

## 11. Decision summary

**NOW:** GA4 + minimal Admin configuration architecture.

**AFTER FIRST PAYING CUSTOMERS:** decide on GTM, PostHog, LinkedIn, UX
analytics, and customer-support tooling based on actual needs.

**CONDITIONAL:** Meta Pixel and other advertising pixels only when the
corresponding advertising channel is actually used.

**NEVER BY DEFAULT:** uncontrolled third-party tracking, sensitive-data
collection, opaque scripts, unnecessary duplicate analytics, and session
recording of sensitive CarbonTally workflows without reliable masking.

This document is a roadmap and architectural boundary. It does not by
itself authorize implementation of future providers. Only the currently
specified GA4 work is in scope for the initial OHD task.
