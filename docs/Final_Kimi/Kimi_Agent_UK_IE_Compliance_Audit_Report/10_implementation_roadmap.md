# 10 — CarbonTally Implementation Roadmap (Phases A–L)

*Frontend/application implementation roadmap for the CarbonTally v1.0 launch (UK primary, Ireland beta; customer / consultant / staff workspaces; single codebase: Next.js 15 App Router, React 19, TypeScript, Tailwind, shadcn/ui, `packages/ui`, `packages/validation`, Supabase Realtime). Database is frozen at RC2: no SQL, no migrations, no seed data appear in this document. Complexity classes (S / M / L / XL) are the required unit of estimation — no duration estimates are given; any sequencing statement is a planning assumption, not a schedule.*

**Phase A assumes the RC1 database migration package (files 001–006 plus verification 007) has been applied and verified** — renames (`emission_factors`, `emission_factor_id`, `default_factor_year`), approved columns (Eircode, sqm floor area, sort code, factor provenance, `file_checksum`), constraints (GB/IE and GBP/EUR IN-lists, ≥0 ranges, uniqueness set), ~160 RLS policies and the `set_updated_at` trigger family are live and green before any application phase begins.

---

## Milestone overview

| Phase | Modules delivered | Total complexity | Suggested sequencing notes |
|---|---|---|---|
| **A — Foundation** | App shell, design system, validation package, org-country context | L | Everything depends on A; land the UK/IE country-context and validation packs here so no later module re-derives them |
| **B — Authentication** | Login, 2FA, reset, signup/invite, onboarding wizard | M | Thin phase (Supabase Auth owns credentials); only the invite acceptance and onboarding wizard carry real weight |
| **C — Organizations** | Workspace chrome, org settings, members/invites, facilities, suspend states | L | Facilities' postcode/Eircode duality is the first consumer of the country context |
| **D — Suppliers** | Directory, detail, banking masks, duplicate controls | M | Trigram "did you mean?" and masked banking are the only non-CRUD parts |
| **E — Documents** | Upload pipeline UI, lifecycle board, detail, PDF viewer | L | Depends on C/D pickers; checksum duplicate UX is a launch-gate behaviour |
| **F — OCR** | OCR review workspace, extraction corrections, mapping suggest, review queue handoff | XL | Highest-risk UI in the programme; build against mock-PDF fixtures before live OCR |
| **G — Carbon Engine** | Factor picker/explorer, emission entry, emissions dashboard and charts | L | Depends on F for extracted quantities; UK/IE factor catalogue split lands here |
| **H — Reports** | Report list, SECR builder, versions, generation status, viewer | L | Depends on G verified data; SECR is GB-only, IE gets beta messaging |
| **I — Messaging** | Realtime chat, notifications bell/centre, presence | L | Self-contained; may run parallel to E–G once A/B land |
| **J — Support & Tasks** | Ticket list/detail/composer, staff ticket console, task board/cards (consultant + internal tasks) | L | Reuses I's thread/composer primitives; tasks are an adjacent consultant workflow delivered alongside support |
| **K — Admin Workspace** | Staff ops consoles: queues, QC, SLA/workload, org/user admin, billing/subscriptions console, settings/factors, audit viewers | XL | Largest surface; staff-only; depends on E/F queues and C org data |
| **L — Testing** | Cross-cutting: GB/IE fixtures, RLS-visible behaviour, realtime soak, accessibility, launch checklist | L | Runs continuously from Phase C; formal exit gate before launch |

---

## Phase A — Foundation

