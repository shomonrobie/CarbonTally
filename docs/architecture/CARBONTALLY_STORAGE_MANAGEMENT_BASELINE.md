# CarbonTally — Storage Management Baseline

**Document ID:** CT-STORAGE-MANAGEMENT-BASELINE-20260930-001
**Repository:** `ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **HEAD:** `cabdca8380415e73a25cf23eb393d0b15c0af391` (2026-09-29)
**Date:** 2026-09-30
**Nature:** **read-only architectural baseline audit.** No source, test, migration, schema, configuration, Storage, Supabase or data change was made in producing this document. The only artefact written is this file.

**Evidence label vocabulary used throughout**

| Label | Meaning |
|---|---|
| `LIVE — READ-ONLY VERIFIED` | Observed directly, in this session, through a read-only probe (SELECT-only SQL / filesystem listing) against the named environment. |
| `CODE-TRACED` | Derived by reading repository source at the cited file:line. Not executed. |
| `DOCUMENTED INTENT` | Stated by a product decision, migration header or operations document. |
| `UNVERIFIED` | Not established either way by this audit; explicitly left open. |

**Status vocabulary used throughout:** `EXISTS` · `PARTIAL` · `MISSING` · `UNKNOWN` · `CONFLICTING` · `UNVERIFIED`.

---

## 1. Purpose, mandate and scope

### 1.1 Purpose

Establish a factual, evidence-labelled baseline of how CarbonTally **stores, serves, limits, authorizes and removes documents and report artefacts today**, so that later work can be measured against a statement of the current state rather than against intent, memory or a prior audit.

### 1.2 Mandate (what this document does)

* Describes the storage subsystem **as it exists** at the recorded HEAD, with file:line citations.
* Reports **documentation-vs-implementation conflicts** as findings. It does **not** reconcile, resolve, redesign or propose fixes.
* Labels every non-trivial claim with an evidence label and a status.
* Ends with a numbered final report (§19) and stops.

### 1.3 Explicit exclusions

* No redesign of the consultant, Processing-Entity, staff or customer actor models. Actor definitions are **cited** from `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`, not re-invented.
* No change to code, tests, migrations, schema, storage buckets, environment files or data.
* No deployment, migration application, bucket creation, object upload, object deletion or JWT issuance.
* No assertion about environments that were not probed.

### 1.4 Scope boundary

In scope: Supabase Storage buckets (`documents`, `report-artifacts`), the object-path model, every application ingress that writes objects, every application surface that reads/signs objects, upload limits and their configuration, retention/delete behaviour as it concerns stored objects, storage RLS, storage-related migrations, and the live state of the two databases reachable from this checkout.

Out of scope: report generation logic, disclosure policy internals, email delivery, billing, and any non-storage subsystem except where a storage path crosses it.

---

## 2. Method, evidence labelling and safety controls

### 2.1 Read-only controls applied

| Control | Implementation |
|---|---|
| No repository mutation | Only reads (`read_files`, `sed -n`, `grep`, `git rev-parse/status/log`, `ls`). `git status --porcelain` at the end of the session was identical to its state at the start. |
| No database mutation | Only `SELECT` statements were issued (`supabase_migrations.schema_migrations`, `storage.buckets`, `storage.objects`, `public.organization_files`, `pg_policies`, `information_schema`-style catalog reads). No `INSERT`/`UPDATE`/`DELETE`/DDL was issued against any database. |
| No storage mutation | No upload, no `remove`, no `create_signed_url`, no bucket creation. Storage was inspected **only** through SQL catalog/row reads. |
| No credential exposure | Credentials were read from `backend/.env` into the shell for the probe and were never printed; probe output was filtered to state facts (bucket name, `public`, `file_size_limit`, object counts, policy metadata). |
| No deployment | Nothing committed, pushed, migrated, restarted or deployed. |
| Shell hygiene | Probe output was redirected to `/tmp/ct_*.txt` and read back from disk, because terminal integration in this session was intermittent. |

### 2.2 Environments probed

| Ref | What it is | How reached | Provenance statement |
|---|---|---|---|
| **ENV-LOCAL** | Local disposable PostgreSQL/Supabase clone, database `ct_local_93d5cdd` | `DATABASE_URL` in `backend/.env` → `127.0.0.1:54426` (container-tunnelled) | `LIVE — READ-ONLY VERIFIED` as *a* database named `ct_local_93d5cdd`. |
| **ENV-LIVE** | Remote database reachable from this checkout | `SUPABASE_LIVE_POSTGRES_DATABASE_URL` in `backend/.env` → IPv6 pooler session `2a05:d01c:874:6b01:6fcd:e130:fb9:3b90/128`, user `postgres` | `LIVE — READ-ONLY VERIFIED` as *the database that the configured live DSN points at*. Its identity as the CarbonTally **production** project is **`UNVERIFIED`** — this audit did not verify project ref, billing, or provider console identity. |

State facts observed in each environment are in §13. Where a fact comes from one environment only, the environment ref is named.

### 2.3 Structural conventions

Section structure follows the read-only baseline/audit convention already used in this repository (`docs/architecture/CT-P8-PO-DECISION-INVENTORY-20260922.md`, `docs/architecture/CT-PO-CT-READINESS-01/02`): purpose → method → authority → inventory → findings-by-area → conformance status → final report.

---

## 3. Authority hierarchy and terminology

### 3.1 Authority order (highest first)

| # | Layer | Storage-relevant instances |
|---|---|---|
| 1 | **Product-owner decisions** | `D32` (private document storage + org-scoped storage RLS), `CT-FINAL-01` (ratified upload limits 10 MB / 50 files / 500 MB), `B4-D5/D6/D7` (mandatory frozen report artefact in the private `report-artifacts` bucket), `P8-D17-D32-STORAGE-POLICY-RESOLUTION-001` (Route C — no provider-role privilege escalation), `D-11` (operational bucket provisioning, no migration), `PX-7` (telemetry retention 90 days; aggregates indefinite), `CL-42` (viewer read-only), `D15` (active consultant-client grant required), `D19/P6-1C` (client-status lifecycle) |
| 2 | **Architecture / operations documents** | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`; `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (§3 actor table A1–A14 — the canonical actor definitions cited in §16); `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md`; `docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md` |
| 3 | **Migrations and operator scripts** | `supabase/migrations/20260823000000_d32_private_documents_storage.sql`; `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql`; `e2e/environment/scripts/d32_storage_operator.sql`; `e2e/environment/scripts/verify_d32_policy_semantics.sql` |
| 4 | **Implementation code** | `backend/services/storage.py`; `backend/utils/upload_limits.py`; `backend/services/retention.py`; `backend/services/report_artefact_storage.py`; `backend/domain/report_artefact.py`; `backend/api/v3_documents.py`; `backend/api/v3_consultants.py`; `backend/api/v3_operations.py`; `backend/api/v3_pe.py`; `backend/api/v3_evidence.py`; `backend/api/v3_emissions.py`; `backend/api/v3_automatic_processing.py`; `backend/api/v3_disclosure.py`; `backend/routes/upload.py`; `backend/routes/organizations/files.py`; `backend/routes/reports.py` |
| 5 | **This baseline** | Descriptive only. It creates no requirement and resolves no conflict. |

### 3.2 Terminology (as used in this document)

| Term | Meaning here | Source of record |
|---|---|---|
| **Bucket** | A Supabase Storage bucket (`storage.buckets` row). Two exist in the design: `documents`, `report-artifacts`. | `services/storage.py:26`, `domain/report_artefact.py:24` |
| **Object key / path** | Bucket-relative object name, e.g. `uploads/<org>/2026/09/30/<hex>_<file>`. | `services/storage.py:35-54` |
| **Canonical path** | The bare key persisted on `organization_files.path` (never a URL). `path_from_url()` converts a legacy public URL, a signed URL or a bare path into the canonical path. | `services/storage.py:35-54` |
| **Signed URL** | Short-lived, server-issued URL from `create_signed_url`; expiry is mandatory (signed URLs always expire). | `services/storage.py:9-10, 29, 57-71` |
| **Service-role client** | `infra.supabase.get_service_client()` — bypasses storage RLS; used for every application object read/write/sign. | `services/storage.py:14-16, 23, 64` |
| **Storage RLS** | Row-level policies on the provider-owned `storage.objects` table, scoped to `authenticated` only. | §11 |
| **Ratified cap** | Hard ceiling configuration may never exceed (10 MB / 50 / 500 MB). | `utils/upload_limits.py:39-48` |
| **Effective default** | Value applied when no administrator has configured the policy (6 MB / 50 / 500 MB). | `utils/upload_limits.py:53-55` |
| **Report artefact** | The frozen PDF of a finalised report version in the private `report-artifacts` bucket, key `{organization_id}/{report_id}/{report_version_id}.pdf`. | `domain/report_artefact.py:24, 103-116` |
| **Actor A1…A14** | Canonical actor identifiers in `CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §3. | cited, not redefined |

---

## 4. Storage architecture overview

### 4.1 Provider and layering

CarbonTally uses **Supabase Storage** as its only object store. Three layers are involved:

1. **Platform layer** — the provider-managed `storage` schema (`storage.buckets`, `storage.objects`, `storage.foldername(name)`). `storage.objects` is owned by the provider role `supabase_storage_admin`; CarbonTally's migration role must **not** be granted ownership or membership (PO decision — Route C): `20260823000000_d32_private_documents_storage.sql` header and `e2e/environment/scripts/d32_storage_operator.sql` header.
2. **Application layer** — the FastAPI backend. Every object write, read and signed-URL issuance runs through the **service-role** client (RLS-bypassing); authorization is enforced **before** the storage call, in the API layer (`services/storage.py:14-16`).
3. **Record layer** — `public.organization_files` holds `path`, `bucket`, `size_bytes`, `mime_type`, uploader/activity fields; `report_version_artifacts` holds frozen-artefact metadata (`storage_bucket`, `object_key`, `content_sha256`, `byte_size`, `content_type`).

### 4.2 Bucket inventory

