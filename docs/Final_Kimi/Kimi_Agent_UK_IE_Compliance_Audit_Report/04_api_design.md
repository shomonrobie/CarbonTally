# CarbonTally v1.0 — API Design Specification (RC2-Frozen Schema)

Architecture specification only. No SQL, no application code, no migrations. All table/column names use the post-RC1/RC2 vocabulary (`emission_factors`, `emission_factor_id`, `emission_factor_used`, `default_factor_year`, `facilities.eircode`, `organizations.is_active`, `customer_documents.file_checksum`, `user_invitations` canonical, `pending_invites` write-blocked).

## 1. Global Conventions

### 1.1 Platform, Base Path and Versioning

| Item | Decision |
|---|---|
| Implementation | Next.js 15 App Router: route handlers for everything in this document; server actions permitted only for same-page form mutations, which delegate to the same typed service layer and zod schemas |
| Base path | `/api/v1` (URL-path versioning; v1 frozen for launch, breaking changes require `/api/v2`) |
| Service layer | Every handler calls a typed service module; handlers never query the database directly. Service layer is the only place `organization_id` filtering is applied in code |
| Auth model | Supabase Auth owns login, logout credential checks, 2FA (TOTP), password reset and magic links. Endpoints in §2 are app-level session/context/profile concerns only. No parallel credential state in the application schema (REJECT C14 honoured) |
| DB access roles | Browser requests connect as `authenticated` (RLS enforced via `organization_members.role` + `client_access` union). Service role is used only in workers and server-side system paths, always with explicit `organization_id` filtering |

### 1.2 Tenant Scoping and Workspace Context

| Item | Rule |
|---|---|
| Tenant context header | `X-Organization-Id: <uuid>` required on every tenant-scoped request. Server verifies the caller has access: membership in `organization_members` (active) OR consultant grant via `consultant_clients` / `consultant_firm_members.client_access`. Mismatch → `403 TENANT_ACCESS_DENIED` |
| Workspace resolution | Derived server-side from the caller, never from the client: Customer workspace → `organization_members.role ∈ {owner, admin, member, viewer}`; Consultant workspace → row in `consultant_profiles` + `consultant_firm_members`; Staff workspace → row in `staff_profiles` + `staff_roles` |
| Org-switch | Persists no server-side session state beyond the audited `POST /auth/org-switch` event; each request restates `X-Organization-Id`, and RLS + code-level filtering re-derive tenancy per request |
| Suspended tenants | `organizations.is_active = false` → reads permitted, all writes return `423 ORGANISATION_SUSPENDED` (mirrors RLS write policies) |

### 1.3 Pagination, Filtering, Sorting

| Item | Rule |
|---|---|
| Pagination | Keyset (cursor) only: `?limit=1..100` (default 25) + `?cursor=<opaque>`. Cursor encodes the last `(sort_key, id)` pair. Response envelope carries `next_cursor`, `has_more`. Offset pagination is not offered |
| Default sort | `(created_at DESC, id DESC)` unless the endpoint table states otherwise |
| Filtering | Explicit query parameters per endpoint; unknown parameters are rejected `400 UNKNOWN_QUERY_PARAM` (fail closed) |
| Text search | `?search=` maps to the trigram indexes (`suppliers_name_trgm_idx`, `suppliers_vat_number_trgm_idx`, `organizations_name_trgm_idx`); minimum 2 characters |

### 1.4 Error Envelope and Status Codes

All errors return one envelope shape:

| Field | Content |
|---|---|
| `error.code` | Stable machine-readable `SCREAMING_SNAKE` code |
| `error.message` | Human-readable, UK English, no stack traces |
| `error.details` | Array of `{field, issue}` for validation failures (zod issue map) |
| `error.request_id` | Correlation id echoed into `audit_logs` / worker logs |
| `error.retry_after` | Seconds, present only on `429` / `503` |

| Status | When used |
|---|---|
| 400 | Malformed body, unknown query param, cursor invalid |
| 401 | No/invalid/expired Supabase session |
| 403 | Authenticated but role/workspace/tenant grant insufficient |
| 404 | Resource absent **or** outside tenant scope (existence is not leaked cross-tenant) |
| 409 | State conflict: wrong document status for the action, duplicate natural key (K5), idempotency replay with a different payload |
| 413 | Upload exceeds `system_settings.max_upload_size_mb` / `max_batch_size_mb` |
| 422 | zod format-validation failure (postcode, VAT+MOD97, Eircode, CH number, E.164, email, IBAN, sort code) — the API layer is the sole format authority |
| 423 | Organisation suspended (`is_active = false`) |
| 429 | Rate limit exceeded |
| 500/503 | Internal error / worker dependency unavailable |

