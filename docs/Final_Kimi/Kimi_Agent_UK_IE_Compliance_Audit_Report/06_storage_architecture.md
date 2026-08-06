# CarbonTally — Storage Architecture (RC2-Frozen)

*Status: architecture specification only. Database frozen at RC2 — no SQL, no code, no migrations, no seed data. Consistent with `CarbonTally_RC2_Architecture_Freeze.md` §6–§7 and §8.12–§8.13, and with `008_RC1_RELEASE_NOTES.md` post-migration table/column names (`emission_factors`, `emission_factor_used`, `customer_documents.file_checksum`). All volume figures are stated assumptions, not measurements.*

## 1. Supabase Storage Layout — Overview

Bytes live in Supabase Storage; metadata lives in Postgres. The database tables carry the object *path* in the `file_url`-family columns (`customer_documents.file_url`, `file_attachments.file_url`, `manual_review_queue.file_url`, `export_history.file_url`, `report_generation_queue.final_report_url`, `organization_files.file_url`, logo columns) — never a public URL and never a long-lived signed URL. Signed URLs are generated server-side on demand and are never persisted (persisted URLs expire and leak; paths do not).

Fixed posture (from the freeze, §8.12–§8.13 — restated, not re-decided):

| Decision | Posture |
|---|---|
| Bucket visibility | **All buckets private.** No public bucket exists anywhere in the system, including branding imagery. |
| Object path layout | **Tenant-prefixed**: `{organization_id}/…` on every tenant-content bucket, mirroring the RLS boundary so a path alone can never reach another tenant's object. |
| Authorisation | **RLS on `storage.objects`** with the same membership predicate as the tables; worker/ingestion writes are service-role only. Verified in the same Gate 4 exercise as table policies. |
| Client access | **Short-expiry signed URLs** (minutes, not hours), minted server-side after an authorisation check against the requesting user's membership and role. |
| Upload flow | **Two-phase init/complete**: `init` validates (MIME/type/size at the API layer per the layering rule — formats in the application, integrity in the database), computes/records SHA-256 into `customer_documents.file_checksum` for duplicate detection, and returns a signed upload URL; `complete` confirms the object landed, finalises the metadata row, and enqueues `document_processing_queue` with status `pending`. |
| Workers | Virus scan → OCR/extraction workers read from storage with service-role credentials; they never receive client-signed URLs. |

## 2. Bucket Structure — Minimal Set

Five buckets. Each must justify its existence against a distinct lifecycle, access pattern, or risk class; no bucket is created "for tidiness".

| Bucket | Contents | Justification (why separate) |
|---|---|---|
| `documents` | Customer-uploaded source documents (invoices, bills, statements) backing `customer_documents` / `document_processing_queue` / `manual_review_queue` | The crown-jewel bucket: highest sensitivity (supplier PII, financial data), longest retention, strictest access. Isolating it lets retention, audit, and erasure policy target one bucket precisely. |
| `temp-uploads` | Objects from phase-1 `init` that have not yet been `complete`d | Distinct **abandonment lifecycle**: unconfirmed uploads expire in hours, not years. Mixing them into `documents` would force per-object sentinel logic; a separate bucket makes cleanup a blanket prefix sweep. Virus scanning runs **here, before the complete-move**; scan-clean objects are *moved* (server-side copy + delete) into `documents` on `complete`, while infected objects are **retained in a `quarantine/` prefix** for investigation (§6). |
| `generated-reports` | Platform-generated report exports (PDF/XLSX) backing `export_history` / `report_generation_queue.final_report_url` | Different producer (the platform, not the customer), different retention class (regenerable artefacts), different access pattern (infrequent download bursts). Keeping them out of `documents` prevents derived bytes inflating the source-of-truth bucket's size metrics. |
| `ai-temp` | Worker scratch: OCR page images, intermediate extraction payloads, chunked pages for AI processing | Strict-TTL scratch space. Must never accumulate, must never be customer-visible, must be bulk-deletable without touching customer data. Failure isolation: a cleanup bug here loses scratch; a cleanup bug in `documents` loses the business. |
| `images` | Organisation/consultant logos (`organizations.logo_url`, `consultant_profiles.logo_url`), user avatars, feedback screenshots (`user_feedback.screenshot_url`) | Public-adjacent UX imagery that is *still private* (served via signed URLs) but carries a permissive content class (validated images only) and cosmetic sensitivity. Separating it keeps binary-mimetype sniffing rules and cache headers distinct from financial documents. |

