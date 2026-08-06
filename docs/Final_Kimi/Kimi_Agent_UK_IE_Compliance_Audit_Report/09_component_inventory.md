# 09 — CarbonTally UI Component Inventory (RC2 Architecture Specification)

*Complete inventory of every UI component required for CarbonTally v1.0 — UK primary launch, Ireland beta, three workspaces (customer / consultant / internal staff), single codebase in `apps/web` (Next.js 15 App Router, React 19, TypeScript, Tailwind, shadcn/ui, `packages/ui` primitives, `packages/validation` zod schemas shared with the API, Supabase Realtime for chat/notifications). Database frozen at RC2: every "Data source" cell names frozen tables in prose. No SQL, no code, no seed data in this document.*

*Conventions: server components by default; components marked (client) are interactive islands. UK/IE column records jurisdiction-dual behaviour: country defaults GB (currency GBP, Europe/London, DD/MM/YYYY dates, £ formatting); IE orgs switch to EUR/€, Europe/Dublin, Eircode fields, m² floor area, IE factor rows — driven by `organizations.country` and the country-conditional validation packs of `packages/validation`.*

*Counts: 24 primitives · 22 shared app components · 74 feature components = **120 components**.*

---

## (a) Primitives — shadcn/ui (`packages/ui`)

Only primitives actually consumed by the feature surfaces below are listed.

| Primitive | Used by (representative surfaces) | Notes |
|---|---|---|
| Button | Every screen | Variants: default, destructive (suspend/delete flows), outline, ghost; loading state |
| Input | All forms | Bound via FormField wrappers to zod schemas |
| Textarea | Chat composer, ticket replies, notes | Autosize in composer |
| Select | Country (GB/IE), currency (GBP/EUR), units, roles | Options constrained to IN-list vocabularies |
| Combobox | Supplier/facility pickers, factor activity types | Type-ahead over trigram-backed search |
| Checkbox | Multi-select, QC checklist items | |
| Radio Group | Scope selection, billing options | |
| Switch | Feature flags, secr_enabled, notification prefs | |
| Date Picker / Calendar | Billing periods, reporting year, contract dates | DD/MM/YYYY; end-before-start inline error |
| Form | All validated forms | React Hook Form + zod resolvers; schemas imported from `packages/validation` |
| Table | Simple listings | Feature tables use the shared DataTable wrapper |
| Dialog | Confirmations, invite user, add facility/supplier | Focus-trapped; destructive confirms require typed confirm on suspend flows |
| Alert Dialog | Archive org, reject document, GDPR erasure confirm | |
| Drawer / Sheet | Mobile nav, notification centre, OCR field inspector | Right-side sheet for notification centre |
| Popover | Workspace/org switcher menus, filter pickers | |
| Dropdown Menu | Row actions, user menu | |
| Tabs | Settings sections, report builder steps, doc detail (data/activity/verifications) | |
| Accordion | FAQ/support, SECR guidance, audit diff expansion | |
| Tooltip | Confidence scores, field-level help, masked bank values | |
| Badge | Status pills, country chip (GB/IE), confidence colours | Status vocabulary matches frozen K4 lists |
| Toast (Sonner) | Async action feedback, realtime notification popups | Realtime-triggered toasts deduped with centre |
| Skeleton | All loading states | Server-component fallbacks via Suspense |
| Card | Dashboard tiles, intensity-ratio cards | |
| Progress | Upload progress, report generation % | Wired to upload/progress channels |
| Separator / Scroll Area / Avatar | Layout chrome, thread lists, user chips | |

---

## (b) Shared app components (`apps/web/components/shared`)