### 1.5 Validation Layering (frozen decision)

Every request field validated at the API boundary with zod schemas from the shared `packages/validation` pack. Endpoint tables reference the schema by name; no inline regexes in this document.

| Schema (packages/validation) | Applied to fields | Notes |
|---|---|---|
| `ukPostcode` | `postcode` (GB) | Normalised to uppercase spaced form before write |
| `eircode` | `eircode` (IE) | Shape + routing-key plausibility at API layer only |
| `gbVatNumber` | `vat_number` where `country='GB'` | HMRC MOD97 checksum authoritative; GD/HA ranges exempted |
| `ieVatNumber` | `vat_number` where `country='IE'` | Format only in v1.0; checksum/VIES v1.1 |
| `companyNumberGB` | `company_number` (GB) | Companies House prefix rules |
| `croNumberIE` | `company_number`/`registration_number` (IE) | CRO format, beta |
| `e164Phone` | all phone fields | libphonenumber-backed |
| `emailAddress` | all email fields | RFC-practical, lowercased at write |
| `iban` | `suppliers.iban` | ISO 13616 MOD-97 |
| `sortCode` | `suppliers.sort_code` | Vocalink modulus rules |
| `countryCode` | `country` | IN-list GB/IE (mirrors DB K1) |
| `currencyCode` | currency fields | IN-list GBP/EUR (mirrors DB K2) |
| `isoDate` / `datePair` | date fields | ISO `YYYY-MM-DD`; start ≤ end enforced |
| `nonNegativeNumber`, `percentage0to100`, `confidenceScore` | quantities, factors, confidence | Mirrors DB K3 ranges |

The database enforces only IN-lists, ranges, presence and uniqueness. Frontend validates for UX only and is never trusted.

### 1.6 Idempotency

| Item | Rule |
|---|---|
| Uploads | Document upload is two-phase (init → complete, §6). Init accepts `Idempotency-Key` header; combined with `customer_documents.file_checksum` the service layer detects duplicate content and returns the existing document (`200`, `duplicate: true`) instead of a new row |
| Other POSTs | Mutations that create rows accept `Idempotency-Key`; replays with the same key + identical payload return the original response; same key + different payload → `409 IDEMPOTENCY_CONFLICT` |
| Queue writes | Worker-enqueueing endpoints are naturally idempotent: the pipeline state machine (§05) ignores duplicate enqueue requests for a document already in a non-terminal status |

### 1.7 Rate Limits

| Class | Limit (per `system_settings.api_rate_limit` family) | Scope |
|---|---|---|
| Authenticated reads | `api_rate_limit` req/min | user + organisation |
| Mutations | `api_rate_limit` / 2 per min | user + organisation |
| Upload init/complete | `max_file_upload_daily` per day; `max_documents_per_batch` per batch | organisation |
| Auth endpoints (§2) | 10 req/min | IP + user |
| Burst | `api_rate_limit_burst` | token bucket |

`429` responses include `error.retry_after`. Staff workspace internal routes have separate, higher limits.

---

## 2. Authentication (app-level)

Supabase Auth owns login, 2FA enrolment/verification, password reset and magic links; none of those are re-implemented here. These endpoints cover session context, org switching and profile.

| # | Path | Method | Auth (role/workspace) | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 1 | `/auth/session` | GET | Any authenticated | — | `user:{id,email,first_name,last_name,user_type,email_verified}`, `workspaces:[customer\|consultant\|staff]`, `memberships:[{organization_id,role,organization_name,is_active}]`, `consultant_profile_id?`, `staff_profile_id?` | 401 unauthenticated |
| 2 | `/auth/org-switch` | POST | Member or consultant with grant on target org | `organization_id` | `active_organization:{id,name,country,currency,role,subscription_status}`, `permissions:[…]` | 401; 403 TENANT_ACCESS_DENIED; 423 org suspended; 404 unknown org |
| 3 | `/auth/profile` | PATCH | Self | `first_name,last_name` (free text ≤100); `phone?` → `e164Phone` | Updated `users` row fields + `updated_at` | 401; 422 format |
| 4 | `/auth/beta-code/redeem` | POST | Authenticated, not yet in an org | `code` (matches `beta_access_codes.code`), `email` → `emailAddress` | `status`, `organization_id?` (if code auto-provisions), `magic_token` delivery notice | 401; 404/410 code invalid/expired/used; 422 |
| 5 | `/auth/accept-invite` | POST | Authenticated; email must match invite | `token` (`user_invitations.token`, hashed lookup) | `organization_id`, `role`, membership row id | 401; 403 EMAIL_MISMATCH; 404/410 token invalid/expired; 409 already a member |
| 6 | `/auth/erasure-request` | POST | Self, or staff, or service context (per `anonymise_user` actor guard) | `confirm_email` → `emailAddress`, `reason?` | `request_id`, `status:"scheduled"` — execution via approved runbook only; irreversible | 401; 403 unauthorised actor; 409 already anonymised |

