# CarbonTally v1.0 — Security Architecture

*Companion to `01_application_architecture.md`. Database frozen at RC2; post-migration names throughout (`emission_factors`, `emission_factor_id`, `emission_factor_used`, `default_factor_year`; `facilities.eircode`, `organizations.is_active`, `facilities.meter_mpan_mprn`, `suppliers.sort_code`). No SQL, no code, no seed data — specification prose and tables only.*

## 1. Authentication

**Supabase Auth is the sole identity provider and owns credentials end to end** (frozen decision): sign-in, JWT issuance and refresh, TOTP-based 2FA, lockout/back-off and password reset are platform responsibilities. Consequently `users.password_hash` is a dead column — never written by any code path — and no parallel `totp_secret`/`two_factor_enabled`/`backup_codes`/`failed_login_attempts`/`locked_until` columns exist; parallel auth state is rejected as two drifting credential stores. Marketing and enterprise questionnaires must describe 2FA/lockout exactly as the platform delivers them, no more.

**Session model.** The Supabase SSR pattern: short-lived access JWT plus refresh token in httpOnly, SameSite cookies; middleware refreshes near-expiry sessions; Server Components, route handlers and server actions build a per-request Supabase client bound to the session JWT. Logout revokes the refresh family. Sessions are per-identity, not per-organisation.

**Org switching.** A user may hold multiple memberships (`organization_members`), consultant grants (`consultant_clients`, `client_access` array) and/or a staff profile. The *active organisation* is carried by a stateless `X-Organization-Id` header — **no server-side session state is held for org context**; every switch and every request is re-validated server-side against membership/grant before the context is honoured, so client state is never trusted. The switching contract is proven by the frozen Gate 4 test: a user switching between two organisations sees exactly the union of their own tenants' rows, writes carry the correct `organization_id`, and no stale-tenant row survives the switch.

**Invitations and reset.** `user_invitations` is the canonical invite path (hashed token, expiry, status); `pending_invites` is write-blocked. Password reset is latest-valid-wins against `password_reset_tokens` (the UNIQUE on `user_id` was deliberately dropped to close the unauthenticated reset-DoS; `token` UNIQUE retained, tokens hashed).

## 2. Authorisation

**RLS-first.** Every tenant table is RLS-protected for the `authenticated` role under the frozen ~160-policy set; the caller's JWT is the authorisation context on every query. Application-level checks add capability granularity but never substitute for RLS.

**Role matrix (condensed).** ✔ = permitted under RLS + service-layer capability; — = denied; R = read-only.

| Resource (frozen tables) | Customer owner/admin | Customer member | Customer viewer | Consultant (granted client) | Staff |
|---|---|---|---|---|---|
| Organisation settings (`organizations`, `organization_metadata`) | ✔ | R | R | R (granted orgs) | ✔ ops, incl. suspend via `is_active`/`archived_at` |
| Members & invites (`organization_members`, `user_invitations`) | ✔ | — | — | — | ✔ support path |
| Facilities/assets (`facilities` incl. `eircode`, `meter_mpan_mprn`; `assets`) | ✔ | ✔ | R | ✔ granted orgs | R |
| Suppliers (`suppliers` incl. `sort_code`; categories) | ✔ | ✔ | R | ✔ granted orgs | R (bank fields masked) |
| Documents (`customer_documents`, `upload_batches`, `file_attachments`) | ✔ | ✔ | R | ✔ granted orgs | R for review duty |
| Pipeline queues (`document_processing_queue`, `manual_review_queue`, `manual_extraction_*`) | status R | status R | — | status R | ✔ review/QC actions |
| Approvals (`customer_verifications`, `customer_review_log`) | ✔ approve | ✔ approve | — | R | R audit |
| Emissions (`emissions_logs`, `emission_factors`) | ✔ entries / factors R | ✔ entries | R | ✔ granted orgs | R |
| Reports (`report_versions`, `report_comments`, exports) | ✔ | ✔ | R | ✔ granted orgs | R |
| Messaging (`conversations`, `messages`, participants) | ✔ in-org threads | ✔ | ✔ | ✔ threads they participate in | — unless participant |
| Notifications (`notifications`) | own rows | own rows | own rows | own rows | own rows |
| Billing (`customer_subscriptions`, `usage_tracking`, `consultant_billing`) | owner ✔ / admin R | — | — | own firm billing | ✔ ops |
| Audit/activity logs (`audit_logs`, `activity_logs`, `*_activity_log`) | R own org (defined surfaces) | R scoped | — | R scoped granted orgs | ✔ |
| Staff internals (`staff_*`, `processing_queue`, assignments) | — | — | — | — | ✔ |