| Bucket | Constant | Purpose | Privacy (documented end state) | Provisioning mechanism | Live state (both probed envs) |
|---|---|---|---|---|---|
| `documents` | `DOCUMENTS_BUCKET` — `services/storage.py:26` | Customer-uploaded source documents (the only user-upload ingress bucket) | **private** (`public = FALSE`) — D32 | Bucket created by environment provisioning; the D32 migration sets/asserts private; RLS policies created by the provider-context operator step | **present; `public = false`** (§13) |
| `report-artifacts` | `ARTEFACT_BUCKET` — `domain/report_artefact.py:24` | Internally generated frozen report PDFs (not a user upload ingress) | **private**; no public URL form exists in the adapter (`services/report_artefact_storage.py:4-8`) | **Operational** provisioning only — no migration creates it and no `create_bucket` call exists in `backend/` (`docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md`, §"Current state" and §2) | **absent** from `storage.buckets` in **both** probed environments (§13) → `MISSING` |

### 4.3 Access model in one line

* **Application path (primary):** caller → API authentication/authorization → *service-role* storage operation (upload / download / `create_signed_url`).
* **Direct path (bypass):** caller holding a Supabase user JWT → Storage/PostgREST API → `storage.objects` RLS. Only the four approved `d32_documents_*` policies exist (§11); they authorize `authenticated` only, and only inside the `uploads/<org_id>/…` prefix.

### 4.4 Where storage state actually lives

| State | Store | Written by |
|---|---|---|
| Object bytes | Supabase Storage bucket | Backend via service-role client |
| Object identity (`path`, `bucket`) | `organization_files` | `create_document_and_enqueue` (`api/v3_documents.py`), legacy routes |
| Signed URL | Never persisted as durable state; issued per view (the legacy V3 upload path also stores a *fresh signed URL* inside `organization_files.metadata.file_url`, which therefore expires) | `services/storage.py:74-80`, `api/v3_documents.py` |
| Upload limits | `system_settings` row keyed `upload_policy` | `data/settings.py:417-484`; Admin Panel → Upload Policy (`api/v3_settings.py`, `GET`/`PUT /upload-policy`, `require_admin`) |
| Retention policy | `system_settings` (`platform_retention`) | surfaced by `/api/v3/settings/retention`; enforced by `services/retention.py` |

---

## 5. Storage component and call-site inventory

### 5.1 Components (`CODE-TRACED`)

| Component | File | Responsibility | Status |
|---|---|---|---|
| Document storage helpers | `backend/services/storage.py` (80 lines) | `DOCUMENTS_BUCKET` constant; `SIGNED_URL_TTL_SECONDS = 3600`; `path_from_url()` (public URL / signed URL / bare path → canonical path); `storage_signed_url()` (service-role `create_signed_url`, returns `""` on any failure); `signed_item()` (dataclass copy with freshly signed `file_url`) | `EXISTS` |
| Report-artefact adapter | `backend/services/report_artefact_storage.py` | Private-bucket upload (`upsert=false`), signed URL (`TTL 300`), `exists()` via `list`, `bucket_exists()` preflight via `list_buckets`, in-memory double, process-wide accessor + setter | `EXISTS` |
| Report-artefact invariants | `backend/domain/report_artefact.py` | `ARTEFACT_BUCKET='report-artifacts'`, `ARTEFACT_CONTENT_TYPE='application/pdf'`, derived `object_key_for()`, SHA-256 hex validation, PDF magic check | `EXISTS` |
| Canonical upload policy | `backend/utils/upload_limits.py` (321 lines) | `PLATFORM_MAX_*` caps; `DEFAULT_*` effective defaults; `resolve_policy()`; `effective_*`; `enforce_single_file()` (413); `enforce_batch()` (400 count / 413 size); machine-detectable codes `UPLOAD_FILE_TOO_LARGE`, `UPLOAD_TOO_MANY_FILES`, `UPLOAD_BATCH_TOO_LARGE`, `UPLOAD_SIZE_UNKNOWN`; `validate_upload_policy()`; `human_summary()` | `EXISTS` |
| Persisted policy store | `backend/data/settings.py:42, 60, 417-484` | `_UPLOAD_POLICY_KEY = "upload_policy"`; `get_upload_policy()`; `update_upload_policy()` (validated before write) | `EXISTS` |
| Admin policy surface | `backend/api/v3_settings.py` (`GET`/`PUT /upload-policy`) | `require_admin()`; returns `configured` + `effective` + documented defaults + ratified caps; `PUT` refuses out-of-range values with 422 | `EXISTS` |
| Retention enforcement | `backend/services/retention.py` (148 lines) | Eligible domains `document_retention_days`, `operational_telemetry_retention_days`; soft-delete (`deleted_at`) only; explicit never-purge list; dry-run by default | `EXISTS` (does not touch objects — §9) |
| Storage RLS operator step | `e2e/environment/scripts/d32_storage_operator.sql` (9,257 bytes) | Provider-context creation of exactly four `d32_documents_*` policies; idempotent; fail-closed; refuses `anon`/`public` policies; run by `supabase_admin` between migration 26 and migration 27 | `EXISTS` |
| Storage RLS semantic verifier | `e2e/environment/scripts/verify_d32_policy_semantics.sql` (11,329 bytes) | Behavioural verification of the policy predicate | `EXISTS` |
| Storage security tests | `backend/tests/unit/api/test_storage_security.py` (3,118 bytes) | `path_from_url` parsing and private-documents hardening | `EXISTS` |
| Upload-limit tests | `backend/tests/unit/api/test_ct_final_01_upload_limits.py` (24,836 bytes) | CT-FINAL-01 canonical-limit behaviour across ingresses | `EXISTS` |

### 5.2 `storage.from_(...)` call-site inventory (`CODE-TRACED`)

| Class | Call site | Operation |
|---|---|---|
| **Writer** | `api/v3_documents.py:304` | `.upload(path, content, file_options={"content-type": mime_type})` — the canonical V3 ingress |
| **Writer** | `routes/organizations/files.py:586` | `.upload(...)` — `POST /api/organizations/{org_id}/files/upload` |
| **Writer** | `routes/organizations/files.py:869` | `.upload(...)` — `POST /api/organizations/{org_id}/files/bulk-upload` |
| **Writer** | `routes/upload.py:488` | `.upload(...)` — legacy `POST /api/repair-pdf`, bucket literal `'documents'`, key `repaired_pdfs/...` |
| **Writer** | `routes/upload.py:709` | `.upload(...)` — legacy `POST /api/upload`, bucket literal `'documents'` |
| **Writer** | `services/report_artefact_storage.py:54` | `.upload(path=object_key, upsert=false)` — frozen artefact |
| **Reader** | `api/v3_documents.py:552` | `.download(path_from_url(doc.path))` — OCR re-run |
| **Reader** | `routes/organizations/files.py:340` | `.download(path)` — streaming download |
| **Reader** | `services/automatic_processing.py:581` | `.download(path)` — pipeline ingest (bounded by `_MAX_INGEST_BYTES`) |
| **Remover** | `routes/organizations/files.py:474` | `.remove([path])` — permanent delete |
| **Signer** | `services/storage.py:64` | `create_signed_url(path, 3600)` |
| **Signer** | `routes/organizations/files.py:150` | `create_signed_url(path, expires_in=3600)` |
| **Signer** | `services/report_artefact_storage.py:61` | `create_signed_url(object_key, 300)` |
| **Probe** | `services/report_artefact_storage.py:69, 85` | `.list(path=...)` for `exists()`; `list_buckets()` for `bucket_exists()` |
| **Legacy public URL** | `routes/upload.py:494, 718`; `routes/organizations/files.py:594` | `.get_public_url(path)` — residual public-URL construction on a private bucket (§17 F-4) |

---

## 6. Canonical object-path model

### 6.1 Producers and key templates (`CODE-TRACED`, except where marked)

| # | Producer | Key template | Citation |
|---|---|---|---|
| P1 | V3 canonical pipeline — `POST /api/v3/uploads` (org member) **and** consultant client upload; both call `create_document_and_enqueue()` | `uploads/{organization_id}/{YYYY/MM/DD}/{uuid4().hex}_{filename}` | `api/v3_documents.py:288` (day computed `datetime.utcnow().strftime("%Y/%m/%d")`) |
| P2 | Legacy `POST /api/upload` | `uploads/{organization_id}/{YYYY/MM/DD}/{YYYYMMDD_HHMMSS}_{filename}` | `routes/upload.py:703` |
| P3 | `POST /api/organizations/{org_id}/files/upload` and `…/bulk-upload` | `organizations/{org_id}/{YYYY-MM}/{slug}_{timestamp}.{ext}` | `routes/organizations/files.py:110-129` (`get_organization_upload_path`) |
| P4 | Legacy `POST /api/repair-pdf` | `repaired_pdfs/{repaired_filename}` | `routes/upload.py:486` |
| P5 | Report finalisation (frozen artefact) | `{organization_id}/{report_id}/{report_version_id}.pdf` — **derived, never caller-supplied** | `domain/report_artefact.py:24, 103-116`; enforced in DB by `CHECK (object_key = organization_id || '/' || report_id || '/' || report_version_id || '.pdf')` (`LIVE — READ-ONLY VERIFIED`, ENV-LIVE) |
| P6 | Legacy/ops-written keys observed in the live bucket but **not** produced by any current application code path traced in this audit: `batches/<org_id>/…`, `manual_review/<org_id or literal>/…` | — | `LIVE — READ-ONLY VERIFIED`, ENV-LIVE (`storage.objects` prefix counts) |

### 6.2 Path parsing and normalization

`path_from_url()` (`services/storage.py:35-54`) accepts three input shapes and always returns a bare key:

1. a bare key (anything not starting with `http`) → returned unchanged;
2. a legacy public URL containing `/object/public/documents/` → text after the marker;
3. a signed URL containing `/object/sign/documents/` → text after the marker, `?token=…` stripped;
4. last-resort fallback: text after `/documents/`, query stripped.

This is what allows rows written before D32 (which stored public URLs) to keep resolving after the bucket became private (`CODE-TRACED`; unit coverage in `tests/unit/api/test_storage_security.py`).

### 6.3 Prefix distribution actually present in the live bucket

`LIVE — READ-ONLY VERIFIED` (ENV-LIVE, `storage.objects`, 58 rows total):

| First path segment | Objects | Covered by the D32 storage-RLS predicate? |
|---|---|---|
| `manual_review/…` | 38 | **No** — predicate requires `foldername(name)[1] = 'uploads'` |
| `uploads/…` | 14 | **Yes** |
| `batches/…` | 6 | **No** |
| `organizations/…` (P3), `repaired_pdfs/…` (P4) | 0 observed | **No** (would be outside if written) |