Audit: org-switch, invite acceptance, erasure request and beta redemption write `audit_logs` / `activity_logs` rows (service layer concern, not separate endpoints).

## 3. Organizations (+ members, invites, metadata)

Organisation creation is service-role only (no `authenticated` INSERT policy on `organizations` by design); the onboarding endpoint below runs in a server-side privileged path.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 7 | `/organizations` | POST | Authenticated (onboarding, server path) | `name`; `country` → `countryCode`; `company_number?` → `companyNumberGB`/`croNumberIE`; `vat_number?` → `gbVatNumber`/`ieVatNumber`; `postcode?` → `ukPostcode`; `eircode?` → `eircode`; `currency` → `currencyCode` (defaulted by country); `primary_contact_email` → `emailAddress`; `industry?, sector?, company_size?` | Full org row incl. `id, subscription_status, trial_start_date, trial_end_date, default_factor_year, is_active` + created `organization_members` (owner) row | 401; 409 company_number exists (K5); 422 |
| 8 | `/organizations/current` | GET | Member/consultant (tenant header) | — | Org row fields incl. `country, currency, timezone, reporting_standard, secr_enabled, financial_year_end, default_factor_year, vat_registered, is_active, archived_at` | 401; 403; 404 |
| 9 | `/organizations/current` | PATCH | owner/admin | Any of: `name, industry, sector, company_size, website, timezone, reporting_standard, financial_year_end, preferred_units, default_factor_year, address fields (postcode→ukPostcode, eircode→eircode), primary/billing contacts (email→emailAddress, phone→e164Phone), vat_number→gbVatNumber/ieVatNumber, vat_registered, sic_code, nace_code` | Updated org row | 401; 403; 422; 423 |
| 10 | `/organizations/current/metadata` | GET / PATCH | GET: member+; PATCH: owner/admin | PATCH: `total_employees, full_time_employees, …, annual_revenue, ebitda, total_assets, total_facilities, total_floor_area_sqm, occupied_floor_area_sqm, renewable_energy_percentage→percentage0to100, carbon_offset_percentage→percentage0to100, reporting_standard, fiscal_year_start/fiscal_year_end→isoDate+datePair, primary/sustainability contacts, industry_sector, sic_code, custom_metrics` | `organization_metadata` row | 401; 403; 422; 423 |
| 11 | `/organizations/current/members` | GET | member+ | `?role?, ?search? (trigram on user email/name), cursor params` | `[{id, user_id, email, first_name, last_name, role, is_active, created_at}]`, `next_cursor`, `has_more` | 401; 403 |
| 12 | `/organizations/current/members/{memberId}` | PATCH | owner/admin; owner-only for role=owner | `role ∈ {owner,admin,member,viewer}` and/or `is_active` | Updated membership row | 401; 403; 404; 409 last-owner demotion; 423 |
| 13 | `/organizations/current/members/{memberId}` | DELETE | owner/admin | — | `204` (row deactivated: `is_active=false`; history retained) | 401; 403; 404; 409 last-owner removal; 423 |
| 14 | `/organizations/current/invitations` | POST | owner/admin | `email` → `emailAddress`; `role ∈ {admin,member,viewer}`; `expires_at?` → future `isoDate` (default +14d) | `{id, email, role, status:"pending", expires_at}` — token never returned in body; delivery via Email Worker | 401; 403; 409 pending invite exists for email; 422; 423. Writes `user_invitations` only — `pending_invites` is write-blocked |
| 15 | `/organizations/current/invitations` | GET | owner/admin | `?status?` ∈ {pending, accepted, expired, revoked} | Invitation list (token redacted) + cursor envelope | 401; 403 |
| 16 | `/organizations/current/invitations/{invitationId}` | DELETE | owner/admin | — | `status:"revoked"` row | 401; 403; 404; 409 already accepted; 423 |
| 17 | `/organizations/current/subscription` | GET | owner/admin | — | `customer_subscriptions` row: `plan, status, ai_extraction_limit/used, batch_upload_limit, manual_extraction_pages_included/used, currency` + `usage_tracking` current month | 401; 403; 404 |

