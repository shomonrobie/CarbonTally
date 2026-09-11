# CarbonTally — Cookie Policy (Draft / Update)

**Document status:** DRAFT update for review by qualified legal counsel and the Product Owner.
**Version:** 0.1 (draft update)
**Effective date:** [EFFECTIVE DATE — TO BE INSERTED]
**Last updated:** 24 August 2026 (draft)
**Document owner:** [TO BE ASSIGNED]
**Supersedes:** `frontend/src/CookiePolicy.jsx` (once finalised and published) and the current `/cookies` page.
**Basis:** Product audit of `frontend/public/index.html`, `frontend/src`, and `website_candidate/frontend` confirmed **no third-party advertising, analytics, or marketing cookies or scripts** are deployed.

> **Drafting note:** The substance of the existing `/cookies` page is accurate and is retained. This update (1) aligns the Cookie Banner copy, which currently implies cookies are set when they are not; (2) adds version/change-control metadata; and (3) records the obligations that apply before any non-essential cookies are introduced.

---

## 1. What we use

1.1 **No third-party cookies.** The CarbonTally public website currently deploys no third-party advertising, analytics, or marketing cookies, and no third-party tracking scripts. This was verified in the current product audit (24 August 2026).

1.2 **Browser local storage (not a cookie).** The authenticated platform stores your session in browser local storage so that you can remain signed in. The Cookie Banner also records your banner preference (`cookieConsent`) in local storage. This data stays in your browser and is not used for tracking.

1.3 **Essential cookies.** The public website itself sets no essential cookies at this time. Server-side session handling for the authenticated platform relies on Supabase Auth sessions (stored in browser storage) rather than first-party session cookies set by the website.

## 2. The cookie banner

2.1 The current banner text — "We use cookies to enhance your experience. By continuing to visit this site, you agree to our use of cookies." — **does not accurately describe the site**, which sets no cookies. `[PRODUCT GAP — banner copy to be updated]`

2.2 Recommended replacement copy (for the engineering change when approved):

> "This website sets no tracking cookies. We use browser local storage to keep you signed in to the platform. See our Cookie Policy for details."

2.3 If the banner is retained purely as a preference notice, its accept/decline buttons should either be removed or repurposed to record a documented preference only when there is a legitimate purpose (e.g., if non-essential features are later added).

## 3. Managing cookies and storage

3.1 You can clear cookies and browser storage at any time through your browser settings. Clearing authentication storage will sign you out of the platform.

3.2 Because no non-essential cookies are set, no consent is currently required for cookie-based processing under PECR/UK GDPR. `[LEGAL REVIEW]`

## 4. Future changes — obligations before adding cookies

4.1 If CarbonTally adds analytics, advertising, or any non-essential cookies or third-party tracking in future, the following must happen **before** deployment:
- update this Cookie Policy (and the Privacy Policy) to describe the new cookies and their purposes;
- implement appropriate consent capture (consent banner that accurately describes the cookies and honours accept/decline choices) where required by the Privacy and Electronic Communications (EC Directive) Regulations 2003 (as amended) and the UK GDPR;
- record consent evidence where required; and
- update the third-party processor register if any new provider processes personal data.

## 5. Contact

Cookie enquiries: email **[PLACEHOLDER: hello@carbontally.co.uk — CONFIRM]**.

---

## Change control

| Version | Date | Change summary | Owner |
|---|---|---|---|
| 0.1 | 2026-08-24 | Draft update: verified no cookies/trackers; flagged banner-copy mismatch; added future-changes obligations and change control | [OpenHands audit draft] |