Explicitly rejected: per-tenant buckets (bucket-count explosion, policy-management nightmare — the `{organization_id}` path prefix *is* the tenant boundary); a public assets bucket (marketing assets belong to the Next.js deployment, not tenant storage); a separate `attachments` bucket for `file_attachments` (chat attachments are stored in `documents` under a dedicated prefix — see §3 — because they are customer content with identical sensitivity and retention).

## 3. Naming Conventions

### 3.1 Object path grammar (per bucket)

| Bucket | Grammar | Example |
|---|---|---|
| `documents` | `{org_id}/docs/{yyyy}/{mm}/{customer_document_id}/{v{n}}_{sanitised_filename}` | `7c3…/docs/2025/06/9f2…/v1_invoice-march.pdf` |
| `documents` (chat attachments) | `{org_id}/attachments/{conversation_id}/{file_attachment_id}_{sanitised_filename}` | `7c3…/attachments/4aa…/81b…_meter-photo.jpg` |
| `temp-uploads` | `{org_id}/pending/{upload_session_id}/{sanitised_filename}` | `7c3…/pending/2dd…/scan001.pdf` |
| `generated-reports` | `{org_id}/reports/{yyyy}/{report_id}/v{version_number}/{export_id}.{ext}` | `7c3…/reports/2025/5b1…/v3/c40….pdf` |
| `ai-temp` | `{org_id}/scratch/{processing_queue_id}/{step}/{yyyy-mm-dd}/{uuid}.{ext}` | `7c3…/scratch/66e…/ocr/2025-06-11/a01….png` |
| `images` | `{org_id}/brand/{kind}_{entity_id}.{ext}` (logos); `avatars/{user_id}.{ext}`; `{org_id}/feedback/{feedback_id}.{ext}` | `7c3…/brand/logo_7c3….png` |

Grammar rules:

1. **Tenant prefix is mandatory and first.** Every RLS policy on `storage.objects` extracts segment 1 and tests it against the membership predicate — identical shape across buckets.
2. **Entity IDs in the path, not just the filename.** `{customer_document_id}` / `{export_id}` directories make objects self-describing, make per-entity erasure a prefix delete, and make collisions impossible by construction.
3. **Sanitised filename**: lower-cased, ASCII-folded, whitespace and non-`[a-z0-9._-]` collapsed to `-`, truncated to 80 chars, original preserved verbatim in the metadata row (`file_name`). The path is an identifier; the column is the display name.
4. **Date segments** (`yyyy/mm`) bound prefix-listing cost and give lifecycle sweeps a cheap time axis without listing the entire bucket.
5. **Extension from validated MIME**, not from the user-supplied name: the API layer's MIME/type validation (fixed decision) determines the stored extension.

### 3.2 Idempotency

| Scenario | Behaviour |
|---|---|
| Retried `init` | Same idempotency key → same `{upload_session_id}` and same signed upload URL returned; no duplicate object. |
| Retried `complete` | Metadata row finalised once (unique on `customer_document_id`); second call returns the existing row. |
| Same bytes re-uploaded | SHA-256 in `customer_documents.file_checksum` matches an existing row → application duplicate prompt fires (shipped RC1 behaviour). Hard UNIQUE enforcement stays **deferred** (HP-C2) until duplicate-resolution UX in v1.1 — storage does not block the write; detection is a table-level comparison. |
| Worker reprocessing | Workers address objects by `{customer_document_id}` prefix; reprocessing writes a new version object (§4), never mutates in place. |

## 4. Versioning — Tables, Not Object Overwrites

**Decision: document versions are modelled as new rows + new objects (`v{n}` path segment); object overwrites are forbidden everywhere.** Supabase Storage versioning features are not used.

| Alternative | Verdict | Reason |
|---|---|---|
| Object overwrite in place | **Rejected** | Destroys the audit trail the frozen schema is built around (`document_activity_log`, `processing_audit_trail`); breaks `file_checksum` duplicate detection semantics (path-stable, content-mutating); makes a half-overwritten object visible to an in-flight OCR worker. |
| Native storage versioning | **Rejected** | Moves version state out of the frozen tables into a platform feature the RC2 schema cannot see, query, RLS-guard, or reconcile with `report_versions(report_id, version_number)` (K5 unique-backed, frozen). |
| New row + new object (chosen) | **Approved** | Every version is an immutable object and a queryable row; `is_current`-style resolution already exists in the frozen `report_versions` unique path and the same pattern applies to document re-uploads (new `customer_documents` row superseding the old, old row retained for audit until retention). Immutability means no cache-invalidation problem anywhere downstream. |