## 4. Facilities (+ assets)

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 18 | `/facilities` | POST | member+ (viewer excluded) | `name`; `country` → `countryCode`; `postcode?` → `ukPostcode`; `eircode?` → `eircode`; country-conditional rule: `country='GB'` ⇒ postcode expected, `country='IE'` ⇒ eircode required (API-layer rule; DB holds presence CHECK postcode-or-eircode); `type?, address_line1/2?, city?, county?, region?, meter_mpan_mprn?`, `latitude?/longitude?` (range ±90/±180) | Facility row incl. `id, is_active` | 401; 403; 422 (incl. neither postcode nor eircode); 423 |
| 19 | `/facilities` | GET | viewer+ | `?is_active?, ?country?, ?search?, cursor` | Facility list + cursor envelope | 401; 403 |
| 20 | `/facilities/{id}` | GET / PATCH | GET viewer+; PATCH member+ | PATCH: any create field + `is_active` | Facility row | 401; 403; 404; 422; 423 |
| 21 | `/facilities/{id}/assets` | POST / GET | POST member+; GET viewer+ | POST: `name, type?, description?, capacity?→nonNegativeNumber, capacity_unit?, serial_number?, installation_date?→isoDate` | Asset rows scoped to facility | 401; 403; 404 facility; 422; 423 |
| 22 | `/assets/{id}` | PATCH / DELETE | member+ | PATCH: any asset field + `is_active`; DELETE = deactivate (`is_active=false`) | Asset row / `204` | 401; 403; 404; 423 |

## 5. Suppliers

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 23 | `/suppliers` | POST | member+ | `name`; `country` → `countryCode`; `vat_number?` → `gbVatNumber`/`ieVatNumber`; `company_number?` → `companyNumberGB`/`croNumberIE`; `postcode?`/`eircode?`; contact fields (`primary_email` → `emailAddress`, `primary_phone` → `e164Phone`); `iban?` → `iban`; `sort_code?` → `sortCode` (GB only — rejected when `country='IE'`); `payment_currency?` → `currencyCode`; `supplier_category_id?, supplier_type?, contract_start/end→datePair, certification_*, payment_terms?` | Supplier row | 401; 403; 409 duplicate `(organization_id, vat_number)` or `(organization_id, company_number)` (K5 partial uniques); 422; 423 |
| 24 | `/suppliers` | GET | viewer+ | `?search?` (trigram name/vat_number — powers autocomplete + "did you mean?"), `?supplier_category_id?, ?is_active?, ?country?, cursor` | List incl. `similarity` score when `search` present | 401; 403 |
| 25 | `/suppliers/{id}` | GET / PATCH | GET viewer+; PATCH member+ | PATCH: any create field | Supplier row incl. emissions summary fields | 401; 403; 404; 409; 422; 423 |
| 26 | `/suppliers/{id}/emissions-summary` | GET | viewer+ | `?reporting_year?` | Aggregates from `emissions_logs` where `supplier_id` = id: totals per `scope`, per year, document count | 401; 403; 404 |
| 27 | `/supplier-categories` | GET | viewer+ | — | Reference list (read-only reference table) | 401 |

## 6. Documents (upload init/complete, review, confirm)