| Component | Purpose | Workspace(s) | Data source (frozen tables, in prose) | Key states |
|---|---|---|---|---|
| DataTable (keyset pagination) | Canonical table wrapper: sort, column visibility, keyset (cursor) pagination — never OFFSET | All three | Any tenant list surface (documents, suppliers, facilities, queues, tickets) | Loading skeleton; empty-state CTA; error with retry; cursor-exhausted footer |
| FormField (schema-bound wrapper) | Label + control + error message bound to a `packages/validation` zod schema field | All three | n/a (binds API validation schemas 1:1) | Default/focus/error/disabled; UK-vs-IE schema pack selected by org country |
| CountryAwareFields | Address block that renders postcode (GB) or optional Eircode + 26-county dropdown (IE) | Customer, consultant | Address columns on organizations/facilities/suppliers/consultant_profiles | GB: postcode required with GIR-shape mask; IE: Eircode shape `D02 X285`, county list from app config (no DB lookup); facilities enforce at-least-one presence |
| CurrencyDisplay | Money formatting £/€ from row currency column | All three | Currency columns constrained to GBP/EUR | GBP default; EUR for IE rows; negative values impossible (frozen ≥0 rule) — renders adjustment pattern instead |
| DateDisplay / DateRangePicker | DD/MM/YYYY presentation, Europe/London vs Europe/Dublin aware | All three | All date/timestamptz columns | Locale-selected; invalid-pair inline error |
| FileUploadDropzone | Drag-drop upload with per-file progress, checksum (SHA-256) state, type/size allowlist | Customer, consultant | customer_documents, file_attachments, upload_batches | Idle/drag-over/uploading/hashing/duplicate-prompt (file_checksum match)/rejected (extension+MIME rules)/error |
| PdfViewer | Paginated in-browser PDF render with zoom/rotate; pan-to-region hooks for OCR review | Customer, consultant, staff | file_url columns (signed URLs only) | Loading; render error; signed-URL-expired refresh |
| EmissionTrendChart (bar/line) | Period-over-period emissions trend | Customer, consultant, staff | emissions_logs aggregated by (organization_id, start_date) | Loading; empty (no verified logs); UK/IE identical except unit/currency chips |
| ScopeBreakdownDonut | Scope 1/2/3 split | Customer, consultant, staff | emissions_logs.scope rollups | Empty; single-scope; verified vs unverified toggle |
| IntensityRatioCard | Ratio tiles (per employee, per m²/sqft, per £/€ revenue) | Customer, consultant | organization_metadata headcount/floor-area (sqft GB, sqm IE)/revenue | Unit chip flips sqft↔m² by org country; missing-denominator placeholder |
| FactorSourceBadge | Provenance chip: factor set, source (DEFRA-DESNZ / SEAI / EPA), year, country | Customer, staff | emission_factors provenance columns | GB vs IE variant; deprecated/unknown factor warning |
| ConfidenceBadge | 0–100 confidence pill with amber/red thresholds routing to review | Customer, staff | confidence columns on customer_documents, emissions_logs, document_processing_queue | High/medium/low; un-scored placeholder |
| StatusPipeline | Horizontal stepper of document lifecycle states | Customer, consultant, staff | customer_documents.status, document_processing_queue.status | K4-constrained values only; stuck-state highlight |
| NotificationBell | Header bell with unread badge (unread-partial-index-shaped query) + Realtime | All three | notifications (recipient polymorphic pair) | Badge 0/n/99+; realtime pop; degraded-offline |
| NotificationCentre | Drawer: grouped, filterable notification list, mark-read actions | All three | notifications + notification_delivery_log | Empty; loading; realtime prepend; per-type filters |
| RealtimeProvider | Supabase Realtime channel manager (chat, notifications, presence) with reconnection/backoff | All three | conversations/messages/notifications subscription surface | Connected/reconnecting/offline banner |
| PresenceAvatarStack | Online/typing presence chips in chat and review collaboration | All three | user_presence, typing_status | Ephemeral; offline fallback |
| KeysetPager | Previous/next cursor controls + page-size selector used inside DataTable | All three | n/a | First/middle/last-known-page |
| MaskedValue | Last-4 rendering for bank account/IBAN/sort code with reveal-on-permission | Customer (own), staff | suppliers banking columns | Masked default; staff reveal audit-logged |
| AuditDiffViewer | old_data/new_data side-by-side expansion for audit rows | Staff, customer (own org log) | audit_logs, audit_trail jsonb diff columns | Loading; identical-values collapsed; large-payload truncation |
| EmptyState / ErrorState / SuspendedOrgBanner | Standard empty and error surfaces; read-only banner when organization suspended | All three | organizations.is_active / archived_at | Write actions disabled with explanation when org inactive |
| ExportButton | Request export → progress → download of signed URL | Customer, consultant, staff | export_history | Queued/generating/ready/expired link |

---

## (c) Feature components per module

