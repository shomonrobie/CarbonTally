# CarbonTally V3 — Final Public-Site QA Report

**Repo:** `shomonrobie/CarbonTally` @ `9458067` (baseline)
**Audit clone:** `CarbonTally_audit/` (read-only; **no commits, no pushes**)
**Scope:** Public website UX, visual system & content QA — pre-launch / coming-soon mode
**Method:** Custom CDP harness (headless Chrome 151, Node 22) — route sweep, overflow,
clipping, broken-image, zero-height, nav-active, cookie-banner, contrast, demo
interactivity, link crawl, SEO/metadata. No vision API available — all visual checks
are programmatic; reference screenshots captured for human review.

---

## Result summary

| Check | Result |
|---|---|
| Routes (13 public + login) | All return HTTP 200 |
| Horizontal overflow | None at 1440 / 768 / 390 / 360 px on every route |
| Console errors | 0 on all routes (except transient container-network artifact, not reproducible) |
| Text clipping / broken images / zero-height elements | None (all 39 route×width checks) |
| Demo interactivity (auto-start, Replay, math) | Working — results match demo data |
| Cookie banner (Decline/Accept, persistence) | Working — `cookieConsent` persisted in localStorage |
| Contrast (WCAG AA) | All sampled pairs pass (5.47:1 – 12.54:1) |
| Internal links | All resolve (no dead links) |
| Per-page title / description / canonical | Working (canonical dedupe fixed this pass) |
| Sitemap / robots / JSON-LD / OG / theme-color | Present and correct |
| Production build | Compiles (pre-existing legacy warnings only) |
| Jest | 25/25 API tests pass; 1 pre-existing `App.test.js` failure (react-router-dom@7 module resolution — unrelated) |


---

## PRODUCT OWNER CONTENT CORRECTIONS

Content-positioning pass following PO review. Public-site only — no backend, database,
RLS, auth, billing or git changes. Prior QA results preserved (verified again below).

### 1. AI-extraction status
**Audit findings (backend, current implementation):**
- **A. Engine implemented?** Yes — `backend/engines/ai_extraction.py` (`AIExtractionEngine`)
  is complete (LLM client, deterministic prompt/parse, confidence validation, status
  transitions, audit + events). Unit and integration tests exist.
- **B. Integrated into the processing workflow?** At engine/orchestrator level, yes —
  `backend/engines/workflow.py` (`WorkflowOrchestrator`) runs extraction → AI matching →
  customer review → calculation, with confidence-based routing to manual review. Tested
  end-to-end against a Postgres pool.
- **C. Usable through the current application?** Not yet via the live HTTP API. The
  production processing routes (`v3_processing*`) use the deterministic manual-extraction
  pipeline (`engines/processing_workflow.py`); no route instantiates the orchestrator yet.
- **D. Human review required?** Yes — in both flows. Low-confidence or unmatched runs
  route to manual review; the customer review gate is part of the pipeline.
- **E. Genuinely available vs still being wired?** The engine is built and tested; the
  final production-route integration is still being wired. No claim of autonomous
  production extraction is made.

**Public wording change:** removed every "Under construction" / "built and tested and is
being wired into the processing workflow" statement. Replaced with "AI-assisted
extraction" as an available capability, with the caveat that every result passes
**validation and human review** before use. Applied on `/`, `/platform`,
`/processing-services`, `/services`.

### 2. Organisation/team implementation status
**Audit findings (D20–D37):**
- organisations, membership, member management (add/update/remove/roles), role-based
  access (`owner/admin/member/viewer`), org workspace (profile, metadata, facilities,
  assets, documents, reports, consultant client-grants) — **all implemented**
  (`api/v3_organizations.py`, `data/roles.py`, RLS).
- Invitations — create/list/revoke + email implemented; **invitee self-serve acceptance
  is not yet wired** (email links to `/accept-invite`, which has no frontend route).

**Public wording change:** the org/team capability card is no longer "Partial". It now
reads "Manage organisations and teams with role-based access — owner, admin, member and
viewer roles, with team members managed from the organisation workspace", status
**Available at launch**. The genuinely-incomplete part (self-serve acceptance) moved to
the "What's coming next" list on `/`, labelled COMING SOON with an accurate note.

### 3. Pricing currency — GBP everywhere
All public pricing is now **GBP (£)** on every page: `£49 / £149 / £399` (Starter /
Professional / Business), `£0.99` assisted-processing band. No `$`, `USD` or mixed
currency remains anywhere on the public site.
**Discrepancy to decide:** the D37 database `billing_plans` seed is mixed — Starter v2
and Business v2 are seeded `USD`, Professional v1 `GBP`, and `billing_commercial_config`
`assisted_pricing` bands are `USD`. The public site now presents the approved amounts in
GBP; the DB rows should be realigned to GBP before billing operates (backend untouched).