Two-phase upload against Supabase Storage private buckets with signed URLs. Status vocabulary is frozen: `customer_documents.status ∈ {uploaded, pending, processing, processed, manual_review, verified, approved, rejected, failed}`.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 28 | `/documents/uploads/init` | POST | member+ | `Idempotency-Key` header; `file_name, file_type (MIME allowlist), file_size_bytes` ≤ `max_upload_size_mb`; `file_checksum` (SHA-256 hex, 64 chars); `asset_id?` or `facility_id?`; `document_type_code?`; `supplier_id?`; `billing_period_start/end?` → `datePair`; `batch_id?` | `{document_id, status:"uploaded", signed_upload_url, upload_expires_at, duplicate:false}` or `{duplicate:true, existing_document_id, existing_status}` when checksum matches | 401; 403; 404 asset/facility/supplier; 413 size; 422; 423; 429 daily limit (`max_file_upload_daily`) |
| 29 | `/documents/uploads/{documentId}/complete` | POST | member+ (same uploader) | `file_checksum` (re-verified against stored bytes); `page_count?` | `{document_id, status:"pending", queue_entry_id}` — enqueues `document_processing_queue` (status `pending`) and `processing_queue`; pipeline choreography per §05 | 401; 403; 404; 409 checksum mismatch / already completed / idempotency conflict; 423 |
| 30 | `/documents/batches` | POST | member+ | `batch_name?, batch_type?` ∈ plan allowance; array of init payloads (≤ `max_documents_per_batch`); `manual_extraction_requested?` | `upload_batches` row `{id, total_files, status}` + per-file init results as #28 | 401; 403; 413 batch size; 422; 423; 429 plan batch limit |
| 31 | `/documents/batches/{id}` | GET | viewer+ | — | Batch row: `total_files, processed_files, error_count, status, completed_at` + per-document status list | 401; 403; 404 |
| 32 | `/documents` | GET | viewer+ | `?status?` (frozen IN-list), `?document_type_code?, ?supplier_id?, ?asset_id?, ?billing_period_from/to?, ?search? (file_name), cursor` | Document list: `id, file_name, file_type, status, document_type_code, confidence_score, calculated_emissions_kg_co2e, billing_period_*, upload_date, supplier_id` | 401; 403 |
| 33 | `/documents/{id}` | GET | viewer+ | — | Full document row + signed download URL (short-lived) + `extracted_data, mapped_data` summaries + latest `customer_verifications` status | 401; 403; 404 |
| 34 | `/documents/{id}/classification` | PATCH | member+ | `document_type_code` (must exist in `document_types`/`document_type_categories`); `organization_classification?`; `organization_notes?` | Updated fields + `classification_by, classification_at` | 401; 403; 404; 409 status not classifiable; 422; 423 |
| 35 | `/documents/{id}/review` | GET | viewer+ | — | Review payload: `extracted_data, mapped_data, confidence_score`, AI mapping hints (`ai_mapped_facility_id/asset_id/supplier_id, ai_mapping_confidence` from queue row), factor used (`emission_factor_used` resolved against `emission_factors`), `calculated_emissions_kg_co2e` | 401; 403; 404; 409 document not in review state |
| 36 | `/documents/{id}/confirm` | POST | member+ | `approved: bool`; `mapped_data?` (corrected mapping: `facility_id, asset_id, supplier_id, document_type_code`); `rejection_reason?` (required when `approved=false`); `notes?` | `status` → `approved` (writes `customer_verifications` verified columns + `verification_logs`; emits `emissions_logs` row via service layer) or → `rejected` with reason; `customer_approved` on queue row | 401; 403; 404; 409 not in `customer_review`/verifiable status; 422; 423 |
| 37 | `/documents/{id}/request-manual-extraction` | POST | owner/admin | `notes?` | Queue row updated: `status:"manual_extraction", manual_requested_by/at`; `manual_review_queue` row created (`priority, sla_deadline` from `sla_definitions`) | 401; 403; 404; 409 already in manual path; 423; 402-style 403 plan pages exhausted (`manual_extraction_pages_used ≥ included`) |
| 38 | `/documents/{id}` | DELETE | owner/admin | — | Hard delete pre-soft-delete era (C13 deferred): removes storage object + row; audit row written | 401; 403; 404; 409 status in {approved, verified} — deletion blocked for audit; 423 |

## 7. Reports (+ SECR)

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 39 | `/reports` | POST | member+ | `report_type` (from `report_templates`); `reporting_year` (2000–2100); `report_name?`; `data_sources?` (scope/facility/supplier filters); `template_id?` | `report_generation_queue` row `{id, status:"pending", progress_percentage:0}`; generation is async (Report Generation + PDF workers) | 401; 403; 422; 423; 429 concurrent-generation limit |
| 40 | `/reports` | GET | viewer+ | `?report_type?, ?reporting_year?, ?status?, cursor` | List: `id, report_name, report_type, reporting_year, status, progress_percentage, current_step, completed_at` | 401; 403 |
| 41 | `/reports/{id}` | GET | viewer+ | — | Queue row + `generated_content` summary + `final_report_file_name, final_report_size_bytes` + signed URL to `final_report_url` | 401; 403; 404 |
| 42 | `/reports/{id}/edits` | PATCH | member+ | `user_edits` (jsonb patch against `generated_content` sections) | Updated row; `progress_percentage` reset triggers regeneration of affected sections | 401; 403; 404; 409 status=completed requires new version; 422; 423 |
| 43 | `/reports/{id}/versions` | GET / POST | GET viewer+; POST member+ | POST: `notes?, change_summary?` — snapshots current content into `report_versions` (`is_current` flip) | Version list `{version_number, file_name, is_current, created_by, created_at}` / new version row | 401; 403; 404; 409 duplicate (report_id, version_number) |
| 44 | `/reports/{id}/comments` | GET / POST | GET viewer+; POST member+ | POST: `section_id?, comment, comment_type?` | `report_comments` rows | 401; 403; 404; 422 |
| 45 | `/reports/comments/{commentId}/resolve` | POST | member+ | `resolution_notes?` | `is_resolved=true, resolved_at, resolved_by` | 401; 403; 404; 409 already resolved |
| 46 | `/reports/secr` | POST | member+; org must have `secr_enabled=true` | `reporting_year`; `include_intensity_ratios?` | SECR report job on `report_generation_queue` (`report_type:"SECR"`) — energy use, Scope 1/2, intensity ratio from `organization_metadata` floor area / turnover | 401; 403; 409 SECR not enabled for org; 422 (UK org required: `country='GB'`) |
| 47 | `/reports/secr/eligibility` | GET | viewer+ | — | Eligibility evaluation from `organization_metadata` (employees, turnover, balance sheet) + quoted-company flags from org row: `{eligible, thresholds_met:[…], missing_data:[…]}` | 401; 403 |
| 48 | `/report-templates` | GET | viewer+ | `?report_type?` | `report_templates` reference list | 401; 403 |
| 49 | `/reports/{id}/export` | POST | member+ | `format ∈ {pdf,csv,xlsx}` | `export_history` row + signed URL when ready (`status`, `expires_at`) | 401; 403; 404; 409 generation incomplete; 422 |