### Upload & documents

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| UploadBatchPanel (client) | Batch upload orchestration: queue list, per-file progress + checksum, batch summary | Customer, consultant | upload_batches, customer_documents, file_attachments | Empty; uploading; duplicate-checksum prompt; partial-failure retry; MIME/extension rejection reasons |
| DocumentList | Keyset-paginated document table with status/type/date filters | Customer, consultant | customer_documents (tenant composite ordering) | Loading; empty-onboarding CTA; status filter chips; error |
| DocumentDetail | Tabbed detail: extracted data, activity feed, verifications, file preview | Customer, consultant | customer_documents (extracted_data/mapped_data jsonb), document_activity_log, customer_verifications | Per-status rendering; unextracted placeholder; verification timeline |
| DocumentLifecycleBoard | Pipeline board of documents by lifecycle status (Kanban or stepper grouped) | Customer, consultant, staff | customer_documents.status + document_processing_queue stages | Column empties; stuck-item highlight; realtime status moves |
| DocumentTypePicker | Document type + category select driving per-type requirement flags (facility/asset/supplier required) | Customer, consultant | document_types, document_type_categories | Type-dependent requirement hints; UK/IE neutral |
| DuplicateUploadDialog | Shown when file_checksum matches an existing document: open existing / upload anyway | Customer, consultant | customer_documents.file_checksum | Single vs multiple matches |

### OCR review

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| OcrReviewWorkspace (client) | Side-by-side: PDF viewer (left) + extracted-fields panel (right) with confidence highlighting and correction form; saving writes corrections and routes forward | Staff (primary), customer (approval view) | document_processing_queue (ai_* columns, confidence), customer_documents.extracted_data, manual_extraction_items | Loading pair; low-confidence fields amber/red; corrected-field diff marker; read-only for customer approval |
| ExtractedFieldRow | Single extracted field: label, value, confidence badge, correction input, "copied from page" highlight link | Staff, customer | extracted_data/mapped_data payloads | High/low confidence; corrected; missing-required |
| SupplierMappingSuggest | AI-suggested supplier/facility/asset mapping with accept/change; trigram "did you mean?" | Staff | AI-mapping hint references, suppliers (partial identifier uniqueness), facilities, assets | Suggested/unmapped/conflict (duplicate identifier rejection); cross-tenant impossible under RLS |
| OcrConfidenceSummary | Document-level confidence header + routing rationale (auto-accept vs manual review) | Staff | document_processing_queue.ai_confidence_score, qc_required | Auto-routed; manual-required |

### Navigation & workspace chrome

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| Sidebar | Per-workspace nav (route groups customer/consultant/staff), collapsible, badge counts | All three | Badge counts from notifications/queues/tasks | Active-section highlight; collapsed; suspended-org dimming of write entries |
| WorkspaceSwitcher | Switch between workspaces the user can access (member vs consultant vs staff) | All three | organization_members, consultant_profiles, staff_profiles | Single-workspace hidden; role-gated entries |
| OrganizationSwitcher | Consultant/staff org context switcher with trigram-backed org autocomplete | Consultant, staff | consultant_clients, consultant_firm_members client_access, organizations | Granted-union only; search-as-you-type; current-org chip with GB/IE badge |
| UserMenu | Profile, preferences, sign-out | All three | users | Default; unread dot |
| Breadcrumbs/PageHeader | Title, context (org/facility), primary action slot | All three | n/a | — |

### Notifications

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| (See shared NotificationBell, NotificationCentre, RealtimeProvider) | | | | |
| NotificationPreferencesForm | Channel toggles per notification type (in-app/email) | All three | notification_templates + user-level preference surface | Default-on; save states; template-gated options |
| EmailDeliveryStatusChip | Delivery/opened status on notification detail (staff) | Staff | notification_delivery_log, email_logs | Sent/delivered/opened/failed |

### Chat / messaging

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| ConversationList | Keyset-paginated thread list with unread counts, participant avatars | All three | conversations (denormalised unread/participant caches), conversation_participants | Loading; empty; realtime reorder; unread badges |
| MessageThread | Realtime message timeline with day dividers, read receipts (1:1 vs group semantics), attachment bubbles | All three | messages, file_attachments, message_activity_log | Loading history; realtime append; offline queue indicator; expired-attachment refresh |
| MessageComposer (client) | Text input with attachment upload, typing-status emission, send-with-retry | All three | messages, typing_status, file_attachments | Typing indicator of peer; sending/failed-retry; attachment allowlist enforcement |
| NewConversationDialog | Start thread with org members / assigned consultant / support staff | All three | organization_members, consultant_clients, staff assignments | Participant search; role-gated options |

