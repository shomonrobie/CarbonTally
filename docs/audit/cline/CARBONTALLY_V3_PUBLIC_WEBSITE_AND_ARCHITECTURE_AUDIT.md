# CarbonTally V3 Public Website & Architecture Audit

**Status:** AUDIT ONLY — read-only review. No application source, schema, RLS, API, migration, route, or content was modified during this task. The only repository addition is this report.

**Date:** 2026-08-24
**Scope:** Public website, commercial messaging, pricing, legal pages, SEO, frontend architecture, backend architecture, directory structure, tests, configuration, security, performance.
**Live-site caveat:** `https://carbontally.co.uk/` serves a client-rendered Create-React-App shell (the raw HTML contains only *"You need to enable JavaScript to run this app."*). `/pricing` and `/about` return HTTP 404 at the server level because they are client-side routes. Live content was therefore audited from the repository implementation (`frontend/src`), with the live shell confirming the deployed architecture. No live-site finding is invented.

---

## 1. Executive Summary

CarbonTally V3 has completed D32–D37 and is a technically mature pre-production commercial platform (self-service onboarding D35, private storage D32, evidence traceability D33, complete commercial billing foundation D37). **The public website has not caught up with the product.** It still presents CarbonTally primarily as a *limited beta* with a *fake waitlist form*, while the product now supports self-service signup and configurable commercial plans.

Key findings, in severity order:

1. **P0 — Committed credential:** `tools/carbon_data_factory/deeepseek_api.txt` (tracked in git) contains what appears to be a live third-party LLM provider API key (`sk-…`). Revoke/rotate the key and purge the file from history. (Details in §25/§26 — value intentionally not reproduced.)
2. **P1 — The Pricing page is effectively unreachable and the Privacy Policy is shadowed.** There is **no `/pricing` route**. Header/footer "Pricing" links point to `/PricingPage` (no such route → redirect to `/`); `BulkUpload.jsx` navigates to `/pricing` (no route). A **duplicate `/privacy` route renders `<PricingPage/>`**, which in React Router shadows the real `<PrivacyPolicy/>`. A visitor clicking "Privacy Policy" gets the pricing page, and can never reach the pricing page through normal navigation.
3. **P1 — Fake waitlist / broken CTA.** The homepage and pricing CTAs ("Request Beta Access", "Start processing your data", every plan button) open a client-side modal whose submit handler is a `setTimeout` simulation. **No email is persisted anywhere.** The backend waitlist endpoint (`backend/routes/waitlist.py`) is a `pass` stub. Lead capture is silently discarded.
4. **P1 — Legal pages are not launch-safe.** Privacy Policy publishes literal placeholders (`[Your Company Address]`, `[Your Company Number]`, `[Your Phone Number]`); Terms claim "monthly or annual" billing (annual billing does not exist); all three legal pages compute their "Last updated" date client-side (always today); the Cookie Policy describes Google Analytics / HubSpot / LinkedIn / Google Ads cookies that are **not implemented anywhere** in the codebase.
5. **P1 — About page contains fabricated team members.** Three team profiles (CTO, Head of Carbon, Product Lead) are literally labelled "Fictional" in the source comments and use auto-generated avatars from an external service. This is legally sensitive if it remains public. "Trusted by businesses across the UK" and "Start Free Trial" (no free trial exists; the button sends users to `/dashboard`, which requires login) are unsupported.
6. **P2 — Beta transition.** Public beta messaging ("Limited Beta Access", "Join our beta program", "🧪 Beta" header badge) is now misleading: D37 configured the commercial plans, the D35 self-service signup is live, and the beta flow is only needed as an administrative invite mechanism at `/beta/signup`.
7. **P2 — SEO is effectively default.** Stock CRA `<title>CarbonTally</title>` and meta description *"Web site created using create-react-app"*; no Open Graph, Twitter, canonical, sitemap, or structured data; client-rendered SPA with no prerendering.
8. **P2 — Directory/repository hygiene.** The repo root is polluted with ~60 scratch `_*.txt` / `tmp_*.txt` / `probe_out*.txt` files (untracked but on disk), tracked dead files (`backend - backup.zip`, `App copy.js`, `LandingPage copy.jsx`, `main copy.py`, `requirements copy.txt`, `config copy.toml`, mock CSVs, `v1.9.txt`, zips inside `docs/`), a separate `admin/` dashboard app and `carbon-tally-ui-demo/`, an abandoned `prisma/`+Snaplet seed experiment, a stray root `src/` Python package, and a root `requirements.txt` with invalid `=>` syntax.
9. **Good.** The engineering core is strong: the D37 billing layer (services/data/domain/api) has clean responsibilities and dependency direction; `frontend/src/v3` feature folders are coherent; the API client (`v3/api.js`) is disciplined (timeouts, friendly errors, server-authoritative post-login routing); billing RLS is deny-by-default; migrations are additive and idempotent; the modern test layout (`tests/unit/api|domain`, `tests/integration`) is good.

**Overall rating:** the product engineering is **Level B−** while the public website and repository hygiene are **Level C−**. The site is safe to keep developing, but a coordinated content + beta-transition + hygiene task (D38 or equivalent) should be authorised before public commercial launch. Scores and the full recommendation are in the final sections of this report.

---

## 2. Current Product Positioning

Approved strategic positioning (context):

> *"CarbonTally is the carbon-data processing layer that turns messy source data into structured, mapped, calculated and traceable emissions data."*

Audience classes: **Direct Customers**, **Consultants**, **Processing Entities**, and **B2B carbon-reporting/accounting platforms**.

**Where the site aligns with the positioning:**
- Homepage hero: *"Turn messy carbon data into traceable emissions"* + the messy-data pipeline (Extract → Normalize → Map → Calculate → Validate → Preserve evidence) is on-message.
- Traceability section ("Know where every number came from"; "Where did this emission come from?") communicates the core differentiator strongly.
- "Built for Platforms" section addresses the B2B/processing-layer story directly.
- Pricing FAQ explicitly answers *"Is CarbonTally a carbon-reporting platform?"* — "primarily a carbon-data processing and management platform … can work alongside carbon-accounting and reporting platforms."

**Where the site diverges:**
- The About page and Terms still frame the company narrowly as *"carbon accounting software for UK businesses"* with an SECR focus, a subset of the approved positioning that does not match the wider customer types.
- The beta framing ("Limited Beta", "all features are ready") undermines commercial credibility and contradicts the existence of live self-service signup and a configured commercial catalogue.
- Footer "Solutions" links (SECR Reporting, ESG Compliance, Supply Chain, Real Estate, Manufacturing) imply a vertical product family that does not exist as separate offerings.

---

## 3. Public Website Inventory

### 3.1 Routes defined in `frontend/src/App.js` (public surface)

| Route | Component | Notes |
|---|---|---|
| `/` | `LandingPage` | Beta banner + fake waitlist |
| `/login` | `Login` | Supabase password login |
| `/privacy` | `PrivacyPolicy` | **Shadowed** by the duplicate `/privacy` → `PricingPage` route below |
| `/privacy` (duplicate) | `PricingPage` | **Defect** — renders the pricing page at the privacy URL |
| `/cookies` | `CookiePolicy` | |
| `/terms` | `TermsPage` | |
| `/about` | `AboutUs` | Fictional team, stale positioning |
| `/carbon-reduction-plan` | `CarbonReductionPlan` | |
| `/auth/callback` | `AuthCallback` | Supabase email-confirm landing |
| `/signup` | `SelfServiceSignup` | D35 self-service journey |
| `/beta/signup` | `BetaSignup` | Invite-code flow (admin use) |
| `/beta-login` | `BetaLogin` | Legacy beta login |
| `/glossary` | `Glossary` | |
| `/auth/magic` | `MagicLink` | Still routes to `/beta-login` |
| `/dashboard/*` (x2) | `Navigate→/home` **and** `ProtectedRoute+Dashboard` | Duplicate route definitions |
| `*` | `Navigate→/` | Catch-all |

**Missing route:** `/pricing` — referenced by `AppHeader` (`/PricingPage`), `AppFooter` (`/PricingPage`), and `BulkUpload.jsx` (`/pricing`), but defined nowhere.

### 3.2 Unreachable / dead public components
`DataSecurity.jsx`, `PDFIngestionPortal.jsx`, `RecentProcessedData.jsx` are unused/unreachable components still imported into the bundle. There is **no Contact page** and no contact route; every footer "Contact" link is `href="#"`.