## 8. Notifications

Realtime delivery via Supabase Realtime on `notifications`; these endpoints manage state and history.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 50 | `/notifications` | GET | Self (recipient) | `?is_read?, ?notification_type?, ?priority?, cursor` | `{id, notification_type, title, message, priority, link, is_read, read_at, is_dismissed, created_at}` | 401 |
| 51 | `/notifications/{id}/read` | POST | Self (recipient only) | — | `is_read=true, read_at` | 401; 403 not recipient; 404 |
| 52 | `/notifications/read-all` | POST | Self | — | `{updated_count}` | 401 |
| 53 | `/notifications/{id}/dismiss` | POST | Self | — | `is_dismissed=true, dismissed_at` | 401; 403; 404 |
| 54 | `/notifications/delivery` | GET | Self | `?channel?, cursor` | `notification_delivery` rows (email/push/receipt evidence) | 401 |

## 9. Messages (conversations)

Realtime via Supabase Realtime on `messages` + `conversation_participants`; REST for history and mutations.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 55 | `/conversations` | POST | member+ (customer) or staff/consultant | `subject?`, `participant_user_ids:[…]` (tenant-checked), `is_urgent?`, `priority?` ∈ {low,normal,high,urgent} | Conversation row + `conversation_participants` created | 401; 403 participant outside org/grant; 422; 423 |
| 56 | `/conversations` | GET | Participant | `?status?, ?is_urgent?, cursor` (sort `last_message_at DESC`) | List incl. `unread_count, participant_count, last_message_at` | 401; 403 |
| 57 | `/conversations/{id}` | GET / PATCH | Participant; PATCH staff/creator | PATCH: `status` (open/closed), `priority, is_urgent, subject` | Conversation row (`closed_by, closed_at` on close) | 401; 403; 404 |
| 58 | `/conversations/{id}/messages` | POST | Participant | `content`; `parent_message_id?`; `attachments:[{file_name,file_url,file_size,mime_type}]` → `file_attachments` rows | Message row: `id, sender_id, sent_at, has_attachments` | 401; 403; 404; 409 conversation closed; 422; 423 |
| 59 | `/conversations/{id}/messages` | GET | Participant | `?before? cursor` | Message page (exclude `is_deleted`) + attachment signed URLs | 401; 403; 404 |
| 60 | `/conversations/{id}/read` | POST | Participant | `up_to_message_id?` | `conversation_participants.last_read_at` updated; `unread_count` recomputed | 401; 403; 404 |
| 61 | `/conversations/{id}/participants` | POST / DELETE | Staff/creator | `user_id` | Participant row (`is_active`) | 401; 403; 404; 409 already participant |

## 10. Tasks (consultant workspace)

Client-facing task management on `consultant_tasks`. Internal staff tasks are under Admin/staff (§13).

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 62 | `/consultant/tasks` | POST | Consultant (`can_manage_clients` or task creator) | `task_title, task_description?, task_type?, priority? ∈ {low,normal,high,urgent}, client_id? (must be in caller's `client_access`), assigned_to? (firm member), due_date? → isoDate` | Task row | 401; 403 client not granted; 422 |
| 63 | `/consultant/tasks` | GET | Consultant firm member | `?status?, ?client_id?, ?assigned_to?, ?due_before?, cursor` | Task list | 401; 403 |
| 64 | `/consultant/tasks/{id}` | GET / PATCH | Firm member; PATCH assignee/manager | PATCH: `status, assigned_to, due_date, priority, task_description` | Task row (`completed_at` set on completion) | 401; 403; 404; 422 |

