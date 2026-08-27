# CarbonTally V3 — Public Website Pre-Launch Refactor Report

**Audit target:** `shomonrobie/CarbonTally` @ `9458067c073bdaedae2a621b9cee42e419f14a75`
**Working copy:** `CarbonTally_audit` (read-only audit; detached HEAD unchanged; no commits, no pushes)
**Task:** Second pass — Product Owner requirements for the pre-launch public website:
(1) interactive product demos built from the real `CarbonTallyDemo.jsx` + backend workflows,
plus terminology/audience/status hardening across all public pages.
**Mode executed:** Research → Design → Implement → Verify
**Agent:** OpenHands + DeepSeek V4 Flash
**Date:** 2026-08-25
**Server:** dev server running at `http://localhost:3006` (all 13 routes return 200)

First-pass pre-launch refactor report: `CARBONTALLY_V3_WEBSITE_PRELAUNCH_REFACTOR_REPORT_FLASH.md`.
Flash audit report: `CARBONTALLY_V3_INDEPENDENT_PRODUCT_PLATFORM_AUDIT_FLASH.md`.

---

## 1. Executive summary

This pass delivers the interactive demo layer for the pre-launch website and hardens
the public-facing copy so the site reads as a professional full-service offering
without overclaiming.

1. **Six interactive product demos** are built and wired into the public pages. They are
   entirely client-side (React + CSS transitions), use one coherent fictional dataset
   (Aurora Foods Ltd), and mirror the real backend pipeline (extraction → mapping →
   validation → calculation → review → approval) plus evidence traceability and the
   reporting dashboard.