Corollary: all buckets are write-once at the object level. The only storage mutations are **create**, **move** (temp-uploads → documents on `complete`, gated on a clean virus scan), **quarantine-retain** (infected objects moved to the `quarantine/` prefix for investigation), and **delete** (retention/erasure, and post-investigation quarantine purge). Update-in-place is not a storage operation CarbonTally performs.

## 5. Archive — Cold/Archive Posture

| Item | Posture |
|---|---|
| Storage tiering | **None at launch.** Freeze §7 defers storage tiering/lifecycle classes to v1.1+, trigger: storage cost trajectory at the first annual review. Single-tier (standard) storage now. |
| Archive bucket | **Not created.** An `archive` bucket today would be an empty artefact with a policy surface to maintain. When tiering activates (v1.1+), the mechanism is lifecycle transition of cold `documents` prefixes, evaluated against measured access frequency — not a speculative second bucket. |
| Logical archive | Organisations carry `is_active` / `archived_at` (RC1) — a *logical* archive: archived orgs' objects remain in place, access is cut by the active-org predicate, no data movement. Logical-first, physical-later. |
| Audit archive | The T2 audit-archive **table** is deferred to v1.1 with a trigger (frozen §7) — a database matter; it does not create storage objects. |
| Post-expiry retention | Objects past `retention_until` on the document class (already B-class per §7) are **deleted**, not archived — retention exists to shrink the estate, and a cold tier full of post-retention documents is a GDPR liability, not a saving. |

## 6. Temporary Uploads

| Aspect | Rule |
|---|---|
| Home | `temp-uploads` bucket only. |
| Expiry | Signed upload URLs expire in **≤ 15 minutes**; unconfirmed objects expire in **24 hours** (abandoned between init and complete). |
| Cleanup worker | Hourly sweeper (service role) lists `*/pending/*` older than 24 h and deletes object **and** orphaned upload-session row; emits a metric (`temp_uploads_swept`). Runs far inside any maintenance window. |
| Complete path | `complete` triggers the virus scan **in `temp-uploads`, before any move**; on a clean verdict the object is moved into `documents` (server-side copy under the §3.1 grammar, checksum re-verified against `file_checksum`, then source delete) and `document_processing_queue` is enqueued (`pending`). A move, not a re-upload — the customer's bytes cross the network once. |
| Failure mode | Virus-scan failure at `complete` → infected object is **retained in the `quarantine/` prefix** for investigation (it never touches `documents` and no download URL is ever issued for it), the session row is marked failed, and the uploader is notified; quarantined objects are purged only after investigation per the operations runbook. Validation failure (non-infection, e.g. checksum mismatch) → object deleted from `temp-uploads` immediately, session row marked failed. |

## 7. Report Exports — Retention and Regeneration

**Decision: regenerate over retain.** Exports are derived artefacts: the inputs (`emissions_logs`, factors, report definitions) are the durable record; the PDF/XLSX is a rendering.

| Aspect | Rule |
|---|---|
| Retention | Export objects in `generated-reports` live **90 days** from generation, then are deleted by the nightly lifecycle job. `export_history` rows persist (metadata is cheap; bytes are not). |
| Regeneration | Post-expiry download = a new `report_generation_queue` job (`I2c` partial index path, frozen) producing a new `export_id` object. Regeneration re-reads current data; for point-in-time fidelity the durable record is `report_versions(report_id, version_number)` (frozen K5 unique), so v3 of a report regenerates from v3's frozen inputs, not today's data. |
| Why not long retention | A 10 MB report × thousands of orgs × monthly cadence is the fastest-growing byte class in the platform, and every retained derived byte duplicates what the database already guarantees. 90 days covers the realistic "download again" window (board meetings, auditor requests in-season); outside it, regeneration is seconds of worker time. |
| Legal hold exception | A report under active audit/verification (SEC​R submission evidence) is pinned via metadata flag; the lifecycle job skips pinned prefixes. Pin count is monitored — pinning is the exception path, not the default. |

