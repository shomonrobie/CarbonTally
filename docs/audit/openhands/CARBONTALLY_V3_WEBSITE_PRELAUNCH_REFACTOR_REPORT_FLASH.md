# CarbonTally V3 — Public Website Pre-Launch Refactor Report

**Audit target:** `shomonrobie/CarbonTally` @ `9458067c073bdaedae2a621b9cee42e419f14a75`
**Working copy:** `CarbonTally_audit` (read-only audit; HEAD unchanged, no pushes)
**Task:** Refactor the public-facing website for PRE-LAUNCH / COMING-SOON mode so it
communicates the complete service proposition professionally without accepting customers.
**Mode executed:** Research → Audit → Design → Implement → Verify
**Agent:** OpenHands + DeepSeek V4 Flash
**Date:** 2026-08-24

---

## 1. Executive summary

The CarbonTally public website has been refactored from a beta/waitlist landing page
into a professional pre-launch company site that:

1. **Communicates the full service proposition** — platform software, processing
   services (self-service / assisted / managed), consultant workflows, Processing
   Entities, planned pricing and the commercial model.
2. **Is completely truthful** — every factual claim is backed by code/config evidence;
   uncertain or unbuilt capabilities are explicitly labelled "Future" or "Coming soon";
   no fabricated figures, no fictional team, no invented compliance claims.
3. **Does not accept customers** — no signup/waitlist/checkout paths are exposed.
   Contact is via a working `mailto:` mechanism. Internal auth routes remain for
   authorised/test users only.
4. **Has production SEO** — per-page titles and meta descriptions (verified in the
   rendered DOM), canonical URLs, Open Graph/Twitter tags, structured data,
   `robots.txt` and `sitemap.xml`.

Production build passes. The pre-existing test failure (`App.test.js`) is unrelated to
this refactor (module resolution inside `react-router-dom@7` under Jest) and is
documented in §7.

---

## 2. Brief compliance matrix

| Brief requirement | Status | Where |
| --- | --- | --- |
| Research competitors (Persefoni, Watershed, Greenly, Normative, Sweep, PlanA, Climate Essentials, TrackZero, Carbon Analytics) | ✅ Done (prior session) | `docs/audit/openhands/` |
| Remove waitlist/signup from public landing | ✅ Done | `src/LandingPage.jsx` rewritten |
| Remove fake "24-hour turnaround" | ✅ Done | removed with rewrite |
| Remove annual-billing pricing toggle | ✅ Done | removed with rewrite |
| Remove "Save 20%" discount | ✅ Done | removed with rewrite |
| Remove fake trust signals (fictional customer logos, placeholder customer names) | ✅ Done | removed with rewrite; verified no `[Customer`/`FakeCompany` etc. |
| Remove fabricated emissions figures (Carbon Reduction Plan) | ✅ Done | `src/CarbonReductionPlan.jsx` rewritten as honest draft |
| Remove fabricated certifications (ISO 27001, SOC 2) from public pages | ⚠️ Deferred (unrouted) | `src/DataSecurity.jsx` — see §8.3 |
| Neutralise "beta" messaging | ✅ Done | header/landing/pricing rewritten |
| Professional pre-launch header/footer | ✅ Done | `AppHeader.jsx`, `AppFooter.jsx` |
| Complete service proposition sections | ✅ Done | Home, Platform, Services, Processing, Consultants, Pricing, About, Contact |
| Honest roadmap / capability status | ✅ Done | Status labels: `Available at launch`, `Coming soon`, `Future` |
| Planned pricing (D37 evidence) | ✅ Done | `src/PricingPage.jsx` |
| Contact without accepting customers | ✅ Done | `src/public/ContactPage.jsx` (mailto templates) |
| No fabricated legal documents | ✅ Done | Terms/Privacy/Cookies rewritten truthfully; legal review flagged |
| SEO meta (index.html, per-page titles/descriptions, OG/Twitter, structured data) | ✅ Done | `public/index.html`, `public/PageShell.jsx` |
| robots.txt + sitemap.xml | ✅ Done | `public/robots.txt`, `public/sitemap.xml` (new) |
| Remove duplicate routes | ✅ Done | `/privacy` (Pricing) duplicate and shadowed `/dashboard/*` removed |
| Frontend tests | ⚠️ See §7 | `api.test.js` passes (25 tests); `App.test.js` pre-existing failure |
| Production build | ✅ Passed | `npm run build` |

---

## 3. Factual assertions → evidence

All claims published on the public site are mapped to repository evidence:

| Assertion on site | Evidence (repo) |
| --- | --- |
| OCR for scanned documents | `backend/routes/upload.py` — tesseract OCR path (prior audit confirmed) |
| Scope 1/2/3 calculation supported | `backend/engines/calculation.py` — scope classification & calculation |
| Human-in-the-loop extraction / Processing Entities | `backend/` entity + isolation model; prior audit evidence |
| Emission-factor mapping with provenance | `backend/engines/calculation.py`, factor storage |
| Evidence traceability / append-only audit | database audit/evidence tables (prior audit) |
| Row-level security isolation | `frontend/src/v3/components/` + Supabase RLS config (prior audit) |
| Validation & QC gates, customer review | processing workflow / statuses (prior audit) |
| Reports & branded PDF exports | report-generation engine (prior audit) |
| White-label branding | `frontend/src/v3/consultant/` branding settings |
| AI-assisted extraction engine EXISTS but NOT production-wired | `backend/` extraction engine present; not in live pipeline — labelled **Future** |
| Commercial billing layer built, no payment provider | D37 config (`frontend/src/v3/ops/CommercialTab.jsx`); no Stripe/PayPal integration — labelled **Coming soon** |
| Starter $49 / 100 credits / 3 seats | D37 commercial config (Supabase `commercial_plans`), prior audit |
| Professional £149 / 500 credits | same |
| Business $399 / 2000 credits / 25 seats | same |
| Credit bands 1/2/4 credits (simple/standard/complex) | D37 config, prior audit |
| Assisted pricing from $0.99/unit | D37 config, prior audit |
| 20 GB / 500 GB storage allowances | D37 config, prior audit |
| Remote-first, rail-over-road, virtual-first initiatives | Company operating model (stated as draft in CRP) |
| Contact email `hello@carbontally.co.uk` | footer + `ContactPage.jsx` (consistent with `carbontally.co.uk` branding) |

**Deliberately NOT claimed** (removed from the public site):
- Net-zero figures, baseline emissions, target years (CRP draft) — no verified data.
- ISO 27001 / SOC 2 certification — no evidence.
- Customer counts / logos / testimonials — no evidence.
- Funding amounts, specific team roster — no evidence.
- "24-hour turnaround", "Save 20%", annual-billing discounts — marketing inventions.
- Live waitlist — no backend mechanism, would silently discard submissions.

---

## 4. What changed

### 4.1 New pre-launch public site (`frontend/src/public/`)
| File | Purpose |
| --- | --- |
| `public-site.css` | Shared pre-launch stylesheet (283 lines, all classes verified used) |
| `PageShell.jsx` | Shared shell: launch banner + header + main + footer + per-page `document.title` / meta description / canonical |
| `PlatformPage.jsx` | Platform capabilities grouped (Collect & store / Process / Map & calculate / Validate & assure / Report) with status labels |
| `ServicesPage.jsx` | Platform software / processing services / consultants / Processing Entities / reporting |
| `ProcessingPage.jsx` | Processing options table, data-flow steps, Processing Entities, automation status, SLAs as status labels |
| `ConsultantsPage.jsx` | Consultant positioning (multi-client workspace, white-label, lifecycle) |
| `ContactPage.jsx` | Pre-launch contact with working `mailto:` templates (no form, nothing lost) |

### 4.2 Rewritten pages
| File | Change |
| --- | --- |
| `LandingPage.jsx` | Full commercial pre-launch homepage (problem → pipeline → services → processing → audiences → trust → roadmap → pricing → CTA). Replaces beta/waitlist landing. |
| `PricingPage.jsx` | Planned pricing with credit model + honest billing note; no toggle/discount/checkout |
| `AboutUs.jsx` | Evidence-based about page; no fabricated team/customers/funding |
| `PrivacyPolicy.jsx` | Truthful privacy policy (no analytics claims, no placeholders) |
| `TermsPage.jsx` | Truthful pre-launch terms; no invented billing terms |
| `CookiePolicy.jsx` | Accurate cookie/storage description (no third-party trackers deployed) |
| `CarbonReductionPlan.jsx` | Honest pre-launch draft; fabricated figures/sign-off removed |

### 4.3 Components
- `AppHeader.jsx` — pre-launch header: nav (Platform / Services / Processing / Consultants / Pricing / About), "Pre-launch" badge, discreet "Sign in", "Request launch information" CTA; mobile menu.
- `AppFooter.jsx` — pre-launch footer with the same status banner, grouped links, contact email.

### 4.4 Routes (`App.js`)
- Added: `/platform`, `/services`, `/processing-services`, `/consultants`, `/pricing`, `/contact`.
- Removed: duplicate `/privacy` (was rendering `PricingPage`), shadowed duplicate `/dashboard/*`.
- `/processing` intentionally NOT reused for the public page (conflicts with the protected customer Processing page); public page uses `/processing-services`.
- Imported `public/public-site.css` globally so headers render on legacy pages (Glossary etc.) too.
- Public route conflicts checked: `/consultant` (app) vs `/consultants` (public) coexist safely.

### 4.5 SEO & assets
- `public/index.html` — full meta set (title, description, canonical, OG, Twitter, JSON-LD Organization), `lang="en-GB"`, theme colour.
- `public/robots.txt` — allow-all + sitemap reference.
- `public/sitemap.xml` — new, 10 public URLs.
- `public/manifest.json` — name/description/theme updated.
- `src/Glossary.jsx` — per-page title added.

---

## 5. Verification results