2. **Terminology refactor** — the internal term "Processing Entity" has been replaced
   with customer-facing language ("human processing services", "specialist processing
   teams") across every public page, header, footer and meta description.
3. **Audience segmentation** — the homepage and About page now present four audiences
   (individuals & sole traders; small & growing businesses; organisations; consultants
   & advisers), matching the D37 plan ladder (Starter → Enterprise).
4. **Honest status labels** — AI-assisted extraction is now labelled **Under
   construction** (it exists and is being wired in) rather than "Future — product
   decision required"; every page's status legend and roadmap stay consistent.
5. **Verification** — production build passes; all 13 routes return 200; every demo was
   exercised end-to-end in a real browser (auto-start on scroll, staged animation,
   completion, Replay); no console errors. Frontend tests: 25 pass (`api.test.js`);
   `App.test.js` keeps its pre-existing failure (unrelated to this work).

---

## 2. Product Owner requirement (1) — INTERACTIVE PRODUCT DEMOS

### 2.1 Approach

- **Reference:** the old in-app demo `frontend/src/components/CarbonTallyDemo.jsx`
  (1176 lines; MUI/styled-components; `MOCK_CSV_DATA`; `ExecutiveDashboard`). It was
  a single-screen, MUI-heavy widget tied to a fake CSV dataset — not reusable for a
  public marketing site.
- **Redesign:** a shared demo infrastructure (`demoCore.jsx`, `demoData.js`, `demos.css`)
  and six small demo components. Each demo is: static to start, staged with
  transitions, auto-starts on scroll into view (IntersectionObserver), respects
  `prefers-reduced-motion`, and exposes a Replay control when finished.
- **Fidelity to the real product:** every demo step is grounded in actual backend code
  (see the mapping table in §2.3). Data values are fictional but plausible and
  internally consistent — one invoice line is carried through demos A, C, D, E and F so
  the narrative is traceable across the whole site.

### 2.2 Demo inventory (A–F)

| ID | Demo | Page(s) | Stages (run) | What the visitor sees |
| --- | --- | --- | --- | --- |
| A | **Data to Emissions** (one messy line, end-to-end) | Home — pipeline section | Raw record → Cleaned → Activity → Factor → Calculated | A scanned invoice line (`RED DIESEL… 4,258.9 L`) is cleaned, classified as an activity, matched to a DEFRA factor and calculated (`10,732 kg CO₂e ≈ 10.7 t CO₂e`), with a snapshot reference |
| B | **Document Extraction** | Processing — "See extraction and review in action" | Document → Extraction → Fields detected → Structured → Review | A fictional invoice becomes structured fields (date, description, site, fuel, quantity, unit) with per-field confidence scores and a review state |
| C | **Factor Mapping** | Platform — "See factor mapping in action" | Activity → Candidates → Selected → Calculated | Candidate emission factors with source (DEFRA 2026, 2023-24) and confidence; selection is explained and the calculation shown |
| D | **Human Review / QC** | Services — "Human processing services, explained" | Extracted → Confidence → Needs review → Reviewed → Approved | Validation findings (unit inconsistency, abbreviated activity, inferred reporting year), reviewer checks, resolution and approval |
| E | **Evidence Traceability** | Home — trust section ("Trace one number back to its source") | Number → Calculation → Factor → Extracted line → Document | The result `10.7 t CO₂e` is traced backwards through its calculation snapshot, factor, extracted line and source document |
| F | **Dashboard / Reporting** | Home — "From processed records to a reportable result" | Records → Scopes → Categories → Trend | Records/verified/flagged stats, Scope 1–3 totals, a by-category breakdown and a monthly trend chart (recharts) built from the approved dataset |

### 2.3 Demo → real-backend mapping (evidence)

| Demo step | Real implementation in repo |
| --- | --- |
| Document upload → org-scoped storage, signed URLs | `frontend/src/supabaseClient.js`; `domain/storage.py` (private org-scoped storage, signed URLs) |
| Extraction (human-in-the-loop) | `domain/work_items.py` (`extraction` status); `engines/ai_extraction.py` (AI-assisted extraction engine, built & tested) |
| Cleaning / normalisation | `engines/validation.py` (cleaning + validation rules) |
| Activity classification | `domain/facilities.py`, `domain/activity_types.py` |
| Factor matching with candidates + confidence | `engines/factor_matching.py` (candidate factors, scores/provenance); `domain/emission_factors.py` |
| Calculation with snapshots | `engines/calculation.py` (`CalculationSnapshot`); `domain/emission_records.py` (snapshot v1.0) |
| Validation findings | `engines/validation.py` (flag + resolution workflow) |
| Customer review / approval gates | `domain/work_items.py` (`needs_review`, `approved`); `v3_processing_workflow.py` |
| Evidence traceability (result → document) | `docs`/`domain/evidence.py` (D33.1 evidence bundle model: document → page → line → factor → calculation) |
| Reporting dashboard (scopes, categories, trend) | `domain/reporting.py`, `frontend/src/v3/reporting/*`; recharts used app-wide |

### 2.4 Animation & interaction inventory

All demos share `demoCore.jsx` (`useDemoRun`, `useInView`, `useAutoStart`,
`useCountUp`, `usePrefersReducedMotion`) and `DemoFrame`/`DemoControls` (Run /
Replay, step counter). Interactions:

- Auto-start on scroll into view (IntersectionObserver, threshold 0.3); manual Run button.
- Staged step progression with CSS class swaps (`is-active`, `done`, `filled`) — no JS
  animation library; `demos.css` (786 lines) covers all six demos.
- Per-field confidence badges (B), candidate-factor rows with match bars (C), findings +
  check list (D), reverse chain reveal (E), count-up stats and recharts bar/trend (F).
- Replay resets and re-runs; reduced-motion users get static completed states.

### 2.5 Accessibility & honesty constraints

- All demos are **fully static without JavaScript interaction** (content is in the
  markup; scripts only sequence reveals), so the site works with JS disabled.
- ARIA labels on each demo's key region; `prefers-reduced-motion` honoured.
- Every demo is clearly marked as a demonstration with fictional data
  ("fictional invoice", "Same fictional dataset, one narrative…") — no fabricated
  customer figures are presented as real.
- Nothing is uploaded: all data is bundled in `demoData.js`.

### 2.6 Files created

```
frontend/src/public/demos/
  demoCore.jsx          (151 lines)   hooks + frame/controls
  demoData.js           (155 lines)   one coherent fictional dataset
  demos.css             (786 lines)   all demo styling
  DataToEmissionsDemo.jsx             (86 lines)
  DocumentExtractionDemo.jsx          (70 lines)
  FactorMappingDemo.jsx               (78 lines)
  HumanReviewDemo.jsx                 (78 lines)
  EvidenceTraceabilityDemo.jsx        (60 lines)
  DashboardDemo.jsx                   (115 lines)
```

### 2.7 Files wired

| File | Change |
| --- | --- |
| `frontend/src/App.js` | import `demos.css` |
| `frontend/src/LandingPage.jsx` | demos A, E, F + "one messy line" intro + "trace one number" intro + dashboard section |
| `frontend/src/public/PlatformPage.jsx` | demo C ("See factor mapping in action") |
| `frontend/src/public/ServicesPage.jsx` | demo D ("Human processing services, explained") |
| `frontend/src/public/ProcessingPage.jsx` | demo B ("See extraction and review in action") |

---

## 3. Terminology refactor (Processing Entity → public language)

The internal model uses a `processing_entity` / `staff_profile` role for specialist
data-operations teams. This is internal terminology and was leaking into public copy.
All public pages now use customer-facing wording:

| Internal / old public | New public wording |
| --- | --- |
| Processing Entity / Processing Entities | human processing services; specialist processing teams |
| "vetted Processing Entity network" | "specialist teams that can help prepare, extract, structure and review" |
| "strictly isolated, mediated access" | "controlled access"; "structured communication through the platform" |
| "Processing Entity ecosystem" (Services category) | category renamed **Human processing services** |
| "Processing Entity data isolated…" | "customer, consultant and specialist processing teams are isolated…" |

Files updated: `LandingPage.jsx`, `public/PlatformPage.jsx`, `public/ServicesPage.jsx`,
`public/ProcessingPage.jsx`, `AboutUs.jsx`, `public/PageShell.jsx` (checked; clean).
Verified via `grep` — no remaining `Processing Entit*`, `entity_id`, `staff_profile`,
`entity-scoped` or "mediated" in any public-facing file.

---

## 4. Audience segmentation

The homepage "Built for everyone in the middle of carbon data" section and the About
page "Who CarbonTally serves" section now present four audiences aligned with the D37
plan ladder:

| Audience | Plan fit (per D37) |
| --- | --- |
| Individuals & sole traders | Starter (3 members, 100 credits) |
| Small & growing businesses | Professional / Business |
| Organisations | Business / Enterprise |
| Consultants & advisers | Consultant workspace (multi-client, white-label) |

---

## 5. Status-label hardening (AI-assisted extraction)

| Old label | New label | New copy |
| --- | --- | --- |
| "Future — product decision required" / "FUTURE" | **UNDER CONSTRUCTION** | "An AI-assisted field-extraction engine is built and tested and is being wired into the processing workflow. Until then, extraction runs with human review." |

Applied consistently across: homepage roadmap table, `PlatformPage.jsx` capabilities,
`ServicesPage.jsx` catalogue and `ProcessingPage.jsx` automation section. The status
legend is unchanged (`Available at launch` / `Under construction` / `Future`).

---

## 6. Verification results

| Check | Result |
| --- | --- |
| Production build (`npm run build`) | ✅ Passed — demo content confirmed in `main.*.js` bundle |
| Route scan (13 public routes, production bundle) | ✅ All `200` |
| Frontend tests (`CI=true npm test`) | ✅ `api.test.js` 25/25 pass; ⚠️ `App.test.js` pre-existing failure (react-router-dom@7 module resolution under Jest — unrelated, see §7 of first-pass report) |
| Real-browser demo run (A, B, D, E, F) | ✅ Auto-start on scroll; staged animation; completion state + Replay; no console errors |
| Recharts dashboard chart (F) | ✅ Renders with data in a real browser (monthly labels + series values) |
| Headless DOM (all pages) | ✅ Demo frames, section headings, terminology, statuses present |
| Screenshots | `docs/audit/openhands/screenshots/v2/{home,platform,services,processing-services}.png` |

---

## 7. Remaining Product Owner requirements

Requirement (1) INTERACTIVE PRODUCT DEMOS is complete and verified. The remaining
sections of the second-pass brief (items 2+) were referenced in the task context but
their full text was not present in this session's input — they remain **pending** and
should be re-supplied to continue. Known open items from the first pass (still valid):

- ISO 27001 / SOC 2 references in unrouted `src/DataSecurity.jsx` (deferred).
- Legal review of Terms / Privacy / Cookies before launch.
- Payment-provider integration before online checkout can operate (COMING SOON).
- `App.test.js` pre-existing Jest failure.

---

## 8. Version-control status

- No commits or pushes made. HEAD remains `9458067c073bdaedae2a621b9cee42e419f14a75`
  (detached; `origin/main` unchanged).
- Modified (first pass, uncommitted): the 14 pre-launch refactor files plus untracked
  `frontend/src/public/`, `frontend/public/sitemap.xml`, `docs/audit/openhands/`.
- Second pass adds: `frontend/src/public/demos/*` (new, untracked) and further edits to
  `App.js`, `LandingPage.jsx`, `AboutUs.jsx`, `public/PlatformPage.jsx`,
  `public/ServicesPage.jsx`, `public/ProcessingPage.jsx`.