### Tasks

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| TaskBoard | Kanban of tasks with status columns, assignee filter, due-date badges | Consultant (consultant_tasks), Staff (internal_tasks) | consultant_tasks, internal_tasks, task_assignments | Empty columns; overdue highlight; drag-move confirmation |
| TaskCard / TaskDetailDrawer | Task summary card + detail drawer (description, assignees, linked client org) | Consultant, staff | task tables + assignments | Loading; unassigned; completed history |
| TaskCreateDialog | New task with client-org picker (consultant) | Consultant, staff | task tables; org pickers as above | Role-gated client list |

### Support

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| SupportTicketList | Customer's tickets (or staff's all-ticket view) with type/status filters | Customer (own), staff (all) | `user_feedback` (ticket row: type/severity/status) | Empty CTA "contact support"; open/closed filters |
| SupportTicketDetail | Ticket conversation thread + metadata sidebar (type, severity, status) | Customer, staff | `user_feedback` ticket row + `customer_communication` thread (`is_internal` segregates staff-only notes) | Awaiting-customer vs awaiting-support; resolved |
| NewTicketDialog | Category (type), subject, description, attachment; routes to staff triage | Customer, consultant | `user_feedback` (creates the ticket row) | Validation errors; submitted confirmation with reference |

### Settings

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| OrgSettingsForm | Org profile: identifiers (company number CH/CRO, VAT GB/IE), addresses (CountryAwareFields), sector, reporting flags | Customer, staff | organizations, organization_metadata | GB vs IE variant (VAT checksum pack, CRO vs CH rules, m² vs sqft floor area, GBP/EUR); suspend/archive read-only |
| UsersSettingsPanel | Members list, role management, invite user, revoke | Customer (admins), staff | organization_members, user_invitations, roles | Pending invites; role-gated management; duplicate-membership impossible (unique pair) |
| InviteAcceptanceScreen | Token-landing acceptance: set password/2FA, join org | Public (auth) | user_invitations (token/status/expires) | Valid/expired/used-token states |
| BillingSettingsPanel | Subscription tier, usage meters vs limits, currency-denominated amounts, Stripe linkage | Customer | customer_subscriptions, usage_tracking, consultant_billing (consultant view) | GBP vs EUR by country; near-limit warnings; month uniqueness |
| FactorsSettingsPanel | Default factor year, factor-source visibility, reporting standard flags | Customer (read), staff (manage) | organizations.default_factor_year, system_settings defaults, emission_factors provenance | GB vs IE catalogue view; read-only for non-admins |
| PreferencesPanel | Locale, timezone (Europe/London vs Europe/Dublin), date format, notification prefs | All three | users, system_settings defaults | Country-derived defaults, overridable |
| SecuritySettingsPanel | Password change, 2FA enrolment (Supabase Auth-owned), sessions, login history | All three | users, login_history | 2FA enrolled/not; session list |

### Facilities

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| FacilityList | Keyset table of facilities with country/type filters | Customer, consultant | facilities (tenant composite), assets counts | Empty onboarding CTA; inactive filter |
| FacilityDetail | Facility profile, assets, linked emissions, meter identifier | Customer, consultant | facilities, assets, emissions_logs (via asset linkage) | GB: postcode shown; IE: Eircode shown, postcode absent; meter MPAN/MPRN label by country |
| FacilityFormDialog | Create/edit with CountryAwareFields; presence rule enforced (postcode OR eircode); optional coordinates with UK-plausibility soft warning | Customer, consultant | facilities (presence constraint backing the rule) | GB default (postcode required); IE variant (Eircode optional-but-recommended, county dropdown, m²); both-empty blocked inline |