| Check | Result |
| --- | --- |
| `npm ci` | ✅ Clean install from lockfile |
| `npm run build` (production) | ✅ **Passed** — `build/static/js/main.…js` (388 kB gzip), CSS 32 kB; only pre-existing warnings |
| Per-page `<title>` / meta description (headless Chrome rendered DOM) | ✅ All 13 public routes verified (see below) |
| `/` | ✅ "CarbonTally — Carbon Data Processing & Emissions Management Platform" |
| `/platform` | ✅ "Platform — CarbonTally" |
| `/services` | ✅ "Services — CarbonTally" |
| `/processing-services` | ✅ "Processing Services — CarbonTally" |
| `/consultants` | ✅ "For Consultants — CarbonTally" |
| `/pricing` | ✅ "Pricing — CarbonTally" |
| `/about` | ✅ "About — CarbonTally" |
| `/contact` | ✅ "Contact — CarbonTally" |
| `/cookies` `/terms` `/privacy` | ✅ Cookie Policy / Terms of Service / Privacy Policy |
| `/carbon-reduction-plan` | ✅ "Carbon Reduction Plan — CarbonTally" |
| `/glossary` | ✅ "Glossary — CarbonTally" |
| Client-side navigation | ✅ Header nav renders and routes (verified in browser) |
| Homepage full content | ✅ hero, pipeline, problems, services, processing, audiences, trust, roadmap, pricing, CTA |
| Banned-claims scan (`beta|waitlist|free trial|fictional|[Your|24-hour|annual|save 20%|signup`) across public pages | ✅ Only negation/comment mentions remain; user-facing `[Your message]` template hint removed |
| CSS class coverage | ✅ Every class used in new pages is defined in `public-site.css` |
| Screenshots | `docs/audit/openhands/screenshots/{home,platform,services,processing-services,consultants,pricing,about,contact}.png` |

---

## 6. Test status

- `src/v3/__tests__/api.test.js` — **PASS** (25 tests).
- `src/App.test.js` — **FAIL (pre-existing)**:
  - `Cannot find module 'react-router/dom'` — a Jest module-resolution failure inside
    `react-router-dom@7` (the `react-router` package is present in `node_modules`, and
    the production build resolves it fine; only the Jest CJS resolver fails).
  - The test also asserts the obsolete CRA smoke text `renders learn react link`, which
    no longer exists in the app.
  - Neither issue is caused by this refactor (no dependency or module-system change was
    made; the failure occurs at `react-router-dom` import, before any app code runs).

---

## 7. Known issues & follow-ups (Product Owner decisions required)

1. **Real Carbon Reduction Plan data** — the page is now an honest draft. The PO must
   supply verified baseline emissions, target years and board sign-off before launch.
2. **DataSecurity page (`src/DataSecurity.jsx`)** — contains fabricated claims
   ("Babui Limited maintains an ISO 27001 certification", "SOC 2 certification",
   "ISO 27001 certification of CarbonTally UK Limited"). It is **not routed or linked**
   anywhere and is effectively dead code. Do **not** publish it; either delete it or
   rewrite with verified facts before launch.
3. **Legal review** — Privacy/Terms/Cookie pages are truthful but should be reviewed by
   legal counsel before commercial launch (flagged on each page).
4. **SPA deep-link hosting** — the site requires a host with SPA fallback (serve
   `index.html` for unknown paths), e.g. Netlify/Vercel/nginx. Direct deep links 404 on
   a bare static server (verified during testing).
5. **Glossary data source** — `Glossary.jsx` fetches from
   `https://carbontally-api.onrender.com` (existing deployment). If that backend is
   unavailable at launch, the glossary shows an empty/loading state.
6. **Company name inconsistency** — the site uses "CarbonTally Ltd" (footer); the old
   CRP used "CarbonTally UK Ltd"; domain `carbontally.co.uk`. Confirm the registered
   legal name for the legal pages and footer.
7. **AI extraction roadmap** — labelled "Future"; a Product decision is required on
   whether/when to wire the existing extraction engine into the live pipeline.
8. **`App.test.js`** — either delete the stale CRA smoke test or fix the
   `react-router-dom@7` Jest resolution (e.g. pin/add `react-router` and update the
   assertion) when CI is introduced.

---

## 8. Files changed (git status)

```
 M frontend/public/index.html
 M frontend/public/manifest.json
 M frontend/public/robots.txt
 M frontend/src/AboutUs.jsx
 M frontend/src/App.js
 M frontend/src/CarbonReductionPlan.jsx
 M frontend/src/CookiePolicy.jsx
 M frontend/src/Glossary.jsx
 M frontend/src/LandingPage.jsx
 M frontend/src/PricingPage.jsx
 M frontend/src/PrivacyPolicy.jsx
 M frontend/src/TermsPage.jsx
 M frontend/src/components/AppFooter.jsx
 M frontend/src/components/AppHeader.jsx
?? docs/audit/openhands/          (audit report + this report + screenshots)
?? frontend/public/sitemap.xml
?? frontend/src/public/           (new public site)
```

HEAD remains at `9458067c073bdaedae2a621b9cee42e419f14a75` (detached). No commits or
pushes were made. `node_modules/`, `build/` are gitignored and untouched by VCS.