Notes: consultant access resolves as a policy union over `consultant_clients` plus the GIN-indexed `consultant_firm_members.client_access` array — a consultant sees exactly granted tenants and nothing else. Staff authority is exercised through the frozen staff policies and is journaled on every privileged read path. The service role sits outside this matrix entirely (§6).

## 3. JWT and Org-context Resolution

- **Claims**: the Supabase-issued JWT carries the subject (user id), session/expiry and the `authenticated` role; custom claims are kept minimal — tenant authorisation is *not* baked into the token, because membership and consultant grants change without re-login. Tenant truth lives in the database and is enforced by RLS per query.
- **Resolution flow**: request arrives → middleware refreshes session → server resolves the requested org context (route param or session attribute) → service layer asserts the user is a member (`organization_members`) or a granted consultant (`consultant_clients`/`client_access`) or an authorised staff actor for the route class → all queries run under the user's JWT so RLS re-derives the same boundary at the database. This double derivation (app asserts, RLS enforces) means a context-resolution bug degrades to zero rows rather than cross-tenant rows.
- **Suspended tenants**: `is_org_active(uuid)` in write policies blocks member writes when `organizations.is_active = false`; reads continue; the UI renders read-only with a banner. Context resolution refuses to set a suspended org as a *write* context.

## 4. Supabase Auth (frozen ownership)

2FA (TOTP enrolment, verification, recovery codes), lockout/credential-stuffing back-off, and password reset delivery are owned by Supabase Auth — this is a frozen platform decision, not a deferral. The application responsibilities are: configure the platform controls (MFA enforcement policy per plan, rate limits on auth endpoints), present honest security claims to customers, keep `users` as a profile/tenancy table with the dead `password_hash` column never written, and route all recovery flows through Auth so there is exactly one credential store. The consultant API key (`consultant_profiles.api_key`, hashed — see §7) is a separate, non-login credential for server-to-server consultant integrations and does not interact with Auth.

## 5. Row-Level Security

- **Posture**: the frozen RC2 set — up to ~160 policies: 36 tenant tables × 4 CRUD policies, 2 on `organizations`, 2 each on `users`/`notifications`, 10 reference-table read policies; create-if-absent against pre-existing policies, which stand. RLS is enabled on every tenant table; no FORCE ROW LEVEL SECURITY anywhere (table-owner flows unaffected); the verification gates require §6a/§6b emptiness — no RLS-enabled-no-policy table and no org-bearing table without RLS.
- **Helper functions**: `is_org_member(uuid)` and `is_org_active(uuid)` (executable by `authenticated` and `service_role`; PUBLIC revoked) are the frozen policy primitives. Membership, consultant-grant and staff predicates resolve through these plus the `client_access` array predicate (GIN-served).
- **Organisation creation**: intentionally service-role only — no INSERT policy for `authenticated` on `organizations`; tenant provisioning is a privileged server flow.
- **Inactive-org suspension**: write policies require `organizations.is_active = true`; setting `is_active = false` / `archived_at` blocks all member writes while reads remain — the churned-customer lever that never requires deleting audit evidence. Offboarding communicates read-only state in all workspaces.
- **Penetration matrix (Gate 4)**: scripted cross-tenant SELECT/INSERT/UPDATE/DELETE attempts per role (customer, consultant, staff, service) against every tenant table class; one cross-tenant row from any role is a launch-stopping failure.

## 6. Service Role

The service role bypasses RLS and is the platform's most dangerous credential; its use is confined to a **registered set** — any new use requires architecture sign-off and an entry here:

| Registered use | Context | Tenant safety |
|---|---|---|
| Organisation creation/provisioning | app server privileged flow | Creates the tenant; subsequent writes carry `organization_id` |
| Worker queue claims and pipeline writes (`document_processing_queue`, `processing_queue`, `report_generation_queue`, stage outputs) | `apps/workers` | Every query filters `organization_id` in code — code-review-gated invariant, Gate 4-tested |
| Erasure via `anonymise_user(uuid, uuid, text)` | runbook-invoked, actor-guarded (self, active staff, or service context) | Idempotent; irreversible by design |
| Append-only audit/log writes | service layer, all modules | Insert-only; no UPDATE/DELETE grants (hardening v1.0.1) |
| Signed-URL issuance and Storage lifecycle (quarantine promotion, retention deletes) | server/workers | Issued only after an RLS-checked authorisation read; tenant-prefixed paths re-asserted |

**Custody**: the key lives only in server-side environment secrets / Supabase Vault; it is never in the repository, never in client bundles (the `packages/supabase` service-role factory is import-guarded so client bundling fails the build), never in logs or error messages (pino redaction list). **Rotation**: scheduled rotation plus immediate rotation on any suspicion of exposure; rotation is a config deploy, no code change; both app server and workers pick up the new key at restart. Client-side use is an architectural impossibility by construction, verified in CI bundle inspection.