| Attribute | Detail |
|---|---|
| **Goal** | Stand up the deployable application skeleton: route groups per workspace, the shared design system, the shared validation package, and the organisation-country context that every UK/IE dual behaviour keys off. |
| **Modules delivered** | App shell & route groups (customer/consultant/staff layouts, Sidebar, UserMenu) · design system (`packages/ui` primitives themed, badges/cards/toasts) · `packages/validation` zod packs (GB + IE country-conditional schemas shared with the API) · org-country context & formatting services (£/€, DD/MM/YYYY, Europe/London vs Europe/Dublin) · DataTable with keyset pagination · Suspended-org read-only banner |
| **Dependencies** | RC1 package applied and verified (assumed); none otherwise |
| **Exit criteria** | All three route groups render behind role gating; every primitive used by later phases exists in `packages/ui`; a GB org and an IE org render the same screen with correct currency/date/postcode-vs-Eircode variants driven purely by org country; keyset pagination demonstrated against a seeded list with no OFFSET; validation schemas imported identically by a form and its API handler |
| **Complexity per module** | App shell & route groups — **M** (three workspaces, role-gated nav); design system — **L** (breadth of primitives, theming, accessibility baseline); validation packs — **L** (GB MOD97/GIR/Eircode-shape/CRO/CH conditional rules, shared frontend/API); country context & formatting — **S** (small, but load-bearing); DataTable keyset — **M** (cursor plumbing reused everywhere); suspend banner — **S** |

## Phase B — Authentication

| Attribute | Detail |
|---|---|
| **Goal** | Deliver the complete auth journey on Supabase Auth: login, 2FA challenge, password reset, signup with country picker, and invite acceptance — with zero credential state in the application schema (frozen decision). |
| **Modules delivered** | Login screen · 2FA challenge · password reset (request + token landing, latest-valid-wins) · signup with GB-primary / IE-beta country picker and beta access code · invite acceptance landing · onboarding wizard shell (org profile step wired in Phase C) |
| **Dependencies** | A (shell, validation packs) |
| **Exit criteria** | Full journeys pass for GB and IE signups; 2FA enrolment and challenge work via platform auth only; expired/used invite and reset tokens render distinct states; IE signup shows beta messaging (and the gating fallback copy if the IE factor load is unavailable); login history entries appear for staff view |
| **Complexity per module** | Login — **S** (platform-owned); 2FA — **S** (platform-owned challenge UI only); password reset — **M** (multi-token lifecycle edge states); signup + country picker — **M** (jurisdiction branching, beta gating); invite acceptance — **M** (token states, join-org write path); onboarding shell — **S** at this phase |

## Phase C — Organizations

| Attribute | Detail |
|---|---|
| **Goal** | Ship the tenant-management surface: workspace chrome finalised, organisation settings, member/invite management, and the facilities module whose postcode/Eircode duality is the flagship UK/IE behaviour. |
| **Modules delivered** | Workspace & organization switchers (granted-union scoping) · org settings form (identifiers, addresses, reporting flags) · users/members panel + invite management · facility list/detail/form with CountryAwareFields (postcode GB default; Eircode + 26-county dropdown IE; presence rule surfaced inline) · org metadata (headcount, floor area sqft GB / sqm IE, revenue) · suspended-org enforcement end-to-end |
| **Dependencies** | A, B |
| **Exit criteria** | IE organisation creates an Eircode-only facility and a both-empty submission is blocked inline (matching the frozen presence rule); GB forms never render an Eircode field and IE forms never force a postcode; role-gated member management works with duplicate membership impossible; a suspended org renders read-only across every C surface; sqft/sqm field flips by country with the intensity-corruption guard documented |
| **Complexity per module** | Switchers — **M** (consultant/staff granted-union autocomplete); org settings — **L** (very wide frozen column set, country-conditional identifiers); members/invites — **M**; facilities — **L** (dual-country forms, presence rule, coordinates soft warning, meter identifier labelling); org metadata — **S**; suspend enforcement — **M** (touches every write action) |

## Phase D — Suppliers

| Attribute | Detail |
|---|---|
| **Goal** | Deliver the supplier directory and detail surfaces with country-conditional identifier validation, duplicate controls and jurisdiction-aware banking display. |
| **Modules delivered** | Supplier directory (trigram autocomplete, "did you mean?" nudge) · supplier form (GB VAT MOD97 + Companies House vs IE VAT format + CRO shape; duplicate VAT/company warnings) · supplier detail (scoped emissions/factors, compliance, contracts) · masked banking (GB sort code + account vs IE IBAN; last-4 reveal) |
| **Dependencies** | C (org context, pickers) |
| **Exit criteria** | Duplicate identifier submissions surface the frozen uniqueness rejections as friendly warnings; legitimate same-name suppliers save without error (name-unique correctly absent); banking renders masked with the correct jurisdictional fields per supplier country; directory search returns fuzzy matches at launch data volumes |
| **Complexity per module** | Directory + autocomplete — **M**; supplier form — **L** (conditional validation packs, duplicate surfacing); detail — **M**; masked banking — **S** |