**Finding (recorded, not reconciled):** the object-path model spans at least five prefixes (P1–P6), while the storage-RLS predicate authorizes **only** the `uploads/` prefix. 44 of the 58 live objects (76 %) sit outside the policy's authorized prefix. Because every application read/write goes through the service-role client (which bypasses RLS), this does not block the application's own paths today; it means the direct/user-JWT path authorizes only a subset of the objects that exist. See §17 F-1.

---

## 7. Upload ingress paths (object writers)

### 7.1 Ingress inventory (`CODE-TRACED`)

| # | Endpoint | Guard / authorization | Limit enforcement | Storage write | Result record |
|---|---|---|---|---|---|
| I1 | `POST /api/v3/uploads` (form: `organization_id`, `data_type`, `file`) | `require_org_member()`; `ensure_org_access(current_user, organization_id)`; **explicit viewer denial** (403 "Viewers are read-only and cannot upload documents", CL-42) — *the denial precedes any storage object or DB row* | `resolve_policy()` once per request, then `enforce_single_file()` inside `create_document_and_enqueue()` **before** the upload call | `client.storage.from_(DOCUMENTS_BUCKET).upload(...)` | `repos.files.create(...)` with `path`, `bucket="documents"`, and `metadata={"data_type", "file_url": <fresh signed URL>}`; then durable enqueue into the manual-extraction pipeline (upload failures do not fail the upload) |
| I2 | `POST /api/organizations/{org_id}/files/upload` | `require_org_member()`; explicit `str(org_id) != str(current_user.organization_id)` → 403 | `resolve_policy()` + `enforce_single_file()` (413 with the canonical code) | `supabase.storage.from_('documents').upload(...)` | insert into `organization_files` |
| I3 | `POST /api/organizations/{org_id}/files/bulk-upload` | `require_org_member()`; org taken from `current_user.organization_id` | `enforce_batch()` (count → 400, per-file/batch → 413) **before** any upload; per-file re-check inside the loop | `.upload(...)` per file | insert per file; failures collected in `failed[]` |
| I4 | `POST /api/upload` (legacy) | `require_org_member()`; `enforce_org_body_scope(organization_id, current_user)` | `resolve_policy()` + `enforce_single_file()` | `.upload(...)`, bucket literal `'documents'` | insert into `organization_files` |
| I5 | `POST /api/upload-csv`, `POST /api/upload-pdf` (legacy) | `require_org_member()` (via route guard) | `validate_file_upload(...)` → `enforce_single_file()` | none (these parse pandas frames; no object write traced) | n/a |
| I6 | `POST /api/repair-pdf` (legacy) | `require_org_member()` | `resolve_policy()` + `enforce_single_file()` | `.upload(...)` key `repaired_pdfs/...` | response returns a public URL (see F-4) |
| I7 | `POST /api/v3/consultants/clients/{client_id}/documents` | `require_consultant()`; `_authorized_client_org(...)` (active `consultant_clients` grant, firm-ownership; 404 cross-firm / 403 not active); `ensure_consultant_permission(context, "upload_documents")` → 403 when `can_upload_documents` is false | `resolve_policy()` then `create_document_and_enqueue(..., configured_limit_mb=…)` | **same** `create_document_and_enqueue()` write as I1 (single shared writer) | same record shape as I1 |
| I8 | `POST /api/reports/admin/import-defra-factors` (admin factor import) | `require_admin()` | `resolve_policy()` + `enforce_single_file()` | none (writes factor rows, not objects) | n/a |
| I9 | Report finalisation (frozen artefact) | disclosure/finalisation authorization (`_authorize_read` / finalisation service) | not an upload-limit ingress | `SupabaseReportArtefactStorage.upload(..., upsert=False)` | `report_version_artifacts` row |

`CODE-TRACED` generalisations:

* **Every** traced upload ingress resolves the canonical policy (`utils.upload_limits.resolve_policy`) — no route carries its own size constants; the legacy `get_system_settings()` in `routes/upload.py:51-86` explicitly documents that the retired 50 MB / 20 / 200 MB values are no longer read for limits.
* **Two ingresses share one writer** (I1, I7 → `create_document_and_enqueue`), so the consultant path cannot drift from the customer path in path shape, limit enforcement or pipeline enqueue.
* Rejections happen **before** any storage object or database row is created (`utils/upload_limits.py:21-24`).

### 7.2 Content-type handling

`create_document_and_enqueue()` rewrites generic browser MIME types to renderable ones before upload (PDF → `application/pdf`, images → `image/*`, spreadsheets → `text/csv`/xlsx) so the viewer renders inline instead of forcing a download; unknown types fall back to the supplied value (`api/v3_documents.py`, `_renderable_content_type`). `CODE-TRACED`.

### 7.3 OCR / extraction after write

Upload triggers best-effort text/OCR extraction (`_extract_document_text`, `api/v3_documents.py:41-88`), with a 200,000-character cap on the JSONB copy (`_OCR_TEXT_CAP`), a 20-character minimum to count as "text" (`_OCR_MIN_TEXT`), and an explicit guarantee that OCR failure never fails an upload. Re-runnable via `POST /api/v3/uploads/{file_id}/ocr`, which re-downloads the object (`api/v3_documents.py:552`) and never overwrites human-entered data. `CODE-TRACED`.

---

## 8. Read, view and signed-URL paths (object readers / signers)

### 8.1 Signing surfaces (`CODE-TRACED`)

| # | Surface | Guard | Signing call | TTL | Notes |
|---|---|---|---|---|---|
| S1 | `GET /api/v3/documents/{file_id}/signed-url` | `require_org_member()` + `ensure_org_access(current_user, doc.organization_id)` | `storage_signed_url(path_from_url(doc.path))` | 3600 s | Returns `{"url", "expires_in_seconds": 3600}`; 404 `"document not found"` / `"document object not found in storage"`. Documented as *"the only way viewers obtain access"* (D32) — `api/v3_documents.py:588-614` |
| S2 | `GET /api/v3/documents/{file_id}` | `require_org_member()` + `ensure_org_access` | — | — | Returns the record only (`api/v3_documents.py:585-591`) |
| S3 | Ops entity batch items / item workspace | `require_staff()` + `_entity_workspace_guard()` + `ensure_entity_batch_access()` | `signed_item(i)` per item | 3600 s (via `services/storage.py`) | **Persisted storage paths are never returned to entity staff**; URLs are view-only (PE no-download boundary) — `api/v3_operations.py` (`entity_extraction_batch_items`, `entity_extraction_item_workspace`) |
| S4 | PE workspace items | PE assignment guard (`_ensure_assigned_item`) | `_ops.signed_item(i)` | 3600 s | `api/v3_pe.py:547` |
| S5 | Emission ↔ document reverse lookup | org-scoped (`ensure_org_access`) | `storage_signed_url(path_from_url(file_row.path))` | 3600 s | `api/v3_emissions.py:405-463`; also `api/v3_documents.py:617-667` returns emissions for a document and writes an append-only `evidence.reverse_lookup` audit entry (ids only) |
| S6 | Evidence line-item provenance | evidence surface guard | `storage_signed_url(path_from_url(file_row.path))` | 3600 s | `api/v3_evidence.py:156-158` |
| S7 | Legacy `GET /api/organizations/{org_id}/files/{file_id}/url` | `require_org_member()`; row filtered by `organization_id` + `is_active` | `get_file_download_url()` → `create_signed_url(path, expires_in=3600)` | **helper hard-codes 3600** | The handler accepts an `expires_in` query parameter (60–86400, default 3600) and echoes it in the response, but the helper always signs for 3600 — see §17 F-5 (`routes/organizations/files.py:146-160`, `:371-425`) |
| S8 | Legacy `GET /api/organizations/{org_id}/files/{file_id}/download` | `require_org_member()`; row filtered by `organization_id` + `is_active` | none (byte stream) | — | `.download(path)` → `StreamingResponse`; updates `last_accessed` / `access_count` (`routes/organizations/files.py:290-366`) |
| S9 | `GET /api/v3/reports/{report_id}/frozen-artefact` | `require_org_member()` + `_authorize_read(...)` | none | — | **Never returns a URL** — metadata only (bucket, derived key, SHA-256, size) (`api/v3_disclosure.py:645-672`) |
| S10 | `POST /api/v3/reports/{report_id}/frozen-artefact/signed-url` | `require_org_member()` + `_authorize_read(...)` (PE staff and CarbonTally staff are denied) | `DisclosureFinalisationService.artefact_download_url(..., storage=…)` → adapter `create_signed_url` | **300 s** | `api/v3_disclosure.py:675-700`; TTL mandated by `services/report_artefact_storage.py:22-24` |

### 8.2 Properties evidenced across all signing surfaces

* **Authorization precedes signing** at every traced surface; the signing client is always the service-role client (`services/storage.py:14-16, 57-71`).
* **Failure is non-fatal and non-leaky**: `storage_signed_url()` returns `""` on any exception and callers turn that into 404/absent URL, never into an error dump (`services/storage.py:60-71`).
* **`signed_item()` is defensive**: a non-dataclass item is returned unchanged rather than raising (`services/storage.py:74-80`).
* **No public read path is a sanctioned viewer path** — D32 requires signed URLs for `documents`; the artefact bucket has no public form at all (`services/report_artefact_storage.py:4-8`).
* `UNVERIFIED`: `api/v3_automatic_processing.py:567-623` converts a stored path with `path_from_url()` and surfaces it as a `file_url` field in that projection. Whether that payload is browser-facing (i.e. whether a bare key can reach a client) was **not established** by this audit.

---

## 9. Deletion, retention and object lifecycle

### 9.1 Deletion surfaces traced (`CODE-TRACED`)

| # | Path | Behaviour | Object deleted? | Audit entry? |
|---|---|---|---|---|
| D1 | `DELETE /api/organizations/{org_id}/files/{file_id}` (default) | Soft delete: sets `is_active = False`, `deleted_at = now()` on `organization_files` | **No** — bytes remain in the bucket | **No** audit call traced in the handler (`routes/organizations/files.py:436-513`) |
| D2 | `DELETE /api/organizations/{org_id}/files/{file_id}?permanent=true` | `.remove([path])` **then** row `DELETE`; a storage failure is caught and logged and the row is deleted anyway | Yes (best-effort) | **No** audit call traced in the handler |
| D3 | Retention enforcer (N3 / PX-7) | Soft-deletes eligible rows via `repos.files.expire_documents_older_than(cutoff, dry_run=…)`; per-domain reporting; **dry-run by default** | **No** — object bytes are never touched | Retention report returned to the caller; no per-row audit entry traced |