## 7. Secrets and Sensitive Data

- **Hashed at rest per RC2** (frozen): `consultant_profiles.api_key`, `password_reset_tokens.token`, `user_invitations.token` are stored SHA-256 hashed with a lookup prefix; API keys carry rotation columns and are displayed once at issuance. Plaintext credential recovery from any dump, backup or log must be impossible — verified on staging.
- **Bank details**: `suppliers.sort_code` and account fields are masked to last-4 in every API response and log line; full values never leave the service layer. Envelope encryption (vault/KMS) is a v1.1 provider decision; masking is the v1.0 control.
- **Repository hygiene**: no secrets in the repo — enforced by CI secret scanning and environment-variable injection at deploy; `.env` templates carry names only.
- **PII minimisation in telemetry**: Sentry events are scrubbed before send; pino redaction covers tokens, signed URLs, bank details and classified PII fields; Realtime payloads carry ids, not content, where feasible.

## 8. Rate Limiting

Three layers, consistent with the `system_settings.api_rate_limit` posture (a settings commitment, not an API product):

| Layer | Scope | Mechanism | Response |
|---|---|---|---|
| Edge | per-IP, unauthenticated surfaces (sign-in, reset, invite acceptance, webhooks) | Upstash Redis sliding-window counters at the Next.js edge | 429 + back-off headers; auth endpoints stricter and paired with Supabase Auth lockout |
| Per-organisation | API actions and mutations (uploads, exports, report generation requests) keyed by `organization_id` | Redis counters seeded from plan limits; plan ceiling from `customer_subscriptions`/`usage_tracking` (`used ≤ limit`) | 429 with upgrade CTA where plan-driven |
| Auth endpoints | sign-in, sign-up, reset, invite redeem | Edge limits plus Supabase Auth platform throttling | 429; alerting on distributed patterns |

Abuse handling: repeated 403s and 429s feed Sentry alerting; the unread-badge, messaging and queue-status Realtime paths are subscription-scoped and cannot be used as amplification loops.

## 9. Audit Logging

- **Append-only set (frozen taxonomy)**: `audit_logs`, `activity_logs`, `processing_logs`, `email_logs`, plus the per-domain journals (`user_activity_log`, `document_activity_log`, `message_activity_log`, `conversation_activity_log`, `verification_activity_log`, `customer_review_log`, `review_audit_trail`, `processing_audit_trail`). Consolidation is rejected (frozen ADR); a unified read-only view is a v1.1 reporting convenience.
- **Write discipline**: inserts via service role from the service layer/workers only; the six core append-only tables deliberately carry no `updated_at` triggers; privilege hardening (revoke UPDATE/DELETE) lands v1.0.1 so the only writer is insert-only.
- **Hash-chain explicitly rejected**: a tamper-evident chain whose verifier is the same principal as its writer has no external evidentiary value. The honest tamper storey is privilege revocation + dropped `updated_at` + Supabase PITR; external anchoring may be revisited in v2.x.
- **Retention classes** (v1.0.1 schedule): processing 90 days; login/email 12 months; activity 12–24 months; audit 24 months; erasure leaves audit rows untouched (anonymised subject, intact referential graph).

## 10. File Validation

- **At the API layer** (the format-validation authority): MIME/type allowlist per document class (invoices, statements, evidence images/PDF), extension/MIME agreement check, per-plan and platform size limits enforced before a signed upload URL is issued (post-RC2 int8 sizes remove the 2 GB overflow class but limits remain policy).
- **Checksum duplicate detection**: SHA-256 computed on upload, stored in `customer_documents.file_checksum`; same-checksum re-upload in the same organisation triggers a duplicate prompt (advisory in v1.0; hard UNIQUE is a v1.1 decision tied to duplicate-resolution UX so legitimate re-uploads are never rejected).
- **Post-upload verification**: workers re-verify size and checksum against the registered row before processing; a mismatch fails the document rather than processing unverified content.
- **Storage separation**: unscanned content lives in the `temp-uploads` bucket; download URLs are issuable only for scan-clean objects promoted into `documents`.

## 11. Malware Scanning

- **Pipeline stage**: scanning happens in `temp-uploads` **before the complete-move into `documents`**, and before OCR. The worker fetches the object from `temp-uploads` via service-role signed URL, submits to the scanner, and records the verdict in processing logs.
- **Quarantine posture**: infected or unscannable → document `failed`, object **retained in the `quarantine/` prefix** for investigation (not deleted immediately), uploader notified, no download URL ever issued for the object; clean → object moved from `temp-uploads` into the tenant document prefix and downstream stages proceed.
- **Coverage**: all inbound file surfaces — customer documents, message attachments (`file_attachments`), organisation files (`organization_files`); generated exports are outbound-only and re-validated at issuance.
- **Fail-closed**: scanner outage pauses the stage (queue rows stay `pending`/`processing` under retry policy); nothing is marked clean by default.