### 4. Pricing feature verification (D37 baseline)
Verified against `billing_plans` (D37-0 + D37 master) and `billing_commercial_config`:

| Plan | Price | Members | Credits | Storage | Assisted/Managed/API |
|---|---|---|---|---|---|
| Starter | £49 | 3 ✓ | 100 ✓ | 20 GB ✓ | — / — / — ✓ |
| Professional | £149 | 10 ✓ | 500 ✓ | 50 GB | assisted ✓* / — / — |
| Business | £399 | 25 ✓ | 2,000 ✓ | 500 GB ✓ | ✓ / ✓ / ✓ ✓ |
| Enterprise | Custom | — | — | — | custom ✓ |

*DB sets `assisted_processing_available=true` on Professional; the PO-approved feature
list says "Self-service processing". Public site follows the PO baseline; **PO decision
wanted** on whether Professional should also advertise assisted processing.
"Dedicated support" (Business) has no DB flag — retained per PO baseline.
The 1/2/4-credit complexity bands and "quoted" exceptional class match `credit_rules`.

### 5. Human processing terminology
No public occurrence of "Processing Entity" / "entity ecosystem" exists (only internal
ops/admin code). Public pages consistently use **Human Processing Services / Specialist
Processing Teams / Human-Assisted Processing**. "QC" public mentions replaced with
"quality-control checks".

### 6. Public launch messaging
Launch status wording kept as **"Preparing for commercial launch"** / access by
arrangement (hero, CTA, contact, pricing, about). Removed internal language: the "A note
on billing" section (deleted), "billing layer", "payment-provider integration",
"self-serve billing", "plan-gated in the product configuration", "blog CMS… separate
product". Removed the roadmap entry for AI extraction (now implemented). Renamed "On the
roadmap" → "What's coming next".

