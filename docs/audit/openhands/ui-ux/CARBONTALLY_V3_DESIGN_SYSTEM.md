# CarbonTally V3 — Design System Specification (D21)

| | |
|---|---|
| Document type | Design system (authoritative, implements D21 + D21.1–D21.9) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | AUTHORITATIVE (UX phase) — does not contradict D21 |
| Date | 2026-08-24 |
| Basis | Actual CarbonTally design tokens and frontend implementation (`frontend/src/index.css`, `frontend/src/App.css`, `frontend/src/v3/v3.css`, `frontend/src/v3/ops/ops.css`, `frontend/src/v3/admin/admin.css`, `frontend/src/v3/consultant/consultant.css`, `frontend/src/v3/reports/reports.css`) |

## 1. Principle

One unified visual design system across public website, customer, consultant,
Processing Entity, CarbonTally Staff and CarbonTally Admin (D21). Role
interfaces differ in information density and workflow presentation but remain
recognisably one product. **Extend the existing CarbonTally identity — do not
invent an unrelated visual identity.**

Legend: EXISTING / ALIGNED = token already exists and matches · INCONSISTENT =
exists in conflicting variants · MISSING = absent · TARGET REQUIRED = must be
defined.

## 2. D21.1 — Colour

### 2.1 Existing token inventory (evidence)

| Token (semantic) | Current value(s) | Location | Classification |
|---|---|---|---|
| primary | `#2f855a` (v3) vs `#2d6a4f` (App.css) | v3.css / App.css `:root` | **INCONSISTENT** — two greens |
| primary-dark / hover | `#276749` (v3) vs `#1b4332` (App.css) | v3.css / App.css | INCONSISTENT |
| primary-light | `#52b788` | App.css `--primary-light` | EXISTING / ALIGNED |
| secondary/accent | `#2b6cb0` (blue used in notes) · `#1e40af` consultant badge · `#2563eb` App.css `--blue` | v3.css / App.css | INCONSISTENT (several blues) |
| background | `#f7fafc` (v3 shell) / `#f8fafc` (App gray-50) | v3.css / App.css | EXISTING / ALIGNED (near) |
| surface | `#ffffff` | v3.css `.v3-card` etc. | EXISTING / ALIGNED |
| elevated surface | white + shadow (`box-shadow: 0 20px 50px rgba(0,0,0,0.25)`) | v3.css `.v3-modal` | EXISTING / ALIGNED |
| primary text | `#1a202c` (v3) vs `#1e293b` (App gray-800) | v3.css / App.css | INCONSISTENT |
| secondary text | `#4a5568` | v3.css | EXISTING / ALIGNED |
| muted text | `#718096` | v3.css | EXISTING / ALIGNED |
| border | `#e2e8f0` (v3) vs `#cbd5e1` (App gray-300) | v3.css / App.css | INCONSISTENT |
| focus | `border-color #2f855a + box-shadow 0 0 0 2px rgba(47,133,90,0.15)` | v3.css | EXISTING / ALIGNED |
| success | `#c6f6d5` bg / `#22543d` text; `#276749` result text | v3.css | EXISTING / ALIGNED |
| warning | `#fefcbf` bg / `#744210` text; `#fffaf0`/`#fbd38d`/`#975a16` notes | v3.css | EXISTING / ALIGNED |
| error | `#fed7d7` bg / `#822727`; `#fff5f5`/`#feb2b2`/`#9b2c2c` | v3.css | EXISTING / ALIGNED |
| information | `#ebf8ff` bg / `#90cdf4` border / `#2b6cb0` text | v3.css `.v3-note` | EXISTING / ALIGNED |
| pending | `#fefcbf` / `#744210` | v3.css `.v3-status.pending` | EXISTING / ALIGNED |
| processing / in-progress | `#bee3f8` / `#2b6cb0` (generating) | v3.css | TARGET REQUIRED (map to states) |
| review | amber family (pending-like) | — | TARGET REQUIRED |
| approved | green family (`#c6f6d5`/`#22543d`) | v3.css | EXISTING / ALIGNED |
| rejected | red family (`#fed7d7`/`#822727`) | v3.css | EXISTING / ALIGNED |
| correction required | amber family | — | TARGET REQUIRED |
| disabled | `opacity: 0.5; cursor: not-allowed` | v3.css | EXISTING / ALIGNED |
| evidence / traceability | `#e3f6e8`/`#1b7f3b` complete · `#fdf3e3`/`#9a6b1f` partial · `#f1f1f1`/`#666` unavailable | v3.css (D33.1) | EXISTING / ALIGNED |
| navigation (dark rail) | `#0f172a` bg / `#e2e8f0` text / active `rgba(255,255,255,0.14)` | v3.css `.v3-nav` | EXISTING / ALIGNED |
| brand tag | `#2f855a` bg white text | v3.css `.v3-nav-tag` | EXISTING / ALIGNED |