## 12. GDPR and Data Protection

- **Controllers/regulators**: UK launch under UK GDPR (ICO); Ireland beta under EU GDPR (DPC). Residency verified: Supabase region UK-London or eu-west-1 with backup location matching (`system_settings.backup_storage_location` evidence in the compliance pack).
- **Erasure (launch-gated, frozen procedure)**: `anonymise_user(uuid, uuid, text)` — anonymise-in-place because hard delete is structurally impossible against ~40 FK references. It hashes email to `deleted-<sha256>@anonymised.invalid`, sets the name to "Deleted User", nulls credentials, deactivates the account, and scrubs profile PII across consultant/staff/beta/feedback tables while preserving `users.id` so the referential graph (invoices, audit rows, emissions evidence) stays intact. It is **irreversible**, idempotent on re-run, and actor-guarded (self, active staff, or service context); invocation is runbook-only with the Gate 5 staging rehearsal (timed, production-like FK graph, residual-PII scan clean) as the standing evidence.
- **DSAR**: one-month statutory clock; export assembled from the service layer across the frozen tables (identity, documents metadata, emissions, messages, logs) delivered as a time-limited signed-URL data pack with expiry journaled; erasure requests execute the runbook above; both tracked in the compliance log.
- **Retention**: ~6 years for financial/accounting records consistent with the Companies Act obligations (UK) and equivalent Irish requirements; operational log classes per §9; document class carries `retention_until`; waitlist/beta PII purged at GA; retention jobs run as scheduled worker jobs with dry-run counts first.
- **Lawful basis and notices**: contract/legitimate interest at onboarding; consultant processing governed by DPA; OCR/AI providers operate under DPAs with minimal-payload rules.

## 13. Backups

- **Posture**: Supabase managed backups with **Point-in-Time Recovery (PITR)** as the restoration mechanism; PITR is also a named component of the audit tamper storey (with the hash-chain rejected, PITR plus privilege hardening is the integrity narrative).
- **Residency**: backup storage location matches the verified region (UK-London / eu-west-1) and is evidenced in the compliance pack.
- **Restore rehearsal**: scheduled rehearsal each release cycle — restore to an isolated project, verify row counts on hot tables (`customer_documents`, `emissions_logs`, `organization_members`), verify RLS posture survives, time the operation; results recorded against the DR runbook. The pre-migration snapshots retained from the RC programme are the only un-backfill path for the tenancy backfill and are preserved accordingly.
- **Storage objects**: bucket lifecycle plus provider redundancy; document objects are re-derivable from the customer re-upload path only as a last resort — Storage backup coverage is part of the rehearsal checklist.

## 14. Disaster Recovery

- **Targets**: **RTO 4 hours**, **RPO 15 minutes** (PITR window granularity) for the core platform — database, Auth, Storage, Realtime; workers and edge redeploy from source within the RTO. These are launch targets, reviewed against the first year's incident history.
- **Runbook outline**:
  1. **Declare**: on-call confirms scope (region loss vs data corruption vs credential compromise) and declares the incident; comms lead assigned; status page updated.
  2. **Data corruption / bad deploy**: identify corruption window; PITR-restore to an isolated project at the pre-incident point; export affected tenant slices; selective re-application under service role with `organization_id` filters; replay affected queue rows (jobs are idempotent).
  3. **Region/platform loss**: provision in the alternate approved region (within UK/EU residency), restore latest PITR base, repoint environment secrets, redeploy `apps/web` and `apps/workers`, re-verify RLS penetration matrix smoke subset before reopening traffic.
  4. **Credential compromise**: rotate service-role key and provider secrets (§6), invalidate sessions via Supabase Auth, audit the append-only logs for the exposure window, ICO/DPC assessment within 72-hour notification duty if personal data is implicated.
  5. **Recover and verify**: Gate 4 smoke subset (cross-tenant matrix on restored data), pipeline end-to-end fixture (upload → confirmed emissions), Irish fixture (Dublin Scope 2 resolves to the IE factor), then reopen; post-incident review feeds the runbook.
- **Principles**: workers are stateless and disposable; the database is the only irreplaceable state; every recovery path ends with the penetration-matrix smoke subset because a restore that re-opens a tenancy hole is worse than downtime.

---

*Document 07 of the architecture set. Companion: `01_application_architecture.md`. All names per RC2 freeze; no SQL, code or seed data specified.*