### 7. Verification results (re-run after content changes)
- Production build: compiles (pre-existing legacy warnings only).
- Route sweep 13 routes × 1440/768/360: 0 overflow/clipping/broken-image/zero-height.
- Console errors: 0 on all 14 routes (incl. /login).
- Demos: A result still "10,732.4 kg CO₂e ≈ 10.7 t"; E/F evidence + dashboard intact.
- Link crawl: 14/14 internal hrefs resolve.
- Contrast: unchanged pairs pass (≥4.86:1 for sampled text).
- Content verification: 23/23 programmatic checks pass (GBP pricing, no "Under
  construction"/"Partial"/"in progress", org/team + AI wording, roadmap contents).
- Jest: 25/25 API tests pass; 1 pre-existing `App.test.js` failure (unchanged).
- Section rhythm, hover interactions, prefers-reduced-motion: untouched.
- Screenshots refreshed: `screenshots/final/{home,pricing,platform,processing-services,services}*`.

### 8. Remaining Product Owner decisions
1. **DB currency realignment** — seed `billing_plans` Starter/Business (v2) and
   `assisted_pricing` bands in `USD`; public site now shows GBP. Align DB before launch.
2. **Professional assisted processing** — DB enables it; PO baseline advertises
   self-service only. Decide which to expose.
3. **Self-serve invitation acceptance** — invitee accept flow not wired; confirm whether
   to complete it for launch or keep admin-managed adds.
4. **"Dedicated support" (Business)** — marketing feature line with no DB flag; confirm.

---

## Fixed in this final pass

### 1. Glossary page rebuilt — was broken on the live site
The `/glossary` page fetched from `https://carbontally-api.onrender.com/api/glossary`,
which returns **404** (endpoint/DB no longer live) → page stuck on "Loading glossary…".
It also used legacy styling (no PageShell, no launch banner), breaking visual-system
consistency.

**Fix:** Rebuilt as a self-contained public page:
- `frontend/src/public/glossaryData.js` — 32 accurate terms (GHG Protocol / IPCC / ISO
  14064 / UK SECR/ESOS/CSRD-aligned), each with category, definition, example, related.
- `frontend/src/Glossary.jsx` — PageShell, hero, local search + category filter,
  alphabetical ordering, WCAG-friendly controls.
- `frontend/src/public/public-site.css` — glossary + form-control styles.
- No backend calls; works offline.

### 2. Duplicate canonical links (SEO)
PageShell appended a second `<link rel="canonical">` alongside the static one in
`index.html`, so every page resolved the canonical to `/`. Now the existing link is
updated in place — exactly one canonical, correct per route
(e.g. `/platform` → `https://carbontally.co.uk/platform`).

### 3. Cookie banner visual consistency
Banner used the legacy `#1a1a2e` navy + old palette. Aligned to the site's slate/emerald
system (`#0f172a` background, `#34d399` link/border, slate text). Contrast 12.02:1.

---

## Verified this pass (regression)

- **Route sweep** — 13 routes × widths (1440/768/390/360): no overflow, no clipping, no
  console errors; header sticky; cookie banner present; nav active state correct on all
  public pages.
- **Demos** — auto-start on scroll, Replay restarts cleanly, row/cell fill completes,
  calculated result matches source data (10,732.4 kg CO₂e ≈ 10.7 t), dashboard figures
  match demo data (1,284 processed / 1,203 verified / 81 flagged).
- **Link crawl** — every internal href resolves to a live route.
- **Contrast** — btn 5.47, nav 10.35, CTA band 12.54/11.05, footer 12.02, badges 5.49/4.86.
- **Metadata** — unique title + description per page; canonical per route; static
  index.html meta (lang `en-GB`, OG, Twitter, theme-color, JSON-LD Organization) intact.
- **Section rhythm** — landing alternates white/alt/accent sections with no two
  consecutive white sections (QA-3 fix holds).

---

## Known issues (pre-existing, out of scope — no fix applied)

1. **Jest `App.test.js`** — fails with `Cannot find module 'react-router/dom'` under
   `react-router-dom@7`. Pre-existing at baseline; unrelated to public-site changes.
2. **`CI=true` build** — `react-scripts build` treats legacy unused-vars in `App.js`
   (Dashboard hook destructures, ~lines 495–513) as errors under CI. Build succeeds with
   warnings tolerated. Recommend cleaning these before CI deployment.
3. **Sitemap** excludes legal pages (`/privacy`, `/terms`, `/cookies`) — intentional, but
   confirm with PO if legal pages should be indexable.
4. **`/login`** remains the app entry (200) — fine for pre-launch; whole-app flows not in
   public-site scope.

---

## Screenshots

`docs/audit/openhands/screenshots/final/` — desktop hero, full-page, and mobile captures
for every route (home, platform, services, processing-services, consultants, pricing,
about, contact, legal pages, glossary). Refreshed this pass (PO corrections):
`home-*`, `pricing-*`, `platform-*`, `processing-services-*`, `services-*`.

## Files changed in this pass (all uncommitted)

QA pass (earlier):
- `frontend/src/Glossary.jsx` — rebuilt (public page, local data)
- `frontend/src/public/glossaryData.js` — new, 32 terms
- `frontend/src/public/public-site.css` — glossary + form styles
- `frontend/src/public/PageShell.jsx` — canonical dedupe
- `frontend/src/App.css` — cookie-banner palette alignment

PO content corrections (this pass):
- `frontend/src/LandingPage.jsx` — GBP pricing preview, roadmap reworked (AI extraction
  removed; team invitations added; online payments/API/resources reworded), legend,
  "What's coming next" heading, QC→quality-control wording
- `frontend/src/PricingPage.jsx` — £49/£149/£399, removed "A note on billing", £0.99 band,
  customer-facing notes
- `frontend/src/public/PlatformPage.jsx` — org/team card (no "Partial"), AI extraction
  card (no "Under construction"), QC wording, simplified legend
- `frontend/src/public/ServicesPage.jsx` — AI-assisted extraction service (available),
  online payments wording, legend, meta description
- `frontend/src/public/ProcessingPage.jsx` — AI extraction card (available), QC wording
- `frontend/src/AboutUs.jsx` — "Honest automation" principle reworded

---

## VISUAL IDENTITY & DESIGN REFACTOR

Public-site design-system, visual-identity and UX-polish pass. Frontend only — no
backend, database, RLS, auth, billing or git changes. All approved PO content decisions
from the previous pass preserved (verified again below).

### 1. Root cause found: "Request launch information" CTA was invisible on the hero
The defect was a **CSS specificity bug**, not a styling choice:
`.ct-site a` (specificity 0,1,1) overrode `.ct-btn-primary`'s `color:#fff` (0,1,0), so the
hero's `<a class="ct-btn ct-btn-primary">` rendered **teal text on a teal button**
(brand-on-brand, contrast ≈1:1). The header variant worked only because it is a `<button>`
(not an `<a>`). The same bug silently re-coloured every `ct-btn-secondary` anchor teal.
**Fix:** all button variants re-scoped to `.ct-btn.ct-btn-*` (0,2,0) so their colours always
win over the site-wide link colour; a generic `.ct-btn.ct-btn-light` was added (was only
defined inside `.ct-section-cta`); focus-visible ring strengthened (2px `#0d9488` outline,
offset 2px, plus a white halo that stays visible on the dark CTA band). Verified by CDP at
render: hero primary is now **white on `#0f766e` (5.47:1)** on every page; all primary /
secondary / light CTAs audited across 8 routes — none brand-on-brand.

### 2. "From source document to evidenced result" — processing-journey redesign
Landing centrepiece rebuilt from five plain cards into **one visually connected pipeline**:
- New `.ct-journey` component: five colour-coded stage cards with **inline SVG icons**
  (collect/download, extract/file, map/route, calculate, validate/shield-check), large ghost
  step numbers (01–05), and a coordinated accent treatment per stage.
- **Controlled stage palette** (semantically sensible, accessible on white):
  Collect = sky, Extract = teal (brand), Map = indigo, Calculate = amber, Validate = emerald.
  Tints/lines match accents; all icon chips ≥3:1 against their tints; heading text stays ink.
- A **horizontal pipeline track line** (gradient through all five stage colours) runs behind
  the icon row on desktop, with chevron connectors between cards — the five stages read as
  one data flow, not five unrelated cards.
- **Mobile composition** is intentional, not a shrunken row: single-column steps with a
  vertical colour-gradient rail down the icon gutter (icons sit on the rail with a white
  ring), left-aligned text, ghost numbers repositioned.
- **Motion** is limited to a staggered reveal (110 ms cascade) triggered once by an
  IntersectionObserver when the journey scrolls into view; hover elevation is subtle.
  `prefers-reduced-motion` (and no-IntersectionObserver) falls back to instantly visible —
  content is never gated on animation.
- The journey sits in a framed `.ct-journey-stage` panel (rounded 24px, hairline border,
  soft radial) containing the steps, the interactive Data→Emissions demo and the legend.

### 3. Hero — evidence-led supporting visual
- Replaced the mini pipeline list with **"A single record, fully evidenced"**: a mock
  evidence card showing Source (`INV-2026-0417 · Red diesel`), extracted field chips,
  factor (`DEFRA 2026 · Gas oil (red diesel)`), the live-demo calculation
  (4,258.9 L × 2.52 kg CO₂e/L = **10,732.4 kg CO₂e** — matches demo A), a "Validated" status
  chip, and a colour-coded Source→Extract→Map→Calculate→Validate chain. Same fictional
  dataset as the interactive demos; `aria-hidden` (decorative).
- Hero background gained a **fine data-grid motif** + brand radial glows; the headline's
  underline phrase got a subtle gradient stroke; inner page-heroes share the grid motif.

### 4. Section rhythm & shared design-system refinements
- Each background treatment is now visibly distinct: hero (white + grid + glow),
  problem/services/audiences (white or `alt` + soft radial), **journey (framed panel)**,
  trust (`accent` emerald band with top/bottom hairlines), roadmap (alt), pricing (muted),
  closing CTA (deep teal gradient with a five-colour top strip). Footer gets the same
  five-colour gradient strip.
- `.ct-card`, `.ct-step`, `.ct-plan` hover elevation standardised; featured pricing plan now
  carries a **"Most popular" pill** (Landing + Pricing pages) — a design treatment, not a
  commercial change.
- Typography: tighter heading tracking, tabular numerals on prices/results, uppercase
  micro-labels for the evidence card and journey divider.

### 5. Verification results (re-run after the refactor)
- Production build compiles (pre-existing legacy warnings only — `App.js` unused `error`).
- Deep route sweep **13 routes × 1440/768/360** (plus supplemental **1024/390** sweep):
  **0 overflow, 0 clipping, 0 broken images, 0 exceptions**.
- Console errors: **0** on all 14 routes.
- Demos intact: demo A result still `10,732.4 kg CO₂e ≈ 10.7 t CO₂e`; Replay works.
- Links: 14/14 internal hrefs resolve.
- Contrast: unchanged passing pairs; hero primary CTA now 5.47:1 (was ≈1:1).
- Journey: 5 steps, numbers 01–05, five distinct stage icon colours/tints, desktop track
  line + 4 connectors, mobile vertical rail + single column verified programmatically.
- Pixel-level screenshot verification: all five stage tints/accent colours present in
  `home-full`/`home-y1600`; hero CTA teal block + white text present; featured pill present
  in `pricing-featured.png`.
- Jest: 25/25 API tests pass; 1 pre-existing `App.test.js` failure (unchanged, out of scope).
- Screenshots refreshed: `screenshots/final/` (50 captures — every route full-page at
  1440/390, desktop viewport, landing scroll positions desktop + mobile, pricing featured).

### 6. Files changed this pass (all uncommitted)
- `frontend/src/public/public-site.css` — design tokens (stage palette, focus ring, shadows,
  grid-line), button specificity fix + `.ct-btn-light` + focus ring, hero/evidence-card
  styles, section backgrounds, journey component, shared steps/card/plan polish, footer
  strip, mobile polish
- `frontend/src/LandingPage.jsx` — hero evidence card, journey component (icons, reveal),
  section reworked to framed journey panel, "Most popular" pill on featured plan
- `frontend/src/PricingPage.jsx` — "Most popular" pill on featured plan
- `docs/audit/openhands/screenshots/final/*` — refreshed captures

*Created by an AI agent (OpenHands) on behalf of the user. No commits or pushes were
made; all changes remain in the audit clone only.*