### 2.2 Target semantic palette (single source of truth)

| Semantic token | Target value | Maps to |
|---|---|---|
| `ct-color-primary` | `#2f855a` (adopt v3; migrate App.css `--primary` → token) | primary buttons, active nav, links, focus |
| `ct-color-primary-hover` | `#276749` | hover |
| `ct-color-primary-soft` | `#f0fff4` / `#c6f6d5` | success-ish surfaces |
| `ct-color-accent` | `#2b6cb0` | information, secondary emphasis, links-alt |
| `ct-color-bg` | `#f7fafc` | app background |
| `ct-color-surface` | `#ffffff` | cards, panes, modals |
| `ct-color-border` | `#e2e8f0` | borders, dividers |
| `ct-color-text` | `#1a202c` | primary text |
| `ct-color-text-secondary` | `#4a5568` | secondary |
| `ct-color-text-muted` | `#718096` | muted, metadata |
| `ct-color-focus` | `2px rgba(47,133,90,0.15)` ring + `#2f855a` border | focus visible |
| `ct-color-success` | `#c6f6d5` / `#22543d` | completed, approved, qc_approved |
| `ct-color-warning` | `#fefcbf` / `#744210` | pending, review, correction required |
| `ct-color-error` | `#fed7d7` / `#822727` | failed, rejected |
| `ct-color-info` | `#ebf8ff` / `#2b6cb0` | information, processing, in_progress |
| `ct-color-nav` | `#0f172a` / `#e2e8f0` | top nav rail |
| `ct-color-evidence-complete` | `#e3f6e8` / `#1b7f3b` | evidence Complete |
| `ct-color-evidence-partial` | `#fdf3e3` / `#9a6b1f` | evidence Partial |
| `ct-color-evidence-unavailable` | `#f1f1f1` / `#666` | evidence Unavailable |
| `ct-color-disabled` | `opacity 0.5` | disabled |

**Rule: status never relies on colour alone** (D21.4) — always paired with text
and (where practical) an icon.

## 3. D21.2 — Typography

| Element | Target | Current evidence | Classification |
|---|---|---|---|
| Font family (UI) | System stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` | Used in v3.css, admin.css, consultant.css, reports.css, App.css, index.css | EXISTING / ALIGNED |
| Monospace | `ui-monospace, SFMono-Regular, Menlo, Consolas, 'Courier New', monospace` | v3.css `.v3-mono`, `.v3-formula`; reports.css | EXISTING / ALIGNED |
| Heading hierarchy | h1 26px/700 (`v3-page-header h1`); h2 16px/600 (card); h3 15px/600 (pane); modal h2 18px/700; admin h1 24px/700 | v3.css/admin.css | EXISTING / ALIGNED |
| Body | 14px; color `#1a202c` | v3.css | EXISTING / ALIGNED |
| Labels | 12px/600 `#4a5568` | v3.css `.v3-form-group label` | EXISTING / ALIGNED |
| Metadata | 12–13px muted `#718096`; uppercase letter-spaced stat labels | v3.css | EXISTING / ALIGNED |
| Table typography | th 12px uppercase `#718096`; td 14px | v3.css `.v3-table` | EXISTING / ALIGNED |
| Numerical / emissions figures | 26px/700 stat values; mono for formulas/IDs | v3.css | EXISTING / ALIGNED |
| Helper text | 12px `#718096` | v3.css `.v3-form-hint`, `.v3-muted` | EXISTING / ALIGNED |
| Error text | 14px `#9b2c2c` on `#fff5f5` | v3.css `.v3-error` | EXISTING / ALIGNED |
| TARGET REQUIRED | Type scale token set (`--ct-type-*`) for consistency across all surfaces | — | TARGET REQUIRED |