Untraced: no lifecycle rule, no bucket `lifecycle_configuration` write, no scheduled object-deletion job and no orphan-sweep job were found in the repository. `UNVERIFIED`: the live `storage.buckets.lifecycle_configuration` **value** was not read (only the column list was enumerated).

### 9.2 Retention policy as implemented

`backend/services/retention.py`

* **Eligible domains:** `document_retention_days`, `operational_telemetry_retention_days` (`:35`).
* **Only configured durations are enforced** — `None` means "not configured" and nothing is purged; no duration is invented (`:9-11, 57-72`).
* **Soft delete only** — the existing `deleted_at` convention; rows are never hard-deleted by retention (`:12-13`).
* **Never-purge list** (`_TELEMETRY_EXCLUDED_TABLES`, `:40-49`, exposed via `telemetry_excluded_tables()`): `document_processing_queue`, `processing_logs`, `report_versions`, `report_version_artifacts`, `evidence_line_items`, `calculation_snapshots`, `emissions_logs`, `audit_trail`.
* **Audit and evidence are explicitly excluded** as a security invariant (immutability of the calculation/evidence model) (`:14-17`).
* **Safe by default:** `enforce_retention()` defaults to `dry_run=True`; a deployment scheduler must pass `dry_run=False` explicitly (`:18-19, 87`).
* Telemetry pruning is scoped to two stores (`prune_operational_alerts_before`, `prune_operational_metrics_before`) and asserts the excluded list in its own report (`:111-146`).
* `compute_expired()` is a stub that returns `{}` (`:75-84`) — it is documented as a trivial/pure helper whose real work is done in the repository layer.

### 9.3 Object lifecycle position (factual)

| Property | Observation | Status |
|---|---|---|
| Soft delete removes the object | Never | `EXISTS` (by design) |
| Retention removes objects | Never — retention is row-level only | **`MISSING`** (no object lifecycle policy is enforced by application code) |
| Orphan objects possible | Yes: D2 deletes the row even if the storage remove failed; all other delete paths leave bytes in place | `CONFLICTING` / recorded (§17 F-6) |
| Live object count vs rows | ENV-LIVE: **58** objects in `documents` vs **11** rows in `organization_files` (`LIVE — READ-ONLY VERIFIED`) | The cause of the 47-object difference was **not established** (`UNVERIFIED`); the distinction matters because retention/delete only act on rows |
| Frozen artefacts | Never purged (explicitly in the never-purge list); protected by `UNIQUE (report_version_id)` and `upsert=false` on upload | `EXISTS` |
| Object overwrite | Not possible on the artefact path (`upsert=false`); on the `documents` paths keys are unique per upload (UUID or timestamp component), so an accidental overwrite requires an identical generated key | `EXISTS` |

---

## 10. Size limits, quotas and configuration surfaces

### 10.1 The two-layer limit model (`CODE-TRACED`)

| Layer | Values | Source of authority | May be changed by? |
|---|---|---|---|
| **Ratified platform caps** (hard ceilings) | file **10 MB**; **50** files per batch; **500 MB** per batch | `utils/upload_limits.py:39-48` (`PLATFORM_MAX_FILE_SIZE_MB`, `PLATFORM_MAX_FILES_PER_BATCH`, `PLATFORM_MAX_BATCH_TOTAL_MB`) + `20261024000000_ct_final_01…sql` header (ratified production scope, CT-FINAL-01) | Nobody — configuration may only tighten relative to them |
| **Effective defaults** (nothing configured) | file **6 MB**; **50** files; **500 MB** | `utils/upload_limits.py:53-55` | An administrator, within the caps |
| **Persisted configuration** | `system_settings` key `upload_policy`, fields `max_file_size_mb`, `max_files_per_batch`, `max_batch_size_mb` | `data/settings.py:42, 58-62, 417-484` | `PUT /api/v3/settings/upload-policy` (`require_admin()`), validated by `validate_upload_policy()` → 422 on out-of-range, nothing stored |

### 10.2 Enforcement semantics (`CODE-TRACED`)

| Condition | Outcome |
|---|---|
| File larger than the effective per-file limit | `UploadLimitExceeded(UPLOAD_FILE_TOO_LARGE)` → **HTTP 413** |
| Size cannot be determined | `UploadLimitExceeded(UPLOAD_SIZE_UNKNOWN)` → **HTTP 413** — an unknown size can never bypass the limit (fail-closed) |
| More files than the effective per-batch count | `UploadLimitExceeded(UPLOAD_TOO_MANY_FILES)` → **HTTP 400** (request-shape problem) |
| Batch total larger than the effective batch limit | `UploadLimitExceeded(UPLOAD_BATCH_TOO_LARGE)` → **HTTP 413** |
| Order of checks | file count → per-file → batch total, **all before** any storage object or database row is created |

Configuration resolution: `resolve_policy(settings_repo)` merges persisted values over the documented defaults (`DEFAULT_*`); a settings read failure is logged and falls back to the defaults — it never becomes "unlimited" (`utils/upload_limits.py:211-241`, module docstring `:17-24`).

### 10.3 Storage-layer alignment

`supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` (`CODE-TRACED`, header + body read in full):

* Sets `storage.buckets.file_size_limit = 10485760` for `documents` **only** when it is `NULL` or larger than the ratified cap — a deliberately configured *smaller* limit is never raised.
* Re-asserts `public = FALSE` (idempotent).
* Is a deliberate **NO-OP** where the storage layer is absent (`to_regclass('storage.buckets') IS NULL`) so a schema-only PostgreSQL cannot be broken by it.
* Ends with a **fail-closed assertion**: if `file_size_limit` is NULL or > 10485760, or the bucket is public, the migration raises.
* States explicitly that it does **not** touch `report-artifacts`, storage RLS policies, grants, object data or any application table.

### 10.4 Observed limit state (`LIVE — READ-ONLY VERIFIED`)

| Environment | `documents` bucket limit | Applied migration chain |
|---|---|---|
| **ENV-LOCAL** (`ct_local_93d5cdd`) | column `file_size_limit` **does not exist** in that environment's simplified `storage.buckets` (columns: `id`, `name`, `public`) → bucket-level limit **not present / not applicable** | `supabase_migrations.schema_migrations` relation absent → migration chain not tracked locally |
| **ENV-LIVE** | **`2097152` bytes (2 MiB)**, `public = false`, `allowed_mime_types = NULL` | Highest applied version = `20260927000000`; `20260823000000` (D32) applied; **`20261024000000` (CT-FINAL-01 bucket limit) NOT applied**; `20260919000000` applied |

### 10.5 Limit-related conflicts recorded (not reconciled)