## 11. Support (tickets + communication)

No dedicated tickets table exists in the frozen schema; tickets are `user_feedback` rows (type/severity/status) and support dialogue runs on `customer_communication` + conversations.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 65 | `/support/tickets` | POST | Any authenticated (org context optional) | `type ∈ {bug, feature_request, question, billing}`, `title, description`, `severity?`, `rating?` (1–5), `screenshot_url?, browser_info?, os_info?, url?` | `user_feedback` row `{id, status:"open"}` | 401; 422; 429 |
| 66 | `/support/tickets` | GET | Self (own rows); staff see all (§13) | `?status?, ?type?, cursor` | Ticket list `{id, type, title, severity, status, created_at, resolved_at}` | 401 |
| 67 | `/support/tickets/{id}` | GET | Owner or assigned staff | — | Ticket + `resolution_notes` + linked `customer_communication` thread | 401; 403; 404 |
| 68 | `/support/tickets/{id}/messages` | POST | Owner or staff | `content`, `is_internal?` (staff only — internal notes hidden from customer) | `customer_communication` row; notification emitted to counterpart | 401; 403; 404; 409 ticket resolved |

## 12. Audit (read-only)

Append-only tables; no mutation endpoints exist by design.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 69 | `/audit/activity` | GET | owner/admin (tenant scoped) | `?user_id?, ?action?, ?resource_type?, ?from?, ?to?, cursor` | `activity_logs` rows: `action, resource_type, resource_id, user_id, ip_address, created_at, details` | 401; 403 |
| 70 | `/audit/documents/{documentId}` | GET | viewer+ | — | Combined trail: `document_activity_log` + `processing_logs` + `verification_logs` for the document | 401; 403; 404 |
| 71 | `/audit/reports/{reportId}` | GET | viewer+ | — | `report_versions` history + `ai_content_history` provenance (model, tokens, cost) | 401; 403; 404 |
| 72 | `/audit/exports` | GET | owner/admin | `cursor` | `export_history` rows | 401; 403 |

## 13. Admin / Staff workspace

Staff identity via `staff_profiles` + `staff_roles`; all tenant data access is service-role with explicit org filters and full `staff_activity_log` audit.

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 73 | `/admin/organizations` | GET | Staff (support role+) | `?search? (trigram), ?country?, ?subscription_status?, ?is_active?, cursor` | Org list + subscription summary | 401; 403 |
| 74 | `/admin/organizations/{id}/suspend` | POST | Staff (ops role+) | `reason` | `is_active=false, archived_at` set — tenant becomes read-only platform-wide | 401; 403; 404; 409 already suspended |
| 75 | `/admin/organizations/{id}/reactivate` | POST | Staff (ops role+) | — | `is_active=true, archived_at=null` | 401; 403; 404 |
| 76 | `/admin/queues/manual-review` | GET | Staff | `?status?, ?assigned_to?, ?sla_breached?, ?priority_min?, cursor` (sort `priority_score DESC, sla_deadline ASC`) | `manual_review_queue` rows | 401; 403 |
| 77 | `/admin/queues/manual-review/{id}/assign` | POST | Staff (team lead+) | `assigned_to` (staff id) | Assignment updated (`assigned_by, started_at`); `review_assignment_history` row | 401; 403; 404; 409 status not assignable |
| 78 | `/admin/queues/manual-review/{id}/complete` | POST | Assigned staff | `manual_extraction_result / data_entry`, `staff_notes?`, `quality self-check` | `status:"completed", completed_at/by, review_time_seconds`; document returns to customer review pipeline | 401; 403; 404; 409 not assigned to caller; 422 |
| 79 | `/admin/queues/processing` | GET | Staff | `?queue_status?, ?sla_breached?, cursor` | `processing_queue` rows + `processing_assignments` | 401; 403 |
| 80 | `/admin/qc` | GET / POST | QC staff | GET: `?status?, cursor` on `qc_checks`/`qc_checklists`; POST `/admin/qc/{queueId}`: `qc_approved: bool, qc_notes?, errors:[qc_errors entries]` | QC outcome; on fail document returns to `manual_extraction` | 401; 403; 404; 409 wrong status |
| 81 | `/admin/support/tickets` | GET / PATCH | Staff | PATCH `/admin/support/tickets/{id}`: `status, assigned_to, resolution_notes` (sets `resolved_at`) | `user_feedback` rows | 401; 403; 404 |
| 82 | `/admin/tasks` | POST / GET / PATCH | Staff | `internal_tasks` fields + `task_assignments` (`assigned_to, due_date`) | Task/assignment rows | 401; 403; 404; 422 |
| 83 | `/admin/communication` | POST / GET | Staff | POST: `organization_id, communication_type, subject?, content, is_internal` | `customer_communication` rows | 401; 403; 404; 422 |
| 84 | `/admin/metrics` | GET | Staff (manager+) | `?date_from?, ?date_to?` | `staff_daily_performance, team_performance, sla_compliance, dashboard_metrics` | 401; 403 |
| 85 | `/admin/settings` | GET / PATCH | Staff (admin role) | `setting_key`, `setting_value` (jsonb; `is_editable` enforced) | `system_settings` / `queue_settings` rows | 401; 403; 404; 409 not editable |
| 86 | `/admin/sla-definitions` | GET / PATCH | Staff (admin role) | `document_type, priority_level, sla_hours, escalation_hours, is_active` | `sla_definitions` rows | 401; 403; 422 |
| 87 | `/admin/staff` | GET / PATCH | Staff (admin role) | `staff_profiles` + `staff_roles` management; workload rebalance | Staff rows + `staff_workload` | 401; 403; 404 |
| 88 | `/admin/users/{userId}/erasure` | POST | Staff (approved runbook, service context) | `reason` | Executes `anonymise_user` (irreversible); confirmation payload | 401; 403; 409 already anonymised |