### 3.3 Navigation
- Header nav: Features, Pricing (`/PricingPage` — broken), About, Carbon Plan.
- Footer: Product (Features, Pricing-broken, Integrations/#, Changelog/#, Roadmap/#), Solutions (all `#`), Resources (Blog/#, Documentation/#, Help Center/#, Glossary, Community/#), Company (About/#, Careers/#, Contact/#, Carbon Reduction Plan, Privacy Policy, Terms).
- **Dead-link inventory:** Integrations, Changelog, Roadmap, SECR Reporting, ESG Compliance, Supply Chain, Real Estate, Manufacturing, Blog, Documentation, Help Center, Community, About, Careers, Contact, and both social links (`#`). 16 of ~22 footer links are dead anchors.

### 3.4 Deployment topology
- `vercel.json`: rewrites `/admin/*` → a separate `admin/` app; all other paths → `/frontend/index.html`. Root `package.json` ("carbon-ledger-monorepo") builds `frontend/` + `admin/` and copies them into `public/` and `public/admin/`.
- Backend on Render (`https://carbontally-api.onrender.com` referenced in `Glossary.jsx`).
- Supabase live project URL hard-coded in `frontend/src/supabaseClient.js`.

---

## 4. Homepage Audit

Component: `frontend/src/LandingPage.jsx` (655 lines).

| Item | Finding |
|---|---|
| Hero | H1 *"Turn messy carbon data into traceable emissions"* — **strong, on-positioning**. Subtext explains processing of invoices/PDFs/spreadsheets/CSVs with evidence. |
| Who it is for | Implied (organizations and platforms sections), but the hero does not name customer types; the "Built for Platforms" section does. |
| What problem it solves | Messy data → structured, calculated, traceable emissions. Clear. |
| Why different | Traceability/evidence and human-in-the-loop are clearly communicated. |
| Next step | "Request Beta Access" / "Start processing your data →" — both open the **fake waitlist modal**. The single most important CTA is broken. |
| Beta framing | Beta banner *"Limited Beta Access — All features are ready! Join our beta program"*, hero badge *"🧪 Limited Beta — All Features Available"*, header *"🧪 Beta"* badge. **Obsolete** relative to D35/D37. |
| Waitlist modal | Submits via `setTimeout` simulation. "You're on the list!" — the email is discarded. |
| Feature grid | 9 "Ready" cards. Several claims require verification: "certified Scope 1, 2, and 3 disclosures", "Compliant Auditor & Boardroom PDF Reports … SECR, CSRD, ESRS E1, ISSB", "24-hour turnaround", "Tesseract OCR", "AES-256 / SOC 2 / SSO" (§12). |
| Platform section | Good B2B/processing-layer pitch; CTA opens the fake waitlist. |
| CTA section | "Start processing your data →" (opens waitlist) + "Full features. Limited spots. No credit card required." |
| Security claim | "AES-256 at rest and in transit. SOC 2 compliant infrastructure with SSO, RBAC, audit logs, GDPR-compliant" — partially verified in-app; infra claims need hosting-provider confirmation. |

**Verdict:** the top of the page is on-message, but the page *as a whole* still sells a beta, and every conversion path is a dead end.

---

## 5. Beta Program Audit

### 5.1 Occurrences

| Location | Customer-facing? | Type |
|---|---|---|
| `LandingPage.jsx` — beta banner, hero badge, waitlist modal, CTA copy | Yes | Marketing |
| `PricingPage.jsx` — same banner/modal/CTA | Yes | Marketing |
| `components/AppHeader.jsx` — `isBetaMode=true` default, "🧪 Beta" badge, "Request Beta Access" button | Yes | Header |
| `/beta/signup` (`BetaSignup.jsx`) | Yes (invite-only) | Flow |
| `/beta-login` (`BetaLogin.jsx`) | Yes | Flow |
| `/auth/magic` (`MagicLink.jsx`) — routes to `/beta-login`, toast "Welcome to CarbonTally Beta!" | Yes | Flow |
| `SelfServiceSignup.jsx` — "Have an access code? Use your beta access code" | Yes | Link |
| `backend/routes/waitlist.py` — stub endpoint | No | Backend |
| Terms/Privacy/Cookie pages | No beta references | — |
| `frontend/public/manifest.json` — "Carbon Accounting, Simplified." | Yes | PWA metadata |

### 5.2 Assessment
1. **Where it exists:** marketing surfaces, header, three auth flows, one backend stub.
2. **Customer-facing:** yes — it is the *primary* public CTA.
3. **Technically required?** Only `/beta/signup` + `beta_access_codes` remain a real (admin/invite) mechanism. The marketing waitlist has no persistence and is not required.
4. **Conflict with current product:** yes — D35 made signup self-service; D37 configured commercial plans; the site still says "limited beta", suppressing the `/signup` journey.
5. **Keep internally:** `/beta/signup` and `beta_access_codes` as an administrative invite path; remove public links except a subtle "Have an access code?" note on login/signup pages.
6. **Remove publicly:** the beta banner, hero badge, header "🧪 Beta" badge, "Request Beta Access" buttons and the waitlist modal (or replace with a **real** persisted waitlist endpoint if the PO wants pre-launch capture).
7. **Recommended replacement CTA:** "Get Started" / "Create account" → `/signup` (primary); "View Pricing" → working `/pricing` (secondary); "Talk to us / Book a demo" → new Contact page (tertiary). See §11.

---

## 6. Pricing Audit

Component: `frontend/src/PricingPage.jsx` (831 lines), compared against D37 plan/config seed (`20260824020000_d37_0_…`, `20260824030000_d37_master_…`).

### 6.1 Plan values — match
| Plan | Pricing page | D37 DB seed | Match |
|---|---|---|---|
| Starter | $49 / 100 credits | v2: 49 USD/month, 100 credits, 3 seats | ✅ |
| Professional | $149 / 500 credits | v1: 149 **GBP**/month, 500 credits | ⚠️ currency |
| Business | $399 / 2,000 credits | v2: 399 USD/month, 2,000 credits, 25 seats | ✅ |
| Enterprise | Custom | — (no seeded row) | ✅ |
| Assisted | $0.99 / $1.99 / $3.99 per doc | simple/standard/complex 0.99/1.99/3.99 USD | ✅ (missing "Exceptional — quote" tier) |
| Credit classes | Simple 1, Standard 2, Complex 4, Exceptional assessed | same values | ✅ |

### 6.2 Content-quality findings
1. **Currency inconsistency in the source of truth itself:** Professional is seeded in **GBP** while Starter/Business are **USD**. The pricing page displays `$` for all plans. Fix the DB config (P1); keep prices in config, not code.
2. **Annual toggle "Save 20%" is not real.** D37 plans are all `billing_interval = 'month'`; no annual billing exists anywhere in the engine. The toggle only changes displayed numbers client-side. Remove it or defer until annual billing is implemented. **P1 (misleading commercial claim).**
3. **Stale disclaimer:** *"Pricing shown is a proposed baseline and may change before commercial launch."* D37 now has versioned, admin-configurable plans. **P2.**
4. **Plan feature claims vs DB config:** Starter has `assisted_processing_available = FALSE`, `managed_processing_available = FALSE`, `api_access = FALSE`; Business has all TRUE. The page lists "Assisted Processing access" under Professional and "Assisted/Managed Processing access" under Business — consistent, but the page never states Assisted/Managed availability is **plan-gated**. **P2.**
5. **"Priority processing" / "Priority support"** (Professional/Business) and **"Processing priority"** have no matching field in the plan seed — unverified soft claims. **P2 (verify or soften).**
6. **Credits are explained well:** "A CarbonTally Credit represents a unit of automated processing entitlement" + complexity table + structured-data bands. **This is the correct public vocabulary.** Structured bands are honestly labelled "draft … may be refined". ✅
7. **Rollover:** FAQ says *"Our planned model allows eligible paid credits to roll over"* — D37 `credit_policy.rollover.enabled = TRUE` is already live. "Planned" is stale; say "available, terms shown before purchase". **P2.**
8. **Storage:** page says "Basic/Extended/More document storage" with no numbers; FAQ says additional storage can be purchased. D37 seeds Starter 20 GiB / Business 500 GiB. Public numbers are **not required** — qualitative language is fine. **P3.**
9. **Standard (non-credit) commercial mode** appears only in the FAQ ("supports both a Credit-Based and a Standard commercial model"). Given STANDARD-mode per-item complexity is still a PO decision, keeping it vague is **correct**. ✅
10. **Example cost** (10×0.99 + 4×1.99 + 1×3.99 = $21.85) is arithmetically correct. ✅
11. **All plan CTAs open the fake waitlist** instead of `/signup`. **P1.**

### 6.3 What customers actually need to know (recommendation)
- Plan prices + included credits + seats.
- What a credit is, and that complexity determines consumption (1/2/4).
- Assisted ($/document) and Managed (batch/quote) exist as upgrades; availability is plan-gated.
- No separate calculation charge.
- Rollover exists (terms shown before purchase).
- Payment provider/tax not yet enabled — use "billing is activated on your account" language rather than pretending a checkout exists.

---

## 7. About Us Audit

Component: `frontend/src/AboutUs.jsx` (253 lines).

| Item | Finding |
|---|---|
| Company identity | Header: "About CarbonTally (UK) Limited". **Inconsistent** with Terms/Privacy/Footer/Cookies ("CarbonTally Ltd") and with `legal@carbontally.com` / `dpo@carbontally.com` emails (site domain is carbontally.co.uk). |
| Fictional team | Three profiles — CTO James Mitchell, Head of Carbon Sarah Okafor, Product Lead Aisha Patel — are **marked "Fictional" in source comments** and use `ui-avatars.com` generated images. **P1 legally sensitive / unverifiable.** |
| Founder story | "Founded in 2024 by Shomon Robie … algorithmic trading systems at LakshmiFX" — a real claim that must be confirmed by the PO before it stays public. |
| Social proof | "trusted by businesses across the UK" — **unsupported**. |
| Mission | "make UK carbon accounting effortlessly simple…" — narrower than the approved processing-layer positioning; fine as a mission statement but should be reconciled. |
| CTA | "Start Free Trial" → `window.location.href='/dashboard'`. **No free trial exists**; `/dashboard` redirects to `/home`, which requires login. **P1 misleading CTA.** |
| External dependency | `ui-avatars.com` runtime image calls — third-party privacy/availability surface. |
| Regulations | Mentions SECR / PPN 06/21 / UK Sustainability Reporting Standards — SECR is supported; the broader standards claims live on the homepage feature grid (§12). |

---

## 8. Terms & Conditions Audit

Component: `frontend/src/TermsPage.jsx` (84 lines).

1. **"Last updated: {new Date()}"** is computed client-side → the page always shows today's date. Misleading. **P1.**
2. **§7 Payment Terms:** "billed in advance on a monthly or annual basis" — **annual billing does not exist** and no payment provider is integrated (D37 hard stop). "All fees are non-refundable except as required by law" is premature without a payment provider and chargeback framework.
3. **Missing commercial content:** no definition of credits, credit consumption, complexity, rollover, Assisted/Managed processing, storage limits/retention, orders, payment records, or suspension-for-non-payment. The Terms must be rewritten against the D37 commercial model when payment is enabled.
4. **§8 Termination:** "30 days' written notice" — invented term.
5. **§10 Governing law:** England and Wales — reasonable; PO should confirm courts/London.
6. **§5 Intellectual property:** "owned by CarbonTally Ltd" — company-name inconsistency (§7).
7. **Absent:** acceptable use for Processing Entities, processing of third-party documents, AI/human extraction, liability for emissions figures. All **require professional legal review** before launch.
8. **VAT/tax:** absent (correctly — tax integration is deferred; do not invent VAT language).

**Action:** professional legal review + rewrite aligned to D37 architecture; fix identity and dynamic dates. **P1.**

---

## 9. Privacy / Cookie / GDPR Audit

Components: `PrivacyPolicy.jsx` (144), `CookiePolicy.jsx` (93), `CookieBanner.jsx` (45).

1. **Published placeholders (P1):** `[Your Company Address]`, `[Your Company Number]`, `[Your Phone Number]` appear on the live privacy page.
2. **Dynamic dates** on all three legal pages (always "today"). **P2.**
3. **Processors not disclosed:** the policy names generic "hosting providers, email delivery services, analytics providers, and payment processors" but does not name **Supabase, Vercel, Render, Resend**, any AI/LLM provider, or Processing Entities that handle customer documents. For a GDPR-heavy product this is a substantive gap. **P1 for legal review.**
4. **Cookie Policy describes cookies that do not exist:** Google Analytics, HubSpot, LinkedIn Insight, Google Ads are listed — **no analytics/tracking scripts exist anywhere** in the codebase (verified by search). The only consent UI is a minimal accept/decline banner storing a flag in `localStorage`; the policy's "customise which non-essential cookies you permit" has no corresponding UI. **P1 content accuracy.**
5. **Data retention:** "6 years to comply with HMRC and SECR requirements", "marketing data … 5 years after last interaction" — invented specifics without evidence; legal review required. **P1/P2.**
6. **Rights list** (access/rectification/erasure/restriction/portability/object/withdraw) — standard and complete. ✅
7. **CookieBanner** is wired in `App.js` and functional (accept/decline + localStorage). It runs on public pages too. Minor copy issue: banner says "We use cookies… By continuing… you agree", but the site currently sets no third-party cookies at all. **P3.**

---

## 10. Customer Journey Audit

Intended journey: Discover → Sign up → Create/adopt org → OWNER → Upload → Process → Map → Calculate → Evidence → Export.

| Step | Current site behaviour | Verdict |
|---|---|---|
| Discover | Landing page explains the product well | ✅ |
| Convert | Primary CTA → **fake waitlist** | ❌ P1 |
| Sign up | `/signup` (D35 self-service) exists and is solid | ✅ but hidden behind beta CTAs |
| Email confirm | `/auth/callback` handles confirmation | ✅ |
| Onboarding | `/onboarding` + OnboardingWizard (D35) | ✅ |
| Login | `/login` (password) + magic-link page | ✅ |
| Pricing | Unreachable (`/PricingPage`/`/pricing` broken; only via `/privacy` bug) | ❌ P1 |
| Beta flow | `/beta/signup` invite-code path | ⚠️ keep internal |
| Post-login routing | Server-authoritative `resolvePostLoginPath` (org→/home, staff→/ops, consultant→/consultant, new→/onboarding) | ✅ strong |
| Billing | In-app `/billing` customer page + `/ops` commercial tab | ✅ (payment disabled by design) |
| Contact | No contact page; footer `#` links | ❌ P2 |

**Terminology friction:** the journey mixes "beta", "request access", "start free trial", and "create account" across surfaces; a visitor cannot tell which path to take.

---

## 11. CTA Audit

Current CTAs (all mapped):

| CTA | Surface | Target | Verdict |
|---|---|---|---|
| "Request Beta Access" | Header, landing, pricing, modals | Fake waitlist | Remove / replace |
| "Start processing your data →" | Landing CTA section | Fake waitlist | Replace with /signup |
| "Join our beta program" | Beta banners | Fake waitlist | Remove |
| Plan buttons (Start with Starter / Choose Business / Talk to CarbonTally…) | Pricing | Fake waitlist | Replace with /signup (or /contact when available) |
| "Request a Managed Batch" | Pricing managed tab | Fake waitlist | Replace with contact/quote form |
| "Start Free Trial" | About | `/dashboard` (login required) | Remove or make a real trial |
| "Sign in" / "Create Account" | Header (logged-out uses beta button), Login, Signup | Real flows | Keep — make primary |
| "Talk to us about integration" | Landing platform section | Fake waitlist | Real contact |
| "Use your beta access code" | Signup page | `/beta/signup` | Keep (admin path) |

**Recommended hierarchy:**
1. Primary: **"Get Started" / "Create account" → `/signup`**.
2. Secondary: **"View Pricing" → `/pricing`** (once the route is fixed).
3. Tertiary: **"Talk to us" / "Book a demo" → real contact page** (enterprise/managed/consultant CTAs).
4. Login stays in the header for returning users.

---

## 12. Product Messaging Audit

| Message | Status |
|---|---|
| Processing layer / "messy data → structured, mapped, calculated, traceable" | ✅ Clearly communicated (hero, pipeline, pricing hero, FAQ). |
| Traceability / "Where did this emission come from?" | ✅ Strong (dedicated sections, evidence record). |
| Human fallback (automation → human extraction) | ✅ "Human processing when automation isn't enough" + Processing Entity network. |
| Self-Service / Assisted / Managed workflow | ✅ Pricing tabs; **weakly linked from the homepage** (homepage mentions human processing but not the three-mode workflow explicitly). **P2: add a "How it works" section or page.** |
| Managed Processing | ⚠️ One card on pricing + one homepage feature card; deserves homepage placement and/or a dedicated page (§14). |
| Consultant multi-client | ✅ Pricing consultant section + platform section; in-app `/consultant` exists. |
| B2B processing-layer (platforms) | ✅ "Built for Platforms" + "Your platform. CarbonTally underneath." |
| No separate calculation charge | ✅ FAQ; not on homepage (fine). |
| Beta/early-access | ❌ Contradicts current product (§5). |
| "carbon accounting / SECR" general framing (About, Terms, footer Solutions) | ⚠️ Undersells the platform; inconsistent with processing-layer positioning. |
| "certified Scope 1, 2, and 3 disclosures", "SECR, CSRD, ESRS E1, ISSB" | ⚠️ Requires evidence — D30/D31 reporting exists, but "certified" and the specific standards need PO/domain-expert verification. |
| "SOC 2 / SSO / AES-256" | ⚠️ Infrastructure claim requiring provider confirmation. |
| "24-hour turnaround" (managed ops) | ⚠️ Operational claim not backed by an SLA implementation. |
| "Full features. Limited spots. No credit card required." | ⚠️ "No credit card required" is true (no payment provider); "Limited spots" is unverifiable. |
| "Pricing … may change before commercial launch" | ❌ Stale vs D37 configurable plans. |

---

## 13. Assisted Processing Audit

Current public explanation (pricing tab):
- Tiers Simple $0.99 / Standard $1.99 / Complex $3.99 per document; **no "Exceptional — quote" tier** (it exists in D37 config as `exceptional → quoted`).
- Copy: "CarbonTally handles documents that need human assistance"; example estimate with correct math; "You review the estimate and decide whether to proceed" — matches the D37 customer approval flow (estimate → approve → idempotent credit charge). ✅
- Human-fallback messaging is covered on the homepage.

**Recommendation (P2):** add the "Exceptional — quote" tier; keep "CarbonTally determines the processing complexity" (already stated); keep the customer-approval language; confirm whether assisted items consume credits or are charged as per-document fees before publishing any consumption claim.

---

## 14. Managed Processing Audit

Current public explanation (pricing tab): "On-Demand Managed Batch" card ("You upload the documents. We manage the rest.") + Enterprise Managed Processing card + one homepage feature card ("Premium Managed Back-Office Operations … batch-upload up to 50 documents … 24-hour turnaround").

**Assessment:** the messaging exists but is thin, and Managed Processing is one of CarbonTally's strongest differentiators and its highest-touch commercial product. Recommendation **P2:** give Managed Processing homepage placement (a dedicated section already half-exists via the "Premium Managed Back-Office" card) and optionally a dedicated page; keep pricing as quote-based ("we'll agree the workflow, volume, service requirements and commercial terms"). The "24-hour turnaround" claim needs PO/ops sign-off or removal.

---

## 15. Storage Messaging Audit

Claims found:
- Pricing plan features: "Basic document storage" / "Extended document storage" / "More document storage" / "Enterprise storage".
- FAQ: "Basic storage is included with your plan. Additional storage can be purchased when your document library grows."
- Homepage: "Source-document access" (feature), "Your source data stays connected".

D37 reality: `billing_storage_usage` metering + per-plan storage config (Starter 20 GiB, Business 500 GiB included), overage charged when exceeded (configurable).

**Assessment:** public claims are **qualitative and not misleading**, but the FAQ statement "additional storage can be purchased" implies a purchase path that does not exist yet (payment disabled). **P2:** soften the FAQ ("additional storage will be available") or implement purchase when payments land. No numeric limits are required publicly.

---

## 16. SEO Audit

Evidence: `frontend/public/index.html` (default CRA), `robots.txt`, `manifest.json`, SPA-only rendering.

| Item | Status |
|---|---|
| `<title>` | "CarbonTally" (default) |
| Meta description | **"Web site created using create-react-app"** (default) |
| Per-route titles/descriptions | None (no head manager) |
| Canonical URLs | None |
| Open Graph | None |
| Twitter cards | None |
| Structured data (JSON-LD) | None |
| Sitemap | None (robots.txt has no `Sitemap:` entry) |
| robots.txt | `User-agent: * / Disallow:` (allows all; no sitemap) |
| Semantic HTML | Reasonable (sections, h1/h2/h3, ul) |
| Image alt text | Present on avatar images; visual sections use emoji |
| Internal linking | **Broken:** Pricing links (`/PricingPage`, `/pricing`), dead footer anchors |
| URL structure | Client routes fine, but `/privacy` renders pricing (duplicate), `/PricingPage` is dead |
| Indexability | Client-rendered SPA — crawlers see only the shell + default meta; Vercel serves `index.html` for all routes |
| Duplicate content risk | `/privacy` (pricing) vs intended privacy — same URL ambiguous |
| Beta/obsolete pages | `/beta-login`, `/beta/signup` are public and indexable; beta copy dominates meta-visible text |

**Recommendation (P2, P1-for-launch):** real titles/descriptions (per-route), OG/Twitter/canonical, `sitemap.xml`, fix robots, JSON-LD Organisation/SoftwareApplication; consider prerendering or a small static marketing layer (e.g. `react-snap`-style prerender) — proportionate at this scale, no framework migration required.

---

## 17. Content Consistency Audit

Terminology matrix across the repo:

| Term | Usage | Consistency |
|---|---|---|
| CarbonTally | Standard everywhere | ✅ |
| Carbon Tally | Not found in public UI | ✅ |
| carbon accounting | About mission, footer, Terms §2, manifest name "Carbon Accounting, Simplified." | ⚠️ overused vs processing-layer positioning |
| emissions reporting | Homepage features ("auditor-ready reports"), Terms | ⚠️ product is primarily processing |
| credits / processing units | Pricing: "CarbonTally Credits"; structured-data table uses **"Processing units"** | ⚠️ two terms for related concepts — unify on "credits" (D37 config uses `structured_data_units`) |
| tokens / documents | "tokens" not used; "documents" used for assisted pricing | ✅ (recommend: avoid "documents" as a billing unit except assisted per-document fees) |
| beta / beta program / early access | See §5 | ❌ stale |
| customer / organization / client | In-app: customer + organization; consultant UI uses "clients"; pricing uses "customer organizations" | ⚠️ acceptable; define in glossary |
| consultant / processing entity | "Processing Entity network" (homepage), "consultants" (pricing) | ✅ differentiated correctly |
| managed / assisted processing | Consistent across pricing tabs and FAQ | ✅ |
| subscription | FAQ "when you subscribe"; Terms "subscription fees" | ⚠️ no purchase path yet — keep provisional |
| CarbonTally Ltd vs CarbonTally (UK) Limited | Footer/Terms/Privacy/Cookies = "CarbonTally Ltd"; About = "CarbonTally (UK) Limited"; legal emails use `carbontally.com`, site domain `carbontally.co.uk` | ❌ inconsistent identity + domain |

**Recommended single public vocabulary:** CarbonTally Credit (unit of automated processing entitlement); Document (input file); Assisted Processing (per-document human-assisted, quoted by complexity); Managed Processing (batch, quote); Subscription (monthly plan); Plan (Starter/Professional/Business/Enterprise); Organisation (customer entity); Client (a consultant's customer organisation); Processing Entity (external processing operator).

---

## 18. Frontend Directory Structure Audit

Current (`frontend/src`):

```
src/
├── App.js                     (2,113 lines — routes + providers + legacy layout logic)
├── index.js / App.css / index.css / reportWebVitals / setupTests / logo.svg
├── supabaseClient.js          (hard-coded live URL + publishable key fallback)
├── LandingPage.jsx, PricingPage.jsx, AboutUs.jsx, TermsPage.jsx,
│   PrivacyPolicy.jsx, CookiePolicy.jsx, CookieBanner.jsx,
│   BetaSignup.jsx, BetaLogin.jsx, SelfServiceSignup.jsx, Glossary.jsx,
│   CarbonReductionPlan.jsx, Login.js, MagicLink.jsx, AuthCallback.js,
│   OnboardingPage.jsx, OnboardingWizard.jsx, ... (~30 flat files)
├── components/                (AppHeader/AppFooter/DashboardSummary/... + chat/)
├── context/                   (RealtimeContext, ReferenceDataContext)
├── css/                       (flat 22 files, incl. lp2.css, pricing_page.css)
├── hooks/  lib/  services/  images/
├── v3/                        (api.js ~700 lines, utils.js, v3.css,
│    customer/ ops/ admin/ consultant/ reports/ components/ __tests__/)
└── App copy.js / App copy.css / LandingPage copy.jsx (dead copies)
```

**What is good:**
- `v3/` is a coherent feature-vertical structure (customer/ops/admin/consultant/reports) with a shared API client and shared components (`V3Layout`, `RoleRoute`, `StateViews`). This is the right pattern.
- `context/` separation for auth-adjacent state is fine.
- Tests colocated in `v3/__tests__/`.

**What is non-standard / should change (P2, staged):**
1. **Monolithic `App.js` (2,113 lines):** routes + providers + inline layout + legacy dashboard. Split route tables per area (public/auth/ops/consultant) and move legacy layouts out.
2. **Flat `src/` root:** ~30 top-level page/feature files. Move public marketing pages to `src/pages/` (or `src/marketing/`), legacy app features to `src/legacy/` or their own folder.
3. **Dead copies committed:** `App copy.js`, `App copy.css`, `LandingPage copy.jsx`, `components/CarbonTallyDemo copy.jsx`, `components/FileUploadHero copy.jsx`.
4. **Duplicated component concepts:** `DocumentStatus.jsx` (root) vs `components/DocumentStatus.jsx`; `ManualEntry.jsx` / `ManualEntryStandalone.jsx` / `ManualEntryView.jsx`; `PDFIngestionPortal.jsx` + `PDFRepairTool.js` + `UploadSection.js` + `UploadManager.js` + `BulkUpload.jsx` overlap.
5. **No code splitting:** `React.lazy`/`Suspense` are absent; the whole app (MUI, recharts, react-pdf, xlsx, framer-motion) ships in one bundle (§27).
6. **Duplicate route declarations** in App.js (`/privacy` twice, `/dashboard/*` twice) — a P1 bug source.
7. **API base URL inconsistency:** `v3/api.js` defaults to `http://localhost:8000`; `Glossary.jsx` defaults to `https://carbontally-api.onrender.com`; both read different env vars. Consolidate in one config module.

---

## 19. Backend Directory Structure Audit

Current (`backend/`):

```
backend/
├── main.py            (394 lines — mounts legacy routes/* AND api/ router)
├── config.py, database.py, auth.py
├── api/               (v3_*.py + admin_*.py + business.py + dependencies.py + router.py + middleware.py)
├── routes/            (LEGACY v1 surface — still mounted: upload, reports, documents_main, waitlist, admin/...)
├── services/          (billing.py, storage.py, email_service.py, v3_email.py, email.js ← JS file in Python dir)
├── data/              (repositories — organizations.py, billing.py, tenant.py, base.py, ...)
├── domain/            (organization.py, billing.py, document.py, ...)
├── engines/           (ai_extraction.py, extraction.py, factor_matching.py, calculation.py, processing_workflow.py, ...)
├── core/              (exceptions.py, logging.py, types.py)
├── infra/             (config.py, supabase.py, audit_logger.py, event_bus.py, llm_client.py, search_index.py)
├── middleware/        (rate_limit.py)
├── utils/             (document_classifier.py, email.py, audit_logger.py, staff_workload.py, ...)
├── tests/             (unit/{api,domain,engines,infra}, integration/, + legacy scripts at root)
└── ROOT-LEVEL SCRATCH: main copy.py, main copy 2.py, main_v2.py, glossary copy.py,
    pdf_engine.py, process_emissions.py, report_generator.py, featurelist.txt,
    _cf_verify*.py, _phase9*.py, _phase10*.py, _v3m12_*.py, test_results.json,
    carbon_tally_backup.sql (+ .bak), requirements copy.txt, backend/.env.bak
```

**Good:**
- The V3 core (api → services → domain → data → infra/engines) has clear, consistent dependency direction. The D37 billing slice is exemplary: `api/v3_billing.py` + `api/v3_commercial.py` → `services/billing.py` (entitlement/orders/metering) → `domain/billing.py` → `data/billing.py` → Supabase. No circular imports found in the billing slice.
- Error contract (core.exceptions → consistent HTTP envelope) is a strong pattern.
- `api/router.py` is a clean composition root.

**Non-standard / should change (P2/P3, staged):**
1. **Legacy `routes/` still mounted** alongside `api/` — a deliberate transition state, but it means two routing generations, two auth styles, and a stub waitlist live in production code. Plan a cutover/removal phase.
2. **Middleware/audit duplication:** `api/middleware.py` (RequestContextMiddleware) vs `middleware/rate_limit.py` vs `utils/audit_logger.py` vs `infra/audit_logger.py`.
3. **Root-level legacy modules** (`pdf_engine.py`, `process_emissions.py`, `report_generator.py`, `glossary.py`, `main_v2.py`) — move into `engines/` or archive.
4. **Copy files** (`main copy.py`, `main copy 2.py`, `glossary copy.py`, `requirements copy.txt`) — dead.
5. **`services/email.js`** — a JavaScript file inside the Python services package.
6. **`api/v3_commercial.py` (822 lines) and `data/billing.py` (914 lines)** are large but cohesive; acceptable, though commercial could be split into routes + handlers for readability.
7. **Config in code:** `config.py` `FOUNDER_EMAIL` fallback to a personal address; duplicated `www.carbontally.co.uk` origin; `https://*.onrender.com` wildcard; `CORS_ALLOW_METHODS/HEADERS=["*"]` with `CORS_ALLOW_CREDENTIALS=True` (§25/§26).

---

## 20. Domain / Service / Repository Audit

**Overall: the V3 architecture follows API → Service → Domain → Repository → DB, and the billing domain does it cleanly.**

- `services/billing.py` (832 lines): entitlement engine, ledger grant/consume/rollover/adjust/reverse/refund, subscription lifecycle, orders, storage metering, `charge_processing`. One responsibility cluster (commercial operations) — acceptable.
- `domain/billing.py` (288): value objects/enums for the billing model. Clean.
- `data/billing.py` (914): repositories (subscription, ledger, orders, storage, payments, idempotency) + `UsageTrackingRepository`. Thin SQL/PostgREST mapping. Clean.
- `api/v3_billing.py` (300) + `api/v3_commercial.py` (822): customer and admin surfaces. Some orchestration logic lives in routes (acceptable at this scale, but `v3_commercial.py` is a candidate for splitting handlers from route definitions).
- **Boundary notes:** a few routes elsewhere call repositories directly (bypassing a service layer) — fine for simple CRUD; no dangerous domain leakage found in the billing path. The one intentional exception is the D36/D37 replacement of direct client-side PostgREST writes with server-authoritative APIs — the correct decision.
- **Frontend mirror:** `v3/api.js` is the single client for the V3 backend; components receive data through it rather than computing domain values. Good.

---

## 21. API Architecture Audit

- Naming: `/api/v2/*` (health) + `/api/v3/*` (V3 feature surfaces) + legacy `/api/*` (`routes/`). Coherent per generation.
- Billing surface: customer `/api/v3/billing/*` (me/credits/orders/payments/storage/refresh, assisted estimate+approve+cancel, managed orders) and admin `/api/v3/commercial/*` (subscriptions, orders+complete, storage, payments, entitlement, credit ops) — consistent, org-scoped, authorization-checked (per D37-0/D37 reports).
- Error handling: centralised envelope via `router.py`; consistent status codes. ✅
- Response formats: consistent JSON envelopes. ✅
- **Issues:**
  1. **Two routing generations in production** (`api/` + `routes/`) with different auth patterns — transition debt.
  2. `routes/waitlist.py` is a stub (`pass`) — dead endpoint inviting misuse.
  3. `/api/v2/health` is current while V3 exists — harmless but inconsistent; health should be `/api/v3/health` (or root).
  4. No public API documentation page for customers (B2B/platform API is a future promise; `docs/api` exists internally). Roadmap item (P3), not a defect.

---

## 22. Database / Migration Organization Audit

Location: `supabase/migrations/` (30 migrations).

- **Naming/chronology:** good — `YYYYMMDDHHMMSS_<slug>.sql`; additive and mostly idempotent (D37-0/D37 verified idempotent on main + test DBs).
- **Versioning:** rc2 baseline → v3m series → D-series with a D37-0/D37 master split. Clear.
- **Gaps:** `20260810030000_v3m4` is skipped (v3m1→v3m2→v3m3→v3m5). Harmless but untidy.
- **Idempotency/reversibility:** migrations use `IF NOT EXISTS` / `DO $$ … ON CONFLICT DO NOTHING` patterns; no down-migrations (normal for Supabase).
- **Schema snapshots at repo root are duplicated/divergent:** `CarbonTally_DB_Schema_V3M2.sql` (244 KB), `v3_schema.sql` (232 KB), `schema.sql`, `supabase/seed.sql`, plus `backups/`. These drift from `supabase/migrations`; treat migrations as the single source of truth and archive the snapshots. **P2.**
- **Data defect in seed:** Professional plan seeded with `currency = 'GBP'` while Starter/Business are `USD` (§6). **P1 config fix.**
- **Migration history hygiene:** `00000000000000_init_schema.sql` remains as the baseline (fine); header doc-comments on each migration are good practice.

---

## 23. Test Architecture Audit

- **Good:** `backend/tests/unit/{api,domain,engines,infra}` and `backend/tests/integration/` are well organised; `tests/unit/api/fakes.py` + `conftest.py` + `route_paths.py` are sensible shared helpers; RLS has its own integration suite (`test_v3_rls_behavior.py`); frontend API client has `src/v3/__tests__/api.test.js`. Suite health (from D37 report): unit 1039→1056, RLS 23→27, frontend 23→25 — green.
- **Known pre-existing issues (unchanged):** `App.test.js` fails (react-router-dom v7 resolution); unit + RLS suites must run in separate pytest processes (conftest env mutation → 5 customer-admin failures when combined). Documented; not this audit's scope to fix.
- **Legacy scripts polluting `tests/` root:** `create_test_users.py`, `setup_test_data.py`, `setup_test_orgs.py`, `test_api.py`, `test_api_simple.py`, `test_auth_simple.py`, `test_failing_endpoints.py`, `test_all_endpoints.py`, `verify_setup.py`, `fix_imports.py`, `check_imports.py`, `export_postman.py`, `audit_code.py`, `config.py`, `auth_helper.py`. Move to `scripts/` or delete. **P2.**
- **Live smoke scripts** (`/tmp/d37_live_smoke.py`, `/tmp/d370_live_smoke.py`) live outside the repo — good; consider promoting a checked-in `scripts/live_smoke/` version. **P3.**

---

## 24. Temporary / Legacy File Audit

Classification (nothing deleted — recommendations only):

**Must remove / purge (P0/P1):**
- `tools/carbon_data_factory/deeepseek_api.txt` — contains a live `sk-…` API key committed to git. Revoke the key, delete the file, purge from history (`git filter-repo` or equivalent), and audit git history for other keys (§26).

**Should remove from the repo (untracked junk on disk):**
- Root scratch: ~60 `_*.txt`, `tmp_*.txt`, `probe_out*.txt`, `tmp_*.log`; `_cf_verify*.py`, `_phase9*.py`, `_phase10*.py`, `_v3m12_*.py`, `_bypass.txt`, `_gate_check.txt`.
- `admin-dashboard.zip` (127 MB, untracked), `backend - backup.zip` (tracked), `backend/carbon_tally_backup*.sql` (ignored), `test_results.json` (root + backend), `clean_emissions_output.json`, `mock_*.csv`, `v1.9.txt`, `current_project_structure.txt`, `clean.js`, `create_admin_dashboard.py`, `list_endpoints.py`, `quick_api_ref.py`, `generate_*.py`, `export_postman.py`, `seed.config.ts` / `seed.ts` / `prisma.config.ts` / `prisma/schema.prisma` (abandoned Snaplet/Prisma experiment), `local_backups/`, `.tmp_pgdata/`.

**Should move / archive (tracked, non-production):**
- `docs/Final/`, `docs/Final_Kimi/` (incl. scratch PNGs + a zip), `docs/architecture/*.zip` (UI.zip, DB_Migration zips), `docs/architecture/chatGptPrompts.txt`, `docs/Final_Kimi/user_pasted_clipboard_*.txt`.
- Copy files tracked in git: `backend/glossary copy.py`, `backend/main copy.py`, `backend/main copy 2.py`, `backend/requirements copy.txt`, `frontend/src/App copy.js`, `App copy.css`, `LandingPage copy.jsx`, `components/CarbonTallyDemo copy.jsx`, `components/FileUploadHero copy.jsx`, `supabase/config copy.toml`.
- `output/` (14 tracked files) → git-ignore/archive.
- `uploads/` sample images → `docs/samples` or assets.
- `carbon-tally-ui-demo/` → archive or delete (superseded by `frontend/`).

**Safe to keep:**
- `tools/` (benchmark_runner, load_tester, schema_auditor, migration_generator, carbon_data_factory **minus the secret file**, documentation_generator).
- `demodatagen/` (documented dev tool), `backups/`, `screenshots/` (dev-only).
- `API_ENDPOINTS.md`, `supabase/config.toml`, `supabase/seed/`.

---

## 25. Configuration / Environment Audit

**What is done well:**
- `.gitignore` excludes `.env*`, `*.dump`, `/.tmp_pgdata/`, scratch `_*`/`tmp_*` patterns, `admin-dashboard/`, node_modules. Env files are **not tracked** (verified via `git ls-files`).
- Per-environment env files exist (`.env`, `.env.local`, `.env.production`, `.env.test`, `backend/.env`).

**Findings (no secret values reproduced):**
1. **P0 — committed credential:** `tools/carbon_data_factory/deeepseek_api.txt` (tracked). Category: third-party LLM provider API key. Must be revoked + history-purged.
2. **P1/P2 — hard-coded live endpoints in tracked source:**
   - `frontend/src/supabaseClient.js` — live Supabase project URL + publishable key as hard-coded fallbacks (publishable keys are public by Supabase design, but the live URL in source is a config smell; keep URLs in env only).
   - `frontend/src/Glossary.jsx` — hard-coded `https://carbontally-api.onrender.com` fallback.
   - `frontend/src/v3/api.js` — `http://localhost:8000` fallback (inconsistent with Glossary).
   - `prisma/schema.prisma` (untracked) — local Postgres connection string with credentials in plaintext on disk.
3. **P2 — env files on disk with secrets:** root `.env*`, `backend/.env`, `backend/.env.bak` contain service-role keys, JWT secret, Resend key, etc. They are gitignored (good), but `backend/.env.bak` should be deleted rather than kept as a working file.
4. **P2 — config.py hygiene:** duplicate `www.carbontally.co.uk` origin; `https://*.onrender.com` wildcard origin; `FOUNDER_EMAIL` fallback to a personal address; `CORS_ALLOW_METHODS/HEADERS=["*"]` combined with `CORS_ALLOW_CREDENTIALS=True` (browser-safe only because origins are enumerated — tighten to explicit methods/headers).
5. **P3 — version drift:** root `requirements.txt` uses invalid `=>` syntax and duplicates `backend/requirements.txt`; root `package.json` duplicates `frontend/package.json` responsibilities.

---

## 26. Security Audit

**Strong areas (verified from D37-0/D37 reports and migration inspection):**
- Billing tables RLS **deny-by-default**; table-level `REVOKE INSERT/UPDATE/DELETE` on `organizations`, `usage_tracking`, `customer_subscriptions`, `consultant_billing` from `authenticated`; service-role-only writes; tenant write policies dropped. The D36 P0 (column-level REVOKE not overriding table grants) is fixed.
- Server-authoritative entitlement resolution (`BillingService.get_entitlement`), fail-closed.
- Append-only credit ledger with derived balance; durable idempotency keys on every commercial mutation.
- V3 routes enforce `ProtectedRoute`/`RoleRoute` (frontend) and staff permission checks (`can_manage_billing`, `operations_auth` chain) (backend).
- `v3/api.js`: 25s timeouts, friendly errors, bearer auth, and no client-supplied role claims for post-login routing.

**Findings / risks:**
1. **P0 — committed `sk-…` key** (§25). Tooling key, but any committed key is a P0 until revoked and purged.
2. **P1 — `/privacy` renders `PricingPage`** (duplicate route). A legal URL serves the wrong page; Privacy Policy must be reliably reachable before any public launch.
3. **P1 — beta code validation is client-side and pre-auth.** `BetaSignup.jsx` reads `beta_access_codes` directly via the Supabase client (anon). The migrations contain **no RLS policy or `ENABLE ROW LEVEL SECURITY`** statement for `beta_access_codes`/`beta_users`. If RLS is disabled on those tables in the live DB, invite codes (and their bound emails) could be enumerable by unauthenticated visitors → invite-only signup bypass. **Verify RLS state immediately; if anon-readable, lock down (P0/P1).**
4. **P2 — `supabaseClient.js` hard-codes the live project URL + publishable key** — publishable by Supabase design, but ensure it is current and that all sensitive tables (not just billing) are RLS-locked.
5. **P2 — wildcard CORS + `*` methods/headers with credentials** (§25).
6. **P2 — public auth surfaces** (`/beta-login`, `/beta/signup`, `/auth/magic`) remain indexed/visible; the magic-link flow still greets "Welcome to CarbonTally Beta!".
7. **P3 — `console.log` of session/email** in `App.js`/`Login.js` initialization (dev noise; remove before launch).
8. **No source-map concern identified** beyond CRA defaults; no service-role key found in tracked frontend source (the `sb_publishable_…` value is a publishable key, not a service-role key).

---

## 27. Performance Audit

- **Single bundle:** no `React.lazy`/`Suspense` anywhere in `App.js` (verified). All routes ship in one bundle; heavy deps include `@mui/material` v9, `recharts`, `react-pdf`, `xlsx`, `framer-motion`. Public marketing pages pay the same load cost as the full app.
- **Client-rendered SPA:** first paint depends on JS download/execution; the raw HTML has no meaningful content. No Lighthouse data was available — none is fabricated here.
- **Public pages that fire Supabase auth + org lookups:** `AppHeader` fetches the session + `organization_members` on every public page — small but unnecessary DB calls on marketing pages.
- **Images:** unoptimised PNGs/GIFs in `src/images/` and `public/`; `ui-avatars.com` external fetches on the About page.
- **Dependencies:** `purgecss`/`postcss-purgecss` are configured as devDeps but no build integration is evident in `frontend/package.json` scripts.
- **Recommendations (P2/P3):** split routes with `React.lazy` (marketing first); add a prerender/static layer for the 5–6 public pages; keep analytics scripts out until the cookie policy matches reality; defer heavy libs (xlsx/react-pdf) behind lazy imports.

---

## 28. Industry-Standard Architecture Assessment

**Backend V3 core: Level A−/B+.** FastAPI + layered services/domain/repos + centralised error contract + RLS-bounded persistence is genuinely production-shaped for a small team. The billing slice (D37) would pass review in most small-SaaS shops.

**Frontend: Level B−/C+.** The `v3/` feature folders are good, but a 2,100-line `App.js`, a flat 30-file `src/` root, dead copies, duplicate routes, and a single bundle are typical organically-grown React debt that is cheap to fix incrementally.

**Repository/workspace hygiene: Level C−.** Root-level scratch, tracked backups/zips, a second dashboard app, an abandoned Prisma/Snaplet experiment, and a stray root `src/` Python package blur boundaries and slow onboarding.

**Overall: Level B− (acceptable with structured refactoring)** for the product core; the public website is **Level C−** and is the main commercial-launch blocker.

---

## 29. Technical Debt Inventory

| # | Item | Area | Priority |
|---|---|---|---|
| 1 | Committed `sk-…` key in `tools/carbon_data_factory/deeepseek_api.txt` | Security/repo | **P0** |
| 2 | No `/pricing` route; `/privacy` shadowed by PricingPage; `/dashboard/*` duplicated | Frontend routes | **P1** |
| 3 | Fake waitlist (frontend simulation + backend `pass` stub) — lost leads | Public site | **P1** |
| 4 | Legal pages: placeholders, invented terms, non-existent cookies/analytics, dynamic dates | Legal/public | **P1** |
| 5 | About page fictional team + "Start Free Trial" + "trusted by businesses" | Public/legal | **P1** |
| 6 | Annual "Save 20%" toggle not backed by billing engine | Pricing | **P1** |
| 7 | Professional plan currency GBP vs USD seed | Billing config | **P1** |
| 8 | `beta_access_codes` RLS status unverified + client-side code validation | Security | **P1** |
| 9 | Beta messaging everywhere (§5) | Public | **P2** |
| 10 | Dead footer links (16 of ~22) + no Contact page | Public | **P2** |
| 11 | Legacy `routes/` still mounted beside `api/`; stub waitlist endpoint | Backend | **P2** |
| 12 | Copy/backup files tracked in git (zips, `* copy.*`, mock CSVs, `v1.9.txt`) | Repo | **P2** |
| 13 | Root scratch files (~60) on disk | Repo | **P2** |
| 14 | Monolithic `App.js`; flat `src/`; no code splitting | Frontend | **P2** |
| 15 | SEO defaults (title/description/OG/sitemap/structured data) | Public/SEO | **P2** |
| 16 | Storage FAQ "additional storage can be purchased" — not purchasable yet | Pricing | **P2** |
| 17 | "Priority support/processing", "24-hour turnaround", "SOC 2/SSO/AES-256", "certified … CSRD/ESRS/ISSB" claims need verification | Public | **P2** |
| 18 | Inconsistent API base URL defaults (`localhost:8000` vs `onrender.com`) | Frontend | **P2** |
| 19 | CORS wildcards/`*` headers; duplicate origins; founder email fallback | Backend | **P2** |
| 20 | `tests/` root legacy scripts; `backend/tests/` scratch | Tests | **P2** |
| 21 | Duplicated schema snapshots at root (`CarbonTally_DB_Schema_V3M2.sql`, `v3_schema.sql`, `schema.sql`) | DB/docs | **P2** |
| 22 | `services/email.js` inside Python services | Backend | **P3** |
| 23 | `utils/` vs `infra/` audit-logger duplication; `middleware/` vs `api/middleware.py` | Backend | **P3** |
| 24 | `v3m4` migration gap; root `requirements.txt` invalid `=>` syntax | Repo | **P3** |
| 25 | `console.log` session data; magic-link beta greeting | Frontend | **P3** |
| 26 | Unused components (`DataSecurity`, `PDFIngestionPortal`, etc.) in bundle | Frontend | **P3** |
| 27 | Pre-existing test infra friction (App.test.js; pytest conftest env mutation) | Tests | **P3** |

---

## 30. Recommended Directory Structure

### CURRENT (abridged, relevant parts)

```
carbon_tally/
├── .env / .env.local / .env.production / .env.test / .local-demo-credentials.md
├── requirements.txt            # stray (invalid syntax)
├── package.json                # "monorepo" build wrapper
├── prisma/  prisma.config.ts  seed.ts  seed.config.ts   # abandoned experiment
├── src/                        # stray Python package (commands/, providers/)
├── admin/                      # second dashboard app
├── carbon-tally-ui-demo/  demodatagen/  tools/
├── backend/
│   ├── main.py  config.py  database.py  auth.py
│   ├── api/  routes/  services/  data/  domain/  engines/  core/  infra/  middleware/  utils/
│   ├── main copy.py  main copy 2.py  main_v2.py  glossary copy.py  pdf_engine.py ...
├── frontend/src/               # ~30 flat files + components/ + css/ + v3/ + copies
├── supabase/  (migrations/, seed/, config.toml, config copy.toml)
├── docs/  (architecture/, audit/, cline/, Final/, Final_Kimi/, Pricing/, ...)
├── output/  screenshots/  backups/  local_backups/  uploads/
├── *_/*.txt scratch (~60), probe_out*.txt, admin-dashboard.zip, backend - backup.zip
└── *_mock.csv, v1.9.txt, CarbonTally_DB_Schema_V3M2.sql, v3_schema.sql, schema.sql
```

### PROPOSED (realistic for a small team — do NOT implement now)

```
carbon_tally/
├── apps/
│   ├── frontend/               # (existing frontend/) — public + app
│   └── admin/                  # (existing admin/) — internal dashboard (fate TBD)
├── backend/                    # (existing backend/, cleaned)
│   └── …api/ services/ data/ domain/ engines/ core/ infra/ tests/
├── supabase/                   # migrations (source of truth) + seed + config.toml
├── scripts/                    # dev/ops/one-off scripts (from root + tests/ + tools/ subsets)
│   ├── seed/  live_smoke/
├── docs/
│   ├── architecture/  audit/  guides/  pricing/  business/
│   └── _archive/               # Final/, Final_Kimi/, zips, stale specs
├── assets/                     # screenshots/, uploads/, marketing samples (optional; git-ignored)
├── .env.example                # the ONLY env file template tracked
└── README.md  CONTRIBUTING.md  Makefile|Taskfile
```

**What moves:** root scratch → delete; `tools/` → `scripts/` (or keep `tools/` with the secret file removed); `demodatagen/` → `scripts/demodatagen/`; `carbon-tally-ui-demo/`, `prisma/`, root `src/` → archive/delete; mock CSVs → `scripts/` fixtures or delete; `v1.9.txt`/`API_ENDPOINTS.md` → `docs/`; schema snapshots → `docs/archive/` or `supabase/snapshots/` (migrations stay authoritative); `output/`/`screenshots/` → git-ignored.
**What stays:** `backend/` (with the `routes/`→`api/` cutover planned), `frontend/` (with `v3/` promoted and `src/` flat files grouped), `supabase/migrations`, `docs/audit/cline` reports, `.agents/` skills.
**What consolidates:** the two admin UIs (`admin/` app vs `frontend` `/ops` hub) — decide one owner (recommend keeping `/ops` in the main app and archiving the standalone `admin/` app unless it is genuinely used); duplicate `requirements*.txt`; duplicated audit-logger modules.
**What becomes infrastructure:** `infra/` (config, supabase client, event bus, llm client, search index) stays as-is — it already is infrastructure.
**What becomes tests:** move legacy `tests/*.py` scripts to `scripts/`; keep `tests/unit|integration`; promote a checked-in live-smoke script.

---

## 31. Recommended Public Website Structure

Smallest coherent structure that communicates the product:

| Route | Purpose |
|---|---|
| `/` | Home — positioning, three workflow modes, traceability, platforms, CTA → signup |
| `/pricing` | **Fix the route.** Existing PricingPage content; remove beta banner, wire CTAs |
| `/how-it-works` (optional, P3) | Self-Service → Assisted → Managed; evidence chain; human fallback |
| `/managed-processing` (optional, P3) | Dedicated managed story + enterprise CTA |
| `/for-consultants` (optional, P3) | Multi-client story (currently a pricing section) |
| `/about` | Real company story (founder-verified), remove fictional team |
| `/contact` | **New.** Contact/enterprise/demo/quote CTAs land here |
| `/terms` `/privacy` `/cookies` | Legal — fix placeholders, identity, dates; legal review |
| `/signup` `/login` | Existing D35 flows (keep) |
| `/beta/signup` | Keep as admin-only invite path; unlink from public nav |

**Removed/redirected:** beta banner, `/beta-login` (fold into login or redirect), `/PricingPage` (dead), `/dashboard/*` legacy (already redirecting).

---

## 32. Recommended Content Changes

1. **Remove beta framing** from all public surfaces (§5) — banner, badges, modal, CTA copy.
2. **Wire CTAs** to `/signup` (primary), `/pricing` (secondary), `/contact` (tertiary). Replace the waitlist modal with a real implementation **or** a genuine (persisted) waitlist endpoint if the PO wants pre-launch capture.
3. **Pricing page:** remove the annual toggle (or gate it behind real annual plans); remove the "proposed baseline" disclaimer; add "Exceptional — quote" assisted tier; align plan-feature copy with D37 plan config; state Assisted/Managed availability is plan-gated; correct rollover language from "planned" to "available".
4. **About page:** remove fictional team; confirm founder/founding facts; replace "Start Free Trial" with a real CTA; align company identity ("CarbonTally Ltd" everywhere, correct email domain); remove unverifiable "trusted by businesses".
5. **Footer:** replace dead links with real ones (only ship links to pages that exist); add Contact; fix company identity and social links.
6. **Legal:** professional review; remove placeholders; correct cookie/analytics claims to match reality (no analytics scripts today); name processors (Supabase, Vercel, Render, Resend, AI providers, Processing Entities); remove invented retention/termination terms; remove "annual" billing claim until implemented.
7. **Consistency pass:** unify "credits"/"processing units" vocabulary; reconcile "carbon accounting vs processing layer" positioning in About/Terms/footer Solutions; single company name + domain.
8. **Claims pass (§12):** verify or soften "certified … SECR/CSRD/ESRS/ISSB", "SOC 2/SSO/AES-256", "24-hour turnaround", "priority support", "Limited spots".

---

## 33. Recommended Beta Transition

1. **Remove public beta marketing** (banners, badges, hero badge, waitlist CTA) — the product is now commercially configured with self-service signup.
2. **Keep `/beta/signup` + `beta_access_codes`** as the internal/admin invite mechanism; keep the small "Have an access code?" link on the signup page; unlink from nav/footer.
3. **Replace the Beta CTA** with "Get Started → `/signup`".
4. **Decision needed from PO:** whether a genuine waitlist/capture form is wanted before payments launch (if yes, implement a persisted endpoint + GDPR-consistent capture; if no, delete the modal + waitlist stub).
5. **Verify RLS on `beta_access_codes`/`beta_users`** before treating `/beta/signup` as an admin-only path (§26).
6. Optionally retire `/beta-login` and the magic-link beta greeting in the same change.

---

## 34. Recommended Refactoring Sequence

Safe order (each stage independently shippable):

- **Stage 1 — Security/hygiene (P0/P1):** revoke + purge the committed `sk-…` key; verify/lock `beta_access_codes` RLS; delete `backend/.env.bak`; confirm no other secrets in history.
- **Stage 2 — Public content correction:** fix `/privacy` duplicate + add `/pricing` route; fix header/footer Pricing links; remove beta banner/badges; wire CTAs to `/signup`; add Contact page; replace fake waitlist (real endpoint or removal); correct About/footer content.
- **Stage 3 — Commercial messaging:** pricing page alignment with D37 (annual toggle, disclaimer, Exceptional tier, plan-gated features, rollover wording); currency fix for Professional plan in DB config.
- **Stage 4 — Legal content review:** placeholders, identity/domain, cookies/analytics accuracy, processors, retention, termination, payment/tax language; professional legal sign-off.
- **Stage 5 — SEO/performance:** titles/descriptions, OG/Twitter/canonical, sitemap, robots, structured data; `React.lazy` for heavy routes; prerender/static marketing layer (proportionate option).
- **Stage 6 — Frontend structural refactor:** split `App.js` routes; group flat `src/` files (pages/, legacy/); delete copy files; consolidate API-base config; remove unused components.
- **Stage 7 — Backend structural refactor:** plan the `routes/`→`api/` cutover; move root-level legacy modules into `engines/`; delete copy files; resolve middleware/audit duplication; split `v3_commercial.py` if needed.
- **Stage 8 — Repo/test cleanup:** move/delete scratch + tracked junk; archive `docs/Final*`, zips; clean `tests/` root; consolidate requirements; decide `admin/` app fate; single `.env.example`.
- **Stage 9 — Final public QA:** journey test, link audit, SEO audit, Lighthouse baseline, RLS re-verification.

---

## 35. Priority Matrix

| Priority | Items |
|---|---|
| **P0** | Revoke/purge committed API key; verify + lock `beta_access_codes` RLS (verify → P0 if anon-readable) |
| **P1** | `/privacy` shadow fix + `/pricing` route; fake waitlist; legal placeholders/terms/cookie-policy accuracy; About fictional team + "Free Trial"; annual toggle; Professional currency seed; contact page; correct CTA hierarchy |
| **P2** | Beta messaging removal; dead footer links; legacy `routes/` cutover plan; copy/backup tracked files; root scratch; `App.js` split + code splitting; SEO foundation; storage FAQ wording; unverified marketing claims; API-base inconsistency; CORS tightening; `tests/` root cleanup; schema snapshot duplication |
| **P3** | `email.js` move; audit-logger/middleware consolidation; `v3m4` gap; `requirements.txt` syntax; console.log cleanup; unused components; test-infra friction |

---

## 36. Product Owner Decisions Required

1. **Beta transition:** remove all public beta marketing? Keep `/beta/signup` as the only invite path? (Recommend: yes / yes.)
2. **Waitlist:** implement a real persisted waitlist before payments, or delete the modal + stub? (Recommend: delete — `/signup` exists.)
3. **Pricing page:** annual toggle — remove now, or invest in real annual billing? (Recommend: remove until annual billing exists.)
4. **Claims:** confirm which marketing claims can be evidenced (SOC 2/SSO/AES-256 infra, "24-hour turnaround", "priority support", CSRD/ESRS/ISSB report compliance, "certified" Scope 1/2/3).
5. **About page:** confirm founder/founding facts; approve removal of the three fictional team profiles; confirm company legal identity + registered details + official contact email domain for the legal pages.
6. **Analytics/cookies:** are GA/HubSpot/LinkedIn intended to be installed? If yes, install them and keep the policy; if no, rewrite the Cookie Policy to match reality.
7. **Professional plan currency:** confirm USD as the catalogue currency (config fix) — or confirm a deliberate GBP/USD mixed catalogue.
8. **Admin surfaces:** keep the standalone `admin/` app and the in-app `/ops` hub, or consolidate to one?
9. **Contact route:** create a public Contact page (recommended) — with what email/mechanism?
10. **D38 scope:** approve Stage 1–5 as the next implementation task, or a narrower public-content-only pass first.

---

## 37. What Must NOT Be Changed

- **D37-0 P0 RLS lockdown** (table-level REVOKEs, dropped tenant write policies) — do not weaken.
- **Credit ledger architecture** — append-only, derived balance, idempotency keys.
- **Server-authoritative entitlement/billing** — no client-computed commercial values.
- **The `/api/v3/*` + `v3/api.js` contract** — the app ↔ API surface is coherent; evolve, don't rewrite.
- **The D37 plan numbers** (Starter $49/100, Professional $149/500, Business $399/2,000) — they match across config + pricing page; only currency/terminology needs fixing.
- **The D35 self-service signup + server-authoritative post-login routing** — keep `/signup` as the primary journey.
- **Supabase/FastAPI/React/JSX stack** — no platform or TypeScript migration is warranted.
- **`supabase/migrations`** as the single source of truth for schema (do not replace with generated snapshots).
- **Existing test suites** and the current `tests/unit|integration` layout — extend, don't relocate wholesale.
- **`/beta/signup` admin invite mechanism** until the RLS question is resolved and an explicit PO decision replaces it.

---

## 38. Proposed Next Implementation Task

Recommend a **D38 — Public Website & Commercial Readiness** task (separate from this audit), executed in the Stage 1–5 order (§34):

- **Phase A (security):** revoke/purge the committed key; RLS verification for beta tables; remove `backend/.env.bak`.
- **Phase B (public correctness):** fix the `/privacy`→PricingPage bug, add `/pricing`, repair nav/footer links, add Contact, replace fake waitlist with `/signup` wiring.
- **Phase C (beta transition + pricing):** remove public beta messaging; align pricing page with D37 (annual toggle, disclaimer, Exceptional tier, rollover wording, plan-gated features); fix Professional currency in commercial config.
- **Phase D (legal):** professional legal review and rewrite of Terms/Privacy/Cookies (identity, placeholders, processors, cookie accuracy, payment/tax language).
- **Phase E (SEO/performance):** meta/OG/sitemap/structured data + route-level lazy loading.

Explicit **out of scope:** payment-provider integration, tax/accounting integration, blog CMS integration, backend `routes/` cutover, directory refactor, and any RLS weakening — all remain on the roadmap behind PO decisions.

---

## Overall Assessment

### Public Website — **3 / 10**
Client-rendered SPA only; the single most important page (pricing) is unreachable; a legal page is shadowed; 16 dead footer links; no contact page; fake waitlist discards leads. The marketing copy that does exist is strong, which is the only thing keeping this above 2.

### Commercial Messaging — **5 / 10**
Pricing numbers and credit/complexity explanation are accurate against D37; FAQ is genuinely good. Penalised by beta framing, the non-existent annual discount, the "proposed baseline" disclaimer, and unsupported claims (SOC 2/SSO, 24-hour turnaround, certified standards, fictional team).

### UX — **4 / 10**
The product journey (signup → onboarding → workspace → billing) is well built and server-authoritative. The public surface fails to route users into it (CTAs → fake waitlist, broken pricing, no contact), and terminology (beta vs self-service vs free trial) is confusing.

### SEO — **1 / 10**
Default CRA title and "Web site created using create-react-app" description, no OG/Twitter/canonical/sitemap/structured data, no prerendering, broken pricing links, duplicate `/privacy`. Effectively no organic-search strategy is implemented.

### Frontend Architecture — **4 / 10**
The `v3/` vertical structure and API client are genuinely good. Monolithic 2,100-line App.js, ~30 flat root files, committed copy files, duplicated routes, no code splitting, and inconsistent API base URLs drag it down.

### Backend Architecture — **7 / 10**
The V3 layered core (api → services → domain → data → infra) with a centralised error contract and the D37 billing slice are production-grade for this scale. Penalised by the still-mounted legacy `routes/` generation, root-level legacy modules, copy files, and middleware/audit duplication.

### Directory Structure — **2 / 10**
Root-level scratch, tracked backups and zips, a second admin app, an abandoned Prisma/Snaplet experiment, a stray Python package at `src/`, duplicated schema snapshots, and dead copy files. The weakest area and the biggest onboarding hazard.

### Maintainability — **4 / 10**
Core modules are well-factored and tested, but the workspace noise, dual routing generations, dead files, and multiple "source of truth" snapshots make every change more expensive than it should be.

### Production Readiness — **3 / 10**
The **application** is pre-production-complete and HARD-STOPPED correctly pending payment integration. The **public site** is not launch-safe: P0 credential hygiene, P1 route/legal/fake-waitlist defects, RLS verification outstanding on beta tables, and unverified claims must be resolved first.

---

## Final Recommendation

**1. Should the public "Join our Beta Program" messaging be removed?**
**Yes.** It conflicts with the D35 self-service signup and the D37 commercial configuration. Remove the banner, badges, and waitlist CTA from the public surfaces; keep an internal invite path only.

**2. Should `/beta/signup` remain?**
**Yes** — as the administrative/invite mechanism, **after** verifying RLS on `beta_access_codes`/`beta_users`. Remove public links except the subtle "Have an access code?" note on the signup page.

**3. What should replace the Beta CTA?**
"Get Started / Create account" → `/signup` (primary), "View Pricing" → `/pricing` (secondary), "Talk to us / Book a demo" → new `/contact` (tertiary). Log in remains in the header.

**4. Is the current pricing page consistent with D37?**
**Numbers: yes** (plans, credits, assisted fees, credit classes all match the D37 seed). **Presentation: no** — the annual "Save 20%" toggle has no billing-engine support, the "proposed baseline" disclaimer is stale, the Exceptional/quote assisted tier is missing, Professional's currency is seeded GBP while the page shows $, and all CTAs dead-end in the fake waitlist.

**5. What public pages should be added?**
`/pricing` (actually wired), `/contact`. Optional P3: `/how-it-works`, `/managed-processing`, `/for-consultants`. The Blog CMS exists separately and is not part of D37 — do not integrate now.

**6. What public pages should be removed?**
The beta banner/modal components (content, not pages); `/beta-login` (fold into `/login`); `/PricingPage` dead link (replace with `/pricing`). The standalone `admin/` app should be archived or its fate decided.

**7. What legal pages require professional review?**
All three: Terms (credits/rollover/processing/storage/orders/payment/cancellation/termination language is missing; "annual" and "30 days' notice" are invented), Privacy (placeholders, processors, retention, AI/Processing-Entity disclosure), Cookies (describes cookies that are not installed; no granular consent UI).

**8. What parts of the directory structure are non-standard?**
Root scratch files; tracked zips/backups/mock CSVs; committed `* copy.*` files; `prisma/`+Snaplet experiment; stray root `src/` Python package; root `requirements.txt` (invalid `=>`); duplicate schema snapshots; `admin/` second app; `docs/Final_Kimi` scratch content; `tests/` root legacy scripts; `services/email.js`.

**9. What should be refactored first?**
Stage 1 security/hygiene (P0 key, beta RLS) → Stage 2 public content/route correctness → Stage 3 pricing/commercial alignment → Stage 4 legal → Stage 5 SEO/perf. Structural refactors (Stages 6–8) come after the public site is coherent.

**10. What should NOT be refactored?**
The D37 RLS lockdown and credit-ledger architecture; the `/api/v3/*` contract and `v3/api.js`; the D35 signup/post-login routing; the billing service/domain/repo layering; `supabase/migrations` as schema source of truth; the current test suites; the Supabase/FastAPI/React/JSX stack.

**11. Is the current architecture safe to continue developing?**
**Yes for the application core** (HARD STOP on payment integration maintained). **Not safe to promote publicly** until the P0/P1 items in §§26/35 are resolved. Development can continue safely with the directory hygiene staged in parallel.

**12. What should the next Cline implementation task be?**
**D38 — Public Website & Commercial Readiness** as scoped in §38: (A) revoke/purge committed key + beta-table RLS verification, (B) fix `/privacy`/`/pricing` routes and wire CTAs to `/signup`, add `/contact`, replace the fake waitlist, (C) beta-transition messaging + pricing-page alignment with D37, (D) legal content remediation, (E) SEO/performance foundation. All subject to PO sign-off on the decisions in §36.

---

*End of audit. No application source, database schema, RLS, API, migration, route, or content was modified during this task.*