## 4. D21.3 — Iconography

- **Actual icon library:** no icon library is imported. The V3 UI uses emoji
  glyphs (🌱, 🧾, 🗂️, 🧮, ⏱️, ✓, ✗, ⏻, ← →) and simple text marks.
  `recharts` provides chart elements. The public site uses emoji extensively.
- **Classification:** INCONSISTENT — emoji are used ad hoc; no semantic icon
  set.
- **Target:** adopt a single icon library (e.g. inline SVG set or lucide-style
  strokes) consistent with the CarbonTally identity, with a semantic mapping:

| Semantic | Icon |
|---|---|
| Home | house |
| Documents | file-text |
| Processing | gears / workflow |
| Emissions | leaf / co2 cloud |
| Reports | bar-chart |
| Issues | alert-triangle |
| Billing | credit-card |
| Organisation | building |
| Locations | map-pin |
| Facilities | factory |
| Assets | server / box |
| Vehicles | truck |
| Suppliers | truck-in / handshake |
| Members | users |
| Custom Factors | sliders / percent |
| Evidence | link / receipt |
| Validation | check-badge |
| Review | eye |
| Approval | check-circle |
| Rejection | x-circle |
| Settings | cog |
| Logs | scroll |
| Audit | shield |
| Notifications | bell |

**Rule: do not mix unrelated icon families.** Emoji may remain for marketing
copy but not for functional controls.

## 5. D21.4 — Status system

Reconcile the D21.4 vocabulary with the actual backend state model
(`backend/domain/partners.py`, `entity.py`, `issue.py`, `v3_reports.py`).

| D21.4 term | Backend state(s) | Visual treatment (colour + text + icon) |
|---|---|---|
| pending | item `pending`; report `pending`; subscription `pending` | warning amber + "Pending" + clock icon |
| in_progress | item `extracting|mapping|validating|calculating`; issue `in_progress`; batch `in_progress` | info blue + text + spinner/dot |
| needs_review | `customer_review` | warning amber + "Needs review" + eye icon |
| validation | `validating` | info blue + "Validating" |
| qc | batch `qc_in_progress` | info blue + "QC in progress" |
| qc_approved | item `qc_approved`; batch `qc_passed` | success green + "QC approved" |
| customer_review | `customer_review` | warning amber + "Customer review" |
| approved | item `approved` | success green + "Approved" + check icon |
| rejected | item `rejected`; batch `cancelled` | error red + "Rejected" + x icon |
| correction_required | (rework loop: mapped/extracting return) | warning amber + "Correction required" |
| completed | item/batch `completed`; report `completed`; issue `resolved/closed` | success green + "Completed" |
| failed | item/batch/report `failed` | error red + "Failed" |
| issue statuses | open/in_progress/on_hold/escalated/resolved/closed | mapped to above families |
| entity lifecycle | active/remediation/suspended/terminated | active=green; remediation=amber; suspended=amber; terminated=gray |

**Rule:** status = text label + icon + colour (never colour alone). The status
system is implemented as reusable `v3-status`/`v3-badge` components.

## 6. D21.5 — Buttons