## Phase E — Documents

| Attribute | Detail |
|---|---|
| **Goal** | Ship the document lifecycle: batch upload with progress and checksum duplicate detection, the documents lifecycle board, document detail, and the PDF viewer that OCR review will reuse. |
| **Modules delivered** | Upload dropzone + batch panel (per-file progress, SHA-256 checksum state, extension/MIME allowlist) · duplicate-upload dialog · document list (keyset, filters) · document lifecycle board (status pipeline) · document detail tabs · PdfViewer (pagination, zoom, region hooks) |
| **Dependencies** | C, D (facility/supplier pickers in metadata) |
| **Exit criteria** | Rejected files explain the allowlist reason before upload starts; a checksum-identical file triggers the duplicate prompt; every lifecycle status is renderable and transitions appear without refresh (polled or realtime); PDF viewer handles large files within the widened size envelope; empty states guide first upload for both GB and IE tenants |
| **Complexity per module** | Dropzone + batch panel — **L** (resumable-feel progress, hashing, failure retries); duplicate dialog — **S**; list — **M**; lifecycle board — **M** (pipeline visualisation, realtime moves); detail — **M**; PdfViewer — **L** (render performance, region hooks consumed by Phase F) |

## Phase F — OCR

| Attribute | Detail |
|---|---|
| **Goal** | Deliver the extraction-review experience: the side-by-side OCR review workspace with confidence highlighting and correction forms, supplier/facility mapping suggestions, and the handoff into the manual review queue. |
| **Modules delivered** | OCR review workspace (PDF left, extracted fields right) · extracted-field rows with confidence badges and correction inputs · supplier/facility/asset mapping suggest with trigram fallback · confidence summary + routing rationale · customer verification panel (submitted/verified/rejected/revision states) |
| **Dependencies** | E (PDF viewer, documents), D (supplier data), C (facilities) |
| **Exit criteria** | Low-confidence fields render amber/red and corrections persist; accepting a mapping writes the correct tenant-scoped reference (cross-tenant suggestion demonstrably impossible); the customer approval view is read-only against the same surface; every verification state transition is reachable and audited; the workspace performs acceptably on the mock GB/IE PDF fixture set |
| **Complexity per module** | OCR review workspace — **XL** (split-pane synchronisation, region highlighting, correction diffs, the single most complex screen in the product); field rows — **M**; mapping suggest — **L** (fuzzy search, conflict states, AI-hint presentation); confidence summary — **S**; verification panel — **M** |

## Phase G — Carbon Engine

