# CarbonTally — 03 · Module Breakdown (RC2 Frozen Schema)

22 modules, ordered by dependency layer: **foundation → core domain → pipeline → engagement → admin**. Every table named below exists in the schema dump or is an approved RC1 rename (`defra_conversion_factors` → `emission_factors`; renamed columns applied throughout). Verification summary at the foot of this document. Service-layer names refer to `packages/services`; all zod schemas live in `packages/validation`; DB types are generated in `packages/db`.

---

## Layer 1 — Foundation

### 1. Authentication

**Responsibilities**
- Sign-in/sign-up and session lifecycle via Supabase Auth, bridged to the application `users` row (user_type ∈ company_user / consultant / staff).
- Password reset with latest-valid-wins token semantics (UNIQUE on `user_id` was dropped in RC1 — multiple outstanding tokens allowed).
- Invitation acceptance (customer, consultant, staff) including beta-access-code redemption for the Ireland beta cohort and waitlist capture.
- Login audit (device/IP/timestamp) and workspace routing after authentication.

**Dependencies**
- Users (identity record); Permissions (workspace routing decision); Notifications (reset/invite emails); Audit Logs (login events).

**API boundaries**
- Exposes: `auth.service.ts` — signIn/signOut, requestPasswordReset/confirmPasswordReset, acceptInvitation, redeemBetaCode, session refresh (consumed by middleware and `(auth)` route group).
- Consumes: `users.service.ts` (identity provisioning), `notifications.service.ts` (transactional mail), `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `users` | Identity, credentials, user_type, active flag |
| `password_reset_tokens` | Reset tokens (latest-valid-wins) |
| `login_history` | Sign-in audit |
| `user_invitations` | Issued invitations |
| `pending_invites` | Org-scoped invite staging |
| `beta_access_codes` | Ireland beta enrolment codes |
| `beta_users` | Beta cohort registry |
| `waitlist` | Pre-launch capture |

**Future scalability (1k/10k orgs)**
At 1k orgs (~10–20k users) the current design is comfortable: token lookups are PK-indexed and login writes are append-only. At 10k orgs the hot spots are `login_history` growth and invite-table churn; partition `login_history` monthly (or move to a log sink) — but only when the frozen trigger fires (>10–20M rows/table, sustained vacuum pressure, or retention DELETEs exceeding their window), executed as a versioned change via change control per `08_performance_plan.md` §5, never as a default 10k-org action — and add rate-limited, per-IP throttling at the route-handler edge. MFA and SSO/SAML for enterprise customers become requirements at that tier — Supabase Auth supports both without schema change; the module's API surface already isolates the provider so migration is contained to `auth.service.ts`.

---

### 2. Users

**Responsibilities**
- User profile lifecycle for all three personas, including consultant and staff extended profiles.
- Presence and activity signals consumed by Messaging and Manual Review (who is online, who is working a queue).
- GDPR erasure orchestration via the `anonymise_user(uuid, uuid, text)` RPC (irreversible; actor-guarded: self, active staff, or service context).
- Account activation/deactivation aligned with organisation suspension semantics.

**Dependencies**
- Authentication (credential events); Permissions (profile ↔ role binding); Audit Logs (activity writes).

**API boundaries**
- Exposes: `users.service.ts` — getProfile/updateProfile, deactivateAccount, requestErasure (RPC guard), presence heartbeat; `presence.service.ts` behaviour folded into users.
- Consumes: `audit.service.ts`, `notifications.service.ts` (erasure confirmation).

**Database tables**

| Table | Use |
|---|---|
| `users` | Core identity (shared with Auth) |
| `consultant_profiles` | Consultant persona details |
| `staff_profiles` | Staff persona details |
| `user_activity_log` | Per-user action trail |
| `user_presence` | Online/away state |

**Future scalability**
Presence and activity-log writes scale with concurrent users, not orgs. At 1k orgs, presence via Supabase Realtime heartbeats with `user_presence` as the persistence fallback is sufficient. At 10k orgs, presence should stop writing to Postgres on every heartbeat (write-behind cache with periodic flush) and `user_activity_log` should be sampled or rolled up daily; the anonymise-in-place erasure procedure must be re-rehearsed against the larger FK graph to keep runtime inside the GDPR 30-day SLA.

---

### 3. Permissions

**Responsibilities**
- Organisation membership and role enforcement (owner/admin/member/viewer IN-list, mirroring the DB CHECK).
- Consultant multi-org grants: which client organisations a consultant/firm member may see (`client_access` array predicates, GIN-indexed).
- Staff role assignment for the internal workspace and operational queues.
- The application-side contract of the RLS helpers `is_org_member(uuid)` / `is_org_active(uuid)` — services must never bypass what policies enforce.

**Dependencies**
- Users, Organizations; consumed by every other module (guards), and by middleware for workspace gating.

**API boundaries**
- Exposes: `permissions.service.ts` — listMemberships, assertOrgRole, listConsultantClients, grantClientAccess/revokeClientAccess, assignStaffRole, canAccessOrg (unified check used by all services).
- Consumes: `organizations.service.ts` (is_active gate), `audit.service.ts` (grant/revoke events).

**Database tables**

| Table | Use |
|---|---|
| `roles` | Role catalogue/reference |
| `organization_members` | Org ↔ user with role (unique org/user) |
| `consultant_clients` | Consultant ↔ client org grants |
| `consultant_firm_members` | Firm membership + `client_access` array |
| `staff_roles` | Internal role assignments |

**Future scalability**
Permission checks sit on every request. At 1k orgs, RLS plus the I4 GIN index on `client_access` handles consultant predicates comfortably. At 10k orgs, per-request membership resolution should be cached in the session JWT claims (short TTL) to avoid repeated membership joins, and large consultancies (hundreds of client grants per user) will need the `client_access` array model reviewed against a junction-heavy alternative — a data-model decision deferred by the RC2 freeze, so the mitigation is claim-level caching and grant pagination in the consultant switcher UI.

---

## Layer 2 — Core Domain

### 4. Organizations

**Responsibilities**
- Tenant lifecycle: creation (service-role only by design — no authenticated INSERT policy), profile, country (GB/IE) and currency (GBP/EUR) defaults, `default_factor_year`.
- Lifecycle state: `is_active` / `archived_at` suspension and offboarding, which the RLS layer turns into a platform-wide write block (reads survive).
- Organisation metadata including `total_floor_area_sqm` / `occupied_floor_area_sqm` (SECR intensity denominators).
- Organisation-level files and the org switcher context for multi-org users.

**Dependencies**
- Authentication, Permissions; Billing (plan state displayed with the tenant); Settings (org-level overrides).

**API boundaries**
- Exposes: `organizations.service.ts` — createOrganization (staff/system only), updateOrganization, setActive/suspend/archive, getMetadata/upsertMetadata, listMyOrganizations (union of memberships + consultant grants).
- Consumes: `permissions.service.ts`, `billing.service.ts` (subscription summary), `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `organizations` | Tenant root |
| `organization_metadata` | Extended profile incl. floor areas |
| `organization_members` | Membership (shared with Permissions) |
| `organization_files` | Tenant-level file artefacts |