### Suppliers

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| SupplierDirectory | Keyset table with trigram autocomplete search, "did you mean?" duplicate nudge | Customer, consultant | suppliers (name/vat trigram, partial identifier uniqueness), supplier_categories | Loading; empty; duplicate-identifier rejection surfacing |
| SupplierDetail | Profile: scoped emissions/factors, banking (masked), compliance, contracts | Customer, consultant | suppliers (scoped emission columns, banking columns, compliance), product_categories | GB: sort code + account; IE: IBAN; masked values with audited reveal |
| SupplierFormDialog | Create/edit with country-conditional VAT/company-number validation and duplicate prompts | Customer, consultant | suppliers + validation packs | GB VAT MOD97 + CH number vs IE VAT format + CRO shape; duplicate VAT/company warning |

### Carbon engine & emissions

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| EmissionsDashboard | Headline tiles + trend chart + scope donut + intensity cards + period selector | Customer, consultant, staff | emissions_logs (unit/scope self-describing), dashboard_metrics cache | Empty (no verified data); loading; UK/IE unit chips; SECR-kWh subtotal for GB orgs |
| EmissionsLogTable | Keyset table of emission entries with verification state and factor provenance | Customer, consultant | emissions_logs, emission_factors | Verified vs pending; factor badge; correction (signed-row) entry pattern |
| ManualEmissionEntryForm | Manual log entry: quantity + unit (units reference), dates, asset/supplier pickers | Customer, consultant | emissions_logs, units, assets, suppliers | Negative input blocked with adjustment explanation; kWh GB default unit |
| FactorPicker | Activity-type type-ahead resolving to a factor for org country + reporting year; unresolvable routes to manual review | Customer, staff | emission_factors (natural key: year, activity, country), activity_categories | GB DEFRA-DESNZ list vs IE SEAI/EPA core set; no-match guidance |
| FactorExplorerTable | Staff browse/manage of factor catalogue with provenance columns | Staff | emission_factors | Country filter GB/IE; duplicate natural-key rejection surfaced |

### Reports

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| ReportList | Reports with current version, status, generated date | Customer, consultant | reports + report_versions (current-version uniqueness), export_history | Empty; generating progress; version history expansion |
| SecrReportBuilder (client) | Stepper: period → facilities/assets scope → energy kWh totals → intensity ratio → governance narrative → generate | Customer, consultant | report_templates, emissions_logs (kWh/unit/scope), organization_metadata (intensity denominators) | UK-only flow (SECR flag); missing-data checklist; IE orgs see "not applicable in beta" guidance |
| ReportVersionHistory | Version list with regenerate action, comments | Customer, consultant | report_versions, report_comments | Duplicate-version rejection surfaced; current badge |
| ReportGenerationStatus | Async progress of generation queue with AI cost telemetry (staff) | Customer (progress only), staff | report_generation_queue (progress %, ai cost columns) | Queued/running/complete/failed |
| ReportViewer | Rendered report + provenance footnotes (factor set, source, year per figure) + export | Customer, consultant | final report artefact URLs, emission_factors provenance | Signed-URL expiry refresh; GB/IE provenance chips |

### Manual review & queues (staff)

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| ManualReviewQueue | Claimable worklist: FIFO, SLA countdowns, escalation flags, claim button | Staff | manual_review_queue (SLA/escalation columns), processing_queue (claim partial-index shape) | Empty; claimed-by-me filter; SLA-breached highlight |
| ReviewAssignmentPanel | Assignment/reassignment history and workload balancing view | Staff leads | processing_assignments, review_assignment_history, reassignment_history, staff_workload | Capacity % bars; reassign dialog |
| QcChecklistPanel | QC checklist execution per item with error logging | Staff | qc_checks, qc_checklists (checklist items jsonb), qc_errors | Pass/fail per item; error taxonomy; quality score |
| CustomerVerificationPanel | Customer submitted/verified/rejected/revision state machine actions | Customer (own), staff | customer_verifications | Each state transition; escalation view |

### Audit & activity

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| OrgAuditLogViewer | Tenant-scoped business-event audit with filters + diff expansion | Customer (own org), staff | audit_logs (old/new/changes jsonb), activity_logs | Loading; filter by actor/resource; large-diff truncation |
| RowVersionTrailViewer | Row-version history for a selected record | Staff | audit_trail | Version timeline; diff between adjacent versions |
| SecurityActivityViewer | Per-user security events (logins, resets, erasure records) | Staff, user (self) | user_activity_log, login_history | Self vs staff view |
| ActivityFeed | Org activity stream for dashboard sidebar | Customer, consultant | activity_feed | Empty; realtime prepend |