| Type | Target | Current evidence |
|---|---|---|
| Primary | filled `#2f855a`, white text, hover `#276749` | `.v3-btn.v3-btn-primary` / `.v3-btn.primary` — EXISTING / ALIGNED |
| Secondary | white bg, `#cbd5e0` border, `#1a202c` text | `.v3-btn` default — EXISTING / ALIGNED |
| Tertiary | text/link button (underline) | `.v3-link-btn` — EXISTING / ALIGNED |
| Destructive | filled `#c53030`, white text | `.v3-btn.v3-btn-danger` — EXISTING / ALIGNED |
| Approval | primary-success variant (green) with check icon | TARGET REQUIRED (distinct from generic primary) |
| Rejection | destructive variant (red) with x icon | TARGET REQUIRED (distinct; require confirmation) |
| Icon-only | square, accessible label (aria-label) | TARGET REQUIRED |
| Loading | spinner inside/next to button, disabled while busy | `.v3-btn:disabled` + spinner — PARTIAL |
| Disabled | `opacity: 0.5; cursor: not-allowed` | EXISTING / ALIGNED |
| Confirmation | destructive/irreversible actions open a confirm (modal or inline) | `.v3-modal` exists — PARTIAL; standard confirmation pattern TARGET REQUIRED |

## 7. D21.6 — Forms

| Element | Target | Current evidence |
|---|---|---|
| Labels | 12px/600 above field | EXISTING / ALIGNED |
| Required | `*` + aria-required | TARGET REQUIRED |
| Optional | "(optional)" text | TARGET REQUIRED |
| Helper text | 12px muted below field | `.v3-form-hint` — EXISTING / ALIGNED |
| Validation | inline field errors on blur/submit | PARTIAL (backend errors surfaced; inline field validation target) |
| Errors | `#9b2c2c` text, error border | `.v3-error` — EXISTING / ALIGNED |
| Warnings | amber | `.v3-note.warn` — EXISTING / ALIGNED |
| Confidence | badge next to AI-extracted fields (0–1) | TARGET REQUIRED (D16/D19) |
| Read-only | no border / muted bg + "Read only" affordance | TARGET REQUIRED |
| Autosave | "Saving… / Saved" indicator | TARGET REQUIRED (D19 workbench) |
| Unsaved changes | warning on leave | TARGET REQUIRED |
| Disabled | opacity 0.5 | EXISTING / ALIGNED |
| Source-linked fields | link icon + highlight ↔ source document | TARGET REQUIRED (D19) |

## 8. D21.7 — Tables

| Behaviour | Target | Current evidence |
|---|---|---|
| Sorting | clickable headers + indicator | TARGET REQUIRED |
| Filtering | toolbar filters (status/date/type) | PARTIAL (API filters; UI toolbar target) |
| Pagination | paged footer | PARTIAL |
| Column visibility | toggle | TARGET REQUIRED (admin density) |
| Density | comfortable (customer) vs compact (admin) | TARGET REQUIRED |
| Row selection + bulk actions | checkboxes + bulk bar | TARGET REQUIRED |
| Status cells | badge component (D21.4) | `.v3-badge` — EXISTING / ALIGNED |
| Expandable rows | row expand | PARTIAL (batch → items expand exists) |
| Evidence links | link to evidence chain | PARTIAL |
| Contextual actions | row action menu | TARGET REQUIRED |

## 9. D21.8 — Responsive

| Surface | Desktop (≥1024) | Tablet (768–1023) | Mobile (<768) |
|---|---|---|---|
| Navigation | full top rail | rail wraps (existing flex-wrap) | rail compresses; hamburger/menu target |
| Tables | full | horizontal scroll | card list transformation target |
| Forms | multi-column grid | 1–2 columns | 1 column |
| Split panes | 40/60·50/50·60/40 | adaptive split / stacked with tray toggle | **tray-based** (Source ⇄ Data), never squeezed split (D20) |
| Drawers | right drawer | right drawer | full-screen sheet |
| Filters | toolbar | collapsible | collapsible sheet |
| Action bars | inline | wrap | pinned bottom bar |
| Evidence panels | side/by default | stacked | tabbed |
| Notifications | list | list | list with FAB target |

Current evidence: `.v3-grid-2`, `.extraction-grid`, `.workspace-grid` collapse
at ≤900px — EXISTING baseline; tray behaviour TARGET REQUIRED.

## 10. D21.9 — Accessibility

