## Section 8 — Security Review

This section records the security posture of the RC2 freeze as approved, not as audited. Every posture below is either already shipped in the RC1 migration package (files 001–006, verified by 007) or scheduled against a named release window in the Production Hardening Plan (§3/§4/§7). Nothing here re-opens a triaged decision: rejected mechanisms stay rejected, deferred mechanisms stay deferred, and each entry names the control that actually ships instead.

### 8.1 Row-Level Security — approved posture

RLS is the tenant-isolation boundary and its RC1 posture is frozen as-is for RC2. Approximately 160 policies cover the 36 tenant tables (four CRUD policies each), plus owner/scoped policies on `organizations`, `users` and `notifications`, and read policies on the ten reference tables. Two SECURITY DEFINER-style helpers, `is_org_member(uuid)` and `is_org_active(uuid)`, carry the predicates so policy bodies stay uniform and auditable.

| Posture element | Approved behaviour |
|---|---|
| Tenant isolation | Every tenant-table policy filters on `organization_id` via `is_org_member()`; consultant access adds the `consultant_clients` grant union and the `consultant_firm_members.client_access` array predicate (GIN-backed) |
| Suspend predicate | Write policies require `organizations.is_active = true`; suspending an organisation blocks member writes while reads continue — the churn lever that never deletes audit evidence |
| Organisation creation | Deliberately service-role only — no INSERT policy for `authenticated` on `organizations` |
| Verification gate | 007 §6a (no RLS-enabled table without a policy) and §6b (no org-bearing table without RLS) must both return empty; the Gate 4 penetration matrix must show zero cross-tenant rows for customer, consultant, staff and service roles |

**Rule: RLS is never weakened.** A policy found too tight is fixed by correcting the predicate or the data, never by disabling RLS, adding `FORCE ROW LEVEL SECURITY` exceptions, or widening to `USING (true)`. One cross-tenant sighting is a reportable ICO/DPC incident; the enabled-but-no-policy gate exists precisely because a silently unprotected table fails invisibly at demo scale and publicly in production.

### 8.2 Permissions — service-role versus authenticated paths

Two database roles carry the whole permission model, and the boundary between them is an enforcement rule, not a convention.

| Role | May do | May never |
|---|---|---|
| `authenticated` | Read/write own-tenant rows under RLS; execute `is_org_member`/`is_org_active`; execute `anonymise_user` only under the guarded self-service path | Touch another tenant's rows; create organisations; bypass the suspend predicate |
| `service_role` | Bypass RLS for server-side, worker, migration and erasure paths; execute all four RC1 functions; insert into audit/append-only tables | Appear in any client bundle, browser, mobile app or user-facing configuration |

Workers connecting as `service_role` **must filter `organization_id` in code** — the role bypasses the boundary, so the discipline moves to the application, and the Gate 4 matrix includes a service-role row to prove the filter exists. PUBLIC is revoked on all four RC1 functions. Privilege hardening (revoking UPDATE/DELETE on the append-only audit tables; dropping `updated_at` from them so no `trg_set_updated_at_*` trigger touches them) is a B-window item landing v1.0.1 — approved, scheduled, and not launch-gating.

### 8.3 JWT — platform ownership

JSON Web Tokens are owned end-to-end by Supabase Auth. The database performs no app-level JWT handling: no token minting, no signing-key storage, no custom claim manipulation in the application schema. Session and membership claims reach policies through Supabase's request context (`auth.uid()`), which is what `is_org_member()` reads. The corollaries are equally fixed: `users.password_hash` is dead-columned and never written (Supabase Auth is the IdP — the A-class ownership decision); per-user 2FA/lockout columns are REJECTED as parallel auth state (structural review C14), with TOTP and lockout belonging to the platform's `auth.mfa_*` responsibility; and the global `two_factor_required` flag is marketed honestly as a configuration intent, not an enforced control, until the platform feature ships.

### 8.4 Service Role — permitted usage register

The service role is the most powerful credential in the system and its permitted call sites are enumerated, not implied:

| Permitted use | Constraint |
|---|---|
| Organisation creation | Sole INSERT path into `organizations` (§8.1) |
| Queue workers (`document_processing_queue`, `processing_queue`, `report_generation_queue`, notification delivery) | Must filter `organization_id` in code; claim predicates must match the I2 partial indexes exactly |
| Erasure actor | `anonymise_user(uuid, uuid, text)` invoked only via the approved runbook; actor guard admits self, active staff, or service context |
| Migrations and data loads | Never run as a user-facing session |