* **F-2 — repository configuration vs ratified cap.** `supabase/config.toml:145` and `e2e/environment/supabase/config.toml:157` set the Supabase CLI stack `[storage] file_size_limit = "50MiB"`, i.e. five times the ratified 10 MB cap. (This is the CLI stack's global storage setting, not the bucket row the migration writes, but it is the value the local/staging stack provisions with.) `CONFLICTING`.
* **F-3 — live storage ceiling below the application's effective default.** In ENV-LIVE the bucket permits 2 MiB while the application's documented effective default permits 6 MB per file (cap 10 MB). An upload between 2 MiB and 6 MB therefore passes every application check and is rejected by the storage layer, with a raw storage error surface rather than a `UPLOAD_FILE_TOO_LARGE` code. Because the CT-FINAL-01 migration tightens only, it would **not** raise the 2 MiB value. `CONFLICTING`.
* **Quotas.** No per-organisation storage quota, no object-count quota, no total-bytes quota and no storage-specific rate limit were found in the traced code (`MISSING`).

---

## 11. Storage RLS policies and database objects

### 11.1 The four approved policies

`LIVE — READ-ONLY VERIFIED` — identical policy set observed in **both** probed environments (`pg_policies`, `schemaname='storage'`, `tablename='objects'`), count = 4:

| Policy | Command | Roles |
|---|---|---|
| `d32_documents_select_org_member` | SELECT | `{authenticated}` |
| `d32_documents_insert_org_member` | INSERT (WITH CHECK) | `{authenticated}` |
| `d32_documents_update_org_member` | UPDATE | `{authenticated}` |
| `d32_documents_delete_org_member` | DELETE | `{authenticated}` |

Predicate (verbatim from the live catalog, SELECT variant):

```
bucket_id = 'documents'
AND (storage.foldername(name))[1] = 'uploads'
AND ((storage.foldername(name))[2])::uuid IN (
      SELECT organization_members.organization_id
        FROM organization_members
       WHERE organization_members.user_id = auth.uid()
         AND organization_members.is_active = true)
```

`CODE-TRACED` consequences of that predicate:

1. **Only active organisation memberships grant access.** A consultant, CarbonTally staff member or Processing-Entity staff member holding a Supabase user JWT does **not** satisfy the predicate (no `is_org_consultant` / staff branch exists in it).
2. **Only the `uploads/` first path segment is covered** (§6.3). Objects under `batches/`, `manual_review/`, `organizations/`, `repaired_pdfs/` are outside the authorized prefix.
3. The second path segment is **cast to `uuid`**, so a path whose second segment is not a UUID (e.g. the live `manual_review/unknown`, `manual_review/mock-org-id` prefixes — `LIVE — READ-ONLY VERIFIED`) would raise a cast error rather than simply not match. Behavioural consequence **not verified** (`UNVERIFIED`).
4. No policy grants `anon` or `public`; only `authenticated` appears in `roles`.

### 11.2 Creation mechanism (provider context, not a migration)

`e2e/environment/scripts/d32_storage_operator.sql` (`CODE-TRACED`, read in full) is the single operational statement that cannot be a CarbonTally migration, because `CREATE POLICY` requires ownership of the provider-owned `storage.objects` table and the CarbonTally migration role must not receive that ownership (Route C, no privilege escalation).

* **Ordering (documented in its header):** LAYER 1 platform (Supabase Postgres image + Storage service) → LAYER 2 migrations 1–26 (application schema the predicates reference) → **this step** (private bucket + four policies) → LAYER 2 migrations 27–89 (migration 27 validates what this step created).
* **Idempotent:** each approved policy is `DROP POLICY IF EXISTS` then recreated; exactly four policies and one private bucket result.
* **Fail-closed:** absent platform layer, absent `public.organization_members`, unexpected policy count, wrong command, missing `authenticated` role, or any `anon`/`public` policy aborts the transaction.
* **No privilege statements:** it issues no `GRANT` and no RLS change other than the four named policies.
* **Single source of truth:** the predicate also lives in the header of `supabase/migrations/20260823000000_d32_private_documents_storage.sql`; repository tests assert the operator file still matches that header.

### 11.3 Application-side database objects

| Object | Storage-relevant content | Evidence |
|---|---|---|
| `organization_files` | `path` (canonical key), `bucket` (written as `'documents'`), `size_bytes`, `mime_type`, `file_type`, `is_active`, `deleted_at`, `last_accessed`, `access_count`, uploader/metadata | `LIVE — READ-ONLY VERIFIED` (ENV-LIVE: 11 rows, all `bucket='documents'`); `CODE-TRACED` writers in §5.2 |
| `report_version_artifacts` | `storage_bucket`, `object_key`, `content_sha256`, `byte_size`, `content_type` | `LIVE — READ-ONLY VERIFIED` — CHECK constraints: `storage_bucket = 'report-artifacts'`; `object_key = organization_id || '/' || report_id || '/' || report_version_id || '.pdf'`; `content_sha256 ~ '^[0-9a-f]{64}$'`; `byte_size > 0`; `content_type = 'application/pdf'` |
| `system_settings` | `upload_policy` (upload limits), `platform_retention` (retention) | `LIVE — READ-ONLY VERIFIED` (ENV-LIVE and ENV-LOCAL: one settings row; the only key observed was `platform_retention`) |

### 11.4 Not established (`UNVERIFIED`)

* The **table-level `GRANT` matrix on `storage.objects`** was probed with two differently-scoped queries that returned different shapes (one 0-row result, one listing roles `anon`, `authenticated`, `postgres`, `service_role`). This audit **did not** establish which relation that role list referred to, nor whether the grants are the provider defaults. The direct/user-JWT exposure therefore rests on *grants + RLS together*, and only the RLS half is verified (see §15.4 for the matching open item).

---

## 12. Storage migrations and schema state

### 12.1 Migrations that carry storage behaviour

| Migration | Role in storage management | Status |
|---|---|---|
| `supabase/migrations/20260823000000_d32_private_documents_storage.sql` (15,583 bytes) | **D32 primary artefact.** Makes the `documents` bucket PRIVATE (`UPDATE storage.buckets SET public = FALSE WHERE name = 'documents'`, line 121), documents the four approved policy predicates in its header (lines 82–106), carries the provider-context escalation rationale, and validates (before/after assertion) that exactly the four approved policies exist and that nothing is granted to `anon`/`public`. It also records the canonical upload prefix requirement (`'bucket_id','documents','foldername','uploads'`, line 168). | `EXISTS`; applied in ENV-LIVE (`LIVE — READ-ONLY VERIFIED`) |
| `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` (4,167 bytes) | **CT-FINAL-01 storage-layer alignment** — tighten-only `file_size_limit = 10485760` + private re-assertion + fail-closed assertion; NO-OP where the storage layer is absent; explicitly does not touch `report-artifacts`, RLS, grants or objects. | `EXISTS`; **not applied in ENV-LIVE** (highest applied version `20260927000000`), not tracked in ENV-LOCAL |
| `supabase/migrations/20261012000000_p17d_scope3_category_taxonomy.sql` | Mentions storage but is a taxonomy migration — **not** a storage-management artefact | reference only |
| `supabase/migrations/20261020000000_p17k_governed_capability_catalogue.sql` | Mentions storage but is a capability-catalogue migration — **not** a storage-management artefact | reference only |

Storage-referencing migration inventory obtained by grepping the migration chain for `storage` (four files, above). **No migration creates the `report-artifacts` bucket** (D-11 operational provisioning).

### 12.2 Operator scripts (part of the storage deployment contract, not migrations)

| Script | Purpose | Verified existence |
|---|---|---|
| `e2e/environment/scripts/d32_storage_operator.sql` | Creates the four D32 policies in provider context; asserts bucket private + exactly four policies + no `anon`/`public` | `EXISTS` (9,257 bytes) |
| `e2e/environment/scripts/verify_d32_policy_semantics.sql` | Behavioural verification of the predicate | `EXISTS` (11,329 bytes) |
| `e2e/environment/scripts/apply_migrations.sh`, `canonical_schema_rebuild.sh`, `d32_search_path_regression.sh` | Enforce the layer ordering and the role contract around the operator step | `EXISTS` |
| `docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md` | Migration drift gate procedure | `EXISTS` |
| `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` | Bucket provisioning runbook for `report-artifacts` | `EXISTS` |

### 12.3 Environment schema state (`LIVE — READ-ONLY VERIFIED`)

| Fact | ENV-LOCAL | ENV-LIVE |
|---|---|---|
| `storage.buckets` columns | `id`, `name`, `public` (3) | `id`, `name`, `owner`, `created_at`, `updated_at`, `public`, `avif_autodetection`, `file_size_limit`, `allowed_mime_types`, `owner_id`, `type`, `versioning_status`, `lifecycle_configuration`, `lifecycle_configuration_generation` (14) |
| Buckets present | `documents` (private) | `documents` (private) — **no `report-artifacts`** |
| Migration ledger | `supabase_migrations.schema_migrations` **absent** | present; latest `20260927000000` |
| `storage.objects` rows | 0 | 58 |
| `organization_files` rows | 0 | 11 |

**Interpretation guard:** the two environments are different schema generations (the local one is a simplified/older storage schema without `file_size_limit`). Findings drawn from one environment are labelled with that environment and must not be transferred to the other.

### 12.4 Migration-chain vs ratified-state finding recorded (not reconciled)

ENV-LIVE has D32 applied but **not** CT-FINAL-01's storage alignment, and its bucket limit is 2 MiB — i.e. the ratified 10 MB platform cap is not the operative storage-layer ceiling in the probed environment, and the migration that would align it has not run there. Whether that is expected for that environment (staging vs production), and whether the 2 MiB value was set deliberately by an operator, is **`UNVERIFIED`**. Recorded as F-3 (§10.5) / F-9 (§17).

---

## 13. Live environment state (read-only verified)

### 13.1 ENV-LIVE — facts observed by SELECT-only probes

| Fact | Value |
|---|---|
| Buckets in `storage.buckets` | exactly one: `documents` |
| `documents.public` | `false` |
| `documents.file_size_limit` | `2097152` (2 MiB) |
| `documents.allowed_mime_types` | `NULL` |
| Storage policies | exactly 4 (`d32_documents_{select,insert,update,delete}_org_member`), all `{authenticated}` |
| `storage.objects` rows | **58** |
| Object first-segment distribution | `manual_review/*` = **38**; `uploads/*` = **14**; `batches/*` = **6** |
| Object second-segment examples | real organisation UUIDs, plus the literals `unknown` and `mock-org-id` (non-UUID) |
| `public.organization_files` rows | **11**, all `bucket = 'documents'` |
| `report_version_artifacts` | table present; CHECK constraints as quoted in §11.3 |
| `report-artifacts` bucket | **absent** |
| `system_settings` | 1 row; the only key observed was `platform_retention`; **no `upload_policy` row observed** → the upload policy is unconfigured and the documented effective defaults are therefore what applies (§10.1) |
| Migration ledger | latest applied `20260927000000`; `20260823000000` applied; `20261024000000` **not** applied |
| Factor store (context only) | `emission_factors` row count 7,049 |

### 13.2 ENV-LOCAL — facts observed by SELECT-only probes

| Fact | Value |
|---|---|
| Buckets | exactly one: `documents`, `public = false` |
| Storage policies | the same four `d32_documents_*` policies on `storage.objects` |
| `storage.objects` rows | 0 |
| `organization_files` rows | 0 |
| `organizations` / `organization_members` rows | 25 / 16 |
| `system_settings` | 1 row (`platform_retention`) |
| Migration ledger | absent |

### 13.3 What a read-only SQL probe cannot establish

The following are explicitly **`UNVERIFIED`** in this audit, and no claim about them is made anywhere in this document:

1. **Storage API behaviour** — no `create_signed_url`, upload, download, `remove` or `list_buckets` call was executed. Signed-URL issuance, TTL enforcement and object read/write therefore rest on code traces only.
2. **RLS behaviour under a real user JWT** — no JWT was minted and no direct Storage request was issued; the predicate is verified as *catalog text*, not as runtime allow/deny behaviour. The repository's own behavioural verifier (`verify_d32_policy_semantics.sql`) exists but was not run (running it would require provider credentials and is an operational action, not a read-only inspection).
3. **Cross-tenant negative test** — no cross-organisation request was attempted (§15.4).
4. **Bucket provisioning state of environments not reachable from this checkout** (staging / production project consoles) — not probed.
5. **ENV-LIVE project identity** — see §2.2.

---

## 14. Report-artefact storage — a separate bucket concern

### 14.1 Why it is separate

`report-artifacts` holds **internally generated output**, not user uploads. It is therefore deliberately outside every upload ingress, every upload limit and the `documents` bucket's policy set: the CT-FINAL-01 migration header states it is *"unchanged"* by that migration, and the provisioning document states the application never creates the bucket.

### 14.2 Mandated properties (`DOCUMENTED INTENT` + `CODE-TRACED`)

| Property | Value / rule | Source |
|---|---|---|
| Bucket | `report-artifacts`, private — the **only** bucket permitted | `domain/report_artefact.py:24, 103-110` (raises if any other bucket is passed); `services/report_artefact_storage.py:4-8` |
| Object key | **Derived**, never caller-supplied: `{organization_id}/{report_id}/{report_version_id}.pdf` | `domain/report_artefact.py` (`object_key_for`) |
| Content type | `application/pdf` only | `domain/report_artefact.py:172`; DB CHECK (live-verified) |
| Integrity | SHA-256 lowercase hex recorded on the row; `byte_size > 0`; PDF magic `%PDF-` sanity check | `domain/report_artefact.py`; DB CHECKs (live-verified) |
| Immutability | one record per finalised version (`UNIQUE (report_version_id)`) and `upload(..., upsert=false)` — a frozen artefact is never overwritten | `services/report_artefact_storage.py:52-59` |
| Access | signed URLs only, TTL **300 s**, issued **after** authorization; no public URL form exists in the adapter | `services/report_artefact_storage.py:22-24, 61-65` |
| Mandatory at finalisation | no optional/exception path (nothing in the module can express "FINAL without a frozen artefact") | `domain/report_artefact.py:100-102` |
| Preflight | read-only `bucket_exists()` via `list_buckets()`; absence or provider error → `False` (fail-safe, never raises) | `services/report_artefact_storage.py:74-90` |

### 14.3 Provisioning state

| Environment | Bucket present? | Evidence |
|---|---|---|
| ENV-LIVE | **No** — `storage.buckets` contains only `documents` | `LIVE — READ-ONLY VERIFIED` |
| ENV-LOCAL | **No** | `LIVE — READ-ONLY VERIFIED` |
| Repository | **No migration and no `create_bucket` call in `backend/`** — provisioning is an operator action | `CODE-TRACED`; `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` ("Bucket created locally / in staging / in production — **NO — not performed**") |

**Consequence recorded (not reconciled):** in the probed environments the frozen-artefact storage path cannot succeed, while the schema and code mandate the artefact. The provisioning document's own verification section requires one end-to-end finalisation in a disposable environment, which is the only proof that the real storage path works (the unit/runtime suites use the in-memory adapter). Status: **`MISSING` (provisioning) / `UNVERIFIED` (runtime)**.

---

## 15. Cross-tenant isolation and negative-access evidence

### 15.1 Application-layer isolation (`CODE-TRACED`)

| Layer | Control |
|---|---|
| Org member upload (I1) | `ensure_org_access(current_user, organization_id)` rejects a foreign `organization_id` before anything is written; viewer role → 403 |
| Org member upload (I2) | explicit `str(org_id) != str(current_user.organization_id)` → 403 (a body-supplied org is never trusted) |
| Org member bulk upload (I3) | org is taken from `current_user.organization_id`, never from the request |
| Legacy upload (I4) | `enforce_org_body_scope(organization_id, current_user)` — the historical "any member could write into another tenant" defect's fix |
| Document read/sign (S1, S2) | the row is loaded by id and then `ensure_org_access(current_user, doc.organization_id)` is applied — a foreign document id yields 403, not a signed URL |
| Legacy file read/sign/download/delete (S7, S8, D1, D2) | rows are filtered by `organization_id = current_user.organization_id` **and** `is_active` |
| Batch status/progress (legacy upload route) | F2 IDOR fix: non-admin callers are checked against `organization_members` for the batch's organisation; 403 otherwise |
| Consultant (I7 and consultant reads) | `require_consultant()` → `_authorized_client_org()` (firm ownership + **active** `consultant_clients` grant per `D15`) → per-capability `ensure_consultant_permission()` |
| Entity staff (S3) | `_entity_workspace_guard()` + `ensure_entity_batch_access()` / `_entity_checked_item()`; item lists filtered through the effective entity map; **persisted paths are never returned** (only signed URLs, view-only) |
| Report artefact (S9, S10) | `_authorize_read(current_user, organization_id)`; Processing-Entity and CarbonTally staff are denied on that surface |

### 15.2 Storage-layer isolation (`LIVE — READ-ONLY VERIFIED` catalog text)

The four policies restrict any direct (user-JWT) object access to objects whose `foldername[2]` is an organisation of which `auth.uid()` is an **active** member — and only inside the `uploads/` prefix (§11.1). No `anon`/`public` policy exists.

### 15.3 Residual exposure surface (factual, not a verdict)

Because the application always uses the service-role client, tenant isolation on the **application** path depends entirely on the API guards above — storage RLS never participates in it. Any code path that passed an unvalidated `organization_id` to a service-role storage call, or that returned a persisted path to a client, would bypass RLS entirely. One such projection was observed but not resolved (`UNVERIFIED` — §8.2, `api/v3_automatic_processing.py:567-623`).

### 15.4 Negative-access evidence status

| Test | Performed? | Status |
|---|---|---|
| Cross-tenant upload with a foreign `organization_id` | **No** | `UNVERIFIED` — code-traced guard only |
| Cross-tenant document read / signed URL with a foreign `file_id` | **No** | `UNVERIFIED` — code-traced guard only |
| Direct Storage access with a user JWT (RLS allow/deny) | **No** | `UNVERIFIED` — policy text verified, behaviour not exercised |
| Consultant access with a non-active client grant | **No** | `UNVERIFIED` — code-traced guard only |
| Entity staff access to an unassigned batch/item | **No** | `UNVERIFIED` — code-traced guard only |

`LIVE — READ-ONLY VERIFIED` isolation facts are limited to: bucket privacy (`public = false`), absence of `anon`/`public` policies, the policy predicate text, and the object/row counts in §13.

---

## 16. Actor × operation authorization matrix

### 16.1 Method and legend

Actors are cited from the canonical actor table (`docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`, §3, rows A1–A14); they are **not** redefined here. Actor columns are grouped where the storage-relevant guard is identical.

Every cell is `CODE-TRACED` unless stated otherwise. `LIVE — READ-ONLY VERIFIED` applies only to the bucket/policy facts in OP-14. **No cell is behaviourally executed in this audit** — see §15.4.

| Column | Actors (as cited) |
|---|---|
| **A1/A2** | A1 Customer org **owner**, A2 Customer org **admin** |
| **A3** | A3 Customer org **member** |
| **A4** | A4 Customer org **viewer** |
| **A5–A8** | Internal CarbonTally staff: A5 operator, A6 reviewer, A7 QC specialist, A8 staff admin |
| **A13** | A13 Processing-Entity staff |
| **A9–A12** | Consultant firm owner / manager / consultant / viewer (authority comes from `consultant_firm_members` boolean flags, not from the role name) |
| **SVC** | Service-role client (`infra.supabase.get_service_client()`) — not an end-user actor |

Cell values: `ALLOW` · `DENY` · `N/A` (actor class cannot reach this surface by construction) · `PARTIAL` · `UNVERIFIED`.

### 16.2 Matrix — rows OP-1 … OP-7

| Operation | A1/A2 | A3 | A4 | A5–A8 | A13 | A9–A12 | SVC |
|---|---|---|---|---|---|---|---|
| **OP-1** Upload via canonical pipeline `POST /api/v3/uploads` | `ALLOW` — `require_org_member` + `ensure_org_access` + policy limit | `ALLOW` — same guards | `DENY` — 403 "Viewers are read-only and cannot upload documents" (CL-42), before any write | `DENY` — `require_org_member` refuses non-members (`is_org_member`), so the internal-staff bypass inside `ensure_org_access` is unreachable behind it | `DENY` — same guard; `ensure_org_access` additionally refuses entity staff outright | `N/A` — consultant capacity must use OP-4 | `N/A` (executes the write on behalf of the authorized caller) |
| **OP-2** Upload via legacy `POST /api/upload` / `POST /api/repair-pdf` | `ALLOW` — `require_org_member` + `enforce_org_body_scope` | `ALLOW` | **`PARTIAL`/`UNVERIFIED`** — **no viewer denial is traced on these legacy handlers** (CL-42's check exists only on OP-1) | `DENY` — `require_org_member` | `DENY` | `N/A` | `N/A` |
| **OP-2b** Legacy helpers `POST /api/upload-csv`, `/api/upload-pdf`, `/api/test-upload`, `/api/upload-batch` | `UNVERIFIED` — guards not established by this audit (no object write traced for the CSV/PDF helpers) | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `N/A` |
| **OP-3** Upload via `POST /api/organizations/{org_id}/files/upload` and `/bulk-upload` | `ALLOW` — `require_org_member` + explicit org equality | `ALLOW` | **`PARTIAL`/`UNVERIFIED`** — no viewer denial traced on these handlers | `DENY` — `require_org_member` | `DENY` | `N/A` | `N/A` |
| **OP-4** Consultant uploads for a client `POST /api/v3/consultants/clients/{client_id}/documents` | `N/A` / `DENY` — consultant context does not resolve while the caller acts as an org member | `N/A` / `DENY` | `N/A` / `DENY` | `N/A` — not a consultant capacity | `N/A` | `ALLOW` **only if** active firm membership **and** active `consultant_clients` grant **and** `can_upload_documents = true`; otherwise 404 (cross-firm) / 403 (no active grant) / 403 (capability absent); then the same shared writer and same policy limits as OP-1 | `N/A` |
| **OP-5** List/read document metadata | `ALLOW` | `ALLOW` | `ALLOW` (read-only role) | `ALLOW` on ops surfaces; internal staff hold the operational any-org bypass in `ensure_org_access` | `ALLOW` only for assigned work; **persisted paths never returned** | `ALLOW` for granted clients (`GET …/clients/{client_id}/documents`) | `N/A` |
| **OP-6** Obtain a signed document URL (S1) | `ALLOW` — `require_org_member` + `ensure_org_access` + service-role signing | `ALLOW` | `ALLOW` (read path; viewer is read-only but this is a read) | `DENY` on this endpoint (`require_org_member`); internal staff obtain URLs through their own ops/entity workspaces | `DENY` on this endpoint; view-only URLs are issued in the assigned-workspace payloads instead | `DENY` on this endpoint (consultant capacity is not an org member); consultant documents are served by consultant-scoped surfaces | `N/A` (the signer) |
| **OP-7** Download raw bytes `GET /api/organizations/{org_id}/files/{file_id}/download` | `ALLOW` — `require_org_member`, row filtered by org + `is_active` | `ALLOW` | `PARTIAL`/`UNVERIFIED` — no viewer-specific denial traced; this path returns bytes rather than a URL, so a viewer that is denied the upload path is not denied this one by any traced check | `DENY` — `require_org_member` | `DENY` | `N/A` | `N/A` |

### 16.3 Matrix — rows OP-8 … OP-14

| Operation | A1/A2 | A3 | A4 | A5–A8 | A13 | A9–A12 | SVC |
|---|---|---|---|---|---|---|---|
| **OP-8** Soft delete (trash) `DELETE …/files/{file_id}` | `ALLOW` — `require_org_member`, org-scoped row | `ALLOW` | `PARTIAL`/`UNVERIFIED` — no viewer-specific denial traced on the delete handler | `DENY` — `require_org_member` | `DENY` | `N/A` | `N/A` |
| **OP-9** Permanent delete `…?permanent=true` (removes the object) | `ALLOW` (same guard; best-effort object removal, no audit entry traced) | `ALLOW` | `PARTIAL`/`UNVERIFIED` — as OP-8 | `DENY` | `DENY` | `N/A` | `N/A` |
| **OP-10** Configure upload limits `GET`/`PUT /api/v3/settings/upload-policy` | `DENY` — `require_admin()` is not satisfied by org roles | `DENY` | `DENY` | `ALLOW` **only** for an A8-style `staff_roles.name='admin'` identity (`require_admin`) | `DENY` | `DENY` | `N/A` |
| **OP-11** Apply retention enforcement | `UNVERIFIED` — no HTTP caller of `enforce_retention()` exists in the traced code; it is a server-side entry point whose invocation (deployment scheduler) was not identified. Config surface `/api/v3/settings/retention` exists; dry-run is the default | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `N/A` |
| **OP-12** View documents inside the ops / entity workspace (S3, S4) | `DENY` — these are staff surfaces (`require_staff`) | `DENY` | `DENY` | `ALLOW` — internal staff (operational oversight); signed, view-only URLs; persisted paths withheld | `ALLOW` **only** for assigned batches/items (`_entity_workspace_guard`, `ensure_entity_batch_access`, effective item map); signed, view-only, no download boundary | `DENY` — not a staff capacity | `N/A` (the signer) |
| **OP-13** Frozen report artefact read / signed URL (S9, S10) | `ALLOW` — `require_org_member` + `_authorize_read`; signed URL TTL 300 s | `ALLOW` | `ALLOW` (read) | `DENY` — `_authorize_read` denies CarbonTally staff on this surface | `DENY` — `_authorize_read` denies Processing-Entity staff | `DENY` — not an org member | `N/A` |
| **OP-14** **Direct Storage access with a Supabase user JWT** (bypasses the application) | `ALLOW`, but **only** for objects whose first segment is `uploads` **and** whose second segment is an organisation of which the caller is an **active** member — `LIVE — READ-ONLY VERIFIED` policy predicate (§11.1) | `ALLOW` — same predicate | `ALLOW` — the predicate is membership-based and does not distinguish the viewer role | `DENY` — no staff branch exists in the predicate | `DENY` — no entity branch exists in the predicate | `DENY` — the predicate has no consultant/grant branch (`client_access` and `consultant_clients` are not consulted by it) | `N/A` — the service role bypasses storage RLS entirely |

### 16.4 Matrix notes (factual)

1. **`ensure_org_access` is not a flat rule** (`api/dependencies.py:163-189`): internal CarbonTally staff receive an **operational any-organisation bypass**; Processing-Entity staff are **denied outright**; org members are restricted to their own organisation. OP-1/OP-6 sit behind `require_org_member()`, which refuses non-members, so the internal-staff bypass is not reachable on those endpoints.
2. **Viewer (A4) enforcement is inconsistent across surfaces** (`CODE-TRACED`): an explicit, written viewer denial exists on OP-1 only. OP-2, OP-3, OP-7, OP-8, OP-9 have **no** traced viewer-specific check — `require_org_member()` accepts any org role. Recorded as finding F-10 (§17); not reconciled.
3. **Storage RLS is a different authorization model from the application's**: it knows only "active organisation member" and only the `uploads/` prefix, so it cannot express consultancy grants, staff oversight, or viewer read-only (§11.1, §16.4 OP-14).
4. **Consultant authority is capability-based, not role-based**: `CONSULTANT_PERMISSIONS` maps `upload_documents → can_upload_documents` (and `manage_clients`, `generate_reports`, `manage_team`, `extract`, `map`, `validate`, `calculate`, `confirm_automation`, `submit`); revocation authority is deliberately role-based (`owner`/`admin`/`manager`) (`api/consultant_auth.py:36-57, 152-181`).
5. The `client_access` per-member shortcut does **not** independently grant organisation access — the active `consultant_clients` row is the single source (`api/consultant_auth.py:212-242`, D15).

---

## 17. Documented intent vs implemented behaviour — conflicts register

Findings are **recorded, not reconciled**. Each row states what the evidence shows, what the documentation/decision states, and the status. No fix, target or recommendation is implied.

| ID | Finding (evidence) | Documented intent | Status |
|---|---|---|---|
| **F-1** | The storage-RLS predicate authorizes only the `uploads/` first path segment, while the object-path model uses at least five prefixes (`uploads/`, `organizations/`, `repaired_pdfs/`, and the live-only `batches/`, `manual_review/`). Live: 44 of 58 objects sit outside the authorized prefix (`LIVE — READ-ONLY VERIFIED`; `CODE-TRACED`) | D32 hardening: *"only authenticated members of the owning organisation can read/manage the objects under `uploads/<org_id>/`"* (`20260823000000_d32_private_documents_storage.sql` header wording: *"the objects under ``uploads/<org_id>/``"*) | `CONFLICTING` |
| **F-2** | Supabase CLI stack config sets `[storage] file_size_limit = "50MiB"` (`supabase/config.toml:145`, `e2e/environment/supabase/config.toml:157`) | Ratified cap is 10 MB per file (CT-FINAL-01); configuration may only tighten relative to the cap | `CONFLICTING` |
| **F-3** | ENV-LIVE `documents.file_size_limit = 2097152` (2 MiB), while the application's documented effective default is 6 MB per file (cap 10 MB). Uploads between 2 MiB and 6 MB pass every application check and fail at the storage layer with a raw storage error, not the canonical `UPLOAD_FILE_TOO_LARGE` code; the CT-FINAL-01 migration tightens only and would not raise the smaller value | CT-FINAL-01: 10 MB per file enforced **server-side**, with the storage layer aligned to the same number | `CONFLICTING` |
| **F-4** | Residual public-URL construction on a private bucket: `get_public_url()` is still called in `routes/upload.py:494, 718` and `routes/organizations/files.py:594`. In the legacy `/api/upload` handler the returned URL is assigned to a local variable and does **not** appear among the fields of the `file_record` built by the same handler; in `*/repair-pdf` it is returned to the caller | D32: *"the documents bucket is PRIVATE. Only short-lived signed URLs are ever produced — never a public URL"* (`api/v3_documents.py` comment) | `CONFLICTING` |
| **F-5** | `GET …/files/{file_id}/url` accepts `expires_in` (60–86400, default 3600) and echoes it in the response (`"expires_in": expires_in`, `"expires_at"`), but the helper always requests 3600 s | The endpoint advertises a caller-controlled signed-URL lifetime | `CONFLICTING` (metadata vs behaviour; behaviour not executed) |
| **F-6** | On `?permanent=true` the handler deletes the `organization_files` row **even when** the storage `remove()` failed (the exception is caught and only logged), so an orphaned object can remain with no row; no other delete path removes bytes | Retention/delete semantics assume the record is the unit of lifecycle management | `CONFLICTING` |
| **F-7** | No object-lifecycle enforcement exists in application code: retention soft-deletes rows only, and no bucket lifecycle rule or orphan sweep was traced; live evidence shows 58 objects against 11 `organization_files` rows | Retention is described as a configurable platform capability (N3 / PX-7) whose enforcement is row-level and explicitly excludes audit/evidence | `MISSING` (object lifecycle) / cause of the 47-object gap `UNVERIFIED` |
| **F-8** | The table-level `GRANT` matrix on `storage.objects` was not established (two differently-scoped probes returned different shapes) | D32 asserts that **no** anonymous access is permitted (`anon`/`public` policy check), and the operator script refuses broad grants — but the grant catalogue itself was not resolved by this audit | `UNVERIFIED` |
| **F-9** | ENV-LIVE's applied migration ceiling is `20260927000000`; the CT-FINAL-01 bucket-size-limit migration (`20261024000000`) is **not applied** there, so the storage layer is not aligned with the ratified cap in that environment | CT-FINAL-01 requires the storage layer to be aligned with the ratified per-file limit | `CONFLICTING` / environment expectation `UNVERIFIED` |
| **F-10** | Viewer read-only (CL-42) is written as an explicit 403 on the canonical upload endpoint only. The legacy upload (`/api/upload`, `/api/repair-pdf`), the organisation-files upload/bulk-upload, download, and both delete handlers carry no traced viewer-specific check — `require_org_member()` accepts any organisation role | CL-42 / product model: a Viewer is read-only | `CONFLICTING` (not behaviourally executed) |
| **F-11** | Neither delete path writes an audit entry; only the evidence reverse-lookup path was traced as audited (`evidence.reverse_lookup`) | Auditability is a stated security invariant (`services/retention.py:14-17`), and evidence/audit tables are never purged | `CONFLICTING` (asymmetry recorded) |
| **F-12** | The `report-artifacts` bucket is mandated by B4 and by the schema CHECK constraints but is absent from both probed environments; no migration creates it and no `create_bucket` call exists in `backend/`; the provisioning document records "not performed" | `B4-D5/D6/D7` make the frozen artefact mandatory at finalisation in that private bucket | `MISSING` (provisioning) / `UNVERIFIED` (runtime path) |
| **F-13** | The canonical upload path stores a **freshly signed** URL inside `organization_files.metadata.file_url`, and a signed URL expires (3600 s) | `path` is the durable identity; signed URLs are per-view, short-lived artefacts | `CONFLICTING` (a persisted field that is valid only for an hour) |
| **F-14** | Exactly-one-bucket reality vs two-bucket design: both probed environments contain only `documents`; the design requires `documents` + `report-artifacts` | Two buckets are named in code and schema (`DOCUMENTS_BUCKET`, `ARTEFACT_BUCKET`) | `CONFLICTING` (same root cause as F-12) |

---

## 18. Conformance status inventory

Status vocabulary: `EXISTS` · `PARTIAL` · `MISSING` · `UNKNOWN` · `CONFLICTING` · `UNVERIFIED`.

| # | Item | Status | Basis |
|---|---|---|---|
| C-01 | Single storage provider (Supabase Storage) with a named service-role access path | `EXISTS` | `CODE-TRACED` §4.1 |
| C-02 | `documents` bucket exists and is private | `EXISTS` | `LIVE` (both environments) |
| C-03 | `report-artifacts` bucket exists and is private | `MISSING` | `LIVE` (absent in both) + provisioning doc |
| C-04 | Only two buckets are referenced by code/schema (no drift into a third) | `EXISTS` | `CODE-TRACED` (`DOCUMENTS_BUCKET`, `ARTEFACT_BUCKET`; bucket-name guard in `domain/report_artefact.py:103-110`) |
| C-05 | Canonical object-path model documented | `PARTIAL` | Producers P1–P5 are traceable in code; **no single document** states the full key model, and P6 prefixes exist only in live data |
| C-06 | Every user-upload ingress enforces the canonical upload policy server-side | `EXISTS` | `CODE-TRACED` (I1–I4, I6–I8) §7.1 |
| C-07 | Registered-but-unverified legacy helper ingresses (`upload-csv`, `upload-pdf`, `test-upload`, `upload-batch`) | `UNVERIFIED` | §7.1 OP-2b |
| C-08 | Upload limits persisted in `system_settings` and admin-configurable within ratified caps | `EXISTS` | `CODE-TRACED` (`data/settings.py`, `api/v3_settings.py`) |
| C-09 | Storage layer aligned to the ratified per-file limit | `MISSING` in ENV-LIVE / `PARTIAL` overall | Migration exists but is unapplied there; live limit 2 MiB (F-9) |
| C-10 | Repository CLI stack configuration consistent with the ratified cap | `CONFLICTING` | `50MiB` vs 10 MB (F-2) |
| C-11 | Per-organisation / total storage quota or storage rate limit | `MISSING` | §10.5 |
| C-12 | Private-bucket viewer path is signed URLs only | `PARTIAL` | Sanctioned surfaces use signed URLs; residual `get_public_url()` calls remain (F-4) |
| C-13 | Signed-URL TTL is bounded and documented per surface | `PARTIAL` | 3600 s for documents, 300 s for artefacts; legacy `…/url` endpoint's advertised TTL is not honoured (F-5) |
| C-14 | Storage RLS exists, is scoped, and grants nothing to `anon`/`public` | `EXISTS` | `LIVE` (4 policies, `{authenticated}`) |
| C-15 | Storage RLS predicate covers the object-path model actually in use | `CONFLICTING` | Only `uploads/` covered; 44/58 live objects outside (F-1) |
| C-16 | RLS behaviour proven under a real user JWT | `UNVERIFIED` | §13.3, §15.4 |
| C-17 | RLS policies created through a repeatable, idempotent, fail-closed operator step | `EXISTS` | `e2e/environment/scripts/d32_storage_operator.sql` |
| C-18 | Storage-object access audit trail | `MISSING` | Only `evidence.reverse_lookup` audited; deletes unaudited (F-11) |
| C-19 | Retention policy enforcement that covers stored objects | `MISSING` | Row-level soft delete only (F-7) |
| C-20 | Immutable frozen report artefact (derived key, SHA-256, one per version, no overwrite) | `EXISTS` | `CODE-TRACED` + live CHECK constraints |
| C-21 | Frozen-artefact storage reachable end-to-end | `UNVERIFIED` | Bucket absent (F-12); no runtime proof performed |
| C-22 | Cross-tenant read/write denial proven behaviourally | `UNVERIFIED` | §15.4 |
| C-23 | Service-role usage is deliberate and documented as RLS-bypassing | `EXISTS` | `services/storage.py:14-16` |
| C-24 | Orphan-object risk eliminated | `CONFLICTING` | Row deleted on failed object removal (F-6) |
| C-25 | `organization_files` holds a durable, non-expiring object identity | `PARTIAL` | `path`/`bucket` durable; stored `metadata.file_url` expires (F-13) |
| C-26 | Every ingested document reaches the durable processing pipeline from every ingress | `PARTIAL` | True for the shared writer (I1/I7); the legacy ingresses write records without the same enqueue (their pipeline path was not traced) |
| C-27 | Storage tests exist for the hardening and limit behaviour | `EXISTS` | `test_storage_security.py`, `test_ct_final_01_upload_limits.py` |
| C-28 | Storage layer behaviour tested end-to-end in this audit | `UNVERIFIED` | No storage API call was executed (§13.3) |

---

## 19. Limitations, open items and final report

### 19.1 Limitations of this baseline

1. **No execution.** No application code, test, migration, SQL statement (beyond `SELECT`), storage API call or HTTP request was executed. Everything except the live catalog/count facts in §13 is `CODE-TRACED`.
2. **No behavioural security proof.** Cross-tenant denial, RLS enforcement under a JWT, consultant capability denial and entity-staff scoping are **not** proven here (§15.4).
3. **Environment provenance.** ENV-LIVE is "the database the configured live DSN points at"; its identity as the production project is `UNVERIFIED` (§2.2). ENV-LOCAL is a simplified storage schema (§12.3), so its missing `file_size_limit` column and absent migration ledger are environment facts, not findings about the platform.
4. **Several large modules were read only in ranges**, not in full (`routes/upload.py`, `routes/organizations/files.py`, `api/v3_consultants.py`, `api/v3_operations.py`, `api/v3_pe.py`, `api/v3_evidence.py`, `api/v3_emissions.py`, `api/v3_automatic_processing.py`, `auth.py`). Statements about them are limited to the cited regions; a guard outside a cited region could change an OP-2b/OP-7 conclusion.
5. **The storage `GRANT` catalogue was not resolved** (F-8).
6. **State outside the two probed environments was not inspected** (staging, production consoles; provider settings such as `lifecycle_configuration` values).

### 19.2 Open items (unresolved by this audit — no action implied)

| # | Open item | Why unresolved |
|---|---|---|
| O-1 | Which environments are expected to have the CT-FINAL-01 bucket alignment applied | Migration unapplied in ENV-LIVE; expectation not documented for that environment (`UNVERIFIED`) |
| O-2 | Whether the live 2 MiB bucket limit is deliberate | No record found in the repository |
| O-3 | Which relation the observed storage `GRANT` rows belong to | Two inconsistent probes (F-8) |
| O-4 | Whether `api/v3_automatic_processing.py:567-623` surfaces a bare storage key to a browser | Payload consumer not established |
| O-5 | Who invokes `enforce_retention()` in a deployed system | No caller traced |
| O-6 | Whether the legacy helper ingresses (`upload-csv`, `upload-pdf`, `test-upload`, `upload-batch`) write objects or accept viewer roles | Regions not read |
| O-7 | Whether the 47-object surplus over `organization_files` rows is expected | Cause not established |
| O-8 | Whether the `report-artifacts` bucket has since been provisioned in any environment | Not probed |

### 19.3 Final report — 15 items

1. **Bucket reality.** The design names two buckets (`documents`, `report-artifacts`); both probed environments contain **only `documents`, private** — the mandated `report-artifacts` bucket is absent, is created by no migration and by no `create_bucket` call in `backend/`, and the repository's own provisioning document records it as not performed. (`LIVE — READ-ONLY VERIFIED`, `CODE-TRACED`; F-12, F-14, C-03.)
2. **Private-document viewer model.** The `documents` bucket is private, and the only sanctioned viewer access is a server-issued, expiring signed URL (3600 s for documents, 300 s for frozen artefacts), issued **after** authorization on every traced surface. (`CODE-TRACED`; §8, S1–S10, C-12.)
3. **Service-role access model.** Every application object write, read and signing call goes through the RLS-bypassing service-role client; storage RLS therefore never participates in the application's own authorization, which lives entirely in the API guards. (`CODE-TRACED`; §4.1, §15.3, C-23.)
4. **Storage RLS present and narrow.** Exactly four policies exist (`d32_documents_{select,insert,update,delete}_org_member`), granted to `authenticated` only, with no `anon`/`public` policy, in both probed environments. (`LIVE — READ-ONLY VERIFIED`; C-14.)
5. **RLS scope does not match the path model actually in use.** The predicate authorizes only `uploads/<org_uuid>/…` for active members of that organisation; live data shows 44 of 58 objects under `manual_review/` or `batches/`, outside the authorized prefix. (`LIVE — READ-ONLY VERIFIED`; F-1, C-15.)
6. **Object-path model.** Five producers are traceable in code (`uploads/<org>/<date>/<uuid>_<file>` and its timestamp variant, `organizations/<org>/<month>/<slug>_<ts>`, `repaired_pdfs/<file>`, and the derived artefact key), plus two prefixes (`batches/…`, `manual_review/…`) that exist in storage but are produced by no code path traced here; no single document states the model. (`CODE-TRACED` + live; F-1, C-05.)
7. **One shared upload writer.** The customer pipeline upload and the consultant client upload both call `create_document_and_enqueue()`, so the two paths cannot drift in key shape, limit enforcement, content-type normalisation or pipeline enqueue. (`CODE-TRACED`; §7.1.)
8. **Canonical upload limits.** Ratified caps 10 MB per file / 50 files / 500 MB per batch; effective defaults 6 MB / 50 / 500 MB; machine-detectable codes with 413/400 semantics; an unknown size is rejected rather than allowed; every traced ingress resolves the same policy and every rejection precedes any write. (`CODE-TRACED`; §10.1–10.2, C-06, C-08.)
9. **The storage layer is not aligned with the ratified cap in the probed live environment.** `documents.file_size_limit` is 2 MiB there, the aligning migration (`20261024000000`) is unapplied, and it deliberately tightens only, so it would not raise that value. (`LIVE — READ-ONLY VERIFIED` + `CODE-TRACED`; F-3, F-9, C-09.)
10. **Repository configuration contradicts the ratified cap.** The in-repo Supabase CLI stack configuration sets a 50 MiB storage file-size limit — five times the ratified 10 MB ceiling. (`CODE-TRACED`; F-2, C-10.)
11. **Viewer read-only is enforced inconsistently.** An explicit 403 viewer denial exists on the canonical upload endpoint only; the legacy upload, organisation-files upload/bulk-upload, download and delete handlers carry no traced viewer-specific check. (`CODE-TRACED`, not executed; F-10.)
12. **Deletion is record-oriented, not object-oriented.** Soft delete leaves bytes in place; permanent delete removes the object best-effort and then deletes the row **even if** the object removal failed; neither path writes an audit entry. (`CODE-TRACED`; F-6, F-11, C-18, C-24.)
13. **Retention does not cover objects.** Retention enforcement is row-level soft delete, dry-run by default, restricted to the document/telemetry domains, and explicitly never touches the audit/evidence tables; stored objects are outside its scope, and no alternative object-lifecycle mechanism was found. (`CODE-TRACED`; F-7, C-19.)
14. **No behavioural security evidence was produced.** Cross-tenant read/write denial, RLS allow/deny under a real user JWT, consultant-grant enforcement and entity-staff scoping are all code-traced only; no negative-access test was executed in this audit. (`UNVERIFIED`; §15.4, C-16, C-22, C-28.)
15. **Fourteen documentation-vs-implementation conflicts are recorded without reconciliation.** They cluster into path/prefix scope (F-1), storage-layer limit alignment (F-2, F-3, F-9), object lifecycle and auditing (F-6, F-7, F-11), residual public-URL and TTL handling (F-4, F-5, F-13), missing artefact provisioning (F-12, F-14), viewer enforcement (F-10), and an unresolved grant catalogue (F-8). (§17, §18.)

**END OF BASELINE — no implementation change was made; the only artefact produced is this document.**