### Consultant workspace

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| ClientPortfolioGrid | Cards of granted client orgs: country badge, emissions snapshot, open items | Consultant | consultant_clients, consultant_firm_members client_access, organizations, dashboard_metrics | Empty (no clients); granted-union only; per-client GB/IE badge |
| ClientContextBanner | Persistent "acting on behalf of <org>" banner with switcher | Consultant | current client context | Always visible in client context |
| ConsultantBrandingSettings | White-label logo/colours/support contact | Consultant | consultant_profiles (branding columns) | Preview; saved |
| ConsultantBillingPanel | Per-client billing rows with currency | Consultant | consultant_billing (currency-denominated) | GBP vs EUR per client |
| FirmMembersPanel | Firm member management + client_access grants | Consultant (firm admin) | consultant_firm_members | Grant editor; GIN-backed predicate note invisible to user |

### Staff admin consoles

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| StaffDashboard | Ops overview: queue depths, SLA compliance, workload | Staff | staff_workload, sla_compliance, sla_definitions, team_performance | Loading; breach alerts |
| OrgAdminConsole | Cross-tenant org search, suspend/reactivate (is_active/archived_at), read-only inspection | Staff | organizations, organization_members | Suspend confirmation (typed); suspended org renders read-only everywhere |
| UserAdminConsole | User search, login history, GDPR erasure invocation (guarded) | Staff (privileged) | users, login_history; erasure procedure per freeze | Erasure irreversible double-confirm; actor-guard errors surfaced |
| SystemSettingsConsole | Platform settings: default factor year, currency/timezone defaults, retention/SLA knobs | Staff (admin) | system_settings, queue_settings | Editable vs locked (is_editable) rows |
| FactorManagementConsole | Factor catalogue CRUD-lite and yearly load status per country | Staff | emission_factors | GB vs IE catalogue; duplicate natural-key rejection |
| ApprovalRequestsPanel | Approval inbox with decisions trail | Staff | approval_requests, approval_decisions | Pending/approved/rejected |
| QueueSettingsConsole | Worker/queue knobs, business hours | Staff (admin) | queue_settings, business_hours | — |
| BetaAndWaitlistConsole | Beta access codes, waitlist review (pre-GA only) | Staff | beta_users, beta_access_codes, waitlist | Post-GA retired surfaces hidden |

### Auth

| Component | Purpose | Workspace(s) | Data source | Key states |
|---|---|---|---|---|
| LoginScreen | Email/password sign-in (Supabase Auth), country-neutral | Public | users (mirror), login_history | Invalid credentials; unverified email; suspended-org notice post-login |
| TwoFactorScreen | 2FA challenge (TOTP) post-password | Public | Supabase Auth-owned (no app-schema credential columns, per freeze) | Challenge; recovery-code path; lockout handled by platform |
| PasswordResetScreen | Request + token-landing reset | Public | password_reset_tokens (token-unique lifecycle; latest-valid-wins) | Sent; expired/used token; success |
| SignupScreen | Registration with country picker (GB primary; IE beta flagged), beta access code support | Public | users, organizations (service-role creation), beta_access_codes | GB default; IE beta messaging; IE gating fallback state if SEAI/EPA load slips |
| OnboardingWizard | Post-signup: org profile → first facility (CountryAwareFields) → units/currency defaults by country | Customer | organizations, organization_metadata, facilities | GB vs IE variants throughout; skip-and-complete-later |

---

*Verification: every brief-listed component is present — Upload ✓, PDF Viewer ✓, OCR Review (side-by-side + confidence + correction form) ✓, Sidebar ✓, Workspace Switcher ✓, Organization Switcher ✓, Notifications bell + centre ✓, Chat list/thread/composer realtime ✓, Task Board ✓, Support list + detail ✓, Settings (org/users/billing/factors/preferences) ✓, facilities dual postcode/Eircode ✓, suppliers directory + detail ✓, documents lifecycle board ✓, manual review queue ✓, emissions dashboard ✓, factor picker ✓, reports list + SECR builder ✓, audit log viewers ✓, consultant portfolio ✓, staff admin consoles ✓, auth screens ✓. UK/IE dual behaviour is recorded on every affected row.*