The service key is never exposed client-side — not in the web bundle, the mobile app, environment-derived client configuration, or error telemetry. Suspected exposure is treated as a credential compromise: rotate, then investigate.

### 8.5 Audit — append-only, honestly told

The existing per-domain audit/activity log family (`audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, `review_audit_trail`, `user_activity_log`, `staff_activity_log`, `login_history` and peers) is kept: the per-domain taxonomy is a frozen ADR and consolidation is rejected (D6). The six append-only log tables deliberately carry no `set_updated_at` trigger (007 §7c must remain empty).

**Hash-chain tamper-evidence remains REJECTED (D5), and RC2 does not resurrect it.** The reason is evidentiary, not effort: the chain's verifier is the same principal as its writer (the service role / DBA can rewrite rows and re-hash the chain), so the construction proves nothing to an external auditor — security theatre. The honest storey ships instead: revoke UPDATE/DELETE on the audit tables (B-window privilege hardening, v1.0.1), no `updated_at` on append-only tables, and point-in-time-recovery backups. Genuine cryptographic tamper-evidence requires external anchoring and is a v2.x conversation.

### 8.6 GDPR — erasure and DSAR posture

The approved erasure model is **anonymise-in-place**, shipped in RC1 as `anonymise_user()` and **launch-gated** (Hardening Plan §3 item 22): hard delete is structurally impossible against ~40 referencing foreign keys, so erasure hashes `users.email` to `deleted-<sha256>@anonymised.invalid`, sets the name to "Deleted User", nulls credentials, deactivates the account, and scrubs profile PII across the consultant/staff/beta/feedback tables while preserving `users.id` and every FK — and leaving audit rows untouched. The procedure is irreversible by design, idempotent on re-run, and callable only under the actor guard (§8.4). Gate 5 requires a timed staging rehearsal against a production-like FK graph with a clean residual-PII scan before launch; the one-month statutory clock means the rehearsal, not the first live DSAR, is where the procedure earns trust.

DSAR posture is dual-regulator: ICO (UK) as primary supervisory authority, DPC (Ireland) for the beta cohort. v1.0 obligations beyond erasure are the PII inventory (§8.10), DSAR export expiry, waitlist/beta PII purge at GA, and the residency verification (Supabase region UK-London or eu-west-1 with backups co-located — one free configuration check on which every enterprise questionnaire's residency claim depends). Erasure self-serve UI and consent/PECR capture fields stay deferred (C24); v1.0 onboarding rests on contract/legitimate interest.

### 8.7 Data retention

Retention principle: **keep financial evidence for the statutory period, age out operational exhaust on schedule, and never let a retention job touch an audit-bearing row before its time.** The Companies Act 2006 baseline is ~6 years for financial records, which anchors the document/billing classes; Ireland's equivalent obligations are of the same order and the single schedule serves both markets. Operational logs age out far sooner: `processing_logs` 90 days; login/email logs 12 months; activity logs 12–24 months; audit tables 24 months. `retention_until` rides the document class so customer evidence carries its own expiry.

The retention pg_cron jobs are a **B-window item (v1.0.1, first weeks post-launch)** — the Hardening Plan's deliberate inversion of the audit's rating: on empty tables nothing ages out for months, so a cron job cannot be a day-one gate, while the erasure procedure (which can be demanded on day one) was promoted to A. Jobs run in small batches with dry-run counts first; rollback is dropping the job. Monthly RANGE partitioning as an alternative retention mechanism stays rejected (D4): low-seven-figure row counts after year one are trivially served by B-trees plus retention deletes, with a documented revisit trigger above 10–20M rows per table.

### 8.8 Soft delete — DEFERRED, and staying deferred

**Decision: soft delete (`customer_documents.deleted_at`) remains DEFERRED per the structural review (C13) and the Hardening Plan B-window; RC2 does not ship it and this document does not resurrect it.** The reasoning stands as written: the change is Small structurally but Medium application-wide — every document read path must gain filter discipline, and partial adoption leaks deleted rows into reported totals. At pre-revenue volumes nothing is unrecoverable via backups, so the undo path does not gate launch. What v1.0 does instead: tenant lifecycle is handled by `organizations.is_active` / `organizations.archived_at` (suspend preserves all rows; archive is deliberate and communicated), document lifecycle by the `customer_documents.status` vocabulary (`rejected`/`failed` terminal states), and disaster recovery by PITR backups. The C13 target window is early in the v1.0.x hardening cycle, while the table is young — the earliest safe moment, not a silent cancellation. RC2's verification obligation is negative and cheap: confirm no `deleted_at` column exists on `customer_documents`.

### 8.9 PII — register and classification

The PII register below is the v1.0 inventory the compliance pack maintains; classification drives masking, retention and erasure scoping.

| Class | Definition | Tables/columns (principal, not exhaustive) |
|---|---|---|
| **Identity** | Names a natural person | `users.email`, `first_name`, `last_name`; `staff_profiles.email`; `consultant_profiles` name/contact columns; `beta_users`, `waitlist` emails |
| **Credentials/secrets** | Grants access if disclosed | `consultant_profiles.api_key` (hashed, RC2 fix), `password_reset_tokens.token`, `user_invitations.token` (hashed); `users.password_hash` (dead-columned); `auth.magic_token` |
| **Financial-personal** | Payment/banking data | `suppliers.bank_name`, `bank_account`, `iban`, `swift_code`, `sort_code` (RC1); `consultant_billing` |
| **Behavioural** | Reveals activity patterns | `login_history` (incl. `ip_address`), `user_activity_log`, `staff_activity_log`, `activity_logs` |
| **Customer business data** | Tenant-confidential, not personal | `customer_documents` + `extracted_data`, `emissions_logs`, `organization_metadata`, `organizations.registered_address` |
| **Operational exhaust** | Short-retention telemetry | `processing_logs`, `email_logs`, `typing_status`/`user_presence` (interim purge until the Realtime migration, C21) |

Erasure scope follows the Identity and Credentials classes (`anonymise_user` coverage); retention classes follow §8.7; the Financial-personal class carries the §8.11 masking/encryption posture. `ip_address` standardisation on `inet` is deferred (C4) and rides the v1.1 retention work.

### 8.10 Secrets — plaintext fixes approved, envelope encryption deferred

| Item | Status | Detail |
|---|---|---|
| `consultant_profiles.api_key` plaintext | **Fix approved (A)** | SHA-256 hash + lookup prefix + rotation columns; rollback is roll-forward — re-issue keys, never reverse |
| `password_reset_tokens.token` plaintext | **Fix approved (A)** | Hashed; UNIQUE stays on `token`, dropped on `user_id` (closes the reset-DoS); latest-valid-wins in the app |
| `user_invitations.token` plaintext | **Fix approved (A)** | Hashed; `pending_invites` (the weaker parallel table — no token, expiry or status) is write-blocked, `user_invitations` canonical |
| Bank details at rest | **Masking approved (B-window, v1.0.2)** | API responses mask to last-4; storage untouched in v1.0 |
| Vault/KMS envelope encryption for bank columns | **Deferred (C30, v1.1)** | Needs a vault-versus-KMS provider decision that must not be rushed inside a launch sprint |

Rationale for the A rating on hashing: plaintext credentials defeat RLS — any escaped backup, verbose log or service-role context yields live keys, and the first such escape converts a marketing promise into a reportable incident.

### 8.11 Uploads

Duplicate detection is **approved and shipped**: `customer_documents.file_checksum` (SHA-256) gives deterministic duplicate detection on the primary pipeline entity; hard UNIQUE enforcement stays deferred (C2) until the duplicate-resolution UX exists in v1.1, because rejecting legitimate re-uploads before then punishes customers for the pipeline's own re-processing. File-type and MIME validation is an **API-layer responsibility by design** (the layering rule: integrity in the database, formats in the application — D1/K9 stay rejected); the database's upload-side obligations are structural only: `file_attachments.file_size` widened to int8 (the 2 GB int4 overflow was reachable by invoice bundles and would have failed the upload at the customer's highest-value moment) with non-negative size CHECKs, and queue rows landing with non-NULL `organization_id` and a valid status. Size limits are enforced at the API/storage layer against per-plan policy, not by the schema.

### 8.12 Storage buckets — posture statement

Supabase Storage follows the same tenancy discipline as the tables. Posture: **all customer-document buckets are private** (no public buckets for tenant content); **object paths are tenant-prefixed** (`<organization_id>/…`) so path layout mirrors the RLS boundary and a path alone can never guess another tenant's object; and **RLS on `storage.objects`** enforces the same membership predicate as the tables, with service-role-only writes from the ingestion workers. Bucket policies are verified in the same Gate 4 exercise as table policies — storage is not a side-door around the matrix.

### 8.13 Signed URLs

All client access to stored documents is via **short-expiry signed URLs** — minutes, not hours — generated server-side after an authorisation check against the requesting user's membership and role. Consultant access is **scoped to the `consultant_clients` grant set**: a consultant receives signed URLs only for tenants appearing in their grants (mirroring the §8.1 policy union), never for the firm-wide `client_access` superset without a corresponding grant. URLs are single-purpose (one object, one operation), never logged in full, and regeneration is cheap so expiry is kept aggressive. Staff-side document access rides the same mechanism — no persistent public or long-lived URLs exist anywhere in the product.

## Section 10 — Final Approval Checklist

Every row must carry its named evidence before the RC2 freeze is approved. There is no partial credit: one open row is a NO-GO.

| ☐ | # | Item | Acceptance criterion |
|---|---|---|---|
| ☐ | 1 | Naming conventions | All identifiers consistent and jurisdiction-neutral post-RC1 — `emission_factors`, `emission_factor_id`, `default_factor_year` in use; no `defra_*` remnant outside the documented rename trail (RC1 §Breaking Changes 1–3) |
| ☐ | 2 | Validation layering | Database carries exactly four rule shapes — IN-lists, ranges, presence, uniqueness (53 CHECKs, 002); all format validation (VAT/MOD97, CH/CRO, postcode, Eircode shape, phone, email) confirmed at the API layer, D1/K9 not resurrected (§8.11) |
| ☐ | 3 | Tables | Table inventory matches the approved register: zero tables added, one renamed; no T1/T3 (rejected) or T2 (deferred) artefact present |
| ☐ | 4 | Relationships | All 11 F1 foreign keys validated; FK/ON DELETE inventory complete with RESTRICT/NO ACTION on financial/audit tables; staging destructive-delete rehearsal matches the inventory (Plan §7 row 10) |
| ☐ | 5 | Constraints | 53 CHECKs and 7 UNIQUEs present and validated; `password_reset_tokens(user_id)` UNIQUE dropped, `token` UNIQUE retained; violation smoke script rejects out-of-list and negative writes (007 §5) |
| ☐ | 6 | RLS | ~160 policies live; 007 §6a/§6b empty (no enabled-no-policy table, no org-bearing table without RLS); Gate 4 penetration matrix shows zero cross-tenant rows for all four roles; suspend predicate demonstrated (§8.1) |
| ☐ | 7 | Performance | 18 targeted indexes + 7 unique-backed in place; Gate 7 load smoke green — claim-query partial indexes used, p95 within target at year-one volumes; no blanket-index creep (D2/D19) |
| ☐ | 8 | GDPR | `anonymise_user` rehearsed on staging (Gate 5): timed, residual-PII scan clean, idempotent, actor guard enforced; PII register (§8.9) current; DSAR export expiry and waitlist/beta purge scheduled |
| ☐ | 9 | UK launch readiness | `country` IN ('GB','IE'), currency IN ('GBP','EUR') enforced; GB fixtures pass end-to-end; residency evidence (UK-London or eu-west-1, backups co-located) archived (Plan §7 rows 3, 4, 24) |
| ☐ | 10 | Ireland beta readiness | IE fixture green: Eircode-only facility insert succeeds, both-NULL rejected; EUR default applied; minimal SEAI/EPA core factor set loaded and the Dublin fixture's Scope 2 resolves to the IE factor (Gate 3; §11 Phase B) |
| ☐ | 11 | Seed data | Staging seed holds only GB/IE rows; out-of-market `.de`/`.fr`/`.fi`/`.ai` seed users removed; IE org + facility fixtures present; no PII-flavoured marketing seed survives to GA (Plan §7 row 11; §11 Phase B) |
| ☐ | 12 | API ready | Application enums/constants exactly match the five K4 status/role vocabularies; normalised value writes only ('GB'/'GBP'); `file_checksum` populated on ingest; signed-URL generation scoped per §8.13 |
| ☐ | 13 | UI ready | Eircode-only facility forms ship; suspend/read-only state communicated; duplicate-upload prompt wired to `file_checksum`; trigram "did you mean?" UX on supplier/org name fields |
| ☐ | 14 | Mobile ready | No service-role key in any mobile bundle (§8.2/§8.4); all document access via short-expiry signed URLs; RLS-authenticated paths only |
| ☐ | 15 | No ADR conflicts | Per-domain audit taxonomy, additive-only posture, array columns and queue design untouched; C14/D6/D7/D8/D17 rejections intact — no platform-ownership or consolidation drift (§8.5, §8.3) |
| ☐ | 16 | No DEFER/REJECT leakage | No `deleted_at` on `customer_documents` (C13 stays deferred, §8.8); no hash-chain artefacts (D5, §8.5); no regex CHECKs, no enums, no partitioning, no `country_code`, no 2FA/lockout columns, no `api_keys`/`webhook_events` tables |
| ☐ | 17 | Migration-file inspection gate passed | Gate 1 "action zero" signed note on file reconciling the schema dump against the Supabase migration files; findings re-scored against reality (Plan §7 row 1) |
| ☐ | 18 | Verification SQL green | `007_rc1_verification.sql` §3, §5, §6, §7 all pass on a production-like restore; zero unvalidated constraints, zero orphans, zero policy gaps |
| ☐ | 19 | Rollback strategy accepted | Per-file rollback/roll-forward paths (RC1 §Rollback) reviewed; Gate 6 rehearsals done — snapshot restore for the org backfill, re-issuance for credential hashing; erasure irreversibility acknowledged |
| ☐ | 20 | **Approve RC2 freeze** | Rows 1–19 all evidenced and initialled; the freeze is approved for the §11 implementation order to consume |

## Section 11 — Implementation Order

The client's 13-phase roadmap, A–M, consumed against the RC2-approved schema. Phase A takes the RC1 migration package **as-is** — files 001–006 plus verification 007 — with no re-scoping: Gate 1's reconciliation note is the only permitted amendment, and it re-points findings at evidence rather than changing the package. Phase B includes the **DEFRA/DESNZ current-year factors, the minimal SEAI/EPA core set for the Ireland beta (grid electricity, natural gas, common liquid/gaseous fuels, current reporting year), the reference data, and seed-user cleanup** — the out-of-market `.de`/`.fr`/`.fi`/`.ai` seed users are removed and only GB/IE fixtures survive.

| Phase | Objective | Depends on | Database touchpoints | Exit criteria |
|---|---|---|---|---|
| **A — Database migration** | Deploy the RC1 hardening package to production: renames, 16 columns, 53 CHECKs, 7 UNIQUEs, 11 FKs, 13 NOT NULLs, 18+7 indexes, ~160 RLS policies, 4 functions, `set_updated_at` triggers. | Gate 1 note; Gate 2 staging data audit; Gate 6 rollback rehearsals | Migration files 001–006 applied in order; `007_rc1_verification.sql` | 007 §3/§5/§6/§7 green on production; zero breaking-change regressions in smoke suite; RLS penetration matrix clean |
| **B — Seed data** | Load factor and reference data for both markets; clean the seed set. Includes: DEFRA/DESNZ current-year factors (backfilled `factor_source`/`factor_set`), the minimal SEAI/EPA IE core set, units/document-types/glossary reference data, and removal of the `.de`/`.fr`/`.fi`/`.ai` seed users with IE org + facility fixtures added. | A | `emission_factors` (data only — structure already shipped), `units`, `document_types`, `roles`, seed block of `users`/`organizations`/`facilities` | Dublin fixture's Scope 2 resolves to the IE factor, not DEFRA; factor natural-key UNIQUE rejects a scripted duplicate; staging seed holds only GB/IE rows; Gate 3 Irish end-to-end fixture passes |
| **C — Storage buckets** | Stand up private, tenant-prefixed buckets with RLS on `storage.objects` per §8.12/§8.13. | A | `storage.objects` policies; `file_attachments`, `organization_files` path conventions | Cross-tenant signed-URL attempt fails; bucket policies verified in the Gate 4 exercise; no public bucket exists for tenant content |
| **D — Mock PDFs** | Generate representative GB/IE invoice/statement PDF fixtures to exercise the pipeline before live OCR. | A, B | `customer_documents` (fixture rows), `upload_batches`, `document_types` | Fixture set covers both jurisdictions (GB sort-code/postcode, IE Eircode/EUR cases) and exercises every `customer_documents.status` transition once on staging |
| **E — OCR** | Wire the OCR stage into the document processing queue for text extraction from uploads. | C, D | `document_processing_queue` (status transitions), `processing_logs`, `customer_documents.file_checksum` populated on ingest | Claim query uses `dpq_claim_idx` (predicate matches exactly); end-to-end fixture document moves `uploaded → processing → ai_extracted`-ready with non-NULL org; >2 GB synthetic path handled |
| **F — AI Extraction** | Land AI field extraction into `extracted_data` with confidence scoring and supplier auto-mapping hints. | E | `customer_documents.extracted_data`, `document_processing_queue` AI statuses, `ai_content_history`, 4 AI-mapping hint FKs, `suppliers` partial UNIQUEs | Extracted fixture values land in jsonb within the K3c confidence range; duplicate supplier identifiers rejected by the K5 partials; wrong-tenant mapping impossible under RLS |
| **G — Realtime Messaging** | Launch customer↔staff↔consultant messaging on the conversations model. | A | `conversations`, `messages`, `conversation_participants`, `message_activity_log`; presence tables (`typing_status`, `user_presence`) under interim UNIQUE+purge | Cross-tenant message read returns zero rows (Gate 4 class); `messages(conversation_id, created_at)` index used; unread badge path uses the unread-notifications partial index |
| **H — Notifications** | Deliver in-app and email notifications from queue and pipeline events. | G | `notifications`, `notification_templates`, `notification_delivery`, `email_templates`, `email_logs` | Every delivery row tenant-scoped and RLS-clean; dedup decision (keep one delivery table) executed per the B-window note; email log retention scheduled |
| **I — Customer Portal** | Ship the customer-facing portal: facilities, suppliers, documents, emissions dashboards. | B, E, F | `organizations`, `facilities` (Eircode path), `suppliers`, `customer_documents`, `emissions_logs` (+ `unit`/`scope`), `organization_members` | GB and IE onboarding complete end-to-end; SECR kWh totals computable without the factor join; suspend state renders read-only; portal runs entirely on `authenticated` + signed URLs |
| **J — Consultant Portal** | Ship the consultant workspace with grant-scoped multi-client access. | I | `consultant_profiles` (hashed `api_key`), `consultant_clients`, `consultant_firm_members.client_access` (GIN), `consultant_tasks`, `consultant_billing` (now `currency`-denominated) | Consultant sees exactly the granted-tenant union and nothing else (Gate 4 consultant row); `client_access` predicate resolves via GIN in EXPLAIN; no plaintext API key recoverable from a dump |
| **K — Internal Staff Portal** | Ship staff operations: manual review, QC, workload and SLA surfaces. | F, H | `processing_queue`, `manual_review_queue`, `qc_checks`/`qc_errors`/`qc_checklists`, `staff_profiles`, `staff_workload`, `sla_compliance`, `staff_activity_log` | Staff role row of Gate 4 clean; queue-claim partial indexes used by staff claim queries; erasure actor guard admits active staff per runbook; audit inserts succeed via service role |
| **L — Reports** | Generate versioned customer reports and exports from verified emissions data. | I, J | `report_templates`, `report_versions` (UNIQUE per version), `report_generation_queue`, `report_comments`, `export_history`, `emission_factors` provenance columns | Every generated figure traceable to a factor row stating unit, scope and source; regenerated report of the same version number rejected by UNIQUE; report claim query uses its partial index; GB and IE fixture reports reconcile to fixture expectations |
| **M — Public Launch** | GA cut-over: marketing purge, compliance pack closure, go-live checklist sign-off. | A–L; Section 10 rows 1–19 | `waitlist`/`beta_users` purge at GA; `system_settings` residency/backup evidence; retention pg_cron jobs armed (B-window v1.0.1) | Section 10 fully initialled (row 20); erasure rehearsal evidence archived; residency evidence in the compliance pack; out-of-market seed remnants confirmed absent in production; retention jobs scheduled with dry-run counts |

**Sequencing notes.** Phases C–F form the pipeline spine and must not be reordered; G–H are separable but H consumes G's tables. The B-window hardening items (audit privilege revocation, bank masking, retention jobs, soft-delete evaluation per C13) land in the v1.0.x releases after M, not inside any phase above — the roadmap consumes the RC2 freeze, it does not amend it. Where a phase exposes a schema need not in the approved register, the change returns through structural review; it is never improvised inside a phase.