## 14. Consultant (client management)

Cross-org access strictly via `consultant_clients` + `consultant_firm_members.client_access` (GIN-indexed array predicates).

| # | Path | Method | Auth | Request fields | Response fields | Errors |
|---|---|---|---|---|---|---|
| 89 | `/consultant/profile` | GET / PATCH | Consultant (self firm) | PATCH: branding (`brand_name, logo_url, primary_color, secondary_color, footer_text, email_from`), address (`postcode→ukPostcode, eircode→eircode, country→countryCode`), `vat_number→gbVatNumber/ieVatNumber, company_number→companyNumberGB/croNumberIE, support_email→emailAddress, support_phone→e164Phone, webhook_url (https), client_portal_url` | `consultant_profiles` row (`api_key` never returned — rotation endpoint only) | 401; 403; 422 |
| 90 | `/consultant/profile/api-key/rotate` | POST | Consultant owner | — | `{api_key_prefix, rotated_at}` — new key shown once; stored SHA-256 hashed | 401; 403 |
| 91 | `/consultant/clients` | POST | `can_manage_clients` | `client_name`; `organization_id` (target client org); `client_industry?`; contact fields (`client_contact_email→emailAddress, client_contact_phone→e164Phone`); `billing_plan?, billing_cycle?, tags?` | `consultant_clients` row (`status:"active"`); unique `(consultant_id, organization_id)` enforced (K5) | 401; 403; 409 client link exists; 404 org; 422 |
| 92 | `/consultant/clients` | GET | Firm member | `?status?, ?search?, ?tag?, cursor` | Client list + per-client `consultant_billing` usage summary | 401; 403 |
| 93 | `/consultant/clients/{id}` | GET / PATCH | Firm member with grant | PATCH: `status, notes, tags, billing_plan, billing_cycle, contact fields` | Client row | 401; 403; 404 |
| 94 | `/consultant/clients/{id}/access` | POST / DELETE | `can_manage_team` | `user_id` (firm member) — adds/removes client org id in `consultant_firm_members.client_access` | Updated `client_access` array | 401; 403; 404; 409 member lacks firm membership |
| 95 | `/consultant/clients/{id}/billing` | GET / PATCH | `can_manage_clients` | PATCH: `plan, auto_extraction_limit, manual_extraction_credit, billing_cycle, currency→currencyCode` | `consultant_billing` row incl. usage counters and `next_invoice_date` | 401; 403; 404; 422 |
| 96 | `/consultant/team` | GET / POST / PATCH | `can_manage_team` | POST: invite firm member (`user_id/email→emailAddress, role, can_*` permission flags); PATCH: flags + `is_active` | `consultant_firm_members` rows | 401; 403; 404; 409 duplicate membership |

---

**Endpoint count: 96** across 13 groups (Auth 6; Organizations 11; Facilities 5; Suppliers 5; Documents 11; Reports 11; Notifications 5; Messages 7; Tasks 3; Support 4; Audit 4; Admin/Staff 16; Consultant 8). Every group in the brief is covered; all names verified against the frozen dump + RC1 release notes; no SQL, no code, no new tables or columns introduced.