| Area | Target |
|---|---|
| Standard | WCAG 2.2 AA (target) |
| Keyboard | full keyboard operation incl. workbench (D19), modal focus trap, skip-link |
| Visible focus | `ct-color-focus` ring on all interactive elements |
| Contrast | AA contrast on text (verify against token pairs) |
| Semantic HTML | landmarks, headings hierarchy, `nav`/`main`/`section`, `th` scope |
| Screen readers | aria-labels on icon-only buttons, status regions (`aria-live`), table captions |
| Accessible forms | labels bound to inputs, error summaries, `aria-invalid` |
| Error announcements | `role="alert"` / live region |
| Icon-only controls | aria-label always |
| Modals | focus trap + restore on close |
| Tables | captions + row/col headers |
| Status without colour | text + icon + colour (D21.4) |

Current evidence: nav has `aria-label="V3 navigation"`; forms use bound
`<label>`; sandboxed iframe viewer. Overall accessibility target is a P0/P1
work item (see matrix).

## 11. Components checklist (target vocabulary)

cards (`v3-card`) · panels · drawers · modals (`v3-modal`) · alerts
(`v3-error`, `v3-note`, `v3-notice`) · notifications · status indicators
(`v3-status`, `v3-badge`) · loading (`v3-loading`/`v3-spinner`) · empty
(`v3-empty`) · errors (`v3-error`) · confirmation patterns · data
visualisation (recharts convention, consistent colours from the palette).

## 12. Migration guidance for Cline

1. Introduce CSS custom properties per §2.2 under a single `:root` token block
   (e.g. `frontend/src/v3/tokens.css`) and reference tokens from all
   `v3*`/`ops`/`admin`/`consultant`/`reports` stylesheets.
2. Migrate `App.css` primary green to the unified token (P0-9).
3. Build the status system as shared components from §5.
4. Apply the icon mapping (§4) with one icon set.
5. Follow WCAG 2.2 AA targets (§10) with keyboard + focus + contrast checks.
6. Do not change the visual identity — the palette above IS the CarbonTally
   identity; unify, don't replace.

## 13. Spacing, borders, radii and shadows (geometry tokens)

Evidence-based from the actual V3 implementation (`frontend/src/v3/v3.css`).
These are EXISTING conventions to be codified as tokens during consolidation —
nothing new is invented; values that remain undecided are marked TARGET
REQUIRED.

| Token family | Current evidence (v3.css) | Classification |
|---|---|---|
| Spacing (component padding) | `8px 12px` (nav links) · `6px 12px` (nav buttons) · `4px 12px` (org pill) · `3px 10px` (badges) · `16px 18px` (stat/summary cards) · `18px 20px` (cards) · `22px 24px` (modal) · `10px 14px` (notes/errors) · `gap: 6px` (status) | EXISTING / ALIGNED — codify as `--ct-space-*` (4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24) |
| Radii | `6px` (tags) · `8px` (buttons/inputs/notes/errors/tabs-top) · `10px` (result cards, workspace banner) · `12px` (cards, modals, stat cards, summary cards) · `999px` (pills, badges, org pill, nav badge) | EXISTING / ALIGNED — codify as `--ct-radius-*` (6, 8, 10, 12, full) |
| Borders | `1px solid #e2e8f0` (cards, table header) · `1px solid #cbd5e0` (inputs) · `1px dashed #cbd5e0` (inline cards) · status border colours per §2.1 | EXISTING / ALIGNED |
| Shadows | `0 1px 3px rgba(0,0,0,0.2)` (inputs) · `0 2px 8px rgba(47,133,90,0.15)` (stat-card hover) · `0 20px 50px rgba(0,0,0,0.25)` (modal) · focus ring `0 0 0 2px rgba(47,133,90,0.15)` | EXISTING / ALIGNED — codify as `--ct-shadow-sm / --ct-shadow-md / --ct-shadow-lg / --ct-focus-ring` |
| Layout spacing (page) | `v3-main` padding; grid gap conventions in `ops.css`/`admin.css` | PARTIAL — a page-level spacing scale (section gaps, grid gaps) is TARGET REQUIRED |
| Undecided | A named elevation scale beyond the three shadows above; a dedicated grid/column token set | MARKED UNDECIDED — no new visual decision invented; Cline should codify the existing values above and flag any new token for review |

*End of design system. Implements D21 without contradiction.*