## 8. AI Temporary Files — Strict TTL

| Aspect | Rule |
|---|---|
| Contents | OCR page rasterisations, chunked document payloads sent to extraction models, intermediate per-page extraction JSON staged as objects when too large for queue payloads. |
| TTL | **72 hours hard cap**, target **24 hours**: the extraction worker deletes its own scratch prefix on successful completion (delete-before-exit), and the hourly sweeper force-deletes anything in `ai-temp` older than 72 h regardless of job state. |
| Why strict | Scratch contains the same PII/financial content as the source document but with none of its audit scaffolding; every hour it persists is uncontrolled PII exposure. It is also pure cost — it is never re-read after the job completes. |
| Access | Service role only. No signed URL is ever minted for an `ai-temp` object; no client code path references the bucket. RLS on `storage.objects` here denies `authenticated` outright (not tenant-scoped — denied). |
| Failure handling | On job failure, scratch is retained until the 72 h sweep for debugging, then deleted — debugging never extends TTL. |

## 9. Generated PDFs

Covers all platform-rendered PDFs: report exports (§7) and document-derived PDFs (e.g., normalised renders of uploaded images for reviewer display).

| Class | Bucket & path | Retention | Access |
|---|---|---|---|
| Report export PDFs | `generated-reports/{org}/reports/…` | 90 days, regenerable (§7) | Signed URL (≤ 15 min) to org members with report permission; download logged to `document_activity_log`. |
| Review-render PDFs (normalised for manual review) | `documents/{org}/docs/…/derived/` alongside the source document | Life-of-document (they are part of the evidentiary bundle) | Same signed-URL path as source documents; reviewer and customer views both authorise against the owning `customer_document_id`. |

Generated PDFs are immutable once written (§4): a re-render is a new object, never an overwrite.

## 10. Images

| Class | Path | Validation | Retention |
|---|---|---|---|
| Org / consultant logos | `images/{org_id}/brand/…` | Images-only MIME allowlist, server-side re-encode (strips payloads/metadata), ≤ 2 MB | Until replaced; replacement writes a new object and the old is deleted in the same flow. |
| User avatars | `images/avatars/{user_id}.{ext}` | As above, ≤ 1 MB | Life-of-account; deleted by the erasure procedure (§12). |
| Feedback screenshots | `images/{org_id}/feedback/{feedback_id}.{ext}` | As above, ≤ 5 MB | 12 months, aligned to the `user_feedback` review cycle, then swept. |
| Document-embedded images | Part of `documents` (page renders are `ai-temp` or derived PDFs, §8/§9) | — | — |

Despite being "just images", the bucket is **private** (fixed posture): logos and avatars are served through the same signed-URL endpoint as everything else, with a longer-lived edge cache keyed on the signed response at the CDN/Next.js layer where justified. No public bucket, no exceptions.

## 11. Retention Rules (per bucket)