| Attribute | Detail |
|---|---|
| **Goal** | Surface the calculation layer to users: factor selection by country and year, manual emission entry, and the emissions dashboard with trend, scope and intensity visualisations. |
| **Modules delivered** | Factor picker (activity type-ahead resolving against the org's country catalogue) · factor explorer (staff browse with provenance columns) · manual emission entry form (units from the reference table, non-negative enforcement with adjustment guidance) · emissions dashboard (trend bar/line, scope donut, intensity-ratio cards) · emissions log table with verification state and factor provenance badges |
| **Dependencies** | F (extracted quantities flow into logs), C (metadata denominators for intensity) |
| **Exit criteria** | A GB org resolves DEFRA-DESNZ factors and an IE org resolves the SEAI/EPA core set with no cross-contamination; unresolvable activity types route to manual review with clear copy; negative entry is blocked with the signed-correction pattern explained; the Dublin fixture's Scope 2 visibly carries an IE factor badge; SECR kWh subtotals display for GB orgs without any join ambiguity (unit/scope carried on the log) |
| **Complexity per module** | Factor picker — **L** (country/year resolution, no-match routing); factor explorer — **M**; manual entry — **M**; dashboard + charts — **L** (aggregation presentation, empty/verified states, dual units); log table — **M** |

## Phase H — Reports

| Attribute | Detail |
|---|---|
| **Goal** | Deliver customer-facing reporting: report list with versions, the SECR report builder for UK orgs, generation progress, and a provenance-annotated report viewer. |
| **Modules delivered** | Report list + version history · SECR report builder (period → scope → kWh totals → intensity → narrative → generate) · report generation status (queue progress) · report viewer (per-figure factor provenance, export) · report comments |
| **Dependencies** | G (verified emissions data), E (export/download plumbing) |
| **Exit criteria** | Regenerating the same version number surfaces the frozen uniqueness rejection cleanly; every figure in a generated report carries factor set/source/year provenance; IE orgs see honest "SECR not applicable in beta" guidance rather than a broken flow; GB and IE fixture reports reconcile to fixture expectations; generation progress is visible without refresh |
| **Complexity per module** | Report list + versions — **M**; SECR builder — **XL** (multi-step wizard, intensity denominators, narrative inputs, UK-statutory correctness bar); generation status — **S**; viewer — **L** (provenance footnoting, signed-URL expiry); comments — **S** |

## Phase I — Messaging

| Attribute | Detail |
|---|---|
| **Goal** | Launch realtime communication: customer↔consultant↔staff chat with presence and typing, plus the notifications bell and centre delivered over Supabase Realtime. |
| **Modules delivered** | Conversation list · message thread (read receipts, attachments) · composer (typing status, attachments, retry) · new-conversation dialog · notification bell + centre · notification preferences |
| **Dependencies** | A (RealtimeProvider, shell); independent of C–H data modules once membership data exists |
| **Exit criteria** | Messages and notifications arrive without refresh with reconnection backoff and an offline indicator; unread badge counts match the centre at all times; a cross-tenant thread read demonstrably returns nothing; attachments obey the upload allowlist; keyset pagination holds on long threads |
| **Complexity per module** | Conversation list — **M**; thread — **L** (realtime append, receipt semantics 1:1 vs group, attachment refresh); composer — **M**; new-conversation — **S**; bell + centre — **L** (realtime dedupe between toast and centre, unread-partial-shaped queries); preferences — **S** |

## Phase J — Support & Tasks

| Attribute | Detail |
|---|---|
| **Goal** | Deliver the support surface (customer ticket creation and tracking, staff ticket console) and the Tasks module — tasks and support are adjacent consultant workflows sharing the same thread/composer primitives, so they land together. |
| **Modules delivered** | New-ticket dialog · ticket list (customer own / staff all) · ticket detail thread with metadata sidebar · staff triage actions (status, resolution notes) · task board (kanban of `consultant_tasks`/`internal_tasks` with status columns and due-date badges) · task card / detail drawer · task create dialog with client-org picker |
| **Dependencies** | I (thread/composer primitives), B |
| **Exit criteria** | Customer sees exactly their own tickets; staff triage transitions all states; ticket threads reuse the messaging composer with attachments; resolved tickets archive cleanly; consultants create, move and complete tasks against granted client orgs only, and staff work internal tasks on the same board pattern |
| **Complexity per module** | New ticket — **S**; list — **M**; detail — **M**; staff triage — **M**; task board — **M** (kanban drag-move states, consultant/internal duality); task card/drawer — **S**; task create dialog — **S** |

## Phase K — Admin Workspace

| Attribute | Detail |
|---|---|
| **Goal** | Ship the internal staff workspace: claimable review and processing queues, QC execution, workload/SLA monitoring, cross-tenant org and user administration, platform settings, billing/subscription administration and the audit viewers. |
| **Modules delivered** | Staff dashboard (queue depths, SLA, workload) · manual review queue (claim, SLA countdown, escalation) · QC checklist panel + error logging · assignment/reassignment and workload panels · org admin console (search, suspend/reactivate, read-only inspection) · user admin console (login history, guarded GDPR erasure invocation) · billing/subscriptions console (`customer_subscriptions`/`usage_tracking` inspection, plan changes, Stripe reconciliation review, past_due handling) · system settings & queue settings consoles · factor management console · audit log viewers (business events, row-version trail, security activity) |
| **Dependencies** | E, F (queues and review content exist), C (org data), H (factor/report telemetry) |
| **Exit criteria** | Queue claiming is race-safe in the UI (claimed items lock visually); SLA breaches highlight before deadline; suspend/reactivate propagates the read-only state platform-wide; erasure invocation enforces the actor guard with an irreversible double-confirm; staff plan changes and dunning actions reflect correctly in `customer_subscriptions` and reconcile against Stripe; every audit viewer renders jsonb diffs readably; staff cannot escalate their own visibility beyond their role row |
| **Complexity per module** | Staff dashboard — **M**; manual review queue — **L** (claim UX, SLA, escalation); QC panel — **M**; assignment/workload — **M**; org admin — **L** (cross-tenant power with suspend blast radius); user admin + erasure — **L** (guarded, irreversible flows); billing/subscriptions console — **M** (plan/limit inspection and Stripe reconciliation surfaces; cross-tenant, read-mostly with guarded writes); settings consoles — **M**; factor management — **M**; audit viewers — **L** (diff rendering across several log families) |

## Phase L — Testing

| Attribute | Detail |
|---|---|
| **Goal** | Prove the launch: end-to-end GB and IE fixture journeys, RLS-visible behaviour from the client, realtime under load, accessibility, and the go-live checklist. |
| **Modules delivered** | GB + IE end-to-end fixture suites (onboarding → facility → supplier → upload → OCR → factor → report) · cross-tenant isolation checks exercised through the UI · realtime soak (chat/notifications under concurrent tenants) · accessibility pass (WCAG 2.2 AA on committed screens) · performance smoke on the keyset-paginated hot screens · launch checklist runbook |
| **Dependencies** | All of A–K |
| **Exit criteria** | Both jurisdiction fixtures pass end-to-end on staging, including the Eircode-only facility and the Dublin Scope 2 IE-factor assertion; zero cross-tenant rows observable from any workspace role; realtime degradation is graceful (banner, retry) not silent; hot-screen p95 within target at year-one stated volumes; the go-live checklist is fully initialled |
| **Complexity per module** | GB/IE fixture suites — **L** (breadth across every module × 2 jurisdictions); isolation checks — **M** (scripted but unforgiving); realtime soak — **M**; accessibility — **M**; performance smoke — **M**; launch runbook — **S** |

---

## Delivery risks — top three

1. **OCR/AI extraction accuracy (Phase F).** The review workspace is specified on the assumption that extraction confidence meaningfully separates auto-accept from manual review. If real GB/IE invoice accuracy underperforms the mock fixtures, manual review volume swells, Phase K's queues become the bottleneck, and the confidence thresholds baked into the UI (amber/red routing) need re-tuning mid-delivery. Mitigation: build F against the mock-PDF fixture set first, treat thresholds as configuration, and keep the customer correction loop (verification panel) as the accuracy safety net from day one.
2. **RLS–application integration.** The RC1 package's ~160 policies change access behaviour on every tenant request: any client path connecting without an authenticated context reads zero rows, and a single wrong policy is either a cross-tenant leak (launch-stopping) or a dead screen. The granted-union consultant predicate (array-backed client access) is the sharpest edge. Mitigation: Phase A's org-country/tenant context owns session-scoped queries; Phase L's isolation checks run per role per workspace; workers and cron never share the client path.
3. **Realtime at scale (Phases I–J).** Supabase Realtime carries chat, notifications, presence and document-status moves; connection churn across many tenants risks missed events, duplicate toasts and stale unread badges — failures that erode trust precisely because they are intermittent. Mitigation: the RealtimeProvider centralises channel lifecycle with backoff and resync-on-reconnect; unread counts re-derive from the server after any reconnect; Phase L's soak test runs before launch sign-off.

*Note: Phase A assumes the RC1 database migration package has been applied and verified (007 checks green) before any application work begins; this roadmap consumes the frozen RC2 schema and never amends it — any schema need discovered inside a phase returns through structural review.*

*Verification: all 12 phases A–L present, each with Goal, Modules delivered, Dependencies, Exit criteria and per-module complexity (S/M/L/XL with one-line justifications); milestone overview table and risk paragraph included; UK/IE dual behaviour noted in Phases A, B, C, D, G, H and L; complexity classes are the only estimation unit used; no SQL, code or seed data.*