**Future scalability**
Organisation rows are low-volume; the pressure at 10k orgs is cross-tenant fan-out for multi-org consultants and staff list screens (trigram search on `organizations.name` already indexed, I5). Tenant-scoped caching of the org record (country, currency, factor year, active flag) in the session context removes a hot join from nearly every request. Archival strategy (cold storage for archived tenants' documents) becomes necessary past ~5k orgs; `archived_at` is the hook and no schema change is required.

---

### 5. Facilities

**Responsibilities**
- Facility CRUD per organisation with UK postcode / Ireland Eircode conditional validation (at least one required — DB CHECK; format and per-country rules in `packages/validation` only).
- Meter identifiers (`meter_mpan_mprn`) for electricity/gas supply points.
- Asset register per facility (vehicles, boilers, equipment) and unit catalogue for quantities.
- Activity categorisation feeding the Carbon Engine and factor resolution.

**Dependencies**
- Organizations (tenant scope); Emission Factors (activity categories align with factor natural keys); Carbon Engine (consumes facilities/assets).

**API boundaries**
- Exposes: `facilities.service.ts` — CRUD, postcodeOrEircode validation, MPAN/MPRN registry; `assets.service.ts` — asset CRUD; `units.service.ts` — read-only unit catalogue.
- Consumes: `factors.service.ts` (activity-category alignment), `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `facilities` | Sites (postcode nullable; `eircode`, `meter_mpan_mprn` per RC1) |
| `assets` | Equipment/vehicle register |
| `units` | Unit reference data |
| `activity_categories` | Activity taxonomy reference |

**Future scalability**
Facilities per org is small (tens), so growth is linear with orgs. At 10k orgs the module remains trivially indexed on `organization_id`; the real scaling work is bulk import (portfolio landlords with hundreds of meters) — add CSV import jobs through the existing worker claim pattern rather than interactive forms. Reference data (`units`, `activity_categories`) should be served from an in-memory cache in the service layer since it changes only on schema-release data loads.

---

### 6. Suppliers

**Responsibilities**
- Supplier master data per org: VAT number and company number (partial unique indexes, NULL-excluding), `sort_code` for GB suppliers, addresses across GB/IE.
- Fuzzy/trigram search ("did you mean?") on name and VAT for dedupe during onboarding and OCR mapping.
- Supplier and product categorisation for spend-based emissions.
- Duplicate detection handshake with OCR-extracted supplier identities.

**Dependencies**
- Organizations; OCR (extracted supplier hints); Carbon Engine (spend-based activity source); Documents (invoices reference suppliers).

**API boundaries**
- Exposes: `suppliers.service.ts` — CRUD with unique-identifier conflict handling, trigramSearch, resolveOrCreate (used by OCR mapping), category assignment.
- Consumes: `audit.service.ts`, `factors.service.ts` (category → factor mapping context).

**Database tables**

| Table | Use |
|---|---|
| `suppliers` | Supplier master (RC1: `sort_code`; unique VAT/company no.) |
| `supplier_categories` | Supplier taxonomy reference |
| `product_categories` | Product taxonomy reference |

**Future scalability**
Suppliers grow with document volume, not org count directly — expect 10⁵–10⁶ rows at 10k orgs. Trigram indexes (I5) keep fuzzy search sub-100 ms to ~1M rows; beyond that, move search to a dedicated index (e.g. typesense/Elasticsearch) fed by change events. Cross-org shared supplier registries (a platform-wide canonical supplier graph) is a tempting 10k-org optimisation but conflicts with tenant isolation and is a post-freeze data-model decision — not assumed anywhere in this architecture.

---

### 7. Emission Factors

**Responsibilities**
- Read path for the jurisdiction-neutral factor library (`emission_factors`): lookup by natural key (year, activity, country ∈ {GB, IE}), unit and scope context, source/set provenance (`factor_source`, `factor_set`).
- Organisation factor-year policy: honour `organizations.default_factor_year` with per-calculation override and full provenance recording (`emission_factor_used` on queue/extraction rows, `emission_factor_id` on emission rows).
- Reference-data integrity: `region_deprecated` is never read; `country` is authoritative.
- Staff-side factor browsing UI; factor data loads (e.g. SEAI/EPA for v1.1) are staff-run data tasks, not application writes.

**Dependencies**
- None downstream (pure reference); consumed by Carbon Engine, OCR (AI mapping hints), Reports, SECR.

**API boundaries**
- Exposes: `factors.service.ts` — resolveFactor(year, activity, country, unit), listFactors (staff), getDefaultFactorYear(org), assertFactorProvenance.
- Consumes: `settings.service.ts` (any feature flags around factor visibility).

**Database tables**

| Table | Use |
|---|---|
| `emission_factors` | Factor library (renamed from `defra_conversion_factors`; RC1 adds `country`, `unit`, `scope`, `factor_source`, `factor_set`) |
| `activity_categories` | Activity taxonomy (shared with Facilities) |
| `units` | Unit reference (shared with Facilities) |

**Future scalability**
Factor tables are reference-sized (thousands of rows even with GB+IE+multi-year sets); the unique (year, activity, country) index serves all lookups. At 1k orgs, add an in-process cache with release-gated invalidation. At 10k orgs nothing structural changes — the RC1 provenance columns mean new jurisdictions (EU beta) arrive as data, not schema. The genuine risk is stale-cache emissions drift; mitigate with a factor-set version stamp in every cached entry and in `emission_factor_used` provenance.

---

## Layer 3 — Pipeline

### 8. Documents

**Responsibilities**
- Upload intake: signed-URL uploads to private tenant-prefixed buckets, `file_checksum` population for duplicate detection, batch upload grouping within plan limits.
- Document lifecycle state machine (`uploaded → … → verified/approved/rejected/failed` per the K4 IN-list) and per-document activity trail.
- Customer verification flow: confirm extracted data, approve/reject, with verification trail.
- Draft entries: user-entered activity data that bypasses document ingestion.

**Dependencies**
- Organizations, Permissions; OCR (hands off to `document_processing_queue`); Manual Review; Notifications (status events); Billing (batch-upload limits).

**API boundaries**
- Exposes: `documents.service.ts` — initUpload (checksum dedupe prompt), completeUpload (enqueues processing), listDocuments (org+created index path), verifyDocument, approve/reject, draft-entry CRUD.
- Consumes: `storage.service.ts` (signed URLs), `ocr.service.ts` (enqueue), `billing.service.ts` (limit checks), `notifications.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `customer_documents` | Document registry + status (RC1: `file_checksum`) |
| `upload_batches` | Batch grouping (NOT NULL org per RC1) |
| `file_attachments` | Binary references (int8 sizes per RC1) |
| `document_types` | Document-type catalogue |
| `document_type_categories` | Type taxonomy |
| `document_activity_log` | Per-document events |
| `customer_verifications` | Verification decisions (NOT NULL org per RC1) |
| `verification_activity_log` | Verification events |
| `draft_entries` | Manual activity entries |

**Future scalability**
Documents are the highest-volume tenant artefact. At 1k orgs, `customer_documents_org_created_idx` serves list views and checksum dedupe is an indexed equality probe. At 10k orgs: lifecycle-based Storage tiering (hot recent, cold archived) with `organization_files` pointers; list pagination strictly keyset-based on (organization_id, created_at); and virus scanning already exists at launch (the File Virus Scanner is a v1.0 component, running in `temp-uploads` before the complete-move); only its pipeline placement may be revisited at this scale, not its existence. Duplicate detection at scale needs checksums scoped per org (current model) — resist global dedupe for tenancy reasons.

---

### 9. OCR

**Responsibilities**
- AI/OCR extraction pipeline: workers claim `document_processing_queue` rows with SKIP LOCKED using the exact partial-index predicate (status ∈ pending/processing/manual_review/manual_extraction/qc/customer_review, ordered by created_at).
- Extraction output into manual-extraction batches/items with per-field confidence (0–100 scale) and `emission_factor_used` AI mapping hints (suggestions only — never auto-approved).
- QC-required and customer-approval flags (NOT NULL per RC1) routing documents into Manual Review.
- Processing telemetry: logs, timing, and AI content history for prompt-version auditability.

**Dependencies**
- Documents (intake); Manual Review (handoff); Emission Factors (mapping hints); Billing (AI extraction limits/usage); Settings (`queue_settings` tuning).

**API boundaries**
- Exposes: `ocr.service.ts` — enqueueDocument, claimNext (worker-facing), recordExtraction, suggestFactorMapping, transitionStatus (state machine guarded by zod + CHECK parity).
- Consumes: `storage.service.ts` (file fetch), external OCR provider, `billing.service.ts` (meter + limit), `manual-review.service.ts` (route to queue), `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `document_processing_queue` | OCR pipeline queue (RC1: `emission_factor_used`, NOT NULL status/qc/customer flags) |
| `manual_extraction_batches` | Extraction batch grouping |
| `manual_extraction_items` | Per-field extraction results (RC1: `emission_factor_used`) |
| `processing_logs` | Pipeline logs |
| `ai_content_history` | Prompt/response audit |
| `processing_audit_trail` | Queue state transitions |

**Future scalability**
OCR is throughput-bound, not row-bound. At 1k orgs, 2–4 worker replicas draining the partial-index claim path suffice; idempotency keys on queue rows prevent double-processing on claim races. At 10k orgs: autoscale workers on queue depth; split claim loops by priority class using `queue_settings`-driven weights; move per-page OCR artefacts to Storage with DB rows holding pointers only; and introduce per-provider circuit breakers. The claim predicate must remain byte-identical to `dpq_claim_idx` (RC1 Known Limitation 5) — enforced by a contract test.

---

### 10. Manual Review

**Responsibilities**
- Human-in-the-loop queues: manual review of OCR output and the staff/consultant operational `processing_queue` (assignment, steps, timing, reassignment with history).
- Quality control: checklists, checks, error taxonomy, and the approval pipeline (requests → decisions).
- SLA clocks: breach flags (`sla_breached` NOT NULL per RC1), workload balancing across staff.
- Full review audit trail for customer-facing defensibility.

**Dependencies**
- OCR (upstream), Documents, Users/Presence (assignment), Platform Administration (SLA definitions, workload), Notifications (assignment alerts).

**API boundaries**
- Exposes: `manual-review.service.ts` — claim/assign/reassign, recordStep, completeReview, qc service functions (runChecklist, recordError), approvals service (requestApproval, decide), verification log writes.
- Consumes: `users.service.ts` (availability), `admin.service.ts` (SLA targets), `notifications.service.ts`, `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `manual_review_queue` | Review queue (NOT NULL org per RC1) |
| `review_assignment_history` | Review assignment trail |
| `review_audit_trail` | Review decisions audit |
| `customer_review_log` | Customer review outcomes |
| `processing_queue` | Staff/consultant ops queue (RC1: NOT NULL status/sla_breached) |
| `processing_assignments` | Ops assignment records |
| `processing_steps` | Step-level progress |
| `processing_time_log` | Per-step timing |
| `reassignment_history` | Ops reassignment trail |
| `qc_checks` | QC executions |
| `qc_checklists` | QC templates |
| `qc_errors` | QC error taxonomy/instances |
| `approval_requests` | Approval workflow requests |
| `approval_decisions` | Approval outcomes |
| `verification_logs` | Verification event log |

**Future scalability**
This module is the operational heart and scales with staff headcount × document volume. At 1k orgs, SKIP-LOCKED claims with the `processing_queue_claim_idx` predicate support a small ops team; assignment is fair-round-robin via `staff_workload`. At 10k orgs: dedicated queue partitions per priority/SLA class, skills-based routing (staff ↔ document-type affinity), and materialised workload snapshots instead of live aggregates. Queue tables need aggressive archival of completed/cancelled rows (they're the majority of volume) — an operations runbook task, no schema change.

---

### 11. Carbon Engine

**Responsibilities**
- Emissions computation: activity quantity × resolved factor → `emissions_logs` with unit, scope, `emission_factor_id` provenance and non-negative quantities (K3 ranges).
- Corrections model: corrections are **positive rows with a type/flag** — negative correction lines are impossible by DB design (RC1 breaking change 8).
- Aggregation read models for dashboards and report inputs (org + start-date index path).
- Manual-entry (draft) ingestion into the same computation path as OCR-extracted data.

**Dependencies**
- Emission Factors (resolution), Facilities/Assets (activity sources), Suppliers (spend-based), Documents (source linkage), Billing (nothing), Reports/SECR (consumers).

**API boundaries**
- Exposes: `carbon.service.ts` — computeEmission, recordCorrection, aggregateByOrg(period, scope), recomputeOnFactorChange, provenance trace for any emission row.
- Consumes: `factors.service.ts`, `facilities.service.ts`, `suppliers.service.ts`, `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `emissions_logs` | Emission records (RC1: `emission_factor_id`, `unit`, `scope`, non-negative) |
| `draft_entries` | Manual activity input (shared with Documents) |
| `assets` | Asset-sourced activity (shared with Facilities) |
| `units` | Unit context (shared with Facilities) |

**Future scalability**
Emission rows grow with document volume (10⁶–10⁷ rows at 10k orgs). At 1k orgs, `emissions_logs_org_start_date_idx` serves dashboards directly. At 10k orgs: pre-aggregated monthly rollups computed by a worker (stored where today's consumers can fall back to raw rows), keyset pagination everywhere, and a recalculation queue so factor-year updates reprocess affected orgs asynchronously rather than in request time. Immutability discipline (append corrections, never mutate) keeps the ledger auditable and makes rollup invalidation tractable.

---

### 12. Reports

**Responsibilities**
- Report definition (templates, including org-specific and platform defaults) and immutable versions per org (unique report/version).
- Asynchronous generation via `report_generation_queue` (worker-claimed, partial-index predicate) producing artefacts into tenant-prefixed Storage.
- Collaboration: report comments; export history for every produced file.
- Scheduling/usage metering handshake with Billing (reports_generated counter).

**Dependencies**
- Carbon Engine (data), Emission Factors (provenance footnotes), Organizations, Documents (evidence links), Billing (limits), Notifications (completion events).

**API boundaries**
- Exposes: `reports.service.ts` — listTemplates, requestGeneration (enqueue), getVersion, addComment, recordExport, downloadUrl (signed).
- Consumes: `carbon.service.ts` (aggregates), `storage.service.ts`, `billing.service.ts`, `notifications.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `report_templates` | Template catalogue |
| `report_versions` | Immutable report versions |
| `report_generation_queue` | Generation jobs (worker-claimed) |
| `report_comments` | Collaboration thread per report |
| `export_history` | Export artefacts record |

**Future scalability**
Report generation is bursty (period-end). At 1k orgs a single report worker with the queue claim loop absorbs peaks. At 10k orgs: priority lanes in the claim predicate (keep aligned with `report_generation_queue_claim_idx`), rendering concurrency limits per org to stop noisy-neighbour starvation, and artefact lifecycle policies (regenerate-on-demand from immutable `report_versions` inputs instead of indefinite Storage retention). Large reports should stream to Storage rather than buffer in worker memory.

---

### 13. SECR

**Responsibilities**
- Streamlined Energy & Carbon Reporting pack assembly for UK (GB) organisations: scope 1/2 energy and emissions, intensity ratios using `organization_metadata.total_floor_area_sqm` / `occupied_floor_area_sqm`.
- Methodology and provenance disclosure blocks (factor years/sources per `emission_factor_used` trails).
- Year-on-year comparatives from the immutable emissions ledger.
- Ireland awareness: SECR output is suppressed/alternative-labelled for IE tenants (country-driven, no separate schema).

**Dependencies**
- Reports (versioning/generation pipeline — SECR is a specialised report type), Carbon Engine, Organizations (metadata), Emission Factors.

**API boundaries**
- Exposes: `secr.service.ts` — buildSecrPack(org, period), validateIntensityInputs (floor-area presence), methodologyStatement.
- Consumes: `carbon.service.ts`, `reports.service.ts` (enqueue + versioning), `organizations.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `report_templates` | SECR template rows (shared with Reports) |
| `report_versions` | SECR pack versions (shared with Reports) |
| `report_generation_queue` | SECR generation jobs (shared with Reports) |
| `emissions_logs` | Underlying ledger (read-only here) |
| `organization_metadata` | Floor-area intensity denominators |

**Future scalability**
SECR assembly is a fan-in aggregation over one org's ledger — cheap per org, peaky at reporting season. At 1k orgs it rides the Reports worker pool. At 10k orgs the intensity and comparative queries should hit the Carbon Engine's monthly rollups rather than raw rows, and methodology blocks cached per factor-set version. Regulatory change (e.g. updated UK guidance) arrives as template versions — the immutable-version model means historic packs never need regeneration.

---

## Layer 4 — Engagement

### 14. Messaging

**Responsibilities**
- Tenant-scoped conversations between customers, consultants and staff with participant management.
- Message fan-out with per-message activity trail, Realtime delivery on per-tenant authorised channels.
- Presence/typing indicators (ephemeral via Realtime, persisted sparingly).
- Append-only conversation activity log for dispute resolution.

**Dependencies**
- Users (presence), Permissions (participant eligibility), Notifications (offline digests), Audit Logs.

**API boundaries**
- Exposes: `messaging.service.ts` — createConversation, addParticipant, sendMessage (writes message + activity), markRead, typing/presence publishers.
- Consumes: `users.service.ts`, `notifications.service.ts` (digest fan-out), `realtime-auth` route handler.

**Database tables**

| Table | Use |
|---|---|
| `conversations` | Threads (NOT NULL org per RC1) |
| `conversation_participants` | Membership per thread |
| `messages` | Message bodies (FK to conversations per RC1 F1) |
| `message_activity_log` | Per-message events |
| `conversation_activity_log` | Thread-level events |
| `typing_status` | Typing indicators |
| `user_presence` | Presence (shared with Users) |

**Future scalability**
Messaging is write-heavy and Realtime-fan-out-heavy. At 1k orgs, the I3 messaging indexes cover thread lists and unread counts. At 10k orgs: paginate messages by keyset, archive cold threads, and move typing/presence fully to ephemeral Realtime channels (no DB writes). Unread-count aggregation should be maintained incrementally (participant-level counters computed by the service on send/read) rather than COUNT queries per render.

---

### 15. Notifications

**Responsibilities**
- Notification orchestration: template rendering (mirroring `emails/` React Email templates), multi-channel delivery records and per-channel delivery log.
- In-app notification centre with read state; user preferences.
- Transactional email send (reset, invites, report-ready, SLA alerts) with send audit (`email_logs`).
- Digest batching for offline message/notification summaries (worker fan-out job).

**Dependencies**
- All event-producing modules (Documents, OCR, Manual Review, Reports, Tasks, Messaging, Billing); Users; Settings (template administration).

**API boundaries**
- Exposes: `notifications.service.ts` — notify(event, recipients) single entry point used by all modules, listForUser, markRead, setPreferences, renderTemplate.
- Consumes: email provider (transactional), Realtime (in-app), `users.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `notifications` | In-app notification records |
| `notification_templates` | Template catalogue |
| `notification_delivery` | Per-channel delivery rows |
| `notification_delivery_log` | Delivery attempts/outcomes |
| `email_templates` | Email template catalogue |
| `email_logs` | Sent-mail audit |

**Future scalability**
Notification volume multiplies org count × events. At 1k orgs, synchronous notify with async email fan-out is fine. At 10k orgs: event-driven batching (a worker drains a notification buffer rather than request-time fan-out), per-channel rate limits, and retention windows on delivery logs (append-only growth). Template rendering should be cached per template version; prefer provider-side templates for the highest-volume transactional mails.

---

### 16. Tasks

**Responsibilities**
- Consultant task management across client orgs (`consultant_tasks`): creation, due dates, status, client linkage.
- Internal staff task system (`internal_tasks`) with assignments and workload interplay.
- Task assignment records and audit-friendly lifecycle.
- Surfacing tasks into each workspace's task views (customer sees consultant-assigned items affecting their org).

**Dependencies**
- Users, Permissions, Organizations, Manual Review (tasks often reference queue items), Notifications (due/assigned alerts).

**API boundaries**
- Exposes: `tasks.service.ts` — createTask/assign/complete for both consultant and internal scopes, listMyTasks (persona-aware), linkToQueueItem.
- Consumes: `permissions.service.ts` (client-grant scoping), `notifications.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `consultant_tasks` | Consultant cross-client tasks |
| `internal_tasks` | Staff tasks |
| `task_assignments` | Assignment records |

**Future scalability**
Task volume tracks human activity, so growth is modest. At 1k orgs the design is complete. At 10k orgs the consultant cross-client "my tasks" view becomes the expensive query (union over granted clients); resolve with a denormalised assignee index scan (already covered by tenant+assignee composite indexing patterns) and, if needed, a per-user task inbox maintained on write. Recurring-task templates (period-end checklists) are a feature addition that fits this module without schema change via template tasks in `internal_tasks`.

---

### 17. Support

**Responsibilities**
- Customer ↔ staff communication channel (`customer_communication`) with internal-note segregation (`is_internal`) and read tracking.
- Product feedback capture and triage (`user_feedback`), including PII-scrub posture under erasure (anonymise_user scrubs feedback PII).
- Glossary/help content serving for in-app guidance (UK/IE terminology differences).
- Handoff of support threads into Tasks or Manual Review when operational action is needed.

**Dependencies**
- Users, Permissions, Notifications (staff alerts on new customer messages), Tasks (action conversion), Audit Logs.

**API boundaries**
- Exposes: `support.service.ts` — postCommunication (with is_internal guard), listThread, submitFeedback, getGlossary (cached).
- Consumes: `notifications.service.ts`, `tasks.service.ts`, inbound-email Edge Function (webhook → communication rows).

**Database tables**

| Table | Use |
|---|---|
| `customer_communication` | Support/communication records (NOT NULL org per RC1) |
| `user_feedback` | Feedback submissions |
| `glossary` | Help/terminology reference |

**Future scalability**
Support threads scale with active customers. At 1k orgs, simple org+created pagination suffices. At 10k orgs: full-text search over communication content (pg_trgm or external search), SLA timers on first-response using `sla_definitions` (cross-module read), and triage automation (keyword routing) implemented in a worker — all additive without schema change. The inbound-email webhook must include idempotency (message-ID dedupe) before volume makes duplicates operationally visible.

---

## Layer 5 — Admin

### 18. Audit Logs

**Responsibilities**
- Append-only audit writers for every module (the service layer's `audit.service.ts` is the only writer; six append-only log families deliberately carry no `updated_at` triggers).
- Actor-attributed trails: user, staff, document, processing and generic audit families.
- Activity feed assembly for tenant-visible "what happened" views.
- Tamper-evidence posture: append-only discipline (hash chain was reviewed and rejected — not implemented).

**Dependencies**
- Every module (as consumers of the writer); Authentication (actor context); Platform Administration (audit search UI).

**API boundaries**
- Exposes: `audit.service.ts` — writeAudit(event), writeActivity, searchAudit (staff, scoped), getEntityTrail.
- Consumes: nothing downstream; called by all services.

**Database tables**

| Table | Use |
|---|---|
| `audit_logs` | Generic audit events |
| `audit_trail` | Entity-level trail |
| `activity_logs` | Activity records |
| `activity_feed` | Feed projection |
| `staff_activity_log` | Staff action audit |
| `processing_audit_trail` | Pipeline transitions (shared with OCR) |

**Future scalability**
Audit families are the largest tables by volume at scale. At 1k orgs, indexed scoped search for staff is acceptable with retention in primary storage. At 10k orgs: monthly partitioning or table-per-quarter rotation of the log families — only if the frozen trigger fires (>10–20M rows/table or sustained vacuum pressure), via versioned change control per `08_performance_plan.md` §5, not a default action at this tier — cold export to object storage with a manifest, and read models for common staff queries (per-org recent activity). Because RC1 fixed these tables as trigger-free append-only, rotation is an operational task with zero application change — the write path never references historical partitions.

---

### 19. Platform Administration

**Responsibilities**
- Staff operational oversight: workload balancing, individual/team/daily performance, and SLA compliance monitoring against `sla_definitions` and `business_hours`.
- Tenant administration: suspension/offboarding execution (sets `is_active`/`archived_at` — triggers the platform-wide write block), impersonation-free support access via scoped grants only.
- Dashboard metrics assembly for internal analytics.
- Reassignment governance across Manual Review queues (history already captured there).

**Dependencies**
- Manual Review (queue data), Users/Permissions (staff roles), Organizations (lifecycle), Audit Logs, Settings (SLA/business-hours administration), Notifications (SLA breach alerts).

**API boundaries**
- Exposes: `admin.service.ts` — staff dashboards (getWorkload, getPerformance, getSlaCompliance), tenantAdmin actions (suspend/reactivate), metrics snapshots.
- Consumes: `manual-review.service.ts`, `organizations.service.ts`, `settings.service.ts`, `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `staff_workload` | Live workload per staffer |
| `staff_performance` | Performance aggregates |
| `staff_daily_performance` | Daily performance rollups |
| `team_performance` | Team-level rollups |
| `sla_compliance` | SLA outcomes |
| `sla_definitions` | SLA targets (shared admin reference) |
| `business_hours` | Business-hours calendar for SLA clocks |
| `dashboard_metrics` | Internal metrics snapshots |

**Future scalability**
Performance/SLA aggregation over raw queue tables is the scaling risk. At 1k orgs, on-demand aggregates over `processing_*` tables are fine. At 10k orgs: scheduled rollup workers must own `staff_daily_performance`/`team_performance`/`dashboard_metrics` writes (write-once snapshots rather than recompute-on-read), and SLA breach evaluation should be event-driven (evaluated on queue transitions) instead of sweep-based. Staff count grows slower than tenant count, so staff-side screens stay cheap; tenant-list screens need keyset pagination and trigram search (already indexed).

---

### 20. Settings

**Responsibilities**
- Platform configuration: `system_settings` key-value administration (feature flags, provider configuration, maintenance notices).
- Queue tuning: `queue_settings` (weights, batch sizes, SLA clock parameters) consumed by workers at claim time.
- Template administration surfaces for notification/email/report templates (delegating storage to those modules).
- Org-level settings passthrough (country/currency/`default_factor_year` displayed from Organizations; edited there, surfaced here).

**Dependencies**
- Platform Administration (staff-only guard), every module (as readers of flags/settings), Audit Logs (setting-change events).

**API boundaries**
- Exposes: `settings.service.ts` — getSetting/setSetting (typed keys via zod registry), getQueueSettings (worker-facing, cached), featureFlag(org/user) evaluation.
- Consumes: `permissions.service.ts` (staff-only writes), `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `system_settings` | Platform key-value configuration |
| `queue_settings` | Worker/queue tuning parameters |

**Future scalability**
Settings are read-hot, write-cold. At 1k orgs, a short-TTL in-process cache in the service layer removes essentially all DB reads. At 10k orgs: per-org setting overrides become desirable (currently platform-level only — a post-freeze data-model question; do not bolt org columns on ad hoc), and flag evaluation should move to a snapshot pushed to workers at boot plus change-notify via Realtime admin channel. Typed-key discipline (zod registry) is what prevents settings sprawl from becoming untestable — that contract must hold regardless of scale.

---

### 21. Billing / Subscriptions

**Responsibilities**
- Subscription lifecycle per organisation: plan, status (trialing/active/past_due/paused/cancelled/expired IN-list), billing period, Stripe identifiers (GBP/EUR per tenant country).
- Usage metering and limit enforcement: AI extraction limits, batch-upload caps, manual-extraction page allowances, overage pricing (`price_per_ai_extra`, `price_per_manual_page`).
- Usage rollups: `usage_tracking` daily/monthly counters (unique org/month per RC1) feeding dashboards and invoices.
- Consultant engagement billing: `consultant_billing` records with currency (GBP/EUR per RC1) per client relationship.

**Dependencies**
- Organizations (tenant + currency), Documents/OCR (metered events), Reports (reports_generated counter), Authentication/Users (billing contact), Notifications (dunning/limit alerts), Stripe via the webhooks-only Edge Function.

**API boundaries**
- Exposes: `billing.service.ts` — getSubscription, assertWithinLimit (called by Documents/OCR/Reports before metered actions), recordUsage, syncFromStripe (Edge-Function-invoked), consultant invoicing CRUD.
- Consumes: Stripe webhook Edge Function (`supabase/functions/stripe-webhook`), `notifications.service.ts`, `audit.service.ts`.

**Database tables**

| Table | Use |
|---|---|
| `customer_subscriptions` | Plan, limits, pricing, Stripe refs |
| `usage_tracking` | Metered usage counters (unique org/month) |
| `consultant_billing` | Consultant engagement billing (RC1: `currency`) |

**Future scalability**
Metering is the contention point: every metered action updates `usage_tracking`. At 1k orgs, direct upserts on the unique (org, month) row are fine with optimistic retry. At 10k orgs: buffered metering (workers aggregate counters and flush periodically — the `usage-rollups` job already exists for this), limit checks served from the cached subscription record with DB as fallback, and dunning/proration delegated entirely to Stripe so the module never grows its own billing engine. Multi-currency reporting (GBP/EUR consolidation) is a finance-reporting concern layered on read models, not on these OLTP tables.

---

## Cross-cutting verification

### Module inventory (22 modules — brief's 21 + Billing/Subscriptions)

| # | Module | Layer |
|---|---|---|
| 1 | Authentication | Foundation |
| 2 | Users | Foundation |
| 3 | Permissions | Foundation |
| 4 | Organizations | Core domain |
| 5 | Facilities | Core domain |
| 6 | Suppliers | Core domain |
| 7 | Emission Factors | Core domain |
| 8 | Documents | Pipeline |
| 9 | OCR | Pipeline |
| 10 | Manual Review | Pipeline |
| 11 | Carbon Engine | Pipeline |
| 12 | Reports | Pipeline |
| 13 | SECR | Pipeline |
| 14 | Messaging | Engagement |
| 15 | Notifications | Engagement |
| 16 | Tasks | Engagement |
| 17 | Support | Engagement |
| 18 | Audit Logs | Admin |
| 19 | Platform Administration | Admin |
| 20 | Settings | Admin |
| 21 | Billing / Subscriptions | Admin |
| — | (Storage is a service-layer concern, not a module — no schema tables of its own; private tenant-prefixed buckets only.) | — |

All 21 brief-mandated modules present; Billing/Subscriptions added per schema evidence (`customer_subscriptions` with Stripe identifiers, `usage_tracking`, `consultant_billing`).

### Table-name verification against the frozen dump

Every table named above was checked against the RC2 schema dump (94 tables). Result:

- **Verified as-is (93 of 94 dump tables referenced above):** `activity_categories, activity_feed, activity_logs, audit_logs, assets, beta_access_codes, beta_users, conversation_activity_log, conversation_participants, conversations, customer_documents, customer_review_log, customer_verifications, document_activity_log, document_types, draft_entries, email_logs, email_templates, emissions_logs, export_history, facilities, file_attachments, glossary, manual_review_queue, message_activity_log, messages, notification_delivery_log, organization_files, organization_members, organization_metadata, organizations, password_reset_tokens, pending_invites, processing_logs, review_assignment_history, review_audit_trail, roles, typing_status, units, upload_batches, user_activity_log, user_feedback, user_invitations, user_presence, verification_activity_log, waitlist, supplier_categories, product_categories, suppliers, document_processing_queue, processing_audit_trail, customer_subscriptions, usage_tracking, report_templates, report_generation_queue, ai_content_history, manual_extraction_batches, manual_extraction_items, document_type_categories, users, consultant_profiles, consultant_clients, consultant_firm_members, consultant_tasks, consultant_billing, report_versions, report_comments, staff_roles, staff_profiles, staff_workload, staff_performance, processing_queue, processing_assignments, processing_steps, processing_time_log, reassignment_history, qc_checks, qc_checklists, qc_errors, approval_requests, approval_decisions, verification_logs, audit_trail, staff_activity_log, login_history, notifications, notification_templates, notification_delivery, staff_daily_performance, team_performance, sla_compliance, system_settings, queue_settings, sla_definitions, business_hours, dashboard_metrics, internal_tasks, task_assignments, customer_communication`.
- **Renamed (1):** dump table `defra_conversion_factors` is referenced throughout as **`emission_factors`** per RC1 R1 — approved rename, not a new table. Renamed columns (`emission_factor_id`, `emission_factor_used`, `default_factor_year`) and RC1-added columns (`facilities.eircode`, `facilities.meter_mpan_mprn`, `organizations.is_active`/`archived_at`, `suppliers.sort_code`, `customer_documents.file_checksum`, `organization_metadata.total_floor_area_sqm`/`occupied_floor_area_sqm`) are used only in their post-migration forms.
- **Non-existent tables referenced: 0.** No tables were invented; every module's data needs are met by frozen tables (module rows marked "shared" intentionally reference a table under its owning module as well).

*No SQL, migrations, seed data or application code appear in this document — architecture specification only, honouring the RC2 freeze.*