| Bucket | Object retention | Cleanup owner | GDPR / erasure interaction |
|---|---|---|---|
| `documents` | Life-of-document: until customer deletion or org offboarding + 30-day grace; `retention_until` on the document class (B-class, already scheduled) drives sweeps | Nightly lifecycle job (service role); deletions logged to `document_activity_log` | Erasure deletes by `{org_id}/docs/…` and `…/attachments/…` prefixes tied to the subject's rows (§12). Source documents may be legitimately retained for financial-record obligations where they are the org's records, not the data subject's — assessed per DSAR. |
| `temp-uploads` | 24 h | Hourly sweeper | Subject to prefix sweep in erasure (rarely holds personal data beyond minutes). |
| `generated-reports` | 90 days (pinned exports excepted) | Nightly lifecycle job | Exports may embed personal data → swept in erasure regardless of the 90-day clock; regeneration post-erasure renders anonymised data, so no stale PII can reappear. |
| `ai-temp` | 24 h target / 72 h hard | Worker self-delete + hourly sweeper | Always deleted within 72 h; erasure additionally sweeps the subject's org prefix immediately. |
| `images` | Logos/avatars: until replaced/account end. Screenshots: 12 months | Replacement flow + nightly sweep | Avatars deleted at erasure (they are the user's own PII); org logos survive (organisation data, not personal); screenshots swept if they identify the subject. |

## 12. GDPR Erasure — Storage Procedure

`anonymise_user()` (RC2-041, frozen, launch-gated) is **anonymise-in-place in the database and deliberately does not touch storage objects**. Storage therefore needs its own erasure leg, executed as part of the same runbook invocation. Specification:

| Step | Action | Owner |
|---|---|---|
| 1 | Run `anonymise_user()` per the approved runbook (hashes email, scrubs profile PII, preserves `users.id` and FKs). | Service role, guarded invocation |
| 2 | **Avatar & personal imagery**: delete `images/avatars/{user_id}.*` — unambiguous personal data. | Storage erasure worker (service role) |
| 3 | **Org-scoped prefix sweep where the subject is the sole/last member** or the org is closing: delete `{org_id}/…` across `documents`, `temp-uploads`, `generated-reports`, `ai-temp` after the 30-day offboarding grace. | Storage erasure worker |
| 4 | **Named-person content in shared org data** (chat attachments the subject uploaded, documents they uploaded): the frozen anonymise-in-place model keeps rows and FKs intact; uploaded documents are *organisation* records (financial-record retention), not erased on an individual DSAR unless the DSAR scope lawfully extends. Attachments the subject authored in support conversations are deleted on assessment; `file_attachments` rows remain, pointing at a tombstone marker in metadata (row preserved for FK/audit integrity — consistent with hard delete being structurally impossible across ~40 FKs). | DSAR assessor + worker |
| 5 | **Sweep residuals**: `temp-uploads` and `ai-temp` prefixes for the org (≤ 72 h old content may still name the subject). | Storage erasure worker |
| 6 | **Verification & evidence**: post-run listing confirms zero objects under the erased prefixes; the deletion manifest (bucket, prefix, object count, timestamp) is written to the audit trail. The one-month DSAR clock and the Gate 5 rehearsal cover this storage leg end-to-end exactly as they cover the database leg. | Compliance |

Hard guarantees: no erasure path ever deletes another tenant's object (prefixes are tenant-prefixed by construction); no signed URL survives erasure meaningfully (≤ 15-minute expiry); regeneration can never resurrect erased PII because it renders from anonymised rows.

## 13. Bucket-Policy Posture

Access is exclusively via short-expiry signed URLs minted server-side after an authorisation check. "Never public" is absolute. RLS on `storage.objects` is the second line, not the first.

| Bucket | Customer (owner/admin/member) | Customer (viewer) | Consultant (via client access) | Staff reviewer | Service/worker | Anonymous |
|---|---|---|---|---|---|---|
| `documents` | Read/write own-org via signed URL; upload via init/complete | Read own-org via signed URL (no upload) | Read client-org via signed URL where `client_access` covers the org | Read via signed URL on assigned review items only | Full (service role, RLS-bypass) — scan/OCR/move/lifecycle | **Denied** |
| `temp-uploads` | Write own-org (signed upload URL, ≤ 15 min); no read path | Denied | Denied | Denied | Full — move-on-complete, sweep | **Denied** |
| `generated-reports` | Read own-org via signed URL | Read own-org via signed URL | Read client-org via signed URL | Read via signed URL (support context, logged) | Full — generate, pin, sweep | **Denied** |
| `ai-temp` | Denied (no client surface) | Denied | Denied | Denied (debug via service tooling, not signed URLs) | Full — scratch lifecycle | **Denied** |
| `images` | Read via signed URL; write own-org logos/own avatar | Read via signed URL | Read client-org via signed URL | Read via signed URL | Full — re-encode pipeline, sweep | **Denied** |

Policy notes: (a) every signed-URL mint is authorised against membership/role server-side *before* calling storage — storage RLS exists to catch authorisation bugs, not to implement them; (b) `authenticated` access on `ai-temp` is outright denied rather than tenant-scoped; (c) staff/consultant access paths are logged (`document_activity_log` / `message_activity_log`) so storage reads carry the same audit discipline as table reads; (d) bucket policies are verified in Gate 4 alongside table policies — storage is not a side-door around the RLS matrix.

---

*Consistency statement: no new indexes, no partitioning, no schema change, and no platform feature outside the RC2 freeze is proposed above. All table references use post-RC1 names. Versioning and regeneration strategies rely only on frozen objects (`file_checksum`, `report_versions` K5 unique, `retention_until` B-class, `anonymise_user` runbook).*
